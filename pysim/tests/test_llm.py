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


def test_schema_restricts_stations_to_eligible():
    s = response_schema(["A", "B1"])
    assert s["properties"]["act"]["items"]["properties"]["station"]["enum"] == ["A", "B1"]


def test_maintain_maps_to_maintenance(model):
    fake = FakeModel({"act": [{"station": "A", "action": "maintain"}], "reason": "x"})
    p = LLMPlanner(fake, repair_min=45)
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == [Maintenance("A", 45)]
    assert p.calls[0].acted_on == ["A"] and p.calls[0].problems == []


def test_reroute_uses_the_free_twin_chosen_by_code(model):
    fake = FakeModel({"act": [{"station": "B1", "action": "reroute_and_maintain"}], "reason": "x"})
    acts = LLMPlanner(fake).plan(ctx(model, InterventionState(model), 0.0, ["B1"]))
    assert acts == [Reroute("B1", "B2", 1.0), Maintenance("B1", 60.0)]


def test_reroute_without_twin_is_downgraded_and_recorded(model):
    fake = FakeModel({"act": [{"station": "A", "action": "reroute_and_maintain"}], "reason": "x"})
    p = LLMPlanner(fake)
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == [Maintenance("A", 60.0)]
    assert any("downgraded" in x for x in p.calls[0].problems)


def test_empty_act_means_no_action(model):
    p = LLMPlanner(FakeModel({"act": [], "reason": "noise"}))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A", "B1"])) == []
    assert p.calls[0].reason == "noise"


def test_invalid_json_is_recorded_not_swallowed(model):
    p = LLMPlanner(FakeModel("this is not json"))
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == []
    assert p.calls[0].problems == ["invalid JSON"]


def test_ineligible_and_duplicate_stations_are_rejected(model):
    fake = FakeModel({"act": [{"station": "C", "action": "maintain"},
                              {"station": "A", "action": "maintain"},
                              {"station": "A", "action": "maintain"}], "reason": "x"})
    p = LLMPlanner(fake)
    assert p.plan(ctx(model, InterventionState(model), 0.0, ["A"])) == [Maintenance("A", 60.0)]
    probs = p.calls[0].problems
    assert any("not eligible" in x for x in probs) and any("duplicate" in x for x in probs)


def test_no_call_when_nothing_is_eligible(model):
    fake = FakeModel({"act": [], "reason": ""})
    st = InterventionState(model)
    st.apply(Maintenance("A", 60.0), 0.0)
    assert LLMPlanner(fake).plan(ctx(model, st, 10.0, ["A", "BEGIN"])) == []
    assert fake.seen == []


def test_cooldown_applies_after_acting(model):
    fake = FakeModel({"act": [{"station": "A", "action": "maintain"}], "reason": "x"})
    p = LLMPlanner(fake, cooldown_min=240)
    st = InterventionState(model)
    p.plan(ctx(model, st, 0.0, ["A"]))
    p.plan(ctx(model, InterventionState(model), 100.0, ["A"]))
    assert len(fake.seen) == 1


def test_prompt_describes_twins_and_state(model):
    fake = FakeModel({"act": [], "reason": ""})
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
    with pytest.raises(LLMError, match="connection refused"):
        OllamaClient().chat([{"role": "user", "content": "x"}])


# ---- C2: retrieval-augmented planner -------------------------------------

def test_memory_counts_alarms_in_windows():
    from ssac.rag_planner import OperationalMemory
    m = OperationalMemory()
    for t in (0, 50, 100, 1000):
        m.add_alarm(float(t), "STATION_FAILURE", ("A", "BEGIN"))
    assert m.count("A", 0, 100) == 3
    assert m.count("A", 101, 2000) == 1
    assert "BEGIN" not in m.alarm_times


def test_c2_prompt_carries_retrieved_knowledge(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel({"act": [], "reason": ""})
    p = RAGPlanner(fake, baseline_per_min={"A": 0.5 / 60})
    st = InterventionState(model)
    for t in (0.0, 30.0, 60.0):
        p.plan(ctx(model, st, t, ["A"]))
    system, user = fake.seen[-1][0][0]["content"], fake.seen[-1][0][1]["content"]
    assert "RETRIEVED KNOWLEDGE" in system and "RETRIEVED KNOWLEDGE" in user
    assert "3 in the last 2 h" in user
    assert "normal rate in fault-free operation: 0.50/h" in user
    assert "t=30: alarm STATION_FAILURE flagged A" in user


def test_c2_flags_self_inflicted_load(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel({"act": [], "reason": ""})
    st = InterventionState(model)
    st.apply(Reroute("B1", "B2"), 0.0)
    RAGPlanner(fake).plan(ctx(model, st, 10.0, ["B2"]))
    assert "rerouting the load of B1 ONTO B2" in fake.seen[0][0][1]["content"]


def test_c2_reports_repair_outcomes(model):
    from ssac.rag_planner import RAGPlanner
    fake = FakeModel({"act": [], "reason": ""})
    p = RAGPlanner(fake, cooldown_min=0)
    st = InterventionState(model)
    for t in (10.0, 20.0, 30.0):                  # 3 alarms before the repair
        p.plan(ctx(model, st, t, ["A"]))
    st.apply(Maintenance("A", 60.0), 40.0)        # repair 40 -> 100
    for t in (110.0, 400.0):                      # 1 alarm in the 2 h after
        p.plan(ctx(model, st, t, ["A"]))
    user = fake.seen[-1][0][1]["content"]
    assert "repaired at t=40: 3 alarms in the 2 h before, 1 in the 2 h after" in user
    assert "you applied MAINTENANCE A (60 min)" in user


def test_c1_prompt_has_no_retrieved_knowledge(model):
    fake = FakeModel({"act": [], "reason": ""})
    LLMPlanner(fake).plan(ctx(model, InterventionState(model), 0.0, ["A"]))
    assert "RETRIEVED" not in fake.seen[0][0][0]["content"] + fake.seen[0][0][1]["content"]
