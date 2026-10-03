# Nivesh Firewall Browser Extension (Phase 13.1 & 13.2)

The **Nivesh Firewall Browser Extension** provides real-time financial content protection and pre-action intervention directly in Chromium-compatible browsers.

- **Phase 13.1**: Extension Foundation (MV3 manifest, service worker, content script, typed messaging, least-privilege permissions, API client).
- **Phase 13.2**: Page & Content Capture (User-initiated capture, 3 capture modes, visible text extraction, selection validation, URL privacy, compact preview, strict credential exclusion).

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
            Extension API Client
               (client.ts)
                     ↓
     Unified Firewall API (Backend)
      POST /api/v1/firewall/analyze
                     ↓
         Engine 8 Policy Decision
```

### Component Responsibilities

| Component | Responsibility | Constraints |
| :--- | :--- | :--- |
| **Popup UI** | Presents 3 explicit capture triggers (`Selected Text`, `Current Page`, `Page URL`), renders compact preview before submission, and shows Engine 8 decision cards. | Strictly uses `textContent` to prevent XSS. Disables buttons for unsupported browser-internal pages (`chrome://`, etc.). |
| **Content Script** | Extracts visible page text or highlighted selection on demand; checks selection state (`CHECK_SELECTION`). | Never accesses `<input type="password">`, OTP, PIN, CVV, card numbers, or hidden inputs. No keystroke listeners. |
| **Sanitizer Layer** | Normalizes whitespace, removes control characters, and redacts accidental credit card numbers, CVVs, and PINs. | Rejects payloads exceeding maximum character limits (`CONTENT_TOO_LARGE`). |
| **URL Privacy Layer** | Separates full `analysisInputUrl` (sent to backend) from sanitized `displayUrl` (stripped of tracking codes and sensitive query tokens). | Flags unsupported internal schemes (`chrome:`, `edge:`, `about:`, `devtools:`). |
| **Background Worker** | Coordinates request correlation (`capture_id` → `request_id` → `analysis_id`), manages ephemeral state, and dispatches to API client. | Zero local threat scoring or policy intelligence. |
| **Extension API Client** | Dispatches structured payloads to `POST /api/v1/firewall/analyze` and checks health via `GET /api/v1/health`. | Never calls individual backend engines directly. No secrets stored in bundle. |

---

## 2. Supported Capture Modes (Phase 13.2)

1. **User-Selected Text (`SELECTED_TEXT`)**:
   - Captures only the text highlighted by the user on the active page.
   - If no text is selected, popup displays a helpful prompt (`"Select text on the page first."`) and returns `NO_SELECTION`.
   - Rejects selections originating inside sensitive credential fields.
   - Enforces a 5,000-character upper limit.
2. **Current Page (`CURRENT_PAGE`)**:
   - Walks the DOM starting from visible content, extracting headers, paragraphs, and list items.
   - Excludes `<script>`, `<style>`, `<iframe>`, `<svg>`, `<nav>`, `<footer>`, and buttons.
   - Skips hidden elements (`display: none`, `visibility: hidden`, `hidden`, `aria-hidden="true"`).
   - Enforces a 15,000-character upper limit.
3. **Current URL (`URL`)**:
   - Validates that the active page URL uses `http:` or `https:`.
   - Sends target URL to Unified Firewall API for Engine 4 reputation and threat inspection.
   - Masks sensitive query parameters (`token`, `auth`, `session_id`, `key`) in popup display and telemetry logs.

---

## 3. Privacy Safeguards & Non-Surveillance

- **User-Initiated Capture Model**: Content is captured ONLY when the user clicks an analysis trigger. Continuous background DOM scraping, page recording, or automated uploads are strictly prohibited.
- **Sensitive Field Neutralization**: Input fields with `type="password"`, `type="hidden"`, or matching patterns for `otp`, `pin`, `cvv`, `cvc`, `card number`, `ssn`, `secret`, `token` are completely excluded from extraction.
- **Accidental Pattern Redaction**: Text containing full credit card numbers, CVVs, or ATM PINs is automatically masked (`[CARD_NUMBER_REDACTED]`, `[CVV_REDACTED]`, `[PIN_REDACTED]`).
- **Zero Credential Persistence**: No cookies, session storage, local storage, authorization headers, or keystroke listeners are accessed or stored.

---

## 4. Message Protocol Contracts

Extended in Phase 13.2:

```text
Popup                       Background                      Content Script
  │                              │                                │
  │─── CHECK_SELECTION ─────────>│─── CHECK_SELECTION ───────────>│
  │<── hasSelection (true/false)─│<── hasSelection (true/false)───│
  │                              │                                │
  │─── CAPTURE_REQUEST ─────────>│─── DO_CAPTURE ────────────────>│
  │    (sourceType, tabId)       │    (sourceType, captureId)     │
  │                              │<── CAPTURE_RESPONSE ───────────│
  │<── CAPTURE_RESPONSE ─────────│    (CapturePayload)            │
  │    (Render Preview)          │                                │
  │                              │                                │
  │─── SCAN_REQUEST ────────────>│─── POST /firewall/analyze ────> (Unified API)
  │    (CapturePayload)          │<── Decision / Ref ───────────── (Engine 8)
  │<── ANALYSIS_COMPLETED ───────│
```

---

## 5. Development & Testing Commands

From the `extension/` directory:

```bash
# Run all unit, privacy, and capture tests (Vitest + JSDOM)
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
