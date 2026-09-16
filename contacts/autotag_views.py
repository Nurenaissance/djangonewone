"""
AI-based auto lead-tagging (rule-driven, reusable, tenant-scoped).
POST /auto-tag?tenant=<id>[&dry_run=1]   Auth: X-Api-Key or user JWT.

Rules (as specified):
  cold  -> contact replied only once and didn't engage      (<=1 user message)
  warm  -> some conversation                                 (>=2 user messages, no full details)
  hot   -> gave all their details                            (shared an email = final step of the lead flow)

Manual tags (customField.tag_source == 'manual') are never overwritten.
"""
import re
import logging
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Contact
from simplecrm.models import Tenant
from interaction.models import Conversation

logger = logging.getLogger(__name__)
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")


def _decrypt(enc, key):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    import json
    enc = bytes(enc); iv = enc[:16]; ct = enc[16:]
    d = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend()).decryptor()
    p = d.update(ct) + d.finalize()
    try:
        return json.loads(p[:-p[-1]].decode(errors="replace"))
    except Exception:
        return ""


NO_EMAIL_RE = re.compile(
    r"(no\s*e?-?mail|don'?t\s*have\s*(an?\s*)?e?-?mail|dont\s*have\s*e?-?mail|"
    r"e?-?mail\s*(nahi|nhi|nahin)|(nahi|nhi|nahin)\s*(hai|h)?\s*e?-?mail|"
    r"mail\s*nahi|no\s*mail)", re.I)

def classify(user_msgs, bot_msgs):
    """Rules: hot = gave email OR reached the email step (fully qualified) OR declined email.
    warm = some conversation. cold = replied once."""
    n = len(user_msgs)
    gave_email = any(EMAIL_RE.search(str(m) or "") for m in user_msgs)
    declined_email = any(NO_EMAIL_RE.search(str(m) or "") for m in user_msgs)
    # the bot asks for email only after name + city + pincode, so this == a deep, qualified lead
    reached_email_step = any("email" in str(b or "").lower() for b in bot_msgs)
    # HOT = shared an actual email address with the bot (only signal that counts).
    if gave_email:
        return "hot"
    if n >= 2:
        return "warm"
    return "cold"


class AutoTagView(APIView):
    def post(self, request, *args, **kwargs):
        tenant_id = request.GET.get("tenant") or request.headers.get("X-Tenant-Id")
        if not tenant_id:
            return Response({"error": "tenant is required"}, status=400)
        dry = str(request.GET.get("dry_run", "")).lower() in ("1", "true", "yes")
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({"error": "tenant not found"}, status=404)
        key = bytes(tenant.key) if tenant.key else None

        counts = {"cold": 0, "warm": 0, "hot": 0, "skipped_manual": 0, "no_convo": 0}
        changed = []
        for contact in Contact.objects.filter(tenant_id=tenant_id):
            cf = contact.customField or {}
            if cf.get("tag_source") == "manual":
                counts["skipped_manual"] += 1
                continue
            rows = (Conversation.objects
                    .filter(tenant_id=tenant_id, contact_id=contact.phone)
                    .order_by("date_time"))
            if not rows:
                counts["no_convo"] += 1
                continue
            umsgs, bmsgs = [], []
            for r in rows:
                t = _decrypt(r.encrypted_message_text, key) if (key and r.encrypted_message_text) else (r.message_text or "")
                (umsgs if r.sender == "user" else bmsgs).append(str(t))
            if not umsgs:
                counts["no_convo"] += 1
                continue
            msgs = umsgs
            tag = classify(umsgs, bmsgs)
            counts[tag] += 1
            if cf.get("tag") != tag:
                changed.append({"contact": contact.phone, "name": contact.name or "", "tag": tag, "user_msgs": len(msgs)})
                if not dry:
                    cf["tag"] = tag
                    cf["tag_source"] = "auto"
                    cf["tag_updated_at"] = timezone.now().isoformat()
                    contact.customField = cf
                    contact.save(update_fields=["customField"])
        return Response({"tenant": tenant_id, "dry_run": dry, "distribution": counts,
                         "changed_count": len(changed), "changed": changed[:100]})
