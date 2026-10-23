"""SubprocessPipeline offline: stand-in steps (small scripts) behind real launchers.

The steps write what windows, spark_pipeline and verify write, or misbehave on purpose. A
scripted heartbeat stands in for the job store's renewals. The tests cover:
- the result rule, attempt.json, manifest.json and the digest;
- renewals that are refused, fail, or hang;
- the watchdog ending a tree while the worker thread is stuck;
- stopping;
- the classification of failures;
- the step environment.
The real steps run in tests/test_jobs_worker_spark.py.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np
import psutil
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import runs
from etf_risk.jobs import processes
from etf_risk.jobs.params import JobParams, input_checksums
from etf_risk.jobs.pipeline import SubprocessPipeline
from etf_risk.jobs.store import Claim
from etf_risk.jobs.timing import Timing
from etf_risk.jobs.worker import Fenced, PipelineError

STORE = "e" * 32
TIMING = Timing(lease=8.0, renew_interval=0.5, fence_margin=1.5, worker_tick=0.1, watchdog_tick=0.1,
                term_grace=0.5, kill_confirm=0.5, safety=0.4, windows_limit=20, spark_pipeline_limit=20,
                verify_limit=20, attempt_limit=60, session_timeout=6.0, heartbeat_interval=2.0)

SPARK = r"""
import json, os, sys
folder, status, checks = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(folder)
for table in ("window_stats", "path_days", "path_summary", "paired"):
    os.makedirs(os.path.join(folder, table))
    open(os.path.join(folder, table, "part-0.parquet"), "wb").write(b"rows of " + table.encode())
    open(os.path.join(folder, table, "_SUCCESS"), "w").close()
json.dump({"g": {"c": checks}}, open(os.path.join(folder, "checks.json"), "w"))
json.dump({"status": status}, open(os.path.join(folder, "run.json"), "w"))
sys.exit(int(sys.argv[4]))
"""
VERIFY = r"""
import json, os, sys
json.dump({"mismatch_count": int(sys.argv[2]), "breached_windows": {"same": True}},
          open(os.path.join(sys.argv[1], "verify.json"), "w"))
sys.exit(int(sys.argv[3]))
"""
TREE = r"""
import json, os, subprocess, sys, time
child = subprocess.Popen([sys.executable, "-c", "import os, time; os.setpgid(0, 0); time.sleep(600)"])
with open(sys.argv[1] + ".tmp", "w") as f:
    json.dump({"step": os.getpid(), "child": child.pid}, f)
os.replace(sys.argv[1] + ".tmp", sys.argv[1])
time.sleep(float(sys.argv[2]))
"""
ENV = r"""
import json, os, sys
json.dump(dict(os.environ), open(sys.argv[1], "w"))
"""


class Steps(SubprocessPipeline):
    """The pipeline with stand-in steps; plan maps a step to its argv after the interpreter."""

    def __init__(self, tmp_path, plan, **kwargs):
        super().__init__(store_id=STORE, processed_root=tmp_path / "processed", worker_id="worker-test",
                         lock_path=tmp_path / "locks" / "host.lock", timing=TIMING, **kwargs)
        self.plan = plan

    def commands(self, params, claim, run_dir):
        folder = str(self.run_folder(params, claim, run_dir))
        return [(name, [self.python, "-c", *[a.replace("{run}", folder) for a in self.plan[name]]])
                for name in ("windows", "spark_pipeline", "verify")]


def good(spark=("ok", "0", "0"), verify=("0", "0")):
    return {"windows": ["import sys; sys.exit(0)"],
            "spark_pipeline": [SPARK, "{run}", *spark],
            "verify": [VERIFY, "{run}", *verify]}


class Heartbeat:
    """Scripted renewals: answers, one per call, then repeat the last; a callable answer is
    called (to block or raise)."""

    def __init__(self, *answers):
        self.answers, self.calls = list(answers) or [True], 0
        self.claimed_mono = time.monotonic()

    def __call__(self):
        answer = self.answers[min(self.calls, len(self.answers) - 1)]
        self.calls += 1
        return answer() if callable(answer) else answer


@pytest.fixture
def claim(tmp_path):
    dates = nyse_sessions("2024-01-02", 31)
    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(1).normal(0, 0.01, 30))})
    params = JobParams("snap", "rolling", window_days=8, stride=21, anchor="2024-01-02", sample_ticker="AAA")
    run_dir = tmp_path / "runs" / "job-1-attempt-1"
    run_dir.mkdir(parents=True)
    return Claim(1, 1, "t" * 32, "job-1-attempt-1", run_dir, 3, params.to_dict(),
                 input_checksums(tmp_path / "processed", "snap"))


def wait_for(path, timeout=20.0):
    deadline = time.monotonic() + timeout
    while not Path(path).exists():
        assert time.monotonic() < deadline, f"{path} never appeared"
        time.sleep(0.05)
    return json.loads(Path(path).read_text())


def gone(pid):
    try:
        return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return True


@pytest.fixture(autouse=True)
def kill_leftovers():
    yield
    for value, procs in processes.marked_processes().items():
        if value.startswith(STORE + ":"):
            for p in procs:
                try:
                    p.kill()
                except psutil.Error:
                    pass


def test_a_good_run_is_recorded_and_returns_the_digest_of_its_run_folder(tmp_path, claim):
    pipeline = Steps(tmp_path, good())
    digest = pipeline.run(claim, claim.output_dir, Heartbeat())
    run_folder = claim.output_dir / "output" / "snap" / "rolling-8-s21" / "job-1-attempt-1"
    assert digest == runs.folder_digest(run_folder)
    assert json.loads((claim.output_dir / "manifest.json").read_text()) == runs.manifest(run_folder)
    record = json.loads((claim.output_dir / "attempt.json").read_text())
    assert [(s["name"], s["outcome"], s["returncode"]) for s in record["steps"]] == [
        ("windows", "exited", 0), ("spark_pipeline", "exited", 0), ("verify", "exited", 0)]
    assert record["code"]["source_sha256"]["jobs/pipeline.py"] and record["store_id"] == STORE
    assert not (claim.output_dir / ".work").exists()
    assert pipeline.fence_at > time.monotonic()                   # renewed just before acceptance


@pytest.mark.parametrize("plan, retryable, words", [
    (good(spark=("ok", "0", "3")), False, "input checksum differs"),
    (good(spark=("checks_failed", "1", "1")), False, "checks failed"),
    (good(spark=("failed", "0", "2")), True, "with status failed"),
    (good(verify=("2", "1")), False, "2 mismatches"),
    (good(verify=("0", "1")), True, "without a clean verify.json"),
    ({**good(), "windows": ["import sys; sys.exit(1)"]}, True, "windows exited 1"),
    ({**good(), "windows": ["import time; time.sleep(60)"]}, True, "timeout"),
])
def test_failures_are_classified_from_the_records(tmp_path, claim, plan, retryable, words):
    timing = TIMING.__class__(**{**TIMING.__dict__, "windows_limit": 1.0})
    pipeline = Steps(tmp_path, plan)
    pipeline.timing = timing
    with pytest.raises(PipelineError, match=words) as failed:
        pipeline.run(claim, claim.output_dir, Heartbeat())
    assert failed.value.retryable is retryable


def test_inputs_that_changed_since_the_submission_fail_for_good_before_any_step(tmp_path, claim):
    (tmp_path / "processed" / "snap" / "quality_report.json").write_text('{"unverified_extreme_days": [1]}')
    with pytest.raises(PipelineError, match="inputs changed") as failed:
        Steps(tmp_path, good()).run(claim, claim.output_dir, Heartbeat())
    assert failed.value.retryable is False and not (claim.output_dir / "logs").exists()


def tree_plan(tmp_path, seconds=600):
    pids = tmp_path / "tree.pids"
    return {**good(), "spark_pipeline": [TREE, str(pids), str(seconds)]}, pids


class Switch:
    """Renewals that succeed until the step's tree is up (its pids file exists), then answer
    with then(): independent of how many renewals the earlier steps took."""

    def __init__(self, pids_file, then):
        self.pids_file, self.then, self.claimed_mono = pids_file, then, time.monotonic()

    def __call__(self):
        return True if not Path(self.pids_file).exists() else self.then()


def test_a_refused_renewal_ends_the_step_tree_and_fences_the_attempt(tmp_path, claim):
    plan, pids_file = tree_plan(tmp_path)
    beats = Switch(pids_file, lambda: False)                      # refused once the Spark step runs
    with pytest.raises(Fenced, match="fenced"):
        Steps(tmp_path, plan).run(claim, claim.output_dir, beats)
    pids = json.loads(pids_file.read_text())
    assert all(gone(p) for p in pids.values())
    step = json.loads((claim.output_dir / "logs" / "spark_pipeline.launcher.json").read_text())
    assert step["outcome"] == "eof" and set(pids.values()) <= set(step["ended"]["terminated"])


def test_failing_renewals_fence_the_worker_by_its_deadline_and_no_step_starts_after_it(tmp_path, claim):
    plan, pids_file = tree_plan(tmp_path)

    def down():
        raise ConnectionError("database unreachable")
    beats = Switch(pids_file, down)
    # Both layers act at the same deadline F: the worker fences itself and closes the pipe, and
    # the launcher's watchdog fires; whichever comes first ends the tree.
    with pytest.raises(Fenced, match="self_fenced|deadline"):
        Steps(tmp_path, plan).run(claim, claim.output_dir, beats)
    pids = json.loads(pids_file.read_text())
    assert all(gone(p) for p in pids.values())
    assert not (claim.output_dir / "logs" / "verify.launcher.json").exists()     # verify never started


def test_while_the_worker_is_stuck_in_a_renewal_the_watchdog_ends_the_tree_before_the_lease_expires(tmp_path, claim):
    """The worker thread blocks inside a database call for longer than the lease: the launcher
    acts on its last absolute deadline F alone, and the tree is gone by F + t_w + G."""
    plan, pids_file = tree_plan(tmp_path)
    release, renewed = threading.Event(), []

    def renewal_then_hang():
        if not renewed:
            renewed.append(time.monotonic())                      # m0 of the last renewal that succeeds
            return True
        release.wait(30)                                          # then a database call that hangs
        return False
    beats = Switch(pids_file, renewal_then_hang)
    result = {}
    worker = threading.Thread(target=lambda: result.setdefault("error", _capture(
        lambda: Steps(tmp_path, plan).run(claim, claim.output_dir, beats))))
    worker.start()
    pids = wait_for(pids_file)
    while not all(gone(p) for p in pids.values()):
        time.sleep(0.05)
    died = time.monotonic()
    m0 = renewed[-1]
    deadline = m0 + TIMING.lease - TIMING.fence_margin
    assert died <= deadline + TIMING.watchdog_tick + TIMING.kill_grace + 1.0      # +1 s for this test's polling
    assert died < m0 + TIMING.lease                                                # before the lease could expire
    assert worker.is_alive()                                                       # the worker was still stuck
    release.set()
    worker.join(30)
    assert isinstance(result["error"], Fenced)


def _capture(call):
    try:
        call()
    except BaseException as error:  # noqa: BLE001 - handed back to the test
        return error
    return None


def test_a_stopped_worker_ends_the_running_step_and_the_job_is_retried(tmp_path, claim):
    plan, pids_file = tree_plan(tmp_path)
    stop = threading.Event()
    pipeline = Steps(tmp_path, plan, stop=stop)
    threading.Timer(0.1, lambda: (wait_for(pids_file), stop.set())).start()
    with pytest.raises(PipelineError, match="stopped") as stopped:
        pipeline.run(claim, claim.output_dir, Heartbeat())
    assert stopped.value.retryable and all(gone(p) for p in json.loads(pids_file.read_text()).values())


def test_the_step_environment_is_an_allowlist_with_the_marker_and_the_scratch_folders(tmp_path, claim, monkeypatch):
    monkeypatch.setenv("ETF_RISK_MYSQL_URL", "mysql://root:secret@127.0.0.1:3307/jobs")
    monkeypatch.setenv("ETF_RISK_KAFKA_BOOTSTRAP", "127.0.0.1:9094")
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-Dsomething")
    env_file = tmp_path / "env.json"
    plan = {**good(), "windows": [ENV, str(env_file)]}
    Steps(tmp_path, plan).run(claim, claim.output_dir, Heartbeat())
    env = json.loads(env_file.read_text())
    work = str(claim.output_dir.resolve() / ".work")
    assert not {"ETF_RISK_MYSQL_URL", "ETF_RISK_KAFKA_BOOTSTRAP", "JAVA_TOOL_OPTIONS", "_JAVA_OPTIONS"} & set(env)
    assert env[processes.MARKER_ENV] == f"{STORE}:job-1-attempt-1:{processes.attempt_key('t' * 32)}"
    assert (env["TMPDIR"], env["SPARK_LOCAL_DIRS"]) == (f"{work}/tmp", f"{work}/spark")
    assert env["SPARK_SUBMIT_OPTS"] == f"-Djava.io.tmpdir={work}/jtmp -XX:-UsePerfData"
    assert env["PYSPARK_PYTHON"] == env["PYSPARK_DRIVER_PYTHON"] == sys.executable
    assert env["PATH"].split(os.pathsep)[0] == str(Path(sys.executable).parent)


def test_a_renewal_refused_just_before_acceptance_fences_the_attempt(tmp_path, claim):
    """The last renewal comes after every step and the records: a takeover meanwhile means no digest is returned."""
    beats = Switch(claim.output_dir / "manifest.json", lambda: False)   # written just before that renewal
    with pytest.raises(Fenced, match="before acceptance"):
        Steps(tmp_path, good()).run(claim, claim.output_dir, beats)
    assert (claim.output_dir / "manifest.json").exists()             # written, but never accepted


def test_the_result_rule_refuses_check_violations_even_with_status_ok(tmp_path, claim):
    with pytest.raises(PipelineError, match="1 check violations") as failed:
        Steps(tmp_path, good(spark=("ok", "1", "0"))).run(claim, claim.output_dir, Heartbeat())
    assert failed.value.retryable is False
