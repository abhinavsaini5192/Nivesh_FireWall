import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from '../App';
import { apiClient, FirewallClientError } from '../api/client';
import { AnalysisResultView } from '../components/firewall/AnalysisResultView';
import type { FirewallAnalysisResponse } from '../types/firewall';

// Helper to construct canonical response fixtures matching Phase 11.4 schemas
const createMockResponse = (
  overrides: Partial<FirewallAnalysisResponse> = {}
): FirewallAnalysisResponse => ({
  analysis_id: 'ORCH-MOCK-TEST-001',
  session_id: 'SESSION-TEST-XYZ',
  pipeline_status: 'COMPLETED',
  created_at: '2026-10-03T06:30:00Z',
  completed_at: '2026-10-03T06:30:01Z',
  duration_ms: 450.5,
  decision: {
    decision: 'PAUSE',
    severity: 'HIGH',
    primary_reason: 'High-impact financial action combined with unverified entity identity.',
    reason_codes: ['RULE-PAUSE-01', 'ENTITY-UNVERIFIED'],
    explanation: {
      decision: 'PAUSE',
      user_message: 'Please pause and verify the advisor credentials independently.',
      technical_message: 'High consequence action combined with unregistered entity.',
      primary_reason: 'High-impact financial action combined with unverified entity identity.',
      supporting_signals: ['FINANCIAL_REQUEST', 'IDENTITY_NOT_ESTABLISHED'],
    },
    actions_required: ['REQUIRE_CONFIRMATION'],
    required_user_confirmation: true,
    cooldown_seconds: 30,
    policy_version: '8.0.0',
    decision_id: 'DEC-001',
  },
  content: {
    content_id: 'CONT-001',
    input_type: 'text',
    channel: 'telegram',
    summary: 'Transfer ₹5,000 to VIP channel',
    contains_financial_content: true,
    entities: { ORGANIZATION: ['VIP Signals'] },
  },
  claims: [
    {
      claim_id: 'CLM-001',
      text: 'Guaranteed 40% monthly returns',
      topic: 'RETURN_PROMISE',
      predicate: 'PROMISES_RETURN',
      modality: 'CERTAIN',
      verification_status: 'CONTRADICTED',
    },
    {
      claim_id: 'CLM-002',
      text: 'SEBI registered research analyst Rahul Sharma',
      topic: 'REGULATORY_STATUS',
      predicate: 'CLAIMS_REGISTRATION',
      modality: 'ASSERTED',
      verification_status: 'INSUFFICIENT_EVIDENCE',
    },
  ],
  actions: [
    {
      action_id: 'ACT-001',
      action_type: 'DOWNLOAD',
      target: 'trading_terminal.apk',
      impact_category: 'APPLICATION_INSTALLATION',
      reversibility: 'DIFFICULT',
      urgency_detected: false,
    },
    {
      action_id: 'ACT-002',
      action_type: 'TRANSFER_MONEY',
      target: 'vip@icici',
      impact_category: 'FINANCIAL_REQUEST',
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
    source_documents_count: 2,
    retrieval_status: 'COMPLETED',
  },
  identity: {
    identity_status: 'NOT_ESTABLISHED',
    claimed_entities: ['Rahul Sharma', 'VIP Signals'],
    findings_count: 2,
    findings_summary: [
      'Registration number does not match official SEBI intermediary database.',
    ],
    confidence: 0.15,
  },
  threat: {
    threat_signals: ['SOFTWARE_INSTALLATION', 'FINANCIAL_REQUEST'],
    attack_stage: 'CHANNEL_MIGRATION',
    terminal_stage: 'FINANCIAL_EXTRACTION',
    threat_families: ['OFF_MARKET_TRADING_SCHEME'],
    high_impact_action_count: 1,
    confidence: 0.92,
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
    signals: ['TIME_PRESSURE', 'CHANNEL_MIGRATION', 'RAPID_ACTION_ESCALATION'],
    findings: [
      'Severe urgency detected: "Only 5 minutes left!"',
      'Migration from public forum to private VIP group.',
    ],
    session_id: 'SESSION-TEST-XYZ',
    events_in_session: 4,
    time_pressure_detected: true,
    rapid_escalation_detected: true,
    channel_migration_detected: true,
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

describe('Phase 12.2 — Complete Firewall Analysis Workflow & Results', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.location.hash = '';
  });

  // Test 1 — Empty submission
  it('Test 1: Cannot submit empty content (button disabled and validation enforced)', () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    render(<App />);

    const submitBtn = screen.getByRole('button', { name: /Analyze Content/i });
    expect(submitBtn).toBeDisabled();
  });

  // Test 2 — Valid submission
  it('Test 2: Valid input calls real API client with correct parameters', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    const analyzeSpy = vi.spyOn(apiClient, 'analyze').mockResolvedValue(createMockResponse());
    const user = userEvent.setup();

    render(<App />);

    const input = screen.getByLabelText('Message or Financial Content');
    await user.type(input, 'SEBI registered Rahul Sharma guaranteed 40% returns');

    const submitBtn = screen.getByRole('button', { name: /Analyze Content/i });
    expect(submitBtn).not.toBeDisabled();
    await user.click(submitBtn);

    expect(analyzeSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        input_type: 'text',
        text: 'SEBI registered Rahul Sharma guaranteed 40% returns',
        channel: 'web',
      })
    );
  });

  // Test 3 — API success renders result screen
  it('Test 3: API success transitions from input to primary analysis result screen', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    vi.spyOn(apiClient, 'analyze').mockResolvedValue(createMockResponse());
    const user = userEvent.setup();

    render(<App />);

    const input = screen.getByLabelText('Message or Financial Content');
    await user.type(input, 'Sample investment claim');
    await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

    await waitFor(() => {
      expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
      expect(screen.getByText('ORCH-MOCK-TEST-001')).toBeInTheDocument();
    });
  });

  // Test 4 — ALLOW result
  it('Test 4: Displays ALLOW status and verified neutral presentation from Engine 8', () => {
    const mockAllow = createMockResponse({
      decision: {
        decision: 'ALLOW',
        severity: 'INFORMATIONAL',
        primary_reason: 'Content contains educational financial concepts without solicitation.',
        reason_codes: ['NEUTRAL_FINANCIAL_CONTENT'],
        explanation: {
          decision: 'ALLOW',
          user_message: 'This content appears to be informational. No high-risk action detected.',
          technical_message: 'All checks passed neutral.',
          primary_reason: 'Content contains educational financial concepts.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={mockAllow} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ACTION PERMITTED — VERIFIED NEUTRAL')).toBeInTheDocument();
    expect(screen.getByText('Allow / Verified Neutral')).toBeInTheDocument();
    expect(screen.getByText(/This content appears to be informational/i)).toBeInTheDocument();
  });

  // Test 5 — INFORM result
  it('Test 5: Displays INFORM status and informational advisory presentation', () => {
    const mockInform = createMockResponse({
      decision: {
        decision: 'INFORM',
        severity: 'LOW',
        primary_reason: 'General advisory regarding unregistered advice.',
        reason_codes: ['INFORMATIONAL_ADVISORY'],
        explanation: {
          decision: 'INFORM',
          user_message: 'Be aware that social media tips may not be suitable for your profile.',
          technical_message: 'General advisory.',
          primary_reason: 'General advisory.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={mockInform} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('INFORMATIONAL ADVISORY')).toBeInTheDocument();
    expect(screen.getByText('Inform / Advisory')).toBeInTheDocument();
  });

  // Test 6 — WARN result
  it('Test 6: Displays WARN status and caution explanation from backend', () => {
    const mockWarn = createMockResponse({
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

    render(<AnalysisResultView analysis={mockWarn} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('CAUTION RECOMMENDED')).toBeInTheDocument();
    expect(screen.getByText('Warning / Caution Required')).toBeInTheDocument();
    expect(screen.getByText(/Exercise caution before joining private investment groups/i)).toBeInTheDocument();
  });

  // Test 7 — PAUSE result
  it('Test 7: Displays PAUSE status and explicit confirmation requirement', () => {
    const mockPause = createMockResponse();

    render(<AnalysisResultView analysis={mockPause} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
    expect(screen.getByText('Pause / Confirmation Required')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent(/Explicit Confirmation Required/i);
    expect(screen.getByText(/Recommended cooldown pause: 30 seconds/i)).toBeInTheDocument();
  });

  // Test 8 — BLOCK result
  it('Test 8: Displays BLOCK status and threat prevented presentation', () => {
    const mockBlock = createMockResponse({
      decision: {
        decision: 'BLOCK',
        severity: 'CRITICAL',
        primary_reason: 'Severe multi-signal scam pattern with fraudulent APK download.',
        reason_codes: ['RULE-BLOCK-01', 'MALICIOUS_DOWNLOAD'],
        explanation: {
          decision: 'BLOCK',
          user_message: 'This action has been blocked to prevent immediate loss.',
          technical_message: 'Terminal attack-path stage reached.',
          primary_reason: 'Severe multi-signal scam pattern.',
          supporting_signals: ['MALICIOUS_APP', 'CREDENTIAL_THEFT'],
        },
        actions_required: ['TERMINATE_ACTION'],
        required_user_confirmation: true,
        policy_version: '8.0.0',
      },
    });

    render(<AnalysisResultView analysis={mockBlock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ACTION BLOCKED — THREAT PREVENTED')).toBeInTheDocument();
    expect(screen.getByText('Blocked / Threat Prevented')).toBeInTheDocument();
    expect(screen.getByText(/This action has been blocked to prevent immediate loss/i)).toBeInTheDocument();
  });

  // Test 9 — Backend error handling
  it('Test 9: Surfaces safe error UI when backend call fails', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    vi.spyOn(apiClient, 'analyze').mockRejectedValue(
      new FirewallClientError({
        error_code: 'INPUT_TOO_LARGE',
        message: 'Payload text exceeds maximum permitted limit.',
      })
    );
    const user = userEvent.setup();

    render(<App />);

    const input = screen.getByLabelText('Message or Financial Content');
    await user.type(input, 'Large input text');
    await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

    await waitFor(() => {
      expect(screen.getByText('Analysis Could Not Be Completed')).toBeInTheDocument();
      expect(screen.getAllByText('Payload text exceeds maximum permitted limit.').length).toBeGreaterThan(0);
      expect(screen.getByText(/Error Code: INPUT_TOO_LARGE/i)).toBeInTheDocument();
    });
  });

  // Test 10 — Loading state prevents duplicate submissions
  it('Test 10: Prevents duplicate submissions while analysis is in progress', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    let resolveAnalysis: (val: FirewallAnalysisResponse) => void;
    const delayedPromise = new Promise<FirewallAnalysisResponse>((resolve) => {
      resolveAnalysis = resolve;
    });
    const analyzeSpy = vi.spyOn(apiClient, 'analyze').mockReturnValue(delayedPromise);
    const user = userEvent.setup();

    render(<App />);

    const input = screen.getByLabelText('Message or Financial Content');
    await user.type(input, 'Testing double click prevention');

    const submitBtn = screen.getByRole('button', { name: /Analyze Content/i });
    await user.click(submitBtn);

    // Now in loading state
    expect(screen.getByText(/Analyzing financial interaction across firewall pipeline/i)).toBeInTheDocument();
    expect(analyzeSpy).toHaveBeenCalledTimes(1);

    // Resolve delayed response
    await act(async () => {
      resolveAnalysis!(createMockResponse());
    });

    await waitFor(() => {
      expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
    });
  });

  // Test 11 — Claims rendering
  it('Test 11: Correctly displays canonical atomic claims from Engine 2 and verification status', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('"Guaranteed 40% monthly returns"')).toBeInTheDocument();
    expect(screen.getByText('"SEBI registered research analyst Rahul Sharma"')).toBeInTheDocument();
    expect(screen.getAllByText('CONTRADICTED').length).toBeGreaterThan(0);
  });

  // Test 12 — Actions rendering
  it('Test 12: Correctly displays requested user actions, impact category, and reversibility', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('DOWNLOAD')).toBeInTheDocument();
    expect(screen.getByText('TRANSFER_MONEY')).toBeInTheDocument();
    expect(screen.getAllByText('IRREVERSIBLE').length).toBeGreaterThan(0);
    expect(screen.getByText('Urgency Detected')).toBeInTheDocument();
  });

  // Test 13 — Evidence rendering
  it('Test 13: Evidence breakdown preserves granular states (SUPPORTED, CONTRADICTED, INSUFFICIENT)', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('Evidence Verification')).toBeInTheDocument();
    expect(screen.getByText('Contradicted Claims')).toBeInTheDocument();
    expect(screen.getByText('Insufficient Evidence')).toBeInTheDocument();
    expect(screen.getByText('Source Filings Retrieved')).toBeInTheDocument();
  });

  // Test 14 — Identity rendering
  it('Test 14: Preserves exact identity verification status (NOT_ESTABLISHED) without converting to scam labels', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('Entity Identity Resolution')).toBeInTheDocument();
    expect(screen.getAllByText('NOT_ESTABLISHED').length).toBeGreaterThan(0);
    expect(screen.getByText('Rahul Sharma')).toBeInTheDocument();
    expect(screen.getByText(/Registration number does not match official SEBI intermediary database/i)).toBeInTheDocument();
  });

  // Test 15 — Threat rendering
  it('Test 15: Renders attack stage progression and threat signals from Engine 6', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('Threat & Attack-Path Analysis')).toBeInTheDocument();
    expect(screen.getByText('CHANNEL_MIGRATION → FINANCIAL_EXTRACTION')).toBeInTheDocument();
    expect(screen.getByText('SOFTWARE_INSTALLATION')).toBeInTheDocument();
    expect(screen.getByText('FINANCIAL_REQUEST')).toBeInTheDocument();
  });

  // Test 16 — Fingerprint rendering
  it('Test 16: Renders structural fingerprint match and equivalence from Engine 7', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('Scam Fingerprint Intelligence')).toBeInTheDocument();
    expect(screen.getAllByText('SEMANTIC_VARIANT').length).toBeGreaterThan(0);
    expect(screen.getByText('YES (Known Template Structure)')).toBeInTheDocument();
    expect(screen.getByText(/42 sightings across 3 channels/i)).toBeInTheDocument();
  });

  // Test 17 — Behaviour rendering
  it('Test 17: Displays behavioural signals without adding psychological labels', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('Behavioural Signal Intelligence')).toBeInTheDocument();
    expect(screen.getByText('Time Pressure / Urgency')).toBeInTheDocument();
    expect(screen.getByText('Rapid Action Escalation')).toBeInTheDocument();
    expect(screen.getByText('Off-Platform Migration')).toBeInTheDocument();
    expect(screen.getByText(/Severe urgency detected/i)).toBeInTheDocument();
  });

  // Test 18 — Privacy boundary
  it('Test 18: Ensures forbidden sensitive fields (passwords, PINs, OTPs, raw card numbers) are not shown', () => {
    const mock = createMockResponse();
    const { container } = render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    const htmlContent = container.innerHTML.toLowerCase();
    expect(htmlContent).not.toContain('cvv');
    expect(htmlContent).not.toContain('otp');
    expect(htmlContent).not.toContain('pin');
    expect(htmlContent).not.toContain('card_number');
    expect(htmlContent).not.toContain('raw_credentials');
  });

  // Test 19 — Session correlation
  it('Test 19: Retains session and analysis correlation metadata', () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    expect(screen.getByText('ORCH-MOCK-TEST-001')).toBeInTheDocument();
    expect(screen.getAllByText('telegram').length).toBeGreaterThan(0);
  });

  // Test 20 — Analyze another returns to input state
  it('Test 20: "Analyze Another Content" button returns cleanly to clean input state', async () => {
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    vi.spyOn(apiClient, 'analyze').mockResolvedValue(createMockResponse());
    const user = userEvent.setup();

    render(<App />);

    const input = screen.getByLabelText('Message or Financial Content');
    await user.type(input, 'First analysis');
    await user.click(screen.getByRole('button', { name: /Analyze Content/i }));

    await waitFor(() => {
      expect(screen.getByText('ACTION PAUSED — VERIFICATION REQUIRED')).toBeInTheDocument();
    });

    const anotherBtn = screen.getByRole('button', { name: /Analyze Another Content/i });
    await user.click(anotherBtn);

    expect(screen.getByText('Protect your next financial action')).toBeInTheDocument();
    expect(screen.queryByText('ACTION PAUSED — VERIFICATION REQUIRED')).not.toBeInTheDocument();
  });

  // Test 21 — Retrieval by ID without re-executing pipeline
  it('Test 21: Deep-linked analysis ID retrieves existing analysis without rerun', async () => {
    window.location.hash = '#protect?id=ORCH-CACHED-999';
    vi.spyOn(apiClient, 'checkHealth').mockResolvedValue({ status: 'active' });
    const getAnalysisSpy = vi.spyOn(apiClient, 'getAnalysis').mockResolvedValue(
      createMockResponse({
        analysis_id: 'ORCH-CACHED-999',
      })
    );
    const analyzeSpy = vi.spyOn(apiClient, 'analyze');

    await act(async () => {
      render(<App />);
    });

    await waitFor(() => {
      expect(screen.getByText('ORCH-CACHED-999')).toBeInTheDocument();
    });

    expect(getAnalysisSpy).toHaveBeenCalledWith('ORCH-CACHED-999');
    expect(analyzeSpy).not.toHaveBeenCalled();
  });

  // Test 22 — Accessibility
  it('Test 22: Analysis result controls and accordion toggles are accessible with keyboard', async () => {
    const mock = createMockResponse();
    render(<AnalysisResultView analysis={mock} onAnalyzeAnother={() => {}} />);

    const accordionButtons = screen.getAllByRole('button', { expanded: true });
    expect(accordionButtons.length).toBeGreaterThan(0);

    const copyBtn = screen.getByLabelText('Copy Analysis ID');
    expect(copyBtn).toBeInTheDocument();

    const anotherBtn = screen.getByRole('button', { name: /Analyze Another Content/i });
    expect(anotherBtn).toBeInTheDocument();
  });
});
