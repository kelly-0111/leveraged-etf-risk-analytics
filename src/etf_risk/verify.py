"""Compare a sample of a Spark run with an independent Python computation.

Usage:
    uv run python -m etf_risk.verify --run data/outputs/windows/full-2026-10-12/rolling-252-s21/<run-id>

Never run this inside timed runs. Steps:
  1. Verify the SHA-256 of windows.parquet, quality_report.json and every return
     file recorded in the window config; refuse to continue on a mismatch.
  2. Sample: every window of --sample-ticker (default AAPL), every window that
     breaches at 2x (as found by Spark or by Python), and the first and last window
     of each ticker.
  3. Spark filters path_summary and paired to the sample keys before collecting.
  4. Python slices each window from its own sorted returns by locating entry_date
     (not through entry_row), checks the slice ends on exit_date, runs
     model.simulate_path and model.summarize_path, and computes the same turnover,
     date and exact-gap values with the same null rules.
  5. Numbers are compared with rtol = atol = 1e-9 (NaN equals null), dates exactly.
Writes verify.json into the run folder; exit code 1 on any mismatch, 3 on a checksum error.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_verify.py, including a deliberately altered summary value.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from etf_risk.model import STATUS_OK, simulate_path, summarize_path
from etf_risk.provenance import code_state, resolve
from etf_risk.spark_pipeline import INITIAL_NAV, LEVERAGES, PATH_KEY, build_spark
from etf_risk.windows import WINDOW_KEY, ChecksumError, load_returns, verify_checksums

RTOL = ATOL = 1e-9
SUMMARY_NUMBERS = ["n_rows", "days_ok", "breach_day", "final_nav", "total_return", "max_drawdown", "total_abs_rebalance",
                   "max_abs_rebalance", "mean_turnover", "max_turnover", "total_turnover", "n_turnover_days"]
SUMMARY_FLAGS = ["breached"]
SUMMARY_DATES = ["breach_date", "last_ok_date", "max_turnover_date", "first_return_date", "exit_date"]
PAIRED_NUMBERS = ["return_1x", "return_2x", "log_gap", "exact_gap", "realized_variance", "mdd_1x", "mdd_2x",
                  "mdd_2x_pre_breach", "mean_turnover_2x", "mean_turnover_2x_pre_breach", "max_turnover_2x",
                  "max_turnover_2x_pre_breach", "total_turnover_2x", "total_turnover_2x_pre_breach", "days_ok_2x"]


class TickerReturns:
    """One ticker's rows sorted by date, with a date -> position lookup built once."""

    def __init__(self, frame: pd.DataFrame):
        self.dates = frame["date"].to_numpy()
        self.returns = frame["daily_return"].to_numpy(dtype=float)
        self.position = {d: i for i, d in enumerate(self.dates)}

    def window(self, entry_date: date, window_days: int) -> tuple[np.ndarray, np.ndarray]:
        """Dates and returns of the window entered at the close of entry_date (not via entry_row)."""
        if entry_date not in self.position:
            raise KeyError(f"entry date {entry_date} not in the ticker's data")
        i = self.position[entry_date]
        dates, r = self.dates[i + 1:i + 1 + window_days], self.returns[i + 1:i + 1 + window_days]
        if len(dates) != window_days:
            raise ValueError(f"window entered {entry_date} has {len(dates)} of {window_days} returns")
        return dates, r


def python_exact_gap(r: np.ndarray) -> float | None:
    """Exact 2x log gap; None (not a partial sum) if any term is undefined."""
    if not (1 + 2 * r > 0).all():
        return None
    return float(np.log1p(-(r / (1 + r)) ** 2).sum())


def python_summary(dates: np.ndarray, r: np.ndarray, leverage: float, initial_nav: float = INITIAL_NAV) -> dict:
    path = simulate_path(r, leverage, initial_nav)
    s = summarize_path(path, initial_nav)
    ok = path[path["status"] == STATUS_OK]
    turnover = (ok["rebalance"].abs() / ok["nav_start"]).to_numpy()
    out = {
        **s, "n_rows": len(path),
        "breach_day": s["breach_day"],
        "breach_date": dates[s["breach_day"] - 1] if s["breached"] else None,
        "last_ok_date": dates[len(ok) - 1] if len(ok) else None,
        "n_turnover_days": len(turnover),
        "mean_turnover": float(turnover.mean()) if len(turnover) else None,
        "max_turnover": float(turnover.max()) if len(turnover) else None,
        "total_turnover": float(turnover.sum()) if len(turnover) else None,
        "max_turnover_date": None,
    }
    if len(turnover) and turnover.max() > 0:
        out["max_turnover_date"] = dates[int(np.flatnonzero(turnover == turnover.max())[0])]   # earliest on ties
    return out


def select_sample(defs: pd.DataFrame, breached_keys: set[tuple], sample_ticker: str) -> pd.DataFrame:
    by_entry = defs.sort_values(["ticker", "entry_date"], kind="mergesort")
    edges = pd.concat([by_entry.groupby("ticker").head(1), by_entry.groupby("ticker").tail(1)])
    keys = defs[WINDOW_KEY].apply(tuple, axis=1)
    chosen = (defs["ticker"] == sample_ticker) | keys.isin(breached_keys)
    sample = pd.concat([defs[chosen], edges]).drop_duplicates(subset=WINDOW_KEY)
    return sample.sort_values(["ticker", "entry_date"], kind="mergesort").reset_index(drop=True)


def _same_number(a, b) -> bool:
    a = np.nan if a is None or (isinstance(a, float) and math.isnan(a)) else float(a)
    b = np.nan if b is None or (isinstance(b, float) and math.isnan(b)) else float(b)
    return bool(np.isclose(a, b, rtol=RTOL, atol=ATOL, equal_nan=True))


def _same_date(a, b) -> bool:
    norm = lambda x: None if x is None or (isinstance(x, float) and math.isnan(x)) or x is pd.NaT else pd.Timestamp(x).date()  # noqa: E731
    return norm(a) == norm(b)


def compare(sample: pd.DataFrame, tickers: dict[str, TickerReturns], spark_summary: pd.DataFrame,
            spark_paired: pd.DataFrame, leverages=LEVERAGES, initial_nav: float = INITIAL_NAV) -> tuple[list[str], int]:
    """Return (mismatches, number of paths compared)."""
    problems: list[str] = []
    summary_by_key = {tuple(row[k] for k in PATH_KEY): row for row in spark_summary.to_dict("records")}
    paired_by_key = {tuple(row[k] for k in WINDOW_KEY): row for row in spark_paired.to_dict("records")}
    compared = 0
    for w in sample.to_dict("records"):
        wkey = tuple(w[k] for k in WINDOW_KEY)
        try:
            dates, r = tickers[w["ticker"]].window(w["entry_date"], int(w["window_days"]))
        except (KeyError, ValueError) as exc:
            problems.append(f"{wkey}: {exc}")
            continue
        if dates[0] != w["first_return_date"] or dates[-1] != w["exit_date"]:
            problems.append(f"{wkey}: Python slice runs {dates[0]}..{dates[-1]}, definition says "
                            f"{w['first_return_date']}..{w['exit_date']}")
        py = {}
        for lev in leverages:
            pkey = wkey + (float(lev),)
            py[lev] = expected = python_summary(dates, r, float(lev), initial_nav)
            got = summary_by_key.get(pkey)
            compared += 1
            if got is None:
                problems.append(f"{pkey}: missing from Spark path_summary")
                continue
            expected = {**expected, "first_return_date": dates[0], "exit_date": dates[-1]}
            for f in SUMMARY_NUMBERS:
                if not _same_number(expected[f], got[f]):
                    problems.append(f"{pkey} {f}: python={expected[f]} spark={got[f]}")
            for f in SUMMARY_FLAGS:
                if bool(expected[f]) != bool(got[f]):
                    problems.append(f"{pkey} {f}: python={expected[f]} spark={got[f]}")
            for f in SUMMARY_DATES:
                if not _same_date(expected[f], got[f]):
                    problems.append(f"{pkey} {f}: python={expected[f]} spark={got[f]}")
        got = paired_by_key.get(wkey)
        if got is None:
            problems.append(f"{wkey}: missing from Spark paired")
            continue
        one, two = py[1.0], py[2.0]
        not_breached = not two["breached"]
        expected = {
            "return_1x": one["total_return"], "return_2x": two["total_return"],
            "log_gap": math.log1p(two["total_return"]) - 2 * math.log1p(one["total_return"]) if not_breached else None,
            "exact_gap": python_exact_gap(r) if not_breached else None,
            "realized_variance": float((r ** 2).sum()), "mdd_1x": one["max_drawdown"], "days_ok_2x": two["days_ok"],
        }
        # breached 2x: full-window values are null, the partial pre-breach values sit in *_pre_breach columns
        for field, source in (("mdd_2x", "max_drawdown"), ("mean_turnover_2x", "mean_turnover"),
                              ("max_turnover_2x", "max_turnover"), ("total_turnover_2x", "total_turnover")):
            expected[field] = two[source] if not_breached else None
            expected[f"{field}_pre_breach"] = None if not_breached else two[source]
        for f in PAIRED_NUMBERS:
            if not _same_number(expected[f], got[f]):
                problems.append(f"{wkey} paired {f}: python={expected[f]} spark={got[f]}")
    return problems, compared


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--run", type=Path, required=True, help="run folder written by etf_risk.spark_pipeline")
    parser.add_argument("--sample-ticker", default="AAPL")
    args = parser.parse_args(argv)
    started = time.perf_counter()

    record = json.loads((args.run / "run.json").read_text())
    windows_dir = Path(record["windows_dir"])
    try:
        config, verified = verify_checksums(windows_dir)
    except (ChecksumError, FileNotFoundError, KeyError) as exc:
        print(f"checksum verification failed, nothing compared:\n{exc}", file=sys.stderr)
        return 3
    tickers = {t: TickerReturns(f) for t, f in load_returns(resolve(config["snapshot_dir"])).items()}
    defs = pd.read_parquet(windows_dir / config["windows_file"])

    python_breached = {
        tuple(w[k] for k in WINDOW_KEY) for w in defs.to_dict("records")
        if (1 + 2 * tickers[w["ticker"]].window(w["entry_date"], int(w["window_days"]))[1] <= 0).any()
    }
    from pyspark.sql import SparkSession
    own_session = SparkSession.getActiveSession() is None      # only stop a session started here
    spark = build_spark()
    paired_all = spark.read.parquet(str(args.run / "paired"))
    spark_breached = {tuple(r[k] for k in WINDOW_KEY)
                      for r in paired_all.where("breached_2x").select(*WINDOW_KEY).toPandas().to_dict("records")}
    sample = select_sample(defs, python_breached | spark_breached, args.sample_ticker)
    keys = spark.createDataFrame(sample[WINDOW_KEY])
    spark_summary = spark.read.parquet(str(args.run / "path_summary")).join(keys, WINDOW_KEY, "inner").toPandas()
    spark_paired = paired_all.join(keys, WINDOW_KEY, "inner").toPandas()

    problems, compared = compare(sample, tickers, spark_summary, spark_paired)
    result = {
        "run": str(args.run), "code": code_state(), "verified_sha256": verified, "sample_ticker": args.sample_ticker,
        "sample_windows": len(sample), "paths_compared": compared,
        "breached_windows": {"python": len(python_breached), "spark": len(spark_breached),
                             "same": python_breached == spark_breached},
        "mismatches": problems[:200], "mismatch_count": len(problems),
        "tolerance": {"rtol": RTOL, "atol": ATOL}, "seconds": round(time.perf_counter() - started, 2),
    }
    if python_breached != spark_breached:
        problems.append("breached windows differ between Python and Spark")
        result["mismatch_count"] = len(problems)
    (args.run / "verify.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    if own_session:
        spark.stop()
    print(f"verify: {len(sample)} sample windows, {compared} paths compared, {len(problems)} mismatches "
          f"(breached windows: python {len(python_breached)}, spark {len(spark_breached)})")
    for p in problems[:10]:
        print("  ", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
