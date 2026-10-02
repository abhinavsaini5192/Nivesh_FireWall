"""Temporal and sequence timing analysis for Engine 10: Behavioural Signal Intelligence.

Provides configurable thresholds and time-interval calculations to detect
rapid escalation, rapid channel transitions, and repetition timing.
"""

from datetime import datetime, timezone, time
import re
from typing import Optional, Sequence
from pydantic import BaseModel, Field

from nivesh.behaviour.event_model import InteractionEvent


class TemporalThresholds(BaseModel):
    """Configurable temporal thresholds for behavioural pattern detection."""
    rapid_escalation_seconds_threshold: float = Field(
        default=300.0,
        description="Maximum seconds between initial step and high-impact action to qualify as rapid escalation (default: 5 mins)",
    )
    rapid_channel_migration_seconds_threshold: float = Field(
        default=180.0,
        description="Maximum seconds between channel transitions to qualify as rapid channel migration (default: 3 mins)",
    )
    short_interval_seconds_threshold: float = Field(
        default=60.0,
        description="Interval below which back-to-back actions are considered rapid succession (default: 1 min)",
    )
    repeated_request_threshold: int = Field(
        default=2,
        description="Minimum number of times an action request must appear to be considered repeated (default: 2)",
    )
    urgency_repetition_threshold: int = Field(
        default=2,
        description="Minimum number of urgency signals required to qualify as repeated urgency (default: 2)",
    )


# Default global thresholds
DEFAULT_TEMPORAL_THRESHOLDS = TemporalThresholds()


_TIME_REGEX = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}(?:\.\d+)?))?$")


def parse_timestamp(ts: Optional[str]) -> Optional[datetime]:
    """Parse an ISO 8601 string, epoch string, or HH:MM[:SS] clock string.

    Returns a timezone-aware or naive datetime, or None if unparseable.
    """
    if not ts or not isinstance(ts, str):
        return None

    cleaned = ts.strip()
    if not cleaned:
        return None

    # Check clock string format (e.g. "10:00", "10:03:30")
    clock_match = _TIME_REGEX.match(cleaned)
    if clock_match:
        hour = int(clock_match.group(1))
        minute = int(clock_match.group(2))
        sec_str = clock_match.group(3)
        if sec_str is not None:
            if "." in sec_str:
                sec_val, micro_val = sec_str.split(".", 1)
                second = int(sec_val)
                microsecond = int(micro_val.ljust(6, "0")[:6])
            else:
                second = int(sec_str)
                microsecond = 0
        else:
            second = 0
            microsecond = 0
        return datetime(2026, 1, 1, hour, minute, second, microsecond, tzinfo=timezone.utc)

    # Try ISO 8601
    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        pass

    # Try numeric epoch
    try:
        val = float(cleaned)
        return datetime.fromtimestamp(val, tz=timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def compute_duration_seconds(start_ts: Optional[str], end_ts: Optional[str]) -> Optional[float]:
    """Compute elapsed duration in seconds between two timestamps."""
    start_dt = parse_timestamp(start_ts)
    end_dt = parse_timestamp(end_ts)
    if not start_dt or not end_dt:
        return None

    duration = (end_dt - start_dt).total_seconds()
    return max(0.0, duration)


def is_rapid_interval(start_ts: Optional[str], end_ts: Optional[str], threshold_seconds: float) -> bool:
    """Return True if the interval between start and end is <= threshold_seconds."""
    duration = compute_duration_seconds(start_ts, end_ts)
    if duration is None:
        return False
    return duration <= threshold_seconds


def calculate_event_intervals(events: Sequence[InteractionEvent]) -> list[float]:
    """Calculate successive intervals in seconds between sequential events."""
    if len(events) < 2:
        return []

    intervals: list[float] = []
    for i in range(len(events) - 1):
        dur = compute_duration_seconds(events[i].timestamp, events[i + 1].timestamp)
        if dur is not None:
            intervals.append(dur)
    return intervals
