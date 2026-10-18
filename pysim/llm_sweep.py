#!/usr/bin/env python3
"""Final evaluation of the LLM planners on the HELD-OUT traces, design v2.

Design v2 (results/dev_log.md, 2026-10-11): 3 fault onsets per scenario
(ssac/onsets.py), a repair clears only faults active when it starts, and every
fault run stops 24 h after the onset; recovery is measured within that horizon.

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
from ssac.intervention import EffectModel, Fault
from ssac.llm import OllamaClient
from ssac.llm_planner import PROMPT_VERSION, LLMPlanner
from ssac.metrics import outcome
from ssac.onsets import HORIZON_MIN, HORIZONS_MIN, onsets
from ssac.hybrid_planner import HybridPlanner
from ssac.planning import (AdaptiveRulePlanner, BurstVetoRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner,
                           NoOpPlanner, RandomVetoRulePlanner, TwinOnlyRulePlanner)
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
RULES = ["noop", "rules_cal", "rules_adapt", "rules_twin", "rules_adapt_ctx", "rules_cal_rt", "rules_adapt_ctx_rt",
         "rules_burst", "rules_burst_ctx", "rules_burst2_ctx"]
# veto controls chosen on the development trace (results/veto_controls/summary.md)
BURST = json.loads((HERE / "results" / "veto_controls" / "chosen.json").read_text()) \
    if (HERE / "results" / "veto_controls" / "chosen.json").exists() else {}
# validation on new traces (results/dev_log.md, 2026-10-15): base rates from the development trace
NEW_TRACES = {f"test_cases_{n}.td": "test_cases_0-100m.td"
              for n in ("300m-400m", "400m-500m", "600m-700m", "700m-800m", "800m-900m")}
LLMS = ["llm_c2", "llm_c1", "hybrid"]
LLM_VERSIONS = {"llm_c1": PROMPT_VERSION, "llm_c2": PROMPT_VERSION, "hybrid": "v2+h1"}
# --analyze processing: the per-station detector (results/detector_choice.json) and prompt v3
ANALYZE = "legacy"
PROCESSING_PARAMS: dict = {}

ROW_FIELDS = ["trace", "station", "shape", "onset_idx", "planner", "model", "prompt_version", "excess_delay_min",
              "excess_h8_min", "excess_h24_min", "fault_h24_min", "actions_h24_min", "exposure_h24",
              "maintenances_on_fault", "maintenances_false", "first_action_latency_min", "pieces_rerouted",
              "maintenance_wait_min", "congestion_extra_min", "span_h", "calls", "cache_hits",
              "seconds", "finished", "fault_start_min", "maint_log"]
CALL_FIELDS = ["trace", "station", "shape", "onset_idx", "planner", "t_min", "eligible", "verdicts", "acted_on",
               "reason", "problems", "cached", "latency_s"]


COMMON_CAUSE = False   # results/dev_log.md, 2026-10-16: one fault on four stations at once
GROUPS = {"+".join(STATIONS_TWIN): STATIONS_TWIN, "+".join(STATIONS_NO_TWIN): STATIONS_NO_TWIN}


def scenarios(limit: int | None):
    out = []
    for trace in HELD_OUT:
        data = SimulationData.load(ROOT / trace)
        t_first, t_last = data.events[0].start_time, data.events[-1].start_time
        out.append((trace, "", "", "", None))                       # fault-free, whole trace
        for station in (list(GROUPS) if COMMON_CAUSE else STATIONS_TWIN + STATIONS_NO_TWIN):
            for shape in SHAPES:
                for k, onset in enumerate(onsets(trace, station, shape, t_first, t_last)):
                    out.append((trace, station, shape, k, onset))
    return out[:limit] if limit else out


FAULT_FACTOR = 3.0
REPAIR_MIN = 60.0
EFFECTS: dict = {}     # congestion_alpha / maintenance_mode overrides (sensitivity runs)
ABLATION: dict = {}   # alarm_text / burst_cue overrides (results/dev_log.md, 2026-10-15)


def llm_kw(name: str) -> dict:
    kw = {"analyze": ANALYZE, "prompt_version": LLM_VERSIONS[name]} if ANALYZE == "processing" else {}
    if ABLATION:
        kw = {**kw, "analyze": ANALYZE, "prompt_version": LLM_VERSIONS[name]}
        if "alarm_text" in ABLATION:
            kw["alarm_text"] = ABLATION["alarm_text"]
        if name == "hybrid" and "burst_cue" in ABLATION:
            kw["burst_cue"] = ABLATION["burst_cue"]
    return kw


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
                done.add((r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]))
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
        client = AgentSDKClient(model=args.model, effort=args.effort, cache_path=HERE / "cache" / "llm_cache.sqlite",
                                offline=args.offline,
                                **({"harness": f"strict-mcp-v1|replica-{args.replica}"} if args.replica else {}))
    else:
        client = OllamaClient(model=args.model, cache_path=HERE / "cache" / "llm_cache.sqlite", offline=args.offline)
    done = load_done(args.model, args.tag)
    todo = scenarios(args.limit)
    # Phase 1: rules + C2 on every scenario; phase 2: C1. If the night runs
    # out, the main comparison (C2 vs. rules) is complete and C1 resumes later.
    if args.backend == "agent-sdk":   # scarce quota: C2 (the main comparison) first, then the hybrid, then C1
        phases = [[p for p in RULES if p in args.planners],
                  [p for p in ["llm_c2"] if p in args.planners],
                  [p for p in ["hybrid"] if p in args.planners],
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
    # Onset-major order: every planner finishes onset 1 of every scenario (and
    # the fault-free runs) before any planner starts onset 2, so that a quota
    # cut still leaves complete, comparable blocks.
    blocks = [[t for t in todo if t[3] in ("", 0)], [t for t in todo if t[3] == 1], [t for t in todo if t[3] == 2]]
    for phase, block in [(p, b) for b in blocks for p in phases]:
        for trace, station, shape, k, onset in block:
            if trace not in cache:
                data = SimulationData.load(ROOT / trace)
                m, _ = BusinessProcessModel.load(MODEL)
                ref = SimulationEngine(m, data)
                ref.run()
                rates = alarm_rates(MODEL, SimulationData.load(ROOT / HELD_OUT[trace]), (ANALYZE,),
                                    processing_params=PROCESSING_PARAMS or None)
                cache = {trace: (data, dict(ref.lifetimes), rates)}
            data, reference, rates = cache[trace]
            span_h = (data.events[-1].start_time - data.events[0].start_time) / 60.0
            faults = [] if not station else [Fault(s, FAULT_FACTOR, onset, shape=shape) for s in station.split("+")]

            for name in phase:
                if (trace, station, shape, str(k), label(name, args.tag)) in done:
                    continue
                planner = {
                    "noop": lambda: NoOpPlanner(),
                    "rules_cal": lambda: CalibratedRulePlanner(rates, repair_min=REPAIR_MIN),
                    "rules_adapt": lambda: AdaptiveRulePlanner(repair_min=REPAIR_MIN),
                    "rules_twin": lambda: TwinOnlyRulePlanner(repair_min=REPAIR_MIN),
                    "rules_adapt_ctx": lambda: ContextAdaptiveRulePlanner(repair_min=REPAIR_MIN),
                    # re-tuned on the development trace (results/processing/rule_sweep_summary.md)
                    "rules_cal_rt": lambda: CalibratedRulePlanner(rates, window_min=240.0, alpha=1e-4,
                                                                  repair_min=REPAIR_MIN, name="rules_cal_rt"),
                    "rules_adapt_ctx_rt": lambda: ContextAdaptiveRulePlanner(window_min=240.0, alpha=1e-3,
                                                                             history_min=1440.0, repair_min=REPAIR_MIN,
                                                                             name="rules_adapt_ctx_rt"),
                    "rules_burst": lambda: BurstVetoRulePlanner(repair_min=REPAIR_MIN, name="rules_burst",
                                                                **BURST["rules_burst"]),
                    "rules_burst_ctx": lambda: BurstVetoRulePlanner(repair_min=REPAIR_MIN, name="rules_burst_ctx",
                                                                    **BURST["rules_burst_ctx"]),
                    # best burst configuration on the evaluation traces, not selectable on development
                    "rules_burst2_ctx": lambda: BurstVetoRulePlanner(repair_min=REPAIR_MIN, name="rules_burst2_ctx",
                                                                     max_alarm_stations=2, load_veto=True),
                    "hybrid": lambda: HybridPlanner(client, baseline_per_min=rates, repair_min=REPAIR_MIN,
                                                    **llm_kw("hybrid")),
                    "llm_c1": lambda: LLMPlanner(client, repair_min=REPAIR_MIN, **llm_kw("llm_c1")),
                    "llm_c2": lambda: RAGPlanner(client, baseline_per_min=rates, repair_min=REPAIR_MIN,
                                                 **llm_kw("llm_c2")),
                }[name]()
                m, _ = BusinessProcessModel.load(MODEL)
                eng = SimulationEngine(m, data, faults=faults, planner=planner, detectors=(ANALYZE,),
                                       processing_params=PROCESSING_PARAMS or None, effects=EffectModel(**EFFECTS))
                h0 = client.stats["cache_hits"]
                t0 = time.perf_counter()
                eng.run(until_min=onset + HORIZON_MIN if station else None)
                o = outcome(name, eng, reference, faults, horizons_min=HORIZONS_MIN)
                hx = o.excess_h or {}
                is_llm = isinstance(planner, LLMPlanner)
                append(ROWS, ROW_FIELDS, [{
                    "trace": trace, "station": station, "shape": shape, "onset_idx": k,
                    "planner": label(name, args.tag),
                    "model": args.model if is_llm else "", "prompt_version": planner.prompt_version if is_llm else "",
                    # fault runs stop 24 h after the onset: whole-trace excess is undefined
                    "excess_delay_min": "" if station else round(o.excess_delay_min, 3),
                    "excess_h8_min": round(hx.get(480.0, 0.0), 3) if station else "",
                    "excess_h24_min": round(hx.get(1440.0, 0.0), 3) if station else "",
                    "fault_h24_min": round((o.fault_h or {}).get(1440.0, 0.0), 3) if station else "",
                    "actions_h24_min": round((o.actions_h or {}).get(1440.0, 0.0), 3) if station else "",
                    # transitions leaving the faulty station in the window: how much the fault can cost
                    "exposure_h24": sum(1 for e in data.events if e.begin_actor in station.split("+")
                                        and onset <= e.start_time < onset + HORIZON_MIN) if station else "",
                    "maintenances_on_fault": (o.maintenances_on_fault_h or {}).get(HORIZON_MIN, 0) if station
                    else 0,
                    "maintenances_false": (o.maintenances_false_h or {}).get(HORIZON_MIN, 0) if station
                    else o.maintenances_false,
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
                        "trace": trace, "station": station, "shape": shape, "onset_idx": k,
                        "planner": label(name, args.tag), "t_min": round(c.t_min, 1), "eligible": " ".join(c.eligible),
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
                      f"{shape:12} {k!s:2} {label(name, args.tag):18} {time.perf_counter() - t0:6.0f}s  "
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
        r["excess"] = float(r["excess_h24_min"]) if r["station"] else float(r["excess_delay_min"])
    noop = {(r["trace"], r["station"], r["shape"], r["onset_idx"]): r["excess"] for r in rows if r["planner"] == "noop"}
    present = []
    for r in rows:
        if r["planner"].split(":")[0] in LLMS and r["planner"] not in present:
            present.append(r["planner"])
    planners = ["rules_cal", "rules_adapt", "rules_twin", "rules_adapt_ctx"] + sorted(present)
    twins = set(STATIONS_TWIN)

    def pooled(sel):
        num = sum(r["excess"] for r in sel)
        den = sum(noop.get((r["trace"], r["station"], r["shape"], r["onset_idx"]), 0.0) for r in sel)
        wins = sum(1 for r in sel if noop.get((r["trace"], r["station"], r["shape"], r["onset_idx"]), 0.0) > r["excess"])
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
            "Dentro de las 24 h tras el inicio. Acierto específico: actúa sobre la estación averiada cuando, sin el fallo, no lo habría hecho (±120 min). "
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
    ap.add_argument("--factor", type=float, default=3.0, help="fault factor k (sensitivity runs)")
    ap.add_argument("--repair-min", type=float, default=60.0, help="repair duration (sensitivity runs)")
    ap.add_argument("--congestion", type=float, default=None, help="congestion alpha (sensitivity runs)")
    ap.add_argument("--mode", choices=["contingency", "stop"], default=None, help="maintenance mode (sensitivity runs)")
    ap.add_argument("--common-cause", action="store_true", help="one fault on four stations at once")
    ap.add_argument("--replica", type=int, default=None, help="agent-sdk: separate response-store key (replicas)")
    ap.add_argument("--new-traces", action="store_true", help="the five new validation traces instead of the held-out ones")
    ap.add_argument("--alarm-text", choices=["legacy", "processing"], default=None,
                    help="ablation: describe the alarms as this detector regardless of --analyze")
    ap.add_argument("--no-burst-cue", action="store_true", help="ablation: hybrid prompt without the burst cue")
    ap.add_argument("--offline", action="store_true",
                    help="replay from the response store only; a cache miss is an error, no model is called")
    ap.add_argument("--analyze", choices=["legacy", "processing"], default="legacy",
                    help="processing: per-station detector of results/detector_choice.json, prompt v3")
    args = ap.parse_args()
    if args.model is None:
        args.model = "claude-fable-5-1" if args.backend == "agent-sdk" else "qwen2.5:7b"
    if args.tag is None:
        args.tag = {"claude-fable-5-1": "fable-5.1", "claude-fable-5": "fable-5"}.get(args.model, "" if args.backend == "ollama" else args.model)
    if args.analyze == "processing":
        global ANALYZE, PROCESSING_PARAMS
        ANALYZE = "processing"
        PROCESSING_PARAMS = json.loads((HERE / "results" / "detector_choice.json").read_text())
        LLM_VERSIONS.update({"llm_c1": "v3", "llm_c2": "v3", "hybrid": "v3+h1"})
    global FAULT_FACTOR, REPAIR_MIN, COMMON_CAUSE
    FAULT_FACTOR = args.factor
    REPAIR_MIN = args.repair_min
    COMMON_CAUSE = args.common_cause
    if args.congestion is not None:
        EFFECTS["congestion_alpha"] = args.congestion
    if args.mode is not None:
        EFFECTS["maintenance_mode"] = args.mode
    if args.new_traces:
        HELD_OUT.clear()
        HELD_OUT.update(NEW_TRACES)
    if args.alarm_text or args.no_burst_cue:
        base = {"legacy": "v2", "processing": "v3"}[args.alarm_text or args.analyze]
        hyb = base + "+h1" + ("-nocue" if args.no_burst_cue else "")
        LLM_VERSIONS.update({"llm_c1": base, "llm_c2": base, "hybrid": hyb})
        if args.alarm_text:
            ABLATION["alarm_text"] = args.alarm_text
        if args.no_burst_cue:
            ABLATION["burst_cue"] = False
        if args.results is None:
            args.results = HERE / "results" / "processing"
            args.results.mkdir(parents=True, exist_ok=True)
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
