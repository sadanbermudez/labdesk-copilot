"""HTTP service: POST /ask, GET /health, GET /metrics, and a one-page UI at /."""

from __future__ import annotations

import argparse
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from . import __version__
from .answer import Assistant
from .corpus import DOCS_VERSION, load
from .llm import ChatClient
from .retrieve import BM25
from .telemetry import Telemetry, cost_usd

STATIC = Path(__file__).with_name("static")


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


def create_app(client: ChatClient | None = None, telemetry: Telemetry | None = None) -> FastAPI:
    chunks = load()
    client = client or ChatClient()
    assistant = Assistant(BM25(chunks), client)
    tel = telemetry or Telemetry()
    app = FastAPI(title="LabDesk", version=__version__)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC / "index.html")

    @app.get("/health")
    def health() -> dict:
        return {
            "status": "ok",
            "model_server": client.healthy(),
            "model": client.model,
            "docs_version": DOCS_VERSION,
            "sections": len(chunks),
        }

    @app.get("/metrics")
    def metrics() -> dict:
        return tel.metrics()

    @app.post("/ask")
    def ask(req: AskRequest) -> dict:
        try:
            a = assistant.ask(req.question)
        except Exception as exc:
            raise HTTPException(502, f"model server error: {type(exc).__name__}") from exc
        tel.record(a)
        return {
            "answer": a.text,
            "refused": a.refused,
            "sources": a.sources,
            "cited": a.cited,
            "invalid_citations": a.invalid_citations,
            "tool_used": a.tool_used,
            "latency_s": round(a.latency_s, 3),
            "tokens": {"prompt": a.prompt_tokens, "completion": a.completion_tokens},
            "cost_usd": cost_usd(a.prompt_tokens, a.completion_tokens),
            "model": a.model,
        }

    return app


def main() -> None:
    import uvicorn

    p = argparse.ArgumentParser(description="LabDesk PyVISA support assistant")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8790)
    args = p.parse_args()
    uvicorn.run(create_app(), host=args.host, port=args.port)


if __name__ == "__main__":
    main()
