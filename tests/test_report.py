from agent_citation import ValidationReport


def test_is_clean_when_nothing_missing():
    r = ValidationReport(facts_with_citations=2, coverage_ratio=1.0)
    assert r.is_clean


def test_is_dirty_when_missing_citations():
    r = ValidationReport(facts_with_citations=1, facts_missing_citations=1)
    assert not r.is_clean


def test_is_dirty_with_dangling_citations():
    r = ValidationReport(dangling_citation_ids=["3"])
    assert not r.is_clean


def test_as_markdown_clean_report_mentions_status_clean():
    r = ValidationReport(facts_with_citations=1, coverage_ratio=1.0)
    md = r.as_markdown()
    assert "Status: clean" in md
    assert "Coverage ratio: **1.00**" in md


def test_as_markdown_dirty_report_mentions_needs_review():
    r = ValidationReport(
        facts_with_citations=1,
        facts_missing_citations=1,
        dangling_citation_ids=["7"],
        duplicate_citation_ids=["1"],
        coverage_ratio=0.5,
    )
    md = r.as_markdown()
    assert "Status: needs review" in md
    assert "Dangling citation ids: `7`" in md
    assert "Duplicate citation ids: `1`" in md
