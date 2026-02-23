import pandas as pd
import sys

# Read the original Excel file
df = pd.read_excel('audio_questions_ehgymjv_20260127_172840.xlsx')

# Define question patterns to identify each question type
question_patterns = {
    'name': 'हमें अपना नाम बताइए',
    'address': 'हमें अपना पता बताइए',
    'calibration': 'कैलिब्रेशन निर्देश',
    'question1': 'Q1 आप अपने गाँव में',  # Q1-Q3
    'question2': 'Q4 पिछले महीने',  # Q4-Q6
    'question3': 'Q7 आपके पास 5000',  # Q7-Q9
    'question4': 'Q10 दिन के अंत में',  # Q10-Q11
}

def identify_question_type(question_text):
    """Identify the type of question based on text content"""
    if pd.isna(question_text):
        return None
    for q_type, pattern in question_patterns.items():
        if pattern in str(question_text):
            return q_type
    return None

# Add question type column
df['question_type'] = df['Question (Bot Message)'].apply(identify_question_type)

# Group by Contact Number and create one row per contact
results = []

for contact, group in df.groupby('Contact Number'):
    row = {
        'phone_no': contact,
        'address': None,
        'name': None,
        'timestamp': None,
        'calibration': None,
        'question1': None,
        'question2': None,
        'question3': None,
        'question4': None,
        'status': 'completed'  # Default status
    }

    for _, record in group.iterrows():
        q_type = record['question_type']
        if q_type and q_type in row:
            # Use Audio Media URL as the response/answer
            row[q_type] = record['Audio Media URL']
            # Use the first timestamp we encounter
            if row['timestamp'] is None:
                row['timestamp'] = record['Question Time']

    # Check if conversation ended properly
    if 'The conversation has ended' in group['Question (Bot Message)'].astype(str).str.cat():
        row['status'] = 'completed'
    elif 'धन्यवाद' in group['Question (Bot Message)'].astype(str).str.cat():
        row['status'] = 'completed'
    else:
        row['status'] = 'incomplete'

    results.append(row)

# Create output DataFrame with desired column order
output_df = pd.DataFrame(results)
output_df = output_df[['address', 'name', 'timestamp', 'phone_no', 'calibration',
                        'question1', 'question2', 'question3', 'question4', 'status']]

# Save to new Excel file
output_filename = 'audio_questions_converted.xlsx'
output_df.to_excel(output_filename, index=False)

print(f"Converted {len(output_df)} contacts to new format")
print(f"Output saved to: {output_filename}")
print("\nPreview of converted data:")
print(output_df.head().to_string())
