import https from 'https';
import axios from "axios";
import { createClient } from 'redis';
import { google } from 'googleapis';
import { GoogleAuth } from 'google-auth-library';
import { io, userSessions } from "../server.js";
import { getIndianCurrentTime } from '../utils.js';
import { updateStatus, updateLastSeen, saveMessage, sendNotification, executeFallback, getSession, triggerFlowById } from "../helpers/misc.js";
import { findNextNodesFromEdges, findNodeById, extractButtonOptionIndex } from "../helpers/edge-navigation.js";
import { manualWebhook } from "../webhooks/manualWebhook.js";
import { personWebhook } from "../webhooks/personWebhook.js";
import { businessWebhook } from "../webhooks/businessWebhook.js";
import { sendMessage } from "../send-message.js";
import { handleCatalogManagement } from "../drishtee/drishtee.js"
import { checkRRPEligibility, processOrderForDrishtee } from "../drishtee/drishteeservice.js";
import { handleMediaUploads, getImageAndUploadToBlob } from "../helpers/handle-media.js";
import { languageMap } from "../dataStore/dictionary.js";
import { djangoURL, sendNodeMessage } from "./snm.js";
import { normalizePhone } from '../normalize.js';
const redisOptions = {
  url: process.env.REDIS_URL || 'redis://localhost:6379',
  ...(process.env.REDIS_PASSWORD && { password: process.env.REDIS_PASSWORD }),
  socket: {
    reconnectStrategy: (retries) => {
      if (retries > 10) {
        console.error('❌ Redis max retries reached');
        return new Error('Max retries reached');
      }
      const delay = Math.min(retries * 100, 3000);
      console.log(`🔄 Redis reconnecting in ${delay}ms (attempt ${retries})`);
      return delay;
    },
    connectTimeout: 30000,
    keepAlive: 5000,
    noDelay: true
  },
  enableAutoPipelining: true,
  enableOfflineQueue: true
};

const client = createClient(redisOptions);
const mediaClient = createClient(redisOptions);
let isRedisConnected = false; // ✅ CRITICAL FIX

// ✅ Enhanced event handlers for client
client.on('error', (err) => {
  console.error('Redis Client Error:', err.message);
  isRedisConnected = false;
});
client.on('connect', () => {
  console.log('✅ Redis client connected');
  isRedisConnected = true;
});
client.on('reconnecting', () => {
  console.log('🔄 Redis client reconnecting...');
  isRedisConnected = false;
});
client.on('ready', () => {
  console.log('✅ Redis client ready');
  isRedisConnected = true;
});
client.on('end', () => {
  console.log('⚠️ Redis client connection ended');
  isRedisConnected = false;
});
client.on('disconnect', () => {
  console.log('⚠️ Redis client disconnected');
  isRedisConnected = false;
});

// ✅ Complete event handlers for mediaClient
mediaClient.on('error', (err) => console.error('Media Redis Client Error:', err.message));
mediaClient.on('connect', () => console.log('✅ Media Redis client connected'));
mediaClient.on('reconnecting', () => console.log('🔄 Media Redis reconnecting...'));
mediaClient.on('ready', () => console.log('✅ Media Redis ready'));
mediaClient.on('end', () => console.log('⚠️ Media Redis connection ended'));
mediaClient.on('disconnect', () => console.log('⚠️ Media Redis disconnected'));

async function ensureRedisConnection() {
  const maxRetries = 3;
  let attempt = 0;
  
  while (attempt < maxRetries) {
    try {
      if (!client.isOpen) {
        console.log(`🔌 Attempting Redis connection (${attempt + 1}/${maxRetries})...`);
        await client.connect();
      }
      if (!mediaClient.isOpen) {
        await mediaClient.connect();
      }
      
      await client.ping();
      await mediaClient.ping();
      
      console.log('✅ Redis connections verified');
      isRedisConnected = true;
      return true;
      
    } catch (err) {
      attempt++;
      console.error(`❌ Redis connection attempt ${attempt} failed:`, err.message);
      
      if (attempt < maxRetries) {
        const delay = Math.min(attempt * 1000, 5000);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }
  
  console.error('❌ All Redis connection attempts failed');
  isRedisConnected = false;
  return false;
}

// ✅ Keepalive function
async function keepRedisAlive() {
  if (isRedisConnected && client.isOpen && mediaClient.isOpen) {
    try {
      await client.ping();
      await mediaClient.ping();
      console.log('💓 Redis keepalive ping successful');
    } catch (err) {
      console.error('⚠️ Redis keepalive ping failed:', err.message);
      isRedisConnected = false;
      await ensureRedisConnection();
    }
  } else {
    console.log('🔄 Redis not fully connected, attempting reconnection...');
    await ensureRedisConnection();
  }
}

// Call at startup
ensureRedisConnection().catch(console.error);

// ✅ Keepalive every 5 minutes
setInterval(keepRedisAlive, 5 * 60 * 1000);

export const agent = new https.Agent({
  rejectUnauthorized: false,
});



// ==================== HELLOZESTAY (DEPRECATED - Now handled by hjiqoheHandler.js) ====================
// Kept for backward compatibility with imports

export function isInHelloZestayFlow(userPhoneNumber, businessPhoneId) {
  // HelloZestay flow is now handled by the dedicated hjiqoheHandler.js
  // This function is kept for backward compatibility only
  return false;
}


export async function userWebhook(req) {
  // TEMPORARILY REDUCED LOGGING FOR HJIQOHE DEBUGGING
  await ensureRedisConnection().catch(err => {
    console.error('⚠️ Redis connection issue:', err.message);
  });
  const business_phone_number_id = req.body.entry?.[0].changes?.[0].value?.metadata?.phone_number_id;
  const contact = req.body.entry?.[0]?.changes[0]?.value?.contacts?.[0];
  const message = req.body.entry?.[0]?.changes[0]?.value?.messages?.[0];
  const userPhoneNumber = normalizePhone(contact?.wa_id);
  const userName = contact?.profile?.name || null;
  const products = message?.order?.product_items;

  const message_type = message?.type;
  const message_text = message?.text?.body ||
    (message?.interactive ? (message?.interactive?.button_reply?.title ||
      message?.interactive?.list_reply?.title) : null) ||
    message?.button?.text ||
    message?.audio?.id ||
    message?.document?.id ||
    message?.image?.id ||
    message?.video?.id ||
    message?.reaction?.emoji ||
    message?.sticker?.id ||
    JSON.stringify(message?.location);

  console.log(`[userWebhook] Processing: ${message_type} from ${userPhoneNumber}`);

  let timestamp = await getIndianCurrentTime();

  const repliedTo = message?.context?.id || null;
  if (repliedTo !== null) updateStatus("replied", repliedTo, null, null, null, null, timestamp);

  // Get user session (HelloZestay for hjiqohe is now handled by dedicated handler in webhookRoute.js)
  const userSession = await getSession(business_phone_number_id, contact);

  const sessionKey = userSession.userPhoneNumber + userSession.business_phone_number_id;

  // Extract trigger text for trigger handling
  const triggerText = message?.text?.body ||
    message?.interactive?.button_reply?.title ||
    message?.interactive?.list_reply?.title ||
    message?.button?.text;

  try {
    let formattedConversation;
    if (message_type == "text" || message_type == "interactive" || message_type == "button") {
      formattedConversation = [{
        text: message_text,
        sender: "user",
        message_type: "text"
      }];
    }
    else if (message_type == "reaction") {
      const emoji = message?.reaction?.emoji;
      const messageId = message?.reaction?.message_id;
      formattedConversation = [{
        text: `Reacted ${emoji} to message`,
        sender: "user",
        message_type: "reaction"
      }];
    }
    else if (message_type == "sticker") {
      formattedConversation = [{
        text: "[Sticker]",
        sender: "user",
        message_type: "sticker"
      }];
    }
    else if (message_type == "image") {
      const mediaID = message?.image?.id;
      const caption = message?.image?.caption || "";

      try {
        console.log(`📷 Processing image upload: ${mediaID}`);
        const blobUrl = await getImageAndUploadToBlob(mediaID, userSession.accessToken);

        formattedConversation = [{
          message_type: "image",
          media_url: blobUrl,
          media_caption: caption,
          text: caption || "",
          sender: "user"
        }];

        console.log(`✅ Image uploaded to Blob: ${blobUrl}`);
      } catch (error) {
        console.error("❌ Error uploading image to blob:", error.message);
        // Fallback to placeholder if upload fails
        formattedConversation = [{
          message_type: "image",
          text: caption ? `[Image: ${caption}]` : "[Image]",
          sender: "user"
        }];
      }
    }
    else if (message_type == "video") {
      const mediaID = message?.video?.id;
      const caption = message?.video?.caption || "";

      try {
        console.log(`🎥 Processing video upload: ${mediaID}`);
        const blobUrl = await getImageAndUploadToBlob(mediaID, userSession.accessToken);

        formattedConversation = [{
          message_type: "video",
          media_url: blobUrl,
          media_caption: caption,
          text: caption || "",
          sender: "user"
        }];

        console.log(`✅ Video uploaded to Blob: ${blobUrl}`);
      } catch (error) {
        console.error("❌ Error uploading video to blob:", error.message);
        formattedConversation = [{
          message_type: "video",
          text: caption ? `[Video: ${caption}]` : "[Video]",
          sender: "user"
        }];
      }
    }
    else if (message_type == "document") {
      const mediaID = message?.document?.id;
      const filename = message?.document?.filename || "document";

      try {
        console.log(`📄 Processing document upload: ${mediaID}`);
        const blobUrl = await getImageAndUploadToBlob(mediaID, userSession.accessToken);

        formattedConversation = [{
          message_type: "document",
          media_url: blobUrl,
          media_filename: filename,
          text: filename,
          sender: "user"
        }];

        console.log(`✅ Document uploaded to Blob: ${blobUrl}`);
      } catch (error) {
        console.error("❌ Error uploading document to blob:", error.message);
        formattedConversation = [{
          message_type: "document",
          text: `[Document: ${filename}]`,
          sender: "user"
        }];
      }
    }
    else if (message_type == "audio") {
      const mediaID = message?.audio?.id;

      try {
        console.log(`🎵 Processing audio upload: ${mediaID}`);
        const blobUrl = await getImageAndUploadToBlob(mediaID, userSession.accessToken);

        formattedConversation = [{
          message_type: "audio",
          media_url: blobUrl,
          text: "",
          sender: "user"
        }];

        console.log(`✅ Audio uploaded to Blob: ${blobUrl}`);
      } catch (error) {
        console.error("❌ Error uploading audio to blob:", error.message);
        formattedConversation = [{
          message_type: "audio",
          text: "[Voice message]",
          sender: "user"
        }];
      }
    }
    else if (message_type == "location") {
      const lat = message?.location?.latitude;
      const lng = message?.location?.longitude;
      const locationName = message?.location?.name || "";
      formattedConversation = [{
        text: locationName ? `[Location: ${locationName}]` : "[Location shared]",
        sender: "user",
        message_type: "location",
        media_caption: lat && lng ? `${lat},${lng}` : ""
      }];
    }
    else if (message_type == "contacts") {
      const contactName = message?.contacts?.[0]?.name?.formatted_name || "Unknown";
      formattedConversation = [{
        text: `[Contact shared: ${contactName}]`,
        sender: "user",
        message_type: "contacts"
      }];
    }

    // Save incoming message
    try {
      await saveMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, formattedConversation, userSession.tenant, timestamp);
    } catch (saveError) {
      console.error(`❌ CRITICAL: Failed to save incoming message for ${userSession.userPhoneNumber}:`, saveError.message);
      // Retry once after a short delay
      try {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await saveMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, formattedConversation, userSession.tenant, timestamp);
        console.log(`✅ Message saved on retry for ${userSession.userPhoneNumber}`);
      } catch (retryError) {
        console.error(`❌ CRITICAL: Retry also failed for ${userSession.userPhoneNumber}:`, retryError.message);
      }
    }

    const notif_body = { content: `${userSession.userPhoneNumber} | New meessage from ${userSession.userName || userSession.userPhoneNumber}: ${message_text}`, created_on: timestamp };
    sendNotification(notif_body, userSession.tenant);

    ioEmissions(message, userSession, timestamp);
    updateLastSeen("replied", timestamp, userSession.userPhoneNumber, userSession.business_phone_number_id);

    if (userSession.type == "nothing") {
      return;
    }

    await sendReadAndTypingIndicator(message.id, business_phone_number_id, userSession.accessToken);

    const agents = userSession.agents;
    if (agents) {
      const isBusiness = agents.includes(userPhoneNumber);
      if (isBusiness) return businessWebhook(req);
    }

    if (userSession.type == "one2one") {
      return manualWebhook(req, userSession);
    }
    else if (userSession.type == 'person') {
      return personWebhook(req, userSession);
    }

    if (message_text == "/human") {
      userSession.type = "one2one";
      const key = userPhoneNumber + business_phone_number_id;
      await userSessions.set(key, userSession);
      return sendWelcomeMessage(userSession);
    }
    else if (message_text == '/person') {
      userSession.type = 'person';
      return personWebhook(req, userSession);
    }
    else if (message_text == '/language') {
      if (!userSession.doorbell) return;
      
      const key = String(userPhoneNumber) + String(business_phone_number_id);
      await userSessions.delete(key);
      userSession = await getSession(business_phone_number_id, contact);
      return sendLanguageSelectionMessage(userSession.doorbell, userSession.accessToken, userSession.userPhoneNumber, userSession.business_phone_number_id, userSession.tenant);
    }

    // Regular trigger handling
    if (triggerText) {
      const messageText = triggerText.trim().toLowerCase();
      const prefixEnabledTriggers = ["checkin", "hellozestay", "/review"];

      for (const triggerKey in userSession.triggers) {
        const isPrefixMatch = prefixEnabledTriggers.includes(triggerKey.toLowerCase()) &&
                              messageText.startsWith(triggerKey.toLowerCase());
        const isExactMatch = messageText === triggerKey.toLowerCase();

        if (isPrefixMatch || isExactMatch) {
          try {
            console.log("Trigger found:", triggerKey, "from message type:", message_type);
            const id = userSession.triggers[triggerKey];

            if (isPrefixMatch && message?.text?.body) {
              const parts = messageText.split(" ");
              if (parts.length > 1) {
                userSession.guestId = parts[1];
              }
            }

            await triggerFlowById(userSession, id);
            return;
          } catch (error) {
            console.log("Error in triggering flow:", error.response?.data || error.message);
          }
        }
      }
    }

    if (userSession.tenant == 'leqcjsk') {
      if (userSession?.isRRPEligible == undefined) userSession = await checkRRPEligibility(userSession);
      if (userSession?.isRRPEligible && message_type == "order") return processOrderForDrishtee(userSession, products);
      else if (!userSession?.isRRPEligible) {
        const messageData = {
          type: 'text',
          text: {
            body: 'Sorry, our services are not available in your area. Please join our RRP network to avail these services.'
          }
        };
        return sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, messageData, userSession.accessToken, userSession.tenant);
      }
    }

    if (userSession?.flowData && userSession?.flowData.length == 0) return;

    if (userSession.multilingual && !['order', 'location'].includes(message_type)) {
      if (message_type === "text" || message_type == "interactive") {
        const doorbell = userSession.doorbell;
        const language_data = doorbell?.languages;

        const languageKeys = Object.keys(language_data);
        const languageValues = Object.values(language_data);

        if (languageKeys.includes(message_text) || languageValues.includes(message_text)) {
          let lang_code;
          if (languageKeys.includes(message_text)) {
            const language = language_data[message_text];
            lang_code = languageMap[language];
          } else {
            lang_code = languageMap[message_text];
          }

          const flowData = userSession.flowData;
          userSession.language = lang_code;

          const selectedFlowData = flowData.find(data => data.language === lang_code);
          userSession.flowData = selectedFlowData?.flow_data;

          userSession.multilingual = false;
          userSession.fallback_msg = selectedFlowData?.fallback_message;

          sendNodeMessage(userPhoneNumber, business_phone_number_id);
        }
        else {
          sendLanguageSelectionMessage(doorbell, userSession.accessToken, userSession.userPhoneNumber, userSession.business_phone_number_id, userSession.tenant);
        }
      }
      return;
    }

    if (userSession.AIMode) {
      if (message_type == "interactive") {
        let userSelectionID = message?.interactive?.button_reply?.id || message?.interactive?.list_reply?.id;
        if (userSelectionID == "Exit AI") {
          userSession.AIMode = false;
          userSession.nextNode = userSession.adjList[userSession.currNode];
          userSession.currNode = userSession.nextNode[0];
          sendNodeMessage(userPhoneNumber, business_phone_number_id);
        }
        else if (userSelectionID.startsWith("Hop")) {
          const node = Number(userSelectionID.split(":")[1]);
          userSession.AIMode = false;
          userSession.currNode = node;
          userSession.nextNode = userSession.adjList[userSession.currNode];
          sendNodeMessage(userSession.userPhoneNumber, userSession.business_phone_number_id);
        }
      }
      else if (message_type == "text") {
        const query = message.text.body;
        handleQuery(query, userSession);
      }
      else if (message_type == "audio") {
        try {
          const mediaID = message.audio.id;
          const response = await axios.post("https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/voice", { mediaID: mediaID, userSession: userSession });
          const query = response.data;
          handleQuery(query, userSession);
        } catch (error) {
          console.log("error handling audio query:", error.response?.data || error.message);
        }
      }
      else if (message_type == "image" || message_type == "document" || message_type == "video") {
        const mediaID = message?.image?.id || message?.document?.id || message?.video?.id;
        const doc_name = userSession.inputVariable;
        try {
          await handleMediaUploads(userName, userPhoneNumber, doc_name, mediaID, userSession, userSession.tenant);
        } catch (error) {
          console.error("Error retrieving media content:", error);
        }
      }
      return;
    }

    handleInput(userSession, message_text);
    
    if (message_type === "interactive") {
      if (message.interactive.type === "nfm_reply") {
        let nfm_response = message.interactive.nfm_reply.response_json;
        const responseJson = JSON.parse(nfm_response);
        console.log("Flow response: ", responseJson);
        const flowName = responseJson.flow_name || "Unknown_Flow";
        const sheetName = flowName;
        const spreadsheet_id = "1QBhLjiD8MCflufTNE0K51qsLtMyI0lyQIoM7Pg9aBYU";
        const auth = new GoogleAuth({
          credentials: JSON.parse(Buffer.from(process.env.GOOGLE_SERVICE_ACCOUNT_BASE64, 'base64').toString('utf-8')),
          scopes: 'https://www.googleapis.com/auth/spreadsheets',
        });
        const sheets = google.sheets({ version: 'v4', auth });

        const timestamp = await getIndianCurrentTime();
        let rowData = [userSession.tenant, userSession.userPhoneNumber, timestamp];
        Object.keys(responseJson).forEach(key => {
          if (key !== 'flow_name') {
            rowData.push(responseJson[key] || '');
          }
        });
        try {
          await axios.post(
            "https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/nfm",
            {
              tenant: userSession.tenant,
              phone: userSession.userPhoneNumber,
              timestamp: timestamp,
              flow_name: flowName,
              data: responseJson
            }
          );
          console.log("NFM JSON sent to external webhook successfully.");
        } catch (err) {
          console.error("Failed to send NFM JSON to external webhook:", err.message);
        }
        try {
          const response = await sheets.spreadsheets.values.append({
            spreadsheetId: spreadsheet_id,
            range: `${sheetName}!A:Z`,
            valueInputOption: 'RAW',
            insertDataOption: 'INSERT_ROWS',
            resource: {
              values: [rowData]
            }
          });
          console.log(`${response.data.updates.updatedCells} cells appended.`);
        } catch (error) {
          console.error('Error appending data to sheet:', error);
        }

        // FlowJSON node already advanced currNode when it sent the flow
        // So we just need to process the current node (which is already the next node after flowjson)
        console.log(`📨 NFM reply received for flow: ${flowName}`);
        console.log(`📍 Current node after flow: ${userSession.currNode}`);

        // Process the current node (no need to advance again)
        sendNodeMessage(userPhoneNumber, business_phone_number_id);
        return;
      }
      else {
        let userSelectionID = message?.interactive?.button_reply?.id || message?.interactive?.list_reply?.id;

        if (userSelectionID === "restart_flow") {
          console.log(`🔄 Restart button clicked for ${userSession.userPhoneNumber}`);

          userSession.currNode = userSession.flowVersion === 2 ? userSession.startNodeId : userSession.startNode;

          if (userSession.flowVersion === 2) {
            userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
          } else {
            userSession.nextNode = userSession.adjList[userSession.startNode];
          }

          userSession.inputVariable = null;
          const sessionKey = userSession.userPhoneNumber + userSession.business_phone_number_id;
          await userSessions.set(sessionKey, userSession);
          sendNodeMessage(userPhoneNumber, business_phone_number_id);
          return;
        }

        if (typeof userSelectionID == "string" && userSelectionID.split('_')[0] == 'drishtee') {
          handleCatalogManagement(userSelectionID, userSession);
        }

        // DUAL MODE NAVIGATION
        if (userSession.flowVersion === 2) {
          // NEW MODE: Edge-based navigation
          console.log("Using edge-based navigation (v2)");

          const sourceHandle = extractButtonOptionIndex(
            userSelectionID,
            userSession.nodes,
            userSession.edges,
            userSession.currNode
          );

          const nextNodes = findNextNodesFromEdges(
            userSession.edges,
            userSession.currNode,
            sourceHandle
          );

          if (nextNodes.length > 0) {
            // SINGLE ADVANCE (FIX: no double-advance)
            userSession.currNode = nextNodes[0];
            userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
            console.log(`Advanced to node: ${userSession.currNode}`);
          } else {
            console.warn(`No matching edge found for selection ${userSelectionID}`);
            await executeFallback(userSession);
            return;
          }

        } else {
          // LEGACY MODE: Adjacency list navigation (WITH FIX)
          console.log("Using adjacency list navigation (legacy)");

          let found = false;

          // First: check in nextNode array
          for (let i = 0; i < userSession.nextNode.length; i++) {
            if (userSession.flowData[userSession.nextNode[i]].id == userSelectionID) {
              // FIX: Single advance only
              userSession.currNode = userSession.nextNode[i];
              userSession.nextNode = userSession.adjList[userSession.currNode];
              // REMOVED: userSession.currNode = userSession.nextNode[0];  <-- DOUBLE-ADVANCE BUG FIXED
              found = true;
              console.log(`Found in nextNode array, advanced to: ${userSession.currNode}`);

              // CRITICAL FIX: Auto-advance through button_element/list_element nodes
              const nodeType = userSession.flowData[userSession.currNode]?.type;
              if (nodeType === 'button_element' || nodeType === 'list_element') {
                const oldNode = userSession.currNode;
                console.log(`🔧 BUTTON CLICK: Auto-advancing through ${nodeType} node ${oldNode}`);

                if (userSession.nextNode && userSession.nextNode.length > 0) {
                  userSession.currNode = userSession.nextNode[0];
                  userSession.nextNode = userSession.adjList[userSession.currNode];
                  console.log(`🔧 Auto-advanced from ${nodeType} ${oldNode} to target ${userSession.currNode}`);
                } else {
                  console.error(`⚠️ ${nodeType} node ${oldNode} has no nextNode!`);
                }
              }

              break;
            }
          }

          // Second: global search in flowData
          if (!found) {
            for (let i = 0; i < userSession.flowData.length; i++) {
              if (userSession.flowData[i].id == userSelectionID) {
                // FIX: Single advance only
                userSession.currNode = i;
                userSession.nextNode = userSession.adjList[userSession.currNode];
                // REMOVED: userSession.currNode = userSession.nextNode[0];  <-- DOUBLE-ADVANCE BUG FIXED

                // Handle input variable from parent
                for (let j = 0; j < userSession.flowData.length; j++) {
                  if (userSession.adjList[j].includes(i)) {
                    var variable = userSession.flowData[j].variable;
                    if (variable) {
                      userSession.inputVariable = variable;
                      handleInput(userSession, message_text);
                    }
                  }
                }
                console.log(`Found in global search, advanced to: ${userSession.currNode}`);
                break;
              }
            }
          }

          // CRITICAL FIX: Auto-advance through button_element/list_element nodes
          // After button click, if we landed on a button_element, advance through it automatically
          const currentNodeType = userSession.flowData[userSession.currNode]?.type;
          if (currentNodeType === 'button_element' || currentNodeType === 'list_element') {
            const oldNode = userSession.currNode;
            console.log(`🔧 BUTTON CLICK: Auto-advancing through ${currentNodeType} node ${oldNode}`);

            // Advance through the element to the actual target node
            if (userSession.nextNode && userSession.nextNode.length > 0) {
              userSession.currNode = userSession.nextNode[0];
              userSession.nextNode = userSession.adjList[userSession.currNode];
              console.log(`🔧 Auto-advanced from button_element ${oldNode} to actual target ${userSession.currNode}`);
            } else {
              console.error(`⚠️ button_element node ${oldNode} has no nextNode!`);
            }
          }
        }
      }
    }
    else if (message_type === "text" || message_type == "image") {
      // 🔍 HELLOZESTAY DEBUG: Log when image arrives
      if (userSession.tenant === 'hjiqohe') {
        console.log(`🔍 [hjiqohe] Image/Text received in flow`);
        console.log(`   currNode: ${userSession.currNode}`);
        console.log(`   flowVersion: ${userSession.flowVersion}`);
        console.log(`   flowData length: ${userSession.flowData?.length}`);
        console.log(`   isTrigger: ${userSession.isTrigger}`);
        console.log(`   inputVariable: ${userSession.inputVariable}`);
      }
      if (userSession.flowVersion === 2) {
        // NEW MODE
        const currNodeObj = findNodeById(userSession.nodes, userSession.currNode);
        const nodeType = currNodeObj?.type;

        const startNode = userSession.startNodeId || userSession.startNode;
        if (userSession.currNode != startNode) {
          console.log("Node Type: ", nodeType);

          if (['sendMessage', 'ai', 'api', 'template', 'customint', 'flowjson'].includes(nodeType)) {
            // Auto-advance for message nodes
            const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
            if (nextNodes.length > 0) {
              userSession.currNode = nextNodes[0];
            }
          }
          else if (['askQuestion'].includes(nodeType)) {
            // Check if expecting text input
            const data = currNodeObj?.data || {};
            if (data.optionType === 'Text') {
              // Text input - advance
              const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
              if (nextNodes.length > 0) {
                userSession.currNode = nextNodes[0];
              }
            } else {
              // Button/List - should use interactive, fallback
              await executeFallback(userSession);
              return;
            }
          }
        }
      } else {
        // LEGACY MODE
        const flow = userSession.flowData;
        const type = flow[userSession.currNode]?.type;

        console.log("=== LEGACY MODE DEBUG ===");
        console.log("Current Node:", userSession.currNode);
        console.log("Node Type:", type);
        console.log("Next Node Array:", userSession.nextNode);
        console.log("Adjacency List:", JSON.stringify(userSession.adjList));
        console.log("========================");

        // CRITICAL: button_element is a button OPTION, not an interactive node
        // If user is stuck at a button_element, they must have arrived there incorrectly
        // We should advance them automatically through it
        if (type === 'button_element' || type === 'list_element') {
          const oldNode = userSession.currNode;
          console.log(`FIXING: User stuck at ${type} node ${oldNode}, auto-advancing...`);

          // Auto-advance through button/list elements
          userSession.currNode = userSession.nextNode[0];
          userSession.nextNode = userSession.adjList[userSession.currNode];

          console.log(`Auto-advanced from ${oldNode} to ${userSession.currNode}`);
        }
        // CRITICAL: Auto-advancing nodes (string, customint, api, template, custom)
        // These nodes execute automatically and don't wait for user input
        // If user sends text while at these nodes, still process them via sendNodeMessage
        // The session save before sendNodeMessage + save inside each case prevents loops
        else if (['string', 'customint', 'api', 'template', 'custom', 'flowjson'].includes(type)) {
          console.log(`User at auto-advancing node "${type}" - will execute via sendNodeMessage`);
          // Continue to sendNodeMessage - the node will process and advance automatically
        }
        // Text input nodes should advance after receiving text
        else if (['Text', 'audio', 'video', 'location', 'image', 'AI', 'product'].includes(type)) {
          // Save old node for logging
          const oldNode = userSession.currNode;

          console.log(`Before advancement: currNode=${oldNode}, nextNode=${userSession.nextNode}`);

          // Advance to next node
          userSession.currNode = userSession.nextNode[0];
          // CRITICAL: Update nextNode using adjacency list
          userSession.nextNode = userSession.adjList[userSession.currNode];

          console.log(`After advancement: currNode=${userSession.currNode}, nextNode=${userSession.nextNode}`);
          console.log(`Advanced from ${oldNode} to ${userSession.currNode} after text input`);

          // 🔍 HELLOZESTAY DEBUG: Log the new node details
          if (userSession.tenant === 'hjiqohe') {
            const newNodeData = userSession.flowData?.[userSession.currNode];
            console.log(`🔍 [hjiqohe] New node details:`);
            console.log(`   newNode type: ${newNodeData?.type}`);
            console.log(`   newNode body: ${newNodeData?.body?.substring?.(0, 50) || newNodeData?.body}`);
          }
        }
        else if (['Button', 'List'].includes(type)) {
          // User sent text to a button/list node - fallback
          console.log("User sent text to Button/List node - executing fallback");
          await executeFallback(userSession);
          return;
        }
        else {
          console.log(`WARNING: Unhandled node type "${type}" - no advancement`);
        }
      }
    }
    else if (message_type == "audio") {
      // LEGACY MODE: Advance for audio messages
      if (userSession.flowVersion !== 2) {
        const oldNode = userSession.currNode;
        userSession.currNode = userSession.nextNode[0];
        userSession.nextNode = userSession.adjList[userSession.currNode];
        console.log(`Audio message: Advanced from ${oldNode} to ${userSession.currNode}`);
      } else {
        // V2 mode handling if needed
        userSession.currNode = userSession.nextNode[0];
      }
    }
    else if (message_type == "document") {
      // LEGACY MODE: Advance for document messages
      if (userSession.flowVersion !== 2) {
        const oldNode = userSession.currNode;
        userSession.currNode = userSession.nextNode[0];
        userSession.nextNode = userSession.adjList[userSession.currNode];
        console.log(`Document message: Advanced from ${oldNode} to ${userSession.currNode}`);
      } else {
        // V2 mode handling if needed
        userSession.currNode = userSession.nextNode[0];
      }
    }
   else if (message_type == "order") {
      console.log("xyz");
      let urltest = "https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/customNode";
      if (userSession.tenant == 'ecdayvn')
        urltest = "https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/order-payment";
      try {
        const config = {
          headers: {
            'Authorization': `Bearer ${userSession.accessToken}`,
            'Content-Type': 'application/json'
          }
        };
        const requestBody = {
          message,
          userSession
        };
        await axios.post(urltest, requestBody, config);
      } catch (err) {
        console.log("error in order", err.message);
      }
      return;
    }
    else if (message_type == "location") {
      if (userSession.tenant == 'ecdayvn') {
        const url = "https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/order-payment";
        try {
          const config = {
            headers: {
              'Authorization': `Bearer ${userSession.accessToken}`,
              'Content-Type': 'application/json'
            }
          };
          const requestBody = {
            message,
            userSession
          };
          await axios.post(url, requestBody, config);
        } catch (err) {
          console.log("error in location", err.message);
        }
        return;
      } else if (userSession.tenant !== 'ecdayvn') {
        const url = "https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/a0d463e0-ed45-4642-bb11-da3c132a533b";
        try {
          const config = {
            headers: {
              'Authorization': `Bearer ${userSession.accessToken}`,
              'Content-Type': 'application/json'
            }
          };
          const requestBody = {
            message,
            userSession
          };
          await axios.post(url, requestBody, config);
        } catch (err) {
          console.log("error in location for other tenants", err.message);
        }
        return;
      }
      userSession.currNode = userSession.nextNode[0];
    }
    else if (message_type == "reaction") {
      // Reactions are already saved to conversation, no flow progression needed
      console.log(`Reaction ${message?.reaction?.emoji} saved to conversation`);
      return;
    }
    else if (message_type == "sticker") {
      // Stickers are already saved to conversation, no flow progression needed
      console.log("Sticker saved to conversation");
      return;
    }
    else if (message_type == "contacts") {
      // Contact shares are already saved to conversation
      console.log("Contact shared saved to conversation");
      return;
    }

    // CRITICAL FIX: Save session BEFORE sendNodeMessage retrieves it from storage
    // Otherwise sendNodeMessage will get the old session state without node advancement
    await userSessions.set(sessionKey, userSession);
    console.log("Session saved before sending node message");

    sendNodeMessage(userPhoneNumber, business_phone_number_id);
    console.log("Webhook processing completed successfully");
  } finally {
    // Save session state after processing
    await userSessions.set(sessionKey, userSession);
  }
}
function assignAgent(agentList) {
  for (let agent of agentList) {
    if (agent in nurenConsumerMap) continue
    else return agent
  }
  return agentList[0]
}

async function sendReadAndTypingIndicator(message_id, business_phone_number_id, access_token) {
  try {
    await axios.post(
      `https://graph.facebook.com/v18.0/${business_phone_number_id}/messages`,
      {
        messaging_product: "whatsapp",
        status: "read",
        message_id: message_id,
        typing_indicator: { type: "text" }
      },
      { headers: { Authorization: `Bearer ${access_token}` } }
    );
  } catch (error) {
    console.error("Error sending read receipt and typing indicator:", error?.response?.data || error.message);
  }
}

async function sendWelcomeMessage(userSession) {
  const waitingMessageForConsumer = "Hang tight! We're connecting you with an agent. It won't take long. ⏳"
  sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, { type: "text", text: { body: waitingMessageForConsumer } }, userSession.accessToken, userSession.tenant)

  const welcomeMessageForRetailer = `${userSession.userName} wants to chat with you! Press the button to start the conversation. 🚀`
  const buttonMessageBody = {
    type: "interactive",
    interactive: {
      type: "button",
      body: { text: welcomeMessageForRetailer },
      action: { buttons: [{ type: "reply", reply: { id: `chatwith_${userSession.userPhoneNumber}`, title: "Start Talking" } }] }
    }
  }
  const agents = userSession.agents
  agents.forEach(agent => {
    sendMessage(agent, userSession.business_phone_number_id, buttonMessageBody, userSession.accessToken, userSession.tenant)
  })
}

async function handleQuery(query, userSession) {
  try {
    const nodes = userSession.hop_nodes;
    const language = Object.keys(languageMap).find(key => languageMap[key] === userSession.language) || "English";
    const prompt = userSession.AIModePrompt || "You are a helpful assistant. Reply to the point. Dont include any apologies or explanations in your replies. IMPORTANT: Your entire response must be 1000 characters or less due to WhatsApp message limitations."
    const userPhoneNumber = userSession.userPhoneNumber;
    const data = { query: query, nodes: nodes, language: language, prompt: prompt, phone: userPhoneNumber };
    const headers = { 'X-Tenant-Id': userSession.tenant };
    const response = await axios.post(`${djangoURL}/query-faiss/`, data, { headers: headers });
    console.log("openai response:", response.data);

    const nodeId = response.data.id;
    const messageText = response.data.message;
    const fixedMessageText = messageText.replace(/"/g, "'");
    const messageData = {
      type: "interactive",
      interactive: {
        type: "button",
        body: { text: fixedMessageText },
        action: {
          buttons: [
            {
              type: 'reply',
              reply: {
                id: "Exit AI",
                title: "Exit"
              }
            }
          ]
        }
      }
    }
    await sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, messageData, userSession.accessToken, userSession.tenant)

    if (nodeId != -1) {
      const index = nodes.findIndex(obj => obj.id == nodeId)
      const action = nodes[index].action;
      const messageData = {
        type: "interactive",
        interactive: {
          type: "button",
          body: { text: `Do you want to explore ${action} further?` },
          action: {
            buttons: [
              {
                type: 'reply',
                reply: {
                  id: `Hop:${nodeId}`,
                  title: "Yes"
                }
              }
            ]
          }
        }
      }
      sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, messageData, userSession.accessToken, userSession.tenant)
    }
  } catch (error) {
    console.log("Error in openai response:", error.response?.data || error.message);
  }
}

async function sendLanguageSelectionMessage(doorbell, access_token, phoneNumber, business_phone_number_id, tenant_id) {
  let messageData = {}
  if (doorbell.type === "button") {
    let button_rows = Object.entries(doorbell.languages).map(([key, value]) => ({
      type: 'reply',
      reply: {
        id: key,
        title: value
      }
    }));
    messageData = {
      type: "interactive",
      interactive: {
        type: "button",
        body: { text: doorbell.message },
        action: { buttons: button_rows }
      }
    };
  }
  else if (doorbell.type === "list") {
    let list_rows = Object.entries(doorbell.languages).map(([key, value]) => ({
      id: key,
      title: value
    }));
    messageData = {
      type: "interactive",
      interactive: {
        type: "list",
        body: { text: doorbell.message },
        action: {
          button: "Choose Language",
          sections: [{ title: "Section Title", rows: list_rows }]
        }
      }
    };
  }
  else {
    messageData = {
      type: "text",
      text: {
        body: doorbell.message
      }
    };
  }
  return sendMessage(phoneNumber, business_phone_number_id, messageData, access_token, tenant_id);
}

async function handleInput(userSession, value) {
  console.log("handleInput called with value:", value);

  try {
    if (
      userSession.inputVariable !== undefined &&
      userSession.inputVariable !== null &&
      userSession.inputVariable.length > 0
    ) {
      console.log("Valid inputVariable detected:", userSession.inputVariable);

      const input_variable = userSession.inputVariable;
      const phone = userSession.userPhoneNumber;
      const flow_name = userSession.flowName;

      console.log("Extracted user session details:", { input_variable, phone, flow_name });

      userSession.api.POST[input_variable] = value;
      console.log(`Stored value in userSession.api.POST[${input_variable}] = ${value}`);

      userSession.inputVariable = null;
      console.log("Cleared inputVariable after storing value");

      const payload = { flow_name, input_variable, value, phone };
      console.log("Constructed payload:", payload);

      try {
        console.log("Sending data to API:", `${djangoURL}/add-dynamic-data/`);
        const response = await axios.post(`${djangoURL}/add-dynamic-data/`, payload, {
          headers: { 'X-Tenant-Id': userSession.tenant }
        });

        console.log("Data sent successfully! Response:", response.data);
      } catch (error) {
        console.error("Error while sending data in handleInput:", error.response?.data || error.message);
      }
    } else {
      console.log("No valid inputVariable found, skipping API call.");
    }
  } catch (error) {
    console.error("Unexpected error in handleInput:", error);
  }

  console.log("Returning updated userSession:");
  return userSession;
}

export async function ioEmissions(message, userSession, timestamp) {
  const message_text = message?.text?.body || (message?.interactive ? (message?.interactive?.button_reply?.title || message?.interactive?.list_reply?.title) : null)
  const temp_user = message?.text?.body?.startsWith('*/') ? message.text.body.split('*/')[1]?.split(' ')[0] : null;
  if (temp_user) {
    io.emit('temp-user', {
      temp_user: temp_user,
      phone_number_id: userSession.business_phone_number_id,
      contactPhone: userSession.userPhoneNumber,
      time: timestamp
    });
  }

  io.emit('new-message', {
    message: { type: "text", text: { body: message_text } },
    phone_number_id: userSession.business_phone_number_id,
    contactPhone: userSession.userPhoneNumber,
    name: userSession.userName,
    time: timestamp
  });
}
