import jwt
from django.http import JsonResponse
from django.conf import settings

EXCLUDED_PATHS = [
    "/login/",
    "/logout/",
    "/register/",
    "/oauth/token/",
    "/health/",
    "/facebook-callback/",
    "/add-dynamic-data/",
]

class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Allow unauthenticated paths
        if any(request.path.startswith(x) for x in EXCLUDED_PATHS):
            return self.get_response(request)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JsonResponse({"error": "unauthorized"}, status=401)

        token = auth.replace("Bearer ", "")

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            return JsonResponse({"error": "token_expired"}, status=401)
        except Exception:
            return JsonResponse({"error": "invalid_token"}, status=401)

        request.user_id = payload.get("sub")
        jwt_tenant_id = payload.get("tenant_id")  # extracted but not applied yet
        request.user_role = payload.get("role")
        request.scope = payload.get("scope")

        # Prefer header if available, else use JWT tenant
        request.tenant_id = request.headers.get("X-Tenant-ID", jwt_tenant_id)

        if request.scope == "service" or request.user_role == "system":
            request.is_service = True
            return self.get_response(request)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            request.user = User.objects.get(id=request.user_id)
        except User.DoesNotExist:
            return JsonResponse({"error": "user_not_found"}, status=401)

        return self.get_response(request)
