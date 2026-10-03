/**
 * DOM Visible Content Extractor (Phase 13.2 Sections 6, 7, 8, 9, 16)
 *
 * Efficiently extracts visible textual content from the active document,
 * filtering out:
 * - Hidden elements (display:none, visibility:hidden, hidden attribute, aria-hidden)
 * - Non-content tags (script, style, noscript, svg, template, iframe)
 * - Interactive form inputs, credential fields, and button controls
 * - Unrelated navigation boilerplate
 */

import { isSensitiveElement } from '../content/context';
import { validateAndSanitizeContent, MAX_PAGE_TEXT_LENGTH } from './sanitizer';
import type { CaptureValidationResult } from '../types/capture';

// Tags completely excluded from text extraction (scripts, styles, inputs, and navigation/footer noise)
const EXCLUDED_TAGS = new Set([
  'script',
  'style',
  'noscript',
  'template',
  'svg',
  'iframe',
  'canvas',
  'video',
  'audio',
  'object',
  'embed',
  'input',
  'textarea',
  'select',
  'option',
  'button',
  'nav',
  'footer',
]);

/**
 * Checks if a DOM element is visually hidden from the user.
 */
export function isElementHidden(element: Element): boolean {
  if (!element) return true;

  // 1. Explicit HTML hidden attribute
  if (element.hasAttribute('hidden')) return true;

  // 2. ARIA hidden
  if (element.getAttribute('aria-hidden') === 'true') return true;

  // 3. Inline style check
  const styleAttr = element.getAttribute('style') || '';
  if (/display\s*:\s*none/i.test(styleAttr)) return true;
  if (/visibility\s*:\s*hidden/i.test(styleAttr)) return true;
  if (/opacity\s*:\s*0(?![.\d])/i.test(styleAttr)) return true;

  // 4. Computed style check in real browser environment
  if (typeof window !== 'undefined' && typeof window.getComputedStyle === 'function') {
    try {
      const computed = window.getComputedStyle(element);
      if (
        computed.display === 'none' ||
        computed.visibility === 'hidden' ||
        computed.visibility === 'collapse' ||
        computed.opacity === '0'
      ) {
        return true;
      }
    } catch {
      // Fallback silently if computed style fails on disconnected nodes
    }
  }

  return false;
}

/**
 * Extracts visible text content from a DOM root element.
 * Excludes navigation, footers, scripts, and hidden inputs while capturing
 * headers, articles, sections, and body copy.
 */
export function extractVisiblePageText(doc: Document): CaptureValidationResult {
  if (!doc || !doc.body) {
    return {
      isValid: false,
      status: 'EMPTY_CONTENT',
      error: 'Document body is unavailable.',
    };
  }

  // Walk document.body while excluding nav, footer, scripts, styles, etc.
  const targetRoot = doc.body;

  const collectedChunks: string[] = [];
  let totalLength = 0;

  // 2. Recursive DOM walker collecting visible text nodes
  function walk(node: Node): void {
    if (totalLength > MAX_PAGE_TEXT_LENGTH * 1.5) {
      return; // Early break if page text greatly exceeds allowable bounds
    }

    if (node.nodeType === Node.TEXT_NODE) {
      const text = (node.textContent || '').trim();
      if (text.length > 0) {
        collectedChunks.push(text);
        totalLength += text.length;
      }
      return;
    }

    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node as Element;
      const tagName = el.tagName.toLowerCase();

      // Skip non-content tags
      if (EXCLUDED_TAGS.has(tagName)) {
        return;
      }

      // Skip sensitive form inputs
      if (isSensitiveElement(el)) {
        return;
      }

      // Skip hidden elements
      if (isElementHidden(el)) {
        return;
      }

      // Process children
      for (let child = node.firstChild; child !== null; child = child.nextSibling) {
        walk(child);
      }

      // Add a paragraph break after block-level elements
      if (/^(p|div|section|article|h[1-6]|li|blockquote|tr)$/.test(tagName)) {
        collectedChunks.push('\n');
      }
    }
  }

  walk(targetRoot);

  const rawCombinedText = collectedChunks.join(' ');
  return validateAndSanitizeContent(rawCombinedText, 'CURRENT_PAGE', MAX_PAGE_TEXT_LENGTH);
}

/**
 * Extracts the user-selected text on the active window.
 */
export function extractUserSelection(win: Window): CaptureValidationResult {
  if (!win || typeof win.getSelection !== 'function') {
    return {
      isValid: false,
      status: 'NO_SELECTION',
      error: 'Window selection API unavailable.',
    };
  }

  const selection = win.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    return {
      isValid: false,
      status: 'NO_SELECTION',
      error: 'No text is currently selected on the page.',
    };
  }

  const anchorNode = selection.anchorNode;
  const targetElement: Element | null =
    anchorNode instanceof Element ? anchorNode : (anchorNode?.parentElement ?? null);

  // If selection originated inside a sensitive field, return NO_SELECTION immediately
  if (targetElement) {
    if (isSensitiveElement(targetElement) || isSensitiveElement(targetElement.closest('input, textarea'))) {
      return {
        isValid: false,
        status: 'NO_SELECTION',
        error: 'Selection originated inside a protected credential or financial field.',
      };
    }
  }

  const rawText = selection.toString().trim();
  return validateAndSanitizeContent(rawText, 'SELECTED_TEXT');
}
