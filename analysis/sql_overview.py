"""SQL analysis 1: a per-ticker overview of a run's paired table.

For each ticker: the number of windows, of 2x breaches and of windows that use an
unverified extreme day, and exact medians of the 1x and 2x returns (a breached window
has no 2x return). Also prints the table's schema, a few rows and the query's plan.

    uv run python analysis/sql_overview.py <run folder>

The run folder is one written by etf_risk.spark_pipeline (its paired/ table is read);
the paired/ folder itself also works.

The query was written by the project author; the command-line input was added with
Claude Code (Opus 5.5).
"""
import argparse
from pathlib import Path

from etf_risk.spark_pipeline import build_spark

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("run", type=Path, help="run folder from etf_risk.spark_pipeline, or its paired/ folder")
args = parser.parse_args()
paired_dir = args.run / "paired" if (args.run / "paired").is_dir() else args.run
if not any(paired_dir.glob("*.parquet")):
    parser.error(f"no paired table (Parquet files) in {paired_dir}")

spark = build_spark()

try:
    paired = spark.read.parquet(str(paired_dir))

    paired.printSchema()
    paired.select(
        "ticker",
        "breached_2x",
        "contains_unverified_day",
        "return_1x",
        "return_2x",
    ).show(5)

    paired.createOrReplaceTempView("paired")

    result = spark.sql("""
        SELECT
            ticker,
            COUNT(*) AS n_windows,
            COUNT(return_2x) AS n_return_2x,
            SUM(CASE WHEN breached_2x THEN 1 ELSE 0 END) AS n_breached_2x,
            SUM(CASE WHEN contains_unverified_day THEN 1 ELSE 0 END) AS n_flagged,
            percentile(return_1x, 0.5) AS median_return_1x,
            percentile(return_2x, 0.5) AS median_return_2x
        FROM paired
        GROUP BY ticker
        ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
    """)

    result.explain("formatted")
    result.show(truncate=False)

finally:
    spark.stop()
