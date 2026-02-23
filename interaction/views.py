from django.shortcuts import get_object_or_404
from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from datetime import datetime
from .models import Conversation,Group
from tenant.models import Tenant
from django.contrib.contenttypes.models import ContentType
from .serializers import GroupSerializer
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import viewsets
from django.http import JsonResponse
from django.db.models import Count
import random
from django.views.decorators.csrf import csrf_exempt
import json, os
from django.db import transaction
from django.views.decorators.http import require_http_methods
from django.utils.timezone import make_aware
import re
import logging
logger = logging.getLogger('simplecrm')
from django.utils import timezone
import json
import logging
from typing import List, Dict
import base64



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .tasks import process_conversations
from redis import Redis, ConnectionPool

# # Redis Connection Pool Configuration
# REDIS_CONFIG = {
#     'host': 'whatsappnuren.redis.cache.windows.net',
#     'port': 6379,
#     'password': 'O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM=',
#     # 'ssl': True,
#     'max_connections': 50  # Adjust based on your infrastructure
# }

# redis_pool = ConnectionPool(**REDIS_CONFIG)
# redis_client = Redis(connection_pool=redis_pool)
logger = logging.getLogger(__name__)


def convert_time(datetime_str):
    """
    Converts a date-time string from 'DD/MM/YYYY, HH:MM:SS.SSS'
    to PostgreSQL-compatible 'YYYY-MM-DD HH:MM:SS.SSS' format.
    
    Args:
        datetime_str (str): The date-time string to be converted.
    
    Returns:
        str: Converted date-time string in PostgreSQL format.
    """
    try:
        # Parse the input date-time string
        parsed_datetime = datetime.strptime(datetime_str, "%d/%m/%Y, %H:%M:%S.%f")
        aware_datetime = make_aware(parsed_datetime)
        postgres_format = aware_datetime.strftime("%Y-%m-%d %H:%M:%S.%f")
        return postgres_format
    except ValueError as e:
        print(f"Error converting datetime: {e}")
        return None
    

def create_conversation_objects(payload: Dict) -> List[Conversation]:
    return [
        Conversation(
            contact_id=payload['contact_id'],
            message_text=message.get('text', ''),

            # Media support fields
            message_type=message.get('message_type', 'text'),
            media_url=message.get('media_url'),
            media_caption=message.get('media_caption'),
            media_filename=message.get('media_filename'),
            thumbnail_url=message.get('thumbnail_url'),

            sender=message.get('sender', ''),
            tenant_id=payload['tenant'],
            source=payload['source'],
            business_phone_number_id=payload['business_phone_number_id'],
            date_time = payload['time']
        ) for message in payload['conversations']
    ]

def bulk_create_with_batching(objects: List, batch_size: int = 500):
    """Bulk create with batch processing to prevent memory overload"""
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i+batch_size]
        Conversation.objects.bulk_create(batch, ignore_conflicts=True)


# Encrypt the data using AES symmetric encryption
# IMP: Saves conversation, takes in data from whatsappbotserver, saves data in db using redis
#
# ROBUST FALLBACK MECHANISM (3-tier):
# 1. Celery + Redis (fast async) - tries first if Redis is available
# 2. Direct sync save (blocking but immediate) - fallback if Celery fails
# 3. Database queue (guaranteed delivery) - last resort, processed by cron

def check_redis_health():
    """Quick check if Redis is accessible"""
    try:
        from django.conf import settings
        import redis
        r = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
        r.ping()
        return True
    except Exception:
        return False


def _get_dedup_redis():
    """Get a Redis client for deduplication (cached per-thread via module-level)."""
    try:
        from django.conf import settings
        import redis
        return redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=2)
    except Exception:
        return None


def _check_idempotency(message_id):
    """
    Check if a message_id was already processed recently (5-min window).
    Returns True if duplicate (already processed), False if new.

    Uses a 2-phase approach:
    - Phase 1 (here): SET NX with short 30s TTL as a "processing lock"
    - Phase 2 (_mark_idempotency_done): Extend TTL to 5 min after successful save

    If the save fails, the 30s lock expires and retries can succeed.
    If the save succeeds, the 5-min TTL prevents retry duplicates.
    """
    if not message_id:
        return False
    try:
        r = _get_dedup_redis()
        if not r:
            return False
        key = f"msg:dedup:{message_id}"
        # Short 30s lock — if save fails, retries can still succeed after lock expires
        was_set = r.set(key, "processing", nx=True, ex=30)
        return not was_set  # True = duplicate, False = new
    except Exception:
        return False


def _mark_idempotency_done(message_id):
    """Mark a message_id as successfully saved — extend TTL to 5 minutes."""
    if not message_id:
        return
    try:
        r = _get_dedup_redis()
        if not r:
            return
        key = f"msg:dedup:{message_id}"
        r.set(key, "done", ex=300)  # 5-minute TTL
    except Exception:
        pass


@csrf_exempt
def save_conversations(request, contact_id):
    """
    Save conversations with robust 3-tier fallback:
    1. Celery (async) - if Redis healthy
    2. Sync save (blocking) - immediate fallback
    3. DB queue (guaranteed) - if sync fails, queued for later processing
    """
    payload = None
    try:
        payload = extract_payload(request)
        payload['time'] = timezone.now()

        # Idempotency check: skip if this message_id was already saved recently
        message_id = payload.get('message_id')
        if _check_idempotency(message_id):
            logger.info(f"Duplicate save skipped for message_id={message_id[:30] if message_id else 'N/A'}")
            return JsonResponse(
                {"message": "Already saved", "method": "deduplicated"},
                status=200
            )

        tenant = Tenant.objects.get(id=payload['tenant'])

        # Handle missing encryption key — save without encryption rather than crashing
        if tenant.key:
            key = bytes(tenant.key)
        else:
            logger.warning(f"Tenant {tenant.id} has no encryption key — saving without encryption")
            key = None

        safe_payload = json.loads(json.dumps(payload, default=str))
        safe_key = base64.b64encode(key).decode() if key else ""

        # TIER 1: Try Celery ONLY if explicitly enabled (requires Celery worker running)
        # Enable by setting USE_CELERY=true in Azure App Service Configuration
        use_celery = os.environ.get('USE_CELERY', 'false').lower() == 'true'
        if use_celery and key and check_redis_health():
            try:
                process_conversations.delay(safe_payload, safe_key)
                # Note: _mark_idempotency_done is called inside the Celery task
                # after the actual DB save succeeds (see interaction/tasks.py)
                logger.info(f"Conversation queued via Celery for {payload.get('contact_id')}")
                return JsonResponse(
                    {"message": "Conversation accepted", "method": "async"},
                    status=202
                )
            except Exception as celery_error:
                logger.warning(f"Celery failed, trying sync: {celery_error}")

        # TIER 2: Direct sync save (primary path until Celery is enabled)
        try:
            logger.info(f"Saving conversation directly for {payload.get('contact_id')}")
            result = save_conversations_sync(payload, key)
            _mark_idempotency_done(message_id)
            return result
        except Exception as sync_error:
            logger.error(f"Sync save failed, queuing to DB: {sync_error}")

            # TIER 3: Queue to database (guaranteed delivery)
            try:
                from interaction.pending_tasks import queue_pending_task
                task = queue_pending_task(safe_payload, key)
                _mark_idempotency_done(message_id)
                logger.info(f"Conversation queued to DB (task {task.id}) for {payload.get('contact_id')}")
                return JsonResponse(
                    {"message": "Conversation queued for processing", "method": "db_queue", "task_id": task.id},
                    status=202
                )
            except Exception as queue_error:
                logger.critical(f"ALL SAVE METHODS FAILED for {payload.get('contact_id')}: {queue_error}")
                return JsonResponse(
                    {"error": "Failed to save conversation", "details": str(sync_error)},
                    status=500
                )

    except Tenant.DoesNotExist:
        logger.error(f"Tenant not found: {payload.get('tenant') if payload else 'unknown'}")
        return JsonResponse({"error": "Tenant not found"}, status=404)
    except Exception as e:
        logger.error(f"Error saving conversation: {e}", exc_info=True)
        return handle_error(e)


def save_conversations_sync(payload, key):
    """
    Synchronous fallback when Celery is unavailable.
    OPTIMIZED: Uses bulk_create for much faster inserts.
    Supports key=None for tenants without encryption keys (saves plaintext).
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import os as sync_os

    try:
        contact_id = payload['contact_id']
        conversations = payload.get('conversations', [])
        tenant_id = payload['tenant']
        source = payload.get('source', '')
        bpid = payload.get('business_phone_number_id', '')
        timestamp = payload.get('time', timezone.now())

        if not conversations:
            logger.warning(f"Empty conversations for {contact_id}")
            return JsonResponse({"message": "No conversations to save"}, status=200)

        # OPTIMIZED: Prepare all objects first, then bulk insert
        conversations_to_create = []

        for message in conversations:
            try:
                text = message.get('text', '')

                if key:
                    # Encrypt message text
                    data_str = json.dumps(text)
                    iv = sync_os.urandom(16)
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                    encryptor = cipher.encryptor()
                    pad_len = 16 - len(data_str) % 16
                    data_str += chr(pad_len) * pad_len
                    encrypted_data = iv + encryptor.update(data_str.encode()) + encryptor.finalize()

                    conversations_to_create.append(Conversation(
                        contact_id=contact_id,
                        encrypted_message_text=encrypted_data,
                        sender=message.get('sender', 'unknown'),
                        tenant_id=tenant_id,
                        source=source,
                        business_phone_number_id=bpid,
                        date_time=timestamp,
                        message_type=message.get('message_type', 'text'),
                        media_url=message.get('media_url'),
                        media_caption=message.get('media_caption'),
                        media_filename=message.get('media_filename'),
                        thumbnail_url=message.get('thumbnail_url')
                    ))
                else:
                    # No encryption key — save as plaintext
                    conversations_to_create.append(Conversation(
                        contact_id=contact_id,
                        message_text=text,
                        sender=message.get('sender', 'unknown'),
                        tenant_id=tenant_id,
                        source=source,
                        business_phone_number_id=bpid,
                        date_time=timestamp,
                        message_type=message.get('message_type', 'text'),
                        media_url=message.get('media_url'),
                        media_caption=message.get('media_caption'),
                        media_filename=message.get('media_filename'),
                        thumbnail_url=message.get('thumbnail_url')
                    ))
            except Exception as msg_error:
                logger.error(f"Error preparing message: {msg_error}")
                continue

        # OPTIMIZED: Single bulk insert instead of N individual inserts
        if conversations_to_create:
            with transaction.atomic():
                Conversation.objects.bulk_create(conversations_to_create, batch_size=500)

        saved_count = len(conversations_to_create)
        logger.info(f"Sync saved {saved_count} conversations for {contact_id} (bulk)")
        return JsonResponse(
            {"message": "Conversation saved (sync-bulk)", "method": "sync-bulk", "saved": saved_count},
            status=201
        )

    except Exception as e:
        logger.error(f"❌ Sync save failed: {e}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


def save_conversations_sync_from_pending(payload, key):
    """
    Process a conversation from the pending tasks queue.
    Similar to save_conversations_sync but without HTTP response.
    Raises exception on failure (for retry logic).
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import os as sync_os

    contact_id = payload['contact_id']
    conversations = payload.get('conversations', [])
    tenant_id = payload['tenant']
    source = payload.get('source', '')
    bpid = payload.get('business_phone_number_id', '')
    timestamp = payload.get('time', timezone.now())

    if not conversations:
        logger.warning(f"⚠️ Empty conversations for pending task {contact_id}")
        return 0

    conversations_to_create = []

    for message in conversations:
        text = message.get('text', '')
        data_str = json.dumps(text)
        iv = sync_os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        pad_len = 16 - len(data_str) % 16
        data_str += chr(pad_len) * pad_len
        encrypted_data = iv + encryptor.update(data_str.encode()) + encryptor.finalize()

        conversations_to_create.append(Conversation(
            contact_id=contact_id,
            encrypted_message_text=encrypted_data,
            sender=message.get('sender', 'unknown'),
            tenant_id=tenant_id,
            source=source,
            business_phone_number_id=bpid,
            date_time=timestamp,
            message_type=message.get('message_type', 'text'),
            media_url=message.get('media_url'),
            media_caption=message.get('media_caption'),
            media_filename=message.get('media_filename'),
            thumbnail_url=message.get('thumbnail_url')
        ))

    if conversations_to_create:
        with transaction.atomic():
            Conversation.objects.bulk_create(conversations_to_create, batch_size=500)

    saved_count = len(conversations_to_create)
    logger.info(f"✅ Pending task saved {saved_count} conversations for {contact_id}")
    return saved_count
# def check_rate_limit(request, max_requests: int = 100, window: int = 60) -> bool:
#     """Implement sliding window rate limiting"""
#     client_ip = get_client_ip(request)
#     rate_limit_key = f'conversations_ratelimit:{client_ip}'
    
#     with redis_client.pipeline() as pipe:
#         pipe.incr(rate_limit_key)
#         pipe.expire(rate_limit_key, window)
#         current_count, _ = pipe.execute()
    
#     return current_count <= max_requests

def extract_payload(request) -> Dict:
    """Validate and extract request payload"""
    if request.method != 'POST':
        raise ValueError("Invalid request method")
    
    body = json.loads(request.body)
    return {
        'contact_id': request.resolver_match.kwargs['contact_id'],
        'conversations': body.get('conversations', []),
        'tenant': body.get('tenant'),
        'source': request.GET.get('source', ''),
        'business_phone_number_id': body.get('business_phone_number_id'),
        'time': body.get('time'),
        'message_id': body.get('message_id'),  # WhatsApp wamid for deduplication
    }

def handle_error(error):
    """Centralized error handling"""
    if isinstance(error, json.JSONDecodeError):
        logger.error(f"JSON decode error: {error}")
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    else:
        logger.error(f"Unexpected error in handle error: {error}")
        return JsonResponse({"error": str(error)}, status=500)

# def get_client_ip(request):
#     """Get client IP with X-Forwarded-For support"""
#     x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
#     return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

# GET req at fastAPI
# not using here at django
# Most of GET requests are done at fastAPI
@csrf_exempt
def view_conversation(request, contact_id):
    try:
        # Query conversations for a specific contact_id
        source = request.GET.get('source', '')
        bpid = request.GET.get('bpid')
        tenant_id = request.headers.get('X-Tenant-Id')

        conversations = Conversation.objects.filter(contact_id=contact_id,business_phone_number_id=bpid,source=source).values('message_text', 'sender', 'encrypted_message_text').order_by('date_time')

        tenant = Tenant.objects.get(id = tenant_id)
        encryption_key = tenant.key
        # print("ENC KEY: ", tenant_id)

        # Format data as per your requirement
        formatted_conversations = []
        for conv in conversations:
            text_to_append = conv.get('message_text', None)
            encrypted_text = conv.get('encrypted_message_text', None)
            # print("text: ", text)

            if encrypted_text!= None:
                encrypted_text = encrypted_text.tobytes()
                decrypted_text = decrypt_data(encrypted_text, key=encryption_key)
                # print("Decrypted Text: ", decrypted_text)
                if decrypted_text:
                    text_to_append = json.dumps(decrypted_text)
                    if text_to_append.startswith('"') and text_to_append.endswith('"'):
                        text_to_append = text_to_append[1:-1]
            # print("Text to append: ", text_to_append, type(text_to_append))
            formatted_conversations.append({'text': text_to_append, 'sender': conv['sender']})

        return JsonResponse(formatted_conversations, safe=False)

    except Exception as e:
        print("Error while fetching conversation data:", e)
        return JsonResponse({'error': str(e)}, status=500)


def is_encrypted(data):
    return data.startswith('b"')


from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json

def decrypt_data(encrypted_data, key):
    # Extract the IV from the first 16 bytes  # Assuming it's still in string format
    # print("rcvd data: ", encrypted_data)
    # print(type(encrypted_data))

    # Correctly extract IV (first 16 bytes) and the actual encrypted data
    iv = encrypted_data[:16]
    encrypted_data = encrypted_data[16:]

    # Ensure the key is in bytes (handle memoryview if needed)
    if isinstance(key, memoryview):
        key = bytes(key)


    # Initialize the cipher
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    # Perform decryption
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    # Remove padding (PKCS#7 padding)
    pad_len = decrypted_data[-1]
    decrypted_data = decrypted_data[:-pad_len]

    return json.loads(decrypted_data.decode())


# not using
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def list(self, request):
        """
        Handle GET requests to retrieve all Group entries.
        """
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        """
        Handle GET requests to retrieve a single Group entry by ID.
        """
        group = self.get_object()
        serializer = self.get_serializer(group)
        return Response(serializer.data)

    def create(self, request):
        """
        Handle POST requests to create a new Group entry.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        Handle PUT requests to update a Group entry by ID.
        """
        group = self.get_object()
        serializer = self.get_serializer(group, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        Handle DELETE requests to delete a Group entry by ID.
        """
        group = self.get_object()
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
