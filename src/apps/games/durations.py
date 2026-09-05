"""Playtime parsing and formatting.

Playtime is stored as an hour range (``duration_hours_min`` /
``duration_hours_max``) so it can be filtered and sorted. The human readable
string the API exposes is generated from that range, which keeps a single
source of truth instead of the previous free-text field.
"""

import re

ENDLESS = "∞"

_RANGE_RE = re.compile(r"^(\d+)\s*-\s*(\d+)\s+час\S*$")
_SINGLE_RE = re.compile(r"^(\d+)\s+час\S*$")


def parse_duration(text: str) -> tuple[int | None, int | None]:
    """Parse ``"10 часов"`` / ``"5-10 часов"`` / ``"∞"`` into an hour range.

    Endless games are represented by a ``(None, None)`` range; the
    ``duration_type`` reference ("бесконечная") carries that meaning too.
    """
    text = (text or "").strip()
    if text == ENDLESS:
        return None, None

    match = _RANGE_RE.match(text)
    if match:
        return int(match.group(1)), int(match.group(2))

    match = _SINGLE_RE.match(text)
    if match:
        hours = int(match.group(1))
        return hours, hours

    raise ValueError(f"Unrecognised duration: {text!r}")


def hours_word(hours: int) -> str:
    """Russian plural form of "час" for the given number."""
    if hours % 100 in (11, 12, 13, 14):
        return "часов"
    if hours % 10 == 1:
        return "час"
    if hours % 10 in (2, 3, 4):
        return "часа"
    return "часов"


def format_duration(hours_min: int | None, hours_max: int | None) -> str:
    """Render an hour range the way the catalog has always displayed it."""
    if hours_min is None or hours_max is None:
        return ENDLESS
    if hours_min == hours_max:
        return f"{hours_min} {hours_word(hours_min)}"
    return f"{hours_min}-{hours_max} часов"
