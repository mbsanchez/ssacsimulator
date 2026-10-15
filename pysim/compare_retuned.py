#!/usr/bin/env python3
"""The hybrid planners against re-tuned rules, per-station detector, design v2.
No language model is called. Writes results/processing/compare_retuned.md.

Rules: the configuration selected on the development trace for the calibrated
rule and for the adaptive rule with load veto (results/processing/
rule_sweep_summary.md), and the held-out optimum of the latter (an upper bound
no honest protocol reaches)."""
import csv
import random
from pathlib import Path

from scipy.stats import wilcoxon

from stats import read_all

D = Path(__file__).resolve().parent / "results" / "processing"
RULES = [("rules_cal", "w=240 a=0.0001", "calibrada, elegida en desarrollo"),
         ("rules_adapt_ctx", "w=240 a=0.001 h=1440", "adaptativa + veto, elegida en desarrollo"),
         ("rules_adapt_ctx", "w=180 a=0.0001 h=720", "adaptativa + veto, óptimo en reservadas")]
L = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): float(r["excess_h24_min"])
     for r in read_all(D / "llm_sweep_rows.csv") if r["station"]}
RS = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"] + "|" + r["config"]): float(r["excess_h24_min"])
      for r in csv.DictReader((D / "rule_sweep.csv").open())
      if r["station"] and r["trace"] != "test_cases_0-100m.td"}
ks = sorted({k[:4] for k in L})
traces = sorted({k[0] for k in ks})
out = ["# Híbridos frente a reglas reajustadas — detector por estación, diseño v2\n",
       "Δ = recuperación a 24 h (híbrido) − ídem (regla); IC 95 % bootstrap estratificado por traza (10 000, semilla 0); "
       "Wilcoxon emparejado sobre el exceso a 24 h por escenario.\n",
       "| Híbrido | Regla | Δ | IC 95 % | híbrido mejor en | p |", "|---|---|---|---|---|---|"]
for a in ("hybrid:fable-5.1", "hybrid"):
    for p, cfg, desc in RULES:
        b = f"{p}|{cfg}"

        def d(s):
            return (sum(RS[k + (b,)] for k in s) - sum(L[k + (a,)] for k in s)) / sum(L[k + ("noop",)] for k in s)
        strata = {t: [k for k in ks if k[0] == t] for t in traces}
        rng = random.Random(0)
        boot = sorted(d([rng.choice(strata[t]) for t in traces for _ in strata[t]]) for _ in range(10_000))
        pv = wilcoxon([L[k + (a,)] - RS[k + (b,)] for k in ks if L[k + (a,)] != RS[k + (b,)]]).pvalue
        better = sum(L[k + (a,)] < RS[k + (b,)] for k in ks)
        out.append(f"| {a} | {desc} `{cfg}` | {d(ks):+.3f} | [{boot[249]:+.3f}, {boot[9749]:+.3f}] | {better}/{len(ks)} | {pv:.2g} |")
(D / "compare_retuned.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
