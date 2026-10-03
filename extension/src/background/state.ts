/**
 * Background Runtime State Manager (Phase 13.1 Section 5, 10, 16, 17)
 *
 * Maintains minimal temporary state:
 * - Current lifecycle status
 * - Backend connection state
 * - Active request correlation record
 * - Last analysis reference
 *
 * Does NOT persist complete page contents or browsing history.
 */

import type {
  ExtensionRuntimeState,
  ExtensionStatus,
  ConnectionState,
  ActiveRequestRecord,
  LastAnalysisReference,
} from '../types/state';

class BackgroundStateManager {
  private state: ExtensionRuntimeState = {
    status: 'READY',
    connectionState: 'CONNECTING',
    currentTabId: null,
    activeRequest: null,
    lastAnalysis: null,
    lastError: null,
  };

  public getState(): ExtensionRuntimeState {
    return { ...this.state };
  }

  public setStatus(status: ExtensionStatus): void {
    this.state.status = status;
  }

  public setConnectionState(connectionState: ConnectionState): void {
    this.state.connectionState = connectionState;
  }

  public setCurrentTabId(tabId: number | null): void {
    this.state.currentTabId = tabId;
  }

  public startRequest(activeRequest: ActiveRequestRecord): void {
    this.state.status = 'ANALYZING';
    this.state.activeRequest = activeRequest;
    this.state.lastError = null;
  }

  public completeRequest(reference: LastAnalysisReference): void {
    this.state.status = 'RESULT_AVAILABLE';
    this.state.lastAnalysis = reference;
    this.state.activeRequest = null;
    this.state.lastError = null;
  }

  public failRequest(error: { code: string; message: string }): void {
    this.state.status = 'ERROR';
    this.state.activeRequest = null;
    this.state.lastError = {
      code: error.code,
      message: error.message,
      timestamp: new Date().toISOString(),
    };
  }

  public reset(): void {
    this.state.status = 'READY';
    this.state.activeRequest = null;
    this.state.lastError = null;
  }
}

export const backgroundState = new BackgroundStateManager();
