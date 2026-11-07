#!/usr/bin/env python3
"""Sensitivity of the hybrids and the rules to the effect model, common-cause
faults and replicas of the frontier hybrid without stored responses
(results/dev_log.md, 2026-10-15 and 2026-10-16), from stored results only.
No language model is called. Writes results/llm_sensitivity.md."""

from __future__ import annotations

from pathlib import Path

from extra_analyses import boot, compare, keys, load, pooled

RES = Path(__file__).resolve().parent / "results"
CONDS = [("central (k = 3, 60 min, α = 0,5, contingencia)", "processing"), ("k = 1,5", "sens_k1.5"), ("k = 5", "sens_k5"),
         ("reparación 15 min", "sens_r15"), ("reparación 240 min", "sens_r240"), ("modo parada", "sens_stop"),
         ("α = 0", "sens_a0"), ("α = 1", "sens_a1"), ("causa común (4 estaciones)", "commoncause")]
PLANNERS = ["rules_cal", "rules_adapt", "rules_adapt_ctx", "rules_cal_rt", "rules_adapt_ctx_rt", "rules_burst",
            "rules_burst_ctx", "rules_burst2_ctx", "hybrid", "hybrid:fable-5.1"]


def main() -> int:
    out = ["# Sensibilidad de los planificadores (trazas reservadas, detector por estación, diseño v2)\n",
           "Recuperación neta a 24 h. `rules_burst*` en la condición central: `results/veto_controls/` (misma configuración).\n",
           "| Condición | escenarios | " + " | ".join(PLANNERS) + " | Fable − burst_ctx [IC 95 %] | Fable − burst2_ctx [IC 95 %] | Fable − mejor regla [IC 95 %] |",
           "|---|---|" + "---|" * (len(PLANNERS) + 3)]
    for name, d in CONDS:
        R = load(RES / d)
        if d == "processing":
            import csv
            nm = {"burst|line120>=8": "rules_burst", "burst_ctx|size>=3": "rules_burst_ctx",
                  "burst_ctx|size>=2": "rules_burst2_ctx"}
            for r in [*csv.DictReader((RES / "veto_controls" / "rows.csv").open()),
                      *csv.DictReader((RES / "veto_controls2" / "rows.csv").open())]:
                if r["planner"] in nm and r["station"]:
                    R[(r["trace"], r["station"], r["shape"], r["onset_idx"], nm[r["planner"]])] = r
            cal_rt = {}
            for r in csv.DictReader((RES / "processing" / "rule_sweep.csv").open()):
                if r["station"] and r["planner"] == "rules_cal" and r["config"] == "w=240 a=0.0001":
                    R[(r["trace"], r["station"], r["shape"], r["onset_idx"], "rules_cal_rt")] = {"excess_h24_min": r["excess_h24_min"]}
                if r["station"] and r["planner"] == "rules_adapt_ctx" and r["config"] == "w=240 a=0.001 h=1440":
                    R[(r["trace"], r["station"], r["shape"], r["onset_idx"], "rules_adapt_ctx_rt")] = {"excess_h24_min": r["excess_h24_min"]}
        ks = [k for k in keys(R) if k + ("noop",) in R]
        have = [p for p in PLANNERS if all(k + (p,) in R for k in ks)]
        cells = [f"{pooled(R, p, ks):+.2f}" if p in have else "–" for p in PLANNERS]
        rules = [p for p in have if p.startswith("rules")]
        best = max(rules, key=lambda p: pooled(R, p, ks))
        c1 = compare(R, "hybrid:fable-5.1", R, "rules_burst_ctx", ks) if "rules_burst_ctx" in have else None
        c2 = compare(R, "hybrid:fable-5.1", R, best, ks)
        c3 = compare(R, "hybrid:fable-5.1", R, "rules_burst2_ctx", ks)
        f = lambda c: f"{c['delta']:+.2f} [{c['ci'][0]:+.2f}, {c['ci'][1]:+.2f}]" if c else "–"
        out.append(f"| {name} | {len(ks)} | " + " | ".join(cells) + f" | {f(c1)} | {f(c3)} | {f(c2)} ({best}) |")

    out += ["\n## Réplicas del híbrido Fable sin reutilizar respuestas de la evaluación reservada\n",
            "| Ejecución | recuperación 24 h [IC 95 %] | Δ frente a rules_adapt_ctx | llamadas nuevas |", "|---|---|---|---|"]
    H = load(RES / "processing")
    ks = keys(H)
    lo, hi = boot(lambda s: pooled(H, "hybrid:fable-5.1", s), ks, n=4000)
    out.append(f"| original | {pooled(H, 'hybrid:fable-5.1', ks):+.3f} [{lo:+.3f}, {hi:+.3f}] | "
               f"{compare(H, 'hybrid:fable-5.1', H, 'rules_adapt_ctx', ks)['delta']:+.3f} | – |")
    for i in (1, 2, 3):
        R = load(RES / f"replica_{i}")
        lo, hi = boot(lambda s: pooled(R, "hybrid:fable-5.1", s), ks, n=4000)
        rows = [R[k + ("hybrid:fable-5.1",)] for k in ks]
        new = sum(int(r["calls"]) - int(r["cache_hits"]) for r in rows)
        d = compare(R, "hybrid:fable-5.1", H, "rules_adapt_ctx", ks)["delta"]
        out.append(f"| réplica {i} | {pooled(R, 'hybrid:fable-5.1', ks):+.3f} [{lo:+.3f}, {hi:+.3f}] | {d:+.3f} | {new} |")
    (RES / "llm_sensitivity.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
