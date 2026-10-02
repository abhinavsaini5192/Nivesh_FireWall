# Nivesh Firewall — Backend Core

Production-quality implementations of **Engine 1 (Content Intelligence Engine)**, **Engine 2 (Claim Intelligence Engine)**, and **Engine 3 (Action Intelligence Engine)** for the **Nivesh Firewall** backend.

```
RAW CONTENT (Text, URL, Image)
          │
          ▼
┌───────────────────────────────────────┐
│ ENGINE 1: Content Intelligence Engine │
└───────────────────────────────────────┘
          │ (Answers: "What information exists in this content?")
          ▼
   NormalizedContent
          │
          ▼
┌───────────────────────────────────────┐
│  ENGINE 2: Claim Intelligence Engine  │
└───────────────────────────────────────┘
          │ (Answers: "What specific assertions are being made?")
          ▼
     ClaimAnalysis (CanonicalClaim[])
          │
          ▼
┌───────────────────────────────────────┐
│  ENGINE 3: Action Intelligence Engine │
└───────────────────────────────────────┘
          │ (Answers: "What is the content asking the user to do?")
          ▼
     ActionAnalysis (CanonicalAction[])
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ DOWNSTREAM ENGINES (Engine 4+):                         │
│ - Evidence & Identity Verification Engines              │
│ - Behavioural Signal Engine                             │
│ - Threat / Attack-Path Engine                           │
│ - Scam Fingerprint Engine                               │
│ - Policy & Decision Engine                              │
└─────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Strict Separation of Responsibilities**:
> - **Engine 1** normalizes text, extracts multi-modal signals, and preserves 100% provenance without risk scoring.
> - **Engine 2** structures claims into atomic Subject-Predicate-Object canonical claims with modality, temporal context, fingerprint inputs, and verification requirements.
> - **Engine 3** structures requested user actions into canonical actions with action types, progression hierarchy, targets, parameters, sequence, modality, and rationale claim linkage.
> - **Engines 1, 2, and 3 NEVER** evaluate scam likelihood, calculate risk scores, determine attack paths, or block content. Those responsibilities belong strictly to later threat and policy engines.

---

## 1. Engine 1: Content Intelligence Engine

Converts raw, unstructured content into a clean, normalized, structured schema (`NormalizedContent`).

### Capabilities
1. **Multi-Modal Ingestion**:
   - **Text**: Direct raw text ingestion.
   - **URL Ingestion Adapter** (`UrlAdapter`): Safe web fetching with 5s timeout, 5MB size limit, and BeautifulSoup tag stripping.
   - **OCR Ingestion Adapter** (`OcrAdapter`): Direct Windows Native OCR bridge (`Windows.Media.Ocr.OcrEngine`), format verification, oversized rejection, blank image detection.
2. **Text Normalization** (`TextNormalizer`):
   - Unicode NFKC (flattens math bold/italic homoglyphs).
   - Zero-width space removal (`\u200B`, `\u200C`, `\u200D`, `\uFEFF`).
   - Line-break & whitespace standardization.
   - Repeated punctuation normalization (`!!!!` -> `!`).
   - OCR hyphenation repair (`inves-\ntor` -> `investor`).
3. **Structured Signal Extraction**:
   - **URLs & Domains**: Effective domains, subdomains, multi-part TLDs (`.co.in`), ports, queries.
   - **Social Handles**: Telegram, Instagram, YouTube, Twitter/X, WhatsApp, `@mentions`.
   - **Contacts**: Normalized lowercase emails and E.164 phone numbers (`+91`).
   - **Financial Signals**: `₹` values, `lakh`/`crore`, percentages (`40%`), registration codes (`SEBI INA/INZ/IN-DP`, `GSTIN`, `CIN`, `PAN`), dates, financial terms.
   - **Entities**: Regulators with canonical expansion (`SEBI` -> `Securities and Exchange Board of India`), people names, corporate orgs, instruments.
   - **Call-To-Action (CTA)**: Detects actions (`contact`, `click`, `join_channel`, `download`, `payment`, `upload`, `credential_request`).
4. **Classifiers**:
   - **Language Detector**: English (`en`), Devanagari Hindi (`hi`), and Romanized Hindi code-mixing (`hinglish`).
   - **Financial Relevance**: Conservative boolean classification without risk labeling.

---

## 2. Engine 2: Claim Intelligence Engine

Converts `NormalizedContent` into atomic, canonical claims (`ClaimAnalysis`).

### Capabilities
1. **Atomic Claim Segmentation & Action Separation** (`ClaimSegmenter`):
   - Breaks compound sentences on discourse markers (`and therefore`, `because`, `so`).
   - Splits appositive regulatory titles and return guarantees (`SEBI registered advisor Rahul Sharma guarantees 40% returns` -> Claim 1: Regulatory identity, Claim 2: Financial return guarantee).
   - **Strict Action Filtering**: Discards pure Call-To-Action imperatives (`Join our Telegram VIP group`, `Download our app and pay ₹5,000`, `Contact rahul@example.com`, `Buy now`).
   - Extracts factual assertions embedded in action rationales (`Join Telegram because SEBI approved this group` -> extracts `SEBI approved this group` as a claim while dropping the action instruction).
2. **Canonical Subject / Predicate / Object Structuring** (`ClaimCanonicalizer`):
   - Standardizes equivalent phrasing to identical semantic forms:
     - `XYZ is debt free` == `XYZ has zero debt` == `XYZ carries no debt` -> `Subject: XYZ | Predicate: HAS_DEBT | Object: 0`.
     - `Rahul Sharma is a SEBI registered advisor` -> `Subject: Rahul Sharma | Predicate: REGISTERED_WITH | Object: SEBI`.
     - `Guaranteed 40% returns` -> `Subject: unspecified_offer | Predicate: GUARANTEED_RETURN | Object: 40%`.
     - `ABC announced a 1:1 bonus` -> `Subject: ABC | Predicate: ANNOUNCED_BONUS | Object: 1:1`.
     - `ABC will reach ₹500 next year` -> `Subject: ABC | Predicate: REACH_PRICE | Object: ₹500`.
     - `I think ABC is undervalued` -> `Subject: ABC | Predicate: VALUATION_STATUS | Object: undervalued`.
   - **Separation of Mentioned Entities from Claim Subjects**:
     - Prevents unsupported subject attribution: mentioned entities (e.g. `Rahul Sharma`) in proximity are never inferred to be claim subjects unless explicitly asserted by source text.
     - Passive / generic offers without explicit subjects default to `unspecified_offer` (e.g. `Guaranteed 40% returns`).
     - Explicit speaker attribution (e.g. `According to Rahul Sharma, ...` or `Rahul Sharma claims that ...`) is parsed separately into the `attribution` field (`ClaimAttribution`), retaining the actual claim subject as `the investment` or `unspecified_offer`.
3. **Modality & Certainty Language Detection** (`ModalityDetector`):
   - Identifies: `assertion`, `possibility`, `prediction`, `opinion`, `conditional`, `question`.
   - Captures certainty language: `guaranteed`, `definitely`, `confirmed`, `officially`, `will`, `may`, `might`, `I think`, `probably`.
4. **Temporal Context Detection** (`TemporalDetector`):
   - Classifies: `historical` (e.g. reported FY2025 profit), `current` (e.g. debt free, registered), `future` (e.g. price targets), `unknown`.
5. **Verification Requirements Generator** (`VerificationRequirementsGenerator`):
   - Generates non-evaluative evidence checklists needed later by the Evidence Verification Engine:
     - Regulatory: `["official_regulator_registry", "registration_number", "registered_entity_or_person", "registration_status", "validity_period"]`
     - Guaranteed Returns: `["statutory_regulatory_prohibition_check", "advisory_agreement_terms", "sebi_advertisement_code_compliance", ...]`
     - Corporate Events: `["official_company_announcement", "exchange_filing_bse_nse", "announcement_date", "record_date_and_ratio"]`
     - Predictions: `["unverifiable_future_outcome", "analyst_research_basis", "historical_trend_support"]`
6. **Claim Relationship Detection** (`RelationDetector`):
   - Expressed connections: `CAUSES`, `DEPENDS_ON`, `SAME_UNDERLYING_CLAIM`, `SUPPORTS`, `CONTRADICTS`, `REFINES`.
7. **Claim Deduplication** (`ClaimDeduplicator`):
   - Merges identical assertions within the same content and tracks recurring source spans.
8. **Deterministic Fingerprinting**:
   - Generates fingerprint input string for Engine 8 (Scam Fingerprint Engine):
     e.g., `ENTITY:XYZ|PREDICATE:HAS_DEBT|OBJECT:0|TEMPORAL:CURRENT|MODALITY:ASSERTION`.

---

---

## 3. Engine 3: Action Intelligence Engine

Converts `NormalizedContent` and `ClaimAnalysis` into structured canonical actions (`ActionAnalysis`).

### Capabilities
1. **Canonical Action Structuring** (`ActionSegmenter`, `ActionClassifier`):
   - Categorizes 28 normalized action types:
     - `INFORMATIONAL` / `COMMUNICATION`: `CONTACT`, `MESSAGE_PERSON`, `CALL_PERSON`, `SHARE`, `FORWARD`
     - `CHANNEL_MIGRATION`: `JOIN_CHANNEL`, `JOIN_GROUP`, `FOLLOW_ACCOUNT`
     - `NAVIGATION`: `CLICK_LINK`, `OPEN_WEBSITE`
     - `SOFTWARE_INSTALLATION`: `DOWNLOAD`, `INSTALL`
     - `DATA_DISCLOSURE`: `UPLOAD_DOCUMENT`, `UPLOAD_IDENTITY`, `SHARE_PERSONAL_INFORMATION`, `SHARE_FINANCIAL_INFORMATION`
     - `CREDENTIAL_ACCESS`: `ENTER_CREDENTIALS`, `SHARE_OTP`
     - `ACCOUNT_AUTHORIZATION`: `CONNECT_ACCOUNT`, `CONNECT_BANK`, `AUTHORIZE_ACCESS`, `SIGN_DOCUMENT`
     - `FINANCIAL_TRANSACTION`: `PAYMENT`, `TRANSFER_MONEY`, `DEPOSIT_MONEY`, `WITHDRAW_MONEY`, `BUY`, `SELL`
     - Fallback: `OTHER`
2. **Action Progression Hierarchy**:
   - Maps every action to one of 9 non-evaluative structural stages:
     `INFORMATIONAL` (1) → `COMMUNICATION` (2) → `CHANNEL_MIGRATION` (3) → `NAVIGATION` (4) → `SOFTWARE_INSTALLATION` (5) → `DATA_DISCLOSURE` (6) → `CREDENTIAL_ACCESS` (7) → `ACCOUNT_AUTHORIZATION` (8) → `FINANCIAL_TRANSACTION` (9).
   - This progression purely reflects functional action categories, strictly independent of risk or threat judgments.
3. **Target Normalization** (`ActionTargetExtractor`):
   - Reuses Engine 1 entities, handles, URLs, and contacts to resolve action targets:
     - `channel`: Telegram, WhatsApp, Discord, etc.
     - `application`: APK, mobile apps, desktop binaries.
     - `website`: Domains and destination URLs.
     - `person`: Extracted advisors, contacts, emails, or phone numbers.
     - `account`: Transfer and deposit recipient accounts.
4. **Structured Parameter Extraction & Privacy Protection** (`ActionParameterExtractor`):
   - Extracts currencies (`INR`), amounts (`5000.0`), deadlines (`6 PM`), timeframes, and urgency indicators.
   - **Strict Privacy**: Never collects, extracts, or stores sensitive user passwords, OTP values, or credit card numbers. Only represents the presence of credential or verification objects (e.g. `trading password`, `OTP`).
5. **Modality & Intent Strength** (`ActionModalityDetector`):
   - Distinguishes:
     - `instruction` (`direct`): "Pay ₹5,000 now."
     - `suggestion` (`indirect`): "You should consider joining our group."
     - `invitation` (`direct`/`indirect`): "Join us on Telegram."
     - `warning` (`direct`): "Beware of fake accounts."
     - `implicit` (`indirect`): "To activate your account, KYC must be completed."
6. **Multi-Action Sequencing & Relationship Tracking** (`ActionRationaleLinker`):
   - Preserves compound action execution sequence: `1 -> JOIN_CHANNEL`, `2 -> DOWNLOAD`, `3 -> UPLOAD_DOCUMENT`, `4 -> PAYMENT`.
   - Links action relationships: `ENABLES`, `PRECEDES`.
   - Links Engine 2 claim justification rationales: `RATIONALE_FOR` (e.g. `CLAIM-001` "SEBI approved this group" -> `ACTION-001` "Join Telegram").
7. **Action Deduplication & Deterministic Fingerprints** (`ActionDeduplicator`, `ActionFingerprintGenerator`):
   - Merges recurring identical actions into a single canonical action record while tracking all occurrence spans (`source_spans`).
   - Produces stable fingerprints for downstream indexing (e.g. `ACTION:PAYMENT|AMOUNT:5000.0|CURRENCY:INR|TARGET:ACCOUNT`).

---

## 4. Benchmark Fixture Execution

### Benchmark Input:
```
"🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join our Telegram VIP group: https://t.me/rahulinvest. Download our app and pay ₹5,000. Contact rahul@example.com."
```

### Pipeline Flow:
```
Raw Text ──▶ Engine 1 (NormalizedContent) ──▶ Engine 2 (ClaimAnalysis) ──▶ Engine 3 (ActionAnalysis)
```

### Engine 1 (NormalizedContent):
- **Entities**:
  - People: `Rahul Sharma` (confidence: 0.96)
  - Regulators: `SEBI` -> `Securities and Exchange Board of India` (confidence: 0.99)
- **Structured Signals**:
  - URLs: `https://t.me/rahulinvest`
  - Social Handles: `{"platform": "telegram", "handle": "rahulinvest"}`
  - Email: `rahul@example.com`
  - Currency: `₹5,000` (INR 5000.0)
  - Percentages: `40%` (40.0)
- **Actions Detected**: `join_channel`, `download`, `payment`, `contact`

### Engine 2 (ClaimAnalysis):
```json
{
  "content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
  "claims": [
    {
      "claim_id": "CLAIM-001",
      "claim_type": "REGULATORY",
      "subject": "Rahul Sharma",
      "predicate": "REGISTERED_WITH",
      "object": "SEBI",
      "canonical_fingerprint": "ENTITY:RAHUL_SHARMA|PREDICATE:REGISTERED_WITH|OBJECT:SEBI|TEMPORAL:CURRENT|MODALITY:ASSERTION"
    },
    {
      "claim_id": "CLAIM-002",
      "claim_type": "FINANCIAL",
      "subject": "unspecified_offer",
      "predicate": "GUARANTEED_RETURN",
      "object": "40% returns",
      "canonical_fingerprint": "ENTITY:UNSPECIFIED_OFFER|PREDICATE:GUARANTEED_RETURN|OBJECT:40__RETURNS|TEMPORAL:UNKNOWN|MODALITY:ASSERTION"
    }
  ]
}
```

### Engine 3 (ActionAnalysis):
```json
{
  "content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
  "actions": [
    {
      "action_id": "ACTION-001",
      "source_content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
      "text": {
        "original": "Join our Telegram VIP group: https://t.me/rahulinvest.",
        "normalized": "Join our Telegram VIP group: https://t.me/rahulinvest."
      },
      "action_type": "JOIN_CHANNEL",
      "actor": { "type": "user", "name": null },
      "target": { "type": "channel", "value": "Telegram" },
      "objects": [],
      "parameters": {},
      "sequence": { "index": 1, "is_prerequisite_for": null, "depends_on": null },
      "modality": { "type": "instruction", "strength": "direct" },
      "source_span": { "start": 64, "end": 127 },
      "confidence": 0.95,
      "canonical_fingerprint": "ACTION:JOIN_CHANNEL|TARGET:CHANNEL|MODALITY:INSTRUCTION",
      "provenance": { "extraction_method": "hybrid", "processing_version": "1.0.0" }
    },
    {
      "action_id": "ACTION-002",
      "source_content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
      "text": {
        "original": "Download our app",
        "normalized": "Download our app"
      },
      "action_type": "DOWNLOAD",
      "actor": { "type": "user", "name": null },
      "target": { "type": "application", "value": "app" },
      "objects": ["app"],
      "parameters": {},
      "sequence": { "index": 2, "is_prerequisite_for": null, "depends_on": null },
      "modality": { "type": "instruction", "strength": "direct" },
      "source_span": { "start": 128, "end": 144 },
      "confidence": 0.95,
      "canonical_fingerprint": "ACTION:DOWNLOAD|TARGET:APPLICATION|MODALITY:INSTRUCTION",
      "provenance": { "extraction_method": "hybrid", "processing_version": "1.0.0" }
    },
    {
      "action_id": "ACTION-003",
      "source_content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
      "text": {
        "original": "pay ₹5,000.",
        "normalized": "pay ₹5,000."
      },
      "action_type": "PAYMENT",
      "actor": { "type": "user", "name": null },
      "target": { "type": "account", "value": null },
      "objects": [],
      "parameters": { "amount": 5000.0, "currency": "INR", "deadline": null, "timeframe": null, "urgency": null },
      "sequence": { "index": 3, "is_prerequisite_for": null, "depends_on": null },
      "modality": { "type": "instruction", "strength": "direct" },
      "source_span": { "start": 149, "end": 160 },
      "confidence": 0.95,
      "canonical_fingerprint": "ACTION:PAYMENT|AMOUNT:5000.0|CURRENCY:INR|TARGET:ACCOUNT|MODALITY:INSTRUCTION",
      "provenance": { "extraction_method": "hybrid", "processing_version": "1.0.0" }
    },
    {
      "action_id": "ACTION-004",
      "source_content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
      "text": {
        "original": "Contact rahul@example.com.",
        "normalized": "Contact rahul@example.com."
      },
      "action_type": "CONTACT",
      "actor": { "type": "user", "name": null },
      "target": { "type": "person", "value": "rahul@example.com" },
      "objects": [],
      "parameters": {},
      "sequence": { "index": 4, "is_prerequisite_for": null, "depends_on": null },
      "modality": { "type": "instruction", "strength": "direct" },
      "source_span": { "start": 161, "end": 187 },
      "confidence": 0.95,
      "canonical_fingerprint": "ACTION:CONTACT|TARGET:PERSON|MODALITY:INSTRUCTION",
      "provenance": { "extraction_method": "hybrid", "processing_version": "1.0.0" }
    }
  ],
  "action_relations": [],
  "analysis_metadata": {
    "processing_time_ms": 3.42,
    "total_actions": 4,
    "action_types_count": { "JOIN_CHANNEL": 1, "DOWNLOAD": 1, "PAYMENT": 1, "CONTACT": 1 },
    "hierarchy_categories_present": ["COMMUNICATION", "CHANNEL_MIGRATION", "SOFTWARE_INSTALLATION", "FINANCIAL_TRANSACTION"],
    "max_hierarchy_rank": 9,
    "duplicate_actions_merged": 0
  }
}
```

---

## 5. API Endpoints

Start the server:
```bash
uvicorn nivesh.api.app:app --host 0.0.0.0 --port 8000
```

1. **`GET /health`** / **`GET /api/v1/health`**:
   Returns system status and active engines (`content_intelligence`, `claim_intelligence`, `action_intelligence`).
2. **`POST /api/v1/content/analyze`** (Engine 1):
   - Body: `{"text": "...", "url": "...", "channel": "telegram"}`
   - Form-Data: `file=@screenshot.png`, `channel=whatsapp`
   - Output: `NormalizedContent`
3. **`POST /api/v1/claims/analyze`** (Engine 2):
   - Body: `NormalizedContent` JSON
   - Output: `ClaimAnalysis`
4. **`POST /api/v1/actions/analyze`** (Engine 3):
   - Body: `{"content": NormalizedContent, "claims": ClaimAnalysis (optional)}` or directly `NormalizedContent`
   - Output: `ActionAnalysis`

---

## 6. Direct Python Service Interface

```python
from nivesh import (
    ContentIntelligenceEngine,
    ClaimIntelligenceEngine,
    ActionIntelligenceEngine,
)

# Initialize engines
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()
actions_engine = ActionIntelligenceEngine()

raw_text = (
    "SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
    "Join our Telegram VIP group: https://t.me/rahulinvest. "
    "Download our app and pay ₹5,000. Contact rahul@example.com."
)

# Step 1: Engine 1 (What information exists?)
normalized = content_engine.process_text(raw_text)

# Step 2: Engine 2 (What claims are being made?)
claims = claims_engine.analyze(normalized)

# Step 3: Engine 3 (What actions are requested?)
actions = actions_engine.analyze(normalized, claims)

print(f"Content ID: {normalized.content_id}")
print(f"Extracted {len(claims.claims)} claims:")
for c in claims.claims:
    print(f"  [{c.claim_id}] {c.subject} -> {c.predicate} -> {c.object}")

print(f"\nExtracted {len(actions.actions)} actions:")
for a in actions.actions:
    print(f"  [{a.action_id}] #{a.sequence.index} {a.action_type} (Target: {a.target.type}={a.target.value})")
    if a.parameters.amount:
        print(f"      Parameters: {a.parameters.currency} {a.parameters.amount}")
    if a.rationale_claim_ids:
        print(f"      Rationale Claims: {a.rationale_claim_ids}")
```

---

## 7. Test Suite Verification

Run all pytest unit and integration tests:

```bash
python -X utf8 -m pytest -v
```

**Results:** `133 passed in 4.67s` (0 failed, 100% pass rate).
- **Engine 1 Unit Tests**: Text normalizer (7), URL extractor (8), Social extractor (6), Contact extractor (4), Financial extractor (6), Entity extractor (5), CTA extractor (7), Language detector (4), Financial relevance (4), OCR adapter (6), URL adapter (3), Primary fixture (3), API (4) -> **67 tests**.
- **Engine 2 Unit Tests**: Claim canonicalizer (7), Modality and Temporal (8), Claim segmenter & Action filtering (5), Verification requirements & Relations (5), Benchmark cases (7), Primary fixture (1), Engine 1 -> Engine 2 integration (3), Claim API (3), Correction tests (5) -> **44 tests**.
- **Engine 3 Unit Tests**: Schemas & validation (3), Classifier & hierarchy (3), Parameter extractor & privacy (4), Benchmark cases (6), Primary fixture benchmark (2), Engine 1 -> Engine 2 -> Engine 3 integration (2), Action API (2) -> **22 tests**.

