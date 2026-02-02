#!/bin/bash

# Azure App Service startup script for Django
# This runs automatically on every deployment

echo "Starting Django application..."

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files (if needed)
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Startup complete!"

# Start Gunicorn
exec gunicorn --bind=0.0.0.0:8000 --timeout 600 simplecrm.wsgi
