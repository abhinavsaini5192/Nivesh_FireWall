"""Provenance and Audit Trail Generator for Engine 9.

Tracks inputs, execution timestamps, source documents, evidence items,
and creates verifiable upstream reference mappings.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.sources import SourceAnalysis
from nivesh.schemas.evidence import EvidenceAnalysis
from nivesh.schemas.threat import ThreatAnalysis
from nivesh.identity.schemas import IdentityProvenance, ENGINE_VERSION


class ProvenanceBuilder:
    """Builds identity verification provenance and audit references."""

    @classmethod
    def build(
        cls,
        content: NormalizedContent,
        claims: Optional[ClaimAnalysis] = None,
        sources: Optional[SourceAnalysis] = None,
        evidence: Optional[EvidenceAnalysis] = None,
        threat: Optional[ThreatAnalysis] = None,
    ) -> tuple[IdentityProvenance, dict[str, Any]]:
        """Constructs IdentityProvenance and upstream reference dictionary."""
        source_doc_count = 0
        source_ids = []
        if sources:
            for csr in sources.claim_sources:
                source_doc_count += len(csr.documents)
                source_ids.extend([d.document_id for d in csr.documents])

        evidence_count = len(evidence.verifications) if evidence else 0
        evidence_ids = [vr.claim_id for vr in evidence.verifications] if evidence else []
        claim_count = len(claims.claims) if claims else 0
        claim_ids = [c.claim_id for c in claims.claims] if claims else []

        provenance = IdentityProvenance(
            engine_version=ENGINE_VERSION,
            verified_at=datetime.now(timezone.utc).isoformat(),
            input_content_id=content.content_id,
            claim_count=claim_count,
            source_document_count=source_doc_count,
            evidence_count=evidence_count,
        )

        upstream_references = {
            "content_id": content.content_id,
            "claim_ids": claim_ids,
            "source_ids": source_ids,
            "evidence_ids": evidence_ids,
            "threat_id": (getattr(threat, "analysis_id", None) or getattr(threat, "content_id", None)) if threat else None,
        }

        return provenance, upstream_references
