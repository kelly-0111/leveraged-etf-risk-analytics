"""Run the leveraged-return model over window definitions in Spark, then summarize, pair and check.

Usage:
    uv run python -m etf_risk.spark_pipeline --windows data/windows/full-2026-10-12/rolling-252-s21
    (for timed runs, start it through etf_risk.measure, which also records peak memory)

Input:  a window-definition folder from etf_risk.windows (windows.parquet + config.json) and
        the return files of the snapshot named in its config. Every SHA-256 recorded in the
        config is verified before Spark starts; a mismatch stops the run.
Output: data/outputs/windows/<snapshot>/<definitions name>/<run id>/
          window_stats/   one row per window, from returns and prices only (no model)
          path_days/      one row per (window, leverage, day), partitioned by ticker
          path_summary/   one row per (window, leverage)
          paired/         one row per window, 1x and 2x side by side
          checks.json     violation counts of the full-scale checks
          run.json        configuration, checksums, Spark settings, timings, counts, status
          plans.json      with --record-plans: final plans and AQE shuffle-read partition counts

Options for the shuffle-partition experiment (docs/partition-experiment.md 4.1-4.2):
  --shuffle-partitions N, --coalesce on|off
          Spark settings, left at Spark's defaults when not given. Refused inside an existing
          Spark session (as in the tests), whose settings building a session would change.
  --record-plans
          plans.json (etf_risk.plans), written after the run's status is set. A capture failure
          is recorded in run.json and leaves the status and exit code unchanged.

How the work is split (docs/spec.md, sections 6 and 7):
  - window members: each definition is exploded into its rows and joined to a
    broadcast of the returns (about 39k rows).
  - model: groupBy(window key).applyInPandas sorts each window by date, checks it is
    complete, and runs model.simulate_path for every leverage on the same returns,
    so 1x and 2x always share their input.
  - summaries: Spark aggregations written separately from model.summarize_path, so
    comparing the two (etf_risk.verify) is a real check.
  - pairing: conditional aggregation on the window key, never a join on ticker only.
  - null rule: Spark's sum/avg/min/max skip nulls, so every aggregate carries the
    count of terms it used and is null unless that count is complete.

Exit codes: 0 all checks passed, 1 a check failed, 2 the run failed, 3 checksum error.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_spark_equivalence.py (including failure injection), by the
sample comparison in etf_risk.verify on the stride-21 run, and, for the
options above, with tests/test_partition_options.py.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from collections.abc import Sequence
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path

import pandas as pd
from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, IntegerType, StringType, StructField, StructType

from etf_risk import plans
from etf_risk.model import STATUS_BREACH, STATUS_OK, simulate_path
from etf_risk.provenance import code_state, resolve
from etf_risk.windows import WINDOW_KEY, ChecksumError, verify_checksums

LEVERAGES = (1.0, 2.0)            # pairing compares these two
PATH_KEY = WINDOW_KEY + ["leverage"]
INITIAL_NAV = 100.0
RTOL, ATOL = 1e-9, 1e-12          # 1x identity and turnover identity
GAP_ATOL = 1e-9                   # exact log-gap identity
BOUND_TOL = 1e-12                 # drawdown bound

PATH_DAY_SCHEMA = StructType([
    StructField("window_kind", StringType(), False),
    StructField("ticker", StringType(), False),
    StructField("window_days", IntegerType(), False),
    StructField("entry_date", DateType(), False),
    StructField("leverage", DoubleType(), False),
    StructField("day", IntegerType(), False),
    StructField("date", DateType(), False),
    StructField("daily_return", DoubleType(), False),
    StructField("nav_start", DoubleType(), True),
    StructField("nav", DoubleType(), True),
    StructField("exposure_before", DoubleType(), True),
    StructField("exposure_target", DoubleType(), True),
    StructField("rebalance", DoubleType(), True),
    StructField("running_peak", DoubleType(), True),
    StructField("drawdown", DoubleType(), True),
    StructField("status", StringType(), False),
])

PAIR_SQL = """
SELECT window_kind, ticker, window_days, entry_date,
       COUNT(*)                                                AS n_paths,
       COUNT(DISTINCT leverage)                                AS n_leverages,
       MAX(CASE WHEN leverage = 1.0 THEN total_return END)     AS return_1x,
       MAX(CASE WHEN leverage = 2.0 THEN total_return END)     AS return_2x,
       MAX(CASE WHEN leverage = 1.0 THEN max_drawdown END)     AS mdd_1x,
       MAX(CASE WHEN leverage = 2.0 THEN max_drawdown END)     AS _mdd_2x,
       BOOL_OR(CASE WHEN leverage = 1.0 THEN breached END)     AS breached_1x,
       BOOL_OR(CASE WHEN leverage = 2.0 THEN breached END)     AS breached_2x,
       MAX(CASE WHEN leverage = 2.0 THEN breach_date END)      AS breach_date_2x,
       MAX(CASE WHEN leverage = 2.0 THEN breach_day END)       AS breach_day_2x,
       MAX(CASE WHEN leverage = 2.0 THEN last_ok_date END)     AS last_ok_date_2x,
       MAX(CASE WHEN leverage = 2.0 THEN days_ok END)          AS days_ok_2x,
       MAX(CASE WHEN leverage = 2.0 THEN mean_turnover END)    AS _mean_turnover_2x,
       MAX(CASE WHEN leverage = 2.0 THEN max_turnover END)     AS _max_turnover_2x,
       MAX(CASE WHEN leverage = 2.0 THEN total_turnover END)   AS _total_turnover_2x,
       MAX(CASE WHEN leverage = 2.0 THEN n_turnover_days END)  AS n_turnover_days_2x
FROM path_summary
GROUP BY window_kind, ticker, window_days, entry_date
"""


def build_spark(master: str = "local[*]", shuffle_partitions: int | None = None,
                coalesce: bool | None = None) -> SparkSession:
    """None leaves a setting at Spark's default. On an existing session, getOrCreate() applies these
    settings to it, which is why main() refuses the partition flags inside one."""
    # Without this, Spark binds to the Wi-Fi interface on macOS.
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    builder = (
        SparkSession.builder.master(master)
        .appName("etf-risk")
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
    )
    if shuffle_partitions is not None:
        builder = builder.config("spark.sql.shuffle.partitions", str(shuffle_partitions))
    if coalesce is not None:
        builder = builder.config("spark.sql.adaptive.coalescePartitions.enabled", "true" if coalesce else "false")
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


# --- building blocks -------------------------------------------------------------

def returns_with_rows(returns: DataFrame) -> DataFrame:
    """Add `row` per ticker (0 = first price), the index used by the window definitions."""
    return returns.withColumn("row", (F.row_number().over(Window.partitionBy("ticker").orderBy("date")) - 1).cast("int"))


def window_members(defs: DataFrame, returns: DataFrame) -> DataFrame:
    rows = defs.select(*WINDOW_KEY, F.explode(F.sequence(F.col("entry_row") + 1, F.col("entry_row") + F.col("window_days"))).alias("row"))
    return rows.join(F.broadcast(returns.select("ticker", "row", "date", "daily_return")), ["ticker", "row"], "inner")


def window_stats(members: DataFrame, defs: DataFrame, returns: DataFrame) -> DataFrame:
    """Per window, from returns and prices only. Count-guarded: null unless every term was valid."""
    r = F.col("daily_return")
    valid_r = r.isNotNull() & ~F.isnan(r)
    gap_term_ok = valid_r & (1 + 2 * r > 0)         # then (r/(1+r))^2 < 1, so the log is defined
    agg = members.groupBy(*WINDOW_KEY).agg(
        F.count(F.lit(1)).alias("n_member_rows"),
        F.countDistinct("date").alias("n_member_dates"),
        F.min("date").alias("min_date"),
        F.max("date").alias("max_date"),
        F.sum(valid_r.cast("int")).alias("n_valid_returns"),
        F.sum(F.when(valid_r, r * r)).alias("_sum_sq"),
        F.sum(F.when(valid_r, F.abs(r))).alias("_sum_abs"),
        F.max(F.when(valid_r, F.abs(r))).alias("_max_abs"),
        F.sum(gap_term_ok.cast("int")).alias("n_gap_terms_valid"),
        F.sum(F.when(gap_term_ok, F.log1p(-F.pow(r / (1 + r), 2)))).alias("_exact_gap"),
    )
    complete = F.col("n_valid_returns") == F.col("window_days")
    agg = agg.select(
        *WINDOW_KEY, "n_member_rows", "n_member_dates", "min_date", "max_date", "n_valid_returns", "n_gap_terms_valid",
        F.when(complete, F.col("_sum_sq")).alias("realized_variance"),
        F.when(complete, F.col("_sum_abs")).alias("sum_abs_return"),
        F.when(complete, F.col("_max_abs")).alias("max_abs_return"),
        F.when(F.col("n_gap_terms_valid") == F.col("window_days"), F.col("_exact_gap")).alias("exact_gap"),
    )
    prices = returns.select("ticker", "row", "date", "adjusted_price")
    entry = prices.select("ticker", F.col("row").alias("entry_row"), F.col("date").alias("entry_price_date"),
                          F.col("adjusted_price").alias("entry_price"))
    exit_ = prices.select("ticker", F.col("row").alias("exit_row"), F.col("date").alias("exit_price_date"),
                          F.col("adjusted_price").alias("exit_price"))
    d = (defs.select(*WINDOW_KEY, "entry_row", "first_return_date", "exit_date", "contains_unverified_day",
                     "unverified_day_count", "entry_on_unverified_day")
         .withColumn("exit_row", F.col("entry_row") + F.col("window_days")))
    d = d.join(F.broadcast(entry), ["ticker", "entry_row"], "left").join(F.broadcast(exit_), ["ticker", "exit_row"], "left")
    return d.join(agg, WINDOW_KEY, "left").withColumn("price_return", F.col("exit_price") / F.col("entry_price") - 1.0)


def simulate_windows(members: DataFrame, leverages: Sequence[float] = LEVERAGES, initial_nav: float = INITIAL_NAV) -> DataFrame:
    names = PATH_DAY_SCHEMA.fieldNames()
    levs = [float(x) for x in leverages]

    def run(pdf: pd.DataFrame) -> pd.DataFrame:
        pdf = pdf.sort_values("date", kind="mergesort")
        key = {k: pdf[k].iloc[0] for k in WINDOW_KEY}
        if len(pdf) != int(key["window_days"]) or pdf["date"].duplicated().any():
            raise ValueError(f"incomplete window {key}: {len(pdf)} rows for {key['window_days']} days")
        dates, returns = pdf["date"].to_numpy(), pdf["daily_return"].to_numpy()
        out = []
        for lev in levs:
            path = simulate_path(returns, lev, initial_nav)
            for k, v in key.items():
                path[k] = v
            path["leverage"] = lev
            path["date"] = dates[path["day"].to_numpy() - 1]
            out.append(path)
        return pd.concat(out, ignore_index=True)[names]

    return members.groupBy(*WINDOW_KEY).applyInPandas(run, schema=PATH_DAY_SCHEMA)


def _valid(cond, col):
    """The value where `cond` holds and it is a real number (not null, not NaN)."""
    return F.when(cond & col.isNotNull() & ~F.isnan(col), col)


def summarize_paths(path_days: DataFrame, defs: DataFrame, initial_nav: float = INITIAL_NAV) -> DataFrame:
    ok, breach = F.col("status") == STATUS_OK, F.col("status") == STATUS_BREACH
    turnover = F.abs(F.col("rebalance")) / F.col("nav_start")       # fraction of that day's starting NAV
    g = path_days.groupBy(*PATH_KEY).agg(
        F.count(F.lit(1)).alias("n_rows"),
        F.countDistinct("day").alias("n_distinct_days"),
        F.max("day").alias("max_day"),
        F.sum(ok.cast("int")).alias("days_ok"),
        F.bool_or(breach).alias("breached"),
        F.sum(breach.cast("int")).alias("n_breach_rows"),
        F.min(F.when(breach, F.col("day"))).alias("breach_day"),
        F.min(F.when(breach, F.col("date"))).alias("breach_date"),
        F.max(F.when(ok, F.col("date"))).alias("last_ok_date"),
        F.max_by(_valid(ok, F.col("nav")), F.when(ok, F.col("day"))).alias("_last_ok_nav"),
        F.count(_valid(ok, F.col("nav"))).alias("n_valid_nav"),
        F.max(_valid(ok, F.col("drawdown"))).alias("_max_drawdown"),
        F.count(_valid(ok, F.col("drawdown"))).alias("n_valid_drawdown"),
        F.avg(_valid(ok, turnover)).alias("_mean_turnover"),
        F.max(_valid(ok, turnover)).alias("_max_turnover"),
        F.sum(_valid(ok, turnover)).alias("_total_turnover"),
        # ties: the earliest date with the maximum turnover
        F.max_by(F.col("date"), F.struct(_valid(ok, turnover), -F.unix_date(F.col("date")))).alias("_max_turnover_date"),
        F.count(_valid(ok, turnover)).alias("n_turnover_days"),
        F.sum(_valid(ok, F.abs(F.col("rebalance")))).alias("_total_abs_rebalance"),
        F.max(_valid(ok, F.abs(F.col("rebalance")))).alias("_max_abs_rebalance"),
        F.count(_valid(ok, F.abs(F.col("rebalance")))).alias("n_valid_rebalance"),
    )
    s = g.select(
        *PATH_KEY, "n_rows", "n_distinct_days", "max_day", "days_ok", "breached", "n_breach_rows",
        "breach_day", "breach_date", "last_ok_date", "n_valid_nav", "n_valid_drawdown", "n_turnover_days",
        "n_valid_rebalance",
        F.when(_final_nav_complete(), F.col("_last_ok_nav")).alias("final_nav"),
        # the starting NAV is a peak candidate, so a path with no ok day has drawdown 0 (as summarize_path)
        F.when(_drawdown_complete(), F.coalesce(F.col("_max_drawdown"), F.lit(0.0))).alias("max_drawdown"),
        F.when(_turnover_complete(), F.col("_mean_turnover")).alias("mean_turnover"),
        F.when(_turnover_complete(), F.col("_max_turnover")).alias("max_turnover"),
        F.when(_turnover_complete(), F.col("_total_turnover")).alias("total_turnover"),
        F.when(_turnover_complete() & (F.col("_max_turnover") > 0), F.col("_max_turnover_date")).alias("max_turnover_date"),
        F.when(_rebalance_complete(), F.coalesce(F.col("_total_abs_rebalance"), F.lit(0.0))).alias("total_abs_rebalance"),
        F.when(_rebalance_complete(), F.coalesce(F.col("_max_abs_rebalance"), F.lit(0.0))).alias("max_abs_rebalance"),
    ).withColumn("total_return", F.col("final_nav") / F.lit(initial_nav) - 1.0)
    scheduled = defs.select(*WINDOW_KEY, "first_return_date", "exit_date", "stride", "calendar_year",
                            "contains_unverified_day", "unverified_day_count", "entry_on_unverified_day")
    return s.join(scheduled, WINDOW_KEY, "left")


# Completeness rules for count-guarded path values; summarize_paths applies them and check 10 tests them.
def _final_nav_complete():
    return ~F.col("breached") & (F.col("n_valid_nav") == F.col("days_ok")) & (F.col("days_ok") == F.col("window_days"))


def _drawdown_complete():
    return F.col("n_valid_drawdown") == F.col("days_ok")


def _turnover_complete():
    return (F.col("n_turnover_days") == F.col("days_ok")) & (F.col("days_ok") > 0)


def _rebalance_complete():
    return F.col("n_valid_rebalance") == F.col("days_ok")


PAIRED_2X_PATH_VALUES = ["mdd_2x", "mean_turnover_2x", "max_turnover_2x", "total_turnover_2x"]


def pair_paths(summary: DataFrame, stats: DataFrame, leverages: Sequence[float] = LEVERAGES) -> DataFrame:
    """One row per window, 1x and 2x side by side. For a breached 2x path the drawdown and turnover cover only
    the days before the breach: they go to *_pre_breach columns and the full-window columns are null."""
    if tuple(float(x) for x in leverages) != (1.0, 2.0):
        raise ValueError(f"pairing compares 1x with 2x; got leverages {tuple(leverages)}")
    spark = summary.sparkSession
    summary.createOrReplaceTempView("path_summary")
    paired = spark.sql(PAIR_SQL)
    s = stats.select(*WINDOW_KEY, "first_return_date", "exit_date", "contains_unverified_day", "unverified_day_count",
                     "entry_on_unverified_day", "realized_variance", "sum_abs_return", "max_abs_return", "price_return",
                     F.col("exact_gap").alias("_exact_gap"))
    p = paired.join(s, WINDOW_KEY, "left")
    breached, not_breached = F.col("breached_2x"), ~F.col("breached_2x")
    for name in PAIRED_2X_PATH_VALUES:
        p = p.withColumn(name, F.when(not_breached, F.col(f"_{name}"))) \
             .withColumn(f"{name}_pre_breach", F.when(breached, F.col(f"_{name}"))).drop(f"_{name}")
    return (
        p.withColumn("exact_gap", F.when(not_breached, F.col("_exact_gap"))).drop("_exact_gap")
        .withColumn("log_gap", F.when(not_breached & F.col("return_1x").isNotNull() & F.col("return_2x").isNotNull(),
                                      F.log1p("return_2x") - 2 * F.log1p("return_1x")))
        .withColumn("approx_gap", -F.col("realized_variance"))
        .withColumn("approx_rel_error", F.when(F.col("exact_gap").isNotNull() & F.col("realized_variance").isNotNull()
                                               & (F.abs("exact_gap") > 0),
                                               (F.col("approx_gap") - F.col("exact_gap")) / F.abs("exact_gap")))
        .withColumn("mdd_bound", F.when(not_breached & F.col("mdd_1x").isNotNull(), 1 - F.pow(1 - F.col("mdd_1x"), 2)))
    )


# --- checks ----------------------------------------------------------------------

def _violations(df: DataFrame, checks: dict[str, object]) -> dict[str, int]:
    """Count rows matching each violation condition, in one Spark job."""
    row = df.agg(*[F.sum(F.when(cond, 1).otherwise(0)).alias(name) for name, cond in checks.items()]).first()
    return {name: int(row[name] or 0) for name in checks}


def construction_checks(stats: DataFrame) -> dict[str, int]:
    wd = F.col("window_days")
    return _violations(stats, {
        "member_rows_not_window_days": F.col("n_member_rows").isNull() | (F.col("n_member_rows") != wd)
                                       | (F.col("n_member_dates") != wd),
        "first_or_last_date_mismatch": ~F.col("min_date").eqNullSafe(F.col("first_return_date"))
                                       | ~F.col("max_date").eqNullSafe(F.col("exit_date")),
        "entry_or_exit_price_date_mismatch": ~F.col("entry_price_date").eqNullSafe(F.col("entry_date"))
                                             | ~F.col("exit_price_date").eqNullSafe(F.col("exit_date")),
        "missing_entry_or_exit_price": F.col("entry_price").isNull() | F.col("exit_price").isNull(),
    })


def run_checks(stats: DataFrame, path_days: DataFrame, summary: DataFrame, paired: DataFrame, defs: DataFrame,
               leverages: Sequence[float] = LEVERAGES) -> dict[str, dict]:
    n_lev = len(leverages)
    breached = F.col("breached")
    results = {"window_construction": construction_checks(stats)}
    results["complete_paths"] = _violations(summary, {
        "rows_not_window_days_or_breach_day": (~breached & (F.col("n_rows") != F.col("window_days")))
                                              | (breached & ~F.col("n_rows").eqNullSafe(F.col("breach_day"))),
        "days_not_numbered_1_to_rows": (F.col("max_day") != F.col("n_rows")) | (F.col("n_distinct_days") != F.col("n_rows")),
        "days_ok_inconsistent": F.col("days_ok") != F.col("n_rows") - F.when(breached, 1).otherwise(0),
        "more_than_one_breach_row": F.col("n_breach_rows") > 1,
    })
    missing = defs.select(*WINDOW_KEY).join(paired.select(*WINDOW_KEY), WINDOW_KEY, "left_anti").count()
    extra = paired.select(*WINDOW_KEY).join(defs.select(*WINDOW_KEY), WINDOW_KEY, "left_anti").count()
    results["pairing"] = {
        **_violations(paired, {"not_one_row_per_leverage": (F.col("n_paths") != n_lev) | (F.col("n_leverages") != n_lev)}),
        "definitions_without_paired_row": missing,
        "paired_rows_without_definition": extra,
    }
    not_breached_2x = ~F.col("breached_2x")
    results["one_x_identity"] = _violations(paired, {
        "return_1x_differs_from_price_return": F.col("return_1x").isNull() | F.col("price_return").isNull()
        | (F.abs(F.col("return_1x") - F.col("price_return")) > ATOL + RTOL * F.abs(F.col("price_return"))),
    })
    results["exact_log_gap"] = _violations(paired, {
        "log_gap_differs_from_exact_gap": not_breached_2x & (F.col("log_gap").isNull() | F.col("exact_gap").isNull()
                                                             | (F.abs(F.col("log_gap") - F.col("exact_gap")) > GAP_ATOL)),
    })
    results["drawdown_bound"] = _violations(paired, {
        "mdd_2x_below_bound": not_breached_2x & (F.col("mdd_2x").isNull() | F.col("mdd_bound").isNull()
                                                 | (F.col("mdd_2x") < F.col("mdd_bound") - BOUND_TOL)),
    })
    nav, ok = F.col("nav"), F.col("status") == STATUS_OK
    expected_turnover = F.col("leverage") * (F.col("leverage") - 1) * F.abs(F.col("daily_return"))
    turnover = F.abs(F.col("rebalance")) / F.col("nav_start")
    results["nav_sanity"] = _violations(path_days, {
        "negative_nav": nav < 0,
        "nan_nav_outside_breach_rows": F.isnan(nav) & (F.col("status") != STATUS_BREACH),
        "ok_row_without_valid_nav": ok & (nav.isNull() | F.isnan(nav)),
    })
    results["turnover_identity"] = _violations(path_days, {
        "turnover_differs_from_L(L-1)|r|": ok & (turnover.isNull() | F.isnan(turnover)
                                               | (F.abs(turnover - expected_turnover) > ATOL + RTOL * expected_turnover)),
        "nonzero_turnover_at_1x": ok & (F.col("leverage") == 1.0) & (F.abs(F.col("rebalance")) != 0),
    })
    results["breach_flagged_unverified"] = _violations(paired, {
        "breached_window_not_flagged": F.col("breached_2x") & ~F.col("contains_unverified_day"),
    })
    results["null_rule"] = null_rule_checks(stats, summary, paired)
    return results


def _null_iff(column: str, should_be_null) -> object:
    """Violation: the column is null when it should be set, or set when it should be null (both directions)."""
    return F.col(column).isNull() != F.coalesce(should_be_null, F.lit(True))


def null_rule_checks(stats: DataFrame, summary: DataFrame, paired: DataFrame) -> dict[str, int]:
    """Check 10: every count-guarded value is null exactly when its count of valid terms is short."""
    returns_short = F.col("n_valid_returns") != F.col("window_days")
    gap_short = F.col("n_gap_terms_valid") != F.col("window_days")
    breached = F.col("breached_2x")
    return {
        **_violations(stats, {
            "window_stats.realized_variance": _null_iff("realized_variance", returns_short),
            "window_stats.sum_abs_return": _null_iff("sum_abs_return", returns_short),
            "window_stats.max_abs_return": _null_iff("max_abs_return", returns_short),
            "window_stats.exact_gap": _null_iff("exact_gap", gap_short),
        }),
        **_violations(summary, {
            "path_summary.final_nav": _null_iff("final_nav", ~_final_nav_complete()),
            "path_summary.total_return": _null_iff("total_return", ~_final_nav_complete()),
            "path_summary.max_drawdown": _null_iff("max_drawdown", ~_drawdown_complete()),
            "path_summary.mean_turnover": _null_iff("mean_turnover", ~_turnover_complete()),
            "path_summary.max_turnover": _null_iff("max_turnover", ~_turnover_complete()),
            "path_summary.total_turnover": _null_iff("total_turnover", ~_turnover_complete()),
            "path_summary.max_turnover_date": _null_iff("max_turnover_date",
                                                        ~(_turnover_complete() & (F.col("max_turnover") > 0))),
            "path_summary.total_abs_rebalance": _null_iff("total_abs_rebalance", ~_rebalance_complete()),
            "path_summary.max_abs_rebalance": _null_iff("max_abs_rebalance", ~_rebalance_complete()),
        }),
        **_violations(paired, {
            # in a 2x window without a breach every gap term is valid, so these are set exactly when not breached
            "paired.exact_gap": _null_iff("exact_gap", breached),
            "paired.log_gap": _null_iff("log_gap", breached),
            "paired.return_2x": _null_iff("return_2x", breached),
            "paired.mdd_bound": _null_iff("mdd_bound", breached),
            "paired.approx_rel_error": _null_iff("approx_rel_error", breached | (F.abs(F.col("exact_gap")) == 0)),
            "paired.mdd_2x": _null_iff("mdd_2x", breached),
            "paired.mdd_2x_pre_breach": _null_iff("mdd_2x_pre_breach", ~breached),
            **{f"paired.{name}": _null_iff(name, breached) for name in PAIRED_2X_PATH_VALUES[1:]},
            # no pre-breach turnover exists when the breach is on day 1 (no day before it)
            **{f"paired.{name}_pre_breach": _null_iff(f"{name}_pre_breach", ~breached | (F.col("days_ok_2x") == 0))
               for name in PAIRED_2X_PATH_VALUES[1:]},
        }),
    }


def total_violations(checks: dict[str, dict]) -> int:
    return sum(v for group in checks.values() for v in group.values())


# --- whole run -------------------------------------------------------------------

def compute(spark: SparkSession, defs: DataFrame, returns: DataFrame, leverages: Sequence[float] = LEVERAGES,
            initial_nav: float = INITIAL_NAV, out_dir: Path | None = None, timings: dict | None = None) -> dict:
    """Run everything. With out_dir, each table is written and read back, so the model runs once."""
    timings = {} if timings is None else timings

    def materialize(df: DataFrame, name: str, partition_by: str | None = None) -> DataFrame:
        if out_dir is None:
            return df
        writer = df.write.mode("error")
        if partition_by:
            writer = writer.partitionBy(partition_by)
        writer.parquet(str(out_dir / name))
        return spark.read.parquet(str(out_dir / name))

    def phase(name: str):
        spark.sparkContext.setJobGroup(name, name)
        return time.perf_counter()

    t = phase("window_stats")
    returns = returns_with_rows(returns)
    members = window_members(defs, returns)
    stats = materialize(window_stats(members, defs, returns), "window_stats")
    construction = construction_checks(stats)
    timings["window_stats_and_construction_check"] = time.perf_counter() - t
    if sum(construction.values()):
        return {"checks": {"window_construction": construction}, "model_run": False, "stats": stats}

    t = phase("model")
    path_days = materialize(simulate_windows(members, leverages, initial_nav), "path_days", partition_by="ticker")
    timings["model_and_path_days"] = time.perf_counter() - t

    t = phase("summaries")
    summary = materialize(summarize_paths(path_days, defs, initial_nav), "path_summary")
    paired = materialize(pair_paths(summary, stats, leverages), "paired")
    timings["summaries_and_pairing"] = time.perf_counter() - t

    t = phase("checks")
    checks = run_checks(stats, path_days, summary, paired, defs, leverages)
    timings["checks"] = time.perf_counter() - t
    return {"checks": checks, "model_run": True, "stats": stats, "path_days": path_days, "summary": summary, "paired": paired}


def stage_task_counts(spark: SparkSession, groups: Sequence[str]) -> dict:
    tracker = spark.sparkContext.statusTracker()
    out = {}
    for group in groups:
        jobs = tracker.getJobIdsForGroup(group)
        stages = [s for j in jobs if (info := tracker.getJobInfo(j)) for s in info.stageIds]
        tasks = [si.numTasks for s in stages if (si := tracker.getStageInfo(s))]
        out[group] = {"jobs": len(jobs), "stages": len(stages), "tasks": sum(tasks)}
    return out


def spark_settings(spark: SparkSession) -> dict:
    """Effective values. spark.conf.get(key) without a default returns Spark's default for unset SQL
    settings; passing a default instead would return that default whenever the key was never set."""
    sql_keys = ["spark.sql.shuffle.partitions", "spark.sql.adaptive.enabled",
                "spark.sql.adaptive.coalescePartitions.enabled", "spark.sql.adaptive.advisoryPartitionSizeInBytes",
                "spark.sql.autoBroadcastJoinThreshold"]
    settings = {k: spark.conf.get(k) for k in sql_keys}
    conf = spark.sparkContext.getConf()
    settings["spark.master"] = conf.get("spark.master")
    settings["spark.driver.memory"] = conf.get("spark.driver.memory", "not set (Spark default 1g)")
    settings["default_parallelism"] = spark.sparkContext.defaultParallelism
    settings["spark_version"] = spark.version
    try:      # the heap the driver JVM actually got, rather than the configured or default value
        settings["jvm_max_heap_bytes"] = int(spark.sparkContext._jvm.java.lang.Runtime.getRuntime().maxMemory())
    except Exception:
        settings["jvm_max_heap_bytes"] = None
    return settings


def environment() -> dict:
    env = {
        "platform": platform.platform(), "macos": platform.mac_ver()[0] or None, "machine": platform.machine(),
        "cpu_count": os.cpu_count(), "python": platform.python_version(),
        "packages": {p: _version(p) for p in ("pyspark", "pandas", "numpy", "pyarrow", "pandas_market_calendars", "psutil")},
    }
    try:
        java = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
        env["java"] = (java.stderr or java.stdout).splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        env["java"] = "unknown"
    try:
        import psutil
        env["ram_total_bytes"] = psutil.virtual_memory().total
    except ImportError:
        env["ram_total_bytes"] = None
    return env


def _version(package: str) -> str | None:
    try:
        return package_version(package)
    except Exception:
        return None


def run_dir_for(windows_dir: Path, out_root: Path, run_id: str) -> Path:
    config = json.loads((windows_dir / "config.json").read_text())
    return out_root / config["snapshot"] / windows_dir.name / run_id


def positive_int(text: str) -> int:
    value = int(text)
    if value < 1:
        raise argparse.ArgumentTypeError(f"must be at least 1, got {value}")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--windows", type=Path, required=True, help="window-definition folder from etf_risk.windows")
    parser.add_argument("--out-root", type=Path, default=Path("data/outputs/windows"))
    parser.add_argument("--run-id", default=None, help="default: run-<UTC time>")
    parser.add_argument("--initial-nav", type=float, default=INITIAL_NAV)
    parser.add_argument("--master", default="local[*]")
    parser.add_argument("--shuffle-partitions", type=positive_int, default=None,
                        help="spark.sql.shuffle.partitions (default: Spark's, 200); needs a fresh process")
    parser.add_argument("--coalesce", choices=["on", "off"], default=None,
                        help="spark.sql.adaptive.coalescePartitions.enabled (default: Spark's, on); needs a fresh process")
    parser.add_argument("--record-plans", action="store_true",
                        help="write plans.json: the final plan of every SQL execution of the run and the partition "
                             "counts of AQE's shuffle reads (docs/partition-experiment.md 4.2)")
    return parser


PLAN_GROUPS = ("window_stats", "model", "summaries", "checks", "bookkeeping")


def record_plans(spark: SparkSession, after_id: int | None, start_error: str | None, run_dir: Path,
                 timings: dict) -> dict:
    """Write plans.json and return the run.json summary of the capture. Never raises: a failure is
    recorded here and leaves the run's status and exit code unchanged (docs/partition-experiment.md 3.4)."""
    t = time.perf_counter()
    path = run_dir / "plans.json"
    try:
        if start_error is not None:
            raise plans.PlanCaptureError(f"no watermark at the start of the run: {start_error}")
        doc = plans.capture(spark, after_id, PLAN_GROUPS)
        path.write_text(json.dumps(doc, indent=2) + "\n")
        result = {"status": "ok", "file": path.name, "executions": len(doc["executions"]),
                  "first_execution_id": doc["first_execution_id"]}
    except Exception as exc:
        path.unlink(missing_ok=True)
        result = {"status": "failed", "error": "".join(traceback.format_exception_only(type(exc), exc)).strip()[-2000:]}
    timings["plan_capture"] = timings.get("plan_capture", 0.0) + time.perf_counter() - t
    return result


def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    args = build_parser().parse_args(argv)
    sets_spark = args.shuffle_partitions is not None or args.coalesce is not None
    if sets_spark and SparkSession.getActiveSession() is not None:
        print("--shuffle-partitions and --coalesce need a fresh process: a Spark session already exists here, "
              "and building one would change its settings", file=sys.stderr)
        return 2
    run_id = args.run_id or "run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        config, verified = verify_checksums(args.windows)
    except (ChecksumError, FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"checksum verification failed, Spark not started:\n{exc}", file=sys.stderr)
        return 3
    run_dir = run_dir_for(args.windows, args.out_root, run_id)
    if run_dir.exists():
        print(f"{run_dir} exists; use a new --run-id", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True)
    record = {
        "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "code": code_state(), "windows_dir": str(args.windows),
        "windows_config": config, "verified_sha256": verified, "leverages": list(LEVERAGES),
        "initial_nav": args.initial_nav, "environment": environment(), "status": "running",
    }
    if sets_spark or args.record_plans:          # without the new flags, run.json is as before
        record["pipeline_options"] = {"shuffle_partitions": args.shuffle_partitions, "coalesce": args.coalesce,
                                      "record_plans": args.record_plans}
    timings: dict[str, float] = {}
    status, code = "failed", 2
    spark = None
    own_session = SparkSession.getActiveSession() is None      # only stop a session started here
    plan_after, plan_start_error = None, None
    try:
        t = time.perf_counter()
        spark = build_spark(args.master, args.shuffle_partitions,
                            None if args.coalesce is None else args.coalesce == "on")
        timings["session_start"] = time.perf_counter() - t
        record["spark"] = spark_settings(spark)
        if args.record_plans:                    # the executions after this id are this run's
            t = time.perf_counter()
            try:
                plan_after = plans.watermark(spark)
            except Exception as exc:
                plan_start_error = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-500:]
            timings["plan_capture"] = time.perf_counter() - t
        defs = spark.read.parquet(str(args.windows / config["windows_file"]))
        return_files = [str(resolve(config["snapshot_dir"]) / rel) for rel in config["inputs_sha256"] if rel.startswith("daily_returns/")]
        returns = spark.read.parquet(*return_files)
        results = compute(spark, defs, returns, LEVERAGES, args.initial_nav, out_dir=run_dir, timings=timings)
        checks = results["checks"]
        (run_dir / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
        record["checks"] = checks
        record["model_run"] = results["model_run"]
        spark.sparkContext.setJobGroup("bookkeeping", "row counts for run.json")   # not part of any timed phase
        record["row_counts"] = {"windows": defs.count(), "window_stats": results["stats"].count()}
        if results["model_run"]:
            record["row_counts"].update({name: results[name].count() for name in ("path_days", "summary", "paired")})
        record["stage_task_counts"] = stage_task_counts(spark, ["window_stats", "model", "summaries", "checks"])
        status, code = ("ok", 0) if total_violations(checks) == 0 else ("checks_failed", 1)
        if args.record_plans:                    # after the status is set, which it cannot change
            record["plan_capture"] = record_plans(spark, plan_after, plan_start_error, run_dir, timings)
    except Exception as exc:
        record["error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-4000:]
    finally:
        timings["total_in_process"] = time.perf_counter() - started
        record.update({"status": status, "timings_seconds": timings, "finished_at_utc": datetime.now(timezone.utc).isoformat()})
        (run_dir / "run.json").write_text(json.dumps(record, indent=2, default=str) + "\n")
        if spark is not None and own_session:
            spark.stop()
    print(f"{run_id}: {status}  ({record.get('row_counts', {})})  -> {run_dir}")
    for group, violations in record.get("checks", {}).items():
        bad = {k: v for k, v in violations.items() if v}
        print(f"  {group}: {'ok' if not bad else bad}")
    if "error" in record:
        print("  error:", record["error"].splitlines()[-1], file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
