from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django import db
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# CRITICAL: Connection Cleanup Middleware
# =============================================================================
# This middleware ensures database connections are properly cleaned up after
# EVERY request to prevent "remaining connection slots" errors on Azure PostgreSQL
# =============================================================================

class ConnectionCleanupMiddleware:
    """
    Middleware that ensures database connections are closed after every request.
    This is critical for preventing connection exhaustion on Azure PostgreSQL.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Close old/stale connections before processing
        db.close_old_connections()

        response = self.get_response(request)

        # Close old connections after the request (respects CONN_MAX_AGE)
        # With CONN_MAX_AGE=0, this closes all connections
        db.close_old_connections()

        return response

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request):
        logger.debug("Processing request in TenantMiddleware")

        paths_to_skip = [
            '/login/', '/register/', '/createTenant/', '/track_open/',
            '/track_open_count/', '/track_click/', '/create_table/', '/insert-data/',
            '/get-tenant/', '/whatsapp-media-uploads/', '/verifyTenant/', '/change-password/',
            '/password_reset/', '/reset/', '/whatsapp_convo_get/', '/whatsapp_tenant',
            '/set-status/', '/update-last-seen/', '/add-key/', '/test-api/',
            '/contacts_by_tenant/', '/individual_message_statistics/', '/payments-webhook',
            '/tenant-agents/', '/flows/', '/health/','/oauth/token/'
        ]

        # if any(request.path.startswith(path) for path in paths_to_skip):
        #     logger.debug(f"Skipping tenant processing for path: {request.path}")
        #     return

        # tenant_id = request.headers.get('X-Tenant-Id')
        # if not tenant_id:
        #     logger.warning("No Tenant ID found in request headers")
        #     return HttpResponse('No Tenant ID provided', status=400)

        # try:
        #     # Verify tenant exists
        #     tenant = Tenant.objects.get(id=tenant_id)
        #     logger.debug(f"Tenant verified: {tenant}")
            
        #     # Store tenant info in request - no database changes needed
        #     request.tenant = tenant
        #     request.tenant_id = tenant_id
            
        # except Tenant.DoesNotExist:
        #     logger.error(f"Tenant does not exist for ID: {tenant_id}")
        #     return HttpResponse('Tenant does not exist', status=404)
        # except Exception as e:
        #     logger.error(f"Error verifying tenant: {e}")
        #     return HttpResponse('Error verifying tenant', status=500)


# Keep your existing LogRequestTimeMiddleware unchanged
class LogRequestTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from datetime import datetime
        timestamp = datetime.now().isoformat()
        endpoint = request.path
        log_message = f"Request received at: {timestamp} for endpoint: {endpoint}"
        print(log_message)
        logger.info(log_message)

        response = self.get_response(request)
        return response
