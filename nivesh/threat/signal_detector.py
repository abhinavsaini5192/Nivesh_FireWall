"""Threat Signal Detector for Engine 6.

Extracts explainable, structured threat signals from:
- NormalizedContent (language cues, handles, domains, URLs, financial signals)
- ClaimAnalysis (authority assertions, return promises, modality)
- ActionAnalysis (channel migration, app downloads, credentials, payments)
- SourceAnalysis (retrieval status, document availability)
- EvidenceAnalysis (regulatory conflicts, identity gaps, unestablished assertions)

Signals are neutral, structured observations with traceable provenance.
They do NOT represent an accusation of criminality or final scam verdict.
"""

import re
from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis, VerificationResult
from nivesh.schemas.threat import ThreatSignal, ThreatSignalType, SignalSource


class ThreatSignalDetector:
    """Detects explainable threat signals across all pipeline dimensions."""

    URGENCY_KEYWORDS = (
        "hurry", "urgent", "immediately", "immediate", "limited time",
        "act now", "today only", "fast", "instant", "last chance", "expires"
    )

    FOMO_KEYWORDS = (
        "don't miss", "dont miss", "exclusive vip", "vip group", "vip channel",
        "few spots left", "golden opportunity", "secret", "guaranteed profit",
        "insider", "limited seats", "special access"
    )

    SECRECY_KEYWORDS = (
        "keep secret", "don't tell anyone", "dont tell", "confidential",
        "keep private", "do not share", "between us", "private group only"
    )

    UPFRONT_FEE_KEYWORDS = (
        "registration fee", "joining fee", "activation fee", "entry fee",
        "pay to join", "subscription fee", "membership fee", "vip fee"
    )

    @classmethod
    def detect_signals(
        cls,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
    ) -> list[ThreatSignal]:
        """Detects structured threat signals with grounded provenance."""
        signals: list[ThreatSignal] = []
        sig_counter = 1

        raw_text = ""
        if content.normalized and content.normalized.text:
            raw_text = content.normalized.text
        elif content.raw and content.raw.text:
            raw_text = content.raw.text
        elif hasattr(content, "raw_text") and content.raw_text:
            raw_text = content.raw_text

        raw_text_lower = (raw_text or "").lower()

        # Map verifications by claim_id
        verifications_by_claim: dict[str, VerificationResult] = {
            v.claim_id: v for v in evidence.verifications
        }

        # ---------------------------------------------------------
        # 1. CLAIMS & EVIDENCE SIGNALS
        # ---------------------------------------------------------
        for claim in claims.claims:
            v_res = verifications_by_claim.get(claim.claim_id)
            pred_upper = (claim.predicate or "").upper()
            claim_text = (claim.text.original if claim.text else "").lower()

            # A. Regulatory / Authority Claims & Impersonation
            regulators = ("SEBI", "RBI", "IRDAI", "PFRDA", "NSE", "BSE")
            subj_upper = (claim.subject or "").upper()
            is_registration_or_licensing = (
                pred_upper in ("REGISTERED_WITH", "LICENSED_BY", "APPROVED_BY", "RECOGNISED_BY", "AUTHORIZED_BY", "AFFILIATED_WITH")
                or any(f"{r.lower()} registered" in claim_text or f"{r.lower()} approved" in claim_text or f"{r.lower()} certified" in claim_text for r in regulators)
            )

            if is_registration_or_licensing and not any(r == subj_upper for r in regulators):
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="REGULATORY_AUTHORITY_CLAIM",
                    source="claim",
                    evidence=f"Claim '{claim.subject}' asserts registration/licensing with '{claim.object or 'regulator'}'",
                    confidence=0.90,
                    description=f"Content asserts regulatory authority by stating association with {claim.object or 'regulator'}.",
                    claim_id=claim.claim_id
                ))
                sig_counter += 1

                # Check evidence verification results (Engine 5)
                if v_res:
                    # Check for concrete identity mismatch or contradiction
                    reasoning_lower = " ".join(v_res.reasoning_trace).lower() if v_res.reasoning_trace else ""
                    # Concrete identity mismatch requires explicit mismatch findings, belonging to another entity, or CONTRADICTED status
                    is_mismatch = (
                        v_res.status == "CONTRADICTED"
                        or "identity mismatch" in reasoning_lower
                        or "belongs to another" in reasoning_lower
                        or "different entity" in reasoning_lower
                    )

                    if is_mismatch:
                        contradiction_note = v_res.reasoning_trace[0] if v_res.reasoning_trace else f"Evidence contradicts claimed registration for '{claim.subject}'"
                        signals.append(ThreatSignal(
                            signal_id=f"SIG-{sig_counter:03d}",
                            type="IDENTITY_MISMATCH",
                            source="evidence_verification",
                            evidence=f"Official registry verification contradicts registration: {contradiction_note}",
                            confidence=v_res.confidence,
                            description=f"Evidence establishes that claimed registration does not belong to '{claim.subject}'.",
                            claim_id=claim.claim_id
                        ))
                        sig_counter += 1

                        signals.append(ThreatSignal(
                            signal_id=f"SIG-{sig_counter:03d}",
                            type="AUTHORITY_IMPERSONATION",
                            source="evidence_verification",
                            evidence=f"Authority claim elevated to impersonation based on identity mismatch: {contradiction_note}",
                            confidence=v_res.confidence,
                            description="Unsubstantiated regulatory claim elevated to authority impersonation based on contradicting identity evidence.",
                            claim_id=claim.claim_id
                        ))
                        sig_counter += 1

                    elif v_res.status == "INSUFFICIENT_EVIDENCE":
                        # Registry search returned 0 matches or insufficient records -> IDENTITY_NOT_ESTABLISHED
                        # Must NOT emit AUTHORITY_IMPERSONATION, FRAUD, IMPERSONATOR, or SCAMMER
                        signals.append(ThreatSignal(
                            signal_id=f"SIG-{sig_counter:03d}",
                            type="IDENTITY_NOT_ESTABLISHED",
                            source="evidence_verification",
                            evidence=f"Official registry verification for '{claim.subject}' returned status '{v_res.status}'",
                            confidence=v_res.confidence,
                            description=f"Claimed regulatory authority for '{claim.subject}' was not established by official database records.",
                            claim_id=claim.claim_id
                        ))
                        sig_counter += 1

            # B. Guaranteed Return Language & Statutory Regulatory Conflict
            if pred_upper in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or "guaranteed" in claim_text:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="GUARANTEED_RETURN_LANGUAGE",
                    source="claim",
                    evidence=f"Claim asserts guaranteed return: '{claim.object or 'returns'}'",
                    confidence=0.95,
                    description="Content uses deterministic guaranteed return promises, an anomalous risk factor in securities markets.",
                    claim_id=claim.claim_id
                ))
                sig_counter += 1

                # Check if regulatory conflict was reported in Engine 5
                if v_res and v_res.regulatory_findings:
                    for rf in v_res.regulatory_findings:
                        if rf.type == "REGULATORY_CONFLICT":
                            signals.append(ThreatSignal(
                                signal_id=f"SIG-{sig_counter:03d}",
                                type="REGULATORY_CLAIM_CONFLICT",
                                source="evidence_verification",
                                evidence=rf.excerpt or "Statutory regulation prohibits assured returns",
                                confidence=0.95,
                                description="The guaranteed return promise directly conflicts with applicable statutory regulations prohibiting assured returns.",
                                claim_id=claim.claim_id,
                                source_document_id=rf.source_document_id
                            ))
                            sig_counter += 1

            # C. Unsupported Claims
            if v_res and v_res.status in ("INSUFFICIENT_EVIDENCE", "CONTRADICTED") and claim.claim_type not in ("REGULATORY", "IDENTITY"):
                # Avoid duplicating guaranteed return signal
                if pred_upper not in ("GUARANTEED_RETURN", "ASSURED_PROFIT"):
                    signals.append(ThreatSignal(
                        signal_id=f"SIG-{sig_counter:03d}",
                        type="UNSUPPORTED_CLAIM",
                        source="evidence_verification",
                        evidence=f"Claim '{claim.predicate}' evaluated with status '{v_res.status}'",
                        confidence=0.85,
                        description=f"Substantive financial assertion for '{claim.subject}' is not substantiated by authoritative evidence.",
                        claim_id=claim.claim_id
                    ))
                    sig_counter += 1

        # ---------------------------------------------------------
        # 2. ACTIONS SIGNALS
        # ---------------------------------------------------------
        for action in actions.actions:
            atype = (action.action_type or "").upper()
            target_str = str(action.target.value or "").lower() if action.target else ""
            desc = getattr(action, "description", None) or (
                ((action.text.original or "") + " " + (action.text.normalized or "")).lower()
                if action.text else ""
            )

            # A. Channel Migration
            if atype == "JOIN_CHANNEL" or "telegram" in target_str or "whatsapp" in target_str:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="PRIVATE_CHANNEL_MIGRATION",
                    source="action",
                    evidence=f"Action requests joining private communication channel: '{action.target.value if action.target else 'channel'}'",
                    confidence=0.92,
                    description="Interaction encourages moving communication to private, encrypted messaging platforms (e.g. Telegram/WhatsApp).",
                    action_id=action.action_id
                ))
                sig_counter += 1

            # B. External Application Download
            elif atype == "DOWNLOAD" or "app" in target_str or ".apk" in target_str or "download" in desc:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="EXTERNAL_APP",
                    source="action",
                    evidence=f"Action instructs downloading external application: '{action.target.value if action.target else 'app'}'",
                    confidence=0.90,
                    description="Interaction requests installation or downloading of external software outside standard public directories.",
                    action_id=action.action_id
                ))
                sig_counter += 1

            # C. Payment Request & Upfront Fee
            elif atype == "PAYMENT" or "pay" in desc or "transfer" in desc:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="PAYMENT_REQUEST",
                    source="action",
                    evidence=f"Action requests monetary payment/transfer: '{action.parameters.get('amount', 'unspecified amount')}'",
                    confidence=0.94,
                    description="Interaction solicits direct monetary payments or financial account transfers.",
                    action_id=action.action_id
                ))
                sig_counter += 1

                # Check if it represents an upfront fee
                if any(k in raw_text_lower for k in cls.UPFRONT_FEE_KEYWORDS) or "fee" in desc:
                    signals.append(ThreatSignal(
                        signal_id=f"SIG-{sig_counter:03d}",
                        type="UPFRONT_FEE",
                        source="action",
                        evidence="Payment requested prior to delivery of returns, advisory, or VIP channel access",
                        confidence=0.88,
                        description="Content requires upfront payment as a prerequisite for promised financial services.",
                        action_id=action.action_id
                    ))
                    sig_counter += 1

            # D. Credential & Identity Requests
            elif atype == "ENTER_CREDENTIALS" or "password" in desc or "pin" in desc:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="CREDENTIAL_REQUEST",
                    source="action",
                    evidence=f"Action requests entering credentials: '{action.target.value if action.target else 'credentials'}'",
                    confidence=0.95,
                    description="Interaction requests sensitive authentication credentials.",
                    action_id=action.action_id
                ))
                sig_counter += 1

            elif atype == "PROVIDE_OTP" or "otp" in desc:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="OTP_REQUEST",
                    source="action",
                    evidence="Action solicits One-Time Password (OTP) disclosure",
                    confidence=0.98,
                    description="High-risk request for second-factor authorization or OTP transmission.",
                    action_id=action.action_id
                ))
                sig_counter += 1

            elif atype == "PROVIDE_KYC" or "aadhaar" in desc or "pan" in desc or "identity document" in desc:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="IDENTITY_DOCUMENT_REQUEST",
                    source="action",
                    evidence=f"Action solicits identity documentation: '{action.target.value if action.target else 'identity document'}'",
                    confidence=0.90,
                    description="Interaction requests personal government identity verification documents.",
                    action_id=action.action_id
                ))
                sig_counter += 1

            elif atype == "AUTHORIZE_APP" or "access" in desc:
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="ACCOUNT_ACCESS_REQUEST",
                    source="action",
                    evidence="Action requests third-party account delegation or app authorization",
                    confidence=0.90,
                    description="Interaction requests account authorization or remote delegation.",
                    action_id=action.action_id
                ))
                sig_counter += 1

        # ---------------------------------------------------------
        # 3. CONTENT-LEVEL PSYCHOLOGICAL & NETWORK SIGNALS
        # ---------------------------------------------------------
        # A. Urgency
        if any(re.search(rf"\b{re.escape(k)}\b", raw_text_lower) for k in cls.URGENCY_KEYWORDS):
            matched = [k for k in cls.URGENCY_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", raw_text_lower)]
            signals.append(ThreatSignal(
                signal_id=f"SIG-{sig_counter:03d}",
                type="URGENCY",
                source="content",
                evidence=f"Text contains urgency cues: {matched}",
                confidence=0.82,
                description="Language creates artificial time compression to expedite user action without deliberation."
            ))
            sig_counter += 1

        # B. FOMO / Exclusivity
        if any(re.search(rf"\b{re.escape(k)}\b", raw_text_lower) for k in cls.FOMO_KEYWORDS):
            matched = [k for k in cls.FOMO_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", raw_text_lower)]
            signals.append(ThreatSignal(
                signal_id=f"SIG-{sig_counter:03d}",
                type="FOMO",
                source="content",
                evidence=f"Text contains exclusivity/FOMO cues: {matched}",
                confidence=0.85,
                description="Language stimulates fear-of-missing-out or false exclusivity to motivate user participation."
            ))
            sig_counter += 1

        # C. Secrecy / Isolation Language
        if any(re.search(rf"\b{re.escape(k)}\b", raw_text_lower) for k in cls.SECRECY_KEYWORDS):
            matched = [k for k in cls.SECRECY_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", raw_text_lower)]
            signals.append(ThreatSignal(
                signal_id=f"SIG-{sig_counter:03d}",
                type="ISOLATION_LANGUAGE",
                source="content",
                evidence=f"Text instructs secrecy or isolation: {matched}",
                confidence=0.90,
                description="Content explicitly discourages consultation with third parties or family members."
            ))
            sig_counter += 1

        # D. External & Lookalike Domains
        urls = []
        if content.structured_signals and content.structured_signals.urls:
            urls = content.structured_signals.urls
        elif hasattr(content, "signals") and getattr(content, "signals", None) and hasattr(content.signals, "urls"):
            urls = content.signals.urls

        for url_sig in urls:
            domain = url_sig.domain.lower() if url_sig.domain else ""
            # Check for lookalike cues
            if any(sub in domain for sub in ("sebi-", "nse-", "bse-", "gov-", "official-")) and not domain.endswith(".gov.in"):
                signals.append(ThreatSignal(
                    signal_id=f"SIG-{sig_counter:03d}",
                    type="LOOKALIKE_DOMAIN",
                    source="content",
                    evidence=f"Domain '{domain}' mimics official regulatory or exchange naming structures",
                    confidence=0.92,
                    description="Domain name incorporates regulatory keywords without official authoritative TLD."
                ))
                sig_counter += 1
            elif domain and not any(official in domain for official in ("sebi.gov.in", "nseindia.com", "bseindia.com", "rbi.org.in")):
                # General external domain in financial investment context
                if not any(s.type == "EXTERNAL_DOMAIN" for s in signals):
                    signals.append(ThreatSignal(
                        signal_id=f"SIG-{sig_counter:03d}",
                        type="EXTERNAL_DOMAIN",
                        source="content",
                        evidence=f"External financial/advisory destination referenced: '{domain}'",
                        confidence=0.75,
                        description="External domain outside official exchanges and regulatory portals."
                    ))
                    sig_counter += 1

        return signals
