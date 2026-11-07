"""Event data — headless port of simulationevent.{h,cpp}.

Two fidelity details worth stating explicitly, because both change results:

1. The original keeps `DATA_INITIAL_CHUNK_LENGHT = 100000` and never calls
   `getNextChunck` again, so a run covers at most the first 100 000 events of a
   file. `max_events` defaults to that value to reproduce it; pass None to read
   the whole file.

2. A malformed row is skipped only when BOTH `duration` and `start` fail to
   parse (`if(!durationOk && !startTimeOk)`). A row whose duration is garbage
   but whose start time parses is KEPT, with duration 0.0 — Qt's `toDouble`
   yields 0.0 on failure. This looks like a bug, but it is the published
   behaviour, so the port reproduces it and counts the occurrences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .numeric import qt_to_double, qt_to_int

DATA_INITIAL_CHUNK_LENGTH = 100_000


@dataclass(slots=True)
class SimulationEvent:
    case_id: str
    begin_actor: str
    end_actor: str
    transition_time: float   # minutes
    start_time: float        # minutes
    fails: int = -1

    @property
    def transition_time_ms(self) -> int:
        # static_cast<ulong>(_transitionTime * 60ul * 1000ul)
        return int(self.transition_time * 60 * 1000)

    @property
    def start_time_ms(self) -> int:
        # static_cast<qulonglong>(_startTime * 60ull * 1000ull)
        return int(self.start_time * 60 * 1000)


@dataclass
class LoadReport:
    declared_events: int = 0
    min_time: float = 0.0
    max_time: float = 0.0
    rows_read: int = 0
    rows_kept: int = 0
    rows_bad_shape: int = 0
    rows_skipped_unparsable: int = 0
    rows_duration_defaulted: int = 0
    rows_start_defaulted: int = 0


@dataclass
class SimulationData:
    events: list[SimulationEvent] = field(default_factory=list)
    report: LoadReport = field(default_factory=LoadReport)
    _last_accessed: int = -1

    @classmethod
    def load(
        cls,
        filename: str | Path,
        max_events: int | None = DATA_INITIAL_CHUNK_LENGTH,
    ) -> "SimulationData":
        data = cls()
        rep = data.report

        with Path(filename).open("r", encoding="utf-8", errors="replace") as fh:
            header = fh.readline()
            if not header:
                raise ValueError("error reading the events data file: empty")

            meta = fh.readline()
            if not meta:
                raise ValueError("error reading the events data file: no metadata row")

            row = meta.split(",")
            if not 5 <= len(row) <= 6:
                raise ValueError("events data must contain 5 or 6 columns")

            declared, ok = qt_to_double(row[0].strip())
            if not ok or declared <= 0:
                raise ValueError("events number must be a number >= 0")
            rep.declared_events = int(declared)

            rep.min_time, ok = qt_to_double(row[1].strip())
            if not ok or rep.min_time < 0:
                raise ValueError("min simulation time must be a number >= 0")

            rep.max_time, ok = qt_to_double(row[2].strip())
            if not ok or rep.max_time <= 0:
                raise ValueError("max simulation time must be a number > 0")

            limit = max_events if max_events is not None else float("inf")
            while rep.rows_read < limit:
                line = fh.readline()
                if not line:
                    break
                rep.rows_read += 1

                row = line.rstrip("\n").split(",")
                if not row:
                    continue
                if not 5 <= len(row) <= 6:
                    rep.rows_bad_shape += 1
                    continue

                duration, duration_ok = qt_to_double(row[3].strip())
                start_time, start_ok = qt_to_double(row[4].strip())
                fails = -1 if len(row) < 6 else qt_to_int(row[5].strip())

                # Original: skip only when BOTH fail.
                if not duration_ok and not start_ok:
                    rep.rows_skipped_unparsable += 1
                    continue
                if not duration_ok:
                    rep.rows_duration_defaulted += 1
                if not start_ok:
                    rep.rows_start_defaulted += 1

                data.events.append(
                    SimulationEvent(
                        case_id=row[0].strip(),
                        begin_actor=row[1].strip(),
                        end_actor=row[2].strip(),
                        transition_time=duration,
                        start_time=start_time,
                        fails=fails,
                    )
                )
                rep.rows_kept += 1

        return data

    def event_at(self, i: int) -> SimulationEvent | None:
        if 0 <= i < len(self.events):
            self._last_accessed = i
            return self.events[i]
        return None

    def restart(self) -> None:
        self._last_accessed = -1

    def __len__(self) -> int:
        return len(self.events)
