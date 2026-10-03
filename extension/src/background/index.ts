/**
 * Background Service Worker Entry Point (Phase 13.1 Section 5)
 *
 * Coordinates extension lifecycle, message dispatching, and health telemetry.
 */

import { routeExtensionMessage } from './router';
import { backgroundState } from './state';
import { ExtensionApiClient } from '../api/client';
import { DEFAULT_CONFIG } from '../config';
import type { ExtensionMessage, ExtensionResponse } from '../types/messages';

const apiClient = new ExtensionApiClient();

/**
 * Initializes the background service worker lifecycle listeners.
 */
export function initializeBackgroundWorker(): void {
  if (typeof chrome === 'undefined' || !chrome.runtime) {
    return;
  }

  // 1. Extension Installation / Update Handler
  chrome.runtime.onInstalled?.addListener((details) => {
    if (details.reason === 'install') {
      // Seed default configuration safely
      chrome.storage.local.set({ config: DEFAULT_CONFIG });
    }
    backgroundState.reset();
  });

  // 2. Central Message Listener
  chrome.runtime.onMessage.addListener(
    (message: ExtensionMessage, _sender, sendResponse: (response: ExtensionResponse) => void) => {
      routeExtensionMessage(message)
        .then((response) => sendResponse(response))
        .catch((err) => {
          sendResponse({
            success: false,
            requestId: message?.requestId || 'UNKNOWN',
            error: {
              code: 'BACKGROUND_ROUTER_ERROR',
              message: err instanceof Error ? err.message : 'Unexpected background error.',
            },
          });
        });

      return true; // Keep asynchronous message channel open
    }
  );

  // 3. Initial Health Check Probe
  apiClient.checkHealth(3000).then((health) => {
    backgroundState.setConnectionState(health.isAvailable ? 'CONNECTED' : 'UNAVAILABLE');
  });
}

// Auto-initialize when executing in service worker scope
if (typeof self !== 'undefined' && 'ServiceWorkerGlobalScope' in self) {
  initializeBackgroundWorker();
}
