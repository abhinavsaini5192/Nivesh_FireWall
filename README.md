# Nivesh Firewall — Backend Core

Production-quality implementations of **Engine 1 (Content Intelligence)**, **Engine 2 (Claim Intelligence)**, **Engine 3 (Action Intelligence)**, **Engine 4 (Source Intelligence)**, and **Engine 5 (Evidence Verification Engine)** for the **Nivesh Firewall** backend.

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
┌───────────────────────────────────────┐
│  ENGINE 4: Source Intelligence Engine │
└───────────────────────────────────────┘
          │ (Answers: "Where is authoritative information, and what source material was retrieved?")
          ▼
     SourceAnalysis (SourceDocument[], EvidenceCandidate[])
          │
          ▼
┌───────────────────────────────────────────┐
│ ENGINE 5: Evidence Verification Engine    │
└───────────────────────────────────────────┘
          │ (Answers: "What does the retrieved evidence actually establish about this claim?")
          ▼
     EvidenceAnalysis (VerificationResult[])
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ DOWNSTREAM ENGINES (Engine 6+):                         │
│ - Threat / Attack-Path Engine (Engine 6)                │
│ - Scam Fingerprint Engine (Engine 7)                    │
│ - Policy & Safety Intervention Engine (Engine 8)        │
└─────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Strict Separation of Responsibilities**:
> - **Engine 1** normalizes text, extracts multi-modal signals, and preserves 100% provenance without risk scoring.
> - **Engine 2** structures claims into atomic Subject-Predicate-Object canonical claims with modality, temporal context, fingerprint inputs, and verification requirements.
> - **Engine 3** structures requested user actions into canonical actions with action types, progression hierarchy, targets, parameters, sequence, modality, and rationale claim linkage.
> - **Engine 4** routes claims to authoritative source taxonomies, queries official registries/filings (SEBI, NSE, etc.), normalizes retrieved documents, and generates structured evidence candidates with full provenance while keeping verification status strictly `UNVERIFIED`.
> - **Engine 5** evaluates claim-level evidence relationships (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `NOT_VERIFIABLE`, `SOURCE_CONFLICT`), strictly separating source retrieval status from claim truth, and distinguishing absence of evidence from falsity.
> - **Engines 1 through 5 NEVER** recommend buying/selling/holding investments, predict future market outcomes, calculate general "scam probabilities", determine overall attack paths, or create final blocking decisions. Those decisions belong strictly to later threat and policy engines.


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

## 4. Engine 4: Source Intelligence Engine

Discovers authoritative sources, routes structured claims, retrieves official filings/registries, and normalizes candidate evidence (`SourceAnalysis`).

### Capabilities
1. **Controlled Source Taxonomy & Authority Tiers**:
   - Taxonomies: `REGULATOR`, `REGULATORY_REGISTRY`, `STOCK_EXCHANGE`, `GOVERNMENT`, `COMPANY_OFFICIAL`, `STATUTORY_DOCUMENT`, `FINANCIAL_FILING`, `CORPORATE_ANNOUNCEMENT`, `CORPORATE_ACTION`, `LEGAL_DOCUMENT`, `DOMAIN_SOURCE`, `PUBLIC_DATABASE`, `NEWS`, `OTHER`.
   - Authority Tiers: `PRIMARY_OFFICIAL`, `SECONDARY_RELIABLE`, `SECONDARY`, `UNKNOWN` (describes source authority, NOT claim truth).
2. **Centralized Source Catalog** (`SourceCatalog`):
   - Central registry for official data sources (SEBI Intermediaries Registry, SEBI Enforcement/Regulations, NSE Corporate Announcements, NSE Corporate Actions, NSE Company Filings, BSE, RBI, MCA21, etc.).
   - Prevents hardcoded lookup logic across the application.
3. **Deterministic Source Routing** (`SourceRouter`):
   - Routes claims based strictly on structured fields (`subject`, `predicate`, `object`, `temporal_context`, registration numbers):
     - `REGULATORY` / `REGISTERED_WITH` → `sebi_recognised_intermediaries`
     - `GUARANTEED_RETURN` → `sebi_public_regulatory_pages` (SEBI Code of Conduct prohibitions)
     - `CORPORATE_EVENT` / `ANNOUNCED_BONUS` → `nse_corporate_actions` / `nse_corporate_announcements`
     - `FINANCIAL` / `REPORTED_PROFIT` → `nse_company_filings`
4. **Authoritative Source Adapters** (`SEBIAdapter`, `NSEAdapter`, `BSEAdapter`, etc.):
   - `SEBIAdapter`: Real adapter supporting registration numbers, person/intermediary names, trade names, and statutory prohibitions.
   - `NSEAdapter`: Real adapter supporting company symbols, announcement keywords, date filtering, and corporate actions.
   - Boundary Adapters: `BSEAdapter`, `RBIAdapter`, `CompanySourceAdapter` (return explicit `SOURCE_UNAVAILABLE` when unconfigured).
   - **Explicit Execution Modes**: `LIVE`, `CACHE`, `FIXTURE` (never fakes live provenance).
5. **SSRF Protection & Outbound Request Safety** (`SsrfValidator`):
   - Rejects non-HTTP(S) schemes (`file://`, `ftp://`).
   - Rejects loopback (`127.0.0.0/8`, `localhost`, `::1`), private networks (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local (`169.254.0.0/16`), and internal hostnames (`.local`, `.internal`).
   - Validates redirects iteratively against SSRF before following.
   - Enforces 5MB size caps and 5.0s timeouts.
6. **Caching & Rate Limiting** (`SourceCache`, `RateLimiter`):
   - In-memory cache with query hash keys and TTLs.
   - Rate limiting with token intervals and exponential backoff.
7. **Document Normalization & Evidence Candidates** (`SourceNormalizer`):
   - Normalizes disparate sources into a standard `SourceDocument`.
   - Extracts focused `EvidenceCandidate` excerpts with `matched_terms`, `matched_entities`, and `matched_dates`.
   - **CRITICAL**: Verification status is strictly preserved as `UNVERIFIED`. Engine 5 evaluates truth.

---

## 5. Engine 5: Evidence Verification Engine

Evaluates whether retrieved source material supports, contradicts, partially supports, or fails to establish a claim (`EvidenceAnalysis`).

### Capabilities
1. **Rich Verification Status Model**:
   - `SUPPORTED`: Authoritative source directly corroborates the factual assertion.
   - `PARTIALLY_SUPPORTED`: Evidence confirms core aspects (e.g., 1:1 bonus ratio) but leaves other aspects unverified (e.g., announcement date).
   - `CONTRADICTED`: Authoritative source directly refutes the claim with an incompatible fact (e.g., debt-free assertion vs reported borrowings of ₹240 Cr; claimed 40% growth vs actual calculated 20%).
   - `INSUFFICIENT_EVIDENCE`: Available evidence does not establish the claim, or forward-looking predictions cannot be proven as present facts. (Absence of evidence is never falsely marked `FALSE`).
   - `NOT_VERIFIABLE`: Subjective opinions, evaluative assertions lacking empirical criteria ("safest", "best", ungrounded "undervalued").
   - `SOURCE_CONFLICT`: Multiple relevant sources present mutually conflicting facts.
   - `SOURCE_UNAVAILABLE`: Sources were uncontactable or unconfigured.
2. **Separation of Factual Contradiction vs. Regulatory Conflict**:
   - **`FACTUAL_CONTRADICTION` (`CONTRADICTED`)**: Used ONLY when evidence establishes a direct factual state incompatible with the claim (e.g., debt-free vs reported ₹240 Cr borrowings).
   - **`REGULATORY_CONFLICT`**: When evidence establishes that the described conduct or claim conflicts with an official regulation, circular, or prohibition (e.g., SEBI code of conduct ban on guaranteed returns). The claim status is set to `INSUFFICIENT_EVIDENCE` (the rule does not establish whether the person factually made the claim), and the regulatory violation is captured in a structured `regulatory_findings` field with full provenance.
3. **Strict Separation of Claim Status ≠ Source Status**:
   - Explicitly decouples retrieval outcomes from verification outcomes (e.g., `{ "source_status": "NO_MATCH", "claim_verification_status": "INSUFFICIENT_EVIDENCE" }`).
4. **Structured Verification Engines**:
   - **`RegulatoryEvaluator`**: Performs structured identity matching between claimed entities and official registries (SEBI), records registry mismatches without baseless fraud accusations, and attaches `REGULATORY_CONFLICT` findings when conduct violates statutory prohibitions.
   - **`NumericalEvaluator`**: Computes exact percentage changes and baseline-to-current arithmetic derivations (`(v2 - v1) / v1 * 100`), checks debt-free vs outstanding borrowings, bonus/split ratios, and applies a controlled 0.5% tolerance policy for rounding differences.
   - **`OpinionPredictionEvaluator`**: Evaluates forward-looking predictions safely without inventing market projections, and classifies subjective opinions as `NOT_VERIFIABLE`.
   - **`ConflictDetector`**: Detects discrepancies and factual disagreements across multiple retrieved sources.
   - **`LlmVerifier`**: Constrained semantic comparison with prompt injection defense, sandboxing retrieved text in `<UNTRUSTED_SOURCE_PASSAGE>` and ignoring adversarial instructions.
5. **Context Gap Detection**:
   - Flags when a numerical assertion is mathematically correct but omits critical context (omitted reporting periods, omitted baseline absolute figures).
6. **Auditable Reasoning Trace & Citations**:
   - Generates concise step-by-step audit traces for frontend explanation without exposing internal LLM deliberative thinking.
   - Retains source IDs, URLs, organizations, and verbatim excerpts with full provenance.

---

## 6. Benchmark Fixture Execution

### Benchmark Input:
```
"🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. Join our Telegram VIP group: https://t.me/rahulinvest. Download our app and pay ₹5,000. Contact rahul@example.com."
```

### Pipeline Flow:
```
Raw Text ──▶ Engine 1 (Content) ──▶ Engine 2 (Claims) ──▶ Engine 3 (Actions) ──▶ Engine 4 (Sources) ──▶ Engine 5 (Evidence)
```

### Engine 1 (NormalizedContent):
- **Entities**: `Rahul Sharma` (person, 0.96), `SEBI` (regulator, 0.99)
- **Structured Signals**: URL: `https://t.me/rahulinvest`, Handle: `telegram:rahulinvest`, Email: `rahul@example.com`, Currency: `₹5,000` (INR 5000.0), Percentage: `40%` (40.0)
- **Actions Detected**: `join_channel`, `download`, `payment`, `contact`

### Engine 2 (ClaimAnalysis):
- **`CLAIM-001`**: `Rahul Sharma` → `REGISTERED_WITH` → `SEBI` (`REGULATORY`)
- **`CLAIM-002`**: `unspecified_offer` → `GUARANTEED_RETURN` → `40% returns` (`FINANCIAL`)

### Engine 3 (ActionAnalysis):
- **`ACTION-001`**: `#1 JOIN_CHANNEL` (Target: `channel:Telegram`)
- **`ACTION-002`**: `#2 DOWNLOAD` (Target: `application:app`)
- **`ACTION-003`**: `#3 PAYMENT` (Target: `account`, Amount: `INR 5000.0`)
- **`ACTION-004`**: `#4 CONTACT` (Target: `person:rahul@example.com`)

### Engine 4 (SourceAnalysis):
```json
{
  "content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
  "claim_sources": [
    {
      "claim_id": "CLAIM-001",
      "source_plan": {
        "primary": ["sebi_recognised_intermediaries"],
        "fallback": ["sebi_public_regulatory_pages", "government_official_sources"],
        "required_source_types": ["REGULATORY_REGISTRY", "REGULATOR"],
        "query": { "name": "Rahul Sharma", "keywords": ["registration", "intermediary", "advisor"] }
      },
      "searches": [
        {
          "result_id": "SEBI-SEARCH-E1A40BD3",
          "source_id": "sebi_recognised_intermediaries",
          "title": "SEBI Recognized Intermediary Registry Search: Rahul Sharma",
          "url": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFmr=yes&intmId=13&searchTerm=Rahul+Sharma"
        }
      ],
      "documents": [
        {
          "document_id": "DOC-C9B6A974",
          "organization": "SEBI",
          "source_type": "REGULATORY_REGISTRY",
          "url": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doRecognisedFmr=yes&intmId=13&searchTerm=Rahul+Sharma",
          "retrieval": {
            "status": "NO_MATCH",
            "http_status": 200,
            "method": "SEBIAdapter",
            "mode": "FIXTURE"
          },
          "content": "SEBI RECOGNISED INTERMEDIARY DATABASE SEARCH RESULT\nQuery: 'rahul sharma'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND\nNotice: No entity or advisor matching 'rahul sharma' is registered in the official SEBI registry database."
        }
      ],
      "evidence_candidates": [
        {
          "evidence_id": "EVID-C9B6A974-001",
          "claim_id": "CLAIM-001",
          "source_document_id": "DOC-C9B6A974",
          "excerpt": "Query: 'rahul sharma'\nMatches Found: 0\nStatus: NO_RECORDS_FOUND",
          "relevance": {
            "matched_terms": ["registered"],
            "matched_entities": ["Rahul Sharma"],
            "matched_dates": []
          },
          "source_type": "REGULATORY_REGISTRY",
          "authority_tier": "PRIMARY_OFFICIAL",
          "verification_status": "UNVERIFIED"
        }
      ]
    },
    {
      "claim_id": "CLAIM-002",
      "source_plan": {
        "primary": ["sebi_public_regulatory_pages"],
        "fallback": ["rbi_regulatory_publications"],
        "required_source_types": ["REGULATOR", "STATUTORY_DOCUMENT"],
        "query": { "keywords": ["guaranteed returns prohibition", "investment advisers regulations"] }
      },
      "searches": [
        {
          "result_id": "SEBI-REG-001",
          "source_id": "sebi_public_regulatory_pages",
          "title": "SEBI (Investment Advisers) Regulations & Code of Conduct — Prohibition on Assured/Guaranteed Returns",
          "url": "https://www.sebi.gov.in/legal/circulars/sep-2020/guidelines-for-investment-advisers_47640.html"
        }
      ],
      "documents": [
        {
          "document_id": "DOC-72D984FA",
          "organization": "SEBI",
          "source_type": "REGULATOR",
          "url": "https://www.sebi.gov.in/legal/circulars/sep-2020/guidelines-for-investment-advisers_47640.html",
          "retrieval": {
            "status": "SUCCESS",
            "http_status": 200,
            "method": "SEBIAdapter",
            "mode": "FIXTURE"
          },
          "content": "Securities and Exchange Board of India (Investment Advisers) Regulations, 2013 [Third Schedule - Code of Conduct]:\nProhibition on Assured / Guaranteed Returns: No registered Investment Adviser, Research Analyst, or intermediary shall assure, promise, or guarantee any fixed, risk-free, or predetermined percentage of returns on investments in the securities market."
        }
      ],
      "evidence_candidates": [
        {
          "evidence_id": "EVID-72D984FA-001",
          "claim_id": "CLAIM-002",
          "source_document_id": "DOC-72D984FA",
          "excerpt": "Prohibition on Assured / Guaranteed Returns: No registered Investment Adviser, Research Analyst, or intermediary shall assure, promise, or guarantee any fixed, risk-free, or predetermined percentage of returns on investments in the securities market.",
          "relevance": {
            "matched_terms": ["40% returns"],
            "matched_entities": [],
            "matched_dates": []
          },
          "source_type": "REGULATOR",
          "authority_tier": "PRIMARY_OFFICIAL",
          "verification_status": "UNVERIFIED"
        }
      ]
    }
  ],
  "analysis_metadata": {
    "claims_processed": 2,
    "sources_queried": 2,
    "documents_retrieved": 2,
    "evidence_candidates_count": 2,
    "retrieval_failures": 0,
    "cache_hits": 0,
    "processing_time_ms": 4.12
  }
}
```

### Engine 5 (EvidenceAnalysis):
```json
{
  "content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
  "verifications": [
    {
      "claim_id": "CLAIM-001",
      "status": "INSUFFICIENT_EVIDENCE",
      "confidence": 0.95,
      "evidence_strength": "LOW",
      "supporting_evidence": [],
      "contradicting_evidence": [],
      "missing_elements": [
        "Official SEBI Registration Certificate or active registry listing under 'Rahul Sharma'"
      ],
      "context_gaps": [],
      "source_assessment": [
        {
          "source_id": "sebi_recognised_intermediaries",
          "organization": "SEBI",
          "authority_tier": "PRIMARY_OFFICIAL",
          "retrieval_status": "NO_MATCH",
          "relevance_summary": "Retrieved document 'SEBI Recognized Intermediary Registry Search: Rahul Sharma' with status NO_MATCH"
        }
      ],
      "reasoning_trace": [
        "1. Claim asserts: 'Rahul Sharma' -> 'REGISTERED_WITH' -> 'SEBI'",
        "2. Consulted official SEBI Recognized Intermediary Registry",
        "3. Official SEBI database returned 0 matching records for intermediary/advisor name 'Rahul Sharma'",
        "4. Absence of matching registry record does not establish registration; per evidence standards, recorded as INSUFFICIENT_EVIDENCE (not assumed false)."
      ],
      "uncertainty": [
        "Advisor may operate under an unstated corporate/LLP registered trade name rather than individual personal name"
      ],
      "provenance": {
        "engine_version": "5.0.0",
        "verification_method": "RULE_BASED",
        "verified_at": "2026-10-02T16:00:00Z"
      }
    },
    {
      "claim_id": "CLAIM-002",
      "status": "INSUFFICIENT_EVIDENCE",
      "confidence": 0.95,
      "evidence_strength": "HIGH",
      "supporting_evidence": [],
      "contradicting_evidence": [],
      "regulatory_findings": [
        {
          "type": "REGULATORY_CONFLICT",
          "source_document_id": "DOC-72D984FA",
          "source_url": "https://www.sebi.gov.in/legal/circulars/sep-2020/guidelines-for-investment-advisers_47640.html",
          "organization": "REGULATOR",
          "excerpt": "Prohibition on Assured / Guaranteed Returns: No registered Investment Adviser, Research Analyst, or intermediary shall assure, promise, or guarantee any fixed, risk-free, or predetermined percentage of returns on investments in the securities market.",
          "retrieved_at": "2026-10-02T12:00:00Z",
          "description": "Securities market regulations (SEBI Code of Conduct) strictly prohibit intermediaries from assuring or guaranteeing fixed, risk-free, or predetermined returns. The described guarantee conflicts with this applicable regulatory prohibition."
        }
      ],
      "missing_elements": [
        "Direct factual evidence establishing whether the financial return was actually guaranteed, paid, or delivered"
      ],
      "context_gaps": [],
      "source_assessment": [
        {
          "source_id": "sebi_public_regulatory_pages",
          "organization": "SEBI",
          "authority_tier": "PRIMARY_OFFICIAL",
          "retrieval_status": "SUCCESS",
          "relevance_summary": "Retrieved document 'SEBI (Investment Advisers) Regulations & Code of Conduct — Prohibition on Assured/Guaranteed Returns' with status SUCCESS"
        }
      ],
      "reasoning_trace": [
        "1. Claim asserts: guaranteed return of '40% returns'",
        "2. Consulted SEBI statutory code of conduct and regulations",
        "3. SEBI regulations state: 'Prohibition on Assured / Guaranteed Returns: No registered Investment Adviser, Research Analyst, or intermediary shall assure, promise, or guarantee any fixed, risk-free, or predetermined percentage of returns...'",
        "4. Regulatory finding: REGULATORY_CONFLICT recorded against statutory regulations.",
        "5. Distinction preserved: The retrieved regulation establishes that guaranteed returns are prohibited for covered entities; it does not independently establish whether the claimant factually promised or paid such returns. Status recorded as INSUFFICIENT_EVIDENCE with REGULATORY_CONFLICT (not factual contradiction)."
      ],
      "uncertainty": [
        "The retrieved regulation prohibits the described guarantee for covered entities; it does not independently establish whether the person/content actually made the claim"
      ],
      "provenance": {
        "engine_version": "5.0.0",
        "verification_method": "RULE_BASED",
        "verified_at": "2026-10-02T16:00:00Z"
      }
    }
  ],
  "analysis_metadata": {
    "total_claims_evaluated": 2,
    "supported_count": 0,
    "partially_supported_count": 0,
    "contradicted_count": 0,
    "insufficient_evidence_count": 2,
    "not_verifiable_count": 0,
    "source_conflicts_count": 0,
    "processing_time_ms": 2.85
  }
}
```

---

## 7. API Endpoints

Start the server:
```bash
uvicorn nivesh.api.app:app --host 0.0.0.0 --port 8000
```

1. **`GET /health`** / **`GET /api/v1/health`**:
   Returns system status and active engines (`content_intelligence`, `claim_intelligence`, `action_intelligence`, `source_intelligence`, `evidence_verification`).
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
5. **`POST /api/v1/sources/analyze`** (Engine 4):
   - Body: `{"content": NormalizedContent, "claims": ClaimAnalysis, "actions": ActionAnalysis (optional)}` or directly `NormalizedContent`
   - Output: `SourceAnalysis`
6. **`POST /api/v1/evidence/verify`** (Engine 5):
   - Body: `{"content": NormalizedContent, "claims": ClaimAnalysis, "sources": SourceAnalysis}`
   - Output: `EvidenceAnalysis`

---

## 8. Direct Python Service Interface

```python
from nivesh import (
    ContentIntelligenceEngine,
    ClaimIntelligenceEngine,
    ActionIntelligenceEngine,
    SourceIntelligenceEngine,
    EvidenceVerificationEngine,
)

# Initialize engines
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()
actions_engine = ActionIntelligenceEngine()
sources_engine = SourceIntelligenceEngine()
evidence_engine = EvidenceVerificationEngine()

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

# Step 4: Engine 4 (Where is authoritative info & what was retrieved?)
sources = sources_engine.discover_and_retrieve(normalized, claims, actions)

# Step 5: Engine 5 (What does the retrieved evidence actually establish?)
evidence = evidence_engine.verify(normalized, claims, sources)

print(f"Content ID: {normalized.content_id}")
print(f"Claims Evaluated: {evidence.analysis_metadata.total_claims_evaluated}")

for verification in evidence.verifications:
    print(f"\n[Verification for {verification.claim_id}]")
    print(f"  Status: {verification.status}")
    print(f"  Confidence: {verification.confidence} | Evidence Strength: {verification.evidence_strength}")
    print(f"  Trace: {' -> '.join(verification.reasoning_trace[:2])}")
    if verification.supporting_evidence:
        print(f"  Supporting Citations: {[e.source_url for e in verification.supporting_evidence]}")
    if verification.contradicting_evidence:
        print(f"  Contradicting Citations: {[e.source_url for e in verification.contradicting_evidence]}")
    if verification.missing_elements:
        print(f"  Missing Elements: {verification.missing_elements}")
```

---

## 9. Test Suite Verification

Run all pytest unit and integration tests:

```bash
python -X utf8 -m pytest -v
```

**Results:** `203 passed in 7.98s` (0 failed, 100% pass rate).
- **Engine 1 Unit Tests**: Text normalizer (7), URL extractor (8), Social extractor (6), Contact extractor (4), Financial extractor (6), Entity extractor (5), CTA extractor (7), Language detector (4), Financial relevance (4), OCR adapter (6), URL adapter (3), Primary fixture (3), API (4) -> **67 tests**.
- **Engine 2 Unit Tests**: Claim canonicalizer (7), Modality and Temporal (8), Claim segmenter & Action filtering (5), Verification requirements & Relations (5), Benchmark cases (7), Primary fixture (1), Engine 1 -> Engine 2 integration (3), Claim API (3), Correction tests (5) -> **44 tests**.
- **Engine 3 Unit Tests**: Schemas & validation (3), Classifier & hierarchy (3), Parameter extractor & privacy (4), Benchmark cases (6), Primary fixture benchmark (2), Engine 1 -> Engine 2 -> Engine 3 integration (2), Action API (2) -> **22 tests**.
- **Engine 4 Unit Tests**: Schemas & validation (4), SSRF protection (20), Source routing (4), Adapters & caching (7), Evidence candidates (1), Primary fixture (1), Full 4-engine integration (1), Source API (3), Correction & boundaries -> **45 tests**.
- **Engine 5 Unit Tests**: Schemas & validation (2), Regulatory & identity matching (6), Numerical, ratios, & debt verification (6), Opinions & predictions (2), Source conflicts & absence handling (3), Prompt injection defense (1), Primary fixture benchmark (1), Full 5-engine end-to-end integration (1), Evidence API (3) -> **25 tests**.

