# Phase 15.C.2 — NSEPython Provider Integration & Provenance Preservation

## Executive Summary

Phase 15.C.2 establishes an optional, strictly sandboxed connector (`NSEPythonProvider`) within the Nivesh Firewall authoritative source gateway. This connector allows the system to verify corporate actions, corporate announcements, board meetings, and financial results against publicly accessible National Stock Exchange of India (NSE) disclosures while rigorously maintaining security boundaries and provenance truthfulness.

Crucially:
- `NSEPythonProvider` is **optional**: the core firewall operates deterministically whether `nsepython` is installed or not.
- Provenance is **strictly partitioned**: public disclosures retrieved via this connector are labeled `LIVE_PUBLIC`, **never** `LIVE_AUTHORIZED`.
- Security is **hardened**: SSRF protection, HTTPS enforcement, allowed-host whitelisting, rate limiting, and an execution guard that blocks shell execution (`os.popen` / `vpn` mode) are enforced on every outbound request.
- Backward compatibility is **100% preserved**: SEBI, RBI, and BSE adapters are completely unaffected.

---

## 1. Provider Architecture & Priority Model

### 1.1 Provider Hierarchy

The `NSEAdapter` abstracts multiple data retrieval strategies through a unified `BaseNSEProvider` interface:

```text
                        Claim Verification Request (NSE)
                                       │
                                       ▼
                 ┌───────────────────────────────────────────┐
                 │ Are Official API Credentials Configured?  │
                 │              (NSE_API_KEY)                │
                 └─────────────────────┬─────────────────────┘
                                       │
                        YES            │            NO
         ┌─────────────────────────────┘            └─────────────────────────────┐
         ▼                                                                        ▼
┌──────────────────────────────┐                            ┌───────────────────────────────────────────┐
│  OfficialAuthorizedProvider  │                            │ Is Direct Public NSE Connector Permitted? │
│     (LIVE_AUTHORIZED)        │                            │       (public_provider_enabled=True)      │
└──────────────────────────────┘                            └─────────────────────┬─────────────────────┘
                                                                                  │
                                                                   YES            │            NO
                                                    ┌─────────────────────────────┘            └──────────────────────────┐
                                                    ▼                                                                     ▼
                                     ┌──────────────────────────────┐                       ┌───────────────────────────────────────────┐
                                     │      PublicNSEProvider       │                       │ Is Sandboxed NSEPython Provider Enabled   │
                                     │        (LIVE_PUBLIC)         │                       │         & Package Installed?              │
                                     └──────────────────────────────┘                       └─────────────────────┬─────────────────────┘
                                                                                                                  │
                                                                                                   YES            │            NO
                                                                                    ┌─────────────────────────────┘            └──────────────┐
                                                                                    ▼                                                         ▼
                                                                     ┌──────────────────────────────┐                           ┌───────────────────────────┐
                                                                     │      NSEPythonProvider       │                           │     OfficialSnapshot      │
                                                                     │        (LIVE_PUBLIC)         │                           │   / Fixture Fallback      │
                                                                     └──────────────────────────────┘                           └───────────────────────────┘
```

### 1.2 Provider Priority Rules

| Priority | Provider Class | Trigger Condition | Success Mode | Source Authority |
|---|---|---|---|---|
| **1 (Primary Live)** | `OfficialAuthorizedProvider` | `api_key` configured | `LIVE_AUTHORIZED` | `National Stock Exchange of India` |
| **2 (Direct Public)** | `PublicNSEProvider` | Direct public client enabled | `LIVE_PUBLIC` | `NSE-originated public endpoint` |
| **3 (Optional Wrapper)**| `NSEPythonProvider` | `nsepython_enabled=True` & package available | `LIVE_PUBLIC` | `NSE-originated public endpoint` |
| **4 (Snapshot Fallback)**| `OfficialSnapshot` | Credentials absent / live disabled | `OFFICIAL_SNAPSHOT` | `National Stock Exchange of India` |
| **5 (Test Fixture)** | `Fixture` | `default_mode="FIXTURE"` | `FIXTURE` | `National Stock Exchange of India` |

### 1.3 Configuration Flags

The gateway and adapter configuration is controlled via environment variables:

| Environment Variable | Settings Field | Default | Description |
|---|---|---|---|
| `NIVESH_NSE_LIVE_ENABLED` | `nse_live_enabled` | `False` | Master gate permitting live NSE network operations |
| `NIVESH_NSE_PROVIDER_PREFERENCE` | `nse_provider_preference` | `"AUTO"` | Provider selection priority: `AUTO`, `OFFICIAL`, `PUBLIC`, or `NSEPYTHON` |
| `NIVESH_NSEPYTHON_ENABLED` | `nsepython_enabled` | `False` | Explicit gate permitting the optional sandboxed `NSEPythonProvider` |
| `NIVESH_NSE_API_KEY` | `nse_api_key` | `None` | Production authorized API key for legitimate exchange data feeds |
| `NIVESH_NSE_API_SECRET` | `nse_api_secret` | `None` | Production authorized API secret |

---

## 2. Security & Sandboxing Architecture

### 2.1 SSRF & Hostname Enforcement

Every outbound URL resolved by `NSEPythonProvider` must pass two levels of validation before execution:
1. **Generic SSRF Filter (`SsrfValidator.validate_or_raise`)**:
   - Blocks IPv4/IPv6 private ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`).
   - Blocks loopback (`127.0.0.1`, `localhost`, `::1`).
   - Blocks cloud metadata endpoints (`169.254.169.254`).
   - Rejects non-HTTPS schemes (`http://`, `file://`, `ftp://`).
2. **Authoritative Domain Whitelist**:
   Target hosts are restricted strictly to official NSE web and blob storage domains:
   - `nseindia.com`
   - `www.nseindia.com`
   - `archives.nseindia.com`
   - `nsearchives.nseindia.com`
   - `iislliveblob.niftyindices.com`

### 2.2 Rejection of Unsafe Execution Modes

The audit revealed that third-party utilities may attempt to bypass edge bot detection using shell commands or VPN tunnels. Nivesh Firewall permanently forbids these execution paths:
- **`vpn` mode permanently blocked**: Calling `provider.set_mode("vpn")` raises `SecurityError`.
- **Dynamic Mode Audit**: `provider.enforce_safe_mode()` actively inspects `nsepython.mode` and `nsepython.rahu.mode`. Any mode other than `"local"` aborts execution immediately.
- **`os.popen` Interception Guard**: During invocation of `fetch_fn`, `os.popen` is temporarily patched with a protective wrapper that raises `SecurityError("Shell execution via os.popen is strictly forbidden in Nivesh Firewall.")`.

### 2.3 Operational Safeguards

- **Rate Limiting**: Integrated `RateLimiter` enforces client-side request throttling against `www.nseindia.com`.
- **Response Size Bounds**: Outbound responses are capped at `MAX_SOURCE_DOC_BYTES = 5 * 1024 * 1024` (5 MB) to prevent denial-of-service via memory exhaustion.
- **Timeout Limits**: Network timeouts are bounded at `5.0s` by default.
- **No CAPTCHA / WAF Bypass**: If upstream edge protection rejects an unauthenticated public query with HTTP 403 or HTML challenges, the provider emits `ACCESS_UNAUTHORIZED` and safely falls back. It does not attempt automated CAPTCHA solving, session forgery, or unauthorized proxy rotation.

---

## 3. Provenance Preservation Rules

### 3.1 Truthful Mode Classification

Nivesh Firewall strictly enforces that data origins reflect reality:
- **`LIVE_AUTHORIZED`**: Reserved exclusively for authenticated, contracted exchange API products where legitimate production API credentials (`NSE_API_KEY`) were used.
- **`LIVE_PUBLIC`**: Mandatory for data obtained via public web endpoints or third-party scraping libraries.
- **`OFFICIAL_SNAPSHOT`**: Mandatory for verified regulatory snapshot datasets.
- **`CACHE`**: Mandatory for cached authoritative records.
- **`SOURCE_UNAVAILABLE`**: Mandatory when required credentials or packages are missing.

### 3.2 Canonical Provenance Metadata

Every document retrieved via `NSEPythonProvider` populates `AuthoritativeProvenance` as follows:

```json
{
  "source": "NSE",
  "provider": "NSEPythonProvider",
  "retrieval_mode": "LIVE_PUBLIC",
  "access_method": "NSEPython / NSE public endpoint",
  "source_authority": "NSE-originated public endpoint",
  "source_record_id": "INE584A01023",
  "source_reference": "https://www.nseindia.com/api/corporates-corporateActions?index=equities",
  "adapter_name": "NSEAdapter",
  "adapter_version": "1.0.0",
  "response_status": "SUCCESS",
  "freshness": "CURRENT",
  "evidence": "Live NSE corporate disclosure query confirmed record INE584A01023 for NMDC."
}
```

**Prohibited Behaviors**:
- Never rewrite `provider: "NSEPythonProvider"` as `"OfficialAuthorizedProvider"` or `"NSE Official API"`.
- Never rewrite `retrieval_mode: "LIVE_PUBLIC"` as `"LIVE_AUTHORIZED"`.

---

## 4. Normalization Specification

Raw records returned from NSE public endpoints (via JSON or DataFrame rows) are normalized into standard schema fields:

| Field Name | Type | NSE Announcement Source | NSE Corporate Action Source | NSE Event / Board Meeting | Description |
|---|---|---|---|---|---|
| `symbol` | `str` | `symbol` / `sm_symbol` | `symbol` | `symbol` | Exchange trading ticker (e.g. `NMDC`) |
| `company_name` | `str` | `sm_name` / `companyName` | `comp` | `company` | Legal entity name |
| `subject` | `str` | `desc` / `attchmntText` | `subject` | `purpose` / `bm_desc` | Filing subject or resolution text |
| `broadcast_date` | `str` | `an_dt` | `exDate` / `recDate` | `date` | Broadcast or event date |
| `accession_number` | `str` | `seq_id` | `isin` / sequence | `seq_id` / generated ref | Unique filing identifier |
| `url` | `str` | `attchmntFile` (PDF link) | Public action endpoint | Public event endpoint | Source document URL or filing PDF |
| `details` | `str` | Structured text block | Structured text block | Structured text block | Full normalized disclosure content |
| `raw_fields` | `dict` | Raw dictionary | Raw dictionary | Raw dictionary | Preserved raw upstream payload |

---

## 5. Test Evidence Matrix

The dedicated test suite (`tests/test_nsepython_provider.py`) contains 16 automated tests validating all contract guarantees:

| Test ID | Test Name | Purpose | Execution Status |
|---|---|---|---|
| **Test A** | `test_a_optional_dependency_absent` | Proves system starts and routes queries without `nsepython` installed | **PASSED** |
| **Test B** | `test_b_optional_provider_available` | Proves provider initializes in safe `local` mode when package is present | **PASSED** |
| **Test C** | `test_c_live_public_request_execution` | Verifies execution of public corporate filing search | **PASSED** |
| **Test D** | `test_d_real_record_normalization` | Verifies field-by-field normalization of real NSE disclosures | **PASSED** |
| **Test E** | `test_e_evidence_verification_supported` | Verifies numerical evaluator supports matching dividend/bonus claim | **PASSED** |
| **Test F** | `test_f_contradiction_detection` | Verifies numerical evaluator flags contradictory dividend claim | **PASSED** |
| **Test G** | `test_g_provenance_truthfulness` | Verifies strict `LIVE_PUBLIC` and `NSEPythonProvider` labeling | **PASSED** |
| **Test H** | `test_h_failure_handling` | Proves upstream timeout maps to `SOURCE_UNAVAILABLE`, never fake evidence | **PASSED** |
| **Test I** | `test_i_unsafe_mode_blocked` | Proves `vpn` mode and `os.popen` execution are actively blocked | **PASSED** |
| **Test J** | `test_j_ssrf_protection` | Proves loopback, private IP, metadata, HTTP, and non-NSE hosts fail | **PASSED** |
| **Test K** | `test_k_cache_and_snapshot_separation` | Proves snapshots and cache are never mislabeled as `LIVE_PUBLIC` | **PASSED** |
| **Test L** | `test_l_fallback_behavior` | Proves graceful fallback to snapshot on edge firewall HTTP 403 | **PASSED** |
| **Test M** | `test_m_frontend_provenance_contract` | Verifies frontend UI serialization exposes provider & access method | **PASSED** |
| **Test N** | `test_n_full_gateway_integration` | End-to-end multi-engine pipeline: Claim -> Gateway -> Evidence -> Identity -> Policy | **PASSED** |
| **Test O** | `test_o_provider_priority_hierarchy` | Proves official credentials take precedence over optional NSEPython | **PASSED** |
| **Live Probe**| `test_live_nse_public_probe` | Validates live network endpoint schemas against `nseindia.com` | **PASSED** |

---

## 6. Operational Runbook & Configuration Guide

### 6.1 Default Mode (Zero External Dependencies)
By default, Nivesh Firewall runs with `nsepython_enabled=False` and uses official regulatory snapshots for deterministic, offline verification:
```bash
# Default operational state (No optional packages required)
export NIVESH_NSE_LIVE_ENABLED=False
export NIVESH_NSEPYTHON_ENABLED=False
```

### 6.2 Enabling Optional Sandboxed NSEPython Provider
When live public corporate verification is desired in development or staging environments:
1. Install optional dependency:
   ```bash
   pip install nsepython
   ```
2. Enable configuration flags:
   ```bash
   export NIVESH_LIVE_SOURCES_ENABLED=True
   export NIVESH_NSE_LIVE_ENABLED=True
   export NIVESH_NSEPYTHON_ENABLED=True
   export NIVESH_NSE_PROVIDER_PREFERENCE=NSEPYTHON
   ```
3. Verify health via gateway endpoint:
   ```bash
   curl http://localhost:8000/api/sources/health
   ```
   Expected response:
   ```json
   {
     "NSE": {
       "state": "LIVE_AVAILABLE",
       "access_mechanism": "NSE-originated public data (via sandboxed NSEPython provider)",
       "credentials_required": false,
       "has_credentials": true
     }
   }
   ```

### 6.3 Transitioning to Production Authorized Feed
When production exchange feed contracts are provisioned:
```bash
export NIVESH_LIVE_SOURCES_ENABLED=True
export NIVESH_NSE_LIVE_ENABLED=True
export NIVESH_NSE_API_KEY="your-licensed-production-key"
export NIVESH_NSE_API_SECRET="your-licensed-production-secret"
export NIVESH_NSE_PROVIDER_PREFERENCE=AUTO
```
In `AUTO` mode, the presence of `NIVESH_NSE_API_KEY` causes the gateway to immediately prioritize `OfficialAuthorizedProvider`, setting `LIVE_AUTHORIZED` provenance.

---

## 7. Production Readiness Assessment

| Dimension | Assessment | Recommendation |
|---|---|---|
| **Architectural Isolation** | Complete | Provider interface cleanly decouples core gateway from implementation. |
| **Security & Sandboxing** | Robust | SSRF validation, HTTPS whitelist, and `os.popen` guard prevent lateral movement. |
| **Provenance Truthfulness**| Enforced | `LIVE_PUBLIC` cannot be escalated to `LIVE_AUTHORIZED`. |
| **Licensing (GPLv3)** | Isolated | Kept as an optional runtime connector; not statically linked to proprietary core. |
| **Upstream Reliability** | Fragile | Public endpoints are subject to unannounced schema changes and Akamai rate limiting. |
| **Production Recommendation** | Prototype / Dev Only | **Use as optional public connector in development/research; obtain official contracted NSE data product subscription for enterprise production.** |
