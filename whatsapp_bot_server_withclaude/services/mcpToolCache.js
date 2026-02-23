/**
 * MCP Tool Cache Service
 *
 * Handles Redis caching for MCP tool definitions and execution results.
 * Provides fast access to tool configurations with automatic cache invalidation.
 */

import Redis from 'ioredis';
import crypto from 'crypto';
import dotenv from 'dotenv';

dotenv.config();

// ============================================================================
// REDIS CONNECTION
// ============================================================================

let redis = null;

// Initialize Redis connection
function initializeRedis() {
  if (redis) return redis;

  const redisConfig = {
    host: process.env.REDIS_HOST || 'localhost',
    port: process.env.REDIS_PORT || 6379,
    retryStrategy: (times) => {
      const delay = Math.min(times * 50, 2000);
      return delay;
    },
    maxRetriesPerRequest: 3,
    enableReadyCheck: true,
    lazyConnect: true
  };

  if (process.env.REDIS_PASSWORD) {
    redisConfig.password = process.env.REDIS_PASSWORD;
  }

  redis = new Redis(redisConfig);

  redis.on('connect', () => {
    console.log('✅ [MCP Cache] Redis connected');
  });

  redis.on('error', (err) => {
    console.error('❌ [MCP Cache] Redis error:', err.message);
  });

  redis.on('ready', () => {
    console.log('✅ [MCP Cache] Redis ready');
  });

  return redis;
}

// Initialize on module load
initializeRedis();

// ============================================================================
// CONSTANTS
// ============================================================================

const TOOL_CACHE_TTL = 300; // 5 minutes for tool definitions
const TOOL_CACHE_PREFIX = 'mcp_tools:';
const RESULT_CACHE_PREFIX = 'mcp_result:';
const VERSION_CACHE_PREFIX = 'mcp_version:';

// FastAPI URL for fetching tools
const FASTAPI_URL = process.env.FASTAPI_URL || 'http://localhost:8000';
const FASTAPI_SERVICE_KEY = process.env.FASTAPI_SERVICE_KEY || process.env.NODEJS_SERVICE_KEY;

// ============================================================================
// TOOL DEFINITION CACHING
// ============================================================================

/**
 * Get cached tools for a tenant, fetching from FastAPI if cache miss.
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<Array>} Array of tool definitions
 */
export async function getCachedTools(tenantId) {
  if (!tenantId) {
    console.warn('[MCP Cache] No tenant ID provided');
    return [];
  }

  const cacheKey = `${TOOL_CACHE_PREFIX}${tenantId}`;

  try {
    // Try cache first
    if (redis && redis.status === 'ready') {
      const cached = await redis.get(cacheKey);
      if (cached) {
        console.log(`📦 [MCP Cache] Hit: tools for tenant ${tenantId}`);
        return JSON.parse(cached);
      }
    }

    console.log(`🔍 [MCP Cache] Miss: fetching tools for tenant ${tenantId}`);

    // Fetch from FastAPI
    const tools = await fetchToolsFromAPI(tenantId);

    // Store in cache
    if (redis && redis.status === 'ready' && tools.length > 0) {
      await redis.setex(cacheKey, TOOL_CACHE_TTL, JSON.stringify(tools));
      console.log(`💾 [MCP Cache] Stored ${tools.length} tools for tenant ${tenantId}`);
    }

    return tools;

  } catch (error) {
    console.error(`❌ [MCP Cache] Error getting tools for ${tenantId}:`, error.message);
    return [];
  }
}

/**
 * Fetch tools from FastAPI endpoint.
 * @param {string} tenantId - Tenant ID
 * @returns {Promise<Array>} Array of tool definitions
 */
async function fetchToolsFromAPI(tenantId) {
  try {
    const response = await fetch(`${FASTAPI_URL}/mcp-tools/tenant/${tenantId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-Service-Key': FASTAPI_SERVICE_KEY,
        'X-Tenant-Id': tenantId
      },
      timeout: 5000
    });

    if (!response.ok) {
      if (response.status === 404) {
        // No tools configured for this tenant - this is normal
        return [];
      }
      throw new Error(`FastAPI returned ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();

    // Store version for cache invalidation
    if (data.cache_version && redis && redis.status === 'ready') {
      await redis.set(`${VERSION_CACHE_PREFIX}${tenantId}`, data.cache_version);
    }

    return data.tools || [];

  } catch (error) {
    console.error(`❌ [MCP Cache] Error fetching tools from API:`, error.message);
    return [];
  }
}

/**
 * Invalidate tool cache for a tenant (called when tools are updated).
 * @param {string} tenantId - Tenant ID
 */
export async function invalidateToolCache(tenantId) {
  if (!redis || redis.status !== 'ready') return;

  try {
    const cacheKey = `${TOOL_CACHE_PREFIX}${tenantId}`;
    await redis.del(cacheKey);
    console.log(`🗑️ [MCP Cache] Invalidated tools cache for tenant ${tenantId}`);
  } catch (error) {
    console.error(`❌ [MCP Cache] Error invalidating cache:`, error.message);
  }
}

// ============================================================================
// RESULT CACHING
// ============================================================================

/**
 * Generate cache key for a tool result.
 * @param {Object} tool - Tool definition
 * @param {Object} params - Request parameters
 * @returns {string} Cache key
 */
function generateResultCacheKey(tool, params) {
  const paramsHash = crypto
    .createHash('md5')
    .update(JSON.stringify(params || {}))
    .digest('hex')
    .substring(0, 12);

  return `${RESULT_CACHE_PREFIX}${tool.id}:${paramsHash}`;
}

/**
 * Get cached result for a tool execution.
 * @param {Object} tool - Tool definition
 * @param {Object} params - Request parameters
 * @returns {Promise<Object|null>} Cached result or null
 */
export async function getCachedResult(tool, params) {
  // Skip if no cache TTL configured
  if (!tool.cache_ttl_seconds || tool.cache_ttl_seconds <= 0) {
    return null;
  }

  if (!redis || redis.status !== 'ready') {
    return null;
  }

  try {
    const cacheKey = generateResultCacheKey(tool, params);
    const cached = await redis.get(cacheKey);

    if (cached) {
      console.log(`📦 [MCP Cache] Result hit for tool ${tool.name}`);
      return JSON.parse(cached);
    }

    return null;
  } catch (error) {
    console.error(`❌ [MCP Cache] Error getting cached result:`, error.message);
    return null;
  }
}

/**
 * Cache a tool execution result.
 * @param {Object} tool - Tool definition
 * @param {Object} params - Request parameters
 * @param {Object} result - Execution result to cache
 */
export async function cacheResult(tool, params, result) {
  // Skip if no cache TTL configured
  if (!tool.cache_ttl_seconds || tool.cache_ttl_seconds <= 0) {
    return;
  }

  if (!redis || redis.status !== 'ready') {
    return;
  }

  try {
    const cacheKey = generateResultCacheKey(tool, params);
    await redis.setex(cacheKey, tool.cache_ttl_seconds, JSON.stringify(result));
    console.log(`💾 [MCP Cache] Cached result for tool ${tool.name} (TTL: ${tool.cache_ttl_seconds}s)`);
  } catch (error) {
    console.error(`❌ [MCP Cache] Error caching result:`, error.message);
  }
}

/**
 * Clear all cached results for a specific tool.
 * @param {string} toolId - Tool ID
 */
export async function clearToolResults(toolId) {
  if (!redis || redis.status !== 'ready') return;

  try {
    const pattern = `${RESULT_CACHE_PREFIX}${toolId}:*`;
    const keys = await redis.keys(pattern);

    if (keys.length > 0) {
      await redis.del(...keys);
      console.log(`🗑️ [MCP Cache] Cleared ${keys.length} cached results for tool ${toolId}`);
    }
  } catch (error) {
    console.error(`❌ [MCP Cache] Error clearing tool results:`, error.message);
  }
}

// ============================================================================
// HEALTH CHECK
// ============================================================================

/**
 * Check if cache is available and healthy.
 * @returns {Promise<boolean>}
 */
export async function isCacheHealthy() {
  if (!redis) return false;

  try {
    await redis.ping();
    return true;
  } catch {
    return false;
  }
}

/**
 * Get cache statistics.
 * @returns {Promise<Object>}
 */
export async function getCacheStats() {
  if (!redis || redis.status !== 'ready') {
    return { status: 'disconnected' };
  }

  try {
    const info = await redis.info('memory');
    const toolKeys = await redis.keys(`${TOOL_CACHE_PREFIX}*`);
    const resultKeys = await redis.keys(`${RESULT_CACHE_PREFIX}*`);

    return {
      status: 'connected',
      toolCacheEntries: toolKeys.length,
      resultCacheEntries: resultKeys.length
    };
  } catch (error) {
    return { status: 'error', error: error.message };
  }
}

export default {
  getCachedTools,
  invalidateToolCache,
  getCachedResult,
  cacheResult,
  clearToolResults,
  isCacheHealthy,
  getCacheStats
};
