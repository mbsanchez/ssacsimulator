#!/usr/bin/env python3
"""Diagnostics of the Analyze layers, separate from the planners (design v2).
No language model is called. Writes results/processing/detector_diagnostics.md.

For the legacy detector, the per-station binomial detector of the paper and a
control with the same processing regime and windows but a fixed threshold
instead of the binomial test (median of the last N processing transitions above
1.3 times the station's median over the previous 24 h), on the 216 held-out
fault scenarios:
  * detection: whether, and how soon after the onset, an alarm names the faulty
    station within 24 h, by fault shape and by station;
  * false alarms: alarms per hour naming any station, and stations per alarm,
    in the fault-free runs;
  * the rule-based planners with each per-station detector (24-h recovery).
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import Fault
from ssac.metrics import outcome
from ssac.onsets import HORIZON_MIN, HORIZONS_MIN, onsets
from ssac.planning import AdaptiveRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner, NoOpPlanner

HERE = Path(__file__).resolve().parent
R = HERE.parent / "DataSets I4.0"
M = R / "bosch_pl_tm_model.pg"
P = json.loads((HERE / "results" / "detector_choice.json").read_text())
HELD_OUT = {"test_cases_100m-200m.td": "test_cases_0-100m.td",
            "test_cases_200m-300m.td": "test_cases_500m-600m.td",
            "test_cases_500m-600m.td": "test_cases_200m-300m.td"}
STATIONS = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]
DETECTORS = {"legacy": (("legacy",), None),
             "per-station (binomial)": (("processing",), P),
             "per-station (threshold control)": (("processing",), {**P, "test": "threshold"})}
PLANNERS = ["noop", "rules_cal", "rules_adapt", "rules_adapt_ctx"]

_W: dict = {}


def _init():
    _W["data"], _W["ref"], _W["rates"] = {}, {}, {}
    for t, c in HELD_OUT.items():
        d = SimulationData.load(R / t)
        m, _ = BusinessProcessModel.load(M)
        e = SimulationEngine(m, d)
        e.run()
        _W["data"][t], _W["ref"][t] = d, dict(e.lifetimes)


def _rates(trace, det):
    key = (trace, det)
    if key not in _W["rates"]:
        dets, params = DETECTORS[det]
        _W["rates"][key] = alarm_rates(M, SimulationData.load(R / HELD_OUT[trace]), dets, processing_params=params)
    return _W["rates"][key]


def run(task):
    kind, det, trace, station, shape, onset, planner = task
    dets, params = DETECTORS[det]
    d = _W["data"][trace]
    m, _ = BusinessProcessModel.load(M)
    faults = [Fault(station, 3.0, onset, shape=shape)] if station else []
    pl = {"noop": NoOpPlanner, "rules_cal": lambda: CalibratedRulePlanner(_rates(trace, det)),
          "rules_adapt": AdaptiveRulePlanner, "rules_adapt_ctx": ContextAdaptiveRulePlanner}[planner]()
    e = SimulationEngine(m, d, faults=faults, planner=pl if planner != "noop" else None, detectors=dets,
                         processing_params=params)
    e.run(until_min=onset + HORIZON_MIN if station else None)
    if kind == "freerun":
        span_h = (d.events[-1].start_time - d.events[0].start_time) / 60
        sizes = [len(x.stations) for x in e.detections if x.stations]
        return task, {"alarms_per_h": len(sizes) / span_h, "stations_per_alarm": sum(sizes) / max(len(sizes), 1)}
    hits = [x.sim_time_min - onset for x in e.detections if station in x.stations and onset <= x.sim_time_min]
    o = outcome(planner, e, _W["ref"][trace], faults, horizons_min=HORIZONS_MIN)
    return task, {"detected": bool(hits), "delay": min(hits) if hits else None, "e24": o.excess_h[HORIZON_MIN]}


def main():
    tasks = []
    for det in DETECTORS:
        for t in HELD_OUT:
            tasks.append(("freerun", det, t, "", "", 0.0, "noop"))
            d = SimulationData.load(R / t)
            for s in STATIONS:
                for sh in SHAPES:
                    for o in onsets(t, s, sh, d.events[0].start_time, d.events[-1].start_time):
                        for p in PLANNERS:
                            if det == "legacy" and p != "noop":
                                continue
                            tasks.append(("fault", det, t, s, sh, o, p))
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 3), initializer=_init) as ex:
        res = dict(ex.map(run, tasks, chunksize=8))

    def det_rows(det, pred):
        rs = [v for k, v in res.items() if k[0] == "fault" and k[1] == det and k[6] == "noop" and pred(k)]
        delays = sorted(v["delay"] for v in rs if v["delay"] is not None)
        med = f"{delays[len(delays) // 2] / 60:.1f}" if delays else "–"
        return f"{sum(v['detected'] for v in rs)}/{len(rs)}", med

    out = ["# Diagnóstico de las capas Analyze (trazas reservadas, diseño v2, sin planificador)\n",
           "Detectado: alguna alarma nombra a la estación averiada en las 24 h tras el inicio. Retraso: mediana, en horas, "
           "desde el inicio hasta esa primera alarma (escenarios detectados). Falsas alarmas: ejecuciones sin fallo de las "
           "tres trazas reservadas, traza completa.\n",
           "## Detección por forma de fallo\n",
           "| Detector | " + " | ".join(f"{s}: detectado / retraso (h)" for s in SHAPES) + " | todas |",
           "|---|" + "---|" * (len(SHAPES) + 1)]
    for det in DETECTORS:
        cells = [" / ".join(det_rows(det, lambda k, s=s: k[4] == s)) for s in SHAPES]
        out.append(f"| {det} | " + " | ".join(cells) + f" | {' / '.join(det_rows(det, lambda k: True))} |")
    out += ["\n## Detección por estación (todas las formas)\n",
            "| Detector | " + " | ".join(STATIONS) + " |", "|---|" + "---|" * len(STATIONS)]
    for det in DETECTORS:
        out.append(f"| {det} | " + " | ".join(det_rows(det, lambda k, s=s: k[3] == s)[0] for s in STATIONS) + " |")
    out += ["\n## Alarmas sin fallo\n", "| Detector | alarmas por hora (media de las trazas) | estaciones por alarma |",
            "|---|---|---|"]
    for det in DETECTORS:
        rs = [v for k, v in res.items() if k[0] == "freerun" and k[1] == det]
        out.append(f"| {det} | {sum(v['alarms_per_h'] for v in rs) / len(rs):.2f} | "
                   f"{sum(v['stations_per_alarm'] for v in rs) / len(rs):.1f} |")
    out += ["\n## Reglas con cada detector por estación (recuperación a 24 h, hiperparámetros por defecto)\n",
            "| Detector | " + " | ".join(PLANNERS[1:]) + " |", "|---|" + "---|" * (len(PLANNERS) - 1)]
    for det in list(DETECTORS)[1:]:
        cells = []
        for p in PLANNERS[1:]:
            ks = [k for k in res if k[0] == "fault" and k[1] == det and k[6] == p]
            num = sum(res[k]["e24"] for k in ks)
            den = sum(res[k[:6] + ("noop",)]["e24"] for k in ks)
            cells.append(f"{1 - num / den:+.3f}")
        out.append(f"| {det} | " + " | ".join(cells) + " |")
    path = HERE / "results" / "processing" / "detector_diagnostics.md"
    path.write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
