# Smart Group Auto-Sync - Deployment Summary

## ✅ Implementation Complete!

Your smart groups will now automatically sync once daily to keep members up-to-date with matching contacts.

---

## What Was Implemented

### 1. Automatic Scheduler ✅
- **File:** `whatsapp_tenant/scheduler.py` (NEW)
- **Functionality:**
  - Syncs all smart groups daily at configured time
  - Default: 2:00 AM (configurable via .env)
  - Comprehensive logging and error handling
  - Statistics tracking for monitoring

### 2. API Endpoints ✅
- **File:** `whatsapp_tenant/router.py` (MODIFIED)
- **New Endpoints:**
  - `GET /smart-groups/scheduler/status` - Check scheduler status
  - `POST /smart-groups/scheduler/start` - Start scheduler
  - `POST /smart-groups/scheduler/stop` - Stop scheduler
  - `POST /smart-groups/sync-all` - Manual sync (all tenants)
  - `POST /smart-groups/sync-tenant` - Manual sync (current tenant)

### 3. Auto-Start on FastAPI Startup ✅
- **File:** `main.py` (MODIFIED)
- **Functionality:**
  - Scheduler starts automatically when FastAPI starts
  - Reads configuration from .env
  - Graceful shutdown when FastAPI stops

---

## Deployment Steps

### Step 1: Update .env File (Optional)

Add these lines to configure sync time:

```env
# Smart Group Auto-Sync Configuration (Optional - defaults to 2:00 AM)
SMART_GROUP_SYNC_HOUR=2
SMART_GROUP_SYNC_MINUTE=0
```

**Examples:**
- `SMART_GROUP_SYNC_HOUR=3` - Run at 3:00 AM
- `SMART_GROUP_SYNC_HOUR=0` - Run at midnight
- `SMART_GROUP_SYNC_HOUR=13` - Run at 1:00 PM

### Step 2: Restart FastAPI

```bash
# On Azure:
az webapp restart --name fastapiyes --resource-group YOUR_RESOURCE_GROUP

# Or locally:
sudo systemctl restart fastapi

# Or with PM2:
pm2 restart fastapi
```

### Step 3: Verify Scheduler Started

Check the FastAPI logs:

```bash
# Azure:
az webapp log tail --name fastapiyes --resource-group YOUR_RESOURCE_GROUP

# Look for this line:
# ✅ Smart Group Auto-Sync Scheduler started (daily at 02:00)
```

Or use the API:

```bash
curl -X GET "http://localhost:8000/smart-groups/scheduler/status" \
  -H "X-Tenant-Id: your-tenant-id"

# Should return:
{
  "success": true,
  "scheduler": {
    "running": true,
    "jobs": [...]
  }
}
```

### Step 4: Test with Manual Sync

Trigger a manual sync to test:

```bash
curl -X POST "http://localhost:8000/smart-groups/sync-tenant" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Expected response:**
```json
{
  "success": true,
  "message": "Sync completed for tenant your-tenant-id",
  "stats": {
    "groups_processed": 5,
    "groups_synced": 4,
    "contacts_added": 12,
    "contacts_removed": 3,
    "errors": 0
  }
}
```

---

## How It Works

### Daily Auto-Sync

1. **Scheduler runs** at configured time (default 2:00 AM)
2. **Fetches all smart groups** with `auto_rules.enabled = true`
3. **For each group:**
   - Get all contacts for that tenant
   - Evaluate rules to find matches
   - Update members list
   - Log results
4. **Logs summary** with total statistics

### What Gets Synced

- ✅ Adds contacts that now match the rules
- ✅ Removes contacts that no longer match
- ✅ Respects `manual_mode` (excluded from auto-sync)
- ✅ Works across all tenants

---

## User Experience

### Before (Manual Sync):
1. User creates smart group
2. Clicks "Sync" button
3. Group populates
4. **Problem:** Group becomes stale as new contacts are added

### After (Auto-Sync):
1. User creates smart group
2. **Syncs automatically every day**
3. Group stays current
4. Manual sync still available for immediate updates

---

## Monitoring

### Check Scheduler Status

```bash
curl -X GET "http://localhost:8000/smart-groups/scheduler/status" \
  -H "X-Tenant-Id: your-tenant-id"
```

### View Logs

Auto-sync logs detailed information:

```
===============================================================================
SMART GROUP AUTO-SYNC STARTED at 2026-01-11 02:00:00
===============================================================================
Found 15 groups with auto_rules
Syncing group: New Customers (ID: abc-123, Tenant: tenant1)
  ✅ Synced: 42 -> 47 members (+5, -0)
...
===============================================================================
SMART GROUP AUTO-SYNC COMPLETED
Duration: 2.34 seconds
Groups processed: 15
Groups synced: 12
Contacts added: 45
Contacts removed: 8
Errors: 0
===============================================================================
```

---

## API Endpoints Reference

### 1. Get Scheduler Status
```bash
GET /smart-groups/scheduler/status
Headers: X-Tenant-Id: your-tenant-id
```

### 2. Start Scheduler
```bash
POST /smart-groups/scheduler/start?hour=2&minute=0
Headers: X-Tenant-Id: your-tenant-id
```

### 3. Stop Scheduler
```bash
POST /smart-groups/scheduler/stop
Headers: X-Tenant-Id: your-tenant-id
```

### 4. Manual Sync (All Tenants)
```bash
POST /smart-groups/sync-all
Headers: X-Tenant-Id: your-tenant-id
```

### 5. Manual Sync (Current Tenant)
```bash
POST /smart-groups/sync-tenant
Headers: X-Tenant-Id: your-tenant-id
```

---

## Troubleshooting

### Issue: Scheduler Not Running

**Solution 1: Restart FastAPI**
```bash
sudo systemctl restart fastapi
```

**Solution 2: Start Manually**
```bash
curl -X POST "http://localhost:8000/smart-groups/scheduler/start" \
  -H "X-Tenant-Id: your-tenant-id"
```

### Issue: Contacts Not Being Added

**Check:**
1. Is `auto_rules.enabled = true`?
2. Does contact match the rules?
3. Is `contact.manual_mode = false`?

**Test rules:**
```bash
curl -X POST "http://localhost:8000/broadcast-groups/test-rules" \
  -H "X-Tenant-Id: your-tenant-id" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_rules": {...your rules...},
    "limit": 10
  }'
```

### Issue: Sync Taking Too Long

**If duration > 30 seconds:**
- Add database indexes
- Reduce number of smart groups
- Run less frequently (e.g., every 2 days)

---

## Files Modified Summary

| File | Status | Purpose |
|------|--------|---------|
| `whatsapp_tenant/scheduler.py` | ✅ NEW | Scheduler service with auto-sync logic |
| `whatsapp_tenant/router.py` | ✅ MODIFIED | Added scheduler management endpoints |
| `main.py` | ✅ MODIFIED | Initialize scheduler on startup |

**Total:** 3 files (1 new, 2 modified)

---

## Configuration Options

### .env Variables

```env
# Optional - Default is 2:00 AM
SMART_GROUP_SYNC_HOUR=2        # Hour (0-23)
SMART_GROUP_SYNC_MINUTE=0      # Minute (0-59)
```

### Common Configurations

```env
# Run at 2:00 AM (default)
SMART_GROUP_SYNC_HOUR=2
SMART_GROUP_SYNC_MINUTE=0

# Run at midnight
SMART_GROUP_SYNC_HOUR=0

# Run at 3:30 AM
SMART_GROUP_SYNC_HOUR=3
SMART_GROUP_SYNC_MINUTE=30

# Run at noon
SMART_GROUP_SYNC_HOUR=12
SMART_GROUP_SYNC_MINUTE=0
```

---

## Performance Impact

### Resources Used

- ✅ **Minimal CPU:** Runs once daily during off-peak hours
- ✅ **Minimal Memory:** Processes one group at a time
- ✅ **Database:** Read-heavy, minimal writes

### Expected Performance

- **10 groups, 1000 contacts:** ~2-5 seconds
- **50 groups, 5000 contacts:** ~10-20 seconds
- **100+ groups:** Consider less frequent syncs

### Best Practices

1. **Run during off-peak hours** (2:00 AM - 4:00 AM)
2. **Monitor first few syncs** to establish baseline
3. **Add database indexes** if needed
4. **Alert on errors** using log monitoring

---

## Success Criteria

After deployment, verify:

✅ **Scheduler is running:**
```bash
curl GET /smart-groups/scheduler/status
# Returns: "running": true
```

✅ **Manual sync works:**
```bash
curl POST /smart-groups/sync-tenant
# Returns: stats with contacts added/removed
```

✅ **Logs show next run time:**
```
✅ Smart Group Auto-Sync Scheduler started (daily at 02:00)
Next run: 2026-01-12T02:00:00
```

✅ **Smart groups populate automatically:**
- Create a smart group with simple rules
- Wait for scheduled sync (or trigger manually)
- Group has matching contacts

---

## Rollback Plan

If you need to disable auto-sync:

### Option 1: Stop Scheduler via API
```bash
curl -X POST "http://localhost:8000/smart-groups/scheduler/stop" \
  -H "X-Tenant-Id: your-tenant-id"
```

### Option 2: Comment Out Auto-Start

In `main.py`, comment out the scheduler initialization:

```python
# Startup code
# try:
#     from whatsapp_tenant.scheduler import smart_group_scheduler
#     ...
#     smart_group_scheduler.start(...)
# except Exception as e:
#     ...
```

Then restart FastAPI.

### Option 3: Disable Specific Groups

Set `auto_rules.enabled = false` for groups you don't want to sync.

---

## Next Steps

1. **✅ Deploy to production** (restart FastAPI)
2. **Monitor logs** for first sync
3. **Check scheduler status** via API
4. **Test manual sync** to verify functionality
5. **Document for team** (share this guide)

---

## Documentation

- **Complete Guide:** `SMART_GROUP_AUTO_SYNC_GUIDE.md`
- **Deployment Summary:** This file
- **API Reference:** See complete guide

---

## Support

**Logs location:**
- Azure: `az webapp log tail --name fastapiyes`
- Local: Check console output or `/var/log/fastapi.log`

**API for help:**
- `GET /smart-groups/scheduler/status` - Check if running
- `POST /smart-groups/sync-tenant` - Test sync manually

---

**Deployment Date:** _________________
**Deployed By:** _________________
**Status:** ✅ READY FOR PRODUCTION

---

## Summary

🎉 **Smart Group Auto-Sync is now implemented!**

- Syncs automatically once daily
- Keeps groups up-to-date
- Comprehensive logging
- Manual override available
- Zero user intervention needed

**Just restart FastAPI and you're done!** 🚀
