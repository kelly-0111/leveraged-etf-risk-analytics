from etf_risk.spark_pipeline import build_spark

spark = build_spark()

try:
    paired = spark.read.parquet(
        "data/outputs/windows/full-2026-10-12/"
        "rolling-252-s21-r2/run-20261013T043848Z-4/paired"
    )
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