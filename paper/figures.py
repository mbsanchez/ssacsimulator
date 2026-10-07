#!/usr/bin/env python3
"""Figures for the paper, generated from the stored held-out results.

    ../pysim/.venv/bin/python figures.py

Palette: the first three slots of the validated categorical palette (all-pairs
safe; see dataviz skill), one hue per planner family. The aqua slot is below
3:1 contrast on white, so every mark is directly labelled and each family also
has its own marker shape - the figures stay readable in grayscale.
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "pysim" / "results"
OUT = HERE / "figures"
OUT.mkdir(exist_ok=True)

INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
FAMILY = {  # colour, marker
    "rules": ("#2a78d6", "o"),
    "qwen": ("#eb6834", "s"),
    "fable": ("#1baf7a", "^"),
}
PLANNERS = [  # (row name, label, family)
    ("rules_cal", "Rule: calibrated", "rules"),
    ("rules_adapt", "Rule: adaptive", "rules"),
    ("rules_adapt_ctx", "Rule: adaptive + load veto", "rules"),
    ("llm_c1", "C1 (Qwen 7B)", "qwen"),
    ("llm_c2", "C2 RAG (Qwen 7B)", "qwen"),
    ("hybrid", "Hybrid (Qwen 7B)", "qwen"),
    ("llm_c2:fable-5.1", "C2 RAG (Fable 5.1)", "fable"),
    ("hybrid:fable-5.1", "Hybrid (Fable 5.1)", "fable"),
]
SHAPES = ["step", "intermittent", "drift"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6, "pdf.fonttype": 42,
})


def load():
    rows = list(csv.DictReader((RESULTS / "llm_sweep_rows.csv").open()))
    fault = {(r["trace"], r["station"], r["shape"], r["planner"]): float(r["excess_delay_min"])
             for r in rows if r["station"]}
    free = {(r["trace"], r["planner"]): float(r["excess_delay_min"]) / float(r["span_h"])
            for r in rows if not r["station"]}
    keys = sorted({k[:3] for k in fault})
    return fault, free, keys


def pooled(fault, keys, p):
    return 1 - sum(fault[k + (p,)] for k in keys) / sum(fault[k + ("noop",)] for k in keys)


def bootstrap_ci(fault, keys, p, n=10_000, seed=0):
    traces = sorted({k[0] for k in keys})
    strata = {t: [k for k in keys if k[0] == t] for t in traces}
    rng = random.Random(seed)
    vals = []
    for _ in range(n):
        s = [rng.choice(strata[t]) for t in traces for _ in strata[t]]
        vals.append(pooled(fault, s, p))
    vals.sort()
    return vals[int(0.025 * n)], vals[int(0.975 * n) - 1]


def style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)


def fig_recovery(fault, keys):
    data = []
    for p, label, fam in PLANNERS:
        lo, hi = bootstrap_ci(fault, keys, p)
        data.append((pooled(fault, keys, p), lo, hi, label, fam))
    data.sort(key=lambda d: d[0])
    fig, ax = plt.subplots(figsize=(6.3, 3.0))
    for i, (v, lo, hi, label, fam) in enumerate(data):
        c, m = FAMILY[fam]
        ax.plot([lo, hi], [i, i], color=c, linewidth=1.4, solid_capstyle="round")
        ax.plot(v, i, marker=m, markersize=6.5, color=c, markeredgecolor="white", markeredgewidth=1.0)
        ax.text(hi + 0.02, i, f"{v:+.2f}", va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(data)), [d[3] for d in data], color=INK)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_xlabel("Pooled recovery on held-out traces (95% stratified bootstrap CI)")
    ax.set_xlim(min(d[1] for d in data) - 0.05, max(d[2] for d in data) + 0.15)
    style(ax)
    fig.tight_layout()
    fig.savefig(OUT / "fig_recovery.pdf")
    plt.close(fig)


def fig_tradeoff(fault, free, keys):
    traces = sorted({k[0] for k in keys})
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    offsets = {"rules_adapt": (6, -10), "rules_adapt_ctx": (6, 4), "rules_cal": (6, 3),
               "llm_c2:fable-5.1": (6, 3), "hybrid": (6, -3), "hybrid:fable-5.1": (6, 3),
               "llm_c1": (6, -3), "llm_c2": (6, 3)}
    for p, label, fam in PLANNERS:
        c, m = FAMILY[fam]
        x = sum(free[(t, p)] for t in traces) / len(traces)
        y = pooled(fault, keys, p)
        ax.plot(x, y, marker=m, markersize=7, color=c, markeredgecolor="white", markeredgewidth=1.0, linestyle="none")
        ax.annotate(label, (x, y), xytext=offsets.get(p, (6, 3)), textcoords="offset points",
                    fontsize=7.5, color=INK, va="center")
    ax.set_xlabel("False-alarm cost without faults (piece-min/h, mean of held-out traces)")
    ax.set_ylabel("Pooled recovery with faults")
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(-8, 230)
    handles = [plt.Line2D([], [], marker=FAMILY[f][1], color=FAMILY[f][0], linestyle="none", markersize=6, label=l)
               for f, l in (("rules", "Rule-based"), ("qwen", "LLM: Qwen 2.5 7B"), ("fable", "LLM: Claude Fable 5.1"))]
    ax.legend(handles=handles, frameon=False, loc="lower right", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(OUT / "fig_tradeoff.pdf")
    plt.close(fig)


def fig_shapes(fault, keys):
    chosen = [("rules_adapt_ctx", "Rule: adaptive + load veto", "rules"),
              ("llm_c2", "C2 RAG (Qwen 7B)", "qwen"),
              ("llm_c2:fable-5.1", "C2 RAG (Fable 5.1)", "fable")]
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    width = 0.26
    for j, (p, label, fam) in enumerate(chosen):
        c, _ = FAMILY[fam]
        for i, s in enumerate(SHAPES):
            ks = [k for k in keys if k[2] == s]
            v = pooled(fault, ks, p)
            x = i + (j - 1) * (width + 0.02)
            ax.bar(x, v, width=width, color=c, edgecolor="white", linewidth=1.0)
            ax.text(x, v + (0.03 if v >= 0 else -0.03), f"{v:+.2f}", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=7, color=INK)
    ax.set_xticks(range(len(SHAPES)), [s.capitalize() for s in SHAPES], color=INK)
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.set_ylabel("Pooled recovery")
    ax.set_ylim(-0.85, 0.85)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=FAMILY[f][0], label=l) for _, l, f in chosen]
    ax.legend(handles=handles, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=7.5, ncol=3)
    fig.tight_layout()
    fig.savefig(OUT / "fig_shapes.pdf")
    plt.close(fig)


def main():
    fault, free, keys = load()
    fig_recovery(fault, keys)
    fig_tradeoff(fault, free, keys)
    fig_shapes(fault, keys)
    for f in sorted(OUT.glob("*.pdf")):
        print("wrote", f.relative_to(HERE))


if __name__ == "__main__":
    main()
