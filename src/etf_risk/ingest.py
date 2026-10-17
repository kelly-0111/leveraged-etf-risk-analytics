"""Clean raw Yahoo Finance daily CSVs, compute daily returns, save Parquet.

Usage:
    uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo/full-2026-10-12
    uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo --tickers NVDA AAPL MSFT TSLA  # 2020-2025 prototype

Input:  a raw snapshot folder whose manifest lists each CSV and its SHA-256:
        manifest.json (from etf_risk.download) or the prototype's verification.json
Output: data/processed/<snapshot folder name>/daily_returns/<TICKER>.parquet
        data/processed/<snapshot folder name>/quality_report.json

Each CSV must match the SHA-256 in its manifest, so processed data always comes
from a recorded snapshot. Return definition: simple return between consecutive
observed trading days, computed from "Adj Close" (split- and dividend-adjusted).
The first row keeps its price but has a null return; it is never treated as a
zero return. Check results and data limitations: docs/data-sources.md.

AI contribution: drafted with Claude Code (Opus 5.5). Verified with
tests/test_ingest.py and tests/test_validation.py, and by running on the
2020-2025 prototype snapshot and the full-history snapshot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from etf_risk.validate import REFERENCE_CALENDAR, validate_prices, validate_returns

RAW_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]
MANIFEST_NAMES = ("manifest.json", "verification.json")  # current, prototype

RETURNS_SCHEMA = pa.schema([
    pa.field("ticker", pa.string(), nullable=False),
    pa.field("date", pa.date32(), nullable=False),
    pa.field("adjusted_price", pa.float64(), nullable=False),
    pa.field("daily_return", pa.float64(), nullable=True),  # null on the first row only
])


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(raw_dir: Path) -> tuple[Path, dict]:
    for name in MANIFEST_NAMES:
        path = raw_dir / name
        if path.is_file():
            return path, json.loads(path.read_text())
    raise FileNotFoundError(f"no {' or '.join(MANIFEST_NAMES)} in {raw_dir}")


def load_raw_csv(path: Path, ticker: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in RAW_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    # Timestamps look like "2020-01-02 00:00:00-05:00": midnight exchange time,
    # with the offset switching at DST. The first 10 characters are the
    # trading date; converting to UTC first could shift it.
    df["date"] = pd.to_datetime(df["Date"].str[:10], format="%Y-%m-%d").dt.date
    df.insert(0, "ticker", ticker)
    return df


def compute_daily_returns(prices: pd.DataFrame) -> pd.DataFrame:
    out = (
        prices.sort_values("date", kind="mergesort")
        .loc[:, ["ticker", "date", "Adj Close"]]
        .rename(columns={"Adj Close": "adjusted_price"})
        .reset_index(drop=True)
    )
    # Written out instead of pct_change(), which can forward-fill missing prices.
    out["daily_return"] = out["adjusted_price"] / out["adjusted_price"].shift(1) - 1.0
    return out


def write_returns_parquet(returns: pd.DataFrame, path: Path, metadata: dict[str, str]) -> None:
    table = pa.Table.from_pandas(returns, schema=RETURNS_SCHEMA, preserve_index=False)
    table = table.replace_schema_metadata({k.encode(): v.encode() for k, v in metadata.items()})
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)


def process_ticker(ticker: str, raw_dir: Path, out_dir: Path, entry: dict | None, snapshot: dict) -> dict:
    report = {"ticker": ticker, "input": {"errors": [], "warnings": []}}

    def failed(message: str) -> dict:
        report["input"]["errors"].append(message)
        report["status"] = "failed"
        return report

    if entry is None or entry.get("status") != "ok":
        return failed(f"no usable manifest entry for {ticker}")
    csv_path = raw_dir / Path(entry["file"]).name  # prototype manifests hold absolute paths
    if not csv_path.is_file():
        return failed(f"{csv_path} not found")
    input_sha = sha256_file(csv_path)
    report.update({"input_file": str(csv_path), "input_sha256": input_sha})
    if input_sha != entry.get("sha256"):
        return failed(f"SHA-256 of {csv_path.name} does not match the manifest (file changed since download)")

    prices = load_raw_csv(csv_path, ticker)
    price_report = validate_prices(prices)
    split_rows = prices.loc[prices["Stock Splits"] != 0]
    splits = {str(d): float(x) for d, x in zip(split_rows["date"], split_rows["Stock Splits"])}
    report.update({"split_events": splits, "prices": price_report})
    if price_report["errors"]:
        report["status"] = "failed"
        return report

    returns = compute_daily_returns(prices)
    returns_report = validate_returns(returns, splits)
    report["returns"] = returns_report
    if returns_report["errors"]:
        report["status"] = "failed"
        return report

    out_path = out_dir / "daily_returns" / f"{ticker}.parquet"
    write_returns_parquet(returns, out_path, {
        "source": "Yahoo Finance via yfinance (auto_adjust=False)",
        "price_field": "Adj Close",
        "return_definition": "adjusted_price_t / adjusted_price_(t-1) - 1 over consecutive observed trading days",
        "input_sha256": input_sha,
        "snapshot": snapshot["name"],
        "manifest_sha256": snapshot["manifest_sha256"],
        "downloaded_at_utc": snapshot["downloaded_at_utc"],
    })
    report.update({
        "status": "ok",
        "output_file": str(out_path),
        "output_rows": len(returns),
        "first_date": str(returns["date"].iloc[0]),
        "last_date": str(returns["date"].iloc[-1]),
        "verification_status": verification_status(price_report, returns_report),
    })
    return report


def verification_status(price_report: dict, returns_report: dict) -> dict:
    """What was checked and what was not. Never reports the data as fully verified."""
    calendar = price_report["checks"]["trading_calendar"]
    dividends = price_report["checks"]["dividend_adjustment"]
    unresolved = dividends["unresolved_adjustment_steps"]
    extreme = returns_report["unverified_extreme_days"]
    return {
        "trading_calendar": f"checked against {REFERENCE_CALENDAR}: {len(calendar['missing_rows'])} missing rows, "
                            f"{len(calendar['extra_rows'])} extra rows",
        # Reached only when no split-day return resembled an unadjusted split (that is an error).
        "splits": f"none of {len(returns_report['checks']['split_day_returns'])} split-day returns resembles an "
                  "unadjusted split; split adjustments not independently confirmed",
        "dividends": f"Adj Close consistent with Yahoo's dividend records on {dividends['ex_dividend_days']} "
                     f"ex-dividend days ({len(dividends['mismatched_ex_dividend_days'])} mismatches); "
                     f"{unresolved['count']} unresolved adjustment steps; amounts not independently confirmed",
        "second_source": f"not done; {len(extreme)} extreme days unverified",
        "license": "not reviewed",
        "overall": "not fully verified",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/yahoo"))
    parser.add_argument("--tickers", nargs="+", help="default: every ticker in the manifest")
    parser.add_argument("--out-dir", type=Path, help="default: data/processed/<raw-dir folder name>")
    args = parser.parse_args(argv)
    out_dir = args.out_dir or Path("data/processed") / args.raw_dir.name

    manifest_path, manifest = load_manifest(args.raw_dir)
    entries = {r["ticker"]: r for r in manifest["results"]}
    snapshot = {
        "name": args.raw_dir.name,
        "manifest": manifest_path.name,
        "manifest_sha256": sha256_file(manifest_path),
        "downloaded_at_utc": manifest.get("downloaded_at_utc", ""),
        "source": manifest.get("source", ""),
        "settings": {k: manifest.get(k) for k in ("start", "end_exclusive", "auto_adjust", "actions")},
    }

    tickers = args.tickers or list(entries)
    reports = [process_ticker(t, args.raw_dir, out_dir, entries.get(t), snapshot) for t in tickers]
    extreme = [
        {"ticker": r["ticker"], **day}
        for r in reports if r["status"] == "ok"
        for day in r["returns"]["unverified_extreme_days"]
    ]
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / "quality_report.json"
    report_path.write_text(json.dumps({
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
        "reference_calendar": f"{REFERENCE_CALENDAR} (pandas_market_calendars {package_version('pandas_market_calendars')})",
        "overall_status": "not fully verified",
        "tickers": reports,
        "unverified_extreme_days": extreme,
    }, indent=2, default=str) + "\n")

    for r in reports:
        line = f"{r['ticker']}: {r['status']}"
        if r["status"] == "ok":
            line += f"  rows={r['output_rows']}  {r['first_date']}..{r['last_date']}"
        print(line)
        for section in ("input", "prices", "returns"):
            for msg in r.get(section, {}).get("errors", []):
                print(f"  ERROR   {msg}")
            for msg in r.get(section, {}).get("warnings", []):
                print(f"  warning {msg}")
    print(f"{len(extreme)} extreme days listed as unverified (no second source yet)")
    print(f"report: {report_path}")
    return 0 if all(r["status"] == "ok" for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
