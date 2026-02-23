"""
Migration to add unique constraint on phone + tenant for contacts.

This prevents duplicate contacts with the same phone number within a tenant.
The constraint uses a conditional index to allow NULL tenants if needed.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add unique constraint for phone + tenant combination."""

    dependencies = [
        ('contacts', '0009_contact_customfield'),
    ]

    operations = [
        # First, add an index for better query performance
        migrations.AddIndex(
            model_name='contact',
            index=models.Index(
                fields=['phone', 'tenant'],
                name='contact_phone_tenant_idx'
            ),
        ),

        # Add unique constraint for phone + tenant
        # This will prevent duplicate contacts within the same tenant
        migrations.AddConstraint(
            model_name='contact',
            constraint=models.UniqueConstraint(
                fields=['phone', 'tenant'],
                name='unique_contact_phone_per_tenant',
                # Only apply to contacts that have a tenant assigned
                condition=models.Q(tenant__isnull=False),
            ),
        ),
    ]
