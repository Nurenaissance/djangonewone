from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Q
from .models import InterviewResponse
from .serializers import InterviewResponseSerializer, InterviewResponseCreateSerializer
from tenant.models import Tenant
import logging

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
