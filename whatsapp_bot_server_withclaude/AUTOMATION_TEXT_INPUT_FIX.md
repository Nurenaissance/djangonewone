# Automation Text Input Fix for Tenant ehgymjv

## Issue Description
For tenant `ehgymjv` and certain phone numbers (e.g., 919021404255), when users input text for name and address fields, the automation keeps repeating the same questions. Only audio inputs were being accepted and properly advancing the flow.

## Root Cause Analysis

### The Problem
1. When a flow node asks for input (name/address), it sets `inputVariable` in the session
2. **Race condition**: Between setting `inputVariable` and receiving the user's text response, the variable was getting lost/cleared
3. When text arrived, `handleInput` checked for `inputVariable` but found it NULL
4. Result: User input was **not stored**, flow advanced but without saving the data
5. Next iteration asked for the same input again → **infinite loop**

### Why Audio Worked But Text Didn't
Looking at `userWebhook.js` lines 1069-1089:
- **Audio messages** have explicit auto-advancement logic that moves to the next node regardless of inputVariable
- **Text messages** rely on proper inputVariable handling to record the input before advancing
- If inputVariable is missing, text input fails silently while audio still advances

## Fixes Applied

### Fix 1: Early InputVariable Recovery (lines ~109-140)
**Location**: `mainwebhook/userWebhook.js`

Added logic to recover `inputVariable` from the current node configuration when loading a session:

```javascript
// If inputVariable is missing from session, check the current node
if (!userSession.inputVariable) {
  let currNodeData, nodeType;

  // Handle both legacy (flowData) and V2 (nodes) flows
  if (userSession.flowVersion === 2) {
    currNodeData = userSession.nodes?.find(n => n.id === userSession.currNode)?.data;
    nodeType = userSession.nodes?.find(n => n.id === userSession.currNode)?.type;
  } else {
    currNodeData = userSession.flowData?.[userSession.currNode];
    nodeType = currNodeData?.type;
  }

  // Recover variable from node configuration
  const inputNodeTypes = ['Text', 'Button', 'List', 'askQuestion'];
  if (inputNodeTypes.includes(nodeType) && currNodeData?.variable) {
    userSession.inputVariable = currNodeData.variable;
    userSession.inputVariableType = currNodeData.dataType || 'text';
    await userSessions.set(sessionKey, userSession);
  }
}
```

### Fix 2: Pre-Input Handling Check (lines ~645-665)
**Location**: `mainwebhook/userWebhook.js` (before `handleInput` call)

Added safety check right before processing text input:

```javascript
// For text messages, ensure inputVariable is set before handling input
if (message_type === "text" && !userSession.inputVariable) {
  // Same recovery logic as Fix 1
  // Checks current node and recovers variable if needed
}
```

## Key Changes

1. **Dual-mode support**: Fixes work for both:
   - **Legacy flows** (flowData/adjList structure)
   - **V2 flows** (nodes/edges structure)

2. **Node types covered**:
   - `Text` (legacy)
   - `Button` (legacy)
   - `List` (legacy)
   - `askQuestion` (V2)

3. **Immediate persistence**: When inputVariable is recovered, it's immediately saved to Redis to prevent re-loss

## Testing Instructions

### Test Case 1: Text Input for Name
1. Start a conversation with tenant `ehgymjv` automation
2. When prompted for name, send a **text message** (e.g., "John Doe")
3. **Expected**: Flow advances to next question, name is recorded
4. **Previous behavior**: Flow repeats the name question

### Test Case 2: Text Input for Address
1. Continue the flow to address question
2. Send a **text message** for address (e.g., "123 Main St")
3. **Expected**: Flow advances, address is recorded
4. **Previous behavior**: Flow repeats the address question

### Test Case 3: Audio Still Works
1. Test the same flow with **audio messages**
2. **Expected**: Audio continues to work as before
3. Confirm no regression

### Test Phone Numbers
Test with the following phone numbers from tenant `ehgymjv`:
- 919021404255 (reported issue)
- 918720962751
- 919425030130
- 919643393874
- 918010901678

## Verification

### Check Logs
Look for these log messages indicating the fix is working:

```
📝 [inputVariable] RECOVERED inputVariable="name" from node X configuration (type: Text, version: 1)
```

```
🔧 [FIX] Recovered missing inputVariable="address" from node Y (type: Text)
```

### Database Check
After user provides text input, verify in database that the variable was recorded:
```sql
SELECT * FROM dynamic_data
WHERE phone = '919021404255'
AND tenant_id = 'ehgymjv'
ORDER BY created_at DESC;
```

## Deployment

### 1. Backup Current Version
```bash
cd /path/to/whatsapp_bot_server_withclaude
git add .
git commit -m "Backup before text input fix"
```

### 2. Deploy Changes
```bash
# Changes are already in mainwebhook/userWebhook.js
git add mainwebhook/userWebhook.js
git commit -m "Fix: Text input not advancing flow for tenant ehgymjv

- Added inputVariable recovery from node configuration
- Handles both legacy and V2 flow structures
- Fixes infinite loop when users send text for name/address
"
git push origin newios
```

### 3. Restart Server
```bash
# If using PM2
pm2 restart whatsapp-bot-server

# If using Azure App Service
# Restart from Azure Portal or CLI
az webapp restart --name whatsappbotserver --resource-group <resource-group>
```

## Rollback Plan

If issues occur, revert the changes:

```bash
git revert HEAD
git push origin newios
# Restart server as above
```

## Related Files
- `mainwebhook/userWebhook.js` - Main fix location
- `mainwebhook/snm.js` - Flow node processing (no changes needed, but related)
- `sessionManager.js` - Redis session management (existing code)

## Additional Notes

### Why This Issue Occurred
1. **Timing sensitivity**: The issue manifested when there was a delay between setting inputVariable and receiving user response
2. **Tenant-specific**: More likely with tenants that have longer flows or specific node configurations
3. **Phone number specific**: Some phone numbers might have slower network conditions, increasing the race condition window

### Prevention for Future
1. Always verify inputVariable exists before using it
2. Implement defensive coding for session state management
3. Consider adding inputVariable to node processing pipeline rather than session-only

## Contact
For issues or questions about this fix, contact the development team.

**Fix Applied**: 2026-01-29
**Tested**: Pending
**Status**: Ready for deployment
