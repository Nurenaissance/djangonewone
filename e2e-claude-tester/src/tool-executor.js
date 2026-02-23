/**
 * Dispatches AI tool calls to their implementations.
 */

import { httpRequest } from './tools/http-request.js';
import { checkHealth } from './tools/health-check.js';
import { simulateWebhook, runWebhookFlow } from './tools/webhook-simulator.js';
import { testCampaignApi } from './tools/campaign-tester.js';
import { testAuth } from './tools/auth-tester.js';
import { reportTestResult } from './tools/report-result.js';

const handlers = {
  http_request: httpRequest,
  check_health: checkHealth,
  simulate_webhook: simulateWebhook,
  run_webhook_flow: runWebhookFlow,
  test_campaign_api: testCampaignApi,
  test_auth: testAuth,
  report_test_result: reportTestResult,
};

/**
 * Execute a tool call from the AI, wrapping with error handling and timing.
 */
export async function executeTool(name, argsJson) {
  const handler = handlers[name];
  if (!handler) {
    return JSON.stringify({ error: `Unknown tool: ${name}` });
  }

  let args;
  try {
    args = typeof argsJson === 'string' ? JSON.parse(argsJson) : argsJson;
  } catch {
    return JSON.stringify({ error: `Invalid JSON arguments for tool ${name}` });
  }

  const start = Date.now();
  try {
    const result = await handler(args);
    const elapsed = Date.now() - start;
    return JSON.stringify({ ...result, _tool_duration_ms: elapsed });
  } catch (err) {
    return JSON.stringify({ error: err.message, _tool_duration_ms: Date.now() - start });
  }
}
