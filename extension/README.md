# Nivesh Firewall Browser Extension (Phase 13.1, 13.2, 13.3 & 13.4)

The **Nivesh Firewall Browser Extension** provides real-time financial content protection, pre-action intervention, and in-page protection directly in Chromium-compatible browsers.

- **Phase 13.1**: Extension Foundation (MV3 manifest, service worker, content script, typed messaging, least-privilege permissions, API client).
- **Phase 13.2**: Page & Content Capture (User-initiated capture, 3 capture modes, visible text extraction, selection validation, URL privacy, compact preview, strict credential exclusion).
- **Phase 13.3**: Nivesh Analysis Bridge (Unified Firewall API integration, request correlation, tab-scoped session isolation, multi-tab isolation, bounded retry, Engine 8 intelligence preservation, safe fallback, web-app deep link handoff).
- **Phase 13.4**: In-Page Protection & Interaction (Policy-to-protection mapping, Shadow DOM isolation, targeted interaction protection, safe navigation interception, explicit PAUSE override confirmation, BLOCK preservation, Safe Uncertainty Rule, active tab synchronization).

---

## 1. Architecture Overview

```text
Browser
  ↓
Content Script
  ↓
Protection Layer
  ↓
Background Worker
  ↓
Analysis Bridge
  ↓
Nivesh Unified API
  ↓
Engine 8 Policy
  ↓
Protection Decision
  ↓
┌──────────────┼──────────────┐
▼              ▼              ▼
Extension       Page UI       Web App
 Popup        Intervention    Details
```

### Component Responsibilities

| Component | Responsibility | Constraints |
| :--- | :--- | :--- |
| **Popup UI** | Presents 3 explicit capture triggers (`Selected Text`, `Current Page`, `Page URL`), renders compact preview, and displays synchronized Engine 8 decision summary with deep-link handoff. | Strictly uses `textContent` to prevent XSS. Synchronizes dynamically with the active tab. |
| **Content Script** | Extracts visible page text on demand, hosts the In-Page Protection Layer, and mounts Shadow DOM overlays. | Never accesses password/OTP/PIN/CVV/card fields. Zero continuous DOM monitoring or keystroke logging. |
| **Protection Layer** | Renders isolated Shadow DOM banners/modals, evaluates conservative target action matching, and intercepts targeted actions. | Zero frontend risk scoring. Follows Safe Uncertainty Rule: never blocks if target match is ambiguous. |
| **Sanitizer Layer** | Normalizes whitespace, removes control characters, and redacts accidental credit card numbers, CVVs, and PINs. | Rejects payloads exceeding maximum character limits (`CONTENT_TOO_LARGE`). |
| **URL Privacy Layer** | Separates full `analysisInputUrl` from sanitized `displayUrl` (stripped of tracking codes and sensitive tokens). | Flags unsupported internal schemes (`chrome:`, `edge:`, `about:`, `devtools:`). |
| **Background Worker** | Coordinates request correlation (`capture_id` → `request_id` → `analysis_id`), manages isolated tab state, and dispatches intervention messages to content scripts. | Zero local threat scoring or policy intelligence. |
| **Analysis Bridge** | Canonical typed bridge submitting to `POST /api/v1/firewall/analyze`. Handles request validation, bounded retry, safe fallback, and safe telemetry. | Zero intelligence logic. Preserves Engine 8 decision and all engine findings unchanged. |

---

## 2. Policy-to-Protection Mapping (Phase 13.4)

Frontend presentation maps directly and faithfully from the backend Engine 8 decision:

```text
ALLOW   → No in-page intervention overlay; subtle "No intervention required" status in popup.
INFORM  → Lightweight, non-blocking informational banner at top of viewport.
WARN    → Visible non-blocking warning banner with structured reason breakdown.
PAUSE   → High-visibility centered modal overlay; requires explicit confirmation before proceeding.
BLOCK   → Strong blocking experience; targeted interaction prevented according to policy.
```

### Protection Overlay Specifications

- **Shadow DOM Isolation**: Injected into `#nivesh-firewall-root` with an open `ShadowRoot` containing all CSS styles, completely isolating the intervention UI from host-page styles and preventing host scripts from breaking layout.
- **Trusted UI Identity**: Clearly branded with `🛡️ NIVESH FIREWALL` badge. Treats all page text and backend strings as untrusted text using `textContent` only (zero `innerHTML` injection).
- **Structured Reason Breakdown**: Displays Engine 8 findings (Claim verification, Identity status, Action classification, Evidence sufficiency, Threat pattern, and Behavioural progression).
- **Web App Analysis Handoff**: Dedicated `"View Full Analysis ↗"` action opens `http://localhost:5173/#protect?id={analysis_id}`.
- **Accessibility**: ARIA roles (`role="dialog"`, `role="status"`), `aria-modal="true"`, accessible headings, and keyboard navigation (Escape key dismissal where permitted).

---

## 3. Targeted Interaction Protection & Navigation Handling

The protection layer strictly distinguishes between whole-page context and specific analyzed targets:

1. **Target Action Matching (`targetMatcher.ts`)**:
   - Matches backend action targets (e.g. payment link, APK download, external app navigation) against DOM elements using exact URL/origin matching.
   - **Safe Uncertainty Rule**: If multiple matching elements exist or the target is ambiguous, the system resolves `matchConfidence: 'AMBIGUOUS'` and `matchedElement: null`. **No arbitrary elements or buttons are ever blocked.**

2. **Targeted Navigation Interception (`navigationInterceptor.ts`)**:
   - Installs a capture-phase click listener strictly for the matched element.
   - Unrelated page navigation and normal links remain **100% unaffected**.
   - If a user clicks a targeted `PAUSE` element, the modal overlay re-surfaces requiring explicit confirmation.
   - If a user clicks a targeted `BLOCK` element, navigation is intercepted and prevented (`preventDefault()` and `stopPropagation()`).

3. **Override Flow Semantics**:
   - **PAUSE**: Displays an explicit confirmation dialog: *"Continue with this action? Nivesh previously paused this action because additional verification was required."*
   - Cancelling the override preserves the original `PAUSE` policy state without side-effects.
   - **BLOCK**: **Zero local bypass.** A blocked interaction cannot be silently overridden or cleared via UI dismissal.

---

## 4. Privacy Boundaries & Scope Guarantees

- **Zero Continuous Surveillance**: No background DOM polling, no `MutationObserver` on unanalyzed pages, no browser history tracking.
- **Zero Sensitive Form Interception**: Password fields, OTPs, PINs, CVVs, card numbers, and bank account inputs are strictly excluded from capture and never overlaid.
- **Zero Keystroke Monitoring**: No `keydown`/`keypress` listeners installed on form inputs.
- **Multi-Tab Isolation**: Protection state is strictly isolated per tab in background runtime memory. Tab A showing `PAUSE` never leaks to Tab B showing `ALLOW`.
- **Active Tab Synchronization**: Extension popup automatically queries and displays the analysis and protection state corresponding to the active browser tab.
- **Event & Memory Cleanup**: Calling `cleanup()` removes all Shadow DOM hosts, detaches all navigation listeners, and clears state without memory leaks.

---

## 5. Development & Testing Commands

From the `extension/` directory:

```bash
# Run all unit, privacy, capture, bridge, and in-page protection tests (14 test files, 120 tests)
npm test

# Run linter (Oxlint - 0 errors, 0 warnings)
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
