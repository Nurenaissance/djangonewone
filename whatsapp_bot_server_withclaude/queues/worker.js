import axios from "axios";
import { writeFile, readFile } from 'fs/promises';
import { messageQueue, getCampaignUserSession, setCampaignUserSession, setTemplateName } from "./workerQueues.js";
import { getIndianCurrentTime } from '../utils.js';
import { getCampaignState, incrementCounter, emitProgress } from '../campaignControl.js';
import { trackMessageSend } from '../analytics/tracker.js';
import pLimit from 'p-limit';

const djangoURL = process.env.DJANGO_URL || "https://backeng4whatsapp-dxbmgpakhzf9bped.centralindia-01.azurewebsites.net"

// Reduced workers to avoid rate limits - Facebook allows ~80 messages/second
// But safer to stay around 30-50/second to avoid hitting limits
const numberOfWorkers = parseInt(process.env.BULK_WORKERS || '5', 10);

// Rate limiting configuration
const RATE_LIMIT_DELAY_MS = parseInt(process.env.RATE_LIMIT_DELAY_MS || '100', 10); // Delay between messages (ms)
const MAX_RETRIES = 3;
const INITIAL_BACKOFF_MS = 2000; // Start with 2 second backoff

// Helper function for delay
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// ============================================================================
// DJANGO CALL THROTTLING
// ============================================================================
// Limit concurrent HTTP requests to Django during bulk campaigns.
// Without this, 5 workers × 2 Django calls each = 10+ concurrent requests
// that pile up and starve Django for login/interactive requests.
const DJANGO_CONCURRENCY = parseInt(process.env.DJANGO_CAMPAIGN_CONCURRENCY || '3', 10);
const djangoLimit = pLimit(DJANGO_CONCURRENCY);
const DJANGO_TIMEOUT_MS = 10000; // 10s timeout for campaign saves (non-critical)

/**
 * Fire-and-forget Django call with concurrency limiting and timeout.
 * Campaign stats/saves are important but NOT worth blocking workers or
 * starving Django's ability to serve login and interactive requests.
 */
function djangoPostFireAndForget(url, data, headers = {}) {
  djangoLimit(() =>
    axios.post(url, data, { headers, timeout: DJANGO_TIMEOUT_MS })
  ).catch(err => {
    console.warn(`⚠️ [Campaign Django] ${url} failed: ${err.message}`);
  });
}

// Check if error is a rate limit error
function isRateLimitError(error) {
  const errorCode = error.response?.data?.error?.code;
  const errorSubcode = error.response?.data?.error?.error_subcode;
  // Facebook rate limit error codes
  return errorCode === 130429 || // Rate limit hit
         errorCode === 131056 || // Too many requests
         errorSubcode === 2494055 || // Rate limit
         error.response?.status === 429;
}

// ============================================================================
// QUEUE WORKERS (Only register if messageQueue is available)
// ============================================================================

if (messageQueue) {
  console.log('🔄 Registering Bull Queue workers...');

  messageQueue.process('campaign', numberOfWorkers, async(job) => {
  try{
    const { messageData, contact, templateInfo, campaignData, batchId } = job.data
    console.log("Rcvd message queue data in campaign worker: ", job.data)

    // CAMPAIGN STATE CHECK - Skip if campaign has been stopped
    if (batchId) {
      const state = await getCampaignState(batchId);
      if (state !== 'active') {
        console.log(`[Worker] Campaign ${batchId} is ${state} - skipping message to ${contact}`);
        return { skipped: true, reason: `Campaign ${state}`, contact };
      }
    }

    const key = `${campaignData.bpid}_${contact}`
    const campaignUserSession = await getCampaignUserSession(key)

    const messageID = await sendMessage(messageData, contact, campaignData.bpid, campaignData.access_token, campaignData.tenant_id, templateInfo?.name)

    // Track progress based on success/failure
    if (batchId) {
      if (messageID) {
        await incrementCounter(batchId, 'sent');
      } else {
        await incrementCounter(batchId, 'failed');
      }
      await emitProgress(batchId);
    }

    if (messageID) {
      campaignUserSession.templateInfo = templateInfo;
      campaignUserSession.lastMessageID = messageID;
      await setCampaignUserSession(key, campaignUserSession)
      addData(key, campaignData)

      const data = {message_id: messageID, status: "sent", type: "campaign", type_identifier: campaignData.name, template_name: templateInfo.name, userPhone: contact, tenant_id: campaignData.tenant_id}
      djangoPostFireAndForget(`${djangoURL}/individual_message_statistics/`, data, {'bpid': campaignData.bpid})
    }

    return { messageID, contact };
  }catch(err){
    console.error("Error occured in messageQueue(campaign): ", err)
    // Track as failed
    const { batchId } = job.data;
    if (batchId) {
      await incrementCounter(batchId, 'failed');
      await emitProgress(batchId);
    }
    throw err;
  }
})

messageQueue.process('template', numberOfWorkers, async(job) => {
  try {
    const { messageData, contact, templateData, batchId } = job.data;
    console.log("Rcvd message queue data in template worker: ", job.data);

    // CAMPAIGN STATE CHECK - Skip if campaign has been stopped
    if (batchId) {
      const state = await getCampaignState(batchId);
      if (state !== 'active') {
        console.log(`[Worker] Template batch ${batchId} is ${state} - skipping message to ${contact}`);
        return { skipped: true, reason: `Campaign ${state}`, contact };
      }
    }

    const messageID = await sendMessage(messageData, contact, templateData.bpid, templateData.access_token, templateData.tenant_id, templateData.name);

    // Track progress based on success/failure
    if (batchId) {
      if (messageID) {
        await incrementCounter(batchId, 'sent');
      } else {
        await incrementCounter(batchId, 'failed');
      }
      await emitProgress(batchId);
    }

    if (messageID) {
      // Store the messageID in the job's result
      job.data.messageID = messageID;

      const key = `template_wamid:${messageID}`;
      await setTemplateName(key, templateData.name, { EX: 600 });

      const data = {
        message_id: messageID,
        status: "sent",
        type: "template",
        type_identifier: templateData.name,
        template_name: templateData.name,
        userPhone: contact,
        tenant_id: templateData.tenant_id
      };
      djangoPostFireAndForget(`${djangoURL}/individual_message_statistics/`, data, { 'bpid': templateData.bpid });
    }

    return { messageID, contact }; // Return result for job

  } catch (err) {
    console.error("Error occurred in messageQueue(template): ", err);
    // Track as failed
    const { batchId } = job.data;
    if (batchId) {
      await incrementCounter(batchId, 'failed');
      await emitProgress(batchId);
    }
    throw err; // Rethrow to mark job as failed
  }
});

messageQueue.process('group', numberOfWorkers, async(job) => {
  try {
    const { messageData, contact, groupData, batchId } = job.data;
    console.log("Rcvd message queue data in group worker: ", job.data);

    // CAMPAIGN STATE CHECK - Skip if campaign has been stopped
    if (batchId) {
      const state = await getCampaignState(batchId);
      if (state !== 'active') {
        console.log(`[Worker] Group batch ${batchId} is ${state} - skipping message to ${contact}`);
        return { skipped: true, reason: `Campaign ${state}`, contact };
      }
    }

    const messageID = await sendMessage(messageData, contact, groupData.bpid, groupData.access_token, groupData.tenant_id, groupData.templateName);

    // Track progress based on success/failure
    if (batchId) {
      if (messageID) {
        await incrementCounter(batchId, 'sent');
      } else {
        await incrementCounter(batchId, 'failed');
      }
      await emitProgress(batchId);
    }

    if (messageID) {
      const key = `template_wamid:${messageID}`;
      await setTemplateName(key, groupData.templateName, { EX: 600 });

      const data = {
        message_id: messageID,
        status: "sent",
        type: "group",
        type_identifier: groupData.name,
        template_name: groupData.templateName,
        userPhone: contact,
        tenant_id: groupData.tenant_id
      };
      djangoPostFireAndForget(`${djangoURL}/individual_message_statistics/`, data, { 'bpid': groupData.bpid });
    }

    return { messageID, contact };

  } catch (err) {
    console.error("Error occurred in messageQueue(group): ", err);
    // Track as failed
    const { batchId } = job.data;
    if (batchId) {
      await incrementCounter(batchId, 'failed');
      await emitProgress(batchId);
    }
    throw err;
  }
});

  console.log('✅ Bull Queue workers registered successfully');
} else {
  console.log('⚠️  Bull Queue workers disabled (messageQueue not available in local development mode)');
}

// ============================================================================
// MESSAGE SENDING FUNCTION (Always available)
// ============================================================================

export async function sendMessage(messageData, contact, bpid, access_token, tenant_id, templateName = null, retryCount = 0) {
  try{
    // Add small delay between messages to avoid rate limits
    if (RATE_LIMIT_DELAY_MS > 0) {
      await delay(RATE_LIMIT_DELAY_MS);
    }

    const url = `https://graph.facebook.com/v18.0/${bpid}/messages`;
    const headers = { 'Authorization': `Bearer ${access_token}`}

    contact = String(contact).trim();
    if(contact.length == 10) contact = `91${contact}`
    console.log("Sending Message to: ", contact, messageData, headers)
    const response = await axios.post(
      url,
      {
        messaging_product: "whatsapp",
        recipient_type: "individual",
        to: contact,
        ...messageData
      },
      {
        headers: headers
      }
    );
    const messageID = response.data.messages[0].id
    console.log("Message sent successfully: ", messageID)

    // Track analytics for frontend logs display
    try {
      const resolvedTemplateName = templateName || messageData?.template?.name || null;
      if (resolvedTemplateName) {
        await trackMessageSend({
          tenantId: tenant_id,
          messageId: messageID,
          templateId: resolvedTemplateName,
          templateName: resolvedTemplateName,
          recipientPhone: contact,
          recipientName: null,
          contactId: null,
          campaignId: null,
          broadcastGroupId: null,
          messageType: messageData.type || 'template',
          conversationCategory: 'marketing',
          cost: null,
          timestamp: new Date()
        });
        console.log(`✅ [Analytics] Tracked template message: ${resolvedTemplateName} to ${contact}`);
      }
    } catch (analyticsError) {
      console.error('❌ [Analytics] Failed to track message send:', analyticsError.message);
      // Don't fail the message send if analytics tracking fails
    }

    // Save template message to conversation (fire-and-forget with throttling)
    const timestamp = await getIndianCurrentTime();
    const formattedConversation = [{ text: messageData, sender: "bot" }];
    djangoPostFireAndForget(
      `${djangoURL}/whatsapp_convo_post/${contact}/?source=whatsapp`,
      {
        contact_id: contact,
        business_phone_number_id: bpid,
        conversations: formattedConversation,
        tenant: tenant_id,
        time: timestamp
      },
      { 'Content-Type': 'application/json', 'X-Tenant-Id': tenant_id }
    );

    return messageID
  }catch(error){
    console.error("Error rcvd in sendMessage: ", JSON.stringify(error, null, 7))

    // Log the specific Facebook API error if available
    if (error.response?.data) {
      console.error("❌ Facebook API Error Details:", JSON.stringify(error.response.data, null, 2));
    }

    // Handle rate limit errors with exponential backoff retry
    if (isRateLimitError(error) && retryCount < MAX_RETRIES) {
      const backoffTime = INITIAL_BACKOFF_MS * Math.pow(2, retryCount);
      console.log(`⚠️ Rate limit hit for ${contact}. Retrying in ${backoffTime}ms (attempt ${retryCount + 1}/${MAX_RETRIES})`);
      await delay(backoffTime);
      return sendMessage(messageData, contact, bpid, access_token, tenant_id, templateName, retryCount + 1);
    }

    // Return null to indicate failure
    return null;
  }
}

import path from 'path'
import { fileURLToPath } from 'url';


const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const filePath = path.resolve(__dirname, "../dataStore/activeCampaign.json");

export async function readData() {
  try {
      const data = await readFile(filePath, 'utf8');
      return JSON.parse(data);
  } catch (err) {
      console.error('Error reading the file:', err);
      return {};
  }
}

export async function writeData(data) {
  try {
      console.log("Erititng data: ", data, "to file: ", filePath)
      await writeFile(filePath, JSON.stringify(data, null, 2), 'utf8');
      console.log('Data successfully written to file: ', filePath);
  } catch (err) {
      console.error('Error writing to the file:', err);
  }
}

export async function addData(key, value) {
  try {
      const data = await readData();
      data[key] = value;
      await writeData(data);
      console.log(`Data added successfully for key: ${key}`);
  } catch (err) {
      console.error('Error adding data:', err);
  }
}

export async function deleteData(key) {
  try {
      const data = await readData();
      if (data[key]) {
          delete data[key];
          await writeData(data);
          console.log(`Data deleted for key: ${key}`);
      } else {
          console.log(`Key not found: ${key}`);
      }
  } catch (err) {
      console.error('Error deleting data:', err);
  }
}