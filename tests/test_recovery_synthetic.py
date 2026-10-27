"""A synthetic batch of the recovery experiments, end to end, with no services: the harness's own
Batch.run (etf_risk.jobs.harness) drives workers and a reconciler in this process, on a SQLite job
table, and the collector (analysis/collect_recovery_measurements.py) then reads the batch folder
as it would read a real one. No formal experiment: nothing here measures the job system.

Real code: the harness's run, run_job, after_job, arming, phases, Tracker, observation, cross-check
and final snapshot; the CLI's init-db, submit, status --check and export, run in process; Worker,
FaultFile, Reconciler and the job store; the frozen crosscheck.sql, translated for SQLite
(tests/recovery_sqlite.py); the collector.
Stand-ins: Kafka (Group: one partition in memory, with the assignment events kafka.log_assignment
writes); the Spark steps and their launchers (SyntheticPipeline); the job processes (ThreadProc,
where a SIGKILL lands within a tick); MySQL (SQLite); the containers (no peaks, no restarts). The
lease is 3 s and a dead member loses the partition after 0.5 s.

Covered: C0 twice, the second with a deadline observation that fails on purpose; W1, W2, W3; W4,
whose deadline is set short so that it completes late; W5a, W5b and X1. Not covered: W6 and W7
(SIGSTOP of processes), K1 and K2 (Kafka down), D1 and D2 (MySQL down), which need the services.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import importlib.util
import io
import itertools
import json
import os
import signal
import subprocess
import sys
import threading
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from conftest import nyse_sessions, write_snapshot
from recovery_sqlite import REPO, sqlite_statement

from etf_risk import runs
from etf_risk.jobs import cli, faults, harness, kafka
from etf_risk.jobs.events import EventLog, read_events
from etf_risk.jobs.queue import Delivery
from etf_risk.jobs.reconciler import Reconciler
from etf_risk.jobs.simulated import MemoryQueue, SimulatedCrash
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite
from etf_risk.jobs.worker import Fenced, Worker
from etf_risk.provenance import code_identity, source_identity

spec = importlib.util.spec_from_file_location("collect_recovery_measurements",
                                              REPO / "analysis" / "collect_recovery_measurements.py")
crm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crm)

LEASE_S, MARGIN_S = 3.0, 0.5            # the synthetic lease; F = m0 + LEASE_S - MARGIN_S
SESSION_S = 0.5                         # a dead member loses the partition this long after its death
STEPS = (("windows", 0.05), ("spark_pipeline", 1.0), ("verify", 0.05))     # mid-step: 0.2 s into 1 s
TICK = 0.01
JOBS = ["C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "X1", "C0"]     # job ids 1-9, in this order
UNOBSERVED = {9}                        # the second C0's deadline observation fails
LATE = {"W4": 3.0}                      # seconds: it cannot succeed before the lease (3 s) and a run (1.1 s)
DEADLINE_S = 20.0                       # every other case's deadline


class ThreadProc:
    """A job process as the harness drives it (poll, kill, send_signal, wait), run as a thread. A
    SIGKILL lands at the thread's next check, within a tick; SIGTERM asks it to stop."""
    _pids = itertools.count(60001)

    def __init__(self, target):
        self.pid = next(ThreadProc._pids)
        self.killed, self.stopping = threading.Event(), threading.Event()
        self.code, self.died_at, self.error = None, None, None
        self._thread = threading.Thread(target=self._run, args=(target,), daemon=True)
        self._thread.start()

    def _run(self, target):
        code = 0
        try:
            target(self)
        except SimulatedCrash:
            code = -signal.SIGKILL
        except BaseException:
            code, self.error = 1, traceback.format_exc()
        self.died_at = time.monotonic()
        self.code = code

    def poll(self):
        return self.code

    def kill(self):
        self.killed.set()

    def send_signal(self, sig):
        (self.killed if sig == signal.SIGKILL else self.stopping).set()

    def halted(self) -> bool:
        return self.killed.is_set() or self.stopping.is_set()

    def check(self):
        """Where a SIGKILL lands."""
        if self.killed.is_set():
            raise SimulatedCrash("SIGKILL")

    def wait(self, timeout=None):
        self._thread.join(timeout)
        if self._thread.is_alive():
            raise subprocess.TimeoutExpired(f"thread {self.pid}", timeout)
        return self.code


class Group:
    """One partition and one consumer group, with what the harness relies on from Kafka (outline
    2.4): the first member to join owns the partition, and a newcomer gets nothing while the
    owner lives; a member that died loses the partition SESSION_S later, one that left at once,
    to the earliest live member, which reads on from the group's committed offset. Assignments go
    to the member's event log as kafka.log_assignment writes them."""

    def __init__(self, queue: MemoryQueue, topic: str):
        self.queue, self.topic = queue, topic
        self.lock = threading.Lock()
        self.members, self.owner, self.committed = [], None, 0

    def join(self, events: EventLog, proc: ThreadProc) -> "Member":
        member = Member(self, events, proc)
        with self.lock:
            self.members.append(member)
            self._rebalance()
            if member is not self.owner:
                member.assigned([])
        return member

    def _rebalance(self):
        owner = self.owner
        if owner is not None and not owner.left and owner.proc.poll() is None:
            return
        if owner is not None and not owner.left and time.monotonic() - owner.proc.died_at < SESSION_S:
            return                                                   # its session has not expired yet
        live = [m for m in self.members if not m.left and m.proc.poll() is None]
        self.owner = live[0] if live else None
        if self.owner is not None:
            self.owner.position = self.committed
            self.owner.assigned([SimpleNamespace(topic=self.topic, partition=0)])


class Member:
    """A worker's consumer in the Group."""

    def __init__(self, group: Group, events: EventLog, proc: ThreadProc):
        self.group, self.events, self.proc = group, events, proc
        self.position, self.left = 0, False

    def memberid(self):
        return f"member-{self.proc.pid}"

    def assigned(self, partitions):
        kafka.log_assignment(self.events, "assigned", self, partitions)

    def poll(self, timeout: float = 0.0):
        self.proc.check()
        with self.group.lock:
            self.group._rebalance()
            messages = self.group.queue.messages
            if self.group.owner is self and self.position < len(messages):
                delivery = Delivery(messages[self.position], self.position)
                self.position += 1
                return delivery
        time.sleep(min(timeout, TICK))
        return None

    def commit(self, delivery: Delivery):
        with self.group.lock:
            if self.group.owner is not self:
                raise ConnectionError("the partition was reassigned")
            self.group.committed = max(self.group.committed, delivery.position + 1)

    def rewind(self, delivery: Delivery):
        self.position = delivery.position

    def close(self):
        self.left = True


def write_tables(folder) -> None:
    """Four small tables, the same in every run, as the reference comparison of 6.2 reads them."""
    day = date(2024, 1, 2)
    key = {"window_kind": ["calendar-year"] * 2, "ticker": ["AAA", "BBB"], "window_days": [252, 252],
           "entry_date": [day, day]}
    tables = {
        "window_stats": {**key, "mean_return": [0.01, 0.02]},
        "path_days": {**key, "leverage": [2, 2], "day": [1, 1], "value": [101.0, 99.0]},
        "path_summary": {**key, "leverage": [2, 2], "breached": [False, True], "n_breach_rows": [0, 1],
                         "breach_day": [None, 1], "breach_date": [None, day], "last_ok_date": [day, None],
                         "days_ok": [1, 0]},
        "paired": {**key, "breached_1x": [False, False], "breached_2x": [False, True], "breach_date_2x": [None, day],
                   "breach_day_2x": [None, 1], "last_ok_date_2x": [day, None], "days_ok_2x": [1, 0]},
    }
    for name, columns in tables.items():
        (folder / name).mkdir(parents=True)
        pq.write_table(pa.table(columns), folder / name / "part-00000.parquet")
        (folder / name / "_SUCCESS").touch()


def write_result(folder) -> None:
    folder.mkdir(parents=True)
    write_tables(folder)
    (folder / "run.json").write_text(json.dumps({"status": "ok"}))
    (folder / "checks.json").write_text(json.dumps({"window_stats": {"nulls": 0}, "paired": {"mismatched": 0}}))


class SyntheticPipeline:
    """Stands in for SubprocessPipeline in a worker thread, with what the harness and the collector
    read from a real run: a renewal before each step and before acceptance, with F as fence_at;
    step_started (with the launch-time code identity) and step_ended as the pipeline logs them;
    logs/<step>.log from the step's start; logs/<step>.launcher.json with the step's monotonic
    interval once its tree has ended, also when the worker was killed mid-step, since a launcher
    outlives its worker (EOF); attempt.json, a run folder whose tables equal the reference run's,
    and manifest.json. A kill during spark_pipeline leaves Spark scratch in `scratch`."""

    def __init__(self, events: EventLog, proc: ThreadProc, snapshot: str, scratch):
        self.events, self.proc, self.snapshot, self.scratch = events, proc, snapshot, scratch
        self.fence_at = None

    def _renew(self, heartbeat, claim, before: str):
        m0 = time.monotonic()
        ok = heartbeat()
        self.events.log("renewed" if ok else "renewal_refused", job_id=claim.job_id, attempt=claim.attempt_number,
                        seconds=round(time.monotonic() - m0, 3))
        if not ok:
            raise Fenced(f"{claim.run_id}: the renewal before {before} was refused")
        self.fence_at = m0 + LEASE_S - MARGIN_S

    def run(self, claim, run_dir, heartbeat) -> str:
        self.fence_at = heartbeat.claimed_mono + LEASE_S - MARGIN_S
        logs, run_folder = run_dir / "logs", run_dir / "output" / self.snapshot / "w" / claim.run_id
        logs.mkdir()
        for name, seconds in STEPS:
            self._renew(heartbeat, claim, before=name)
            self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name,
                            code=source_identity())
            (logs / f"{name}.log").write_text(f"{name} started\n")
            started, outcome = time.monotonic(), "eof"
            try:
                while time.monotonic() - started < seconds:
                    if self.proc.killed.is_set() and name == "spark_pipeline":
                        (self.scratch / f"spark-{claim.run_id}").mkdir()     # what a killed Spark step leaves
                    self.proc.check()
                    time.sleep(TICK)
                outcome = "exited"
            finally:
                ended = time.monotonic()
                (logs / f"{name}.launcher.json").write_text(json.dumps(
                    {"outcome": outcome, "returncode": 0 if outcome == "exited" else -15,
                     "step_started_mono": started, "tree_ended_mono": ended, "step_seconds": round(ended - started, 3)}))
            if name == "spark_pipeline":
                write_result(run_folder)
            elif name == "verify":
                (run_folder / "verify.json").write_text(json.dumps(
                    {"mismatch_count": 0, "breached_windows": {"python": 1, "spark": 1, "same": True}}))
            self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number, name=name,
                            outcome=outcome, returncode=0, seconds=round(ended - started, 3))
        (run_dir / "attempt.json").write_text(json.dumps({"run_folder": run_folder.relative_to(run_dir).as_posix()}))
        manifest = runs.manifest(run_folder)
        (run_dir / "manifest.json").write_text(json.dumps(manifest))
        self._renew(heartbeat, claim, before="acceptance")
        return runs.digest(manifest)


def worker_main(batch: "SyntheticBatch", name: str):
    """What cmd_worker does, in a thread: the started event, the fault file, serve; no sweep (no processes)."""
    def main(proc: ThreadProc):
        store = batch.job_store()
        store_id = store.store_id()
        events = EventLog(batch.events_dir / f"{name}.jsonl", "worker", store_id=store_id, worker_id=name, pid=proc.pid)
        events.log("started", topic=batch.topic, code=code_identity(), fault_file=str(batch.fault_file(name)))

        def kill():
            proc.kill()
            proc.check()

        pipeline = SyntheticPipeline(events, proc, batch.settings.snapshot, batch.scratch_dir)
        worker = Worker(store, pipeline, batch.jobs_root / store_id,
                        worker_id=name, events=events, fault=faults.FaultFile(batch.fault_file(name), events, kill=kill))
        consumer = batch.group.join(events, proc)
        worker.serve(consumer, stop=proc.halted, poll_timeout=0.05, retry_delay=0.1)
        proc.check()                                                   # killed: no orderly leave
        consumer.close()
        events.log("stopped")
    return main


def reconciler_main(batch: "SyntheticBatch"):
    def main(proc: ThreadProc):
        store = batch.job_store()
        events = EventLog(batch.events_dir / f"reconciler-{proc.pid}.jsonl", "reconciler", store_id=store.store_id(),
                          pid=proc.pid)
        events.log("started", topic=batch.topic, code=code_identity())
        halt = SimpleNamespace(is_set=proc.halted, wait=time.sleep)
        Reconciler(store, batch.queue.publisher(), events=events,
                   publication_grace=timedelta(seconds=11)).run(halt, interval=timedelta(seconds=0.2))
        proc.check()
        events.log("stopped")
    return main


class SyntheticBatch(harness.Batch):
    """harness.Batch with SQLite, the Group, ThreadProc processes and no containers."""
    SNAPSHOT, PARAM = "BEGIN", "?"

    def __init__(self, plan, out, processed_root):
        super().__init__(plan, out)
        self.processed_root = processed_root
        self.db_path = out / "jobs.sqlite"
        self.db = self.env["ETF_RISK_JOBS_DB"] = f"sqlite:///{self.db_path}"
        self.queue = MemoryQueue()
        self.group = Group(self.queue, self.topic)
        self.scratch_dir = out.parent / "scratch"
        (self.scratch_dir / "spark-before-the-batch").mkdir(parents=True)        # never reported as new
        day_before = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S %z")
        self.power_log_read = lambda: f"{day_before} Sleep               \tEntering Sleep state due to 'Idle Sleep'\n"

    def container_monitor(self):
        """No Docker: a silent stream, so the whole-batch monitor runs, sees nothing and fails nothing."""
        return self.services.ContainerEvents(command=[sys.executable, "-c", "import time; time.sleep(3600)"])

    def job_store(self) -> JobStore:
        return JobStore(None, SQLITE, lease=timedelta(seconds=LEASE_S),
                        connect=lambda: open_sqlite(self.db_path, check_same_thread=False))

    # No containers

    def services_up(self):
        self.services_started = True                                   # as the real one marks it: then quiesce
        self.log.log("services_up", seconds=0.0, others=[])

    def compose(self, *args, timeout=300):
        return 0.0

    def wait_ready(self, service):
        return time.monotonic()

    def read_peaks(self, closes=None):
        for service in ("mysql", "kafka"):
            self.peaks.add(service, None, None, closes)
            self.log.log("peaks", service=service, peak_bytes=None, limit_bytes=None, closes=closes, verdict="unknown")
        return "ok"

    def reference_run(self):
        """The reference's two steps, with launcher records as the real ones are written, and its tables."""
        run_dir = self.out / "reference"
        (run_dir / "logs").mkdir(parents=True)
        for name in ("windows", "spark_pipeline"):
            before = started = time.monotonic()
            if name == "spark_pipeline":
                write_result(run_dir / "output" / self.settings.snapshot / "w" / "reference")
            time.sleep(0.02)
            (run_dir / "logs" / f"{name}.launcher.json").write_text(json.dumps(
                {"outcome": "exited", "returncode": 0, "step_started_mono": started, "tree_ended_mono": time.monotonic()}))
            self.log.log("reference_step", step=name, exit=0, before=before, after=time.monotonic())

    # The CLI and the processes, in this process

    def common_args(self):
        args = super().common_args()
        args[args.index("--processed-root") + 1] = str(self.processed_root)
        return args

    def cli(self, *argv, check=True, timeout=180):
        if argv[0] == "create-topic":                                 # no broker
            return subprocess.CompletedProcess(argv, 0, "", "")
        names = ("ETF_RISK_JOBS_DB", "ETF_RISK_KAFKA_BOOTSTRAP", "ETF_RISK_JOBS_TOPIC")
        saved = {k: os.environ.get(k) for k in names}
        os.environ.update({k: self.env[k] for k in names})
        out, err = io.StringIO(), io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                try:
                    code = cli.main([*argv, *self.common_args()])
                except SystemExit as exit_:
                    code = exit_.code if isinstance(exit_.code, int) else 1
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        done = subprocess.CompletedProcess(argv, code, out.getvalue(), err.getvalue())
        if check and code != 0:
            raise RuntimeError(f"{argv[0]}: exit {code}: {done.stderr.strip()[-500:]}")
        return done

    def start(self, name, *argv, extra_env=None):
        before = time.monotonic()
        proc = self.procs[name] = ThreadProc(reconciler_main(self) if argv[0] == "reconciler" else worker_main(self, name))
        self._check_start(name, proc, before)
        return proc

    def publish_again(self, job_id):
        return self.queue.publisher().publish(job_id)

    # SQLite

    def new_store(self):
        return self.job_store()

    def scratch_folders(self):
        return [self.scratch_dir]

    def connect(self, **timeouts):
        if getattr(self._local, "unreachable", False):
            raise ConnectionRefusedError("synthetic: the database cannot be reached")
        return open_sqlite(self.db_path, check_same_thread=False)

    def statement(self, sql):
        return sqlite_statement(sql)

    def other_connections(self):
        return 0                                                       # SQLite: no server to ask

    def other_containers(self):
        return 0                                                       # no Docker in a synthetic batch

    def observe(self, job_id):
        self._local.unreachable = job_id in UNOBSERVED
        try:
            return super().observe(job_id)
        finally:
            self._local.unreachable = False


def run_batch(tmp_path, monkeypatch):
    dates = nyse_sessions("2024-01-02", 31)
    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(5).normal(0, 0.01, 30))})
    processed = tmp_path / "processed"
    settings = harness.Settings(snapshot="snap", poll_s=0.05, phase_delay_s=0.2, phase_timeout_s=15.0)
    plan = harness.make_plan(settings, seed=1, purpose="preflight", jobs=JOBS)     # never a formal result
    out = tmp_path / "batch"
    batch = SyntheticBatch(plan, out, processed)
    (out / "plan.json").write_text(json.dumps(plan, indent=2))
    queue = batch.queue

    class QueuePublisher:                                              # what cmd_submit publishes with
        def __init__(self, *args, **kwargs):
            self._publisher = queue.publisher()

        def publish(self, job_id):
            return self._publisher.publish(job_id)

        def close(self):
            pass

    monkeypatch.setattr(kafka, "KafkaPublisher", QueuePublisher)
    monkeypatch.setattr(harness, "deadline_seconds", lambda case, timing, s: LATE.get(case, DEADLINE_S))
    monkeypatch.setattr(harness, "host_state", lambda: {     # a host on AC power, lid open, whatever runs the test
        "available_bytes": 4 * 2**30, "total_bytes": 8 * 2**30, "swap_used_bytes": 0, "pageins_bytes": 0,
        "pageouts_bytes": 0, "swapins_bytes": 0, "swapouts_bytes": 0, "memory_pressure": 1,
        "power_source": "AC Power", "lid_closed": False})
    assert batch.run() == 0
    return batch, processed


def test_a_synthetic_batch_runs_end_to_end_and_the_collector_reads_it(tmp_path, monkeypatch):
    batch, processed = run_batch(tmp_path, monkeypatch)
    assert [p.error for p in batch.procs.values() if p.error] == []
    events = read_events(batch.out / "harness.jsonl")
    assert harness.events_named(events, "job_error") == [] and harness.events_named(events, "final_error") == []
    assert harness.events_named(events, "batch_ended")[0]["stop_reason"] is None
    assert len(harness.events_named(events, "restarted")) == 6           # W1, W2, W3, W4, W5a and W5b each killed one
    host = harness.events_named(events, "host_state")                    # at the start, before every job, at the end
    assert [e["stage"] for e in host] == ["start"] + ["job"] * 9 + ["end"]
    assert [e["position"] for e in host if e["stage"] == "job"] == list(range(1, 10))
    assert all(e["available_bytes"] > 0 and e["pageouts_bytes"] >= 0 and e["swapouts_bytes"] >= 0
               and "power_source" in e and "lid_closed" in e and e["other_containers"] == 0 for e in host)
    assert not any("swap_out_bytes" in e or "swap_in_bytes" in e for e in host)       # the names retired on 2026-10-27
    monitor = harness.events_named(events, "container_monitor")             # the whole batch, start to end
    assert [(m["error"], m["events"], m["other_project_events"]) for m in monitor] == [(None, 0, 0)]
    assert (batch.out / "containers.jsonl").read_text() == ""
    power = harness.events_named(events, "power_log")[0]                    # evidence, with the log covering the batch
    assert power["available"] is True and power["covers_batch"] is True and power["entries"] == []
    quiescent = harness.events_named(events, "quiescent")[0]           # 6.5: the killed W3 attempt's Spark scratch
    assert quiescent["spark_scratch_new"] == [str(batch.scratch_dir / "spark-job-4-attempt-1")]
    cleanup = (batch.out / "cleanup.txt").read_text()                  # 6.2: the unaccepted attempts' folders
    assert cleanup.startswith("exit 0\n") and "nothing was deleted" in cleanup
    assert sorted(line.split("/")[-1].split()[0] for line in cleanup.splitlines()
                  if line.startswith("ended, not accepted")) == ["job-4-attempt-1", "job-5-attempt-1"]

    # Arming changed no ownership: the armed worker owned the partition before and after it, its
    # fault fired, and no assignment moved between the arming and the fault.
    logs = batch.worker_logs()
    for armed in harness.events_named(events, "armed"):
        injection = harness.events_named(events, "injection", position=armed["position"])[0]
        assert armed["worker"] == armed["owner_after"] == injection["worker"]
        assert [e for w in logs for e in logs[w]
                if e["event"] == "assigned" and armed["mono"] < e["mono"] < injection["t_inj"]] == []

    assert crm.main(["--batch", str(batch.out), "--processed-root", str(processed)]) == 0
    result = crm.collect(batch.out, processed_root=processed)
    assert (result["purpose"], result["validity_failed"]) == ("preflight", [])
    assert result["validity"]["records_complete"] == {"passed": True, "setup_errors": [], "final_errors": []}
    assert result["verdicts"] == {"correctness": {"valid": True, "failed": []}, "timing": {"valid": True, "failed": []}}
    events_check = result["validity"]["container_events"]                  # the whole-batch condition 4
    assert (events_check["passed"], events_check["other_project_events"]) == (True, 0)
    assert result["outcomes"]["sleep_wake"]["recorded"] is True and result["outcomes"]["sleep_wake"]["covers_batch"]
    rows = {r["position"]: r for r in result["rows"]}
    assert [rows[p]["status"] for p in rows] == ["made"] * 9
    assert [rows[p]["q1_verdict"] for p in rows] == ["ok"] * 9
    assert [rows[p]["timeliness"] for p in rows] == ["on time"] * 4 + ["late"] + ["on time"] * 3 + [
        "deadline not observed"]
    assert (rows[5]["deadline_met"], rows[9]["deadline_met"]) == ("no", "unknown")
    assert [rows[p]["q3a_verdict"] for p in rows] == ["reported once"] * 5 + ["no matching report"] + [
        "reported once"] * 3
    assert [rows[p]["claims"] for p in rows] == ["1", "1", "2", "2", "2", "1", "1", "1", "1"]
    assert [rows[p]["executions"] for p in rows] == [1, 1, 1, 2, 2, 1, 1, 1, 1]          # W2's first claim ran nothing
    assert [rows[p]["complete_executions"] for p in rows] == [1, 1, 1, 1, 2, 1, 1, 1, 1]  # W4's first run was complete
    for p in (2, 3, 4, 5):                                                               # W1-W4: measured
        assert isinstance(rows[p]["detection_s"], float) and isinstance(rows[p]["rerun_s"], float)
        assert isinstance(rows[p]["finish_s"], float) and isinstance(rows[p]["overhead_s"], float)
    assert rows[2]["detection_s"] >= SESSION_S and min(rows[p]["detection_s"] for p in (3, 4, 5)) > 1.0
    assert (rows[1]["detection_s"], rows[6]["detection_s"], rows[8]["finish_s"] > 0) == (
        "n/a: no failure", "n/a: after acceptance", True)
    assert rows[4]["wasted_step_s"] > 0 and rows[5]["wasted_step_s"] >= sum(s for _, s in STEPS)
    assert [rows[p]["wasted_step_s"] for p in (1, 2, 3, 6, 7, 8, 9)] == [0.0] * 7

    outcomes = result["outcomes"]
    assert outcomes["overlap"]["verdict"] == "no overlap" and outcomes["overlap"]["steps_without_interval"] == []
    assert outcomes["q1_not_ok"] == [] and outcomes["invariant_violations"] == {} and outcomes["status_check_exit"] == 0
    assert len(outcomes["accepted_attempts"]) == 9 and all(a["problems"] == [] for a in outcomes["accepted_attempts"])
    assert outcomes["q3b_not_matching"] == [] and outcomes["q2b_rows"] == []
    assert outcomes["nothing_left"] == {"processes_left": False, "other_connections": 0,
                                        "spark_scratch_new": [str(batch.scratch_dir / "spark-job-4-attempt-1")]}
    assert outcomes["cleanup_listing"] == "cleanup.txt" and outcomes["host_state"]["jobs_with_a_reading"] == 9
    assert all(rows[p]["host_available_bytes"] > 0 for p in rows)
    tally = {t["case"]: t for t in result["tally"]}
    for case in set(JOBS):
        assert (tally[case]["made"], tally[case]["missed"], tally[case]["not_run"], tally[case]["unrecorded"]) == (
            JOBS.count(case), 0, 0, 0)
    assert (tally["W4"]["q2: late"], tally["C0"]["q2: deadline not observed"], tally["W5a"]["q3a: no matching report"]) \
        == (1, 1, 1)
    assert sum(t["planned"] for t in tally.values()) == 9 and tally["D2"]["planned"] == 0
