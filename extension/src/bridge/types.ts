/**
 * Bridge Type Definitions (Phase 13.3 Sections 2, 3, 12, 13, 14, 24)
 *
 * Defines the canonical request model, response preservation contracts,
 * and error mappings for the Nivesh Analysis Bridge.
 */

import type { CaptureSourceType } from '../types/capture';
import type { LastAnalysisReference } from '../types/state';

/**
 * Canonical Browser-to-Backend Bridge Request Model (Section 3)
 */
export interface BrowserAnalysisRequest {
  captureId: string;
  requestId: string;
  sessionId?: string;
  sourceType: CaptureSourceType;
  text?: string;
  url?: string;
  pageOrigin?: string;
  pageTitle?: string;
  tabId?: number;
  timestamp: string;
}

/**
 * Canonical Engine 8 Policy Decision from Backend
 */
export type Engine8PolicyDecision = 'ALLOW' | 'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK';

/**
 * Full Preserved Backend Response (Section 12 & 13)
 */
export interface FirewallExplanation {
  decision: string;
  user_message: string;
  technical_message: string;
  primary_reason: string;
  supporting_signals: string[];
}

export interface FirewallDecisionSummary {
  decision: Engine8PolicyDecision | string;
  severity: string;
  primary_reason: string;
  reason_codes: string[];
  explanation: FirewallExplanation;
  actions_required: string[];
  required_user_confirmation: boolean;
  cooldown_seconds?: number | null;
  policy_version: string;
  decision_id?: string | null;
}

export interface FirewallContentSummary {
  content_id: string;
  input_type: string;
  channel: string;
  summary: string;
  contains_financial_content: boolean;
  language?: string | null;
  language_confidence?: number | null;
  entities: Record<string, string[]>;
}

export interface FirewallClaimSummary {
  claim_id: string;
  text: string;
  topic: string;
  predicate: string;
  modality: string;
  verification_status?: string | null;
}

export interface FirewallActionSummary {
  action_id: string;
  action_type: string;
  target?: string | null;
  impact_category: string;
  reversibility: string;
  urgency_detected: boolean;
}

export interface FirewallEvidenceSummary {
  overall_status: string; // SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE, SOURCE_UNAVAILABLE, NOT_ESTABLISHED
  verification_count: number;
  supported_claims_count: number;
  contradicted_claims_count: number;
  insufficient_claims_count: number;
  source_documents_count: number;
  retrieval_status: string;
}

export interface FirewallIdentitySummary {
  identity_status: string; // ESTABLISHED, NOT_ESTABLISHED, IDENTITY_MISMATCH, AMBIGUOUS
  claimed_entities: string[];
  findings_count: number;
  findings_summary: string[];
  confidence: number;
}

export interface FirewallThreatSummary {
  threat_signals: string[];
  attack_stage?: string | null;
  terminal_stage?: string | null;
  threat_families: string[];
  high_impact_action_count: number;
  confidence: number;
}

export interface FirewallFingerprintSummary {
  match_type: string; // EXACT_MATCH, SEMANTIC_VARIANT, STRUCTURAL_MATCH, NO_MATCH
  fingerprint_id?: string | null;
  match_confidence: number;
  observation_count: number;
  distinct_channels_count: number;
  attack_path_signature?: string | null;
}

export interface FirewallBehaviourSummary {
  signals: string[];
  findings: string[];
  session_id?: string | null;
  events_in_session: number;
  time_pressure_detected: boolean;
  rapid_escalation_detected: boolean;
  channel_migration_detected: boolean;
}

export interface FirewallAnalysisResponse {
  analysis_id: string;
  session_id?: string | null;
  pipeline_status: string;
  created_at: string;
  completed_at?: string | null;
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

export interface BridgeAnalysisResult {
  analysisId: string;
  captureId: string;
  requestId: string;
  reference: LastAnalysisReference;
  fullResponse: FirewallAnalysisResponse;
  retriesAttempted: number;
  durationMs: number;
}

/**
 * Standard Bridge Error Codes (Section 24)
 */
export type BridgeErrorCode =
  | 'INVALID_REQUEST'
  | 'UNSUPPORTED_INPUT'
  | 'INPUT_TOO_LARGE'
  | 'BACKEND_UNAVAILABLE'
  | 'BACKEND_TIMEOUT'
  | 'ANALYSIS_NOT_FOUND'
  | 'PIPELINE_FAILURE'
  | 'PERMISSION_DENIED'
  | 'MALFORMED_RESPONSE'
  | 'SCAN_IN_PROGRESS';
