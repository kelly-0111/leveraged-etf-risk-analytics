"""SQL analysis 3: 2x return medians with and without flagged windows.

For each ticker: the count and exact median of the 2x return over all windows, and over
the windows without an unverified extreme day. Leaving the flagged windows out is a
sensitivity analysis: it shows how much a median depends on those periods, not whether
those days are data errors.

    uv run python analysis/sql_sensitivity.py <run folder>

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
    paired.createOrReplaceTempView("paired")
    result = spark.sql("""
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
        GROUP BY ticker
        ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
    """)



    result.show(truncate=False)

finally:
    spark.stop()
