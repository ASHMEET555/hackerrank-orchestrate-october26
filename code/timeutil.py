"""Time utilities for parsing, UTC normalization, and cutoff checking."""

from datetime import datetime, timezone
from typing import Optional


def parse_iso(ts_str: Optional[str]) -> Optional[datetime]:
    """Parses an ISO 8601 / RFC 3339 timestamp string into timezone-aware UTC datetime."""
    if not ts_str:
        return None
    try:
        s = ts_str.strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def format_iso(dt: Optional[datetime]) -> str:
    """Formats a datetime to ISO 8601 UTC string with Z suffix."""
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat().replace("+00:00", "Z")


def is_usable_at(captured_at: Optional[datetime], audit_at: Optional[datetime]) -> bool:
    """Checks whether evidence captured_at is <= case audit_at."""
    if not captured_at or not audit_at:
        return False
    return captured_at <= audit_at
