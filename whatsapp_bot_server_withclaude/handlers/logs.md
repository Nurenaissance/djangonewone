
warning: in the working copy of 'analytics/db.js', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'mainwebhook/snm.js', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'mainwebhook/userWebhook.js', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'queues/worker.js', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'services/mcpLLMSelector.js', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'templateService.js', LF will be replaced by CRLF the next time Git touches it
PS C:\Users\Adarsh\MyProject\Deployed_Finals\djangobackendaug2025\whatsapp_latest_final-mainjunk\whatsapp_bot_server_withclaude> git commit -m "-15/01/26"
[newone 4ffbacd] -15/01/26
 6 files changed, 193 insertions(+), 149 deletions(-)
PS C:\Users\Adarsh\MyProject\Deployed_Finals\djangobackendaug2025\whatsapp_latest_final-mainjunk\whatsapp_bot_server_withclaude> node server.js
⚠️  Bull Message Queue disabled (Redis not configured - using local development mode)
⚠️  Redis client for campaign sessions disabled (using local development mode)
⚠️  Analytics Redis cache disabled (using direct fetch in local development mode)
⚠️  Bull Queue workers disabled (messageQueue not available in local development mode)
🔌 Attempting Redis connection (1/3)...
✅ WhatsApp Flow encryption keys loaded from environment variables
🔄 Redis: Connecting...
✅ Redis client connected
✅ Redis: Connected and ready
✅ Redis client ready
✅ Tenant Automation Control: Redis connected
✅ Rate Limiter: Redis connected

🔑 ============ OPENAI API KEY DEBUG ============
🔑 API Key loaded: sk-proj-Yo..._Dz0zR6gEA
📏 Key length: 164
📍 Key starts with: sk-proj-YoAv_Ub...
🔑 ============================================

⏰ [Aggregation] Setting up cron jobs...
✅ [Aggregation] Cron jobs set up successfully
✅ Analytics aggregation jobs initialized
Server is listening on port: 8080
✅ Media Redis client connected
✅ Media Redis ready
✅ Redis connections verified
============================================================
🔔 [WEBHOOK-VERIFY] GET /webhook request received - 2026-01-20T09:04:40.891Z
📋 [WEBHOOK-VERIFY] Query params:
   hub.mode: subscribe
   hub.verify_token: [PRESENT]
   hub.challenge: [PRESENT]
received req body:  {}
✅ [WEBHOOK-VERIFY] Webhook verified successfully!
============================================================

========== WEBHOOK: text from 919643393874 ==========
✅ Redis connections verified
[userWebhook] Processing: text from 919643393874

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts_by_tenant/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/whatsapp_tenant
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

🔍 [MCP Cache] Miss: fetching tools for tenant ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Message saved for 919643393874

----- OUTGOING REQUEST -----
URL: https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/notifications
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/replied
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

handleInput called with value: Heyyy
No valid inputVariable found, skipping API call.
Returning updated userSession:
=== LEGACY MODE DEBUG ===
Current Node: 9
Node Type: string
Next Node Array: [ 7 ]
Adjacency List: [[1],[2],[3],[5],[],[4],[0],[8],[6],[7]]
========================
User at auto-advancing node "string" - will execute via sendNodeMessage
Session saved before sending node message
[snm] Node: 9 | Version: 1
[snm] Processing: type=string, body="नमस्कार...", next=[7]
cCess:token:  EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------


========== WEBHOOK: text from 919643393874 ==========
✅ Redis connections verified
[userWebhook] Processing: text from 919643393874
🔍 [MCP Cache] Miss: fetching tools for tenant ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSQTUzODRBOUFEMTMyNzlEN0UxAA=='
    }
  ]
}
Tenant sent in send-message:  ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Message saved for 919643393874

----- OUTGOING REQUEST -----
URL: https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/notifications
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/replied
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

ℹ️ Could not fetch contact name for analytics
handleInput called with value: Heyy
No valid inputVariable found, skipping API call.
Returning updated userSession:
=== LEGACY MODE DEBUG ===
Current Node: 9
Node Type: string
Next Node Array: [ 7 ]
Adjacency List: [[1],[2],[3],[5],[],[4],[0],[8],[6],[7]]
========================
User at auto-advancing node "string" - will execute via sendNodeMessage
Session saved before sending node message
[snm] Node: 9 | Version: 1
[snm] Processing: type=string, body="नमस्कार...", next=[7]
cCess:token:  EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSNkYxRDQzNTVBQjY2NkUwODZGAA=='
    }
  ]
}
Tenant sent in send-message:  ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

ℹ️ Could not fetch contact name for analytics
✅ Analytics database connected
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:04:57.753Z
============================================================
⚠️ Slow query (2302ms): 
      INSERT INTO message_events (
        tenant_id, message_id, template_id, template_name,

✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSQTUzODRBOUFEMTMyNzlEN0UxAA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Analytics database connected

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:04:59.144Z
============================================================
⚠️ Slow query (2066ms): 
      INSERT INTO message_events (
        tenant_id, message_id, template_id, template_name,

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSQTUzODRBOUFEMTMyNzlEN0UxAA==

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSNkYxRDQzNTVBQjY2NkUwODZGAA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:00.236Z
============================================================
✅ Message saved for 919643393874
[snm] string auto-advance to node 7
[snm] Node: 7 | Version: 1
[snm] Processing: type=Text, body="हमें अपना नाम बताइए।...", next=[8]
[snm] Text node set inputVariable="name"
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDQ2MzVEMzA0RTQzQTgwRjA3AA=='
    }
  ]
}
Tenant sent in send-message:  ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Analytics database connected
⚠️ Slow query (2077ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSNkYxRDQzNTVBQjY2NkUwODZGAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:02.705Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:03.119Z
============================================================
ℹ️ Could not fetch contact name for analytics
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:03.378Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDQ2MzVEMzA0RTQzQTgwRjA3AA==
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDQ2MzVEMzA0RTQzQTgwRjA3AA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:04.739Z
============================================================
Failed to save message statistics: socket hang up
✅ Message saved for 919643393874
[snm] string auto-advance to node 7
[snm] Node: 7 | Version: 1
[snm] Processing: type=Text, body="हमें अपना नाम बताइए।...", next=[8]
[snm] Text node set inputVariable="name"
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRjJCOEFCOEYyRENGRUFBNzU0AA=='
    }
  ]
}
Tenant sent in send-message:  ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:12.333Z
============================================================
ℹ️ Could not fetch contact name for analytics

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRjJCOEFCOEYyRENGRUFBNzU0AA==
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRjJCOEFCOEYyRENGRUFBNzU0AA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:05:14.285Z
============================================================
✅ Message saved for 919643393874
Updated Current Node:  7
Updated Current Node:  7
Webhook processing completed successfully
✅ Message saved for 919643393874
Updated Current Node:  7
Updated Current Node:  7
Webhook processing completed successfully

========== WEBHOOK: text from 919643393874 ==========
✅ Redis connections verified
[userWebhook] Processing: text from 919643393874
🔍 [MCP Cache] Miss: fetching tools for tenant ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Message saved for 919643393874

----- OUTGOING REQUEST -----
URL: https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/notifications
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/replied
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

handleInput called with value: Okay
No valid inputVariable found, skipping API call.
Returning updated userSession:
=== LEGACY MODE DEBUG ===
Current Node: 7
Node Type: Text
Next Node Array: [ 8 ]
Adjacency List: [[1],[2],[3],[5],[],[4],[0],[8],[6],[7]]
========================
Before advancement: currNode=7, nextNode=8
After advancement: currNode=8, nextNode=6
Advanced from 7 to 8 after text input
Session saved before sending node message
[snm] Node: 8 | Version: 1
[snm] Processing: type=Text, body="हमें अपना पता बताइए।...", next=[6]
[snm] Text node set inputVariable="address"
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/927560953782559/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDFBOEVFMTIyQzY1Qzk4RUYzAA=='
    }
  ]
}
Tenant sent in send-message:  ehgymjv

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

ℹ️ Could not fetch contact name for analytics

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:06:42.135Z
============================================================
✅ Analytics database connected
⚠️ Slow query (3247ms): 
      INSERT INTO message_events (
        tenant_id, message_id, template_id, template_name,

✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDFBOEVFMTIyQzY1Qzk4RUYzAA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Analytics database connected
⚠️ Slow query (1989ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDFBOEVFMTIyQzY1Qzk4RUYzAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:06:44.359Z
============================================================
✅ Message saved for 919643393874
Updated Current Node:  8
Webhook processing completed successfully
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:07.166Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRTE4NEZFNEI2Mzg5MEY2REZFAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:08.856Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:09.134Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRTgxOUY0RjM5QjdGQzI4RjlFAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:10.629Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:11.372Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSNzg2MDRFNDY2NjQ4Qzk5QTg4AA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:12.891Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:13.254Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDM4RUE3Q0M0RDBDNTU3QTVDAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:14.361Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:14.713Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSN0FCQjUxNjU4QzE5RjBDMEY1AA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:16.263Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:16.674Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRDg3NUExRTI2MzNCNkU5MEQyAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:17.831Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:18.573Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:19.623Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '927560953782559',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Analytics database connected
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRTgzODdCQjgwQzQ3NzY5QTFFAA==
⚠️ Slow query (2037ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRkMwNkNGQzkzNEE0RTBEMkI5AA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:21.282Z
============================================================
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-20T09:07:21.341Z
============================================================