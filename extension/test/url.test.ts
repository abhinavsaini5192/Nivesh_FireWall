import { describe, it, expect } from 'vitest';
import { isUnsupportedPageUrl, getSanitizedDisplayUrl, isValidAnalysisUrl } from '../src/capture/url';

describe('URL Privacy & Validation Layer (Phase 13.2 Sections 12, 13, 22)', () => {
  it('correctly identifies unsupported browser-internal and extension scheme URLs', () => {
    expect(isUnsupportedPageUrl('chrome://settings')).toBe(true);
    expect(isUnsupportedPageUrl('edge://extensions')).toBe(true);
    expect(isUnsupportedPageUrl('about:blank')).toBe(true);
    expect(isUnsupportedPageUrl('chrome-extension://abcdef/popup.html')).toBe(true);
    expect(isUnsupportedPageUrl('devtools://devtools/bundled/inspector.html')).toBe(true);
    expect(isUnsupportedPageUrl('view-source:https://example.com')).toBe(true);

    expect(isUnsupportedPageUrl('https://invest.example.com/schemes')).toBe(false);
    expect(isUnsupportedPageUrl('http://localhost:5173')).toBe(false);
  });

  it('generates privacy-safe display URLs by stripping tracking parameters and redacting session tokens', () => {
    const rawUrl =
      'https://fintech-portal.com/transfer?utm_source=facebook&utm_campaign=winter&token=secret_jwt_token_123&session_id=sess_456&category=stocks';

    const displayUrl = getSanitizedDisplayUrl(rawUrl);

    // Strips tracking params
    expect(displayUrl).not.toContain('utm_source');
    expect(displayUrl).not.toContain('utm_campaign');

    // Redacts sensitive auth/session tokens
    expect(displayUrl).toContain('token=%5BREDACTED%5D');
    expect(displayUrl).toContain('session_id=%5BREDACTED%5D');

    // Preserves benign business query parameters
    expect(displayUrl).toContain('category=stocks');
    expect(displayUrl).toContain('https://fintech-portal.com/transfer');
  });

  it('validates URLs for backend analysis compatibility', () => {
    expect(isValidAnalysisUrl('https://valid-bank.com').isValid).toBe(true);
    expect(isValidAnalysisUrl('http://localhost:8000/api').isValid).toBe(true);

    const empty = isValidAnalysisUrl('');
    expect(empty.isValid).toBe(false);
    expect(empty.error).toContain('cannot be empty');

    const ftp = isValidAnalysisUrl('ftp://files.example.com');
    expect(ftp.isValid).toBe(false);
    expect(ftp.error).toContain('Unsupported protocol');
  });
});
