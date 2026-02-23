import { client, messageQueue } from './queues/workerQueues.js';
import { io } from './server.js';

// ============================================================================
// CAMPAIGN STATE MANAGEMENT SERVICE
// ============================================================================
// This service handles:
// - Campaign state tracking (active/stopped/completed)
// - Progress counters (sent/failed/pending)
// - WebSocket real-time updates
// - Emergency HARD STOP capability
// ============================================================================

// In-memory fallback for local development (when Redis is not available)
const localCampaignState = new Map();
const localCampaignProgress = new Map();
const localCampaignMeta = new Map();
const localTenantCampaigns = new Map();
const localCampaignPhones = new Map();   // batchId -> Set of all target phones
const localCampaignSentPhones = new Map();   // batchId -> Set of sent phones
const localCampaignFailedPhones = new Map(); // batchId -> Set of failed phones

// TTL values (in seconds)
const STATE_TTL = 24 * 60 * 60;      // 24 hours
const PROGRESS_TTL = 24 * 60 * 60;   // 24 hours
const META_TTL = 7 * 24 * 60 * 60;   // 7 days

// Progress emit throttle - emit every N messages to reduce WebSocket traffic
const PROGRESS_EMIT_INTERVAL = 5;

/**
 * Initialize a new campaign for tracking
 * @param {string} batchId - Unique batch identifier
 * @param {object} metadata - Campaign metadata (tenantId, bpid, type, name, total)
 * @param {Array<string>} phoneNumbers - Optional list of target phone numbers for resume support
 */
export async function initializeCampaign(batchId, metadata, phoneNumbers = []) {
  const { tenantId, bpid, type, name, total } = metadata;

  const progress = {
    total: total || 0,
    sent: 0,
    failed: 0,
    pending: total || 0,
    startedAt: Date.now()
  };

  if (!client) {
    // Local development fallback
    localCampaignState.set(batchId, 'active');
    localCampaignProgress.set(batchId, progress);
    localCampaignMeta.set(batchId, { tenantId, bpid, type, name });

    // Store phone numbers for resume capability
    if (phoneNumbers.length > 0) {
      localCampaignPhones.set(batchId, new Set(phoneNumbers));
    }
    localCampaignSentPhones.set(batchId, new Set());
    localCampaignFailedPhones.set(batchId, new Set());

    // Track campaign for tenant
    const tenantKey = `${tenantId}:${bpid}`;
    if (!localTenantCampaigns.has(tenantKey)) {
      localTenantCampaigns.set(tenantKey, new Set());
    }
    localTenantCampaigns.get(tenantKey).add(batchId);

    console.log(`[CampaignControl] Campaign ${batchId} initialized (local mode)`);
  } else {
    try {
      const stateKey = `campaign:state:${batchId}`;
      const progressKey = `campaign:progress:${batchId}`;
      const metaKey = `campaign:meta:${batchId}`;
      const tenantKey = `tenant:campaigns:${tenantId}:${bpid}`;
      const phonesKey = `campaign:phones:${batchId}`;

      // Use pipeline for atomic operations
      const pipeline = client.multi();

      pipeline.set(stateKey, 'active', { EX: STATE_TTL });
      pipeline.hSet(progressKey, {
        total: String(progress.total),
        sent: '0',
        failed: '0',
        pending: String(progress.pending),
        startedAt: String(progress.startedAt)
      });
      pipeline.expire(progressKey, PROGRESS_TTL);
      pipeline.hSet(metaKey, { tenantId, bpid, type, name });
      pipeline.expire(metaKey, META_TTL);
      pipeline.sAdd(tenantKey, batchId);

      // Store phone numbers for resume capability
      if (phoneNumbers.length > 0) {
        pipeline.sAdd(phonesKey, phoneNumbers);
        pipeline.expire(phonesKey, META_TTL);
      }

      await pipeline.exec();

      console.log(`[CampaignControl] Campaign ${batchId} initialized in Redis`);
    } catch (err) {
      console.error(`[CampaignControl] Error initializing campaign ${batchId}:`, err);
      throw err;
    }
  }

  // Emit campaign started event via WebSocket
  emitCampaignEvent(batchId, 'campaign:started', {
    batchId,
    total: progress.total,
    type,
    name,
    startedAt: progress.startedAt
  });

  return { batchId, state: 'active', progress };
}

/**
 * Get current campaign state
 * @param {string} batchId - Campaign batch ID
 * @returns {Promise<string>} - State: 'active' | 'stopped' | 'completed' | null
 */
export async function getCampaignState(batchId) {
  if (!client) {
    return localCampaignState.get(batchId) || null;
  }

  try {
    const stateKey = `campaign:state:${batchId}`;
    return await client.get(stateKey);
  } catch (err) {
    console.error(`[CampaignControl] Error getting state for ${batchId}:`, err);
    return null;
  }
}

/**
 * Get campaign progress counters
 * @param {string} batchId - Campaign batch ID
 * @returns {Promise<object>} - Progress object with sent, failed, pending, total
 */
export async function getCampaignProgress(batchId) {
  if (!client) {
    return localCampaignProgress.get(batchId) || null;
  }

  try {
    const progressKey = `campaign:progress:${batchId}`;
    const data = await client.hGetAll(progressKey);

    if (!data || Object.keys(data).length === 0) {
      return null;
    }

    return {
      total: parseInt(data.total, 10) || 0,
      sent: parseInt(data.sent, 10) || 0,
      failed: parseInt(data.failed, 10) || 0,
      pending: parseInt(data.pending, 10) || 0,
      startedAt: parseInt(data.startedAt, 10) || 0
    };
  } catch (err) {
    console.error(`[CampaignControl] Error getting progress for ${batchId}:`, err);
    return null;
  }
}

/**
 * Get campaign metadata
 * @param {string} batchId - Campaign batch ID
 * @returns {Promise<object>} - Metadata object
 */
export async function getCampaignMeta(batchId) {
  if (!client) {
    return localCampaignMeta.get(batchId) || null;
  }

  try {
    const metaKey = `campaign:meta:${batchId}`;
    return await client.hGetAll(metaKey);
  } catch (err) {
    console.error(`[CampaignControl] Error getting meta for ${batchId}:`, err);
    return null;
  }
}

/**
 * HARD STOP a campaign - immediately prevents any further message sending
 * @param {string} batchId - Campaign batch ID
 * @param {string} reason - Reason for stopping
 * @returns {Promise<object>} - Final stats
 */
export async function stopCampaign(batchId, reason = 'User requested stop') {
  console.log(`[CampaignControl] HARD STOP requested for campaign ${batchId}: ${reason}`);

  let progress;
  let previousState;

  if (!client) {
    previousState = localCampaignState.get(batchId);
    progress = localCampaignProgress.get(batchId);

    if (previousState !== 'active') {
      return {
        success: false,
        error: `Campaign is not active (current state: ${previousState})`,
        stats: progress
      };
    }

    localCampaignState.set(batchId, 'stopped');

    if (progress) {
      progress.stoppedAt = Date.now();
      progress.stopReason = reason;
      localCampaignProgress.set(batchId, progress);
    }
  } else {
    try {
      const stateKey = `campaign:state:${batchId}`;
      const progressKey = `campaign:progress:${batchId}`;

      // Check current state
      previousState = await client.get(stateKey);

      if (previousState !== 'active') {
        progress = await getCampaignProgress(batchId);
        return {
          success: false,
          error: `Campaign is not active (current state: ${previousState})`,
          stats: progress
        };
      }

      // Atomically set state to stopped
      await client.set(stateKey, 'stopped', { EX: STATE_TTL });

      // Update progress with stop info
      await client.hSet(progressKey, {
        stoppedAt: String(Date.now()),
        stopReason: reason
      });

      progress = await getCampaignProgress(batchId);
    } catch (err) {
      console.error(`[CampaignControl] Error stopping campaign ${batchId}:`, err);
      throw err;
    }
  }

  const stats = {
    sent: progress?.sent || 0,
    failed: progress?.failed || 0,
    stopped: progress?.pending || 0,
    total: progress?.total || 0,
    stoppedAt: Date.now(),
    stopReason: reason
  };

  // Emit campaign stopped event via WebSocket
  emitCampaignEvent(batchId, 'campaign:stopped', {
    batchId,
    stats,
    reason
  });

  console.log(`[CampaignControl] Campaign ${batchId} STOPPED - sent: ${stats.sent}, stopped: ${stats.stopped}`);

  // Also try to remove pending jobs from Bull queue if available
  if (messageQueue) {
    try {
      const waitingJobs = await messageQueue.getWaiting();
      const delayedJobs = await messageQueue.getDelayed();
      const allPendingJobs = [...waitingJobs, ...delayedJobs];

      let removedCount = 0;
      for (const job of allPendingJobs) {
        if (job.data?.batchId === batchId) {
          await job.remove();
          removedCount++;
        }
      }

      if (removedCount > 0) {
        console.log(`[CampaignControl] Removed ${removedCount} pending jobs from Bull queue for ${batchId}`);
        stats.removedFromQueue = removedCount;
      }
    } catch (queueErr) {
      console.error(`[CampaignControl] Error removing jobs from queue:`, queueErr.message);
    }
  }

  return { success: true, stats };
}

/**
 * Increment a counter for the campaign (sent or failed)
 * @param {string} batchId - Campaign batch ID
 * @param {string} field - Field to increment: 'sent' | 'failed'
 * @param {string} phone - Optional phone number to track in sent/failed sets
 */
export async function incrementCounter(batchId, field, phone = null) {
  if (!['sent', 'failed'].includes(field)) {
    console.warn(`[CampaignControl] Invalid counter field: ${field}`);
    return;
  }

  if (!client) {
    const progress = localCampaignProgress.get(batchId);
    if (progress) {
      progress[field] = (progress[field] || 0) + 1;
      progress.pending = Math.max(0, progress.total - progress.sent - progress.failed);
      localCampaignProgress.set(batchId, progress);
    }
    // Track individual phone in local sets
    if (phone) {
      const setMap = field === 'sent' ? localCampaignSentPhones : localCampaignFailedPhones;
      if (!setMap.has(batchId)) setMap.set(batchId, new Set());
      setMap.get(batchId).add(phone);
    }
    return;
  }

  try {
    const progressKey = `campaign:progress:${batchId}`;

    // Increment the specified field and decrement pending
    const pipeline = client.multi();
    pipeline.hIncrBy(progressKey, field, 1);
    pipeline.hIncrBy(progressKey, 'pending', -1);

    // Track individual phone number in Redis set
    if (phone) {
      const phoneSetKey = `campaign:${field}:${batchId}`;
      pipeline.sAdd(phoneSetKey, phone);
      pipeline.expire(phoneSetKey, META_TTL);
    }

    await pipeline.exec();
  } catch (err) {
    console.error(`[CampaignControl] Error incrementing ${field} for ${batchId}:`, err);
  }
}

/**
 * Emit progress update via WebSocket
 * @param {string} batchId - Campaign batch ID
 * @param {boolean} force - Force emit even if not at interval
 */
export async function emitProgress(batchId, force = false) {
  const progress = await getCampaignProgress(batchId);

  if (!progress) return;

  // Throttle emissions unless forced
  const processed = progress.sent + progress.failed;
  if (!force && processed % PROGRESS_EMIT_INTERVAL !== 0 && processed < progress.total) {
    return;
  }

  const percentComplete = progress.total > 0
    ? Math.round((processed / progress.total) * 100)
    : 0;

  emitCampaignEvent(batchId, 'campaign:progress', {
    batchId,
    sent: progress.sent,
    failed: progress.failed,
    pending: progress.pending,
    total: progress.total,
    percentComplete
  });

  // Check if campaign is completed
  if (progress.pending <= 0) {
    await completeCampaign(batchId);
  }
}

/**
 * Mark campaign as completed
 * @param {string} batchId - Campaign batch ID
 */
async function completeCampaign(batchId) {
  const state = await getCampaignState(batchId);

  // Don't complete if already stopped
  if (state !== 'active') return;

  const progress = await getCampaignProgress(batchId);
  const meta = await getCampaignMeta(batchId);

  if (!client) {
    localCampaignState.set(batchId, 'completed');
    if (progress) {
      progress.completedAt = Date.now();
      localCampaignProgress.set(batchId, progress);
    }
  } else {
    try {
      const stateKey = `campaign:state:${batchId}`;
      const progressKey = `campaign:progress:${batchId}`;

      await client.set(stateKey, 'completed', { EX: STATE_TTL });
      await client.hSet(progressKey, 'completedAt', String(Date.now()));
    } catch (err) {
      console.error(`[CampaignControl] Error completing campaign ${batchId}:`, err);
    }
  }

  const duration = progress?.startedAt
    ? Date.now() - progress.startedAt
    : 0;

  emitCampaignEvent(batchId, 'campaign:completed', {
    batchId,
    stats: {
      sent: progress?.sent || 0,
      failed: progress?.failed || 0,
      total: progress?.total || 0
    },
    duration,
    name: meta?.name
  });

  console.log(`[CampaignControl] Campaign ${batchId} completed - sent: ${progress?.sent}, failed: ${progress?.failed}`);

  // Remove from tenant's active campaigns list
  if (meta?.tenantId && meta?.bpid) {
    await removeCampaignFromTenant(batchId, meta.tenantId, meta.bpid);
  }
}

/**
 * Remove campaign from tenant's active list
 */
async function removeCampaignFromTenant(batchId, tenantId, bpid) {
  if (!client) {
    const tenantKey = `${tenantId}:${bpid}`;
    if (localTenantCampaigns.has(tenantKey)) {
      localTenantCampaigns.get(tenantKey).delete(batchId);
    }
    return;
  }

  try {
    const tenantKey = `tenant:campaigns:${tenantId}:${bpid}`;
    await client.sRem(tenantKey, batchId);
  } catch (err) {
    console.error(`[CampaignControl] Error removing campaign from tenant list:`, err);
  }
}

/**
 * List active campaigns for a tenant/bpid
 * @param {string} tenantId - Tenant ID
 * @param {string} bpid - Business phone number ID
 * @returns {Promise<Array>} - List of active campaigns with details
 */
export async function listActiveCampaigns(tenantId, bpid) {
  const campaigns = [];

  if (!client) {
    const tenantKey = `${tenantId}:${bpid}`;
    const batchIds = localTenantCampaigns.get(tenantKey) || new Set();

    for (const batchId of batchIds) {
      const state = localCampaignState.get(batchId);
      // Show active AND stopped campaigns (so paused campaigns remain visible)
      if (state) {
        const progress = localCampaignProgress.get(batchId);
        const meta = localCampaignMeta.get(batchId);
        campaigns.push({
          batchId,
          state,
          progress,
          meta
        });
      }
    }
  } else {
    try {
      const tenantKey = `tenant:campaigns:${tenantId}:${bpid}`;
      const batchIds = await client.sMembers(tenantKey);

      for (const batchId of batchIds) {
        const state = await getCampaignState(batchId);

        // Only include active campaigns, or recently completed/stopped
        if (state) {
          const progress = await getCampaignProgress(batchId);
          const meta = await getCampaignMeta(batchId);
          campaigns.push({
            batchId,
            state,
            progress,
            meta
          });
        }
      }
    } catch (err) {
      console.error(`[CampaignControl] Error listing campaigns:`, err);
    }
  }

  return campaigns;
}

/**
 * Get full campaign status
 * @param {string} batchId - Campaign batch ID
 * @returns {Promise<object>} - Full campaign status
 */
export async function getCampaignStatus(batchId) {
  const state = await getCampaignState(batchId);
  const progress = await getCampaignProgress(batchId);
  const meta = await getCampaignMeta(batchId);

  if (!state) {
    return null;
  }

  const percentComplete = progress?.total > 0
    ? Math.round(((progress.sent + progress.failed) / progress.total) * 100)
    : 0;

  return {
    batchId,
    state,
    progress: {
      ...progress,
      percentComplete
    },
    meta
  };
}

/**
 * Helper to emit WebSocket events to campaign room
 * @param {string} batchId - Campaign batch ID
 * @param {string} event - Event name
 * @param {object} data - Event payload
 */
function emitCampaignEvent(batchId, event, data) {
  try {
    if (io) {
      io.to(`campaign:${batchId}`).emit(event, data);
      console.log(`[CampaignControl] Emitted ${event} for ${batchId}`);
    }
  } catch (err) {
    console.error(`[CampaignControl] Error emitting ${event}:`, err);
  }
}

/**
 * Get phone sets for a campaign (all phones, sent phones, failed phones)
 * @param {string} batchId - Campaign batch ID
 * @returns {Promise<object>} - { allPhones, sentPhones, failedPhones }
 */
export async function getCampaignPhones(batchId) {
  if (!client) {
    return {
      allPhones: localCampaignPhones.get(batchId) || new Set(),
      sentPhones: localCampaignSentPhones.get(batchId) || new Set(),
      failedPhones: localCampaignFailedPhones.get(batchId) || new Set()
    };
  }

  try {
    const phonesKey = `campaign:phones:${batchId}`;
    const sentKey = `campaign:sent:${batchId}`;
    const failedKey = `campaign:failed:${batchId}`;

    const [allPhones, sentPhones, failedPhones] = await Promise.all([
      client.sMembers(phonesKey),
      client.sMembers(sentKey),
      client.sMembers(failedKey)
    ]);

    return {
      allPhones: new Set(allPhones),
      sentPhones: new Set(sentPhones),
      failedPhones: new Set(failedPhones)
    };
  } catch (err) {
    console.error(`[CampaignControl] Error getting phones for ${batchId}:`, err);
    return { allPhones: new Set(), sentPhones: new Set(), failedPhones: new Set() };
  }
}

/**
 * Resume a stopped campaign
 * @param {string} batchId - Campaign batch ID
 * @returns {Promise<object>} - { success, unsentPhones, metadata }
 */
export async function resumeCampaign(batchId) {
  console.log(`[CampaignControl] Resume requested for campaign ${batchId}`);

  const currentState = await getCampaignState(batchId);
  if (currentState !== 'stopped') {
    return {
      success: false,
      error: `Campaign cannot be resumed (current state: ${currentState})`
    };
  }

  const { allPhones, sentPhones } = await getCampaignPhones(batchId);
  if (allPhones.size === 0) {
    return {
      success: false,
      error: 'No phone list stored for this campaign — cannot resume'
    };
  }

  // Compute unsent phones (all phones minus already-sent phones)
  const unsentPhones = [...allPhones].filter(p => !sentPhones.has(p));
  if (unsentPhones.length === 0) {
    return {
      success: false,
      error: 'All phones have already been sent — nothing to resume'
    };
  }

  const metadata = await getCampaignMeta(batchId);
  const progress = await getCampaignProgress(batchId);

  // Update state back to active
  if (!client) {
    localCampaignState.set(batchId, 'active');
    const localProgress = localCampaignProgress.get(batchId);
    if (localProgress) {
      localProgress.pending = unsentPhones.length;
      localProgress.total = (localProgress.sent || 0) + (localProgress.failed || 0) + unsentPhones.length;
      delete localProgress.stoppedAt;
      delete localProgress.stopReason;
      localCampaignProgress.set(batchId, localProgress);
    }
  } else {
    try {
      const stateKey = `campaign:state:${batchId}`;
      const progressKey = `campaign:progress:${batchId}`;
      const newTotal = (progress?.sent || 0) + (progress?.failed || 0) + unsentPhones.length;

      const pipeline = client.multi();
      pipeline.set(stateKey, 'active', { EX: STATE_TTL });
      pipeline.hSet(progressKey, {
        pending: String(unsentPhones.length),
        total: String(newTotal)
      });
      // Remove stop-related fields
      pipeline.hDel(progressKey, 'stoppedAt', 'stopReason');
      await pipeline.exec();
    } catch (err) {
      console.error(`[CampaignControl] Error resuming campaign ${batchId}:`, err);
      throw err;
    }
  }

  const newTotal = (progress?.sent || 0) + (progress?.failed || 0) + unsentPhones.length;

  // Emit campaign resumed event via WebSocket
  emitCampaignEvent(batchId, 'campaign:resumed', {
    batchId,
    unsentCount: unsentPhones.length,
    newTotal,
    name: metadata?.name
  });

  console.log(`[CampaignControl] Campaign ${batchId} RESUMED — ${unsentPhones.length} unsent phones`);

  return {
    success: true,
    unsentPhones,
    metadata,
    newTotal
  };
}

// Export all functions
export default {
  initializeCampaign,
  getCampaignState,
  getCampaignProgress,
  getCampaignMeta,
  stopCampaign,
  incrementCounter,
  emitProgress,
  listActiveCampaigns,
  getCampaignStatus,
  getCampaignPhones,
  resumeCampaign
};
