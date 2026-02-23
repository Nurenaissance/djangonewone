# Azure Database Migration Checklist

You have **3 database migrations** to run on Azure PostgreSQL. Here's the complete checklist:

---

## ✅ Migration 1: Analytics Tables (Node.js Backend)

**Issue**: `relation "message_events" does not exist`, `relation "hourly_analytics" does not exist`
**File**: `CREATE_ANALYTICS_TABLES_COMPLETE.sql` (in project root)

### Steps:
1. Go to **Azure Portal** → Your PostgreSQL server
2. Navigate to **Query editor**
3. Copy entire contents of `CREATE_ANALYTICS_TABLES_COMPLETE.sql`
4. Paste and execute
5. Verify with:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_name IN ('message_events', 'button_clicks', 'hourly_analytics', 'template_analytics_daily', 'campaign_analytics')
   ORDER BY table_name;
   ```

**Expected Result**: Should return 5 rows showing all analytics tables exist

---

## ✅ Migration 2: Auto-Rules & Manual Mode (FastAPI Backend)

**Issue**: `column broadcast_groups.auto_rules does not exist` & `column contacts_contact.manual_mode does not exist`
**File**: See SQL below

### SQL to Run:
```sql
-- Add auto_rules column to broadcast_groups
ALTER TABLE broadcast_groups ADD COLUMN IF NOT EXISTS auto_rules JSON NULL;

-- Add manual_mode column to contacts_contact
ALTER TABLE contacts_contact ADD COLUMN IF NOT EXISTS manual_mode BOOLEAN DEFAULT FALSE NULL;

-- Verify columns were added
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_name IN ('broadcast_groups', 'contacts_contact')
  AND column_name IN ('auto_rules', 'manual_mode')
ORDER BY table_name, column_name;
```

**Expected Result**: Should return 2 rows:
- `broadcast_groups | auto_rules | json`
- `contacts_contact | manual_mode | boolean`

---

## ✅ Post-Migration Step 3: Uncomment Manual Mode Code

**ONLY AFTER migrations succeed**, uncomment these sections:

### File 1: `fastAPIWhatsapp_withclaude/contacts/models.py`
**Line 25** - Uncomment:
```python
manual_mode = Column(Boolean, default=False, nullable=True)
```

### File 2: `fastAPIWhatsapp_withclaude/whatsapp_tenant/group_service.py`
**Lines 44-45** - Uncomment:
```python
# Filter out contacts with manual_mode enabled
matching_contacts = [c for c in matching_contacts if not c.manual_mode]
```

**Lines 88-91** - Uncomment:
```python
# Skip if contact has manual mode enabled
if contact.manual_mode:
    logger.info(f"Contact {contact.phone} has manual_mode enabled, skipping auto-assignment")
    return []
```

### File 3: `fastAPIWhatsapp_withclaude/contacts/router.py`
**Line 300** - Uncomment:
```python
manual_mode=body.get('manual_mode', False)
```

**Lines 369-370** - Uncomment:
```python
if 'manual_mode' in body:
    contact.manual_mode = body['manual_mode']
```

**Lines 390-438** - Uncomment entire endpoint (toggle_manual_mode function)

---

## ✅ Step 4: Restart Services

After all migrations and code changes:

### Restart FastAPI (Required for route order fix)
```bash
# Azure Portal → App Service (fastapione) → Restart
```

### Restart Node.js (If running)
```bash
# Azure Portal → App Service (whatsapp_bot_server) → Restart
```

---

## 🧪 Verification Tests

### Test 1: Analytics Table
**Endpoint**: Your Node.js analytics logs endpoint
**Expected**: Should return logs array (not "message_events does not exist")

### Test 2: Notifications Clear All
**Endpoint**: `DELETE /notifications/all?confirm=true`
**Expected**: Should return success (not "unable to parse string as an integer")

### Test 3: Smart Groups
**Frontend**: Open Groups → Smart Group tab
**Expected**: Should be able to create smart groups with auto-rules

### Test 4: Manual Mode
**Frontend**: Should see manual mode toggle on contacts (after uncommenting code)
**Expected**: Contacts with manual_mode=true are excluded from auto-groups

---

## 📝 Summary of Changes

| Component | Table/Column | Status |
|-----------|-------------|--------|
| Node.js Analytics | `message_events` table | ❌ Missing |
| Node.js Analytics | `button_clicks` table | ❌ Missing |
| Node.js Analytics | `hourly_analytics` table | ❌ Missing |
| Node.js Analytics | `template_analytics_daily` table | ❌ Missing |
| Node.js Analytics | `campaign_analytics` table | ❌ Missing |
| FastAPI Smart Groups | `broadcast_groups.auto_rules` | ❌ Missing |
| FastAPI Manual Mode | `contacts_contact.manual_mode` | ❌ Missing |
| FastAPI Routes | Route ordering fix | ⚠️ Needs restart |

---

## 🚨 Important Notes

1. **Run migrations in order** - Don't skip steps
2. **Verify each migration** before proceeding to next
3. **Don't uncomment code** until migrations succeed
4. **Restart servers** after all changes
5. **Test thoroughly** after restart

---

## 💡 Quick Copy-Paste Commands

### All Migrations in One Block:

**IMPORTANT**: Use the complete SQL file instead: `CREATE_ANALYTICS_TABLES_COMPLETE.sql`

Or copy this quick version (includes all tables):

```sql
-- Migration 1: ALL Analytics Tables (message_events, button_clicks, hourly_analytics, template_analytics_daily, campaign_analytics)
-- See CREATE_ANALYTICS_TABLES_COMPLETE.sql for the full version with indexes, triggers, and views

-- Migration 2: Auto-Rules & Manual Mode
ALTER TABLE broadcast_groups ADD COLUMN IF NOT EXISTS auto_rules JSON NULL;
ALTER TABLE contacts_contact ADD COLUMN IF NOT EXISTS manual_mode BOOLEAN DEFAULT FALSE NULL;

-- Quick Verify (run after full migration)
SELECT 'message_events' as table_name, COUNT(*) as exists FROM information_schema.tables WHERE table_name = 'message_events'
UNION ALL SELECT 'button_clicks', COUNT(*) FROM information_schema.tables WHERE table_name = 'button_clicks'
UNION ALL SELECT 'hourly_analytics', COUNT(*) FROM information_schema.tables WHERE table_name = 'hourly_analytics'
UNION ALL SELECT 'template_analytics_daily', COUNT(*) FROM information_schema.tables WHERE table_name = 'template_analytics_daily'
UNION ALL SELECT 'campaign_analytics', COUNT(*) FROM information_schema.tables WHERE table_name = 'campaign_analytics'
UNION ALL SELECT 'auto_rules column', COUNT(*) FROM information_schema.columns WHERE table_name = 'broadcast_groups' AND column_name = 'auto_rules'
UNION ALL SELECT 'manual_mode column', COUNT(*) FROM information_schema.columns WHERE table_name = 'contacts_contact' AND column_name = 'manual_mode';
```

**Expected Result**: All rows should show `1` in the exists column

**⚠️ RECOMMENDED**: Use the complete file `CREATE_ANALYTICS_TABLES_COMPLETE.sql` which includes:
- All 5 analytics tables
- Proper indexes for performance
- Auto-update triggers
- Helper views
- Verification queries

---

Good luck! 🚀
