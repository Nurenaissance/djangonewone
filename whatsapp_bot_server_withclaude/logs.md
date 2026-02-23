========== WEBHOOK: text from 919643393874 ==========
✅ Redis connections verified
✓ Message wamid.HBgMOTE5NjQzMz... marked as processed
[userWebhook] Processing: text from 919643393874 (msgId: wamid.HBgMOTE5NjQzMz...)

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

📝 [inputVariable] Session has NO inputVariable, currNode=9
🔒 Lock acquired for 919643393874927560953782559
🔒 [LOCK] Acquired lock for 919643393874 on attempt 1
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

handleInput called with value: Hi
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
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRkU1N0Y0M0ZEMzMxOUI4NzUxAA=='
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
ℹ️ Could not fetch contact name for analytics
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:15:51.191Z
============================================================
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

⚠️ Slow query (1886ms): 
      INSERT INTO message_events (
        tenant_id, message_id, template_id, template_name,

✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRkU1N0Y0M0ZEMzMxOUI4NzUxAA==
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

[snm] string auto-advance to node 7
[snm] Node: 7 | Version: 1
[snm] Processing: type=Text, body="हमें अपना नाम बताइए।...", next=[8]
[snm] Text node set inputVariable="name" for node 7
✅ [snm] inputVariable="name" verified in Redis
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
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRjQyQTBCOTUzQzEwNDUzREI0AA=='
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
⚠️ Slow query (1733ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRkU1N0Y0M0ZEMzMxOUI4NzUxAA==
✅ Message saved for 919643393874
ℹ️ Could not fetch contact name for analytics
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:15:54.043Z
============================================================
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRjQyQTBCOTUzQzEwNDUzREI0AA==
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

[snm] Final save: currNode=7, inputVariable="name"
Updated Current Node:  7
Webhook processing completed successfully
🔓 Lock released for 919643393874927560953782559
🔓 [LOCK] Released lock for 919643393874
✅ Message saved for 919643393874
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:15:54.761Z
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

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRjQyQTBCOTUzQzEwNDUzREI0AA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:15:55.999Z
============================================================

========== WEBHOOK: audio from 919643393874 ==========
✅ Redis connections verified
✓ Message wamid.HBgMOTE5NjQzMz... marked as processed
[userWebhook] Processing: audio from 919643393874 (msgId: wamid.HBgMOTE5NjQzMz...)
[getSession] Retrieved existing session: currNode=7, inputVariable="null"
📝 [inputVariable] Session has NO inputVariable, currNode=7
🔒 Lock acquired for 919643393874927560953782559
🔒 [LOCK] Acquired lock for 919643393874 on attempt 1
🎵 Processing audio upload: 913435718013964
blob doesnt exist

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v22.0/913435718013964
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Media URL:  https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=913435718013964&source=getMedia&ext=1769062861&hash=ARmc_yLPBqFBF4VuR2EUan25LVXBMc58X7ePdXlR394Luw

----- OUTGOING REQUEST -----
URL: https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=913435718013964&source=getMedia&ext=1769062861&hash=ARmc_yLPBqFBF4VuR2EUan25LVXBMc58X7ePdXlR394Luw
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Uploaded media media_913435718013964 successfully, request ID: 6f80a117-401e-002e-0766-8b1b7b000000
✅ Audio uploaded to Blob: https://pdffornurenai.blob.core.windows.net/pdf/media_913435718013964?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-11-30T22:32:25Z&st=2025-06-21T14:32:25Z&spr=https&sig=bDza6nKhK9n6dwDRGXmktSkMX%2BCKxM3U3PyfCPe2EvQ%3D

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

handleInput called with value: 913435718013964
No valid inputVariable found, skipping API call.
Returning updated userSession:
Audio message: Advanced from 7 to 8
Session saved before sending node message
[snm] Node: 8 | Version: 1
[snm] Processing: type=Text, body="हमें अपना पता बताइए।...", next=[6]
[snm] Text node set inputVariable="address" for node 8
✅ [snm] inputVariable="address" verified in Redis
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

✅ Message saved for 919643393874
Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSMEI1QTA2NkU4RkQzNUIzOEUxAA=='
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
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSMEI1QTA2NkU4RkQzNUIzOEUxAA==
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

[snm] Final save: currNode=8, inputVariable="address"
Updated Current Node:  8
Webhook processing completed successfully
🔓 Lock released for 919643393874927560953782559
🔓 [LOCK] Released lock for 919643393874
✅ Message saved for 919643393874

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
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:05.216Z
============================================================
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSMEI1QTA2NkU4RkQzNUIzOEUxAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:06.194Z
============================================================

========== WEBHOOK: audio from 919643393874 ==========
✅ Redis connections verified
✓ Message wamid.HBgMOTE5NjQzMz... marked as processed
[userWebhook] Processing: audio from 919643393874 (msgId: wamid.HBgMOTE5NjQzMz...)
[getSession] Retrieved existing session: currNode=8, inputVariable="address"
📝 [inputVariable] Session has inputVariable="address" for currNode=8
🔒 Lock acquired for 919643393874927560953782559
🔒 [LOCK] Acquired lock for 919643393874 on attempt 1
🎵 Processing audio upload: 1261223122734495
blob doesnt exist

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v22.0/1261223122734495
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Media URL:  https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1261223122734495&source=getMedia&ext=1769062871&hash=ARkWOUz8iu66RRwUJSUDeWQI0Wlssr4TU6l5bEGtRHs2XA

----- OUTGOING REQUEST -----
URL: https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=1261223122734495&source=getMedia&ext=1769062871&hash=ARkWOUz8iu66RRwUJSUDeWQI0Wlssr4TU6l5bEGtRHs2XA
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Uploaded media media_1261223122734495 successfully, request ID: 6f80b870-401e-002e-0466-8b1b7b000000
✅ Audio uploaded to Blob: https://pdffornurenai.blob.core.windows.net/pdf/media_1261223122734495?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-11-30T22:32:25Z&st=2025-06-21T14:32:25Z&spr=https&sig=bDza6nKhK9n6dwDRGXmktSkMX%2BCKxM3U3PyfCPe2EvQ%3D

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

✅ Message saved for 919643393874
handleInput called with value: 1261223122734495
Valid inputVariable detected: address
Extracted user session details: {
  input_variable: 'address',
  phone: '919643393874',
  flow_name: 'interviewdrishtee'
}
Stored value in userSession.api.POST[address] = 1261223122734495
Cleared inputVariable after storing value
Constructed payload: {
  flow_name: 'interviewdrishtee',
  input_variable: 'address',
  value: '1261223122734495',
  phone: '919643393874'
}
Sending data to API: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/add-dynamic-data/
Audio message: Advanced from 8 to 6

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/add-dynamic-data/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

📝 Preserved inputVariable="address" from existing session
Session saved before sending node message
[snm] Node: 6 | Version: 1
[snm] Processing: type=string, body="प्रत्येक प्रश्न का उत्तर इस प्...", next=[0]
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
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSODc5OEJFQkRFNUZBQjMyQTlBAA=='
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

Data sent successfully! Response: { message: 'Success' }
Returning updated userSession:
ℹ️ Could not fetch contact name for analytics
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSODc5OEJFQkRFNUZBQjMyQTlBAA==
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

[snm] string auto-advance to node 0
[snm] Node: 0 | Version: 1
[snm] Processing: type=Text, body="कैलिब्रेशन निर्देश

कृपया नीचे...", next=[1]
[snm] Text node set inputVariable="calibration" for node 0
✅ [snm] inputVariable="calibration" verified in Redis
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

============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:15.729Z
============================================================
✅ Message saved for 919643393874

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

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRTQ1MzA0MjE4QjNGRUZFMUM4AA=='
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

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSODc5OEJFQkRFNUZBQjMyQTlBAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:17.023Z
============================================================
ℹ️ Could not fetch contact name for analytics
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:17.339Z
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

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRTQ1MzA0MjE4QjNGRUZFMUM4AA==
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSRTQ1MzA0MjE4QjNGRUZFMUM4AA==
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

[snm] Final save: currNode=0, inputVariable="calibration"
Updated Current Node:  0
Webhook processing completed successfully
🔓 Lock released for 919643393874927560953782559
🔓 [LOCK] Released lock for 919643393874
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:18.647Z
============================================================
✅ Message saved for 919643393874

========== WEBHOOK: audio from 919643393874 ==========
✅ Redis connections verified
✓ Message wamid.HBgMOTE5NjQzMz... marked as processed
[userWebhook] Processing: audio from 919643393874 (msgId: wamid.HBgMOTE5NjQzMz...)
[getSession] Retrieved existing session: currNode=0, inputVariable="address"
📝 [inputVariable] Session has inputVariable="address" for currNode=0
🔒 Lock acquired for 919643393874927560953782559
🔒 [LOCK] Acquired lock for 919643393874 on attempt 1
🎵 Processing audio upload: 744274392078404
blob doesnt exist

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v22.0/744274392078404
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Media URL:  https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=744274392078404&source=getMedia&ext=1769062883&hash=ARkjZqYLkrJ3fCY4SWwO9doIqDFK5w02DL073SVuy7uCUw

----- OUTGOING REQUEST -----
URL: https://lookaside.fbsbx.com/whatsapp_business/attachments/?mid=744274392078404&source=getMedia&ext=1769062883&hash=ARkjZqYLkrJ3fCY4SWwO9doIqDFK5w02DL073SVuy7uCUw
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBQUtjkjy3ph8t9HBWCmOdxuOQqFqGCDynFLtZBzMxJg8ZB98ZAgfGtjyN1Pn19ikV154PU9NtJXaZC2Ag6mJ5rMzABICcnSDdqVU9naZC37EESXbh4RPCUa8eJlax3LLexmlbZCqAduqQuBKRyM4VIN44qvO6MJ28KSZBhXUGmUnZAKjelU0UgFZBkBdK64bNvWoTTJ6TK66M4S0ZC9KUA3zmUFGzZCRz1j62lojZCTZBgyQ5tXQR2cxttKiNfZC5lY5Djll1ZBcoZB8vUdRq1r6FqR7UfTNH'
}
-----------------------------

Uploaded media media_744274392078404 successfully, request ID: 6f80d224-401e-002e-2e66-8b1b7b000000
✅ Audio uploaded to Blob: https://pdffornurenai.blob.core.windows.net/pdf/media_744274392078404?sv=2024-11-04&ss=bfqt&srt=sco&sp=rwdlacupiytfx&se=2026-11-30T22:32:25Z&st=2025-06-21T14:32:25Z&spr=https&sig=bDza6nKhK9n6dwDRGXmktSkMX%2BCKxM3U3PyfCPe2EvQ%3D

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

✅ Message saved for 919643393874
handleInput called with value: 744274392078404
Valid inputVariable detected: address
Extracted user session details: {
  input_variable: 'address',
  phone: '919643393874',
  flow_name: 'interviewdrishtee'
}
Stored value in userSession.api.POST[address] = 744274392078404
Cleared inputVariable after storing value
Constructed payload: {
  flow_name: 'interviewdrishtee',
  input_variable: 'address',
  value: '744274392078404',
  phone: '919643393874'
}
Sending data to API: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/add-dynamic-data/
Audio message: Advanced from 0 to 1

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/add-dynamic-data/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'ehgymjv',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

📝 Preserved inputVariable="address" from existing session
Session saved before sending node message
[snm] Node: 1 | Version: 1
[snm] Processing: type=Text, body="Q1 आप अपने गाँव में 10 से 15 न...", next=[2]
[snm] Text node set inputVariable="question1" for node 1
✅ [snm] inputVariable="question1" verified in Redis
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

Data sent successfully! Response: { message: 'Success' }
Returning updated userSession:
Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSMzMxRTEyQkU3NTZBNTQyMTA5AA=='
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
✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSMzMxRTEyQkU3NTZBNTQyMTA5AA==
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

[snm] Final save: currNode=1, inputVariable="question1"
Updated Current Node:  1
Webhook processing completed successfully
🔓 Lock released for 919643393874927560953782559
🔓 [LOCK] Released lock for 919643393874
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:27.191Z
============================================================
✅ Message saved for 919643393874

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

✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSMzMxRTEyQkU3NTZBNTQyMTA5AA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-22T06:16:28.548Z
=====