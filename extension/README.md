# Nivesh Firewall Browser Extension (Phase 13.1, 13.2 & 13.3)

The **Nivesh Firewall Browser Extension** provides real-time financial content protection and pre-action intervention directly in Chromium-compatible browsers.

- **Phase 13.1**: Extension Foundation (MV3 manifest, service worker, content script, typed messaging, least-privilege permissions, API client).
- **Phase 13.2**: Page & Content Capture (User-initiated capture, 3 capture modes, visible text extraction, selection validation, URL privacy, compact preview, strict credential exclusion).
- **Phase 13.3**: Nivesh Analysis Bridge (Unified Firewall API integration, request correlation, tab-scoped session isolation, multi-tab isolation, bounded retry, Engine 8 intelligence preservation, safe fallback, web-app deep link handoff).

---

## 1. Architecture Overview

```text
                  WEBPAGE
                     │
          ┌──────────┴──────────┐
          │                     │
   User-selected text      Current page
          │                     │
          └──────────┬──────────┘
                     ↓
               Content Script
               (extractor.ts)
                     ↓
                 Sanitizer
               (sanitizer.ts)
                     ↓
            Background Service Worker
               (handlers.ts)
                     ↓
            Nivesh Analysis Bridge
             (analysisBridge.ts)
                     ↓
     Unified Firewall API (Backend)
      POST /api/v1/firewall/analyze
                     ↓
        Product Orchestrator (Phase 11.1)
                     ↓
        Nivesh Intelligence Pipeline
         (Engines 1 through 10)
                     ↓
            Engine 8 Policy Engine
                     ↓
        Unified Firewall Analysis Result
                     ↓
            Popup Result Summary
                     ↓
       Web Application Handoff Deep Link
       (/#protect?id={analysis_id})
```

### Component Responsibilities

| Component | Responsibility | Constraints |
| :--- | :--- | :--- |
| **Popup UI** | Presents 3 explicit capture triggers (`Selected Text`, `Current Page`, `Page URL`), renders compact preview before submission, and displays Engine 8 decision summary and intelligence chips. | Strictly uses `textContent` to prevent XSS. Disables buttons for unsupported browser-internal pages (`chrome://`, etc.). |
| **Content Script** | Extracts visible page text or highlighted selection on demand; checks selection state (`CHECK_SELECTION`). | Never accesses `<input type="password">`, OTP, PIN, CVV, card numbers, or hidden inputs. No keystroke listeners. |
| **Sanitizer Layer** | Normalizes whitespace, removes control characters, and redacts accidental credit card numbers, CVVs, and PINs. | Rejects payloads exceeding maximum character limits (`CONTENT_TOO_LARGE`). |
| **URL Privacy Layer** | Separates full `analysisInputUrl` (sent to backend) from sanitized `displayUrl` (stripped of tracking codes and sensitive query tokens). | Flags unsupported internal schemes (`chrome:`, `edge:`, `about:`, `devtools:`). |
| **Background Worker** | Coordinates request correlation (`capture_id` → `request_id` → `analysis_id`), manages isolated tab state, and routes to Analysis Bridge. | Zero local threat scoring or policy intelligence. |
| **Analysis Bridge** | Canonical typed bridge submitting to `POST /api/v1/firewall/analyze`. Handles request validation, bounded retry, safe fallback, and safe telemetry. | Zero intelligence logic. Preserves Engine 8 decision and all engine findings unchanged. |
| **Extension API Client** | HTTP client for health checks (`GET /api/v1/health`) and API calls. | Never calls individual backend engines directly. No secrets stored in bundle. |

---

## 2. Capture-to-Analysis Lifecycle (Phase 13.3)

```text
USER ACTION
    ↓
CAPTURE
    ↓
SANITIZE
    ↓
BRIDGE REQUEST
    ↓
UNIFIED FIREWALL API
    ↓
ORCHESTRATOR
    ↓
ENGINE PIPELINE (E1 - E10)
    ↓
ENGINE 8 DECISION
    ↓
UNIFIED ANALYSIS
    ↓
EXTENSION SUMMARY
    ↓
OPTIONAL WEB-APP DETAIL
```

### 1. Request Correlation (Section 4)
The bridge coordinates and preserves the canonical identifier chain:
```text
capture_id  (CAP-...)
    ↓
request_id  (EXT-...)
    ↓
analysis_id (ORCH-... / ANA-...)
```

### 2. Session Isolation (Section 5 & 29)
- Sessions are tab-scoped (`SESS-TAB-{tabId}-{timestamp}`).
- Consecutive requests within the same browser tab preserve session continuity for multi-turn behavioral analysis (Engine 10).
- Separate tabs maintain isolated sessions to prevent behavioral contamination across unrelated web browsing contexts.

### 3. Multi-Tab Isolation (Section 28)
- Tab states are stored in isolated runtime memory (`Map<number, TabRuntimeState>`).
- Running a scan on Tab A does not affect or overwrite the analysis state on Tab B.

### 4. Bounded Retry Strategy (Section 11)
- **Transient failures** (network error, HTTP 500/502/503/504, request timeout): Retried at most **1 time** (2 attempts maximum) with a 500ms backoff.
- **Client/Input errors** (HTTP 400, `INVALID_REQUEST`, `UNSUPPORTED_INPUT`): **Never retried**. Fails immediately without wasting requests.

### 5. Safe Fallback Principle (Section 20)
- If the backend is offline, times out, or returns a malformed response:
  - Extension displays `Nivesh protection service is unavailable` or `BACKEND_TIMEOUT`.
  - **UNAVAILABLE is NEVER converted to ALLOW or "Safe"**.
  - No assumption of safety is made when analysis cannot complete.

### 6. Web Application Handoff (Section 15 & 17)
- Result card provides a direct link: `"Open Full Intelligence in Web App ↗"`.
- Handoff URL uses only the safe analysis reference: `http://localhost:5173/#protect?id={analysis_id}`.
- Raw text, passwords, OTPs, credentials, or sensitive page contents are **never** included in the URL or query parameters.

### 7. Zero Frontend Intelligence (Section 25)
- The extension contains zero threat scoring, policy classification, or risk heuristic logic.
- All decisions (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`) and intelligence findings (claims, actions, evidence, identity, threat, fingerprint, behaviour) originate directly from Engine 8 and backend engines.

---

## 3. Privacy Safeguards & Telemetry (Section 22 & 23)

- **Sanitized Telemetry Logging**:
  Logs include only metadata:
  ```json
  {
    "tag": "[Nivesh Bridge]",
    "requestId": "EXT-...",
    "captureId": "CAP-...",
    "analysisId": "ANA-...",
    "sourceType": "SELECTED_TEXT",
    "status": "COMPLETED",
    "durationMs": 45,
    "retries": 0
  }
  ```
  Zero raw text, passwords, OTPs, credit cards, or full API response bodies are written to logs.

---

## 4. Development & Testing Commands

From the `extension/` directory:

```bash
# Run all unit, privacy, capture, and bridge tests (13 test files, 92 tests)
npm test

# Run linter (Oxlint)
npm run lint

# Run bundle smoke test
npm run test:smoke

# Build production extension (TypeScript + Vite)
npm run build
```

Compiled output is located in `extension/dist/`.

To load in Chromium browsers:
1. Navigate to `chrome://extensions/`
2. Enable **Developer mode**.
3. Click **Load unpacked** and select `extension/dist/`.
