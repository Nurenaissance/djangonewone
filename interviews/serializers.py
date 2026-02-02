from rest_framework import serializers
from .models import InterviewResponse


class InterviewResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for Interview Response model
    """
    class Meta:
        model = InterviewResponse
        fields = [
            'id',
            'phone_no',
            'tenant',
            'flow_name',
            'timestamp',
            'candidate_name',
            'name',
            'address',
            'calibration',
            'status',
            'question1',
            'question2',
            'question3',
            'question4',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'timestamp', 'created_at', 'updated_at']


class InterviewResponseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Interview Response
    """
    class Meta:
        model = InterviewResponse
        fields = [
            'phone_no',
            'tenant',
            'flow_name',
            'candidate_name',
            'name',
            'address',
            'calibration',
            'status',
            'question1',
            'question2',
            'question3',
            'question4'
        ]

    def validate_phone_no(self, value):
        """Validate phone number format"""
        if not value:
            raise serializers.ValidationError("Phone number is required")
        return value
