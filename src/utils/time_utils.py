"""
Time utilities — all timestamps in the agentic suite use Central Time.
Import now_ct() everywhere instead of datetime.now().
"""

from datetime import datetime
from zoneinfo import ZoneInfo

CENTRAL = ZoneInfo("America/Chicago")


def now_ct() -> datetime:
    """Return the current datetime in Central Time (CT)."""
    return datetime.now(CENTRAL)


def now_ct_str(fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Return the current CT datetime as a formatted string."""
    return now_ct().strftime(fmt)
