#!/usr/bin/env python3
"""Paired statistics for the held-out evaluation (results/llm_sweep_rows.csv).

No LLM calls: works on stored results only. Writes results/stats.md.

For each comparison A vs B over the fault scenarios (same trace, station and
fault shape for both planners):
  * per-scenario: Wilcoxon signed-rank test on excess delay (A - B), and the
    number of scenarios where A loses less time than B;
  * aggregate: difference in pooled recovery, with a 95% bootstrap interval
    stratified by trace (scenarios on the same trace share alarms, so they
    are resampled within their trace), 10 000 resamples, fixed seed.
Subgroups (fault shape, twin / no twin) repeat the same analysis. Latency is
compared only on scenarios where both planners acted on the faulty station.

p-values are reported raw and Holm-adjusted within each table.

    python stats.py
    python stats.py --a llm_c2:fable-5.1 --b rules_adapt_ctx rules_adapt
"""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
ROWS = HERE / "results" / "llm_sweep_rows.csv"
OUT = HERE / "results" / "stats.md"
TWINS = {"L0_S2", "L0_S4", "L0_S6", "L3_S35"}
SHAPES = ["step", "intermittent", "drift"]


def load():
    rows = list(csv.DictReader(ROWS.open()))
    by = {(r["trace"], r["station"], r["shape"], r["planner"]): r for r in rows if r["station"]}
    keys = sorted({k[:3] for k in by})
    return by, keys


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj = [0.0] * len(ps)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = running
    return adj


def compare(by, keys, a, b, n_boot=10_000, seed=0):
    ex = lambda k, p: float(by[k + (p,)]["excess_delay_min"])
    keys = [k for k in keys if k + (a,) in by and k + (b,) in by and k + ("noop",) in by]
    d = [ex(k, a) - ex(k, b) for k in keys]
    nonzero = [x for x in d if x != 0]
    p = wilcoxon(nonzero).pvalue if len(nonzero) >= 6 else float("nan")
    noop = {k: ex(k, "noop") for k in keys}
    den = sum(noop.values())
    delta = (sum(ex(k, b) for k in keys) - sum(ex(k, a) for k in keys)) / den if den else float("nan")

    traces = sorted({k[0] for k in keys})
    strata = {t: [k for k in keys if k[0] == t] for t in traces}
    rng = random.Random(seed)
    boots = []
    for _ in range(n_boot):
        s = [rng.choice(strata[t]) for t in traces for _ in strata[t]]
        dd = sum(noop[k] for k in s)
        if dd:
            boots.append((sum(ex(k, b) for k in s) - sum(ex(k, a) for k in s)) / dd)
    boots.sort()
    lo, hi = boots[int(0.025 * len(boots))], boots[int(0.975 * len(boots)) - 1]
    return {"n": len(keys), "a_better": sum(x < 0 for x in d), "b_better": sum(x > 0 for x in d),
            "p": p, "delta": delta, "lo": lo, "hi": hi}


def latency(by, keys, a, b):
    def lat(k, p):
        v = by[k + (p,)]["first_action_latency_min"]
        return float(v) if v not in ("", "None") else None
    pairs = [(lat(k, a), lat(k, b)) for k in keys
             if k + (a,) in by and k + (b,) in by and lat(k, a) is not None and lat(k, b) is not None]
    d = sorted(x - y for x, y in pairs)
    nonzero = [x for x in d if x != 0]
    p = wilcoxon(nonzero).pvalue if len(nonzero) >= 6 else float("nan")
    return {"n": len(pairs), "a_sooner": sum(x < 0 for x in d), "b_sooner": sum(x > 0 for x in d),
            "median": d[len(d) // 2] if d else float("nan"), "p": p}


def table(results: list[tuple[str, dict]]) -> list[str]:
    adj = holm([r["p"] for _, r in results])
    out = ["| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | Δ recuperación agregada | IC 95% |",
           "|---|---|---|---|---|---|---|---|"]
    for (name, r), pa in zip(results, adj):
        out.append(f"| {name} | {r['n']} | {r['a_better']} | {r['b_better']} | {r['p']:.3g} | {pa:.3g} | "
                   f"{r['delta']:+.3f} | [{r['lo']:+.3f}, {r['hi']:+.3f}] |")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", default="llm_c2:fable-5.1")
    ap.add_argument("--b", nargs="+", default=["rules_adapt_ctx", "rules_adapt", "rules_cal", "llm_c2", "hybrid:fable-5.1"])
    ap.add_argument("--main-b", default="rules_adapt_ctx", help="comparison broken down by subgroup")
    args = ap.parse_args()

    by, keys = load()
    a = args.a
    out = [f"# Estadística pareada — A = `{a}`\n",
           "Escenarios con fallo de las trazas reservadas, pareados por (traza, estación, forma del fallo). "
           "Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap "
           "estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples "
           "dentro de cada tabla.\n",
           "## Frente a cada planificador\n"]
    out += table([(f"{a} vs {b}", compare(by, keys, a, b)) for b in args.b])

    b = args.main_b
    out += [f"\n## Por subgrupo, frente a `{b}`\n"]
    groups = [(f"fallo {s}", [k for k in keys if k[2] == s]) for s in SHAPES]
    groups += [("con gemela", [k for k in keys if k[1] in TWINS]),
               ("sin gemela", [k for k in keys if k[1] not in TWINS])]
    out += table([(name, compare(by, ks, a, b)) for name, ks in groups])

    out += ["\n## Latencia de la primera acción sobre la estación averiada\n",
            "Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.\n",
            "| Comparación | pares | A antes | B antes | mediana de la diferencia (min) | p (Wilcoxon) |",
            "|---|---|---|---|---|---|"]
    for bb in args.b:
        r = latency(by, keys, a, bb)
        out.append(f"| {a} vs {bb} | {r['n']} | {r['a_sooner']} | {r['b_sooner']} | {r['median']:+.0f} | {r['p']:.3g} |")

    OUT.write_text("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
