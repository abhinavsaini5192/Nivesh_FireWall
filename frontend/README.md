# Nivesh Firewall — Frontend Application (Phase 12.2)

Production-grade user interface for the **Nivesh Firewall** financial-content protection system.

```text
                  NIVESH FIREWALL FRONTEND
                             │
     ┌───────────────────────┼───────────────────────┐
     ↓                       ↓                       ↓
  AppShell               Navigation               Header
(Responsive)           (Small/Focused)        (Live Status)
     │
     ▼
  Active View (Protect / Activity / Threat Intel / Settings)
     │
     ├─► [ProtectView] Content Input (Text/URL) ──► Validation
     │        │
     │        ▼
     │   POST /api/v1/firewall/analyze (Unified Firewall API)
     │        │
     │        ▼
     │   [AnalysisResultView]
     │        ├─► Engine 8 Canonical Safety Decision (ALLOW | INFORM | WARN | PAUSE | BLOCK)
     │        ├─► Explanation & Required User Confirmation Alert
     │        ├─► Primary Reason & Canonical Reason Codes
     │        └─► 8 Intelligence Breakdown Panels (E2, E3, E4/E5, E9, E6, E7, E10, Provenance)
     │
     └─► [ActivityView] Session History & Inspection Audit
```

---

## 1. Core Architecture & Workflow

### 1.1 Ingestion & Analysis Workflow
1. **User Input**: User enters financial text or URL into `ContentEntryCard` on `ProtectView`.
2. **Client-side Validation**: Verifies presence of content, supported channel, character boundaries (<100,000 characters).
3. **API Dispatch**: Dispatches `POST /api/v1/firewall/analyze` via canonical `apiClient`.
4. **Authoritative Response**: Consumes canonical `FirewallAnalysisResponse`. Frontend performs **zero threat calculations or mock detections**.
5. **State Transition**: Transitions state model from `SUBMITTING` → `ANALYZING` → `SUCCESS` (or `ERROR` / `PARTIAL_RESULT`).
6. **Result View**: Renders `AnalysisResultView` with Engine 8 policy outcome and multi-engine intelligence panels.
7. **Audit & Activity**: Results are stored in the session history, browsable in `ActivityView` and deep-linkable via hash (`#protect?id=ORCH-...`).

### 1.2 Frontend Analysis State Model
```text
      IDLE
       │
  (User types)
       ▼
   VALIDATING ──(Invalid)──► ERROR (Input Level)
       │
    (Valid)
       ▼
   SUBMITTING
       │
       ▼
   ANALYZING
       │
   ┌───┴──────────────┬────────────────┐
   │                  │                │
(Success)          (Partial)        (Failure)
   ▼                  ▼                ▼
SUCCESS        PARTIAL_RESULT        ERROR (Safe UI)
```

---

## 2. API Integration & Backend Contract

The frontend connects directly to the **Phase 11 Unified Firewall API** (`/api/v1/firewall/...`) rather than invoking individual engines directly.

| Endpoint | Method | Purpose |
| :--- | :--- | :--- |
| `/api/v1/firewall/analyze` | `POST` | Primary analysis endpoint executing full multi-engine pipeline |
| `/api/v1/firewall/analysis/{id}` | `GET` | Retrieves existing analysis by ID without re-executing pipeline |
| `/api/v1/firewall/health` | `GET` | Health probe confirming engine pipeline readiness |

---

## 3. Response Rendering Architecture

The frontend adheres strictly to the backend's authoritative output:

### 3.1 Policy Outcome (Sole Authority: Engine 8)
- `ALLOW`: Action permitted — verified neutral financial content.
- `INFORM`: Informational advisory — awareness context.
- `WARN`: Caution recommended — speculative or unverified claims.
- `PAUSE`: Action paused — requires explicit confirmation and verification cooldown.
- `BLOCK`: Action blocked — high-impact threat prevented.

### 3.2 Intelligence Summary Panels (Accordions)
1. **Extracted Financial Claims (Engine 2 & 5)**: Atomic assertions with topic, predicate, modality, and evidence verification status (`SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`).
2. **Requested User Actions (Engine 3)**: Action type (`TRANSFER_MONEY`, `DOWNLOAD`, `CREDENTIAL_ACCESS`, etc.), target, reversibility, and urgency indicators.
3. **Evidence Verification (Engine 5 & 4)**: Verifications against regulatory records and official filings with distinct counts.
4. **Entity Identity Resolution (Engine 9)**: Entity status (`ESTABLISHED`, `NOT_ESTABLISHED`, `IDENTITY_MISMATCH`), confidence, claimed entities, and official registry lookup findings.
5. **Threat & Attack-Path Analysis (Engine 6)**: Multi-signal progression stages (e.g. `CHANNEL_MIGRATION → FINANCIAL_EXTRACTION`), threat families, and high-impact action count.
6. **Scam Fingerprint Intelligence (Engine 7)**: Structural pattern matching (`EXACT_MATCH`, `SEMANTIC_VARIANT`, `STRUCTURAL_EQUIVALENCE`, `NO_MATCH`) and collective observation sightings.
7. **Behavioural Signal Intelligence (Engine 10)**: Observed interaction dynamics (time pressure, off-platform migration, rapid escalation) without armchair psychological labeling.
8. **Provenance & Pipeline Audit**: Pipeline status, execution duration in milliseconds, channel, and engine execution lineage.

---

## 4. Privacy & UI Security Safeguards

- **Forbidden Fields**: The UI strictly forbids displaying or storing sensitive user credentials (`password`, `otp`, `pin`, `cvv`, `card_number`, `bank_account`).
- **No Raw Logging**: Console logging of full private backend responses is avoided.
- **XSS Prevention**: Zero usage of `dangerouslySetInnerHTML`. User input and backend strings are escaped through React's virtual DOM.
- **Duplicate Protection**: Analyze button is disabled during active submissions to prevent duplicate execution.
- **Safe Error Surfaces**: Internal stack traces or database errors are never displayed to the user. Sanitized client error messages are surfaced with actionable error codes.

---

## 5. Directory Structure

```text
frontend/
├── public/
│   └── favicon.svg             # Shield icon
├── src/
│   ├── api/
│   │   └── client.ts           # Unified Firewall API client with timeout, error sanitization, health check, analyze, getAnalysis
│   ├── types/
│   │   └── firewall.ts         # Types matching Phase 11 & 12 schemas exactly
│   ├── styles/
│   │   ├── tokens.css          # Design tokens: typography, colors, spacing, radius, shadows, borders, motion
│   │   ├── base.css            # Reset, typography, accessibility baseline, focus-visible, media queries
│   │   └── index.css           # Imports tokens and base
│   ├── components/
│   │   ├── common/             # Reusable UI component library
│   │   │   ├── Accordion.tsx        # Accessible keyboard-navigable accordion panels
│   │   │   ├── Button.tsx           # Button (primary, secondary, outline, ghost, danger)
│   │   │   ├── IconButton.tsx       # Accessible icon button
│   │   │   ├── Input.tsx            # Accessible text input with label, error, helper
│   │   │   ├── Textarea.tsx         # Accessible textarea with character count
│   │   │   ├── Select.tsx           # Clean select dropdown
│   │   │   ├── Card.tsx             # Card (Header, Title, Description, Content, Footer)
│   │   │   ├── Panel.tsx            # Technical panel with accent border and title
│   │   │   ├── Badge.tsx            # Categorical & status badges
│   │   │   ├── StatusIndicator.tsx  # Dot indicator (active, connecting, unavailable, error, neutral)
│   │   │   ├── Alert.tsx            # Alert banner (info, warning, error, success)
│   │   │   ├── EmptyState.tsx       # Intentional empty state (icon, title, desc, action)
│   │   │   ├── LoadingState.tsx     # Loading spinner and multi-step pipeline skeleton
│   │   │   ├── ErrorState.tsx       # Structured error display with code, safe message, retry
│   │   │   ├── Modal.tsx            # Accessible dialog with ESC handling and backdrop
│   │   │   ├── Tooltip.tsx          # Accessible inline tooltip
│   │   │   ├── Divider.tsx          # Clean horizontal/vertical divider
│   │   │   ├── SectionHeader.tsx    # Title, subtitle, badge
│   │   │   ├── MetadataRow.tsx      # Label-value pair with copy affordance
│   │   │   └── index.ts             # Barrel export
│   │   ├── status/
│   │   │   ├── SemanticStatusBadge.tsx  # ALLOW / INFORM / WARN / PAUSE / BLOCK presentation
│   │   │   └── ProtectionStatus.tsx     # active / connecting / unavailable / error system status
│   │   ├── shell/
│   │   │   ├── Header.tsx               # Brand, ProtectionStatus, Mobile toggle
│   │   │   ├── Navigation.tsx           # Protect, Activity, Threat Intelligence, Settings
│   │   │   └── AppShell.tsx             # Responsive layout container with persistent/collapsible nav
│   │   └── firewall/
│   │       ├── AnalysisResultView.tsx   # Canonical Phase 12.2 Result Presentation with 8 Intelligence Panels
│   │       ├── ContentEntryCard.tsx     # Primary input card (Empty, Ready, Loading, Error, Disabled states)
│   │       └── PrivacyNotice.tsx        # Restrained trust and privacy disclosure
│   ├── views/
│   │   ├── ProtectView.tsx              # Main Firewall Landing, Analysis Input & Result View
│   │   ├── ActivityView.tsx             # History of inspected sessions and result inspection
│   │   ├── ThreatIntelligenceView.tsx   # Threat intelligence reference
│   │   └── SettingsView.tsx             # Preferences & Privacy settings
│   ├── test/
│   │   ├── setup.ts                     # Vitest setup with jest-dom
│   │   ├── analysisWorkflow.test.tsx    # 22 Tests covering all Phase 12.2 scenarios
│   │   ├── App.test.tsx                 # Boot, routing, navigation tests
│   │   ├── components.test.tsx          # Component rendering, status, inputs, buttons
│   │   └── api.test.ts                  # API client configuration and error handling tests
│   ├── App.tsx                          # Root application with view-based routing and analysis lifecycle
│   └── main.tsx                         # Entry point
├── .env.example                         # Environment template
├── .env                                 # Local development environment
├── vite.config.ts                       # Vite & Vitest configuration
├── tsconfig.json                        # TypeScript project configuration
└── package.json                         # Package dependencies and scripts
```

---

## 6. Testing & Quality Standards

Run all frontend checks:

```bash
# Lint check (Oxlint)
npm --prefix frontend run lint

# Vitest Suite (47/47 passed)
npm --prefix frontend test

# Production Build
npm --prefix frontend run build
```
