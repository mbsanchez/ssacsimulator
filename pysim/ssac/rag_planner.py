"""C2: the LLM planner augmented with retrieved operational knowledge — the K
of MAPE-K that the 2020 system never implemented.

Knowledge sources:
  * the controller's own operational log: every alarm it has seen and every
    intervention it has made, as timestamped text records;
  * per-station alarm base rates from a fault-free reference trace (the same
    single piece of knowledge `CalibratedRulePlanner` gets).

For each station the LLM may act on, the retriever assembles:
  1. alarm statistics: count in the last 2 h and 24 h, rate since the start of
     operation, and the base rate in fault-free operation;
  2. self-inflicted load: whether the controller is currently rerouting a
     twin's load ONTO this station (an alarm there may be its own doing);
  3. outcome of past repairs of the station: alarms in the 2 h before vs the
     2 h after each repair — if repairing it did not change its alarm rate,
     its alarms were probably noise;
  4. the k most recent log records that mention the station.

Retrieval is keyed (by station) and ordered by recency, not by embedding
similarity. On a structured log the station name is an exact key, and exact
filtering is strictly better than approximate semantic search. An embedding
retriever is a possible ablation, not the method. All numbers are computed by
code; the LLM never does arithmetic over the log.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field

from .actions import Maintenance, Reroute, Restore, describe
from .llm_planner import SYSTEM_PROMPT, LLMPlanner
from .planning import PlanningContext
from .topology import SENTINELS

C2_SYSTEM_SUFFIX = """

You also receive RETRIEVED KNOWLEDGE for each station: its alarm history compared with its normal (fault-free) alarm rate, whether you are currently pushing extra load onto it, what happened after you repaired it before, and recent log records. Use it:
- a station alarming far more often than its normal rate, steadily, is probably degraded;
- a station alarming at about its normal rate is probably healthy;
- a station receiving load you rerouted onto it will alarm because of you; repairing it does not help;
- if repairing a station before did not reduce its alarms, its alarms are probably noise."""


@dataclass
class OperationalMemory:
    """Timestamped alarm and intervention records, indexed by station."""
    alarm_times: dict[str, list[float]] = field(default_factory=dict)
    records: dict[str, list[tuple[float, str]]] = field(default_factory=dict)
    t_start: float | None = None
    _seen_log: int = 0

    def add_alarm(self, t: float, kind: str, stations: tuple[str, ...]) -> None:
        if self.t_start is None:
            self.t_start = t
        names = [s for s in stations if s not in SENTINELS]
        text = f"t={t:.0f}: alarm {kind} flagged {', '.join(names)}"
        for s in names:
            self.alarm_times.setdefault(s, []).append(t)
            self.records.setdefault(s, []).append((t, text))

    def sync_interventions(self, log) -> None:
        """Ingest interventions applied since the last call (incl. automatic
        restores when a repair completes)."""
        for entry in log[self._seen_log:]:
            a = entry.action
            stations = []
            if isinstance(a, Reroute):
                stations = [a.station, a.twin]
            elif isinstance(a, (Maintenance, Restore)):
                stations = [a.station]
            text = f"t={entry.t_min:.0f}: you applied {describe(a)}"
            for s in stations:
                self.records.setdefault(s, []).append((entry.t_min, text))
        self._seen_log = len(log)

    def count(self, station: str, t0: float, t1: float) -> int:
        ts = self.alarm_times.get(station, [])
        return bisect_right(ts, t1) - bisect_left(ts, t0)

    def recent(self, station: str, t: float, k: int) -> list[str]:
        return [text for when, text in self.records.get(station, []) if when <= t][-k:]


@dataclass
class RAGPlanner(LLMPlanner):
    baseline_per_min: dict[str, float] = field(default_factory=dict)
    k_records: int = 6
    name: str = "llm_c2"
    memory: OperationalMemory = field(default_factory=OperationalMemory)

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT + C2_SYSTEM_SUFFIX

    def observe(self, ctx: PlanningContext) -> None:
        self.memory.sync_interventions(ctx.interventions.log)
        self.memory.add_alarm(ctx.t_min, ctx.detection.type.value, ctx.detection.stations)

    def _repair_outcomes(self, station: str, ctx: PlanningContext) -> list[str]:
        out = []
        for start, end in ctx.interventions.repairs.get(station, []):
            if end + 120 > ctx.t_min:
                continue  # not enough time after the repair to judge
            before = self.memory.count(station, start - 120, start)
            after = self.memory.count(station, end, end + 120)
            out.append(f"repaired at t={start:.0f}: {before} alarms in the 2 h before, {after} in the 2 h after")
        return out

    def context_block(self, ctx: PlanningContext, eligible: list[str]) -> list[str]:
        t = ctx.t_min
        mem = self.memory
        elapsed_h = max((t - (mem.t_start or t)) / 60.0, 1e-9)
        lines = ["RETRIEVED KNOWLEDGE"]
        for s in eligible:
            base = self.baseline_per_min.get(s)
            base_txt = f"{base * 60:.2f}/h" if base is not None else "never alarmed in fault-free operation"
            total = mem.count(s, float("-inf"), t)
            lines.append(f"[{s}]")
            lines.append(
                f"- alarms: {mem.count(s, t - 120, t)} in the last 2 h, {mem.count(s, t - 1440, t)} in the last 24 h, "
                f"{total} since operation started ({total / elapsed_h:.2f}/h over {elapsed_h:.0f} h); "
                f"normal rate in fault-free operation: {base_txt}"
            )
            onto = [src for src, (twin, _) in ctx.interventions.reroutes.items() if twin == s]
            if onto:
                lines.append(f"- you are currently rerouting the load of {', '.join(onto)} ONTO {s}")
            outcomes = self._repair_outcomes(s, ctx)
            if outcomes:
                lines.append("- past repairs: " + "; ".join(outcomes))
            recent = mem.recent(s, t, self.k_records)
            if recent:
                lines.append("- recent log:")
                lines += [f"    {r}" for r in recent]
        return lines
