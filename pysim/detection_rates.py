#!/usr/bin/env python3
"""How often each Analyze layer flags the faulty station within 24 h of the
onset, with no planner, on the held-out scenarios of design v2; and how often it
flags the same station in the same window without the fault.
No language model is called. Writes results/detection_rates.md."""
import json
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.intervention import Fault
from ssac.onsets import HORIZON_MIN, onsets

HERE = Path(__file__).resolve().parent
R = HERE.parent / "DataSets I4.0"
M = R / "bosch_pl_tm_model.pg"
P = json.loads((HERE / "results" / "detector_choice.json").read_text())
HO = ["test_cases_100m-200m.td", "test_cases_200m-300m.td", "test_cases_500m-600m.td"]
ST = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SH = ["step", "intermittent", "drift"]


def run(t):
    tr, s, sh, o, det, fault = t
    d = SimulationData.load(R / tr)
    m, _ = BusinessProcessModel.load(M)
    e = SimulationEngine(m, d, faults=[Fault(s, 3.0, o, shape=sh)] if fault else [], detectors=(det,),
                         processing_params=P if det == "processing" else None)
    e.run(until_min=o + HORIZON_MIN)
    hits = [x for x in e.detections if s in x.stations and o <= x.sim_time_min < o + HORIZON_MIN]
    others = [len(x.stations) for x in hits]
    return t, (len(hits), sum(others) / len(others) if others else 0.0)


def main():
    tasks = []
    for tr in HO:
        d = SimulationData.load(R / tr)
        for s in ST:
            for sh in SH:
                for o in onsets(tr, s, sh, d.events[0].start_time, d.events[-1].start_time):
                    for det in ("legacy", "processing"):
                        for fault in (True, False):
                            tasks.append((tr, s, sh, o, det, fault))
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 3)) as ex:
        res = dict(ex.map(run, tasks, chunksize=8))
    out = ["# Detección del fallo en 24 h, sin planificador (trazas reservadas, diseño v2)\n",
           "Alarmas que nombran a la estación averiada en las 24 h tras el inicio, con el fallo y en la misma ventana sin él. "
           "Estaciones por alarma: tamaño medio de esas alarmas.\n",
           "| Detector | escenarios con alguna alarma (con / sin fallo) | alarmas por escenario, media (con / sin fallo) "
           "| razón | estaciones por alarma (con fallo) |", "|---|---|---|---|---|"]
    for det in ("legacy", "processing"):
        w = [v for k, v in res.items() if k[4] == det and k[5]]
        wo = [v for k, v in res.items() if k[4] == det and not k[5]]
        mw, mwo = sum(c for c, _ in w) / len(w), sum(c for c, _ in wo) / len(wo)
        size = [z for c, z in w if c]
        out.append(f"| {det} | {sum(c > 0 for c, _ in w)}/216 / {sum(c > 0 for c, _ in wo)}/216 | {mw:.1f} / {mwo:.1f} | "
                   f"{mw / mwo if mwo else float('inf'):.1f} | {sum(size) / len(size):.1f} |")
    (HERE / "results" / "detection_rates.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))


if __name__ == "__main__":
    main()
