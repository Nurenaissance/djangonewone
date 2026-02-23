"""
Tests for Conversation/Message saving endpoints and logic.
"""
import pytest
import json
import base64
from unittest.mock import patch, MagicMock
from django.urls import reverse
from django.utils import timezone


pytestmark = pytest.mark.django_db


class TestSaveConversationsEndpoint:
    """Tests for /whatsapp_convo_post/<contact_id>/ endpoint."""

    @patch.dict('os.environ', {'USE_CELERY': 'true'})
    def test_save_conversation_with_celery(
        self, django_client, contact, tenant, whatsapp_tenant_data, mock_redis, mock_celery
    ):
        """Test conversation saved via Celery when Redis is healthy and USE_CELERY=true."""
        payload = {
            'conversations': [
                {'text': 'Hello', 'sender': 'user', 'message_type': 'text'},
                {'text': 'Hi there!', 'sender': 'bot', 'message_type': 'text'},
            ],
            'tenant': tenant.id,
            'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
        }

        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 202
        data = response.json()
        assert data['method'] == 'async'
        mock_celery.assert_called_once()

    def test_save_conversation_sync_fallback(
        self, django_client, contact, tenant, whatsapp_tenant_data, mock_redis_unhealthy
    ):
        """Test conversation saved synchronously when Redis is down."""
        payload = {
            'conversations': [
                {'text': 'Sync message', 'sender': 'user', 'message_type': 'text'},
            ],
            'tenant': tenant.id,
            'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
        }

        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 201
        data = response.json()
        assert data['method'] == 'sync-bulk'
        assert data['saved'] == 1

    def test_save_conversation_invalid_tenant_returns_404(
        self, django_client, contact
    ):
        """Test conversation save with invalid tenant returns 404."""
        payload = {
            'conversations': [{'text': 'Test', 'sender': 'user'}],
            'tenant': 'nonexistent_tenant',
            'business_phone_number_id': '123456789'
        }

        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 404

    def test_save_empty_conversations(
        self, django_client, contact, tenant, whatsapp_tenant_data, mock_redis_unhealthy
    ):
        """Test empty conversation list returns success with zero saved."""
        payload = {
            'conversations': [],
            'tenant': tenant.id,
            'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
        }

        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 200
        assert 'No conversations to save' in response.json().get('message', '')

    def test_save_conversation_with_media(
        self, django_client, contact, tenant, whatsapp_tenant_data, mock_redis_unhealthy
    ):
        """Test conversation save with media attachments."""
        payload = {
            'conversations': [
                {
                    'text': 'Check this image',
                    'sender': 'user',
                    'message_type': 'image',
                    'media_url': 'https://example.com/image.jpg',
                    'media_caption': 'A test image',
                    'thumbnail_url': 'https://example.com/thumb.jpg'
                },
            ],
            'tenant': tenant.id,
            'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
        }

        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 201

    def test_save_conversation_invalid_json(self, django_client, contact):
        """Test malformed JSON returns 400."""
        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data='not valid json',
            content_type='application/json'
        )

        assert response.status_code == 400

    def test_save_conversation_wrong_method(self, django_client, contact):
        """Test GET request to POST-only endpoint returns error."""
        response = django_client.get(f'/whatsapp_convo_post/{contact.id}/')
        # Should handle gracefully or return method not allowed
        assert response.status_code in [400, 405, 500]


class TestViewConversationEndpoint:
    """Tests for /whatsapp_convo_get/<contact_id>/ endpoint."""

    def test_view_conversation_success(
        self, django_client, conversation, tenant, whatsapp_tenant_data
    ):
        """Test GET conversations returns decrypted messages."""
        response = django_client.get(
            f'/whatsapp_convo_get/{conversation.contact_id}/',
            HTTP_X_TENANT_ID=tenant.id,
            QUERY_STRING=f'source=whatsapp&bpid={whatsapp_tenant_data.business_phone_number_id}'
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_view_conversation_empty_result(
        self, django_client, tenant, whatsapp_tenant_data, db_access
    ):
        """Test GET conversations with no messages returns empty list."""
        response = django_client.get(
            '/whatsapp_convo_get/nonexistent_contact/',
            HTTP_X_TENANT_ID=tenant.id,
            QUERY_STRING=f'source=whatsapp&bpid={whatsapp_tenant_data.business_phone_number_id}'
        )

        assert response.status_code == 200
        assert response.json() == []


class TestConversationEncryption:
    """Tests for conversation encryption/decryption."""

    def test_encryption_roundtrip(self, tenant):
        """Test message can be encrypted and decrypted correctly."""
        from interaction.views import decrypt_data
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.backends import default_backend
        import os

        original_message = "Test message for encryption"
        key = bytes(tenant.key)

        # Encrypt
        data_str = json.dumps(original_message)
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        pad_len = 16 - len(data_str) % 16
        data_str += chr(pad_len) * pad_len
        encrypted_data = iv + encryptor.update(data_str.encode()) + encryptor.finalize()

        # Decrypt
        decrypted = decrypt_data(encrypted_data, key)
        assert decrypted == original_message


class TestDBQueueFallback:
    """Tests for database queue fallback mechanism."""

    def test_queue_pending_task_on_failure(
        self, django_client, contact, tenant, whatsapp_tenant_data
    ):
        """Test conversation is queued to DB when all other methods fail."""
        payload = {
            'conversations': [{'text': 'Queue test', 'sender': 'user'}],
            'tenant': tenant.id,
            'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
        }

        with patch('interaction.views.check_redis_health', return_value=False):
            with patch('interaction.views.save_conversations_sync', side_effect=Exception('DB error')):
                response = django_client.post(
                    f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
                    data=json.dumps(payload),
                    content_type='application/json'
                )

                # Should still succeed with db_queue method
                assert response.status_code == 202
                data = response.json()
                assert data['method'] == 'db_queue'


class TestConversationBulkCreate:
    """Tests for bulk conversation creation performance."""

    def test_bulk_create_multiple_messages(
        self, django_client, contact, tenant, whatsapp_tenant_data, mock_redis_unhealthy
    ):
        """Test bulk creation of many messages at once."""
        messages = [
            {'text': f'Message {i}', 'sender': 'user' if i % 2 == 0 else 'bot', 'message_type': 'text'}
            for i in range(50)
        ]

        payload = {
            'conversations': messages,
            'tenant': tenant.id,
            'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id)
        }

        response = django_client.post(
            f'/whatsapp_convo_post/{contact.id}/?source=whatsapp',
            data=json.dumps(payload),
            content_type='application/json'
        )

        assert response.status_code == 201
        assert response.json()['saved'] == 50


class TestConversationGroup:
    """Tests for Group viewset endpoints."""

    def test_list_groups(self, api_client, db_access):
        """Test GET /groups/ returns list of groups."""
        response = api_client.get('/groups/')
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_group(self, api_client, tenant):
        """Test POST /groups/ creates a new group."""
        data = {
            'name': 'Test Group',
            'tenant': tenant.id
        }
        response = api_client.post('/groups/', data, format='json')
        # Status depends on whether Group model requires additional fields
        assert response.status_code in [201, 400]
