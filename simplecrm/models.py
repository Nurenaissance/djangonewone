from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import AbstractUser
from tenant.models import Tenant 

class CustomUser(AbstractUser):
    # Define choices for user roles
    ADMIN = 'admin'
    EMPLOYEE = 'employee'
    MANAGER = 'manager'
    ROLE_CHOICES = [
        (ADMIN, 'Admin'),
        (EMPLOYEE, 'Employee'),
        (MANAGER, 'Manager'),
    ]

    # Existing fields
    organization = models.CharField(max_length=100)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=EMPLOYEE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    # Additional fields
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    job_profile = models.CharField(max_length=255, blank=True, null=True)
    must_change_password = models.BooleanField(default=False)
    password_changed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username


class PasswordResetToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="password_reset_tokens")
    token_hash = models.CharField(max_length=64, unique=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"PasswordResetToken(user={self.user_id}, used={bool(self.used_at)})"
    
