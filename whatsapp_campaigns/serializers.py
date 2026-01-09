from rest_framework import serializers
from .models import MessageTemplate, Campaign, BroadcastGroup


class MessageTemplateSerializer(serializers.ModelSerializer):
    """Serializer for MessageTemplate model"""

    class Meta:
        model = MessageTemplate
        fields = ['id', 'template_id', 'name', 'category', 'language', 'status', 'components', 'tenant', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class BroadcastGroupSerializer(serializers.ModelSerializer):
    """Serializer for BroadcastGroup model"""
    total_contacts = serializers.SerializerMethodField()

    class Meta:
        model = BroadcastGroup
        fields = ['id', 'name', 'tenant', 'total_contacts', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_contacts(self, obj):
        return obj.total_contacts()


class CampaignSerializer(serializers.ModelSerializer):
    """Serializer for Campaign model"""
    broadcast_group_id = serializers.IntegerField(source='broadcast_group.id', read_only=True, allow_null=True)

    class Meta:
        model = Campaign
        fields = ['id', 'campaign_id', 'name', 'status', 'started_at', 'completed_at', 'tenant', 'broadcast_group_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
