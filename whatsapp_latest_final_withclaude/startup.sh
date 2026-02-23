#!/bin/bash
APP_DIR=/home/site/wwwroot
cd "$APP_DIR"

# Ensure Python can find the app modules
export PYTHONPATH="${APP_DIR}:${PYTHONPATH}"

# Activate virtual environment if it exists
if [ -d "$APP_DIR/antenv" ]; then
  source "$APP_DIR/antenv/bin/activate"
fi

# Debug: confirm simplecrm is findable
ls -d "$APP_DIR/simplecrm" 2>/dev/null && echo "simplecrm directory found" || echo "ERROR: simplecrm directory NOT found in $APP_DIR"

# Start Celery worker in background (only if USE_CELERY=true)
if [ "${USE_CELERY,,}" = "true" ]; then
  celery -A simplecrm worker \
    --loglevel=info \
    --concurrency=2 \
    --queues=process_conv_queue,last_seen_updates,message_status_queue,upload_file_queue \
    --max-tasks-per-child=500 \
    &
  echo "Celery worker started in background"
fi

# Start gunicorn in foreground
gunicorn --bind=0.0.0.0:8000 \
  --chdir="$APP_DIR" \
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
