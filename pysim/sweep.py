#!/usr/bin/env python3
"""Sensitivity sweep over the assumptions of the effect model.

Two parts, both on the legacy (original 2020) detectors:

  central grid   full factorial over the scenario axes, at the central
                 parameters: trace x station x fault shape, all planners.
  one-at-a-time  around the central point, vary one parameter at a time:
                 fault severity, repair duration, congestion alpha,
                 maintenance mode. Step faults only.

Every assumption we could not ground in data (repair time, congestion, how
Bosch handles a station under repair) is an axis here, so the paper can
report the range over which a conclusion holds instead of one invented value.

    python sweep.py                  # full sweep, all cores
    python sweep.py --quick          # 1 trace, 2 stations: smoke test
    python sweep.py --workers 4
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass, replace
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import EffectModel, Fault
from ssac.metrics import outcome
from ssac.planning import (AdaptiveRulePlanner, CalibratedRulePlanner, NoOpPlanner, RuleBasedPlanner,
                           TwinOnlyRulePlanner)
from ssac.topology import find_twins

ROOT = Path(__file__).resolve().parent.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
DETECTORS = ("legacy",)

# test trace -> calibration trace (always a different one)
TRACES = {
    "test_cases_0-100m.td": "test_cases_100m-200m.td",
    "test_cases_100m-200m.td": "test_cases_0-100m.td",
    "test_cases_200m-300m.td": "test_cases_500m-600m.td",
    "test_cases_500m-600m.td": "test_cases_200m-300m.td",
}
# Every station has >= 200 short (processing-regime) transitions in all four
# traces, so a fault on it is observable everywhere; each twin station comes
# from a different twin pair.
STATIONS_TWIN = ["L0_S2", "L0_S4", "L0_S6", "L3_S35"]
STATIONS_NO_TWIN = ["L0_S1", "L0_S8", "L3_S29", "L3_S33"]
MIN_FAULT_COST = 1000.0   # scenarios where doing nothing costs less are not scored per-scenario
SHAPES = ["step", "intermittent", "drift"]
FAULT_OFFSET_MIN = 600.0   # fault starts this long after the trace's first event


@dataclass(frozen=True)
class Config:
    factor: float = 3.0
    repair_min: float = 60.0
    alpha: float = 0.5
    mode: str = "contingency"
    contingency_factor: float = 1.5


CENTRAL = Config()
OAT = {
    "factor": [1.5, 5.0],
    "repair_min": [15.0, 240.0],
    "alpha": [0.0, 1.0],
    "mode": ["stop"],
}


@dataclass(frozen=True)
class Task:
    part: str          # "central" | "oat" | "faultfree"
    varied: str        # name of the varied parameter, "" for central
    trace: str
    station: str
    shape: str
    planner: str
    cfg: Config


# ---- worker ------------------------------------------------------------

_W: dict = {}


def _init(references: dict[str, dict[str, float]], rates: dict[str, dict[str, float]]) -> None:
    _W["references"] = references
    _W["rates"] = rates
    _W["data"] = {}


def _data(trace: str) -> SimulationData:
    if trace not in _W["data"]:
        _W["data"][trace] = SimulationData.load(ROOT / trace)
    return _W["data"][trace]


def _planner(name: str, trace: str, cfg: Config):
    if name == "noop":
        return NoOpPlanner()
    if name == "rules_naive":
        return RuleBasedPlanner(repair_min=cfg.repair_min)
    if name == "rules_cal":
        return CalibratedRulePlanner(_W["rates"][trace], repair_min=cfg.repair_min)
    if name == "rules_adapt":
        return AdaptiveRulePlanner(repair_min=cfg.repair_min)
    if name == "rules_twin":
        return TwinOnlyRulePlanner(repair_min=cfg.repair_min)
    raise ValueError(name)


def run_task(task: Task) -> dict:
    t0 = time.perf_counter()
    data = _data(task.trace)
    start = data.events[0].start_time + FAULT_OFFSET_MIN
    faults = [] if task.part == "faultfree" else [Fault(task.station, task.cfg.factor, start, shape=task.shape)]
    model, errors = BusinessProcessModel.load(MODEL)
    assert not errors, errors
    effects = EffectModel(
        congestion_alpha=task.cfg.alpha,
        maintenance_mode=task.cfg.mode,
        contingency_factor=task.cfg.contingency_factor,
    )
    engine = SimulationEngine(
        model, data,
        faults=faults,
        planner=_planner(task.planner, task.trace, task.cfg),
        effects=effects,
        detectors=DETECTORS,
    )
    engine.run()
    o = outcome(task.planner, engine, _W["references"][task.trace], faults)
    span_h = (data.events[-1].start_time - data.events[0].start_time) / 60.0
    row = {
        "part": task.part, "varied": task.varied, "trace": task.trace,
        "station": task.station, "shape": task.shape, "planner": task.planner,
        **{f"cfg_{k}": v for k, v in asdict(task.cfg).items()},
        **{k: v for k, v in asdict(o).items() if k not in ("policy", "recovery")},
        "span_h": round(span_h, 2),
        "seconds": round(time.perf_counter() - t0, 2),
    }
    return row


# ---- setup -------------------------------------------------------------

def _reference(trace: str) -> dict[str, float]:
    model, _ = BusinessProcessModel.load(MODEL)
    engine = SimulationEngine(model, SimulationData.load(ROOT / trace), detectors=DETECTORS)
    engine.run()
    return dict(engine.lifetimes)


def _rates(calib_trace: str) -> dict[str, float]:
    return alarm_rates(MODEL, SimulationData.load(ROOT / calib_trace), DETECTORS)


def build_tasks(traces, stations) -> list[Task]:
    tasks: list[Task] = []
    planners = ["noop", "rules_naive", "rules_cal", "rules_adapt", "rules_twin"]
    for trace in traces:
        for p in ["rules_naive", "rules_cal", "rules_adapt", "rules_twin"]:
            tasks.append(Task("faultfree", "", trace, "", "", p, CENTRAL))
            for param in ("repair_min", "alpha", "mode"):
                for v in OAT[param]:
                    cfg = replace(CENTRAL, **{param: v})
                    tasks.append(Task("faultfree", f"{param}={v:g}" if isinstance(v, float) else f"{param}={v}",
                                      trace, "", "", p, cfg))
        for station in stations:
            for shape in SHAPES:
                for p in planners:
                    tasks.append(Task("central", "", trace, station, shape, p, CENTRAL))
            for param, values in OAT.items():
                for v in values:
                    cfg = replace(CENTRAL, **{param: v})
                    # noop does not depend on planner-side parameters; only on the fault
                    planners_here = ["noop", "rules_cal", "rules_adapt", "rules_twin"] if param == "factor" \
                        else ["rules_cal", "rules_adapt", "rules_twin"]
                    for p in planners_here:
                        tasks.append(Task("oat", f"{param}={v:g}" if isinstance(v, float) else f"{param}={v}",
                                          trace, station, "step", p, cfg))
    return tasks


# ---- analysis ----------------------------------------------------------

def add_recovery(rows: list[dict]) -> None:
    """Per-scenario net benefit against the no-action run with the same fault.

    `recovery` is only defined when doing nothing costs at least
    MIN_FAULT_COST: a fault on a station that barely works in a trace costs
    almost nothing, and dividing a fixed false-alarm cost by it is meaningless.
    Aggregate results use the pooled ratio instead (see `pooled`)."""
    noop = {}
    for r in rows:
        if r["planner"] == "noop":
            noop[(r["trace"], r["station"], r["shape"], r["cfg_factor"])] = r["excess_delay_min"]
    for r in rows:
        base = noop.get((r["trace"], r["station"], r["shape"], r["cfg_factor"]))
        r["noop_excess_min"] = base
        r["net_benefit_min"] = (base - r["excess_delay_min"]) if base is not None else None
        r["recovery"] = (1.0 - r["excess_delay_min"] / base) if base and base >= MIN_FAULT_COST else None


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return float("nan")
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def pooled(sel: list[dict]) -> float:
    """1 - sum(policy excess) / sum(no-action excess)."""
    num = sum(r["excess_delay_min"] for r in sel)
    den = sum(r["noop_excess_min"] for r in sel if r["noop_excess_min"] is not None)
    return 1.0 - num / den if den > 0 else float("nan")


def summarize(rows: list[dict], twins: set[str]) -> str:
    out = []
    planners = ["rules_naive", "rules_cal", "rules_adapt", "rules_twin"]

    def cell(sel):
        wins = sum(1 for r in sel if (r["net_benefit_min"] or 0) > 0)
        return f"{pooled(sel):+6.2f} ({wins}/{len(sel)})"

    central = [r for r in rows if r["part"] == "central"]

    out.append("## Coste de las falsas alarmas — corridas SIN fallo\n")
    out.append("Minutos-pieza perdidos por hora de operación, solo por actuar sobre ruido. Punto central.\n")
    out.append("| Traza | " + " | ".join(planners) + " |")
    out.append("|---|" + "---|" * len(planners))
    ff = [r for r in rows if r["part"] == "faultfree" and r["varied"] == ""]
    for tr in sorted({r["trace"] for r in ff}):
        cells = []
        for p in planners:
            sel = [r for r in ff if r["trace"] == tr and r["planner"] == p]
            cells.append(f"{sel[0]['excess_delay_min'] / sel[0]['span_h']:,.0f}" if sel else "-")
        out.append(f"| {tr} | " + " | ".join(cells) + " |")

    out.append("\n## Rejilla central — recuperación agregada (escenarios con beneficio neto > 0)\n")
    out.append("Recuperación agregada = 1 − Σ exceso(política) / Σ exceso(no hacer nada). "
               "Detector legacy; fallo x3, reparación 60 min, α = 0,5, contingencia.\n")
    out.append("| Grupo | " + " | ".join(planners) + " |")
    out.append("|---|" + "---|" * len(planners))
    groups = [("todas", lambda r: True),
              ("con gemela", lambda r: r["station"] in twins),
              ("sin gemela", lambda r: r["station"] not in twins)]
    groups += [(f"fallo {s}", (lambda s: lambda r: r["shape"] == s)(s)) for s in SHAPES]
    groups += [(f"traza {t.split('_')[2].removesuffix('.td')}", (lambda t: lambda r: r["trace"] == t)(t))
               for t in sorted({r["trace"] for r in central})]
    for name, pred in groups:
        out.append(f"| {name} | " + " | ".join(
            cell([r for r in central if r["planner"] == p and pred(r)]) for p in planners) + " |")

    out.append("\n## Sensibilidad uno-a-uno — recuperación agregada\n")
    out.append("Fallo escalón. Cada fila cambia un único parámetro respecto al punto central.\n")
    pl = ["rules_cal", "rules_adapt", "rules_twin"]
    out.append("| Variación | " + " | ".join(pl) + " |")
    out.append("|---|" + "---|" * len(pl))
    central_step = [r for r in central if r["shape"] == "step"]
    out.append("| **central** | " + " | ".join(cell([r for r in central_step if r["planner"] == p]) for p in pl) + " |")
    oat = [r for r in rows if r["part"] == "oat"]
    for varied in sorted({r["varied"] for r in oat}):
        out.append(f"| {varied} | " + " | ".join(
            cell([r for r in oat if r["varied"] == varied and r["planner"] == p]) for p in pl) + " |")

    out.append("\n## Desglose del coste — rejilla central, medias por escenario (minutos-pieza)\n")
    out.append("| Planificador | exceso | mant. sobre fallo | mant. falsos | latencia 1ª acción (min) | contingencia | congestión |")
    out.append("|---|---|---|---|---|---|---|")
    for p in ["noop"] + planners:
        sel = [r for r in central if r["planner"] == p]
        out.append(
            f"| {p} | {_mean([r['excess_delay_min'] for r in sel]):,.0f} | "
            f"{_mean([r['maintenances_on_fault'] for r in sel]):.1f} | "
            f"{_mean([r['maintenances_false'] for r in sel]):.1f} | "
            f"{_median([r['first_action_latency_min'] for r in sel if r['first_action_latency_min'] not in (None, '')]):,.0f} | "
            f"{_mean([r['maintenance_wait_min'] for r in sel]):,.0f} | "
            f"{_mean([r['congestion_extra_min'] for r in sel]):,.0f} |"
        )
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "results")
    args = ap.parse_args()

    traces = list(TRACES)[:1] if args.quick else list(TRACES)
    stations = ([STATIONS_TWIN[0], STATIONS_NO_TWIN[0]] if args.quick
                else STATIONS_TWIN + STATIONS_NO_TWIN)
    tasks = build_tasks(traces, stations)

    model, _ = BusinessProcessModel.load(MODEL)
    twins = set(find_twins(model))
    for s in STATIONS_TWIN:
        assert s in twins, f"{s} expected to have a twin"
    for s in STATIONS_NO_TWIN:
        assert s not in twins, f"{s} expected to have no twin"

    t0 = time.perf_counter()
    print(f"{len(tasks)} runs on {args.workers} workers; computing references and calibration...")
    with ProcessPoolExecutor(args.workers) as pool:
        ref_f = {t: pool.submit(_reference, t) for t in traces}
        rate_f = {t: pool.submit(_rates, TRACES[t]) for t in traces}
        references = {t: f.result() for t, f in ref_f.items()}
        rates = {t: f.result() for t, f in rate_f.items()}
    print(f"  done in {time.perf_counter() - t0:.0f}s")

    rows: list[dict] = []
    t1 = time.perf_counter()
    with ProcessPoolExecutor(args.workers, initializer=_init, initargs=(references, rates)) as pool:
        futures = [pool.submit(run_task, t) for t in tasks]
        for i, f in enumerate(as_completed(futures), 1):
            rows.append(f.result())
            if i % 20 == 0 or i == len(futures):
                el = time.perf_counter() - t1
                print(f"  {i}/{len(futures)}  {el:.0f}s elapsed, ~{el / i * (len(futures) - i):.0f}s left", flush=True)

    add_recovery(rows)
    args.out.mkdir(parents=True, exist_ok=True)
    with (args.out / "sweep.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["part"], r["varied"], r["trace"], r["station"], r["shape"], r["planner"])))
    summary = summarize(rows, twins)
    (args.out / "sweep_summary.md").write_text(summary + "\n")
    (args.out / "sweep_meta.json").write_text(json.dumps({
        "runs": len(rows), "workers": args.workers, "quick": args.quick,
        "seconds": round(time.perf_counter() - t0), "central": asdict(CENTRAL),
        "oat": OAT, "traces": TRACES, "stations_twin": STATIONS_TWIN,
        "stations_no_twin": STATIONS_NO_TWIN, "detectors": DETECTORS,
        "min_fault_cost": MIN_FAULT_COST, "effect_model": "additive, scaled by tau_S",
    }, indent=2))
    print("\n" + summary)
    print(f"\nwrote {args.out}/sweep.csv, sweep_summary.md, sweep_meta.json  ({time.perf_counter() - t0:.0f}s total)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
