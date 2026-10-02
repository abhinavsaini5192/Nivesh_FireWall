# Nivesh Firewall — Backend Core

Production-quality implementations of **Engine 1 (Content Intelligence)**, **Engine 2 (Claim Intelligence)**, **Engine 3 (Action Intelligence)**, **Engine 4 (Source Intelligence)**, **Engine 5 (Evidence Verification)**, **Engine 6 (Threat & Attack-Path Intelligence)**, **Engine 7 (Scam Fingerprint & Collective Threat Intelligence)**, **Engine 8 (Policy & Intervention Engine)**, **Engine 9 (Identity Verification & Entity Resolution Engine)**, and **Engine 10 (Behavioural Signal Intelligence Engine)** for the **Nivesh Firewall** backend.

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
       │                  downstream intelligence                │
       └─────────────────────────────────────────────────────────┘
          ↓                          ↓                         ↓
┌───────────────────────┐  ┌───────────────────┐  ┌─────────────────────────┐
│ ENGINE 6: Threat Intel│  │ ENGINE 7: Fingerpr│  │ ENGINE 9: Identity Verif│
└───────────────────────┘  └───────────────────┘  └─────────────────────────┘
          \                          │                         /
           \                         │                        /
            ↓                        ↓                       ↓
┌───────────────────────────────────────────────────────────────────────────┐
│ ENGINE 10: Behavioural Signal Intelligence Engine                         │
└───────────────────────────────────────────────────────────────────────────┘
          │ (Answers: "What behavioural pattern is emerging across this interaction sequence?")
          ▼
     BehaviouralAnalysis (BehaviouralSignal[], BehaviouralFinding[], BehaviouralPolicyHints)
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ ENGINE 8: Policy & Intervention Engine                  │
└─────────────────────────────────────────────────────────┘
          │ (Answers: "Given threat, fingerprint, identity, and behavioural findings, what safety intervention applies?")
          ▼
     PolicyDecision (ALLOW | INFORM | WARN | PAUSE | BLOCK)
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│ Browser / Desktop Local Enforcement Adapter             │
└─────────────────────────────────────────────────────────┘
```

> [!IMPORTANT]
> **Strict Separation of Responsibilities**:
> - **Engine 1** normalizes text, extracts multi-modal signals, and preserves 100% provenance without risk scoring.
> - **Engine 2** structures claims into atomic Subject-Predicate-Object canonical claims with modality, temporal context, fingerprint inputs, and verification requirements.
> - **Engine 3** structures requested user actions into canonical actions with action types, progression hierarchy, targets, parameters, sequence, modality, and rationale claim linkage.
> - **Engine 4** routes claims to authoritative source taxonomies, queries official registries/filings (SEBI, NSE, etc.), normalizes retrieved documents, and generates structured evidence candidates with full provenance while keeping verification status strictly `UNVERIFIED`.
> - **Engine 5** evaluates claim-level evidence relationships (`SUPPORTED`, `PARTIALLY_SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `NOT_VERIFIABLE`, `SOURCE_CONFLICT`), strictly separating source retrieval status from claim truth, and distinguishing absence of evidence from falsity.
> - **Engine 6** constructs structured attack paths, identifies threat stages & transitions, links claims to actions (`RATIONALE_FOR`, `JUSTIFIES`), surfaces evidence weaknesses, evaluates high-impact actions with reversibility ratings, and detects multi-signal combinations without predicting prices or calculating generic scam probabilities.
> - **Engine 7** creates privacy-preserving structural scam fingerprints, normalizes threat patterns across multiple observations, detects exact and semantic variants, maintains observation counts with copy-amplification protection, and provides collective intelligence without storing raw PII, declaring criminality, or predicting scam probability.
> - **Engine 8** evaluates multi-engine structured intelligence against explicit, deterministic policy rules and precedence hierarchies to emit intervention decisions (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`) with machine-readable reason codes, non-accusatory user explanations, and zero PII or investment advice.
> - **Engine 9** resolves entity identities, normalizes organization and person names without over-aggressive merging, verifies registration credentials against official databases, evaluates domain lookalikes vs official domains, validates regulatory authority claims vs actual records, and assesses social handles without assuming ownership—producing structured findings and identity resolution confidence without declaring criminality or fraud.
> - **Engine 10** identifies emerging behavioural and sequence patterns (time pressure, FOMO urgency, progressive commitment, rapid action escalation, retry after decline, channel migration, information-to-transaction shift) across interaction sequences without making psychological inferences, judging user character, declaring scam probabilities, or issuing policy interventions.
> - **Engines 1 through 10 NEVER** recommend buying/selling/holding investments, predict future market outcomes, calculate general "scam probabilities" (e.g. 0.94), declare individuals criminals, or directly manipulate the host OS/browser (device-level enforcement is delegated to downstream adapters).



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

## 6. Engine 6: Threat & Attack-Path Intelligence Engine

Constructs an auditable, structured **attack path** connecting claims, requested actions, identity signals, and evidence verification findings into an explainable threat model (`ThreatAnalysis`).

Engine 6 answers:
> *"How do the claims, requested actions, identity signals, and evidence relationships combine into a potentially harmful financial interaction?"*

It does NOT simply ask "Is this a scam?", but systematically models:
```
CLAIM ──▶ TRUST / JUSTIFICATION ──▶ ACTION ──▶ NEXT ACTION ──▶ POTENTIAL HARM TRANSITION
```

### Capabilities
1. **Threat Signal Detection (`ThreatSignalDetector`)**:
   - Detects 15+ structured, auditable signals with explicit provenance (`content`, `claim`, `action`, `source_verification`, `evidence_verification`, `fingerprint_database`, `combination`).
   - Signal types include: `AUTHORITY_IMPERSONATION`, `IDENTITY_NOT_ESTABLISHED`, `IDENTITY_MISMATCH`, `UNSUPPORTED_CLAIM`, `REGULATORY_CONFLICT`, `GUARANTEED_RETURN_LANGUAGE`, `URGENCY`, `FOMO`, `PRIVATE_CHANNEL_MIGRATION`, `EXTERNAL_DOMAIN`, `LOOKALIKE_DOMAIN`, `EXTERNAL_APP`, `CREDENTIAL_REQUEST`, `IDENTITY_DOCUMENT_REQUEST`, `ACCOUNT_ACCESS_REQUEST`, `PAYMENT_REQUEST`, `UPFRONT_FEE`, `OTP_REQUEST`, `ISOLATION_LANGUAGE`, `SECRECY_REQUEST`.
   - Never infers malicious intent solely from a single weak signal.
2. **Attack Path Modeling (`AttackPathBuilder`)**:
   - Models interactions as ordered graph sequences across a normalized 10-stage taxonomy:
     `DISCOVERY` ➔ `TRUST_BUILDING` ➔ `CHANNEL_MIGRATION` ➔ `NAVIGATION` ➔ `SOFTWARE_INSTALLATION` ➔ `DATA_COLLECTION` ➔ `CREDENTIAL_CAPTURE` ➔ `ACCOUNT_ACCESS` ➔ `FINANCIAL_REQUEST` ➔ `FINANCIAL_TRANSFER`.
   - Captures stage transitions with supporting actions, supporting claims, and transition confidence.
3. **Claim ➔ Action Semantic Linking (`ClaimActionLinker`)**:
   - Identifies how claims justify or serve as rationale for actions (`RATIONALE_FOR`, `JUSTIFIES`, `ENABLES`, `PRECEDES`, `LEADS_TO`, `REQUESTS`).
4. **High-Impact Action & Evidence Weakness Evaluation (`ImpactEvaluator`)**:
   - Evaluates high-consequence actions by impact category (`CREDENTIAL`, `IDENTITY`, `DEVICE`, `FINANCIAL`) and reversibility (`REVERSIBLE`, `DIFFICULT_TO_REVERSE`, `IRREVERSIBLE`).
   - Translates Engine 5 verification outcomes into structured evidentiary limits without legal overclaiming (`IDENTITY_NOT_ESTABLISHED`, `REGULATORY_CONFLICT`).
5. **Multi-Signal Combination Logic (`CombinationEngine`)**:
   - Combines independently observable signals into structured mechanisms (`unsubstantiated_regulatory_authority`, `trust_migration_to_payment_transition`, `external_app_monetary_solicitation`, `private_channel_credential_harvesting`).
   - Maps observed structures into recognized threat families: `IDENTITY_IMPERSONATION`, `INVESTMENT_PROMOTION_SCAM`, `CREDENTIAL_HARVESTING`, `PAYMENT_FRAUD`, `MALICIOUS_SOFTWARE`, `ACCOUNT_TAKEOVER`, `REGULATORY_IMPERSONATION`, `SOCIAL_ENGINEERING`.
   - Strict negative guardrails prevent false escalation on weak signals alone (e.g. Telegram alone, research recommendations alone, regulatory circular mentions alone, isolated course fees).
6. **Non-Accusatory Structural Explanation (`ThreatExplainer`)**:
   - Synthesizes auditable structural narratives and lists explicit uncertainties (e.g. absence of registry records establishes lack of public verification, not legal proof of fraud).
   - Generates normalized components ready for Engine 7 Scam Fingerprinting (`normalized_claim_patterns`, `normalized_action_patterns`, `normalized_identity_patterns`, `normalized_channel_patterns`, `normalized_threat_families`, `normalized_attack_stages`, `normalized_transitions`).

---

## 7. Benchmark Fixture Execution

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

### Engine 6 (ThreatAnalysis):
```json
{
  "content_id": "b68255d2-133f-4bcc-8625-fa5ab0cdc5ca",
  "threat_signals": [
    {
      "signal_id": "SIG-001",
      "type": "REGULATORY_AUTHORITY_CLAIM",
      "source": "claim",
      "evidence": "Claim 'Rahul Sharma' asserts registration/licensing with 'SEBI'",
      "confidence": 0.9,
      "description": "Content asserts regulatory authority by stating association with SEBI.",
      "claim_id": "CLAIM-001"
    },
    {
      "signal_id": "SIG-002",
      "type": "IDENTITY_NOT_ESTABLISHED",
      "source": "evidence_verification",
      "evidence": "Official registry verification for 'Rahul Sharma' returned status 'INSUFFICIENT_EVIDENCE'",
      "confidence": 0.95,
      "description": "Claimed regulatory authority for 'Rahul Sharma' was not established by official database records.",
      "claim_id": "CLAIM-001"
    },
    {
      "signal_id": "SIG-003",
      "type": "GUARANTEED_RETURN_LANGUAGE",
      "source": "claim",
      "evidence": "Claim asserts guaranteed return: '40% returns'",
      "confidence": 0.95,
      "description": "Content uses deterministic guaranteed return promises, an anomalous risk factor in securities markets.",
      "claim_id": "CLAIM-002"
    },
    {
      "signal_id": "SIG-004",
      "type": "REGULATORY_CLAIM_CONFLICT",
      "source": "evidence_verification",
      "evidence": "SEBI Code of Conduct prohibits intermediaries from assuring returns",
      "confidence": 0.9,
      "description": "The guaranteed return promise directly conflicts with applicable statutory regulations prohibiting assured returns.",
      "claim_id": "CLAIM-002"
    },
    {
      "signal_id": "SIG-005",
      "type": "PRIVATE_CHANNEL_MIGRATION",
      "source": "action",
      "evidence": "Action requests joining private communication channel: 'Telegram'",
      "confidence": 0.92,
      "description": "Interaction encourages moving communication to private, encrypted messaging platforms (e.g. Telegram/WhatsApp).",
      "action_id": "ACTION-001"
    },
    {
      "signal_id": "SIG-006",
      "type": "EXTERNAL_APP",
      "source": "action",
      "evidence": "Action solicits download of external app/APK: 'app'",
      "confidence": 0.88,
      "description": "Interaction requests installation or downloading of external software outside standard public directories.",
      "action_id": "ACTION-002"
    },
    {
      "signal_id": "SIG-007",
      "type": "PAYMENT_REQUEST",
      "source": "action",
      "evidence": "Action requests monetary payment/transfer: 'INR 5000.0'",
      "confidence": 0.94,
      "description": "Interaction solicits direct monetary payments or financial account transfers.",
      "action_id": "ACTION-003"
    },
    {
      "signal_id": "SIG-008",
      "type": "FOMO",
      "source": "content",
      "evidence": "Text leverages FOMO cues: ['vip']",
      "confidence": 0.78,
      "description": "Content utilizes exclusive opportunity language to induce fear of missing out."
    }
  ],
  "attack_path": {
    "nodes": [
      { "node_id": "NODE-01", "stage": "DISCOVERY", "type": "financial_content_ingestion", "label": "Content Discovery & Initial Exposure" },
      { "node_id": "NODE-02", "stage": "TRUST_BUILDING", "type": "trust_building_stage", "label": "Regulatory Authority & Return Guarantee Claims", "linked_claim_ids": ["CLAIM-001", "CLAIM-002"] },
      { "node_id": "NODE-03", "stage": "CHANNEL_MIGRATION", "type": "channel_migration_stage", "label": "Migration to Private Channel", "linked_action_ids": ["ACTION-001"] },
      { "node_id": "NODE-04", "stage": "SOFTWARE_INSTALLATION", "type": "software_installation_stage", "label": "Installation of External Application", "linked_action_ids": ["ACTION-002"] },
      { "node_id": "NODE-05", "stage": "FINANCIAL_REQUEST", "type": "financial_request_stage", "label": "Direct Financial Solicitations", "linked_action_ids": ["ACTION-003"] }
    ],
    "transitions": [
      { "from_stage": "TRUST_BUILDING", "to_stage": "CHANNEL_MIGRATION", "confidence": 0.88 },
      { "from_stage": "CHANNEL_MIGRATION", "to_stage": "SOFTWARE_INSTALLATION", "confidence": 0.88 },
      { "from_stage": "SOFTWARE_INSTALLATION", "to_stage": "FINANCIAL_REQUEST", "confidence": 0.88 }
    ],
    "entry_stage": "TRUST_BUILDING",
    "terminal_stage": "FINANCIAL_REQUEST"
  },
  "claim_action_links": [],
  "evidence_weaknesses": [
    { "weakness_id": "EW-001", "claim_id": "CLAIM-001", "weakness_type": "IDENTITY_NOT_ESTABLISHED", "evidence_status": "INSUFFICIENT_EVIDENCE", "severity": "HIGH" },
    { "weakness_id": "EW-002", "claim_id": "CLAIM-002", "weakness_type": "REGULATORY_CONFLICT", "evidence_status": "INSUFFICIENT_EVIDENCE", "severity": "HIGH" }
  ],
  "high_impact_actions": [
    { "action_id": "ACTION-002", "action_type": "DOWNLOAD", "impact_category": "DEVICE", "reversibility": "DIFFICULT_TO_REVERSE" },
    { "action_id": "ACTION-003", "action_type": "PAYMENT", "impact_category": "FINANCIAL", "reversibility": "IRREVERSIBLE" }
  ],
  "threat_families": [
    "INVESTMENT_PROMOTION_SCAM",
    "MALICIOUS_SOFTWARE",
    "PAYMENT_FRAUD",
    "SOCIAL_ENGINEERING"
  ],
  "fingerprint_prep": {
    "normalized_claim_patterns": ["claim:regulatory:registered_with:sebi", "claim:financial:guaranteed_return:40% returns"],
    "normalized_action_patterns": ["action:join_channel:https://t.me/rahulinvest", "action:download:app", "action:payment:unknown"],
    "normalized_identity_patterns": ["identity:person:rahul sharma", "identity:regulator:securities and exchange board of india"],
    "normalized_channel_patterns": ["channel:telegram:rahulinvest"],
    "normalized_attack_stages": ["TRUST_BUILDING", "CHANNEL_MIGRATION", "SOFTWARE_INSTALLATION", "FINANCIAL_REQUEST"],
    "normalized_transitions": ["TRUST_BUILDING->CHANNEL_MIGRATION", "CHANNEL_MIGRATION->SOFTWARE_INSTALLATION", "SOFTWARE_INSTALLATION->FINANCIAL_REQUEST"]
  },
  "explanation": {
    "summary": "Observed interaction follows an attack path through 4 active stages: [TRUST_BUILDING ➔ CHANNEL_MIGRATION ➔ SOFTWARE_INSTALLATION ➔ FINANCIAL_REQUEST]. Regulatory authority claims were not substantiated by official public registry records. Financial promises conflict directly with statutory regulatory prohibitions.",
    "mechanisms": ["trust_migration_to_payment_transition", "prohibited_return_app_distribution", "unsubstantiated_regulatory_authority", "external_app_monetary_solicitation"]
  },
  "uncertainty": [
    "Analysis describes observed behavioral and structural patterns, not a legal adjudication of criminality.",
    "Actual intent of the content creator cannot be verified from published text and public records alone.",
    "Absence of matching registry records establishes lack of public verification, but does not definitively prove fraud."
  ],
  "confidence": 0.90
}
```

---

## 7. Engine 7: Scam Fingerprint & Collective Threat Intelligence Engine

Creates and manages **privacy-preserving scam fingerprints** across multi-user observations.

### Fundamental Question
> **"Have we previously observed this underlying financial threat pattern, and which structural characteristics make the current observation similar?"**

### Core Architectural Principle
A scammer may change the URL, handle, domain, or monetary amount (e.g. ₹5,000 ↔ ₹4,999, Telegram ↔ WhatsApp). Engine 7 abstracts superficial variations into **invariant structural dimensions** rather than hashing raw messages (`SHA256(raw_text)`).

```
Observation A (Telegram + SEBI + Guaranteed 40% + App + ₹5,000)
       \
        \
         → STRUCTURAL / SEMANTIC VARIANT MATCH (Confidence 0.91)
        /
Observation B (WhatsApp + SEBI + Assured 40% + App + ₹4,999)
       ↓
Shared Threat Family / Structural Fingerprint (SFP-001, count = 2)
```

### Capabilities & Safeguards
1. **Multi-Dimensional Normalized Features**:
   - `identity_patterns`: Canonical regulatory authority assertions (`IDENTITY:REGULATORY_AUTHORITY_CLAIM`, `IDENTITY:NOT_ESTABLISHED`)
   - `claim_patterns`: Canonical claims (`CLAIM:GUARANTEED_RETURN`, `CLAIM:REGULATORY_REGISTRATION`)
   - `action_patterns`: Canonical requested user actions (`ACTION:CHANNEL_MIGRATION`, `ACTION:SOFTWARE_INSTALLATION`, `ACTION:PAYMENT_REQUEST`)
   - `attack_stages` & `attack_transitions`: Interaction attack path progression
   - `threat_patterns` & `evidence_patterns`: Normalized regulatory conflict and unverified identity states
2. **Deterministic Canonical Signatures**:
   - `exact_signature`: SHA-256 digest of strictly sorted canonical features for $O(1)$ exact matches.
   - `semantic_signature`: SHA-256 digest of invariant structural dimensions (omitting channel, lookalike domain, and exact rupee amount) for instantaneous variant detection.
   - `attack_path_signature`: Normalized stage transition chain (`TRUST_BUILDING>CHANNEL_MIGRATION>SOFTWARE_INSTALLATION>FINANCIAL_REQUEST`).
3. **Deterministic Single-Valued Match Hierarchy**:
   - Every match returns exactly **ONE** primary `match_type` enum value:
     - `EXACT_MATCH`: 100% identical canonical structure ($1.00$ confidence).
     - `STRUCTURAL_MATCH`: Same core attack path and threat mechanics with differing external channel or domain ($0.90$–$0.95$ confidence).
     - `SEMANTIC_VARIANT`: Equivalent threat structure with mutated wording, amounts, or channels ($0.85$–$0.92$ confidence). When wording, channel, domain, or amount changes while normalized threat structure remains equivalent, Engine 7 deterministically sets `match_type = "SEMANTIC_VARIANT"` and sets `structural_equivalence = True`.
     - `RELATED_PATTERN`: Shares threat family and partial attack path ($0.40$–$0.70$ confidence).
     - `NO_MATCH`: Unrelated or benign informational content ($0.00$ confidence).
4. **Copy-Amplification & Duplicate-Origin Defense**:
   - Tracks `content_hash` of normalized text (ignoring URL tracking parameters like `?ref=...`).
   - Copied forwards across different channels (e.g. Telegram to WhatsApp) are identified as `is_duplicate_origin = True` and do **not** increment independent `observation_count`.
   - Distinct channels are recorded in `distinct_channels` for metadata visibility without artificially inflating collective corroboration.
5. **Lifecycle & Dispute Management**:
   - States: `NEW` ➔ `ACTIVE` (promoted upon reaching 2+ independent observations) ➔ `STALE` (inactivity threshold) ➔ `ARCHIVED` / `DISPUTED`.
   - Disputes record notes and auditor provenance without silently deleting historical observations.
   - **Prototype Persistence Note**: For this hackathon prototype, an in-memory repository with thread-safe locking and indexing is implemented. Full persistence across process restarts (e.g., PostgreSQL with pgvector / Redis) is a production hardening item.
6. **Strict Privacy Preservation**:
   - Zero raw PII (names, phone numbers, email addresses, bank accounts, OTPs, PAN, Aadhaar) or raw message text in stored fingerprints, observations, or collective context.
   - User identities remain completely anonymous.
   - Downstream responses to other users disclose only normalized threat mechanics.

### Schema Example: `ScamFingerprint`
```json
{
  "fingerprint_id": "SFP-001",
  "schema_version": "1.0",
  "identity_patterns": [
    "IDENTITY:NOT_ESTABLISHED",
    "IDENTITY:REGULATOR:SEBI",
    "IDENTITY:REGULATORY_AUTHORITY_CLAIM"
  ],
  "claim_patterns": [
    "CLAIM:GUARANTEED_RETURN",
    "CLAIM:REGULATORY_REGISTRATION"
  ],
  "action_patterns": [
    "ACTION:CHANNEL_MIGRATION",
    "ACTION:PAYMENT_REQUEST",
    "ACTION:SOFTWARE_INSTALLATION"
  ],
  "channel_patterns": [
    "CHANNEL:TELEGRAM"
  ],
  "attack_stages": [
    "TRUST_BUILDING",
    "CHANNEL_MIGRATION",
    "SOFTWARE_INSTALLATION",
    "FINANCIAL_REQUEST"
  ],
  "attack_path_signature": "TRUST_BUILDING>CHANNEL_MIGRATION>SOFTWARE_INSTALLATION>FINANCIAL_REQUEST",
  "exact_signature": "0e6761ca783f982a...",
  "semantic_signature": "81f148e657cba31e...",
  "observation_count": 2,
  "distinct_channels": ["telegram", "whatsapp"],
  "distinct_variants": 2,
  "status": "ACTIVE"
}
```

---

## 8. Engine 8: Policy & Intervention Engine

Engine 8 is the **decision and safety support engine** of the Nivesh Firewall. It consumes the structured intelligence produced by Engines 1 through 7 and Engine 9 (Identity Verification) and determines the appropriate safety intervention before or during a user's potentially harmful financial action.

```
Engine 1 (Content) ──► Engine 2 (Claims) ──► Engine 3 (Actions)
       │                      │                      │
       ▼                      ▼                      ▼
Engine 4 (Sources) ──► Engine 5 (Evidence) ──► Engine 6 (Threats)
       │                                             │
       │                                             ▼
       │                                      Engine 7 (Fingerprints)
       │                                             │
       ▼                                             │
Engine 9 (Identity Resolution) ◄─────────────────────┘
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ ENGINE 8: Policy & Intervention                        │
│ - Explicit Rule Evaluator                              │
│ - Consumes ThreatAnalysis, SFP, and IdentityAnalysis   │
│ - Deterministic Precedence Resolver                    │
│ - Dual-Channel Explainability                          │
│ - Privacy-Preserving Audit Engine                      │
└────────────────────────────────────────────────────────┘
       │
       ▼
PolicyDecision
(ALLOW | INFORM | WARN | PAUSE | BLOCK)
       │
       ▼
Browser/Desktop Enforcement Adapter
```

### Core Architecture & Principles

1. **Strict Decision Boundary**:
   - Engine 8 answers: *"What safety response should be presented before or during the user's potentially harmful financial action?"*
   - Engine 8 **never** directly manipulates the host operating system, browser, network connections, payments, or files. It returns a typed `PolicyDecision` object for downstream client enforcement adapters.
   - Engine 8 **never** provides investment advice (no `BUY`, `SELL`, `HOLD`, `INVEST`, price targets, or return predictions).
   - Engine 8 **never** issues criminal or fraud accusations (no *"scammer detected"* or legal adjudication labels).

2. **Five Intervention Levels (`PolicyDecisionType`)**:
   - `ALLOW`: No meaningful threat indicators; content is informational or benign; no high-impact action is occurring. *(ALLOW does not mean a financial claim is factually true; it means the firewall has no policy reason to intervene).*
   - `INFORM`: Neutral contextual guidance for relevant financial topics, market opinions, or unverifiable forward-looking claims without high-impact actions.
   - `WARN`: Advisory notice when meaningful risk indicators exist (unverified regulatory status, guaranteed-return language, private channel migration) but immediate consequential action is not yet occurring.
   - `PAUSE`: Temporary interaction interruption requesting explicit user confirmation before high-impact or irreversible actions (payments, external software downloads, credential disclosures) linked to unverified authority or threat patterns.
   - `BLOCK`: Strongest protection intervention. Reserved strictly for critical high-impact actions combined with confirmed structural threat patterns or direct factual contradictions.

3. **Explicit Rule-Based Reasoning (No Black-Box 0–100 Scores)**:
   - Evaluates explicit, transparent boolean predicates across upstream outputs:
     - `RULE-BLOCK-01`: Critical Credential Access Request with Confirmed Threat Match.
     - `RULE-BLOCK-02`: Irreversible Payment Request with Factual Contradiction or Known Exploit.
     - `RULE-PAUSE-01`: Payment Request with Multi-Signal Threat Pattern (`PAYMENT` + unverified authority / guaranteed returns / threat match).
     - `RULE-PAUSE-02`: External Software Installation with Unverified Financial Context (`DOWNLOAD` / `INSTALL` + unverified claims).
     - `RULE-PAUSE-03`: Sensitive Data or Credential Request by Unverified Entity.
     - `RULE-WARN-01`: Private Channel Migration with Unverified Authority (`TELEGRAM` / `WHATSAPP` + unverified regulatory claim).
     - `RULE-WARN-02`: Guaranteed Return Language in Financial Promotion.
     - `RULE-WARN-03`: Unverified Regulatory Status Claim (`SEBI registered` with `NO_MATCH` in official registry).
     - `RULE-WARN-04`: Interaction Resembles Previously Observed Threat Structure (`SEMANTIC_VARIANT` / `STRUCTURAL_MATCH`).
     - `RULE-INFORM-01`: Market Opinion or Prediction Disclosure.
     - `RULE-INFORM-02`: General Financial Content Informational Context.
     - `RULE-ALLOW-01`: Benign Educational or Low-Risk Content Baseline.

4. **Deterministic Precedence Hierarchy**:
   $$\text{BLOCK} \succ \text{PAUSE} \succ \text{WARN} \succ \text{INFORM} \succ \text{ALLOW}$$
   - When multiple rules trigger, the highest severity decision wins deterministically.
   - All triggered reason codes and signals are aggregated and deduplicated.
   - If an optional `UserOverride` is supplied for a `PAUSE` decision, the decision is demoted to `WARN` with `USER_OVERRIDE_APPLIED` recorded in audit metadata. User overrides **cannot** bypass a `BLOCK` decision.

5. **Stable Machine-Readable Reason Codes (`ReasonCode`)**:
   - `NO_INTERVENTION_REQUIRED`, `FINANCIAL_CONTENT_DETECTED`, `UNVERIFIED_REGULATORY_CLAIM`, `IDENTITY_NOT_ESTABLISHED`, `REGULATORY_CONFLICT`, `INSUFFICIENT_EVIDENCE`, `SOURCE_UNAVAILABLE`, `SOURCE_CONFLICT`, `GUARANTEED_RETURN_LANGUAGE`, `PRIVATE_CHANNEL_MIGRATION`, `EXTERNAL_APP_INSTALLATION`, `CREDENTIAL_ACCESS_REQUEST`, `ACCOUNT_AUTHORIZATION_REQUEST`, `PAYMENT_REQUEST`, `HIGH_IMPACT_ACTION`, `KNOWN_THREAT_STRUCTURAL_MATCH`, `KNOWN_THREAT_SEMANTIC_VARIANT`, `KNOWN_THREAT_RELATED_PATTERN`, `MULTI_SIGNAL_THREAT_PATTERN`, `DANGEROUS_ACTION_SEQUENCE`, `IRREVERSIBLE_ACTION_DETECTED`, `USER_CONFIRMATION_REQUIRED`, `POLICY_ESCALATION`, `USER_OVERRIDE_APPLIED`, `OPINION_OR_PREDICTION_DISCLOSED`.

6. **Dual-Channel Neutral Explainability**:
   - `user_message`: Objective, non-accusatory guidance designed for non-technical users (e.g., *"Pause before continuing. This interaction combines an unverified financial identity claim, private channel migration, external software installation, and an irreversible payment request."*).
   - `technical_message`: Formatted, reproducible pipeline trace detailing rule IDs, decision, reason codes, triggered signals, and cooldown parameters.

7. **Privacy Preservation & Auditability**:
   - Policy decisions and audit metadata strictly redact and exclude passwords, OTPs, bank accounts, UPI PINs, and raw unscrubbed content.
   - Every decision is stamped with `decision_id`, immutable `created_at` timestamp, and centralized `policy_version` (`8.0.0`).

---

## 9. Engine 9: Identity Verification & Entity Resolution Engine

Engine 9 answers the core question:

> *"Does the identity, organization, regulator, intermediary, brand, domain, or other entity being represented in this financial interaction actually align with authoritative identity evidence?"*

The engine focuses strictly on **identity consistency and entity resolution**. It does not declare criminality or fraud, provide investment advice, or make final intervention decisions. It emits structured identity findings (`IdentityAnalysis`) that Engine 6, Engine 7, and Engine 8 consume.

```
ENTITY EXTRACTION INPUT
        ↓
ENTITY NORMALIZATION (Person names without aggressive merging, org legal suffixes, domains, handles)
        ↓
IDENTITY CANDIDATE RESOLUTION
        ↓
AUTHORITATIVE ENTITY MATCHING (Deterministic attribute-by-attribute comparison)
        ↓
IDENTITY ATTRIBUTE COMPARISON (Legal name, registration number, entity type, regulator, domain)
        ↓
DOMAIN / BRAND / AUTHORITY ALIGNMENT
        ↓
IDENTITY STATUS (ESTABLISHED | PARTIALLY_ESTABLISHED | NOT_ESTABLISHED | IDENTITY_MISMATCH | AMBIGUOUS | SOURCE_UNAVAILABLE)
        ↓
IDENTITY FINDINGS (Stable reason codes with complete source/evidence provenance)
```

### Core Responsibilities & Modules

1. **Entity Extraction & Disambiguation (`entity_resolver.py`)**:
   - Categorizes entities into typed taxonomy: `PERSON`, `ORGANIZATION`, `REGULATOR`, `FINANCIAL_INTERMEDIARY`, `BROKER`, `ADVISER`, `COMPANY`, `BRAND`, `WEBSITE`, `DOMAIN`, `SOCIAL_ACCOUNT`, `CHANNEL`.
   - Distinguishes contact points/channels/domains from person entities (e.g. `contact@example.com` or `@handle` is a contact point, never automatically a person).
   - Associates claimed registrations, domains, and social channels with primary claimed entities.

2. **Deterministic Normalization (`normalizer.py`)**:
   - **Person Names**: Strips honorifics/titles (`Dr.`, `CA`, `Mr.`), applies Unicode NFKC normalization, but strictly avoids over-aggressive merging (`Rahul Sharma` $\neq$ `Rahul K Sharma` $\neq$ `Rahul Kumar Sharma`).
   - **Organizations**: Standardizes legal suffixes (`PVT LTD`, `LLP`, `LTD`, `INC`) while preserving original legal representations for provenance.
   - **Domains**: Normalizes URLs, strips ports, paths, schemes, tracking query parameters (`utm_*`, `ref`), and handles two-part TLDs (`.co.in`, `.gov.in`).
   - **Registrations**: Normalizes alphanumeric registration identifiers (stripping whitespace, hyphens, slashes).
   - **Social Handles**: Standardizes handles across Telegram, WhatsApp, Twitter/X, Instagram, and YouTube.

3. **Registration Resolution (`registration_resolver.py`)**:
   - Connects claimed entity $\rightarrow$ registration identifier $\rightarrow$ authoritative candidate record.
   - Distinguishes:
     - `REGISTRATION_ENTITY_MATCH`: Registration exists and officially belongs to the claimed entity (`ESTABLISHED`).
     - `REGISTRATION_ENTITY_MISMATCH`: Registration exists but officially belongs to a *different* legal entity (`IDENTITY_MISMATCH`).
     - `REGISTRATION_IDENTIFIER_UNRESOLVED`: Registration claimed but identifier is missing or unverified (`NOT_ESTABLISHED`).
     - Registry search `NO_MATCH` $\rightarrow$ `NOT_ESTABLISHED` (strictly **never** `IDENTITY_MISMATCH` or fraud).
     - Source unavailable $\rightarrow$ `SOURCE_UNAVAILABLE`.

4. **Domain and Brand Alignment (`domain_resolver.py`)**:
   - Compares observed domains against claimed brands and authoritative registry records.
   - Evaluates:
     - `ALIGNED` / `DOMAIN_ALIGNMENT_ESTABLISHED`: Observed domain matches official registry record.
     - `MISMATCH` / `DOMAIN_IDENTITY_MISMATCH`: Authoritative domain is known, but observed domain is a lookalike or different domain.
     - `NOT_ESTABLISHED` / `DOMAIN_ALIGNMENT_NOT_ESTABLISHED`: Domain unverified in records (unknown domain $\neq$ malicious domain; brand keyword in domain $\neq$ official ownership).

5. **Authority Identity Resolution (`authority_resolver.py`)**:
   - Handles regulatory authorities (SEBI, RBI, NSE, BSE, IRDAI, PFRDA).
   - Distinguishes:
     - `AUTHORITY_CLAIM`: Content makes an explicit regulatory reference.
     - `AUTHORITY_IDENTITY_NOT_ESTABLISHED`: Asserted registration cannot be established in registry records.
     - `AUTHORITY_IDENTITY_MISMATCH`: Authoritative records contradict registration details, or interaction improperly purports to be the regulator itself.

6. **Social Channel Resolution (`social_resolver.py`)**:
   - Evaluates Telegram groups, WhatsApp channels, Twitter handles, etc.
   - Enforces the core rule: **A matching username or handle does NOT establish official ownership without authoritative evidence** (`SOCIAL_ACCOUNT_NOT_ESTABLISHED`).

7. **Deterministic Attribute Matcher (`matcher.py`)**:
   - Compares legal name, registration number, entity type, regulator, domain, and jurisdiction.
   - Detects ambiguity (`AMBIGUOUS`) when multiple candidates match without distinguishing data (does not arbitrarily choose one).

8. **Findings & Traceability (`findings.py`, `provenance.py`)**:
   - Generates structured, non-accusatory `IdentityFinding` objects with complete upstream provenance links (`source_ids`, `evidence_ids`, `claim_id`, `entity_id`).
   - Confidence represents **identity resolution confidence** (0.0 to 1.0), strictly **not** scam probability.

---

## 10. API Endpoints

Start the FastAPI server:
```bash
uvicorn nivesh.api.app:app --host 0.0.0.0 --port 8000
```

1. **`GET /health`** / **`GET /api/v1/health`**:
   Returns system status and all 9 active engines.
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
   - Body: `{"content": NormalizedContent, "claims": ClaimAnalysis, "sources": SourceAnalysis}` or directly `NormalizedContent`
   - Output: `EvidenceAnalysis`
7. **`POST /api/v1/threat/analyze`** (Engine 6):
   - Body: `{"content": NormalizedContent, "claims": ClaimAnalysis, "actions": ActionAnalysis, "sources": SourceAnalysis, "evidence": EvidenceAnalysis}` or directly `NormalizedContent` (with auto-cascading pipeline execution)
   - Output: `ThreatAnalysis`
8. **`POST /api/v1/fingerprints/match`** (Engine 7):
   - Body: Full payload or `NormalizedContent` (with auto-cascading execution through Engine 6)
   - Output: `FingerprintAnalysis`
9. **`POST /api/v1/fingerprints/create`** (Engine 7):
   - Body: Direct `ScamFingerprint` or content payload
   - Output: `ScamFingerprint`
10. **`GET /api/v1/fingerprints/{fingerprint_id}`** (Engine 7):
    - Output: `ScamFingerprint`
11. **`GET /api/v1/fingerprints/search`** (Engine 7):
    - Params: `query`, `status`, `threat_family`, `channel`
    - Output: `list[ScamFingerprint]`
12. **`POST /api/v1/fingerprints/{fingerprint_id}/dispute`** (Engine 7):
    - Body: `{"reason": "...", "actor": "compliance_officer"}`
    - Output: `ScamFingerprint` with `status="DISPUTED"`
13. **`POST /api/v1/policy/decide`** (Engine 8):
    - Body: Multi-engine structured outputs or `NormalizedContent` (with auto-cascading pipeline execution)
    - Output: `PolicyDecision` (with `decision`, `severity`, `reason_codes`, `user_message`, `technical_message`, `required_user_confirmation`, `cooldown_seconds`)
14. **`GET /api/v1/policy/rules`** (Engine 8):
    - Output: `list[dict]` of all active policy rules, scopes, and target decisions.
15. **`GET /api/v1/policy/{decision_id}`** (Engine 8):
    - Output: Stored `PolicyDecision` record.
16. **`POST /api/v1/policy/explain`** (Engine 8):
    - Body: `PolicyDecision` JSON
    - Output: `{"decision_id": "...", "decision": "PAUSE", "user_message": "...", "technical_message": "...", "reason_codes": [...]}`
17. **`POST /api/v1/identity/verify`** (Engine 9):
    - Body: `{"text": "..."}` or `{"content": NormalizedContent, "claims": ClaimAnalysis, "sources": SourceAnalysis, "evidence": EvidenceAnalysis}`
    - Output: `IdentityAnalysis` (with `entities`, `identity_matches`, `identity_findings`, `identity_status`, `authority_alignments`, `domain_alignments`, `confidence`, `provenance`)
18. **`GET /api/v1/identity/{analysis_id}`** (Engine 9):
    - Output: Stored `IdentityAnalysis` record.
19. **`GET /api/v1/identity/entities/{entity_id}`** (Engine 9):
    - Output: Stored `ClaimedEntity` record.

---

## 11. Direct Python Service Interface

```python
from nivesh import (
    ContentIntelligenceEngine,
    ClaimIntelligenceEngine,
    ActionIntelligenceEngine,
    SourceIntelligenceEngine,
    EvidenceVerificationEngine,
    ThreatIntelligenceEngine,
    ScamFingerprintEngine,
    PolicyInterventionEngine,
    IdentityVerificationEngine,
    PolicyDecisionType,
    IdentityStatus,
)

# Initialize all 9 engines
content_engine = ContentIntelligenceEngine()
claims_engine = ClaimIntelligenceEngine()
actions_engine = ActionIntelligenceEngine()
sources_engine = SourceIntelligenceEngine(default_mode="FIXTURE")
evidence_engine = EvidenceVerificationEngine()
threat_engine = ThreatIntelligenceEngine()
fingerprint_engine = ScamFingerprintEngine()
policy_engine = PolicyInterventionEngine()
identity_engine = IdentityVerificationEngine()

# Observation 1: Standard benchmark threat
raw_text_1 = (
    "🚨 SEBI registered advisor Rahul Sharma! Guaranteed 40% returns. "
    "Join our Telegram VIP group: https://t.me/rahulinvest. "
    "Download our app and pay ₹5,000."
)

# Process Observation 1 through Engines 1-7
c1 = content_engine.process_text(raw_text_1)
cl1 = claims_engine.analyze(c1)
a1 = actions_engine.analyze(c1, cl1)
s1 = sources_engine.discover_and_retrieve(c1, cl1, a1)
e1 = evidence_engine.verify(c1, cl1, s1)
t1 = threat_engine.analyze(c1, cl1, a1, s1, e1)
fp1 = fingerprint_engine.create_or_match(c1, cl1, a1, s1, e1, t1)

# Engine 9: Verify Identity & Resolve Entities (executes before final Policy evaluation)
identity_1 = identity_engine.verify(
    content=c1,
    claims=cl1,
    sources=s1,
    evidence=e1,
    threat=t1,
)

# Engine 8: Decide Intervention Policy (consumes IdentityAnalysis from Engine 9)
decision_1 = policy_engine.decide(
    content=c1,
    claims=cl1,
    actions=a1,
    sources=s1,
    evidence=e1,
    threat=t1,
    fingerprint=fp1,
    identity=identity_1,
)

print(f"Identity Status: {identity_1.identity_status}")           # IdentityStatus.NOT_ESTABLISHED
print(f"Entities: {[e.name for e in identity_1.entities]}")       # ['Rahul Sharma', ...]
print(f"Authority Alignment: {identity_1.authority_alignments[0].alignment_status}") # NOT_ESTABLISHED
print(f"Policy Decision: {decision_1.decision}")                   # PolicyDecisionType.PAUSE
print(f"Severity: {decision_1.severity}")                         # PolicySeverity.HIGH
print(f"Requires Confirmation: {decision_1.required_user_confirmation}") # True
print(f"Relevant Identity ID: {decision_1.relevant_identity_id}") # IDA-001

# Observation 2: Verified official entity (Positive Benchmark)
raw_text_2 = (
    "ABC Securities Private Limited is a SEBI registered broker (Registration: INZ00012345). "
    "Visit our official portal at https://www.abcsecurities.com for services."
)
c2 = content_engine.process_text(raw_text_2)
cl2 = claims_engine.analyze(c2)
s2 = sources_engine.discover_and_retrieve(c2, cl2)
e2 = evidence_engine.verify(c2, cl2, s2)
identity_2 = identity_engine.verify(content=c2, claims=cl2, sources=s2, evidence=e2)

print(f"Verified Identity Status: {identity_2.identity_status}")   # IdentityStatus.ESTABLISHED
print(f"Identity Resolution Confidence: {identity_2.confidence}")  # >= 0.95
```

---

## 11. Engine 10: Behavioural Signal Intelligence Engine

Identifies behavioural and interaction-pattern signals emerging across sequences of financial content and user actions without making legal fraud adjudications, diagnosing psychological conditions, or issuing direct policy interventions.

### Core Capabilities
1. **Interaction Event Model & Session History**:
   - Small typed event model (`InteractionEvent`, `InteractionEventType`, `InteractionHistory`).
   - Privacy-safe reference storage (`action_id`, `claim_id`, `decision_id`, `sequence_index`, `timestamp`) with automatic scrubbing of forbidden sensitive keys (`password`, `otp`, `pin`, `cvv`, `keystrokes`, etc.).
2. **Temporal & Progression Analysis**:
   - Configurable timing thresholds (`rapid_escalation_seconds_threshold`, `rapid_channel_migration_seconds_threshold`, `short_interval_seconds_threshold`).
   - Interval computations and time-budget evaluation.
3. **Multi-Pattern Detectors**:
   - **Pressure Detector** (`PressureDetector`): Identifies `TIME_PRESSURE`, `FOMO_PRESSURE`, `REPEATED_URGENCY`, and `URGENCY_ESCALATION` without accusatory labeling.
   - **Escalation Detector** (`EscalationDetector`): Identifies `LOW_TO_HIGH_IMPACT_TRANSITION`, `PROGRESSIVE_COMMITMENT`, `RAPID_ACTION_ESCALATION`, and `INFORMATION_TO_TRANSACTION_SHIFT`.
   - **Persistence Detector** (`PersistenceDetector`): Identifies `RETRY_AFTER_DECLINE`, `PERSISTENT_PAYMENT_REQUEST`, `PERSISTENT_CREDENTIAL_REQUEST`, `REPEATED_ACTION_REQUEST`, `USER_OVERRIDE`, and `REPEATED_WARNING_OVERRIDE`.
   - **Channel Detector** (`ChannelDetector`): Identifies `CHANNEL_MIGRATION`, `RAPID_CHANNEL_MIGRATION`, and `PRIVATE_CHANNEL_ESCALATION`.
4. **Findings & Downstream Policy Hints**:
   - High-level `BehaviouralFinding` generation with objective evidence basis and provenance.
   - Structured `BehaviouralPolicyHints` flags for Engine 8 consumption (`high_impact_action_progression`, `pressure_present`, `repeated_request_present`, `user_override_present`, `rapid_escalation_present`, `information_to_transaction_shift`).
   - `SessionBehaviourSummary` aggregating session statistics without user trustworthiness scoring or character grading.

### Usage Example

```python
from nivesh.behaviour import (
    BehaviouralSignalEngine,
    InteractionEvent,
    InteractionEventType,
    InteractionHistory,
)

engine = BehaviouralSignalEngine()

# Session history with sequence of observable events
history = InteractionHistory(session_id="SESS-001")
history.add_event(InteractionEvent(
    event_id="EVT-01",
    timestamp="10:00:00",
    event_type=InteractionEventType.CONTENT_VIEW,
))
history.add_event(InteractionEvent(
    event_id="EVT-02",
    timestamp="10:01:00",
    event_type=InteractionEventType.CHANNEL_CHANGED,
    channel="telegram",
))
history.add_event(InteractionEvent(
    event_id="EVT-03",
    timestamp="10:03:00",
    event_type=InteractionEventType.PAYMENT_REQUESTED,
))

analysis = engine.analyze(
    content=content,
    claims=claims,
    actions=actions,
    interaction_history=history,
)

print(analysis.signals)       # [LOW_TO_HIGH_IMPACT_TRANSITION, CHANNEL_MIGRATION, ...]
print(analysis.policy_hints)  # high_impact_action_progression=True, ...
```


---

## 13. Phase 11.1: Product Orchestrator Core

The central **Product Orchestrator Core** (`nivesh.orchestrator`) coordinates all 10 intelligence engines into a single, cohesive analysis system. It acts as the application-level coordinator sitting above the intelligence engines, without duplicating, replacing, or overriding engine intelligence.

### 13.1 Architectural Position & Principles

```text
Raw User Input (Text, URL, Image)
          │
          ▼
┌────────────────────────────────────────────────────────┐
│             Product Orchestrator Core                  │
│               (nivesh.orchestrator)                    │
└────────────────────────────────────────────────────────┘
          │
          ├─► Engine 1: Content Intelligence
          │        ↓
          ├─► Engine 2: Claim Intelligence
          │        ↓
          ├─► Engine 3: Action Intelligence
          │        ↓
          ├─► Engine 4: Source Intelligence
          │        ↓
          ├─► Engine 5: Evidence Verification
          │        ↓
          ├─► [Downstream Intelligence Branches]
          │   ├── Engine 6: Threat & Attack-Path Intelligence
          │   ├── Engine 7: Scam Fingerprint & Collective Intelligence
          │   ├── Engine 9: Identity Verification & Entity Resolution
          │   └── Engine 10: Behavioural Signal Intelligence
          │        ↓
          ├─► Engine 8: Policy & Intervention Engine (SOLE FINAL AUTHORITY)
          │        ↓
          ▼
┌────────────────────────────────────────────────────────┐
│        Unified OrchestrationResult                     │
│  (analysis_id, pipeline_status, policy_decision, ...)  │
└────────────────────────────────────────────────────────┘
```

- **Strict Coordination, Zero Duplicate Intelligence**: The orchestrator contains no scam classification keywords, threat heuristic rules, or risk scores. It only routes canonical inputs and outputs between engines.
- **Engine 8 Remains the Sole Policy Authority**: The orchestrator never decides `ALLOW`, `INFORM`, `WARN`, `PAUSE`, or `BLOCK`. It delegates 100% of policy evaluation to Engine 8.
- **Deterministic Pipeline**: Identical inputs and upstream conditions produce identical engine invocation sequences, policy decisions, and reason codes.

### 13.2 Canonical Execution Flow & Dependency Model

1. **Step 1 (Engine 1: Content)**: Ingests raw text, URL, or image bytes and normalizes it into `NormalizedContent`. Missing input or fatal Engine 1 failure triggers `FatalOrchestrationError`.
2. **Step 2 (Engine 2: Claims)**: Extracts atomic assertions from `content`.
3. **Step 3 (Engine 3: Actions)**: Categorizes requested actions conditioned on `content` and `claims`.
4. **Step 4 (Engine 4: Sources)**: Retrieves official filings and registry records conditioned on `content`, `claims`, and `actions`.
5. **Step 5 (Engine 5: Evidence)**: Evaluates claim verification conditioned on `content`, `claims`, and `sources`.
6. **Downstream Intelligence Branches**:
   - **Engine 6 (Threat)**: Analyzes multi-stage attack paths (`content`, `claims`, `actions`, `sources`, `evidence`).
   - **Engine 7 (Fingerprint)**: Matches or generates collective structural fingerprints (`content`, `claims`, `actions`, `sources`, `evidence`, `threat`).
   - **Engine 9 (Identity)**: Resolves entity credentials and authority claims (`content`, `claims`, `sources`, `evidence`, `threat`).
   - **Engine 10 (Behaviour)**: Analyzes sequence progression and urgency signals (`content`, `claims`, `actions`, `threat`, `fingerprint`, `identity`, `interaction_history`).
7. **Step 10 (Engine 8: Policy & Intervention)**: Evaluates all gathered intelligence and emits the final intervention decision (`PolicyDecision`).

### 13.3 Error Classification & Failure Isolation

The orchestrator classifies engine outcomes into four distinct categories (`EngineOutcomeType`):

| Error Category | Classification | Orchestrator Handling |
| :--- | :--- | :--- |
| **Engine Success** | `SUCCESS` | Normal progression; records output ID and duration in telemetry. |
| **Expected Analytical Result** | `EXPECTED_ANALYTICAL_RESULT` | Non-failure analytical findings (`NO_MATCH`, `NOT_ESTABLISHED`, `INSUFFICIENT_EVIDENCE`, `SOURCE_UNAVAILABLE`). Preserved without fabricating evidence or crashing. Counted in `engines_succeeded`. |
| **Recoverable Engine Failure** | `RECOVERABLE_FAILURE` | Engine raises a runtime exception. In default mode (`fail_fast=False`), the pipeline degrades gracefully (`status="DEGRADED"`), passes safe empty structures downstream, records warnings, and allows Engine 8 to decide with available context. |
| **Fatal Orchestration Failure** | `FATAL_FAILURE` | Critical failure (e.g. invalid input, Engine 1 crash, or failure under `fail_fast=True`). Pipeline halts immediately with `FatalOrchestrationError`. |

### 13.4 Analysis Identity, Provenance & Privacy Boundary

- **Analysis Correlation**: Every analysis request is assigned a unique `analysis_id` (e.g., `ORCH-XXXXXXXXXXXX`). Intermediate output IDs (`content_id`, `claims_id`, `fingerprint_id`, `decision_id`, etc.) are mapped in `engine_output_ids`.
- **Session Handling & Isolation**: When `session_id` is supplied, `ProductOrchestrator` maintains session histories in separate namespaces, guaranteeing that interactions in Session A never contaminate Session B.
- **Privacy Boundary**: Prohibited credentials and PII (`password`, `otp`, `pin`, `cvv`, `card_number`, `account_number`, `api_key`, `token`, `bearer`, etc.) are automatically stripped from `request_metadata` during initialization and never retained in telemetry or provenance.

### 13.5 Python Usage Example

```python
from nivesh.orchestrator import ProductOrchestrator, OrchestratorConfig
from nivesh.behaviour.event_model import InteractionEvent, InteractionEventType

orchestrator = ProductOrchestrator()

# Record an observable session event
orchestrator.record_interaction_event(
    "SESSION-001",
    InteractionEvent(
        event_id="EVT-01",
        timestamp="10:00:00",
        event_type=InteractionEventType.CHANNEL_CHANGED,
        channel="telegram",
    ),
)

# Analyze incoming content
result = orchestrator.analyze(
    text="Guaranteed 40% returns on private Telegram VIP group. Pay ₹5,000 now.",
    session_id="SESSION-001",
)

print(result.pipeline_status)      # "COMPLETED"
print(result.decision)             # PolicyDecisionType.PAUSE
print(result.primary_reason)        # "Pause before proceeding: This payment request..."
print(result.engine_output_ids)     # {'analysis_id': 'ORCH-...', 'content_id': '...', ...}
print(result.telemetry.engines_executed) # ['engine_1_content', ..., 'engine_8_policy']
```

---

## 14. Phase 11.2: Canonical Unified Analysis Context (AnalysisContext)

The **Unified Analysis Context** (
ivesh.orchestrator.AnalysisContext) serves as the single, canonical case record for one complete Nivesh Firewall analysis from input ingestion through final policy decision.

`
       Engines (1–7, 9, 10)
               │
               ▼
┌──────────────────────────────┐
│       AnalysisContext        │  ◄── Single canonical case record
└──────────────────────────────┘      Strongly typed engine outputs
               │                      Execution states & durations
               ▼                      Traceability & provenance
┌──────────────────────────────┐
│     Product Orchestrator     │
└──────────────────────────────┘
               │
               ▼
┌──────────────────────────────┐
│    Engine 8: Policy Engine   │
└──────────────────────────────┘
`

### 14.1 Architectural Purpose & Case Record

The AnalysisContext answers all audit and correlation queries for a single financial interaction:
- **What was analyzed?** Input type, channel, content reference, sanitized metadata.
- **Which analysis does this belong to?** Traceable nalysis_id and optional session_id.
- **What did each engine produce?** Strongly typed, unflattened canonical models (NormalizedContent, ClaimAnalysis, ActionAnalysis, SourceAnalysis, EvidenceAnalysis, ThreatAnalysis, FingerprintAnalysis, IdentityAnalysis, BehaviouralAnalysis, PolicyDecision).
- **Which engines succeeded vs failed?** Explicit EngineExecutionState per engine with ISO timestamps, duration in ms, and sanitized error messages.
- **Which results were partial or negative?** Explicit distinction between analytical findings (e.g. SOURCE_UNAVAILABLE, NOT_ESTABLISHED, INSUFFICIENT_EVIDENCE, NO_MATCH) and system crashes (FAILED).
- **How are all outputs correlated?** engine_result_ids mapping all canonical output IDs to the common nalysis_id.

### 14.2 Structure & Fields

| Field Group | Fields | Description |
| :--- | :--- | :--- |
| **Identity & Status** | nalysis_id, session_id, created_at, updated_at, status, stage | Request identifiers, timestamps, overall PipelineStatus, and ContextLifecycleStage |
| **Input Information** | input_type, channel, content_reference, 
equest_metadata | Ingestion channel and sanitized request metadata (PII/credentials stripped) |
| **Canonical Outputs** | content, claims, ctions, sources, evidence, 	hreat, ingerprint, identity, ehaviour, policy | Strongly typed canonical engine models preserved without type dilution |
| **Execution Telemetry** | engine_states, execution_metadata, warnings, errors | Per-engine EngineExecutionState, warnings, and errors |
| **Traceability** | upstream_references, engine_result_ids, provenance | Map of consumed upstream IDs, correlated result IDs, and execution audit trail |

### 14.3 Lifecycle Stages & State Transitions

The context lifecycle transitions strictly through:
\text{CREATED} \to \text{CONTENT\_READY} \to \text{CLAIMS\_READY} \to \text{ACTIONS\_READY} \to \text{SOURCES\_READY} \to \text{EVIDENCE\_READY} \to \text{DOWNSTREAM\_INTELLIGENCE\_READY} \to \text{BEHAVIOUR\_READY} \to \text{POLICY\_READY} \to \text{COMPLETED}

Each engine follows structured transitions:
- PENDING: Initial state upon context creation.
- RUNNING: Transitioned upon mark_engine_started(engine_key).
- COMPLETED: Transitioned upon mark_engine_completed(...).
- SKIPPED: Transitioned upon mark_engine_skipped(...) with recorded skip reason.
- FAILED: Transitioned upon mark_engine_failed(...) with recorded error code and message.

### 14.4 Sensitive Data Boundary

The AnalysisContext enforces zero storage of sensitive credentials, OTPs, or financial secrets:
- Automatic metadata scrubbing on initialization (model_post_init).
- Prohibited key matching (password, otp, pin, cvv, card_number, ccount_number, earer, secret, pi_key, private_key, 	oken, credential, keystroke).
- Recursive sanitization during serialization via context.to_safe_dict().

### 14.5 Immutability & Validation Rules

- **Upstream Prerequisite Validation**: set_policy_result(...) enforces that Engines 1 through 5 results are present before policy can be finalized.
- **Session Correlation Validation**: set_behaviour_result(...) asserts that the behavioural session ID matches context.session_id.
- **Mutation Protection**: Attaching downstream results never mutates previously stored upstream engine results.
- **Consistency Verification**: context.validate_consistency() validates that no engine is simultaneously COMPLETED and FAILED, and verifies result ID alignment.

---

## 15. Engine Pipeline & Failure Handling (Phase 11.3)

Phase 11.3 introduces production-style dependency-aware pipeline execution and failure handling inside the Product Orchestrator without modifying engine intelligence logic or creating a secondary policy engine.

### 15.1 Canonical Dependency Execution Graph

The orchestrator executes the 10 intelligence engines according to an explicit DAG (PipelineGraph):

\\	ext
                    ENGINE 1 (Content)
                            │
                            ▼
                    ENGINE 2 (Claims)
                            │
                            ▼
                    ENGINE 3 (Actions)
                            │
                            ▼
                    ENGINE 4 (Sources)
                            │
                            ▼
                    ENGINE 5 (Evidence)
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
       ENGINE 6 (Threat) ENGINE 7 (FP) ENGINE 9 (Identity)
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                     ENGINE 10 (Behaviour)
                            │
                            ▼
                     ENGINE 8 (Policy)
                            │
                            ▼
                      FINAL POLICY
\
### 15.2 Execution State Model & Failure Categorization

Every engine invocation transitions through controlled lifecycle states (PENDING -> RUNNING -> COMPLETED / SKIPPED / FAILED / CANCELLED). Outcomes are strictly partitioned into three categories:

1. **Successful Analysis**: Engine executes and returns its analytical result (SUCCESS).
2. **Recoverable / Expected Analytical Degraded State**: Engine reports valid domain outcomes such as SOURCE_UNAVAILABLE, NOT_ESTABLISHED, INSUFFICIENT_EVIDENCE, or NO_MATCH. These are recorded as analytical results (EXPECTED_ANALYTICAL_RESULT), not system crashes.
3. **Execution Failure**: Unexpected exceptions, timeouts, or dependency crashes. These are marked FAILED with sanitized error messages and never fabricated into fake intelligence signals.

### 15.3 Dependency-Aware Blocking

If an engine requires a failed prerequisite:
- The dependent engine is marked SKIPPED with dependency_blocked=True and ailed_dependency set to the prerequisite key.
- No synthetic or fabricated evidence, threat signals, identity findings, or behavioural events are created.
- Upstream successful results remain completely intact and uncorrupted.

### 15.4 Bounded Retry & Side-Effect Protection

- Transient network and orchestration failures support bounded retries (max_retries, 
etry_delay_ms).
- Retries are deterministic, observable (
etry_count tracked in both telemetry and EngineExecutionState), and side-effect safe.
- **Fingerprint Protection**: Engine 7 duplicate origin hash detection (_content_hash_registry) guarantees that retried or repeated executions never artificially inflate fingerprint observation counts.

### 15.5 Timeouts & Cooperative Cancellation

- **Per-Engine Timeout Enforcement**: Handled via SafeEngineExecutor using worker thread timeouts (engine_timeout_ms). On timeout, the engine is cleanly marked FAILED with timeout reason and duration recorded.
- **Safe Cancellation**: Controlled via thread-safe CancellationToken. When cancelled, in-flight pipelines transition from RUNNING to CANCELLED, remaining engines are marked CANCELLED, and the context accurately reports CANCELLED (never falsely reporting COMPLETED).

### 15.6 Policy Gate & Policy Authority Boundary

- **Engine 8 Sole Authority**: Engine 8 remains the sole, final safety policy decision authority. The orchestrator never independently invents or overrides policy decisions.
- **Policy Gate (PolicyGate.verify_gate)**: Before invoking Engine 8, the Policy Gate verifies that:
  1. Required content exists.
  2. Claims and actions states are valid.
  3. Source and evidence results are represented (or explicitly degraded).
  4. Threat, fingerprint, identity, and behavioural findings are represented where required.
  5. No prerequisite engine is in an unresolved RUNNING or PENDING state.
  6. The pipeline has not been cancelled.
- If prerequisites fail or cancellation occurred, Engine 8 is skipped and no fallback policy decision is fabricated (policy_decision=None).

### 15.7 Structured Telemetry & Privacy Boundary

- Telemetry captures structured metrics: engine_name, engine_key, engine_version, started_at, completed_at, duration_ms, status, output_id, 
etry_count, and metadata.
- **Privacy Sanitization**: Passwords, OTPs, PINs, CVVs, card numbers, bank account numbers, raw credentials, and keystrokes are automatically scrubbed from error messages, telemetry, and execution metadata using regular expression redaction ([REDACTED], [REDACTED_CARD]).

---

## 16. Test Suite Verification

Run all pytest unit, integration, regression, orchestration, context, and pipeline tests across all 10 engines and the product orchestrator:

```bash
python -X utf8 -m pytest -v
```
**Results:** 441 passed in 24.42s (0 failed, 100% pass rate).
- **Existing 10 Intelligence Engines**: 386 tests.
- **Phase 11.1 Product Orchestrator Core (`tests/test_orchestrator.py`)**: 17 tests.
- **Phase 11.2 Unified Analysis Context Suite (`tests/test_context.py`)**: 20 tests.
- **Phase 11.3 Engine Pipeline & Failure Handling (`tests/test_pipeline.py`)**: 18 tests.
  1. Full successful execution (`E1` -> `E2` -> `E3` -> `E4` -> `E5` -> `E6/E7/E9/E10` -> `E8`)
  2. Correct dependency order enforcement
  3. Engine 1 failure blocks downstream engines
  4. Engine 4 source failure preserves failure, skips E5, produces no fake evidence
  5. Engine 6 threat failure preserves independent E9/E10 results, skips E7
  6. Engine 7 fingerprint failure isolation
  7. Engine 9 identity failure not converted to `IDENTITY_MISMATCH`
  8. Engine 10 behaviour failure creates no synthetic behavioural signals
  9. Policy Gate blocks Engine 8 when prerequisites are unresolved
  10. Policy authority: Engine 8 is sole decision authority; orchestrator never invents policy
  11. Timeout protection: engine timeout handled gracefully without hanging
  12. Bounded retry: transient failure retried deterministically with observable `retry_count`
  13. Retry safety for fingerprinting: repeated runs do not inflate observation count
  14. Session isolation: simultaneous sessions remain completely independent
  15. Context integrity: one engine cannot overwrite another engine's results
  16. Safe cancellation: leaves context as CANCELLED, never COMPLETED
  17. Deterministic execution: equivalent inputs yield identical execution states
  18. Privacy preservation: telemetry and errors never leak credentials, OTPs, PINs, or cards

**Reconciled Arithmetic**:
386 \text{ (Engines 1--10)} + 17 \text{ (Phase 11.1)} + 20 \text{ (Phase 11.2)} + 18 \text{ (Phase 11.3)} = 441 \text{ tests (100\% match)}
*(Zero regressions across all existing suites, zero skipped, 0 failed across consecutive fresh-process runs).*
