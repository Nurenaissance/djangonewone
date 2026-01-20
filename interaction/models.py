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

