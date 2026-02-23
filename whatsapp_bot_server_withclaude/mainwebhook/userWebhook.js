import https from 'https';
import axios from "axios";
import { google } from 'googleapis';
import { GoogleAuth } from 'google-auth-library';
import { io, userSessions } from "../server.js";
import { isAgent } from "../helpers/agentMapping.js";
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
import { djangoURL, fastURL, sendNodeMessage } from "./snm.js";
import { normalizePhone } from '../normalize.js';
import { evaluateMCPTools } from '../services/mcpToolRouter.js';
import { processWithQueue, isMessageProcessed, markMessageProcessed, acquireUserLock, releaseUserLock } from '../helpers/userMessageQueue.js';
import sessionManager from '../sessionManager.js';

// ✅ OPTIMIZED: Removed redundant Redis clients - now uses sessionManager's single connection
// This prevents Redis connection pool exhaustion

async function ensureRedisConnection() {
  try {
    if (!sessionManager.isConnected) {
      console.log('🔌 Attempting Redis connection via sessionManager...');
      await sessionManager.connect();
    }
    console.log('✅ Redis connections verified');
    return true;
  } catch (err) {
    console.error('❌ Redis connection failed:', err.message);
    return false;
  }
}

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
  const messageId = message?.id; // WhatsApp message ID for deduplication

  // ==================== MESSAGE DEDUPLICATION ====================
  // Check if this exact message has already been processed
  if (messageId) {
    const isDuplicate = await isMessageProcessed(messageId);
    if (isDuplicate) {
      console.log(`🔄 [DUPLICATE] Skipping already processed message: ${messageId.substring(0, 30)}...`);
      return;
    }
    // Mark as processed immediately to prevent race conditions
    await markMessageProcessed(messageId);
  }
  // ==================== END DEDUPLICATION ====================

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

  console.log(`[userWebhook] Processing: ${message_type} from ${userPhoneNumber} (msgId: ${messageId?.substring(0, 20)}...)`);

  let timestamp = await getIndianCurrentTime();

  const repliedTo = message?.context?.id || null;
  if (repliedTo !== null) updateStatus("replied", repliedTo, null, null, null, null, timestamp);

  // Get user session (HelloZestay for hjiqohe is now handled by dedicated handler in webhookRoute.js)
  let userSession = await getSession(business_phone_number_id, contact);

  const sessionKey = userSession.userPhoneNumber + userSession.business_phone_number_id;

  // FIX: Re-read session from Redis to get the LATEST inputVariable
  // This is needed because getSession may return a cached/stale version
  // while snm.js from the previous request saved a newer version with inputVariable
  const latestSession = await userSessions.get(sessionKey);
  if (latestSession && latestSession.inputVariable && !userSession.inputVariable) {
    userSession.inputVariable = latestSession.inputVariable;
    userSession.inputVariableType = latestSession.inputVariableType;
    console.log(`📝 [inputVariable] RECOVERED inputVariable="${userSession.inputVariable}" from Redis (was missing in getSession)`);
  }

  // ENHANCED FIX: If still no inputVariable, try to get it from current node configuration
  // This fixes the issue where text inputs don't get recorded for certain phone numbers
  if (!userSession.inputVariable) {
    let currNodeData, nodeType;

    // Handle both legacy (flowData) and V2 (nodes) flow structures
    if (userSession.flowVersion === 2) {
      // V2 flow: find node in nodes array
      currNodeData = userSession.nodes?.find(n => n.id === userSession.currNode)?.data;
      nodeType = userSession.nodes?.find(n => n.id === userSession.currNode)?.type;
    } else {
      // Legacy flow: index into flowData array
      currNodeData = userSession.flowData?.[userSession.currNode];
      nodeType = currNodeData?.type;
    }

    // Check if current node should have an inputVariable
    // V2 uses 'askQuestion', legacy uses 'Text', 'Button', 'List'
    const inputNodeTypes = ['Text', 'Button', 'List', 'askQuestion'];
    if (inputNodeTypes.includes(nodeType) && currNodeData?.variable) {
      userSession.inputVariable = currNodeData.variable;
      userSession.inputVariableType = currNodeData.dataType || 'text';
      console.log(`📝 [inputVariable] RECOVERED inputVariable="${userSession.inputVariable}" from node ${userSession.currNode} configuration (type: ${nodeType}, version: ${userSession.flowVersion || 1})`);
      // Save immediately to Redis
      await userSessions.set(sessionKey, userSession);
    }
  }

  // FIX: Log inputVariable state for debugging variable recording issues
  if (userSession.inputVariable) {
    console.log(`📝 [inputVariable] Session has inputVariable="${userSession.inputVariable}" for currNode=${userSession.currNode}`);
  } else {
    console.log(`📝 [inputVariable] Session has NO inputVariable, currNode=${userSession.currNode}`);
  }

  // ==================== USER-LEVEL LOCKING ====================
  // Acquire lock to prevent concurrent processing of messages from the same user
  // This prevents race conditions where multiple messages process the same node
  const maxLockWaitAttempts = 10;
  const lockWaitDelayMs = 500;
  let lockAcquired = false;

  for (let attempt = 0; attempt < maxLockWaitAttempts; attempt++) {
    lockAcquired = await acquireUserLock(sessionKey, 60000); // 60 second lock TTL
    if (lockAcquired) {
      console.log(`🔒 [LOCK] Acquired lock for ${userPhoneNumber} on attempt ${attempt + 1}`);
      break;
    }
    // Wait before retrying
    console.log(`⏳ [LOCK] Waiting for lock (attempt ${attempt + 1}/${maxLockWaitAttempts}) for ${userPhoneNumber}`);
    await new Promise(resolve => setTimeout(resolve, lockWaitDelayMs));
  }

  if (!lockAcquired) {
    console.warn(`⚠️ [LOCK] Could not acquire lock for ${userPhoneNumber} after ${maxLockWaitAttempts} attempts, proceeding anyway`);
  }
  // ==================== END USER-LEVEL LOCKING ====================

  // Extract trigger text for trigger handling
  const triggerText = message?.text?.body ||
    message?.interactive?.button_reply?.title ||
    message?.interactive?.list_reply?.title ||
    message?.button?.text;

  // ==================== MCP TOOL EVALUATION ====================
  // Speed-first approach: keyword matching, then intent matching, then LLM fallback
  // Only evaluate for text messages (not interactive button clicks, media, etc.)
  if (userSession.mcpToolsEnabled !== false && message_type === "text" && message_text) {
    try {
      const mcpResult = await evaluateMCPTools(
        userSession,
        message_text,
        [] // conversationHistory - can be enhanced later
      );

      if (mcpResult.toolExecuted && mcpResult.message) {
        console.log(`🔧 [MCP] Tool ${mcpResult.toolName} executed via ${mcpResult.triggerType}`);

        // Store result in session for potential use in flow
        userSession.mcpToolResult = mcpResult;

        // Send the tool's response message to the user
        const messageData = {
          type: 'text',
          text: {
            body: mcpResult.message
          }
        };

        await sendMessage(
          userSession.userPhoneNumber,
          userSession.business_phone_number_id,
          messageData,
          userSession.accessToken,
          userSession.tenant
        );

        // Save the MCP response as a conversation
        await saveMessage(
          userPhoneNumber,
          mcpResult.message,
          "bot",
          "text",
          business_phone_number_id,
          timestamp,
          userSession.tenant
        );

        // If the tool handled the request completely, stop processing
        // (User can continue their normal flow with subsequent messages)
        if (!mcpResult.error) {
          console.log(`✅ [MCP] Request handled by tool ${mcpResult.toolName}`);
          // Release lock before early return
          if (lockAcquired) {
            await releaseUserLock(sessionKey);
            console.log(`🔓 [LOCK] Released lock for ${userPhoneNumber} (MCP handled)`);
          }
          return;
        }
        // If there was an error, continue with normal flow processing
      }
    } catch (mcpError) {
      console.error('❌ [MCP] Error evaluating tools:', mcpError.message);
      // Continue with normal flow on MCP errors - don't block the user
    }
  }
  // ==================== END MCP TOOL EVALUATION ====================

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

    // Save incoming message (with wamid for deduplication — retries handled internally by saveMessage)
    try {
      await saveMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, formattedConversation, userSession.tenant, timestamp, 0, { messageId });
    } catch (saveError) {
      console.error(`❌ CRITICAL: Failed to save incoming message for ${userSession.userPhoneNumber}:`, saveError.message);
    }

    const notif_body = { content: `${userSession.userPhoneNumber} | New meessage from ${userSession.userName || userSession.userPhoneNumber}: ${message_text}`, created_on: timestamp };
    sendNotification(notif_body, userSession.tenant);

    ioEmissions(message, userSession, timestamp);
    updateLastSeen("replied", timestamp, userSession.userPhoneNumber, userSession.business_phone_number_id);

    if (userSession.type == "nothing") {
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }

    await sendReadAndTypingIndicator(message.id, business_phone_number_id, userSession.accessToken);

    const agents = userSession.agents;
    if (agents) {
      const isBusiness = agents.includes(userPhoneNumber);
      if (isBusiness) {
        if (lockAcquired) await releaseUserLock(sessionKey);
        return businessWebhook(req);
      }
    }

    if (userSession.type == "one2one") {
      if (lockAcquired) await releaseUserLock(sessionKey);
      return manualWebhook(req, userSession);
    }
    else if (userSession.type == 'person') {
      if (lockAcquired) await releaseUserLock(sessionKey);
      return personWebhook(req, userSession);
    }

    if (message_text == "/human") {
      userSession.type = "one2one";
      const key = userPhoneNumber + business_phone_number_id;
      await userSessions.set(key, userSession);
      if (lockAcquired) await releaseUserLock(sessionKey);
      return sendWelcomeMessage(userSession);
    }
    else if (message_text == '/person') {
      userSession.type = 'person';
      if (lockAcquired) await releaseUserLock(sessionKey);
      return personWebhook(req, userSession);
    }
    else if (message_text == '/language') {
      if (!userSession.doorbell) {
        if (lockAcquired) await releaseUserLock(sessionKey);
        return;
      }

      const key = String(userPhoneNumber) + String(business_phone_number_id);
      await userSessions.delete(key);
      userSession = await getSession(business_phone_number_id, contact);
      if (lockAcquired) await releaseUserLock(sessionKey);
      return sendLanguageSelectionMessage(userSession.doorbell, userSession.accessToken, userSession.userPhoneNumber, userSession.business_phone_number_id, userSession.tenant);
    }

    // Trigger handling - match trigger text to configured triggers (case-insensitive)
    if (triggerText && userSession.triggers && Object.keys(userSession.triggers).length > 0) {
      const normalizedInput = triggerText.trim().toLowerCase();
      const matchedTrigger = Object.keys(userSession.triggers).find(
        key => key.trim().toLowerCase() === normalizedInput
      );
      if (matchedTrigger) {
        const matchedFlowId = userSession.triggers[matchedTrigger];
        try {
          console.log("Trigger matched:", matchedTrigger, "id:", matchedFlowId);
          await triggerFlowById(userSession, matchedFlowId);
          if (lockAcquired) await releaseUserLock(sessionKey);
          return;
        } catch (error) {
          console.log("Error triggering matched flow:", error.message);
        }
      }
    }

    if (userSession.tenant == 'leqcjsk') {
      if (userSession?.isRRPEligible == undefined) userSession = await checkRRPEligibility(userSession);
      if (userSession?.isRRPEligible && message_type == "order") {
        if (lockAcquired) await releaseUserLock(sessionKey);
        return processOrderForDrishtee(userSession, products);
      }
    }

    if (userSession?.flowData && userSession?.flowData.length == 0) {
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }

    // Check if flow was already completed - only respond to restart button
    if (userSession.flowCompleted) {
      // Allow restart_flow button to work
      if (message_type === "interactive") {
        const userSelectionID = message?.interactive?.button_reply?.id || message?.interactive?.list_reply?.id;
        if (userSelectionID === "restart_flow") {
          console.log(`🔄 Restarting completed flow for ${userSession.userPhoneNumber}`);
          userSession.flowCompleted = false;
          userSession.currNode = userSession.flowVersion === 2 ? userSession.startNodeId : userSession.startNode;
          if (userSession.flowVersion === 2) {
            userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
          } else {
            userSession.nextNode = userSession.adjList[userSession.startNode];
          }
          userSession.inputVariable = null;
          await userSessions.set(sessionKey, userSession);
          await sendNodeMessage(userPhoneNumber, business_phone_number_id);

          if (lockAcquired) {
            await releaseUserLock(sessionKey);
          }
          return;
        }
      }

      // For any other message when flow is completed, remind them they can restart
      console.log(`📭 User sent message after flow completion, sending restart reminder`);
      const reminderMessage = {
        type: "interactive",
        interactive: {
          type: "button",
          body: { text: "The conversation has ended. Would you like to start over?" },
          action: {
            buttons: [
              {
                type: 'reply',
                reply: {
                  id: "restart_flow",
                  title: "Start Over"
                }
              }
            ]
          }
        }
      };
      await sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, reminderMessage, userSession.accessToken, userSession.tenant);

      if (lockAcquired) {
        await releaseUserLock(sessionKey);
      }
      return;
    }

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

          await userSessions.set(sessionKey, userSession);
          await sendNodeMessage(userPhoneNumber, business_phone_number_id);
        }
        else {
          sendLanguageSelectionMessage(doorbell, userSession.accessToken, userSession.userPhoneNumber, userSession.business_phone_number_id, userSession.tenant);
        }
      }
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }

    if (userSession.AIMode) {
      if (message_type == "interactive") {
        let userSelectionID = message?.interactive?.button_reply?.id || message?.interactive?.list_reply?.id;
        if (userSelectionID == "Exit AI") {
          userSession.AIMode = false;
          userSession.nextNode = userSession.adjList[userSession.currNode];
          // FIX: Check nextNode before accessing [0]
          if (userSession.nextNode && userSession.nextNode.length > 0) {
            userSession.currNode = userSession.nextNode[0];
            userSession.nextNode = userSession.adjList[userSession.currNode];
          }
          await userSessions.set(sessionKey, userSession);
          await sendNodeMessage(userPhoneNumber, business_phone_number_id);
        }
        else if (userSelectionID.startsWith("Hop")) {
          const node = Number(userSelectionID.split(":")[1]);
          userSession.AIMode = false;
          userSession.currNode = node;
          userSession.nextNode = userSession.adjList[userSession.currNode];
          await userSessions.set(sessionKey, userSession);
          await sendNodeMessage(userSession.userPhoneNumber, userSession.business_phone_number_id);
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
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }

    // FIX: For text messages, ensure inputVariable is set before handling input
    // This prevents the issue where text inputs don't get recorded because inputVariable is null
    if (message_type === "text" && !userSession.inputVariable) {
      let currNodeData, nodeType;

      // Handle both legacy and V2 flow structures
      if (userSession.flowVersion === 2) {
        currNodeData = userSession.nodes?.find(n => n.id === userSession.currNode)?.data;
        nodeType = userSession.nodes?.find(n => n.id === userSession.currNode)?.type;
      } else {
        currNodeData = userSession.flowData?.[userSession.currNode];
        nodeType = currNodeData?.type;
      }

      // If current node is a Text/Button/List/askQuestion node with a variable, set it now
      const inputNodeTypes = ['Text', 'Button', 'List', 'askQuestion'];
      if (inputNodeTypes.includes(nodeType) && currNodeData?.variable) {
        userSession.inputVariable = currNodeData.variable;
        userSession.inputVariableType = currNodeData.dataType || 'text';
        console.log(`🔧 [FIX] Recovered missing inputVariable="${currNodeData.variable}" from node ${userSession.currNode} (type: ${nodeType})`);
      }
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
        await userSessions.set(sessionKey, userSession);
        await sendNodeMessage(userPhoneNumber, business_phone_number_id);
        if (lockAcquired) await releaseUserLock(sessionKey);
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
          userSession.flowCompleted = false;
          const sessionKey = userSession.userPhoneNumber + userSession.business_phone_number_id;
          await userSessions.set(sessionKey, userSession);
          await sendNodeMessage(userPhoneNumber, business_phone_number_id);
          if (lockAcquired) await releaseUserLock(sessionKey);
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
            // CRITICAL FIX: Mark that node was advanced so session gets saved before sendNodeMessage
            userSession.nodeAdvanced = true;
          } else {
            console.warn(`No matching edge found for selection ${userSelectionID}`);
            await executeFallback(userSession);
            if (lockAcquired) await releaseUserLock(sessionKey);
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
                  userSession.nextNode = userSession.adjList[userSession.currNode] || [];
                  console.log(`🔧 Auto-advanced from ${nodeType} ${oldNode} to target ${userSession.currNode}`);
                } else {
                  console.error(`⚠️ ${nodeType} node ${oldNode} has no nextNode!`);
                }
              }

              break;
            }
          }

          // Second: global search in flowData (only if flowData is array)
          if (!found && Array.isArray(userSession.flowData)) {
            for (let i = 0; i < userSession.flowData.length; i++) {
              if (userSession.flowData[i].id == userSelectionID) {
                // FIX: Single advance only
                userSession.currNode = i;
                userSession.nextNode = userSession.adjList[userSession.currNode] || [];
                // REMOVED: userSession.currNode = userSession.nextNode[0];  <-- DOUBLE-ADVANCE BUG FIXED

                // Handle input variable from parent
                for (let j = 0; j < userSession.flowData.length; j++) {
                  if (userSession.adjList[j] && userSession.adjList[j].includes(i)) {
                    var variable = userSession.flowData[j].variable;
                    if (variable) {
                      userSession.inputVariable = variable;
                      handleInput(userSession, message_text);
                    }
                  }
                }
                found = true;
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
              userSession.nextNode = userSession.adjList[userSession.currNode] || [];
              console.log(`🔧 Auto-advanced from button_element ${oldNode} to actual target ${userSession.currNode}`);
            } else {
              console.error(`⚠️ button_element node ${oldNode} has no nextNode!`);
            }
          }

          // CRITICAL FIX: Mark that node was advanced so session gets saved before sendNodeMessage
          // Without this, sendNodeMessage reads the old currNode from Redis
          userSession.nodeAdvanced = true;
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

        console.log(`🔍 [V2] Processing currNode=${userSession.currNode}, nodeType="${nodeType || 'UNDEFINED'}"`);

        // CRITICAL: Check if node was found
        if (!currNodeObj) {
          console.error(`❌ [V2 ERROR] Node ${userSession.currNode} NOT FOUND in nodes array!`);
          console.error(`❌ Available nodes:`, userSession.nodes?.map(n => n.id).join(', '));
          // Don't proceed with invalid node - let sendNodeMessage handle it
        } else {
          // CRITICAL FIX: Removed (currNode != startNode) condition that was preventing
          // first askQuestion nodes from being handled. ALL nodes should be processed,
          // regardless of whether they're the start node or not.

          if (['sendMessage', 'ai', 'api', 'template', 'customint', 'flowjson'].includes(nodeType)) {
          // Auto-advance for message nodes that don't wait for user input
          const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
          if (nextNodes.length > 0) {
            userSession.currNode = nextNodes[0];
          }
        }
        else if (['askQuestion'].includes(nodeType)) {
            // Accept text input for ANY askQuestion node, regardless of optionType or dataType
            // This allows users to respond with text even when audio/buttons/lists are expected
            const data = currNodeObj?.data || {};
            const oldNode = userSession.currNode;
            const variable = data.variable;

            console.log(`📝 [V2 askQuestion] Received text input for node ${oldNode} with optionType="${data.optionType}", dataType="${data.dataType}"`);

            // CRITICAL FIX: Save the text response to the variable BEFORE advancing
            // Without this, the bot doesn't store the user's response and may repeat the question
            if (variable && message_text) {
              userSession[variable] = message_text;
              console.log(`✅ [V2 askQuestion] Saved text response "${message_text.substring(0, 50)}..." to variable "${variable}"`);
            } else if (variable) {
              console.log(`⚠️ [V2 askQuestion] Variable "${variable}" defined but no message_text to save`);
            }

            // Always advance when text is received for askQuestion nodes
            const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
            console.log(`🔍 [DEBUG] Found ${nextNodes.length} next nodes from ${oldNode}: [${nextNodes.join(', ')}]`);
            if (nextNodes.length > 0) {
              userSession.currNode = nextNodes[0];
              userSession.nodeAdvanced = true; // Flag that we advanced the node
              console.log(`✅ [V2 askQuestion] Advanced from ${oldNode} to ${userSession.currNode} after text input`);
              console.log(`🔍 [DEBUG] nodeAdvanced flag SET, session will be saved before sendNodeMessage`);
            } else {
              // V2 terminal node - flow is complete
              console.log(`🏁 [V2 FLOW COMPLETE] User at terminal node ${userSession.currNode}, automation has ended`);

              const completionMessage = userSession.fallback_msg || "Thank you! The conversation has ended.";
              const messageData = {
                type: "interactive",
                interactive: {
                  type: "button",
                  body: { text: completionMessage + "\n\nWould you like to start over?" },
                  action: {
                    buttons: [
                      {
                        type: 'reply',
                        reply: {
                          id: "restart_flow",
                          title: "Start Over"
                        }
                      }
                    ]
                  }
                }
              };

              await sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, messageData, userSession.accessToken, userSession.tenant);
              userSession.flowCompleted = true;
              await userSessions.set(sessionKey, userSession);

              if (lockAcquired) {
                await releaseUserLock(sessionKey);
              }
              return;
            }
        }
        else {
          // FALLBACK: Unknown node type or no handler matched
          // Use the SAME logic as audio - check if we have nextNode pre-computed by snm.js
          console.log(`⚠️ [V2 FALLBACK] Unhandled node type "${nodeType}" at currNode=${userSession.currNode}`);

          // CRITICAL: Use nextNode array (like audio does) instead of checking inputVariable
          // snm.js already computed the next node when it sent the question
          if (userSession.nextNode && userSession.nextNode.length > 0) {
            const oldNode = userSession.currNode;
            console.log(`📝 [V2 FALLBACK] Using pre-computed nextNode array: [${userSession.nextNode.join(', ')}]`);
            userSession.currNode = userSession.nextNode[0];
            userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
            userSession.nodeAdvanced = true;
            console.log(`✅ [V2 FALLBACK] Advanced from ${oldNode} to ${userSession.currNode} (same as audio logic)`);
          } else if (userSession.inputVariable) {
            // Secondary fallback: if nextNode not set but inputVariable is, try edges
            console.log(`📝 [V2 FALLBACK] No nextNode array, but inputVariable="${userSession.inputVariable}" is set`);
            const nextNodes = findNextNodesFromEdges(userSession.edges, userSession.currNode);
            console.log(`🔍 [V2 FALLBACK] Found ${nextNodes.length} next nodes from edges: [${nextNodes.join(', ')}]`);

            if (nextNodes.length > 0) {
              const oldNode = userSession.currNode;
              userSession.currNode = nextNodes[0];
              userSession.nodeAdvanced = true;
              console.log(`✅ [V2 FALLBACK] Advanced from ${oldNode} to ${userSession.currNode}`);
            } else {
              console.log(`⚠️ [V2 FALLBACK] No next nodes found, staying at currNode=${userSession.currNode}`);
            }
          } else {
            console.log(`⚠️ [V2 FALLBACK] No nextNode array and no inputVariable, will let sendNodeMessage handle it`);
          }
        }
        } // End of currNodeObj check
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

          // Auto-advance through button/list elements - FIX: null check
          if (userSession.nextNode && userSession.nextNode.length > 0) {
            userSession.currNode = userSession.nextNode[0];
            userSession.nextNode = userSession.adjList[userSession.currNode] || [];
            console.log(`Auto-advanced from ${oldNode} to ${userSession.currNode}`);
          } else {
            console.error(`⚠️ ${type} node ${oldNode} has no nextNode, cannot auto-advance!`);
          }
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

          // Check if this is the last node (no next nodes)
          if (!userSession.nextNode || userSession.nextNode.length === 0) {
            console.log(`🏁 [FLOW COMPLETE] User at terminal node ${oldNode}, automation has ended`);

            // Send completion message with restart option
            const completionMessage = userSession.fallback_msg || "Thank you! The conversation has ended.";
            const messageData = {
              type: "interactive",
              interactive: {
                type: "button",
                body: { text: completionMessage + "\n\nWould you like to start over?" },
                action: {
                  buttons: [
                    {
                      type: 'reply',
                      reply: {
                        id: "restart_flow",
                        title: "Start Over"
                      }
                    }
                  ]
                }
              }
            };

            await sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, messageData, userSession.accessToken, userSession.tenant);

            // Mark the flow as completed (set currNode to a special marker)
            userSession.flowCompleted = true;
            await userSessions.set(sessionKey, userSession);

            // Release lock before returning
            if (lockAcquired) {
              await releaseUserLock(sessionKey);
              console.log(`🔓 [LOCK] Released lock for ${userPhoneNumber} (flow completed)`);
            }
            return;
          }

          // Advance to next node - FIX: Already checked nextNode.length above, but double-check
          if (userSession.nextNode && userSession.nextNode.length > 0) {
            userSession.currNode = userSession.nextNode[0];
            // CRITICAL: Update nextNode using adjacency list
            userSession.nextNode = userSession.adjList[userSession.currNode] || [];

            console.log(`After advancement: currNode=${userSession.currNode}, nextNode=${userSession.nextNode}`);
            console.log(`Advanced from ${oldNode} to ${userSession.currNode} after text input`);
          } else {
            console.error(`⚠️ Cannot advance - nextNode is empty at node ${oldNode}`);
          }

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
          if (lockAcquired) await releaseUserLock(sessionKey);
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
        if (userSession.nextNode && userSession.nextNode.length > 0) {
          const oldNode = userSession.currNode;
          userSession.currNode = userSession.nextNode[0];
          userSession.nextNode = userSession.adjList[userSession.currNode] || [];
          userSession.nodeAdvanced = true; // Flag that we advanced the node
          console.log(`Audio message: Advanced from ${oldNode} to ${userSession.currNode}`);
        } else {
          console.log(`Audio message: No next node to advance to from ${userSession.currNode}`);
        }
      } else {
        // V2 mode handling
        if (userSession.nextNode && userSession.nextNode.length > 0) {
          userSession.currNode = userSession.nextNode[0];
          userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
          userSession.nodeAdvanced = true; // Flag that we advanced the node
        }
      }
    }
    else if (message_type == "document") {
      // LEGACY MODE: Advance for document messages
      if (userSession.flowVersion !== 2) {
        if (userSession.nextNode && userSession.nextNode.length > 0) {
          const oldNode = userSession.currNode;
          userSession.currNode = userSession.nextNode[0];
          userSession.nextNode = userSession.adjList[userSession.currNode] || [];
          userSession.nodeAdvanced = true; // Flag that we advanced the node
          console.log(`Document message: Advanced from ${oldNode} to ${userSession.currNode}`);
        } else {
          console.log(`Document message: No next node to advance to from ${userSession.currNode}`);
        }
      } else {
        // V2 mode handling
        if (userSession.nextNode && userSession.nextNode.length > 0) {
          userSession.currNode = userSession.nextNode[0];
          userSession.nextNode = findNextNodesFromEdges(userSession.edges, userSession.currNode);
          userSession.nodeAdvanced = true; // Flag that we advanced the node
        }
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
      if (lockAcquired) await releaseUserLock(sessionKey);
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
        if (lockAcquired) await releaseUserLock(sessionKey);
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
        if (lockAcquired) await releaseUserLock(sessionKey);
        return;
      }
      // FIX: null check for nextNode
      if (userSession.nextNode && userSession.nextNode.length > 0) {
        userSession.currNode = userSession.nextNode[0];
        userSession.nextNode = userSession.adjList?.[userSession.currNode] || [];
      }
    }
    else if (message_type == "reaction") {
      // Reactions are already saved to conversation, no flow progression needed
      console.log(`Reaction ${message?.reaction?.emoji} saved to conversation`);
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }
    else if (message_type == "sticker") {
      // Stickers are already saved to conversation, no flow progression needed
      console.log("Sticker saved to conversation");
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }
    else if (message_type == "contacts") {
      // Contact shares are already saved to conversation
      console.log("Contact shared saved to conversation");
      if (lockAcquired) await releaseUserLock(sessionKey);
      return;
    }

    // NOTE: We intentionally do NOT save the session before sendNodeMessage anymore.
    // Saving here was overwriting the inputVariable that snm.js set in the previous request.
    // snm.js handles all session state management including inputVariable.
    // The currNode advancement for audio/document messages is passed via the session object
    // that snm.js reads directly.

    // Pass the advanced currNode to snm.js by saving ONLY if node was advanced
    // This ensures snm.js starts from the correct node for audio/document messages
    if (userSession.nodeAdvanced) {
      console.log(`🔍 [DEBUG] nodeAdvanced is TRUE, saving session before sendNodeMessage`);
      console.log(`🔍 [DEBUG] About to save: currNode=${userSession.currNode}, inputVariable="${userSession.inputVariable || 'null'}"`);

      // CRITICAL FIX: Clear inputVariable when node advances
      // The NEW node will set its own inputVariable via snm.js
      // Preserving the old inputVariable causes confusion between questions
      userSession.inputVariable = null;
      console.log(`🔍 [DEBUG] Cleared inputVariable - new node will set its own`);

      await userSessions.set(sessionKey, userSession);
      console.log(`✅ [SAVE] Session saved with advanced node: currNode=${userSession.currNode}`);
      console.log(`🔍 [DEBUG] Session save completed, now calling sendNodeMessage`);
      userSession.nodeAdvanced = false; // Reset flag
    } else {
      console.log(`⚠️ [DEBUG] nodeAdvanced is FALSE, session will NOT be saved before sendNodeMessage`);
    }

    console.log(`🔍 [DEBUG] Calling sendNodeMessage with currNode=${userSession.currNode}`);
    await sendNodeMessage(userPhoneNumber, business_phone_number_id);
    console.log("Webhook processing completed successfully");
  } catch (error) {
    console.error("Error in webhook processing:", error);
  } finally {
    // ==================== RELEASE USER LOCK ====================
    // NOTE: We do NOT save the session here anymore!
    // sendNodeMessage() already saves the correctly advanced session state.
    // Saving here would overwrite the advanced currNode with the old value,
    // causing nodes to repeat (the bug we fixed).
    if (lockAcquired) {
      await releaseUserLock(sessionKey);
      console.log(`🔓 [LOCK] Released lock for ${userPhoneNumber}`);
    }
    // ==================== END RELEASE USER LOCK ====================
  }
}
async function assignAgent(agentList) {
  for (let agent of agentList) {
    if (await isAgent(agent)) continue
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
    const userPhoneNumber = userSession.userPhoneNumber;
    const headers = { 'X-Tenant-Id': userSession.tenant };

    let response;

    if (userSession.agentModeEnabled) {
      // ---- AI Agent Mode ----
      // Fetch recent conversation history
      let conversationHistory = [];
      try {
        const convoResp = await axios.get(
          `${djangoURL}/whatsapp_convo_get/${userPhoneNumber}/`,
          { headers, timeout: 5000 }
        );
        const messages = convoResp.data?.data || convoResp.data || [];
        // Convert to {text, sender} format, take last 20
        conversationHistory = (Array.isArray(messages) ? messages : [])
          .slice(-20)
          .map(m => ({
            text: m.message_text || m.body || m.text || "",
            sender: (m.direction === "outbound" || m.sender === "bot") ? "bot" : "user"
          }));
      } catch (convoErr) {
        console.log("[Agent] Could not fetch conversation history:", convoErr.message);
      }

      const agentData = {
        query: query,
        phone: userPhoneNumber,
        nodes: nodes,
        language: language,
        use_tools: true,
        conversation_history: conversationHistory,
        agent_system_prompt: userSession.agentSystemPrompt || ""
      };

      response = await axios.post(
        `${djangoURL}/agent-query/`,
        agentData,
        { headers, timeout: 30000 }
      );
      console.log("[Agent] response:", response.data);

      // Log tool executions
      if (response.data.tool_executions && response.data.tool_executions.length > 0) {
        response.data.tool_executions.forEach(te => {
          console.log(`[Agent] Tool: ${te.tool_name}, success: ${te.success}, duration: ${te.duration_ms}ms`);
        });
      }
    } else {
      // ---- Legacy Mode (keyword-based) ----
      const prompt = userSession.AIModePrompt || "You are a helpful assistant. Reply to the point. Dont include any apologies or explanations in your replies. IMPORTANT: Your entire response must be 1000 characters or less due to WhatsApp message limitations."
      const useMCPTools = userSession.mcpToolsInAIMode !== false;
      const endpoint = useMCPTools ? '/query-faiss-with-tools/' : '/query-faiss/';

      const data = {
        query: query,
        nodes: nodes,
        language: language,
        prompt: prompt,
        phone: userPhoneNumber,
        use_tools: useMCPTools
      };

      response = await axios.post(`${djangoURL}${endpoint}`, data, { headers });
      console.log("openai response:", response.data);

      if (response.data.tool_execution) {
        console.log("MCP Tool executed:", response.data.tool_execution.tool_name);
        console.log("Tool success:", response.data.tool_execution.tool_success);
      }
    }

    // ---- Common: send response to user ----
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
      if (index !== -1) {
        const action = nodes[index].action;
        const hopMessageData = {
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
        sendMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, hopMessageData, userSession.accessToken, userSession.tenant)
      }
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
