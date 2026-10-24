"""M2's acceptance runs against the services: workers and a reconciler started as
`python -m etf_risk.jobs` processes, real jobs on the full-2026-10-12 snapshot (data/processed),
and failures injected on purpose. They take minutes per case, so they run only with
ETF_RISK_LIVE_PIPELINE=1 as well as ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP (README
runbook), and each module run uses a database and a topic of its own.

The lease is 24 s here, renewed every 4 s, so F = m0 + 14 s: the same relations as the
defaults (etf_risk.jobs.timing), on a shorter clock. Every case ends with check():
- the job succeeded, with exactly one accepted attempt;
- that attempt's recorded digest equals its run folder's digest;
- its tables equal a reference run's by content;
- invariant_violations() is empty;
- no two launchers' step intervals overlap, across every attempt of the module, on the host's
  monotonic clock (the launcher records' step_started_mono and tree_ended_mono);
- no process of any attempt is left.

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil
import pytest

from etf_risk import runs
from etf_risk.jobs import processes
from etf_risk.jobs.store import JobStore, Outcome, Status
from jobs_backends import KAFKA_BOOTSTRAP, MYSQL_URL

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = "full-2026-10-12"
PROCESSED = (REPO / "data" / "processed").resolve()
LIVE = os.environ.get("ETF_RISK_LIVE_PIPELINE") == "1"
pytestmark = [pytest.mark.spark, pytest.mark.skipif(
    not (LIVE and MYSQL_URL and KAFKA_BOOTSTRAP and (PROCESSED / SNAPSHOT).is_dir()),
    reason="set ETF_RISK_LIVE_PIPELINE=1, ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP, with the snapshot in data/")]
TIMING = ["--timing", "lease=24", "--timing", "renew_interval=4", "--timing", "session_timeout=10"]
CALENDAR = {"kind": "calendar-year", "stride": 21}
ROLLING = {"kind": "rolling", "stride": 21}
COMPOSE = ["docker", "compose", "-f", str(REPO / "docker" / "compose.yaml")]

sys.path.insert(0, str(REPO / "analysis"))
_spec = importlib.util.spec_from_file_location("collect_caching_measurements",
                                               REPO / "analysis" / "collect_caching_measurements.py")
ccm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ccm)


class Stack:
    """The module's database, topic, folders, and the processes it started."""

    def __init__(self, root: Path):
        self.root = root
        self.db = f"{MYSQL_URL.rstrip('/')}/etf_live_{secrets.token_hex(4)}"
        self.topic = f"etf-live-{secrets.token_hex(4)}"
        self.output, self.events_dir = root / "out", root / "events"
        self.lock = root / "locks" / "spark-exec.lock"
        self.env = {**os.environ, "ETF_RISK_JOBS_DB": self.db, "ETF_RISK_KAFKA_BOOTSTRAP": KAFKA_BOOTSTRAP,
                    "ETF_RISK_JOBS_TOPIC": self.topic}
        self.procs: dict[str, subprocess.Popen] = {}
        self.cli("init-db")
        self.cli("create-topic")
        from etf_risk.jobs import mysql
        self.store = JobStore(None, mysql.MYSQL, connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))
        self.store_id = self.store.store_id()

    def args(self) -> list[str]:
        return ["--output-root", str(self.output), "--processed-root", str(PROCESSED), "--events",
                str(self.events_dir)]

    def cli(self, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
        out = subprocess.run([sys.executable, "-m", "etf_risk.jobs", *argv, *self.args()], env=self.env,
                             capture_output=True, text=True, timeout=120)
        if check and out.returncode != 0:
            raise AssertionError(f"{argv}: exit {out.returncode}\n{out.stdout}\n{out.stderr}")
        return out

    def start(self, name: str, *argv: str, extra: tuple[str, ...] = ()) -> subprocess.Popen:
        log = open(self.root / f"{name}.log", "ab")
        proc = subprocess.Popen([sys.executable, "-m", "etf_risk.jobs", *argv, *self.args(), *TIMING, *extra],
                                env=self.env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        self.procs[name] = proc
        return proc

    def worker(self, name: str, *extra: str) -> subprocess.Popen:
        return self.start(name, "worker", "--worker-id", name, "--lock", str(self.lock), extra=extra)

    def submit(self, params: dict, max_attempts: int = 3) -> int:
        out = self.cli("submit", "--snapshot", SNAPSHOT, "--kind", params["kind"], "--stride", str(params["stride"]),
                       "--max-attempts", str(max_attempts))
        return json.loads(out.stdout)["job_id"]

    def events(self, name: str) -> list[dict]:
        path = self.events_dir / f"{name}.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []

    def stop_all(self) -> None:
        for proc in self.procs.values():
            if proc.poll() is None:
                try:
                    os.kill(proc.pid, signal.SIGCONT)
                    proc.send_signal(signal.SIGTERM)
                except ProcessLookupError:
                    pass
        for proc in self.procs.values():
            try:
                proc.wait(timeout=60)
            except subprocess.TimeoutExpired:
                proc.kill()
        self.procs.clear()
        for value, procs in processes.marked_processes().items():
            if value.startswith(self.store_id + ":"):
                for p in procs:
                    try:
                        p.resume()
                        p.kill()
                    except psutil.Error:
                        pass


@pytest.fixture(scope="module")
def stack(tmp_path_factory, scratch_before):
    stack = Stack(tmp_path_factory.mktemp("live"))
    stack.scratch_before = scratch_before
    yield stack
    stack.stop_all()
    from etf_risk.jobs.kafka import delete_topic
    delete_topic(KAFKA_BOOTSTRAP, stack.topic)


@pytest.fixture
def services(stack):
    """A reconciler and a standby worker for one case; both stopped afterwards."""
    stack.start("reconciler", "reconciler", extra=("--interval", "2"))
    yield stack
    stack.stop_all()


@pytest.fixture(scope="module")
def references(tmp_path_factory):
    """Direct runs of the three CLIs, one per parameter set, made before any worker starts, so
    no reference run overlaps a worker's Spark step."""
    root, made = tmp_path_factory.mktemp("reference"), {}
    py = sys.executable
    for params in (CALENDAR, ROLLING):
        name = "calendar-year" if params["kind"] == "calendar-year" else f"rolling-252-s{params['stride']}"
        subprocess.run([py, "-m", "etf_risk.windows", "--snapshot", SNAPSHOT, "--processed-root", str(PROCESSED),
                        "--kind", params["kind"], "--stride", str(params["stride"]), "--out-root", str(root / "w"),
                        "--name", name], check=True, capture_output=True, timeout=300)
        subprocess.run([py, "-m", "etf_risk.spark_pipeline", "--windows", str(root / "w" / SNAPSHOT / name),
                        "--out-root", str(root / "out"), "--run-id", "reference"],
                       check=True, capture_output=True, timeout=900)
        made[params["kind"]] = root / "out" / SNAPSHOT / name / "reference"
    return lambda params: made[params["kind"]]


SCRATCH_PREFIXES = ("spark-", "blockmgr-", "pyspark-", "snappy-", "libzstd-jni", "liblz4-java", "hsperfdata_")


def spark_scratch() -> set[str]:
    """What Spark, PySpark and the JVM leave in the temporary folders when a run is killed."""
    names = set()
    for folder in {Path("/private/tmp"), Path(tempfile.gettempdir())}:
        if folder.is_dir():
            names |= {f"{folder}/{p.name}" for p in folder.iterdir() if p.name.startswith(SCRATCH_PREFIXES)}
    return names


@pytest.fixture(scope="module")
def scratch_before(references):
    """The temporary folders once the reference runs are done, before any worker starts."""
    return spark_scratch()


def wait_until(predicate, timeout: float, what: str, step: float = 0.5):
    """predicate()'s first true value. The test's own store loses its connection when MySQL
    stalls; that poll counts as "not yet", and the next one reconnects (store.py)."""
    from etf_risk.jobs.mysql import MYSQL
    deadline = time.monotonic() + timeout
    while True:
        try:
            value = predicate()
        except Exception as error:
            if not MYSQL.is_disconnect(error):
                raise
            value = None
        if value:
            return value
        assert time.monotonic() < deadline, f"timed out waiting for {what}"
        time.sleep(step)


def finished(stack, job):
    j = stack.store.job(job)
    return j if j["status"] in (Status.SUCCEEDED, Status.FAILED) else None


def run_dir(stack, attempt) -> Path:
    return Path(attempt["output_dir"])


def step_running(stack, job, attempt_number, step="spark_pipeline"):
    """The attempt's step has started its process (the launcher holds the lock and the log exists)."""
    attempts = stack.store.attempts(job)
    if len(attempts) < attempt_number:
        return False
    return (run_dir(stack, attempts[attempt_number - 1]) / "logs" / f"{step}.log").exists()


def job_of(stack, marker_value):
    """The job id a marker of this store names, or None."""
    owner = processes.parse_marker(marker_value)
    if owner is None or owner[0] != stack.store_id:
        return None
    return int(owner[1].split("-")[1])


def attempt_procs(stack, run_id):
    """The live processes of one attempt of this store (exact run id, never a prefix)."""
    found = []
    for value, procs in processes.marked_processes().items():
        owner = processes.parse_marker(value)
        if owner is not None and owner[0] == stack.store_id and owner[1] == run_id:
            found += procs
    return found


def claimed_by_a(stack):
    """Worker A claims a calendar-year job; only then does standby B join the group, so the
    job is A's, whatever partition assignment the group would have made with both present."""
    a = stack.worker("A")
    job = stack.submit(CALENDAR)
    wait_until(lambda: stack.store.attempts(job), 300, "worker A's claim")
    assert stack.store.attempts(job)[0]["worker_id"] == "A"
    stack.worker("B")
    return a, job


def launcher_intervals(stack) -> list[tuple[float, float, str]]:
    """Every started step's interval on the monotonic clock. A launcher that never started its
    step records neither end; one that did must record both, so a missing end fails here."""
    intervals = []
    for path in sorted((stack.output / stack.store_id).glob("job-*-attempt-*/logs/*.launcher.json")):
        result = json.loads(path.read_text())
        if "step_started_mono" in result:
            intervals.append((result["step_started_mono"], result["tree_ended_mono"], str(path)))
    return sorted(intervals)


def check(stack, references, job, params, *, attempts=None):
    j = stack.store.job(job)
    rows = stack.store.attempts(job)
    accepted = [a for a in rows if a["outcome"] is Outcome.ACCEPTED]
    assert j["status"] is Status.SUCCEEDED and len(accepted) == 1, (j, rows)
    if attempts is not None:
        assert len(rows) == attempts, rows
    a = accepted[0]
    record = json.loads((run_dir(stack, a) / "attempt.json").read_text())
    folder = run_dir(stack, a) / record["run_folder"]
    assert a["result_digest"] == runs.folder_digest(folder)
    reference = references(params)
    for table, key in ccm.TABLE_KEYS.items():
        problems, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(folder, table), key,
                                             ccm.cpm.BREACH_FIELDS.get(table, []))
        assert problems == [], (table, problems)
    assert stack.store.invariant_violations() == {}
    intervals = launcher_intervals(stack)
    for (s1, e1, p1), (s2, e2, p2) in zip(intervals, intervals[1:]):
        assert s2 >= e1, f"overlapping steps:\n  {p1} until {e1}\n  {p2} from {s2}"
    assert not [v for v in processes.marked_processes() if job_of(stack, v) == job]   # nothing of this job left
    assert spark_scratch() <= stack.scratch_before, spark_scratch() - stack.scratch_before
    return a, record


def test_a_calendar_year_job_and_a_stride_21_job_succeed(services, references):
    stack = services
    stack.worker("A")
    calendar, rolling = stack.submit(CALENDAR), stack.submit(ROLLING)
    for job, params in ((calendar, CALENDAR), (rolling, ROLLING)):
        wait_until(lambda: finished(stack, job), 900, f"job {job}")
        _, record = check(stack, references, job, params, attempts=1)
        print(f"job {job} {params['kind']}: " + ", ".join(
            f"{s['name']} {s['seconds']} s, peak {s['peak_rss_bytes'] / 2**30:.2f} GiB" for s in record["steps"]))
    assert stack.cli("status", "--check").returncode == 0


def test_a_worker_killed_during_step_2_leaves_nothing_and_the_job_is_recovered(services, references):
    stack = services
    a, job = claimed_by_a(stack)                                    # then B joins as a standby
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    time.sleep(3)
    first = stack.store.attempts(job)[0]
    a.kill()                                                       # SIGKILL: the lifeline (EOF) ends the tree
    wait_until(lambda: not attempt_procs(stack, first["run_id"]), 7 + 3, "the end of attempt 1's tree")
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    _, record = check(stack, references, job, CALENDAR, attempts=2)
    assert [r["outcome"] for r in stack.store.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    result = json.loads((run_dir(stack, first) / "logs" / "spark_pipeline.launcher.json").read_text())
    assert result["outcome"] == "eof"


def test_a_stopped_worker_is_outlived_by_its_watchdog_and_fenced_when_it_resumes(services, references):
    """Worker-only SIGSTOP during step 2. Before SIGCONT: attempt 1's tree is gone by its
    deadline plus the kill grace; attempt 2's Spark step started after attempt 1's tree
    ended; attempt 1's renewal count no longer changes. After SIGCONT, worker A is fenced
    and writes nothing."""
    stack = services
    a, job = claimed_by_a(stack)                                    # then B joins as a standby
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    os.kill(a.pid, signal.SIGSTOP)
    stopped = time.monotonic()
    first = stack.store.attempts(job)[0]
    wait_until(lambda: not attempt_procs(stack, first["run_id"]), 14 + 0.5 + 7 + 5,
               "the watchdog to end attempt 1's tree")
    assert time.monotonic() - stopped <= 14 + 0.5 + 7 + 5          # F is at most 14 s after the last renewal
    wait_until(lambda: finished(stack, job), 600, f"job {job}")   # attempt 2, by worker B, while A is stopped
    rows = stack.store.attempts(job)
    renewals_at_takeover = rows[0]["renewals"]
    one = json.loads((run_dir(stack, rows[0]) / "logs" / "spark_pipeline.launcher.json").read_text())
    two = json.loads((run_dir(stack, rows[1]) / "logs" / "spark_pipeline.launcher.json").read_text())
    assert one["outcome"] == "deadline"
    assert two["step_started_mono"] >= one["tree_ended_mono"]
    os.kill(a.pid, signal.SIGCONT)
    wait_until(lambda: any(e["event"] == "fenced" for e in stack.events("A")), 60, "worker A to see it was fenced")
    time.sleep(3)
    assert stack.store.attempts(job)[0]["renewals"] == renewals_at_takeover
    check(stack, references, job, CALENDAR, attempts=2)


def test_a_whole_stopped_tree_keeps_the_replacement_from_starting_spark(services, references):
    """Whole-tree SIGSTOP (worker, launcher, Spark). Before SIGCONT: the replacement, worker
    B, starts no step; it waits on the host lock, and only the frozen tree exists. After
    SIGCONT the frozen launcher's deadline has passed: it ends its tree at once, and B goes on."""
    stack = services
    a, job = claimed_by_a(stack)                                    # then B joins as a standby
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    first = stack.store.attempts(job)[0]
    frozen = [psutil.Process(a.pid)] + attempt_procs(stack, first["run_id"])
    for p in frozen:
        p.suspend()
    wait_until(lambda: len(stack.store.attempts(job)) == 2, 120, "worker B to take attempt 2 over")
    time.sleep(10)                                                 # B's launcher is waiting for the lock
    second = stack.store.attempts(job)[1]
    assert not (run_dir(stack, second) / "logs" / "windows.log").exists()       # no step of attempt 2 started
    waiting = attempt_procs(stack, second["run_id"])
    assert [p.cmdline()[2] for p in waiting] == ["etf_risk.jobs.launcher"]   # only attempt 2's launcher, waiting
    for p in reversed(frozen):
        p.resume()
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    one = json.loads((run_dir(stack, first) / "logs" / "spark_pipeline.launcher.json").read_text())
    assert one["outcome"] == "deadline"
    check(stack, references, job, CALENDAR, attempts=2)


def test_a_step_over_its_limit_is_ended_and_retried_until_the_attempts_run_out(stack):
    stack.start("reconciler", "reconciler", extra=("--interval", "2"))
    stack.worker("A", "--timing", "spark_pipeline_limit=5")
    try:
        job = stack.submit(CALENDAR)
        j = wait_until(lambda: finished(stack, job), 600, f"job {job}")
        rows = stack.store.attempts(job)
        assert j["status"] is Status.FAILED and [r["outcome"] for r in rows] == [Outcome.FAILED] * 3
        assert all("timeout" in r["error"] for r in rows)
        assert stack.store.invariant_violations() == {}
        assert not [v for v in processes.marked_processes() if v.startswith(stack.store_id + ":")]
    finally:
        stack.stop_all()


@pytest.mark.parametrize("stall", ["lock-tables", "pause", "restart"])
def test_a_database_stall_during_a_run_needs_no_manual_restart(services, references, stall):
    stack = services
    stack.worker("A")
    job = stack.submit(CALENDAR)
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    if stall == "lock-tables":
        from etf_risk.jobs import mysql
        holder = mysql.connect_mysql(stack.db)
        with holder.cursor() as cursor:
            cursor.execute("LOCK TABLES jobs WRITE")
            time.sleep(8)
            cursor.execute("UNLOCK TABLES")
        holder.close()
    elif stall == "pause":
        subprocess.run([*COMPOSE, "pause", "mysql"], check=True, capture_output=True)
        time.sleep(8)
        subprocess.run([*COMPOSE, "unpause", "mysql"], check=True, capture_output=True)
    else:
        subprocess.run([*COMPOSE, "restart", "mysql"], check=True, capture_output=True, timeout=120)
        subprocess.run([sys.executable, "-m", "etf_risk.services", "ready", "mysql"], check=True,
                       capture_output=True, timeout=180, env={**os.environ, "ETF_RISK_MYSQL_URL": MYSQL_URL})
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    check(stack, references, job, CALENDAR)
    assert stack.procs["A"].poll() is None and stack.procs["reconciler"].poll() is None   # both still serving
    renewal_failures = [e for e in stack.events("A") if e["event"] == "renewal_failed"]
    print(f"{stall}: {len(renewal_failures)} failed renewals; attempts "
          f"{[r['outcome'].value for r in stack.store.attempts(job)]}")


def test_a_kafka_restart_during_a_run_needs_no_manual_restart(services, references):
    stack = services
    stack.worker("A")
    job = stack.submit(CALENDAR)
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    subprocess.run([*COMPOSE, "restart", "kafka"], check=True, capture_output=True, timeout=120)
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    check(stack, references, job, CALENDAR, attempts=1)
    second = wait_until(lambda: _submit_when_kafka_is_back(stack), 120, "a submission after the restart")
    wait_until(lambda: finished(stack, second), 600, f"job {second}")
    check(stack, references, second, CALENDAR)


def _submit_when_kafka_is_back(stack):
    out = stack.cli("submit", "--snapshot", SNAPSHOT, "--kind", "calendar-year", check=False)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout)["job_id"]


def test_a_starting_worker_keeps_another_workers_running_attempt(services, references):
    stack = services
    stack.worker("A")
    job = stack.submit(CALENDAR)
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    stack.worker("B")
    sweep = wait_until(lambda: next((e for e in stack.events("B") if e["event"] == "sweep"), None), 60, "B's sweep")
    assert sweep["preserved"] == 1 and sweep["terminated"] == 0
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    check(stack, references, job, CALENDAR, attempts=1)
