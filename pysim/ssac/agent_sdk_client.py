"""Client for Claude models through the Claude Agent SDK, with the same
interface and cache as `OllamaClient`.

Why the Agent SDK and not the Messages API: the SDK authenticates with the
local Claude Code login, so calls draw on the user's Claude plan instead of
separately billed API credits. It must therefore NOT run with
ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN in the environment — that would
switch billing to the API. The client refuses to start if they are set.

Each call is configured to be a single, tool-less completion so that the
Claude Code harness does not confound the comparison with the local model:
custom system prompt (the planner's), no built-in tools, no filesystem
settings or CLAUDE.md, NO MCP servers, and the planner's JSON schema enforced
as structured output.

The MCP part matters. `tools=[]` only removes built-in tools; when logged in
with a Claude account the CLI also loads the account's claude.ai connectors
(e.g. Atlassian, Google Drive), whose tool definitions were sent with every
call — ~19 000 extra input tokens, and tools the model could see while
deciding about a production line. `--strict-mcp-config` with no config loads
none. The harness version is part of the cache key, so responses obtained
without it are never reused.

Differences from the local model that the paper must state:
  * no temperature control (removed on current Claude models), so runs are
    not bit-reproducible; the response cache is what makes them replayable;
  * the model reasons internally before answering (always on for Fable);
    `effort` controls how much.

`total_cost_usd` reported by the SDK is the API-equivalent price of each
call. Under a plan it is informative, not charged; it is accumulated in
`stats["api_equivalent_usd"]`.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sqlite3
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from .llm import LLMError, LLMResponse


@dataclass
class AgentSDKClient:
    model: str = "claude-fable-5"
    effort: str | None = "low"
    max_turns: int = 3
    retries: int = 3
    retry_wait_s: float = 30.0
    cache_path: Path | None = None
    offline: bool = False          # replay only: raise instead of calling the model on a cache miss
    allow_api_key: bool = False
    harness: str = "strict-mcp-v1"   # part of the cache key
    stats: dict = field(default_factory=lambda: {
        "calls": 0, "cache_hits": 0, "seconds": 0.0, "invalid_json": 0, "retries": 0,
        "api_equivalent_usd": 0.0, "input_tokens": 0, "output_tokens": 0,
    })

    def __post_init__(self) -> None:
        if not self.allow_api_key and (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            raise LLMError(
                "ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN is set: the Agent SDK would bill the API instead of "
                "the Claude plan. Unset it, or pass allow_api_key=True deliberately."
            )
        self._workdir = Path(tempfile.mkdtemp(prefix="ssac-agent-"))   # empty cwd: nothing to pick up
        self._db = None
        if self.cache_path is not None:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._db = sqlite3.connect(self.cache_path, timeout=60)
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS responses ("
                " key TEXT PRIMARY KEY, model TEXT, request TEXT, response TEXT,"
                " latency_s REAL, prompt_tokens INTEGER, output_tokens INTEGER, created REAL)"
            )
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS agent_usage ("
                " key TEXT PRIMARY KEY, cost_usd REAL, usage TEXT, model_usage TEXT)"
            )
            self._db.commit()

    # ---- public ----------------------------------------------------------

    def chat(self, messages: list[dict], schema: dict | None = None) -> LLMResponse:
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        prompt = "\n\n".join(m["content"] for m in messages if m["role"] == "user")
        request = {"backend": "claude-agent-sdk", "harness": self.harness, "model": self.model,
                   "effort": self.effort, "system": system, "prompt": prompt, "schema": schema}
        key = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        self.stats["calls"] += 1

        if self._db is not None:
            row = self._db.execute(
                "SELECT response, latency_s, prompt_tokens, output_tokens FROM responses WHERE key = ?", (key,)
            ).fetchone()
            if row is not None:
                self.stats["cache_hits"] += 1
                return self._wrap(row[0], row[1], row[2], row[3], True, key)
        if getattr(self, "offline", False):
            raise LLMError(f"offline replay: request not in the cache (key {key[:12]})")

        wait = self.retry_wait_s
        for attempt in range(self.retries + 1):
            t0 = time.perf_counter()
            try:
                result = asyncio.run(self._query(system, prompt, schema))
                break
            except LLMError:
                raise
            except Exception as exc:  # SDK/CLI errors: retry, then surface
                if attempt == self.retries:
                    raise LLMError(f"Agent SDK call failed after {self.retries + 1} attempts "
                                   f"(model {self.model}): {exc!r}") from exc
                self.stats["retries"] += 1
                time.sleep(wait)
                wait *= 2
        latency = time.perf_counter() - t0
        self.stats["seconds"] += latency

        if result.is_error:
            raise LLMError(f"Agent SDK returned an error (model {self.model}): "
                           f"{result.subtype} {result.errors} {result.terminal_reason}")

        if result.structured_output is not None:
            content = json.dumps(result.structured_output)
        else:
            content = result.result or ""
        usage = result.usage or {}
        p_tok = (usage.get("input_tokens") or 0) + (usage.get("cache_read_input_tokens") or 0) \
            + (usage.get("cache_creation_input_tokens") or 0)
        o_tok = usage.get("output_tokens") or 0
        cost = result.total_cost_usd or 0.0
        self.stats["api_equivalent_usd"] += cost
        self.stats["input_tokens"] += p_tok
        self.stats["output_tokens"] += o_tok

        if self._db is not None:
            self._db.execute(
                "INSERT OR REPLACE INTO responses VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (key, self.model, json.dumps(request), content, latency, p_tok, o_tok, time.time()),
            )
            self._db.execute(
                "INSERT OR REPLACE INTO agent_usage VALUES (?, ?, ?, ?)",
                (key, cost, json.dumps(usage), json.dumps(result.model_usage, default=str)),
            )
            self._db.commit()
        return self._wrap(content, latency, p_tok, o_tok, False, key)

    # ---- internals ---------------------------------------------------------

    async def _query(self, system: str, prompt: str, schema: dict | None):
        from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=system,
            tools=[],
            setting_sources=[],
            max_turns=self.max_turns,
            effort=self.effort,
            cwd=str(self._workdir),
            output_format={"type": "json_schema", "schema": schema} if schema else None,
            mcp_servers={},
            extra_args={"strict-mcp-config": None},
        )
        final = None
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                final = message
        if final is None:
            raise LLMError("Agent SDK produced no result message")
        return final

    def _wrap(self, content, latency, p_tok, o_tok, cached, key) -> LLMResponse:
        try:
            parsed, ok = json.loads(content), True
        except (json.JSONDecodeError, TypeError):
            parsed, ok = None, False
            self.stats["invalid_json"] += 1
        return LLMResponse(content, parsed, ok, latency, p_tok, o_tok, cached, key)
