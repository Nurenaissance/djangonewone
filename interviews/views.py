from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.db.models import Q
from .models import InterviewResponse
from .serializers import InterviewResponseSerializer, InterviewResponseCreateSerializer
from tenant.models import Tenant
from interaction.models import Conversation
from contacts.models import Contact
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import re

logger = logging.getLogger(__name__)


class InterviewResponseListView(generics.ListAPIView):
    """
    GET /interviews/responses/
    Fetch all interview responses for a tenant
    Requires X-Tenant-Id header
    """
    serializer_class = InterviewResponseSerializer

    def get_queryset(self):
        tenant_id = self.request.headers.get('X-Tenant-Id') or self.request.headers.get('X-Tenant-ID')
        flow_name = self.request.query_params.get('flow_name', 'interviewdrishtee')

        if not tenant_id:
            return InterviewResponse.objects.none()

        queryset = InterviewResponse.objects.filter(
            tenant_id=tenant_id,
            flow_name=flow_name
        ).select_related('tenant').order_by('-timestamp')

        # Optional filtering by phone number
        phone_no = self.request.query_params.get('phone_no')
        if phone_no:
            queryset = queryset.filter(phone_no=phone_no)

        # Optional filtering by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        return queryset


class InterviewResponseCreateView(generics.CreateAPIView):
    """
    POST /interviews/responses/
    Create a new interview response
    Requires X-Tenant-Id header
    Body: {
        "phone_no": "919999999999",
        "candidate_name": "John Doe",
        "name": "John",
        "address": "123 Main St",
        "calibration": "passed",
        "status": "completed",
        "question1": "audio_url_or_media_id_1",
        "question2": "audio_url_or_media_id_2",
        "question3": "audio_url_or_media_id_3",
        "question4": "audio_url_or_media_id_4"
    }
    """
    serializer_class = InterviewResponseCreateSerializer

    def create(self, request, *args, **kwargs):
        tenant_id = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')

        if not tenant_id:
            return Response(
                {"error": "X-Tenant-Id header is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            tenant = Tenant.objects.get(tenant_id=tenant_id)
        except Tenant.DoesNotExist:
            return Response(
                {"error": f"Tenant {tenant_id} not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Add tenant to request data
        data = request.data.copy()
        data['tenant'] = tenant.id
        if 'flow_name' not in data:
            data['flow_name'] = 'interviewdrishtee'

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        logger.info(f"Interview response created for phone: {data.get('phone_no')} in tenant: {tenant_id}")

        return Response(
            {
                "message": "Interview response saved successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )


class InterviewResponseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /interviews/responses/<id>/
    Retrieve, update, or delete a specific interview response
    Requires X-Tenant-Id header
    """
    serializer_class = InterviewResponseSerializer

    def get_queryset(self):
        tenant_id = self.request.headers.get('X-Tenant-Id') or self.request.headers.get('X-Tenant-ID')
        if not tenant_id:
            return InterviewResponse.objects.none()

        return InterviewResponse.objects.filter(tenant_id=tenant_id)


@api_view(['POST'])
def save_interview_from_flow(request):
    """
    POST /interviews/save-from-flow/
    Save interview response from WhatsApp flow execution
    This endpoint is called by the WhatsApp bot when flow completes

    Body: {
        "phone_no": "919999999999",
        "tenant_id": "ehgymjv",
        "variables": {
            "name": "John",
            "address": "123 Main St",
            "candidate_name": "John Doe",
            "calibration": "passed",
            "question1": "media_id_1",
            "question2": "media_id_2",
            "question3": "media_id_3",
            "question4": "media_id_4"
        },
        "status": "completed"
    }
    """
    try:
        phone_no = request.data.get('phone_no')
        tenant_id = request.data.get('tenant_id') or request.headers.get('X-Tenant-Id')
        variables = request.data.get('variables', {})
        status_value = request.data.get('status', 'completed')

        if not phone_no or not tenant_id:
            return Response(
                {"error": "phone_no and tenant_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        tenant = Tenant.objects.get(tenant_id=tenant_id)

        # Create interview response
        interview_response = InterviewResponse.objects.create(
            phone_no=phone_no,
            tenant=tenant,
            flow_name='interviewdrishtee',
            candidate_name=variables.get('candidate_name', ''),
            name=variables.get('name', ''),
            address=variables.get('address', ''),
            calibration=variables.get('calibration', ''),
            status=status_value,
            question1=variables.get('question1', ''),
            question2=variables.get('question2', ''),
            question3=variables.get('question3', ''),
            question4=variables.get('question4', '')
        )

        serializer = InterviewResponseSerializer(interview_response)

        logger.info(f"Interview response saved from flow for {phone_no}")

        return Response(
            {
                "message": "Interview response saved successfully",
                "data": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    except Tenant.DoesNotExist:
        return Response(
            {"error": f"Tenant {tenant_id} not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error saving interview from flow: {str(e)}")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def interview_stats(request):
    """
    GET /interviews/stats/
    Get statistics for interview responses
    Requires X-Tenant-Id header
    """
    tenant_id = request.headers.get('X-Tenant-Id') or request.headers.get('X-Tenant-ID')
    if not tenant_id:
        return Response(
            {"error": "X-Tenant-Id header is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    flow_name = request.query_params.get('flow_name', 'interviewdrishtee')

    total_responses = InterviewResponse.objects.filter(
        tenant_id=tenant_id,
        flow_name=flow_name
    ).count()

    unique_numbers = InterviewResponse.objects.filter(
        tenant_id=tenant_id,
        flow_name=flow_name
    ).values('phone_no').distinct().count()

    status_counts = {}
    statuses = InterviewResponse.objects.filter(
        tenant_id=tenant_id,
        flow_name=flow_name
    ).values('status').distinct()

    for status_obj in statuses:
        status_name = status_obj['status']
        count = InterviewResponse.objects.filter(
            tenant_id=tenant_id,
            flow_name=flow_name,
            status=status_name
        ).count()
        status_counts[status_name] = count

    return Response({
        "total_responses": total_responses,
        "unique_numbers": unique_numbers,
        "status_breakdown": status_counts
    })


# Helper functions for import
def extract_phone_number(contact_id):
    """Clean phone number"""
    phone = re.sub(r'\D', '', contact_id)
    if len(phone) == 10:
        return f"91{phone}"
    return phone


def group_into_sessions(conversations, session_gap_hours=2):
    """
    Group conversations into sessions based on time gaps
    If gap between messages > session_gap_hours, start new session
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
        if last_timestamp is None or (conv.date_time - last_timestamp) > timedelta(hours=session_gap_hours):
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


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def import_from_direct_chat(request):
    """
    POST/GET /interviews/import-from-chat/
    Import interview data from Direct Chat conversations
    Creates separate entries for each conversation session

    Query params or Body:
        tenant_id: Tenant ID (default: ehgymjv)
        session_gap_hours: Hours between sessions (default: 2)

    Returns:
        {
            "success": true,
            "imported_count": 71,
            "skipped_count": 29,
            "total_sessions": 100,
            "message": "Import completed successfully"
        }
    """
    try:
        # Get parameters
        if request.method == 'POST':
            tenant_id = request.data.get('tenant_id', 'ehgymjv')
            session_gap_hours = int(request.data.get('session_gap_hours', 2))
        else:
            tenant_id = request.query_params.get('tenant_id', 'ehgymjv')
            session_gap_hours = int(request.query_params.get('session_gap_hours', 2))

        # Get tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": f"Tenant {tenant_id} not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        # Get all conversations
        conversations = Conversation.objects.filter(
            tenant=tenant,
            sender='user'
        ).order_by('contact_id', 'date_time')

        logger.info(f"Import: Found {conversations.count()} user messages for tenant {tenant_id}")

        # Group by phone first
        phone_conversations = defaultdict(list)
        for conv in conversations:
            phone = extract_phone_number(conv.contact_id)
            phone_conversations[phone].append(conv)

        # Now group each phone's conversations into sessions
        all_sessions = []
        for phone, convs in phone_conversations.items():
            sessions = group_into_sessions(convs, session_gap_hours)
            for session in sessions:
                all_sessions.append((phone, session))

        logger.info(f"Import: Found {len(all_sessions)} total sessions")

        # Process each session
        imported_count = 0
        skipped_count = 0
        imported_details = []

        for phone, session in all_sessions:
            session_data = extract_session_data(session)
            audio_count = len(session_data['audio_urls'])
            has_calibration = session_data['calibration_audio'] or session_data['calibration_text']

            # Get session timestamp
            if not session_data['timestamps']:
                skipped_count += 1
                continue

            session_start = min(session_data['timestamps'])
            session_end = max(session_data['timestamps'])

            # Skip if no audio
            if audio_count == 0 and not has_calibration:
                skipped_count += 1
                continue

            # Check if this exact session already exists
            existing = InterviewResponse.objects.filter(
                phone_no=phone,
                tenant=tenant,
                timestamp=session_start
            ).first()

            if existing:
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

            imported_count += 1
            imported_details.append({
                'id': response.id,
                'phone_no': phone,
                'session_time': session_start.strftime('%Y-%m-%d %H:%M'),
                'audio_count': audio_count
            })

            logger.info(f"Import: Created entry ID {response.id} for {phone}")

        # Return summary
        return Response({
            "success": True,
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "total_sessions": len(all_sessions),
            "message": f"Import completed successfully. Imported {imported_count} sessions, skipped {skipped_count}.",
            "details": imported_details[:20]  # Return first 20 for reference
        })

    except Exception as e:
        logger.error(f"Error importing from direct chat: {str(e)}")
        return Response(
            {
                "success": False,
                "error": str(e)
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
