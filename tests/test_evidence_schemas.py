"""Unit tests for Evidence Verification schemas in Engine 5."""

import pytest
from pydantic import ValidationError
from nivesh.schemas.evidence import (
    ClaimVerificationStatus,
    EvidenceRelationType,
    EvidenceStrength,
    EvidenceItemEvaluation,
    SourceAssessmentItem,
    VerificationProvenance,
    VerificationResult,
    EvidenceAnalysisMetadata,
    EvidenceAnalysis,
)


def test_verification_result_schema_valid():
    res = VerificationResult(
        claim_id="CLAIM-001",
        status="SUPPORTED",
        confidence=0.95,
        evidence_strength="HIGH",
        supporting_evidence=[
            EvidenceItemEvaluation(
                evidence_id="EVID-001",
                source_document_id="DOC-001",
                source_url="https://www.nseindia.com",
                organization="NSE",
                relation="SUPPORTS",
                excerpt="Company announced 1:1 bonus issue.",
                reasoning="Direct confirmation in exchange filing.",
                matched_signals=["1:1", "bonus"]
            )
        ],
        contradicting_evidence=[],
        missing_elements=[],
        context_gaps=["Reporting date omitted"],
        source_assessment=[
            SourceAssessmentItem(
                source_id="nse_corporate_actions",
                organization="NSE",
                authority_tier="PRIMARY_OFFICIAL",
                retrieval_status="SUCCESS",
                relevance_summary="Direct corporate action filing"
            )
        ],
        reasoning_trace=["1. Claim matched with official filing"],
        uncertainty=[],
        provenance=VerificationProvenance(
            engine_version="1.0.0",
            verification_method="hybrid",
            verified_at="2026-10-02T12:00:00Z"
        )
    )

    assert res.claim_id == "CLAIM-001"
    assert res.status == "SUPPORTED"
    assert res.confidence == 0.95
    assert res.evidence_strength == "HIGH"
    assert len(res.supporting_evidence) == 1
    assert len(res.context_gaps) == 1


def test_evidence_analysis_schema_valid():
    analysis = EvidenceAnalysis(
        content_id="content-uuid-123",
        verifications=[],
        analysis_metadata=EvidenceAnalysisMetadata(
            total_claims=2,
            claims_supported=1,
            claims_contradicted=1,
            processing_time_ms=12.4
        )
    )
    assert analysis.content_id == "content-uuid-123"
    assert analysis.analysis_metadata.total_claims == 2
    assert analysis.analysis_metadata.claims_supported == 1
