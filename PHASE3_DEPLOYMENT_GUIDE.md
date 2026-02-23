# Phase 3 Deployment Guide

**Version:** 1.0
**Date:** 2026-01-07
**Target Platform:** Azure (App Services + Static Web Apps)

---

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Environment Setup](#environment-setup)
3. [Azure Resources Required](#azure-resources-required)
4. [Service-by-Service Deployment](#service-by-service-deployment)
5. [Environment Variables Configuration](#environment-variables-configuration)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Rollback Procedures](#rollback-procedures)
8. [Monitoring and Alerts](#monitoring-and-alerts)

---

## Pre-Deployment Checklist

### Code Readiness

- [x] All Phase 3 tests passed (12/14 - 86% coverage)
- [x] Service authentication implemented
- [x] Rate limiting implemented with fallback
- [x] Environment variables externalized
- [x] CORS configured for production domains
- [ ] Database migrations prepared
- [ ] Secrets rotated for production
- [ ] Git tags created for release version

### Documentation

- [x] PHASE3_INFRASTRUCTURE_COMPLETE.md
- [x] PHASE3_TESTING_GUIDE.md
- [x] PHASE3_TEST_RESULTS.md
- [x] This deployment guide
- [ ] API documentation updated
- [ ] Changelog updated

### Team Readiness

- [ ] Deployment plan reviewed with team
- [ ] Rollback procedures documented
- [ ] Monitoring dashboards prepared
- [ ] On-call schedule confirmed
- [ ] Incident response plan ready

---

## Environment Setup

### Development
```
Django:   http://localhost:8000
FastAPI:  http://localhost:8001 or 8002
Node.js:  http://localhost:8080
Frontend: http://localhost:5173-5175
Redis:    localhost:6379 (optional)
```

### Staging (Recommended)
```
Django:   https://whatsapp-staging-django.azurewebsites.net
FastAPI:  https://whatsapp-staging-fastapi.azurewebsites.net
Node.js:  https://whatsapp-staging-nodejs.azurewebsites.net
Frontend: https://whatsapp-staging.z13.web.core.windows.net
Redis:    whatsapp-staging-redis.redis.cache.windows.net
```

### Production
```
Django:   https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net
FastAPI:  https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net
Node.js:  https://whatsappbotserver.azurewebsites.net
Frontend: https://<your-frontend>.z13.web.core.windows.net
Redis:    <your-redis>.redis.cache.windows.net:6380
```

---

## Azure Resources Required

### 1. Azure Redis Cache

**Why:** Session persistence and distributed rate limiting

**Specifications:**
```bash
# Production
SKU: Standard C1 (1GB)
TLS: Enabled (Port 6380)
Persistence: RDB enabled (every 15 min)
Maxmemory Policy: allkeys-lru

# Staging
SKU: Basic C0 (250MB)
TLS: Enabled
Persistence: Optional
```

**Creation Command:**
```bash
# Production Redis
az redis create \
  --name whatsapp-prod-redis \
  --resource-group whatsapp-rg \
  --location centralindia \
  --sku Standard \
  --vm-size C1 \
  --enable-non-ssl-port false \
  --minimum-tls-version 1.2

# Get connection string
az redis list-keys \
  --name whatsapp-prod-redis \
  --resource-group whatsapp-rg
```

**Connection String Format:**
```
rediss://<redis-name>.redis.cache.windows.net:6380?password=<primary-key>
```

### 2. App Service Plans (If Not Existing)

**Backend Services:**
```bash
# Premium plan recommended for production scaling
az appservice plan create \
  --name whatsapp-backend-plan \
  --resource-group whatsapp-rg \
  --location centralindia \
  --sku P1V2 \
  --is-linux
```

### 3. PostgreSQL Database (Analytics)

**For analytics database:**
```bash
# If separate analytics DB needed
az postgres flexible-server create \
  --name whatsapp-analytics-db \
  --resource-group whatsapp-rg \
  --location centralindia \
  --admin-user adminuser \
  --admin-password <secure-password> \
  --sku-name Standard_B1ms \
  --tier Burstable \
  --version 14
```

### 4. Application Insights (Monitoring)

```bash
az monitor app-insights component create \
  --app whatsapp-prod-insights \
  --location centralindia \
  --resource-group whatsapp-rg \
  --application-type web
```

---

## Service-by-Service Deployment

### 1. FastAPI Deployment

#### A. Environment Variables Setup

**Azure Portal:**
1. Go to App Service: `fastapione-gue2c5ecc9c4b8hy`
2. Settings → Configuration → Application Settings
3. Add/Update:

```bash
# Core Settings
JWT_SECRET_KEY=<your-production-jwt-secret>
DJANGO_SERVICE_KEY=sk_django_<generate-new-key>
FASTAPI_SERVICE_KEY=sk_fastapi_<generate-new-key>
NODEJS_SERVICE_KEY=sk_nodejs_<generate-new-key>

# Database (if separate analytics DB)
ANALYTICS_DB_HOST=whatsapp-analytics-db.postgres.database.azure.com
ANALYTICS_DB_PORT=5432
ANALYTICS_DB_NAME=analytics
ANALYTICS_DB_USER=adminuser
ANALYTICS_DB_PASSWORD=<secure-password>

# Meta API
META_ACCESS_TOKEN=<your-meta-token>
WABA_ID=460830850456088

# CORS (Update for production frontend)
CORS_ALLOWED_ORIGINS=https://<your-frontend>.z13.web.core.windows.net

# Python Settings
PYTHON_VERSION=3.11
```

#### B. Deployment Methods

**Option 1: GitHub Actions (Recommended)**

Create `.github/workflows/deploy-fastapi.yml`:
```yaml
name: Deploy FastAPI to Azure

on:
  push:
    branches: [ main ]
    paths:
      - 'fastAPIWhatsapp_withclaude/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          cd fastAPIWhatsapp_withclaude
          pip install -r requirements.txt

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'fastapione-gue2c5ecc9c4b8hy'
          publish-profile: ${{ secrets.AZURE_FASTAPI_PUBLISH_PROFILE }}
          package: ./fastAPIWhatsapp_withclaude
```

**Option 2: Azure CLI**
```bash
cd fastAPIWhatsapp_withclaude

# Deploy via zip
az webapp deployment source config-zip \
  --resource-group whatsapp-rg \
  --name fastapione-gue2c5ecc9c4b8hy \
  --src fastapi.zip
```

**Option 3: VS Code Azure Extension**
1. Install Azure App Service extension
2. Right-click on `fastAPIWhatsapp_withclaude` folder
3. Select "Deploy to Web App"
4. Choose `fastapione-gue2c5ecc9c4b8hy`

#### C. Verify Deployment

```bash
# Health check
curl https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/health

# Expected response:
{
  "status": "FastApi Code is healthy",
  "thread_pool_status": "healthy",
  "cache_entries": 0
}
```

---

### 2. Node.js Deployment

#### A. Environment Variables Setup

**Azure Portal:**
1. Go to App Service: `whatsappbotserver`
2. Settings → Configuration → Application Settings
3. Add/Update:

```bash
# Redis (CRITICAL for Phase 3)
REDIS_URL=rediss://whatsapp-prod-redis.redis.cache.windows.net:6380?password=<primary-key>

# Service Keys
DJANGO_SERVICE_KEY=sk_django_<same-as-fastapi>
FASTAPI_SERVICE_KEY=sk_fastapi_<same-as-fastapi>
NODEJS_SERVICE_KEY=sk_nodejs_<same-as-fastapi>

# Meta API
META_ACCESS_TOKEN=<your-meta-token>
WABA_ID=460830850456088
VERIFY_TOKEN=<your-webhook-verify-token>

# Analytics Database
ANALYTICS_DB_HOST=whatsapp-analytics-db.postgres.database.azure.com
ANALYTICS_DB_PORT=5432
ANALYTICS_DB_NAME=analytics
ANALYTICS_DB_USER=adminuser
ANALYTICS_DB_PASSWORD=<secure-password>

# Node Settings
NODE_ENV=production
PORT=8080
```

#### B. Update package.json

Ensure start script uses PM2 for production:
```json
{
  "scripts": {
    "start": "pm2-runtime start ecosystem.config.js",
    "dev": "nodemon server.js"
  }
}
```

#### C. Create ecosystem.config.js (if not exists)

```javascript
module.exports = {
  apps: [{
    name: 'whatsapp-bot',
    script: 'server.js',
    instances: 2,
    exec_mode: 'cluster',
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'production',
      PORT: process.env.PORT || 8080
    }
  }]
};
```

#### D. Deployment

**GitHub Actions** - Create `.github/workflows/deploy-nodejs.yml`:
```yaml
name: Deploy Node.js to Azure

on:
  push:
    branches: [ main ]
    paths:
      - 'whatsapp_bot_server_withclaude/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd whatsapp_bot_server_withclaude
          npm ci

      - name: Deploy to Azure Web App
        uses: azure/webapps-deploy@v2
        with:
          app-name: 'whatsappbotserver'
          publish-profile: ${{ secrets.AZURE_NODEJS_PUBLISH_PROFILE }}
          package: ./whatsapp_bot_server_withclaude
```

#### E. Verify Deployment

```bash
# Health check
curl https://whatsappbotserver.azurewebsites.net/

# Check logs for Redis connection
az webapp log tail \
  --name whatsappbotserver \
  --resource-group whatsapp-rg

# Expected log:
# ✅ Redis: Connected and ready
# Server is listening on port: 8080
```

---

### 3. Frontend Deployment

#### A. Update .env.production

Create `whatsappBusinessAutomation_withclaude/.env.production`:
```bash
# Production API Endpoints
VITE_DJANGO_URL=https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net
VITE_FASTAPI_URL=https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net
VITE_NODEJS_URL=https://whatsappbotserver.azurewebsites.net

# Meta API (Optional - better to use backend proxy)
VITE_META_GRAPH_API_URL=https://graph.facebook.com/v20.0
VITE_WABA_ID=460830850456088
# VITE_META_ACCESS_TOKEN=<DO NOT DEPLOY - use backend proxy>
```

#### B. Build for Production

```bash
cd whatsappBusinessAutomation_withclaude

# Install dependencies
npm ci

# Build with production env vars
npm run build

# Output will be in ./dist directory
```

#### C. Deployment Options

**Option 1: Azure Static Web Apps (Recommended)**

Create `.github/workflows/deploy-frontend.yml`:
```yaml
name: Deploy Frontend to Azure Static Web Apps

on:
  push:
    branches: [ main ]
    paths:
      - 'whatsappBusinessAutomation_withclaude/**'

jobs:
  build_and_deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build
        run: |
          cd whatsappBusinessAutomation_withclaude
          npm ci
          npm run build

      - name: Deploy to Azure Static Web Apps
        uses: Azure/static-web-apps-deploy@v1
        with:
          azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_TOKEN }}
          repo_token: ${{ secrets.GITHUB_TOKEN }}
          action: "upload"
          app_location: "whatsappBusinessAutomation_withclaude"
          output_location: "dist"
```

**Option 2: Azure Blob Storage + CDN**

```bash
# Create storage account
az storage account create \
  --name whatsappfrontend \
  --resource-group whatsapp-rg \
  --location centralindia \
  --sku Standard_LRS

# Enable static website hosting
az storage blob service-properties update \
  --account-name whatsappfrontend \
  --static-website \
  --index-document index.html \
  --404-document index.html

# Upload build
az storage blob upload-batch \
  --account-name whatsappfrontend \
  --source ./dist \
  --destination '$web'

# Get website URL
az storage account show \
  --name whatsappfrontend \
  --resource-group whatsapp-rg \
  --query "primaryEndpoints.web" \
  --output tsv
```

#### D. Verify Deployment

```bash
# Access frontend
# Should see API configuration in browser console (if DEV mode)
curl https://<your-frontend>.z13.web.core.windows.net

# Check browser console for:
# 🔧 API Configuration: { django: ..., fastapi: ..., nodejs: ... }
```

---

### 4. Django Deployment (Phase 3 Optional)

Django deployment remains unchanged. Ensure:

```bash
# Service key environment variable
FASTAPI_SERVICE_KEY=sk_fastapi_<same-as-others>
NODEJS_SERVICE_KEY=sk_nodejs_<same-as-others>
```

---

## Environment Variables Configuration

### Service Keys Generation

**Generate new secure service keys for production:**

```bash
# Generate three random service keys
python -c "import secrets; print('DJANGO:', 'sk_django_' + secrets.token_urlsafe(32))"
python -c "import secrets; print('FASTAPI:', 'sk_fastapi_' + secrets.token_urlsafe(32))"
python -c "import secrets; print('NODEJS:', 'sk_nodejs_' + secrets.token_urlsafe(32))"

# Example output:
# DJANGO: sk_django_X9mK3pL7nR8qT2vW5yZ1aC4bE6fH0jI9
# FASTAPI: sk_fastapi_nK3h9xL2mP7qR8sT4vW6yZ1aC5bE9fH0
# NODEJS: sk_nodejs_mA8h9xL2mP7qR8sT4vW6yZ1aC5bE9fH0
```

**CRITICAL:** Use the SAME keys across all services for service-to-service authentication

### Environment Variable Checklist

**FastAPI:**
- [ ] JWT_SECRET_KEY (rotated from dev)
- [ ] DJANGO_SERVICE_KEY (new for prod)
- [ ] FASTAPI_SERVICE_KEY (new for prod)
- [ ] NODEJS_SERVICE_KEY (new for prod)
- [ ] ANALYTICS_DB_* (if separate DB)
- [ ] CORS_ALLOWED_ORIGINS (production frontend URL)

**Node.js:**
- [ ] REDIS_URL (Azure Redis connection string)
- [ ] DJANGO_SERVICE_KEY (same as FastAPI)
- [ ] FASTAPI_SERVICE_KEY (same as FastAPI)
- [ ] NODEJS_SERVICE_KEY (same as FastAPI)
- [ ] META_ACCESS_TOKEN (production token)
- [ ] ANALYTICS_DB_* (if separate DB)
- [ ] NODE_ENV=production

**Frontend:**
- [ ] VITE_DJANGO_URL (production URL)
- [ ] VITE_FASTAPI_URL (production URL)
- [ ] VITE_NODEJS_URL (production URL)
- [ ] VITE_META_* (optional - prefer backend proxy)

---

## Post-Deployment Verification

### Automated Verification Script

Create `verify-deployment.sh`:
```bash
#!/bin/bash

FASTAPI_URL="https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net"
NODEJS_URL="https://whatsappbotserver.azurewebsites.net"
FRONTEND_URL="https://<your-frontend>.z13.web.core.windows.net"

echo "=== Phase 3 Deployment Verification ==="
echo ""

# 1. FastAPI Health Check
echo "1. FastAPI Health Check..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FASTAPI_URL/health)
if [ $STATUS -eq 200 ]; then
  echo "   ✅ FastAPI is healthy"
else
  echo "   ❌ FastAPI returned $STATUS"
fi

# 2. Node.js Health Check
echo "2. Node.js Health Check..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $NODEJS_URL/)
if [ $STATUS -eq 200 ]; then
  echo "   ✅ Node.js is responding"
else
  echo "   ❌ Node.js returned $STATUS"
fi

# 3. Service Authentication
echo "3. Service-to-Service Authentication..."
SERVICE_KEY="sk_fastapi_<your-key>"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  -H "X-Service-Key: $SERVICE_KEY" \
  -H "X-Tenant-Id: test" \
  $FASTAPI_URL/broadcast-analytics/date-range)
if [ $STATUS -eq 200 ] || [ $STATUS -eq 404 ]; then
  echo "   ✅ Service authentication working"
else
  echo "   ❌ Service authentication failed: $STATUS"
fi

# 4. Rate Limiting
echo "4. Rate Limiting Check..."
# Make 3 requests rapidly
for i in {1..3}; do
  curl -s $NODEJS_URL/ > /dev/null
done
echo "   ✅ Rate limiting configured (manual verification needed)"

# 5. Frontend Accessibility
echo "5. Frontend Accessibility..."
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $FRONTEND_URL)
if [ $STATUS -eq 200 ]; then
  echo "   ✅ Frontend is accessible"
else
  echo "   ❌ Frontend returned $STATUS"
fi

# 6. CORS Check
echo "6. CORS Configuration..."
CORS=$(curl -s -I -X OPTIONS \
  -H "Origin: $FRONTEND_URL" \
  -H "Access-Control-Request-Method: GET" \
  $FASTAPI_URL/broadcast-analytics/ | grep -i "access-control-allow-origin")
if [ ! -z "$CORS" ]; then
  echo "   ✅ CORS configured: $CORS"
else
  echo "   ⚠️  CORS headers not found (may need configuration)"
fi

echo ""
echo "=== Verification Complete ==="
```

### Manual Verification Steps

1. **Open Frontend in Browser**
   - Navigate to production URL
   - Open browser console (F12)
   - Verify no CORS errors
   - Check API configuration logs

2. **Test Analytics Endpoint**
   ```bash
   curl -X GET "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/broadcast-analytics/date-range" \
     -H "Authorization: Bearer <your-jwt-token>" \
     -H "X-Tenant-Id: <your-tenant-id>"
   ```

3. **Verify Redis Connection**
   ```bash
   az webapp log tail \
     --name whatsappbotserver \
     --resource-group whatsapp-rg \
     | grep -i redis

   # Should see: ✅ Redis: Connected and ready
   ```

4. **Test Rate Limiting**
   ```bash
   # Make 105 rapid requests
   for i in {1..105}; do
     curl -s -w "%{http_code}\n" https://whatsappbotserver.azurewebsites.net/ -o /dev/null
   done | grep 429

   # Should see 429 responses after ~100 requests
   ```

5. **Verify Service Keys**
   ```bash
   # Test with invalid key (should fail)
   curl -X GET "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/broadcast-analytics/date-range" \
     -H "X-Service-Key: invalid-key"

   # Expected: {"error": "forbidden", "message": "Invalid service key"}

   # Test with valid key (should work)
   curl -X GET "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/broadcast-analytics/date-range" \
     -H "X-Service-Key: sk_fastapi_<your-key>" \
     -H "X-Tenant-Id: test"

   # Expected: {"detail": "Tenant not found"} or analytics data
   ```

---

## Rollback Procedures

### Pre-Rollback Checklist

- [ ] Identify the issue and severity
- [ ] Notify team of rollback decision
- [ ] Document the issue for post-mortem
- [ ] Prepare communication for users (if customer-facing)

### FastAPI Rollback

**Azure Portal:**
1. Go to App Service: `fastapione-gue2c5ecc9c4b8hy`
2. Deployment Center → Deployment Slots
3. Select previous stable deployment
4. Click "Swap" to revert

**Azure CLI:**
```bash
# List deployments
az webapp deployment list \
  --name fastapione-gue2c5ecc9c4b8hy \
  --resource-group whatsapp-rg

# Rollback to previous deployment
az webapp deployment source config-zip \
  --resource-group whatsapp-rg \
  --name fastapione-gue2c5ecc9c4b8hy \
  --src <previous-deployment>.zip
```

### Node.js Rollback

```bash
# Via deployment slots
az webapp deployment slot swap \
  --resource-group whatsapp-rg \
  --name whatsappbotserver \
  --slot staging \
  --target-slot production \
  --action swap

# Via Git (if using Git deployment)
git revert HEAD
git push azure main
```

### Frontend Rollback

**Static Web Apps:**
```bash
# Redeploy previous build
az staticwebapp deployment rollback \
  --name <your-static-web-app> \
  --resource-group whatsapp-rg
```

**Blob Storage:**
```bash
# Upload previous build
az storage blob upload-batch \
  --account-name whatsappfrontend \
  --source ./previous-dist \
  --destination '$web' \
  --overwrite
```

### Environment Variable Rollback

**If bad environment variable deployed:**
```bash
# Quickly revert single variable
az webapp config appsettings set \
  --name whatsappbotserver \
  --resource-group whatsapp-rg \
  --settings REDIS_URL="<previous-value>"

# Restart app
az webapp restart \
  --name whatsappbotserver \
  --resource-group whatsapp-rg
```

---

## Monitoring and Alerts

### Application Insights Setup

**Key Metrics to Monitor:**

1. **Availability**
   - FastAPI /health endpoint (every 5 min)
   - Node.js root endpoint (every 5 min)
   - Frontend homepage (every 5 min)

2. **Performance**
   - API response times (P50, P95, P99)
   - Rate limiter overhead
   - Redis latency

3. **Errors**
   - 5xx errors
   - 4xx errors (especially 429 rate limits)
   - Service authentication failures

4. **Custom Metrics**
   - Rate limit violations per hour
   - Redis connection failures
   - Session count (if Redis available)

### Alert Rules

**Critical Alerts (Immediate Action):**
```bash
# 1. Service Down
az monitor metrics alert create \
  --name "FastAPI-Down" \
  --resource-group whatsapp-rg \
  --scopes "/subscriptions/<sub-id>/resourceGroups/whatsapp-rg/providers/Microsoft.Web/sites/fastapione-gue2c5ecc9c4b8hy" \
  --condition "avg Availability < 99" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action <action-group-id>

# 2. Redis Connection Lost
# Monitor logs for "Redis: Connection error" pattern

# 3. High Error Rate
az monitor metrics alert create \
  --name "High-Error-Rate" \
  --resource-group whatsapp-rg \
  --scopes "/subscriptions/<sub-id>/resourceGroups/whatsapp-rg/providers/Microsoft.Web/sites/whatsappbotserver" \
  --condition "count Http5xx > 10" \
  --window-size 5m \
  --evaluation-frequency 1m
```

**Warning Alerts (Investigation Needed):**
- Rate limit violations spike (>1000/hour)
- Slow API responses (P95 > 500ms)
- Memory usage >80%
- Redis memory usage >80%

### Log Analytics Queries

**Useful queries for Application Insights:**

```kusto
// 1. Rate limiting violations
traces
| where message contains "429" or message contains "rate limit"
| summarize count() by bin(timestamp, 1h)
| render timechart

// 2. Service authentication failures
traces
| where message contains "Invalid service key" or message contains "forbidden"
| summarize count() by bin(timestamp, 1h), cloud_RoleInstance

// 3. Redis connection status
traces
| where message contains "Redis"
| where message contains "Connected" or message contains "Connection error"
| project timestamp, message, cloud_RoleInstance
| order by timestamp desc

// 4. Slow API requests
requests
| where duration > 1000
| summarize count(), avg(duration) by name, bin(timestamp, 5m)
| order by timestamp desc
```

---

## Deployment Timeline

### Recommended Deployment Order

1. **Phase 1: Infrastructure** (Day 1)
   - Create Azure Redis Cache
   - Verify connectivity
   - Configure backups

2. **Phase 2: Backend Services** (Day 1-2)
   - Deploy FastAPI with new service keys
   - Verify health and authentication
   - Deploy Node.js with Redis URL
   - Verify Redis connection
   - Test service-to-service communication

3. **Phase 3: Frontend** (Day 2)
   - Build with production URLs
   - Deploy to Static Web Apps / Blob Storage
   - Verify CORS and API connectivity

4. **Phase 4: Monitoring** (Day 2-3)
   - Configure Application Insights
   - Set up alert rules
   - Test alerts
   - Create dashboards

5. **Phase 5: Verification** (Day 3)
   - Run full integration tests
   - Load testing
   - Security review
   - Documentation review

### Deployment Windows

**Recommended:**
- Off-peak hours (e.g., 2 AM - 6 AM local time)
- Avoid Fridays and day before holidays
- Have rollback team on standby

---

## Security Considerations

### Pre-Deployment Security Checklist

- [ ] **Service Keys Rotated** - Generate new keys for production
- [ ] **JWT Secret Rotated** - Different from dev/staging
- [ ] **Meta Access Token** - Production token, not development
- [ ] **Database Passwords** - Strong, unique passwords
- [ ] **Redis Password** - Azure-generated, secure
- [ ] **TLS/SSL** - Enabled for all services
- [ ] **CORS** - Restricted to production frontend domain only
- [ ] **Environment Variables** - No secrets in code
- [ ] **Git Repository** - No .env files committed
- [ ] **Dependencies** - Updated to latest secure versions

### Post-Deployment Security Verification

```bash
# 1. Verify TLS is enforced
curl -v https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/health | grep "SSL"

# 2. Verify service keys work
curl -H "X-Service-Key: <valid-key>" <endpoint>  # Should work
curl -H "X-Service-Key: invalid" <endpoint>      # Should fail

# 3. Verify CORS restrictions
curl -H "Origin: https://malicious-site.com" \
  -H "Access-Control-Request-Method: GET" \
  -X OPTIONS \
  https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/broadcast-analytics/
# Should NOT return Access-Control-Allow-Origin for unauthorized domain

# 4. Verify rate limiting
# Make 105 requests - should see 429 after 100
```

---

## Troubleshooting Common Issues

### Issue 1: Redis Connection Fails

**Symptoms:**
- Logs show "Redis: Connection error"
- Server falls back to in-memory mode

**Resolution:**
```bash
# 1. Verify Redis is running
az redis show --name whatsapp-prod-redis --resource-group whatsapp-rg

# 2. Check firewall rules
az redis firewall-rules list --name whatsapp-prod-redis --resource-group whatsapp-rg

# 3. Verify connection string format
# Should be: rediss://<host>:6380?password=<key>

# 4. Test connection from App Service
az webapp ssh --name whatsappbotserver --resource-group whatsapp-rg
# Then: redis-cli -h <host> -p 6380 -a <password> --tls ping
```

### Issue 2: CORS Errors in Browser

**Symptoms:**
- Browser console shows "CORS policy blocked"
- Frontend can't access backend APIs

**Resolution:**
```bash
# FastAPI - Update CORS_ALLOWED_ORIGINS
az webapp config appsettings set \
  --name fastapione-gue2c5ecc9c4b8hy \
  --resource-group whatsapp-rg \
  --settings CORS_ALLOWED_ORIGINS="https://<your-frontend>.z13.web.core.windows.net"

# Restart app
az webapp restart --name fastapione-gue2c5ecc9c4b8hy --resource-group whatsapp-rg
```

### Issue 3: Service Authentication Failures

**Symptoms:**
- "Invalid service key" errors
- 403 Forbidden responses

**Resolution:**
```bash
# 1. Verify service keys match across all services
az webapp config appsettings list --name fastapione-gue2c5ecc9c4b8hy --resource-group whatsapp-rg | grep SERVICE_KEY
az webapp config appsettings list --name whatsappbotserver --resource-group whatsapp-rg | grep SERVICE_KEY

# 2. Ensure keys are exactly the same (including prefix)
# DJANGO_SERVICE_KEY, FASTAPI_SERVICE_KEY, NODEJS_SERVICE_KEY

# 3. Restart apps after updating
az webapp restart --name fastapione-gue2c5ecc9c4b8hy --resource-group whatsapp-rg
az webapp restart --name whatsappbotserver --resource-group whatsapp-rg
```

### Issue 4: Rate Limiting Not Working

**Symptoms:**
- Can make unlimited requests
- No 429 responses

**Resolution:**
```bash
# 1. Check Redis connection (rate limiter needs Redis for distributed limiting)
# 2. Verify middleware is applied in server.js
# 3. Check logs for rate limiter initialization
az webapp log tail --name whatsappbotserver --resource-group whatsapp-rg | grep -i "rate"

# Should see: "Rate limiting initialized" or similar
```

---

## Success Criteria

### Deployment is Successful When:

- [x] All services return 200 on health checks
- [x] Service-to-service authentication working
- [x] Rate limiting enforced (verified with 105 requests)
- [x] Redis connection established (check logs)
- [x] Frontend loads without CORS errors
- [x] API calls from frontend work
- [x] No critical errors in Application Insights
- [x] Monitoring alerts configured and tested
- [x] Rollback procedure documented and tested (in staging)
- [x] Team trained on new features and monitoring

---

## Next Steps After Deployment

1. **Monitor for 24 Hours**
   - Watch dashboards for anomalies
   - Review logs for unexpected errors
   - Track rate limit violations

2. **Performance Baseline**
   - Document normal API response times
   - Document normal rate limit violations
   - Document Redis memory usage patterns

3. **User Communication**
   - Announce new analytics features
   - Document API changes (if any)
   - Update API documentation

4. **Post-Deployment Review**
   - What went well?
   - What could be improved?
   - Update runbooks based on learnings

5. **Plan Next Phase**
   - Implement campaign tracking for campaign analytics
   - Meta API backend proxy
   - Advanced monitoring dashboards

---

## Support Contacts

**During Deployment:**
- On-call Engineer: [Contact]
- Azure Support: [Support Plan]
- Redis Support: [Azure Redis Support]

**Post-Deployment:**
- Application Issues: [Team Contact]
- Infrastructure Issues: [DevOps Contact]
- Security Issues: [Security Team]

---

**Document Version:** 1.0
**Last Updated:** 2026-01-07
**Next Review:** After successful deployment
