"""ValidationReport dataclass + rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ValidationReport:
    """Outcome of validating agent text against a citation list.

    Attributes:
        facts_with_citations: Count of unique markers in the text that have
            a matching Citation in the supplied list.
        facts_missing_citations: Count of unique markers in the text whose
            id has no matching Citation. These are orphan markers.
        dangling_citation_ids: Citation ids supplied but never referenced
            by any marker inside the text. Often a hint that the agent
            dropped a fact during summarization.
        duplicate_citation_ids: Citation ids that appear more than once in
            the supplied citation list. The store still accepts them, but
            validators should flag the duplication.
        coverage_ratio: facts_with_citations / total_unique_markers.
            Falls back to 1.0 when there are no markers, so an empty answer
            does not look uncovered.
        markers_in_order: All marker ids in the order they appeared. Useful
            for downstream UI that wants to render footnotes.
    """

    facts_with_citations: int = 0
    facts_missing_citations: int = 0
    dangling_citation_ids: list[str] = field(default_factory=list)
    duplicate_citation_ids: list[str] = field(default_factory=list)
    coverage_ratio: float = 1.0
    markers_in_order: list[str] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        """True when nothing is missing, dangling, or duplicated."""
        return (
            self.facts_missing_citations == 0
            and not self.dangling_citation_ids
            and not self.duplicate_citation_ids
        )

    def as_markdown(self) -> str:
        """Render a small markdown report. Handy for CI logs or PR comments."""
        lines: list[str] = []
        lines.append("# Citation validation report")
        lines.append("")
        lines.append(f"- Facts with citations: **{self.facts_with_citations}**")
        lines.append(f"- Facts missing citations: **{self.facts_missing_citations}**")
        lines.append(f"- Coverage ratio: **{self.coverage_ratio:.2f}**")
        if self.dangling_citation_ids:
            joined = ", ".join(self.dangling_citation_ids)
            lines.append(f"- Dangling citation ids: `{joined}`")
        if self.duplicate_citation_ids:
            joined = ", ".join(self.duplicate_citation_ids)
            lines.append(f"- Duplicate citation ids: `{joined}`")
        if self.is_clean:
            lines.append("")
            lines.append("Status: clean")
        else:
            lines.append("")
            lines.append("Status: needs review")
        return "\n".join(lines)
