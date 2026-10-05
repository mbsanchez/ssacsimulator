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
from ssac.planning import AdaptiveRulePlanner, CalibratedRulePlanner, NoOpPlanner, TwinOnlyRulePlanner
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
    ap.add_argument("--planners", nargs="+", default=["c2"], choices=["c1", "c2"])
    ap.add_argument("--model", default="qwen2.5:7b")
    ap.add_argument("--note", default="")
    ap.add_argument("--cache", type=Path, default=HERE / "cache" / "llm_cache.sqlite")
    args = ap.parse_args()

    data = SimulationData.load(ROOT / DEV_TRACE)
    span_h = (data.events[-1].start_time - data.events[0].start_time) / 60.0
    rates = alarm_rates(MODEL, SimulationData.load(ROOT / CALIB_TRACE), ("legacy",))
    m, _ = BusinessProcessModel.load(MODEL)
    ref = SimulationEngine(m, data)
    ref.run()
    reference = dict(ref.lifetimes)
    client = OllamaClient(model=args.model, cache_path=args.cache)

    def make(name):
        return {
            "noop": lambda: NoOpPlanner(),
            "rules_cal": lambda: CalibratedRulePlanner(rates),
            "rules_adapt": lambda: AdaptiveRulePlanner(),
            "rules_twin": lambda: TwinOnlyRulePlanner(),
            "c1": lambda: LLMPlanner(client),
            "c2": lambda: RAGPlanner(client, baseline_per_min=rates),
        }[name]()

    rows = []
    llm_stats = {}
    for label, station, shape in DEV_SET:
        faults = [] if station is None else [Fault(station, 3.0, data.events[0].start_time + 600, shape=shape)]
        base = None
        for name in ["noop", "rules_cal", "rules_adapt", "rules_twin"] + args.planners:
            planner = make(name)
            m, _ = BusinessProcessModel.load(MODEL)
            eng = SimulationEngine(m, data, faults=faults, planner=planner)
            h0, s0 = client.stats["cache_hits"], client.stats["seconds"]
            t0 = time.perf_counter()
            eng.run()
            o = outcome(name, eng, reference, faults)
            if name == "noop":
                base = o.excess_delay_min
            row = {
                "case": label, "planner": name, "excess": o.excess_delay_min,
                "recovery": (1 - o.excess_delay_min / base) if station and base else None,
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
    lines = [f"\n## {stamp} — prompt {PROMPT_VERSION}, model {args.model}, trace {DEV_TRACE}\n"]
    if args.note:
        lines.append(f"{args.note}\n")
    names = ["rules_cal", "rules_adapt", "rules_twin"] + args.planners
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
    with log.open("a") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nappended to {log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
