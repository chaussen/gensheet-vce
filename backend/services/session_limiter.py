import logging
import os
from datetime import date

logger = logging.getLogger(__name__)

DAILY_LIMIT = 3

_state: dict = {
    "date": None,
    "count": 0,
}


class SessionLimitExceeded(Exception):
    pass


def _get_tier() -> str:
    return os.environ.get("TIER", "free").lower()


def check_and_increment() -> None:
    """Increment the daily session counter. Raises SessionLimitExceeded on free tier when limit is reached."""
    if _get_tier() == "dev":
        return

    today = date.today().isoformat()
    if _state["date"] != today:
        _state["date"] = today
        _state["count"] = 0

    if _state["count"] >= DAILY_LIMIT:
        logger.info("Daily session limit reached (%d/%d)", _state["count"], DAILY_LIMIT)
        raise SessionLimitExceeded(f"Daily limit of {DAILY_LIMIT} sessions reached")

    _state["count"] += 1
    logger.info("Session count today: %d/%d", _state["count"], DAILY_LIMIT)


def get_remaining() -> int | None:
    """Return remaining sessions for today, or None if tier is unlimited."""
    if _get_tier() == "dev":
        return None

    today = date.today().isoformat()
    if _state["date"] != today:
        return DAILY_LIMIT

    return max(0, DAILY_LIMIT - _state["count"])
