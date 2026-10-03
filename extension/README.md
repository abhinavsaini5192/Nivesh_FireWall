# Nivesh Firewall Browser Extension (Phase 13.1 Foundation)

The **Nivesh Firewall Browser Extension** provides real-time financial content protection and pre-action intervention directly in the browser.

Phase 13.1 establishes the foundational architecture:
- Manifest V3 structure
- Background service worker lifecycle and state coordination
- Content script safe context extraction (zero credential scraping)
- Popup user interface with explicit user-initiated analysis
- Typed message communication protocol with request correlation
- Secure API client communicating with Unified Firewall API (`POST /api/v1/firewall/analyze`)
- Safe web application deep linking (`analysis_id` handoff)

---

## 1. Architecture Overview

```text
               Chromium Browser
                      │
       ┌──────────────┼──────────────┐
       ↓              ↓              ↓
 Content Script     Popup UI     Background
 (Safe Context)   (User Action)    Worker
       │              │              │
       └──────────────┴──────────────┘
                      ↓
              Extension API Client
                      ↓
       Nivesh Unified Firewall API (Backend)
         POST /api/v1/firewall/analyze
                      ↓
               Engine 8 Policy
```

### Separation of Responsibilities

| Component | Responsibility | Constraints |
| :--- | :--- | :--- |
| **Popup UI** | Communicates current extension state, displays active tab domain, and triggers user-initiated content scan. | Never analyzes silently. Uses `textContent` to prevent XSS. |
| **Content Script** | Extracts safe, non-sensitive page context (`pageUrl`, `pageOrigin`, `pageTitle`, user selection) upon explicit user request. | Never accesses `<input type="password">`, OTP, PIN, CVV, or hidden inputs. No keystroke listeners. |
| **Background Worker** | Coordinates message routing, runtime state transitions, request correlation, and API invocations. | No local threat scoring, claim extraction, or policy logic. Intelligence is 100% backend-driven. |
| **Extension API Client** | Communicates exclusively with the Unified Firewall API (`POST /api/v1/firewall/analyze`) and health probes (`GET /api/v1/health`). | Never calls individual engines. No secrets stored in extension bundle. |

---

## 2. Manifest & Least Privilege Permissions

The extension targets **Manifest V3** for modern Chromium-compatible browsers (Chrome, Edge, Brave):

| Permission | Purpose | Principle of Least Privilege Justification |
| :--- | :--- | :--- |
| `activeTab` | Grants temporary access to the active tab only when the user interacts with the extension. | Eliminates the need for broad `<all_urls>` host permissions. |
| `storage` | Persists user preferences and backend configuration (`backendApiUrl`, `webAppBaseUrl`). | Runtime scan state remains in memory; page content is never persisted. |
| `scripting` | Enables content script injection and context communication upon user action. | Used strictly on-demand. |

### Restricted Host Permissions
- `http://localhost:8000/*`
- `http://127.0.0.1:8000/*`

Broad wildcard permissions such as `<all_urls>`, `*://*/*`, `history`, `bookmarks`, `passwords`, `downloads`, `webRequest`, and clipboard-wide access are **strictly prohibited**.

---

## 3. Privacy Safeguards & Non-Surveillance

1. **User-Initiated Capture Model**: Analysis occurs ONLY when the user clicks **"Scan Current Content"**. The extension never passively monitors browsing activity in the background or continuously uploads page DOMs.
2. **Sensitive Element Exclusion**: Input elements with `type="password"`, `type="hidden"`, or matching patterns for `otp`, `pin`, `cvv`, `cvc`, `card number`, `ssn`, `secret`, `token`, or autocomplete codes are explicitly rejected and ignored.
3. **Selection Sanitization**: User text selection is checked against its anchor/parent DOM nodes. If selection originated within a credential field, extraction is blocked and returns `undefined`.
4. **Zero Credential Persistence**: Passwords, OTPs, PINs, bank details, and keystrokes are never intercepted, logged, or sent to backend services.

---

## 4. Typed Message Protocol & Correlation

All inter-component communication is strictly typed and correlated via `requestId` (`EXT-...`):

```text
Popup                    Background                   Content Script
  │                           │                             │
  │─── SCAN_REQUEST ─────────>│                             │
  │    (tabId, requestId)     │─── GET_PAGE_CONTEXT ───────>│
  │                           │    (requestId)              │
  │                           │<── PAGE_CONTEXT_RESPONSE ───│
  │                           │    (SafePageContext)        │
  │                           │                             │
  │                           │─── POST /firewall/analyze ─> (Unified API)
  │                           │<── Decision / Ref ────────── (Engine 8 Result)
  │<── SCAN_RESULT ───────────│
       (LastAnalysisReference)
```

Supported Messages:
- `GET_STATUS`: Queries current runtime status (`READY`, `ANALYZING`, `RESULT_AVAILABLE`, `ERROR`, `DISCONNECTED`).
- `GET_PAGE_CONTEXT`: Retrieves sanitized `SafePageContext` from active tab.
- `SCAN_REQUEST`: Dispatches firewall analysis through background worker.
- `OPEN_NIVESH_APP`: Deep-links into the Nivesh web application passing exclusively `analysis_id` (`/#protect?id={analysis_id}`).

---

## 5. Development & Testing Commands

From the `extension/` directory:

```bash
# Install dependencies
npm install

# Run unit and contract tests (Vitest + JSDOM)
npm test

# Run linter (Oxlint)
npm run lint

# Run bundle smoke test
npm run test:smoke

# Build production extension (TypeScript + Vite)
npm run build
```

The compiled extension is output to `extension/dist/`.

### Loading in Browser (Chrome / Edge / Brave):
1. Navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in upper right).
3. Click **Load unpacked** and select the `extension/dist/` directory.
4. The Nivesh Firewall extension will appear in the toolbar.
