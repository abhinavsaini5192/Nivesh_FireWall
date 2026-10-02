"""Fingerprint Repository and Collective Memory Store for Engine 7.

Maintains privacy-safe threat fingerprints, observation histories, multi-user consolidations,
lifecycle state transitions, and dispute records.
Prevents content amplification from inflating observation counts.
"""

import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from nivesh.schemas.fingerprint import (
    ScamFingerprint,
    FingerprintObservation,
    FingerprintStatus,
)


class FingerprintRepository:
    """Thread-safe collective intelligence repository for ScamFingerprints."""

    def __init__(self):
        self._lock = threading.RLock()
        self._fingerprints: dict[str, ScamFingerprint] = {}
        self._observations: dict[str, list[FingerprintObservation]] = {}
        self._content_hash_registry: dict[str, set[str]] = {}  # fingerprint_id -> set of content hashes

        # Accelerated Lookup Indexes
        self._exact_index: dict[str, str] = {}                 # exact_sig -> fp_id
        self._semantic_index: dict[str, set[str]] = {}          # semantic_sig -> set of fp_ids
        self._family_index: dict[str, set[str]] = {}            # threat_family -> set of fp_ids
        self._path_index: dict[str, set[str]] = {}              # attack_path_sig -> set of fp_ids

    def add_fingerprint(self, fp: ScamFingerprint) -> ScamFingerprint:
        """Stores a new ScamFingerprint and updates lookup indexes."""
        with self._lock:
            self._fingerprints[fp.fingerprint_id] = fp
            if fp.fingerprint_id not in self._observations:
                self._observations[fp.fingerprint_id] = []
            if fp.fingerprint_id not in self._content_hash_registry:
                self._content_hash_registry[fp.fingerprint_id] = set()

            # Index exact and semantic signatures
            if fp.exact_signature:
                self._exact_index[fp.exact_signature] = fp.fingerprint_id

            if fp.semantic_signature:
                if fp.semantic_signature not in self._semantic_index:
                    self._semantic_index[fp.semantic_signature] = set()
                self._semantic_index[fp.semantic_signature].add(fp.fingerprint_id)

            if fp.attack_path_signature:
                if fp.attack_path_signature not in self._path_index:
                    self._path_index[fp.attack_path_signature] = set()
                self._path_index[fp.attack_path_signature].add(fp.fingerprint_id)

            for fam in fp.threat_families:
                if fam not in self._family_index:
                    self._family_index[fam] = set()
                self._family_index[fam].add(fp.fingerprint_id)

            return fp

    def get_fingerprint(self, fingerprint_id: str) -> Optional[ScamFingerprint]:
        """Retrieves a fingerprint by ID."""
        with self._lock:
            return self._fingerprints.get(fingerprint_id)

    def get_by_exact_signature(self, exact_signature: str) -> Optional[ScamFingerprint]:
        """Fast lookup by exact canonical signature."""
        with self._lock:
            fp_id = self._exact_index.get(exact_signature)
            return self._fingerprints.get(fp_id) if fp_id else None

    def get_candidates(self, features: dict[str, Any]) -> list[ScamFingerprint]:
        """Retrieves candidate fingerprints for deep comparison using index lookups."""
        with self._lock:
            candidate_ids: set[str] = set()

            # 1. Exact match candidate
            exact_sig = features.get("exact_signature")
            if exact_sig and exact_sig in self._exact_index:
                candidate_ids.add(self._exact_index[exact_sig])

            # 2. Semantic match candidates
            sem_sig = features.get("semantic_signature")
            if sem_sig and sem_sig in self._semantic_index:
                candidate_ids.update(self._semantic_index[sem_sig])

            # 3. Path match candidates
            path_sig = features.get("attack_path_signature")
            if path_sig and path_sig in self._path_index:
                candidate_ids.update(self._path_index[path_sig])

            # 4. Family match candidates
            for fam in features.get("threat_families", []):
                if fam in self._family_index:
                    candidate_ids.update(self._family_index[fam])

            # If candidates found, return them; otherwise check all active fingerprints
            if candidate_ids:
                return [self._fingerprints[fid] for fid in candidate_ids if fid in self._fingerprints]
            return list(self._fingerprints.values())

    def record_observation(
        self,
        fingerprint_id: str,
        observation: FingerprintObservation,
        content_hash: Optional[str] = None
    ) -> None:
        """Consolidates an observation against a fingerprint with amplification safeguards."""
        with self._lock:
            fp = self._fingerprints.get(fingerprint_id)
            if not fp:
                return

            now_iso = datetime.now(timezone.utc).isoformat()
            fp.last_seen = now_iso
            fp.updated_at = now_iso

            # Amplification & duplicate origin check
            is_dup = False
            if content_hash:
                seen_hashes = self._content_hash_registry[fingerprint_id]
                if content_hash in seen_hashes:
                    # Message was identical copy from same source (do NOT count as independent report)
                    is_dup = True
                    observation.is_duplicate_origin = True
                else:
                    seen_hashes.add(content_hash)
                    fp.content_hashes.append(content_hash)

            if not is_dup:
                fp.observation_count += 1

            # Track distinct channels
            if observation.channel and observation.channel not in fp.distinct_channels:
                fp.distinct_channels.append(observation.channel)

            # Track distinct variants
            if observation.match_type in ("SEMANTIC_VARIANT", "STRUCTURAL_MATCH"):
                if observation.match_type == "SEMANTIC_VARIANT":
                    fp.distinct_variants += 1

            # Lifecycle promotion: promote NEW to ACTIVE on multiple independent observations
            if fp.status == "NEW" and fp.observation_count >= 2:
                fp.status = "ACTIVE"
                fp.status_change_history.append({
                    "from_status": "NEW",
                    "to_status": "ACTIVE",
                    "timestamp": now_iso,
                    "reason": f"Promoted to ACTIVE upon reaching {fp.observation_count} observations"
                })

            self._observations[fingerprint_id].append(observation)

    def dispute_fingerprint(
        self,
        fingerprint_id: str,
        reason: str,
        actor: Optional[str] = None
    ) -> Optional[ScamFingerprint]:
        """Registers a user or analyst dispute for a fingerprint without deleting history."""
        with self._lock:
            fp = self._fingerprints.get(fingerprint_id)
            if not fp:
                return None

            now_iso = datetime.now(timezone.utc).isoformat()
            old_status = fp.status
            fp.status = "DISPUTED"
            fp.dispute_count += 1
            fp.dispute_notes.append(f"[{now_iso}] {reason}")
            fp.updated_at = now_iso
            fp.status_change_history.append({
                "from_status": old_status,
                "to_status": "DISPUTED",
                "timestamp": now_iso,
                "reason": reason,
                "actor": actor or "user"
            })
            return fp

    def mark_stale_if_inactive(
        self,
        fingerprint_id: str,
        threshold_days: int = 90
    ) -> bool:
        """Transitions a fingerprint to STALE if no observations seen within threshold."""
        with self._lock:
            fp = self._fingerprints.get(fingerprint_id)
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
                fp.status_change_history.append({
                    "from_status": old_status,
                    "to_status": "STALE",
                    "timestamp": now.isoformat(),
                    "reason": f"No observations in {threshold_days} days"
                })
                return True
            return False

    def archive_fingerprint(
        self,
        fingerprint_id: str,
        reason: str = "Archived by policy"
    ) -> Optional[ScamFingerprint]:
        """Archives a fingerprint."""
        with self._lock:
            fp = self._fingerprints.get(fingerprint_id)
            if not fp:
                return None

            now_iso = datetime.now(timezone.utc).isoformat()
            old_status = fp.status
            fp.status = "ARCHIVED"
            fp.updated_at = now_iso
            fp.status_change_history.append({
                "from_status": old_status,
                "to_status": "ARCHIVED",
                "timestamp": now_iso,
                "reason": reason
            })
            return fp

    def link_related_fingerprints(self, fp_id_1: str, fp_id_2: str) -> None:
        """Establishes a bi-directional structural relationship between two fingerprints."""
        with self._lock:
            fp1 = self._fingerprints.get(fp_id_1)
            fp2 = self._fingerprints.get(fp_id_2)
            if fp1 and fp_id_2 not in fp1.related_fingerprint_ids:
                fp1.related_fingerprint_ids.append(fp_id_2)
            if fp2 and fp_id_1 not in fp2.related_fingerprint_ids:
                fp2.related_fingerprint_ids.append(fp_id_1)

    def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        threat_family: Optional[str] = None,
        channel: Optional[str] = None
    ) -> list[ScamFingerprint]:
        """Searches fingerprints by status, threat family, channel, or keyword."""
        with self._lock:
            results = list(self._fingerprints.values())
            if status:
                results = [fp for fp in results if fp.status.upper() == status.upper()]
            if threat_family:
                results = [fp for fp in results if any(threat_family.lower() in f.lower() for f in fp.threat_families)]
            if channel:
                results = [fp for fp in results if any(channel.lower() in c.lower() for c in fp.distinct_channels or fp.channel_patterns)]
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
        with self._lock:
            return list(self._observations.get(fingerprint_id, []))

    def reset(self) -> None:
        """Clears all stored fingerprints and indexes (used in tests)."""
        with self._lock:
            self._fingerprints.clear()
            self._observations.clear()
            self._content_hash_registry.clear()
            self._exact_index.clear()
            self._semantic_index.clear()
            self._family_index.clear()
            self._path_index.clear()
