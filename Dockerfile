FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Production WSGI via gunicorn — `manage.py runserver` is single-threaded,
# leaks memory under load, and emits "accessing development server over HTTPS"
# noise on every request from the Nginx reverse proxy. gthread worker class
# multiplexes requests across threads per worker, good balance for Django.
#   workers=4   matches the 4-core Hetzner box (CPU-bound budget)
#   threads=8   per worker (32 concurrent request capacity)
#   timeout=300 long enough for slow mobile uplinks pushing multipart
#               audio (Naad 2.0 interview submissions are 5-15 MB across
#               three webm/opus parts; rural Indian uplinks at 50 KB/s
#               need ~3 min just to land the bytes). Was 120s; raised
#               to 300s as part of the Naad upload stability pass.
#   --access-logfile -  log to stdout so docker logs sees them
#   --limit-request-line 8190  default; large enough for our URLs
CMD ["gunicorn", "simplecrm.wsgi:application", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "4", \
     "--threads", "8", \
     "--worker-class", "gthread", \
     "--timeout", "300", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--forwarded-allow-ips", "*"]
