/**
 * Extension State Model (Phase 13.1 Section 16 & 17)
 *
 * Separates ephemeral runtime coordination state from persistent user preferences.
 * Adheres strictly to lifecycle semantics: Does NOT use intelligence/policy labels
 * (SAFE, SCAM, DANGEROUS) as extension lifecycle states.
 */

export type ExtensionStatus =
  | 'READY'
  | 'ANALYZING'
  | 'RESULT_AVAILABLE'
  | 'ERROR'
  | 'DISCONNECTED';

export type ConnectionState =
  | 'CONNECTED'
  | 'CONNECTING'
  | 'UNAVAILABLE';

export interface ActiveRequestRecord {
  requestId: string;
  tabId: number;
  startedAt: string;
  pageOrigin: string;
  pageUrl: string;
}

export interface LastAnalysisReference {
  analysisId: string;
  captureId?: string;
  requestId?: string;
  tabId?: number;
  decision: 'ALLOW' | 'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK' | string;
  severity: string;
  primaryReason: string;
  userMessage?: string;
  completedAt: string;
  webAppUrl: string;
  claimsCount?: number;
  evidenceStatus?: string;
  identityStatus?: string;
  fingerprintMatch?: string;
  threatSignalCount?: number;
  durationMs?: number;
}

export interface TabRuntimeState {
  tabId: number;
  status: ExtensionStatus;
  activeRequest: ActiveRequestRecord | null;
  lastAnalysis: LastAnalysisReference | null;
  lastError: {
    code: string;
    message: string;
    timestamp: string;
  } | null;
  sessionId?: string;
}

export interface ExtensionRuntimeState {
  status: ExtensionStatus;
  connectionState: ConnectionState;
  currentTabId: number | null;
  activeRequest: ActiveRequestRecord | null;
  lastAnalysis: LastAnalysisReference | null;
  lastError: {
    code: string;
    message: string;
    timestamp: string;
  } | null;
}

/**
 * Persistent Settings (Stored via chrome.storage.local/sync)
 */
export interface ExtensionPersistentConfig {
  backendApiUrl: string;
  webAppBaseUrl: string;
  autoConnectHealthCheck: boolean;
  theme: 'dark' | 'light' | 'system';
}
