"""Bad inputs must be reported, not silently fixed.

AI contribution: drafted with Claude Code (Opus 5.5).
"""
from datetime import date

import numpy as np
import pandas as pd
import pytest

from etf_risk.ingest import compute_daily_returns, load_raw_csv
from etf_risk.validate import validate_prices, validate_returns

HEADER = "Date,Open,High,Low,Close,Adj Close,Volume,Dividends,Stock Splits\n"


def raw_frame(adj_close, dates=None):
    n = len(adj_close)
    dates = dates or [date(2024, 1, 2 + i) for i in range(n)]
    return pd.DataFrame({
        "ticker": "TEST", "date": dates,
        "Open": 1.0, "High": 1.0, "Low": 1.0, "Close": 1.0, "Adj Close": adj_close,
        "Volume": 100, "Dividends": 0.0, "Stock Splits": 0.0,
    })


def test_clean_data_passes():
    report = validate_prices(raw_frame([10.0, 11.0, 12.0]))
    assert report["errors"] == []


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


def test_long_gap_is_a_warning():
    df = raw_frame([10.0, 11.0], dates=[date(2024, 1, 2), date(2024, 1, 12)])
    assert any("gaps" in w for w in validate_prices(df)["warnings"])


def test_unsorted_input_is_sorted_and_first_return_is_null():
    df = raw_frame([12.0, 10.0, 11.0], dates=[date(2024, 1, 4), date(2024, 1, 2), date(2024, 1, 3)])
    assert any("order" in w for w in validate_prices(df)["warnings"])
    out = compute_daily_returns(df)
    assert out["date"].tolist() == [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4)]
    assert pd.isna(out["daily_return"].iloc[0])  # excluded, not 0
    assert out["daily_return"].iloc[1:].tolist() == pytest.approx([0.1, 12.0 / 11.0 - 1.0])
    assert validate_returns(out, split_dates=[])["errors"] == []


def test_unadjusted_split_shows_up_as_warning():
    # A 4:1 split without adjustment looks like a -75% day
    out = compute_daily_returns(raw_frame([100.0, 25.0, 25.5]))
    report = validate_returns(out, split_dates=["2024-01-03"])
    assert report["warnings"]
    assert report["checks"]["split_day_returns"]["2024-01-03"] == pytest.approx(-0.75)


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
