import express from 'express';
import axios from 'axios';
import pLimit from 'p-limit';

import { getSession, saveMessage, updateLastSeen } from '../helpers/misc.js';
import { convertToValidDateFormat, delay, getIndianCurrentTime, isRequestSignatureValid } from '../utils.js';
import { userWebhook } from '../mainwebhook/userWebhook.js';
import { campaignWebhook } from '../webhooks/campaignWebhook.js';
import { readData } from '../queues/worker.js';
import { djangoURL, fastURL } from '../mainwebhook/snm.js';
import { io, messageCache, userSessions } from '../server.js';
import { delTemplateName, getTemplateName } from '../queues/workerQueues.js';
import { sendMessage } from '../send-message.js';
import { normalizePhone } from '../normalize.js';
import { trackMessageStatus, trackMessageReply, trackButtonClick } from '../analytics/tracker.js';
import { handleHjiqoheMessage, isInHjiqoheFlow } from '../handlers/hjiqoheHandler.js';
const router = express.Router();

// Throttle status webhook Django calls to prevent starving login/interactive requests
const statusDjangoLimit = pLimit(3);
function throttledStatsPost(url, data, headers) {
  statusDjangoLimit(() =>
    axios.post(url, data, { headers, timeout: 10000 })
  ).catch(err => console.warn(`⚠️ [Status Django] stats post failed: ${err.message}`));
}
const WEBHOOK_VERIFY_TOKEN = "COOL";

// ==================== MULTI MEDIA BATCH DETECTION (MOVED FROM userWebhook.js) ====================
// ==================== MULTI MEDIA BATCH DETECTION ====================
const mediaCollectionMap = new Map();

const MEDIA_CONFIG = {
  DETECTION_WINDOW: 5000,           // Wait 5s for additional files
  SINGLE_FILE_TIMEOUT: 2500,        // Fast process single files after 2.5s
  BATCH_PROCESSING_DELAY: 5000,     // Process batch after 5s of last file
  MAX_FILES: 10,
  CLEANUP_AFTER: 8000
};

function collectMedia(userKey, mediaId, messageType, userSession) {
  const now = Date.now();
  
  if (mediaCollectionMap.has(userKey)) {
    const collection = mediaCollectionMap.get(userKey);
    
    if (collection.processed || collection.isProcessing) {
      console.log(`⚠️ [BATCH] Collection already processed/processing, not adding: ${mediaId}`);
      return { collected: false, isFirstFile: false, count: 0, alreadyProcessed: true };
    }
    
    const timeSinceLastUpload = now - collection.lastUploadTime;
    
    if (timeSinceLastUpload < MEDIA_CONFIG.DETECTION_WINDOW) {
      collection.mediaIds.push(mediaId);
      collection.types.push(messageType);
      collection.lastUploadTime = now;
      
      const newCount = collection.mediaIds.length;
      console.log(`📦 [BATCH] Added to collection (${newCount} files): ${mediaId}`);
      
      // Clear single file timeout since we have multiple files
      if (collection.singleFileTimeout) {
        clearTimeout(collection.singleFileTimeout);
        collection.singleFileTimeout = null;
      }
      
      // 🚀 CRITICAL FIX: Only schedule batch timeout if this is the 2nd file
      // Don't reset it for subsequent files
      if (newCount === 2) {
        console.log(`📦 [BATCH] Multiple files detected (${newCount}), scheduling batch processing`);
        scheduleBatchProcessing(userKey);
      }
      // For files 3+, just extend the collection but don't reset the timeout
      else if (newCount > 2) {
        console.log(`📦 [BATCH] Extended collection to ${newCount} files, keeping existing batch schedule`);
      }
      
      return { collected: true, isFirstFile: false, count: newCount };
    } else {
      // Time window expired - process existing and start new
      console.log(`⏱️ [BATCH] Time window expired (${timeSinceLastUpload}ms), processing existing collection`);
      processMediaBatch(userKey);
      
      // Start new collection
      mediaCollectionMap.set(userKey, {
        mediaIds: [mediaId],
        types: [messageType],
        startTime: now,
        lastUploadTime: now,
        userSession: userSession,
        batchTimeout: null,
        singleFileTimeout: null,
        processed: false,
        isProcessing: false,
        skipNodeMessage: true
      });
      
      console.log(`📦 [BATCH] Started new collection for ${userKey}: ${mediaId}`);
      scheduleSingleFileTimeout(userKey);
      return { collected: true, isFirstFile: true, count: 1 };
    }
  } else {
    // First file - create new collection
    mediaCollectionMap.set(userKey, {
      mediaIds: [mediaId],
      types: [messageType],
      startTime: now,
      lastUploadTime: now,
      userSession: userSession,
      batchTimeout: null,
      singleFileTimeout: null,
      processed: false,
      isProcessing: false,
      skipNodeMessage: true
    });
    
    console.log(`📦 [BATCH] Started collection for ${userKey}: ${mediaId} (waiting for more files)`);
    scheduleSingleFileTimeout(userKey);
    
    return { collected: true, isFirstFile: true, count: 1 };
  }
}

function scheduleBatchProcessing(userKey) {
  const collection = mediaCollectionMap.get(userKey);
  if (!collection) return;
  
  // 🔥 Clear any existing single file timeout
  if (collection.singleFileTimeout) {
    clearTimeout(collection.singleFileTimeout);
    collection.singleFileTimeout = null;
  }
  
  if (collection.batchTimeout) {
    clearTimeout(collection.batchTimeout);
  }
  
  const fileCount = collection.mediaIds.length;
  console.log(`⏱️ [BATCH] Batch timer scheduled for ${fileCount} files - will process in ${MEDIA_CONFIG.BATCH_PROCESSING_DELAY}ms`);
  
  collection.batchTimeout = setTimeout(() => {
    processMediaBatch(userKey);
  }, MEDIA_CONFIG.BATCH_PROCESSING_DELAY);  // 🔥 CHANGED: Use longer delay for batches
}
function scheduleSingleFileTimeout(userKey) {
  const collection = mediaCollectionMap.get(userKey);
  if (!collection) return;
  
  collection.singleFileTimeout = setTimeout(async () => {
    const currentCollection = mediaCollectionMap.get(userKey);
    if (currentCollection && 
        !currentCollection.processed && 
        !currentCollection.isProcessing &&
        currentCollection.mediaIds.length === 1) {
      
      console.log(`⏰ [SINGLE] Fast-track timeout - only 1 file received, processing immediately`);
      
      // 🔥 CRITICAL: Clear the batch timeout first
      if (currentCollection.batchTimeout) {
        clearTimeout(currentCollection.batchTimeout);
        currentCollection.batchTimeout = null;
      }
      
      await processMediaBatch(userKey);
    }
  }, MEDIA_CONFIG.SINGLE_FILE_TIMEOUT);  // 🔥 CHANGED: Use dedicated single file timeout (2.5s)
}
async function processMediaBatch(userKey) {
  const collection = mediaCollectionMap.get(userKey);
  
  if (!collection || collection.processed || collection.isProcessing) {
    console.log(`⚠️ [BATCH] No collection or already processed/processing for ${userKey}`);
    return;
  }
  
  collection.isProcessing = true;
  
  // Clear all timeouts
  if (collection.singleFileTimeout) {
    clearTimeout(collection.singleFileTimeout);
  }
  if (collection.batchTimeout) {
    clearTimeout(collection.batchTimeout);
  }
  
  const totalFiles = collection.mediaIds.length;
  const userSession = collection.userSession;
  
  console.log(`🚀 [BATCH] Processing ${totalFiles} file(s) for ${userKey}`);
  
  try {
    const sessionKey = userSession.userPhoneNumber + userSession.business_phone_number_id;
    const currentSession = await userSessions.get(sessionKey);
    
    if (!currentSession) {
      console.error('❌ [BATCH] Session lost during processing');
      return;
    }
    
    if (totalFiles === 1) {
      console.log(`📄 [SINGLE] Only 1 file - releasing to normal userWebhook flow`);

      // Mark as processed BEFORE creating mock request
      collection.processed = true;

      // 🔍 DEBUG: Log session state before processing
      if (currentSession.tenant === 'hjiqohe') {
        console.log(`🔍 [BATCH-DEBUG] Session state before userWebhook:`);
        console.log(`   inputVariable: ${currentSession.inputVariable}`);
        console.log(`   currNode: ${currentSession.currNode}`);
        console.log(`   nextNode: ${JSON.stringify(currentSession.nextNode)}`);
        console.log(`   isProcessing: ${currentSession.isProcessing}`);
        console.log(`   flowData node: ${JSON.stringify(currentSession.flowData?.[currentSession.currNode])}`);
      }

      // 🔧 CRITICAL FIX: Reset isProcessing lock before calling userWebhook
      // The HelloZestay fast path may have left this flag set, blocking batch-released images
      if (currentSession.tenant === 'hjiqohe' && currentSession.isProcessing) {
        console.log(`🔓 [BATCH] Clearing stale isProcessing lock for hjiqohe tenant`);
        currentSession.isProcessing = false;
        await userSessions.set(sessionKey, currentSession);
      }

      // Create mock request to pass to userWebhook
      const mockReq = {
        body: {
          entry: [{
            changes: [{
              value: {
                metadata: {
                  phone_number_id: userSession.business_phone_number_id
                },
                contacts: [{
                  wa_id: userSession.userPhoneNumber,
                  profile: { name: userSession.userName }
                }],
                messages: [{
                  type: collection.types[0],
                  id: 'batch_released_' + Date.now(),
                  timestamp: Math.floor(Date.now() / 1000),
                  [collection.types[0]]: {
                    id: collection.mediaIds[0]
                  }
                }]
              }
            }]
          }]
        }
      };
      
      // Clean up immediately since we're processing now
      mediaCollectionMap.delete(userKey);
      console.log(`🧹 [BATCH] Cleaned up single-file collection for ${userKey}`);
      
      // Import and call userWebhook from the correct path
      const { userWebhook } = await import('../mainwebhook/userWebhook.js');
      await userWebhook(mockReq);
      
      console.log(`✅ [SINGLE] File released and processed successfully`);
      return;
    }
    
    // Multiple files - send to bulk endpoint
    if (totalFiles >= 2) {
      console.log(`📦 [BULK] ${totalFiles} files detected - sending to bulk endpoint & jumping to node 1`);

      // 🔧 CRITICAL FIX: Reset isProcessing lock before continuing flow
      // Prevents subsequent messages from being blocked
      if (currentSession.tenant === 'hjiqohe' && currentSession.isProcessing) {
        console.log(`🔓 [BULK] Clearing stale isProcessing lock for hjiqohe tenant (multi-file)`);
        currentSession.isProcessing = false;
        await userSessions.set(sessionKey, currentSession);
      }

      const mediaData = collection.mediaIds.map((id, index) => ({
        mediaId: id,
        type: collection.types[index],
        sequence: index + 1
      }));
      
      try {
        console.log(`📤 [BULK] Sending ${totalFiles} files to bulk API`);
        const response = await axios.post(
          'https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/process-multiple-media',
          {
            userPhone: userSession.userPhoneNumber,
            businessPhoneId: userSession.business_phone_number_id,
            flowName: userSession.flowName,
            inputVariable: userSession.inputVariable,
            totalFiles: totalFiles,
            mediaFiles: mediaData,
            timestamp: await getIndianCurrentTime()
          },
          {
            headers: { 
              'X-Tenant-Id': userSession.tenant,
              'Authorization': `Bearer ${userSession.accessToken}`,
              'Content-Type': 'application/json'
            },
            timeout: 30000
          }
        );
        
        console.log(`✅ [BULK] API Success:`, response.status, response.data);
        
        currentSession.inputVariable = null;
        
        const targetNodeIndex = currentSession.flowData.findIndex(node => node.id === 1);
        
        if (targetNodeIndex === -1) {
          console.error('❌ [BULK] Node with id 1 not found in flowData');
          
          const fallbackNodeIndex = currentSession.flowData.findIndex(node => 
            node.type === 'Button' || (node.body && node.body.includes('Got it'))
          );
          
          if (fallbackNodeIndex !== -1) {
            console.warn(`⚠️ [BULK] Using fallback button node at index ${fallbackNodeIndex}`);
            currentSession.currNode = fallbackNodeIndex;
            currentSession.nextNode = currentSession.adjList[fallbackNodeIndex];
          } else {
            console.error('❌ [BULK] No suitable fallback node found');
            throw new Error('Target node with id 1 not found and no fallback available');
          }
        } else {
          currentSession.currNode = targetNodeIndex;
          currentSession.nextNode = currentSession.adjList[targetNodeIndex];
        }
        
        await userSessions.set(sessionKey, currentSession);
        
        console.log(`🎯 [BULK] Jumped to node with id:1 (array index: ${targetNodeIndex})`);
        
        const { sendNodeMessage } = await import('../mainwebhook/snm.js');
        console.log("testingggggggggg");
        await sendNodeMessage(
          currentSession.userPhoneNumber, 
          currentSession.business_phone_number_id
        );
        
        console.log(`✅ [BULK] Flow continued successfully from node 1`);
        
      } catch (error) {
        console.error(`❌ [BULK] API Error:`, error.response?.data || error.message);
        
        const errorMsg = {
          type: "text",
          text: {
            body: "⚠️ There was an error processing your documents. Please try uploading them again one by one."
          }
        };
        
        await sendMessage(
          userSession.userPhoneNumber,
          userSession.business_phone_number_id,
          errorMsg,
          userSession.accessToken,
          userSession.tenant
        );
        
        currentSession.inputVariable = userSession.inputVariable;
        await userSessions.set(sessionKey, currentSession);
      }
    }
    
  } catch (error) {
    console.error(`❌ [BATCH] Unexpected error:`, error);
  } finally {
    if (!collection.processed) {
      collection.processed = true;
    }
    collection.isProcessing = false;
    
    // Clean up after delay
    setTimeout(() => {
      if (mediaCollectionMap.has(userKey)) {
        mediaCollectionMap.delete(userKey);
        console.log(`🧹 [BATCH] Delayed cleanup for ${userKey}`);
      }
    }, MEDIA_CONFIG.CLEANUP_AFTER);
  }
}

function isInBatchCollection(userKey) {
  const collection = mediaCollectionMap.get(userKey);
  if (!collection) return false;
  // Only block if collection is being processed, not just because it has 2+ files
  return collection.isProcessing;  // ✅ CORRECT
}

function getCollectionCount(userKey) {
  const collection = mediaCollectionMap.get(userKey);
  return collection ? collection.mediaIds.length : 0;
}

function wasMediaCollected(userKey, mediaId) {
  const collection = mediaCollectionMap.get(userKey);
  if (!collection) return false;
  return collection.mediaIds.includes(mediaId);
}

// 🔥 NEW: Export function to check if we should skip node message
export function shouldSkipNodeMessage(userKey) {
  const collection = mediaCollectionMap.get(userKey);
  if (!collection) return false;
  return collection.skipNodeMessage === true && !collection.processed && !collection.isProcessing;
}

// ==================== WEBHOOK HANDLER ====================
router.post("/webhook", async (req, res) => {
  // TEMPORARILY SIMPLIFIED LOGGING FOR HJIQOHE DEBUGGING
  const message = req.body.entry?.[0]?.changes[0]?.value?.messages?.[0];
  const contact = req.body.entry?.[0]?.changes[0]?.value?.contacts?.[0];
  const statuses = req.body.entry?.[0]?.changes[0]?.value?.statuses?.[0];

  // Only log if it's a message (not status updates)
  if (message) {
    console.log(`\n========== WEBHOOK: ${message.type} from ${contact?.wa_id} ==========`);
  }

  try {
    res.sendStatus(200);

    const business_phone_number_id = req.body.entry?.[0].changes?.[0].value?.metadata?.phone_number_id;
    const smb = req.body.entry?.[0]?.changes[0]?.value?.message_echoes?.[0];
    // message, contact, statuses already extracted above

    // ==================== HJIQOHE HANDLER ====================
    // Handles:
    // 1. HelloZestay command - Redis guest check + welcome + trigger flow 209
    // 2. Bulk media uploads - Collects images/docs and sends to process-multiple-media endpoint
    if (message) {
      const messageType = message?.type;
      const messageText = message?.text?.body || '';
      const isHelloZestay = messageText.toLowerCase().startsWith('hellozestay');
      const isMedia = ['image', 'document'].includes(messageType);

      if (isHelloZestay || isMedia) {
        const tempSessionForHjiqohe = await getSession(business_phone_number_id, contact);

        if (tempSessionForHjiqohe.tenant === 'hjiqohe') {
          console.log(`[hjiqohe-route] ${isHelloZestay ? 'HelloZestay' : 'Media upload'} detected - routing to handler`);

          try {
            const handled = await handleHjiqoheMessage(tempSessionForHjiqohe, message, req);
            if (handled) {
              console.log(`[hjiqohe-route] Message handled successfully by hjiqohe handler`);
              return; // Exit - handled by hjiqohe handler
            }
          } catch (err) {
            console.error(`[hjiqohe-route] Handler error:`, err.message);
            // Fall through to normal flow on error
          }
        }
      }
    }

    // ==================== EARLY MEDIA BATCH DETECTION ====================
    if (message) {
      const userPhoneNumber = normalizePhone(contact?.wa_id);

      const message_type = message?.type;
      const isMediaMessage = ['image', 'document', 'video'].includes(message_type);
      const mediaId = message?.image?.id || message?.document?.id || message?.video?.id;
      const userKey = `${userPhoneNumber}:${business_phone_number_id}`;
   // Note: hjiqohe unsupported/text message handling is now done by the dedicated handler above

      // CHECK: Is there already a collection in progress?
      if (isInBatchCollection(userKey)) {
        const count = getCollectionCount(userKey);
        console.log(`⏸️ [BATCH] BLOCKING webhook - batch collection in progress (${count} file(s))`);
        
        const timestamp = await getIndianCurrentTime();
        await updateLastSeen("replied", timestamp, userPhoneNumber, business_phone_number_id);
        
        return; // EXIT - Don't pass to userWebhook
      }

      // CHECK: Was this media already processed in a batch?
      if (isMediaMessage && mediaId && wasMediaCollected(userKey, mediaId)) {
        console.log(`✅ [BATCH] Media ${mediaId} already in batch - ignoring duplicate`);
        return; // EXIT
      }

      // Note: hjiqohe media batch collection is now handled by the dedicated handler above
      // This section is kept for other tenants that may need batch collection in the future

      // Continue to userWebhook if not blocked
      return userWebhook(req);
    }

    // ==================== HANDLE NON-MESSAGE WEBHOOKS ====================
    
    if (smb) {
      const smb_type = smb.type;
      const phoneNumber = smb.to;
      let timestamp = await getIndianCurrentTime();
      let userSession = await getSession(business_phone_number_id, { wa_id: phoneNumber });

      let formattedConversation;
      let messageData = {
        type: smb_type
      };

      // Handle different message types for saving
      if (smb_type == "text") {
        formattedConversation = [{
          text: smb.text.body,
          sender: "bot",
          message_type: "text"
        }];
        messageData.text = smb.text.body;
      } else if (smb_type == "image") {
        formattedConversation = [{
          text: smb.image?.caption || '',
          sender: "bot",
          message_type: "image",
          media_url: smb.image?.link || smb.image?.id || '',
          media_caption: smb.image?.caption || ''
        }];
        messageData.image = smb.image;
      } else if (smb_type == "video") {
        formattedConversation = [{
          text: smb.video?.caption || '',
          sender: "bot",
          message_type: "video",
          media_url: smb.video?.link || smb.video?.id || '',
          media_caption: smb.video?.caption || ''
        }];
        messageData.video = smb.video;
      } else if (smb_type == "audio") {
        formattedConversation = [{
          text: '[Audio message]',
          sender: "bot",
          message_type: "audio",
          media_url: smb.audio?.link || smb.audio?.id || ''
        }];
        messageData.audio = smb.audio;
      } else if (smb_type == "document") {
        formattedConversation = [{
          text: smb.document?.filename || '[Document]',
          sender: "bot",
          message_type: "document",
          media_url: smb.document?.link || smb.document?.id || '',
          media_filename: smb.document?.filename || '',
          media_caption: smb.document?.caption || ''
        }];
        messageData.document = smb.document;
      } else if (smb_type == "sticker") {
        formattedConversation = [{
          text: '[Sticker]',
          sender: "bot",
          message_type: "sticker"
        }];
        messageData.sticker = smb.sticker;
      } else {
        // Fallback for other types
        formattedConversation = [{
          text: `[${smb_type} message]`,
          sender: "bot",
          message_type: smb_type
        }];
      }

      // Only save if we have formatted conversation
      if (formattedConversation) {
        try {
          await saveMessage(userSession.userPhoneNumber, userSession.business_phone_number_id, formattedConversation, userSession.tenant, timestamp);
        } catch (saveError) {
          console.error(`❌ Failed to save SMB message for ${phoneNumber}:`, saveError.message);
        }
      }

      io.emit('node-message', {
        message: messageData,
        phone_number_id: business_phone_number_id,
        contactPhone: phoneNumber,
        time: timestamp
      });
    }

    if (statuses) {
      let timestamp = await getIndianCurrentTime();
      const convertedTimestamp = await convertToValidDateFormat(timestamp);
      const status = statuses?.status;
      const id = statuses?.id;
      const userPhone = statuses?.recipient_id;
      const business_phone_number_id = req.body.entry?.[0].changes?.[0].value?.metadata?.phone_number_id;

      const sendTemplateStatusUpdate = async (status, errorCode = null) => {
        try {
          await delay(1000);
          const redisKey = `template_wamid:${id}`;
          let templateName = await getTemplateName(redisKey);

          // If template name not found (external sends), use fallback to ensure tracking still works
          const isExternalSend = !templateName;
          if (!templateName) {
            templateName = "external_template"; // Fallback for templates sent directly via Facebook API
            console.log(`📋 [TEMPLATE_STATUS] External template (no mapping) for wamid: ${id?.substring(0, 30)}... (status: ${status}, phone: ${userPhone})`);
          } else {
            console.log(`📋 [TEMPLATE_STATUS] Found template "${templateName}" for wamid: ${id?.substring(0, 30)}... (status: ${status})`);
            await delTemplateName(redisKey);
          }

          // Get tenant info - wrap in try-catch to ensure we continue even if lookup fails
          let tenant_id = null;
          let userName = null;

          try {
            let responseData = messageCache.get(business_phone_number_id);
            if (!responseData) {
              const response = await axios.get(`${fastURL}/whatsapp_tenant`, { headers: { 'bpid': business_phone_number_id } });
              responseData = response.data;
              messageCache.set(business_phone_number_id, responseData);
            }
            tenant_id = responseData?.whatsapp_data?.[0]?.tenant_id || null;
          } catch (tenantErr) {
            console.warn(`⚠️ [TEMPLATE_STATUS] Could not fetch tenant for bpid ${business_phone_number_id}: ${tenantErr.message}`);
          }

          // Try to get username - don't fail if not found
          try {
            if (tenant_id) {
              const response = await axios.get(`${djangoURL}/contacts-by-phone/${userPhone}/`, {
                headers: { 'X-Tenant-Id': tenant_id }
              });
              userName = response.data?.[0]?.name || null;
            }
          } catch (userErr) {
            // Contact not found is common for new/external users - just log it
            console.log(`📋 [TEMPLATE_STATUS] Contact not found for ${userPhone} (continuing with null name)`);
          }

          const templateStatusPayload = {
            template_name: templateName,
            phone_number: userPhone,
            name: userName,
            tenant_id: tenant_id,
            status: status,
            timestamp: convertedTimestamp,
            is_external_send: isExternalSend // Flag to identify external sends
          };

          if (status === "failed" && errorCode) {
            templateStatusPayload.error_code = errorCode;
          }

          await axios.post('https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/template_status', templateStatusPayload);
          console.log(`Template status update sent for ${status}:`, templateStatusPayload);

          // DISABLED: Auto-reschedule was causing duplicate/unwanted template sends
          // When a template fails with rate limit (131049), we now log it instead of auto-rescheduling
          // This prevents old templates from being sent unexpectedly
          if (errorCode && errorCode === 131049) {
            console.log(`[RATE_LIMIT] Template '${templateName}' failed for ${userPhone} due to rate limit (131049). NOT auto-rescheduling to prevent duplicates.`);
            // Log to a separate endpoint for manual review if needed
            try {
              await axios.post(`${djangoURL}/rate-limited-templates/`, {
                template_name: templateName,
                phone_number: userPhone,
                tenant_id: tenant_id,
                business_phone_number_id: business_phone_number_id,
                error_code: errorCode,
                timestamp: new Date().toISOString()
              }, { headers: { 'X-Tenant-Id': tenant_id } });
            } catch (logError) {
              console.error('[RATE_LIMIT] Failed to log rate-limited template:', logError.message);
            }
          }
        } catch (error) {
          console.error('Error sending template status update:', error);
        }
      };

      if (status == "sent") {
        // Handle "sent" status - message was accepted by WhatsApp
        const isoTimestamp = new Date(convertedTimestamp).toISOString();
        throttledStatsPost(`${djangoURL}/individual_message_statistics/`, { message_id: id, status, timestamp: isoTimestamp }, { 'bpid': business_phone_number_id });
        console.log(`📤 [STATUS] Sent to: ${userPhone} (wamid: ${id?.substring(0, 30)}...)`);
        await sendTemplateStatusUpdate(status);

        // Track analytics
        try {
          await trackMessageStatus({
            messageId: id,
            status: 'sent',
            timestamp: new Date(convertedTimestamp)
          });
        } catch (analyticsError) {
          console.error('❌ [Analytics] Failed to track sent status:', analyticsError);
        }
      }
      else if (status == "failed") {
        // Convert to ISO 8601 with timezone for Django
        const isoTimestamp = new Date(convertedTimestamp).toISOString();
        throttledStatsPost(`${djangoURL}/individual_message_statistics/`, { message_id: id, status, timestamp: isoTimestamp }, { 'bpid': business_phone_number_id });
        const error = statuses?.errors[0];
        console.log(`❌ [STATUS] Failed: ${userPhone} - ${error?.message || 'Unknown'} (wamid: ${id?.substring(0, 30)}...)`);
        io.emit('failed-response', error);
        await sendTemplateStatusUpdate(status, error?.code);

        // Save failed status to conversation
        try {
          const userSession = await getSession(business_phone_number_id, { wa_id: userPhone }, true);
          await saveMessage(
            userPhone,
            business_phone_number_id,
            [{ text: `[System: Message failed - ${error?.message || 'Unknown error'}]`, sender: "system" }],
            userSession.tenant,
            timestamp
          );
        } catch (err) {
          console.error('Error saving failed status to conversation:', err.message);
        }

        // Track analytics
        try {
          await trackMessageStatus({
            messageId: id,
            status: 'failed',
            timestamp: new Date(convertedTimestamp),
            errorReason: error?.message || error?.error_data?.details
          });
        } catch (analyticsError) {
          console.error('❌ [Analytics] Failed to track failed status:', analyticsError);
        }
      }
      else if (status == "delivered") {
        // Convert to ISO 8601 with timezone for Django
        const isoTimestamp = new Date(convertedTimestamp).toISOString();
        throttledStatsPost(`${djangoURL}/individual_message_statistics/`, { message_id: id, status, timestamp: isoTimestamp }, { 'bpid': business_phone_number_id });
        console.log("Delivered: ", userPhone);
        updateLastSeen("delivered", timestamp, userPhone, business_phone_number_id);
        await sendTemplateStatusUpdate(status);

        // Track analytics
        try {
          await trackMessageStatus({
            messageId: id,
            status: 'delivered',
            timestamp: new Date(convertedTimestamp)
          });
        } catch (analyticsError) {
          console.error('❌ [Analytics] Failed to track delivered status:', analyticsError);
        }
      }
      else if (status == "read") {
        // Convert to ISO 8601 with timezone for Django
        const isoTimestamp = new Date(convertedTimestamp).toISOString();
        throttledStatsPost(`${djangoURL}/individual_message_statistics/`, { message_id: id, status, timestamp: isoTimestamp }, { 'bpid': business_phone_number_id });
        console.log(`👁️ [STATUS] Read by: ${userPhone} (wamid: ${id?.substring(0, 30)}...)`);
        updateLastSeen("seen", timestamp, userPhone, business_phone_number_id);
        await sendTemplateStatusUpdate(status);

        // Track analytics
        try {
          await trackMessageStatus({
            messageId: id,
            status: 'read',
            timestamp: new Date(convertedTimestamp)
          });
        } catch (analyticsError) {
          console.error('❌ [Analytics] Failed to track read status:', analyticsError);
        }
      }
      else if (statuses.type == "payment") {
        console.log("recieved payment")
        const userSession = await getSession(business_phone_number_id, { wa_id: statuses.recipient_id });
        const urltest = "https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/order-payment";
        const config = {
          headers: {
            'Authorization': `Bearer ${userSession.accessToken}`,
            'Content-Type': 'application/json'
          }
        };
        const requestBody = {
          status: statuses,
          userSession
        };
        const response = await axios.post(urltest, requestBody, config);
      }

      const activeCampaign = await readData();
      const key = `${business_phone_number_id}_${userPhone}`;
      if (key in activeCampaign) {
        return campaignWebhook(req, res, activeCampaign[key]);
      }
    }
    console.log("============================================================");
    console.log("✅ [WEBHOOK] Webhook Processing Complete - " + new Date().toISOString());
    console.log("============================================================");
  }
  catch (error) {
    console.error("============================================================");
    console.error("❌ [WEBHOOK] Error in webhook handler:", error);
    console.error("❌ [WEBHOOK] Error stack:", error.stack);
    console.error("============================================================");
    // Only send error status if response hasn't been sent yet
    if (!res.headersSent) {
      res.sendStatus(500);
    }
  }
});

// ==================== REGISTER EXTERNAL TEMPLATE SENDS ====================
// Use this endpoint when sending templates directly via Facebook API
// to enable proper status tracking in this server
router.post("/register-template-send", async (req, res) => {
  try {
    const { message_id, template_name, phone_number, business_phone_id } = req.body;

    if (!message_id || !template_name) {
      return res.status(400).json({
        error: "Missing required fields",
        required: ["message_id", "template_name"],
        optional: ["phone_number", "business_phone_id"]
      });
    }

    const { setTemplateName } = await import('../queues/workerQueues.js');
    const redisKey = `template_wamid:${message_id}`;

    // Store with 10-minute TTL (same as internal sends)
    await setTemplateName(redisKey, template_name, { EX: 600 });

    console.log(`📋 [REGISTER] External template registered: "${template_name}" -> ${message_id?.substring(0, 30)}...`);
    if (phone_number) console.log(`   Phone: ${phone_number}`);

    return res.status(200).json({
      success: true,
      message: "Template send registered successfully",
      message_id,
      template_name,
      expires_in_seconds: 600
    });
  } catch (error) {
    console.error("❌ [REGISTER] Error registering template:", error.message);
    return res.status(500).json({ error: "Failed to register template send" });
  }
});

// Batch register multiple template sends at once
router.post("/register-template-sends-batch", async (req, res) => {
  try {
    const { sends } = req.body;

    if (!Array.isArray(sends) || sends.length === 0) {
      return res.status(400).json({
        error: "Missing or invalid 'sends' array",
        example: { sends: [{ message_id: "wamid.xxx", template_name: "my_template" }] }
      });
    }

    const { setTemplateName } = await import('../queues/workerQueues.js');
    const results = [];

    for (const send of sends) {
      const { message_id, template_name } = send;

      if (!message_id || !template_name) {
        results.push({ message_id, success: false, error: "Missing message_id or template_name" });
        continue;
      }

      try {
        const redisKey = `template_wamid:${message_id}`;
        await setTemplateName(redisKey, template_name, { EX: 600 });
        results.push({ message_id, template_name, success: true });
      } catch (err) {
        results.push({ message_id, success: false, error: err.message });
      }
    }

    const successCount = results.filter(r => r.success).length;
    console.log(`📋 [REGISTER-BATCH] Registered ${successCount}/${sends.length} templates`);

    return res.status(200).json({
      success: true,
      registered: successCount,
      total: sends.length,
      results
    });
  } catch (error) {
    console.error("❌ [REGISTER-BATCH] Error:", error.message);
    return res.status(500).json({ error: "Failed to register template sends" });
  }
});

router.get("/webhook", (req, res) => {
  console.log("============================================================");
  console.log("🔔 [WEBHOOK-VERIFY] GET /webhook request received - " + new Date().toISOString());
  const mode = req.query["hub.mode"];
  const token = req.query["hub.verify_token"];
  const challenge = req.query["hub.challenge"];
  console.log("📋 [WEBHOOK-VERIFY] Query params:");
  console.log("   hub.mode:", mode);
  console.log("   hub.verify_token:", token ? "[PRESENT]" : "[MISSING]");
  console.log("   hub.challenge:", challenge ? "[PRESENT]" : "[MISSING]");
  console.log("received req body: ", req.body);
  if (mode === "subscribe" && token === WEBHOOK_VERIFY_TOKEN) {
    res.status(200).send(challenge);
    console.log("✅ [WEBHOOK-VERIFY] Webhook verified successfully!");
  } else {
    console.log("❌ [WEBHOOK-VERIFY] Verification failed - token mismatch or wrong mode");
    res.sendStatus(403);
  }
  console.log("============================================================");
});

export default router;
