# Azure Environment Variables Setup Guide

## 🚨 CRITICAL: Your App is Missing Environment Variables!

You only have 4 environment variables configured in Azure, but your app needs **20+ variables** to work properly.

---

## 📋 What's Missing?

All of these from your `.env` file:

- ✅ `REDIS_URL` (already added)
- ❌ `JWT_SECRET_KEY` (CRITICAL)
- ❌ `DJANGO_SERVICE_KEY` (CRITICAL)
- ❌ `FASTAPI_SERVICE_KEY` (CRITICAL)
- ❌ `NODEJS_SERVICE_KEY` (CRITICAL)
- ❌ `DJANGO_URL`
- ❌ `FASTAPI_URL`
- ❌ `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- ❌ `ANALYTICS_DB_*` (all analytics DB variables)
- ❌ `OPENAI_API_KEY`
- ❌ `APP_SECRET` (Meta)
- ❌ `GOOGLE_SERVICE_ACCOUNT_BASE64`
- ❌ `PASSPHRASE`, `PRIVATE_KEY`, `PUBLIC_KEY`
- And more...

---

## ✅ SOLUTION: Choose Your Method

### **Option 1: Automated Script (RECOMMENDED)** ⚡

Uploads ALL variables from your `.env` file automatically.

#### **For Windows (PowerShell):**

```powershell
# 1. Open upload_env_to_azure.ps1
# 2. Update lines 7-8 with your Azure details:
$RESOURCE_GROUP = "your-resource-group"
$APP_NAME = "your-app-service-name"

# 3. Run the script
cd whatsapp_bot_server_withclaude
.\upload_env_to_azure.ps1
```

#### **For Linux/Mac (Bash):**

```bash
# 1. Open upload_env_to_azure.sh
# 2. Update lines 7-8 with your Azure details:
RESOURCE_GROUP="your-resource-group"
APP_NAME="your-app-service-name"

# 3. Run the script
cd whatsapp_bot_server_withclaude
chmod +x upload_env_to_azure.sh
./upload_env_to_azure.sh
```

**Find your Azure details:**
```bash
az webapp list --query "[].{name:name, resourceGroup:resourceGroup}" -o table
```

---

### **Option 2: Manual via Azure Portal** 🖱️

**Step 1: Copy Variables**

Copy ALL these variables from your `.env` file:

```
JWT_SECRET_KEY=whatsapp-business-automation-jwt-secret-2026-change-in-production
JWT_SECRET=whatsapp-business-automation-jwt-secret-2026-change-in-production
DJANGO_SERVICE_KEY=sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc
FASTAPI_SERVICE_KEY=sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k
NODEJS_SERVICE_KEY=sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34
DJANGO_URL=https://django-faecdbgwhgepemec.canadacentral-01.azurewebsites.net
FASTAPI_URL=https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net
FAST_API_URL=https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net
NODEJS_URL=http://localhost:8080
REDIS_PASSWORD=O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM=
OPENAI_API_KEY=sk-cm8m6Rq-m4CjagBssykBM7QjXuc-oYxhLOc1Gz3nFnT3BlbkFJNVYczQDlGxipQYe6sXE927pH-zugcBFZxa-4lHmkgA
APP_SECRET=1cc11e828571e071c91f56da993bb60b
PASSPHRASE=COOL
DB_HOST=nurenaistore.postgres.database.azure.com
DB_PORT=5432
DB_NAME=nurenpostgres_Whatsapp
DB_USER=nurenai
DB_PASSWORD=Biz1nurenWar*
ANALYTICS_DB_HOST=nurenaistore.postgres.database.azure.com
ANALYTICS_DB_PORT=5432
ANALYTICS_DB_NAME=nurenpostgres_Whatsapp
ANALYTICS_DB_USER=nurenai
ANALYTICS_DB_PASSWORD=Biz1nurenWar*
```

**Note:** For `PRIVATE_KEY`, `PUBLIC_KEY`, and `GOOGLE_SERVICE_ACCOUNT_BASE64`, copy the ENTIRE value including all line breaks.

**Step 2: Add to Azure**

1. Go to [Azure Portal](https://portal.azure.com/)
2. Find your App Service (Node.js bot server)
3. Go to **Configuration** → **Application settings**
4. For EACH variable:
   - Click **+ New application setting**
   - Name: Variable name (e.g., `JWT_SECRET_KEY`)
   - Value: Variable value
   - Click **OK**
5. Click **Save** at the top
6. Click **Continue** to restart

**This will take ~10-15 minutes to add all variables manually.**

---

### **Option 3: Azure CLI One-Liner** 🚀

**Fastest if you know Azure CLI:**

```bash
# Replace YOUR_RESOURCE_GROUP and YOUR_APP_NAME
az webapp config appsettings set \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME \
  --settings \
    JWT_SECRET_KEY="whatsapp-business-automation-jwt-secret-2026-change-in-production" \
    JWT_SECRET="whatsapp-business-automation-jwt-secret-2026-change-in-production" \
    DJANGO_SERVICE_KEY="sk_django_oOcCi1SfeOtcAY3q5iuH-xzulCnwunYeedAZUFEinNc" \
    FASTAPI_SERVICE_KEY="sk_fastapi_9DoPMGmd4I-5HhX_d68me-A_rwjhz_FANd1M0dIeV6k" \
    NODEJS_SERVICE_KEY="sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34" \
    DJANGO_URL="https://django-faecdbgwhgepemec.canadacentral-01.azurewebsites.net" \
    FASTAPI_URL="https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net" \
    FAST_API_URL="https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net" \
    OPENAI_API_KEY="sk-cm8m6Rq-m4CjagBssykBM7QjXuc-oYxhLOc1Gz3nFnT3BlbkFJNVYczQDlGxipQYe6sXE927pH-zugcBFZxa-4lHmkgA" \
    APP_SECRET="1cc11e828571e071c91f56da993bb60b" \
    PASSPHRASE="COOL" \
    DB_HOST="nurenaistore.postgres.database.azure.com" \
    DB_PORT="5432" \
    DB_NAME="nurenpostgres_Whatsapp" \
    DB_USER="nurenai" \
    DB_PASSWORD="Biz1nurenWar*" \
    ANALYTICS_DB_HOST="nurenaistore.postgres.database.azure.com" \
    ANALYTICS_DB_PORT="5432" \
    ANALYTICS_DB_NAME="nurenpostgres_Whatsapp" \
    ANALYTICS_DB_USER="nurenai" \
    ANALYTICS_DB_PASSWORD="Biz1nurenWar*" \
    REDIS_PASSWORD="O6qxsVvcWHfbwdgBxb1yEDfLeBv5VBmaUAzCaJvnELM="

# Restart the app
az webapp restart --resource-group YOUR_RESOURCE_GROUP --name YOUR_APP_NAME
```

**Note:** For multi-line values (`PRIVATE_KEY`, `PUBLIC_KEY`, `GOOGLE_SERVICE_ACCOUNT_BASE64`), you'll need to add them separately via the Portal or use the automated script.

---

## ✅ After Adding Variables

### Step 1: Verify Environment Variables

```bash
# View all configured variables
az webapp config appsettings list \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME \
  --query "[].{name:name}" -o table
```

You should see 20+ variables now (not just 4).

### Step 2: Check Logs

```bash
az webapp log tail \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME
```

**Look for success messages:**
```
✅ Rate Limiter: Redis connected
✅ Analytics aggregation jobs initialized
Server is listening on port: 8080
```

**These errors should be GONE:**
```
❌ Redis Client Error: connect ECONNREFUSED 127.0.0.1:6379
⚠️ Using in-memory rate limiting as fallback
```

---

## 🔐 Security Note

**IMPORTANT:** Never commit `.env` files or these scripts (with your keys) to Git!

Your `.gitignore` should include:
```
.env
upload_env_to_azure.ps1
upload_env_to_azure.sh
AZURE_ENV_SETUP.md
```

---

## 📊 Quick Status Check

After deployment, verify ALL variables are set:

```bash
# Count variables (should be 20+, not 4)
az webapp config appsettings list \
  --resource-group YOUR_RESOURCE_GROUP \
  --name YOUR_APP_NAME \
  --query "length(@)"
```

---

## 🆘 Troubleshooting

### Issue: "az command not found"
**Solution:** Install Azure CLI: https://aka.ms/installazurecliwindows

### Issue: "Subscription not found"
**Solution:** Login to Azure: `az login`

### Issue: Script permission denied (Linux/Mac)
**Solution:** `chmod +x upload_env_to_azure.sh`

### Issue: Variables not showing up
**Solution:** Wait 30 seconds after restart, then check again

---

## 🎯 Recommended Approach

**Use Option 1 (Automated Script)** - It's:
- ✅ Fastest (30 seconds vs 15 minutes)
- ✅ No typos
- ✅ Handles multi-line values correctly
- ✅ Masks sensitive values in output

Just update the Resource Group and App Name in the script, and run it!

---

## 📞 Need Help?

**Find your Azure details:**
```bash
az account show
az webapp list --query "[].{name:name, resourceGroup:resourceGroup}" -o table
```

**Common Resource Group names:**
- whatsapp-rg
- whatsapp-bot-rg
- nodejs-app-rg
- (check your Azure Portal)

**Common App Service names:**
- whatsappbotserver
- nodejs-app
- whatsapp-webhook
- (check your Azure Portal)
