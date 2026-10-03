import { describe, it, expect, vi, beforeEach } from 'vitest';
import { initializeContentScript } from '../src/content/index';

describe('Content Script Foundation & Tab Context Lifecycle (Phase 13.1 Sections 4, 10, 11)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('registers runtime message listener on initialization', () => {
    initializeContentScript();
    expect(chrome.runtime.onMessage.addListener).toHaveBeenCalled();
  });

  it('responds safely to GET_PAGE_CONTEXT messages with non-sensitive page context', () => {
    let capturedListener: Function | null = null;
    (chrome.runtime.onMessage.addListener as any).mockImplementation((cb: Function) => {
      capturedListener = cb;
    });

    initializeContentScript();
    expect(capturedListener).toBeDefined();

    // Simulate incoming GET_PAGE_CONTEXT message from background
    const mockSendResponse = vi.fn();
    const queryMessage = {
      type: 'GET_PAGE_CONTEXT',
      requestId: 'EXT-REQ-CONTEXT-01',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: { requestId: 'EXT-REQ-CONTEXT-01' },
    };

    const keepOpen = capturedListener!(queryMessage, { id: 'background' }, mockSendResponse);
    expect(keepOpen).toBe(true);

    expect(mockSendResponse).toHaveBeenCalledWith(
      expect.objectContaining({
        success: true,
        requestId: 'EXT-REQ-CONTEXT-01',
        data: expect.objectContaining({
          context: expect.objectContaining({
            capturedAt: expect.any(String),
          }),
        }),
      })
    );
  });

  it('ignores unrelated messages and returns false to close channel', () => {
    let capturedListener: Function | null = null;
    (chrome.runtime.onMessage.addListener as any).mockImplementation((cb: Function) => {
      capturedListener = cb;
    });

    initializeContentScript();
    const mockSendResponse = vi.fn();

    const unrelatedMessage = {
      type: 'UNRELATED_EVENT',
      requestId: 'EXT-OTHER',
      timestamp: new Date().toISOString(),
      payload: {},
    };

    const keepOpen = capturedListener!(unrelatedMessage, { id: 'background' }, mockSendResponse);
    expect(keepOpen).toBe(false);
    expect(mockSendResponse).not.toHaveBeenCalled();
  });
});
