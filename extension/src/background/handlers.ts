/**
 * Background Message Handlers (Phase 13.1 & 13.2)
 *
 * Coordinates extension actions without implementing intelligence logic:
 * - Status queries
 * - Selection availability checks (CHECK_SELECTION)
 * - Page and content capture coordination (CAPTURE_REQUEST -> DO_CAPTURE)
 * - Content inspection requests (relayed to Unified Firewall API)
 * - Safe web app handoff
 */

import { backgroundState } from './state';
import { ExtensionApiClient, ExtensionApiClientError } from '../api/client';
import { analysisBridge } from '../bridge';
import type { BrowserAnalysisRequest } from '../bridge';
import { getExtensionConfig, buildNiveshWebAppUrl } from '../config';
import { generateExtensionRequestId } from '../types/messages';
import { generateCaptureId } from '../types/capture';
import { isUnsupportedPageUrl, getSanitizedDisplayUrl, isValidAnalysisUrl } from '../capture/url';
import type {
  ExtensionResponse,
  ScanRequestMessage,
  GetStatusMessage,
  OpenNiveshAppMessage,
  GetPageContextMessage,
  PageContextResponseMessage,
  CaptureRequestMessage,
  CaptureResponsePayload,
  DoCaptureMessage,
  CheckSelectionMessage,
  CheckSelectionResponsePayload,
} from '../types/messages';
import type { ExtensionRuntimeState, LastAnalysisReference } from '../types/state';
import type { SafePageContext } from '../types/context';
import type { CapturePayload, CaptureSourceType } from '../types/capture';

const apiClient = new ExtensionApiClient();

/**
 * Handles GET_STATUS request from Popup or DevTools.
 */
export async function handleGetStatus(
  _message: GetStatusMessage
): Promise<ExtensionResponse<ExtensionRuntimeState>> {
  const tabId = _message.payload?.tabId;
  // Probe health in background if still connecting
  const current = backgroundState.getState(tabId);
  if (current.connectionState === 'CONNECTING') {
    const health = await apiClient.checkHealth(2500);
    backgroundState.setConnectionState(health.isAvailable ? 'CONNECTED' : 'UNAVAILABLE');
  }

  return {
    success: true,
    requestId: _message.requestId,
    data: backgroundState.getState(tabId),
  };
}

/**
 * Handles CHECK_SELECTION request from Popup.
 */
export async function handleCheckSelection(
  message: CheckSelectionMessage
): Promise<ExtensionResponse<CheckSelectionResponsePayload>> {
  const tabId = message.payload.tabId;
  const requestId = message.requestId || generateExtensionRequestId();

  if (!tabId) {
    return {
      success: true,
      requestId,
      data: { hasSelection: false },
    };
  }

  return new Promise((resolve) => {
    if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.tabs.sendMessage) {
      return resolve({
        success: true,
        requestId,
        data: { hasSelection: false },
      });
    }

    const checkMsg: CheckSelectionMessage = {
      type: 'CHECK_SELECTION',
      requestId,
      tabId,
      timestamp: new Date().toISOString(),
      payload: { tabId },
    };

    chrome.tabs.sendMessage(tabId, checkMsg, (response: ExtensionResponse<CheckSelectionResponsePayload>) => {
      if (chrome.runtime.lastError || !response || !response.success || !response.data) {
        return resolve({
          success: true,
          requestId,
          data: { hasSelection: false },
        });
      }
      resolve(response);
    });
  });
}

/**
 * Handles CAPTURE_REQUEST from Popup (Phase 13.2).
 */
export async function handleCaptureRequest(
  message: CaptureRequestMessage
): Promise<ExtensionResponse<CaptureResponsePayload>> {
  const { tabId, sourceType } = message.payload;
  const requestId = message.requestId || generateExtensionRequestId();
  const captureId = message.payload.captureId || generateCaptureId();

  // 1. Inspect tab metadata
  let tabUrl = '';
  let tabTitle = '';
  if (typeof chrome !== 'undefined' && chrome.tabs && chrome.tabs.get) {
    try {
      const tab = await chrome.tabs.get(tabId);
      tabUrl = tab.url || '';
      tabTitle = tab.title || '';
    } catch {
      // Tab info query fallback
    }
  }

  // 2. Reject unsupported browser-internal pages
  if (isUnsupportedPageUrl(tabUrl)) {
    return {
      success: false,
      requestId,
      error: {
        code: 'UNSUPPORTED_PAGE',
        message: 'This page cannot be analyzed by the extension.',
      },
    };
  }

  // 3. Mode C: URL Capture directly from tab metadata
  if (sourceType === 'URL') {
    const validUrl = isValidAnalysisUrl(tabUrl);
    if (!validUrl.isValid) {
      return {
        success: false,
        requestId,
        error: {
          code: 'INVALID_URL',
          message: validUrl.error || 'The page URL cannot be analyzed.',
        },
      };
    }

    const capture: CapturePayload = {
      captureId,
      sourceType: 'URL',
      status: 'CAPTURED',
      url: tabUrl,
      displayUrl: getSanitizedDisplayUrl(tabUrl),
      pageTitle: tabTitle,
      pageOrigin: tabUrl ? new URL(tabUrl).origin : '',
      tabId,
      timestamp: new Date().toISOString(),
      contentLength: tabUrl.length,
      sanitized: true,
    };

    return {
      success: true,
      requestId,
      data: { capture },
    };
  }

  // 4. Mode A & B: Query Content Script on active tab
  return new Promise((resolve) => {
    if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.tabs.sendMessage) {
      // Unit testing fallback
      const mockCapture: CapturePayload = {
        captureId,
        sourceType,
        status: 'CAPTURED',
        text: 'Sample captured visible text for testing.',
        url: tabUrl || 'https://example.com',
        displayUrl: getSanitizedDisplayUrl(tabUrl || 'https://example.com'),
        pageTitle: tabTitle || 'Test Page',
        pageOrigin: 'https://example.com',
        tabId,
        timestamp: new Date().toISOString(),
        contentLength: 40,
        sanitized: true,
      };
      return resolve({
        success: true,
        requestId,
        data: { capture: mockCapture },
      });
    }

    const doCaptureMsg: DoCaptureMessage = {
      type: 'DO_CAPTURE',
      requestId,
      tabId,
      timestamp: new Date().toISOString(),
      payload: { captureId, sourceType },
    };

    chrome.tabs.sendMessage(tabId, doCaptureMsg, (response: ExtensionResponse<CaptureResponsePayload>) => {
      if (chrome.runtime.lastError) {
        return resolve({
          success: false,
          requestId,
          error: {
            code: 'TAB_COMMUNICATION_FAILED',
            message: chrome.runtime.lastError.message || 'Could not communicate with tab content script.',
          },
        });
      }

      if (!response || !response.success || !response.data) {
        return resolve({
          success: false,
          requestId,
          error: response?.error || {
            code: 'CAPTURE_FAILED',
            message: 'Content script failed to capture content.',
          },
        });
      }

      resolve(response);
    });
  });
}

/**
 * Handles SCAN_REQUEST from Popup.
 * 1. Coordinates request ID.
 * 2. Uses structured CapturePayload or fetches safe page context.
 * 3. Dispatches to Unified Firewall API.
 * 4. Records completion and returns Engine 8 decision reference.
 */
export async function handleScanRequest(
  message: ScanRequestMessage
): Promise<ExtensionResponse<LastAnalysisReference>> {
  const { tabId, capture } = message.payload;
  const requestId = message.requestId || generateExtensionRequestId();

  // 1. Guard against concurrent duplicate scans on this specific tab
  const currentState = backgroundState.getState(tabId);
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

  // 2. Prepare canonical bridge request parameters (Phase 13.3 Section 3 & 8)
  let sourceType: CaptureSourceType = capture?.sourceType || 'CURRENT_PAGE';
  let analyzeText: string | undefined;
  let analyzeUrl: string | undefined;
  let pageOrigin = '';
  let pageTitle = '';
  let captureId = capture?.captureId || generateCaptureId();

  if (capture) {
    pageOrigin = capture.pageOrigin;
    pageTitle = capture.pageTitle || '';
    analyzeUrl = capture.url;
    sourceType = capture.sourceType;
    if (sourceType === 'URL') {
      analyzeUrl = capture.url;
    } else {
      analyzeText = capture.text;
    }
  } else {
    // Phase 13.1 Fallback: Fetch safe context from tab
    let pageContext: SafePageContext;
    try {
      pageContext = await fetchPageContextFromTab(tabId, requestId);
      pageOrigin = pageContext.pageOrigin;
      pageTitle = pageContext.pageTitle || '';
      analyzeUrl = pageContext.pageUrl;
      analyzeText = pageContext.selectedText || pageContext.metaDescription || pageContext.pageTitle;
      sourceType = pageContext.selectedText ? 'SELECTED_TEXT' : 'CURRENT_PAGE';
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Could not communicate with tab content script.';
      backgroundState.failRequest({ code: 'TAB_COMMUNICATION_FAILED', message: errorMsg }, tabId);
      return {
        success: false,
        requestId,
        error: { code: 'TAB_COMMUNICATION_FAILED', message: errorMsg },
      };
    }
  }

  // 3. Attach tab-scoped session context (Phase 13.3 Section 5 & 29)
  const sessionId = backgroundState.getSessionIdForTab(tabId);

  const bridgeRequest: BrowserAnalysisRequest = {
    captureId,
    requestId,
    sessionId,
    sourceType,
    text: analyzeText,
    url: analyzeUrl,
    pageOrigin,
    pageTitle,
    tabId,
    timestamp: new Date().toISOString(),
  };

  // 4. Mark request started with correlation (Section 4)
  backgroundState.startRequest(
    {
      requestId,
      tabId,
      startedAt: new Date().toISOString(),
      pageOrigin,
      pageUrl: analyzeUrl || '',
    },
    sessionId
  );

  // 5. Dispatch via Nivesh Analysis Bridge (Unified Firewall API)
  try {
    const bridgeResult = await analysisBridge.submitAnalysis(bridgeRequest);

    backgroundState.completeRequest(bridgeResult.reference, tabId);

    // Phase 13.4: Dispatch in-page intervention to content script if decision is not ALLOW
    if (
      bridgeResult.reference.decision !== 'ALLOW' &&
      typeof chrome !== 'undefined' &&
      chrome.tabs &&
      chrome.tabs.sendMessage
    ) {
      try {
        chrome.tabs.sendMessage(
          tabId,
          {
            type: 'SHOW_INTERVENTION',
            requestId,
            tabId,
            timestamp: new Date().toISOString(),
            payload: {
              analysisId: bridgeResult.analysisId,
              decision: bridgeResult.reference.decision,
              severity: bridgeResult.reference.severity,
              primaryReason: bridgeResult.reference.primaryReason,
              userMessage: bridgeResult.reference.userMessage,
              claimsCount: bridgeResult.reference.claimsCount,
              evidenceStatus: bridgeResult.reference.evidenceStatus,
              identityStatus: bridgeResult.reference.identityStatus,
              fingerprintMatch: bridgeResult.reference.fingerprintMatch,
              threatSignalCount: bridgeResult.reference.threatSignalCount,
              webAppUrl: bridgeResult.reference.webAppUrl,
              targetUrl: bridgeRequest.url,
              sourceType: bridgeRequest.sourceType,
              actions: bridgeResult.fullResponse?.actions,
              timestamp: new Date().toISOString(),
            },
          },
          () => {
            if (chrome.runtime.lastError) {
              // Tab communication fallback
            }
          }
        );
      } catch {
        // Tab dispatch error fallback
      }
    }

    return {
      success: true,
      requestId,
      data: bridgeResult.reference,
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

    backgroundState.failRequest({ code: errorCode, message: errorMessage }, tabId);
    return {
      success: false,
      requestId,
      error: { code: errorCode, message: errorMessage },
    };
  }
}

/**
 * Handles OPEN_NIVESH_APP request.
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
