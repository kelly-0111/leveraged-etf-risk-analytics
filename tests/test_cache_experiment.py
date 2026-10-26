"""etf_risk.cache_experiment without Spark or Redis: the workload's exact hit rates (also as the
real cache realizes them), the plan's structure, the keys the experiment owns and deletes, and the
monitors' parsing. The driver itself is validated by dry runs (docs/result-cache-experiment.md).

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import random
import sys
from collections import Counter

import pytest

from cache_fakes import FakeRedis, FakeRedisError
from etf_risk import cache, cache_experiment as e3, runs, summary
from run_fakes import write_run

SMALL = e3.Settings(rounds=2, block_size=30, n_size=6, f_phase=6, warmups=12)


def per_query(requests):
    return Counter(r["query"] for r in requests)


def test_the_key_space_is_every_query_with_every_non_empty_ticker_subset():
    assert len(e3.SUBSETS) == 31 and len({tuple(s) for s in e3.SUBSETS}) == 31
    assert len(e3.KEY_SPACE) == 93 and len(set(e3.KEY_SPACE)) == 93


@pytest.mark.parametrize("hit_rate", [0.0, 0.5, 0.8, 0.9])
def test_a_block_has_exactly_its_designed_hit_rate_and_is_balanced(hit_rate):
    reqs = e3.hit_rate_requests(random.Random(7), 30, hit_rate)
    sources = e3.designed_sources(reqs)
    assert len(reqs) == 30 and sources.count("cache") == round(30 * hit_rate)
    assert set(per_query(reqs).values()) == {10}


@pytest.mark.parametrize("n, hit_rate", [(30, 2 / 3), (30, 0.95), (30, 0.7), (10, 0.5)])
def test_a_hit_rate_that_is_not_exact_or_balanced_is_refused(n, hit_rate):
    with pytest.raises(ValueError):
        e3.hit_rate_requests(random.Random(7), n, hit_rate)


@pytest.mark.parametrize("hit_rate", [0.0, 0.5, 0.9])
def test_the_real_cache_realizes_the_designed_hit_rate(hit_rate):
    """Through ResultCache on an empty fake Redis, with the identity summary.py builds."""
    reqs = e3.hit_rate_requests(random.Random(3), 30, hit_rate)
    rc = cache.ResultCache(FakeRedis(), errors=(FakeRedisError,))
    realized = []
    for r in reqs:
        q = summary.QUERIES[r["query"]]
        ident = cache.identity(run_digest="a" * 64, query=r["query"], sql=q.sql, engine="pyspark x",
                               params=cache.normalize_params(q.params, {"tickers": r["tickers"]}))
        realized.append(rc.get_or_compute(ident, lambda: {"columns": [], "rows": []})[1])
    assert realized == e3.designed_sources(reqs)
    assert realized.count("cache") / 30 == hit_rate


def test_the_plan_is_deterministic_by_seed():
    assert e3.plan_blocks(5, SMALL) == e3.plan_blocks(5, SMALL)
    assert e3.plan_blocks(5, SMALL) != e3.plan_blocks(6, SMALL)


def test_even_rounds_run_the_forward_order_and_odd_rounds_its_exact_reverse():
    blocks = e3.plan_blocks(1, e3.Settings())
    forward = ["W0", "R0", "W50", "R50", "W90", "R90", "N", "F"]
    assert e3.forward_order(e3.Settings()) == forward
    for k in range(6):
        labels = [e3.block_label(b) for b in blocks if b["round"] == k]
        assert labels == (forward if k % 2 == 0 else forward[::-1])
    assert len(blocks) == 49 and len({b["id"] for b in blocks}) == 49
    assert blocks[0]["config"] == "L" and blocks[0]["round"] == -1 and blocks[0]["id"] == "b00-L"
    assert e3.designed_sources(blocks[0]["requests"]) == ["spark"] * 30 and len(blocks[0]["warmups"]) == 12


def test_the_lead_in_can_be_left_out():
    blocks = e3.plan_blocks(1, e3.Settings(lead_in=False))
    assert len(blocks) == 48 and blocks[0]["config"] == "W"


def test_each_r_block_has_a_w_control_with_the_identical_requests_and_warmups():
    blocks = e3.plan_blocks(1, SMALL)
    for r in [b for b in blocks if b["config"] == "R"]:
        (w,) = [b for b in blocks if b["config"] == "W" and b["round"] == r["round"] and b["pair"] == r["pair"]]
        assert w["requests"] == r["requests"] and w["warmups"] == r["warmups"] and "hit_rate" not in w


def test_n_runs_the_first_requests_of_each_query_in_the_zero_percent_sequence():
    blocks = e3.plan_blocks(1, SMALL)
    for k in (0, 1):
        r0 = next(b for b in blocks if b["round"] == k and b.get("hit_rate") == 0.0)
        n = next(b for b in blocks if b["round"] == k and b["config"] == "N")
        assert n["requests"] == [r for q in e3.QUERIES for r in [x for x in r0["requests"] if x["query"] == q][:2]]


def test_a_plan_without_the_zero_rate_is_refused():
    with pytest.raises(ValueError):
        e3.plan_blocks(1, e3.Settings(hit_rates=(0.5, 0.9)))


def test_f_has_three_equal_phases_over_one_key_per_query():
    f = next(b for b in e3.plan_blocks(1, SMALL) if b["config"] == "F")
    assert len(f["phases"]) == 3 and all(p == f["phases"][0] for p in f["phases"])
    assert set(per_query(f["phases"][0]).values()) == {2} and len({e3._rk(r) for r in f["phases"][0]}) == 3
    assert f["requests"] == [r for p in f["phases"] for r in p]


def test_warm_processes_get_balanced_warmups_starting_with_the_full_ticker_set():
    for b in e3.plan_blocks(1, SMALL):
        if b["config"] == "N":
            assert b["warmups"] == []
            continue
        assert len(b["warmups"]) == 12 and set(per_query(b["warmups"]).values()) == {4}
        firsts = [next(r for r in b["warmups"] if r["query"] == q) for q in e3.QUERIES]
        assert all(r["tickers"] == sorted(summary.TICKERS) for r in firsts)


def test_the_experiments_key_is_the_key_summary_writes(tmp_path):
    repo = tmp_path / "repo"
    folder = write_run(repo / "data" / "run-4")
    registry = repo / "docs" / "accepted-runs.json"
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"format": 1, "runs": [runs.registry_entry(folder, approved_on="2026-10-26",
                                                                              registry=registry)]}))
    redis = FakeRedis()
    service = summary.Service(registry=registry, result_cache=cache.ResultCache(redis, errors=(FakeRedisError,)),
                              execute=lambda f, sql, p: {"columns": [["x", "bigint"]], "rows": [[1]]})
    r = service.handle({"query": "comparison", "run": str(folder), "params": {"tickers": ["tsla", "AAPL"]}})
    assert r["status"] == "ok"
    expected = e3.key_of("comparison", ["AAPL", "TSLA"], digest=runs.folder_digest(folder), engine=summary.engine())
    assert list(redis.data) == [expected]


class KeyClient:
    """exists, dbsize and delete over a dict, as redis-py answers them."""

    def __init__(self, keys):
        self.data = dict.fromkeys(keys, b"v")

    def exists(self, *keys):
        return sum(k in self.data for k in keys)

    def dbsize(self):
        return len(self.data)

    def delete(self, *keys):
        return sum(self.data.pop(k, None) is not None for k in keys)


def test_only_the_named_keys_are_deleted_and_foreign_keys_are_counted():
    client = KeyClient(["ours-1", "ours-2", "theirs"])
    assert e3.foreign_keys(client, ["ours-1", "ours-2", "ours-3"]) == 1
    assert e3.delete_keys(client, ["ours-1", "ours-3"]) == 1
    assert sorted(client.data) == ["ours-2", "theirs"]
    assert e3.delete_keys(client, []) == 0


def test_a_container_event_keeps_its_action_and_project_but_no_name():
    line = json.dumps({"status": "start", "Action": "start", "id": "abc", "time": 5,
                       "Actor": {"ID": "abc", "Attributes": {"name": "someone-else-1",
                                                             "com.docker.compose.project": "elsewhere"}}})
    event = e3.parse_container_event(line, "etf-risk-jobs")
    assert event == {"action": "start", "ours": False, "time": 5}
    assert e3.parse_container_event("not json", "etf-risk-jobs") is None


def test_the_container_monitor_counts_events_in_a_window():
    lines = [json.dumps({"Action": a, "Actor": {"Attributes": {"com.docker.compose.project": p}}})
             for a, p in [("start", "etf-risk-jobs"), ("start", "other"), ("die", "other")]]
    script = "import sys; print(" + repr("\n".join(lines)) + ")"
    monitor = e3.ContainerEvents("etf-risk-jobs", command=[sys.executable, "-c", script])
    monitor.start()
    monitor.join(timeout=10)
    assert monitor.count(0, float("inf"), ours=False) == 2 and monitor.count(0, float("inf"), ours=True) == 1
    assert monitor.count(-2, -1, ours=False) == 0


@pytest.mark.parametrize("text, expected", [
    ("Note: No thermal warning level has been recorded\nNote: No performance warning level has been recorded\n",
     {"thermal_warning": None, "performance_warning": None, "cpu_speed_limit": None}),
    ("Thermal warning level: 2\nPerformance warning level: 1\n",
     {"thermal_warning": 2, "performance_warning": 1, "cpu_speed_limit": None}),
    ("CPU_Speed_Limit \t= 70\n", {"thermal_warning": None, "performance_warning": None, "cpu_speed_limit": 70}),
])
def test_pmset_therm_is_parsed(text, expected):
    assert e3.parse_therm(text) == expected


def test_the_host_window_gives_extremes_and_swap_traffic():
    sampler = e3.HostSampler(0.01)
    sampler.samples = [{"mono": 1.0, "pressure_level": 1, "swap_out_bytes": 100, "swap_in_bytes": 10,
                        "thermal_warning": None, "performance_warning": None},
                       {"mono": 2.0, "pressure_level": 4, "swap_out_bytes": 150, "swap_in_bytes": 90,
                        "thermal_warning": None, "performance_warning": None},
                       {"mono": 9.0, "pressure_level": 1, "swap_out_bytes": 999, "swap_in_bytes": 999,
                        "thermal_warning": 3, "performance_warning": None}]
    assert sampler.window(0.5, 2.5) == {"samples": 2, "max_pressure_level": 4, "thermal_warning": None,
                                         "performance_warning": None, "swap_out_bytes": 50, "swap_in_bytes": 80}
    assert sampler.window(20, 30) == {"samples": 0}


READY = dict(formal=True, host={"power_source": "AC Power", "lid_closed": False, "memory_pressure": 2},
             other_containers=0, our_services=["redis"], redis_ok=True, foreign=0,
             therm={"thermal_warning": None, "performance_warning": None}, clean=True)


def test_a_ready_host_passes_the_preflight():
    assert e3.preflight_problems(**READY) == []


@pytest.mark.parametrize("change, problem", [
    (dict(host={**READY["host"], "power_source": "Battery Power"}), "power"),
    (dict(host={**READY["host"], "lid_closed": None}), "lid"),
    (dict(other_containers=1), "other projects"),
    (dict(other_containers=None), "other projects"),
    (dict(our_services=["redis", "mysql"]), "other services"),
    (dict(redis_ok=False), "PING"),
    (dict(foreign=3), "does not own"),
    (dict(host={**READY["host"], "memory_pressure": 4}), "critical"),
    (dict(therm={"thermal_warning": 1, "performance_warning": None}), "warning"),
    (dict(clean=False), "clean worktree"),
])
def test_the_preflight_names_what_blocks_a_batch(change, problem):
    problems = e3.preflight_problems(**{**READY, **change})
    assert len(problems) == 1 and problem in problems[0]


def test_a_dirty_worktree_only_blocks_a_formal_batch():
    assert e3.preflight_problems(**{**READY, "formal": False, "clean": False}) == []


def test_the_plan_command_turns_the_lead_in_off_only_when_asked(tmp_path, monkeypatch):
    plans = {}
    monkeypatch.setattr(e3, "make_plan", lambda seed, settings: plans.setdefault("s", settings) and {"blocks": [], "keys": []})
    e3.main(["plan", "--seed", "1", "--out", str(tmp_path / "dry-run" / "a")])
    assert plans.pop("s").lead_in is True
    e3.main(["plan", "--seed", "1", "--no-lead-in", "--out", str(tmp_path / "dry-run" / "b")])
    assert plans.pop("s").lead_in is False
