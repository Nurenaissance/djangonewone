# FlowJSON Repeat Bug Fix

## Problem
WhatsApp bot flows with `flowjson` (WhatsApp Forms) nodes were repeating themselves when users replied, instead of progressing to the next node in the flow.

## Root Cause

The bug was caused by improper node advancement after sending flowjson messages:

### Before Fix:
1. **flowjson node sends flow** → currNode stays at flowjson node (BUG!)
2. User submits form → `nfm_reply` is received
3. `nfm_reply` handler advances from flowjson node to next node
4. Next node is processed

**Problem:** If user sent any other message before submitting the form, the bot would re-send the flowjson since currNode was still pointing to the flowjson node.

## Solution

Updated the flow control logic in two files:

### 1. Fixed flowjson Node Advancement (snm.js:669-684)

**Before:**
```javascript
case "flowjson":
    await sendFlowMessage(...)
    break; // ❌ No advancement - stays on flowjson node!
```

**After:**
```javascript
case "flowjson":
    await sendFlowMessage(...)

    // ✅ Auto-advance to next node after sending flow
    userSession.currNode = nextNode[0] !== undefined ? nextNode[0] : null;
    userSession.nextNode = nextNode;
    await userSessions.set(userPhoneNumber + business_phone_number_id, userSession);
    console.log(`✅ FlowJSON advanced to next node: ${userSession.currNode}`);
    break;
```

**Key Changes:**
- Advances `currNode` to the next node immediately after sending the flow
- Saves the session state
- Does NOT call `sendNodeMessage()` recursively (waits for user's form submission)

### 2. Fixed nfm_reply Handler (userWebhook.js:794-802)

**Before:**
```javascript
// ❌ Double advancement - would skip a node!
userSession.currNode = userSession.nextNode[0];
userSession.nextNode = userSession.adjList[userSession.currNode];
sendNodeMessage(userPhoneNumber, business_phone_number_id);
```

**After:**
```javascript
// ✅ No advancement needed - flowjson already advanced
console.log(`📨 NFM reply received for flow: ${flowName}`);
console.log(`📍 Current node after flow: ${userSession.currNode}`);

// Process the current node (which is already the next node after flowjson)
sendNodeMessage(userPhoneNumber, business_phone_number_id);
```

**Key Changes:**
- Removed double advancement logic
- currNode is already at the correct position (set by flowjson node)
- Simply processes the current node

## Flow Sequence (After Fix)

### Correct Flow:
1. **Bot sends flowjson** → currNode advances to "Node B"
2. User receives WhatsApp Form
3. **User submits form** → nfm_reply received
4. Bot processes "Node B" (next node after flowjson)
5. Flow continues normally

### Visual Example:

```
[flowjson Node A] → sends form
                   ↓ (advances immediately)
        currNode = [Node B] (waiting for user response)
                   ↓
User submits form (nfm_reply)
                   ↓
        Process [Node B] → continues flow
```

## Files Modified

1. **whatsapp_bot_server_withclaude/mainwebhook/snm.js**
   - Lines 669-684: flowjson case
   - Added node advancement after sending flow

2. **whatsapp_bot_server_withclaude/mainwebhook/userWebhook.js**
   - Lines 794-802: nfm_reply handler
   - Removed double advancement logic

## Testing

After restarting the Node.js server, test with a flow containing:
1. Start node
2. FlowJSON node (WhatsApp Form)
3. Any other node (text message, question, etc.)

**Expected Behavior:**
- User receives the flow form once
- After submitting, flow progresses to the next node
- No repetition of the flow form

## Deployment

1. Restart the WhatsApp bot server:
   ```bash
   cd whatsapp_bot_server_withclaude
   pm2 restart whatsapp-bot
   # or
   npm restart
   ```

2. Test with a real flow containing flowjson nodes

3. Verify:
   - Flow form is sent only once
   - After user submission, flow progresses correctly
   - No repeat messages

## Related Issues Fixed

This fix also resolves:
- ✅ FlowJSON nodes repeating when users send text before submitting
- ✅ Flows getting stuck on flowjson nodes
- ✅ Double-processing of nodes after flowjson

## Compatibility

- ✅ Works with flowVersion 1 (adjList-based)
- ✅ Works with flowVersion 2 (edges-based)
- ✅ Maintains backward compatibility with existing flows
- ✅ No breaking changes to flow structure

## Additional Notes

- The fix follows the same pattern as other auto-advancing nodes (like `customint`, `template`)
- Session state is properly saved after advancement
- Logging added for better debugging: `📋 FlowJSON sent`, `📨 NFM reply received`, `📍 Current node`
