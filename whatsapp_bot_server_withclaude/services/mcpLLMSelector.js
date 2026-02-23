/**
 * MCP LLM Selector Service
 *
 * Uses OpenAI function calling to intelligently select the appropriate
 * tool when keyword matching fails. This is the fallback path for
 * complex or ambiguous user intents.
 *
 * NOTE: OpenAI is loaded dynamically to prevent crashes if the package is not installed.
 */

import { executeTool } from './mcpToolExecutor.js';
import dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// OPENAI CLIENT (OPTIONAL - DYNAMICALLY LOADED)
// ============================================================================

let openai = null;
let OpenAI = null;
let openaiLoadAttempted = false;

async function getOpenAIClient() {
  // Only attempt to load OpenAI once
  if (!openaiLoadAttempted) {
    openaiLoadAttempted = true;
    try {
      const openaiModule = await import('openai');
      OpenAI = openaiModule.default;
      console.log('✅ [MCP LLM] OpenAI module loaded successfully');
    } catch (err) {
      console.warn('⚠️ [MCP LLM] OpenAI package not installed - LLM fallback disabled');
      return null;
    }
  }

  if (!OpenAI) {
    return null;
  }

  if (!openai) {
    const apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      console.warn('⚠️ [MCP LLM] OpenAI API key not configured');
      return null;
    }
    openai = new OpenAI({ apiKey });
  }
  return openai;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const LLM_MODEL = process.env.MCP_LLM_MODEL || 'gpt-4o-mini';
const LLM_TIMEOUT = parseInt(process.env.MCP_LLM_TIMEOUT || '10000', 10);
const MAX_HISTORY_MESSAGES = 5;

// ============================================================================
// TOOL CONVERSION
// ============================================================================

/**
 * Convert MCP tool definitions to OpenAI function format.
 * @param {Array} tools - Array of MCP tool definitions
 * @returns {Array} OpenAI function definitions
 */
function convertToolsToFunctions(tools) {
  return tools.map(tool => ({
    type: 'function',
    function: {
      name: tool.name,
      description: tool.description,
      parameters: tool.parameters || {
        type: 'object',
        properties: {},
        required: []
      }
    }
  }));
}

/**
 * Build system prompt for tool selection.
 * @param {Array} tools - Available tools
 * @returns {string} System prompt
 */
function buildSystemPrompt(tools) {
  const toolDescriptions = tools.map(t =>
    `- ${t.name}: ${t.description}`
  ).join('\n');

  return `You are a helpful customer support assistant. Your job is to understand customer requests and select the most appropriate tool to help them.

Available tools:
${toolDescriptions}

Guidelines:
- Only select a tool if the user's request clearly relates to one of the available tools
- Extract any relevant parameters from the user's message
- If you're uncertain about which tool to use, or if no tool seems appropriate, do not call any function
- Be conservative - only call tools when you're confident they match the user's intent`;
}

// ============================================================================
// LLM TOOL SELECTION
// ============================================================================

/**
 * Use LLM to select appropriate tool and extract parameters.
 * @param {string} messageText - User's message
 * @param {Array} tools - Available tools
 * @param {Array} conversationHistory - Recent conversation for context
 * @param {Object} userSession - User session data
 * @returns {Promise<Object>} Tool execution result or { toolExecuted: false }
 */
export async function llmToolSelection(messageText, tools, conversationHistory, userSession) {
  const client = await getOpenAIClient();

  if (!client) {
    console.warn('[MCP LLM] OpenAI client not available');
    return { toolExecuted: false, reason: 'llm_unavailable' };
  }

  if (!tools || tools.length === 0) {
    return { toolExecuted: false, reason: 'no_tools' };
  }

  try {
    console.log(`🤖 [MCP LLM] Analyzing message: "${messageText.substring(0, 50)}..."`);

    // Build messages array
    const messages = [
      {
        role: 'system',
        content: buildSystemPrompt(tools)
      }
    ];

    // Add recent conversation history for context
    if (conversationHistory && conversationHistory.length > 0) {
      const recentHistory = conversationHistory.slice(-MAX_HISTORY_MESSAGES);
      for (const msg of recentHistory) {
        messages.push({
          role: msg.sender === 'user' ? 'user' : 'assistant',
          content: msg.text || msg.message_text || ''
        });
      }
    }

    // Add current message
    messages.push({
      role: 'user',
      content: messageText
    });

    // Convert tools to OpenAI function format
    const functions = convertToolsToFunctions(tools);

    // Call OpenAI with function calling
    const response = await Promise.race([
      client.chat.completions.create({
        model: LLM_MODEL,
        messages,
        tools: functions,
        tool_choice: 'auto', // Let the model decide
        temperature: 0.1, // Low temperature for consistent tool selection
        max_tokens: 500
      }),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('LLM timeout')), LLM_TIMEOUT)
      )
    ]);

    const choice = response.choices[0];

    // Check if model decided to call a function
    if (choice.message.tool_calls && choice.message.tool_calls.length > 0) {
      const toolCall = choice.message.tool_calls[0];
      const functionName = toolCall.function.name;
      const functionArgs = JSON.parse(toolCall.function.arguments || '{}');

      console.log(`🎯 [MCP LLM] Selected tool: ${functionName}`);
      console.log(`📝 [MCP LLM] Extracted params:`, functionArgs);

      // Find the matching tool
      const selectedTool = tools.find(t => t.name === functionName);

      if (selectedTool) {
        // Execute the tool
        return await executeTool(
          selectedTool,
          functionArgs,
          userSession,
          messageText,
          'llm'
        );
      } else {
        console.warn(`[MCP LLM] Tool ${functionName} not found in available tools`);
        return { toolExecuted: false, reason: 'tool_not_found' };
      }
    }

    // Model decided not to call any function
    console.log('[MCP LLM] No tool selected by LLM');
    return {
      toolExecuted: false,
      reason: 'no_match',
      llmResponse: choice.message.content
    };

  } catch (error) {
    console.error('❌ [MCP LLM] Error in tool selection:', error.message);
    return {
      toolExecuted: false,
      reason: 'error',
      error: error.message
    };
  }
}

/**
 * Check if LLM fallback is available and configured.
 * @returns {boolean}
 */
export function isLLMAvailable() {
  return !!process.env.OPENAI_API_KEY;
}

/**
 * Estimate the cost of an LLM call for monitoring.
 * @param {number} inputTokens - Estimated input tokens
 * @param {number} outputTokens - Estimated output tokens
 * @returns {number} Estimated cost in USD
 */
export function estimateLLMCost(inputTokens = 500, outputTokens = 100) {
  // gpt-4o-mini pricing (as of 2024)
  const inputCostPer1K = 0.00015;
  const outputCostPer1K = 0.0006;

  return (inputTokens / 1000 * inputCostPer1K) + (outputTokens / 1000 * outputCostPer1K);
}

// ============================================================================
// INTENT MATCHING (Alternative to full LLM call)
// ============================================================================

/**
 * Check if message matches any tool's trigger intents using simple NLP.
 * This is faster than a full LLM call but less accurate.
 * @param {string} messageText - User message
 * @param {Array} tools - Available tools
 * @returns {Object|null} Matched tool or null
 */
export function matchIntent(messageText, tools) {
  const lowerMessage = messageText.toLowerCase();

  for (const tool of tools) {
    if (!tool.trigger_intents || tool.trigger_intents.length === 0) {
      continue;
    }

    for (const intent of tool.trigger_intents) {
      // Simple intent matching - check if intent words appear in message
      const intentWords = intent.toLowerCase().split(/[_\s]+/);
      const matchCount = intentWords.filter(word =>
        word.length > 2 && lowerMessage.includes(word)
      ).length;

      // If most of the intent words match, consider it a match
      if (matchCount >= Math.ceil(intentWords.length * 0.6)) {
        console.log(`🎯 [MCP LLM] Intent match: "${intent}" for tool ${tool.name}`);
        return tool;
      }
    }
  }

  return null;
}

/**
 * Combined tool selection: intent matching first, then LLM fallback.
 * @param {string} messageText - User message
 * @param {Array} tools - Available tools
 * @param {Array} conversationHistory - Conversation history
 * @param {Object} userSession - User session
 * @returns {Promise<Object>} Execution result
 */
export async function selectAndExecuteTool(messageText, tools, conversationHistory, userSession) {
  // First, try intent matching (fast path)
  const intentMatch = matchIntent(messageText, tools);
  if (intentMatch) {
    const params = {}; // Would need parameter extraction
    return await executeTool(intentMatch, params, userSession, messageText, 'intent');
  }

  // Fall back to LLM (slow path)
  return await llmToolSelection(messageText, tools, conversationHistory, userSession);
}

export default {
  llmToolSelection,
  isLLMAvailable,
  matchIntent,
  selectAndExecuteTool,
  estimateLLMCost
};
