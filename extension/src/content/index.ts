/**
 * Content Script Entry Point (Phase 13.1 Section 4)
 *
 * Responsibilities:
 * - Load safely without altering host page behavior.
 * - Establish typed message listener for background worker requests.
 * - Safely extract non-sensitive page context on explicit user command.
 * - Strictly avoid silent page scraping or credential field inspection.
 */

import { extractSafePageContext } from './context';
import type { ExtensionMessage, ExtensionResponse, PageContextResponsePayload } from '../types/messages';

export function initializeContentScript(): void {
  if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.onMessage) {
    return;
  }

  // Handle messages dispatched by the background worker
  chrome.runtime.onMessage.addListener(
    (message: ExtensionMessage, _sender, sendResponse: (response: ExtensionResponse) => void) => {
      if (message.type === 'GET_PAGE_CONTEXT') {
        try {
          const context = extractSafePageContext();
          const response: ExtensionResponse<PageContextResponsePayload> = {
            success: true,
            requestId: message.requestId,
            data: { context },
          };
          sendResponse(response);
        } catch (err) {
          sendResponse({
            success: false,
            requestId: message.requestId,
            error: {
              code: 'CONTEXT_EXTRACTION_FAILED',
              message: err instanceof Error ? err.message : 'Failed to extract page context.',
            },
          });
        }
        return true; // Keep channel open for asynchronous response
      }

      return false;
    }
  );
}

// Auto-initialize when loaded in browser environment
if (typeof window !== 'undefined') {
  initializeContentScript();
}
