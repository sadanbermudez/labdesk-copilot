"""Per-request log and running metrics.

Each request is appended as one JSON line (question, sources, citations,
tokens, latency, cost) so quality problems can be traced to a specific answer.
Cost uses per-million-token prices from the environment; on-premises defaults to 0.

  LABDESK_PRICE_IN_PER_M, LABDESK_PRICE_OUT_PER_M   USD per million tokens
  LABDESK_LOG                                        path of the JSONL log
"""

from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict
from pathlib import Path

from .answer import Answer


def price() -> tuple[float, float]:
    return (
        float(os.environ.get("LABDESK_PRICE_IN_PER_M", 0)),
        float(os.environ.get("LABDESK_PRICE_OUT_PER_M", 0)),
    )


def cost_usd(prompt_tokens: int, completion_tokens: int, prices: tuple[float, float] | None = None) -> float:
    p_in, p_out = prices or price()
    return (prompt_tokens * p_in + completion_tokens * p_out) / 1e6


def percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    pos = (len(s) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


class Telemetry:
    def __init__(self, log_path: Path | None = None):
        self.path = Path(log_path or os.environ.get("LABDESK_LOG", "logs/requests.jsonl"))
        self.lock = threading.Lock()
        self.latencies: list[float] = []
        self.count = self.refusals = self.invalid = self.tool_calls = 0
        self.tokens_in = self.tokens_out = 0
        self.cost = 0.0

    def record(self, a: Answer) -> dict:
        cost = cost_usd(a.prompt_tokens, a.completion_tokens)
        row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **asdict(a), "cost_usd": cost}
        with self.lock:
            self.count += 1
            self.refusals += a.refused
            self.invalid += bool(a.invalid_citations)
            self.tool_calls += a.tool_used
            self.tokens_in += a.prompt_tokens
            self.tokens_out += a.completion_tokens
            self.cost += cost
            self.latencies.append(a.latency_s)
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row) + "\n")
        return row

    def metrics(self) -> dict:
        with self.lock:
            return {
                "requests": self.count,
                "refusal_rate": self.refusals / self.count if self.count else 0.0,
                "invalid_citation_rate": self.invalid / self.count if self.count else 0.0,
                "tool_calls": self.tool_calls,
                "latency_p50_s": round(percentile(self.latencies, 0.5), 3),
                "latency_p95_s": round(percentile(self.latencies, 0.95), 3),
                "tokens_in": self.tokens_in,
                "tokens_out": self.tokens_out,
                "cost_usd": round(self.cost, 6),
            }
