/**
 * Conservative Target Action Matcher (Phase 13.4 Sections 9, 10, 11, 25)
 *
 * Resolves whether a specific DOM element (e.g. navigation link or external action button)
 * on the current webpage corresponds to the backend's analyzed target.
 *
 * CRITICAL RULE: Safe Uncertainty Rule (Section 25)
 * If the target match is uncertain or ambiguous, DO NOT GUESS.
 * Return AMBIGUOUS with matchedElement: null to prevent accidental interference
 * with normal browsing.
 */

import type { TargetMatchResult, TargetActionInfo } from './types';

/**
 * Attempts conservative matching between analyzed action target and DOM elements.
 *
 * @param doc Target document (default: window.document)
 * @param targetUrl Explicit target URL analyzed by the backend (if any)
 * @param actions Extracted high-impact actions from Engine 3 / Engine 6
 */
export function matchTargetAction(
  doc: Document = document,
  targetUrl?: string,
  actions?: TargetActionInfo[]
): TargetMatchResult {
  // If no target URL and no specific action targets exist, no specific element can be matched safely
  if (!targetUrl && (!actions || actions.length === 0)) {
    return {
      matchedElement: null,
      matchConfidence: 'NO_MATCH',
      reason: 'No explicit target URL or action reference provided in backend analysis.',
    };
  }

  // 1. Check for explicit URL match in links (<a href="...">)
  if (targetUrl && targetUrl.trim()) {
    const cleanTarget = targetUrl.trim();
    let parsedTargetUrl: URL | null = null;
    try {
      parsedTargetUrl = new URL(cleanTarget);
    } catch {
      // Malformed target URL
    }

    if (parsedTargetUrl) {
      const links = Array.from(doc.querySelectorAll<HTMLAnchorElement>('a[href]'));
      const matchingLinks = links.filter((link) => {
        try {
          const linkUrl = new URL(link.href, window.location.href);
          // Match origin and exact pathname (excluding dynamic ephemeral query tokens)
          return (
            linkUrl.origin.toLowerCase() === parsedTargetUrl!.origin.toLowerCase() &&
            linkUrl.pathname.toLowerCase() === parsedTargetUrl!.pathname.toLowerCase()
          );
        } catch {
          return false;
        }
      });

      if (matchingLinks.length === 1) {
        return {
          matchedElement: matchingLinks[0],
          matchConfidence: 'EXACT',
          targetUrl: cleanTarget,
          reason: 'Single exact destination link matched on page.',
        };
      } else if (matchingLinks.length > 1) {
        // Multiple candidate links: Ambiguous! Section 25 Safe Uncertainty Rule
        return {
          matchedElement: null,
          matchConfidence: 'AMBIGUOUS',
          targetUrl: cleanTarget,
          reason: 'Multiple links match target URL. Applying Safe Uncertainty Rule (no arbitrary blocking).',
        };
      }
    }
  }

  // 2. Check actions with explicit action targets
  if (actions && actions.length > 0) {
    for (const action of actions) {
      if (action.target && action.target.trim().startsWith('http')) {
        const result = matchTargetAction(doc, action.target);
        if (result.matchConfidence === 'EXACT') {
          return {
            ...result,
            actionId: action.actionId,
          };
        }
      }
    }
  }

  return {
    matchedElement: null,
    matchConfidence: 'NO_MATCH',
    reason: 'No element on the page matches the analyzed target.',
  };
}
