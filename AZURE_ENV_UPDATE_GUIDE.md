# Azure Environment Variables Update Guide

## ⚠️ CRITICAL ISSUE FOUND
Django backend is returning 500 errors because **AI_API_KEY is missing** from Azure environment variables!

Error from Azure logs:
```
ProviderError: The api_key client option must be set either by passing api_key to the client or by setting the AI_API_KEY environment variable
```

This happens in `/node_temps/views.py` line 126 where AI provider client is initialized at module import time.

## Quick Fix: Update Azure App Service Environment Variables

### For Django Backend (django-faecdbgwhgepemec.canadacentral-01.azurewebsites.net)

1. **Go to Azure Portal** → App Services → `django-faecdbgwhgepemec`

2. **Navigate to**: Configuration → Application Settings

3. **Add/Update these environment variables** (CRITICAL - MUST HAVE):

```bash
# ⚠️ MOST CRITICAL - Without this, Django won't even start!
AI_API_KEY=sk-cm8m6Rq-m4CjagBssykBM7QjXuc-oYxhLOc1Gz3nFnT3BlbkFJNVYczQDlGxipQYe6sXE927pH-zugcBFZxa-4lHmkgA

# Database Configuration
DB_NAME=nurenpostgres_Whatsapp
DB_USER=nurenai
DB_PASSWORD=Biz1nurenWar*
DB_HOST=nurenaistore.postgres.database.azure.com
DB_PORT=5432
DB_SSL_MODE=require

# Analytics Database (same as main for now)
ANALYTICS_DB_NAME=nurenpostgres_Whatsapp
ANALYTICS_DB_USER=nurenai
ANALYTICS_DB_PASSWORD=Biz1nurenWar*
ANALYTICS_DB_HOST=nurenaistore.postgres.database.azure.com
ANALYTICS_DB_PORT=5432

# Azure Redis Configuration
AZURE_REDIS_HOST=whatsappnuren.redis.cache.windows.net
AZURE_REDIS_PORT=6379
AZURE_REDIS_PASSWORD=O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM=

# JWT Configuration
JWT_SECRET=whatsapp-business-automation-jwt-secret-2026-change-in-production
JWT_ALGORITHM=HS256

# Service Keys
DJANGO_SERVICE_KEY=sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc
FASTAPI_SERVICE_KEY=sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
```

4. **Click "Save"** at the top

5. **Restart the App Service** (it will auto-restart after saving, but you can manually restart to be sure)

### For Node.js Bot Server (if deployed on Azure)

If your Node.js server is also deployed on Azure, update its environment variables similarly:

```bash
# Analytics Database
ANALYTICS_DB_HOST=nurenaistore.postgres.database.azure.com
ANALYTICS_DB_PORT=5432
ANALYTICS_DB_NAME=nurenpostgres_Whatsapp
ANALYTICS_DB_USER=nurenai
ANALYTICS_DB_PASSWORD=Biz1nurenWar*

# Main Database
DB_HOST=nurenaistore.postgres.database.azure.com
DB_PORT=5432
DB_NAME=nurenpostgres_Whatsapp
DB_USER=nurenai
DB_PASSWORD=Biz1nurenWar*

# Redis
REDIS_URL=redis://whatsappnuren.redis.cache.windows.net:6379
REDIS_PASSWORD=O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM=
```

## Using Azure CLI (Alternative Method)

If you prefer command line:

```bash
# Login to Azure
az login

# Set environment variables for Django
az webapp config appsettings set --name django-faecdbgwhgepemec --resource-group YourResourceGroup --settings \
  DB_NAME=nurenpostgres_Whatsapp \
  DB_USER=nurenai \
  DB_PASSWORD=Biz1nurenWar* \
  DB_HOST=nurenaistore.postgres.database.azure.com \
  DB_PORT=5432 \
  ANALYTICS_DB_NAME=nurenpostgres_Whatsapp \
  ANALYTICS_DB_USER=nurenai \
  ANALYTICS_DB_PASSWORD=Biz1nurenWar* \
  ANALYTICS_DB_HOST=nurenaistore.postgres.database.azure.com \
  ANALYTICS_DB_PORT=5432 \
  AZURE_REDIS_HOST=whatsappnuren.redis.cache.windows.net \
  AZURE_REDIS_PORT=6379 \
  AZURE_REDIS_PASSWORD=O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM=

# Restart the app
az webapp restart --name django-faecdbgwhgepemec --resource-group YourResourceGroup
```

## What This Fixes

- ✅ Analytics database connection errors
- ✅ Django 500 errors when Node.js calls Django endpoints
- ✅ Redis connection issues for Celery
- ✅ Service-to-service authentication

## Testing After Update

1. Wait 1-2 minutes for the app to fully restart
2. Check logs in Azure Portal → App Service → Log Stream
3. Test the endpoint that was failing:
   ```bash
   curl https://django-faecdbgwhgepemec.canadacentral-01.azurewebsites.net/health
   ```

## Do You Need to Redeploy Code?

**NO** - You only need to update environment variables. The code itself hasn't changed, only the configuration.

Only redeploy if:
- You make code changes to the Django or Node.js applications
- The environment variable update doesn't fix the issue (unlikely)

## Connection String Format

The analytics db.js file will automatically use these variables:
- Primary: `ANALYTICS_DB_HOST`, `ANALYTICS_DB_USER`, `ANALYTICS_DB_PASSWORD`
- Fallback: `DB_HOST`, `DB_USER`, `DB_PASSWORD`

So as long as either set is configured, it will work.
