# Smart Groups Debug Guide

## Problem: Smart groups showing 0 contacts

Follow these steps to diagnose and fix the issue.

## Step 1: Restart FastAPI Server ⚠️ CRITICAL

The Contact model was fixed to use the correct data type. You **MUST** restart the server for changes to take effect:

```bash
# Azure App Service - restart via portal or CLI
az webapp restart --name fastapiyes --resource-group YOUR_RESOURCE_GROUP

# Or restart via Azure Portal:
# Go to App Service → fastapiyes → Restart
```

**Wait 2-3 minutes** for the server to fully restart before testing.

## Step 2: Verify Contacts Exist (Debug Endpoint)

Test this endpoint to see if contacts are being found at all:

```bash
curl -X GET "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/broadcast-groups/debug-contacts" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "tenant_id": "ai",
  "tenant_id_type": "str",
  "total_contacts_in_sample": 20,
  "contacts": [
    {
      "id": 123,
      "phone": "+919876543210",
      "name": "John Doe",
      "createdOn": "2025-01-05T10:30:00",
      "createdOn_type": "datetime",
      "tenant_id": "ai",
      "tenant_id_type": "str"
    }
  ]
}
```

### If You Get 0 Contacts:

**Problem:** Tenant ID mismatch between database and API request.

**Solution:** Run this SQL in Azure PostgreSQL Query Editor:

```sql
-- Check what tenant_id values exist
SELECT DISTINCT tenant_id, COUNT(*) as contact_count
FROM contacts_contact
GROUP BY tenant_id
ORDER BY contact_count DESC;

-- Check if your tenant_id exists
SELECT * FROM contacts_contact
WHERE tenant_id = 'ai'  -- Change 'ai' to your tenant_id
LIMIT 5;
```

If tenant_id doesn't match, update your API header to use the correct value.

## Step 3: Check Database Schema

Run this in Azure PostgreSQL to verify column types:

```sql
-- Check contacts_contact schema
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'contacts_contact'
  AND column_name IN ('tenant_id', 'createdOn');

-- Should show:
-- tenant_id    | character varying | 50
-- createdOn    | timestamp without time zone | NULL
```

### If tenant_id is INTEGER:

This is the problem! The SQLAlchemy model expects String but database has Integer.

**Fix Option 1 - Change Model (if database can't be changed):**
```python
# In fastAPIWhatsapp_withclaude/contacts/models.py
tenant_id = Column(Integer, ForeignKey("tenant_tenant.id"), nullable=True)
```

**Fix Option 2 - Change Database (recommended):**
```sql
-- Backup first!
-- Then alter the column type
ALTER TABLE contacts_contact
ALTER COLUMN tenant_id TYPE VARCHAR(50);
```

## Step 4: Test with Simple Rules

After confirming contacts exist, test with a simple rule first:

```bash
curl -X POST "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/broadcast-groups/test-rules" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": {
      "enabled": true,
      "logic": "AND",
      "conditions": []
    }
  }'
```

**Expected:** Should match all contacts (since no conditions).

## Step 5: Test Date Range Rules

Now test your actual date rules:

```bash
curl -X POST "https://fastapiyes-avaaadfjgzafe6ff.canadacentral-01.azurewebsites.net/broadcast-groups/test-rules" \
  -H "X-Tenant-Id: ai" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": {
      "enabled": true,
      "logic": "AND",
      "conditions": [
        {
          "type": "date",
          "field": "createdOn",
          "operator": "greater_than",
          "value": "2024-11-30T22:45"
        },
        {
          "type": "date",
          "field": "createdOn",
          "operator": "less_than",
          "value": "2026-01-09T23:46"
        }
      ]
    }
  }'
```

## Step 6: Check Logs

Check your FastAPI logs for detailed debugging info:

```bash
# Azure App Service logs
az webapp log tail --name fastapiyes --resource-group YOUR_RESOURCE_GROUP

# Look for:
# - "Fetching contacts for tenant_id=..."
# - "Total contacts found: X"
# - "Sample contacts (first 5):"
# - "Evaluating contact X: field=createdOn, actual=..., operator=..., expected=..."
# - "Date comparison: ... > ... = True/False"
```

## Common Issues & Fixes

### Issue 1: tenant_id Type Mismatch
**Symptom:** debug-contacts returns 0 contacts
**Fix:** Ensure Contact model tenant_id type matches database

### Issue 2: createdOn is NULL
**Symptom:** All contacts filtered out
**Check:**
```sql
SELECT COUNT(*) FROM contacts_contact WHERE "createdOn" IS NULL;
```
**Fix:** Update NULL values:
```sql
UPDATE contacts_contact
SET "createdOn" = NOW()
WHERE "createdOn" IS NULL;
```

### Issue 3: Timezone Mismatch
**Symptom:** Dates close to boundaries fail
**Fix:** Already handled in code - datetimes are compared timezone-naive

### Issue 4: Date Format Not Recognized
**Symptom:** Logs show "Failed to parse datetime"
**Fix:** Use format `YYYY-MM-DDTHH:MM` (e.g., `2024-11-30T22:45`)

## Fixes Applied in This Update

1. **Enhanced datetime parsing** (rule_engine.py):
   - Now handles format: `2024-11-30T22:45` (your frontend format)
   - Supports 7 different datetime formats
   - Removes timezone info for consistent comparison

2. **Timezone handling** (rule_engine.py):
   - Compares all datetimes as timezone-naive
   - Prevents timezone-aware vs naive comparison errors

3. **Better logging** (rule_engine.py, router.py):
   - Shows which format was used to parse dates
   - Logs all date comparisons
   - Shows why contacts match or don't match

4. **Debug endpoint** (router.py):
   - `/broadcast-groups/debug-contacts` - verify contacts exist
   - Shows actual data types
   - Returns sample contacts with dates

## Next Steps

1. ✅ Restart FastAPI server
2. ✅ Test `/broadcast-groups/debug-contacts` endpoint
3. ✅ Share the debug-contacts response if still 0
4. ✅ Test `/broadcast-groups/test-rules` with empty conditions first
5. ✅ Test with your actual date rules
6. ✅ Check logs for detailed debugging info

## If Still Not Working

Share the following:

1. Response from `/broadcast-groups/debug-contacts`
2. Your test-rules request body
3. Your test-rules response
4. FastAPI server logs (last 50 lines)
5. SQL result from:
   ```sql
   SELECT id, phone, name, "createdOn", tenant_id
   FROM contacts_contact
   WHERE tenant_id = 'ai'  -- your tenant
   LIMIT 5;
   ```

This will help identify the exact issue!
