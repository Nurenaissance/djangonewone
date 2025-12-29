
from .models import Contact,Tenant
from .serializers import ContactSerializer
from django.http import JsonResponse
from datetime import datetime
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework import status, views
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView
from django.views.decorators.csrf import csrf_exempt
from helpers.tables import get_db_connection
from whatsapp_chat.models import WhatsappTenantData
from .tasks import update_contact_last_seen
from django.utils import timezone



from rest_framework.views import APIView


class ContactcustomfieldAPIView(ListCreateAPIView):
    """
    API endpoint to handle incoming webhook data and store it in Contact model
    """
    def post(self, request, *args, **kwargs):
        try:
            # Get tenant ID from header
            tenant_id = request.headers.get('X-Tenant-Id')
            if not tenant_id:
                return Response({
                    'error': 'X-Tenant-Id header is required',
                    'message': 'Missing tenant information'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get tenant instance
            try:
                tenant_instance = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return Response({
                    'error': f'Tenant with ID {tenant_id} not found',
                    'message': 'Invalid tenant information'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get all model fields from Contact model
            model_fields = [field.name for field in Contact._meta.fields]
            
            # Identify foreign key fields that need special handling
            foreign_key_fields = ['tenant', 'createdBy']
            
            # Initialize data dictionaries
            contact_data = {'tenant': tenant_instance}  # Set tenant from header
            custom_field_data = {}  # For fields to store in customField JSONField
            
            # Handle createdBy if it exists in request data
            if 'createdBy' in request.data:
                value = request.data.get('createdBy')
                if value:
                    custom_field_data['createdBy'] = value
            
            # Process all other fields in the request data
            for key, value in request.data.items():
                if key in foreign_key_fields:
                    # Skip foreign keys as we already handled them
                    continue
                
                if key in model_fields:
                    # If the key matches a model field, store directly
                    contact_data[key] = value
                else:
                    # Otherwise, store in customField
                    custom_field_data[key] = value
            
            # Add customField to contact_data
            contact_data['customField'] = custom_field_data
            
            # Check if a contact with the given phone number and tenant already exists
            existing_contact = None
            if 'phone' in contact_data:
                try:
                    # Filter by both phone and tenant
                    existing_contact = Contact.objects.get(
                        phone=contact_data['phone'],
                        tenant=tenant_instance
                    )
                except Contact.DoesNotExist:
                    # No existing contact found with this phone number in this tenant
                    pass
                except Contact.MultipleObjectsReturned:
                    # Handle the case where multiple contacts have the same phone in the same tenant
                    logger.warning(f"Multiple contacts found with phone {contact_data['phone']} in tenant {tenant_instance.id}")
                    # Get the most recently updated one
                    existing_contact = Contact.objects.filter(
                        phone=contact_data['phone'],
                        tenant=tenant_instance
                    ).order_by('-createdOn').first()
            
            if existing_contact:
                # Update existing contact with new data
                for key, value in contact_data.items():
                    if key == 'customField':
                        # Merge customField dictionaries (existing + new)
                        current_custom_fields = existing_contact.customField or {}
                        current_custom_fields.update(value)
                        setattr(existing_contact, key, current_custom_fields)
                    else:
                        setattr(existing_contact, key, value)
                
                existing_contact.save()
                contact = existing_contact
                status_code = status.HTTP_200_OK
                message = "Contact updated successfully"
            else:
                # Create a new contact
                contact = Contact.objects.create(**contact_data)
                status_code = status.HTTP_201_CREATED
                message = "Contact created successfully"
            
            serializer = ContactSerializer(contact)
            return Response({
                'data': serializer.data,
                'message': message
            }, status=status_code)
        
        except Exception as e:
            return Response({
                'error': str(e),
                'message': 'Failed to process webhook data'
            }, status=status.HTTP_400_BAD_REQUEST)
        
# class ContactcustomfieldAPIView(ListCreateAPIView):
#     """
#     API endpoint to handle incoming webhook data and store it in Contact model
#     """
#     def post(self, request, *args, **kwargs):
#         try:
#             # Get all model fields from Contact model
#             model_fields = [field.name for field in Contact._meta.fields]
            
#             # Identify foreign key fields that need special handling
#             foreign_key_fields = ['tenant', 'createdBy']
            
#             # Initialize data dictionaries
#             contact_data = {}  # For fields directly in the Contact model
#             custom_field_data = {}  # For fields to store in customField JSONField
            
#             # Handle foreign key fields first
#             for fk_field in foreign_key_fields:
#                 if fk_field in request.data:
#                     value = request.data.get(fk_field)
#                     if value:
#                         if fk_field == 'tenant':
#                             # Handle tenant field
#                             try:
#                                 # Use the serializer to get the tenant instance
#                                 partial_data = {'tenant': value}
#                                 temp_serializer = ContactSerializer(data=partial_data, partial=True)
#                                 # Just validate, don't save yet
#                                 if temp_serializer.is_valid():
#                                     # Extract the tenant instance from validated data
#                                     tenant_instance = temp_serializer.validated_data.get('tenant')
#                                     if tenant_instance:
#                                         contact_data['tenant'] = tenant_instance
#                                     else:
#                                         # If serializer didn't convert it, try manual lookup
#                                         try:
#                                             tenant_instance = Tenant.objects.get(id=value)
#                                             contact_data['tenant'] = tenant_instance
#                                         except (ValueError, Tenant.DoesNotExist):
#                                             try:
#                                                 tenant_instance = Tenant.objects.get(name=value)
#                                                 contact_data['tenant'] = tenant_instance
#                                             except (Tenant.DoesNotExist, AttributeError):
#                                                 # If all fails, store in customField
#                                                 custom_field_data[fk_field] = value
#                                 else:
#                                     # If validation fails, store in customField
#                                     custom_field_data[fk_field] = value
#                             except Exception as e:
#                                 logger.error(f"Error handling tenant: {str(e)}")
#                                 custom_field_data[fk_field] = value
#                         elif fk_field == 'createdBy':
#                             # Handle createdBy field (User model)
#                             # Similar approach as tenant if needed
#                             custom_field_data[fk_field] = value
            
#             # Process all other fields in the request data
#             for key, value in request.data.items():
#                 if key in foreign_key_fields:
#                     # Skip foreign keys as we already handled them
#                     continue
                
#                 if key in model_fields:
#                     # If the key matches a model field, store directly
#                     contact_data[key] = value
#                 else:
#                     # Otherwise, store in customField
#                     custom_field_data[key] = value
            
#             # Add customField to contact_data
#             contact_data['customField'] = custom_field_data
            
#             # Simply create a new contact without checking if it exists
#             contact = Contact.objects.create(**contact_data)
            
#             serializer = ContactSerializer(contact)
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#         except Exception as e:
#             return Response({
#                 'error': str(e),
#                 'message': 'Failed to process webhook data'
#             }, status=status.HTTP_400_BAD_REQUEST)
class ContactListCreateAPIView(ListCreateAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    # permission_classes = (IsAdminUser,)  # Optionally, add permission classes

class ContactDetailAPIView(RetrieveUpdateDestroyAPIView):
    queryset = Contact.objects.all()
    serializer_class = ContactSerializer
    # permission_classes = (IsAdminUser,)  # Optionally, add permission classes

class ContactByAccountAPIView(ListCreateAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        account_id = self.kwargs.get('account_id')  # Get account ID from URL parameters
        return Contact.objects.filter(account_id=account_id)  # Filter by 
    
class ContactByPhoneAPIView(ListCreateAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        phone = self.kwargs.get('phone')
        tenant_id = self.request.headers.get('X-Tenant-Id')

        # Validate inputs
        if not phone or not tenant_id:
            raise ValidationError("Both 'phone' and 'X-Tenant-Id' are required.")

        try:
            phone_str = str(phone)
            queryset = Contact.objects.filter(phone=phone_str, tenant=tenant_id)
            print(f"Query executed: {queryset.query}")  # Log the query
            return queryset
        except Exception as e:
            print(f"An error occurred while fetching contacts: {e}")
            raise APIException(f"An error occurred while fetching contacts: {e}")

    def list(self, request, *args, **kwargs):
        try:
            # Get the original response
            response = super().list(request, *args, **kwargs)
            print("Response Data: ", response.data)
            # Flatten customField in the response data
            for item in response.data:
                if 'customField' in item and item['customField'] is not None:
                    custom_fields = item.pop('customField')  # Remove customField
                    item.update(custom_fields)  # Merge customField into the parent object

            return response
        except Exception as e:
            print(f"An error occurred while processing the response: {e}")
            return Response(
                {"error": "An error occurred while processing the response."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class ContactByTenantAPIView(CreateAPIView):
    serializer_class = ContactSerializer

    def get_queryset(self):
        tenant_id = self.request.headers.get('X-Tenant-Id')
        return Contact.objects.filter(tenant_id=tenant_id)
    
    def create(self, request, *args, **kwargs):
        try:
            bpid = request.headers.get('bpid')
            whatsapp_tenant_data = WhatsappTenantData.objects.filter(business_phone_number_id = bpid).first()
            tenant_id = whatsapp_tenant_data.tenant_id
            contact_data = request.data
            name = contact_data.get('name')
            phone = contact_data.get('phone')

            contact_exists = Contact.objects.filter(tenant_id=tenant_id, phone=phone).exists()

            if contact_exists:
                contact = Contact.objects.get(tenant_id=tenant_id, phone=phone)
                if name:
                    contact.name = name
                    contact.save()
                return Response(
                    {"detail": "Contact already exists under this tenant."},
                    status=status.HTTP_200_OK
                )

            serializer = self.get_serializer(data=contact_data)
            serializer.is_valid(raise_exception=True)
            serializer.save(tenant_id=tenant_id)  # Save with tenant_id from headers
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except WhatsappTenantData.DoesNotExist:
            return Response(
                {"detail": "Tenant-ID header is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class UpdateContactAPIView(views.APIView):
    def patch(self, request, *args, **kwargs):
        try:
            data = request.data
            phone = data.get('phone')
            tenant_id = request.headers.get('X-Tenant-Id')

            errors = []
            contact = Contact.objects.filter(phone=phone, tenant_id=tenant_id).first()
            if not contact:
                raise Contact.DoesNotExist

            # Update all fields including 'template_key'
            for field, value in data.items():
                if hasattr(contact, field):
                    setattr(contact, field, value)

            contact.save()
            print(f"Contact {phone} updated successfully")
        except Contact.DoesNotExist:
            print("Error in fetching contact: ")
            errors.append(f"Contact with phone {phone} does not exist.")
        except Exception as e:
            print("Error: ", str(e))
            errors.append(str(e))

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Contact updated successfully"}, status=status.HTTP_200_OK)
    
from django.shortcuts import get_object_or_404
from communication.models import Conversation
from topicmodelling.models import TopicModelling

def delete_contact_by_phone(request, phone_number):
    try:
        # Get the contact based on phone number
        contact = get_object_or_404(Contact, phone=phone_number)

        # Find all conversations related to this contact
        conversations = Conversation.objects.filter(contact_id=contact)

        # Loop through conversations and delete related TopicModelling entries
        for conversation in conversations:
            # Delete the related TopicModelling
            TopicModelling.objects.filter(conversation=conversation).delete()

            # Delete the conversation
            conversation.delete()

        # Finally, delete the contact
        contact.delete()

        return JsonResponse({"message": f"Contact with phone number {phone_number} and related data deleted successfully."}, status=200)

    except Contact.DoesNotExist:
        return JsonResponse({"message": f"Contact with phone number {phone_number} does not exist."}, status=404)

    except Exception as e:
        return JsonResponse({"message": str(e)}, status=500)

@csrf_exempt
def get_contacts_sql(req):
    if req.method == "GET":

        query = "SELECT * FROM public.contacts_contact"
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(query)
        results = cursor.fetchall()

        columns = [col[0] for col in cursor.description]  # Get column names
        results = [dict(zip(columns, row)) for row in results]

        print(results)

        return JsonResponse(results , safe=False)


import logging
from .models import Contact

logger = logging.getLogger(__name__)


# views.py
import logging, json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)

def convert_time(datetime_str):
    """
    Converts a date-time string from 'DD/MM/YYYY, HH:MM:SS.SSS'
    to PostgreSQL-compatible 'YYYY-MM-DD HH:MM:SS.SSS' format.
    
    Args:
        datetime_str (str): The date-time string to be converted.
    
    Returns:
        str: Converted date-time string in PostgreSQL format.
    """
    try:
        parsed_datetime = datetime.strptime(datetime_str, "%d/%m/%Y, %H:%M:%S.%f")
        print("Parsed Time: ", parsed_datetime)
        aware_time = make_aware(parsed_datetime)
        print("Aware Date time: ", aware_time)
        return aware_time
    except ValueError as e:
        print(f"Error converting datetime: {e}")
        return None
    

import threading

def async_last_seen(phone, type, time, tenant):
    try:
        update_contact_last_seen(phone, type, time, tenant)
    except Exception as e:
        logger.error(f"Async last_seen failed: {e}")


@csrf_exempt
@require_http_methods(["PATCH"])
def updateLastSeen(request, phone, type):
    try:
        formatted_timestamp = timezone.now()

        bpid = request.headers.get("bpid")
        whatsapp_tenant_data = WhatsappTenantData.objects.filter(
            business_phone_number_id=bpid
        ).first()

        tenant_id = whatsapp_tenant_data.tenant_id

        threading.Thread(
            target=async_last_seen,
            args=(phone, type, formatted_timestamp, tenant_id),
            daemon=True
        ).start()

        return JsonResponse({
            "success": True,
            "message": "Update accepted"
        }, status=202)

    except Exception as e:
        return JsonResponse({
            "error": "Internal server error",
            "details": str(e)
        }, status=500)
   
# Optional: Task status checking view
def check_task_status(request, task_id):
    """
    Check the status of a queued task
    
    :param request: HTTP request
    :param task_id: ID of the Celery task
    :return: JSON response with task status
    """
    try:
        from celery.result import AsyncResult
        
        task_result = AsyncResult(task_id)
        
        return JsonResponse({
            "task_id": task_id,
            "status": task_result.status,
            "result": task_result.result
        })
    
    except Exception as e:
        logger.error(f"Error checking task status: {e}")
        return JsonResponse({"error": "Could not retrieve task status"}, status=500)

