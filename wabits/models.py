# models.py

from django.db import models
from tenant.models import Tenant  # adjust import as needed

class WAbits(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    flow_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant} - {self.name}"
