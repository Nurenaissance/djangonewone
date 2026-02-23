# HelloZestay Flow Verification Guide

**Tenant:** hjiqohe
**Flow Name:** HelloZestay
**Date:** 2026-01-09

---

## Overview

HelloZestay is a specialized, ultra-optimized flow for the hjiqohe tenant that provides instant guest check-in via WhatsApp.

### How It Works

1. **Trigger Format:** `HelloZestay GUEST_ID` (e.g., `HelloZestay ABC123`)
2. **Lookup:** Searches Redis cache or API for guest's resort name
3. **Response:** Sends personalized greeting with resort name
4. **Flow Launch:** Triggers flow ID "209" (zestayreceptionmain)
5. **Webhook:** Sends guest data to backend for processing

### Special Features

- ⚡ **Ultra-fast path:** Parallel Redis/API lookup during session initialization
- 🔒 **Locking mechanism:** Prevents concurrent processing for same user
- 🔄 **Restart capability:** Allows users to restart flow by sending HelloZestay again
- 🚫 **Language blocking:** Prevents `/language` command during active flow
- 📊 **Performance tracking:** Logs execution time at each step

---

## Compatibility with Recent Fixes

### ✅ Session Save Timing Fix (COMPATIBLE)

**Our Fix:** Session saved BEFORE `sendNodeMessage` call
**HelloZestay:** Uses direct `sendMessage` and `triggerFlowById`, NOT `sendNodeMessage`
**Impact:** NO CONFLICT - HelloZestay bypasses the regular flow entirely

### ✅ Button Element Auto-Advancement (COMPATIBLE)

**Our Fix:** Auto-advances through button_element nodes
**HelloZestay:** Triggers flow 209 directly, then user interacts with that flow
**Impact:** NO CONFLICT - Once flow 209 starts, button fixes apply normally

### ✅ Infinite Loop Fix (COMPATIBLE)

**Our Fix:** Save session before recursive sendNodeMessage calls
**HelloZestay:** No recursive calls in the HelloZestay handler itself
**Impact:** NO CONFLICT - Flow 209 benefits from the fix once it starts

### ✅ Audio/Document Advancement (COMPATIBLE)

**Our Fix:** Properly update nextNode for media messages
**HelloZestay:** May receive media in flow 209
**Impact:** BENEFICIAL - Media handling improved in flow 209

---

## Potential Issues & Mitigations

### Issue 1: Session Locking Conflicts

**Risk:** hjiqohe has `isProcessing` lock, HelloZestay has separate lock
**Mitigation:** HelloZestay lock is separate (HELLOZESTAY_LOCKS Map) - no conflict
**Status:** ✅ SAFE

### Issue 2: Flow 209 Session State

**Risk:** Flow 209 might use legacy adjacency list navigation
**Mitigation:** All our node advancement fixes apply to flow 209 automatically
**Status:** ✅ SAFE

### Issue 3: Concurrent HelloZestay Messages

**Risk:** User sends multiple HelloZestay messages rapidly
**Mitigation:** Locking mechanism in place (`acquireHelloZestayLock`)
**Status:** ✅ PROTECTED

### Issue 4: Guest ID Not Found

**Risk:** Invalid guest ID causes flow to hang
**Mitigation:** Error message sent, lock released, function returns
**Status:** ✅ HANDLED

---

## Testing Checklist

### Prerequisites

- [ ] **Node.js server running** (`node server.js`)
- [ ] **hjiqohe phone number ID** configured
- [ ] **Valid test guest ID** available in system
- [ ] **Flow 209 exists** and is configured correctly
- [ ] **Redis or API** has test guest data

### Test Scenarios

#### Test 1: Valid Guest ID ✅
```bash
node testing/test-hellozestay-flow.js valid
```

**Expected:**
- ✅ Greeting message sent with resort name
- ✅ Flow 209 triggered
- ✅ Webhook to backend successful
- ✅ Lock acquired and released
- ⏱️ Response time < 2 seconds

**Verify in logs:**
```
⚡⚡⚡ [hjiqohe] ULTRA-FAST PATH: HelloZestay executing
⚡ [WARMUP] Parallel fetch starting for HelloZestay ABC123
✅ [t=XXXms] Resort: Resort Name Here
📤 [t=XXXms] Sending greeting + triggering flow
✅ [t=XXXms] Both greeting and flow complete
✅✅✅ [hjiqohe] HelloZestay completed
```

#### Test 2: Invalid Guest ID ✅
```bash
node testing/test-hellozestay-flow.js invalid
```

**Expected:**
- ✅ Error message sent to user
- ❌ Flow 209 NOT triggered
- ✅ Lock released properly

**Verify in logs:**
```
⚠️ [t=XXXms] Redis empty, trying API...
❌ [t=XXXms] Guest not found in Redis OR API: INVALID999
```

#### Test 3: Missing Guest ID ✅
```bash
node testing/test-hellozestay-flow.js missing
```

**Expected:**
- ✅ Validation message sent
- ❌ Flow NOT triggered
- ✅ Lock released immediately

**Verify in logs:**
```
⚠️ Please provide your Property ID
```

#### Test 4: Flow Restart ✅
```bash
node testing/test-hellozestay-flow.js restart
```

**Expected:**
- ✅ First flow starts normally
- ✅ Second HelloZestay clears and restarts
- ❌ NO conflicts

**Verify in logs:**
```
🔄 [hjiqohe] HelloZestay restart requested for 919999999999
🗑️ HelloZestay flow cleared for 919999999999+phoneId
```

#### Test 5: Language Blocking ✅
```bash
node testing/test-hellozestay-flow.js language
```

**Expected:**
- ✅ /language command blocked
- ✅ Flow continues normally

**Verify in logs:**
```
⚠️ [hjiqohe] Language change blocked during HelloZestay flow
```

#### Test 6: Concurrent Prevention ✅
```bash
node testing/test-hellozestay-flow.js concurrent
```

**Expected:**
- ✅ First request processes
- ✅ Second request blocked
- ❌ NO duplicate processing

**Verify in logs:**
```
⚠️ [hjiqohe] HelloZestay lock already held, skipping
```

---

## Performance Benchmarks

### Expected Timing (from logs)

| Operation | Expected Time |
|-----------|---------------|
| Session initialization + Redis lookup | 0-100ms |
| Guest not in Redis, trying API | 100-500ms |
| Send greeting + trigger flow | 200-800ms |
| Total (happy path) | 500-1500ms |
| Total (with API fallback) | 800-2000ms |

### Performance Indicators

**Fast (< 1s):**
- ✅ Guest in Redis cache
- ✅ Parallel operations working

**Medium (1-2s):**
- ⚠️ Redis miss, API lookup required
- ⚠️ Network latency to backend

**Slow (> 2s):**
- ❌ API timeout issues
- ❌ Network problems
- ❌ Backend overloaded

---

## Common Issues & Solutions

### Issue: Lock Already Held

**Symptom:**
```
⚠️ [hjiqohe] HelloZestay lock already held, skipping
```

**Cause:** Previous HelloZestay request still processing

**Solution:** Wait for previous request to complete (auto-releases after ~5s timeout)

**Prevention:** None needed - this is expected behavior

---

### Issue: Guest Not Found

**Symptom:**
```
❌ [t=XXXms] Guest not found in Redis OR API: ABC123
```

**Cause:** Guest ID doesn't exist in system

**Solution:** Verify guest ID is correct, check Redis cache and API endpoint

**Prevention:** Ensure guest data is synced to Redis

---

### Issue: Slow Performance

**Symptom:** Total time > 2 seconds

**Cause:** Redis cache miss, API slow

**Solution:**
1. Check Redis cache hit rate
2. Monitor API response times
3. Consider increasing Redis TTL
4. Add monitoring for API performance

**Prevention:** Warm Redis cache with frequently accessed guest IDs

---

### Issue: Flow 209 Not Triggered

**Symptom:** Greeting sent but no flow starts

**Cause:** Flow 209 missing or misconfigured

**Solution:**
1. Verify flow 209 exists in database
2. Check flow is published/active
3. Verify flow belongs to hjiqohe tenant

**Prevention:** Backup flow 209 configuration

---

### Issue: Webhook to Backend Fails

**Symptom:**
```
Webhook error: [error message]
```

**Cause:** Backend endpoint down or slow

**Solution:**
1. Check backend API health
2. Verify authentication token
3. Check network connectivity

**Prevention:**
- Webhook is sent in background (doesn't block flow)
- Errors logged but don't stop user flow
- This is non-critical

---

## Code Locations

### Main Handler
**File:** `mainwebhook/userWebhook.js`
**Function:** `handleHelloZestayFlowOptimized` (lines 232-298)
**Trigger Detection:** Lines 330-344
**Ultra-fast Path:** Lines 428-496

### Locking Functions
**File:** `mainwebhook/userWebhook.js`
- `acquireHelloZestayLock` (lines 182-193)
- `releaseHelloZestayLock` (lines 194-197)
- `markHelloZestayActive` (lines 166-173)
- `clearHelloZestayFlow` (lines 175-180)
- `isInHelloZestayFlow` (lines 151-164)

### Flow Trigger
**File:** `helpers/misc.js`
**Function:** `triggerFlowById` (line 543)

---

## Monitoring Recommendations

### Key Metrics to Track

1. **Response Time Distribution**
   - Track p50, p95, p99 latency
   - Alert if p95 > 2 seconds

2. **Cache Hit Rate**
   - Track Redis hits vs API lookups
   - Alert if hit rate < 80%

3. **Error Rate**
   - Track "Guest not found" errors
   - Track lock conflicts
   - Alert if error rate > 5%

4. **Concurrent Requests**
   - Track lock contention
   - Identify users sending multiple requests

### Logging

Current logs provide excellent observability:
- ⚡ Execution time at each step
- ✅ Success/failure indicators
- 🔒 Lock acquisition/release
- 📊 Performance breakdown

**No additional logging needed.**

---

## Production Deployment Notes

### Before Deploying

1. ✅ Test with actual guest IDs from production database
2. ✅ Verify Redis cache is populated
3. ✅ Test API fallback when Redis is down
4. ✅ Verify flow 209 exists and works
5. ✅ Test all scenarios (valid, invalid, missing, restart, concurrent)

### During Deployment

1. Monitor error rates
2. Track response times
3. Watch for lock conflicts
4. Verify cache hit rates

### After Deployment

1. Monitor for 24 hours
2. Check performance metrics
3. Verify no regressions
4. Collect user feedback

---

## Rollback Plan

If HelloZestay breaks:

1. **Quick Fix:** Disable ultra-fast path
   ```javascript
   // In userWebhook.js line 430, change:
   if (false && isValidHelloZestay && !inActiveHelloZestayFlow) {
   ```

2. **Full Rollback:** Revert to previous version
   ```bash
   git revert HEAD
   git push
   ```

3. **Emergency:** Remove HelloZestay trigger
   - Comment out lines 428-496 in userWebhook.js
   - HelloZestay will fall through to normal flow processing

---

## Success Criteria

HelloZestay flow is considered WORKING if:

- ✅ Valid guest IDs trigger flow correctly
- ✅ Invalid guest IDs show error message
- ✅ Missing guest IDs show validation message
- ✅ 95% of requests complete in < 2 seconds
- ✅ Lock prevents concurrent processing
- ✅ Restart functionality works
- ✅ Language blocking works during flow
- ✅ No infinite loops
- ✅ No session corruption
- ✅ Flow 209 starts correctly

---

## Test Results Template

After running tests, document results here:

```
Date: [YYYY-MM-DD]
Tester: [Your Name]
Server Version: [Git commit hash]

Test 1 - Valid Guest ID: ✅ PASS / ❌ FAIL
  - Greeting sent: [ ]
  - Flow 209 triggered: [ ]
  - Response time: [XXX]ms
  - Errors: [None / List errors]

Test 2 - Invalid Guest ID: ✅ PASS / ❌ FAIL
  - Error message sent: [ ]
  - Flow NOT triggered: [ ]
  - Lock released: [ ]

Test 3 - Missing Guest ID: ✅ PASS / ❌ FAIL
  - Validation message sent: [ ]
  - Lock released immediately: [ ]

Test 4 - Flow Restart: ✅ PASS / ❌ FAIL
  - Flow cleared and restarted: [ ]
  - No conflicts: [ ]

Test 5 - Language Blocking: ✅ PASS / ❌ FAIL
  - /language blocked: [ ]
  - Flow continued: [ ]

Test 6 - Concurrent Prevention: ✅ PASS / ❌ FAIL
  - Second request blocked: [ ]
  - No duplicate processing: [ ]

Notes:
[Add any observations]
```

---

## Final Verdict

**Status:** ✅ READY FOR TESTING

**Compatibility with Recent Fixes:** ✅ FULLY COMPATIBLE

**Recommendation:** Run all test scenarios, monitor logs, verify performance benchmarks.

---

**Documentation Status:** COMPLETE ✅
**Test Script Status:** READY ✅
**Production Readiness:** PENDING TESTING ⏳
