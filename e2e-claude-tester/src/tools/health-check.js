/**
 * Health check tool — verifies service availability.
 */

import config from '../config.js';
import { httpRequest } from './http-request.js';

const HEALTH_ENDPOINTS = {
  nodejs: { url: `${config.services.nodejs}/health`, expectField: 'status' },
  fastapi: { url: `${config.services.fastapi}/health`, expectValue: 'FastApi Code is healthy' },
  django: { url: `${config.services.django}/health/`, expectField: 'status' },
};

export async function checkHealth({ service }) {
  if (service === 'all') {
    const results = {};
    for (const [name, ep] of Object.entries(HEALTH_ENDPOINTS)) {
      results[name] = await checkOne(name, ep);
    }
    const allHealthy = Object.values(results).every((r) => r.healthy);
    return { allHealthy, services: results };
  }

  const ep = HEALTH_ENDPOINTS[service];
  if (!ep) {
    return { error: `Unknown service "${service}". Valid: ${Object.keys(HEALTH_ENDPOINTS).join(', ')}, all` };
  }
  return checkOne(service, ep);
}

async function checkOne(name, ep) {
  const res = await httpRequest({ url: ep.url, timeout: 15000 });
  if (!res.success) {
    return { service: name, healthy: false, status: res.status, error: res.error || 'Non-200 response', responseTime_ms: res.responseTime_ms };
  }

  let healthy = true;
  if (ep.expectValue && res.body) {
    const statusVal = typeof res.body === 'object' ? res.body.status : res.body;
    healthy = statusVal === ep.expectValue;
  } else if (ep.expectField && typeof res.body === 'object') {
    healthy = ep.expectField in res.body;
  }

  return { service: name, healthy, status: res.status, body: res.body, responseTime_ms: res.responseTime_ms };
}
