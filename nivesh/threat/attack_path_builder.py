"""Attack-Path Graph and Transition Builder for Engine 6.

Constructs an ordered sequence/graph of interaction stages and transitions
connecting claims, actions, and evidence items into a structured interaction path.

Stages:
DISCOVERY -> TRUST_BUILDING -> CHANNEL_MIGRATION -> NAVIGATION ->
SOFTWARE_INSTALLATION -> DATA_COLLECTION -> CREDENTIAL_CAPTURE ->
ACCOUNT_ACCESS -> FINANCIAL_REQUEST -> FINANCIAL_TRANSFER
"""

from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.evidence import EvidenceAnalysis, VerificationResult
from nivesh.schemas.threat import (
    AttackStage,
    AttackNode,
    AttackTransition,
    AttackPath,
)


class AttackPathBuilder:
    """Builds structured attack path nodes and stage transitions."""

    # Stage canonical ordering
    STAGE_ORDER: list[AttackStage] = [
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
    def build_path(
        cls,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
        evidence: EvidenceAnalysis,
    ) -> tuple[AttackPath, list[AttackTransition]]:
        """Constructs AttackPath and detected stage transitions."""
        nodes: list[AttackNode] = []
        node_counter = 1

        stage_claims: dict[AttackStage, list[str]] = {s: [] for s in cls.STAGE_ORDER}
        stage_actions: dict[AttackStage, list[str]] = {s: [] for s in cls.STAGE_ORDER}
        stage_evidence: dict[AttackStage, list[str]] = {s: [] for s in cls.STAGE_ORDER}

        # Map verifications by claim_id
        verifications_by_claim = {v.claim_id: v for v in evidence.verifications}

        # ---------------------------------------------------------
        # 1. Map Claims to Stages
        # ---------------------------------------------------------
        for claim in claims.claims:
            pred_upper = (claim.predicate or "").upper()
            claim_type = (claim.claim_type or "").upper()

            # Authority, registration, guaranteed returns, or performance claims -> TRUST_BUILDING
            if (
                claim_type in ("REGULATORY", "IDENTITY")
                or pred_upper in ("REGISTERED_WITH", "LICENSED_BY", "GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN")
                or "guarantee" in (claim.text.original.lower() if claim.text else "")
            ):
                stage_claims["TRUST_BUILDING"].append(claim.claim_id)
                v = verifications_by_claim.get(claim.claim_id)
                if v:
                    for ev in v.supporting_evidence + v.contradicting_evidence:
                        stage_evidence["TRUST_BUILDING"].append(ev.evidence_id)
                    for rf in v.regulatory_findings:
                        if rf.source_document_id:
                            stage_evidence["TRUST_BUILDING"].append(rf.source_document_id)

        # ---------------------------------------------------------
        # 2. Map Actions to Stages
        # ---------------------------------------------------------
        for action in actions.actions:
            atype = (action.action_type or "").upper()
            target_val = str(action.target.value or "").lower() if action.target else ""
            desc = getattr(action, "description", None) or (
                ((action.text.original or "") + " " + (action.text.normalized or "")).lower()
                if action.text else ""
            )

            if atype == "JOIN_CHANNEL" or "telegram" in target_val or "whatsapp" in target_val:
                stage_actions["CHANNEL_MIGRATION"].append(action.action_id)
            elif atype in ("CLICK_LINK", "VISIT_WEBSITE", "NAVIGATE"):
                stage_actions["NAVIGATION"].append(action.action_id)
            elif atype in ("DOWNLOAD", "INSTALL_APP", "INSTALL_SOFTWARE") or "app" in target_val or ".apk" in target_val:
                stage_actions["SOFTWARE_INSTALLATION"].append(action.action_id)
            elif atype in ("REQUEST_INFO", "PROVIDE_KYC", "UPLOAD_DOCUMENT") or "identity" in target_val:
                stage_actions["DATA_COLLECTION"].append(action.action_id)
            elif atype in ("ENTER_CREDENTIALS", "PROVIDE_OTP") or "otp" in target_val or "password" in target_val:
                stage_actions["CREDENTIAL_CAPTURE"].append(action.action_id)
            elif atype == "AUTHORIZE_APP":
                stage_actions["ACCOUNT_ACCESS"].append(action.action_id)
            elif atype in ("PAYMENT", "TRANSFER_FUNDS", "PAY_FEE", "TRANSFER_MONEY") or "pay" in desc or "fee" in desc:
                stage_actions["FINANCIAL_REQUEST"].append(action.action_id)

        # ---------------------------------------------------------
        # 3. Form Nodes for Active Stages
        # ---------------------------------------------------------
        raw_text = ""
        if content.normalized and content.normalized.text:
            raw_text = content.normalized.text
        elif content.raw and content.raw.text:
            raw_text = content.raw.text
        elif hasattr(content, "raw_text") and content.raw_text:
            raw_text = content.raw_text

        # Add initial discovery node if there is content
        if raw_text:
            nodes.append(AttackNode(
                node_id=f"NODE-{node_counter:02d}",
                stage="DISCOVERY",
                type="financial_content_ingestion",
                label="Content Discovery & Initial Exposure",
                linked_claim_ids=[],
                linked_action_ids=[],
                evidence_ids=[]
            ))
            node_counter += 1

        active_stages: list[AttackStage] = []
        for stage in cls.STAGE_ORDER:
            c_ids = stage_claims[stage]
            a_ids = stage_actions[stage]
            e_ids = stage_evidence[stage]

            if c_ids or a_ids:
                active_stages.append(stage)
                nodes.append(AttackNode(
                    node_id=f"NODE-{node_counter:02d}",
                    stage=stage,
                    type=f"{stage.lower()}_stage",
                    label=cls._get_stage_label(stage, c_ids, a_ids),
                    linked_claim_ids=c_ids,
                    linked_action_ids=a_ids,
                    evidence_ids=e_ids
                ))
                node_counter += 1

        # ---------------------------------------------------------
        # 4. Form Sequential Transitions Between Active Stages
        # ---------------------------------------------------------
        transitions: list[AttackTransition] = []
        for i in range(len(active_stages) - 1):
            s_from = active_stages[i]
            s_to = active_stages[i + 1]

            supp_actions = stage_actions[s_to] or stage_actions[s_from]
            supp_claims = stage_claims[s_from] or stage_claims[s_to]

            transitions.append(AttackTransition(
                from_stage=s_from,
                to_stage=s_to,
                supporting_actions=supp_actions,
                supporting_claims=supp_claims,
                confidence=0.88,
                description=f"Interaction progresses from {s_from} to {s_to} via solicitations and authority assertions."
            ))

        entry_stage = active_stages[0] if active_stages else ("DISCOVERY" if raw_text else None)
        terminal_stage = active_stages[-1] if active_stages else ("DISCOVERY" if raw_text else None)

        attack_path = AttackPath(
            nodes=nodes,
            transitions=transitions,
            entry_stage=entry_stage,
            terminal_stage=terminal_stage
        )

        return attack_path, transitions

    @classmethod
    def _get_stage_label(
        cls,
        stage: AttackStage,
        claim_ids: list[str],
        action_ids: list[str]
    ) -> str:
        """Returns human-readable label for the stage."""
        labels = {
            "DISCOVERY": "Exposure to Financial Promotion",
            "TRUST_BUILDING": "Regulatory Authority & Return Guarantee Claims",
            "CHANNEL_MIGRATION": "Private Channel Migration (e.g. Telegram / WhatsApp)",
            "NAVIGATION": "Outbound Navigation to External Domain",
            "SOFTWARE_INSTALLATION": "External Application Installation",
            "DATA_COLLECTION": "Identity & KYC Information Gathering",
            "CREDENTIAL_CAPTURE": "Authentication Credential or OTP Solicitation",
            "ACCOUNT_ACCESS": "Third-Party App Account Delegation",
            "FINANCIAL_REQUEST": "Fee or Fund Transfer Solicitation",
            "FINANCIAL_TRANSFER": "Monetary Asset Transfer Execution",
        }
        return labels.get(stage, f"{stage} Stage")
