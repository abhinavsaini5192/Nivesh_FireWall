/**
 * In-Page Protection Layer Types (Phase 13.4)
 *
 * Types for in-page intervention overlay, targeted action matching,
 * override flow, and protection lifecycle states.
 */

export type InPageDecision = 'ALLOW' | 'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK';

export interface TargetActionInfo {
  actionId: string;
  actionType: string;
  target?: string | null;
  impactCategory: string;
  reversibility?: string;
  urgencyDetected?: boolean;
}

export interface InPageInterventionPayload {
  analysisId: string;
  decision: InPageDecision | string;
  severity: string;
  primaryReason: string;
  userMessage?: string;
  claimsCount?: number;
  evidenceStatus?: string;
  identityStatus?: string;
  fingerprintMatch?: string;
  threatSignalCount?: number;
  webAppUrl: string;
  targetUrl?: string;
  sourceType?: string;
  actions?: TargetActionInfo[];
  timestamp?: string;
}

export interface TargetMatchResult {
  matchedElement: HTMLElement | null;
  matchConfidence: 'EXACT' | 'AMBIGUOUS' | 'NO_MATCH';
  targetUrl?: string;
  actionId?: string;
  reason: string;
}

export interface ProtectionState {
  active: boolean;
  decision: InPageDecision | null;
  analysisId: string | null;
  targetUrl?: string;
  overridden: boolean;
  blockedTargetUrl?: string;
  timestamp?: string;
}
