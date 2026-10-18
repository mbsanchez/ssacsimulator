#!/usr/bin/env python3
"""How the planners compare when a share of faults have a common cause,
from stored results only (held-out traces, per-station detector). No language
model is called. Writes results/prevalence.md.

A population of fault events in which a fraction pi are common-cause faults
(one fault on four stations at once, results/commoncause/) and 1 - pi are
single-station faults (results/processing/). Recovery of a planner over that
population = 1 - [(1 - pi) mean E24_single(planner) + pi mean E24_cc(planner)]
             / [(1 - pi) mean E24_single(noop) + pi mean E24_cc(noop)],
with means over the scenarios of each kind. Intervals: the two kinds are
resampled independently, each stratified by trace.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

from extra_analyses import e, keys, load

RES = Path(__file__).resolve().parent / "results"
PLANNERS = [("rules_adapt_ctx", "Adaptive + load veto"), ("rules_burst_ctx", "Burst ≥3 + load veto"), ("rules_burst2_ctx", "Burst ≥2 + load veto"),
            ("hybrid", "Hybrid, Qwen 7B"), ("hybrid:fable-5.1", "Hybrid, Fable 5.1")]
PIS = [0.0, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5]


def main() -> int:
    S, C = load(RES / "processing"), load(RES / "commoncause")
    nm = {"burst_ctx|size>=3": "rules_burst_ctx", "burst_ctx|size>=2": "rules_burst2_ctx"}
    for r in [*csv.DictReader((RES / "veto_controls" / "rows.csv").open()),
              *csv.DictReader((RES / "veto_controls2" / "rows.csv").open())]:
        if r["planner"] in nm and r["station"]:
            S[(r["trace"], r["station"], r["shape"], r["onset_idx"], nm[r["planner"]])] = r
    ks, kc = [k for k in keys(S) if k + ("noop",) in S], keys(C)

    def rec(p, a, b, pi):
        ms = lambda R, ks_, q: sum(e(R, k, q) for k in ks_) / len(ks_)
        num = (1 - pi) * ms(S, a, p) + pi * ms(C, b, p)
        den = (1 - pi) * ms(S, a, "noop") + pi * ms(C, b, "noop")
        return 1 - num / den

    def strat(ks_):
        st = {}
        for k in ks_:
            st.setdefault(k[0], []).append(k)
        return st
    ss, sc = strat(ks), strat(kc)
    rng = random.Random(0)
    draws = [([rng.choice(v) for v in ss.values() for _ in v], [rng.choice(v) for v in sc.values() for _ in v])
             for _ in range(4000)]
    out = ["# Prevalencia de fallos de causa común (trazas reservadas, detector por estación)\n",
           "π: fracción de los fallos que son de causa común (un fallo en cuatro estaciones a la vez). Recuperación neta a 24 h "
           "sobre una población de fallos con esa mezcla. IC 95 %: bootstrap de cada tipo de escenario, estratificado por traza.\n",
           "| π | " + " | ".join(n for _, n in PLANNERS) + " | Fable − adaptativa+carga [IC] | Fable − ráfaga≥3 [IC] | Fable − ráfaga≥2 [IC] |",
           "|---|" + "---|" * (len(PLANNERS) + 3)]
    for pi in PIS:
        cells = [f"{rec(p, ks, kc, pi):+.3f}" for p, _ in PLANNERS]
        for b in ("rules_adapt_ctx", "rules_burst_ctx", "rules_burst2_ctx"):
            d = rec("hybrid:fable-5.1", ks, kc, pi) - rec(b, ks, kc, pi)
            v = sorted(rec("hybrid:fable-5.1", a, c, pi) - rec(b, a, c, pi) for a, c in draws)
            cells.append(f"{d:+.3f} [{v[100]:+.3f}, {v[3899]:+.3f}]")
        out.append(f"| {pi:.2f} | " + " | ".join(cells) + " |")
    (RES / "prevalence.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
