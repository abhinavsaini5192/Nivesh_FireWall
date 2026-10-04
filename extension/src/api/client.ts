/**
 * Extension API Client (Phase 13.1 Section 12 & 23)
 *
 * Dedicated client communicating exclusively with the Unified Firewall API
 * (POST /api/v1/firewall/analyze). Does NOT call individual engines directly.
 */

import { getExtensionConfig, EXTENSION_METADATA, buildNiveshWebAppUrl } from '../config';
import type { LastAnalysisReference } from '../types/state';

export interface ExtensionAnalyzePayload {
  input_type: 'url' | 'text';
  text?: string;
  url?: string;
  channel?: string;
  session_id?: string;
}

export interface ExtensionApiError {
  code: string;
  message: string;
  statusCode?: number;
  details?: Record<string, unknown>;
}

export class ExtensionApiClientError extends Error {
  public code: string;
  public statusCode?: number;
  public details?: Record<string, unknown>;

  constructor(error: ExtensionApiError) {
    super(error.message);
    this.name = 'ExtensionApiClientError';
    this.code = error.code;
    this.statusCode = error.statusCode;
    this.details = error.details;
  }
}

export class ExtensionApiClient {
  private baseUrlOverride?: string;

  constructor(baseUrlOverride?: string) {
    this.baseUrlOverride = baseUrlOverride;
  }

  private async getBaseUrl(): Promise<string> {
    if (this.baseUrlOverride) {
      return this.baseUrlOverride.replace(/\/+$/, '');
    }
    const config = await getExtensionConfig();
    return config.backendApiUrl.replace(/\/+$/, '');
  }

  /**
   * Health check probe to determine backend readiness.
   */
  public async checkHealth(timeoutMs = 4000): Promise<{ isAvailable: boolean; status?: string }> {
    const baseUrl = await this.getBaseUrl();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${baseUrl}/api/v1/health`, {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (response.ok) {
        const data = await response.json();
        return { isAvailable: true, status: data.status || 'healthy' };
      }
      return { isAvailable: false };
    } catch {
      clearTimeout(timeoutId);
      return { isAvailable: false };
    }
  }

  /**
   * Dispatches analysis request to Unified Firewall API (POST /api/v1/firewall/analyze).
   */
  public async analyze(
    payload: ExtensionAnalyzePayload,
    timeoutMs = EXTENSION_METADATA.defaultTimeoutMs
  ): Promise<LastAnalysisReference> {
    const baseUrl = await this.getBaseUrl();
    const config = await getExtensionConfig();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${baseUrl}/api/v1/firewall/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({
          input_type: payload.input_type,
          text: payload.text,
          url: payload.url,
          channel: payload.channel || 'web',
          session_id: payload.session_id || `EXT-SESS-${Date.now().toString(36).toUpperCase()}`,
        }),
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        let errData: { error_code?: string; message?: string } = {};
        try {
          errData = await response.json();
        } catch {
          // Non-JSON response
        }

        let code = errData.error_code;
        let message = errData.message;

        if (!code) {
          if (response.status === 429) {
            code = 'RATE_LIMITED';
            message = message || 'Rate limit reached. Please wait a moment before analyzing again.';
          } else if (response.status === 400) {
            code = 'INVALID_REQUEST';
            message = message || 'The analysis request was invalid.';
          } else if (response.status === 404) {
            code = 'ENDPOINT_NOT_FOUND';
            message = message || 'The requested Firewall endpoint was not found.';
          } else if (response.status >= 500) {
            code = 'PIPELINE_FAILURE';
            message = message || 'Firewall service encountered an internal error. Please try again.';
          } else {
            code = 'HTTP_ERROR';
            message = message || `Firewall service responded with status ${response.status}`;
          }
        }

        throw new ExtensionApiClientError({
          code,
          message: message || `Firewall service responded with status ${response.status}`,
          statusCode: response.status,
        });
      }

      let result: any;
      try {
        result = await response.json();
      } catch {
        throw new ExtensionApiClientError({
          code: 'MALFORMED_RESPONSE',
          message: 'Received invalid JSON response from Nivesh Firewall.',
          statusCode: response.status,
        });
      }

      if (!result || typeof result !== 'object') {
        throw new ExtensionApiClientError({
          code: 'MALFORMED_RESPONSE',
          message: 'Received invalid response payload structure from Nivesh Firewall.',
          statusCode: response.status,
        });
      }

      const decisionObj = result.decision || {};
      const analysisId = result.analysis_id || 'UNKNOWN';

      return {
        analysisId,
        decision: decisionObj.decision || 'WARN',
        severity: decisionObj.severity || 'MEDIUM',
        primaryReason: decisionObj.primary_reason || 'Interaction inspected by Nivesh Firewall.',
        completedAt: result.completed_at || new Date().toISOString(),
        webAppUrl: buildNiveshWebAppUrl(config.webAppBaseUrl, analysisId),
      };
    } catch (err) {
      clearTimeout(timeoutId);

      if (err instanceof ExtensionApiClientError) {
        throw err;
      }

      if (err instanceof DOMException && err.name === 'AbortError') {
        throw new ExtensionApiClientError({
          code: 'BACKEND_TIMEOUT',
          message: 'The Firewall inspection request timed out.',
        });
      }

      throw new ExtensionApiClientError({
        code: 'BACKEND_UNAVAILABLE',
        message: 'Could not connect to Nivesh Firewall service.',
      });
    }
  }
}
