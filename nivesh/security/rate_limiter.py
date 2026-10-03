"""In-memory rate limiting and abuse protection for Nivesh Firewall.

Phase 14.3: Security, Access Control & Secrets.
Implements a thread-safe sliding window rate limiter per client IP or authenticated principal.
"""

import time
import threading
from typing import Tuple, Dict, List


class SlidingWindowRateLimiter:
    """Thread-safe sliding-window rate limiter."""

    def __init__(self):
        self._lock = threading.Lock()
        # client_id -> list of request timestamps in seconds
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(
        self,
        client_id: str,
        limit: int = 120,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """Check if a request from client_id is permitted within the sliding window.

        Returns:
            (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            timestamps = self._requests.get(client_id, [])
            # Prune timestamps older than window
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= limit:
                # Rate limit exceeded
                oldest = valid_timestamps[0]
                retry_after = max(1, int(oldest + window_seconds - now))
                self._requests[client_id] = valid_timestamps
                return False, 0, retry_after

            # Request is allowed
            valid_timestamps.append(now)
            self._requests[client_id] = valid_timestamps
            remaining = max(0, limit - len(valid_timestamps))
            return True, remaining, 0

    def reset(self) -> None:
        """Clear all tracked request history (for tests)."""
        with self._lock:
            self._requests.clear()


# Default singleton instance
rate_limiter = SlidingWindowRateLimiter()
