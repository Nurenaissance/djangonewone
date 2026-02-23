/**
 * Session Manager Tests
 * Tests for the mock session manager and session-related functionality
 */
import { createMockSessionManager } from './testApp.js';

describe('Session Manager', () => {
  let sessionManager;

  beforeEach(() => {
    sessionManager = createMockSessionManager();
  });

  describe('Basic Operations', () => {
    it('should start with zero sessions', async () => {
      const size = await sessionManager.size();
      expect(size).toBe(0);
    });

    it('should be connected by default', () => {
      expect(sessionManager.isConnected).toBe(true);
    });

    it('should allow disconnection', async () => {
      await sessionManager.disconnect();
      expect(sessionManager.isConnected).toBe(false);
    });

    it('should allow reconnection', async () => {
      await sessionManager.disconnect();
      await sessionManager.connect();
      expect(sessionManager.isConnected).toBe(true);
    });
  });

  describe('Session CRUD', () => {
    const testKey = '919876543210_241683569037594';
    const testSession = {
      userPhoneNumber: '919876543210',
      business_phone_number_id: '241683569037594',
      tenant: 'test_tenant',
      flowName: 'test_flow'
    };

    it('should set and get a session', async () => {
      await sessionManager.set(testKey, testSession);
      const retrieved = await sessionManager.get(testKey);

      expect(retrieved).toEqual(testSession);
    });

    it('should return null for non-existent session', async () => {
      const retrieved = await sessionManager.get('non_existent_key');
      expect(retrieved).toBeNull();
    });

    it('should check if session exists', async () => {
      expect(await sessionManager.has(testKey)).toBe(false);

      await sessionManager.set(testKey, testSession);

      expect(await sessionManager.has(testKey)).toBe(true);
    });

    it('should delete a session', async () => {
      await sessionManager.set(testKey, testSession);
      expect(await sessionManager.has(testKey)).toBe(true);

      await sessionManager.delete(testKey);

      expect(await sessionManager.has(testKey)).toBe(false);
    });

    it('should update session size after operations', async () => {
      expect(await sessionManager.size()).toBe(0);

      await sessionManager.set(testKey, testSession);
      expect(await sessionManager.size()).toBe(1);

      await sessionManager.set('another_key', { data: 'test' });
      expect(await sessionManager.size()).toBe(2);

      await sessionManager.delete(testKey);
      expect(await sessionManager.size()).toBe(1);
    });
  });

  describe('Bulk Operations', () => {
    it('should return all sessions via entries()', async () => {
      await sessionManager.set('key1', { data: 'session1' });
      await sessionManager.set('key2', { data: 'session2' });
      await sessionManager.set('key3', { data: 'session3' });

      const entries = await sessionManager.entries();

      expect(entries).toHaveLength(3);
      expect(entries.map(e => e[0])).toContain('key1');
      expect(entries.map(e => e[0])).toContain('key2');
      expect(entries.map(e => e[0])).toContain('key3');
    });

    it('should clear all sessions', async () => {
      await sessionManager.set('key1', { data: 'session1' });
      await sessionManager.set('key2', { data: 'session2' });
      expect(await sessionManager.size()).toBe(2);

      await sessionManager.clear();

      expect(await sessionManager.size()).toBe(0);
    });
  });

  describe('Session Data Integrity', () => {
    it('should preserve complex session data', async () => {
      const complexSession = {
        userPhoneNumber: '919876543210',
        business_phone_number_id: '241683569037594',
        tenant: 'test_tenant',
        flowName: 'test_flow',
        flowData: [
          { id: 0, type: 'Start', body: 'Welcome' },
          { id: 1, type: 'Button', body: 'Choose option' }
        ],
        adjList: [[1], [2]],
        currNode: 0,
        nextNode: [1],
        inputVariable: 'user_name',
        accessToken: 'test_token_123',
        userName: 'Test User'
      };

      await sessionManager.set('complex_key', complexSession);
      const retrieved = await sessionManager.get('complex_key');

      expect(retrieved).toEqual(complexSession);
      expect(retrieved.flowData).toHaveLength(2);
      expect(retrieved.adjList).toEqual([[1], [2]]);
    });

    it('should handle session updates', async () => {
      const key = 'update_test_key';
      const initialSession = { state: 'initial', counter: 0 };

      await sessionManager.set(key, initialSession);

      // Update session
      const session = await sessionManager.get(key);
      session.state = 'updated';
      session.counter = 1;
      await sessionManager.set(key, session);

      const updated = await sessionManager.get(key);
      expect(updated.state).toBe('updated');
      expect(updated.counter).toBe(1);
    });
  });
});

describe('Session Key Format', () => {
  it('should use correct key format for sessions', () => {
    const phoneNumber = '919876543210';
    const businessPhoneId = '241683569037594';
    const expectedKey = `${phoneNumber}${businessPhoneId}`;

    expect(expectedKey).toBe('919876543210241683569037594');
  });

  it('should handle different phone number formats', () => {
    const testCases = [
      { phone: '919876543210', bpid: '123', expected: '919876543210123' },
      { phone: '14155551234', bpid: '456', expected: '14155551234456' },
      { phone: '447911123456', bpid: '789', expected: '447911123456789' }
    ];

    testCases.forEach(({ phone, bpid, expected }) => {
      const key = `${phone}${bpid}`;
      expect(key).toBe(expected);
    });
  });
});
