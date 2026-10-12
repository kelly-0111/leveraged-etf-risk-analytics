"""Quality checks for raw daily price data and computed daily returns.

Checks return a report instead of raising, so every problem is listed at once.
`errors` block the pipeline; `warnings` are recorded but do not block it.
Nothing is silently dropped or filled. Results and remaining limitations of
the downloaded data are recorded in docs/data-sources.md.

AI contribution: drafted with Claude Code (Opus 5.5). Verified with
tests/test_validation.py and by running on the 2020-2025 and full-history
Yahoo snapshots.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal

PRICE_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close"]

# The NYSE schedule is the reference calendar, also for the Nasdaq-listed
# tickers; docs/data-sources.md records how well it matched.
REFERENCE_CALENDAR = "NYSE"

# Adj Close / Close should change only on ex-dividend days, by
# -log(1 - dividend / previous close). Tolerances are in log units.
DIVIDEND_STEP_TOLERANCE = 1e-5
UNEXPLAINED_STEP_THRESHOLD = 1e-6

# A split-day return this close to the unadjusted move (1/ratio - 1, e.g.
# -50% for 2:1) means the price series was probably not split-adjusted.
SPLIT_UNADJUSTED_MARGIN = 0.05

# A move this large in one day is possible but rare for these tickers; it is
# also what an unadjusted split would look like (4:1 split -> -75%).
SUSPICIOUS_ABS_RETURN = 0.5

# Days that need a second data source before results depending on them are
# treated as findings rather than as possible data errors.
EXTREME_ABS_RETURN = 0.20
REVERSAL_ABS_RETURN = 0.15       # a move larger than this ...
REVERSAL_NEXT_ABS_RETURN = 0.13  # ... reversed by an opposite move larger than this
SPLIT_DAY_ABS_RETURN = 0.10


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

    zero_volume = _day_strings(df.loc[df["Volume"] == 0, "date"])
    if zero_volume:
        warnings.append(f"{len(zero_volume)} zero-volume rows (price may be carried over, not traded): {zero_volume}")
    flat = flat_bars(df)
    if flat:
        warnings.append(f"{len(flat)} rows with Open = High = Low = Close (no intraday range; the close is still used): {flat}")

    calendar = check_trading_calendar(df["date"]) if len(df) else {}
    if calendar.get("missing_rows"):
        errors.append(f"{len(calendar['missing_rows'])} {REFERENCE_CALENDAR} sessions have no data row: {calendar['missing_rows']}")
    if calendar.get("extra_rows"):
        errors.append(f"{len(calendar['extra_rows'])} data rows fall on non-session days: {calendar['extra_rows']}")

    # Needs usable prices (it takes logs); a calendar error does not prevent it.
    dividends = check_dividend_adjustment(df) if not (missing or nonfinite or nonpositive) else {}
    if dividends.get("mismatched_ex_dividend_days"):
        warnings.append(
            f"{len(dividends['mismatched_ex_dividend_days'])} ex-dividend days where the Adj Close adjustment differs "
            f"from the reported dividend by more than {DIVIDEND_STEP_TOLERANCE:g}: {dividends['mismatched_ex_dividend_days']}"
        )
    unresolved = dividends.get("unresolved_adjustment_steps", {})
    if unresolved.get("count"):
        warnings.append(
            f"{unresolved['count']} unexplained Adj Close / Close steps on non-ex-dividend days "
            f"(max {unresolved['max_abs_log_step']:.1e} in log units); cause not determined"
        )

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
            "zero_volume_rows": zero_volume,
            "flat_bars": flat,
            "trading_calendar": calendar,
            "dividend_adjustment": dividends,
        },
    }


def validate_returns(returns: pd.DataFrame, splits: dict[str, float]) -> dict:
    """Check computed daily returns (output of ingest.compute_daily_returns).

    splits: split date (YYYY-MM-DD) -> ratio as reported by Yahoo (2.0 for 2:1).
    """
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
        warnings.append(f"|return| > {SUSPICIOUS_ABS_RETURN:.0%} on {big}; unverified (no second source yet)")

    # If the price series were not split-adjusted, split days would show the split ratio.
    by_date = returns.assign(date=returns["date"].astype(str)).set_index("date")["daily_return"]
    split_day_returns = {d: float(by_date[d]) for d in splits if d in by_date.index}
    unadjusted = [
        d for d, ret in split_day_returns.items()
        if abs(ret - (1.0 / splits[d] - 1.0)) < SPLIT_UNADJUSTED_MARGIN
    ]
    if unadjusted:
        errors.append(f"split-day returns match an unadjusted split on {unadjusted}")

    extreme = unverified_extreme_days(returns, splits)

    return {
        "errors": errors,
        "warnings": warnings,
        "checks": {
            "return_rows": int(rest.notna().sum()),
            "min_return": float(rest.min()),
            "max_return": float(rest.max()),
            "split_day_returns": split_day_returns,
            "zero_return_share": float((rest == 0.0).mean()),
        },
        "unverified_extreme_days": extreme,
    }


def check_trading_calendar(dates: pd.Series) -> dict:
    """Compare data dates with the reference exchange schedule.

    Only the span between this ticker's first and last data date is checked.
    A session without a data row is a missing row; a weekday without a session
    is a market closure (a regular holiday or a special closure), not an error.
    """
    d = pd.DatetimeIndex(pd.to_datetime(dates)).normalize().unique().sort_values()
    first, last = d[0], d[-1]
    calendar = mcal.get_calendar(REFERENCE_CALENDAR)
    sessions = _naive(calendar.valid_days(first, last))
    regular = set(_naive(calendar.regular_holidays.holidays(first, last)))
    closures = pd.bdate_range(first, last).difference(sessions)
    special = [c for c in closures if c not in regular]
    return {
        "reference": REFERENCE_CALENDAR,
        "first_date": str(first.date()),
        "last_date": str(last.date()),
        "sessions": len(sessions),
        "data_dates": len(d),
        "missing_rows": _day_strings(sessions.difference(d)),
        "extra_rows": _day_strings(d.difference(sessions)),
        "weekday_closures": len(closures),
        "regular_holiday_closures": len(closures) - len(special),
        "special_closures": _day_strings(special),
    }


def check_dividend_adjustment(df: pd.DataFrame) -> dict:
    """Compare each Adj Close / Close step with the reported dividend."""
    p = df.sort_values("date", kind="mergesort").reset_index(drop=True)
    step = np.log(p["Adj Close"] / p["Close"]).diff()
    expected = -np.log1p(-p["Dividends"] / p["Close"].shift(1))
    ex_dividend = p["Dividends"] != 0
    mismatch = (step - expected).abs()
    bad = ex_dividend & (mismatch > DIVIDEND_STEP_TOLERANCE)
    unexplained = ~ex_dividend & (step.abs() > UNEXPLAINED_STEP_THRESHOLD)
    return {
        "ex_dividend_days": int(ex_dividend.sum()),
        "max_ex_dividend_mismatch": float(mismatch[ex_dividend].max()) if ex_dividend.any() else 0.0,
        "mismatched_ex_dividend_days": _day_strings(p.loc[bad, "date"]),
        "unresolved_adjustment_steps": {
            "count": int(unexplained.sum()),
            "max_abs_log_step": float(step[unexplained].abs().max()) if unexplained.any() else 0.0,
            "dates": _day_strings(p.loc[unexplained, "date"]),
        },
    }


def flat_bars(df: pd.DataFrame) -> list[str]:
    flat = df[["Open", "High", "Low"]].eq(df["Close"], axis=0).all(axis=1)
    return _day_strings(df.loc[flat, "date"])


def unverified_extreme_days(returns: pd.DataFrame, splits: dict[str, float]) -> list[dict]:
    """Days to confirm with a second source before treating results that use them as findings."""
    r = returns["daily_return"]
    nxt, prev = r.shift(-1), r.shift(1)
    dates = returns["date"].astype(str)
    reasons: dict[int, list[str]] = {}

    def flag(mask: pd.Series, reason: str) -> None:
        for i in returns.index[mask.fillna(False).to_numpy(dtype=bool)]:
            reasons.setdefault(i, []).append(reason)

    flag(r.abs() >= EXTREME_ABS_RETURN, f"|return| >= {EXTREME_ABS_RETURN:.0%}")
    reversal = (r.abs() > REVERSAL_ABS_RETURN) & (nxt.abs() > REVERSAL_NEXT_ABS_RETURN) & (np.sign(nxt) == -np.sign(r))
    flag(reversal, "reversed by the next day")
    flag(reversal.shift(1, fill_value=False) & prev.notna(), "reverses the previous day")
    flag(dates.isin(list(splits)) & (r.abs() >= SPLIT_DAY_ABS_RETURN), f"split day with |return| >= {SPLIT_DAY_ABS_RETURN:.0%}")
    return [
        {"date": dates[i], "daily_return": float(r[i]), "reasons": reasons[i], "second_source": "not checked"}
        for i in sorted(reasons)
    ]


def _naive(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    index = pd.DatetimeIndex(index)
    return (index.tz_convert(None) if index.tz is not None else index).normalize()


def _day_strings(values) -> list[str]:
    return [str(pd.Timestamp(v).date()) for v in values]
