/**
 * Content Capture Sanitization Layer (Phase 13.2 Sections 14, 15, 16, 17)
 *
 * Sanitizes, validates, and normalizes captured textual content prior to
 * packaging into a CapturePayload or dispatching to the Unified Firewall API.
 *
 * Ensures:
 * 1. Control characters are stripped.
 * 2. Excessive whitespace and duplicate blank lines are compressed while preserving paragraphs.
 * 3. Accidental sensitive patterns (e.g., credit card numbers, CVVs) are redacted.
 * 4. Content bounds are strictly enforced (CONTENT_TOO_LARGE).
 */

import type { CaptureValidationResult, CaptureSourceType } from '../types/capture';

export const MAX_SELECTION_LENGTH = 5000;
export const MAX_PAGE_TEXT_LENGTH = 15000;

// Credit card number pattern (13 to 19 digits, possibly hyphen or space separated)
const CREDIT_CARD_PATTERN = /\b(?:\d{4}[ -]?){3}\d{4}\b|\b\d{15,16}\b/g;

// CVV pattern (explicitly labeled CVV/CVC with 3 or 4 digits)
const CVV_PATTERN = /\b(?:cvv|cvc|security\s*code)[:\s=]+(\d{3,4})\b/gi;

// PIN pattern (explicitly labeled PIN)
const PIN_PATTERN = /\b(?:pin|atm\s*pin)[:\s=]+(\d{4,6})\b/gi;

/**
 * Normalizes text content:
 * - Strips control characters
 * - Converts multiple horizontal whitespace to a single space
 * - Compresses more than two consecutive newlines into two newlines (preserving paragraph boundaries)
 */
export function normalizeTextContent(raw: string): string {
  if (!raw) return '';

  return (
    raw
      // Strip control characters (except tab \t, linefeed \n, carriage return \r)
      // eslint-disable-next-line no-control-regex
      .replace(/[\u0000-\u0008\u000B-\u000C\u000E-\u001F\u007F-\u009F]/g, '')
      // Standardize Windows / Mac newlines to \n
      .replace(/\r\n/g, '\n')
      .replace(/\r/g, '\n')
      // Collapse multiple horizontal spaces and tabs into single space
      .replace(/[ \t]+/g, ' ')
      // Remove trailing spaces on lines
      .replace(/ +\n/g, '\n')
      .replace(/\n +/g, '\n')
      // Collapse 3 or more consecutive line breaks into 2 (preserving clean paragraphs)
      .replace(/\n{3,}/g, '\n\n')
      .trim()
  );
}

/**
 * Redacts any accidental sensitive numbers (credit cards, CVVs, PINs) from text.
 */
export function redactSensitivePatterns(text: string): { text: string; hadRedactions: boolean } {
  let hadRedactions = false;

  let sanitized = text.replace(CREDIT_CARD_PATTERN, (match) => {
    hadRedactions = true;
    return `[CARD_NUMBER_REDACTED_${match.length}]`;
  });

  sanitized = sanitized.replace(CVV_PATTERN, (_match) => {
    hadRedactions = true;
    return '[CVV_REDACTED]';
  });

  sanitized = sanitized.replace(PIN_PATTERN, (_match) => {
    hadRedactions = true;
    return '[PIN_REDACTED]';
  });

  return { text: sanitized, hadRedactions };
}

/**
 * Validates and sanitizes captured content according to its source type.
 */
export function validateAndSanitizeContent(
  rawText: string | undefined | null,
  sourceType: CaptureSourceType,
  customMaxLength?: number
): CaptureValidationResult {
  if (sourceType === 'URL') {
    return {
      isValid: true,
      status: 'CAPTURED',
      sanitizedText: '',
    };
  }

  if (!rawText || !rawText.trim()) {
    return {
      isValid: false,
      status: sourceType === 'SELECTED_TEXT' ? 'NO_SELECTION' : 'EMPTY_CONTENT',
      error: sourceType === 'SELECTED_TEXT' ? 'No text selected on page.' : 'No visible text found on page.',
    };
  }

  const maxLength =
    customMaxLength || (sourceType === 'SELECTED_TEXT' ? MAX_SELECTION_LENGTH : MAX_PAGE_TEXT_LENGTH);

  // Check size limit prior to processing
  if (rawText.length > maxLength) {
    return {
      isValid: false,
      status: 'CONTENT_TOO_LARGE',
      error: `Captured content length (${rawText.length} characters) exceeds safe limit of ${maxLength} characters.`,
    };
  }

  const normalized = normalizeTextContent(rawText);

  if (!normalized) {
    return {
      isValid: false,
      status: sourceType === 'SELECTED_TEXT' ? 'NO_SELECTION' : 'EMPTY_CONTENT',
      error: 'Normalized content is empty.',
    };
  }

  const { text: sanitized } = redactSensitivePatterns(normalized);

  return {
    isValid: true,
    status: 'CAPTURED',
    sanitizedText: sanitized,
  };
}
