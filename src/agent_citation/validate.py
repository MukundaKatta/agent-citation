"""Validation: compare agent text markers against a citation list."""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from .attribute import attribute, unique_marker_ids
from .citation import Citation
from .report import ValidationReport


def validate(text: str, citations: Iterable[Citation]) -> ValidationReport:
    """Compare bracketed markers inside `text` with supplied citations.

    The check is structural, not semantic: we do not try to verify whether
    the source actually supports the fact. We only check whether each
    marker has a citation entry and whether the supplied citations were
    actually referenced.
    """
    citations_list = list(citations)
    citation_ids = [c.id for c in citations_list]
    citation_id_set = set(citation_ids)

    # Spot duplicate citation ids in the supplied list.
    duplicates = sorted({cid for cid, count in Counter(citation_ids).items() if count > 1})

    markers = attribute(text)
    ordered_ids = unique_marker_ids(markers)
    marker_id_set = set(ordered_ids)

    matched = [mid for mid in ordered_ids if mid in citation_id_set]
    missing = [mid for mid in ordered_ids if mid not in citation_id_set]
    dangling = sorted(citation_id_set - marker_id_set)

    if ordered_ids:
        coverage = len(matched) / len(ordered_ids)
    else:
        # No markers means nothing to attribute; treat as fully covered so
        # an empty agent reply does not register as uncovered.
        coverage = 1.0

    return ValidationReport(
        facts_with_citations=len(matched),
        facts_missing_citations=len(missing),
        dangling_citation_ids=dangling,
        duplicate_citation_ids=duplicates,
        coverage_ratio=coverage,
        markers_in_order=ordered_ids,
    )
