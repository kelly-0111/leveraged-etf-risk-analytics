"""Window definitions: shared start grid, scheduled dates, calendar years, flags and checksums.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
from datetime import date

import numpy as np
import pyarrow.parquet as pq
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import windows
from etf_risk.windows import ChecksumError, build_definitions, session_grid, verify_checksums, write_definitions

ANCHOR = "2024-01-02"


def two_ticker_snapshot(tmp_path, unverified=None):
    a_dates = nyse_sessions(ANCHOR, 31)                     # rows 0..30
    b_dates = nyse_sessions("2024-01-05", 26)               # starts 3 sessions later
    rng = np.random.default_rng(0)
    return write_snapshot(tmp_path, "snap", {
        "AAA": (a_dates, rng.normal(0, 0.01, 30)),
        "BBB": (b_dates, rng.normal(0, 0.01, 25)),
    }, unverified)


def test_rolling_windows_start_on_the_shared_grid(tmp_path):
    snap = two_ticker_snapshot(tmp_path)
    defs, _ = build_definitions(snap, "rolling", window_days=5, stride=3, anchor=ANCHOR)
    grid = session_grid(date(2024, 1, 2), date(2024, 3, 1), date(2024, 1, 2))
    assert all(grid[d] % 3 == 0 for d in defs["first_return_date"])
    starts = {t: set(g["first_return_date"]) for t, g in defs.groupby("ticker")}
    overlap = [d for d in starts["AAA"] if min(starts["BBB"]) <= d <= max(starts["BBB"])]
    assert overlap and set(overlap) <= starts["BBB"]          # same start dates where both can start


def test_scheduled_dates_follow_the_rows(tmp_path):
    snap = two_ticker_snapshot(tmp_path)
    defs, _ = build_definitions(snap, "rolling", window_days=5, stride=3, anchor=ANCHOR)
    for ticker, g in defs.groupby("ticker"):
        rows = pq.read_table(snap / "daily_returns" / f"{ticker}.parquet").to_pandas()["date"].tolist()
        n = len(rows) - 1
        for w in g.itertuples():
            assert w.window_days == 5 and w.stride == 3
            assert (w.entry_date, w.first_return_date, w.exit_date) == (rows[w.entry_row], rows[w.entry_row + 1], rows[w.entry_row + 5])
            assert w.entry_row + 5 <= n                       # complete windows only
        grid = session_grid(rows[0], rows[-1], date(2024, 1, 2)) if ticker == "AAA" else None
        if grid:
            expected = [k for k in range(1, n - 5 + 2) if grid[rows[k]] % 3 == 0]
            assert list(g["entry_row"] + 1) == expected


def test_calendar_year_windows_cover_complete_years_only(tmp_path):
    full = nyse_sessions("2019-06-03", 800)
    full = [d for d in full if d <= date(2021, 12, 31)]
    short = [d for d in full if d <= date(2021, 6, 30)]         # 2021 incomplete for this ticker
    snap = write_snapshot(tmp_path, "snap", {
        "AAA": (full, np.full(len(full) - 1, 0.001)), "BBB": (short, np.full(len(short) - 1, 0.001))})
    defs, config = build_definitions(snap, "calendar-year")
    a = defs[defs["ticker"] == "AAA"].set_index("calendar_year")
    assert list(a.index) == [2020, 2021]
    assert a.loc[2020, "entry_date"] == date(2019, 12, 31) and a.loc[2020, "exit_date"] == date(2020, 12, 31)
    assert a.loc[2020, "window_days"] == sum(d.year == 2020 for d in full)       # 253 sessions in 2020
    assert a.loc[2021, "window_days"] == sum(d.year == 2021 for d in full)       # 252 sessions in 2021
    assert list(defs[defs["ticker"] == "BBB"]["calendar_year"]) == [2020]
    assert config["skipped_calendar_years"] == {"AAA": [2019], "BBB": [2019, 2021]}


def test_full_period_is_one_window_per_ticker(tmp_path):
    snap = two_ticker_snapshot(tmp_path)
    defs, _ = build_definitions(snap, "full-period")
    assert defs.set_index("ticker")["window_days"].to_dict() == {"AAA": 30, "BBB": 25}
    assert (defs["entry_row"] == 0).all()


def test_unverified_days_are_counted_over_every_price_date_including_entry(tmp_path):
    a = nyse_sessions(ANCHOR, 31)
    # stride 3 on the grid: AAA's first return rows are 3, 6, 9, 12, ..., so its entry rows are 2, 5, 8, 11, ...
    snap = two_ticker_snapshot(tmp_path, unverified=[{"ticker": "AAA", "date": str(a[10])},
                                                     {"ticker": "AAA", "date": str(a[11])}])
    defs, config = build_definitions(snap, "rolling", window_days=5, stride=3, anchor=ANCHOR)
    for w in defs.itertuples():
        expected = sum(w.entry_date <= d <= w.exit_date for d in (a[10], a[11])) if w.ticker == "AAA" else 0
        assert w.unverified_day_count == expected and w.contains_unverified_day == (expected > 0)
        assert w.entry_on_unverified_day == (w.ticker == "AAA" and w.entry_date in (a[10], a[11]))
    # conservative rule: a window entered at the close of an unverified day uses that price, so it is flagged
    entered = defs[(defs["ticker"] == "AAA") & (defs["entry_date"] == a[11])]
    assert len(entered) == 1                                   # the case is really exercised
    assert entered["contains_unverified_day"].all() and entered["entry_on_unverified_day"].all()
    assert entered["first_return_date"].iloc[0] == a[12]       # its return dates alone would not contain a[11]
    assert config["counts"]["with_unverified_day"]["BBB"] == 0
    assert "entry_date" in config["unverified_flag_rule"]


def test_self_check_passes_and_catches_tampered_definitions(tmp_path):
    snap = two_ticker_snapshot(tmp_path, unverified=[{"ticker": "AAA", "date": str(nyse_sessions(ANCHOR, 31)[12])}])
    defs, config = build_definitions(snap, "rolling", window_days=5, stride=3, anchor=ANCHOR)
    assert config["definition_checks"] and not any(config["definition_checks"].values())
    frames = windows.load_returns(snap)
    grid = session_grid(date(2024, 1, 2), date(2024, 3, 1), date(2024, 1, 2))
    unverified = {"AAA": [str(nyse_sessions(ANCHOR, 31)[12])]}

    def violations(changed):
        return {k: v for k, v in windows.check_definitions(changed, frames, "rolling", unverified, 5, 3, grid).items() if v}

    shifted = defs.copy()
    shifted.loc[0, "entry_row"] += 1                          # rows no longer match the recorded dates
    assert "row_dates_mismatch" in violations(shifted)
    dropped = defs.drop(index=1).reset_index(drop=True)       # a missing window breaks spacing and coverage
    assert {"spacing_not_stride", "missing_or_extra_windows"} <= set(violations(dropped))
    unflagged = defs.copy()
    unflagged["contains_unverified_day"] = False
    assert "flag_mismatch" in violations(unflagged)


def test_config_records_provenance_and_resolves_relative_paths(tmp_path):
    snap = two_ticker_snapshot(tmp_path)
    _, config = build_definitions(snap, "full-period")
    assert {"git_commit", "git_worktree_clean", "source_sha256", "uv_lock_sha256"} <= set(config["code"])
    assert "windows.py" in config["code"]["source_sha256"]
    assert config["raw_manifest_sha256_by_ticker"] == {"AAA": "test-manifest", "BBB": "test-manifest"}
    from etf_risk.provenance import REPO_ROOT, resolve
    assert resolve("data/processed/x") == REPO_ROOT / "data/processed/x" and resolve(snap) == snap


def test_config_records_checksums_and_any_change_is_detected(tmp_path):
    snap = two_ticker_snapshot(tmp_path)
    out = write_definitions(*build_definitions(snap, "rolling", window_days=5, stride=3, anchor=ANCHOR), tmp_path / "w")
    config = json.loads((out / "config.json").read_text())
    assert set(config["inputs_sha256"]) == {"daily_returns/AAA.parquet", "daily_returns/BBB.parquet", "quality_report.json"}
    _, verified = verify_checksums(out)
    assert len(verified) == 4                                   # two return files, quality report, windows.parquet
    for path in (snap / "quality_report.json", out / "windows.parquet", snap / "daily_returns" / "BBB.parquet"):
        original = path.read_bytes()
        path.write_bytes(original + b" ")
        with pytest.raises(ChecksumError, match=path.name):
            verify_checksums(out)
        path.write_bytes(original)
    verify_checksums(out)


def test_dense_stride_needs_an_explicit_override(tmp_path):
    two_ticker_snapshot(tmp_path)
    args = ["--snapshot", "snap", "--processed-root", str(tmp_path / "processed"), "--kind", "rolling",
            "--stride", "5", "--out-root", str(tmp_path / "w")]
    with pytest.raises(SystemExit):
        windows.main(args)
    assert windows.main(args + ["--window-days", "5", "--anchor", ANCHOR, "--allow-dense-stride"]) == 0


def test_existing_definitions_are_not_overwritten(tmp_path):
    snap = two_ticker_snapshot(tmp_path)
    defs, config = build_definitions(snap, "full-period")
    write_definitions(defs, config, tmp_path / "w")
    with pytest.raises(FileExistsError):
        write_definitions(defs, config, tmp_path / "w")
