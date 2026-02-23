/**
 * Health Endpoint Tests
 */
import request from 'supertest';
import { createTestApp } from './testApp.js';

describe('Health Endpoints', () => {
  let app;

  beforeAll(() => {
    app = createTestApp();
  });

  describe('GET /health', () => {
    it('should return 200 with health status', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status');
      expect(response.body).toHaveProperty('server');
      expect(response.body).toHaveProperty('redis');
      expect(response.body).toHaveProperty('timestamp');
      expect(response.body.status).toBe('healthy');
    });

    it('should include response time', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('responseTime');
      expect(response.body.responseTime).toMatch(/\d+ms/);
    });

    it('should include session count', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('sessions');
      expect(response.body.sessions).toHaveProperty('activeCount');
    });
  });

  describe('GET /health/live', () => {
    it('should return 200 with alive status', async () => {
      const response = await request(app)
        .get('/health/live')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'alive');
      expect(response.body).toHaveProperty('timestamp');
    });

    it('should have valid ISO timestamp', async () => {
      const response = await request(app)
        .get('/health/live')
        .expect(200);

      const timestamp = new Date(response.body.timestamp);
      expect(timestamp.getTime()).not.toBeNaN();
    });
  });

  describe('GET /health/ready', () => {
    it('should return 200 when server is ready', async () => {
      const response = await request(app)
        .get('/health/ready')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'ready');
      expect(response.body).toHaveProperty('timestamp');
    });
  });

  describe('GET /health/detailed', () => {
    it('should return detailed health information', async () => {
      const response = await request(app)
        .get('/health/detailed')
        .expect(200);

      expect(response.body).toHaveProperty('status');
      expect(response.body).toHaveProperty('server');
      expect(response.body).toHaveProperty('memory');
      expect(response.body).toHaveProperty('redis');
      expect(response.body).toHaveProperty('sessions');
    });

    it('should include memory usage', async () => {
      const response = await request(app)
        .get('/health/detailed')
        .expect(200);

      expect(response.body.memory).toHaveProperty('status', 'healthy');
      expect(response.body.memory).toHaveProperty('heapUsed');
      expect(response.body.memory).toHaveProperty('heapTotal');
    });

    it('should include server uptime', async () => {
      const response = await request(app)
        .get('/health/detailed')
        .expect(200);

      expect(response.body.server).toHaveProperty('uptime');
      expect(typeof response.body.server.uptime).toBe('number');
    });
  });
});
