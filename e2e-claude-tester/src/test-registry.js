/**
 * Registry of E2E test scenarios with service tags and priority.
 */

const ALL_TESTS = [
  // --- Health checks (always run) ---
  { id: 'health-nodejs', name: 'Health Check - Node.js', services: ['nodejs'], priority: 1, category: 'health' },
  { id: 'health-fastapi', name: 'Health Check - FastAPI', services: ['fastapi'], priority: 1, category: 'health' },
  { id: 'health-django', name: 'Health Check - Django', services: ['django'], priority: 1, category: 'health' },

  // --- Webhook tests ---
  { id: 'webhook-text', name: 'Webhook - Text Message', services: ['nodejs'], priority: 2, category: 'webhook' },
  { id: 'webhook-button', name: 'Webhook - Button Reply', services: ['nodejs'], priority: 2, category: 'webhook' },
  { id: 'webhook-list', name: 'Webhook - List Reply', services: ['nodejs'], priority: 2, category: 'webhook' },
  { id: 'webhook-status', name: 'Webhook - Status Update', services: ['nodejs'], priority: 3, category: 'webhook' },
  { id: 'webhook-image', name: 'Webhook - Image Message', services: ['nodejs'], priority: 3, category: 'webhook' },
  { id: 'webhook-greeting-flow', name: 'Webhook - Greeting Flow', services: ['nodejs'], priority: 2, category: 'webhook' },
  { id: 'webhook-verification', name: 'Webhook - GET Verification', services: ['nodejs'], priority: 2, category: 'webhook' },

  // --- Campaign API tests ---
  { id: 'campaign-status', name: 'Campaign API - Status Endpoint', services: ['nodejs'], priority: 2, category: 'campaign' },
  { id: 'campaign-list', name: 'Campaign API - List Endpoint', services: ['nodejs'], priority: 2, category: 'campaign' },
  { id: 'campaign-stop', name: 'Campaign API - Stop Validation', services: ['nodejs'], priority: 3, category: 'campaign' },
  { id: 'campaign-resume', name: 'Campaign API - Resume Validation', services: ['nodejs'], priority: 3, category: 'campaign' },

  // --- Auth tests ---
  { id: 'auth-login', name: 'Auth - Django Login Endpoint', services: ['django'], priority: 2, category: 'auth' },
  { id: 'auth-jwt-flow', name: 'Auth - Full JWT Flow', services: ['django', 'fastapi'], priority: 3, category: 'auth' },

  // --- FastAPI endpoint tests ---
  { id: 'fastapi-root', name: 'FastAPI - Root Endpoint', services: ['fastapi'], priority: 2, category: 'fastapi' },
  { id: 'fastapi-contacts-auth', name: 'FastAPI - Contacts Auth Check', services: ['fastapi'], priority: 3, category: 'fastapi' },
];

/**
 * Get tests relevant to the affected services.
 */
export function getTestsForServices(affectedServices, forceAll = false) {
  if (forceAll) return ALL_TESTS;

  // Always include health checks + tests for affected services
  return ALL_TESTS.filter((t) => {
    if (t.category === 'health') return true;
    return t.services.some((s) => affectedServices.includes(s));
  }).sort((a, b) => a.priority - b.priority);
}

export function getTestRegistry() {
  return ALL_TESTS;
}
