#!/usr/bin/env python3
"""Rule-only probe of the fault-onset design (no language model is called).

The held-out evaluation injects every fault 600 min after the first event and
lets a repair clear any fault that begins before the repair ends. An audit of the design showed that this credits routine repairs that happen to fall at the fixed
onset. This probe reruns the rule planners with
  * the original design (onset 600 min, "begun_before_end"),
  * the corrected repair rule only ("active_at_start"),
  * the corrected rule and K onsets per scenario drawn uniformly, with a fixed
    seed, between 24 h after the first event and 24 h before the last,
and reports pooled recovery on the held-out traces.

    python onset_probe.py            # writes results/onset_probe.md
"""

from __future__ import annotations

import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import EffectModel, Fault
from ssac.metrics import outcome
from ssac.planning import (AdaptiveRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner, NoOpPlanner,
                           RuleBasedPlanner, TwinOnlyRulePlanner)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
HELD_OUT = {"test_cases_100m-200m.td": "test_cases_0-100m.td",
            "test_cases_200m-300m.td": "test_cases_500m-600m.td",
            "test_cases_500m-600m.td": "test_cases_200m-300m.td"}
STATIONS = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]
PLANNERS = ["noop", "rules_naive", "rules_cal", "rules_adapt", "rules_adapt_ctx", "rules_twin"]
K_ONSETS = 3
SEED = 0
MARGIN_MIN = 24 * 60

_W: dict = {}


def _init():
    _W["data"], _W["ref"], _W["rates"] = {}, {}, {}
    for t, c in HELD_OUT.items():
        d = SimulationData.load(ROOT / t)
        m, _ = BusinessProcessModel.load(MODEL)
        e = SimulationEngine(m, d)
        e.run()
        _W["data"][t], _W["ref"][t] = d, dict(e.lifetimes)
        _W["rates"][t] = alarm_rates(MODEL, SimulationData.load(ROOT / c), ("legacy",))


def _planner(name, trace):
    return {"noop": NoOpPlanner, "rules_naive": lambda: RuleBasedPlanner(cooldown_min=240.0),
            "rules_cal": lambda: CalibratedRulePlanner(_W["rates"][trace]), "rules_adapt": AdaptiveRulePlanner,
            "rules_adapt_ctx": ContextAdaptiveRulePlanner, "rules_twin": TwinOnlyRulePlanner}[name]()


def run(task):
    design, trace, station, shape, onset, planner = task
    d = _W["data"][trace]
    m, _ = BusinessProcessModel.load(MODEL)
    clears = "begun_before_end" if design == "original" else "active_at_start"
    faults = [Fault(station, 3.0, onset, shape=shape)]
    e = SimulationEngine(m, d, faults=faults, planner=_planner(planner, trace),
                         effects=EffectModel(repair_clears=clears))
    e.run()
    return task, outcome(planner, e, _W["ref"][trace], faults).excess_delay_min


def main() -> int:
    rng = random.Random(SEED)
    tasks = []
    spans = {}
    for t in HELD_OUT:
        d = SimulationData.load(ROOT / t)
        t0, t1 = d.events[0].start_time, d.events[-1].start_time
        spans[t] = (t0, t1)
        for s in STATIONS:
            for sh in SHAPES:
                onsets = [rng.uniform(t0 + MARGIN_MIN, t1 - MARGIN_MIN) for _ in range(K_ONSETS)]
                for p in PLANNERS:
                    tasks.append(("original", t, s, sh, t0 + 600.0, p))
                    tasks.append(("clears_fixed", t, s, sh, t0 + 600.0, p))
                    for o in onsets:
                        tasks.append(("random_onset", t, s, sh, round(o), p))
    tasks = list(dict.fromkeys(tasks))
    print(f"{len(tasks)} runs", flush=True)
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 1), initializer=_init) as pool:
        res = dict(pool.map(run, tasks, chunksize=8))

    def pooled(design, p, shapes=SHAPES):
        ks = [k for k in res if k[0] == design and k[5] == p and k[3] in shapes]
        num = sum(res[k] for k in ks)
        den = sum(res[k[:5] + ("noop",)] for k in ks)
        return 1 - num / den
    out = ["# Diseño del inicio del fallo: comprobación solo con reglas\n",
           f"Trazas reservadas. «original»: inicio a 600 min, una reparación elimina todo fallo iniciado antes de que termine. "
           f"«clears_fixed»: inicio a 600 min, solo se eliminan los fallos activos al empezar la reparación. "
           f"«random_onset»: regla corregida y {K_ONSETS} inicios por escenario, uniformes entre 24 h tras el primer evento y "
           f"24 h antes del último (semilla {SEED}); {len(STATIONS) * len(SHAPES) * len(HELD_OUT) * K_ONSETS} escenarios.\n",
           "| Planificador | diseño | todas | escalón | intermitente | deriva |", "|---|---|---|---|---|---|"]
    for p in PLANNERS[1:]:
        for design in ("original", "clears_fixed", "random_onset"):
            out.append(f"| {p} | {design} | {pooled(design, p):+.3f} | "
                       + " | ".join(f"{pooled(design, p, [s]):+.3f}" for s in SHAPES) + " |")
    (HERE / "results" / "onset_probe.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
