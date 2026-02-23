# Fix: hourly_analytics table does not exist

## Error You're Seeing

```
❌ [Analytics] Error updating hourly analytics: error: relation "hourly_analytics" does not exist
```

## Root Cause

The `hourly_analytics` table (and other analytics tables) haven't been created in your Azure PostgreSQL database yet.

---

## Quick Fix (5 minutes)

### Step 1: Open Azure Portal
1. Go to **Azure Portal** (portal.azure.com)
2. Navigate to your **PostgreSQL flexible server**
3. Click on **Query editor** in the left sidebar

### Step 2: Run the Migration SQL

**Option A: Use the Complete File (RECOMMENDED)**
1. Open the file: `CREATE_ANALYTICS_TABLES_COMPLETE.sql` (in your project root)
2. Copy **ALL** the contents (Ctrl+A, Ctrl+C)
3. Paste into Azure Query Editor
4. Click **Run** or press F5

**Option B: Quick Manual Script**
Copy and paste this into Azure Query Editor:

```sql
-- Create hourly_analytics table
CREATE TABLE IF NOT EXISTS hourly_analytics (
    id BIGSERIAL PRIMARY KEY,
    tenant_id VARCHAR(255) NOT NULL,
    hour_start TIMESTAMP WITH TIME ZONE NOT NULL,
    total_sent INTEGER DEFAULT 0,
    total_delivered INTEGER DEFAULT 0,
    total_read INTEGER DEFAULT 0,
    total_failed INTEGER DEFAULT 0,
    total_replied INTEGER DEFAULT 0,
    total_button_clicks INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 4) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (tenant_id, hour_start)
);

-- Add index for performance
CREATE INDEX IF NOT EXISTS idx_hourly_analytics_tenant_hour
ON hourly_analytics(tenant_id, hour_start);

-- Add auto-update trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_hourly_analytics_updated_at ON hourly_analytics;
CREATE TRIGGER update_hourly_analytics_updated_at
BEFORE UPDATE ON hourly_analytics
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Step 3: Verify the Table Was Created

Run this verification query:

```sql
SELECT table_name,
       (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'hourly_analytics') as column_count
FROM information_schema.tables
WHERE table_name = 'hourly_analytics';
```

**Expected Result**:
- 1 row returned
- `table_name`: hourly_analytics
- `column_count`: 12 (or more)

### Step 4: Restart Your Node.js Server

If the server is running on Azure App Service:
1. Go to **Azure Portal** → **App Services**
2. Find your **whatsapp_bot_server** app
3. Click **Restart**
4. Wait 30-60 seconds for restart to complete

If running locally:
```bash
# Stop the server (Ctrl+C)
# Then restart
npm start
```

---

## Verify the Fix

After restarting, check your Node.js logs. You should see:
- ✅ No more "hourly_analytics does not exist" errors
- ✅ Analytics updates working successfully

---

## What This Table Does

`hourly_analytics` stores aggregated message statistics per hour:
- Total messages sent/delivered/read/failed
- Button clicks
- Cost tracking
- Used for real-time analytics dashboard

---

## Other Missing Tables?

If you see errors for other analytics tables, run the **complete migration**:

**File**: `CREATE_ANALYTICS_TABLES_COMPLETE.sql`

This creates ALL analytics tables:
1. `message_events` - Individual message tracking
2. `button_clicks` - Button interaction tracking
3. `hourly_analytics` - Hourly aggregations
4. `template_analytics_daily` - Daily template stats
5. `campaign_analytics` - Campaign performance

---

## Troubleshooting

### "Permission denied" error
**Solution**: Make sure you're logged in with admin credentials in Query Editor

### "Function already exists" warning
**Solution**: This is OK! The function will be replaced with the new version

### Table created but still getting errors
**Solution**:
1. Verify table exists: `SELECT * FROM hourly_analytics LIMIT 1;`
2. Restart your Node.js server
3. Check server logs for new errors

### Need to delete and recreate?
```sql
DROP TABLE IF EXISTS hourly_analytics CASCADE;
-- Then run the CREATE TABLE script again
```

---

## Full Migration Checklist

For a complete setup, see: `AZURE_MIGRATION_CHECKLIST.md`

This includes:
- All analytics tables
- Smart groups (auto_rules column)
- Manual mode (manual_mode column)
- Service restarts

---

## Success Confirmation

You'll know it's working when:
- ✅ No errors in Node.js logs about hourly_analytics
- ✅ Can query the table: `SELECT COUNT(*) FROM hourly_analytics;`
- ✅ Analytics dashboard updates without errors
- ✅ New analytics data appears in the table

---

Need help? Check the main migration guide: `AZURE_MIGRATION_CHECKLIST.md`
