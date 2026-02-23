"""
Tests for the Celery gate / 3-tier save logic in interaction/views.py.
Covers: sync save, celery async, idempotency dedup, fallback on failure.
"""
import pytest
import json
import os
from unittest.mock import patch, MagicMock
from django.test import Client
from django.utils import timezone


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


def _post_conversation(client, contact, tenant, whatsapp_tenant_data, extra=None):
    """Helper to POST a conversation save request."""
    payload = {
        'conversations': [
            {'text': 'Hello', 'sender': 'user', 'message_type': 'text'},
        ],
        'tenant': tenant.id,
        'source': 'whatsapp',
        'business_phone_number_id': str(whatsapp_tenant_data.business_phone_number_id),
    }
    if extra:
        payload.update(extra)
    return client.post(
        f'/whatsapp_convo_post/{contact.id}/',
        data=json.dumps(payload),
        content_type='application/json',
    )


# ──────────────────────────────────────────────
# Sync Save (USE_CELERY disabled)
# ──────────────────────────────────────────────

class TestSyncSave:
    @patch.dict(os.environ, {'USE_CELERY': 'false'})
    @patch('interaction.views._check_idempotency', return_value=False)
    @patch('interaction.views._mark_idempotency_done')
    def test_sync_save_when_celery_disabled(
        self, mock_mark, mock_dedup, client, contact, tenant, whatsapp_tenant_data
    ):
        resp = _post_conversation(client, contact, tenant, whatsapp_tenant_data)
        assert resp.status_code == 201
        body = resp.json()
        assert body['method'] == 'sync-bulk'

    @patch.dict(os.environ, {}, clear=True)
    @patch('interaction.views._check_idempotency', return_value=False)
    @patch('interaction.views._mark_idempotency_done')
    def test_celery_disabled_by_default(
        self, mock_mark, mock_dedup, client, contact, tenant, whatsapp_tenant_data
    ):
        """No USE_CELERY env var → defaults to sync save (the bug that broke production)."""
        # Remove USE_CELERY if set
        os.environ.pop('USE_CELERY', None)
        resp = _post_conversation(client, contact, tenant, whatsapp_tenant_data)
        assert resp.status_code == 201
        body = resp.json()
        assert body['method'] == 'sync-bulk'


# ──────────────────────────────────────────────
# Celery Path (USE_CELERY enabled)
# ──────────────────────────────────────────────

class TestCelerySave:
    @patch.dict(os.environ, {'USE_CELERY': 'true'})
    @patch('interaction.views._check_idempotency', return_value=False)
    @patch('interaction.views.check_redis_health', return_value=True)
    @patch('interaction.views.process_conversations.delay')
    def test_celery_save_when_enabled(
        self, mock_delay, mock_redis, mock_dedup, client, contact, tenant, whatsapp_tenant_data
    ):
        resp = _post_conversation(client, contact, tenant, whatsapp_tenant_data)
        assert resp.status_code == 202
        body = resp.json()
        assert body['method'] == 'async'
        mock_delay.assert_called_once()

    @patch.dict(os.environ, {'USE_CELERY': 'true'})
    @patch('interaction.views._check_idempotency', return_value=False)
    @patch('interaction.views._mark_idempotency_done')
    @patch('interaction.views.check_redis_health', return_value=True)
    @patch('interaction.views.process_conversations.delay', side_effect=Exception('Redis down'))
    def test_sync_fallback_on_celery_failure(
        self, mock_delay, mock_redis, mock_mark, mock_dedup,
        client, contact, tenant, whatsapp_tenant_data
    ):
        """USE_CELERY=true but delay() raises → falls back to sync."""
        resp = _post_conversation(client, contact, tenant, whatsapp_tenant_data)
        assert resp.status_code == 201
        body = resp.json()
        assert body['method'] == 'sync-bulk'


# ──────────────────────────────────────────────
# Idempotency / Deduplication
# ──────────────────────────────────────────────

class TestIdempotency:
    @patch.dict(os.environ, {'USE_CELERY': 'false'})
    @patch('interaction.views._mark_idempotency_done')
    def test_idempotency_blocks_duplicate(
        self, mock_mark, client, contact, tenant, whatsapp_tenant_data
    ):
        """Same message_id twice → second returns 200 'deduplicated'."""
        msg_id = 'wamid.unique123'

        with patch('interaction.views._check_idempotency', return_value=False):
            resp1 = _post_conversation(
                client, contact, tenant, whatsapp_tenant_data,
                extra={'message_id': msg_id},
            )
        assert resp1.status_code == 201

        with patch('interaction.views._check_idempotency', return_value=True):
            resp2 = _post_conversation(
                client, contact, tenant, whatsapp_tenant_data,
                extra={'message_id': msg_id},
            )
        assert resp2.status_code == 200
        assert resp2.json()['method'] == 'deduplicated'

    @patch.dict(os.environ, {'USE_CELERY': 'false'})
    @patch('interaction.views._check_idempotency', return_value=False)
    @patch('interaction.views._mark_idempotency_done')
    def test_idempotency_allows_different_messages(
        self, mock_mark, mock_dedup, client, contact, tenant, whatsapp_tenant_data
    ):
        """Different message_ids both save successfully."""
        resp1 = _post_conversation(
            client, contact, tenant, whatsapp_tenant_data,
            extra={'message_id': 'wamid.aaa'},
        )
        resp2 = _post_conversation(
            client, contact, tenant, whatsapp_tenant_data,
            extra={'message_id': 'wamid.bbb'},
        )
        assert resp1.status_code == 201
        assert resp2.status_code == 201

    @patch.dict(os.environ, {'USE_CELERY': 'false'})
    @patch('interaction.views._check_idempotency', return_value=False)
    @patch('interaction.views._mark_idempotency_done')
    def test_idempotency_skipped_without_message_id(
        self, mock_mark, mock_dedup, client, contact, tenant, whatsapp_tenant_data
    ):
        """No message_id in payload → saves normally (no dedup check)."""
        resp = _post_conversation(client, contact, tenant, whatsapp_tenant_data)
        assert resp.status_code == 201

    def test_mark_idempotency_done_extends_ttl(self):
        """After save, key gets 300s TTL via _mark_idempotency_done."""
        mock_redis = MagicMock()
        with patch('interaction.views._get_dedup_redis', return_value=mock_redis):
            from interaction.views import _mark_idempotency_done
            _mark_idempotency_done('wamid.test_ttl')
            mock_redis.set.assert_called_once_with('msg:dedup:wamid.test_ttl', 'done', ex=300)
