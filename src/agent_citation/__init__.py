"""agent-citation: structured citations for AI agent outputs.

Public API:
- Citation                 source pointer dataclass
- CitationStore            turn-scoped capture facade
- InMemorySink, JsonlSink  bundled sinks
- Sink                     Protocol for custom backends
- AttributionRecord        one captured turn
- attribute(text)          extract bracketed markers from agent prose
- validate(text, citations) structural check, returns ValidationReport
- ValidationReport         dataclass with coverage_ratio + markdown render
"""

from .attribute import Marker, attribute, unique_marker_ids
from .citation import Citation
from .report import ValidationReport
from .store import (
    AttributionRecord,
    CitationStore,
    InMemorySink,
    JsonlSink,
    Sink,
)
from .validate import validate

__all__ = [
    "AttributionRecord",
    "Citation",
    "CitationStore",
    "InMemorySink",
    "JsonlSink",
    "Marker",
    "Sink",
    "ValidationReport",
    "attribute",
    "unique_marker_ids",
    "validate",
]

__version__ = "0.1.0"
