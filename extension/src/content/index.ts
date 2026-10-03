/**
 * Content Script Entry Point (Phase 13.1 & 13.2)
 *
 * Responsibilities:
 * - Load safely without altering host page behavior.
 * - Establish typed message listener for background worker requests.
 * - Respond to selection checks (CHECK_SELECTION) to power popup UI state.
 * - Perform visible content and user-selected text extraction on demand (DO_CAPTURE).
 * - Strictly avoid silent page scraping, credential field reading, or background surveillance.
 */

import { extractSafePageContext } from './context';
import { extractUserSelection, extractVisiblePageText } from '../capture/extractor';
import { getSanitizedDisplayUrl } from '../capture/url';
import { protectionManager } from '../protection';
import type {
  ExtensionMessage,
  ExtensionResponse,
  PageContextResponsePayload,
  CheckSelectionResponsePayload,
  CaptureResponsePayload,
  DoCaptureMessage,
  ShowInterventionMessage,
} from '../types/messages';
import type { CapturePayload } from '../types/capture';

export function initializeContentScript(): void {
  if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.onMessage) {
    return;
  }

  chrome.runtime.onMessage.addListener(
    (message: ExtensionMessage, _sender, sendResponse: (response: ExtensionResponse) => void) => {
      // 1. GET_PAGE_CONTEXT (Phase 13.1 compatibility)
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
        return true;
      }

      // 2. CHECK_SELECTION (Phase 13.2)
      if (message.type === 'CHECK_SELECTION') {
        try {
          const result = extractUserSelection(window);
          const hasSelection = result.isValid && !!result.sanitizedText;
          const previewText = hasSelection ? result.sanitizedText!.slice(0, 100) : undefined;

          const response: ExtensionResponse<CheckSelectionResponsePayload> = {
            success: true,
            requestId: message.requestId,
            data: {
              hasSelection,
              length: result.sanitizedText ? result.sanitizedText.length : 0,
              previewText,
            },
          };
          sendResponse(response);
        } catch {
          sendResponse({
            success: true,
            requestId: message.requestId,
            data: { hasSelection: false },
          });
        }
        return true;
      }

      // 3. DO_CAPTURE (Phase 13.2 Page & Content Capture)
      if (message.type === 'DO_CAPTURE') {
        const doCaptureMsg = message as DoCaptureMessage;
        const { captureId, sourceType } = doCaptureMsg.payload;

        try {
          const currentUrl = window.location.href || '';
          const pageOrigin = window.location.origin || '';
          const pageTitle = (document.title || '').trim().slice(0, 500);
          const displayUrl = getSanitizedDisplayUrl(currentUrl);

          let capturePayload: CapturePayload;

          if (sourceType === 'SELECTED_TEXT') {
            const result = extractUserSelection(window);
            capturePayload = {
              captureId,
              sourceType: 'SELECTED_TEXT',
              status: result.status,
              text: result.sanitizedText,
              displayUrl,
              pageTitle,
              pageOrigin,
              timestamp: new Date().toISOString(),
              contentLength: result.sanitizedText ? result.sanitizedText.length : 0,
              sanitized: true,
              error: result.error,
            };
          } else if (sourceType === 'CURRENT_PAGE') {
            const result = extractVisiblePageText(document);
            capturePayload = {
              captureId,
              sourceType: 'CURRENT_PAGE',
              status: result.status,
              text: result.sanitizedText,
              url: currentUrl,
              displayUrl,
              pageTitle,
              pageOrigin,
              timestamp: new Date().toISOString(),
              contentLength: result.sanitizedText ? result.sanitizedText.length : 0,
              sanitized: true,
              error: result.error,
            };
          } else {
            // URL mode
            capturePayload = {
              captureId,
              sourceType: 'URL',
              status: 'CAPTURED',
              url: currentUrl,
              displayUrl,
              pageTitle,
              pageOrigin,
              timestamp: new Date().toISOString(),
              contentLength: currentUrl.length,
              sanitized: true,
            };
          }

          const response: ExtensionResponse<CaptureResponsePayload> = {
            success: capturePayload.status === 'CAPTURED',
            requestId: message.requestId,
            data: { capture: capturePayload },
            error:
              capturePayload.status !== 'CAPTURED'
                ? {
                    code: capturePayload.status,
                    message: capturePayload.error || 'Failed to capture content.',
                  }
                : undefined,
          };
          sendResponse(response);
        } catch (err) {
          sendResponse({
            success: false,
            requestId: message.requestId,
            error: {
              code: 'CAPTURE_FAILED',
              message: err instanceof Error ? err.message : 'Unexpected error during page capture.',
            },
          });
        }
        return true;
      }

      // 4. SHOW_INTERVENTION (Phase 13.4 In-Page Protection)
      if (message.type === 'SHOW_INTERVENTION') {
        try {
          const showMsg = message as ShowInterventionMessage;
          protectionManager.showIntervention(showMsg.payload);
          sendResponse({
            success: true,
            requestId: message.requestId,
            data: protectionManager.getState(),
          });
        } catch (err) {
          sendResponse({
            success: false,
            requestId: message.requestId,
            error: {
              code: 'INTERVENTION_FAILED',
              message: err instanceof Error ? err.message : 'Failed to display intervention.',
            },
          });
        }
        return true;
      }

      // 5. HIDE_INTERVENTION (Phase 13.4)
      if (message.type === 'HIDE_INTERVENTION') {
        protectionManager.hideIntervention();
        sendResponse({
          success: true,
          requestId: message.requestId,
          data: protectionManager.getState(),
        });
        return true;
      }

      // 6. GET_PROTECTION_STATE (Phase 13.4)
      if (message.type === 'GET_PROTECTION_STATE') {
        sendResponse({
          success: true,
          requestId: message.requestId,
          data: protectionManager.getState(),
        });
        return true;
      }

      return false;
    }
  );
}

// Auto-initialize when loaded in browser environment
if (typeof window !== 'undefined') {
  initializeContentScript();
}
