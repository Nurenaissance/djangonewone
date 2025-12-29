import jwt, datetime, json
from django.http import JsonResponse
from django.contrib.auth import authenticate
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from tenant.models import Tenant  # <-- Ensure this import exists


@csrf_exempt
def oauth_token(request):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    try:
        body = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({"error": "invalid_json"}, status=400)

    grant_type = body.get("grant_type")

    # ----------------- LOGIN FLOW -----------------
    if grant_type == "password":
        user = authenticate(
            username=body.get("username"),
            password=body.get("password")
        )

        if not user:
            return JsonResponse({"error": "invalid_credentials"}, status=401)

        tenant_id = getattr(user, "tenant_id", None)
        
        # 🔥 Fetch Tier
        try:
            tenant_obj = Tenant.objects.get(id=tenant_id)
            tier = tenant_obj.tier
        except Tenant.DoesNotExist:
            tier = "free"

        access_payload = {
            "sub": str(user.id),
            "tenant_id": str(tenant_id),
            "tier": tier,                # ⬅ Added
            "scope": "user",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME)
        }

        refresh_payload = {
            "sub": str(user.id),
            "tenant_id": str(tenant_id),
            "tier": tier,                # ⬅ Added to refresh too
            "type": "refresh",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        }

        return JsonResponse({
            "access_token": jwt.encode(access_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM),
            "refresh_token": jwt.encode(refresh_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM),
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME
        })

    # ----------------- REFRESH TOKEN FLOW -----------------
    if grant_type == "refresh_token":
        try:
            payload = jwt.decode(body.get("refresh_token"), settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except:
            return JsonResponse({"error": "invalid_refresh_token"}, status=401)

        access_payload = {
            "sub": payload["sub"],
            "tenant_id": payload["tenant_id"],
            "tier": payload.get("tier", "free"),  # ⬅ Persist tier across refresh
            "scope": "user",
            "exp": datetime.datetime.utcnow() + datetime.timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME)
        }

        return JsonResponse({
            "access_token": jwt.encode(access_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM),
            "token_type": "Bearer",
            "expires_in": settings.JWT_ACCESS_TOKEN_LIFETIME
        })

    return JsonResponse({"error": "unsupported_grant_type"}, status=400)
