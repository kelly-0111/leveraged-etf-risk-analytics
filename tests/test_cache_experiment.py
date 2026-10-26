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
    assert len(blocks) == 56 and len({b["id"] for b in blocks}) == 56


def test_the_lead_in_is_a_full_forward_round_of_its_own_before_round_0():
    blocks = e3.plan_blocks(1, e3.Settings())
    lead = [b for b in blocks if b.get("lead_in")]
    assert blocks[:8] == lead and all(b["round"] == -1 for b in lead)
    assert [e3.block_label(b) for b in lead] == e3.forward_order(e3.Settings())
    assert [b["id"] for b in lead[:2]] == ["b00-lead-W0", "b01-lead-R0"]
    r0 = next(b for b in blocks if b["round"] == 0 and b.get("hit_rate") == 0.0)
    assert lead[1]["requests"] != r0["requests"] and not any(b.get("lead_in") for b in blocks[8:])


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


VM_STAT = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                4589.
Pages stored in compressor:             1172538.
Decompressions:                      1515682285.
Compressions:                        1585740227.
Pageins:                               49262910.
Pageouts:                               1562003.
Swapins:                               80132854.
Swapouts:                              84015127.
"""


def test_vm_stat_gives_the_page_size_and_its_four_counters_by_their_own_names():
    assert e3.parse_vm_stat(VM_STAT) == {"page_size": 16384, "pageins": 49262910, "pageouts": 1562003,
                                         "swapins": 80132854, "swapouts": 84015127}


def test_a_counter_vm_stat_does_not_print_is_none():
    assert e3.parse_vm_stat("") == {"page_size": None, "pageins": None, "pageouts": None, "swapins": None,
                                    "swapouts": None}
    assert e3.parse_vm_stat(VM_STAT.replace("Swapouts", "Swap outs"))["swapouts"] is None


def _sample(mono, pressure, pageins, swapins, busy, idle, load, thermal=None):
    return {"mono": mono, "pressure_level": pressure, "page_size": 16384, "pageins": pageins, "pageouts": 7,
            "swapins": swapins, "swapouts": 3, "cpu_busy_s": busy, "cpu_idle_s": idle, "load_1m": load,
            "thermal_warning": thermal, "performance_warning": None}


def test_the_host_window_gives_extremes_paging_swap_and_load():
    sampler = e3.HostSampler(0.01)
    sampler.samples = [_sample(1.0, 1, 100, 10, busy=50.0, idle=150.0, load=2.0),
                       _sample(2.0, 4, 160, 10, busy=80.0, idle=220.0, load=3.0),
                       _sample(9.0, 1, 999, 999, busy=999.0, idle=999.0, load=9.0, thermal=3)]
    assert sampler.window(0.5, 2.5) == {
        "samples": 2, "max_pressure_level": 4, "thermal_warning": None, "performance_warning": None,
        "page_size": 16384, "pageins": 60, "pageouts": 0, "swapins": 0, "swapouts": 0,
        "load_1m_mean": 2.5, "load_1m_max": 3.0, "cpu_busy_share": 0.3}
    assert sampler.window(20, 30) == {"samples": 0}


def test_a_counter_missing_from_one_sample_is_taken_from_the_samples_that_have_it():
    sampler = e3.HostSampler(0.01)
    sampler.samples = [_sample(1.0, 1, 100, 10, 50.0, 150.0, 2.0), _sample(2.0, 1, 130, 12, 60.0, 160.0, 2.0),
                       {**_sample(3.0, 1, None, None, 70.0, 170.0, 2.0), "page_size": None}]
    window = sampler.window(0, 5)
    assert (window["pageins"], window["swapins"], window["page_size"]) == (30, 2, 16384)
    sampler.samples = [{**s, "swapins": None} for s in sampler.samples]
    assert sampler.window(0, 5)["swapins"] is None


def test_a_host_sample_names_vm_stats_counters_and_never_psutils_sin_and_sout(monkeypatch):
    outputs = {"sysctl": "1\n", "vm_stat": VM_STAT, "pmset": "Note: No thermal warning level has been recorded\n"}
    monkeypatch.setattr(e3, "_run", lambda *argv: outputs[argv[0]])
    sample = e3.read_host_sample()
    assert sample["pressure_level"] == 1 and sample["swapins"] == 80132854 and sample["pageins"] == 49262910
    assert sample["cpu_busy_s"] > 0 and sample["cpu_idle_s"] > 0 and sample["load_1m"] >= 0
    assert not set(e3.PSUTIL_PAGING) & set(sample)


def test_the_block_readings_leave_out_psutils_mislabelled_counters(monkeypatch):
    from etf_risk.jobs import harness
    monkeypatch.setattr(harness, "host_state", lambda: {"available_bytes": 5, "swap_used_bytes": 6,
                                                        "swap_in_bytes": 7, "swap_out_bytes": 8,
                                                        "power_source": "AC Power"})
    assert e3.host_reading() == {"available_bytes": 5, "swap_used_bytes": 6, "power_source": "AC Power"}


@pytest.mark.skipif(sys.platform != "darwin", reason="the mapping is macOS's")
def test_psutils_sin_and_sout_are_vm_stats_pageins_and_pageouts_on_macos():
    """The reason for the correction of 2026-10-26: each psutil counter lies between two vm_stat
    readings of Pageins (Pageouts) taken around it. Fails if psutil changes its mapping."""
    import subprocess
    import psutil

    def vm():
        return e3.parse_vm_stat(subprocess.run(["vm_stat"], capture_output=True, text=True, check=True).stdout)
    before, swap, after = vm(), psutil.swap_memory(), vm()
    page = before["page_size"]
    assert before["pageins"] * page <= swap.sin <= after["pageins"] * page
    assert before["pageouts"] * page <= swap.sout <= after["pageouts"] * page


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


# The settle

class FakeProcess:
    def __init__(self, pid, created=100.0, name="java", cmdline=("java", "org.apache.spark.deploy.SparkSubmit")):
        self.pid, self._created, self._name, self._cmdline = pid, created, name, list(cmdline)

    def name(self):
        return self._name

    def cmdline(self):
        return self._cmdline

    def create_time(self):
        return self._created


class Script:
    """scan() returns the next list of live processes; clock() advances by each poll's sleep."""

    def __init__(self, scans):
        self.scans, self.now, self.ended = list(scans), 10.0, []

    def scan(self):
        return self.scans.pop(0) if len(self.scans) > 1 else self.scans[0]

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds

    def end(self, processes, rescan):
        self.ended += [p.pid for p in processes]
        return {"terminated": [p.pid for p in processes], "killed": [], "remaining": []}


def test_processes_that_exit_within_the_grace_are_recorded_with_their_timing():
    jvm = FakeProcess(7)
    s = Script([[jvm], [jvm], []])
    r = e3.settle("e3:b:x", exited_mono=10.0, root_pid=1, grace=15, poll=0.25,
                  scan=s.scan, clock=s.clock, sleep=s.sleep, end=s.end, owned=lambda p, c: True)
    assert r["settled_after_s"] == 0.5 and r["survivors"] == [] and r["cleanup"] is None and r["confirmed_clean"]
    (seen,) = r["seen"]
    assert (seen["pid"], seen["kind"], seen["first_seen_s"], seen["last_seen_s"], seen["gone_by_s"]) == (
        7, "spark_jvm", 0.0, 0.25, 0.5)
    assert s.ended == []


def test_a_survivor_after_the_grace_is_recorded_and_ended_once_its_ownership_is_verified():
    jvm = FakeProcess(7)
    s = Script([[jvm]])
    r = e3.settle("e3:b:x", exited_mono=10.0, root_pid=1, grace=1.0, poll=0.25,
                  scan=s.scan, clock=s.clock, sleep=s.sleep, end=s.end, owned=lambda p, c: c == 100.0)
    assert r["settled_after_s"] is None and [x["pid"] for x in r["survivors"]] == [7]
    assert s.ended == [7] and r["unverified"] == [] and r["confirmed_clean"]


def test_a_survivor_that_remains_after_cleanup_is_not_confirmed_clean():
    jvm = FakeProcess(7)
    s = Script([[jvm]])
    stubborn = lambda procs, rescan: {"terminated": [7], "killed": [7], "remaining": [7]}
    r = e3.settle("e3:b:x", exited_mono=10.0, root_pid=1, grace=0.5, poll=0.25,
                  scan=s.scan, clock=s.clock, sleep=s.sleep, end=stubborn, owned=lambda p, c: True)
    assert not r["confirmed_clean"] and r["cleanup"]["remaining"] == [7]


def test_a_survivor_whose_ownership_cannot_be_verified_is_never_signalled():
    reused = FakeProcess(7, created=999.0)
    s = Script([[reused]])
    r = e3.settle("e3:b:x", exited_mono=10.0, root_pid=1, grace=0.5, poll=0.25,
                  scan=s.scan, clock=s.clock, sleep=s.sleep, end=s.end, owned=lambda p, c: False)
    assert s.ended == [] and [x["pid"] for x in r["unverified"]] == [7] and not r["confirmed_clean"]


def _marked_child(marker, seconds):
    import os
    import subprocess
    from etf_risk.jobs.processes import MARKER_ENV
    return subprocess.Popen([sys.executable, "-c", f"import time; time.sleep({seconds})"],
                            env={**os.environ, MARKER_ENV: marker})


def test_a_real_marked_process_that_exits_is_seen_and_found_gone():
    import secrets
    import time
    marker = f"e3:test:{secrets.token_hex(4)}"
    child = _marked_child(marker, 0.6)
    r = e3.settle(marker, exited_mono=time.monotonic(), root_pid=0, grace=10, poll=0.1)
    child.wait(timeout=10)
    assert r["confirmed_clean"] and r["survivors"] == [] and r["settled_after_s"] is not None
    assert [x["pid"] for x in r["seen"]] == [child.pid] and r["seen"][0]["gone_by_s"] is not None


def test_a_real_survivor_is_ended_and_confirmed():
    import secrets
    import time
    marker = f"e3:test:{secrets.token_hex(4)}"
    child = _marked_child(marker, 60)
    r = e3.settle(marker, exited_mono=time.monotonic(), root_pid=0, grace=0.5, poll=0.1)
    assert [x["pid"] for x in r["survivors"]] == [child.pid] and r["cleanup"]["terminated"] == [child.pid]
    import psutil
    assert r["confirmed_clean"] and not psutil.pid_exists(child.pid)    # psutil reaped it: Popen.wait would say 0
