#!/usr/bin/env python3
"""Every number of the paper's held-out tables, from the stored results.
No language model is called. Writes results/paper_tables.md.

Design v2, held-out traces, 24-h horizon after the fault onset. One table per
Analyze layer (legacy detector, per-station detector), plus the comparison of
evaluation designs (v1 against v2)."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from stats import read_all

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
SHAPES = ["step", "intermittent", "drift"]
PLANNERS = ["rules_cal", "rules_adapt", "rules_adapt_ctx", "rules_twin", "llm_c1", "llm_c2", "hybrid",
            "llm_c1:fable-5.1", "llm_c2:fable-5.1", "hybrid:fable-5.1"]


def load(d: Path):
    rows = read_all(d / "llm_sweep_rows.csv")
    fault = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): r for r in rows if r["station"]}
    free = {(r["trace"], r["planner"]): r for r in rows if not r["station"]}
    return fault, free


def table(d: Path, title: str) -> list[str]:
    fault, free = load(d)
    keys = sorted({k[:4] for k in fault})
    traces = sorted({k[0] for k in keys})
    ex = lambda k, p: float(fault[k + (p,)]["excess_h24_min"])

    def pooled(p, ks):
        return 1 - sum(ex(k, p) for k in ks) / sum(ex(k, "noop") for k in ks)

    def ci(p):
        strata = {t: [k for k in keys if k[0] == t] for t in traces}
        rng = random.Random(0)
        b = sorted(pooled(p, [rng.choice(strata[t]) for t in traces for _ in strata[t]]) for _ in range(10_000))
        return b[249], b[9749]

    out = [f"## {title}\n", f"{len(keys)} escenarios con fallo, {len(traces)} trazas reservadas.\n",
           "| Planificador | recuperación 24 h [IC 95 %] | escalón | intermitente | deriva | actúa (24 h) | mediana latencia (min) "
           "| reparaciones falsas / escenario (24 h) | coste falsas alarmas (min-pieza/h) |",
           "|---|---|---|---|---|---|---|---|---|"]
    for p in PLANNERS:
        if not all(k + (p,) in fault for k in keys):
            continue
        lo, hi = ci(p)
        sh = [pooled(p, [k for k in keys if k[2] == s]) for s in SHAPES]
        acts = sum(int(fault[k + (p,)]["maintenances_on_fault"]) > 0 for k in keys)
        lats = sorted(float(fault[k + (p,)]["first_action_latency_min"]) for k in keys
                      if fault[k + (p,)]["first_action_latency_min"] not in ("", "None"))
        lat = f"{lats[len(lats) // 2]:,.0f}" if lats else "–"
        fp = sum(int(fault[k + (p,)]["maintenances_false"]) for k in keys) / len(keys)
        fa = sum(float(free[(t, p)]["excess_delay_min"]) / float(free[(t, p)]["span_h"]) for t in traces) / len(traces)
        out.append(f"| {p} | {pooled(p, keys):+.3f} [{lo:+.3f}, {hi:+.3f}] | "
                   + " | ".join(f"{v:+.3f}" for v in sh)
                   + f" | {acts}/{len(keys)} | {lat} | {fp:.1f} | {fa:.0f} |")
    return out


def v1_row() -> dict[str, float]:
    rows = list(csv.DictReader((RES / "v1" / "llm_sweep_rows.csv").open()))
    f = {(r["trace"], r["station"], r["shape"], r["planner"]): float(r["excess_delay_min"]) for r in rows if r["station"]}
    keys = sorted({k[:3] for k in f})
    return {p: 1 - sum(f[k + (p,)] for k in keys) / sum(f[k + ("noop",)] for k in keys)
            for p in PLANNERS if all(k + (p,) in f for k in keys)}


def designs() -> list[str]:
    v1 = v1_row()
    out = ["## Diseño de evaluación: v1 frente a v2\n",
           "v1: fallo a 600 min del primer evento, una reparación elimina también fallos iniciados durante ella, "
           "recuperación sobre la traza completa, 72 escenarios. v2: 3 inicios aleatorios, solo se eliminan fallos activos "
           "al empezar la reparación, recuperación a 24 h, 216 escenarios.\n",
           "| Planificador | v1 (detector heredado) | v2, detector heredado | v2, detector por estación |", "|---|---|---|---|"]
    rec = {}
    for d in (RES, RES / "processing"):
        fault, _ = load(d)
        keys = sorted({k[:4] for k in fault})
        rec[d] = {p: 1 - sum(float(fault[k + (p,)]["excess_h24_min"]) for k in keys)
                  / sum(float(fault[k + ("noop",)]["excess_h24_min"]) for k in keys)
                  for p in PLANNERS if all(k + (p,) in fault for k in keys)}
    fmt = lambda x: f"{x:+.2f}" if x is not None else "–"
    for p in PLANNERS:
        out.append(f"| {p} | {fmt(v1.get(p))} | {fmt(rec[RES].get(p))} | {fmt(rec[RES / 'processing'].get(p))} |")
    return out


def sensitivity() -> list[str]:
    """Rule-based planners, per-station detector, held-out traces only, from results/processing/sweep.csv."""
    rows = [r for r in csv.DictReader((RES / "processing" / "sweep.csv").open())
            if r["station"] and r["trace"] != "test_cases_0-100m.td"]

    def key(r):
        v = r["varied"] if r["varied"].startswith("factor") else ""
        return ("oat" if v else "central", v, r["trace"], r["station"], r["shape"], r["onset_idx"])
    noop = {key(r): float(r["excess_h24_min"]) for r in rows if r["planner"] == "noop"}

    def pooled(sel):
        return 1 - sum(float(r["excess_h24_min"]) for r in sel) / sum(noop[key(r)] for r in sel)
    out = ["## Sensibilidad (reglas, detector por estación, solo trazas reservadas)\n",
           "| | rules_naive | rules_cal | rules_adapt | rules_twin |", "|---|---|---|---|---|"]
    cen = [r for r in rows if r["part"] == "central"]
    for name, shapes in (("todas", SHAPES), ("escalón", ["step"]), ("intermitente", ["intermittent"]), ("deriva", ["drift"])):
        out.append(f"| central, {name} | " + " | ".join(
            f"{pooled([r for r in cen if r['planner'] == p and r['shape'] in shapes]):+.2f}"
            for p in ("rules_naive", "rules_cal", "rules_adapt", "rules_twin")) + " |")
    for v in sorted({r["varied"] for r in rows if r["part"] == "oat"}):
        out.append(f"| {v} | – | " + " | ".join(
            f"{pooled([r for r in rows if r['part'] == 'oat' and r['varied'] == v and r['planner'] == p]):+.2f}"
            for p in ("rules_cal", "rules_adapt", "rules_twin")) + " |")
    return out


def main() -> int:
    out = ["# Tablas del artículo (trazas reservadas, diseño v2)\n"]
    out += table(RES, "Detector heredado") + [""]
    out += table(RES / "processing", "Detector por estación") + [""]
    out += designs() + [""]
    out += sensitivity()
    (RES / "paper_tables.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
