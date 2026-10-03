import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FirewallApiClient, FirewallClientError } from '../api/client';
import type { FirewallAnalysisResponse, FirewallApiError } from '../types/firewall';

describe('Nivesh Firewall API Client Foundation', () => {
  let client: FirewallApiClient;

  beforeEach(() => {
    vi.restoreAllMocks();
    client = new FirewallApiClient('http://test-firewall.local:8000');
  });

  it('1. Initializes with configured base URL without trailing slashes', () => {
    const custom = new FirewallApiClient('http://test-firewall.local:8000///');
    expect(custom.getBaseUrl()).toBe('http://test-firewall.local:8000');
  });

  it('2. Checks backend health and maps HTTP 200 to active status', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'healthy', version: '1.0.0' }),
    } as Response);

    const result = await client.checkHealth();
    expect(result.status).toBe('active');
    expect(result.data?.status).toBe('healthy');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://test-firewall.local:8000/health',
      expect.objectContaining({ method: 'GET' })
    );
  });

  it('3. Maps network errors to unavailable protection status', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Connection refused'));

    const result = await client.checkHealth();
    expect(result.status).toBe('unavailable');
  });

  it('4. Successfully posts to /api/v1/firewall/analyze and parses response', async () => {
    const mockResponse: Partial<FirewallAnalysisResponse> = {
      analysis_id: 'ORCH-TEST-1234',
      pipeline_status: 'COMPLETED',
      decision: {
        decision: 'ALLOW',
        severity: 'INFORMATIONAL',
        primary_reason: 'Content is verified neutral.',
        reason_codes: ['NEUTRAL_FINANCIAL_CONTENT'],
        explanation: {
          decision: 'ALLOW',
          user_message: 'Content is verified.',
          technical_message: 'All checks passed.',
          primary_reason: 'Content is verified neutral.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '8.0.0',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const response = await client.analyze({
      input_type: 'text',
      text: 'Learn how mutual funds work.',
      channel: 'web',
    });

    expect(response.analysis_id).toBe('ORCH-TEST-1234');
    expect(response.decision.decision).toBe('ALLOW');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://test-firewall.local:8000/api/v1/firewall/analyze',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({ 'Content-Type': 'application/json' }),
      })
    );
  });

  it('5. Properly intercepts and wraps backend 400/500 errors into FirewallClientError without leaking internals', async () => {
    const mockError: FirewallApiError = {
      error_code: 'INPUT_TOO_LARGE',
      message: 'Payload text exceeds maximum permitted limit.',
      details: { max_limit: 50000 },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => mockError,
    } as Response);

    await expect(
      client.analyze({
        input_type: 'text',
        text: 'A'.repeat(60000),
      })
    ).rejects.toThrowError(FirewallClientError);

    try {
      await client.analyze({ input_type: 'text', text: 'large' });
    } catch (err) {
      const clientErr = err as FirewallClientError;
      expect(clientErr.errorCode).toBe('INPUT_TOO_LARGE');
      expect(clientErr.message).toBe('Payload text exceeds maximum permitted limit.');
      expect(clientErr.details).toEqual({ max_limit: 50000 });
    }
  });

  it('6. Retrieves prior analysis result by ID from /api/v1/firewall/analysis/{id}', async () => {
    const mockResponse: Partial<FirewallAnalysisResponse> = {
      analysis_id: 'ORCH-CACHED-777',
      pipeline_status: 'COMPLETED',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const response = await client.getAnalysis('ORCH-CACHED-777');
    expect(response.analysis_id).toBe('ORCH-CACHED-777');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://test-firewall.local:8000/api/v1/firewall/analysis/ORCH-CACHED-777',
      expect.objectContaining({ method: 'GET' })
    );
  });
});
