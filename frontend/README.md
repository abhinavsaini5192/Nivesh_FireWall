# Nivesh Firewall — Frontend Application (Phase 12.3)

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
     │        ├─► ProtectionBanner & InterventionHeader (ALLOW | INFORM | WARN | PAUSE | BLOCK)
     │        ├─► HighImpactActionAlert (Engine 3: Transfer, Credentials, External Software)
     │        ├─► ProtectionSummaryCard (Action, Identity, Evidence, Threat, Behaviour)
     │        ├─► WhyIntervenedSection (Primary Reason & Canonical Reason Codes with Section Deep Links)
     │        ├─► RecommendedNextStepCard (Protective UX Instructions & Contextual Actions)
     │        ├─► OverrideConfirmationModal (Explicit 2-Step Non-Shaming Policy Override)
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
6. **Intervention Mapping**: Maps authoritative `policy` response into `InterventionModel` via pure translation.
7. **Result View**: Renders `AnalysisResultView` with intervention headers, banners, summary cards, and deep intelligence links.
8. **Audit & Activity**: Results are stored in session history, browsable in `ActivityView` and deep-linkable via hash (`#protect?id=ORCH-...`).

> **Core Architectural Rule**:
> The frontend presents the Engine 8 policy decision and does not perform independent policy evaluation.

---

## 2. Intervention & Protection Experience (Phase 12.3)

### 2.1 Intervention State Model
The frontend maps the backend's canonical Engine 8 policy decision to a presentation model:

```text
Backend Engine 8 Decision
           ↓
┌──────────────────────────────────────┐
│ ALLOW  │ INFORM │ WARN │ PAUSE │ BLOCK│
└──────────────────────────────────────┘
           ↓
   Intervention Model (Pure Presentation)
           ↓
┌──────────────────────────────────────┐
│ • Protection Banner & Header         │
│ • High-Impact Action Surfacing       │
│ • 5-Dimension Protection Summary     │
│ • "Why Did Nivesh Intervene?" Codes  │
│ • Recommended Next Step Actions      │
│ • Explicit User Override Dialog      │
└──────────────────────────────────────┘
```

### 2.2 Decision Rendering Semantics
- **`ALLOW`**: Calm confirmation ("Action Permitted — Verified Neutral"). No claims of "100% safe" or "guaranteed legitimate".
- **`INFORM`**: Contextual awareness ("Informational Advisory"). Discloses predictions or general context without alarmism.
- **`WARN`**: Visible caution state ("Caution Recommended — Verified Signal Alert"). Highlights unverified claims or unestablished identity; never labels entities as "scammers".
- **`PAUSE`**: High-visibility pause state ("Action Paused — Verification Required"). Highlights active cooldown requirements and explicit confirmation checks.
- **`BLOCK`**: Strong protection state ("Action Blocked — Threat Prevented"). Authoritative intervention without sensational accusations ("you were definitely scammed").

### 2.3 Reason & Intelligence Connection
- Primary reasons and canonical reason codes (`UNVERIFIED_AUTHORITY_CLAIM`, `URGENT_FINANCIAL_EXTRACTION`, etc.) are rendered directly from Engine 8.
- Each reason includes actionable deep links (`[ See Identity Resolution ]`, `[ See Claim Evidence ]`, etc.) that smoothly scroll to and expand the corresponding Engine panel.

### 2.4 Protective Next Steps vs. Financial Advice
The interface strictly limits recommended next steps to **protective UX instructions** (e.g., verifying identity out-of-band, rejecting software installations). It **never provides financial or investment advice**, buy/sell recommendations, or market predictions.

### 2.5 Safe Error Handling & Policy Integrity
- **Rendering Fallbacks**: If parsing or rendering encounters an unexpected state, the UI falls back to a safe error card preserving the canonical decision.
- **No Downgrades**: A `BLOCK`, `PAUSE`, or `WARN` state is **never downgraded to `ALLOW`** due to a rendering or parsing error.

### 2.6 User Override Model
- Only exposed when backend policy indicates an overridable condition.
- Uses an accessible two-step confirmation dialog with non-shaming, neutral language explaining what is being overridden.
- Preserves the original policy state on cancellation.

---

## 3. Directory Structure

```text
frontend/
├── src/
│   ├── api/
│   │   └── client.ts                     # Unified Firewall API client
│   ├── types/
│   │   ├── firewall.ts                   # Core schemas matching backend contracts
│   │   └── intervention.ts               # Intervention presentation model & mapping
│   ├── components/
│   │   ├── common/                       # Reusable UI component library (Accordion, Modal, etc.)
│   │   ├── intervention/                 # Dedicated Phase 12.3 intervention components
│   │   │   ├── ProtectionBanner.tsx      # Top banner for decision states
│   │   │   ├── InterventionHeader.tsx    # Hero decision header & status
│   │   │   ├── HighImpactActionAlert.tsx # Engine 3 high-impact action warning
│   │   │   ├── ProtectionSummaryCard.tsx # 5-dimension summary card with deep links
│   │   │   ├── WhyIntervenedSection.tsx  # Reason codes with link to engine panels
│   │   │   ├── RecommendedNextStepCard.tsx # Protective UX instructions & actions
│   │   │   ├── OverrideConfirmationModal.tsx # Accessible 2-step override dialog
│   │   │   └── index.ts                  # Barrel export
│   │   ├── firewall/
│   │   │   ├── AnalysisResultView.tsx    # Canonical Phase 12.2 & 12.3 Presentation
│   │   │   ├── ContentEntryCard.tsx      # Primary input card
│   │   │   └── PrivacyNotice.tsx         # Trust and privacy disclosure
│   │   └── shell/                        # AppShell, Header, Navigation
│   └── test/
│       ├── interventionExperience.test.tsx # 20 Tests covering all Phase 12.3 requirements
│       ├── analysisWorkflow.test.tsx       # 22 Tests covering Phase 12.2 workflow
│       ├── components.test.tsx             # 13 Reusable component tests
│       ├── App.test.tsx                    # 6 App shell & navigation tests
│       └── api.test.ts                     # 6 API client tests
```

---

## 4. Testing & Quality Standards

Run all frontend checks:

```bash
# Lint check (Oxlint)
npm --prefix frontend run lint

# Vitest Suite (67/67 passed)
npm --prefix frontend test

# Production Build
npm --prefix frontend run build
```us, inputs, buttons
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
