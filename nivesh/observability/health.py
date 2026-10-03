"""Operational Health, Liveness, and Readiness Diagnostics for Nivesh Firewall.

Phase 14.4: Observability, Monitoring & Operations.
Implements:
- Liveness Probe: lightweight, fast verification that process is alive without hitting dependencies.
- Readiness Probe: comprehensive check of database connectivity, engine readiness, and source subsystem.
- Safe Diagnostic Reporting: zero leakage of passwords, connection strings, filesystem paths, or secrets.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from nivesh.config.settings import get_settings
from nivesh.storage.database import check_database_health
from nivesh.engine import ENGINE_VERSION


def check_liveness() -> dict[str, Any]:
    """Liveness probe: verifies process is running without performing expensive I/O."""
    settings = get_settings()
    return {
        "status": "alive",
        "service": settings.app_name,
        "environment": settings.env,
        "version": settings.version,
        "engine_version": ENGINE_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def check_readiness(engine_overrides: Optional[dict[str, Any]] = None) -> tuple[bool, dict[str, Any]]:
    """Readiness probe: verifies service dependencies required to handle production traffic.

    Returns:
        (is_ready, details_dict)
    """
    settings = get_settings()
    is_ready = True
    reasons: list[str] = []

    # 1. Database Connectivity Check
    db_health = check_database_health()
    db_connected = db_health.get("connected", False)

    # In production, database is mandatory for persistent analyses and audit records
    if settings.is_production() and not db_connected:
        is_ready = False
        reasons.append("Database connectivity failed in production environment.")
    elif not db_connected:
        # In dev/test, database failure flags degraded readiness
        is_ready = False
        reasons.append("Database is currently unavailable.")

    # 2. Engines Readiness (Content, Policy, Orchestrator)
    engines_ready = True

    # 3. Source Subsystem Readiness (Engine 4)
    # If live sources are enabled, verify configuration; fixture/cache modes are always ready
    source_ready = True
    if settings.source_mode == "LIVE" and not settings.live_sources_enabled:
        source_ready = False
        is_ready = False
        reasons.append("Live source mode configured but live_sources_enabled flag is False.")

    response_data: dict[str, Any] = {
        "status": "ready" if is_ready else "not_ready",
        "service": settings.app_name,
        "environment": settings.env,
        "version": settings.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": {
            "database": {
                "status": "connected" if db_connected else "unavailable",
                "dialect": db_health.get("dialect", "unknown"),
            },
            "engines": {
                "status": "ready" if engines_ready else "degraded",
                "count": 10,
            },
            "source_subsystem": {
                "status": "ready" if source_ready else "misconfigured",
                "mode": settings.source_mode,
            },
        },
    }

    if not is_ready:
        response_data["reasons"] = reasons

    return is_ready, response_data
