"""Threat Explainer and Fingerprint Preparation for Engine 6.

Synthesizes objective, non-accusatory structural explanations of the interaction
and prepares normalized patterns for downstream Engine 7 (Scam Fingerprint Engine).
"""

from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import (
    ThreatSignal,
    AttackPath,
    AttackTransition,
    ClaimActionLink,
    EvidenceWeakness,
    HighImpactAction,
    ThreatCombination,
    ThreatFamily,
    ThreatExplanation,
    FingerprintPreparation,
)


class ThreatExplainer:
    """Builds auditable explanations and prepares normalized fingerprint features."""

    @classmethod
    def generate_explanation(
        cls,
        signals: list[ThreatSignal],
        attack_path: AttackPath,
        combinations: list[ThreatCombination],
        threat_families: list[ThreatFamily],
        weaknesses: list[EvidenceWeakness],
    ) -> ThreatExplanation:
        """Constructs an objective, structural explanation of the observed path."""
        stages = [n.stage for n in attack_path.nodes if n.stage != "DISCOVERY"]

        if not stages and not threat_families:
            return ThreatExplanation(
                summary="Content represents informational or educational material with no significant threat path detected.",
                mechanisms=[],
                key_factors=["Absence of high-impact action requests or unverified authority claims"]
            )

        # Build narrative summary
        stage_names = " ➔ ".join(stages) if stages else "Direct Interaction"
        summary_parts = [
            f"Observed interaction follows an attack path through {len(stages)} active stages: [{stage_names}]."
        ]

        if any(w.weakness_type == "IDENTITY_NOT_ESTABLISHED" for w in weaknesses):
            summary_parts.append(
                "Regulatory authority or identity claims were not substantiated by official public registry records."
            )
        if any(w.weakness_type == "REGULATORY_CONFLICT" for w in weaknesses):
            summary_parts.append(
                "Financial promises (e.g. guaranteed returns) conflict directly with statutory regulatory prohibitions."
            )

        if combinations:
            combo_descs = [c.mechanism.replace("_", " ") for c in combinations]
            summary_parts.append(f"Identified composite threat patterns: {', '.join(combo_descs)}.")

        mechanisms = [c.mechanism for c in combinations]
        key_factors = [s.description for s in signals[:5]]

        return ThreatExplanation(
            summary=" ".join(summary_parts),
            mechanisms=mechanisms,
            key_factors=key_factors
        )

    @classmethod
    def prepare_fingerprint_components(
        cls,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        threat_families: list[ThreatFamily],
        attack_path: AttackPath,
        transitions: list[AttackTransition],
    ) -> FingerprintPreparation:
        """Extracts normalized structural components for Engine 7 (Scam Fingerprint Engine)."""
        claim_patterns: list[str] = []
        for c in claims.claims:
            p = f"claim:{c.claim_type.lower() if c.claim_type else 'general'}:{(c.predicate or '').lower()}"
            if c.object:
                p += f":{str(c.object).strip().lower()}"
            claim_patterns.append(p)

        action_patterns: list[str] = []
        for a in actions.actions:
            pat = f"action:{(a.action_type or '').lower()}"
            if a.target and a.target.value:
                pat += f":{str(a.target.value).strip().lower()}"
            action_patterns.append(pat)

        identity_patterns: list[str] = []
        if content.entities and content.entities.people:
            for p in content.entities.people:
                p_val = getattr(p, "normalized", None) or getattr(p, "text", "")
                if p_val:
                    identity_patterns.append(f"identity:person:{str(p_val).strip().lower()}")
        if content.entities and content.entities.regulators:
            for r in content.entities.regulators:
                r_val = getattr(r, "normalized", None) or getattr(r, "text", "")
                if r_val:
                    identity_patterns.append(f"identity:regulator:{str(r_val).strip().lower()}")

        channel_patterns: list[str] = []
        handles = []
        if content.structured_signals and content.structured_signals.social_handles:
            handles = content.structured_signals.social_handles
        elif hasattr(content, "signals") and getattr(content, "signals", None) and hasattr(content.signals, "social_handles"):
            handles = content.signals.social_handles

        for sh in handles:
            channel_patterns.append(f"channel:{sh.platform.lower()}:{sh.handle.lower()}")

        attack_stages = [n.stage for n in attack_path.nodes if n.stage != "DISCOVERY"]
        transition_patterns = [f"{t.from_stage}->{t.to_stage}" for t in transitions]

        return FingerprintPreparation(
            normalized_claim_patterns=claim_patterns,
            normalized_action_patterns=action_patterns,
            normalized_identity_patterns=identity_patterns,
            normalized_channel_patterns=channel_patterns,
            normalized_threat_families=threat_families,
            normalized_attack_stages=attack_stages,
            normalized_transitions=transition_patterns
        )

    @classmethod
    def collect_uncertainties(
        cls,
        signals: list[ThreatSignal],
        weaknesses: list[EvidenceWeakness],
        evidence: EvidenceAnalysis,
    ) -> list[str]:
        """Lists explicit evidentiary and inferential limits to prevent overclaiming."""
        uncertainties: list[str] = [
            "Analysis describes observed behavioral and structural patterns, not a legal adjudication of criminality.",
            "Actual intent of the content creator cannot be verified from published text and public records alone."
        ]

        if any(w.weakness_type == "IDENTITY_NOT_ESTABLISHED" for w in weaknesses):
            uncertainties.append(
                "Absence of matching registry records establishes lack of public verification, but does not definitively prove fraud."
            )

        if any(s.type == "REGULATORY_CLAIM_CONFLICT" for s in signals):
            uncertainties.append(
                "Regulatory conflict establishes that conduct is prohibited for covered entities, not whether financial transactions occurred."
            )

        return uncertainties
