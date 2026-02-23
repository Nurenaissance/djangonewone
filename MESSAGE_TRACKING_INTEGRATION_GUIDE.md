# Message Tracking Integration Guide

This guide shows how to integrate analytics tracking when sending WhatsApp messages from the frontend.

---

## 🎯 Overview

Every time a message is sent via the WhatsApp API, you need to:
1. Send the message via WhatsApp Graph API
2. Get the `message_id` from the response
3. Track the send event via custom analytics backend

---

## 📝 Code Example

### **Template: Message Sending with Analytics Tracking**

```javascript
import { axiosFast } from '../../api'; // Your axios instance for Node.js backend
import axios from 'axios';

async function sendTemplateMessage({
  recipientPhone,
  templateName,
  templateId,
  language = 'en',
  campaignId = null,
  broadcastGroupId = null,
  contactId = null,
  recipientName = null
}) {
  try {
    const tenantId = localStorage.getItem('tenant_id');
    const accessToken = localStorage.getItem('whatsapp_access_token'); // or fetch from backend
    const phoneNumberId = localStorage.getItem('phone_number_id'); // or fetch from backend

    // ======================================
    // STEP 1: Send message via WhatsApp API
    // ======================================
    const whatsappResponse = await axios.post(
      `https://graph.facebook.com/v20.0/${phoneNumberId}/messages`,
      {
        messaging_product: 'whatsapp',
        to: recipientPhone,
        type: 'template',
        template: {
          name: templateName,
          language: { code: language }
        }
      },
      {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      }
    );

    // Extract message ID from WhatsApp response
    const messageId = whatsappResponse.data.messages[0].id;

    console.log('✅ Message sent via WhatsApp:', messageId);

    // ======================================
    // STEP 2: Track the send event
    // ======================================
    try {
      await axiosFast.post('/api/analytics/track-event', {
        eventType: 'message.sent',
        tenantId: tenantId,
        messageId: messageId,
        templateId: templateId,
        templateName: templateName,
        recipientPhone: recipientPhone,
        recipientName: recipientName,
        contactId: contactId,
        campaignId: campaignId,
        broadcastGroupId: broadcastGroupId,
        messageType: 'template',
        conversationCategory: 'marketing', // or 'utility', 'authentication', 'service'
        cost: calculateMessageCost('marketing'), // See cost calculation below
        timestamp: new Date().toISOString()
      }, {
        headers: {
          'X-Tenant-ID': tenantId
        }
      });

      console.log('✅ Message tracking recorded:', messageId);
    } catch (trackingError) {
      // Don't fail the message send if tracking fails
      console.error('⚠️ Failed to track message (non-critical):', trackingError);
    }

    return {
      success: true,
      messageId: messageId,
      recipientPhone: recipientPhone
    };

  } catch (error) {
    console.error('❌ Failed to send message:', error);
    throw error;
  }
}

// ======================================
// Cost Calculation Helper
// ======================================
function calculateMessageCost(conversationCategory) {
  // WhatsApp Business API pricing (India - INR)
  const costs = {
    marketing: 0.65,      // Marketing conversations
    utility: 0.25,        // Utility conversations
    authentication: 0.15, // Authentication conversations
    service: 0.35         // Service conversations
  };

  return costs[conversationCategory] || 0.65;
}

// ======================================
// USAGE EXAMPLE
// ======================================
const result = await sendTemplateMessage({
  recipientPhone: '919876543210',
  templateName: 'welcome_message',
  templateId: '123456789',
  language: 'en',
  campaignId: 'campaign_001',
  recipientName: 'John Doe',
  contactId: 12345
});

console.log('Message result:', result);
```

---

## 🔧 Integration Points

### **Files to Update**

Based on the codebase structure, you need to integrate tracking in these files:

1. **`src/Pages/Chatbot/Broadcast/BroadcastPage.jsx`**
   - When sending bulk messages
   - Track each message individually in a loop

2. **`src/Pages/Chatbot/Broadcast/BroadcastPopup.jsx`**
   - When sending individual template messages
   - Track immediately after WhatsApp API call

3. **Any custom message sending components**
   - Search for: `graph.facebook.com` or `messages` endpoints
   - Add tracking after successful send

---

## 📊 Event Types Reference

### **Message Events**

```javascript
// Message Sent (tracked by frontend)
{
  eventType: 'message.sent',
  messageId: 'wamid.xxx',
  // ... other fields
}

// Message Delivered (tracked by webhook - automatic)
{
  eventType: 'message.delivered',
  messageId: 'wamid.xxx',
  timestamp: '2026-01-06T10:30:00Z'
}

// Message Read (tracked by webhook - automatic)
{
  eventType: 'message.read',
  messageId: 'wamid.xxx',
  timestamp: '2026-01-06T10:35:00Z'
}

// Message Failed (tracked by webhook - automatic)
{
  eventType: 'message.failed',
  messageId: 'wamid.xxx',
  timestamp: '2026-01-06T10:30:00Z'
}

// Message Replied (tracked by webhook - automatic)
{
  eventType: 'message.replied',
  messageId: 'wamid.xxx',
  timestamp: '2026-01-06T10:40:00Z'
}
```

### **Button Click Events**

```javascript
// Button Click (tracked by webhook - automatic)
await axiosFast.post('/api/analytics/track-button-click', {
  tenantId: 'ai',
  messageId: 'wamid.xxx',
  buttonId: 'btn_1',
  buttonText: 'Learn More',
  buttonType: 'url', // or 'quick_reply', 'call_to_action'
  buttonIndex: 0,
  recipientPhone: '919876543210',
  timestamp: new Date().toISOString()
});
```

---

## 🧪 Testing Your Integration

### **1. Manual Testing**

```javascript
// Test script to verify tracking works
async function testMessageTracking() {
  try {
    // Send a test message
    const result = await sendTemplateMessage({
      recipientPhone: 'YOUR_TEST_NUMBER',
      templateName: 'test_template',
      templateId: '123456',
      language: 'en'
    });

    console.log('✅ Test message sent:', result);

    // Wait 30 seconds for delivery
    await new Promise(resolve => setTimeout(resolve, 30000));

    // Check analytics dashboard
    console.log('Check your analytics dashboard now!');

  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Run the test
testMessageTracking();
```

### **2. Database Verification**

After sending a test message, check the database:

```sql
-- Check if message was tracked
SELECT * FROM message_events
WHERE recipient_phone = '919876543210'
ORDER BY created_at DESC
LIMIT 1;

-- Expected result:
-- message_id | template_id | recipient_phone | current_status | sent_at | ...
-- wamid.xxx  | 123456      | 919876543210    | sent          | 2026-01-06 10:30:00 | ...
```

### **3. API Testing with cURL**

```bash
# Test tracking endpoint directly
curl -X POST "https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/api/analytics/track-event" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ai" \
  -d '{
    "eventType": "message.sent",
    "tenantId": "ai",
    "messageId": "test_wamid_123",
    "templateId": "123456",
    "templateName": "test_template",
    "recipientPhone": "919876543210",
    "messageType": "template",
    "cost": 0.65
  }'

# Expected response:
# {
#   "success": true,
#   "eventId": 12345,
#   "message": "Event tracked successfully"
# }
```

---

## 🚨 Common Mistakes to Avoid

### ❌ **Mistake 1: Not handling tracking failures**
```javascript
// BAD - Will fail message send if tracking fails
await axiosFast.post('/api/analytics/track-event', { ... });
```

```javascript
// GOOD - Tracking failure doesn't affect message send
try {
  await axiosFast.post('/api/analytics/track-event', { ... });
} catch (error) {
  console.error('Tracking failed (non-critical):', error);
}
```

### ❌ **Mistake 2: Missing message ID**
```javascript
// BAD - Using template ID instead of message ID
messageId: templateId

// GOOD - Using actual message ID from WhatsApp response
messageId: whatsappResponse.data.messages[0].id
```

### ❌ **Mistake 3: Wrong timestamp format**
```javascript
// BAD - Unix timestamp
timestamp: Date.now()

// GOOD - ISO string
timestamp: new Date().toISOString()
```

### ❌ **Mistake 4: Missing tenant ID header**
```javascript
// BAD - No tenant header
await axiosFast.post('/api/analytics/track-event', data);

// GOOD - Include tenant header
await axiosFast.post('/api/analytics/track-event', data, {
  headers: { 'X-Tenant-ID': tenantId }
});
```

---

## 🔍 Debugging Checklist

If tracking isn't working:

- [ ] Check browser console for errors
- [ ] Verify `axiosFast` is imported correctly
- [ ] Ensure tenant ID is in localStorage
- [ ] Check Node.js server logs for incoming requests
- [ ] Verify PostgreSQL connection is working
- [ ] Check if message ID is valid (starts with `wamid.`)
- [ ] Verify API endpoint URL is correct
- [ ] Check CORS settings if getting CORS errors
- [ ] Ensure authentication headers are included

---

## 📈 Success Metrics

After integration, you should see:

1. **Immediate (< 1 second)**:
   - Console log: "✅ Message tracking recorded"
   - Database entry in `message_events` table

2. **Within 30 seconds**:
   - Status updates to "delivered" (if recipient is online)
   - Webhook receives status update

3. **Within 5 minutes**:
   - Analytics dashboard shows the message
   - Template performance metrics updated
   - Daily aggregation includes the message

---

## 📞 Support

If you encounter issues:

1. Check the logs:
   - Browser console (frontend)
   - Node.js server logs (backend)
   - PostgreSQL logs (database)

2. Verify endpoints:
   ```bash
   # Test analytics API health
   curl https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/api/analytics/overview?tenantId=ai&startDate=2026-01-01&endDate=2026-01-31
   ```

3. Check database:
   ```sql
   SELECT COUNT(*), current_status
   FROM message_events
   WHERE tenant_id = 'ai'
   GROUP BY current_status;
   ```

---

**Ready to integrate!** 🚀

Add the tracking code to your message sending functions and test thoroughly.
