"""End-to-end: simulate a small RAG turn and validate the captured trace."""

import json

from agent_citation import (
    Citation,
    CitationStore,
    JsonlSink,
    validate,
)


def test_full_rag_turn_capture_then_validate(tmp_path):
    path = tmp_path / "citations.jsonl"
    store = CitationStore(sink=JsonlSink(str(path)))

    text = (
        "The policy expires 2026-12-31 [1]. "
        "Renewal requires 60 days notice [2]. "
        "Joint policies may renew earlier under section 4 [1, 3]."
    )
    citations = [
        Citation(
            id="1",
            source_uri="docs://policy/v3",
            span="2026-12-31 expiration",
            page=4,
            confidence=0.91,
        ),
        Citation(
            id="2",
            source_uri="docs://renewal/v1",
            span="60 days advance notice required",
            page=2,
            confidence=0.87,
        ),
        Citation(
            id="3",
            source_uri="docs://policy/v3",
            span="section 4 joint renewals",
            page=11,
            confidence=0.82,
        ),
    ]

    record = store.attach("turn_42", text, citations)
    assert record.turn_id == "turn_42"

    report = validate(text, citations)
    assert report.facts_with_citations == 3
    assert report.facts_missing_citations == 0
    assert report.dangling_citation_ids == []
    assert report.duplicate_citation_ids == []
    assert report.coverage_ratio == 1.0
    assert report.is_clean

    # Audit log is durable and parseable.
    raw = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(raw) == 1
    parsed = json.loads(raw[0])
    assert parsed["turn_id"] == "turn_42"
    assert len(parsed["citations"]) == 3


def test_e2e_detects_hallucinated_marker():
    store = CitationStore()
    text = "Real fact [1]. Made-up fact [9]."
    citations = [Citation(id="1", source_uri="docs://a")]
    store.attach("turn_1", text, citations)
    report = validate(text, citations)
    assert report.facts_missing_citations == 1
    assert "9" in [m for m in report.markers_in_order if m == "9"]
    md = report.as_markdown()
    assert "needs review" in md


def test_e2e_custom_sink_protocol(tmp_path):
    """A user-supplied sink can plug in via the Sink Protocol."""

    class CountingSink:
        def __init__(self):
            self.records = []

        def write(self, record):
            self.records.append(record)

        def read_all(self):
            return list(self.records)

    sink = CountingSink()
    store = CitationStore(sink=sink)
    store.attach("t1", "A [1].", [Citation(id="1", source_uri="docs://a")])
    store.attach("t2", "B [2].", [Citation(id="2", source_uri="docs://b")])
    assert len(sink.records) == 2
    assert {r.turn_id for r in sink.records} == {"t1", "t2"}
