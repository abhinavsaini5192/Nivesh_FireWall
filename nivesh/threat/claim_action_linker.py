"""Claim-to-Action Linker for Engine 6.

Establishes explicit semantic connections between claims (assertions of fact or authority)
and requested actions (instructions or solicitations directed at the user).

Core Principle:
A claim→action relationship must be created only when:
1. The source text explicitly links the claim to the action, OR
2. The relationship is strongly and locally supported by explicit connective language.

Do NOT infer justification solely because:
- the claim appears near the action
- the claim appears earlier
- the same content contains both
- the entity mentioned in the claim is also associated with the action
"""

import re
from typing import Optional
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis, CanonicalClaim
from nivesh.schemas.actions import ActionAnalysis, CanonicalAction
from nivesh.schemas.threat import ClaimActionLink, ClaimActionLinkType


class ClaimActionLinker:
    """Discovers semantic linkages between canonical claims and canonical actions."""

    # Forward connectives (Claim precedes Action: "Claim, so Action")
    FORWARD_CONNECTIVE_PATTERN = re.compile(
        r"^\s*[,;]?\s*(?:so|therefore|hence|thus|in\s+order\s+to|to\s+enable)\b",
        re.IGNORECASE
    )

    # Backward connectives (Action precedes Claim: "Action because Claim")
    BACKWARD_CONNECTIVE_PATTERN = re.compile(
        r"^\s*[,;]?\s*(?:because|since|as)\b",
        re.IGNORECASE
    )

    # Contextual purpose/participation connectives linking return guarantee to payment action
    PURPOSE_PARTICIPATION_PATTERN = re.compile(
        r"\b(?:to\s+participate|to\s+qualify|for\s+returns|to\s+get\s+returns|to\s+receive\s+returns|fee\s+to|to\s+invest|to\s+join\s+the\s+plan)\b",
        re.IGNORECASE
    )

    @classmethod
    def _get_span(cls, obj, full_text: str) -> tuple[int, int]:
        """Resolves source character span for a claim or action."""
        if hasattr(obj, "source_span") and obj.source_span and (obj.source_span.start != 0 or obj.source_span.end != 0):
            return obj.source_span.start, obj.source_span.end
        if hasattr(obj, "text") and obj.text:
            if obj.text.original and obj.text.original in full_text:
                idx = full_text.find(obj.text.original)
                return idx, idx + len(obj.text.original)
            if obj.text.normalized and obj.text.normalized in full_text:
                idx = full_text.find(obj.text.normalized)
                return idx, idx + len(obj.text.normalized)
        return -1, -1

    @classmethod
    def link_claims_and_actions(
        cls,
        content: NormalizedContent,
        claims: ClaimAnalysis,
        actions: ActionAnalysis,
    ) -> list[ClaimActionLink]:
        """Maps claims to requested actions ONLY when explicit connectives exist."""
        links: list[ClaimActionLink] = []
        link_counter = 1
        seen_pairs: set[tuple[str, str]] = set()

        if not claims.claims or not actions.actions:
            return links

        full_text = ""
        if content.normalized and content.normalized.text:
            full_text = content.normalized.text
        elif content.raw and content.raw.text:
            full_text = content.raw.text
        elif hasattr(content, "raw_text") and content.raw_text:
            full_text = content.raw_text

        for claim in claims.claims:
            pred_upper = (claim.predicate or "").upper()
            claim_text = (claim.text.original if claim.text else "").lower()
            c_start, c_end = cls._get_span(claim, full_text)

            is_return_claim = (
                pred_upper in ("GUARANTEED_RETURN", "ASSURED_PROFIT", "FIXED_RETURN")
                or "return" in str(claim.object or "").lower()
                or "guaranteed" in claim_text
            )

            for action in actions.actions:
                pair_key = (claim.claim_id, action.action_id)
                if pair_key in seen_pairs:
                    continue

                atype = (action.action_type or "").upper()
                action_text = (action.text.original if action.text else "").lower()
                a_start, a_end = cls._get_span(action, full_text)

                is_payment_action = (
                    atype in ("PAYMENT", "TRANSFER_MONEY", "DEPOSIT_MONEY")
                    or action.category == "FINANCIAL_TRANSACTION"
                    or "pay" in action_text
                )

                # -------------------------------------------------------------
                # 1. Direct RATIONALE link: Action explicitly cites claim ID or rationale
                # -------------------------------------------------------------
                if claim.claim_id in getattr(action, "rationale_claim_ids", []):
                    links.append(ClaimActionLink(
                        link_id=f"CAL-{link_counter:03d}",
                        claim_id=claim.claim_id,
                        action_id=action.action_id,
                        type="RATIONALE_FOR",
                        confidence=0.95,
                        explanation=f"Action '{action.action_type}' explicitly cites claim '{claim.predicate}' as its justifying rationale."
                    ))
                    seen_pairs.add(pair_key)
                    link_counter += 1
                    continue

                action_rat = getattr(action, "rationale", None) or ""
                if action_rat and (
                    claim.predicate.lower() in action_rat.lower()
                    or (claim.subject and claim.subject.lower() in action_rat.lower())
                    or (claim.object and str(claim.object).lower() in action_rat.lower())
                ):
                    links.append(ClaimActionLink(
                        link_id=f"CAL-{link_counter:03d}",
                        claim_id=claim.claim_id,
                        action_id=action.action_id,
                        type="RATIONALE_FOR",
                        confidence=0.92,
                        explanation=f"Action '{action.action_type}' cites rationale '{action_rat}' matching claim '{claim.predicate}'."
                    ))
                    seen_pairs.add(pair_key)
                    link_counter += 1
                    continue

                # -------------------------------------------------------------
                # 2. Explicit connective language in source text
                # -------------------------------------------------------------
                if full_text and c_start >= 0 and c_end >= 0 and a_start >= 0 and a_end >= 0:
                    # Case 2A: Claim precedes Action (e.g. "SEBI approved this platform, so join Telegram")
                    if c_end <= a_start:
                        between = full_text[c_end:a_start]
                        # Check for explicit forward connective (e.g. ", so ", " therefore ")
                        if cls.FORWARD_CONNECTIVE_PATTERN.search(between):
                            m = cls.FORWARD_CONNECTIVE_PATTERN.search(between)
                            matched_conn = m.group(0).strip() if m else "so"
                            links.append(ClaimActionLink(
                                link_id=f"CAL-{link_counter:03d}",
                                claim_id=claim.claim_id,
                                action_id=action.action_id,
                                type="RATIONALE_FOR",
                                confidence=0.92,
                                explanation=(
                                    f"Claim '{claim.predicate}' is explicitly linked to action '{action.action_type}' "
                                    f"by connective language ('{matched_conn}')."
                                )
                            ))
                            seen_pairs.add(pair_key)
                            link_counter += 1
                            continue

                        # Case 2B: Contextual purpose connective linking return claim to payment
                        # e.g. "Guaranteed 40% returns. Pay ₹5,000 to participate."
                        if is_return_claim and is_payment_action:
                            if cls.PURPOSE_PARTICIPATION_PATTERN.search(action_text) or cls.PURPOSE_PARTICIPATION_PATTERN.search(between):
                                links.append(ClaimActionLink(
                                    link_id=f"CAL-{link_counter:03d}",
                                    claim_id=claim.claim_id,
                                    action_id=action.action_id,
                                    type="RATIONALE_FOR",
                                    confidence=0.90,
                                    explanation=(
                                        f"Return guarantee claim '{claim.predicate}' provides explicit rationale "
                                        f"for payment action '{action.action_type}' via contextual purpose connective ('to participate')."
                                    )
                                ))
                                seen_pairs.add(pair_key)
                                link_counter += 1
                                continue

                    # Case 2C: Action precedes Claim (e.g. "Join Telegram because SEBI approved this platform")
                    elif a_end <= c_start:
                        between = full_text[a_end:c_start]
                        if cls.BACKWARD_CONNECTIVE_PATTERN.search(between):
                            m = cls.BACKWARD_CONNECTIVE_PATTERN.search(between)
                            matched_conn = m.group(0).strip() if m else "because"
                            links.append(ClaimActionLink(
                                link_id=f"CAL-{link_counter:03d}",
                                claim_id=claim.claim_id,
                                action_id=action.action_id,
                                type="RATIONALE_FOR",
                                confidence=0.92,
                                explanation=(
                                    f"Action '{action.action_type}' explicitly cites claim '{claim.predicate}' "
                                    f"via causal connective ('{matched_conn}')."
                                )
                            ))
                            seen_pairs.add(pair_key)
                            link_counter += 1
                            continue

                # In the absence of explicit connective language or direct rationale reference:
                # Do NOT infer justification solely due to proximity or occurrence in the same document.
                # relationship = NONE

        return links
