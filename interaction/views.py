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


def _conversation_kwargs_from_message(message):
    """Extract all rich-media + reaction fields from an incoming message dict.

    Accepts both the new Node payload shape (type/caption/filename/...) and the
    legacy shape (message_type/media_caption/media_filename) so a Django deploy
    that lands ahead of the Node deploy keeps working.

    Returns a dict suitable for Conversation(**kwargs).
    """
    kw = {
        # Type (Node sends 'type', legacy 'message_type'). Default text.
        "message_type": message.get("type") or message.get("message_type") or "text",
        # Media fields
        "wa_message_id": message.get("wa_message_id"),
        "media_id": message.get("media_id"),
        "mime_type": message.get("mime_type"),
        "media_caption": message.get("caption") or message.get("media_caption"),
        "media_filename": message.get("filename") or message.get("media_filename"),
        "media_url": message.get("media_url"),
        "thumbnail_url": message.get("thumbnail_url"),
        # Reply / quote
        "quoted_message_id": message.get("quoted_message_id"),
        # Variant flags
        "is_voice": bool(message.get("is_voice", False)),
        "is_animated": bool(message.get("is_animated", False)),
        "forwarded": bool(message.get("forwarded", False)),
        "frequently_forwarded": bool(message.get("frequently_forwarded", False)),
        # Type-specific payloads
        "location_data": message.get("location"),
        "contacts_data": message.get("contacts"),
        "interactive_data": message.get("interactive"),
        "referred_product": message.get("referred_product"),
        "order_data": message.get("order"),
    }
    # Reaction event (type='reaction'): the row itself is the reaction. Capture
    # target + emoji so we can both (a) keep it as a discrete row and (b) update
    # the original target message's reactions[] in a follow-up step.
    reaction = message.get("reaction") or {}
    if reaction:
        kw["reaction_target_id"] = reaction.get("target_message_id") or reaction.get("message_id")
        kw["reaction_emoji"] = reaction.get("emoji") or None
    # Drop keys whose value is None to keep the row tidy and let DB defaults apply
    return {k: v for k, v in kw.items() if v is not None}


def _apply_reactions_to_targets(reaction_rows):
    """For each reaction-type row just saved, append it to the target message's
    cumulative `reactions` JSON array. Lookup is by wa_message_id =
    reaction_target_id. A WhatsApp user sending an empty-emoji reaction removes
    their previous reaction — handle that case by filtering them out.

    `reaction_rows` is an iterable of dicts with keys: target_message_id,
    emoji, from_phone, timestamp, tenant_id.
    """
    if not reaction_rows:
        return
    # Group by target so we do one UPDATE per target message
    by_target = {}
    for r in reaction_rows:
        tgt = r.get("target_message_id")
        if not tgt:
            continue
        by_target.setdefault(tgt, []).append(r)
    if not by_target:
        return
    for target_id, new_reactions in by_target.items():
        try:
            with transaction.atomic():
                # Update across ALL message-rows sharing this wa_message_id
                # (typically one). select_for_update so concurrent reactions
                # don't trample each other.
                rows = list(
                    Conversation.objects.select_for_update()
                    .filter(wa_message_id=target_id)
                )
                for row in rows:
                    current = list(row.reactions or [])
                    # Drop any prior reaction from the same user — a user can
                    # only have one active reaction per message at a time.
                    for nr in new_reactions:
                        sender_phone = nr.get("from_phone")
                        current = [c for c in current if c.get("from") != sender_phone]
                        if nr.get("emoji"):  # empty emoji = removed
                            current.append({
                                "from": sender_phone,
                                "emoji": nr["emoji"],
                                "timestamp": nr.get("timestamp"),
                            })
                    row.reactions = current
                    row.save(update_fields=["reactions"])
        except Exception as exc:
            logger.warning(
                f"Failed to apply reactions to target {target_id}: {exc}"
            )


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
        # Collect reaction events so we can update the target messages' cumulative
        # reactions[] array after the bulk insert.
        reaction_rows_to_apply = []

        for message in conversations:
            try:
                text = message.get('text', '')
                rich_kwargs = _conversation_kwargs_from_message(message)

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
                        **rich_kwargs,
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
                        **rich_kwargs,
                    ))

                # Stash reaction events for the post-insert aggregation step.
                if rich_kwargs.get("reaction_target_id"):
                    reaction_rows_to_apply.append({
                        "target_message_id": rich_kwargs["reaction_target_id"],
                        "emoji": rich_kwargs.get("reaction_emoji"),
                        "from_phone": contact_id,
                        "timestamp": str(timestamp),
                        "tenant_id": tenant_id,
                    })
            except Exception as msg_error:
                logger.error(f"Error preparing message: {msg_error}")
                continue

        # OPTIMIZED: Single bulk insert instead of N individual inserts
        if conversations_to_create:
            with transaction.atomic():
                Conversation.objects.bulk_create(conversations_to_create, batch_size=500)

        # Aggregate reactions onto the target message's reactions[] array.
        _apply_reactions_to_targets(reaction_rows_to_apply)

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
    reaction_rows_to_apply = []

    for message in conversations:
        text = message.get('text', '')
        rich_kwargs = _conversation_kwargs_from_message(message)
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
            **rich_kwargs,
        ))

        if rich_kwargs.get("reaction_target_id"):
            reaction_rows_to_apply.append({
                "target_message_id": rich_kwargs["reaction_target_id"],
                "emoji": rich_kwargs.get("reaction_emoji"),
                "from_phone": contact_id,
                "timestamp": str(timestamp),
                "tenant_id": tenant_id,
            })

    if conversations_to_create:
        with transaction.atomic():
            Conversation.objects.bulk_create(conversations_to_create, batch_size=500)

    _apply_reactions_to_targets(reaction_rows_to_apply)

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
    """
    Return a contact's full WhatsApp conversation history including all rich
    fields the chat UI needs to render real-WhatsApp-style:
      - reactions on each message
      - quoted_message_id for reply quote boxes
      - media (caption, filename, mime_type, media_id, media_url)
      - voice notes vs audio files (is_voice flag)
      - stickers (is_animated)
      - location / contacts / interactive / order payloads
      - forwarded label
    """
    try:
        source = request.GET.get('source', '')
        bpid = request.GET.get('bpid')
        tenant_id = request.headers.get('X-Tenant-Id')

        # Fields the UI needs. Order matches the model declaration so any new
        # column can be added once and shows up here automatically once added
        # to this whitelist.
        RICH_FIELDS = (
            'id', 'message_text', 'encrypted_message_text', 'sender', 'date_time',
            'message_type', 'wa_message_id', 'media_id', 'media_url', 'media_caption',
            'media_filename', 'mime_type', 'thumbnail_url',
            'quoted_message_id',
            'reaction_target_id', 'reaction_emoji', 'reactions',
            'is_voice', 'is_animated', 'forwarded', 'frequently_forwarded',
            'location_data', 'contacts_data', 'interactive_data',
            'referred_product', 'order_data',
        )
        conversations = (
            Conversation.objects
            .filter(contact_id=contact_id, business_phone_number_id=bpid, source=source)
            .values(*RICH_FIELDS)
            .order_by('date_time')
        )

        tenant = Tenant.objects.get(id=tenant_id)
        encryption_key = tenant.key

        formatted_conversations = []
        for conv in conversations:
            text_to_append = conv.get('message_text', None)
            encrypted_text = conv.get('encrypted_message_text', None)

            if encrypted_text is not None:
                try:
                    encrypted_text = encrypted_text.tobytes()
                    decrypted_text = decrypt_data(encrypted_text, key=encryption_key)
                    if decrypted_text:
                        text_to_append = json.dumps(decrypted_text)
                        if text_to_append.startswith('"') and text_to_append.endswith('"'):
                            text_to_append = text_to_append[1:-1]
                except Exception as dec_err:
                    logger.warning(f"Decrypt failed for conv id={conv.get('id')}: {dec_err}")

            # Synthesize the Node media-proxy URL when media_url is empty but
            # media_id is present (post-cutover Node writer doesn't pre-resolve
            # the Meta media URL). Keeps the chat UI download/play button alive
            # for new audio/voice/image rows.
            effective_media_url = conv.get('media_url')
            if not effective_media_url and conv.get('media_id'):
                effective_media_url = (
                    f"https://webhook.nuren.ai/media/{conv['media_id']}?bpid={bpid or ''}"
                )

            # Build the rich entry. UI can use `type` to switch render mode
            # (text/image/voice/reaction/quote-bubble/etc.).
            entry = {
                'id': conv.get('id'),
                'text': text_to_append,
                'sender': conv['sender'],
                'timestamp': conv.get('date_time').isoformat() if conv.get('date_time') else None,
                'type': conv.get('message_type') or 'text',
                'wa_message_id': conv.get('wa_message_id'),
                'media_id': conv.get('media_id'),
                'media_url': effective_media_url,
                'mime_type': conv.get('mime_type'),
                'caption': conv.get('media_caption'),
                'filename': conv.get('media_filename'),
                'thumbnail_url': conv.get('thumbnail_url'),
                'quoted_message_id': conv.get('quoted_message_id'),
                'reaction_target_id': conv.get('reaction_target_id'),
                'reaction_emoji': conv.get('reaction_emoji'),
                # Reactions left on this message by other users — list of
                # {from, emoji, timestamp}. Chat UI renders bubbles based on this.
                'reactions': conv.get('reactions') or [],
                'is_voice': bool(conv.get('is_voice')),
                'is_animated': bool(conv.get('is_animated')),
                'forwarded': bool(conv.get('forwarded')),
                'frequently_forwarded': bool(conv.get('frequently_forwarded')),
                'location': conv.get('location_data'),
                'contacts': conv.get('contacts_data'),
                'interactive': conv.get('interactive_data'),
                'referred_product': conv.get('referred_product'),
                'order': conv.get('order_data'),
            }
            # Drop None/empty values to keep response payloads small
            entry = {k: v for k, v in entry.items()
                     if v is not None and v != [] and v != {}}
            formatted_conversations.append(entry)

        return JsonResponse(formatted_conversations, safe=False)

    except Exception as e:
        logger.error(f"Error while fetching conversation data: {e}", exc_info=True)
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
