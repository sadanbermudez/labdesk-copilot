"""Unit tests. No model server needed: a fake client stands in for it."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from labdesk.answer import REFUSAL, Assistant, build_messages, is_refusal
from labdesk.api import create_app
from labdesk.corpus import SOURCE_URL, load
from labdesk.instrument import read_power_meter
from labdesk.llm import Completion
from labdesk.retrieve import BM25, tokenize
from labdesk.telemetry import Telemetry, cost_usd, percentile


class FakeClient:
    model = "fake"

    def __init__(self, reply: str):
        self.reply = reply
        self.seen: list[dict] = []

    def complete(self, messages, max_tokens=600):
        self.seen = messages
        return Completion(self.reply, prompt_tokens=1000, completion_tokens=50, seconds=0.01, model="fake")

    def healthy(self):
        return True


@pytest.fixture(scope="module")
def chunks():
    return load()


@pytest.fixture(scope="module")
def index(chunks):
    return BM25(chunks)


def test_corpus_sections_have_titles_and_links(chunks):
    assert len(chunks) > 50
    assert all(c.title and c.text for c in chunks)
    assert all(c.url.startswith(SOURCE_URL) and c.url.endswith(".rst") for c in chunks)
    assert not any(".. include::" in c.text for c in chunks)


def test_tokenize_splits_identifiers():
    toks = tokenize("Set read_termination on ASRL2")
    assert {"read_termination", "read", "termination", "asrl2"} <= set(toks)


def test_retrieval_finds_the_timeout_section(index):
    top = index.search("how do I set an infinite timeout", 3)
    assert top[0][0].path == "introduction/resources.rst"


def test_retrieval_finds_faq_for_missing_library(index):
    top = index.search("Could not find VISA library", 3)
    assert top[0][0].path == "faq/faq.rst"


def test_prompt_numbers_passages_and_question(index):
    hits = [c for c, _ in index.search("baud rate", 2)]
    msgs = build_messages("What baud rate?", hits, None)
    assert msgs[0]["role"] == "system" and REFUSAL in msgs[0]["content"]
    assert "[S1]" in msgs[1]["content"] and "[S2]" in msgs[1]["content"]
    assert "[T1]" not in msgs[1]["content"]


def test_citations_are_validated(index):
    a = Assistant(index, FakeClient("Use 9600 baud [S1]. Also see [S9].")).ask("default baud rate serial")
    assert a.cited == ["S1", "S9"]
    assert a.invalid_citations == ["S9"]  # only S1..S5 were supplied
    assert not a.refused


def test_refusal_is_detected(index):
    a = Assistant(index, FakeClient(REFUSAL)).ask("Which oscilloscope should I buy?")
    assert a.refused and is_refusal(REFUSAL) and a.cited == []


def test_power_meter_question_uses_the_tool(index):
    client = FakeClient("It reads 123.4 mW [T1].")
    a = Assistant(index, client).ask("What does the power meter read?")
    assert a.tool_used and a.invalid_citations == []
    assert "123.4 mW" in client.seen[1]["content"]


def test_doc_question_does_not_use_the_tool(index):
    a = Assistant(index, FakeClient("x [S1]")).ask("How do I list resources?")
    assert not a.tool_used


def test_simulated_power_meter():
    r = read_power_meter()
    assert r.ok and r.identity.startswith("Thorlabs,PM100USB,P2000123")
    assert r.power_mw == pytest.approx(123.4)


def test_power_meter_failure_is_reported_not_raised(monkeypatch):
    monkeypatch.setenv("LABDESK_POWER_METER", "USB0::0xDEAD::0xBEEF::NOPE::INSTR")
    r = read_power_meter()
    assert not r.ok and "could not read" in r.as_passage()


def test_cost_and_percentiles():
    assert cost_usd(1_000_000, 1_000_000, (0.15, 0.60)) == pytest.approx(0.75)
    assert percentile([1, 2, 3, 4], 0.5) == pytest.approx(2.5)
    assert percentile([], 0.95) == 0.0


def test_api_ask_health_metrics(tmp_path):
    tel = Telemetry(tmp_path / "log.jsonl")
    app = create_app(client=FakeClient("Set timeout to None [S1]."), telemetry=tel)
    c = TestClient(app)
    assert c.get("/health").json()["status"] == "ok"
    r = c.post("/ask", json={"question": "How do I set an infinite timeout?"}).json()
    assert r["cited"] == ["S1"] and r["tokens"] == {"prompt": 1000, "completion": 50}
    assert r["sources"][0]["url"].startswith(SOURCE_URL)
    m = c.get("/metrics").json()
    assert m["requests"] == 1 and m["tokens_in"] == 1000
    row = json.loads((tmp_path / "log.jsonl").read_text().splitlines()[0])
    assert row["question"].startswith("How do I set") and row["retrieved_paths"]
    assert c.post("/ask", json={"question": ""}).status_code == 422
    assert "LabDesk" in c.get("/").text
