# 05 · Handover and runbook

For the engineers who maintain LabDesk after the engagement.

## Run it

```
python -m venv .venv
.venv\Scripts\pip install -e ".[test]"          # Linux/macOS: .venv/bin/pip
labdesk --port 8790                              # http://127.0.0.1:8790
```

| Variable | Default | Purpose |
|---|---|---|
| `LABDESK_BASE_URL` | `http://127.0.0.1:18434/v1` | Model server (any OpenAI-compatible endpoint) |
| `LABDESK_MODEL` | `Qwen3.6-35B-A3B-UD-Q4_K_M` | Model name on that server |
| `LABDESK_API_KEY` / `LABDESK_API_KEY_FILE` | local router key file | Credential; never commit it, never log it |
| `LABDESK_VISA_BACKEND` | simulated PM100USB | `@ivi` or `@py` for real hardware |
| `LABDESK_POWER_METER` | `USB0::0x1313::0x8078::P2000123::INSTR` | Resource name of the meter |
| `LABDESK_PRICE_IN_PER_M`, `LABDESK_PRICE_OUT_PER_M` | 0 | USD per million tokens, for the cost field |
| `LABDESK_LOG` | `logs/requests.jsonl` | Request log |

## Check it is healthy

- `GET /health`: `model_server: true` means the model endpoint answers.
- `GET /metrics`: request count, refusal rate, invalid-citation rate, latency p50/p95, tokens, cost since start.
- `logs/requests.jsonl`: one line per question with the sources it saw and cited.

## Common changes

| Change | Steps |
|---|---|
| New PyVISA release | Replace `corpus/pyvisa/` with the new `docs/source`, update `DOCS_VERSION` in `corpus.py`, run the full eval, compare with the last report before deploying |
| Different model | Set `LABDESK_MODEL` (and URL/key), run `python evals/run_eval.py`, compare `docs/report.md` with the previous one |
| Prompt change | Edit `SYSTEM` in `answer.py`, run the full eval; never ship a prompt change without it |
| Add a question the bot got wrong | Add a line to `evals/make_questions.py` with gold files and required facts checked against the docs, regenerate `questions.jsonl` |

## Incidents

| Symptom | Likely cause | Action |
|---|---|---|
| `/ask` returns 502 | Model server down or key wrong | `/health`; check the server and the key file |
| Answers slow | Model reasoning mode on, or server overloaded | Confirm `enable_thinking` is false for Qwen; check server load |
| Many refusals on real questions | Retrieval missing sections, or a model change | Run `run_eval.py --retrieval-only`, then the full eval; read the failures in the report |
| `invalid_citations` appearing | Model citing passages it was not given | Run the full eval; if citation validity dropped, roll back the model or prompt |
| Power meter "could not read" | Wrong resource name or backend, cable, or VISA not installed | `pyvisa-info`; `pyvisa-shell` with the same backend |
