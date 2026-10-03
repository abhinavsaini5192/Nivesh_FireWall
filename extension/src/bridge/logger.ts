/**
 * Safe Bridge Telemetry Logger (Phase 13.3 Section 23)
 *
 * Strictly logs diagnostic metadata (correlation IDs, timing, status, error codes).
 * NEVER logs raw text, full sensitive URLs, form fields, credentials, or raw responses.
 */

export interface SafeBridgeLogEvent {
  captureId?: string;
  requestId: string;
  analysisId?: string;
  sourceType?: string;
  status: 'SUBMITTING' | 'COMPLETED' | 'FAILED' | 'RETRYING';
  durationMs?: number;
  errorCode?: string;
  retriesAttempted?: number;
}

class BridgeTelemetryLogger {
  public log(event: SafeBridgeLogEvent): void {
    // Sanitized structured telemetry log
    const entry = {
      tag: '[Nivesh Bridge]',
      timestamp: new Date().toISOString(),
      requestId: event.requestId,
      captureId: event.captureId || 'NONE',
      analysisId: event.analysisId || 'PENDING',
      sourceType: event.sourceType || 'UNKNOWN',
      status: event.status,
      durationMs: typeof event.durationMs === 'number' ? Math.round(event.durationMs) : undefined,
      errorCode: event.errorCode,
      retries: event.retriesAttempted || 0,
    };

    if (event.status === 'FAILED') {
      console.warn(entry.tag, JSON.stringify(entry));
    } else {
      console.info(entry.tag, JSON.stringify(entry));
    }
  }
}

export const bridgeLogger = new BridgeTelemetryLogger();
