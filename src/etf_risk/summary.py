"""Summary queries over a run's paired table, with the result cache in front (spec §11).

    uv run --group cache python -m etf_risk.summary query overview --run <run folder> [--tickers QQQ AAPL]
    uv run --group cache --group jobs python -m etf_risk.summary query overview --job 3 [--store-id <id>]
    uv run --group cache python -m etf_risk.summary serve           # JSON lines on stdin and stdout
    add --no-cache to either for Spark without Redis

One request:
1. resolve the run (etf_risk.runs): a job run whose accepted attempt recorded its run digest,
   or a historical run in the reviewed registry; anything else is refused;
2. check the folder against that digest. The first request for a folder in a process hashes
   it in full (so every one-shot request does); later ones in a warm process use the stat
   check, whose limits runs.FolderCheck states;
3. normalize the parameters and build the result's identity (etf_risk.cache);
4. get_or_compute: a hit returns the stored result. A miss runs the query in Spark, checks
   the folder again, and only then returns the result and writes it back: a folder that
   changed while Spark read it is refused and nothing is cached;
5. answer with the result and this request's own provenance.

Provenance. The response's "run" comes from step 1 of this request, never from the cache.
A cached result is identified by the run digest, so a hit may have been computed for another
run with the same files (another store's job, a registered copy); that does not change which
job, store or registry entry made this request's run servable.

Spark starts on the first miss; a hit never starts it. Timings in each response: resolve
(steps 1-3), spark (the query alone), post_check, and total.

serve reads one JSON object per line: {"id": ..., "query": "overview", "run": "<folder>"} or
{..., "job": 3, "store_id": "<optional>"}, with optional "params": {"tickers": [...]} and
"verify_full": true (hash the folder in full now). It answers one line each, with status ok,
refused (the run may not be served), invalid (the request cannot be read as written) or error
(anything else; the traceback goes to stderr and serving continues).

AI contribution: written with Claude Code (Opus 5.5), except the SQL in QUERIES, which the
project author moves here from the analysis/sql_*.py scripts (they stay unchanged). Tested
with tests/test_summary.py and tests/test_summary_spark.py.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from importlib.metadata import version
from pathlib import Path
from typing import IO, Any

from etf_risk import cache, runs
from etf_risk.cache import Param

TICKERS = ("AAPL", "MSFT", "NVDA", "TSLA", "QQQ")    # the project's tickers, in plots.TICKER_ORDER
TICKER_SET = Param(kind="string_set", default=TICKERS, allowed=TICKERS)
DEFAULT_REDIS_URL = "redis://127.0.0.1:6380/0"        # as services.DEFAULT_REDIS_URL


@dataclass(frozen=True)
class Query:
    """A named query over the view `paired` (the run's paired/ table). Its SQL takes each
    declared parameter as a named marker (:tickers, an array of strings)."""
    source: str                     # the analysis script its SQL comes from
    params: Mapping[str, Param]
    sql: str | None = None          # None until the author moves the SQL here


# STEP 7 (the author): move each query's SQL here from its source script, adding the
# :tickers marker, for example WHERE array_contains(:tickers, ticker).
QUERIES = {
    "overview": Query(
        "analysis/sql_overview.py",
        {"tickers": TICKER_SET},
        sql="""
            SELECT
                ticker,
                COUNT(*) AS n_windows,
                COUNT(return_2x) AS n_return_2x,
                SUM(CASE WHEN breached_2x THEN 1 ELSE 0 END) AS n_breached_2x,
                SUM(CASE WHEN contains_unverified_day THEN 1 ELSE 0 END) AS n_flagged,
                percentile(return_1x, 0.5) AS median_return_1x,
                percentile(return_2x, 0.5) AS median_return_2x
            FROM paired
            WHERE array_contains(:tickers, ticker)
            GROUP BY ticker
            ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
        """,
    ),
    "comparison": Query(
        "analysis/sql_comparison.py",
        {"tickers": TICKER_SET},
        sql="""
            WITH comparisons AS (
                SELECT
                    ticker,
                    return_2x > 2 * return_1x AS is_above
                FROM paired
                WHERE array_contains(:tickers, ticker)
            ),
            counts AS (
                SELECT
                    ticker,
                    COUNT(*) AS n_windows,
                    COUNT(is_above) AS n_compared,
                    SUM(CASE WHEN is_above IS NULL
                             THEN 1 ELSE 0 END) AS n_not_compared,
                    SUM(CASE WHEN is_above
                             THEN 1 ELSE 0 END) AS n_2x_above
                FROM comparisons
                GROUP BY ticker
            )
            SELECT
                ticker,
                n_windows,
                n_compared,
                n_not_compared,
                n_2x_above,
                CASE WHEN n_compared > 0
                     THEN CAST(n_2x_above AS DOUBLE) / n_compared
                     ELSE NULL
                END AS share_2x_above
            FROM counts
            ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
        """,
    ),
    "sensitivity": Query(
        "analysis/sql_sensitivity.py",
        {"tickers": TICKER_SET},
        sql="""
            SELECT
                ticker,
                COUNT(*) AS n_windows,
                COUNT(return_2x) AS n_return_2x,
                percentile(return_2x, 0.5) AS median_return_2x,

                COUNT(*) FILTER (
                    WHERE contains_unverified_day = false
                ) AS n_unflagged,

                COUNT(return_2x) FILTER (
                    WHERE contains_unverified_day = false
                ) AS n_return_2x_unflagged,

                percentile(return_2x, 0.5) FILTER (
                    WHERE contains_unverified_day = false
                ) AS median_return_2x_unflagged
            FROM paired
            WHERE array_contains(:tickers, ticker)
            GROUP BY ticker
            ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
        """,
    ),
}


class Invalid(ValueError):
    """A request that cannot be read as written."""


def engine() -> str:
    return f"pyspark {version('pyspark')}"


def run_query(spark: Any, folder: Path, sql: str, params: Mapping[str, Any]) -> dict:
    """The query on the run folder's paired/ table, as {"columns": [[name, type]], "rows": [...]}."""
    from pyspark.sql import functions as F
    spark.read.parquet(str(Path(folder) / "paired")).createOrReplaceTempView("paired")
    frame = spark.sql(sql, args={name: F.array(*[F.lit(v) for v in values]) for name, values in params.items()})
    rows = [list(row) for row in frame.collect()]
    for value in (v for row in rows for v in row):
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise TypeError(f"a result value of type {type(value).__name__}: cast it in the SQL")
    return {"columns": [[f.name, f.dataType.simpleString()] for f in frame.schema.fields], "rows": rows}


class Service:
    """Answers requests, one at a time. A warm process keeps one Service; a one-shot process
    makes one for its request. result_cache None: no Redis, every request runs the query.
    store: the job table, for requests that name a job. execute(folder, sql, params) runs a
    query; by default in a SparkSession started on first use."""

    def __init__(self, *, result_cache: cache.ResultCache | None = None, store: Any = None,
                 registry: str | Path = runs.REGISTRY, queries: Mapping[str, Query] = QUERIES,
                 execute: Callable[[Path, str, Mapping[str, Any]], dict] | None = None,
                 clock: Callable[[], float] = time.perf_counter):
        self.cache, self.store, self.registry, self.queries = result_cache, store, registry, queries
        self.execute = execute or self._spark_query
        self.clock = clock
        self.engine = engine()
        self.checks: dict[tuple[Path, str], runs.FolderCheck] = {}
        self.spark = None

    def _spark_query(self, folder: Path, sql: str, params: Mapping[str, Any]) -> dict:
        if self.spark is None:
            from etf_risk.spark_pipeline import build_spark
            self.spark = build_spark()
        return run_query(self.spark, folder, sql, params)

    def _resolve(self, request: Mapping[str, Any]) -> runs.Servable:
        if ("run" in request) == ("job" in request):
            raise Invalid('name either "run" (a folder) or "job" (a job id)')
        if "run" in request:
            if not isinstance(request["run"], str):
                raise Invalid(f"a run is a folder path, not {request['run']!r}")
            return runs.resolve_registered(request["run"], registry=self.registry)
        if self.store is None:
            raise Invalid("a job run needs the job table: --db or ETF_RISK_JOBS_DB")
        if not isinstance(request["job"], int) or isinstance(request["job"], bool):
            raise Invalid(f"a job id is an integer, not {request['job']!r}")
        return runs.resolve_job(self.store, request["job"], store_id=request.get("store_id"))

    def _checked(self, run: runs.Servable, *, full: bool) -> runs.FolderCheck:
        key = (run.folder.resolve(), run.digest)
        if key not in self.checks:
            self.checks[key] = runs.FolderCheck(run.folder, run.digest)      # a full hash
        elif full:
            self.checks[key].verify_full()
        else:
            self.checks[key].check()
        return self.checks[key]

    def handle(self, request: Mapping[str, Any]) -> dict:
        start = self.clock()
        response: dict[str, Any] = {"id": request.get("id")}
        try:
            name = request.get("query")
            if name not in self.queries:
                raise Invalid(f"no query {name!r}; the queries are {sorted(self.queries)}")
            query = self.queries[name]
            if query.sql is None:
                raise NotImplementedError(f"the SQL of {name!r} is not in etf_risk.summary yet ({query.source})")
            given = request.get("params") or {}
            if not isinstance(given, dict):
                raise Invalid(f"params is a JSON object, not {given!r}")
            try:
                params = cache.normalize_params(query.params, given)
            except ValueError as error:
                raise Invalid(str(error)) from None
            run = self._resolve(request)
            check = self._checked(run, full=bool(request.get("verify_full")))
            ident = cache.identity(run_digest=run.digest, query=name, sql=query.sql, params=params,
                                   engine=self.engine)
            resolved = self.clock()
            seconds = {"spark": 0.0, "post_check": 0.0}

            def compute() -> dict:
                began = self.clock()
                result = self.execute(run.folder, query.sql, params)
                ran = self.clock()
                check.check()                    # the files Spark read must still be the accepted ones
                seconds.update(spark=ran - began, post_check=self.clock() - ran)
                return result

            if self.cache is None:
                result, source = compute(), "spark"
            else:
                result, source = self.cache.get_or_compute(ident, compute)
            response.update(status="ok", query=name, params=params, run={**run.provenance, "digest": run.digest},
                            source=source, result=result, full_hashes=check.full_hashes,
                            counters=asdict(self.cache.counters) if self.cache is not None else None)
            seconds["resolve"] = resolved - start
        except runs.Refused as error:
            response.update(status="refused", reason=str(error))
            seconds = {}
        except Invalid as error:
            response.update(status="invalid", reason=str(error))
            seconds = {}
        response["seconds"] = {**seconds, "total": self.clock() - start}
        return response

    def close(self) -> None:
        if self.spark is not None:
            self.spark.stop()
        if self.cache is not None and hasattr(self.cache.client, "close"):
            self.cache.client.close()


def serve(service: Service, lines: Iterable[str], out: IO[str]) -> int:
    """One response line per request line, until the input ends."""
    for line in lines:
        if not line.strip():
            continue
        request: Any = None
        try:
            request = json.loads(line)
            if not isinstance(request, dict):
                raise Invalid("a request is a JSON object")
            response = service.handle(request)
        except (json.JSONDecodeError, Invalid) as error:
            response = {"id": None, "status": "invalid", "reason": str(error)}
        except Exception as error:
            traceback.print_exc(file=sys.stderr)
            response = {"id": request.get("id") if isinstance(request, dict) else None, "status": "error",
                        "error": f"{type(error).__name__}: {error}"}
        out.write(json.dumps(response) + "\n")
        out.flush()
    return 0


def open_cache(url: str, config: cache.CacheConfig = cache.CacheConfig()) -> cache.ResultCache:
    try:
        import redis
    except ImportError:
        raise SystemExit("the result cache needs redis-py: add --group cache, or pass --no-cache") from None
    from etf_risk.services import redis_client
    client = redis_client(url, connect_timeout=config.connect_timeout, read_timeout=config.read_timeout)
    return cache.ResultCache(client, errors=(redis.exceptions.RedisError,), config=config)


def open_job_table(db: str) -> Any:
    from etf_risk.jobs.cli import open_store
    from etf_risk.jobs.timing import DEFAULT_TIMING
    return open_store(db, DEFAULT_TIMING)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.summary", description=__doc__.splitlines()[0])
    parser.add_argument("--no-cache", action="store_true", help="run every query in Spark; Redis is not used")
    parser.add_argument("--redis-url", default=os.environ.get("ETF_RISK_REDIS_URL", DEFAULT_REDIS_URL))
    parser.add_argument("--db", default=os.environ.get("ETF_RISK_JOBS_DB"), help="the job table, for job runs")
    parser.add_argument("--registry", type=Path, default=runs.REGISTRY)
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("query", help="answer one request in this process")
    one.add_argument("query", choices=sorted(QUERIES))
    where = one.add_mutually_exclusive_group(required=True)
    where.add_argument("--run", help="a registered run folder")
    where.add_argument("--job", type=int, help="a job id in the job table")
    one.add_argument("--store-id", help="with --job: the job table must be this store")
    one.add_argument("--tickers", nargs="+", help="a subset of the tickers (default: all)")
    commands.add_parser("serve", help="answer JSON-line requests from stdin until it ends")
    args = parser.parse_args(argv)

    service = Service(result_cache=None if args.no_cache else open_cache(args.redis_url),
                      store=open_job_table(args.db) if args.db else None, registry=args.registry)
    try:
        if args.command == "serve":
            return serve(service, sys.stdin, sys.stdout)
        request: dict[str, Any] = {"query": args.query}
        request.update({"run": args.run} if args.run else {"job": args.job})
        if args.store_id:
            request["store_id"] = args.store_id
        if args.tickers:
            request["params"] = {"tickers": args.tickers}
        response = service.handle(request)
        print(json.dumps(response, indent=2))
        return {"ok": 0, "refused": 1, "invalid": 2}[response["status"]]
    finally:
        service.close()


if __name__ == "__main__":
    sys.exit(main())
