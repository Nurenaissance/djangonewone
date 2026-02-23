# GitHub Actions CI/CD Workflows

This directory contains automated deployment workflows for the WhatsApp Business Automation platform.

## Workflows

### 1. `deploy-fastapi.yml`
**Deploys:** FastAPI backend to Azure App Service
**Triggers:** Push to `main` branch (when `fastAPIWhatsapp_withclaude/**` changes)
**Target:** `fastapione-gue2c5ecc9c4b8hy.azurewebsites.net`

### 2. `deploy-nodejs.yml`
**Deploys:** Node.js bot server to Azure App Service
**Triggers:** Push to `main` branch (when `whatsapp_bot_server_withclaude/**` changes)
**Target:** `whatsappbotserver.azurewebsites.net`

### 3. `deploy-frontend.yml`
**Deploys:** React frontend to Azure Static Web Apps
**Triggers:** Push to `main` branch (when `whatsappBusinessAutomation_withclaude/**` changes)
**Target:** Azure Static Web App (configured separately)

---

## Setup Instructions

### Prerequisites

1. **Azure Resources Created:**
   - FastAPI App Service
   - Node.js App Service
   - Azure Static Web App (for frontend)
   - Azure Redis Cache (for Node.js sessions)

2. **GitHub Repository:**
   - Code pushed to GitHub
   - Admin access to repository settings

### Step 1: Get Azure Publish Profiles

#### For FastAPI App Service:
```bash
az webapp deployment list-publishing-profiles \
  --name fastapione-gue2c5ecc9c4b8hy \
  --resource-group whatsapp-rg \
  --xml
```

**OR** via Azure Portal:
1. Go to App Service: `fastapione-gue2c5ecc9c4b8hy`
2. Deployment Center → Manage publish profile
3. Click "Download publish profile"

#### For Node.js App Service:
```bash
az webapp deployment list-publishing-profiles \
  --name whatsappbotserver \
  --resource-group whatsapp-rg \
  --xml
```

**OR** via Azure Portal:
1. Go to App Service: `whatsappbotserver`
2. Deployment Center → Manage publish profile
3. Click "Download publish profile"

#### For Azure Static Web Apps:
```bash
az staticwebapp secrets list \
  --name <your-static-web-app-name> \
  --resource-group whatsapp-rg
```

**OR** via Azure Portal:
1. Go to Static Web App resource
2. Settings → Deployment token
3. Copy the deployment token

### Step 2: Add GitHub Secrets

1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secrets:

#### Required Secrets:

| Secret Name | Value | Used By |
|-------------|-------|---------|
| `AZURE_FASTAPI_PUBLISH_PROFILE` | FastAPI publish profile XML | deploy-fastapi.yml |
| `AZURE_NODEJS_PUBLISH_PROFILE` | Node.js publish profile XML | deploy-nodejs.yml |
| `AZURE_STATIC_WEB_APPS_API_TOKEN` | Static Web Apps deployment token | deploy-frontend.yml |

#### Frontend Environment Secrets:

| Secret Name | Example Value | Description |
|-------------|---------------|-------------|
| `VITE_DJANGO_URL` | `https://backeng4whatsapp-...azurewebsites.net` | Django backend URL |
| `VITE_FASTAPI_URL` | `https://fastapione-...azurewebsites.net` | FastAPI backend URL |
| `VITE_NODEJS_URL` | `https://whatsappbotserver.azurewebsites.net` | Node.js server URL |
| `VITE_META_GRAPH_API_URL` | `https://graph.facebook.com/v20.0` | Meta Graph API URL |
| `VITE_WABA_ID` | `460830850456088` | WhatsApp Business Account ID |

**Note:** `VITE_META_ACCESS_TOKEN` should NOT be added to GitHub secrets if using backend proxy (recommended)

### Step 3: Configure Azure Environment Variables

The workflows only deploy code. Azure App Service environment variables must be configured separately:

#### FastAPI Configuration:
```bash
az webapp config appsettings set \
  --name fastapione-gue2c5ecc9c4b8hy \
  --resource-group whatsapp-rg \
  --settings \
    JWT_SECRET_KEY="<your-secret>" \
    DJANGO_SERVICE_KEY="sk_django_<key>" \
    FASTAPI_SERVICE_KEY="sk_fastapi_<key>" \
    NODEJS_SERVICE_KEY="sk_nodejs_<key>" \
    CORS_ALLOWED_ORIGINS="https://<your-frontend-url>"
```

#### Node.js Configuration:
```bash
az webapp config appsettings set \
  --name whatsappbotserver \
  --resource-group whatsapp-rg \
  --settings \
    REDIS_URL="rediss://<redis-name>.redis.cache.windows.net:6380?password=<key>" \
    DJANGO_SERVICE_KEY="sk_django_<key>" \
    FASTAPI_SERVICE_KEY="sk_fastapi_<key>" \
    NODEJS_SERVICE_KEY="sk_nodejs_<key>" \
    NODE_ENV="production"
```

**See PHASE3_DEPLOYMENT_GUIDE.md for full environment variable list**

### Step 4: Test Workflows

#### Manual Test:
1. Go to GitHub repository
2. Actions tab
3. Select workflow (e.g., "Deploy FastAPI to Azure App Service")
4. Click "Run workflow"
5. Select `main` branch
6. Click "Run workflow"

#### Automatic Test:
1. Make a small change to the service code
2. Commit and push to `main` branch
3. Watch GitHub Actions tab for automatic deployment

---

## Workflow Features

### Automatic Deployment
- Workflows trigger automatically on push to `main`
- Only deploys if relevant files changed (smart path filtering)
- Parallel deployments possible (different services)

### Build Verification
- Installs dependencies
- Creates optimized build packages
- Excludes unnecessary files (`.git`, `.env`, `__pycache__`, etc.)

### Deployment Verification
- Health checks after deployment
- FastAPI: Tests `/health` endpoint
- Node.js: Tests root `/` endpoint
- Frontend: Manual verification required

### Deployment Summary
- Creates summary in GitHub Actions UI
- Shows deployment details (URL, version, deployer)
- Lists manual verification steps

---

## Troubleshooting

### Issue: Workflow fails with "publish profile invalid"

**Solution:**
1. Download fresh publish profile from Azure
2. Update GitHub secret with new XML content
3. Ensure entire XML is copied (no truncation)

### Issue: Workflow succeeds but app doesn't work

**Possible causes:**
1. **Environment variables not set** - Set via Azure Portal or CLI
2. **CORS not configured** - Update `CORS_ALLOWED_ORIGINS`
3. **Service keys mismatch** - Ensure all services have same keys
4. **Redis not connected** - Check `REDIS_URL` and firewall rules

**Debugging:**
```bash
# Check app logs
az webapp log tail \
  --name <app-name> \
  --resource-group whatsapp-rg

# Check current environment variables
az webapp config appsettings list \
  --name <app-name> \
  --resource-group whatsapp-rg
```

### Issue: Frontend build fails with "VITE_* undefined"

**Solution:**
1. Ensure GitHub secrets are set (Settings → Secrets → Actions)
2. Secret names must match exactly: `VITE_DJANGO_URL` etc.
3. Check workflow logs for which secret is missing

### Issue: Node.js deployment succeeds but Redis fails

**Check:**
1. `REDIS_URL` environment variable set in Azure App Service
2. Redis firewall allows App Service IPs
3. Redis connection string format correct
4. Fallback mode logs: "Using in-memory rate limiting as fallback"

**Redis should work, but fallback is safe**

---

## Best Practices

### 1. Use Branch Protection
```
Settings → Branches → Add rule for `main`
- Require pull request reviews
- Require status checks to pass (optional)
- Include administrators
```

### 2. Test in Staging First
- Create separate workflows for staging environment
- Test deployments there before production
- Use different Azure resources for staging

### 3. Manual Approval (Optional)
Add manual approval step to production deployments:
```yaml
jobs:
  deploy:
    environment:
      name: production
      # Requires manual approval in GitHub UI
```

### 4. Rollback Capability
- Keep previous deployment packages
- Use Azure deployment slots for instant rollback
- Document rollback procedure

### 5. Monitor Deployments
- Check GitHub Actions tab after each push
- Verify health checks in workflow logs
- Monitor Azure Application Insights
- Set up alerts for deployment failures

---

## Deployment Frequency

**Recommended:**
- Development: Continuous (every push)
- Staging: Daily or per-feature
- Production: Weekly or per-release

**Current Setup:**
- Deploys on every push to `main` (when files change)
- Manual trigger available via "Run workflow" button

---

## Manual Deployment (Fallback)

If GitHub Actions unavailable, deploy manually:

### FastAPI:
```bash
cd fastAPIWhatsapp_withclaude
zip -r deploy.zip . -x "*.git*" ".env"
az webapp deployment source config-zip \
  --resource-group whatsapp-rg \
  --name fastapione-gue2c5ecc9c4b8hy \
  --src deploy.zip
```

### Node.js:
```bash
cd whatsapp_bot_server_withclaude
zip -r deploy.zip . -x "*.git*" ".env" "*.log"
az webapp deployment source config-zip \
  --resource-group whatsapp-rg \
  --name whatsappbotserver \
  --src deploy.zip
```

### Frontend:
```bash
cd whatsappBusinessAutomation_withclaude
npm ci
npm run build
az storage blob upload-batch \
  --account-name <storage-account> \
  --source ./dist \
  --destination '$web'
```

---

## Security Notes

1. **Never commit:**
   - `.env` files
   - `publish profiles`
   - `service keys`
   - `access tokens`

2. **Use GitHub secrets for:**
   - Azure publish profiles
   - Environment-specific URLs
   - API tokens (if needed in build)

3. **Use Azure App Settings for:**
   - Service keys
   - Database credentials
   - Redis connection strings
   - JWT secrets

4. **Rotate secrets regularly:**
   - Service keys (quarterly)
   - JWT secrets (quarterly)
   - Meta access tokens (per Meta guidelines)

---

## Support

**Issues with workflows:**
- Check GitHub Actions logs
- Review Azure deployment center
- Consult PHASE3_DEPLOYMENT_GUIDE.md

**Issues with Azure:**
- Check Azure Portal diagnostics
- Review App Service logs
- Check Application Insights

**Phase 3 specific issues:**
- See PHASE3_TESTING_GUIDE.md
- See PHASE3_DEPLOYMENT_CHECKLIST.md

---

**Last Updated:** 2026-01-07
**Workflows Version:** 1.0
