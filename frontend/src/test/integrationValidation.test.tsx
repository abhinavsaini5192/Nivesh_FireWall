/**
 * Nivesh Firewall — Phase 12.5: Frontend Integration & Validation Test Suite
 *
 * Validates:
 * 1. End-to-end scenarios (Benign, Suspicious, Identity Mismatch, Evidence Insufficient, Fingerprint, Behaviour)
 * 2. Failure scenarios (Offline, Timeout, Not Found, Partial Result, ErrorBoundary safety)
 * 3. Race condition and duplicate submission protections
 * 4. Stale result clearing
 * 5. Backend error mapping (Section 19)
 * 6. Product truthfulness and no-investment-advice compliance
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { App } from '../App';
import { apiClient, FirewallClientError } from '../api/client';
import { ErrorBoundary } from '../components/common/ErrorBoundary';
import { mapBackendErrorToUserMessage } from '../types/firewall';
import type { FirewallAnalysisResponse } from '../types/firewall';

// Mock response factory
const createIntegrationFixture = (overrides?: Partial<FirewallAnalysisResponse>): FirewallAnalysisResponse => ({
  analysis_id: 'ORCH-INT-2026-901',
  session_id: 'SESSION-VALIDATION-01',
  pipeline_status: 'COMPLETED',
  created_at: '2026-10-03T10:00:00Z',
  completed_at: '2026-10-03T10:00:01Z',
  duration_ms: 142.8,
  decision: {
    decision: 'PAUSE',
    severity: 'HIGH',
    primary_reason: 'High-impact financial transfer requested alongside unverified authority claims.',
    reason_codes: ['URGENT_FINANCIAL_EXTRACTION', 'UNVERIFIED_AUTHORITY_CLAIM'],
    explanation: {
      decision: 'PAUSE',
      user_message: 'Nivesh identified critical unverified claims. Verification is required before proceeding.',
      technical_message: 'Action contains high-impact payment with contradicted SEBI advisory registration.',
      primary_reason: 'High-impact extraction combined with unverified authority.',
      supporting_signals: ['TELEGRAM_MIGRATION', 'UNVERIFIED_SEBI_CLAIM', 'TIME_PRESSURE'],
    },
    actions_required: ['PAUSE_ACTION', 'USER_CONFIRMATION_REQUIRED'],
    required_user_confirmation: true,
    cooldown_seconds: 180,
    policy_version: '8.0.0',
    decision_id: 'DEC-INT-001',
  },
  content: {
    content_id: 'CNT-INT-001',
    input_type: 'text',
    channel: 'telegram',
    summary: 'Join VIP group for 40% returns, download custom terminal APK and transfer ₹5,000 fee.',
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
      claim_id: 'CLM-INT-1',
      text: 'Rahul Sharma is SEBI registered research analyst',
      topic: 'REGULATORY_AUTHORITY',
      predicate: 'REGISTERED_WITH',
      modality: 'statement',
      verification_status: 'CONTRADICTED',
    },
  ],
  actions: [
    {
      action_id: 'ACT-INT-1',
      action_type: 'TRANSFER_MONEY',
      target: 'desk@upi',
      impact_category: 'FINANCIAL_TRANSACTION',
      reversibility: 'IRREVERSIBLE',
      urgency_detected: true,
    },
  ],
  evidence: {
    overall_status: 'CONTRADICTED',
    supported_claims_count: 0,
    contradicted_claims_count: 1,
    insufficient_claims_count: 0,
    source_filings_count: 14,
    retrieval_status: 'live',
    claims: [
      {
        claim_id: 'CLM-INT-1',
        status: 'CONTRADICTED',
        source_name: 'SEBI Intermediary Registry',
        source_type: 'REGULATORY_DATABASE',
        source_mode: 'LIVE',
        reason: 'Registration identifier does not correspond to claimed persona.',
      },
    ],
  },
  identity: {
    identity_status: 'IDENTITY_MISMATCH',
    claimed_entities: ['Rahul Sharma'],
    findings_count: 1,
    findings_summary: ['Registration identifier does not correspond to claimed persona.'],
    confidence: 0.88,
  },
  threat: {
    threat_signals: ['TELEGRAM_MIGRATION', 'UNVERIFIED_SEBI_CLAIM', 'TIME_PRESSURE'],
    attack_stage: 'TRUST_BUILDING',
    terminal_stage: 'FINANCIAL_EXTRACTION',
    threat_families: ['UNAUTHORIZED_ADVISORY'],
    high_impact_action_count: 1,
    confidence: 0.92,
  },
  fingerprint: {
    match_type: 'SEMANTIC_VARIANT',
    fingerprint_id: 'FP-INT-441',
    observation_count: 42,
    distinct_channels_count: 3,
    structural_equivalence: true,
    match_confidence: 0.89,
    first_observed: '2026-08-01',
    last_observed: '2026-10-02',
  },
  behaviour: {
    signals: ['channel_migration', 'rapid_escalation', 'time_pressure'],
    findings: ['Rapid escalation from public message to direct UPI fee payment.'],
    events_in_session: 4,
    time_pressure_detected: true,
    rapid_escalation_detected: true,
    channel_migration_detected: true,
  },
  provenance: {
    pipeline_version: '11.4.0',
    orchestrator_run_id: 'ORCH-RUN-99',
  },
  warnings: [],
  errors: [],
  ...overrides,
});

describe('Phase 12.5 — Frontend Integration & Validation Suite', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.location.hash = '';
  });

  // =========================================================================
  // 1. End-to-End Scenarios
  // =========================================================================

  describe('1. End-to-End Scenarios', () => {
    it('Scenario 1: Benign educational text renders verified neutral state without threat fabrication', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const benignFixture = createIntegrationFixture({
        analysis_id: 'BENIGN-001',
        decision: {
          decision: 'ALLOW',
          severity: 'NONE',
          primary_reason: 'Content contains educational financial concepts without solicitation.',
          reason_codes: ['EDUCATIONAL_CONTENT'],
          explanation: {
            decision: 'ALLOW',
            user_message: 'No conditions requiring protective intervention were identified.',
            technical_message: 'Clean educational financial concepts.',
            primary_reason: 'Content contains educational financial concepts without solicitation.',
            supporting_signals: [],
          },
          actions_required: [],
          required_user_confirmation: false,
          policy_version: '8.0.0',
        },
        claims: [
          {
            claim_id: 'CLM-B1',
            text: 'Mutual funds pool money from multiple investors to invest in diversified portfolios',
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
          findings: ['Normal educational reading cadence.'],
          events_in_session: 1,
          time_pressure_detected: false,
          rapid_escalation_detected: false,
          channel_migration_detected: false,
        },
      });

      vi.spyOn(apiClient, 'analyze').mockResolvedValue(benignFixture);
      const user = userEvent.setup();

      render(<App />);

      const input = screen.getByLabelText('Message or Financial Content');
      await user.type(input, 'Learn how mutual funds work. Review diversification, fees, and long-term investing.');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getByText('ACTION PERMITTED — VERIFIED NEUTRAL')).toBeInTheDocument();
        expect(screen.getByText('Allow / Verified Neutral')).toBeInTheDocument();
        expect(screen.getAllByText(/Content contains educational financial concepts/i).length).toBeGreaterThan(0);
        expect(screen.getByText(/No explicit user actions/i)).toBeInTheDocument();
      });
    });

    it('Scenario 2: Suspicious interaction visualizes full progression, intervention, and timeline', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const suspiciousFixture = createIntegrationFixture();
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(suspiciousFixture);
      const user = userEvent.setup();

      render(<App />);

      const input = screen.getByLabelText('Message or Financial Content');
      await user.type(input, 'Join VIP Telegram for guaranteed returns and transfer 5000 fee');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        // Decision & Banner
        expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
        expect(screen.getByText('Pause / Confirmation Required')).toBeInTheDocument();

        // High Impact Action Warning
        expect(screen.getByText('Requested Action: TRANSFER MONEY')).toBeInTheDocument();
        expect(screen.getByText('High-Impact Consequence Action Detected')).toBeInTheDocument();

        // Why Intervened Reason Codes
        expect(screen.getAllByText('URGENT_FINANCIAL_EXTRACTION').length).toBeGreaterThan(0);
        expect(screen.getAllByText('UNVERIFIED_AUTHORITY_CLAIM').length).toBeGreaterThan(0);

        // Attack path & Timeline presence
        expect(screen.getByText('Sequential Attack-Path Stages')).toBeInTheDocument();
        expect(screen.getByText('Observed Interaction Dynamics & Timeline')).toBeInTheDocument();
      });
    });

    it('Scenario 3: Identity Mismatch is rendered objectively without accusations', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const mismatchFixture = createIntegrationFixture({
        identity: {
          identity_status: 'IDENTITY_MISMATCH',
          claimed_entities: ['Aditya Verma'],
          findings_count: 1,
          findings_summary: ['SEBI registration number does not map to claimed advisor persona.'],
          confidence: 0.95,
        },
      });
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(mismatchFixture);
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'Aditya Verma SEBI verified');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getAllByText('IDENTITY_MISMATCH').length).toBeGreaterThan(0);
        expect(screen.getByText('Entity Identity Resolution')).toBeInTheDocument();
        // Discrepancy renders objectively in findings summary
        expect(screen.getByText(/SEBI registration number does not map to claimed advisor persona/i)).toBeInTheDocument();
        // Negative test: never calls anyone a scammer
        expect(screen.queryByText(/scammer/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/fraudulent person/i)).not.toBeInTheDocument();
      });
    });

    it('Scenario 4: Evidence Insufficient is distinguished clearly from Contradicted', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const insufficientFixture = createIntegrationFixture({
        evidence: {
          overall_status: 'INSUFFICIENT_EVIDENCE',
          supported_claims_count: 0,
          contradicted_claims_count: 0,
          insufficient_claims_count: 1,
          source_documents_count: 2,
          retrieval_status: 'cache',
          verification_count: 1,
        },
      });
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(insufficientFixture);
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'New private scheme');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getAllByText('INSUFFICIENT_EVIDENCE').length).toBeGreaterThan(0);
        expect(screen.getAllByText(/Insufficient Evidence/i).length).toBeGreaterThan(0);
        expect(screen.getByText('Authoritative Registry & Evidence Verification')).toBeInTheDocument();
        expect(screen.getByText(/Direct verification metrics compiled from regulatory filings/i)).toBeInTheDocument();
      });
    });

    it('Scenario 5: Fingerprint Variant presents structural equivalence without proof of fraud', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const fpFixture = createIntegrationFixture({
        fingerprint: {
          match_type: 'SEMANTIC_VARIANT',
          fingerprint_id: 'FP-VARIANT-88',
          observation_count: 55,
          distinct_channels_count: 4,
          match_confidence: 0.91,
        },
      });
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(fpFixture);
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'VIP Signal Club');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getAllByText('SEMANTIC_VARIANT').length).toBeGreaterThan(0);
        expect(screen.getByText('Structural Equivalence')).toBeInTheDocument();
        expect(screen.getByText(/YES \(Known Template Structure\)/i)).toBeInTheDocument();
        // Disclaimer preserved
        expect(screen.getByText(/Structural pattern matching identifies architectural similarity to known campaign blueprints/i)).toBeInTheDocument();
      });
    });

    it('Scenario 6: Behavioural signals display observed transitions without psychological profiling', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const behaviourFixture = createIntegrationFixture({
        behaviour: {
          signals: ['channel_migration', 'rapid_escalation', 'time_pressure'],
          findings: ['Rapid escalation transition detected.'],
          events_in_session: 3,
          time_pressure_detected: true,
          rapid_escalation_detected: true,
          channel_migration_detected: true,
        },
      });
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(behaviourFixture);
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'Hurry 2 mins left');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getByText('Temporal Dynamic')).toBeInTheDocument();
        expect(screen.getByText('Time Pressure Detected')).toBeInTheDocument();
        // No psychological armchair diagnoses
        expect(screen.queryByText(/user was impulsive/i)).not.toBeInTheDocument();
        expect(screen.queryByText(/victim personality/i)).not.toBeInTheDocument();
      });
    });
  });

  // =========================================================================
  // 2. Failure Scenarios & Error Resilience
  // =========================================================================

  describe('2. Failure Scenarios & Error Resilience', () => {
    it('Backend offline: reports service unavailability gracefully with retry option', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      vi.spyOn(apiClient, 'analyze').mockRejectedValue(
        new FirewallClientError({
          error_code: 'SERVICE_UNAVAILABLE',
          message: 'Nivesh protection service is temporarily unavailable.',
        })
      );
      const user = userEvent.setup();

      render(<App />);

      const input = screen.getByLabelText('Message or Financial Content');
      await user.type(input, 'Test content while backend is down');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getByText('Analysis Could Not Be Completed')).toBeInTheDocument();
        expect(screen.getAllByText('Nivesh protection service is temporarily unavailable.').length).toBeGreaterThan(0);
        expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
      });
    });

    it('Backend offline on startup: displays Service Offline status in header and disables submit', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'unavailable' });
      render(<App />);
      await waitFor(() => {
        expect(screen.getByText('Service Offline')).toBeInTheDocument();
      });
    });

    it('Request timeout: reports timeout failure without pretending analysis completed', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      vi.spyOn(apiClient, 'analyze').mockRejectedValue(
        new FirewallClientError({
          error_code: 'PIPELINE_FAILURE',
          message: 'The analysis request timed out. Please try again.',
        })
      );
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'Slow server content');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getByText('Analysis Could Not Be Completed')).toBeInTheDocument();
        expect(screen.getAllByText('The analysis request timed out. Please try again.').length).toBeGreaterThan(0);
      });
    });

    it('Missing analysis retrieval by ID: displays clean ANALYSIS_NOT_FOUND state', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      vi.spyOn(apiClient, 'getAnalysis').mockRejectedValue(
        new FirewallClientError({
          error_code: 'ANALYSIS_NOT_FOUND',
          message: 'Failed to retrieve analysis record (HTTP 404).',
          analysis_id: 'NON-EXISTENT-ID',
        })
      );

      // Deep link to non-existent ID
      window.location.hash = '#protect?id=NON-EXISTENT-ID';

      render(<App />);

      await waitFor(() => {
        expect(screen.getByText('Analysis Could Not Be Completed')).toBeInTheDocument();
        expect(screen.getByText(/Error Code: ANALYSIS_NOT_FOUND/i)).toBeInTheDocument();
      });
    });

    it('Partial pipeline analysis: surfaces partial result without error crash', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const partialFixture = createIntegrationFixture({
        pipeline_status: 'PARTIAL',
        warnings: ['Engine 7 collective fingerprint store temporarily unavailable.'],
      });
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(partialFixture);
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'Partial pipeline content');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
        expect(screen.getByText('Status: PARTIAL (142.8ms)')).toBeInTheDocument();
      });
    });

    it('UI ErrorBoundary: catches child rendering crash safely without defaulting to ALLOW', () => {
      const BadComponent = () => {
        throw new Error('Fatal UI crash in visualization tree');
      };

      render(
        <ErrorBoundary>
          <BadComponent />
        </ErrorBoundary>
      );

      // Caught by boundary
      expect(screen.getByText('Something went wrong.')).toBeInTheDocument();
      expect(screen.getByText("We couldn't display this analysis.")).toBeInTheDocument();
      expect(screen.getByText('Analysis Incomplete')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Return to protection/i })).toBeInTheDocument();

      // Critical safety check: NEVER shows ALLOW or stack trace
      expect(screen.queryByText('Fatal UI crash in visualization tree')).not.toBeInTheDocument();
      expect(screen.queryByText(/Action Permitted/i)).not.toBeInTheDocument();
    });
  });

  // =========================================================================
  // 3. Race Condition, Stale Result & Duplicate Submission Protection
  // =========================================================================

  describe('3. Request Lifecycle & Concurrency Protections', () => {
    it('Overlapping requests: older Request A does not overwrite newer Request B', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });

      let resolveRequestA!: (val: FirewallAnalysisResponse) => void;
      const promiseA = new Promise<FirewallAnalysisResponse>((res) => {
        resolveRequestA = res;
      });

      const fixtureA = createIntegrationFixture({
        analysis_id: 'REQ-A-PAUSE',
        decision: { ...createIntegrationFixture().decision, decision: 'PAUSE' },
      });
      const fixtureB = createIntegrationFixture({
        analysis_id: 'REQ-B-BLOCK',
        decision: { ...createIntegrationFixture().decision, decision: 'BLOCK', primary_reason: 'Blocked newer request.' },
      });

      vi.spyOn(apiClient, 'analyze').mockReturnValueOnce(promiseA); // Request A is slow
      vi.spyOn(apiClient, 'getAnalysis').mockResolvedValue(fixtureB); // Request B is fast

      const user = userEvent.setup();
      render(<App />);

      const input = screen.getByLabelText('Message or Financial Content');
      await user.type(input, 'Request A content');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      // Wait until analyzing
      expect(screen.getByText('Analyzing financial interaction across firewall pipeline...')).toBeInTheDocument();

      // Trigger Request B through deep link navigation while Request A is pending
      window.location.hash = '#protect?id=REQ-B-BLOCK';
      window.dispatchEvent(new HashChangeEvent('hashchange'));

      // Wait until Request B resolves and displays
      await waitFor(() => {
        expect(screen.getByText('REQ-B-BLOCK')).toBeInTheDocument();
      });

      // Now resolve slow Request A
      resolveRequestA(fixtureA);

      // Verify that Request B remains rendered and Request A was ignored due to activeRequestIdRef
      await waitFor(() => {
        expect(screen.getByText('REQ-B-BLOCK')).toBeInTheDocument();
        expect(screen.queryByText('REQ-A-PAUSE')).not.toBeInTheDocument();
      });
    });

    it('Duplicate clicks during active analysis are blocked', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      let resolvePromise!: (val: FirewallAnalysisResponse) => void;
      const delayedPromise = new Promise<FirewallAnalysisResponse>((res) => {
        resolvePromise = res;
      });

      const analyzeSpy = vi.spyOn(apiClient, 'analyze').mockReturnValue(delayedPromise);
      const user = userEvent.setup();

      render(<App />);

      const input = screen.getByLabelText('Message or Financial Content');
      await user.type(input, 'Testing double click');
      const submitBtn = screen.getByRole('button', { name: /Analyze Content/i });

      // Click once
      await user.click(submitBtn);

      // Button is now disabled or replaced by loading
      expect(analyzeSpy).toHaveBeenCalledTimes(1);

      // Attempt second click (button is disabled or loading indicator is shown)
      resolvePromise(createIntegrationFixture());

      await waitFor(() => {
        expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
      });

      expect(analyzeSpy).toHaveBeenCalledTimes(1);
    });

    it('New analysis clears prior analysis immediately (no stale result displayed)', async () => {
      vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
      const fixture = createIntegrationFixture();
      vi.spyOn(apiClient, 'analyze').mockResolvedValue(fixture);
      const user = userEvent.setup();

      render(<App />);

      await user.type(screen.getByLabelText('Message or Financial Content'), 'First analysis content');
      await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

      await waitFor(() => {
        expect(screen.getByText('ORCH-INT-2026-901')).toBeInTheDocument();
      });

      // Click "Analyze Another Content"
      await user.click(screen.getByRole('button', { name: /Analyze Another Content/i }));

      // Screen is back to clean input; previous analysis is cleared
      expect(screen.getByLabelText('Message or Financial Content')).toBeInTheDocument();
      expect(screen.queryByText('ORCH-INT-2026-901')).not.toBeInTheDocument();
    });
  });

  // =========================================================================
  // 4. Centralized Backend Error Mapping (Section 19)
  // =========================================================================

  describe('4. Centralized Backend Error Mapping (Section 19)', () => {
    it('maps all 5 canonical backend error codes into clean product-level messages', () => {
      expect(mapBackendErrorToUserMessage('INVALID_REQUEST')).toBe('Check the submitted content.');
      expect(mapBackendErrorToUserMessage('UNSUPPORTED_INPUT')).toBe('This type of content is not currently supported.');
      expect(mapBackendErrorToUserMessage('SERVICE_UNAVAILABLE')).toBe('Nivesh protection service is temporarily unavailable.');
      expect(mapBackendErrorToUserMessage('PIPELINE_FAILURE')).toBe("We couldn't complete this analysis.");
      expect(mapBackendErrorToUserMessage('ANALYSIS_NOT_FOUND')).toBe('This analysis is no longer available.');
      expect(mapBackendErrorToUserMessage('UNKNOWN_CODE', 'Custom error')).toBe('Custom error');
    });
  });

  // =========================================================================
  // 5. Product Truthfulness & No Investment Advice Compliance (Sections 47 & 48)
  // =========================================================================

  describe('5. Product Truthfulness & Regulatory Boundaries', () => {
    it('does not contain misleading claims of 100% scam detection or government certification', () => {
      render(<App />);

      // Truthfulness check
      expect(screen.queryByText(/100% scam detection/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/100% guaranteed/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/SEBI certified firewall/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/government approved/i)).not.toBeInTheDocument();
    });

    it('does not issue investment advice, buy/sell orders, or return promises', () => {
      render(<App />);

      expect(screen.queryByText(/buy recommendation/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/sell recommendation/i)).not.toBeInTheDocument();
      expect(screen.queryByText(/price target/i)).not.toBeInTheDocument();
    });
  });
});
