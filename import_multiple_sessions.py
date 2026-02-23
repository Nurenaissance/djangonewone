#!/usr/bin/env python
"""
Import interview data with MULTIPLE ENTRIES per phone number
Creates separate entries for each conversation session
"""
import os
import sys
import django
from datetime import datetime, timedelta
from collections import defaultdict

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplecrm.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from interviews.models import InterviewResponse
from interaction.models import Conversation
from contacts.models import Contact
from tenant.models import Tenant

TENANT_ID = 'ehgymjv'
SESSION_GAP_HOURS = 2  # Consider messages as same session if within 2 hours

def extract_phone_number(contact_id):
    """Clean phone number"""
    import re
    phone = re.sub(r'\D', '', contact_id)
    if len(phone) == 10:
        return f"91{phone}"
    return phone

def group_into_sessions(conversations):
    """
    Group conversations into sessions based on time gaps
    If gap between messages > SESSION_GAP_HOURS, start new session
    """
    if not conversations:
        return []

    sessions = []
    current_session = []
    last_timestamp = None

    for conv in conversations:
        if not conv.date_time:
            continue

        # If first message or gap is large, start new session
        if last_timestamp is None or (conv.date_time - last_timestamp) > timedelta(hours=SESSION_GAP_HOURS):
            if current_session:
                sessions.append(current_session)
            current_session = [conv]
        else:
            current_session.append(conv)

        last_timestamp = conv.date_time

    # Add last session
    if current_session:
        sessions.append(current_session)

    return sessions

def extract_session_data(session_conversations):
    """Extract audio and text data from a session"""
    data = {
        'audio_urls': [],
        'text_messages': [],
        'timestamps': [],
        'calibration_audio': None,
        'calibration_text': None,
    }

    for conv in session_conversations:
        if conv.date_time:
            data['timestamps'].append(conv.date_time)

        # Audio messages
        if conv.message_type == 'audio' and conv.media_url:
            # Check if it's calibration
            caption = (conv.media_caption or '').lower()
            if 'calibration' in caption or 'calib' in caption:
                data['calibration_audio'] = conv.media_url
            else:
                data['audio_urls'].append(conv.media_url)

        # Text messages
        if conv.message_text:
            text = conv.message_text.lower()
            # Check if calibration text
            if 'calibration' in text:
                data['calibration_text'] = conv.message_text
            else:
                data['text_messages'].append(conv.message_text)

    return data

def main():
    print("="*70)
    print("Import Multiple Sessions per Phone Number")
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
        sender='user'
    ).order_by('contact_id', 'date_time')

    print(f"Found {conversations.count()} user messages")

    # Group by phone first
    phone_conversations = defaultdict(list)
    for conv in conversations:
        phone = extract_phone_number(conv.contact_id)
        phone_conversations[phone].append(conv)

    print(f"Grouped into {len(phone_conversations)} phone numbers")

    # Now group each phone's conversations into sessions
    print(f"\nGrouping into sessions (gap > {SESSION_GAP_HOURS}h = new session)...")

    all_sessions = []
    for phone, convs in phone_conversations.items():
        sessions = group_into_sessions(convs)
        for session in sessions:
            all_sessions.append((phone, session))

    print(f"Found {len(all_sessions)} total sessions\n")

    # Process each session
    print("="*70)
    print("Creating interview entries...")
    print("="*70 + "\n")

    imported_count = 0
    skipped_count = 0

    for phone, session in all_sessions:
        session_data = extract_session_data(session)
        audio_count = len(session_data['audio_urls'])
        has_calibration = session_data['calibration_audio'] or session_data['calibration_text']

        # Get session timestamp
        if not session_data['timestamps']:
            continue

        session_start = min(session_data['timestamps'])
        session_end = max(session_data['timestamps'])

        print(f"\n[SESSION] {phone}")
        print(f"  Time: {session_start.strftime('%Y-%m-%d %H:%M')} to {session_end.strftime('%H:%M')}")
        print(f"  Audio files: {audio_count}")
        print(f"  Calibration: {'Yes' if has_calibration else 'No'}")

        # Skip if no audio
        if audio_count == 0 and not has_calibration:
            print(f"  [SKIP] No audio data")
            skipped_count += 1
            continue

        # Check if this exact session already exists
        existing = InterviewResponse.objects.filter(
            phone_no=phone,
            tenant=tenant,
            timestamp=session_start
        ).first()

        if existing:
            print(f"  [WARN] Session already imported (ID: {existing.id})")
            skipped_count += 1
            continue

        # Get name from Contact
        name = ''
        address = ''
        try:
            contact = Contact.objects.filter(phone=phone, tenant=tenant).first()
            if contact:
                name = contact.name or ''
                address = contact.address or ''
        except:
            pass

        # Extract name from text if not found
        if not name and session_data['text_messages']:
            for text in session_data['text_messages'][:5]:
                if 2 < len(text.split()) < 10 and len(text) < 100:
                    name = text.strip()[:200]
                    break

        # Assign audio URLs to questions
        question1 = session_data['audio_urls'][0] if len(session_data['audio_urls']) > 0 else ''
        question2 = session_data['audio_urls'][1] if len(session_data['audio_urls']) > 1 else ''
        question3 = session_data['audio_urls'][2] if len(session_data['audio_urls']) > 2 else ''
        question4 = session_data['audio_urls'][3] if len(session_data['audio_urls']) > 3 else ''

        # Calibration
        calibration = ''
        if session_data['calibration_audio']:
            calibration = session_data['calibration_audio']
        elif session_data['calibration_text']:
            calibration = session_data['calibration_text'][:200]

        # Create entry
        response = InterviewResponse.objects.create(
            phone_no=phone,
            tenant=tenant,
            flow_name='interviewdrishtee',
            timestamp=session_start,
            candidate_name=name,
            name=name,
            address=address,
            calibration=calibration,
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
        print(f"       Questions: {audio_count}, Calibration: {'Yes' if calibration else 'No'}")
        imported_count += 1

    # Summary
    print(f"\n{'='*70}")
    print("Import Complete!")
    print(f"{'='*70}")
    print(f"[OK] Imported: {imported_count} session entries")
    print(f"[SKIP] Skipped: {skipped_count} (no audio or already exists)")
    print(f"\nTotal sessions found: {len(all_sessions)}")
    print(f"[TIP] Each phone number now has multiple entries if they used the bot multiple times!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
