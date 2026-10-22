"""The caching collector (analysis/collect_caching_measurements.py) on a fake batch built from real runs.

The fixture runs the pipeline once per configuration in a fresh process, as etf_risk.measure starts
it, with --cache and --record-plans. It then copies those runs into an A-B-C-C-B-A batch of two runs
per protocol, with protocol JSONs, measurement sections and positions.tsv as measure and the session
helpers write them. The records' worktree is marked clean, because the tests run on uncommitted
code. The collector must accept that batch, and each planted problem must fail the criterion that
covers it. Runs that failed or were aborted without their outputs must be reported, not stop it.

AI contribution: written with Claude Code (Opus 5.5).
"""
import csv
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk.windows import build_definitions, write_definitions

REPO = Path(__file__).resolve().parents[1]
ANALYSIS = REPO / "analysis"
sys.path.insert(0, str(ANALYSIS))
_spec = importlib.util.spec_from_file_location("collect_caching_measurements", ANALYSIS / "collect_caching_measurements.py")
ccm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ccm)

pytestmark = pytest.mark.spark
ANCHOR = "2024-01-02"
REPEATS = 2
STAMPS = [f"20261022T1{i}0000Z" for i in range(6)]


@pytest.fixture(scope="module")
def windows(tmp_path_factory):
    root = tmp_path_factory.mktemp("snap")
    rng = np.random.default_rng(17)
    dates = nyse_sessions(ANCHOR, 61)
    b = rng.normal(0, 0.02, 60)
    b[29] = -0.60                                              # a 2x breach
    snap = write_snapshot(root, "snap", {"AAA": (dates, rng.normal(0, 0.02, 60)), "BBB": (dates, b)},
                          unverified=[{"ticker": "BBB", "date": str(dates[30])}])
    return write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR), root / "w")


@pytest.fixture(scope="module")
def templates(windows, tmp_path_factory):
    """One fresh-process run per configuration."""
    out = tmp_path_factory.mktemp("templates")
    for config, mode in ccm.CACHE.items():
        proc = subprocess.run([sys.executable, "-m", "etf_risk.spark_pipeline", "--windows", str(windows),
                               "--out-root", str(out), "--run-id", config, "--cache", mode, "--record-plans"],
                              cwd=REPO, capture_output=True, text=True, timeout=600)
        assert proc.returncode == 0, proc.stderr[-2000:]
    return out / "snap" / windows.name


@pytest.fixture(scope="module")
def batch(templates, windows, tmp_path_factory):
    batch = tmp_path_factory.mktemp("batches") / "batch-1"
    lines = ["\t".join(["position", "config", "protocol", "measure_exit", "cache_check", "logged_at_utc"])]
    for position, (config, stamp) in enumerate(zip(ccm.ORDER, STAMPS), start=1):
        folder = batch / config / "snap" / windows.name
        folder.mkdir(parents=True, exist_ok=True)
        entries, code = [], None
        for i in range(1, REPEATS + 1):
            run_id = f"run-{stamp}-{i}"
            shutil.copytree(templates / config, folder / run_id)
            record = json.loads((folder / run_id / "run.json").read_text())
            record["run_id"] = run_id
            record["code"]["git_worktree_clean"] = True                 # as if the code had been committed
            record["measurement"] = {
                "warmup": i == 1, "exit_code": 0, "protocol_status": "ok", "stop_reasons": [], "wall_seconds": 10.0 + i,
                "started_at_utc": f"2026-10-22T1{position - 1}:00:0{i}+00:00", "free_memory_before_bytes": 4 * 2**30,
                "peak_rss_total_bytes": 2**31, "peak_rss_by_kind_bytes": {"driver": 2**27, "spark_jvm": 2**30},
                "samples": 40, "max_processes_seen": 11, "threshold_first_exceeded_after_seconds": None}
            (folder / run_id / "run.json").write_text(json.dumps(record))
            entries.append({"run_id": run_id, "warmup": i == 1, "status": "ok", "exit_code": 0, "wall_seconds": 10.0 + i})
            code = record["code"]
        (folder / f"protocol-{stamp}.json").write_text(json.dumps({
            "protocol_started": stamp, "code": code, "repeats_requested": REPEATS, "runs_started": REPEATS,
            "stopped_early": False, "stop_reason": None, "runs": entries}))
        lines.append("\t".join([str(position), config, stamp, "0", "ok", "2026-10-22T12:00:00Z"]))
    (batch / "positions.tsv").write_text("\n".join(lines) + "\n")
    return batch


def collect(batch, windows):
    return ccm.collect(batch, windows, REPEATS)


def failing(acceptance) -> dict:
    return {name: c["problems"] for name, c in acceptance["criteria"].items() if not c["ok"]}


def copy_of(batch, tmp_path):
    shutil.copytree(batch, tmp_path / "batch-1")
    return tmp_path / "batch-1"


def first_run(batch: Path, config: str) -> Path:
    return sorted(p for p in (batch / config).rglob("run-*") if p.is_dir())[0]


def edit(path: Path, change) -> None:
    doc = json.loads(path.read_text())
    change(doc)
    path.write_text(json.dumps(doc))


def in_memory_scans(doc: dict, phase: str):
    return [s for e in doc["executions"] if phase in e["phase"].split("+") for s in e["scans"]
            if s["node"] == "InMemoryTableScan"]


def test_the_batch_meets_every_criterion(batch, windows):
    rows, acceptance = collect(batch, windows)
    assert acceptance["all_ok"], failing(acceptance)
    assert len(rows) == len(ccm.ORDER) * REPEATS
    for table in ccm.TABLE_KEYS:
        assert {r[f"{table}_vs_reference"] for r in rows} == {"pass", "reference"}
    by_config = {r["config"]: r for r in rows}
    assert by_config["A"]["cached_reads_checks"] == "0/0/0" and by_config["C"]["cached_reads_checks"].split("/")[0] != "0"
    assert by_config["C"]["path_days_memory_bytes"] > 0 and by_config["A"]["path_days_memory_bytes"] == ""
    assert {c: {r["fill_executions"] for r in rows if r["config"] == c} for c in "ABC"} == {"A": {0}, "B": {1}, "C": {5}}


def test_the_check_after_each_protocol_knows_the_configuration(batch):
    for config, wrong in (("A", "B"), ("B", "C"), ("C", "A")):
        protocol = next((batch / config).rglob("protocol-*.json"))
        assert ccm.check_protocol(protocol, config) == []
        assert ccm.check_protocol(protocol, wrong)


def test_the_csv_has_one_row_per_started_run_and_the_documented_columns(batch, windows, tmp_path):
    rows, _ = collect(batch, windows)
    ccm.write_csv(rows, tmp_path / "m.csv")
    with (tmp_path / "m.csv").open() as f:
        reader = csv.reader(f)
        assert next(reader) == ccm.FIELDS
        assert sum(1 for _ in reader) == len(rows)


def test_more_or_fewer_downstream_reads_than_the_dry_batch_found_still_pass(batch, windows, tmp_path):
    """6.4 asks for downstream reads in each phase that reads a cache, not for the dry batch's counts."""
    target = copy_of(batch, tmp_path)

    def change(d):
        checks = [e for e in d["executions"] if e["phase"] == "checks"]
        read = next(s for s in checks[0]["scans"] if s["node"] == "InMemoryTableScan")
        checks[0]["scans"].append(dict(read))                                        # one read more
        checks[1]["scans"] = [s for s in checks[1]["scans"] if s["node"] != "InMemoryTableScan"]   # one fewer
    edit(first_run(target, "C") / "plans.json", change)
    assert "3 settings" not in failing(collect(target, windows)[1])


def test_a_zero_row_cached_read_counts_as_use(batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    plans = first_run(target, "B") / "plans.json"
    edit(plans, lambda d: [s.update(rows=0) for s in in_memory_scans(d, "model")])
    assert "3 settings" not in failing(collect(target, windows)[1])


def _missing_metric(d):
    for scan in in_memory_scans(d, "model"):
        scan["rows"] = None
        scan["metrics"].pop("number of output rows", None)


def _no_cached_read(d):
    for e in d["executions"]:
        if "model" in e["phase"].split("+"):
            e["scans"] = [s for s in e["scans"] if s["node"] != "InMemoryTableScan"]


def _read_in_checks(d):
    e = next(e for e in d["executions"] if e["phase"] == "checks")
    e["scans"].append({"node": "InMemoryTableScan", "rows": 5, "metrics": {"number of output rows": "5"}, "desc": ""})


def _fill_only(d):
    """In window_stats only the fill's count() reads the cache: the statistics read no cached members."""
    for e in d["executions"]:
        if e["phase"] == "window_stats" and not e["description"].startswith(ccm.FILL_PREFIX):
            e["scans"] = [s for s in e["scans"] if s["node"] != "InMemoryTableScan"]


def _unmarked_fill(d):
    """The members' fill without its description: the plans no longer show which execution filled them."""
    next(e for e in d["executions"] if e["description"] == ccm.FILL_PREFIX + "members")["description"] = "window_stats"


@pytest.mark.parametrize("config, file, change, criterion, expected", [
    ("C", "run.json", lambda r: r["cache"]["tables"]["path_days"].update(released_by="cleanup"), "3 settings",
     "not by the plan"),
    ("C", "run.json", lambda r: r["cache"]["tables"]["members"]["after_fill"][0].update(cached_partitions=0),
     "3 settings", "partitions cached after the fill"),
    ("C", "run.json", lambda r: r["cache"]["tables"]["paired"].update(rows=1), "3 settings", "the fill counted 1 rows"),
    ("A", "run.json", lambda r: r["cache"]["snapshots"][1]["cached"].append(
        {"rdd_id": 999, "partitions": 1, "cached_partitions": 1, "memory_bytes": 1, "disk_bytes": 0,
         "storage_level": ccm.STORAGE_LEVEL}), "3 settings", "at the end of model"),
    ("B", "run.json", lambda r: r["pipeline_options"].update(cache="none"), "3 settings", "pipeline options"),
    ("B", "plans.json", _no_cached_read, "3 settings", "no downstream cached read with a row metric in model"),
    ("B", "plans.json", _missing_metric, "3 settings", "with the metric missing"),
    ("A", "plans.json", _read_in_checks, "3 settings", "1 downstream cached reads in checks"),
    ("B", "plans.json", _fill_only, "3 settings", "no downstream cached read with a row metric in window_stats"),
    ("B", "plans.json", _unmarked_fill, "3 settings", "members: 0 fill executions in the plans, not 1"),
    ("C", "plans.json", lambda d: d.update(format=1), "3 settings", "plans format 1"),
    ("C", "run.json", lambda r: r.update(status="checks_failed"), "4 results", "status checks_failed"),
    ("B", "run.json", lambda r: r["code"].update(uv_lock_sha256="other"), "1 code state", "hashes differ"),
])
def test_a_planted_problem_fails_its_criterion(batch, windows, tmp_path, config, file, change, criterion, expected):
    target = copy_of(batch, tmp_path)
    edit(first_run(target, config) / file, change)
    problems = failing(collect(target, windows)[1])
    assert criterion in problems and any(expected in p for p in problems[criterion]), problems


def test_a_changed_output_value_fails_the_comparison(batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    (part, *_) = sorted((first_run(target, "C") / "path_days").rglob("*.parquet"))
    table = pq.read_table(part)
    values = table["nav"].to_pylist()
    values[0] = values[0] + 1e-3
    pq.write_table(table.set_column(table.column_names.index("nav"), "nav", pa.array(values)), part)
    problems = failing(collect(target, windows)[1])
    assert any("path_days: nav: 1 values outside" in p for p in problems["4 results"]), problems


def set_protocol_entry(run_dir: Path, **values) -> None:
    """The run's entry in its protocol JSON, as measure records a run that did not end ok."""
    stamp = run_dir.name.removeprefix("run-").rsplit("-", 1)[0]
    edit(run_dir.parent / f"protocol-{stamp}.json",
         lambda p: next(e for e in p["runs"] if e["run_id"] == run_dir.name).update(values))


def test_runs_that_failed_or_were_aborted_without_outputs_fail_the_criteria_instead_of_stopping_the_collector(
        batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    # Aborted in the model phase: the pipeline wrote no run.json, so measure wrote its own; path_days was not
    # committed, the later tables were never written, and plans.json was cut off.
    aborted = sorted(p for p in (target / "C").rglob("run-*") if p.is_dir())[1]
    measurement = json.loads((aborted / "run.json").read_text())["measurement"]
    (aborted / "run.json").write_text(json.dumps({"run_id": aborted.name, "status": "no run.json written",
                                                  "measurement": {**measurement, "exit_code": -15,
                                                                  "protocol_status": "failed"}}))
    set_protocol_entry(aborted, status="failed", exit_code=-15)
    (aborted / "path_days" / "_SUCCESS").unlink()
    for name in ("path_summary", "paired"):
        shutil.rmtree(aborted / name)
    (aborted / "plans.json").write_text('{"format": 2, "executions": [')
    # Failed with an error after the summaries: its run.json says so, and paired is missing.
    failed = first_run(target, "B")
    edit(failed / "run.json", lambda r: r.update(status="failed", error="RuntimeError: forced"))
    set_protocol_entry(failed, status="failed", exit_code=2)
    shutil.rmtree(failed / "paired")

    rows, acceptance = collect(target, windows)                 # reports the runs, does not stop
    problems = failing(acceptance)
    assert f"{aborted.name} path_days: incomplete (no _SUCCESS marker)" in problems["4 results"]
    assert f"{aborted.name} paired: missing" in problems["4 results"]
    assert f"{failed.name} paired: missing" in problems["4 results"]
    assert any(aborted.name in p and "ended failed" in p for p in problems["5 completeness"])
    assert any(aborted.name in p and "plan capture missing" in p for p in problems["3 settings"])
    row = next(r for r in rows if r["run_id"] == aborted.name)
    assert [row[f"{t}_vs_reference"] for t in ccm.TABLE_KEYS] == ["pass", "incomplete", "missing", "missing"]
    protocol = aborted.parent / f"protocol-{aborted.name.removeprefix('run-').rsplit('-', 1)[0]}.json"
    reported = ccm.check_protocol(protocol, "C")                # the check after the protocol reports it too
    assert f"{aborted.name}: ended failed" in reported and any("no cache section" in p for p in reported)


def test_a_reference_run_without_an_output_table_is_reported_and_that_comparison_skipped(batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    position_1 = (target / "positions.tsv").read_text().splitlines()[1].split("\t")[2]
    reference = next((target / "A").rglob(f"run-{position_1}-2"))
    shutil.rmtree(reference / "path_days")
    rows, acceptance = collect(target, windows)
    assert "the reference run's path_days: missing" in failing(acceptance)["4 results"]
    assert {r["path_days_vs_reference"] for r in rows} == {"missing", "no reference"}
    assert {r["paired_vs_reference"] for r in rows} == {"pass", "reference"}


def test_positions_out_of_order_or_missing_fail_completeness(batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    lines = (target / "positions.tsv").read_text().splitlines()
    (target / "positions.tsv").write_text("\n".join(lines[:3] + [lines[4]]) + "\n")
    problems = failing(collect(target, windows)[1])["5 completeness"]
    assert any("position 3" in p and "has no protocol" in p for p in problems)
    assert any("is not in positions.tsv" in p for p in problems)
