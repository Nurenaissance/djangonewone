from django.urls import path
from .views import (
    InterviewResponseListView,
    InterviewResponseCreateView,
    InterviewResponseDetailView,
    save_interview_from_flow,
    interview_stats,
    import_from_direct_chat,
    public_interview_submit,
    public_employee_audio_upload,
    file_upload_view,
    dashboard_tabs,
)

urlpatterns = [
    # List all interview responses
    path('responses/', InterviewResponseListView.as_view(), name='interview-response-list'),

    # Create new interview response
    path('responses/create/', InterviewResponseCreateView.as_view(), name='interview-response-create'),

    # Get/Update/Delete specific interview response
    path('responses/<int:pk>/', InterviewResponseDetailView.as_view(), name='interview-response-detail'),

    # Save from WhatsApp flow (webhook)
    path('save-from-flow/', save_interview_from_flow, name='save-interview-from-flow'),

    # Get statistics
    path('stats/', interview_stats, name='interview-stats'),

    # Import from Direct Chat
    path('import-from-chat/', import_from_direct_chat, name='import-from-direct-chat'),

    # Dashboard tabs (tab config with counts)
    path('dashboard/tabs/', dashboard_tabs, name='dashboard-tabs'),

    # ========== PUBLIC ENDPOINTS (No authentication required) ==========
    # Public interview submission page
    path('public/submit/', public_interview_submit, name='public-interview-submit'),
    # Per-part employee audio upload (replaces frontend-direct-to-Azure SAS)
    path('public/employee-upload/', public_employee_audio_upload, name='public-employee-audio-upload'),

    # Generic authenticated file upload (replaces frontend-direct-to-Azure SAS
    # in src/azureUpload.jsx — flow-builder uploads, etc).
    path('files/upload/', file_upload_view, name='file-upload'),
]
