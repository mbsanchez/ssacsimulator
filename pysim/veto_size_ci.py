#!/usr/bin/env python3
"""Veto rate by alarm size (robustness_analyses.py, part A) with 95% intervals
from a bootstrap over the clusters of trace x faulty station, and the
difference healthy - faulty per size. Replays the hybrids from the response
store; a cache miss is an error, no model is called. Writes
results/veto_size_ci.md."""

from __future__ import annotations

import os
import random
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from robustness_analyses import HELD_OUT, ROOT, SHAPES, STATIONS, _replay
from ssac import SimulationData
from ssac.onsets import onsets

RES = Path(__file__).resolve().parent / "results"
SIZES = [1, 2, 3, 4, 5]


def main() -> int:
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
    out = ["# Veto según el tamaño de la alarma, con intervalos por grupos traza × estación averiada\n",
           "Proporción de candidatos vetados; IC 95 % por bootstrap de los 24 grupos (4 000 remuestreos). "
           "Diferencia = sanas − averiada.\n",
           "| Modelo | tamaño | averiada [IC] | sanas [IC] | diferencia [IC] |", "|---|---|---|---|---|"]
    for b in ("fable", "qwen"):
        cl = defaultdict(list)          # (trace, faulty station) -> records
        for (bb, t, s, *_), recs in res:
            if bb == b:
                cl[(t, s)] += recs
        groups = list(cl.values())

        def share(rs, size, faulty):
            sel = [v for z, f, v in rs if min(z, 5) == size and f == faulty]
            return (sum(sel) / len(sel)) if sel else None
        rng = random.Random(0)
        draws = [[r for g in (rng.choice(groups) for _ in groups) for r in g] for _ in range(4000)]
        allr = [r for g in groups for r in g]
        for size in SIZES:
            cells = []
            for faulty in (True, False):
                v = sorted(x for x in (share(dr, size, faulty) for dr in draws) if x is not None)
                p = share(allr, size, faulty)
                cells.append(f"{p:.0%} [{v[int(.025 * len(v))]:.0%}, {v[int(.975 * len(v)) - 1]:.0%}]" if p is not None else "–")
            dd = sorted(h - f for f, h in ((share(dr, size, True), share(dr, size, False)) for dr in draws)
                        if f is not None and h is not None)
            p = share(allr, size, False) - share(allr, size, True)
            lab = str(size) if size < 5 else "≥5"
            out.append(f"| {b} | {lab} | {cells[0]} | {cells[1]} | {p:+.0%} [{dd[int(.025 * len(dd))]:+.0%}, "
                       f"{dd[int(.975 * len(dd)) - 1]:+.0%}] |")
    (RES / "veto_size_ci.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
