/**
 * Background Message Handlers (Phase 13.1 Section 5, 7, 8, 9, 12, 14)
 *
 * Coordinates extension actions without implementing intelligence logic:
 * - Status queries
 * - Content inspection requests (relayed to Unified Firewall API)
 * - Safe web app handoff
 */

import { backgroundState } from './state';
import { ExtensionApiClient, ExtensionApiClientError } from '../api/client';
import { getExtensionConfig, buildNiveshWebAppUrl } from '../config';
import { generateExtensionRequestId } from '../types/messages';
import type {
  ExtensionResponse,
  ScanRequestMessage,
  GetStatusMessage,
  OpenNiveshAppMessage,
  GetPageContextMessage,
  PageContextResponseMessage,
} from '../types/messages';
import type { ExtensionRuntimeState, LastAnalysisReference } from '../types/state';
import type { SafePageContext } from '../types/context';

const apiClient = new ExtensionApiClient();

/**
 * Handles GET_STATUS request from Popup or DevTools.
 */
export async function handleGetStatus(
  _message: GetStatusMessage
): Promise<ExtensionResponse<ExtensionRuntimeState>> {
  // Probe health in background if still connecting
  const current = backgroundState.getState();
  if (current.connectionState === 'CONNECTING') {
    const health = await apiClient.checkHealth(2500);
    backgroundState.setConnectionState(health.isAvailable ? 'CONNECTED' : 'UNAVAILABLE');
  }

  return {
    success: true,
    requestId: _message.requestId,
    data: backgroundState.getState(),
  };
}

/**
 * Handles SCAN_REQUEST from Popup.
 * 1. Coordinates request ID.
 * 2. Fetches safe page context from content script.
 * 3. Dispatches to Unified Firewall API.
 * 4. Records completion and returns decision reference.
 */
export async function handleScanRequest(
  message: ScanRequestMessage
): Promise<ExtensionResponse<LastAnalysisReference>> {
  const { tabId } = message.payload;
  const requestId = message.requestId || generateExtensionRequestId();

  // 1. Guard against concurrent duplicate scans
  const currentState = backgroundState.getState();
  if (currentState.status === 'ANALYZING') {
    return {
      success: false,
      requestId,
      error: {
        code: 'SCAN_IN_PROGRESS',
        message: 'An analysis is already in progress for this content.',
      },
    };
  }

  // 2. Fetch Safe Context from Content Script
  let pageContext: SafePageContext;
  try {
    pageContext = await fetchPageContextFromTab(tabId, requestId);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : 'Could not communicate with tab content script.';
    backgroundState.failRequest({ code: 'TAB_COMMUNICATION_FAILED', message: errorMsg });
    return {
      success: false,
      requestId,
      error: { code: 'TAB_COMMUNICATION_FAILED', message: errorMsg },
    };
  }

  // 3. Mark request started
  backgroundState.startRequest({
    requestId,
    tabId,
    startedAt: new Date().toISOString(),
    pageOrigin: pageContext.pageOrigin,
    pageUrl: pageContext.pageUrl,
  });

  // 4. Dispatch to Unified Firewall API (No client-side risk scoring)
  try {
    const analysisRef = await apiClient.analyze({
      input_type: pageContext.pageUrl ? 'url' : 'text',
      url: pageContext.pageUrl,
      text: pageContext.selectedText || pageContext.metaDescription || pageContext.pageTitle,
      channel: 'web',
      session_id: requestId,
    });

    backgroundState.completeRequest(analysisRef);
    return {
      success: true,
      requestId,
      data: analysisRef,
    };
  } catch (err) {
    let errorCode = 'PIPELINE_FAILURE';
    let errorMessage = 'Firewall analysis failed.';

    if (err instanceof ExtensionApiClientError) {
      errorCode = err.code;
      errorMessage = err.message;
    } else if (err instanceof Error) {
      errorMessage = err.message;
    }

    backgroundState.failRequest({ code: errorCode, message: errorMessage });
    return {
      success: false,
      requestId,
      error: { code: errorCode, message: errorMessage },
    };
  }
}

/**
 * Handles OPEN_NIVESH_APP request.
 * Opens the Nivesh Web Application in a new browser tab with the analysis_id reference.
 */
export async function handleOpenNiveshApp(
  message: OpenNiveshAppMessage
): Promise<ExtensionResponse<{ openedUrl: string }>> {
  const config = await getExtensionConfig();
  const targetUrl = buildNiveshWebAppUrl(config.webAppBaseUrl, message.payload.analysisId);

  if (typeof chrome !== 'undefined' && chrome.tabs && chrome.tabs.create) {
    await chrome.tabs.create({ url: targetUrl });
  }

  return {
    success: true,
    requestId: message.requestId,
    data: { openedUrl: targetUrl },
  };
}

/**
 * Helper: Sends message to tab content script to retrieve safe page context.
 */
export async function fetchPageContextFromTab(
  tabId: number,
  requestId: string
): Promise<SafePageContext> {
  if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.tabs.sendMessage) {
    // Non-browser fallback for unit testing
    return {
      pageUrl: 'https://example.com/test-financial-page',
      pageOrigin: 'https://example.com',
      pageTitle: 'Test Page',
      capturedAt: new Date().toISOString(),
    };
  }

  const queryMessage: GetPageContextMessage = {
    type: 'GET_PAGE_CONTEXT',
    requestId,
    tabId,
    timestamp: new Date().toISOString(),
    payload: { requestId },
  };

  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, queryMessage, (response: ExtensionResponse<PageContextResponseMessage['payload']>) => {
      if (chrome.runtime.lastError) {
        return reject(new Error(chrome.runtime.lastError.message || 'Content script unavailable.'));
      }
      if (!response || !response.success || !response.data) {
        return reject(new Error(response?.error?.message || 'Failed to extract context from tab.'));
      }
      resolve(response.data.context);
    });
  });
}
