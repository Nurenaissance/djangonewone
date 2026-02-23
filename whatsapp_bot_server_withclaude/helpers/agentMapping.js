import sessionManager from '../sessionManager.js';

const AGENT_MAP_PREFIX = 'agent:map:';
const AGENT_MAP_TTL = 86400; // 24 hours

/**
 * Redis-backed agent-to-customer mapping
 * Replaces in-memory nurenConsumerMap for horizontal scaling
 */

export async function setAgentMapping(agentPhone, customerPhone) {
  const key = AGENT_MAP_PREFIX + agentPhone;
  await sessionManager.client.setEx(key, AGENT_MAP_TTL, customerPhone);
}

export async function getAgentMapping(agentPhone) {
  const key = AGENT_MAP_PREFIX + agentPhone;
  return await sessionManager.client.get(key);
}

export async function deleteAgentMapping(agentPhone) {
  const key = AGENT_MAP_PREFIX + agentPhone;
  await sessionManager.client.del(key);
}

export async function isCustomerMapped(customerPhone) {
  // Scan for any agent mapped to this customer
  const keys = [];
  for await (const key of sessionManager.client.scanIterator({ MATCH: AGENT_MAP_PREFIX + '*', COUNT: 100 })) {
    keys.push(key);
  }
  for (const key of keys) {
    const mapped = await sessionManager.client.get(key);
    if (mapped === customerPhone) return true;
  }
  return false;
}

export async function isAgent(phone) {
  const key = AGENT_MAP_PREFIX + phone;
  return await sessionManager.client.exists(key) === 1;
}
