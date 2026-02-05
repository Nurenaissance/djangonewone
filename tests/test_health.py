"""
Tests for Health Check endpoint.
"""
import pytest
from unittest.mock import patch, MagicMock


pytestmark = pytest.mark.django_db


class TestHealthCheckEndpoint:
    """Tests for /health/ endpoint."""

    def test_health_check_returns_response(self, django_client):
        """Test health check returns a valid response."""
        response = django_client.get('/health/')
        # Should return 200 or 503 depending on component health
        assert response.status_code in [200, 503]
        data = response.json()
        assert 'status' in data
        assert 'components' in data
        assert 'timestamp' in data

    def test_health_check_includes_database_status(self, django_client):
        """Test health check includes database connectivity status."""
        response = django_client.get('/health/')
        data = response.json()
        assert 'database' in data['components']
        assert 'status' in data['components']['database']

    def test_health_check_includes_redis_status(self, django_client):
        """Test health check includes Redis connectivity status."""
        response = django_client.get('/health/')
        data = response.json()
        assert 'redis' in data['components']
        assert 'status' in data['components']['redis']

    def test_health_check_includes_celery_status(self, django_client):
        """Test health check includes Celery worker status."""
        response = django_client.get('/health/')
        data = response.json()
        assert 'celery' in data['components']
        assert 'status' in data['components']['celery']

    def test_health_check_includes_disk_status(self, django_client):
        """Test health check includes disk space status."""
        response = django_client.get('/health/')
        data = response.json()
        assert 'disk' in data['components']
        assert 'status' in data['components']['disk']

    def test_health_check_includes_timestamp(self, django_client):
        """Test health check response includes ISO timestamp."""
        response = django_client.get('/health/')
        data = response.json()
        assert 'timestamp' in data
        # Should be ISO format
        assert 'T' in data['timestamp'] or '-' in data['timestamp']

    def test_health_check_includes_pending_queue_status(self, django_client):
        """Test health check includes pending task queue status."""
        response = django_client.get('/health/')
        data = response.json()
        assert 'pending_queue' in data['components']
        assert 'status' in data['components']['pending_queue']


class TestHealthCheckPerformance:
    """Performance-related health check tests."""

    @pytest.mark.slow
    def test_health_check_responds_within_timeout(self, django_client):
        """Test health check responds within acceptable time."""
        import time

        start = time.time()
        response = django_client.get('/health/')
        elapsed = time.time() - start

        assert response.status_code in [200, 503]
        # Should respond within 30 seconds (generous for CI)
        assert elapsed < 30.0
