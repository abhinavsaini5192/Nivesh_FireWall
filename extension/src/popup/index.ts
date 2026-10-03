/**
 * Extension Popup Controller (Phase 13.1 Section 6, 7, 8, 9, 22)
 *
 * Safe, progressive disclosure UI communicating with the background worker.
 * Security: Uses textContent exclusively for user/page content to prevent XSS.
 */

import { generateExtensionRequestId } from '../types/messages';
import type {
  ExtensionResponse,
  GetStatusMessage,
  ScanRequestMessage,
  OpenNiveshAppMessage,
} from '../types/messages';
import type { ExtensionRuntimeState, LastAnalysisReference } from '../types/state';

// DOM Element References
const connectionDot = document.getElementById('connection-dot') as HTMLSpanElement;
const connectionText = document.getElementById('connection-text') as HTMLSpanElement;
const targetDomainEl = document.getElementById('target-domain') as HTMLDivElement;
const targetUrlEl = document.getElementById('target-url') as HTMLDivElement;
const errorBox = document.getElementById('error-box') as HTMLDivElement;

const viewReady = document.getElementById('view-ready') as HTMLDivElement;
const viewAnalyzing = document.getElementById('view-analyzing') as HTMLDivElement;
const viewResult = document.getElementById('view-result') as HTMLDivElement;

const btnScan = document.getElementById('btn-scan') as HTMLButtonElement;
const btnOpenApp = document.getElementById('btn-open-app') as HTMLButtonElement;
const btnRescan = document.getElementById('btn-rescan') as HTMLButtonElement;
const linkWebApp = document.getElementById('link-web-app') as HTMLAnchorElement;

const decisionCard = document.getElementById('decision-card') as HTMLDivElement;
const decisionBadge = document.getElementById('decision-badge') as HTMLSpanElement;
const analysisIdBadge = document.getElementById('analysis-id-badge') as HTMLSpanElement;
const decisionReason = document.getElementById('decision-reason') as HTMLParagraphElement;

let currentTabId: number | null = null;
let currentAnalysisId: string | undefined;

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
 * Transitions the popup view between READY, ANALYZING, and RESULT.
 */
function transitionView(view: 'ready' | 'analyzing' | 'result'): void {
  viewReady.style.display = view === 'ready' ? 'flex' : 'none';
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
 * Fetches the active tab and updates the context card.
 */
async function loadActiveTabContext(): Promise<void> {
  if (typeof chrome === 'undefined' || !chrome.tabs || !chrome.tabs.query) {
    targetDomainEl.textContent = 'localhost (Test)';
    targetUrlEl.textContent = 'http://localhost:5173';
    return;
  }

  try {
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    const activeTab = tabs[0];
    if (activeTab && activeTab.id) {
      currentTabId = activeTab.id;

      if (activeTab.url) {
        try {
          const parsed = new URL(activeTab.url);
          targetDomainEl.textContent = parsed.hostname;
          targetUrlEl.textContent = activeTab.url;
        } catch {
          targetDomainEl.textContent = activeTab.title || 'Current Page';
          targetUrlEl.textContent = activeTab.url || '';
        }
      }
    }
  } catch (err) {
    targetDomainEl.textContent = 'Active tab unavailable';
    showError(err instanceof Error ? err.message : 'Could not query current tab.');
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
 * Dispatches scan request on user click.
 */
async function handleScanClick(): Promise<void> {
  if (!currentTabId) {
    showError('No active browser tab found to inspect.');
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
    payload: { tabId: currentTabId, forceFresh: true },
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
    window.close(); // Close popup once tab opens
  } catch (err) {
    showError(err instanceof Error ? err.message : 'Could not open Nivesh Web App.');
  }
}

// Bind Listeners
document.addEventListener('DOMContentLoaded', async () => {
  await loadActiveTabContext();
  await syncStatus();

  btnScan.addEventListener('click', handleScanClick);
  btnRescan.addEventListener('click', () => {
    transitionView('ready');
  });
  btnOpenApp.addEventListener('click', handleOpenAppClick);
  linkWebApp.addEventListener('click', (e) => {
    e.preventDefault();
    handleOpenAppClick();
  });
});
