import jwt
import os
import logging
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger(__name__)

# Load service keys from environment
SERVICE_KEYS = {
    'django': os.getenv('DJANGO_SERVICE_KEY'),
    'fastapi': os.getenv('FASTAPI_SERVICE_KEY'),
    'nodejs': os.getenv('NODEJS_SERVICE_KEY'),
}

EXCLUDED_PATHS = [
    "/login/",
    "/logout/",
    "/register/",
    "/register-tenant/",
    "/register-unified/",
    "/register-google/",
    "/login-google/",
    "/validate-invite-code/",
    "/oauth/token/",
    "/health/",
    "/facebook-callback/",
    # "/add-dynamic-data/" removed: legitimate callers (Node via setupAuth, n8n
    # via X-Api-Key) authenticate; blanket bypass let any anonymous client write
    # to any tenant via X-Tenant-Id header.
    "/admin/",  # Django admin uses its own auth
    "/interviews/import-from-chat/",  # Public endpoint for chat import
    "/interviews/public/submit/",  # Public interview submission from web form
    "/interviews/public/employee-upload/",  # Naad 2.0 employee audio upload (replaces frontend-direct-to-Azure)
    "/interviews/public/candidate-upload/",  # Naad 2.0 candidate per-part audio upload
    "/interviews/public/finalize/",  # Naad 2.0 candidate flow finalize (records DB row from uploaded URLs)
]

# Origins that bypass authentication (trusted internal services)
BYPASS_AUTH_ORIGINS = [
    'https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net'
]

# Trusted source identifiers (for X-Trusted-Source header)
TRUSTED_SOURCES = [
    'nurenaiautomatic'
]

# Simple API key for n8n bypass (easier to configure than service keys)
N8N_API_KEY = 'n8n-nuren-2026'

def is_trusted_request(request):
    """Check if request is from a trusted source via multiple methods"""
    # Check simple X-Api-Key header (easiest for n8n)
    api_key = request.META.get('HTTP_X_API_KEY', '')
    if api_key == N8N_API_KEY:
        return True

    # Check query parameter ?api_key=xxx
    api_key_param = request.GET.get('api_key', '')
    if api_key_param == N8N_API_KEY:
        return True

    # Check Origin header
    origin = request.META.get('HTTP_ORIGIN', '')
    if any(origin.startswith(allowed) for allowed in BYPASS_AUTH_ORIGINS):
        return True

    # Check Referer header
    referer = request.META.get('HTTP_REFERER', '')
    if any(referer.startswith(allowed) for allowed in BYPASS_AUTH_ORIGINS):
        return True

    # Check custom X-Trusted-Source header
    trusted_source = request.META.get('HTTP_X_TRUSTED_SOURCE', '')
    if trusted_source in TRUSTED_SOURCES:
        return True

    return False

def is_valid_service_key(api_key):
    """
    Check if API key is a valid service key
    Returns: (is_valid, service_name)
    """
    for service_name, key in SERVICE_KEYS.items():
        if key and api_key == key:
            return True, service_name
    return False, None

class JWTAuthMiddleware:
    """
    Enhanced JWT middleware supporting dual authentication:
    1. Service-to-service authentication (X-Service-Key header)
    2. User JWT authentication (Authorization: Bearer token)
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        """
        Authentication priority:
        0. Allow CORS preflight (OPTIONS) so the CORS middleware can answer it.
           Preflights never carry credentials by spec — applying JWT auth here
           breaks every cross-origin POST/PUT/DELETE from the browser.
        1. Check if route is public → Allow
        2. Check for service API key → Allow (service-level access)
        3. Check for user JWT token → Validate and allow
        4. Reject request
        """
        # 0. Always let CORS preflights through to the CORS middleware
        if request.method == "OPTIONS":
            return self.get_response(request)

        # 1. Allow unauthenticated/public paths
        if any(request.path.startswith(x) for x in EXCLUDED_PATHS):
            return self.get_response(request)

        # 2. Allow requests from trusted origins (bypass auth)
        if is_trusted_request(request):
            request.is_trusted_origin = True
            logger.info(f"✅ Request from trusted source - bypassing auth")
            return self.get_response(request)

        # 3. Check for Service API Key (X-Service-Key header)
        service_key = request.META.get('HTTP_X_SERVICE_KEY')

        if service_key:
            is_valid, service_name = is_valid_service_key(service_key)

            if is_valid:
                # Valid service request
                request.is_service_request = True
                request.service_name = service_name

                # Get tenant context if provided
                tenant_id = request.META.get('HTTP_X_TENANT_ID')
                if tenant_id:
                    request.tenant_id = tenant_id

                logger.info(f"✅ Service request from: {service_name} (tenant: {tenant_id or 'none'})")
                return self.get_response(request)
            else:
                logger.warning(f"❌ Invalid service key attempted from {request.META.get('REMOTE_ADDR')}")
                return JsonResponse(
                    {'error': 'forbidden', 'message': 'Invalid service key'},
                    status=403
                )

        # 3. Check for User JWT Token (Authorization header)
        auth = request.headers.get("Authorization", "")

        if not auth.startswith("Bearer "):
            return JsonResponse(
                {"error": "unauthorized", "message": "Authorization token missing"},
                status=401
            )

        token = auth.replace("Bearer ", "")

        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )

            request.user_id = payload.get("sub")
            jwt_tenant_id = payload.get("tenant_id")
            request.user_role = payload.get("role")
            request.scope = payload.get("scope")
            request.is_service_request = False

            # Tenant precedence:
            # - JWT claim is authoritative for user requests (prevents header-spoofing
            #   a different tenant).
            # - Header is only used when the JWT carries no claim (legacy clients).
            # - Mismatch between header and claim is logged but does NOT override.
            header_tenant_id = request.headers.get("X-Tenant-ID")
            if header_tenant_id and jwt_tenant_id and header_tenant_id != jwt_tenant_id:
                logger.warning(
                    "Tenant header/JWT mismatch: header=%s jwt=%s user=%s (using JWT)",
                    header_tenant_id, jwt_tenant_id, request.user_id,
                )
            request.tenant_id = jwt_tenant_id or header_tenant_id

            # Handle system/service scope from JWT
            if request.scope == "service" or request.user_role == "system":
                request.is_service = True
                return self.get_response(request)

            # Load user for regular user requests
            from django.contrib.auth import get_user_model
            User = get_user_model()

            try:
                request.user = User.objects.get(id=request.user_id)
            except User.DoesNotExist:
                return JsonResponse(
                    {"error": "user_not_found"},
                    status=401
                )

            return self.get_response(request)

        except jwt.ExpiredSignatureError:
            # Trusted origins must still present a non-expired token. Previously
            # we accepted any expired token from a trusted origin, which made the
            # origin allowlist a full auth bypass. Surface a clearer error so the
            # caller knows to refresh, but never trust an expired credential.
            logger.warning(
                "Expired JWT (trusted_origin=%s)", is_trusted_request(request)
            )
            return JsonResponse(
                {"error": "token_expired", "message": "Access token has expired"},
                status=401
            )
        except jwt.InvalidTokenError as e:
            logger.warning(
                "Invalid JWT (trusted_origin=%s): %s",
                is_trusted_request(request), str(e),
            )
            return JsonResponse(
                {"error": "invalid_token", "message": "Invalid token"},
                status=401
            )
        except Exception as e:
            logger.error(
                "Unexpected error in JWT middleware (trusted_origin=%s): %s",
                is_trusted_request(request), str(e),
            )
            return JsonResponse(
                {"error": "authentication_error", "message": "Authentication failed"},
                status=401
            )
