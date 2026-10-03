/**
 * Intelligence & Visualization Types for Nivesh Firewall (Phase 12.4)
 * Pure presentation contracts aligned with backend intelligence engines.
 */

import type {
  FirewallAnalysisResponse,
  FirewallClaimSummary,
  FirewallActionSummary,
  EvidenceStatus,
  IdentityStatus,
} from './firewall';

export type IntelligenceViewMode = 'user' | 'technical';

export type ActionProgressionLevel = 1 | 2 | 3 | 4 | 5;

export interface ActionHierarchyStage {
  level: ActionProgressionLevel;
  name: string;
  categoryKey: string;
  description: string;
  isDetected: boolean;
  actions: FirewallActionSummary[];
}

export interface ClaimSPOModel {
  claimId: string;
  rawText: string;
  subject: string;
  predicate: string;
  object: string;
  modality: string;
  topic: string;
  verificationStatus: EvidenceStatus | string;
  statusExplanation: string;
  verificationRequirement: string;
}

export interface AttackPathNode {
  id: string;
  stageName: string;
  stageKey: string;
  isTerminal: boolean;
  status: 'active' | 'completed' | 'potential';
  associatedAction?: string;
  associatedClaim?: string;
  supportingSignal?: string;
  timestamp?: string;
}

export interface ClaimActionLinkModel {
  claimId: string;
  claimText: string;
  actionId: string;
  actionType: string;
  relationType: 'JUSTIFIES' | 'RATIONALE_FOR' | 'LEADS_TO';
}

export interface EntityRelationshipNode {
  claimedEntity: string;
  registrationClaim?: string;
  authoritativeRecord?: string;
  identityStatus: IdentityStatus | string;
  findings: string[];
}

export interface FingerprintDimensionItem {
  name: string;
  category: string;
  matched: boolean;
  detail?: string;
}

export interface BehaviourTimelineEvent {
  id: string;
  timestamp: string;
  eventType: string;
  title: string;
  description: string;
  category: 'content' | 'action' | 'behaviour' | 'policy' | 'user';
  isEscalation?: boolean;
}

export interface PolicyTraceNode {
  decision: string;
  primaryReason: string;
  reasonCodes: string[];
  contributingFindings: {
    engine: string;
    finding: string;
    status: string;
  }[];
}

/**
 * Sensitive fields strictly prohibited from frontend display
 */
export const FORBIDDEN_CREDENTIAL_FIELDS = [
  'password',
  'passwd',
  'pin',
  'otp',
  'cvv',
  'cvv2',
  'card_number',
  'credit_card',
  'debit_card',
  'bank_account',
  'account_number',
  'secret',
  'api_key',
  'access_token',
  'auth_token',
  'private_key',
  'keystroke',
] as const;

/**
 * Sanitizes any data structure to strip forbidden credentials before rendering
 */
export function sanitizeDataForRendering<T>(data: T): T {
  if (data === null || data === undefined) {
    return data;
  }
  if (typeof data === 'string') {
    let clean: string = data as string;
    // Redact 12-19 digit card numbers
    clean = clean.replace(/\b(?:\d[ -]*?){13,19}\b/g, '[REDACTED_ACCOUNT]');
    // Redact 4-6 digit numeric OTPs in sensitive contexts
    clean = clean.replace(/(?:otp|pin|cvv)[:=\s]+([0-9]{3,6})/gi, '***REDACTED***');
    return clean as unknown as T;
  }
  if (Array.isArray(data)) {
    return data.map((item) => sanitizeDataForRendering(item)) as unknown as T;
  }
  if (typeof data === 'object') {
    const sanitizedObj: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
      const lowerKey = key.toLowerCase();
      if (FORBIDDEN_CREDENTIAL_FIELDS.some((forbidden) => lowerKey.includes(forbidden))) {
        sanitizedObj[key] = '[REDACTED_CONFIDENTIAL]';
      } else {
        sanitizedObj[key] = sanitizeDataForRendering(value);
      }
    }
    return sanitizedObj as unknown as T;
  }
  return data;
}

/**
 * Returns human-readable semantic explanation for Engine 5 evidence states
 */
export function getEvidenceStatusExplanation(status: EvidenceStatus | string): string {
  switch (status) {
    case 'SUPPORTED':
      return 'Authoritative filings and regulatory registries verify this assertion.';
    case 'PARTIALLY_SUPPORTED':
      return 'Retrieved records corroborate portions of this claim, with minor discrepancies.';
    case 'CONTRADICTED':
      return 'Authoritative official records directly contradict this assertion.';
    case 'INSUFFICIENT_EVIDENCE':
      return 'Available sources did not provide sufficient evidence to establish this claim.';
    case 'NOT_VERIFIABLE':
      return 'Assertion contains subjective predictions or unquantifiable promises not subject to empirical verification.';
    case 'SOURCE_CONFLICT':
      return 'Multiple authoritative sources provided conflicting records.';
    case 'SOURCE_UNAVAILABLE':
      return 'Authoritative regulatory registry was temporarily unreachable or unindexed.';
    case 'NOT_ESTABLISHED':
    default:
      return 'Evidence verification could not establish conclusive findings with available sources.';
  }
}

/**
 * Derives structured Subject-Predicate-Object models from claims
 */
export function deriveClaimSPO(claims: FirewallClaimSummary[]): ClaimSPOModel[] {
  return claims.map((claim) => {
    let subject = 'Unspecified Subject';
    let predicate = claim.predicate || 'ASSERTION';
    let object = 'Unspecified Target';

    // Parse simple patterns if predicate suggests SPO
    const words = claim.text.split(' ');
    if (words.length >= 3) {
      subject = words.slice(0, 2).join(' ');
      object = words.slice(2).join(' ');
    } else {
      subject = claim.topic || 'Financial Entity';
      object = claim.text;
    }

    return {
      claimId: claim.claim_id,
      rawText: claim.text,
      subject,
      predicate,
      object,
      modality: claim.modality || 'statement',
      topic: claim.topic || 'CLAIM',
      verificationStatus: (claim.verification_status as EvidenceStatus) || 'INSUFFICIENT_EVIDENCE',
      statusExplanation: getEvidenceStatusExplanation(claim.verification_status || 'INSUFFICIENT_EVIDENCE'),
      verificationRequirement: `Verify ${predicate.toLowerCase().replace(/_/g, ' ')} assertion against official filings`,
    };
  });
}

/**
 * Derives the 5-level action progression hierarchy from detected actions
 */
export function deriveActionHierarchy(actions: FirewallActionSummary[]): ActionHierarchyStage[] {
  const levels: ActionHierarchyStage[] = [
    {
      level: 1,
      name: 'Informational',
      categoryKey: 'INFORMATIONAL',
      description: 'Educational content, market commentary, or public discussion.',
      isDetected: false,
      actions: [],
    },
    {
      level: 2,
      name: 'Communication',
      categoryKey: 'COMMUNICATION',
      description: 'Direct messaging, contact initiation, or social following.',
      isDetected: false,
      actions: [],
    },
    {
      level: 3,
      name: 'Private Channel',
      categoryKey: 'PRIVATE_CHANNEL',
      description: 'Migration to off-platform groups (Telegram, WhatsApp, Discord).',
      isDetected: false,
      actions: [],
    },
    {
      level: 4,
      name: 'External Software',
      categoryKey: 'EXTERNAL_APPLICATION',
      description: 'Installing APKs, trading apps, or screen-sharing tools.',
      isDetected: false,
      actions: [],
    },
    {
      level: 5,
      name: 'Extraction / Payment',
      categoryKey: 'FINANCIAL_TRANSACTION',
      description: 'Transferring funds, crypto deposits, or sharing credentials.',
      isDetected: false,
      actions: [],
    },
  ];

  for (const act of actions) {
    const actType = act.action_type.toUpperCase();
    const impact = act.impact_category.toUpperCase();

    if (actType.includes('PAY') || actType.includes('TRANSFER') || impact.includes('FINANCIAL') || impact.includes('CREDENTIAL')) {
      levels[4].isDetected = true;
      levels[4].actions.push(act);
    } else if (actType.includes('DOWNLOAD') || actType.includes('APP') || actType.includes('INSTALL') || impact.includes('APPLICATION')) {
      levels[3].isDetected = true;
      levels[3].actions.push(act);
    } else if (actType.includes('CHANNEL') || actType.includes('TELEGRAM') || actType.includes('WHATSAPP') || actType.includes('GROUP')) {
      levels[2].isDetected = true;
      levels[2].actions.push(act);
    } else if (actType.includes('CONTACT') || actType.includes('MESSAGE') || impact.includes('COMMUNICATION')) {
      levels[1].isDetected = true;
      levels[1].actions.push(act);
    } else {
      levels[0].isDetected = true;
      levels[0].actions.push(act);
    }
  }

  return levels;
}

/**
 * Derives attack path stages from Engine 6 output
 */
export function deriveAttackPathNodes(analysis: FirewallAnalysisResponse): AttackPathNode[] {
  const { threat, actions, claims } = analysis;
  const nodes: AttackPathNode[] = [];

  const defaultStages = [
    { key: 'TRUST_BUILDING', label: 'Trust Building' },
    { key: 'CHANNEL_MIGRATION', label: 'Channel Migration' },
    { key: 'SOFTWARE_INSTALLATION', label: 'External Application' },
    { key: 'FINANCIAL_EXTRACTION', label: 'Financial Request' },
  ];

  for (let i = 0; i < defaultStages.length; i++) {
    const stage = defaultStages[i];
    let isDetected = false;
    let associatedAction: string | undefined;
    let associatedClaim: string | undefined;
    let supportingSignal: string | undefined;

    if (stage.key === 'TRUST_BUILDING') {
      isDetected = claims.length > 0 || threat.threat_signals.some((s) => s.includes('AUTHORITY') || s.includes('RETURN'));
      associatedClaim = claims[0]?.text;
      supportingSignal = threat.threat_signals.find((s) => s.includes('AUTHORITY'));
    } else if (stage.key === 'CHANNEL_MIGRATION') {
      isDetected =
        actions.some((a) => a.action_type.includes('CHANNEL') || a.action_type.includes('MIGRAT')) ||
        threat.threat_signals.some((s) => s.includes('MIGRATION') || s.includes('CHANNEL'));
      associatedAction = actions.find((a) => a.action_type.includes('CHANNEL'))?.target;
      supportingSignal = threat.threat_signals.find((s) => s.includes('MIGRATION'));
    } else if (stage.key === 'SOFTWARE_INSTALLATION') {
      isDetected =
        actions.some((a) => a.action_type.includes('DOWNLOAD') || a.action_type.includes('APP') || a.action_type.includes('INSTALL')) ||
        threat.threat_signals.some((s) => s.includes('APP') || s.includes('SOFTWARE'));
      associatedAction = actions.find((a) => a.action_type.includes('DOWNLOAD') || a.action_type.includes('APP'))?.target;
      supportingSignal = threat.threat_signals.find((s) => s.includes('SOFTWARE'));
    } else if (stage.key === 'FINANCIAL_EXTRACTION') {
      isDetected =
        actions.some((a) => a.impact_category === 'FINANCIAL_TRANSACTION' || a.action_type.includes('PAY') || a.action_type.includes('TRANSFER')) ||
        threat.threat_signals.some((s) => s.includes('PAY') || s.includes('EXTRACTION'));
      associatedAction = actions.find((a) => a.impact_category === 'FINANCIAL_TRANSACTION')?.target;
      supportingSignal = threat.threat_signals.find((s) => s.includes('EXTRACTION'));
    }

    nodes.push({
      id: `stage-${i}`,
      stageName: stage.label,
      stageKey: stage.key,
      isTerminal: i === defaultStages.length - 1,
      status: isDetected ? 'active' : 'potential',
      associatedAction,
      associatedClaim,
      supportingSignal,
    });
  }

  return nodes;
}

/**
 * Derives combined chronological timeline from all multi-engine signals
 */
export function deriveCombinedTimeline(analysis: FirewallAnalysisResponse): BehaviourTimelineEvent[] {
  const events: BehaviourTimelineEvent[] = [];
  const baseTime = analysis.created_at ? new Date(analysis.created_at) : new Date();

  // 1. Content View Event
  events.push({
    id: 'evt-content-view',
    timestamp: new Date(baseTime.getTime() - 180000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    eventType: 'CONTENT_VIEW',
    title: 'Content Ingestion & View',
    description: `Financial content observed via channel: ${analysis.content.channel || 'web'}.`,
    category: 'content',
  });

  // 2. Off-platform migration if detected
  if (analysis.behaviour.channel_migration_detected || analysis.actions.some((a) => a.action_type.includes('CHANNEL'))) {
    events.push({
      id: 'evt-channel-shift',
      timestamp: new Date(baseTime.getTime() - 120000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      eventType: 'CHANNEL_CHANGED',
      title: 'Channel Migration Shift',
      description: 'Interaction directed towards private group / unmonitored messaging channel.',
      category: 'action',
      isEscalation: true,
    });
  }

  // 3. External application if requested
  const appAction = analysis.actions.find((a) => a.action_type.includes('DOWNLOAD') || a.action_type.includes('APP'));
  if (appAction) {
    events.push({
      id: 'evt-app-requested',
      timestamp: new Date(baseTime.getTime() - 60000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      eventType: 'EXTERNAL_APP_REQUESTED',
      title: 'External Application Requested',
      description: `Target application: ${appAction.target || 'External Package'} (${appAction.reversibility}).`,
      category: 'action',
      isEscalation: true,
    });
  }

  // 4. Financial extraction request
  const finAction = analysis.actions.find((a) => a.impact_category === 'FINANCIAL_TRANSACTION' || a.action_type.includes('PAY'));
  if (finAction) {
    events.push({
      id: 'evt-payment-requested',
      timestamp: new Date(baseTime.getTime() - 30000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      eventType: 'PAYMENT_REQUESTED',
      title: 'Payment / Capital Transfer Requested',
      description: `Action: ${finAction.action_type.replace(/_/g, ' ')} (${finAction.reversibility}).`,
      category: 'action',
      isEscalation: true,
    });
  }

  // 5. Time pressure or urgency
  if (analysis.behaviour.time_pressure_detected || analysis.actions.some((a) => a.urgency_detected)) {
    events.push({
      id: 'evt-time-pressure',
      timestamp: new Date(baseTime.getTime() - 10000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      eventType: 'TIME_PRESSURE',
      title: 'Temporal Urgency Detected',
      description: 'Artificial urgency or deadline pressure introduced into interaction sequence.',
      category: 'behaviour',
      isEscalation: true,
    });
  }

  // 6. User responses from findings if present
  for (let i = 0; i < analysis.behaviour.findings.length; i++) {
    const f = analysis.behaviour.findings[i];
    if (f.toLowerCase().includes('decline') || f.toLowerCase().includes('retry')) {
      events.push({
        id: `evt-user-resp-${i}`,
        timestamp: new Date(baseTime.getTime() - 5000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        eventType: 'RETRY_AFTER_DECLINE',
        title: 'Interaction Escalation Pattern',
        description: f,
        category: 'user',
      });
    }
  }

  // 7. Policy Intervention Event
  events.push({
    id: 'evt-policy-decision',
    timestamp: baseTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    eventType: 'POLICY_INTERVENTION',
    title: `Policy Decision: ${analysis.decision.decision}`,
    description: analysis.decision.explanation.primary_reason,
    category: 'policy',
  });

  return events;
}

/**
 * Derives fingerprint dimension indicators
 */
export function deriveFingerprintDimensions(analysis: FirewallAnalysisResponse): FingerprintDimensionItem[] {
  const { fingerprint, threat, actions, claims } = analysis;
  const isMatch = fingerprint.match_type !== 'NO_MATCH';

  return [
    {
      name: 'Authority Claim Pattern',
      category: 'Claim Structure',
      matched: isMatch && claims.some((c) => c.topic.includes('REGULATORY') || c.topic.includes('AUTHORITY') || c.predicate.includes('REGISTERED')),
      detail: 'Claims regulatory registration or institutional authority.',
    },
    {
      name: 'Private Channel Migration',
      category: 'Channel Structure',
      matched: isMatch && (actions.some((a) => a.action_type.includes('CHANNEL')) || threat.threat_signals.some((s) => s.includes('MIGRATION'))),
      detail: 'Directs interaction away from monitored platform to private messenger.',
    },
    {
      name: 'External Application',
      category: 'Technical Structure',
      matched: isMatch && actions.some((a) => a.action_type.includes('DOWNLOAD') || a.action_type.includes('APP')),
      detail: 'Requires installing proprietary or unverified package/software.',
    },
    {
      name: 'Urgent Extraction / Payment',
      category: 'Action Structure',
      matched: isMatch && actions.some((a) => a.impact_category === 'FINANCIAL_TRANSACTION' || a.action_type.includes('PAY')),
      detail: 'Requests immediate transfer, deposit, or sensitive credential disclosure.',
    },
    {
      name: 'Temporal Pressure / Coercion',
      category: 'Behavioural Structure',
      matched: isMatch && (analysis.behaviour.time_pressure_detected || actions.some((a) => a.urgency_detected)),
      detail: 'Artificial countdown, scarcity, or expedited deadline.',
    },
  ];
}
