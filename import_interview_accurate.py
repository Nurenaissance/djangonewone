#!/usr/bin/env python
"""
Accurately import interview data by analyzing conversation flow
Maps audio responses to correct variables: calibration, question1-4, name, address
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
import re

TENANT_ID = 'ehgymjv'
SESSION_GAP_HOURS = 2

# Variable names in order they appear in flow
# (This is the expected order based on typical interview flows)
VARIABLE_ORDER = ['name', 'address', 'calibration', 'question1', 'question2', 'question3', 'question4']

def extract_phone_number(contact_id):
    """Clean phone number"""
    phone = re.sub(r'\D', '', contact_id)
    if len(phone) == 10:
        return f"91{phone}"
    return phone

def group_into_sessions(conversations, session_gap_hours=2):
    """Group conversations into sessions based on time gaps"""
    if not conversations:
        return []

    sessions = []
    current_session = []
    last_timestamp = None

    for conv in conversations:
        if not conv.date_time:
            continue

        if last_timestamp is None or (conv.date_time - last_timestamp) > timedelta(hours=session_gap_hours):
            if current_session:
                sessions.append(current_session)
            current_session = [conv]
        else:
            current_session.append(conv)

        last_timestamp = conv.date_time

    if current_session:
        sessions.append(current_session)

    return sessions

def analyze_session_accurate(session_conversations):
    """
    Analyze conversation sequence to map responses to correct variables
    Returns dict with keys: calibration, question1-4, name, address, and their _audio variants
    """
    result = {
        'calibration': '',
        'calibration_audio': '',
        'question1': '',
        'question2': '',
        'question3': '',
        'question4': '',
        'name': '',
        'name_audio': '',
        'address': '',
        'address_audio': '',
        'candidate_name': '',
        'timestamps': []
    }

    # Collect all user audio and text messages in order
    user_responses = []
    for conv in session_conversations:
        if conv.date_time:
            result['timestamps'].append(conv.date_time)

        if conv.sender == 'user':
            if conv.message_type == 'audio' and conv.media_url:
                user_responses.append({
                    'type': 'audio',
                    'value': conv.media_url,
                    'timestamp': conv.date_time
                })
            elif conv.message_text:
                user_responses.append({
                    'type': 'text',
                    'value': conv.message_text,
                    'timestamp': conv.date_time
                })

    print(f"      Found {len(user_responses)} user responses")

    # Map responses to variables based on expected order
    # Assuming the flow asks questions in the order: name, address, calibration, q1, q2, q3, q4
    for i, response in enumerate(user_responses):
        if i < len(VARIABLE_ORDER):
            var_name = VARIABLE_ORDER[i]
            value = response['value']

            # Handle audio vs text appropriately
            if response['type'] == 'audio':
                # Audio response
                if var_name in ['name', 'address', 'calibration']:
                    # Save to _audio field
                    result[f'{var_name}_audio'] = value
                    print(f"      [{i+1}] {var_name}_audio = {value[:60]}...")
                else:
                    # question1-4
                    result[var_name] = value
                    print(f"      [{i+1}] {var_name} = audio: {value[:60]}...")
            else:
                # Text response
                if var_name in ['name', 'candidate_name']:
                    result[var_name] = value[:200]  # Truncate for CharField
                    print(f"      [{i+1}] {var_name} = text: {value[:60]}...")
                else:
                    result[var_name] = value
                    print(f"      [{i+1}] {var_name} = text: {value[:60]}...")

    # Try to get candidate name from Contact or first text message
    if not result['candidate_name'] and result['name']:
        result['candidate_name'] = result['name']

    return result

def main():
    print("="*70)
    print("Accurate Interview Import - Maps Responses to Correct Variables")
    print("="*70)

    try:
        tenant = Tenant.objects.get(id=TENANT_ID)
        print(f"[OK] Tenant: {tenant.organization}")
    except Tenant.DoesNotExist:
        print(f"[ERROR] Tenant {TENANT_ID} not found!")
        return

    # Get all user conversations
    conversations = Conversation.objects.filter(
        tenant=tenant,
        sender='user'
    ).order_by('contact_id', 'date_time')

    print(f"\nFound {conversations.count()} user messages")

    # Group by phone
    phone_conversations = defaultdict(list)
    for conv in conversations:
        phone = extract_phone_number(conv.contact_id)
        phone_conversations[phone].append(conv)

    print(f"Grouped into {len(phone_conversations)} phone numbers")

    # Group into sessions
    all_sessions = []
    for phone, convs in phone_conversations.items():
        sessions = group_into_sessions(convs, SESSION_GAP_HOURS)
        for session in sessions:
            all_sessions.append((phone, session))

    print(f"Found {len(all_sessions)} total sessions\n")

    # Process each session
    print("="*70)
    print("Creating interview entries...")
    print("="*70 + "\n")

    imported_count = 0
    skipped_count = 0

    # First, delete all existing entries to re-import accurately
    print("[INFO] Clearing existing entries for re-import...")
    deleted_count = InterviewResponse.objects.filter(
        tenant=tenant,
        flow_name='interviewdrishtee'
    ).delete()[0]
    print(f"[OK] Deleted {deleted_count} existing entries\n")

    for phone, session in all_sessions:
        session_data = analyze_session_accurate(session)

        if not session_data['timestamps']:
            skipped_count += 1
            continue

        session_start = min(session_data['timestamps'])
        session_end = max(session_data['timestamps'])

        print(f"\n[SESSION] {phone}")
        print(f"  Time: {session_start.strftime('%Y-%m-%d %H:%M')} to {session_end.strftime('%H:%M')}")

        # Check if we have any meaningful data
        has_data = any([
            session_data['calibration'],
            session_data['calibration_audio'],
            session_data['question1'],
            session_data['question2'],
            session_data['question3'],
            session_data['question4'],
            session_data['name'],
            session_data['name_audio'],
            session_data['address'],
            session_data['address_audio']
        ])

        if not has_data:
            print(f"  [SKIP] No data")
            skipped_count += 1
            continue

        # Get contact info
        try:
            contact = Contact.objects.filter(phone=phone, tenant=tenant).first()
            if contact:
                if not session_data['name'] and contact.name:
                    session_data['name'] = contact.name
                if not session_data['candidate_name'] and contact.name:
                    session_data['candidate_name'] = contact.name
                if not session_data['address'] and contact.address:
                    session_data['address'] = contact.address
        except:
            pass

        # Create entry
        response = InterviewResponse.objects.create(
            phone_no=phone,
            tenant=tenant,
            flow_name='interviewdrishtee',
            timestamp=session_start,
            candidate_name=session_data['candidate_name'] or session_data['name'],
            name=session_data['name'],
            name_audio=session_data['name_audio'],
            address=session_data['address'],
            address_audio=session_data['address_audio'],
            calibration=session_data['calibration'],
            calibration_audio=session_data['calibration_audio'],
            status='completed',
            question1=session_data['question1'],
            question2=session_data['question2'],
            question3=session_data['question3'],
            question4=session_data['question4'],
        )

        print(f"  [OK] Created entry (ID: {response.id})")
        try:
            name_display = session_data['name'][:50] if session_data['name'] else ('Audio' if session_data['name_audio'] else 'N/A')
            addr_display = session_data['address'][:50] if session_data['address'] else ('Audio' if session_data['address_audio'] else 'N/A')
            calib_display = session_data['calibration'] if session_data['calibration'] else ('Audio' if session_data['calibration_audio'] else 'No')
            print(f"       Name: {name_display}")
            print(f"       Address: {addr_display}")
            print(f"       Calibration: {calib_display}")
            print(f"       Questions: q1={bool(session_data['question1'])}, q2={bool(session_data['question2'])}, q3={bool(session_data['question3'])}, q4={bool(session_data['question4'])}")
        except UnicodeEncodeError:
            print("       [Details contain non-ASCII characters]")
        imported_count += 1

    # Summary
    print(f"\n{'='*70}")
    print("Import Complete!")
    print(f"{'='*70}")
    print(f"[OK] Imported: {imported_count} session entries")
    print(f"[SKIP] Skipped: {skipped_count} (no data)")
    print(f"\nTotal sessions: {len(all_sessions)}")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
