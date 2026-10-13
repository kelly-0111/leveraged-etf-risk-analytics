"""Shared fixtures: one local Spark session, and small synthetic snapshots on real NYSE sessions.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import pytest

from etf_risk.ingest import write_returns_parquet


def nyse_sessions(start: str, n: int) -> list[date]:
    days = mcal.get_calendar("NYSE").valid_days(start, pd.Timestamp(start) + pd.Timedelta(days=2 * n + 30))
    return [d.date() for d in days[:n]]


def write_snapshot(root: Path, name: str, series: dict[str, tuple[list[date], np.ndarray]],
                   unverified: list[dict] | None = None) -> Path:
    """series: ticker -> (dates, daily returns for rows 1..n); prices start at 100."""
    snap = root / "processed" / name
    (snap / "daily_returns").mkdir(parents=True)
    for ticker, (dates, returns) in series.items():
        prices = 100.0 * np.concatenate([[1.0], np.cumprod(1.0 + np.asarray(returns, dtype=float))])
        df = pd.DataFrame({"ticker": ticker, "date": dates, "adjusted_price": prices,
                           "daily_return": np.concatenate([[np.nan], returns])})
        write_returns_parquet(df, snap / "daily_returns" / f"{ticker}.parquet",
                              {"snapshot": name, "manifest_sha256": "test-manifest"})
    (snap / "quality_report.json").write_text(json.dumps({"unverified_extreme_days": unverified or []}))
    return snap


@pytest.fixture(scope="session")
def spark():
    from etf_risk.spark_pipeline import build_spark
    session = build_spark(master="local[2]", shuffle_partitions=4)
    yield session
    session.stop()
