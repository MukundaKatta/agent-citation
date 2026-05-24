"""CitationStore facade + pluggable sinks.

The Store records turn-scoped attribution: each `attach(turn_id, text, citations)`
call captures the text the agent produced and the citations it claimed to
back that text with. Sinks decide where the records live: in-memory for
tests, JSONL for audit, your own implementation for a database.
"""

from __future__ import annotations

import io
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Protocol

from .citation import Citation


@dataclass(frozen=True)
class AttributionRecord:
    """One turn's worth of agent text plus the citations that back it."""

    turn_id: str
    text: str
    citations: tuple[Citation, ...]
    captured_at: float = field(default_factory=lambda: time.time())

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "text": self.text,
            "citations": [c.to_dict() for c in self.citations],
            "captured_at": self.captured_at,
        }


class Sink(Protocol):
    """Storage backend for AttributionRecord values."""

    def write(self, record: AttributionRecord) -> None: ...

    def read_all(self) -> list[AttributionRecord]: ...


class InMemorySink:
    """Keeps records in process memory. Fastest path for tests + small demos."""

    def __init__(self) -> None:
        self._records: list[AttributionRecord] = []

    def write(self, record: AttributionRecord) -> None:
        self._records.append(record)

    def read_all(self) -> list[AttributionRecord]:
        return list(self._records)

    def clear(self) -> None:
        self._records.clear()


class JsonlSink:
    """Appends records to a JSONL file. One record per line so audit logs
    can be tailed and grep'd with normal Unix tools.
    """

    def __init__(self, path: str) -> None:
        self._path = path
        # Make sure the parent dir exists so write() does not surprise the caller.
        parent = os.path.dirname(os.path.abspath(path))
        if parent:
            os.makedirs(parent, exist_ok=True)

    @property
    def path(self) -> str:
        return self._path

    def write(self, record: AttributionRecord) -> None:
        payload = json.dumps(record.to_dict(), ensure_ascii=False)
        # Open per write keeps the file flushed and survives crash-mid-run.
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(payload + "\n")

    def read_all(self) -> list[AttributionRecord]:
        if not os.path.exists(self._path):
            return []
        out: list[AttributionRecord] = []
        with open(self._path, "r", encoding="utf-8") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                data = json.loads(raw)
                citations = tuple(Citation.from_dict(c) for c in data.get("citations", []))
                out.append(
                    AttributionRecord(
                        turn_id=str(data["turn_id"]),
                        text=str(data["text"]),
                        citations=citations,
                        captured_at=float(data.get("captured_at", 0.0)),
                    )
                )
        return out


class CitationStore:
    """Public facade. Wraps a Sink and centralizes turn-level capture.

    Defaults to in-memory storage so smoke tests work with no setup.
    Swap the sink for JsonlSink or a custom backend in production.
    """

    def __init__(self, sink: Sink | None = None) -> None:
        self._sink: Sink = sink if sink is not None else InMemorySink()

    @property
    def sink(self) -> Sink:
        return self._sink

    def attach(
        self,
        turn_id: str,
        text: str,
        citations: Iterable[Citation],
    ) -> AttributionRecord:
        """Capture one turn of agent output plus its claimed citations."""
        if not isinstance(turn_id, str) or not turn_id.strip():
            raise ValueError("turn_id must be a non-empty string")
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        # Force the iterable here so we get a stable tuple even if the
        # caller passed a generator that would exhaust mid-write.
        record = AttributionRecord(
            turn_id=turn_id,
            text=text,
            citations=tuple(citations),
        )
        self._sink.write(record)
        return record

    def export(self) -> list[dict[str, Any]]:
        """Return JSON-friendly dicts for downstream UI rendering or audit."""
        return [record.to_dict() for record in self._sink.read_all()]

    def render_text_summary(self) -> str:
        """Human-readable one-record-per-line summary. Useful for CLI debug."""
        buf = io.StringIO()
        for record in self._sink.read_all():
            cite_ids = ",".join(c.id for c in record.citations) or "-"
            buf.write(f"[{record.turn_id}] cites={cite_ids} len={len(record.text)}\n")
        return buf.getvalue()
