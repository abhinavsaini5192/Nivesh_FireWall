import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { isSensitiveElement, getSafeUserSelection, extractSafePageContext } from '../src/content/context';

describe('Privacy Safeguards & Sensitive Field Neutralization (Phase 13.1 Sections 11, 19, 20)', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('detects and flags password input fields as sensitive', () => {
    const input = document.createElement('input');
    input.type = 'password';
    input.id = 'user-password';
    document.body.appendChild(input);

    expect(isSensitiveElement(input)).toBe(true);
  });

  it('detects and flags hidden input fields as sensitive', () => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'csrf_token';
    input.value = 'secret123';
    document.body.appendChild(input);

    expect(isSensitiveElement(input)).toBe(true);
  });

  it('detects and flags OTP, PIN, CVV, Card Number, and SSN fields as sensitive', () => {
    const testCases = [
      { name: 'otp_code', placeholder: 'Enter 6-digit OTP' },
      { name: 'login_pin', placeholder: 'ATM PIN' },
      { name: 'card_cvv', placeholder: 'CVV/CVC' },
      { id: 'credit_card_number', placeholder: 'Card Number' },
      { name: 'user_ssn', placeholder: 'Social Security Number' },
      { autocomplete: 'one-time-code', name: 'verification' },
      { name: 'api_token', placeholder: 'Bearer token' },
      { name: 'user_passcode', placeholder: 'Enter Passcode' },
    ];

    for (const testCase of testCases) {
      const input = document.createElement('input');
      input.type = 'text';
      if (testCase.name) input.name = testCase.name;
      if (testCase.id) input.id = testCase.id;
      if (testCase.placeholder) input.placeholder = testCase.placeholder;
      if (testCase.autocomplete) input.setAttribute('autocomplete', testCase.autocomplete);

      document.body.appendChild(input);
      expect(isSensitiveElement(input)).toBe(true);
      document.body.removeChild(input);
    }
  });

  it('permits non-sensitive standard inputs (search, amount, notes, username query)', () => {
    const input = document.createElement('input');
    input.type = 'text';
    input.name = 'search_query';
    input.placeholder = 'Search stocks, mutual funds, or articles';
    document.body.appendChild(input);

    expect(isSensitiveElement(input)).toBe(false);
  });

  it('refuses to extract selection if anchor originates inside a sensitive element', () => {
    const form = document.createElement('form');
    const sensitiveInput = document.createElement('input');
    sensitiveInput.type = 'password';
    sensitiveInput.value = 'mySecretPassword123';
    form.appendChild(sensitiveInput);
    document.body.appendChild(form);

    // Mock window.getSelection to simulate selection inside sensitive element
    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 1,
      isCollapsed: false,
      anchorNode: sensitiveInput,
      toString: () => 'mySecretPassword123',
    } as unknown as Selection);

    const safeText = getSafeUserSelection();
    expect(safeText).toBeUndefined();

    window.getSelection = originalGetSelection;
  });

  it('extracts sanitized text from benign elements and strips control characters', () => {
    const paragraph = document.createElement('p');
    paragraph.textContent = 'Guaranteed 50% returns in 3 days! Join Telegram channel now.';
    document.body.appendChild(paragraph);

    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 1,
      isCollapsed: false,
      anchorNode: paragraph,
      toString: () => 'Guaranteed 50% returns in 3 days!\u0000\u0007 Join Telegram channel now.',
    } as unknown as Selection);

    const safeText = getSafeUserSelection();
    expect(safeText).toBeDefined();
    expect(safeText).not.toContain('\u0000');
    expect(safeText).not.toContain('\u0007');
    expect(safeText).toBe('Guaranteed 50% returns in 3 days! Join Telegram channel now.');

    window.getSelection = originalGetSelection;
  });

  it('safely extracts metadata from document head and bounds lengths', () => {
    document.title = 'Guaranteed Forex Arbitrage - Instant Wealth';
    const metaDesc = document.createElement('meta');
    metaDesc.name = 'description';
    metaDesc.content = 'Official high-yield investment scheme platform.';
    document.head.appendChild(metaDesc);

    const context = extractSafePageContext({ maxContentLength: 1000 });

    expect(context.pageTitle).toBe('Guaranteed Forex Arbitrage - Instant Wealth');
    expect(context.metaDescription).toBe('Official high-yield investment scheme platform.');
    expect(context.capturedAt).toBeDefined();
    expect(new Date(context.capturedAt).getTime()).not.toBeNaN();
  });
});
