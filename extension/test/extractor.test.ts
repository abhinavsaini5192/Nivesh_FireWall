import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { extractVisiblePageText, extractUserSelection, isElementHidden } from '../src/capture/extractor';

describe('DOM Visible Content Extractor (Phase 13.2 Sections 6, 7, 8, 9, 35)', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  it('correctly identifies hidden elements via attributes and inline styles', () => {
    const hiddenAttrEl = document.createElement('div');
    hiddenAttrEl.setAttribute('hidden', '');
    expect(isElementHidden(hiddenAttrEl)).toBe(true);

    const ariaHiddenEl = document.createElement('div');
    ariaHiddenEl.setAttribute('aria-hidden', 'true');
    expect(isElementHidden(ariaHiddenEl)).toBe(true);

    const displayNoneEl = document.createElement('div');
    displayNoneEl.setAttribute('style', 'display:none;');
    expect(isElementHidden(displayNoneEl)).toBe(true);

    const visHiddenEl = document.createElement('div');
    visHiddenEl.setAttribute('style', 'visibility: hidden;');
    expect(isElementHidden(visHiddenEl)).toBe(true);

    const visibleEl = document.createElement('div');
    expect(isElementHidden(visibleEl)).toBe(false);
  });

  it('extracts visible page text preserving structural paragraphs and excluding scripts/styles', () => {
    document.body.innerHTML = `
      <header>
        <h1>Prime High-Yield Fund</h1>
      </header>
      <script>var x = "SHOULD_BE_IGNORED";</script>
      <style>.test { color: red; }</style>
      <main>
        <p>Deposit 100 USDT today to receive guaranteed 30% monthly ROI.</p>
        <p>Withdrawals are instant and fully insured by smart contracts.</p>
      </main>
      <footer>
        <span style="display: none;">Technical tracking footer ID 12345</span>
      </footer>
    `;

    const result = extractVisiblePageText(document);

    expect(result.isValid).toBe(true);
    expect(result.status).toBe('CAPTURED');
    expect(result.sanitizedText).toContain('Deposit 100 USDT today to receive guaranteed 30% monthly ROI.');
    expect(result.sanitizedText).toContain('Withdrawals are instant and fully insured');
    expect(result.sanitizedText).not.toContain('SHOULD_BE_IGNORED');
    expect(result.sanitizedText).not.toContain('Technical tracking footer');
  });

  it('returns EMPTY_CONTENT when the document body has no visible text', () => {
    document.body.innerHTML = `
      <div style="display: none;">Only hidden text</div>
      <script>console.log("script");</script>
    `;

    const result = extractVisiblePageText(document);
    expect(result.isValid).toBe(false);
    expect(result.status).toBe('EMPTY_CONTENT');
  });

  it('returns NO_SELECTION when user has not selected text on the active window', () => {
    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 0,
      isCollapsed: true,
      toString: () => '',
    } as unknown as Selection);

    const result = extractUserSelection(window);

    expect(result.isValid).toBe(false);
    expect(result.status).toBe('NO_SELECTION');
    expect(result.error).toContain('No text is currently selected');

    window.getSelection = originalGetSelection;
  });

  it('returns CONTENT_TOO_LARGE when selected text exceeds safe limit', () => {
    const massiveText = 'A'.repeat(6000);
    const p = document.createElement('p');
    p.textContent = massiveText;
    document.body.appendChild(p);

    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 1,
      isCollapsed: false,
      anchorNode: p,
      toString: () => massiveText,
    } as unknown as Selection);

    const result = extractUserSelection(window);

    expect(result.isValid).toBe(false);
    expect(result.status).toBe('CONTENT_TOO_LARGE');
    expect(result.error).toContain('exceeds safe limit');

    window.getSelection = originalGetSelection;
  });

  it('returns NO_SELECTION if user selection originates within a password field', () => {
    const pwdInput = document.createElement('input');
    pwdInput.type = 'password';
    pwdInput.value = 'bankSecretPassword';
    document.body.appendChild(pwdInput);

    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 1,
      isCollapsed: false,
      anchorNode: pwdInput,
      toString: () => 'bankSecretPassword',
    } as unknown as Selection);

    const result = extractUserSelection(window);

    expect(result.isValid).toBe(false);
    expect(result.status).toBe('NO_SELECTION');
    expect(result.error).toContain('credential or financial field');

    window.getSelection = originalGetSelection;
  });
});
