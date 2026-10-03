/**
 * Safe Page Context Extractor (Phase 13.1 Section 4, 11, 19, 20)
 *
 * Strict Privacy Rules:
 * - NO password fields (<input type="password">)
 * - NO credit card, CVV, OTP, or PIN fields
 * - NO hidden inputs (<input type="hidden">)
 * - NO keystroke listening
 * - NO automatic background surveillance
 *
 * Only extracts public, non-sensitive page metadata when explicitly requested by user action.
 */

import type { SafePageContext, PageContextExtractionOptions } from '../types/context';

const SENSITIVE_INPUT_PATTERNS = [
  /password/i,
  /passcode/i,
  /otp/i,
  /one-time-code/i,
  /pin/i,
  /cvv/i,
  /cvc/i,
  /card.*number/i,
  /credit.*card/i,
  /cc-/i,
  /account.*number/i,
  /bank/i,
  /routing/i,
  /secret/i,
  /ssn/i,
  /token/i,
  /security.*code/i,
];

/**
 * Checks whether an element is a sensitive credential or financial input field.
 */
export function isSensitiveElement(element: Element | null): boolean {
  if (!element) return false;

  const tagName = element.tagName.toLowerCase();
  if (tagName === 'input' || tagName === 'textarea') {
    const input = element as HTMLInputElement;
    const type = (input.type || '').toLowerCase();
    if (type === 'password' || type === 'hidden') {
      return true;
    }

    const name = input.name || '';
    const id = input.id || '';
    const placeholder = input.placeholder || '';
    const autocomplete = input.autocomplete || '';

    const textToTest = `${name} ${id} ${placeholder} ${autocomplete}`;
    return SENSITIVE_INPUT_PATTERNS.some((pattern) => pattern.test(textToTest));
  }

  return false;
}

/**
 * Extracts sanitized user selection if present on the document, ensuring
 * that the selected text did NOT originate from a sensitive credential input.
 */
export function getSafeUserSelection(): string | undefined {
  if (typeof window === 'undefined' || typeof window.getSelection !== 'function') {
    return undefined;
  }

  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    return undefined;
  }

  const anchorNode = selection.anchorNode;
  const targetElement: Element | null =
    anchorNode instanceof Element ? anchorNode : (anchorNode?.parentElement ?? null);

  if (targetElement) {
    if (isSensitiveElement(targetElement) || isSensitiveElement(targetElement.closest('input, textarea'))) {
      return undefined;
    }
  }

  const rawText = selection.toString().trim();
  if (!rawText) return undefined;

  // Bound to a safe maximum length (e.g. 5000 chars) and sanitize control characters
  // eslint-disable-next-line no-control-regex
  return rawText.slice(0, 5000).replace(/[\u0000-\u0008\u000B-\u000C\u000E-\u001F]/g, '');
}

/**
 * Safely extracts non-sensitive page context.
 */
export function extractSafePageContext(
  options: PageContextExtractionOptions = {}
): SafePageContext {
  const maxLen = options.maxContentLength || 5000;

  let pageUrl = '';
  let pageOrigin = '';
  let pageTitle = '';
  let metaDescription: string | undefined;

  if (typeof window !== 'undefined' && window.location) {
    pageUrl = window.location.href || '';
    pageOrigin = window.location.origin || '';
  }

  if (typeof document !== 'undefined') {
    pageTitle = (document.title || '').trim().slice(0, 500);

    const metaTag = document.querySelector('meta[name="description"]') as HTMLMetaElement | null;
    if (metaTag && metaTag.content) {
      metaDescription = metaTag.content.trim().slice(0, 1000);
    }
  }

  const selectedText = options.includeSelection !== false ? getSafeUserSelection() : undefined;

  return {
    pageUrl: pageUrl.slice(0, maxLen),
    pageOrigin,
    pageTitle,
    selectedText,
    metaDescription,
    capturedAt: new Date().toISOString(),
  };
}
