"""Hybrid planner: classical change detection triages, the LLM vetoes.

The held-out evaluation showed the LLM planners (C1, C2) are worse at triage
than the adaptive rule-based test that uses the same knowledge. The hybrid
gives each part the job it did best:

  * the adaptive change test (`AdaptiveRulePlanner.candidates`) decides WHICH
    stations look anomalous — the LLM is never asked about a station the
    statistics do not flag, so it cannot add false alarms of its own;
  * the LLM receives the same retrieved knowledge as C2 and acts as a
    contextual VETO: it confirms, or rejects with a reason the test cannot
    see (load the controller rerouted onto the station, a past repair that
    did not help, ...), and chooses repair vs. reroute + repair.

By construction the hybrid can only act on a subset of what the adaptive rule
acts on (plus the choice of action). It cannot improve detection latency.
A vetoed station is not proposed again for `veto_snooze_min`.

Control: `ContextAdaptiveRulePlanner` implements the main contextual veto as
a plain rule. The hybrid's contribution is what it does beyond that control.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .actions import Action
from .planning import AdaptiveRulePlanner, PlanningContext
from .rag_planner import RAGPlanner

HYBRID_SUFFIX = """

In this mode a statistical change detector has already screened the alarms. The stations listed were flagged because their recent alarm count is improbably high compared with their own recent history. The detector is usually right, but it cannot see context: load you rerouted onto a station, a previous repair that did not reduce its alarms, a burst of alarms shared by many stations at once. Give "degraded" unless the retrieved knowledge gives a concrete reason to doubt the detector; then give the verdict that reason supports."""


@dataclass
class HybridPlanner(RAGPlanner):
    detector: AdaptiveRulePlanner = field(default_factory=AdaptiveRulePlanner)
    veto_snooze_min: float = 120.0
    name: str = "hybrid"
    prompt_version: str = "v2+h1"

    def system_prompt(self) -> str:
        return super().system_prompt() + HYBRID_SUFFIX

    def plan(self, ctx: PlanningContext) -> list[Action]:
        self.observe(ctx)
        candidates = self.detector.candidates(ctx)
        if not candidates:
            return []
        actions = self.decide(ctx, candidates)
        acted = set(self.calls[-1].acted_on)
        for station in candidates:
            if station in acted:
                self.detector._last_acted[station] = ctx.t_min
            else:
                self.detector.snooze(station, ctx.t_min + self.veto_snooze_min)
        return actions
