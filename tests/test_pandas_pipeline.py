"""The single-process baseline (etf_risk.pandas_pipeline) must match the Spark pipeline table for table and check for check.

Both pipelines run on the small synthetic snapshot of tests/test_spark_equivalence.py (a 2x breach, an
unverified day, a shorter ticker). Every output table is compared by its full key with the shuffle-partition
collector's rules (docs/partition-experiment.md 7: keys, types, nulls and non-floating fields exactly,
floats within 1e-12 + 1e-9 |r|), and the check counts must be equal, also for the failures that
tests/test_spark_equivalence.py injects.

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import measure
from etf_risk import pandas_pipeline as pp
from etf_risk.windows import WINDOW_KEY, build_definitions, write_definitions

ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"
_spec = importlib.util.spec_from_file_location("collect_partition_measurements",
                                               ANALYSIS / "collect_partition_measurements.py")
cpm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpm)

ANCHOR = "2024-01-02"
BREACH_ROW = 30                          # row of BBB's -60% day
TABLE_KEYS = {"window_stats": WINDOW_KEY, "path_days": [*pp.PATH_KEY, "day"], "path_summary": pp.PATH_KEY,
              "paired": WINDOW_KEY}


@pytest.fixture(scope="module")
def snapshot(tmp_path_factory):
    """The snapshot of tests/test_spark_equivalence.py."""
    root = tmp_path_factory.mktemp("snap")
    rng = np.random.default_rng(7)
    dates = nyse_sessions(ANCHOR, 61)                          # rows 0..60
    b = rng.normal(0, 0.02, 60)
    b[BREACH_ROW - 1] = -0.60                                  # 1 + 2r < 0: a 2x breach
    snap = write_snapshot(root, "snap", {
        "AAA": (dates, rng.normal(0, 0.02, 60)),
        "BBB": (dates, b),
        "CCC": (dates[:41], rng.normal(0, 0.03, 40)),
    }, unverified=[{"ticker": "BBB", "date": str(dates[BREACH_ROW])}])
    out = write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR), root / "w")
    return {"root": root, "snap": snap, "windows": out, "dates": dates}


def pandas_inputs(snapshot):
    config = json.loads((snapshot["windows"] / "config.json").read_text())
    return pp.read_inputs(snapshot["windows"], config)


def spark_inputs(spark, snapshot):
    return (spark.read.parquet(str(snapshot["windows"] / "windows.parquet")),
            spark.read.parquet(str(snapshot["snap"] / "daily_returns")))


def read(folder: Path) -> pa.Table:
    """A table as the collector reads it, with the ticker partition column as plain strings."""
    table = pq.read_table(folder)
    if "ticker" in table.column_names and pa.types.is_dictionary(table.schema.field("ticker").type):
        table = table.set_column(table.column_names.index("ticker"), "ticker", table["ticker"].cast(pa.string()))
    return table


@pytest.fixture(scope="module")
def runs(spark, snapshot, tmp_path_factory):
    """One materialized run of each pipeline on the same inputs."""
    from etf_risk import spark_pipeline
    spark_dir, pandas_dir = tmp_path_factory.mktemp("spark"), tmp_path_factory.mktemp("pandas")
    s = spark_pipeline.compute(spark, *spark_inputs(spark, snapshot), out_dir=spark_dir)
    p = pp.compute(*pandas_inputs(snapshot), out_dir=pandas_dir)
    return {"spark": s, "pandas": p, "spark_dir": spark_dir, "pandas_dir": pandas_dir}


def test_constants_and_path_day_columns_are_the_spark_pipelines():
    from etf_risk import spark_pipeline as sp
    assert (pp.LEVERAGES, pp.PATH_KEY, pp.INITIAL_NAV, pp.RTOL, pp.ATOL, pp.GAP_ATOL, pp.BOUND_TOL,
            pp.PAIRED_2X_PATH_VALUES) == (sp.LEVERAGES, sp.PATH_KEY, sp.INITIAL_NAV, sp.RTOL, sp.ATOL, sp.GAP_ATOL,
                                          sp.BOUND_TOL, sp.PAIRED_2X_PATH_VALUES)
    assert pp.PATH_DAY_COLUMNS == sp.PATH_DAY_SCHEMA.fieldNames()


def test_the_module_never_imports_pyspark():
    out = subprocess.run([sys.executable, "-c", "import sys, etf_risk.pandas_pipeline; print('pyspark' in sys.modules)"],
                         capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


@pytest.mark.spark
@pytest.mark.parametrize("table", list(TABLE_KEYS))
def test_every_table_matches_the_spark_pipeline(runs, table):
    ref, got = read(runs["spark_dir"] / table), read(runs["pandas_dir"] / table)
    assert [(f.name, f.type) for f in got.schema] == [(f.name, f.type) for f in ref.schema]
    problems, _ = cpm.compare_tables(ref, got, TABLE_KEYS[table], cpm.BREACH_FIELDS.get(table, []))
    assert not problems, problems
    assert got.num_rows > 0


@pytest.mark.spark
def test_the_check_counts_are_the_spark_pipelines_in_the_same_order(runs):
    assert json.dumps(runs["pandas"]["checks"]) == json.dumps(runs["spark"]["checks"])
    assert pp.total_violations(runs["pandas"]["checks"]) == 0 and runs["pandas"]["model_run"]


@pytest.mark.spark
def test_the_breach_and_its_pre_breach_values_are_kept_apart(runs):
    paired = runs["pandas"]["paired"]
    hit = paired[paired["breached_2x"].astype(bool)]
    assert len(hit) > 0 and hit["return_2x"].isna().all() and hit["mdd_2x"].isna().all()
    assert hit["mdd_2x_pre_breach"].notna().all() and (hit["ticker"] == "BBB").all()


@pytest.mark.spark
def test_a_dropped_return_row_stops_both_before_the_model(spark, snapshot):
    from pyspark.sql import functions as F

    from etf_risk import spark_pipeline as sp
    gone = snapshot["dates"][20]
    defs_s, returns_s = spark_inputs(spark, snapshot)
    s = sp.compute(spark, defs_s, returns_s.where(~((F.col("ticker") == "AAA") & (F.col("date") == F.lit(gone)))))
    defs_p, returns_p = pandas_inputs(snapshot)
    p = pp.compute(defs_p, returns_p[~((returns_p["ticker"] == "AAA") & (returns_p["date"] == pd.Timestamp(gone)))])
    assert p["model_run"] is False and s["model_run"] is False
    assert p["checks"] == s["checks"] and sum(p["checks"]["window_construction"].values()) > 0


@pytest.mark.spark
def test_a_changed_price_breaks_the_1x_identity_in_both(spark, snapshot, tmp_path):
    from pyspark.sql import functions as F

    from etf_risk import spark_pipeline as sp
    defs_p, returns_p = pandas_inputs(snapshot)
    target = snapshot["dates"][int(defs_p.query("ticker == 'AAA'")["entry_row"].iloc[1])]
    defs_s, returns_s = spark_inputs(spark, snapshot)
    changed_s = returns_s.withColumn("adjusted_price", F.when((F.col("ticker") == "AAA") & (F.col("date") == F.lit(target)),
                                                              F.col("adjusted_price") * 1.01).otherwise(F.col("adjusted_price")))
    s = sp.compute(spark, defs_s, changed_s, out_dir=tmp_path / "s")
    at = (returns_p["ticker"] == "AAA") & (returns_p["date"] == pd.Timestamp(target))
    returns_p.loc[at, "adjusted_price"] *= 1.01
    p = pp.compute(defs_p, returns_p)
    assert p["checks"] == s["checks"]
    assert p["checks"]["one_x_identity"]["return_1x_differs_from_price_return"] > 0


@pytest.mark.spark
def test_a_duplicated_leverage_row_breaks_pairing_in_both(spark, snapshot, runs):
    from etf_risk import spark_pipeline as sp
    s, p = runs["spark"], runs["pandas"]
    defs_s, _ = spark_inputs(spark, snapshot)
    doubled_s = s["summary"].unionByName(s["summary"].where("ticker = 'AAA' AND leverage = 2.0").limit(1))
    checks_s = sp.run_checks(s["stats"], s["path_days"], doubled_s, sp.pair_paths(doubled_s, s["stats"]), defs_s)
    defs_p, _ = pandas_inputs(snapshot)
    summary = p["summary"]
    doubled_p = pd.concat([summary, summary[(summary["ticker"] == "AAA") & (summary["leverage"] == 2.0)].head(1)],
                          ignore_index=True)
    checks_p = pp.run_checks(p["stats"], p["path_days"], doubled_p, pp.pair_paths(doubled_p, p["stats"]), defs_p)
    assert checks_p == checks_s and checks_p["pairing"]["not_one_row_per_leverage"] == 1


@pytest.mark.spark
def test_an_invalid_log_term_gives_a_null_exact_gap_not_a_partial_sum(runs):
    stats = runs["pandas"]["stats"]
    short = stats["n_gap_terms_valid"] < stats["window_days"]
    assert short.any()
    assert stats.loc[short, "exact_gap"].isna().all() and stats.loc[~short, "exact_gap"].notna().all()


@pytest.mark.spark
def test_pairing_refuses_leverages_other_than_1x_and_2x(runs):
    with pytest.raises(ValueError, match="1x with 2x"):
        pp.pair_paths(runs["pandas"]["summary"], runs["pandas"]["stats"], leverages=(1.0, 3.0))


def test_an_incomplete_window_stops_the_model_as_in_spark():
    pdf = pd.DataFrame({"window_kind": "rolling", "ticker": "AAA", "window_days": 3,
                        "entry_date": pd.Timestamp("2024-01-02"),
                        "date": pd.to_datetime(["2024-01-03", "2024-01-04"]), "daily_return": [0.01, -0.02]})
    with pytest.raises(ValueError, match="incomplete window"):
        pp.simulate_window(pdf, [1.0, 2.0], 100.0)


def test_nulls_follow_sql_rules_in_the_checks():
    assert pp._violations({"c": pd.Series([True, pd.NA, False], dtype="boolean")}) == {"c": 1}
    a = pd.Series([1, None, None, 2], dtype="Int64")
    b = pd.Series([1, None, 3, 3], dtype="Int64")
    assert pp._eq_null_safe(a, b).tolist() == [True, True, False, False]
    assert pp._violations({"c": a != b}) == {"c": 1}           # null != 3 is null, not a violation
    nav = pp._float(pd.Series([1.0, np.nan]))                  # a NaN from the model is stored as null
    assert nav.isna().tolist() == [False, True] and not pp._isnan(nav).any()


def test_main_writes_the_spark_pipelines_outputs_without_spark_fields(snapshot, tmp_path):
    from etf_risk import spark_pipeline as sp
    assert pp.main(["--windows", str(snapshot["windows"]), "--out-root", str(tmp_path / "out"), "--run-id", "r1"]) == 0
    run = tmp_path / "out" / "snap" / snapshot["windows"].name / "r1"
    assert {p.name for p in run.iterdir()} == {"window_stats", "path_days", "path_summary", "paired", "checks.json",
                                               "run.json"}
    assert {p.name for p in (run / "path_days").iterdir()} == {"ticker=AAA", "ticker=BBB", "ticker=CCC"}
    record = json.loads((run / "run.json").read_text())
    assert record["engine"] == "pandas" and record["status"] == "ok" and len(record["verified_sha256"]) == 5
    assert "spark" not in record and "stage_task_counts" not in record and "pipeline_options" not in record
    assert set(record["timings_seconds"]) == {"window_stats_and_construction_check", "model_and_path_days",
                                              "summaries_and_pairing", "checks", "total_in_process"}
    assert set(record["row_counts"]) == {"windows", "window_stats", "path_days", "summary", "paired"}
    assert record["environment"].keys() == sp.environment().keys()
    assert record["code"]["git_worktree_clean"] in (True, False) and "pandas_pipeline.py" in record["code"]["source_sha256"]
    assert pp.main(["--windows", str(snapshot["windows"]), "--out-root", str(tmp_path / "out"), "--run-id", "r1"]) == 2


def test_a_changed_input_file_stops_the_run_before_anything_is_computed(snapshot, tmp_path, monkeypatch):
    copy = tmp_path / "w"
    shutil.copytree(snapshot["windows"], copy)
    (copy / "windows.parquet").write_bytes((copy / "windows.parquet").read_bytes() + b" ")
    monkeypatch.setattr(pp, "compute", lambda *a, **k: pytest.fail("nothing may be computed"))
    assert pp.main(["--windows", str(copy), "--out-root", str(tmp_path / "out")]) == 3
    assert not (tmp_path / "out").exists()


def test_measure_runs_the_pandas_pipeline_in_fresh_processes(snapshot, tmp_path):
    out = tmp_path / "out"
    assert measure.main(["--pipeline", "pandas", "--repeats", "2", "--",
                         "--windows", str(snapshot["windows"]), "--out-root", str(out)]) == 0
    base = out / "snap" / snapshot["windows"].name
    protocol = json.loads(next(base.glob("protocol-*.json")).read_text())
    assert protocol["pipeline"] == "pandas" and protocol["runs_started"] == 2
    assert [r["status"] for r in protocol["runs"]] == ["ok", "ok"]
    record = json.loads((base / protocol["runs"][1]["run_id"] / "run.json").read_text())
    assert record["engine"] == "pandas" and record["measurement"]["peak_rss_total_bytes"] > 0
    kinds = set(record["measurement"]["peak_rss_by_kind_bytes"])
    assert "driver" in kinds and not kinds & {"spark_jvm", "python_worker"}   # no Spark; a sampled helper is other
    assert record["measurement"]["process_kinds"] == measure.PROCESS_KINDS


@pytest.mark.spark
def test_measure_still_records_the_spark_jvm_of_a_spark_pipeline_run(snapshot, tmp_path):
    out = tmp_path / "out"
    assert measure.main(["--repeats", "1", "--", "--windows", str(snapshot["windows"]), "--out-root", str(out)]) == 0
    base = out / "snap" / snapshot["windows"].name
    protocol = json.loads(next(base.glob("protocol-*.json")).read_text())
    record = json.loads((base / protocol["runs"][0]["run_id"] / "run.json").read_text())
    assert record["measurement"]["peak_rss_by_kind_bytes"]["spark_jvm"] > 0        # the JVM runs for seconds


def test_measure_without_the_flag_starts_the_spark_pipeline_and_records_no_pipeline(snapshot, tmp_path, monkeypatch):
    seen = {}

    def fake_protocol(make_command, run_dir_of, log_dir, repeats, **kwargs):
        seen["command"] = list(make_command("run-x"))
        log_dir.mkdir(parents=True, exist_ok=True)            # as run_protocol does
        return {"protocol_started": "20260101T000000Z", "threshold_bytes": 1, "total_ram_bytes": 1,
                "runs_started": 0, "runs": [], "stopped_early": False, "stop_reason": None}

    monkeypatch.setattr(measure, "run_protocol", fake_protocol)
    out = tmp_path / "out"
    assert measure.main(["--repeats", "1", "--", "--windows", str(snapshot["windows"]), "--out-root", str(out)]) == 0
    assert seen["command"][1:3] == ["-m", "etf_risk.spark_pipeline"] and seen["command"][-2:] == ["--run-id", "run-x"]
    protocol = json.loads(next((out / "snap" / snapshot["windows"].name).glob("protocol-*.json")).read_text())
    assert "pipeline" not in protocol
