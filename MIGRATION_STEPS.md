# Database Migration Steps for Auto-Rules and Manual Mode

## Current Status
- ✅ All code is written and ready
- ❌ Database columns don't exist yet
- 🔒 Manual mode code is commented out to prevent errors

## Step 1: Run Database Migrations on Azure

### SQL Commands to Execute:
```sql
-- Add auto_rules column to broadcast_groups
ALTER TABLE broadcast_groups ADD COLUMN IF NOT EXISTS auto_rules JSON NULL;

-- Add manual_mode column to contacts_contact
ALTER TABLE contacts_contact ADD COLUMN IF NOT EXISTS manual_mode BOOLEAN DEFAULT FALSE NULL;

-- Verify columns were added
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'broadcast_groups' AND column_name = 'auto_rules';

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'contacts_contact' AND column_name = 'manual_mode';
```

### How to Run on Azure:
1. Go to Azure Portal → Your PostgreSQL server
2. Navigate to "Query editor"
3. Connect with admin credentials
4. Paste and execute the SQL above
5. Verify both SELECT queries return one row each

## Step 2: Uncomment Manual Mode Code

After migrations succeed, uncomment these sections:

### File 1: `fastAPIWhatsapp_withclaude/contacts/models.py`

**Line 25** - Uncomment the manual_mode column:
```python
# Currently commented:
# manual_mode = Column(Boolean, default=False, nullable=True)  # TODO: Add this column to database first

# Change to:
manual_mode = Column(Boolean, default=False, nullable=True)
```

### File 2: `fastAPIWhatsapp_withclaude/whatsapp_tenant/group_service.py`

**Lines 44-45** - Uncomment manual_mode filter in sync_group_members:
```python
# Currently commented:
# Filter out contacts with manual_mode enabled
# TODO: Uncomment when manual_mode column is added to database
# matching_contacts = [c for c in matching_contacts if not c.manual_mode]

# Change to:
# Filter out contacts with manual_mode enabled
matching_contacts = [c for c in matching_contacts if not c.manual_mode]
```

**Lines 88-91** - Uncomment manual_mode check in auto_assign_contact_to_groups:
```python
# Currently commented:
# Skip if contact has manual mode enabled
# TODO: Uncomment when manual_mode column is added to database
# if contact.manual_mode:
#     logger.info(f"Contact {contact.phone} has manual_mode enabled, skipping auto-assignment")
#     return []

# Change to:
# Skip if contact has manual mode enabled
if contact.manual_mode:
    logger.info(f"Contact {contact.phone} has manual_mode enabled, skipping auto-assignment")
    return []
```

### File 3: `fastAPIWhatsapp_withclaude/contacts/router.py`

**Line 300** - Uncomment manual_mode in create_contact:
```python
# Currently commented:
# manual_mode=body.get('manual_mode', False)  # TODO: Uncomment when column is added to database

# Change to:
manual_mode=body.get('manual_mode', False)
```

**Lines 369-370** - Uncomment manual_mode in update_single_contact:
```python
# Currently commented:
# if 'manual_mode' in body:  # TODO: Uncomment when column is added to database
#     contact.manual_mode = body['manual_mode']

# Change to:
if 'manual_mode' in body:
    contact.manual_mode = body['manual_mode']
```

**Lines 390-438** - Uncomment the entire toggle_manual_mode endpoint:
```python
# Remove the comment block markers from the entire function
# Change this:
# TODO: Uncomment when manual_mode column is added to database
# @router.patch("/contacts/{contact_id}/manual-mode")
# async def toggle_manual_mode(...):
#     ...

# To this:
@router.patch("/contacts/{contact_id}/manual-mode")
async def toggle_manual_mode(
    contact_id: int,
    request: Request,
    db: orm.Session = Depends(get_db)
):
    """Toggle manual mode for a contact to disable/enable automation"""
    # ... (rest of function code)
```

## Step 3: Restart FastAPI Server

After uncommenting all code:
```bash
# If running locally with uvicorn:
# Press Ctrl+C to stop, then restart

# On Azure App Service:
# Go to Azure Portal → Your App Service → Restart
```

## Step 4: Verify Functionality

### Test Auto-Rules:
1. Create a broadcast group with auto-rules (e.g., "contacts created after 2025-01-01")
2. Verify existing matching contacts are added to the group
3. Create a new contact that matches the rules
4. Verify the contact is automatically added to the group

### Test Manual Mode:
1. Select a contact and enable manual_mode via API:
   ```bash
   PATCH /contacts/{contact_id}/manual-mode
   Body: {"manual_mode": true}
   ```
2. Create a new group with rules that match this contact
3. Verify the contact is NOT added to the group (manual mode prevents auto-assignment)
4. Disable manual_mode for the contact
5. Re-sync the group and verify the contact is now added

### Test Reset Automation:
1. Go to Groups page in frontend
2. Hover over a group with auto-rules
3. Click the reset automation button (RotateCcw icon)
4. Verify group rules are cleared but members remain

## Troubleshooting

### If "column already exists" error:
- Columns were already added, safe to proceed to Step 2

### If "permission denied" error:
- Make sure you're using the admin/owner account for PostgreSQL
- Check Azure RBAC permissions for the database

### If FastAPI still shows errors after uncommenting:
- Verify migrations actually completed (run the SELECT queries)
- Clear any cached connections: Restart the FastAPI server
- Check Azure logs for specific error messages

## Files Modified in This Implementation

- ✅ `fastAPIWhatsapp_withclaude/whatsapp_tenant/models.py` - Added auto_rules column
- ✅ `fastAPIWhatsapp_withclaude/whatsapp_tenant/schema.py` - Added rule validation schemas
- ✅ `fastAPIWhatsapp_withclaude/whatsapp_tenant/rule_engine.py` - NEW: Rule evaluation logic
- ✅ `fastAPIWhatsapp_withclaude/whatsapp_tenant/group_service.py` - NEW: Group sync service
- ✅ `fastAPIWhatsapp_withclaude/whatsapp_tenant/router.py` - Added rule management endpoints
- ✅ `fastAPIWhatsapp_withclaude/contacts/models.py` - Added manual_mode column (commented)
- ✅ `fastAPIWhatsapp_withclaude/contacts/router.py` - Added auto-assignment integration
- ✅ `whatsappBusinessAutomation_withclaude/src/Pages/Chatbot/Broadcast/GroupPopup.jsx` - Added reset button
- ✅ `whatsappBusinessAutomation_withclaude/src/api.jsx` - Fixed header case
- ✅ `fastAPIWhatsapp_withclaude/main.py` - Added header case compatibility
