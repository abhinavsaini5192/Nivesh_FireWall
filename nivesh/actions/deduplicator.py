"""Action deduplication component for Engine 3.

Merges identical recurring actions within the same content item:
- Groups actions by canonical fingerprint or (action_type, target.type, target.value)
- Consolidates occurrences into `source_spans`
- Preserves the earliest presentation order and highest confidence
- Re-indexes sequence numbers seamlessly.
"""

from nivesh.schemas.actions import CanonicalAction, ActionSequence


class ActionDeduplicator:
    """Deduplicates repeated identical actions within the same content item."""

    def deduplicate(self, actions: list[CanonicalAction]) -> tuple[list[CanonicalAction], int]:
        """Merges duplicate actions and populates source_spans.
        
        Returns:
            (deduplicated_actions, duplicate_count)
        """
        if not actions:
            return [], 0

        deduped: list[CanonicalAction] = []
        # Key: (action_type, target.type, target.value)
        seen_keys: dict[tuple, CanonicalAction] = {}
        merged_count = 0

        for act in actions:
            # Normalize target value for key
            t_val = (act.target.value or "").lower().strip()
            key = (act.action_type, act.target.type, t_val)

            if key in seen_keys:
                existing = seen_keys[key]
                # Merge span into existing.source_spans
                if not existing.source_spans:
                    existing.source_spans = [existing.source_span]
                existing.source_spans.append(act.source_span)
                # Keep highest confidence
                existing.confidence = max(existing.confidence, act.confidence)
                # Merge parameters
                for k, v in act.parameters.items():
                    if k not in existing.parameters:
                        existing.parameters[k] = v
                # Merge rationale claims
                for cid in act.rationale_claim_ids:
                    if cid not in existing.rationale_claim_ids:
                        existing.rationale_claim_ids.append(cid)
                merged_count += 1
            else:
                act.source_spans = [act.source_span]
                seen_keys[key] = act
                deduped.append(act)

        # Re-index sequence numbers sequentially
        for idx, act in enumerate(deduped, start=1):
            act.sequence = ActionSequence(index=idx)
            act.action_id = f"ACTION-{idx:03d}"

        return deduped, merged_count
