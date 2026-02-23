
from django.apps import apps
from django.http import JsonResponse
from rest_framework.decorators import api_view
from .utils import deduplicate_model
from django.db import connection
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.db import connection, OperationalError

def health_check(request):
    """
    Comprehensive health check endpoint.
    Returns status of all critical components:
    - Database connection
    - Redis connection
    - Celery workers
    - Pending tasks queue
    - Disk space
    """
    import shutil
    from django.conf import settings

    health_status = {
        'status': 'healthy',
        'components': {},
        'timestamp': None
    }

    from django.utils import timezone
    health_status['timestamp'] = timezone.now().isoformat()

    overall_healthy = True

    # 1. Check Database
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['components']['database'] = {'status': 'healthy', 'message': 'Connected'}
    except Exception as e:
        health_status['components']['database'] = {'status': 'unhealthy', 'message': str(e)}
        overall_healthy = False

    # 2. Check Redis
    try:
        import redis
        r = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=3)
        r.ping()
        health_status['components']['redis'] = {'status': 'healthy', 'message': 'Connected'}
    except Exception as e:
        health_status['components']['redis'] = {'status': 'unhealthy', 'message': str(e)}
        # Redis being down is not critical - we have fallback

    # 3. Check Celery (via Redis)
    try:
        from simplecrm.celery import app as celery_app
        inspect = celery_app.control.inspect(timeout=2)
        active_workers = inspect.active()
        if active_workers:
            worker_count = len(active_workers)
            health_status['components']['celery'] = {
                'status': 'healthy',
                'message': f'{worker_count} worker(s) active',
                'workers': list(active_workers.keys())
            }
        else:
            health_status['components']['celery'] = {
                'status': 'degraded',
                'message': 'No active workers (using sync fallback)'
            }
    except Exception as e:
        health_status['components']['celery'] = {
            'status': 'degraded',
            'message': f'Cannot connect: {str(e)} (using sync fallback)'
        }

    # 4. Check Pending Tasks Queue
    try:
        from interaction.pending_tasks import get_pending_task_stats
        pending_stats = get_pending_task_stats()
        pending_count = pending_stats.get('pending', 0)
        failed_count = pending_stats.get('failed', 0)

        if failed_count > 100:
            health_status['components']['pending_queue'] = {
                'status': 'warning',
                'message': f'{failed_count} failed tasks need attention',
                'stats': pending_stats
            }
        else:
            health_status['components']['pending_queue'] = {
                'status': 'healthy',
                'message': f'{pending_count} pending, {failed_count} failed',
                'stats': pending_stats
            }
    except Exception as e:
        health_status['components']['pending_queue'] = {
            'status': 'unknown',
            'message': f'Cannot check: {str(e)}'
        }

    # 5. Check Disk Space
    try:
        total, used, free = shutil.disk_usage("/")
        free_gb = free // (2**30)
        total_gb = total // (2**30)
        used_percent = (used / total) * 100

        if used_percent > 90:
            health_status['components']['disk'] = {
                'status': 'critical',
                'message': f'{free_gb}GB free of {total_gb}GB ({used_percent:.1f}% used)'
            }
            overall_healthy = False
        elif used_percent > 80:
            health_status['components']['disk'] = {
                'status': 'warning',
                'message': f'{free_gb}GB free of {total_gb}GB ({used_percent:.1f}% used)'
            }
        else:
            health_status['components']['disk'] = {
                'status': 'healthy',
                'message': f'{free_gb}GB free of {total_gb}GB ({used_percent:.1f}% used)'
            }
    except Exception as e:
        health_status['components']['disk'] = {'status': 'unknown', 'message': str(e)}

    # Set overall status
    health_status['status'] = 'healthy' if overall_healthy else 'unhealthy'

    status_code = 200 if overall_healthy else 503
    return JsonResponse(health_status, status=status_code)


@api_view(['POST'])
def deduplicate_view(request):
    app_name = request.data.get('app-name')
    model_name = request.data.get('model')
    unique_field = request.data.get('field')
    
    if not app_name or not model_name or not unique_field :
        return JsonResponse({'status': 'error', 'message': 'app-name,model and field name are required.'}, status=400)
    
    try:
        model_class = apps.get_model(app_name, model_name)
    except LookupError:
        return JsonResponse({'status': 'error', 'message': f'Model {model_name} not found in App.'}, status=400)

    try:
        deduplicate_model(model_class, unique_field)
        return JsonResponse({'status': 'success', 'message': f'Duplicates removed successfully from {model_name}.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@api_view(['POST'])
def store_selected_emails(request):
    selected_emails = request.data  # Expecting a list of emails

    with connection.cursor() as cursor:
        for email_data in selected_emails:
            email_id = email_data.get('email_id')
            from_address = email_data.get('from')
            subject = email_data.get('subject')
            text = email_data.get('text')

            # Insert email into the selected_emails table
            cursor.execute("""
                INSERT INTO selected_emails (email_id, from_address, subject, text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (email_id) DO NOTHING;
            """, [email_id, from_address, subject, text])

    return Response({"message": "Emails stored successfully"}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def fetch_all_emails(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT email_id, from_address, subject, text FROM selected_emails;")
        emails = cursor.fetchall()

    # Transform fetched data into a list of dictionaries
    email_list = [
        {
            "email_id": email[0],
            "from_address": email[1],
            "subject": email[2],
            "text": email[3],
        }
        for email in emails
    ]
    
    return Response(email_list, status=status.HTTP_200_OK)
