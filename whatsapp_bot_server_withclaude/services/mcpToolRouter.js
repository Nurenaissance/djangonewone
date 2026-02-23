/**
 * MCP Tool Router Service
 *
 * Main entry point for MCP tool processing. Implements a speed-first approach:
 * 1. Keyword matching (< 5ms) - instant for obvious intents
 * 2. Intent matching (< 10ms) - simple NLP-based matching
 * 3. LLM fallback (500-1500ms) - for complex/ambiguous cases
 */

import { getCachedTools } from './mcpToolCache.js';
import { executeTool, extractParameters } from './mcpToolExecutor.js';
import { llmToolSelection, isLLMAvailable, matchIntent } from './mcpLLMSelector.js';
import dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// CONFIGURATION
// ============================================================================

// Enable/disable LLM fallback globally
const ENABLE_LLM_FALLBACK = process.env.MCP_ENABLE_LLM_FALLBACK !== 'false';

// Minimum message length to consider for MCP processing
const MIN_MESSAGE_LENGTH = 2;

// ============================================================================
// KEYWORD MATCHING (FAST PATH)
// ============================================================================

/**
 * Find tool matching by keyword - O(n*k) where n=tools, k=keywords.
 * This is the fastest path and should match most common cases.
 * @param {string} messageText - User message
 * @param {Array} tools - Available tools sorted by priority
 * @returns {Object|null} Matched tool or null
 */
export function findKeywordMatch(messageText, tools) {
  if (!messageText || !tools || tools.length === 0) {
    return null;
  }

  const lowerMessage = messageText.toLowerCase();

  // Tools should already be sorted by priority (highest first)
  for (const tool of tools) {
    if (!tool.trigger_keywords || tool.trigger_keywords.length === 0) {
      continue;
    }

    // Check if any keyword matches
    for (const keyword of tool.trigger_keywords) {
      if (keyword && lowerMessage.includes(keyword.toLowerCase())) {
        console.log(`⚡ [MCP Router] Keyword match: "${keyword}" -> tool: ${tool.name}`);
        return tool;
      }
    }
  }

  return null;
}

// ============================================================================
// MAIN EVALUATION FUNCTION
// ============================================================================

/**
 * Main entry point for MCP tool evaluation.
 * Called from userWebhook.js for every incoming message.
 *
 * @param {Object} userSession - User session containing tenant info
 * @param {string} messageText - The user's message text
 * @param {Array} conversationHistory - Recent conversation for LLM context
 * @returns {Promise<Object>} Result object with toolExecuted flag
 *
 * Result structure:
 * {
 *   toolExecuted: boolean,      // Whether a tool was executed
 *   toolName: string,           // Name of executed tool (if any)
 *   message: string,            // Response message to send to user
 *   data: Object,               // Raw API response data
 *   error: boolean,             // Whether execution failed
 *   errorDetails: string,       // Error message (if any)
 *   fromCache: boolean,         // Whether result was from cache
 *   triggerType: string         // 'keyword', 'intent', or 'llm'
 * }
 */
export async function evaluateMCPTools(userSession, messageText, conversationHistory = []) {
  const startTime = Date.now();

  // Quick exit conditions
  if (!userSession || !messageText) {
    return { toolExecuted: false, reason: 'invalid_input' };
  }

  // Skip very short messages
  if (messageText.trim().length < MIN_MESSAGE_LENGTH) {
    return { toolExecuted: false, reason: 'message_too_short' };
  }

  // Check if MCP tools are explicitly disabled for this session
  if (userSession.mcpToolsEnabled === false) {
    return { toolExecuted: false, reason: 'disabled_for_session' };
  }

  const tenantId = userSession.tenant;
  if (!tenantId) {
    return { toolExecuted: false, reason: 'no_tenant' };
  }

  try {
    // STEP 1: Get cached tools for this tenant
    const tools = await getCachedTools(tenantId);

    if (!tools || tools.length === 0) {
      // No tools configured - this is normal for tenants without MCP
      return { toolExecuted: false, reason: 'no_tools_configured' };
    }

    console.log(`🔧 [MCP Router] Evaluating ${tools.length} tools for tenant ${tenantId}`);

    // STEP 2: FAST PATH - Keyword matching (< 5ms)
    const keywordMatch = findKeywordMatch(messageText, tools);

    if (keywordMatch) {
      // Extract parameters from message
      const params = extractParameters(messageText, keywordMatch);

      // Execute tool
      const result = await executeTool(
        keywordMatch,
        params,
        userSession,
        messageText,
        'keyword'
      );

      result.triggerType = 'keyword';
      result.evaluationTime = Date.now() - startTime;
      console.log(`✅ [MCP Router] Keyword match completed in ${result.evaluationTime}ms`);

      return result;
    }

    // STEP 3: MEDIUM PATH - Intent matching (< 10ms)
    const intentMatch = matchIntent(messageText, tools);

    if (intentMatch) {
      const params = extractParameters(messageText, intentMatch);

      const result = await executeTool(
        intentMatch,
        params,
        userSession,
        messageText,
        'intent'
      );

      result.triggerType = 'intent';
      result.evaluationTime = Date.now() - startTime;
      console.log(`✅ [MCP Router] Intent match completed in ${result.evaluationTime}ms`);

      return result;
    }

    // STEP 4: SLOW PATH - LLM fallback (only if enabled)
    if (ENABLE_LLM_FALLBACK && isLLMAvailable() && userSession.mcpUseLLMFallback !== false) {
      console.log(`🤖 [MCP Router] No keyword/intent match, trying LLM fallback...`);

      const result = await llmToolSelection(
        messageText,
        tools,
        conversationHistory,
        userSession
      );

      if (result.toolExecuted) {
        result.triggerType = 'llm';
        result.evaluationTime = Date.now() - startTime;
        console.log(`✅ [MCP Router] LLM selection completed in ${result.evaluationTime}ms`);
        return result;
      }
    }

    // No tool matched
    const evaluationTime = Date.now() - startTime;
    console.log(`ℹ️ [MCP Router] No tool matched (evaluated in ${evaluationTime}ms)`);

    return {
      toolExecuted: false,
      reason: 'no_match',
      evaluationTime
    };

  } catch (error) {
    console.error('❌ [MCP Router] Error evaluating tools:', error);

    return {
      toolExecuted: false,
      reason: 'error',
      error: error.message,
      evaluationTime: Date.now() - startTime
    };
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Get recent conversation history for LLM context.
 * @param {Object} userSession - User session
 * @param {number} limit - Max messages to return
 * @returns {Promise<Array>} Recent messages
 */
export async function getRecentConversation(userSession, limit = 5) {
  // This would typically fetch from your conversation storage
  // For now, return empty array - the webhook can pass conversation history
  return userSession.recentMessages || [];
}

/**
 * Check if MCP tools are available for a tenant.
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<boolean>}
 */
export async function hasMCPTools(tenantId) {
  try {
    const tools = await getCachedTools(tenantId);
    return tools && tools.length > 0;
  } catch {
    return false;
  }
}

/**
 * Get tool statistics for monitoring.
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<Object>}
 */
export async function getMCPStats(tenantId) {
  const tools = await getCachedTools(tenantId);

  return {
    tenantId,
    toolCount: tools.length,
    tools: tools.map(t => ({
      name: t.name,
      keywordCount: t.trigger_keywords?.length || 0,
      intentCount: t.trigger_intents?.length || 0,
      priority: t.priority
    })),
    llmEnabled: ENABLE_LLM_FALLBACK && isLLMAvailable()
  };
}

// ============================================================================
// EXPRESS MIDDLEWARE (Optional)
// ============================================================================

/**
 * Express middleware for MCP tool processing.
 * Can be used to add MCP processing to any route.
 */
export function mcpMiddleware(options = {}) {
  return async (req, res, next) => {
    const { messageText, userSession, conversationHistory } = req.body;

    if (!messageText || !userSession) {
      return next();
    }

    try {
      const mcpResult = await evaluateMCPTools(
        userSession,
        messageText,
        conversationHistory || []
      );

      // Attach result to request for downstream handlers
      req.mcpResult = mcpResult;

      // If tool was executed and has a message, optionally short-circuit
      if (options.shortCircuit && mcpResult.toolExecuted && mcpResult.message) {
        return res.json({
          success: true,
          mcpHandled: true,
          message: mcpResult.message,
          toolName: mcpResult.toolName
        });
      }

      next();
    } catch (error) {
      console.error('[MCP Middleware] Error:', error);
      req.mcpResult = { toolExecuted: false, error: error.message };
      next();
    }
  };
}

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  evaluateMCPTools,
  findKeywordMatch,
  getRecentConversation,
  hasMCPTools,
  getMCPStats,
  mcpMiddleware
};
