# NIVESH FIREWALL — AUTHORITATIVE SOURCE GATEWAY & FOUR-SOURCE VERIFICATION SYSTEM
**Phase 15.E Engineering Documentation & Production Release Reference**

---

## 1. Executive Summary

Phase 15.E represents the final engineering consolidation of Nivesh Firewall's authoritative-source verification architecture. Nivesh Firewall integrates four primary authoritative institutions across the Indian financial and securities ecosystem:

1. **SEBI** (Securities and Exchange Board of India) — Statutory Intermediary Master Registry, regulatory circulars, and orders.
2. **RBI** (Reserve Bank of India) — Policy rates, MPC gazettes, DBIE publications, registered NBFC entities, and statutory MLM/prize chit prohibitions.
3. **NSE** (National Stock Exchange of India) — Corporate actions (bonus issues, splits, dividends), board meetings, filings, and financial disclosures.
4. **BSE** (Bombay Stock Exchange) — Corporate data API disclosures, scrip filings, corporate action announcements, and statutory filings.

The system does NOT function as a generic crawler or unconstrained scraper. It operates under a deterministic, evidence-based verification pipeline:

```text
Content Input
    ↓
Engine 1: Content Intelligence (Ingestion, Normalization, Entity & Signal Extraction)
    ↓
Engine 2: Claim Intelligence (Modal Claims, Attribution, Verification Requirements)
    ↓
Engine 3: Action Intelligence (Observable Actions, Urgency, Consequential Next Steps)
    ↓
Engine 4: Source Intelligence (Authoritative Gateway Routing & Provider Hierarchy)
    ↓
Engine 5: Evidence Verification (Cross-Source Corroboration, Conflict Detection, Numerical Evaluation)
    ↓
Engine 6: Threat & Attack-Path Intelligence (Consequential Paths, No Psychological Fraud Scoring)
    ↓
Engine 7: Scam Fingerprint & Collective Intelligence (Structural Variant Hashes, Zero PII)
    ↓
Engine 9: Identity Verification & Entity Resolution (Attribution Separation, Lookalike Checks)
    ↓
Engine 10: Behavioural Signal Intelligence (Multi-Step Trajectory & Interaction Velocities)
    ↓
Engine 8: Policy & Intervention Engine (Sole Policy Authority: ALLOW, INFORM, WARN, PAUSE, BLOCK)
```

Truthful, unforgeable provenance is preserved end-to-end.

---

## 2. Four-Source Architecture & Provider Hierarchy

Every supported source routes deterministically through `AuthoritativeSourceGateway` (`nivesh/sources/gateway.py`). Provider selection is deterministic and strictly prioritized; no random or provider-score resolution is used.

### Provider Hierarchy Matrix

| Source | Provider Priority Order | Access Method | Retrieval Modes | Fallback Behavior |
|---|---|---|---|---|
| **SEBI** | 1. `PublicSEBIProvider`<br>2. `OfficialSnapshotSEBIProvider` | HTTPS GET to Recognized Intermediary Query Interface (`OtherAction.do?doRecognisedFmr=yes`) | `LIVE`, `OFFICIAL_SNAPSHOT`, `CACHE`, `SOURCE_UNAVAILABLE` | Live network failure, captcha, or upstream portal outage deterministically falls back to pre-downloaded official regulatory snapshot dataset. |
| **RBI** | 1. `PublicRBIProvider`<br>2. `OfficialSnapshotRBIProvider` | HTTPS GET to DBIE publications & Press Release portal (`rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx`) | `LIVE`, `OFFICIAL_SNAPSHOT`, `CACHE`, `SOURCE_UNAVAILABLE` | Live network failure or upstream portal outage falls back to official MPC & regulatory prohibition snapshot dataset. |
| **NSE** | 1. `OfficialAuthorizedProvider`<br>2. `PublicNSEProvider`<br>3. `NSEPythonProvider`<br>4. `OfficialSnapshotNSEProvider` | Authenticated enterprise API, public portal query, or NSEPython wrapper | `LIVE_AUTHORIZED`, `LIVE_PUBLIC`, `OFFICIAL_SNAPSHOT`, `CACHE`, `SOURCE_UNAVAILABLE` | If API credentials missing or unauthenticated access blocked (Akamai HTTP 403), falls back through Public/NSEPython (`LIVE_PUBLIC`) to `OfficialSnapshotNSEProvider`. |
| **BSE** | 1. `OfficialAuthorizedBSEProvider`<br>2. `PublicBSEProvider`<br>3. `OfficialSnapshotBSEProvider` | Authenticated BSE Corporate Data API v1, public announcements portal, or snapshot | `LIVE_AUTHORIZED`, `LIVE_PUBLIC`, `OFFICIAL_SNAPSHOT`, `CACHE`, `SOURCE_UNAVAILABLE` | If `BSE_API_KEY` missing, falls back to Public Dissemination if enabled; otherwise falls back directly to `OfficialSnapshotBSEProvider`. |

---

## 3. Strict Retrieval Mode & Provenance Semantics

Retrieval modes are never collapsed into a generic "live" state. The firewall preserves truthful semantics at all layers:

1. **`LIVE_AUTHORIZED`**: The query was executed against an official authenticated provider with validated server-side credentials (`NSE_API_KEY` or `BSE_API_KEY`).
2. **`LIVE_PUBLIC`**: The query was executed against an official public endpoint or public library (e.g. `NSEPythonProvider`). **`NSEPythonProvider` is ALWAYS `LIVE_PUBLIC` and NEVER `LIVE_AUTHORIZED`**.
3. **`LIVE`**: The query was executed against an unauthenticated but official regulatory endpoint (e.g. SEBI or RBI public query portals).
4. **`OFFICIAL_SNAPSHOT`**: The query was serviced from pre-verified, tamper-evident regulatory snapshots dated and embedded in the source adapters.
5. **`CACHE`**: The query was serviced from in-memory SHA-256 keyed cache within the configured TTL (`SOURCE_FRESHNESS_TTL_SECONDS`).
6. **`FIXTURE`**: The query was serviced from offline developer test fixtures. Fixtures are strictly isolated to test environments.
7. **`SOURCE_UNAVAILABLE`**: The source could not be contacted, required credentials were not configured, or the upstream endpoint was down.

### Core Invariants

- **A technical source failure is NEVER evidence of fraud.** If SEBI, RBI, NSE, or BSE is offline or times out, the system produces `SOURCE_UNAVAILABLE` and `INSUFFICIENT_EVIDENCE`. It NEVER classifies the subject as fraudulent due to network errors.
- **NEVER report `LIVE` when fallback occurred.** If live retrieval fails and snapshot data is used, the resulting provenance explicitly reports `retrieval_mode = "OFFICIAL_SNAPSHOT"`.
- **Credential isolation.** API keys and secrets exist only in runtime memory. They are redacted in `Settings`, excluded from `safe_dump()`, scrubbed from logs via `scrub_sensitive_tokens`, and stripped from client outputs.

---

## 4. Cross-Source Intelligence & Evidence Correlation

Engine 5 correlates evidence across multiple authoritative sources under the principle of **Evidence Over Guessing**:

### Corroboration Semantics
- When NSE and BSE independently confirm the same corporate action (e.g., dual-listed company bonus ratio or AGM approval), the evidence picture is corroborated.
- Corroboration strengthens the factual basis, but **does NOT artificially multiply or inflate confidence** (no `2 sources = 2x confidence`). Confidence remains strictly bounded ($\le 0.99$).
- Provenance documents both participating sources and their respective provider modes independently.

### Conflict Detection & Preservation
- If Source A (e.g. NSE) and Source B (e.g. BSE) provide conflicting factual assertions (e.g. different record dates or ratios), the conflict is **explicitly preserved** as `SOURCE_CONFLICT`.
- The system never silently chooses whichever source returned first or hides discrepancies.

### Identity Separation
- **Entity Existence $\ne$ Attribution Proof**: Verifying that a research analyst or broker exists in SEBI's registry establishes that the entity exists; it does **not** prove that the current message author is that entity.
- **Absence of Record $\ne$ Criminal Fraud**: If a claimed registration number is not found in SEBI's database, the identity status is `NOT_ESTABLISHED` (or `UNVERIFIED`). It is **never** escalated to `IDENTITY_MISMATCH` or criminal impersonation without evidentiary lookalike or domain conflict proof.

### Numerical Evaluator
- Compares asserted quantitative metrics against official filings:
  - **Exact Match**: Fully supported ratio / amount.
  - **Material Contradiction**: Claimed 5:1 bonus vs. official filing 1:1 bonus yields `CONTRADICTED`.
  - **Missing Elements**: Ratio matches but announcement date is unconfirmed yields `PARTIALLY_SUPPORTED`.

---

## 5. Security & Isolation Boundaries

All four authoritative sources adhere to strict defensive controls:

1. **SSRF Prevention**: All outbound URLs pass through `SsrfValidator`. Private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`, `169.254.169.254`), loopbacks, and non-HTTP/HTTPS schemes are blocked.
2. **Redirect Validation**: Redirects are followed with continuous SSRF re-validation at each hop.
3. **Payload Limits**: Inbound responses are capped at 2MB to prevent memory exhaustion.
4. **Rate Limiting**: Host-level token-bucket rate limiting prevents throttling and denial-of-service.
5. **No Anti-Bot Bypass**: Nivesh does not employ CAPTCHA solving, rotating residential proxies, or headless browser automation to bypass exchange protections. When public access is blocked, it fails safely to official snapshots.
6. **Data Sanitization**: Sensitive inputs (passwords, OTPs, PINs, card numbers) are scrubbed before reaching fingerprints, logs, provenance, threat models, or client outputs.

---

## 6. Configuration & Credential Requirements

```env
# Master Authoritative Gateway Configuration
SOURCE_MODE=OFFICIAL_SNAPSHOT          # Supported: LIVE, OFFICIAL_SNAPSHOT, CACHE, FIXTURE
LIVE_SOURCES_ENABLED=true              # Master outbound switch

# Source-Specific Live Query Switches
SEBI_LIVE_ENABLED=true                 # SEBI public intermediary verification
RBI_LIVE_ENABLED=true                  # RBI public DBIE & press release queries
NSE_LIVE_ENABLED=false                 # Enabled when NSE_API_KEY is provisioned
NSE_PUBLIC_ENABLED=true                # Enabled for NSE public endpoints & NSEPython
BSE_LIVE_ENABLED=false                 # Enabled when BSE_API_KEY is provisioned
BSE_PUBLIC_ENABLED=false               # BSE public dissemination endpoints

# Server-Side Exchange Credentials (Optional)
NSE_API_KEY=
NSE_API_SECRET=
BSE_API_KEY=
BSE_API_SECRET=

# Freshness & Cache Settings
SOURCE_FRESHNESS_TTL_SECONDS=3600      # 1-hour cache lifetime
SNAPSHOT_FRESHNESS_DAYS=30             # Maximum snapshot age
```

### Operational States Matrix

| Condition | Internal Status | Retrieval Mode | Evidence Status | Policy Action |
|---|---|---|---|---|
| Credentials Missing | `CREDENTIALS_MISSING` | `OFFICIAL_SNAPSHOT` or `SOURCE_UNAVAILABLE` | Evaluated against snapshot if available, else `INSUFFICIENT_EVIDENCE` | Proportional intervention based on remaining signals |
| Network Timeout | `TIMEOUT` | `OFFICIAL_SNAPSHOT` or `SOURCE_UNAVAILABLE` | Snapshot fallback or `INSUFFICIENT_EVIDENCE` | No punitive or alarming fraud verdict |
| Upstream HTTP 403 (WAF/Anti-Bot) | `ACCESS_UNAUTHORIZED` | `OFFICIAL_SNAPSHOT` | Fallback to official snapshot | Truthful snapshot provenance |
| Entity Not in Registry | `NOT_FOUND` | Source query successful | `INSUFFICIENT_EVIDENCE` | `NOT_ESTABLISHED` identity status |
| Numerical Value Contradicted | `SUCCESS` | Official filing retrieved | `CONTRADICTED` | `WARN` or `PAUSE` policy intervention |
