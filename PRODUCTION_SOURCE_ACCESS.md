# PRODUCTION SOURCE ACCESS & AUTHORITATIVE VERIFICATION MATRIX

## Nivesh Firewall — Phase 15.B Authoritative Source Readiness

This document defines the production access architecture, credential isolation policy, real-record verification evidence, and operational diagnostics for authoritative financial and regulatory sources within Nivesh Firewall.

---

## 1. Provider Access & Capability Matrix

| Source | Capability | Access Mechanism | LIVE Access | Credentials Required | Actual Live Test | Snapshot | Cache | Limitation |
|---|---|---|---|---|---|---|---|---|
| **SEBI** | Investment Adviser, Research Analyst, Stock Broker Registry Lookup | Official Recognised Intermediary Search (HTTPS GET) | **YES (Verified)** | No (Public Regulatory Registry) | **PASSED (2026-10-03)**<br>`360 ONE` (`INA000000888`) | YES (`2026-09-30`) | YES (TTL: 3600s) | Rate limited to 1 req/sec; Anti-bot header compliance; Contact PII (phone/email) stripped |
| **RBI** | Monetary Policy Repo Rates, Benchmark Metrics, NBFC Registry | Official DBIE & Statutory Publication Access (HTTPS GET) | **YES (Verified)** | No (Public Statutory Publications) | **PASSED (2026-10-03)**<br>MPC Repo Rate `6.50%` | YES (`2026-09-30`) | YES (TTL: 3600s) | Macro statistics separated from intermediary licensing; DBIE format shifts |
| **NSE** | Corporate Filings, Board Meeting Outcomes, Bonus/Split Disclosures | NSE Corporate Announcements API (Enterprise HTTPS API) | **CREDENTIALS_MISSING** (Unless Configured) | **YES** (`NSE_API_KEY`, `NSE_API_SECRET`) | Tested with missing creds & mock auth | YES (`2026-09-30`) | YES (TTL: 3600s) | Requires licensed data subscription; Akamai WAF blocks non-API web crawlers; LIVE differs from UAT |
| **BSE** | Corporate Announcements, Corporate Actions, Company Data | BSE Corporate Data API v1 (Authorized HTTPS API) | **CREDENTIALS_MISSING** (Unless Configured) | **YES** (`BSE_API_KEY`, `BSE_API_SECRET`) | Tested with missing creds & mock auth | YES (`2026-09-30`) | YES (TTL: 3600s) | Requires licensed Corporate Data API subscription; Production server IP restriction applies |

> [!IMPORTANT]
> **Zero Credential Faking Principle**:
> Where API credentials have not been configured (`NSE_API_KEY`, `BSE_API_KEY`), Nivesh Firewall explicitly reports `CREDENTIALS_MISSING`. It **NEVER** silently falls back to an invented response and labels it as `LIVE`.

---

## 2. Server-Side Secret Management & Isolation

Credentials for licensed stock exchange APIs and external services remain strictly isolated to the server runtime environment:

1. **Server-Side Only**: Loaded via environment variables (`NIVESH_NSE_API_KEY`, `NIVESH_NSE_API_SECRET`, `NIVESH_BSE_API_KEY`, `NIVESH_BSE_API_SECRET`) through Pydantic `Settings`.
2. **Never Exposed**:
   - Never packaged in Frontend React/Vite builds.
   - Never packaged in Browser Extension scripts (`manifest.json`, background service worker, content scripts).
   - Never stored in Git or version-controlled files (`.env` is strictly gitignored; only `.env.example` is committed).
   - Never persisted in SQLite or PostgreSQL database records.
   - Never included in HTTP API responses (the `/api/v1/sources/health` diagnostics endpoint returns boolean `has_credentials` flags, never raw secret strings).
   - Automatically redacted by `SensitiveDataRedactor` and `settings.safe_dump()` across all system logs and distributed traces.

---

## 3. SEBI Real-Record Verification (Engine 4 & Engine 9)

### 3.1 Live Access Endpoint
- **URL**: `https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13&search={query}`
- **Protocol**: HTTPS GET with standard modern browser headers (`User-Agent`, `Accept: text/html,application/xhtml+xml`).
- **Parsing**: Standard HTML DOM table and Bootstrap card containers (`.card-table-left`, `.card-table-right`, `.card-view`).

### 3.2 Actual Live Verification Execution
On **2026-10-03**, a real live query was executed against the live SEBI registry:

```text
REAL CLAIM:
"360 ONE Investment Adviser and Trustee Services Limited is registered as a SEBI Investment Adviser."
        ↓
GATEWAY ROUTING:
Target: sebi_recognised_intermediaries (Primary Official Authority)
        ↓
LIVE REQUEST:
GET https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFpi=yes&intmId=13&search=360+ONE
HTTP Status: 200 OK
        ↓
EXTRACTED REAL RECORD:
Registration Number: INA000000888
Entity Name: 360 ONE Investment Adviser and Trustee Services Limited
Category: Investment Adviser
Registration Status: CURRENT
Address: IIFL Centre, Kamala Mills, Senapati Bapat Marg, Lower Parel, Mumbai (PII redacted)
        ↓
PROVENANCE:
Source: SEBI
Source Authority: Securities and Exchange Board of India
Retrieval Mode: LIVE
Freshness: CURRENT
Record ID: INA000000888
        ↓
EVIDENCE VERIFICATION (Engine 5):
Status: SUPPORTED
Confidence: 0.98
        ↓
IDENTITY RESOLUTION (Engine 9):
Claimed Entity: 360 ONE Investment Adviser and Trustee Services Limited
Match Status: ESTABLISHED
Confidence: 0.95
```

### 3.3 Privacy & PII Protection
Public regulatory registries sometimes display phone numbers and personal compliance email addresses. In accordance with Nivesh privacy policies:
- Phone numbers (`\+91\d+`, `\d{10}`) and email addresses are automatically stripped by `SEBIAdapter._parse_sebi_html_table()` before being placed into normalized content, evidence items, or user-facing UI cards.

### 3.4 Nonexistent Registration Handling
A search for nonexistent registration `INA999999999`:
- Returns `NO_MATCH` from the registry.
- Resolves to `NOT_ESTABLISHED` in Identity Verification.
- **Invariant**: Does **NOT** falsely fabricate `FRAUD` or `IDENTITY_MISMATCH` without positive conflicting evidence.

---

## 4. RBI Authoritative Access (Engine 4 & Engine 5)

### 4.1 Access Mechanism
- **Data Source**: Database on Indian Economy (DBIE) and official statutory press releases / master directions at `https://www.rbi.org.in`.
- **Supported Claims**:
  1. **Monetary Policy Benchmark Rates**: Repo rate (6.50%), SDF (6.25%), MSF (6.75%), Bank Rate (6.75%).
  2. **Statutory Prohibitions**: Prize Chits and Money Circulation Schemes (Banning) Act, 1978 advisory prohibiting unauthorized deposit taking and MLM schemes.
  3. **NBFC Master Registry**: Verification of authorized non-banking financial companies (e.g. Bajaj Finance Limited `B-13.00407`).
- **Authentication**: Public statutory access; no commercial API key required.

---

## 5. Stock Exchanges: NSE & BSE Production Access

### 5.1 NSE (National Stock Exchange of India)
- **Product Requirement**: NSE Corporate Filings and Announcements API.
- **Access Architecture**:
  - Live access requires commercial enterprise credentials.
  - Direct web scraping of `nseindia.com` is prohibited by Akamai bot-mitigation policies and terms of service; Nivesh Firewall strictly complies and does not use unauthorized bypasses or proxies.
- **Operational States**:
  - `CREDENTIALS_MISSING`: When `NIVESH_NSE_API_KEY` is null.
  - `ACCESS_UNAUTHORIZED`: When upstream API returns HTTP 401/403.
  - `LIVE`: When authorized API credentials return HTTP 200 JSON.

### 5.2 BSE (Bombay Stock Exchange)
- **Product Requirement**: BSE Corporate Data API v1.
- **Access Architecture**:
  - Dedicated HTTPS JSON API at `api.bseindia.com`.
  - Authenticated via `X-BSE-API-KEY`.
- **Operational States**:
  - `CREDENTIALS_MISSING`: When `NIVESH_BSE_API_KEY` is null.
  - `ACCESS_UNAUTHORIZED`: When API key is expired or invalid.
  - `LIVE`: When authorized API key returns valid announcements JSON.

---

## 6. Operational Health Diagnostics API

The system exposes operational source health and credential readiness via:
`GET /api/v1/sources/health`

### Response Payload Structure
```json
{
  "timestamp": "2026-10-03T08:15:22.880303+00:00",
  "summary": {
    "SEBI": "LIVE_AVAILABLE",
    "RBI": "LIVE_AVAILABLE",
    "NSE": "CREDENTIALS_MISSING",
    "BSE": "CREDENTIALS_MISSING"
  },
  "sources": {
    "SEBI": {
      "source_identifier": "SEBI",
      "authority_name": "Securities and Exchange Board of India",
      "state": "LIVE_AVAILABLE",
      "access_mechanism": "Official Intermediary Registry Search (HTTPS GET)",
      "credentials_required": false,
      "has_credentials": true,
      "live_supported": true,
      "snapshot_fallback_available": true,
      "limitations": [
        "Public registry search rate-limited to 1 req/sec",
        "Requires anti-bot header compliance",
        "Personal contact PII redacted from evidence display"
      ],
      "diagnostic_message": "Official Intermediary Registry live search active"
    },
    "NSE": {
      "source_identifier": "NSE",
      "authority_name": "National Stock Exchange of India",
      "state": "CREDENTIALS_MISSING",
      "access_mechanism": "NSE Official Corporate Announcements API (Authorized HTTPS API)",
      "credentials_required": true,
      "has_credentials": false,
      "live_supported": true,
      "snapshot_fallback_available": true,
      "limitations": [
        "Authorized API product subscription required",
        "Akamai / anti-bot controls prevent unauthorized web scraping",
        "LIVE credentials differ from UAT credentials"
      ],
      "diagnostic_message": "NSE API credentials missing (NSE_API_KEY unconfigured). Requires authorized product access."
    }
  }
}
```

---

## 7. Frontend Provenance Presentation

The frontend components (`ClaimEvidenceDetailCard` and `ProvenanceAuditPanel`) display:
1. **Source Authority**: Formal name of the regulator/exchange.
2. **Retrieval Mode Badge**:
   - `LIVE: Checked Live` (Green)
   - `OFFICIAL SNAPSHOT: Downloaded Dataset` (Blue)
   - `CACHE: Cached Evidence` (Gray)
   - `UNAVAILABLE: Source Unreachable` (Yellow/Orange)
   - `FIXTURE: Test Fixture` (Slate)
3. **Retrieval Timestamp**: Exact ISO-8601 moment of retrieval.
4. **Source Reference**: Clickable URL link or official circular ID.
5. **Record Identifier**: Registration number or accession ID.
6. **Freshness Rating**: `CURRENT`, `HISTORICAL`, `SNAPSHOT`, or `STALE`.

---

## 8. Verification Results

All 10 Phase 15.B test suites execute and pass deterministically:

```bash
pytest tests/test_production_source_access.py -v
```

```text
tests/test_production_source_access.py::test_sebi_real_record_verification_chain PASSED
tests/test_production_source_access.py::test_sebi_nonexistent_record_no_match PASSED
tests/test_production_source_access.py::test_rbi_real_data_verification PASSED
tests/test_production_source_access.py::test_nse_credentials_missing_state PASSED
tests/test_production_source_access.py::test_bse_credentials_missing_state PASSED
tests/test_production_source_access.py::test_live_failure_never_becomes_supported_live PASSED
tests/test_production_source_access.py::test_official_snapshot_mode_preserved PASSED
tests/test_production_source_access.py::test_cache_preserves_original_source_and_timestamp PASSED
tests/test_production_source_access.py::test_cross_source_corroboration PASSED
tests/test_production_source_access.py::test_frontend_provenance_health_contract PASSED
```
