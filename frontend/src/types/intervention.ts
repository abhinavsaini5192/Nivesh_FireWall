/**
 * Canonical Types for Nivesh Firewall Intervention Layer (Phase 12.3)
 *
 * Provides presentation-level structures derived strictly from the backend
 * Engine 8 policy decision and supporting engine summaries.
 * ZERO client-side policy evaluation or threat scoring.
 */

import type {
  PolicyDecisionType,
  PolicySeverity,
  FirewallActionSummary,
  FirewallAnalysisResponse,
} from './firewall';

export type {
  PolicyDecisionType,
  PolicySeverity,
  FirewallActionSummary,
  FirewallAnalysisResponse,
};

export type UserActionType =
  | 'continue'
  | 'view-details'
  | 'review-why'
  | 'review-details'
  | 'view-evidence'
  | 'go-back'
  | 'override'
  | 'analyze-another'
  | 'return-to-protect';

export interface InterventionReasonItem {
  id: string;
  label: string;
  sourceEngine: 'e2' | 'e3' | 'e4' | 'e5' | 'e6' | 'e7' | 'e8' | 'e9' | 'e10';
  targetSectionId: string;
  code?: string;
  actionText?: string;
}

export interface ProtectionSummaryDimension {
  dimension: string;
  status: string;
  detail?: string;
  variant: 'neutral' | 'allow' | 'inform' | 'warn' | 'pause' | 'block';
  targetSectionId: string;
}

export interface InterventionModel {
  decision: PolicyDecisionType;
  severity: PolicySeverity;
  headline: string;
  statusLabel: string;
  subheadline: string;
  userMessage: string;
  primaryReason: string;
  reasonCodes: string[];
  recommendedNextStep: string;
  reasons: InterventionReasonItem[];
  protectionSummary: ProtectionSummaryDimension[];
  highImpactActions: FirewallActionSummary[];
  requiresConfirmation: boolean;
  cooldownSeconds?: number;
  availableActions: UserActionType[];
  analysisId: string;
  sessionId?: string;
}

/**
 * Pure derivation helper: maps canonical backend FirewallAnalysisResponse
 * into a presentation-level InterventionModel.
 *
 * CRITICAL RULE: This function NEVER calculates risk, re-evaluates policy,
 * or modifies the backend decision. The backend Engine 8 decision is authoritative.
 */
export function deriveInterventionModel(analysis: FirewallAnalysisResponse): InterventionModel {
  // Safety Boundary: If decision is unexpectedly missing, default to BLOCK
  const rawDecision = analysis?.decision?.decision;
  const decision: PolicyDecisionType = (
    rawDecision && ['ALLOW', 'INFORM', 'WARN', 'PAUSE', 'BLOCK'].includes(rawDecision)
      ? rawDecision
      : 'BLOCK'
  ) as PolicyDecisionType;

  const severity: PolicySeverity = analysis?.decision?.severity || 'HIGH';
  const userMessage =
    analysis?.decision?.explanation?.user_message ||
    analysis?.decision?.primary_reason ||
    'Protection policy evaluated this content.';
  const primaryReason =
    analysis?.decision?.primary_reason || 'Policy rule conditions satisfied.';
  const reasonCodes = analysis?.decision?.reason_codes || [];

  // High-Impact Actions identified by Engine 3
  const highImpactActions = (analysis?.actions || []).filter(
    (act: FirewallActionSummary) =>
      act.impact_category === 'FINANCIAL_REQUEST' ||
      act.impact_category === 'APPLICATION_INSTALLATION' ||
      act.impact_category === 'CREDENTIAL_ACCESS' ||
      act.reversibility === 'IRREVERSIBLE' ||
      act.urgency_detected
  );

  // Dimension 1: Action Requested (Engine 3)
  const topAction = highImpactActions[0] || analysis?.actions?.[0];
  const actionSummaryStatus = topAction
    ? `${topAction.action_type.replace(/_/g, ' ')}${topAction.target ? ` (${topAction.target})` : ''}`
    : 'None detected';

  // Dimension 2: Identity Status (Engine 9)
  const identityStatusRaw = analysis?.identity?.identity_status || 'NOT_ESTABLISHED';
  const identityStatusFormatted = identityStatusRaw.replace(/_/g, ' ');

  // Dimension 3: Evidence Status (Engine 5)
  const evidenceStatusRaw = analysis?.evidence?.overall_status || 'INSUFFICIENT_EVIDENCE';
  const evidenceStatusFormatted = evidenceStatusRaw.replace(/_/g, ' ');

  // Dimension 4: Threat Pattern (Engine 6 & 7)
  const fingerprintMatch = analysis?.fingerprint?.match_type || 'NO_MATCH';
  const threatPatternFormatted =
    fingerprintMatch !== 'NO_MATCH'
      ? `Template: ${fingerprintMatch.replace(/_/g, ' ')}`
      : analysis?.threat?.threat_signals?.length
      ? `${analysis.threat.threat_signals.length} signal${analysis.threat.threat_signals.length === 1 ? '' : 's'} mapped`
      : 'No template match';

  // Dimension 5: Behavioural Signal (Engine 10)
  const behaviourSignals = analysis?.behaviour?.signals || [];
  const behaviourFormatted =
    behaviourSignals.length > 0
      ? behaviourSignals.map((s: string) => s.replace(/_/g, ' ')).join(', ')
      : 'Neutral interaction';

  const protectionSummary: ProtectionSummaryDimension[] = [
    {
      dimension: 'Requested Action',
      status: actionSummaryStatus,
      detail: topAction ? `Reversibility: ${topAction.reversibility}` : undefined,
      variant:
        topAction?.reversibility === 'IRREVERSIBLE'
          ? 'danger' as any
          : topAction
          ? 'warn'
          : 'neutral',
      targetSectionId: 'panel-actions',
    },
    {
      dimension: 'Entity Identity',
      status: identityStatusFormatted,
      detail: analysis?.identity?.claimed_entities?.length
        ? `Entities: ${analysis.identity.claimed_entities.join(', ')}`
        : undefined,
      variant:
        identityStatusRaw === 'ESTABLISHED'
          ? 'allow'
          : identityStatusRaw === 'IDENTITY_MISMATCH'
          ? 'block'
          : 'warn',
      targetSectionId: 'panel-identity',
    },
    {
      dimension: 'Claim Evidence',
      status: evidenceStatusFormatted,
      detail: `${analysis?.evidence?.supported_claims_count || 0} supported, ${
        analysis?.evidence?.contradicted_claims_count || 0
      } contradicted`,
      variant:
        evidenceStatusRaw === 'SUPPORTED'
          ? 'allow'
          : evidenceStatusRaw === 'CONTRADICTED'
          ? 'block'
          : 'warn',
      targetSectionId: 'panel-evidence',
    },
    {
      dimension: 'Threat Template',
      status: threatPatternFormatted,
      detail: analysis?.threat?.attack_stage && analysis?.threat?.terminal_stage
        ? `Progression: ${analysis.threat.attack_stage} -> ${analysis.threat.terminal_stage}`
        : undefined,
      variant:
        fingerprintMatch !== 'NO_MATCH' || (analysis?.threat?.threat_signals?.length || 0) > 0
          ? 'block'
          : 'neutral',
      targetSectionId: fingerprintMatch !== 'NO_MATCH' ? 'panel-fingerprint' : 'panel-threat',
    },
    {
      dimension: 'Observed Behaviour',
      status: behaviourFormatted,
      detail: analysis?.behaviour?.time_pressure_detected
        ? 'Time pressure / countdown detected'
        : undefined,
      variant: behaviourSignals.length > 0 ? 'warn' : 'neutral',
      targetSectionId: 'panel-behaviour',
    },
  ];

  // Specific Why Intervened Supporting Items (Connected to relevant engines)
  const reasons: InterventionReasonItem[] = [];

  // Primary Reason
  reasons.push({
    id: 'reason-primary',
    label: primaryReason,
    sourceEngine: 'e8',
    targetSectionId: 'panel-provenance',
    code: reasonCodes[0],
  });

  // High-impact action finding (Engine 3)
  if (highImpactActions.length > 0) {
    const act = highImpactActions[0];
    reasons.push({
      id: 'reason-action',
      label: `Requested ${act.action_type.replace(/_/g, ' ')} action${
        act.target ? ` targeting ${act.target}` : ''
      } (${act.reversibility.toLowerCase()} reversibility).`,
      sourceEngine: 'e3',
      targetSectionId: 'panel-actions',
      actionText: 'See requested action',
    });
  }

  // Identity finding (Engine 9)
  if (
    analysis?.identity?.identity_status === 'NOT_ESTABLISHED' ||
    analysis?.identity?.identity_status === 'IDENTITY_MISMATCH'
  ) {
    reasons.push({
      id: 'reason-identity',
      label:
        analysis.identity.identity_status === 'IDENTITY_MISMATCH'
          ? 'Claimed identity does not match official intermediary registry details.'
          : 'Claimed entity could not be verified against official regulatory registries.',
      sourceEngine: 'e9',
      targetSectionId: 'panel-identity',
      actionText: 'See identity verification',
    });
  }

  // Contradicted claims (Engine 2 & 5)
  if ((analysis?.evidence?.contradicted_claims_count || 0) > 0) {
    reasons.push({
      id: 'reason-evidence',
      label: 'Financial claim or return guarantee contradicted by statutory regulations.',
      sourceEngine: 'e5',
      targetSectionId: 'panel-evidence',
      actionText: 'See contradicted claims',
    });
  }

  // Threat signals (Engine 6)
  if ((analysis?.threat?.threat_signals?.length || 0) > 0) {
    reasons.push({
      id: 'reason-threat',
      label: `Detected threat signals: ${analysis.threat.threat_signals
        .map((s: string) => s.replace(/_/g, ' '))
        .join(', ')}.`,
      sourceEngine: 'e6',
      targetSectionId: 'panel-threat',
      actionText: 'View threat analysis',
    });
  }

  // Structural Template (Engine 7)
  if (analysis?.fingerprint?.match_type && analysis.fingerprint.match_type !== 'NO_MATCH') {
    reasons.push({
      id: 'reason-fingerprint',
      label: `Matched structural template pattern (${analysis.fingerprint.match_type.replace(
        /_/g,
        ' '
      )}) previously observed in circulation.`,
      sourceEngine: 'e7',
      targetSectionId: 'panel-fingerprint',
      actionText: 'View template match',
    });
  }

  // Behavioural finding (Engine 10)
  if ((analysis?.behaviour?.signals?.length || 0) > 0) {
    reasons.push({
      id: 'reason-behaviour',
      label: `Interaction signals: ${analysis.behaviour.signals
        .map((s: string) => s.replace(/_/g, ' '))
        .join(', ')}.`,
      sourceEngine: 'e10',
      targetSectionId: 'panel-behaviour',
      actionText: 'View behavioural signals',
    });
  }

  // Configure Experience Properties by Canonical Backend Decision
  switch (decision) {
    case 'ALLOW':
      return {
        decision: 'ALLOW',
        severity,
        headline: 'ACTION PERMITTED — VERIFIED NEUTRAL',
        statusLabel: 'Action Permitted',
        subheadline:
          'Nivesh did not identify a condition requiring protection intervention under applicable policy conditions.',
        userMessage,
        primaryReason,
        reasonCodes,
        recommendedNextStep:
          'You may continue with your interaction. Always independently verify financial counterparties before transferring funds.',
        reasons,
        protectionSummary,
        highImpactActions,
        requiresConfirmation: false,
        cooldownSeconds: undefined,
        availableActions: ['continue', 'view-details', 'analyze-another'],
        analysisId: analysis.analysis_id,
        sessionId: analysis.session_id,
      };

    case 'INFORM':
      return {
        decision: 'INFORM',
        severity,
        headline: 'INFORMATIONAL ADVISORY',
        statusLabel: 'Informational Advisory',
        subheadline:
          'Nivesh found contextual information that may be helpful to review before continuing.',
        userMessage,
        primaryReason,
        reasonCodes,
        recommendedNextStep:
          'Review the advisory context below to ensure this interaction aligns with your financial intentions.',
        reasons,
        protectionSummary,
        highImpactActions,
        requiresConfirmation: false,
        cooldownSeconds: undefined,
        availableActions: ['continue', 'view-details', 'analyze-another'],
        analysisId: analysis.analysis_id,
        sessionId: analysis.session_id,
      };

    case 'WARN':
      return {
        decision: 'WARN',
        severity,
        headline: 'CAUTION RECOMMENDED',
        statusLabel: 'Caution Recommended',
        subheadline:
          'Nivesh identified potential risk signals that should be verified before you proceed.',
        userMessage,
        primaryReason,
        reasonCodes,
        recommendedNextStep:
          'Verify the adviser credentials and offering details through official SEBI/NSE channels before taking any action.',
        reasons,
        protectionSummary,
        highImpactActions,
        requiresConfirmation: false,
        cooldownSeconds: undefined,
        availableActions: ['review-details', 'go-back', 'analyze-another'],
        analysisId: analysis.analysis_id,
        sessionId: analysis.session_id,
      };

    case 'PAUSE':
      return {
        decision: 'PAUSE',
        severity,
        headline: 'ACTION PAUSED — VERIFICATION REQUIRED',
        statusLabel: 'Action Paused',
        subheadline:
          'Take a moment before continuing. Nivesh identified multiple signals requiring additional verification.',
        userMessage,
        primaryReason,
        reasonCodes,
        recommendedNextStep:
          'Do not proceed without independent out-of-band verification. Discontinue private communication channels requesting payment.',
        reasons,
        protectionSummary,
        highImpactActions,
        requiresConfirmation: !!analysis?.decision?.required_user_confirmation,
        cooldownSeconds: analysis?.decision?.cooldown_seconds || 30,
        availableActions: analysis?.decision?.required_user_confirmation
          ? ['review-why', 'go-back', 'override', 'analyze-another']
          : ['review-why', 'go-back', 'analyze-another'],
        analysisId: analysis.analysis_id,
        sessionId: analysis.session_id,
      };

    case 'BLOCK':
    default:
      return {
        decision: 'BLOCK',
        severity,
        headline: 'ACTION BLOCKED — THREAT PREVENTED',
        statusLabel: 'Action Blocked',
        subheadline:
          'This action was blocked by Nivesh Firewall because the protection policy determined that intervention is required.',
        userMessage,
        primaryReason,
        reasonCodes,
        recommendedNextStep:
          'Do not transfer funds, share OTPs/credentials, or download external applications from this source.',
        reasons,
        protectionSummary,
        highImpactActions,
        requiresConfirmation: true,
        cooldownSeconds: undefined,
        availableActions: ['view-evidence', 'return-to-protect', 'analyze-another'],
        analysisId: analysis.analysis_id,
        sessionId: analysis.session_id,
      };
  }
}
