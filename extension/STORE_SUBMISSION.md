# Nivesh Firewall — Chrome Web Store Submission & Packaging Guide

This document contains the verified metadata, single-purpose declaration, reviewer permission justifications, privacy disclosures, installation UX specifications, and asset checklists for submitting **Nivesh Firewall** to the Chrome Web Store.

---

## 1. Executive Status & Deployment Reality

```text
Chrome Web Store package:
Technically ready

Public API dependency:
NOT YET DEPLOYED

Public user installation:
NOT YET END-TO-END VERIFIED

Store Publication Status:
NOT PUBLISHED (Preparation & Review Materials Only)
```

> [!IMPORTANT]
> The Nivesh Firewall extension package (`nivesh-firewall-v1.0.0.zip`) is technically prepared and audited for Chrome Web Store compliance. However, public user installation and end-to-end verification cannot be completed until the public production API endpoint (`https://api.nivesh.ai/*`) is deployed and operational. The extension must NOT be claimed as "published" or "live for public users" until Chrome Web Store review is approved and the production API is online.

---

## 2. Store Listing Metadata

| Field | Value | Notes |
| :--- | :--- | :--- |
| **Extension Name** | `Nivesh Firewall` | Official product title |
| **Version** | `1.0.0` | Synchronized with `manifest.json` and `package.json` |
| **Manifest Version** | `3` | Full MV3 compliance |
| **Category** | `Privacy & Security` (Secondary: `Productivity`) | Chrome Web Store categories |
| **Short Description** | `Inspect financial content and verify claims before consequential actions with real-time pre-action safety checks.` | 114 chars (under 132 char limit) |
| **Primary Language** | English | |
| **Support / Website URL** | `https://nivesh.ai` | Configurable deployment variable |
| **Web Store Listing URL** | `https://chromewebstore.google.com/detail/<extension-id>` | Configurable post-submission URL |

---

## 3. Single-Purpose Declaration

The Chrome Web Store Developer Program Policies require an explicit, narrow single-purpose declaration:

> **Single Purpose**:
> **Helping users inspect financial content and understand potential safety concerns before consequential actions.**

### Behavioral Boundaries
- **User-Initiated Activation**: The extension operates strictly upon explicit user interaction (clicking the toolbar action or clicking "Analyze This Page" in the popup).
- **No Background Surveillance**: The extension does NOT passively monitor, record, log, or transmit background browsing activity.
- **No Autonomous Trading**: The extension does NOT execute trades, transfer funds, or interact with banking accounts.

---

## 4. Detailed Store Description

```markdown
Nivesh Firewall provides pre-action verification and intervention for financial content, claims, and investment solicitations directly within your browser.

Before you make a financial commitment, wire funds, join an unverified investment group, or act on high-pressure advisory claims, Nivesh Firewall helps you evaluate the content against authoritative financial signals and scam patterns.

### Key Capabilities

• One-Click Page Analysis: Inspect visible financial claims, return promises, and advisory content on any active webpage with a single click.
• Selected Text Verification: Highlight specific claims, WhatsApp/Telegram forward texts, or advisory messages to inspect them in isolation.
• Pre-Action Interventions: Receive non-invasive warnings, pauses, or block interventions when high-risk patterns or unverified regulatory claims are detected.
• Deep-Link Audit: Open the full Nivesh Web Application with a single click to review detailed claims breakdown, regulatory provenance, and threat intelligence.
• Privacy-Preserving Architecture: Operates strictly on-demand. Zero continuous background tracking, zero keystroke logging, and zero credential harvesting.

### Regulatory & Fiduciary Notice

Nivesh Firewall is a technical security tool designed to detect manipulation patterns and verify publicly verifiable regulatory registrations. 

Nivesh Firewall:
- is NOT a registered investment advisor (RIA) or broker-dealer
- does NOT offer investment advice, buy/sell recommendations, or portfolio management
- does NOT execute financial transactions
- does NOT guarantee that any opportunity is risk-free or fraudulent
- does NOT guarantee scam or fraud prevention
```

---

## 5. Chrome Web Store Permission Justifications

Reviewers require an explicit, granular explanation for every requested permission demonstrating adherence to the **Principle of Least Privilege**:

### `activeTab`
> **Reviewer Justification**: Granted only when the user explicitly interacts with the Nivesh Firewall extension (clicking the extension icon in the toolbar or triggering "Analyze This Page"). It provides temporary access to the active tab to inspect the current webpage URL and visible text for financial claims without requiring broad, persistent access to the user's browsing history or all open tabs.

### `storage`
> **Reviewer Justification**: Used exclusively to store local user preferences (such as auto-scan settings and UI theme) and transient, tab-scoped analysis identifiers (`analysisId`, last evaluation status). It ensures UI continuity when the Manifest V3 service worker suspends between actions. It never stores sensitive credentials, passwords, or personal banking data.

### `scripting`
> **Reviewer Justification**: Injects an ephemeral, isolated Shadow DOM intervention overlay (`SHOW_INTERVENTION`) on the active tab only when an analysis returns a `WARN`, `PAUSE`, or `BLOCK` policy decision, alerting the user to critical financial risks before they proceed.

### Host Permissions (`https://api.nivesh.ai/*`)
> **Reviewer Justification**: Required exclusively to transmit user-initiated analysis requests to the secure Nivesh Unified Firewall API (`POST /api/v1/firewall/analyze`) and receive real-time threat evaluations and regulatory provenance data over encrypted HTTPS. No communication is permitted with any other domain or origin.

### Strictly Forbidden Permissions Audit
The extension explicitly avoids all invasive permissions:
- `*://*/*` or `<all_urls>` (No broad web access)
- `tabs` (No general tab monitoring or history tracking)
- `history` (No access to browsing history)
- `cookies` (No session or cookie extraction)
- `passwords` / `credentials` (Zero credential access)
- `clipboardRead` / `clipboardWrite` (No clipboard access)
- `webRequest` / `webRequestBlocking` (No traffic interception)
- `downloads` (No file download control)
- `geolocation` (No location tracking)
- `management` (No extension management)

---

## 6. Privacy & Data Use Disclosure

### Data Types Accessed & Transmitted
1. **User-Selected / Page Content**: Visible text or user-highlighted text from the active tab upon explicit user invocation.
2. **Page URL & Title**: The URL of the inspected page to evaluate domain registration age and known scam fingerprints.
3. **Transmission Channel**: Encrypted HTTPS directly to `https://api.nivesh.ai/*`.

### Zero-Collection Guarantee (Excluded Data Types)
The extension includes active content filtering and sanitization:
- **No Passwords**: `<input type="password">` fields and credentials are never captured.
- **No Payment Details**: Credit card numbers, CVVs, expiration dates, PINs, and bank account numbers are scrubbed prior to transmission.
- **No OTPs / 2FA**: One-time passwords and SMS security codes are strictly filtered out.
- **No Hidden Inputs**: `<input type="hidden">` values are excluded.
- **No Keystroke Surveillance**: No global keyboard event listeners exist.
- **No Continuous Surveillance**: Pages are never scanned autonomously in the background; analysis requires explicit user invocation.

### Local Storage Policy
- Local extension storage (`chrome.storage.local`) holds only client configuration flags and short-lived request tokens.
- No personally identifiable information (PII) is persisted locally.

---

## 7. Production API Dependency & Environment Status

The production package references the official production API origin:
```text
https://api.nivesh.ai/*
```

### Current Operational Status
- **Backend Deployment**: The production backend and Unified Firewall API have not yet been deployed to the public domain `api.nivesh.ai`.
- **Public End-to-End Verification**: Pending public backend deployment.
- **Review Pre-Condition**: For Chrome Web Store public submission, either the production backend must be live on `https://api.nivesh.ai`, or reviewer test credentials and mock endpoints must be documented in the submission notes.

---

## 8. Installation UX Specification

### Intended Normal-User Flow
```text
Nivesh Landing Page
        ↓
Click "Add to Chrome"
        ↓
Chrome Web Store Listing Page
        ↓
Click "Add to Chrome" button
        ↓
Chrome Native Permission Confirmation Dialog
        ↓
Extension Installed & Action Pinned
        ↓
User clicks Nivesh icon → Opens Popup Ready State
```

### Normal-User Guardrails
- **No Developer Mode Instructions**: The landing page and public documentation must **NEVER** instruct end users to open `chrome://extensions`, enable Developer Mode, or "Load unpacked".
- **Dynamic Store Link**: The "Add to Chrome" button on the web landing page uses a configurable environment variable (`VITE_CHROME_WEBSTORE_URL`). During pre-launch, it links to a clear waitlist or readiness modal rather than a broken or fabricated link.

---

## 9. Store Screenshot Preparation Checklist

Chrome Web Store requires high-resolution screenshots showing the actual extension in use. The following 5 scenes represent real, implemented UI states:

| Scene # | Screenshot Title | UI State Captured | Visual Composition & Details | Resolution |
| :---: | :--- | :--- | :--- | :--- |
| **1** | **Popup Idle / Ready State** | Extension toolbar popup opened on active webpage | Displays domain context (`example.com`), active protection status badge (`PROTECTED`), clear "Analyze This Page" call-to-action button, and recent audit history count. | `1280 x 800 px` |
| **2** | **Analyze This Page State** | Active analysis in progress | Progress indicator displaying "Extracting page content...", real-time signal detection progress, and cancel option. | `1280 x 800 px` |
| **3** | **Example Analysis Result** | Policy decision and findings summary | Clear visual verdict card (e.g., `WARN` or `ALLOW`), risk score gauge, detected claims breakdown (e.g., unverified 50% guaranteed monthly returns), and SEBI verification status. | `1280 x 800 px` |
| **4** | **Full Firewall Handoff** | Transition to deep audit | User clicking "Open Full Audit in Nivesh", showing clean deep-link handoff to the web dashboard (`/firewall/audit/<id>`) with complete forensic evidence breakdown. | `1280 x 800 px` |
| **5** | **In-Page Intervention Overlay** | Shadow DOM warning banner on risky content | Non-invasive top banner overlay (`NIVESH FIREWALL WARNING: Unregistered Advisory Claims Detected`) with "Proceed with Caution" and "Dismiss" actions. | `1280 x 800 px` |

### Asset Technical Requirements
- **Dimensions**: `1280 x 800 px` (preferred) or `640 x 400 px`.
- **Format**: PNG or 24-bit JPEG with no alpha.
- **Authenticity**: Must depict real extension UI rendered from the codebase. No fabricated statistics, fake regulatory seals, or misleading security guarantees.

---

## 10. Store Review Risk Audit

A comprehensive review against Chrome Web Store Developer Program rejection reasons:

| Risk Factor | Review Concern | Nivesh Implementation & Mitigation |
| :--- | :--- | :--- |
| **1. Misleading Description** | Promising guaranteed safety or fraud immunity | All store copy clearly states Nivesh is a technical verification tool and does not guarantee scam detection. |
| **2. Unnecessary Permissions** | Requesting `<all_urls>` or `tabs` | Permissions strictly restricted to `activeTab`, `storage`, and `scripting`. |
| **3. Remote Code Execution** | Violates Manifest V3 CSP | Zero `eval()`, zero `new Function()`, zero dynamic external scripts, zero remote script tags. 100% bundled local code. |
| **4. Unclear Privacy Behavior** | Undisclosed user data transmission | Complete data disclosures provided; explicit zero-collection guarantee for passwords, OTPs, PINs, and keystrokes. |
| **5. Financial Advisor Disclaimers** | Unlicensed financial advisory claims | Prominent notice that Nivesh is NOT an RIA, broker, or trading platform. |
| **6. Development Endpoints** | `localhost` URLs in production manifest | Packaging pipeline automatically replaces development hosts with `https://api.nivesh.ai/*` in the distribution ZIP. |
| **7. Hidden Functionality** | Undocumented background behaviors | Extension behavior strictly corresponds to declared popup and intervention flows. |
| **8. Unexplained Data Collection** | Background tracking or browsing history scraping | Ephemeral, user-invoked analysis only; zero continuous surveillance. |
| **9. Misleading Branding** | Confusion with official regulatory agencies | Brand clearly identified as "Nivesh Firewall", an independent technical security system. |

---

## 11. Distributable Package & Operational Verification

The production ZIP package is generated and verified using deterministic scripts:

```bash
# Clean production build
npm run build

# Security, secrets, and path audit
npm run audit

# Deterministic ZIP packager
npm run package
```

- **Output Archive**: `nivesh-firewall-v1.0.0.zip`
- **Archive Size**: ~24.9 KB
- **Contents**: Strictly contains Manifest V3 runtime assets (`manifest.json`, `background.js`, `content.js`, `popup/*`, `icons/*`). Zero source code, tests, `.env` files, or local filesystem paths.
