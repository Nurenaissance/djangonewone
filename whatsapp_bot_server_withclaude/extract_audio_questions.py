"""
Extract audio files and their associated questions for tenant ehgymjv
"""
import sys
import io

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import psycopg2
import pandas as pd
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import json

# Database connection details
DB_CONFIG = {
    'host': 'nurenaistore.postgres.database.azure.com',
    'database': 'nurenpostgres_Whatsapp',
    'user': 'nurenai',
    'password': 'Biz1nurenWar*',
    'port': '5432',
    'sslmode': 'require'
}

# Target tenant
TENANT_ID = 'ehgymjv'

# Target phone numbers
TARGET_PHONES = [
    '918720962751',
    '919425030130',
    '919643393874',
    '918010901678',
    '918708790107',
    '918114611767',
    '919101634037',
    '917068535635',
    '918103341576',
    '918112469870',
    '918005385732',
    '916295905155',
    '918005070038',
    '916000853723',
    '919706993867',
]

def decrypt_data(encrypted_data: bytes, key: bytes):
    """Decrypt AES-encrypted data"""
    try:
        if encrypted_data is None:
            return None

        # Handle memoryview
        if isinstance(encrypted_data, memoryview):
            encrypted_data = bytes(encrypted_data)
        if isinstance(key, memoryview):
            key = bytes(key)

        # Extract the IV from the first 16 bytes
        iv = encrypted_data[:16]
        encrypted_data = encrypted_data[16:]

        # Initialize the cipher
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        # Perform decryption
        decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

        # Remove padding (PKCS#7 padding)
        pad_len = decrypted_data[-1]
        decrypted_data = decrypted_data[:-pad_len]

        return json.loads(decrypted_data.decode())
    except Exception as e:
        print(f"Decryption error: {str(e)}")
        return None

def get_message_text(message_text, encrypted_text, encryption_key):
    """Get decrypted message text or plain text"""
    if encrypted_text is not None and encryption_key is not None:
        decrypted = decrypt_data(encrypted_text, encryption_key)
        if decrypted:
            if isinstance(decrypted, str):
                return decrypted
            return json.dumps(decrypted)
    return message_text

def main():
    print(f"Connecting to database...")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # First get the encryption key for the tenant
    print(f"Fetching encryption key for tenant: {TENANT_ID}")
    cursor.execute("SELECT key FROM tenant_tenant WHERE id = %s", (TENANT_ID,))
    tenant_row = cursor.fetchone()

    if not tenant_row:
        print(f"Tenant {TENANT_ID} not found!")
        return

    encryption_key = tenant_row[0]
    if encryption_key:
        encryption_key = bytes(encryption_key) if isinstance(encryption_key, memoryview) else encryption_key
    print(f"Encryption key retrieved: {bool(encryption_key)}")

    # Build the query to get all conversations for the specified contacts
    phone_placeholders = ','.join(['%s'] * len(TARGET_PHONES))

    query = f"""
        SELECT
            id, contact_id, message_text, encrypted_message_text,
            message_type, media_url, media_caption, media_filename,
            sender, date_time
        FROM interaction_conversation
        WHERE tenant_id = %s
        AND contact_id IN ({phone_placeholders})
        ORDER BY contact_id, date_time ASC
    """

    params = [TENANT_ID] + TARGET_PHONES
    print(f"Executing query for {len(TARGET_PHONES)} contacts...")
    cursor.execute(query, params)

    rows = cursor.fetchall()
    print(f"Found {len(rows)} conversation messages")

    # Organize conversations by contact
    conversations_by_contact = {}
    for row in rows:
        (id_, contact_id, message_text, encrypted_text,
         message_type, media_url, media_caption, media_filename,
         sender, date_time) = row

        # Decrypt message if needed
        text = get_message_text(message_text, encrypted_text, encryption_key)

        if contact_id not in conversations_by_contact:
            conversations_by_contact[contact_id] = []

        conversations_by_contact[contact_id].append({
            'id': id_,
            'contact_id': contact_id,
            'text': text,
            'message_type': message_type,
            'media_url': media_url,
            'media_caption': media_caption,
            'media_filename': media_filename,
            'sender': sender,
            'date_time': date_time
        })

    # Find audio messages and their preceding questions
    results = []

    for contact_id, messages in conversations_by_contact.items():
        print(f"\nProcessing contact: {contact_id} ({len(messages)} messages)")

        for i, msg in enumerate(messages):
            if msg['message_type'] == 'audio' and msg['media_url']:
                # Find the preceding question (look back for bot messages)
                question = None
                question_time = None

                # Look backwards for the most recent bot message before this audio
                for j in range(i - 1, -1, -1):
                    prev_msg = messages[j]
                    if prev_msg['sender'] in ['bot', 'Bot', 'BOT', 'assistant']:
                        question = prev_msg['text']
                        question_time = prev_msg['date_time']
                        break

                results.append({
                    'Contact Number': contact_id,
                    'Question (Bot Message)': question,
                    'Question Time': question_time,
                    'Audio Media URL': msg['media_url'],
                    'Audio Time': msg['date_time'],
                    'Audio Caption': msg['media_caption'],
                    'Audio Filename': msg['media_filename']
                })

                print(f"  Found audio file")
                if question:
                    print(f"    Has preceding question")

    cursor.close()
    conn.close()

    if results:
        # Create DataFrame and export to Excel
        df = pd.DataFrame(results)

        # Format datetime columns
        for col in ['Question Time', 'Audio Time']:
            df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d %H:%M:%S')

        output_file = f'audio_questions_{TENANT_ID}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(output_file, index=False, engine='openpyxl')
        print(f"\n✅ Exported {len(results)} audio records to: {output_file}")

        # Also print summary
        print(f"\nSummary by contact:")
        for contact in df['Contact Number'].unique():
            count = len(df[df['Contact Number'] == contact])
            print(f"  {contact}: {count} audio files")
    else:
        print("\n⚠️ No audio messages found for the specified contacts")

if __name__ == "__main__":
    main()
