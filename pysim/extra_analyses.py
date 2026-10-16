#!/usr/bin/env python3
"""Analyses registered in advance (results/dev_log.md,
2026-10-15), from stored results only. No language model is called.
Writes results/extra_analyses.md.

  A  scenarios without cost, recovery on costed scenarios, and the split of the
     24-h delay into the fault's own delay and the cost of the actions
     (offline replay of the held-out runs, results/replay/);
  B  sensitivity to a mild fault (k = 1.5) with the LLM hybrids;
  C  ablations of the veto: no burst cue; per-station detector with the v2
     alarm text; legacy detector with the v3 alarm text;
  D  validation on five new traces, everything frozen.
"""

from __future__ import annotations

import itertools
import random
from pathlib import Path

from scipy.stats import wilcoxon

from stats import STRICT, read_all

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
SHAPES = ["step", "intermittent", "drift"]


def load(d: Path) -> dict:
    return {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): r
            for r in read_all(d / "llm_sweep_rows.csv") if r["station"]}


def e(R, k, p, col="excess_h24_min"):
    return float(R[k + (p,)][col])


def keys(R):
    return sorted({k[:4] for k in R})


def pooled(R, p, ks):
    return 1 - sum(e(R, k, p) for k in ks) / sum(e(R, k, "noop") for k in ks)


def boot(f, ks, n=10_000, two_level=False):
    traces = sorted({k[0] for k in ks})
    st = {t: [k for k in ks if k[0] == t] for t in traces}
    rng = random.Random(0)
    out = []
    for _ in range(n):
        if two_level:
            s = []
            for t in (rng.choice(traces) for _ in traces):
                s += [rng.choice(st[t]) for _ in st[t]]
        else:
            s = [rng.choice(st[t]) for t in traces for _ in st[t]]
        out.append(f(s))
    out.sort()
    return out[int(0.025 * n)], out[int(0.975 * n) - 1]


def compare(RA, a, RB, b, ks):
    """Recovery of A minus recovery of B, paired over the same scenarios."""
    def d(s):
        return (sum(e(RB, k, b) for k in s) - sum(e(RA, k, a) for k in s)) / sum(e(RA, k, "noop") for k in s)
    traces = sorted({k[0] for k in ks})
    st = {t: [k for k in ks if k[0] == t] for t in traces}
    lo, hi = boot(d, ks)
    lo2, hi2 = boot(d, ks, two_level=True)
    draws = [d([k for t in c for k in st[t]]) for c in itertools.product(traces, repeat=len(traces))]
    diffs = [e(RA, k, a) - e(RB, k, b) for k in ks if e(RA, k, a) != e(RB, k, b)]
    return {"delta": d(ks), "ci": (lo, hi), "ci2": (lo2, hi2), "better": sum(x < 0 for x in diffs),
            "worse": sum(x > 0 for x in diffs), "p": wilcoxon(diffs).pvalue if len(diffs) > 5 else float("nan"),
            "draws_le0": sum(x <= 0 for x in draws), "draws": len(draws),
            "per_trace": [d(st[t]) for t in traces]}


def fmt_cmp(name, c):
    pt = ", ".join(f"{x:+.3f}" for x in c["per_trace"])
    return (f"| {name} | {c['delta']:+.3f} | [{c['ci'][0]:+.3f}, {c['ci'][1]:+.3f}] | [{c['ci2'][0]:+.3f}, {c['ci2'][1]:+.3f}] "
            f"| {c['better']} / {c['worse']} | {c['p']:.2g} | {c['draws_le0']}/{c['draws']} | {pt} |")


CMP_HEAD = ["| Comparación (A − B) | Δ recuperación 24 h | IC 95 % estratificado | IC 95 % dos niveles | A mejor / peor "
            "| p Wilcoxon | extracciones de trazas con Δ ≤ 0 | Δ por traza |", "|---|---|---|---|---|---|---|---|"]


def planner_table(R, planners):
    ks = keys(R)
    pos = [k for k in ks if e(R, k, "noop") > 0]
    out = ["| Planificador | recuperación 24 h [IC 95 %] | sobre escenarios con coste | "
           + " | ".join(SHAPES) + " |", "|---|---|---|---|---|---|"]
    for p in planners:
        if not all(k + (p,) in R for k in ks):
            continue
        lo, hi = boot(lambda s: pooled(R, p, s), ks, n=4000)
        out.append(f"| {p} | {pooled(R, p, ks):+.3f} [{lo:+.3f}, {hi:+.3f}] | {pooled(R, p, pos):+.3f} | "
                   + " | ".join(f"{pooled(R, p, [k for k in ks if k[2] == s]):+.3f}" for s in SHAPES) + " |")
    return out


def vetoes(d):
    C = [c for c in read_all(d / "llm_sweep_calls.csv") if c["planner"] == "hybrid:fable-5.1"]
    v = [c for c in C if set(c["eligible"].split()) - set(c["acted_on"].split())]
    return len(C), len(v), sum(bool(STRICT.search(c["reason"])) for c in v)


def main() -> int:
    out = ["# Análisis adicionales (diseño v2, detector por estación salvo indicación)\n"]
    planners = ["rules_cal", "rules_adapt", "rules_adapt_ctx", "rules_twin", "rules_cal_rt", "rules_adapt_ctx_rt",
                "llm_c1", "llm_c2", "hybrid", "llm_c1:fable-5.1", "llm_c2:fable-5.1", "hybrid:fable-5.1"]

    # A
    R = load(RES / "replay")
    ks = keys(R)
    zero = [k for k in ks if e(R, k, "noop") == 0]
    pos = [k for k in ks if k not in zero]
    noexp = sum(int(R[k + ("noop",)]["exposure_h24"]) == 0 for k in zero)
    out += ["## A. Escenarios sin coste y descomposición del retraso (trazas reservadas)\n",
            f"{len(zero)} de {len(ks)} escenarios tienen coste nulo sin acción en las 24 h: {noexp} porque la estación "
            "averiada no tiene ninguna transición en la ventana y el resto porque todas caen en la fase apagada de un fallo "
            "intermitente. Por traza: " + ", ".join(f"{t[11:-3]} {sum(1 for k in zero if k[0] == t)}"
                                                    for t in sorted({k[0] for k in ks}))
            + "; por forma: " + ", ".join(f"{s} {sum(1 for k in zero if k[2] == s)}" for s in SHAPES) + ".\n",
            "Fallo restante y coste de las acciones: fracciones del coste sin acción, sobre los escenarios con coste "
            "(recuperación = 1 − fallo − acciones).\n",
            "| Planificador | recuperación, todos | recuperación, con coste [IC 95 %] | fallo restante | coste de las acciones "
            "| coste de las acciones en escenarios sin coste (min-pieza) |", "|---|---|---|---|---|---|"]
    den = sum(e(R, k, "noop") for k in pos)
    for p in planners:
        if not all(k + (p,) in R for k in ks):
            continue
        lo, hi = boot(lambda s: pooled(R, p, s), pos, n=4000)
        fl = sum(e(R, k, p, "fault_h24_min") for k in pos) / den
        ac = sum(e(R, k, p, "actions_h24_min") for k in pos) / den
        az = sum(e(R, k, p, "actions_h24_min") for k in zero)
        out.append(f"| {p} | {pooled(R, p, ks):+.3f} | {pooled(R, p, pos):+.3f} [{lo:+.3f}, {hi:+.3f}] | {fl:.3f} | {ac:.3f} "
                   f"| {az:,.0f} |")
    out += ["\nSobre los escenarios con coste:\n"] + CMP_HEAD
    for b in ("rules_adapt_ctx", "hybrid", "llm_c2:fable-5.1"):
        out.append(fmt_cmp(f"hybrid:fable-5.1 − {b}", compare(R, "hybrid:fable-5.1", R, b, pos)))

    # B
    S = load(RES / "sens_k1.5")
    out += ["\n## B. Sensibilidad: fallo leve (k = 1,5), trazas reservadas\n"]
    out += planner_table(S, planners)
    out += [""] + CMP_HEAD
    for b in ("rules_adapt_ctx", "hybrid"):
        out.append(fmt_cmp(f"hybrid:fable-5.1 − {b}", compare(S, "hybrid:fable-5.1", S, b, keys(S))))

    # C
    M = load(RES / "processing")
    L = load(RES)
    out += ["\n## C. Ablaciones del veto (híbrido Fable, trazas reservadas)\n",
            "| Detector | texto de alarmas | pista de ráfagas | recuperación 24 h [IC 95 %] | llamadas | con veto | vetos que citan ráfagas |",
            "|---|---|---|---|---|---|---|"]
    rows = [("por estación", "v3", "sí", M, RES / "processing"), ("por estación", "v2", "sí", load(RES / "ablation_v2text"), RES / "ablation_v2text"),
            ("por estación", "v3", "no", load(RES / "ablation_nocue"), RES / "ablation_nocue"),
            ("heredado", "v2", "sí", L, RES), ("heredado", "v3", "sí", load(RES / "ablation_legacy_v3text"), RES / "ablation_legacy_v3text")]
    for det, txt, cue, D, path in rows:
        kk = keys(D)
        lo, hi = boot(lambda s: pooled(D, "hybrid:fable-5.1", s), kk, n=4000)
        n, nv, nb = vetoes(path)
        out.append(f"| {det} | {txt} | {cue} | {pooled(D, 'hybrid:fable-5.1', kk):+.3f} [{lo:+.3f}, {hi:+.3f}] | {n} | {nv} | "
                   f"{nb / max(nv, 1):.0%} |")
    out += [""] + CMP_HEAD
    out.append(fmt_cmp("con pista − sin pista (por estación)", compare(M, "hybrid:fable-5.1", load(RES / "ablation_nocue"),
                                                                        "hybrid:fable-5.1", keys(M))))
    out.append(fmt_cmp("texto v3 − texto v2 (por estación)", compare(M, "hybrid:fable-5.1", load(RES / "ablation_v2text"),
                                                                      "hybrid:fable-5.1", keys(M))))
    out.append(fmt_cmp("texto v2 − texto v3 (heredado)", compare(L, "hybrid:fable-5.1", load(RES / "ablation_legacy_v3text"),
                                                                  "hybrid:fable-5.1", keys(L))))

    # D
    N = load(RES / "newtraces")
    kn = keys(N)
    out += ["\n## D. Validación en cinco trazas nuevas (todo congelado)\n",
            f"{len(kn)} escenarios con fallo; {sum(1 for k in kn if e(N, k, 'noop') == 0)} sin coste.\n"]
    out += planner_table(N, planners)
    out += [""] + CMP_HEAD
    for b in ("rules_cal_rt", "rules_cal", "rules_adapt_ctx", "rules_adapt_ctx_rt", "hybrid"):
        out.append(fmt_cmp(f"hybrid:fable-5.1 − {b}", compare(N, "hybrid:fable-5.1", N, b, kn)))
    n, nv, nb = vetoes(RES / "newtraces")
    out.append(f"\nVetos del híbrido Fable en las trazas nuevas: {nv} de {n} llamadas; {nb / max(nv, 1):.0%} citan ráfagas.")

    (RES / "extra_analyses.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
