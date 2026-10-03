/**
 * Tests for Phase 12.4: Intelligence, Evidence & Timeline Views
 * Validates all Section 36, 37, and 38 requirements.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { FirewallAnalysisResponse } from '../types/firewall';
import { AnalysisResultView } from '../components/firewall/AnalysisResultView';
import {
  ActionHierarchyCard,
  ClaimEvidenceDetailCard,
  EntityRelationshipGraph,
  AttackPathVisualizer,
  FingerprintIntelligenceCard,
  BehaviourTimelineView,
  PolicyReasonTraceView,
  PrivacySafeguardNotice,
  UserExecutiveSummaryCard,
  IntelligenceDetailView,
  ClaimsCard,
} from '../components/intelligence';
import { sanitizeDataForRendering } from '../types/intelligence';

// Factory for mock response
const createMockAnalysis = (overrides?: Partial<FirewallAnalysisResponse>): FirewallAnalysisResponse => ({
  analysis_id: 'ORCH-INTEL-TEST-001',
  session_id: 'SESSION-INTEL-445',
  pipeline_status: 'COMPLETED',
  created_at: '2026-10-03T10:00:00Z',
  completed_at: '2026-10-03T10:00:01Z',
  duration_ms: 125.4,
  decision: {
    decision: 'PAUSE',
    severity: 'HIGH',
    primary_reason: 'High-impact extraction combined with unverified identity and rapid escalation.',
    reason_codes: ['URGENT_FINANCIAL_EXTRACTION', 'UNVERIFIED_AUTHORITY_CLAIM', 'RAPID_ESCALATION'],
    explanation: {
      decision: 'PAUSE',
      user_message: 'Nivesh identified multiple signals requiring independent verification before proceeding.',
      technical_message: 'High impact action detected with unverified authority claims.',
      primary_reason: 'High-impact extraction combined with unverified identity.',
      supporting_signals: ['TELEGRAM_MIGRATION', 'UNVERIFIED_SEBI_CLAIM', 'TIME_PRESSURE'],
    },
    actions_required: ['PAUSE_ACTION', 'USER_CONFIRMATION_REQUIRED'],
    required_user_confirmation: true,
    cooldown_seconds: 300,
    policy_version: '8.0.0',
    decision_id: 'DEC-001',
  },
  content: {
    content_id: 'CNT-001',
    input_type: 'text',
    channel: 'telegram',
    summary: 'Join VIP group for 40% returns, download our terminal and transfer fees.',
    contains_financial_content: true,
    entities: {
      people: ['Rahul Sharma'],
      organizations: ['Alpha Wealth Advisors'],
      regulators: ['SEBI'],
      financial_instruments: ['Equities'],
    },
  },
  claims: [
    {
      claim_id: 'CLM-001',
      text: 'Rahul Sharma is SEBI registered research analyst',
      topic: 'REGULATORY_AUTHORITY',
      predicate: 'REGISTERED_WITH',
      modality: 'statement',
      verification_status: 'CONTRADICTED',
    },
    {
      claim_id: 'CLM-002',
      text: 'Guaranteed 40% monthly returns on all trades',
      topic: 'GUARANTEED_RETURNS',
      predicate: 'PROMISES_RETURN',
      modality: 'prediction',
      verification_status: 'INSUFFICIENT_EVIDENCE',
    },
  ],
  actions: [
    {
      action_id: 'ACT-001',
      action_type: 'DOWNLOAD',
      target: 'custom_trading.apk',
      impact_category: 'APPLICATION_INSTALLATION',
      reversibility: 'DIFFICULT',
      urgency_detected: false,
    },
    {
      action_id: 'ACT-002',
      action_type: 'TRANSFER_MONEY',
      target: 'vip_desk@upi',
      impact_category: 'FINANCIAL_TRANSACTION',
      reversibility: 'IRREVERSIBLE',
      urgency_detected: true,
    },
  ],
  evidence: {
    overall_status: 'CONTRADICTED',
    verification_count: 2,
    supported_claims_count: 0,
    contradicted_claims_count: 1,
    insufficient_claims_count: 1,
    source_documents_count: 3,
    retrieval_status: 'COMPLETED',
  },
  identity: {
    identity_status: 'IDENTITY_MISMATCH',
    claimed_entities: ['Rahul Sharma', 'Alpha Wealth Advisors'],
    findings_count: 2,
    findings_summary: [
      'Registration number does not align with claimed entity in official SEBI database.',
      'Domain lookup does not match official registered website.',
    ],
    confidence: 0.12,
  },
  threat: {
    threat_signals: ['CHANNEL_MIGRATION', 'SOFTWARE_INSTALLATION', 'FINANCIAL_EXTRACTION'],
    attack_stage: 'TRUST_BUILDING',
    terminal_stage: 'FINANCIAL_EXTRACTION',
    threat_families: ['OFF_MARKET_TRADING_SCHEME'],
    high_impact_action_count: 1,
    confidence: 0.89,
  },
  fingerprint: {
    match_type: 'SEMANTIC_VARIANT',
    fingerprint_id: 'FP-VIP-TELEGRAM-01',
    match_confidence: 0.88,
    observation_count: 42,
    distinct_channels_count: 3,
    attack_path_signature: 'TELEGRAM->APK->UPI',
  },
  behaviour: {
    signals: ['RAPID_ESCALATION', 'TIME_PRESSURE', 'CHANNEL_MIGRATION'],
    findings: [
      'Rapid progression from informational query to transfer request.',
      'Urgency language observed with artificial countdown.',
      'Payment request repeated after initial hesitation.',
    ],
    session_id: 'SESSION-INTEL-445',
    events_in_session: 5,
    time_pressure_detected: true,
    rapid_escalation_detected: true,
    channel_migration_detected: true,
  },
  provenance: {
    engine_lineage: ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E9', 'E10', 'E8'],
    source_mode: 'LIVE',
    sanitized: true,
  },
  warnings: [],
  errors: [],
  ...overrides,
});

describe('Phase 12.4 — Detailed Intelligence, Evidence & Timeline Views', () => {
  // 1. Claims View
  describe('1. Claim Intelligence View (Engine 2 & 5)', () => {
    it('renders canonical claims with Subject-Predicate-Object decomposition', () => {
      const mock = createMockAnalysis();
      render(<ClaimsCard claims={mock.claims} />);

      expect(screen.getByText('"Rahul Sharma is SEBI registered research analyst"')).toBeInTheDocument();
      expect(screen.getByText('"Guaranteed 40% monthly returns on all trades"')).toBeInTheDocument();
      expect(screen.getByText('REGISTERED_WITH')).toBeInTheDocument();
      expect(screen.getByText('PROMISES_RETURN')).toBeInTheDocument();
    });

    it('keeps evidence verification statuses distinct without collapsing negative states into fake', () => {
      const mock = createMockAnalysis();
      render(<ClaimsCard claims={mock.claims} />);

      // CONTRADICTED and INSUFFICIENT_EVIDENCE must both be clearly shown
      expect(screen.getAllByText('CONTRADICTED').length).toBeGreaterThan(0);
      expect(screen.getAllByText('INSUFFICIENT_EVIDENCE').length).toBeGreaterThan(0);
      expect(screen.getByText(/Available sources did not provide sufficient evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/Authoritative official records directly contradict/i)).toBeInTheDocument();
    });
  });

  // 2. Action Hierarchy View
  describe('2. Action Hierarchy View (Engine 3)', () => {
    it('renders requested actions with progression scale and reversibility rating', () => {
      const mock = createMockAnalysis();
      render(<ActionHierarchyCard actions={mock.actions} />);

      expect(screen.getByText('Action Progression Hierarchy')).toBeInTheDocument();
      expect(screen.getByText('Level 1')).toBeInTheDocument();
      expect(screen.getByText('Level 5')).toBeInTheDocument();
      expect(screen.getByText('DOWNLOAD')).toBeInTheDocument();
      expect(screen.getByText('TRANSFER_MONEY')).toBeInTheDocument();
      expect(screen.getByText('IRREVERSIBLE')).toBeInTheDocument();
      expect(screen.getByText('Urgency Detected')).toBeInTheDocument();
    });
  });

  // 3. Evidence View
  describe('3. Evidence Verification View (Engine 4 & 5)', () => {
    it('displays evidence metrics with correct source filings count', () => {
      const mock = createMockAnalysis();
      render(<ClaimEvidenceDetailCard evidence={mock.evidence} sourceMode="COMPLETED" />);

      expect(screen.getByText('Authoritative Registry & Evidence Verification')).toBeInTheDocument();
      expect(screen.getByText('Supported Claims')).toBeInTheDocument();
      expect(screen.getByText('Contradicted Claims')).toBeInTheDocument();
      expect(screen.getByText('Insufficient Evidence')).toBeInTheDocument();
      expect(screen.getByText('Source Filings Retrieved')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument(); // source documents count
    });
  });

  // 4. Identity Verification View
  describe('4. Entity Identity Resolution View (Engine 9)', () => {
    it('renders IDENTITY_MISMATCH objectively without calling anyone a scammer', () => {
      const mock = createMockAnalysis();
      render(<EntityRelationshipGraph identity={mock.identity} />);

      expect(screen.getByText('Entity Identity Resolution')).toBeInTheDocument();
      expect(screen.getAllByText('IDENTITY_MISMATCH').length).toBeGreaterThan(0);
      expect(screen.getByText('SEBI / Registered Directory')).toBeInTheDocument();
      expect(screen.getByText(/Registration number does not align with claimed entity/i)).toBeInTheDocument();

      // Ensure non-accusatory language
      const bodyText = document.body.textContent?.toLowerCase() || '';
      expect(bodyText).not.toContain('fake person');
      expect(bodyText).not.toContain('scammer');
    });

    it('handles ESTABLISHED and NOT_ESTABLISHED statuses faithfully', () => {
      const mockEstablished = createMockAnalysis({
        identity: {
          identity_status: 'ESTABLISHED',
          claimed_entities: ['HDFC Securities'],
          findings_count: 1,
          findings_summary: ['Registration verified with active SEBI license.'],
          confidence: 0.98,
        },
      });

      render(<EntityRelationshipGraph identity={mockEstablished.identity} />);
      expect(screen.getAllByText('ESTABLISHED').length).toBeGreaterThan(0);
      expect(screen.getByText('HDFC Securities')).toBeInTheDocument();
      expect(screen.getByText(/Registration verified with active SEBI license/i)).toBeInTheDocument();
    });
  });

  // 5. Threat Summary & Attack Path View
  describe('5. Threat Attack-Path Visualizer (Engine 6)', () => {
    it('renders sequential progression stages and claim-action relationship', () => {
      const mock = createMockAnalysis();
      render(<AttackPathVisualizer analysis={mock} />);

      expect(screen.getByText('Sequential Attack-Path Stages')).toBeInTheDocument();
      expect(screen.getByText('TRUST_BUILDING → FINANCIAL_EXTRACTION')).toBeInTheDocument();
      expect(screen.getByText('Trust Building')).toBeInTheDocument();
      expect(screen.getByText('Channel Migration')).toBeInTheDocument();
      expect(screen.getByText('External Application')).toBeInTheDocument();
      expect(screen.getByText('Financial Request')).toBeInTheDocument();

      // Claim -> Action linkage
      expect(screen.getByText(/Claim → Action Linkage/i)).toBeInTheDocument();
      expect(screen.getByText(/Rationale: Rahul Sharma is SEBI registered research analyst/i)).toBeInTheDocument();
      expect(screen.getByText(/Target Action: DOWNLOAD/i)).toBeInTheDocument();
    });

    it('has an accessible linear textual representation for screen readers', () => {
      const mock = createMockAnalysis();
      render(<AttackPathVisualizer analysis={mock} />);

      const srElement = document.querySelector('.sr-only');
      expect(srElement).toBeInTheDocument();
      expect(srElement?.textContent).toContain('Attack Path Progression');
    });
  });

  // 6. Fingerprint Intelligence View
  describe('6. Scam Fingerprint Intelligence (Engine 7)', () => {
    it('renders SEMANTIC_VARIANT and structural equivalence independently', () => {
      const mock = createMockAnalysis();
      render(<FingerprintIntelligenceCard analysis={mock} />);

      expect(screen.getByText('Structural Match Blueprint & Dimensions')).toBeInTheDocument();
      expect(screen.getAllByText('SEMANTIC_VARIANT').length).toBeGreaterThan(0);
      expect(screen.getByText('YES (Known Template Structure)')).toBeInTheDocument();
      expect(screen.getByText(/42 sightings across 3 channels/i)).toBeInTheDocument();
    });

    it('handles NO_MATCH without stating that no match equals safe', () => {
      const mockNoMatch = createMockAnalysis({
        fingerprint: {
          match_type: 'NO_MATCH',
          fingerprint_id: undefined,
          match_confidence: 0.0,
          observation_count: 0,
          distinct_channels_count: 0,
        },
      });

      render(<FingerprintIntelligenceCard analysis={mockNoMatch} />);
      expect(screen.getAllByText('NO_MATCH').length).toBeGreaterThan(0);
      expect(screen.getByText('NO')).toBeInTheDocument();
      expect(screen.getByText(/0 matching sightings recorded/i)).toBeInTheDocument();

      // Ensure "no match = safe" is not claimed
      const bodyText = document.body.textContent || '';
      expect(bodyText).not.toContain('No match = safe');
    });
  });

  // 7. Behaviour Timeline View
  describe('7. Behavioural Signal Intelligence & Timeline (Engine 10)', () => {
    it('renders chronological timeline and pattern confidence without scam probabilities', () => {
      const mock = createMockAnalysis();
      render(<BehaviourTimelineView analysis={mock} />);

      expect(screen.getByText('Observed Interaction Dynamics & Timeline')).toBeInTheDocument();
      expect(screen.getByText('Content Ingestion & View')).toBeInTheDocument();
      expect(screen.getByText('Channel Migration Shift')).toBeInTheDocument();
      expect(screen.getByText('Payment / Capital Transfer Requested')).toBeInTheDocument();
      expect(screen.getByText('Temporal Urgency Detected')).toBeInTheDocument();
      expect(screen.getByText(/Interaction Pattern Confidence/i)).toBeInTheDocument();

      // Ensure no psychological labels or scam confidence
      const bodyText = document.body.textContent?.toLowerCase() || '';
      expect(bodyText).not.toContain('user was impulsive');
      expect(bodyText).not.toContain('scam probability');
      expect(bodyText).not.toContain('fraud probability');
    });
  });

  // 8. Policy Reason Trace View
  describe('8. Policy Reason Trace View (Engine 8)', () => {
    it('traces multi-engine signals to Engine 8 deterministic policy decision', () => {
      const mock = createMockAnalysis();
      render(<PolicyReasonTraceView analysis={mock} />);

      expect(screen.getByText('Engine 8 Policy Reason Trace')).toBeInTheDocument();
      expect(screen.getByText('Engine 9 (Identity)')).toBeInTheDocument();
      expect(screen.getByText('Engine 3 (Action)')).toBeInTheDocument();
      expect(screen.getByText('Engine 6 (Threat)')).toBeInTheDocument();
      expect(screen.getByText('Engine 10 (Behaviour)')).toBeInTheDocument();
      expect(screen.getByText('Engine 5 (Evidence)')).toBeInTheDocument();
      expect(screen.getByText('URGENT_FINANCIAL_EXTRACTION')).toBeInTheDocument();
      expect(screen.getByText('Intervention: PAUSE')).toBeInTheDocument();
    });
  });

  // 9. User Executive Summary Mode
  describe('9. Executive Summary Mode (Plain English)', () => {
    it('renders 5 clear questions and answers for everyday users', async () => {
      const mock = createMockAnalysis();
      const exploreFn = vi.fn();
      render(<UserExecutiveSummaryCard analysis={mock} onExploreTechnical={exploreFn} />);

      expect(screen.getByText('Protection Overview (Plain English)')).toBeInTheDocument();
      expect(screen.getByText('1. What content was inspected?')).toBeInTheDocument();
      expect(screen.getByText('2. What was requested from you?')).toBeInTheDocument();
      expect(screen.getByText('3. What claims were made?')).toBeInTheDocument();
      expect(screen.getByText('4. What did authoritative records show?')).toBeInTheDocument();
      expect(screen.getByText('5. Why did Nivesh Firewall intervene?')).toBeInTheDocument();

      const exploreBtn = screen.getByRole('button', { name: /Explore technical attack-paths/i });
      await userEvent.click(exploreBtn);
      expect(exploreFn).toHaveBeenCalledTimes(1);
    });
  });

  // 10. Privacy Sanitization Boundary
  describe('10. Privacy Sanitization Safeguards', () => {
    it('scrubs sensitive credentials before rendering', () => {
      const dirtyData = {
        password: 'SuperSecretPassword123',
        otp_code: '984512',
        cvv: '999',
        card_number: '4111 2222 3333 4444',
        user_note: 'Here is my password: secret and pin: 1234',
        normal_data: 'Rahul Sharma research analyst',
      };

      const cleaned = sanitizeDataForRendering(dirtyData);
      expect(cleaned.password).toBe('[REDACTED_CONFIDENTIAL]');
      expect(cleaned.card_number).toBe('[REDACTED_CONFIDENTIAL]');
      expect(cleaned.normal_data).toBe('Rahul Sharma research analyst');
    });

    it('renders privacy safeguard notice', () => {
      render(<PrivacySafeguardNotice />);
      expect(screen.getByText(/Privacy & Confidentiality Safeguards Active/i)).toBeInTheDocument();
      expect(screen.getByText(/Sensitive user credentials/i)).toBeInTheDocument();
    });
  });

  // 11. Real Benchmark Scenario Validation (Section 37)
  describe('11. Real Benchmark Scenario: Rapid Escalation + Payment', () => {
    it('faithfully visualizes all stages of the Telegram -> APK -> Payment benchmark', () => {
      const benchmarkMock = createMockAnalysis({
        content: {
          content_id: 'CNT-BENCHMARK',
          input_type: 'text',
          channel: 'telegram',
          summary: '10:00 Educational info, 10:01 Telegram VIP, 10:02 Install APK, 10:03 Pay ₹5,000, 10:03:30 5 mins left',
          contains_financial_content: true,
          entities: { people: ['VIP Guru'], organizations: [], regulators: [], financial_instruments: [] },
        },
        actions: [
          {
            action_id: 'ACT-BENCH-1',
            action_type: 'DOWNLOAD',
            target: 'trading_app.apk',
            impact_category: 'APPLICATION_INSTALLATION',
            reversibility: 'DIFFICULT',
            urgency_detected: false,
          },
          {
            action_id: 'ACT-BENCH-2',
            action_type: 'TRANSFER_MONEY',
            target: 'upi@paytm',
            impact_category: 'FINANCIAL_TRANSACTION',
            reversibility: 'IRREVERSIBLE',
            urgency_detected: true,
          },
        ],
      });

      render(<AnalysisResultView analysis={benchmarkMock} onAnalyzeAnother={() => {}} />);

      // Verify that all components rendered faithfully
      expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
      expect(screen.getByText('Requested User Actions')).toBeInTheDocument();
      expect(screen.getByText('Scam Fingerprint Intelligence')).toBeInTheDocument();
      expect(screen.getByText('Threat & Attack-Path Analysis')).toBeInTheDocument();
    });
  });

  // 12. Benign Educational Content Validation (Section 38)
  describe('12. Benign Content Validation', () => {
    it('renders clean neutral verification without fabricating threat paths or warnings', () => {
      const benignMock = createMockAnalysis({
        decision: {
          decision: 'ALLOW',
          severity: 'NONE',
          primary_reason: 'Content contains educational financial concepts without solicitation.',
          reason_codes: ['NEUTRAL_FINANCIAL_CONTENT'],
          explanation: {
            decision: 'ALLOW',
            user_message: 'Nivesh did not identify conditions requiring protection intervention.',
            technical_message: 'Clean mutual funds educational text.',
            primary_reason: 'Content contains educational financial concepts.',
            supporting_signals: [],
          },
          actions_required: [],
          required_user_confirmation: false,
          policy_version: '8.0.0',
        },
        claims: [
          {
            claim_id: 'CLM-BENIGN',
            text: 'Mutual funds offer portfolio diversification across asset classes',
            topic: 'EDUCATIONAL',
            predicate: 'EXPLAINS_CONCEPT',
            modality: 'statement',
            verification_status: 'SUPPORTED',
          },
        ],
        actions: [],
        threat: {
          threat_signals: [],
          attack_stage: undefined,
          terminal_stage: undefined,
          threat_families: [],
          high_impact_action_count: 0,
          confidence: 0.0,
        },
        fingerprint: {
          match_type: 'NO_MATCH',
          observation_count: 0,
          distinct_channels_count: 0,
          match_confidence: 0.0,
        },
        behaviour: {
          signals: [],
          findings: ['Normal educational viewing cadence.'],
          events_in_session: 1,
          time_pressure_detected: false,
          rapid_escalation_detected: false,
          channel_migration_detected: false,
        },
      });

      render(<AnalysisResultView analysis={benignMock} onAnalyzeAnother={() => {}} />);

      expect(screen.getByText('ACTION PERMITTED — VERIFIED NEUTRAL')).toBeInTheDocument();
      expect(screen.getByText('Allow / Verified Neutral')).toBeInTheDocument();
      expect(screen.getAllByText('NO_MATCH').length).toBeGreaterThan(0);
      expect(screen.getByText(/No explicit user actions/i)).toBeInTheDocument();
    });
  });

  // 13. Mode Switching Accessibility
  describe('13. View Mode Switching', () => {
    it('toggles smoothly between Executive Summary and Deep Intelligence views', async () => {
      const mock = createMockAnalysis();
      render(<IntelligenceDetailView analysis={mock} />);

      // Default is Technical view
      expect(screen.getByText('Sequential Attack-Path Stages')).toBeInTheDocument();

      // Click Executive Summary
      const summaryBtn = screen.getByRole('button', { name: /Executive Summary/i });
      await userEvent.click(summaryBtn);

      expect(screen.getByText('Protection Overview (Plain English)')).toBeInTheDocument();

      // Click Deep Intelligence
      const deepBtn = screen.getByRole('button', { name: /Deep Intelligence & Timelines/i });
      await userEvent.click(deepBtn);

      expect(screen.getByText('Sequential Attack-Path Stages')).toBeInTheDocument();
    });
  });
});
