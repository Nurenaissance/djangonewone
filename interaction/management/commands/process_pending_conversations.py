"""
Management command to process pending conversation tasks.

Run this periodically (every 1-5 minutes) via cron or Azure scheduled task:

    python manage.py process_pending_conversations

Options:
    --batch-size: Number of tasks to process (default: 50)
    --cleanup: Also cleanup old completed/failed tasks
    --stats: Just show statistics, don't process
"""

from django.core.management.base import BaseCommand
from interaction.pending_tasks import (
    process_pending_tasks,
    cleanup_old_tasks,
    get_pending_task_stats
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process pending conversation tasks from the database queue'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of tasks to process in one run (default: 50)'
        )
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Skip tasks older than this many hours (default: 24)'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Also cleanup old completed/failed tasks (older than 7 days)'
        )
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=7,
            help='Days to keep completed/failed tasks before cleanup (default: 7)'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Just show statistics, do not process tasks'
        )

    def handle(self, *args, **options):
        # Show stats
        stats = get_pending_task_stats()
        self.stdout.write(f"📊 Pending task statistics: {stats}")

        if options['stats']:
            return

        # Process pending tasks
        batch_size = options['batch_size']
        max_age = options['max_age_hours']

        self.stdout.write(f"🔄 Processing up to {batch_size} pending tasks...")

        results = process_pending_tasks(batch_size=batch_size, max_age_hours=max_age)

        self.stdout.write(self.style.SUCCESS(
            f"✅ Processed: {results['processed']}, "
            f"Failed: {results['failed']}, "
            f"Skipped (expired): {results['skipped']}"
        ))

        # Cleanup if requested
        if options['cleanup']:
            cleanup_days = options['cleanup_days']
            self.stdout.write(f"🧹 Cleaning up tasks older than {cleanup_days} days...")
            deleted = cleanup_old_tasks(days=cleanup_days)
            self.stdout.write(self.style.SUCCESS(f"🧹 Deleted {deleted} old tasks"))

        # Final stats
        final_stats = get_pending_task_stats()
        self.stdout.write(f"📊 Final statistics: {final_stats}")
