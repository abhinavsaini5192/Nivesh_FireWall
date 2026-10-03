"""Nivesh Firewall Observability, Monitoring & Operations Subsystem.

Phase 14.4: Observability, Monitoring & Operations.
Exports:
- Structured logging, correlation context, and sensitive credential scrubber
- Centralized metrics registry and Prometheus/JSON exposition
- Distributed tracing spans and tracer singleton
- Liveness and readiness diagnostic checks
- HTTP Observability middleware
"""

from nivesh.observability.logging import (
    request_id_ctx,
    correlation_id_ctx,
    analysis_id_ctx,
    engine_key_ctx,
    scrub_sensitive_tokens,
    SensitiveDataScrubberFilter,
    StructuredJsonFormatter,
    StandardTextFormatter,
    configure_observability_logging,
)
from nivesh.observability.metrics import (
    metrics,
    MetricsRegistry,
    MetricCounter,
    MetricHistogram,
)
from nivesh.observability.tracing import (
    tracer,
    Tracer,
    TraceSpan,
    current_trace_id,
    current_span_id,
)
from nivesh.observability.health import (
    check_liveness,
    check_readiness,
)
from nivesh.observability.middleware import ObservabilityMiddleware

__all__ = [
    "request_id_ctx",
    "correlation_id_ctx",
    "analysis_id_ctx",
    "engine_key_ctx",
    "scrub_sensitive_tokens",
    "SensitiveDataScrubberFilter",
    "StructuredJsonFormatter",
    "StandardTextFormatter",
    "configure_observability_logging",
    "metrics",
    "MetricsRegistry",
    "MetricCounter",
    "MetricHistogram",
    "tracer",
    "Tracer",
    "TraceSpan",
    "current_trace_id",
    "current_span_id",
    "check_liveness",
    "check_readiness",
    "ObservabilityMiddleware",
]
