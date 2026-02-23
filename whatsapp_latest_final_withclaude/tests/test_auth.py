"""
Tests for authentication endpoints: register, login, logout, invite codes, change password.
Covers simplecrm/Register_login.py views.
"""
import pytest
import json
from django.test import Client


pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    return Client()


# ──────────────────────────────────────────────
# Register Tenant
# ──────────────────────────────────────────────

class TestRegisterTenant:
    def test_register_tenant_success(self, client):
        resp = client.post(
            '/register-tenant/',
            data=json.dumps({'email': 'new@example.com', 'password': 'Str0ngP@ss'}),
            content_type='application/json',
        )
        assert resp.status_code == 200
        body = resp.json()
        assert 'tenant_id' in body
        assert body['msg'] == 'Tenant and admin user created successfully'

    def test_register_tenant_duplicate_email(self, client):
        # First registration
        client.post(
            '/register-tenant/',
            data=json.dumps({'email': 'dup@example.com', 'password': 'Pass1234'}),
            content_type='application/json',
        )
        # Second registration with same email
        resp = client.post(
            '/register-tenant/',
            data=json.dumps({'email': 'dup@example.com', 'password': 'Pass1234'}),
            content_type='application/json',
        )
        assert resp.status_code == 400
        assert 'already registered' in resp.json()['msg'].lower()

    def test_register_tenant_missing_fields(self, client):
        resp = client.post(
            '/register-tenant/',
            data=json.dumps({'email': 'no_pass@example.com'}),
            content_type='application/json',
        )
        assert resp.status_code == 400


# ──────────────────────────────────────────────
# Login
# ──────────────────────────────────────────────

class TestLogin:
    def test_login_success(self, client, test_user):
        resp = client.post(
            '/login/',
            data=json.dumps({'username': 'testuser', 'password': 'testpassword123'}),
            content_type='application/json',
        )
        assert resp.status_code == 200
        body = resp.json()
        assert 'access_token' in body
        assert 'refresh_token' in body
        assert body['tenant_id'] == test_user.tenant.id

    def test_login_wrong_password(self, client, test_user):
        resp = client.post(
            '/login/',
            data=json.dumps({'username': 'testuser', 'password': 'wrongpassword'}),
            content_type='application/json',
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user(self, client, db):
        resp = client.post(
            '/login/',
            data=json.dumps({'username': 'nobody', 'password': 'pass'}),
            content_type='application/json',
        )
        assert resp.status_code == 401


# ──────────────────────────────────────────────
# Logout
# ──────────────────────────────────────────────

class TestLogout:
    def test_logout_success(self, client, tenant):
        resp = client.post(
            '/logout/',
            content_type='application/json',
            HTTP_X_TENANT_ID=tenant.id,
        )
        assert resp.status_code == 200
        assert resp.json()['msg'] == 'Logout successful'


# ──────────────────────────────────────────────
# Unified Registration (invite codes)
# ──────────────────────────────────────────────

class TestRegisterUnified:
    def test_register_with_invite_code(self, client, tenant, admin_user):
        from tenant.models import InviteCode
        invite = InviteCode.objects.create(
            code='TESTJOIN',
            tenant=tenant,
            created_by=admin_user,
            role='employee',
        )
        resp = client.post(
            '/register-unified/',
            data=json.dumps({
                'mode': 'join',
                'username': 'invited_user',
                'email': 'invited@example.com',
                'password': 'InvitedPass1',
                'invite_code': 'TESTJOIN',
            }),
            content_type='application/json',
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body['tenant_id'] == tenant.id
        assert body['role'] == 'employee'
        # Verify use_count incremented
        invite.refresh_from_db()
        assert invite.use_count == 1

    def test_register_invalid_invite_code(self, client, db):
        resp = client.post(
            '/register-unified/',
            data=json.dumps({
                'mode': 'join',
                'username': 'bad_invite',
                'email': 'bad@example.com',
                'password': 'Pass1234',
                'invite_code': 'INVALID9',
            }),
            content_type='application/json',
        )
        assert resp.status_code == 400


# ──────────────────────────────────────────────
# Change Password
# ──────────────────────────────────────────────

class TestChangePassword:
    def test_change_password(self, client, test_user):
        resp = client.post(
            '/change-password/',
            data=json.dumps({
                'username': 'testuser',
                'newPassword': 'NewStrongPass99',
            }),
            content_type='application/json',
        )
        assert resp.status_code == 200
        # Verify new password works via Django authenticate
        from django.contrib.auth import authenticate
        user = authenticate(username='testuser', password='NewStrongPass99')
        assert user is not None
        assert user.username == 'testuser'
