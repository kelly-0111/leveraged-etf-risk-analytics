"""Clean raw Yahoo Finance daily CSVs, compute daily returns, save Parquet.

Usage:
    uv run python -m etf_risk.ingest --tickers NVDA
    uv run python -m etf_risk.ingest --tickers NVDA AAPL MSFT TSLA

Input:  data/raw/yahoo/<TICKER>-2020-2025.csv (+ verification.json manifest)
Output: data/processed/daily_returns/<TICKER>.parquet
        data/processed/quality_report.json

Return definition: simple return between consecutive observed trading days,
computed from "Adj Close" (split- and dividend-adjusted). The first row keeps
its price but has a null return; it is never treated as a zero return.

AI contribution: drafted with Claude Code (Opus 5.5). Verified by running on
the NVDA/AAPL/MSFT/TSLA snapshot (row counts, dates, and SHA-256 matched
verification.json) and with tests/test_validation.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from etf_risk.validate import validate_prices, validate_returns

RAW_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]

RETURNS_SCHEMA = pa.schema([
    pa.field("ticker", pa.string(), nullable=False),
    pa.field("date", pa.date32(), nullable=False),
    pa.field("adjusted_price", pa.float64(), nullable=False),
    pa.field("daily_return", pa.float64(), nullable=True),  # null on the first row only
])


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def process_ticker(ticker: str, raw_dir: Path, out_dir: Path, manifest: dict) -> dict:
    csv_path = raw_dir / f"{ticker}-2020-2025.csv"
    input_sha = sha256_file(csv_path)
    expected_sha = manifest.get(ticker, {}).get("sha256")

    prices = load_raw_csv(csv_path, ticker)
    price_report = validate_prices(prices)
    split_dates = [str(d) for d in prices.loc[prices["Stock Splits"] != 0, "date"]]

    report = {
        "ticker": ticker,
        "input_file": str(csv_path),
        "input_sha256": input_sha,
        "manifest_sha256_match": (input_sha == expected_sha) if expected_sha else None,
        "split_events": dict(zip(split_dates, prices.loc[prices["Stock Splits"] != 0, "Stock Splits"].tolist())),
        "prices": price_report,
    }
    if price_report["errors"]:
        report["status"] = "failed"
        return report

    returns = compute_daily_returns(prices)
    returns_report = validate_returns(returns, split_dates)
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
    })
    report.update({
        "status": "ok",
        "output_file": str(out_path),
        "output_rows": len(returns),
        "first_date": str(returns["date"].iloc[0]),
        "last_date": str(returns["date"].iloc[-1]),
    })
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tickers", nargs="+", default=["NVDA"])
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/yahoo"))
    parser.add_argument("--out-dir", type=Path, default=Path("data/processed"))
    args = parser.parse_args(argv)

    manifest_path = args.raw_dir / "verification.json"
    manifest = {}
    if manifest_path.exists():
        manifest = {r["ticker"]: r for r in json.loads(manifest_path.read_text())["results"]}

    reports = [process_ticker(t, args.raw_dir, args.out_dir, manifest) for t in args.tickers]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    report_path = args.out_dir / "quality_report.json"
    report_path.write_text(json.dumps({
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "tickers": reports,
    }, indent=2, default=str))

    for r in reports:
        line = f"{r['ticker']}: {r['status']}"
        if r["status"] == "ok":
            line += f"  rows={r['output_rows']}  {r['first_date']}..{r['last_date']}  sha_match={r['manifest_sha256_match']}"
        print(line)
        for section in ("prices", "returns"):
            for msg in r.get(section, {}).get("errors", []):
                print(f"  ERROR   {msg}")
            for msg in r.get(section, {}).get("warnings", []):
                print(f"  warning {msg}")
    print(f"report: {report_path}")
    return 0 if all(r["status"] == "ok" for r in reports) else 1


if __name__ == "__main__":
    sys.exit(main())
