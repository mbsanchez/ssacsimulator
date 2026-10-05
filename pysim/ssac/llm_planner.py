"""LLM planners for the Plan phase.

C1 (`LLMPlanner`): the LLM sees the current alarm, which flagged stations can
be acted on, whether each has a free twin, and the controller's current
interventions. It has the same structural information as the rule-based
planners and no operational history. It decides, per station, whether to act
and how.

Division of labour, deliberately narrow:
  * the LLM triages (act or not) and picks the action TYPE;
  * code picks the twin (the same `respond` rule the baselines use), so the
    model has no free-text field in which to invent a station;
  * the JSON schema restricts `station` to the eligible stations, so the
    decoder cannot emit any other;
  * every resulting action still goes through the symbolic validator.

Every call is recorded in `calls` (prompt key, response, latency, cache hit,
what was done with it), which is what the paper's qualitative analysis and
any audit of a decision will read.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .actions import Action, Maintenance
from .llm import ChatModel
from .planning import PlanningContext, _eligible, respond
from .topology import SENTINELS

PROMPT_VERSION = "c1-v1"

SYSTEM_PROMPT = """You are the Plan phase of an autonomic controller for a manufacturing line (the Bosch production line: about 50 stations on 4 sub-lines).

How alarms work. The Analyze phase raises an alarm listing stations whose recent transition times exceeded 1.3 times their reference time within the same batch of events. In normal operation this detector also raises false alarms: a station named in an alarm may be perfectly healthy.

What you can do for each flagged station:
- leave it alone;
- "maintain": repair it for 60 minutes. While it is being repaired a slower backup handles its work. Repairing a degraded station fixes it. Repairing a healthy station fixes nothing and only slows production;
- "reroute_and_maintain": only for a station with a free twin. The twin takes all of the station's load during the repair (the twin slows down because of the extra load), and the station is repaired.

Objective: minimise total production delay. Acting on a healthy station wastes production. Ignoring a truly degraded station lets its delay accumulate for as long as it stays degraded.

Answer only with JSON matching the schema. List in "act" only the stations you decide to act on; omit the ones you leave alone ("act" may be empty). Keep "reason" under 25 words."""


def response_schema(eligible: list[str]) -> dict:
    return {
        "type": "object",
        "properties": {
            "act": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "station": {"type": "string", "enum": eligible},
                        "action": {"type": "string", "enum": ["maintain", "reroute_and_maintain"]},
                    },
                    "required": ["station", "action"],
                },
            },
            "reason": {"type": "string"},
        },
        "required": ["act", "reason"],
    }


@dataclass
class CallRecord:
    t_min: float
    trigger: str
    eligible: list[str]
    key: str
    cached: bool
    latency_s: float
    ok: bool
    acted_on: list[str]
    reason: str
    raw: str
    problems: list[str]


@dataclass
class LLMPlanner:
    client: ChatModel
    repair_min: float = 60.0
    cooldown_min: float = 240.0
    react_to: frozenset[str] = frozenset({"STATION_FAILURE", "STATION_DEGRADED"})
    name: str = "llm_c1"
    calls: list[CallRecord] = field(default_factory=list)
    _last_acted: dict[str, float] = field(default_factory=dict)

    # ---- prompt ---------------------------------------------------------

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def describe_state(self, ctx: PlanningContext, eligible: list[str]) -> list[str]:
        state = ctx.interventions
        lines = [f"Time: t = {ctx.t_min:.0f} min.", "", "Flagged stations you may act on:"]
        for s in eligible:
            free = [
                t.twin for t in ctx.twins.get(s, [])
                if t.twin not in state.reroutes
                and state.inbound_share(t.twin) == 0
                and not state.under_maintenance(t.twin, ctx.t_min)
            ]
            twin = f"free twin available ({free[0]})" if free else (
                "has a twin, but it is busy" if ctx.twins.get(s) else "no twin")
            lines.append(f"- {s}: {twin}")
        others = [s for s in ctx.detection.stations if s not in eligible and s not in SENTINELS]
        if others:
            lines.append(f"Also flagged but not actionable now (already handled or recently acted on): {', '.join(others)}")
        under = sorted(s for s in ctx.model.actors if state.under_maintenance(s, ctx.t_min))
        lines.append("")
        lines.append(f"Stations under repair now: {', '.join(under) if under else 'none'}.")
        rr = [f"{s} -> {t}" for s, (t, _) in state.reroutes.items()]
        lines.append(f"Active reroutes: {', '.join(rr) if rr else 'none'}.")
        return lines

    def context_block(self, ctx: PlanningContext, eligible: list[str]) -> list[str]:
        """Retrieved knowledge. None in C1; C2 overrides this."""
        return []

    def build_messages(self, ctx: PlanningContext, eligible: list[str]) -> list[dict]:
        lines = self.describe_state(ctx, eligible)
        extra = self.context_block(ctx, eligible)
        if extra:
            lines += [""] + extra
        return [
            {"role": "system", "content": self.system_prompt()},
            {"role": "user", "content": "\n".join(lines)},
        ]

    # ---- plan -----------------------------------------------------------

    def observe(self, ctx: PlanningContext) -> None:
        """Hook called on every detection, actionable or not. C2 uses it to
        record alarms in its memory."""

    def plan(self, ctx: PlanningContext) -> list[Action]:
        self.observe(ctx)
        if ctx.detection.type.value not in self.react_to:
            return []

        eligible = []
        for s in ctx.detection.stations:
            if s not in eligible and _eligible(s, ctx, self._last_acted, self.cooldown_min):
                eligible.append(s)
        if not eligible:
            return []

        resp = self.client.chat(self.build_messages(ctx, eligible), response_schema(eligible))
        problems: list[str] = []
        acted: list[str] = []
        actions: list[Action] = []
        reason = ""

        if not resp.ok or not isinstance(resp.parsed, dict):
            problems.append("invalid JSON")
        else:
            reason = str(resp.parsed.get("reason", ""))[:500]
            claimed: set[str] = set()
            for item in resp.parsed.get("act", []) or []:
                if not isinstance(item, dict):
                    problems.append(f"malformed item {item!r}")
                    continue
                station, kind = item.get("station"), item.get("action")
                if station not in eligible:
                    problems.append(f"station {station!r} not eligible")
                    continue
                if station in acted:
                    problems.append(f"duplicate {station}")
                    continue
                if kind == "maintain":
                    actions.append(Maintenance(station, self.repair_min))
                elif kind == "reroute_and_maintain":
                    acts = respond(station, ctx, claimed, self.repair_min)
                    if len(acts) == 1:
                        problems.append(f"{station}: no free twin, reroute downgraded to maintain")
                    actions += acts
                else:
                    problems.append(f"{station}: unknown action {kind!r}")
                    continue
                acted.append(station)
                self._last_acted[station] = ctx.t_min

        self.calls.append(CallRecord(
            t_min=ctx.t_min, trigger=ctx.detection.type.value, eligible=eligible, key=resp.key,
            cached=resp.cached, latency_s=resp.latency_s, ok=resp.ok, acted_on=acted,
            reason=reason, raw=resp.content, problems=problems,
        ))
        return actions
