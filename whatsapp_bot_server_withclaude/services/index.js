/**
 * MCP Tools Service Index
 *
 * Central export point for all MCP tool-related services.
 */

// Main router - entry point for MCP tool evaluation
export { evaluateMCPTools, findKeywordMatch, hasMCPTools, getMCPStats, mcpMiddleware } from './mcpToolRouter.js';

// Cache service - Redis caching for tools and results
export { getCachedTools, invalidateToolCache, getCachedResult, cacheResult, isCacheHealthy, getCacheStats } from './mcpToolCache.js';

// Executor service - HTTP execution and response formatting
export { executeTool, interpolateUrl, renderTemplate, buildAuthHeaders, extractParameters } from './mcpToolExecutor.js';

// LLM service - OpenAI function calling for fallback
export { llmToolSelection, isLLMAvailable, matchIntent, selectAndExecuteTool } from './mcpLLMSelector.js';
