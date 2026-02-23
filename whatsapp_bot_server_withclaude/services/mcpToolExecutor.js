/**
 * MCP Tool Executor Service
 *
 * Executes MCP tools by calling client APIs with retry logic,
 * timeout handling, and response formatting.
 */

import axios from 'axios';
import https from 'https';
import { getCachedResult, cacheResult } from './mcpToolCache.js';
import dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// AXIOS CONFIGURATION
// ============================================================================

// Create axios instance with connection pooling
const httpClient = axios.create({
  timeout: 30000, // Default timeout, will be overridden per-tool
  httpsAgent: new https.Agent({
    keepAlive: true,
    maxSockets: 50,
    maxFreeSockets: 10,
    timeout: 60000,
    freeSocketTimeout: 30000
  }),
  headers: {
    'User-Agent': 'WhatsApp-MCP-Bot/1.0'
  }
});

// FastAPI URL for logging executions
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const FASTAPI_SERVICE_KEY = process.env.FASTAPI_SERVICE_KEY || process.env.NODEJS_SERVICE_KEY;

// ============================================================================
// URL & TEMPLATE HELPERS
// ============================================================================

/**
 * Interpolate URL template with parameter values.
 * Replaces ${var} placeholders with actual values.
 * @param {string} url - URL template
 * @param {Object} params - Parameter values
 * @returns {string} Interpolated URL
 */
export function interpolateUrl(url, params) {
  if (!url || !params) return url;

  let result = url;
  for (const [key, value] of Object.entries(params)) {
    result = result.replace(new RegExp(`\\$\\{${key}\\}`, 'g'), encodeURIComponent(String(value)));
  }
  return result;
}

/**
 * Render a Jinja2-style template with {{var}} placeholders.
 * @param {string} template - Template string
 * @param {Object} data - Data for interpolation
 * @returns {string} Rendered string
 */
export function renderTemplate(template, data) {
  if (!template) {
    return data ? JSON.stringify(data) : '';
  }

  let result = template;
  const flatData = flattenObject(data);

  for (const [key, value] of Object.entries(flatData)) {
    const placeholder = new RegExp(`\\{\\{\\s*${escapeRegex(key)}\\s*\\}\\}`, 'g');
    result = result.replace(placeholder, value != null ? String(value) : '');
  }

  // Clean up any remaining placeholders
  result = result.replace(/\{\{[^}]+\}\}/g, '');

  return result.trim();
}

/**
 * Flatten nested object for template rendering.
 * @param {Object} obj - Object to flatten
 * @param {string} prefix - Key prefix
 * @returns {Object} Flattened object
 */
function flattenObject(obj, prefix = '') {
  if (!obj || typeof obj !== 'object') return {};

  const result = {};

  for (const [key, value] of Object.entries(obj)) {
    const newKey = prefix ? `${prefix}.${key}` : key;

    if (value && typeof value === 'object' && !Array.isArray(value)) {
      Object.assign(result, flattenObject(value, newKey));
    }

    // Add both nested and direct keys
    result[newKey] = value;
    result[key] = value;
  }

  return result;
}

/**
 * Escape special regex characters in a string.
 */
function escapeRegex(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// ============================================================================
// AUTHENTICATION HELPERS
// ============================================================================

/**
 * Build authentication headers based on tool configuration.
 * @param {Object} tool - Tool definition
 * @returns {Object} Headers object
 */
export function buildAuthHeaders(tool) {
  const headers = { ...(tool.headers || {}) };

  if (!tool.auth_type || tool.auth_type === 'none') {
    return headers;
  }

  const config = tool.auth_config || {};

  switch (tool.auth_type) {
    case 'bearer':
      if (config.token) {
        headers['Authorization'] = `Bearer ${config.token}`;
      }
      break;

    case 'api_key':
      const headerName = config.header || 'X-API-Key';
      if (config.key) {
        headers[headerName] = config.key;
      }
      break;

    case 'basic':
      if (config.username && config.password) {
        const credentials = Buffer.from(`${config.username}:${config.password}`).toString('base64');
        headers['Authorization'] = `Basic ${credentials}`;
      }
      break;
  }

  return headers;
}

// ============================================================================
// TOOL EXECUTION
// ============================================================================

/**
 * Execute a tool by calling its API endpoint.
 * @param {Object} tool - Tool definition
 * @param {Object} params - Parameters extracted from user message
 * @param {Object} userSession - User session data
 * @param {string} messageText - Original user message
 * @param {string} triggerType - 'keyword' or 'llm'
 * @returns {Promise<Object>} Execution result
 */
export async function executeTool(tool, params, userSession, messageText, triggerType = 'keyword') {
  const startTime = Date.now();

  // Check cache first
  const cachedResult = await getCachedResult(tool, params);
  if (cachedResult) {
    // Log cached execution
    logExecution(tool, params, cachedResult, userSession, messageText, triggerType, true, Date.now() - startTime);

    return {
      toolExecuted: true,
      toolName: tool.name,
      data: cachedResult.data,
      message: cachedResult.message,
      fromCache: true
    };
  }

  let retries = 0;
  const maxRetries = tool.retry_count || 1;

  while (retries < maxRetries) {
    try {
      const result = await executeToolRequest(tool, params);
      const duration = Date.now() - startTime;

      // Format response message
      const responseMessage = renderTemplate(tool.response_template, { ...params, ...result.data });

      const executionResult = {
        toolExecuted: true,
        toolName: tool.name,
        data: result.data,
        message: responseMessage || JSON.stringify(result.data),
        fromCache: false
      };

      // Cache successful result
      if (result.success) {
        await cacheResult(tool, params, {
          data: result.data,
          message: responseMessage
        });
      }

      // Log execution
      logExecution(tool, params, executionResult, userSession, messageText, triggerType, false, duration, result.url);

      return executionResult;

    } catch (error) {
      retries++;
      console.error(`❌ [MCP Executor] Tool ${tool.name} attempt ${retries}/${maxRetries} failed:`, error.message);

      if (retries >= maxRetries) {
        const duration = Date.now() - startTime;
        const errorResult = {
          toolExecuted: true,
          toolName: tool.name,
          error: true,
          message: tool.error_template || "Sorry, I couldn't complete that action. Please try again.",
          errorDetails: error.message
        };

        // Log failed execution
        logExecution(tool, params, errorResult, userSession, messageText, triggerType, false, duration, null, error.message);

        return errorResult;
      }

      // Wait before retry (exponential backoff)
      await new Promise(resolve => setTimeout(resolve, Math.pow(2, retries) * 100));
    }
  }
}

/**
 * Execute the actual HTTP request for a tool.
 * @param {Object} tool - Tool definition
 * @param {Object} params - Request parameters
 * @returns {Promise<Object>} Request result
 */
async function executeToolRequest(tool, params) {
  const url = interpolateUrl(tool.endpoint_url, params);
  const headers = buildAuthHeaders(tool);
  const timeout = (tool.timeout_seconds || 10) * 1000;

  const config = {
    method: tool.http_method.toUpperCase(),
    url,
    headers,
    timeout
  };

  // Handle request body/params based on method
  if (config.method === 'GET') {
    // For GET, filter params to only include those not in URL template
    const urlParams = {};
    for (const [key, value] of Object.entries(params)) {
      if (!tool.endpoint_url.includes(`\${${key}}`)) {
        urlParams[key] = value;
      }
    }
    if (Object.keys(urlParams).length > 0) {
      config.params = urlParams;
    }
  } else {
    // For POST/PUT/PATCH, send params as body
    if (tool.request_body_template) {
      try {
        config.data = JSON.parse(renderTemplate(tool.request_body_template, params));
      } catch {
        config.data = params;
      }
    } else {
      config.data = params;
    }
  }

  console.log(`🔧 [MCP Executor] Calling ${config.method} ${url}`);

  const response = await httpClient(config);

  return {
    success: response.status >= 200 && response.status < 300,
    status: response.status,
    data: response.data,
    url
  };
}

// ============================================================================
// EXECUTION LOGGING
// ============================================================================

/**
 * Log tool execution to FastAPI for analytics.
 * @param {Object} tool - Tool definition
 * @param {Object} params - Request parameters
 * @param {Object} result - Execution result
 * @param {Object} userSession - User session
 * @param {string} messageText - Original message
 * @param {string} triggerType - Trigger type
 * @param {boolean} fromCache - Whether result was from cache
 * @param {number} duration - Execution duration in ms
 * @param {string} requestUrl - Final request URL
 * @param {string} errorMessage - Error message if any
 */
async function logExecution(tool, params, result, userSession, messageText, triggerType, fromCache, duration, requestUrl = null, errorMessage = null) {
  // Fire and forget - don't block on logging
  try {
    fetch(`${FASTAPI_URL}/mcp-tools/executions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Service-Key': FASTAPI_SERVICE_KEY
      },
      body: JSON.stringify({
        tool_id: tool.id,
        tenant_id: userSession?.tenant,
        contact_phone: userSession?.userPhoneNumber,
        message_text: messageText,
        trigger_type: triggerType,
        request_params: params,
        request_url: requestUrl,
        response_data: result.data,
        response_message: result.message,
        status: result.error ? 'failed' : 'success',
        error_message: errorMessage,
        duration_ms: duration,
        from_cache: fromCache
      })
    }).catch(err => {
      console.warn('[MCP Executor] Failed to log execution:', err.message);
    });
  } catch (err) {
    // Silently ignore logging errors
  }
}

// ============================================================================
// PARAMETER EXTRACTION
// ============================================================================

/**
 * Extract parameters from user message based on tool's parameter schema.
 * Simple pattern matching - for complex extraction, use LLM.
 * @param {string} message - User message
 * @param {Object} tool - Tool definition
 * @returns {Object} Extracted parameters
 */
export function extractParameters(message, tool) {
  const params = {};

  if (!tool.parameters || !tool.parameters.properties) {
    return params;
  }

  const properties = tool.parameters.properties;

  for (const [key, schema] of Object.entries(properties)) {
    // Try to extract based on type and common patterns
    const extracted = extractValue(message, key, schema);
    if (extracted !== null) {
      params[key] = extracted;
    }
  }

  return params;
}

/**
 * Extract a single parameter value from message.
 * @param {string} message - User message
 * @param {string} key - Parameter key
 * @param {Object} schema - Parameter schema
 * @returns {*} Extracted value or null
 */
function extractValue(message, key, schema) {
  const lowerMsg = message.toLowerCase();

  // Common patterns for different parameter types
  const patterns = {
    // Order ID patterns
    order_id: [
      /order\s*(?:#|id|number)?[:\s]*([A-Z0-9-]+)/i,
      /(?:#|ORD|order)[:\s]*([A-Z0-9-]+)/i,
      /([A-Z]{2,3}[0-9]{5,})/i
    ],
    // Phone patterns
    phone: [
      /(?:phone|mobile|contact)[:\s]*([+]?[0-9\s-]{10,})/i,
      /([+]?[0-9]{10,15})/
    ],
    // Email patterns
    email: [
      /([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/
    ],
    // Date patterns
    date: [
      /(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})/,
      /(today|tomorrow|next\s+\w+)/i
    ],
    // Time patterns
    time: [
      /(\d{1,2}:\d{2}\s*(?:am|pm)?)/i,
      /(\d{1,2}\s*(?:am|pm))/i
    ],
    // Generic ID
    id: [
      /(?:id|#)[:\s]*([A-Z0-9-]+)/i,
      /([A-Z0-9]{6,})/
    ]
  };

  // Try specific patterns for this key
  const keyPatterns = patterns[key.toLowerCase()] || patterns.id;

  for (const pattern of keyPatterns) {
    const match = message.match(pattern);
    if (match && match[1]) {
      return match[1].trim();
    }
  }

  // Try enum matching if schema has enum values
  if (schema.enum) {
    for (const enumValue of schema.enum) {
      if (lowerMsg.includes(enumValue.toLowerCase())) {
        return enumValue;
      }
    }
  }

  return null;
}

export default {
  executeTool,
  interpolateUrl,
  renderTemplate,
  buildAuthHeaders,
  extractParameters
};
