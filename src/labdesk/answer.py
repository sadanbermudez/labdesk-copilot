"""Retrieve, call the model, check its citations.

The model only sees the retrieved passages (and, for power-meter questions, the
instrument tool's reading). It must cite them as [S1], [T1]... or reply with the
fixed refusal sentence. Citations are checked against what was actually supplied.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field

from .corpus import Chunk
from .instrument import read_power_meter
from .llm import ChatClient
from .retrieve import BM25

REFUSAL = "The PyVISA documentation I have does not cover this."

SYSTEM = f"""You are LabDesk, a support assistant for the PyVISA Python library (version 1.16.2).
Answer ONLY from the numbered passages provided. Never use outside knowledge, never invent methods, arguments or values.
Cite every factual sentence with the passage label in square brackets, for example [S2] or [T1].
If the passages do not contain the answer, reply with exactly this sentence and nothing else:
{REFUSAL}
Keep answers short and practical: a few sentences, plus a short code example when the passages show one."""

TOOL_INTENT = re.compile(
    r"\b(power ?meter|pm100\w*|live reading|current reading|what does (it|the meter) read|"
    r"is the (meter|instrument) (connected|talking|responding))\b",
    re.I,
)
CITATION = re.compile(r"\[([ST]\d+)\]")


@dataclass
class Answer:
    question: str
    text: str
    refused: bool
    sources: list[dict]  # what was supplied, label -> section
    cited: list[str]  # labels the answer used
    invalid_citations: list[str]  # labels cited but never supplied
    tool_used: bool
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    model: str = ""
    retrieved_paths: list[str] = field(default_factory=list)


def is_refusal(text: str) -> bool:
    return REFUSAL.lower().rstrip(".") in text.lower()


def build_messages(question: str, hits: list[Chunk], tool_text: str | None) -> list[dict]:
    blocks = [f"[S{i}] {c.title} ({c.path})\n{c.text}" for i, c in enumerate(hits, 1)]
    if tool_text:
        blocks.append(f"[T1] {tool_text}")
    user = "Passages:\n\n" + "\n\n---\n\n".join(blocks) + f"\n\nQuestion: {question}"
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user}]


class Assistant:
    def __init__(self, index: BM25, client: ChatClient, k: int = 5):
        self.index, self.client, self.k = index, client, k

    def ask(self, question: str) -> Answer:
        t0 = time.perf_counter()
        hits = [c for c, _ in self.index.search(question, self.k)]
        tool_text = read_power_meter().as_passage() if TOOL_INTENT.search(question) else None
        out = self.client.complete(build_messages(question, hits, tool_text))

        supplied = {f"S{i}": c for i, c in enumerate(hits, 1)}
        sources = [{"label": k, "title": c.title, "path": c.path, "url": c.url} for k, c in supplied.items()]
        if tool_text:
            sources.append({"label": "T1", "title": "Instrument tool (power meter)", "path": "", "url": ""})
        cited = list(dict.fromkeys(CITATION.findall(out.text)))
        valid = set(supplied) | ({"T1"} if tool_text else set())
        return Answer(
            question=question,
            text=out.text.strip(),
            refused=is_refusal(out.text),
            sources=sources,
            cited=cited,
            invalid_citations=[c for c in cited if c not in valid],
            tool_used=tool_text is not None,
            prompt_tokens=out.prompt_tokens,
            completion_tokens=out.completion_tokens,
            latency_s=time.perf_counter() - t0,
            model=out.model,
            retrieved_paths=[c.path for c in hits],
        )
