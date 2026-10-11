"""Unit tests for the Plan / Execute layer, on a tiny synthetic line:

    BEGIN -> A -> {B1, B2} -> C -> END        (B1 and B2 are twins)
"""

from __future__ import annotations

import pytest

from ssac import BusinessProcessModel, FailType
from ssac.actions import Maintenance, NoOp, Reroute, Restore, validate
from ssac.engine import Detection
from ssac.events import SimulationEvent
from ssac.intervention import EffectModel, Fault, InterventionState
from ssac.planning import (
    CalibratedRulePlanner,
    PlanningContext,
    RuleBasedPlanner,
    poisson_threshold,
)
from ssac.topology import find_twins

PG = """process:tiny
actors:+BEGIN,A,B1,B2,C,-END
process_througout_time:20
total_cases:100
transitions:
BEGIN=A;0.0;100.0;1
A=B1;2.0;50.0;1!B2;2.0;50.0;1
B1=C;5.0;50.0;1
B2=C;5.0;50.0;1
C=END;0.0;100.0;1
"""


@pytest.fixture
def model(tmp_path):
    f = tmp_path / "tiny.pg"
    f.write_text(PG)
    m, errors = BusinessProcessModel.load(f)
    assert errors == []
    return m


@pytest.fixture
def twins(model):
    return find_twins(model)


# processing times for the tiny line; chosen equal to the test durations so
# that additive effects are easy to read: a x3 fault on B1 adds 2 * 5 = 10.
TAU = {"A": 2.0, "B1": 5.0, "B2": 5.0, "C": 1.0}


def ev(case, b, e, dur, start=0.0):
    return SimulationEvent(case, b, e, dur, start)


# ---- topology ----------------------------------------------------------

def test_twins_are_found_both_ways(twins):
    assert [t.twin for t in twins["B1"]] == ["B2"]
    assert [t.twin for t in twins["B2"]] == ["B1"]
    assert "A" not in twins and "C" not in twins


# ---- faults ------------------------------------------------------------

def test_fault_scales_only_its_station_and_only_while_scheduled(model):
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, start_min=10.0)])
    assert st.transform(ev("1", "B1", "C", 5.0), t_min=5.0).transition_time == 5.0
    assert st.transform(ev("1", "B1", "C", 5.0), t_min=10.0).transition_time == 15.0
    assert st.transform(ev("2", "B2", "C", 5.0), t_min=10.0).transition_time == 5.0
    assert st.transform(ev("3", "A", "B1", 2.0), t_min=10.0).transition_time == 2.0


def test_unchanged_event_is_returned_as_is(model):
    st = InterventionState(model, service_times=TAU)
    e = ev("1", "A", "B1", 2.0)
    assert st.transform(e, 0.0) is e


# ---- reroute -----------------------------------------------------------

def test_reroute_diverts_the_whole_trajectory(model):
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 0.0)], effects=EffectModel(congestion_alpha=0.5))
    st.apply(Reroute("B1", "B2", 1.0), 0.0)

    first = st.transform(ev("1", "A", "B1", 2.0), 1.0)
    assert (first.begin_actor, first.end_actor) == ("A", "B2")

    second = st.transform(ev("1", "B1", "C", 5.0), 2.0)
    assert (second.begin_actor, second.end_actor) == ("B2", "C")
    # leaves from B2: no B1 fault, but B2 absorbs 100% extra load -> x1.5
    assert second.transition_time == pytest.approx(7.5)
    assert st.stats.pieces_rerouted == 1


def test_fractional_reroute_is_deterministic(model):
    def run():
        st = InterventionState(model, service_times=TAU)
        st.apply(Reroute("B1", "B2", 0.5), 0.0)
        return [st.transform(ev(str(i), "A", "B1", 2.0), 0.0).end_actor for i in range(200)]
    a, b = run(), run()
    assert a == b
    assert 60 < a.count("B2") < 140


# ---- maintenance -------------------------------------------------------

def test_maintenance_stop_mode_adds_wait_then_clears_fault(model):
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 0.0)],
                           effects=EffectModel(maintenance_mode="stop"))
    st.apply(Maintenance("B1", 60.0), 100.0)
    during = st.transform(ev("1", "B1", "C", 5.0), 120.0)
    assert during.transition_time == pytest.approx(5.0 * 3 + 40.0)   # faulty + waits 40
    after = st.transform(ev("2", "B1", "C", 5.0), 170.0)
    assert after.transition_time == 5.0


def test_fault_starting_after_repair_is_not_cleared(model):
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, start_min=500.0)])
    st.apply(Maintenance("B1", 60.0), 100.0)
    assert st.transform(ev("1", "B1", "C", 5.0), 600.0).transition_time == 15.0


def test_reroute_lifts_when_repair_completes(model):
    st = InterventionState(model, service_times=TAU)
    st.apply(Reroute("B1", "B2", 1.0), 100.0)
    st.apply(Maintenance("B1", 60.0), 100.0)
    st.advance(150.0)
    assert "B1" in st.reroutes
    st.advance(160.0)
    assert "B1" not in st.reroutes
    assert isinstance(st.log[-1].action, Restore)


# ---- validator ---------------------------------------------------------

@pytest.mark.parametrize("action, fragment", [
    (Reroute("B1", "C"), "not a structural twin"),
    (Reroute("B1", "B1"), "itself"),
    (Reroute("B1", "B2", 0.0), "outside"),
    (Reroute("B1", "B2", 1.5), "outside"),
    (Reroute("X", "B2"), "unknown station"),
    (Reroute("END", "B2"), "unknown station"),
    (Restore("B1"), "no active reroute"),
    (Maintenance("ZZ"), "unknown station"),
    (Maintenance("A", 0.0), "positive"),
])
def test_validator_rejects(model, twins, action, fragment):
    errors = validate(action, model, twins, InterventionState(model, service_times=TAU), 0.0)
    assert any(fragment in e for e in errors), errors


def test_validator_rejects_chains_and_busy_targets(model, twins):
    st = InterventionState(model, service_times=TAU)
    st.apply(Reroute("B1", "B2"), 0.0)
    assert any("chain" in e for e in validate(Reroute("B2", "B1"), model, twins, st, 0.0))

    st2 = InterventionState(model, service_times=TAU)
    st2.apply(Maintenance("B2", 60.0), 0.0)
    assert any("under maintenance" in e for e in validate(Reroute("B1", "B2"), model, twins, st2, 10.0))
    assert any("already under maintenance" in e for e in validate(Maintenance("B2"), model, twins, st2, 10.0))


def test_validator_accepts_admissible_actions(model, twins):
    st = InterventionState(model, service_times=TAU)
    for a in (Reroute("B1", "B2", 0.5), Maintenance("A", 30.0), NoOp("ok")):
        assert validate(a, model, twins, st, 0.0) == []


# ---- planners ----------------------------------------------------------

def ctx(model, twins, st, t, stations, kind=FailType.STATION_DEGRADED):
    det = Detection(kind, int(t * 60000), 0, "", stations=tuple(stations))
    return PlanningContext(t, det, model, twins, st)


def test_poisson_threshold():
    assert poisson_threshold(0.1, 1e-3) == 3
    assert poisson_threshold(1.0, 1e-3) == 6
    assert poisson_threshold(4.0, 1e-3) == 12
    assert poisson_threshold(0.0, 1e-3) == 1


def test_naive_rules_reroute_to_twin_then_repair(model, twins):
    st = InterventionState(model, service_times=TAU)
    actions = RuleBasedPlanner(repair_min=45).plan(ctx(model, twins, st, 0.0, ["B1"]))
    assert actions == [Reroute("B1", "B2", 1.0), Maintenance("B1", 45)]


def test_naive_rules_repair_only_without_twin(model, twins):
    st = InterventionState(model, service_times=TAU)
    assert RuleBasedPlanner().plan(ctx(model, twins, st, 0.0, ["A"])) == [Maintenance("A", 60.0)]


def test_naive_rules_respect_cooldown(model, twins):
    st = InterventionState(model, service_times=TAU)
    p = RuleBasedPlanner(cooldown_min=120)
    assert p.plan(ctx(model, twins, st, 0.0, ["A"]))
    assert p.plan(ctx(model, twins, st, 100.0, ["A"])) == []


def test_calibrated_rules_wait_for_an_improbable_count(model, twins):
    st = InterventionState(model, service_times=TAU)
    # base rate 1 alarm / 120 min -> mean 1 per window -> threshold 6
    p = CalibratedRulePlanner({"A": 1 / 120}, window_min=120, alpha=1e-3)
    assert p.threshold("A") == 6
    for i in range(5):
        assert p.plan(ctx(model, twins, st, float(i), ["A"])) == []
    assert p.plan(ctx(model, twins, st, 5.0, ["A"])) == [Maintenance("A", 60.0)]


def test_calibrated_rules_forget_alarms_outside_the_window(model, twins):
    st = InterventionState(model, service_times=TAU)
    p = CalibratedRulePlanner({"A": 1 / 120}, window_min=120)
    for t in (0, 50, 100, 300, 350):
        assert p.plan(ctx(model, twins, st, float(t), ["A"])) == []


def test_adaptive_rules_do_nothing_during_warmup(model, twins):
    from ssac.planning import AdaptiveRulePlanner
    st = InterventionState(model, service_times=TAU)
    p = AdaptiveRulePlanner(warmup_min=480)
    for t in range(0, 400, 5):
        assert p.plan(ctx(model, twins, st, float(t), ["A"])) == []


def test_adaptive_rules_fire_on_a_rate_step_not_on_steady_noise(model, twins):
    from ssac.planning import AdaptiveRulePlanner
    st = InterventionState(model, service_times=TAU)
    p = AdaptiveRulePlanner(window_min=120, history_min=1440, warmup_min=480, cooldown_min=10_000)
    # steady noise: one alarm every 60 min for 20 h -> never fires
    acted = [a for t in range(0, 1200, 60) for a in p.plan(ctx(model, twins, st, float(t), ["A"]))]
    assert acted == []
    # step change: one alarm every 5 min -> fires within the window
    fired_at = None
    for t in range(1200, 1320, 5):
        if p.plan(ctx(model, twins, st, float(t), ["A"])):
            fired_at = t
            break
    assert fired_at is not None and fired_at < 1260


def test_adaptive_rules_are_causal(model, twins):
    """Feeding the same alarms must give the same decisions regardless of
    what comes later — the planner has no access to the future."""
    from ssac.planning import AdaptiveRulePlanner
    times = [float(t) for t in range(0, 1500, 7)]
    def decisions(upto):
        st = InterventionState(model, service_times=TAU)
        p = AdaptiveRulePlanner()
        return [bool(p.plan(ctx(model, twins, st, t, ["A"]))) for t in times[:upto]]
    assert decisions(100) == decisions(len(times))[:100]


def test_maintenance_contingency_mode_uses_slower_backup_not_the_fault(model):
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 0.0)],
                           effects=EffectModel(maintenance_mode="contingency", contingency_factor=1.5))
    st.apply(Maintenance("B1", 60.0), 100.0)
    assert st.transform(ev("1", "B1", "C", 5.0), 120.0).transition_time == pytest.approx(7.5)
    assert st.transform(ev("2", "B1", "C", 5.0), 170.0).transition_time == 5.0


def test_contingency_is_the_default(model):
    assert EffectModel().maintenance_mode == "contingency"


def test_maintaining_a_healthy_station_still_costs(model):
    st = InterventionState(model, service_times=TAU)
    st.apply(Maintenance("A", 60.0), 0.0)
    assert st.transform(ev("1", "A", "B1", 2.0), 10.0).transition_time == pytest.approx(3.0)


# ---- fault shapes ------------------------------------------------------

def test_step_fault_shape():
    f = Fault("S", 3.0, start_min=100.0)
    assert [f.factor_at(t) for t in (50, 100, 5000)] == [1.0, 3.0, 3.0]


def test_intermittent_fault_alternates():
    f = Fault("S", 3.0, start_min=0.0, shape="intermittent", on_min=60, off_min=120)
    assert f.factor_at(10) == 3.0
    assert f.factor_at(90) == 1.0
    assert f.factor_at(185) == 3.0     # second "on" period starts at 180


def test_drift_fault_ramps_linearly_then_holds():
    f = Fault("S", 3.0, start_min=0.0, shape="drift", ramp_min=600)
    assert f.factor_at(0) == 1.0
    assert f.factor_at(300) == pytest.approx(2.0)
    assert f.factor_at(600) == pytest.approx(3.0)
    assert f.factor_at(9000) == pytest.approx(3.0)


def test_repair_clears_any_shape(model):
    for shape in ("step", "intermittent", "drift"):
        st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 0.0, shape=shape, ramp_min=10)])
        st.apply(Maintenance("B1", 60.0), 0.0)
        assert st.fault_factor("B1", 61.0) == 1.0, shape


@pytest.mark.parametrize("kwargs", [{"shape": "zigzag"}, {"factor": 0.5}])
def test_invalid_faults_are_rejected(kwargs):
    with pytest.raises(ValueError):
        Fault("S", **{"factor": 3.0, "start_min": 0.0, **kwargs})


def test_invalid_maintenance_mode_is_rejected():
    with pytest.raises(ValueError):
        EffectModel(maintenance_mode="pray")


def test_effects_do_not_stretch_waiting_time(model):
    """A 10 000-min transition is mostly storage. A x3 fault adds 2 * tau_S to
    it, not 20 000 min. This is the bug the additive model exists to avoid."""
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 0.0)])
    assert st.transform(ev("1", "B1", "C", 10_000.0), 1.0).transition_time == pytest.approx(10_010.0)


def test_unknown_station_uses_default_service_time(model):
    from ssac.intervention import DEFAULT_SERVICE_MIN
    st = InterventionState(model, service_times={}, faults=[Fault("B1", 3.0, 0.0)])
    assert st.transform(ev("1", "B1", "C", 5.0), 1.0).transition_time == pytest.approx(5.0 + 2 * DEFAULT_SERVICE_MIN)


def test_estimate_service_times_ignores_storage_and_zeros(model):
    from ssac.intervention import estimate_service_times
    events = [ev("1", "B1", "C", d) for d in (0.0, 4.0, 6.0, 8.0, 5000.0)] + [ev("2", "A", "B1", 2.0)]
    assert estimate_service_times(model, events) == {"B1": 6.0, "A": 2.0}


def test_twin_only_control_ignores_stations_without_twin(model, twins):
    from ssac.planning import TwinOnlyRulePlanner
    st = InterventionState(model, service_times=TAU)
    acts = TwinOnlyRulePlanner(repair_min=30).plan(ctx(model, twins, st, 0.0, ["A", "B1"]))
    assert acts == [Reroute("B1", "B2", 1.0), Maintenance("B1", 30)]


def test_twin_only_control_skips_when_twin_is_busy(model, twins):
    from ssac.planning import TwinOnlyRulePlanner
    st = InterventionState(model, service_times=TAU)
    st.apply(Maintenance("B2", 60.0), 0.0)
    assert TwinOnlyRulePlanner().plan(ctx(model, twins, st, 10.0, ["B1"])) == []


def test_repair_does_not_clear_a_fault_that_begins_during_it(model):
    """Design v2: a repair clears only faults active when it starts. A fault
    beginning 12 min into a routine repair survives it."""
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 12.0)])
    st.apply(Maintenance("B1", 60.0), 0.0)
    assert st.fault_factor("B1", 61.0) == 3.0
    v1 = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 12.0)],
                           effects=EffectModel(repair_clears="begun_before_end"))
    v1.apply(Maintenance("B1", 60.0), 0.0)
    assert v1.fault_factor("B1", 61.0) == 1.0


def test_extras_log_records_every_addition(model):
    st = InterventionState(model, service_times=TAU, faults=[Fault("B1", 3.0, 0.0)])
    st.transform(ev("1", "B1", "C", 5.0), 1.0)
    st.transform(ev("2", "B1", "C", 5.0), 2.0)
    assert sum(x for _, x in st.extras) == pytest.approx(2 * 2 * TAU["B1"])


def test_onsets_are_stable_and_inside_margins():
    from ssac.onsets import onsets
    a = onsets("t.td", "S", "step", 0.0, 10_000.0)
    assert a == onsets("t.td", "S", "step", 0.0, 10_000.0)
    assert a != onsets("t.td", "S", "drift", 0.0, 10_000.0)
    assert len(a) == 3 and all(1440.0 <= x <= 10_000.0 - 1440.0 for x in a)
