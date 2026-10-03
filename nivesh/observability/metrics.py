"""Centralized Metrics and Operational Telemetry Registry for Nivesh Firewall.

Phase 14.4: Observability, Monitoring & Operations.
Implements thread-safe, low-cardinality operational telemetry across:
- HTTP API layer (requests, latency, status distributions, timeouts)
- Firewall Pipeline (analyses, per-engine durations, outcomes, timeouts, retries)
- Policy Enforcement (operational intervention distributions)
- Persistence Layer (ACID operations, rollbacks, latencies, connection failures)
- External Regulatory Sources (requests, availability, timeouts, cache hits)

Strictly enforces low label cardinality (NO user IDs, IP addresses, emails, or raw content).
"""

import threading
import time
from collections import defaultdict
from typing import Any, Optional


class MetricCounter:
    """Thread-safe counter with multi-dimensional low-cardinality labels."""

    def __init__(self, name: str, description: str, label_names: list[str]):
        self.name = name
        self.description = description
        self.label_names = tuple(label_names)
        self._counts: dict[tuple[str, ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def inc(self, value: float = 1.0, **labels: str) -> None:
        key = tuple(str(labels.get(lbl, "")) for lbl in self.label_names)
        with self._lock:
            self._counts[key] += value

    def get(self, **labels: str) -> float:
        key = tuple(str(labels.get(lbl, "")) for lbl in self.label_names)
        with self._lock:
            return self._counts.get(key, 0.0)

    def get_all(self) -> dict[tuple[str, ...], float]:
        with self._lock:
            return dict(self._counts)

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()


class MetricHistogram:
    """Thread-safe latency histogram and summary tracker."""

    def __init__(self, name: str, description: str, label_names: list[str]):
        self.name = name
        self.description = description
        self.label_names = tuple(label_names)
        self._counts: dict[tuple[str, ...], int] = defaultdict(int)
        self._sums: dict[tuple[str, ...], float] = defaultdict(float)
        self._lock = threading.Lock()

    def observe(self, value: float, **labels: str) -> None:
        key = tuple(str(labels.get(lbl, "")) for lbl in self.label_names)
        with self._lock:
            self._counts[key] += 1
            self._sums[key] += value

    def get(self, **labels: str) -> tuple[int, float]:
        key = tuple(str(labels.get(lbl, "")) for lbl in self.label_names)
        with self._lock:
            return self._counts.get(key, 0), self._sums.get(key, 0.0)

    def get_all(self) -> dict[tuple[str, ...], dict[str, float]]:
        with self._lock:
            out = {}
            for k in set(self._counts.keys()).union(self._sums.keys()):
                cnt = self._counts.get(k, 0)
                sm = self._sums.get(k, 0.0)
                avg = (sm / cnt) if cnt > 0 else 0.0
                out[k] = {"count": cnt, "sum": sm, "avg": avg}
            return out

    def reset(self) -> None:
        with self._lock:
            self._counts.clear()
            self._sums.clear()


class MetricsRegistry:
    """Singleton registry tracking all system-level operational metrics."""

    def __init__(self):
        # 1. API Metrics
        self.http_requests_total = MetricCounter(
            "nivesh_http_requests_total",
            "Total HTTP requests received by method, route, and status code",
            ["method", "route", "status_code"],
        )
        self.http_request_duration_seconds = MetricHistogram(
            "nivesh_http_request_duration_seconds",
            "HTTP request execution latency in seconds",
            ["method", "route"],
        )
        self.http_timeouts_total = MetricCounter(
            "nivesh_http_timeouts_total",
            "Total HTTP requests that timed out",
            ["route"],
        )

        # 2. Firewall Pipeline Metrics
        self.pipeline_requests_total = MetricCounter(
            "nivesh_firewall_pipeline_requests_total",
            "Total analysis pipeline invocations by input type and channel",
            ["input_type", "channel"],
        )
        self.pipeline_completed_total = MetricCounter(
            "nivesh_firewall_pipeline_completed_total",
            "Total pipeline executions finalized by terminal status",
            ["status"],
        )
        self.pipeline_duration_seconds = MetricHistogram(
            "nivesh_firewall_pipeline_duration_seconds",
            "End-to-end pipeline latency in seconds by status",
            ["status"],
        )
        self.engine_executions_total = MetricCounter(
            "nivesh_firewall_engine_executions_total",
            "Total intelligence engine invocations by engine key and outcome status",
            ["engine_key", "status"],
        )
        self.engine_duration_seconds = MetricHistogram(
            "nivesh_firewall_engine_duration_seconds",
            "Per-engine execution latency in seconds",
            ["engine_key", "status"],
        )
        self.engine_timeouts_total = MetricCounter(
            "nivesh_firewall_engine_timeouts_total",
            "Total per-engine executions that timed out",
            ["engine_key"],
        )
        self.engine_retries_total = MetricCounter(
            "nivesh_firewall_engine_retries_total",
            "Total engine execution retries",
            ["engine_key"],
        )

        # 3. Policy & Intervention Metrics
        self.policy_decisions_total = MetricCounter(
            "nivesh_firewall_policy_decisions_total",
            "Total policy intervention outcomes generated by decision and severity",
            ["decision", "severity"],
        )

        # 4. Persistence Metrics
        self.persistence_operations_total = MetricCounter(
            "nivesh_firewall_persistence_operations_total",
            "Total database operations by operation type and outcome status",
            ["operation", "status"],
        )
        self.persistence_duration_seconds = MetricHistogram(
            "nivesh_firewall_persistence_duration_seconds",
            "Database operation latency in seconds",
            ["operation"],
        )
        self.persistence_rollbacks_total = MetricCounter(
            "nivesh_firewall_persistence_rollbacks_total",
            "Total database transaction rollbacks",
            ["operation"],
        )
        self.persistence_connection_failures_total = MetricCounter(
            "nivesh_firewall_persistence_connection_failures_total",
            "Total database connection health check or pool connection failures",
            [],
        )

        # 5. External Source Intelligence Metrics
        self.source_requests_total = MetricCounter(
            "nivesh_firewall_source_requests_total",
            "Total external source queries by source provider and status",
            ["source_name", "status"],
        )
        self.source_duration_seconds = MetricHistogram(
            "nivesh_firewall_source_duration_seconds",
            "External source query duration in seconds",
            ["source_name"],
        )
        self.source_unavailable_total = MetricCounter(
            "nivesh_firewall_source_unavailable_total",
            "Total external source unavailable events",
            ["source_name"],
        )
        self.source_cache_hits_total = MetricCounter(
            "nivesh_firewall_source_cache_hits_total",
            "Total regulatory cache hits",
            ["source_name"],
        )
        self.source_cache_misses_total = MetricCounter(
            "nivesh_firewall_source_cache_misses_total",
            "Total regulatory cache misses",
            ["source_name"],
        )

    def reset_all(self) -> None:
        """Reset all registered metrics for testing or benchmark isolation."""
        for attr in dir(self):
            val = getattr(self, attr)
            if isinstance(val, (MetricCounter, MetricHistogram)):
                val.reset()

    def export_json(self) -> dict[str, Any]:
        """Export metrics as a structured JSON object."""
        result: dict[str, Any] = {}
        for attr in dir(self):
            val = getattr(self, attr)
            if isinstance(val, MetricCounter):
                all_data = val.get_all()
                serialized = {}
                for k, count in all_data.items():
                    lbl_str = ",".join(f"{lbl}={val}" for lbl, val in zip(val.label_names, k))
                    serialized[lbl_str or "total"] = count
                result[val.name] = {
                    "type": "counter",
                    "description": val.description,
                    "data": serialized,
                }
            elif isinstance(val, MetricHistogram):
                all_data = val.get_all()
                serialized = {}
                for k, stats in all_data.items():
                    lbl_str = ",".join(f"{lbl}={v}" for lbl, v in zip(val.label_names, k))
                    serialized[lbl_str or "total"] = stats
                result[val.name] = {
                    "type": "histogram",
                    "description": val.description,
                    "data": serialized,
                }
        return result

    def export_prometheus(self) -> str:
        """Export metrics in standard Prometheus exposition format."""
        lines: list[str] = []
        for attr in sorted(dir(self)):
            val = getattr(self, attr)
            if isinstance(val, MetricCounter):
                lines.append(f"# HELP {val.name} {val.description}")
                lines.append(f"# TYPE {val.name} counter")
                all_data = val.get_all()
                if not all_data and not val.label_names:
                    lines.append(f"{val.name} 0.0")
                for k, count in sorted(all_data.items()):
                    if val.label_names:
                        lbls = ",".join(f'{lbl}="{v}"' for lbl, v in zip(val.label_names, k))
                        lines.append(f"{val.name}{{{lbls}}} {count}")
                    else:
                        lines.append(f"{val.name} {count}")
            elif isinstance(val, MetricHistogram):
                lines.append(f"# HELP {val.name} {val.description}")
                lines.append(f"# TYPE {val.name} summary")
                all_data = val.get_all()
                for k, stats in sorted(all_data.items()):
                    if val.label_names:
                        lbls_count = ",".join(f'{lbl}="{v}"' for lbl, v in zip(val.label_names, k))
                        lines.append(f"{val.name}_count{{{lbls_count}}} {stats['count']}")
                        lines.append(f"{val.name}_sum{{{lbls_count}}} {stats['sum']:.6f}")
                    else:
                        lines.append(f"{val.name}_count {stats['count']}")
                        lines.append(f"{val.name}_sum {stats['sum']:.6f}")
        return "\n".join(lines) + "\n"


# Global singleton instance
metrics = MetricsRegistry()
