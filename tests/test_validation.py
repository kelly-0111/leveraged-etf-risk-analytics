"""Bad inputs must be reported, not silently fixed.

AI contribution: drafted with Claude Code (Opus 5.5).
"""
from datetime import date

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import pytest

from etf_risk.ingest import compute_daily_returns, load_raw_csv
from etf_risk.validate import check_dividend_adjustment, validate_prices, validate_returns

HEADER = "Date,Open,High,Low,Close,Adj Close,Volume,Dividends,Stock Splits\n"


def sessions(n, start="2024-01-02"):
    """The first n NYSE sessions from start (so the calendar check passes)."""
    days = mcal.get_calendar("NYSE").valid_days(start, pd.Timestamp(start) + pd.Timedelta(days=3 * n + 10))
    return [d.date() for d in days[:n]]


def raw_frame(adj_close, dates=None, close=None, dividends=0.0, volume=100):
    n = len(adj_close)
    return pd.DataFrame({
        "ticker": "TEST", "date": dates or sessions(n),
        "Open": 1.0, "High": 1.0, "Low": 1.0,
        "Close": adj_close if close is None else close, "Adj Close": adj_close,
        "Volume": volume, "Dividends": dividends, "Stock Splits": 0.0,
    })


def test_clean_data_passes():
    report = validate_prices(raw_frame([10.0, 11.0, 12.0]))
    assert report["errors"] == [] and report["warnings"] == []


@pytest.mark.parametrize("bad, expected", [
    ([10.0, np.nan, 12.0], "missing"),
    ([10.0, np.inf, 12.0], "infinite"),
    ([10.0, 0.0, 12.0], "non-positive"),
    ([10.0, -1.0, 12.0], "non-positive"),
])
def test_bad_prices_are_errors(bad, expected):
    errors = validate_prices(raw_frame(bad))["errors"]
    assert any(expected in e for e in errors), errors


def test_duplicate_dates_are_errors():
    df = raw_frame([10.0, 11.0, 12.0], dates=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 3)])
    assert any("duplicate" in e for e in validate_prices(df)["errors"])


# --- trading calendar ----------------------------------------------------------

def test_missing_session_is_an_error_with_its_date():
    # Thu 2024-01-04 was a normal NYSE session
    df = raw_frame([10.0, 11.0, 12.0], dates=[date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 5)])
    report = validate_prices(df)
    assert report["checks"]["trading_calendar"]["missing_rows"] == ["2024-01-04"]
    assert any("no data row" in e and "2024-01-04" in e for e in report["errors"])


def test_row_on_a_non_session_day_is_an_error():
    df = raw_frame([10.0, 11.0, 12.0], dates=[date(2024, 1, 5), date(2024, 1, 6), date(2024, 1, 8)])  # Sat 01-06
    report = validate_prices(df)
    assert report["checks"]["trading_calendar"]["extra_rows"] == ["2024-01-06"]
    assert any("non-session" in e and "2024-01-06" in e for e in report["errors"])


@pytest.mark.parametrize("dates, regular, special", [
    ([date(2024, 7, 3), date(2024, 7, 5)], 1, []),                                    # Independence Day
    ([date(2012, 10, 26), date(2012, 10, 31)], 0, ["2012-10-29", "2012-10-30"]),     # Hurricane Sandy
    ([date(2001, 9, 10), date(2001, 9, 17)], 0, ["2001-09-11", "2001-09-12", "2001-09-13", "2001-09-14"]),
])
def test_market_closures_are_not_errors(dates, regular, special):
    report = validate_prices(raw_frame([10.0, 11.0], dates=dates))
    calendar = report["checks"]["trading_calendar"]
    assert report["errors"] == []
    assert calendar["missing_rows"] == [] and calendar["extra_rows"] == []
    assert calendar["regular_holiday_closures"] == regular
    assert calendar["special_closures"] == special


def test_calendar_checks_only_the_tickers_own_span():
    # Data starts on 2024-01-04: the 01-02 and 01-03 sessions before it are not missing rows
    df = raw_frame([10.0, 11.0], dates=[date(2024, 1, 4), date(2024, 1, 5)])
    calendar = validate_prices(df)["checks"]["trading_calendar"]
    assert calendar["first_date"] == "2024-01-04" and calendar["missing_rows"] == []


# --- dividend adjustment ---------------------------------------------------------

def dividend_frame(factor):
    # Dividend 1.0 goes ex on the third day; Adj Close before it is Close * factor
    close = [100.0, 101.0, 99.0, 100.0]
    adj = [close[0] * factor, close[1] * factor, close[2], close[3]]
    return raw_frame(adj, close=close, dividends=[0.0, 0.0, 1.0, 0.0])


def test_dividend_adjustment_matching_the_reported_dividend_passes():
    report = validate_prices(dividend_frame(1 - 1.0 / 101.0))   # 1 - dividend / previous close
    dividends = report["checks"]["dividend_adjustment"]
    assert dividends["ex_dividend_days"] == 1 and dividends["max_ex_dividend_mismatch"] < 1e-12
    assert dividends["mismatched_ex_dividend_days"] == [] and report["warnings"] == []


def test_dividend_adjustment_not_matching_is_flagged():
    report = validate_prices(dividend_frame(1 - 2.0 / 101.0))   # adjusted as if the dividend were 2.0
    assert report["checks"]["dividend_adjustment"]["mismatched_ex_dividend_days"] == [str(sessions(4)[2])]
    assert any("ex-dividend" in w for w in report["warnings"])
    assert report["errors"] == []


def test_unexplained_adjustment_step_is_recorded_not_blocking():
    close = [100.0, 101.0, 102.0]
    adj = [100.0, 101.0 * (1 + 5e-6), 102.0 * (1 + 5e-6)]       # a step on a day without a dividend
    report = validate_prices(raw_frame(adj, close=close))
    steps = check_dividend_adjustment(raw_frame(adj, close=close))["unresolved_adjustment_steps"]
    assert steps["count"] == 1 and steps["dates"] == [str(sessions(3)[1])]
    assert steps["max_abs_log_step"] == pytest.approx(5e-6, rel=1e-3)
    assert any("unexplained" in w for w in report["warnings"]) and report["errors"] == []


# --- returns, splits, placeholders, extreme days ---------------------------------

def test_unsorted_input_is_sorted_and_first_return_is_null():
    d = sessions(3)
    df = raw_frame([12.0, 10.0, 11.0], dates=[d[2], d[0], d[1]])
    assert any("order" in w for w in validate_prices(df)["warnings"])
    out = compute_daily_returns(df)
    assert out["date"].tolist() == d
    assert pd.isna(out["daily_return"].iloc[0])  # excluded, not 0
    assert out["daily_return"].iloc[1:].tolist() == pytest.approx([0.1, 12.0 / 11.0 - 1.0])
    assert validate_returns(out, splits={})["errors"] == []


def test_unadjusted_split_is_an_error():
    # A 4:1 split without adjustment looks like a -75% day
    out = compute_daily_returns(raw_frame([100.0, 25.0, 25.5]))
    split_day = str(sessions(3)[1])
    report = validate_returns(out, splits={split_day: 4.0})
    assert any("unadjusted split" in e for e in report["errors"])
    assert report["checks"]["split_day_returns"][split_day] == pytest.approx(-0.75)


def test_adjusted_split_is_not_an_error():
    out = compute_daily_returns(raw_frame([100.0, 101.0, 102.0]))
    assert validate_returns(out, splits={str(sessions(3)[1]): 4.0})["errors"] == []


def test_zero_volume_rows_and_flat_bars_are_separate_warnings():
    df = raw_frame([10.0, 11.0, 12.0], volume=[100, 0, 100])
    df.loc[2, ["Open", "High", "Low"]] = 12.0          # Open = High = Low = Close
    report = validate_prices(df)
    d = sessions(3)
    assert report["checks"]["zero_volume_rows"] == [str(d[1])]
    assert report["checks"]["flat_bars"] == [str(d[2])]
    assert any("zero-volume" in w for w in report["warnings"])
    assert any("no intraday range" in w for w in report["warnings"]) and report["errors"] == []


def test_extreme_days_are_listed_as_unverified():
    # returns: +25%, -1%, +16% then -14% (a reversal), +2%, +11% on a split day
    prices = [100.0]
    for r in [0.25, -0.01, 0.16, -0.14, 0.02, 0.11]:
        prices.append(prices[-1] * (1 + r))
    out = compute_daily_returns(raw_frame(prices))
    d = [str(x) for x in sessions(len(prices))]
    days = validate_returns(out, splits={d[6]: 2.0})["unverified_extreme_days"]
    assert [x["date"] for x in days] == [d[1], d[3], d[4], d[6]]
    assert days[0]["reasons"] == ["|return| >= 20%"]
    assert days[1]["reasons"] == ["reversed by the next day"]
    assert days[2]["reasons"] == ["reverses the previous day"]
    assert days[3]["reasons"] == ["split day with |return| >= 10%"]
    assert {x["second_source"] for x in days} == {"not checked"}


# --- raw CSV parsing ------------------------------------------------------------

def test_dst_offsets_keep_the_trading_date(tmp_path):
    # DST started 2021-03-14: offset changes from -05:00 to -04:00
    csv = tmp_path / "X.csv"
    csv.write_text(HEADER
                   + "2021-03-12 00:00:00-05:00,1,1,1,1,1,1,0,0\n"
                   + "2021-03-15 00:00:00-04:00,1,1,1,1,1,1,0,0\n")
    df = load_raw_csv(csv, "X")
    assert df["date"].tolist() == [date(2021, 3, 12), date(2021, 3, 15)]


def test_missing_column_is_rejected(tmp_path):
    csv = tmp_path / "X.csv"
    csv.write_text("Date,Close\n2021-03-12 00:00:00-05:00,1\n")
    with pytest.raises(ValueError, match="missing columns"):
        load_raw_csv(csv, "X")
