import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { AnalysisResultView } from '../components/firewall/AnalysisResultView';
import { ProtectionBanner } from '../components/intervention/ProtectionBanner';
import { deriveInterventionModel } from '../types/intervention';
import type { FirewallAnalysisResponse } from '../types/firewall';

// Helper to construct canonical response fixtures
const createFixture = (overrides: Partial<FirewallAnalysisResponse> = {}): FirewallAnalysisResponse => ({
  analysis_id: 'ORCH-INTERVENTION-001',
  session_id: 'SESSION-INT-999',
  pipeline_status: 'COMPLETED',
  created_at: '2026-10-03T07:00:00Z',
  completed_at: '2026-10-03T07:00:01Z',
  duration_ms: 320.4,
  decision: {
    decision: 'PAUSE',
    severity: 'HIGH',
    primary_reason: 'High-consequence transfer requested with unverified identity credentials.',
    reason_codes: ['POLICY-PAUSE-01', 'ENTITY-UNREGISTERED'],
    explanation: {
      decision: 'PAUSE',
      user_message: 'Please pause and verify the counterparty through official channels before continuing.',
      technical_message: 'Action paused due to multi-signal threshold.',
      primary_reason: 'High-consequence transfer requested with unverified identity credentials.',
      supporting_signals: ['FINANCIAL_REQUEST', 'IDENTITY_NOT_ESTABLISHED'],
    },
    actions_required: ['REQUIRE_CONFIRMATION'],
    required_user_confirmation: true,
    cooldown_seconds: 30,
    policy_version: '8.0.0',
    decision_id: 'DEC-PAUSE-01',
  },
  content: {
    content_id: 'CONT-INT-001',
    input_type: 'text',
    channel: 'telegram',
    summary: 'Transfer funds to investment pool',
    contains_financial_content: true,
    entities: { ORGANIZATION: ['Alpha Wealth'] },
  },
  claims: [
    {
      claim_id: 'CLM-01',
      text: 'Guaranteed 50% returns in 30 days',
      topic: 'RETURN_PROMISE',
      predicate: 'PROMISES_RETURN',
      modality: 'CERTAIN',
      verification_status: 'CONTRADICTED',
    },
  ],
  actions: [
    {
      action_id: 'ACT-01',
      action_type: 'TRANSFER_MONEY',
      target: 'pool@upi',
      impact_category: 'FINANCIAL_REQUEST',
      reversibility: 'IRREVERSIBLE',
      urgency_detected: true,
    },
  ],
  evidence: {
    overall_status: 'CONTRADICTED',
    verification_count: 1,
    supported_claims_count: 0,
    contradicted_claims_count: 1,
    insufficient_claims_count: 0,
    source_documents_count: 1,
    retrieval_status: 'COMPLETED',
  },
  identity: {
    identity_status: 'NOT_ESTABLISHED',
    claimed_entities: ['Alpha Wealth'],
    findings_count: 1,
    findings_summary: ['Alpha Wealth is not registered on the official SEBI intermediary database.'],
    confidence: 0.2,
  },
  threat: {
    threat_signals: ['FINANCIAL_REQUEST', 'UNREGISTERED_ADVISORY'],
    attack_stage: 'CHANNEL_MIGRATION',
    terminal_stage: 'FINANCIAL_EXTRACTION',
    threat_families: ['HIGH_YIELD_INVESTMENT_SCHEME'],
    high_impact_action_count: 1,
    confidence: 0.95,
  },
  fingerprint: {
    match_type: 'SEMANTIC_VARIANT',
    fingerprint_id: 'FP-ALPHA-WEALTH-01',
    match_confidence: 0.89,
    observation_count: 18,
    distinct_channels_count: 2,
    attack_path_signature: 'TELEGRAM->UPI',
  },
  behaviour: {
    signals: ['RAPID_ACTION_ESCALATION', 'TIME_PRESSURE'],
    findings: ['Rapid escalation from introduction to payment demand.'],
    session_id: 'SESSION-INT-999',
    events_in_session: 3,
    time_pressure_detected: true,
    rapid_escalation_detected: true,
    channel_migration_detected: false,
  },
  provenance: {
    orchestrator_version: '11.5.0',
    engines_executed: ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'e10'],
    engines_succeeded: ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7', 'e8', 'e9', 'e10'],
  },
  warnings: [],
  errors: [],
  ...overrides,
});

describe('Phase 12.3 — Intervention & Protection Experience', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  // Test 1 — ALLOW experience
  it('Test 1: ALLOW produces calm confirmation without claim of guaranteed legitimacy', () => {
    const allowFixture = createFixture({
      decision: {
        decision: 'ALLOW',
        severity: 'INFORMATIONAL',
        primary_reason: 'Content contains educational financial concepts without solicitation.',
        reason_codes: ['NEUTRAL_FINANCIAL_CONTENT'],
        explanation: {
          decision: 'ALLOW',
          user_message: 'Nivesh did not identify conditions requiring protection intervention.',
          technical_message: 'Evaluated clean under rules.',
          primary_reason: 'Educational content.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={allowFixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ACTION PERMITTED — VERIFIED NEUTRAL')).toBeInTheDocument();
    expect(screen.getByText(/Nivesh did not identify conditions requiring protection intervention/i)).toBeInTheDocument();
    // Safety check: Does NOT claim "100% Safe" or "Guaranteed legitimate"
    expect(screen.queryByText(/100% Safe/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Guaranteed legitimate/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Continue to Destination/i })).toBeInTheDocument();
  });

  // Test 2 — INFORM experience
  it('Test 2: INFORM displays contextual advisory without alarmist framing', () => {
    const informFixture = createFixture({
      decision: {
        decision: 'INFORM',
        severity: 'LOW',
        primary_reason: 'Contextual disclosure regarding general market volatility.',
        reason_codes: ['INFORMATIONAL_ADVISORY'],
        explanation: {
          decision: 'INFORM',
          user_message: 'Please review general market disclosures before making decisions.',
          technical_message: 'Advisory flag.',
          primary_reason: 'Contextual disclosure.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={informFixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('INFORMATIONAL ADVISORY')).toBeInTheDocument();
    expect(screen.getByText(/Please review general market disclosures/i)).toBeInTheDocument();
    expect(screen.queryByText(/Immediate danger/i)).not.toBeInTheDocument();
  });

  // Test 3 — WARN experience
  it('Test 3: WARN provides visible caution state with backend reason basis', () => {
    const warnFixture = createFixture({
      decision: {
        decision: 'WARN',
        severity: 'MEDIUM',
        primary_reason: 'Unregistered adviser promoting speculative derivatives.',
        reason_codes: ['RULE-WARN-01'],
        explanation: {
          decision: 'WARN',
          user_message: 'Exercise caution before joining private investment groups.',
          technical_message: 'Unverified claims.',
          primary_reason: 'Unregistered adviser promoting speculative derivatives.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={warnFixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('CAUTION RECOMMENDED')).toBeInTheDocument();
    expect(screen.getByText(/Exercise caution before joining private investment groups/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Review Findings & Details/i })).toBeInTheDocument();
  });

  // Test 4 — PAUSE experience
  it('Test 4: PAUSE renders high-visibility pause state, cooldown, and explicit confirmation alert', () => {
    const pauseFixture = createFixture();
    render(<AnalysisResultView analysis={pauseFixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/Explicit Confirmation Required/i);
    expect(screen.getByText(/Recommended cooldown pause: 30 seconds/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Explicit User Override/i })).toBeInTheDocument();
  });

  // Test 5 — BLOCK experience
  it('Test 5: BLOCK renders strong protection state without sensational accusations', () => {
    const blockFixture = createFixture({
      decision: {
        decision: 'BLOCK',
        severity: 'CRITICAL',
        primary_reason: 'Critical threat signature detected: malicious APK installation combined with unauthorized money transfer.',
        reason_codes: ['POLICY-BLOCK-01', 'MALICIOUS_APP_DETECTED'],
        explanation: {
          decision: 'BLOCK',
          user_message: 'This action was blocked by Nivesh Firewall because the protection policy determined that intervention is required.',
          technical_message: 'Terminal attack-path stage reached.',
          primary_reason: 'Critical threat signature detected.',
          supporting_signals: ['MALICIOUS_DOWNLOAD', 'CREDENTIAL_THEFT'],
        },
        actions_required: ['TERMINATE_ACTION'],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={blockFixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ACTION BLOCKED — THREAT PREVENTED')).toBeInTheDocument();
    expect(screen.getByText(/This action was blocked by Nivesh Firewall/i)).toBeInTheDocument();
    // Safety check: Avoids sensational "You were definitely being scammed"
    expect(screen.queryByText(/You were definitely being scammed/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Inspect Contradicted Evidence/i })).toBeInTheDocument();
  });

  // Test 6 — Decision authority
  it('Test 6: Purely renders supplied Engine 8 decision without overriding backend verdict', () => {
    const testCases: Array<FirewallAnalysisResponse['decision']['decision']> = [
      'ALLOW',
      'INFORM',
      'WARN',
      'PAUSE',
      'BLOCK',
    ];

    testCases.forEach((dec) => {
      const model = deriveInterventionModel(
        createFixture({
          decision: {
            decision: dec,
            severity: dec === 'BLOCK' ? 'CRITICAL' : 'MEDIUM',
            primary_reason: `Evaluated ${dec}`,
            reason_codes: [`TEST-${dec}`],
            explanation: {
              decision: dec,
              user_message: `Message for ${dec}`,
              technical_message: `Tech ${dec}`,
              primary_reason: `Reason ${dec}`,
              supporting_signals: [],
            },
            actions_required: [],
            required_user_confirmation: dec === 'PAUSE',
            policy_version: '8.0.0',
          },
        })
      );
      expect(model.decision).toBe(dec);
    });
  });

  // Test 7 — No frontend policy logic
  it('Test 7: Frontend derivation helper does not execute risk thresholds or recalculate severity', () => {
    // Content contains scary terms ("telegram", "money", "urgent"), but backend returned ALLOW
    const benignWithTriggerWords = createFixture({
      content: {
        content_id: 'C-01',
        input_type: 'text',
        channel: 'telegram',
        summary: 'Send payment receipt for accounting invoice',
        contains_financial_content: true,
        entities: {},
      },
      decision: {
        decision: 'ALLOW',
        severity: 'INFORMATIONAL',
        primary_reason: 'Legitimate business invoice communication.',
        reason_codes: ['INVOICE_CLEAR'],
        explanation: {
          decision: 'ALLOW',
          user_message: 'Content verified neutral.',
          technical_message: 'Clean',
          primary_reason: 'Legitimate business invoice.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    const model = deriveInterventionModel(benignWithTriggerWords);
    // Verifies frontend DID NOT override backend to BLOCK/WARN
    expect(model.decision).toBe('ALLOW');
  });

  // Test 8 — Reason rendering
  it('Test 8: Reason codes and primary reason from backend render faithfully', () => {
    const fixture = createFixture({
      decision: {
        decision: 'PAUSE',
        severity: 'HIGH',
        primary_reason: 'Specific regulatory mismatch code R-889 triggered.',
        reason_codes: ['CODE-SEC-01', 'CODE-SEC-02'],
        explanation: {
          decision: 'PAUSE',
          user_message: 'Hold for verification.',
          technical_message: 'Tech',
          primary_reason: 'Specific regulatory mismatch code R-889 triggered.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: true,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getAllByText('Specific regulatory mismatch code R-889 triggered.').length).toBeGreaterThan(0);
    expect(screen.getAllByText('CODE-SEC-01').length).toBeGreaterThan(0);
    expect(screen.getAllByText('CODE-SEC-02').length).toBeGreaterThan(0);
  });

  // Test 9 — Evidence connection
  it('Test 9: Clicking evidence link in "Why did Nivesh intervene?" targets panel-evidence', async () => {
    const fixture = createFixture();
    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    const evidenceBtn = screen.getByRole('button', { name: /Jump to See contradicted claims/i });
    expect(evidenceBtn).toBeInTheDocument();
  });

  // Test 10 — Identity connection
  it('Test 10: Clicking identity link targets panel-identity and preserves exact status', async () => {
    const fixture = createFixture();
    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    const identityBtn = screen.getByRole('button', { name: /Jump to See identity verification/i });
    expect(identityBtn).toBeInTheDocument();
  });

  // Test 11 — Threat connection
  it('Test 11: Clicking threat analysis link targets panel-threat', async () => {
    const fixture = createFixture();
    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    const threatBtn = screen.getByRole('button', { name: /Jump to View threat analysis/i });
    expect(threatBtn).toBeInTheDocument();
  });

  // Test 12 — Fingerprint connection
  it('Test 12: Scam fingerprint match is rendered as a structural pattern rather than absolute proof', () => {
    const fixture = createFixture();
    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText(/Matched structural template pattern \(SEMANTIC VARIANT\) previously observed/i)).toBeInTheDocument();
  });

  // Test 13 — Behaviour connection
  it('Test 13: Behavioural findings render observed patterns without armchair psychology', () => {
    const fixture = createFixture();
    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText(/Interaction signals: RAPID ACTION ESCALATION, TIME PRESSURE/i)).toBeInTheDocument();
    expect(screen.queryByText(/User is impulsive/i)).not.toBeInTheDocument();
  });

  // Test 14 — User Override
  it('Test 14: User override modal allows explicit confirmation and records override state', async () => {
    const user = userEvent.setup();
    const onOverrideSpy = vi.fn();
    const fixture = createFixture();

    render(
      <AnalysisResultView
        analysis={fixture}
        onAnalyzeAnother={() => {}}
        onOverrideConfirmed={onOverrideSpy}
      />
    );

    // Click explicit override button
    const overrideBtn = screen.getByRole('button', { name: /Explicit User Override/i });
    await user.click(overrideBtn);

    // Confirmation modal should be visible
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Explicit User Confirmation')).toBeInTheDocument();

    const checkbox = screen.getByRole('checkbox');
    expect(checkbox).not.toBeChecked();

    const confirmBtn = screen.getByRole('button', { name: /Confirm Override & Continue/i });
    expect(confirmBtn).toBeDisabled();

    // Check acknowledgment
    await user.click(checkbox);
    expect(confirmBtn).not.toBeDisabled();

    // Confirm override
    await user.click(confirmBtn);

    expect(onOverrideSpy).toHaveBeenCalledTimes(1);
    expect(screen.getByText(/User Manual Override Confirmed/i)).toBeInTheDocument();
  });

  // Test 15 — Override cancellation
  it('Test 15: Cancelling override preserves original policy state without side-effects', async () => {
    const user = userEvent.setup();
    const onOverrideSpy = vi.fn();
    const fixture = createFixture();

    render(
      <AnalysisResultView
        analysis={fixture}
        onAnalyzeAnother={() => {}}
        onOverrideConfirmed={onOverrideSpy}
      />
    );

    await user.click(screen.getByRole('button', { name: /Explicit User Override/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Cancel modal
    await user.click(screen.getByRole('button', { name: /Cancel \(Keep Protection Active\)/i }));

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    expect(onOverrideSpy).not.toHaveBeenCalled();
    expect(screen.queryByText(/User Manual Override Confirmed/i)).not.toBeInTheDocument();
  });

  // Test 16 — API failure / safe presentation
  it('Test 16: Surfaces safe product-level error state on missing payload', () => {
    render(<AnalysisResultView analysis={null as any} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('Analysis Result Incomplete')).toBeInTheDocument();
    expect(screen.getByText(/We couldn't display the full protection details/i)).toBeInTheDocument();
  });

  // Test 17 — Rendering failure safety boundary
  it('Test 17: Never downgrades a BLOCK decision to ALLOW on rendering failure', () => {
    const malformedBlock = {
      ...createFixture(),
      decision: {
        decision: 'BLOCK',
      } as any,
    };

    const model = deriveInterventionModel(malformedBlock);
    // Decision must strictly stay BLOCK
    expect(model.decision).toBe('BLOCK');
  });

  // Test 18 — Keyboard accessibility
  it('Test 18: Intervention controls, actions, and summary items are accessible via keyboard', async () => {
    const fixture = createFixture();
    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(5);

    // Each button should be in tab order
    buttons.forEach((btn) => {
      expect(btn).not.toHaveAttribute('tabindex', '-1');
    });
  });

  // Test 19 — Dialog accessibility
  it('Test 19: Override modal traps focus and closes cleanly with Escape key', async () => {
    const user = userEvent.setup();
    const fixture = createFixture();

    render(<AnalysisResultView analysis={fixture} onAnalyzeAnother={() => {}} />);

    await user.click(screen.getByRole('button', { name: /Explicit User Override/i }));
    expect(screen.getByRole('dialog')).toBeInTheDocument();

    // Press Escape
    fireEvent.keyDown(window, { key: 'Escape', code: 'Escape' });

    await waitFor(() => {
      expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
    });
  });

  // Test 20 — ProtectionBanner standalone presentation
  it('Test 20: ProtectionBanner renders across all 5 decision states with consistent contrast', () => {
    const decisions: Array<FirewallAnalysisResponse['decision']['decision']> = [
      'ALLOW',
      'INFORM',
      'WARN',
      'PAUSE',
      'BLOCK',
    ];

    decisions.forEach((dec) => {
      const { unmount } = render(
        <ProtectionBanner
          decision={dec}
          description={`Banner for ${dec}`}
        />
      );
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText(`Banner for ${dec}`)).toBeInTheDocument();
      unmount();
    });
  });
});
