"""Build fixed holding-window definitions from a processed daily-returns snapshot.

Usage:
    uv run python -m etf_risk.windows --snapshot full-2026-10-12 --kind rolling --stride 21
    uv run python -m etf_risk.windows --snapshot full-2026-10-12 --kind calendar-year
    uv run python -m etf_risk.windows --snapshot yahoo --kind full-period

Input:  data/processed/<snapshot>/daily_returns/<TICKER>.parquet and quality_report.json
Output: data/windows/<snapshot>/<name>/windows.parquet and config.json, where <name> is
        rolling-<window_days>-s<stride>, calendar-year or full-period

A window is `window_days` consecutive daily returns of one ticker: entry at the
close on entry_date (the price date before the first return), exit at the close
on exit_date (the last return date). See docs/spec.md, section 7.

- rolling (main analysis): 252 returns; a window starts where its first return
  date is an NYSE session whose index, counted from the anchor date, is a
  multiple of the stride, so all tickers' windows start on the same dates. Only
  complete windows are kept.
- calendar-year (labeled supplement): entry at the ticker's close on the last
  session of the previous year, returns for every session of the year; only
  complete years, so window_days varies.
- full-period: one window per ticker over all its returns (the prototype case).

Unverified-day flag (conservative rule, changed in the Stage 2 cleanup): a window
is flagged when any date whose closing price it uses, entry_date through
exit_date, is an unverified extreme day from quality_report.json. The first rule
counted only return dates (first_return_date..exit_date); the entry date was
added because the entry price comes from that day's close. The flag marks
windows for a sensitivity analysis; it does not mean the data is wrong.

Before writing, check_definitions() re-derives every window from the returns and
must find no violation (dates of entry/first/exit rows, the start grid and
spacing, complete coverage, calendar years, flags); the counts go into config.json.
config.json also records the SHA-256 of every return file, of quality_report.json
and of windows.parquet; verify_checksums() is called by the Spark pipeline and by
verify.py before they read anything.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_windows.py, by check_definitions() on every window, and by checking
the stride-21 counts against an earlier independent count (1,790 windows).
"""
from __future__ import annotations

import argparse
import bisect
import json
import sys
from datetime import date, datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path

import numpy as np
import pandas as pd
import pandas_market_calendars as mcal
import pyarrow as pa
import pyarrow.parquet as pq

from etf_risk.ingest import sha256_file
from etf_risk.provenance import code_state, resolve
from etf_risk.validate import REFERENCE_CALENDAR

ROLLING_WINDOW_DAYS = 252
MIN_STRIDE = 21                   # smaller strides need --allow-dense-stride (measure first)
DEFAULT_ANCHOR = "1980-01-02"     # first NYSE session of 1980; fixes the shared start grid
KIND_NAMES = {"rolling": "rolling", "calendar-year": "calendar_year", "full-period": "full_period"}
WINDOW_KEY = ["window_kind", "ticker", "window_days", "entry_date"]

DEFINITION_SCHEMA = pa.schema([
    pa.field("window_kind", pa.string(), nullable=False),
    pa.field("ticker", pa.string(), nullable=False),
    pa.field("window_days", pa.int32(), nullable=False),
    pa.field("entry_date", pa.date32(), nullable=False),
    pa.field("first_return_date", pa.date32(), nullable=False),
    pa.field("exit_date", pa.date32(), nullable=False),
    pa.field("entry_row", pa.int32(), nullable=False),     # row of the entry price, 0 = first price
    pa.field("stride", pa.int32(), nullable=True),          # rolling only
    pa.field("calendar_year", pa.int32(), nullable=True),   # calendar-year only
    pa.field("contains_unverified_day", pa.bool_(), nullable=False),     # any price date entry..exit unverified
    pa.field("unverified_day_count", pa.int32(), nullable=False),        # unverified days among entry..exit
    pa.field("entry_on_unverified_day", pa.bool_(), nullable=False),     # the entry date itself is unverified
])


class ChecksumError(RuntimeError):
    """An input or definition file differs from the SHA-256 recorded in config.json."""


def load_returns(snapshot_dir: Path) -> dict[str, pd.DataFrame]:
    """One frame per ticker, sorted by date, index = row (0 = first price)."""
    frames = {}
    for path in sorted((snapshot_dir / "daily_returns").glob("*.parquet")):
        df = pq.read_table(path).to_pandas().sort_values("date", kind="mergesort").reset_index(drop=True)
        ticker = path.stem
        if df["date"].duplicated().any():
            raise ValueError(f"{path}: duplicate dates")
        if not pd.isna(df["daily_return"].iloc[0]) or df["daily_return"].iloc[1:].isna().any():
            raise ValueError(f"{path}: expected a null return on the first row only")
        frames[ticker] = df
    if not frames:
        raise FileNotFoundError(f"no return files in {snapshot_dir / 'daily_returns'}")
    return frames


def session_grid(first: date, last: date, anchor: date) -> dict[date, int]:
    """NYSE session -> its index counted from the anchor session."""
    sessions = mcal.get_calendar(REFERENCE_CALENDAR).valid_days(anchor, last).tz_convert(None).normalize()
    if sessions.empty or sessions[0].date() != anchor:
        raise ValueError(f"anchor {anchor} is not an {REFERENCE_CALENDAR} session")
    if first < anchor:
        raise ValueError(f"data starts {first}, before the anchor {anchor}")
    return {d.date(): i for i, d in enumerate(sessions)}


def rolling_windows(ticker: str, df: pd.DataFrame, window_days: int, stride: int, grid: dict[date, int]) -> pd.DataFrame:
    dates = df["date"].tolist()
    off_grid = [d for d in dates if d not in grid]
    if off_grid:
        raise ValueError(f"{ticker}: {len(off_grid)} dates are not {REFERENCE_CALENDAR} sessions, e.g. {off_grid[:3]}")
    n = len(dates) - 1                                   # returns are rows 1..n
    first_rows = np.arange(1, n - window_days + 2)       # first return row k; last return row k + window_days - 1
    index = np.array([grid[d] for d in dates])
    first_rows = first_rows[index[first_rows] % stride == 0]
    return pd.DataFrame({
        "window_kind": "rolling", "ticker": ticker, "window_days": window_days,
        "entry_date": [dates[k - 1] for k in first_rows],
        "first_return_date": [dates[k] for k in first_rows],
        "exit_date": [dates[k + window_days - 1] for k in first_rows],
        "entry_row": first_rows - 1, "stride": stride, "calendar_year": None,
    })


def calendar_year_windows(ticker: str, df: pd.DataFrame) -> tuple[pd.DataFrame, list[int]]:
    """Complete calendar years only; returns (windows, skipped years)."""
    dates = pd.to_datetime(df["date"])
    calendar = mcal.get_calendar(REFERENCE_CALENDAR)
    rows, skipped = [], []
    for year in sorted(set(dates.dt.year)):
        sessions = calendar.valid_days(f"{year - 1}-01-01", f"{year}-12-31").tz_convert(None).normalize()
        prev_last = sessions[sessions.year == year - 1].max()
        year_sessions = sessions[sessions.year == year]
        in_year = np.flatnonzero((dates.dt.year == year).to_numpy())
        complete = (
            len(in_year) == len(year_sessions)
            and in_year[0] >= 1
            and dates.iloc[in_year[0] - 1] == prev_last
            and (dates.iloc[in_year].to_numpy() == year_sessions.to_numpy()).all()
        )
        if not complete:
            skipped.append(int(year))
            continue
        entry_row = int(in_year[0] - 1)
        rows.append({
            "window_kind": "calendar_year", "ticker": ticker, "window_days": len(in_year),
            "entry_date": df["date"].iloc[entry_row], "first_return_date": df["date"].iloc[in_year[0]],
            "exit_date": df["date"].iloc[in_year[-1]], "entry_row": entry_row,
            "stride": None, "calendar_year": int(year),
        })
    return pd.DataFrame(rows), skipped


def full_period_windows(ticker: str, df: pd.DataFrame) -> pd.DataFrame:
    n = len(df) - 1
    return pd.DataFrame([{
        "window_kind": "full_period", "ticker": ticker, "window_days": n,
        "entry_date": df["date"].iloc[0], "first_return_date": df["date"].iloc[1],
        "exit_date": df["date"].iloc[n], "entry_row": 0, "stride": None, "calendar_year": None,
    }])


def flag_unverified(defs: pd.DataFrame, unverified: dict[str, list[str]]) -> pd.DataFrame:
    """Conservative rule: count unverified extreme days among the price dates a window uses,
    entry_date through exit_date (the entry price is that day's close)."""
    counts, on_entry = [], []
    for ticker, entry, last in zip(defs["ticker"], defs["entry_date"], defs["exit_date"]):
        days = unverified.get(ticker, [])
        start = bisect.bisect_left(days, str(entry))
        counts.append(bisect.bisect_right(days, str(last)) - start)
        on_entry.append(start < len(days) and days[start] == str(entry))
    defs = defs.copy()
    defs["unverified_day_count"] = counts
    defs["contains_unverified_day"] = defs["unverified_day_count"] > 0
    defs["entry_on_unverified_day"] = on_entry
    return defs


def check_definitions(defs: pd.DataFrame, frames: dict[str, pd.DataFrame], kind: str, unverified: dict[str, list[str]],
                      window_days: int | None = None, stride: int | None = None,
                      grid: dict[date, int] | None = None) -> dict[str, int]:
    """Re-derive every window from the returns; each count is a number of violations (all must be 0)."""
    v = dict.fromkeys(["duplicate_window_keys", "unknown_ticker", "rows_out_of_range", "row_dates_mismatch",
                       "flag_mismatch", "not_on_grid", "wrong_window_days", "spacing_not_stride",
                       "missing_or_extra_windows", "calendar_year_mismatch", "not_full_period"], 0)
    v["duplicate_window_keys"] = int(defs[WINDOW_KEY].duplicated().sum())
    year_sessions: dict[int, list[date]] = {}
    calendar = mcal.get_calendar(REFERENCE_CALENDAR)
    for ticker, g in defs.groupby("ticker"):
        if ticker not in frames:
            v["unknown_ticker"] += len(g)
            continue
        dates = frames[ticker]["date"].tolist()
        n = len(dates) - 1
        used = set(unverified.get(ticker, []))
        for w in g.itertuples():
            if w.entry_row < 0 or w.entry_row + w.window_days > n:
                v["rows_out_of_range"] += 1
                continue
            if (dates[w.entry_row], dates[w.entry_row + 1], dates[w.entry_row + w.window_days]) != \
                    (w.entry_date, w.first_return_date, w.exit_date):
                v["row_dates_mismatch"] += 1
            count = sum(str(d) in used for d in dates[w.entry_row:w.entry_row + w.window_days + 1])
            if (count, count > 0, str(w.entry_date) in used) != \
                    (w.unverified_day_count, w.contains_unverified_day, w.entry_on_unverified_day):
                v["flag_mismatch"] += 1
            if kind == "calendar-year":
                y = int(w.calendar_year)
                if y not in year_sessions:
                    s = calendar.valid_days(f"{y}-01-01", f"{y}-12-31").tz_convert(None).normalize()
                    year_sessions[y] = [d.date() for d in s]
                if (w.entry_date.year, w.first_return_date, w.exit_date, w.window_days) != \
                        (y - 1, year_sessions[y][0], year_sessions[y][-1], len(year_sessions[y])):
                    v["calendar_year_mismatch"] += 1
        if kind == "rolling":
            index = np.sort([grid[d] for d in g["first_return_date"]])
            v["not_on_grid"] += int((index % stride != 0).sum())
            v["wrong_window_days"] += int((g["window_days"] != window_days).sum())
            v["spacing_not_stride"] += int((np.diff(index) != stride).sum())
            expected = sum(1 for k in range(1, n - window_days + 2) if grid[dates[k]] % stride == 0)
            v["missing_or_extra_windows"] += abs(expected - len(g))
        elif kind == "full-period":
            v["not_full_period"] += int(((g["entry_row"] != 0) | (g["window_days"] != n)).sum()) + (len(g) != 1)
    return v


def build_definitions(snapshot_dir: Path, kind: str, window_days: int = ROLLING_WINDOW_DAYS,
                      stride: int = MIN_STRIDE, anchor: str = DEFAULT_ANCHOR) -> tuple[pd.DataFrame, dict]:
    frames = load_returns(snapshot_dir)
    report = json.loads((snapshot_dir / "quality_report.json").read_text())
    unverified: dict[str, list[str]] = {}
    for day in report["unverified_extreme_days"]:
        unverified.setdefault(day["ticker"], []).append(day["date"])
    unverified = {t: sorted(d) for t, d in unverified.items()}

    parts, skipped, grid = [], {}, None
    if kind == "rolling":
        anchor_date = date.fromisoformat(anchor)
        grid = session_grid(min(df["date"].iloc[0] for df in frames.values()),
                            max(df["date"].iloc[-1] for df in frames.values()), anchor_date)
        parts = [rolling_windows(t, df, window_days, stride, grid) for t, df in frames.items()]
    elif kind == "calendar-year":
        for t, df in frames.items():
            windows, skipped[t] = calendar_year_windows(t, df)
            parts.append(windows)
    elif kind == "full-period":
        parts = [full_period_windows(t, df) for t, df in frames.items()]
    else:
        raise ValueError(f"unknown kind {kind!r}")

    defs = pd.concat([p for p in parts if not p.empty], ignore_index=True)
    defs = flag_unverified(defs, unverified).sort_values(["ticker", "entry_date"], kind="mergesort")
    defs = defs.reset_index(drop=True)[DEFINITION_SCHEMA.names]
    checks = check_definitions(defs, frames, kind, unverified, window_days, stride, grid)
    if any(checks.values()):
        raise ValueError(f"window definitions failed their self-check: { {k: n for k, n in checks.items() if n} }")

    manifests = {t: (pq.read_schema(snapshot_dir / "daily_returns" / f"{t}.parquet").metadata or {})
                 .get(b"manifest_sha256", b"").decode() or None for t in frames}
    config = {
        "kind": KIND_NAMES[kind],
        "window_days": window_days if kind == "rolling" else None,
        "stride": stride if kind == "rolling" else None,
        "anchor": anchor if kind == "rolling" else None,
        "calendar": f"{REFERENCE_CALENDAR} (pandas_market_calendars {package_version('pandas_market_calendars')})",
        "unverified_flag_rule": "unverified extreme days among the price dates entry_date..exit_date "
                                "(conservative rule; the entry date was added in the Stage 2 cleanup)",
        "snapshot": snapshot_dir.name,
        "snapshot_dir": str(snapshot_dir),        # relative paths are resolved against the repository root
        "raw_manifest_sha256_by_ticker": manifests,
        "definition_checks": checks,
        "inputs_sha256": {
            **{f"daily_returns/{t}.parquet": sha256_file(snapshot_dir / "daily_returns" / f"{t}.parquet") for t in frames},
            "quality_report.json": sha256_file(snapshot_dir / "quality_report.json"),
        },
        "counts": {
            "windows": len(defs),
            "by_ticker": {t: int(n) for t, n in defs.groupby("ticker").size().items()},
            "with_unverified_day": {t: int(n) for t, n in defs.groupby("ticker")["contains_unverified_day"].sum().items()},
        },
        "skipped_calendar_years": skipped or None,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "code": code_state(),
    }
    return defs, config


def write_definitions(defs: pd.DataFrame, config: dict, out_dir: Path, overwrite: bool = False) -> Path:
    if (out_dir / "config.json").exists() and not overwrite:
        raise FileExistsError(f"{out_dir} already has window definitions (use --overwrite)")
    out_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pandas(defs, schema=DEFINITION_SCHEMA, preserve_index=False), out_dir / "windows.parquet")
    config = {**config, "windows_file": "windows.parquet", "windows_sha256": sha256_file(out_dir / "windows.parquet")}
    (out_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    return out_dir


def verify_checksums(windows_dir: Path) -> tuple[dict, dict[str, str]]:
    """Recompute every recorded SHA-256; raise ChecksumError naming each missing or changed file."""
    config = json.loads((windows_dir / "config.json").read_text())
    snapshot_dir = resolve(config["snapshot_dir"])
    expected = {str(windows_dir / config["windows_file"]): config["windows_sha256"]}
    expected.update({str(snapshot_dir / rel): sha for rel, sha in config["inputs_sha256"].items()})
    problems, verified = [], {}
    for path, sha in expected.items():
        if not Path(path).is_file():
            problems.append(f"{path}: missing")
        elif (actual := sha256_file(Path(path))) != sha:
            problems.append(f"{path}: SHA-256 {actual[:12]}… differs from recorded {sha[:12]}…")
        else:
            verified[path] = sha
    if problems:
        raise ChecksumError("input checksum verification failed:\n  " + "\n  ".join(problems))
    return config, verified


def default_name(kind: str, window_days: int, stride: int) -> str:
    return f"rolling-{window_days}-s{stride}" if kind == "rolling" else kind


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--snapshot", required=True, help="folder name under --processed-root")
    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
    parser.add_argument("--kind", choices=list(KIND_NAMES), required=True)
    parser.add_argument("--window-days", type=int, default=ROLLING_WINDOW_DAYS)
    parser.add_argument("--stride", type=int, default=MIN_STRIDE)
    parser.add_argument("--anchor", default=DEFAULT_ANCHOR)
    parser.add_argument("--allow-dense-stride", action="store_true",
                        help=f"allow --stride below {MIN_STRIDE} (only after measuring memory and runtime)")
    parser.add_argument("--out-root", type=Path, default=Path("data/windows"))
    parser.add_argument("--name", help="output folder name (default: rolling-<days>-s<stride>, calendar-year or full-period)")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args(argv)
    if args.kind == "rolling" and args.stride < MIN_STRIDE and not args.allow_dense_stride:
        parser.error(f"--stride below {MIN_STRIDE} needs --allow-dense-stride (measure a sparser stride first)")

    snapshot_dir = args.processed_root / args.snapshot
    defs, config = build_definitions(snapshot_dir, args.kind, args.window_days, args.stride, args.anchor)
    out_dir = args.out_root / args.snapshot / (args.name or default_name(args.kind, args.window_days, args.stride))
    write_definitions(defs, config, out_dir, overwrite=args.overwrite)
    print(f"{len(defs)} windows -> {out_dir}")
    for t, n in config["counts"]["by_ticker"].items():
        print(f"  {t}: {n} windows, {config['counts']['with_unverified_day'][t]} with an unverified day")
    if config["skipped_calendar_years"]:
        print("  incomplete calendar years skipped:", {t: y for t, y in config["skipped_calendar_years"].items() if y})
    return 0


if __name__ == "__main__":
    sys.exit(main())
