"""Fault onsets for evaluation design v2.

Each (trace, station, shape) gets `k` onsets drawn uniformly between
`margin_min` after the first event and `margin_min` before the last, from a
generator seeded by the scenario's name, so onsets do not depend on the order
in which scenarios are run or on which other scenarios exist.
"""

from __future__ import annotations

import hashlib
import random

MARGIN_MIN = 24 * 60.0
K_ONSETS = 3


def onsets(trace: str, station: str, shape: str, t_first: float, t_last: float,
           k: int = K_ONSETS, margin_min: float = MARGIN_MIN) -> list[float]:
    seed = int.from_bytes(hashlib.sha256(f"v2|{trace}|{station}|{shape}".encode()).digest()[:8], "big")
    rng = random.Random(seed)
    lo, hi = t_first + margin_min, t_last - margin_min
    if hi <= lo:
        raise ValueError(f"{trace}: trace too short for margin {margin_min} min")
    return sorted(round(rng.uniform(lo, hi), 1) for _ in range(k))

HORIZON_MIN = 1440.0            # primary: recovery within 24 h of the onset
HORIZONS_MIN = (480.0, 1440.0)  # secondary 8 h (one shift) and primary 24 h
