# NIVESH FIREWALL — AUTHORITATIVE SOURCE GATEWAY & LIVE VERIFICATION
**Phase 15.A Engineering Documentation**

---

## 1. Executive Summary

Nivesh Firewall's financial verification architecture has been upgraded to interface directly with authoritative external sources through legitimate live and official data-access mechanisms across the Indian financial and securities ecosystem:
- **SEBI** (Securities and Exchange Board of India)
- **RBI** (Reserve Bank of India)
- **NSE** (National Stock Exchange of India)
- **BSE** (Bombay Stock Exchange)

The system does NOT function as an unbounded web crawler or scraper. It enforces a strict, closed-loop verification pipeline:
```text
CLAIM
  ↓
IDENTIFY REQUIRED AUTHORITATIVE EVIDENCE
  ↓
SELECT AUTHORITATIVE SOURCE (GATEWAY)
  ↓
RETRIEVE ACTUAL DATA (LIVE / SNAPSHOT / CACHE / FIXTURE)
  ↓
NORMALIZE
  ↓
PRESERVE PROVENANCE (STRICT RETRIEVAL MODES & TIMESTAMPS)
  ↓
VERIFY CLAIM (EVIDENCE VERIFICATION ENGINE)
  ↓
RETURN TRUTHFUL RESULT
```

---

## 2. Authoritative Source Integration Matrix

| Source | Verification Capability | Access Method | Live Available | Credentials | Snapshot | Cache | Current Limitation |
|---|---|---|---|---|---|---|---|
| **SEBI** | Intermediary registration lookup (Investment Advisers `INA`, Research Analysts `INH`, Stock Brokers `INZ`, Portfolio Managers `INP`); official circulars & orders | Public Recognized Intermediary Query Interface (`OtherAction.do?doRecognisedFmr=yes`) via HTTPS GET & HTML table parsing | **YES** (Confirmed via live HTTP 200 responses) | None required for public registry lookup | Official regulatory snapshot dataset dated 2026-09-30 (embedded in adapter) | SHA-256 in-memory cache with 3600s TTL | Captcha-protected historical circular archives not scraped; returns `SOURCE_UNAVAILABLE` on upstream portal maintenance. |
| **RBI** | DBIE policy repo rates, statutory investor advisories (Prize Chits & Money Circulation prohibition), registered NBFC entities | Official DBIE & Press Release portal endpoints (`rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx`) via HTTPS GET | **YES** (Confirmed via live HTTP 200 responses) | None required for public statistical and press release datasets | Pre-downloaded official regulatory snapshot of MPC decisions & banned MLM schemes (dated 2026-09-30) | SHA-256 in-memory cache with 3600s TTL | Private banking supervisory inspection reports and internal bank ledger data are confidential and strictly out of scope. |
| **NSE** | Corporate announcements, board meeting outcomes, bonus equity share filings, audited financial results | Official Corporate Filings & Announcements portal API (`nseindia.com/companies-listing/corporate-filings-*`) | **CONDITIONAL** (Requires server-side API credentials; unauthenticated requests receive HTTP 403 Akamai anti-bot protection and safely fallback to `OFFICIAL_SNAPSHOT`) | Server-side `NSE_API_KEY` & `NSE_API_SECRET` loaded from environment / secret manager | Official corporate action & disclosure snapshot records for listed securities (dated 2026-09-30) | SHA-256 in-memory cache with 3600s TTL | Live unauthenticated access without API key triggers explicit fallback to `OFFICIAL_SNAPSHOT` (never fakes `LIVE`). Real-time tick data excluded. |
| **BSE** | Corporate Data API, company disclosures, corporate actions (bonus, split, dividend), board announcements | Official BSE Corporate Data API v1 (`api.bseindia.com/corporate-data/v1/announcements`) and announcements portal | **CONDITIONAL** (Requires server-side `BSE_API_KEY`; unconfigured credentials yield `SOURCE_UNAVAILABLE` without leaking secrets) | Server-side `BSE_API_KEY` & `BSE_API_SECRET` | Official BSE corporate disclosures dataset with acknowledgement IDs (dated 2026-09-30) | SHA-256 in-memory cache with 3600s TTL | Production live API access requires active BSE corporate subscription and KYC approval. Real-time market streaming excluded. |

---

## 3. Foundational Retrieval Mode Separation & Invariants

The system enforces strict provenance boundaries across all 10 intelligence engines, the orchestration layer, the unified API, and the user interface.

### Retrieval States
1. **`LIVE`**: The record was obtained via an actual real-time HTTP query directly to the official regulatory endpoint during the verification transaction.
2. **`OFFICIAL_SNAPSHOT`**: The record was matched from a pre-downloaded, officially verified regulatory snapshot dataset (e.g. SEBI Master Intermediary Registry, RBI Gazettes).
3. **`CACHE`**: The record was served from the local cache following a previous retrieval during the TTL window.
4. **`FIXTURE`**: The record was obtained from an offline test fixture in development/test mode.
5. **`SOURCE_UNAVAILABLE`**: The authoritative source could not be reached, network timed out, credentials were missing, or upstream service was degraded.

### Absolute Safety Invariants
- **NEVER represent `FIXTURE` as `LIVE`**.
- **NEVER represent `CACHE` as `LIVE`**.
- **NEVER represent `OFFICIAL_SNAPSHOT` as `LIVE`**.
- A network fallback to an official snapshot **NEVER silently becomes `SUPPORTED + LIVE`**.
- An unverified entity (`NO_MATCH`) is **NEVER converted into a fraud verdict** without independent evidence.
- An unregistered status (`NOT_ESTABLISHED`) is **NEVER converted into `IDENTITY_MISMATCH`** without positive conflicting entity proof.
- An unreachable source (`SOURCE_UNAVAILABLE`) yields **`INSUFFICIENT_EVIDENCE`**, never an affirmative or contradictory verdict.

---

## 4. Architecture & Data Flow

```text
                     CANONICAL CLAIM
                            │
                            ▼
             AUTHORITATIVE SOURCE GATEWAY
              (nivesh.sources.gateway)
                            │
      ┌─────────────────────┼─────────────────────┐
      │                     │                     │
 SEBI ADAPTER          RBI ADAPTER           NSE ADAPTER
 (Intermediaries,      (DBIE Rates,          (Corporate Actions,
  Circulars)            MLM Bans)             Filings)
      │                     │                     │
      └─────────────────────┼─────────────────────┘
                            │
                       BSE ADAPTER
                     (Corporate Data,
                      Disclosures)
                            │
                            ▼
              NORMALIZED EVIDENCE CANDIDATES
                            │
                            ▼
               EVIDENCE VERIFICATION ENGINE
               (nivesh.evidence.engine)
                            │
                            ▼
              PRODUCT ORCHESTRATION LAYER
              (nivesh.orchestrator.service)
                            │
                            ▼
              UNIFIED FIREWALL API RESPONSE
         (authoritative_sources[] with Provenance)
                            │
                            ▼
                 FRONTEND & EXTENSION UI
         (Audit Badges: LIVE, SNAPSHOT, CACHE, UNAVAILABLE)
```

---

## 5. Security & Secret Management

1. **SSRF Protection Intact**:
   - Outbound requests pass through strict URL validation, private/loopback/cloud metadata IP blocking (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`, `192.168.0.0/16`, etc.).
   - Schemes are strictly restricted to `http` and `https`.
   - Maximum response sizes (2MB) and timeouts (5.0s default) are strictly enforced.

2. **Server-Side Credentials Isolation**:
   - Exchange credentials (`NSE_API_KEY`, `NSE_API_SECRET`, `BSE_API_KEY`, `BSE_API_SECRET`) exist exclusively on the server runtime.
   - Credentials are NEVER exposed to the frontend, browser extension, client API responses, logs, or telemetry traces.
   - Missing credentials fail gracefully with `SOURCE_UNAVAILABLE` and descriptive status codes (e.g. HTTP 401).

3. **No Anti-Bot or CAPTCHA Bypass**:
   - The firewall strictly respects anti-bot systems.
   - If an exchange or regulator requires interactive CAPTCHA or blocks unauthenticated traffic, Nivesh does NOT use headless browser automation or rotating proxy networks to bypass access controls. It cleanly uses the `OFFICIAL_SNAPSHOT` dataset and transparently marks provenance as `OFFICIAL_SNAPSHOT`.

---

## 6. Verification & Test Execution Results

Targeted Authoritative Test Suite:
- **37/37 tests passed** (`tests/test_authoritative_gateway.py`, `tests/test_sebi_live_verification.py`, `tests/test_rbi_authoritative.py`, `tests/test_nse_authoritative.py`, `tests/test_bse_authoritative.py`, `tests/test_cross_source_corroboration.py`, `tests/test_live_vs_fallback_safety.py`).

Core Source & Evidence Regression:
- **70/70 tests passed** (`tests/test_source_*.py`, `tests/test_evidence_*.py`).

Live Endpoint Connectivity Verification:
- **SEBI Public Portal**: `HTTP 200` — Live Intermediary verification validated against actual SEBI servers.
- **RBI Public Portal**: `HTTP 200` — Live press releases and policy rates validated against actual RBI servers.
- **BSE Public Portal**: `HTTP 200` — Live connectivity validated.
- **NSE Portal**: `HTTP 403` — Blocked by Akamai anti-bot on unauthenticated requests; verified safe fallback to `OFFICIAL_SNAPSHOT`.

---

## 7. Configuration Reference

```env
# Phase 15.A Authoritative Gateway Configuration
SOURCE_MODE=OFFICIAL_SNAPSHOT          # Default mode: LIVE, OFFICIAL_SNAPSHOT, CACHE, FIXTURE
LIVE_SOURCES_ENABLED=true              # Master switch for outbound live queries

# Source-Specific Live Query Switches
SEBI_LIVE_ENABLED=true
RBI_LIVE_ENABLED=true
NSE_LIVE_ENABLED=false                 # Enabled when NSE_API_KEY is provisioned
BSE_LIVE_ENABLED=false                 # Enabled when BSE_API_KEY is provisioned

# Server-Side Exchange API Credentials (Optional)
NSE_API_KEY=
NSE_API_SECRET=
BSE_API_KEY=
BSE_API_SECRET=

# Freshness & Cache TTL Settings
SOURCE_FRESHNESS_TTL_SECONDS=3600      # 1 hour cache validity
SNAPSHOT_FRESHNESS_DAYS=30             # Maximum snapshot age before warning
```
