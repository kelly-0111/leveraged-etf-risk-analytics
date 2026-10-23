"""The startup sweep: a starting worker ends the processes of this store's attempts that are no
longer valid, keeps those of a valid active attempt (whoever runs it), leaves other stores'
alone, and removes only the scratch of attempts that ended. With the database out of reach
it does nothing.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
import subprocess
import sys
import time

import psutil
import pytest

from etf_risk.jobs import processes
from etf_risk.jobs.pipeline import startup_sweep
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite


def marked(value):
    """A process that carries the marker, as a step of that attempt would."""
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"],
                            env={**os.environ, processes.MARKER_ENV: value}, start_new_session=True)


@pytest.fixture
def store(tmp_path):
    store = JobStore(open_sqlite(tmp_path / "jobs.sqlite", create=True), SQLITE)
    store.ensure_identity()
    return store


def wait_marked(*values, timeout=10.0):
    deadline = time.monotonic() + timeout
    while not set(values) <= set(processes.marked_processes()):
        assert time.monotonic() < deadline, "the marked processes never showed up"
        time.sleep(0.05)


def test_the_sweep_ends_only_what_is_no_longer_valid(tmp_path, store):
    root = tmp_path / "runs" / store.store_id()
    running_job = store.submit({"n": 1}, {})
    running = store.claim(running_job, "worker-A", root)               # valid and active (worker A's)
    ended_job = store.submit({"n": 2}, {})
    ended = store.claim(ended_job, "worker-B", root)
    store.fail_attempt(ended, "boom", retryable=True)                  # attempt 1 ended; the job is queued again
    for claim in (running, ended):
        (claim.output_dir / ".work" / "tmp").mkdir(parents=True)
    valid = processes.marker(store.store_id(), running.run_id, running.token)
    stale = processes.marker(store.store_id(), ended.run_id, ended.token)
    other = processes.marker("o" * 32, "job-1-attempt-1", "x" * 32)
    procs = {name: marked(value) for name, value in (("valid", valid), ("stale", stale), ("other", other))}
    try:
        wait_marked(valid, stale, other)
        report = startup_sweep(store, root)
        assert report["preserved"] == [valid] and report["other_stores"] == [other]
        assert [t["marker"] for t in report["terminated"]] == [stale]
        assert procs["stale"].wait(timeout=10) is not None
        assert procs["valid"].poll() is None and procs["other"].poll() is None
        assert report["scratch_removed"] == [ended.run_id]
        assert (running.output_dir / ".work").is_dir() and not (ended.output_dir / ".work").exists()
        assert ended.output_dir.is_dir()                                # a folder is never removed
    finally:
        for p in procs.values():
            p.kill()
            p.wait()


def test_with_the_database_out_of_reach_the_sweep_does_nothing(tmp_path, store):
    store.connection.close()
    stale = marked(processes.marker(store.store_id(), "job-9-attempt-1", "y" * 32))
    try:
        wait_marked(processes.marker(store.store_id(), "job-9-attempt-1", "y" * 32))
        assert startup_sweep(store, tmp_path) == {"skipped": True}
        assert psutil.Process(stale.pid).is_running()
    finally:
        stale.kill()
        stale.wait()
