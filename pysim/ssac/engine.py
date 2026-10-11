"""Headless simulation engine — port of simulationengine.cpp and the
timing half of smartobject.cpp.

What the original does, and therefore what this reproduces:

* Monitor: reads events in order, advancing a virtual clock.
* Analyze: three hardcoded thresholds.
    - station: edge mean transition time > edge reference time * 1.3
    - stations: more than 10% of actors flagged within one simultaneous batch
    - global: mean piece lifetime > process throughout time * 1.1
* Plan / Execute: ABSENT. `emit_reconfiguration` only produced a log line in
  the Qt UI. Here it appends a `Detection`. Nothing acts on it.

The GUI parts of SmartObject (painting, slerp geometry) are dropped; only the
animation *clock* is kept, because `time_count` and `finished` feed the global
performance check.

One documented deviation: in C++ `dxMillis = eventStartTime - _currentTimeMillis`
is unsigned, so an out-of-order event (start time earlier than the clock)
underflows to a huge value — undefined behaviour in practice. Rather than
reproduce that, we clamp to 0 and count it in `clock_regressions`, so a
non-monotonic input file is visible instead of silently corrupting a run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .actions import Action, validate
from .events import SimulationData, SimulationEvent
from .intervention import EffectModel, Fault, InterventionState, estimate_service_times
from .model import BusinessProcessModel
from .planning import Planner, PlanningContext
from .topology import find_twins

DEFAULT_SPEED = 150        # 1 simulated minute per 3 s of wall clock in the UI
MAX_SPEED = 15_000
MIN_SPEED = 1
DEFAULT_TIME_DELAY = 20    # ms per UI tick


class FailType(Enum):
    PREDICTED_FAILURE = "PREDICTED_FAILURE"
    STATION_FAILURE = "STATION_FAILURE"
    GLOBAL_FAILURE = "GLOBAL_FAILURE"
    # Not in the original: per-station detector, opt-in (see SimulationEngine).
    STATION_DEGRADED = "STATION_DEGRADED"


@dataclass(slots=True)
class Detection:
    """One `reconfigureIsNeeded` emission."""
    type: FailType
    sim_time_ms: int
    event_index: int
    detail: str
    stations: tuple[str, ...] = ()

    @property
    def sim_time_min(self) -> float:
        return self.sim_time_ms / 60000.0


@dataclass(slots=True)
class Piece:
    """SmartObject without the graphics."""
    case_id: str
    end_actor: str = ""
    seq: int = 0              # entry order; the original removes pieces in this order
    _current_ms: int = 0
    _anim_ms: int = 0
    _time_count: float = 0.0
    _has_path: bool = False

    def set_path(self, has_path: bool, anim_time_ms: int) -> None:
        self._has_path = has_path
        self._current_ms = 0
        self._anim_ms = anim_time_ms
        self._time_count += anim_time_ms / 60000.0
        if anim_time_ms <= 0 or not has_path:
            self._anim_ms = 0

    def next_step(self, dx_ms: int) -> None:
        if not self._has_path or self._current_ms >= self._anim_ms or dx_ms == 0:
            return
        x = self._current_ms + dx_ms
        if x >= self._anim_ms:
            x = self._anim_ms
        self._current_ms = x

    @property
    def finished(self) -> bool:
        return self._current_ms >= self._anim_ms

    @property
    def time_count(self) -> float:
        return self._time_count


@dataclass(slots=True)
class Decision:
    """One action proposed by the planner, with the validator's verdict."""
    t_min: float
    trigger: FailType
    action: Action
    errors: list[str]

    @property
    def accepted(self) -> bool:
        return not self.errors


@dataclass
class RunStats:
    events_processed: int = 0
    pieces_entered: int = 0
    pieces_completed: int = 0
    ticks: int = 0
    unknown_actor: int = 0
    unknown_edge: int = 0
    clock_regressions: int = 0
    final_pieces_in_system: int = 0
    final_sim_time_ms: int = 0


class SimulationEngine:
    def __init__(
        self,
        process_model: BusinessProcessModel,
        data: SimulationData,
        speed: int = DEFAULT_SPEED,
        time_delay: int = DEFAULT_TIME_DELAY,
        *,
        faults: tuple[Fault, ...] | list[Fault] = (),
        planner: Planner | None = None,
        effects: EffectModel | None = None,
        detectors: tuple[str, ...] = ("legacy",),
        degraded_window: int = 10,
        step_all_pieces: bool = False,
    ) -> None:
        """
        faults           injected faults (ground truth; never shown to the planner)
        planner          Plan phase; None reproduces the original (detect only)
        effects          parameters of the action effect model
        detectors        "legacy" = the three original detectors (always on);
                         "per_station" adds STATION_DEGRADED, which evaluates
                         each edge with a non-zero reference time over a
                         tumbling window of `degraded_window` transitions and
                         emits one detection per station. See README for why
                         the legacy station detector cannot isolate a single
                         faulty station.
        step_all_pieces  True runs the original per-tick loop over every piece
                         in the system. Kept only as the test oracle for the
                         fast path; results are identical either way.
        """
        self.model = process_model
        self.data = data
        self.speed = max(MIN_SPEED, min(MAX_SPEED, speed))
        self.time_delay = time_delay

        self.current_time_ms: int = 0
        self.last_event: int = -1
        self.pieces: dict[str, Piece] = {}
        self.detections: list[Detection] = []
        self.decisions: list[Decision] = []
        self.lifetimes: dict[str, float] = {}
        self.stats = RunStats()

        self.planner = planner
        self.detectors = frozenset(detectors) | {"legacy"}
        self.degraded_window = degraded_window
        self._degraded_acc: dict[tuple[str, str], list[float]] = {}

        self.twins = find_twins(process_model)
        self.interventions: InterventionState | None = None
        if faults or planner is not None:
            self.interventions = InterventionState(
                model=process_model,
                faults=list(faults),
                effects=effects or EffectModel(),
                service_times=estimate_service_times(process_model, data.events),
            )

        # Performance. The original advances the animation clock of EVERY piece
        # on EVERY tick. But a piece can only leave the system when its
        # end_actor is an end node, and the clock of any other piece is never
        # observed: set_path() resets it on the piece's next event. So only
        # pieces heading to an end node ("exiting") need stepping — a handful
        # at any time, against thousands of pieces stuck in the system. On the
        # 10 098-min trace this is the difference between ~1 billion and a few
        # thousand step calls per run. Removal order is preserved via `seq`.
        # tests/test_parity.py checks the fast path against the original loop.
        self.step_all_pieces = step_all_pieces
        self._end_set = frozenset(process_model.end_actors)
        self._exiting: dict[str, Piece] = {}
        self._seq = 0

        self.model.reset_failing_actors()

    # ---- main loop -----------------------------------------------------

    def run(self, max_ticks: int | None = None) -> RunStats:
        base_dx = self.time_delay * self.speed

        while True:
            if max_ticks is not None and self.stats.ticks >= max_ticks:
                break

            event = self.data.event_at(self.last_event + 1)
            if event is None:
                break

            self.stats.ticks += 1
            dx = base_dx
            process_next = False
            event_start = event.start_time_ms

            if not self.pieces:
                self.current_time_ms = event_start

            if self.current_time_ms + dx >= event_start:
                dx = event_start - self.current_time_ms
                if dx < 0:
                    self.stats.clock_regressions += 1
                    dx = 0
                process_next = True

            self.current_time_ms += dx

            if self.interventions is not None and process_next:
                self.interventions.advance(self.current_time_ms / 60000.0)

            while process_next:
                self.last_event += 1
                self.stats.events_processed += 1

                ev = event
                if self.interventions is not None:
                    ev = self.interventions.transform(event, self.current_time_ms / 60000.0)

                if ev.case_id in self.pieces:
                    piece = self.pieces[ev.case_id]
                    self._update_edge(piece, ev)
                else:
                    piece = self._enter(ev)

                event = self.data.event_at(self.last_event + 1)
                if event is None or self.current_time_ms != event.start_time_ms:
                    process_next = False
                    self._check_station_failures()

            to_remove = None
            if self.step_all_pieces:
                end_actors = self.model.end_actors
                for piece in self.pieces.values():
                    piece.next_step(dx)
                    if piece.finished and piece.end_actor in end_actors:
                        if to_remove is None:
                            to_remove = []
                        to_remove.append(piece)
            else:
                for piece in self._exiting.values():
                    piece.next_step(dx)
                    if piece.finished:
                        if to_remove is None:
                            to_remove = []
                        to_remove.append(piece)
                if to_remove is not None and len(to_remove) > 1:
                    to_remove.sort(key=lambda pc: pc.seq)

            if to_remove is not None:
                for piece in to_remove:
                    self._leave(piece)

        for piece in self.pieces.values():
            self.lifetimes[piece.case_id] = piece.time_count
        self.stats.final_pieces_in_system = len(self.pieces)
        self.stats.final_sim_time_ms = self.current_time_ms
        return self.stats

    # ---- piece lifecycle -----------------------------------------------

    def _enter(self, event: SimulationEvent) -> Piece:
        piece = Piece(case_id=event.case_id, seq=self._seq)
        self._seq += 1
        self.pieces[event.case_id] = piece
        self.stats.pieces_entered += 1
        self._predict_failure(piece, event)
        self._update_edge(piece, event)
        return piece

    def _update_edge(self, piece: Piece, event: SimulationEvent) -> None:
        edge = None
        if event.begin_actor in self.model.edges:
            edge = self.model.edges[event.begin_actor].get(event.end_actor)
            if edge is None:
                self.stats.unknown_edge += 1
        else:
            self.stats.unknown_actor += 1

        # In the Qt app the piece follows the edge only when it was added to
        # the scene, i.e. when show == True.
        if edge is None or not edge.show:
            piece.set_path(False, event.transition_time_ms)
            piece.end_actor = ""
        else:
            piece.set_path(True, event.transition_time_ms)
            piece.end_actor = event.end_actor

        if piece.end_actor in self._end_set:
            self._exiting[piece.case_id] = piece
        else:
            self._exiting.pop(piece.case_id, None)

        if edge is not None:
            edge.add_event_time(event.transition_time)
        self._check_station_performance(edge)
        if edge is not None and "per_station" in self.detectors:
            self._check_station_degraded(edge, event.transition_time)

    def _leave(self, piece: Piece) -> None:
        self.lifetimes[piece.case_id] = piece.time_count
        self._exiting.pop(piece.case_id, None)
        self.model.add_event_time(piece.time_count)
        self._check_global_performance(piece)
        self.pieces.pop(piece.case_id, None)
        self.stats.pieces_completed += 1

    # ---- analyze -------------------------------------------------------

    def _predict_failure(self, piece: Piece, event: SimulationEvent) -> None:
        if event.fails == 1:
            self._emit(
                FailType.PREDICTED_FAILURE,
                f"piece {piece.case_id} predicted to fail",
            )

    def _check_station_performance(self, edge) -> None:
        if edge is None:
            return
        if edge.time_count_mean > self.model.station_threshold(edge):
            edge.reset_time_count()
            actor = self.model.actors.get(edge.begin)
            if actor is not None:
                actor.failing = True

    def _check_station_degraded(self, edge, duration: float) -> None:
        if edge.time <= 0.0:
            return  # zero reference time: threshold would be 0, pure noise
        acc = self._degraded_acc.setdefault((edge.begin, edge.end), [0, 0.0])
        acc[0] += 1
        acc[1] += duration
        if acc[0] < self.degraded_window:
            return
        mean = acc[1] / acc[0]
        acc[0], acc[1] = 0, 0.0
        if mean > self.model.station_threshold(edge):
            self._emit(
                FailType.STATION_DEGRADED,
                f"{edge.begin}: mean {mean:.1f} min on {edge.name} "
                f"(reference {edge.time:g}, window {self.degraded_window})",
                stations=(edge.begin,),
            )

    def _check_station_failures(self) -> None:
        if self.model.count_failing_actors() > self.model.station_failure_threshold:
            failing = tuple(a.name for a in self.model.actors.values() if a.failing)
            self._emit(
                FailType.STATION_FAILURE,
                f"stations not working properly: {self.model.failing_actors_as_string()}",
                stations=failing,
            )
        self.model.reset_failing_actors()

    def _check_global_performance(self, piece: Piece) -> None:
        if self.model.time_count_mean > self.model.global_threshold:
            self.model.reset_time_count()
            self._emit(FailType.GLOBAL_FAILURE, "global production delay detected")

    def _emit(self, fail_type: FailType, detail: str, stations: tuple[str, ...] = ()) -> None:
        detection = Detection(
            type=fail_type,
            sim_time_ms=self.current_time_ms,
            event_index=self.last_event,
            detail=detail,
            stations=stations,
        )
        self.detections.append(detection)
        if self.planner is not None:
            self._plan(detection)

    # ---- plan / execute ------------------------------------------------

    def _plan(self, detection: Detection) -> None:
        assert self.interventions is not None
        t_min = self.current_time_ms / 60000.0
        ctx = PlanningContext(
            t_min=t_min,
            detection=detection,
            model=self.model,
            twins=self.twins,
            interventions=self.interventions,
        )
        for action in self.planner.plan(ctx):
            errors = validate(action, self.model, self.twins, self.interventions, t_min)
            self.decisions.append(Decision(t_min, detection.type, action, errors))
            if not errors:
                self.interventions.apply(action, t_min)

    # ---- reporting -----------------------------------------------------

    def detection_counts(self) -> dict[str, int]:
        counts = {t.value: 0 for t in FailType}
        for d in self.detections:
            counts[d.type.value] += 1
        return counts
