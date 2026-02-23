/**
 * Tests for helpers/misc.js saveMessage function.
 * Mocks axios and all transitive dependencies to avoid real HTTP/Redis calls.
 */
import { jest } from '@jest/globals';

const mockAxiosPost = jest.fn();
const mockAxiosGet = jest.fn();

jest.unstable_mockModule('axios', () => ({
  default: {
    post: mockAxiosPost,
    get: mockAxiosGet,
    create: jest.fn(() => ({
      post: mockAxiosPost,
      get: mockAxiosGet,
      interceptors: { request: { use: jest.fn() }, response: { use: jest.fn() } },
    })),
  },
}));

// Mock server.js (imports @socket.io/redis-adapter transitively)
jest.unstable_mockModule('../server.js', () => ({
  userSessions: new Map(),
  messageCache: new Map(),
  io: null,
}));

// Mock mainwebhook/snm.js
jest.unstable_mockModule('../mainwebhook/snm.js', () => ({
  sendTextMessage: jest.fn(),
  sendNodeMessage: jest.fn(),
  fastURL: 'http://localhost:8001',
  djangoURL: 'http://localhost:8000',
}));

// Mock sessionManager
jest.unstable_mockModule('../sessionManager.js', () => ({
  default: { client: null, getSession: jest.fn(), setSession: jest.fn() },
}));

// Mock OpenAI
jest.unstable_mockModule('openai', () => ({
  default: class OpenAI { constructor() {} },
}));

// Mock normalize
jest.unstable_mockModule('../normalize.js', () => ({
  normalizePhone: jest.fn(p => p),
}));

// Mock edge-navigation
jest.unstable_mockModule('../helpers/edge-navigation.js', () => ({
  findNextNodesFromEdges: jest.fn(() => []),
  findNodeById: jest.fn(() => null),
}));

// Now import the module under test
const { saveMessage } = await import('../helpers/misc.js');


describe('saveMessage', () => {
  beforeEach(() => {
    mockAxiosPost.mockReset();
  });

  test('saveMessage posts to Django /whatsapp_convo_post/', async () => {
    mockAxiosPost.mockResolvedValueOnce({
      data: { message: 'Conversation saved', method: 'sync-bulk', saved: 1 },
    });

    const result = await saveMessage(
      '91123456789',
      '111222333',
      [{ text: 'Hello', sender: 'bot' }],
      'test_tenant',
      '2026-02-11T00:00:00Z',
      0,
      { blocking: true },
    );

    expect(mockAxiosPost).toHaveBeenCalledTimes(1);
    const [url, body] = mockAxiosPost.mock.calls[0];
    expect(url).toContain('/whatsapp_convo_post/91123456789/');
    expect(body.tenant).toBe('test_tenant');
    expect(body.conversations).toHaveLength(1);
  });

  test('saveMessage includes message_id when provided', async () => {
    mockAxiosPost.mockResolvedValueOnce({ data: { saved: 1 } });

    await saveMessage(
      '91999888777',
      '111222333',
      [{ text: 'Hi', sender: 'user' }],
      'test_tenant',
      null,
      0,
      { blocking: true, messageId: 'wamid.abc123' },
    );

    const [, body] = mockAxiosPost.mock.calls[0];
    expect(body.message_id).toBe('wamid.abc123');
  });

  test('saveMessage non-blocking returns {queued: true} immediately', async () => {
    mockAxiosPost.mockResolvedValueOnce({ data: { saved: 1 } });

    const result = await saveMessage(
      '91555666777',
      '111222333',
      [{ text: 'Fire and forget', sender: 'bot' }],
      'test_tenant',
      null,
      0,
      { blocking: false },
    );

    expect(result).toEqual({ queued: true });
  });

  test('saveMessage retries on server error (blocking mode)', async () => {
    mockAxiosPost
      .mockRejectedValueOnce({ response: { status: 500 }, message: 'Internal Server Error', code: null })
      .mockRejectedValueOnce({ response: { status: 500 }, message: 'Internal Server Error', code: null })
      .mockResolvedValueOnce({ data: { saved: 1 } });

    const result = await saveMessage(
      '91retry',
      '111222333',
      [{ text: 'Retry test', sender: 'bot' }],
      'test_tenant',
      null,
      0,
      { blocking: true },
    );

    expect(mockAxiosPost).toHaveBeenCalledTimes(3);
    expect(result).toEqual({ saved: 1 });
  }, 30000);
});
