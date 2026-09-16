"""
Reusable, multi-tenant 9-hour re-engagement reminder.

POST /reengage/run?tenant=<id>[&dry_run=1][&min_hours=9][&max_hours=22][&limit=50]
Auth: X-Api-Key: n8n-nuren-2026 (server-to-server, called by an n8n schedule).

A contact is "due" when their LATEST message is a bot message that ends with a
question ("?"), sent between min_hours and max_hours ago (so we stay inside
WhatsApp's 24h free-form window), and they have not already been reminded.
The reminder is built from chat history (echoes the pending question) and sent
via the node /sendMessage route so it persists and shows in the dashboard.
Idempotent: sets customField.reengaged_at so each contact is reminded once.
"""
import logging
from datetime import timedelta

import requests
from django.utils import timezone
from django.db.models import Max
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Contact
from simplecrm.models import Tenant
from interaction.models import Conversation
from whatsapp_chat.models import WhatsappTenantData

logger = logging.getLogger(__name__)
NODE_SEND_URL = "https://webhook.nuren.ai/sendMessage"
N8N_API_KEY = "n8n-nuren-2026"


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


def _topic(text):
    t = (text or "").lower()
    if "door" in t or "window" in t or "fenesta" in t:
        return "premium doors & windows"
    return "what we offer"


def _build_reminder(name, last_bot_q):
    """Contextual, catchy re-engagement nudge with a hook + 'still interested?' CTA."""
    who = f" {name}" if name and name.strip() else " there"
    topic = _topic(last_bot_q)
    # single asterisks render as *bold* on WhatsApp
    return (f"Hey{who}! 👋 Still thinking about {topic}? 🚪✨\n\n"
            f"You were *this close* to getting sorted — one quick reply and our expert "
            f"will help you finish in under 2 minutes.\n\n"
            f"Are you still interested? 😊")


class ReengageRunView(APIView):
    def post(self, request, *args, **kwargs):
        tenant_id = request.GET.get("tenant") or request.headers.get("X-Tenant-Id")
        if not tenant_id:
            return Response({"error": "tenant is required"}, status=400)
        dry = str(request.GET.get("dry_run", "")).lower() in ("1", "true", "yes")
        min_h = float(request.GET.get("min_hours", 9))
        max_h = float(request.GET.get("max_hours", 22))
        limit = int(request.GET.get("limit", 50))

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response({"error": "tenant not found"}, status=404)
        key = bytes(tenant.key) if tenant.key else None
        wtd = WhatsappTenantData.objects.filter(tenant_id=tenant_id).first()
        if not wtd:
            return Response({"error": "no WhatsApp config for tenant"}, status=400)

        now = timezone.now()
        lo, hi = now - timedelta(hours=max_h), now - timedelta(hours=min_h)

        # contacts whose LATEST message time falls in [lo, hi]
        latest = (Conversation.objects.filter(tenant_id=tenant_id)
                  .values("contact_id").annotate(last=Max("date_time"))
                  .filter(last__gte=lo, last__lte=hi)[:500])

        results = []
        for row in latest:
            if len(results) >= limit:
                break
            cid = row["contact_id"]
            last_msg = (Conversation.objects.filter(tenant_id=tenant_id, contact_id=cid)
                        .order_by("-date_time").first())
            if not last_msg or last_msg.sender != "bot":
                continue  # user spoke last (not a drop-off) or no msg
            last_text = _decrypt(last_msg.encrypted_message_text, key) if (key and last_msg.encrypted_message_text) else (last_msg.message_text or "")
            if not str(last_text).strip().endswith("?"):
                continue  # bot's last line wasn't a pending question -> not mid-way
            contact = Contact.objects.filter(tenant_id=tenant_id, phone=cid).first()
            cf = (contact.customField if contact else None) or {}
            if cf.get("reengaged_at"):
                continue  # already reminded (one per contact)

            name = (contact.name if contact else "") or ""
            reminder = _build_reminder(name, str(last_text))
            entry = {"contact_id": cid, "name": name, "pending_q": str(last_text)[:120],
                     "reminder": reminder}

            if not dry:
                try:
                    requests.post(NODE_SEND_URL,
                        json={"custom": True, "phone": cid,
                              "business_phone_number_id": wtd.business_phone_number_id,
                              "access_token": wtd.access_token, "tenant_id": tenant_id,
                              "message": {"type": "text", "text": {"body": reminder}}},
                        headers={"Content-Type": "application/json", "X-Api-Key": N8N_API_KEY,
                                 "X-Tenant-Id": tenant_id}, timeout=20)
                    if contact:
                        cf["reengaged_at"] = now.isoformat()
                        contact.customField = cf
                        contact.save(update_fields=["customField"])
                    entry["sent"] = True
                except Exception as e:
                    logger.error("reengage send failed for %s: %s", cid, e)
                    entry["sent"] = False
            results.append(entry)

        return Response({"tenant": tenant_id, "dry_run": dry,
                         "window_hours": [min_h, max_h], "due_count": len(results),
                         "contacts": results})
