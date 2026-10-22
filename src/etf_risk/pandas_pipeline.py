"""Compute the Spark pipeline's results in one Python process with pandas, without Spark: the single-process baseline.

Usage:
    uv run python -m etf_risk.pandas_pipeline --windows data/windows/full-2026-10-12/rolling-252-s21
    (for timed runs, start it through etf_risk.measure --pipeline pandas)

The baseline of docs/spec.md, section 8, expectation 5 ("a single-process pandas run may be faster at
these sizes"; docs/pandas-baseline.md). From the same inputs it computes the same outputs, phase by
phase and with the same Parquet column types, as etf_risk.spark_pipeline:
  window_stats/, path_days/ (partitioned by ticker), path_summary/, paired/, checks.json, run.json
run.json has the Spark pipeline's fields apart from the Spark ones (spark, stage_task_counts and the
session_start timing) and adds "engine": "pandas".

It is a separate implementation that shares only the model function with the Spark pipeline; it
builds the member rows, aggregates, checks and writes in its own way. Timing the two is therefore an
end-to-end comparison of implementations, not a measurement of Spark's overhead.

How it corresponds to the Spark pipeline:
  - inputs: every SHA-256 recorded in the window config is verified first. Reading the files counts
    toward the window-statistics phase, where the Spark pipeline reads them.
  - window members: each definition's rows (entry_row + 1 to entry_row + window_days) are looked up in
    its ticker's returns; rows that do not exist are dropped, as by the Spark pipeline's inner join.
  - model: one call per window that sorts it by date, checks it is complete and runs
    model.simulate_path for every leverage on the same returns, the body of the Spark pipeline's
    grouped pandas function.
  - window statistics, summaries, pairing and the ten checks: the same rules, count guards and
    tolerances. The checks use nullable pandas types, so a null compares as in SQL and is never a
    violation by itself. A NaN from the model is stored as null, as the Spark pipeline stores it.
  - outputs: each table is written once; the Spark pipeline writes it and reads it back.
It never imports pyspark.

Exit codes as in the Spark pipeline: 0 all checks passed, 1 a check failed, 2 the run failed,
3 checksum error.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_pandas_pipeline.py:
every output table and every check count equal to the Spark pipeline's on the test snapshot,
including the failures that tests/test_spark_equivalence.py injects.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from collections.abc import Sequence
from datetime import datetime, timezone
from importlib.metadata import version as package_version
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from etf_risk.model import STATUS_BREACH, STATUS_OK, simulate_path
from etf_risk.provenance import code_state, resolve
from etf_risk.windows import WINDOW_KEY, ChecksumError, verify_checksums

# The Spark pipeline's values; tests/test_pandas_pipeline.py checks they are equal.
LEVERAGES = (1.0, 2.0)
PATH_KEY = WINDOW_KEY + ["leverage"]
INITIAL_NAV = 100.0
RTOL, ATOL = 1e-9, 1e-12
GAP_ATOL = 1e-9
BOUND_TOL = 1e-12
PAIRED_2X_PATH_VALUES = ["mdd_2x", "mean_turnover_2x", "max_turnover_2x", "total_turnover_2x"]

_S, _I32, _I64, _F, _B, _D = pa.string(), pa.int32(), pa.int64(), pa.float64(), pa.bool_(), pa.date32()


def _schema(*fields: tuple[str, pa.DataType]) -> pa.Schema:
    return pa.schema([pa.field(name, kind) for name, kind in fields])


# Column names, order and types of the Spark pipeline's Parquet output.
_KEY = [("window_kind", _S), ("ticker", _S), ("window_days", _I32), ("entry_date", _D)]
_SCHEDULED = [("first_return_date", _D), ("exit_date", _D)]
_FLAGS = [("contains_unverified_day", _B), ("unverified_day_count", _I32), ("entry_on_unverified_day", _B)]
WINDOW_STATS_SCHEMA = _schema(
    *_KEY, ("exit_row", _I32), ("entry_row", _I32), *_SCHEDULED, *_FLAGS,
    ("entry_price_date", _D), ("entry_price", _F), ("exit_price_date", _D), ("exit_price", _F),
    ("n_member_rows", _I64), ("n_member_dates", _I64), ("min_date", _D), ("max_date", _D), ("n_valid_returns", _I64),
    ("n_gap_terms_valid", _I64), ("realized_variance", _F), ("sum_abs_return", _F), ("max_abs_return", _F),
    ("exact_gap", _F), ("price_return", _F))
PATH_DAYS_SCHEMA = _schema(                 # as stored in each ticker=<ticker> folder, without the ticker
    ("window_kind", _S), ("window_days", _I32), ("entry_date", _D), ("leverage", _F), ("day", _I32), ("date", _D),
    ("daily_return", _F), ("nav_start", _F), ("nav", _F), ("exposure_before", _F), ("exposure_target", _F),
    ("rebalance", _F), ("running_peak", _F), ("drawdown", _F), ("status", _S))
PATH_SUMMARY_SCHEMA = _schema(
    *_KEY, ("leverage", _F), ("n_rows", _I64), ("n_distinct_days", _I64), ("max_day", _I32), ("days_ok", _I64),
    ("breached", _B), ("n_breach_rows", _I64), ("breach_day", _I32), ("breach_date", _D), ("last_ok_date", _D),
    ("n_valid_nav", _I64), ("n_valid_drawdown", _I64), ("n_turnover_days", _I64), ("n_valid_rebalance", _I64),
    ("final_nav", _F), ("max_drawdown", _F), ("mean_turnover", _F), ("max_turnover", _F), ("total_turnover", _F),
    ("max_turnover_date", _D), ("total_abs_rebalance", _F), ("max_abs_rebalance", _F), ("total_return", _F),
    *_SCHEDULED, ("stride", _I32), ("calendar_year", _I32), *_FLAGS)
PAIRED_SCHEMA = _schema(
    *_KEY, ("n_paths", _I64), ("n_leverages", _I64), ("return_1x", _F), ("return_2x", _F), ("mdd_1x", _F),
    ("breached_1x", _B), ("breached_2x", _B), ("breach_date_2x", _D), ("breach_day_2x", _I32), ("last_ok_date_2x", _D),
    ("days_ok_2x", _I64), ("n_turnover_days_2x", _I64), *_SCHEDULED, *_FLAGS, ("realized_variance", _F),
    ("sum_abs_return", _F), ("max_abs_return", _F), ("price_return", _F),
    *[(f"{name}{suffix}", _F) for name in PAIRED_2X_PATH_VALUES for suffix in ("", "_pre_breach")],
    ("exact_gap", _F), ("log_gap", _F), ("approx_gap", _F), ("approx_rel_error", _F), ("mdd_bound", _F))
PATH_DAY_COLUMNS = ["window_kind", "ticker", "window_days", "entry_date", *PATH_DAYS_SCHEMA.names[3:]]


# --- reading and writing ---------------------------------------------------------

def read_parquet(path: Path | str) -> pd.DataFrame:
    """A file or folder of Parquet files; dates become datetime64[ns]."""
    df = pq.read_table(path).to_pandas(date_as_object=False)
    for name in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[name]):
            df[name] = df[name].astype("datetime64[ns]")
    return df


def read_inputs(windows_dir: Path, config: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The window definitions and every return file named in the config, as the Spark pipeline reads them."""
    defs = read_parquet(windows_dir / config["windows_file"])
    files = [resolve(config["snapshot_dir"]) / rel for rel in config["inputs_sha256"] if rel.startswith("daily_returns/")]
    return defs, pd.concat([read_parquet(f) for f in files], ignore_index=True)


def to_table(df: pd.DataFrame, schema: pa.Schema) -> pa.Table:
    """The frame's columns with exactly the schema's types; missing values (None, NaN, NaT) become nulls."""
    arrays = []
    for field in schema:
        s = df[field.name]
        if pa.types.is_date32(field.type):
            days = pd.to_datetime(s).to_numpy(dtype="datetime64[ns]").astype("datetime64[D]")
            arr = pa.array(days, type=_D, from_pandas=True)
        elif pa.types.is_integer(field.type):
            arr = pa.array(pd.array(s, dtype="Int64"), type=_I64).cast(field.type)
        elif pa.types.is_boolean(field.type):
            arr = pa.array(pd.array(s, dtype="boolean"), type=_B)
        elif pa.types.is_floating(field.type):
            arr = pa.array(pd.to_numeric(s).to_numpy(dtype=float, na_value=np.nan), type=_F, from_pandas=True)
        else:
            arr = pa.array(s.astype(object).where(s.notna(), None), type=field.type)
        arrays.append(arr)
    return pa.Table.from_arrays(arrays, schema=schema)


def write_table(df: pd.DataFrame, schema: pa.Schema, folder: Path) -> None:
    folder.mkdir(parents=True)
    pq.write_table(to_table(df, schema), folder / "part-00000.parquet")


def write_path_days(path_days: pd.DataFrame, folder: Path) -> None:
    """One ticker=<ticker> folder per ticker, as the Spark pipeline's partitionBy("ticker") writes."""
    folder.mkdir(parents=True)
    for ticker, part in path_days.groupby("ticker", sort=True):
        write_table(part, PATH_DAYS_SCHEMA, folder / f"ticker={ticker}")


# --- SQL null semantics for the checks -------------------------------------------

def _int(s: pd.Series) -> pd.Series:
    return s.astype("Int64")


def _float(s: pd.Series) -> pd.Series:
    return pd.Series(pd.array(pd.to_numeric(s).to_numpy(dtype=float, na_value=np.nan), dtype="Float64"), index=s.index)


def _bool(s: pd.Series) -> pd.Series:
    return pd.Series(pd.array(s, dtype="boolean"), index=s.index)


def _isnan(s: pd.Series) -> pd.Series:
    """True for a NaN that is not a null (a stored NaN; Float64 keeps the two apart)."""
    values = s.to_numpy(dtype=float, na_value=np.nan)
    return pd.Series(np.isnan(values) & s.notna().to_numpy(), index=s.index)


def _eq_null_safe(a: pd.Series, b: pd.Series) -> pd.Series:
    """SQL's <=>: true when both are null or both are set and equal."""
    both_null = a.isna() & b.isna()
    return both_null | (a.notna() & b.notna() & (a == b))


def _violations(checks: dict[str, pd.Series]) -> dict[str, int]:
    """Rows where each condition is true; a null condition is not a violation (SQL's WHEN)."""
    return {name: int(pd.Series(cond).fillna(False).astype(bool).sum()) for name, cond in checks.items()}


# --- building blocks -------------------------------------------------------------

def returns_with_rows(returns: pd.DataFrame) -> pd.DataFrame:
    """Sorted by ticker and date, with `row` per ticker (0 = first price)."""
    rows = returns.sort_values(["ticker", "date"], kind="mergesort", ignore_index=True)
    rows["row"] = rows.groupby("ticker", sort=False).cumcount()
    return rows


def _ticker_lookup(rows: pd.DataFrame, tickers: np.ndarray, row: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """For each (ticker, row): whether that row exists, and its position in `rows`."""
    counts = rows.groupby("ticker", sort=False).size()
    first = counts.cumsum() - counts                         # position of each ticker's row 0
    size = counts.reindex(tickers).to_numpy(dtype=float)     # NaN for a ticker without returns
    start = first.reindex(tickers).to_numpy(dtype=float)
    exists = (row >= 0) & (row < size)
    return exists, np.where(exists, start + row, 0).astype(np.int64)


def window_ids(defs: pd.DataFrame) -> np.ndarray:
    """One id per distinct window key: rows are grouped by key values, as Spark's groupBy(window key) does."""
    return defs.groupby(WINDOW_KEY, sort=False, dropna=False).ngroup().to_numpy()


def window_members(defs: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Each definition's member rows with their date and return; `_w` is the window's id (window_ids)."""
    n = defs["window_days"].to_numpy(dtype=np.int64)
    which = np.repeat(np.arange(len(defs)), n)
    within = np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)
    member_row = defs["entry_row"].to_numpy(dtype=np.int64)[which] + 1 + within
    exists, pos = _ticker_lookup(rows, defs["ticker"].to_numpy()[which], member_row)
    which, member_row, pos = which[exists], member_row[exists], pos[exists]
    members = defs[WINDOW_KEY].iloc[which].reset_index(drop=True)
    members["_w"] = window_ids(defs)[which]
    members["row"] = member_row
    members["date"] = rows["date"].to_numpy()[pos]
    members["daily_return"] = rows["daily_return"].to_numpy(dtype=float)[pos]
    return members


def window_stats(members: pd.DataFrame, defs: pd.DataFrame, rows: pd.DataFrame) -> pd.DataFrame:
    """Per window, from returns and prices only. Count-guarded: null unless every term was valid."""
    ids = window_ids(defs)
    n_windows = int(ids.max()) + 1 if len(ids) else 0
    w = members["_w"].to_numpy()
    r = members["daily_return"].to_numpy(dtype=float)
    valid = ~np.isnan(r)
    gap_ok = valid & (1 + 2 * r > 0)                 # then (r/(1+r))^2 < 1, so the log is defined
    gap_terms = np.zeros_like(r)
    gap_terms[gap_ok] = np.log1p(-(r[gap_ok] / (1 + r[gap_ok])) ** 2)
    by = pd.Series(w)
    per = pd.DataFrame(index=pd.RangeIndex(n_windows))
    per["n_member_rows"] = np.bincount(w, minlength=n_windows)
    per["n_member_dates"] = pd.Series(members["date"].to_numpy()).groupby(by).nunique()
    per["min_date"] = pd.Series(members["date"].to_numpy()).groupby(by).min()
    per["max_date"] = pd.Series(members["date"].to_numpy()).groupby(by).max()
    per["n_valid_returns"] = np.bincount(w, weights=valid, minlength=n_windows)
    per["_sum_sq"] = np.bincount(w, weights=np.where(valid, r * r, 0.0), minlength=n_windows)
    per["_sum_abs"] = np.bincount(w, weights=np.where(valid, np.abs(r), 0.0), minlength=n_windows)
    per["_max_abs"] = pd.Series(np.where(valid, np.abs(r), np.nan)).groupby(by).max()
    per["n_gap_terms_valid"] = np.bincount(w, weights=gap_ok, minlength=n_windows)
    per["_exact_gap"] = np.bincount(w, weights=gap_terms, minlength=n_windows)
    per = per.where(per["n_member_rows"] > 0, axis=0)   # no member row: no aggregate row (the left join's nulls)
    complete = per["n_valid_returns"] == defs_window_days(defs, n_windows, ids)
    gap_complete = per["n_gap_terms_valid"] == defs_window_days(defs, n_windows, ids)
    per["realized_variance"] = per["_sum_sq"].where(complete)
    per["sum_abs_return"] = per["_sum_abs"].where(complete)
    per["max_abs_return"] = per["_max_abs"].where(complete)
    per["exact_gap"] = per["_exact_gap"].where(gap_complete)

    d = defs[[*WINDOW_KEY, "entry_row", "first_return_date", "exit_date", "contains_unverified_day",
              "unverified_day_count", "entry_on_unverified_day"]].reset_index(drop=True)
    d["exit_row"] = d["entry_row"] + d["window_days"]
    tickers = d["ticker"].to_numpy()
    for side, row_col in (("entry", "entry_row"), ("exit", "exit_row")):
        exists, pos = _ticker_lookup(rows, tickers, d[row_col].to_numpy(dtype=np.int64))
        d[f"{side}_price_date"] = pd.Series(rows["date"].to_numpy()[pos]).where(exists)
        d[f"{side}_price"] = pd.Series(rows["adjusted_price"].to_numpy(dtype=float)[pos]).where(exists)
    agg = per.iloc[ids].reset_index(drop=True)
    for name in ("n_member_rows", "n_member_dates", "min_date", "max_date", "n_valid_returns", "n_gap_terms_valid",
                 "realized_variance", "sum_abs_return", "max_abs_return", "exact_gap"):
        d[name] = agg[name]
    d["price_return"] = d["exit_price"] / d["entry_price"] - 1.0
    return d[WINDOW_STATS_SCHEMA.names]


def defs_window_days(defs: pd.DataFrame, n_windows: int, ids: np.ndarray) -> pd.Series:
    """window_days per window id (equal for every definition of a key, which includes window_days)."""
    out = np.zeros(n_windows, dtype=np.int64)
    out[ids] = defs["window_days"].to_numpy(dtype=np.int64)
    return pd.Series(out)


def construction_checks(stats: pd.DataFrame) -> dict[str, int]:
    wd = _int(stats["window_days"])
    n_rows, n_dates = _int(stats["n_member_rows"]), _int(stats["n_member_dates"])
    return _violations({
        "member_rows_not_window_days": n_rows.isna() | (n_rows != wd) | (n_dates != wd),
        "first_or_last_date_mismatch": ~_eq_null_safe(stats["min_date"], stats["first_return_date"])
                                       | ~_eq_null_safe(stats["max_date"], stats["exit_date"]),
        "entry_or_exit_price_date_mismatch": ~_eq_null_safe(stats["entry_price_date"], stats["entry_date"])
                                             | ~_eq_null_safe(stats["exit_price_date"], stats["exit_date"]),
        "missing_entry_or_exit_price": stats["entry_price"].isna() | stats["exit_price"].isna(),
    })


def simulate_window(pdf: pd.DataFrame, leverages: Sequence[float], initial_nav: float) -> pd.DataFrame:
    """The body of the Spark pipeline's grouped pandas function, for one window."""
    pdf = pdf.sort_values("date", kind="mergesort")
    key = {k: pdf[k].iloc[0] for k in WINDOW_KEY}
    if len(pdf) != int(key["window_days"]) or pdf["date"].duplicated().any():
        raise ValueError(f"incomplete window {key}: {len(pdf)} rows for {key['window_days']} days")
    dates, returns = pdf["date"].to_numpy(), pdf["daily_return"].to_numpy()
    out = []
    for lev in leverages:
        path = simulate_path(returns, lev, initial_nav)
        for k, v in key.items():
            path[k] = v
        path["leverage"] = lev
        path["date"] = dates[path["day"].to_numpy() - 1]
        out.append(path)
    return pd.concat(out, ignore_index=True)[PATH_DAY_COLUMNS]


def simulate_windows(members: pd.DataFrame, leverages: Sequence[float] = LEVERAGES,
                     initial_nav: float = INITIAL_NAV) -> pd.DataFrame:
    levs = [float(x) for x in leverages]
    parts = [simulate_window(pdf, levs, initial_nav) for _, pdf in members.groupby("_w", sort=False)]
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=PATH_DAY_COLUMNS)


def summarize_paths(path_days: pd.DataFrame, defs: pd.DataFrame, initial_nav: float = INITIAL_NAV) -> pd.DataFrame:
    ok, breach = path_days["status"].eq(STATUS_OK), path_days["status"].eq(STATUS_BREACH)
    nav, drawdown, rebalance = (pd.to_numeric(path_days[c]).astype(float) for c in ("nav", "drawdown", "rebalance"))
    turnover = rebalance.abs() / pd.to_numeric(path_days["nav_start"]).astype(float)   # of that day's starting NAV
    f = path_days[PATH_KEY].copy()
    f["day"], f["date"], f["ok"], f["breach"] = path_days["day"], path_days["date"], ok, breach
    f["breach_day_"] = path_days["day"].where(breach)
    f["breach_date_"] = path_days["date"].where(breach)
    f["ok_date"] = path_days["date"].where(ok)
    f["v_nav"] = nav.where(ok & nav.notna())
    f["v_drawdown"] = drawdown.where(ok & drawdown.notna())
    f["v_turnover"] = turnover.where(ok & turnover.notna())
    f["v_rebalance"] = rebalance.abs().where(ok & rebalance.notna())
    g = f.groupby(PATH_KEY, sort=False, dropna=False)
    s = g.agg(n_rows=("day", "size"), n_distinct_days=("day", "nunique"), max_day=("day", "max"),
              days_ok=("ok", "sum"), breached=("breach", "any"), n_breach_rows=("breach", "sum"),
              breach_day=("breach_day_", "min"), breach_date=("breach_date_", "min"), last_ok_date=("ok_date", "max"),
              n_valid_nav=("v_nav", "count"), _max_drawdown=("v_drawdown", "max"),
              n_valid_drawdown=("v_drawdown", "count"), _mean_turnover=("v_turnover", "mean"),
              _max_turnover=("v_turnover", "max"), _total_turnover=("v_turnover", "sum"),
              n_turnover_days=("v_turnover", "count"), _total_abs_rebalance=("v_rebalance", "sum"),
              _max_abs_rebalance=("v_rebalance", "max"), n_valid_rebalance=("v_rebalance", "count"))
    # the nav of the last ok day (max_by), and the earliest date with the largest turnover
    ok_rows = f[ok]
    last_ok = ok_rows.loc[ok_rows.groupby(PATH_KEY, sort=False, dropna=False)["day"].idxmax()]
    s["_last_ok_nav"] = last_ok.set_index(PATH_KEY)["v_nav"]
    largest = f["v_turnover"].eq(g["v_turnover"].transform("max"))
    s["_max_turnover_date"] = f[largest].groupby(PATH_KEY, sort=False, dropna=False)["date"].min()
    s = s.reset_index()

    final_ok = ~s["breached"] & (s["n_valid_nav"] == s["days_ok"]) & (s["days_ok"] == s["window_days"])
    drawdown_ok = s["n_valid_drawdown"] == s["days_ok"]
    turnover_ok = (s["n_turnover_days"] == s["days_ok"]) & (s["days_ok"] > 0)
    rebalance_ok = s["n_valid_rebalance"] == s["days_ok"]
    s["final_nav"] = s["_last_ok_nav"].where(final_ok)
    s["max_drawdown"] = s["_max_drawdown"].fillna(0.0).where(drawdown_ok)    # the starting NAV is a peak candidate
    s["mean_turnover"] = s["_mean_turnover"].where(turnover_ok)
    s["max_turnover"] = s["_max_turnover"].where(turnover_ok)
    s["total_turnover"] = s["_total_turnover"].where(turnover_ok)
    s["max_turnover_date"] = s["_max_turnover_date"].where(turnover_ok & (s["_max_turnover"] > 0))
    s["total_abs_rebalance"] = s["_total_abs_rebalance"].fillna(0.0).where(rebalance_ok)
    s["max_abs_rebalance"] = s["_max_abs_rebalance"].fillna(0.0).where(rebalance_ok)
    s["total_return"] = s["final_nav"] / initial_nav - 1.0
    scheduled = defs[[*WINDOW_KEY, "first_return_date", "exit_date", "stride", "calendar_year",
                      "contains_unverified_day", "unverified_day_count", "entry_on_unverified_day"]]
    return s.merge(scheduled, on=WINDOW_KEY, how="left")[PATH_SUMMARY_SCHEMA.names]


def pair_paths(summary: pd.DataFrame, stats: pd.DataFrame, leverages: Sequence[float] = LEVERAGES) -> pd.DataFrame:
    """One row per window, 1x and 2x side by side; as the Spark pipeline's PAIR_SQL and pair_paths."""
    if tuple(float(x) for x in leverages) != (1.0, 2.0):
        raise ValueError(f"pairing compares 1x with 2x; got leverages {tuple(leverages)}")
    by_key = summary.groupby(WINDOW_KEY, sort=False, dropna=False)
    p = by_key.agg(n_paths=("leverage", "size"), n_leverages=("leverage", "nunique"))
    one = summary[summary["leverage"] == 1.0].groupby(WINDOW_KEY, sort=False, dropna=False).agg(
        return_1x=("total_return", "max"), mdd_1x=("max_drawdown", "max"), breached_1x=("breached", "any"))
    two = summary[summary["leverage"] == 2.0].groupby(WINDOW_KEY, sort=False, dropna=False).agg(
        return_2x=("total_return", "max"), _mdd_2x=("max_drawdown", "max"), breached_2x=("breached", "any"),
        breach_date_2x=("breach_date", "max"), breach_day_2x=("breach_day", "max"),
        last_ok_date_2x=("last_ok_date", "max"), days_ok_2x=("days_ok", "max"),
        _mean_turnover_2x=("mean_turnover", "max"), _max_turnover_2x=("max_turnover", "max"),
        _total_turnover_2x=("total_turnover", "max"), n_turnover_days_2x=("n_turnover_days", "max"))
    p = p.join(one).join(two).reset_index()
    s = stats[[*WINDOW_KEY, "first_return_date", "exit_date", "contains_unverified_day", "unverified_day_count",
               "entry_on_unverified_day", "realized_variance", "sum_abs_return", "max_abs_return", "price_return",
               "exact_gap"]].rename(columns={"exact_gap": "_exact_gap"})
    p = p.merge(s, on=WINDOW_KEY, how="left")
    breached = _bool(p["breached_2x"])
    when_breached, when_not = breached.fillna(False).astype(bool), (~breached).fillna(False).astype(bool)
    for name in PAIRED_2X_PATH_VALUES:
        p[name] = p[f"_{name}"].where(when_not)
        p[f"{name}_pre_breach"] = p[f"_{name}"].where(when_breached)
    r1, r2 = p["return_1x"].astype(float), p["return_2x"].astype(float)
    p["exact_gap"] = p["_exact_gap"].where(when_not)
    p["log_gap"] = (_log1p(r2) - 2 * _log1p(r1)).where(when_not & r1.notna() & r2.notna())
    p["approx_gap"] = -p["realized_variance"]
    gap = p["exact_gap"].astype(float)
    p["approx_rel_error"] = ((p["approx_gap"] - gap) / gap.abs()).where(
        gap.notna() & p["realized_variance"].notna() & (gap.abs() > 0))
    mdd_1x = p["mdd_1x"].astype(float)
    p["mdd_bound"] = (1 - (1 - mdd_1x) ** 2).where(when_not & mdd_1x.notna())
    return p[PAIRED_SCHEMA.names]


def _log1p(x: pd.Series) -> pd.Series:
    """Spark's log1p: null at or below -1, where the logarithm is not defined."""
    values = x.to_numpy(dtype=float)
    out = np.full_like(values, np.nan)
    defined = values > -1
    out[defined] = np.log1p(values[defined])
    return pd.Series(out, index=x.index)


# --- checks ----------------------------------------------------------------------

def run_checks(stats: pd.DataFrame, path_days: pd.DataFrame, summary: pd.DataFrame, paired: pd.DataFrame,
               defs: pd.DataFrame, leverages: Sequence[float] = LEVERAGES) -> dict[str, dict]:
    """The Spark pipeline's ten checks, with the same names, conditions and tolerances."""
    n_lev = len(leverages)
    results = {"window_construction": construction_checks(stats)}
    breached = _bool(summary["breached"])
    n_rows, wd = _int(summary["n_rows"]), _int(summary["window_days"])
    results["complete_paths"] = _violations({
        "rows_not_window_days_or_breach_day": (~breached & (n_rows != wd))
                                              | (breached & ~_eq_null_safe(n_rows, _int(summary["breach_day"]))),
        "days_not_numbered_1_to_rows": (_int(summary["max_day"]) != n_rows) | (_int(summary["n_distinct_days"]) != n_rows),
        "days_ok_inconsistent": _int(summary["days_ok"]) != n_rows - breached.astype("Int64"),
        "more_than_one_breach_row": _int(summary["n_breach_rows"]) > 1,
    })
    defined = pd.MultiIndex.from_frame(defs[WINDOW_KEY])
    paired_keys = pd.MultiIndex.from_frame(paired[WINDOW_KEY])
    results["pairing"] = {
        **_violations({"not_one_row_per_leverage": (_int(paired["n_paths"]) != n_lev) | (_int(paired["n_leverages"]) != n_lev)}),
        "definitions_without_paired_row": int((~defined.isin(paired_keys)).sum()),
        "paired_rows_without_definition": int((~paired_keys.isin(defined)).sum()),
    }
    b2 = _bool(paired["breached_2x"])
    r1, price_return = _float(paired["return_1x"]), _float(paired["price_return"])
    log_gap, exact_gap = _float(paired["log_gap"]), _float(paired["exact_gap"])
    mdd_2x, mdd_bound = _float(paired["mdd_2x"]), _float(paired["mdd_bound"])
    results["one_x_identity"] = _violations({
        "return_1x_differs_from_price_return": r1.isna() | price_return.isna()
        | ((r1 - price_return).abs() > ATOL + RTOL * price_return.abs()),
    })
    results["exact_log_gap"] = _violations({
        "log_gap_differs_from_exact_gap": ~b2 & (log_gap.isna() | exact_gap.isna() | ((log_gap - exact_gap).abs() > GAP_ATOL)),
    })
    results["drawdown_bound"] = _violations({
        "mdd_2x_below_bound": ~b2 & (mdd_2x.isna() | mdd_bound.isna() | (mdd_2x < mdd_bound - BOUND_TOL)),
    })
    nav, ok = _float(path_days["nav"]), path_days["status"].eq(STATUS_OK)
    leverage, rebalance = _float(path_days["leverage"]), _float(path_days["rebalance"])
    expected_turnover = leverage * (leverage - 1) * _float(path_days["daily_return"]).abs()
    turnover = rebalance.abs() / _float(path_days["nav_start"])
    results["nav_sanity"] = _violations({
        "negative_nav": nav < 0,
        "nan_nav_outside_breach_rows": _isnan(nav) & path_days["status"].ne(STATUS_BREACH),
        "ok_row_without_valid_nav": ok & (nav.isna() | _isnan(nav)),
    })
    results["turnover_identity"] = _violations({
        "turnover_differs_from_L(L-1)|r|": ok & (turnover.isna() | _isnan(turnover)
                                               | ((turnover - expected_turnover).abs() > ATOL + RTOL * expected_turnover)),
        "nonzero_turnover_at_1x": ok & (leverage == 1.0) & (rebalance.abs() != 0),
    })
    results["breach_flagged_unverified"] = _violations({
        "breached_window_not_flagged": b2 & ~_bool(paired["contains_unverified_day"]),
    })
    results["null_rule"] = null_rule_checks(stats, summary, paired)
    return results


def _null_iff(column: pd.Series, should_be_null: pd.Series) -> pd.Series:
    """Violation: the column is null when it should be set, or set when it should be null (both directions)."""
    return column.isna() != _bool(should_be_null).fillna(True).astype(bool)


def null_rule_checks(stats: pd.DataFrame, summary: pd.DataFrame, paired: pd.DataFrame) -> dict[str, int]:
    """Check 10: every count-guarded value is null exactly when its count of valid terms is short."""
    wd = _int(stats["window_days"])
    returns_short = _int(stats["n_valid_returns"]) != wd
    gap_short = _int(stats["n_gap_terms_valid"]) != wd
    s = summary
    days_ok = _int(s["days_ok"])
    final_ok = ~_bool(s["breached"]) & (_int(s["n_valid_nav"]) == days_ok) & (days_ok == _int(s["window_days"]))
    drawdown_ok = _int(s["n_valid_drawdown"]) == days_ok
    turnover_ok = (_int(s["n_turnover_days"]) == days_ok) & (days_ok > 0)
    rebalance_ok = _int(s["n_valid_rebalance"]) == days_ok
    breached = _bool(paired["breached_2x"])
    exact_gap = _float(paired["exact_gap"])
    return {
        **_violations({
            "window_stats.realized_variance": _null_iff(stats["realized_variance"], returns_short),
            "window_stats.sum_abs_return": _null_iff(stats["sum_abs_return"], returns_short),
            "window_stats.max_abs_return": _null_iff(stats["max_abs_return"], returns_short),
            "window_stats.exact_gap": _null_iff(stats["exact_gap"], gap_short),
        }),
        **_violations({
            "path_summary.final_nav": _null_iff(s["final_nav"], ~final_ok),
            "path_summary.total_return": _null_iff(s["total_return"], ~final_ok),
            "path_summary.max_drawdown": _null_iff(s["max_drawdown"], ~drawdown_ok),
            "path_summary.mean_turnover": _null_iff(s["mean_turnover"], ~turnover_ok),
            "path_summary.max_turnover": _null_iff(s["max_turnover"], ~turnover_ok),
            "path_summary.total_turnover": _null_iff(s["total_turnover"], ~turnover_ok),
            "path_summary.max_turnover_date": _null_iff(s["max_turnover_date"],
                                                        ~(turnover_ok & (_float(s["max_turnover"]) > 0))),
            "path_summary.total_abs_rebalance": _null_iff(s["total_abs_rebalance"], ~rebalance_ok),
            "path_summary.max_abs_rebalance": _null_iff(s["max_abs_rebalance"], ~rebalance_ok),
        }),
        **_violations({
            # in a 2x window without a breach every gap term is valid, so these are set exactly when not breached
            "paired.exact_gap": _null_iff(paired["exact_gap"], breached),
            "paired.log_gap": _null_iff(paired["log_gap"], breached),
            "paired.return_2x": _null_iff(paired["return_2x"], breached),
            "paired.mdd_bound": _null_iff(paired["mdd_bound"], breached),
            "paired.approx_rel_error": _null_iff(paired["approx_rel_error"], breached | (exact_gap.abs() == 0)),
            "paired.mdd_2x": _null_iff(paired["mdd_2x"], breached),
            "paired.mdd_2x_pre_breach": _null_iff(paired["mdd_2x_pre_breach"], ~breached),
            **{f"paired.{name}": _null_iff(paired[name], breached) for name in PAIRED_2X_PATH_VALUES[1:]},
            # no pre-breach turnover exists when the breach is on day 1 (no day before it)
            **{f"paired.{name}_pre_breach": _null_iff(paired[f"{name}_pre_breach"], ~breached | (_int(paired["days_ok_2x"]) == 0))
               for name in PAIRED_2X_PATH_VALUES[1:]},
        }),
    }


def total_violations(checks: dict[str, dict]) -> int:
    return sum(v for group in checks.values() for v in group.values())


# --- whole run -------------------------------------------------------------------

def compute(defs: pd.DataFrame, returns: pd.DataFrame, leverages: Sequence[float] = LEVERAGES,
            initial_nav: float = INITIAL_NAV, out_dir: Path | None = None, timings: dict | None = None) -> dict:
    """Run everything in the Spark pipeline's phases. With out_dir, each table is written once."""
    timings = {} if timings is None else timings

    t = time.perf_counter()
    rows = returns_with_rows(returns)
    members = window_members(defs, rows)
    stats = window_stats(members, defs, rows)
    if out_dir is not None:
        write_table(stats, WINDOW_STATS_SCHEMA, out_dir / "window_stats")
    construction = construction_checks(stats)
    timings["window_stats_and_construction_check"] = time.perf_counter() - t
    if sum(construction.values()):
        return {"checks": {"window_construction": construction}, "model_run": False, "stats": stats}

    t = time.perf_counter()
    path_days = simulate_windows(members, leverages, initial_nav)
    if out_dir is not None:
        write_path_days(path_days, out_dir / "path_days")
    timings["model_and_path_days"] = time.perf_counter() - t

    t = time.perf_counter()
    summary = summarize_paths(path_days, defs, initial_nav)
    paired = pair_paths(summary, stats, leverages)
    if out_dir is not None:
        write_table(summary, PATH_SUMMARY_SCHEMA, out_dir / "path_summary")
        write_table(paired, PAIRED_SCHEMA, out_dir / "paired")
    timings["summaries_and_pairing"] = time.perf_counter() - t

    t = time.perf_counter()
    checks = run_checks(stats, path_days, summary, paired, defs, leverages)
    timings["checks"] = time.perf_counter() - t
    return {"checks": checks, "model_run": True, "stats": stats, "path_days": path_days, "summary": summary, "paired": paired}


def environment() -> dict:
    """The Spark pipeline's environment record, so that the two engines' records can be compared."""
    env = {
        "platform": platform.platform(), "macos": platform.mac_ver()[0] or None, "machine": platform.machine(),
        "cpu_count": os.cpu_count(), "python": platform.python_version(),
        "packages": {p: _version(p) for p in ("pyspark", "pandas", "numpy", "pyarrow", "pandas_market_calendars", "psutil")},
    }
    try:
        java = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
        env["java"] = (java.stderr or java.stdout).splitlines()[0]
    except (OSError, subprocess.SubprocessError, IndexError):
        env["java"] = "unknown"
    try:
        import psutil
        env["ram_total_bytes"] = psutil.virtual_memory().total
    except ImportError:
        env["ram_total_bytes"] = None
    return env


def _version(package: str) -> str | None:
    try:
        return package_version(package)
    except Exception:
        return None


def run_dir_for(windows_dir: Path, out_root: Path, run_id: str) -> Path:
    config = json.loads((windows_dir / "config.json").read_text())
    return out_root / config["snapshot"] / windows_dir.name / run_id


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--windows", type=Path, required=True, help="window-definition folder from etf_risk.windows")
    parser.add_argument("--out-root", type=Path, default=Path("data/outputs/windows"))
    parser.add_argument("--run-id", default=None, help="default: run-<UTC time>")
    parser.add_argument("--initial-nav", type=float, default=INITIAL_NAV)
    return parser


def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    args = build_parser().parse_args(argv)
    run_id = args.run_id or "run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        config, verified = verify_checksums(args.windows)
    except (ChecksumError, FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"checksum verification failed, nothing computed:\n{exc}", file=sys.stderr)
        return 3
    run_dir = run_dir_for(args.windows, args.out_root, run_id)
    if run_dir.exists():
        print(f"{run_dir} exists; use a new --run-id", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True)
    record = {
        "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(), "engine": "pandas",
        "code": code_state(), "windows_dir": str(args.windows),
        "windows_config": config, "verified_sha256": verified, "leverages": list(LEVERAGES),
        "initial_nav": args.initial_nav, "environment": environment(), "status": "running",
    }
    timings: dict[str, float] = {}
    status, code = "failed", 2
    try:
        t = time.perf_counter()
        defs, returns = read_inputs(args.windows, config)
        read_seconds = time.perf_counter() - t
        results = compute(defs, returns, LEVERAGES, args.initial_nav, out_dir=run_dir, timings=timings)
        timings["window_stats_and_construction_check"] += read_seconds   # where the Spark pipeline reads them
        checks = results["checks"]
        (run_dir / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
        record["checks"] = checks
        record["model_run"] = results["model_run"]
        record["row_counts"] = {"windows": len(defs), "window_stats": len(results["stats"])}
        if results["model_run"]:
            record["row_counts"].update({name: len(results[name]) for name in ("path_days", "summary", "paired")})
        status, code = ("ok", 0) if total_violations(checks) == 0 else ("checks_failed", 1)
    except Exception as exc:
        record["error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-4000:]
    finally:
        timings["total_in_process"] = time.perf_counter() - started
        record.update({"status": status, "timings_seconds": timings, "finished_at_utc": datetime.now(timezone.utc).isoformat()})
        (run_dir / "run.json").write_text(json.dumps(record, indent=2, default=str) + "\n")
    print(f"{run_id}: {status}  ({record.get('row_counts', {})})  -> {run_dir}")
    for group, violations in record.get("checks", {}).items():
        bad = {k: v for k, v in violations.items() if v}
        print(f"  {group}: {'ok' if not bad else bad}")
    if "error" in record:
        print("  error:", record["error"].splitlines()[-1], file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
