"""The job queue's commands on a SQLite job table, offline. Kafka is replaced by a fake
publisher; the worker and reconciler commands run against the services in
tests/test_jobs_live_pipeline.py.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json

import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk.jobs import cli
from etf_risk.jobs.events import read_events
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite
from etf_risk.provenance import code_identity


class FakePublisher:
    published: list = []

    def __init__(self, bootstrap, topic, **kwargs):
        self.topic = topic

    def publish(self, job_id):
        FakePublisher.published.append((self.topic, job_id))
        return True

    def close(self):
        pass


@pytest.fixture
def setup(tmp_path, monkeypatch):
    dates = nyse_sessions("2024-01-02", 31)
    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(2).normal(0, 0.01, 30))})
    monkeypatch.setattr("etf_risk.jobs.kafka.KafkaPublisher", FakePublisher)
    FakePublisher.published = []
    db = f"sqlite:///{tmp_path / 'jobs.sqlite'}"
    base = ["--db", db, "--output-root", str(tmp_path / "out"), "--processed-root", str(tmp_path / "processed")]
    return db, base, tmp_path


def run(capsys, *argv):
    code = cli.main(list(argv))
    return code, capsys.readouterr().out


def test_init_db_writes_one_store_id_and_keeps_it(setup, capsys):
    db, base, _ = setup
    code, out = run(capsys, "init-db", *base)
    first = json.loads(out)["store_id"]
    assert code == 0 and json.loads(run(capsys, "init-db", *base)[1])["store_id"] == first


def test_submit_records_the_parameters_and_the_input_checksums(setup, capsys):
    db, base, tmp_path = setup
    run(capsys, "init-db", *base)
    code, out = run(capsys, "submit", *base, "--snapshot", "snap", "--kind", "rolling", "--window-days", "8",
                    "--anchor", "2024-01-02", "--sample-ticker", "AAA")
    assert code == 0 and json.loads(out) == {"job_id": 1, "published": True, "recorded": True}
    job = JobStore(open_sqlite(tmp_path / "jobs.sqlite"), SQLITE).job(1)
    assert job["params"] == {"snapshot": "snap", "kind": "rolling", "window_days": 8, "stride": 21,
                             "anchor": "2024-01-02", "sample_ticker": "AAA"}
    assert sorted(job["input_checksums"]) == ["daily_returns/AAA.parquet", "quality_report.json"]
    assert FakePublisher.published == [("etf-risk-jobs", 1)]
    events = read_events(tmp_path / "out" / "events" / "submit.jsonl")
    assert [e["event"] for e in events] == ["started", "submitted"]
    assert events[0]["code"] == code_identity()                    # the code identity, recorded at launch


def test_unusable_parameters_are_refused_before_anything_is_written(setup, capsys):
    db, base, tmp_path = setup
    run(capsys, "init-db", *base)
    with pytest.raises(SystemExit, match="at least 21"):
        cli.main(["submit", *base, "--snapshot", "snap", "--kind", "rolling", "--stride", "7"])
    assert JobStore(open_sqlite(tmp_path / "jobs.sqlite"), SQLITE).all_jobs() == []


def test_status_check_export_and_cleanup(setup, capsys):
    db, base, tmp_path = setup
    store_id = json.loads(run(capsys, "init-db", *base)[1])["store_id"]
    store = JobStore(open_sqlite(tmp_path / "jobs.sqlite"), SQLITE)
    job = store.submit({"snapshot": "snap", "kind": "rolling"}, {})
    claim = store.claim(job, "worker-A", tmp_path / "out" / store_id)
    claim.output_dir.mkdir(parents=True)
    assert store.fail_attempt(claim, "boom", retryable=True).value == "queued"
    code, out = run(capsys, "status", *base, "--check")
    assert code == 0 and "1 jobs 1 queued" in out and "attempts 1:failed" in out and "all hold" in out
    code, out = run(capsys, "cleanup", *base)
    assert code == 0 and "job-1-attempt-1" in out and "nothing was deleted" in out and claim.output_dir.exists()
    code, out = run(capsys, "export", *base, str(tmp_path / "export"))
    exported = {p.name: json.loads(p.read_text()) for p in (tmp_path / "export").iterdir()}
    assert exported["store.json"]["store_id"] == store_id and exported["invariant_violations.json"] == {}
    assert [a["outcome"] for a in exported["job_attempts.json"]] == ["failed"]
    open_sqlite(tmp_path / "jobs.sqlite").execute(
        "UPDATE job_attempts SET output_dir = 'shared'")                      # what --check must catch
    store.connection.execute("INSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id,"
                             " output_dir, outcome, claimed_at, lease_expires_at, renewals)"
                             " SELECT 1, 9, 'x', 'w', 'r9', 'shared', 'running', claimed_at, lease_expires_at, 0"
                             " FROM job_attempts")
    assert run(capsys, "status", *base, "--check")[0] == 1


def test_settings_hide_passwords_and_keep_the_time_relations():
    assert cli.safe_url("mysql://root:jobs-test@127.0.0.1:3307/etf_jobs") == "mysql://root:***@127.0.0.1:3307/etf_jobs"
    assert cli.timing_from(["lease=24", "renew_interval=4", "session_timeout=10"]).lease == 24.0
    with pytest.raises(SystemExit, match="fence_margin"):
        cli.timing_from(["fence_margin=3"])
    with pytest.raises(SystemExit, match="unknown setting"):
        cli.timing_from(["lease_seconds=24"])
