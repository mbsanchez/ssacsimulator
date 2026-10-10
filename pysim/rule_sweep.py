#!/usr/bin/env python3
"""Rule-only experiments. No language model is called.

  A  naive cooldown   the naive planner with the 240 min cooldown of every
                      other planner (it uses 120 min by default).
  B  tuned baselines  grid over the change-test hyperparameters (window,
                      Poisson level, history) of the adaptive rule and its
                      load-veto control, and over window and level of the
                      calibrated rule, on all fault shapes. Configurations are
                      SELECTED on the development trace 0-100m only and then
                      evaluated on the three held-out traces, the same protocol
                      the LLM prompts followed. The held-out optimum is also
                      reported, as an upper bound no honest protocol reaches.

Scenarios are those of llm_sweep.py (8 stations x 3 shapes, fault x3 starting
600 min after the first event, central effect model), so held-out results are
directly comparable with the rows in results/llm_sweep_rows.csv.

    python rule_sweep.py              # run everything (~10 min on 7 workers)
    python rule_sweep.py --summary    # rebuild the summary from the CSV
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import Fault
from ssac.metrics import outcome
from ssac.planning import (AdaptiveRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner, NoOpPlanner,
                           RuleBasedPlanner)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
RESULTS = HERE / "results"
ROWS = RESULTS / "rule_sweep.csv"
SUMMARY = RESULTS / "rule_sweep_summary.md"

DEV = "test_cases_0-100m.td"
# trace -> calibration trace (same pairs as sweep.py / llm_sweep.py)
TRACES = {
    "test_cases_0-100m.td": "test_cases_100m-200m.td",
    "test_cases_100m-200m.td": "test_cases_0-100m.td",
    "test_cases_200m-300m.td": "test_cases_500m-600m.td",
    "test_cases_500m-600m.td": "test_cases_200m-300m.td",
}
HELD_OUT = [t for t in TRACES if t != DEV]
STATIONS = ["L0_S2", "L0_S4", "L0_S6", "L3_S35", "L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]
FAULT_OFFSET_MIN = 600.0

WINDOWS = [60.0, 120.0, 180.0, 240.0, 360.0]
ALPHAS = [1e-2, 1e-3, 1e-4]
HISTORIES = [720.0, 1440.0, 2880.0]
DEFAULT = {"window_min": 120.0, "alpha": 1e-3, "history_min": 1440.0}

FIELDS = ["trace", "station", "shape", "planner", "config", "excess_delay_min", "maintenances_on_fault",
          "maintenances_false", "first_action_latency_min", "span_h", "fault_start_min", "maint_log"]


def configs() -> list[tuple[str, str, dict]]:
    """(planner kind, config label, constructor kwargs)."""
    out = [("noop", "", {}),
           ("rules_naive", "cooldown=120", {"cooldown_min": 120.0}),
           ("rules_naive", "cooldown=240", {"cooldown_min": 240.0})]
    for w, a in itertools.product(WINDOWS, ALPHAS):
        out.append(("rules_cal", f"w={w:g} a={a:g}", {"window_min": w, "alpha": a}))
    for kind in ("rules_adapt", "rules_adapt_ctx"):
        for w, a, h in itertools.product(WINDOWS, ALPHAS, HISTORIES):
            out.append((kind, f"w={w:g} a={a:g} h={h:g}", {"window_min": w, "alpha": a, "history_min": h}))
    return out


def default_label(kind: str) -> str:
    d = DEFAULT
    if kind == "rules_cal":
        return f"w={d['window_min']:g} a={d['alpha']:g}"
    return f"w={d['window_min']:g} a={d['alpha']:g} h={d['history_min']:g}"


# ---- worker ------------------------------------------------------------

_W: dict = {}


def _init(references, rates):
    _W.update(references=references, rates=rates, data={})


def _data(trace):
    if trace not in _W["data"]:
        _W["data"][trace] = SimulationData.load(ROOT / trace)
    return _W["data"][trace]


def _planner(kind, kwargs, trace):
    if kind == "noop":
        return NoOpPlanner()
    if kind == "rules_naive":
        return RuleBasedPlanner(**kwargs)
    if kind == "rules_cal":
        return CalibratedRulePlanner(_W["rates"][trace], **kwargs)
    if kind == "rules_adapt":
        return AdaptiveRulePlanner(**kwargs)
    if kind == "rules_adapt_ctx":
        return ContextAdaptiveRulePlanner(**kwargs)
    raise ValueError(kind)


def run_task(task):
    trace, station, shape, kind, label, kwargs = task
    data = _data(trace)
    faults = [] if not station else [Fault(station, 3.0, data.events[0].start_time + FAULT_OFFSET_MIN, shape=shape)]
    model, _ = BusinessProcessModel.load(MODEL)
    eng = SimulationEngine(model, data, faults=faults, planner=_planner(kind, kwargs, trace))
    eng.run()
    o = outcome(kind, eng, _W["references"][trace], faults)
    return {
        "trace": trace, "station": station, "shape": shape, "planner": kind, "config": label,
        "excess_delay_min": round(o.excess_delay_min, 3),
        "maintenances_on_fault": o.maintenances_on_fault, "maintenances_false": o.maintenances_false,
        "first_action_latency_min": "" if o.first_action_latency_min is None else o.first_action_latency_min,
        "span_h": round((data.events[-1].start_time - data.events[0].start_time) / 60.0, 2),
        "fault_start_min": faults[0].start_min if faults else "",
        "maint_log": " ".join(f"{d.action.station}@{d.t_min:.0f}" for d in eng.decisions
                              if d.accepted and type(d.action).__name__ == "Maintenance"),
    }


def _reference(trace):
    m, _ = BusinessProcessModel.load(MODEL)
    eng = SimulationEngine(m, SimulationData.load(ROOT / trace))
    eng.run()
    return dict(eng.lifetimes)


def _rates(trace):
    return alarm_rates(MODEL, SimulationData.load(ROOT / TRACES[trace]), ("legacy",))


def run(workers: int) -> None:
    scen = [(t, "", "") for t in TRACES] + [(t, s, sh) for t in TRACES for s in STATIONS for sh in SHAPES]
    tasks = [(t, s, sh, kind, label, kw) for t, s, sh in scen for kind, label, kw in configs()
             if not (kind == "noop" and not s)]
    print(f"{len(tasks)} runs on {workers} workers", flush=True)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(workers) as pool:
        refs = {t: pool.submit(_reference, t) for t in TRACES}
        rts = {t: pool.submit(_rates, t) for t in TRACES}
        references = {t: f.result() for t, f in refs.items()}
        rates = {t: f.result() for t, f in rts.items()}
    rows = []
    with ProcessPoolExecutor(workers, initializer=_init, initargs=(references, rates)) as pool:
        futs = [pool.submit(run_task, t) for t in tasks]
        for i, f in enumerate(as_completed(futs), 1):
            rows.append(f.result())
            if i % 500 == 0 or i == len(futs):
                el = time.perf_counter() - t0
                print(f"  {i}/{len(futs)}  {el:.0f}s, ~{el / i * (len(futs) - i):.0f}s left", flush=True)
    RESULTS.mkdir(exist_ok=True)
    with ROWS.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["planner"], r["config"], r["trace"], r["station"], r["shape"])))
    (RESULTS / "rule_sweep_meta.json").write_text(json.dumps({
        "runs": len(rows), "workers": workers, "seconds": round(time.perf_counter() - t0),
        "dev": DEV, "held_out": HELD_OUT, "calibration": TRACES, "windows": WINDOWS, "alphas": ALPHAS,
        "histories": HISTORIES, "default": DEFAULT, "fault_factor": 3.0, "fault_offset_min": FAULT_OFFSET_MIN,
    }, indent=2))


# ---- analysis ----------------------------------------------------------

def load_rows():
    rows = list(csv.DictReader(ROWS.open()))
    for r in rows:
        r["excess"] = float(r["excess_delay_min"])
    return rows


def maint(r):
    out = []
    for tok in (r.get("maint_log") or "").split():
        st, t = tok.rsplit("@", 1)
        out.append((st, float(t)))
    return out


def summarize() -> None:
    rows = load_rows()
    noop = {(r["trace"], r["station"], r["shape"]): r["excess"] for r in rows if r["planner"] == "noop"}
    fault = [r for r in rows if r["station"] and r["planner"] != "noop"]
    ff = {(r["trace"], r["planner"], r["config"]): r for r in rows if not r["station"]}
    by = {}
    for r in fault:
        by.setdefault((r["planner"], r["config"]), []).append(r)

    def sel(p, c, traces, shapes=SHAPES):
        return [r for r in by[(p, c)] if r["trace"] in traces and r["shape"] in shapes]

    def pooled(rs):
        den = sum(noop[(r["trace"], r["station"], r["shape"])] for r in rs)
        return 1 - sum(r["excess"] for r in rs) / den if den else float("nan")

    def wins(rs):
        return sum(1 for r in rs if noop[(r["trace"], r["station"], r["shape"])] > r["excess"])

    def fa_cost(p, c, traces):
        return sum(ff[(t, p, c)]["excess"] / float(ff[(t, p, c)]["span_h"]) for t in traces) / len(traces)

    def hits(rs, p, c):
        hit = sum(1 for r in rs if int(r["maintenances_on_fault"]) > 0)
        spec = 0
        for r in rs:
            t0 = float(r["fault_start_min"])
            fft = [t for st, t in maint(ff[(r["trace"], p, c)]) if st == r["station"]]
            spec += any(st == r["station"] and t >= t0 and all(abs(t - u) > 120 for u in fft) for st, t in maint(r))
        lats = sorted(float(r["first_action_latency_min"]) for r in rs if r["first_action_latency_min"])
        med = lats[len(lats) // 2] if lats else float("nan")
        return hit, spec, med

    # LLM rows for comparison (held-out only)
    llm = {}
    llm_path = RESULTS / "llm_sweep_rows.csv"
    if llm_path.exists():
        for r in csv.DictReader(llm_path.open()):
            if r["station"]:
                llm.setdefault(r["planner"], []).append(dict(r, excess=float(r["excess_delay_min"])))

    out = ["# Experimentos solo con reglas (sin LLM)\n",
           "Escenarios de `llm_sweep.py`: 8 estaciones × 3 formas, fallo ×3 desde el minuto 600, modelo de efectos central. "
           "Recuperación agregada = 1 − Σ exceso / Σ exceso sin acción; entre paréntesis, escenarios con beneficio neto. "
           f"Desarrollo = `{DEV}`; reservadas = las otras tres.\n"]

    # consistency with the held-out evaluation
    chk = []
    for p in ("rules_adapt", "rules_adapt_ctx", "rules_cal"):
        if p in llm:
            mine = {(r["trace"], r["station"], r["shape"]): r["excess"] for r in sel(p, default_label(p), HELD_OUT)}
            theirs = {(r["trace"], r["station"], r["shape"]): r["excess"] for r in llm[p]}
            diff = max(abs(mine[k] - theirs[k]) for k in theirs)
            chk.append(f"{p}: máx. |Δ exceso| = {diff:.3f} min-pieza en {len(theirs)} escenarios")
    if chk:
        out += ["Comprobación: la configuración por defecto reproduce `llm_sweep_rows.csv` — " + "; ".join(chk) + ".\n"]

    # A: naive cooldown
    out += ["## A. Planificador ingenuo con el mismo tiempo de espera que el resto\n",
            "| Tiempo de espera | 4 trazas | reservadas | mant. falsos / escenario | coste falsas alarmas (min-pieza/h, 4 trazas) |",
            "|---|---|---|---|---|"]
    for c in ("cooldown=120", "cooldown=240"):
        a = sel("rules_naive", c, list(TRACES))
        h = sel("rules_naive", c, HELD_OUT)
        fp = sum(int(r["maintenances_false"]) for r in a) / len(a)
        out.append(f"| {c.split('=')[1]} min | {pooled(a):+.3f} ({wins(a)}/{len(a)}) | {pooled(h):+.3f} ({wins(h)}/{len(h)}) "
                   f"| {fp:.1f} | {fa_cost('rules_naive', c, list(TRACES)):,.0f} |")

    # B: tuned baselines
    for p in ("rules_adapt", "rules_adapt_ctx", "rules_cal"):
        cfgs = sorted(c for (pp, c) in by if pp == p)
        dflt = default_label(p)
        out += [f"\n## B. `{p}` — {len(cfgs)} configuraciones\n"]
        # selection on dev, all shapes and per shape
        best_dev = max(cfgs, key=lambda c: pooled(sel(p, c, [DEV])))
        best_ho = max(cfgs, key=lambda c: pooled(sel(p, c, HELD_OUT)))
        rowsel = [("por defecto", dflt), ("elegida en desarrollo (todas las formas)", best_dev),
                  ("óptimo en reservadas (cota superior)", best_ho)]
        out += ["| Configuración | | desarrollo | reservadas | escalón | intermitente | deriva | acierta / específico / latencia mediana | falsas alarmas (min-pieza/h) |",
                "|---|---|---|---|---|---|---|---|---|"]
        for name, c in rowsel:
            ho = sel(p, c, HELD_OUT)
            shp = [pooled(sel(p, c, HELD_OUT, [s])) for s in SHAPES]
            hit, spec, med = hits(ho, p, c)
            out.append(f"| {name} | `{c}` | {pooled(sel(p, c, [DEV])):+.3f} | {pooled(ho):+.3f} ({wins(ho)}/{len(ho)}) | "
                       + " | ".join(f"{v:+.3f}" for v in shp)
                       + f" | {hit}/{len(ho)} / {spec}/{len(ho)} / {med:,.0f} | {fa_cost(p, c, HELD_OUT):,.0f} |")
        # per-shape selection on dev (a rule specialised for intermittent faults)
        out += ["\nSelección por forma de fallo (elegida en desarrollo sobre esa forma; evaluada en reservadas sobre esa forma):\n",
                "| Forma | elegida en desarrollo | desarrollo | reservadas | óptimo en reservadas | reservadas (óptimo) |",
                "|---|---|---|---|---|---|"]
        for s in SHAPES:
            bd = max(cfgs, key=lambda c: pooled(sel(p, c, [DEV], [s])))
            bh = max(cfgs, key=lambda c: pooled(sel(p, c, HELD_OUT, [s])))
            out.append(f"| {s} | `{bd}` | {pooled(sel(p, c=bd, traces=[DEV], shapes=[s])):+.3f} | "
                       f"{pooled(sel(p, bd, HELD_OUT, [s])):+.3f} | `{bh}` | {pooled(sel(p, bh, HELD_OUT, [s])):+.3f} |")
        # distribution of held-out recovery over the grid
        vals = sorted(pooled(sel(p, c, HELD_OUT)) for c in cfgs)
        ivals = sorted(pooled(sel(p, c, HELD_OUT, ["intermittent"])) for c in cfgs)
        out += [f"\nEn la rejilla, recuperación en reservadas: mín. {vals[0]:+.3f}, mediana {vals[len(vals) // 2]:+.3f}, "
                f"máx. {vals[-1]:+.3f}. Solo intermitente: mín. {ivals[0]:+.3f}, mediana {ivals[len(ivals) // 2]:+.3f}, "
                f"máx. {ivals[-1]:+.3f}."]

    # comparison with the LLM planners on the same held-out scenarios
    if llm:
        out += ["\n## Comparación con los planificadores LLM (reservadas, mismos 72 escenarios)\n",
                "| Planificador | todas | escalón | intermitente | deriva |", "|---|---|---|---|---|"]

        def lp(rs, shapes=SHAPES):
            rs = [r for r in rs if r["shape"] in shapes]
            return pooled(rs)
        lines = [("rules_adapt_ctx por defecto", sel("rules_adapt_ctx", default_label("rules_adapt_ctx"), HELD_OUT))]
        for p in ("rules_adapt", "rules_adapt_ctx"):
            cfgs = sorted(c for (pp, c) in by if pp == p)
            bd = max(cfgs, key=lambda c: pooled(sel(p, c, [DEV])))
            lines.append((f"{p} elegida en desarrollo `{bd}`", sel(p, bd, HELD_OUT)))
            bi = max(cfgs, key=lambda c: pooled(sel(p, c, [DEV], ["intermittent"])))
            lines.append((f"{p} especializada en intermitente (desarrollo) `{bi}`", sel(p, bi, HELD_OUT)))
        for name in ("llm_c2:fable-5.1", "hybrid:fable-5.1", "llm_c2"):
            if name in llm:
                lines.append((name, llm[name]))
        for name, rs in lines:
            out.append(f"| {name} | {lp(rs):+.3f} | " + " | ".join(f"{lp(rs, [s]):+.3f}" for s in SHAPES) + " |")

        # paired comparison of C2 on Fable against re-tuned rules
        if "llm_c2:fable-5.1" in llm:
            import random
            from scipy.stats import wilcoxon
            fab = {(r["trace"], r["station"], r["shape"]): r["excess"] for r in llm["llm_c2:fable-5.1"]}
            out += ["\n## C2 con Fable 5.1 frente a reglas reajustadas (emparejado)\n",
                    "Δ = recuperación(Fable) − recuperación(regla), IC 95 % bootstrap estratificado por traza "
                    "(10 000, semilla 0, como `stats.py`); Wilcoxon sobre el exceso por escenario, sin ajuste.\n",
                    "| Regla | Configuración | Formas | Δ | IC 95 % | Fable mejor en | p |", "|---|---|---|---|---|---|---|"]
            targets = []
            for p in ("rules_adapt", "rules_adapt_ctx"):
                cfgs = sorted(c for (pp, c) in by if pp == p)
                targets += [(p, "por defecto", default_label(p)),
                            (p, "elegida en desarrollo", max(cfgs, key=lambda c: pooled(sel(p, c, [DEV])))),
                            (p, "óptimo en reservadas", max(cfgs, key=lambda c: pooled(sel(p, c, HELD_OUT))))]
            for p, kind, c in targets:
                ru = {(r["trace"], r["station"], r["shape"]): r["excess"] for r in sel(p, c, HELD_OUT)}
                for sname, shapes in (("todas", SHAPES), ("intermitente", ["intermittent"])):
                    ks = sorted(k for k in fab if k[2] in shapes)

                    def d(s):
                        return (sum(ru[k] for k in s) - sum(fab[k] for k in s)) / sum(noop[k] for k in s)
                    strata = {t: [k for k in ks if k[0] == t] for t in HELD_OUT}
                    rng = random.Random(0)
                    boot = sorted(d([rng.choice(strata[t]) for t in HELD_OUT for _ in strata[t]]) for _ in range(10_000))
                    better = sum(fab[k] < ru[k] for k in ks)
                    pv = wilcoxon([fab[k] - ru[k] for k in ks]).pvalue
                    out.append(f"| {p} | {kind} `{c}` | {sname} | {d(ks):+.3f} | [{boot[249]:+.3f}, {boot[9749]:+.3f}] "
                               f"| {better}/{len(ks)} | {pv:.3f} |")

    SUMMARY.write_text("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nwrote {SUMMARY}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--summary", action="store_true")
    args = ap.parse_args()
    if not args.summary:
        run(args.workers)
    summarize()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
