import { describe, it, expect, vi, beforeEach } from 'vitest';
import { FirewallApiClient, FirewallClientError } from '../api/client';
import type { FirewallAnalysisResponse, FirewallApiError } from '../types/firewall';

describe('Phase 16.4 — Frontend Production Configuration & Connectivity', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('1. Initializes with production HTTPS base URL without trailing slash', () => {
    const prodClient = new FirewallApiClient('https://api.nivesh.ai///');
    expect(prodClient.getBaseUrl()).toBe('https://api.nivesh.ai');
  });

  it('2. Supports relative API URL for reverse-proxy / same-origin deployment', () => {
    const relativeClient = new FirewallApiClient('');
    expect(relativeClient.getBaseUrl()).toBe('');
  });

  it('3. Successfully communicates with production HTTPS API and parses health probe', async () => {
    const client = new FirewallApiClient('https://api.nivesh.ai');

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ status: 'healthy', version: '1.0.0' }),
    } as Response);

    const health = await client.checkHealth();
    expect(health.status).toBe('active');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'https://api.nivesh.ai/health',
      expect.objectContaining({
        method: 'GET',
        headers: { Accept: 'application/json' },
      })
    );
  });

  it('4. Submits analysis request to production API endpoint with standard JSON contract', async () => {
    const client = new FirewallApiClient('https://api.nivesh.ai');

    const mockResponse: Partial<FirewallAnalysisResponse> = {
      analysis_id: 'ANA-PROD-2026-001',
      pipeline_status: 'COMPLETED',
      decision: {
        decision: 'ALLOW',
        severity: 'INFORMATIONAL',
        primary_reason: 'Authentic educational financial analysis verified.',
        reason_codes: ['BENIGN_CONTENT'],
        explanation: {
          decision: 'ALLOW',
          user_message: 'Verified authentic educational financial disclosure.',
          technical_message: 'Passed all verification layers.',
          primary_reason: 'Authentic educational financial analysis verified.',
          supporting_signals: [],
        },
        actions_required: [],
        required_user_confirmation: false,
        policy_version: '1.0.0',
      },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const result = await client.analyze({
      input_type: 'text',
      text: 'Understanding RBI repo rate mechanisms.',
      channel: 'web',
    });

    expect(result.analysis_id).toBe('ANA-PROD-2026-001');
    expect(result.decision.decision).toBe('ALLOW');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'https://api.nivesh.ai/api/v1/firewall/analyze',
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          input_type: 'text',
          text: 'Understanding RBI repo rate mechanisms.',
          channel: 'web',
        }),
      })
    );
  });

  it('5. Retrieves prior analysis record from production API by ID', async () => {
    const client = new FirewallApiClient('https://api.nivesh.ai');

    const mockRecord: Partial<FirewallAnalysisResponse> = {
      analysis_id: 'ANA-PROD-2026-999',
      pipeline_status: 'COMPLETED',
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => mockRecord,
    } as Response);

    const record = await client.getAnalysis('ANA-PROD-2026-999');
    expect(record.analysis_id).toBe('ANA-PROD-2026-999');
    expect(globalThis.fetch).toHaveBeenCalledWith(
      'https://api.nivesh.ai/api/v1/firewall/analysis/ANA-PROD-2026-999',
      expect.objectContaining({
        method: 'GET',
        headers: { Accept: 'application/json' },
      })
    );
  });

  it('6. Handles production API errors safely without leaking internal diagnostic details', async () => {
    const client = new FirewallApiClient('https://api.nivesh.ai');

    const errorPayload: FirewallApiError = {
      error_code: 'RATE_LIMIT_EXCEEDED',
      message: 'Too many requests. Rate limit exceeded.',
      details: { retry_after: 60 },
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 429,
      json: async () => errorPayload,
    } as Response);

    await expect(
      client.analyze({ input_type: 'text', text: 'Spam payload', channel: 'web' })
    ).rejects.toThrowError(FirewallClientError);

    try {
      await client.analyze({ input_type: 'text', text: 'Spam payload', channel: 'web' });
    } catch (err) {
      const clientErr = err as FirewallClientError;
      expect(clientErr.errorCode).toBe('RATE_LIMIT_EXCEEDED');
      expect(clientErr.message).toBe('Too many requests. Rate limit exceeded.');
      expect(clientErr.details).toEqual({ retry_after: 60 });
    }
  });
});
