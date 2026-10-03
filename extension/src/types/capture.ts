/**
 * Capture Layer Type Definitions (Phase 13.2 Sections 3, 10, 11, 18, 20)
 *
 * Defines explicit capture models, source types, and lifecycle states.
 */

export type CaptureSourceType = 'SELECTED_TEXT' | 'CURRENT_PAGE' | 'URL';

export type CaptureStatus =
  | 'CAPTURED'
  | 'NO_SELECTION'
  | 'EMPTY_CONTENT'
  | 'CONTENT_TOO_LARGE'
  | 'UNSUPPORTED_PAGE'
  | 'PERMISSION_DENIED'
  | 'SANITIZATION_FAILED'
  | 'ERROR';

export interface CaptureMetadata {
  captureId: string;
  sourceType: CaptureSourceType;
  tabId?: number;
  pageOrigin: string;
  pageTitle: string;
  timestamp: string;
  charCount: number;
  wordCount: number;
}

export interface CapturePayload {
  captureId: string;
  sourceType: CaptureSourceType;
  status: CaptureStatus;
  text?: string;
  url?: string;
  displayUrl: string;
  pageTitle: string;
  pageOrigin: string;
  tabId?: number;
  timestamp: string;
  contentLength: number;
  sanitized: boolean;
  error?: string;
}

export interface CaptureOptions {
  sourceType: CaptureSourceType;
  maxTextLength?: number;
  stripTrackingParams?: boolean;
}

export interface CaptureValidationResult {
  isValid: boolean;
  status: CaptureStatus;
  sanitizedText?: string;
  error?: string;
}

/**
 * Creates a unique capture correlation identifier (Phase 13.2 Section 11 & 31)
 */
export function generateCaptureId(): string {
  const timestamp = Date.now().toString(36);
  const randomSuffix = Math.random().toString(36).substring(2, 8);
  return `CAP-${timestamp}-${randomSuffix}`.toUpperCase();
}
