#!/usr/bin/env python
"""
Import interview data from Direct Chat conversations
Extracts audio recordings and responses to create interview dashboard entries
"""
import os
import sys
import django
import re
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
FLOW_NAME = 'interviewdrishtee'

# Keywords to identify interview questions
QUESTION_KEYWORDS = {
    'question1': ['question 1', 'q1', 'first question', 'प्रश्न 1'],
    'question2': ['question 2', 'q2', 'second question', 'प्रश्न 2'],
    'question3': ['question 3', 'q3', 'third question', 'प्रश्न 3'],
    'question4': ['question 4', 'q4', 'fourth question', 'प्रश्न 4'],
}

# Keywords to identify personal info
INFO_KEYWORDS = {
    'name': ['name', 'नाम', 'what is your name', 'your name'],
    'address': ['address', 'पता', 'where do you live', 'location'],
    'candidate_name': ['candidate name', 'full name', 'complete name'],
    'calibration': ['calibration', 'result', 'status', 'pass', 'fail'],
}

def extract_phone_number(contact_id):
    """Clean and format phone number"""
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', contact_id)

    # If it's 10 digits, assume India and add 91
    if len(phone) == 10:
        return f"91{phone}"

    # If it already has country code, return as is
    return phone

def identify_question_number(text):
    """Identify which question is being asked based on text"""
    if not text:
        return None

    text_lower = text.lower()

    for question_key, keywords in QUESTION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return question_key

    return None

def extract_personal_info(text):
    """Extract personal information from text"""
    if not text:
        return {}

    info = {}
    text_lower = text.lower()

    # Extract name
    name_patterns = [
        r'(?:name|नाम)[\s:]*([a-zA-Z\s]{2,50})',
        r'my name is\s+([a-zA-Z\s]{2,50})',
        r'i am\s+([a-zA-Z\s]{2,50})',
    ]

    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['name'] = match.group(1).strip()
            break

    # Extract address
    address_patterns = [
        r'(?:address|पता)[\s:]*([^,\n]{5,200})',
        r'(?:live|रहते|stay)[\s:]*(?:at|in)?\s*([^,\n]{5,200})',
    ]

    for pattern in address_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            info['address'] = match.group(1).strip()
            break

    return info

def group_conversations_by_phone(tenant):
    """Group all conversations by phone number"""
    print(f"\nFetching conversations for tenant {TENANT_ID}...")

    conversations = Conversation.objects.filter(
        tenant=tenant
    ).order_by('contact_id', 'date_time')

    print(f"Found {conversations.count()} conversations")

    # Group by phone number
    phone_conversations = defaultdict(list)

    for conv in conversations:
        phone = extract_phone_number(conv.contact_id)
        phone_conversations[phone].append(conv)

    print(f"Grouped into {len(phone_conversations)} unique phone numbers")

    return phone_conversations

def analyze_conversation_thread(conversations):
    """Analyze a conversation thread to extract interview data"""
    interview_data = {
        'name': '',
        'address': '',
        'candidate_name': '',
        'calibration': '',
        'question1': '',
        'question2': '',
        'question3': '',
        'question4': '',
        'timestamps': [],
    }

    current_question = None

    for conv in conversations:
        # Track all timestamps
        if conv.date_time:
            interview_data['timestamps'].append(conv.date_time)

        # Bot messages (assistant) - identify questions
        if conv.sender == 'assistant':
            question_num = identify_question_number(conv.message_text)
            if question_num:
                current_question = question_num

        # User messages - responses
        elif conv.sender == 'user':
            # If it's an audio message and we know which question, save it
            if conv.message_type == 'audio' and current_question:
                if conv.media_url:
                    interview_data[current_question] = conv.media_url
                    print(f"    Found audio for {current_question}: {conv.media_url[:50]}...")

            # Extract personal info from text messages
            if conv.message_text:
                personal_info = extract_personal_info(conv.message_text)
                for key, value in personal_info.items():
                    if value and not interview_data.get(key):
                        interview_data[key] = value
                        print(f"    Found {key}: {value}")

                # Check for calibration keywords
                text_lower = conv.message_text.lower()
                if any(word in text_lower for word in ['pass', 'passed', 'qualified', 'selected']):
                    interview_data['calibration'] = 'passed'
                elif any(word in text_lower for word in ['fail', 'failed', 'rejected']):
                    interview_data['calibration'] = 'failed'

    return interview_data

def create_interview_entry(phone, interview_data, tenant):
    """Create an InterviewResponse entry"""

    # Use earliest timestamp as interview timestamp
    timestamp = min(interview_data['timestamps']) if interview_data['timestamps'] else datetime.now()

    # Check if entry already exists for this phone and timestamp
    existing = InterviewResponse.objects.filter(
        phone_no=phone,
        tenant=tenant,
        timestamp__date=timestamp.date()
    ).first()

    if existing:
        print(f"  [WARN] Entry already exists for {phone} on {timestamp.date()}")
        return None

    # Create new entry
    response = InterviewResponse.objects.create(
        phone_no=phone,
        tenant=tenant,
        flow_name=FLOW_NAME,
        timestamp=timestamp,
        candidate_name=interview_data.get('candidate_name', ''),
        name=interview_data.get('name', ''),
        address=interview_data.get('address', ''),
        calibration=interview_data.get('calibration', ''),
        status='completed',
        question1=interview_data.get('question1', ''),
        question2=interview_data.get('question2', ''),
        question3=interview_data.get('question3', ''),
        question4=interview_data.get('question4', ''),
    )

    return response

def main():
    print("="*70)
    print("Import Interview Data from Direct Chat")
    print("="*70)

    try:
        tenant = Tenant.objects.get(id=TENANT_ID)
        print(f"[OK] Tenant found: {tenant.organization}")
    except Tenant.DoesNotExist:
        print(f"[ERROR] Tenant {TENANT_ID} not found!")
        return

    # Group conversations by phone
    phone_conversations = group_conversations_by_phone(tenant)

    if not phone_conversations:
        print("\n[ERROR] No conversations found!")
        return

    # Process each phone number's conversations
    print(f"\n{'='*70}")
    print("Processing conversations...")
    print(f"{'='*70}\n")

    imported_count = 0
    skipped_count = 0

    for phone, conversations in phone_conversations.items():
        print(f"\n[PHONE] Processing: {phone} ({len(conversations)} messages)")

        # Analyze conversation thread
        interview_data = analyze_conversation_thread(conversations)

        # Check if we have any meaningful data
        has_audio = any(interview_data.get(f'question{i}') for i in range(1, 5))
        has_info = any(interview_data.get(key) for key in ['name', 'address', 'candidate_name'])

        if has_audio or has_info:
            entry = create_interview_entry(phone, interview_data, tenant)
            if entry:
                print(f"  [OK] Created interview entry (ID: {entry.id})")
                imported_count += 1
            else:
                skipped_count += 1
        else:
            print(f"  [SKIP] No interview data found")
            skipped_count += 1

    # Summary
    print(f"\n{'='*70}")
    print("Import Complete!")
    print(f"{'='*70}")
    print(f"[OK] Imported: {imported_count} interview entries")
    print(f"[SKIP] Skipped: {skipped_count} (no data or already exists)")
    print(f"\nTotal phone numbers processed: {len(phone_conversations)}")
    print(f"\n[TIP] Refresh your dashboard to see the imported data!")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    main()
