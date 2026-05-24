"""Marker extraction for inline citations.

Agent prose tends to use bracketed numeric markers like `[1]` or `[12]`.
This module reads a string and returns the markers it found, in document
order, with their string offsets. Downstream code in `validate.py` uses
these to compare what the agent claimed with what the citation list backs.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Match [n] or [n, n] style markers. Numeric only to keep false-positives low.
# Authors who want symbolic ids should call attribute() with a custom pattern.
_DEFAULT_MARKER_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


@dataclass(frozen=True)
class Marker:
    """A single citation reference inside agent text.

    Attributes:
        id: The marker text the citation was tagged with ("1", "12", etc).
        start: Inclusive offset of `[` inside the source string.
        end: Exclusive offset of `]` + 1 inside the source string.
    """

    id: str
    start: int
    end: int


def attribute(text: str, *, pattern: re.Pattern[str] | None = None) -> list[Marker]:
    """Extract citation markers from `text`.

    Args:
        text: Agent output prose.
        pattern: Optional custom compiled regex. The first capture group must
            contain one or more comma-separated ids.

    Returns:
        List of Markers in document order. `[1, 2]` expands to two Markers
        sharing the same start/end pair so writers can render either as a
        joined chip or as two chips.
    """
    if text is None:
        raise TypeError("attribute() requires a string, not None")

    regex = pattern or _DEFAULT_MARKER_RE
    markers: list[Marker] = []
    for match in regex.finditer(text):
        raw_group = match.group(1)
        ids = [part.strip() for part in raw_group.split(",") if part.strip()]
        for marker_id in ids:
            markers.append(Marker(id=marker_id, start=match.start(), end=match.end()))
    return markers


def unique_marker_ids(markers: list[Marker]) -> list[str]:
    """Return ids in first-seen order, deduped."""
    seen: set[str] = set()
    out: list[str] = []
    for marker in markers:
        if marker.id not in seen:
            seen.add(marker.id)
            out.append(marker.id)
    return out
