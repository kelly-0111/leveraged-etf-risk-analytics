"""The pandas-baseline collector (analysis/collect_baseline_measurements.py) on a real small batch.

The fixture runs the S-P-P-S order with etf_risk.measure --pipeline on the synthetic snapshot of
tests/test_spark_equivalence.py (two runs per protocol), writes positions.tsv as the session helpers
do, and marks the records' worktree clean (the tests run on uncommitted code). The collector must
accept that batch, and each planted problem must fail the criterion that covers it.

AI contribution: written with Claude Code (Opus 5.5).
"""
import csv
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk import measure
from etf_risk.windows import build_definitions, write_definitions

ANALYSIS = Path(__file__).resolve().parents[1] / "analysis"
sys.path.insert(0, str(ANALYSIS))
_spec = importlib.util.spec_from_file_location("collect_baseline_measurements", ANALYSIS / "collect_baseline_measurements.py")
cbm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cbm)

pytestmark = pytest.mark.spark
ANCHOR = "2024-01-02"
REPEATS = 2


@pytest.fixture(scope="module")
def windows(tmp_path_factory):
    root = tmp_path_factory.mktemp("snap")
    rng = np.random.default_rng(7)
    dates = nyse_sessions(ANCHOR, 61)
    b = rng.normal(0, 0.02, 60)
    b[29] = -0.60                                              # a 2x breach
    snap = write_snapshot(root, "snap", {"AAA": (dates, rng.normal(0, 0.02, 60)), "BBB": (dates, b)},
                          unverified=[{"ticker": "BBB", "date": str(dates[30])}])
    return write_definitions(*build_definitions(snap, "rolling", window_days=10, stride=3, anchor=ANCHOR), root / "w")


@pytest.fixture(scope="module")
def batch(windows, tmp_path_factory):
    batch = tmp_path_factory.mktemp("batches") / "batch-1"
    lines = ["\t".join(cbm.POSITION_FIELDS)]
    for position, engine in enumerate(cbm.ORDER, start=1):
        out = batch / engine
        before = set(out.rglob("protocol-*.json"))
        assert measure.main(["--pipeline", cbm.ENGINES[engine], "--repeats", str(REPEATS), "--",
                             "--windows", str(windows), "--out-root", str(out)]) == 0
        (protocol,) = set(out.rglob("protocol-*.json")) - before
        check = cbm.check_protocol(protocol, engine)
        lines.append("\t".join([str(position), engine, protocol.stem.removeprefix("protocol-"), "0",
                                "ok" if not check else "failed", "2026-10-22T00:00:00Z"]))
    (batch / "positions.tsv").write_text("\n".join(lines) + "\n")
    for path in batch.rglob("*.json"):                     # as if the code had been committed
        record = json.loads(path.read_text())
        if "code" in record:
            record["code"]["git_worktree_clean"] = True
            path.write_text(json.dumps(record))
    return batch


def collect(batch, windows):
    return cbm.collect(batch, windows, REPEATS)


def copy_of(batch, tmp_path):
    target = tmp_path / "batch-1"
    shutil.copytree(batch, target)
    return target


def run_dirs(batch, engine):
    return sorted(p for p in (batch / engine).rglob("run-*") if p.is_dir())


def edit_run(run_dir: Path, change) -> None:
    record = json.loads((run_dir / "run.json").read_text())
    change(record)
    (run_dir / "run.json").write_text(json.dumps(record))


def failing(acceptance) -> dict:
    return {name: c["problems"] for name, c in acceptance["criteria"].items() if not c["ok"]}


def test_the_batch_meets_every_criterion(batch, windows):
    rows, acceptance = collect(batch, windows)
    assert acceptance["all_ok"], failing(acceptance)
    assert len(rows) == len(cbm.ORDER) * REPEATS
    by_run = {r["run_id"]: r for r in rows}
    p_full = [r for r in rows if r["engine"] == "P" and r["run_number"] == cbm.FULL_PATH_DAYS_RUN]
    assert len(p_full) == 2 and all(r["path_days_vs_reference"] == "pass" for r in p_full)
    assert all(r["paired_vs_reference"] in ("pass", "reference") for r in by_run.values())
    assert {r["engine"]: r["peak_rss_spark_jvm_bytes"] == "" for r in rows} == {"S": False, "P": True}


def test_the_check_after_each_protocol_knows_the_engine(batch):
    for engine, other in (("S", "P"), ("P", "S")):
        protocol = next((batch / engine).rglob("protocol-*.json"))
        assert cbm.check_protocol(protocol, engine) == []
        assert any("pipeline" in p for p in cbm.check_protocol(protocol, other))


def test_the_csv_has_one_row_per_started_run_and_the_documented_columns(batch, windows, tmp_path):
    rows, _ = collect(batch, windows)
    cbm.write_csv(rows, tmp_path / "m.csv")
    with (tmp_path / "m.csv").open() as f:
        reader = csv.reader(f)
        assert next(reader) == cbm.FIELDS
        assert sum(1 for _ in reader) == len(rows)


@pytest.mark.parametrize("plant, criterion, expected", [
    (lambda b: edit_run(run_dirs(b, "S")[2], lambda r: r["spark"].update({cbm.cpm.PARTITIONS: "8"})),
     "3 settings", "Spark's default"),
    (lambda b: edit_run(run_dirs(b, "S")[1], lambda r: r.update(pipeline_options={"record_plans": True})),
     "3 settings", "pipeline options"),
    (lambda b: edit_run(run_dirs(b, "P")[1], lambda r: r.pop("engine")), "3 settings", "pandas position"),
    (lambda b: edit_run(run_dirs(b, "P")[2], lambda r: r["environment"].update(python="3.13.0")),
     "3 settings", "environments differ"),
    (lambda b: edit_run(run_dirs(b, "P")[3], lambda r: r["code"].update(uv_lock_sha256="other")),
     "1 code state", "hashes differ"),
    (lambda b: edit_run(run_dirs(b, "P")[0], lambda r: r["verified_sha256"].clear()), "2 inputs", "verified input"),
    (lambda b: edit_run(run_dirs(b, "P")[2], lambda r: r.update(status="checks_failed")), "4 results", "status checks_failed"),
])
def test_a_planted_record_problem_fails_its_criterion(batch, windows, tmp_path, plant, criterion, expected):
    target = copy_of(batch, tmp_path)
    plant(target)
    problems = failing(collect(target, windows)[1])
    assert criterion in problems and any(expected in p for p in problems[criterion]), problems


def test_a_changed_output_value_fails_the_comparison(batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    paired = run_dirs(target, "P")[3] / "paired"
    (part,) = paired.glob("*.parquet")
    table = pq.read_table(part)
    values = table["return_1x"].to_pylist()
    values[0] = values[0] + 1e-3
    pq.write_table(table.set_column(table.column_names.index("return_1x"), "return_1x", pa.array(values)), part)
    problems = failing(collect(target, windows)[1])
    assert any("paired: return_1x: 1 values outside" in p for p in problems["4 results"]), problems


def test_positions_out_of_order_or_missing_fail_completeness(batch, windows, tmp_path):
    target = copy_of(batch, tmp_path)
    lines = (target / "positions.tsv").read_text().splitlines()
    (target / "positions.tsv").write_text("\n".join([lines[0], lines[1], lines[3].replace("\tP\t", "\tS\t", 1)]) + "\n")
    problems = failing(collect(target, windows)[1])["5 completeness"]
    assert any("position 4" in p and "has no protocol" in p for p in problems)
    assert any("is not in positions.tsv" in p for p in problems)
