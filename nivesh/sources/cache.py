"""Source Caching for Engine 4 (Source Intelligence Engine).

Provides in-memory caching of authoritative source documents and searches to:
- Avoid hammering official government and stock exchange portals
- Record exact retrieved_at and expires_at timestamps
- Return explicit 'CACHE' mode on hits without faking freshness
"""

import time
import hashlib
import json
from typing import Optional, Any
from datetime import datetime, timezone, timedelta
from nivesh.schemas.sources import SourceDocument, SourceSearchResult


class SourceCache:
    """Thread-safe in-memory cache for source queries and documents."""

    def __init__(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self._cache: dict[str, dict[str, Any]] = {}

    @staticmethod
    def generate_cache_key(source_id: str, query_params: dict[str, Any]) -> str:
        """Generates deterministic cache key from source ID and query dict."""
        # Sort keys for stable hash
        serialized = json.dumps(query_params, sort_keys=True, default=str)
        hash_digest = hashlib.sha256(f"{source_id}:{serialized}".encode("utf-8")).hexdigest()
        return f"{source_id}:{hash_digest}"

    def get_document(self, cache_key: str) -> Optional[SourceDocument]:
        """Retrieves cached SourceDocument if present and not expired."""
        entry = self._cache.get(cache_key)
        if not entry:
            return None

        now = time.time()
        if now > entry["expires_at"]:
            # Stale entry
            del self._cache[cache_key]
            return None

        doc: SourceDocument = entry["document"]
        # Return a copy with mode marked as CACHE
        doc_dict = doc.model_dump()
        doc_dict["retrieval"]["mode"] = "CACHE"
        return SourceDocument(**doc_dict)

    def set_document(
        self,
        cache_key: str,
        document: SourceDocument,
        ttl_seconds: Optional[int] = None
    ) -> None:
        """Stores a SourceDocument in cache with an expiration timestamp."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = time.time()
        expires_at = now + ttl

        self._cache[cache_key] = {
            "document": document,
            "cached_at": now,
            "expires_at": expires_at,
        }

    def clear(self) -> None:
        """Clears all cached entries."""
        self._cache.clear()

    def count(self) -> int:
        """Returns number of active cached items."""
        now = time.time()
        # Clean expired
        keys_to_del = [k for k, v in self._cache.items() if now > v["expires_at"]]
        for k in keys_to_del:
            del self._cache[k]
        return len(self._cache)
