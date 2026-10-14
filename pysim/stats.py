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

p-values are reported raw and Holm-adjusted within each table; each table
holds exactly the comparisons of one block of Table 3 in the paper. Effect
size: matched-pairs rank-biserial correlation r = (W+ - W-) / (W+ + W-), with
W+ the rank sum of scenarios where A loses less time (r = 1: A better in
every scenario).

Also: recovery per trace, latency medians, sensitivity of the specific-hit
window, and an explicit keyword coding of the reasons the hybrid planners
give for their vetoes.

    python stats.py
    python stats.py --a llm_c2:fable-5.1 --b rules_adapt_ctx rules_adapt
"""

from __future__ import annotations

import argparse
import csv
import random
import re
from pathlib import Path

from scipy.stats import rankdata, wilcoxon

HERE = Path(__file__).resolve().parent
ROWS = HERE / "results" / "llm_sweep_rows.csv"
CALLS = HERE / "results" / "llm_sweep_calls.csv"
OUT = HERE / "results" / "stats.md"
EXCESS = "excess_h24_min"   # design v2: primary horizon; --horizon 8 switches to the 8 h one
TWINS = {"L0_S2", "L0_S4", "L0_S6", "L3_S35"}
SHAPES = ["step", "intermittent", "drift"]


def read_all(path: Path) -> list[dict]:
    """Rows of a results directory plus those of its LLM sub-runs (e.g. qwen/),
    which were written by separate processes."""
    out = list(csv.DictReader(path.open()))
    have = {x["planner"] for x in out}
    for name in ("qwen", "qwen_v2"):      # the only LLM sub-runs (separate processes)
        sub = path.parent / name / path.name
        if sub.exists():
            out += [r for r in csv.DictReader(sub.open()) if r["planner"] not in have]
    return out


def load():
    rows = read_all(ROWS)
    by = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): r for r in rows if r["station"]}
    keys = sorted({k[:4] for k in by})
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
    ex = lambda k, p: float(by[k + (p,)][EXCESS])
    keys = [k for k in keys if k + (a,) in by and k + (b,) in by and k + ("noop",) in by]
    d = [ex(k, a) - ex(k, b) for k in keys]
    nonzero = [x for x in d if x != 0]
    p = wilcoxon(nonzero).pvalue if len(nonzero) >= 6 else float("nan")
    ranks = rankdata([abs(x) for x in nonzero])
    w_a = sum(r for r, x in zip(ranks, nonzero) if x < 0)
    rb = (2 * w_a - sum(ranks)) / sum(ranks) if nonzero else float("nan")
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
            "p": p, "r": rb, "delta": delta, "lo": lo, "hi": hi}


def latency(by, keys, a, b):
    def lat(k, p):
        v = by[k + (p,)]["first_action_latency_min"]
        return float(v) if v not in ("", "None") else None
    pairs = [(lat(k, a), lat(k, b)) for k in keys
             if k + (a,) in by and k + (b,) in by and lat(k, a) is not None and lat(k, b) is not None]
    d = sorted(x - y for x, y in pairs)
    nonzero = [x for x in d if x != 0]
    p = wilcoxon(nonzero).pvalue if len(nonzero) >= 6 else float("nan")
    med = lambda xs: sorted(xs)[len(xs) // 2] if xs else float("nan")
    marg = lambda q: [lat(k, q) for k in keys if k + (q,) in by and lat(k, q) is not None]
    return {"n": len(pairs), "a_sooner": sum(x < 0 for x in d), "b_sooner": sum(x > 0 for x in d),
            "median": med(d), "p": p, "a_med": med([x for x, _ in pairs]), "b_med": med([y for _, y in pairs]),
            "p10": d[len(d) // 10] if d else float("nan"), "p75": d[3 * len(d) // 4] if d else float("nan"),
            "a_n": len(marg(a)), "a_all": med(marg(a)), "b_n": len(marg(b)), "b_all": med(marg(b))}


def table(results: list[tuple[str, dict]]) -> list[str]:
    adj = holm([r["p"] for _, r in results])
    out = ["| Comparación | n | A mejor | B mejor | p (Wilcoxon) | p Holm | r | Δ recuperación agregada | IC 95% |",
           "|---|---|---|---|---|---|---|---|---|"]
    for (name, r), pa in zip(results, adj):
        out.append(f"| {name} | {r['n']} | {r['a_better']} | {r['b_better']} | {r['p']:.3g} | {pa:.3g} | {r['r']:+.2f} | "
                   f"{r['delta']:+.3f} | [{r['lo']:+.3f}, {r['hi']:+.3f}] |")
    return out


def _maint(r):
    out = []
    for tok in (r.get("maint_log") or "").split():
        st, t = tok.rsplit("@", 1)
        out.append((st, float(t)))
    return out


def hits_section(by, keys) -> list[str]:
    """Acts on the faulty station at all, and specific hits for several windows."""
    rows = read_all(ROWS)
    ff = {(r["trace"], r["planner"]): _maint(r) for r in rows if not r["station"]}
    planners = [p for p in ["rules_cal", "rules_adapt", "rules_adapt_ctx", "rules_twin", "llm_c1", "llm_c2", "hybrid",
                            "llm_c2:fable-5.1", "hybrid:fable-5.1"] if any(k + (p,) in by for k in keys)]
    windows = [60, 120, 240]

    def spec(r, w):
        t0 = float(r["fault_start_min"])
        u = [t for st, t in ff[(r["trace"], r["planner"])] if st == r["station"]]
        return any(st == r["station"] and t >= t0 and all(abs(t - x) > w for x in u) for st, t in _maint(r))

    out = ["\n## Aciertos sobre la estación averiada\n",
           "Actúa: al menos una reparación de la estación averiada. Específico (±w min): además, la misma política sin fallo "
           "no la reparó en ±w min. Por forma: actúa / específico (±120).\n",
           "| Planificador | actúa | " + " | ".join(f"específico ±{w}" for w in windows) + " | "
           + " | ".join(SHAPES) + " |", "|---|---|" + "---|" * (len(windows) + len(SHAPES))]
    for p in planners:
        sel = [by[k + (p,)] for k in keys if k + (p,) in by]
        acts = sum(int(r["maintenances_on_fault"]) > 0 for r in sel)
        cells = [f"{sum(spec(r, w) for r in sel)}/{len(sel)}" for w in windows]
        shp = []
        for s_ in SHAPES:
            ss = [r for r in sel if r["shape"] == s_]
            shp.append(f"{sum(int(r['maintenances_on_fault']) > 0 for r in ss)} / {sum(spec(r, 120) for r in ss)}")
        out.append(f"| {p} | {acts}/{len(sel)} | " + " | ".join(cells) + " | " + " | ".join(shp) + " |")
    return out


# Explicit coding of veto reasons. STRICT: the line-wide / shared-burst
# argument itself. BROAD additionally matches any mention of sharing or
# upstream causes, which the 7B model often uses while still concluding
# that the station is degraded.
STRICT = re.compile(r"burst|line-wide|line wide|common (upstream )?cause|systemic", re.I)
BROAD = re.compile(r"burst|line-wide|line wide|common|shared|simultaneous|many stations|all stations|systemic|cascade|upstream", re.I)


def veto_section() -> list[str]:
    if not CALLS.exists():
        return []
    calls = read_all(CALLS)
    out = ["\n## Razones de los vetos del híbrido\n",
           f"Veto: llamada en la que al menos una estación elegible no recibe acción. Estricto: `{STRICT.pattern}`. "
           f"Amplio: `{BROAD.pattern}`. Insensible a mayúsculas.\n",
           "| Planificador | llamadas | con veto | estricto | amplio | vetos de la estación averiada | de ellos, estricto |",
           "|---|---|---|---|---|---|---|"]
    for p in ["hybrid", "hybrid:fable-5.1"]:
        cs = [c for c in calls if c["planner"] == p]
        if not cs:
            continue
        v = [c for c in cs if set(c["eligible"].split()) - set(c["acted_on"].split())]
        vf = [c for c in v if c["station"] in set(c["eligible"].split()) - set(c["acted_on"].split())]
        n = lambda xs, rx: sum(bool(rx.search(c["reason"])) for c in xs)
        out.append(f"| {p} | {len(cs)} | {len(v)} | {n(v, STRICT)} ({n(v, STRICT) / len(v):.1%}) | "
                   f"{n(v, BROAD)} ({n(v, BROAD) / len(v):.1%}) | {len(vf)} | {n(vf, STRICT)} |")
    out += ["\n## Caché de respuestas\n", "| Planificador | llamadas | servidas desde caché |", "|---|---|---|"]
    for p in sorted({c["planner"] for c in calls}):
        cs = [c for c in calls if c["planner"] == p]
        hit = sum(c["cached"] in ("True", "1", "true") for c in cs)
        out.append(f"| {p} | {len(cs)} | {hit} ({hit / len(cs):.0%}) |")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a", default="llm_c2:fable-5.1")
    ap.add_argument("--b", nargs="+", default=["rules_adapt_ctx", "rules_adapt", "rules_cal", "llm_c2", "llm_c1:fable-5.1"])
    ap.add_argument("--main-b", default="rules_adapt_ctx", help="comparison broken down by subgroup")
    ap.add_argument("--dir", type=Path, default=None, help="results directory (default: results/)")
    ap.add_argument("--horizon", type=int, choices=[8, 24], default=24, help="horizon in hours after the onset")
    args = ap.parse_args()
    global EXCESS, OUT, ROWS, CALLS
    if args.dir is not None:
        ROWS, CALLS, OUT = args.dir / "llm_sweep_rows.csv", args.dir / "llm_sweep_calls.csv", args.dir / "stats.md"
    if args.horizon == 8:
        EXCESS, OUT = "excess_h8_min", OUT.with_name("stats_h8.md")

    by, keys = load()
    a = args.a
    present = {k[4] for k in by}
    args.b = [b for b in args.b if b in present]
    out = [f"# Estadística pareada — A = `{a}`\n",
           "Diseño v2. Escenarios con fallo de las trazas reservadas (3 inicios cada uno), pareados por (traza, estación, forma, inicio); retraso en exceso dentro del horizonte tras el inicio. "
           "Δ > 0: A recupera más. Wilcoxon sobre el retraso en exceso por escenario. IC por bootstrap "
           "estratificado por traza (10 000 remuestras, semilla 0). p Holm: ajuste por comparaciones múltiples "
           "dentro de cada tabla.\n",
           "## Frente a cada planificador\n"]
    out += table([(f"{a} vs {b}", compare(by, keys, a, b)) for b in args.b])

    b = args.main_b
    out += [f"\n## Por subgrupo, frente a `{b}`\n"]
    groups = [(f"fallo {s}", [k for k in keys if k[2] == s]) for s in SHAPES]
    out += table([(name, compare(by, ks, a, b)) for name, ks in groups])
    out += ["\nCon y sin gemela (familia aparte):\n"]
    groups = [("con gemela", [k for k in keys if k[1] in TWINS]),
              ("sin gemela", [k for k in keys if k[1] not in TWINS])]
    out += table([(name, compare(by, ks, a, b)) for name, ks in groups])
    out += ["\nPor traza (exploratorio, sin ajuste):\n"]
    traces = sorted({k[0] for k in keys})
    out += table([(f"traza {t.split('_')[2][:-3]}", compare(by, [k for k in keys if k[0] == t], a, b)) for t in traces])
    out += ["\nPor traza y forma (Δ recuperación agregada; A mejor / n):\n",
            "| Traza | " + " | ".join(SHAPES) + " |", "|---|---|---|---|"]
    for t in traces:
        cells = []
        for s_ in SHAPES:
            r = compare(by, [k for k in keys if k[0] == t and k[2] == s_], a, b, n_boot=1)
            cells.append(f"{r['delta']:+.3f} ({r['a_better']}/{r['n']})")
        out.append(f"| {t.split('_')[2][:-3]} | " + " | ".join(cells) + " |")

    out += ["\n## Latencia de la primera acción sobre la estación averiada\n",
            "Solo escenarios donde ambos actúan sobre ella. Diferencia < 0: A actúa antes.\n",
            "Latencia desde el inicio del fallo. Medianas marginales: sobre todos los escenarios en que cada uno actúa.\n",
            "| Comparación | pares | A antes | B antes | mediana A / B en los pares (min) | diferencia: p10 / mediana / p75 | p (Wilcoxon) | marginal A (n) | marginal B (n) |",
            "|---|---|---|---|---|---|---|---|---|"]
    for bb in args.b:
        r = latency(by, keys, a, bb)
        out.append(f"| {a} vs {bb} | {r['n']} | {r['a_sooner']} | {r['b_sooner']} | {r['a_med']:,.0f} / {r['b_med']:,.0f} | "
                   f"{r['p10']:+,.0f} / {r['median']:+,.0f} / {r['p75']:+,.0f} | {r['p']:.3g} | "
                   f"{r['a_all']:,.0f} ({r['a_n']}) | {r['b_all']:,.0f} ({r['b_n']}) |")

    out += hits_section(by, keys) + veto_section()

    OUT.write_text("\n".join(out) + "\n")
    print("\n".join(out))
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
