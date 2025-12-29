from celery import shared_task
from django.db import transaction
from .models import Conversation
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os
import json
from django.utils import timezone
import base64

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, queue='process_conv_queue')
def process_conversations(self, payload, key):
    try:
        print("tasks PRocessing conv")

        # ✅ Decode Base64 key
        if isinstance(key, str):
            key = base64.b64decode(key)

        assert isinstance(key, (bytes, bytearray)), "Encryption key is not bytes"
        assert len(key) in (16, 24, 32), "Invalid AES key length"

        with transaction.atomic():
            contact_id = payload['contact_id']
            conversations = payload['conversations']
            tenant = payload['tenant']
            source = payload['source']
            bpid = payload['business_phone_number_id']
            timestamp = payload['time']

            batch_size = 100
            for i in range(0, len(conversations), batch_size):
                batch = conversations[i:i + batch_size]

                conversations_to_create = [
                    Conversation(
                        contact_id=contact_id,
                        encrypted_message_text=encrypt_data(
                            data=message.get('text', ''),
                            key=key
                        ),
                        sender=message.get('sender', ''),
                        tenant_id=tenant,
                        source=source,
                        business_phone_number_id=bpid,
                        date_time=timestamp
                    )
                    for message in batch
                ]

                Conversation.objects.bulk_create(conversations_to_create)

        print("✅ Conversations saved successfully")
        return True

    except Exception as exc:
        logger.error(f"❌ Error processing conversations: {exc}", exc_info=True)
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

def encrypt_data(data, key):
    data_str = json.dumps(data)
    
    iv = os.urandom(16)  # AES block size is 16 bytes
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()


    pad_len = 16 - len(data_str) % 16
    data_str += chr(pad_len) * pad_len

    encrypted_data = encryptor.update(data_str.encode()) + encryptor.finalize()


    return iv + encrypted_data
