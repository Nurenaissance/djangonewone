


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import WhatsappCampaign, MessageTemplate, Campaign, BroadcastGroup
from .serializers import MessageTemplateSerializer, CampaignSerializer, BroadcastGroupSerializer
from tenant.models import Tenant
from rest_framework.parsers import JSONParser
from whatsapp_chat.models import WhatsappTenantData

class WhatsappCampaignView(APIView):
    """
    Handle CRUD operations for WhatsappCampaign.
    """
    parser_classes = [JSONParser]

    def get(self, request, *args, **kwargs):
        """
        Retrieve all campaigns or a specific campaign by ID.
        """
        campaign_id = request.query_params.get('id', None)
        tenant_id = request.headers.get('X-Tenant-Id')
        if campaign_id:
            campaign = get_object_or_404(WhatsappCampaign, id=campaign_id, tenant_id = tenant_id)
            return Response({
                "id": campaign.id,
                "name": campaign.name,
                # "bpid": campaign.bpid,
                # "access_token": campaign.access_token,
                # "account_id": campaign.account_id,
                "tenant_id": campaign.tenant.id,
                "phone": campaign.phone,
                "templates_data": campaign.templates_data,
                "init": 1
            }, status=status.HTTP_200_OK)

        campaigns = WhatsappCampaign.objects.filter(tenant_id = tenant_id)
        data = [
            {
                "id": campaign.id,
                "name": campaign.name,
                "bpid": campaign.bpid,
                "access_token": campaign.access_token,
                "account_id": campaign.account_id,
                "tenant_id": campaign.tenant.id,
                "phone": campaign.phone,
                "templates_data": campaign.templates_data
            }
            for campaign in campaigns
        ]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        """
        Add a new campaign to the database.
        """
        try:
            # Validate tenant ID
            tenant_id = request.headers.get("X-Tenant-Id")
            if not tenant_id:
                return Response(
                    {"error": "X-Tenant-Id header is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            tenant = get_object_or_404(Tenant, id=tenant_id)
            
            # Fetch WhatsApp tenant data
            whatsapp_data = WhatsappTenantData.objects.filter(tenant_id=tenant_id)

            if not whatsapp_data.exists():
                return Response(
                    {"detail": "No WhatsappTenantData found for this tenant_id."},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Example: Use the first record
            whatsapp_data = whatsapp_data.first()
            
            # Validate required fields in request data
            required_fields = ["name", "phone", "templates_data"]
            missing_fields = [field for field in required_fields if field not in request.data]
            if missing_fields:
                return Response(
                    {"error": f"Missing required fields: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Create the campaign
            campaign = WhatsappCampaign.objects.create(
                name=request.data.get("name"),
                bpid=whatsapp_data.business_phone_number_id,
                access_token=whatsapp_data.access_token,
                account_id=whatsapp_data.business_account_id,
                tenant=tenant,
                phone=request.data.get("phone"),
                templates_data=request.data.get("templates_data"),
            )

            return Response(
                {
                    "message": "Campaign created successfully!",
                    "id": campaign.id,
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def patch(self, request, *args, **kwargs):
        """
        Update an existing campaign partially.
        """
        campaign_id = request.data.get('id')
        campaign = get_object_or_404(WhatsappCampaign, id=campaign_id)
        
        for key, value in request.data.items():
            if hasattr(campaign, key) and key != 'id':  # Exclude ID
                setattr(campaign, key, value)
        
        campaign.save()
        return Response({
            "message": "Campaign updated successfully!",
            "id": campaign.id
        }, status=status.HTTP_200_OK)

    def delete(self, request, *args, **kwargs):
        """
        Delete a campaign by ID.
        """
        campaign_id = request.query_params.get('id')
        campaign = get_object_or_404(WhatsappCampaign, id=campaign_id)
        campaign.delete()
        return Response({
            "message": "Campaign deleted successfully!"
        }, status=status.HTTP_204_NO_CONTENT)


class MessageTemplateListCreateView(APIView):
    """
    API endpoint for MessageTemplate LIST and CREATE operations
    GET /api/templates/ - List all templates for tenant
    POST /api/templates/ - Create new template
    """

    def get(self, request, *args, **kwargs):
        """List all message templates for tenant"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            templates = MessageTemplate.objects.filter(tenant_id=tenant_id)
            serializer = MessageTemplateSerializer(templates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """Create new message template"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get tenant object
            tenant = get_object_or_404(Tenant, id=tenant_id)

            # Add tenant to request data
            data = request.data.copy()
            data['tenant'] = tenant.id

            serializer = MessageTemplateSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MessageTemplateDetailView(APIView):
    """
    API endpoint to retrieve, update, or delete template by template_id
    GET /api/templates/{template_id}/
    PATCH /api/templates/{template_id}/
    DELETE /api/templates/{template_id}/
    """

    def get(self, request, template_id, *args, **kwargs):
        """Retrieve template details by template_id"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = MessageTemplate.objects.get(
                template_id=template_id,
                tenant_id=tenant_id
            )
            serializer = MessageTemplateSerializer(template)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except MessageTemplate.DoesNotExist:
            return Response({
                'error': f'Template with ID {template_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, template_id, *args, **kwargs):
        """Update template partially"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = MessageTemplate.objects.get(
                template_id=template_id,
                tenant_id=tenant_id
            )

            serializer = MessageTemplateSerializer(template, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except MessageTemplate.DoesNotExist:
            return Response({
                'error': f'Template with ID {template_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, template_id, *args, **kwargs):
        """Delete template"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = MessageTemplate.objects.get(
                template_id=template_id,
                tenant_id=tenant_id
            )
            template.delete()
            return Response({
                'message': 'Template deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except MessageTemplate.DoesNotExist:
            return Response({
                'error': f'Template with ID {template_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CampaignListCreateView(APIView):
    """
    API endpoint for Campaign LIST and CREATE operations
    GET /api/campaigns/ - List all campaigns for tenant
    POST /api/campaigns/ - Create new campaign
    """

    def get(self, request, *args, **kwargs):
        """List all campaigns for tenant"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            campaigns = Campaign.objects.filter(tenant_id=tenant_id)
            serializer = CampaignSerializer(campaigns, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """Create new campaign"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get tenant object
            tenant = get_object_or_404(Tenant, id=tenant_id)

            # Add tenant to request data
            data = request.data.copy()
            data['tenant'] = tenant.id

            serializer = CampaignSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CampaignDetailView(APIView):
    """
    API endpoint to retrieve, update, or delete campaign by campaign_id
    GET /api/campaigns/{campaign_id}/
    PATCH /api/campaigns/{campaign_id}/
    DELETE /api/campaigns/{campaign_id}/
    """

    def get(self, request, campaign_id, *args, **kwargs):
        """Retrieve campaign details by campaign_id"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            campaign = Campaign.objects.get(
                campaign_id=campaign_id,
                tenant_id=tenant_id
            )
            serializer = CampaignSerializer(campaign)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Campaign.DoesNotExist:
            return Response({
                'error': f'Campaign with ID {campaign_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, campaign_id, *args, **kwargs):
        """Update campaign status and other fields"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            campaign = Campaign.objects.get(
                campaign_id=campaign_id,
                tenant_id=tenant_id
            )

            serializer = CampaignSerializer(campaign, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Campaign.DoesNotExist:
            return Response({
                'error': f'Campaign with ID {campaign_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, campaign_id, *args, **kwargs):
        """Delete campaign"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            campaign = Campaign.objects.get(
                campaign_id=campaign_id,
                tenant_id=tenant_id
            )
            campaign.delete()
            return Response({
                'message': 'Campaign deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except Campaign.DoesNotExist:
            return Response({
                'error': f'Campaign with ID {campaign_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupListCreateView(APIView):
    """
    API endpoint for BroadcastGroup LIST and CREATE operations
    GET /api/broadcast-groups/ - List all broadcast groups for tenant
    POST /api/broadcast-groups/ - Create new broadcast group
    """

    def get(self, request, *args, **kwargs):
        """List all broadcast groups for tenant"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            groups = BroadcastGroup.objects.filter(tenant_id=tenant_id)
            serializer = BroadcastGroupSerializer(groups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request, *args, **kwargs):
        """Create new broadcast group"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Get tenant object
            tenant = get_object_or_404(Tenant, id=tenant_id)

            # Add tenant to request data
            data = request.data.copy()
            data['tenant'] = tenant.id

            serializer = BroadcastGroupSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class BroadcastGroupDetailView(APIView):
    """
    API endpoint to retrieve, update, or delete broadcast group by group_id
    GET /api/broadcast-groups/{group_id}/
    PATCH /api/broadcast-groups/{group_id}/
    DELETE /api/broadcast-groups/{group_id}/
    """

    def get(self, request, group_id, *args, **kwargs):
        """Retrieve broadcast group details by group_id"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = BroadcastGroup.objects.get(
                id=group_id,
                tenant_id=tenant_id
            )
            serializer = BroadcastGroupSerializer(group)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except BroadcastGroup.DoesNotExist:
            return Response({
                'error': f'Broadcast group with ID {group_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request, group_id, *args, **kwargs):
        """Update broadcast group"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = BroadcastGroup.objects.get(
                id=group_id,
                tenant_id=tenant_id
            )

            serializer = BroadcastGroupSerializer(group, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except BroadcastGroup.DoesNotExist:
            return Response({
                'error': f'Broadcast group with ID {group_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, group_id, *args, **kwargs):
        """Delete broadcast group"""
        tenant_id = request.headers.get('X-Tenant-Id')

        if not tenant_id:
            return Response({
                'error': 'X-Tenant-Id header is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = BroadcastGroup.objects.get(
                id=group_id,
                tenant_id=tenant_id
            )
            group.delete()
            return Response({
                'message': 'Broadcast group deleted successfully'
            }, status=status.HTTP_204_NO_CONTENT)
        except BroadcastGroup.DoesNotExist:
            return Response({
                'error': f'Broadcast group with ID {group_id} not found for tenant {tenant_id}'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': f'An error occurred: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)