"""Citation dataclass and small helpers.

A Citation is a structured pointer to a source that backs a fact emitted by
an AI agent. The fields are intentionally narrow so the lib stays zero-dep
and renderable in any UI (web, markdown, terminal, mobile).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass(frozen=True)
class Citation:
    """A pointer from a fact in agent output to its source location.

    Attributes:
        id: Marker the agent uses inline, for example "1" for the marker [1].
            Stored as a string so authors can use slugs like "policy-v3-p4".
        source_uri: Where the source lives. Could be a URL, a doc store URI
            (`docs://policy/v3`), an S3 key, or a vector-db row id.
        span: The exact substring or quote inside the source that supports
            the fact. Optional but strongly recommended.
        page: Optional page or chunk number for paginated sources.
        confidence: Optional float in [0.0, 1.0]. When unset, downstream UI
            should treat the citation as unscored.
        metadata: Free-form extras (retriever score, embedding model id, etc).
    """

    id: str
    source_uri: str
    span: str | None = None
    page: int | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Validation runs once at construction so callers fail fast.
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("Citation.id must be a non-empty string")
        if not isinstance(self.source_uri, str) or not self.source_uri.strip():
            raise ValueError("Citation.source_uri must be a non-empty string")
        if self.page is not None and self.page < 0:
            raise ValueError("Citation.page must be >= 0 when provided")
        if self.confidence is not None:
            if not (0.0 <= self.confidence <= 1.0):
                raise ValueError("Citation.confidence must be within [0.0, 1.0]")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly dict. Drops None fields to keep payload small."""
        out = asdict(self)
        return {k: v for k, v in out.items() if v is not None and v != {}}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Citation":
        """Hydrate a Citation from a previously exported dict."""
        return cls(
            id=str(data["id"]),
            source_uri=str(data["source_uri"]),
            span=data.get("span"),
            page=data.get("page"),
            confidence=data.get("confidence"),
            metadata=dict(data.get("metadata", {})),
        )
