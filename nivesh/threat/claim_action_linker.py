"""Claim-to-Action Linker for Engine 6.

Establishes explicit semantic connections between claims (assertions of fact or authority)
and requested actions (instructions or solicitations directed at the user).

Answers:
- Which claim provides the rationale for which action?
- Which assertion justifies or enables a subsequent user instruction?
"""

from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.threat import ClaimActionLink, ClaimActionLinkType


class ClaimActionLinker:
    """Discovers semantic linkages between canonical claims and canonical actions."""

    @classmethod
    def link_claims_and_actions(
        cls,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
    ) -> list[ClaimActionLink]:
        """Maps claims to requested actions with semantic link types."""
        links: list[ClaimActionLink] = []
        link_counter = 1

        if not claims.claims or not actions.actions:
            return links

        for claim in claims.claims:
            pred_upper = (claim.predicate or "").upper()
            claim_type = (claim.claim_type or "").upper()
            subject_str = (claim.subject or "").lower()

            for action in actions.actions:
                atype = (action.action_type or "").upper()
                desc = getattr(action, "description", None) or (
                    ((action.text.original or "") + " " + (action.text.normalized or "")).lower()
                    if action.text else ""
                )
                target_str = str(action.target.value or "").lower() if action.target else ""

                # 1. Direct RATIONALE link: Action explicitly references claim ID or rationale
                action_rat = getattr(action, "rationale", None) or ""
                if claim.claim_id in getattr(action, "rationale_claim_ids", []) or (
                    action_rat and (
                        claim.predicate.lower() in action_rat.lower()
                        or (claim.subject and claim.subject.lower() in action_rat.lower())
                        or (claim.object and str(claim.object).lower() in action_rat.lower())
                    )
                ):
                    links.append(ClaimActionLink(
                        link_id=f"CAL-{link_counter:03d}",
                        claim_id=claim.claim_id,
                        action_id=action.action_id,
                        type="RATIONALE_FOR",
                        confidence=0.92,
                        explanation=f"Action '{action.action_type}' explicitly cites claim '{claim.predicate}' as its justifying rationale."
                    ))
                    link_counter += 1
                    continue

                # 2. Authority / Regulatory Trust Claim -> Private Channel / App / Contact Action
                if claim_type in ("REGULATORY", "IDENTITY") or pred_upper in ("REGISTERED_WITH", "LICENSED_BY"):
                    if atype in ("JOIN_CHANNEL", "DOWNLOAD", "CONTACT", "PAYMENT"):
                        links.append(ClaimActionLink(
                            link_id=f"CAL-{link_counter:03d}",
                            claim_id=claim.claim_id,
                            action_id=action.action_id,
                            type="JUSTIFIES",
                            confidence=0.88,
                            explanation=(
                                f"Regulatory identity assertion '{claim.subject} registered with {claim.object}' "
                                f"serves as trust foundation to justify requesting action '{action.action_type}'."
                            )
                        ))
                        link_counter += 1
                        continue

                # 3. Guaranteed Return / Financial Promise -> Payment / Download Action
                if pred_upper in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN") or "returns" in str(claim.object).lower():
                    if atype in ("PAYMENT", "DOWNLOAD", "JOIN_CHANNEL"):
                        links.append(ClaimActionLink(
                            link_id=f"CAL-{link_counter:03d}",
                            claim_id=claim.claim_id,
                            action_id=action.action_id,
                            type="ENABLES",
                            confidence=0.90,
                            explanation=(
                                f"Financial return guarantee of '{claim.object}' acts as commercial incentive "
                                f"to induce user into executing action '{action.action_type}'."
                            )
                        ))
                        link_counter += 1
                        continue

                # 4. Sequential or Discourse Proximity Linking
                # If content mentions a claim right before requesting an action
                if atype == "REQUEST_INFO" or atype == "ENTER_CREDENTIALS":
                    links.append(ClaimActionLink(
                        link_id=f"CAL-{link_counter:03d}",
                        claim_id=claim.claim_id,
                        action_id=action.action_id,
                        type="PRECEDES",
                        confidence=0.75,
                        explanation=f"Assertion '{claim.predicate}' establishes engagement context preceding data collection request '{action.action_type}'."
                    ))
                    link_counter += 1

        return links
