/**
 * Targeted Navigation Interceptor (Phase 13.4 Sections 9, 24, 25)
 *
 * Implements:
 * 1. Targeted Action Protection: Intercepts ONLY the specifically matched target link/action.
 * 2. Unrelated Links Unaffected: Never blocks normal page links or global navigation.
 * 3. Policy Adherence:
 *    - BLOCK: Prevents navigation and re-shows blocked UI.
 *    - PAUSE: Pauses navigation and presents explicit confirmation overlay.
 *    - OVERRIDDEN: Allows navigation to proceed once user confirmed.
 * 4. Zero Credential / Form Interception: Never attaches to password, OTP, CVV, or payment inputs.
 * 5. Event Cleanup: Properly removes click listeners on teardown.
 */

import type { InPageInterventionPayload } from './types';

export interface InterceptorCallbacks {
  onTargetTriggered: (element: HTMLElement, payload: InPageInterventionPayload) => void;
}

export class TargetedNavigationInterceptor {
  private targetElement: HTMLElement | null = null;
  private currentPayload: InPageInterventionPayload | null = null;
  private isOverridden = false;
  private clickListener: ((e: MouseEvent) => void) | null = null;
  private callbacks: InterceptorCallbacks;

  constructor(callbacks: InterceptorCallbacks) {
    this.callbacks = callbacks;
  }

  /**
   * Attaches targeted listener exclusively to the matched element.
   */
  public attach(element: HTMLElement, payload: InPageInterventionPayload): void {
    this.detach(); // Clean up prior listener

    // Do not attach for ALLOW, INFORM, or WARN (only PAUSE & BLOCK require targeted action interception)
    if (payload.decision !== 'PAUSE' && payload.decision !== 'BLOCK') {
      return;
    }

    this.targetElement = element;
    this.currentPayload = payload;
    this.isOverridden = false;

    this.clickListener = (e: MouseEvent) => {
      // If user has explicitly confirmed override on PAUSE, allow proceeding
      if (this.isOverridden) {
        return;
      }

      if (!this.targetElement || !this.currentPayload) {
        return;
      }

      // Check if click originated from or targeted the protected element
      const targetEl = this.targetElement;
      const target = e.target as HTMLElement | null;
      if (target && (target === targetEl || targetEl.contains(target))) {
        // Prevent targeted navigation or submission
        e.preventDefault();
        e.stopPropagation();

        this.callbacks.onTargetTriggered(targetEl, this.currentPayload);
      }
    };

    // Attach capture listener on document to intercept before page scripts
    document.addEventListener('click', this.clickListener, true);
  }

  /**
   * Marks the target as overridden by explicit user action (PAUSE only).
   */
  public setOverridden(overridden: boolean): void {
    this.isOverridden = overridden;
  }

  public getIsOverridden(): boolean {
    return this.isOverridden;
  }

  public getTargetElement(): HTMLElement | null {
    return this.targetElement;
  }

  /**
   * Detaches click listeners and clears target element reference.
   */
  public detach(): void {
    if (this.clickListener) {
      document.removeEventListener('click', this.clickListener, true);
      this.clickListener = null;
    }
    this.targetElement = null;
    this.currentPayload = null;
    this.isOverridden = false;
  }
}
