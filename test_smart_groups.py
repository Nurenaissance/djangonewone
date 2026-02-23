"""
Test script for Smart Groups functionality
Tests the auto-sync feature when creating smart groups with rules
"""

import requests
import json
from datetime import datetime
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# API Configuration
FASTAPI_URL = "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net"
# FASTAPI_URL = "http://localhost:8000"  # Uncomment for local testing

# Test tenant ID (replace with your actual tenant ID)
TENANT_ID = "test_tenant_123"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_create_smart_group():
    """Test 1: Create a smart group with auto-rules"""
    print_section("TEST 1: Create Smart Group with Auto-Rules")

    payload = {
        "name": f"Test Smart Group {datetime.now().strftime('%H%M%S')}",
        "members": [],
        "auto_rules": {
            "enabled": True,
            "logic": "AND",
            "conditions": [
                {
                    "type": "text",
                    "field": "name",
                    "operator": "contains",
                    "value": "test"
                }
            ]
        }
    }

    headers = {
        "X-Tenant-Id": TENANT_ID,
        "Content-Type": "application/json"
    }

    print(f"\n[>>] Sending request to: {FASTAPI_URL}/broadcast-groups/")
    print(f"[DATA] Payload: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            f"{FASTAPI_URL}/broadcast-groups/",
            json=payload,
            headers=headers,
            timeout=10
        )

        print(f"\n[OK] Status Code: {response.status_code}")

        if response.status_code in [200, 201]:
            data = response.json()
            print(f"[OK] Response: {json.dumps(data, indent=2)}")

            # Check if members were auto-populated
            members_count = len(data.get('members', []))
            print(f"\n[INFO] Members auto-populated: {members_count}")

            if members_count > 0:
                print("[SUCCESS] Smart group created with members!")
                print(f"   First few members:")
                for i, member in enumerate(data['members'][:3]):
                    print(f"   {i+1}. {member.get('name')} - {member.get('phone')}")
            else:
                print("[WARN] Smart group created but no members matched the rules")
                print("   This could mean:")
                print("   - No contacts match the criteria")
                print("   - Contacts table is empty")
                print("   - Rule evaluation failed")

            return data.get('id')
        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to FastAPI server")
        print(f"   Make sure the server is running at: {FASTAPI_URL}")
        return None
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None

def test_get_groups():
    """Test 2: Get all groups and verify smart group is listed"""
    print_section("TEST 2: Get All Broadcast Groups")

    headers = {
        "X-Tenant-Id": TENANT_ID
    }

    print(f"\n[>>] Sending request to: {FASTAPI_URL}/broadcast-groups/")

    try:
        response = requests.get(
            f"{FASTAPI_URL}/broadcast-groups/",
            headers=headers,
            timeout=10
        )

        print(f"\n[OK] Status Code: {response.status_code}")

        if response.status_code == 200:
            groups = response.json()
            print(f"[OK] Total groups: {len(groups)}")

            smart_groups = [g for g in groups if g.get('auto_rules') and g['auto_rules'].get('enabled')]
            print(f"[INFO] Smart groups: {len(smart_groups)}")

            if smart_groups:
                print("\n[LIST] Smart Groups Details:")
                for i, group in enumerate(smart_groups, 1):
                    print(f"\n   {i}. {group['name']}")
                    print(f"      ID: {group['id']}")
                    print(f"      Members: {len(group.get('members', []))}")
                    print(f"      Auto-Rules: {group.get('auto_rules')}")

            return groups
        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return None

def test_sync_group(group_id):
    """Test 3: Test manual sync functionality"""
    if not group_id:
        print("\n[SKIP] Sync test (no group ID)")
        return

    print_section("TEST 3: Test Group Sync")

    headers = {
        "X-Tenant-Id": TENANT_ID
    }

    print(f"\n[>>] Syncing group: {group_id}")

    try:
        response = requests.post(
            f"{FASTAPI_URL}/broadcast-groups/{group_id}/sync",
            headers=headers,
            timeout=10
        )

        print(f"\n[OK] Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Sync result: {json.dumps(data, indent=2)}")
            print(f"\n[STATS] Sync Statistics:")
            print(f"   Members before: {data.get('members_before', 'N/A')}")
            print(f"   Members after: {data.get('members_after', 'N/A')}")
            print(f"   Members added: {data.get('members_added', 'N/A')}")
            print(f"   Members removed: {data.get('members_removed', 'N/A')}")
        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")

def test_rules_testing():
    """Test 4: Test rules before creating group"""
    print_section("TEST 4: Test Rules (Preview)")

    payload = {
        "conditions": [
            {
                "type": "text",
                "field": "name",
                "operator": "contains",
                "value": "test"
            }
        ],
        "logic": "AND"
    }

    headers = {
        "X-Tenant-Id": TENANT_ID,
        "Content-Type": "application/json"
    }

    print(f"\n[>>] Testing rules: {json.dumps(payload, indent=2)}")

    try:
        response = requests.post(
            f"{FASTAPI_URL}/broadcast-groups/test-rules",
            json=payload,
            headers=headers,
            timeout=10
        )

        print(f"\n[OK] Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            matching_count = len(data.get('matching_contacts', []))
            print(f"[OK] Matching contacts: {matching_count}")

            if matching_count > 0:
                print("\n[LIST] Sample matching contacts:")
                for i, contact in enumerate(data['matching_contacts'][:5], 1):
                    print(f"   {i}. {contact.get('name')} - {contact.get('phone')}")
            else:
                print("[WARN] No contacts match these rules")
        else:
            print(f"[ERROR] Request failed: {response.status_code}")
            print(f"   Error: {response.text}")

    except Exception as e:
        print(f"[ERROR] {str(e)}")

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  SMART GROUPS FUNCTIONALITY TEST SUITE")
    print("=" * 60)

    print(f"\n[*] Testing against: {FASTAPI_URL}")
    print(f"[*] Tenant ID: {TENANT_ID}")

    # Test 1: Create smart group
    group_id = test_create_smart_group()

    # Test 2: Get all groups
    test_get_groups()

    # Test 3: Sync group
    test_sync_group(group_id)

    # Test 4: Test rules
    test_rules_testing()

    # Summary
    print_section("TEST SUMMARY")
    print("\n[SUCCESS] All tests completed!")
    print("\n[NEXT STEPS]:")
    print("   1. Check if smart groups show members in the UI")
    print("   2. Try expanding a smart group to see contact list")
    print("   3. Test sync button in the UI")
    print("   4. Create contacts and verify they auto-join groups")
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
