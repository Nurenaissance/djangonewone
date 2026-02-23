# Simplified HelloZestay Flow for hjiqohe

## Problem with Current Approach
- Flow 209 has multiple steps asking for front ID, back ID, etc.
- After bulk upload, flow still navigates to "ask for document" nodes
- Too complex for users in a hurry

## New Simplified Flow

### User Journey (3 steps total)

```
USER: HelloZestay BZOC
         ↓
BOT:  Hi *Adarsh*! You have arrived at *Resort Name*.

      📄 Please upload all your ID documents now.
      (You can send multiple photos at once)
         ↓
USER: [Uploads 1-5 images/documents in bulk]
         ↓
      [3 second wait for any more uploads]
         ↓
BOT:  ✅ Received 3 document(s). Processing your check-in...
         ↓
      [Send media IDs to n8n endpoint]
         ↓
      [n8n handles everything else - blob upload, OCR, etc.]
         ↓
BOT:  [Response from n8n - could be success message or next steps]
```

### Key Principles

1. **No Flow 209** - Don't trigger the complex flow at all
2. **Single Upload Step** - User uploads everything at once
3. **Batch Collection** - Wait 3 seconds for multiple uploads
4. **Endpoint Handles Logic** - n8n decides what to do next
5. **Fast** - Minimal back-and-forth

### Implementation Plan

#### State Machine (Simple)

```
STATES:
  - IDLE: No active session
  - AWAITING_DOCS: Waiting for user to upload documents
  - PROCESSING: Batch timeout expired, sending to endpoint

TRANSITIONS:
  "HelloZestay [ID]" → AWAITING_DOCS (send welcome + upload prompt)
  [Media received] in AWAITING_DOCS → Reset 3s timer, collect media
  [3s timeout] → PROCESSING → Send to endpoint → IDLE
```

#### Data Sent to Endpoint

```json
{
  "userPhone": "919643393874",
  "businessPhoneId": "606239485906302",
  "guestId": "BZOC",
  "resortName": "Adarsh Resort",
  "userName": "Adarsh Sharma",
  "timestamp": "2026-01-18T...",
  "mediaFiles": [
    { "mediaId": "abc123", "type": "image", "sequence": 1 },
    { "mediaId": "def456", "type": "image", "sequence": 2 },
    { "mediaId": "ghi789", "type": "document", "sequence": 3 }
  ],
  "accessToken": "EAAVZBob..."
}
```

#### n8n Endpoint Response Options

Option A: Simple acknowledgment
```json
{
  "success": true,
  "message": "Documents received successfully!"
}
```

Option B: Custom message to send
```json
{
  "success": true,
  "sendMessage": {
    "type": "text",
    "text": "✅ Check-in complete! Your room is 304. WiFi: GuestNet / welcome123"
  }
}
```

Option C: Send buttons for next action
```json
{
  "success": true,
  "sendMessage": {
    "type": "interactive",
    "interactive": {
      "type": "button",
      "body": { "text": "Documents received! What would you like to do?" },
      "action": {
        "buttons": [
          { "type": "reply", "reply": { "id": "hotel_info", "title": "Hotel Info" } },
          { "type": "reply", "reply": { "id": "room_service", "title": "Room Service" } }
        ]
      }
    }
  }
}
```

### Code Changes Required

1. **Remove** flow 209 trigger from HelloZestay handler
2. **Add** simple state tracking (AWAITING_DOCS per user)
3. **Send** upload prompt after welcome
4. **Collect** media with 3s batch timeout
5. **Send** to endpoint when batch complete
6. **Forward** endpoint response to user (if any)

### Questions to Decide

1. **Timeout duration**: 3 seconds good? Or 5 seconds for slow uploaders?
2. **Max documents**: Limit to 5? Or unlimited?
3. **Endpoint response**: Should n8n always send a response message, or just acknowledge?
4. **Session expiry**: How long to wait for uploads after welcome? (10 min?)
5. **Re-upload**: If user sends more docs later, start new batch or add to existing?

### Benefits

- ⚡ **Fast**: 3 messages total (welcome, upload, confirmation)
- 🎯 **Simple**: No confusing multi-step flow
- 📱 **WhatsApp native**: Users can select multiple photos at once
- 🔄 **Flexible**: n8n controls what happens after upload
- 🛡️ **Robust**: No flow state to get corrupted

---

## Approval Needed

Please confirm:
1. Is this the right approach?
2. What should the upload prompt message say?
3. What timeout duration (3s or 5s)?
4. Should the endpoint send the final response, or should we send a generic "Documents received" message?
