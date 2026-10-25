"""The recovery harness's offline parts (etf_risk.jobs.harness): plans, deadlines, the
partition's owner from assignment events, worker reports, memory peaks by segment, the
cross-check SQL, fingerprints and the duration estimate. The batch itself needs the services and
the snapshot, and has not run: no formal experiment.

The cross-check SQL must stay the SQL validated on 2026-10-23 (docs/recovery-sql.md, section 6):
crosscheck.sql below its separator equals the document's SQL blocks, byte for byte.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import json
import re
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from etf_risk.jobs import harness
from etf_risk.jobs.events import read_events
from etf_risk.jobs.timing import DEFAULT_TIMING

REPO = Path(__file__).resolve().parents[1]
DEFAULTS = harness.Settings()


def test_a_plan_has_two_jobs_of_every_case_in_an_order_fixed_by_its_seed():
    """P1's preferred draft (2026-10-24): 2 jobs of each case in one batch, 28 in all."""
    jobs = harness.plan_jobs(DEFAULTS, seed=7)
    assert len(jobs) == 28 and Counter(jobs) == {case: 2 for case in harness.CASES}
    assert jobs == harness.plan_jobs(DEFAULTS, seed=7) != harness.plan_jobs(DEFAULTS, seed=8)


def test_the_deadlines_at_the_default_clock():
    """P3, revised: B plus twice the slowest step sum, rounded up to 5 s; K2, D1 and D2 count from
    their service's return, so no restart duration is assumed."""
    d = {case: harness.deadline_seconds(case, DEFAULT_TIMING, DEFAULTS) for case in harness.CASES}
    assert d == {"C0": 75, "W1": 90, "W2": 140, "W3": 140, "W4": 140, "W5a": 75, "W5b": 75, "W6": 140,
                 "W7": 170, "K1": 75, "K2": 125, "D1": 140, "D2": 140, "X1": 75}
    assert {case: harness.deadline_reference(case) for case in ("C0", "W3", "K2", "D1", "D2", "X1")} == {
        "C0": "submit", "W3": "injection", "K2": "restored", "D1": "restored", "D2": "restored", "X1": "injection"}


def test_w7_waits_for_the_later_of_the_takeover_and_the_end_of_the_stopped_tree():
    short = harness.Settings(w7_stop_s=10.0)
    assert harness.bound_to_next_run("W7", DEFAULT_TIMING, short) == 65.0          # the takeover decides
    assert harness.bound_to_next_run("W7", DEFAULT_TIMING, DEFAULTS) == 90.0 + 2 * 0.5 + 7.0


def assigned(mono, *partitions, pid=1):
    return {"event": "assigned", "mono": mono, "pid": pid, "partitions": [["t", p] for p in partitions]}


def test_the_owner_comes_from_the_assignment_events_of_live_workers_only():
    logs = {"A": [{"event": "started", "mono": 1}, assigned(2, 0)],
            "B": [{"event": "started", "mono": 3}, assigned(4)]}
    assert harness.owner(logs, {"A", "B"}) == "A"
    logs["A"].append({"event": "revoked", "mono": 5, "partitions": [["t", 0]]})
    logs["B"].append(assigned(6, 0))
    assert harness.owner(logs, {"A", "B"}) == "B"
    assert harness.owner(logs, {"A"}) is None                                    # B died holding it
    logs["B"].append({"event": "started", "mono": 7})                            # B restarted: holds nothing yet
    assert harness.owner(logs, {"A", "B"}) is None
    both = {"A": [assigned(1, 0)], "B": [assigned(2, 0)]}
    assert harness.owner(both, {"A", "B"}) is None                               # never guessed


def test_worker_reports_carry_the_logs_identity():
    logs = {"A": [{"event": "accepted", "store_id": "s" * 32, "worker_id": "A", "pid": 11, "job_id": 3, "attempt": 2,
                   "digest": "d" * 64}, {"event": "claimed", "job_id": 4}]}
    assert harness.worker_accepts(logs) == [("s" * 32, "A", 11, 3, 2, "d" * 64)]


def test_peaks_by_segment_keep_the_maximum_and_mark_a_lost_reading():
    book = harness.PeakBook()
    book.add("mysql", 300 * 2**20, 512 * 2**20, "mysql stop")                    # closes the first segment
    book.add("mysql", 200 * 2**20, 512 * 2**20, None)                            # restarted: a new, lower count
    peak = book.batch_peak("mysql")
    assert (peak["peak_bytes"], peak["incomplete"], peak["readings"]) == (300 * 2**20, False, 2)
    book.add("mysql", None, None, "end")
    assert book.batch_peak("mysql")["incomplete"] is True
    assert book.batch_peak("kafka")["incomplete"] is True                         # never read
    assert [harness.memory_verdict(f, DEFAULTS) for f in (None, 0.5, 0.91, 0.96)] == ["unknown", "ok", "flag", "stop"]


def doc_blocks() -> list[str]:
    doc = (REPO / "docs" / "recovery-sql.md").read_text()
    blocks = re.findall(r"^```sql\n(.*?)^```$", doc, flags=re.S | re.M)
    prefixes = ("-- The harness's records", "-- Q0.", "-- Q1.", "-- Q2.", "-- Q2b.", "-- Q3a.", "-- Q3b.")
    return [next(b for b in blocks if b.startswith(p)) for p in prefixes]


def test_crosscheck_sql_is_the_validated_sql_byte_for_byte():
    text = harness.CROSSCHECK_SQL.read_text()
    body = text.split("\n", next(i for i, line in enumerate(text.splitlines()) if harness._SEPARATOR.match(line)) + 1)[-1]
    assert body == "\n".join(doc_blocks())


def test_the_crosscheck_statements_come_in_order_with_their_names():
    names = [name for name, _ in harness.crosscheck_statements()]
    assert names == ["DDL", "DDL", "DDL", "Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b"]
    assert all(sql.rstrip().endswith(";") for _, sql in harness.crosscheck_statements())


def test_the_exported_fingerprint_counts_jobs_versions_attempts_and_renewals(tmp_path):
    (tmp_path / "jobs.json").write_text(json.dumps([{"version": 4}, {"version": 7}]))
    (tmp_path / "job_attempts.json").write_text(json.dumps([{"renewals": 2}, {"renewals": 1}, {"renewals": 2}]))
    assert harness.fingerprint_from_export(tmp_path) == {"n_jobs": 2, "sum_version": 11, "n_attempts": 3,
                                                         "sum_renewals": 5}


def test_settings_refuse_unknown_names_and_cases_and_survive_a_plan(tmp_path):
    with pytest.raises(ValueError, match="unknown settings"):
        harness.Settings.from_dict({"jobs_per_kase": 3})
    with pytest.raises(ValueError, match="unknown cases"):
        harness.Settings.from_dict({"cases": ["C0", "W9"]})
    plan = harness.make_plan(DEFAULTS, seed=1)
    again = json.loads(json.dumps(plan))
    assert harness.Settings.from_dict(again["settings"]) == DEFAULTS and len(again["jobs"]) == 28
    assert again["deadlines_s"]["W7"] == 170 and set(again["code"]) >= {"source_digest", "uv_lock_sha256"}


def test_the_estimate_of_the_preferred_draft_and_of_the_84_job_alternative():
    """Under Assumptions (none measured): 1,403 s for one job of each case; 2,986 s for the
    preferred batch of 28 jobs; 4,389 s for each of the alternative's two batches of 42."""
    result = harness.estimate(harness.make_plan(DEFAULTS, seed=1))
    per = result["per_case_s"]
    assert (per["C0"], per["W1"], per["W4"], per["W7"], per["K2"], per["D1"], per["D2"]) == (42, 74, 159, 159, 118, 116,
                                                                                            149)
    assert sum(per.values()) == 1403 and (result["jobs"], result["batch_s"]) == (28, 2 * 1403 + 180) == (28, 2986)
    alternative = harness.estimate(harness.make_plan(harness.Settings(jobs_per_case=3), seed=1))
    assert (alternative["jobs"], alternative["batch_s"]) == (42, 3 * 1403 + 180) == (42, 4389)    # twice: 8,778 s


def test_a_plan_states_its_purpose_and_a_preflight_keeps_the_listed_order():
    plan = harness.make_plan(DEFAULTS, seed=1, purpose="preflight", jobs=["C0", "W1", "D2"])
    assert (plan["purpose"], plan["order"], plan["jobs"]) == ("preflight", "as listed", ["C0", "W1", "D2"])
    assert set(plan["deadlines_s"]) == {"C0", "W1", "D2"}
    assert (harness.make_plan(DEFAULTS, seed=1)["purpose"], harness.make_plan(DEFAULTS, seed=1)["order"]) == (
        "formal", "shuffled")
    with pytest.raises(ValueError, match="purpose"):
        harness.make_plan(DEFAULTS, seed=1, purpose="trial")
    with pytest.raises(ValueError, match="unknown cases"):
        harness.make_plan(DEFAULTS, seed=1, purpose="preflight", jobs=["C0", "W9"])


def test_a_batch_runs_only_in_its_purposes_folder_and_a_formal_one_only_with_formal(tmp_path, capsys):
    """Refused before anything is made: no folder, no services."""
    for purpose in ("preflight", "formal"):
        harness.main(["plan", "--purpose", purpose, "--seed", "1", "--out", str(tmp_path / f"{purpose}.json")])
    unlabelled = json.loads((tmp_path / "formal.json").read_text())
    del unlabelled["purpose"]
    (tmp_path / "old.json").write_text(json.dumps(unlabelled))
    for plan, out, extra, message in (
            ("preflight.json", tmp_path / "formal" / "b1", [], "folder named preflight"),
            ("formal.json", tmp_path / "preflight" / "b2", ["--formal"], "folder named formal"),
            ("formal.json", tmp_path / "formal" / "b3", [], "needs --formal"),
            ("old.json", tmp_path / "formal" / "b4", ["--formal"], "names no purpose")):
        with pytest.raises(SystemExit):
            harness.main(["batch", "--plan", str(tmp_path / plan), "--out", str(out), *extra])
        assert message in capsys.readouterr().err and not out.exists()


# Arming, phases and the deadline observation, on a batch with no services

class FakeProc:
    """A worker's Popen as the harness reads it: alive until killed."""

    def __init__(self, pid):
        self.pid, self.code = pid, None

    def poll(self):
        return self.code

    def kill(self):
        self.code = -9


def offline_batch(tmp_path, **settings) -> harness.Batch:
    batch = harness.Batch(harness.make_plan(harness.Settings(**settings), seed=1), tmp_path / "batch")
    batch.procs = {"A": FakeProc(11), "B": FakeProc(22)}
    return batch


def log(batch, worker, *events):
    with open(batch.events_dir / f"{worker}.jsonl", "a") as f:
        f.writelines(json.dumps(e) + "\n" for e in events)


def test_arming_writes_only_the_owners_fault_file_and_leaves_the_partition_where_it_was(tmp_path):
    batch = offline_batch(tmp_path)
    log(batch, "A", {"event": "started", "pid": 11, "mono": 1}, assigned(2, 0, pid=11))
    log(batch, "B", {"event": "started", "pid": 22, "mono": 3}, assigned(4, pid=22))
    procs = dict(batch.procs)
    assert batch.wait_owner(timeout=1) == "A"
    assert batch.arm_fault(5, "W2", "A") == ("A", None)
    assert json.loads(batch.fault_file("A").read_text()) == {"point": "after_claim", "action": "kill"}
    assert not batch.fault_file("B").exists()
    assert batch.procs == procs and all(p.poll() is None for p in procs.values())    # nothing started or stopped
    assert batch.current_owner() == "A" and len(harness.events_named(batch.worker_logs()["A"], "assigned")) == 1
    armed = harness.events_named(read_events(batch.out / "harness.jsonl"), "armed")[-1]
    assert (armed["worker"], armed["point"], armed["action"], armed["owner_after"]) == ("A", "after_claim", "kill", "A")
    batch.fault_file("A").unlink()                                   # the W2 fault fired
    _, release = batch.arm_fault(6, "D2", "A")
    assert json.loads(batch.fault_file("A").read_text()) == {
        "point": "after_pipeline", "action": "hold", "release": str(release), "timeout_s": 630.0}


def test_a_fault_counts_only_after_this_jobs_delivery_and_is_missed_once_the_other_worker_claims(tmp_path):
    batch = offline_batch(tmp_path, phase_timeout_s=1.0, poll_s=0.05)
    log(batch, "A", {"event": "delivered", "job_id": 6, "mono": 1},
        {"event": "fault_injected", "point": "after_claim", "mono": 2})          # an earlier job's
    with pytest.raises(harness.PhaseMissed, match="timed out"):
        batch.wait_fault("A", 7, "after_claim")
    log(batch, "A", {"event": "delivered", "job_id": 7, "mono": 3},
        {"event": "claimed", "job_id": 7, "attempt": 1, "run_id": "job-7-attempt-1", "mono": 4},
        {"event": "fault_injected", "point": "after_claim", "mono": 5})
    assert batch.wait_fault("A", 7, "after_claim")["mono"] == 5
    slow = offline_batch(tmp_path / "slow", phase_timeout_s=60.0, poll_s=0.05)
    log(slow, "B", {"event": "delivered", "job_id": 8, "mono": 1},
        {"event": "claimed", "job_id": 8, "attempt": 1, "run_id": "job-8-attempt-1", "mono": 2})
    start = time.monotonic()
    with pytest.raises(harness.PhaseMissed, match="claimed by worker B, not the armed A"):
        slow.wait_fault("A", 8, "after_claim")
    assert time.monotonic() - start < 5                                          # not the 60 s phase timeout


class Statuses:
    """What a Tracker reads: job_status() returns the status the clock has reached in `timeline`
    ([(seconds from start, status)]); observe() returns that status, or fails (status None)."""

    def __init__(self, timeline, *, failing=False):
        self.start, self.timeline, self.failing = time.monotonic(), timeline, failing
        self.settings = harness.Settings(poll_s=0.01)
        self.observed = []

    def job_status(self, job_id):
        elapsed = time.monotonic() - self.start
        return [status for at, status in self.timeline if at <= elapsed][-1]

    def observe(self, job_id):
        t = time.monotonic()
        record = {"job_id": job_id, "observed_from_mono": t, "observed_to_mono": t,
                  "status": None if self.failing else self.job_status(job_id)}
        self.observed.append(record)
        return record


def track(fake, deadline_s, drain_s):
    tracker = harness.Tracker(fake, 1, fake.start + deadline_s, fake.start + deadline_s + drain_s)
    tracker.start()
    tracker.join(10)
    return tracker


def test_a_job_that_finishes_first_is_observed_at_completion_and_never_waits_out_its_deadline():
    fake = Statuses([(0, "running"), (0.1, "succeeded")])
    tracker = track(fake, deadline_s=30, drain_s=30)
    assert [o["status"] for o in fake.observed] == ["succeeded"] and tracker.final == "succeeded"
    assert tracker.finished_mono - fake.start < 5


def test_a_late_job_is_observed_once_at_its_deadline_and_followed_to_its_end():
    fake = Statuses([(0, "running"), (0.6, "succeeded")])
    tracker = track(fake, deadline_s=0.2, drain_s=5)
    assert [o["status"] for o in fake.observed] == ["running"] and tracker.final == "succeeded"
    assert fake.observed[0]["observed_from_mono"] >= tracker.deadline_mono          # Q2: late
    assert tracker.finished_mono >= fake.start + 0.6


def test_a_failed_observation_is_kept_and_never_repeated():
    fake = Statuses([(0, "running"), (0.5, "succeeded")], failing=True)
    tracker = track(fake, deadline_s=0.1, drain_s=5)
    assert [o["status"] for o in fake.observed] == [None] and tracker.final == "succeeded"   # Q2: not observed


def test_an_unfinished_job_is_followed_until_its_drain_limit_only():
    fake = Statuses([(0, "running")])
    tracker = track(fake, deadline_s=0.1, drain_s=0.2)
    assert [o["status"] for o in fake.observed] == ["running"]
    assert (tracker.final, tracker.finished_mono) == (None, None) and not tracker.is_alive()


def test_the_spark_step_counts_as_running_from_its_start_until_its_step_ended_record(tmp_path):
    """step_ended is the pipeline's step record, which names the step in "name", not "step"."""
    batch = offline_batch(tmp_path)
    batch.store_id = "s" * 32
    log(batch, "A", {"event": "claimed", "job_id": 7, "attempt": 1, "run_id": "job-7-attempt-1", "mono": 1})
    assert batch.spark_running(7) is None                                        # not started
    log(batch, "A", {"event": "step_started", "job_id": 7, "attempt": 1, "step": "spark_pipeline", "mono": 2})
    assert batch.spark_running(7) is None                                        # no step log yet
    logs = batch.attempt_dir("job-7-attempt-1") / "logs"
    logs.mkdir(parents=True)
    (logs / "spark_pipeline.log").touch()
    assert batch.spark_running(7)["worker"] == "A"
    log(batch, "A", {"event": "step_ended", "job_id": 7, "attempt": 1, "name": "spark_pipeline", "outcome": "exited",
                     "mono": 3})
    assert batch.spark_running(7) is None



# The setup, quiescence and the final records (gaps G1, G2, G5 and G7 of docs/recovery-part-a.md)

class SetupFails(harness.Batch):
    """A batch whose services start (or are found running already) and whose setup then fails."""

    def __init__(self, plan, out, *, containers_exist=False):
        super().__init__(plan, out)
        self.containers_exist, self.calls = containers_exist, []

    def services_up(self):
        if self.containers_exist:
            raise RuntimeError("this project's containers exist already; a batch starts on fresh ones")
        self.services_started = True

    def cli(self, *argv, check=True, timeout=180):
        raise RuntimeError(f"{argv[0]}: exit 1: no database")

    def compose(self, *args, timeout=300):
        self.calls.append(("compose", *args))
        return 0.0

    def quiesce(self):
        self.calls.append(("quiesce",))
        return {}

    def final_snapshot(self):
        self.calls.append(("final_snapshot",))
        return {}

    def scratch_folders(self):
        return []


def test_a_setup_failure_is_recorded_and_every_planned_job_kept_as_not_run(tmp_path):
    plan = harness.make_plan(DEFAULTS, seed=1, purpose="preflight", jobs=["C0", "W1"])
    batch = SetupFails(plan, tmp_path / "preflight" / "b")
    assert batch.run() == 1
    events = read_events(batch.out / "harness.jsonl")
    assert [e["error"] for e in harness.events_named(events, "setup_error")] == [
        "RuntimeError: init-db: exit 1: no database"]
    assert [(e["position"], e["why"]) for e in harness.events_named(events, "not_run")] == [
        (1, "an error in the setup"), (2, "an error in the setup")]
    assert harness.events_named(events, "batch_ended")[0]["stop_reason"] == "an error in the setup"
    assert batch.calls == [("quiesce",), ("final_snapshot",), ("compose", "down", "-v")]   # its own services


def test_containers_found_running_are_never_taken_down(tmp_path):
    plan = harness.make_plan(DEFAULTS, seed=1, purpose="preflight", jobs=["C0"])
    batch = SetupFails(plan, tmp_path / "preflight" / "b", containers_exist=True)
    assert batch.run() == 1
    events = read_events(batch.out / "harness.jsonl")
    assert "exist already" in harness.events_named(events, "setup_error")[0]["error"]
    assert batch.calls == []                                     # no quiescence, no final snapshot, no down -v


class FakeMySQL:
    """A server's process list: each open connection is listed until it is closed."""

    def __init__(self):
        self.open, self.next_id = set(), 100

    def connection(self):
        server = self

        class Connection:
            def __init__(self):
                server.next_id += 1
                self.id = server.next_id
                server.open.add(self.id)

            def cursor(self):
                return Cursor(self)

            def close(self):
                server.open.discard(self.id)

        class Cursor:
            def __init__(self, connection):
                self.connection, self.rows = connection, []

            def execute(self, sql, params=None):
                if sql == "SELECT CONNECTION_ID()":
                    self.rows = [(self.connection.id,)]
                elif sql == "SHOW FULL PROCESSLIST":
                    self.rows = ([(i, "root", "localhost", "etf_recovery", "Sleep") for i in sorted(server.open)]
                                 + [(1, "event_scheduler", "localhost", None, "Daemon")])

            def fetchone(self):
                return self.rows[0]

            def fetchall(self):
                return self.rows

            def close(self):
                pass

        return Connection()


def quiet_batch(tmp_path, server, scratch=()):
    batch = offline_batch(tmp_path)
    batch.procs, batch.store_id = {}, "s" * 32
    batch.connect = lambda **timeouts: server.connection()
    batch._marked = lambda: False
    batch.scratch_folders = lambda: list(scratch)
    batch.QUIESCE_CONNECTIONS_WAIT_S = 0.2
    return batch


def test_quiescence_closes_the_harness_own_connections_and_counts_only_other_clients(tmp_path):
    """4.4: no client connection but the harness's; its own stores reopen on their next use."""
    server = FakeMySQL()
    batch = quiet_batch(tmp_path, server)
    batch._stores = [SimpleNamespace(connection=server.connection()), SimpleNamespace(connection=None)]
    assert batch.quiesce()["other_connections"] == 0
    assert all(store.connection is None for store in batch._stores) and server.open == set()
    server.connection()                                          # a client that is not the harness
    assert batch.quiesce()["other_connections"] == 1


def test_spark_scratch_has_its_prefixes_only_and_quiescence_reports_what_is_new(tmp_path):
    folder = tmp_path / "tmp"
    folder.mkdir()
    for name in ("spark-1", "blockmgr-2", "hsperfdata_x", "unrelated", "pyspark-3"):
        (folder / name).mkdir()
    assert [Path(p).name for p in harness.spark_scratch([folder, tmp_path / "missing"])] == [
        "blockmgr-2", "hsperfdata_x", "pyspark-3", "spark-1"]
    batch = quiet_batch(tmp_path / "b", FakeMySQL(), scratch=[folder])
    batch.scratch_before = harness.spark_scratch([folder])
    (folder / "spark-new").mkdir()
    assert batch.quiesce()["spark_scratch_new"] == [str(folder / "spark-new")]


def test_plan_creates_the_folder_it_writes_into(tmp_path):
    out = tmp_path / "data" / "outputs-recovery" / "formal" / "plan-7.json"
    assert harness.main(["plan", "--purpose", "formal", "--seed", "7", "--out", str(out)]) == 0
    assert json.loads(out.read_text())["purpose"] == "formal"


def test_a_relative_batch_folder_reaches_the_reference_launcher_as_absolute_paths(tmp_path, monkeypatch):
    """G9: the reference run's launcher runs in its .work folder, so a relative path handed to it
    resolved there and the step could not start (preflight-1, 2026-10-24)."""
    calls = []

    class Launcher:                                              # the launcher's process, as the harness sees it
        def __init__(self, command, **kwargs):
            calls.append((command, kwargs))
            self.stdin = SimpleNamespace(write=lambda data: None, flush=lambda: None, close=lambda: None)

        def wait(self, timeout=None):
            return 0

    monkeypatch.chdir(tmp_path)
    batch = harness.Batch(harness.make_plan(DEFAULTS, seed=1, purpose="preflight", jobs=["C0"]), Path("preflight/b"))
    batch.store_id = "s" * 32
    monkeypatch.setattr(harness.subprocess, "Popen", Launcher)
    batch.reference_run()
    assert batch.out == (tmp_path / "preflight" / "b").resolve() and len(calls) == 2
    for command, kwargs in calls:
        assert Path(kwargs["cwd"]).is_absolute()
        assert all(Path(command[command.index(flag) + 1]).is_absolute()
                   for flag in ("--cwd", "--step-log", "--result", "--lock", "--registry"))
        step = command[command.index("--") + 1:]
        assert all(Path(value).is_absolute() for flag, value in zip(step, step[1:])
                   if flag.startswith("--") and "/" in value)        # the step's own folders too
