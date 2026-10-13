"""Spark windows must match an independent Python computation, and every check must catch its failure.

Python slices each window from its own sorted returns (etf_risk.verify), so the
comparison also checks the Spark window construction.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import shutil

import numpy as np
import pandas as pd
import pytest
from conftest import nyse_sessions, write_snapshot
from pyspark.sql import functions as F

from etf_risk import spark_pipeline
from etf_risk.model import simulate_path
from etf_risk.spark_pipeline import compute, pair_paths, run_checks, total_violations, window_members, window_stats
from etf_risk.verify import TickerReturns, compare, python_summary
from etf_risk.windows import build_definitions, load_returns, write_definitions

pytestmark = pytest.mark.spark
ANCHOR = "2024-01-02"
BREACH_ROW = 30                         # row of BBB's -60% day


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    root = tmp_path_factory.mktemp("snap")
    rng = np.random.default_rng(7)
    dates = nyse_sessions(ANCHOR, 61)                          # rows 0..60
    b = rng.normal(0, 0.02, 60)
    b[BREACH_ROW - 1] = -0.60                                  # 1 + 2r < 0: a 2x breach
    snap = write_snapshot(root, "snap", {
        "AAA": (dates, rng.normal(0, 0.02, 60)),
        "BBB": (dates, b),
        "CCC": (dates[:41], rng.normal(0, 0.03, 40)),
    }, unverified=[{"ticker": "BBB", "date": str(dates[BREACH_ROW])}])
    out = write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR), root / "w")
    return {"root": root, "snap": snap, "windows": out, "dates": dates}


def load(spark, snapshot):
    defs = spark.read.parquet(str(snapshot["windows"] / "windows.parquet"))
    returns = spark.read.parquet(str(snapshot["snap"] / "daily_returns"))
    return defs, returns


@pytest.fixture(scope="module")
def result(spark, snapshot, tmp_path_factory):
    """One materialized run (tables written and read back, as the CLI does) shared by the read-only tests."""
    defs, returns = load(spark, snapshot)
    return compute(spark, defs, returns, out_dir=tmp_path_factory.mktemp("run"))


def test_all_checks_pass_with_one_row_per_leverage(spark, snapshot, result):
    defs, _ = load(spark, snapshot)
    res = result
    assert res["model_run"] and total_violations(res["checks"]) == 0, res["checks"]
    paired = res["paired"].toPandas()
    assert len(paired) == defs.count() and set(paired["n_paths"]) == {2} and set(paired["n_leverages"]) == {2}


@pytest.mark.parametrize("partitions", [1, 3, 7])
def test_results_do_not_depend_on_row_order_or_partitions(spark, snapshot, result, tmp_path, partitions):
    defs, returns = load(spark, snapshot)
    base = result["summary"].toPandas().sort_values(spark_pipeline.PATH_KEY).reset_index(drop=True)
    shuffled = returns.orderBy(F.rand(partitions)).repartition(partitions)
    other = compute(spark, defs.repartition(partitions), shuffled, out_dir=tmp_path)["summary"].toPandas()
    other = other.sort_values(spark_pipeline.PATH_KEY).reset_index(drop=True)[base.columns]
    pd.testing.assert_frame_equal(base, other, check_exact=False, rtol=1e-12)


def test_every_window_matches_independent_python_slicing(snapshot, result):
    tickers = {t: TickerReturns(f) for t, f in load_returns(snapshot["snap"]).items()}
    sample = pd.read_parquet(snapshot["windows"] / "windows.parquet")
    problems, compared = compare(sample, tickers, result["summary"].toPandas(), result["paired"].toPandas())
    assert problems == [] and compared == 2 * len(sample)


def test_breached_window_keeps_scheduled_exit_date(snapshot, result):
    res = result
    breach_date, before = snapshot["dates"][BREACH_ROW], snapshot["dates"][BREACH_ROW - 1]
    s = res["summary"].toPandas()
    two = s[(s["ticker"] == "BBB") & (s["leverage"] == 2.0) & s["breached"]]
    assert len(two) > 0
    assert (two["breach_date"] == breach_date).all()
    scheduled = pd.read_parquet(snapshot["windows"] / "windows.parquet").query("ticker == 'BBB'").set_index("entry_date")["exit_date"]
    assert all(two["exit_date"] == scheduled.loc[two["entry_date"]].to_numpy())     # scheduled, not shortened
    assert two.apply(lambda w: w["exit_date"] >= breach_date and w["first_return_date"] <= breach_date, axis=1).all()
    assert (two["final_nav"].isna() & two["total_return"].isna()).all()
    assert all(d == before for d, day in zip(two["last_ok_date"], two["breach_day"]) if day > 1)
    one = s[(s["ticker"] == "BBB") & (s["leverage"] == 1.0)]
    assert not one["breached"].any()
    p = res["paired"].toPandas()
    breached = p[p["breached_2x"]]
    assert len(breached) == len(two) and breached["exact_gap"].isna().all() and breached["log_gap"].isna().all()
    assert breached["contains_unverified_day"].all()


def test_full_period_windows_match_the_model_on_the_whole_series(spark, snapshot, tmp_path):
    out = write_definitions(*build_definitions(snapshot["snap"], "full-period"), tmp_path / "full")
    defs = spark.read.parquet(str(out / "windows.parquet"))
    res = compute(spark, defs, load(spark, snapshot)[1])
    s = res["summary"].toPandas().set_index(["ticker", "leverage"])
    for ticker, frame in load_returns(snapshot["snap"]).items():
        r = frame["daily_return"].iloc[1:].to_numpy()
        for lev in (1.0, 2.0):
            expected = python_summary(frame["date"].iloc[1:].to_numpy(), r, lev)
            assert np.isclose(s.loc[(ticker, lev), "max_drawdown"], expected["max_drawdown"], rtol=1e-12)
            if not expected["breached"]:
                path = simulate_path(r, lev)
                assert np.isclose(s.loc[(ticker, lev), "final_nav"], path["nav"].iloc[-1], rtol=1e-12)


def test_breached_windows_keep_partial_values_only_in_pre_breach_columns(result):
    p = result["paired"].toPandas()
    breached, clean = p[p["breached_2x"]], p[~p["breached_2x"]]
    assert len(breached) > 0
    for name in spark_pipeline.PAIRED_2X_PATH_VALUES:
        assert breached[name].isna().all() and clean[name].notna().all()          # full-window values only
        assert clean[f"{name}_pre_breach"].isna().all()
    assert breached["mdd_2x_pre_breach"].notna().all()
    assert (breached["days_ok_2x"] == breached["breach_day_2x"] - 1).all()


# --- failure injection --------------------------------------------------------------

def test_null_rule_catches_values_set_without_a_complete_count(result):
    summary, stats, paired = result["summary"], result["stats"], result["paired"]
    planted = summary.withColumn("final_nav", F.when(F.col("breached"), F.lit(1.0)).otherwise(F.col("final_nav")))
    assert spark_pipeline.null_rule_checks(stats, planted, paired)["path_summary.final_nav"] > 0
    leaked = paired.withColumn("mdd_2x", F.coalesce(F.col("mdd_2x"), F.col("mdd_2x_pre_breach")))
    assert spark_pipeline.null_rule_checks(stats, summary, leaked)["paired.mdd_2x"] > 0
    missing = stats.withColumn("realized_variance", F.lit(None).cast("double"))
    assert spark_pipeline.null_rule_checks(missing, summary, paired)["window_stats.realized_variance"] > 0


def test_pairing_refuses_leverages_other_than_1x_and_2x(result):
    with pytest.raises(ValueError, match="1x with 2x"):
        pair_paths(result["summary"], result["stats"], leverages=(1.0, 3.0))

def test_dropped_return_row_stops_before_the_model(spark, snapshot):
    defs, returns = load(spark, snapshot)
    gone = snapshot["dates"][20]
    res = compute(spark, defs, returns.where(~((F.col("ticker") == "AAA") & (F.col("date") == F.lit(gone)))))
    assert res["model_run"] is False
    assert sum(res["checks"]["window_construction"].values()) > 0


def test_changed_price_breaks_the_1x_identity(spark, snapshot, tmp_path):
    defs, returns = load(spark, snapshot)
    entry_row = int(pd.read_parquet(snapshot["windows"] / "windows.parquet").query("ticker == 'AAA'")["entry_row"].iloc[1])
    target = snapshot["dates"][entry_row]
    changed = returns.withColumn("adjusted_price", F.when((F.col("ticker") == "AAA") & (F.col("date") == F.lit(target)),
                                                          F.col("adjusted_price") * 1.01).otherwise(F.col("adjusted_price")))
    res = compute(spark, defs, changed, out_dir=tmp_path)
    assert res["checks"]["window_construction"] == {k: 0 for k in res["checks"]["window_construction"]}
    assert res["checks"]["one_x_identity"]["return_1x_differs_from_price_return"] > 0


def test_duplicated_leverage_row_breaks_pairing(spark, snapshot, result):
    defs, _ = load(spark, snapshot)
    res = result
    doubled = res["summary"].unionByName(res["summary"].where("ticker = 'AAA' AND leverage = 2.0").limit(1))
    paired = pair_paths(doubled, res["stats"])
    checks = run_checks(res["stats"], res["path_days"], doubled, paired, defs)
    assert checks["pairing"]["not_one_row_per_leverage"] == 1


def test_invalid_log_term_gives_null_exact_gap_not_a_partial_sum(spark, snapshot):
    defs, returns = load(spark, snapshot)
    rows = spark_pipeline.returns_with_rows(returns)
    stats = window_stats(window_members(defs, rows), defs, rows).toPandas()
    has_breach_day = stats["n_gap_terms_valid"] < stats["window_days"]
    assert has_breach_day.any()
    assert stats.loc[has_breach_day, "exact_gap"].isna().all()       # the other 9 terms are NOT summed
    assert stats.loc[~has_breach_day, "exact_gap"].notna().all()


def test_changed_input_file_stops_the_run_before_spark_starts(snapshot, tmp_path, monkeypatch):
    copy = tmp_path / "w"
    shutil.copytree(snapshot["windows"], copy)
    (copy / "windows.parquet").write_bytes((copy / "windows.parquet").read_bytes() + b" ")
    monkeypatch.setattr(spark_pipeline, "build_spark", lambda *a, **k: pytest.fail("Spark must not start"))
    assert spark_pipeline.main(["--windows", str(copy), "--out-root", str(tmp_path / "out")]) == 3
    assert not (tmp_path / "out").exists()


def test_main_writes_all_outputs(spark, snapshot, tmp_path):
    assert spark_pipeline.main(["--windows", str(snapshot["windows"]), "--out-root", str(tmp_path / "out"),
                                "--run-id", "r1"]) == 0
    run = tmp_path / "out" / "snap" / snapshot["windows"].name / "r1"
    assert {p.name for p in run.iterdir()} >= {"window_stats", "path_days", "path_summary", "paired", "checks.json", "run.json"}
    assert {p.name for p in (run / "path_days").iterdir() if p.is_dir()} == {"ticker=AAA", "ticker=BBB", "ticker=CCC"}
    record = json.loads((run / "run.json").read_text())
    assert record["status"] == "ok" and len(record["verified_sha256"]) == 5
    assert all(v is not None for v in record["spark"].values())          # effective settings, not "unset"
    assert record["spark"]["spark.sql.adaptive.enabled"] in ("true", "false")
    assert record["spark"]["jvm_max_heap_bytes"] > 0                     # measured, not assumed
    code = record["code"]
    assert code["git_worktree_clean"] in (True, False) and {"spark_pipeline.py", "windows.py"} <= set(code["source_sha256"])
    assert set(record["timings_seconds"]) >= {"session_start", "model_and_path_days", "checks", "total_in_process"}
