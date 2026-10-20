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
| Measured results, every failure listed | [report-heldout.md](docs/report-heldout.md), [report.md](docs/report.md) |

## Results

Two question sets, local `Qwen3.6-35B-A3B` Q4 on an AMD Ryzen AI Max+ 392 laptop, temperature 0. The **held-out set** was written after development, phrased like real tickets, and committed before the system ever saw it ([07ba575](https://github.com/sadanbermudez/labdesk-copilot/commit/07ba575)); it is the number to quote. Full reports with every failure: [held-out](docs/report-heldout.md), [development](docs/report.md).

| Metric | Held-out (42 q) | Development (41 q) | Target |
|---|---|---|---|
| Correct answers (in-scope) | **26 / 31** (0.84) | 31 / 33 (0.94) | ≥ 0.85 |
| Cites a section that actually answers it | **27 / 31** (0.87) | 32 / 33 (0.97) | ≥ 0.85 |
| Off-topic questions refused | **8 / 8** | 6 / 6 | ≥ 0.80 |
| In-scope questions wrongly refused | 3 / 31 | 1 / 33 | ≤ 10% |
| Instrument tool questions | 3 / 3 | 2 / 2 | all |
| Retrieval recall@5 / MRR | 0.90 / 0.79 | 1.00 / 0.94 | ≥ 0.90 |
| Latency p50 / p95 | 2.7 s / 4.8 s | 3.3 s / 5.0 s | p95 < 10 s |
| Cost per 1,000 questions | $0 local; $0.27 at an illustrative $0.15 / $0.60 per M tokens | $0.33 | |

**The held-out set misses the correctness target by one answer.** That is the point of having one: the development score (0.94) measured how well the system fits questions its builder had seen. The five held-out failures, all real:

- **Three retrieval misses on reworded questions** ("can I test without the instrument connected", "can I use the shell without NI-VISA", "how does it decide which object to return"). BM25 never surfaced the section, and in two of the three the model correctly refused rather than guess. This is the paraphrase weakness predicted in [ADR-1](docs/04-architecture.md), now measured: recall@5 drops from 1.00 to 0.90 and MRR from 0.94 to 0.79.
- **One answer plus a refusal.** Asked whether PyVISA is an NI product, the model answered "no" correctly, then appended the refusal sentence.
- **One incomplete answer.** Asked whether the event queue and a handler can run together, it said yes but missed `EventMechanism.all`.
- The trap question (a power-meter calibration question that triggers the instrument tool but that nothing answers) was correctly refused.

**Development set:** two real failures remain there too (a paraphrase miss, and the model writing `'?'` where the docs say `'?*'`). Across three runs, four failures turned out to be faults in my evaluation, not the model (two checker patterns, an incomplete gold list, and an off-topic question the docs actually answer). Each is logged with its evidence in [03-eval-spec.md](docs/03-eval-spec.md); raw results of every run are kept in `evals/results/`.

**What happens next, and why in this order.** Retrieval is the bottleneck on both sets, so the next change is hybrid retrieval (BM25 plus embeddings), developed against the development set only. Because the held-out failures are now known, this held-out set is spent once that change is made: its questions move to the development set and a new held-out set is written before the change is judged.

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
