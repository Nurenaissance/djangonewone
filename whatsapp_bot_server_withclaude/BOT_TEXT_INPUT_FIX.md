# Bot Text Input Fix - Global V2 Flow Issue

## Problem Summary

**Symptom:** When users sent text responses to askQuestion nodes in V2 flows, the bot would repeat the same question instead of advancing to the next question.

**Scope:** **GLOBAL BUG** affecting ALL tenants using flowVersion 2, not tenant-specific.

**Discovery:** Found while fixing interview dashboard for tenant ehgymjv, but affects all V2 flows across all tenants.

## Root Causes

### 1. Text Responses Not Being Saved
**Location:** `mainwebhook/userWebhook.js` lines 925-940

**Issue:**
- When text was received for askQuestion nodes, the code would advance to the next node
- BUT it never saved the text response to the variable
- This caused the bot to think no response was received
- Result: Question would repeat

**Before:**
```javascript
else if (['askQuestion'].includes(nodeType)) {
    const data = currNodeObj?.data || {};
    const oldNode = userSession.currNode;

    // Advances node but DOESN'T save response ❌
    const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
    if (nextNodes.length > 0) {
      userSession.currNode = nextNodes[0];
      userSession.nodeAdvanced = true;
    }
}
```

**After:**
```javascript
else if (['askQuestion'].includes(nodeType)) {
    const data = currNodeObj?.data || {};
    const oldNode = userSession.currNode;
    const variable = data.variable;

    // ✅ SAVE text response to variable BEFORE advancing
    if (variable && message_text) {
      userSession[variable] = message_text;
      console.log(`✅ Saved text response to variable "${variable}"`);
    }

    // Then advance to next node
    const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
    if (nextNodes.length > 0) {
      userSession.currNode = nextNodes[0];
      userSession.nodeAdvanced = true;
    }
}
```

### 2. Stale InputVariable Preservation
**Location:** `mainwebhook/userWebhook.js` lines 1259-1270

**Issue:**
- When node advanced, code preserved OLD inputVariable from previous question
- Created inconsistent state: `currNode = "address"` but `inputVariable = "name"`
- Caused confusion in message processing

**Before:**
```javascript
if (userSession.nodeAdvanced) {
  // ❌ Preserved OLD inputVariable from previous question
  const existingSession = await userSessions.get(sessionKey);
  if (existingSession && existingSession.inputVariable) {
    userSession.inputVariable = existingSession.inputVariable;
  }
  await userSessions.set(sessionKey, userSession);
}
```

**After:**
```javascript
if (userSession.nodeAdvanced) {
  // ✅ Clear inputVariable - new node sets its own
  userSession.inputVariable = null;
  console.log(`🔍 Cleared inputVariable - new node will set its own`);
  await userSessions.set(sessionKey, userSession);
}
```

## Impact

### Who Was Affected
- **ALL tenants** using `flowVersion === 2`
- **ALL flows** with askQuestion nodes
- **ANY scenario** where users send text to askQuestion nodes

### What's Fixed
✅ Text responses now saved to variables correctly
✅ Questions advance properly after text input
✅ No more question repetition
✅ inputVariable cleared on node advance
✅ Consistent behavior between text and audio responses

## Testing

### Before Fix
1. Bot asks: "What's your name?"
2. User types: "John"
3. Bot asks: "What's your name?" ← **REPEATS**

### After Fix
1. Bot asks: "What's your name?"
2. User types: "John"
3. Bot asks: "What's your address?" ← **ADVANCES CORRECTLY**

## Deployment

### Bot Server (Node.js)
**File:** `mainwebhook/userWebhook.js`
**Branch:** newone
**Commit:** 4cffac5

**To deploy:**
```bash
cd whatsapp_bot_server_withclaude
git push origin newone
```

Azure will auto-deploy the bot server.

### Django Backend
**Files:**
- `interviews/models.py` - Added audio fields
- `interviews/serializers.py` - Updated serializers
- `import_interview_accurate.py` - Accurate import script

**Branch:** hotfix
**Commit:** 7114e34

**To deploy:**
```bash
cd whatsapp_latest_final_withclaude
git push origin hotfix
```

Azure will auto-deploy and run migrations.

## Related Fixes

This fix complements the dashboard data accuracy fix:
1. **Dashboard Fix** - Correctly maps audio/text responses to fields
2. **Bot Fix** - Ensures text responses are saved and processed correctly
3. **Together** - Complete solution for interview automation

## Verification

After deployment, verify:
1. Send text to first question - should save and advance
2. Check logs for: `✅ Saved text response to variable "name"`
3. Check logs for: `✅ Advanced from [node1] to [node2]`
4. Verify no question repetition occurs
5. Test with multiple tenants/flows to confirm global fix

## Summary

This was a **critical global bug** in the V2 flow processing logic that affected all tenants, not just one. The fix ensures:
- Text responses are properly saved
- Nodes advance correctly
- No confusion between questions
- Consistent behavior across all input types

**Status:** ✅ Fixed and committed, ready to deploy
