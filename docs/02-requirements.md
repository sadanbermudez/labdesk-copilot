# 02 · Requirements

Turning the brief into testable requirements. Each one names how it is verified; "eval" means the automated evaluation in `evals/`, "test" means the unit tests in `tests/`.

## Functional

| ID | Requirement | Verified by |
|---|---|---|
| F1 | Answer PyVISA usage questions using only retrieved passages from the PyVISA 1.16.2 docs. | eval: correctness, groundedness |
| F2 | Every answer cites its sources as `[S1]`, `[S2]`…, each mapping to a documentation section with a link. | test: citation parsing; eval: citation validity |
| F3 | If the passages do not contain the answer, reply with a fixed refusal sentence and no invented content. | eval: refusal accuracy on out-of-scope questions |
| F4 | Questions about the live power meter call the instrument tool and report its actual reading. | eval: tool questions; test: tool |
| F5 | HTTP API: `POST /ask`, `GET /health`, `GET /metrics`, and a minimal web page. | test: API with a fake model |
| F6 | Every request is logged: question, retrieved sources, cited sources, latency, tokens. | test: telemetry |

## Non-functional

| ID | Requirement | Target | Verified by |
|---|---|---|---|
| N1 | Retrieval puts a relevant section in the top 5 | recall@5 ≥ 0.90 | eval (also a CI gate, no model needed) |
| N2 | Answer correctness on in-scope questions | ≥ 0.85 | eval |
| N3 | Citations point to a relevant section | ≥ 0.85 of answers | eval |
| N4 | Correct refusal on out-of-scope questions | ≥ 0.80, and no in-scope question refused more than 10% of the time | eval |
| N5 | Latency per answer on the client's hardware | p95 < 10 s | eval |
| N6 | Runs fully on-premises; no network calls except to the configured model server | design | review |
| N7 | Cost visible per request, for local and for any configured hosted price | per-request field | test |

## Out of scope (agreed)

- Other libraries' documentation (instrument SCPI manuals, NI-MAX, MATLAB).
- Writing or running arbitrary instrument commands: the tool is read-only.
- Fine-tuning a model.

## Risks and how they are handled

| Risk | Mitigation |
|---|---|
| The model ignores the passages and answers from memory | System prompt forbids it; eval measures groundedness via required facts and citation validity; refusal sentence for gaps |
| Fluent but wrong citations | Citations validated against the passages actually supplied; invalid ones flagged in the response |
| A model or prompt change silently degrades quality | Eval suite with thresholds; retrieval gate in CI on every push |
| Instrument tool misuse | Tool is read-only, narrow (identify, read power), and errors are returned as text, never raised into the chat |
| Docs version drift | Corpus pinned to 1.16.2 and committed with its licence |
