#!/usr/bin/env python3
"""Burst-veto controls, second part (results/dev_log.md, 2026-10-18), design v2,
per-station detector. No language model is called.

  1. every configuration of the burst-veto grid of veto_controls.py on the
     held-out and validation traces: distribution, and the configuration best
     on the held-out traces as an upper bound no honest protocol could select;
  2. the chosen burst veto with load veto, overridden for candidates whose
     alarms over 24 h are at least R times their fault-free base rate (the
     statistic the LLM planners retrieve); R chosen on the development trace.

Writes results/veto_controls2/rows.csv and summary.md.
"""

from __future__ import annotations

import csv
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from extra_analyses import compare, keys, load
from robustness_analyses import cluster_boot
from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import Fault
from ssac.metrics import outcome
from ssac.onsets import HORIZON_MIN, HORIZONS_MIN
from ssac.planning import BurstVetoRulePlanner, SustainedBurstVetoRulePlanner
from veto_controls import DEV, GRID, HELD_OUT, M, NEW, P, R, boot, recovery, tasks

HERE = Path(__file__).resolve().parent
OUT = HERE / "results" / "veto_controls2"
PREV = HERE / "results" / "veto_controls" / "rows.csv"
CALIB = {"test_cases_0-100m.td": "test_cases_100m-200m.td",
         "test_cases_100m-200m.td": "test_cases_0-100m.td",
         "test_cases_200m-300m.td": "test_cases_500m-600m.td",
         "test_cases_500m-600m.td": "test_cases_200m-300m.td",
         **{t: "test_cases_0-100m.td" for t in NEW}}
RATIOS = [1.5, 2.0, 3.0, 5.0, 10.0]
CHOSEN = {"burst|line120>=8", "burst_ctx|size>=3"}

_W: dict = {}


def _init():
    _W["data"], _W["ref"], _W["rates"] = {}, {}, {}


def _trace(t):
    if t not in _W["data"]:
        d = SimulationData.load(R / t)
        m, _ = BusinessProcessModel.load(M)
        e = SimulationEngine(m, d)
        e.run()
        _W["data"][t], _W["ref"][t] = d, dict(e.lifetimes)
    return _W["data"][t], _W["ref"][t]


def _rates(t):
    if t not in _W["rates"]:
        _W["rates"][t] = alarm_rates(M, SimulationData.load(R / CALIB[t]), ("processing",), processing_params=P)
    return _W["rates"][t]


def make(name, trace):
    if name == "noop":
        return None
    if name.startswith("sustained|"):
        return SustainedBurstVetoRulePlanner(name=name, max_alarm_stations=3, load_veto=True,
                                             baseline_per_min=_rates(trace), override_ratio=float(name.split("|")[1]))
    return BurstVetoRulePlanner(name=name, **GRID[name])


def run(task):
    trace, station, shape, k, onset, planner = task
    d, ref = _trace(trace)
    m, _ = BusinessProcessModel.load(M)
    faults = [Fault(station, 3.0, onset, shape=shape)] if station else []
    e = SimulationEngine(m, d, faults=faults, planner=make(planner, trace), detectors=("processing",),
                         processing_params=P)
    e.run(until_min=onset + HORIZON_MIN if station else None)
    o = outcome(planner, e, ref, faults, horizons_min=HORIZONS_MIN)
    span_h = (d.events[-1].start_time - d.events[0].start_time) / 60
    return {"trace": trace, "station": station, "shape": shape, "onset_idx": str(k), "planner": planner,
            "excess_h24_min": round(o.excess_h[HORIZON_MIN], 3) if station else "",
            "false_cost_per_h": "" if station else round(o.excess_delay_min / span_h, 2),
            "maintenances_false": (o.maintenances_false_h or {}).get(HORIZON_MIN, 0) if station else o.maintenances_false,
            "maintenances_on_fault": (o.maintenances_on_fault_h or {}).get(HORIZON_MIN, 0) if station else 0}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    workers = max(1, (os.cpu_count() or 2) - 3)
    prev = list(csv.DictReader(PREV.open()))
    others = [g for g in GRID if g not in CHOSEN]
    sustained = [f"sustained|{r:g}" for r in RATIOS]
    with ProcessPoolExecutor(workers, initializer=_init) as ex:
        dev = list(ex.map(run, [t for t in tasks(DEV, sustained)], chunksize=4))
    dev_all = [r for r in prev if r["trace"] in DEV] + dev
    dev_rec = {p: recovery(dev_all, p, DEV) for p in sustained}
    best_s = max(sustained, key=lambda p: dev_rec[p])
    with ProcessPoolExecutor(workers, initializer=_init) as ex:
        ev = list(ex.map(run, tasks(HELD_OUT + NEW, others + [best_s]), chunksize=4))
    rows = dev + ev
    with (OUT / "rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    allrows = prev + rows
    out = ["# Controles del veto, segunda parte (solo reglas, detector por estación, diseño v2)\n",
           "## 1. Todas las configuraciones del control de ráfagas\n",
           "| Configuración | desarrollo | reservadas | validación |", "|---|---|---|---|"]
    rec = {}
    for g in GRID:
        rec[g] = (recovery(allrows, g, DEV), recovery(allrows, g, HELD_OUT), recovery(allrows, g, NEW))
    for g, (a, b, c) in sorted(rec.items(), key=lambda x: -x[1][1]):
        mark = " (elegida)" if g in CHOSEN else ""
        out.append(f"| {g}{mark} | {a:+.3f} | {b:+.3f} | {c:+.3f} |")
    best_h = max(GRID, key=lambda g: rec[g][1])
    best_n = max(GRID, key=lambda g: rec[g][2])
    out.append(f"\nMejor en reservadas: {best_h}; mejor en validación: {best_n}.\n")

    # margins of the frontier hybrid
    out += ["## Margen del híbrido Fable\n",
            "| Frente a | conjunto | Δ | IC 95 % estratificado | IC 95 % por grupos traza × estación | mejor / peor |",
            "|---|---|---|---|---|---|"]
    targets = [("burst_ctx|size>=3", "elegida"), (best_h, "mejor en reservadas"), (best_s, "exceso sostenido (elegida)")]
    for setname, d in (("reservadas", "processing"), ("validación", "newtraces")):
        Rr = load(HERE / "results" / d)
        traces = HELD_OUT if setname == "reservadas" else NEW
        for r in allrows:
            if r["station"] and r["trace"] in traces:
                Rr[(r["trace"], r["station"], r["shape"], r["onset_idx"], "ctl:" + r["planner"])] = r
        ks = [k for k in keys(Rr) if k[0] in traces]
        for g, label in targets + ([(best_n, "mejor en validación")] if setname == "validación" else []):
            c = compare(Rr, "hybrid:fable-5.1", Rr, "ctl:" + g, ks)
            _, lo, hi, _ = cluster_boot(Rr, "hybrid:fable-5.1", "ctl:" + g, ks)
            out.append(f"| {g} ({label}) | {setname} | {c['delta']:+.3f} | [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}] | "
                       f"[{lo:+.3f}, {hi:+.3f}] | {c['better']} / {c['worse']} |")

    out += ["\n## 2. Control con exceso sostenido: selección en desarrollo\n", "| R | desarrollo |", "|---|---|"]
    out += [f"| {p.split('|')[1]} | {dev_rec[p]:+.3f} |" for p in sustained]
    a, b = recovery(allrows, best_s, HELD_OUT), recovery(allrows, best_s, NEW)
    la, ha = boot(allrows, best_s, HELD_OUT)
    lb, hb = boot(allrows, best_s, NEW)
    fr = [float(r["maintenances_false"]) for r in allrows if r["planner"] == best_s and r["station"] and r["trace"] in HELD_OUT]
    out.append(f"\nElegido: {best_s}. Reservadas {a:+.3f} [{la:+.3f}, {ha:+.3f}]; validación {b:+.3f} [{lb:+.3f}, {hb:+.3f}]; "
               f"reparaciones falsas por escenario (reservadas) {sum(fr) / len(fr):.1f}.")
    (OUT / "summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
