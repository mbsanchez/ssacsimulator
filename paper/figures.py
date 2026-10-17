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
RESULTS = HERE.parent / "pysim" / "results" / "processing"   # per-station detector, design v2
OUT = HERE / "figures"
LANG = "en"

ES = {
    "Rule: calibrated": "Regla: calibrada",
    "Rule: adaptive": "Regla: adaptativa",
    "Rule: adaptive + load veto": "Regla: adaptativa + veto por carga",
    "Hybrid (Qwen 7B)": "Híbrido (Qwen 7B)",
    "Hybrid (Fable 5.1)": "Híbrido (Fable 5.1)",
    "24-h recovery on held-out traces (95% stratified bootstrap CI)":
        "Recuperación a 24 h, trazas reservadas (IC 95%, bootstrap)",
    "Rule: twin-only (control)": "Regla: solo gemelas (control)",
    "Rule: burst veto (control)": "Regla: veto por ráfaga (control)",
    "Rule: burst + load veto (control)": "Regla: ráfaga + veto por carga (control)",
    "Rule: burst + load veto": "Regla: ráfaga + veto por carga",
    "False-alarm cost without faults (piece-min/h, mean of held-out traces)":
        "Coste de falsas alarmas sin fallos (min-pieza/h, media de las trazas reservadas)",
    "24-h recovery with faults": "Recuperación a 24 h con fallos",
    "24-h recovery": "Recuperación a 24 h",
    "Rule-based": "Reglas",
    "Step": "Escalón", "Intermittent": "Intermitente", "Drift": "Deriva",
}


def T(text: str) -> str:
    """Label in the current language (English is the source)."""
    return ES.get(text, text) if LANG == "es" else text


def num(v: float, fmt: str = "{:+.2f}") -> str:
    out = fmt.format(v)
    return out.replace(".", ",") if LANG == "es" else out


def decimal_axes(ax, *axes):
    """Decimal comma on numeric axes in Spanish."""
    if LANG != "es":
        return
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda x, _: f"{x:g}".replace(".", ","))
    for a in axes:
        (ax.xaxis if a == "x" else ax.yaxis).set_major_formatter(f)

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
    ("rules_twin", "Rule: twin-only (control)", "rules"),
    ("rules_burst", "Rule: burst veto (control)", "rules"),
    ("rules_burst_ctx", "Rule: burst + load veto (control)", "rules"),
    ("llm_c1", "C1 (Qwen 7B)", "qwen"),
    ("llm_c2", "C2 RAG (Qwen 7B)", "qwen"),
    ("hybrid", "Hybrid (Qwen 7B)", "qwen"),
    ("llm_c1:fable-5.1", "C1 (Fable 5.1)", "fable"),
    ("llm_c2:fable-5.1", "C2 RAG (Fable 5.1)", "fable"),
    ("hybrid:fable-5.1", "Hybrid (Fable 5.1)", "fable"),
]
SHAPES = ["step", "intermittent", "drift"]

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.linewidth": 0.6, "pdf.fonttype": 42,
})


def load():
    import sys
    sys.path.insert(0, str(HERE.parent / "pysim"))
    from stats import read_all
    rows = read_all(RESULTS / "llm_sweep_rows.csv")
    fault = {(r["trace"], r["station"], r["shape"], r["onset_idx"], r["planner"]): float(r["excess_h24_min"])
             for r in rows if r["station"]}
    free = {(r["trace"], r["planner"]): float(r["excess_delay_min"]) / float(r["span_h"])
            for r in rows if not r["station"]}
    # veto controls (pysim/results/veto_controls/), same scenarios and detector
    import csv
    names = {"burst|line120>=8": "rules_burst", "burst_ctx|size>=3": "rules_burst_ctx"}
    for r in csv.DictReader((RESULTS.parent / "veto_controls" / "rows.csv").open()):
        if r["planner"] in names:
            if r["station"]:
                fault[(r["trace"], r["station"], r["shape"], r["onset_idx"], names[r["planner"]])] = float(r["excess_h24_min"])
            else:
                free[(r["trace"], names[r["planner"]])] = float(r["false_cost_per_h"])
    keys = sorted({k[:4] for k in fault if k[:4] + ("noop",) in fault})
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
        ax.text(hi + 0.02, i, num(v), va="center", fontsize=8, color=INK)
    ax.set_yticks(range(len(data)), [T(d[3]) for d in data], color=INK)
    ax.axvline(0, color=INK2, linewidth=0.8)
    ax.set_xlabel(T("24-h recovery on held-out traces (95% stratified bootstrap CI)"))
    decimal_axes(ax, "x")
    ax.set_xlim(min(d[1] for d in data) - 0.05, max(d[2] for d in data) + 0.15)
    style(ax)
    fig.tight_layout()
    fig.savefig(out_dir() / "fig_recovery.pdf")
    plt.close(fig)


def fig_tradeoff(fault, free, keys):
    traces = sorted({k[0] for k in keys})
    fig, ax = plt.subplots(figsize=(6.3, 3.4))
    # (dx, dy) in points and horizontal alignment of each label
    offsets = {"rules_adapt": (7, 7, "left"), "rules_adapt_ctx": (7, 4, "left"), "rules_cal": (7, -8, "left"),
               "llm_c2:fable-5.1": (-7, 0, "right"), "hybrid": (7, 0, "left"), "hybrid:fable-5.1": (7, 0, "left"),
               "llm_c1": (7, 0, "left"), "llm_c2": (-7, 0, "right"), "llm_c1:fable-5.1": (7, 0, "left"),
               "rules_twin": (7, 0, "left"), "rules_burst": (-7, -6, "right"), "rules_burst_ctx": (7, 4, "left")}
    for p, label, fam in PLANNERS:
        c, m = FAMILY[fam]
        x = sum(free[(t, p)] for t in traces) / len(traces)
        y = pooled(fault, keys, p)
        ax.plot(x, y, marker=m, markersize=7, color=c, markeredgecolor="white", markeredgewidth=1.0, linestyle="none")
        dx, dy, ha = offsets.get(p, (7, 0, "left"))
        ax.annotate(T(label), (x, y), xytext=(dx, dy), textcoords="offset points",
                    fontsize=7.5, color=INK, va="center", ha=ha)
    ax.set_xlabel(T("False-alarm cost without faults (piece-min/h, mean of held-out traces)"))
    ax.set_ylabel(T("24-h recovery with faults"))
    decimal_axes(ax, "y")
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.set_xlim(-8, 230)
    handles = [plt.Line2D([], [], marker=FAMILY[f][1], color=FAMILY[f][0], linestyle="none", markersize=6, label=T(l))
               for f, l in (("rules", "Rule-based"), ("qwen", "LLM: Qwen 2.5 7B"), ("fable", "LLM: Claude Fable 5.1"))]
    ax.legend(handles=handles, frameon=False, loc="upper right", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(out_dir() / "fig_tradeoff.pdf")
    plt.close(fig)


def fig_shapes(fault, keys):
    chosen = [("rules_burst_ctx", "Rule: burst + load veto", "rules"),
              ("hybrid", "Hybrid (Qwen 7B)", "qwen"),
              ("hybrid:fable-5.1", "Hybrid (Fable 5.1)", "fable")]
    fig, ax = plt.subplots(figsize=(6.3, 2.8))
    width = 0.26
    for j, (p, label, fam) in enumerate(chosen):
        c, _ = FAMILY[fam]
        for i, s in enumerate(SHAPES):
            ks = [k for k in keys if k[2] == s]
            v = pooled(fault, ks, p)
            lo, hi = bootstrap_ci(fault, ks, p)
            x = i + (j - 1) * (width + 0.02)
            ax.bar(x, v, width=width, color=c, edgecolor="white", linewidth=1.0)
            ax.plot([x, x], [lo, hi], color=INK2, linewidth=0.9)
            ax.text(x, (hi + 0.03) if v >= 0 else (lo - 0.03), num(v), ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=7, color=INK)
    ax.set_xticks(range(len(SHAPES)), [T(s.capitalize()) for s in SHAPES], color=INK)
    ax.axhline(0, color=INK2, linewidth=0.8)
    ax.set_ylabel(T("24-h recovery"))
    decimal_axes(ax, "y")
    ax.set_ylim(-0.6, 0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=FAMILY[f][0], label=T(l)) for _, l, f in chosen]
    ax.legend(handles=handles, frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), fontsize=7.5, ncol=3)
    fig.tight_layout()
    fig.savefig(out_dir() / "fig_shapes.pdf")
    plt.close(fig)


def out_dir() -> Path:
    d = OUT / "es" if LANG == "es" else OUT
    d.mkdir(parents=True, exist_ok=True)
    return d


def main():
    import argparse
    global LANG
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["en", "es"], default="en")
    LANG = ap.parse_args().lang
    fault, free, keys = load()
    fig_recovery(fault, keys)
    fig_tradeoff(fault, free, keys)
    fig_shapes(fault, keys)
    for f in sorted(out_dir().glob("*.pdf")):
        print("wrote", f.relative_to(HERE))


if __name__ == "__main__":
    main()
