/**
 * Typed Message Protocol Contracts (Phase 13.1 Section 7, 8, 9)
 *
 * Defines explicit typed messaging between:
 * Content Script ↔ Background Service Worker ↔ Popup UI
 *
 * Every analysis message carries a correlated `requestId` (EXT-...)
 * ensuring responses never interleave or get attributed to the wrong request.
 */

import type { SafePageContext } from './context';
import type { ExtensionRuntimeState, LastAnalysisReference } from './state';

export type ExtensionMessageType =
  | 'EXTENSION_READY'
  | 'GET_STATUS'
  | 'STATUS_UPDATE'
  | 'GET_PAGE_CONTEXT'
  | 'PAGE_CONTEXT_RESPONSE'
  | 'SCAN_REQUEST'
  | 'ANALYSIS_STARTED'
  | 'ANALYSIS_COMPLETED'
  | 'ANALYSIS_FAILED'
  | 'OPEN_NIVESH_APP';

export interface ExtensionMessageError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface BaseExtensionMessage<T = unknown> {
  type: ExtensionMessageType;
  requestId: string;
  tabId?: number;
  timestamp: string;
  payload: T;
}

// 1. GET_STATUS Request & Response
export interface GetStatusPayload {
  tabId?: number;
}
export type GetStatusMessage = BaseExtensionMessage<GetStatusPayload>;

export interface StatusUpdatePayload {
  state: ExtensionRuntimeState;
}
export type StatusUpdateMessage = BaseExtensionMessage<StatusUpdatePayload>;

// 2. GET_PAGE_CONTEXT (Background -> Content Script) & Response
export interface GetPageContextPayload {
  requestId: string;
}
export type GetPageContextMessage = BaseExtensionMessage<GetPageContextPayload>;

export interface PageContextResponsePayload {
  context: SafePageContext;
}
export type PageContextResponseMessage = BaseExtensionMessage<PageContextResponsePayload>;

// 3. SCAN_REQUEST (Popup -> Background)
export interface ScanRequestPayload {
  tabId: number;
  forceFresh?: boolean;
}
export type ScanRequestMessage = BaseExtensionMessage<ScanRequestPayload>;

// 4. ANALYSIS_STARTED (Background -> Popup)
export interface AnalysisStartedPayload {
  pageUrl: string;
  pageOrigin: string;
}
export type AnalysisStartedMessage = BaseExtensionMessage<AnalysisStartedPayload>;

// 5. ANALYSIS_COMPLETED (Background -> Popup)
export interface AnalysisCompletedPayload {
  reference: LastAnalysisReference;
}
export type AnalysisCompletedMessage = BaseExtensionMessage<AnalysisCompletedPayload>;

// 6. ANALYSIS_FAILED (Background -> Popup)
export interface AnalysisFailedPayload {
  error: ExtensionMessageError;
}
export type AnalysisFailedMessage = BaseExtensionMessage<AnalysisFailedPayload>;

// 7. OPEN_NIVESH_APP (Popup -> Background)
export interface OpenNiveshAppPayload {
  analysisId?: string;
}
export type OpenNiveshAppMessage = BaseExtensionMessage<OpenNiveshAppPayload>;

// Union of all supported message types
export type ExtensionMessage =
  | GetStatusMessage
  | StatusUpdateMessage
  | GetPageContextMessage
  | PageContextResponseMessage
  | ScanRequestMessage
  | AnalysisStartedMessage
  | AnalysisCompletedMessage
  | AnalysisFailedMessage
  | OpenNiveshAppMessage;

// Generic response envelope
export interface ExtensionResponse<T = unknown> {
  success: boolean;
  requestId: string;
  data?: T;
  error?: ExtensionMessageError;
}

/**
 * Creates a unique, traceable request correlation identifier (Phase 13.1 Section 9)
 */
export function generateExtensionRequestId(): string {
  const timestamp = Date.now().toString(36);
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  return `EXT-${timestamp}-${randomSuffix}`.toUpperCase();
}
