"""The result cache's job-run path against a MySQL job table: a functional check outside the E3
batches, which use the registered run only (docs/result-cache-experiment.md, section 1). Skipped
unless ETF_RISK_MYSQL_URL is set; the end-to-end test also needs the registered run under data/.

    docker compose -f docker/compose.yaml up -d --wait mysql
    uv run --group jobs --group cache python -m etf_risk.services ready mysql
    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --group jobs --group cache \\
        python -m pytest tests/test_resolver_mysql_live.py

Each test creates and drops a database of its own (tests/jobs_backends.py).

AI contribution: written with Claude Code (Opus 5.5).
"""
import pytest

from cache_fakes import FakeRedis, FakeRedisError
from etf_risk import cache, runs, summary
from etf_risk.jobs.store import JobStore
from jobs_backends import MySQLBackend, needs_mysql
from run_fakes import PARAMS, accepted_job

pytestmark = needs_mysql


@pytest.fixture
def mysql():
    backend = MySQLBackend()
    yield backend
    backend.close()


def store_on(backend):
    store = JobStore(backend.connect(), backend.dialect)
    store.ensure_identity()
    return store


def test_an_accepted_job_on_mysql_resolves_and_resolving_only_reads(mysql, tmp_path):
    store = store_on(mysql)
    job_id, folder = accepted_job(store, tmp_path / "out")
    before = mysql.dump()
    run = runs.resolve_job(store_on(mysql), job_id, store_id=store.store_id())
    assert run.folder == folder and run.digest == runs.folder_digest(folder)
    assert run.provenance["store_id"] == store.store_id() and run.provenance["basis"] == "job"
    runs.FolderCheck(run.folder, run.digest)
    assert mysql.dump() == before


def test_unfinished_jobs_and_another_store_are_refused_on_mysql(mysql, tmp_path):
    store = store_on(mysql)
    queued = store.submit(PARAMS, {})
    running = store.submit(PARAMS, {})
    store.claim(running, "worker-a", tmp_path / "out")
    for job_id in (queued, running):
        with pytest.raises(runs.Refused, match="not succeeded"):
            runs.resolve_job(store, job_id)
    done, _ = accepted_job(store, tmp_path / "out")
    with pytest.raises(runs.Refused):
        runs.resolve_job(store, done, store_id="0" * 32)


def test_a_job_request_names_the_mysql_store(mysql, tmp_path):
    store = store_on(mysql)
    job_id, folder = accepted_job(store, tmp_path / "out")
    r = summary.Service(store=store, execute=lambda f, sql, p: {"columns": [["x", "bigint"]], "rows": [[1]]}).handle(
        {"query": "overview", "job": job_id})
    assert r["status"] == "ok" and r["run"]["basis"] == "job" and r["run"]["store_id"] == store.store_id()


@pytest.mark.spark
def test_a_job_with_the_registered_runs_files_is_answered_like_the_registered_run(mysql, tmp_path, spark):
    entries = runs.load_registry()
    registered = runs.REPO_ROOT / entries[0]["path"] if entries else None
    if registered is None or not registered.is_dir():
        pytest.skip("the registered run is not here (data/ is not in Git)")
    store = store_on(mysql)
    job_id, folder = accepted_job(store, tmp_path / "out", copy_of=registered)
    assert runs.folder_digest(folder) == entries[0]["digest"]
    redis = FakeRedis()

    def service(**kwargs):
        return summary.Service(result_cache=cache.ResultCache(redis, errors=(FakeRedisError,)),
                               execute=lambda f, sql, p: summary.run_query(spark, f, sql, p), **kwargs)
    by_registry = service().handle({"query": "sensitivity", "run": str(registered)})
    by_job = service(store=store).handle({"query": "sensitivity", "job": job_id})
    assert (by_registry["status"], by_job["status"]) == ("ok", "ok")
    assert (by_registry["source"], by_job["source"]) == ("spark", "cache")       # same digest: one entry
    assert by_job["result"] == by_registry["result"]
    assert by_job["run"]["basis"] == "job" and by_job["run"]["store_id"] == store.store_id()
    plain = summary.Service(store=store, execute=lambda f, sql, p: summary.run_query(spark, f, sql, p)).handle(
        {"query": "sensitivity", "job": job_id})
    assert plain["result"] == by_registry["result"]
