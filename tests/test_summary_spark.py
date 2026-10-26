"""etf_risk.summary in Spark: the :tickers marker bound as an array, the result's columns and value
types, and (step 7, once the author's SQL is in QUERIES) the spec §8 values on the registered run
of record, which is skipped without data/.

AI contribution: written with Claude Code (Opus 5.5).
"""
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from cache_fakes import step
from etf_risk import runs, summary

pytestmark = pytest.mark.spark


@pytest.fixture
def paired_run(tmp_path):
    folder = tmp_path / "run"
    (folder / "paired").mkdir(parents=True)
    table = pa.table({"ticker": ["AAPL", "AAPL", "MSFT", "QQQ", "QQQ", "QQQ"],
                      "return_1x": [0.1, 0.2, 0.3, 0.05, -0.1, 0.0],
                      "return_2x": [0.2, None, 0.7, 0.1, -0.2, 0.0],
                      "breached_2x": [False, True, False, False, False, False],
                      "contains_unverified_day": [False, True, False, False, False, False]})
    pq.write_table(table, folder / "paired" / "part-00000.parquet")
    return folder


SQL = """SELECT ticker, COUNT(*) AS n_windows, COUNT(return_2x) AS n_return_2x, percentile(return_1x, 0.5) AS median_1x
         FROM paired WHERE array_contains(:tickers, ticker) GROUP BY ticker ORDER BY ticker"""


def test_the_tickers_marker_selects_the_subset(spark, paired_run):
    result = summary.run_query(spark, paired_run, SQL, {"tickers": ["QQQ", "AAPL"]})
    assert result["columns"] == [["ticker", "string"], ["n_windows", "bigint"], ["n_return_2x", "bigint"],
                                 ["median_1x", "double"]]
    assert result["rows"] == [["AAPL", 2, 1, 0.15000000000000002], ["QQQ", 3, 3, 0.0]]
    assert [type(v) for v in result["rows"][0]] == [str, int, int, float]


def test_a_value_json_cannot_hold_is_refused(spark, paired_run):
    with pytest.raises(TypeError, match="Decimal"):
        summary.run_query(spark, paired_run, "SELECT CAST(1.5 AS DECIMAL(4, 2)) AS d FROM paired LIMIT 1",
                          {"tickers": ["AAPL"]})


def registered_run() -> Path:
    entries = runs.load_registry()
    if not entries:
        pytest.skip("no registered run")
    folder = runs.REPO_ROOT / entries[0]["path"]
    if not folder.is_dir():
        pytest.skip(f"{entries[0]['path']} is not here (data/ is not in Git)")
    return folder


def answer(spark, query, **params):
    service = summary.Service(execute=lambda folder, sql, p: summary.run_query(spark, folder, sql, p))
    response = service.handle({"query": query, "run": str(registered_run()), "params": params})
    assert response["status"] == "ok", response
    names = [c[0] for c in response["result"]["columns"]]
    return {row[0]: dict(zip(names, row)) for row in response["result"]["rows"]}


def percent(value) -> float:
    return round(100 * value, 1)


@step(7)
def test_the_queries_reproduce_spec_8_on_the_registered_run(spark):
    pytest.importorskip("matplotlib")                       # etf_risk.plots holds the documented values
    from etf_risk.plots import DOCUMENTED as D
    overview, comparison, sensitivity = (answer(spark, q) for q in ("overview", "comparison", "sensitivity"))
    assert list(overview) == list(summary.TICKERS)          # AAPL, MSFT, NVDA, TSLA, then QQQ
    for t in summary.TICKERS:
        o, c, s = overview[t], comparison[t], sensitivity[t]
        assert o["n_windows"] == D["windows"][t]
        assert o["n_flagged"] == D["windows_with_an_unverified_day"][t]
        assert o["n_breached_2x"] == (D["breaches"]["windows"] if t in D["breaches"]["tickers"] else 0)
        assert percent(o["median_return_1x"]) == D["median_return_1x_percent"][t]
        assert (percent(o["median_return_2x"]), o["n_return_2x"]) == D["median_return_2x_percent"][t]
        assert (c["n_2x_above"], c["n_compared"]) == D["above_twice_1x"][t]
        assert (percent(s["median_return_2x_unflagged"]), s["n_unflagged"]) == D["median_return_2x_unflagged_percent"][t]


@step(7)
def test_a_ticker_subset_gives_the_same_rows_as_the_full_query(spark):
    full, subset = answer(spark, "overview"), answer(spark, "overview", tickers=["QQQ", "TSLA"])
    assert list(subset) == ["TSLA", "QQQ"] and subset == {t: full[t] for t in ("TSLA", "QQQ")}
