#!/usr/bin/env python3
"""Analyses of stored results registered on 2026-10-16 (results/dev_log.md).
No language model is called: part A replays the hybrids from the response
store (a cache miss is an error). Writes results/robustness_analyses.md.

  A  probability of a veto as a function of the number of stations named in
     the alarm, for the faulty station and for the others (held-out traces,
     per-station detector);
  B  bootstrap by clusters of trace x station (24 clusters on the held-out
     traces, 40 on the validation traces);
  C  distribution over scenarios of the delay difference against doing nothing;
  D  recovery with a fixed cost added for every repair.
"""

from __future__ import annotations

import json
import os
import random
import statistics
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from extra_analyses import e, keys, load, pooled
from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.hybrid_planner import HybridPlanner
from ssac.intervention import Fault
from ssac.onsets import HORIZON_MIN, onsets

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
ROOT = HERE.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
P = json.loads((RES / "detector_choice.json").read_text())
HELD_OUT = {"test_cases_100m-200m.td": "test_cases_0-100m.td",
            "test_cases_200m-300m.td": "test_cases_500m-600m.td",
            "test_cases_500m-600m.td": "test_cases_200m-300m.td"}
STATIONS = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]


class SizedHybrid(HybridPlanner):
    """The hybrid, recording the number of stations of the alarm behind each call."""
    def plan(self, ctx):
        n = len(self.calls)
        out = super().plan(ctx)
        if len(self.calls) > n:
            self.sizes.append(len([s for s in ctx.detection.stations]))
        return out


def _replay(task):
    backend, trace, station, shape, onset = task
    if backend == "fable":
        from ssac.agent_sdk_client import AgentSDKClient
        client = AgentSDKClient(model="claude-fable-5-1", effort="low", cache_path=HERE / "cache" / "llm_cache.sqlite",
                                offline=True)
    else:
        from ssac.llm import OllamaClient
        client = OllamaClient(model="qwen2.5:7b", cache_path=HERE / "cache" / "llm_cache.sqlite", offline=True)
    rates = alarm_rates(MODEL, SimulationData.load(ROOT / HELD_OUT[trace]), ("processing",), processing_params=P)
    pl = SizedHybrid(client, baseline_per_min=rates, analyze="processing", prompt_version="v3+h1")
    pl.sizes = []
    m, _ = BusinessProcessModel.load(MODEL)
    faults = [Fault(station, 3.0, onset, shape=shape)] if station else []
    eng = SimulationEngine(m, SimulationData.load(ROOT / trace), faults=faults, planner=pl, detectors=("processing",),
                           processing_params=P)
    eng.run(until_min=onset + HORIZON_MIN if station else None)
    out = []
    for c, size in zip(pl.calls, pl.sizes):
        if station and c.t_min < onset:
            continue
        for s in c.eligible:
            out.append((size, s == station, s not in c.acted_on))
    return task, out


def part_a(out):
    tasks = []
    for t in HELD_OUT:
        d = SimulationData.load(ROOT / t)
        for s in STATIONS:
            for sh in SHAPES:
                for o in onsets(t, s, sh, d.events[0].start_time, d.events[-1].start_time):
                    for b in ("fable", "qwen"):
                        tasks.append((b, t, s, sh, o))
    with ProcessPoolExecutor(max(1, (os.cpu_count() or 2) - 3)) as ex:
        res = list(ex.map(_replay, tasks, chunksize=2))
    out += ["## A. Probabilidad de veto según el tamaño de la alarma (trazas reservadas, desde el inicio del fallo)\n",
            "Cada candidato propuesto por el test en una llamada posterior al inicio del fallo; veto = no se actúa sobre él. "
            "Tamaño = estaciones nombradas en la alarma que dispara la llamada.\n",
            "| Modelo | estaciones en la alarma | candidatos: averiada | vetada | candidatos: sanas | vetadas |",
            "|---|---|---|---|---|---|"]
    for b in ("fable", "qwen"):
        agg = defaultdict(lambda: [0, 0, 0, 0])
        for (bb, *_), recs in res:
            if bb != b:
                continue
            for size, faulty, vetoed in recs:
                g = agg[min(size, 5)]
                if faulty:
                    g[0] += 1; g[1] += vetoed
                else:
                    g[2] += 1; g[3] += vetoed
        for size in sorted(agg):
            a = agg[size]
            lab = f"{size}" if size < 5 else "≥5"
            out.append(f"| {b} | {lab} | {a[0]} | {a[1] / a[0]:.0%} |" if a[0] else f"| {b} | {lab} | 0 | – |")
            out[-1] += f" {a[2]} | {a[3] / a[2]:.0%} |" if a[2] else " 0 | – |"


def cluster_boot(R, a, b, ks, n=10_000):
    cl = defaultdict(list)
    for k in ks:
        cl[(k[0], k[1])].append(k)
    groups = list(cl.values())
    rng = random.Random(0)

    def d(s):
        return (sum(e(R, k, b) for k in s) - sum(e(R, k, a) for k in s)) / sum(e(R, k, "noop") for k in s)
    vals = sorted(d([k for g in (rng.choice(groups) for _ in groups) for k in g]) for _ in range(n))
    return d(ks), vals[int(0.025 * n)], vals[int(0.975 * n) - 1], len(groups)


def main() -> int:
    out = ["# Análisis de robustez (resultados almacenados, sin llamadas al modelo)\n"]
    part_a(out)

    H, N = load(RES / "processing"), load(RES / "newtraces")
    out += ["\n## B. Bootstrap por conglomerados traza × estación\n",
            "| Comparación (A − B) | conjunto | Δ | IC 95 % | conglomerados |", "|---|---|---|---|---|"]
    for R, name, pairs in [(H, "reservadas", [("hybrid:fable-5.1", "rules_adapt_ctx"), ("hybrid:fable-5.1", "hybrid"),
                                              ("hybrid:fable-5.1", "llm_c2:fable-5.1")]),
                           (N, "validación", [("hybrid:fable-5.1", "rules_cal_rt"), ("hybrid:fable-5.1", "rules_adapt_ctx")])]:
        for a, b in pairs:
            dlt, lo, hi, g = cluster_boot(R, a, b, keys(R))
            out.append(f"| {a} − {b} | {name} | {dlt:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {g} |")

    out += ["\n## C. Distribución por escenario del retraso añadido frente a no hacer nada (min-pieza; negativo = mejor)\n",
            "| Planificador | conjunto | p5 | p25 | mediana | p75 | p95 | peor | escenarios peor que no hacer nada |",
            "|---|---|---|---|---|---|---|---|---|"]
    for R, name, ps in [(H, "reservadas", ["rules_adapt_ctx", "hybrid", "llm_c2:fable-5.1", "hybrid:fable-5.1"]),
                        (N, "validación", ["rules_cal_rt", "rules_adapt_ctx", "hybrid", "hybrid:fable-5.1"])]:
        for p in ps:
            dd = sorted(e(R, k, p) - e(R, k, "noop") for k in keys(R))
            q = lambda f: dd[min(int(f * len(dd)), len(dd) - 1)]
            out.append(f"| {p} | {name} | {q(.05):,.0f} | {q(.25):,.0f} | {statistics.median(dd):,.0f} | {q(.75):,.0f} | "
                       f"{q(.95):,.0f} | {dd[-1]:,.0f} | {sum(x > 0 for x in dd)} |")

    out += ["\n## D. Recuperación con un coste fijo por reparación (min-pieza añadidos por cada reparación en 24 h)\n",
            "| Planificador | conjunto | 0 | 60 | 240 | 960 |", "|---|---|---|---|---|---|"]
    for R, name, ps in [(H, "reservadas", ["rules_adapt_ctx", "hybrid", "llm_c2:fable-5.1", "hybrid:fable-5.1"]),
                        (N, "validación", ["rules_cal_rt", "rules_adapt_ctx", "hybrid", "hybrid:fable-5.1"])]:
        ks = keys(R)
        den = sum(e(R, k, "noop") for k in ks)
        for p in ps:
            reps = [float(R[k + (p,)]["maintenances_on_fault"]) + float(R[k + (p,)]["maintenances_false"]) for k in ks]
            cells = [f"{1 - (sum(e(R, k, p) for k in ks) + c * sum(reps)) / den:+.3f}" for c in (0, 60, 240, 960)]
            out.append(f"| {p} | {name} | " + " | ".join(cells) + " |")
    (RES / "robustness_analyses.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
