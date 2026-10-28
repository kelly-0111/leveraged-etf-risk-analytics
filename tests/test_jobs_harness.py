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
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from etf_risk.jobs import harness
from etf_risk.jobs.events import read_events
from etf_risk.jobs.timing import DEFAULT_TIMING

REPO = Path(__file__).resolve().parents[1]
DEFAULTS = harness.Settings()


def test_a_plan_has_two_jobs_of_every_case_in_an_order_fixed_by_its_seed():
    """P1's preferred draft (2026-10-24): 2 jobs of each case in one batch, 28, shuffled; with the
    approved controls, a C0 at each end, 30 in all."""
    jobs = harness.plan_jobs(DEFAULTS, seed=7)
    assert len(jobs) == 30 and Counter(jobs) == {**{case: 2 for case in harness.CASES}, "C0": 4}
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
    assert harness.Settings.from_dict(again["settings"]) == DEFAULTS and len(again["jobs"]) == 30
    assert again["deadlines_s"]["W7"] == 170 and set(again["code"]) >= {"source_digest", "uv_lock_sha256"}


def test_the_estimate_of_the_preferred_draft_and_of_the_84_job_alternative():
    """Under Assumptions (none measured): 1,403 s for one job of each case; 3,070 s for the
    preferred batch of 30 jobs (28 and two C0 controls); 4,473 s for each of the alternative's two
    batches of 44."""
    result = harness.estimate(harness.make_plan(DEFAULTS, seed=1))
    per = result["per_case_s"]
    assert (per["C0"], per["W1"], per["W4"], per["W7"], per["K2"], per["D1"], per["D2"]) == (42, 74, 159, 159, 118, 116,
                                                                                            149)
    assert sum(per.values()) == 1403
    assert (result["jobs"], result["batch_s"]) == (30, 2 * 1403 + 2 * 42 + 180) == (30, 3070)
    alternative = harness.estimate(harness.make_plan(harness.Settings(jobs_per_case=3), seed=1))
    assert (alternative["jobs"], alternative["batch_s"]) == (44, 3 * 1403 + 2 * 42 + 180) == (44, 4473)   # twice


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

    def other_containers(self):
        return 0


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
    assert [(e["stage"], e["other_containers"]) for e in harness.events_named(events, "host_state")] == [
        ("start", 0), ("end", 0)]                                         # recorded all the same


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



# The host's state (docs/recovery-part-a.md, section 12)

PMSET_AC = "Now drawing from 'AC Power'\n -InternalBattery-0 (id=1)\t100%; charged; 0:00 remaining present: true\n"
PMSET_BATTERY = "Now drawing from 'Battery Power'\n -InternalBattery-0 (id=1)\t97%; discharging; 7:54 remaining\n"
IOREG_OPEN = '  |   "AppleClamshellCausesSleep" = No\n  |   "AppleClamshellState" = No\n'
IOREG_CLOSED = '  |   "AppleClamshellState" = Yes\n'


def test_the_power_source_and_the_lid_are_read_from_pmset_and_ioreg():
    assert [harness.parse_power_source(t) for t in (PMSET_AC, PMSET_BATTERY, "")] == ["AC Power", "Battery Power", None]
    assert [harness.parse_lid_closed(t) for t in (IOREG_OPEN, IOREG_CLOSED, "")] == [False, True, None]


VM_STAT = """Mach Virtual Memory Statistics: (page size of 16384 bytes)
Pages free:                                4589.
Pageins:                                    100.
Pageouts:                                     7.
Swapins:                                     30.
Swapouts:                                    40.
"""


def test_the_host_state_has_memory_swap_in_use_vm_counters_pressure_power_and_the_lid():
    outputs = {"sysctl": "4\n", "pmset": PMSET_BATTERY, "ioreg": IOREG_CLOSED, "vm_stat": VM_STAT}
    state = harness.host_state(command=lambda *argv: outputs[argv[0]])
    assert set(state) == {"available_bytes", "total_bytes", "swap_used_bytes", "pageins_bytes", "pageouts_bytes",
                          "swapins_bytes", "swapouts_bytes", "memory_pressure", "power_source", "lid_closed"}
    assert (state["memory_pressure"], state["power_source"], state["lid_closed"]) == (4, "Battery Power", True)
    assert (state["pageins_bytes"], state["pageouts_bytes"], state["swapins_bytes"], state["swapouts_bytes"]) == (
        100 * 16384, 7 * 16384, 30 * 16384, 40 * 16384)
    assert all(isinstance(state[k], int) and state[k] >= 0 for k in ("available_bytes", "swap_used_bytes"))
    unknown = harness.host_state(command=lambda *argv: "")                 # a host that gives none of them
    assert (unknown["memory_pressure"], unknown["power_source"], unknown["lid_closed"]) == (None, None, None)
    assert {k: unknown[k] for k in ("pageins_bytes", "swapouts_bytes")} == {"pageins_bytes": None, "swapouts_bytes": None}


def test_the_host_state_never_writes_psutils_page_counts_under_swap_names():
    """Until 2026-10-27, swap_in_bytes and swap_out_bytes held psutil's sin and sout: on macOS,
    page-ins and page-outs (docs/host-counters-correction.md). No new record may hold them."""
    state = harness.host_state(command=lambda *argv: VM_STAT if argv[0] == "vm_stat" else "")
    assert not {"swap_in_bytes", "swap_out_bytes"} & set(state)


POWER_LOG = """2026-10-26 22:40:00 -0500 Notification        Display is turned on
2026-10-26 22:51:27 -0500 Sleep               \tEntering Sleep state due to 'Clamshell Sleep':TCPKeepAlive=active
2026-10-26 22:51:29 -0500 Wake Request        \t[*process*=powerd request=Maintenance deltaSecs=7200]
2026-10-26 22:53:00 -0500 DarkWake            \tDarkWake from Deep Idle [CDNP] : due to SMC.OutboxNotEmpty
2026-10-26 22:55:07 -0500 Wake                \tWake from Deep Idle [CDNVA] : due to UserActivity Assertion
2026-10-26 23:30:00 -0500 Sleep               \tEntering Sleep state due to 'Idle Sleep'
"""


def test_the_power_log_gives_sleep_and_wake_entries_in_the_batch_by_time_and_kind_only():
    start = datetime.fromisoformat("2026-10-27T03:45:00+00:00")             # 22:45 -0500
    end = datetime.fromisoformat("2026-10-27T04:00:00+00:00")               # 23:00 -0500
    found = harness.parse_power_log(POWER_LOG, start, end)
    assert [e["kind"] for e in found["entries"]] == ["Sleep", "DarkWake", "Wake"]   # not the Wake Request, nor 23:30
    assert all(set(e) == {"ts", "kind"} for e in found["entries"])                    # never the reason text
    assert found["covers_batch"] is True and found["log_starts"].startswith("2026-10-26T22:40:00")
    late = harness.parse_power_log(POWER_LOG, datetime.fromisoformat("2026-10-27T03:00:00+00:00"), end)
    assert late["covers_batch"] is False                                              # the log starts after the batch


def test_missing_power_log_evidence_is_stated_never_taken_as_no_sleep():
    ts = ("2026-10-27T03:45:00+00:00", "2026-10-27T04:00:00+00:00")
    assert harness.power_log_evidence(*ts, read=lambda: "") == {"available": False, "why": "pmset -g log printed nothing"}
    assert harness.power_log_evidence(*ts, read=lambda: "no dates here\n")["available"] is False

    def failing():
        raise OSError("no pmset")
    assert harness.power_log_evidence(*ts, read=failing)["why"].startswith("pmset -g log failed: OSError")
    assert harness.power_log_evidence(*ts, read=lambda: POWER_LOG)["available"] is True


class StubLog:
    def __init__(self):
        self.records = []

    def log(self, event, **fields):
        self.records.append({"event": event, **fields})


def test_the_container_monitor_keeps_its_events_and_records_its_count_and_error(tmp_path):
    events = [{"action": "start", "ours": True, "time": 1, "mono": 5.0},
              {"action": "start", "ours": False, "time": 2, "mono": 6.0}]
    monitor = SimpleNamespace(events=events, error=None, stop=lambda: None)
    batch = SimpleNamespace(containers=monitor, out=tmp_path, log=StubLog(), monitor_start_error=None)
    harness.Batch.stop_container_monitor(batch)
    assert [json.loads(line) for line in (tmp_path / "containers.jsonl").read_text().splitlines()] == events
    assert batch.log.records == [{"event": "container_monitor", "error": None, "events": 2, "other_project_events": 1}]


def test_a_monitor_that_never_started_is_recorded_as_such(tmp_path):
    batch = SimpleNamespace(containers=None, out=tmp_path, log=StubLog(), monitor_start_error="OSError: docker")
    harness.Batch.stop_container_monitor(batch)
    assert batch.log.records[0]["error"] == "not started: OSError: docker"
    assert not (tmp_path / "containers.jsonl").exists()


def test_every_host_reading_records_the_containers_outside_this_project(tmp_path, monkeypatch):
    """Section 12, condition 4, at every reading since 2026-10-25: a count, or None when docker cannot say."""
    plan = harness.make_plan(DEFAULTS, seed=1, purpose="preflight", jobs=["C0"])
    batch = harness.Batch(plan, tmp_path / "preflight" / "b")
    monkeypatch.setattr(harness, "host_state", lambda: {"power_source": "AC Power", "lid_closed": False})

    class Counted:
        def other_containers(self):
            return 2

    class Broken:
        def other_containers(self):
            raise RuntimeError("docker ps failed with exit code 1")

    batch.services = Counted()
    batch.log_host("start")
    batch.services = Broken()
    batch.log_host("job", position=1)
    readings = harness.events_named(read_events(batch.out / "harness.jsonl"), "host_state")
    assert [(e["stage"], e.get("position"), e["power_source"], e["other_containers"]) for e in readings] == [
        ("start", None, "AC Power", 2), ("job", 1, "AC Power", None)]



def test_the_controls_bracket_the_shuffled_order_and_a_listed_order_gets_none():
    """Section 12, condition 6, approved on 2026-10-24: a C0 control at each end of the shuffle."""
    bracketed = harness.plan_jobs(DEFAULTS, seed=7)
    plain = harness.plan_jobs(harness.Settings(bracket_controls=False), seed=7)
    assert bracketed == ["C0", *plain, "C0"] and len(plain) == 28        # the same shuffle inside
    assert harness.make_plan(DEFAULTS, seed=7)["controls"] == "a C0 at each end"
    listed = harness.make_plan(DEFAULTS, seed=7, purpose="preflight", jobs=["W1", "C0"])
    assert (listed["jobs"], listed["controls"]) == (["W1", "C0"], None)
