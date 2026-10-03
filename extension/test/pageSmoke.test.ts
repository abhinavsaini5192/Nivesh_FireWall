import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { extractVisiblePageText, extractUserSelection } from '../src/capture/extractor';
import { routeExtensionMessage } from '../src/background/router';
import { backgroundState } from '../src/background/state';
import { generateCaptureId, type CapturePayload } from '../src/types/capture';
import type { ScanRequestMessage } from '../src/types/messages';

describe('Real-Page & Full-Page Capture Smoke Scenarios (Phase 13.2 Sections 38, 39, 40)', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    document.body.innerHTML = '';
    backgroundState.reset();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    document.body.innerHTML = '';
    globalThis.fetch = originalFetch;
  });

  // Section 38: Controlled page with promotional text, testing selection capture through to Unified API
  it('Section 38: Selected text capture on promotional page captures text and sends structured payload to Unified API', async () => {
    document.body.innerHTML = `
      <div class="article">
        <h1>Learn About Mutual Funds</h1>
        <p class="intro">Standard mutual funds pool money from investors into stocks and bonds.</p>
        <div class="user-comment">
          <p id="target-promo">Guaranteed returns. Contact us on Telegram. Install our application and make a payment.</p>
        </div>
      </div>
    `;

    const targetEl = document.getElementById('target-promo')!;
    const originalGetSelection = window.getSelection;
    window.getSelection = () => ({
      rangeCount: 1,
      isCollapsed: false,
      anchorNode: targetEl,
      focusNode: targetEl,
      toString: () => 'Guaranteed returns. Contact us on Telegram. Install our application and make a payment.',
    } as unknown as Selection);

    // 1. Capture via Extractor
    const captureResult = extractUserSelection(window);
    expect(captureResult.isValid).toBe(true);
    expect(captureResult.status).toBe('CAPTURED');
    expect(captureResult.sanitizedText).toBe(
      'Guaranteed returns. Contact us on Telegram. Install our application and make a payment.'
    );

    // 2. Package CapturePayload
    const capId = generateCaptureId();
    const capture: CapturePayload = {
      captureId: capId,
      sourceType: 'SELECTED_TEXT',
      status: 'CAPTURED',
      text: captureResult.sanitizedText,
      url: 'https://finance-portal.test/mutual-funds',
      displayUrl: 'https://finance-portal.test/mutual-funds',
      pageTitle: 'Learn About Mutual Funds',
      pageOrigin: 'https://finance-portal.test',
      tabId: 101,
      timestamp: new Date().toISOString(),
      contentLength: captureResult.sanitizedText!.length,
      sanitized: true,
    };

    // 3. Mock Unified Firewall API
    const mockApiResponse = {
      analysis_id: 'ANA-PROMO-7711',
      completed_at: new Date().toISOString(),
      decision: {
        decision: 'BLOCK',
        severity: 'CRITICAL',
        primary_reason: 'High-risk unverified payment solicitation and guaranteed return scheme.',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockApiResponse),
    } as Response);

    // 4. Dispatch through background handler
    const scanMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'EXT-REQ-PROMO',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture,
      },
    };

    const res = await routeExtensionMessage(scanMsg);

    expect(res.success).toBe(true);
    expect((res.data as any).analysisId).toBe('ANA-PROMO-7711');
    expect((res.data as any).decision).toBe('BLOCK');

    // Verify structured payload sent to Unified API
    const callArgs = (globalThis.fetch as any).mock.calls[0];
    const body = JSON.parse(callArgs[1].body);
    expect(body.input_type).toBe('text');
    expect(body.text).toContain('Guaranteed returns. Contact us on Telegram');
    expect(body.channel).toBe('web');

    window.getSelection = originalGetSelection;
  });

  // Section 39: Full-Page Smoke Test on the same page, verifying visible text is captured and hidden elements are excluded
  it('Section 39: Full page capture captures visible text while excluding hidden fields, passwords, and tracking scripts', () => {
    document.body.innerHTML = `
      <header>
        <h1>Learn About Mutual Funds</h1>
      </header>
      <script>var trackingToken = "SECRET_TRACKER_TOKEN_999";</script>
      <style>.hidden { display: none; }</style>
      <main>
        <p>Standard mutual funds pool money from investors into stocks and bonds.</p>
        <div class="user-comment">
          <p>Guaranteed returns. Contact us on Telegram. Install our application and make a payment.</p>
        </div>
        <form style="display: none;">
          <input type="password" value="HiddenAdminPassword123" />
          <input type="text" name="otp" value="998877" />
        </form>
      </main>
      <footer>
        <span style="display: none;">Internal admin telemetry</span>
      </footer>
    `;

    const pageResult = extractVisiblePageText(document);

    expect(pageResult.isValid).toBe(true);
    expect(pageResult.status).toBe('CAPTURED');
    expect(pageResult.sanitizedText).toContain('Learn About Mutual Funds');
    expect(pageResult.sanitizedText).toContain('Standard mutual funds pool money');
    expect(pageResult.sanitizedText).toContain('Guaranteed returns. Contact us on Telegram');

    // Excluded items
    expect(pageResult.sanitizedText).not.toContain('SECRET_TRACKER_TOKEN_999');
    expect(pageResult.sanitizedText).not.toContain('HiddenAdminPassword123');
    expect(pageResult.sanitizedText).not.toContain('998877');
    expect(pageResult.sanitizedText).not.toContain('Internal admin telemetry');
  });

  // Section 40: Benign Page Test
  it('Section 40: Benign educational page captures normally without extension attempting to score or label it', () => {
    document.body.innerHTML = `
      <main>
        <h1>How Mutual Funds Work</h1>
        <p>Learn how mutual funds work. Review diversification and expense ratios.</p>
        <p>A balanced portfolio helps manage long-term equity risk.</p>
      </main>
    `;

    const result = extractVisiblePageText(document);

    expect(result.isValid).toBe(true);
    expect(result.status).toBe('CAPTURED');
    expect(result.sanitizedText).toContain('Learn how mutual funds work.');
    expect(result.sanitizedText).toContain('Review diversification and expense ratios.');

    // Structural integrity: capture result contains zero threat labels or policy claims
    expect((result as any).threat).toBeUndefined();
    expect((result as any).isFraud).toBeUndefined();
    expect((result as any).riskScore).toBeUndefined();
    expect((result as any).decision).toBeUndefined();
  });
});
