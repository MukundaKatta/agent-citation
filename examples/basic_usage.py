"""Basic usage of agent-citation.

Run with:
    python examples/basic_usage.py
"""

from agent_citation import Citation, CitationStore, validate


def main() -> None:
    store = CitationStore()

    text = (
        "The policy expires 2026-12-31 [1]. "
        "Renewal requires 60 days notice [2]."
    )
    citations = [
        Citation(
            id="1",
            source_uri="docs://policy/v3",
            span="2026-12-31 expiration",
            page=4,
        ),
        Citation(
            id="2",
            source_uri="docs://renewal/v1",
            span="60 days advance notice required",
            page=2,
        ),
    ]

    store.attach("turn_1", text, citations)
    report = validate(text, citations)

    print(report.as_markdown())
    print()
    print("Captured records:")
    for record in store.export():
        print(" -", record["turn_id"], "->", len(record["citations"]), "citations")


if __name__ == "__main__":
    main()
