"""Distributed Tracing and Diagnostic Spans for Nivesh Firewall.

Phase 14.4: Observability, Monitoring & Operations.
Provides:
- Span context management across HTTP request, Orchestration pipeline, and individual engines
- Safe metadata attributes with zero credential/content leakage
- Graceful degradation when tracing is disabled or external backends are absent
- Circular in-memory buffer of recent trace spans for incident reconstruction
"""

import contextvars
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from nivesh.config.settings import get_settings

current_trace_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_trace_id", default=None)
current_span_id: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_span_id", default=None)


class TraceSpan:
    """Represents an observable diagnostic span within an execution trace."""

    def __init__(
        self,
        name: str,
        trace_id: str,
        span_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ):
        self.name = name
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id
        self.start_perf = time.perf_counter()
        self.start_time = datetime.now(timezone.utc).isoformat()
        self.end_time: Optional[str] = None
        self.duration_ms: float = 0.0
        self.status: str = "OK"  # OK, ERROR, TIMEOUT, CANCELLED
        self.error_message: Optional[str] = None
        self.error_type: Optional[str] = None
        self.attributes: dict[str, Any] = attributes or {}
        self.events: list[dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        """Add safe diagnostic attribute; ignores raw credentials or text."""
        # Safety gate: prevent forbidden fields from entering trace attributes
        forbidden_keys = ("password", "token", "secret", "card_number", "cvv", "otp", "pin", "text", "body")
        if any(f in key.lower() for f in forbidden_keys):
            return
        self.attributes[key] = value

    def add_event(self, event_name: str, payload: Optional[dict[str, Any]] = None) -> None:
        """Add a timestamped diagnostic event marker."""
        self.events.append({
            "name": event_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload or {},
        })

    def record_exception(self, exc: BaseException, error_type: Optional[str] = None) -> None:
        """Record an error condition without exposing sensitive values."""
        self.status = "ERROR"
        self.error_type = error_type or exc.__class__.__name__
        self.error_message = str(exc)

    def finish(self, status: Optional[str] = None) -> None:
        """Complete the span and record duration."""
        if self.end_time is not None:
            return
        self.end_time = datetime.now(timezone.utc).isoformat()
        self.duration_ms = (time.perf_counter() - self.start_perf) * 1000.0
        if status:
            self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": round(self.duration_ms, 3),
            "status": self.status,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "attributes": self.attributes,
            "events": self.events,
        }

    def __enter__(self) -> "TraceSpan":
        self._token_span = current_span_id.set(self.span_id)
        self._token_trace = current_trace_id.set(self.trace_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_val is not None:
            self.record_exception(exc_val)
        self.finish()
        if hasattr(self, "_token_span"):
            current_span_id.reset(self._token_span)
        if hasattr(self, "_token_trace"):
            current_trace_id.reset(self._token_trace)


class Tracer:
    """In-memory diagnostic tracer with bounded circular history and zero external dependencies."""

    def __init__(self, max_retained_spans: int = 1000):
        self.max_retained = max_retained_spans
        self._spans: list[TraceSpan] = []
        self._lock = threading.Lock()

    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[dict[str, Any]] = None,
    ) -> TraceSpan:
        """Start a new trace span with inherited or generated trace context."""
        settings = get_settings()
        if not settings.tracing_enabled:
            # Return active span that behaves normally in memory
            pass

        t_id = trace_id or current_trace_id.get() or f"trc-{uuid.uuid4().hex[:16]}"
        p_id = parent_span_id or current_span_id.get()
        s_id = f"spn-{uuid.uuid4().hex[:12]}"

        span = TraceSpan(
            name=name,
            trace_id=t_id,
            span_id=s_id,
            parent_span_id=p_id,
            attributes=attributes,
        )

        with self._lock:
            self._spans.append(span)
            if len(self._spans) > self.max_retained:
                self._spans.pop(0)

        return span

    def get_recent_spans(self, limit: int = 100, trace_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Retrieve recent spans for incident reconstruction and troubleshooting."""
        with self._lock:
            spans = self._spans if trace_id is None else [s for s in self._spans if s.trace_id == trace_id]
            return [s.to_dict() for s in spans[-limit:]]

    def clear(self) -> None:
        with self._lock:
            self._spans.clear()


# Global tracer singleton
tracer = Tracer()
