/**
 * Tests for helpers/agentMapping.js — Redis-backed agent-to-customer mapping.
 * Mocks sessionManager.client to use an in-memory store.
 */
import { jest } from '@jest/globals';

// Create an in-memory Redis mock
function createMockRedisClient() {
  const store = new Map();

  return {
    setEx: jest.fn(async (key, ttl, value) => {
      store.set(key, value);
    }),
    get: jest.fn(async (key) => {
      return store.get(key) || null;
    }),
    del: jest.fn(async (key) => {
      store.delete(key);
    }),
    exists: jest.fn(async (key) => {
      return store.has(key) ? 1 : 0;
    }),
    scanIterator: jest.fn(function* ({ MATCH }) {
      const prefix = MATCH.replace('*', '');
      for (const key of store.keys()) {
        if (key.startsWith(prefix)) yield key;
      }
    }),
    _store: store,  // Expose for test inspection
  };
}

const mockClient = createMockRedisClient();

jest.unstable_mockModule('../sessionManager.js', () => ({
  default: { client: mockClient },
}));

const {
  setAgentMapping,
  getAgentMapping,
  deleteAgentMapping,
  isAgent,
  isCustomerMapped,
} = await import('../helpers/agentMapping.js');


describe('Agent Mapping', () => {
  beforeEach(() => {
    mockClient._store.clear();
    jest.clearAllMocks();
  });

  test('setAgentMapping stores and getAgentMapping retrieves', async () => {
    await setAgentMapping('91agent', '91customer');
    const result = await getAgentMapping('91agent');
    expect(result).toBe('91customer');
  });

  test('deleteAgentMapping removes mapping', async () => {
    await setAgentMapping('91del_agent', '91del_customer');
    await deleteAgentMapping('91del_agent');
    const result = await getAgentMapping('91del_agent');
    expect(result).toBeNull();
  });

  test('isAgent returns true for mapped phone', async () => {
    await setAgentMapping('91is_agent', '91some_customer');
    const result = await isAgent('91is_agent');
    expect(result).toBe(true);
  });

  test('isAgent returns false for unmapped phone', async () => {
    const result = await isAgent('91unknown');
    expect(result).toBe(false);
  });

  test('isCustomerMapped finds customer across agents', async () => {
    await setAgentMapping('91agentX', '91targetCustomer');
    const result = await isCustomerMapped('91targetCustomer');
    expect(result).toBe(true);
  });

  test('agent mapping uses agent:map: prefix', async () => {
    await setAgentMapping('91prefix_test', '91cust');
    expect(mockClient.setEx).toHaveBeenCalledWith(
      'agent:map:91prefix_test',
      86400,
      '91cust'
    );
  });
});
