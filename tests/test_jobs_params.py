"""A job's parameters and the input checksums that tie it to its snapshot.

AI contribution: written with Claude Code (Opus 5.5).
"""
import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk.jobs.params import InvalidParams, JobParams, check_inputs, input_checksums


def test_defaults_and_the_windows_folder_name():
    p = JobParams.from_dict({"snapshot": "full-2026-10-12", "kind": "rolling"})
    assert (p.window_days, p.stride, p.anchor, p.sample_ticker) == (252, 21, "1980-01-02", "AAPL")
    assert p.windows_name == "rolling-252-s21" and JobParams.from_dict(p.to_dict()) == p
    assert JobParams("full-2026-10-12", "calendar-year").windows_name == "calendar-year"


@pytest.mark.parametrize("data, problem", [
    ({"snapshot": "s", "kind": "rolling", "tickers": ["AAPL"]}, "unknown job parameters: tickers"),
    ({"snapshot": "../etc", "kind": "rolling"}, "plain folder name"),
    ({"snapshot": "a/b", "kind": "rolling"}, "plain folder name"),
    ({"snapshot": "s", "kind": "weekly"}, "kind must be one of"),
    ({"snapshot": "s", "kind": "rolling", "stride": 7}, "at least 21"),
    ({"snapshot": "s", "kind": "rolling", "window_days": "252"}, "positive integer"),
    ({"snapshot": "s", "kind": "rolling", "window_days": True}, "positive integer"),
    ({"snapshot": "s", "kind": "rolling", "anchor": "yesterday"}, "ISO date"),
    ({"snapshot": "s", "kind": "rolling", "sample_ticker": "aapl; rm"}, "ticker symbol"),
    ({"kind": "rolling"}, "snapshot"),
])
def test_unusable_parameters_are_refused(data, problem):
    with pytest.raises(InvalidParams, match=problem):
        JobParams.from_dict(data)


def test_the_checksums_cover_the_returns_and_the_quality_report_and_catch_any_change(tmp_path):
    dates = nyse_sessions("2024-01-02", 31)
    rng = np.random.default_rng(1)
    snap = write_snapshot(tmp_path, "snap", {"AAA": (dates, rng.normal(0, 0.01, 30)),
                                             "BBB": (dates, rng.normal(0, 0.01, 30))})
    root = tmp_path / "processed"
    recorded = input_checksums(root, "snap")
    assert sorted(recorded) == ["daily_returns/AAA.parquet", "daily_returns/BBB.parquet", "quality_report.json"]
    check_inputs(root, "snap", recorded)
    (snap / "quality_report.json").write_text('{"unverified_extreme_days": [{"ticker": "AAA"}]}')
    with pytest.raises(InvalidParams, match="changed \\['quality_report.json'\\]"):
        check_inputs(root, "snap", recorded)
    with pytest.raises(InvalidParams, match="no daily returns"):
        input_checksums(root, "missing")
