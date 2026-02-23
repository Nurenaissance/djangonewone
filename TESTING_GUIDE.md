# Service Authentication - Testing Guide

**Date**: 2026-01-06
**Status**: Ready for Testing

---

## 🎉 Implementation Complete!

All code changes are complete. Now it's time to test the service authentication system.

---

## Prerequisites

Before testing, ensure:
- ✅ All .env files are created (Django, FastAPI, Node.js)
- ✅ Service keys are configured in all .env files
- ✅ JWT_SECRET is configured (same across all services)
- ✅ Database credentials are correct
- ✅ All services can connect to their databases

---

## Testing Strategy

We'll test in phases:

1. **Phase 1**: Service authentication (without JWT middleware active)
2. **Phase 2**: Enable JWT middleware (after Phase 1 succeeds)
3. **Phase 3**: End-to-end testing

---

## Phase 1: Test Service Authentication

### Step 1.1: Start All Services

**Terminal 1 - Django:**
```bash
cd whatsapp_latest_final_withclaude
python manage.py runserver 8000
```

**Terminal 2 - FastAPI:**
```bash
cd fastAPIWhatsapp_withclaude
uvicorn main:app --reload --port 8001
```

**Terminal 3 - Node.js:**
```bash
cd whatsapp_bot_server_withclaude
npm start
# or
node server.js
```

### Step 1.2: Test Service Authentication to Django

**Test 1: Valid Service Key (Node.js → Django)**
```bash
curl -X GET http://localhost:8000/contacts-by-phone/919876543210/ \
  -H "X-Service-Key: sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34" \
  -H "X-Tenant-Id: ai"
```

**Expected Response:**
- Status 200 or 404 (404 is OK if contact doesn't exist)
- JSON response with contact data or error message
- **NOT** an authentication error

**What to Check in Django Logs:**
```
Service-authenticated request from nodejs for tenant ai
```

---

**Test 2: Invalid Service Key (Should Fail)**
```bash
curl -X GET http://localhost:8000/contacts-by-phone/919876543210/ \
  -H "X-Service-Key: sk_invalid_key_12345" \
  -H "X-Tenant-Id: ai"
```

**Expected Response:**
- Status 403 (Forbidden)
- JSON: `{"error": "Invalid service key"}`

**What to Check in Django Logs:**
```
Invalid service key provided in request
```

---

**Test 3: Missing Tenant ID**
```bash
curl -X GET http://localhost:8000/contacts-by-phone/919876543210/ \
  -H "X-Service-Key: sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34"
```

**Expected Response:**
- Status 400 or 403
- JSON: Error about missing tenant ID

---

### Step 1.3: Test Service Authentication to FastAPI

**NOTE**: FastAPI JWT middleware is currently **DISABLED** (line 146 in main.py is commented).
This means FastAPI will accept requests without authentication for now.

**Test 4: Check FastAPI Service Authentication (Currently Bypassed)**
```bash
curl -X GET http://localhost:8001/api/analytics/messages/stats \
  -H "X-Service-Key: sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34" \
  -H "X-Tenant-Id: ai"
```

**Expected Response:**
- Status 200 (will work even without auth because middleware is disabled)
- JSON response with message stats or empty array

**After Phase 1 succeeds, we'll enable FastAPI middleware in Phase 2.**

---

## Phase 2: Enable JWT Middleware (OPTIONAL - Do After Phase 1 Works)

### Step 2.1: Enable FastAPI Middleware

**Edit**: `fastAPIWhatsapp_withclaude/main.py`

**Line 146 - Change from:**
```python
#app.middleware("http")(jwt_middleware)
```

**To:**
```python
app.middleware("http")(jwt_middleware)
```

**Save and restart FastAPI server.**

---

### Step 2.2: Test FastAPI Service Authentication (With Middleware Active)

**Test 5: Valid Service Key to FastAPI**
```bash
curl -X GET http://localhost:8001/api/analytics/messages/stats \
  -H "X-Service-Key: sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34" \
  -H "X-Tenant-Id: ai"
```

**Expected Response:**
- Status 200
- JSON response with data

**What to Check in FastAPI Logs:**
```
Service-authenticated request from nodejs
```

---

**Test 6: Invalid Service Key to FastAPI (Should Fail)**
```bash
curl -X GET http://localhost:8001/api/analytics/messages/stats \
  -H "X-Service-Key: sk_invalid_key" \
  -H "X-Tenant-Id: ai"
```

**Expected Response:**
- Status 403
- JSON: `{"detail": "Invalid service key"}`

---

### Step 2.3: Test User Authentication Still Works

**Test 7: User Login (Get JWT Token)**
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_test_user",
    "password": "your_test_password"
  }'
```

**Expected Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 1,
    "username": "your_test_user",
    "tenant": "ai"
  }
}
```

**Copy the `access` token for the next test.**

---

**Test 8: User-Authenticated Request to Django**
```bash
curl -X GET http://localhost:8000/contacts/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

**Expected Response:**
- Status 200
- JSON array of contacts

---

**Test 9: User-Authenticated Request to FastAPI**
```bash
curl -X GET http://localhost:8001/api/analytics/messages/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

**Expected Response:**
- Status 200
- JSON response with analytics data

---

## Phase 3: End-to-End Testing

### Test 10: Node.js Calling Django (Real Service Call)

**Check Node.js code that calls Django:**

Look for files in `whatsapp_bot_server_withclaude/` that make HTTP calls to Django.

**Example locations to check:**
- `routes/*.js`
- `controllers/*.js`
- `services/*.js`

**What to look for:**
```javascript
// Old way (without service authentication)
const response = await axios.get(`${DJANGO_URL}/contacts-by-phone/${phone}/`);

// New way (with service authentication) - FUTURE UPDATE
const { nodejsClient } = require('./services/serviceClient');
const contact = await nodejsClient.get(
  `${DJANGO_URL}/contacts-by-phone/${phone}/`,
  tenantId
);
```

**For now**, existing calls will work because:
- FastAPI JWT middleware is disabled
- Django middleware allows public routes

**Later**, you'll want to update these calls to use `ServiceClient`.

---

### Test 11: Real WhatsApp Webhook Flow

**Trigger a real WhatsApp message** to your bot and verify:

1. **Node.js receives webhook** → logs show "Received WhatsApp message"
2. **Node.js queries Django** for contact → logs show service auth success
3. **Node.js sends message** → response received
4. **FastAPI logs analytics** (if analytics endpoint is called)

**What to Check:**
- No authentication errors in any service
- All cross-service calls succeed
- Tenant isolation maintained (each request processes only its tenant's data)

---

## Troubleshooting

### Issue 1: "Invalid service key" Error

**Symptoms:**
```json
{"error": "Invalid service key"}
```

**Possible Causes:**
1. Service key in .env doesn't match SERVICE_KEYS in middleware
2. .env file not loaded
3. Typo in service key

**Fix:**
```bash
# Check .env file exists
ls -la fastAPIWhatsapp_withclaude/.env
ls -la whatsapp_latest_final_withclaude/.env
ls -la whatsapp_bot_server_withclaude/.env

# Verify service keys match
grep "SERVICE_KEY" fastAPIWhatsapp_withclaude/.env
grep "SERVICE_KEY" whatsapp_latest_final_withclaude/.env
grep "SERVICE_KEY" whatsapp_bot_server_withclaude/.env

# Restart services after .env changes
```

---

### Issue 2: "Missing tenant_id" Error

**Symptoms:**
```json
{"error": "Missing tenant_id for service request"}
```

**Fix:**
Add `X-Tenant-Id` header to your request:
```bash
curl ... -H "X-Tenant-Id: ai"
```

---

### Issue 3: Services Can't Talk to Each Other

**Symptoms:**
- Connection refused
- Timeout errors
- 404 errors

**Check:**
1. All services are running
2. Service URLs in .env are correct:
   ```env
   DJANGO_URL=http://localhost:8000
   FASTAPI_URL=http://localhost:8001
   NODEJS_URL=http://localhost:3000
   ```
3. No firewall blocking localhost connections

---

### Issue 4: JWT Token Validation Fails

**Symptoms:**
```json
{"error": "Invalid token"}
```

**Possible Causes:**
1. JWT_SECRET different across services
2. Token expired
3. Token malformed

**Fix:**
```bash
# Verify JWT_SECRET is the same across all services
grep "JWT_SECRET" fastAPIWhatsapp_withclaude/.env
grep "JWT_SECRET" whatsapp_latest_final_withclaude/.env
grep "JWT_SECRET" whatsapp_bot_server_withclaude/.env

# All should show:
# JWT_SECRET=whatsapp-business-automation-jwt-secret-2026-change-in-production
```

---

## Success Criteria

✅ **Phase 1 Complete** when:
- Valid service key requests to Django return 200/404 (not 403)
- Invalid service keys return 403
- Django logs show "Service-authenticated request from nodejs"

✅ **Phase 2 Complete** when:
- FastAPI middleware enabled
- Valid service key requests to FastAPI return 200
- Invalid service keys return 403
- User JWT authentication still works (both Django and FastAPI)

✅ **Phase 3 Complete** when:
- Real WhatsApp webhook flow works end-to-end
- All cross-service calls succeed
- No authentication errors in any logs
- Tenant isolation maintained

---

## Next Steps After Testing

Once all tests pass:

### 1. Update Service Calls (Optional but Recommended)

Replace direct HTTP calls with `ServiceClient`:

**Before:**
```javascript
const response = await axios.get(`${DJANGO_URL}/contacts/`, {
  headers: { 'X-Tenant-Id': tenantId }
});
```

**After:**
```javascript
const { nodejsClient } = require('./services/serviceClient');
const contacts = await nodejsClient.get(
  `${process.env.DJANGO_URL}/contacts/`,
  tenantId
);
```

### 2. Production Configuration

Update .env files for production:

```env
# Production URLs
DJANGO_URL=https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net
FASTAPI_URL=https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net
NODEJS_URL=https://whatsappbotserver.azurewebsites.net

# Strong JWT secret
JWT_SECRET=<GENERATE-NEW-STRONG-SECRET-FOR-PRODUCTION>
```

### 3. Security Hardening

- [ ] Add rate limiting
- [ ] Set up monitoring for failed auth attempts
- [ ] Configure log aggregation
- [ ] Enable HTTPS only
- [ ] Add IP whitelisting (if needed)

---

## Testing Checklist

Copy this checklist and mark items as you test:

```
Phase 1: Service Authentication
[ ] Django service running (port 8000)
[ ] FastAPI service running (port 8001)
[ ] Node.js service running (port 3000)
[ ] Test 1: Valid service key to Django - PASS
[ ] Test 2: Invalid service key to Django - FAIL (expected)
[ ] Test 3: Missing tenant ID - ERROR (expected)

Phase 2: Enable JWT Middleware
[ ] FastAPI middleware enabled (line 146 uncommented)
[ ] FastAPI restarted
[ ] Test 5: Valid service key to FastAPI - PASS
[ ] Test 6: Invalid service key to FastAPI - FAIL (expected)
[ ] Test 7: User login successful - JWT received
[ ] Test 8: User request to Django with JWT - PASS
[ ] Test 9: User request to FastAPI with JWT - PASS

Phase 3: End-to-End
[ ] Real WhatsApp webhook flow works
[ ] All cross-service calls succeed
[ ] No authentication errors in logs
[ ] Tenant isolation verified
```

---

## Quick Reference

**Service Keys:**
```
DJANGO_SERVICE_KEY=sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc
FASTAPI_SERVICE_KEY=sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
```

**JWT Secret:**
```
JWT_SECRET=whatsapp-business-automation-jwt-secret-2026-change-in-production
```

**Service URLs (Development):**
```
DJANGO_URL=http://localhost:8000
FASTAPI_URL=http://localhost:8001
NODEJS_URL=http://localhost:3000
```

---

## Need Help?

If you encounter issues:

1. Check the logs - they contain detailed error messages
2. Review `IMPLEMENTATION_GUIDE_SERVICE_AUTH.md` - has troubleshooting section
3. Verify .env files have correct keys
4. Ensure all services can connect to databases
5. Test one service at a time

---

**Status**: Ready to begin Phase 1 testing! 🚀

Start with the curl commands in Step 1.2 and work through each phase systematically.
