# Quick Migration Checklist

## ✅ Pre-Migration (Current State - COMPLETE)
- [x] Auto-rules feature fully implemented
- [x] Manual mode feature fully implemented
- [x] All manual_mode code commented out with TODO markers
- [x] Frontend reset automation button added
- [x] Header case compatibility fixed (X-Tenant-Id / X-Tenant-ID)
- [x] All files ready for migration

## 🔄 Migration Steps (TODO - Run on Azure)

### Step 1: Run SQL on Azure PostgreSQL
```sql
ALTER TABLE broadcast_groups ADD COLUMN IF NOT EXISTS auto_rules JSON NULL;
ALTER TABLE contacts_contact ADD COLUMN IF NOT EXISTS manual_mode BOOLEAN DEFAULT FALSE NULL;
```

### Step 2: Uncomment Code (Search for "TODO" in these files)
- [ ] `fastAPIWhatsapp_withclaude/contacts/models.py` - Line 25
- [ ] `fastAPIWhatsapp_withclaude/whatsapp_tenant/group_service.py` - Lines 44-45, 88-91
- [ ] `fastAPIWhatsapp_withclaude/contacts/router.py` - Lines 300, 369-370, 390-438

### Step 3: Restart FastAPI
- [ ] Restart Azure App Service

### Step 4: Test Features
- [ ] Test auto-rules: Create group with conditions, verify contacts auto-assigned
- [ ] Test manual mode: Enable for contact, verify NOT auto-assigned
- [ ] Test reset automation: Click reset button, verify rules cleared

---

## Quick SQL Verification Query
After running migrations, verify columns exist:
```sql
SELECT
    t.table_name,
    c.column_name,
    c.data_type
FROM information_schema.columns c
JOIN information_schema.tables t ON c.table_name = t.table_name
WHERE t.table_schema = 'public'
  AND c.column_name IN ('auto_rules', 'manual_mode')
ORDER BY t.table_name, c.column_name;
```

Expected result:
```
table_name        | column_name  | data_type
------------------+--------------+-----------
broadcast_groups  | auto_rules   | json
contacts_contact  | manual_mode  | boolean
```

---

## Files with TODO Comments (Ready for Uncommenting)

Run this to find all TODOs after migration:
```bash
grep -rn "TODO.*manual_mode" fastAPIWhatsapp_withclaude/
```

Current TODOs:
1. `contacts/models.py:25` - Uncomment manual_mode column definition
2. `contacts/router.py:300` - Uncomment manual_mode in contact creation
3. `contacts/router.py:369` - Uncomment manual_mode in contact update
4. `contacts/router.py:390` - Uncomment entire toggle endpoint (lines 390-438)
5. `group_service.py:44` - Uncomment manual_mode filter in sync
6. `group_service.py:88` - Uncomment manual_mode check in auto-assign

---

## New API Endpoints Available

Once migrations complete, these endpoints will be fully functional:

### Auto-Rules Management:
- `PUT /broadcast-groups/{group_id}/rules` - Update group rules
- `POST /broadcast-groups/{group_id}/sync` - Manually sync group members
- `POST /broadcast-groups/test-rules` - Test rules before saving
- `DELETE /broadcast-groups/{group_id}/rules` - Reset automation

### Manual Mode:
- `PATCH /contacts/{contact_id}/manual-mode` - Toggle automation for contact

### Contact Auto-Assignment:
- `POST /contacts/` - Now returns auto_assigned_groups list
- `PUT /contacts/{contact_id}` - Re-evaluates group membership on update
- `PATCH /contacts/{contact_id}` - Re-evaluates group membership on update

---

## Example Auto-Rules JSON

```json
{
  "enabled": true,
  "logic": "AND",
  "conditions": [
    {
      "type": "date",
      "field": "createdOn",
      "operator": "greater_than",
      "value": "2025-01-01T00:00:00Z"
    },
    {
      "type": "text",
      "field": "name",
      "operator": "contains",
      "value": "Premium"
    },
    {
      "type": "custom_field",
      "field": "customField.tier",
      "operator": "equals",
      "value": "gold"
    }
  ]
}
```

---

## Need Help?

See detailed instructions in `MIGRATION_STEPS.md`
