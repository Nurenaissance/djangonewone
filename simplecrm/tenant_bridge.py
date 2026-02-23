from django.http import JsonResponse

class TenantBridgeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant = getattr(request, "tenant_id", None)

        # Only inject if header not already present
        if tenant and "HTTP_X_TENANT_ID" not in request.META:
            request.META["HTTP_X_TENANT_ID"] = str(tenant)
            request.headers._store["x-tenant-id"] = ("X-Tenant-ID", str(tenant))

        return self.get_response(request)


