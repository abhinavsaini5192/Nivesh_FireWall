# Nivesh Firewall — Release Candidate Specification (v1.0.0-rc1)

## Executive Summary

This document establishes the official **Release Candidate (RC1)** specification for **Nivesh Firewall**.

Nivesh Firewall is an institutional-grade financial scam prevention, pre-action intervention, and security intelligence platform. It operates as a defensive firewall between individual investors and unsolicited, deceptive, or high-risk financial schemes across digital channels (Web, Telegram, WhatsApp, SMS, and Email).

---

## 1. System Architecture

The architecture consists of exactly **ten (10) specialized intelligence engines**, coordinated by a dependency-aware **Product Orchestration Layer**, exposed via a unified **Firewall API**, and rendered through a **Web Dashboard** and **Browser Extension (Manifest V3)**:

```
[ User Content / Ingestion ]
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      PRODUCT ORCHESTRATOR LAYER                         │
│                                                                        │
│   [Engine 1: Content Intelligence] ──► Text Normalization & Features   │
│                 │                                                      │
│                 ├──► [Engine 2: Claim Intelligence]                    │
│                 │            │                                         │
│                 │            ▼                                         │
│                 ├──► [Engine 3: Action Intelligence]                   │
│                 │            │                                         │
│                 │            ▼                                         │
│                 └──► [Engine 4: Source Intelligence]                   │
│                              │                                         │
│                              ▼                                         │
│                      [Engine 5: Evidence Verification]                 │
│                              │                                         │
│                              ▼                                         │
│                      [Engine 6: Threat Intelligence]                   │
│                              │                                         │
│                              ▼                                         │
│                      [Engine 7: Scam Fingerprint Intelligence]         │
│                              │                                         │
│                              ▼                                         │
│                      [Engine 9: Identity Verification]                 │
│                              │                                         │
│                              ▼                                         │
│                      [Engine 10: Behavioural Signal Intelligence]      │
│                              │                                         │
│                              ▼                                         │
│                      [Engine 8: Policy & Intervention Engine]          │
│                              │                                         │
│                              ▼                                         │
│                      [Persistence & Audit Layer]                       │
└────────────────────────────────────────────────────────────────────────┘
           │
           ▼
[ Unified Firewall Response: Decision, Interventions, Explanations ]
```

### Engine Catalog & Responsibilities

| Engine | Name | Primary Responsibility | Input Dependencies | Output Artifact |
| :--- | :--- | :--- | :--- | :--- |
| **Engine 1** | **Content Intelligence** | Multimodal ingestion, text cleaning, entity extraction, financial relevance classification | Raw Text / URL / Image | `NormalizedContent` |
| **Engine 2** | **Claim Intelligence** | Synthesizes atomic, canonical claims; classifies modality, temporal scope, and financial predicates | Engine 1 | `ClaimAnalysis` |
| **Engine 3** | **Action Intelligence** | Discovers requested, encouraged, or implicit user actions; models action progression and irreversibility | Engine 1, Engine 2 | `ActionAnalysis` |
| **Engine 4** | **Source Intelligence** | Identifies authoritative registries (SEBI, RBI, NSE, BSE), executes queries, and retrieves official documents | Engine 1, Engine 2, Engine 3 | `SourceAnalysis` |
| **Engine 5** | **Evidence Verification** | Cross-examines extracted claims against authoritative records; determines corroboration or contradiction | Engine 1, Engine 2, Engine 4 | `EvidenceAnalysis` |
| **Engine 6** | **Threat Intelligence** | Reconstructs multi-stage attack paths; identifies threat families, credential abuse, and deception patterns | Engines 1–5 | `ThreatAnalysis` |
| **Engine 7** | **Scam Fingerprint** | Generates structural, privacy-preserving fingerprints; executes collective threat matching; manages deduplicated sightings | Engines 1–6 | `FingerprintAnalysis` |
| **Engine 8** | **Policy & Intervention** | **Sole and final intervention authority**; determines action gating (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`) | Engines 1–7, 9, 10 | `PolicyDecision` |
| **Engine 9** | **Identity Verification** | Resolves claimed advisers, intermediaries, and entities against official registries; checks domain and brand consistency | Engines 1–2, 4–6 | `IdentityAnalysis` |
| **Engine 10** | **Behavioural Signal** | Tracks temporal interaction histories, pressure tactics, escalation patterns, and channel switches | Engines 1–3, Session History | `BehaviouralAnalysis` |

---

## 2. Product Flow

Nivesh Firewall executes seven deterministic lifecycle phases for every evaluated interaction:

1. **OBSERVE**: Content is captured via browser extension active-tab extraction, URL inspection, image OCR, or direct text submission.
2. **UNDERSTAND**: Engine 1 normalizes language, Engine 2 parses atomic claims, and Engine 3 constructs the action sequence.
3. **VERIFY**: Engine 4 queries official regulatory registers (SEBI, RBI, exchanges), Engine 5 evaluates evidentiary support, and Engine 9 validates entity registration numbers and credentials.
4. **IDENTIFY DANGEROUS ACTION**: Engine 6 evaluates irreversible financial exposure (e.g. transfers, credential disclosure, APK installation), while Engine 10 measures behavioural urgency and channel migration.
5. **INTERVENE**: Engine 8 applies precedence rules to emit actionable user interventions:
   - `ALLOW`: Low-risk or informational interaction permitted without friction.
   - `INFORM`: Neutral educational advisory provided without blocking actions.
   - `WARN`: User alerted to unverified claims or structural resemblance to known schemes.
   - `PAUSE`: Action paused with mandatory cooldown or confirmation checkbox.
   - `BLOCK`: High-consequence action obstructed to prevent financial loss.
6. **EDUCATE**: Explanations provide contextual grounding, explaining *why* an intervention occurred, citing specific missing registrations or observed deception indicators.
7. **COLLECTIVE MEMORY**: Engine 7 records privacy-safe structural signatures into collective memory, protecting all network participants against variant attacks.

---

## 3. API Documentation & Contracts

### 3.1 Unified Analysis Endpoint
- **Method & Path**: `POST /api/v1/firewall/analyze`
- **Authentication**: Optional Bearer JWT (rate limit tracked per tenant or client IP).
- **Request Body (`FirewallAnalyzeRequest`)**:
  ```json
  {
    "input_type": "text",
    "text": "Join VIP stock tips group. Guaranteed 40% monthly returns. SEBI registered INA000123456. Transfer ₹10,000 to UPI ID advisor@bank.",
    "channel": "telegram",
    "session_id": "SESS-USER-4019",
    "interaction_history": {
      "session_id": "SESS-USER-4019",
      "events": [
        {
          "event_id": "EVT-001",
          "session_id": "SESS-USER-4019",
          "event_type": "CONTENT_VIEW",
          "timestamp": "2026-10-03T12:00:00Z",
          "channel": "telegram"
        }
      ]
    },
    "metadata": {
      "origin": "https://t.me/advisor_group"
    }
  }
  ```
- **Response Body (`FirewallAnalysisResponse`)**:
  ```json
  {
    "analysis_id": "ORCH-9F83A20B1C4D",
    "session_id": "SESS-USER-4019",
    "pipeline_status": "COMPLETED",
    "created_at": "2026-10-03T12:00:01.120Z",
    "completed_at": "2026-10-03T12:00:01.162Z",
    "decision": {
      "decision": "BLOCK",
      "severity": "CRITICAL",
      "primary_reason": "Blocked high-impact payment requested by unverified entity asserting regulatory credentials.",
      "reason_codes": [
        "UNVERIFIED_REGULATORY_CLAIM",
        "HIGH_IMPACT_PAYMENT_REQUESTED"
      ],
      "explanation": {
        "decision": "BLOCK",
        "user_message": "Action blocked: The entity claims SEBI registration INA000123456, but authoritative records failed to corroborate registration.",
        "technical_message": "DECISION=BLOCK | RULE=RULE-BLOCK-01 | SEVERITY=CRITICAL"
      },
      "actions_required": ["HALT_PAYMENT"],
      "required_user_confirmation": false,
      "cooldown_seconds": 60
    },
    "threat": {
      "threat_signals": ["UNVERIFIED_AUTHORITY", "PROMISED_RETURNS", "DIRECT_PAYMENT"],
      "attack_stage": "CREDENTIAL_SOLICITATION",
      "threat_families": ["ADVANCE_FEE_FRAUD"],
      "confidence": 0.95
    }
  }
  ```

### 3.2 Secure Analysis Retrieval
- **Method & Path**: `GET /api/v1/firewall/analysis/{analysis_id}`
- **Security**: IDOR protected. Analyses associated with an authenticated user or organization are inaccessible to unauthorized callers (returns `404 Not Found`).

### 3.3 System Health & Telemetry
- `GET /health/live`: Fast liveness check verifying HTTP server responsiveness without database hits.
- `GET /health/ready`: Deep readiness check validating database connectivity, migration status, and core engine availability. Returns `503 Service Unavailable` on database outage.
- `GET /api/v1/metrics`: Prometheus (`text/plain; version=0.0.4`) and JSON operational telemetry.

---

## 4. Deployment Guide

### Environment Variables
Production deployments require non-default, high-entropy secrets and explicit configurations:

```ini
NIVESH_ENV=production
NIVESH_DEBUG=false
NIVESH_DATABASE_URL=postgresql://nivesh_user:StrongPassword@postgres:5432/nivesh_db
NIVESH_SECRET_KEY=32_byte_minimum_high_entropy_secret_key_generated_via_openssl
NIVESH_ALLOWED_ORIGINS=["https://app.nivesh.ai"]
NIVESH_SOURCE_MODE=FIXTURE
NIVESH_RATE_LIMIT_PER_MINUTE=120
```

### Preflight & Startup Procedure
1. **Preflight Validation & Migrations**:
   ```bash
   python scripts/entrypoint.py --check-only
   ```
2. **Container Launch**:
   ```bash
   docker compose up -d --build
   ```
3. **Verify Deployment Health**:
   ```bash
   curl -f http://localhost/health/ready
   ```

### Graceful Shutdown
Containers handle `SIGTERM` cleanly. Active analysis requests are allowed up to 15 seconds to persist before database connection pools are closed.

---

## 5. Security & Privacy Model

### Authentication & Authorization
- **Bearer Tokens**: Signed using HMAC-SHA256 with expiration and role claims (`user`, `analyst`, `admin`, `service`).
- **Administrative Endpoints**: Access to `/api/v1/admin/audit-logs` and `/api/v1/fingerprints/create` requires `admin` role.
- **IDOR Defense**: All analysis records enforce ownership checks; unauthorized attempts are concealed via HTTP 404 to prevent enumeration.

### Privacy Guarantees
- **Zero Surveillance**: Extension runs with `activeTab` permission; no background keystroke logging or cross-tab tracking.
- **Data Scrubbing**: Passwords, OTPs, PINs, CVVs, full card numbers, and banking credentials are systematically stripped before persistence or log emission.
- **Structural Anonymization**: Collective memory fingerprints store only normalized abstract structures (e.g. `ACTION:PAYMENT|CHANNEL:TELEGRAM`), never user identity data.

---

## 6. Operational Runbook

| Incident Type | Observed Symptoms | Immediate Mitigation | Recovery Procedure |
| :--- | :--- | :--- | :--- |
| **Database Failure** | `/health/ready` returns 503; persistence errors logged | System auto-degrades to fail-safe in-memory mode | Restart PostgreSQL service; check volume storage; verify migrations |
| **Registry Outage** | External SEBI/RBI HTTP timeouts | Source Engine marks sources as `SOURCE_UNAVAILABLE` | Pipeline safely emits `WARN`/`PAUSE`; verification is never fabricated |
| **High Latency** | Request duration > 200ms | Switch `NIVESH_SOURCE_MODE` to `CACHE` or `FIXTURE` | Inspect network egress; check database connection pool saturation |
| **Engine Crash** | Trace shows engine failure | `SafeEngineExecutor` isolates crash; pipeline finishes in `DEGRADED` | Inspect error trace ID in structured logs; patch regex/parser |

---

## 7. Known Limitations

1. **OCR Multimodal Input**: Image analysis accuracy depends on image clarity and orientation. Heavily compressed or stylized screenshots may yield partial text extractions.
2. **External Registry Latency**: When operating in `LIVE` source mode, response latency is subject to external regulatory portal uptime. The system defaults to bounded timeouts and fallback caching.
3. **Browser Compatibility**: Extension Manifest V3 is optimized for Chromium-based browsers (Chrome, Edge, Brave); Firefox requires MV2/MV3 cross-compilation target.
4. **Single-Node Rate Limiting**: The built-in rate limiter utilizes in-memory sliding windows. Distributed multi-node clusters should deploy Redis or an API gateway rate limiter.

---

## 8. Release Candidate Verification Gate

The Release Candidate was validated across the entire test suite and production build toolchains:

| Verification Suite | Test Count | Result | Duration |
| :--- | :---: | :---: | :---: |
| **Backend Full Regression** | 600 tests | **100% Passed (600/600)** | 10.8s |
| **Frontend Test Suite** | 103 tests | **100% Passed (103/103)** | 15.5s |
| **Browser Extension Suite** | 141 tests | **100% Passed (141/141)** | 7.6s |
| **Production Readiness Suite** | 20 tests | **100% Passed (20/20)** | 2.5s |
| **Final RC Audit Suite** | 19 tests | **100% Passed (19/19)** | 2.0s |
| **Frontend Production Build** | Vite + TS | **Clean Build (0 errors)** | 841ms |
| **Extension Production Build** | Vite + TS | **Clean Build (0 errors)** | 141ms |

### Final Release Version
- **Tag**: `v1.0.0-rc1`
- **Release Version**: `1.0.0-rc1`
- **Engine Version**: `1.0.0`
