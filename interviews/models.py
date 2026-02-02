from django.db import models
from tenant.models import Tenant


class InterviewResponse(models.Model):
    """
    Model to store interview responses from the interviewdrishtee flow
    Supports multiple entries per phone number with timestamps
    """
    # Primary identification
    phone_no = models.CharField(max_length=20, db_index=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='interview_responses')
    flow_name = models.CharField(max_length=100, default='interviewdrishtee', db_index=True)

    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    # Personal information
    candidate_name = models.CharField(max_length=200, blank=True, null=True)
    name = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    # Calibration and status
    calibration = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, default='pending', db_index=True)

    # Audio file URLs or Media IDs for questions
    question1 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')
    question2 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')
    question3 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')
    question4 = models.TextField(blank=True, null=True, help_text='Audio file URL or media ID')

    # Additional metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Interview Response'
        verbose_name_plural = 'Interview Responses'
        indexes = [
            models.Index(fields=['tenant', 'flow_name', '-timestamp']),
            models.Index(fields=['phone_no', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.candidate_name or self.phone_no} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
