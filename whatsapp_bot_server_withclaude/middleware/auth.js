/**
 * Authentication Middleware for Node.js Bot Server
 * Supports dual authentication: User JWT tokens and Service API keys
 */

const jwt = require('jsonwebtoken');

// Load service keys from environment
const SERVICE_KEYS = {
  django: process.env.DJANGO_SERVICE_KEY,
  fastapi: process.env.FASTAPI_SERVICE_KEY,
  nodejs: process.env.NODEJS_SERVICE_KEY,
};

// Public routes that don't require authentication
const PUBLIC_ROUTES = [
  '/health',
  '/webhook',  // Webhook has its own signature validation
];

// Origins that bypass authentication (trusted internal services)
const BYPASS_AUTH_ORIGINS = [
  'https://nurenaiautomatic-b7hmdnb4fzbpbtbh.canadacentral-01.azurewebsites.net'
];

// Trusted source identifiers (for X-Trusted-Source header)
const TRUSTED_SOURCES = ['nurenaiautomatic'];

// Simple API key for n8n bypass (easier to configure than service keys)
const N8N_API_KEY = 'n8n-nuren-2026';

/**
 * Check if request is from a trusted source
 * @param {Object} req - Express request object
 * @returns {boolean}
 */
function isTrustedRequest(req) {
  // Debug logging - remove after fixing
  console.log('🔍 Auth Debug - Checking trusted request:');
  console.log('  Path:', req.path);
  console.log('  X-Api-Key:', req.headers['x-api-key'] || '(not set)');
  console.log('  User-Agent:', req.headers['user-agent'] || '(not set)');
  console.log('  Origin:', req.headers.origin || '(not set)');
  console.log('  Query api_key:', req.query.api_key || '(not set)');

  // Check simple X-Api-Key header (easiest for n8n)
  const apiKey = req.headers['x-api-key'] || '';
  if (apiKey === N8N_API_KEY) {
    console.log('  ✅ Matched X-Api-Key header');
    return true;
  }

  // Check query parameter ?api_key=xxx
  const apiKeyParam = req.query.api_key || '';
  if (apiKeyParam === N8N_API_KEY) {
    console.log('  ✅ Matched query parameter api_key');
    return true;
  }

  // Check Origin header
  const origin = req.headers.origin || '';
  if (BYPASS_AUTH_ORIGINS.some(allowed => origin.startsWith(allowed))) {
    console.log('  ✅ Matched Origin header');
    return true;
  }

  // Check Referer header
  const referer = req.headers.referer || '';
  if (BYPASS_AUTH_ORIGINS.some(allowed => referer.startsWith(allowed))) {
    console.log('  ✅ Matched Referer header');
    return true;
  }

  // Check custom X-Trusted-Source header
  const trustedSource = req.headers['x-trusted-source'] || '';
  if (TRUSTED_SOURCES.includes(trustedSource)) {
    console.log('  ✅ Matched X-Trusted-Source header');
    return true;
  }

  // Check User-Agent for n8n (n8n sends "n8n" or "axios/x.x.x" as User-Agent)
  const userAgent = req.headers['user-agent'] || '';
  if (userAgent.toLowerCase().includes('n8n') || userAgent.toLowerCase().includes('axios')) {
    console.log('  ✅ Matched n8n/axios User-Agent');
    return true;
  }

  console.log('  ❌ No trusted source match found');
  return false;
}

/**
 * Check if API key is a valid service key
 * @param {string} apiKey - The API key to validate
 * @returns {{valid: boolean, serviceName: string|null}}
 */
function isValidServiceKey(apiKey) {
  for (const [serviceName, key] of Object.entries(SERVICE_KEYS)) {
    if (key && apiKey === key) {
      return { valid: true, serviceName };
    }
  }
  return { valid: false, serviceName: null };
}

/**
 * Authentication middleware supporting both user tokens and service keys
 *
 * Authentication priority:
 * 1. Check if route is public → Allow
 * 2. Check for service API key (X-Service-Key header) → Allow
 * 3. Check for user JWT token (Authorization: Bearer) → Validate and allow
 * 4. Reject request with 401
 */
function authMiddleware(req, res, next) {
  const path = req.path;

  // 1. Allow public routes
  if (PUBLIC_ROUTES.includes(path) || path.startsWith('/docs')) {
    return next();
  }

  // 2. Allow requests from trusted origins (bypass auth)
  if (isTrustedRequest(req)) {
    req.isTrustedOrigin = true;
    console.log('✅ Request from trusted source - bypassing auth');
    return next();
  }

  // 3. Check for Service API Key (X-Service-Key header)
  const serviceKey = req.headers['x-service-key'];

  if (serviceKey) {
    const { valid, serviceName } = isValidServiceKey(serviceKey);

    if (valid) {
      // Valid service request
      req.isServiceRequest = true;
      req.serviceName = serviceName;

      // Get tenant context from X-Tenant-Id header
      const tenantId = req.headers['x-tenant-id'];
      if (tenantId) {
        req.tenantId = tenantId;
      }

      console.log(`✅ Service request from: ${serviceName} (tenant: ${tenantId || 'none'})`);
      return next();
    } else {
      console.warn(`❌ Invalid service key attempted from ${req.ip}`);
      return res.status(403).json({
        error: 'forbidden',
        message: 'Invalid service key'
      });
    }
  }

  // 3. Check for User JWT Token (Authorization: Bearer token)
  const authHeader = req.headers.authorization;

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      error: 'unauthorized',
      message: 'Missing or invalid authorization header'
    });
  }

  const token = authHeader.split(' ')[1];

  try {
    // Verify and decode JWT token
    const secret = process.env.JWT_SECRET_KEY || process.env.JWT_SECRET || 'your-secret-key';
    const payload = jwt.verify(token, secret);

    // Add user info to request
    req.userId = payload.user_id || payload.sub;
    req.tenantId = payload.tenant_id;
    req.userRole = payload.role;
    req.scope = payload.scope;
    req.isServiceRequest = false;

    // Handle system/service scope from JWT
    if (req.scope === 'service' || req.userRole === 'system') {
      req.isService = true;
    }

    return next();

  } catch (error) {
    // Allow trusted sources even with token errors
    if (isTrustedRequest(req)) {
      req.isTrustedOrigin = true;
      console.log('✅ Trusted source with token error - allowing request');
      return next();
    }

    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        error: 'token_expired',
        message: 'Access token has expired'
      });
    }

    if (error.name === 'JsonWebTokenError') {
      console.warn(`Invalid JWT token: ${error.message}`);
      return res.status(401).json({
        error: 'invalid_token',
        message: 'Invalid token'
      });
    }

    console.error(`Unexpected error in auth middleware: ${error.message}`);
    return res.status(401).json({
      error: 'authentication_error',
      message: 'Authentication failed'
    });
  }
}

/**
 * Optional: Middleware to require tenant context
 * Use this after authMiddleware for endpoints that need tenant_id
 */
function requireTenant(req, res, next) {
  if (!req.tenantId) {
    return res.status(400).json({
      error: 'bad_request',
      message: 'Tenant ID is required (X-Tenant-Id header)'
    });
  }
  next();
}

module.exports = {
  authMiddleware,
  requireTenant,
  isValidServiceKey,
  isTrustedRequest,
};
