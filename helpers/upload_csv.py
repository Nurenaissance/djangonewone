import os
import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .tables import get_db_connection, table_mappings
from openai import OpenAI
import pandas as pd
import numpy as np
from tenant.models import Tenant
from contacts.models import Contact
# from simplecrm.middleware import TenantMiddleware
from django.db import transaction, connection
import re

import logging
from .tasks import bulk_upload_contacts

# Initialize logger
logger = logging.getLogger(__name__)

# Assuming df is your DataFrame
default_timestamp = '1970-01-01 00:00:00'

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

def get_tableFields(table_name):
    query = f"SELECT * FROM {table_name} LIMIT 0"  # Use LIMIT 0 to avoid fetching actual data
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        column_names = [desc[0] for desc in cursor.description]
    except Exception as e:
        print(f"Error fetching table fields: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    
    return column_names

SYSTEM_PROMPT = """
You are a helpful assistant who answers STRICTLY to what is asked, based on the info provided. 
DO NOT ADD DATA FROM THE INTERNET. 
Keep your answers concise and only the required information

Map the given two lists with each other.
Fields most similar to each other should be mapped together.
Return only the mapped dictionary in JSON format without nesting.
Skip createdBy_id, tenant_id, template_key, isActive, and createdOn.
The 'phone' and 'name' fields should be mandatorily mapped to their most similar fields.
You can map name to first_name or last_name, but not to both.

If you are not sure about mapping a field, keep it under 'customField' list.

Input Sample: list1: ['name', 'phone', 'email', 'address', 'city'], list2: ['name', 'phone', 'email', 'address', 'description', 'createdBy', 'createdOn', 'isActive', 'tenant', 'template_key', 'last_seen', 'last_delivered', 'last_replied', 'customField']
Output Sample: {'name': 'name', 'phone': 'phone', 'email': 'email', 'customField': ['address', 'city']}
"""



def mappingFunc(list1, list2):
    list1_filtered = [item for item in list1 if item.lower() != 'id']
    list2_filtered = [item for item in list2 if item.lower() != 'id']

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "developer", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Map these two lists with each other. List1: {list1_filtered}, List2: {list2_filtered}."}
            ]
        )
        field_mapping =  response.choices[0].message.content
        
        start = field_mapping.find('{')
        end = field_mapping.find('}')
        field_mapping = field_mapping[start:end + 1]
        field_mapping_json = json.loads(field_mapping)
        print(field_mapping_json)

        return field_mapping_json
    except Exception as e:
        print(f"Error during mapping: {e}")
        raise

@csrf_exempt
def upload_file(request, df):
    if request.method == 'POST':
        try:
            print("Entering upload file")
            print("df: ", df[:5])

            model_name = request.POST.get('model_name')
            xls_file = request.FILES.get('file')
            tenant_id = request.headers.get('X-Tenant-Id')

            print("Received model_name: ", model_name)

            if not (xls_file.name.endswith('.xls') or xls_file.name.endswith('.xlsx') or xls_file.name.endswith('.csv')):
                return JsonResponse({"error": "File is not in XLS/XLSX/CSV format"}, status=400)

            if model_name:
                try:
                    # PREPROCESSING: Combine first_name + last_name into 'name' BEFORE AI mapping
                    if 'first_name' in df.columns and 'last_name' in df.columns:
                        print("Combining first_name and last_name into 'name' column")
                        df['name'] = df['first_name'].fillna('').astype(str) + ' ' + df['last_name'].fillna('').astype(str)
                        df['name'] = df['name'].str.strip()
                        # Drop the original columns to avoid confusion
                        df = df.drop(columns=['first_name', 'last_name'])
                        print("Name column created, first_name and last_name removed")
                    elif 'first_name' in df.columns and 'name' not in df.columns:
                        print("Renaming first_name to name")
                        df = df.rename(columns={'first_name': 'name'})
                    elif 'last_name' in df.columns and 'name' not in df.columns:
                        print("Renaming last_name to name")
                        df = df.rename(columns={'last_name': 'name'})

                    table_name = table_mappings.get(model_name)
                    field_names = get_tableFields(table_name)
                    column_names = df.columns.tolist()
                    print("Columns after preprocessing:", column_names)
                    
                    try:
                        field_mapping = mappingFunc(column_names, field_names)
                    except Exception as e:
                        return JsonResponse({"error": f"Error mapping fields: {e}"}, status=500)
                    
                    df_new = df.rename(columns=field_mapping)
                    print("Renamed DataFrame columns:", df_new.columns.tolist())  # Print column names after renaming

                    # Process the phone column
                    # Process the phone column
                    if 'phone' in df_new.columns:
                        print("Original phone numbers:", df_new['phone'].tolist())  # Print before transformation

                        df_new['phone'] = df_new['phone'].astype(str)  # Ensure it's a string

                        # Remove special characters from phone numbers (keeping only digits)
                        df_new['phone'] = df_new['phone'].apply(lambda x: re.sub(r'\D', '', x))  # Remove non-digit characters

                        # Print after removing special characters
                        print("Phone numbers after removing special characters:", df_new['phone'].tolist())

                        # Keep only numeric values and remove numbers shorter than 9 digits
                        df_new = df_new[df_new['phone'].str.isdigit()]  
                        df_new = df_new[df_new['phone'].str.len() >= 9]  

                        # Print after filtering invalid numbers
                        print("Filtered phone numbers (only 9+ digits):", df_new['phone'].tolist())
                        
                        def process_phone(phone):
                            # For 10-digit numbers, add India country code (91)
                            if len(phone) == 10:  
                                return '91' + phone
                            
                            # For 9-digit numbers, add UAE country code (971)
                            elif len(phone) == 9:
                                return '971' + phone
                                
                            # Keep numbers that already have country codes
                            elif (phone.startswith('91') and len(phone) == 12) or (phone.startswith('971') and len(phone) == 12):
                                return phone
                                
                            # For other valid international numbers
                            elif len(phone) >= 11 and len(phone) <= 15:
                                return phone
                                
                            else:
                                return None  # Mark invalid numbers for removal

                        df_new['phone'] = df_new['phone'].apply(process_phone)
                        
                        # Remove invalid numbers (None values)
                        df_new = df_new.dropna(subset=['phone'])

                        # Print final processed numbers
                        print("Final processed phone numbers:", df_new['phone'].tolist())

                    # Print final DataFrame to confirm processing
                    print("Final DataFrame after processing:")
                    print(df_new.head())
                    # if 'phone' in df_new.columns:
                    #     print("Original phone numbers:", df_new['phone'].tolist())  # Print before transformation

                    #     df_new['phone'] = df_new['phone'].astype(str)  # Ensure it's a string

                    #     # Remove special characters from phone numbers (keeping only digits)
                    #     df_new['phone'] = df_new['phone'].apply(lambda x: re.sub(r'\D', '', x))  # Remove non-digit characters

                    #     # Print after removing special characters
                    #     print("Phone numbers after removing special characters:", df_new['phone'].tolist())

                    #     # Keep only numeric values and remove numbers shorter than 10 digits
                    #     df_new = df_new[df_new['phone'].str.isdigit()]  
                    #     df_new = df_new[df_new['phone'].str.len() >= 10]  

                    #     # Print after filtering invalid numbers
                    #     print("Filtered phone numbers (only 10+ digits):", df_new['phone'].tolist())
                        
                    #     def process_phone(phone):
                    #         if len(phone) == 10:  
                    #             return '91' + phone
                    #         elif phone.startswith('91') and len(phone) == 12:  
                    #             return phone
                    #         else:
                    #             return None  # Mark invalid numbers for removal

                    #     df_new['phone'] = df_new['phone'].apply(process_phone)
                        
                    #     # Remove invalid numbers (None values)
                    #     df_new = df_new.dropna(subset=['phone'])

                    #     # Print final processed numbers
                    #     print("Final processed phone numbers:", df_new['phone'].tolist())

                    # # Print final DataFrame to confirm processing
                    # print("Final DataFrame after processing:")
                    # print(df_new.head())


                except Exception as e:
                    print(f"Error processing model_name: {e}")
                    return JsonResponse({"error": f"Error processing model_name: {e}"}, status=500)
            else:
                try:
                    file_name = os.path.splitext(xls_file.name)[0]
                    table_name = file_name.lower().replace(' ', '_')  # Ensure table name is lowercase and replace spaces with underscores
                except Exception as e:
                    print(f"Error processing file_name: {e}")
                    return JsonResponse({"error": f"Error processing file_name: {e}"}, status=500)
            df_new = df_new.to_json(orient="records")
            df_new_json = json.loads(df_new)

            # TEMPORARY: Use synchronous upload until Celery queue issue is resolved
            # TODO: Re-enable async after confirming upload_file_queue is being processed
            USE_CELERY = False  # Set to True when Celery is confirmed working

            if USE_CELERY:
                try:
                    bulk_upload_contacts.delay(df_new_json, tenant_id)
                    return JsonResponse({"success": "Contacts are being uploaded", "count": len(df_new_json)}, status = 200)
                except Exception as celery_error:
                    logger.error(f"Celery failed: {celery_error}")
                    USE_CELERY = False  # Fall through to synchronous

            if not USE_CELERY:
                # Synchronous upload - immediate creation
                logger.info(f"Starting synchronous upload of {len(df_new_json)} contacts for tenant {tenant_id}")
                try:
                    from contacts.models import Contact
                    from tenant.models import Tenant

                    tenant = Tenant.objects.get(id=tenant_id)
                    contacts_created = 0
                    contacts_to_create = []

                    for contact_data in df_new_json:
                        contact_fields = {}
                        custom_fields = {}

                        for field, value in contact_data.items():
                            # Skip null/NaN values
                            if pd.isna(value):
                                continue
                            if hasattr(Contact, field) and field not in ['customField', 'tenant', 'id', 'createdOn']:
                                contact_fields[field] = value
                            else:
                                custom_fields[field] = value

                        contact_fields['customField'] = json.dumps(custom_fields) if custom_fields else None
                        contact_fields['tenant'] = tenant

                        contacts_to_create.append(Contact(**contact_fields))
                        contacts_created += 1

                    # Bulk create for better performance
                    Contact.objects.bulk_create(contacts_to_create, ignore_conflicts=True)

                    logger.info(f"Successfully created {contacts_created} contacts synchronously")
                    return JsonResponse({
                        "success": "Contacts uploaded successfully!",
                        "count": contacts_created
                    }, status=200)

                except Exception as sync_error:
                    logger.error(f"Synchronous upload failed: {sync_error}", exc_info=True)
                    return JsonResponse({"error": f"Upload failed: {str(sync_error)}"}, status=500)
            
        except Exception as e:
            print(f"Unexpected error: {e}")
            return JsonResponse({"error": f"Unexpected error: {e}"}, status=500)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)
