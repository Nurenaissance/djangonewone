import express from 'express';
import axios from 'axios';
import { sendCampaign, sendTemplate, sendTemplateToGroup } from '../templateService.js';
import { messageCache } from '../server.js';
import { fastURL } from '../mainwebhook/snm.js';
import crypto from 'crypto';

const router = express.Router();

// Generate unique batch ID for tracking
function generateBatchId() {
  return `batch_${Date.now()}_${crypto.randomBytes(4).toString('hex')}`;
}

router.post("/send-template", async (req, res) => {
  const type = req.body.type || "template";
  const bpid = req.body.business_phone_number_id;
  const batchId = generateBatchId();

  try {
    let responseData = messageCache.get(bpid);
    if (!responseData) {
      const response = await axios.get(`${fastURL}/whatsapp_tenant`, {
        headers: { 'bpid': bpid },
        // Fix BigInt precision issue
        transformResponse: [(data) => {
          if (typeof data === 'string') {
            try {
              // Fix large numbers before JSON parsing
              const fixedData = data.replace(
                /"business_account_id":\s*(\d{15,})/g,
                '"business_account_id":"$1"'
              ).replace(
                /"business_phone_number_id":\s*(\d{15,})/g,
                '"business_phone_number_id":"$1"'
              );
              return JSON.parse(fixedData);
            } catch (e) {
              return JSON.parse(data);
            }
          }
          return data;
        }]
      });
      responseData = response.data;
      messageCache.set(bpid, responseData);
    }

    const whatsappData = responseData.whatsapp_data?.[0];
    if (!whatsappData) {
      return res.status(400).send({ status: 400, message: "Invalid WhatsApp data." });
    }

    const { access_token, tenant_id, business_account_id: account_id } = whatsappData;

    // Validate request data first (fast validation)
    const validateAndRespond = {
      campaign: () => {
        const campaignData = req.body?.campaign;
        if (!campaignData) {
          return { valid: false, error: "Campaign data not found in request" };
        }
        return { valid: true, data: campaignData };
      },
      template: () => {
        const templateData = req.body?.template;
        if (!templateData) {
          return { valid: false, error: "Template data not found in request" };
        }
        templateData.phone = req.body?.phoneNumbers;
        if (!templateData.phone || templateData.phone.length === 0) {
          return { valid: false, error: "Phone numbers not found in request" };
        }
        return { valid: true, data: templateData };
      },
      group: () => {
        const groupData = req.body?.group;
        if (!groupData) {
          return { valid: false, error: "Group data not found in request" };
        }
        return { valid: true, data: groupData };
      }
    };

    if (!validateAndRespond[type]) {
      return res.status(400).send({ status: 400, message: "Invalid type specified in request" });
    }

    const validation = validateAndRespond[type]();
    if (!validation.valid) {
      return res.status(400).send({ status: 400, message: validation.error });
    }

    // RESPOND IMMEDIATELY - user doesn't wait for processing
    res.status(200).send({
      status: 200,
      message: `${type.charAt(0).toUpperCase() + type.slice(1)} send initiated`,
      batchId: batchId,
      recipientCount: type === 'template' ? validation.data.phone?.length : 'processing'
    });

    // PROCESS IN BACKGROUND (after response sent)
    setImmediate(async () => {
      try {
        console.log(`[${batchId}] Starting background processing for ${type}`);

        if (type === 'campaign') {
          await sendCampaign(validation.data, access_token, tenant_id, account_id, bpid, batchId);
        } else if (type === 'template') {
          await sendTemplate(validation.data, access_token, tenant_id, account_id, bpid, batchId);
        } else if (type === 'group') {
          await sendTemplateToGroup(validation.data, access_token, tenant_id, account_id, bpid, batchId);
        }

        console.log(`[${batchId}] Background processing completed for ${type}`);
      } catch (error) {
        console.error(`[${batchId}] Error in background processing:`, error.message);
      }
    });

  } catch (error) {
    console.error("Error in /send-template:", error.message);
    res.status(500).send({ status: 500, message: "Internal server error" });
  }
});

export default router;
