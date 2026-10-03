/**
 * Nivesh Analysis Bridge (Phase 13.3)
 *
 * Connects the browser extension capture layer to the Unified Firewall API
 * (POST /api/v1/firewall/analyze) via the background worker.
 *
 * Core Responsibilities:
 * 1. Validates capture input before transmission.
 * 2. Coordinates capture_id -> request_id -> analysis_id correlation.
 * 3. Applies bounded retries (max 1 retry) for transient network failures.
 * 4. Preserves full Engine 8 intelligence (decision, claims, evidence, threat, etc.).
 * 5. Strictly enforces the Safe Fallback Principle: UNAVAILABLE is NEVER ALLOW.
 * 6. Logs safe telemetry without sensitive data.
 */

import { getExtensionConfig, buildNiveshWebAppUrl } from '../config';
import { ExtensionApiClient, ExtensionApiClientError } from '../api/client';
import { bridgeLogger } from './logger';
import type {
  BrowserAnalysisRequest,
  BridgeAnalysisResult,
  FirewallAnalysisResponse,
} from './types';
import type { LastAnalysisReference } from '../types/state';

export interface BridgeOptions {
  timeoutMs?: number;
  maxRetries?: number;
  apiClientOverride?: ExtensionApiClient;
}

export class NiveshAnalysisBridge {
  private apiClient: ExtensionApiClient;
  private defaultTimeoutMs: number;
  private maxRetries: number;

  constructor(options: BridgeOptions = {}) {
    this.apiClient = options.apiClientOverride || new ExtensionApiClient();
    this.defaultTimeoutMs = options.timeoutMs || 8000;
    this.maxRetries = typeof options.maxRetries === 'number' ? options.maxRetries : 1;
  }

  public getApiClient(): ExtensionApiClient {
    return this.apiClient;
  }

  /**
   * Validates canonical bridge request before submission.
   */
  public validateRequest(request: BrowserAnalysisRequest): void {
    if (!request) {
      throw new ExtensionApiClientError({
        code: 'INVALID_REQUEST',
        message: 'Bridge request cannot be empty.',
      });
    }

    if (!request.requestId || !request.requestId.trim()) {
      throw new ExtensionApiClientError({
        code: 'INVALID_REQUEST',
        message: 'Request correlation ID is missing.',
      });
    }

    if (request.sourceType === 'URL') {
      if (!request.url || !request.url.trim()) {
        throw new ExtensionApiClientError({
          code: 'INVALID_REQUEST',
          message: 'URL capture requires a valid URL target.',
        });
      }
    } else {
      if (!request.text || !request.text.trim()) {
        throw new ExtensionApiClientError({
          code: 'UNSUPPORTED_INPUT',
          message: 'Captured content is empty and cannot be analyzed.',
        });
      }
    }
  }

  /**
   * Executes analysis bridge workflow with correlation and bounded retries.
   */
  public async submitAnalysis(request: BrowserAnalysisRequest): Promise<BridgeAnalysisResult> {
    const startTime = performance.now();
    this.validateRequest(request);

    const config = await getExtensionConfig();
    const baseUrl = config.backendApiUrl.replace(/\/+$/, '');

    bridgeLogger.log({
      captureId: request.captureId,
      requestId: request.requestId,
      sourceType: request.sourceType,
      status: 'SUBMITTING',
    });

    let lastError: unknown;
    let attempt = 0;
    const maxAttempts = 1 + this.maxRetries;

    while (attempt < maxAttempts) {
      attempt++;
      const isRetry = attempt > 1;

      if (isRetry) {
        bridgeLogger.log({
          captureId: request.captureId,
          requestId: request.requestId,
          sourceType: request.sourceType,
          status: 'RETRYING',
          retriesAttempted: attempt - 1,
        });
        // Bounded exponential backoff delay before retry (e.g. 500ms)
        await new Promise((resolve) => setTimeout(resolve, 500));
      }

      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.defaultTimeoutMs);

        const response = await fetch(`${baseUrl}/api/v1/firewall/analyze`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          body: JSON.stringify({
            input_type: request.sourceType === 'URL' ? 'url' : 'text',
            text: request.sourceType === 'URL' ? undefined : request.text,
            url: request.url,
            channel: 'web',
            session_id: request.sessionId || request.captureId || request.requestId,
            metadata: {
              capture_id: request.captureId,
              request_id: request.requestId,
              tab_id: request.tabId,
              page_origin: request.pageOrigin,
              page_title: request.pageTitle,
            },
            idempotency_key: request.requestId,
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

          const errorCode = errData.error_code || (response.status >= 500 ? 'PIPELINE_FAILURE' : 'INVALID_REQUEST');
          const errorMsg = errData.message || `Firewall service responded with HTTP ${response.status}`;

          // Non-transient errors (4xx) should never be retried
          if (response.status < 500) {
            throw new ExtensionApiClientError({
              code: errorCode,
              message: errorMsg,
              statusCode: response.status,
            });
          }

          // 5xx errors may be transient, record and loop
          throw new ExtensionApiClientError({
            code: errorCode,
            message: errorMsg,
            statusCode: response.status,
          });
        }

        const rawResult: FirewallAnalysisResponse = await response.json();
        const durationMs = performance.now() - startTime;

        // Construct Canonical LastAnalysisReference (Section 14 & 16)
        const decisionSummary = rawResult.decision || {};
        const analysisId = rawResult.analysis_id || 'UNKNOWN';

        const reference: LastAnalysisReference = {
          analysisId,
          captureId: request.captureId,
          requestId: request.requestId,
          tabId: request.tabId,
          decision: decisionSummary.decision || 'WARN',
          severity: decisionSummary.severity || 'MEDIUM',
          primaryReason: decisionSummary.primary_reason || 'Interaction inspected by Nivesh Firewall.',
          userMessage: decisionSummary.explanation?.user_message,
          completedAt: rawResult.completed_at || new Date().toISOString(),
          webAppUrl: buildNiveshWebAppUrl(config.webAppBaseUrl, analysisId),
          claimsCount: Array.isArray(rawResult.claims) ? rawResult.claims.length : 0,
          evidenceStatus: rawResult.evidence?.overall_status || 'NOT_ESTABLISHED',
          identityStatus: rawResult.identity?.identity_status || 'NOT_ESTABLISHED',
          fingerprintMatch: rawResult.fingerprint?.match_type || 'NO_MATCH',
          threatSignalCount: Array.isArray(rawResult.threat?.threat_signals) ? rawResult.threat.threat_signals.length : 0,
          durationMs: Math.round(durationMs),
        };

        bridgeLogger.log({
          captureId: request.captureId,
          requestId: request.requestId,
          analysisId,
          sourceType: request.sourceType,
          status: 'COMPLETED',
          durationMs,
          retriesAttempted: attempt - 1,
        });

        return {
          analysisId,
          captureId: request.captureId,
          requestId: request.requestId,
          reference,
          fullResponse: rawResult,
          retriesAttempted: attempt - 1,
          durationMs,
        };
      } catch (err) {
        lastError = err;

        // If error is client validation / non-transient, break retry loop immediately
        if (err instanceof ExtensionApiClientError && err.statusCode && err.statusCode < 500) {
          break;
        }

        // If we have exhausted all retries, break
        if (attempt >= maxAttempts) {
          break;
        }
      }
    }

    // Handle failure according to Safe Fallback Principle (Section 20)
    // NEVER convert failure to ALLOW or "Safe"!
    const durationMs = performance.now() - startTime;
    let mappedError: ExtensionApiClientError;

    if (lastError instanceof ExtensionApiClientError) {
      mappedError = lastError;
    } else if (lastError instanceof DOMException && lastError.name === 'AbortError') {
      mappedError = new ExtensionApiClientError({
        code: 'BACKEND_TIMEOUT',
        message: 'The Firewall inspection request timed out.',
      });
    } else {
      mappedError = new ExtensionApiClientError({
        code: 'BACKEND_UNAVAILABLE',
        message: 'Nivesh protection service is unavailable.',
      });
    }

    bridgeLogger.log({
      captureId: request.captureId,
      requestId: request.requestId,
      sourceType: request.sourceType,
      status: 'FAILED',
      durationMs,
      errorCode: mappedError.code,
      retriesAttempted: attempt - 1,
    });

    throw mappedError;
  }
}

export const analysisBridge = new NiveshAnalysisBridge();
