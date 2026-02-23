/**
 * Webhook simulator tool — sends WhatsApp-format webhook payloads to the Node.js server.
 * Ported from whatsapp_bot_server_withclaude/testing/webhookSimulator.js
 */

import crypto from 'crypto';
import config from '../config.js';
import { httpRequest } from './http-request.js';

// --- Helpers ---

function generateMessageId() {
  return `wamid.${crypto.randomBytes(16).toString('hex').toUpperCase()}`;
}

function generateMediaId() {
  return crypto.randomBytes(16).toString('hex');
}

function getTimestamp() {
  return Math.floor(Date.now() / 1000).toString();
}

function buildBasePayload(phoneNumberId, userPhone, userName) {
  return {
    object: 'whatsapp_business_account',
    entry: [{
      id: phoneNumberId,
      changes: [{
        value: {
          messaging_product: 'whatsapp',
          metadata: {
            display_phone_number: phoneNumberId,
            phone_number_id: phoneNumberId,
          },
          contacts: [{
            profile: { name: userName },
            wa_id: userPhone,
          }],
          messages: [],
        },
        field: 'messages',
      }],
    }],
  };
}

function generateSignature(payloadString, appSecret) {
  const hmac = crypto.createHmac('sha256', appSecret);
  hmac.update(payloadString);
  return `sha256=${hmac.digest('hex')}`;
}

// --- Payload builders ---

function buildTextMessage(text, opts) {
  const payload = buildBasePayload(opts.phoneNumberId, opts.userPhone, opts.userName);
  payload.entry[0].changes[0].value.messages = [{
    from: opts.userPhone, id: generateMessageId(), timestamp: getTimestamp(),
    type: 'text', text: { body: text },
  }];
  return payload;
}

function buildButtonReply(buttonId, buttonTitle, opts) {
  const payload = buildBasePayload(opts.phoneNumberId, opts.userPhone, opts.userName);
  payload.entry[0].changes[0].value.messages = [{
    from: opts.userPhone, id: generateMessageId(), timestamp: getTimestamp(),
    type: 'interactive',
    interactive: { type: 'button_reply', button_reply: { id: buttonId, title: buttonTitle } },
  }];
  return payload;
}

function buildListReply(listId, listTitle, opts) {
  const payload = buildBasePayload(opts.phoneNumberId, opts.userPhone, opts.userName);
  payload.entry[0].changes[0].value.messages = [{
    from: opts.userPhone, id: generateMessageId(), timestamp: getTimestamp(),
    type: 'interactive',
    interactive: { type: 'list_reply', list_reply: { id: listId, title: listTitle, description: '' } },
  }];
  return payload;
}

function buildNfmReply(responseJson, opts) {
  const payload = buildBasePayload(opts.phoneNumberId, opts.userPhone, opts.userName);
  payload.entry[0].changes[0].value.messages = [{
    from: opts.userPhone, id: generateMessageId(), timestamp: getTimestamp(),
    type: 'interactive',
    interactive: {
      type: 'nfm_reply',
      nfm_reply: {
        response_json: typeof responseJson === 'string' ? responseJson : JSON.stringify(responseJson),
        body: 'Sent', name: 'flow',
      },
    },
  }];
  return payload;
}

function buildImageMessage(opts) {
  const payload = buildBasePayload(opts.phoneNumberId, opts.userPhone, opts.userName);
  payload.entry[0].changes[0].value.messages = [{
    from: opts.userPhone, id: generateMessageId(), timestamp: getTimestamp(),
    type: 'image',
    image: {
      id: generateMediaId(), mime_type: 'image/jpeg',
      sha256: crypto.randomBytes(32).toString('hex'), caption: opts.caption || '',
    },
  }];
  return payload;
}

function buildStatusUpdate(status, messageId, opts) {
  return {
    object: 'whatsapp_business_account',
    entry: [{
      id: opts.phoneNumberId,
      changes: [{
        value: {
          messaging_product: 'whatsapp',
          metadata: { display_phone_number: opts.phoneNumberId, phone_number_id: opts.phoneNumberId },
          statuses: [{
            id: messageId || generateMessageId(),
            status, timestamp: getTimestamp(), recipient_id: opts.userPhone,
          }],
        },
        field: 'messages',
      }],
    }],
  };
}

// --- Main tool function ---

export async function simulateWebhook({
  message_type, text, button_id, button_title, list_id, list_title,
  nfm_response_json, status_type, status_message_id, caption,
}) {
  const opts = {
    phoneNumberId: config.whatsapp.phoneNumberId,
    userPhone: config.whatsapp.userPhone,
    userName: config.whatsapp.userName,
    caption,
  };

  let payload;
  switch (message_type) {
    case 'text':
      payload = buildTextMessage(text || 'Hi', opts);
      break;
    case 'button_reply':
      payload = buildButtonReply(button_id || 'btn_1', button_title || 'Yes', opts);
      break;
    case 'list_reply':
      payload = buildListReply(list_id || 'list_1', list_title || 'Option 1', opts);
      break;
    case 'nfm_reply':
      payload = buildNfmReply(nfm_response_json || '{}', opts);
      break;
    case 'image':
      payload = buildImageMessage(opts);
      break;
    case 'status_update':
      payload = buildStatusUpdate(status_type || 'delivered', status_message_id, opts);
      break;
    default:
      return { success: false, error: `Unknown message_type: ${message_type}` };
  }

  const payloadString = JSON.stringify(payload);
  const signature = generateSignature(payloadString, config.whatsapp.appSecret);
  const webhookUrl = `${config.services.nodejs}/webhook`;

  const result = await httpRequest({
    url: webhookUrl,
    method: 'POST',
    headers: { 'x-hub-signature-256': signature },
    body: payloadString,
    timeout: 15000,
  });

  return {
    message_type,
    webhook_status: result.status,
    success: result.success,
    responseTime_ms: result.responseTime_ms,
    response: result.body,
    error: result.error,
  };
}

/**
 * Run a multi-step webhook flow with delays between steps.
 */
export async function runWebhookFlow({ steps, delay_ms = 1500 }) {
  const results = [];
  for (let i = 0; i < steps.length; i++) {
    const step = steps[i];
    const result = await simulateWebhook(step);
    results.push({ step: i + 1, ...result });
    if (i < steps.length - 1) {
      await new Promise((r) => setTimeout(r, delay_ms));
    }
  }
  return { flow_results: results, total_steps: steps.length, passed: results.filter((r) => r.success).length };
}
