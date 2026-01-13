import os
from celery import Celery
from celery.signals import (
    task_postrun, task_prerun, task_failure,
    worker_process_init, worker_process_shutdown
)

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplecrm.settings')

# Create Celery app
app = Celery('simplecrm')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover tasks from all registered Django apps
app.autodiscover_tasks()

# =============================================================================
# CRITICAL: Connection cleanup signals to prevent "remaining connection slots"
# =============================================================================

@task_prerun.connect
def close_stale_connections_before_task(**kwargs):
    """Close any stale database connections before task starts."""
    from django import db
    db.close_old_connections()


@task_postrun.connect
def close_db_connections_after_task(**kwargs):
    """Close ALL database connections after each task completes."""
    from django import db
    db.connections.close_all()


@task_failure.connect
def close_db_connections_on_failure(**kwargs):
    """Close ALL database connections if task fails."""
    from django import db
    db.connections.close_all()


@worker_process_init.connect
def close_db_connections_on_worker_init(**kwargs):
    """Close any inherited DB connections when a worker process starts."""
    from django import db
    db.connections.close_all()


@worker_process_shutdown.connect
def close_db_connections_on_worker_shutdown(**kwargs):
    """Close ALL database connections when worker shuts down."""
    from django import db
    db.connections.close_all()

# Add shared_task decorator
def shared_task(*args, **kwargs):
    return app.task(*args, **kwargs)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')