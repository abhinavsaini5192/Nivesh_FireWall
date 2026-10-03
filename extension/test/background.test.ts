import { describe, it, expect, vi, beforeEach } from 'vitest';
import { backgroundState } from '../src/background/state';
import { routeExtensionMessage } from '../src/background/router';
import {
  type GetStatusMessage,
  type ScanRequestMessage,
  type OpenNiveshAppMessage,
  generateExtensionRequestId,
} from '../src/types/messages';

describe('Background Service Worker & State Coordination (Phase 13.1 Sections 5, 8, 9, 10, 16, 17)', () => {
  beforeEach(() => {
    backgroundState.reset();
    vi.restoreAllMocks();
  });

  it('initializes with clean runtime state without residual analysis', () => {
    const state = backgroundState.getState();
    expect(state.status).toBe('READY');
    expect(state.activeRequest).toBeNull();
    expect(state.lastError).toBeNull();
  });

  it('transitions state cleanly on startRequest, completeRequest, and failRequest', () => {
    const reqId = generateExtensionRequestId();

    // 1. Start Request
    backgroundState.startRequest({
      requestId: reqId,
      tabId: 101,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://test-fund.com',
      pageUrl: 'https://test-fund.com/invest',
    });

    let state = backgroundState.getState();
    expect(state.status).toBe('ANALYZING');
    expect(state.activeRequest?.requestId).toBe(reqId);
    expect(state.activeRequest?.tabId).toBe(101);

    // 2. Complete Request
    backgroundState.completeRequest({
      analysisId: 'ANA-9900',
      decision: 'WARN',
      severity: 'HIGH',
      primaryReason: 'Guaranteed return scheme detected.',
      completedAt: new Date().toISOString(),
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-9900',
    });

    state = backgroundState.getState();
    expect(state.status).toBe('RESULT_AVAILABLE');
    expect(state.activeRequest).toBeNull();
    expect(state.lastAnalysis?.analysisId).toBe('ANA-9900');
    expect(state.lastAnalysis?.decision).toBe('WARN');

    // 3. Fail Request
    backgroundState.failRequest({
      code: 'BACKEND_UNAVAILABLE',
      message: 'Service down.',
    });

    state = backgroundState.getState();
    expect(state.status).toBe('ERROR');
    expect(state.activeRequest).toBeNull();
    expect(state.lastError?.code).toBe('BACKEND_UNAVAILABLE');
  });

  it('routes GET_STATUS message and returns current state', async () => {
    const reqId = generateExtensionRequestId();
    const message: GetStatusMessage = {
      type: 'GET_STATUS',
      requestId: reqId,
      timestamp: new Date().toISOString(),
      payload: {},
    };

    const response = await routeExtensionMessage(message);

    expect(response.success).toBe(true);
    expect(response.requestId).toBe(reqId);
    expect(response.data).toBeDefined();
    expect((response.data as any).status).toBe('READY');
  });

  it('prevents concurrent scans when an analysis is already in progress', async () => {
    backgroundState.startRequest({
      requestId: 'EXT-EXISTING-REQ',
      tabId: 1,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://bank.com',
      pageUrl: 'https://bank.com',
    });

    const duplicateMessage: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'EXT-NEW-REQ',
      tabId: 1,
      timestamp: new Date().toISOString(),
      payload: { tabId: 1 },
    };

    const response = await routeExtensionMessage(duplicateMessage);

    expect(response.success).toBe(false);
    expect(response.error?.code).toBe('SCAN_IN_PROGRESS');
    expect(response.error?.message).toContain('already in progress');
  });

  it('handles OPEN_NIVESH_APP message and dispatches chrome.tabs.create with deep link', async () => {
    const reqId = generateExtensionRequestId();
    const message: OpenNiveshAppMessage = {
      type: 'OPEN_NIVESH_APP',
      requestId: reqId,
      timestamp: new Date().toISOString(),
      payload: { analysisId: 'ANA-DEEP-LINK-101' },
    };

    const response = await routeExtensionMessage(message);

    expect(response.success).toBe(true);
    expect(response.requestId).toBe(reqId);
    expect((response.data as any).openedUrl).toContain('#protect?id=ANA-DEEP-LINK-101');
    expect(chrome.tabs.create).toHaveBeenCalledWith(
      expect.objectContaining({
        url: expect.stringContaining('#protect?id=ANA-DEEP-LINK-101'),
      })
    );
  });

  it('returns clean error envelope for unsupported or malformed message types', async () => {
    const badMessage: any = {
      type: 'UNKNOWN_ACTION',
      requestId: 'EXT-BAD-001',
      payload: {},
    };

    const response = await routeExtensionMessage(badMessage);

    expect(response.success).toBe(false);
    expect(response.error?.code).toBe('UNSUPPORTED_MESSAGE_TYPE');
    expect(response.error?.message).toContain('UNKNOWN_ACTION');
  });

  it('verifies background worker never computes threat or policy scores locally', () => {
    // Structural integrity test: backgroundState strictly holds references, not intelligence logic
    const state = backgroundState.getState();
    expect((state as any).threatScore).toBeUndefined();
    expect((state as any).isScam).toBeUndefined();
    expect((state as any).phishingProbability).toBeUndefined();
  });
});
