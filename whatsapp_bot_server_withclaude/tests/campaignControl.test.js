/**
 * Tests for campaignControl.js — campaign state management.
 * Uses local in-memory mode (client=null) so no Redis needed.
 */
import { jest } from '@jest/globals';

// Mock dependencies before importing the module
const mockIo = { to: jest.fn(() => ({ emit: jest.fn() })) };

jest.unstable_mockModule('../queues/workerQueues.js', () => ({
  client: null,        // Force local in-memory mode
  messageQueue: null,
}));

jest.unstable_mockModule('../server.js', () => ({
  io: mockIo,
}));

const {
  initializeCampaign,
  getCampaignState,
  getCampaignProgress,
  stopCampaign,
  incrementCounter,
  listActiveCampaigns,
  getCampaignStatus,
  getCampaignPhones,
  resumeCampaign,
} = await import('../campaignControl.js');


describe('Campaign Control (local mode)', () => {
  const TENANT = 'tenant_test';
  const BPID = '111222333';
  let batchCounter = 0;

  function uniqueBatchId() {
    return `batch_${Date.now()}_${++batchCounter}`;
  }

  // ────────────────────────────────────────────
  // Initialize
  // ────────────────────────────────────────────

  test('initializeCampaign sets active state', async () => {
    const batchId = uniqueBatchId();
    const result = await initializeCampaign(batchId, {
      tenantId: TENANT,
      bpid: BPID,
      type: 'broadcast',
      name: 'Test Campaign',
      total: 100,
    });
    expect(result.state).toBe('active');
    expect(result.progress.total).toBe(100);
    expect(result.progress.sent).toBe(0);

    const state = await getCampaignState(batchId);
    expect(state).toBe('active');
  });

  // ────────────────────────────────────────────
  // Stop
  // ────────────────────────────────────────────

  test('stopCampaign sets stopped state', async () => {
    const batchId = uniqueBatchId();
    await initializeCampaign(batchId, {
      tenantId: TENANT, bpid: BPID, type: 'broadcast', name: 'Stop Test', total: 50,
    });

    const result = await stopCampaign(batchId, 'user cancelled');
    expect(result.success).toBe(true);
    expect(result.stats.stopReason).toBe('user cancelled');

    const state = await getCampaignState(batchId);
    expect(state).toBe('stopped');
  });

  test('stop already-stopped campaign fails', async () => {
    const batchId = uniqueBatchId();
    await initializeCampaign(batchId, {
      tenantId: TENANT, bpid: BPID, type: 'broadcast', name: 'Double Stop', total: 10,
    });
    await stopCampaign(batchId);

    const result = await stopCampaign(batchId, 'try again');
    expect(result.success).toBe(false);
    expect(result.error).toMatch(/not active/i);
  });

  // ────────────────────────────────────────────
  // List Campaigns
  // ────────────────────────────────────────────

  test('listActiveCampaigns includes stopped campaigns (THE BUG FIX)', async () => {
    const batchId = uniqueBatchId();
    await initializeCampaign(batchId, {
      tenantId: 'list_tenant', bpid: 'list_bpid', type: 'broadcast', name: 'Visible', total: 5,
    });
    await stopCampaign(batchId);

    const campaigns = await listActiveCampaigns('list_tenant', 'list_bpid');
    const found = campaigns.find(c => c.batchId === batchId);
    expect(found).toBeDefined();
    expect(found.state).toBe('stopped');
  });

  test('listActiveCampaigns includes active campaigns', async () => {
    const batchId = uniqueBatchId();
    await initializeCampaign(batchId, {
      tenantId: 'active_list', bpid: 'active_bpid', type: 'broadcast', name: 'Active One', total: 20,
    });

    const campaigns = await listActiveCampaigns('active_list', 'active_bpid');
    expect(campaigns.length).toBeGreaterThanOrEqual(1);
    expect(campaigns.some(c => c.state === 'active')).toBe(true);
  });

  test('listActiveCampaigns empty for unknown tenant', async () => {
    const campaigns = await listActiveCampaigns('unknown_tenant', 'unknown_bpid');
    expect(campaigns).toEqual([]);
  });

  // ────────────────────────────────────────────
  // Progress Tracking
  // ────────────────────────────────────────────

  test('incrementCounter updates sent/failed counters', async () => {
    const batchId = uniqueBatchId();
    await initializeCampaign(batchId, {
      tenantId: TENANT, bpid: BPID, type: 'broadcast', name: 'Counter Test', total: 10,
    });

    await incrementCounter(batchId, 'sent', '91111');
    await incrementCounter(batchId, 'sent', '91222');
    await incrementCounter(batchId, 'failed', '91333');

    const progress = await getCampaignProgress(batchId);
    expect(progress.sent).toBe(2);
    expect(progress.failed).toBe(1);
    expect(progress.pending).toBe(7); // 10 - 2 - 1
  });

  // ────────────────────────────────────────────
  // Resume
  // ────────────────────────────────────────────

  test('resumeCampaign returns unsent phones', async () => {
    const phones = ['91001', '91002', '91003', '91004', '91005'];
    const batchId = uniqueBatchId();
    await initializeCampaign(batchId, {
      tenantId: TENANT, bpid: BPID, type: 'broadcast', name: 'Resume Test', total: 5,
    }, phones);

    // Simulate sending 2 messages
    await incrementCounter(batchId, 'sent', '91001');
    await incrementCounter(batchId, 'sent', '91002');

    await stopCampaign(batchId);

    const result = await resumeCampaign(batchId);
    expect(result.success).toBe(true);
    expect(result.unsentPhones).toHaveLength(3);
    expect(result.unsentPhones).toContain('91003');
    expect(result.unsentPhones).not.toContain('91001');
  });

  // ────────────────────────────────────────────
  // Isolation
  // ────────────────────────────────────────────

  test('campaign state isolation by tenant', async () => {
    const batchA = uniqueBatchId();
    const batchB = uniqueBatchId();

    await initializeCampaign(batchA, {
      tenantId: 'tenantA', bpid: 'bpidA', type: 'broadcast', name: 'A Campaign', total: 10,
    });
    await initializeCampaign(batchB, {
      tenantId: 'tenantB', bpid: 'bpidB', type: 'broadcast', name: 'B Campaign', total: 10,
    });

    const campaignsA = await listActiveCampaigns('tenantA', 'bpidA');
    const campaignsB = await listActiveCampaigns('tenantB', 'bpidB');

    // Tenant A should not see Tenant B's campaign
    expect(campaignsA.every(c => c.batchId !== batchB)).toBe(true);
    expect(campaignsB.every(c => c.batchId !== batchA)).toBe(true);
  });

  // ────────────────────────────────────────────
  // getCampaignStatus
  // ────────────────────────────────────────────

  test('getCampaignStatus returns null for unknown batch', async () => {
    const status = await getCampaignStatus('nonexistent_batch');
    expect(status).toBeNull();
  });
});
