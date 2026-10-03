import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { isSensitiveElement, extractSafePageContext } from '../src/content/context';
import { extractVisiblePageText, extractUserSelection } from '../src/capture/extractor';
import { redactSensitivePatterns } from '../src/capture/sanitizer';
import { backgroundState } from '../src/background/state';

describe('Privacy Safeguards & Sensitive Field Neutralization (Phase 13.2 Section 34 Tests A-J)', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  // Test A: Selected text capture captures only selection
  it('Test A: Selected text capture captures strictly the highlighted text without surrounding paragraphs', () => {
    const p1 = document.createElement('p');
    p1.textContent = 'Unrelated introductory paragraph before the selected section.';
    const p2 = document.createElement('p');
    p2.textContent = 'TARGET: Guaranteed 25% weekly returns via Telegram trading robot.';
    const p3 = document.createElement('p');
    p3.textContent = 'Unrelated footer terms after the selected section.';

    document.body.appendChild(p1);
    document.body.appendChild(p2);
    document.body.appendChild(p3);

    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 1,
      isCollapsed: false,
      anchorNode: p2,
      focusNode: p2,
      toString: () => 'TARGET: Guaranteed 25% weekly returns via Telegram trading robot.',
    } as unknown as Selection);

    const result = extractUserSelection(window);

    expect(result.isValid).toBe(true);
    expect(result.status).toBe('CAPTURED');
    expect(result.sanitizedText).toBe('TARGET: Guaranteed 25% weekly returns via Telegram trading robot.');
    expect(result.sanitizedText).not.toContain('Unrelated introductory paragraph');
    expect(result.sanitizedText).not.toContain('Unrelated footer terms');

    window.getSelection = originalGetSelection;
  });

  // Test B: Page capture excludes hidden fields
  it('Test B: Page capture excludes elements with display:none, visibility:hidden, hidden, and aria-hidden', () => {
    const visibleP = document.createElement('p');
    visibleP.textContent = 'Visible financial educational article on mutual funds.';

    const hiddenDiv = document.createElement('div');
    hiddenDiv.setAttribute('style', 'display: none;');
    hiddenDiv.textContent = 'SECRET_HIDDEN_DATA: Internal tracking code 998877';

    const hiddenAttrP = document.createElement('p');
    hiddenAttrP.setAttribute('hidden', '');
    hiddenAttrP.textContent = 'HIDDEN_ATTR_DATA: Should not be captured';

    const ariaHiddenP = document.createElement('p');
    ariaHiddenP.setAttribute('aria-hidden', 'true');
    ariaHiddenP.textContent = 'ARIA_HIDDEN_DATA: Screenreader hidden text';

    document.body.appendChild(visibleP);
    document.body.appendChild(hiddenDiv);
    document.body.appendChild(hiddenAttrP);
    document.body.appendChild(ariaHiddenP);

    const result = extractVisiblePageText(document);

    expect(result.isValid).toBe(true);
    expect(result.sanitizedText).toContain('Visible financial educational article');
    expect(result.sanitizedText).not.toContain('SECRET_HIDDEN_DATA');
    expect(result.sanitizedText).not.toContain('HIDDEN_ATTR_DATA');
    expect(result.sanitizedText).not.toContain('ARIA_HIDDEN_DATA');
  });

  // Test C: Password field values are never captured
  it('Test C: Password field values are never captured or queried', () => {
    const p = document.createElement('p');
    p.textContent = 'Account login portal for mutual fund management.';
    document.body.appendChild(p);

    const form = document.createElement('form');
    const pwdInput = document.createElement('input');
    pwdInput.type = 'password';
    pwdInput.value = 'SuperSecretPassword!2026';
    pwdInput.id = 'login-password';
    form.appendChild(pwdInput);
    document.body.appendChild(form);

    expect(isSensitiveElement(pwdInput)).toBe(true);

    const pageResult = extractVisiblePageText(document);
    expect(pageResult.isValid).toBe(true);
    expect(pageResult.sanitizedText).toContain('Account login portal');
    expect(pageResult.sanitizedText || '').not.toContain('SuperSecretPassword!2026');
  });

  // Test D: OTP / PIN values are never captured
  it('Test D: OTP and PIN fields and values are never captured', () => {
    const p = document.createElement('p');
    p.textContent = 'Two-factor authentication step.';
    document.body.appendChild(p);

    const otpInput = document.createElement('input');
    otpInput.type = 'text';
    otpInput.name = 'otp_code';
    otpInput.value = '987654';

    const pinInput = document.createElement('input');
    pinInput.type = 'text';
    pinInput.name = 'atm_pin';
    pinInput.value = '4321';

    document.body.appendChild(otpInput);
    document.body.appendChild(pinInput);

    expect(isSensitiveElement(otpInput)).toBe(true);
    expect(isSensitiveElement(pinInput)).toBe(true);

    const pageResult = extractVisiblePageText(document);
    expect(pageResult.isValid).toBe(true);
    expect(pageResult.sanitizedText).toContain('Two-factor authentication step.');
    expect(pageResult.sanitizedText || '').not.toContain('987654');
    expect(pageResult.sanitizedText || '').not.toContain('4321');
  });

  // Test E: CVV / card-number fields are never captured, and accidental card numbers are redacted
  it('Test E: CVV and card-number fields are never captured, and numbers in text are redacted', () => {
    const cardInput = document.createElement('input');
    cardInput.type = 'text';
    cardInput.name = 'credit_card_number';
    cardInput.value = '4532-1188-9922-3344';
    document.body.appendChild(cardInput);

    expect(isSensitiveElement(cardInput)).toBe(true);

    // Also test sanitization layer redacting accidental card and cvv patterns
    const rawText = 'Please send fees to card 4532 1188 9922 3344 with CVV: 891';
    const { text, hadRedactions } = redactSensitivePatterns(rawText);

    expect(hadRedactions).toBe(true);
    expect(text).toContain('[CARD_NUMBER_REDACTED');
    expect(text).toContain('[CVV_REDACTED]');
    expect(text).not.toContain('4532 1188');
    expect(text).not.toContain('891');
  });

  // Test F: No cookies are captured
  it('Test F: No document.cookie or cookie values are captured in context or payload', () => {
    document.cookie = 'session_jwt=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test; path=/';
    const p = document.createElement('p');
    p.textContent = 'Banking overview session page.';
    document.body.appendChild(p);

    const context = extractSafePageContext();
    expect((context as any).cookies).toBeUndefined();
    expect((context as any).cookie).toBeUndefined();

    const pageResult = extractVisiblePageText(document);
    expect(pageResult.isValid).toBe(true);
    expect(pageResult.sanitizedText || '').not.toContain('session_jwt');
  });

  // Test G: No keystroke event listeners are registered
  it('Test G: No keydown, keyup, or input surveillance listeners are registered', () => {
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
    const docAddEventListenerSpy = vi.spyOn(document, 'addEventListener');

    // Trigger extraction
    extractVisiblePageText(document);
    extractSafePageContext();

    const monitoredEvents = ['keydown', 'keyup', 'keypress', 'input', 'beforeinput'];
    for (const eventName of monitoredEvents) {
      expect(addEventListenerSpy).not.toHaveBeenCalledWith(eventName, expect.any(Function));
      expect(docAddEventListenerSpy).not.toHaveBeenCalledWith(eventName, expect.any(Function));
    }
  });

  // Test H: No local/session storage is captured
  it('Test H: No localStorage or sessionStorage contents are accessed or captured', () => {
    localStorage.setItem('auth_token_key', 'SECRET_LOCAL_STORAGE_VAL');
    sessionStorage.setItem('temp_session_key', 'SECRET_SESSION_STORAGE_VAL');
    const p = document.createElement('p');
    p.textContent = 'Secure wallet balance display.';
    document.body.appendChild(p);

    const context = extractSafePageContext();
    expect((context as any).localStorage).toBeUndefined();
    expect((context as any).sessionStorage).toBeUndefined();

    const pageResult = extractVisiblePageText(document);
    expect(pageResult.isValid).toBe(true);
    expect(pageResult.sanitizedText || '').not.toContain('SECRET_LOCAL_STORAGE_VAL');
    expect(pageResult.sanitizedText || '').not.toContain('SECRET_SESSION_STORAGE_VAL');
  });

  // Test I: No authentication tokens are captured in payload metadata
  it('Test I: No authorization headers or bearer tokens are captured in metadata', () => {
    const context = extractSafePageContext();
    expect((context as any).authorization).toBeUndefined();
    expect((context as any).token).toBeUndefined();
    expect((context as any).bearerToken).toBeUndefined();
  });

  // Test J: No complete browsing history is collected
  it('Test J: No browsing history or unrelated tab URLs are persisted in runtime state', () => {
    const state = backgroundState.getState();
    expect((state as any).history).toBeUndefined();
    expect((state as any).visitedUrls).toBeUndefined();
    expect((state as any).tabHistory).toBeUndefined();
  });
});
