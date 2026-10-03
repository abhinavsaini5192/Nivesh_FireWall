# PHASE 15.C.1 — NSEPYTHON COMPATIBILITY & PROVENANCE AUDIT REPORT

## Executive Summary

This report evaluates whether `NSEPython` can safely serve as an optional data connector for Nivesh Firewall's NSE verification workflow. 

**Boundary Status:**
- This phase is an **AUDIT AND PROTOTYPE** phase.
- NSE production LIVE_AUTHORIZED access is **NOT** declared.
- The existing `NSEAdapter` is **PRESERVED** with 100% backward compatibility.
- RBI and BSE adapters remain untouched.
- No new intelligence engine has been introduced.
- Strict provenance boundaries are enforced: `NSEPython ≠ Authorized NSE API`.

---

## 1. Package, Dependency & License Audit

### Package Metadata
| Attribute | Detail |
|---|---|
| **Package Name** | `nsepython` |
| **Evaluated Version** | `2.97` (latest on PyPI) |
| **Author** | Aeron7 (Rahul Mittal) |
| **Repository** | [https://github.com/aeron7/nsepython](https://github.com/aeron7/nsepython) |
| **Python Compatibility** | Python >= 3.10 (tested and verified on Python 3.14.3) |
| **Declaring Homepage** | [https://forum.unofficed.com](https://forum.unofficed.com) |

### License Analysis
- **Verified License:** **GNU General Public License Version 3 (GPL v3)**, confirmed directly from `nsepython-2.97.dist-info/licenses/LICENSE` in the PyPI wheel archive.
- **Project Obligation & Compatibility:** 
  - GNU GPL v3 is a strong copyleft license. 
  - If `nsepython` were included as a mandatory runtime dependency in Nivesh Firewall's `dependencies = [...]` in `pyproject.toml`, the copyleft terms could impose source code disclosure and licensing requirements across the entire Nivesh codebase upon distribution.
  - **Verdict:** `nsepython` **cannot and must not** be a mandatory core dependency. It is isolated as an **optional dependency** under `[project.optional-dependencies] nsepython = ["nsepython>=2.97"]` and accessed dynamically via an isolated provider interface (`NSEPythonProvider`).

### Dependency Footprint
- **Direct Dependencies:** `requests`, `pandas`, `scipy`
- **Transitive Dependencies:** `numpy`, `urllib3`, `certifi`, `idna`, `charset-normalizer`
- **Server Impact:**
  - `pandas` and `scipy` require heavy C-extensions (>100MB disk/memory overhead), which is unnecessarily bloated for a high-performance security firewall core that otherwise relies on lightweight async HTTP (`httpx`) and `pydantic`.
  - Nivesh's `PublicNSEProvider` provides a zero-dependency alternative that directly queries the identical NSE endpoints using Nivesh's native SSRF-safe `httpx` client.

### Internal Implementation & Network Behavior
- **File Structure:** The entire library consists of two files: `__init__.py` and `rahu.py` (966 lines).
- **Session Seed Mechanism:** Every call to `nsefetch(payload)` in `local` mode initiates a fresh `requests.Session()`, makes two sequential GET requests to `https://www.nseindia.com` and `https://www.nseindia.com/option-chain` to acquire cookies, and then issues a third GET request to the target payload.
- **Fragility & Shell Risk:** 
  - In `vpn` mode, `rahu.py` uses `os.popen(f'curl ...')` with string interpolation, presenting a shell-injection vulnerability if untrusted inputs enter payload URLs.
  - In `local` mode, `rahu.py` catches `ValueError` (such as on HTML error pages) and silently returns `{}` instead of raising explicit errors.
  - No SSRF validation or IP blocking is performed by the library natively.

---

## 2. Capability Audit

An empirical audit of `rahu.py` was conducted to determine which operations exist and whether they produce data useful for Nivesh Firewall's corporate disclosure verification:

| Nivesh Requirement | NSEPython Operation | Underlying NSE Endpoint Used | Data Returned | Useful for Verification |
|---|---|---|---|---|
| **Corporate announcements** | `nsefetch(url)` *(No dedicated top-level function in rahu.py)* | `/api/corporate-announcements?index=equities` | JSON list with `symbol`, `sm_name`, `desc`, `an_dt`, `attchmntText`, `attchmntFile` (PDF URL), `seq_id`, `sm_isin` | **YES** |
| **Corporate actions** | `nsefetch(url)` *(No dedicated top-level function in rahu.py)* | `/api/corporates-corporateActions?index=equities` | JSON list with `symbol`, `comp`, `subject` (dividends, splits, bonus), `exDate`, `recDate`, `isin` | **YES** |
| **Board meetings** | `nse_events()` | `/api/event-calendar` | JSON list with `symbol`, `company`, `purpose`, `bm_desc`, `date` | **YES** |
| **Financial results** | `nse_results(index, period)` | `/api/corporates-financial-results?index=equities&period=Quarterly` | JSON list / DataFrame with `companyName`, `broadCastDate`, `financialYear`, `period`, `resultDescription`, `resultDetailedDataLink` | **YES** |
| **Annual reports** | `nsefetch(url)` *(Requires index=cm&symbol=XYZ)* | `/api/annual-reports?index=cm&symbol=` | JSON list with `companyName`, `fromYr`, `toYr`, `broadcast_dttm`, `fileName` (PDF URL) | **YES** |
| **Company metadata** | `nse_eq(symbol)` / `quote_equity(symbol)` | `/api/quote-equity?symbol=` | HTTP 403 Forbidden (Blocked by Akamai edge WAF on automated requests); returns `{}` | **NO (Blocked by WAF)** |

*Note:* Functions for options trading, futures, option chains (`nse_optionchain_scrapper`, `oi_chain_builder`), and technical indicators were identified in `rahu.py` but are strictly excluded as outside Nivesh's verification scope.

---

## 3. Endpoint & Data-Origin Audit

| Endpoint Parameter | Audit Finding |
|---|---|
| **HTTP Method** | `GET` |
| **Target Hosts** | `www.nseindia.com`, `nsearchives.nseindia.com` |
| **Session Requirements** | Browser `User-Agent` (Chrome/Edge), `Accept`, `Accept-Language`, and session cookies seeded from exchange homepage. |
| **Response Format** | `application/json` (or HTML 403 Access Denied when challenged by WAF). |
| **Data Origin** | **NSE-originated public REST endpoint**. These are the identical endpoints consumed by the official NSE corporate filings web application. |
| **Authentication Type** | **Public / Unauthenticated**. No API key or Bearer token is accepted by these web endpoints. Access control is managed exclusively via Akamai Bot Manager and rate limiting. |
| **Rate Limiting** | Aggressive querying (>1-2 req/s) triggers HTTP 403 / 429 IP bans. |
| **Documentation Status** | **Undocumented internal APIs**. NSE reserves the right to alter schemas, parameter names, or cookie policies without notice. |
| **Stable Identifiers** | Announcements include `seq_id` and document PDF URLs; corporate actions include `symbol`, `isin`, and `exDate`; financial results include `seqNumber`. |
| **Source Traceability** | Records contain direct canonical links to official regulatory filings hosted on `https://nsearchives.nseindia.com/corporate/...`. |

---

## 4. Real NSE Record Comparison

Three live records were retrieved directly from official NSE public corporate filing endpoints on **October 3, 2026** and compared field-by-field against NSEPython extraction:

### Record A — Corporate Announcement
```text
Category: Corporate Announcement
Company: Pioneer Embroideries Limited (Symbol: PIONEEREMB)
Date: 03-Oct-2026 14:37:49 (Dissemination: 03-Oct-2026 14:37:50)
NSE Reference: seq_id 106806218 | ISIN INE156C01018
NSEPython Result: Successfully parsed via nsefetch
Matched Fields:
  - symbol: PIONEEREMB
  - company_name: Pioneer Embroideries Limited
  - subject: Structural Digital Database (Compliance certificate for quarter ended 30th September 2026)
  - broadcast_date: 03-Oct-2026 14:37:49
  - accession_number: 106806218
  - attachment_url: https://nsearchives.nseindia.com/corporate/PIONEEREMB_03102026143739_CoveringRegulation30092026.pdf
Mismatches: None. All fields directly mirror authoritative NSE announcement feed.
```

### Record B — Corporate Action
```text
Category: Corporate Action (Dividend)
Company: NMDC Limited (Symbol: NMDC)
Date: Ex-Date: 05-Oct-2026 | Record Date: 05-Oct-2026
NSE Reference: ISIN INE584A01023 | Series EQ
NSEPython Result: Successfully parsed via nsefetch
Matched Fields:
  - symbol: NMDC
  - company_name: NMDC Limited
  - subject: Dividend - Re 1 Per Share
  - face_value: 1
  - ex_date: 05-Oct-2026
  - record_date: 05-Oct-2026
  - isin: INE584A01023
Mismatches: None. Corporate action payout and dates match official filing records.
```

### Record C — Board Meeting
```text
Category: Board Meeting Intimation
Company: D. P. Abhushan Limited (Symbol: DPABHUSHAN)
Date: 05-Oct-2026
NSE Reference: Event Calendar Intimation
NSEPython Result: Successfully parsed via nse_events()
Matched Fields:
  - symbol: DPABHUSHAN
  - company_name: D. P. Abhushan Limited
  - purpose: Fund Raising/Other business matters
  - bm_desc: Board Meeting Intimation for Considering Raising Of Funds By Issuance Of Equity Shares And/Or Warrants...
  - meeting_date: 05-Oct-2026
Mismatches: None. Board meeting description and agenda match official exchange calendar.
```

---

## 5. Provenance Architecture & Provider Boundaries

To guarantee that unofficial web data is **never conflated** with authorized exchange API data, Nivesh Firewall enforces an explicit Conceptual Provider Boundary within `NSEAdapter`:

```text
                  Authoritative Source Gateway
                               │
                           NSEAdapter
                               │
    ┌──────────────────────────┼──────────────────────────┐
    │                          │                          │
OfficialAuthorizedProvider   PublicNSEProvider     NSEPythonProvider
    │                          │                          │
Production Exchange API      SSRF-Safe Native HTTP     Sandboxed Unofficial Wrapper
Status: LIVE_AUTHORIZED      Status: LIVE_PUBLIC       Status: LIVE_PUBLIC
Auth: Authorized API         Auth: Public Endpoint     Auth: Public Endpoint (via NSEPython)
```

### Strict Provenance Rules:
1. **No Accidental Authorization Claim:**
   - Data retrieved via `NSEPythonProvider` receives `retrieval_mode: LIVE_PUBLIC`.
   - It is **strictly forbidden** to assign `LIVE_AUTHORIZED` or `LIVE` to NSEPython data.
   - The UI displays:
     ```text
     Source: NSE
     Access: NSEPython / NSE public endpoint
     Authority: NSE-originated public endpoint
     Mode: LIVE_PUBLIC
     ```
   - The UI **never** displays: `"Verified by official NSE API"` when accessed through NSEPython.
2. **Offline Fallback Preservation:**
   - If an endpoint times out, is blocked by WAF (403), or fails, it produces `retrieval_mode: SOURCE_UNAVAILABLE` or falls back to `OFFICIAL_SNAPSHOT` / `FIXTURE`.
   - Network failure never produces a fake `SUPPORTED` or fake `LIVE` result.

---

## 6. Security, SSRF & Operational Resilience

### Security Constraints:
1. **SSRF Sandboxing:**
   - `NSEPythonProvider` validates all target URLs through Nivesh's `SsrfValidator` before any request is dispatched.
   - Private IP addresses (`127.0.0.1`, `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), AWS/cloud metadata (`169.254.169.254`), and non-NSE domains are strictly blocked.
2. **No Shell Execution:**
   - The `vpn` mode of `rahu.py` (which invokes `os.popen(f"curl ...")`) is disabled and blocked.
3. **No Credential Bypasses or Proxy Rotation:**
   - No CAPTCHAs are bypassed.
   - No proxy rotators or credential circumvention methods are permitted.
   - If Akamai issues an HTTP 403 challenge, the adapter records `ACCESS_UNAUTHORIZED` and gracefully falls back to snapshot.

---

## 7. Evidence Verification Integration (Engine 5)

Normalized records produced by the prototype were tested against Engine 5's `NumericalEvaluator`:

1. **Supporting Claim:**
   - **Claim:** *"NMDC announced a dividend of ₹1 per share."*
   - **Authoritative Filing:** *"Dividend - Re 1 Per Share"*
   - **Engine 5 Result:** `SUPPORTED` (Confidence: 0.98, Evidence Strength: HIGH).
2. **Contradicting Claim:**
   - **Claim:** *"NMDC announced a dividend of ₹50 per share."*
   - **Authoritative Filing:** *"Dividend - Re 1 Per Share"*
   - **Engine 5 Result:** `CONTRADICTED` (Confidence: 0.96, Evidence Strength: HIGH).
3. **Failure Isolation:**
   - Upstream network errors or missing packages produce `SOURCE_UNAVAILABLE` and do not generate false contradictions or false confirmations.

---

## 8. Final Audit Recommendation

Based on empirical testing, dependency footprint inspection, license review, and security audit:

```text
RECOMMENDATION:
INTEGRATE AS OPTIONAL PROVIDER
```

### Justification:
1. **Data Legitimacy:** NSEPython retrieves genuine NSE-originated public filings (corporate announcements, corporate actions, board meetings, and financial results).
2. **License Isolation:** Because `nsepython` is licensed under GNU GPL v3, it must remain an **optional, isolated connector** (`NSEPythonProvider`) and must never be bundled into Nivesh's core mandatory dependencies.
3. **Sandboxing Required:** To run safely, NSEPython must be wrapped in Nivesh's SSRF validator, timeout controllers, and provenance mappers.
4. **Distinct Provenance:** Its output must strictly be classified as `LIVE_PUBLIC`, preserving a clear operational distinction from future production-licensed `LIVE_AUTHORIZED` NSE data feeds.

---
*Audit Completed on October 3, 2026 | Nivesh Firewall Security Engineering*
