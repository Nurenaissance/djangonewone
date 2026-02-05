"""
Shared pytest fixtures for Django test suite.
"""
import pytest
import json
import os
from datetime import datetime, timedelta
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock


# ==============================================================================
# Database Fixtures
# ==============================================================================

@pytest.fixture
def db_access(db):
    """Allow database access for tests."""
    pass


@pytest.fixture
def tenant(db):
    """Create a test tenant."""
    from tenant.models import Tenant

    tenant = Tenant.objects.create(
        id='test_tenant_001',
        organization='Test Organization',
        db_user='test_user',
        db_user_password='test_password',
        tier='pro',
        key=os.urandom(32)  # AES-256 key for encryption
    )
    return tenant


@pytest.fixture
def another_tenant(db):
    """Create a second test tenant for multi-tenant tests."""
    from tenant.models import Tenant

    tenant = Tenant.objects.create(
        id='test_tenant_002',
        organization='Another Organization',
        db_user='another_user',
        db_user_password='another_password',
        tier='basic',
        key=os.urandom(32)
    )
    return tenant


@pytest.fixture
def test_user(db, tenant):
    """Create a test user associated with a tenant."""
    from simplecrm.models import CustomUser

    user = CustomUser.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpassword123',
        tenant=tenant,
        organization=tenant.organization,
        role='employee'
    )
    return user


@pytest.fixture
def admin_user(db, tenant):
    """Create an admin user for testing admin-only endpoints."""
    from simplecrm.models import CustomUser

    user = CustomUser.objects.create_superuser(
        username='adminuser',
        email='admin@example.com',
        password='adminpassword123',
        tenant=tenant,
        organization=tenant.organization,
        role='admin'
    )
    return user


# ==============================================================================
# Contact Fixtures
# ==============================================================================

@pytest.fixture
def contact(db, tenant):
    """Create a test contact."""
    from contacts.models import Contact

    contact = Contact.objects.create(
        name='Test Contact',
        phone='919876543210',
        email='test@example.com',
        address='123 Test Street',
        tenant=tenant,
        isActive=True,
        customField={'source': 'test', 'category': 'vip'}
    )
    return contact


@pytest.fixture
def contact_without_country_code(db, tenant):
    """Create a contact with 10-digit phone number."""
    from contacts.models import Contact

    contact = Contact.objects.create(
        name='Local Contact',
        phone='9876543210',
        tenant=tenant,
        isActive=True
    )
    return contact


@pytest.fixture
def multiple_contacts(db, tenant):
    """Create multiple test contacts."""
    from contacts.models import Contact

    contacts = []
    for i in range(5):
        contact = Contact.objects.create(
            name=f'Contact {i+1}',
            phone=f'9198765432{i:02d}',
            email=f'contact{i+1}@example.com',
            tenant=tenant,
            isActive=True
        )
        contacts.append(contact)
    return contacts


# ==============================================================================
# WhatsApp Tenant Data Fixtures
# ==============================================================================

@pytest.fixture
def whatsapp_tenant_data(db, tenant):
    """Create WhatsApp tenant configuration."""
    from whatsapp_chat.models import WhatsappTenantData

    wtd = WhatsappTenantData.objects.create(
        business_phone_number_id=123456789012345,
        tenant=tenant,
        access_token='test_access_token',
        business_account_id=987654321098765,
        flow_version=2
    )
    return wtd


# ==============================================================================
# API Client Fixtures
# ==============================================================================

@pytest.fixture
def api_client():
    """Return DRF API test client."""
    return APIClient()


@pytest.fixture
def django_client():
    """Return Django test client."""
    return Client()


@pytest.fixture
def tenant_headers(tenant):
    """Return headers with tenant ID for API requests."""
    return {'HTTP_X_TENANT_ID': tenant.id}


@pytest.fixture
def authenticated_client(api_client, test_user):
    """Return an authenticated API client."""
    api_client.force_authenticate(user=test_user)
    return api_client


# ==============================================================================
# Conversation/Message Fixtures
# ==============================================================================

@pytest.fixture
def conversation_payload(contact, tenant, whatsapp_tenant_data):
    """Create a sample conversation payload."""
    return {
        'contact_id': str(contact.id),
        'conversations': [
            {'text': 'Hello, how can I help?', 'sender': 'bot', 'message_type': 'text'},
            {'text': 'I need support', 'sender': 'user', 'message_type': 'text'},
        ],
        'tenant': tenant.id,
        'source': 'whatsapp',
        'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
    }


@pytest.fixture
def conversation(db, contact, tenant, whatsapp_tenant_data):
    """Create a test conversation entry."""
    from interaction.models import Conversation

    conv = Conversation.objects.create(
        contact_id=str(contact.id),
        message_text='Test message',
        sender='user',
        tenant=tenant,
        source='whatsapp',
        business_phone_number_id=str(whatsapp_tenant_data.business_phone_number_id),
        date_time=timezone.now(),
        message_type='text'
    )
    return conv


# ==============================================================================
# Mock Fixtures
# ==============================================================================

@pytest.fixture
def mock_redis():
    """Mock Redis connection for tests that don't need real Redis."""
    with patch('redis.from_url') as mock:
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock.return_value = mock_redis_instance
        yield mock_redis_instance


@pytest.fixture
def mock_celery():
    """Mock Celery for tests that don't need actual task queue."""
    with patch('interaction.tasks.process_conversations.delay') as mock:
        yield mock


@pytest.fixture
def mock_redis_unhealthy():
    """Mock Redis as unhealthy (connection failure)."""
    with patch('interaction.views.check_redis_health') as mock:
        mock.return_value = False
        yield mock


# ==============================================================================
# Interview Fixtures
# ==============================================================================

@pytest.fixture
def interview(db, tenant, contact):
    """Create a test interview."""
    from interviews.models import Interview

    interview = Interview.objects.create(
        tenant=tenant,
        contact=contact,
        status='pending',
        scheduled_at=timezone.now() + timedelta(hours=1)
    )
    return interview


# ==============================================================================
# Utility Fixtures
# ==============================================================================

@pytest.fixture
def sample_phone_numbers():
    """Return various phone number formats for testing phone validation."""
    return {
        'valid_indian': ['919876543210', '9876543210', '+919876543210'],
        'valid_uae': ['971501234567'],
        'invalid': ['123', 'abcdefghij', '', None, '12345678901234567890']
    }


@pytest.fixture
def freeze_time():
    """Fixture for freezing time in tests."""
    from freezegun import freeze_time
    return freeze_time


@pytest.fixture
def json_headers():
    """Return JSON content-type headers."""
    return {'content_type': 'application/json'}


# ==============================================================================
# Cleanup Fixtures
# ==============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test(request):
    """Cleanup fixture that runs after each test."""
    yield
    # Add any cleanup logic here if needed


# ==============================================================================
# Settings Override Fixtures
# ==============================================================================

@pytest.fixture
def override_debug_true(settings):
    """Override DEBUG setting to True."""
    settings.DEBUG = True


@pytest.fixture
def override_debug_false(settings):
    """Override DEBUG setting to False."""
    settings.DEBUG = False
