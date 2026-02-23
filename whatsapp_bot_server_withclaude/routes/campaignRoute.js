import express from 'express';
import axios from 'axios';
import {
  stopCampaign,
  getCampaignStatus,
  listActiveCampaigns,
  resumeCampaign
} from '../campaignControl.js';
import { sendTemplate, sendCampaign, sendTemplateToGroup } from '../templateService.js';
import { messageCache } from '../server.js';
import { fastURL } from '../mainwebhook/snm.js';

const router = express.Router();

/**
 * POST /api/campaign/stop
 * Emergency HARD STOP for a campaign - immediately prevents any further message sending
 *
 * Request body:
 * {
 *   "batchId": "batch_xxx",
 *   "reason": "Emergency stop" (optional)
 * }
 *
 * Response:
 * {
 *   "success": true,
 *   "stats": {
 *     "sent": 500,
 *     "failed": 10,
 *     "stopped": 490,
 *     "total": 1000
 *   }
 * }
 */
router.post('/api/campaign/stop', async (req, res) => {
  const { batchId, reason } = req.body;

  if (!batchId) {
    return res.status(400).json({
      success: false,
      error: 'batchId is required'
    });
  }

  try {
    console.log(`[CampaignRoute] Stop request for campaign ${batchId}`);

    const result = await stopCampaign(batchId, reason || 'User requested stop');

    if (result.success) {
      res.json({
        success: true,
        message: `Campaign ${batchId} stopped successfully`,
        stats: result.stats
      });
    } else {
      res.status(400).json({
        success: false,
        error: result.error,
        stats: result.stats
      });
    }
  } catch (error) {
    console.error('[CampaignRoute] Error stopping campaign:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while stopping campaign'
    });
  }
});

/**
 * GET /api/campaign/status
 * Get current status and progress of a campaign
 *
 * Query params:
 * - batchId: Campaign batch ID (required)
 *
 * Response:
 * {
 *   "batchId": "batch_xxx",
 *   "state": "active",
 *   "progress": {
 *     "sent": 500,
 *     "failed": 10,
 *     "pending": 490,
 *     "total": 1000,
 *     "percentComplete": 51
 *   },
 *   "meta": {
 *     "tenantId": "xxx",
 *     "bpid": "xxx",
 *     "type": "template",
 *     "name": "promo_template"
 *   }
 * }
 */
router.get('/api/campaign/status', async (req, res) => {
  const { batchId } = req.query;

  if (!batchId) {
    return res.status(400).json({
      success: false,
      error: 'batchId query parameter is required'
    });
  }

  try {
    const status = await getCampaignStatus(batchId);

    if (!status) {
      return res.status(404).json({
        success: false,
        error: `Campaign ${batchId} not found`
      });
    }

    res.json({
      success: true,
      ...status
    });
  } catch (error) {
    console.error('[CampaignRoute] Error getting campaign status:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while fetching campaign status'
    });
  }
});

/**
 * GET /api/campaign/list
 * List all active/recent campaigns for a tenant
 *
 * Query params:
 * - tenant_id: Tenant ID (required)
 * - bpid: Business phone number ID (required)
 *
 * Response:
 * {
 *   "success": true,
 *   "campaigns": [
 *     {
 *       "batchId": "batch_xxx",
 *       "state": "active",
 *       "progress": {...},
 *       "meta": {...}
 *     }
 *   ]
 * }
 */
router.get('/api/campaign/list', async (req, res) => {
  const { tenant_id, bpid } = req.query;

  if (!tenant_id || !bpid) {
    return res.status(400).json({
      success: false,
      error: 'tenant_id and bpid query parameters are required'
    });
  }

  try {
    const campaigns = await listActiveCampaigns(tenant_id, bpid);

    res.json({
      success: true,
      campaigns,
      count: campaigns.length
    });
  } catch (error) {
    console.error('[CampaignRoute] Error listing campaigns:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while listing campaigns'
    });
  }
});

/**
 * POST /api/campaign/resume
 * Resume a stopped campaign — re-sends unsent phones
 *
 * Request body:
 * {
 *   "batchId": "batch_xxx"
 * }
 */
router.post('/api/campaign/resume', async (req, res) => {
  const { batchId } = req.body;

  if (!batchId) {
    return res.status(400).json({
      success: false,
      error: 'batchId is required'
    });
  }

  try {
    console.log(`[CampaignRoute] Resume request for campaign ${batchId}`);

    const result = await resumeCampaign(batchId);

    if (!result.success) {
      return res.status(400).json({
        success: false,
        error: result.error
      });
    }

    const { unsentPhones, metadata, newTotal } = result;

    // Respond immediately
    res.json({
      success: true,
      message: `Campaign ${batchId} resumed with ${unsentPhones.length} unsent phones`,
      batchId,
      unsentCount: unsentPhones.length
    });

    // Process in background
    setImmediate(async () => {
      try {
        const bpid = metadata.bpid;
        const type = metadata.type || 'template';

        // Fetch tenant credentials
        let responseData = messageCache.get(bpid);
        if (!responseData) {
          const response = await axios.get(`${fastURL}/whatsapp_tenant`, {
            headers: { 'bpid': bpid },
            transformResponse: [(data) => {
              if (typeof data === 'string') {
                try {
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
          console.error(`[CampaignRoute] No WhatsApp data found for bpid ${bpid}`);
          return;
        }

        const { access_token, tenant_id, business_account_id: account_id } = whatsappData;

        console.log(`[CampaignRoute] Resuming ${type} campaign ${batchId} with ${unsentPhones.length} phones`);

        if (type === 'template') {
          await sendTemplate(
            { name: metadata.name, phone: unsentPhones },
            access_token, tenant_id, account_id, bpid, batchId, true
          );
        } else if (type === 'group') {
          await sendTemplateToGroup(
            { name: metadata.name, templateName: metadata.name, phone: unsentPhones },
            access_token, tenant_id, account_id, bpid, batchId, true
          );
        } else if (type === 'campaign') {
          // For campaigns, we re-use sendTemplate with unsent phones
          await sendTemplate(
            { name: metadata.name, phone: unsentPhones },
            access_token, tenant_id, account_id, bpid, batchId, true
          );
        }

        console.log(`[CampaignRoute] Resume background processing completed for ${batchId}`);
      } catch (error) {
        console.error(`[CampaignRoute] Error in resume background processing:`, error.message);
      }
    });
  } catch (error) {
    console.error('[CampaignRoute] Error resuming campaign:', error);
    res.status(500).json({
      success: false,
      error: 'Internal server error while resuming campaign'
    });
  }
});

export default router;
