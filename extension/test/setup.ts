import { vi } from 'vitest';

// Chrome Mock Implementation for Browser Extension Testing
export function createChromeMock() {
  const listeners: Record<string, Function[]> = {
    'runtime.onMessage': [],
    'runtime.onInstalled': [],
    'tabs.onActivated': [],
    'tabs.onUpdated': [],
    'tabs.onRemoved': [],
  };

  const storageData: Record<string, unknown> = {};

  return {
    _listeners: listeners,
    runtime: {
      id: 'mock-extension-id-12345',
      lastError: null as { message: string } | null,
      onMessage: {
        addListener: vi.fn((callback: Function) => {
          listeners['runtime.onMessage'].push(callback);
        }),
        removeListener: vi.fn((callback: Function) => {
          listeners['runtime.onMessage'] = listeners['runtime.onMessage'].filter((cb) => cb !== callback);
        }),
        hasListener: vi.fn((callback: Function) => {
          return listeners['runtime.onMessage'].includes(callback);
        }),
      },
      onInstalled: {
        addListener: vi.fn((callback: Function) => {
          listeners['runtime.onInstalled'].push(callback);
        }),
      },
      sendMessage: vi.fn((message: unknown, responseCallback?: (response: unknown) => void) => {
        // Broadcast to runtime.onMessage listeners
        let responded = false;
        const sendResponse = (res: unknown) => {
          responded = true;
          if (responseCallback) responseCallback(res);
        };

        for (const listener of listeners['runtime.onMessage']) {
          const keepOpen = listener(message, { id: 'test-sender' }, sendResponse);
          if (keepOpen) break;
        }

        if (!responded && responseCallback) {
          responseCallback(null);
        }
      }),
    },
    tabs: {
      onActivated: {
        addListener: vi.fn((callback: Function) => {
          listeners['tabs.onActivated'].push(callback);
        }),
        removeListener: vi.fn((callback: Function) => {
          listeners['tabs.onActivated'] = listeners['tabs.onActivated'].filter((cb) => cb !== callback);
        }),
      },
      onUpdated: {
        addListener: vi.fn((callback: Function) => {
          listeners['tabs.onUpdated'].push(callback);
        }),
        removeListener: vi.fn((callback: Function) => {
          listeners['tabs.onUpdated'] = listeners['tabs.onUpdated'].filter((cb) => cb !== callback);
        }),
      },
      onRemoved: {
        addListener: vi.fn((callback: Function) => {
          listeners['tabs.onRemoved'].push(callback);
        }),
        removeListener: vi.fn((callback: Function) => {
          listeners['tabs.onRemoved'] = listeners['tabs.onRemoved'].filter((cb) => cb !== callback);
        }),
      },
      get: vi.fn().mockImplementation((id: number) =>
        Promise.resolve({
          id,
          url: 'https://bank-portal.example.com/dashboard',
          title: 'Secure Banking Dashboard',
        })
      ),
      query: vi.fn().mockResolvedValue([
        {
          id: 101,
          url: 'https://bank-portal.example.com/dashboard',
          title: 'Secure Banking Dashboard',
          active: true,
          currentWindow: true,
        },
      ]),
      sendMessage: vi.fn((_tabId: number, message: unknown, responseCallback?: (response: unknown) => void) => {
        if (!responseCallback) return;
        const msg = message as any;
        const reqId = msg?.requestId || 'EXT-TEST';

        if (msg?.type === 'CHECK_SELECTION') {
          return responseCallback({
            success: true,
            requestId: reqId,
            data: { hasSelection: true, length: 45, previewText: 'Test sample text' },
          });
        }

        if (msg?.type === 'DO_CAPTURE') {
          return responseCallback({
            success: true,
            requestId: reqId,
            data: {
              capture: {
                captureId: msg.payload?.captureId || 'CAP-MOCK-1',
                sourceType: msg.payload?.sourceType || 'SELECTED_TEXT',
                status: 'CAPTURED',
                text: 'Guaranteed 25% returns via Telegram robot.',
                url: 'https://bank-portal.example.com/dashboard',
                displayUrl: 'https://bank-portal.example.com/dashboard',
                pageTitle: 'Secure Banking Dashboard',
                pageOrigin: 'https://bank-portal.example.com',
                tabId: 101,
                timestamp: new Date().toISOString(),
                contentLength: 42,
                sanitized: true,
              },
            },
          });
        }

        if (msg?.type === 'SHOW_INTERVENTION') {
          return responseCallback({
            success: true,
            requestId: reqId,
            data: {
              active: true,
              decision: msg.payload?.decision,
              analysisId: msg.payload?.analysisId,
              targetUrl: msg.payload?.targetUrl,
              overridden: false,
            },
          });
        }

        if (msg?.type === 'HIDE_INTERVENTION') {
          return responseCallback({
            success: true,
            requestId: reqId,
            data: { active: false, decision: null, analysisId: null, overridden: false },
          });
        }

        if (msg?.type === 'GET_PROTECTION_STATE') {
          return responseCallback({
            success: true,
            requestId: reqId,
            data: { active: false, decision: null, analysisId: null, overridden: false },
          });
        }

        // Default GET_PAGE_CONTEXT response
        responseCallback({
          success: true,
          requestId: reqId,
          data: {
            context: {
              pageUrl: 'https://bank-portal.example.com/dashboard',
              pageOrigin: 'https://bank-portal.example.com',
              pageTitle: 'Secure Banking Dashboard',
              capturedAt: new Date().toISOString(),
            },
          },
        });
      }),
      create: vi.fn().mockResolvedValue({ id: 102 }),
    },
    storage: {
      local: {
        get: vi.fn((keys: string[] | null) => {
          if (!keys) return Promise.resolve({ ...storageData });
          const result: Record<string, unknown> = {};
          for (const key of keys) {
            if (key in storageData) {
              result[key] = storageData[key];
            }
          }
          return Promise.resolve(result);
        }),
        set: vi.fn((items: Record<string, unknown>) => {
          Object.assign(storageData, items);
          return Promise.resolve();
        }),
        remove: vi.fn((keys: string | string[]) => {
          const keyList = Array.isArray(keys) ? keys : [keys];
          for (const key of keyList) {
            delete storageData[key];
          }
          return Promise.resolve();
        }),
        clear: vi.fn(() => {
          for (const key of Object.keys(storageData)) {
            delete storageData[key];
          }
          return Promise.resolve();
        }),
      },
    },
  };
}

const mockChrome = createChromeMock();
(globalThis as any).chrome = mockChrome;
