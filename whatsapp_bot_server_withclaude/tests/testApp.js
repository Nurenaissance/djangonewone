/**
 * Test Application
 * Creates a minimal Express app for testing routes without Redis/external dependencies
 */
import express from 'express';

/**
 * Create a test app with mocked dependencies
 */
export function createTestApp() {
  const app = express();

  // Basic middleware
  app.use(express.json());

  // Mock session manager for health routes
  const mockSessionManager = {
    isConnected: true,
    size: async () => 5,
    get: async () => null,
    set: async () => true,
    delete: async () => true
  };

  // Health routes with mock
  app.get('/health', async (req, res) => {
    const startTime = Date.now();
    const checks = {
      server: 'healthy',
      redis: mockSessionManager.isConnected ? 'healthy' : 'unhealthy',
      sessions: {
        status: 'healthy',
        activeCount: await mockSessionManager.size()
      },
      timestamp: new Date().toISOString()
    };

    const isHealthy = checks.server === 'healthy' && checks.redis === 'healthy';
    checks.status = isHealthy ? 'healthy' : 'degraded';
    checks.responseTime = `${Date.now() - startTime}ms`;

    res.status(isHealthy ? 200 : 503).json(checks);
  });

  app.get('/health/live', (req, res) => {
    res.status(200).json({ status: 'alive', timestamp: new Date().toISOString() });
  });

  app.get('/health/ready', (req, res) => {
    res.status(200).json({ status: 'ready', timestamp: new Date().toISOString() });
  });

  app.get('/health/detailed', async (req, res) => {
    const memUsage = process.memoryUsage();
    res.status(200).json({
      status: 'healthy',
      server: { status: 'healthy', uptime: process.uptime() },
      memory: {
        status: 'healthy',
        heapUsed: `${Math.round(memUsage.heapUsed / 1024 / 1024)}MB`,
        heapTotal: `${Math.round(memUsage.heapTotal / 1024 / 1024)}MB`
      },
      redis: { status: 'healthy' },
      sessions: { status: 'healthy', activeCount: 5 },
      timestamp: new Date().toISOString()
    });
  });

  // Webhook verification route
  const WEBHOOK_VERIFY_TOKEN = 'COOL';
  app.get('/webhook', (req, res) => {
    const mode = req.query['hub.mode'];
    const token = req.query['hub.verify_token'];
    const challenge = req.query['hub.challenge'];

    if (mode === 'subscribe' && token === WEBHOOK_VERIFY_TOKEN) {
      res.status(200).send(challenge);
    } else {
      res.sendStatus(403);
    }
  });

  // Webhook POST route (simplified for testing)
  app.post('/webhook', (req, res) => {
    // Acknowledge immediately
    res.sendStatus(200);
  });

  // Default route
  app.get('/', (req, res) => {
    res.send('<pre>Nothing to see here. Checkout README.md to start.</pre>');
  });

  // 404 handler
  app.use((req, res) => {
    res.status(404).json({ error: 'Not found' });
  });

  return app;
}

/**
 * Create mock session manager
 */
export function createMockSessionManager(options = {}) {
  return {
    isConnected: options.isConnected ?? true,
    sessions: new Map(),
    async size() {
      return this.sessions.size;
    },
    async get(key) {
      return this.sessions.get(key) || null;
    },
    async set(key, value) {
      this.sessions.set(key, value);
      return true;
    },
    async delete(key) {
      this.sessions.delete(key);
      return true;
    },
    async has(key) {
      return this.sessions.has(key);
    },
    async clear() {
      this.sessions.clear();
      return true;
    },
    async entries() {
      return Array.from(this.sessions.entries());
    },
    async connect() {
      this.isConnected = true;
      return true;
    },
    async disconnect() {
      this.isConnected = false;
    }
  };
}

/**
 * Create mock WhatsApp message payload
 */
export function createMockWebhookPayload(options = {}) {
  const {
    type = 'text',
    phoneNumber = '919876543210',
    businessPhoneId = '241683569037594',
    messageBody = 'Hello',
    contact = { wa_id: phoneNumber, profile: { name: 'Test User' } }
  } = options;

  const message = {
    id: `wamid.test_${Date.now()}`,
    from: phoneNumber,
    timestamp: Math.floor(Date.now() / 1000).toString(),
    type
  };

  if (type === 'text') {
    message.text = { body: messageBody };
  } else if (type === 'image') {
    message.image = {
      id: `media_id_${Date.now()}`,
      mime_type: 'image/jpeg'
    };
  } else if (type === 'document') {
    message.document = {
      id: `doc_id_${Date.now()}`,
      filename: 'test.pdf',
      mime_type: 'application/pdf'
    };
  }

  return {
    object: 'whatsapp_business_account',
    entry: [{
      id: businessPhoneId,
      changes: [{
        value: {
          messaging_product: 'whatsapp',
          metadata: {
            display_phone_number: '15551234567',
            phone_number_id: businessPhoneId
          },
          contacts: [contact],
          messages: [message]
        },
        field: 'messages'
      }]
    }]
  };
}

/**
 * Create mock status update payload
 */
export function createMockStatusPayload(options = {}) {
  const {
    status = 'delivered',
    messageId = `wamid.test_${Date.now()}`,
    phoneNumber = '919876543210',
    businessPhoneId = '241683569037594'
  } = options;

  return {
    object: 'whatsapp_business_account',
    entry: [{
      id: businessPhoneId,
      changes: [{
        value: {
          messaging_product: 'whatsapp',
          metadata: {
            display_phone_number: '15551234567',
            phone_number_id: businessPhoneId
          },
          statuses: [{
            id: messageId,
            status,
            timestamp: Math.floor(Date.now() / 1000).toString(),
            recipient_id: phoneNumber
          }]
        },
        field: 'messages'
      }]
    }]
  };
}
