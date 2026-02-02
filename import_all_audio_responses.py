#!/usr/bin/env python
"""
Import ALL audio messages from Direct Chat as interview responses
Creates one entry per phone number with all their audio responses
"""
import os
import sys
import django
from datetime import datetime
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplecrm.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from interviews.models import InterviewResponse
from interaction.models import Conversation
from contacts.models import Contact
from tenant.models import Tenant

TENANT_ID = 'ehgymjv'

def extract_phone_number(contact_id):
    """Clean phone number"""
    import re
    phone = re.sub(r'\D', '', contact_id)
    if len(phone) == 10:
        return f"91{phone}"
    return phone

def main():
    print("="*70)
    print("Import Audio Messages from Direct Chat")
    print("="*70)

    try:
        tenant = Tenant.objects.get(id=TENANT_ID)
        print(f"[OK] Tenant: {tenant.organization}")
    except Tenant.DoesNotExist:
        print(f"[ERROR] Tenant {TENANT_ID} not found!")
        return

    # Get all conversations
    print(f"\nFetching conversations...")
    conversations = Conversation.objects.filter(
        tenant=tenant,
        sender='user'  # Only user messages
    ).order_by('contact_id', 'date_time')

    total = conversations.count()
    print(f"Found {total} user messages")

    # Group by phone
    phone_data = defaultdict(lambda: {
        'audio_messages': [],
        'text_messages': [],
        'timestamps': [],
        'contact_info': {}
    })

    print("\nGrouping messages by phone number...")
    for conv in conversations:
        phone = extract_phone_number(conv.contact_id)

        # Store timestamp
        if conv.date_time:
            phone_data[phone]['timestamps'].append(conv.date_time)

        # Store audio messages
        if conv.message_type == 'audio' and conv.media_url:
            phone_data[phone]['audio_messages'].append({
                'url': conv.media_url,
                'timestamp': conv.date_time,
                'caption': conv.media_caption or ''
            })

        # Store text messages for name/address extraction
        if conv.message_text:
            phone_data[phone]['text_messages'].append(conv.message_text)

    print(f"Grouped into {len(phone_data)} phone numbers\n")

    # Process each phone number
    print("="*70)
    print("Creating interview entries...")
    print("="*70 + "\n")

    imported_count = 0
    skipped_count = 0

    for phone, data in phone_data.items():
        audio_count = len(data['audio_messages'])

        print(f"\n[PHONE] {phone}")
        print(f"  Audio messages: {audio_count}")
        print(f"  Text messages: {len(data['text_messages'])}")

        # Skip if no audio messages
        if audio_count == 0:
            print(f"  [SKIP] No audio messages")
            skipped_count += 1
            continue

        # Get earliest timestamp
        timestamp = min(data['timestamps']) if data['timestamps'] else datetime.now()

        # Check if already exists
        existing = InterviewResponse.objects.filter(
            phone_no=phone,
            tenant=tenant
        ).first()

        if existing:
            print(f"  [WARN] Entry already exists (ID: {existing.id})")
            skipped_count += 1
            continue

        # Extract name/address from text messages
        name = ''
        address = ''
        candidate_name = ''

        # Try to find name in text messages
        for text in data['text_messages'][:10]:  # Check first 10 messages
            if len(text) < 100 and any(c.isalpha() for c in text):
                if not name and 2 < len(text.split()) < 10:
                    name = text.strip()[:200]
                    candidate_name = text.strip()[:200]
                elif not address and len(text) > 10:
                    address = text.strip()[:500]

        # Try to get from Contact model
        try:
            contact = Contact.objects.filter(phone=phone, tenant=tenant).first()
            if contact:
                if not name and contact.name:
                    name = contact.name
                    candidate_name = contact.name
                if not address and contact.address:
                    address = contact.address
        except:
            pass

        # Assign audio URLs to questions
        question1 = data['audio_messages'][0]['url'] if len(data['audio_messages']) > 0 else ''
        question2 = data['audio_messages'][1]['url'] if len(data['audio_messages']) > 1 else ''
        question3 = data['audio_messages'][2]['url'] if len(data['audio_messages']) > 2 else ''
        question4 = data['audio_messages'][3]['url'] if len(data['audio_messages']) > 3 else ''

        # Create entry
        response = InterviewResponse.objects.create(
            phone_no=phone,
            tenant=tenant,
            flow_name='interviewdrishtee',
            timestamp=timestamp,
            candidate_name=candidate_name,
            name=name,
            address=address,
            calibration='',
            status='completed',
            question1=question1,
            question2=question2,
            question3=question3,
            question4=question4,
        )

        print(f"  [OK] Created entry (ID: {response.id})")
        try:
            print(f"       Name: {name[:50] if name else 'N/A'}")
        except:
            print(f"       Name: [Contains special characters]")
        print(f"       Audio URLs: {audio_count} stored")
        imported_count += 1

    # Summary
    print(f"\n{'='*70}")
    print("Import Complete!")
    print(f"{'='*70}")
    print(f"[OK] Imported: {imported_count} interview entries")
    print(f"[SKIP] Skipped: {skipped_count} (no audio or already exists)")
    print(f"\nTotal phone numbers: {len(phone_data)}")
    print(f"[TIP] Refresh your dashboard to see the data!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
