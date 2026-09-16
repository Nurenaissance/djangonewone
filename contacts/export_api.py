"""
Scoped, revocable chat-history export for external integrations (e.g. Quiver).

Auth: header `X-Export-Key`. The key is looked up in the `export_api_keys`
table, which maps ONE key -> ONE tenant. The tenant is derived ONLY from that
mapping (never from a request header/JWT), so a key can read exactly one
tenant's history and nothing else. The key is not a platform JWT and is
rejected everywhere except this endpoint. Revoke by setting active=false.

GET /nuren-export/messages/?after_id=<int>&limit=<=1000
  -> paginated messages for the key's tenant, ascending by id.
     `external_id` (wa_message_id) is stable for dedup on re-runs.
"""
import json
import logging

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

from interaction.models import Conversation
from simplecrm.models import Tenant

logger = logging.getLogger(__name__)


def _tenant_for_key(key):
    if not key:
        return None
    with connection.cursor() as c:
        c.execute("SELECT tenant_id FROM export_api_keys WHERE key=%s AND active=true", [key])
        row = c.fetchone()
    return row[0] if row else None


def _decrypt(enc, keyb):
    enc = bytes(enc); iv = enc[:16]; ct = enc[16:]
    d = Cipher(algorithms.AES(keyb), modes.CBC(iv), backend=default_backend()).decryptor()
    p = d.update(ct) + d.finalize()
    try:
        return json.loads(p[:-p[-1]].decode(errors="replace"))
    except Exception:
        return ""


def _flatten(v):
    """Some rows store the raw WhatsApp envelope as text; return clean string."""
    if isinstance(v, dict):
        if isinstance(v.get("text"), dict):
            return v["text"].get("body", "")
        if v.get("type") == "interactive":
            return (v.get("interactive", {}) or {}).get("body", {}).get("text", "") or "[interactive]"
        for k in ("image", "document", "video", "audio"):
            if isinstance(v.get(k), dict):
                return v[k].get("caption") or f"[{k}]"
        return json.dumps(v)
    return v


@csrf_exempt
def export_messages(request):
    tenant_id = _tenant_for_key(request.headers.get("X-Export-Key"))
    if not tenant_id:
        return JsonResponse({"error": "invalid or inactive export key"}, status=401)
    try:
        after_id = int(request.GET.get("after_id", 0))
    except (TypeError, ValueError):
        after_id = 0
    try:
        limit = min(max(int(request.GET.get("limit", 500)), 1), 1000)
    except (TypeError, ValueError):
        limit = 500

    tenant = Tenant.objects.get(id=tenant_id)
    keyb = bytes(tenant.key) if tenant.key else None

    rows = list(Conversation.objects.filter(tenant_id=tenant_id, id__gt=after_id)
                .order_by("id")[:limit])
    out = []
    for r in rows:
        text = r.message_text
        if getattr(r, "encrypted_message_text", None) and keyb:
            try:
                text = _decrypt(r.encrypted_message_text, keyb)
            except Exception:
                pass
        out.append({
            "id": r.id,
            "external_id": r.wa_message_id or f"nuren-{r.id}",
            "contact_id": r.contact_id,
            "sender": r.sender,
            "text": _flatten(text),
            "type": getattr(r, "message_type", None) or "text",
            "timestamp": r.date_time.isoformat() if r.date_time else None,
            "business_phone_number_id": r.business_phone_number_id,
        })
    return JsonResponse({
        "tenant": tenant_id,
        "count": len(out),
        "next_after_id": out[-1]["id"] if out else after_id,
        "has_more": len(out) == limit,
        "messages": out,
    })
