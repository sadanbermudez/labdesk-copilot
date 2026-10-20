# 04 · Architecture and decisions

```
question ──► BM25 over 98 doc sections ──► top 5 passages [S1..S5] ─┐
        └──► power-meter intent? ──► read-only VISA tool ──► [T1] ──┤
                                                                    ▼
                         system prompt (docs only, cite, or refuse) + passages
                                                                    ▼
                       OpenAI-compatible model server (local llama.cpp by default)
                                                                    ▼
                 citation check (cited ⊆ supplied) ──► answer + sources + telemetry
```

| Module | Job |
|---|---|
| `corpus.py` | Splits the pinned PyVISA 1.16.2 `.rst` docs at headings into sections with a title trail and a GitHub link |
| `retrieve.py` | BM25 ranking, with identifiers like `read_termination` also split into their words |
| `instrument.py` | Reads identity and power from the power meter; simulated by default, real with two environment variables |
| `llm.py` | Calls any OpenAI-compatible `/chat/completions` endpoint |
| `answer.py` | Builds the prompt, calls the model, checks citations, detects refusals |
| `telemetry.py` | JSONL request log, running metrics, cost from configurable prices |
| `api.py` | FastAPI service and the one-page UI |
| `evals/` | Question set, evaluator, results; `docs/report.md` is generated |

## ADR-1 · Lexical retrieval (BM25), not embeddings

**Context.** 98 sections; users ask with the docs' own identifiers (`query_delay`, `ASRL2`, `PYVISA_LIBRARY`).
**Decision.** BM25 in 60 lines of Python, no vector store.
**Consequences.** No embedding model to host or version, identical ranking every run, retrieval testable in CI without a GPU. It would miss paraphrases that share no words with the docs; the eval measures that (recall@5, MRR) and the switch to hybrid search is only worth making if it starts failing.

## ADR-2 · Refusal is a fixed sentence

**Context.** The client's main fear is a confident invented answer.
**Decision.** The prompt requires one exact sentence when the passages don't answer the question.
**Consequences.** Refusals are machine-detectable, so they can be counted, shown differently in the UI and evaluated. A model that paraphrases the sentence is scored as not refusing, which is the safe direction for the metric.

## ADR-3 · Rule-based routing to the instrument tool, not model function calling

**Context.** One read-only tool, used for one kind of question, with a small local model.
**Decision.** A regular expression detects power-meter questions; the tool runs before the model and its reading is supplied as passage `[T1]`.
**Consequences.** Deterministic, unit-testable and one model call per question. Adding many tools would justify moving to function calling; with one tool it would add a second model round trip and a new failure mode.

## ADR-4 · Citations are checked, not trusted

**Decision.** Every `[S#]`/`[T#]` in the answer is compared with the labels actually supplied; extras are returned as `invalid_citations` and shown as a warning.
**Consequences.** A fabricated citation is visible to the user at answer time, not only in the eval.

## ADR-5 · Model behind an OpenAI-compatible interface

**Decision.** The model is addressed by base URL, model name and key from the environment.
**Consequences.** The same code runs on the client's llama.cpp server or a hosted provider; the eval compares them on identical questions, which is how the cost question in the brief gets a measured answer.

## ADR-6 · Deterministic eval checks

See [03-eval-spec.md](03-eval-spec.md). Pattern-matched facts instead of an LLM judge: auditable, repeatable, strict.
