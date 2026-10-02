"""Action rationale linkage and relationship detector for Engine 3.

Links Engine 2 claims that serve as justification/rationale for an action
(e.g. 'Join our Telegram because SEBI approved this group' -> rationale_claim_ids = ['CLAIM-001']).
Also identifies sequential and enabling relationships between multiple actions
(e.g. 'Join Telegram to receive payment instructions' -> ENABLES / PRECEDES).
"""

from typing import Optional
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import CanonicalAction, ActionRelation


class ActionRationaleLinker:
    """Connects claims to actions as rationales and detects action-to-action relationships."""

    def link_rationales(
        self,
        action: CanonicalAction,
        rationale_text: Optional[str],
        claims: Optional[ClaimAnalysis] = None,
    ) -> None:
        """Links any matching claims from ClaimAnalysis to the action's rationale_claim_ids."""
        if not claims or not claims.claims:
            return

        if rationale_text:
            r_lower = rationale_text.lower().strip()
            for claim in claims.claims:
                c_orig = claim.text.original.lower()
                c_norm = claim.text.normalized.lower()
                # Check for textual overlap between rationale clause and claim
                if (r_lower in c_orig or c_orig in r_lower or
                    r_lower in c_norm or any(w in r_lower for w in ["sebi approved", "approved this", "registered advisor"])):
                    if claim.claim_id not in action.rationale_claim_ids:
                        action.rationale_claim_ids.append(claim.claim_id)

    def detect_action_relations(
        self,
        actions: list[CanonicalAction],
        full_text: str
    ) -> list[ActionRelation]:
        """Detects sequential and enabling relationships between multiple actions."""
        relations: list[ActionRelation] = []
        if len(actions) < 2:
            return relations

        t_lower = full_text.lower()

        # Check for explicitly connected actions:
        # e.g. "Join our Telegram group to receive the payment instructions"
        # -> ACTION-001 ENABLES ACTION-002
        for i in range(len(actions) - 1):
            act_a = actions[i]
            act_b = actions[i + 1]

            # If connected by "to receive", "to get", "in order to", "before"
            between_span = full_text[act_a.source_span.end:act_b.source_span.start].lower() if act_b.source_span.start >= act_a.source_span.end else ""
            if any(w in between_span for w in ["to receive", "to get", "in order to", "and then", "to"]):
                relations.append(ActionRelation(
                    source_action_id=act_a.action_id,
                    target_action_id=act_b.action_id,
                    relation_type="ENABLES",
                    confidence=0.90,
                    description=f"{act_a.action_type} enables {act_b.action_type}"
                ))
            else:
                # Default sequential precedence in the stated sequence
                relations.append(ActionRelation(
                    source_action_id=act_a.action_id,
                    target_action_id=act_b.action_id,
                    relation_type="PRECEDES",
                    confidence=0.85,
                    description=f"{act_a.action_type} precedes {act_b.action_type}"
                ))

        return relations
