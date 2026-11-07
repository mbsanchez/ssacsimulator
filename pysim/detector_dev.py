#!/usr/bin/env python3
"""Choose the processing-time detector on the DEVELOPMENT trace only (design v2
amendment, results/dev_log.md). No language model is called.

For each detector configuration (window N, level alpha, refractory period),
runs no action and the rule planners with their default hyperparameters on the
development scenarios (8 stations x 3 shapes x 3 onsets, runs stopped 24 h
after the onset) and the fault-free development trace, and reports pooled
24-h recovery, detection within 24 h and the false-alarm cost. The selected
configuration maximises the recovery of the adaptive rule with load veto, the
strongest baseline of the paper.

    python detector_dev.py     # writes results/detector_dev.md
"""

from __future__ import annotations

import itertools
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import Fault
from ssac.metrics import outcome
from ssac.onsets import HORIZON_MIN, HORIZONS_MIN, onsets
from ssac.planning import (AdaptiveRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner, NoOpPlanner,
                           RuleBasedPlanner)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
DEV, CALIB = "test_cases_0-100m.td", "test_cases_100m-200m.td"
STATIONS = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]
PLANNERS = ["noop", "rules_naive", "rules_cal", "rules_adapt", "rules_adapt_ctx"]
GRID = {"window": [10, 20, 40], "alpha": [1e-2, 1e-3, 1e-4], "refractory_min": [6.0, 30.0, 60.0]}

_W: dict = {}


def _init():
    d = SimulationData.load(ROOT / DEV)
    m, _ = BusinessProcessModel.load(MODEL)
    e = SimulationEngine(m, d)
    e.run()
    _W.update(data=d, ref=dict(e.lifetimes), rates={})


def run(task):
    cfg, station, shape, onset, p = task
    params = dict(zip(GRID, cfg))
    if cfg not in _W["rates"]:
        _W["rates"][cfg] = alarm_rates(MODEL, SimulationData.load(ROOT / CALIB), ("processing",),
                                       processing_params=params)
    planner = {"noop": NoOpPlanner, "rules_naive": RuleBasedPlanner,
               "rules_cal": lambda: CalibratedRulePlanner(_W["rates"][cfg]), "rules_adapt": AdaptiveRulePlanner,
               "rules_adapt_ctx": ContextAdaptiveRulePlanner}[p]()
    faults = [Fault(station, 3.0, onset, shape=shape)] if station else []
    m, _ = BusinessProcessModel.load(MODEL)
    e = SimulationEngine(m, _W["data"], faults=faults, planner=planner, detectors=("processing",),
                         processing_params=params)
    e.run(until_min=onset + HORIZON_MIN if station else None)
    o = outcome(p, e, _W["ref"], faults, horizons_min=HORIZONS_MIN)
    if not station:
        span = (_W["data"].events[-1].start_time - _W["data"].events[0].start_time) / 60
        return task, {"fa_cost": o.excess_delay_min / span, "alarms": len(e.detections)}
    det = [x for x in e.detections if station in x.stations and onset <= x.sim_time_min < onset + HORIZON_MIN]
    return task, {"h24": o.excess_h[HORIZON_MIN], "acts": o.maintenances_on_fault_h[HORIZON_MIN] > 0,
                  "false": o.maintenances_false_h[HORIZON_MIN], "detected": bool(det)}


def main() -> int:
    d = SimulationData.load(ROOT / DEV)
    t0, t1 = d.events[0].start_time, d.events[-1].start_time
    scen = [(s, sh, o) for s in STATIONS for sh in SHAPES for o in onsets(DEV, s, sh, t0, t1)]
    cfgs = list(itertools.product(*GRID.values()))
    tasks = [(c, s, sh, o, p) for c in cfgs for s, sh, o in scen for p in PLANNERS]
    tasks += [(c, "", "", 0.0, p) for c in cfgs for p in PLANNERS if p != "noop"]
    print(f"{len(tasks)} runs", flush=True)
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 2), initializer=_init) as pool:
        res = dict(pool.map(run, tasks, chunksize=16))

    def pooled(c, p):
        ks = [(c, s, sh, o) for s, sh, o in scen]
        return 1 - sum(res[k + (p,)]["h24"] for k in ks) / sum(res[k + ("noop",)]["h24"] for k in ks)
    rows = []
    for c in cfgs:
        det = sum(res[(c, s, sh, o, "noop")]["detected"] for s, sh, o in scen)
        rows.append((c, det, {p: pooled(c, p) for p in PLANNERS[1:]},
                     {p: res[(c, "", "", 0.0, p)]["fa_cost"] for p in PLANNERS[1:]},
                     res[(c, "", "", 0.0, "rules_naive")]["alarms"]))
    best = max(rows, key=lambda r: r[2]["rules_adapt_ctx"])
    out = ["# Detector por estación: selección en la traza de desarrollo\n",
           f"Traza {DEV}; {len(scen)} escenarios (8 estaciones × 3 formas × 3 inicios), horizonte 24 h; tasas base de la "
           f"regla calibrada aprendidas en {CALIB} sin fallo. Detectado: alguna alarma sobre la estación averiada en las "
           "24 h tras el inicio, sin planificador. Criterio de selección: recuperación de la regla adaptativa con veto por carga.\n",
           "| ventana | α | refractario (min) | detectado | alarmas sin fallo | " + " | ".join(PLANNERS[1:])
           + " | coste falsas alarmas (adapt+veto) |", "|---|---|---|---|---|" + "---|" * (len(PLANNERS) - 1) + "---|"]
    for c, det, rec, fa, al in rows:
        mark = " **(elegida)**" if c == best[0] else ""
        out.append(f"| {c[0]} | {c[1]:g} | {c[2]:g}{mark} | {det}/{len(scen)} | {al} | "
                   + " | ".join(f"{rec[p]:+.3f}" for p in PLANNERS[1:]) + f" | {fa['rules_adapt_ctx']:.0f} |")
    out.append(f"\nElegida: {dict(zip(GRID, best[0]))}")
    (HERE / "results" / "detector_dev.md").write_text("\n".join(out) + "\n")
    (HERE / "results" / "detector_choice.json").write_text(json.dumps(dict(zip(GRID, best[0])), indent=2))
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
