from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse
import os
import pandas as pd
import json
import requests
import pymupdf
import logging
from .vectorize import vectorize_FAISS, vectorize
from .table_from_img import data_from_image
from .upload_csv import upload_file

logger = logging.getLogger(__name__)

# ============================================================================
# FILE UPLOAD LIMITS - Prevent memory exhaustion and DoS
# ============================================================================
MAX_FILE_SIZE_MB = 50  # Maximum file size in MB
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_ROWS = 100000  # Maximum rows in CSV/Excel files


def validate_file_upload(uploaded_file):
    """
    Validate uploaded file size and basic sanity checks.
    Raises ValueError if validation fails.
    """
    if not uploaded_file:
        raise ValueError("No file provided")

    # Check file size
    file_size = uploaded_file.size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(
            f"File too large: {file_size / (1024*1024):.1f}MB. "
            f"Maximum allowed: {MAX_FILE_SIZE_MB}MB"
        )

    # Check file name
    if not uploaded_file.name:
        raise ValueError("File must have a name")

    file_extension = os.path.splitext(uploaded_file.name)[1].lower()
    allowed_extensions = ['.csv', '.xlsx', '.xls', '.pdf', '.png', '.jpg', '.jpeg']

    if file_extension not in allowed_extensions:
        raise ValueError(
            f"Unsupported file type: {file_extension}. "
            f"Allowed: {', '.join(allowed_extensions)}"
        )

    logger.info(f"📁 File validated: {uploaded_file.name} ({file_size / 1024:.1f}KB)")
    return True


def validate_dataframe_size(df, filename="file"):
    """
    Validate DataFrame row count to prevent memory issues.
    """
    if len(df) > MAX_ROWS:
        raise ValueError(
            f"Too many rows in {filename}: {len(df):,}. "
            f"Maximum allowed: {MAX_ROWS:,}"
        )
    logger.info(f"📊 DataFrame validated: {len(df):,} rows")
    return True



def create_subfile(df, columns_text, merge_columns):
    print("DataFrame columns: ", df.columns)

    def get_column_names(df, indices):
        return [df.columns[i] for i in indices]

    df_new = df.copy()   

    if merge_columns:
        try:
            merge_columns_dict = json.loads(merge_columns)  
            print("Merge columns dict: ", merge_columns_dict)

            for new_col, indices in merge_columns_dict.items():
                desc = False
                if indices[0] == "desc":
                    desc = True
                    indices = indices[1:]  
                    
                if len(indices) < 2:
                    return JsonResponse({'error': 'Merge columns should be a list of at least two indices'}, status=400)

                try:
                    columns = get_column_names(df, indices)
                    if desc:
                        df_new[new_col] = df_new[columns].apply(
                            lambda x: ', '.join([f'{col}: {val}' for col, val in zip(columns, x)]), axis=1)
                    else:
                        df_new[new_col] = df_new[columns].astype(str).agg(', '.join, axis=1)

                    print(f"New column '{new_col}':", df_new[new_col])
                except IndexError:
                    return JsonResponse({'error': 'One or more column indices are out of range'}, status=400)

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            return JsonResponse({'error': 'Invalid JSON format for merge_columns'}, status=400)
        except Exception as e:
            print("Exception:", e)
            return JsonResponse({'error': str(e)}, status=400)

    if columns_text:
        try:
            columns_dict = json.loads(columns_text)
            print("Columns dict:", columns_dict)

            columns_dict_with_names = {}
            for old_index, new_name in columns_dict.items():
                try:
                    old_col = df.columns[int(old_index)]
                    columns_dict_with_names[old_col] = new_name
                except IndexError:
                    return JsonResponse({'error': f'Column index {old_index} is out of range'}, status=400)

            
            df_new = df_new.rename(columns=columns_dict_with_names)

            
            df_new = df_new[list(columns_dict.values()) + (list(merge_columns_dict.keys()) if merge_columns else [])]

        except json.JSONDecodeError as e:
            print("JSONDecodeError:", e)
            return JsonResponse({'error': 'Invalid JSON format for columns'}, status=400)
        except KeyError as e:
            print("KeyError:", e)
            return JsonResponse({'error': f'Column {e} not found in the input file'}, status=400)
        except Exception as e:
            print("Exception:", e)
            return JsonResponse({'error': str(e)}, status=400)
    else:
        
        df_new = df

    print("Final DataFrame created")
    return df_new


@csrf_exempt
def dispatcher(request):
    try:
        if request.method == 'POST':
            uploaded_file = request.FILES.get('file')
            json_data = request.POST.get('jsonData')
            columns_text = request.POST.get('columns')
            merge_columns = request.POST.get('merge_columns')
            tenant_id = request.headers.get('X-Tenant-Id')

            if uploaded_file:
                # SECURITY: Validate file before processing
                try:
                    validate_file_upload(uploaded_file)
                except ValueError as e:
                    logger.warning(f"⚠️ File validation failed: {e}")
                    return JsonResponse({'error': str(e)}, status=400)

                file_name = uploaded_file.name
                file_extension = os.path.splitext(uploaded_file.name)[1].lower()
                logger.info(f"📁 Processing upload: {file_name} ({file_extension})")

            if file_extension == '.pdf':
                try:
                    print("Processing PDF File")
                    if file_extension == '.pdf':
                        pdf_file = uploaded_file.read()
                    else:
                        pdf_file = uploaded_file
                    
                    # vectorize(pdf_file=pdf_file)
                    return vectorize_FAISS(pdf_file, file_name, json_data, tenant_id)
                except Exception as e:
                    return JsonResponse({'error': f"Failed to process PDF: {str(e)}"}, status=500)

            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
                try:
                    return data_from_image(request)
                except Exception as e:
                    return JsonResponse({'error': f"Failed to process image: {str(e)}"}, status=500)

            elif file_extension == '.csv':
                if not uploaded_file:
                    return JsonResponse({'error': 'Input file must be provided'}, status=400)

                try:
                    df = pd.read_csv(uploaded_file)
                except pd.errors.EmptyDataError:
                    return JsonResponse({'error': 'The CSV file is empty'}, status=400)
                except pd.errors.ParserError:
                    return JsonResponse({'error': 'Error parsing CSV file'}, status=400)
                except Exception as e:
                    return JsonResponse({'error': f"Error reading CSV file: {str(e)}"}, status=400)

                # SECURITY: Validate row count
                try:
                    validate_dataframe_size(df, file_name)
                except ValueError as e:
                    return JsonResponse({'error': str(e)}, status=400)

                try:
                    new_df = create_subfile(df, columns_text, merge_columns)
                    return upload_file(request, new_df)
                except Exception as e:
                    return JsonResponse({'error': f"Error processing CSV file: {str(e)}"}, status=500)

            elif file_extension in ['.xls', '.xlsx']:

                if not uploaded_file:
                    return JsonResponse({'error': 'Input file must be provided'}, status=400)

                try:
                    # Read metadata (sheet names)
                    excel_file = pd.ExcelFile(uploaded_file)
                    sheet_names = excel_file.sheet_names
                    print("📄 Sheets detected:", sheet_names)

                    # Selection logic
                    if "Contacts" in sheet_names:
                        df = pd.read_excel(uploaded_file, sheet_name="Contacts")
                    elif len(sheet_names) == 1:
                        df = pd.read_excel(uploaded_file, sheet_name=sheet_names[0])
                    else:
                        return JsonResponse({
                            'error': (
                                "Multiple sheets found but none named 'Contacts'.\n\n"
                                "To avoid mistakes, please name the sheet containing data as 'Contacts'.\n"
                                f"Sheets found: {', '.join(sheet_names)}"
                            )
                        }, status=400)

                except Exception as e:
                    return JsonResponse({'error': f"Error reading Excel file: {str(e)}"}, status=400)

                # SECURITY: Validate row count
                try:
                    validate_dataframe_size(df, file_name)
                except ValueError as e:
                    return JsonResponse({'error': str(e)}, status=400)

                # ---------------- VALIDATION ----------------

                # RELAXED REQUIREMENTS: Only phone is mandatory
                mandatory_columns = {"phone"}
                recommended_columns = {
                    "first_name", "last_name", "name", "company_name", "address", "city",
                    "county", "state", "zip", "email"
                }

                # Normalize column names for validation (CASE INSENSITIVE)
                cleaned_df_columns = {str(col).strip().lower(): col for col in df.columns}

                # Check for mandatory phone column
                if "phone" not in cleaned_df_columns:
                    return JsonResponse({
                        'error': (
                            "Missing required column: 'phone'\n\n"
                            "The Excel file MUST have a 'phone' column with valid phone numbers.\n\n"
                            "Recommended columns:\n" +
                            ", ".join(sorted(recommended_columns)) +
                            "\n\nOther columns are optional and will be stored as custom fields."
                        )
                    }, status=400)

                # Ensure phone column has some usable data
                phone_col_name = cleaned_df_columns["phone"]
                if df[phone_col_name].isnull().all():
                    return JsonResponse({
                        'error': (
                            "The 'phone' column is empty.\n\n"
                            "Please ensure at least one row has a valid phone number.\n"
                            "Valid formats: 10-digit (9123456789), 12-digit with country code (919123456789)"
                        )
                    }, status=400)

                # ---------------- NORMALIZATION ----------------

                # Rename columns to lowercase for consistency
                df.columns = [str(col).strip().lower() for col in df.columns]

                # Merge first_name + last_name into 'name' if needed
                if 'first_name' in df.columns and 'last_name' in df.columns:
                    if 'name' not in df.columns:
                        df['name'] = df['first_name'].fillna('') + ' ' + df['last_name'].fillna('')
                        df['name'] = df['name'].str.strip()

                # Ensure phone column is first, followed by name/email if present
                priority_cols = ['phone', 'name', 'first_name', 'last_name', 'email']
                ordered_cols = [c for c in priority_cols if c in df.columns] + \
                               [c for c in df.columns if c not in priority_cols]
                df = df[ordered_cols]

                # ---------------- FINAL PROCESS ----------------
                try:
                    new_df = create_subfile(df, columns_text=columns_text, merge_columns=merge_columns)
                    return upload_file(request, new_df)
                except Exception as e:
                    return JsonResponse({'error': f"Error processing Excel data: {str(e)}"}, status=500)

            else:
                return HttpResponseBadRequest('Unsupported file type.')
        else:
            return HttpResponseBadRequest('No file uploaded.')
    
    except Exception as e:
        return JsonResponse({'error': f"Unexpected error occurred: {str(e)}"}, status=500)