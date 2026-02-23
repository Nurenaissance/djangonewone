# Socket.io Implementation Issues & Fixes

## Date: 2026-01-09

## Summary
The Socket.io implementation in the WhatsApp bot server had several issues with message structure handling. The server was emitting complex nested message objects, but the frontend was not properly extracting the text content, leading to `[object Object]` or stringified JSON being displayed.

## Issues Found

### 1. **Message Structure Mismatch**

**Server emits** (userWebhook.js:1359):
```javascript
io.emit('new-message', {
  message: {
    type: "text",
    text: {
      body: message_text
    }
  },
  phone_number_id: userSession.business_phone_number_id,
  contactPhone: userSession.userPhoneNumber,
  name: userSession.userName,
  time: timestamp
});
```

**Frontend was accessing**:
- `message.message` - which is the complex nested object `{ type: "text", text: { body: "..." } }`
- `message.message.text.body` - hardcoded for text messages only, breaks for other types
- `JSON.stringify(message.message)` - creates messy string representation

### 2. **No Support for Different Message Types**
The frontend had no proper handling for:
- Interactive messages (buttons, lists)
- Media messages (images, videos, documents)
- Audio messages
- Location/Contact shares

### 3. **Files Affected**
- `whatsappBusinessAutomation_withclaude/src/Pages/Chatbot/hooks/useWebSocket.jsx`
- `whatsappBusinessAutomation_withclaude/src/Pages/Chatbot/chatbot.jsx`
- `whatsappBusinessAutomation_withclaude/src/NavbarMain.jsx`

## Fixes Applied

### 1. **Created Message Parser Utility** (`src/utils/messageParser.js`)

Created a comprehensive utility to handle all WhatsApp message types:

```javascript
export function extractMessageText(messageObj) {
  // Handles:
  // - Text messages: messageObj.text.body
  // - Interactive messages: button/list replies
  // - Media messages: captions or type indicators
  // - Audio/Location/Contacts: friendly labels
  // - Fallback: JSON stringification for unknown types
}

export function formatSocketMessage(socketMessage, sender = 'user') {
  // Formats socket events into chat message objects
}
```

### 2. **Updated useWebSocket Hook**
**Before:**
```javascript
socket.on('new-message', (message) => {
  if (message?.contactPhone === selectedContact?.phone) {
    onNewMessage({
      text: message.message,  // ❌ Object, not string
      sender: 'user',
      timestamp: new Date().toISOString()
    });
  }
});
```

**After:**
```javascript
import { extractMessageText } from '../../../utils/messageParser';

socket.on('new-message', (message) => {
  if (message?.contactPhone === selectedContact?.phone) {
    const messageText = extractMessageText(message.message);  // ✅ Proper text extraction

    onNewMessage({
      text: messageText,
      sender: 'user',
      timestamp: message.time || new Date().toISOString()
    });
  }
});
```

### 3. **Updated chatbot.jsx**
**Before:**
```javascript
{
  id: `msg_${Date.now()}`,
  text: JSON.stringify(message.message),  // ❌ Messy JSON string
  sender: "user",
  timestamp: Date.now(),
  time: currentTimestamp,
}
```

**After:**
```javascript
import { extractMessageText } from "../../utils/messageParser";

{
  id: `msg_${Date.now()}`,
  text: extractMessageText(message.message),  // ✅ Clean text
  sender: "user",
  timestamp: Date.now(),
  time: currentTimestamp,
}
```

### 4. **Updated NavbarMain.jsx**
**Before:**
```javascript
const handleNewMessage = (message) => {
  const newNotification = {
    id: Date.now(),
    text: `New message from ${message.contactPhone}: ${message.message.text.body}`,  // ❌ Breaks for non-text messages
    read: false,
  };
  // ...
};
```

**After:**
```javascript
import { extractMessageText } from './utils/messageParser';

const handleNewMessage = (message) => {
  const messageText = extractMessageText(message.message);  // ✅ Works for all types

  const newNotification = {
    id: Date.now(),
    text: `New message from ${message.contactPhone}: ${messageText}`,
    read: false,
  };
  // ...
};
```

## Testing Checklist

### Backend (WhatsApp Bot Server)
- [x] Socket.io server initializes correctly
- [x] `io.emit('new-message')` emits with correct structure
- [x] `io.emit('node-message')` emits with correct structure
- [x] `io.emit('temp-user')` emits with correct structure
- [x] `io.emit('failed-response')` emits with correct structure
- [x] Connection/disconnection logs work properly

### Frontend (React App)
- [ ] Test text message display
- [ ] Test interactive message (button click) display
- [ ] Test image message with caption display
- [ ] Test document message display
- [ ] Test audio message display
- [ ] Test notification display in NavbarMain
- [ ] Test unread count updates in Navbar
- [ ] Test real-time message updates in chatbot page
- [ ] Verify no "[object Object]" or stringified JSON appears

## Socket Events Documentation

### Server -> Client Events

#### 1. `new-message`
Emitted when user sends a message to the bot.

**Payload:**
```javascript
{
  message: {
    type: "text" | "interactive" | "image" | "video" | "document" | "audio" | "location" | "contacts",
    text: { body: string },                    // For text messages
    interactive: { ... },                      // For button/list replies
    image: { id, caption },                    // For images
    // ... other fields based on type
  },
  phone_number_id: string,
  contactPhone: string,
  name: string,
  time: string (ISO timestamp)
}
```

#### 2. `node-message`
Emitted when bot sends a message to user.

**Payload:** Similar to `new-message`

#### 3. `temp-user`
Emitted when a temporary user is detected (command: `*/username`)

**Payload:**
```javascript
{
  temp_user: string,
  phone_number_id: string,
  tenant: string
}
```

#### 4. `failed-response`
Emitted when a message send fails.

**Payload:**
```javascript
{
  code: number,
  title: string,
  message: string,
  // ... error details
}
```

## Performance Considerations

1. **Message Parser Caching**: The `extractMessageText` function could be memoized for repeated calls with same message object
2. **Socket Connection**: Each hook/component creates new socket connection - consider using a shared socket context
3. **Event Listeners**: Properly cleaning up listeners on unmount to prevent memory leaks

## Future Improvements

1. **Centralized Socket Management**: Create a React Context for socket management instead of multiple socket instances
2. **Type Safety**: Add TypeScript definitions for socket event payloads
3. **Message Queue**: Implement message queue for handling high-frequency socket events
4. **Reconnection Logic**: Add automatic reconnection with exponential backoff
5. **Error Boundaries**: Add error boundaries to catch and handle socket-related errors gracefully

## Monitoring

To verify socket is working:
1. Open browser DevTools -> Network -> WS tab
2. Look for Socket.io connection to `whatsappURL`
3. Monitor events in Console (connection/disconnection logs)
4. Send test message and verify real-time update

## Notes

- The socket server uses Socket.io v4.x (check package.json)
- CORS is configured to allow connections from specific origins (server.js:36-42)
- Socket connects on component mount and disconnects on unmount
- All socket events are broadcast to all connected clients (using `io.emit()`)
- Consider using rooms/namespaces for multi-tenant isolation
