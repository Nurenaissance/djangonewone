/**
 * Server and Route Tests
 */
import request from 'supertest';
import { createTestApp } from './testApp.js';

describe('Server', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  describe('Default Route', () => {
    it('should return welcome message on GET /', async () => {
      const response = await request(app)
        .get('/')
        .expect(200);

      expect(response.text).toContain('README.md');
    });
  });

  describe('404 Handling', () => {
    it('should return 404 for unknown routes', async () => {
      const response = await request(app)
        .get('/unknown-route')
        .expect(404);

      expect(response.body).toHaveProperty('error', 'Not found');
    });

    it('should return 404 for unknown POST routes', async () => {
      const response = await request(app)
        .post('/unknown-route')
        .send({})
        .expect(404);

      expect(response.body).toHaveProperty('error', 'Not found');
    });
  });

  describe('Content Type Handling', () => {
    it('should accept JSON content type', async () => {
      await request(app)
        .post('/webhook')
        .set('Content-Type', 'application/json')
        .send({})
        .expect(200);
    });

    it('should handle requests without content type', async () => {
      await request(app)
        .post('/webhook')
        .send({})
        .expect(200);
    });
  });

  describe('HTTP Methods', () => {
    it('should respond to GET requests', async () => {
      await request(app)
        .get('/health')
        .expect(200);
    });

    it('should respond to POST requests', async () => {
      await request(app)
        .post('/webhook')
        .send({})
        .expect(200);
    });
  });
});

describe('Response Headers', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  it('should return JSON content type for health endpoint', async () => {
    const response = await request(app)
      .get('/health')
      .expect(200);

    expect(response.headers['content-type']).toMatch(/application\/json/);
  });

  it('should return text for webhook verification', async () => {
    const response = await request(app)
      .get('/webhook')
      .query({
        'hub.mode': 'subscribe',
        'hub.verify_token': 'COOL',
        'hub.challenge': 'test_challenge'
      })
      .expect(200);

    expect(response.text).toBe('test_challenge');
  });
});

describe('Error Handling', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  it('should handle malformed JSON gracefully', async () => {
    const response = await request(app)
      .post('/webhook')
      .set('Content-Type', 'application/json')
      .send('not valid json');

    // Should either return 400 (bad request) or 200 (graceful handling)
    expect([200, 400]).toContain(response.status);
  });

  it('should handle empty body', async () => {
    await request(app)
      .post('/webhook')
      .send(null)
      .expect(200);
  });

  it('should handle array body', async () => {
    await request(app)
      .post('/webhook')
      .send([])
      .expect(200);
  });
});

describe('Request Validation', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  describe('Webhook Verification', () => {
    it('should require all verification parameters', async () => {
      // Missing hub.mode
      await request(app)
        .get('/webhook')
        .query({
          'hub.verify_token': 'COOL',
          'hub.challenge': 'test'
        })
        .expect(403);

      // Missing hub.verify_token
      await request(app)
        .get('/webhook')
        .query({
          'hub.mode': 'subscribe',
          'hub.challenge': 'test'
        })
        .expect(403);
    });
  });
});

describe('Security Considerations', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  it('should not expose internal errors in response', async () => {
    const response = await request(app)
      .get('/health')
      .expect(200);

    // Should not contain stack traces
    expect(JSON.stringify(response.body)).not.toContain('Error:');
    expect(JSON.stringify(response.body)).not.toContain('at ');
  });

  it('should not include sensitive data in health response', async () => {
    const response = await request(app)
      .get('/health')
      .expect(200);

    // Should not contain passwords or tokens
    expect(JSON.stringify(response.body).toLowerCase()).not.toContain('password');
    expect(JSON.stringify(response.body).toLowerCase()).not.toContain('secret');
    expect(JSON.stringify(response.body).toLowerCase()).not.toContain('token');
  });
});
