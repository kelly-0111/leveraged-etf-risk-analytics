"""SQL analysis 2: how often the 2x return beats twice the 1x return.

For each ticker: the windows where `return_2x > 2 * return_1x` is defined (both returns
exist), where it is not (breached windows), where it holds, and the share among the
windows where it is defined.

    uv run python analysis/sql_comparison.py <run folder>

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
        WITH comparisons AS (
            SELECT
                ticker,
                return_2x > 2 * return_1x AS is_above
            FROM paired
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
    """)

    result.show(truncate=False)

finally:
    spark.stop()
