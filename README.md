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

---

## 16. Unified Firewall API & Result (Phase 11.4)

Phase 11.4 provides the **single canonical, frontend-facing product API layer** for Nivesh Firewall. It abstracts the internal multi-engine architecture (Engines 1–10) behind a clean, stable product interface.

### 16.1 Product API Architecture

The frontend communicates with a single canonical endpoint rather than orchestrating individual engines:

```text
Frontend (Web / Extension / Mobile)
               │
               ▼
   POST /api/v1/firewall/analyze
               │
               ▼
┌──────────────────────────────────────────────┐
│           Product Orchestrator               │
│               (Phase 11.3)                   │
│                                              │
│   E1 -> E2 -> E3 -> E4 -> E5                 │
│         -> E6, E7, E9 -> E10                 │
│         -> E8 (Policy Decision Authority)    │
└──────────────────────────────────────────────┘
               │
               ▼
   FirewallAnalysisResponse
 (Clean, sanitized, unified frontend result)
```

- **Canonical Analyze Endpoint**: `POST /api/v1/firewall/analyze`
- **Canonical Retrieval Endpoint**: `GET /api/v1/firewall/analysis/{analysis_id}`
- **Sole Decision Authority**: The final decision (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`) comes exclusively from Engine 8. The API transport layer performs zero decision calculations.
- **Additive & Backwards-Compatible**: All 10 existing engine endpoints under `/api/v1/...` remain completely intact for testing and diagnostic use.

### 16.2 Canonical Request & Response Schemas

#### Request (`FirewallAnalyzeRequest`)
- `input_type`: `text`, `url`, `image`, or `normalized`
- `text`: Raw text payload (max 50,000 characters)
- `url`: Optional target URL
- `session_id`: Optional session identifier (max 128 characters)
- `channel`: Ingestion channel (e.g., `web`, `browser`, `telegram`, `whatsapp`, `instagram`, `youtube`, `email`, `sms`)
- `metadata`: Optional client metadata

#### Response (`FirewallAnalysisResponse`)
- **Analysis Identifiers**: `analysis_id`, `session_id`, `pipeline_status`, `created_at`, `completed_at`, `duration_ms`
- **Canonical Decision**: `decision` (`ALLOW` / `INFORM` / `WARN` / `PAUSE` / `BLOCK`), `severity`, `primary_reason`, `reason_codes`, `explanation` (`user_message`, `technical_message`, `supporting_signals`), `actions_required`, `required_user_confirmation`, `cooldown_seconds`
- **Structured Engine Sections**:
  - `content`: `content_id`, `summary`, `contains_financial_content`, `language`, `entities`
  - `claims`: `claim_id`, `text`, `topic`, `predicate`, `verification_status`
  - `actions`: `action_id`, `action_type`, `description`, `target`, `impact_level`
  - `evidence`: `overall_status`, `verification_count`, `supported_claims_count`, `contradicted_claims_count`, `source_documents_count`, `retrieval_status`
  - `identity`: `identity_status` (`ESTABLISHED`, `NOT_ESTABLISHED`, `IDENTITY_MISMATCH`, `AMBIGUOUS`), `claimed_entities`, `findings_summary`, `confidence`
  - `threat`: `threat_signals`, `attack_stage`, `terminal_stage`, `threat_families`, `high_impact_action_count`, `confidence`
  - `fingerprint`: `match_type` (`NO_MATCH`, `EXACT_MATCH`, `SEMANTIC_VARIANT`, `STRUCTURAL_MATCH`), `fingerprint_id`, `match_confidence`
  - `behaviour`: `signals`, `findings`, `session_id`, `events_in_session`, `time_pressure_detected`, `rapid_escalation_detected`, `channel_migration_detected`
- **Provenance & Telemetry**: `provenance` (`orchestrator_version`, `source_mode`, `engines_executed`, `engines_succeeded`), `warnings`, `errors`

### 16.3 Privacy Boundary & Error Sanitization

- **Zero Secret Leakage**: Passwords, OTPs, PINs, CVVs, card numbers, bank accounts, and raw credentials are scrubbed and redacted (`[REDACTED]`, `[REDACTED_CARD]`) at the API serialization boundary.
- **Safe Error Structure (`FirewallApiError`)**: Rejections and pipeline errors return structured JSON (`error_code`, `message`, `analysis_id`, `details`). Internal stack traces, python exceptions, and server filesystem paths are never leaked to clients.
- **Session Isolation**: Session histories and behavioural event streams are strictly isolated per `session_id`.

### 16.4 Phase 11.5: End-to-End Integration & Validation

Phase 11.5 establishes the complete, production-grade end-to-end integration and architectural boundary validation of the Product Orchestration Layer.

```text
                 NIVESH FIREWALL
                       │
                       ▼
              UNIFIED FIREWALL API
                       │
                       ▼
               PRODUCT ORCHESTRATOR
                       │
                       ▼
                ANALYSIS CONTEXT
                       │
                       ▼
            DEPENDENCY-AWARE PIPELINE
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
    Intelligence    Identity      Behaviour
        │              │              │
        └──────────────┼──────────────┘
                       ↓
                   ENGINE 8
                     POLICY
                       ↓
                UNIFIED RESULT
```

> [!NOTE]
> Phase 11 creates the complete product backend foundation. Device adapters, browser extension clients, and frontend user interfaces will consume this unified API in subsequent phases.

#### Key Architectural & Validation Guarantees:
1. **Full API-to-Engine Execution**: HTTP requests to `POST /api/v1/firewall/analyze` pass seamlessly into `ProductOrchestrator`, instantiate a thread-safe `AnalysisContext`, execute the dependency-aware pipeline across Engines 1–7, 9, 10, and conclude at Engine 8.
2. **Canonical 5-Stage Benchmark Validation**: Multi-stage attack progression (Educational Claim -> Telegram Migration -> APK Install -> Financial Request -> Time Pressure) reliably produces Action Progression (`DOWNLOAD`, `TRANSFER_MONEY`), Threat Signals (`SOFTWARE_INSTALLATION`, `FINANCIAL_REQUEST`), Identity Verification (`NOT_ESTABLISHED`), Behavioural Escalation (`TIME_PRESSURE`, `REPEATED_URGENCY`), and Engine 8 intervention (`PAUSE`/`BLOCK`) without artificial score inflation.
3. **Benign Scenario Safety**: Purely educational financial content is recognized as financial by Content Intelligence while Claim and Action analysis remain neutral, producing an `ALLOW` decision without synthetic alerts or suspicion.
4. **Identity & Evidence State Preservation**: Precise analytical states (`ESTABLISHED`, `NOT_ESTABLISHED`, `IDENTITY_MISMATCH`, `AMBIGUOUS`, `INSUFFICIENT_EVIDENCE`, `SUPPORTED`, `CONTRADICTED`, `SOURCE_CONFLICT`, `SOURCE_UNAVAILABLE`) are preserved intact and never coerced into generic "scam" or "fraud" flags.
5. **Fingerprint Equivalence & Anti-Inflation**: Semantic variants across wording and amounts trigger structural equivalence (`SEMANTIC_VARIANT`) without inflating observation counters upon retries.
6. **Behavioural Persistence & Session Isolation**: Multi-event interaction streams (e.g. `USER_DECLINED` -> `PAYMENT_REQUEST` -> `URGENCY`) detect `RETRY_AFTER_DECLINE` and `PERSISTENT_PAYMENT_REQUEST`. Session data is strictly isolated; distinct sessions receive zero cross-session behavioral bleed.
7. **Failure Isolation Across All Engines**: Simulated failures in Engines 1 through 10 are safely isolated. Fatal errors halt downstream execution, source/evidence/identity failures produce valid degraded analytical states without fake evidence, and Engine 8 failure never synthesizes a fake policy decision.
8. **Strict Policy Authority Boundary**: AST and runtime verification prove that the Product Orchestrator, API transport, and Engines 1–7, 9, and 10 perform zero policy calculations. Engine 8 is the sole, non-bypassable decision authority.
9. **Explainability & Reason Tracing**: Non-ALLOW decisions expose clear primary reasons, machine-readable reason codes, and supporting findings traceable directly to engine outputs.
10. **Zero-PII Privacy & Error Sanitization**: Passwords, OTPs, PINs, CVVs, card numbers, and raw credentials are scrubbed at all boundaries. Errors return structured API error objects without exposing Python tracebacks, filesystem paths, or internal credentials.
11. **Concurrency Safety & Determinism**: Independent parallel analyses execute with isolated contexts, unique IDs, and perfectly correlated, reproducible results.

---

## 17. Test Suite Verification

Run all pytest unit, integration, regression, orchestration, context, pipeline, product API, and end-to-end validation tests across all 10 engines and the product orchestrator:

```bash
python -X utf8 -m pytest -v
```
**Results:** 481 passed (0 failed, 100% pass rate).
- **Existing 10 Intelligence Engines**: 386 tests.
- **Phase 11.1 Product Orchestrator Core (`tests/test_orchestrator.py`)**: 17 tests.
- **Phase 11.2 Unified Analysis Context Suite (`tests/test_context.py`)**: 20 tests.
- **Phase 11.3 Engine Pipeline & Failure Handling (`tests/test_pipeline.py`)**: 18 tests.
- **Phase 11.4 Unified Firewall API & Result (`tests/test_firewall_api.py`)**: 20 tests.
- **Phase 11.5 End-to-End Integration & Validation (`tests/test_e2e_validation.py`)**: 20 tests.
  1. Full API-to-Engine pipeline integration (`POST /api/v1/firewall/analyze`)
  2. Primary 5-stage threat benchmark end-to-end validation
  3. Full benign financial content scenario validation
  4. Identity state preservation (`ESTABLISHED`, `NOT_ESTABLISHED`, `IDENTITY_MISMATCH`)
  5. Evidence verification state preservation (`SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`)
  6. Fingerprint semantic variants and anti-inflation on repeated analysis
  7. Behavioural progression and persistence (`RETRY_AFTER_DECLINE`, `PERSISTENT_PAYMENT_REQUEST`)
  8. Comprehensive failure injection testing across Engines 1–10
  9. Partial pipeline analytical state validation (valid degraded states vs HTTP 500)
  10. Strict session isolation (Session A and Session B context isolation)
  11. Concurrency safety (concurrent independent analyses with isolated contexts)
  12. Privacy end-to-end sanitization (zero secret/credential leakage)
  13. Provenance validation (traceable engine lineage without secret exposure)
  14. Strict Engine 8 policy authority boundary regression test
  15. Explainability validation for non-ALLOW policy decisions
  16. Stable frontend API contract freeze validation
  17. Analysis retrieval validation (`GET /api/v1/firewall/analysis/{analysis_id}`)
  18. Structured error response sanitization (no stack traces or filepaths)
  19. Performance latency and engine execution smoke test
  20. Pipeline execution determinism test

**Reconciled Arithmetic**:
386 (Engines 1–10) + 17 (Phase 11.1) + 20 (Phase 11.2) + 18 (Phase 11.3) + 20 (Phase 11.4) + 20 (Phase 11.5) = 481 tests (100% match)
*(Zero regressions across all existing suites, zero skipped, 0 failed across consecutive fresh-process runs).*

---

## 18. Product UI Foundation (Phase 12.1)

Phase 12.1 establishes the foundational user interface and design system for the **Nivesh Firewall** product.

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

### 18.1 Key Frontend Architecture Decisions
- **Stack**: React 19, TypeScript, Vite 8, Vitest, React Testing Library, Oxlint.
- **Design Tokens (`tokens.css`)**: Coherent, calm dark slate palette (`--color-bg-canvas`, `--color-bg-surface`, `--color-accent`) with standardized typography, 4px-base spacing scale, borders, and restrained elevation.
- **Accessibility Baseline (`base.css`)**: Visible focus indicators (`:focus-visible`), aria landmarks, semantic HTML, and reduced motion queries.
- **Small, Focused Navigation**: 4 core routes (`Protect`, `Activity`, `Threat Intelligence`, `Settings`).
- **Semantic Status Presentation (`SemanticStatusBadge`)**: Pure presentation system for Engine 8 outcomes (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`) with zero frontend policy calculations.
- **Dynamic Protection Status (`ProtectionStatus`)**: State-driven (`active`, `connecting`, `unavailable`, `error`) probing real `/health` backend status.
- **Zero Mock Intelligence**: No fake scam scores, fabricated threat data, or hardcoded criminal accusations.
- **Reusable Component Library (`components/common/`)**: 18 accessible components (`Button`, `IconButton`, `Input`, `Textarea`, `Select`, `Card`, `Panel`, `Badge`, `StatusIndicator`, `Alert`, `EmptyState`, `LoadingState`, `ErrorState`, `Modal`, `Tooltip`, `Divider`, `SectionHeader`, `MetadataRow`).
- **Frontend Verification**: 25 Vitest unit/component/API tests passing with 0 warnings and 0 errors.

---

## 19. Firewall Analysis Experience (Phase 12.2)

Phase 12.2 connects the user interface to the **real Phase 11 Unified Firewall API**, delivering the complete user-facing content analysis workflow with zero fake data and zero client-side policy recalculation.

```text
Enter financial content
        ↓
Submit for analysis
        ↓
Nivesh Firewall processes it (POST /api/v1/firewall/analyze)
        ↓
Receive authoritative backend response
        ↓
View Engine 8 Policy Decision (ALLOW | INFORM | WARN | PAUSE | BLOCK)
        ↓
Explore 8 Intelligence Panels (Claims, Actions, Evidence, Identity, Threat, Fingerprint, Behaviour, Provenance)
```

### 19.1 Key Deliverables & Architectural Implementation
1. **Real Content Input & Submission**:
   - `ContentEntryCard` on `ProtectView` with client-side character boundary validation (<100,000 chars), channel selection, and duplicate submission prevention during active inflight requests.
2. **Authoritative Backend API Integration**:
   - Dispatches requests via `apiClient.analyze()` to `POST /api/v1/firewall/analyze` with session correlation.
   - Handles deep linking via hash routing (`#protect?id=ORCH-...`) using `apiClient.getAnalysis(id)` without redundant pipeline rerun.
3. **Calm, Honest State Model**:
   - State machine: `IDLE` → `VALIDATING` → `SUBMITTING` → `ANALYZING` → `SUCCESS` (or `ERROR` / `PARTIAL_RESULT`).
   - Multi-step loading experience reflecting the actual pipeline engines without simulated timers.
4. **Authoritative Decision Presentation (Sole Policy Authority: Engine 8)**:
   - Hero banner displaying backend `decision` (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`) with `SemanticStatusBadge`.
   - Non-accusatory `user_message`, explicit confirmation requirement alerts (`required_user_confirmation`), cooldown pauses (`cooldown_seconds`), and official reason codes.
5. **8 Multi-Engine Intelligence Breakdown Panels (`AnalysisResultView`)**:
   - **Claims Intelligence (Engine 2 & 5)**: Atomic assertions with topic, predicate, modality, and verification status (`SUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`).
   - **Requested Actions (Engine 3)**: Action classifications (`DOWNLOAD`, `TRANSFER_MONEY`, `CREDENTIAL_ACCESS`, etc.), targets, urgency, and reversibility.
   - **Evidence Verification (Engine 5 & 4)**: Official registry checks, supported/contradicted claim counts, and source filing retrieval status.
   - **Entity Identity Resolution (Engine 9)**: Exact status (`ESTABLISHED`, `NOT_ESTABLISHED`, `IDENTITY_MISMATCH`), confidence, claimed entities, and regulatory registry findings.
   - **Threat & Attack-Path Analysis (Engine 6)**: Multi-signal attack progression (e.g. `CHANNEL_MIGRATION → FINANCIAL_EXTRACTION`), threat signals, and high-impact action counts.
   - **Scam Fingerprint Intelligence (Engine 7)**: Structural pattern matching (`EXACT_MATCH`, `SEMANTIC_VARIANT`, `NO_MATCH`) and collective observation counts across channels.
   - **Behavioural Signal Intelligence (Engine 10)**: Observed dynamics (time pressure, off-platform migration, rapid escalation) without armchair psychological labeling.
   - **Provenance & Pipeline Audit**: Pipeline status, execution duration in milliseconds, channel, and engine lineage.
6. **Privacy & Security Enforcement**:
   - Strictly excludes and prevents storage or display of forbidden credentials (`password`, `otp`, `pin`, `cvv`, `card_number`, `bank_account`).
   - XSS-safe Virtual DOM rendering without `dangerouslySetInnerHTML`.
7. **Verification & Quality Standards**:
   - **Frontend Tests**: 47 Vitest tests passing (100% pass rate across 4 test suites: `api.test.ts`, `App.test.tsx`, `components.test.tsx`, `analysisWorkflow.test.tsx`).
   - **Lint**: 0 warnings, 0 errors (Oxlint).
   - **Build**: Production bundle built cleanly (`tsc -b && vite build`) in <1 second.
   - **Backend Compatibility**: 481 backend tests passing (100% pass rate across all 10 intelligence engines, context, pipeline, and product API).

---

## 20. Intervention & Protection Experience (Phase 12.3)

Phase 12.3 establishes the dedicated user-facing intervention and protection experience for Nivesh Firewall, transforming the canonical Engine 8 policy decisions into transparent, accessible, and honest protection workflows.

```text
Engine 8 Decision (Sole Policy Authority)
                  ↓
       Intervention Model (Pure Presentation)
                  ↓
┌────────────────────────────────────────────────────────┐
│ ProtectionBanner & InterventionHeader                  │
│ HighImpactActionAlert (Transfers, Credentials, App)    │
│ ProtectionSummaryCard (5 Dimensions with Deep Links)   │
│ WhyIntervenedSection (Primary Reason & Reason Codes)   │
│ RecommendedNextStepCard (Protective Actions Only)      │
│ OverrideConfirmationModal (Explicit 2-Step Workflow)   │
└────────────────────────────────────────────────────────┘
```

### 20.1 Core Architecture & Principles
1. **Frontend as Pure Policy Consumer**:
   - The frontend strictly consumes Engine 8's canonical policy decision. It performs **zero** client-side risk scoring, threat heuristics, or policy re-evaluation.
2. **Honest, Non-Accusatory UX Semantics**:
   - **`ALLOW`**: Calm confirmation ("Action Permitted — Verified Neutral"). No misleading claims of "100% safe" or "guaranteed legitimate".
   - **`INFORM`**: Contextual informational advisory without alarmist framing.
   - **`WARN`**: Caution recommended with backend-supported reasons; never labels an entity as a "scammer".
   - **`PAUSE`**: High-visibility pause state with verification cooldown and explicit confirmation requirements.
   - **`BLOCK`**: Strong protection state ("Action Blocked — Threat Prevented") without sensationalism ("you were definitely scammed").
3. **5-Dimension Protection Summary**:
   - Summarizes Requested Action, Entity Identity, Claim Evidence, Threat Template, and Observed Behaviour with 1-click smooth scrolling to the underlying intelligence panel.
4. **Protective-Only UX Recommendations**:
   - Strictly protective actions (e.g. independently verifying identity, returning to safety); **strictly zero financial or investment advice**.
5. **Fail-Safe Safety Boundary**:
   - If rendering or network issues occur, the UI surfaces a safe error state and **never downgrades** a `BLOCK`, `PAUSE`, or `WARN` state to `ALLOW`.
6. **Explicit User Override**:
   - A 2-step confirmation modal with non-shaming language for overridable policy states, preserving the original policy state if cancelled.
7. **Verification & Quality Standards**:
   - **Frontend Tests**: 103 Vitest tests passing across 7 test suites.
   - **Lint**: 0 warnings, 0 errors (Oxlint).
   - **Production Build**: Built cleanly with Vite and TypeScript compiler.
   - **Extension Tests**: 141 Vitest tests passing across 15 test suites.
   - **Backend Compatibility**: 498 backend tests passing (100% pass rate in `pytest`).

---

## 21. Production Configuration & Environment Architecture (Phase 14.1)

Phase 14.1 establishes a centralized, typed configuration management system across backend (FastAPI), web application (React/Vite), and browser extension (MV3/Vite). The system enforces environment separation between `development`, `test`, and `production` with zero hardcoded environment-specific credentials or secrets.

```text
Environment (.env / Process Environment)
           │
           ▼
Central Settings Layer (nivesh.config.Settings)
           │
   ┌───────┴────────────────────────┬────────────────────────┐
   ▼                                ▼                        ▼
FastAPI Server              Product Orchestrator      Logging System
- CORS Middleware           - Source Mode (LIVE/FIX)  - Sensitive Redaction
- Lifespan Validation       - Engine Timeouts         - Level Control
- Payload Constraints       - Resilience Controls
```

### 21.1 Environment Separation Matrix

| Parameter | Development | Test | Production |
| :--- | :--- | :--- | :--- |
| **`NIVESH_ENV`** | `development` | `test` | `production` |
| **`NIVESH_DEBUG`** | `True` or `False` | `False` | **Strictly `False`** (validated at startup) |
| **`NIVESH_DATABASE_URL`** | `sqlite:///./nivesh_dev.db` (safe fallback) | `sqlite:///:memory:` (isolated) | **Required persistent URI** (e.g. PostgreSQL) |
| **`NIVESH_ALLOWED_ORIGINS`** | Local dev origins (`localhost:5173`, `127.0.0.1:5173`) | Test fixtures | **Strict explicit origin whitelist** (Wildcard `*` rejected) |
| **`NIVESH_LOG_LEVEL`** | `DEBUG` / `INFO` | `WARNING` | `INFO` / `WARNING` (Sensitive data auto-redacted) |
| **`NIVESH_SOURCE_MODE`** | `FIXTURE` / `CACHE` | `FIXTURE` (deterministic) | `FIXTURE`, `CACHE`, or gated `LIVE` |
| **`NIVESH_LIVE_SOURCES_ENABLED`** | `False` | `False` | Explicit gate (required if `source_mode=LIVE`) |

### 21.2 Backend Configuration Reference

All backend variables use the `NIVESH_` prefix and are defined in `nivesh.config.Settings`:

- **Core Server**:
  - `NIVESH_ENV`: Operating environment (`development`, `test`, `production`). Default: `development`.
  - `NIVESH_HOST`: Binding host interface. Default: `127.0.0.1`.
  - `NIVESH_PORT`: HTTP server port. Default: `8000`.
  - `NIVESH_DEBUG`: Debug flag. Strictly rejected if `True` in production.
  - `NIVESH_SECRET_KEY`: Cryptographic signing and token key. Must be set securely in production.
  - `NIVESH_DATABASE_URL`: Database connection string. Required in production; SQLite in-memory or dev fallback rejected in production.
- **Frontend & CORS**:
  - `NIVESH_FRONTEND_URL`: URL of the web UI. Default: `http://localhost:5173`.
  - `NIVESH_ALLOWED_ORIGINS`: Comma-separated or JSON list of allowed origins. Wildcard `*` strictly rejected in production.
  - `NIVESH_ALLOWED_EXTENSION_IDS`: Browser extension IDs permitted to contact the backend (`chrome-extension://<id>`).
- **Logging & Redaction**:
  - `NIVESH_LOG_LEVEL`: System log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`).
  - `SensitiveDataRedactor`: Custom logging filter automatically redacting passwords, tokens, OTPs, PINs, CVVs, and card numbers.
- **Source Intelligence & Safety**:
  - `NIVESH_SOURCE_MODE`: Retrieval mode (`FIXTURE`, `CACHE`, `LIVE`).
  - `NIVESH_LIVE_SOURCES_ENABLED`: Boolean gate. `source_mode=LIVE` in production requires this to be `True`.
- **Operational Feature Flags**:
  - `NIVESH_FEATURE_BROWSER_EXTENSION`: Controls browser content ingestion (`True`/`False`).
  - `NIVESH_FEATURE_ANALYSIS_RETRIEVAL`: Controls `/api/v1/firewall/analysis/{id}` endpoint (`True`/`False`).
- **Network Timeouts & Payload Limits**:
  - `NIVESH_TIMEOUT_REQUEST_SECONDS`: API request timeout (default: `30.0s`).
  - `NIVESH_TIMEOUT_RETRIEVAL_SECONDS`: Source retrieval timeout (default: `10.0s`).
  - `NIVESH_TIMEOUT_PIPELINE_MS`: End-to-end orchestration timeout (default: unconstrained / `None`).
  - `NIVESH_MAX_REQUEST_BYTES`: Max HTTP request body size (default: `10MB`).
  - `NIVESH_MAX_CONTENT_LENGTH`: Max text length (default: `50,000` chars).
  - `NIVESH_MAX_URL_LENGTH`: Max URL length (default: `2,048` chars).
  - `NIVESH_MAX_IMAGE_BYTES`: Max image payload (default: `10MB`).
  - `NIVESH_MAX_SESSION_ID_LENGTH`: Max session ID length (default: `128` chars).

### 21.3 Web Frontend & Browser Extension Configuration

- **Frontend (`frontend/`)**:
  - Configured via `frontend/src/config/env.ts` reading Vite `import.meta.env`.
  - Public variables:
    - `VITE_API_BASE_URL`: Firewall backend URL (default: `http://localhost:8000`).
    - `VITE_APP_NAME`: Application name.
    - `VITE_APP_VERSION`: Release version.
  - Development template: `frontend/.env.example`.
- **Browser Extension (`extension/`)**:
  - Configured via `extension/src/config/index.ts`.
  - Build-time variables:
    - `VITE_API_BASE_URL`: Backend API URL (default: `http://localhost:8000`).
    - `VITE_WEB_APP_URL`: Deep-link web app URL (default: `http://localhost:5173`).
  - Development template: `extension/.env.example`.
  - Security guarantee: Zero secrets, tokens, or backend credentials are embedded in extension bundles.

### 21.4 Startup Validation & Fail-Safe Enforcements

On application startup, `Settings.validate_production_readiness()` verifies that:
1. `NIVESH_DEBUG` is not `True`.
2. `NIVESH_DATABASE_URL` is configured and does not use SQLite in-memory or dev fallback.
3. `NIVESH_ALLOWED_ORIGINS` does not contain `*` and contains at least one explicit origin.
4. `NIVESH_SOURCE_MODE=LIVE` is backed by `NIVESH_LIVE_SOURCES_ENABLED=True`.
5. Any failure aborts startup safely without printing passwords, credentials, or secrets in logs or exceptions.

---

## 22. Persistent Data & Storage Layer (Phase 14.2)

Phase 14.2 establishes the persistent data and storage layer for Nivesh Firewall. It replaces prototype in-memory state with a reliable, transactional database-backed persistence architecture while preserving the strict privacy and zero-secret retention model.

```text
                        NIVESH APPLICATION / API LAYER
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
  AnalysisRepository         FingerprintRepository        SessionRepository
(SqlAlchemyAnalysisRepo)    (SqlAlchemyFingerprintRepo) (SqlAlchemySessionRepo)
           │                          │                          │
           ▼                          ▼                          ▼
   analyses                   fingerprints                sessions
   policy_decisions           fingerprint_observations    session_events
   analysis_results
   engine_executions
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      │
                                      ▼
                        AuditRepository (AuditRecordModel)
                                      │
                                      ▼
                      CENTRAL DATABASE ENGINE & POOL
                 (SQLAlchemy 2.0 / Dialect-Aware Pooling)
                                      │
            ┌─────────────────────────┴─────────────────────────┐
            ▼                                                   ▼
Development & Test: SQLite                           Production: PostgreSQL
(sqlite:///./nivesh_dev.db / in-memory)              (NIVESH_DATABASE_URL)
```

### 22.1 Storage Architecture & Repositories

The storage architecture is organized under `nivesh/storage/` with clean interface abstractions and dependency injection:

1. **`SqlAlchemyAnalysisRepository` (`AnalysisRepository`)**:
   - Persists complete `FirewallAnalysisResponse` cases including Engine 8 policy decisions, normalized content summaries, extracted claims, action classifications, evidence verification summaries, threat stages, fingerprint matches, and behavioral signals.
   - Preserves per-engine execution states (`EngineExecutionModel`) with durations, timestamps, and error codes.
   - Enforces atomic ACID transactions: analysis record, policy decision, results, and execution states commit together or roll back on error.
   - Supports safe retrieval by `analysis_id` and querying recent analyses filtered by decision or session.
   - Implements safe soft-deletion semantics (`soft_delete_analysis`) and privacy-compliant hard deletion with foreign key cascading.

2. **`SqlAlchemyFingerprintRepository` (`FingerprintRepository`)**:
   - Stores collective threat patterns (`ScamFingerprint`) and individual observations (`FingerprintObservation`).
   - Indexes canonical signatures (`exact_signature`, `semantic_signature`, `attack_path_signature`) and threat families for fast candidate retrieval.
   - Implements duplicate-origin safeguards (`content_hashes` registry) to prevent copy-amplification from artificially inflating observation counts.
   - Manages fingerprint lifecycle promotion: automatically promotes fingerprints from `NEW` to `ACTIVE` upon reaching independent observation thresholds (>= 2).
   - Supports user and analyst disputes (`dispute_fingerprint`) with immutable audit notes.

3. **`SqlAlchemySessionRepository` (`SessionRepository`)**:
   - Tracks temporal user interaction sequences (`InteractionHistory`, `InteractionEvent`) for Engine 10 behavioural signal intelligence.
   - Enforces strict session isolation: sessions are partitioned by `session_id`.
   - Automatically sanitizes and scrubs forbidden credential fields (`password`, `otp`, `pin`, `cvv`, `card_number`, `token`, `keystrokes`) before persistence.
   - Rejects payloads containing raw credentials with `ForbiddenFieldError`.

4. **`SqlAlchemyAuditRepository` (`AuditRepository`)**:
   - Append-only audit trail (`AuditRecordModel`) recording operational actions, actor identities, target resources, and event metadata.
   - Enforces tamper-evident timestamps and sanitized metadata serialization.

### 22.2 Privacy Boundary & Zero-Secret Retention Guarantee

The persistent storage layer strictly adheres to the Nivesh Privacy Model:
- **What is Persisted**:
  - Analysis metadata, timestamps, processing duration, and pipeline status.
  - Engine 8 authoritative policy decisions, severity levels, and reason codes.
  - Normalized content summaries, entity names, and public claim texts.
  - Structural threat fingerprints, canonical hashes, and collective observation counts.
  - Privacy-safe interaction event types (`CONTENT_VIEW`, `CHANNEL_CHANGED`, `PAYMENT_REQUESTED`).
- **What is NEVER Persisted**:
  - Raw passwords, OTPs, PINs, CVVs, debit/credit card numbers, and bank account numbers.
  - Full raw browser DOM dumps or un-normalized webpage contents by default.
  - User keystrokes, personal identity documents, or authentication tokens.
- **Fail-Safe Sanitization**:
  - `ForbiddenFieldError` raised if unredacted financial credentials attempt to enter storage repositories.
  - Automatic regex-based redaction on all serialized metadata and error messages.

### 22.3 Database Configuration & Schema Migrations

- **Database Engine Management (`nivesh.storage.database`)**:
  - Configured via `Settings.database_url`.
  - Dialect-aware pooling: `StaticPool` with WAL mode for SQLite; `QueuePool` with pre-ping, connection recycling (`pool_recycle=1800`), and overflow limits for PostgreSQL.
  - Context-managed sessions via `get_db_session()` ensuring deterministic commit and rollback semantics.
  - Health check utility (`check_database_health()`) reporting connectivity, dialect, pool status, and response latency without leaking connection credentials.
- **Alembic Migrations (`alembic/`)**:
  - Migration script: `alembic/versions/001_initial_persistence_schema.py`.
  - Creates all 9 tables: `analyses`, `policy_decisions`, `analysis_results`, `engine_executions`, `fingerprints`, `fingerprint_observations`, `sessions`, `session_events`, and `audit_records`.
  - Fully reversible migrations with complete `upgrade()` and `downgrade()` routines.
  - Automated programmatic migration runner (`run_migrations()`) invoked on startup.

### 22.4 Storage Verification & Test Suite

Verify the persistence layer across unit, integration, concurrency, idempotency, restart persistence, and privacy protection tests:

```bash
python -X utf8 -m pytest tests/test_persistence.py -v
```
**Results:** 23 passed in `test_persistence.py` (0 failed, 100% pass rate).
- Full backend regression suite: **521 passed in 225s** (100% pass rate).
- Web frontend test suite: **103 passed in 15s** (100% pass rate).
- Browser extension test suite: **141 passed in 7s** (100% pass rate).
- Frontend & extension production builds: **Clean (0 errors, 0 warnings)**.


---

## 23. Security, Access Control & Secrets (Phase 14.3)

Phase 14.3 establishes the production security layer for Nivesh Firewall. It secures the application boundary, APIs, administrative operations, and persistent data without modifying the detection semantics of Engines 1–10.

### 23.1 Authentication & Authorization Architecture

Nivesh Firewall implements server-side Role-Based Access Control (RBAC) and dual authentication schemes:

1. **HMAC-SHA256 (HS256) Bearer JWT Tokens (`nivesh.security.tokens`)**:
   - Zero external dependency implementation using Python standard library (`hmac`, `hashlib`, `base64`, `json`).
   - Encodes `user_id`, `organization_id`, `roles`, `session_id`, issue timestamp (`iat`), and expiration (`exp`).
   - Rejects tampered, malformed, or expired tokens with structured security exceptions (`InvalidTokenError`, `TokenExpiredError`, `MalformedTokenError`).
   - Token minting endpoint available at `POST /api/v1/auth/token`.

2. **Timing-Safe Static API Keys (`nivesh.security.api_keys`)**:
   - Accepts `X-API-Key` or `Authorization: ApiKey <key>`.
   - Uses `hmac.compare_digest` to prevent timing attacks.
   - Distinct keys for `admin_api_key` (`ADMIN` role) and `service_api_key` (`SERVICE` role).

3. **Server-Side RBAC Roles (`UserRole`)**:
   - **`ADMIN`**: Full platform authority; fingerprint creation, status promotion/demotion, analysis deletion, and audit log inspection.
   - **`ANALYST`**: Threat review, collective intelligence analysis, dispute processing.
   - **`USER`**: Standard end-user; submit analyses, view owned analyses within user/organization boundary.
   - **`SERVICE`**: Machine-to-machine background tasks and ingestion workers.
   - **`ANONYMOUS`**: Public submission for browser extension and demo traffic (creates unowned analysis).

### 23.2 Authorization Matrix

| Endpoint | Method | Permitted Roles | Notes / Enforcement |
|:---|:---|:---|:---|
| `/api/v1/firewall/analyze` | `POST` | All (`ANONYMOUS`, `USER`, `ADMIN`) | Tags analysis with `user_id` / `org_id` if authenticated |
| `/api/v1/firewall/analysis/{id}` | `GET` | Owner, Org Member, `ADMIN` | **Conceals existence (404)** on IDOR attempts |
| `/api/v1/firewall/analysis/{id}` | `DELETE` | `ADMIN` only | Soft-deletes or purges analysis record; records audit log |
| `/api/v1/fingerprints/create` | `POST` | `ADMIN` only | Protects collective threat intelligence from poisoning |
| `/api/v1/fingerprints/{id}/status` | `POST` | `ADMIN` only | Promotes/demotes fingerprint state with audit trail |
| `/api/v1/fingerprints/{id}/dispute` | `POST` | `USER`, `ANALYST`, `ADMIN` | Allows users to dispute false-positive fingerprint matches |
| `/api/v1/admin/audit-logs` | `GET` | `ADMIN` only | Returns tamper-evident security audit records |
| `/api/v1/auth/token` | `POST` | Public / Gateway | Issues signed HMAC-SHA256 JWT access tokens |
| `/api/v1/health` | `GET` | Public | Status probe with safe database connection check |

### 23.3 Insecure Direct Object Reference (IDOR) & Existence Concealment

When a user attempts to access an analysis belonging to a different user or organization:
- The system **never** returns `403 Forbidden` for IDOR attempts, as returning `403` confirms that the sensitive ID exists.
- The system returns `404 Not Found` with a generic `ANALYSIS_NOT_FOUND` error code, completely concealing the existence of the resource.
- An `IDOR_ACCESS_ATTEMPT` security event is simultaneously recorded in the append-only audit trail with the actor's user ID, IP address, and target analysis ID.

### 23.4 Network & Transport Security Middleware (`nivesh.security.middleware`)

1. **`SecurityHeadersMiddleware`**:
   - `X-Content-Type-Options: nosniff` — Prevents MIME-type sniffing.
   - `X-Frame-Options: DENY` — Prevents clickjacking framing.
   - `Content-Security-Policy: default-src 'self'` — Restricts resource origins.
   - `Referrer-Policy: strict-origin-when-cross-origin` — Protects referrer leakage.
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains` — Enforced automatically in production environments.
   - `Cache-Control: no-store, no-cache, must-revalidate` — Automatically set on sensitive analysis and admin endpoints.

2. **`CorrelationIdMiddleware`**:
   - Extracts incoming `X-Request-ID` or generates a cryptographically random UUIDv4.
   - Injects `request_id` into request state, audit records, and downstream responses via the `X-Request-ID` header.

3. **`SlidingWindowRateLimiter` (`nivesh.security.rate_limiter`)**:
   - Thread-safe in-memory sliding window rate limiter.
   - Tracks requests per authenticated principal (`user:{id}`) or client IP (`ip:{addr}`).
   - Returns `429 Too Many Requests` with `Retry-After`, `X-RateLimit-Limit`, and `X-RateLimit-Remaining` headers.

### 23.5 Zero Secret Leakage & Credential Sanitization

- `safe_dump()` in `Settings` masks all database passwords, `secret_key`, `admin_api_key`, and `service_api_key`.
- `SqlAlchemyAuditRepository` and `log_security_event()` strictly reject and scrub forbidden credentials (`password`, `token`, `otp`, `cvv`, `card_number`, `secret`) before writing to the database.
- Database URLs are dynamically masked (`://user:[REDACTED]@host`) in all health probes, connection logs, and telemetry.

### 23.6 Security Verification & Test Suite

The security layer is verified by a dedicated 20-test test suite (`tests/test_security.py`):

```bash
python -X utf8 -m pytest tests/test_security.py -v
```
**Results:** **20 passed in 40s** (100% pass rate).
- Full backend regression suite: **541 passed in 264s** (100% pass rate).
- Web frontend test suite: **103 passed in 38s** (100% pass rate).
- Browser extension test suite: **141 passed in 19s** (100% pass rate).
- Production bundle builds: **Clean (0 errors, 0 warnings)**.

---

## 24. Observability, Monitoring & Operations (Phase 14.4)

Phase 14.4 establishes the production observability, metrics telemetry, distributed tracing, health probing, and operational runbook for Nivesh Firewall. It provides deep visibility into pipeline execution, engine performance, persistence operations, and external dependencies without introducing behavioral surveillance, user scoring, or sensitive data leakage.

```text
                               INCOMING REQUEST
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │    ObservabilityMiddleware    │
                      │  - X-Request-ID propagation   │
                      │  - X-Correlation-ID tracing   │
                      │  - Route normalization        │
                      │  - Structured access logging  │
                      │  - HTTP metrics recording     │
                      └───────────────┬───────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │      Product Orchestrator     │
                      │  Root Pipeline Trace Span     │
                      │  (nivesh.pipeline.analysis)   │
                      └───────────────┬───────────────┘
                                      │
       ┌──────────────────────────────┼──────────────────────────────┐
       ▼                              ▼                              ▼
┌──────────────┐               ┌──────────────┐               ┌──────────────┐
│  Engines 1-5 │               │ Engines 6,7, │               │   Engine 8   │
│ Child Spans  │──────────────►│    9, 10     │──────────────►│ Policy Span  │
│  & Duration  │               │ Child Spans  │               │ & Decision   │
│  Histograms  │               │  & Duration  │               │ Telemetry    │
└──────────────┘               └──────────────┘               └──────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │      Storage Persistence      │
                      │  - Persistence duration span  │
                      │  - ACID rollback counter      │
                      │  - DB health check probe      │
                      └───────────────┬───────────────┘
                                      │
                                      ▼
                      ┌───────────────────────────────┐
                      │     Observability Outlets     │
                      │  • GET /api/v1/metrics (Prom) │
                      │  • GET /api/v1/traces/recent  │
                      │  • GET /health/live (Probe)   │
                      │  • GET /health/ready (Probe)  │
                      │  • JSON Structured Log Stream │
                      └───────────────────────────────┘
```

### 24.1 Structured Logging & Correlation (`nivesh.observability.logging`)

- **Dual Formatting Modes**:
  - `StructuredJsonFormatter`: Emits standardized JSON lines with ISO-8601 UTC timestamps, log level, service name (`nivesh-firewall`), environment (`development`/`production`/`testing`), request ID, correlation ID, analysis ID, engine key, route, HTTP method, status code, duration, and error details.
  - `StandardTextFormatter`: Emits human-readable terminal output for local development.
- **Context Propagation**:
  - Thread-safe context variables (`request_id_ctx`, `correlation_id_ctx`, `analysis_id_ctx`, `engine_key_ctx`) maintain contextual identifiers across asynchronous execution boundaries and pipeline stages.
- **Fail-Safe Secret Scrubber Filter (`SensitiveDataScrubberFilter`)**:
  - Intercepts all log records and scrubs passwords, tokens, API keys, private keys, OTPs, PINs, CVVs, debit/credit cards, raw authorization headers, and database connection strings (`user:[REDACTED]@host`) before emission.
  - Request bodies are never logged in full by default.

### 24.2 Metrics & Performance Telemetry (`nivesh.observability.metrics`)

The metrics subsystem collects multi-dimensional system operational telemetry while strictly enforcing low label cardinality:

1. **HTTP API Metrics**:
   - `http_requests_total`: Counter partitioned by `method`, `route` (normalized parameterized paths, e.g. `/api/v1/firewall/analysis/{analysis_id}`), and `status_code`.
   - `http_request_duration_seconds`: Histogram measuring latency across standardized latency buckets (`0.005s` to `10.0s`).
   - `http_request_failures_total`: Counter tracking server-side 5xx exceptions and network timeouts.

2. **Firewall Pipeline & Engine Metrics**:
   - `firewall_analysis_requests_total`: Counter of received analysis runs.
   - `firewall_analysis_completed_total`: Counter partitioned by completion status (`COMPLETED`, `DEGRADED`, `FAILED`).
   - `firewall_pipeline_duration_seconds`: Histogram measuring full end-to-end analysis processing time.
   - `firewall_engine_duration_seconds`: Per-engine execution latency histogram labeled by `engine`.
   - `firewall_engine_failures_total`: Counter tracking engine-level failures by `engine` and `error_type`.
   - `firewall_engine_timeouts_total`: Counter tracking execution timeouts per engine.

3. **Policy Decision Metrics (Zero User Profiling)**:
   - `policy_decisions_total`: Counter recording system-level distribution of decisions (`ALLOW`, `INFORM`, `WARN`, `PAUSE`, `BLOCK`). Strictly system metrics; never used to compute hidden user risk scores or profile individuals.

4. **Persistence & Database Metrics**:
   - `persistence_operations_total`: Counter tracking database operations by `operation` and `status`.
   - `persistence_duration_seconds`: Latency histogram of storage repository queries.
   - `persistence_transaction_rollbacks_total`: Counter recording database rollbacks and transaction failures.
   - `persistence_connection_failures_total`: Counter recording database connection pool exhaustion or dropouts.

5. **External Verification Source Metrics**:
   - `source_requests_total`: Counter partitioned by `source_id`.
   - `source_unavailable_total`: Counter recording source outage and reachability failures.
   - `source_cache_hits_total` & `source_cache_misses_total`: Source cache performance counters.

6. **Prometheus Exposition Endpoint**:
   - Standard text-based Prometheus exposition available at `GET /api/v1/metrics`.

### 24.3 Distributed Tracing & Pipeline Diagnostics (`nivesh.observability.tracing`)

- **In-Memory Tracer (`Tracer`)**:
  - Zero third-party APM dependency requirement. Retains spans in a bounded circular buffer (`max_recent_traces=1000`) for production incident reconstruction.
  - Automatically disabled or enabled via `NIVESH_TRACING_ENABLED`.
- **Trace Spans across Canonical Stages**:
  - Root span: `nivesh.pipeline.analysis`
  - Engine spans: `engine.1.content`, `engine.2.claims`, `engine.3.actions`, `engine.4.sources`, `engine.5.evidence`, `engine.6.threat`, `engine.7.fingerprints`, `engine.8.policy`, `engine.9.identity`, `engine.10.behaviour`.
  - Storage span: `storage.persistence`.
- **Sanitized Trace Metadata**:
  - Automatically redacts sensitive fields from span attributes. Raw text, credentials, financial identifiers, and private page DOM dumps are strictly excluded from span metadata.
- **Incident Inspection Endpoint**:
  - `GET /api/v1/traces/recent`: Admin-only endpoint returning sanitized JSON traces for incident analysis.

### 24.4 Health, Readiness & Operational Diagnostics (`nivesh.observability.health`)

1. **Liveness Probe (`GET /health/live`, `GET /api/v1/health/liveness`)**:
   - Answers: *"Is the process running?"*
   - Ultra-lightweight in-memory check without touching database connections or external networks. Always responds in `< 5ms`.

2. **Readiness Probe (`GET /health/ready`, `GET /api/v1/health/readiness`)**:
   - Answers: *"Is the service capable of serving production traffic?"*
   - Checks:
     - Central database connectivity and schema responsiveness (`check_database_health()`).
     - Engine readiness (all 10 engines instantiated and initialized).
     - Source subsystem configuration.
   - Returns `200 OK` (`status="UP"`) or `503 Service Unavailable` (`status="DOWN"`).
   - Zero Credential Leakage: Health outputs report status, latency, and sanitized dialect names. Database passwords, usernames, ports, filesystem paths, and internal connection strings are never exposed.

3. **Graceful Shutdown**:
   - FastAPI lifespan handler coordinates safe termination: rejects incoming traffic, finishes active analysis requests, gracefully closes persistent database connection pools, and flushes trace and metric buffers.

---

### 24.5 Operational Troubleshooting Runbook

This runbook defines actionable operational procedures for production incidents.

#### Runbook A: Database Failure & Connection Pool Exhaustion

- **Symptoms**:
  - Readiness probe returns `503 Service Unavailable` with `dependencies.database.status = "DOWN"`.
  - Metric `persistence_connection_failures_total` or `persistence_transaction_rollbacks_total` is increasing.
  - Log entries with `reason_code: "DATABASE_UNAVAILABLE"`.
- **Diagnostic Procedure**:
  1. Inspect `/health/ready` response for database latency and error codes.
  2. Query Prometheus: `rate(persistence_connection_failures_total[5m])`.
  3. Search structured logs for `service="storage"` and `error_type="DatabaseUnavailableError"`.
- **Operator Action**:
  1. Check PostgreSQL instance status, disk space, and memory utilization.
  2. Verify network connectivity between application cluster and PostgreSQL host.
  3. If connections are exhausted, check active connections in PostgreSQL (`pg_stat_activity`) and increase `pool_size` or review slow transactions.
  4. Application behavior: Pipeline operations fail-safe with `503 Service Unavailable` without corrupting records or leaking database credentials.

#### Runbook B: External Source Outage (SEBI / Exchanges / Registries)

- **Symptoms**:
  - Metric `source_unavailable_total{source_id="..."}` spikes.
  - Upstream Engine 4 and Engine 5 log `source_status: "SOURCE_UNAVAILABLE"`.
- **Diagnostic Procedure**:
  1. Inspect Prometheus: `sum by (source_id) (rate(source_unavailable_total[5m]))`.
  2. Trace failed requests via `/api/v1/traces/recent` checking `engine.4.sources` and `engine.5.evidence` child spans.
- **Operator Action**:
  1. Verify if official government/regulatory portals (e.g. SEBI website) are undergoing scheduled maintenance.
  2. Check firewall egress rules and outbound proxy connectivity.
  3. If an upstream portal is down, verify that Nivesh Firewall maintains fail-safe operation: **Nivesh NEVER pretends unverified claims are verified**. Engine 8 policy automatically emits `WARN` or `PAUSE` with `ReasonCode.SOURCE_UNAVAILABLE` or `ReasonCode.INSUFFICIENT_EVIDENCE`.
  4. If outage is prolonged, temporarily adjust cache TTLs in `SourceIntelligenceEngine` if cached authoritative records are acceptable.

#### Runbook C: Engine Failure or Execution Timeout

- **Symptoms**:
  - Metric `firewall_engine_failures_total{engine="..."}` or `firewall_engine_timeouts_total{engine="..."}` is non-zero.
  - Pipeline completion metric indicates degraded state: `firewall_analysis_completed_total{status="DEGRADED"}`.
- **Diagnostic Procedure**:
  1. Identify failing engine from Prometheus: `topk(3, sum by (engine) (rate(firewall_engine_failures_total[5m])))`.
  2. Search structured logs: `grep '"engine_key": "<failing_engine>"' logs.json | jq .`.
  3. Retrieve full execution trace using `correlation_id` from the log entry.
- **Operator Action**:
  1. Check if the failure is due to malformed input payload or memory exhaustion.
  2. Verify that `SafeEngineExecutor` has isolated the failure: the orchestrator logs a warning, passes safe fallback structures downstream, and completes the pipeline in `DEGRADED` status without crashing the process.
  3. If timeouts are occurring in Engine 1 (OCR) or Engine 6 (Graph analysis), evaluate scaling worker CPU limits or tuning engine execution timeout configurations.

#### Runbook D: High Latency & Slow Processing Spikes

- **Symptoms**:
  - Metric `http_request_duration_seconds` P95/P99 latency exceeds SLA (> 2.0s).
  - Metric `firewall_pipeline_duration_seconds` is elevated.
- **Diagnostic Procedure**:
  1. Compare `firewall_pipeline_duration_seconds` with `http_request_duration_seconds` to isolate API gateway overhead vs pipeline execution.
  2. Check per-engine latency in Prometheus: `histogram_quantile(0.95, sum by (le, engine) (rate(firewall_engine_duration_seconds_bucket[5m])))`.
  3. Inspect `persistence_duration_seconds` to verify if slow database queries are bottlenecking the pipeline.
- **Operator Action**:
  1. If `engine.4.sources` is slow: investigate network latency to external registries; enable caching.
  2. If `storage.persistence` is slow: inspect PostgreSQL query plans on `analyses` and `fingerprints` tables; ensure indexes are active.
  3. If `engine.1.content` is slow: inspect image OCR resolution limits.

#### Runbook E: Elevated API Errors (4xx / 5xx Spikes)

- **Symptoms**:
  - `http_requests_total{status_code=~"5.."}` rate increases above 1%.
  - `http_request_failures_total` alerts fire.
- **Diagnostic Procedure**:
  1. Run query: `sum by (status_code, route) (rate(http_requests_total[5m]))`.
  2. Extract `request_id` from response headers of failing requests.
  3. Search structured logs for `request_id: "<id>"` to reconstruct full request lifecycle and stack trace.
- **Operator Action**:
  1. Distinguish 400 Bad Request (client errors / schema mismatch) from 500 Internal Server Errors.
  2. For 500 errors, review error type and root cause in structured logs.
  3. Verify that secret redaction filter has scrubbed any client credentials from error logs.

#### Runbook F: Deployment Rollback & Verification

- **Procedure**:
  1. **Pre-Rollback Check**:
     - Check current error rates: `rate(http_requests_total{status_code=~"5.."}[5m])`.
     - Confirm whether database migrations occurred. Phase 14.2 schema migrations (`alembic/versions/001_initial_persistence_schema.py`) are backward-compatible.
  2. **Execute Rollback**:
     - Switch deployment traffic to prior stable release container/image.
  3. **Post-Rollback Verification**:
     - Query `/health/live`: Must return `200 OK` within 5 seconds.
     - Query `/health/ready`: Must return `200 OK` with database status `UP`.
     - Verify Prometheus metric `http_requests_total{status_code="200"}` resumes normal baseline.
     - Confirm zero rollback errors in `alembic_version`.

---

### 24.6 Observability Verification & Test Suite

The observability subsystem is verified across 20 comprehensive unit and integration tests (`tests/test_observability.py`):

```bash
python -X utf8 -m pytest tests/test_observability.py -v
```

**Results:** **20 passed in 18s** (100% pass rate).
- Full backend regression suite: **561 passed in 278s** (100% pass rate).
- Web frontend test suite: **103 passed in 14s** (100% pass rate).
- Browser extension test suite: **141 passed in 7s** (100% pass rate).
- Production bundle builds: **Clean (0 errors, 0 warnings)**.



