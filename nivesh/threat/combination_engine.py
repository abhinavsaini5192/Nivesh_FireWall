"""Multi-Signal Combination and Threat Family Classifier for Engine 6.

Analyzes composite interactions across signals, actions, and evidence gaps.
Crucial principle: Requires meaningful contextual combinations. A single weak signal
(e.g., a Telegram handle alone, or an educational course fee) must NOT escalate
into an investment scam or threat family.
"""

from typing import Optional
from nivesh.schemas.threat import (
    ThreatSignal,
    ThreatCombination,
    ThreatFamily,
    AttackStage,
    HighImpactAction,
)


class CombinationEngine:
    """Evaluates multi-signal combinations and determines matching threat families."""

    @classmethod
    def evaluate(
        cls,
        signals: list[ThreatSignal],
        stages: list[AttackStage],
        high_impact_actions: list[HighImpactAction],
    ) -> tuple[list[ThreatCombination], list[ThreatFamily]]:
        """Evaluates signal combinations and assigns applicable threat families."""
        combinations: list[ThreatCombination] = []
        threat_families: set[ThreatFamily] = set()

        sig_types = {s.type for s in signals}

        # Helper to check if any of the given types are in sig_types
        has_signal = lambda *types: any(t in sig_types for t in types)

        # -----------------------------------------------------------------
        # 1. Multi-Signal Combination Detection
        # -----------------------------------------------------------------
        # Combination 1: Authority Claim / Identity Gap + Private Channel + Payment
        if (
            has_signal("REGULATORY_AUTHORITY_CLAIM", "AUTHORITY_CLAIM", "AUTHORITY_IMPERSONATION", "IDENTITY_NOT_ESTABLISHED", "IDENTITY_MISMATCH")
            and has_signal("PRIVATE_CHANNEL_MIGRATION")
            and has_signal("PAYMENT_REQUEST", "UPFRONT_FEE")
        ):
            lead_sig = "IDENTITY_NOT_ESTABLISHED" if "IDENTITY_NOT_ESTABLISHED" in sig_types else (
                "IDENTITY_MISMATCH" if "IDENTITY_MISMATCH" in sig_types else (
                    "REGULATORY_AUTHORITY_CLAIM" if "REGULATORY_AUTHORITY_CLAIM" in sig_types else "AUTHORITY_IMPERSONATION"
                )
            )
            combinations.append(ThreatCombination(
                combination=[
                    lead_sig,
                    "PRIVATE_CHANNEL_MIGRATION",
                    "PAYMENT_REQUEST"
                ],
                mechanism="trust_migration_to_payment_transition",
                confidence=0.92,
                description=(
                    "Content leverages unverified regulatory or authority claims to move the user "
                    "into private communication channels, culminating in a direct payment request."
                )
            ))
            threat_families.add("INVESTMENT_PROMOTION_SCAM")
            threat_families.add("PAYMENT_FRAUD")

        # Combination 2: Guaranteed Returns + Regulatory Conflict + External App / Channel
        if (
            has_signal("GUARANTEED_RETURN_LANGUAGE", "REGULATORY_CLAIM_CONFLICT")
            and has_signal("PRIVATE_CHANNEL_MIGRATION", "EXTERNAL_APP")
        ):
            combinations.append(ThreatCombination(
                combination=[
                    "GUARANTEED_RETURN_LANGUAGE",
                    "REGULATORY_CLAIM_CONFLICT" if "REGULATORY_CLAIM_CONFLICT" in sig_types else "GUARANTEED_RETURN_LANGUAGE",
                    "EXTERNAL_APP" if "EXTERNAL_APP" in sig_types else "PRIVATE_CHANNEL_MIGRATION"
                ],
                mechanism="prohibited_return_app_distribution",
                confidence=0.90,
                description=(
                    "Promises of guaranteed returns (conflicting with regulatory standards) are coupled with "
                    "solicitations to download external software or enter private discussion groups."
                )
            ))
            threat_families.add("INVESTMENT_PROMOTION_SCAM")

        # Combination 3: Regulatory Impersonation / Unsubstantiated Authority
        if has_signal("AUTHORITY_IMPERSONATION") or has_signal("IDENTITY_MISMATCH"):
            combinations.append(ThreatCombination(
                combination=[
                    "AUTHORITY_IMPERSONATION" if "AUTHORITY_IMPERSONATION" in sig_types else "IDENTITY_MISMATCH",
                    "IDENTITY_MISMATCH" if "IDENTITY_MISMATCH" in sig_types else "AUTHORITY_IMPERSONATION"
                ],
                mechanism="unsubstantiated_regulatory_authority",
                confidence=0.94,
                description=(
                    "Official registry verification contradicts claimed regulatory authority or establishes identity mismatch."
                )
            ))
            threat_families.add("REGULATORY_IMPERSONATION")
            threat_families.add("IDENTITY_IMPERSONATION")
        elif (
            has_signal("REGULATORY_AUTHORITY_CLAIM", "AUTHORITY_CLAIM")
            and has_signal("IDENTITY_NOT_ESTABLISHED")
        ):
            combinations.append(ThreatCombination(
                combination=[
                    "REGULATORY_AUTHORITY_CLAIM" if "REGULATORY_AUTHORITY_CLAIM" in sig_types else "AUTHORITY_CLAIM",
                    "IDENTITY_NOT_ESTABLISHED"
                ],
                mechanism="unsubstantiated_regulatory_authority",
                confidence=0.88,
                description=(
                    "Content explicitly asserts official regulatory status (e.g. SEBI registered), "
                    "yet official registry lookups returned no matching records."
                )
            ))
            # Note: Do not escalate to REGULATORY_IMPERSONATION without identity mismatch evidence

        # Combination 4: Software Installation + Financial Transfer
        if has_signal("EXTERNAL_APP") and has_signal("PAYMENT_REQUEST"):
            combinations.append(ThreatCombination(
                combination=["EXTERNAL_APP", "PAYMENT_REQUEST"],
                mechanism="external_app_monetary_solicitation",
                confidence=0.88,
                description="Interaction instructs downloading external application software accompanied by fee payments."
            ))
            threat_families.add("PAYMENT_FRAUD")
            if has_signal("PRIVATE_CHANNEL_MIGRATION", "AUTHORITY_IMPERSONATION", "REGULATORY_AUTHORITY_CLAIM"):
                threat_families.add("MALICIOUS_SOFTWARE")

        # Combination 5: Credential / OTP Capture in Unverified Channel
        if has_signal("CREDENTIAL_REQUEST", "OTP_REQUEST") and has_signal("PRIVATE_CHANNEL_MIGRATION", "EXTERNAL_DOMAIN"):
            combinations.append(ThreatCombination(
                combination=[
                    "OTP_REQUEST" if "OTP_REQUEST" in sig_types else "CREDENTIAL_REQUEST",
                    "PRIVATE_CHANNEL_MIGRATION" if "PRIVATE_CHANNEL_MIGRATION" in sig_types else "EXTERNAL_DOMAIN"
                ],
                mechanism="private_channel_credential_harvesting",
                confidence=0.96,
                description="Solicitation of authentication credentials or OTPs through private channels or unverified web links."
            ))
            threat_families.add("CREDENTIAL_HARVESTING")
            threat_families.add("ACCOUNT_TAKEOVER")

        # Combination 6: Social Engineering (Urgency + FOMO + Secrecy + Payment)
        if (
            has_signal("URGENCY", "FOMO", "ISOLATION_LANGUAGE")
            and has_signal("PAYMENT_REQUEST", "CREDENTIAL_REQUEST", "UPFRONT_FEE")
        ):
            combinations.append(ThreatCombination(
                combination=[
                    "URGENCY" if "URGENCY" in sig_types else "FOMO",
                    "PAYMENT_REQUEST" if "PAYMENT_REQUEST" in sig_types else "CREDENTIAL_REQUEST"
                ],
                mechanism="psychological_urgency_solicitation",
                confidence=0.85,
                description="Manipulative psychological cues (urgency, FOMO, or secrecy) utilized to expedite irreversible user actions."
            ))
            threat_families.add("SOCIAL_ENGINEERING")

        # -----------------------------------------------------------------
        # 2. Strict Negative Handling & Guardrails
        # -----------------------------------------------------------------
        # A. Telegram alone without authority claims or payment requests -> NO threat family
        if len(sig_types) == 1 and "PRIVATE_CHANNEL_MIGRATION" in sig_types:
            threat_families.clear()
            combinations.clear()

        # B. General payment mention alone (e.g. "Course fee is ₹500") without trust/authority or private channel -> NO threat family
        if len(sig_types) == 1 and "PAYMENT_REQUEST" in sig_types:
            threat_families.clear()
            combinations.clear()

        # C. Simple educational or informational content without actions -> NO threat family
        if not high_impact_actions and not has_signal("PAYMENT_REQUEST", "CREDENTIAL_REQUEST", "OTP_REQUEST", "EXTERNAL_APP"):
            if not has_signal("IDENTITY_NOT_ESTABLISHED", "REGULATORY_CLAIM_CONFLICT"):
                threat_families.clear()
                combinations.clear()

        return combinations, sorted(list(threat_families))
