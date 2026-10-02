"""Claim deduplication component for Engine 2.

Merges identical duplicate claims extracted from a single content item:
- Groups claims by canonical semantic fingerprint
- Preserves primary source span and appends recurring spans to attributes
- Prevents redundant downstream processing while maintaining provenance.
"""

from nivesh.schemas.claims import CanonicalClaim


class ClaimDeduplicator:
    """Deduplicates repeated identical assertions within the same content item."""

    def deduplicate(self, claims: list[CanonicalClaim]) -> tuple[list[CanonicalClaim], int]:
        """Merges duplicate claims with matching canonical fingerprints.
        
        Returns:
            (deduplicated_claims, duplicate_count)
        """
        if not claims:
            return [], 0

        deduped: list[CanonicalClaim] = []
        seen_fingerprints: dict[str, CanonicalClaim] = {}
        merged_count = 0

        for claim in claims:
            fp = claim.canonical_fingerprint
            if fp and fp in seen_fingerprints:
                existing = seen_fingerprints[fp]
                # Merge span into existing attributes
                if "additional_spans" not in existing.attributes:
                    existing.attributes["additional_spans"] = []
                existing.attributes["additional_spans"].append({
                    "start": claim.source_span.start,
                    "end": claim.source_span.end,
                    "text": claim.text.original
                })
                merged_count += 1
            else:
                if fp:
                    seen_fingerprints[fp] = claim
                deduped.append(claim)

        return deduped, merged_count
