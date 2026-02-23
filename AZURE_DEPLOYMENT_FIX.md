# Azure Deployment Fix - Session Initialization Issue

## Problem Summary

The Node.js WhatsApp bot server was experiencing infinite recursion errors when trying to initialize sessions:

```
Session initialization failed: Session initialization failed: Session initialization failed: ...
Maximum call stack size exceeded
```

## Root Causes Identified

### 1. FastAPI Not Running on Azure ❌
**Issue**: The FastAPI deployment at `https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net` is showing Azure's default welcome page instead of the application.

**Evidence**:
- `curl https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/` returns Azure welcome HTML
- `/whatsapp_tenant` endpoint returns 404
- `/health` endpoint returns 404

**Impact**: All FastAPI requests from Node.js fail, falling back to Django.

### 2. Missing Service Authentication ❌
**Issue**: Node.js server was not sending `X-Service-Key` headers required by both FastAPI and Django.

**Evidence**:
- FastAPI main.py:158 requires `X-Service-Key` OR `Authorization: Bearer` token
- Django has similar authentication middleware
- Node.js misc.js:331,341 was only sending `bpid` header

**Impact**: Even if FastAPI was running, requests would be rejected with 401/403.

### 3. Infinite Recursion with No Safeguards ❌
**Issue**: When both backends failed, `getSession` would recursively call itself without limit.

**Evidence**:
- misc.js:469, 476, 488 had recursive `getSession` calls
- No retry counter or max attempts check
- Error message kept wrapping: "Session initialization failed: Session initialization failed: ..."

**Impact**: Node.js process crashes with stack overflow.

## Fixes Implemented ✅

### Fix 1: Added Recursion Limit Safeguard
**File**: `whatsapp_bot_server_withclaude/helpers/misc.js`

**Changes**:
```javascript
// BEFORE:
export async function getSession(business_phone_number_id, contact, skipAddContact = false) {

// AFTER:
export async function getSession(business_phone_number_id, contact, skipAddContact = false, retryCount = 0) {
    const MAX_RETRIES = 3;

    if (retryCount >= MAX_RETRIES) {
        throw new Error(`Session initialization failed after ${MAX_RETRIES} attempts. Please check backend connectivity and service authentication.`);
    }
```

**Impact**: Prevents stack overflow, provides clear error message after 3 attempts.

### Fix 2: Added Service Authentication Headers
**File**: `whatsapp_bot_server_withclaude/helpers/misc.js`

**Changes**:
```javascript
// Service authentication headers
const serviceHeaders = {
    'bpid': business_phone_number_id,
    'X-Service-Key': process.env.NODEJS_SERVICE_KEY || process.env.NODE_SERVICE_KEY
};

// FastAPI call
const response = await axios.get(`${fastURL}/whatsapp_tenant`, {
    headers: serviceHeaders,
    timeout: 10000
});

// Django call
const response = await axios.get(`${djangoURL}/whatsapp_tenant`, {
    headers: serviceHeaders,
    timeout: 10000
});
```

**Impact**: Requests will now include proper authentication.

### Fix 3: Updated Recursive Calls
**Files**: `whatsapp_bot_server_withclaude/helpers/misc.js` (lines 493, 500, 512)

**Changes**: All recursive `getSession` calls now pass `retryCount + 1`:
```javascript
return await getSession(business_phone_number_id, contact, skipAddContact, retryCount + 1);
```

### Fix 4: Added Service Auth to triggerFlowById
**File**: `whatsapp_bot_server_withclaude/helpers/misc.js:527-536`

**Changes**: Added service authentication to Django flow trigger calls.

### Fix 5: Updated Environment Configuration
**Files**:
- `.env` - Updated with new Azure URLs
- `.env.example` - Documented production Azure URLs

**Changes**:
```bash
DJANGO_URL=https://django-faecdbgwhgepemec.canadacentral-01.azurewebsites.net
FASTAPI_URL=https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
```

## FastAPI Deployment Troubleshooting

### Check 1: Verify Deployment Status

```bash
# Check if app is deployed
az webapp deployment source show \
  --name fastapiyes \
  --resource-group <your-resource-group>
```

### Check 2: Check Application Logs

```bash
# View live logs
az webapp log tail \
  --name fastapiyes \
  --resource-group <your-resource-group>

# Download logs
az webapp log download \
  --name fastapiyes \
  --resource-group <your-resource-group> \
  --log-file fastapi-logs.zip
```

### Check 3: Verify Startup Command

Azure App Service needs a startup command for FastAPI. Check in Azure Portal:
1. Go to: **fastapiyes** App Service
2. **Configuration** → **General settings** → **Startup Command**

Should be one of:
```bash
# Option 1: Gunicorn with Uvicorn workers (recommended for production)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000

# Option 2: Uvicorn directly (simpler, good for testing)
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Check 4: Verify requirements.txt

FastAPI deployment needs these dependencies:

```txt
fastapi
uvicorn[standard]
gunicorn
python-dotenv
sqlalchemy
psycopg2-binary
redis
aiohttp
python-jose[cryptography]
pyjwt
```

### Check 5: Set Environment Variables in Azure

Go to: **Configuration** → **Application settings** and add:

```bash
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
DJANGO_SERVICE_KEY=sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc
FASTAPI_SERVICE_KEY=sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k
JWT_SECRET_KEY=whatsapp-business-automation-jwt-secret-2026-change-in-production
DATABASE_URL=<your-database-connection-string>
REDIS_URL=<your-redis-connection-string>
```

### Check 6: Test Deployment

After fixing deployment, test with:

```bash
# Test health endpoint
curl https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/health

# Expected response:
# {"status": "FastApi Code is healthy", "thread_pool_status": "healthy", ...}

# Test whatsapp_tenant endpoint with auth
curl https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/whatsapp_tenant \
  -H "bpid: 241683569037594" \
  -H "X-Service-Key: sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34"

# Expected response: JSON with whatsapp_data, agents, triggers
```

## Quick Deployment Fix (If App Not Deployed)

If FastAPI hasn't been deployed yet:

```bash
# 1. Navigate to FastAPI directory
cd fastAPIWhatsapp_withclaude

# 2. Create .deployment file (if not exists)
cat > .deployment << 'EOF'
[config]
command = deploy.sh
EOF

# 3. Create deploy.sh (if not exists)
cat > deploy.sh << 'EOF'
#!/bin/bash
python -m pip install --upgrade pip
pip install -r requirements.txt
EOF

# 4. Deploy using Azure CLI
az webapp up \
  --name fastapiyes \
  --resource-group <your-resource-group> \
  --location canadacentral \
  --runtime "PYTHON:3.11" \
  --sku B1

# 5. Set startup command
az webapp config set \
  --name fastapiyes \
  --resource-group <your-resource-group> \
  --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000"

# 6. Add environment variables
az webapp config appsettings set \
  --name fastapiyes \
  --resource-group <your-resource-group> \
  --settings \
    NODEJS_SERVICE_KEY="sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34" \
    DJANGO_SERVICE_KEY="sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc" \
    FASTAPI_SERVICE_KEY="sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k" \
    JWT_SECRET_KEY="whatsapp-business-automation-jwt-secret-2026-change-in-production"

# 7. Restart the app
az webapp restart \
  --name fastapiyes \
  --resource-group <your-resource-group>
```

## Testing the Complete Fix

After deploying FastAPI and restarting Node.js:

```bash
# 1. Test Node.js server locally with deployed backends
cd whatsapp_bot_server_withclaude
npm start

# 2. Send a test webhook (use your test phone number ID)
# The session should now initialize successfully

# 3. Check logs for success messages:
# ✅ FastAPI tenant fetch successful
# OR
# ✅ Django tenant fetch successful
```

## Expected Behavior After Fix

1. **First Attempt**: Node.js tries FastAPI with service key
   - If FastAPI is running and auth is valid → Success ✅
   - If FastAPI fails → Continue to Django

2. **Second Attempt**: Node.js tries Django with service key
   - If Django is running and auth is valid → Success ✅
   - If Django fails → Error after 3 total retries

3. **Error Handling**: After 3 failed attempts
   - Clear error message: "Session initialization failed after 3 attempts..."
   - No stack overflow
   - Logs show which services failed and why

## Next Steps

1. **Deploy/Fix FastAPI** - Follow Check 1-6 above
2. **Restart Node.js server** - Kill and restart to load new code
3. **Test with webhook** - Send test message to verify session creation
4. **Monitor logs** - Watch for success messages in console

## Service Keys Reference

All services must have these same keys:

```bash
DJANGO_SERVICE_KEY=sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc
FASTAPI_SERVICE_KEY=sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
```

## Contact for Issues

If you encounter issues after implementing these fixes:
1. Check application logs in Azure Portal
2. Verify all service keys match across services
3. Test each endpoint individually with curl
4. Check network connectivity between services
