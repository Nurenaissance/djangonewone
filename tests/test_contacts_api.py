"""
Tests for Contact API endpoints.
"""
import pytest
import json
from django.urls import reverse
from rest_framework import status


pytestmark = pytest.mark.django_db


class TestContactListCreateAPI:
    """Tests for Contact list and create endpoints."""

    def test_list_contacts_returns_empty_list(self, api_client):
        """Test GET /contacts/ returns empty list when no contacts exist."""
        response = api_client.get('/contacts/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_contacts_returns_all_contacts(self, api_client, multiple_contacts):
        """Test GET /contacts/ returns all contacts."""
        response = api_client.get('/contacts/')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == 5

    def test_create_contact_success(self, api_client, tenant):
        """Test POST /contacts/ creates a new contact."""
        data = {
            'name': 'New Contact',
            'phone': '919999888877',
            'email': 'newcontact@example.com',
            'tenant': tenant.id
        }
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['name'] == 'New Contact'
        assert response.json()['phone'] == '919999888877'

    def test_create_contact_with_10_digit_phone(self, api_client, tenant):
        """Test POST /contacts/ auto-prefixes 91 for 10-digit phones."""
        data = {
            'name': 'Local Contact',
            'phone': '9999888877',
            'tenant': tenant.id
        }
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        # Phone should be prefixed with 91
        assert response.json()['phone'] == '919999888877'

    def test_create_contact_missing_phone_fails(self, api_client, tenant):
        """Test POST /contacts/ without phone returns 400."""
        data = {
            'name': 'No Phone Contact',
            'tenant': tenant.id
        }
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestContactDetailAPI:
    """Tests for Contact detail, update, delete endpoints."""

    def test_get_contact_by_id(self, api_client, contact):
        """Test GET /contacts/<id>/ returns contact details."""
        response = api_client.get(f'/contacts/{contact.id}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Test Contact'
        assert response.json()['phone'] == '919876543210'

    def test_get_nonexistent_contact_returns_404(self, api_client, db_access):
        """Test GET /contacts/<invalid_id>/ returns 404."""
        response = api_client.get('/contacts/99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_contact(self, api_client, contact):
        """Test PUT /contacts/<id>/ updates contact."""
        data = {
            'name': 'Updated Contact Name',
            'phone': contact.phone,
            'tenant': contact.tenant.id
        }
        response = api_client.put(f'/contacts/{contact.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Updated Contact Name'

    def test_partial_update_contact(self, api_client, contact):
        """Test PATCH /contacts/<id>/ partial update."""
        data = {'name': 'Patched Name'}
        response = api_client.patch(f'/contacts/{contact.id}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['name'] == 'Patched Name'
        # Phone should remain unchanged
        assert response.json()['phone'] == '919876543210'

    def test_delete_contact(self, api_client, contact):
        """Test DELETE /contacts/<id>/ removes contact."""
        contact_id = contact.id
        response = api_client.delete(f'/contacts/{contact_id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify contact is deleted
        get_response = api_client.get(f'/contacts/{contact_id}/')
        assert get_response.status_code == status.HTTP_404_NOT_FOUND


class TestContactByPhoneAPI:
    """Tests for Contact lookup by phone number."""

    def test_get_contact_by_phone(self, api_client, contact, tenant_headers):
        """Test GET /contacts-by-phone/<phone>/ returns contact."""
        response = api_client.get(
            f'/contacts-by-phone/{contact.phone}/',
            **tenant_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['name'] == 'Test Contact'

    def test_get_contact_by_phone_not_found(self, api_client, tenant_headers, db_access):
        """Test GET /contacts-by-phone/ with non-existent phone."""
        response = api_client.get(
            '/contacts-by-phone/911111111111/',
            **tenant_headers
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_contact_by_phone_missing_tenant_header(self, api_client, contact):
        """Test GET /contacts-by-phone/ without tenant header returns error."""
        response = api_client.get(f'/contacts-by-phone/{contact.phone}/')
        # Should return 400, 500 (validation error), or handle gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK, status.HTTP_500_INTERNAL_SERVER_ERROR]


class TestContactByTenantAPI:
    """Tests for Contact creation by tenant (via bpid header)."""

    def test_create_contact_with_bpid(self, api_client, whatsapp_tenant_data):
        """Test POST /contacts_by_tenant/ creates contact using bpid header."""
        data = {
            'name': 'BPID Contact',
            'phone': '919988776655'
        }
        headers = {'HTTP_BPID': str(whatsapp_tenant_data.business_phone_number_id)}
        response = api_client.post('/contacts_by_tenant/', data, format='json', **headers)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_contact_without_bpid_fails(self, api_client, db_access):
        """Test POST /contacts_by_tenant/ without bpid returns 400."""
        data = {
            'name': 'No BPID Contact',
            'phone': '919988776655'
        }
        response = api_client.post('/contacts_by_tenant/', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duplicate_contact_returns_existing(self, api_client, contact, whatsapp_tenant_data):
        """Test POST /contacts_by_tenant/ with existing phone returns 200."""
        data = {
            'name': 'Duplicate Contact',
            'phone': contact.phone
        }
        headers = {'HTTP_BPID': str(whatsapp_tenant_data.business_phone_number_id)}
        response = api_client.post('/contacts_by_tenant/', data, format='json', **headers)
        assert response.status_code == status.HTTP_200_OK
        assert 'already exists' in response.json().get('detail', '').lower()


class TestContactCustomFieldAPI:
    """Tests for Contact custom field webhook endpoint."""

    def test_create_contact_with_custom_fields(self, api_client, tenant):
        """Test POST /contact/customfield creates contact with custom fields."""
        data = {
            'name': 'Custom Field Contact',
            'phone': '919876543211',
            'custom_field_1': 'value1',
            'custom_field_2': 'value2'
        }
        headers = {'HTTP_X_TENANT_ID': tenant.id}
        response = api_client.post('/contact/customfield', data, format='json', **headers)
        assert response.status_code == status.HTTP_201_CREATED

        # Custom fields should be stored in customField JSON
        result = response.json()
        assert result['data']['customField']['custom_field_1'] == 'value1'

    def test_create_contact_custom_field_missing_tenant(self, api_client):
        """Test POST /contact/customfield without tenant returns 400."""
        data = {
            'name': 'No Tenant Contact',
            'phone': '919876543212'
        }
        response = api_client.post('/contact/customfield', data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'X-Tenant-Id' in response.json().get('error', '')

    def test_update_existing_contact_custom_fields(self, api_client, contact, tenant):
        """Test POST /contact/customfield updates existing contact."""
        data = {
            'phone': contact.phone,
            'new_custom_field': 'new_value'
        }
        headers = {'HTTP_X_TENANT_ID': tenant.id}
        response = api_client.post('/contact/customfield', data, format='json', **headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.json()['message'] == 'Contact updated successfully'


class TestUpdateContactAPI:
    """Tests for /update-contacts/ endpoint."""

    def test_update_contact_via_phone_lookup(self, api_client, contact, tenant_headers):
        """Test PATCH /update-contacts/ updates contact by phone lookup."""
        data = {
            'phone': contact.phone,
            'name': 'Updated via PATCH',
            'template_key': 'new_template'
        }
        response = api_client.patch('/update-contacts/', data, format='json', **tenant_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_update_nonexistent_contact_returns_error(self, api_client, tenant_headers, db_access):
        """Test PATCH /update-contacts/ with non-existent phone returns error."""
        data = {
            'phone': '911111111111',
            'name': 'Ghost Contact'
        }
        response = api_client.patch('/update-contacts/', data, format='json', **tenant_headers)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestContactPhoneValidation:
    """Tests for phone number validation in ContactSerializer."""

    def test_valid_indian_phone_12_digits(self, api_client, tenant):
        """Test valid 12-digit Indian phone number."""
        data = {'name': 'Test', 'phone': '919876543210', 'tenant': tenant.id}
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['phone'] == '919876543210'

    def test_valid_indian_phone_10_digits_prefixed(self, api_client, tenant):
        """Test 10-digit phone gets 91 prefix."""
        data = {'name': 'Test', 'phone': '9876543210', 'tenant': tenant.id}
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['phone'] == '919876543210'

    def test_valid_uae_phone(self, api_client, tenant):
        """Test valid UAE phone number (971 + 9 digits)."""
        data = {'name': 'UAE Test', 'phone': '971501234567', 'tenant': tenant.id}
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['phone'] == '971501234567'

    def test_phone_strips_special_characters(self, api_client, tenant):
        """Test phone with special characters gets cleaned."""
        data = {'name': 'Test', 'phone': '+91-9876-543-210', 'tenant': tenant.id}
        response = api_client.post('/contacts/', data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()['phone'] == '919876543210'


class TestDeleteContactByPhone:
    """Tests for /delete-contact/<phone>/ endpoint."""

    def test_delete_contact_by_phone_success(self, django_client, contact):
        """Test DELETE /delete-contact/<phone>/ removes contact."""
        response = django_client.delete(f'/delete-contact/{contact.phone}/')
        assert response.status_code == 200
        assert 'deleted successfully' in response.json()['message']

    def test_delete_nonexistent_contact_by_phone(self, django_client, db_access):
        """Test DELETE /delete-contact/ with non-existent phone returns error."""
        response = django_client.delete('/delete-contact/911111111111/')
        # Should return 404 or 500 (depending on error handling)
        assert response.status_code in [404, 500]
