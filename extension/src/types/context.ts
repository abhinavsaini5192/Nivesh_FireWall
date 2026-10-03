/**
 * Safe Page Context Representation (Phase 13.1 Section 11)
 *
 * Captures ONLY minimum non-sensitive context for financial content inspection.
 * Strict Privacy Safeguards: Never captures passwords, form credentials, OTP fields,
 * banking inputs, or arbitrary keystrokes.
 */

export interface SafePageContext {
  pageUrl: string;
  pageOrigin: string;
  pageTitle: string;
  tabId?: number;
  selectedText?: string;
  metaDescription?: string;
  capturedAt: string;
}

export interface PageContextExtractionOptions {
  includeSelection?: boolean;
  maxContentLength?: number;
}
