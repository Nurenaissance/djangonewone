from celery import shared_task
from django.db import transaction, connection
from django import db
from .models import Conversation
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json
from django.utils import timezone
import base64

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=5, queue='process_conv_queue')
def process_conversations(self, payload, key):
    # CRITICAL: Close any stale connections at start
    db.close_old_connections()

    try:
        logger.info(f"📝 Processing conversation for contact: {payload.get('contact_id')}")

        # Validate payload
        required_fields = ['contact_id', 'conversations', 'tenant', 'source', 'business_phone_number_id']
        for field in required_fields:
            if field not in payload or payload[field] is None:
                raise ValueError(f"Missing required field: {field}")

        conversations = payload['conversations']
        if not conversations or len(conversations) == 0:
            logger.warning(f"⚠️ Empty conversations array for {payload.get('contact_id')}, skipping")
            return {'status': 'skipped', 'reason': 'empty conversations'}

        # ✅ Decode Base64 key
        if isinstance(key, str):
            key = base64.b64decode(key)

        assert isinstance(key, (bytes, bytearray)), "Encryption key is not bytes"
        assert len(key) in (16, 24, 32), f"Invalid AES key length: {len(key)}"

        with transaction.atomic():
            contact_id = payload['contact_id']
            tenant = payload['tenant']
            source = payload['source']
            bpid = payload['business_phone_number_id']
            timestamp = payload.get('time') or timezone.now()

            batch_size = 100
            total_saved = 0

            for i in range(0, len(conversations), batch_size):
                batch = conversations[i:i + batch_size]

                conversations_to_create = []
                for message in batch:
                    # Skip invalid messages
                    if not isinstance(message, dict):
                        logger.warning(f"⚠️ Skipping invalid message (not a dict): {type(message)}")
                        continue

                    try:
                        conv = Conversation(
                            contact_id=contact_id,
                            encrypted_message_text=encrypt_data(
                                data=message.get('text', ''),
                                key=key
                            ),
                            sender=message.get('sender', 'unknown'),
                            tenant_id=tenant,
                            source=source,
                            business_phone_number_id=bpid,
                            date_time=timestamp,
                            # Media support fields
                            message_type=message.get('message_type', 'text'),
                            media_url=message.get('media_url'),
                            media_caption=message.get('media_caption'),
                            media_filename=message.get('media_filename'),
                            thumbnail_url=message.get('thumbnail_url')
                        )
                        conversations_to_create.append(conv)
                    except Exception as msg_error:
                        logger.error(f"❌ Error creating conversation object: {msg_error}")
                        continue

                if conversations_to_create:
                    Conversation.objects.bulk_create(conversations_to_create)
                    total_saved += len(conversations_to_create)

        logger.info(f"✅ Saved {total_saved} conversations for {contact_id}")
        return {'status': 'success', 'saved': total_saved, 'contact_id': contact_id}

    except Exception as exc:
        logger.error(f"❌ Error processing conversations for {payload.get('contact_id', 'unknown')}: {exc}", exc_info=True)

        # Don't retry for validation errors
        if isinstance(exc, (ValueError, AssertionError)):
            logger.error(f"❌ Non-retryable error, not retrying: {exc}")
            return {'status': 'failed', 'error': str(exc), 'retryable': False}

        # Exponential backoff: 2, 4, 8, 16, 32 seconds
        countdown = 2 ** (self.request.retries + 1)
        raise self.retry(exc=exc, countdown=countdown)

    finally:
        # CRITICAL: Always close database connections after task
        try:
            db.connections.close_all()
        except Exception as e:
            logger.warning(f"Error closing database connections: {e}")

def encrypt_data(data, key):
    data_str = json.dumps(data)
    
    iv = os.urandom(16)  # AES block size is 16 bytes
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()


    pad_len = 16 - len(data_str) % 16
    data_str += chr(pad_len) * pad_len

    encrypted_data = encryptor.update(data_str.encode()) + encryptor.finalize()


    return iv + encrypted_data
