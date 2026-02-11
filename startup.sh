#!/bin/bash
cd /home/site/wwwroot

# Start Celery worker in background for async task processing
celery -A simplecrm worker \
  --loglevel=info \
  --concurrency=2 \
  --queues=process_conv_queue,last_seen_updates,message_status_queue,upload_file_queue \
  --max-tasks-per-child=500 \
  &

# Start gunicorn in foreground
gunicorn --bind=0.0.0.0:8000 \
  --workers=${WEB_CONCURRENCY:-4} \
  --threads=4 \
  --worker-class=gthread \
  --timeout=120 \
  --graceful-timeout=30 \
  --keep-alive=65 \
  --max-requests=1000 \
  --max-requests-jitter=50 \
  --log-level=info \
  simplecrm.wsgi
