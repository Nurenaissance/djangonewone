from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from tenant.models import Tenant 
from django.utils import timezone
from contacts.models import Contact
from simplecrm.models import CustomUser

# we are using it, it stores all the conversation happening to our bot
class Conversation(models.Model):
    contact_id = models.CharField(max_length=255, db_index=True)  # Added index
    message_text = models.TextField(null=True, blank=True)
    encrypted_message_text = models.BinaryField(null=True, blank=True)

    # Media support fields
    message_type = models.CharField(max_length=20, null=True, blank=True, help_text="text, image, video, audio, document")
    media_url = models.URLField(max_length=500, null=True, blank=True, help_text="Azure Blob Storage URL")
    media_caption = models.TextField(null=True, blank=True, help_text="Caption for image/video")
    media_filename = models.CharField(max_length=255, null=True, blank=True, help_text="Original filename")
    thumbnail_url = models.URLField(max_length=500, null=True, blank=True, help_text="Thumbnail URL for videos")

    sender = models.CharField(max_length=50)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    source = models.CharField(max_length=255, db_index=True)  # Added index
    date_time = models.DateTimeField(null=True, blank=True, db_index=True)  # Added index
    business_phone_number_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)  # Added index
    mapped = models.BooleanField(default=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, blank=True, null=True, related_name='interaction_conversations')

    class Meta:
        # Composite index for the most common query pattern
        indexes = [
            models.Index(fields=['contact_id', 'business_phone_number_id', 'source'], name='conv_contact_bpid_source_idx'),
            models.Index(fields=['contact_id', 'date_time'], name='conv_contact_datetime_idx'),
            models.Index(fields=['tenant', 'date_time'], name='conv_tenant_datetime_idx'),
        ]

    def __str__(self):
        return f"Conversation ID: {self.id}, Contact ID: {self.contact_id}, Sender: {self.sender}"


# not using
class Group(models.Model):
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(Contact, related_name='groups')
    date_created = models.DateTimeField(auto_now_add=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"Group ID: {self.id}, Name: {self.name}, Members: {self.members.count()}"


class PendingConversationTask(models.Model):
    """
    Database-backed queue for conversation saves when Celery/Redis is unavailable.
    Ensures no message is ever lost - provides guaranteed delivery.

    Workflow:
    1. If Redis/Celery fails, task is queued here
    2. Management command processes pending tasks periodically
    3. On success, task marked completed; on failure, retried up to max_attempts
    """
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]

    # Task data
    payload = models.JSONField(help_text='Serialized conversation payload')
    encryption_key = models.TextField(help_text='Base64 encoded encryption key')

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=5)

    # Error tracking
    last_error = models.TextField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    # Metadata for tracking/debugging
    contact_id = models.CharField(max_length=255, db_index=True, help_text='For tracking/debugging')
    tenant_id = models.CharField(max_length=100, db_index=True)
    message_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['tenant_id', 'status']),
        ]
        verbose_name = 'Pending Conversation Task'
        verbose_name_plural = 'Pending Conversation Tasks'

    def __str__(self):
        return f"PendingTask {self.id} - {self.contact_id} ({self.status})"

    def mark_processing(self):
        """Mark task as being processed"""
        self.status = self.PROCESSING
        self.attempts += 1
        self.save(update_fields=['status', 'attempts', 'updated_at'])

    def mark_completed(self):
        """Mark task as successfully completed"""
        self.status = self.COMPLETED
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at', 'updated_at'])

    def mark_failed(self, error_message):
        """Mark task as failed"""
        self.last_error = str(error_message)[:1000]  # Truncate long errors
        if self.attempts >= self.max_attempts:
            self.status = self.FAILED
        else:
            self.status = self.PENDING  # Will retry
        self.save(update_fields=['status', 'last_error', 'updated_at'])

