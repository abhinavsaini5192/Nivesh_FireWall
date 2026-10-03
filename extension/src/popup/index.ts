/**
 * Extension Popup Controller (Phase 13.1 & 13.2)
 *
 * User-initiated analysis with three explicit capture modes:
 * - Selected text
 * - Current visible page text
 * - Current URL
 *
 * Provides a compact preview prior to submission, supports cancellation,
 * and detects unsupported internal browser pages.
 *
 * Security: Uses textContent exclusively for user/page content to prevent XSS.
 */

import { generateExtensionRequestId } from '../types/messages';
import { isUnsupportedPageUrl, getSanitizedDisplayUrl } from '../capture/url';
import type {
  ExtensionResponse,
  GetStatusMessage,
  ScanRequestMessage,
  OpenNiveshAppMessage,
  CaptureRequestMessage,
  CaptureResponsePayload,
  CheckSelectionMessage,
  CheckSelectionResponsePayload,
} from '../types/messages';
import type { ExtensionRuntimeState, LastAnalysisReference } from '../types/state';
import type { CapturePayload, CaptureSourceType } from '../types/capture';

// DOM Element References
const connectionDot = document.getElementById('connection-dot') as HTMLSpanElement;
const connectionText = document.getElementById('connection-text') as HTMLSpanElement;
const targetDomainEl = document.getElementById('target-domain') as HTMLDivElement;
const targetUrlEl = document.getElementById('target-url') as HTMLDivElement;
const unsupportedBox = document.getElementById('unsupported-box') as HTMLDivElement;
const errorBox = document.getElementById('error-box') as HTMLDivElement;

const viewReady = document.getElementById('view-ready') as HTMLDivElement;
const viewPreview = document.getElementById('view-preview') as HTMLDivElement;
const viewAnalyzing = document.getElementById('view-analyzing') as HTMLDivElement;
const viewResult = document.getElementById('view-result') as HTMLDivElement;

// Action Buttons
const btnScanSelection = document.getElementById('btn-scan-selection') as HTMLButtonElement;
const selectionHint = document.getElementById('selection-hint') as HTMLSpanElement;
const btnScanPage = document.getElementById('btn-scan-page') as HTMLButtonElement;
const btnScanUrl = document.getElementById('btn-scan-url') as HTMLButtonElement;

// Preview Elements
const previewBadge = document.getElementById('preview-badge') as HTMLSpanElement;
const previewSnippet = document.getElementById('preview-snippet') as HTMLElement;
const previewLength = document.getElementById('preview-length') as HTMLSpanElement;
const previewOrigin = document.getElementById('preview-origin') as HTMLSpanElement;
const btnConfirmAnalyze = document.getElementById('btn-confirm-analyze') as HTMLButtonElement;
const btnCancelPreview = document.getElementById('btn-cancel-preview') as HTMLButtonElement;
const btnCancelAnalyzing = document.getElementById('btn-cancel-analyzing') as HTMLButtonElement;

// Result Elements
const btnOpenApp = document.getElementById('btn-open-app') as HTMLButtonElement;
const btnRescan = document.getElementById('btn-rescan') as HTMLButtonElement;
const linkWebApp = document.getElementById('link-web-app') as HTMLAnchorElement;

const decisionCard = document.getElementById('decision-card') as HTMLDivElement;
const decisionBadge = document.getElementById('decision-badge') as HTMLSpanElement;
const analysisIdBadge = document.getElementById('analysis-id-badge') as HTMLSpanElement;
const decisionReason = document.getElementById('decision-reason') as HTMLParagraphElement;

let currentTabId: number | null = null;
let currentAnalysisId: string | undefined;
let activeCapture: CapturePayload | null = null;
let isPageSupported = true;

/**
 * Updates connection indicator in popup header.
 */
function updateConnectionUI(state: ExtensionRuntimeState['connectionState']): void {
  connectionDot.className = `dot ${state.toLowerCase()}`;
  switch (state) {
    case 'CONNECTED':
      connectionText.textContent = 'Active';
      break;
    case 'CONNECTING':
      connectionText.textContent = 'Checking...';
      break;
    case 'UNAVAILABLE':
    default:
      connectionText.textContent = 'Offline';
      break;
  }
}

/**
 * Transitions the popup view between READY, PREVIEW, ANALYZING, and RESULT.
 */
function transitionView(view: 'ready' | 'preview' | 'analyzing' | 'result'): void {
  viewReady.style.display = view === 'ready' ? 'flex' : 'none';
  viewPreview.style.display = view === 'preview' ? 'flex' : 'none';
  viewAnalyzing.style.display = view === 'analyzing' ? 'flex' : 'none';
  viewResult.style.display = view === 'result' ? 'flex' : 'none';
  hideError();
}

function showError(message: string): void {
  errorBox.textContent = message;
  errorBox.style.display = 'block';
}

function hideError(): void {
  errorBox.textContent = '';
  errorBox.style.display = 'none';
}

/**
 * Enables or disables capture buttons during active operations.
 */
function setCaptureControlsDisabled(disabled: boolean): void {
  btnScanSelection.disabled = disabled;
  btnScanPage.disabled = disabled;
  btnScanUrl.disabled = disabled;
}

/**
 * Renders an Engine 8 analysis result into the result card.
 */
function renderAnalysisResult(reference: LastAnalysisReference): void {
  currentAnalysisId = reference.analysisId;

  decisionBadge.textContent = reference.decision;
  analysisIdBadge.textContent = reference.analysisId;
  decisionReason.textContent = reference.primaryReason;

  decisionCard.className = `decision-card ${reference.decision}`;
  transitionView('result');
}

/**
 * Sends a typed message to the background service worker.
 */
async function sendMessageToBackground<T>(message: unknown): Promise<ExtensionResponse<T>> {
  if (typeof chrome === 'undefined' || !chrome.runtime || !chrome.runtime.sendMessage) {
    throw new Error('Chrome runtime messaging is unavailable.');
  }

  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response: ExtensionResponse<T>) => {
      if (chrome.runtime.lastError) {
        return reject(new Error(chrome.runtime.lastError.message || 'Background worker error.'));
      }
      resolve(response);
    });
  });
}

/**
 * Checks whether user has an active text selection on the current page.
 */
async function checkActiveSelection(): Promise<void> {
  if (!currentTabId || !isPageSupported) {
    btnScanSelection.disabled = true;
    selectionHint.style.display = 'block';
    return;
  }

  const requestId = generateExtensionRequestId();
  const checkMsg: CheckSelectionMessage = {
    type: 'CHECK_SELECTION',
    requestId,
    timestamp: new Date().toISOString(),
    payload: { tabId: currentTabId },
  };

  try {
    const res = await sendMessageToBackground<CheckSelectionResponsePayload>(checkMsg);
    if (res.success && res.data?.hasSelection) {
      btnScanSelection.disabled = false;
      selectionHint.style.display = 'none';
    } else {
      btnScanSelection.disabled = true;
      selectionHint.style.display = 'block';
    }
  } catch {
    btnScanSelection.disabled = true;
    selectionHint.style.display = 'block';
  }
}

/**
 * Fetches the active tab and checks eligibility.
 */
async function loadActiveTabContext(): Promise<void> {
  if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.tabs.query) {
    targetDomainEl.textContent = 'localhost (Test)';
    targetUrlEl.textContent = 'http://localhost:5173';
    isPageSupported = true;
    return;
  }

  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const activeTab = tabs[0];
    if (activeTab && activeTab.id) {
      currentTabId = activeTab.id;
      const tabUrl = activeTab.url || '';

      if (isUnsupportedPageUrl(tabUrl)) {
        isPageSupported = false;
        targetDomainEl.textContent = 'Browser Internal Page';
        targetUrlEl.textContent = tabUrl;
        unsupportedBox.style.display = 'block';
        setCaptureControlsDisabled(true);
        return;
      }

      isPageSupported = true;
      unsupportedBox.style.display = 'none';

      try {
        const parsed = new URL(tabUrl);
        targetDomainEl.textContent = parsed.hostname;
        targetUrlEl.textContent = getSanitizedDisplayUrl(tabUrl);
      } catch {
        targetDomainEl.textContent = activeTab.title || 'Current Page';
        targetUrlEl.textContent = tabUrl;
      }
    }
  } catch (err) {
    targetDomainEl.textContent = 'Active tab unavailable';
    showError(err instanceof Error ? err.message : 'Could not query current tab.');
  }
}

/**
 * Initiates content capture for a chosen mode (SELECTED_TEXT, CURRENT_PAGE, URL).
 */
async function handleTriggerCapture(sourceType: CaptureSourceType): Promise<void> {
  if (!currentTabId) {
    showError('No active browser tab found to inspect.');
    return;
  }

  if (!isPageSupported) {
    showError('This page cannot be analyzed by the extension.');
    return;
  }

  hideError();
  setCaptureControlsDisabled(true);

  const requestId = generateExtensionRequestId();
  const captureReqMsg: CaptureRequestMessage = {
    type: 'CAPTURE_REQUEST',
    requestId,
    tabId: currentTabId,
    timestamp: new Date().toISOString(),
    payload: { tabId: currentTabId, sourceType },
  };

  try {
    const response = await sendMessageToBackground<CaptureResponsePayload>(captureReqMsg);
    setCaptureControlsDisabled(false);

    if (response.success && response.data?.capture) {
      const capture = response.data.capture;
      activeCapture = capture;

      // Render Compact Preview (Phase 13.2 Section 25)
      let sourceLabel = 'Webpage Content';
      if (sourceType === 'SELECTED_TEXT') sourceLabel = 'Selected Text';
      if (sourceType === 'URL') sourceLabel = 'Page URL';
      previewBadge.textContent = sourceLabel;

      const previewText = capture.text || capture.url || '';
      const displaySnippet = previewText.length > 200 ? `${previewText.slice(0, 197)}...` : previewText;
      previewSnippet.textContent = displaySnippet || '(No content)';

      previewLength.textContent = `${capture.contentLength} characters`;
      previewOrigin.textContent = capture.displayUrl || capture.pageOrigin;

      transitionView('preview');
    } else {
      const code = response.error?.code || 'CAPTURE_FAILED';
      const msg = response.error?.message || 'Could not capture content.';
      if (code === 'NO_SELECTION') {
        showError('No text is selected. Highlight text on the page or choose "Analyze Current Page".');
      } else if (code === 'CONTENT_TOO_LARGE') {
        showError('Selected content exceeds size limits. Please select a smaller passage.');
      } else {
        showError(msg);
      }
      transitionView('ready');
    }
  } catch (err) {
    setCaptureControlsDisabled(false);
    showError(err instanceof Error ? err.message : 'Failed to capture page content.');
    transitionView('ready');
  }
}

/**
 * Confirms analysis from the Preview step and dispatches to backend.
 */
async function handleConfirmAnalysis(): Promise<void> {
  if (!currentTabId || !activeCapture) {
    transitionView('ready');
    return;
  }

  transitionView('analyzing');
  hideError();

  const requestId = generateExtensionRequestId();
  const scanMsg: ScanRequestMessage = {
    type: 'SCAN_REQUEST',
    requestId,
    tabId: currentTabId,
    timestamp: new Date().toISOString(),
    payload: {
      tabId: currentTabId,
      forceFresh: true,
      capture: activeCapture,
    },
  };

  try {
    const response = await sendMessageToBackground<LastAnalysisReference>(scanMsg);
    if (response.success && response.data) {
      renderAnalysisResult(response.data);
    } else {
      showError(response.error?.message || 'Inspection failed.');
      transitionView('ready');
    }
  } catch (err) {
    showError(err instanceof Error ? err.message : 'Failed to communicate with Firewall service.');
    transitionView('ready');
  }
}

/**
 * Syncs initial state with background service worker.
 */
async function syncStatus(): Promise<void> {
  const requestId = generateExtensionRequestId();
  const message: GetStatusMessage = {
    type: 'GET_STATUS',
    requestId,
    timestamp: new Date().toISOString(),
    payload: { tabId: currentTabId || undefined },
  };

  try {
    const response = await sendMessageToBackground<ExtensionRuntimeState>(message);
    if (response.success && response.data) {
      const state = response.data;
      updateConnectionUI(state.connectionState);

      if (state.status === 'ANALYZING') {
        transitionView('analyzing');
      } else if (state.status === 'RESULT_AVAILABLE' && state.lastAnalysis) {
        renderAnalysisResult(state.lastAnalysis);
      } else if (state.status === 'ERROR' && state.lastError) {
        showError(state.lastError.message);
        transitionView('ready');
      } else {
        transitionView('ready');
      }
    }
  } catch {
    updateConnectionUI('UNAVAILABLE');
    transitionView('ready');
  }
}

/**
 * Opens full analysis in Nivesh Web Application.
 */
async function handleOpenAppClick(): Promise<void> {
  const requestId = generateExtensionRequestId();
  const openMsg: OpenNiveshAppMessage = {
    type: 'OPEN_NIVESH_APP',
    requestId,
    timestamp: new Date().toISOString(),
    payload: { analysisId: currentAnalysisId },
  };

  try {
    await sendMessageToBackground(openMsg);
    window.close();
  } catch (err) {
    showError(err instanceof Error ? err.message : 'Could not open Nivesh Web App.');
  }
}

// Bind Listeners
document.addEventListener('DOMContentLoaded', async () => {
  await loadActiveTabContext();
  await checkActiveSelection();
  await syncStatus();

  btnScanSelection.addEventListener('click', () => handleTriggerCapture('SELECTED_TEXT'));
  btnScanPage.addEventListener('click', () => handleTriggerCapture('CURRENT_PAGE'));
  btnScanUrl.addEventListener('click', () => handleTriggerCapture('URL'));

  btnConfirmAnalyze.addEventListener('click', handleConfirmAnalysis);
  btnCancelPreview.addEventListener('click', () => {
    activeCapture = null;
    transitionView('ready');
  });
  btnCancelAnalyzing.addEventListener('click', () => {
    transitionView('ready');
  });

  btnRescan.addEventListener('click', async () => {
    activeCapture = null;
    transitionView('ready');
    await checkActiveSelection();
  });

  btnOpenApp.addEventListener('click', handleOpenAppClick);
  linkWebApp.addEventListener('click', (e) => {
    e.preventDefault();
    handleOpenAppClick();
  });
});
