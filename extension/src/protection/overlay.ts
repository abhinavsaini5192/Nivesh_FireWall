/**
 * In-Page Protection Overlay Component (Phase 13.4 Sections 13, 14, 15, 16, 36, 37, 38)
 *
 * Implements:
 * 1. Shadow DOM Isolation: Encapsulates all styles and DOM from host page interference.
 * 2. Trusted UI Identity: Clearly branded Nivesh Firewall UI, distinct from webpage.
 * 3. DOM Safety: Treats all backend & page text as untrusted data using textContent exclusively.
 * 4. Policy Faithful Rendering: Distinct UI for INFORM, WARN, PAUSE, BLOCK.
 * 5. Explicit Override Dialog: For PAUSE with user confirmation; no silent BLOCK bypass.
 * 6. Accessibility & Focus Management: Keyboard navigation, ARIA attributes, Escape key handling.
 * 7. Event Cleanup: Complete teardown preventing memory leaks.
 */

import type { InPageInterventionPayload, InPageDecision } from './types';

export interface OverlayCallbacks {
  onDismiss: () => void;
  onOpenAnalysis: (analysisId: string) => void;
  onConfirmOverride?: (analysisId: string) => void;
  onReturn?: () => void;
}

export class ProtectionOverlay {
  private hostElement: HTMLElement | null = null;
  private shadowRoot: ShadowRoot | null = null;
  private keydownHandler: ((e: KeyboardEvent) => void) | null = null;
  private currentPayload: InPageInterventionPayload | null = null;
  private callbacks: OverlayCallbacks;

  constructor(callbacks: OverlayCallbacks) {
    this.callbacks = callbacks;
  }

  /**
   * Renders in-page protection overlay inside an isolated Shadow DOM container.
   */
  public render(payload: InPageInterventionPayload): void {
    this.destroy(); // Clean up any existing overlay

    if (payload.decision === 'ALLOW') {
      return; // ALLOW requires zero injected intervention (Section 4)
    }

    this.currentPayload = payload;

    // 1. Create root host element attached to document.body
    this.hostElement = document.createElement('div');
    this.hostElement.id = 'nivesh-firewall-root';
    this.hostElement.style.cssText = 'all: initial; position: relative; z-index: 2147483647;';

    // 2. Attach Shadow DOM (open mode for inspection & testing)
    this.shadowRoot = this.hostElement.attachShadow({ mode: 'open' });

    // 3. Inject CSS rules into shadow root
    const styleEl = document.createElement('style');
    styleEl.textContent = this.getOverlayStyles();
    this.shadowRoot.appendChild(styleEl);

    // 4. Build UI based on decision
    const uiWrapper = document.createElement('div');
    uiWrapper.className = `nivesh-container ${payload.decision.toLowerCase()}`;

    if (payload.decision === 'INFORM' || payload.decision === 'WARN') {
      uiWrapper.appendChild(this.buildBanner(payload));
    } else if (payload.decision === 'PAUSE') {
      uiWrapper.appendChild(this.buildPauseModal(payload));
    } else if (payload.decision === 'BLOCK') {
      uiWrapper.appendChild(this.buildBlockModal(payload));
    }

    this.shadowRoot.appendChild(uiWrapper);
    document.body.appendChild(this.hostElement);

    // 5. Setup keyboard trap and escape handling
    this.setupAccessibility(uiWrapper, payload.decision as InPageDecision);
  }

  /**
   * Builds non-blocking banner for INFORM or WARN.
   */
  private buildBanner(payload: InPageInterventionPayload): HTMLElement {
    const banner = document.createElement('div');
    banner.className = `nivesh-banner ${payload.decision.toLowerCase()}`;
    banner.setAttribute('role', 'status');
    banner.setAttribute('aria-live', 'polite');

    // Header
    const header = document.createElement('div');
    header.className = 'banner-header';

    const brand = document.createElement('span');
    brand.className = 'brand-tag';
    brand.textContent = 'NIVESH FIREWALL';

    const title = document.createElement('strong');
    title.className = 'banner-title';
    title.textContent =
      payload.decision === 'WARN' ? '⚠ Review Before Continuing' : 'ℹ Nivesh Information';

    header.appendChild(brand);
    header.appendChild(title);
    banner.appendChild(header);

    // Message Body
    const body = document.createElement('p');
    body.className = 'banner-body';
    body.textContent =
      payload.userMessage || payload.primaryReason || 'Review the information before proceeding.';
    banner.appendChild(body);

    // Action buttons
    const actions = document.createElement('div');
    actions.className = 'banner-actions';

    const btnView = document.createElement('button');
    btnView.className = 'btn btn-primary';
    btnView.textContent = payload.decision === 'WARN' ? 'Review Details' : 'View Analysis';
    btnView.addEventListener('click', () => {
      this.callbacks.onOpenAnalysis(payload.analysisId);
    });

    const btnDismiss = document.createElement('button');
    btnDismiss.className = 'btn btn-ghost';
    btnDismiss.textContent = 'Dismiss';
    btnDismiss.addEventListener('click', () => {
      this.destroy();
      this.callbacks.onDismiss();
    });

    actions.appendChild(btnView);
    actions.appendChild(btnDismiss);
    banner.appendChild(actions);

    return banner;
  }

  /**
   * Builds modal overlay for PAUSE with explicit override path.
   */
  private buildPauseModal(payload: InPageInterventionPayload): HTMLElement {
    const backdrop = document.createElement('div');
    backdrop.className = 'nivesh-backdrop';
    const modal = this.buildPauseModalElement(payload);
    backdrop.appendChild(modal);
    return backdrop;
  }

  private buildPauseModalElement(payload: InPageInterventionPayload): HTMLElement {
    const modal = document.createElement('div');
    modal.className = 'nivesh-modal pause';
    modal.setAttribute('role', 'dialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'nivesh-pause-title');

    // Header Badge
    const header = document.createElement('div');
    header.className = 'modal-header';

    const badge = document.createElement('span');
    badge.className = 'decision-badge pause';
    badge.textContent = '⏸ ACTION PAUSED';

    const brand = document.createElement('span');
    brand.className = 'brand-tag';
    brand.textContent = 'NIVESH FIREWALL';

    header.appendChild(badge);
    header.appendChild(brand);
    modal.appendChild(header);

    // Title & Primary Reason
    const title = document.createElement('h2');
    title.id = 'nivesh-pause-title';
    title.className = 'modal-title';
    title.textContent = 'Action Paused Before Proceeding';

    const desc = document.createElement('p');
    desc.className = 'modal-description';
    desc.textContent =
      payload.userMessage ||
      payload.primaryReason ||
      'Nivesh recommends reviewing the available evidence before continuing.';

    modal.appendChild(title);
    modal.appendChild(desc);

    // Structured Inspection Grid (Section 17)
    const grid = document.createElement('div');
    grid.className = 'reason-grid';

    if (payload.identityStatus) {
      grid.appendChild(this.buildGridItem('Identity', payload.identityStatus));
    }
    if (payload.evidenceStatus) {
      grid.appendChild(this.buildGridItem('Evidence', payload.evidenceStatus));
    }
    if (payload.claimsCount && payload.claimsCount > 0) {
      grid.appendChild(this.buildGridItem('Claims Evaluated', `${payload.claimsCount}`));
    }
    if (payload.fingerprintMatch && payload.fingerprintMatch !== 'NO_MATCH') {
      grid.appendChild(this.buildGridItem('Pattern', payload.fingerprintMatch));
    }
    modal.appendChild(grid);

    // Actions
    const actions = document.createElement('div');
    actions.className = 'modal-actions';

    const btnReviewWhy = document.createElement('button');
    btnReviewWhy.className = 'btn btn-secondary';
    btnReviewWhy.textContent = 'Review Why (Open Details)';
    btnReviewWhy.addEventListener('click', () => {
      this.callbacks.onOpenAnalysis(payload.analysisId);
    });

    const btnReturn = document.createElement('button');
    btnReturn.className = 'btn btn-ghost';
    btnReturn.textContent = 'Return to Page';
    btnReturn.addEventListener('click', () => {
      this.destroy();
      if (this.callbacks.onReturn) this.callbacks.onReturn();
      this.callbacks.onDismiss();
    });

    const btnOverride = document.createElement('button');
    btnOverride.className = 'btn btn-outline';
    btnOverride.textContent = 'Continue After Confirmation';
    btnOverride.addEventListener('click', () => {
      this.showOverrideConfirmationDialog(payload);
    });

    actions.appendChild(btnReviewWhy);
    actions.appendChild(btnReturn);
    actions.appendChild(btnOverride);
    modal.appendChild(actions);

    return modal;
  }

  /**
   * Builds modal overlay for BLOCK.
   */
  private buildBlockModal(payload: InPageInterventionPayload): HTMLElement {
    const backdrop = document.createElement('div');
    backdrop.className = 'nivesh-backdrop';

    const modal = document.createElement('div');
    modal.className = 'nivesh-modal block';
    modal.setAttribute('role', 'alertdialog');
    modal.setAttribute('aria-modal', 'true');
    modal.setAttribute('aria-labelledby', 'nivesh-block-title');

    // Header Badge
    const header = document.createElement('div');
    header.className = 'modal-header';

    const badge = document.createElement('span');
    badge.className = 'decision-badge block';
    badge.textContent = '🛑 ACTION BLOCKED';

    const brand = document.createElement('span');
    brand.className = 'brand-tag';
    brand.textContent = 'NIVESH FIREWALL';

    header.appendChild(badge);
    header.appendChild(brand);
    modal.appendChild(header);

    // Title & Primary Reason
    const title = document.createElement('h2');
    title.id = 'nivesh-block-title';
    title.className = 'modal-title';
    title.textContent = 'Supported Interaction Blocked';

    const desc = document.createElement('p');
    desc.className = 'modal-description';
    desc.textContent =
      payload.userMessage ||
      'Nivesh Firewall blocked this supported interaction according to its protection policy.';
    modal.appendChild(title);
    modal.appendChild(desc);

    if (payload.primaryReason && payload.primaryReason !== payload.userMessage) {
      const reasonBox = document.createElement('div');
      reasonBox.className = 'grid-item';
      const reasonTitle = document.createElement('span');
      reasonTitle.className = 'grid-label';
      reasonTitle.textContent = 'Primary Reason:';
      const reasonVal = document.createElement('p');
      reasonVal.className = 'modal-description';
      reasonVal.textContent = payload.primaryReason;
      reasonBox.appendChild(reasonTitle);
      reasonBox.appendChild(reasonVal);
      modal.appendChild(reasonBox);
    }

    // Actions (NO generic bypass, Section 21)
    const actions = document.createElement('div');
    actions.className = 'modal-actions';

    const btnView = document.createElement('button');
    btnView.className = 'btn btn-primary';
    btnView.textContent = 'View Full Technical Analysis';
    btnView.addEventListener('click', () => {
      this.callbacks.onOpenAnalysis(payload.analysisId);
    });

    const btnReturn = document.createElement('button');
    btnReturn.className = 'btn btn-ghost';
    btnReturn.textContent = 'Close Notification';
    btnReturn.addEventListener('click', () => {
      this.destroy();
      if (this.callbacks.onReturn) this.callbacks.onReturn();
      this.callbacks.onDismiss();
    });

    actions.appendChild(btnView);
    actions.appendChild(btnReturn);
    modal.appendChild(actions);

    backdrop.appendChild(modal);
    return backdrop;
  }

  /**
   * Shows explicit confirmation dialog for PAUSE override (Section 20).
   */
  private showOverrideConfirmationDialog(payload: InPageInterventionPayload): void {
    if (!this.shadowRoot) return;

    // Replace current modal content with explicit confirmation dialog inside existing backdrop
    const backdrop = this.shadowRoot.querySelector('.nivesh-backdrop');
    if (!backdrop) return;

    backdrop.innerHTML = '';

    const dialog = document.createElement('div');
    dialog.className = 'nivesh-modal override-dialog';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.setAttribute('aria-labelledby', 'nivesh-override-title');

    const brand = document.createElement('span');
    brand.className = 'brand-tag';
    brand.textContent = 'NIVESH CONFIRMATION REQUIRED';
    dialog.appendChild(brand);

    const title = document.createElement('h3');
    title.id = 'nivesh-override-title';
    title.className = 'modal-title';
    title.textContent = 'Continue With This Action?';
    dialog.appendChild(title);

    const desc = document.createElement('p');
    desc.className = 'modal-description';
    desc.textContent =
      'Nivesh previously paused this action because additional verification was required. Confirming will allow this interaction to proceed.';
    dialog.appendChild(desc);

    const actions = document.createElement('div');
    actions.className = 'modal-actions';

    const btnCancel = document.createElement('button');
    btnCancel.className = 'btn btn-ghost';
    btnCancel.textContent = 'Cancel';
    btnCancel.addEventListener('click', () => {
      // Return to PAUSE modal inside existing backdrop
      backdrop.innerHTML = '';
      const pauseModal = this.buildPauseModalElement(payload);
      backdrop.appendChild(pauseModal);
    });

    const btnConfirm = document.createElement('button');
    btnConfirm.className = 'btn btn-danger';
    btnConfirm.textContent = 'Confirm & Continue';
    btnConfirm.addEventListener('click', () => {
      this.destroy();
      if (this.callbacks.onConfirmOverride) {
        this.callbacks.onConfirmOverride(payload.analysisId);
      }
    });

    actions.appendChild(btnCancel);
    actions.appendChild(btnConfirm);
    dialog.appendChild(actions);

    backdrop.appendChild(dialog);
    btnCancel.focus();
  }

  private buildGridItem(label: string, value: string): HTMLElement {
    const item = document.createElement('div');
    item.className = 'grid-item';

    const lbl = document.createElement('span');
    lbl.className = 'grid-label';
    lbl.textContent = label;

    const val = document.createElement('strong');
    val.className = 'grid-value';
    val.textContent = value;

    item.appendChild(lbl);
    item.appendChild(val);
    return item;
  }

  /**
   * Sets up focus trapping and keyboard listeners.
   */
  private setupAccessibility(container: HTMLElement, decision: InPageDecision): void {
    const focusable = container.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    if (focusable.length > 0) {
      focusable[0].focus();
    }

    this.keydownHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (decision === 'INFORM' || decision === 'WARN') {
          this.destroy();
          this.callbacks.onDismiss();
        }
      }

      if (e.key === 'Tab' && focusable.length > 1) {
        const first = focusable[0];
        const last = focusable[focusable.length - 1];

        if (e.shiftKey && document.activeElement === first) {
          last.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', this.keydownHandler);
  }

  /**
   * Cleans up all DOM nodes and event listeners.
   */
  public destroy(): void {
    if (this.keydownHandler) {
      document.removeEventListener('keydown', this.keydownHandler);
      this.keydownHandler = null;
    }

    if (this.hostElement && this.hostElement.parentNode) {
      this.hostElement.parentNode.removeChild(this.hostElement);
    }

    this.hostElement = null;
    this.shadowRoot = null;
    this.currentPayload = null;
  }

  public getPayload(): InPageInterventionPayload | null {
    return this.currentPayload;
  }

  /**
   * Shadow DOM CSS styles encapsulated completely from the host page.
   */
  private getOverlayStyles(): string {
    return `
      :host {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        color: #f8fafc;
        line-height: 1.5;
      }
      * {
        box-sizing: border-box;
        margin: 0;
        padding: 0;
      }
      .brand-tag {
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
      }

      /* Non-blocking Banners (INFORM & WARN) */
      .nivesh-banner {
        position: fixed;
        top: 20px;
        right: 20px;
        width: 360px;
        max-width: calc(100vw - 40px);
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.4);
        display: flex;
        flex-direction: column;
        gap: 10px;
        z-index: 2147483647;
        animation: niveshSlideIn 0.2s cubic-bezier(0.16, 1, 0.3, 1);
      }
      .nivesh-banner.warn {
        border-color: #f59e0b;
        background: #1e1b18;
      }
      .banner-header {
        display: flex;
        flex-direction: column;
        gap: 4px;
      }
      .banner-title {
        font-size: 14px;
        color: #f8fafc;
      }
      .nivesh-banner.warn .banner-title {
        color: #fbbf24;
      }
      .banner-body {
        font-size: 12px;
        color: #cbd5e1;
        line-height: 1.4;
      }
      .banner-actions {
        display: flex;
        gap: 8px;
        margin-top: 4px;
      }

      /* Modal Overlays (PAUSE & BLOCK) */
      .nivesh-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(15, 23, 42, 0.85);
        backdrop-filter: blur(4px);
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
        z-index: 2147483647;
        animation: niveshFadeIn 0.2s ease;
      }
      .nivesh-modal {
        background: #0f172a;
        border: 1px solid #334155;
        border-radius: 12px;
        width: 480px;
        max-width: 100%;
        padding: 24px;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .nivesh-modal.pause {
        border-color: #f97316;
      }
      .nivesh-modal.block {
        border-color: #ef4444;
      }
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .decision-badge {
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 4px;
      }
      .decision-badge.pause {
        background: rgba(249, 115, 22, 0.2);
        color: #fb923c;
        border: 1px solid #f97316;
      }
      .decision-badge.block {
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid #ef4444;
      }
      .modal-title {
        font-size: 18px;
        font-weight: 700;
        color: #f8fafc;
      }
      .modal-description {
        font-size: 13px;
        color: #cbd5e1;
        line-height: 1.5;
      }
      .reason-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 10px;
        background: #1e293b;
        padding: 12px;
        border-radius: 8px;
        border: 1px solid #334155;
      }
      .grid-item {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .grid-label {
        font-size: 10px;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 600;
      }
      .grid-value {
        font-size: 12px;
        color: #f1f5f9;
        font-family: monospace;
      }
      .modal-actions {
        display: flex;
        gap: 10px;
        margin-top: 8px;
        flex-wrap: wrap;
      }

      /* Buttons */
      .btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        padding: 8px 14px;
        font-size: 12px;
        font-weight: 600;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.15s ease;
        border: 1px solid transparent;
        text-decoration: none;
      }
      .btn-primary {
        background: #0ea5e9;
        color: #0f172a;
      }
      .btn-primary:hover {
        background: #38bdf8;
      }
      .btn-secondary {
        background: #1e293b;
        color: #f8fafc;
        border-color: #475569;
      }
      .btn-secondary:hover {
        background: #334155;
      }
      .btn-ghost {
        background: transparent;
        color: #94a3b8;
        border-color: #334155;
      }
      .btn-ghost:hover {
        background: #1e293b;
        color: #f8fafc;
      }
      .btn-outline {
        background: transparent;
        color: #fb923c;
        border-color: #f97316;
      }
      .btn-outline:hover {
        background: rgba(249, 115, 22, 0.15);
      }
      .btn-danger {
        background: #dc2626;
        color: #f8fafc;
      }
      .btn-danger:hover {
        background: #ef4444;
      }

      @keyframes niveshSlideIn {
        from { opacity: 0; transform: translateY(-10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      @keyframes niveshFadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
      }
    `;
  }
}
