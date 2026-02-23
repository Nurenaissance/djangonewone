# FastAPI 500 Error Fix - Azure Deployment

## Problem Identified
The FastAPI server was returning 500 Internal Server Error due to **wrong JWT library installed**.

### Root Cause
```
AttributeError: module 'jwt' has no attribute 'ExpiredSignatureError'
```

The `requirements.txt` had `jwt` instead of `PyJWT`. These are two different packages:
- ❌ `jwt` - Wrong library (was installed)
- ✅ `PyJWT` - Correct library (needed)

## Files Fixed

### 1. `fastAPIWhatsapp_withclaude/requirements.txt`
- Changed `jwt` → `PyJWT>=2.8.0`
- Added `python-dotenv>=1.0.0`

### 2. `fastAPIWhatsapp_withclaude/main.py`
- Fixed JWT exception imports to use `jwt.exceptions`
- Added fallback exception handling
- Added generic Exception catch for any JWT errors

## Deploy to Azure

### Option 1: Redeploy to Azure (Recommended)

1. **Commit the changes**:
   ```bash
   cd fastAPIWhatsapp_withclaude
   git add requirements.txt main.py
   git commit -m "Fix JWT library - replace jwt with PyJWT"
   git push
   ```

2. **Trigger Azure deployment**:
   - Azure will automatically detect the push and redeploy
   - OR manually trigger deployment in Azure Portal

3. **Wait for deployment** (2-5 minutes)

4. **Verify the fix**:
   ```bash
   curl https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/health
   ```

### Option 2: Manual Fix in Azure (If you can't redeploy)

1. **SSH into Azure App Service**:
   - Go to Azure Portal → Your App Service → SSH / Advanced Tools

2. **Uninstall wrong library**:
   ```bash
   pip uninstall jwt -y
   ```

3. **Install correct library**:
   ```bash
   pip install PyJWT>=2.8.0 python-dotenv
   ```

4. **Restart the app**:
   ```bash
   # In Azure Portal → Overview → Restart
   ```

## Required Environment Variables in Azure

Make sure these are set in **Azure Portal → Configuration → Application settings**:

```bash
JWT_SECRET_KEY=whatsapp-business-automation-jwt-secret-2026-change-in-production
DJANGO_SERVICE_KEY=sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc
FASTAPI_SERVICE_KEY=sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
DATABASE_URL=<your-postgres-connection-string>
```

## Verify the Fix

After deployment, test these endpoints:

```bash
# Health check (should return 200 OK)
curl https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/health

# Notifications endpoint (should return 401 Unauthorized, not 500)
curl https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/notifications
```

Expected results:
- ✅ Health endpoint: Returns `{"status": "FastApi Code is healthy", ...}`
- ✅ Notifications: Returns `401 Unauthorized` with JSON error (not 500)
- ✅ CORS errors should be gone

## Frontend Fix (If still seeing errors)

Your React frontend needs to send the JWT token:

```javascript
// In your axios calls, add:
headers: {
  'Authorization': `Bearer ${localStorage.getItem('token')}`,
  'X-Tenant-Id': tenantId
}
```

## Summary

The 500 errors were caused by:
1. ❌ Wrong JWT library (`jwt` instead of `PyJWT`)
2. ❌ Missing exception classes (`ExpiredSignatureError`, `InvalidTokenError`)

The fix:
1. ✅ Updated `requirements.txt` to use `PyJWT>=2.8.0`
2. ✅ Fixed exception imports in `main.py`
3. ✅ Added fallback error handling

Deploy the changes and the errors should be resolved!
