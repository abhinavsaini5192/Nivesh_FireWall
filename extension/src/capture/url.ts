/**
 * URL Privacy & Sanitization Layer (Phase 13.2 Sections 12, 13, 22)
 *
 * Implements strict separation between:
 * 1. Analysis Input URL: Full target URL required for backend domain reputation & security inspection.
 * 2. Display / Logging URL: Sanitized URL stripped of tracking codes, tokens, and sensitive query parameters.
 */

// Tracking parameters stripped for privacy-safe display and UI logging
const TRACKING_PARAMS = new Set([
  'utm_source',
  'utm_medium',
  'utm_campaign',
  'utm_term',
  'utm_content',
  'fbclid',
  'gclid',
  'gclsrc',
  'dclid',
  'msclkid',
  'mc_cid',
  'mc_eid',
  'ref',
  'referrer',
  'source',
]);

// Sensitive credential/session query patterns masked in display URLs
const SENSITIVE_QUERY_PATTERNS = [
  /token/i,
  /auth/i,
  /session/i,
  /key/i,
  /secret/i,
  /password/i,
  /passcode/i,
  /jwt/i,
  /sig/i,
  /signature/i,
  /access_token/i,
  /refresh_token/i,
];

// Browser-internal and restricted schemes that cannot be inspected by extension content scripts
const UNSUPPORTED_SCHEMES = [
  'chrome:',
  'edge:',
  'about:',
  'chrome-extension:',
  'moz-extension:',
  'devtools:',
  'view-source:',
  'data:',
  'blob:',
];

/**
 * Determines whether a URL is an unsupported browser-internal or restricted page.
 */
export function isUnsupportedPageUrl(url: string | undefined | null): boolean {
  if (!url || typeof url !== 'string') return true;
  const trimmed = url.trim().toLowerCase();
  return UNSUPPORTED_SCHEMES.some((scheme) => trimmed.startsWith(scheme));
}

/**
 * Checks if a query parameter key represents sensitive credential or session state.
 */
export function isSensitiveQueryParam(key: string): boolean {
  return SENSITIVE_QUERY_PATTERNS.some((pattern) => pattern.test(key));
}

/**
 * Generates a privacy-safe URL representation for display in popup UI and logging.
 * Preserves protocol, hostname, port, and path, but strips tracking parameters
 * and redacts potential sensitive tokens.
 */
export function getSanitizedDisplayUrl(rawUrl: string): string {
  if (!rawUrl || typeof rawUrl !== 'string') return '';

  try {
    const parsed = new URL(rawUrl);

    // If protocol is not http/https, return generic safe string
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return `${parsed.protocol}//${parsed.hostname || 'internal-page'}`;
    }

    const cleanParams = new URLSearchParams();
    parsed.searchParams.forEach((val, key) => {
      const lowerKey = key.toLowerCase();
      if (TRACKING_PARAMS.has(lowerKey)) {
        // Drop tracking parameters from display
        return;
      }
      if (isSensitiveQueryParam(lowerKey)) {
        // Redact sensitive session/auth query values
        cleanParams.set(key, '[REDACTED]');
      } else {
        // Retain benign parameters (e.g. page=2, category=stocks) bounded
        cleanParams.set(key, val.slice(0, 100));
      }
    });

    const queryString = cleanParams.toString();
    const cleanSearch = queryString ? `?${queryString}` : '';

    return `${parsed.origin}${parsed.pathname}${cleanSearch}`;
  } catch {
    // If not a valid standard URL, return domain or safe prefix
    return rawUrl.slice(0, 60);
  }
}

/**
 * Validates whether a URL is suitable for Nivesh Firewall analysis.
 */
export function isValidAnalysisUrl(url: string): { isValid: boolean; error?: string } {
  if (!url || !url.trim()) {
    return { isValid: false, error: 'URL cannot be empty.' };
  }

  try {
    const parsed = new URL(url);
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
      return {
        isValid: false,
        error: `Unsupported protocol '${parsed.protocol}'. Only HTTP and HTTPS URLs can be analyzed.`,
      };
    }
    return { isValid: true };
  } catch {
    return { isValid: false, error: 'Invalid URL format.' };
  }
}
