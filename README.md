# LabDesk

[![ci](https://github.com/sadanbermudez/labdesk-copilot/actions/workflows/ci.yml/badge.svg)](https://github.com/sadanbermudez/labdesk-copilot/actions/workflows/ci.yml)

A support assistant for the PyVISA instrument-control library that answers **only from the official documentation**, cites the section behind every sentence, says so when the docs don't cover a question, and can read a live power meter. It runs on a local model.

This repository is a **simulated forward-deployed engagement**: the client in the brief is invented to frame the work the way a real one arrives. Everything after the brief (requirements, code, evaluation and numbers) is real and reproducible.

## The engagement, in order

| Step | Document |
|---|---|
| What the client asked for | [01-brief.md](docs/01-brief.md) |
| Requirements, each with a target and how it is verified | [02-requirements.md](docs/02-requirements.md) |
| What "good" means before anyone relies on it | [03-eval-spec.md](docs/03-eval-spec.md) |
| Design and the decisions behind it (six ADRs) | [04-architecture.md](docs/04-architecture.md) |
| Running, monitoring and changing it after handover | [05-handover.md](docs/05-handover.md) |
| Measured results, every failure listed | [report.md](docs/report.md) |

## Results

41 questions (33 answerable from the docs, 6 off-topic, 2 for the instrument), local `Qwen3.6-35B-A3B` Q4 on an AMD Ryzen AI Max+ 392 laptop, temperature 0. Full report with every failure: [docs/report.md](docs/report.md).

| Metric | Result | Target |
|---|---|---|
| Correct answers (in-scope) | **31 / 33** (0.94) | ≥ 0.85 |
| Cites a section that actually answers it | **32 / 33** (0.97) | ≥ 0.85 |
| Off-topic questions refused | **6 / 6** | ≥ 0.80 |
| In-scope questions wrongly refused | 1 / 33 | ≤ 10% |
| Instrument tool questions | 2 / 2 | 2 / 2 |
| Latency p50 / p95 | 3.3 s / 5.6 s | p95 < 10 s |
| Tokens per question | 1,906 in, 63 out | |
| Cost per 1,000 questions | $0 local; $0.32 at an illustrative $0.15 / $0.60 per M tokens | |

**The two failures, both real:**

- *"How do I see which instruments are connected?"* shares no words with `list_resources`, so BM25 never retrieved the section that answers it. The model did the right thing with what it had and refused instead of guessing. This is the paraphrase weakness predicted in ADR-1.
- *"How do I list every resource?"* The model copied `'?'` where the docs say `'?*'`. A fluent, wrong, cited answer: the exact failure the client feared, caught by the eval and not by reading the answer.

I have not tuned anything to make these two pass. With only 33 questions there is no held-out set, so a synonym list or prompt tweak aimed at them would be teaching to the test. The next step is a second, unseen question set, then hybrid retrieval (BM25 plus embeddings) judged on it.

**Run 1** scored 29 / 33. Three of its four extra failures were faults in my checker, not the model; each correction and its evidence is logged in [03-eval-spec.md](docs/03-eval-spec.md), and run 1's raw results are kept in `evals/results/`.

## How it works

```
question ──► BM25 over 98 doc sections ──► top 5 passages [S1..S5] ─┐
        └──► power-meter question? ──► read-only VISA tool ──► [T1] ┤
                                                                    ▼
                 prompt: answer only from passages, cite, or refuse with a fixed sentence
                                                                    ▼
                         OpenAI-compatible model server (local llama.cpp)
                                                                    ▼
             citations checked against what was supplied ──► answer + sources + telemetry
```

- **Retrieval:** BM25 over the PyVISA 1.16.2 `.rst` docs split at headings. No vector store: users ask with the docs' own identifiers, and lexical search is exact, deterministic and testable in CI ([ADR-1](docs/04-architecture.md)).
- **Grounding:** fixed refusal sentence, so refusals can be counted; citations checked against the passages actually supplied, with fabricated ones shown as a warning ([ADR-2, ADR-4](docs/04-architecture.md)).
- **Tool:** a read-only PM100USB power-meter reader. Simulated with pyvisa-sim by default; two environment variables point it at real hardware ([ADR-3](docs/04-architecture.md)).
- **Service:** FastAPI with `POST /ask`, `GET /health`, `GET /metrics` and a one-page UI; every request logged as JSON with sources, tokens, latency and cost.
- **Quality gate:** 13 unit tests and a retrieval eval run in CI on every push; the full eval runs against the model before any model or prompt change.

## Run

```
python -m venv .venv
.venv\Scripts\pip install -e ".[test]"
.venv\Scripts\python -m pytest
.venv\Scripts\python evals\run_eval.py --retrieval-only
.venv\Scripts\python evals\run_eval.py --price-in 0.15 --price-out 0.60     # needs a model server
labdesk --port 8790
```

Model server, model name, key, instrument and prices are set by environment variables; see [05-handover.md](docs/05-handover.md).

## Licences

Code: MIT. The documentation corpus in `corpus/pyvisa/` is PyVISA's, under its MIT licence (included).

Built with AI assistance (Claude Code), directed and reviewed by Sergio Adan Bermudez.
