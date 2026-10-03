import { describe, it, expect } from 'vitest';
import {
  generateExtensionRequestId,
  type ExtensionResponse,
  type ScanRequestMessage,
  type GetStatusMessage,
} from '../src/types/messages';

describe('Typed Message Contracts & Correlation (Phase 13.1 Sections 7, 8, 9)', () => {
  it('generates unique, correlated request identifiers with EXT- prefix', () => {
    const id1 = generateExtensionRequestId();
    const id2 = generateExtensionRequestId();

    expect(id1).toMatch(/^EXT-[A-Z0-9]+-[A-Z0-9]+$/);
    expect(id2).toMatch(/^EXT-[A-Z0-9]+-[A-Z0-9]+$/);
    expect(id1).not.toBe(id2);
  });

  it('generates multiple distinct correlation IDs concurrently', () => {
    const ids = new Set<string>();
    for (let i = 0; i < 100; i++) {
      ids.add(generateExtensionRequestId());
    }
    expect(ids.size).toBe(100);
  });

  it('constructs well-formed SCAN_REQUEST messages with correlation ID and tabId', () => {
    const reqId = generateExtensionRequestId();
    const message: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: reqId,
      tabId: 42,
      timestamp: new Date().toISOString(),
      payload: { tabId: 42, forceFresh: true },
    };

    expect(message.type).toBe('SCAN_REQUEST');
    expect(message.requestId).toBe(reqId);
    expect(message.payload.tabId).toBe(42);
    expect(message.payload.forceFresh).toBe(true);
    expect(new Date(message.timestamp).getTime()).not.toBeNaN();
  });

  it('constructs well-formed GET_STATUS messages', () => {
    const reqId = generateExtensionRequestId();
    const message: GetStatusMessage = {
      type: 'GET_STATUS',
      requestId: reqId,
      timestamp: new Date().toISOString(),
      payload: {},
    };

    expect(message.type).toBe('GET_STATUS');
    expect(message.requestId).toBe(reqId);
    expect(message.payload).toEqual({});
  });

  it('structures ExtensionResponse envelopes with explicit success, requestId, and data/error', () => {
    const reqId = generateExtensionRequestId();
    const successResponse: ExtensionResponse<{ count: number }> = {
      success: true,
      requestId: reqId,
      data: { count: 1 },
    };

    expect(successResponse.success).toBe(true);
    expect(successResponse.requestId).toBe(reqId);
    expect(successResponse.data?.count).toBe(1);
    expect(successResponse.error).toBeUndefined();

    const failureResponse: ExtensionResponse = {
      success: false,
      requestId: reqId,
      error: {
        code: 'BACKEND_UNAVAILABLE',
        message: 'Firewall service unreachable.',
      },
    };

    expect(failureResponse.success).toBe(false);
    expect(failureResponse.requestId).toBe(reqId);
    expect(failureResponse.error?.code).toBe('BACKEND_UNAVAILABLE');
    expect(failureResponse.error?.message).toContain('Firewall service');
  });
});
