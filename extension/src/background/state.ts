/**
 * Background Runtime State Manager (Phase 13.1, 13.2 & 13.3)
 *
 * Implements:
 * 1. Multi-Tab Isolation (Section 28): Tab A and Tab B maintain separate runtime states
 *    and cannot clobber each other's analyses.
 * 2. Session Isolation (Section 29): Sessions are tab-scoped and isolated.
 * 3. Worker Restart Resilience (Section 26): Minimal lightweight analysis references
 *    survive service worker suspension via chrome.storage.local.
 * 4. Zero Raw Content Persistence: Raw text, full pages, or credentials are NEVER persisted.
 */

import type {
  ExtensionRuntimeState,
  ExtensionStatus,
  ConnectionState,
  ActiveRequestRecord,
  LastAnalysisReference,
  TabRuntimeState,
} from '../types/state';

class BackgroundStateManager {
  private globalConnectionState: ConnectionState = 'CONNECTING';
  private currentActiveTabId: number | null = null;
  private tabStates: Map<number, TabRuntimeState> = new Map();

  /**
   * Retrieves or initializes isolated runtime state for a specific tab.
   */
  public getTabState(tabId: number): TabRuntimeState {
    let tabState = this.tabStates.get(tabId);
    if (!tabState) {
      tabState = {
        tabId,
        status: 'READY',
        activeRequest: null,
        lastAnalysis: null,
        lastError: null,
        sessionId: `SESS-TAB-${tabId}-${Date.now().toString(36).toUpperCase()}`,
      };
      this.tabStates.set(tabId, tabState);
    }
    return tabState;
  }

  /**
   * Returns current extension runtime state for a specific tab (or default active tab).
   */
  public getState(tabId?: number | null): ExtensionRuntimeState {
    const targetTabId = tabId || this.currentActiveTabId;
    if (typeof targetTabId === 'number' && targetTabId > 0) {
      const tabState = this.getTabState(targetTabId);
      return {
        status: tabState.status,
        connectionState: this.globalConnectionState,
        currentTabId: targetTabId,
        activeRequest: tabState.activeRequest ? { ...tabState.activeRequest } : null,
        lastAnalysis: tabState.lastAnalysis ? { ...tabState.lastAnalysis } : null,
        lastError: tabState.lastError ? { ...tabState.lastError } : null,
      };
    }

    return {
      status: 'READY',
      connectionState: this.globalConnectionState,
      currentTabId: null,
      activeRequest: null,
      lastAnalysis: null,
      lastError: null,
    };
  }

  public setStatus(status: ExtensionStatus, tabId?: number | null): void {
    if (typeof tabId === 'number' && tabId > 0) {
      this.getTabState(tabId).status = status;
    }
  }

  public setConnectionState(connectionState: ConnectionState): void {
    this.globalConnectionState = connectionState;
  }

  public setCurrentTabId(tabId: number | null): void {
    this.currentActiveTabId = tabId;
  }

  /**
   * Starts an active analysis request for a specific tab.
   */
  public startRequest(activeRequest: ActiveRequestRecord, sessionId?: string): void {
    const tabId = activeRequest.tabId;
    this.currentActiveTabId = tabId;
    const tabState = this.getTabState(tabId);

    tabState.status = 'ANALYZING';
    tabState.activeRequest = { ...activeRequest };
    tabState.lastError = null;
    if (sessionId) {
      tabState.sessionId = sessionId;
    }
  }

  /**
   * Completes an analysis request for a specific tab and persists a lightweight
   * recovery reference to chrome.storage.local for worker restart resilience.
   */
  public completeRequest(reference: LastAnalysisReference, tabId?: number | null): void {
    const targetTabId = tabId || reference.tabId || this.currentActiveTabId || 1;
    if (typeof targetTabId === 'number' && targetTabId > 0) {
      const tabState = this.getTabState(targetTabId);
      tabState.status = 'RESULT_AVAILABLE';
      tabState.lastAnalysis = { ...reference, tabId: targetTabId };
      tabState.activeRequest = null;
      tabState.lastError = null;

      // Persist lightweight recovery reference in storage (Section 26)
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({
          [`tab_ref_${targetTabId}`]: {
            analysisId: reference.analysisId,
            decision: reference.decision,
            primaryReason: reference.primaryReason,
            webAppUrl: reference.webAppUrl,
            completedAt: reference.completedAt,
            tabId: targetTabId,
          },
        }).catch(() => {});
      }
    }
  }

  /**
   * Records failure for a specific tab.
   */
  public failRequest(error: { code: string; message: string }, tabId?: number | null): void {
    const targetTabId = tabId || this.currentActiveTabId || 1;
    if (typeof targetTabId === 'number' && targetTabId > 0) {
      const tabState = this.getTabState(targetTabId);
      tabState.status = 'ERROR';
      tabState.activeRequest = null;
      tabState.lastError = {
        code: error.code,
        message: error.message,
        timestamp: new Date().toISOString(),
      };
    }
  }

  public reset(tabId?: number | null): void {
    if (typeof tabId === 'number' && tabId > 0) {
      const tabState = this.getTabState(tabId);
      tabState.status = 'READY';
      tabState.activeRequest = null;
      tabState.lastError = null;
    } else {
      this.tabStates.clear();
      this.currentActiveTabId = null;
    }
  }

  /**
   * Returns a persistent or newly generated session ID for the given tab (Section 5).
   */
  public getSessionIdForTab(tabId: number): string {
    return this.getTabState(tabId).sessionId!;
  }
}

export const backgroundState = new BackgroundStateManager();
