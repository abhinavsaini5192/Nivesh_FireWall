"""Normalized Feature Extractor for Engine 7.

Extracts privacy-preserving, canonical structural feature tokens from the outputs of
Engines 1 through 6. Eliminates superficial variations (e.g. ₹5,000 vs ₹4,999, specific URLs,
phone numbers, and names) while preserving the underlying attack structure.
"""

import hashlib
import re
from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis, AttackStage


class NormalizedFeatureExtractor:
    """Extracts standardized, privacy-preserving structural threat features."""

    CANONICAL_STAGE_ORDER = [
        "DISCOVERY",
        "TRUST_BUILDING",
        "CHANNEL_MIGRATION",
        "NAVIGATION",
        "SOFTWARE_INSTALLATION",
        "DATA_COLLECTION",
        "CREDENTIAL_CAPTURE",
        "ACCOUNT_ACCESS",
        "FINANCIAL_REQUEST",
        "FINANCIAL_TRANSFER",
    ]

    @classmethod
    def extract_features(
        cls,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        sources: SourceAnalysis,
        evidence: EvidenceAnalysis,
        threat: ThreatAnalysis,
    ) -> dict[str, Any]:
        """Extracts multi-dimensional structural features and signatures."""

        # -------------------------------------------------------------
        # 1. Identity Patterns
        # -------------------------------------------------------------
        identity_patterns: set[str] = set()
        sig_types = {s.type for s in threat.threat_signals}

        if "REGULATORY_AUTHORITY_CLAIM" in sig_types or "AUTHORITY_CLAIM" in sig_types:
            identity_patterns.add("IDENTITY:REGULATORY_AUTHORITY_CLAIM")
        if "AUTHORITY_IMPERSONATION" in sig_types:
            identity_patterns.add("IDENTITY:AUTHORITY_IMPERSONATION")
        if "IDENTITY_NOT_ESTABLISHED" in sig_types:
            identity_patterns.add("IDENTITY:NOT_ESTABLISHED")
        if "IDENTITY_MISMATCH" in sig_types:
            identity_patterns.add("IDENTITY:MISMATCH")

        # Entity / regulator checks from content
        RECOGNISED_REGULATORS = {"SEBI", "RBI", "IRDAI", "PFRDA", "NSE", "BSE", "AMFI", "FMC", "MCA"}
        if content.entities:
            if hasattr(content.entities, "regulators") and content.entities.regulators:
                identity_patterns.add("IDENTITY:REGULATORY_AUTHORITY_CLAIM")
                for r in content.entities.regulators:
                    if r.text:
                        r_clean = r.text.strip().upper()
                        if r_clean in RECOGNISED_REGULATORS:
                            identity_patterns.add(f"IDENTITY:REGULATOR:{r_clean}")
            if hasattr(content.entities, "organizations") and content.entities.organizations:
                for org in content.entities.organizations:
                    if "SEBI" in org.text.upper():
                        identity_patterns.add("IDENTITY:REGULATORY_AUTHORITY_CLAIM")
                        identity_patterns.add("IDENTITY:REGULATOR:SEBI")

        # Fallback check on claims if threat signals were not generated
        for c in claims.claims:
            pred_upper = (c.predicate or "").upper()
            if pred_upper in ("REGISTERED_WITH", "LICENSED_BY", "APPROVED_BY", "CERTIFIED_BY"):
                identity_patterns.add("IDENTITY:REGULATORY_AUTHORITY_CLAIM")
                if c.object:
                    obj_clean = str(c.object).strip().upper()
                    if obj_clean in RECOGNISED_REGULATORS:
                        identity_patterns.add(f"IDENTITY:REGULATOR:{obj_clean}")

        if not identity_patterns:
            identity_patterns.add("IDENTITY:UNSPECIFIED_OFFER")

        # -------------------------------------------------------------
        # 2. Claim Patterns (Normalized Semantic Equivalence)
        # -------------------------------------------------------------
        claim_patterns: set[str] = set()
        for c in claims.claims:
            pred_upper = (c.predicate or "").upper()
            c_text = (c.text.original if c.text else "").lower()

            # Guaranteed / Assured / Fixed return equivalence
            if pred_upper in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or any(
                w in c_text for w in ["guarantee", "guaranteed", "assured", "fixed return", "risk free", "100% profit"]
            ):
                claim_patterns.add("CLAIM:GUARANTEED_RETURN")
            elif pred_upper in ("REGISTERED_WITH", "LICENSED_BY", "APPROVED_BY", "CERTIFIED_BY") or str(c.claim_type).upper() in ("REGULATORY", "REGULATORY_REGISTRATION"):
                claim_patterns.add("CLAIM:REGULATORY_REGISTRATION")
            elif pred_upper in ("HIGH_RETURNS", "PROFIT_TARGET", "OUTPERFORMS"):
                claim_patterns.add("CLAIM:FINANCIAL_PROFIT")
            elif c.claim_type:
                claim_patterns.add(f"CLAIM:{c.claim_type.upper()}")

        # -------------------------------------------------------------
        # 3. Action Patterns
        # -------------------------------------------------------------
        action_patterns: set[str] = set()
        for a in actions.actions:
            atype = (a.action_type or "").upper()
            acat = (a.category or "").upper()
            desc = ((a.text.original or "") + " " + (a.text.normalized or "")).lower() if a.text else ""

            if atype in ("JOIN_CHANNEL", "JOIN_GROUP", "FOLLOW_ACCOUNT", "MESSAGE_PERSON") or acat == "CHANNEL_MIGRATION":
                action_patterns.add("ACTION:CHANNEL_MIGRATION")
            elif atype in ("DOWNLOAD", "INSTALL") or acat == "SOFTWARE_INSTALLATION":
                action_patterns.add("ACTION:SOFTWARE_INSTALLATION")
            elif atype in ("PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY") or acat == "FINANCIAL_TRANSACTION":
                action_patterns.add("ACTION:PAYMENT_REQUEST")
                if any(w in desc for w in ["fee", "charge", "activation", "registration fee", "joining fee"]):
                    action_patterns.add("ACTION:UPFRONT_FEE")
            elif atype in ("ENTER_CREDENTIALS", "SHARE_OTP", "CONNECT_ACCOUNT") or acat == "CREDENTIAL_ACCESS":
                action_patterns.add("ACTION:CREDENTIAL_REQUEST")
            elif atype in ("UPLOAD_IDENTITY", "UPLOAD_DOCUMENT") or acat == "DATA_DISCLOSURE":
                action_patterns.add("ACTION:IDENTITY_REQUEST")
            elif atype in ("CONTACT", "CALL_PERSON"):
                action_patterns.add("ACTION:CONTACT_REQUEST")

        # -------------------------------------------------------------
        # 4. Channel Patterns
        # -------------------------------------------------------------
        channel_patterns: set[str] = set()
        handles = []
        if content.structured_signals and content.structured_signals.social_handles:
            handles = content.structured_signals.social_handles
        elif hasattr(content, "signals") and getattr(content, "signals", None) and hasattr(content.signals, "social_handles"):
            handles = content.signals.social_handles

        for sh in handles:
            p_upper = (sh.platform or "").upper()
            if p_upper:
                channel_patterns.add(f"CHANNEL:{p_upper}")

        # Check raw text or features for Telegram / WhatsApp / SMS
        full_text_lower = (content.normalized.text if content.normalized and content.normalized.text else "").lower()
        if "telegram" in full_text_lower or "t.me" in full_text_lower:
            channel_patterns.add("CHANNEL:TELEGRAM")
        if "whatsapp" in full_text_lower or "wa.me" in full_text_lower:
            channel_patterns.add("CHANNEL:WHATSAPP")
        if not channel_patterns:
            channel_patterns.add("CHANNEL:WEB")

        # -------------------------------------------------------------
        # 5. Technical Patterns
        # -------------------------------------------------------------
        technical_patterns: set[str] = set()
        urls = []
        if content.structured_signals and content.structured_signals.urls:
            urls = content.structured_signals.urls
        elif hasattr(content, "signals") and getattr(content, "signals", None) and hasattr(content.signals, "urls"):
            urls = content.signals.urls

        if urls:
            technical_patterns.add("TECHNICAL:EXTERNAL_DOMAIN")

        if "EXTERNAL_APP" in sig_types or "ACTION:SOFTWARE_INSTALLATION" in action_patterns:
            technical_patterns.add("TECHNICAL:EXTERNAL_APP")
        if "LOOKALIKE_DOMAIN" in sig_types:
            technical_patterns.add("TECHNICAL:LOOKALIKE_DOMAIN")

        # -------------------------------------------------------------
        # 6. Threat Patterns
        # -------------------------------------------------------------
        threat_patterns: set[str] = set()
        for sig in threat.threat_signals:
            threat_patterns.add(f"THREAT:{sig.type}")

        # -------------------------------------------------------------
        # 7. Attack Stages & Transitions
        # -------------------------------------------------------------
        attack_stages = [
            n.stage for n in threat.attack_path.nodes
            if n.stage != "DISCOVERY"
        ]
        # Sort stages according to canonical progression
        attack_stages = sorted(
            list(dict.fromkeys(attack_stages)),
            key=lambda s: cls.CANONICAL_STAGE_ORDER.index(s) if s in cls.CANONICAL_STAGE_ORDER else 99
        )

        attack_transitions: list[str] = [
            f"{t.from_stage}->{t.to_stage}" for t in threat.transitions
            if t.from_stage != "DISCOVERY" and t.to_stage != "DISCOVERY"
        ]

        attack_path_signature = ">".join(attack_stages) if attack_stages else "DIRECT"

        # -------------------------------------------------------------
        # 8. Evidence Patterns
        # -------------------------------------------------------------
        evidence_patterns: set[str] = set()
        for w in threat.evidence_weaknesses:
            evidence_patterns.add(f"EVIDENCE:{w.weakness_type}")

        # -------------------------------------------------------------
        # 9. Threat Families
        # -------------------------------------------------------------
        threat_families = sorted(list(set(threat.threat_families)))

        # -------------------------------------------------------------
        # 10. Canonical Features List & Cryptographic Signatures
        # -------------------------------------------------------------
        canonical_features: list[str] = sorted(list(
            identity_patterns
            | claim_patterns
            | action_patterns
            | channel_patterns
            | technical_patterns
            | threat_patterns
            | evidence_patterns
            | {f"STAGE:{s}" for s in attack_stages}
            | {f"TRANSITION:{t}" for t in attack_transitions}
            | {f"FAMILY:{f}" for f in threat_families}
        ))

        # Exact signature: SHA-256 of sorted canonical features
        exact_signature = hashlib.sha256(
            "\n".join(canonical_features).encode("utf-8")
        ).hexdigest()

        # Semantic signature: Invariant core structural features
        # (Omit superficial channel type, specific domain, or superficial wording)
        core_semantic_features = sorted(list(
            {p for p in identity_patterns if not p.startswith("IDENTITY:REGULATOR:")}
            | claim_patterns
            | {p for p in action_patterns if p in ("ACTION:CHANNEL_MIGRATION", "ACTION:SOFTWARE_INSTALLATION", "ACTION:PAYMENT_REQUEST", "ACTION:CREDENTIAL_REQUEST", "ACTION:IDENTITY_REQUEST", "ACTION:CONTACT_REQUEST")}
            | {f"STAGE:{s}" for s in attack_stages}
            | {f"TRANSITION:{t}" for t in attack_transitions}
            | {f"FAMILY:{f}" for f in threat_families if f in ("INVESTMENT_PROMOTION_SCAM", "MALICIOUS_SOFTWARE", "PAYMENT_FRAUD", "REGULATORY_IMPERSONATION")}
        ))
        semantic_payload = f"PATH:{attack_path_signature}|" + "\n".join(core_semantic_features)
        semantic_signature = hashlib.sha256(
            semantic_payload.encode("utf-8")
        ).hexdigest()

        # Content hash: SHA-256 of normalized text for amplification detection
        # Strip superficial URL tracking/ref parameters (?ref=1, &ref=2, ?utm_source=...)
        # so that exact message forwards with altered tracking links are recognized as duplicates.
        content_hash = None
        raw_norm = (content.normalized.text if content.normalized and content.normalized.text else "").strip().lower()
        if raw_norm:
            clean_norm = re.sub(r'(\?|&)(ref|utm_[^=]+|track|s|source|t)=[^&\s\.,;!]+', '', raw_norm)
            clean_norm = re.sub(r'\?(?=\s|[.,;!]|\Z)', '', clean_norm).strip()
            content_hash = hashlib.sha256(clean_norm.encode("utf-8")).hexdigest()

        # Primary observed channel
        observed_channel = None
        if "CHANNEL:TELEGRAM" in channel_patterns:
            observed_channel = "telegram"
        elif "CHANNEL:WHATSAPP" in channel_patterns:
            observed_channel = "whatsapp"
        elif channel_patterns:
            first_ch = sorted(list(channel_patterns))[0].replace("CHANNEL:", "").lower()
            observed_channel = first_ch

        return {
            "identity_patterns": sorted(list(identity_patterns)),
            "claim_patterns": sorted(list(claim_patterns)),
            "action_patterns": sorted(list(action_patterns)),
            "channel_patterns": sorted(list(channel_patterns)),
            "technical_patterns": sorted(list(technical_patterns)),
            "threat_patterns": sorted(list(threat_patterns)),
            "attack_stages": attack_stages,
            "attack_transitions": attack_transitions,
            "evidence_patterns": sorted(list(evidence_patterns)),
            "threat_families": threat_families,
            "canonical_features": canonical_features,
            "exact_signature": exact_signature,
            "semantic_signature": semantic_signature,
            "attack_path_signature": attack_path_signature,
            "content_hash": content_hash,
            "observed_channel": observed_channel,
        }
