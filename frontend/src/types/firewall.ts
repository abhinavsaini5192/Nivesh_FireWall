/**
 * Canonical Frontend Data Types for Nivesh Firewall (Phase 12.1)
 * Strictly aligned with Phase 11.4 Unified Firewall API contracts.
 */

export type PolicyDecisionType = 'ALLOW' | 'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK';

export type PolicySeverity = 'NONE' | 'INFORMATIONAL' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type ChannelType =
  | 'web'
  | 'browser'
  | 'telegram'
  | 'whatsapp'
  | 'instagram'
  | 'youtube'
  | 'email'
  | 'sms'
  | 'unknown';

export type InputType = 'text' | 'url' | 'image';

export type PipelineStatus = 'COMPLETED' | 'DEGRADED' | 'PARTIAL' | 'FAILED' | 'CANCELLED';

export type AnalysisState =
  | 'IDLE'
  | 'VALIDATING'
  | 'SUBMITTING'
  | 'ANALYZING'
  | 'SUCCESS'
  | 'ERROR'
  | 'PARTIAL_RESULT';

export type EvidenceStatus =
  | 'SUPPORTED'
  | 'PARTIALLY_SUPPORTED'
  | 'CONTRADICTED'
  | 'INSUFFICIENT_EVIDENCE'
  | 'NOT_VERIFIABLE'
  | 'SOURCE_CONFLICT'
  | 'SOURCE_UNAVAILABLE'
  | 'NOT_ESTABLISHED';

export type IdentityStatus =
  | 'ESTABLISHED'
  | 'PARTIALLY_ESTABLISHED'
  | 'NOT_ESTABLISHED'
  | 'IDENTITY_MISMATCH'
  | 'AMBIGUOUS'
  | 'INSUFFICIENT_EVIDENCE'
  | 'SOURCE_UNAVAILABLE';

export type FingerprintMatchType =
  | 'EXACT_MATCH'
  | 'SEMANTIC_VARIANT'
  | 'STRUCTURAL_MATCH'
  | 'NO_MATCH';

export interface FirewallAnalyzeRequest {
  input_type: InputType;
  text?: string;
  url?: string;
  image_base64?: string;
  session_id?: string;
  channel?: ChannelType | string;
  metadata?: Record<string, unknown>;
  idempotency_key?: string;
}

export interface FirewallExplanation {
  decision: PolicyDecisionType | string;
  user_message: string;
  technical_message: string;
  primary_reason: string;
  supporting_signals: string[];
}

export interface FirewallDecisionSummary {
  decision: PolicyDecisionType;
  severity: PolicySeverity;
  primary_reason: string;
  reason_codes: string[];
  explanation: FirewallExplanation;
  actions_required: string[];
  required_user_confirmation: boolean;
  cooldown_seconds?: number;
  policy_version: string;
  decision_id?: string;
}

export interface FirewallContentSummary {
  content_id: string;
  input_type: string;
  channel: string;
  summary: string;
  contains_financial_content: boolean;
  language?: string;
  language_confidence?: number;
  entities: Record<string, string[]>;
}

export interface FirewallClaimSummary {
  claim_id: string;
  text: string;
  topic: string;
  predicate: string;
  modality: string;
  verification_status?: string;
}

export interface FirewallActionSummary {
  action_id: string;
  action_type: string;
  target?: string;
  impact_category: string;
  reversibility: string;
  urgency_detected: boolean;
}

export interface FirewallEvidenceSummary {
  overall_status: EvidenceStatus | string;
  verification_count: number;
  supported_claims_count: number;
  contradicted_claims_count: number;
  insufficient_claims_count: number;
  source_documents_count: number;
  retrieval_status: string;
}

export interface FirewallIdentitySummary {
  identity_status: IdentityStatus | string;
  claimed_entities: string[];
  findings_count: number;
  findings_summary: string[];
  confidence: number;
}

export interface FirewallThreatSummary {
  threat_signals: string[];
  attack_stage?: string;
  terminal_stage?: string;
  threat_families: string[];
  high_impact_action_count: number;
  confidence: number;
}

export interface FirewallFingerprintSummary {
  match_type: FingerprintMatchType | string;
  fingerprint_id?: string;
  match_confidence: number;
  observation_count: number;
  distinct_channels_count: number;
  attack_path_signature?: string;
}

export interface FirewallBehaviourSummary {
  signals: string[];
  findings: string[];
  session_id?: string;
  events_in_session: number;
  time_pressure_detected: boolean;
  rapid_escalation_detected: boolean;
  channel_migration_detected: boolean;
}

export interface FirewallAnalysisResponse {
  analysis_id: string;
  session_id?: string;
  pipeline_status: PipelineStatus | string;
  created_at: string;
  completed_at?: string;
  duration_ms: number;
  decision: FirewallDecisionSummary;
  content: FirewallContentSummary;
  claims: FirewallClaimSummary[];
  actions: FirewallActionSummary[];
  evidence: FirewallEvidenceSummary;
  identity: FirewallIdentitySummary;
  threat: FirewallThreatSummary;
  fingerprint: FirewallFingerprintSummary;
  behaviour: FirewallBehaviourSummary;
  provenance: Record<string, unknown>;
  warnings: string[];
  errors: string[];
}

export interface FirewallApiError {
  error_code:
    | 'INVALID_REQUEST'
    | 'UNSUPPORTED_INPUT'
    | 'INPUT_TOO_LARGE'
    | 'INVALID_URL'
    | 'INVALID_SESSION'
    | 'ANALYSIS_NOT_FOUND'
    | 'PIPELINE_FAILURE'
    | string;
  message: string;
  analysis_id?: string;
  details?: Record<string, unknown>;
}

export type ProtectionSystemStatus = 'active' | 'connecting' | 'unavailable' | 'error';

/**
 * Maps canonical backend error codes to product-level user messages (Phase 12.5 Section 19)
 */
export function mapBackendErrorToUserMessage(errorCode: string, fallbackMessage?: string): string {
  switch (errorCode) {
    case 'INVALID_REQUEST':
      return 'Check the submitted content.';
    case 'UNSUPPORTED_INPUT':
      return 'This type of content is not currently supported.';
    case 'SERVICE_UNAVAILABLE':
      return 'Nivesh protection service is temporarily unavailable.';
    case 'PIPELINE_FAILURE':
      return "We couldn't complete this analysis.";
    case 'ANALYSIS_NOT_FOUND':
      return 'This analysis is no longer available.';
    default:
      return fallbackMessage || "We couldn't complete this analysis.";
  }
}
