# agent-citation: the WHERE layer for AI agent answers

*Submission for the Hermes Agent Challenge on dev.to. Repo: https://github.com/MukundaKatta/agent-citation*

## The problem

You ship a RAG agent. A user asks "when does my policy expire?" and the
agent answers, with full confidence, "2026-12-31." The user clicks
through to verify. There is no link. There is no quote. There is just a
sentence.

A week later your support team gets a chargeback complaint. The policy
actually expired on 2025-12-31. The agent hallucinated a year. Nobody
can tell where the wrong fact came from, because the answer never
carried a source pointer in the first place.

This is the gap I built `agent-citation` to close. It is a tiny zero-dep
Python library that captures, validates, and exposes the source pointer
behind each fact an agent emits. It does not call an LLM. It does not
score answers. It does not gate execution. It records the attribution
trail so any downstream UI or audit job can show the user exactly which
source backs each fact.

## What the library does

Three responsibilities, nothing more.

**Capture.** A `CitationStore` records `(turn_id, text, citations)`
records as the agent runs. By default it keeps records in memory. Swap
in `JsonlSink` for an append-only audit log, or implement the `Sink`
protocol for your own backend (Postgres, S3, Kafka, whatever).

**Validate.** A `validate(text, citations)` function reads the agent's
prose, extracts every bracketed marker like `[1]` or `[2, 5]`, and
compares them to the supplied citation list. It returns a
`ValidationReport` with the coverage ratio, missing markers, dangling
citations, and duplicate ids.

**Render.** `ValidationReport.as_markdown()` gives you a paste-ready
markdown block for a PR comment, a CI log, or a Slack message.

That is the whole surface. A single import gets you what you need:

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
print(report.as_markdown())
```

## Why a separate library

Most teams I have talked to roll citation tracking into one of two
places. They either jam it into the LLM client wrapper (which then
becomes a god class) or they cram it into the vector store layer
(which then has to know about agent prose). Both choices age badly.

`agent-citation` is one slice of a small family of zero-dep agent
libraries I have been shipping. Each one captures a different signal
about an agent run, and each one stays out of the others' way:

- **agent-citation** is the WHERE layer. Source pointers for facts in
  agent output.
- **agent-decision-log** is the WHY layer. The reasoning the agent gave
  for picking the tool or the document.
- **agentsnap** is the CALLS layer. Snapshot of tool calls and arguments
  for golden tests.
- **agenttrace** is the COST layer. Token usage, latency, and cost
  rollups per run.

You can adopt any one of these on its own. Use them together and you
get a full ledger: which tools the agent called, why it picked them,
where its facts came from, and what the run cost. Each library is
under 200 lines of code and ships zero runtime dependencies.

## What good citation hygiene looks like

The structural checks turn out to be more useful than I expected.

**Orphan markers.** The agent wrote `[9]` in the answer but only
supplied citations 1 and 2. The user clicks `[9]` and the UI shows
nothing. `validate()` flags this as a missing citation and the
coverage ratio drops.

**Dangling citations.** The retriever surfaced four chunks but the
agent only referenced three of them. The fourth shows up as a
dangling citation. Often this is fine. Sometimes it means the agent
dropped a fact during summarization and you want to ask why.

**Duplicate ids.** Two citations both claim id `1`. The store still
accepts them, but the validator surfaces the duplication so a human
can dedupe.

None of these checks are semantic. The library does not know whether
the cited source actually supports the fact. That part is the agent's
job, or your eval suite's job. What the library guarantees is that
the attribution shape is sound: every marker the user sees has a
matching pointer they can click.

## Wire it into your CI

The validation report is the part I use most in CI. Hook it up like
this:

```python
from agent_citation import validate

def test_agent_answer_is_fully_cited():
    result = run_agent("when does my policy expire?")
    report = validate(result.text, result.citations)
    assert report.is_clean, report.as_markdown()
```

The assert fails with the markdown report embedded in the test output,
so you see the exact missing markers without grepping a log. For a
team that has been bitten by an uncited fact in production, that
single test is worth shipping the library for.

## Design choices worth calling out

**Zero runtime deps.** The library is pure stdlib. It runs on Python
3.10 and up. There is nothing to pin, nothing to upgrade, nothing to
fight with the rest of your stack. Pytest is the only dev dep.

**Frozen dataclasses everywhere.** `Citation`, `Marker`, and
`AttributionRecord` are immutable. You can hash them, you can put them
in sets, and you can ship them across thread boundaries without
worrying about state drift.

**Structural Sink protocol.** No subclassing. If your custom backend
has `write(record)` and `read_all()` methods, it works. The protocol
is a five-line interface and the typing system enforces it for free.

**JSONL by default for audit.** One record per line means `tail -f`,
`grep`, `jq`, and `wc -l` all do exactly what you expect. No special
viewer required.

## Try it

```bash
git clone https://github.com/MukundaKatta/agent-citation.git
cd agent-citation
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest -q
```

42 tests pass in well under a second. Two examples (`basic_usage.py`
and `rag_agent_with_citations.py`) run with no extra setup. Wire it
into your agent loop and your answers stop being unverifiable.

## What's next

Two open questions for feedback. First, whether you want a built-in
adapter for a popular vector store so the citation list builds itself
from retrieval hits. Second, whether semantic validation belongs in
this library or in a sibling library that depends on it. My current
bias is sibling. The point of `agent-citation` is to stay small.

If you ship agents, give it a try. The library is MIT and the failure
mode it catches (an uncited fact in production) is the kind that
costs real money to clean up.

Repo: https://github.com/MukundaKatta/agent-citation
