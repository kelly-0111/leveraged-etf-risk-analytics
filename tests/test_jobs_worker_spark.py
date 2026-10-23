"""The worker with the real pipeline: a job on a small synthetic snapshot runs windows →
spark_pipeline → verify behind launchers, in fresh processes, and its accepted result is
bound to its run digest. It matches, by content, a direct run of the same definitions in this
test's Spark session, under the comparison rules of the earlier experiments
(analysis/collect_partition_measurements.py, compare_tables).

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import runs, spark_pipeline
from etf_risk.jobs import processes
from etf_risk.jobs.params import JobParams, input_checksums
from etf_risk.jobs.pipeline import SubprocessPipeline
from etf_risk.jobs.store import SQLITE, JobStore, Outcome, Status, open_sqlite
from etf_risk.jobs.worker import Result, Worker
from etf_risk.windows import build_definitions, write_definitions

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "analysis"))
_spec = importlib.util.spec_from_file_location("collect_caching_measurements",
                                               REPO / "analysis" / "collect_caching_measurements.py")
ccm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ccm)

pytestmark = pytest.mark.spark
ANCHOR = "2024-01-02"


def spark_scratch():
    """The names Spark, PySpark and the JVM leave in the temporary folders when a run is killed."""
    names = set()
    for folder in {Path("/private/tmp"), Path(tempfile.gettempdir())}:
        if folder.is_dir():
            names |= {p.name for p in folder.iterdir() if p.name.startswith(
                ("spark-", "blockmgr-", "pyspark-", "snappy-", "libzstd-jni", "liblz4-java", "hsperfdata_"))}
    return names


def test_a_job_runs_the_real_steps_and_its_accepted_result_matches_a_direct_run(spark, tmp_path):
    rng = np.random.default_rng(23)
    dates = nyse_sessions(ANCHOR, 61)
    returns = rng.normal(0, 0.02, 60)
    returns[24] = -0.55             # a 2x breach on row 25, inside the window of rows 22-29 (8 days, stride 21)
    snap = write_snapshot(tmp_path, "snap", {"AAA": (dates, rng.normal(0, 0.02, 60)), "BBB": (dates, returns)},
                          unverified=[{"ticker": "BBB", "date": str(dates[25])}])
    params = JobParams("snap", "rolling", window_days=8, stride=21, anchor=ANCHOR, sample_ticker="AAA")
    store = JobStore(open_sqlite(tmp_path / "jobs.sqlite", create=True), SQLITE)
    store_id = store.ensure_identity()
    job = store.submit(params.to_dict(), input_checksums(tmp_path / "processed", "snap"))
    pipeline = SubprocessPipeline(store_id=store_id, processed_root=tmp_path / "processed", worker_id="worker-e2e",
                                  lock_path=tmp_path / "locks" / "spark-exec.lock")
    worker = Worker(store, pipeline, tmp_path / "runs" / store_id, worker_id="worker-e2e")
    scratch_before = spark_scratch()

    handled = worker.handle(job, lambda: None)

    assert handled.result is Result.ACCEPTED, (tmp_path / "runs").rglob("*.log")
    [attempt] = store.attempts(job)
    run_dir = Path(attempt["output_dir"])
    run_folder = run_dir / "output" / "snap" / params.windows_name / attempt["run_id"]
    assert (store.job(job)["status"], attempt["outcome"]) == (Status.SUCCEEDED, Outcome.ACCEPTED)
    assert attempt["result_digest"] == runs.folder_digest(run_folder)
    assert store.invariant_violations() == {}
    record = json.loads((run_folder / "run.json").read_text())
    assert record["status"] == "ok" and not record["environment"]["java"].startswith("Picked up")
    assert "jobs/pipeline.py" in record["code"]["source_sha256"]
    verified = json.loads((run_folder / "verify.json").read_text())
    assert verified["mismatch_count"] == 0 and verified["breached_windows"] == {"python": 1, "spark": 1, "same": True}
    attempt_record = json.loads((run_dir / "attempt.json").read_text())
    assert [s["outcome"] for s in attempt_record["steps"]] == ["exited"] * 3
    assert all(s["peak_rss_bytes"] > 0 for s in attempt_record["steps"])
    assert not (run_dir / ".work").exists() and not any(processes.marked_processes())
    assert spark_scratch() <= scratch_before                         # nothing left in the temporary folders
    assert not (REPO / "spark-warehouse").exists() or (REPO / "spark-warehouse").stat().st_mtime < os.path.getmtime(
        tmp_path)

    # The same definitions run directly, in this test's Spark session.
    windows = write_definitions(*build_definitions(snap, "rolling", window_days=8, stride=21, anchor=ANCHOR),
                                tmp_path / "ref" / "w")
    assert spark_pipeline.main(["--windows", str(windows), "--out-root", str(tmp_path / "ref" / "out"),
                                "--run-id", "direct"]) == 0
    direct = tmp_path / "ref" / "out" / "snap" / windows.name / "direct"
    for table, key in ccm.TABLE_KEYS.items():
        problems, _ = ccm.cpm.compare_tables(ccm.read_table(direct, table), ccm.read_table(run_folder, table), key,
                                             ccm.cpm.BREACH_FIELDS.get(table, []))
        assert problems == [], (table, problems)
