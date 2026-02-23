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
✅ Tenant Automation Control: Redis connected
✅ Media Redis client connected
✅ Media Redis ready
✅ Redis connections verified
============================================================
🔔 [WEBHOOK-VERIFY] GET /webhook request received - 2026-01-17T20:56:35.914Z
📋 [WEBHOOK-VERIFY] Query params:
   hub.mode: subscribe
   hub.verify_token: [PRESENT]
   hub.challenge: [PRESENT]
received req body:  {}
✅ [WEBHOOK-VERIFY] Webhook verified successfully!
============================================================

========== WEBHOOK: text from 919643393874 ==========

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts_by_tenant/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/whatsapp_tenant
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

[getSession] Flow Data missing for bpid: 606239485906302
[hjiqohe-route] Checking: cmd=true, inFlow=false, media=false, restart=false
[hjiqohe-route] Routing to dedicated handler

========== [hjiqohe] HANDLER START ==========
[hjiqohe] User: 919643393874, Type: text
[hjiqohe] Text: "HelloZestay BZOC"
[hjiqohe] In active flow: false
[hjiqohe] HelloZestay command, guestId: BZOC

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Message saved for 919643393874
[hjiqohe] Processing HelloZestay for guest: BZOC
[hjiqohe] Looking up resort for guest: BZOC
[hjiqohe] Redis hit: Adarsh
[hjiqohe] Resort found: Adarsh
[hjiqohe] Sending welcome: Hi Adarsh Sharma! You have arrived at Adarsh
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/606239485906302/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBO8trGDsP8t4bTe2mRA7sNdZCQ346G9ZANwsi4CVdKM5MwYwaPlirOHAcpDQ63LoHxPfx81tN9h2SUIHc1LUeEByCzS8eQGH2J7wwe9tqAxZAdwr4SxkXGku2l7imqWY16qemnlOBrjYH3dMjN4gamsTikIROudOL3ScvBzwkuShhth0rR9P'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSOTU5QkE3QkQ3QkJEN0YxNEQxAA=='
    }
  ]
}
Tenant sent in send-message:  hjiqohe

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

ℹ️ Could not fetch contact name for analytics
✅ Analytics database connected
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:56:54.188Z
============================================================
⚠️ Slow query (1776ms): 
      INSERT INTO message_events (
        tenant_id, message_id, template_id, template_name,


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSOTU5QkE3QkQ3QkJEN0YxNEQxAA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

✅ Analytics database connected
⚠️ Slow query (1701ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSOTU5QkE3QkQ3QkJEN0YxNEQxAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:56:57.144Z
============================================================
✅ Message saved for 919643393874
❌ saveMessage: Missing required parameters {
  userPhoneNumber: true,
  business_phone_number_id: true,
  formattedConversation: true,
  tenant: false
}
[hjiqohe-route] Handler error: Missing required parameters for saveMessage
✅ Redis connections verified
[userWebhook] Processing: text from 919643393874

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

🔌 Connection removed from pool
✅ Message saved for 919643393874

----- OUTGOING REQUEST -----
URL: https://fastapione-gue2c5ecc9c4b8hy.centralindia-01.azurewebsites.net/notifications
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/replied
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/606239485906302/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBO8trGDsP8t4bTe2mRA7sNdZCQ346G9ZANwsi4CVdKM5MwYwaPlirOHAcpDQ63LoHxPfx81tN9h2SUIHc1LUeEByCzS8eQGH2J7wwe9tqAxZAdwr4SxkXGku2l7imqWY16qemnlOBrjYH3dMjN4gamsTikIROudOL3ScvBzwkuShhth0rR9P'
}
-----------------------------

🔌 Connection removed from pool
Trigger found: hellozestay from message type: text
[triggerFlowById] Flow 208

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/flows/208/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

[triggerFlowById] Flow 208 ready, start=0, next=[1]
[snm] Node: 0 | Version: 1
[snm] Processing: type=string, body="Hi *{{contact.name}}*.  ...", next=[1]

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts-by-phone/919643393874
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

cCess:token:  EAAVZBobCt7AcBO8trGDsP8t4bTe2mRA7sNdZCQ346G9ZANwsi4CVdKM5MwYwaPlirOHAcpDQ63LoHxPfx81tN9h2SUIHc1LUeEByCzS8eQGH2J7wwe9tqAxZAdwr4SxkXGku2l7imqWY16qemnlOBrjYH3dMjN4gamsTikIROudOL3ScvBzwkuShhth0rR9P
Sending message to: 919643393874
Sending Message

----- OUTGOING REQUEST -----
URL: https://graph.facebook.com/v18.0/606239485906302/messages
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  Authorization: 'Bearer EAAVZBobCt7AcBO8trGDsP8t4bTe2mRA7sNdZCQ346G9ZANwsi4CVdKM5MwYwaPlirOHAcpDQ63LoHxPfx81tN9h2SUIHc1LUeEByCzS8eQGH2J7wwe9tqAxZAdwr4SxkXGku2l7imqWY16qemnlOBrjYH3dMjN4gamsTikIROudOL3ScvBzwkuShhth0rR9P'
}
-----------------------------

Message sent successfully: {
  messaging_product: 'whatsapp',
  contacts: [ { input: '919643393874', wa_id: '919643393874' } ],
  messages: [
    {
      id: 'wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSREQwMzhDQUY0OEY2MEQyOTRBAA=='
    }
  ]
}
Tenant sent in send-message:  hjiqohe

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/contacts/phone/919643393874/
METHOD: GET
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

ℹ️ Could not fetch contact name for analytics
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:57:08.781Z
============================================================
✅ Analytics database connected

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

⚠️ Slow query (1761ms): 
      INSERT INTO message_events (
        tenant_id, message_id, template_id, template_name,

✅ [Analytics] Message send tracked: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSREQwMzhDQUY0OEY2MEQyOTRBAA==
Emitted Node Message

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/whatsapp_convo_post/919643393874/?source=whatsapp        
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  'X-Tenant-Id': 'hjiqohe',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

📊 Pool Stats: { total: 2, idle: 1, waiting: 0 }
✅ Analytics database connected
⚠️ Slow query (1831ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSREQwMzhDQUY0OEY2MEQyOTRBAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:57:11.788Z
============================================================
✅ Message saved for 919643393874
[snm] string auto-advance to node 1
[snm] Node: 1 | Version: 1
[snm] Processing: type=customint, body="receptionzestay...", next=[]
[customint] Calling webhook: https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/hjiqohe
Updated Current Node:  1

----- OUTGOING REQUEST -----
URL: https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/hjiqohe
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': 'application/json',
  Authorization: 'Bearer EAAVZBobCt7AcBO8trGDsP8t4bTe2mRA7sNdZCQ346G9ZANwsi4CVdKM5MwYwaPlirOHAcpDQ63LoHxPfx81tN9h2SUIHc1LUeEByCzS8eQGH2J7wwe9tqAxZAdwr4SxkXGku2l7imqWY16qemnlOBrjYH3dMjN4gamsTikIROudOL3ScvBzwkuShhth0rR9P'
}
-----------------------------

🔌 Connection removed from pool
[customint] Received n8n response
[customint] N8N returned empty/invalid response, skipping message send
[customint] Response data: {"message":"Workflow was started"}
[customint] Advanced to node null
Updated Current Node:  null
🔌 Connection removed from pool
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:57:18.800Z
============================================================

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/seen
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

Delivered:  919643393874

----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/individual_message_statistics/
METHOD: POST
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------


----- OUTGOING REQUEST -----
URL: https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net/update-last-seen/919643393874/delivered
METHOD: PATCH
HEADERS SENT: Object [AxiosHeaders] {
  Accept: 'application/json, text/plain, */*',
  'Content-Type': undefined,
  bpid: '606239485906302',
  'X-Service-Key': 'sk_nodejs_mA-XH9BJLiDlmXjA9vGa7XgczT68v3CoQNrcvEx0s34'
}
-----------------------------

⚠️  Redis not available - getTemplateName called in local mode
✅ Analytics database connected
⚠️ Slow query (1763ms): 
    UPDATE message_events
    SET read_at = $2, current_status = $3, updated_at = NOW()
    WHERE m
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSOUQ4ODE2QkZEMTM0QzhGQThBAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:57:21.552Z
============================================================
✅ Analytics database connected
⚠️ Slow query (1959ms): 
    UPDATE message_events
    SET delivered_at = $2, current_status = $3, updated_at = NOW()
    WH
✅ [Analytics] Message event updated: wamid.HBgMOTE5NjQzMzkzODc0FQIAERgSOUQ4ODE2QkZEMTM0QzhGQThBAA==
============================================================
✅ [WEBHOOK] Webhook Processing Complete - 2026-01-17T20:57:22.994Z
============================================================
🔌 Connection removed from pool
🔌 Connection removed from pool