import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { routeExtensionMessage } from '../src/background/router';
import { backgroundState } from '../src/background/state';
import { generateExtensionRequestId } from '../src/types/messages';
import { generateCaptureId, type CapturePayload } from '../src/types/capture';
import type {
  CaptureRequestMessage,
  CheckSelectionMessage,
  ScanRequestMessage,
} from '../src/types/messages';

describe('Capture Message Flow & End-to-End Correlation (Phase 13.2 Sections 19, 31, 36, 37)', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    backgroundState.reset();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('generates unique CAP- prefixed correlation identifiers', () => {
    const id1 = generateCaptureId();
    const id2 = generateCaptureId();

    expect(id1).toMatch(/^CAP-[A-Z0-9]+-[A-Z0-9]+$/);
    expect(id2).toMatch(/^CAP-[A-Z0-9]+-[A-Z0-9]+$/);
    expect(id1).not.toBe(id2);
  });

  it('handles CHECK_SELECTION and returns selection status for active tab', async () => {
    const reqId = generateExtensionRequestId();
    const msg: CheckSelectionMessage = {
      type: 'CHECK_SELECTION',
      requestId: reqId,
      timestamp: new Date().toISOString(),
      payload: { tabId: 101 },
    };

    const res = await routeExtensionMessage(msg);

    expect(res.success).toBe(true);
    expect(res.requestId).toBe(reqId);
    expect(res.data).toBeDefined();
  });

  it('handles CAPTURE_REQUEST for URL mode and creates sanitized CapturePayload', async () => {
    const reqId = generateExtensionRequestId();
    const capId = generateCaptureId();

    const msg: CaptureRequestMessage = {
      type: 'CAPTURE_REQUEST',
      requestId: reqId,
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: { tabId: 101, sourceType: 'URL', captureId: capId },
    };

    const res = await routeExtensionMessage(msg);

    expect(res.success).toBe(true);
    expect(res.requestId).toBe(reqId);
    const capture = (res.data as any).capture as CapturePayload;
    expect(capture.captureId).toBe(capId);
    expect(capture.sourceType).toBe('URL');
    expect(capture.status).toBe('CAPTURED');
    expect(capture.displayUrl).toBeDefined();
    expect(capture.sanitized).toBe(true);
  });

  it('handles CAPTURE_REQUEST for SELECTED_TEXT mode and queries content script', async () => {
    const reqId = generateExtensionRequestId();
    const capId = generateCaptureId();

    const msg: CaptureRequestMessage = {
      type: 'CAPTURE_REQUEST',
      requestId: reqId,
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: { tabId: 101, sourceType: 'SELECTED_TEXT', captureId: capId },
    };

    const res = await routeExtensionMessage(msg);

    expect(res.success).toBe(true);
    expect(res.requestId).toBe(reqId);
    const capture = (res.data as any).capture as CapturePayload;
    expect(capture.captureId).toBe(capId);
    expect(capture.sourceType).toBe('SELECTED_TEXT');
    expect(capture.status).toBe('CAPTURED');
  });

  it('submits pre-captured content to Unified Firewall API preserving capture correlation ID', async () => {
    const capId = 'CAP-TEST-SESSION-001';
    const reqId = 'EXT-TEST-REQ-001';

    const mockCapture: CapturePayload = {
      captureId: capId,
      sourceType: 'CURRENT_PAGE',
      status: 'CAPTURED',
      text: 'Guaranteed 40% returns on crypto cloud mining scheme.',
      url: 'https://crypto-scheme.example.com/mining',
      displayUrl: 'https://crypto-scheme.example.com/mining',
      pageTitle: 'Crypto Cloud Mining',
      pageOrigin: 'https://crypto-scheme.example.com',
      tabId: 101,
      timestamp: new Date().toISOString(),
      contentLength: 53,
      sanitized: true,
    };

    const mockBackendResponse = {
      analysis_id: 'ANA-CORRELATED-9988',
      completed_at: new Date().toISOString(),
      decision: {
        decision: 'WARN',
        severity: 'HIGH',
        primary_reason: 'Unrealistic return guarantees detected in promotional copy.',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockBackendResponse),
    } as Response);

    const scanMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: reqId,
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: mockCapture,
      },
    };

    const res = await routeExtensionMessage(scanMsg);

    expect(res.success).toBe(true);
    expect(res.requestId).toBe(reqId);
    expect((res.data as any).analysisId).toBe('ANA-CORRELATED-9988');
    expect((res.data as any).decision).toBe('WARN');

    // Verify correlation ID passed to Unified API session_id
    expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/firewall/analyze'),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining(capId),
      })
    );
  });

  it('prevents concurrent scans while an analysis is actively running', async () => {
    backgroundState.startRequest({
      requestId: 'EXT-EXISTING',
      tabId: 1,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://bank.com',
      pageUrl: 'https://bank.com',
    });

    const duplicateMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'EXT-DUP',
      tabId: 1,
      timestamp: new Date().toISOString(),
      payload: { tabId: 1 },
    };

    const res = await routeExtensionMessage(duplicateMsg);
    expect(res.success).toBe(false);
    expect(res.error?.code).toBe('SCAN_IN_PROGRESS');
  });
});
