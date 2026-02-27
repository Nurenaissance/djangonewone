import string
import uuid
import random

from django.conf import settings
from django.db import models
from django.utils import timezone


class Tenant(models.Model):
    TIER_CHOICES = [
        ('free', 'Free'),
        ('basic', 'Basic'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    id = models.CharField(primary_key=True, max_length=50)
    organization=models.CharField(max_length=100)
    db_user = models.CharField(max_length=100)
    db_user_password = models.CharField(max_length=100)
    spreadsheet_link = models.URLField(null=True, blank=True)
    catalog_id = models.BigIntegerField(null=True, blank=True)
    key = models.BinaryField(null=True, blank=True)
    tier = models.CharField(
        max_length=20, 
        choices=TIER_CHOICES, 
        default='free'
    )
    agents = models.JSONField(null=True, blank=True)

    def __str__(self):
        return self.id

class Plan(models.Model):
    BILLING_INTERVAL_CHOICES = [
        ("monthly", "Monthly"),
        ("annual", "Annual"),
        ("custom", "Custom"),
    ]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    billing_interval = models.CharField(
        max_length=20, choices=BILLING_INTERVAL_CHOICES, default="monthly"
    )
    price_cents = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=10, default="USD")
    features = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.slug})"


class PlanQuota(models.Model):
    ENFORCEMENT_CHOICES = [
        ("soft", "Soft"),
        ("strict", "Strict"),
    ]

    plan = models.ForeignKey(
        Plan, on_delete=models.CASCADE, related_name="quotas"
    )
    quota_key = models.CharField(max_length=60)
    value = models.BigIntegerField(null=True, blank=True)
    unit = models.CharField(max_length=30, default="count")
    enforcement = models.CharField(
        max_length=20, choices=ENFORCEMENT_CHOICES, default="soft"
    )
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("plan", "quota_key")

    def __str__(self):
        return f"{self.plan.name} · {self.quota_key}"


class TenantPlan(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("trialing", "Trialing"),
        ("past_due", "Past Due"),
        ("canceled", "Canceled"),
    ]

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="tenant_plan"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="active"
    )
    stripe_subscription_id = models.CharField(max_length=200, blank=True, null=True)
    trial_ends_at = models.DateTimeField(blank=True, null=True)
    next_billing_at = models.DateTimeField(blank=True, null=True)
    effective_features = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def applied_features(self):
        combined = dict(self.plan.features)
        combined.update(self.effective_features or {})
        return combined

    def __str__(self):
        return f"{self.tenant.id} → {self.plan.name}"


class TenantQuotaUsage(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="quota_usage"
    )
    quota_key = models.CharField(max_length=60)
    period_start = models.DateTimeField(default=timezone.now)
    period_end = models.DateTimeField(null=True, blank=True)
    used = models.BigIntegerField(default=0)
    threshold_flag = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("tenant", "quota_key", "period_start")

    def __str__(self):
        return f"{self.tenant.id} · {self.quota_key} ({self.used})"


class QuotaOverride(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="quota_overrides"
    )
    quota_key = models.CharField(max_length=60)
    value = models.BigIntegerField()
    expires_at = models.DateTimeField(null=True, blank=True)
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("tenant", "quota_key")

    def __str__(self):
        return f"{self.tenant.id} override {self.quota_key}"


class BillingEvent(models.Model):
    EVENT_TYPES = [
        ("upgrade", "Upgrade"),
        ("downgrade", "Downgrade"),
        ("overage", "Overage"),
        ("payment", "Payment"),
        ("invoice", "Invoice"),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="billing_events"
    )
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant.id} [{self.event_type}]"


class InviteCode(models.Model):
    ROLE_CHOICES = [
        ("admin", "Admin"),
        ("employee", "Employee"),
        ("manager", "Manager"),
    ]

    code = models.CharField(max_length=8, unique=True)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="invite_codes"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(default=50)
    use_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="employee")

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        if self.max_uses and self.use_count >= self.max_uses:
            return False
        return True

    @staticmethod
    def generate_code(length=8):
        chars = string.ascii_uppercase + string.digits
        while True:
            code = "".join(random.choices(chars, k=length))
            if not InviteCode.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f"{self.code} ({self.tenant.organization})"


class WA(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    access_token = models.CharField(max_length= 100)
    business_phone_number_id = models.DecimalField(max_digits=40, decimal_places=0)
