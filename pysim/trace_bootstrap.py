#!/usr/bin/env python3
"""Uncertainty with the trace as the unit of resampling (no language model is called).

stats.py resamples scenarios within each held-out trace, which treats the
three traces as fixed. Here the trace is the cluster:

  exact cluster bootstrap   all 27 ordered draws of 3 traces with replacement
                            (equally likely), pooled-recovery difference on each;
  two-level bootstrap       draw 3 traces with replacement, then scenarios
                            within each drawn trace (10 000 resamples, seed 0);
  leave one trace out       the difference on each pair of traces.

    python trace_bootstrap.py      # writes results/trace_bootstrap.md
"""

from __future__ import annotations

import csv
import itertools
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
PAIRS = [("llm_c2:fable-5.1", "rules_adapt_ctx"), ("hybrid:fable-5.1", "rules_adapt_ctx"),
         ("hybrid", "rules_adapt_ctx"), ("hybrid:fable-5.1", "llm_c2:fable-5.1"), ("llm_c2", "rules_adapt_ctx")]
SHAPES = [("todas", None), ("escalón", "step"), ("intermitente", "intermittent"), ("deriva", "drift")]


def main() -> int:
    import sys
    from stats import read_all
    res = Path(sys.argv[1]) if len(sys.argv) > 1 else RESULTS
    rows = read_all(res / "llm_sweep_rows.csv")
    ex = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): float(r["excess_h24_min"])
          for r in rows if r["station"]}
    traces = sorted({k[0] for k in ex})

    def keys(trace, shape):
        return sorted({k[:4] for k in ex if k[0] == trace and (shape is None or k[2] == shape)})

    def delta(sample, a, b):
        den = sum(ex[k + ("noop",)] for k in sample)
        return (sum(ex[k + (b,)] for k in sample) - sum(ex[k + (a,)] for k in sample)) / den

    out = ["# Incertidumbre con la traza como unidad de remuestreo\n",
           "Diseño v2. Δ = recuperación agregada a 24 h (A) − ídem (B) en las trazas reservadas. "
           "«Exacto»: las 27 extracciones ordenadas de 3 trazas con reemplazo; se dan el mínimo, el máximo y la fracción con Δ ≤ 0. "
           "«Dos niveles»: trazas con reemplazo y luego escenarios dentro de cada traza, 10 000 remuestras, semilla 0, IC 95 % percentil. "
           "Con tres conglomerados ningún intervalo es fiable; el objetivo es mostrar cuánto se ensancha respecto del bootstrap estratificado de `stats.md`.\n",
           "| A | B | Formas | Δ | exacto: mín – máx | exacto: P(Δ ≤ 0) | dos niveles: IC 95 % | sin 100m-200m | sin 200m-300m | sin 500m-600m |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for a, b in PAIRS:
        if not any(k[-1] == a for k in ex):
            continue
        for sname, shape in SHAPES:
            per = {t: keys(t, shape) for t in traces}
            full = [k for t in traces for k in per[t]]
            d = delta(full, a, b)
            draws = [delta([k for t in combo for k in per[t]], a, b) for combo in itertools.product(traces, repeat=3)]
            rng = random.Random(0)
            boot = []
            for _ in range(10_000):
                s = []
                for t in (rng.choice(traces) for _ in traces):
                    s += [rng.choice(per[t]) for _ in per[t]]
                boot.append(delta(s, a, b))
            boot.sort()
            loo = [delta([k for t in traces if t != drop for k in per[t]], a, b) for drop in traces]
            out.append(f"| {a} | {b} | {sname} | {d:+.3f} | {min(draws):+.3f} – {max(draws):+.3f} | "
                       f"{sum(x <= 0 for x in draws)}/27 | [{boot[249]:+.3f}, {boot[9749]:+.3f}] | "
                       + " | ".join(f"{x:+.3f}" for x in loo) + " |")
    (res / "trace_bootstrap.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
