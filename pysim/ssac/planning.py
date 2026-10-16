"""Plan phase: the planner interface and the rule-based baseline (C0).

A planner receives a `PlanningContext` for each detection and returns a list
of actions. It never sees injected faults — only what the Analyze phase
reported and the state of its own past interventions. Every returned action
goes through the symbolic validator before it is executed.
"""

from __future__ import annotations

import hashlib
import math
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Protocol

from .actions import Action, Maintenance, Reroute
from .topology import SENTINELS

if TYPE_CHECKING:
    from .engine import Detection
    from .intervention import InterventionState
    from .model import BusinessProcessModel
    from .topology import Twin


@dataclass
class PlanningContext:
    t_min: float
    detection: "Detection"
    model: "BusinessProcessModel"
    twins: dict[str, list["Twin"]]
    interventions: "InterventionState"


class Planner(Protocol):
    name: str

    def plan(self, ctx: PlanningContext) -> list[Action]: ...


class NoOpPlanner:
    """Detect, do nothing — what the 2020 system actually does."""
    name = "noop"

    def plan(self, ctx: PlanningContext) -> list[Action]:
        return []


def respond(station: str, ctx: PlanningContext, claimed: set[str], repair_min: float) -> list[Action]:
    """The shared rule for acting on one station judged faulty: reroute to a
    free twin if there is one, then repair. The reroute lifts when the repair
    completes."""
    state = ctx.interventions
    actions: list[Action] = []
    for twin in ctx.twins.get(station, []):
        t = twin.twin
        busy = (
            t in state.reroutes
            or t in claimed
            or state.inbound_share(t) > 0
            or state.under_maintenance(t, ctx.t_min)
        )
        if not busy:
            actions.append(Reroute(station, t, 1.0))
            claimed.add(t)
            break
    actions.append(Maintenance(station, repair_min))
    return actions


def _eligible(station: str, ctx: PlanningContext, last_acted: dict[str, float], cooldown: float) -> bool:
    state = ctx.interventions
    return not (
        station in SENTINELS
        or ctx.t_min - last_acted.get(station, float("-inf")) < cooldown
        or state.under_maintenance(station, ctx.t_min)
        or station in state.reroutes
    )


@dataclass
class RuleBasedPlanner:
    """C0-naive — act on every station named in an alarm.

    Included to show what happens when the 2020 Analyze layer is wired
    straight into an actuator: detector noise is amplified into repairs. It is
    NOT the baseline the LLM planner has to beat; that is
    `CalibratedRulePlanner`.
    """
    repair_min: float = 60.0
    cooldown_min: float = 240.0   # same as every other planner (120 until design v2)
    react_to: frozenset[str] = frozenset({"STATION_FAILURE", "STATION_DEGRADED"})
    name: str = "rules_naive"
    _last_acted: dict[str, float] = field(default_factory=dict)

    def plan(self, ctx: PlanningContext) -> list[Action]:
        if ctx.detection.type.value not in self.react_to:
            return []
        actions: list[Action] = []
        claimed: set[str] = set()
        for station in ctx.detection.stations:
            if _eligible(station, ctx, self._last_acted, self.cooldown_min):
                actions += respond(station, ctx, claimed, self.repair_min)
                self._last_acted[station] = ctx.t_min
        return actions


def poisson_threshold(mean: float, alpha: float) -> int:
    """Smallest k with P(X >= k) <= alpha for X ~ Poisson(mean)."""
    if mean <= 0:
        return 1
    term = math.exp(-mean)   # P(X = 0)
    cdf = term
    k = 0
    while 1.0 - cdf > alpha:
        k += 1
        term *= mean / k
        cdf += term
        if k > 10_000:
            break
    return k + 1


@dataclass
class CalibratedRulePlanner:
    """C0 — the classical baseline the LLM planner must beat.

    Each station has a background alarm rate learned from a fault-free trace
    (`ssac.calibration.alarm_rates`, on a DIFFERENT trace from the one under
    test). A station is judged faulty when its alarm count over the last
    `window_min` minutes is improbable under that rate: count >= the Poisson
    upper quantile at level `alpha`, and at least `min_count`. Then the same
    rule as the naive planner applies (reroute to a free twin, repair).

    This is a standard rate-based anomaly test. It uses exactly one piece of
    operational knowledge — per-station alarm base rates — and nothing else.
    """
    baseline_per_min: dict[str, float]
    window_min: float = 120.0
    alpha: float = 1e-3
    min_count: int = 3
    floor_per_min: float = 1.0 / 600.0   # stations never seen alarming: 1 per 10 h
    repair_min: float = 60.0
    cooldown_min: float = 240.0
    react_to: frozenset[str] = frozenset({"STATION_FAILURE", "STATION_DEGRADED"})
    name: str = "rules_cal"
    _history: dict[str, deque] = field(default_factory=dict)
    _last_acted: dict[str, float] = field(default_factory=dict)
    _thresholds: dict[str, int] = field(default_factory=dict)

    def threshold(self, station: str) -> int:
        if station not in self._thresholds:
            rate = max(self.baseline_per_min.get(station, 0.0), self.floor_per_min)
            k = poisson_threshold(rate * self.window_min, self.alpha)
            self._thresholds[station] = max(k, self.min_count)
        return self._thresholds[station]

    def plan(self, ctx: PlanningContext) -> list[Action]:
        if ctx.detection.type.value not in self.react_to:
            return []
        actions: list[Action] = []
        claimed: set[str] = set()
        for station in ctx.detection.stations:
            if station in SENTINELS:
                continue
            hist = self._history.setdefault(station, deque())
            hist.append(ctx.t_min)
            while hist and hist[0] < ctx.t_min - self.window_min:
                hist.popleft()
            if len(hist) < self.threshold(station):
                continue
            if _eligible(station, ctx, self._last_acted, self.cooldown_min):
                actions += respond(station, ctx, claimed, self.repair_min)
                self._last_acted[station] = ctx.t_min
                hist.clear()
        return actions


@dataclass
class AdaptiveRulePlanner:
    """C0-adaptive — change detection against each station's own recent past.

    Static base rates fail because alarm noise is not stationary across traces.
    This variant learns each station's rate causally from the trace under test:
    alarms in the short window [t - window_min, t] are compared with the rate
    observed in the preceding `history_min` minutes. A station is judged faulty
    when the short-window count is improbable under that recent rate (Poisson
    tail at `alpha`). No data from the future or from other traces is used.

    Nothing is decided during the first `warmup_min` minutes of the run.
    """
    window_min: float = 120.0
    history_min: float = 1440.0
    warmup_min: float = 480.0
    alpha: float = 1e-3
    min_count: int = 3
    prior_alarms: float = 1.0          # pseudo-count spread over the history
    repair_min: float = 60.0
    cooldown_min: float = 240.0
    react_to: frozenset[str] = frozenset({"STATION_FAILURE", "STATION_DEGRADED"})
    name: str = "rules_adapt"
    _alarms: dict[str, deque] = field(default_factory=dict)
    _last_acted: dict[str, float] = field(default_factory=dict)
    _t0: float | None = None

    _snoozed: dict[str, float] = field(default_factory=dict)

    def snooze(self, station: str, until_min: float) -> None:
        """Do not propose `station` again before `until_min` (used by the
        hybrid planner after the LLM vetoes it)."""
        self._snoozed[station] = until_min

    def candidates(self, ctx: PlanningContext) -> list[str]:
        """Stations judged anomalous by the change test and eligible for
        action. Updates the alarm history; does not decide what to do."""
        if self._t0 is None:
            self._t0 = ctx.t_min
        if ctx.detection.type.value not in self.react_to:
            return []

        t = ctx.t_min
        out: list[str] = []
        for station in ctx.detection.stations:
            if station in SENTINELS:
                continue
            hist = self._alarms.setdefault(station, deque())
            hist.append(t)
            horizon = t - self.window_min - self.history_min
            while hist and hist[0] < horizon:
                hist.popleft()

            if t - self._t0 < self.warmup_min:
                continue

            short = sum(1 for x in hist if x >= t - self.window_min)
            long_ = len(hist) - short
            span = min(self.history_min, max(t - self.window_min - self._t0, 1.0))
            rate = (long_ + self.prior_alarms) / span
            threshold = max(poisson_threshold(rate * self.window_min, self.alpha), self.min_count)

            if (short >= threshold and station not in out
                    and t >= self._snoozed.get(station, float("-inf"))
                    and self.accept(station, ctx)
                    and _eligible(station, ctx, self._last_acted, self.cooldown_min)):
                out.append(station)
        return out

    def accept(self, station: str, ctx: PlanningContext) -> bool:
        """Extra filter on candidates; subclasses override."""
        return True

    def plan(self, ctx: PlanningContext) -> list[Action]:
        actions: list[Action] = []
        claimed: set[str] = set()
        for station in self.candidates(ctx):
            actions += respond(station, ctx, claimed, self.repair_min)
            self._last_acted[station] = ctx.t_min
        return actions


@dataclass
class ContextAdaptiveRulePlanner(AdaptiveRulePlanner):
    """Control for the hybrid planner — not a proposed method.

    The adaptive rule plus the one contextual veto that is easy to write as a
    rule: never act on a station that is receiving load the controller itself
    rerouted onto it. If the hybrid LLM planner does no better than this, its
    contribution cannot be attributed to the LLM.
    """
    name: str = "rules_adapt_ctx"

    def accept(self, station: str, ctx: PlanningContext) -> bool:
        return ctx.interventions.inbound_share(station) == 0


@dataclass
class TwinOnlyRulePlanner:
    """Control for the LLM planner — not a proposed method.

    Acts on every flagged station that has a free twin (reroute + repair) and
    ignores stations without one. This is the structural heuristic the C1 LLM
    planner was observed to follow. If an LLM planner does no better than
    this, its gain cannot be attributed to triage or reasoning.
    """
    repair_min: float = 60.0
    cooldown_min: float = 240.0
    react_to: frozenset[str] = frozenset({"STATION_FAILURE", "STATION_DEGRADED"})
    name: str = "rules_twin"
    _last_acted: dict[str, float] = field(default_factory=dict)

    def plan(self, ctx: PlanningContext) -> list[Action]:
        if ctx.detection.type.value not in self.react_to:
            return []
        actions: list[Action] = []
        claimed: set[str] = set()
        for station in ctx.detection.stations:
            if not ctx.twins.get(station) or not _eligible(station, ctx, self._last_acted, self.cooldown_min):
                continue
            acts = respond(station, ctx, claimed, self.repair_min)
            if len(acts) == 2:          # a free twin was found
                actions += acts
                self._last_acted[station] = ctx.t_min
        return actions


@dataclass
class BurstVetoRulePlanner(AdaptiveRulePlanner):
    """Control for the hybrid planner — not a proposed method.

    The adaptive change test, with the hybrid's most frequently stated veto
    written as a rule: reject a candidate when the alarm names at least
    `max_alarm_stations` stations, or when at least `line_stations` distinct
    stations have alarmed in the last `line_window_min` minutes. A rejected
    station is not proposed again for `veto_snooze_min`, as in the hybrid.
    `load_veto` adds the rule of `ContextAdaptiveRulePlanner`.
    """
    max_alarm_stations: int | None = None
    line_window_min: float = 120.0
    line_stations: int | None = None
    load_veto: bool = False
    veto_snooze_min: float = 120.0
    name: str = "rules_burst"
    _recent: deque = field(default_factory=deque)     # (t, station) of every alarm

    def _vetoed(self, ctx: PlanningContext) -> bool:
        stations = [s for s in ctx.detection.stations if s not in SENTINELS]
        t = ctx.t_min
        for s in stations:
            self._recent.append((t, s))
        while self._recent and self._recent[0][0] < t - self.line_window_min:
            self._recent.popleft()
        if self.max_alarm_stations is not None and len(stations) >= self.max_alarm_stations:
            return True
        if self.line_stations is not None and len({s for _, s in self._recent}) >= self.line_stations:
            return True
        return False

    def accept(self, station: str, ctx: PlanningContext) -> bool:
        return not self.load_veto or ctx.interventions.inbound_share(station) == 0

    def plan(self, ctx: PlanningContext) -> list[Action]:
        vetoed = self._vetoed(ctx) if ctx.detection.type.value in self.react_to else False
        actions: list[Action] = []
        claimed: set[str] = set()
        for station in self.candidates(ctx):
            if vetoed:
                self.snooze(station, ctx.t_min + self.veto_snooze_min)
                continue
            actions += respond(station, ctx, claimed, self.repair_min)
            self._last_acted[station] = ctx.t_min
        return actions


@dataclass
class RandomVetoRulePlanner(AdaptiveRulePlanner):
    """Control for the hybrid planner — not a proposed method.

    The adaptive change test with each candidate vetoed at random with
    probability `veto_rate` (deterministic in station, time and seed), and the
    hybrid's 120-min suspension after a veto.
    """
    veto_rate: float = 0.65
    seed: int = 0
    veto_snooze_min: float = 120.0
    name: str = "rules_randveto"

    def plan(self, ctx: PlanningContext) -> list[Action]:
        actions: list[Action] = []
        claimed: set[str] = set()
        for station in self.candidates(ctx):
            h = hashlib.sha256(f"{self.seed}|{station}|{ctx.t_min:.3f}".encode()).digest()
            if int.from_bytes(h[:8], "big") / 2**64 < self.veto_rate:
                self.snooze(station, ctx.t_min + self.veto_snooze_min)
                continue
            actions += respond(station, ctx, claimed, self.repair_min)
            self._last_acted[station] = ctx.t_min
        return actions
