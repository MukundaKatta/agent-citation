# agent-citation

[![PyPI ready](https://img.shields.io/badge/pypi-pending-lightgrey.svg)](https://pypi.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Zero deps](https://img.shields.io/badge/runtime%20deps-0-brightgreen.svg)](pyproject.toml)

Structured citations for AI agent outputs. Every fact in the agent's answer
maps to one or more source pointers (URL, document id, page, span). When the
agent says "the policy expires 2026-12-31", the user can click through to the
source document and verify.

This is the **WHERE** layer of the agent-stack. It does not score answers, it
does not call an LLM, and it does not gate execution. It captures the
attribution trail so any downstream UI or audit job can show the user
exactly which source backs each fact.

## 60-second quickstart

```bash
pip install -e .[dev]
pytest -q
```

```python
from agent_citation import CitationStore, Citation, validate

store = CitationStore()

text = "The policy expires 2026-12-31 [1]. Renewal requires 60 days notice [2]."
citations = [
    Citation(id="1", source_uri="docs://policy/v3", span="2026-12-31 expiration", page=4),
    Citation(id="2", source_uri="docs://renewal/v1", span="60 days advance notice required", page=2),
]
store.attach("turn_12", text, citations)

report = validate(text, citations)
print(report.coverage_ratio)         # 1.0
print(report.facts_missing_citations) # 0
print(report.is_clean)                # True

for record in store.export():
    print(record["turn_id"], len(record["citations"]))
```

## What you get

| Module          | Purpose                                                                 |
| --------------- | ----------------------------------------------------------------------- |
| `Citation`      | Frozen dataclass: id, source_uri, span, page, confidence, metadata.     |
| `CitationStore` | Facade that captures `(turn_id, text, citations)` records.              |
| `InMemorySink`  | Default sink for tests and small demos.                                 |
| `JsonlSink`     | Append-only JSONL audit log. One record per line so `tail -f` works.    |
| `Sink`          | `Protocol` you implement to plug in your own backend (DB, S3, etc).    |
| `attribute()`   | Extracts bracketed markers like `[1]`, `[2]`, `[1, 2]` from prose.      |
| `validate()`    | Structural check: missing markers, dangling citations, duplicate ids.   |
| `ValidationReport` | Coverage ratio, marker order, markdown render.                       |

## What this is NOT

- Not a fact-checker. We do not call an LLM or compare semantics. If the
  agent claims source A says X and source A actually says Y, the structural
  check still passes. That part is the agent's job.
- Not a citation generator. The agent (or your retriever) decides which
  sources back which sentence. This library captures and validates the
  shape of that decision.
- Not a UI. We give you a `ValidationReport` and a JSONL audit trail. The
  rendering layer (web app, terminal, Slack bot) is yours.
- Not opinionated about source URIs. `docs://policy/v3`, `https://...`,
  `s3://bucket/key`, or `vec://collection/row_123` all work. The library
  treats the URI as an opaque string.

## Where this fits in the agent-stack

agent-citation is one slice of a small zero-dep family of libraries. Each
one captures a different signal about an agent run:

| Library                  | Layer  | What it captures                                                   |
| ------------------------ | ------ | ------------------------------------------------------------------ |
| **agent-citation**       | WHERE  | Source pointers for facts in agent output.                         |
| **agent-decision-log**   | WHY    | The reasoning the agent gave for its choice.                       |
| **agentsnap**            | CALLS  | Snapshot of tool calls and arguments.                              |
| **agenttrace**           | COST   | Token usage, latency, cost rollups per run.                        |

You can use any one of these on its own. Used together they give you a
full ledger: which tools the agent called, why it chose them, where its
facts came from, and what the run cost.

## Catching hallucinated citations

The agent claims source `[9]` but only supplies citations 1 and 2:

```python
from agent_citation import Citation, validate

text = "Real fact [1]. Made-up fact [9]."
citations = [Citation(id="1", source_uri="docs://a")]

report = validate(text, citations)
print(report.facts_missing_citations) # 1
print(report.is_clean)                 # False
print(report.as_markdown())
```

The markdown report is paste-ready for a PR comment or a CI log. Wire it
into your eval suite and you get a coverage signal for every run.

## Custom sinks

`CitationStore` works with anything that implements the `Sink` protocol:

```python
from agent_citation import CitationStore, Citation

class PostgresSink:
    def __init__(self, conn): self.conn = conn
    def write(self, record):
        self.conn.execute("INSERT INTO ...", record.to_dict())
    def read_all(self):
        return [...]

store = CitationStore(sink=PostgresSink(conn))
```

No subclass required. The protocol is structural.

## Examples

- `examples/basic_usage.py` shows the smallest possible loop.
- `examples/rag_agent_with_citations.py` runs a toy retriever, captures the
  citations, and writes the audit log to `/tmp/agent_citation_demo.jsonl`.

## Testing

```bash
pytest -q
```

42 tests cover the full surface including edge cases: orphan markers,
duplicate ids, dangling citations, blank input, generator citation
sources, and the custom-sink protocol.

## License

MIT. See [LICENSE](LICENSE).
