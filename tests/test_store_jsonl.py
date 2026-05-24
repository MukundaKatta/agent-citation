import json
import os

from agent_citation import Citation, CitationStore, JsonlSink


def test_jsonl_sink_writes_and_reads_back(tmp_path):
    path = tmp_path / "citations.jsonl"
    sink = JsonlSink(str(path))
    store = CitationStore(sink=sink)
    store.attach(
        "turn_1",
        "A [1].",
        [Citation(id="1", source_uri="docs://a", page=2)],
    )

    raw_lines = path.read_text(encoding="utf-8").splitlines()
    assert len(raw_lines) == 1
    parsed = json.loads(raw_lines[0])
    assert parsed["turn_id"] == "turn_1"
    assert parsed["citations"][0]["page"] == 2


def test_jsonl_sink_appends_across_calls(tmp_path):
    path = tmp_path / "citations.jsonl"
    sink = JsonlSink(str(path))
    store = CitationStore(sink=sink)
    store.attach("t1", "A [1].", [Citation(id="1", source_uri="docs://a")])
    store.attach("t2", "B [2].", [Citation(id="2", source_uri="docs://b")])

    records = sink.read_all()
    assert [r.turn_id for r in records] == ["t1", "t2"]


def test_jsonl_sink_read_all_on_missing_file_is_empty(tmp_path):
    path = tmp_path / "nope.jsonl"
    sink = JsonlSink(str(path))
    assert sink.read_all() == []


def test_jsonl_sink_creates_parent_dirs(tmp_path):
    path = tmp_path / "nested" / "deeper" / "audit.jsonl"
    sink = JsonlSink(str(path))
    sink.write_path = sink.path  # noqa: just for clarity
    store = CitationStore(sink=sink)
    store.attach("t1", "A [1].", [Citation(id="1", source_uri="docs://a")])
    assert os.path.exists(path)


def test_jsonl_sink_skips_blank_lines(tmp_path):
    path = tmp_path / "audit.jsonl"
    sink = JsonlSink(str(path))
    store = CitationStore(sink=sink)
    store.attach("t1", "A [1].", [Citation(id="1", source_uri="docs://a")])
    # Inject a blank line by hand; read_all should ignore it cleanly.
    with open(path, "a", encoding="utf-8") as fh:
        fh.write("\n   \n")
    records = sink.read_all()
    assert len(records) == 1
