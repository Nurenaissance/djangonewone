from django.db import models
from tenant.models import Tenant


class InterviewResponse(models.Model):
    """
    Model to store interview responses from both Vidushi and Maan Vidushi interviews
    Supports multiple entries per phone number with timestamps
    Stores audio files in Azure Blob Storage with structured paths
    """

    # Interview type choices
    INTERVIEW_TYPE_CHOICES = [
        ('vidushi', 'Vidushi'),
        ('maan_vidushi', 'Maan Vidushi'),
    ]

    # Status choices
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('reviewed', 'Reviewed'),
    ]

    # Primary identification
    phone_no = models.CharField(max_length=20, db_index=True, help_text='Candidate phone number')
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='interview_responses', null=True, blank=True)
    flow_name = models.CharField(max_length=100, default='naad_2.0_interview', db_index=True)

    # Interview type (NEW)
    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPE_CHOICES,
        default='vidushi',
        db_index=True,
        help_text='Type of interview: Vidushi or Maan Vidushi'
    )

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Personal information
    candidate_name = models.CharField(max_length=200, blank=True, null=True, help_text='Full name of the candidate')
    name = models.CharField(max_length=200, blank=True, null=True)
    name_audio = models.TextField(blank=True, null=True, help_text='Audio URL for name')
    address = models.TextField(blank=True, null=True)
    address_audio = models.TextField(blank=True, null=True, help_text='Audio URL for address')

    # Calibration and status
    calibration = models.TextField(blank=True, null=True)
    calibration_audio = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Azure Blob Storage URL for Q0 calibration audio (Parts A, B, C combined)'
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Audio file URLs for grouped questions (NEW STRUCTURE)
    # For Vidushi: part1 = Q1-Q3, part2 = Q4-Q6
    # For Maan Vidushi: part1 = Q1-Q4, part2 = Q5-Q8
    part1_audio = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Azure Blob Storage URL for Part 1 audio (Q1-Q3 for Vidushi, Q1-Q4 for Maan Vidushi)'
    )
    part2_audio = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text='Azure Blob Storage URL for Part 2 audio (Q4-Q6 for Vidushi, Q5-Q8 for Maan Vidushi)'
    )

    # Legacy fields (keep for backward compatibility with existing data)
    question1 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')
    question2 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')
    question3 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')
    question4 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')

    # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Submission metadata
    submission_ip = models.GenericIPAddressField(blank=True, null=True, help_text='IP address of submission')
    user_agent = models.TextField(blank=True, null=True, help_text='Browser user agent string')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Interview Response'
        verbose_name_plural = 'Interview Responses'
        indexes = [
            models.Index(fields=['tenant', 'flow_name', '-timestamp']),
            models.Index(fields=['phone_no', '-timestamp']),
            models.Index(fields=['interview_type', 'status', '-timestamp']),
            models.Index(fields=['candidate_name', '-timestamp']),
        ]

    def __str__(self):
        interview_label = self.get_interview_type_display()
        return f"{self.candidate_name} - {interview_label} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def get_audio_count(self):
        """Returns the number of audio files uploaded"""
        count = 0
        if self.calibration_audio:
            count += 1
        if self.part1_audio:
            count += 1
        if self.part2_audio:
            count += 1
        return count

    def is_complete(self):
        """Checks if all required audio files are uploaded"""
        return bool(
            self.candidate_name and
            self.phone_no and
            self.calibration_audio and
            self.part1_audio and
            self.part2_audio
        )
