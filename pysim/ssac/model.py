"""Process model — headless port of businessprocess.{h,cpp}.

Faithful to the original, including the quirks that matter for behaviour:

* `Edge.time_count_mean` divides by the event count with no guard; the original
  does the same and relies on being called right after `add_event_time`. We
  return NaN instead of raising, matching C++ double division by zero.
* Reference times are binary32 (C++ `float`), so thresholds are computed in
  float32.
* The `show` flag is stored as the original's 4th transition field. In the Qt
  application a piece only follows an edge that was added to the scene, which
  is exactly the set of edges with `show == True`; headless runs use the flag
  directly.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .numeric import f32, qt_to_float, to_ulonglong


class NodeType(Enum):
    NORMAL = 0
    START = 1
    END = 2


@dataclass
class Actor:
    name: str
    type: NodeType
    cases: int = 0
    failing: bool = False


@dataclass
class Edge:
    begin: str
    end: str
    time: float            # reference transition time, minutes (binary32)
    cases: int
    show: bool
    events_count: int = 0
    time_count: float = 0.0

    @property
    def name(self) -> str:
        return f"{self.begin}-{self.end}"

    def add_event_time(self, time_in_min: float) -> None:
        self.events_count += 1
        self.time_count += time_in_min

    def reset_time_count(self) -> None:
        self.events_count = 0
        self.time_count = 0.0

    @property
    def time_count_mean(self) -> float:
        if self.events_count == 0:
            return math.nan
        return self.time_count / self.events_count


class ModelError(Exception):
    pass


@dataclass
class BusinessProcessModel:
    process_name: str = "Unknown Process"
    throughout_time: float = 0.0
    total_cases: int = 0
    begin_actor: str = ""
    end_actors: list[str] = field(default_factory=list)
    actors: dict[str, Actor] = field(default_factory=dict)
    edges: dict[str, dict[str, Edge]] = field(default_factory=dict)

    objects_count: int = 0
    time_count: float = 0.0

    # ---- loading -------------------------------------------------------

    @classmethod
    def load(cls, filename: str | Path) -> tuple["BusinessProcessModel", list[str]]:
        """Parse a .pg file. Returns (model, errors); errors mirrors the
        original's `errors` counter, as messages rather than a count."""
        model = cls()
        errors: list[str] = []
        begin_actors: list[str] = []
        end_actors: list[str] = []

        lines = Path(filename).read_text(encoding="utf-8", errors="replace").splitlines()
        i = 0
        while i < len(lines):
            line = lines[i]
            i += 1

            if not line.strip():
                continue

            if line.startswith("process:"):
                fields = line.split(":")
                model.process_name = fields[1].strip() if len(fields) == 2 else "Unknown Process"

            elif line.startswith("actors:"):
                for raw in line[7:].split(","):
                    node_type = NodeType.NORMAL
                    name = raw.strip()
                    if name.startswith("+"):
                        if not begin_actors:
                            node_type = NodeType.START
                            name = name[1:]
                            begin_actors.append(name)
                        else:
                            errors.append("only one start actor is allowed")
                    elif name.startswith("-"):
                        node_type = NodeType.END
                        name = name[1:]
                        end_actors.append(name)
                    model.actors[name] = Actor(name=name, type=node_type, cases=0)

            elif line.startswith("process_througout_time:"):
                fields = line.split(":")
                model.throughout_time = qt_to_float(fields[1].strip()) if len(fields) == 2 else 0.0

            elif line.startswith("total_cases:"):
                fields = line.split(":")
                model.total_cases = to_ulonglong(fields[1].strip()) if len(fields) == 2 else 0

            elif line.startswith("transitions:"):
                if not begin_actors:
                    errors.append("no actor defined as the process starting point")
                    break
                if not end_actors:
                    errors.append("no actor defined as a process end point")
                    break

                while i < len(lines):
                    transitions = lines[i]
                    i += 1
                    if not transitions.strip():
                        continue

                    vt = transitions.split("=")
                    if len(vt) != 2:
                        errors.append(f"processing transitions: {transitions!r}")
                        continue

                    begin = vt[0].strip()
                    h_edges: dict[str, Edge] = {}

                    for raw_edge in vt[1].strip().split("!"):
                        values = raw_edge.strip().split(";")
                        if len(values) != 4:
                            errors.append(f"processing edge: {raw_edge!r}")
                            continue

                        edge_cases = to_ulonglong(values[2].strip())
                        end = values[0].strip()

                        h_edges[end] = Edge(
                            begin=begin,
                            end=end,
                            time=qt_to_float(values[1].strip()),
                            cases=edge_cases,
                            show=bool(int(values[3].strip() or 0)),
                        )

                        if begin == begin_actors[0]:
                            model.actors[begin].cases += edge_cases

                        if end in model.actors:
                            if begin != end:
                                model.actors[end].cases += edge_cases
                        else:
                            errors.append(f"actor {end!r} was not defined previously")

                    model.edges[begin] = h_edges

        if not model.actors:
            errors.append("no actors defined")
        if not model.edges:
            errors.append("no connections defined")

        if begin_actors:
            begin = model.actors[begin_actors[0]]
            if begin.cases != model.total_cases:
                errors.append(
                    f"begin node cases ({begin.cases}) mismatches total_cases ({model.total_cases})"
                )

        if model.throughout_time <= 0:
            errors.append("throughout time is zero or undefined")
        if model.total_cases <= 0:
            errors.append("total cases is zero or undefined")

        if not errors:
            model.begin_actor = begin_actors[0]
            model.end_actors = end_actors

        return model, errors

    # ---- failing actors ------------------------------------------------

    def count_failing_actors(self) -> int:
        return sum(1 for a in self.actors.values() if a.failing)

    def failing_actors_as_string(self) -> str:
        return ", ".join(a.name for a in self.actors.values() if a.failing)

    def reset_failing_actors(self) -> None:
        for actor in self.actors.values():
            actor.failing = False

    # ---- global timing -------------------------------------------------

    def add_event_time(self, time_in_min: float) -> None:
        self.objects_count += 1
        self.time_count += time_in_min

    def reset_time_count(self) -> None:
        self.objects_count = 0
        self.time_count = 0.0

    @property
    def time_count_mean(self) -> float:
        if self.objects_count == 0:
            return math.nan
        return self.time_count / self.objects_count

    # ---- thresholds (float32, as in the original) ----------------------

    def station_threshold(self, edge: Edge) -> float:
        """`static_cast<double>(pEdge->time() * 1.3f)`"""
        return float(f32(f32(edge.time) * f32(1.3)))

    @property
    def global_threshold(self) -> float:
        """`static_cast<double>(_processModel->thoughoutTime() * 1.1f)`"""
        return float(f32(f32(self.throughout_time) * f32(1.1)))

    @property
    def station_failure_threshold(self) -> float:
        """`_processModel->actors().size()*0.1`"""
        return len(self.actors) * 0.1

    def edge(self, begin: str, end: str) -> Edge | None:
        return self.edges.get(begin, {}).get(end)
