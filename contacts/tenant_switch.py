"""
Scoped account switching ("Switch Numbers").

A user is bound to one tenant (CustomUser.tenant) and the JWT tenant claim is
authoritative. To let one operator move between two of their own accounts
without re-logging-in, we keep an explicit allow-list:

    tenant_switch_access(user_id, tenant_id)

GET  /switch-tenant/options  -> tenants this user may switch to (incl. their own)
POST /switch-tenant          -> {tenant_id} ; returns a fresh JWT scoped to it

Security: a switch is only issued when the target is the user's own tenant or
an explicitly allow-listed pair. Nothing here widens access for anyone else —
an unlisted user gets 403.
"""
import datetime
import logging

import jwt
from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response

from simplecrm.models import Tenant

logger = logging.getLogger(__name__)


def _home_tenant(user_id):
    """The user's real tenant from the DB — never the (possibly switched) JWT claim."""
    from django.contrib.auth import get_user_model
    u = get_user_model().objects.filter(id=user_id).first()
    return str(u.tenant_id) if u and u.tenant_id else None


def _allowed_targets(user_id, own_tenant):
    own_tenant = _home_tenant(user_id) or own_tenant
    with connection.cursor() as c:
        c.execute(
            "SELECT tenant_id FROM tenant_switch_access WHERE user_id=%s AND active=true",
            [str(user_id)],
        )
        rows = [r[0] for r in c.fetchall()]
    out = []
    seen = set()
    for tid in ([own_tenant] + rows):
        if not tid or tid in seen:
            continue
        seen.add(tid)
        t = Tenant.objects.filter(id=tid).first()
        if not t:
            continue
        out.append({
            "tenant_id": t.id,
            "organization": t.organization or t.id,
            "is_current": False,
        })
    return out


class SwitchOptionsView(APIView):
    def get(self, request, *args, **kwargs):
        user_id = getattr(request, "user_id", None)
        own = getattr(request, "tenant_id", None)
        if not user_id:
            return Response({"error": "unauthorized"}, status=401)
        return Response({"options": _allowed_targets(user_id, own)})


class SwitchTenantView(APIView):
    def post(self, request, *args, **kwargs):
        user_id = getattr(request, "user_id", None)
        own = getattr(request, "tenant_id", None)
        target = (request.data or {}).get("tenant_id")
        if not user_id:
            return Response({"error": "unauthorized"}, status=401)
        if not target:
            return Response({"error": "tenant_id is required"}, status=400)

        allowed = {o["tenant_id"] for o in _allowed_targets(user_id, own)}
        if target not in allowed:
            logger.warning("Denied tenant switch: user=%s target=%s", user_id, target)
            return Response({"error": "forbidden", "message": "not allowed for this account"}, status=403)

        t = Tenant.objects.filter(id=target).first()
        if not t:
            return Response({"error": "tenant not found"}, status=404)

        from django.contrib.auth import get_user_model
        user = get_user_model().objects.filter(id=user_id).first()
        if not user:
            return Response({"error": "user not found"}, status=401)

        now = datetime.datetime.utcnow()
        tier = getattr(t, "tier", "free") or "free"
        base = {"sub": str(user_id), "tenant_id": str(target), "tier": tier, "role": user.role}
        access = jwt.encode(
            {**base, "scope": "user", "iat": now,
             "exp": now + datetime.timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME)},
            settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        refresh = jwt.encode(
            {**base, "type": "refresh", "iat": now,
             "exp": now + datetime.timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)},
            settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        if isinstance(access, bytes): access = access.decode()
        if isinstance(refresh, bytes): refresh = refresh.decode()

        return Response({
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME,
            "tenant_id": target,
            "organization": t.organization or target,
            "user_id": int(user_id),
        })
