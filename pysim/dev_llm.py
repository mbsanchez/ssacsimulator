#!/usr/bin/env python3
"""Development runs for the LLM planners — trace 0-100m ONLY.

Prompt and context design may be iterated on this trace and nowhere else. The
other three traces are held out for the final evaluation, so a prompt cannot
be tuned on the data it is evaluated on. Every invocation appends its results
to results/dev_log.md, so the paper can state exactly which versions were
tried.

    python dev_llm.py                     # C2 on the dev set
    python dev_llm.py --planners c1 c2
    python dev_llm.py --note "what changed"
"""

from __future__ import annotations

import argparse
import datetime as dt
import time
from collections import Counter
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.calibration import alarm_rates
from ssac.intervention import Fault
from ssac.llm import OllamaClient
from ssac.llm_planner import PROMPT_VERSION, LLMPlanner
from ssac.metrics import outcome
from ssac.onsets import HORIZON_MIN, HORIZONS_MIN, onsets
from ssac.hybrid_planner import HybridPlanner
from ssac.planning import (AdaptiveRulePlanner, CalibratedRulePlanner, ContextAdaptiveRulePlanner, NoOpPlanner,
                           TwinOnlyRulePlanner)
from ssac.rag_planner import RAGPlanner

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent / "DataSets I4.0"
MODEL = ROOT / "bosch_pl_tm_model.pg"
DEV_TRACE = "test_cases_0-100m.td"
CALIB_TRACE = "test_cases_100m-200m.td"
DEV_SET = [            # (label, station, shape); None = fault-free run
    ("fault-free", None, None),
    ("L0_S2 step", "L0_S2", "step"),
    ("L3_S29 step", "L3_S29", "step"),
    ("L0_S8 drift", "L0_S8", "drift"),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--planners", nargs="+", default=["c2"], choices=["c1", "c2", "hybrid"])
    ap.add_argument("--backend", choices=["ollama", "agent-sdk"], default="ollama",
                    help="ollama = local model; agent-sdk = Claude via the Claude Agent SDK (Claude plan)")
    ap.add_argument("--model", default=None, help="default: qwen2.5:7b (ollama) / claude-fable-5-1 (agent-sdk)")
    ap.add_argument("--effort", default="low", help="agent-sdk only")
    ap.add_argument("--note", default="")
    ap.add_argument("--cache", type=Path, default=HERE / "cache" / "llm_cache.sqlite")
    ap.add_argument("--analyze", choices=["legacy", "processing"], default="legacy",
                    help="processing: design v2 with the per-station detector and prompt v3 "
                         "(first onset of each dev case, 24-h horizon)")
    args = ap.parse_args()
    import json
    proc = args.analyze == "processing"
    params = json.loads((HERE / "results" / "detector_choice.json").read_text()) if proc else None
    det = (args.analyze,)
    kw = {"analyze": "processing"} if proc else {}
    vers = {"c1": "v3", "c2": "v3", "hybrid": "v3+h1"} if proc else {"c1": PROMPT_VERSION, "c2": PROMPT_VERSION,
                                                                       "hybrid": "v2+h1"}

    data = SimulationData.load(ROOT / DEV_TRACE)
    span_h = (data.events[-1].start_time - data.events[0].start_time) / 60.0
    rates = alarm_rates(MODEL, SimulationData.load(ROOT / CALIB_TRACE), det, processing_params=params)
    m, _ = BusinessProcessModel.load(MODEL)
    ref = SimulationEngine(m, data)
    ref.run()
    reference = dict(ref.lifetimes)
    if args.backend == "agent-sdk":
        from ssac.agent_sdk_client import AgentSDKClient
        args.model = args.model or "claude-fable-5-1"
        client = AgentSDKClient(model=args.model, effort=args.effort, cache_path=args.cache)
    else:
        args.model = args.model or "qwen2.5:7b"
        client = OllamaClient(model=args.model, cache_path=args.cache)

    def make(name):
        return {
            "noop": lambda: NoOpPlanner(),
            "rules_cal": lambda: CalibratedRulePlanner(rates),
            "rules_adapt": lambda: AdaptiveRulePlanner(),
            "rules_twin": lambda: TwinOnlyRulePlanner(),
            "c1": lambda: LLMPlanner(client, prompt_version=vers["c1"], **kw),
            "c2": lambda: RAGPlanner(client, baseline_per_min=rates, prompt_version=vers["c2"], **kw),
            "hybrid": lambda: HybridPlanner(client, baseline_per_min=rates, prompt_version=vers["hybrid"], **kw),
            "rules_adapt_ctx": lambda: ContextAdaptiveRulePlanner(),
        }[name]()

    rows = []
    llm_stats = {}
    for label, station, shape in DEV_SET:
        if proc and station:
            onset = onsets(DEV_TRACE, station, shape, data.events[0].start_time, data.events[-1].start_time)[0]
        else:
            onset = data.events[0].start_time + 600
        faults = [] if station is None else [Fault(station, 3.0, onset, shape=shape)]
        base = None
        for name in ["noop", "rules_cal", "rules_adapt", "rules_twin", "rules_adapt_ctx"] + args.planners:
            planner = make(name)
            m, _ = BusinessProcessModel.load(MODEL)
            eng = SimulationEngine(m, data, faults=faults, planner=planner, detectors=det, processing_params=params)
            h0, s0 = client.stats["cache_hits"], client.stats["seconds"]
            t0 = time.perf_counter()
            eng.run(until_min=onset + HORIZON_MIN if (proc and station) else None)
            o = outcome(name, eng, reference, faults, horizons_min=HORIZONS_MIN)
            ex = o.excess_h[HORIZON_MIN] if (proc and station) else o.excess_delay_min
            if name == "noop":
                base = ex
            row = {
                "case": label, "planner": name, "excess": ex,
                "recovery": (1 - ex / base) if station and base else None,
                "fp_per_h": o.excess_delay_min / span_h if station is None else None,
                "hit": o.maintenances_on_fault, "fp": o.maintenances_false,
                "latency": o.first_action_latency_min, "seconds": time.perf_counter() - t0,
            }
            if isinstance(planner, LLMPlanner):
                calls = planner.calls
                hits = client.stats["cache_hits"] - h0
                verdicts = Counter(v for c in calls for v in c.verdicts.values())
                problems = Counter(p.split(":")[-1].strip().split(",")[0] for c in calls for p in c.problems)
                row.update(calls=len(calls), cache=hits,
                           s_per_call=(client.stats["seconds"] - s0) / max(len(calls) - hits, 1),
                           verdicts=dict(verdicts), problems=dict(problems))
                llm_stats.setdefault(name, []).append(row)
            rows.append(row)
            rec = f"{row['recovery']:+.2f}" if row["recovery"] is not None else "   - "
            fph = f"{row['fp_per_h']:6.0f}/h" if row["fp_per_h"] is not None else "        "
            extra = f"  calls={row['calls']} cache={row['cache']} {row['s_per_call']:.1f}s/call" if "calls" in row else ""
            print(f"{label:12} {name:12} recov={rec} {fph} hit={row['hit']} FP={row['fp']:3d}  {row['seconds']:6.0f}s{extra}", flush=True)

    # ---- dev log ---------------------------------------------------------
    log = HERE / "results" / "dev_log.md"
    log.parent.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    versions = ", ".join(f"{n}: {vers[n]}" for n in args.planners) + (", detector processing, design v2" if proc else "")
    lines = [f"\n## {stamp} — prompts ({versions}), model {args.model}, trace {DEV_TRACE}\n"]
    if args.note:
        lines.append(f"{args.note}\n")
    names = ["rules_cal", "rules_adapt", "rules_twin", "rules_adapt_ctx"] + args.planners
    lines.append("| Caso | " + " | ".join(names) + " |")
    lines.append("|---|" + "---|" * len(names))
    for label, station, _ in DEV_SET:
        cells = []
        for n in names:
            r = next(r for r in rows if r["case"] == label and r["planner"] == n)
            main_ = f"{r['fp_per_h']:.0f}/h" if station is None else f"{r['recovery']:+.2f}"
            cells.append(f"{main_} · {r['fp']} FP")
        lines.append(f"| {label} | " + " | ".join(cells) + " |")
    lines.append("\nFault-free: false-alarm cost in piece-minutes per hour. Faults: recovery vs. no action. FP = repairs of healthy stations.\n")
    for name, rs in llm_stats.items():
        v = Counter()
        pr = Counter()
        for r in rs:
            v.update(r["verdicts"])
            pr.update(r["problems"])
        lines.append(f"- {name}: {sum(r['calls'] for r in rs)} calls, verdicts {dict(v)}, problems {dict(pr) or 'none'}")
    if "api_equivalent_usd" in client.stats:
        lines.append(f"- backend agent-sdk, effort {args.effort}: {client.stats['calls']} calls "
                     f"({client.stats['cache_hits']} cached), API-equivalent cost "
                     f"${client.stats['api_equivalent_usd']:.2f}, retries {client.stats['retries']}")
    with log.open("a") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nappended to {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
