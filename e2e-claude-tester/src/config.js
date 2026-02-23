/**
 * Environment configuration for E2E tests.
 * All values come from environment variables (set via GitHub Secrets in CI).
 */

const config = {
  // Service URLs (default to Azure production)
  services: {
    nodejs: process.env.NODEJS_URL || 'https://whatsappbotserver.azurewebsites.net',
    fastapi: process.env.FASTAPI_URL || 'https://fastapione-gue2c5ecc9c4b8hy.azurewebsites.net',
    django: process.env.DJANGO_URL || 'https://backeng4whatsapp.azurewebsites.net',
  },

  // WhatsApp test identifiers
  whatsapp: {
    phoneNumberId: process.env.TEST_PHONE_NUMBER_ID || '123456789012345',
    userPhone: process.env.TEST_USER_PHONE || '919876543210',
    userName: process.env.TEST_USER_NAME || 'E2E Test User',
    appSecret: process.env.APP_SECRET || 'test_app_secret',
    tenantId: process.env.TEST_TENANT_ID || 'test_tenant',
    bpid: process.env.TEST_BPID || 'test_bpid',
  },

  // Django auth test credentials
  auth: {
    username: process.env.TEST_USERNAME || '',
    password: process.env.TEST_PASSWORD || '',
  },

  // AI configuration (GitHub Models via OpenAI SDK)
  ai: {
    token: process.env.GITHUB_TOKEN || '',
    model: process.env.AI_MODEL || 'openai/gpt-4.1-mini',
    baseURL: 'https://models.inference.ai.azure.com',
    maxTurns: 30,
    maxToolCalls: 50,
  },

  // Test execution
  test: {
    scope: process.env.TEST_SCOPE || 'auto',
    forceAll: process.env.FORCE_ALL_TESTS === 'true',
    timeout: parseInt(process.env.TEST_TIMEOUT || '10000', 10),
  },
};

export default config;
