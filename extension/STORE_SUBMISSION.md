# Nivesh Firewall — Chrome Web Store Submission & Packaging Guide

This document contains the verified metadata, permission justifications, privacy disclosures, and asset specifications for submitting **Nivesh Firewall** to the Chrome Web Store.

---

## 1. Store Listing Metadata

| Field | Value |
| :--- | :--- |
| **Extension Name** | `Nivesh Firewall` |
| **Version** | `1.0.0` |
| **Manifest Version** | `3` |
| **Category** | `Privacy & Security` / `Productivity` |
| **Summary / Short Description** | `Inspect financial content and verify claims before consequential actions with real-time pre-action safety checks.` (114 chars, limit: 132 chars) |
| **Primary Language** | English |
| **Support / Website URL** | `https://nivesh.ai` *(or local development placeholder)* |

---

## 2. Detailed Store Description

```markdown
Nivesh Firewall provides pre-action verification and intervention for financial content, claims, and investment solicitations directly within your browser.

Before you make a financial commitment, wire funds, join an unverified investment group, or act on high-pressure advisory claims, Nivesh Firewall helps you evaluate the content against authoritative financial signals and scam patterns.

### Key Capabilities

• One-Click Page Analysis: Inspect visible financial claims and advisory content on any active webpage.
• Selected Text Verification: Highlight specific claims, return promises, or advisory messages to inspect them in isolation.
• Pre-Action Interventions: Non-invasive warnings, pauses, or block interventions when high-risk patterns or fabricated regulatory registrations are detected.
• Deep-Link Audit: Open the full Nivesh Web Application with a single click to review detailed claims breakdown, regulatory provenance, and threat intelligence.
• Privacy-Preserving Architecture: Operates strictly on-demand. Zero continuous background tracking, zero keystroke logging, and zero credential harvesting.

### Regulatory & Fiduciary Notice

Nivesh Firewall is a technical security tool designed to detect manipulation patterns and verify publicly verifiable regulatory registrations. 

Nivesh Firewall:
- is NOT a registered investment advisor (RIA) or broker-dealer
- does NOT offer investment advice, buy/sell recommendations, or portfolio management
- does NOT execute financial transactions
- does NOT guarantee that any opportunity is risk-free or fraudulent
```

---

## 3. Chrome Web Store Permission Justifications

Chrome Web Store reviewers require an explicit justification for every requested permission demonstrating adherence to the **Principle of Least Privilege**:

### `activeTab`
> **Justification**: Granted only when the user explicitly interacts with the Nivesh Firewall extension (e.g., clicking the toolbar popup icon or selecting "Analyze This Page"). It allows the extension to inspect the current active webpage's URL and visible content to evaluate financial claims without requiring broad, persistent access to the user's entire browsing session.

### `storage`
> **Justification**: Used exclusively to persist local user settings (e.g., theme preferences, API endpoint configuration) and tab-scoped lightweight analysis references (`analysisId`, decision status) to ensure UI continuity across service worker suspension cycles. It NEVER stores sensitive credentials, passwords, or raw banking text.

### `scripting`
> **Justification**: Used to display the isolated in-page Shadow DOM intervention overlay (`SHOW_INTERVENTION`) when an analysis returns a `WARN`, `PAUSE`, or `BLOCK` decision, warning the user of detected threats before they proceed with a consequential action.

### Host Permissions (`https://api.nivesh.ai/*`)
> **Justification**: Required exclusively to transmit the user-initiated analysis request to the Nivesh Unified Firewall API over secure HTTPS (`POST /api/v1/firewall/analyze`) and receive real-time policy and threat determinations. The extension does not access any other external domain or origin.

### Strictly Forbidden Permissions Audit
The extension explicitly avoids and does **NOT** request:
- `<all_urls>` or wildcard domain access
- `tabs` (unrestricted tab monitoring)
- `history` (browsing history access)
- `passwords` / `credentials`
- `clipboardRead` / `clipboardWrite`
- `webRequest` / `webRequestBlocking`
- `cookies`

---

## 4. Privacy & Data Disclosure Declaration

### Single Purpose Description
> Nivesh Firewall inspects user-selected or active-page financial claims against authoritative regulatory sources and threat indicators to protect users from deceptive financial schemes.

### Data Types Accessed and Transmitted
1. **Webpage Content**: Visible text or user-highlighted text from the active tab upon explicit user trigger.
2. **Page URL & Title**: The URL of the inspected page to identify domain registration anomalies and scam fingerprints.

### Data Explicitly Excluded (Zero-Collection Guarantee)
The content extractor and background service worker enforce strict sanitization rules:
- **No Passwords**: `<input type="password">` fields are completely excluded.
- **No Payment Credentials**: Credit card numbers, CVVs, expiration dates, PINs, and bank account numbers are scrubbed.
- **No One-Time Passwords (OTPs)**: Security codes and OTP fields are explicitly filtered out.
- **No Hidden Fields**: `<input type="hidden">` values are ignored.
- **No Keystroke Listening**: There are no keyboard event hooks or input logging listeners.
- **No Continuous Surveillance**: The extension does not scrape or monitor pages in the background; it acts strictly upon direct user request.

---

## 5. Visual Asset Specifications

| Asset | Dimensions | Format | Status | Location |
| :--- | :--- | :--- | :--- | :--- |
| **Small Icon** | `16 x 16 px` | PNG (32-bit RGBA) | Built | `icons/icon16.png` |
| **Medium Icon** | `48 x 48 px` | PNG (32-bit RGBA) | Built | `icons/icon48.png` |
| **Store / Large Icon** | `128 x 128 px` | PNG (32-bit RGBA) | Built | `icons/icon128.png` |
| **Screenshot 1** | `1280 x 800 px` | PNG | Ready for capture | Popup: Ready State & Active Context |
| **Screenshot 2** | `1280 x 800 px` | PNG | Ready for capture | Popup: Analyzing & Signal Detection |
| **Screenshot 3** | `1280 x 800 px` | PNG | Ready for capture | In-Page: Warning Intervention Overlay |
| **Screenshot 4** | `1280 x 800 px` | PNG | Ready for capture | Web App: Full Firewall Deep Link Review |

---

## 6. Distributable Package Verification

The production-ready ZIP package is deterministically generated by:
```bash
npm run package
```
- **Archive File**: `nivesh-firewall-v1.0.0.zip`
- **Integrity**: Contains strictly validated Manifest V3 runtime assets, icons, and bundles.
- **Cleanliness**: Contains zero `.ts`, `.test.`, `.map`, `.env`, temporary files, or local filesystem paths.
