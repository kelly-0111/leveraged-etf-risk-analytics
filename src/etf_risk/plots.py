"""Figures for the final write-up (Stage 4, docs/spec.md §4), drawn from result files only.

Run from the repository root (the plotting library is in the "plots" dependency group):

    uv run --group plots python -m etf_risk.plots
    uv run --group plots python -m etf_risk.plots --check
    uv run --group plots python -m etf_risk.plots --check --figures X1 X2 X3 X4

The first writes every figure and figures.json into docs/figures/. --check computes each figure's
checked numbers, compares them with the values the documents report (DOCUMENTED, for the figures
whose inputs are the documented ones) and draws nothing. --figures selects figures; a selection is
drawn only into another folder, given with --out. Every figure reads finished result files (Parquet,
JSON, CSV) and recomputes nothing in Spark:

  M1-M5  the run of record, rolling-252-s21-r2, run-20261013T043848Z-2 (the protocol's four runs
         have identical tables): one panel per ticker, QQQ never pooled with the four stocks it
         holds, the overlapping windows labeled as such, windows that use an unverified extreme day
         marked, and the windows whose 2x path was breached shown on their own (M5)
  S1     the same run, over all windows and over the windows without an unverified day
  D1-D2  the data snapshot's daily returns and the run's window definitions
  X1-X4  the stride, shuffle-partition and caching experiments and the pandas baseline, from the
         reviewed copies of their measurements CSVs in docs/measurements/, which are committed, so
         these four also work from a fresh clone: each with its own time metric (wall_s, or
         wall_excl_capture_s where plans were recorded), its measured runs only, and its documented
         caveats in the note

Nothing is skipped silently. An input that a selected figure needs is unusable if it is missing, if a
CSV, JSON or Parquet part of it cannot be parsed, if it lacks a column or field that the figures read,
or, for a run, if the run did not end with status ok. The command then names each such input and what
is wrong, computes nothing and writes nothing (exit 2). Values inside the inputs are not validated: an
unexpected one, such as a configuration label that a figure does not know, ends in an error, and since
every figure is drawn in memory before any file is written, the output folder stays as it was.
Otherwise the command reports which figures it compared with the documented values and which it did
not, because their inputs are other ones. It exits with 1 if a value differs; --check exits with 0
only if every selected figure was compared and matches, and with 3 if one was not compared. With the
default measurements it also compares each copy with the collector's output under data/, and names
the outputs that are absent.

Regenerating in the same fixed environment (this lockfile's packages, among them matplotlib and its
bundled DejaVu fonts, on the same platform) gives byte-identical files: the Agg backend, a fixed font,
size and DPI, no date or software metadata, and a manifest without timestamps. Another environment
may render the PNGs differently.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_plots.py and, on the
real data, by --check against the values in docs/spec.md §8, data-sources.md and the experiment documents.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")                          # no display: the same renderer on every machine
import matplotlib.pyplot as plt                # noqa: E402
import numpy as np                             # noqa: E402
import pandas as pd                            # noqa: E402
import pyarrow as pa                           # noqa: E402
import pyarrow.parquet as pq                   # noqa: E402
from matplotlib.lines import Line2D             # noqa: E402
from matplotlib.ticker import PercentFormatter  # noqa: E402

from etf_risk.provenance import REPO_ROOT, resolve  # noqa: E402

SNAPSHOT = "full-2026-10-12"
DEFAULT_RUN = Path(f"data/outputs/windows/{SNAPSHOT}/rolling-252-s21-r2/run-20261013T043848Z-2")
DEFAULT_SNAPSHOT = Path(f"data/processed/{SNAPSHOT}")
DEFAULT_WINDOWS = Path(f"data/windows/{SNAPSHOT}/rolling-252-s21-r2")
DEFAULT_OUT = Path("docs/figures")
DEFAULT_MEASUREMENTS = Path("docs/measurements")
MEASUREMENT_CSVS = {   # input name -> (reviewed copy in the measurements folder, the collector's output it copies)
    "stride_csv": ("stride-experiment.csv", Path("data/outputs-experiments/measurements.csv")),
    "partitions_csv": ("shuffle-partition-experiment.csv", Path("data/outputs-partitions/batch-1/measurements.csv")),
    "baseline_csv": ("pandas-baseline.csv", Path("data/outputs-baseline/batch-1/measurements.csv")),
    "caching_csv": ("caching-experiment.csv", Path("data/outputs-caching/batch-1/measurements.csv")),
}
FOLDER_PARTS = {   # what each folder input must hold, its JSON record first; a run must also have ended ok
    "run": ("run.json", "paired/_SUCCESS", "path_days/_SUCCESS"),
    "snapshot": ("quality_report.json", "daily_returns"),
    "windows": ("config.json",),
}
PHASES = ("session_start", "window_stats_and_construction_check", "model_and_path_days", "summaries_and_pairing",
          "checks")
PHASE_LABELS = ("session\nstart", "window\nstatistics", "model and\npath_days", "summaries\nand pairing", "checks")
GROUP_COLORS = ("tab:blue", "tab:orange", "tab:green", "tab:purple")
TICKER_ORDER = ("AAPL", "MSFT", "NVDA", "TSLA", "QQQ")   # the spec's order: the four stocks, then QQQ
KEY = ["window_kind", "ticker", "window_days", "entry_date"]
MEASUREMENT_COLUMNS = {   # measurement CSV -> the columns its figure reads besides RUN_COLUMNS
    "stride_csv": ("protocol_id", "run_id", "role", "stride", "windows", "wall_s"),
    "partitions_csv": ("config", "used", "wall_excl_capture_s"),
    "baseline_csv": ("engine", "used", "wall_s"),
    "caching_csv": ("config", "used", "wall_excl_capture_s"),
}
RUN_COLUMNS = ("warmup", "status", "peak_rss_total_bytes", *(f"{p}_s" for p in PHASES))
TABLE_COLUMNS = {   # Parquet table -> the columns the figures read from it
    "paired": (*KEY, "return_1x", "return_2x", "breached_2x", "breach_date_2x", "contains_unverified_day",
               "exact_gap", "approx_gap", "log_gap", "approx_rel_error", "mdd_1x", "mdd_2x", "mdd_bound",
               "mean_turnover_2x"),
    "path_days": (*KEY, "leverage", "day", "date", "daily_return", "nav"),
    "daily_returns": ("ticker", "date", "daily_return"),
    "windows": (*KEY, "contains_unverified_day"),
}
BOUND_TOL = 1e-12                  # spark_pipeline.BOUND_TOL, the tolerance of the drawdown-bound check
MANIFEST_FORMAT = 1
DPI = 150
STYLE = {
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.titlesize": 8.5, "axes.labelsize": 8.5,
    "legend.fontsize": 7.5, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "axes.spines.top": False,
    "axes.spines.right": False, "axes.grid": True, "grid.alpha": 0.3, "grid.linewidth": 0.5,
    "figure.dpi": DPI, "savefig.dpi": DPI,
}
PLAIN, FLAGGED, GUIDE = "tab:blue", "tab:orange", "0.3"
UNVERIFIED_RULE = ("Unverified extreme day: |daily return| ≥ 20%, a move over 15% reversed the next day by over "
                   "13%, or a split day with |return| ≥ 10%, not yet checked against a second source "
                   "(data-sources.md). The days are kept in the data.")


def overlap_note(unit: str = "panel") -> str:
    return ("Rolling 252-trading-day windows, a new one every 21 trading days, so the windows overlap. "
            f"One {unit} per ticker; QQQ holds the other four and is not pooled with them.")


def signed(value: float, digits: int = 1) -> str:
    """A percentage with its sign and a true minus sign, as the axes print it."""
    return f"{value:+.{digits}%}".replace("-", "−")


# --- inputs ----------------------------------------------------------------------------

def read_table(path: Path, columns: list[str] | None = None, filters=None) -> pd.DataFrame:
    """A Parquet file or table folder as pandas, with the ticker partition column as plain strings."""
    df = pq.read_table(path, columns=columns, filters=filters).to_pandas()
    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].astype(str)
    return df


def tickers_in(values) -> list[str]:
    """The spec's ticker order, then any other ticker alphabetically (as in test data)."""
    present = set(values)
    return [t for t in TICKER_ORDER if t in present] + sorted(present - set(TICKER_ORDER))


def digest(path: Path) -> dict:
    """SHA-256 of a file, or of a folder's sorted (relative path, SHA-256) lines; with the file count."""
    if path.is_file():
        return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "files": 1}
    files = sorted(p for p in path.rglob("*") if p.is_file() and not p.name.startswith("."))
    lines = "".join(f"{p.relative_to(path).as_posix()} {hashlib.sha256(p.read_bytes()).hexdigest()}\n"
                    for p in files)
    return {"sha256": hashlib.sha256(lines.encode()).hexdigest(), "files": len(files)}


def shown_path(path: Path) -> str:
    """Repository-relative where possible, so no local path reaches a committed manifest."""
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def input_problems(name: str, path: Path) -> list[str]:
    """Why an input cannot be used as it is: a missing or unparseable part, a column or field that the
    figures read and that it lacks, or a run that did not end ok. Empty if the input is usable."""
    if not path.exists():
        return [f"{shown_path(path)} does not exist"]
    if name in MEASUREMENT_CSVS:
        return _csv_problems(path, (*MEASUREMENT_COLUMNS[name], *RUN_COLUMNS))
    problems = [f"{shown_path(path / part)} does not exist" for part in FOLDER_PARTS[name]
                if not (path / part).exists()]
    record_path = path / FOLDER_PARTS[name][0]
    if not record_path.exists():
        return problems
    record, unreadable = _json_object(record_path)
    if record is None:
        return problems + unreadable
    if name == "run":
        if record.get("status") != "ok":
            problems.append(f"{shown_path(record_path)} records status {record.get('status')!r}, not 'ok'")
        for table in ("paired", "path_days"):
            if (path / table).is_dir():
                problems += _parquet_problems(path / table, TABLE_COLUMNS[table])
        return problems
    if name == "snapshot":
        days = record.get("unverified_extreme_days")
        if not (isinstance(days, list) and all(isinstance(d, dict) and {"ticker", "date"} <= d.keys() for d in days)):
            problems.append(f"{shown_path(record_path)} lacks fields: unverified_extreme_days, a list of entries "
                            "with ticker and date")
        if (path / "daily_returns").is_dir():
            files = sorted((path / "daily_returns").glob("*.parquet"))
            if not files:
                problems.append(f"{shown_path(path / 'daily_returns')} holds no Parquet file")
            problems += [p for file in files for p in _parquet_problems(file, TABLE_COLUMNS["daily_returns"])]
        return problems
    windows_file = record.get("windows_file")                      # the windows input
    if not isinstance(windows_file, str) or not windows_file:
        return [f"{shown_path(record_path)} lacks fields: windows_file"]
    if not (path / windows_file).is_file():
        return [f"{shown_path(path / windows_file)}, named by {record_path.name}, does not exist"]
    return _parquet_problems(path / windows_file, TABLE_COLUMNS["windows"])


def _json_object(path: Path) -> tuple[dict | None, list[str]]:
    """A JSON file's object, or None and why it cannot be read as one."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return None, [f"{shown_path(path)} cannot be parsed as JSON: {exc}"]
    if not isinstance(value, dict):
        return None, [f"{shown_path(path)} does not hold a JSON object"]
    return value, []


def _csv_problems(path: Path, columns) -> list[str]:
    try:
        found = pd.read_csv(path).columns
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError) as exc:
        return [f"{shown_path(path)} cannot be parsed as CSV: {type(exc).__name__}: {str(exc).strip()}"]
    return _lacking(path, found, columns)


def _parquet_problems(path: Path, columns) -> list[str]:
    try:
        found = (pq.read_schema(path) if path.is_file() else pq.ParquetDataset(path).schema).names
    except pa.ArrowInvalid as exc:
        return [f"{shown_path(path)} cannot be read as Parquet: {exc}"]
    return _lacking(path, found, columns)


def _lacking(path: Path, found, columns) -> list[str]:
    missing = [c for c in columns if c not in set(found)]
    return [f"{shown_path(path)} lacks columns: {', '.join(missing)}"] if missing else []


# --- figure data: (data, checks) ----------------------------------------------------------

def m1_returns(paired: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """M1: 2x against 1x window returns. A breached 2x path has no 2x return, so it is left out."""
    both = paired.dropna(subset=["return_1x", "return_2x"])
    checks = {}
    for t in tickers_in(paired["ticker"]):
        w = both[both["ticker"] == t]
        checks[t] = {"windows_with_both_returns": int(len(w)),
                     "above_twice_1x": int((w["return_2x"] > 2 * w["return_1x"]).sum()),
                     "breached_2x": int((paired.loc[paired["ticker"] == t, "breached_2x"] == True).sum())}  # noqa: E712
    return both, checks


def m2_gap(paired: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """M2: the exact log gap against its approximation −Σr² (expectation 1), windows without a breach."""
    ok = paired.dropna(subset=["exact_gap", "approx_gap"])
    checks = {"windows_without_breach": int(len(ok)),
              "largest_exact_gap": float(ok["exact_gap"].max()),
              "largest_identity_difference": float((ok["log_gap"] - ok["exact_gap"]).abs().max()),
              "median_relative_error": {t: float(ok.loc[ok["ticker"] == t, "approx_rel_error"].median())
                                        for t in tickers_in(ok["ticker"])}}
    return ok, checks


def m3_drawdown(paired: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """M3: 2x against 1x maximum drawdown with the bound 1 − (1 − MDD_1x)² (expectation 2)."""
    ok = paired.dropna(subset=["mdd_1x", "mdd_2x", "mdd_bound"])
    below = ok["mdd_2x"] < ok["mdd_bound"] - BOUND_TOL
    checks = {t: {"windows": int((ok["ticker"] == t).sum()), "below_bound": int(below[ok["ticker"] == t].sum())}
              for t in tickers_in(ok["ticker"])}
    return ok, checks


def m4_turnover(paired: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """M4: the 2x path's mean daily turnover per window (expectation 4); breached windows have none."""
    ok = paired.dropna(subset=["mean_turnover_2x"])
    checks = {t: {"windows": int((ok["ticker"] == t).sum()),
                  "median_mean_turnover_2x": float(ok.loc[ok["ticker"] == t, "mean_turnover_2x"].median())}
              for t in tickers_in(ok["ticker"])}
    return ok, checks


def m5_breaches(paired: pd.DataFrame, run: Path) -> tuple[pd.DataFrame, dict]:
    """M5: the 2x NAV of every window whose 2x path was breached (expectation 3), from path_days."""
    breached = paired[paired["breached_2x"] == True]  # noqa: E712
    paths = []
    for t in tickers_in(breached["ticker"]):
        days = read_table(run / "path_days", columns=[*KEY, "leverage", "day", "date", "daily_return", "nav"],
                          filters=[("ticker", "=", t)])
        paths.append(days[days["leverage"] == 2.0].merge(breached.loc[breached["ticker"] == t, KEY], on=KEY))
    data = (pd.concat(paths, ignore_index=True) if paths
            else pd.DataFrame(columns=[*KEY, "leverage", "day", "date", "daily_return", "nav"]))
    breach_returns = sorted({float(r) for r in data.merge(
        breached[[*KEY, "breach_date_2x"]], on=KEY).query("date == breach_date_2x")["daily_return"]})
    checks = {"breached_windows": int(len(breached)), "tickers": tickers_in(breached["ticker"]),
              "breach_dates": sorted({str(d) for d in breached["breach_date_2x"]}),
              "breach_day_returns": breach_returns,
              "all_use_an_unverified_day": bool(breached["contains_unverified_day"].all())}
    return data, checks


def s1_sensitivity(paired: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """S1: exact medians of the 1x and 2x returns over all windows and over the windows without an
    unverified day, as analysis/sql_sensitivity.py computes them for 2x (percentile 0.5, nulls left out)."""
    rows = []
    for t in tickers_in(paired["ticker"]):
        w = paired[paired["ticker"] == t]
        plain = w[w["contains_unverified_day"] == False]  # noqa: E712
        for leverage, column in (("1x", "return_1x"), ("2x", "return_2x")):
            rows.append({"ticker": t, "leverage": leverage,
                         "all_windows": int(w[column].count()), "all_median": float(w[column].median()),
                         "unflagged_windows": int(plain[column].count()),
                         "unflagged_median": float(plain[column].median()) if plain[column].count() else math.nan})
    data = pd.DataFrame(rows)
    checks = {f"{r.ticker} {r.leverage}": {"all_windows": r.all_windows, "all_median": r.all_median,
                                           "unflagged_windows": r.unflagged_windows,
                                           "unflagged_median": r.unflagged_median} for r in data.itertuples()}
    return data, checks


def d1_returns(snapshot: Path) -> tuple[tuple[pd.DataFrame, pd.DataFrame], dict]:
    """D1: every daily return of the snapshot, with the unverified extreme days of its quality report."""
    returns = pd.concat([read_table(f, columns=["ticker", "date", "daily_return"])
                         for f in sorted((snapshot / "daily_returns").glob("*.parquet"))], ignore_index=True)
    returns = returns.dropna(subset=["daily_return"])
    report = json.loads((snapshot / "quality_report.json").read_text(encoding="utf-8"))
    flagged = pd.DataFrame([{"ticker": d["ticker"], "date": pd.Timestamp(d["date"]).date()}
                            for d in report["unverified_extreme_days"]], columns=["ticker", "date"])
    flagged = flagged.merge(returns, on=["ticker", "date"], how="left")
    checks = {"unverified_extreme_days": int(len(flagged)),
              "unverified_days_without_a_return": int(flagged["daily_return"].isna().sum())}
    for t in tickers_in(returns["ticker"]):
        r = returns[returns["ticker"] == t]
        checks[t] = {"returns": int(len(r)), "first_date": str(r["date"].min()), "last_date": str(r["date"].max()),
                     "unverified_extreme_days": int((flagged["ticker"] == t).sum())}
    return (returns, flagged), checks


def d2_windows(windows: Path) -> tuple[pd.DataFrame, dict]:
    """D2: the entry date of every window definition, and whether it uses an unverified day."""
    config = json.loads((windows / "config.json").read_text(encoding="utf-8"))
    defs = read_table(windows / config["windows_file"], columns=[*KEY, "contains_unverified_day"])
    checks = {t: {"windows": int((defs["ticker"] == t).sum()),
                  "use_an_unverified_day": int(defs.loc[defs["ticker"] == t, "contains_unverified_day"].sum())}
              for t in tickers_in(defs["ticker"])}
    return defs, checks


def measured_runs(csv: Path) -> pd.DataFrame:
    """The runs an experiment's summaries use: not warm-ups, ended ok, and in a used protocol where the
    CSV marks one (the stride experiment's CSV does not)."""
    rows = pd.read_csv(csv)
    keep = (rows["warmup"] == False) & (rows["status"] == "ok")  # noqa: E712
    if "used" in rows:
        keep &= rows["used"] == True  # noqa: E712
    return rows[keep]


def summarize(rows: pd.DataFrame, by: str, metric: str) -> dict:
    """Per group, in order of first appearance: the runs, the experiment's own time metric (median and
    range), the phase medians, and peak total RSS in GiB (median and range)."""
    out = {}
    for key, g in rows.groupby(by, sort=False):
        peak = g["peak_rss_total_bytes"] / 2**30
        out[str(key)] = {"runs": int(len(g)), "metric": metric, "median_s": float(g[metric].median()),
                         "min_s": float(g[metric].min()), "max_s": float(g[metric].max()),
                         "phases_s": {p: float(g[f"{p}_s"].median()) if g[f"{p}_s"].notna().any() else math.nan
                                      for p in PHASES},              # pandas has no session start: undefined
                         "peak_median_gib": float(peak.median()), "peak_min_gib": float(peak.min()),
                         "peak_max_gib": float(peak.max())}
    return out


STRIDE_LABELS = {"baseline": "stride {}, first", "planned": "stride {}", "exploratory": "stride {}, exploratory",
                 "drift_check": "stride {}, repeated"}


def x1_stride(csv: Path) -> tuple[pd.DataFrame, dict]:
    """X1: the stride experiment, per protocol in the order they ran; its time metric is wall_s (no plan
    capture). The repeated stride 21 is the drift check, and stride 3 is exploratory (experiments.md)."""
    rows = measured_runs(csv).sort_values(["protocol_id", "run_id"])
    rows = rows.assign(label=[STRIDE_LABELS[r.role].format(r.stride) for r in rows.itertuples()])
    protocols = summarize(rows, "label", "wall_s")
    for label, c in protocols.items():
        first = rows[rows["label"] == label].iloc[0]
        c.update({"protocol": str(first["protocol_id"]), "role": str(first["role"]), "stride": int(first["stride"]),
                  "windows": int(first["windows"])})
    baseline = next(c for c in protocols.values() if c["role"] == "baseline")
    repeated = next((c for c in protocols.values() if c["role"] == "drift_check"), None)
    drift = (repeated["median_s"] - baseline["median_s"]) / baseline["median_s"] if repeated else None
    return rows, {"protocols": protocols, "drift_of_the_repeated_protocol": drift}


def x2_partitions(csv: Path) -> tuple[pd.DataFrame, dict]:
    """X2: the shuffle-partition experiment's configurations; time metric wall_excl_capture_s."""
    rows = measured_runs(csv)
    return rows, summarize(rows, "config", "wall_excl_capture_s")


def x3_baseline(csv: Path) -> tuple[pd.DataFrame, dict]:
    """X3: the pandas baseline's implementations S and P; time metric wall_s (no plan capture)."""
    rows = measured_runs(csv)
    return rows, summarize(rows, "engine", "wall_s")


def x4_caching(csv: Path) -> tuple[pd.DataFrame, dict]:
    """X4: the caching experiment's configurations; time metric wall_excl_capture_s."""
    rows = measured_runs(csv)
    return rows, summarize(rows, "config", "wall_excl_capture_s")


# --- drawing ------------------------------------------------------------------------------

def _panels(n: int, row_height: float = 2.9):
    """One axes per ticker, three to a row; a spare axes, if any, holds the legend."""
    cols = min(n, 3)
    rows = math.ceil(n / cols)
    fig, grid = plt.subplots(rows, cols, figsize=(3.6 * cols + 0.4, row_height * rows + 0.9), squeeze=False)
    axes = list(grid.ravel())
    for spare in axes[n:]:
        spare.axis("off")
    return fig, axes[:n], (axes[n] if len(axes) > n else None)


def _finish(fig, title: str, note: str | None = None, xlabel: str | None = None, ylabel: str | None = None,
            legend_from=None, legend_in=None, legend_on_top: bool = False) -> None:
    """Title, shared axis labels, legend and footnote, with room for each measured in inches. The legend
    goes into `legend_in` (a spare axes), into a band under the title (`legend_on_top`), or where it fits."""
    height = fig.get_figheight()
    note_room = 0.36 if note else 0.0              # up to two lines of 7-point text
    label_room = 0.32 if xlabel else 0.0
    top_room = 0.36 + (0.3 if legend_on_top else 0.0)
    fig.suptitle(title, x=0.01, ha="left", fontsize=10, fontweight="bold")
    if legend_from is not None:
        handles, labels = legend_from.get_legend_handles_labels()
        if legend_on_top:
            fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.01, 1 - 0.4 / height),
                       ncol=len(labels), frameon=False)
        else:
            (legend_in or legend_from).legend(handles, labels, loc="center" if legend_in else "best", frameon=False)
    fig.tight_layout(rect=(0.03 if ylabel else 0, (note_room + label_room) / height, 1, 1 - top_room / height))
    if xlabel:
        fig.supxlabel(xlabel, y=(note_room + 0.05) / height, va="bottom", fontsize=8.5)
    if ylabel:
        fig.supylabel(ylabel, x=0.004, ha="left", fontsize=8.5)
    if note:
        fig.text(0.01, 0.06 / height, note, fontsize=7, color="0.35", ha="left", va="bottom", wrap=True)


def _percent(ax, x: bool = True, y: bool = True) -> None:
    if x:
        ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    if y:
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))


def _by_flag(ax, w: pd.DataFrame, x: str, y: str) -> None:
    for flag, color, label in ((False, PLAIN, "window without an unverified day"),
                               (True, FLAGGED, "window that uses an unverified day")):
        part = w[w["contains_unverified_day"] == flag]
        ax.scatter(part[x], part[y], s=5, color=color, alpha=0.55, linewidths=0, label=f"{label}")


def draw_m1(data: pd.DataFrame, checks: dict):
    tickers = list(checks)
    fig, axes, spare = _panels(len(tickers))
    for ax, t in zip(axes, tickers):
        w, c = data[data["ticker"] == t], checks[t]
        _by_flag(ax, w, "return_1x", "return_2x")
        xs = np.array([w["return_1x"].min(), w["return_1x"].max()]) if len(w) else np.array([0.0, 0.0])
        ax.plot(xs, 2 * xs, color=GUIDE, lw=0.9, ls="--", label="twice the 1x return")
        ax.set_title(f"{t}: 2x above the line in {c['above_twice_1x']} of {c['windows_with_both_returns']}")
        if c["breached_2x"]:
            ax.text(0.03, 0.97, f"{c['breached_2x']} windows with a breached 2x path not shown (M5)",
                    transform=ax.transAxes, va="top", fontsize=6.5, color="0.35")
        _percent(ax)
    _finish(fig, "M1  The 2x window return against twice the 1x return", note=overlap_note(),
            xlabel="1x window return", ylabel="2x window return", legend_from=axes[0], legend_in=spare)
    return fig


def draw_m2(data: pd.DataFrame, checks: dict):
    tickers = list(checks["median_relative_error"])
    fig, axes, spare = _panels(len(tickers))
    for ax, t in zip(axes, tickers):
        w = data[data["ticker"] == t]
        _by_flag(ax, w, "approx_gap", "exact_gap")
        lo = min(w["approx_gap"].min(), w["exact_gap"].min()) if len(w) else 0.0
        ax.plot([lo, 0], [lo, 0], color=GUIDE, lw=0.9, ls="--", label=r"exact gap $= -\sum r^2$")
        ax.set_title(f"{t}: {len(w)} windows, median error {signed(checks['median_relative_error'][t])}")
    _finish(fig, "M2  The 2x log gap against minus the realized variance (windows without a breach)",
            note=overlap_note() + " Error: (−Σr² − exact gap) / |exact gap|.",
            xlabel=r"$-\sum r^2$, minus the window's realized variance",
            ylabel=r"exact log gap $\log(1+R_{2x}) - 2\,\log(1+R_{1x})$", legend_from=axes[0], legend_in=spare)
    return fig


def draw_m3(data: pd.DataFrame, checks: dict):
    tickers = list(checks)
    fig, axes, spare = _panels(len(tickers))
    for ax, t in zip(axes, tickers):
        w, c = data[data["ticker"] == t], checks[t]
        _by_flag(ax, w, "mdd_1x", "mdd_2x")
        xs = np.linspace(0, w["mdd_1x"].max() if len(w) else 1.0, 200)
        ax.plot(xs, 1 - (1 - xs) ** 2, color=GUIDE, lw=0.9, ls="--", label=r"bound $1-(1-\mathrm{MDD}_{1x})^2$")
        ax.set_title(f"{t}: {c['windows']} windows, {c['below_bound']} below the bound")
        _percent(ax)
    _finish(fig, "M3  2x against 1x maximum drawdown, with the bound (windows without a breach)",
            note=overlap_note(), xlabel="1x maximum drawdown", ylabel="2x maximum drawdown",
            legend_from=axes[0], legend_in=spare)
    return fig


def draw_m4(data: pd.DataFrame, checks: dict):
    tickers = list(checks)
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    values = [data.loc[data["ticker"] == t, "mean_turnover_2x"].to_numpy() for t in tickers]
    ax.boxplot(values, tick_labels=[f"{t}\n{checks[t]['windows']} windows" for t in tickers], widths=0.5,
               medianprops={"color": "tab:red"}, flierprops={"markersize": 2, "alpha": 0.5})
    for i, t in enumerate(tickers, start=1):
        median = checks[t]["median_mean_turnover_2x"]
        ax.annotate(f"median\n{median:.1%}", (i + 0.28, median), va="center", ha="left", fontsize=7)
    ax.set_xlim(0.5, len(tickers) + 0.75)
    ax.set_ylabel("2x mean daily turnover, share of NAV")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _finish(fig, "M4  2x mean daily turnover per window, by ticker (windows without a breach)",
            note=overlap_note("box"))
    return fig


def draw_m5(data: pd.DataFrame, checks: dict):
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    for i, (_, path) in enumerate(data.sort_values("day").groupby(KEY, sort=True)):
        dates, defined = pd.to_datetime(path["date"]), path["nav"].notna()
        ax.plot(dates[defined], path["nav"][defined], lw=0.8, color=FLAGGED, alpha=0.8,
                label="2x NAV of one breached window" if i == 0 else None)
        if (~defined).any():             # the breach day: 1 + 2r < 0, so the NAV is not defined
            last, breach = dates[defined].iloc[-1], dates[~defined].iloc[0]
            ax.plot([last, breach], [path["nav"][defined].iloc[-1], 0], lw=0.6, ls=":", color=FLAGGED)
            ax.plot([breach], [0], marker="x", color="0.2", markersize=5, linestyle="None",
                    label="breach day: 1 + 2r < 0, the 2x path ends" if i == 0 else None)
    returns = ", ".join(signed(r) for r in checks["breach_day_returns"])
    ax.set_title(f"{checks['breached_windows']} windows ({', '.join(checks['tickers'])}), each breached on "
                 f"{', '.join(checks['breach_dates'])}: a 1x return of {returns}, an unverified day", loc="left")
    ax.set_ylabel("2x NAV (100 at entry)")
    ax.legend(frameon=False, loc="upper right")
    _finish(fig, "M5  The 2x NAV of the windows whose 2x path was breached",
            note="The model does not define the 2x NAV on the breach day; the dotted lines only mark the end of "
                 "each path. The windows' pre-breach values are reported apart from the others.")
    return fig


def draw_s1(data: pd.DataFrame, checks: dict):
    tickers = tickers_in(data["ticker"])
    fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.6))
    for ax, leverage in zip(axes, ("1x", "2x")):
        part = data[data["leverage"] == leverage].set_index("ticker").loc[tickers]
        x = np.arange(len(tickers))
        for offset, column, n_column, color, label in (
                (-0.2, "all_median", "all_windows", PLAIN, "all windows"),
                (0.2, "unflagged_median", "unflagged_windows", FLAGGED, "windows without an unverified day")):
            bars = ax.bar(x + offset, part[column], width=0.38, color=color, label=label)
            for bar, n in zip(bars, part[n_column]):
                ax.annotate(f"{n}", (bar.get_x() + bar.get_width() / 2, max(bar.get_height(), 0)),
                            xytext=(0, 2), textcoords="offset points", ha="center", fontsize=6.5)
        ax.set_xticks(x, tickers)
        ax.axhline(0, color="0.2", lw=0.6)
        ax.set_title(f"median {leverage} window return (labels: number of windows)", loc="left")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _finish(fig, "S1  Median window returns with and without the windows that use an unverified day",
            note="A sensitivity analysis: it shows how much a median depends on those periods, "
                 "not whether those days are wrong. QQQ has no window with an unverified day.",
            legend_from=axes[0], legend_on_top=True)
    return fig


def draw_d1(data: tuple[pd.DataFrame, pd.DataFrame], checks: dict):
    returns, flagged = data
    tickers = [t for t in checks if t in set(returns["ticker"])]
    fig, axes, spare = _panels(len(tickers))
    for ax, t in zip(axes, tickers):
        r, f = returns[returns["ticker"] == t], flagged[flagged["ticker"] == t]
        ax.scatter(pd.to_datetime(r["date"]), r["daily_return"], s=1, color=PLAIN, alpha=0.4, linewidths=0,
                   label="daily return")
        ax.scatter(pd.to_datetime(f["date"]), f["daily_return"], s=14, color=FLAGGED, edgecolors="0.2",
                   linewidths=0.4, label="unverified extreme day", zorder=3)
        c = checks[t]
        n = c["unverified_extreme_days"]
        ax.set_title(f"{t}: {c['returns']:,} returns, {n} unverified extreme day{'' if n == 1 else 's'}")
        ax.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    _finish(fig, "D1  Daily returns of the data snapshot, with the unverified extreme days",
            note=UNVERIFIED_RULE, ylabel="daily return", legend_from=axes[0], legend_in=spare)
    return fig


def draw_d2(data: pd.DataFrame, checks: dict):
    tickers = list(checks)
    fig, ax = plt.subplots(figsize=(7.2, 0.55 * len(tickers) + 1.6))
    styles = ((False, PLAIN, "window without an unverified day"), (True, FLAGGED, "window that uses an unverified day"))
    for row, t in enumerate(reversed(tickers)):
        w = data[data["ticker"] == t]
        for flag, color, _ in styles:
            part = w[w["contains_unverified_day"] == flag]
            ax.scatter(pd.to_datetime(part["entry_date"]), np.full(len(part), row), marker="|", s=40,
                       color=color, linewidths=0.8)
        c = checks[t]
        ax.annotate(f"{c['windows']} windows,\n{c['use_an_unverified_day']} flagged", (1.01, row),
                    xycoords=("axes fraction", "data"), va="center", fontsize=7)
    ax.set_yticks(range(len(tickers)), list(reversed(tickers)))
    ax.set_xlabel("window entry date")
    ax.grid(axis="y", visible=False)
    handles = [Line2D([], [], marker="|", linestyle="None", markersize=10, markeredgewidth=2, color=color,
                      label=label) for _, color, label in styles]
    ax.legend(handles=handles, frameon=False, loc="upper left", bbox_to_anchor=(0, -0.22), ncol=2)
    _finish(fig, "D2  Entry dates of the rolling windows, by ticker",
            note="A new 252-trading-day window every 21 trading days, on a start grid shared by all tickers. "
                 "Flagged: the window uses an unverified extreme day.")
    return fig


def draw_x1(data: pd.DataFrame, checks: dict):
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9))
    styles = {"baseline": ("o", PLAIN, True, "planned: stride 21 (first), 14 and 7"),
              "planned": ("o", PLAIN, True, None),
              "drift_check": ("s", "tab:red", False, "stride 21, repeated: the drift check"),
              "exploratory": ("D", "0.4", False, "stride 3: exploratory only")}
    for c in checks["protocols"].values():
        marker, color, filled, _ = styles[c["role"]]
        for ax, mid, lo, hi in ((axes[0], c["median_s"], c["min_s"], c["max_s"]),
                                (axes[1], c["peak_median_gib"], c["peak_min_gib"], c["peak_max_gib"])):
            ax.errorbar([c["windows"]], [mid], yerr=[[mid - lo], [hi - mid]], fmt=marker, color=color, ms=5,
                        mfc=color if filled else "white", capsize=3, lw=0.9)
            ax.annotate(str(c["stride"]), (c["windows"], mid), xytext=(6, -3), textcoords="offset points",
                        fontsize=7, color=color)
    axes[0].set_ylabel("wall_s (s): median and range")
    axes[1].set_ylabel("peak total RSS (GiB): median and range")
    for ax in axes:
        ax.set_xlabel("windows in the workload (labels: the stride)")
        ax.set_xlim(0, max(c["windows"] for c in checks["protocols"].values()) * 1.12)
        ax.margins(y=0.15)
    handles = [Line2D([], [], marker=m, color=col, mfc=col if filled else "white", linestyle="None", label=label)
               for m, col, filled, label in styles.values() if label]
    axes[1].legend(handles=handles, frameon=False, loc="lower right", fontsize=7)
    drift = checks["drift_of_the_repeated_protocol"]
    runs = ", ".join(sorted({str(c["runs"]) for c in checks["protocols"].values()}))
    drift_note = ("" if drift is None else f" Drift detected: the repeated stride-21 median was {signed(drift)} "
                  "against the first, outside the ±10% tolerance, so the comparisons across strides are marked as "
                  "affected.")
    _finish(fig, "X1  Stride experiment: runtime and peak memory against the number of windows",
            note=f"{runs} measured runs per protocol; time is wall_s (no plan capture).{drift_note} Stride 3 was not "
                 "admitted by the experiment's memory rule and is exploratory only (experiments.md).")
    return fig


def _draw_groups(checks: dict, labels: dict[str, str], title: str, metric: str, note: str):
    """Medians and ranges of the experiment's time metric and peak memory, and the phase medians, per group."""
    keys = list(checks)
    colors = dict(zip(keys, GROUP_COLORS))
    fig, (ax_t, ax_p, ax_m) = plt.subplots(1, 3, figsize=(11.6, 3.9), gridspec_kw={"width_ratios": [1, 2.3, 1]})
    x = np.arange(len(keys))
    for ax, (mid, lo, hi), fmt in ((ax_t, ("median_s", "min_s", "max_s"), "{:.1f} s"),
                                   (ax_m, ("peak_median_gib", "peak_min_gib", "peak_max_gib"), "{:.2f} GiB")):
        mids, los, his = (np.array([checks[k][f] for k in keys]) for f in (mid, lo, hi))
        ax.bar(x, mids, yerr=[mids - los, his - mids], color=[colors[k] for k in keys], width=0.6, capsize=3,
               error_kw={"lw": 0.9})
        for xi, m, h in zip(x, mids, his):        # the median's label sits above the range, not on it
            ax.annotate(fmt.format(m), (xi, h), xytext=(0, 3), textcoords="offset points", ha="center", fontsize=7)
        ax.margins(y=0.12)
        ax.set_xticks(x, [labels[k] for k in keys])
    ax_t.set_ylabel(f"{metric} (s): median and range")
    ax_m.set_ylabel("peak total RSS (GiB): median and range")
    width = 0.8 / len(keys)
    for i, k in enumerate(keys):
        values = [checks[k]["phases_s"][p] for p in PHASES]
        ax_p.bar(np.arange(len(PHASES)) + (i - (len(keys) - 1) / 2) * width, values, width=width, color=colors[k],
                 label=labels[k].replace("\n", " "))
    ax_p.set_xticks(np.arange(len(PHASES)), PHASE_LABELS)
    ax_p.set_ylabel("phase time (s): median")
    ax_p.legend(frameon=False, fontsize=7)
    _finish(fig, title, note=note)
    return fig


def draw_x2(data: pd.DataFrame, checks: dict):
    labels = {"A": "A: 200,\ncoalescing on", "B": "B: 200,\ncoalescing off", "C": "C: 8,\ncoalescing off"}
    runs = ", ".join(sorted({str(c["runs"]) for c in checks.values()}))
    return _draw_groups(checks, labels, "X2  Shuffle-partition experiment: requested partitions and AQE coalescing",
                        "wall_excl_capture_s",
                        f"{runs} measured runs per setting; time is wall_excl_capture_s, the wall time without plan "
                        "capture. The machine checks were recorded only before the first protocol, and the last "
                        "protocol followed a two-hour break; CPU time, spilling and GC were not measured "
                        "(partition-experiment.md).")


def draw_x3(data: pd.DataFrame, checks: dict):
    labels = {"S": "S: Spark,\nSpark's defaults", "P": "P: pandas,\none process"}
    runs = ", ".join(sorted({str(c["runs"]) for c in checks.values()}))
    return _draw_groups(checks, labels, "X3  Pandas baseline: the Spark pipeline against a single-process pandas one",
                        "wall_s",
                        f"{runs} measured runs per implementation; time is wall_s. An end-to-end comparison of two "
                        "implementations that share the model function, not a measure of Spark's overhead. P runs in "
                        "one process and has no session start; PyArrow permits multithreaded reads and conversion by "
                        "default, and actual thread use was not recorded (pandas-baseline.md).")


def draw_x4(data: pd.DataFrame, checks: dict):
    labels = {"A": "A:\nno cache", "B": "B:\nmembers", "C": "C: members\n+ 4 tables"}
    runs = ", ".join(sorted({str(c["runs"]) for c in checks.values()}))
    return _draw_groups(checks, labels, "X4  Caching experiment: what is cached", "wall_excl_capture_s",
                        f"{runs} measured runs per configuration; time is wall_excl_capture_s, the wall time "
                        "without plan capture. Positions 2 and 6 started 32 and 18 minutes after the positions before "
                        "them (the others 7 minutes apart), and the author left the computer idle in both gaps; CPU "
                        "time and GC were not measured (caching-experiment.md).")


# --- the figures ---------------------------------------------------------------------------

FIGURES = {   # id -> (file, inputs it reads, drawing function)
    "M1": ("m1-returns-2x-vs-1x.png", ("run",), draw_m1),
    "M2": ("m2-log-gap-vs-variance.png", ("run",), draw_m2),
    "M3": ("m3-drawdown-bound.png", ("run",), draw_m3),
    "M4": ("m4-turnover-2x.png", ("run",), draw_m4),
    "M5": ("m5-breached-windows.png", ("run",), draw_m5),
    "S1": ("s1-sensitivity-medians.png", ("run",), draw_s1),
    "D1": ("d1-daily-returns.png", ("snapshot",), draw_d1),
    "D2": ("d2-window-entry-dates.png", ("windows",), draw_d2),
    "X1": ("x1-stride-experiment.png", ("stride_csv",), draw_x1),
    "X2": ("x2-shuffle-partition-experiment.png", ("partitions_csv",), draw_x2),
    "X3": ("x3-pandas-baseline.png", ("baseline_csv",), draw_x3),
    "X4": ("x4-caching-experiment.png", ("caching_csv",), draw_x4),
}


def default_inputs(run: Path = DEFAULT_RUN, snapshot: Path = DEFAULT_SNAPSHOT, windows: Path = DEFAULT_WINDOWS,
                   measurements: Path = DEFAULT_MEASUREMENTS) -> dict[str, Path]:
    """Every input by name, resolved against the repository root."""
    return {"run": resolve(run), "snapshot": resolve(snapshot), "windows": resolve(windows),
            **{name: resolve(measurements) / copy for name, (copy, _) in MEASUREMENT_CSVS.items()}}


def compute(inputs: dict[str, Path], figures=tuple(FIGURES)) -> dict[str, tuple[object, dict]]:
    """The selected figures' (data, checks), in the order of FIGURES."""
    run = inputs.get("run")
    paired = read_table(run / "paired") if any("run" in FIGURES[f][1] for f in figures) else None
    make = {"M1": lambda: m1_returns(paired), "M2": lambda: m2_gap(paired), "M3": lambda: m3_drawdown(paired),
            "M4": lambda: m4_turnover(paired), "M5": lambda: m5_breaches(paired, run),
            "S1": lambda: s1_sensitivity(paired), "D1": lambda: d1_returns(inputs["snapshot"]),
            "D2": lambda: d2_windows(inputs["windows"]), "X1": lambda: x1_stride(inputs["stride_csv"]),
            "X2": lambda: x2_partitions(inputs["partitions_csv"]), "X3": lambda: x3_baseline(inputs["baseline_csv"]),
            "X4": lambda: x4_caching(inputs["caching_csv"])}
    return {f: make[f]() for f in FIGURES if f in figures}


# The values the documents report for the default inputs (docs/spec.md §8: the run of record and its
# SQL analyses; data-sources.md; the experiment documents), compared at the precision they are reported with.
DOCUMENTED = {
    "windows": {"AAPL": 529, "MSFT": 466, "NVDA": 311, "TSLA": 174, "QQQ": 310},
    "windows_with_an_unverified_day": {"AAPL": 78, "MSFT": 12, "NVDA": 92, "TSLA": 57, "QQQ": 0},
    "above_twice_1x": {"AAPL": (219, 517), "MSFT": (164, 466), "NVDA": (141, 311), "TSLA": (43, 174),
                       "QQQ": (140, 310)},
    "windows_without_breach": 1778,
    "median_relative_error_range": ((-1.2, "NVDA"), (0.3, "TSLA")),          # percent, lowest and highest
    "median_turnover_range": ((1.8, "QQQ"), (5.0, "TSLA")),                 # percent, lowest and highest
    "breaches": {"windows": 12, "tickers": ["AAPL"], "dates": ["2000-09-29"], "returns_percent": [-51.9]},
    "median_return_1x_percent": {"AAPL": 24.4, "MSFT": 22.8, "NVDA": 39.5, "TSLA": 22.5, "QQQ": 16.6},
    "median_return_2x_percent": {"AAPL": (35.2, 517), "MSFT": (39.9, 466), "NVDA": (51.3, 311),
                                 "TSLA": (13.5, 174), "QQQ": (31.4, 310)},
    "median_return_2x_unflagged_percent": {"AAPL": (48.5, 451), "MSFT": (41.4, 454), "NVDA": (52.2, 219),
                                           "TSLA": (-12.3, 117), "QQQ": (31.4, 310)},
    "unverified_extreme_days": 36,
    # data-sources.md: each ticker's rows less the first, which has no return, and its unverified days
    "returns_and_unverified_days": {"AAPL": (11354, 8), "MSFT": (10028, 1), "NVDA": (6777, 18), "TSLA": (3901, 9),
                                    "QQQ": (6745, 0)},
    # Per group, as the experiment documents print it: the time metric's median (min–max) in s, the peak total
    # RSS's median (min–max) in GiB, and the phase medians in s in PHASES order ("—": no such phase)
    "X1": {                                                                          # experiments.md 5.7 and 6.2
        "stride 21, first": ("22.226 (20.918–22.711)", "2.619 (2.482–2.667)", "3.155, 4.969, 4.872, 4.293, 1.916"),
        "stride 14": ("20.294 (20.221–20.346)", "2.684 (2.676–2.686)", "2.359, 4.252, 5.213, 4.471, 1.425"),
        "stride 7": ("25.660 (24.699–26.001)", "2.705 (2.681–2.707)", "2.478, 5.079, 8.099, 5.780, 1.619"),
        "stride 3, exploratory": ("40.170 (39.907–42.032)", "2.733 (2.730–2.767)",
                                  "2.487, 7.895, 16.279, 9.622, 1.864"),
        "stride 21, repeated": ("18.153 (18.029–18.295)", "2.681 (2.658–2.694)", "2.346, 4.013, 4.340, 3.806, 1.460"),
    },
    "X1_drift_percent": -18.3,                                                             # experiments.md 5.5
    "X2": {                                                                             # partition-experiment.md 14.6
        "A": ("26.462 (25.154–27.050)", "2.689 (2.676–2.698)", "2.490, 4.953, 8.435, 6.462, 1.607"),
        "B": ("44.632 (43.090–45.708)", "2.691 (2.659–2.793)", "2.476, 10.447, 12.477, 14.043, 2.552"),
        "C": ("25.277 (23.738–25.555)", "2.691 (2.671–2.702)", "2.514, 4.665, 8.314, 5.090, 1.831"),
    },
    "X3": {                                                                                  # pandas-baseline.md 14.6
        "S": ("26.407 (25.621–27.152)", "2.680 (2.667–2.707)", "2.440, 4.943, 8.622, 6.459, 1.535"),
        "P": ("15.377 (15.202–15.652)", "1.968 (1.924–2.054)", "—, 0.308, 12.134, 1.479, 0.974"),
    },
    "X4": {                                                                               # caching-experiment.md 14.6
        "A": ("26.485 (26.127–26.624)", "2.683 (2.663–2.694)", "2.476, 4.933, 8.534, 6.509, 1.646"),
        "B": ("27.035 (26.663–28.207)", "2.678 (2.667–2.690)", "2.469, 5.865, 8.205, 6.676, 1.548"),
        "C": ("28.721 (28.346–29.135)", "2.698 (2.688–2.713)", "2.468, 5.944, 9.490, 6.909, 1.547"),
    },
}


def compare_documented(results: dict) -> list[str]:
    """Every difference between DOCUMENTED and the checked numbers of the figures in `results`, which
    must have been computed from the documented inputs."""
    doc, problems = DOCUMENTED, []
    c = {figure_id: checks for figure_id, (_, checks) in results.items()}
    tickers = doc["windows"]                     # a ticker missing from the results is a difference, not an error

    def same(label, got, want):
        if got != want:
            problems.append(f"{label}: {got}, documented {want}")

    def pct(value):
        return None if value is None else round(100 * value, 1)

    def extremes(values: dict):                  # (lowest in percent, its ticker), (highest, its ticker)
        return ((round(100 * min(values.values()), 1), min(values, key=values.get)),
                (round(100 * max(values.values()), 1), max(values, key=values.get)))

    if "D1" in c:
        for t in tickers:
            d1t = c["D1"].get(t, {})
            same(f"D1 {t} returns and unverified extreme days",
                 (d1t.get("returns"), d1t.get("unverified_extreme_days")), doc["returns_and_unverified_days"][t])
        same("D1 unverified extreme days", c["D1"]["unverified_extreme_days"], doc["unverified_extreme_days"])
        same("D1 unverified days without a return", c["D1"]["unverified_days_without_a_return"], 0)
    if "D2" in c:
        for t, n in tickers.items():
            d2t = c["D2"].get(t, {})
            same(f"D2 {t} windows", d2t.get("windows"), n)
            same(f"D2 {t} windows with an unverified day", d2t.get("use_an_unverified_day"),
                 doc["windows_with_an_unverified_day"][t])
    if "M1" in c:
        for t in tickers:
            m1t = c["M1"].get(t, {})
            same(f"M1 {t} above twice the 1x return",
                 (m1t.get("above_twice_1x"), m1t.get("windows_with_both_returns")), doc["above_twice_1x"][t])
    if "M2" in c:
        same("M2 windows without a breach", c["M2"]["windows_without_breach"], doc["windows_without_breach"])
        same("M2 largest exact gap is at most 0", c["M2"]["largest_exact_gap"] <= 0, True)
        same("M2 lowest and highest median relative error", extremes(c["M2"]["median_relative_error"]),
             doc["median_relative_error_range"])
    if "M3" in c:
        for t in tickers:
            same(f"M3 {t} windows below the bound", c["M3"].get(t, {}).get("below_bound"), 0)
    if "M4" in c:
        same("M4 lowest and highest median turnover",
             extremes({t: v["median_mean_turnover_2x"] for t, v in c["M4"].items()}), doc["median_turnover_range"])
    if "M5" in c:
        m5 = c["M5"]
        same("M5 breaches", {"windows": m5["breached_windows"], "tickers": m5["tickers"], "dates": m5["breach_dates"],
                             "returns_percent": [round(100 * r, 1) for r in m5["breach_day_returns"]]}, doc["breaches"])
        same("M5 every breached window uses an unverified day", m5["all_use_an_unverified_day"], True)
    if "S1" in c:
        for t in tickers:
            s1x, s2x = c["S1"].get(f"{t} 1x", {}), c["S1"].get(f"{t} 2x", {})
            same(f"S1 {t} median 1x return", pct(s1x.get("all_median")), doc["median_return_1x_percent"][t])
            same(f"S1 {t} median 2x return and windows", (pct(s2x.get("all_median")), s2x.get("all_windows")),
                 doc["median_return_2x_percent"][t])
            same(f"S1 {t} median 2x return and windows without an unverified day",
                 (pct(s2x.get("unflagged_median")), s2x.get("unflagged_windows")),
                 doc["median_return_2x_unflagged_percent"][t])
    for figure_id in ("X1", "X2", "X3", "X4"):
        if figure_id in c:
            groups = c[figure_id]["protocols"] if figure_id == "X1" else c[figure_id]
            for group, values in doc[figure_id].items():
                same(f"{figure_id} {group}", as_documented(groups[group]) if group in groups else None, values)
    if "X1" in c:
        same("X1 drift of the repeated stride 21", pct(c["X1"]["drift_of_the_repeated_protocol"]),
             doc["X1_drift_percent"])
    return problems


def compare_copies(names) -> tuple[list[str], list[str], list[str]]:
    """The reviewed measurement CSVs in docs/measurements against the collectors' outputs under data/:
    (identical copies, differences, sources absent here)."""
    identical, differ, absent = [], [], []
    for name in names:
        copy, source = resolve(DEFAULT_MEASUREMENTS) / MEASUREMENT_CSVS[name][0], resolve(MEASUREMENT_CSVS[name][1])
        if not source.is_file():
            absent.append(shown_path(source))
        elif copy.read_bytes() == source.read_bytes():
            identical.append(shown_path(copy))
        else:
            differ.append(f"{shown_path(copy)} differs from {shown_path(source)}")
    return identical, differ, absent


def as_documented(c: dict) -> tuple[str, str, str]:
    """A group's summary as the experiment documents print it, to three decimals: the time metric's and the
    peak's median (minimum–maximum), and the phase medians ("—" where the group has no such phase)."""
    phases = ", ".join("—" if math.isnan(c["phases_s"][p]) else f"{c['phases_s'][p]:.3f}" for p in PHASES)
    return (f"{c['median_s']:.3f} ({c['min_s']:.3f}–{c['max_s']:.3f})",
            f"{c['peak_median_gib']:.3f} ({c['peak_min_gib']:.3f}–{c['peak_max_gib']:.3f})", phases)


def _rounded(value):
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, 6)
    if isinstance(value, dict):
        return {k: _rounded(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_rounded(v) for v in value]
    return value


def write_figures(results: dict, inputs: dict[str, Path], out: Path) -> dict:
    """The figures in `results` as PNGs in `out`, and figures.json: the inputs they read, with their
    SHA-256, and each figure's file and checks. Every figure is drawn in memory before any file is
    written, so an error while drawing one leaves `out` as it was."""
    plt.rcParams.update(STYLE)
    pngs, entries = {}, []
    for figure_id, (data, checks) in results.items():
        name, reads, draw = FIGURES[figure_id]
        fig = draw(data, checks)
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=DPI, metadata={"Software": None})
        plt.close(fig)
        pngs[name] = buffer.getvalue()
        entries.append({"id": figure_id, "file": name, "inputs": list(reads), "checks": _rounded(checks)})
    manifest = {
        "format": MANIFEST_FORMAT,
        "generator": "etf_risk.plots",
        "plots_py_sha256": digest(Path(__file__))["sha256"],
        "uv_lock_sha256": digest(REPO_ROOT / "uv.lock")["sha256"] if (REPO_ROOT / "uv.lock").is_file() else None,
        "matplotlib": matplotlib.__version__,
        "inputs": {name: {"path": shown_path(path), **digest(path)} for name, path in inputs.items()
                   if any(name in FIGURES[f][1] for f in results)},
        "figures": entries,
    }
    out.mkdir(parents=True, exist_ok=True)
    for name, png in pngs.items():
        (out / name).write_bytes(png)
    (out / "figures.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run", type=Path, default=DEFAULT_RUN, help="run folder (default: the run of record)")
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT, help="processed data snapshot")
    parser.add_argument("--windows", type=Path, default=DEFAULT_WINDOWS, help="window definitions of the run")
    parser.add_argument("--measurements", type=Path, default=DEFAULT_MEASUREMENTS,
                        help="folder with the four measurement CSVs (default: the reviewed copies, docs/measurements)")
    parser.add_argument("--figures", nargs="+", choices=list(FIGURES), default=list(FIGURES), metavar="ID",
                        help=f"figures to compute, of {' '.join(FIGURES)} (default: all)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="folder for the figures and figures.json")
    parser.add_argument("--check", action="store_true",
                        help="print each figure's checked numbers and compare them with the documented values")
    args = parser.parse_args(argv)
    figures, out = [f for f in FIGURES if f in args.figures], resolve(args.out)
    if not args.check and len(figures) < len(FIGURES) and out == resolve(DEFAULT_OUT):
        print(f"nothing drawn: figures.json in {shown_path(out)} would then list only {', '.join(figures)}; "
              "give another folder with --out")
        return 2
    inputs = default_inputs(args.run, args.snapshot, args.windows, args.measurements)
    needed = {name: path for name, path in inputs.items() if any(name in FIGURES[f][1] for f in figures)}
    missing = {name: input_problems(name, path) for name, path in needed.items()}
    missing = {name: problems for name, problems in missing.items() if problems}
    if missing:
        print("nothing computed: inputs that the selected figures need are missing or unusable")
        for name, problems in missing.items():
            print(f"  {name}, for {', '.join(f for f in figures if name in FIGURES[f][1])}:")
            for problem in problems:
                print(f"    {problem}")
        print("Select figures with --figures, or build the inputs (docs/demo.md, 'From a fresh clone').")
        return 2
    results = compute(needed, figures)
    defaults = default_inputs()
    documented = [f for f in figures if all(needed[name] == defaults[name] for name in FIGURES[f][1])]
    not_compared = [f for f in figures if f not in documented]
    problems = compare_documented({f: results[f] for f in documented})
    if args.check:
        for figure_id, (_, checks) in results.items():
            print(f"{figure_id}: {json.dumps(_rounded(checks))}")
    else:
        manifest = write_figures(results, needed, out)
        print(f"{len(manifest['figures'])} figures and figures.json -> {shown_path(out)}")
    if documented:
        print(f"documented values: compared for {', '.join(documented)}: "
              + ("all match" if not problems else f"{len(problems)} differ"))
        for problem in problems:
            print(f"  {problem}")
    if not_compared:
        print(f"documented values: not compared for {', '.join(not_compared)}, "
              "whose inputs are not the documented ones")
    copies = [name for name in needed if name in MEASUREMENT_CSVS]
    if copies and resolve(args.measurements) == resolve(DEFAULT_MEASUREMENTS):
        identical, differ, absent = compare_copies(copies)
        if identical:
            print(f"measurement CSVs: {len(identical)} of {len(copies)} copies identical to their sources under data/")
        for difference in differ:
            print(f"measurement CSVs: {difference}")
        if absent:
            print("measurement CSVs: not compared with their sources, absent here: " + ", ".join(absent))
        problems += differ
    if problems:
        return 1
    return 3 if args.check and not_compared else 0


if __name__ == "__main__":
    sys.exit(main())
