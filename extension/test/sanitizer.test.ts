import { describe, it, expect } from 'vitest';
import {
  normalizeTextContent,
  redactSensitivePatterns,
  validateAndSanitizeContent,
  MAX_SELECTION_LENGTH,
} from '../src/capture/sanitizer';

describe('Capture Sanitization & Normalization Layer (Phase 13.2 Sections 14, 15, 17)', () => {
  it('strips control characters and normalizes erratic line breaks and spaces', () => {
    const raw = 'Heading line   \t   with spaces\r\n\r\n\r\n\r\nParagraph \u0000text\u001F here.';
    const normalized = normalizeTextContent(raw);

    expect(normalized).not.toContain('\u0000');
    expect(normalized).not.toContain('\u001F');
    expect(normalized).not.toContain('\r');
    expect(normalized).not.toContain('\n\n\n');
    expect(normalized).toContain('Heading line with spaces');
    expect(normalized).toContain('Paragraph text here.');
  });

  it('redacts full credit card numbers, CVVs, and PINs from captured text', () => {
    const raw = 'Send transfer to card 5412-7512-3412-3456 with cvv: 432 and pin: 9090.';
    const { text, hadRedactions } = redactSensitivePatterns(raw);

    expect(hadRedactions).toBe(true);
    expect(text).toContain('[CARD_NUMBER_REDACTED');
    expect(text).toContain('[CVV_REDACTED]');
    expect(text).toContain('[PIN_REDACTED]');
    expect(text).not.toContain('5412-7512-3412-3456');
    expect(text).not.toContain('432');
    expect(text).not.toContain('9090');
  });

  it('handles clean text without triggering false positive redactions', () => {
    const benign = 'The Nifty 50 index rose 1.5% today led by banking and IT stocks.';
    const { text, hadRedactions } = redactSensitivePatterns(benign);

    expect(hadRedactions).toBe(false);
    expect(text).toBe(benign);
  });

  it('enforces size limits and returns CONTENT_TOO_LARGE when exceeded', () => {
    const longText = 'x'.repeat(MAX_SELECTION_LENGTH + 50);
    const result = validateAndSanitizeContent(longText, 'SELECTED_TEXT');

    expect(result.isValid).toBe(false);
    expect(result.status).toBe('CONTENT_TOO_LARGE');
    expect(result.error).toContain('exceeds safe limit');
  });

  it('returns appropriate empty status for empty strings', () => {
    const selResult = validateAndSanitizeContent('   ', 'SELECTED_TEXT');
    expect(selResult.isValid).toBe(false);
    expect(selResult.status).toBe('NO_SELECTION');

    const pageResult = validateAndSanitizeContent('', 'CURRENT_PAGE');
    expect(pageResult.isValid).toBe(false);
    expect(pageResult.status).toBe('EMPTY_CONTENT');
  });

  it('successfully processes valid financial text and returns CAPTURED status', () => {
    const validText = 'Invest in mutual funds systematically via SIP to average out market volatility.';
    const result = validateAndSanitizeContent(validText, 'SELECTED_TEXT');

    expect(result.isValid).toBe(true);
    expect(result.status).toBe('CAPTURED');
    expect(result.sanitizedText).toBe(validText);
  });
});
