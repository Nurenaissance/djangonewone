"""
Custom throttling classes for Django REST Framework.

These throttling classes implement rate limiting to prevent API abuse
and ensure fair usage across all clients.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle, SimpleRateThrottle


class BurstRateThrottle(UserRateThrottle):
    """
    Limits short-term burst requests.
    Default: 60 requests per minute for authenticated users.
    """
    scope = 'burst'


class SustainedRateThrottle(UserRateThrottle):
    """
    Limits sustained usage over longer periods.
    Default: 1000 requests per day for authenticated users.
    """
    scope = 'sustained'


class AnonBurstRateThrottle(AnonRateThrottle):
    """
    Limits burst requests from anonymous users.
    Default: 20 requests per minute.
    """
    scope = 'anon_burst'


class AnonSustainedRateThrottle(AnonRateThrottle):
    """
    Limits sustained requests from anonymous users.
    Default: 200 requests per day.
    """
    scope = 'anon_sustained'


class ContactAPIThrottle(SimpleRateThrottle):
    """
    Custom throttle for contact-related endpoints.
    Higher limits for essential contact operations.
    """
    scope = 'contacts'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class WebhookThrottle(SimpleRateThrottle):
    """
    Throttle for webhook endpoints.
    Higher limits as webhooks are typically automated.
    """
    scope = 'webhook'

    def get_cache_key(self, request, view):
        # Use business_phone_number_id for webhook identification if available
        bpid = request.headers.get('bpid') or request.data.get('business_phone_number_id')
        if bpid:
            ident = f"bpid:{bpid}"
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class TenantRateThrottle(SimpleRateThrottle):
    """
    Per-tenant rate limiting.
    Throttles based on X-Tenant-Id header to ensure fair usage per tenant.
    """
    scope = 'tenant'

    def get_cache_key(self, request, view):
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            # Fall back to user or IP
            if request.user and request.user.is_authenticated:
                ident = f"user:{request.user.pk}"
            else:
                ident = self.get_ident(request)
        else:
            ident = f"tenant:{tenant_id}"

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class ConversationSaveThrottle(SimpleRateThrottle):
    """
    Throttle for conversation save endpoint.
    Protects against flood attacks while allowing normal message flow.
    """
    scope = 'conversation_save'

    def get_cache_key(self, request, view):
        # Use contact_id from URL for more granular control
        contact_id = view.kwargs.get('contact_id', '')
        bpid = request.data.get('business_phone_number_id', '')

        if contact_id and bpid:
            ident = f"conv:{bpid}:{contact_id}"
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class InterviewAPIThrottle(SimpleRateThrottle):
    """
    Throttle for interview submission endpoints.
    Prevents automated submission abuse.
    """
    scope = 'interview'

    def get_cache_key(self, request, view):
        # Throttle by phone number if available
        phone = request.data.get('phone_no') or request.data.get('phone')
        if phone:
            ident = f"phone:{phone}"
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


# Throttle rates configuration for settings.py:
#
# REST_FRAMEWORK = {
#     'DEFAULT_THROTTLE_RATES': {
#         'burst': '60/min',
#         'sustained': '1000/day',
#         'anon_burst': '20/min',
#         'anon_sustained': '200/day',
#         'contacts': '120/min',
#         'webhook': '300/min',
#         'tenant': '500/min',
#         'conversation_save': '100/min',
#         'interview': '30/min',
#     }
# }
