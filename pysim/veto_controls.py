#!/usr/bin/env python3
"""Rule controls for the hybrid's veto (results/dev_log.md, 2026-10-16), design
v2, per-station detector. No language model is called.

  (a) burst veto: the adaptive test, rejecting candidates of alarms that name
      >= m stations, or when >= m distinct stations alarmed in the last W min;
      with and without the load veto; 120-min suspension after a veto. The
      configuration is chosen on the development trace;
  (b) random veto at the hybrid's per-candidate veto rate (0.70 on the
      held-out traces), 120-min suspension, 5 seeds.

Evaluated on the held-out and the validation traces. Writes
results/veto_controls/rows.csv and results/veto_controls/summary.md.
"""

from __future__ import annotations

import csv
import json
import os
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.intervention import Fault
from ssac.metrics import outcome
from ssac.onsets import HORIZON_MIN, HORIZONS_MIN, onsets
from ssac.planning import AdaptiveRulePlanner, BurstVetoRulePlanner, ContextAdaptiveRulePlanner, RandomVetoRulePlanner

HERE = Path(__file__).resolve().parent
R = HERE.parent / "DataSets I4.0"
M = R / "bosch_pl_tm_model.pg"
P = json.loads((HERE / "results" / "detector_choice.json").read_text())
OUT = HERE / "results" / "veto_controls"
DEV = ["test_cases_0-100m.td"]
HELD_OUT = ["test_cases_100m-200m.td", "test_cases_200m-300m.td", "test_cases_500m-600m.td"]
NEW = [f"test_cases_{n}.td" for n in ("300m-400m", "400m-500m", "600m-700m", "700m-800m", "800m-900m")]
STATIONS = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]
VETO_RATE = 0.70

GRID = {}
for lv in (False, True):
    for m in (2, 3, 4, 6):
        GRID[f"burst{'_ctx' if lv else ''}|size>={m}"] = dict(max_alarm_stations=m, load_veto=lv)
    for w in (30.0, 120.0):
        for m in (3, 5, 8):
            GRID[f"burst{'_ctx' if lv else ''}|line{w:.0f}>={m}"] = dict(line_window_min=w, line_stations=m, load_veto=lv)


def make(name: str):
    if name == "noop":
        return None
    if name == "rules_adapt":
        return AdaptiveRulePlanner()
    if name == "rules_adapt_ctx":
        return ContextAdaptiveRulePlanner()
    if name.startswith("randveto|"):
        return RandomVetoRulePlanner(veto_rate=VETO_RATE, seed=int(name.split("|")[1]))
    return BurstVetoRulePlanner(name=name, **GRID[name])


_W: dict = {}


def _init():
    _W["data"], _W["ref"] = {}, {}


def _trace(t):
    if t not in _W["data"]:
        d = SimulationData.load(R / t)
        m, _ = BusinessProcessModel.load(M)
        e = SimulationEngine(m, d)
        e.run()
        _W["data"][t], _W["ref"][t] = d, dict(e.lifetimes)
    return _W["data"][t], _W["ref"][t]


def run(task):
    trace, station, shape, k, onset, planner = task
    d, ref = _trace(trace)
    m, _ = BusinessProcessModel.load(M)
    faults = [Fault(station, 3.0, onset, shape=shape)] if station else []
    e = SimulationEngine(m, d, faults=faults, planner=make(planner), detectors=("processing",), processing_params=P)
    e.run(until_min=onset + HORIZON_MIN if station else None)
    o = outcome(planner, e, ref, faults, horizons_min=HORIZONS_MIN)
    span_h = (d.events[-1].start_time - d.events[0].start_time) / 60
    return {"trace": trace, "station": station, "shape": shape, "onset_idx": k, "planner": planner,
            "excess_h24_min": round(o.excess_h[HORIZON_MIN], 3) if station else "",
            "false_cost_per_h": "" if station else round(o.excess_delay_min / span_h, 2),
            "maintenances_false": (o.maintenances_false_h or {}).get(HORIZON_MIN, 0) if station else o.maintenances_false,
            "maintenances_on_fault": (o.maintenances_on_fault_h or {}).get(HORIZON_MIN, 0) if station else 0}


def tasks(traces, planners):
    out = []
    for t in traces:
        d = SimulationData.load(R / t)
        t0, t1 = d.events[0].start_time, d.events[-1].start_time
        for p in planners:
            out.append((t, "", "", "", 0.0, p))
            for s in STATIONS:
                for sh in SHAPES:
                    for k, o in enumerate(onsets(t, s, sh, t0, t1)):
                        out.append((t, s, sh, k, o, p))
    return out


def recovery(rows, planner, traces):
    ks = [r for r in rows if r["planner"] == "noop" and r["station"] and r["trace"] in traces]
    idx = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): r for r in rows}
    den = sum(float(r["excess_h24_min"]) for r in ks)
    num = sum(float(idx[(r["trace"], r["station"], r["shape"], r["onset_idx"], planner)]["excess_h24_min"]) for r in ks)
    return 1 - num / den


def boot(rows, planner, traces, n=4000):
    idx = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): float(r["excess_h24_min"])
           for r in rows if r["station"]}
    keys = sorted({k[:4] for k in idx if k[0] in traces})
    st = {t: [k for k in keys if k[0] == t] for t in traces}
    rng = random.Random(0)
    out = []
    for _ in range(n):
        s = [rng.choice(st[t]) for t in traces for _ in st[t]]
        out.append(1 - sum(idx[k + (planner,)] for k in s) / sum(idx[k + ("noop",)] for k in s))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n) - 1]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    workers = max(1, (os.cpu_count() or 2) - 3)
    with ProcessPoolExecutor(workers, initializer=_init) as ex:
        dev = list(ex.map(run, tasks(DEV, ["noop", "rules_adapt", "rules_adapt_ctx", *GRID]), chunksize=4))
    dev_rec = {p: recovery(dev, p, DEV) for p in ["rules_adapt", "rules_adapt_ctx", *GRID]}
    best = {lv: max((p for p in GRID if p.startswith(lv + "|")), key=lambda p: dev_rec[p]) for lv in ("burst", "burst_ctx")}
    chosen = [best["burst"], best["burst_ctx"]] + [f"randveto|{s}" for s in range(5)]
    with ProcessPoolExecutor(workers, initializer=_init) as ex:
        ev = list(ex.map(run, tasks(HELD_OUT + NEW, ["noop", "rules_adapt", "rules_adapt_ctx", *chosen]), chunksize=4))
    rows = dev + ev
    with (OUT / "rows.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    out = ["# Controles del veto (solo reglas, detector por estación, diseño v2)\n",
           "## Selección en la traza de desarrollo (recuperación a 24 h)\n", "| Configuración | recuperación |", "|---|---|"]
    out += [f"| {p} | {v:+.3f} |" for p, v in sorted(dev_rec.items(), key=lambda x: -x[1])]
    out += [f"\nElegidas: {best['burst']} y {best['burst_ctx']}.\n",
            "## Evaluación\n", "| Planificador | reservadas [IC 95 %] | validación [IC 95 %] | reparaciones falsas / escenario (reservadas) |",
            "|---|---|---|---|"]
    for p in ["rules_adapt", "rules_adapt_ctx", *chosen]:
        a, b = recovery(ev, p, HELD_OUT), recovery(ev, p, NEW)
        la, ha = boot(ev, p, HELD_OUT)
        lb, hb = boot(ev, p, NEW)
        fr = [float(r["maintenances_false"]) for r in ev if r["planner"] == p and r["station"] and r["trace"] in HELD_OUT]
        out.append(f"| {p} | {a:+.3f} [{la:+.3f}, {ha:+.3f}] | {b:+.3f} [{lb:+.3f}, {hb:+.3f}] | {sum(fr) / len(fr):.1f} |")
    rv = [(recovery(ev, f"randveto|{s}", HELD_OUT), recovery(ev, f"randveto|{s}", NEW)) for s in range(5)]
    out.append(f"\nVeto aleatorio (tasa {VETO_RATE}), media de 5 semillas: reservadas {sum(x for x, _ in rv) / 5:+.3f} "
               f"(rango {min(x for x, _ in rv):+.3f} a {max(x for x, _ in rv):+.3f}); validación {sum(y for _, y in rv) / 5:+.3f} "
               f"(rango {min(y for _, y in rv):+.3f} a {max(y for _, y in rv):+.3f}).")
    (OUT / "summary.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
