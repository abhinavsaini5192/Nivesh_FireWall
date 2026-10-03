"""HTTP Observability Middleware for Nivesh Firewall.

Phase 14.4: Observability, Monitoring & Operations.
Implements:
- End-to-end request timing and metric collection
- Context-variable propagation for request ID and correlation ID
- Diagnostic HTTP trace span creation
- Safe structured access logging
"""

import logging
import time
import uuid
from typing import Callable
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from nivesh.observability.logging import (
    request_id_ctx,
    correlation_id_ctx,
)
from nivesh.observability.metrics import metrics
from nivesh.observability.tracing import tracer

logger = logging.getLogger("nivesh.access")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Middleware capturing request metrics, trace context, and structured access logs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()

        # 1. Resolve or generate request & correlation IDs
        req_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
        corr_id = request.headers.get("X-Correlation-ID") or req_id
        trace_id = request.headers.get("X-Trace-ID") or f"trc-{uuid.uuid4().hex[:16]}"

        token_req = request_id_ctx.set(req_id)
        token_corr = correlation_id_ctx.set(corr_id)

        # Store on request state for downstream handlers
        request.state.request_id = req_id
        request.state.correlation_id = corr_id
        request.state.trace_id = trace_id

        # Normalize route path to prevent high cardinality metric labels
        route_path = request.url.path
        if route_path.startswith("/api/v1/firewall/analysis/"):
            normalized_route = "/api/v1/firewall/analysis/{id}"
        elif route_path.startswith("/api/v1/fingerprints/") and "/dispute" in route_path:
            normalized_route = "/api/v1/fingerprints/{id}/dispute"
        elif route_path.startswith("/api/v1/fingerprints/") and "/status" in route_path:
            normalized_route = "/api/v1/fingerprints/{id}/status"
        elif route_path.startswith("/api/v1/fingerprints/"):
            normalized_route = "/api/v1/fingerprints/{id}"
        else:
            normalized_route = route_path

        method = request.method
        status_code = 500

        with tracer.start_span(
            name=f"http_{method.lower()}",
            trace_id=trace_id,
            attributes={"method": method, "route": normalized_route},
        ) as span:
            try:
                response = await call_next(request)
                status_code = response.status_code
                span.set_attribute("status_code", status_code)
                return response
            except Exception as exc:
                span.record_exception(exc)
                logger.error(
                    "Unhandled exception during HTTP request %s %s: %s",
                    method,
                    normalized_route,
                    exc,
                    exc_info=True,
                    extra={
                        "route": normalized_route,
                        "http_method": method,
                        "status_code": 500,
                        "request_id": req_id,
                    },
                )
                raise
            finally:
                duration_sec = time.perf_counter() - start_time
                duration_ms = round(duration_sec * 1000.0, 2)

                # Record metrics with bounded cardinality
                metrics.http_requests_total.inc(
                    method=method,
                    route=normalized_route,
                    status_code=str(status_code),
                )
                metrics.http_request_duration_seconds.observe(
                    duration_sec,
                    method=method,
                    route=normalized_route,
                )

                # Emit structured access log (ignoring noise from frequent health checks if configured)
                if not (normalized_route in ("/health", "/health/live", "/api/v1/health") and status_code == 200):
                    logger.info(
                        "%s %s -> %d (%0.2fms)",
                        method,
                        normalized_route,
                        status_code,
                        duration_ms,
                        extra={
                            "route": normalized_route,
                            "http_method": method,
                            "status_code": status_code,
                            "duration_ms": duration_ms,
                            "request_id": req_id,
                            "correlation_id": corr_id,
                        },
                    )

                # Clean up contextvars
                request_id_ctx.reset(token_req)
                correlation_id_ctx.reset(token_corr)
