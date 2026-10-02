"""Impact and Evidence Weakness Evaluator for Engine 6.

Evaluates:
- High-Impact Actions: Categorizes potentially severe or irreversible user actions
  (CREDENTIAL, IDENTITY, DEVICE, FINANCIAL) and assesses reversibility.
- Evidence Weaknesses: Identifies gaps, missing verifications, and regulatory conflicts
  from Engine 5 that undermine the safety of the interaction path.
"""

from typing import Optional
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.evidence import EvidenceAnalysis, VerificationResult
from nivesh.schemas.threat import (
    HighImpactAction,
    ActionImpactCategory,
    ActionReversibility,
    EvidenceWeakness,
)


class ImpactEvaluator:
    """Evaluates high-impact actions and translates evidence gaps into threat weaknesses."""

    @classmethod
    def evaluate_high_impact_actions(
        cls,
        actions: ActionAnalysis
    ) -> list[HighImpactAction]:
        """Identifies actions carrying elevated consequence or irreversibility."""
        high_impact: list[HighImpactAction] = []

        for action in actions.actions:
            atype = (action.action_type or "").upper()
            target_str = str(action.target.value or "").lower() if action.target else ""
            desc = getattr(action, "description", None) or (
                ((action.text.original or "") + " " + (action.text.normalized or "")).lower()
                if action.text else ""
            )

            # 1. Financial Transfer / Upfront Payment
            if atype == "PAYMENT" or "pay" in desc or "transfer" in desc:
                high_impact.append(HighImpactAction(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    impact_category="FINANCIAL",
                    reversibility="IRREVERSIBLE",
                    description=(
                        "Direct financial transfers or upfront payments are difficult or impossible "
                        "to reverse once settled through banking or UPI rails."
                    )
                ))

            # 2. Software / Device Installation
            elif atype == "DOWNLOAD" or "app" in target_str or ".apk" in target_str:
                high_impact.append(HighImpactAction(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    impact_category="DEVICE",
                    reversibility="DIFFICULT_TO_REVERSE",
                    description=(
                        "Installing external applications grants executable code access on user devices, "
                        "risking persistent background observation or privilege escalation."
                    )
                ))

            # 3. Credential or OTP Disclosures
            elif atype in ("ENTER_CREDENTIALS", "SHARE_OTP", "PROVIDE_OTP") or "otp" in desc or "password" in desc:
                high_impact.append(HighImpactAction(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    impact_category="CREDENTIAL",
                    reversibility="IRREVERSIBLE",
                    description=(
                        "Sharing authentication credentials or OTPs enables immediate account compromise "
                        "and bypasses two-factor security controls."
                    )
                ))

            # 4. Identity / Document Uploads
            elif atype in ("UPLOAD_IDENTITY", "UPLOAD_DOCUMENT", "PROVIDE_KYC") or "aadhaar" in desc or "pan" in desc:
                high_impact.append(HighImpactAction(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    impact_category="IDENTITY",
                    reversibility="IRREVERSIBLE",
                    description=(
                        "Uploading government identity documents creates persistent risk of identity theft "
                        "or fraudulent account creation."
                    )
                ))

            # 5. Account Access Delegation
            elif atype == "AUTHORIZE_APP":
                high_impact.append(HighImpactAction(
                    action_id=action.action_id,
                    action_type=action.action_type,
                    impact_category="CREDENTIAL",
                    reversibility="DIFFICULT_TO_REVERSE",
                    description="Delegating third-party OAuth access can expose financial accounts or personal portfolios."
                ))

        return high_impact

    @classmethod
    def evaluate_evidence_weaknesses(
        cls,
        evidence: EvidenceAnalysis
    ) -> list[EvidenceWeakness]:
        """Translates Engine 5 evidence verification results into structured weaknesses."""
        weaknesses: list[EvidenceWeakness] = []
        ew_counter = 1

        for v in evidence.verifications:
            # 1. Regulatory conflict reported
            if v.regulatory_findings:
                for rf in v.regulatory_findings:
                    if rf.type == "REGULATORY_CONFLICT":
                        weaknesses.append(EvidenceWeakness(
                            weakness_id=f"EW-{ew_counter:03d}",
                            claim_id=v.claim_id,
                            weakness_type="REGULATORY_CONFLICT",
                            description=(
                                f"Claim conflicts with applicable statutory regulations: {rf.description}"
                            ),
                            evidence_status=v.status,
                            severity="HIGH"
                        ))
                        ew_counter += 1

            # 2. Identity or authority unestablished
            if v.status in ("INSUFFICIENT_EVIDENCE", "CONTRADICTED"):
                is_identity_weakness = any("registry" in step.lower() or "0 matches" in step.lower() for step in v.reasoning_trace)
                if is_identity_weakness:
                    weaknesses.append(EvidenceWeakness(
                        weakness_id=f"EW-{ew_counter:03d}",
                        claim_id=v.claim_id,
                        weakness_type="IDENTITY_NOT_ESTABLISHED",
                        description=(
                            "Claimed regulatory registration or entity identity could not be established "
                            "in official public registry records."
                        ),
                        evidence_status=v.status,
                        severity="HIGH"
                    ))
                    ew_counter += 1
                elif v.status == "CONTRADICTED":
                    weaknesses.append(EvidenceWeakness(
                        weakness_id=f"EW-{ew_counter:03d}",
                        claim_id=v.claim_id,
                        weakness_type="FACTUAL_CONTRADICTION",
                        description="Claim was directly contradicted by authoritative documentary filings.",
                        evidence_status=v.status,
                        severity="HIGH"
                    ))
                    ew_counter += 1
                elif v.status == "INSUFFICIENT_EVIDENCE":
                    weaknesses.append(EvidenceWeakness(
                        weakness_id=f"EW-{ew_counter:03d}",
                        claim_id=v.claim_id,
                        weakness_type="UNSUPPORTED_CLAIM",
                        description="Assertion lacks supporting documentary evidence in authoritative records.",
                        evidence_status=v.status,
                        severity="MEDIUM"
                    ))
                    ew_counter += 1

        return weaknesses
