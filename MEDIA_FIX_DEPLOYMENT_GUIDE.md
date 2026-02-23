# Media Display Fix - Deployment Guide

## ✅ Implementation Complete!

All code changes have been implemented successfully. Here's what was done:

### Changes Made

1. **✅ Database Schema** - Added 5 new fields to `Conversation` model
2. **✅ Migration Created** - `interaction/migrations/0007_add_media_support_fields.py`
3. **✅ Webhook Updated** - Now uploads media to Azure Blob instead of saving placeholders
4. **✅ Django API Updated** - Saves media fields to database
5. **✅ Frontend Updated** - Displays images, videos, audio, and documents
6. **✅ CSS Added** - Beautiful styling for all media types

---

## 🚀 Deployment Steps

Follow these steps IN ORDER to deploy the fix:

### Step 1: Run Database Migration (CRITICAL)

**On your Django server:**

```bash
cd /path/to/whatsapp_latest_final_withclaude

# Run the migration
python manage.py migrate interaction

# Verify it worked
python manage.py showmigrations interaction
```

**Expected output:**
```
interaction
 [X] 0001_initial
 [X] 0002_...
 [X] 0007_add_media_support_fields  <-- Should show [X]
```

**If migration fails:**
```bash
# Check for errors
python manage.py migrate interaction --verbosity 3

# If you see conflicts, try:
python manage.py migrate interaction 0007_add_media_support_fields --fake
```

---

### Step 2: Deploy Node.js Webhook Changes

**On your whatsapp_bot_server:**

```bash
cd /path/to/whatsapp_bot_server_withclaude

# Pull latest code
git pull origin main

# Restart the server
pm2 restart whatsapp-bot-server

# OR if using different process manager:
pm2 restart all

# Check logs to ensure it started correctly
pm2 logs whatsapp-bot-server --lines 50
```

**Look for these in the logs:**
- ✅ "Redis client connected"
- ✅ "Media Redis client connected"
- ✅ No error messages about missing imports

---

### Step 3: Deploy Django Backend Changes

**On your Django server:**

```bash
cd /path/to/whatsapp_latest_final_withclaude

# Pull latest code
git pull origin main

# Install any new dependencies (if any)
pip install -r requirements.txt

# Collect static files (if needed)
python manage.py collectstatic --noinput

# Restart Django
sudo systemctl restart gunicorn
# OR
sudo systemctl restart your-django-service

# Check logs
sudo journalctl -u gunicorn -f
```

---

### Step 4: Deploy Frontend Changes

**On your frontend server/build machine:**

```bash
cd /path/to/whatsappBusinessAutomation_withclaude

# Pull latest code
git pull origin main

# Install dependencies (if package.json changed)
npm install

# Build the frontend
npm run build

# Deploy the build folder to your hosting
# (Azure Static Web Apps, Vercel, Netlify, etc.)
```

**If deploying to Azure:**
```bash
# Example for Azure Static Web Apps
az staticwebapp deploy \
  --name your-app-name \
  --resource-group your-resource-group \
  --app-location ./build
```

**If deploying manually:**
```bash
# Copy build folder to your web server
scp -r build/* user@server:/var/www/html/
```

---

## 🧪 Testing

### Test 1: Send an Image

1. Send an image from WhatsApp to your bot
2. **Check Node.js logs:**
   ```bash
   pm2 logs whatsapp-bot-server | grep -E "(Image|Blob)"
   ```
   Should see: `✅ Image uploaded to Blob: https://...`

3. **Check database:**
   ```sql
   SELECT id, message_type, media_url, media_caption
   FROM interaction_conversation
   WHERE message_type = 'image'
   ORDER BY id DESC
   LIMIT 5;
   ```
   Should see: Actual Azure Blob URLs in `media_url`

4. **Check frontend:** Open the chat, you should see the actual image, not "[Image]"

### Test 2: Send a Video

1. Send a video from WhatsApp
2. Check logs: Should see `✅ Video uploaded to Blob: https://...`
3. Check frontend: Should see video player with controls

### Test 3: Send Voice Message

1. Record and send voice message from WhatsApp
2. Check logs: Should see `✅ Audio uploaded to Blob: https://...`
3. Check frontend: Should see audio player

### Test 4: Send a Document

1. Send a PDF or document from WhatsApp
2. Check logs: Should see `✅ Document uploaded to Blob: https://...`
3. Check frontend: Should see "View Document" link

---

## 🐛 Troubleshooting

### Issue: Images still show "[Image]"

**Diagnosis:**
```bash
# Check if webhook is running new code
pm2 logs whatsapp-bot-server | grep "Processing image upload"

# If you DON'T see this log, the webhook hasn't been updated
# Solution: Restart webhook server
pm2 restart whatsapp-bot-server --update-env
```

### Issue: Database error "column does not exist"

**Diagnosis:**
```sql
-- Check if columns were added
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'interaction_conversation'
AND column_name IN ('message_type', 'media_url', 'media_caption');
```

**Solution:**
```bash
# Re-run migration
python manage.py migrate interaction
```

### Issue: "Azure Blob upload failed"

**Check Azure credentials:**
```javascript
// In handle-media.js, verify:
const sas = "sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-11-30..."

// Check expiration date: se=2026-11-30
// If expired, generate new SAS token from Azure Portal
```

**Generate new SAS token:**
1. Go to Azure Portal → Storage Account → Shared access signature
2. Set permissions: Read, Write, Add, Create
3. Set expiry: 1-2 years in future
4. Generate SAS
5. Update `handle-media.js` with new SAS token
6. Restart webhook server

### Issue: CORS errors in browser console

**Solution:**
```bash
# In Azure Portal:
# Storage Account → Settings → Resource sharing (CORS)
# Add:
Allowed origins: https://your-frontend-domain.com
Allowed methods: GET, HEAD, OPTIONS
Allowed headers: *
Max age: 3600
```

### Issue: Frontend not showing media

**Check browser console:**
- Press F12 → Console tab
- Look for errors like:
  - "Failed to load image" → Check if Blob URL is accessible
  - "CORS error" → Fix Azure CORS settings
  - "undefined is not a function" → Frontend code didn't deploy

**Verify API response:**
```bash
# Test API endpoint
curl -H "X-Tenant-Id: your-tenant" \
  "https://your-api.com/conversation/contact_id" \
  | jq '.[] | select(.message_type=="image")'

# Should return:
{
  "message_type": "image",
  "media_url": "https://pdffornurenai.blob.core.windows.net/...",
  "media_caption": "...",
  ...
}
```

---

## 📊 Monitoring

### Key Metrics to Watch

**1. Media Upload Success Rate**
```bash
# Check logs for failures
pm2 logs whatsapp-bot-server | grep "Error uploading"

# Should be close to 0%
```

**2. Azure Blob Storage Usage**
```bash
# Check in Azure Portal:
# Storage Account → Monitoring → Metrics
# Metric: Used capacity

# Set alert if usage > 80%
```

**3. Database Query Performance**
```sql
-- Check if new indexes are needed
EXPLAIN ANALYZE
SELECT * FROM interaction_conversation
WHERE message_type = 'image'
AND date_time > NOW() - INTERVAL '7 days';

-- If slow, add index:
CREATE INDEX idx_message_type_date
ON interaction_conversation(message_type, date_time);
```

**4. Frontend Load Time**
```javascript
// Add to chatbot.jsx for monitoring
console.time('media-load');
fetchConversations().then(() => {
  console.timeEnd('media-load');
  // Target: < 2 seconds
});
```

---

## 🔐 Security Checklist

- [ ] Azure SAS token not exposed in frontend code
- [ ] SAS token expiry date noted (2026-11-30)
- [ ] CORS configured to allow only your domain
- [ ] Media URL validation in webhook
- [ ] File size limits implemented (if needed)
- [ ] Content type validation (images, videos only)

---

## 🎯 Success Criteria

✅ **Implementation Successful When:**

1. User sends image → Image displays in chat within 5 seconds
2. User sends video → Video plays in chat
3. User sends voice message → Audio player appears
4. User sends PDF → Document link appears
5. Page refresh → Media still displays (persisted)
6. No errors in:
   - Browser console
   - Node.js logs
   - Django logs
7. Database shows proper media URLs (not null)
8. Azure Blob Storage shows uploaded files

---

## 📝 Post-Deployment Tasks

### Day 1-3: Monitor Closely
- Check logs every few hours
- Monitor Azure Blob usage
- Watch for error patterns
- Collect user feedback

### Week 1: Performance Tuning
- Add indexes if queries are slow
- Enable CDN if media loads slowly
- Compress images if storage grows too fast
- Implement lifecycle policies (auto-delete after X months)

### Week 2: Optimization
- Add lazy loading for images
- Implement thumbnail generation for videos
- Add image compression before upload
- Set up monitoring alerts

---

## 💰 Cost Monitoring

**Azure Blob Storage Costs:**

Expected monthly costs (1000 media/day):
- Storage (60GB): ~₹90
- Transactions: ~₹0.15
- Bandwidth: ~₹480
- **Total: ~₹570/month (~$7 USD)**

**Set up billing alerts:**
```bash
# In Azure Portal:
# Cost Management → Budgets
# Create alert at ₹500/month
```

---

## 🔄 Rollback Plan

**If something goes wrong:**

### 1. Rollback Frontend (Safest)
```bash
# Revert to previous build
git checkout HEAD~1 -- src/Pages/Chatbot/chatbot.jsx
npm run build
# Deploy old build
```

### 2. Rollback Webhook (Medium Risk)
```bash
# Revert webhook changes
git checkout HEAD~1 -- mainwebhook/userWebhook.js
pm2 restart whatsapp-bot-server
```

### 3. Rollback Database (Last Resort)
```bash
# CAUTION: Only if migration causes issues
python manage.py migrate interaction 0006  # Previous migration
```

---

## 📞 Support & References

**Documentation:**
- Full implementation plan: `MEDIA_DISPLAY_FIX_COMPLETE_PLAN.md`
- Executive summary: `MEDIA_FIX_EXECUTIVE_SUMMARY.md`
- This deployment guide: `MEDIA_FIX_DEPLOYMENT_GUIDE.md`

**Logs Locations:**
- Node.js: `pm2 logs whatsapp-bot-server`
- Django: `/var/log/gunicorn/error.log` or `sudo journalctl -u gunicorn`
- Frontend: Browser DevTools → Console

**Azure Resources:**
- Storage Account: `pdffornurenai`
- Container: `pdf`
- Region: (check Azure Portal)

---

## ✅ Final Checklist

Before marking as complete:

- [ ] Migration applied successfully
- [ ] Webhook restarted with new code
- [ ] Django backend restarted
- [ ] Frontend rebuilt and deployed
- [ ] Sent test image → Displays correctly
- [ ] Sent test video → Plays correctly
- [ ] Sent test audio → Plays correctly
- [ ] Database shows media URLs
- [ ] No errors in logs
- [ ] Azure Blob shows uploaded files
- [ ] CORS configured correctly
- [ ] Team notified of changes
- [ ] Documentation updated

---

## 🎉 Congratulations!

Once all steps are complete, your WhatsApp chat will display media beautifully!

**Before:**
```
User: [Image]
Bot: Hello!
User: [Video]
```

**After:**
```
User: 🖼️ [Beautiful image with caption]
Bot: Hello!
User: 🎥 [Video with play button]
```

Your users will love it! 🚀

---

**Deployment Date:** _________________
**Deployed By:** _________________
**Version:** 1.0
**Status:** ✅ Ready for Production
