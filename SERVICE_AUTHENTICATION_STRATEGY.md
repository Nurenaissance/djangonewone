# Service-to-Service Authentication Strategy
**Date**: 2026-01-06
**Version**: 1.0

---

## Problem Statement

When enabling JWT authentication on all services (Django, FastAPI, Node.js), service-to-service communication breaks because:
- Services need to call each other's APIs
- Tenant-specific JWT tokens don't work for service-level operations
- Services need to perform operations on behalf of multiple tenants
- Cannot use user tokens for automated/background operations

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│         Uses User JWT Tokens (tenant-specific)              │
└─────────────────────────────────────────────────────────────┘
                          ↓
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼───────────┐            ┌──────────▼──────────┐
│   DJANGO BACKEND  │ ←────────→ │  FASTAPI BACKEND    │
│                   │            │                     │
│  Service Token +  │            │  Service Token +    │
│  Tenant Context   │            │  Tenant Context     │
└───────┬───────────┘            └──────────┬──────────┘
        │                                   │
        │         ┌─────────────────────────┘
        │         │
        └─────────▼─────────────┐
              │ NODE.JS BOT     │
              │                 │
              │ Service Token + │
              │ Tenant Context  │
              └─────────────────┘
```

## Solution: Dual Authentication System

### Option 1: Service API Keys with Tenant Headers (RECOMMENDED)

**Concept**: Use special API keys for service-to-service calls, but still pass tenant context via headers.

#### Implementation

##### 1. Generate Service API Keys

```python
# File: shared_utils/service_auth.py (create in all projects)

import secrets
import hashlib
from datetime import datetime, timedelta

class ServiceAuthManager:
    """Manage service-to-service authentication"""

    # Service API keys (store in environment variables)
    SERVICE_KEYS = {
        'django': None,      # Will be loaded from env
        'fastapi': None,     # Will be loaded from env
        'nodejs': None,      # Will be loaded from env
    }

    @classmethod
    def load_from_env(cls):
        """Load service keys from environment"""
        import os
        cls.SERVICE_KEYS['django'] = os.getenv('DJANGO_SERVICE_KEY')
        cls.SERVICE_KEYS['fastapi'] = os.getenv('FASTAPI_SERVICE_KEY')
        cls.SERVICE_KEYS['nodejs'] = os.getenv('NODEJS_SERVICE_KEY')

    @classmethod
    def generate_service_key(cls, service_name: str) -> str:
        """Generate a new service API key"""
        random_part = secrets.token_urlsafe(32)
        key = f"sk_{service_name}_{random_part}"
        return key

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash a service key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()

    @classmethod
    def verify_service_key(cls, provided_key: str) -> tuple[bool, str]:
        """
        Verify if provided key is valid for any service
        Returns: (is_valid, service_name)
        """
        for service_name, stored_key in cls.SERVICE_KEYS.items():
            if stored_key and provided_key == stored_key:
                return True, service_name

        return False, None


# Generate keys (run once, store in env vars)
def generate_all_keys():
    """Generate keys for all services"""
    keys = {}
    for service in ['django', 'fastapi', 'nodejs']:
        key = ServiceAuthManager.generate_service_key(service)
        keys[service] = key
        print(f"{service.upper()}_SERVICE_KEY={key}")
    return keys


if __name__ == "__main__":
    print("Generate these keys and add to .env files:")
    print("-" * 60)
    generate_all_keys()
```

**Generate Keys** (run once):
```bash
python shared_utils/service_auth.py

# Output:
# DJANGO_SERVICE_KEY=sk_django_abc123...
# FASTAPI_SERVICE_KEY=sk_fastapi_xyz789...
# NODEJS_SERVICE_KEY=sk_nodejs_def456...
```

##### 2. FastAPI Middleware Update

```python
# File: fastAPIWhatsapp_withclaude/config/middleware.py

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import jwt
import os
from typing import Optional

# Load service keys
SERVICE_KEYS = {
    'django': os.getenv('DJANGO_SERVICE_KEY'),
    'fastapi': os.getenv('FASTAPI_SERVICE_KEY'),
    'nodejs': os.getenv('NODEJS_SERVICE_KEY'),
}

# Public routes (no auth required)
PUBLIC_ROUTES = [
    "/health",
    "/",
    "/docs",
    "/openapi.json",
]

# Service routes (service key auth only)
SERVICE_ROUTES = [
    "/admin/",
    "/internal/",
]


def is_valid_service_key(api_key: str) -> tuple[bool, Optional[str]]:
    """Check if API key is a valid service key"""
    for service_name, key in SERVICE_KEYS.items():
        if key and api_key == key:
            return True, service_name
    return False, None


async def jwt_middleware(request: Request, call_next):
    """
    Enhanced JWT middleware with service-to-service authentication support

    Authentication priority:
    1. Check if route is public -> Allow
    2. Check for service API key -> Allow (service-level access)
    3. Check for user JWT token -> Validate and allow
    4. Reject request
    """

    path = request.url.path

    # 1. Allow public routes
    if path in PUBLIC_ROUTES or path.startswith("/docs"):
        return await call_next(request)

    # 2. Check for Service API Key (X-Service-Key header)
    service_key = request.headers.get("X-Service-Key")

    if service_key:
        is_valid, service_name = is_valid_service_key(service_key)

        if is_valid:
            # Valid service key - allow request
            # Add service identity to request state
            request.state.is_service_request = True
            request.state.service_name = service_name

            # Still require X-Tenant-Id for tenant-specific operations
            tenant_id = request.headers.get("X-Tenant-Id")
            if tenant_id:
                request.state.tenant_id = tenant_id

            print(f"✅ Service request from: {service_name}")
            return await call_next(request)
        else:
            return JSONResponse(
                status_code=403,
                content={"detail": "Invalid service key"}
            )

    # 3. Check for User JWT Token (existing logic)
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid authorization header"}
        )

    token = auth_header.split(" ")[1]

    try:
        # Decode and verify JWT
        secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])

        # Add user info to request state
        request.state.user_id = payload.get("user_id")
        request.state.tenant_id = payload.get("tenant_id")
        request.state.is_service_request = False

        return await call_next(request)

    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token has expired"}
        )
    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"detail": f"Authentication failed: {str(e)}"}
        )
```

##### 3. Django Middleware Update

```python
# File: whatsapp_latest_final_withclaude/simplecrm/middleware.py

import os
import jwt
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

# Load service keys
SERVICE_KEYS = {
    'django': os.getenv('DJANGO_SERVICE_KEY'),
    'fastapi': os.getenv('FASTAPI_SERVICE_KEY'),
    'nodejs': os.getenv('NODEJS_SERVICE_KEY'),
}

# Public URLs (no auth required)
PUBLIC_URLS = [
    '/health/',
    '/admin/',  # Django admin uses its own auth
    '/register/',
    '/login/',
    '/oauth/token/',
]


class ServiceAuthMiddleware(MiddlewareMixin):
    """
    Middleware to handle both user JWT tokens and service API keys

    Must be placed BEFORE any other authentication middleware
    """

    def is_valid_service_key(self, api_key):
        """Check if API key is valid"""
        for service_name, key in SERVICE_KEYS.items():
            if key and api_key == key:
                return True, service_name
        return False, None

    def process_request(self, request):
        """Process incoming request for authentication"""

        path = request.path

        # 1. Allow public URLs
        if any(path.startswith(url) for url in PUBLIC_URLS):
            return None

        # 2. Check for Service API Key
        service_key = request.META.get('HTTP_X_SERVICE_KEY')

        if service_key:
            is_valid, service_name = self.is_valid_service_key(service_key)

            if is_valid:
                # Valid service request
                request.is_service_request = True
                request.service_name = service_name

                # Get tenant context if provided
                tenant_id = request.META.get('HTTP_X_TENANT_ID')
                if tenant_id:
                    request.tenant_id = tenant_id

                print(f"✅ Service request from: {service_name}")
                return None  # Allow request to proceed
            else:
                return JsonResponse(
                    {'detail': 'Invalid service key'},
                    status=403
                )

        # 3. Check for User JWT Token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Bearer '):
            return JsonResponse(
                {'detail': 'Missing or invalid authorization header'},
                status=401
            )

        token = auth_header.split(' ')[1]

        try:
            # Decode JWT
            secret_key = os.getenv('JWT_SECRET_KEY', 'your-secret-key')
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])

            # Add user info to request
            request.user_id = payload.get('user_id')
            request.tenant_id = payload.get('tenant_id')
            request.is_service_request = False

            return None  # Allow request to proceed

        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {'detail': 'Token has expired'},
                status=401
            )
        except jwt.InvalidTokenError:
            return JsonResponse(
                {'detail': 'Invalid token'},
                status=401
            )
        except Exception as e:
            return JsonResponse(
                {'detail': f'Authentication failed: {str(e)}'},
                status=401
            )
```

**Update settings.py**:
```python
# File: whatsapp_latest_final_withclaude/simplecrm/settings.py

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Add this BEFORE any custom auth middleware
    'simplecrm.middleware.ServiceAuthMiddleware',

    # Your existing custom middleware...
]
```

##### 4. Node.js Middleware Update

```javascript
// File: whatsapp_bot_server_withclaude/middleware/auth.js

const jwt = require('jsonwebtoken');

// Load service keys
const SERVICE_KEYS = {
  django: process.env.DJANGO_SERVICE_KEY,
  fastapi: process.env.FASTAPI_SERVICE_KEY,
  nodejs: process.env.NODEJS_SERVICE_KEY,
};

// Public routes
const PUBLIC_ROUTES = [
  '/health',
  '/webhook',  // Webhook has its own validation
];

/**
 * Check if API key is valid
 */
function isValidServiceKey(apiKey) {
  for (const [serviceName, key] of Object.entries(SERVICE_KEYS)) {
    if (key && apiKey === key) {
      return { valid: true, serviceName };
    }
  }
  return { valid: false, serviceName: null };
}

/**
 * Authentication middleware supporting both user tokens and service keys
 */
function authMiddleware(req, res, next) {
  const path = req.path;

  // 1. Allow public routes
  if (PUBLIC_ROUTES.includes(path) || path.startsWith('/docs')) {
    return next();
  }

  // 2. Check for Service API Key
  const serviceKey = req.headers['x-service-key'];

  if (serviceKey) {
    const { valid, serviceName } = isValidServiceKey(serviceKey);

    if (valid) {
      // Valid service request
      req.isServiceRequest = true;
      req.serviceName = serviceName;

      // Get tenant context
      const tenantId = req.headers['x-tenant-id'];
      if (tenantId) {
        req.tenantId = tenantId;
      }

      console.log(`✅ Service request from: ${serviceName}`);
      return next();
    } else {
      return res.status(403).json({ error: 'Invalid service key' });
    }
  }

  // 3. Check for User JWT Token
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({ error: 'Missing or invalid authorization header' });
  }

  const token = authHeader.split(' ')[1];

  try {
    // Verify JWT
    const secret = process.env.JWT_SECRET_KEY || 'your-secret-key';
    const payload = jwt.verify(token, secret);

    // Add user info to request
    req.userId = payload.user_id;
    req.tenantId = payload.tenant_id;
    req.isServiceRequest = false;

    next();

  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({ error: 'Token has expired' });
    }
    return res.status(401).json({ error: 'Invalid token' });
  }
}

module.exports = { authMiddleware };
```

**Update server.js**:
```javascript
// File: whatsapp_bot_server_withclaude/server.js

const { authMiddleware } = require('./middleware/auth');

// Apply auth middleware to all routes except webhook
app.use((req, res, next) => {
  // Skip auth for webhook (it has signature validation)
  if (req.path === '/webhook') {
    return next();
  }
  authMiddleware(req, res, next);
});

// ... rest of your routes
```

##### 5. Service Client Utilities

Create helper functions for making service-to-service API calls:

**Python (for Django/FastAPI)**:
```python
# File: shared_utils/service_client.py

import os
import httpx
from typing import Optional, Dict, Any

class ServiceClient:
    """Client for making authenticated service-to-service API calls"""

    def __init__(self, service_name: str):
        """
        Initialize service client

        Args:
            service_name: Name of the calling service ('django', 'fastapi', 'nodejs')
        """
        self.service_name = service_name
        self.service_key = os.getenv(f"{service_name.upper()}_SERVICE_KEY")

        if not self.service_key:
            raise ValueError(f"Missing service key for {service_name}")

    def get_headers(self, tenant_id: Optional[str] = None) -> Dict[str, str]:
        """
        Get headers for service request

        Args:
            tenant_id: Tenant ID for tenant-specific operations
        """
        headers = {
            'X-Service-Key': self.service_key,
            'Content-Type': 'application/json',
        }

        if tenant_id:
            headers['X-Tenant-Id'] = tenant_id

        return headers

    async def get(
        self,
        url: str,
        tenant_id: Optional[str] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make GET request to another service"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.get_headers(tenant_id),
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def post(
        self,
        url: str,
        data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make POST request to another service"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self.get_headers(tenant_id),
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def patch(
        self,
        url: str,
        data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make PATCH request to another service"""
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                url,
                headers=self.get_headers(tenant_id),
                json=data,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def delete(
        self,
        url: str,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Make DELETE request to another service"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=self.get_headers(tenant_id),
                timeout=30.0
            )
            response.raise_for_status()
            return response.json() if response.content else {}


# Usage example in FastAPI
from shared_utils.service_client import ServiceClient

# Initialize client (do this once, maybe in main.py)
django_client = ServiceClient('fastapi')  # FastAPI identifying itself

# Make authenticated call to Django
async def get_contact_from_django(phone: str, tenant_id: str):
    url = f"{DJANGO_URL}/contacts-by-phone/{phone}/"
    return await django_client.get(url, tenant_id=tenant_id)

# Make authenticated call to Django with data
async def update_campaign_status(campaign_id: str, status: str, tenant_id: str):
    url = f"{DJANGO_URL}/api/campaigns/{campaign_id}/"
    data = {"status": status}
    return await django_client.patch(url, data, tenant_id=tenant_id)
```

**JavaScript (for Node.js)**:
```javascript
// File: whatsapp_bot_server_withclaude/services/serviceClient.js

const axios = require('axios');

class ServiceClient {
  /**
   * Client for making authenticated service-to-service API calls
   * @param {string} serviceName - Name of calling service ('nodejs')
   */
  constructor(serviceName) {
    this.serviceName = serviceName;
    this.serviceKey = process.env[`${serviceName.toUpperCase()}_SERVICE_KEY`];

    if (!this.serviceKey) {
      throw new Error(`Missing service key for ${serviceName}`);
    }
  }

  /**
   * Get headers for service request
   * @param {string|null} tenantId - Tenant ID for tenant-specific operations
   */
  getHeaders(tenantId = null) {
    const headers = {
      'X-Service-Key': this.serviceKey,
      'Content-Type': 'application/json',
    };

    if (tenantId) {
      headers['X-Tenant-Id'] = tenantId;
    }

    return headers;
  }

  /**
   * Make GET request to another service
   */
  async get(url, tenantId = null, params = null) {
    try {
      const response = await axios.get(url, {
        headers: this.getHeaders(tenantId),
        params: params,
        timeout: 30000,
      });
      return response.data;
    } catch (error) {
      console.error(`Service call failed: GET ${url}`, error.message);
      throw error;
    }
  }

  /**
   * Make POST request to another service
   */
  async post(url, data, tenantId = null) {
    try {
      const response = await axios.post(url, data, {
        headers: this.getHeaders(tenantId),
        timeout: 30000,
      });
      return response.data;
    } catch (error) {
      console.error(`Service call failed: POST ${url}`, error.message);
      throw error;
    }
  }

  /**
   * Make PATCH request to another service
   */
  async patch(url, data, tenantId = null) {
    try {
      const response = await axios.patch(url, data, {
        headers: this.getHeaders(tenantId),
        timeout: 30000,
      });
      return response.data;
    } catch (error) {
      console.error(`Service call failed: PATCH ${url}`, error.message);
      throw error;
    }
  }

  /**
   * Make DELETE request to another service
   */
  async delete(url, tenantId = null) {
    try {
      const response = await axios.delete(url, {
        headers: this.getHeaders(tenantId),
        timeout: 30000,
      });
      return response.data;
    } catch (error) {
      console.error(`Service call failed: DELETE ${url}`, error.message);
      throw error;
    }
  }
}

// Create singleton instances
const nodejsClient = new ServiceClient('nodejs');

module.exports = { ServiceClient, nodejsClient };
```

**Usage in Node.js**:
```javascript
// File: whatsapp_bot_server_withclaude/routes/webhookRoute.js

const { nodejsClient } = require('../services/serviceClient');
const { djangoURL } = require('../config');

// Example: Get contact from Django
async function getContactInfo(phone, tenantId) {
  const url = `${djangoURL}/contacts-by-phone/${phone}/`;
  return await nodejsClient.get(url, tenantId);
}

// Example: Track analytics in FastAPI
async function trackAnalytics(eventData, tenantId) {
  const url = `${fastAPIURL}/api/analytics/track-event`;
  return await nodejsClient.post(url, eventData, tenantId);
}

// Use in webhook handler
router.post('/webhook', async (req, res) => {
  // ... validation ...

  const tenantId = 'ai'; // Get from somewhere
  const phone = '919876543210';

  // Now this works with service authentication!
  const contact = await getContactInfo(phone, tenantId);

  // ... rest of logic ...
});
```

##### 6. Environment Variables Setup

**All Services (.env files)**:
```env
# Service Authentication Keys
DJANGO_SERVICE_KEY=sk_django_abc123xyz789def456...
FASTAPI_SERVICE_KEY=sk_fastapi_xyz789abc123ghi456...
NODEJS_SERVICE_KEY=sk_nodejs_def456ghi789jkl012...

# JWT Secret (should be same across all services for user tokens)
JWT_SECRET_KEY=your-shared-jwt-secret-key-here

# Service URLs (for making cross-service calls)
DJANGO_URL=http://localhost:8000
FASTAPI_URL=http://localhost:8001
NODEJS_URL=http://localhost:3000
```

---

## How It Works: Complete Flow

### User Request Flow
```
1. Frontend sends request with user JWT token
   Authorization: Bearer eyJhbGc...
   X-Tenant-Id: ai

2. Backend receives request
   - Middleware checks Authorization header
   - Validates JWT token
   - Extracts user_id and tenant_id from token
   - Request proceeds with user context

3. Response sent back to frontend
```

### Service-to-Service Request Flow
```
1. Node.js needs to call Django API
   - Node.js creates request with service key
   X-Service-Key: sk_nodejs_def456...
   X-Tenant-Id: ai

2. Django receives request
   - Middleware checks X-Service-Key header
   - Validates service key (matches NODEJS_SERVICE_KEY)
   - Identifies caller as "nodejs" service
   - Extracts tenant_id from X-Tenant-Id header
   - Request proceeds with service context + tenant scope

3. Django returns data to Node.js
```

### Multi-Tenant Service Operation
```
Example: Node.js webhook processes message for tenant "ai"

1. Webhook receives WhatsApp message
   - Extracts tenant info from BPID mapping
   - tenant_id = "ai"

2. Node.js needs contact info from Django
   GET /contacts-by-phone/919876543210/
   Headers:
     X-Service-Key: sk_nodejs_def456...
     X-Tenant-Id: ai

3. Django middleware:
   - Validates service key ✅
   - Sees tenant_id = "ai"
   - Allows request to proceed

4. Django view:
   - Gets tenant_id from request.tenant_id
   - Queries Contact.objects.filter(tenant_id='ai', phone='...')
   - Returns contact for tenant "ai" ONLY

5. Node.js receives contact data
   - Continues processing for tenant "ai"
```

---

## Security Benefits

### 1. Service Identity Validation
- Each service has unique key
- Can track which service made which call
- Can revoke/rotate keys independently

### 2. Tenant Isolation Maintained
- Service key grants access to API
- Tenant context still required for data access
- No cross-tenant data leakage
- Views still filter by tenant_id

### 3. Audit Trail
```python
# Can log service requests
if request.is_service_request:
    logger.info(f"Service request: {request.service_name} -> {request.path} (tenant: {request.tenant_id})")
```

### 4. Rate Limiting
```python
# Can apply different rate limits to services
if request.is_service_request:
    # Higher rate limit for services
    pass
else:
    # Lower rate limit for user requests
    pass
```

### 5. Permission Control
```python
# Can restrict certain operations to services only
if path.startswith('/admin/') and not request.is_service_request:
    return JsonResponse({'error': 'Admin operations require service authentication'}, status=403)
```

---

## Migration Plan

### Phase 1: Setup (1 hour)

1. **Generate Service Keys**:
```bash
python shared_utils/service_auth.py
```

2. **Add to Environment Variables** (all services):
```bash
# .env for each service
DJANGO_SERVICE_KEY=sk_django_...
FASTAPI_SERVICE_KEY=sk_fastapi_...
NODEJS_SERVICE_KEY=sk_nodejs_...
JWT_SECRET_KEY=shared-secret-123
```

3. **Deploy Service Client Utilities**:
- Copy `service_client.py` to Django and FastAPI
- Copy `serviceClient.js` to Node.js

### Phase 2: Update Middleware (2 hours)

1. **FastAPI**: Update `config/middleware.py`
2. **Django**: Update `simplecrm/middleware.py` + settings.py
3. **Node.js**: Create `middleware/auth.js` + update server.js

### Phase 3: Update Service Calls (3 hours)

**Find all cross-service API calls**:
```bash
# Django calling FastAPI or Node.js
grep -r "requests.get\|requests.post" whatsapp_latest_final_withclaude/

# FastAPI calling Django
grep -r "httpx\|requests" fastAPIWhatsapp_withclaude/

# Node.js calling Django or FastAPI
grep -r "axios.get\|axios.post" whatsapp_bot_server_withclaude/
```

**Update Each Call**:
```python
# BEFORE:
response = requests.get(f"{DJANGO_URL}/contacts-by-phone/{phone}/")

# AFTER:
from shared_utils.service_client import ServiceClient
client = ServiceClient('fastapi')
response = await client.get(
    f"{DJANGO_URL}/contacts-by-phone/{phone}/",
    tenant_id=tenant_id
)
```

### Phase 4: Testing (2 hours)

1. **Test User Authentication**:
```bash
# Should work
curl -X GET http://localhost:8001/contacts \
  -H "Authorization: Bearer <user-token>" \
  -H "X-Tenant-Id: ai"
```

2. **Test Service Authentication**:
```bash
# Should work
curl -X GET http://localhost:8000/contacts-by-phone/919876543210/ \
  -H "X-Service-Key: sk_nodejs_..." \
  -H "X-Tenant-Id: ai"
```

3. **Test Service-to-Service Call**:
```javascript
// In Node.js webhook, trigger a call to Django
// Should see in Django logs: "✅ Service request from: nodejs"
```

4. **Test Tenant Isolation**:
```bash
# Service request for tenant1 should not see tenant2 data
curl -X GET http://localhost:8000/contacts \
  -H "X-Service-Key: sk_nodejs_..." \
  -H "X-Tenant-Id: tenant1"
# Should only return tenant1 contacts
```

### Phase 5: Enable JWT Middleware (30 minutes)

Only after service authentication is working:

1. **FastAPI**: Uncomment JWT middleware in main.py
2. **Test Everything Still Works**:
   - User requests work
   - Service requests work
   - Frontend works
   - Webhooks work

---

## Common Service Call Patterns

### Pattern 1: Node.js → Django (Get Contact)
```javascript
// Node.js webhook gets message from user
const userPhone = message.from;
const tenantId = getTenantIdFromBPID(bpid);

// Call Django to get contact info
const contact = await nodejsClient.get(
  `${djangoURL}/contacts-by-phone/${userPhone}/`,
  tenantId
);

console.log(`Contact name: ${contact.name}`);
```

### Pattern 2: Django → FastAPI (Get Analytics)
```python
# Django view needs to show analytics
from shared_utils.service_client import ServiceClient

client = ServiceClient('django')
analytics = await client.get(
    f"{FASTAPI_URL}/broadcast-analytics/",
    tenant_id=request.tenant_id
)

return JsonResponse(analytics)
```

### Pattern 3: FastAPI → Node.js (Track Event)
```python
# FastAPI scheduled event triggers
from shared_utils.service_client import ServiceClient

client = ServiceClient('fastapi')
result = await client.post(
    f"{NODEJS_URL}/api/analytics/track-event",
    data={
        'eventType': 'scheduled.send',
        'templateId': template_id,
        # ... other data
    },
    tenant_id=tenant_id
)
```

### Pattern 4: Background Job (Multi-Tenant)
```python
# Celery task needs to process for all tenants
from shared_utils.service_client import ServiceClient

client = ServiceClient('django')

# Get all tenant IDs
tenants = await client.get(f"{FASTAPI_URL}/tenants/ids")

for tenant_id in tenants['tenant_ids']:
    # Process for each tenant
    analytics = await client.get(
        f"{FASTAPI_URL}/broadcast-analytics/",
        tenant_id=tenant_id
    )
    # ... process analytics ...
```

---

## Alternative Approaches (Not Recommended)

### Option 2: Internal Network / IP Whitelisting
**Concept**: Allow requests from specific IPs without authentication

**Pros**:
- Simple to implement
- No token management

**Cons**:
- Not secure if services are internet-accessible
- Doesn't work in cloud environments with dynamic IPs
- No audit trail of which service made which call
- ❌ NOT RECOMMENDED for production

### Option 3: Mutual TLS (mTLS)
**Concept**: Use SSL certificates for service authentication

**Pros**:
- Very secure
- Industry standard

**Cons**:
- Complex setup and certificate management
- Overkill for internal services
- More operational overhead
- ❌ OVERKILL for your use case

### Option 4: Service-Specific Endpoints
**Concept**: Create separate endpoints just for service calls

**Pros**:
- Clear separation

**Cons**:
- Code duplication
- Harder to maintain
- Doesn't scale
- ❌ BAD ARCHITECTURE

---

## Troubleshooting

### Issue: Service call gets 401 Unauthorized

**Check**:
1. Service key is in .env file
2. Service key matches on both sides
3. Header is `X-Service-Key` (case-sensitive)
4. Middleware is loaded before routes

**Debug**:
```python
# Add to middleware
print(f"Headers: {request.headers}")
print(f"Service key: {request.headers.get('X-Service-Key')}")
print(f"Expected: {SERVICE_KEYS}")
```

### Issue: Service call works but gets wrong tenant data

**Check**:
1. `X-Tenant-Id` header is being sent
2. Middleware extracts tenant_id correctly
3. Views filter by tenant_id

**Debug**:
```python
# Add to view
print(f"Request tenant: {request.tenant_id}")
print(f"Is service: {request.is_service_request}")
```

### Issue: Circular dependency (service A calls B, B calls A)

**Solution**: Avoid circular calls, use message queue instead
```python
# Instead of A -> B -> A
# Do: A -> Queue, B -> Queue
```

---

## Security Checklist

- [ ] All service keys generated and unique
- [ ] Service keys stored in environment variables (not code)
- [ ] Service keys are long and random (32+ characters)
- [ ] JWT secret is same across all services
- [ ] Middleware validates service keys before allowing access
- [ ] Tenant context always passed with service requests
- [ ] Views still filter by tenant_id (don't trust service key alone)
- [ ] Service requests logged for audit trail
- [ ] Rate limiting applied to service endpoints
- [ ] Service keys rotated regularly (quarterly)
- [ ] Old service keys revoked after rotation

---

## Key Takeaways

1. **Service keys grant API access, NOT data access**
   - Service key = "I am a trusted service"
   - Tenant ID = "I want data for this tenant"
   - View filtering = "Here's only that tenant's data"

2. **Tenant isolation is maintained at the data layer**
   - Service key doesn't bypass tenant filtering
   - Views must still check tenant_id
   - Multi-tenant security still intact

3. **Two types of requests, one codebase**
   - User requests: JWT token authentication
   - Service requests: Service key authentication
   - Same endpoints, same views, different auth

4. **Simple but secure**
   - No complex token generation
   - No certificate management
   - Easy to rotate keys
   - Full audit trail

---

## Next Steps

1. Generate service keys (5 min)
2. Update middleware in all services (1 hour)
3. Deploy service client utilities (30 min)
4. Update existing service calls (2-3 hours)
5. Test thoroughly (2 hours)
6. Enable JWT middleware (30 min)
7. Monitor logs for authentication errors (ongoing)

**Estimated Total Time**: 6-8 hours

---

## Summary

This dual authentication system provides:
- ✅ Secure service-to-service communication
- ✅ Maintains tenant isolation
- ✅ Works with existing JWT user authentication
- ✅ Simple to implement and manage
- ✅ Full audit trail
- ✅ Can rotate keys without downtime
- ✅ Supports multi-tenant operations
- ✅ No architectural changes required

You can now safely enable JWT authentication on all services while maintaining full service-to-service communication capabilities.
