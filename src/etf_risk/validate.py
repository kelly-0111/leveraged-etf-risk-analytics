"""Quality checks for raw daily price data and computed daily returns.

Checks return a report instead of raising, so every problem is listed at once.
`errors` block the pipeline; `warnings` are recorded but do not block it.
Nothing is silently dropped or filled (docs/implementation-plan.md §4.1).

AI contribution: drafted with Claude Code (Opus 5.5). Verified with
tests/test_validation.py and by running on the 2020-2025 Yahoo snapshot.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close"]

# Weekends plus a one-day holiday give at most 4 calendar days between trading
# days (e.g. Thu 2021-12-23 -> Mon 2021-12-27). Longer gaps may mean missing
# records. This is not a full exchange-calendar check.
MAX_EXPECTED_GAP_DAYS = 4

# A move this large in one day is possible but rare for these tickers; it is
# also what an unadjusted split would look like (4:1 split -> -75%).
SUSPICIOUS_ABS_RETURN = 0.5


def validate_prices(df: pd.DataFrame) -> dict:
    """Check one ticker's raw prices (columns from ingest.load_raw_csv)."""
    errors: list[str] = []
    warnings: list[str] = []

    if len(df) < 2:
        errors.append(f"need at least 2 rows to compute a return, got {len(df)}")

    dup = int(df.duplicated(["ticker", "date"]).sum())
    if dup:
        errors.append(f"{dup} duplicate (ticker, date) rows")

    if not df["date"].is_monotonic_increasing:
        warnings.append("rows are not in increasing date order in the source; sorted before computing returns")

    prices = df[PRICE_COLUMNS].to_numpy(dtype=float)
    missing = int(np.isnan(prices).sum())
    nonfinite = int((~np.isfinite(prices)).sum()) - missing
    nonpositive = int((prices <= 0).sum())
    if missing:
        errors.append(f"{missing} missing price cells")
    if nonfinite:
        errors.append(f"{nonfinite} infinite price cells")
    if nonpositive:
        errors.append(f"{nonpositive} non-positive price cells")

    negative_volume = int((df["Volume"] < 0).sum())
    if negative_volume:
        errors.append(f"{negative_volume} rows with negative volume")

    gaps = _long_gaps(df["date"])
    if gaps:
        warnings.append(f"{len(gaps)} gaps longer than {MAX_EXPECTED_GAP_DAYS} calendar days: {gaps[:5]}")

    return {
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "rows": len(df),
            "duplicate_dates": dup,
            "missing_price_cells": missing,
            "nonfinite_price_cells": nonfinite,
            "nonpositive_price_cells": nonpositive,
            "negative_volume_rows": negative_volume,
            "long_gaps": len(gaps),
            "exchange_calendar_checked": False,
        },
    }


def validate_returns(returns: pd.DataFrame, split_dates: list[str]) -> dict:
    """Check computed daily returns (output of ingest.compute_daily_returns)."""
    errors: list[str] = []
    warnings: list[str] = []
    r = returns["daily_return"]

    first_is_null = bool(pd.isna(r.iloc[0]))
    if not first_is_null:
        errors.append("first row must have a null return (no previous price)")
    rest = r.iloc[1:]
    if rest.isna().any() or not np.isfinite(rest.to_numpy()).all():
        errors.append("missing or non-finite return after the first row")
    if (rest < -1.0).any():
        errors.append("return below -100%")

    big = returns.loc[r.abs() > SUSPICIOUS_ABS_RETURN, "date"].astype(str).tolist()
    if big:
        warnings.append(f"|return| > {SUSPICIOUS_ABS_RETURN:.0%} on {big}; check corporate-action adjustment")

    # If the price series were not split-adjusted, split days would show huge drops.
    by_date = returns.assign(date=returns["date"].astype(str)).set_index("date")["daily_return"]
    split_day_returns = {d: float(by_date[d]) for d in split_dates if d in by_date.index}

    return {
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "return_rows": int(rest.notna().sum()),
            "min_return": float(rest.min()),
            "max_return": float(rest.max()),
            "split_day_returns": split_day_returns,
        },
    }


def _long_gaps(dates: pd.Series) -> list[str]:
    d = pd.to_datetime(dates).sort_values().reset_index(drop=True)
    gap_days = d.diff().dt.days
    idx = gap_days[gap_days > MAX_EXPECTED_GAP_DAYS].index
    return [f"{d[i - 1].date()}->{d[i].date()}" for i in idx]
