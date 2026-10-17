from etf_risk.spark_pipeline import build_spark

spark = build_spark()

try:
    paired = spark.read.parquet(
        "data/outputs/windows/full-2026-10-12/"
        "rolling-252-s21-r2/run-20261013T043848Z-4/paired"
    )
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