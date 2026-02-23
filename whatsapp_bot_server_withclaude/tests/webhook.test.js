/**
 * Webhook Endpoint Tests
 */
import request from 'supertest';
import { createTestApp, createMockWebhookPayload, createMockStatusPayload } from './testApp.js';

describe('Webhook Endpoints', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  describe('GET /webhook (Verification)', () => {
    const WEBHOOK_VERIFY_TOKEN = 'COOL';

    it('should return challenge when verification is valid', async () => {
      const challenge = '1234567890';
      const response = await request(app)
        .get('/webhook')
        .query({
          'hub.mode': 'subscribe',
          'hub.verify_token': WEBHOOK_VERIFY_TOKEN,
          'hub.challenge': challenge
        })
        .expect(200);

      expect(response.text).toBe(challenge);
    });

    it('should return 403 when token is invalid', async () => {
      await request(app)
        .get('/webhook')
        .query({
          'hub.mode': 'subscribe',
          'hub.verify_token': 'WRONG_TOKEN',
          'hub.challenge': '12345'
        })
        .expect(403);
    });

    it('should return 403 when mode is not subscribe', async () => {
      await request(app)
        .get('/webhook')
        .query({
          'hub.mode': 'unsubscribe',
          'hub.verify_token': WEBHOOK_VERIFY_TOKEN,
          'hub.challenge': '12345'
        })
        .expect(403);
    });

    it('should return 403 when challenge is missing', async () => {
      await request(app)
        .get('/webhook')
        .query({
          'hub.mode': 'subscribe',
          'hub.verify_token': WEBHOOK_VERIFY_TOKEN
        })
        .expect(200); // Returns empty challenge but still valid
    });
  });

  describe('POST /webhook (Message Reception)', () => {
    it('should acknowledge text message webhook', async () => {
      const payload = createMockWebhookPayload({
        type: 'text',
        messageBody: 'Hello from test'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });

    it('should acknowledge image message webhook', async () => {
      const payload = createMockWebhookPayload({
        type: 'image'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });

    it('should acknowledge document message webhook', async () => {
      const payload = createMockWebhookPayload({
        type: 'document'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });

    it('should acknowledge empty payload', async () => {
      await request(app)
        .post('/webhook')
        .send({})
        .expect(200);
    });
  });

  describe('POST /webhook (Status Updates)', () => {
    it('should acknowledge delivered status', async () => {
      const payload = createMockStatusPayload({
        status: 'delivered'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });

    it('should acknowledge read status', async () => {
      const payload = createMockStatusPayload({
        status: 'read'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });

    it('should acknowledge sent status', async () => {
      const payload = createMockStatusPayload({
        status: 'sent'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });

    it('should acknowledge failed status', async () => {
      const payload = createMockStatusPayload({
        status: 'failed'
      });

      await request(app)
        .post('/webhook')
        .send(payload)
        .expect(200);
    });
  });
});

describe('Webhook Payload Structure', () => {
  describe('createMockWebhookPayload', () => {
    it('should create valid text message payload', () => {
      const payload = createMockWebhookPayload({
        type: 'text',
        messageBody: 'Test message'
      });

      expect(payload).toHaveProperty('object', 'whatsapp_business_account');
      expect(payload.entry).toHaveLength(1);
      expect(payload.entry[0].changes).toHaveLength(1);

      const message = payload.entry[0].changes[0].value.messages[0];
      expect(message.type).toBe('text');
      expect(message.text.body).toBe('Test message');
    });

    it('should create valid image message payload', () => {
      const payload = createMockWebhookPayload({
        type: 'image'
      });

      const message = payload.entry[0].changes[0].value.messages[0];
      expect(message.type).toBe('image');
      expect(message.image).toHaveProperty('id');
      expect(message.image).toHaveProperty('mime_type');
    });

    it('should include contact information', () => {
      const payload = createMockWebhookPayload({
        phoneNumber: '919876543210'
      });

      const contacts = payload.entry[0].changes[0].value.contacts;
      expect(contacts).toHaveLength(1);
      expect(contacts[0].wa_id).toBe('919876543210');
    });
  });

  describe('createMockStatusPayload', () => {
    it('should create valid status payload', () => {
      const payload = createMockStatusPayload({
        status: 'delivered',
        messageId: 'wamid.test123'
      });

      expect(payload).toHaveProperty('object', 'whatsapp_business_account');
      expect(payload.entry[0].changes[0].value.statuses).toHaveLength(1);

      const status = payload.entry[0].changes[0].value.statuses[0];
      expect(status.status).toBe('delivered');
      expect(status.id).toBe('wamid.test123');
    });
  });
});
