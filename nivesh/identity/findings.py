"""Identity Findings Generator for Engine 9.

Constructs structured IdentityFinding instances with unique stable IDs,
standardized reason codes, upstream claim/source/evidence provenance links,
and objective non-accusatory descriptions.
"""

from typing import Any
from nivesh.identity.schemas import (
    IdentityFinding,
    IdentityFindingType,
)


class IdentityFindingGenerator:
    """Generates structured, traceable identity findings."""

    @classmethod
    def generate_findings(
        cls,
        finding_records: list[dict[str, Any]],
    ) -> list[IdentityFinding]:
        """Converts raw resolution and alignment records into formal IdentityFinding instances."""
        findings: list[IdentityFinding] = []
        counter = 1
        seen_keys: set[str] = set()

        for rec in finding_records:
            finding_type = rec.get("finding_type")
            if not finding_type:
                continue

            entity_id = rec.get("entity_id")
            if not entity_id and "entity" in rec:
                entity_id = rec["entity"].entity_id

            entity_id = str(entity_id or "UNKNOWN")
            basis = rec.get("basis", "")
            desc = rec.get("description") or basis

            # Deduplication key
            dedup_key = f"{finding_type.value}:{entity_id}:{basis[:60]}"
            if dedup_key in seen_keys:
                continue
            seen_keys.add(dedup_key)

            finding = IdentityFinding(
                finding_id=f"IDF-{counter:03d}",
                finding_type=finding_type if isinstance(finding_type, IdentityFindingType) else IdentityFindingType(finding_type),
                entity_id=entity_id,
                claim_id=rec.get("claim_id"),
                source_ids=rec.get("source_ids", []),
                evidence_ids=rec.get("evidence_ids", []),
                basis=basis,
                description=desc,
            )
            findings.append(finding)
            counter += 1

        return findings
