"""etf_risk.summary without Spark or Redis: resolution and refusals, the folder checks around a
query, provenance across stores, the warm and one-shot hashing, and the serve protocol. The
query runs in a stub; the cache is a stub with get_or_compute's interface, or (once the author's
steps are written) the real ResultCache over the fake Redis.

Until the author's steps 1 and 2 exist, normalize_params and identity are replaced by pass-through
stand-ins, which test summary's use of them, not their contract (tests/test_cache_contract.py).

AI contribution: written with Claude Code (Opus 5.5).
"""
import io
import json
from pathlib import Path

import pytest

from cache_fakes import FakeRedis, FakeRedisError, step
from etf_risk import cache, runs, summary
from run_fakes import accepted_job, job_table, write_run

SQL = "SELECT ticker FROM paired WHERE array_contains(:tickers, ticker)"
QUERIES = {"overview": summary.Query("analysis/sql_overview.py", {"tickers": summary.TICKER_SET}, sql=SQL)}
RESULT = {"columns": [["ticker", "string"], ["n_windows", "bigint"]], "rows": [["AAPL", 529], ["QQQ", 310]]}


@pytest.fixture
def standins(monkeypatch):
    def normalize(declared, given):
        unknown = set(given) - set(declared)
        if unknown:
            raise ValueError(f"unknown {unknown}")
        return dict(given)
    monkeypatch.setattr(cache, "normalize_params", normalize)
    monkeypatch.setattr(cache, "identity", lambda **parts: dict(parts))


class StubCache:
    """get_or_compute's interface over a dict; entries hold exactly what it was given."""

    def __init__(self):
        self.entries: dict[str, dict] = {}
        self.counters = cache.Counters()
        self.client = None

    def get_or_compute(self, ident, compute):
        key = json.dumps(ident, sort_keys=True)
        if key in self.entries:
            return self.entries[key]["result"], "cache"
        result = compute()
        self.entries[key] = {"identity": dict(ident), "result": result}
        return result, "spark"


class Executor:
    def __init__(self, result=RESULT, during=None):
        self.calls = []
        self.result, self.during = result, during

    def __call__(self, folder, sql, params):
        self.calls.append((Path(folder), sql, params))
        if self.during:
            self.during()
        return json.loads(json.dumps(self.result))


@pytest.fixture
def registered(tmp_path):
    repo = tmp_path / "repo"
    folder = write_run(repo / "data" / "outputs" / "run-4")
    registry = repo / "docs" / "accepted-runs.json"
    entry = runs.registry_entry(folder, approved_on="2026-10-25", registry=registry)
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"format": runs.REGISTRY_FORMAT, "runs": [entry]}))
    return folder, registry


def service(registry=None, **kwargs):
    kwargs.setdefault("execute", Executor())
    return summary.Service(registry=registry or "missing.json", queries=QUERIES, **kwargs)


def test_a_registered_run_is_answered_with_its_provenance(standins, registered):
    folder, registry = registered
    s = service(registry)
    r = s.handle({"id": 7, "query": "overview", "run": str(folder), "params": {"tickers": ["AAPL"]}})
    assert r["status"] == "ok" and r["id"] == 7 and r["source"] == "spark" and r["result"] == RESULT
    assert r["run"] == {"basis": "registry", "path": "data/outputs/run-4", "approved_by": "the project author",
                        "approved_on": "2026-10-25", "digest": runs.folder_digest(folder)}
    assert s.execute.calls == [(folder, SQL, {"tickers": ["AAPL"]})]
    assert set(r["seconds"]) == {"resolve", "spark", "post_check", "total"}


def test_an_unregistered_run_is_refused_without_running_the_query(standins, registered, tmp_path):
    folder, registry = registered
    s = service(registry)
    r = s.handle({"query": "overview", "run": str(write_run(tmp_path / "other"))})
    assert r["status"] == "refused" and "not in the registry" in r["reason"] and s.execute.calls == []


def test_a_job_run_is_answered_with_its_store_job_and_attempt(standins, tmp_path):
    store = job_table(tmp_path / "jobs.sqlite")
    job_id, folder = accepted_job(store, tmp_path / "out")
    r = service(store=store).handle({"query": "overview", "job": job_id})
    assert r["status"] == "ok"
    assert r["run"] == {"basis": "job", "store_id": store.store_id(), "job_id": job_id, "attempt_number": 1,
                        "run_id": folder.name, "digest": runs.folder_digest(folder)}


def test_a_hit_computed_for_another_store_reports_the_requesting_store(standins, tmp_path):
    """Revision 3: the entry holds the result's identity; the response's provenance is the
    requesting store's own resolution."""
    store_a, store_b = job_table(tmp_path / "a.sqlite"), job_table(tmp_path / "b.sqlite")
    job_a, folder_a = accepted_job(store_a, tmp_path / "out-a")
    job_b, folder_b = accepted_job(store_b, tmp_path / "out-b", copy_of=folder_a)
    shared = StubCache()                                    # one Redis, two processes
    a = service(store=store_a, result_cache=shared).handle({"query": "overview", "job": job_a})
    b = service(store=store_b, result_cache=shared).handle({"query": "overview", "job": job_b})
    assert (a["source"], b["source"]) == ("spark", "cache") and a["run"]["digest"] == b["run"]["digest"]
    assert b["run"]["store_id"] == store_b.store_id() != store_a.store_id()
    stored = json.dumps(shared.entries)
    assert store_a.store_id() not in stored and str(tmp_path) not in stored


def test_a_folder_changed_since_the_last_request_is_refused(standins, registered):
    folder, registry = registered
    s = service(registry)
    assert s.handle({"query": "overview", "run": str(folder)})["status"] == "ok"
    (folder / "extra.json").write_text("{}")
    r = s.handle({"query": "overview", "run": str(folder)})
    assert r["status"] == "refused" and len(s.execute.calls) == 1


def test_a_folder_changed_during_the_query_is_refused_and_not_cached(standins, registered):
    folder, registry = registered
    stub = StubCache()
    part = folder / "paired" / "part-00000.parquet"
    s = service(registry, result_cache=stub, execute=Executor(during=lambda: part.write_bytes(b"rewritten")))
    r = s.handle({"query": "overview", "run": str(folder)})
    assert r["status"] == "refused" and "not the accepted" in r["reason"] and stub.entries == {}


def test_a_warm_service_hashes_a_folder_once_a_one_shot_service_every_time(standins, registered):
    folder, registry = registered
    request = {"query": "overview", "run": str(folder)}
    warm = service(registry)
    assert [warm.handle(request)["full_hashes"] for _ in range(3)] == [1, 1, 1]
    assert warm.handle({**request, "verify_full": True})["full_hashes"] == 2
    assert [service(registry).handle(request)["full_hashes"] for _ in range(2)] == [1, 1]


def test_spark_is_not_started_on_a_hit(standins, registered):
    folder, registry = registered
    stub = StubCache()
    service(registry, result_cache=stub).handle({"query": "overview", "run": str(folder)})
    warm = summary.Service(registry=registry, queries=QUERIES, result_cache=stub)    # the real Spark executor
    r = warm.handle({"query": "overview", "run": str(folder)})
    assert r["source"] == "cache" and warm.spark is None


def test_without_a_cache_every_request_runs_the_query(standins, registered):
    folder, registry = registered
    s = service(registry)
    sources = [s.handle({"query": "overview", "run": str(folder)})["source"] for _ in range(2)]
    assert sources == ["spark", "spark"] and len(s.execute.calls) == 2 and s.handle(
        {"query": "overview", "run": str(folder)})["counters"] is None


@pytest.mark.parametrize("request_, reason", [
    ({"query": "nope", "run": "x"}, "no query"),
    ({"query": "overview"}, "either"),
    ({"query": "overview", "run": "x", "job": 1}, "either"),
    ({"query": "overview", "job": 1}, "job table"),
    ({"query": "overview", "run": "x", "params": {"stride": [21]}}, "unknown"),
    ({"query": "overview", "run": "x", "params": ["AAPL"]}, "JSON object"),
    ({"query": "overview", "run": 4}, "folder path"),
])
def test_requests_that_cannot_be_read_are_invalid(standins, request_, reason):
    r = service().handle(request_)
    assert r["status"] == "invalid" and reason in r["reason"]


def test_a_job_id_must_be_an_integer(standins, tmp_path):
    r = service(store=job_table(tmp_path / "jobs.sqlite")).handle({"query": "overview", "job": "1"})
    assert r["status"] == "invalid"


def test_a_query_whose_sql_is_not_moved_yet_is_not_answered(standins, registered):
    folder, registry = registered
    s = summary.Service(registry=registry, queries={"overview": summary.Query("analysis/sql_overview.py", {})})
    with pytest.raises(NotImplementedError, match="not in etf_risk.summary yet"):
        s.handle({"query": "overview", "run": str(folder)})


def test_serve_answers_every_line_and_keeps_going_after_an_error(standins, registered):
    folder, registry = registered
    failing = {"n": 0}

    def execute(folder_, sql, params):
        failing["n"] += 1
        if failing["n"] == 1:
            raise RuntimeError("Spark failed")
        return RESULT
    s = service(registry, execute=execute)
    lines = [json.dumps({"id": 1, "query": "overview", "run": str(folder)}), "", "not json", "[1]",
             json.dumps({"id": 4, "query": "overview", "run": str(folder)})]
    out = io.StringIO()
    assert summary.serve(s, lines, out) == 0
    answers = [json.loads(line) for line in out.getvalue().splitlines()]
    assert [(a["id"], a["status"]) for a in answers] == [(1, "error"), (None, "invalid"), (None, "invalid"),
                                                         (4, "ok")]
    assert "RuntimeError: Spark failed" in answers[0]["error"]


def test_the_tickers_are_the_projects():
    pytest.importorskip("matplotlib")                       # etf_risk.plots needs the plots group
    from etf_risk.plots import TICKER_ORDER
    assert summary.TICKERS == TICKER_ORDER


def test_the_queries_take_a_ticker_set_that_defaults_to_all_tickers():
    assert set(summary.QUERIES) == {"overview", "comparison", "sensitivity"}
    for query in summary.QUERIES.values():
        assert query.params == {"tickers": cache.Param("string_set", default=summary.TICKERS, allowed=summary.TICKERS)}
        assert (runs.REPO_ROOT / query.source).is_file()


def test_the_default_redis_url_is_the_services():
    from etf_risk.services import DEFAULT_REDIS_URL
    assert summary.DEFAULT_REDIS_URL == DEFAULT_REDIS_URL


@step(6)
def test_with_the_real_cache_a_cross_store_hit_stores_no_provenance(tmp_path):
    store_a, store_b = job_table(tmp_path / "a.sqlite"), job_table(tmp_path / "b.sqlite")
    job_a, folder_a = accepted_job(store_a, tmp_path / "out-a")
    job_b, _ = accepted_job(store_b, tmp_path / "out-b", copy_of=folder_a)
    redis = FakeRedis()

    def answer(store, job_id):
        rc = cache.ResultCache(redis, errors=(FakeRedisError,))
        return service(store=store, result_cache=rc).handle({"query": "overview", "job": job_id})
    a, b = answer(store_a, job_a), answer(store_b, job_b)
    assert (a["source"], b["source"]) == ("spark", "cache") and b["result"] == a["result"]
    assert b["run"]["store_id"] == store_b.store_id()
    raw = b"".join(redis.data.values())
    assert store_a.store_id().encode() not in raw and str(tmp_path).encode() not in raw
