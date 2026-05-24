import pytest

from agent_citation import Citation


def test_citation_minimal_fields_only():
    c = Citation(id="1", source_uri="docs://policy/v3")
    assert c.id == "1"
    assert c.source_uri == "docs://policy/v3"
    assert c.span is None
    assert c.page is None
    assert c.confidence is None
    assert c.metadata == {}


def test_citation_full_fields_roundtrip():
    c = Citation(
        id="policy-v3-p4",
        source_uri="https://example.com/policy.pdf",
        span="expires 2026-12-31",
        page=4,
        confidence=0.92,
        metadata={"retriever": "bge-large", "score": 0.81},
    )
    as_dict = c.to_dict()
    rehydrated = Citation.from_dict(as_dict)
    assert rehydrated == c


def test_citation_to_dict_drops_empty_fields():
    c = Citation(id="1", source_uri="docs://x")
    out = c.to_dict()
    assert "span" not in out
    assert "page" not in out
    assert "confidence" not in out
    assert "metadata" not in out


def test_citation_rejects_blank_id():
    with pytest.raises(ValueError):
        Citation(id="   ", source_uri="docs://x")


def test_citation_rejects_blank_source_uri():
    with pytest.raises(ValueError):
        Citation(id="1", source_uri="")


def test_citation_rejects_negative_page():
    with pytest.raises(ValueError):
        Citation(id="1", source_uri="docs://x", page=-2)


def test_citation_rejects_out_of_range_confidence():
    with pytest.raises(ValueError):
        Citation(id="1", source_uri="docs://x", confidence=1.5)


def test_citation_is_frozen():
    c = Citation(id="1", source_uri="docs://x")
    with pytest.raises(Exception):
        c.id = "2"  # type: ignore[misc]
