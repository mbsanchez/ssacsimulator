"""Tests for the LLM client and planner, with a fake model (no Ollama needed)."""

from __future__ import annotations

import io
import json

import pytest

from ssac import BusinessProcessModel, FailType
from ssac.actions import Maintenance, Reroute
from ssac.engine import Detection
from ssac.intervention import InterventionState
from ssac.llm import LLMResponse, OllamaClient
from ssac.llm_planner import LLMPlanner, response_schema
from ssac.planning import PlanningContext
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


class FakeModel:
    model = "fake"

    def __init__(self, reply):
        self.reply = reply          # dict, str (raw), or callable(messages, schema)
        self.seen: list[tuple[list[dict], dict]] = []

    def chat(self, messages, schema=None):
        self.seen.append((messages, schema))
        r = self.reply(messages, schema) if callable(self.reply) else self.reply
        raw = r if isinstance(r, str) else json.dumps(r)
        try:
            parsed, ok = json.loads(raw), True
        except json.JSONDecodeError:
            parsed, ok = None, False
        return LLMResponse(raw, parsed, ok, 0.01, 10, 10, False, f"k{len(self.seen)}")


def ctx(model, st, t, stations):
    det = Detection(FailType.STATION_FAILURE, int(t * 60000), 0, "", stations=tuple(stations))
    return PlanningContext(t, det, model, find_twins(model), st)


def reply(**stations):
    """{"A": ("degraded", "maintain"), ...} -> model output in the v2 format."""
    return {"stations": {k: {"verdict": v, "action": a} for k, (v, a) in stations.items()}, "reason": "r"}


def test_schema_requires_a_verdict_for_every_eligible_station():
    s = response_schema(["A", "B1"])
    st = s["properties"]["stations"]
    assert set(st["properties"]) == {"A", "B1"}
    assert st["required"] == ["A", "B1"]
    item = st["properties"]["A"]["properties"]
    assert "degraded" in item["verdict"]["enum"] and "none" in item["action"]["enum"]


def test_maintain_maps_to_maintenance(model):
    p = LLMPlanner(FakeModel(reply(A=("degraded", "maintain"))), repair_min=45)
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == [Maintenance("A", 45)]
    assert p.calls[0].acted_on == ["A"] and p.calls[0].problems == []
    assert p.calls[0].verdicts == {"A": "degraded"}


def test_reroute_uses_the_free_twin_chosen_by_code(model):
    fake = FakeModel(reply(B1=("degraded", "reroute_and_maintain")))
    acts = LLMPlanner(fake).plan(ctx(model, InterventionState(model), 0.0, ["B1"]))
    assert acts == [Reroute("B1", "B2", 1.0), Maintenance("B1", 60.0)]


def test_reroute_without_twin_is_downgraded_and_recorded(model):
    p = LLMPlanner(FakeModel(reply(A=("degraded", "reroute_and_maintain"))))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == [Maintenance("A", 60.0)]
    assert any("downgraded" in x for x in p.calls[0].problems)


@pytest.mark.parametrize("verdict", ["normal", "self_inflicted", "insufficient_evidence"])
def test_action_inconsistent_with_verdict_is_dropped(model, verdict):
    p = LLMPlanner(FakeModel(reply(A=(verdict, "maintain"))))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == []
    assert any("dropped" in x for x in p.calls[0].problems)
    assert p.calls[0].acted_on == []


def test_none_action_means_no_action(model):
    p = LLMPlanner(FakeModel(reply(A=("normal", "none"), B1=("degraded", "none"))))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A", "B1"])) == []
    assert p.calls[0].problems == []


def test_invalid_json_is_recorded_not_swallowed(model):
    p = LLMPlanner(FakeModel("this is not json"))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == []
    assert p.calls[0].problems == ["invalid JSON"]


def test_ineligible_and_missing_stations_are_reported(model):
    p = LLMPlanner(FakeModel(reply(C=("degraded", "maintain"), A=("degraded", "maintain"))))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A", "B1"])) == [Maintenance("A", 60.0)]
    probs = p.calls[0].problems
    assert any("not eligible" in x for x in probs)
    assert any("no verdict for B1" in x for x in probs)


def test_no_call_when_nothing_is_eligible(model):
    fake = FakeModel(reply())
    st = InterventionState(model)
    st.apply(Maintenance("A", 60.0), 0.0)
    assert LLMPlanner(fake).plan(ctx(model, st, 10.0, ["A", "BEGIN"])) == []
    assert fake.seen == []


def test_cooldown_applies_after_acting(model):
    fake = FakeModel(reply(A=("degraded", "maintain")))
    p = LLMPlanner(fake, cooldown_min=240)
    p.plan(ctx(model, InterventionState(model), 0.0, ["A"]))
    p.plan(ctx(model, InterventionState(model), 100.0, ["A"]))
    assert len(fake.seen) == 1


def test_prompt_describes_twins_and_state(model):
    fake = FakeModel(reply())
    st = InterventionState(model)
    st.apply(Maintenance("C", 60.0), 0.0)
    LLMPlanner(fake).plan(ctx(model, st, 5.0, ["A", "B1"]))
    user = fake.seen[0][0][1]["content"]
    assert "A: no twin" in user
    assert "B1: free twin available (B2)" in user
    assert "Stations under repair now: C." in user


# ---- client cache --------------------------------------------------------

class _FakeHTTP(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_client_caches_identical_requests(tmp_path, monkeypatch):
    calls = []

    def fake_urlopen(req, timeout):
        calls.append(json.loads(req.data))
        return _FakeHTTP(json.dumps({"message": {"content": '{"act": [], "reason": "ok"}'},
                                     "prompt_eval_count": 5, "eval_count": 3}).encode())

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    c = OllamaClient(cache_path=tmp_path / "cache.sqlite")
    msgs = [{"role": "user", "content": "hi"}]
    r1, r2 = c.chat(msgs), c.chat(msgs)
    assert len(calls) == 1
    assert not r1.cached and r2.cached and r1.parsed == r2.parsed
    assert calls[0]["options"]["temperature"] == 0.0

    # a fresh client on the same file still hits the cache
    r3 = OllamaClient(cache_path=tmp_path / "cache.sqlite").chat(msgs)
    assert r3.cached and len(calls) == 1


def test_client_raises_on_transport_error(monkeypatch):
    import urllib.error
    from ssac.llm import LLMError

    def boom(req, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", boom)
    with pytest.raises(LLMError, match="after 3 attempts.*connection refused"):
        OllamaClient(retries=2, retry_wait_s=0).chat([{"role": "user", "content": "x"}])


def test_client_retries_transient_failures(monkeypatch):
    import urllib.error
    attempts = []

    def flaky(req, timeout):
        attempts.append(1)
        if len(attempts) < 3:
            raise urllib.error.URLError("temporarily unavailable")
        return _FakeHTTP(json.dumps({"message": {"content": '{"ok": true}'}}).encode())

    monkeypatch.setattr("urllib.request.urlopen", flaky)
    c = OllamaClient(retries=4, retry_wait_s=0)
    assert c.chat([{"role": "user", "content": "x"}]).parsed == {"ok": True}
    assert len(attempts) == 3 and c.stats["retries"] == 2


# ---- C2: retrieval-augmented planner -------------------------------------

def test_memory_counts_alarms_in_windows():
    from ssac.rag_planner import OperationalMemory
    m = OperationalMemory()
    for t in (0, 50, 100, 1000):
        m.add_alarm(float(t), "STATION_FAILURE", ("A", "BEGIN"))
    assert m.count("A", 0, 100) == 3
    assert m.count("A", 101, 2000) == 1
    assert "BEGIN" not in m.alarm_times


def test_c2_says_history_is_too_short_early_on(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel(reply())
    p = RAGPlanner(fake, baseline_per_min={"A": 0.5 / 60}, min_history_h=8)
    st = InterventionState(model)
    for t in (0.0, 30.0, 60.0):
        p.plan(ctx(model, st, t, ["A"]))
    user = fake.seen[-1][0][1]["content"]
    assert "too short to compare" in user and "3 alarms so far" in user
    assert "RETRIEVED KNOWLEDGE" in fake.seen[-1][0][0]["content"]


def test_c2_compares_observed_with_expected_alarms(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel(reply())
    p = RAGPlanner(fake, baseline_per_min={"A": 0.5 / 60}, min_history_h=8, cooldown_min=0)
    st = InterventionState(model)
    p.plan(ctx(model, st, 0.0, ["A"]))           # start of operation
    for t in range(1500, 1620, 20):              # 6 alarms within 2 h, 25 h in
        p.plan(ctx(model, st, float(t), ["A"]))
    user = fake.seen[-1][0][1]["content"]
    assert "last 2 h: 6 alarms; its normal rate predicts 1.0" in user
    assert "last 24 h: 6 alarms; its normal rate predicts 12.0" in user
    assert "[A] (no twin)" in user


def test_c2_marks_stations_that_never_alarmed_normally(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel(reply())
    p = RAGPlanner(fake, baseline_per_min={}, min_history_h=0, cooldown_min=0)
    st = InterventionState(model)
    p.plan(ctx(model, st, 0.0, ["A"]))
    p.plan(ctx(model, st, 60.0, ["A"]))
    assert "never alarmed in fault-free operation" in fake.seen[-1][0][1]["content"]


def test_c2_flags_self_inflicted_load(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel(reply())
    st = InterventionState(model)
    st.apply(Reroute("B1", "B2"), 0.0)
    RAGPlanner(fake).plan(ctx(model, st, 10.0, ["B2"]))
    assert "rerouting the load of B1 ONTO B2" in fake.seen[0][0][1]["content"]


def test_c2_reports_repair_outcomes_digested(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel(reply())
    p = RAGPlanner(fake, cooldown_min=0)
    st = InterventionState(model)
    for t in (10.0, 20.0, 30.0):                  # 3 alarms before the repair
        p.plan(ctx(model, st, t, ["A"]))
    st.apply(Maintenance("A", 60.0), 40.0)        # repair 40 -> 100
    for t in (110.0, 400.0):                      # 1 alarm in the 2 h after
        p.plan(ctx(model, st, t, ["A"]))
    user = fake.seen[-1][0][1]["content"]
    assert "after the repair at t=40 its alarms dropped (3 in the 2 h before, 1 in the 2 h after)" in user
    assert "you applied MAINTENANCE A (60 min)" in user


def test_c1_prompt_has_no_retrieved_knowledge(model):
    fake = FakeModel(reply())
    LLMPlanner(fake).plan(ctx(model, InterventionState(model), 0.0, ["A"]))
    assert "RETRIEVED" not in fake.seen[0][0][0]["content"] + fake.seen[0][0][1]["content"]


# ---- hybrid: change test triages, LLM vetoes ------------------------------

def _eager_detector():
    """An adaptive detector that flags a station on its first alarm."""
    from ssac.planning import AdaptiveRulePlanner
    return AdaptiveRulePlanner(warmup_min=0, min_count=1, alpha=0.5, prior_alarms=0.001)


def test_hybrid_does_not_call_the_llm_without_candidates(model):
    from ssac.hybrid_planner import HybridPlanner
    from ssac.planning import AdaptiveRulePlanner
    fake = FakeModel(reply())
    p = HybridPlanner(fake, detector=AdaptiveRulePlanner(warmup_min=480))
    assert p.plan(ctx(model, InterventionState(model), 10.0, ["A", "B1"])) == []
    assert fake.seen == []


def test_hybrid_asks_only_about_detector_candidates_and_acts_on_confirmation(model):
    from ssac.hybrid_planner import HybridPlanner
    fake = FakeModel(lambda msgs, schema: reply(**{s: ("degraded", "maintain")
                                                   for s in schema["properties"]["stations"]["required"]}))
    p = HybridPlanner(fake, detector=_eager_detector())
    acts = p.plan(ctx(model, InterventionState(model), 0.0, ["A"]))
    assert acts == [Maintenance("A", 60.0)]
    assert fake.seen[0][1]["properties"]["stations"]["required"] == ["A"]
    assert p.detector._last_acted["A"] == 0.0
    assert "statistical change detector" in fake.seen[0][0][0]["content"]


def test_hybrid_veto_blocks_action_and_snoozes_the_station(model):
    from ssac.hybrid_planner import HybridPlanner
    fake = FakeModel(reply(A=("self_inflicted", "none")))
    p = HybridPlanner(fake, detector=_eager_detector(), veto_snooze_min=120)
    st = InterventionState(model)
    assert p.plan(ctx(model, st, 0.0, ["A"])) == []
    assert p.detector._snoozed["A"] == 120.0
    assert p.plan(ctx(model, st, 60.0, ["A"])) == []      # snoozed: not asked again
    assert len(fake.seen) == 1


def test_detector_respects_snooze(model):
    st = InterventionState(model)
    before = _eager_detector()
    before.snooze("A", 100.0)
    assert before.candidates(ctx(model, st, 50.0, ["A"])) == []
    after = _eager_detector()
    after.snooze("A", 100.0)
    assert after.candidates(ctx(model, st, 150.0, ["A"])) == ["A"]


def test_context_control_skips_stations_receiving_rerouted_load(model):
    from ssac.planning import ContextAdaptiveRulePlanner
    det = ContextAdaptiveRulePlanner(warmup_min=0, min_count=1, alpha=0.5, prior_alarms=0.001)
    st = InterventionState(model)
    st.apply(Reroute("B1", "B2"), 0.0)
    assert det.plan(ctx(model, st, 0.0, ["B2", "A"])) == [Maintenance("A", 60.0)]
