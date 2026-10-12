"""PySpark batch version: run the reference model once per path, summarize with Spark.

Usage:
    uv run python -m etf_risk.spark_pipeline --leverages 1 2

Input:  data/processed/<snapshot>/daily_returns/*.parquet (from etf_risk.ingest)
Output: data/outputs/historical_full/path_days/     one row per (path, day)
        data/outputs/historical_full/path_summary/  one row per path
        stdout: Spark SQL comparison and a Python-vs-Spark consistency check

A path is currently (ticker, leverage) over the full period of the input (by
default the 2020-2025 prototype snapshot). Fixed 252-trading-day holding
windows are planned for Stage 2: docs/spec.md, sections 7 and 10.

How the work is split:
  - per-path model: groupBy(path keys).applyInPandas -> model.simulate_path,
    so Spark and the Python reference use the same rules. Each group is sorted
    by date inside the function; input row order is never relied on.
  - path summaries: Spark aggregations written separately from
    model.summarize_path, so comparing the two is a real check.

AI contribution: drafted with Claude Code (Opus 5.5). Verified with
tests/test_spark_equivalence.py (shuffled/repartitioned input) and the --check
comparison on the NVDA/AAPL/MSFT/TSLA data.
"""
from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DateType, DoubleType, IntegerType, StringType, StructField, StructType

from etf_risk.model import STATUS_BREACH, STATUS_OK, simulate_path, summarize_path

PATH_KEYS = ["ticker", "leverage"]

PATH_DAY_SCHEMA = StructType([
    StructField("ticker", StringType(), False),
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

SUMMARY_METRICS = [
    "days_ok", "breached", "breach_day", "final_nav", "total_return",
    "max_drawdown", "total_abs_rebalance", "max_abs_rebalance",
]


def build_spark(master: str = "local[*]", shuffle_partitions: int | None = None) -> SparkSession:
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
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def _simulate_group(pdf: pd.DataFrame, initial_nav: float) -> pd.DataFrame:
    if pdf["date"].duplicated().any():
        raise ValueError(f"duplicate dates in path {pdf[PATH_KEYS].iloc[0].tolist()}: paths are mixed")
    pdf = pdf.sort_values("date", kind="mergesort").reset_index(drop=True)
    leverage = float(pdf["leverage"].iloc[0])
    path = simulate_path(pdf["daily_return"].to_numpy(), leverage, initial_nav)
    path.insert(0, "ticker", pdf["ticker"].iloc[0])
    path.insert(1, "leverage", leverage)
    path["date"] = pdf["date"].to_numpy()[path["day"].to_numpy() - 1]
    return path[PATH_DAY_SCHEMA.fieldNames()]


def compute_path_days(returns: DataFrame, leverages: Sequence[float], initial_nav: float = 100.0) -> DataFrame:
    """returns: (ticker, date, daily_return, ...) with the first-row nulls still present."""
    spark = returns.sparkSession
    lev = spark.createDataFrame([(float(x),) for x in leverages], "leverage double")
    inputs = (
        returns.where(F.col("daily_return").isNotNull())
        .select("ticker", "date", "daily_return")
        .crossJoin(lev)
    )

    # A closure, not functools.partial: applyInPandas reads the function's
    # signature to decide whether to also pass the group key.
    def run(pdf: pd.DataFrame) -> pd.DataFrame:
        return _simulate_group(pdf, initial_nav)

    return inputs.groupBy(*PATH_KEYS).applyInPandas(run, schema=PATH_DAY_SCHEMA)


def summarize_paths(path_days: DataFrame, initial_nav: float = 100.0) -> DataFrame:
    ok = F.col("status") == STATUS_OK
    breach = F.col("status") == STATUS_BREACH
    # Restrict metrics to ok rows explicitly: Spark's max() treats NaN as larger
    # than every number, unlike pandas, which skips NaN.
    ok_only = lambda c: F.when(ok, c)  # noqa: E731
    return (
        path_days.groupBy(*PATH_KEYS)
        .agg(
            F.min("date").alias("start_date"),
            F.max("date").alias("end_date"),
            F.sum(ok.cast("int")).alias("days_ok"),
            F.bool_or(breach).alias("breached"),
            F.min(F.when(breach, F.col("day"))).alias("breach_day"),
            F.max_by(ok_only(F.col("nav")), ok_only(F.col("day"))).alias("last_ok_nav"),
            F.coalesce(F.max(ok_only(F.col("drawdown"))), F.lit(0.0)).alias("max_drawdown"),
            F.coalesce(F.sum(ok_only(F.abs("rebalance"))), F.lit(0.0)).alias("total_abs_rebalance"),
            F.coalesce(F.max(ok_only(F.abs("rebalance"))), F.lit(0.0)).alias("max_abs_rebalance"),
        )
        .withColumn("final_nav", F.when(~F.col("breached"), F.col("last_ok_nav")))
        .withColumn("total_return", F.col("final_nav") / F.lit(initial_nav) - 1.0)
        .drop("last_ok_nav")
    )


COMPARISON_SQL = """
SELECT s.ticker,
       s.leverage,
       s.start_date,
       s.end_date,
       s.days_ok,
       s.breached,
       ROUND(s.total_return, 4)                          AS total_return,
       ROUND(s.leverage * b.total_return, 4)             AS leverage_x_1x_return,
       ROUND(s.max_drawdown, 4)                          AS max_drawdown,
       ROUND(s.total_abs_rebalance / {initial_nav}, 2)   AS abs_rebalance_x_initial_nav
FROM path_summary s
LEFT JOIN path_summary b
       ON s.ticker = b.ticker AND b.leverage = 1.0
ORDER BY s.ticker, s.leverage
"""


def reference_summaries(returns_pdf: pd.DataFrame, leverages: Sequence[float], initial_nav: float = 100.0) -> pd.DataFrame:
    """Python-only path summaries for the same inputs (for consistency checks)."""
    rows = []
    for ticker, g in returns_pdf.dropna(subset=["daily_return"]).groupby("ticker"):
        r = g.sort_values("date")["daily_return"].to_numpy()
        for lev in leverages:
            s = summarize_path(simulate_path(r, float(lev), initial_nav), initial_nav)
            rows.append({"ticker": ticker, "leverage": float(lev), **s})
    return pd.DataFrame(rows)


def compare_summaries(spark_pdf: pd.DataFrame, python_pdf: pd.DataFrame, rtol: float = 1e-9, atol: float = 1e-9) -> list[str]:
    """Return a list of mismatches (empty = consistent). NaN and null count as equal."""
    a = spark_pdf.set_index(PATH_KEYS).sort_index()
    b = python_pdf.set_index(PATH_KEYS).sort_index()
    if not a.index.equals(b.index):
        return [f"path keys differ: spark={a.index.tolist()} python={b.index.tolist()}"]
    problems = []
    for col in SUMMARY_METRICS:
        x = pd.to_numeric(a[col], errors="coerce").to_numpy(dtype=float)
        y = pd.to_numeric(b[col], errors="coerce").to_numpy(dtype=float)
        bad = ~np.isclose(x, y, rtol=rtol, atol=atol, equal_nan=True)
        for key in a.index[bad]:
            problems.append(f"{key} {col}: spark={a.at[key, col]} python={b.at[key, col]}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--returns", type=Path, default=Path("data/processed/yahoo/daily_returns"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/outputs/historical_full"))
    parser.add_argument("--leverages", type=float, nargs="+", default=[1.0, 2.0])
    parser.add_argument("--initial-nav", type=float, default=100.0)
    parser.add_argument("--no-check", action="store_true", help="skip the Python-vs-Spark comparison")
    args = parser.parse_args(argv)
    if 1.0 not in args.leverages:
        parser.error("--leverages must include 1 (the comparison query uses it as the baseline)")

    spark = build_spark()
    returns = spark.read.parquet(str(args.returns))
    path_days = compute_path_days(returns, args.leverages, args.initial_nav)
    path_days.write.mode("overwrite").parquet(str(args.out_dir / "path_days"))

    # Summaries read the written output back, so the model runs once.
    path_days = spark.read.parquet(str(args.out_dir / "path_days"))
    summary = summarize_paths(path_days, args.initial_nav)
    summary.write.mode("overwrite").parquet(str(args.out_dir / "path_summary"))

    spark.read.parquet(str(args.out_dir / "path_summary")).createOrReplaceTempView("path_summary")
    spark.sql(COMPARISON_SQL.format(initial_nav=args.initial_nav)).show(truncate=False)

    status = 0
    if not args.no_check:
        # Small here (one row per path); do not collect path_days at scale.
        spark_pdf = spark.table("path_summary").toPandas()
        python_pdf = reference_summaries(returns.toPandas(), args.leverages, args.initial_nav)
        problems = compare_summaries(spark_pdf, python_pdf)
        print(f"Python vs Spark summaries: {len(spark_pdf)} paths, "
              f"{'consistent' if not problems else f'{len(problems)} MISMATCHES'} (rtol=atol=1e-9)")
        for p in problems:
            print("  ", p)
        status = 1 if problems else 0

    spark.stop()
    return status


if __name__ == "__main__":
    sys.exit(main())
