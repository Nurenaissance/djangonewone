#!/usr/bin/env python3
"""
Pre-deployment validation script for WhatsApp Business Automation Platform.

This script runs comprehensive checks before deployment:
1. Django tests (pytest)
2. Database migrations status
3. Health endpoint verification
4. Configuration validation
5. Security checks

Run before any deployment:
    python scripts/pre_deploy_check.py

Exit codes:
    0 - All checks passed
    1 - One or more checks failed
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Try to import Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'simplecrm.settings')


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")


def print_result(name: str, passed: bool, message: str = "") -> None:
    """Print a formatted test result."""
    status = f"{Colors.GREEN}PASS{Colors.END}" if passed else f"{Colors.RED}FAIL{Colors.END}"
    print(f"  [{status}] {name}")
    if message and not passed:
        print(f"         {Colors.YELLOW}{message}{Colors.END}")


def check_django_tests() -> tuple[bool, str]:
    """
    Run Django test suite using pytest.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        result = subprocess.run(
            ['python', '-m', 'pytest', 'tests/', '-v', '--tb=short', '-q'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            return True, "All tests passed"
        else:
            # Extract failure summary
            output = result.stdout + result.stderr
            lines = output.split('\n')
            failures = [l for l in lines if 'FAILED' in l or 'ERROR' in l]
            failure_msg = '\n'.join(failures[:5])  # First 5 failures
            return False, failure_msg or "Tests failed"

    except subprocess.TimeoutExpired:
        return False, "Tests timed out after 5 minutes"
    except FileNotFoundError:
        return False, "pytest not found. Install with: pip install pytest pytest-django"
    except Exception as e:
        return False, str(e)


def check_migrations() -> tuple[bool, str]:
    """
    Check for unapplied database migrations.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        result = subprocess.run(
            ['python', 'manage.py', 'showmigrations', '--plan'],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=60
        )

        # Check for unapplied migrations (marked with [ ])
        if '[ ]' in result.stdout:
            unapplied = [line for line in result.stdout.split('\n') if '[ ]' in line]
            return False, f"Unapplied migrations: {len(unapplied)}"

        return True, "All migrations applied"

    except subprocess.TimeoutExpired:
        return False, "Migration check timed out"
    except Exception as e:
        return False, str(e)


def check_health_endpoint(url: str = "http://localhost:8000/health/") -> tuple[bool, str]:
    """
    Verify health endpoint responds correctly.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        import urllib.request
        import urllib.error

        req = urllib.request.Request(url, method='GET')
        req.add_header('Accept', 'application/json')

        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())

            if response.status == 200 and data.get('status') == 'healthy':
                return True, "Health endpoint OK"
            else:
                unhealthy = [k for k, v in data.get('components', {}).items()
                           if v.get('status') == 'unhealthy']
                return False, f"Unhealthy components: {', '.join(unhealthy)}"

    except urllib.error.URLError:
        return False, f"Cannot connect to {url} - is the server running?"
    except Exception as e:
        return False, str(e)


def check_settings_security() -> tuple[bool, str]:
    """
    Check Django settings for security issues.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    issues = []

    try:
        import django
        django.setup()
        from django.conf import settings

        # Check DEBUG mode
        if settings.DEBUG:
            issues.append("DEBUG=True (should be False in production)")

        # Check SECRET_KEY
        if 'changeme' in settings.SECRET_KEY.lower() or len(settings.SECRET_KEY) < 32:
            issues.append("SECRET_KEY appears insecure")

        # Check ALLOWED_HOSTS
        if '*' in settings.ALLOWED_HOSTS:
            issues.append("ALLOWED_HOSTS contains '*' (wildcard)")

        # Check database SSL
        db_settings = settings.DATABASES.get('default', {})
        db_options = db_settings.get('OPTIONS', {})
        if db_settings.get('HOST') and 'azure' in db_settings.get('HOST', '').lower():
            if db_options.get('sslmode') != 'require':
                issues.append("Database SSL not enforced for Azure")

        if issues:
            return False, "; ".join(issues)
        return True, "Security settings OK"

    except Exception as e:
        return False, f"Could not check settings: {e}"


def check_required_env_vars() -> tuple[bool, str]:
    """
    Check that required environment variables are set.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    required_vars = [
        'AZURE_REDIS_PASSWORD',
        'AZURE_STORAGE_CONNECTION_STRING',
    ]

    missing = []
    for var in required_vars:
        if not os.environ.get(var):
            missing.append(var)

    if missing:
        return False, f"Missing env vars: {', '.join(missing)}"
    return True, "All required env vars set"


def check_python_version() -> tuple[bool, str]:
    """
    Check Python version meets requirements.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    version = sys.version_info

    if version.major == 3 and version.minor >= 10:
        return True, f"Python {version.major}.{version.minor}.{version.micro}"
    else:
        return False, f"Python 3.10+ required, found {version.major}.{version.minor}"


def check_dependencies() -> tuple[bool, str]:
    """
    Check all dependencies are installed.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        result = subprocess.run(
            ['pip', 'check'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return True, "All dependencies satisfied"
        else:
            return False, result.stdout.strip() or "Dependency issues found"

    except Exception as e:
        return False, str(e)


def check_database_connection() -> tuple[bool, str]:
    """
    Check database connectivity.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        import django
        django.setup()
        from django.db import connection

        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return True, "Database connected"

    except Exception as e:
        return False, f"Database connection failed: {e}"


def check_redis_connection() -> tuple[bool, str]:
    """
    Check Redis connectivity.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    try:
        import django
        django.setup()
        from django.conf import settings
        import redis

        r = redis.from_url(settings.CELERY_BROKER_URL, socket_connect_timeout=5)
        r.ping()

        return True, "Redis connected"

    except Exception as e:
        return False, f"Redis connection failed: {e}"


def check_static_files() -> tuple[bool, str]:
    """
    Check static files are collected.

    Returns:
        Tuple of (passed: bool, message: str)
    """
    static_dir = PROJECT_ROOT / 'staticfiles'

    if static_dir.exists() and any(static_dir.iterdir()):
        return True, "Static files present"
    else:
        return False, "Run 'python manage.py collectstatic'"


def run_all_checks(skip_server_checks: bool = False) -> bool:
    """
    Run all pre-deployment checks.

    Args:
        skip_server_checks: Skip checks that require running server

    Returns:
        True if all checks passed, False otherwise
    """
    print_header("Pre-Deployment Validation")
    print(f"  Project: {PROJECT_ROOT}")
    print(f"  Time: {datetime.now().isoformat()}")

    all_passed = True
    results = []

    # Category: Environment
    print_header("Environment Checks")

    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_required_env_vars),
    ]

    for name, check_func in checks:
        passed, message = check_func()
        print_result(name, passed, message)
        results.append((name, passed, message))
        if not passed:
            all_passed = False

    # Category: Database
    print_header("Database Checks")

    checks = [
        ("Database Connection", check_database_connection),
        ("Migrations", check_migrations),
    ]

    for name, check_func in checks:
        passed, message = check_func()
        print_result(name, passed, message)
        results.append((name, passed, message))
        if not passed:
            all_passed = False

    # Category: Redis/Celery
    print_header("Message Queue Checks")

    passed, message = check_redis_connection()
    print_result("Redis Connection", passed, message)
    results.append(("Redis Connection", passed, message))
    # Redis failures are warnings, not blockers (we have sync fallback)

    # Category: Security
    print_header("Security Checks")

    passed, message = check_settings_security()
    print_result("Settings Security", passed, message)
    results.append(("Settings Security", passed, message))
    if not passed:
        all_passed = False

    # Category: Tests
    print_header("Test Suite")

    passed, message = check_django_tests()
    print_result("Django Tests", passed, message)
    results.append(("Django Tests", passed, message))
    if not passed:
        all_passed = False

    # Category: Server Checks (optional)
    if not skip_server_checks:
        print_header("Server Checks")

        passed, message = check_health_endpoint()
        print_result("Health Endpoint", passed, message)
        results.append(("Health Endpoint", passed, message))
        if not passed:
            print(f"  {Colors.YELLOW}Note: Start server with 'python manage.py runserver' to test{Colors.END}")

    # Summary
    print_header("Summary")

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    if all_passed:
        print(f"  {Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED ({passed_count}/{total_count}){Colors.END}")
        print(f"  {Colors.GREEN}Ready for deployment!{Colors.END}")
    else:
        print(f"  {Colors.RED}{Colors.BOLD}CHECKS FAILED ({passed_count}/{total_count} passed){Colors.END}")
        print(f"  {Colors.RED}Fix issues before deploying.{Colors.END}")

        print("\n  Failed checks:")
        for name, passed, message in results:
            if not passed:
                print(f"    - {name}: {message}")

    return all_passed


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Pre-deployment validation script"
    )
    parser.add_argument(
        '--skip-server-checks',
        action='store_true',
        help="Skip checks that require a running server"
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help="CI mode - skip server checks and suppress colors"
    )

    args = parser.parse_args()

    skip_server = args.skip_server_checks or args.ci

    if args.ci:
        # Disable colors in CI
        Colors.GREEN = ''
        Colors.RED = ''
        Colors.YELLOW = ''
        Colors.BLUE = ''
        Colors.BOLD = ''
        Colors.END = ''

    try:
        success = run_all_checks(skip_server_checks=skip_server)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.END}")
        sys.exit(1)


if __name__ == '__main__':
    main()
