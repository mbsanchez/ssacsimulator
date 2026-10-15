"""Fault injection and the effect model of actions (the Execute phase).

The simulation is trace-driven: event start times come from the recorded
Bosch data and are not shifted. Faults and actions act on transition
durations, which is what every detector and every metric reads (piece
lifetime is the sum of its transition durations). Delay does not propagate as
queueing into later start times: the model estimates time lost per piece; it
is not a queueing simulation.

Effects are ADDITIVE and scale with the station's processing time tau_S, not
with the whole transition. This matters. A Bosch "transition" is the time
between two station timestamps, and it mostly measures waiting, not work:
the median is 0 min and p90 30 min, but p99 is 4 000-6 000 min, and in three
of the four traces more than 84% of all transition time sits in transitions
longer than a day. Multiplying those by a fault factor would make a fault on
a station stretch days of storage, and costs would be driven by whichever
multi-day transitions happened to start inside an action window. An earlier
version did exactly that; see README.

tau_S is estimated from the trace (`estimate_service_times`): the median of
the transitions of up to 60 min leaving S on visible edges — the processing
regime, with storage excluded. It is part of the simulated world, never shown
to a planner. Across the four traces it is 12 min for L0_S2 and 6 min (the
timestamp granularity) for most stations, and very stable between traces.

Effect model, in full (all added to the recorded duration of a transition
leaving station S at time t):

* Fault(S, k, shape): + (k(t) - 1) * tau_S, with k(t) given by the shape:
    step          k from t0 on                               (sudden breakage)
    intermittent  k during `on_min`, 1 during `off_min`, ...  (loose contact)
    drift         rises linearly from 1 at t0 to k at t0+ramp (wear)
  The dataset has no labelled failures; all faults are synthetic.
* Reroute(S, T, f): a deterministic fraction f of the pieces entering S go to
  T instead (selection by CRC32 of the case id, so runs are reproducible). The
  piece then leaves from T, unaffected by S's faults. T absorbs extra load:
  + alpha * f_total * tau_T on every transition leaving T.
* Maintenance(S, d): faults on S already active at t are cleared at t + d
  (`repair_clears="active_at_start"`, the default since design v2; the v1
  rule "begun_before_end" also cleared faults that began during the repair),
  and any reroute away from S is lifted then. During the repair, by
  `maintenance_mode`:
    "contingency" (default)  backup capacity outside the model does the work:
                             + (contingency_factor - 1) * tau_S, and the fault
                             does not apply.
    "stop"                   the line waits: + (t_end - t), and S is still
                             faulty meanwhile. The pessimistic bound.
  Either way, maintaining a healthy station costs something and fixes nothing,
  which is what makes false alarms expensive.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field, replace

from .actions import Action, Maintenance, NoOp, Reroute, Restore
from .events import SimulationEvent
from .model import BusinessProcessModel


FAULT_SHAPES = ("step", "intermittent", "drift")


@dataclass(frozen=True)
class Fault:
    station: str
    factor: float
    start_min: float
    end_min: float | None = None
    shape: str = "step"
    on_min: float = 60.0      # intermittent
    off_min: float = 120.0    # intermittent
    ramp_min: float = 600.0   # drift

    def __post_init__(self) -> None:
        if self.shape not in FAULT_SHAPES:
            raise ValueError(f"unknown fault shape {self.shape!r}; expected one of {FAULT_SHAPES}")
        if self.factor < 1.0:
            raise ValueError("a fault factor must be >= 1")

    def scheduled(self, t_min: float) -> bool:
        return t_min >= self.start_min and (self.end_min is None or t_min < self.end_min)

    def factor_at(self, t_min: float) -> float:
        """Multiplier at time t, ignoring repairs."""
        if not self.scheduled(t_min):
            return 1.0
        elapsed = t_min - self.start_min
        if self.shape == "step":
            return self.factor
        if self.shape == "intermittent":
            return self.factor if elapsed % (self.on_min + self.off_min) < self.on_min else 1.0
        # drift
        return 1.0 + (self.factor - 1.0) * min(elapsed / self.ramp_min, 1.0)


MAINTENANCE_MODES = ("contingency", "stop")


@dataclass(frozen=True)
class EffectModel:
    congestion_alpha: float = 0.5
    maintenance_mode: str = "contingency"
    contingency_factor: float = 1.5
    # Which faults a completed repair clears: "begun_before_end" (any fault
    # that started before the repair ended, the original rule) or
    # "active_at_start" (only faults already active when the repair began).
    repair_clears: str = "active_at_start"

    def __post_init__(self) -> None:
        if self.maintenance_mode not in MAINTENANCE_MODES:
            raise ValueError(f"unknown maintenance mode {self.maintenance_mode!r}")
        if self.repair_clears not in ("begun_before_end", "active_at_start"):
            raise ValueError(f"unknown repair_clears {self.repair_clears!r}")


@dataclass
class InterventionStats:
    pieces_rerouted: int = 0
    reroute_fallbacks: int = 0
    maintenance_wait_min: float = 0.0
    fault_extra_min: float = 0.0
    congestion_extra_min: float = 0.0


@dataclass
class AppliedAction:
    t_min: float
    action: Action


def _selected(case_id: str, fraction: float) -> bool:
    if fraction >= 1.0:
        return True
    return zlib.crc32(case_id.encode()) / 2**32 < fraction


DEFAULT_SERVICE_MIN = 6.0   # timestamp granularity of the Bosch traces


def estimate_service_times(
    model: BusinessProcessModel,
    events,
    max_min: float = 60.0,
) -> dict[str, float]:
    """Median duration of transitions in (0, max_min] leaving each station on
    a visible edge. Stations with no such transition are omitted (callers
    fall back to DEFAULT_SERVICE_MIN)."""
    samples: dict[str, list[float]] = {}
    for e in events:
        if not 0.0 < e.transition_time <= max_min:
            continue
        edge = model.edge(e.begin_actor, e.end_actor)
        if edge is not None and edge.show:
            samples.setdefault(e.begin_actor, []).append(e.transition_time)
    out = {}
    for station, xs in samples.items():
        xs.sort()
        n = len(xs)
        out[station] = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
    return out


@dataclass
class InterventionState:
    model: BusinessProcessModel
    faults: list[Fault] = field(default_factory=list)
    effects: EffectModel = field(default_factory=EffectModel)
    service_times: dict[str, float] = field(default_factory=dict)
    default_service_min: float = DEFAULT_SERVICE_MIN

    reroutes: dict[str, tuple[str, float]] = field(default_factory=dict)   # station -> (twin, fraction)
    repairs: dict[str, list[tuple[float, float]]] = field(default_factory=dict)  # station -> [(start, end)]
    piece_map: dict[str, dict[str, str]] = field(default_factory=dict)     # case -> {station: twin}
    log: list[AppliedAction] = field(default_factory=list)
    stats: InterventionStats = field(default_factory=InterventionStats)
    extras: list[tuple[float, float]] = field(default_factory=list)       # (t_min, added minutes) per changed transition
    # the same additions split into the fault's own delay and the cost of actions
    # (contingency, waiting for a repair in stop mode, congestion on a twin)
    parts: list[tuple[float, float, float]] = field(default_factory=list)  # (t_min, fault, actions)

    # ---- queries --------------------------------------------------------

    def under_maintenance(self, station: str, t_min: float) -> bool:
        return any(s <= t_min < e for s, e in self.repairs.get(station, []))

    def fault_factor(self, station: str, t_min: float) -> float:
        k = 1.0
        for f in self.faults:
            if f.station != station or not f.scheduled(t_min):
                continue
            if self.effects.repair_clears == "active_at_start":
                repaired = any(
                    f.start_min <= start and end <= t_min for start, end in self.repairs.get(station, [])
                )
            else:
                repaired = any(
                    f.start_min < end <= t_min for _, end in self.repairs.get(station, [])
                )
            if not repaired:
                k *= f.factor_at(t_min)
        return k

    def repair_window(self, station: str, t_min: float) -> tuple[float, float] | None:
        for s, e in self.repairs.get(station, []):
            if s <= t_min < e:
                return s, e
        return None

    def service_time(self, station: str) -> float:
        return self.service_times.get(station, self.default_service_min)

    def inbound_share(self, station: str) -> float:
        return sum(frac for twin, frac in self.reroutes.values() if twin == station)

    # ---- execute --------------------------------------------------------

    def apply(self, action: Action, t_min: float) -> None:
        """Apply an already validated action."""
        match action:
            case Reroute(station, twin, fraction):
                self.reroutes[station] = (twin, fraction)
            case Restore(station):
                self.reroutes.pop(station, None)
            case Maintenance(station, duration):
                self.repairs.setdefault(station, []).append((t_min, t_min + duration))
            case NoOp():
                pass
        self.log.append(AppliedAction(t_min, action))

    def advance(self, t_min: float) -> None:
        """Lift reroutes whose station has finished its repair."""
        for station in list(self.reroutes):
            ended = [e for s, e in self.repairs.get(station, []) if e <= t_min]
            if ended and max(ended) > self._reroute_started(station):
                self.reroutes.pop(station)
                self.log.append(AppliedAction(max(ended), Restore(station)))

    def _reroute_started(self, station: str) -> float:
        for entry in reversed(self.log):
            if isinstance(entry.action, Reroute) and entry.action.station == station:
                return entry.t_min
        return float("-inf")

    # ---- event transform ------------------------------------------------

    def transform(self, event: SimulationEvent, t_min: float) -> SimulationEvent:
        cid = event.case_id
        begin, end = event.begin_actor, event.end_actor

        # 1. A piece previously diverted into a twin leaves from the twin.
        diverted = self.piece_map.get(cid)
        if diverted and begin in diverted:
            twin = diverted.pop(begin)
            if self.model.edge(twin, end) is not None:
                begin = twin
            else:
                self.stats.reroute_fallbacks += 1

        # 2. Divert the target if it is being rerouted and this piece is selected.
        rr = self.reroutes.get(end)
        if rr is not None and _selected(cid, rr[1]):
            twin = rr[0]
            if self.model.edge(begin, twin) is not None:
                self.piece_map.setdefault(cid, {})[end] = twin
                end = twin
                self.stats.pieces_rerouted += 1
            else:
                self.stats.reroute_fallbacks += 1

        # 3. Additive effects on the transition leaving `begin`, scaled by
        #    its processing time (never by the waiting part of the transition).
        base = event.transition_time
        duration = base
        fault_part = 0.0
        tau = self.service_time(begin)
        repair = self.repair_window(begin, t_min)
        contingency = repair is not None and self.effects.maintenance_mode == "contingency"

        if contingency:
            # Backup capacity does the work: S's fault does not apply.
            extra = (self.effects.contingency_factor - 1.0) * tau
            self.stats.maintenance_wait_min += extra
            duration += extra
        else:
            k = self.fault_factor(begin, t_min)
            if k != 1.0:
                extra = (k - 1.0) * tau
                self.stats.fault_extra_min += extra
                duration += extra
                fault_part = extra

        share = self.inbound_share(begin)
        if share > 0:
            extra = self.effects.congestion_alpha * share * tau
            self.stats.congestion_extra_min += extra
            duration += extra

        if repair is not None and not contingency:
            wait = repair[1] - t_min
            self.stats.maintenance_wait_min += wait
            duration += wait

        if duration != base:
            self.extras.append((t_min, duration - base))
            self.parts.append((t_min, fault_part, duration - base - fault_part))
        if begin == event.begin_actor and end == event.end_actor and duration == base:
            return event
        return replace(event, begin_actor=begin, end_actor=end, transition_time=duration)
