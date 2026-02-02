from django.db import models
from django.conf import settings
from django.utils import timezone
import string
import random


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

class InviteCode(models.Model):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('manager', 'Manager'),
    ]

    code = models.CharField(max_length=8, unique=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='invite_codes')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    max_uses = models.IntegerField(default=50)
    use_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

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
            code = ''.join(random.choices(chars, k=length))
            if not InviteCode.objects.filter(code=code).exists():
                return code

    def __str__(self):
        return f"{self.code} ({self.tenant.organization})"


class WA(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    access_token = models.CharField(max_length= 100)
    business_phone_number_id = models.DecimalField(max_digits=40, decimal_places=0)
