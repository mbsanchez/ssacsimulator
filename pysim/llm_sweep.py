#!/usr/bin/env python3
"""Final evaluation of the LLM planners on the HELD-OUT traces.

The prompt is frozen before this runs (see results/dev_log.md); trace 0-100m,
used for development, is excluded. For every scenario it runs, on the same
trace and fault: no action, the rule baselines, C1 and C2.

Long-running (hours: the local LLM is the bottleneck) and resumable: each
finished run is appended to results/llm_sweep_rows.csv immediately, and a
relaunch skips runs already there. Combined with the response cache, an
interrupted sweep loses at most the run in progress.

    python llm_sweep.py                # run / resume
    python llm_sweep.py --summary      # only rebuild the summary from the CSV
    python llm_sweep.py --limit 2      # smoke test: first 2 scenarios

Use run_overnight.sh to launch it so the Mac does not sleep.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import time
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import Fault
from ssac.llm import OllamaClient
from ssac.llm_planner import PROMPT_VERSION, LLMPlanner
from ssac.metrics import outcome
from ssac.hybrid_planner import HybridPlanner
from ssac.planning import (AdaptiveRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner, NoOpPlanner,
                           TwinOnlyRulePlanner)
from ssac.rag_planner import RAGPlanner

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
RESULTS = HERE / "results"
ROWS = RESULTS / "llm_sweep_rows.csv"
CALLS = RESULTS / "llm_sweep_calls.csv"
SUMMARY = RESULTS / "llm_sweep_summary.md"

# held-out test trace -> calibration trace
HELD_OUT = {
    "test_cases_100m-200m.td": "test_cases_0-100m.td",
    "test_cases_200m-300m.td": "test_cases_500m-600m.td",
    "test_cases_500m-600m.td": "test_cases_200m-300m.td",
}
STATIONS_TWIN = ["L0_S2", "L0_S4", "L0_S6", "L3_S35"]
STATIONS_NO_TWIN = ["L0_S1", "L0_S8", "L3_S29", "L3_S33"]
SHAPES = ["step", "intermittent", "drift"]
RULES = ["noop", "rules_cal", "rules_adapt", "rules_twin", "rules_adapt_ctx"]
LLMS = ["llm_c2", "llm_c1", "hybrid"]
LLM_VERSIONS = {"llm_c1": PROMPT_VERSION, "llm_c2": PROMPT_VERSION, "hybrid": "v2+h1"}
FAULT_OFFSET_MIN = 600.0

ROW_FIELDS = ["trace", "station", "shape", "planner", "model", "prompt_version", "excess_delay_min",
              "maintenances_on_fault", "maintenances_false", "first_action_latency_min", "pieces_rerouted",
              "maintenance_wait_min", "congestion_extra_min", "span_h", "calls", "cache_hits",
              "seconds", "finished", "fault_start_min", "maint_log"]
CALL_FIELDS = ["trace", "station", "shape", "planner", "t_min", "eligible", "verdicts", "acted_on",
               "reason", "problems", "cached", "latency_s"]


def scenarios(limit: int | None):
    out = []
    for trace in HELD_OUT:
        out.append((trace, "", ""))                       # fault-free
        for station in STATIONS_TWIN + STATIONS_NO_TWIN:
            for shape in SHAPES:
                out.append((trace, station, shape))
    return out[:limit] if limit else out


def label(name: str, tag: str) -> str:
    """Row name for a planner: LLM planners run on a non-default model carry
    a tag (e.g. 'hybrid:fable-5.1') so models are never pooled together."""
    return f"{name}:{tag}" if tag and name in LLMS else name


def load_done(model: str, tag: str) -> set[tuple]:
    if not ROWS.exists():
        return set()
    with ROWS.open() as fh:
        done = set()
        for r in csv.DictReader(fh):
            base = r["planner"].split(":")[0]
            if base in RULES or (r["model"] == model and r["prompt_version"] == LLM_VERSIONS.get(base)):
                done.add((r["trace"], r["station"], r["shape"], r["planner"]))
        return done


def append(path: Path, fields: list[str], rows: list[dict]) -> None:
    new = not path.exists()
    with path.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerows(rows)


def run(args) -> None:
    RESULTS.mkdir(exist_ok=True)
    if args.backend == "agent-sdk":
        from ssac.agent_sdk_client import AgentSDKClient
        client = AgentSDKClient(model=args.model, effort=args.effort, cache_path=HERE / "cache" / "llm_cache.sqlite")
    else:
        client = OllamaClient(model=args.model, cache_path=HERE / "cache" / "llm_cache.sqlite")
    done = load_done(args.model, args.tag)
    todo = scenarios(args.limit)
    # Phase 1: rules + C2 on every scenario; phase 2: C1. If the night runs
    # out, the main comparison (C2 vs. rules) is complete and C1 resumes later.
    if args.backend == "agent-sdk":   # scarce quota: the hybrid first, then C2, then C1
        phases = [[p for p in RULES if p in args.planners],
                  [p for p in ["hybrid"] if p in args.planners],
                  [p for p in ["llm_c2"] if p in args.planners],
                  [p for p in ["llm_c1"] if p in args.planners]]
    else:
        phases = [[p for p in RULES + ["llm_c2"] if p in args.planners],
                  [p for p in ["llm_c1"] if p in args.planners],
                  [p for p in ["hybrid"] if p in args.planners]]
    total = len(todo) * len(args.planners)
    print(f"{dt.datetime.now():%H:%M} prompt {PROMPT_VERSION}, model {args.model}: "
          f"{len(done)} runs already done, {total} in plan", flush=True)

    cache: dict = {}
    t_start = time.perf_counter()
    finished = 0
    for phase in phases:
        for trace, station, shape in todo:
            if trace not in cache:
                data = SimulationData.load(ROOT / trace)
                m, _ = BusinessProcessModel.load(MODEL)
                ref = SimulationEngine(m, data)
                ref.run()
                rates = alarm_rates(MODEL, SimulationData.load(ROOT / HELD_OUT[trace]), ("legacy",))
                cache = {trace: (data, dict(ref.lifetimes), rates)}
            data, reference, rates = cache[trace]
            span_h = (data.events[-1].start_time - data.events[0].start_time) / 60.0
            faults = [] if not station else [Fault(station, 3.0, data.events[0].start_time + FAULT_OFFSET_MIN, shape=shape)]

            for name in phase:
                if (trace, station, shape, label(name, args.tag)) in done:
                    continue
                planner = {
                    "noop": lambda: NoOpPlanner(),
                    "rules_cal": lambda: CalibratedRulePlanner(rates),
                    "rules_adapt": lambda: AdaptiveRulePlanner(),
                    "rules_twin": lambda: TwinOnlyRulePlanner(),
                    "rules_adapt_ctx": lambda: ContextAdaptiveRulePlanner(),
                    "hybrid": lambda: HybridPlanner(client, baseline_per_min=rates),
                    "llm_c1": lambda: LLMPlanner(client),
                    "llm_c2": lambda: RAGPlanner(client, baseline_per_min=rates),
                }[name]()
                m, _ = BusinessProcessModel.load(MODEL)
                eng = SimulationEngine(m, data, faults=faults, planner=planner)
                h0 = client.stats["cache_hits"]
                t0 = time.perf_counter()
                eng.run()
                o = outcome(name, eng, reference, faults)
                is_llm = isinstance(planner, LLMPlanner)
                append(ROWS, ROW_FIELDS, [{
                    "trace": trace, "station": station, "shape": shape, "planner": label(name, args.tag),
                    "model": args.model if is_llm else "", "prompt_version": planner.prompt_version if is_llm else "",
                    "excess_delay_min": round(o.excess_delay_min, 3),
                    "maintenances_on_fault": o.maintenances_on_fault, "maintenances_false": o.maintenances_false,
                    "first_action_latency_min": o.first_action_latency_min, "pieces_rerouted": o.pieces_rerouted,
                    "maintenance_wait_min": round(o.maintenance_wait_min, 3),
                    "congestion_extra_min": round(o.congestion_extra_min, 3), "span_h": round(span_h, 2),
                    "calls": len(planner.calls) if is_llm else "",
                    "cache_hits": client.stats["cache_hits"] - h0 if is_llm else "",
                    "seconds": round(time.perf_counter() - t0, 1), "finished": dt.datetime.now().isoformat(timespec="seconds"),
                    "fault_start_min": faults[0].start_min if faults else "",
                    "maint_log": " ".join(f"{d.action.station}@{d.t_min:.0f}" for d in eng.decisions
                                          if d.accepted and type(d.action).__name__ == "Maintenance"),
                }])
                if is_llm:
                    append(CALLS, CALL_FIELDS, [{
                        "trace": trace, "station": station, "shape": shape, "planner": label(name, args.tag),
                        "t_min": round(c.t_min, 1), "eligible": " ".join(c.eligible),
                        "verdicts": json.dumps(c.verdicts), "acted_on": " ".join(c.acted_on),
                        "reason": c.reason, "problems": " | ".join(c.problems),
                        "cached": c.cached, "latency_s": round(c.latency_s, 2),
                    } for c in planner.calls])
                finished += 1
                el = time.perf_counter() - t_start
                extra = ""
                if "api_equivalent_usd" in client.stats:
                    extra = f"  ${client.stats['api_equivalent_usd']:.2f} eq."
                print(f"{dt.datetime.now():%H:%M} {trace.split('_')[2][:-3]:9} {station or 'fault-free':10} "
                      f"{shape:12} {label(name, args.tag):18} {time.perf_counter() - t0:6.0f}s  "
                      f"[{finished} new, {el / 3600:.1f} h]{extra}", flush=True)
    summarize()


# ---- summary ---------------------------------------------------------------

def summarize() -> None:
    if not ROWS.exists():
        print("no rows yet")
        return
    with ROWS.open() as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        r["excess"] = float(r["excess_delay_min"])
    noop = {(r["trace"], r["station"], r["shape"]): r["excess"] for r in rows if r["planner"] == "noop"}
    present = []
    for r in rows:
        if r["planner"].split(":")[0] in LLMS and r["planner"] not in present:
            present.append(r["planner"])
    planners = ["rules_cal", "rules_adapt", "rules_twin", "rules_adapt_ctx"] + sorted(present)
    twins = set(STATIONS_TWIN)

    def pooled(sel):
        num = sum(r["excess"] for r in sel)
        den = sum(noop.get((r["trace"], r["station"], r["shape"]), 0.0) for r in sel)
        wins = sum(1 for r in sel if noop.get((r["trace"], r["station"], r["shape"]), 0.0) > r["excess"])
        return f"{1 - num / den:+.2f} ({wins}/{len(sel)})" if den > 0 and sel else "-"

    fault_rows = [r for r in rows if r["station"]]
    out = [f"# Evaluación final en trazas reservadas — prompt {PROMPT_VERSION}\n",
           f"Generado {dt.datetime.now():%Y-%m-%d %H:%M}. Recuperación agregada (escenarios con beneficio neto).\n",
           "| Grupo | " + " | ".join(planners) + " |", "|---|" + "---|" * len(planners)]
    groups = [("todas", lambda r: True), ("con gemela", lambda r: r["station"] in twins),
              ("sin gemela", lambda r: r["station"] not in twins)]
    groups += [(f"fallo {s}", (lambda s: lambda r: r["shape"] == s)(s)) for s in SHAPES]
    groups += [(f"traza {t.split('_')[2][:-3]}", (lambda t: lambda r: r["trace"] == t)(t)) for t in HELD_OUT]
    for name, pred in groups:
        out.append(f"| {name} | " + " | ".join(
            pooled([r for r in fault_rows if r["planner"] == p and pred(r)]) for p in planners) + " |")

    out += ["\n## Coste de falsas alarmas sin fallo (min-pieza/h)\n",
            "| Traza | " + " | ".join(planners) + " |", "|---|" + "---|" * len(planners)]
    for t in HELD_OUT:
        cells = []
        for p in planners:
            sel = [r for r in rows if r["trace"] == t and not r["station"] and r["planner"] == p]
            cells.append(f"{sel[0]['excess'] / float(sel[0]['span_h']):,.0f}" if sel else "-")
        out.append(f"| {t} | " + " | ".join(cells) + " |")

    def maint(r):
        out_ = []
        for tok in (r.get("maint_log") or "").split():
            st, t = tok.rsplit("@", 1)
            out_.append((st, float(t)))
        return out_

    faultfree = {(r["trace"], r["planner"]): maint(r) for r in rows if not r["station"]}

    def specific_hit(r) -> bool:
        """Acted on the faulty station after the fault started, at a time when
        the same planner on the same trace WITHOUT the fault did not act on
        that station (+-120 min). Routine repairs that coincide with the fault
        do not count."""
        if not r.get("fault_start_min"):
            return False
        t0 = float(r["fault_start_min"])
        ff = [t for st, t in faultfree.get((r["trace"], r["planner"]), []) if st == r["station"]]
        return any(st == r["station"] and t >= t0 and all(abs(t - u) > 120 for u in ff)
                   for st, t in maint(r))

    out += ["\n## Precisión de las acciones (escenarios con fallo)\n",
            "Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). "
            "Un acierto que coincide con una reparación de rutina no cuenta.\n",
            "| Planificador | acierta el fallo | acierto específico | mant. falsos / escenario | latencia mediana (min) |",
            "|---|---|---|---|---|"]
    for p in planners:
        sel = [r for r in fault_rows if r["planner"] == p]
        if not sel:
            continue
        hit = sum(1 for r in sel if int(r["maintenances_on_fault"]) > 0)
        spec = sum(1 for r in sel if specific_hit(r))
        fp = sum(int(r["maintenances_false"]) for r in sel) / len(sel)
        lats = sorted(float(r["first_action_latency_min"]) for r in sel if r["first_action_latency_min"] not in ("", "None"))
        med = lats[len(lats) // 2] if lats else float("nan")
        out.append(f"| {p} | {hit}/{len(sel)} | {spec}/{len(sel)} | {fp:.1f} | {med:,.0f} |")
    SUMMARY.write_text("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nwrote {SUMMARY}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--backend", choices=["ollama", "agent-sdk"], default="ollama")
    ap.add_argument("--model", default=None, help="default: qwen2.5:7b / claude-fable-5-1")
    ap.add_argument("--effort", default="low", help="agent-sdk only")
    ap.add_argument("--tag", default=None, help="row-name suffix for LLM planners (default: none for qwen, "
                                                "'fable-5.1' for claude-fable-5-1)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--planners", nargs="+", default=RULES + LLMS, choices=RULES + LLMS,
                    help="subset of planners (smoke tests)")
    ap.add_argument("--summary", action="store_true")
    ap.add_argument("--results", type=Path, default=None, help="alternative results dir (smoke tests)")
    args = ap.parse_args()
    if args.model is None:
        args.model = "claude-fable-5-1" if args.backend == "agent-sdk" else "qwen2.5:7b"
    if args.tag is None:
        args.tag = {"claude-fable-5-1": "fable-5.1", "claude-fable-5": "fable-5"}.get(args.model, "" if args.backend == "ollama" else args.model)
    if args.results is not None:
        global RESULTS, ROWS, CALLS, SUMMARY
        RESULTS = args.results
        ROWS, CALLS, SUMMARY = RESULTS / "llm_sweep_rows.csv", RESULTS / "llm_sweep_calls.csv", RESULTS / "llm_sweep_summary.md"
    if args.summary:
        summarize()
    else:
        run(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
