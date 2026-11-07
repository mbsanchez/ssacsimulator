"""Outcome metrics, computed against a fault-free reference run.

The simulation replays the same trace in every run, so each piece can be
compared with itself: excess delay = lifetime under the policy minus lifetime
in the fault-free run. Summed over pieces, it is the production time the fault
cost. The recovery ratio normalises a policy against doing nothing:

    recovery = 1 - excess(policy) / excess(no action)

1.0 means the policy erased the fault's cost; 0 means it did no better than
doing nothing; negative means its actions cost more than the fault itself.
"""

from __future__ import annotations

from dataclasses import dataclass

from .engine import FailType, SimulationEngine
from .intervention import Fault


@dataclass
class Outcome:
    policy: str
    excess_delay_min: float
    pieces_delayed: int
    detections: int
    detections_on_fault: int
    first_detection_latency_min: float | None
    actions_proposed: int
    actions_rejected: int
    maintenances: int
    maintenances_on_fault: int
    maintenances_false: int
    first_action_latency_min: float | None
    reroutes: int
    pieces_rerouted: int
    maintenance_wait_min: float
    fault_extra_min: float
    congestion_extra_min: float
    recovery: float | None = None
    # Design v2: within a horizon after the fault onset (minutes -> value).
    excess_h: dict[float, float] | None = None
    maintenances_on_fault_h: dict[float, int] | None = None
    maintenances_false_h: dict[float, int] | None = None
    fault_h: dict[float, float] | None = None      # the fault's own delay left in the window
    actions_h: dict[float, float] | None = None    # delay caused by the planner's actions in the window


def outcome(
    policy: str,
    engine: SimulationEngine,
    reference: dict[str, float],
    faults: list[Fault],
    station_types: tuple[FailType, ...] = (FailType.STATION_FAILURE, FailType.STATION_DEGRADED),
    horizons_min: tuple[float, ...] = (),
) -> Outcome:
    excess = 0.0
    delayed = 0
    for case_id, lifetime in engine.lifetimes.items():
        d = lifetime - reference.get(case_id, lifetime)
        if d > 1e-9:
            delayed += 1
        excess += d

    faulty = {f.station for f in faults}
    start = min((f.start_min for f in faults), default=None)
    on_fault = [
        d for d in engine.detections
        if d.type in station_types and faulty & set(d.stations)
        and start is not None and d.sim_time_min >= start
    ]
    latency = (on_fault[0].sim_time_min - start) if on_fault else None

    accepted = [d for d in engine.decisions if d.accepted]
    kinds = [type(d.action).__name__ for d in accepted]
    maint = [d for d in accepted if type(d.action).__name__ == "Maintenance"]
    maint_fault = [d for d in maint if d.action.station in faulty and start is not None and d.t_min >= start]
    on_fault_actions = [
        d for d in accepted
        if getattr(d.action, "station", None) in faulty and start is not None and d.t_min >= start
    ]
    iv = engine.interventions
    st = iv.stats if iv is not None else None

    return Outcome(
        policy=policy,
        excess_delay_min=excess,
        pieces_delayed=delayed,
        detections=len(engine.detections),
        detections_on_fault=len(on_fault),
        first_detection_latency_min=latency,
        actions_proposed=len(engine.decisions),
        actions_rejected=sum(1 for d in engine.decisions if not d.accepted),
        maintenances=len(maint),
        maintenances_on_fault=len(maint_fault),
        maintenances_false=len(maint) - len(maint_fault),
        first_action_latency_min=(on_fault_actions[0].t_min - start) if on_fault_actions else None,
        reroutes=kinds.count("Reroute"),
        pieces_rerouted=st.pieces_rerouted if st else 0,
        maintenance_wait_min=st.maintenance_wait_min if st else 0.0,
        fault_extra_min=st.fault_extra_min if st else 0.0,
        congestion_extra_min=st.congestion_extra_min if st else 0.0,
        **_horizon(iv, maint, faulty, start, horizons_min),
    )


def _horizon(iv, maint, faulty, start, horizons_min) -> dict:
    """Excess delay added to transitions in [start, start + h), and repairs
    started in that window, for each horizon h. The model is additive, so the
    sum of per-transition additions over the whole run equals the lifetime
    excess of `excess_delay_min`."""
    if not horizons_min or start is None:
        return {}
    extras = iv.extras if iv is not None else []
    parts = iv.parts if iv is not None else []
    ex, on, false, fp, ap = {}, {}, {}, {}, {}
    for h in horizons_min:
        ex[h] = sum(x for t, x in extras if start <= t < start + h)
        fp[h] = sum(f for t, f, _ in parts if start <= t < start + h)
        ap[h] = sum(a for t, _, a in parts if start <= t < start + h)
        win = [d for d in maint if start <= d.t_min < start + h]
        on[h] = sum(1 for d in win if d.action.station in faulty)
        false[h] = len(win) - on[h]
    return {"excess_h": ex, "maintenances_on_fault_h": on, "maintenances_false_h": false,
            "fault_h": fp, "actions_h": ap}


def with_recovery(outcomes: list[Outcome], baseline: str = "noop") -> list[Outcome]:
    base = next((o for o in outcomes if o.policy == baseline), None)
    if base is None or base.excess_delay_min <= 0:
        return outcomes
    for o in outcomes:
        o.recovery = 1.0 - o.excess_delay_min / base.excess_delay_min
    return outcomes
