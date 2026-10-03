# Nivesh Firewall — Production Readiness Specification

**Release Version:** `1.0.0-prod`  
**Phase:** 14.5 (Deployment, Performance & Production Validation)  
**System Architecture:** 10 Intelligence Engines + Product Orchestrator + Web Frontend + Browser Extension  
**Security Boundary:** Zero Credential Retention, Zero Financial Advice, Zero User Surveillance  

---

## 1. System Architecture & Component Model

Nivesh Firewall is an operational security and intervention firewall protecting retail financial consumers against fraudulent, deceptive, or unauthorized securities and financial operations.

```text
                                INCOMING USER TRAFFIC
                       (Web Interface / Chrome Extension MV3)
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │      Nginx Reverse Proxy (Port 80)   │
                      │  - SSL Termination / HTTP Security   │
                      │  - Static Asset Serving (SPA)        │
                      │  - /api/ and /health/ Routing        │
                      └──────────────────┬───────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Nivesh Firewall Backend (Port 8000)│
                      │  - SecurityHeaders & Observability   │
                      │  - HMAC JWT & API Key Authentication │
                      │  - Sliding Window Rate Limiting      │
                      └──────────────────┬───────────────────┘
                                         │
    ┌────────────────────────────────────┼────────────────────────────────────┐
    ▼                                    ▼                                    ▼
┌─────────────────────────┐  ┌─────────────────────────┐  ┌─────────────────────────┐
│  Input & Verification   │  │ Threat & Fingerprint    │  │  Intervention Authority │
│  - Engine 1: Content    │  │  - Engine 6: Threat     │  │  - Engine 8: Policy     │
│  - Engine 2: Claims     │  │  - Engine 7: Fingerprint│  │    (SOLE AUTHORITY FOR  │
│  - Engine 3: Actions    │  │  - Engine 9: Identity   │  │    ALLOW/INFORM/WARN/   │
│  - Engine 4: Sources    │  │  - Engine 10: Behaviour │  │    PAUSE/BLOCK)         │
│  - Engine 5: Evidence   │  │                         │  │                         │
└─────────────────────────┘  └─────────────────────────┘  └─────────────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │ PostgreSQL 16 Persistent Relational  │
                      │  - Analyses, Results, Executions     │
                      │  - Collective Threat Fingerprints    │
                      │  - Session Events (Scrubbed)         │
                      │  - Append-Only Audit Trail           │
                      └──────────────────────────────────────┘
```

---

## 2. Deployment Topology

The recommended production deployment utilizes a multi-container Docker Compose or Kubernetes Pod architecture:

1. **`postgres` Service (`postgres:16-alpine`)**:
   - Dedicated relational database container with persistent named volume `postgres_data`.
   - Tuned for ACID durability with connection pooling and query pre-ping.
2. **`backend` Service (`nivesh/firewall-backend:1.0.0`)**:
   - Multi-worker Uvicorn ASGI server running Python 3.11-slim as unprivileged user `nivesh` (UID 10001).
   - Internal health probes on `/health/live` and `/health/ready`.
3. **`frontend` Service (`nivesh/firewall-frontend:1.0.0`)**:
   - Production Vite bundle compiled into static assets and served via Alpine Nginx.
   - Built-in reverse proxy routing `/api/` and `/health/` directly to backend container.

---

## 3. Environment & Configuration Requirements

| Variable | Environment | Strict Production Rule |
| :--- | :--- | :--- |
| `NIVESH_ENV` | `production` | Enables strict startup validation. |
| `NIVESH_DEBUG` | `False` | Startup aborts if `True`. |
| `NIVESH_SECRET_KEY` | Hex (64 char) | Cryptographically secure; placeholder keys strictly rejected. |
| `NIVESH_DATABASE_URL` | PostgreSQL URI | In-memory or SQLite fallbacks strictly rejected. |
| `NIVESH_ALLOWED_ORIGINS` | Explicit URLs | Wildcard `*` strictly rejected. |
| `NIVESH_SOURCE_MODE` | `FIXTURE` / `LIVE` | `LIVE` requires `NIVESH_LIVE_SOURCES_ENABLED=True`. |
| `NIVESH_LOG_FORMAT` | `json` | Structured JSON log emission. |
| `NIVESH_RATE_LIMIT_ENABLED` | `True` | Sliding-window burst protection. |

---

## 4. Database & Migration Requirements

1. **Alembic Idempotent Migrations**:
   - Run automatically on startup via `run_migrations()` in `lifespan`.
   - Migration file: `alembic/versions/001_initial_persistence_schema.py`.
   - Supports forward upgrades and clean downgrades.
2. **Connection Pooling**:
   - PostgreSQL QueuePool: `pool_size=10`, `max_overflow=20`, `pool_recycle=1800`.
   - SQLite dev fallback: StaticPool with WAL mode.
3. **Data Integrity**:
   - Foreign key cascading on child tables (`analysis_results`, `engine_executions`, `policy_decisions`).
   - Soft-delete semantics for user privacy requests.

---

## 5. Security & Privacy Controls

- **Zero Credential Retention**: Passwords, OTPs, PINs, CVVs, card numbers, and raw auth headers are scrubbed before reaching logs, metrics, traces, or databases.
- **Role-Based Access Control (RBAC)**: `ADMIN`, `ANALYST`, `USER`, `SERVICE`, `ANONYMOUS`.
- **IDOR Existence Concealment**: Unauthorized access attempts return `404 Not Found` (never `403`) to conceal resource existence.
- **Timing-Safe Auth**: Constant-time comparison (`hmac.compare_digest`) for API keys.
- **HTTP Security Headers**: HSTS, CSP, X-Frame-Options (`DENY`), X-Content-Type-Options (`nosniff`).

---

## 6. Observability & Operational Diagnostics

- **Structured JSON Logging**: UTC ISO timestamps, correlation ID, request ID, analysis ID, and engine keys.
- **Prometheus Telemetry**: `/api/v1/metrics` with strictly low-cardinality labels.
- **Distributed Tracing**: Root span `nivesh.pipeline.analysis` and child spans for all 10 engines and persistence.
- **Health Probing**: Separated `/health/live` (process liveness, < 5ms) and `/health/ready` (dependency validation).

---

## 7. Performance & Latency Baseline

Measured across 7 realistic financial workload scenarios:

| Workload Scenario | Policy Decision | Cold Pipeline | Warm Pipeline | API Latency | Top Latency Contributors |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Benign Financial Education** | `ALLOW` | 11.5ms | 4.7ms | 105.4ms | engine_2_claims (0.9ms), engine_1_content (0.8ms) |
| **Informational Market Commentary** | `WARN` | 4.4ms | 3.1ms | 26.4ms | engine_2_claims (0.6ms), engine_1_content (0.6ms) |
| **Unverified Authority Claim** | `WARN` | 4.7ms | 3.0ms | 35.7ms | engine_1_content (0.7ms), engine_9_identity (0.3ms) |
| **Multi-Signal Threat Pattern** | `PAUSE` | 5.7ms | 5.4ms | 41.0ms | engine_1_content (1.1ms), engine_2_claims (0.6ms) |
| **Dangerous Action Sequence** | `PAUSE` | 6.9ms | 5.8ms | 41.0ms | engine_4_sources (1.4ms), engine_2_claims (1.0ms) |
| **Known Fingerprint Structural Variant** | `PAUSE` | 5.5ms | 4.6ms | 37.4ms | engine_1_content (0.7ms), engine_4_sources (0.7ms) |
| **Behavioural Escalation Sequence** | `PAUSE` | 4.7ms | 4.4ms | 38.9ms | engine_1_content (0.7ms), engine_2_claims (0.6ms) |

---

## 8. Capacity & Concurrency Findings

- **Sustained Pipeline Execution**: < 10ms per analysis.
- **HTTP Overhead**: 20ms–35ms per request.
- **Throughput**: ~100–120 requests/sec per Uvicorn worker process.
- **Concurrency**: Verified multi-threaded execution across concurrent sessions with zero cross-session bleed.

---

## 9. Failure & Recovery Behavior

1. **Database Outage**:
   - `/health/ready` immediately returns `503 Service Unavailable`.
   - Pipeline operations fail safe without corrupting records or leaking database credentials.
2. **External Registry Outage**:
   - Official registries unavailable does NOT cause pipeline failure.
   - Nivesh Firewall **NEVER** fabricates legitimacy when verification cannot be completed.
   - Engine 8 safely degrades to `WARN` or `PAUSE` with `ReasonCode.SOURCE_UNAVAILABLE`.
3. **Engine Runtime Exception**:
   - `SafeEngineExecutor` isolates engine crash, passes safe fallback structures downstream, and completes pipeline in `DEGRADED` status without dropping the request.

---

## 10. Backup & Disaster Recovery

- **Database Backup**: Periodic snapshot via `pg_dump -Fc nivesh_db > backup.dump`.
- **Stateless Application Tier**: Backend API and Frontend containers are fully stateless; replacement instances can be launched immediately.
- **Cold Restart Recovery**: Persisted analysis records and fingerprints are reloaded seamlessly upon application restart.

---

## 11. Operational Runbook References

Refer to **README.md Section 24.5** for detailed step-by-step procedures:
- Runbook A: Database Failure & Connection Pool Exhaustion
- Runbook B: External Source Outage (SEBI / Exchanges)
- Runbook C: Engine Failure or Execution Timeout
- Runbook D: High Latency & Slow Processing Spikes
- Runbook E: Elevated API Errors (4xx / 5xx)
- Runbook F: Deployment Rollback & Verification

---

## 12. Known Limitations

1. **Live Regulatory Scraping**: Live scraping against external registry portals is subject to external rate limiting and third-party portal maintenance. Use cached or fixture mode during external downtime.
2. **Client-Side Image OCR**: Highly compressed or degraded low-resolution screenshots may require client pre-cropping for optimal claim extraction.
3. **Browser Extension Manifest V3 Quotas**: Background service worker sleep cycles require state to be persisted via `chrome.storage.local`.

---

## 13. Production Launch Checklist

- [x] Production environment variables configured in `.env.production` (no debug mode, no wildcard CORS).
- [x] High-entropy `NIVESH_SECRET_KEY` generated (`openssl rand -hex 32`).
- [x] PostgreSQL 16 database running and accessible via `NIVESH_DATABASE_URL`.
- [x] Database migrations verified to head (`python scripts/entrypoint.py --check-only`).
- [x] Frontend production bundle built cleanly (`npm --prefix frontend run build`).
- [x] Browser extension production bundle built cleanly (`npm --prefix extension run build`).
- [x] Liveness (`/health/live`) and readiness (`/health/ready`) probes verified.
- [x] Prometheus metrics scraping configured for `/api/v1/metrics`.
- [x] Rate limiting enabled and tested (`NIVESH_RATE_LIMIT_ENABLED=True`).
- [x] All 20 production readiness tests passing (`tests/test_production_readiness.py`).
- [x] Full regression suites verified.

---

## 14. Rollback Procedure

In the event of a critical deployment failure:
1. **Container Rollback**:
   ```bash
   docker-compose down
   docker-compose -f docker-compose.yml up -d --build
   ```
2. **Database Rollback (if schema changed)**:
   ```bash
   alembic downgrade -1
   ```
3. **Verification**:
   - Query `/health/live` (must return `200 OK` in < 5ms).
   - Query `/health/ready` (must return `200 OK` with `database: UP`).
   - Confirm error rate in Prometheus drops to 0%.
