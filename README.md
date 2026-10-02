# Nivesh Firewall — Backend Core

Production-quality implementations of **Engine 1 (Content Intelligence Engine)** and **Engine 2 (Claim Intelligence Engine)** for the **Nivesh Firewall** backend.

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
┌─────────────────────────────────────────────────────────┐
│ DOWNSTREAM ENGINES (Engine 3+):                         │
│ - Action Intelligence Engine (imperative user actions)   │
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
> - **Engine 2 NEVER** evaluates whether a claim is true or false, never queries SEBI registries, never checks scam likelihood, and never blocks content.

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

## 3. Benchmark Fixture Execution

### Benchmark Input:
```
"🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join our Telegram VIP group: https://t.me/rahulinvest. Download our app and pay ₹5,000. Contact rahul@example.com."
```

### Engine 1 (NormalizedContent):
- **Raw Text preserved**: Exact emoji and text preserved.
- **Normalized Text**: `🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join our Telegram VIP group: https://t.me/rahulinvest. Download our app and pay ₹5,000. Contact rahul@example.com.`
- **Entities**:
  - People: `Rahul Sharma` (confidence: 0.96)
  - Regulators: `SEBI` -> `Securities and Exchange Board of India` (confidence: 0.99)
- **Structured Signals**:
  - URLs: `https://t.me/rahulinvest`
  - Social Handles: `{"platform": "telegram", "handle": "rahulinvest"}`
  - Email: `rahul@example.com`
  - Currency: `₹5,000` (INR 5000.0)
  - Percentages: `40%` (40.0)
  - Financial Terms: `SEBI registered`, `SEBI`, `registered`, `advisor`, `Guaranteed`, `returns`, `Telegram`, `VIP group`, `app`, `pay`
- **Actions Detected**:
  - `Join our Telegram VIP group` (`join_channel`)
  - `Download our app` (`download`)
  - `pay ₹5,000` (`payment`)
  - `Contact rahul@example.com` (`contact`)
- **Financial Relevance**: `contains_financial_content: true` (confidence: 0.99)

### Engine 2 (ClaimAnalysis):
```json
{
  "content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
  "claims": [
    {
      "claim_id": "CLAIM-001",
      "source_content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
      "text": {
        "original": "Rahul Sharma is a SEBI registered advisor",
        "normalized": "Rahul Sharma is registered with SEBI."
      },
      "claim_type": "REGULATORY",
      "subject": "Rahul Sharma",
      "predicate": "REGISTERED_WITH",
      "object": "SEBI",
      "temporal_context": { "type": "current", "date": null, "raw_text": "is" },
      "modality": { "type": "assertion", "certainty_language": null },
      "source_span": { "start": 0, "end": 38 },
      "confidence": 0.95,
      "canonical_fingerprint": "ENTITY:RAHUL_SHARMA|PREDICATE:REGISTERED_WITH|OBJECT:SEBI|TEMPORAL:CURRENT|MODALITY:ASSERTION",
      "verification_requirements": [
        "official_regulator_registry",
        "registration_number",
        "registered_entity_or_person",
        "registration_status",
        "validity_period"
      ],
      "provenance": { "extraction_method": "hybrid", "processing_version": "1.0.0" }
    },
    {
      "claim_id": "CLAIM-002",
      "source_content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
      "text": {
        "original": "Guaranteed 40% returns.",
        "normalized": "40% returns are guaranteed."
      },
      "claim_type": "FINANCIAL",
      "subject": "unspecified_offer",
      "predicate": "GUARANTEED_RETURN",
      "object": "40% returns",
      "attribution": null,
      "temporal_context": { "type": "unknown", "date": null, "raw_text": null },
      "modality": { "type": "assertion", "certainty_language": "Guaranteed" },
      "source_span": { "start": 40, "end": 63 },
      "confidence": 0.95,
      "canonical_fingerprint": "ENTITY:UNSPECIFIED_OFFER|PREDICATE:GUARANTEED_RETURN|OBJECT:40__RETURNS|TEMPORAL:UNKNOWN|MODALITY:ASSERTION",
      "verification_requirements": [
        "statutory_regulatory_prohibition_check",
        "return_terms",
        "offer_documentation",
        "advertising_disclosure_evidence",
        "sebi_advertisement_code_compliance"
      ],
      "provenance": { "extraction_method": "hybrid", "processing_version": "1.0.0" }
    }
  ],
  "claim_relations": [],
  "analysis_metadata": {
    "processing_time_ms": 2.99,
    "total_claims": 2,
    "claim_types_count": { "REGULATORY": 1, "FINANCIAL": 1 },
    "actions_filtered_count": 3,
    "duplicate_claims_merged": 0
  }
}
```

---

## 4. API Endpoints

Start the server:
```bash
uvicorn nivesh.api.app:app --host 0.0.0.0 --port 8000
```

1. **`GET /health`** / **`GET /api/v1/health`**:
   Returns system status and active engines.
2. **`POST /api/v1/content/analyze`** (Engine 1):
   - Body: `{"text": "...", "url": "...", "channel": "telegram"}`
   - Form-Data: `file=@screenshot.png`, `channel=whatsapp`
   - Output: `NormalizedContent`
3. **`POST /api/v1/claims/analyze`** (Engine 2):
   - Body: `NormalizedContent` JSON
   - Output: `ClaimAnalysis`

---

## 5. Direct Python Service Interface

```python
from nivesh import ContentIntelligenceEngine, ClaimIntelligenceEngine

# Initialize engines
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()

# Process content through Engine 1
normalized = content_engine.process_text(
    "SEBI registered advisor Rahul Sharma guarantees 40% returns. "
    "ABC announced a 1:1 bonus. Join our Telegram group."
)

# Process normalized content through Engine 2
analysis = claims_engine.analyze(normalized)

for claim in analysis.claims:
    print(f"[{claim.claim_id}] {claim.subject} -> {claim.predicate} -> {claim.object} ({claim.claim_type})")
    print(f"  Fingerprint: {claim.canonical_fingerprint}")
    print(f"  Verification: {claim.verification_requirements}\n")
```

---

## 6. Test Suite Verification

Run all pytest unit and integration tests:

```bash
python -m pytest -v
```

**Results:** `106 passed in 9.39s` (0 failed, 100% pass rate).
- **Engine 1 Unit Tests**: Text normalizer (7), URL extractor (8), Social extractor (6), Contact extractor (4), Financial extractor (6), Entity extractor (5), CTA extractor (7), Language detector (4), Financial relevance (4), OCR adapter (6), URL adapter (3), Primary fixture (3), API (4) -> **67 tests**.
- **Engine 2 Unit Tests**: Claim canonicalizer (7), Modality and Temporal (8), Claim segmenter & Action filtering (5), Verification requirements & Relations (5), Benchmark cases (7), Primary fixture (1), Engine 1 -> Engine 2 integration (3), Claim API (3) -> **39 tests**.
