from django.db import models
from tenant.models import Tenant
from contacts.models import Contact

class WhatsappCampaign(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    bpid = models.CharField(max_length=255, null=True, blank=True)
    access_token = models.CharField(max_length=255, null=True, blank=True)
    account_id = models.CharField(max_length=255, null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
    phone = models.JSONField(null=True, blank=True)
    templates_data = models.JSONField(null=True, blank=True, default=dict)

    def __init__(self, *args, **kwargs):
        super(WhatsappCampaign, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.name


class BroadcastGroup(models.Model):
    """Model to store broadcast groups for organizing contacts"""
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    contacts = models.ManyToManyField(Contact, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'broadcast_group'

    def __str__(self):
        return f"{self.name} ({self.tenant.id})"

    def total_contacts(self):
        """Return the total number of contacts in this group"""
        return self.contacts.count()


class MessageTemplate(models.Model):
    """Model to store WhatsApp message templates"""
    id = models.AutoField(primary_key=True)
    template_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=50)  # MARKETING, UTILITY, etc.
    language = models.CharField(max_length=10)
    status = models.CharField(max_length=50)
    components = models.JSONField(null=True, blank=True, default=list)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'message_template'

    def __str__(self):
        return f"{self.name} ({self.template_id})"


class Campaign(models.Model):
    """Model to store campaign execution data"""
    id = models.AutoField(primary_key=True)
    campaign_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default='active')  # active, completed, paused
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    broadcast_group = models.ForeignKey(BroadcastGroup, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'campaign'

    def __str__(self):
        return f"{self.name} ({self.campaign_id})"