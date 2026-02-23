/**
 * User Message Queue - Prevents race conditions by processing messages sequentially per user
 *
 * Problem: When a user sends multiple messages quickly, multiple webhooks process simultaneously,
 * reading the same session state and causing duplicate messages.
 *
 * Solution: Queue messages per user and process them one at a time.
 *
 * OPTIMIZED: Reuses the existing sessionManager's Redis client to avoid connection pool exhaustion
 */

import sessionManager from '../sessionManager.js';

/**
 * Get the Redis client from sessionManager (reuses existing connection)
 */
async function getQueueClient() {
  // Wait for sessionManager to be connected
  if (!sessionManager.isConnected) {
    try {
      await sessionManager.connect();
    } catch (err) {
      console.error('❌ User Message Queue: Redis connection failed:', err.message);
      return null;
    }
  }
  return sessionManager.client;
}

/**
 * Acquire a lock for processing a user's messages
 * Uses Redis SETNX for distributed locking
 *
 * @param {string} userKey - Unique key for user (phone + bpid)
 * @param {number} ttlMs - Lock timeout in milliseconds (default 60 seconds)
 * @returns {Promise<boolean>} - true if lock acquired, false otherwise
 */
export async function acquireUserLock(userKey, ttlMs = 60000) {
  try {
    const client = await getQueueClient();
    if (!client) {
      console.warn('⚠️ Queue Redis not available, proceeding without lock');
      return true; // Fallback: allow processing
    }

    const lockKey = `lock:user:${userKey}`;
    const lockValue = Date.now().toString();

    // SET NX with expiry - only sets if key doesn't exist
    const result = await client.set(lockKey, lockValue, {
      NX: true,
      PX: ttlMs
    });

    if (result === 'OK') {
      console.log(`🔒 Lock acquired for ${userKey}`);
      return true;
    } else {
      console.log(`⏳ Lock busy for ${userKey}, message will be queued`);
      return false;
    }
  } catch (err) {
    console.error('❌ Error acquiring lock:', err.message);
    return true; // Fallback: allow processing on error
  }
}

/**
 * Release a user's processing lock
 *
 * @param {string} userKey - Unique key for user (phone + bpid)
 */
export async function releaseUserLock(userKey) {
  try {
    const client = await getQueueClient();
    if (!client) return;

    const lockKey = `lock:user:${userKey}`;
    await client.del(lockKey);
    console.log(`🔓 Lock released for ${userKey}`);
  } catch (err) {
    console.error('❌ Error releasing lock:', err.message);
  }
}

/**
 * Add a message to the user's queue
 *
 * @param {string} userKey - Unique key for user (phone + bpid)
 * @param {object} messageData - The webhook request body to queue
 * @returns {Promise<number>} - Queue length after adding
 */
export async function queueMessage(userKey, messageData) {
  try {
    const client = await getQueueClient();
    if (!client) {
      console.warn('⚠️ Queue Redis not available, cannot queue message');
      return -1;
    }

    const queueKey = `queue:user:${userKey}`;
    const serialized = JSON.stringify(messageData);

    const length = await client.rPush(queueKey, serialized);
    // Set expiry on queue (1 hour) to prevent orphaned queues
    await client.expire(queueKey, 3600);

    console.log(`📥 Message queued for ${userKey}, queue length: ${length}`);
    return length;
  } catch (err) {
    console.error('❌ Error queueing message:', err.message);
    return -1;
  }
}

/**
 * Get the next message from the user's queue
 *
 * @param {string} userKey - Unique key for user (phone + bpid)
 * @returns {Promise<object|null>} - The next message or null if empty
 */
export async function dequeueMessage(userKey) {
  try {
    const client = await getQueueClient();
    if (!client) return null;

    const queueKey = `queue:user:${userKey}`;
    const serialized = await client.lPop(queueKey);

    if (serialized) {
      console.log(`📤 Message dequeued for ${userKey}`);
      return JSON.parse(serialized);
    }
    return null;
  } catch (err) {
    console.error('❌ Error dequeuing message:', err.message);
    return null;
  }
}

/**
 * Get the current queue length for a user
 *
 * @param {string} userKey - Unique key for user (phone + bpid)
 * @returns {Promise<number>} - Queue length
 */
export async function getQueueLength(userKey) {
  try {
    const client = await getQueueClient();
    if (!client) return 0;

    const queueKey = `queue:user:${userKey}`;
    return await client.lLen(queueKey);
  } catch (err) {
    console.error('❌ Error getting queue length:', err.message);
    return 0;
  }
}

/**
 * Check if a message ID has already been processed (deduplication)
 *
 * @param {string} messageId - WhatsApp message ID
 * @returns {Promise<boolean>} - true if already processed
 */
export async function isMessageProcessed(messageId) {
  try {
    const client = await getQueueClient();
    if (!client) return false;

    const key = `processed:msg:${messageId}`;
    const exists = await client.exists(key);
    return exists === 1;
  } catch (err) {
    console.error('❌ Error checking message processed:', err.message);
    return false;
  }
}

/**
 * Mark a message as processed (for deduplication)
 *
 * @param {string} messageId - WhatsApp message ID
 * @param {number} ttlSeconds - How long to remember (default 5 minutes)
 */
export async function markMessageProcessed(messageId, ttlSeconds = 300) {
  try {
    const client = await getQueueClient();
    if (!client) return;

    const key = `processed:msg:${messageId}`;
    await client.set(key, '1', { EX: ttlSeconds });
    console.log(`✓ Message ${messageId.substring(0, 20)}... marked as processed`);
  } catch (err) {
    console.error('❌ Error marking message processed:', err.message);
  }
}

/**
 * Process user messages with queue and locking
 * This is the main function to use in webhooks
 *
 * @param {string} userKey - Unique key for user (phone + bpid)
 * @param {string} messageId - WhatsApp message ID for deduplication
 * @param {object} requestBody - The webhook request body
 * @param {function} processFunction - Async function to process the message
 * @returns {Promise<{processed: boolean, queued: boolean, duplicate: boolean}>}
 */
export async function processWithQueue(userKey, messageId, requestBody, processFunction) {
  // Step 1: Check for duplicate message
  if (messageId) {
    const isDuplicate = await isMessageProcessed(messageId);
    if (isDuplicate) {
      console.log(`🔄 Duplicate message detected: ${messageId.substring(0, 20)}...`);
      return { processed: false, queued: false, duplicate: true };
    }
    // Mark as processed immediately to prevent race conditions
    await markMessageProcessed(messageId);
  }

  // Step 2: Try to acquire lock
  const lockAcquired = await acquireUserLock(userKey);

  if (!lockAcquired) {
    // Step 3a: Lock not acquired - queue the message
    await queueMessage(userKey, requestBody);
    return { processed: false, queued: true, duplicate: false };
  }

  try {
    // Step 3b: Lock acquired - process this message
    console.log(`🚀 Processing message for ${userKey}`);
    await processFunction(requestBody);

    // Step 4: Process any queued messages
    let queuedMessage = await dequeueMessage(userKey);
    while (queuedMessage) {
      console.log(`📨 Processing queued message for ${userKey}`);
      try {
        await processFunction(queuedMessage);
      } catch (queueErr) {
        console.error(`❌ Error processing queued message:`, queueErr.message);
      }
      queuedMessage = await dequeueMessage(userKey);
    }

    return { processed: true, queued: false, duplicate: false };
  } finally {
    // Step 5: Always release the lock
    await releaseUserLock(userKey);
  }
}

export default {
  acquireUserLock,
  releaseUserLock,
  queueMessage,
  dequeueMessage,
  getQueueLength,
  isMessageProcessed,
  markMessageProcessed,
  processWithQueue
};
