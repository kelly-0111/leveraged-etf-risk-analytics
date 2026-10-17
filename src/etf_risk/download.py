"""Download daily Yahoo Finance history into a raw snapshot folder with a manifest.

Usage:
    uv run --group download python -m etf_risk.download \\
        --tickers NVDA AAPL MSFT TSLA QQQ --out data/raw/yahoo/full-2026-10-12

Request settings match the 2020-2025 prototype snapshot: interval=1d,
auto_adjust=False, actions=True. A --start before a ticker's first trading day
returns its history from that first day; --end is exclusive.

Output: <out>/<TICKER>.csv plus <out>/manifest.json with the UTC download time,
tool versions, request settings, and per file: rows, first and last date,
SHA-256 and size. Re-downloading does not reproduce the same bytes (see
docs/data-sources.md), so a snapshot is never overwritten: its manifest is
what identifies the data used downstream.

AI contribution: written with Claude Code (Opus 5.5), based on the download
check used for the prototype snapshot. Verified with tests/test_download.py
(fake fetch, no network) and by downloading the five-ticker full-history
snapshot described in docs/data-sources.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from collections.abc import Callable, Sequence
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = ["Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]
REQUEST_SETTINGS = {"interval": "1d", "auto_adjust": False, "actions": True}

Fetch = Callable[[str, str, str], pd.DataFrame]


def yahoo_history(ticker: str, start: str, end: str) -> pd.DataFrame:
    import yfinance as yf  # only installed with the "download" dependency group

    return yf.Ticker(ticker).history(start=start, end=end, timeout=30, **REQUEST_SETTINGS)


def download_snapshot(tickers: Sequence[str], start: str, end: str, out: Path, fetch: Fetch = yahoo_history) -> dict:
    manifest_path = out / "manifest.json"
    if manifest_path.exists():
        raise FileExistsError(f"{manifest_path} exists; snapshots are not overwritten (choose a new --out)")
    out.mkdir(parents=True, exist_ok=True)

    manifest = {
        "source": "Yahoo Finance via yfinance",
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "yfinance": _version("yfinance"),
        "start": start,
        "end_exclusive": end,
        **REQUEST_SETTINGS,
        "results": [],
    }
    for ticker in tickers:
        try:
            df = fetch(ticker, start, end)
            if df.empty:
                raise ValueError("empty response")
            missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
            if missing:
                raise ValueError(f"missing columns {missing}")
            path = out / f"{ticker}.csv"
            df.to_csv(path)
            entry = {
                "ticker": ticker,
                "status": "ok",
                "file": path.name,
                "rows": len(df),
                "first_date": str(df.index[0].date()),
                "last_date": str(df.index[-1].date()),
                "columns": list(df.columns),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
        except Exception as exc:  # recorded in the manifest; the run reports failure below
            entry = {"ticker": ticker, "status": "error", "error": repr(exc)}
        manifest["results"].append(entry)

    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def _version(package: str) -> str:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return "not installed"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tickers", nargs="+", required=True)
    parser.add_argument("--start", default="1970-01-01")
    parser.add_argument("--end", default="2026-01-01", help="exclusive")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    manifest = download_snapshot(args.tickers, args.start, args.end, args.out)
    for r in manifest["results"]:
        if r["status"] == "ok":
            print(f"{r['ticker']}: {r['rows']} rows {r['first_date']}..{r['last_date']} sha256={r['sha256'][:12]}")
        else:
            print(f"{r['ticker']}: ERROR {r['error']}")
    print(f"manifest: {args.out / 'manifest.json'}")
    return 0 if all(r["status"] == "ok" for r in manifest["results"]) else 1


if __name__ == "__main__":
    sys.exit(main())
