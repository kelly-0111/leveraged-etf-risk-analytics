"""Snapshot downloads record what was fetched; no network is used here.

AI contribution: written with Claude Code (Opus 5.5).
"""
import hashlib
import json

import pandas as pd
import pytest

from etf_risk.download import REQUIRED_COLUMNS, download_snapshot
from etf_risk.ingest import load_raw_csv


def fake_history(ticker, start, end):
    """Shaped like yfinance Ticker.history(auto_adjust=False, actions=True)."""
    if ticker == "BAD":
        raise ConnectionError("simulated network failure")
    index = pd.DatetimeIndex(["2021-03-12", "2021-03-15", "2021-03-16"], name="Date").tz_localize("America/New_York")
    return pd.DataFrame({c: [1.0, 1.1, 1.2] for c in REQUIRED_COLUMNS}, index=index)


def test_manifest_records_settings_files_and_checksums(tmp_path):
    out = tmp_path / "full-2026-10-12"
    manifest = download_snapshot(["AAA"], "1970-01-01", "2026-01-01", out, fetch=fake_history)

    assert json.loads((out / "manifest.json").read_text()) == manifest
    assert manifest["start"] == "1970-01-01" and manifest["end_exclusive"] == "2026-01-01"
    assert manifest["interval"] == "1d" and manifest["auto_adjust"] is False and manifest["actions"] is True
    [entry] = manifest["results"]
    assert entry["file"] == "AAA.csv"                       # basename only, no local paths
    assert entry["rows"] == 3 and (entry["first_date"], entry["last_date"]) == ("2021-03-12", "2021-03-16")
    assert entry["sha256"] == hashlib.sha256((out / "AAA.csv").read_bytes()).hexdigest()


def test_failed_ticker_is_recorded_not_raised(tmp_path):
    manifest = download_snapshot(["AAA", "BAD"], "1970-01-01", "2026-01-01", tmp_path / "s", fetch=fake_history)
    assert [r["status"] for r in manifest["results"]] == ["ok", "error"]
    assert "simulated network failure" in manifest["results"][1]["error"]


def test_existing_snapshot_is_not_overwritten(tmp_path):
    download_snapshot(["AAA"], "1970-01-01", "2026-01-01", tmp_path / "s", fetch=fake_history)
    with pytest.raises(FileExistsError):
        download_snapshot(["AAA"], "1970-01-01", "2026-01-01", tmp_path / "s", fetch=fake_history)


def test_downloaded_csv_is_readable_by_ingest(tmp_path):
    out = tmp_path / "s"
    download_snapshot(["AAA"], "1970-01-01", "2026-01-01", out, fetch=fake_history)
    df = load_raw_csv(out / "AAA.csv", "AAA")
    assert [str(d) for d in df["date"]] == ["2021-03-12", "2021-03-15", "2021-03-16"]  # DST change kept dates
