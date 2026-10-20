"""BM25 retrieval over the documentation sections.

Lexical search suits this corpus: users ask with the same identifiers the docs
use (query_delay, read_termination, ASRL1::INSTR), and BM25 matches those
exactly, needs no model, and gives the same ranking on every run.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from .corpus import Chunk

STOP = set(
    "a an and are as at be by can do does for from how i if in is it its me my of on or "
    "that the this to what when which with you your should there their".split()
)
TOKEN = re.compile(r"[a-z0-9_*?@]+")


def tokenize(text: str) -> list[str]:
    out = []
    for tok in TOKEN.findall(text.lower()):
        if tok in STOP:
            continue
        out.append(tok)
        if "_" in tok:  # read_termination also matches "read" and "termination"
            out.extend(p for p in tok.split("_") if p and p not in STOP)
    return out


class BM25:
    def __init__(self, chunks: list[Chunk], k1: float = 1.4, b: float = 0.75, title_weight: int = 2):
        self.chunks = chunks
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize((c.title + " ") * title_weight + c.text)) for c in chunks]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = sum(self.lengths) / len(self.lengths)
        df = Counter(t for d in self.docs for t in d)
        n = len(chunks)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def search(self, query: str, k: int = 5) -> list[tuple[Chunk, float]]:
        terms = tokenize(query)
        scores = []
        for i, doc in enumerate(self.docs):
            s = 0.0
            norm = self.k1 * (1 - self.b + self.b * self.lengths[i] / self.avg)
            for t in terms:
                f = doc.get(t)
                if f:
                    s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
            if s > 0:
                scores.append((s, i))
        scores.sort(reverse=True)
        return [(self.chunks[i], s) for s, i in scores[:k]]
