"""Spark results must match the Python reference regardless of row order or partitioning.

Since Spark calls the same simulate_path(), these tests mainly check grouping,
ordering, keys (no mixing of paths) and the separately written Spark summary.

AI contribution: drafted with Claude Code (Opus 5.5).
"""
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from etf_risk.model import simulate_path
from etf_risk.spark_pipeline import (
    build_spark, compare_summaries, compute_path_days, reference_summaries, summarize_paths,
)

pytestmark = pytest.mark.spark
LEVERAGES = [1.0, 2.0, 3.0]


@pytest.fixture(scope="module")
def spark():
    session = build_spark(master="local[2]", shuffle_partitions=4)
    yield session
    session.stop()


@pytest.fixture(scope="module")
def returns_pdf():
    rng = np.random.default_rng(42)
    frames = []
    for ticker, n in [("AAA", 40), ("BBB", 25), ("CCC", 60)]:
        prices = 50 * np.cumprod(1 + rng.normal(0, 0.03, n))
        r = np.concatenate([[np.nan], prices[1:] / prices[:-1] - 1])
        frames.append(pd.DataFrame({
            "ticker": ticker,
            "date": [date(2024, 1, 1) + timedelta(days=i) for i in range(n)],
            "adjusted_price": prices,
            "daily_return": r,
        }))
    return pd.concat(frames, ignore_index=True)


@pytest.mark.parametrize("partitions", [1, 3, 7])
def test_summaries_match_python_after_shuffling(spark, returns_pdf, partitions):
    shuffled = returns_pdf.sample(frac=1.0, random_state=partitions)
    returns = spark.createDataFrame(shuffled).repartition(partitions)
    summary = summarize_paths(compute_path_days(returns, LEVERAGES)).toPandas()
    problems = compare_summaries(summary, reference_summaries(returns_pdf, LEVERAGES))
    assert problems == []


def test_breached_path_matches_python(spark):
    # Day 3 is -60%: breach at 2x (1 + 2*(-0.6) < 0) but not at 1x. Needs the TODO in model.py.
    pdf = pd.DataFrame({
        "ticker": "BRK",
        "date": [date(2024, 1, 1) + timedelta(days=i) for i in range(5)],
        "adjusted_price": [10.0, 11.0, 11.5, 4.6, 4.8],
        "daily_return": [np.nan, 0.10, 0.5 / 11.0, -0.60, 0.2 / 4.6],
    })
    summary = summarize_paths(compute_path_days(spark.createDataFrame(pdf), [1.0, 2.0])).toPandas()
    assert compare_summaries(summary, reference_summaries(pdf, [1.0, 2.0])) == []
    two_x = summary.set_index("leverage").loc[2.0]
    assert bool(two_x["breached"]) and two_x["breach_day"] == 3


def test_path_days_match_python_row_by_row(spark, returns_pdf):
    returns = spark.createDataFrame(returns_pdf.sample(frac=1.0, random_state=0)).repartition(5)
    got = compute_path_days(returns, [2.0]).toPandas().sort_values(["ticker", "day"])

    for ticker, g in got.groupby("ticker"):
        src = returns_pdf[returns_pdf["ticker"] == ticker].dropna(subset=["daily_return"])
        expected = simulate_path(src["daily_return"].to_numpy(), 2.0)
        assert g["day"].tolist() == expected["day"].tolist()
        assert g["date"].tolist() == src["date"].tolist()
        for col in ["daily_return", "nav", "rebalance", "drawdown"]:
            np.testing.assert_allclose(g[col].to_numpy(), expected[col].to_numpy(), rtol=1e-9, atol=1e-9)
