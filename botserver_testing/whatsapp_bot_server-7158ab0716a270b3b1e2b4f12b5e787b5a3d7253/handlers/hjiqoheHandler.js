/**
 * HelloZestay Handler for hjiqohe tenant
 *
 * Handles:
 * 1. HelloZestay command - Redis guest ID check + welcome message + trigger flow 209
 * 2. Bulk media uploads - Collects multiple images/docs and sends to process-multiple-media endpoint
 *
 * Everything else uses normal flow handling.
 */

import axios from 'axios';
import { createClient } from 'redis';
import { sendMessage } from '../send-message.js';
import { saveMessage, triggerFlowById } from '../helpers/misc.js';
import { getIndianCurrentTime } from '../utils.js';
import { normalizePhone } from '../normalize.js';
import { userSessions } from '../server.js';
import { sendNodeMessage } from '../mainwebhook/snm.js';

// =============================================================================
// CONFIGURATION
// =============================================================================

const HJIQOHE_CONFIG = {
  FLOW_ID: '209',
  MEDIA_BATCH_TIMEOUT: 3000,  // 3 seconds to wait for additional files
  MULTI_MEDIA_ENDPOINT: 'https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/process-multiple-media',
  RESORT_API: 'https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net/webhook/resort',
  DJANGO_URL: process.env.DJANGO_URL || 'https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net'
};

// =============================================================================
// STATE TRACKING
// =============================================================================

// Track media batches for multi-image uploads
const mediaBatches = new Map(); // userKey -> { mediaFiles, timeout, resolve }

// Redis client for guest lookup
let redisClient = null;

async function getRedisClient() {
  if (redisClient && redisClient.isOpen) {
    return redisClient;
  }
  try {
    redisClient = createClient({
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      ...(process.env.REDIS_PASSWORD && { password: process.env.REDIS_PASSWORD })
    });
    redisClient.on('error', (err) => console.error('[hjiqohe] Redis error:', err.message));
    await redisClient.connect();
    return redisClient;
  } catch (err) {
    console.error('[hjiqohe] Redis connection failed:', err.message);
    return null;
  }
}

// =============================================================================
// PUBLIC API
// =============================================================================

/**
 * Check if there's an active media batch collection for this user
 */
export function isInHjiqoheFlow(userPhoneNumber, businessPhoneId) {
  const userKey = `${normalizePhone(userPhoneNumber)}:${businessPhoneId}`;
  return mediaBatches.has(userKey);
}

/**
 * Main entry point - handles HelloZestay command and bulk media uploads
 */
export async function handleHjiqoheMessage(userSession, message, req) {
  const messageType = message?.type;
  const messageText = message?.text?.body || '';

  // Handle HelloZestay command
  if (messageText.toLowerCase().startsWith('hellozestay')) {
    console.log(`[hjiqohe] HelloZestay command detected`);
    return handleHelloZestayCommand(userSession, message);
  }

  // Handle bulk media uploads (images/documents)
  if (['image', 'document'].includes(messageType)) {
    console.log(`[hjiqohe] Media upload detected: ${messageType}`);
    return handleMediaUpload(userSession, message);
  }

  // Everything else - let normal webhook handle it
  return false;
}

// =============================================================================
// HELLOZESTAY HANDLER
// =============================================================================

async function handleHelloZestayCommand(userSession, message) {
  const userPhoneNumber = normalizePhone(userSession.userPhoneNumber);
  const businessPhoneId = userSession.business_phone_number_id;
  const messageText = message?.text?.body || '';
  const timestamp = await getIndianCurrentTime();

  // Parse guest ID from message
  const parts = messageText.trim().split(/\s+/);
  const guestId = parts.length > 1 ? parts[1].toUpperCase() : null;

  console.log(`[hjiqohe] Processing HelloZestay for guest: ${guestId}`);

  // Save incoming message
  try {
    await saveMessage(
      userPhoneNumber,
      businessPhoneId,
      [{ text: messageText, sender: 'user', message_type: 'text' }],
      userSession.tenant,
      timestamp
    );
  } catch (err) {
    console.error('[hjiqohe] Save incoming message error:', err.message);
  }

  // Validate guest ID
  if (!guestId) {
    await sendMessage(
      userPhoneNumber,
      businessPhoneId,
      {
        type: 'text',
        text: { body: '⚠️ Please provide your Property ID.\n\nFormat: HelloZestay [YOUR_ID]' }
      },
      userSession.accessToken,
      userSession.tenant
    );
    return true;
  }

  // Look up resort name from Redis/API
  const resortName = await lookupResort(guestId);

  if (!resortName) {
    await sendMessage(
      userPhoneNumber,
      businessPhoneId,
      {
        type: 'text',
        text: { body: `⚠️ Guest ID "${guestId}" not found. Please check your Property ID and try again.` }
      },
      userSession.accessToken,
      userSession.tenant
    );
    return true;
  }

  console.log(`[hjiqohe] Resort found: ${resortName}`);

  // Get user's name for welcome message
  const userName = userSession.userName || userSession.name || 'Guest';

  // Store guestId and resortName in session for flow to use
  userSession.guestId = guestId;
  userSession.resortName = resortName;

  // Send welcome message with name and property from Redis
  console.log(`[hjiqohe] Sending welcome: Hi ${userName}! You have arrived at ${resortName}`);
  await sendMessage(
    userPhoneNumber,
    businessPhoneId,
    {
      type: 'text',
      text: { body: `Hi *${userName}*! You have arrived at *${resortName}*.` }
    },
    userSession.accessToken,
    userSession.tenant
  );

  // Save the welcome message
  try {
    await saveMessage(
      userPhoneNumber,
      businessPhoneId,
      [{ text: `Hi ${userName}! You have arrived at ${resortName}.`, sender: 'bot', message_type: 'text' }],
      userSession.tenant,
      timestamp
    );
  } catch (err) {
    console.error('[hjiqohe] Save welcome message error:', err.message);
  }

  // Save dynamic data to Django (background)
  axios.post(
    `${HJIQOHE_CONFIG.DJANGO_URL}/add-dynamic-data/`,
    {
      flow_name: 'zestayreceptionmain',
      input_variable: 'propertyid',
      value: guestId,
      phone: userPhoneNumber
    },
    { headers: { 'X-Tenant-Id': 'hjiqohe' }, timeout: 5000 }
  ).catch(err => console.error('[hjiqohe] Dynamic data error:', err.message));

  // Trigger flow 209 - let it run normally like any other tenant
  console.log(`[hjiqohe] Triggering flow ${HJIQOHE_CONFIG.FLOW_ID}`);
  try {
    await triggerFlowById(userSession, HJIQOHE_CONFIG.FLOW_ID);
    console.log(`[hjiqohe] Flow ${HJIQOHE_CONFIG.FLOW_ID} triggered successfully`);
  } catch (err) {
    console.error(`[hjiqohe] Flow trigger error:`, err.message);
    await sendMessage(
      userPhoneNumber,
      businessPhoneId,
      {
        type: 'text',
        text: { body: '⚠️ An error occurred starting the check-in process. Please try again.' }
      },
      userSession.accessToken,
      userSession.tenant
    );
  }

  return true;
}

// =============================================================================
// BULK MEDIA UPLOAD HANDLER
// =============================================================================

async function handleMediaUpload(userSession, message) {
  const userPhoneNumber = normalizePhone(userSession.userPhoneNumber);
  const businessPhoneId = userSession.business_phone_number_id;
  const userKey = `${userPhoneNumber}:${businessPhoneId}`;
  const sessionKey = userPhoneNumber + businessPhoneId;

  const mediaType = message?.type;
  const mediaId = message?.image?.id || message?.document?.id;
  const timestamp = await getIndianCurrentTime();

  if (!mediaId) {
    console.log(`[hjiqohe] No media ID found in message`);
    return false;
  }

  console.log(`[hjiqohe] Collecting media: ${mediaId} (type: ${mediaType})`);

  // Get current session to get flow info
  const currentSession = await userSessions.get(sessionKey);
  if (!currentSession) {
    console.log(`[hjiqohe] No session found, passing to normal handler`);
    return false;
  }

  // Collect media with batch timeout
  const mediaFiles = await collectMedia(userKey, {
    mediaId: mediaId,
    type: mediaType,
    timestamp: timestamp
  }, currentSession);

  console.log(`[hjiqohe] Batch complete: ${mediaFiles.length} media file(s)`);

  // Process the batch
  await processBulkMedia(userSession, currentSession, mediaFiles, timestamp);

  return true;
}

/**
 * Collect media files with a batch timeout
 * Waits for additional uploads before processing
 */
function collectMedia(userKey, mediaInfo, userSession) {
  return new Promise((resolve) => {
    const existingBatch = mediaBatches.get(userKey);

    if (existingBatch) {
      // Add to existing batch
      existingBatch.mediaFiles.push({
        ...mediaInfo,
        sequence: existingBatch.mediaFiles.length + 1
      });
      console.log(`[hjiqohe] Added to batch: ${existingBatch.mediaFiles.length} files`);

      // Reset timeout
      clearTimeout(existingBatch.timeout);
      existingBatch.timeout = setTimeout(() => {
        const batch = mediaBatches.get(userKey);
        mediaBatches.delete(userKey);
        console.log(`[hjiqohe] Batch timeout - processing ${batch.mediaFiles.length} files`);
        batch.resolve(batch.mediaFiles);
      }, HJIQOHE_CONFIG.MEDIA_BATCH_TIMEOUT);

    } else {
      // Start new batch
      const newBatch = {
        mediaFiles: [{
          ...mediaInfo,
          sequence: 1
        }],
        userSession: userSession,
        resolve: resolve,
        timeout: setTimeout(() => {
          const batch = mediaBatches.get(userKey);
          mediaBatches.delete(userKey);
          console.log(`[hjiqohe] Single file timeout - processing ${batch.mediaFiles.length} files`);
          batch.resolve(batch.mediaFiles);
        }, HJIQOHE_CONFIG.MEDIA_BATCH_TIMEOUT)
      };

      mediaBatches.set(userKey, newBatch);
      console.log(`[hjiqohe] New batch started`);
    }
  });
}

/**
 * Process collected bulk media
 * 1. Send all media IDs to process-multiple-media endpoint
 * 2. Advance to Submit Now button node
 */
async function processBulkMedia(userSession, currentSession, mediaFiles, timestamp) {
  const userPhoneNumber = normalizePhone(userSession.userPhoneNumber);
  const businessPhoneId = userSession.business_phone_number_id;
  const sessionKey = userPhoneNumber + businessPhoneId;

  console.log(`[hjiqohe] Processing ${mediaFiles.length} media files`);

  // Prepare payload for process-multiple-media endpoint (no blob upload - just media IDs)
  const payload = {
    userPhone: userPhoneNumber,
    businessPhoneId: businessPhoneId,
    flowName: currentSession.flowName || 'zestayreceptionmain',
    inputVariable: currentSession.inputVariable || 'document',
    timestamp: timestamp,
    mediaFiles: mediaFiles.map(m => ({
      mediaId: m.mediaId,
      type: m.type,
      sequence: m.sequence
    })),
    guestId: currentSession.guestId || userSession.guestId,
    resortName: currentSession.resortName || userSession.resortName,
    accessToken: currentSession.accessToken  // Include token so endpoint can fetch media if needed
  };

  console.log(`[hjiqohe] Sending to process-multiple-media endpoint:`, JSON.stringify(payload, null, 2));

  // Send to process-multiple-media endpoint
  try {
    const response = await axios.post(HJIQOHE_CONFIG.MULTI_MEDIA_ENDPOINT, payload, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${currentSession.accessToken}`
      },
      timeout: 30000
    });
    console.log(`[hjiqohe] Multi-media endpoint response:`, response.data);
  } catch (err) {
    console.error(`[hjiqohe] Multi-media endpoint error:`, err.message);
    // Continue even if endpoint fails
  }

  // Find and advance to the "Submit Now" button node
  await advanceToSubmitNowNode(currentSession, userPhoneNumber, businessPhoneId, sessionKey);
}

/**
 * Find the node containing "Submit Now" button and advance to it
 */
async function advanceToSubmitNowNode(currentSession, userPhoneNumber, businessPhoneId, sessionKey) {
  const flowData = currentSession.flowData;
  const adjList = currentSession.adjList;

  if (!flowData || !adjList) {
    console.log(`[hjiqohe] No flow data found, cannot advance to Submit Now`);
    return;
  }

  // Find the node that has a "Submit Now" button
  let submitNowNodeId = null;

  for (const [nodeId, nodeData] of Object.entries(flowData)) {
    // Check if this node is a Button type with "Submit Now" text
    if (nodeData.type === 'Button' || nodeData.type === 'button') {
      const bodyText = nodeData.body || '';
      if (bodyText.toLowerCase().includes('submit') ||
          bodyText.toLowerCase().includes('all docs received')) {
        submitNowNodeId = nodeId;
        console.log(`[hjiqohe] Found Submit Now node: ${nodeId} with body: "${bodyText.substring(0, 50)}..."`);
        break;
      }
    }

    // Also check adjacent nodes for button_element with "Submit" text
    const nextNodes = adjList[nodeId] || [];
    for (const nextId of nextNodes) {
      const nextNode = flowData[nextId];
      if (nextNode && (nextNode.body || '').toLowerCase().includes('submit')) {
        submitNowNodeId = nodeId;
        console.log(`[hjiqohe] Found node before Submit button: ${nodeId}`);
        break;
      }
    }
    if (submitNowNodeId) break;
  }

  if (!submitNowNodeId) {
    // Fallback: look for node with id containing common patterns
    for (const nodeId of Object.keys(flowData)) {
      const node = flowData[nodeId];
      if (node.type === 'Button' && adjList[nodeId]?.length >= 2) {
        // Button with multiple options (likely the submit/add more choice)
        submitNowNodeId = nodeId;
        console.log(`[hjiqohe] Fallback: Found Button node with choices: ${nodeId}`);
        break;
      }
    }
  }

  if (submitNowNodeId) {
    console.log(`[hjiqohe] Advancing to Submit Now node: ${submitNowNodeId}`);

    currentSession.currNode = submitNowNodeId;
    currentSession.nextNode = adjList[submitNowNodeId] || [];
    currentSession.inputVariable = null; // Clear input variable

    await userSessions.set(sessionKey, currentSession);

    // Send the node message
    try {
      await sendNodeMessage(userPhoneNumber, businessPhoneId);
      console.log(`[hjiqohe] Submit Now node message sent`);
    } catch (err) {
      console.error(`[hjiqohe] Error sending Submit Now node:`, err.message);
    }
  } else {
    console.log(`[hjiqohe] Could not find Submit Now node, flow will continue from current position`);

    // Just advance to the next node in the flow
    const currNode = currentSession.currNode;
    const nextNodes = adjList[currNode] || adjList[String(currNode)] || [];

    if (nextNodes.length > 0) {
      currentSession.currNode = nextNodes[0];
      currentSession.nextNode = adjList[nextNodes[0]] || [];
      currentSession.inputVariable = null;

      await userSessions.set(sessionKey, currentSession);

      try {
        await sendNodeMessage(userPhoneNumber, businessPhoneId);
      } catch (err) {
        console.error(`[hjiqohe] Error sending next node:`, err.message);
      }
    }
  }
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

async function lookupResort(guestId) {
  console.log(`[hjiqohe] Looking up resort for guest: ${guestId}`);

  // Try Redis first
  try {
    const redis = await getRedisClient();
    if (redis) {
      const cached = await redis.get(`guest:${guestId}:resort`);
      if (cached) {
        console.log(`[hjiqohe] Redis hit: ${cached}`);
        return cached;
      }
    }
  } catch (err) {
    console.error('[hjiqohe] Redis lookup error:', err.message);
  }

  // Try API
  try {
    const response = await axios.get(HJIQOHE_CONFIG.RESORT_API, {
      params: { tenantId: guestId },
      timeout: 5000
    });

    const resortName = response.data?.resortName;
    if (resortName) {
      console.log(`[hjiqohe] API returned: ${resortName}`);

      // Cache in Redis
      const redis = await getRedisClient();
      if (redis) {
        redis.setEx(`guest:${guestId}:resort`, 3600, resortName)
          .catch(err => console.error('[hjiqohe] Redis cache error:', err.message));
      }

      return resortName;
    }
  } catch (err) {
    console.error('[hjiqohe] API lookup error:', err.message);
  }

  return null;
}
