# Phase 3 Deployment Checklist

**Date:** _______________
**Deployed By:** _______________
**Environment:** [ ] Staging [ ] Production

---

## Pre-Deployment (Day Before)

### Code Preparation
- [ ] All Phase 3 code merged to main branch
- [ ] Git tag created: `phase3-v1.0.0`
- [ ] All tests passing (12/14 tests from PHASE3_TEST_RESULTS.md)
- [ ] Code review completed and approved
- [ ] No sensitive data in repository (.env files gitignored)

### Documentation
- [ ] PHASE3_INFRASTRUCTURE_COMPLETE.md reviewed
- [ ] PHASE3_DEPLOYMENT_GUIDE.md reviewed
- [ ] API documentation updated (if needed)
- [ ] Changelog updated

### Team Coordination
- [ ] Deployment time scheduled (off-peak recommended)
- [ ] Team notified of deployment window
- [ ] On-call rotation confirmed
- [ ] Rollback team on standby
- [ ] Communication plan for users (if needed)

---

## Infrastructure Setup (Day 1)

### Azure Redis Cache
- [ ] Redis created: `whatsapp-prod-redis`
- [ ] SKU: Standard C1 (1GB) for production
- [ ] TLS enabled (port 6380)
- [ ] Persistence enabled (RDB every 15 min)
- [ ] Maxmemory policy: allkeys-lru
- [ ] Connection string obtained
- [ ] Firewall rules configured (if needed)
- [ ] Test connection: `redis-cli ping` returns PONG

**Connection String:**
```
rediss://____________.redis.cache.windows.net:6380?password=____________
```

### Application Insights (Optional but Recommended)
- [ ] App Insights resource created
- [ ] Instrumentation key obtained
- [ ] Connected to all 3 services (FastAPI, Node.js, Django)

---

## Security Configuration

### Service Keys Generation
Generate NEW service keys for production (don't reuse dev/staging):

```bash
# Run these commands and save outputs
python -c "import secrets; print('sk_django_' + secrets.token_urlsafe(32))"
python -c "import secrets; print('sk_fastapi_' + secrets.token_urlsafe(32))"
python -c "import secrets; print('sk_nodejs_' + secrets.token_urlsafe(32))"
```

- [ ] Django service key generated: `sk_django_____________`
- [ ] FastAPI service key generated: `sk_fastapi_____________`
- [ ] Node.js service key generated: `sk_nodejs_____________`
- [ ] Keys saved securely (password manager)
- [ ] **CRITICAL:** Same keys used across ALL services

### Other Secrets
- [ ] JWT secret key rotated (different from dev)
- [ ] Meta access token (production token)
- [ ] Database passwords secured
- [ ] All secrets stored in Azure Key Vault or App Settings (NOT in code)

---

## FastAPI Deployment

### Environment Variables
- [ ] JWT_SECRET_KEY configured
- [ ] DJANGO_SERVICE_KEY configured
- [ ] FASTAPI_SERVICE_KEY configured
- [ ] NODEJS_SERVICE_KEY configured
- [ ] CORS_ALLOWED_ORIGINS updated to production frontend URL
- [ ] DATABASE_URL configured (if separate analytics DB)
- [ ] META_ACCESS_TOKEN configured

### Deployment
- [ ] Code deployed to: `fastapione-gue2c5ecc9c4b8hy`
- [ ] Deployment method: [ ] GitHub Actions [ ] Azure CLI [ ] Manual
- [ ] App restarted
- [ ] Logs checked for errors

### Verification
- [ ] Health endpoint responds: `GET /health` returns 200
```bash
curl https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/health
```
- [ ] Service authentication works (test with service key)
- [ ] CORS headers present for frontend origin
- [ ] No errors in Application Insights

**Health Check Result:** _______________

---

## Node.js Deployment

### Environment Variables
- [ ] REDIS_URL configured (Azure Redis connection string)
- [ ] DJANGO_SERVICE_KEY configured (same as FastAPI)
- [ ] FASTAPI_SERVICE_KEY configured (same as FastAPI)
- [ ] NODEJS_SERVICE_KEY configured (same as FastAPI)
- [ ] META_ACCESS_TOKEN configured
- [ ] ANALYTICS_DB_* configured (if separate DB)
- [ ] NODE_ENV=production
- [ ] PORT=8080 (or default)

### Deployment
- [ ] Code deployed to: `whatsappbotserver`
- [ ] PM2 ecosystem.config.js present
- [ ] Deployment method: [ ] GitHub Actions [ ] Azure CLI [ ] Manual
- [ ] App restarted
- [ ] Logs checked for Redis connection

### Verification
- [ ] Root endpoint responds: `GET /` returns 200
```bash
curl https://whatsappbotserver.azurewebsites.net/
```
- [ ] Redis connection successful (check logs)
```
Expected log: "✅ Redis: Connected and ready"
```
- [ ] Rate limiting active (check logs)
```
Expected log: "Rate limiting initialized"
```
- [ ] No errors in Application Insights

**Redis Connection Status:** [ ] Connected [ ] Fallback Mode
**Logs Review:** _______________

---

## Frontend Deployment

### Build Configuration
- [ ] `.env.production` created with production URLs
- [ ] VITE_DJANGO_URL set to Django production URL
- [ ] VITE_FASTAPI_URL set to FastAPI production URL
- [ ] VITE_NODEJS_URL set to Node.js production URL
- [ ] VITE_META_ACCESS_TOKEN removed (use backend proxy) OR present

### Build & Deploy
- [ ] Dependencies installed: `npm ci`
- [ ] Production build created: `npm run build`
- [ ] Build successful (no errors)
- [ ] Deployment target: [ ] Azure Static Web Apps [ ] Blob Storage
- [ ] Files uploaded to production
- [ ] CDN cache purged (if applicable)

### Verification
- [ ] Frontend loads in browser
- [ ] No CORS errors in browser console
- [ ] API configuration logged in console (if dev mode):
```
Expected: 🔧 API Configuration: { django: ..., fastapi: ..., nodejs: ... }
```
- [ ] Test API call works (e.g., get templates)
- [ ] No JavaScript errors

**Frontend URL:** _______________
**Browser Test:** [ ] Pass [ ] Fail

---

## Integration Testing

### Service-to-Service Authentication
```bash
# Test FastAPI with service key
curl -X GET "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/broadcast-analytics/date-range" \
  -H "X-Service-Key: sk_fastapi_____________" \
  -H "X-Tenant-Id: test"
```
- [ ] Returns tenant validation or data (not 403 Forbidden)
- [ ] Invalid service key returns 403

### Rate Limiting
```bash
# Make 105 rapid requests
for i in {1..105}; do
  curl -s -w "%{http_code}\n" https://whatsappbotserver.azurewebsites.net/ -o /dev/null
done | grep 429
```
- [ ] First ~100 requests return 200
- [ ] Requests 101+ return 429 (Too Many Requests)
- [ ] Retry-After header present
- [ ] X-RateLimit-* headers present

### CORS Configuration
```bash
# Test CORS from frontend origin
curl -I -X OPTIONS \
  -H "Origin: https://<your-frontend-url>" \
  -H "Access-Control-Request-Method: GET" \
  https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/broadcast-analytics/
```
- [ ] Access-Control-Allow-Origin includes frontend URL
- [ ] Access-Control-Allow-Methods present
- [ ] Access-Control-Allow-Credentials: true (if needed)

### Frontend → Backend Communication
- [ ] Login works (if testing with user account)
- [ ] Analytics page loads
- [ ] API calls from frontend succeed
- [ ] No authentication errors
- [ ] Data displays correctly

**Integration Test Status:** [ ] All Pass [ ] Issues Found

---

## Monitoring Setup

### Application Insights
- [ ] Availability tests configured:
  - [ ] FastAPI /health (every 5 min)
  - [ ] Node.js / (every 5 min)
  - [ ] Frontend homepage (every 5 min)

- [ ] Alert rules created:
  - [ ] Critical: Service down (availability < 99%)
  - [ ] Critical: High error rate (5xx > 10 in 5 min)
  - [ ] Warning: Slow responses (P95 > 500ms)
  - [ ] Warning: Redis connection failures

- [ ] Action groups configured:
  - [ ] Email notifications
  - [ ] SMS (for critical alerts)
  - [ ] Slack/Teams integration (optional)

### Dashboards
- [ ] Application Insights dashboard created
- [ ] Key metrics pinned:
  - [ ] Availability
  - [ ] Response times
  - [ ] Error rates
  - [ ] Rate limit violations

**Monitoring Status:** [ ] Configured [ ] Pending

---

## Post-Deployment Verification (First 24 Hours)

### Hour 1-2: Immediate Checks
- [ ] All services responding
- [ ] No critical errors in logs
- [ ] Application Insights collecting data
- [ ] User test scenarios working

### Hour 2-6: Monitoring
- [ ] Response times normal
- [ ] Error rates acceptable
- [ ] Redis connections stable
- [ ] Rate limiting working as expected

### Hour 6-24: Stability
- [ ] No memory leaks observed
- [ ] No unexpected rate limit violations
- [ ] No CORS issues reported
- [ ] User feedback collected (if applicable)

**24-Hour Status:** [ ] Stable [ ] Issues Identified

---

## Rollback Plan (If Needed)

### Rollback Decision Criteria
- Critical errors affecting users
- Service unavailability > 10 minutes
- Data integrity issues
- Security vulnerabilities discovered

### Rollback Steps
1. [ ] Notify team of rollback decision
2. [ ] Document issues found
3. [ ] Execute rollback:
   - [ ] FastAPI: Swap deployment slot or redeploy previous version
   - [ ] Node.js: Swap deployment slot or redeploy previous version
   - [ ] Frontend: Redeploy previous build
   - [ ] Environment variables: Revert if needed
4. [ ] Verify services after rollback
5. [ ] Update status page/users
6. [ ] Schedule post-mortem

**Rollback Executed:** [ ] Yes [ ] No
**Rollback Time:** _______________

---

## Sign-Off

### Deployment Team

**FastAPI Deployment:**
- Deployed by: _______________ Date: _____ Time: _____
- Verified by: _______________ Date: _____ Time: _____

**Node.js Deployment:**
- Deployed by: _______________ Date: _____ Time: _____
- Verified by: _______________ Date: _____ Time: _____

**Frontend Deployment:**
- Deployed by: _______________ Date: _____ Time: _____
- Verified by: _______________ Date: _____ Time: _____

**Final Approval:**
- Tech Lead: _______________ Date: _____ Time: _____
- Product Owner: _______________ Date: _____ Time: _____

### Deployment Status

- [ ] **SUCCESSFUL** - All services deployed and verified
- [ ] **PARTIAL** - Some issues, monitoring required
- [ ] **FAILED** - Rollback executed
- [ ] **POSTPONED** - Deployment rescheduled

**Overall Status:** _______________

**Notes:**
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________

---

## Post-Deployment Tasks

- [ ] Update documentation with production URLs
- [ ] Send deployment summary to stakeholders
- [ ] Schedule post-deployment review meeting
- [ ] Update incident response runbook
- [ ] Archive deployment logs
- [ ] Close deployment ticket/issue

**Deployment Complete:** _______________

---

**Checklist Version:** 1.0
**Last Updated:** 2026-01-07
