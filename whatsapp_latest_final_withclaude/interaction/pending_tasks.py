"""
Pending Tasks - Database-backed fallback queue for when Redis/Celery is unavailable.

This provides a robust fallback mechanism:
1. Primary: Celery + Redis (fast, async)
2. Secondary: Direct sync save (immediate but blocking)
3. Tertiary: Database queue (guaranteed delivery, processed by cron/management command)

Usage:
    from interaction.pending_tasks import queue_pending_task, process_pending_tasks

    # In view - queue task when other methods fail
    task = queue_pending_task(payload, key)

    # In management command - process pending tasks
    # python manage.py process_pending_conversations
"""

import logging
import base64
from django.db.models import F
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def queue_pending_task(payload: dict, key: bytes):
    """
    Queue a conversation save task in the database.
    Called when both Celery and sync save fail.
    """
    from interaction.models import PendingConversationTask

    try:
        task = PendingConversationTask.objects.create(
            payload=payload,
            encryption_key=base64.b64encode(key).decode('utf-8'),
            contact_id=payload.get('contact_id', 'unknown'),
            tenant_id=str(payload.get('tenant', 'unknown')),
            message_count=len(payload.get('conversations', [])),
        )
        logger.info(f"📥 Queued pending task {task.id} for contact {task.contact_id}")
        return task
    except Exception as e:
        logger.error(f"❌ Failed to queue pending task: {e}")
        raise


def process_pending_tasks(batch_size: int = 50, max_age_hours: int = 24) -> dict:
    """
    Process pending conversation tasks from the database queue.
    Should be called by a management command or cron job.

    Args:
        batch_size: Number of tasks to process in one batch
        max_age_hours: Skip tasks older than this (they're probably stale)

    Returns:
        dict with counts: {'processed': N, 'failed': N, 'skipped': N}
    """
    from interaction.models import PendingConversationTask
    from interaction.views import save_conversations_sync_from_pending

    cutoff_time = timezone.now() - timedelta(hours=max_age_hours)

    # Get pending tasks (oldest first, not too old)
    pending_tasks = PendingConversationTask.objects.filter(
        status=PendingConversationTask.PENDING,
        created_at__gte=cutoff_time,
        attempts__lt=F('max_attempts')
    ).order_by('created_at')[:batch_size]

    results = {'processed': 0, 'failed': 0, 'skipped': 0}

    for task in pending_tasks:
        try:
            task.mark_processing()

            # Decode the key
            key = base64.b64decode(task.encryption_key)

            # Process the task
            save_conversations_sync_from_pending(task.payload, key)

            task.mark_completed()
            results['processed'] += 1
            logger.info(f"✅ Processed pending task {task.id}")

        except Exception as e:
            task.mark_failed(str(e))
            results['failed'] += 1
            logger.error(f"❌ Failed to process pending task {task.id}: {e}")

    # Mark very old pending tasks as failed
    old_tasks_count = PendingConversationTask.objects.filter(
        status=PendingConversationTask.PENDING,
        created_at__lt=cutoff_time
    ).update(status=PendingConversationTask.FAILED, last_error='Task expired')
    results['skipped'] = old_tasks_count

    logger.info(f"📊 Pending task processing complete: {results}")
    return results


def get_pending_task_stats() -> dict:
    """Get statistics about pending tasks for monitoring"""
    from interaction.models import PendingConversationTask
    from django.db.models import Count

    stats = PendingConversationTask.objects.values('status').annotate(count=Count('id'))
    return {item['status']: item['count'] for item in stats}


def cleanup_old_tasks(days: int = 7) -> int:
    """Remove completed/failed tasks older than specified days"""
    from interaction.models import PendingConversationTask

    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = PendingConversationTask.objects.filter(
        status__in=[PendingConversationTask.COMPLETED, PendingConversationTask.FAILED],
        updated_at__lt=cutoff
    ).delete()
    logger.info(f"🧹 Cleaned up {deleted} old pending tasks")
    return deleted
