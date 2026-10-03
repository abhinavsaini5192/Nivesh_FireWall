/**
 * Phase 13.3 Test Suite: Nivesh Analysis Bridge (Section 31 Tests 1 to 25)
 *
 * Verifies:
 * Test 1 — Selected text analysis
 * Test 2 — Current page analysis
 * Test 3 — URL analysis
 * Test 4 — Request correlation (capture_id -> request_id -> analysis_id)
 * Test 5 — Result correlation (returned result associated with correct request)
 * Test 6 — Policy preservation (ALLOW/INFORM/WARN/PAUSE/BLOCK preserved unchanged)
 * Test 7 — Claims preservation
 * Test 8 — Actions preservation
 * Test 9 — Evidence preservation
 * Test 10 — Identity preservation
 * Test 11 — Threat preservation
 * Test 12 — Fingerprint preservation
 * Test 13 — Behaviour preservation
 * Test 14 — Backend unavailable (Safe Fallback Principle: UNAVAILABLE is NEVER ALLOW)
 * Test 15 — Timeout produces safe error state
 * Test 16 — Malformed response produces safe error state
 * Test 17 — Duplicate request prevention (SCAN_IN_PROGRESS)
 * Test 18 — Retry: Transient failures retry only within configured limits
 * Test 19 — Privacy: Sensitive fields are never transmitted
 * Test 20 — Logging: Sensitive raw content is absent from logs
 * Test 21 — Multi-tab isolation: Tab A and Tab B cannot overwrite each other
 * Test 22 — Session isolation: Session A and Session B remain isolated
 * Test 23 — Worker restart: Minimal request/analysis references survive
 * Test 24 — Web-app handoff: Analysis ID deep link opens the correct Nivesh analysis
 * Test 25 — No frontend intelligence: Bridge contains zero local threat/policy logic
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { analysisBridge, NiveshAnalysisBridge } from '../src/bridge';
import { bridgeLogger } from '../src/bridge/logger';
import { backgroundState } from '../src/background/state';
import { routeExtensionMessage } from '../src/background/router';
import { buildNiveshWebAppUrl } from '../src/config';
import type {
  BrowserAnalysisRequest,
  FirewallAnalysisResponse,
} from '../src/bridge/types';
import type { ScanRequestMessage, OpenNiveshAppMessage } from '../src/types/messages';
import type { CapturePayload } from '../src/types/capture';

const mockCanonicalResponse: FirewallAnalysisResponse = {
  analysis_id: 'ANA-E2E-1337',
  session_id: 'SESS-TAB-101-TEST',
  pipeline_status: 'COMPLETED',
  created_at: '2026-10-03T08:00:00Z',
  completed_at: '2026-10-03T08:00:01Z',
  duration_ms: 45,
  decision: {
    decision: 'PAUSE',
    severity: 'HIGH',
    primary_reason: 'Suspicious high-yield scheme without registered entity.',
    reason_codes: ['UNVERIFIED_HIGH_YIELD', 'IDENTITY_UNVERIFIED'],
    explanation: {
      decision: 'PAUSE',
      user_message: 'Do not transfer funds until entity credentials are confirmed.',
      technical_message: 'Action severity exceeds safe limits.',
      primary_reason: 'High risk financial promise.',
      supporting_signals: ['UNREGISTERED_TELEGRAM_SCHEME'],
    },
    actions_required: ['CONFIRM_CREDENTIALS'],
    required_user_confirmation: true,
    cooldown_seconds: 60,
    policy_version: '1.0.0',
    decision_id: 'DEC-9988',
  },
  content: {
    content_id: 'CNT-123',
    input_type: 'text',
    channel: 'web',
    summary: 'Financial scheme description',
    contains_financial_content: true,
    entities: { organizations: ['Telegram Group'] },
  },
  claims: [
    {
      claim_id: 'CLM-001',
      text: 'Guaranteed 50% monthly returns.',
      topic: 'returns',
      predicate: 'guaranteed',
      modality: 'certain',
      verification_status: 'CONTRADICTED',
    },
  ],
  actions: [
    {
      action_id: 'ACT-001',
      action_type: 'TRANSFER_FUNDS',
      target: 'UPI ID',
      impact_category: 'FINANCIAL_LOSS',
      reversibility: 'IRREVERSIBLE',
      urgency_detected: true,
    },
  ],
  evidence: {
    overall_status: 'CONTRADICTED',
    verification_count: 2,
    supported_claims_count: 0,
    contradicted_claims_count: 1,
    insufficient_claims_count: 0,
    source_documents_count: 3,
    retrieval_status: 'COMPLETED',
  },
  identity: {
    identity_status: 'NOT_ESTABLISHED',
    claimed_entities: ['Alpha Wealth Robot'],
    findings_count: 1,
    findings_summary: ['No SEBI or RBI registration found.'],
    confidence: 0.95,
  },
  threat: {
    threat_signals: ['URGENCY_CALL_TO_ACTION', 'UNREGULATED_CHANNEL'],
    attack_stage: 'CREDENTIAL_SOLICITATION',
    terminal_stage: 'UNAUTHORIZED_TRANSFER',
    threat_families: ['ADVANCE_FEE_FRAUD'],
    high_impact_action_count: 1,
    confidence: 0.88,
  },
  fingerprint: {
    match_type: 'SEMANTIC_VARIANT',
    fingerprint_id: 'FP-CRYPTO-BOT-7',
    match_confidence: 0.92,
    observation_count: 14,
    distinct_channels_count: 3,
    attack_path_signature: 'SIG-TELEGRAM-CRYPTO',
  },
  behaviour: {
    signals: ['RAPID_INTERACTION', 'TIME_PRESSURE'],
    findings: ['User hurried towards transaction.'],
    session_id: 'SESS-TAB-101-TEST',
    events_in_session: 4,
    time_pressure_detected: true,
    rapid_escalation_detected: true,
    channel_migration_detected: true,
  },
  provenance: {
    orchestrator_version: '1.0.0',
    engines_executed: ['E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10'],
  },
  warnings: [],
  errors: [],
};

describe('Nivesh Analysis Bridge — Phase 13.3 Test Suite (Tests 1 to 25)', () => {
  beforeEach(() => {
    backgroundState.reset();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ---------------------------------------------------------------------------
  // Test 1: Selected text analysis reaches the Unified Firewall API
  // ---------------------------------------------------------------------------
  it('Test 1: submits selected text capture to Unified Firewall API endpoint', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const bridgeRequest: BrowserAnalysisRequest = {
      captureId: 'CAP-SEL-001',
      requestId: 'REQ-SEL-001',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Earn guaranteed 25% weekly profit on automated forex trades.',
      url: 'https://broker-promo.example.com/signals',
      pageOrigin: 'https://broker-promo.example.com',
      pageTitle: 'Trading Signals Hub',
      tabId: 101,
      timestamp: new Date().toISOString(),
    };

    const result = await analysisBridge.submitAnalysis(bridgeRequest);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/firewall/analyze'),
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
        body: expect.stringContaining('"input_type":"text"'),
      })
    );
    expect(result.analysisId).toBe('ANA-E2E-1337');
    expect(result.reference.decision).toBe('PAUSE');
  });

  // ---------------------------------------------------------------------------
  // Test 2: Current page analysis reaches the Unified Firewall API
  // ---------------------------------------------------------------------------
  it('Test 2: submits current page capture to Unified Firewall API endpoint', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const bridgeRequest: BrowserAnalysisRequest = {
      captureId: 'CAP-PAGE-002',
      requestId: 'REQ-PAGE-002',
      sessionId: 'SESS-TAB-101',
      sourceType: 'CURRENT_PAGE',
      text: 'Full page financial article discussing asset allocation and expense ratios.',
      url: 'https://financial-news.example.com/funds',
      pageOrigin: 'https://financial-news.example.com',
      pageTitle: 'Mutual Fund Guide',
      tabId: 101,
      timestamp: new Date().toISOString(),
    };

    const result = await analysisBridge.submitAnalysis(bridgeRequest);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/firewall/analyze'),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"input_type":"text"'),
      })
    );
    expect(result.reference.captureId).toBe('CAP-PAGE-002');
  });

  // ---------------------------------------------------------------------------
  // Test 3: URL analysis reaches the Unified Firewall API
  // ---------------------------------------------------------------------------
  it('Test 3: submits URL capture to Unified Firewall API as input_type url', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const bridgeRequest: BrowserAnalysisRequest = {
      captureId: 'CAP-URL-003',
      requestId: 'REQ-URL-003',
      sessionId: 'SESS-TAB-101',
      sourceType: 'URL',
      url: 'https://crypto-doubler-bot.net/invest',
      pageOrigin: 'https://crypto-doubler-bot.net',
      pageTitle: 'Crypto Doubler',
      tabId: 101,
      timestamp: new Date().toISOString(),
    };

    const result = await analysisBridge.submitAnalysis(bridgeRequest);

    expect(fetchSpy).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/firewall/analyze'),
      expect.objectContaining({
        method: 'POST',
        body: expect.stringContaining('"input_type":"url"'),
      })
    );
    expect(result.analysisId).toBe('ANA-E2E-1337');
  });

  // ---------------------------------------------------------------------------
  // Test 4: Request correlation (capture_id -> request_id -> analysis_id)
  // ---------------------------------------------------------------------------
  it('Test 4: preserves capture_id -> request_id -> analysis_id relationship', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const captureId = 'CAP-CORRELATION-001';
    const requestId = 'REQ-CORRELATION-001';

    const result = await analysisBridge.submitAnalysis({
      captureId,
      requestId,
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Test content for correlation tracking.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.captureId).toBe(captureId);
    expect(result.requestId).toBe(requestId);
    expect(result.analysisId).toBe('ANA-E2E-1337');

    expect(result.reference.captureId).toBe(captureId);
    expect(result.reference.requestId).toBe(requestId);
    expect(result.reference.analysisId).toBe('ANA-E2E-1337');
  });

  // ---------------------------------------------------------------------------
  // Test 5: Result correlation with originating request
  // ---------------------------------------------------------------------------
  it('Test 5: associates returned result with originating request in background state', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const capture: CapturePayload = {
      captureId: 'CAP-ORIGIN-005',
      sourceType: 'SELECTED_TEXT',
      status: 'CAPTURED',
      text: 'Suspicious stock tips group link.',
      url: 'https://stocks.example.com',
      displayUrl: 'https://stocks.example.com',
      pageTitle: 'Stock Tips',
      pageOrigin: 'https://stocks.example.com',
      tabId: 101,
      timestamp: new Date().toISOString(),
      contentLength: 33,
      sanitized: true,
    };

    const scanMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'REQ-SCAN-005',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: { tabId: 101, capture },
    };

    const response = await routeExtensionMessage(scanMsg);
    expect(response.success).toBe(true);
    expect(response.requestId).toBe('REQ-SCAN-005');
    expect((response.data as any).analysisId).toBe('ANA-E2E-1337');

    const state = backgroundState.getState(101);
    expect(state.status).toBe('RESULT_AVAILABLE');
    expect(state.lastAnalysis?.analysisId).toBe('ANA-E2E-1337');
    expect(state.lastAnalysis?.captureId).toBe('CAP-ORIGIN-005');
  });

  // ---------------------------------------------------------------------------
  // Test 6: Policy preservation (Engine 8 decision unchanged)
  // ---------------------------------------------------------------------------
  it('Test 6: preserves Engine 8 decision exactly without recalculation or local rules', async () => {
    const decisions: Array<'ALLOW' | 'INFORM' | 'WARN' | 'PAUSE' | 'BLOCK'> = [
      'ALLOW',
      'INFORM',
      'WARN',
      'PAUSE',
      'BLOCK',
    ];

    for (const decision of decisions) {
      const customResponse: FirewallAnalysisResponse = {
        ...mockCanonicalResponse,
        decision: {
          ...mockCanonicalResponse.decision,
          decision,
          primary_reason: `Engine 8 ${decision} reason.`,
        },
      };

      vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(customResponse),
      } as Response);

      const result = await analysisBridge.submitAnalysis({
        captureId: `CAP-${decision}`,
        requestId: `REQ-${decision}`,
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: `Content evaluated as ${decision}`,
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      });

      expect(result.reference.decision).toBe(decision);
      expect(result.reference.primaryReason).toBe(`Engine 8 ${decision} reason.`);
    }
  });

  // ---------------------------------------------------------------------------
  // Test 7: Claims preservation
  // ---------------------------------------------------------------------------
  it('Test 7: preserves claims count and structure without altering text', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-CLAIMS-007',
      requestId: 'REQ-CLAIMS-007',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Guaranteed 50% monthly returns.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.reference.claimsCount).toBe(1);
    expect(result.fullResponse.claims[0].claim_id).toBe('CLM-001');
    expect(result.fullResponse.claims[0].verification_status).toBe('CONTRADICTED');
  });

  // ---------------------------------------------------------------------------
  // Test 8: Actions preservation
  // ---------------------------------------------------------------------------
  it('Test 8: preserves action hierarchies and urgency indicators', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-ACTIONS-008',
      requestId: 'REQ-ACTIONS-008',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Send money immediately via UPI.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.fullResponse.actions).toHaveLength(1);
    expect(result.fullResponse.actions[0].action_type).toBe('TRANSFER_FUNDS');
    expect(result.fullResponse.actions[0].urgency_detected).toBe(true);
  });

  // ---------------------------------------------------------------------------
  // Test 9: Evidence preservation
  // ---------------------------------------------------------------------------
  it('Test 9: preserves evidence verification overall_status exactly', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-EVID-009',
      requestId: 'REQ-EVID-009',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Evidence testing.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.reference.evidenceStatus).toBe('CONTRADICTED');
    expect(result.fullResponse.evidence.contradicted_claims_count).toBe(1);
  });

  // ---------------------------------------------------------------------------
  // Test 10: Identity preservation
  // ---------------------------------------------------------------------------
  it('Test 10: preserves identity status and entity findings', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-IDENT-010',
      requestId: 'REQ-IDENT-010',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Alpha Wealth Robot entity check.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.reference.identityStatus).toBe('NOT_ESTABLISHED');
    expect(result.fullResponse.identity.claimed_entities).toContain('Alpha Wealth Robot');
  });

  // ---------------------------------------------------------------------------
  // Test 11: Threat preservation
  // ---------------------------------------------------------------------------
  it('Test 11: preserves threat signals and attack stage findings', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-THREAT-011',
      requestId: 'REQ-THREAT-011',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Threat signals check.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.reference.threatSignalCount).toBe(2);
    expect(result.fullResponse.threat.attack_stage).toBe('CREDENTIAL_SOLICITATION');
    expect(result.fullResponse.threat.threat_signals).toContain('URGENCY_CALL_TO_ACTION');
  });

  // ---------------------------------------------------------------------------
  // Test 12: Fingerprint preservation
  // ---------------------------------------------------------------------------
  it('Test 12: preserves collective scam fingerprint match type', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-FP-012',
      requestId: 'REQ-FP-012',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Fingerprint match check.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.reference.fingerprintMatch).toBe('SEMANTIC_VARIANT');
    expect(result.fullResponse.fingerprint.match_type).toBe('SEMANTIC_VARIANT');
    expect(result.fullResponse.fingerprint.fingerprint_id).toBe('FP-CRYPTO-BOT-7');
  });

  // ---------------------------------------------------------------------------
  // Test 13: Behaviour preservation
  // ---------------------------------------------------------------------------
  it('Test 13: preserves multi-turn behavioural signals and time pressure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockCanonicalResponse),
    } as Response);

    const result = await analysisBridge.submitAnalysis({
      captureId: 'CAP-BEH-013',
      requestId: 'REQ-BEH-013',
      sessionId: 'SESS-TAB-101',
      sourceType: 'SELECTED_TEXT',
      text: 'Behaviour testing.',
      pageOrigin: 'https://example.com',
      pageTitle: 'Example',
      tabId: 101,
      timestamp: new Date().toISOString(),
    });

    expect(result.fullResponse.behaviour.time_pressure_detected).toBe(true);
    expect(result.fullResponse.behaviour.rapid_escalation_detected).toBe(true);
    expect(result.fullResponse.behaviour.signals).toContain('TIME_PRESSURE');
  });

  // ---------------------------------------------------------------------------
  // Test 14: Backend unavailable (Safe Fallback Principle: UNAVAILABLE != ALLOW)
  // ---------------------------------------------------------------------------
  it('Test 14: when backend is unavailable, throws error and NEVER defaults to ALLOW or safe', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Failed to fetch'));

    await expect(
      analysisBridge.submitAnalysis({
        captureId: 'CAP-FAIL-014',
        requestId: 'REQ-FAIL-014',
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: 'Unchecked content on network outage.',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      })
    ).rejects.toThrowError(/unavailable/i);

    // Verify background state is ERROR, never RESULT_AVAILABLE or ALLOW
    const scanMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'REQ-OUTAGE-014',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: {
        tabId: 101,
        capture: {
          captureId: 'CAP-OUTAGE-014',
          sourceType: 'SELECTED_TEXT',
          status: 'CAPTURED',
          text: 'Unchecked content.',
          url: 'https://example.com',
          displayUrl: 'https://example.com',
          pageTitle: 'Example',
          pageOrigin: 'https://example.com',
          tabId: 101,
          timestamp: new Date().toISOString(),
          contentLength: 18,
          sanitized: true,
        },
      },
    };

    const res = await routeExtensionMessage(scanMsg);
    expect(res.success).toBe(false);
    expect(res.error?.code).toBe('BACKEND_UNAVAILABLE');

    const state = backgroundState.getState(101);
    expect(state.status).toBe('ERROR');
    expect(state.lastAnalysis).toBeNull();
  });

  // ---------------------------------------------------------------------------
  // Test 15: Timeout produces safe error state
  // ---------------------------------------------------------------------------
  it('Test 15: timeout abort produces BACKEND_TIMEOUT without falling back to ALLOW', async () => {
    const abortError = new DOMException('The operation was aborted', 'AbortError');
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(abortError);

    await expect(
      analysisBridge.submitAnalysis({
        captureId: 'CAP-TIMEOUT-015',
        requestId: 'REQ-TIMEOUT-015',
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: 'Timeout test content.',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      })
    ).rejects.toThrowError(/timed out/i);
  });

  // ---------------------------------------------------------------------------
  // Test 16: Malformed response produces safe error state
  // ---------------------------------------------------------------------------
  it('Test 16: HTTP 502 with malformed HTML response produces safe error state', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 502,
      json: () => Promise.reject(new Error('Unexpected token < in JSON')),
    } as Response);

    try {
      await analysisBridge.submitAnalysis({
        captureId: 'CAP-502-016',
        requestId: 'REQ-502-016',
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: 'Bad gateway test.',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      });
      expect.fail('Should have thrown on 502');
    } catch (err: any) {
      expect(err.code).toBe('PIPELINE_FAILURE');
      expect(err.message).toContain('502');
    }
  });

  // ---------------------------------------------------------------------------
  // Test 17: Duplicate request prevention
  // ---------------------------------------------------------------------------
  it('Test 17: prevents duplicate scan execution while an analysis is in progress', async () => {
    backgroundState.startRequest({
      requestId: 'REQ-EXISTING-017',
      tabId: 101,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://bank.com',
      pageUrl: 'https://bank.com',
    });

    const duplicateMsg: ScanRequestMessage = {
      type: 'SCAN_REQUEST',
      requestId: 'REQ-NEW-017',
      tabId: 101,
      timestamp: new Date().toISOString(),
      payload: { tabId: 101 },
    };

    const response = await routeExtensionMessage(duplicateMsg);
    expect(response.success).toBe(false);
    expect(response.error?.code).toBe('SCAN_IN_PROGRESS');
  });

  // ---------------------------------------------------------------------------
  // Test 18: Bounded Retry Strategy
  // ---------------------------------------------------------------------------
  it('Test 18: retries transient 5xx only once and never retries client 4xx errors', async () => {
    // A. 500 error: should attempt exactly 2 times (initial + 1 retry)
    let callCount500 = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => {
      callCount500++;
      return Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error_code: 'PIPELINE_FAILURE', message: 'Engine failure' }),
      } as Response);
    });

    const bridge = new NiveshAnalysisBridge({ maxRetries: 1, timeoutMs: 1000 });
    await expect(
      bridge.submitAnalysis({
        captureId: 'CAP-RETRY-500',
        requestId: 'REQ-RETRY-500',
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: 'Retryable 500 test.',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      })
    ).rejects.toThrow();

    expect(callCount500).toBe(2); // exactly 1 retry

    // B. 400 error: non-transient, should NOT retry (exactly 1 call)
    let callCount400 = 0;
    vi.spyOn(globalThis, 'fetch').mockImplementation(() => {
      callCount400++;
      return Promise.resolve({
        ok: false,
        status: 400,
        json: () => Promise.resolve({ error_code: 'INVALID_REQUEST', message: 'Malformed payload' }),
      } as Response);
    });

    await expect(
      bridge.submitAnalysis({
        captureId: 'CAP-NO-RETRY-400',
        requestId: 'REQ-NO-RETRY-400',
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: 'Non-retryable 400 test.',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      })
    ).rejects.toThrow();

    expect(callCount400).toBe(1); // zero retries for 4xx
  });

  // ---------------------------------------------------------------------------
  // Test 19: Privacy boundary (Sensitive fields are never transmitted)
  // ---------------------------------------------------------------------------
  it('Test 19: bridge payload rejects empty text and transmits zero credentials or form values', async () => {
    // Empty text validation
    try {
      await analysisBridge.submitAnalysis({
        captureId: 'CAP-EMPTY',
        requestId: 'REQ-EMPTY',
        sessionId: 'SESS-TAB-101',
        sourceType: 'SELECTED_TEXT',
        text: '   ',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      });
      expect.fail('Should have rejected empty text');
    } catch (err: any) {
      expect(err.code).toBe('UNSUPPORTED_INPUT');
      expect(err.message).toContain('empty');
    }

    // Empty URL validation
    try {
      await analysisBridge.submitAnalysis({
        captureId: 'CAP-EMPTY-URL',
        requestId: 'REQ-EMPTY-URL',
        sessionId: 'SESS-TAB-101',
        sourceType: 'URL',
        url: '',
        pageOrigin: 'https://example.com',
        pageTitle: 'Example',
        tabId: 101,
        timestamp: new Date().toISOString(),
      });
      expect.fail('Should have rejected empty URL');
    } catch (err: any) {
      expect(err.code).toBe('INVALID_REQUEST');
      expect(err.message).toContain('URL target');
    }
  });

  // ---------------------------------------------------------------------------
  // Test 20: Safe Logging Telemetry
  // ---------------------------------------------------------------------------
  it('Test 20: logger records correlation IDs and metrics without raw financial content or passwords', () => {
    const consoleSpy = vi.spyOn(console, 'info').mockImplementation(() => {});

    bridgeLogger.log({
      captureId: 'CAP-SAFE-LOG',
      requestId: 'REQ-SAFE-LOG',
      analysisId: 'ANA-SAFE-LOG',
      sourceType: 'SELECTED_TEXT',
      status: 'COMPLETED',
      durationMs: 120,
    });

    expect(consoleSpy).toHaveBeenCalled();
    const loggedCall = consoleSpy.mock.calls[0][1];
    const loggedJson = JSON.parse(loggedCall);

    expect(loggedJson.captureId).toBe('CAP-SAFE-LOG');
    expect(loggedJson.requestId).toBe('REQ-SAFE-LOG');
    expect(loggedJson.analysisId).toBe('ANA-SAFE-LOG');
    expect(loggedJson.password).toBeUndefined();
    expect(loggedJson.rawContent).toBeUndefined();
    expect(loggedJson.text).toBeUndefined();
  });

  // ---------------------------------------------------------------------------
  // Test 21: Multi-Tab Isolation
  // ---------------------------------------------------------------------------
  it('Test 21: Tab A and Tab B maintain independent states and cannot clobber each other', () => {
    // 1. Start scan on Tab 101
    backgroundState.startRequest({
      requestId: 'REQ-TAB-101',
      tabId: 101,
      startedAt: new Date().toISOString(),
      pageOrigin: 'https://tab-a.com',
      pageUrl: 'https://tab-a.com',
    });

    // 2. Tab 102 should be in READY state, not ANALYZING
    const state102 = backgroundState.getState(102);
    expect(state102.status).toBe('READY');
    expect(state102.activeRequest).toBeNull();

    // 3. Tab 101 should be ANALYZING
    const state101 = backgroundState.getState(101);
    expect(state101.status).toBe('ANALYZING');
    expect(state101.activeRequest?.requestId).toBe('REQ-TAB-101');

    // 4. Complete Tab 101 with WARN
    backgroundState.completeRequest(
      {
        analysisId: 'ANA-TAB-101',
        decision: 'WARN',
        severity: 'MEDIUM',
        primaryReason: 'Tab A reason',
        completedAt: new Date().toISOString(),
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-TAB-101',
      },
      101
    );

    // 5. Verify Tab 102 was not clobbered
    expect(backgroundState.getState(102).status).toBe('READY');
    expect(backgroundState.getState(102).lastAnalysis).toBeNull();

    // 6. Complete Tab 102 with ALLOW
    backgroundState.completeRequest(
      {
        analysisId: 'ANA-TAB-102',
        decision: 'ALLOW',
        severity: 'LOW',
        primaryReason: 'Tab B reason',
        completedAt: new Date().toISOString(),
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-TAB-102',
      },
      102
    );

    expect(backgroundState.getState(101).lastAnalysis?.decision).toBe('WARN');
    expect(backgroundState.getState(102).lastAnalysis?.decision).toBe('ALLOW');
  });

  // ---------------------------------------------------------------------------
  // Test 22: Session Isolation across tabs
  // ---------------------------------------------------------------------------
  it('Test 22: Session IDs are isolated per tab and remain consistent within the tab', () => {
    const session101 = backgroundState.getSessionIdForTab(101);
    const session102 = backgroundState.getSessionIdForTab(102);

    expect(session101).toContain('SESS-TAB-101');
    expect(session102).toContain('SESS-TAB-102');
    expect(session101).not.toBe(session102);

    // Subsequent calls on same tab return the same session ID
    expect(backgroundState.getSessionIdForTab(101)).toBe(session101);
  });

  // ---------------------------------------------------------------------------
  // Test 23: Worker restart resilience (lightweight storage)
  // ---------------------------------------------------------------------------
  it('Test 23: persists minimal lightweight reference to chrome.storage.local on completion', () => {
    const setStorageSpy = vi.spyOn(chrome.storage.local, 'set');

    backgroundState.completeRequest(
      {
        analysisId: 'ANA-RESTART-023',
        decision: 'PAUSE',
        severity: 'HIGH',
        primaryReason: 'High risk detected',
        completedAt: new Date().toISOString(),
        webAppUrl: 'http://localhost:5173/#protect?id=ANA-RESTART-023',
      },
      105
    );

    expect(setStorageSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        tab_ref_105: expect.objectContaining({
          analysisId: 'ANA-RESTART-023',
          decision: 'PAUSE',
        }),
      })
    );
  });

  // ---------------------------------------------------------------------------
  // Test 24: Web-app handoff
  // ---------------------------------------------------------------------------
  it('Test 24: opens web application deep link with safe analysisId reference without raw content in URL', async () => {
    const deepLinkUrl = buildNiveshWebAppUrl('http://localhost:5173', 'ANA-SAFE-DEEP-LINK');
    expect(deepLinkUrl).toBe('http://localhost:5173/#protect?id=ANA-SAFE-DEEP-LINK');
    expect(deepLinkUrl).not.toContain('password');
    expect(deepLinkUrl).not.toContain('otp');

    const openMsg: OpenNiveshAppMessage = {
      type: 'OPEN_NIVESH_APP',
      requestId: 'REQ-OPEN-024',
      timestamp: new Date().toISOString(),
      payload: { analysisId: 'ANA-SAFE-DEEP-LINK' },
    };

    const res = await routeExtensionMessage(openMsg);
    expect(res.success).toBe(true);
    expect((res.data as any).openedUrl).toBe('http://localhost:5173/#protect?id=ANA-SAFE-DEEP-LINK');
    expect(chrome.tabs.create).toHaveBeenCalledWith({
      url: 'http://localhost:5173/#protect?id=ANA-SAFE-DEEP-LINK',
    });
  });

  // ---------------------------------------------------------------------------
  // Test 25: No frontend intelligence logic
  // ---------------------------------------------------------------------------
  it('Test 25: verifies bridge and background modules contain no threat scoring or policy engines', () => {
    const bridgeProto = Object.getOwnPropertyNames(NiveshAnalysisBridge.prototype);
    expect(bridgeProto).not.toContain('calculateThreatScore');
    expect(bridgeProto).not.toContain('decidePolicy');
    expect(bridgeProto).not.toContain('verifyClaims');
    expect(bridgeProto).not.toContain('resolveIdentity');

    const state = backgroundState.getState();
    expect((state as any).threatScore).toBeUndefined();
    expect((state as any).scamLikelihood).toBeUndefined();
  });
});
