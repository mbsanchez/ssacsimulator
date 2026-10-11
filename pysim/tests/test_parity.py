"""Regression tests pinning the ported semantics.

These do NOT prove parity with the Qt binary — that requires building and
running the original, which is a separate step (see README). What they pin is
that the port's behaviour matches the C++ source as read, and that the
published dataset produces the documented numbers. If a later refactor (e.g.
the deadline-driven engine) changes any of these, it has diverged.

Run:  python -m pytest tests/ -q      (or: python tests/test_parity.py)
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import pytest

from ssac import BusinessProcessModel, FailType, SimulationData, SimulationEngine
from ssac.numeric import f32, to_ulonglong

DATA = Path(os.environ.get("SSAC_DATA", Path(__file__).resolve().parents[2] / "DataSets I4.0"))
PG = DATA / "bosch_pl_tm_model.pg"
TD = DATA / "test_cases_0-100m.td"

requires_data = pytest.mark.skipif(
    not (PG.exists() and TD.exists()),
    reason=f"dataset not found under {DATA}; set SSAC_DATA",
)


# ---- numeric helpers ---------------------------------------------------

def test_to_ulonglong_truncates_at_dot():
    assert to_ulonglong("1183165") == 1183165
    assert to_ulonglong("673862.0") == 673862
    assert to_ulonglong("0.0") == 0


def test_float32_thresholds_differ_from_double():
    """The original computes `time * 1.3f` in binary32. For the thresholds to
    be reproducible we must do the same; this pins that we are not silently
    using double precision."""
    assert f32(f32(19.0) * f32(1.3)) != 19.0 * 1.3


# ---- model loading -----------------------------------------------------

@requires_data
def test_model_loads_without_errors():
    model, errors = BusinessProcessModel.load(PG)
    assert errors == [], errors
    assert model.process_name == "BOSH Production Line using Trimmed Mean"
    assert model.throughout_time == 6420.0
    assert model.total_cases == 1_183_165
    assert model.begin_actor == "BEGIN"
    assert model.end_actors == ["END"]


@requires_data
def test_model_shape():
    model, _ = BusinessProcessModel.load(PG)
    assert len(model.actors) == 54
    assert len(model.edges) == 53
    all_edges = [e for v in model.edges.values() for e in v.values()]
    assert len(all_edges) == 285
    assert sum(1 for e in all_edges if e.show) == 84


@requires_data
def test_begin_actor_cases_match_total():
    """The original raises an error when they disagree; they agree here."""
    model, _ = BusinessProcessModel.load(PG)
    assert model.actors["BEGIN"].cases == model.total_cases


@requires_data
def test_forty_five_edges_have_zero_reference_time():
    """A zero reference time makes the station threshold 0, so ANY positive
    transition duration flags the station as failing. This is the reason
    STATION_FAILURE is the only detector that fires on this dataset."""
    model, _ = BusinessProcessModel.load(PG)
    zero = [e for v in model.edges.values() for e in v.values() if e.time == 0.0]
    assert len(zero) == 45
    for e in zero:
        assert model.station_threshold(e) == 0.0


# ---- event loading -----------------------------------------------------

@requires_data
def test_event_loading_respects_original_chunk_limit():
    data = SimulationData.load(TD)
    assert len(data) == 100_000
    assert data.report.declared_events == 100_000
    assert data.report.min_time == 6.0
    assert data.report.max_time == 3240.0
    assert data.report.rows_bad_shape == 0
    assert data.report.rows_skipped_unparsable == 0


@requires_data
def test_time_conversion_matches_cpp_cast():
    data = SimulationData.load(TD)
    ev = data.events[0]
    assert ev.start_time_ms == int(ev.start_time * 60 * 1000)
    assert ev.transition_time_ms == int(ev.transition_time * 60 * 1000)


def test_malformed_row_is_kept_when_only_one_field_fails(tmp_path):
    """`if(!durationOk && !startTimeOk)` — AND, not OR. A row with a garbage
    duration but a valid start time is kept with duration 0.0. Faithful to the
    original even though it looks like a bug."""
    f = tmp_path / "x.td"
    f.write_text(
        "Id,source,target,duration,start,prediction\n"
        "3,0.0,10.0,0.0,0.0,-1\n"
        "1,A,B,GARBAGE,5.0,-1\n"      # duration fails, start ok -> KEPT
        "2,A,B,1.0,GARBAGE,-1\n"      # start fails, duration ok -> KEPT
        "3,A,B,GARBAGE,GARBAGE,-1\n"  # both fail -> SKIPPED
    )
    data = SimulationData.load(f)
    assert len(data) == 2
    assert data.report.rows_skipped_unparsable == 1
    assert data.report.rows_duration_defaulted == 1
    assert data.report.rows_start_defaulted == 1
    assert data.events[0].transition_time == 0.0
    assert data.events[0].start_time == 5.0


# ---- engine behaviour --------------------------------------------------

@requires_data
def test_run_reproduces_documented_detections():
    model, _ = BusinessProcessModel.load(PG)
    data = SimulationData.load(TD)
    engine = SimulationEngine(model, data)
    stats = engine.run()

    assert engine.detection_counts() == {
        "PREDICTED_FAILURE": 0,
        "STATION_FAILURE": 39,
        "GLOBAL_FAILURE": 0,
        "STATION_DEGRADED": 0,   # new detector, off by default
    }
    assert stats.events_processed == 100_000
    assert stats.pieces_entered == 10_295
    assert stats.pieces_completed == 6_715
    assert stats.final_pieces_in_system == 3_580
    assert stats.clock_regressions == 0
    assert stats.unknown_actor == 0
    assert stats.unknown_edge == 0


@requires_data
def test_predicted_failure_absent_because_dataset_has_no_positives():
    """Not a port defect: this file's `prediction` column holds only -1 and 0.
    Across all four shipped .td files there are 15 rows with prediction == 1
    (0 / 0 / 3 / 12), all of them the first event of their case."""
    data = SimulationData.load(TD)
    assert {e.fails for e in data.events} == {-1, 0}


@requires_data
def test_global_detector_is_unreachable_on_this_dataset():
    """Mean piece lifetime is ~636 min against a threshold of 7062 min, an
    order of magnitude below. The global self-* detector cannot fire here."""
    model, _ = BusinessProcessModel.load(PG)
    data = SimulationData.load(TD)
    engine = SimulationEngine(model, data)
    engine.run()

    assert model.global_threshold == pytest.approx(7062.0)
    assert model.objects_count == 6_715
    assert model.time_count_mean == pytest.approx(635.63, abs=0.01)
    assert model.time_count_mean < model.global_threshold / 10


@requires_data
def test_detections_are_all_station_type_and_ordered():
    model, _ = BusinessProcessModel.load(PG)
    data = SimulationData.load(TD)
    engine = SimulationEngine(model, data)
    engine.run()

    assert all(d.type is FailType.STATION_FAILURE for d in engine.detections)
    times = [d.sim_time_ms for d in engine.detections]
    assert times == sorted(times)


def test_mean_of_empty_counter_is_nan_not_an_exception():
    """C++ divides by zero and gets inf/nan; we must not raise."""
    model = BusinessProcessModel()
    assert math.isnan(model.time_count_mean)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))


# ---- fast path vs. original loop ---------------------------------------

def _fingerprint(engine):
    return {
        "detections": [(d.type, d.sim_time_ms, d.event_index, d.stations) for d in engine.detections],
        "decisions": [(d.t_min, d.trigger, d.action, tuple(d.errors)) for d in engine.decisions],
        "lifetimes": engine.lifetimes,
        "stats": engine.stats,
        "global": (engine.model.objects_count, engine.model.time_count),
    }


@requires_data
@pytest.mark.parametrize("scenario", ["plain", "fault+planner+per_station"])
def test_fast_path_is_identical_to_original_loop(scenario):
    """The fast path steps only pieces heading to an end node. It must give
    exactly the same detections, decisions, piece lifetimes and stats as the
    original loop that steps every piece on every tick."""
    from ssac.intervention import Fault
    from ssac.planning import RuleBasedPlanner

    data = SimulationData.load(TD)

    def run(step_all):
        model, _ = BusinessProcessModel.load(PG)
        if scenario == "plain":
            eng = SimulationEngine(model, data, step_all_pieces=step_all)
        else:
            eng = SimulationEngine(
                model, data, step_all_pieces=step_all,
                faults=[Fault("L0_S2", 3.0, 600.0)],
                planner=RuleBasedPlanner(),
                detectors=("legacy", "per_station"),
            )
        eng.run()
        return _fingerprint(eng)

    fast, slow = run(False), run(True)
    for key in fast:
        assert fast[key] == slow[key], key
