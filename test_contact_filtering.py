"""
Quick test script to diagnose contact filtering issues
Run this to check if contacts exist and why filtering might fail
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'fastAPIWhatsapp_withclaude'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contacts.models import Contact
from datetime import datetime
import os

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost:5432/dbname')

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

try:
    # Test 1: Check if contacts exist
    print("\n" + "="*60)
    print("TEST 1: Total Contacts Check")
    print("="*60)

    total_contacts = db.query(Contact).count()
    print(f"Total contacts in database: {total_contacts}")

    # Test 2: Check contacts by tenant
    print("\n" + "="*60)
    print("TEST 2: Contacts by Tenant ID")
    print("="*60)

    tenant_id = "ai"  # Change this to your tenant_id
    tenant_contacts = db.query(Contact).filter(Contact.tenant_id == tenant_id).all()
    print(f"Contacts for tenant '{tenant_id}': {len(tenant_contacts)}")

    if tenant_contacts:
        print("\nSample contacts:")
        for i, contact in enumerate(tenant_contacts[:5]):
            print(f"  {i+1}. ID: {contact.id}")
            print(f"     Phone: {contact.phone}")
            print(f"     Name: {contact.name}")
            print(f"     CreatedOn: {contact.createdOn} (Type: {type(contact.createdOn)})")
            print(f"     Tenant ID: {contact.tenant_id} (Type: {type(contact.tenant_id)})")
            print()

    # Test 3: Check date filtering
    print("="*60)
    print("TEST 3: Date Range Filter")
    print("="*60)

    start_date = datetime.fromisoformat("2024-11-30T22:45:00")
    end_date = datetime.fromisoformat("2026-01-09T23:46:00")

    print(f"Date range: {start_date} to {end_date}")

    filtered_contacts = db.query(Contact).filter(
        Contact.tenant_id == tenant_id,
        Contact.createdOn > start_date,
        Contact.createdOn < end_date
    ).all()

    print(f"Contacts in date range: {len(filtered_contacts)}")

    if filtered_contacts:
        print("\nMatching contacts:")
        for contact in filtered_contacts[:5]:
            print(f"  - ID {contact.id}: {contact.phone} (Created: {contact.createdOn})")

    # Test 4: Check for NULL createdOn values
    print("\n" + "="*60)
    print("TEST 4: NULL CreatedOn Check")
    print("="*60)

    null_created = db.query(Contact).filter(
        Contact.tenant_id == tenant_id,
        Contact.createdOn.is_(None)
    ).count()

    print(f"Contacts with NULL createdOn: {null_created}")

    # Test 5: Check createdOn date distribution
    print("\n" + "="*60)
    print("TEST 5: CreatedOn Date Distribution")
    print("="*60)

    contacts_with_dates = db.query(Contact).filter(
        Contact.tenant_id == tenant_id,
        Contact.createdOn.isnot(None)
    ).order_by(Contact.createdOn).all()

    if contacts_with_dates:
        print(f"Earliest contact: {contacts_with_dates[0].createdOn}")
        print(f"Latest contact: {contacts_with_dates[-1].createdOn}")
        print(f"\nAll createdOn dates for tenant '{tenant_id}':")
        for contact in contacts_with_dates:
            print(f"  {contact.id}: {contact.createdOn}")

    print("\n" + "="*60)
    print("DIAGNOSIS COMPLETE")
    print("="*60)

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
