"""Minimal client for a local LLM served by Ollama, with an on-disk cache.

Standard library only. Two properties matter for the experiments:

* Determinism: temperature 0 and a fixed seed, so a rerun reproduces the run.
* Caching: responses are stored in SQLite keyed by a hash of the full request
  (model, messages, schema, options). Identical prompts — common, because
  scenarios on the same trace share every alarm before the planner first
  acts — cost nothing the second time, and a reviewer can replay a sweep
  without a GPU by shipping the cache file.

Failures are never swallowed: a transport error raises `LLMError`; a response
that is not valid JSON is returned with `ok=False` so the planner can record
it as a rejected decision.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

DEFAULT_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:7b"


class LLMError(RuntimeError):
    pass


@dataclass
class LLMResponse:
    content: str
    parsed: Any | None
    ok: bool
    latency_s: float
    prompt_tokens: int | None
    output_tokens: int | None
    cached: bool
    key: str


class ChatModel(Protocol):
    model: str

    def chat(self, messages: list[dict], schema: dict | None = None) -> LLMResponse: ...


@dataclass
class OllamaClient:
    model: str = DEFAULT_MODEL
    url: str = DEFAULT_URL
    temperature: float = 0.0
    seed: int = 7
    num_predict: int = 400
    timeout_s: float = 300.0
    cache_path: Path | None = None
    stats: dict = field(default_factory=lambda: {"calls": 0, "cache_hits": 0, "seconds": 0.0, "invalid_json": 0})

    def __post_init__(self) -> None:
        self._db = None
        if self.cache_path is not None:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(self.cache_path, timeout=60)
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS responses ("
                " key TEXT PRIMARY KEY, model TEXT, request TEXT, response TEXT,"
                " latency_s REAL, prompt_tokens INTEGER, output_tokens INTEGER, created REAL)"
            )
            self._db.commit()

    def _options(self) -> dict:
        return {"temperature": self.temperature, "seed": self.seed, "num_predict": self.num_predict}

    def chat(self, messages: list[dict], schema: dict | None = None) -> LLMResponse:
        request = {"model": self.model, "messages": messages, "format": schema, "options": self._options()}
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        self.stats["calls"] += 1

        if self._db is not None:
            row = self._db.execute(
                "SELECT response, latency_s, prompt_tokens, output_tokens FROM responses WHERE key = ?", (key,)
            ).fetchone()
            if row is not None:
                self.stats["cache_hits"] += 1
                return self._wrap(row[0], row[1], row[2], row[3], True, key)

        body = json.dumps({**request, "stream": False}).encode()
        req = urllib.request.Request(f"{self.url}/api/chat", body, {"Content-Type": "application/json"})
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                payload = json.load(resp)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            raise LLMError(f"Ollama request failed ({self.url}, model {self.model}): {exc}") from exc
        latency = time.perf_counter() - t0
        self.stats["seconds"] += latency

        if "message" not in payload:
            raise LLMError(f"unexpected Ollama response: {str(payload)[:300]}")
        content = payload["message"].get("content", "")
        p_tok, o_tok = payload.get("prompt_eval_count"), payload.get("eval_count")

        if self._db is not None:
            self._db.execute(
                "INSERT OR REPLACE INTO responses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (key, self.model, json.dumps(request), content, latency, p_tok, o_tok, time.time()),
            )
            self._db.commit()
        return self._wrap(content, latency, p_tok, o_tok, False, key)

    def _wrap(self, content, latency, p_tok, o_tok, cached, key) -> LLMResponse:
        try:
            parsed, ok = json.loads(content), True
        except (json.JSONDecodeError, TypeError):
            parsed, ok = None, False
            self.stats["invalid_json"] += 1
        return LLMResponse(content, parsed, ok, latency, p_tok, o_tok, cached, key)
