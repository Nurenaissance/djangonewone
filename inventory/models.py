from django.db import models
from tenant.models import Tenant

class ProductInventory(models.Model):
    product_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200)
    description = models.TextField()
    quantity = models.IntegerField(default=0)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True)
