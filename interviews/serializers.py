from rest_framework import serializers
from .models import InterviewResponse


class InterviewResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for Interview Response model
    """
    # User-friendly computed fields for dashboard display
    interview_date = serializers.SerializerMethodField(help_text="Formatted interview date")
    interview_time = serializers.SerializerMethodField(help_text="Formatted interview time")
    has_name_audio = serializers.SerializerMethodField(help_text="Whether name was recorded as audio")
    has_address_audio = serializers.SerializerMethodField(help_text="Whether address was recorded as audio")
    questions_answered = serializers.SerializerMethodField(help_text="Number of interview questions answered")
    display_name = serializers.SerializerMethodField(help_text="Best available name for display")

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
            'name_audio',
            'address',
            'address_audio',
            'calibration',
            'calibration_audio',
            'status',
            'question1',
            'question2',
            'question3',
            'question4',
            'created_at',
            'updated_at',
            # User-friendly fields for dashboard
            'interview_date',
            'interview_time',
            'has_name_audio',
            'has_address_audio',
            'questions_answered',
            'display_name',
        ]
        read_only_fields = ['id', 'timestamp', 'created_at', 'updated_at']

    def get_interview_date(self, obj):
        """Return formatted date like 'Jan 21, 2026'"""
        if obj.timestamp:
            return obj.timestamp.strftime('%b %d, %Y')
        return None

    def get_interview_time(self, obj):
        """Return formatted time like '2:30 PM'"""
        if obj.timestamp:
            return obj.timestamp.strftime('%I:%M %p')
        return None

    def get_has_name_audio(self, obj):
        """Check if name was given as audio"""
        return bool(obj.name_audio)

    def get_has_address_audio(self, obj):
        """Check if address was given as audio"""
        return bool(obj.address_audio)

    def get_questions_answered(self, obj):
        """Count how many of the 4 interview questions were answered"""
        count = 0
        if obj.question1: count += 1
        if obj.question2: count += 1
        if obj.question3: count += 1
        if obj.question4: count += 1
        return count

    def get_display_name(self, obj):
        """Return the best available name for display"""
        if obj.candidate_name:
            return obj.candidate_name
        if obj.name:
            return obj.name
        if obj.name_audio:
            return f"[Audio - {obj.phone_no}]"
        return obj.phone_no


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
            'name_audio',
            'address',
            'address_audio',
            'calibration',
            'calibration_audio',
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
