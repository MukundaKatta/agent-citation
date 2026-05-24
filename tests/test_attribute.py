from agent_citation import attribute, unique_marker_ids


def test_attribute_finds_single_marker():
    text = "The policy expires 2026-12-31 [1]."
    markers = attribute(text)
    assert len(markers) == 1
    assert markers[0].id == "1"
    assert text[markers[0].start : markers[0].end] == "[1]"


def test_attribute_finds_multiple_markers_in_order():
    text = "A [1]. B [2]. C [3]."
    ids = [m.id for m in attribute(text)]
    assert ids == ["1", "2", "3"]


def test_attribute_expands_grouped_markers():
    text = "Both apply here [1, 2]."
    markers = attribute(text)
    assert [m.id for m in markers] == ["1", "2"]
    # Both share the same outer span.
    assert markers[0].start == markers[1].start
    assert markers[0].end == markers[1].end


def test_attribute_ignores_non_numeric_brackets():
    text = "See [Appendix A] for details."
    assert attribute(text) == []


def test_attribute_returns_empty_for_clean_text():
    assert attribute("No citations here at all.") == []


def test_unique_marker_ids_dedupes_in_order():
    text = "A [1]. B [2]. C [1]. D [3]."
    markers = attribute(text)
    assert unique_marker_ids(markers) == ["1", "2", "3"]


def test_attribute_handles_double_digit_ids():
    text = "Big id [12] and [101]."
    ids = [m.id for m in attribute(text)]
    assert ids == ["12", "101"]
