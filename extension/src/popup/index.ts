/**
 * Extension Popup Controller (Phase 17.1 — Production UX & Visual Polish)
 *
 * Primary user journey:
 * - One-click "Analyze This Page" (Idle -> Analyzing -> Result)
 * - Secondary capture triggers (Selected text preview, Page URL)
 * - Safe error recovery with retry mechanism
 * - Semantic protection status reflection (Ready, Analyzing, Protected, Warning/Pause/Block, Offline)
 * - Full Firewall Handoff to web application
 *
 * Security: Uses textContent exclusively for user/page content to prevent XSS.
 * Zero credentials, OTPs, or continuous surveillance data collected.
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
const pageStatusLabel = document.getElementById('page-status-label') as HTMLSpanElement | null;
const unsupportedBox = document.getElementById('unsupported-box') as HTMLDivElement;
const errorBox = document.getElementById('error-box') as HTMLDivElement;
const errorMessageText = document.getElementById('error-message-text') as HTMLDivElement | null;
const btnRetryError = document.getElementById('btn-retry-error') as HTMLButtonElement | null;

const viewReady = document.getElementById('view-ready') as HTMLDivElement;
const viewPreview = document.getElementById('view-preview') as HTMLDivElement;
const viewAnalyzing = document.getElementById('view-analyzing') as HTMLDivElement;
const viewResult = document.getElementById('view-result') as HTMLDivElement;

// Action Buttons
const btnScanPage = document.getElementById('btn-scan-page') as HTMLButtonElement;
const btnScanSelection = document.getElementById('btn-scan-selection') as HTMLButtonElement;
const selectionHint = document.getElementById('selection-hint') as HTMLSpanElement;
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
const decisionSubstatus = document.getElementById('decision-substatus') as HTMLSpanElement | null;
const analysisIdBadge = document.getElementById('analysis-id-badge') as HTMLSpanElement;
const decisionReason = document.getElementById('decision-reason') as HTMLParagraphElement;
const resultSignals = document.getElementById('result-signals') as HTMLDivElement;

let currentTabId: number | null = null;
let currentAnalysisId: string | undefined;
let activeCapture: CapturePayload | null = null;
let isPageSupported = true;
let isAnalyzingInProgress = false;
let lastRetryAction: (() => Promise<void>) | null = null;

/**
 * Updates connection & protection indicator in popup header.
 */
function updateConnectionUI(
  state: ExtensionRuntimeState['connectionState'],
  decision?: string
): void {
  if (!connectionDot || !connectionText) return;

  connectionDot.className = `dot ${state.toLowerCase()}`;
  switch (state) {
    case 'CONNECTED':
      if (decision === 'ALLOW') {
        connectionText.textContent = 'Protected';
      } else if (decision && ['WARN', 'PAUSE', 'BLOCK'].includes(decision)) {
        connectionText.textContent = decision;
      } else {
        connectionText.textContent = 'Ready';
      }
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
  if (viewReady) viewReady.style.display = view === 'ready' ? 'flex' : 'none';
  if (viewPreview) viewPreview.style.display = view === 'preview' ? 'flex' : 'none';
  if (viewAnalyzing) viewAnalyzing.style.display = view === 'analyzing' ? 'flex' : 'none';
  if (viewResult) viewResult.style.display = view === 'result' ? 'flex' : 'none';

  if (view !== 'analyzing') {
    isAnalyzingInProgress = false;
    setCaptureControlsDisabled(!isPageSupported);
  } else {
    isAnalyzingInProgress = true;
    setCaptureControlsDisabled(true);
  }

  hideError();
}

/**
 * Displays a sanitized error message with optional retry handler.
 */
function showError(message: string, retryAction?: () => Promise<void>): void {
  if (!errorBox) return;

  if (errorMessageText) {
    errorMessageText.textContent = message;
  } else {
    errorBox.textContent = message;
  }

  lastRetryAction = retryAction || null;
  if (btnRetryError) {
    btnRetryError.style.display = retryAction ? 'inline-flex' : 'none';
  }

  errorBox.style.display = 'flex';
}

function hideError(): void {
  if (!errorBox) return;
  if (errorMessageText) errorMessageText.textContent = '';
  errorBox.style.display = 'none';
  if (btnRetryError) btnRetryError.style.display = 'none';
  lastRetryAction = null;
}

/**
 * Enables or disables capture buttons during active operations.
 */
function setCaptureControlsDisabled(disabled: boolean): void {
  if (btnScanPage) btnScanPage.disabled = disabled;
  if (btnScanSelection) btnScanSelection.disabled = disabled;
  if (btnScanUrl) btnScanUrl.disabled = disabled;
}

/**
 * Renders an Engine analysis result into the result card.
 */
function renderAnalysisResult(reference: LastAnalysisReference): void {
  currentAnalysisId = reference.analysisId;

  if (decisionBadge) decisionBadge.textContent = reference.decision;
  if (analysisIdBadge) {
    analysisIdBadge.textContent = reference.analysisId ? `#${reference.analysisId.slice(-8)}` : '';
  }
  if (decisionReason) {
    decisionReason.textContent = reference.userMessage || reference.primaryReason;
  }

  if (decisionCard) {
    decisionCard.className = `decision-card ${reference.decision}`;
  }

  // Update substatus label
  if (decisionSubstatus) {
    switch (reference.decision) {
      case 'ALLOW':
        decisionSubstatus.textContent = 'Protected';
        break;
      case 'INFORM':
        decisionSubstatus.textContent = 'Claim Verified';
        break;
      case 'WARN':
        decisionSubstatus.textContent = 'Caution Advised';
        break;
      case 'PAUSE':
        decisionSubstatus.textContent = 'Action Paused';
        break;
      case 'BLOCK':
        decisionSubstatus.textContent = 'Enforcement Block';
        break;
      default:
        decisionSubstatus.textContent = 'Analyzed';
    }
  }

  // Update context label
  if (pageStatusLabel) {
    pageStatusLabel.textContent = reference.decision === 'ALLOW' ? 'Protected' : reference.decision;
  }

  updateConnectionUI('CONNECTED', reference.decision);

  // Populate compact signal chips (only real signals from backend)
  if (resultSignals) {
    resultSignals.innerHTML = '';

    if (typeof reference.claimsCount === 'number' && reference.claimsCount > 0) {
      const chip = document.createElement('span');
      chip.className = 'badge-signal';
      chip.textContent = `${reference.claimsCount} Claim${reference.claimsCount > 1 ? 's' : ''}`;
      resultSignals.appendChild(chip);
    }
    if (reference.evidenceStatus && reference.evidenceStatus !== 'NOT_ESTABLISHED') {
      const chip = document.createElement('span');
      chip.className = 'badge-signal';
      chip.textContent = `Evidence: ${reference.evidenceStatus}`;
      resultSignals.appendChild(chip);
    }
    if (reference.identityStatus && reference.identityStatus !== 'NOT_ESTABLISHED') {
      const chip = document.createElement('span');
      chip.className = 'badge-signal';
      chip.textContent = `Identity: ${reference.identityStatus}`;
      resultSignals.appendChild(chip);
    }
    if (reference.fingerprintMatch && reference.fingerprintMatch !== 'NO_MATCH') {
      const chip = document.createElement('span');
      chip.className = 'badge-signal';
      chip.textContent = `Pattern: ${reference.fingerprintMatch}`;
      resultSignals.appendChild(chip);
    }
    if (reference.severity && reference.severity !== 'INFORMATIONAL') {
      const chip = document.createElement('span');
      chip.className = 'badge-signal';
      chip.textContent = `Severity: ${reference.severity}`;
      resultSignals.appendChild(chip);
    }
  }

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
  if (!btnScanSelection) return;

  if (!currentTabId || !isPageSupported) {
    btnScanSelection.disabled = true;
    if (selectionHint) selectionHint.style.display = 'block';
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
      if (selectionHint) selectionHint.style.display = 'none';
    } else {
      btnScanSelection.disabled = true;
      if (selectionHint) selectionHint.style.display = 'block';
    }
  } catch {
    btnScanSelection.disabled = true;
    if (selectionHint) selectionHint.style.display = 'block';
  }
}

/**
 * Fetches the active tab and checks eligibility.
 */
async function loadActiveTabContext(): Promise<void> {
  if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.tabs.query) {
    if (targetDomainEl) targetDomainEl.textContent = 'localhost (Test)';
    if (targetUrlEl) targetUrlEl.textContent = 'http://localhost:5173';
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
        if (targetDomainEl) targetDomainEl.textContent = 'Browser Internal Page';
        if (targetUrlEl) targetUrlEl.textContent = tabUrl;
        if (unsupportedBox) unsupportedBox.style.display = 'flex';
        if (pageStatusLabel) pageStatusLabel.textContent = 'Restricted';
        setCaptureControlsDisabled(true);
        return;
      }

      isPageSupported = true;
      if (unsupportedBox) unsupportedBox.style.display = 'none';
      if (pageStatusLabel) pageStatusLabel.textContent = 'Ready to Inspect';

      try {
        const parsed = new URL(tabUrl);
        if (targetDomainEl) targetDomainEl.textContent = parsed.hostname;
        if (targetUrlEl) targetUrlEl.textContent = getSanitizedDisplayUrl(tabUrl);
      } catch {
        if (targetDomainEl) targetDomainEl.textContent = activeTab.title || 'Current Page';
        if (targetUrlEl) targetUrlEl.textContent = tabUrl;
      }
    }
  } catch (err) {
    if (targetDomainEl) targetDomainEl.textContent = 'Active tab unavailable';
    showError(err instanceof Error ? err.message : 'Could not query current tab.', loadActiveTabContext);
  }
}

/**
 * Initiates content capture for a chosen mode.
 * If directAnalyze is true, immediately dispatches to analysis pipeline (Idle -> Analyzing -> Result).
 */
async function handleTriggerCapture(
  sourceType: CaptureSourceType,
  directAnalyze: boolean = false
): Promise<void> {
  if (isAnalyzingInProgress) return;

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

      if (directAnalyze) {
        // Fast-path: One-click "Analyze This Page" directly proceeds to analyzing
        await handleConfirmAnalysis();
        return;
      }

      // Preview path for selected text or URL
      let sourceLabel = 'Webpage Content';
      if (sourceType === 'SELECTED_TEXT') sourceLabel = 'Selected Text';
      if (sourceType === 'URL') sourceLabel = 'Page URL';

      if (previewBadge) previewBadge.textContent = sourceLabel;

      const previewText = capture.text || capture.url || '';
      const displaySnippet = previewText.length > 200 ? `${previewText.slice(0, 197)}...` : previewText;
      if (previewSnippet) previewSnippet.textContent = displaySnippet || '(No content)';

      if (previewLength) previewLength.textContent = `${capture.contentLength} characters`;
      if (previewOrigin) previewOrigin.textContent = capture.displayUrl || capture.pageOrigin;

      transitionView('preview');
    } else {
      const code = response.error?.code || 'CAPTURE_FAILED';
      const msg = response.error?.message || 'Could not capture content.';
      if (code === 'NO_SELECTION') {
        showError('No text is selected. Highlight text on the page or choose "Analyze This Page".');
      } else if (code === 'CONTENT_TOO_LARGE') {
        showError('Selected content exceeds size limits. Please select a smaller passage.');
      } else {
        showError(msg, () => handleTriggerCapture(sourceType, directAnalyze));
      }
      transitionView('ready');
    }
  } catch (err) {
    setCaptureControlsDisabled(false);
    showError(
      err instanceof Error ? err.message : 'Failed to capture page content.',
      () => handleTriggerCapture(sourceType, directAnalyze)
    );
    transitionView('ready');
  }
}

/**
 * Confirms analysis and dispatches to background bridge -> Unified Firewall API.
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
      const errorMsg = response.error?.message || 'Inspection failed.';
      showError(errorMsg, handleConfirmAnalysis);
      transitionView('ready');
    }
  } catch (err) {
    showError(
      err instanceof Error ? err.message : 'Nivesh Firewall is temporarily unavailable.',
      handleConfirmAnalysis
    );
    transitionView('ready');
  }
}

/**
 * Syncs initial runtime state with background service worker.
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
      updateConnectionUI(state.connectionState, state.lastAnalysis?.decision);

      if (state.status === 'ANALYZING') {
        transitionView('analyzing');
      } else if (state.status === 'RESULT_AVAILABLE' && state.lastAnalysis) {
        renderAnalysisResult(state.lastAnalysis);
      } else if (state.status === 'ERROR' && state.lastError) {
        showError(state.lastError.message, syncStatus);
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
    if (typeof window !== 'undefined' && window.close) {
      window.close();
    }
  } catch (err) {
    showError(err instanceof Error ? err.message : 'Could not open Nivesh Web App.');
  }
}

// Bind Listeners
document.addEventListener('DOMContentLoaded', async () => {
  await loadActiveTabContext();
  await checkActiveSelection();
  await syncStatus();

  // Primary Action: Analyze This Page (direct 1-click pipeline execution)
  if (btnScanPage) {
    btnScanPage.addEventListener('click', () => handleTriggerCapture('CURRENT_PAGE', true));
  }

  // Secondary Triggers
  if (btnScanSelection) {
    btnScanSelection.addEventListener('click', () => handleTriggerCapture('SELECTED_TEXT', false));
  }
  if (btnScanUrl) {
    btnScanUrl.addEventListener('click', () => handleTriggerCapture('URL', false));
  }

  // Preview Actions
  if (btnConfirmAnalyze) {
    btnConfirmAnalyze.addEventListener('click', handleConfirmAnalysis);
  }
  if (btnCancelPreview) {
    btnCancelPreview.addEventListener('click', () => {
      activeCapture = null;
      transitionView('ready');
    });
  }

  // Analyzing View Cancellation
  if (btnCancelAnalyzing) {
    btnCancelAnalyzing.addEventListener('click', () => {
      transitionView('ready');
    });
  }

  // Rescan / Reset
  if (btnRescan) {
    btnRescan.addEventListener('click', async () => {
      activeCapture = null;
      transitionView('ready');
      await checkActiveSelection();
    });
  }

  // Handoff to Web App
  if (btnOpenApp) {
    btnOpenApp.addEventListener('click', handleOpenAppClick);
  }
  if (linkWebApp) {
    linkWebApp.addEventListener('click', (e) => {
      e.preventDefault();
      handleOpenAppClick();
    });
  }

  // Error Retry
  if (btnRetryError) {
    btnRetryError.addEventListener('click', async () => {
      if (lastRetryAction) {
        hideError();
        await lastRetryAction();
      } else {
        await syncStatus();
      }
    });
  }
});
