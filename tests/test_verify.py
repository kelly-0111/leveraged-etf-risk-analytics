"""The sample reference check: sample selection, exact-gap null rule, and a planted mismatch.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import shutil

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import spark_pipeline, verify
from etf_risk.windows import WINDOW_KEY, build_definitions, write_definitions

pytestmark = pytest.mark.spark
ANCHOR = "2024-01-02"


@pytest.fixture(scope="module")
def run(spark, tmp_path_factory):
    root = tmp_path_factory.mktemp("verify")
    rng = np.random.default_rng(3)
    dates = nyse_sessions(ANCHOR, 41)
    b = rng.normal(0, 0.02, 40)
    b[19] = -0.55                                         # breach at 2x on row 20
    snap = write_snapshot(root, "snap", {"AAA": (dates, rng.normal(0, 0.02, 40)), "BBB": (dates, b)},
                          unverified=[{"ticker": "BBB", "date": str(dates[20])}])
    windows = write_definitions(*build_definitions(snap, "rolling", window_days=8, stride=3, anchor=ANCHOR), root / "w")
    assert spark_pipeline.main(["--windows", str(windows), "--out-root", str(root / "out"), "--run-id", "r1"]) == 0
    return root / "out" / "snap" / windows.name / "r1"


def test_sample_has_the_ticker_breached_windows_and_edges():
    defs = pd.DataFrame({
        "window_kind": "rolling", "window_days": 8,
        "ticker": ["AAA"] * 3 + ["BBB"] * 4,
        "entry_date": pd.to_datetime(["2024-01-02", "2024-01-05", "2024-01-10", "2024-01-02", "2024-01-05",
                                      "2024-01-10", "2024-01-16"]).date,
    })
    breached = {("rolling", "BBB", 8, defs["entry_date"][4])}
    sample = verify.select_sample(defs, breached, "AAA")
    keys = set(sample[WINDOW_KEY].apply(tuple, axis=1))
    assert {k for k in keys if k[1] == "AAA"} == set(defs[defs.ticker == "AAA"][WINDOW_KEY].apply(tuple, axis=1))
    bbb = sorted(k[3] for k in keys if k[1] == "BBB")
    assert bbb == [defs["entry_date"][3], defs["entry_date"][4], defs["entry_date"][6]]   # first, breached, last


def test_exact_gap_is_none_when_any_term_is_undefined():
    assert verify.python_exact_gap(np.array([0.01, -0.5, 0.02])) is None       # 1 + 2r = 0
    assert verify.python_exact_gap(np.array([0.01, -0.02])) == pytest.approx(
        np.log1p(-(0.01 / 1.01) ** 2) + np.log1p(-(0.02 / 0.98) ** 2))


def test_clean_run_has_no_mismatches(spark, run):
    assert verify.main(["--run", str(run), "--sample-ticker", "AAA"]) == 0
    result = json.loads((run / "verify.json").read_text())
    assert result["mismatch_count"] == 0 and result["breached_windows"]["same"] and result["breached_windows"]["spark"] > 0


def test_altered_summary_value_is_reported(spark, run, tmp_path):
    copy = tmp_path / "r1"
    shutil.copytree(run, copy)
    summary = pq.read_table(copy / "path_summary").to_pandas()
    target = summary.index[(summary["ticker"] == "AAA") & (summary["leverage"] == 2.0)][0]
    summary.loc[target, "total_return"] += 1e-6
    shutil.rmtree(copy / "path_summary")
    (copy / "path_summary").mkdir()
    pq.write_table(pa.Table.from_pandas(summary, preserve_index=False), copy / "path_summary" / "part-0.parquet")
    assert verify.main(["--run", str(copy), "--sample-ticker", "AAA"]) == 1
    result = json.loads((copy / "verify.json").read_text())
    assert any("total_return" in m for m in result["mismatches"])


def test_changed_input_file_stops_verification(spark, run, tmp_path):
    record = json.loads((run / "run.json").read_text())
    windows = tmp_path / "w"
    shutil.copytree(record["windows_dir"], windows)
    (windows / "windows.parquet").write_bytes((windows / "windows.parquet").read_bytes() + b" ")
    copy = tmp_path / "r1"
    shutil.copytree(run, copy)
    (copy / "run.json").write_text(json.dumps({**record, "windows_dir": str(windows)}))
    assert verify.main(["--run", str(copy)]) == 3
