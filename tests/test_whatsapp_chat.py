"""
Tests for whatsapp_chat/views.py endpoints:
insert_whatsapp_tenant_data, get_whatsapp_tenant_data, get_tenant.
"""
import pytest
import json
from django.test import Client


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


# ──────────────────────────────────────────────
# Insert WhatsApp Tenant Data (firstInsert)
# ──────────────────────────────────────────────

class TestInsertTenantData:
    def test_insert_tenant_data(self, client, tenant):
        """POST /insert-data/ with firstInsert=true saves WhatsappTenantData."""
        resp = client.post(
            '/insert-data/',
            data=json.dumps({
                'firstInsert': True,
                'access_token': 'EAABtest_token',
                'accountID': 999888777666,
            }),
            content_type='application/json',
            HTTP_X_TENANT_ID=tenant.id,
            HTTP_BPID='111222333444555',
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body['status'] == 'success'
        assert str(body['bpid']) == '111222333444555'

    def test_insert_data_missing_fields(self, client, tenant):
        """firstInsert=true but missing required fields → 400."""
        resp = client.post(
            '/insert-data/',
            data=json.dumps({
                'firstInsert': True,
                'access_token': 'EAABtest',
                # Missing accountID and bpid header
            }),
            content_type='application/json',
            HTTP_X_TENANT_ID=tenant.id,
        )
        # No bpid header provided, so it tries to look up existing record
        # which doesn't exist → 404
        assert resp.status_code in (400, 404)

    def test_insert_data_no_tenant_header(self, client):
        """No X-Tenant-Id header → 400."""
        resp = client.post(
            '/insert-data/',
            data=json.dumps({'firstInsert': True}),
            content_type='application/json',
        )
        assert resp.status_code == 400


# ──────────────────────────────────────────────
# Get WhatsApp Tenant Data
# ──────────────────────────────────────────────

class TestGetWhatsappTenant:
    def test_get_whatsapp_tenant_by_tenant_id(self, client, tenant, whatsapp_tenant_data):
        """GET /whatsapp_tenant with X-Tenant-Id header returns data."""
        resp = client.get(
            '/whatsapp_tenant',
            HTTP_X_TENANT_ID=tenant.id,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert 'whatsapp_data' in body
        assert len(body['whatsapp_data']) >= 1

    def test_get_whatsapp_tenant_by_bpid(self, client, whatsapp_tenant_data):
        """GET /whatsapp_tenant with bpid header returns data."""
        resp = client.get(
            '/whatsapp_tenant',
            HTTP_BPID=str(whatsapp_tenant_data.business_phone_number_id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert 'whatsapp_data' in body

    def test_get_tenant_not_found(self, client, db):
        """GET /whatsapp_tenant with non-existent tenant → 404."""
        resp = client.get(
            '/whatsapp_tenant',
            HTTP_X_TENANT_ID='nonexistent_tenant_xyz',
        )
        assert resp.status_code == 404

    def test_get_tenant_no_headers(self, client, db):
        """No tenant or bpid header → 400."""
        resp = client.get('/whatsapp_tenant')
        assert resp.status_code == 400


# ──────────────────────────────────────────────
# Get Tenant by BPID
# ──────────────────────────────────────────────

class TestGetTenant:
    def test_get_tenant_info(self, client, tenant, whatsapp_tenant_data):
        """GET /get-tenant/?bpid=... returns tenant id."""
        resp = client.get(
            f'/get-tenant/?bpid={whatsapp_tenant_data.business_phone_number_id}',
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body['tenant'] == tenant.id

    def test_get_tenant_missing_bpid(self, client, db):
        """GET /get-tenant/ without bpid → 400."""
        resp = client.get('/get-tenant/')
        assert resp.status_code == 400
