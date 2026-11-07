"""Structural knowledge derived from the process graph.

The Bosch line is built from parallel station pairs (and a few triples): two
stations fed by the same predecessors, feeding the same successors, splitting
the load almost evenly — e.g. L0_S2 / L0_S3 carry 339 345 / 334 054 cases.
Diverting a piece from a station to its twin therefore keeps its trajectory
consistent, which is what makes REROUTE a physically meaningful action.

Only visible edges (show == True) are used: they are the main flows. Invisible
edges are low-volume noise and would make every station look connected to
every other.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .model import BusinessProcessModel

SENTINELS = frozenset({"BEGIN", "END"})


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 0.0


@dataclass(frozen=True)
class Twin:
    station: str
    twin: str
    jaccard_pred: float
    jaccard_succ: float
    load_ratio: float  # twin load / station load


def find_twins(
    model: BusinessProcessModel,
    min_jaccard: float = 0.5,
) -> dict[str, list[Twin]]:
    """Map each station to its twins, best match first.

    Two stations are twins when they sit on the same production line (the
    "L0" in "L0_S2"; models without that naming count as one line) and both
    their predecessor and successor sets overlap by at least `min_jaccard` on
    visible edges.
    """
    succ: dict[str, set[str]] = defaultdict(set)
    pred: dict[str, set[str]] = defaultdict(set)
    load: dict[str, int] = defaultdict(int)

    for begin, edges in model.edges.items():
        for edge in edges.values():
            if edge.show and begin != edge.end:
                succ[begin].add(edge.end)
                pred[edge.end].add(begin)
                load[edge.end] += edge.cases

    stations = [a for a in model.actors if a not in SENTINELS]
    twins: dict[str, list[Twin]] = defaultdict(list)

    def line(name: str) -> str:
        # Bosch naming: "L0_S2" -> line "L0". Other naming: a single line.
        return name.split("_", 1)[0] if "_" in name else ""

    for i, a in enumerate(stations):
        for b in stations[i + 1:]:
            if line(a) != line(b):
                continue
            jp = _jaccard(pred[a], pred[b])
            js = _jaccard(succ[a], succ[b])
            if jp < min_jaccard or js < min_jaccard:
                continue
            la, lb = load[a] or 1, load[b] or 1
            twins[a].append(Twin(a, b, jp, js, lb / la))
            twins[b].append(Twin(b, a, jp, js, la / lb))

    for station in twins:
        twins[station].sort(key=lambda t: (-(t.jaccard_pred + t.jaccard_succ), abs(1 - t.load_ratio)))

    return dict(twins)
