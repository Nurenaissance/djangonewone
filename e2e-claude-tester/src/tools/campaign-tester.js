/**
 * Campaign API tester — validates campaign endpoints with expected error codes (read-only, no real messages).
 */

import config from '../config.js';
import { httpRequest } from './http-request.js';

export async function testCampaignApi({ action }) {
  const base = config.services.nodejs;

  switch (action) {
    case 'validate_status_endpoint': {
      // Should 400 without batchId param
      const noBatch = await httpRequest({ url: `${base}/api/campaign/status` });
      // Should 404 for nonexistent batch
      const fakeBatch = await httpRequest({ url: `${base}/api/campaign/status?batchId=nonexistent_12345` });
      return {
        action,
        no_param: { status: noBatch.status, expected: 400, pass: noBatch.status === 400 },
        nonexistent: { status: fakeBatch.status, expected: 404, pass: fakeBatch.status === 404 },
      };
    }

    case 'validate_list_endpoint': {
      // Should require tenant_id and bpid
      const noParams = await httpRequest({ url: `${base}/api/campaign/list` });
      const withParams = await httpRequest({
        url: `${base}/api/campaign/list?tenant_id=${config.whatsapp.tenantId}&bpid=${config.whatsapp.bpid}`,
      });
      return {
        action,
        no_params: { status: noParams.status, expected_error: true, pass: noParams.status >= 400 },
        with_params: { status: withParams.status, pass: withParams.status === 200 },
      };
    }

    case 'validate_stop_endpoint': {
      // POST without batchId should 400
      const result = await httpRequest({ url: `${base}/api/campaign/stop`, method: 'POST', body: {} });
      return {
        action,
        status: result.status,
        expected: 400,
        pass: result.status === 400,
        body: result.body,
      };
    }

    case 'validate_resume_endpoint': {
      // POST without batchId should 400
      const result = await httpRequest({ url: `${base}/api/campaign/resume`, method: 'POST', body: {} });
      return {
        action,
        status: result.status,
        expected: 400,
        pass: result.status === 400,
        body: result.body,
      };
    }

    default:
      return { error: `Unknown campaign action: ${action}. Valid: validate_status_endpoint, validate_list_endpoint, validate_stop_endpoint, validate_resume_endpoint` };
  }
}
