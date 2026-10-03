# Nivesh Firewall — Frontend Foundation (Phase 12.1)

Production-grade frontend foundation for the **Nivesh Firewall** financial-content protection system.

```text
                  NIVESH FIREWALL UI
                          │
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
      AppShell       Navigation       Header
   (Responsive)     (Small/Focused) (Live Status)
          │
          ▼
   Active View (Protect / Activity / Threat Intel / Settings)
          │
          ▼
   ContentEntryCard (Inspection Shell)
          │
          ▼
   API Client Layer (apiClient)
          │
          ▼
   POST /api/v1/firewall/analyze (Phase 11 Backend)
```

---

## 1. Technology Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 8
- **Styling**: Vanilla CSS Design System with centralized CSS Custom Properties (`tokens.css`, `base.css`)
- **Icons**: Lucide React (tree-shaken SVG icons)
- **Testing**: Vitest + React Testing Library + JSDOM (`@testing-library/jest-dom`)
- **Linter**: Oxlint

---

## 2. Directory Structure

```text
frontend/
├── public/
│   └── favicon.svg             # Shield icon
├── src/
│   ├── api/
│   │   └── client.ts           # Centralized API service with timeout, error sanitization, health check, analyze
│   ├── types/
│   │   └── firewall.ts         # Types matching Phase 11 schemas exactly
│   ├── styles/
│   │   ├── tokens.css          # Design tokens: typography, colors, spacing, radius, shadows, borders, motion
│   │   ├── base.css            # Reset, typography, accessibility baseline, focus-visible, media queries
│   │   └── index.css           # Imports tokens and base
│   ├── components/
│   │   ├── common/             # Reusable UI component library
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
│   │       ├── ContentEntryCard.tsx     # Primary input card (Empty, Ready, Loading, Error, Disabled states)
│   │       └── PrivacyNotice.tsx        # Restrained trust and privacy disclosure
│   ├── views/
│   │   ├── ProtectView.tsx              # Main Firewall Landing & Protection View
│   │   ├── ActivityView.tsx             # History / Past checks (Clean Empty State)
│   │   ├── ThreatIntelligenceView.tsx   # Threat intelligence reference (Clean overview)
│   │   └── SettingsView.tsx             # Preferences & Privacy settings
│   ├── test/
│   │   ├── setup.ts                     # Vitest setup with jest-dom
│   │   ├── App.test.tsx                 # Boot, routing, navigation tests
│   │   ├── components.test.tsx          # Component rendering, status, inputs, buttons
│   │   └── api.test.ts                  # API client configuration and error handling tests
│   ├── App.tsx                          # Root application with view-based routing
│   └── main.tsx                         # Entry point
├── .env.example                         # Environment template
├── .env                                 # Local development environment
├── vite.config.ts                       # Vite & Vitest configuration
├── tsconfig.json                        # TypeScript project configuration
└── package.json                         # Package dependencies and scripts
```

---

## 3. Product Positioning & Design Guidelines

- **Product Identity**: A financial-content protection system that helps users inspect potentially dangerous interactions before taking consequential actions.
- **Tone**: Technical, calm, authoritative, transparent, non-accusatory.
- **Strict Anti-Patterns**:
  - Does NOT look like a stock terminal, brokerage app, or crypto dashboard.
  - Zero promotional or investment advice language ("Buy this", "Winning stock", etc.).
  - Zero mock intelligence, fake scam detections, or fabricated threat scores.
  - SemanticStatusBadge is strictly a presentation layer for backend Engine 8 decisions.

---

## 4. Local Development Commands

All commands can be run from the root using `--prefix frontend` or within `frontend/`:

```bash
# Install dependencies
npm --prefix frontend install

# Start local dev server (default: http://localhost:5173)
npm --prefix frontend run dev

# Run Oxlint validation
npm --prefix frontend run lint

# Run Vitest test suite
npm --prefix frontend test

# Run production build
npm --prefix frontend run build
```

---

## 5. Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Target URL for Nivesh Firewall backend API |
| `VITE_APP_NAME` | `"Nivesh Firewall"` | Brand display name |
| `VITE_APP_VERSION` | `"1.0.0"` | Frontend version identifier |
