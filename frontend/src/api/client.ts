/**
 * Centralized API Client for Nivesh Firewall (Phase 12.1)
 *
 * Dedicated frontend service layer for communicating with the
 * unified Phase 11 Firewall API. Does NOT call individual engines directly.
 */

import type {
  FirewallAnalyzeRequest,
  FirewallAnalysisResponse,
  FirewallApiError,
  ProtectionSystemStatus,
} from '../types/firewall';
import { config } from '../config/env';

export class FirewallClientError extends Error {
  public errorCode: string;
  public analysisId?: string;
  public details: Record<string, unknown>;

  constructor(error: FirewallApiError) {
    super(error.message);
    this.name = 'FirewallClientError';
    this.errorCode = error.error_code;
    this.analysisId = error.analysis_id;
    this.details = error.details || {};
  }
}

export interface HealthCheckResponse {
  status: string;
  engine?: string;
  unified_firewall_api?: string;
  retrieval_api?: string;
  version?: string;
}

export class FirewallApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    // Resolve base URL from explicit argument or centralized environment configuration
    this.baseUrl = (baseUrl !== undefined ? baseUrl : config.apiBaseUrl).replace(/\/+$/, '');
  }

  public getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Probe backend system health to determine real-time protection status.
   */
  public async checkHealth(timeoutMs = 5000): Promise<{ status: ProtectionSystemStatus; data?: HealthCheckResponse }> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/health`, {
        method: 'GET',
        headers: { Accept: 'application/json' },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (response.ok) {
        const data: HealthCheckResponse = await response.json();
        return { status: 'active', data };
      } else {
        return { status: 'error' };
      }
    } catch {
      clearTimeout(timeoutId);
      return { status: 'unavailable' };
    }
  }

  /**
   * Submit content for unified firewall analysis across Engines 1–10.
   */
  public async analyze(
    request: FirewallAnalyzeRequest,
    timeoutMs = 30000
  ): Promise<FirewallAnalysisResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/firewall/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify(request),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorBody: FirewallApiError;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = {
            error_code: response.status === 400 ? 'INVALID_REQUEST' : 'PIPELINE_FAILURE',
            message: `Firewall service returned HTTP ${response.status}.`,
          };
        }
        throw new FirewallClientError(errorBody);
      }

      const data: FirewallAnalysisResponse = await response.json();
      return data;
    } catch (err) {
      clearTimeout(timeoutId);

      if (err instanceof FirewallClientError) {
        throw err;
      }

      if (err instanceof Error && err.name === 'AbortError') {
        throw new FirewallClientError({
          error_code: 'PIPELINE_FAILURE',
          message: 'The analysis request timed out. Please try again.',
        });
      }

      throw new FirewallClientError({
        error_code: 'PIPELINE_FAILURE',
        message: 'Unable to reach the Nivesh Firewall protection service.',
      });
    }
  }

  /**
   * Retrieve prior analysis results by ID without re-executing pipeline.
   */
  public async getAnalysis(
    analysisId: string,
    timeoutMs = 10000
  ): Promise<FirewallAnalysisResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(
        `${this.baseUrl}/api/v1/firewall/analysis/${encodeURIComponent(analysisId)}`,
        {
          method: 'GET',
          headers: { Accept: 'application/json' },
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorBody: FirewallApiError;
        try {
          errorBody = await response.json();
        } catch {
          errorBody = {
            error_code: response.status === 404 ? 'ANALYSIS_NOT_FOUND' : 'PIPELINE_FAILURE',
            message: `Failed to retrieve analysis record (HTTP ${response.status}).`,
            analysis_id: analysisId,
          };
        }
        throw new FirewallClientError(errorBody);
      }

      const data: FirewallAnalysisResponse = await response.json();
      return data;
    } catch (err) {
      clearTimeout(timeoutId);

      if (err instanceof FirewallClientError) {
        throw err;
      }

      throw new FirewallClientError({
        error_code: 'PIPELINE_FAILURE',
        message: 'Unable to retrieve analysis record.',
        analysis_id: analysisId,
      });
    }
  }
}

// Singleton export
export const apiClient = new FirewallApiClient();
