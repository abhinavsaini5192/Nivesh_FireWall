"""Rate Limiter and Retry Handler for Engine 4.

Prevents flooding official regulator and stock exchange servers:
- Enforces minimum delay between consecutive calls per source/domain
- Provides retry with exponential backoff on transient errors (429, 503, timeouts)
- Respects maximum retry limits
"""

import time
import math
from typing import Callable, Any, Optional
from urllib.parse import urlparse


class RateLimiter:
    """Manages request throttling and retries per source or target host."""

    def __init__(
        self,
        min_interval_seconds: float = 0.5,
        max_retries: int = 2,
        backoff_factor: float = 1.5,
    ):
        self.min_interval = min_interval_seconds
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._last_call_time: dict[str, float] = {}

    def throttle(self, source_or_domain: str) -> None:
        """Enforces minimum interval before allowing a request to proceed."""
        now = time.time()
        last_time = self._last_call_time.get(source_or_domain, 0.0)
        elapsed = now - last_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)

        self._last_call_time[source_or_domain] = time.time()

    def execute_with_retry(
        self,
        func: Callable[[], Any],
        source_id: str,
        is_transient_error: Optional[Callable[[Exception], bool]] = None
    ) -> Any:
        """Executes a function with rate limiting and exponential backoff retries."""
        attempts = 0
        while True:
            self.throttle(source_id)
            try:
                return func()
            except Exception as e:
                attempts += 1
                if attempts > self.max_retries:
                    raise e

                # Check if error is transient
                if is_transient_error and not is_transient_error(e):
                    raise e

                # Exponential backoff
                delay = self.min_interval * (self.backoff_factor ** attempts)
                time.sleep(delay)
