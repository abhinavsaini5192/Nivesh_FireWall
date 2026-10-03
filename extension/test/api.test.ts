import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ExtensionApiClient, ExtensionApiClientError } from '../src/api/client';
import { buildNiveshWebAppUrl } from '../src/config';

describe('Extension API Client & Web App Deep Linking (Phase 13.1 Sections 12, 13, 14, 15, 23)', () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  it('constructs safe deep-links to Nivesh Web App with analysis ID without sensitive data', () => {
    const url1 = buildNiveshWebAppUrl('http://localhost:5173', 'EXT-ANA-98765');
    expect(url1).toBe('http://localhost:5173/#protect?id=EXT-ANA-98765');

    // Strips trailing slashes cleanly
    const url2 = buildNiveshWebAppUrl('https://app.nivesh.ai///', 'FW-2026-001');
    expect(url2).toBe('https://app.nivesh.ai/#protect?id=FW-2026-001');

    // Without analysis ID
    const url3 = buildNiveshWebAppUrl('http://localhost:5173');
    expect(url3).toBe('http://localhost:5173/#protect');

    // Does NOT include raw query parameters or text payloads
    expect(url1).not.toContain('text=');
    expect(url1).not.toContain('password=');
    expect(url1).not.toContain('otp=');
  });

  it('performs health check probe against GET /api/v1/health', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: 'healthy', version: '1.0.0' }),
    } as Response);

    const client = new ExtensionApiClient('http://localhost:8000');
    const health = await client.checkHealth();

    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/health',
      expect.objectContaining({ method: 'GET' })
    );
    expect(health.isAvailable).toBe(true);
    expect(health.status).toBe('healthy');
  });

  it('dispatches inspection request to POST /api/v1/firewall/analyze', async () => {
    const mockApiResponse = {
      analysis_id: 'ANA-2026-4412',
      completed_at: '2026-10-03T07:45:00Z',
      decision: {
        decision: 'WARN',
        severity: 'HIGH',
        primary_reason: 'High-risk unverified financial scheme detected.',
      },
      timing_ms: 12.4,
    };

    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockApiResponse),
    } as Response);

    const client = new ExtensionApiClient('http://localhost:8000');
    const result = await client.analyze({
      input_type: 'url',
      url: 'https://dubious-returns.com',
      channel: 'web',
      session_id: 'EXT-REQ-101',
    });

    expect(globalThis.fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/firewall/analyze',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          'Content-Type': 'application/json',
        }),
      })
    );

    // Verifies body payload sent to Unified API
    const callArgs = (globalThis.fetch as any).mock.calls[0];
    const sentBody = JSON.parse(callArgs[1].body);
    expect(sentBody.input_type).toBe('url');
    expect(sentBody.url).toBe('https://dubious-returns.com');
    expect(sentBody.channel).toBe('web');
    expect(sentBody.session_id).toBe('EXT-REQ-101');

    // Verifies normalized result
    expect(result.analysisId).toBe('ANA-2026-4412');
    expect(result.decision).toBe('WARN');
    expect(result.severity).toBe('HIGH');
    expect(result.primaryReason).toBe('High-risk unverified financial scheme detected.');
    expect(result.webAppUrl).toContain('ANA-2026-4412');
  });

  it('maps backend 400 validation errors cleanly to ExtensionApiClientError', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () =>
        Promise.resolve({
          error_code: 'INVALID_INPUT',
          message: 'Both text and url cannot be empty.',
        }),
    } as Response);

    const client = new ExtensionApiClient('http://localhost:8000');

    await expect(
      client.analyze({ input_type: 'text', text: '' })
    ).rejects.toThrowError(ExtensionApiClientError);

    try {
      await client.analyze({ input_type: 'text', text: '' });
    } catch (err: any) {
      expect(err.code).toBe('INVALID_INPUT');
      expect(err.statusCode).toBe(400);
      expect(err.message).toBe('Both text and url cannot be empty.');
    }
  });

  it('handles backend network unavailability gracefully without raw stack traces', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new Error('Failed to fetch (connection refused)'));

    const client = new ExtensionApiClient('http://localhost:8000');

    try {
      await client.analyze({ input_type: 'url', url: 'https://example.com' });
      expect.unreachable('Should have thrown an error');
    } catch (err: any) {
      expect(err).toBeInstanceOf(ExtensionApiClientError);
      expect(err.code).toBe('BACKEND_UNAVAILABLE');
      expect(err.message).toBe('Could not connect to Nivesh Firewall service.');
    }
  });
});
