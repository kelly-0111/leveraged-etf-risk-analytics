"""The shuffle-partition collector: table comparison, plan and settings checks, and a whole fake batch.

No Spark: the batch is built from small JSON records and Parquet tables written here.

AI contribution: written with Claude Code (Opus 5.5).
"""
import csv
import importlib.util
import json
from datetime import date
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from etf_risk.ingest import sha256_file

ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"
_spec = importlib.util.spec_from_file_location("collect_partition_measurements",
                                               ANALYSIS / "collect_partition_measurements.py")
cpm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpm)

KEY = ["window_kind", "ticker", "window_days", "entry_date"]
BREACH = ["breached_2x"]


def paired(rows=None, **changes) -> pa.Table:
    rows = rows or [("rolling", "AAA", 10, date(2024, 1, 2), False, 0.10, 2),
                    ("rolling", "AAA", 10, date(2024, 1, 5), True, None, 2),
                    ("rolling", "BBB", 10, date(2024, 1, 2), False, -0.05, 2)]
    columns = dict(zip(["window_kind", "ticker", "window_days", "entry_date", "breached_2x", "return_2x", "n_paths"],
                       map(list, zip(*rows))))
    columns.update(changes)
    return pa.table({
        "window_kind": pa.array(columns["window_kind"], pa.string()), "ticker": pa.array(columns["ticker"], pa.string()),
        "window_days": pa.array(columns["window_days"], pa.int32()),
        "entry_date": pa.array(columns["entry_date"], pa.date32()),
        "breached_2x": pa.array(columns["breached_2x"], pa.bool_()),
        "return_2x": pa.array(columns["return_2x"], pa.float64()), "n_paths": pa.array(columns["n_paths"], pa.int64()),
    })


def compare(run: pa.Table) -> list[str]:
    return cpm.compare_tables(paired(), run, KEY, BREACH)[0]


def test_identical_and_reordered_tables_pass():
    assert compare(paired()) == []
    assert compare(paired().take([2, 0, 1])) == []          # rows are matched by key, not by position


def test_floats_within_the_tolerance_pass_and_differences_are_reported():
    problems, diffs = cpm.compare_tables(paired(), paired(return_2x=[0.10 * (1 + 1e-13), None, -0.05]), KEY, BREACH)
    assert problems == [] and 0 < diffs["return_2x"]["max_rel"] < 1e-12


@pytest.mark.parametrize("run, expected", [
    (paired(return_2x=[0.10 * (1 + 1e-6), None, -0.05]), "return_2x: 1 values outside"),
    (paired(return_2x=[float("nan"), None, -0.05]), "return_2x: NaN in 1 rows"),
    (paired(return_2x=[0.10, 0.20, -0.05]), "return_2x: null in 1 rows"),
    (paired(breached_2x=[False, False, False]), "breach field breached_2x: 1 values differ"),
    (paired(n_paths=[2, 2, 3]), "n_paths: 1 values differ"),
    (paired().slice(0, 2), "keys differ: 1 missing, 0 extra"),
    (paired().take([0, 1, 2, 2]), "run: 1 duplicate keys"),
    (paired(ticker=["AAA", None, "BBB"]), "run: null in key columns ['ticker']"),
    (paired().append_column("extra", pa.array([1, 2, 3])), "columns differ: missing [], extra ['extra']"),
])
def test_each_kind_of_difference_is_a_problem(run, expected):
    assert any(expected in p for p in compare(run)), compare(run)


def execution(i: int, requested: int, marks=(), adaptive: bool = True, final: str = "true", error=None,
              ran="as requested") -> dict:
    """One plans.json execution with a hash exchange; `ran` is its runtime partition count."""
    written = requested if ran == "as requested" else ran
    if adaptive:
        plan = (f"AdaptiveSparkPlan (9)\n\n(5) Exchange\nArguments: hashpartitioning(k#1, {requested}), "
                "ENSURE_REQUIREMENTS, [plan_id=3]\n\n"
                + "".join(f"(7) AQEShuffleRead\nArguments: {mark}\n\n" for mark in marks)
                + f"(9) AdaptiveSparkPlan\nArguments: isFinalPlan={final}\n")
    else:
        plan = "== Physical Plan ==\nLocalTableScan (1)\n"
    return {"id": i, "phase": "model", "jobs": [i], "error": error, "adaptive": adaptive,
            "final": (final == "true") if adaptive else None,
            "exchanges": [{"partitioning": "hashpartitioning", "requested": requested, "partitions": written,
                           "metrics": {}, "desc": ""}] if adaptive else [],
            "shuffle_reads": [{"mark": mark, "partitions": 8, "metrics": {}} for mark in marks],
            "joins": ["BroadcastHashJoin"], "plan": plan}


def plans_doc(executions, explain="FORMATTED", first=0, version="4.2.0") -> dict:
    return {"format": 1, "spark_version": version, "explain_mode": explain, "first_execution_id": first,
            "executions": executions}


OK = {"status": "ok"}


def test_plan_checks_pass_for_each_configuration():
    assert cpm.check_plans("r", "A", OK, plans_doc([execution(0, 200, ["coalesced"]), execution(1, 0, adaptive=False)])) == []
    assert cpm.check_plans("r", "B", OK, plans_doc([execution(0, 200, ["local"])])) == []
    assert cpm.check_plans("r", "C", OK, plans_doc([execution(0, 8)])) == []


@pytest.mark.parametrize("config, capture, doc, expected", [
    ("B", OK, plans_doc([execution(0, 200, ["coalesced"])]), "marked coalesced"),
    ("C", OK, plans_doc([execution(0, 200, ["coalesced and skewed"])]), "marked coalesced"),
    ("C", OK, plans_doc([execution(0, 200)]), "request [200] partitions, not 8"),
    ("C", OK, plans_doc([execution(0, 8, ran=200)]), "wrote [200] partitions at runtime, not 8"),
    ("A", OK, plans_doc([execution(0, 200, ran=None)]), "wrote [None] partitions at runtime"),
    ("A", OK, plans_doc([execution(0, 200, final="false")]), "adaptive plan not final"),
    ("A", OK, plans_doc([execution(0, 200, error="boom")]), "ended with an error"),
    ("A", OK, plans_doc([execution(0, 200), execution(2, 200)]), "without gaps"),
    ("A", OK, plans_doc([execution(3, 200)], first=3), "without gaps"),
    ("A", OK, plans_doc([execution(0, 200)], explain="extended"), "explain mode"),
    ("A", OK, plans_doc([execution(0, 200)], version="4.1.0"), "plans from Spark 4.1.0"),
    ("A", {"status": "failed"}, None, "plan capture failed"),
    ("A", None, None, "plan capture missing"),
    ("A", OK, None, "plans.json missing"),
])
def test_plan_problems(config, capture, doc, expected):
    problems = cpm.check_plans("r", config, capture, doc)
    assert any(expected in p for p in problems), problems


def code(source="s1", lock="l1", commit="c1", clean=True) -> dict:
    return {"source_sha256": {"spark_pipeline.py": source}, "uv_lock_sha256": lock, "git_commit": commit,
            "git_worktree_clean": clean}


def test_code_state_needs_matching_hashes_but_not_the_same_commit():
    problems, commits = cpm.check_code_state([("a", code()), ("b", code(commit="c2"))])
    assert problems == [] and commits == ["c1", "c2"]
    assert "hashes differ" in cpm.check_code_state([("a", code()), ("b", code(source="s2"))])[0][0]
    assert "hashes differ" in cpm.check_code_state([("a", code()), ("b", code(lock="l2"))])[0][0]
    assert "uncommitted changes" in cpm.check_code_state([("a", code(clean=False))])[0][0]
    assert "no code record" in cpm.check_code_state([("a", None)])[0][0]


# --- a whole fake batch ----------------------------------------------------------------

STAMPS = ["20261020T010000Z", "20261020T011000Z", "20261020T012000Z", "20261020T013000Z", "20261020T014000Z",
          "20261020T015000Z"]


@pytest.fixture
def windows(tmp_path):
    snap = tmp_path / "snap"
    (snap / "daily_returns").mkdir(parents=True)
    (snap / "daily_returns" / "AAA.parquet").write_bytes(b"returns")
    (snap / "quality_report.json").write_text("{}")
    wdir = tmp_path / "windows" / "w"
    wdir.mkdir(parents=True)
    (wdir / "windows.parquet").write_bytes(b"windows")
    config = {"snapshot": "snap", "snapshot_dir": str(snap), "windows_file": "windows.parquet",
              "windows_sha256": sha256_file(wdir / "windows.parquet"),
              "inputs_sha256": {rel: sha256_file(snap / rel) for rel in ("daily_returns/AAA.parquet", "quality_report.json")}}
    (wdir / "config.json").write_text(json.dumps(config))
    return wdir


def write_protocol(batch: Path, windows: Path, config_name: str, stamp: str, repeats: int = 2, status: str = "ok",
                   run_code=None, spark_changes=None, table=None) -> None:
    folder = batch / config_name / "snap" / windows.name
    folder.mkdir(parents=True, exist_ok=True)
    config = json.loads((windows / "config.json").read_text())
    verified = {str(windows / "windows.parquet"): config["windows_sha256"],
                **{f"{config['snapshot_dir']}/{rel}": sha for rel, sha in config["inputs_sha256"].items()}}
    requested = int(cpm.CONFIGS[config_name][cpm.PARTITIONS])
    entries = []
    for i in range(1, repeats + 1):
        run_id = f"run-{stamp}-{i}"
        run_dir = folder / run_id
        summary = paired().append_column("leverage", pa.array([2.0, 2.0, 2.0]))       # its key adds leverage
        for name, tab in (("paired", table if table is not None else paired()), ("path_summary", summary)):
            (run_dir / name).mkdir(parents=True)
            pq.write_table(tab, run_dir / name / "part-0.parquet")
        run_status = status if i == repeats else "ok"
        record = {
            "run_id": run_id, "status": run_status, "code": run_code or code(), "windows_config": config,
            "verified_sha256": verified, "environment": {"python": "3.12"},
            "spark": {**cpm.CONFIGS[config_name], "default_parallelism": 8, "jvm_max_heap_bytes": 1,
                      **(spark_changes or {})},
            "pipeline_options": cpm.OPTIONS[config_name],
            "row_counts": {"windows": 3, "window_stats": 3, "path_days": 6, "summary": 3, "paired": 3},
            "stage_task_counts": {g: {"jobs": 1, "stages": 1, "tasks": 2} for g in cpm.PHASES},
            "timings_seconds": {"session_start": 1.0, "window_stats_and_construction_check": 1.0,
                                "model_and_path_days": 1.0, "summaries_and_pairing": 1.0, "checks": 1.0,
                                "total_in_process": 6.0, "plan_capture": 0.5},
            "checks": {"group": {"violation": 0}}, "plan_capture": {"status": "ok"},
            "measurement": {"warmup": i == 1, "exit_code": 0, "protocol_status": run_status, "wall_seconds": 7.25,
                            "started_at_utc": "2026-10-20T01:00:00+00:00", "free_memory_before_bytes": 3 * 2**30,
                            "peak_rss_total_bytes": 2**30, "peak_rss_by_kind_bytes": {"driver": 1}, "samples": 4,
                            "max_processes_seen": 5, "threshold_first_exceeded_after_seconds": None},
        }
        (run_dir / "run.json").write_text(json.dumps(record))
        marks = ["coalesced"] if config_name == "A" else []
        (run_dir / "plans.json").write_text(json.dumps(plans_doc([execution(0, requested, marks)])))
        entries.append({"run_id": run_id, "warmup": i == 1, "status": run_status, "exit_code": 0})
    protocol = {"protocol_started": stamp, "code": code(), "repeats_requested": repeats, "runs_started": repeats,
                "stopped_early": status != "ok", "runs": entries}
    (folder / f"protocol-{stamp}.json").write_text(json.dumps(protocol))


def write_positions(batch: Path, lines: list[tuple[int, str, str]]) -> None:
    with (batch / "positions.tsv").open("w", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(cpm.POSITION_FIELDS)
        for position, config_name, stamp in lines:
            writer.writerow([position, config_name, stamp, 0, "ok", "2026-10-20T00:00:00Z"])


def full_batch(tmp_path, windows, overrides=None):
    """All six positions, each with a complete protocol; `overrides` maps a position to write_protocol options."""
    batch = tmp_path / "batch-1"
    for position, (config_name, stamp) in enumerate(zip(cpm.ORDER, STAMPS), start=1):
        write_protocol(batch, windows, config_name, stamp, **(overrides or {}).get(position, {}))
    write_positions(batch, [(p, c, s) for p, (c, s) in enumerate(zip(cpm.ORDER, STAMPS), start=1)])
    return batch


def failed(acceptance: dict) -> dict:
    return {name: r["problems"] for name, r in acceptance["criteria"].items() if not r["ok"]}


def test_a_complete_batch_passes_and_gives_one_row_per_run(tmp_path, windows):
    batch = full_batch(tmp_path, windows)
    rows, acceptance = cpm.collect(batch, windows, None, repeats=2)
    assert acceptance["all_ok"], failed(acceptance)
    assert len(rows) == 12 and all(r["used"] for r in rows)
    reference = [r for r in rows if r["paired_vs_reference"] == "reference"]
    assert [r["run_id"] for r in reference] == [f"run-{STAMPS[0]}-2"]
    assert {r["wall_excl_capture_s"] for r in rows} == {6.75}
    assert {r["coalesced_reads"] for r in rows if r["config"] == "A"} == {1}
    assert {(r["config"], r["exchanges_model"], r["reads_model"]) for r in rows} == {
        ("A", "200", "coalesced:8"), ("B", "200", ""), ("C", "8", "")}
    assert cpm.main(["--batch", str(batch), "--windows", str(windows), "--stride-run", "none", "--repeats", "2"]) == 0
    with (batch / "measurements.csv").open(newline="") as f:
        lines = list(csv.reader(f))
    assert lines[0] == cpm.FIELDS and len(lines) == 13
    assert json.loads((batch / "acceptance.json").read_text())["all_ok"]


def test_a_rerun_replaces_the_failed_protocol_at_its_position(tmp_path, windows):
    batch = full_batch(tmp_path, windows)
    write_protocol(batch, windows, "B", "20261020T010500Z", status="failed")      # position 2's first try
    write_positions(batch, [(1, "A", STAMPS[0]), (2, "B", "20261020T010500Z")]
                    + [(p, c, s) for p, (c, s) in enumerate(zip(cpm.ORDER, STAMPS), start=1) if p > 1])
    rows, acceptance = cpm.collect(batch, windows, None, repeats=2)
    assert acceptance["all_ok"], failed(acceptance)
    assert acceptance["used_protocols"]["2"] == STAMPS[1]
    assert {r["used"] for r in rows if r["protocol_id"] == "20261020T010500Z"} == {False}


@pytest.mark.parametrize("overrides, criterion, expected", [
    ({2: {"spark_changes": {cpm.COALESCE: "true"}}}, "3 settings", "configuration B needs 'false'"),
    ({3: {"run_code": code(source="s2")}}, "1 code state", "hashes differ"),
    ({4: {"table": paired(return_2x=[0.2, None, -0.05])}}, "4 results", "values outside"),
    ({5: {"status": "failed"}}, "5 completeness", "ended failed"),
])
def test_a_planted_problem_fails_its_criterion(tmp_path, windows, overrides, criterion, expected):
    _, acceptance = cpm.collect(full_batch(tmp_path, windows, overrides), windows, None, repeats=2)
    problems = acceptance["criteria"][criterion]["problems"]
    assert any(expected in p for p in problems), failed(acceptance)


def test_missing_and_unlisted_protocols_fail_completeness(tmp_path, windows):
    batch = full_batch(tmp_path, windows)
    write_positions(batch, [(p, c, s) for p, (c, s) in enumerate(zip(cpm.ORDER, STAMPS), start=1) if p < 6])
    problems = cpm.collect(batch, windows, None, repeats=2)[1]["criteria"]["5 completeness"]["problems"]
    assert any("position 6 (A) has no protocol" in p for p in problems)
    assert any(f"protocol {STAMPS[5]} is not in positions.tsv" in p for p in problems)


def test_changed_inputs_fail_criterion_2(tmp_path, windows):
    batch = full_batch(tmp_path, windows)
    (windows / "windows.parquet").write_bytes(b"changed")
    problems = cpm.collect(batch, windows, None, repeats=2)[1]["criteria"]["2 inputs"]["problems"]
    assert any("changed after the session" in p for p in problems)


def test_check_protocol_with_a_configuration_also_checks_settings_and_plans(tmp_path, windows):
    batch = full_batch(tmp_path, windows, {2: {"spark_changes": {cpm.COALESCE: "true"}}})
    a = next((batch / "A").rglob(f"protocol-{STAMPS[0]}.json"))
    b = next((batch / "B").rglob(f"protocol-{STAMPS[1]}.json"))
    assert cpm.check_protocol(a, "A") == [] and cpm.check_protocol(b) == []      # without --config: plans only
    assert any("configuration B needs 'false'" in p for p in cpm.check_protocol(b, "B"))
    assert any("marked coalesced" in p for p in cpm.check_protocol(a, "B"))       # A's plans read as B's
    assert cpm.main(["--check-protocol", str(b), "--config", "B"]) == 1


def test_check_protocol_reports_runs_without_plans(tmp_path, windows):
    batch = full_batch(tmp_path, windows)
    protocol = next((batch / "A").rglob(f"protocol-{STAMPS[0]}.json"))
    assert cpm.check_protocol_plans(protocol) == []
    (protocol.parent / f"run-{STAMPS[0]}-2" / "plans.json").unlink()
    assert cpm.check_protocol_plans(protocol) == [f"run-{STAMPS[0]}-2: plans.json missing"]
    assert cpm.main(["--check-protocol", str(protocol)]) == 1
