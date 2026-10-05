"""LLM planners for the Plan phase.

C1 (`LLMPlanner`): the LLM sees the current alarm, which flagged stations can
be acted on, whether each has a free twin, and the controller's current
interventions. It has the same structural information as the rule-based
planners and no operational history.

Output contract (prompt v2): for EVERY actionable station the model must
first give a verdict, then an action. The schema makes each station a
required key, so none can be skipped, and restricts both fields to enums.
Code then enforces coherence: an action on a station the model itself judged
anything other than "degraded" is dropped and recorded as a problem. This
came from prompt v1, where the model repaired stations it had just described
as healthy.

Division of labour, deliberately narrow:
  * the LLM gives a verdict and picks the action TYPE;
  * code picks the twin (the same `respond` rule the baselines use);
  * the schema restricts station names to the eligible ones;
  * every resulting action still goes through the symbolic validator.

Every call is recorded in `calls` for audit and qualitative analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .actions import Action, Maintenance
from .llm import ChatModel
from .planning import PlanningContext, _eligible, respond
from .topology import SENTINELS

PROMPT_VERSION = "v2"

VERDICTS = ["degraded", "normal", "self_inflicted", "insufficient_evidence"]
ACTIONS = ["none", "maintain", "reroute_and_maintain"]

SYSTEM_PROMPT = """You are the Plan phase of an autonomic controller for a manufacturing line (the Bosch production line: about 50 stations on 4 sub-lines).

How alarms work. The Analyze phase raises an alarm listing stations whose recent transition times exceeded 1.3 times their reference time within the same batch of events. In normal operation this detector also raises false alarms: a station named in an alarm may be perfectly healthy.

What you can do for each flagged station:
- "none": leave it alone;
- "maintain": repair it for 60 minutes. While it is being repaired a slower backup handles its work. Repairing a degraded station fixes it. Repairing a healthy station fixes nothing and only slows production;
- "reroute_and_maintain": only for a station with a free twin. The twin takes all of the station's load during the repair (the twin slows down because of the extra load), and the station is repaired.

Objective: minimise total production delay. Acting on a healthy station wastes production. Ignoring a truly degraded station lets its delay accumulate for as long as it stays degraded.

For EVERY station listed, first give a verdict, then an action:
- "degraded": the evidence shows the station itself is not working properly;
- "normal": the station is probably healthy and the alarm is a false alarm;
- "self_inflicted": the station is alarming because of load you rerouted onto it;
- "insufficient_evidence": you cannot tell.
Only a "degraded" station may receive an action other than "none".

Answer only with JSON matching the schema. Keep "reason" under 30 words."""


def response_schema(eligible: list[str]) -> dict:
    per_station = {
        "type": "object",
        "properties": {
            "verdict": {"type": "string", "enum": VERDICTS},
            "action": {"type": "string", "enum": ACTIONS},
        },
        "required": ["verdict", "action"],
    }
    return {
        "type": "object",
        "properties": {
            "stations": {
                "type": "object",
                "properties": {s: per_station for s in eligible},
                "required": list(eligible),
            },
            "reason": {"type": "string"},
        },
        "required": ["stations", "reason"],
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
    verdicts: dict[str, str]
    acted_on: list[str]
    reason: str
    raw: str
    problems: list[str]


def twin_status(station: str, ctx: PlanningContext) -> str:
    state = ctx.interventions
    twins = ctx.twins.get(station, [])
    if not twins:
        return "no twin"
    free = [
        t.twin for t in twins
        if t.twin not in state.reroutes
        and state.inbound_share(t.twin) == 0
        and not state.under_maintenance(t.twin, ctx.t_min)
    ]
    return f"free twin available ({free[0]})" if free else "has a twin, but it is busy"


@dataclass
class LLMPlanner:
    client: ChatModel
    repair_min: float = 60.0
    cooldown_min: float = 240.0
    react_to: frozenset[str] = frozenset({"STATION_FAILURE", "STATION_DEGRADED"})
    name: str = "llm_c1"
    prompt_version: str = PROMPT_VERSION
    calls: list[CallRecord] = field(default_factory=list)
    _last_acted: dict[str, float] = field(default_factory=dict)

    # ---- prompt ---------------------------------------------------------

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def describe_state(self, ctx: PlanningContext, eligible: list[str]) -> list[str]:
        state = ctx.interventions
        lines = [f"Time: t = {ctx.t_min:.0f} min.", "", "Flagged stations you must give a verdict on:"]
        for s in eligible:
            lines.append(f"- {s}: {twin_status(s, ctx)}")
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
        """Hook called on every detection, actionable or not."""

    def plan(self, ctx: PlanningContext) -> list[Action]:
        self.observe(ctx)
        if ctx.detection.type.value not in self.react_to:
            return []

        eligible: list[str] = []
        for s in ctx.detection.stations:
            if s not in eligible and _eligible(s, ctx, self._last_acted, self.cooldown_min):
                eligible.append(s)
        if not eligible:
            return []

        resp = self.client.chat(self.build_messages(ctx, eligible), response_schema(eligible))
        problems: list[str] = []
        verdicts: dict[str, str] = {}
        acted: list[str] = []
        actions: list[Action] = []
        reason = ""

        if not resp.ok or not isinstance(resp.parsed, dict) or not isinstance(resp.parsed.get("stations"), dict):
            problems.append("invalid JSON")
        else:
            reason = str(resp.parsed.get("reason", ""))[:500]
            claimed: set[str] = set()
            per = resp.parsed["stations"]
            for station, item in per.items():
                if station not in eligible:
                    problems.append(f"station {station!r} not eligible")
                    continue
                if not isinstance(item, dict):
                    problems.append(f"{station}: malformed entry")
                    continue
                verdict, kind = item.get("verdict"), item.get("action")
                verdicts[station] = str(verdict)
                if verdict not in VERDICTS or kind not in ACTIONS:
                    problems.append(f"{station}: unknown verdict/action {verdict!r}/{kind!r}")
                    continue
                if kind == "none":
                    continue
                if verdict != "degraded":
                    problems.append(f"{station}: action {kind} dropped, verdict was {verdict}")
                    continue
                if kind == "maintain":
                    actions.append(Maintenance(station, self.repair_min))
                else:
                    acts = respond(station, ctx, claimed, self.repair_min)
                    if len(acts) == 1:
                        problems.append(f"{station}: no free twin, reroute downgraded to maintain")
                    actions += acts
                acted.append(station)
                self._last_acted[station] = ctx.t_min
            missing = [s for s in eligible if s not in per]
            if missing:
                problems.append(f"no verdict for {', '.join(missing)}")

        self.calls.append(CallRecord(
            t_min=ctx.t_min, trigger=ctx.detection.type.value, eligible=eligible, key=resp.key,
            cached=resp.cached, latency_s=resp.latency_s, ok=resp.ok, verdicts=verdicts,
            acted_on=acted, reason=reason, raw=resp.content, problems=problems,
        ))
        return actions
