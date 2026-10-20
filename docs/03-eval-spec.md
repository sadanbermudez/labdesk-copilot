# 03 · Evaluation spec

What "good" means, measured before anyone relies on the assistant.

## Two question sets

### Development set (`evals/questions.jsonl`)

Used while building: free to look at, debug against and fix. 41 questions written from the documentation, the kinds the brief describes:

- **33 in-scope:** installation, backends, configuration file, resource names, termination characters, timeouts, serial settings, reading ASCII and binary data, events, the shell, migration, errors from the FAQ. Each has the documentation file(s) that answer it (`gold`) and the facts a correct answer must contain (`must`, a list of groups; each group is a set of acceptable spellings, and every group must appear).
- **6 out-of-scope:** buying advice, another vendor's SCPI command, MATLAB, instrument prices, unrelated requests. The right answer is the refusal sentence.
- **2 instrument:** the live power-meter reading and its identity. The right answer contains the values the tool returns.

### Held-out test set (`evals/heldout.jsonl`)

The development scores measure how well the system fits questions its builder has seen. The held-out set measures how it does on questions nobody tuned it for, which is what the client will actually send.

- **42 questions:** 31 in-scope, 8 out-of-scope, 3 instrument. Written after development run 2, from doc sections the development set barely touches (binary block headers, events with handlers, the shell, installation, VISA attributes, CI).
- **Phrased as support tickets**, with symptoms and goals rather than the docs' identifiers ("my scope sends hex numbers", not "what does `converter` do"). This is deliberately harder for lexical retrieval.
- **One trap:** "How do I calibrate the power meter's wavelength correction?" mentions the power meter, so the tool router fires, but neither the docs nor the tool answer it. The right answer is the refusal.
- **Frozen before use:** committed (07ba575) before the system answered any of it, so the git history shows the order.
- **Never used for tuning.** A change made because of a held-out failure spends the set; its questions then move to the development set and a new held-out set is written.

## Metrics

| Metric | Definition | Target |
|---|---|---|
| Retrieval recall@5 | Share of in-scope questions with at least one gold file in the top 5 retrieved sections | ≥ 0.90 |
| Retrieval MRR | Mean reciprocal rank of the first gold section | reported |
| Correctness | Share of in-scope answers containing every required fact group | ≥ 0.85 |
| Citation validity | Share of in-scope answers whose citations include at least one gold file, and cite nothing that was not supplied | ≥ 0.85 |
| Refusal accuracy | Share of out-of-scope questions answered with the refusal sentence | ≥ 0.80 |
| Over-refusal | Share of in-scope questions refused | ≤ 0.10 |
| Tool accuracy | Instrument questions whose answer contains the tool's actual values | 2 / 2 |
| Latency | p50 and p95 seconds per answer | p95 < 10 s |
| Tokens and cost | Prompt and completion tokens per answer; cost at the configured price | reported |

## Why these checks are deterministic

Facts are matched with fixed patterns, not judged by another model, so a score means the same thing every run and can be audited line by line. The trade-off is strictness: a correct answer phrased in an unexpected way can fail. The report lists every failure with the answer text so a person can review it, and failures caused by the checker are fixed in the checker, never by editing answers.

## Known limit of the retrieval metric

Gold labels are files, not sections. A question counts as retrieved if any section of a gold file is in the top 5, even when it is the wrong section of that file. Run 1 showed this: `list-resources` scored as retrieved while the section that answers it was missing. Recall@5 therefore flatters retrieval on this small corpus; MRR and the end-to-end correctness score are the more honest signals.

## Checker corrections (log)

Every change to the checker after seeing answers, with the evidence. Answers are never edited. Run 1's results are kept in `evals/results/run1-*`.

| Run | Question | Fault | Fix |
|---|---|---|---|
| 1 | `term-rs232`, `term-common` | Pattern `\r` matched a carriage-return character, not the printed `\r` the docs and answers use | Pattern now matches the backslash and the letter |
| 1 | `not-found` | Required "bitness", but the FAQ section on this error does not mention it (bitness belongs to "No matching architecture") | Now requires the fixes that section gives: a configuration file, or the library path to the constructor |
| 1 | `query-what` | Gold list missed `faq/migrating.rst`, whose "Ask vs. query" section states query is a write followed by a read | Added to gold |
| 2 | `oos-price` | Labelled out-of-scope, but `introduction/getting.rst` says the NI and Keysight libraries "can both be downloaded for free": the docs do answer it, so a refusal was wrongly scored as correct. Found while writing the held-out set | Replaced with a question the docs really do not cover (the price of a specific multimeter) |

## When it runs

- **On every push (CI):** unit tests, plus the retrieval evaluation, which needs no model. The build fails if recall@5 falls below 0.90.
- **Before any release or model or prompt change:** the full evaluation against the model server on the development set (`evals/results/<model>.json`, `docs/report.md`), then once on the held-out set (`--set heldout`, `docs/report-heldout.md`). The held-out number is the one to quote.
