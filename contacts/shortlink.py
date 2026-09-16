"""
Minimal in-house short-link redirector.

GET /s/<slug>  -> 302 to the mapped destination URL (query string preserved).

Links live in the `short_links` table so a destination can be changed without
touching the bot/workflow. Self-contained and public by design (a short link
must be openable by anyone), so it is added to EXCLUDED_PATHS.
"""
import logging
from django.db import connection
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
def follow(request, slug):
    with connection.cursor() as c:
        c.execute("SELECT url FROM short_links WHERE slug=%s AND active=true", [slug])
        row = c.fetchone()
    if not row:
        return JsonResponse({"error": "unknown link"}, status=404)
    url = row[0]
    # keep any extra query params the caller appended
    extra = request.META.get("QUERY_STRING", "")
    if extra:
        url = url + ("&" if "?" in url else "?") + extra
    try:
        with connection.cursor() as c:
            c.execute("UPDATE short_links SET hits = COALESCE(hits,0) + 1 WHERE slug=%s", [slug])
    except Exception as e:  # counting must never break the redirect
        logger.warning("shortlink hit-count failed for %s: %s", slug, e)
    return HttpResponseRedirect(url)
