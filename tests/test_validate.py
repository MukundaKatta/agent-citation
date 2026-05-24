from agent_citation import Citation, validate


def test_validate_full_coverage():
    text = "Expires 2026-12-31 [1]. Notice 60 days [2]."
    citations = [
        Citation(id="1", source_uri="docs://policy/v3"),
        Citation(id="2", source_uri="docs://renewal/v1"),
    ]
    report = validate(text, citations)
    assert report.facts_with_citations == 2
    assert report.facts_missing_citations == 0
    assert report.coverage_ratio == 1.0
    assert report.is_clean


def test_validate_flags_orphan_markers():
    text = "Fact A [1]. Fact B [99]."
    citations = [Citation(id="1", source_uri="docs://a")]
    report = validate(text, citations)
    assert report.facts_with_citations == 1
    assert report.facts_missing_citations == 1
    assert report.coverage_ratio == 0.5
    assert not report.is_clean


def test_validate_flags_dangling_citations():
    text = "Fact A [1]."
    citations = [
        Citation(id="1", source_uri="docs://a"),
        Citation(id="2", source_uri="docs://b"),
    ]
    report = validate(text, citations)
    assert report.dangling_citation_ids == ["2"]
    assert not report.is_clean


def test_validate_flags_duplicate_citation_ids():
    text = "Fact A [1]."
    citations = [
        Citation(id="1", source_uri="docs://a"),
        Citation(id="1", source_uri="docs://a-mirror"),
    ]
    report = validate(text, citations)
    assert report.duplicate_citation_ids == ["1"]
    assert not report.is_clean


def test_validate_empty_text_is_clean():
    report = validate("", [])
    assert report.coverage_ratio == 1.0
    assert report.is_clean


def test_validate_no_markers_with_dangling_citations():
    report = validate(
        "Plain answer with no markers.",
        [Citation(id="1", source_uri="docs://a")],
    )
    assert report.facts_missing_citations == 0
    assert report.dangling_citation_ids == ["1"]
    assert report.coverage_ratio == 1.0
    assert not report.is_clean


def test_validate_unique_dedupes_repeated_markers():
    text = "A [1] and again [1] and once more [1]."
    citations = [Citation(id="1", source_uri="docs://a")]
    report = validate(text, citations)
    assert report.facts_with_citations == 1
    assert report.markers_in_order == ["1"]
