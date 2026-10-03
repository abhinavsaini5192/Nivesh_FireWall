/**
 * In-Page Protection Manager (Phase 13.4 Sections 2, 3, 19, 20, 33, 41)
 *
 * Central coordinator in the content script:
 * - Coordinates ProtectionOverlay and TargetedNavigationInterceptor.
 * - Enforces the Safe Fallback and Safe Uncertainty Rules.
 * - Preserves BLOCK protection state even after UI notification dismissal.
 * - Handles PAUSE override confirmation flow.
 * - Communicates with background worker via typed messages.
 */

import { ProtectionOverlay } from './overlay';
import { TargetedNavigationInterceptor } from './navigationInterceptor';
import { matchTargetAction } from './targetMatcher';
import { generateExtensionRequestId } from '../types/messages';
import type {
  InPageInterventionPayload,
  ProtectionState,
  InPageDecision,
} from './types';
import type { OpenNiveshAppMessage } from '../types/messages';

export class InPageProtectionManager {
  private overlay: ProtectionOverlay;
  private interceptor: TargetedNavigationInterceptor;
  private currentPayload: InPageInterventionPayload | null = null;
  private isOverridden = false;
  private active = false;

  constructor() {
    this.overlay = new ProtectionOverlay({
      onDismiss: () => {
        // For INFORM and WARN, dismissal clears active overlay
        // For BLOCK, the overlay closes but the targeted link remains blocked!
        if (this.currentPayload?.decision === 'INFORM' || this.currentPayload?.decision === 'WARN') {
          this.active = false;
        }
      },
      onOpenAnalysis: (analysisId: string) => {
        this.openWebAppAnalysis(analysisId);
      },
      onConfirmOverride: (analysisId: string) => {
        this.handleOverrideConfirmed(analysisId);
      },
      onReturn: () => {
        // Return to normal page browsing without overriding
      },
    });

    this.interceptor = new TargetedNavigationInterceptor({
      onTargetTriggered: (_element, payload) => {
        // When user clicks the protected target link, re-open the overlay
        this.overlay.render(payload);
      },
    });
  }

  /**
   * Displays in-page intervention and attaches targeted interceptor if applicable.
   */
  public showIntervention(payload: InPageInterventionPayload): void {
    if (!payload || payload.decision === 'ALLOW') {
      this.cleanup();
      return;
    }

    this.currentPayload = payload;
    this.active = true;
    this.isOverridden = false;

    // 1. Conservative target matching (Sections 9, 10, 11, 24, 25)
    if (payload.decision === 'PAUSE' || payload.decision === 'BLOCK') {
      const matchResult = matchTargetAction(document, payload.targetUrl, payload.actions);
      if (matchResult.matchConfidence === 'EXACT' && matchResult.matchedElement) {
        this.interceptor.attach(matchResult.matchedElement, payload);
      } else {
        // Ambiguous or no match: Do not guess, do not block arbitrary elements
        this.interceptor.detach();
      }
    } else {
      this.interceptor.detach();
    }

    // 2. Render isolated Shadow DOM overlay
    this.overlay.render(payload);
  }

  /**
   * Hides the visible overlay without clearing targeted block rules.
   */
  public hideIntervention(): void {
    this.overlay.destroy();
    if (this.currentPayload?.decision === 'INFORM' || this.currentPayload?.decision === 'WARN') {
      this.active = false;
    }
  }

  /**
   * Confirms explicit override for PAUSE.
   */
  private handleOverrideConfirmed(_analysisId: string): void {
    this.isOverridden = true;
    this.interceptor.setOverridden(true);
    this.active = false;
  }

  /**
   * Opens the full analysis in the Nivesh Web Application.
   */
  public openWebAppAnalysis(analysisId: string): void {
    if (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.sendMessage) {
      const openMsg: OpenNiveshAppMessage = {
        type: 'OPEN_NIVESH_APP',
        requestId: generateExtensionRequestId(),
        timestamp: new Date().toISOString(),
        payload: { analysisId },
      };
      chrome.runtime.sendMessage(openMsg);
    } else if (this.currentPayload?.webAppUrl) {
      window.open(this.currentPayload.webAppUrl, '_blank');
    }
  }

  /**
   * Returns current in-page protection state.
   */
  public getState(): ProtectionState {
    return {
      active: this.active,
      decision: (this.currentPayload?.decision as InPageDecision) || null,
      analysisId: this.currentPayload?.analysisId || null,
      targetUrl: this.currentPayload?.targetUrl,
      overridden: this.isOverridden,
      blockedTargetUrl:
        this.currentPayload?.decision === 'BLOCK' ? this.currentPayload.targetUrl : undefined,
      timestamp: this.currentPayload?.timestamp,
    };
  }

  public getOverlay(): ProtectionOverlay {
    return this.overlay;
  }

  public getInterceptor(): TargetedNavigationInterceptor {
    return this.interceptor;
  }

  /**
   * Completely tears down all overlays and listeners.
   */
  public cleanup(): void {
    this.overlay.destroy();
    this.interceptor.detach();
    this.currentPayload = null;
    this.isOverridden = false;
    this.active = false;
  }
}

export const protectionManager = new InPageProtectionManager();
