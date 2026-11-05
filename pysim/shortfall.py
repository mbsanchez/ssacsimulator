#!/usr/bin/env python3
"""Shortfall of each planner from the best planner of each condition of the
sensitivity table, from results/llm_sensitivity.md. Post hoc and descriptive:
every condition weighs the same. No language model is called. Writes
results/shortfall.md."""

from __future__ import annotations

from pathlib import Path

RES = Path(__file__).resolve().parent / "results"
PLANNERS = [("rules_adapt_ctx", "Adaptive + load veto"), ("rules_burst_ctx", "Burst ≥3 + load veto"),
            ("rules_burst2_ctx", "Burst ≥2 + load veto"), ("hybrid", "Hybrid, Qwen 7B"), ("hybrid:fable-5.1", "Hybrid, Fable 5.1")]


def main() -> int:
    rows = [[c.strip() for c in l.strip().strip("|").split("|")]
            for l in (RES / "llm_sensitivity.md").read_text().splitlines() if l.startswith("| ")]
    head, body = rows[0], [r for r in rows[1:] if r[1] in ("216", "54")]
    gaps = {p: [] for p, _ in PLANNERS}
    for r in body:
        v = {p: float(r[head.index(p)]) for p, _ in PLANNERS}
        for p, x in v.items():
            gaps[p].append(max(v.values()) - x)
    out = [f"# Distancia al mejor planificador de cada condición ({len(body)} condiciones, post hoc)\n",
           "| Planificador | máxima | media |", "|---|---|---|"]
    out += [f"| {n} | {max(gaps[p]):.2f} | {sum(gaps[p]) / len(gaps[p]):.3f} |" for p, n in PLANNERS]
    (RES / "shortfall.md").write_text("\n".join(out) + "\n")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
