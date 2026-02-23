# Smart Group Auto-Sync - Complete Guide

## Overview

**Smart Groups now automatically sync with matching contacts once daily!**

Instead of manually clicking "Sync" for each smart group, the system now:
- ✅ Automatically syncs all smart groups every day at a scheduled time
- ✅ Adds new contacts that match the rules
- ✅ Removes contacts that no longer match
- ✅ Provides detailed sync statistics and logging
- ✅ Supports manual triggers for testing

---

## How It Works

### Automatic Daily Sync

1. **Scheduler starts when FastAPI starts** (automatically)
2. **Runs once per day** at configured time (default: 2:00 AM)
3. **Processes all smart groups** across all tenants
4. **Updates membership** based on current contact data
5. **Logs detailed statistics** for monitoring

### What Gets Synced

For each smart group with `auto_rules.enabled = true`:
- ✅ Evaluates all contacts against the group's conditions
- ✅ Adds contacts that now match the rules
- ✅ Removes contacts that no longer match
- ✅ Respects `manual_mode` flag (contacts with manual_mode=true are excluded)
- ✅ Updates the `members` array in the database

---

## Configuration

### Environment Variables (.env)

Add these to your `.env` file:

```env
# Smart Group Auto-Sync Configuration
SMART_GROUP_SYNC_HOUR=2        # Hour to run sync (0-23), default 2 AM
SMART_GROUP_SYNC_MINUTE=0      # Minute to run sync (0-59), default 0
```

### Examples:

```env
# Run at 2:00 AM (default)
SMART_GROUP_SYNC_HOUR=2
SMART_GROUP_SYNC_MINUTE=0

# Run at 3:30 AM
SMART_GROUP_SYNC_HOUR=3
SMART_GROUP_SYNC_MINUTE=30

# Run at midnight
SMART_GROUP_SYNC_HOUR=0
SMART_GROUP_SYNC_MINUTE=0

# Run at 1:00 PM
SMART_GROUP_SYNC_HOUR=13
SMART_GROUP_SYNC_MINUTE=0
```

---

## API Endpoints

### 1. Check Scheduler Status

**GET** `/smart-groups/scheduler/status`

Check if the scheduler is running and when the next sync will happen.

```bash
curl -X GET "http://localhost:8000/smart-groups/scheduler/status" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Response:**
```json
{
  "success": true,
  "scheduler": {
    "running": true,
    "jobs": [
      {
        "id": "daily_smart_group_sync",
        "name": "Daily Smart Group Sync",
        "next_run_time": "2026-01-12T02:00:00",
        "trigger": "cron[hour=2, minute=0]"
      }
    ],
    "scheduler_state": 1
  }
}
```

### 2. Start Scheduler (if not auto-started)

**POST** `/smart-groups/scheduler/start`

Manually start the scheduler with custom time.

```bash
curl -X POST "http://localhost:8000/smart-groups/scheduler/start?hour=3&minute=30" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Parameters:**
- `hour` (optional): Hour to run sync (0-23), default 2
- `minute` (optional): Minute to run sync (0-59), default 0

### 3. Stop Scheduler

**POST** `/smart-groups/scheduler/stop`

Stop the automatic sync scheduler.

```bash
curl -X POST "http://localhost:8000/smart-groups/scheduler/stop" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Note:** The scheduler will auto-restart when FastAPI restarts.

### 4. Manual Sync (All Tenants)

**POST** `/smart-groups/sync-all`

Trigger a manual sync for ALL smart groups across ALL tenants.

```bash
curl -X POST "http://localhost:8000/smart-groups/sync-all" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Response:**
```json
{
  "success": true,
  "message": "Manual sync completed",
  "stats": {
    "total_groups_processed": 15,
    "total_groups_synced": 12,
    "total_contacts_added": 45,
    "total_contacts_removed": 8,
    "errors": 0,
    "tenants_processed": ["tenant1", "tenant2"],
    "duration_seconds": 2.34,
    "sync_details": [...]
  }
}
```

### 5. Manual Sync (Current Tenant Only)

**POST** `/smart-groups/sync-tenant`

Trigger a manual sync for smart groups of the current tenant only.

```bash
curl -X POST "http://localhost:8000/smart-groups/sync-tenant" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Response:**
```json
{
  "success": true,
  "message": "Sync completed for tenant your-tenant-id",
  "stats": {
    "tenant_id": "your-tenant-id",
    "groups_processed": 5,
    "groups_synced": 4,
    "contacts_added": 12,
    "contacts_removed": 3,
    "errors": 0,
    "sync_details": [...]
  }
}
```

---

## Logging and Monitoring

### Log Output

The scheduler logs detailed information:

```
===============================================================================
SMART GROUP AUTO-SYNC STARTED at 2026-01-11 02:00:00
===============================================================================
Found 15 groups with auto_rules
Syncing group: New Customers (ID: abc-123, Tenant: tenant1)
  ✅ Synced: 42 -> 47 members (+5, -0)
Syncing group: VIP Customers (ID: def-456, Tenant: tenant1)
  ✅ Synced: 120 -> 118 members (+0, -2)
...
===============================================================================
SMART GROUP AUTO-SYNC COMPLETED
Duration: 2.34 seconds
Tenants processed: 2
Groups processed: 15
Groups synced: 12
Contacts added: 45
Contacts removed: 8
Errors: 0
===============================================================================
```

### Check Logs

**In production (Azure):**
```bash
az webapp log tail --name fastapiyes --resource-group YOUR_RESOURCE_GROUP
```

**In development:**
```bash
tail -f logs/fastapi.log
# or check console output
```

### Success Indicators

✅ **Healthy sync:**
- `Groups synced` matches `Groups processed` (or close)
- `Errors: 0`
- Duration is reasonable (< 10 seconds for most cases)

❌ **Issues to watch for:**
- High error count
- Very long duration (> 60 seconds)
- Scheduler status shows `"running": false`

---

## How to Test

### Test 1: Manual Sync

1. Create a smart group with simple rules (e.g., created in last 30 days)
2. Trigger manual sync:
   ```bash
   curl -X POST "http://localhost:8000/smart-groups/sync-tenant" \
     -H "X-Tenant-Id: your-tenant-id"
   ```
3. Check the response - should show contacts added
4. Verify in database or frontend that group has members

### Test 2: Check Scheduler Status

```bash
curl -X GET "http://localhost:8000/smart-groups/scheduler/status" \
  -H "X-Tenant-Id: your-tenant-id"
```

Should show:
- `"running": true`
- Next run time in the future

### Test 3: Verify Auto-Sync Works

1. Create a smart group
2. Add some contacts that match the rules
3. Wait for scheduled sync time (or trigger manual sync)
4. Check group members - should be auto-populated

---

## Architecture

### Components

```
┌─────────────────────────────────────┐
│   FastAPI Startup (main.py)        │
│   - Initializes scheduler           │
│   - Reads .env configuration        │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   SmartGroupScheduler               │
│   (whatsapp_tenant/scheduler.py)    │
│   - Manages APScheduler             │
│   - Runs daily at configured time   │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   sync_all_smart_groups()           │
│   - Fetches all smart groups        │
│   - For each group:                 │
│     1. Check if enabled             │
│     2. Get matching contacts        │
│     3. Update members               │
│     4. Log results                  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│   GroupService.sync_group_members() │
│   (whatsapp_tenant/group_service.py)│
│   - Evaluates rules                 │
│   - Updates membership              │
│   - Returns statistics              │
└─────────────────────────────────────┘
```

### Execution Flow

1. **Scheduler triggers** at configured time
2. **Fetches all groups** with `auto_rules` not null
3. **For each group:**
   - Check if `auto_rules.enabled = true`
   - Get all contacts for that tenant
   - Evaluate rules using `RuleEvaluator`
   - Build new members list
   - Update database
   - Log statistics
4. **Log summary** with total statistics

---

## Best Practices

### 1. Choose Off-Peak Time

Run sync during low-traffic hours:
- ✅ Good: 2:00 AM - 4:00 AM
- ⚠️ Okay: 6:00 AM - 8:00 AM
- ❌ Bad: During business hours (users might see lag)

### 2. Monitor Performance

- Check logs after each sync
- Watch for increasing duration
- Alert if errors > 0

### 3. Test Before Production

- Create test smart groups
- Run manual sync first
- Verify results before enabling auto-sync

### 4. Use Manual Mode for Exceptions

If a contact should NEVER be auto-assigned:
- Set `contact.manual_mode = true`
- This contact will be excluded from all auto-syncs

---

## Troubleshooting

### Issue: Scheduler Not Running

**Check:**
```bash
curl -X GET "http://localhost:8000/smart-groups/scheduler/status" \
  -H "X-Tenant-Id: your-tenant-id"
```

**If** `"running": false`:
```bash
# Start it manually
curl -X POST "http://localhost:8000/smart-groups/scheduler/start" \
  -H "X-Tenant-Id: your-tenant-id"
```

**Or** restart FastAPI:
```bash
# Will auto-start on startup
sudo systemctl restart fastapi
```

### Issue: Contacts Not Being Added

**Possible causes:**
1. `auto_rules.enabled = false` - Check group settings
2. Contact has `manual_mode = true` - Check contact settings
3. Rules don't match - Test rules with `/test-rules` endpoint
4. Scheduler not running - Check status

**Debug steps:**
```bash
# 1. Check group has auto_rules enabled
SELECT id, name, auto_rules FROM broadcast_groups WHERE id = 'your-group-id';

# 2. Test rules manually
curl -X POST "http://localhost:8000/broadcast-groups/test-rules" \
  -H "X-Tenant-Id: your-tenant-id" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_rules": {...},
    "limit": 10
  }'

# 3. Trigger manual sync
curl -X POST "http://localhost:8000/smart-groups/sync-tenant" \
  -H "X-Tenant-Id: your-tenant-id"
```

### Issue: Sync Taking Too Long

**If sync duration > 30 seconds:**
1. Check database indexes:
   ```sql
   CREATE INDEX IF NOT EXISTS idx_contacts_tenant ON contacts(tenant_id);
   CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts(created_on);
   ```
2. Reduce number of smart groups
3. Simplify rule conditions
4. Consider running sync less frequently

### Issue: Too Many/Few Contacts in Group

**Verify rules are correct:**
```bash
# Test rules to see what matches
curl -X POST "http://localhost:8000/broadcast-groups/test-rules" \
  -H "X-Tenant-Id: your-tenant-id" \
  -H "Content-Type: application/json" \
  -d '{
    "auto_rules": {
      "enabled": true,
      "logic": "AND",
      "conditions": [
        {
          "type": "date",
          "field": "createdOn",
          "operator": "greater_than",
          "value": "2025-12-01T00:00"
        }
      ]
    },
    "limit": 100
  }'
```

**Common mistakes:**
- Wrong date format (use ISO format: "2025-12-01T00:00")
- Wrong logic ("AND" vs "OR")
- Wrong operator ("greater_than" vs "less_than")

---

## Database Impact

### Performance

**Smart group sync is efficient:**
- ✅ Only updates groups with `auto_rules.enabled = true`
- ✅ Uses bulk operations where possible
- ✅ Processes one group at a time (prevents memory issues)
- ✅ Logs progress for monitoring

**Expected performance:**
- 10 smart groups, 1000 contacts each: ~2-5 seconds
- 50 smart groups, 5000 contacts each: ~10-20 seconds
- 100+ smart groups: Consider running less frequently

### Database Load

**Reads:**
- All groups with auto_rules
- All contacts for tenant (filtered by rules)

**Writes:**
- Updates `members` JSONB field in broadcast_groups
- Commits per group (not per contact)

**Recommendations:**
- Run during off-peak hours
- Monitor database CPU/memory
- Add indexes if needed:
  ```sql
  CREATE INDEX idx_broadcast_groups_auto_rules
  ON broadcast_groups((auto_rules IS NOT NULL));
  ```

---

## Migration from Manual Sync

### Before (Manual):
1. User creates smart group
2. Clicks "Sync" button
3. Group populates
4. **Problem:** Group becomes stale over time

### After (Automatic):
1. User creates smart group
2. **Automatic sync once daily**
3. Group stays up-to-date
4. User can still manually sync if needed

### Migration Steps

1. **Deploy new code** with auto-sync
2. **Verify scheduler is running:**
   ```bash
   curl -X GET "http://localhost:8000/smart-groups/scheduler/status"
   ```
3. **Test with one tenant:**
   ```bash
   curl -X POST "http://localhost:8000/smart-groups/sync-tenant" \
     -H "X-Tenant-Id: test-tenant"
   ```
4. **Monitor logs** for first few days
5. **Keep manual sync button** for user convenience

---

## Advanced Configuration

### Custom Sync Frequency

**Option 1: Daily at specific time (default)**
```python
# In main.py, already configured
SMART_GROUP_SYNC_HOUR=2  # .env
```

**Option 2: Multiple times per day**

Modify `main.py`:
```python
# Run every 12 hours instead of daily
smart_group_scheduler.start_with_interval(hours=12)
```

**Option 3: Per-tenant scheduling**

Create custom endpoint:
```python
@router.post("/smart-groups/schedule-tenant")
async def schedule_tenant_sync(
    hour: int,
    tenant_id: str = Header(None, alias="X-Tenant-Id")
):
    # Implementation left as exercise
    # Would require per-tenant job management
    pass
```

---

## FAQ

### Q: Does this affect manual sync?
**A:** No! Manual sync still works. Auto-sync is just an additional feature.

### Q: Can I disable auto-sync for specific groups?
**A:** Yes! Set `auto_rules.enabled = false` for that group.

### Q: Can I run sync more frequently than daily?
**A:** Yes! Modify `.env` or use `start_with_interval(hours=6)` for every 6 hours.

### Q: What happens if sync fails?
**A:** Error is logged, but other groups still sync. Check logs for details.

### Q: Does this use a lot of resources?
**A:** No! It runs once daily during off-peak hours. Very minimal impact.

### Q: Can I see sync history?
**A:** Check FastAPI logs. Future: Add database table for sync history.

### Q: What if I have 1000+ smart groups?
**A:** Should still work, but consider:
- Running less frequently (e.g., weekly)
- Adding database indexes
- Monitoring performance

---

## Files Modified

1. **whatsapp_tenant/scheduler.py** (NEW)
   - Scheduler service
   - Auto-sync logic
   - Statistics tracking

2. **whatsapp_tenant/router.py**
   - Added scheduler management endpoints
   - Manual sync endpoints

3. **main.py**
   - Initialize scheduler on startup
   - Shutdown scheduler on exit
   - Read .env configuration

---

## Summary

✅ **Auto-sync is now enabled!**

- Smart groups sync automatically once daily
- Runs at 2:00 AM by default (configurable)
- Keeps groups up-to-date without manual intervention
- Comprehensive logging and monitoring
- Manual sync still available for testing

**Next Steps:**
1. Add `SMART_GROUP_SYNC_HOUR=2` to `.env` (optional, 2 is default)
2. Restart FastAPI to start scheduler
3. Check logs to verify first sync
4. Monitor performance for first few days

---

**Implementation Complete:** 2026-01-11
**Status:** ✅ READY FOR PRODUCTION
**Version:** 1.0
