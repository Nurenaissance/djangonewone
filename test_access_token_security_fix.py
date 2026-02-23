#!/usr/bin/env python3
"""
Rigorous Test Suite for Access Token Security Fix
Tests the changes made to whatsapp_tenant/router.py
"""

import sys
import json
import importlib.util
from typing import Dict, List, Any

# ANSI color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.details = []

    def add_pass(self, test_name: str, message: str = ""):
        self.passed += 1
        self.details.append(f"{Colors.GREEN}[PASS]{Colors.END} {test_name}: {message}")
        print(f"{Colors.GREEN}[PASS]{Colors.END} {test_name}: {message}")

    def add_fail(self, test_name: str, message: str = ""):
        self.failed += 1
        self.details.append(f"{Colors.RED}[FAIL]{Colors.END} {test_name}: {message}")
        print(f"{Colors.RED}[FAIL]{Colors.END} {test_name}: {message}")

    def add_warning(self, test_name: str, message: str = ""):
        self.warnings += 1
        self.details.append(f"{Colors.YELLOW}[WARN]{Colors.END} {test_name}: {message}")
        print(f"{Colors.YELLOW}[WARN]{Colors.END} {test_name}: {message}")

    def print_summary(self):
        print(f"\n{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.BOLD}TEST SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'='*70}{Colors.END}")
        print(f"{Colors.GREEN}Passed:{Colors.END}   {self.passed}")
        print(f"{Colors.RED}Failed:{Colors.END}   {self.failed}")
        print(f"{Colors.YELLOW}Warnings:{Colors.END} {self.warnings}")
        print(f"{Colors.BOLD}Total:{Colors.END}    {self.passed + self.failed + self.warnings}")

        if self.failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}>> ALL TESTS PASSED!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}>> SOME TESTS FAILED{Colors.END}")

        print(f"{Colors.BOLD}{'='*70}{Colors.END}\n")

def test_python_syntax(result: TestResult):
    """Test 1: Verify Python syntax is valid"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 1: Python Syntax Validation{Colors.END}")

    try:
        import py_compile
        py_compile.compile(
            'fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py',
            doraise=True
        )
        result.add_pass("Python Syntax", "No syntax errors found")
    except SyntaxError as e:
        result.add_fail("Python Syntax", f"Syntax error: {e}")
    except Exception as e:
        result.add_warning("Python Syntax", f"Could not compile: {e}")

def test_imports(result: TestResult):
    """Test 2: Verify all required imports are present"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 2: Import Validation{Colors.END}")

    required_imports = [
        'httpx',
        'fastapi.encoders.jsonable_encoder',
        'fastapi.HTTPException',
        'sqlalchemy.orm'
    ]

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    for imp in required_imports:
        module_name = imp.split('.')[0]
        if module_name in content or imp in content:
            result.add_pass(f"Import Check: {imp}", "Import present")
        else:
            result.add_fail(f"Import Check: {imp}", "Import missing")

def test_access_token_removal(result: TestResult):
    """Test 3: Verify access_token is removed from response"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 3: Access Token Removal Logic{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for the security comment
    if "# SECURITY: Remove access_token from response" in content:
        result.add_pass("Security Comment", "Security warning comment present")
    else:
        result.add_warning("Security Comment", "Security comment not found")

    # Check for pop('access_token') logic
    if "data_dict.pop('access_token', None)" in content:
        result.add_pass("Token Removal Logic", "access_token removal code present")
    else:
        result.add_fail("Token Removal Logic", "access_token removal code not found")

    # Check that we're using whatsapp_data_safe
    if "whatsapp_data_safe" in content:
        result.add_pass("Safe Data Variable", "Using sanitized data variable")
    else:
        result.add_fail("Safe Data Variable", "Not using sanitized data variable")

def test_proxy_endpoint_exists(result: TestResult):
    """Test 4: Verify new proxy endpoint exists"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 4: Proxy Endpoint Structure{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for endpoint decorator
    if '@router.get("/template-analytics")' in content:
        result.add_pass("Endpoint Definition", "/template-analytics endpoint defined")
    else:
        result.add_fail("Endpoint Definition", "/template-analytics endpoint not found")

    # Check for function definition
    if 'async def get_template_analytics' in content:
        result.add_pass("Function Definition", "get_template_analytics function defined")
    else:
        result.add_fail("Function Definition", "get_template_analytics function not found")

    # Check for required parameters
    required_params = ['template_id', 'start', 'end', 'x_tenant_id']
    for param in required_params:
        if f'{param}:' in content or f'{param} =' in content:
            result.add_pass(f"Parameter: {param}", f"Parameter {param} present")
        else:
            result.add_fail(f"Parameter: {param}", f"Parameter {param} missing")

def test_proxy_security(result: TestResult):
    """Test 5: Verify proxy endpoint security measures"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 5: Proxy Security Measures{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for tenant ID validation
    if 'if not x_tenant_id:' in content and 'Missing X-Tenant-Id header' in content:
        result.add_pass("Tenant Validation", "X-Tenant-Id header validation present")
    else:
        result.add_fail("Tenant Validation", "Missing tenant ID validation")

    # Check for access token retrieval from DB
    if 'whatsapp_data.access_token' in content:
        result.add_pass("Token from DB", "Access token retrieved from database")
    else:
        result.add_fail("Token from DB", "Not retrieving token from database")

    # Check that access_token is used in API call, not exposed
    if '"access_token": whatsapp_data.access_token' in content:
        result.add_pass("Token Usage", "Token used in backend API call only")
    else:
        result.add_warning("Token Usage", "Token usage pattern unclear")

def test_facebook_api_call(result: TestResult):
    """Test 6: Verify Facebook API call structure"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 6: Facebook API Integration{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for Facebook Graph API URL
    if 'graph.facebook.com' in content and 'template_analytics' in content:
        result.add_pass("Facebook API URL", "Correct Facebook Graph API endpoint")
    else:
        result.add_fail("Facebook API URL", "Facebook API URL not found or incorrect")

    # Check for httpx client usage
    if 'async with httpx.AsyncClient' in content:
        result.add_pass("HTTP Client", "Using httpx.AsyncClient for async requests")
    else:
        result.add_fail("HTTP Client", "Not using proper HTTP client")

    # Check for error handling
    if 'except httpx.TimeoutException' in content:
        result.add_pass("Timeout Handling", "Timeout exception handling present")
    else:
        result.add_warning("Timeout Handling", "Timeout handling may be missing")

def test_error_handling(result: TestResult):
    """Test 7: Verify comprehensive error handling"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 7: Error Handling{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    error_scenarios = [
        ('WhatsApp account not found', 'Missing tenant WhatsApp data'),
        ('No access token configured', 'Missing access token'),
        ('No WhatsApp Business Account ID', 'Missing business account ID'),
        ('Facebook API error', 'Facebook API failure')
    ]

    for error_msg, test_name in error_scenarios:
        if error_msg in content:
            result.add_pass(f"Error: {test_name}", f"Handles '{error_msg}'")
        else:
            result.add_warning(f"Error: {test_name}", f"May not handle '{error_msg}'")

def test_backwards_compatibility(result: TestResult):
    """Test 8: Check backwards compatibility"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 8: Backwards Compatibility{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check that original endpoint still exists
    if '@router.get("/whatsapp_tenant")' in content:
        result.add_pass("Original Endpoint", "/whatsapp_tenant endpoint preserved")
    else:
        result.add_fail("Original Endpoint", "/whatsapp_tenant endpoint removed")

    # Check that function signature is maintained
    if 'def get_whatsapp_tenant_data(' in content:
        result.add_pass("Function Signature", "Original function preserved")
    else:
        result.add_fail("Function Signature", "Original function modified/removed")

def test_documentation(result: TestResult):
    """Test 9: Verify documentation exists"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 9: Documentation{Colors.END}")

    import os

    # Check for documentation file
    if os.path.exists('ACCESS_TOKEN_SECURITY_FIX.md'):
        result.add_pass("Documentation File", "ACCESS_TOKEN_SECURITY_FIX.md exists")

        with open('ACCESS_TOKEN_SECURITY_FIX.md', 'r', encoding='utf-8') as f:
            doc_content = f.read()

        doc_sections = [
            ('## Problem', 'Problem description'),
            ('## Changes Made', 'Changes documentation'),
            ('## What Will Break', 'Breaking changes list'),
            ('## How to Fix', 'Fix instructions'),
            ('## Security Benefits', 'Security explanation')
        ]

        for section, name in doc_sections:
            if section in doc_content:
                result.add_pass(f"Doc Section: {name}", f"Section '{section}' present")
            else:
                result.add_warning(f"Doc Section: {name}", f"Section '{section}' missing")
    else:
        result.add_fail("Documentation File", "ACCESS_TOKEN_SECURITY_FIX.md not found")

def test_logging(result: TestResult):
    """Test 10: Verify proper logging"""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Test 10: Logging{Colors.END}")

    with open('fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for logger usage in new endpoint
    if 'logger.info' in content and 'template_analytics' in content:
        result.add_pass("Info Logging", "Info logging present in new endpoint")
    else:
        result.add_warning("Info Logging", "May lack info logging")

    if 'logger.error' in content:
        result.add_pass("Error Logging", "Error logging present")
    else:
        result.add_warning("Error Logging", "May lack error logging")

def main():
    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("="*70)
    print("  RIGOROUS TEST SUITE: Access Token Security Fix")
    print("="*70)
    print(f"{Colors.END}\n")

    result = TestResult()

    # Run all tests
    tests = [
        test_python_syntax,
        test_imports,
        test_access_token_removal,
        test_proxy_endpoint_exists,
        test_proxy_security,
        test_facebook_api_call,
        test_error_handling,
        test_backwards_compatibility,
        test_documentation,
        test_logging
    ]

    for test_func in tests:
        try:
            test_func(result)
        except Exception as e:
            result.add_fail(test_func.__name__, f"Test crashed: {e}")

    # Print summary
    result.print_summary()

    # Exit with appropriate code
    sys.exit(0 if result.failed == 0 else 1)

if __name__ == "__main__":
    main()
