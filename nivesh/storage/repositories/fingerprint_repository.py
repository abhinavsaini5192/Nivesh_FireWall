"""Persistent Scam Fingerprint Repository for Engine 7.

Stores collective threat fingerprints, observation histories, multi-variant consolidation,
lifecycle state changes, and dispute records in relational storage.
Preserves duplicate-origin copy-amplification safeguards and concurrency guarantees.
Contains NO personal data or credentials.
"""

import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, select

from nivesh.schemas.fingerprint import (
    ScamFingerprint,
    FingerprintObservation,
    FingerprintStatus,
)
from nivesh.storage.models import (
    FingerprintModel,
    FingerprintObservationModel,
)
from nivesh.storage.database import get_db_session


def _model_to_pydantic(m: FingerprintModel) -> ScamFingerprint:
    """Convert SQLAlchemy FingerprintModel to Pydantic ScamFingerprint."""
    return ScamFingerprint(
        fingerprint_id=m.fingerprint_id,
        schema_version=m.schema_version,
        identity_patterns=list(m.identity_patterns or []),
        claim_patterns=list(m.claim_patterns or []),
        action_patterns=list(m.action_patterns or []),
        channel_patterns=list(m.channel_patterns or []),
        technical_patterns=list(m.technical_patterns or []),
        threat_patterns=list(m.threat_patterns or []),
        attack_stages=list(m.attack_stages or []),
        attack_transitions=list(m.attack_transitions or []),
        evidence_patterns=list(m.evidence_patterns or []),
        threat_families=list(m.threat_families or []),
        canonical_features=list(m.canonical_features or []),
        exact_signature=m.exact_signature,
        semantic_signature=m.semantic_signature,
        attack_path_signature=m.attack_path_signature or "",
        created_at=m.created_at,
        updated_at=m.updated_at,
        first_seen=m.first_seen,
        last_seen=m.last_seen,
        observation_count=m.observation_count,
        distinct_channels=list(m.distinct_channels or []),
        distinct_variants=m.distinct_variants,
        status=m.status,  # type: ignore
        dispute_count=m.dispute_count,
        dispute_notes=list(m.dispute_notes or []),
        status_change_history=list(m.status_change_history or []),
        related_fingerprint_ids=list(m.related_fingerprint_ids or []),
        content_hashes=list(m.content_hashes or []),
        description=m.description or "",
    )


def _obs_model_to_pydantic(m: FingerprintObservationModel) -> FingerprintObservation:
    """Convert SQLAlchemy FingerprintObservationModel to Pydantic FingerprintObservation."""
    return FingerprintObservation(
        observation_id=m.observation_id,
        fingerprint_id=m.fingerprint_id,
        content_id=m.content_id,
        observed_at=m.observed_at,
        channel=m.channel,
        features=list(m.features or []),
        content_hash=m.content_hash,
        is_duplicate_origin=m.is_duplicate_origin,
        match_type=m.match_type,  # type: ignore
        match_confidence=m.match_confidence,
        matched_dimensions=list(m.matched_dimensions or []),
        provenance=dict(m.provenance or {}),
    )


class SqlAlchemyFingerprintRepository:
    """Thread-safe persistent repository for Engine 7 scam fingerprints and observations."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory
        self._lock = threading.RLock()

    def add_fingerprint(self, fp: ScamFingerprint) -> ScamFingerprint:
        """Persist a new or updated ScamFingerprint."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                existing = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fp.fingerprint_id)
                    .first()
                )

                if existing:
                    # Update fields
                    existing.schema_version = fp.schema_version
                    existing.identity_patterns = fp.identity_patterns
                    existing.claim_patterns = fp.claim_patterns
                    existing.action_patterns = fp.action_patterns
                    existing.channel_patterns = fp.channel_patterns
                    existing.technical_patterns = fp.technical_patterns
                    existing.threat_patterns = fp.threat_patterns
                    existing.attack_stages = fp.attack_stages
                    existing.attack_transitions = fp.attack_transitions
                    existing.evidence_patterns = fp.evidence_patterns
                    existing.threat_families = fp.threat_families
                    existing.canonical_features = fp.canonical_features
                    existing.exact_signature = fp.exact_signature
                    existing.semantic_signature = fp.semantic_signature
                    existing.attack_path_signature = fp.attack_path_signature
                    existing.updated_at = fp.updated_at
                    existing.first_seen = fp.first_seen
                    existing.last_seen = fp.last_seen
                    existing.observation_count = fp.observation_count
                    existing.distinct_channels = fp.distinct_channels
                    existing.distinct_variants = fp.distinct_variants
                    existing.status = fp.status
                    existing.dispute_count = fp.dispute_count
                    existing.dispute_notes = fp.dispute_notes
                    existing.status_change_history = fp.status_change_history
                    existing.related_fingerprint_ids = fp.related_fingerprint_ids
                    existing.content_hashes = fp.content_hashes
                    existing.description = fp.description
                else:
                    new_model = FingerprintModel(
                        fingerprint_id=fp.fingerprint_id,
                        schema_version=fp.schema_version,
                        identity_patterns=fp.identity_patterns,
                        claim_patterns=fp.claim_patterns,
                        action_patterns=fp.action_patterns,
                        channel_patterns=fp.channel_patterns,
                        technical_patterns=fp.technical_patterns,
                        threat_patterns=fp.threat_patterns,
                        attack_stages=fp.attack_stages,
                        attack_transitions=fp.attack_transitions,
                        evidence_patterns=fp.evidence_patterns,
                        threat_families=fp.threat_families,
                        canonical_features=fp.canonical_features,
                        exact_signature=fp.exact_signature,
                        semantic_signature=fp.semantic_signature,
                        attack_path_signature=fp.attack_path_signature,
                        created_at=fp.created_at,
                        updated_at=fp.updated_at,
                        first_seen=fp.first_seen,
                        last_seen=fp.last_seen,
                        observation_count=fp.observation_count,
                        distinct_channels=fp.distinct_channels,
                        distinct_variants=fp.distinct_variants,
                        status=fp.status,
                        dispute_count=fp.dispute_count,
                        dispute_notes=fp.dispute_notes,
                        status_change_history=fp.status_change_history,
                        related_fingerprint_ids=fp.related_fingerprint_ids,
                        content_hashes=fp.content_hashes,
                        description=fp.description,
                    )
                    session.add(new_model)

                return fp

    def get_fingerprint(self, fingerprint_id: str) -> Optional[ScamFingerprint]:
        """Retrieve a fingerprint by ID."""
        with get_db_session(session_factory=self._session_factory) as session:
            m = (
                session.query(FingerprintModel)
                .filter(FingerprintModel.fingerprint_id == fingerprint_id)
                .first()
            )
            return _model_to_pydantic(m) if m else None

    def get_by_exact_signature(self, exact_signature: str) -> Optional[ScamFingerprint]:
        """Fast lookup by exact canonical signature."""
        with get_db_session(session_factory=self._session_factory) as session:
            m = (
                session.query(FingerprintModel)
                .filter(FingerprintModel.exact_signature == exact_signature)
                .first()
            )
            return _model_to_pydantic(m) if m else None

    def get_candidates(self, features: dict[str, Any]) -> list[ScamFingerprint]:
        """Retrieve candidate fingerprints for deep comparison using index lookups."""
        exact_sig = features.get("exact_signature")
        sem_sig = features.get("semantic_signature")
        path_sig = features.get("attack_path_signature")
        threat_families = features.get("threat_families", [])

        with get_db_session(session_factory=self._session_factory) as session:
            clauses = []
            if exact_sig:
                clauses.append(FingerprintModel.exact_signature == exact_sig)
            if sem_sig:
                clauses.append(FingerprintModel.semantic_signature == sem_sig)
            if path_sig:
                clauses.append(FingerprintModel.attack_path_signature == path_sig)

            candidates: list[FingerprintModel] = []
            if clauses:
                candidates = (
                    session.query(FingerprintModel)
                    .filter(or_(*clauses))
                    .all()
                )

            # Check threat family matches if needed or return all active if candidate pool empty
            if not candidates:
                all_fps = session.query(FingerprintModel).all()
                if threat_families:
                    filtered = [
                        fp for fp in all_fps
                        if any(fam in (fp.threat_families or []) for fam in threat_families)
                    ]
                    if filtered:
                        return [_model_to_pydantic(fp) for fp in filtered]
                return [_model_to_pydantic(fp) for fp in all_fps]

            return [_model_to_pydantic(c) for c in candidates]

    def record_observation(
        self,
        fingerprint_id: str,
        observation: FingerprintObservation,
        content_hash: Optional[str] = None,
    ) -> None:
        """Consolidates an observation against a fingerprint with duplicate-origin safeguards."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                fp = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fingerprint_id)
                    .first()
                )
                if not fp:
                    return

                now_iso = datetime.now(timezone.utc).isoformat()
                fp.last_seen = now_iso
                fp.updated_at = now_iso

                # Check copy amplification duplicate origin
                is_dup = False
                hashes = list(fp.content_hashes or [])
                if content_hash:
                    if content_hash in hashes:
                        # Message was identical copy from same source
                        is_dup = True
                        observation.is_duplicate_origin = True
                    else:
                        hashes.append(content_hash)
                        fp.content_hashes = hashes

                if not is_dup:
                    fp.observation_count += 1

                # Track distinct channels
                channels = list(fp.distinct_channels or [])
                if observation.channel and observation.channel not in channels:
                    channels.append(observation.channel)
                    fp.distinct_channels = channels

                # Track distinct variants
                if observation.match_type == "SEMANTIC_VARIANT":
                    fp.distinct_variants += 1

                # Lifecycle promotion: promote NEW to ACTIVE on >= 2 independent observations
                if fp.status == "NEW" and fp.observation_count >= 2:
                    fp.status = "ACTIVE"
                    history = list(fp.status_change_history or [])
                    history.append({
                        "from_status": "NEW",
                        "to_status": "ACTIVE",
                        "timestamp": now_iso,
                        "reason": f"Promoted to ACTIVE upon reaching {fp.observation_count} observations",
                    })
                    fp.status_change_history = history

                # Record Observation Model
                obs_model = FingerprintObservationModel(
                    observation_id=observation.observation_id,
                    fingerprint_id=fingerprint_id,
                    content_id=observation.content_id,
                    observed_at=observation.observed_at,
                    channel=observation.channel,
                    features=observation.features,
                    content_hash=content_hash,
                    is_duplicate_origin=is_dup,
                    match_type=observation.match_type,
                    match_confidence=observation.match_confidence,
                    matched_dimensions=observation.matched_dimensions,
                    provenance=observation.provenance,
                )
                session.add(obs_model)

    def dispute_fingerprint(
        self,
        fingerprint_id: str,
        reason: str,
        actor: Optional[str] = None,
    ) -> Optional[ScamFingerprint]:
        """Registers a user or analyst dispute for a fingerprint without deleting history."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                fp = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fingerprint_id)
                    .first()
                )
                if not fp:
                    return None

                now_iso = datetime.now(timezone.utc).isoformat()
                old_status = fp.status
                fp.status = "DISPUTED"
                fp.dispute_count += 1

                notes = list(fp.dispute_notes or [])
                notes.append(f"[{now_iso}] {reason}")
                fp.dispute_notes = notes
                fp.updated_at = now_iso

                history = list(fp.status_change_history or [])
                history.append({
                    "from_status": old_status,
                    "to_status": "DISPUTED",
                    "timestamp": now_iso,
                    "reason": reason,
                    "actor": actor or "user",
                })
                fp.status_change_history = history
                session.flush()
                return _model_to_pydantic(fp)

    def mark_stale_if_inactive(
        self,
        fingerprint_id: str,
        threshold_days: int = 90,
    ) -> bool:
        """Transitions a fingerprint to STALE if no observations seen within threshold."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                fp = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fingerprint_id)
                    .first()
                )
                if not fp or fp.status in ("ARCHIVED", "DISPUTED"):
                    return False

                now = datetime.now(timezone.utc)
                try:
                    last_dt = datetime.fromisoformat(fp.last_seen)
                except Exception:
                    return False

                if now - last_dt > timedelta(days=threshold_days):
                    old_status = fp.status
                    fp.status = "STALE"
                    fp.updated_at = now.isoformat()
                    history = list(fp.status_change_history or [])
                    history.append({
                        "from_status": old_status,
                        "to_status": "STALE",
                        "timestamp": now.isoformat(),
                        "reason": f"No observations in {threshold_days} days",
                    })
                    fp.status_change_history = history
                    return True
                return False

    def archive_fingerprint(
        self,
        fingerprint_id: str,
        reason: str = "Archived by policy",
    ) -> Optional[ScamFingerprint]:
        """Archives a fingerprint."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                fp = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fingerprint_id)
                    .first()
                )
                if not fp:
                    return None

                now_iso = datetime.now(timezone.utc).isoformat()
                old_status = fp.status
                fp.status = "ARCHIVED"
                fp.updated_at = now_iso
                history = list(fp.status_change_history or [])
                history.append({
                    "from_status": old_status,
                    "to_status": "ARCHIVED",
                    "timestamp": now_iso,
                    "reason": reason,
                })
                fp.status_change_history = history
                session.flush()
                return _model_to_pydantic(fp)

    def link_related_fingerprints(self, fp_id_1: str, fp_id_2: str) -> None:
        """Establishes a bi-directional structural relationship between two fingerprints."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                fp1 = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fp_id_1)
                    .first()
                )
                fp2 = (
                    session.query(FingerprintModel)
                    .filter(FingerprintModel.fingerprint_id == fp_id_2)
                    .first()
                )
                if fp1:
                    rel1 = list(fp1.related_fingerprint_ids or [])
                    if fp_id_2 not in rel1:
                        rel1.append(fp_id_2)
                        fp1.related_fingerprint_ids = rel1
                if fp2:
                    rel2 = list(fp2.related_fingerprint_ids or [])
                    if fp_id_1 not in rel2:
                        rel2.append(fp_id_1)
                        fp2.related_fingerprint_ids = rel2

    def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        threat_family: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> list[ScamFingerprint]:
        """Searches fingerprints by status, threat family, channel, or keyword."""
        with get_db_session(session_factory=self._session_factory) as session:
            q = session.query(FingerprintModel)
            if status:
                q = q.filter(FingerprintModel.status == status.upper())

            results = [_model_to_pydantic(m) for m in q.all()]

            if threat_family:
                tf_lower = threat_family.lower()
                results = [
                    fp for fp in results
                    if any(tf_lower in f.lower() for f in fp.threat_families)
                ]

            if channel:
                ch_lower = channel.lower()
                results = [
                    fp for fp in results
                    if any(ch_lower in c.lower() for c in (fp.distinct_channels or fp.channel_patterns))
                ]

            if query:
                q_lower = query.lower()
                results = [
                    fp for fp in results
                    if q_lower in fp.fingerprint_id.lower()
                    or q_lower in fp.description.lower()
                    or any(q_lower in feat.lower() for feat in fp.canonical_features)
                ]

            return results

    def list_observations(self, fingerprint_id: str) -> list[FingerprintObservation]:
        """Returns all recorded observations for a fingerprint."""
        with get_db_session(session_factory=self._session_factory) as session:
            records = (
                session.query(FingerprintObservationModel)
                .filter(FingerprintObservationModel.fingerprint_id == fingerprint_id)
                .order_by(FingerprintObservationModel.observed_at.asc())
                .all()
            )
            return [_obs_model_to_pydantic(r) for r in records]

    def reset(self) -> None:
        """Clears all stored fingerprints and observations (used in tests)."""
        with self._lock:
            with get_db_session(session_factory=self._session_factory) as session:
                session.query(FingerprintObservationModel).delete()
                session.query(FingerprintModel).delete()
