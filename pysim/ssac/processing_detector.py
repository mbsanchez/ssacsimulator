"""Per-station Analyze on processing times (design v2 amendment, results/dev_log.md).

The legacy station detector compares means of whole transitions, which are
dominated by hours or days of storage, so a fault that adds minutes of
processing barely moves them. This detector looks only at the processing
regime: transitions leaving a station that last at most `regime_max_min`.

For each station, causally:
  reference  the 75th percentile of its processing transitions over the
             `history_min` minutes before the recent window, and the rate p0
             at which transitions in that history exceed it (Laplace-smoothed,
             so ties at the 6-min timestamp granularity are handled);
  test       among its last `window` processing transitions, the number that
             exceed the reference; the station is flagged when that count is
             improbable under Binomial(window, p0) at level `alpha`.
Nothing is flagged during the first `warmup_min` minutes. Flags are collected
per batch of simultaneous events and emitted together; a station is not
flagged again within `refractory_min` minutes.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field


def binomial_threshold(n: int, p: float, alpha: float) -> int:
    """Smallest x with P(X >= x) <= alpha for X ~ Binomial(n, p)."""
    tail = 0.0
    for x in range(n, -1, -1):
        tail += math.comb(n, x) * p ** x * (1 - p) ** (n - x)
        if tail > alpha:
            return x + 1
    return 0


@dataclass
class ProcessingDetector:
    window: int = 20
    alpha: float = 1e-3
    history_min: float = 1440.0
    warmup_min: float = 480.0
    regime_max_min: float = 60.0
    refractory_min: float = 60.0
    refresh_min: float = 60.0
    min_history: int = 20
    exclude: frozenset[str] = frozenset()
    # "binomial" (the detector of the paper) or "threshold": a control with the
    # same windows and the same processing regime but no statistical test, which
    # flags a station when the median of its last `window` processing
    # transitions exceeds `threshold_ratio` times the median of its history.
    test: str = "binomial"
    threshold_ratio: float = 1.3

    _t0: float | None = None
    _hist: dict[str, deque] = field(default_factory=dict)      # station -> (t, duration), history + window
    _ref: dict[str, tuple] = field(default_factory=dict)  # q75, p0, threshold, computed at, median
    _flagged_at: dict[str, float] = field(default_factory=dict)
    _pending: list[str] = field(default_factory=list)
    _thresholds: dict[tuple[int, float], int] = field(default_factory=dict)

    def observe(self, station: str, t_min: float, duration: float) -> None:
        if self._t0 is None:
            self._t0 = t_min
        if station in self.exclude or duration > self.regime_max_min or duration < 0:
            return
        h = self._hist.setdefault(station, deque())
        h.append((t_min, duration))
        while len(h) > self.window and h[0][0] < t_min - self.history_min:
            h.popleft()
        if t_min - self._t0 < self.warmup_min or station in self._pending:
            return
        if t_min - self._flagged_at.get(station, float("-inf")) < self.refractory_min:
            return
        if len(h) < self.window + self.min_history:
            return
        ref = self._ref.get(station)
        if ref is None or t_min - ref[3] >= self.refresh_min:
            ref = self._reference(h, t_min)
            self._ref[station] = ref
        q75, threshold = ref[0], ref[2]
        recent = list(h)[-self.window:]
        if self.test == "threshold":
            r = sorted(d for _, d in recent)
            if r[len(r) // 2] > self.threshold_ratio * ref[4]:
                self._pending.append(station)
            return
        exceed = sum(1 for _, d in recent if d > q75)
        if exceed >= threshold:
            self._pending.append(station)

    def _reference(self, h: deque, t_min: float) -> tuple[float, float, int, float]:
        items = list(h)[:-self.window]
        durs = sorted(d for _, d in items)
        q75 = durs[min(len(durs) - 1, int(0.75 * len(durs)))]
        over = sum(1 for d in durs if d > q75)
        p0 = (over + 1) / (len(durs) + 2)
        key = (self.window, round(p0, 3))
        if key not in self._thresholds:
            self._thresholds[key] = binomial_threshold(self.window, key[1], self.alpha)
        return q75, p0, self._thresholds[key], t_min, durs[len(durs) // 2]

    def flush(self, t_min: float) -> tuple[str, ...]:
        """Stations flagged in the batch that just ended."""
        out = tuple(self._pending)
        for s in out:
            self._flagged_at[s] = t_min
        self._pending.clear()
        return out
