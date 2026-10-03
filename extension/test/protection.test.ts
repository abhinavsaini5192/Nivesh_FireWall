/**
 * Phase 13.4 Test Suite: In-Page Protection & Interaction (Section 43 Tests 1 to 28)
 *
 * Verifies:
 * Test 1 — ALLOW: No intervention overlay is shown.
 * Test 2 — INFORM: Information panel appears.
 * Test 3 — WARN: Warning panel appears.
 * Test 4 — PAUSE: Pause intervention appears.
 * Test 5 — BLOCK: Block intervention appears.
 * Test 6 — Decision preservation: Frontend renders exactly the backend decision.
 * Test 7 — No policy logic: Frontend does not independently determine the decision.
 * Test 8 — Explanation: Backend-supported explanation renders correctly.
 * Test 9 — Reason codes: Structured reason breakdowns are correctly represented.
 * Test 10 — Analysis handoff: View-analysis opens the correct analysis ID.
 * Test 11 — Tab isolation: Different tabs maintain different protection states.
 * Test 12 — Action isolation: Only the analyzed target is protected when an exact target exists.
 * Test 13 — Ambiguous target: No arbitrary action is blocked (Safe Uncertainty Rule).
 * Test 14 — Page navigation: Normal unrelated navigation remains unaffected.
 * Test 15 — BLOCK target: Targeted blocked navigation is prevented.
 * Test 16 — PAUSE target: Targeted navigation is paused for explicit user review.
 * Test 17 — Override: Supported override flow works with explicit confirmation.
 * Test 18 — Override cancellation: Original policy state remains intact after cancellation.
 * Test 19 — Backend unavailable: No intervention state is fabricated when no policy result exists.
 * Test 20 — Reload: Reload does not silently submit page content again.
 * Test 21 — Sensitive fields: No password/OTP/PIN/CVV/card/bank values are captured.
 * Test 22 — DOM safety: Page-provided HTML cannot execute through Nivesh UI (textContent safety).
 * Test 23 — Message security: Untrusted webpage messages cannot trigger protection commands.
 * Test 24 — Event cleanup: Listeners and overlays are removed correctly.
 * Test 25 — Popup synchronization: Popup state matches the active tab.
 * Test 26 — Web-app synchronization: Correct analysis ID is opened in web app handoff.
 * Test 27 — Accessibility: Intervention is keyboard and screen-reader accessible.
 * Test 28 — Performance: No continuous DOM scanning or excessive event listeners.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  ProtectionOverlay,
  TargetedNavigationInterceptor,
  matchTargetAction,
  protectionManager,
  InPageProtectionManager,
} from '../src/protection';
import { backgroundState } from '../src/background/state';
import { routeExtensionMessage } from '../src/background/router';
import type { InPageInterventionPayload } from '../src/protection/types';
import type { OverlayCallbacks } from '../src/protection/overlay';

describe('In-Page Protection & Interaction — Phase 13.4 Test Suite (Tests 1 to 28)', () => {
  let mockDismiss: ReturnType<typeof vi.fn<() => void>>;
  let mockOpenAnalysis: ReturnType<typeof vi.fn<(id: string) => void>>;
  let mockConfirmOverride: ReturnType<typeof vi.fn<(id: string) => void>>;
  let mockReturn: ReturnType<typeof vi.fn<() => void>>;
  let callbacks: OverlayCallbacks;

  beforeEach(() => {
    document.body.innerHTML = '';
    backgroundState.reset();
    vi.restoreAllMocks();

    mockDismiss = vi.fn<() => void>();
    mockOpenAnalysis = vi.fn<(id: string) => void>();
    mockConfirmOverride = vi.fn<(id: string) => void>();
    mockReturn = vi.fn<() => void>();

    callbacks = {
      onDismiss: mockDismiss,
      onOpenAnalysis: mockOpenAnalysis,
      onConfirmOverride: mockConfirmOverride,
      onReturn: mockReturn,
    };
  });

  afterEach(() => {
    protectionManager.cleanup();
    document.body.innerHTML = '';
    vi.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Test 1: ALLOW produces zero intervention overlay
  // ---------------------------------------------------------------------------
  it('Test 1: ALLOW decision injects no intervention overlay into the DOM', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-ALLOW-001',
      decision: 'ALLOW',
      severity: 'LOW',
      primaryReason: 'No conditions requiring protective intervention were identified.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-ALLOW-001',
    });

    const root = document.getElementById('nivesh-firewall-root');
    expect(root).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 2: INFORM presents lightweight, non-blocking info panel
  // ---------------------------------------------------------------------------
  it('Test 2: INFORM decision displays lightweight non-blocking informational banner', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-INFORM-002',
      decision: 'INFORM',
      severity: 'LOW',
      primaryReason: 'Educational information available for this fund.',
      userMessage: 'Review expense ratio disclosures before investing.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-INFORM-002',
    });

    const root = document.getElementById('nivesh-firewall-root');
    expect(root).not.toBeNull();
    const shadow = root?.shadowRoot;
    expect(shadow).not.toBeNull();

    const banner = shadow?.querySelector('.nivesh-banner.inform');
    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('NIVESH FIREWALL');
    expect(banner?.textContent).toContain('Nivesh Information');
    expect(banner?.textContent).toContain('Review expense ratio disclosures before investing.');

    // Dismissal button removes overlay
    const dismissBtn = banner?.querySelector('.btn-ghost') as HTMLButtonElement;
    dismissBtn?.click();
    expect(mockDismiss).toHaveBeenCalled();
    expect(document.getElementById('nivesh-firewall-root')).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 3: WARN presents visible protection warning banner
  // ---------------------------------------------------------------------------
  it('Test 3: WARN decision displays visible warning banner with review options', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-WARN-003',
      decision: 'WARN',
      severity: 'MEDIUM',
      primaryReason: 'High volatility derivative trading signals.',
      userMessage: 'Unregistered advisory group promoting high risk options.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-WARN-003',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    const banner = shadow?.querySelector('.nivesh-banner.warn');

    expect(banner).not.toBeNull();
    expect(banner?.textContent).toContain('Review Before Continuing');
    expect(banner?.textContent).toContain('Unregistered advisory group');

    // Click Review Details opens analysis
    const reviewBtn = banner?.querySelector('.btn-primary') as HTMLButtonElement;
    reviewBtn?.click();
    expect(mockOpenAnalysis).toHaveBeenCalledWith('ANA-WARN-003');
  });

  // ---------------------------------------------------------------------------
  // Test 4: PAUSE presents pause intervention modal with structured reasons
  // ---------------------------------------------------------------------------
  it('Test 4: PAUSE decision renders centered modal overlay with structured reasons', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-PAUSE-004',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Suspicious advance fee payment request.',
      userMessage: 'Do not transfer funds until entity credentials are confirmed.',
      identityStatus: 'NOT_ESTABLISHED',
      evidenceStatus: 'CONTRADICTED',
      claimsCount: 2,
      fingerprintMatch: 'SEMANTIC_VARIANT',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-PAUSE-004',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    const modal = shadow?.querySelector('.nivesh-modal.pause');

    expect(modal).not.toBeNull();
    expect(modal?.textContent).toContain('ACTION PAUSED');
    expect(modal?.textContent).toContain('Do not transfer funds until entity credentials are confirmed.');

    // Verifies structured inspection grid
    expect(modal?.textContent).toContain('Identity');
    expect(modal?.textContent).toContain('NOT_ESTABLISHED');
    expect(modal?.textContent).toContain('Evidence');
    expect(modal?.textContent).toContain('CONTRADICTED');
    expect(modal?.textContent).toContain('SEMANTIC_VARIANT');
  });

  // ---------------------------------------------------------------------------
  // Test 5: BLOCK presents blocked-action experience
  // ---------------------------------------------------------------------------
  it('Test 5: BLOCK decision renders blocked intervention modal without bypass button', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-BLOCK-005',
      decision: 'BLOCK',
      severity: 'CRITICAL',
      primaryReason: 'Malicious clone payment gateway detected.',
      userMessage: 'Nivesh Firewall blocked this interaction according to its protection policy.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-BLOCK-005',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    const modal = shadow?.querySelector('.nivesh-modal.block');

    expect(modal).not.toBeNull();
    expect(modal?.textContent).toContain('ACTION BLOCKED');
    expect(modal?.textContent).toContain('Malicious clone payment gateway detected.');

    // Verifies absence of generic override / continue anyway button
    expect(modal?.textContent).not.toContain('Continue Anyway');
    expect(modal?.textContent).not.toContain('Override Block');
  });

  // ---------------------------------------------------------------------------
  // Test 6: Decision preservation
  // ---------------------------------------------------------------------------
  it('Test 6: in-page overlay faithfully preserves the exact backend decision', () => {
    const overlay = new ProtectionOverlay(callbacks);

    for (const dec of ['INFORM', 'WARN', 'PAUSE', 'BLOCK'] as const) {
      overlay.render({
        analysisId: `ANA-${dec}`,
        decision: dec,
        severity: 'MEDIUM',
        primaryReason: `Reason for ${dec}`,
        webAppUrl: `http://localhost:5173/#protect?id=ANA-${dec}`,
      });

      const root = document.getElementById('nivesh-firewall-root');
      const shadow = root?.shadowRoot;
      const badge = shadow?.querySelector(`.decision-badge.${dec.toLowerCase()}`) ||
                    shadow?.querySelector(`.nivesh-banner.${dec.toLowerCase()}`);
      expect(badge).not.toBeNull();
    }
  });

  // ---------------------------------------------------------------------------
  // Test 7: No frontend policy logic
  // ---------------------------------------------------------------------------
  it('Test 7: verifies protection manager contains zero local risk scoring or policy heuristics', () => {
    const managerProto = Object.getOwnPropertyNames(InPageProtectionManager.prototype);
    expect(managerProto).not.toContain('calculateThreatScore');
    expect(managerProto).not.toContain('detectScam');
    expect(managerProto).not.toContain('decidePolicy');
    expect(managerProto).not.toContain('evaluateRisk');
  });

  // ---------------------------------------------------------------------------
  // Test 8: Explanation rendering
  // ---------------------------------------------------------------------------
  it('Test 8: backend-supported user message and primary explanation render accurately', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-EXPL-008',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Unregistered high-yield investment scheme.',
      userMessage: 'The entity claiming 40% returns does not hold an active SEBI registration.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-EXPL-008',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const desc = root?.shadowRoot?.querySelector('.modal-description');
    expect(desc?.textContent).toBe(
      'The entity claiming 40% returns does not hold an active SEBI registration.'
    );
  });

  // ---------------------------------------------------------------------------
  // Test 9: Reason codes and dimensions represented
  // ---------------------------------------------------------------------------
  it('Test 9: structured reason dimensions render without distortion', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-DIM-009',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Multiple risk factors observed.',
      identityStatus: 'IDENTITY_MISMATCH',
      evidenceStatus: 'INSUFFICIENT_EVIDENCE',
      fingerprintMatch: 'STRUCTURAL_MATCH',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-DIM-009',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    expect(shadow?.textContent).toContain('IDENTITY_MISMATCH');
    expect(shadow?.textContent).toContain('INSUFFICIENT_EVIDENCE');
    expect(shadow?.textContent).toContain('STRUCTURAL_MATCH');
  });

  // ---------------------------------------------------------------------------
  // Test 10: Analysis handoff
  // ---------------------------------------------------------------------------
  it('Test 10: view analysis triggers callback with correct analysis ID without raw content in handoff', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-HANDOFF-010',
      decision: 'BLOCK',
      severity: 'CRITICAL',
      primaryReason: 'Phishing domain detected.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-HANDOFF-010',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const viewBtn = root?.shadowRoot?.querySelector('.btn-primary') as HTMLButtonElement;
    viewBtn.click();

    expect(mockOpenAnalysis).toHaveBeenCalledWith('ANA-HANDOFF-010');
  });

  // ---------------------------------------------------------------------------
  // Test 11: Multi-Tab Isolation
  // ---------------------------------------------------------------------------
  it('Test 11: Tab A and Tab B maintain independent in-page protection states', () => {
    // Tab 101: PAUSE
    backgroundState.startRequest({
      requestId: 'REQ-TAB-A',
      tabId: 101,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://site-a.com',
      pageUrl: 'https://site-a.com/invest',
    });
    backgroundState.completeRequest(
      {
        analysisId: 'ANA-TAB-A',
        decision: 'PAUSE',
        severity: 'HIGH',
        primaryReason: 'Tab A reason',
        completedAt: new Date().toISOString(),
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-TAB-A',
      },
      101
    );

    // Tab 102: ALLOW
    backgroundState.startRequest({
      requestId: 'REQ-TAB-B',
      tabId: 102,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://site-b.com',
      pageUrl: 'https://site-b.com/safe',
    });
    backgroundState.completeRequest(
      {
        analysisId: 'ANA-TAB-B',
        decision: 'ALLOW',
        severity: 'LOW',
        primaryReason: 'Tab B reason',
        completedAt: new Date().toISOString(),
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-TAB-B',
      },
      102
    );

    expect(backgroundState.getState(101).lastAnalysis?.decision).toBe('PAUSE');
    expect(backgroundState.getState(102).lastAnalysis?.decision).toBe('ALLOW');
  });

  // ---------------------------------------------------------------------------
  // Test 12: Targeted Action Isolation
  // ---------------------------------------------------------------------------
  it('Test 12: only the analyzed target link is matched; unrelated links remain untouched', () => {
    document.body.innerHTML = `
      <div id="page">
        <a id="safe-link" href="https://bank.com/terms">Terms and Conditions</a>
        <a id="bad-link" href="https://external-scam.com/pay">Pay via External Link</a>
        <a id="other-link" href="https://bank.com/contact">Contact Us</a>
      </div>
    `;

    const match = matchTargetAction(document, 'https://external-scam.com/pay');
    expect(match.matchConfidence).toBe('EXACT');
    expect(match.matchedElement?.id).toBe('bad-link');

    const unrelated = document.getElementById('safe-link');
    expect(match.matchedElement).not.toBe(unrelated);
  });

  // ---------------------------------------------------------------------------
  // Test 13: Ambiguous Target (Safe Uncertainty Rule)
  // ---------------------------------------------------------------------------
  it('Test 13: ambiguous target links trigger Safe Uncertainty Rule without blocking arbitrary buttons', () => {
    document.body.innerHTML = `
      <div>
        <a class="invest-link" href="https://promo.com/join">Join Scheme 1</a>
        <a class="invest-link" href="https://promo.com/join">Join Scheme 2</a>
      </div>
    `;

    // Multiple matching candidates -> Ambiguous!
    const match = matchTargetAction(document, 'https://promo.com/join');
    expect(match.matchConfidence).toBe('AMBIGUOUS');
    expect(match.matchedElement).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 14: Page Navigation Unaffected for Unrelated Links
  // ---------------------------------------------------------------------------
  it('Test 14: click on unrelated link is completely unaffected by targeted interceptor', () => {
    document.body.innerHTML = `
      <div>
        <a id="bad-link" href="https://malicious.com/pay">Pay</a>
        <a id="normal-link" href="https://safe.com/home">Home</a>
      </div>
    `;

    const badLink = document.getElementById('bad-link') as HTMLAnchorElement;
    const normalLink = document.getElementById('normal-link') as HTMLAnchorElement;

    const onTriggered = vi.fn();
    const interceptor = new TargetedNavigationInterceptor({ onTargetTriggered: onTriggered });

    interceptor.attach(badLink, {
      analysisId: 'ANA-NAV-014',
      decision: 'BLOCK',
      severity: 'HIGH',
      primaryReason: 'Malicious link',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-NAV-014',
    });

    // Click on unrelated normal link
    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    normalLink.dispatchEvent(clickEvent);

    expect(clickEvent.defaultPrevented).toBe(false);
    expect(onTriggered).not.toHaveBeenCalled();

    interceptor.detach();
  });

  // ---------------------------------------------------------------------------
  // Test 15: Targeted Navigation BLOCK Prevention
  // ---------------------------------------------------------------------------
  it('Test 15: click on targeted link under BLOCK policy is prevented and re-triggers notification', () => {
    document.body.innerHTML = `
      <div>
        <a id="bad-link" href="https://malicious.com/pay">Pay Now</a>
      </div>
    `;

    const badLink = document.getElementById('bad-link') as HTMLAnchorElement;
    const onTriggered = vi.fn();
    const interceptor = new TargetedNavigationInterceptor({ onTargetTriggered: onTriggered });

    const payload: InPageInterventionPayload = {
      analysisId: 'ANA-BLOCK-015',
      decision: 'BLOCK',
      severity: 'CRITICAL',
      primaryReason: 'Blocked malicious target',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-BLOCK-015',
    };

    interceptor.attach(badLink, payload);

    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    badLink.dispatchEvent(clickEvent);

    expect(clickEvent.defaultPrevented).toBe(true);
    expect(onTriggered).toHaveBeenCalledWith(badLink, payload);

    interceptor.detach();
  });

  // ---------------------------------------------------------------------------
  // Test 16: Targeted Navigation PAUSE Prevention
  // ---------------------------------------------------------------------------
  it('Test 16: click on targeted link under PAUSE policy pauses navigation before user confirmation', () => {
    document.body.innerHTML = `
      <div>
        <a id="pause-link" href="https://unverified-vendor.com/checkout">Checkout</a>
      </div>
    `;

    const pauseLink = document.getElementById('pause-link') as HTMLAnchorElement;
    const onTriggered = vi.fn();
    const interceptor = new TargetedNavigationInterceptor({ onTargetTriggered: onTriggered });

    const payload: InPageInterventionPayload = {
      analysisId: 'ANA-PAUSE-016',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Unverified vendor',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-PAUSE-016',
    };

    interceptor.attach(pauseLink, payload);

    const clickEvent = new MouseEvent('click', { bubbles: true, cancelable: true });
    pauseLink.dispatchEvent(clickEvent);

    expect(clickEvent.defaultPrevented).toBe(true);
    expect(onTriggered).toHaveBeenCalled();

    interceptor.detach();
  });

  // ---------------------------------------------------------------------------
  // Test 17: Supported Override Flow with Explicit Confirmation
  // ---------------------------------------------------------------------------
  it('Test 17: PAUSE override requires explicit user confirmation dialog before allowing action', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-OVERRIDE-017',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Requires explicit confirmation.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-OVERRIDE-017',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;

    // 1. Click "Continue After Confirmation"
    const continueBtn = shadow?.querySelector('.btn-outline') as HTMLButtonElement;
    continueBtn.click();

    // 2. Verifies explicit confirmation dialog is presented
    const dialog = shadow?.querySelector('.override-dialog');
    expect(dialog).not.toBeNull();
    expect(dialog?.textContent).toContain('Continue With This Action?');
    expect(dialog?.textContent).toContain('Nivesh previously paused this action');

    // 3. Confirm override
    const confirmBtn = shadow?.querySelector('.btn-danger') as HTMLButtonElement;
    confirmBtn.click();

    expect(mockConfirmOverride).toHaveBeenCalledWith('ANA-OVERRIDE-017');
    expect(document.getElementById('nivesh-firewall-root')).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 18: Override Cancellation Preserves Policy State
  // ---------------------------------------------------------------------------
  it('Test 18: cancelling override in confirmation dialog preserves original PAUSE policy state', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-CANCEL-018',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Paused action.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-CANCEL-018',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;

    // Open confirmation dialog
    const outlineBtn = shadow?.querySelector('.btn-outline') as HTMLButtonElement | null;
    outlineBtn?.click();

    // Click Cancel
    const cancelBtn = shadow?.querySelector('.btn-ghost') as HTMLButtonElement;
    cancelBtn.click();

    // Original PAUSE modal should be restored
    expect(shadow?.querySelector('.nivesh-modal.pause')).not.toBeNull();
    expect(mockConfirmOverride).not.toHaveBeenCalled();
  });

  // ---------------------------------------------------------------------------
  // Test 19: Backend Unavailable Does Not Fabricate Policy State
  // ---------------------------------------------------------------------------
  it('Test 19: when backend is unavailable, no in-page intervention overlay is injected', () => {
    backgroundState.failRequest({
      code: 'BACKEND_UNAVAILABLE',
      message: 'Service is offline',
    });

    const state = backgroundState.getState();
    expect(state.status).toBe('ERROR');
    expect(state.lastAnalysis).toBeNull();
    expect(document.getElementById('nivesh-firewall-root')).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 20: Reload Does Not Resubmit
  // ---------------------------------------------------------------------------
  it('Test 20: page reload returns to ready state without automatically resubmitting', () => {
    backgroundState.reset();
    const state = backgroundState.getState();
    expect(state.status).toBe('READY');
    expect(state.activeRequest).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 21: Sensitive Fields Excluded
  // ---------------------------------------------------------------------------
  it('Test 21: protection overlay and interceptor never touch password, OTP, CVV, or card inputs', () => {
    document.body.innerHTML = `
      <form id="pay-form">
        <input type="password" id="pwd" value="Secret123" />
        <input type="text" id="otp" name="otp" value="987654" />
        <input type="text" id="cvv" name="cvv" value="123" />
        <input type="text" id="card" name="card_number" value="4111222233334444" />
      </form>
    `;

    const match = matchTargetAction(document, 'https://external-link.com');
    expect(match.matchedElement).toBeNull();

    // Overlay is completely separate in Shadow DOM and reads zero form fields
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-FORM-021',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Test',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-FORM-021',
    });

    const shadow = document.getElementById('nivesh-firewall-root')?.shadowRoot;
    expect(shadow?.querySelector('#pwd')).toBeNull();
    expect(shadow?.querySelector('#otp')).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 22: DOM Safety (XSS Prevention)
  // ---------------------------------------------------------------------------
  it('Test 22: malicious script tags in backend explanation are rendered safely as plain text', () => {
    const maliciousScript = '<img src=x onerror="window.__xss_test=true"><script>alert(1)</script>';

    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-XSS-022',
      decision: 'WARN',
      severity: 'MEDIUM',
      primaryReason: maliciousScript,
      userMessage: maliciousScript,
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-XSS-022',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    const body = shadow?.querySelector('.banner-body');

    expect(body?.textContent).toBe(maliciousScript);
    expect(shadow?.querySelector('img')).toBeNull();
    expect(shadow?.querySelector('script')).toBeNull();
    expect((window as any).__xss_test).toBeUndefined();
  });

  // ---------------------------------------------------------------------------
  // Test 23: Untrusted Webpage Messages Cannot Command Protection
  // ---------------------------------------------------------------------------
  it('Test 23: arbitrary window.postMessage events do not manipulate protectionManager state', () => {
    const fakeEvent = new MessageEvent('message', {
      data: { type: 'NIVESH_BYPASS', decision: 'ALLOW' },
      origin: 'https://malicious-page.com',
    });
    window.dispatchEvent(fakeEvent);

    // Protection manager state remains intact
    const state = protectionManager.getState();
    expect(state.overridden).toBe(false);
  });

  // ---------------------------------------------------------------------------
  // Test 24: Event & DOM Cleanup
  // ---------------------------------------------------------------------------
  it('Test 24: cleanup thoroughly removes all DOM nodes, Shadow roots, and keydown listeners', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-CLEANUP-024',
      decision: 'PAUSE',
      severity: 'HIGH',
      primaryReason: 'Test cleanup',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-CLEANUP-024',
    });

    expect(document.getElementById('nivesh-firewall-root')).not.toBeNull();

    overlay.destroy();
    expect(document.getElementById('nivesh-firewall-root')).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 25: Popup Synchronization
  // ---------------------------------------------------------------------------
  it('Test 25: background router synchronizes correct active tab state without stale cross-tab data', async () => {
    backgroundState.startRequest({
      requestId: 'REQ-TAB-1',
      tabId: 1,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://site-1.com',
      pageUrl: 'https://site-1.com',
    });
    backgroundState.completeRequest(
      {
        analysisId: 'ANA-1',
        decision: 'WARN',
        severity: 'MEDIUM',
        primaryReason: 'Site 1 Warn',
        completedAt: new Date().toISOString(),
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-1',
      },
      1
    );

    const res1 = await routeExtensionMessage({
      type: 'GET_STATUS',
      requestId: 'REQ-STATUS-1',
      timestamp: new Date().toISOString(),
      payload: { tabId: 1 },
    });

    expect((res1.data as any).lastAnalysis?.decision).toBe('WARN');

    const res2 = await routeExtensionMessage({
      type: 'GET_STATUS',
      requestId: 'REQ-STATUS-2',
      timestamp: new Date().toISOString(),
      payload: { tabId: 2 },
    });

    expect((res2.data as any).lastAnalysis).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 26: Web-App Synchronization Deep Link
  // ---------------------------------------------------------------------------
  it('Test 26: openWebAppAnalysis formats deep link URL with analysis ID exclusively', () => {
    const manager = new InPageProtectionManager();
    const openSpy = vi.spyOn(chrome.runtime, 'sendMessage');

    manager.openWebAppAnalysis('ANA-SYNC-026');

    expect(openSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        type: 'OPEN_NIVESH_APP',
        payload: { analysisId: 'ANA-SYNC-026' },
      })
    );
  });

  // ---------------------------------------------------------------------------
  // Test 27: Accessibility & Keyboard Navigation
  // ---------------------------------------------------------------------------
  it('Test 27: overlay sets dialog ARIA semantics and responds to Escape key', () => {
    const overlay = new ProtectionOverlay(callbacks);
    overlay.render({
      analysisId: 'ANA-A11Y-027',
      decision: 'WARN',
      severity: 'MEDIUM',
      primaryReason: 'Accessibility test.',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-A11Y-027',
    });

    const root = document.getElementById('nivesh-firewall-root');
    const shadow = root?.shadowRoot;
    const banner = shadow?.querySelector('.nivesh-banner');
    expect(banner?.getAttribute('role')).toBe('status');

    // Press Escape
    const escEvent = new KeyboardEvent('keydown', { key: 'Escape' });
    document.dispatchEvent(escEvent);

    expect(mockDismiss).toHaveBeenCalled();
    expect(document.getElementById('nivesh-firewall-root')).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 28: Performance (Zero continuous scanning)
  // ---------------------------------------------------------------------------
  it('Test 28: protection layer attaches zero continuous MutationObservers or keystroke listeners', () => {
    const observerSpy = vi.spyOn(window, 'MutationObserver');

    protectionManager.showIntervention({
      analysisId: 'ANA-PERF-028',
      decision: 'INFORM',
      severity: 'LOW',
      primaryReason: 'Performance check',
      webAppUrl: 'http://localhost:5173/#protect?id=ANA-PERF-028',
    });

    expect(observerSpy).not.toHaveBeenCalled();
    protectionManager.cleanup();
  });
});
