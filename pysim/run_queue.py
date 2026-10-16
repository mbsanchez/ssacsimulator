#!/usr/bin/env python3
"""Run a queue of resumable llm_sweep.py jobs on the Claude Agent SDK, one at a
time, waiting for the 5-hour session limit to reset and stopping at a weekly
limit. Each job is complete when its rows file has `rows` rows per planner.

    nohup caffeinate -i -m -s .venv/bin/python run_queue.py > results/queue.log 2>&1 &
"""

from __future__ import annotations

import csv
import datetime as dt
import re
import subprocess
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = str(HERE / ".venv" / "bin" / "python")
SDK = ["--backend", "agent-sdk", "--model", "claude-fable-5-1"]
# (results dir, extra arguments, planners) in order of priority (results/dev_log.md, 2026-10-16)
P = ["--analyze", "processing"]
RULES = ["noop", "rules_cal", "rules_adapt", "rules_adapt_ctx", "rules_cal_rt", "rules_adapt_ctx_rt",
         "rules_burst", "rules_burst_ctx"]
SENS = [("sens_k5", ["--factor", "5"]), ("sens_r15", ["--repair-min", "15"]), ("sens_a0", ["--congestion", "0"])]
SENS_LATE = [("sens_r240", ["--repair-min", "240"]), ("sens_stop", ["--mode", "stop"]), ("sens_a1", ["--congestion", "1"])]
JOBS = ([(f"results/{d}", P + x, RULES + ["hybrid"]) for d, x in SENS]
        + [("results/newtraces", P + ["--new-traces"], ["noop", "llm_c2"]),
           ("results/commoncause", P + ["--common-cause"], RULES + ["hybrid"])]
        + [(f"results/replica_{i}", P + ["--replica", str(i)], ["noop", "hybrid"]) for i in (1, 2, 3)]
        + [(f"results/{d}", P + x, RULES + ["hybrid"]) for d, x in SENS_LATE])


def rows_per_planner(extra: list[str]) -> int:
    per_trace = 19 if "--common-cause" in extra else 73     # fault scenarios + 1 fault-free
    return (5 if "--new-traces" in extra else 3) * per_trace


def complete(d: Path, planners: list[str], extra: list[str]) -> bool:
    f = d / "llm_sweep_rows.csv"
    if not f.exists():
        return False
    n = Counter(r["planner"].split(":")[0] for r in csv.DictReader(f.open()))
    return all(n[p] >= rows_per_planner(extra) for p in planners)


def wait_for_reset(text: str) -> bool:
    """Sleep until the session limit resets; False if the limit is weekly."""
    if re.search(r"weekly|reached your Fable limit|usage credits", text, re.I):
        return False
    m = re.findall(r"resets (\d{1,2})(?::(\d{2}))?\s*(am|pm)", text)
    now = dt.datetime.now()
    wait = 600.0
    if m:
        h, mi, ap = m[-1]
        h = int(h) % 12 + (12 if ap == "pm" else 0)
        t = now.replace(hour=h, minute=int(mi or 0), second=0, microsecond=0)
        if t < now - dt.timedelta(minutes=5):
            t += dt.timedelta(days=1)
        wait = max(0.0, (t - now).total_seconds()) + 120
    print(f"{now:%m-%d %H:%M} session limit: waiting {wait / 60:.0f} min", flush=True)
    time.sleep(wait)
    return True


def main() -> int:
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--backend-ollama":
        global SDK
        SDK = ["--backend", "ollama"]
        sys.argv.pop(1)
        global JOBS     # the 7B hybrid: same conditions, rows in <dir>/qwen (merged by stats.read_all)
        JOBS = [(f"{d}/qwen", x, ["noop", "hybrid"]) for d, x, p in JOBS
                if "--replica" not in x and "--new-traces" not in x]
    only = sys.argv[1:]          # optional: results dirs to run, e.g. results/newtraces
    for path, extra, planners in JOBS:
        if only and path not in only:
            continue
        d = HERE / path
        d.mkdir(parents=True, exist_ok=True)
        while not complete(d, planners, extra):
            print(f"{dt.datetime.now():%m-%d %H:%M} running {path}", flush=True)
            log = d / "run.log"
            with log.open("a") as fh:
                rc = subprocess.run([PY, "llm_sweep.py", *SDK, *extra, "--planners", *planners, "--results", str(d)],
                                    cwd=HERE, stdout=fh, stderr=subprocess.STDOUT).returncode
            if complete(d, planners, extra):
                break
            tail = log.read_text()[-3000:]
            if rc != 0 and "limit" in tail:
                if not wait_for_reset(tail):
                    print(f"{dt.datetime.now():%m-%d %H:%M} weekly limit reached in {path}: stopping", flush=True)
                    return 1
            elif rc != 0:
                print(f"{dt.datetime.now():%m-%d %H:%M} {path} failed (rc {rc}); see {log}", flush=True)
                return 1
        print(f"{dt.datetime.now():%m-%d %H:%M} done {path}", flush=True)
    print(f"{dt.datetime.now():%m-%d %H:%M} queue complete", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
