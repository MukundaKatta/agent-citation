import pytest

from agent_citation import Citation, CitationStore, InMemorySink


def test_store_defaults_to_memory_sink():
    store = CitationStore()
    assert isinstance(store.sink, InMemorySink)


def test_attach_and_export_roundtrip():
    store = CitationStore()
    store.attach(
        "turn_1",
        "A [1].",
        [Citation(id="1", source_uri="docs://a", span="A fact")],
    )
    out = store.export()
    assert len(out) == 1
    assert out[0]["turn_id"] == "turn_1"
    assert out[0]["citations"][0]["id"] == "1"


def test_attach_accepts_generator_of_citations():
    store = CitationStore()
    def gen():
        yield Citation(id="1", source_uri="docs://a")
        yield Citation(id="2", source_uri="docs://b")
    store.attach("turn_1", "A [1]. B [2].", gen())
    out = store.export()
    assert {c["id"] for c in out[0]["citations"]} == {"1", "2"}


def test_attach_rejects_blank_turn_id():
    store = CitationStore()
    with pytest.raises(ValueError):
        store.attach("", "text", [])


def test_attach_rejects_non_string_text():
    store = CitationStore()
    with pytest.raises(TypeError):
        store.attach("turn_1", 12345, [])  # type: ignore[arg-type]


def test_in_memory_sink_clear():
    sink = InMemorySink()
    store = CitationStore(sink=sink)
    store.attach("turn_1", "A [1].", [Citation(id="1", source_uri="docs://a")])
    sink.clear()
    assert store.export() == []


def test_render_text_summary_lists_each_turn():
    store = CitationStore()
    store.attach("turn_1", "A [1].", [Citation(id="1", source_uri="docs://a")])
    store.attach("turn_2", "B [2].", [Citation(id="2", source_uri="docs://b")])
    summary = store.render_text_summary()
    assert "turn_1" in summary and "turn_2" in summary
    assert "cites=1" in summary
