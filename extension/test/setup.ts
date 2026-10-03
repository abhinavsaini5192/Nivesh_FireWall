import { vi } from 'vitest';

// Chrome Mock Implementation for Browser Extension Testing
export function createChromeMock() {
  const listeners: Record<string, Function[]> = {
    'runtime.onMessage': [],
    'runtime.onInstalled': [],
  };

  const storageData: Record<string, unknown> = {};

  return {
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
        if (responseCallback) {
          responseCallback({
            success: true,
            requestId: (message as any)?.requestId || 'EXT-TEST',
            data: {
              context: {
                pageUrl: 'https://bank-portal.example.com/dashboard',
                pageOrigin: 'https://bank-portal.example.com',
                pageTitle: 'Secure Banking Dashboard',
                capturedAt: new Date().toISOString(),
              },
            },
          });
        }
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
