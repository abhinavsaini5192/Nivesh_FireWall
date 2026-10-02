"""Provenance tracking for Engine 10: Behavioural Signal Intelligence.

Tracks upstream input references and execution audit metadata without storing PII.
"""

from datetime import datetime, timezone
from typing import Optional, Any
from nivesh.behaviour.schemas import BehaviouralProvenance, ENGINE_VERSION
from nivesh.behaviour.event_model import InteractionHistory
from nivesh.schemas.normalized import NormalizedContent
from nivesh.schemas.claims import ClaimAnalysis
from nivesh.schemas.actions import ActionAnalysis


def build_provenance(
    content: Optional[NormalizedContent] = None,
    claims: Optional[ClaimAnalysis] = None,
    actions: Optional[ActionAnalysis] = None,
    interaction_history: Optional[InteractionHistory] = None,
) -> BehaviouralProvenance:
    """Construct an execution audit trail for behavioural analysis."""
    now_iso = datetime.now(timezone.utc).isoformat()
    content_id = content.content_id if content else None
    claims_count = len(claims.claims) if claims and claims.claims else 0
    actions_count = len(actions.actions) if actions and actions.actions else 0
    events_count = len(interaction_history.events) if interaction_history and interaction_history.events else 0
    session_id = interaction_history.session_id if interaction_history else None

    return BehaviouralProvenance(
        engine_version=ENGINE_VERSION,
        analyzed_at=now_iso,
        content_id=content_id,
        claims_count=claims_count,
        actions_count=actions_count,
        events_count=events_count,
        session_id=session_id,
    )


def extract_upstream_references(
    content: Optional[NormalizedContent] = None,
    claims: Optional[ClaimAnalysis] = None,
    actions: Optional[ActionAnalysis] = None,
    threat: Optional[Any] = None,
    fingerprint: Optional[Any] = None,
    identity: Optional[Any] = None,
    interaction_history: Optional[InteractionHistory] = None,
) -> dict[str, Any]:
    """Compile structured references to upstream engines without circular imports."""
    refs: dict[str, Any] = {}
    if content and hasattr(content, "content_id"):
        refs["content_id"] = content.content_id
    if claims and hasattr(claims, "analysis_id"):
        refs["claim_analysis_id"] = claims.analysis_id
    if actions and hasattr(actions, "analysis_id"):
        refs["action_analysis_id"] = actions.analysis_id
    if threat and hasattr(threat, "analysis_id"):
        refs["threat_analysis_id"] = threat.analysis_id
    if fingerprint and hasattr(fingerprint, "analysis_id"):
        refs["fingerprint_analysis_id"] = fingerprint.analysis_id
    if identity and hasattr(identity, "analysis_id"):
        refs["identity_analysis_id"] = identity.analysis_id
    if interaction_history:
        refs["session_id"] = interaction_history.session_id

    return refs
