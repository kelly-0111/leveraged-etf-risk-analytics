"""Ingest reads only files recorded in a snapshot manifest, with matching SHA-256.

AI contribution: written with Claude Code (Opus 5.5).
"""
import hashlib
import json

import pandas as pd
import pandas_market_calendars as mcal
import pyarrow.parquet as pq
import pytest

from etf_risk.ingest import load_manifest, main

HEADER = "Date,Open,High,Low,Close,Adj Close,Volume,Dividends,Stock Splits\n"


def write_csv(path, n=5, start="2024-01-02"):
    days = mcal.get_calendar("NYSE").valid_days(start, "2024-02-28")[:n]
    rows = [f"{d.date()} 00:00:00-05:00,1,1,1,{10 + i},{10 + i},100,0,0\n" for i, d in enumerate(days)]
    path.write_text(HEADER + "".join(rows))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_snapshot(raw, tickers=("AAA",), manifest_name="manifest.json", absolute_paths=False):
    raw.mkdir(parents=True)
    results = []
    for t in tickers:
        csv = raw / f"{t}.csv"
        sha = write_csv(csv)
        results.append({"ticker": t, "status": "ok", "file": str(csv) if absolute_paths else csv.name, "sha256": sha})
    (raw / manifest_name).write_text(json.dumps({"downloaded_at_utc": "2026-10-12T00:00:00+00:00", "results": results}))


def test_ingest_writes_parquet_and_a_report_that_is_not_fully_verified(tmp_path):
    raw, out = tmp_path / "raw" / "snap-1", tmp_path / "out"
    write_snapshot(raw, tickers=("AAA", "BBB"))
    assert main(["--raw-dir", str(raw), "--out-dir", str(out)]) == 0   # default: all manifest tickers

    table = pq.read_table(out / "daily_returns" / "AAA.parquet")
    assert table.num_rows == 5
    assert table.schema.metadata[b"snapshot"] == b"snap-1"
    report = json.loads((out / "quality_report.json").read_text())
    assert [t["ticker"] for t in report["tickers"]] == ["AAA", "BBB"]
    assert report["overall_status"] == "not fully verified"
    assert report["tickers"][0]["verification_status"]["second_source"].startswith("not done")


def test_changed_file_is_rejected(tmp_path):
    raw, out = tmp_path / "raw" / "snap-1", tmp_path / "out"
    write_snapshot(raw)
    with (raw / "AAA.csv").open("a") as f:
        f.write("2024-01-09 00:00:00-05:00,1,1,1,20,20,100,0,0\n")   # edited after download
    assert main(["--raw-dir", str(raw), "--out-dir", str(out)]) == 1
    report = json.loads((out / "quality_report.json").read_text())["tickers"][0]
    assert report["status"] == "failed"
    assert "does not match the manifest" in report["input"]["errors"][0]
    assert not (out / "daily_returns" / "AAA.parquet").exists()


def test_ticker_missing_from_the_manifest_is_an_error(tmp_path):
    raw, out = tmp_path / "raw" / "snap-1", tmp_path / "out"
    write_snapshot(raw)
    assert main(["--raw-dir", str(raw), "--out-dir", str(out), "--tickers", "AAA", "ZZZ"]) == 1
    report = json.loads((out / "quality_report.json").read_text())
    assert [t["status"] for t in report["tickers"]] == ["ok", "failed"]


def test_prototype_verification_json_with_absolute_paths_is_accepted(tmp_path):
    raw, out = tmp_path / "raw" / "yahoo", tmp_path / "out"
    write_snapshot(raw, manifest_name="verification.json", absolute_paths=True)
    assert main(["--raw-dir", str(raw), "--out-dir", str(out)]) == 0


def test_folder_without_a_manifest_is_rejected(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_manifest(tmp_path)


def test_default_output_folder_is_named_after_the_snapshot(tmp_path, monkeypatch):
    raw = tmp_path / "raw" / "full-2099-01-01"
    write_snapshot(raw)
    monkeypatch.chdir(tmp_path)
    assert main(["--raw-dir", str(raw)]) == 0
    assert (tmp_path / "data" / "processed" / "full-2099-01-01" / "daily_returns" / "AAA.parquet").exists()
    assert pd.read_parquet(tmp_path / "data/processed/full-2099-01-01/daily_returns/AAA.parquet")["daily_return"].isna().sum() == 1
