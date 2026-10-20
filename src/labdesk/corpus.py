"""Split the PyVISA reStructuredText docs into citable sections.

Each section keeps its file path, heading trail and a link to the same file
on GitHub at the pinned release, so every answer can point at its source.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DOCS_VERSION = "1.16.2"
SOURCE_URL = f"https://github.com/pyvisa/pyvisa/blob/{DOCS_VERSION}/docs/source/"
DEFAULT_CORPUS = Path(__file__).resolve().parents[2] / "corpus" / "pyvisa"

UNDERLINE = re.compile(r"^([=\-~^\"'*+#])\1{2,}\s*$")
DROP_LINE = re.compile(r"^\.\. (_[\w-]+:|include::|toctree::|currentmodule::|module::)")
MAX_CHARS = 1800
MIN_CHARS = 120


@dataclass(frozen=True)
class Chunk:
    id: str
    path: str  # relative to the docs root, e.g. "introduction/communication.rst"
    title: str  # "Document title > Section"
    text: str

    @property
    def url(self) -> str:
        return SOURCE_URL + self.path


def _sections(lines: list[str]) -> list[tuple[str, list[str]]]:
    """Return (heading, body lines) pairs; text before the first heading is heading ''."""
    out: list[tuple[str, list[str]]] = [("", [])]
    i = 0
    while i < len(lines):
        line = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        is_heading = (
            line.strip()
            and not UNDERLINE.match(line)
            and UNDERLINE.match(nxt)
            and len(nxt.rstrip()) >= len(line.rstrip())
        )
        if is_heading:
            # An overline above the title belongs to the heading, not the previous body.
            if out[-1][1] and UNDERLINE.match(out[-1][1][-1]):
                out[-1][1].pop()
            out.append((line.strip(), []))
            i += 2
            continue
        if not DROP_LINE.match(line):
            out[-1][1].append(line)
        i += 1
    return out


def _split_long(text: str) -> list[str]:
    if len(text) <= MAX_CHARS:
        return [text]
    parts, cur = [], ""
    for para in re.split(r"\n\s*\n", text):
        if cur and len(cur) + len(para) > MAX_CHARS:
            parts.append(cur.strip())
            cur = ""
        cur += para + "\n\n"
    if cur.strip():
        parts.append(cur.strip())
    return parts


def load(root: Path = DEFAULT_CORPUS) -> list[Chunk]:
    chunks: list[Chunk] = []
    for file in sorted(root.rglob("*.rst")):
        rel = file.relative_to(root).as_posix()
        sections = _sections(file.read_text(encoding="utf-8").splitlines())
        doc_title = next((h for h, _ in sections if h), rel)
        for heading, body in sections:
            text = "\n".join(body).strip()
            if len(text) < MIN_CHARS:
                continue
            title = doc_title if heading in ("", doc_title) else f"{doc_title} > {heading}"
            for n, part in enumerate(_split_long(text)):
                chunks.append(Chunk(id=f"{rel}#{len(chunks)}", path=rel, title=title, text=part))
    return chunks
