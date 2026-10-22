"""The --cache option, run.json's cache section and the scan nodes of plans.json (docs/caching-experiment.md 4.1-4.2).

--cache changes no session setting, so these tests run the pipeline in the shared session of
conftest.py (local[2], 4 shuffle partitions). Every run must leave nothing cached there.

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot
from pyspark.sql import functions as F

from etf_risk import plans, spark_pipeline
from etf_risk.windows import build_definitions, write_definitions

ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"
sys.path.insert(0, str(ANALYSIS))
_spec = importlib.util.spec_from_file_location("collect_caching_measurements", ANALYSIS / "collect_caching_measurements.py")
ccm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ccm)

ANCHOR = "2024-01-02"
CONFIG_OF = {mode: config for config, mode in ccm.CACHE.items()}


@pytest.fixture(scope="module")
def windows(tmp_path_factory):
    root = tmp_path_factory.mktemp("caching")
    rng = np.random.default_rng(13)
    dates = nyse_sessions(ANCHOR, 61)
    b = rng.normal(0, 0.02, 60)
    b[29] = -0.60                                              # a 2x breach
    snap = write_snapshot(root, "snap", {"AAA": (dates, rng.normal(0, 0.02, 60)), "BBB": (dates, b)},
                          unverified=[{"ticker": "BBB", "date": str(dates[30])}])
    return {"windows": write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR),
                                         root / "w"), "snap": snap, "dates": dates}


def run_dir(out_root: Path, windows: Path, run_id: str) -> Path:
    return out_root / "snap" / windows.name / run_id


def in_session(windows: Path, out_root: Path, run_id: str, *flags: str) -> tuple[int, dict, Path]:
    code = spark_pipeline.main(["--windows", str(windows), "--out-root", str(out_root), "--run-id", run_id, *flags])
    run = run_dir(out_root, windows, run_id)
    return code, json.loads((run / "run.json").read_text()), run


@pytest.fixture(scope="module")
def runs(spark, windows, tmp_path_factory):
    """One run per mode, with plans, in the shared session."""
    out = tmp_path_factory.mktemp("runs")
    return {mode: in_session(windows["windows"], out, mode, "--cache", mode, "--record-plans") for mode in spark_pipeline.CACHE_MODES}


def test_the_option_defaults_to_no_cache_and_rejects_other_values():
    parser = spark_pipeline.build_parser()
    assert parser.parse_args(["--windows", "w"]).cache is None
    assert parser.parse_args(["--windows", "w", "--cache", "members-checks"]).cache == "members-checks"
    with pytest.raises(SystemExit):
        parser.parse_args(["--windows", "w", "--cache", "everything"])
    with pytest.raises(ValueError):
        spark_pipeline.RunCaches(None, "everything")
    assert set(spark_pipeline.CACHE_TABLES) == set(spark_pipeline.CACHE_MODES) == set(CONFIG_OF)
    assert spark_pipeline.CACHE_TABLES["members-checks"] == ccm.TABLES
    assert spark_pipeline.FILL_DESCRIPTION.format("members") == ccm.FILL_PREFIX + "members"


def test_scan_nodes_are_recognized_and_the_plans_format_is_2():
    assert plans.is_scan("InMemoryTableScan") and plans.is_scan("Scan parquet ") and plans.is_scan("Scan csv ")
    assert not plans.is_scan("Exchange") and not plans.is_scan("LocalTableScan") and plans.FORMAT == 2


@pytest.mark.spark
def test_without_the_option_run_json_is_as_before(spark, windows, tmp_path):
    code, record, _ = in_session(windows["windows"], tmp_path, "plain")
    assert code == 0 and "cache" not in record and "pipeline_options" not in record
    code, record, _ = in_session(windows["windows"], tmp_path, "plans", "--record-plans")
    assert code == 0 and "cache" not in record and record["pipeline_options"] == {
        "shuffle_partitions": None, "coalesce": None, "record_plans": True}
    assert spark_pipeline.storage_info(spark) == []


@pytest.mark.spark
@pytest.mark.parametrize("mode", spark_pipeline.CACHE_MODES)
def test_each_mode_fills_and_releases_its_tables_and_passes_the_cache_check(spark, windows, runs, mode):
    code, record, run = runs[mode]
    assert code == 0 and record["status"] == "ok", record.get("error")
    cache = record["cache"]
    assert record["pipeline_options"]["cache"] == mode and cache["mode"] == mode
    assert set(cache["tables"]) == set(spark_pipeline.CACHE_TABLES[mode])
    for entry in cache["tables"].values():
        assert entry["released_by"] == "plan" and entry["cached_after_release"] == [] and entry["rows"] > 0
        (rdd,) = entry["after_fill"]
        assert 0 < rdd["cached_partitions"] == rdd["partitions"] and rdd["storage_level"] == ccm.STORAGE_LEVEL
    assert [s["at"] for s in cache["snapshots"]] == list(ccm.PHASES) and cache["snapshots"][-1]["cached"] == []
    assert spark_pipeline.storage_info(spark) == []                     # nothing left in the shared session
    doc = json.loads((run / "plans.json").read_text())
    fills = {e["description"].removeprefix(ccm.FILL_PREFIX): e["phase"] for e in doc["executions"]
             if e["description"].startswith(ccm.FILL_PREFIX)}
    assert fills == {name: ccm.FILLED_IN[name] for name in spark_pipeline.CACHE_TABLES[mode]}
    others = {e["description"] for e in doc["executions"] if not e["description"].startswith(ccm.FILL_PREFIX)}
    assert others <= {*ccm.PHASES, "row counts for run.json"}          # each phase's description is restored
    config = CONFIG_OF[mode]
    assert ccm.check_cache("r", config, record, doc, ccm.member_rows(windows["windows"])) == []
    other = {"A": "B", "B": "C", "C": "A"}[config]
    assert ccm.check_cache("r", other, record, doc, ccm.member_rows(windows["windows"]))


@pytest.mark.spark
@pytest.mark.parametrize("mode", ["members", "members-checks"])
def test_cached_runs_write_the_same_tables_as_an_uncached_run(runs, mode):
    reference, run = runs["none"][2], runs[mode][2]
    for table, key in ccm.TABLE_KEYS.items():
        problems, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(run, table), key,
                                             ccm.cpm.BREACH_FIELDS.get(table, []))
        assert not problems, (table, problems)


@pytest.mark.spark
def test_a_failure_after_a_fill_releases_every_cache(spark, windows, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("forced failure after the fills")

    monkeypatch.setattr(spark_pipeline, "simulate_windows", fail)
    code, record, _ = in_session(windows["windows"], tmp_path, "boom", "--cache", "members-checks")
    assert code == 2 and record["status"] == "failed" and "forced failure" in record["error"]
    tables = record["cache"]["tables"]
    assert set(tables) == {"members", "window_stats"}                    # filled before the failure
    assert all(t["released_by"] == "cleanup" and t["released_in"] is None and t["cached_after_release"] == []
               for t in tables.values())
    assert spark_pipeline.storage_info(spark) == []


@pytest.mark.spark
def test_the_early_return_after_a_failed_construction_check_leaves_caches_to_the_cleanup(spark, windows):
    defs = spark.read.parquet(str(windows["windows"] / "windows.parquet"))
    returns = spark.read.parquet(str(windows["snap"] / "daily_returns"))
    gone = windows["dates"][20]
    caches = spark_pipeline.RunCaches(spark, "members-checks")
    result = spark_pipeline.compute(spark, defs, returns.where(~((F.col("ticker") == "AAA") & (F.col("date") == F.lit(gone)))),
                                    caches=caches)
    assert result["model_run"] is False and set(caches.held) == {"members", "window_stats"}
    caches.release_all()
    assert all(t["released_by"] == "cleanup" for t in caches.tables.values()) and spark_pipeline.storage_info(spark) == []
