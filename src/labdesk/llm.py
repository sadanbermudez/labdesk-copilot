"""Minimal client for any OpenAI-compatible chat endpoint (llama.cpp, vLLM, OpenRouter).

Configuration comes from the environment so the same code runs on-premises or
against a hosted model:

  LABDESK_BASE_URL      default http://127.0.0.1:18434/v1 (local llama.cpp router)
  LABDESK_MODEL         default Qwen3.6-35B-A3B-UD-Q4_K_M
  LABDESK_API_KEY       the key itself, or
  LABDESK_API_KEY_FILE  a file holding it (default: the local router's key file)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

import httpx

DEFAULT_BASE = "http://127.0.0.1:18434/v1"
DEFAULT_MODEL = "Qwen3.6-35B-A3B-UD-Q4_K_M"
DEFAULT_KEY_FILE = Path(os.environ.get("LOCALAPPDATA", "~")).expanduser() / "hermes/runtimes/llamacpp/.api_key"


@dataclass
class Completion:
    text: str
    prompt_tokens: int
    completion_tokens: int
    seconds: float
    model: str


def _api_key() -> str | None:
    if key := os.environ.get("LABDESK_API_KEY"):
        return key
    path = Path(os.environ.get("LABDESK_API_KEY_FILE", DEFAULT_KEY_FILE))
    return path.read_text().strip() if path.is_file() else None


class ChatClient:
    def __init__(self, base_url: str | None = None, model: str | None = None, timeout: float = 120):
        self.base_url = (base_url or os.environ.get("LABDESK_BASE_URL", DEFAULT_BASE)).rstrip("/")
        self.model = model or os.environ.get("LABDESK_MODEL", DEFAULT_MODEL)
        key = _api_key()
        headers = {"Authorization": f"Bearer {key}"} if key else {}
        self.http = httpx.Client(timeout=timeout, headers=headers)

    def complete(self, messages: list[dict], max_tokens: int = 600) -> Completion:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": 0,
            "max_tokens": max_tokens,
            # Qwen3 thinking mode adds minutes of hidden reasoning on a laptop; off for support chat.
            "chat_template_kwargs": {"enable_thinking": False},
        }
        t0 = time.perf_counter()
        r = self.http.post(f"{self.base_url}/chat/completions", json=body)
        r.raise_for_status()
        data = r.json()
        usage = data.get("usage") or {}
        return Completion(
            text=data["choices"][0]["message"].get("content") or "",
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            seconds=time.perf_counter() - t0,
            model=data.get("model", self.model),
        )

    def healthy(self) -> bool:
        try:
            return self.http.get(f"{self.base_url}/models", timeout=5).status_code == 200
        except httpx.HTTPError:
            return False
