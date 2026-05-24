"""Toy RAG loop showing how a retriever feeds into agent-citation.

This example does not call any real LLM. It hand-rolls a tiny retriever
and an answer template so you can see the data flow end to end. Run it
with `python examples/rag_agent_with_citations.py`.
"""

from __future__ import annotations

from dataclasses import dataclass

from agent_citation import Citation, CitationStore, JsonlSink, validate


@dataclass
class Chunk:
    chunk_id: str
    source_uri: str
    page: int
    text: str


# Pretend this came from your vector store.
KNOWLEDGE_BASE = [
    Chunk("c1", "docs://policy/v3", 4, "Coverage expires 2026-12-31."),
    Chunk("c2", "docs://renewal/v1", 2, "Renewal requires 60 days advance notice."),
    Chunk("c3", "docs://policy/v3", 11, "Section 4 covers joint policy renewals."),
]


def retrieve(question: str) -> list[Chunk]:
    """Toy retriever: returns chunks whose text shares a keyword with the question."""
    keywords = {w.strip(".,?").lower() for w in question.split()}
    hits: list[Chunk] = []
    for chunk in KNOWLEDGE_BASE:
        words = {w.strip(".,?").lower() for w in chunk.text.split()}
        if keywords & words:
            hits.append(chunk)
    return hits


def synthesize(question: str, chunks: list[Chunk]) -> tuple[str, list[Citation]]:
    """Hand-rolled stand-in for a real LLM. Produces text + matching citations."""
    if not chunks:
        return ("I do not have a source for that.", [])

    parts: list[str] = []
    citations: list[Citation] = []
    for index, chunk in enumerate(chunks, start=1):
        marker = str(index)
        parts.append(f"{chunk.text} [{marker}]")
        citations.append(
            Citation(
                id=marker,
                source_uri=chunk.source_uri,
                span=chunk.text,
                page=chunk.page,
            )
        )
    return (" ".join(parts), citations)


def main() -> None:
    store = CitationStore(sink=JsonlSink("/tmp/agent_citation_demo.jsonl"))

    question = "When does the policy expire and what notice is required?"
    chunks = retrieve(question)
    text, citations = synthesize(question, chunks)

    store.attach("rag_turn_1", text, citations)
    report = validate(text, citations)

    print("Question:", question)
    print("Answer:  ", text)
    print()
    print(report.as_markdown())
    print()
    print("Audit log written to /tmp/agent_citation_demo.jsonl")


if __name__ == "__main__":
    main()
