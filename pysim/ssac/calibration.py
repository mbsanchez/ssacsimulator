"""Learn per-station alarm base rates from a fault-free trace.

Use a different trace from the one under test, or the calibrated planner is
being tuned on its own test data.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .engine import FailType, SimulationEngine
from .events import SimulationData
from .model import BusinessProcessModel


def alarm_rates(
    model_path: str | Path,
    data: SimulationData,
    detectors: tuple[str, ...],
    types: tuple[FailType, ...] = (FailType.STATION_FAILURE, FailType.STATION_DEGRADED),
    processing_params: dict | None = None,
) -> dict[str, float]:
    """Alarms per simulated minute, per station, in a run with no faults."""
    model, errors = BusinessProcessModel.load(model_path)
    if errors:
        raise ValueError(errors)
    engine = SimulationEngine(model, data, detectors=detectors, processing_params=processing_params)
    engine.run()

    counts: Counter[str] = Counter()
    for d in engine.detections:
        if d.type in types:
            counts.update(d.stations)

    span = max(data.report.max_time - data.report.min_time, 1.0)
    if data.events:
        span = max(data.events[-1].start_time - data.events[0].start_time, 1.0)
    return {station: n / span for station, n in counts.items()}
