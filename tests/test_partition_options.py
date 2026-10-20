"""Partition flags, the existing-session guard and plan capture (docs/partition-experiment.md 4.1-4.2).

Tests that pass --shuffle-partitions or --coalesce run the pipeline as a separate process, as
etf_risk.measure does. PySpark applies a session builder's options to an existing session, so
these flags must never reach the shared session of conftest.py (local[2], 4 shuffle partitions).

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import plans, spark_pipeline
from etf_risk.windows import build_definitions, write_definitions

REPO = Path(__file__).resolve().parents[1]
ANCHOR = "2024-01-02"
PARTITIONS = "spark.sql.shuffle.partitions"
COALESCE = "spark.sql.adaptive.coalescePartitions.enabled"


@pytest.fixture(scope="module")
def windows(tmp_path_factory):
    root = tmp_path_factory.mktemp("partitions")
    rng = np.random.default_rng(11)
    dates = nyse_sessions(ANCHOR, 61)
    snap = write_snapshot(root, "snap", {"AAA": (dates, rng.normal(0, 0.02, 60)),
                                         "BBB": (dates, rng.normal(0, 0.02, 60))})
    return write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR), root / "w")


def run_dir(out_root: Path, windows: Path, run_id: str) -> Path:
    return out_root / "snap" / windows.name / run_id


def in_session(windows: Path, out_root: Path, run_id: str, *flags: str) -> int:
    return spark_pipeline.main(["--windows", str(windows), "--out-root", str(out_root), "--run-id", run_id, *flags])


def fresh_process(windows: Path, out_root: Path, run_id: str, *flags: str) -> tuple[dict, Path]:
    """The pipeline in a new process, as etf_risk.measure starts it."""
    proc = subprocess.run([sys.executable, "-m", "etf_risk.spark_pipeline", "--windows", str(windows),
                           "--out-root", str(out_root), "--run-id", run_id, *flags],
                          cwd=REPO, capture_output=True, text=True, timeout=600)
    assert proc.returncode == 0, proc.stderr[-2000:]
    run = run_dir(out_root, windows, run_id)
    return json.loads((run / "run.json").read_text()), run


def requested_counts(doc: dict) -> set[int]:
    return {x["requested"] for e in doc["executions"] for x in e["exchanges"]
            if x["partitioning"] in ("hashpartitioning", "rangepartitioning")}


def runtime_counts(doc: dict) -> set[int | None]:
    """The partitions each hash or range exchange wrote at runtime (its "number of partitions" metric)."""
    return {x["partitions"] for e in doc["executions"] for x in e["exchanges"]
            if x["partitioning"] in ("hashpartitioning", "rangepartitioning")}


def coalesced_reads(doc: dict) -> list[dict]:
    return [r for e in doc["executions"] for r in e["shuffle_reads"] if "coalesced" in r["mark"]]


def test_flags_default_to_spark_settings_and_reject_bad_values():
    parse = spark_pipeline.build_parser().parse_args
    args = parse(["--windows", "w"])
    assert (args.shuffle_partitions, args.coalesce, args.record_plans) == (None, None, False)
    args = parse(["--windows", "w", "--shuffle-partitions", "8", "--coalesce", "off", "--record-plans"])
    assert (args.shuffle_partitions, args.coalesce, args.record_plans) == (8, "off", True)
    for bad in (["--shuffle-partitions", "0"], ["--shuffle-partitions", "-2"], ["--shuffle-partitions", "x"],
                ["--coalesce", "yes"]):
        with pytest.raises(SystemExit):
            parse(["--windows", "w", *bad])


def test_plan_text_parsers():
    assert plans.plan_status("AdaptiveSparkPlan (9)\n(9) AdaptiveSparkPlan\nArguments: isFinalPlan=true\n") == (True, True)
    assert plans.plan_status("Arguments: isFinalPlan=true\nArguments: isFinalPlan=false\n") == (True, False)
    assert plans.plan_status("== Physical Plan ==\nLocalTableScan (1)\n") == (False, None)     # not adaptive
    assert plans.exchange_partitioning(
        "Exchange hashpartitioning(window_kind#1, ticker#2, entry_date#4, 200), ENSURE_REQUIREMENTS, [plan_id=7]"
    ) == ("hashpartitioning", 200)
    assert plans.exchange_partitioning(
        "Exchange rangepartitioning(date#5 ASC NULLS FIRST, 8), ENSURE_REQUIREMENTS, [plan_id=3]") == ("rangepartitioning", 8)
    assert plans.exchange_partitioning("Exchange SinglePartition, ENSURE_REQUIREMENTS, [plan_id=84]") == ("single", None)
    assert plans.read_mark("AQEShuffleRead coalesced") == "coalesced" and plans.read_mark("AQEShuffleRead") == ""
    assert plans.metric_count("1,024") == 1024 and plans.metric_count(None) is None and plans.metric_count("-") is None


@pytest.mark.spark
def test_partition_flags_are_refused_inside_an_existing_session(spark, windows, tmp_path):
    for flags in (["--shuffle-partitions", "8"], ["--coalesce", "off"]):
        assert in_session(windows, tmp_path / "out", "r1", *flags) == 2
    assert not (tmp_path / "out").exists()
    assert spark.conf.get(PARTITIONS) == "4"            # the shared session kept its settings


@pytest.mark.spark
def test_without_the_new_flags_run_json_is_as_before(spark, windows, tmp_path):
    assert in_session(windows, tmp_path / "out", "r1") == 0
    run = run_dir(tmp_path / "out", windows, "r1")
    record = json.loads((run / "run.json").read_text())
    assert "pipeline_options" not in record and "plan_capture" not in record
    assert "plan_capture" not in record["timings_seconds"] and not (run / "plans.json").exists()


@pytest.mark.spark
def test_plans_in_a_shared_session_cover_only_the_runs_own_executions(spark, windows, tmp_path):
    out = tmp_path / "out"
    for run_id in ("r1", "r2"):
        assert in_session(windows, out, run_id, "--record-plans") == 0
    first, second = (json.loads((run_dir(out, windows, r) / "plans.json").read_text()) for r in ("r1", "r2"))
    record = json.loads((run_dir(out, windows, "r2") / "run.json").read_text())
    assert record["plan_capture"]["status"] == "ok" and record["timings_seconds"]["plan_capture"] > 0
    assert record["pipeline_options"] == {"shuffle_partitions": None, "coalesce": None, "record_plans": True}
    ids = [e["id"] for e in second["executions"]]
    assert min(ids) > max(e["id"] for e in first["executions"])
    assert ids == list(range(second["first_execution_id"], second["first_execution_id"] + len(ids)))
    assert {e["phase"] for e in second["executions"]} >= {"window_stats", "model", "summaries", "checks", "bookkeeping"}
    assert all(e["final"] for e in second["executions"] if e["adaptive"]) and not any(e["error"] for e in second["executions"])
    assert requested_counts(second) == runtime_counts(second) == {4}     # the shared session's own setting
    # timing boundaries: the capture adds its own timing and stays outside the phases, which are unchanged
    timings = record["timings_seconds"]
    phases = ["session_start", "window_stats_and_construction_check", "model_and_path_days", "summaries_and_pairing",
              "checks"]
    assert set(timings) == {*phases, "plan_capture", "total_in_process"}
    assert sum(timings[p] for p in phases) + timings["plan_capture"] <= timings["total_in_process"]


@pytest.mark.spark
def test_a_capture_failure_leaves_the_status_and_exit_code(spark, windows, tmp_path, monkeypatch):
    def fail(*args, **kwargs):
        raise plans.PlanCaptureError("simulated")
    monkeypatch.setattr(plans, "capture", fail)
    assert in_session(windows, tmp_path / "out", "r1", "--record-plans") == 0
    run = run_dir(tmp_path / "out", windows, "r1")
    record = json.loads((run / "run.json").read_text())
    assert record["status"] == "ok" and "error" not in record
    assert record["plan_capture"]["status"] == "failed" and "simulated" in record["plan_capture"]["error"]
    assert not (run / "plans.json").exists() and "plan_capture" in record["timings_seconds"]


@pytest.mark.spark
def test_a_fresh_process_without_flags_keeps_spark_defaults(windows, tmp_path):
    record, run = fresh_process(windows, tmp_path / "out", "r1")
    assert (record["spark"][PARTITIONS], record["spark"][COALESCE]) == ("200", "true")
    assert "pipeline_options" not in record and not (run / "plans.json").exists()


@pytest.mark.spark
def test_a_fresh_process_honors_the_flags_without_coalescing(windows, tmp_path):
    record, run = fresh_process(windows, tmp_path / "out", "r1",
                                "--shuffle-partitions", "8", "--coalesce", "off", "--record-plans")
    spark_settings = record["spark"]
    assert (spark_settings[PARTITIONS], spark_settings[COALESCE], spark_settings["spark.sql.adaptive.enabled"]) == \
           ("8", "false", "true")
    assert record["pipeline_options"] == {"shuffle_partitions": 8, "coalesce": "off", "record_plans": True}
    doc = json.loads((run / "plans.json").read_text())
    assert record["plan_capture"]["status"] == "ok" and doc["first_execution_id"] == 0
    assert doc["explain_mode"].lower() == "formatted" and doc["spark_version"] == spark_settings["spark_version"]
    assert any(e["adaptive"] for e in doc["executions"]) and all(e["final"] for e in doc["executions"] if e["adaptive"])
    assert requested_counts(doc) == runtime_counts(doc) == {8} and not coalesced_reads(doc)


@pytest.mark.spark
def test_a_fresh_process_with_coalescing_records_the_partitions_read(windows, tmp_path):
    record, run = fresh_process(windows, tmp_path / "out", "r1",
                                "--shuffle-partitions", "200", "--coalesce", "on", "--record-plans")
    doc = json.loads((run / "plans.json").read_text())
    assert requested_counts(doc) == runtime_counts(doc) == {200}           # coalescing changes reads, not exchanges
    reads = coalesced_reads(doc)
    assert reads and all(1 <= r["partitions"] < 200 for r in reads)
