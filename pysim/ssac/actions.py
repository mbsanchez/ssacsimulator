"""Action space for the Plan / Execute phases, and the symbolic validator.

These phases do not exist in the original SSACSimulator; this module adds them.

Every action a planner proposes — rule-based or LLM — goes through `validate`
before the executor touches the system. The validator only checks facts that
can be decided against the process model and the current intervention state;
it never second-guesses *whether* an action is a good idea. That separation is
the point of condition C3 in the experiments: the LLM proposes, the graph
disposes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Union

from .topology import SENTINELS

if TYPE_CHECKING:
    from .intervention import InterventionState
    from .model import BusinessProcessModel
    from .topology import Twin


@dataclass(frozen=True)
class Reroute:
    """Divert a fraction of the pieces entering `station` to `twin`."""
    station: str
    twin: str
    fraction: float = 1.0


@dataclass(frozen=True)
class Restore:
    """Cancel an active reroute away from `station`."""
    station: str


@dataclass(frozen=True)
class Maintenance:
    """Take `station` down for repair. Clears faults that began before the
    repair ends; pieces still routed through the station wait for it. When the
    repair completes, any reroute away from the station is lifted."""
    station: str
    duration_min: float = 60.0


@dataclass(frozen=True)
class NoOp:
    reason: str = ""


Action = Union[Reroute, Restore, Maintenance, NoOp]


def describe(action: Action) -> str:
    match action:
        case Reroute(s, t, f):
            return f"REROUTE {s} -> {t} ({f:.0%})"
        case Restore(s):
            return f"RESTORE {s}"
        case Maintenance(s, d):
            return f"MAINTENANCE {s} ({d:g} min)"
        case NoOp(r):
            return f"NOOP{f' ({r})' if r else ''}"
    return repr(action)


def validate(
    action: Action,
    model: "BusinessProcessModel",
    twins: dict[str, list["Twin"]],
    state: "InterventionState",
    t_min: float,
) -> list[str]:
    """Return the list of violations; empty means the action is admissible."""
    errors: list[str] = []

    def is_station(name: str) -> bool:
        return name in model.actors and name not in SENTINELS

    match action:
        case NoOp():
            pass

        case Reroute(station, twin, fraction):
            if not is_station(station):
                errors.append(f"unknown station {station!r}")
            if not is_station(twin):
                errors.append(f"unknown station {twin!r}")
            if errors:
                return errors
            if station == twin:
                errors.append("cannot reroute a station to itself")
            if twin not in {t.twin for t in twins.get(station, [])}:
                errors.append(f"{twin} is not a structural twin of {station}")
            if not 0.0 < fraction <= 1.0:
                errors.append(f"fraction {fraction} outside (0, 1]")
            if twin in state.reroutes:
                errors.append(f"{twin} is itself being rerouted away")
            if state.reroutes.get(station, (None,))[0] not in (None, twin):
                errors.append(f"{station} is already rerouted elsewhere")
            if any(t == station for t, _ in state.reroutes.values()):
                errors.append(f"{station} is receiving rerouted load; rerouting it creates a chain")
            if state.under_maintenance(twin, t_min):
                errors.append(f"{twin} is under maintenance")

        case Restore(station):
            if station not in state.reroutes:
                errors.append(f"{station} has no active reroute")

        case Maintenance(station, duration):
            if not is_station(station):
                errors.append(f"unknown station {station!r}")
            elif state.under_maintenance(station, t_min):
                errors.append(f"{station} is already under maintenance")
            if not duration > 0:
                errors.append(f"duration {duration} must be positive")

        case _:
            errors.append(f"unknown action type {type(action).__name__}")

    return errors
