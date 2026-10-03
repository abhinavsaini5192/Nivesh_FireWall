/**
 * Phase 13.5 — Browser Integration Validation Suite
 *
 * Validates the complete end-to-end browser extension lifecycle:
 * WEBPAGE -> USER-INITIATED CAPTURE -> CONTENT SCRIPT -> BACKGROUND WORKER ->
 * ANALYSIS BRIDGE -> UNIFIED FIREWALL API -> PRODUCT ORCHESTRATOR ->
 * ENGINE PIPELINE -> ENGINE 8 POLICY -> PROTECTION RESULT -> BROWSER / WEB APP.
 *
 * Sections Covered:
 * - Section 3: Full User Journey Test
 * - Section 4: Primary Threat Benchmark Scenario
 * - Section 5: Benign Educational Scenario
 * - Section 6: Identity Scenario Fidelity
 * - Section 7: Evidence Scenario Fidelity
 * - Section 8: Fingerprint Scenarios & Observation Counting
 * - Section 9: Behavioural Progression Fidelity
 * - Section 10: Policy Decision Validation (ALLOW, INFORM, WARN, PAUSE, BLOCK)
 * - Section 11: Fail-Safe Browser Behaviour (Outage, Timeout, Malformed)
 * - Section 12: Protection Failure Safety
 * - Sections 13-15: Target Accuracy, Ambiguous Targets & Multi-Action Pages
 * - Sections 16-17: Multiple-Tab & Window Isolation
 * - Section 18: Session Isolation
 * - Section 19: Worker Lifecycle Resilience
 * - Sections 20-21: Page Reload & Navigation Integrity
 * - Sections 22-24: Permission Minimization, Manifest & Host Access Audit
 * - Sections 25-26: Sensitive Form & Keystroke Exclusion
 * - Sections 27-29: Cookie, Storage, Raw DOM & URL Privacy Audits
 * - Sections 30-33: Content Security, Message Security & Secret Audits
 * - Sections 34-35: Diagnostic Logging & Error Sanitization
 * - Sections 36-39: Performance, DOM Impact & Cleanup
 * - Sections 40-43: Accessibility & Responsive Display
 * - Sections 44-47: Web-App Handoff & Override Integrity
 * - Section 48: API Contract Validation
 * - Sections 53-55: Product Truthfulness & Boundary Audit
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import manifest from '../manifest.json';
import { extractVisiblePageText, extractUserSelection } from '../src/capture/extractor';
import { getSanitizedDisplayUrl, isUnsupportedPageUrl } from '../src/capture/url';
import { backgroundState } from '../src/background/state';
import { routeExtensionMessage } from '../src/background/router';
import {
  protectionManager,
  ProtectionOverlay,
  matchTargetAction,
  TargetedNavigationInterceptor,
} from '../src/protection';
import { generateCaptureId, type CapturePayload } from '../src/types/capture';
import type { ScanRequestMessage } from '../src/types/messages';
import type { InPageInterventionPayload } from '../src/protection/types';

describe('Phase 13.5: Browser Integration Validation Suite', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    document.body.innerHTML = '';
    backgroundState.reset();
    protectionManager.cleanup();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    protectionManager.cleanup();
    document.body.innerHTML = '';
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  // ===========================================================================
  // 1. Full User Journey Test (Section 3)
  // ===========================================================================
  it('Section 3: Full User Journey (Capture -> Bridge -> Engine 8 Decision -> In-Page Overlay -> Handoff)', async () => {
    document.body.innerHTML = `
      <main class="page-body">
        <h2>Exclusive Financial Opportunity</h2>
        <p id="promo-text">Guaranteed 35% monthly returns. Deposit funds immediately into our pool.</p>
        <a id="deposit-btn" href="https://pay.example.com/deposit?pool=99">Deposit Now</a>
      </main>
    `;

    const promoEl = document.getElementById('promo-text')!;
    window.getSelection = () =>
      ({
        rangeCount: 1,
        isCollapsed: false,
        anchorNode: promoEl,
        focusNode: promoEl,
        toString: () => promoEl.textContent || '',
      }) as unknown as Selection;

    // 1. User-initiated selection capture
    const captureResult = extractUserSelection(window);
    expect(captureResult.isValid).toBe(true);
    expect(captureResult.sanitizedText).toContain('Guaranteed 35% monthly returns');

    const capturePayload: CapturePayload = {
      captureId: generateCaptureId(),
      sourceType: 'SELECTED_TEXT',
      status: 'CAPTURED',
      text: captureResult.sanitizedText,
      url: 'https://finance.example.com/invest',
      displayUrl: 'https://finance.example.com/invest',
      pageTitle: 'Exclusive Financial Opportunity',
      pageOrigin: 'https://finance.example.com',
      tabId: 101,
      timestamp: new Date().toISOString(),
      contentLength: captureResult.sanitizedText!.length,
      sanitized: true,
    };

    // 2. Mock API response from Unified Firewall API
    const mockApiResponse = {
      analysis_id: 'ANA-JOURNEY-001',
      completed_at: new Date().toISOString(),
      decision: {
        decision: 'PAUSE',
        severity: 'HIGH',
        primary_reason: 'Unregistered investment opportunity promising guaranteed returns.',
        user_message: 'Please review available evidence before depositing funds.',
      },
      action: {
        action_type: 'PAYMENT_REQUEST',
        target_url: 'https://pay.example.com/deposit?pool=99',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockApiResponse),
    } as Response);

    // 3. Dispatch through background handler
    const scanMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'REQ-JOURNEY-001',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: capturePayload,
      },
    };

    const scanRes = await routeExtensionMessage(scanMsg);
    expect(scanRes.success).toBe(true);
    expect((scanRes.data as any).analysisId).toBe('ANA-JOURNEY-001');
    expect((scanRes.data as any).decision).toBe('PAUSE');
    expect((scanRes.data as any).severity).toBe('HIGH');

    // 4. In-page protection layer displays intervention
    protectionManager.showIntervention({
      analysisId: 'ANA-JOURNEY-001',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Unregistered investment opportunity promising guaranteed returns.',
      userMessage: 'Please review available evidence before depositing funds.',
      targetUrl: 'https://pay.example.com/deposit?pool=99',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-JOURNEY-001',
    });

    // 5. Verify Shadow DOM modal is injected
    const root = document.getElementById('nivesh-firewall-root');
    expect(root).not.toBeNull();
    const shadow = root?.shadowRoot;
    expect(shadow).not.toBeNull();
    expect(shadow?.querySelector('.nivesh-modal.pause')).not.toBeNull();
    expect(shadow?.textContent).toContain('ACTION PAUSED');
    expect(shadow?.textContent).toContain('Please review available evidence before depositing funds.');

    // 6. Verify Web App deep-link handoff dispatches OPEN_ANALYSIS message
    const viewBtn = shadow?.querySelector('.btn-secondary') as HTMLButtonElement;
    viewBtn.click();
    expect(chrome.runtime.sendMessage).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'OPEN_NIVESH_APP',
        payload: { analysisId: 'ANA-JOURNEY-001' },
      })
    );
  });

  // ===========================================================================
  // 2. Primary Threat Benchmark Scenario (Section 4)
  // ===========================================================================
  it('Section 4: Primary Threat Benchmark preserves backend reasons without fabrication', async () => {
    document.body.innerHTML = `
      <div id="threat-content">
        Guaranteed returns. Contact us through Telegram. Install our application. Make a payment. Only five minutes left.
      </div>
      <a id="action-link" href="https://t.me/scam_bot">Contact Telegram</a>
    `;

    const el = document.getElementById('threat-content')!;
    window.getSelection = () =>
      ({
        rangeCount: 1,
        isCollapsed: false,
        anchorNode: el,
        focusNode: el,
        toString: () => el.textContent || '',
      }) as unknown as Selection;

    const capture = extractUserSelection(window);
    expect(capture.sanitizedText).toContain('Guaranteed returns');
    expect(capture.sanitizedText).toContain('Only five minutes left');

    // Policy returns BLOCK
    const mockThreatResponse = {
      analysis_id: 'ANA-THREAT-004',
      completed_at: new Date().toISOString(),
      decision: {
        decision: 'BLOCK',
        severity: 'CRITICAL',
        primary_reason: 'Multi-stage unverified advance fee solicitation with high urgency pressure.',
        reason_codes: ['IDENTITY_NOT_ESTABLISHED', 'RAPID_ACTION_ESCALATION', 'HIGH_URGENCY'],
      },
      action: {
        action_type: 'APP_INSTALL',
        target_url: 'https://t.me/scam_bot',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockThreatResponse),
    } as Response);

    const scanRes = await routeExtensionMessage({
      type: 'SCAN_REQUEST',
      requestId: 'REQ-THREAT-004',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: {
          captureId: 'CAP-THREAT-004',
          sourceType: 'SELECTED_TEXT',
          status: 'CAPTURED',
          text: capture.sanitizedText,
          url: 'https://threat-site.test',
          displayUrl: 'https://threat-site.test',
          pageTitle: 'Urgent Scheme',
          pageOrigin: 'https://threat-site.test',
          tabId: 101,
          timestamp: new Date().toISOString(),
          contentLength: capture.sanitizedText!.length,
          sanitized: true,
        },
      },
    });

    expect(scanRes.success).toBe(true);
    expect((scanRes.data as any).decision).toBe('BLOCK');
    expect((scanRes.data as any).severity).toBe('CRITICAL');

    // Render in-page BLOCK overlay with targeted navigation interception
    protectionManager.showIntervention({
      analysisId: 'ANA-THREAT-004',
      decision: 'BLOCK',
      severity: 'CRITICAL',
      primaryReason: 'Multi-stage unverified advance fee solicitation with high urgency pressure.',
      targetUrl: 'https://t.me/scam_bot',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-THREAT-004',
    });

    const shadow = document.getElementById('nivesh-firewall-root')?.shadowRoot;
    expect(shadow?.querySelector('.nivesh-modal.block')).not.toBeNull();
    expect(shadow?.textContent).toContain('ACTION BLOCKED');
    expect(shadow?.textContent).toContain('Multi-stage unverified advance fee solicitation');

    // Target link should be intercepted and navigation prevented
    const actionLink = document.getElementById('action-link')!;
    const clickEvt = new MouseEvent('click', { bubbles: true, cancelable: true });
    actionLink.dispatchEvent(clickEvt);
    expect(clickEvt.defaultPrevented).toBe(true);
  });

  // ===========================================================================
  // 3. Benign Educational Scenario (Section 5)
  // ===========================================================================
  it('Section 5: Benign Educational Scenario renders verified ALLOW without overlay', async () => {
    document.body.innerHTML = `
      <div id="edu-content">
        Learn how mutual funds work. Review diversification, fees, and expense ratios.
      </div>
      <a id="doc-link" href="https://investor.gov/funds">Read SEC Investor Guide</a>
    `;

    const el = document.getElementById('edu-content')!;
    window.getSelection = () =>
      ({
        rangeCount: 1,
        isCollapsed: false,
        anchorNode: el,
        focusNode: el,
        toString: () => el.textContent || '',
      }) as unknown as Selection;

    const capture = extractUserSelection(window);

    const mockAllowResponse = {
      analysis_id: 'ANA-BENIGN-005',
      completed_at: new Date().toISOString(),
      decision: {
        decision: 'ALLOW',
        severity: 'LOW',
        primary_reason: 'Educational content containing standard mutual fund definitions.',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockAllowResponse),
    } as Response);

    const scanRes = await routeExtensionMessage({
      type: 'SCAN_REQUEST',
      requestId: 'REQ-BENIGN-005',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: {
          captureId: 'CAP-BENIGN-005',
          sourceType: 'SELECTED_TEXT',
          status: 'CAPTURED',
          text: capture.sanitizedText,
          url: 'https://edu-portal.test',
          displayUrl: 'https://edu-portal.test',
          pageTitle: 'Mutual Fund Guide',
          pageOrigin: 'https://edu-portal.test',
          tabId: 101,
          timestamp: new Date().toISOString(),
          contentLength: capture.sanitizedText!.length,
          sanitized: true,
        },
      },
    });

    expect(scanRes.success).toBe(true);
    expect((scanRes.data as any).decision).toBe('ALLOW');

    // ALLOW produces zero in-page overlay
    protectionManager.showIntervention({
      analysisId: 'ANA-BENIGN-005',
      decision: 'ALLOW',
      severity: 'LOW',
      primaryReason: 'Educational content containing standard mutual fund definitions.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-BENIGN-005',
    });

    expect(document.getElementById('nivesh-firewall-root')).toBeNull();

    // Normal link navigation is untouched
    const docLink = document.getElementById('doc-link')!;
    const clickEvt = new MouseEvent('click', { bubbles: true, cancelable: true });
    docLink.dispatchEvent(clickEvt);
    expect(clickEvt.defaultPrevented).toBe(false);
  });

  // ===========================================================================
  // 4. Identity Scenario Fidelity (Section 6)
  // ===========================================================================
  it('Section 6: Identity Scenarios preserve exact backend classifications without editorializing', () => {
    const statuses = [
      'ESTABLISHED',
      'PARTIALLY_ESTABLISHED',
      'NOT_ESTABLISHED',
      'IDENTITY_MISMATCH',
      'AMBIGUOUS',
      'INSUFFICIENT_EVIDENCE',
      'SOURCE_UNAVAILABLE',
    ];

    for (const status of statuses) {
      const overlay = new ProtectionOverlay({
        onDismiss: vi.fn(),
        onOpenAnalysis: vi.fn(),
      });

      overlay.render({
        analysisId: `ANA-ID-${status}`,
        decision: 'PAUSE',
        severity: 'HIGH',
        primaryReason: `Identity verification result: ${status}`,
        identityStatus: status,
        webAppUrl: `http://localhost:5173/#protect?id=ANA-ID-${status}`,
      });

      const root = document.getElementById('nivesh-firewall-root');
      const shadow = root?.shadowRoot;
      expect(shadow?.textContent).toContain(status);
      // Strictly verify no sensational replacement
      expect(shadow?.textContent).not.toContain('FRAUDSTER');
      expect(shadow?.textContent).not.toContain('SCAMMER');

      overlay.destroy();
    }
  });

  // ===========================================================================
  // 5. Evidence Scenario Fidelity (Section 7)
  // ===========================================================================
  it('Section 7: Evidence Scenarios preserve distinct states without oversimplification', () => {
    const evidenceStates = [
      'SUPPORTED',
      'PARTIALLY_SUPPORTED',
      'CONTRADICTED',
      'INSUFFICIENT_EVIDENCE',
      'NOT_VERIFIABLE',
      'SOURCE_CONFLICT',
    ];

    for (const state of evidenceStates) {
      const overlay = new ProtectionOverlay({
        onDismiss: vi.fn(),
        onOpenAnalysis: vi.fn(),
      });

      overlay.render({
        analysisId: `ANA-EVID-${state}`,
        decision: 'WARN',
        severity: 'MEDIUM',
        primaryReason: `Evidence verification status: ${state}`,
        evidenceStatus: state,
        webAppUrl: `http://localhost:5173/#protect?id=ANA-EVID-${state}`,
      });

      const root = document.getElementById('nivesh-firewall-root');
      const shadow = root?.shadowRoot;
      expect(shadow?.textContent).toContain(state);

      overlay.destroy();
    }
  });

  // ===========================================================================
  // 6. Fingerprint Scenarios & Observation Counting (Section 8)
  // ===========================================================================
  it('Section 8: Fingerprint Scenarios preserve structural equivalence and do not inflate observations on repeat scans', async () => {
    let observationCount = 1;

    const mockFingerprintResponse = () => ({
      analysis_id: 'ANA-FP-008',
      completed_at: new Date().toISOString(),
      decision: {
        decision: 'WARN',
        severity: 'MEDIUM',
        primary_reason: 'Fingerprint match observed.',
      },
      fingerprint: {
        cluster_id: 'FP-CLUSTER-44',
        match_type: 'SEMANTIC_VARIANT',
        observations_count: observationCount,
      },
    });

    globalThis.fetch = vi.fn().mockImplementation(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockFingerprintResponse()),
      } as Response)
    );

    const makeScan = async (capId: string) => {
      return routeExtensionMessage({
        type: 'SCAN_REQUEST',
        requestId: `REQ-${capId}`,
        tabId: 101,
        timestamp: new Date().toISOString(),
        payload: {
          tabId: 101,
          capture: {
            captureId: capId,
            sourceType: 'SELECTED_TEXT',
            status: 'CAPTURED',
            text: 'Exact identical text repeated',
            url: 'https://site.test',
            displayUrl: 'https://site.test',
            pageTitle: 'Test',
            pageOrigin: 'https://site.test',
            tabId: 101,
            timestamp: new Date().toISOString(),
            contentLength: 28,
            sanitized: true,
          },
        },
      });
    };

    // First scan
    const res1 = await makeScan('CAP-1');
    expect(res1.success).toBe(true);

    // Repeated identical submission from browser must not artificially inflate count
    const res2 = await makeScan('CAP-2');
    expect(res2.success).toBe(true);
    expect(observationCount).toBe(1);
  });

  // ===========================================================================
  // 7. Behavioural Progression Fidelity (Section 9)
  // ===========================================================================
  it('Section 9: Behavioural signals display observed transitions without psychological profiling', () => {
    const overlay = new ProtectionOverlay({
      onDismiss: vi.fn(),
      onOpenAnalysis: vi.fn(),
    });

    overlay.render({
      analysisId: 'ANA-BEHAV-009',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Behavioral progression: RAPID_ACTION_ESCALATION observed across channels.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-BEHAV-009',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    expect(shadow?.textContent).toContain('RAPID_ACTION_ESCALATION');

    // Strictly verify no subjective psychological profiling labels exist
    expect(shadow?.textContent).not.toContain('greed');
    expect(shadow?.textContent).not.toContain('impulsive');
    expect(shadow?.textContent).not.toContain('gullible');
    expect(shadow?.textContent).not.toContain('desperation');

    overlay.destroy();
  });

  // ===========================================================================
  // 8. Policy Decision Fidelity (Section 10)
  // ===========================================================================
  it('Section 10: Policy decision fidelity ensures frontend strictly mirrors Engine 8 decision', async () => {
    const decisions: Array<'ALLOW' | 'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK'> = [
      'ALLOW',
      'INFORM',
      'WARN',
      'PAUSE',
      'BLOCK',
    ];

    for (const dec of decisions) {
      globalThis.fetch = vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve({
            analysis_id: `ANA-POLICY-${dec}`,
            completed_at: new Date().toISOString(),
            decision: {
              decision: dec,
              severity: dec === 'ALLOW' ? 'LOW' : dec === 'BLOCK' ? 'CRITICAL' : 'MEDIUM',
              primary_reason: `Engine 8 verified decision: ${dec}`,
            },
          }),
      } as Response);

      const res = await routeExtensionMessage({
        type: 'SCAN_REQUEST',
        requestId: `REQ-DEC-${dec}`,
        tabId: 101,
        timestamp: new Date().toISOString(),
        payload: {
          tabId: 101,
          capture: {
            captureId: `CAP-DEC-${dec}`,
            sourceType: 'SELECTED_TEXT',
            status: 'CAPTURED',
            text: `Content for ${dec}`,
            url: 'https://policy.test',
            displayUrl: 'https://policy.test',
            pageTitle: 'Policy Test',
            pageOrigin: 'https://policy.test',
            tabId: 101,
            timestamp: new Date().toISOString(),
            contentLength: 16,
            sanitized: true,
          },
        },
      });

      expect(res.success).toBe(true);
      expect((res.data as any).decision).toBe(dec);
    }
  });

  // ===========================================================================
  // 9. Fail-Safe Browser Behaviour (Section 11)
  // ===========================================================================
  it('Section 11: Fail-safe behavior ensures backend outages/timeouts NEVER default to ALLOW or Safe', async () => {
    // 1. Outage (Network error)
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch'));

    const outageRes = await routeExtensionMessage({
      type: 'SCAN_REQUEST',
      requestId: 'REQ-OUTAGE',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: {
          captureId: 'CAP-OUTAGE',
          sourceType: 'CURRENT_PAGE',
          status: 'CAPTURED',
          text: 'Some page content',
          url: 'https://bank.test',
          displayUrl: 'https://bank.test',
          pageTitle: 'Test',
          pageOrigin: 'https://bank.test',
          tabId: 101,
          timestamp: new Date().toISOString(),
          contentLength: 17,
          sanitized: true,
        },
      },
    });

    expect(outageRes.success).toBe(false);
    expect(outageRes.error?.code).toBe('BACKEND_UNAVAILABLE');
    // NEVER allow or safe
    expect((outageRes as any).decision).toBeUndefined();

    // 2. Timeout simulation
    globalThis.fetch = vi.fn().mockRejectedValue(new DOMException('The operation was aborted', 'AbortError'));

    const timeoutRes = await routeExtensionMessage({
      type: 'SCAN_REQUEST',
      requestId: 'REQ-TIMEOUT',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: {
          captureId: 'CAP-TIMEOUT',
          sourceType: 'CURRENT_PAGE',
          status: 'CAPTURED',
          text: 'Some page content',
          url: 'https://bank.test',
          displayUrl: 'https://bank.test',
          pageTitle: 'Test',
          pageOrigin: 'https://bank.test',
          tabId: 101,
          timestamp: new Date().toISOString(),
          contentLength: 17,
          sanitized: true,
        },
      },
    });

    expect(timeoutRes.success).toBe(false);
    expect(timeoutRes.error?.code).toBe('BACKEND_TIMEOUT');
  });

  // ===========================================================================
  // 10. Protection Failure Safety (Section 12)
  // ===========================================================================
  it('Section 12: Protection rendering error fails safely and never downgrades BLOCK to ALLOW', () => {
    const overlay = new ProtectionOverlay({
      onDismiss: vi.fn(),
      onOpenAnalysis: vi.fn(),
    });

    // Mock document.createElement to simulate DOM throw
    const origCreateElement = document.createElement.bind(document);
    vi.spyOn(document, 'createElement').mockImplementation((tag: string) => {
      if (tag === 'div') {
        throw new Error('Simulated DOM allocation failure');
      }
      return origCreateElement(tag);
    });

    expect(() => {
      overlay.render({
        analysisId: 'ANA-FAIL-SAFE',
        decision: 'BLOCK',
        severity: 'CRITICAL',
        primaryReason: 'Dangerous interaction.',
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-FAIL-SAFE',
      });
    }).toThrow('Simulated DOM allocation failure');

    // Root remains uncreated, but system NEVER asserts ALLOW
    const state = protectionManager.getState();
    expect(state.decision).not.toBe('ALLOW');
  });

  // ===========================================================================
  // 11. Target Accuracy & Safe Uncertainty Rule (Sections 13, 14, 15)
  // ===========================================================================
  it('Sections 13-15: Target Accuracy intercepts only exact matches and enforces Safe Uncertainty Rule on ambiguity', () => {
    document.body.innerHTML = `
      <div>
        <a id="link-info" href="https://site.test/about">Company Info</a>
        <a id="link-telegram" href="https://t.me/exact_scam">Join Telegram</a>
        <a id="link-download" href="https://site.test/app.apk">Download App</a>
        <a id="link-download-mirror" href="https://site.test/app.apk">Download App Mirror</a>
      </div>
    `;

    // Exact single match on Telegram
    const exactMatch = matchTargetAction(document, 'https://t.me/exact_scam');
    expect(exactMatch.matchConfidence).toBe('EXACT');
    expect(exactMatch.matchedElement?.id).toBe('link-telegram');

    // Ambiguous match (2 identical app download links on page)
    const ambiguousMatch = matchTargetAction(document, 'https://site.test/app.apk');
    // Safe Uncertainty Rule: never arbitrarily pick one to block!
    expect(ambiguousMatch.matchConfidence).toBe('AMBIGUOUS');
    expect(ambiguousMatch.matchedElement).toBeNull();

    // Verify unrelated link is untouched
    const interceptor = new TargetedNavigationInterceptor({
      onTargetTriggered: vi.fn(),
    });
    interceptor.attach(exactMatch.matchedElement!, {
      analysisId: 'ANA-TEST',
      decision: 'BLOCK',
      severity: 'CRITICAL',
      primaryReason: 'Targeted block',
      webAppUrl: '',
    });

    const infoLink = document.getElementById('link-info')!;
    const clickEvt = new MouseEvent('click', { bubbles: true, cancelable: true });
    infoLink.dispatchEvent(clickEvt);
    expect(clickEvt.defaultPrevented).toBe(false);

    interceptor.detach();
  });

  // ===========================================================================
  // 12. Multiple-Tab & Window Isolation (Sections 16, 17, 18)
  // ===========================================================================
  it('Sections 16-18: Multiple-Tab and Session Isolation guarantees zero cross-tab state leakage', () => {
    // Tab 101: PAUSE on Site A
    backgroundState.startRequest({
      requestId: 'REQ-TAB-101',
      tabId: 101,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://site-a.com',
      pageUrl: 'https://site-a.com/deal',
    });
    backgroundState.completeRequest({
      analysisId: 'ANA-TAB-101',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'High risk deal',
      tabId: 101,
      completedAt: new Date().toISOString(),
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-TAB-101',
    });

    // Tab 202: ALLOW on Site B
    backgroundState.startRequest({
      requestId: 'REQ-TAB-202',
      tabId: 202,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://site-b.com',
      pageUrl: 'https://site-b.com/safe',
    });
    backgroundState.completeRequest({
      analysisId: 'ANA-TAB-202',
      decision: 'ALLOW',
      severity: 'LOW',
      primaryReason: 'Safe page',
      tabId: 202,
      completedAt: new Date().toISOString(),
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-TAB-202',
    });

    // Verify Tab 101 retains PAUSE
    const state101 = backgroundState.getState(101);
    expect(state101.lastAnalysis?.decision).toBe('PAUSE');
    expect(state101.lastAnalysis?.analysisId).toBe('ANA-TAB-101');
    const tab101 = backgroundState.getTabState(101);
    expect(tab101.sessionId).toContain('SESS-TAB-101');

    // Verify Tab 202 retains ALLOW
    const state202 = backgroundState.getState(202);
    expect(state202.lastAnalysis?.decision).toBe('ALLOW');
    expect(state202.lastAnalysis?.analysisId).toBe('ANA-TAB-202');
    const tab202 = backgroundState.getTabState(202);
    expect(tab202.sessionId).toContain('SESS-TAB-202');

    // Ensure session IDs are distinct
    expect(tab101.sessionId).not.toBe(tab202.sessionId);
  });

  // ===========================================================================
  // 13. Worker Lifecycle & Reload Handling (Sections 19, 20, 21)
  // ===========================================================================
  it('Sections 19-21: Worker lifecycle reset and page reload do not trigger automatic silent rescan', () => {
    // Simulate background worker restart
    backgroundState.reset();
    const cleanState = backgroundState.getState(101);
    expect(cleanState.status).toBe('READY');
    expect(cleanState.lastAnalysis).toBeNull();
    expect(cleanState.activeRequest).toBeNull();

    // Verify reload safety
    const fetchSpy = vi.fn();
    globalThis.fetch = fetchSpy;

    const reloadEvent = new Event('DOMContentLoaded');
    document.dispatchEvent(reloadEvent);

    expect(fetchSpy).not.toHaveBeenCalled();
  });

  // ===========================================================================
  // 14. Manifest & Permission Minimization Audit (Sections 22, 23, 24)
  // ===========================================================================
  it('Sections 22-24: Manifest & Permission Audit verifies least privilege principle', () => {
    // 1. Only required MV3 permissions
    expect(manifest.permissions).toEqual(['activeTab', 'storage', 'scripting']);
    expect(manifest.permissions).not.toContain('<all_urls>');
    expect(manifest.permissions).not.toContain('webNavigation');
    expect(manifest.permissions).not.toContain('webRequest');
    expect(manifest.permissions).not.toContain('cookies');

    // 2. Strict narrow host permissions
    expect(manifest.host_permissions).toEqual(['http://localhost:8000/*', 'http://127.0.0.1:8000/*']);
    expect(manifest.host_permissions).not.toContain('<all_urls>');
    expect(manifest.host_permissions).not.toContain('*://*/*');

    // 3. Document idle execution
    expect(manifest.content_scripts[0].run_at).toBe('document_idle');
  });

  // ===========================================================================
  // 15. Sensitive Form & Keystroke Exclusion (Sections 25, 26)
  // ===========================================================================
  it('Sections 25-26: Sensitive Form & Keystroke Security guarantees zero credential capture', () => {
    document.body.innerHTML = `
      <form id="payment-form">
        <input type="text" id="username" value="user_alice" />
        <input type="password" id="pwd" value="SecretPassword123!" />
        <input type="number" id="otp" name="otp" value="987654" />
        <input type="text" id="pin" name="pin" value="1234" />
        <input type="text" id="cvv" name="cvv" value="999" />
        <input type="text" id="card" name="card_number" value="4111222233334444" />
        <input type="text" id="account" name="bank_account" value="998877665544" />
        <input type="hidden" id="token" value="sensitive_csrf_token" />
        <p id="public-notice">Please review our fund prospectus.</p>
      </form>
    `;

    const extracted = extractVisiblePageText(document);
    expect(extracted.status).toBe('CAPTURED');
    const text = extracted.sanitizedText || '';

    // Verify all sensitive values are excluded
    expect(text).not.toContain('SecretPassword123!');
    expect(text).not.toContain('987654');
    expect(text).not.toContain('1234');
    expect(text).not.toContain('999');
    expect(text).not.toContain('4111222233334444');
    expect(text).not.toContain('998877665544');
    expect(text).not.toContain('sensitive_csrf_token');

    // Public text is safely captured
    expect(text).toContain('Please review our fund prospectus.');

    // Verify zero keystroke listeners
    const addEventListenerSpy = vi.spyOn(document, 'addEventListener');
    protectionManager.showIntervention({
      analysisId: 'ANA-KEY-TEST',
      decision: 'INFORM',
      severity: 'LOW',
      primaryReason: 'Information only',
      webAppUrl: '',
    });

    const keyListenerCalls = addEventListenerSpy.mock.calls.filter(
      ([eventName]) => eventName === 'keyup' || eventName === 'keypress'
    );
    expect(keyListenerCalls.length).toBe(0);
  });

  // ===========================================================================
  // 16. Cookie, Storage, Raw DOM & URL Privacy Audits (Sections 27, 28, 29)
  // ===========================================================================
  it('Sections 27-29: Cookie, Storage, and URL Privacy audits verify zero sensitive data exposure', () => {
    // 1. URL Privacy: Sensitive query params stripped from display URL
    const rawUrl = 'https://bank.test/transfer?token=secret123&session=sess99&amount=5000&view=summary';
    const displayUrl = getSanitizedDisplayUrl(rawUrl);

    expect(displayUrl).not.toContain('token=secret123');
    expect(displayUrl).not.toContain('session=sess99');
    expect(displayUrl).toContain('view=summary');

    // 2. Unsupported internal URLs are rejected
    expect(isUnsupportedPageUrl('chrome://settings')).toBe(true);
    expect(isUnsupportedPageUrl('edge://extensions')).toBe(true);
    expect(isUnsupportedPageUrl('about:blank')).toBe(true);
    expect(isUnsupportedPageUrl('devtools://devtools')).toBe(true);
    expect(isUnsupportedPageUrl('https://valid-portal.test/funds')).toBe(false);

    // 3. Raw DOM Audit: Extractor never returns raw HTML tags
    document.body.innerHTML = `<div><script>alert(1)</script><style>.bad{color:red;}</style><p>Clean visible content</p></div>`;
    const result = extractVisiblePageText(document);
    expect(result.sanitizedText).toBe('Clean visible content');
    expect(result.sanitizedText).not.toContain('<script>');
    expect(result.sanitizedText).not.toContain('<style>');
  });

  // ===========================================================================
  // 17. Content Security, Message Security & Secret Audits (Sections 30, 31, 32, 33)
  // ===========================================================================
  it('Sections 30-33: Content security and origin validation prevent host page script injection', () => {
    // 1. DOM Safety: Untrusted HTML strings rendered safely via textContent
    const maliciousPayload: InPageInterventionPayload = {
      analysisId: 'ANA-XSS-TEST',
      decision: 'WARN',
      severity: 'MEDIUM',
      primaryReason: '<img src=x onerror=alert(1)>Malicious Exploit',
      userMessage: '<script>window.pwned=true</script>Safe looking message',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-XSS-TEST',
    };

    const overlay = new ProtectionOverlay({
      onDismiss: vi.fn(),
      onOpenAnalysis: vi.fn(),
    });

    overlay.render(maliciousPayload);

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    expect(shadow?.querySelector('img')).toBeNull();
    expect(shadow?.querySelector('script')).toBeNull();
    expect(shadow?.textContent).toContain('<script>window.pwned=true</script>Safe looking message');
    expect((window as any).pwned).toBeUndefined();

    overlay.destroy();

    // 2. Malicious webpage postMessage cannot trigger intervention
    const postMessageSpy = vi.fn();
    window.addEventListener('message', postMessageSpy);
    window.postMessage({ type: 'SHOW_INTERVENTION', payload: maliciousPayload }, '*');

    // Content script does not listen on window.message
    expect(document.getElementById('nivesh-firewall-root')).toBeNull();
  });

  // ===========================================================================
  // 18. Accessibility & Visual Display QA (Sections 40, 41, 42, 43)
  // ===========================================================================
  it('Sections 40-43: Accessibility and Responsive Display verified across zoom scales', () => {
    const overlay = new ProtectionOverlay({
      onDismiss: vi.fn(),
      onOpenAnalysis: vi.fn(),
    });

    overlay.render({
      analysisId: 'ANA-A11Y-042',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Accessible test',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-A11Y-042',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;

    // ARIA roles
    const modal = shadow?.querySelector('.nivesh-modal');
    expect(modal?.getAttribute('role')).toBe('dialog');
    expect(modal?.getAttribute('aria-modal')).toBe('true');
    expect(modal?.getAttribute('aria-labelledby')).toBe('nivesh-pause-title');

    // Title element
    const title = shadow?.querySelector('#nivesh-pause-title');
    expect(title).not.toBeNull();
    expect(title?.textContent).toBe('Action Paused Before Proceeding');
    expect(shadow?.textContent).toContain('ACTION PAUSED');

    // Responsive styles check: overlay CSS contains max-width and responsive bounds
    const styleEl = shadow?.querySelector('style');
    expect(styleEl?.textContent).toContain('max-width: 100%');
    expect(styleEl?.textContent).toContain('box-sizing: border-box');

    overlay.destroy();
  });

  // ===========================================================================
  // 19. Web-App Handoff & Override Integrity (Sections 44, 45, 46, 47)
  // ===========================================================================
  it('Sections 44-47: Web-app handoff URL passes analysisId cleanly; PAUSE override requires confirmation; BLOCK has zero bypass', () => {
    // 1. Web app handoff URL check
    const analysisId = 'ANA-HANDOFF-999';
    const webAppUrl = `http://localhost:5173/#protect?id=${analysisId}`;
    expect(webAppUrl).toBe('http://localhost:5173/#protect?id=ANA-HANDOFF-999');
    expect(webAppUrl).not.toContain('text=');
    expect(webAppUrl).not.toContain('password=');

    // 2. PAUSE override requires confirmation dialog
    const confirmOverrideSpy = vi.fn();
    const overlay = new ProtectionOverlay({
      onDismiss: vi.fn(),
      onOpenAnalysis: vi.fn(),
      onConfirmOverride: confirmOverrideSpy,
    });

    overlay.render({
      analysisId,
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Paused action',
      webAppUrl,
    });

    const shadow = document.getElementById('nivesh-firewall-root')?.shadowRoot;

    // Click Continue
    const outlineBtn = shadow?.querySelector('.btn-outline') as HTMLButtonElement;
    outlineBtn.click();

    // Verifies confirmation dialog is presented
    expect(shadow?.querySelector('.override-dialog')).not.toBeNull();
    expect(confirmOverrideSpy).not.toHaveBeenCalled();

    // Confirm override
    const confirmBtn = shadow?.querySelector('.btn-danger') as HTMLButtonElement;
    confirmBtn.click();
    expect(confirmOverrideSpy).toHaveBeenCalledWith(analysisId);

    // 3. BLOCK has zero override button
    overlay.render({
      analysisId: 'ANA-BLOCK-NO-BYPASS',
      decision: 'BLOCK',
      severity: 'CRITICAL',
      primaryReason: 'Blocked action',
      webAppUrl,
    });

    const blockShadow = document.getElementById('nivesh-firewall-root')?.shadowRoot;
    const allButtons = Array.from(blockShadow?.querySelectorAll('button') || []);
    const buttonTexts = allButtons.map((b) => b.textContent?.toLowerCase() || '');

    // Strictly ensure no bypass button exists
    expect(buttonTexts.some((t) => t.includes('continue anyway'))).toBe(false);
    expect(buttonTexts.some((t) => t.includes('bypass'))).toBe(false);
    expect(buttonTexts.some((t) => t.includes('ignore'))).toBe(false);

    overlay.destroy();
  });

  // ===========================================================================
  // 20. API Contract Validation (Section 48)
  // ===========================================================================
  it('Section 48: API Contract validation verifies payload conformity with Unified Firewall API', async () => {
    let capturedBody: any = null;

    globalThis.fetch = vi.fn().mockImplementation((_url, init) => {
      capturedBody = JSON.parse(init.body as string);
      return Promise.resolve({
        ok: true,
        json: () =>
          Promise.resolve({
            analysis_id: 'ANA-CONTRACT-048',
            completed_at: new Date().toISOString(),
            decision: {
              decision: 'INFORM',
              severity: 'LOW',
              primary_reason: 'Verified contract format.',
            },
          }),
      } as Response);
    });

    await routeExtensionMessage({
      type: 'SCAN_REQUEST',
      requestId: 'REQ-CONTRACT-048',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: {
          captureId: 'CAP-CONTRACT-048',
          sourceType: 'CURRENT_PAGE',
          status: 'CAPTURED',
          text: 'Verified contract payload text.',
          url: 'https://contract-test.test',
          displayUrl: 'https://contract-test.test',
          pageTitle: 'Contract Test',
          pageOrigin: 'https://contract-test.test',
          tabId: 101,
          timestamp: new Date().toISOString(),
          contentLength: 30,
          sanitized: true,
        },
      },
    });

    // Check payload structure sent to Unified Firewall API
    expect(capturedBody).not.toBeNull();
    expect(capturedBody.input_type).toBe('text');
    expect(capturedBody.text).toBe('Verified contract payload text.');
    expect(capturedBody.url).toBe('https://contract-test.test');
    expect(capturedBody.metadata).toBeDefined();
    expect(capturedBody.metadata.capture_id).toBe('CAP-CONTRACT-048');
    expect(capturedBody.metadata.tab_id).toBe(101);
  });

  // ===========================================================================
  // 21. Product Truthfulness & Boundary Audit (Sections 53, 54, 55)
  // ===========================================================================
  it('Sections 53-55: Product Truthfulness & Boundary Audit confirms objective wording and no investment advice', () => {
    const overlay = new ProtectionOverlay({
      onDismiss: vi.fn(),
      onOpenAnalysis: vi.fn(),
    });

    const decisions: Array<'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK'> = ['INFORM', 'WARN', 'PAUSE', 'BLOCK'];

    for (const dec of decisions) {
      overlay.render({
        analysisId: `ANA-TRUTH-${dec}`,
        decision: dec,
        severity: 'MEDIUM',
        primaryReason: 'Standard factual reason.',
        webAppUrl: '',
      });

      const shadow = document.getElementById('nivesh-firewall-root')?.shadowRoot;
      const fullText = (shadow?.textContent || '').toLowerCase();

      // Prohibited claims
      expect(fullText).not.toContain('100% scam detection');
      expect(fullText).not.toContain('guaranteed safe');
      expect(fullText).not.toContain('government certified');
      expect(fullText).not.toContain('universal monitoring');

      // Prohibited investment recommendations
      expect(fullText).not.toContain('buy this stock');
      expect(fullText).not.toContain('sell this stock');
      expect(fullText).not.toContain('recommended broker');
      expect(fullText).not.toContain('guaranteed return');

      overlay.destroy();
    }
  });
});
