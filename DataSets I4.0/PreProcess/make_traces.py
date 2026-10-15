#!/usr/bin/env python3
"""Python 3 port of PreProcessTestData.py and createTestFileChunk.py (2020).

Same logic, without Windows paths, interactive prompts or the Keras failure
predictor (whose model file is not in the repository): the `prediction` column
is -1 in every row, which only affects the predicted-failure detector.

    python make_traces.py events RAW_DIR            # RAW_DIR/test_date.csv -> RAW_DIR/test_date_events.td
    python make_traces.py chunk RAW_DIR SKIP ROWS OUT.td
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def get_station(column: str) -> str:
    return "_".join(column.split("_")[0:2])


def time_to_min(tm: str) -> float:
    return round(float(tm) * 10 * 60, 2)


def events(raw: Path) -> None:
    out_path = raw / "test_date_events.td"
    rows: set[tuple] = set()          # drop_duplicates
    out: list[tuple] = []
    with (raw / "test_date.csv").open() as fh:
        reader = csv.reader(fh)
        header = next(reader)
        n = 0
        for row in reader:
            case_id = source = target = None
            start_v1 = start_v2 = None
            for col, v1 in zip(header, row):
                if col == "Id":
                    case_id = str(int(v1))
                    continue
                if col == "L3_S51_D4263" and source and case_id and start_v1 > 0:
                    rec = (case_id, source, "END", 0.0, start_v1, -1)
                    if rec not in rows:
                        rows.add(rec); out.append(rec)
                    continue
                if not v1:
                    continue
                if not source:
                    source = get_station(col)
                    start_v1 = time_to_min(v1)
                else:
                    target = get_station(col)
                    start_v2 = time_to_min(v1)
                if case_id and source and target and start_v1 and start_v2:
                    if source == target and start_v1 == start_v2:
                        target = start_v2 = None
                        continue
                    rec = (case_id, source, target, round(start_v2 - start_v1, 10), start_v1, -1)
                    if rec not in rows:
                        rows.add(rec); out.append(rec)
                    source, start_v1 = target, start_v2
                    target = start_v2 = None
            n += 1
            if n % 100_000 == 0:
                print(f"{n} cases, {len(out)} events", flush=True)
    out.sort(key=lambda r: (r[4], int(r[0])))
    with out_path.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Id", "source", "target", "duration", "start", "prediction"])
        w.writerows(out)
    print(f"Events: {len(out)}; min time {out[0][4]}; max time {out[-1][4]}")


def chunk(raw: Path, skip: int, nrows: int, dest: Path) -> None:
    with (raw / "test_date_events.td").open() as fh:
        reader = csv.reader(fh)
        header = next(reader)
        data = list(reader)
    first = skip - 2 if skip > 0 else 0       # pandas skiprows=range(1, skip-1) keeps skip-2 rows out
    part = data[first:first + nrows]
    starts = [float(r[4]) for r in part]
    summary = [" " + str(len(part)), str(min(starts)), str(max(starts)), "0", "0", "-1"]
    part.sort(key=lambda r: (float(r[4]), int(r[0])))
    with dest.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerow(summary)
        w.writerows(part)
    print(f"{dest.name}: {len(part)} events, start {min(starts)}..{max(starts)}")


if __name__ == "__main__":
    if sys.argv[1] == "events":
        events(Path(sys.argv[2]))
    else:
        chunk(Path(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), Path(sys.argv[5]))
