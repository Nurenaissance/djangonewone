# Phase 3 Testing Guide

## Pre-Testing Checklist

### 1. Install Redis (if not already installed)

**Windows:**
```bash
# Using Chocolatey
choco install redis-64

# Or download from: https://github.com/microsoftarchive/redis/releases
```

**Verify Redis Installation:**
```bash
redis-cli ping
# Should return: PONG
```

### 2. Start All Services

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Django:**
```bash
cd whatsapp_latest_final_withclaude
python manage.py runserver
```

**Terminal 3 - FastAPI:**
```bash
cd fastAPIWhatsapp_withclaude
uvicorn main:app --reload --port 8001
```

**Terminal 4 - Node.js:**
```bash
cd whatsapp_bot_server_withclaude
npm start
```

**Terminal 5 - Frontend:**
```bash
cd whatsappBusinessAutomation_withclaude
npm run dev
```

---

## Test 1: Enhanced Analytics Endpoints

### 1.1 Test Date Range Analytics

```bash
# Basic request (last 30 days by default)
curl -X GET "http://localhost:8001/broadcast-analytics/date-range" \
  -H "X-Tenant-Id: test_tenant_123"

# Specific date range
curl -X GET "http://localhost:8001/broadcast-analytics/date-range?start_date=01-12-2025&end_date=07-01-2026" \
  -H "X-Tenant-Id: test_tenant_123"

# Invalid date format (should return 400)
curl -X GET "http://localhost:8001/broadcast-analytics/date-range?start_date=2025-12-01" \
  -H "X-Tenant-Id: test_tenant_123"
```

**Expected Response:**
```json
{
  "start_date": "08-12-2025",
  "end_date": "07-01-2026",
  "total_records": 0,
  "summary": {
    "total_sent": 0,
    "total_delivered": 0,
    "total_read": 0,
    "total_cost": 0,
    "delivery_rate": 0,
    "read_rate": 0
  },
  "data": []
}
```

### 1.2 Test Per-Template Analytics

**Note:** Requires valid template_id and WhatsApp credentials

```bash
curl -X GET "http://localhost:8001/broadcast-analytics/template/YOUR_TEMPLATE_ID?days=7" \
  -H "X-Tenant-Id: test_tenant_123"
```

### 1.3 Test Campaign Analytics

```bash
curl -X GET "http://localhost:8001/broadcast-analytics/campaign/test_campaign_1" \
  -H "X-Tenant-Id: test_tenant_123"
```

**Expected Response:**
```json
{
  "campaign_id": "test_campaign_1",
  "message": "Campaign analytics endpoint - implementation pending",
  "summary": {
    "total_sent": 0,
    "total_delivered": 0,
    "total_read": 0,
    "total_cost": 0
  }
}
```

---

## Test 2: Redis Session Management

### 2.1 Check Redis Connection

```bash
# In Node.js terminal, look for:
✅ Redis: Connected and ready
Server is listening on port: 8080
```

### 2.2 Test Session Storage

**Create a session via webhook (simulate):**
```bash
# This will be tested when the Node.js server receives WhatsApp webhooks
# For now, check Redis directly
```

**Check Redis sessions:**
```bash
redis-cli

# List all session keys
KEYS whatsapp:session:*

# Get a specific session (if any exist)
GET whatsapp:session:1234567890919876543210

# Check TTL (should be around 86400 seconds = 24 hours)
TTL whatsapp:session:1234567890919876543210

# Exit Redis CLI
exit
```

### 2.3 Test Session Persistence

```bash
# 1. Create a session by triggering a webhook
# 2. Stop Node.js server (Ctrl+C)
# 3. Restart Node.js server
# 4. Check if session still exists in Redis
redis-cli KEYS whatsapp:session:*
```

### 2.4 Test Graceful Shutdown

```bash
# In Node.js terminal, press Ctrl+C
# Should see:
^CSIGINT received. Starting graceful shutdown...
✅ HTTP server closed
✅ Socket.IO closed
✅ Redis: Disconnected gracefully
✅ Rate Limiter: Redis connection closed
✅ Graceful shutdown complete
```

---

## Test 3: Rate Limiting

### 3.1 Test API Rate Limit (100 req/min)

**Using curl in a loop:**
```bash
# Windows PowerShell
for ($i=1; $i -le 105; $i++) {
  Write-Host "Request $i"
  curl -X GET "http://localhost:8080/api/test" 2>&1 | Select-String "429"
}

# Linux/Mac/Git Bash
for i in {1..105}; do
  echo "Request $i"
  curl -s -w "%{http_code}\n" -X GET "http://localhost:8080/api/test" -o /dev/null
done
```

**Expected:**
- First 100 requests: 200 or 404 (endpoint may not exist, but not rate limited)
- Requests 101-105: 429 (Too Many Requests)

### 3.2 Test Rate Limit Response Headers

```bash
# Make a request and check headers
curl -i -X GET "http://localhost:8080/api/test"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
```

**After hitting limit:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 60
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-01-07T12:01:00.000Z

{
  "error": "Too Many Requests",
  "message": "API rate limit exceeded. Maximum 100 requests per minute.",
  "retryAfter": 60,
  "limit": 100,
  "remaining": 0
}
```

### 3.3 Test Service-to-Service Exemption

```bash
# Request WITHOUT service key (should be rate limited after 100 requests)
curl -X GET "http://localhost:8080/api/test"

# Request WITH service key (should NOT be rate limited)
curl -X GET "http://localhost:8080/api/test" \
  -H "X-Service-Key: sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34"
```

### 3.4 Check Redis Rate Limit Keys

```bash
redis-cli

# List all rate limit keys
KEYS rl:*

# Check a specific rate limiter
GET rl:api:127.0.0.1

# Check TTL
TTL rl:api:127.0.0.1

exit
```

---

## Test 4: Frontend Environment Configuration

### 4.1 Verify .env File Exists

```bash
cd whatsappBusinessAutomation_withclaude
ls -la | grep ".env"

# Should see:
# .env
# .env.example
```

### 4.2 Check Environment Variables Loaded

**Start frontend in dev mode:**
```bash
npm run dev
```

**Open browser console (F12):**
```
Look for:
🔧 API Configuration: {
  django: 'http://localhost:8000',
  fastapi: 'http://localhost:8001',
  nodejs: 'http://localhost:8080'
}
```

### 4.3 Test API Calls

**In browser console:**
```javascript
// Check if variables are loaded
console.log('Django URL:', import.meta.env.VITE_DJANGO_URL);
console.log('FastAPI URL:', import.meta.env.VITE_FASTAPI_URL);
console.log('Node.js URL:', import.meta.env.VITE_NODEJS_URL);

// Test API call
fetch('http://localhost:8001/docs')
  .then(r => r.text())
  .then(html => console.log('FastAPI docs accessible:', html.length > 0))
```

### 4.4 Verify .env Not Committed

```bash
# Check .gitignore
cat .gitignore | grep ".env"

# Should see:
# .env
# .env.local
# .env.*.local
```

### 4.5 Test Production Build

```bash
# Build with environment variables
npm run build

# Check if env vars are baked into build
cd dist
grep -r "localhost:8001" assets/*.js

# Should find references to localhost URLs (baked in at build time)
```

---

## Test 5: Integration Testing

### 5.1 Full Flow Test

1. **Start all services** (Redis, Django, FastAPI, Node.js, Frontend)

2. **Login to frontend:**
   - Navigate to http://localhost:5173
   - Login with test credentials
   - Check browser console for API configuration logs

3. **Test Analytics:**
   - Navigate to analytics page
   - Try date range filters
   - Check network tab for API calls to FastAPI

4. **Trigger WhatsApp Interaction:**
   - Send a test message to your WhatsApp bot
   - Check Node.js logs for session creation
   - Verify session stored in Redis

5. **Test Rate Limiting:**
   - Make rapid API calls from frontend
   - Should NOT hit rate limit (authenticated user)
   - Remove auth token and try again
   - Should hit rate limit after threshold

### 5.2 Load Testing (Optional)

**Using Apache Bench:**
```bash
# Install Apache Bench
# Windows: Download from Apache website
# Mac: brew install httpd
# Linux: sudo apt-get install apache2-utils

# Test FastAPI analytics endpoint
ab -n 1000 -c 10 http://localhost:8001/broadcast-analytics/

# Test Node.js with rate limiting
ab -n 200 -c 10 http://localhost:8080/api/test

# Should see rate limit errors after threshold
```

---

## Test Results Checklist

### Analytics Endpoints
- [ ] Date range endpoint returns data or empty array
- [ ] Invalid date format returns 400 error
- [ ] Tenant isolation works (different tenant IDs return different data)
- [ ] Summary calculations are correct (delivery_rate, read_rate)
- [ ] Per-template endpoint fetches from Meta API
- [ ] Campaign endpoint returns placeholder structure

### Redis Sessions
- [ ] Redis connection established on startup
- [ ] Sessions stored with correct key format (`whatsapp:session:*`)
- [ ] Sessions have 24-hour TTL
- [ ] Sessions persist across server restarts
- [ ] Graceful shutdown closes Redis connection
- [ ] Falls back to in-memory if Redis unavailable

### Rate Limiting
- [ ] API rate limit enforced (100 req/min)
- [ ] 429 response with correct headers
- [ ] Retry-After header present
- [ ] Service-to-service calls exempt from rate limiting
- [ ] Rate limits stored in Redis (`rl:*` keys)
- [ ] Falls back to in-memory if Redis unavailable

### Frontend Environment
- [ ] .env file loads variables correctly
- [ ] Development logging shows API URLs
- [ ] API calls use environment variable URLs
- [ ] .env file NOT committed to git
- [ ] Production build bakes environment variables
- [ ] All API endpoints accessible from frontend

---

## Troubleshooting

### Redis Connection Errors

**Error:** `Error: connect ECONNREFUSED 127.0.0.1:6379`

**Solutions:**
```bash
# Check if Redis is running
redis-cli ping

# If not running, start Redis
redis-server

# Check Redis port
redis-cli -h localhost -p 6379 ping
```

### Rate Limiting Not Working

**Check:**
1. Redis connection established
2. Middleware applied in correct order
3. Request not using service key
4. Check Redis keys: `redis-cli KEYS rl:*`

### Frontend Environment Variables Not Loading

**Check:**
1. .env file exists in project root
2. Variables start with `VITE_`
3. Server restarted after .env changes
4. Using `import.meta.env.VITE_*` (not `process.env`)

### Analytics Endpoints Not Returning Data

**Check:**
1. Database has BroadcastAnalytics records
2. Tenant ID header provided
3. Date range valid
4. For template analytics: valid template ID and Meta credentials

---

## Next Steps After Testing

1. **Fix any issues found**
2. **Document test results**
3. **Set up monitoring**
4. **Prepare for staging deployment**
5. **Plan production rollout**

---

**Testing Date:** 2026-01-07
**Status:** Ready for testing
