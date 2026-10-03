"""Performance & Capacity Validation Benchmark for Nivesh Firewall.

Phase 14.5: Deployment, Performance & Production Validation

Evaluates cold vs warm pipeline execution, per-engine latencies,
persistence latency, and end-to-end API response time across 7
canonical realistic financial workload scenarios.
"""

import time
from typing import Any, Optional
from dataclasses import dataclass, field
from fastapi.testclient import TestClient

from nivesh.orchestrator.service import ProductOrchestrator
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType
from nivesh.api.app import app


@dataclass
class ScenarioBenchmarkResult:
    scenario_id: str
    scenario_name: str
    decision: str
    cold_duration_ms: float
    warm_duration_ms: float
    avg_duration_ms: float
    engine_durations_ms: dict[str, float] = field(default_factory=dict)
    persistence_duration_ms: float = 0.0
    orchestration_overhead_ms: float = 0.0
    api_latency_ms: float = 0.0


# 7 Canonical Realistic Workload Scenarios
BENCHMARK_SCENARIOS = [
    {
        "id": "SCN-1-BENIGN-EDU",
        "name": "Benign Financial Education",
        "text": (
            "Mutual funds are subject to market risks. Please read all scheme related "
            "documents carefully before investing. Systematic Investment Plans (SIP) "
            "allow long-term rupee cost averaging across diverse equities."
        ),
        "channel": "web",
    },
    {
        "id": "SCN-2-INFORMATIONAL",
        "name": "Informational Market Commentary",
        "text": (
            "The Nifty 50 and BSE Sensex gained 0.8% today in broad-based buying led by "
            "private banks and IT exporters ahead of quarterly earnings reports."
        ),
        "channel": "news",
    },
    {
        "id": "SCN-3-UNVERIFIED-AUTH",
        "name": "Unverified Authority Claim",
        "text": (
            "Hello, I am Rajesh Verma, SEBI registered research analyst. "
            "Join my channel for daily equity recommendations and market reports: "
            "https://t.me/rajesh_equity_research"
        ),
        "channel": "telegram",
    },
    {
        "id": "SCN-4-MULTI-SIGNAL-THREAT",
        "name": "Multi-Signal Threat Pattern",
        "text": (
            "🚨 Guaranteed 35% weekly profit! Officially certified and registered with SEBI. "
            "Join our private VIP Telegram group: https://t.me/quickwealthvip. "
            "Transfer ₹10,000 to activate automated algorithmic trading."
        ),
        "channel": "telegram",
    },
    {
        "id": "SCN-5-DANGEROUS-ACTIONS",
        "name": "Dangerous Action Sequence",
        "text": (
            "Exclusive investment opportunity! Step 1: Join secret group on Telegram. "
            "Step 2: Download and install our custom APK app. Step 3: Grant device permissions. "
            "Step 4: Deposit ₹25,000 via UPI to unlock instant returns."
        ),
        "channel": "telegram",
    },
    {
        "id": "SCN-6-FINGERPRINT-VARIANT",
        "name": "Known Fingerprint Structural Variant",
        "text": (
            "⚡ Assured 35% weekly return! Licensed with SEBI authority. "
            "Connect on our WhatsApp VIP channel: https://chat.whatsapp.com/inv999. "
            "Transfer ₹9,999 to start VIP signals."
        ),
        "channel": "whatsapp",
    },
    {
        "id": "SCN-7-BEHAVIOURAL-ESCALATION",
        "name": "Behavioural Escalation Sequence",
        "text": (
            "URGENT: Offer expiring in 15 minutes! Last 2 spots left. "
            "Move to private chat immediately and send ₹15,000 to guarantee your spot."
        ),
        "channel": "telegram",
        "history_events": [
            ("EVT-1", "10:00:00", InteractionEventType.CONTENT_VIEW, None),
            ("EVT-2", "10:01:00", InteractionEventType.CHANNEL_CHANGED, "telegram"),
            ("EVT-3", "10:02:00", InteractionEventType.USER_DECLINED, None),
            ("EVT-4", "10:02:30", InteractionEventType.PAYMENT_REQUESTED, None),
        ],
    },
]


class PerformanceBenchmarkRunner:
    """Executes systematic performance measurements across the Nivesh Firewall pipeline."""

    def __init__(self):
        self.orchestrator = ProductOrchestrator()
        self.client = TestClient(app)

    def run_benchmark(self, iterations_warm: int = 3) -> list[ScenarioBenchmarkResult]:
        results = []

        for scenario in BENCHMARK_SCENARIOS:
            sc_id = scenario["id"]
            name = scenario["name"]
            text = scenario["text"]
            channel = scenario.get("channel", "web")
            history_events = scenario.get("history_events", [])

            # Prepare session if historical events specified
            session_id = f"BENCH-{sc_id}"
            if history_events:
                for eid, ts, etype, ch in history_events:
                    self.orchestrator.record_interaction_event(
                        session_id,
                        InteractionEvent(
                            event_id=eid,
                            timestamp=ts,
                            event_type=etype,
                            channel=ch,
                        ),
                    )

            # 1. Measure Cold Execution
            t0 = time.perf_counter()
            cold_res = self.orchestrator.analyze(
                text=text,
                channel=channel,
                session_id=session_id,
            )
            cold_ms = (time.perf_counter() - t0) * 1000.0

            # 2. Measure Warm Executions
            warm_durations = []
            warm_res = None
            for _ in range(iterations_warm):
                t_w0 = time.perf_counter()
                warm_res = self.orchestrator.analyze(
                    text=text,
                    channel=channel,
                    session_id=session_id,
                )
                warm_durations.append((time.perf_counter() - t_w0) * 1000.0)

            warm_ms = min(warm_durations)
            avg_ms = sum(warm_durations) / len(warm_durations)

            # 3. Extract per-engine breakdown from telemetry
            engine_breakdown = {}
            if warm_res and warm_res.telemetry and warm_res.telemetry.engine_records:
                for eng_key, exec_rec in warm_res.telemetry.engine_records.items():
                    engine_breakdown[eng_key] = round(exec_rec.duration_ms, 2)

            # Calculate sum of engine execution vs total orchestrator duration
            engine_total_ms = sum(engine_breakdown.values())
            orch_overhead_ms = max(0.0, warm_res.telemetry.total_duration_ms - engine_total_ms)

            # 4. Measure HTTP API Latency
            t_api0 = time.perf_counter()
            api_resp = self.client.post(
                "/api/v1/firewall/analyze",
                json={"text": text, "channel": channel},
            )
            api_latency_ms = (time.perf_counter() - t_api0) * 1000.0

            results.append(
                ScenarioBenchmarkResult(
                    scenario_id=sc_id,
                    scenario_name=name,
                    decision=str(warm_res.decision.value if warm_res else "UNKNOWN"),
                    cold_duration_ms=round(cold_ms, 2),
                    warm_duration_ms=round(warm_ms, 2),
                    avg_duration_ms=round(avg_ms, 2),
                    engine_durations_ms=engine_breakdown,
                    persistence_duration_ms=round(warm_res.telemetry.total_duration_ms - engine_total_ms, 2),
                    orchestration_overhead_ms=round(orch_overhead_ms, 2),
                    api_latency_ms=round(api_latency_ms, 2),
                )
            )

        return results

    def format_markdown_report(self, results: list[ScenarioBenchmarkResult]) -> str:
        lines = [
            "### Production Performance & Latency Baseline",
            "",
            "| Scenario | Decision | Cold (ms) | Warm (ms) | Avg (ms) | API Latency (ms) | Primary Latency Contributors |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :--- |",
        ]

        for r in results:
            # Sort top 2 engines by duration
            top_engines = sorted(
                r.engine_durations_ms.items(), key=lambda kv: kv[1], reverse=True
            )[:2]
            top_str = ", ".join(f"{k} ({v}ms)" for k, v in top_engines) if top_engines else "N/A"
            lines.append(
                f"| **{r.scenario_name}** | `{r.decision}` | {r.cold_duration_ms:.1f}ms | "
                f"{r.warm_duration_ms:.1f}ms | {r.avg_duration_ms:.1f}ms | "
                f"{r.api_latency_ms:.1f}ms | {top_str} |"
            )

        return "\n".join(lines)
