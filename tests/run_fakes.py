"""Run folders and job tables for the tests of etf_risk.runs and etf_risk.summary: a run folder
reduced to the files the worker's acceptance rule reads, and a job table on SQLite whose
connection records every statement it runs.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import shutil

from etf_risk import runs
from etf_risk.jobs.params import JobParams
from etf_risk.jobs.pipeline import SubprocessPipeline
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite

PARAMS = {"snapshot": "snap", "kind": "calendar-year"}


def write_run(folder, *, status="ok", violations=0, mismatches=0, same=True, with_verify_json=True, success=runs.TABLES,
              verify_run=None):
    """A run folder as spark_pipeline and verify leave it, reduced to what is checked."""
    for table in runs.TABLES:
        (folder / table).mkdir(parents=True, exist_ok=True)
        (folder / table / "part-00000.parquet").write_bytes(table.encode() * 50)
        if table in success:
            (folder / table / "_SUCCESS").write_bytes(b"")
    (folder / "run.json").write_text(json.dumps({"status": status, "run_id": folder.name}))
    (folder / "checks.json").write_text(json.dumps({"pairing": {"unpaired": violations}, "nav_sanity": {"negative": 0}}))
    if with_verify_json:
        (folder / "verify.json").write_text(json.dumps({"run": str(verify_run or folder), "mismatch_count": mismatches,
                                                        "breached_windows": {"same": same}}))
    return folder


def job_table(path) -> JobStore:
    """A new job table with its store id; store.statements lists the SQL its connection ran."""
    connection = open_sqlite(path, create=True)
    statements = []
    connection.set_trace_callback(statements.append)
    store = JobStore(connection, SQLITE)
    store.ensure_identity()
    store.statements = statements
    return store


def accepted_job(store, output_root, *, copy_of=None):
    """A job that succeeded, its accepted attempt's run folder where the worker writes it:
    written afresh, or a byte-for-byte copy of copy_of (then both folders have one digest)."""
    job_id = store.submit(PARAMS, {"daily_returns/AAA.parquet": "0" * 64})
    claim = store.claim(job_id, "worker-a", output_root)
    folder = SubprocessPipeline.run_folder(JobParams.from_dict(PARAMS), claim, claim.output_dir)
    if copy_of is None:
        write_run(folder)
    else:
        shutil.copytree(copy_of, folder)
    assert store.accept_result(claim, runs.folder_digest(folder))
    return job_id, folder
