from django.contrib import admin
from .models import InterviewResponse


@admin.register(InterviewResponse)
class InterviewResponseAdmin(admin.ModelAdmin):
    list_display = ['phone_no', 'candidate_name', 'tenant', 'flow_name', 'status', 'timestamp']
    list_filter = ['tenant', 'flow_name', 'status', 'timestamp']
    search_fields = ['phone_no', 'candidate_name', 'name', 'address']
    readonly_fields = ['timestamp', 'created_at', 'updated_at']
    ordering = ['-timestamp']

    fieldsets = (
        ('Basic Information', {
            'fields': ('phone_no', 'tenant', 'flow_name', 'timestamp')
        }),
        ('Personal Details', {
            'fields': ('candidate_name', 'name', 'address')
        }),
        ('Interview Data', {
            'fields': ('calibration', 'status', 'question1', 'question2', 'question3', 'question4')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
