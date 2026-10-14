from etf_risk.spark_pipeline import build_spark

spark = build_spark()

try:
    paired = spark.read.parquet(
        "data/outputs/windows/full-2026-10-12/"
        "rolling-252-s21-r2/run-20261013T043848Z-4/paired"
    )

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

    result.show(truncate=False)

finally:
    spark.stop()