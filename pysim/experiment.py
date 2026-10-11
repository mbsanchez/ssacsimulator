#!/usr/bin/env python3
"""Fault-injection experiments: reference vs. no action vs. planners.

    python experiment.py                         # default scenarios
    python experiment.py --station L0_S2 --factor 3 --start 600

For every scenario it runs, on the same trace:
  reference          no fault, no planner          -> per-piece baseline
  noop/<det>         fault, detect only            -> what the 2020 system does
  rules/<det>        fault, C0 rule-based planner
with <det> = legacy (the three original detectors) or per_station.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.actions import describe
from ssac.intervention import Fault
from ssac.metrics import outcome, with_recovery
from ssac.calibration import alarm_rates
from ssac.planning import AdaptiveRulePlanner, CalibratedRulePlanner, NoOpPlanner, RuleBasedPlanner

ROOT = Path(__file__).resolve().parent.parent / "DataSets I4.0"

DEFAULT_SCENARIOS = [
    # station with a structural twin (L0_S3)
    Fault("L0_S2", factor=3.0, start_min=600.0),
    # high-volume station with no twin
    Fault("L3_S29", factor=3.0, start_min=600.0),
]

DETECTOR_SETS = {
    "legacy": ("legacy",),
    "per_station": ("legacy", "per_station"),
}


def run(model_path, data, faults, planner, detectors):
    model, errors = BusinessProcessModel.load(model_path)
    assert not errors, errors
    engine = SimulationEngine(model, data, faults=faults, planner=planner, detectors=detectors)
    engine.run()
    return engine


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", type=Path, default=ROOT / "bosch_pl_tm_model.pg")
    ap.add_argument("--events", type=Path, default=ROOT / "test_cases_0-100m.td")
    ap.add_argument("--calibration", type=Path, default=ROOT / "test_cases_100m-200m.td",
                    help="fault-free trace for C0 base rates; must differ from --events")
    ap.add_argument("--station")
    ap.add_argument("--factor", type=float, default=3.0)
    ap.add_argument("--start", type=float, default=600.0)
    ap.add_argument("--repair", type=float, default=60.0)
    ap.add_argument("--json", type=Path, help="write all outcomes as JSON")
    ap.add_argument("--show-actions", type=int, default=8, help="print first N decisions per run")
    args = ap.parse_args()

    scenarios = (
        [Fault(args.station, args.factor, args.start)] if args.station else DEFAULT_SCENARIOS
    )

    data = SimulationData.load(args.events)
    t0 = time.perf_counter()
    reference = run(args.model, data, [], None, ("legacy",))
    ref_lifetimes = dict(reference.lifetimes)
    print(f"reference run: {len(ref_lifetimes)} pieces, {time.perf_counter() - t0:.1f}s")

    assert args.calibration.resolve() != args.events.resolve(), "calibrate on a different trace"
    cal_data = SimulationData.load(args.calibration)
    rates = {}
    for det_name, det in DETECTOR_SETS.items():
        t0 = time.perf_counter()
        rates[det_name] = alarm_rates(args.model, cal_data, det)
        top = sorted(rates[det_name].items(), key=lambda kv: -kv[1])[:3]
        print(f"calibration [{det_name}] on {args.calibration.name}: {len(rates[det_name])} stations, "
              f"top {', '.join(f'{s} {r*60:.1f}/h' for s, r in top)}  ({time.perf_counter() - t0:.1f}s)")
    print()

    report = []
    for fault in scenarios:
        print(f"=== fault: {fault.station} x{fault.factor:g} from t={fault.start_min:g} min ===")
        outcomes = []
        for det_name, det in DETECTOR_SETS.items():
            planners = (
                NoOpPlanner(),
                RuleBasedPlanner(repair_min=args.repair),
                CalibratedRulePlanner(rates[det_name], repair_min=args.repair),
                AdaptiveRulePlanner(repair_min=args.repair),
            )
            for planner in planners:
                label = f"{planner.name}/{det_name}"
                t0 = time.perf_counter()
                eng = run(args.model, data, [fault], planner, det)
                o = outcome(label, eng, ref_lifetimes, [fault])
                outcomes.append(o)
                print(f"  {label:20s} {time.perf_counter() - t0:5.1f}s", end="")
                if not isinstance(planner, NoOpPlanner) and args.show_actions:
                    acc = [d for d in eng.decisions if d.accepted][: args.show_actions]
                    print("   " + "; ".join(f"t={d.t_min:.0f} {describe(d.action)}" for d in acc), end="")
                print()

        for det_name in DETECTOR_SETS:
            group = [o for o in outcomes if o.policy.endswith(det_name)]
            with_recovery(group, baseline=f"noop/{det_name}")

        print()
        hdr = (f"  {'policy':22s}{'excess(min)':>12}{'recov':>8}{'act lat':>9}"
               f"{'maint@F':>8}{'maint FP':>9}{'rr':>4}{'rr pcs':>8}{'wait(min)':>10}{'cong(min)':>10}")
        print(hdr)
        for o in outcomes:
            lat = f"{o.first_action_latency_min:.0f}" if o.first_action_latency_min is not None else "-"
            rec = f"{o.recovery:+.2f}" if o.recovery is not None else "-"
            print(f"  {o.policy:22s}{o.excess_delay_min:12.0f}{rec:>8}{lat:>9}"
                  f"{o.maintenances_on_fault:8d}{o.maintenances_false:9d}{o.reroutes:4d}"
                  f"{o.pieces_rerouted:8d}{o.maintenance_wait_min:10.0f}{o.congestion_extra_min:10.0f}")
        print()
        report.append({"fault": asdict(fault), "outcomes": [asdict(o) for o in outcomes]})

    if args.json:
        args.json.write_text(json.dumps(report, indent=2))
        print(f"wrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
