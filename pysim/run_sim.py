#!/usr/bin/env python3
"""Run the headless SSAC simulation and report detections.

    python run_sim.py --model "DataSets I4.0/bosch_pl_tm_model.pg" \
                      --events "DataSets I4.0/test_cases_0-100m.td"

Options worth knowing:
  --all-events   read the whole .td file instead of the original's first 100k
  --speed N      UI speed factor; changes the clock granularity (default 150)
  --jsonl PATH   write one JSON object per detection
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from ssac import BusinessProcessModel, SimulationData, SimulationEngine
from ssac.events import DATA_INITIAL_CHUNK_LENGTH


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, type=Path, help="process graph (.pg)")
    ap.add_argument("--events", required=True, type=Path, help="event data (.td)")
    ap.add_argument("--speed", type=int, default=150)
    ap.add_argument("--all-events", action="store_true",
                    help="read the whole file (the Qt app stops at 100k)")
    ap.add_argument("--max-ticks", type=int, default=None)
    ap.add_argument("--jsonl", type=Path, default=None)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    model, errors = BusinessProcessModel.load(args.model)
    if errors:
        print(f"model loaded with {len(errors)} error(s):", file=sys.stderr)
        for e in errors[:10]:
            print(f"  - {e}", file=sys.stderr)
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more", file=sys.stderr)

    if not args.quiet:
        print(f"process        : {model.process_name}")
        print(f"actors         : {len(model.actors)}")
        print(f"transition sets: {len(model.edges)}")
        print(f"edges          : {sum(len(v) for v in model.edges.values())}")
        print(f"  visible      : {sum(1 for v in model.edges.values() for e in v.values() if e.show)}")
        print(f"throughout time: {model.throughout_time} min")
        print(f"total cases    : {model.total_cases}")
        print(f"begin / end    : {model.begin_actor} / {', '.join(model.end_actors)}")
        print()

    max_events = None if args.all_events else DATA_INITIAL_CHUNK_LENGTH
    data = SimulationData.load(args.events, max_events=max_events)
    rep = data.report

    if not args.quiet:
        print(f"declared events: {rep.declared_events}")
        print(f"time window    : [{rep.min_time}, {rep.max_time}] min")
        print(f"rows read/kept : {rep.rows_read} / {rep.rows_kept}")
        if rep.rows_bad_shape:
            print(f"  bad shape    : {rep.rows_bad_shape}")
        if rep.rows_skipped_unparsable:
            print(f"  skipped      : {rep.rows_skipped_unparsable}")
        if rep.rows_duration_defaulted:
            print(f"  duration->0  : {rep.rows_duration_defaulted}")
        if rep.rows_start_defaulted:
            print(f"  start->0     : {rep.rows_start_defaulted}")
        print()

    engine = SimulationEngine(model, data, speed=args.speed)
    stats = engine.run(max_ticks=args.max_ticks)

    counts = engine.detection_counts()
    print("=== detections ===")
    for name, n in counts.items():
        print(f"{name:20s} {n}")
    print(f"{'TOTAL':20s} {len(engine.detections)}")
    print()
    print("=== run stats ===")
    print(f"ticks              : {stats.ticks}")
    print(f"events processed   : {stats.events_processed}")
    print(f"pieces entered     : {stats.pieces_entered}")
    print(f"pieces completed   : {stats.pieces_completed}")
    print(f"still in system    : {stats.final_pieces_in_system}")
    print(f"final sim time     : {stats.final_sim_time_ms / 60000.0:.2f} min")
    if stats.unknown_actor or stats.unknown_edge:
        print(f"unknown actor/edge : {stats.unknown_actor} / {stats.unknown_edge}")
    if stats.clock_regressions:
        print(f"clock regressions  : {stats.clock_regressions}  (non-monotonic input)")

    if args.jsonl:
        with args.jsonl.open("w", encoding="utf-8") as fh:
            for d in engine.detections:
                fh.write(json.dumps({
                    "type": d.type.value,
                    "sim_time_min": round(d.sim_time_min, 6),
                    "event_index": d.event_index,
                    "detail": d.detail,
                }) + "\n")
        print(f"\nwrote {len(engine.detections)} detections to {args.jsonl}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
