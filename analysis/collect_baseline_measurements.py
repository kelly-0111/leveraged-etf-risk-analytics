"""Collect one batch of the pandas-baseline experiment and evaluate its acceptance criteria.

docs/pandas-baseline.md, sections 4.3, 6, 7 and 10. A batch folder holds:

    positions.tsv   one line per protocol the session helpers ran (docs/baseline-session.zsh)
    run-log.txt     the session's run log (for people; not read here)
    S/, P/          each engine's out-root: <snapshot>/<window set>/protocol-*.json, run-*/

Run from the repository root:

    uv run python analysis/collect_baseline_measurements.py --batch data/outputs-baseline/batch-1
    uv run python analysis/collect_baseline_measurements.py --check-protocol <protocol JSON> --engine S

The first form writes measurements.csv (one row per started run) and acceptance.json (each
acceptance criterion with the problems found, plus observations) into the batch folder, prints a
summary, and exits with 1 if any criterion fails. The second form, which the session helpers run
after each protocol, checks that every run of that protocol ran its position's pipeline with the
settings of section 6 (3.4). The records label the two implementations S and P as `engine`.

The rules it shares with the shuffle-partition experiment (code state, inputs, the comparison of
tables by their full keys) are that experiment's collector's functions, imported unchanged.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_baseline_collector.py
and on a small window set (docs/pandas-baseline.md 4.5).
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))      # the shuffle-partition collector, next to this script
import collect_partition_measurements as cpm  # noqa: E402

from etf_risk.windows import WINDOW_KEY, ChecksumError, verify_checksums  # noqa: E402

PATH_KEY = [*WINDOW_KEY, "leverage"]
ENGINES = {"S": "spark", "P": "pandas"}       # 2.1: the pipeline measure starts (--pipeline)
ORDER = ("S", "P", "P", "S")                  # positions 1 to 4 (2.3)
SPARK_DEFAULTS = {cpm.PARTITIONS: "200", cpm.ADAPTIVE: "true", cpm.COALESCE: "true"}   # S: Spark's, unset (2.1)
WINDOWS = cpm.WINDOWS
REPEATS = 4
TABLE_KEYS = {"window_stats": list(WINDOW_KEY), "path_summary": list(PATH_KEY), "paired": list(WINDOW_KEY)}
PATH_DAYS_KEY = [*PATH_KEY, "day"]
FULL_PATH_DAYS_RUN = 2                        # 7: path_days compared in full for this run of each P protocol
COUNTED_TABLES = ("window_stats", "path_days")
CRITERIA = cpm.CRITERIA
PHASES = ["session_start", "window_stats_and_construction_check", "model_and_path_days",
          "summaries_and_pairing", "checks", "total_in_process"]
PROCESS_KINDS = ["driver", "spark_jvm", "python_worker", "other"]
TASK_GROUPS = ["window_stats", "model", "summaries", "checks"]

IDENTITY_FIELDS = ["batch", "position", "engine", "used", "protocol_id", "run_id", "run_number", "warmup", "status",
                   "exit_code"]
MEASUREMENT_FIELDS = (["started_at_utc", "windows", "path_day_rows", "wall_s"] + [f"{p}_s" for p in PHASES]
                      + ["free_memory_before_bytes", "peak_rss_total_bytes"]
                      + [f"peak_rss_{kind}_bytes" for kind in PROCESS_KINDS]
                      + ["samples", "max_processes_seen", "threshold_crossed", "git_commit", "git_worktree_clean"])
SPARK_FIELDS = (["shuffle_partitions_requested", "adaptive_enabled", "coalesce_enabled", "default_parallelism",
                 "jvm_max_heap_bytes"] + [f"tasks_{group}" for group in TASK_GROUPS])
EXTRA_FIELDS = ([f"files_{table}" for table in cpm.OUTPUT_TABLES]
                + [f"{table}_vs_reference" for table in TABLE_KEYS] + ["path_days_vs_reference"])
FIELDS = IDENTITY_FIELDS + MEASUREMENT_FIELDS + SPARK_FIELDS + EXTRA_FIELDS
POSITION_FIELDS = ["position", "engine", "protocol", "measure_exit", "settings_check", "logged_at_utc"]


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_protocols(batch: Path) -> dict[str, tuple[str, Path]]:
    """Protocol id -> (engine, path) for every protocol JSON in the batch's engine folders."""
    found = {}
    for engine in ENGINES:
        for path in sorted((batch / engine).rglob("protocol-*.json")):
            found[path.stem.removeprefix("protocol-")] = (engine, path)
    return found


def read_table(run_dir: Path, name: str) -> pa.Table:
    """A table with the ticker partition column as plain strings (path_days is partitioned by ticker)."""
    table = pq.read_table(run_dir / name)
    if "ticker" in table.column_names and pa.types.is_dictionary(table.schema.field("ticker").type):
        table = table.set_column(table.column_names.index("ticker"), "ticker", table["ticker"].cast(pa.string()))
    return table


# --- criterion 3: settings (6) ---------------------------------------------------------

def check_settings(label: str, engine: str, run: dict, protocol: dict | None = None) -> list[str]:
    """S: the Spark pipeline with Spark's defaults and no pipeline option; P: the pandas pipeline."""
    problems = []
    if protocol is not None and protocol.get("pipeline") != ENGINES[engine]:
        problems.append(f"{label}: its protocol ran pipeline {protocol.get('pipeline')!r}, not {ENGINES[engine]!r}")
    if engine == "S":
        if run.get("engine") is not None:
            problems.append(f"{label}: engine {run.get('engine')!r} in a Spark position")
        spark = run.get("spark") or {}
        for key, value in SPARK_DEFAULTS.items():
            if spark.get(key) != value:
                problems.append(f"{label}: {key} is {spark.get(key)!r}; Spark's default is {value!r}")
        if "pipeline_options" in run:
            problems.append(f"{label}: pipeline options {run['pipeline_options']} (S passes none)")
    else:
        if run.get("engine") != "pandas":
            problems.append(f"{label}: engine {run.get('engine')!r} in a pandas position")
        if "spark" in run:
            problems.append(f"{label}: a pandas run with Spark settings")
    return problems


def check_protocol(protocol_path: Path, engine: str) -> list[str]:
    """The check after each protocol (3.4): every run's engine and settings match its position."""
    protocol = read_json(protocol_path)
    problems = []
    for entry, run, _ in cpm.load_runs(protocol_path, protocol):
        if run is None:
            problems.append(f"{entry['run_id']}: no run.json")
            continue
        problems += check_settings(entry["run_id"], engine, run, protocol)
    return problems


# --- rows ------------------------------------------------------------------------------

def measurement_columns(run: dict | None) -> dict:
    """The run's values, copied without rounding; a value the run did not record is left empty."""
    def get(*keys):
        value = run or {}
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return ""
            value = value[key]
        return value

    exceeded = get("measurement", "threshold_first_exceeded_after_seconds")
    partitions = get("spark", cpm.PARTITIONS)
    return {
        "started_at_utc": get("measurement", "started_at_utc"), "windows": get("row_counts", "windows"),
        "path_day_rows": get("row_counts", "path_days"), "wall_s": get("measurement", "wall_seconds"),
        **{f"{phase}_s": get("timings_seconds", phase) for phase in PHASES},
        "free_memory_before_bytes": get("measurement", "free_memory_before_bytes"),
        "peak_rss_total_bytes": get("measurement", "peak_rss_total_bytes"),
        **{f"peak_rss_{kind}_bytes": get("measurement", "peak_rss_by_kind_bytes", kind) for kind in PROCESS_KINDS},
        "samples": get("measurement", "samples"), "max_processes_seen": get("measurement", "max_processes_seen"),
        "threshold_crossed": (exceeded is not None) if run and "measurement" in run else "",
        "git_commit": get("code", "git_commit"), "git_worktree_clean": get("code", "git_worktree_clean"),
        "shuffle_partitions_requested": int(partitions) if partitions != "" else "",
        "adaptive_enabled": get("spark", cpm.ADAPTIVE) == "true" if get("spark", cpm.ADAPTIVE) != "" else "",
        "coalesce_enabled": get("spark", cpm.COALESCE) == "true" if get("spark", cpm.COALESCE) != "" else "",
        "default_parallelism": get("spark", "default_parallelism"), "jvm_max_heap_bytes": get("spark", "jvm_max_heap_bytes"),
        **{f"tasks_{group}": get("stage_task_counts", group, "tasks") for group in TASK_GROUPS},
    }


# --- the whole batch -----------------------------------------------------------------

def collect(batch: Path, windows: Path, repeats: int) -> tuple[list[dict], dict]:
    """(CSV rows, acceptance document) for one batch."""
    criteria = {name: [] for name in CRITERIA}
    notes: dict = {}
    positions_path = batch / "positions.tsv"
    rows = cpm.read_positions(positions_path) if positions_path.is_file() else []
    if not rows:
        criteria["5 completeness"].append(f"{positions_path} is missing or empty")
    used = cpm.used_protocols(rows)
    position_of = {row["protocol"]: row["position"] for row in rows}
    loaded = {}
    for protocol_id, (engine, path) in find_protocols(batch).items():
        protocol = read_json(path)
        loaded[protocol_id] = (engine, path, protocol, cpm.load_runs(path, protocol))

    # criterion 5: positions, used protocols, complete protocols
    for row in rows:
        if row["protocol"] not in loaded:
            criteria["5 completeness"].append(f"positions.tsv lists protocol {row['protocol']}, which is not in the batch")
    for protocol_id in sorted(set(loaded) - set(position_of)):
        criteria["5 completeness"].append(f"protocol {protocol_id} is not in positions.tsv (run outside the helpers?)")
    used_ids = {}
    for position, expected in enumerate(ORDER, start=1):
        row = used.get(position)
        if row is None:
            criteria["5 completeness"].append(f"position {position} ({expected}) has no protocol")
            continue
        protocol_id = row["protocol"]
        used_ids[position] = protocol_id
        if protocol_id not in loaded:
            continue
        engine, _, protocol, runs = loaded[protocol_id]
        if row["engine"] != expected or engine != expected:
            criteria["5 completeness"].append(f"position {position}: protocol {protocol_id} is engine {engine} "
                                              f"(positions.tsv: {row['engine']}), not {expected}")
        if protocol["repeats_requested"] != repeats or protocol["runs_started"] != repeats or protocol["stopped_early"]:
            criteria["5 completeness"].append(f"position {position}: {protocol['runs_started']} of "
                                              f"{protocol['repeats_requested']} runs started (needs {repeats} of "
                                              f"{repeats}), stopped early: {protocol['stopped_early']}")
        for entry, run, _ in runs:
            if entry["status"] != "ok":
                criteria["5 completeness"].append(f"position {position}: {entry['run_id']} ended {entry['status']}")
            if run and run.get("measurement", {}).get("threshold_first_exceeded_after_seconds") is not None:
                criteria["5 completeness"].append(f"position {position}: {entry['run_id']} crossed the memory threshold")
    stamps = [used_ids[p] for p in sorted(used_ids)]
    if stamps != sorted(stamps):
        criteria["5 completeness"].append(f"the used protocols did not run in position order: {stamps}")

    # criterion 1: one code state in every record of the batch
    records = []
    for protocol_id, (_, _, protocol, runs) in sorted(loaded.items()):
        records.append((f"protocol {protocol_id}", protocol.get("code")))
        records += [(entry["run_id"], run.get("code") if run else None) for entry, run, _ in runs]
    criteria["1 code state"], notes["commits"] = cpm.check_code_state(records)

    # criterion 2: inputs, and the inputs still unchanged now
    config = read_json(windows / "config.json")
    try:
        verify_checksums(windows)
    except (ChecksumError, FileNotFoundError, KeyError) as exc:
        criteria["2 inputs"].append(f"the window set's inputs changed after the session: {exc}")

    # the reference run (7): run 2 of the used protocol at position 1, a Spark run
    reference_dir, reference = None, {}
    if 1 in used_ids and used_ids[1] in loaded:
        reference_dir = loaded[used_ids[1]][1].parent / f"run-{used_ids[1]}-2"
    if reference_dir is not None and (reference_dir / "run.json").is_file():
        reference = {"run": read_json(reference_dir / "run.json"),
                     **{table: read_table(reference_dir, table) for table in TABLE_KEYS}}
    else:
        criteria["4 results"].append(f"no reference run (run 2 of the used protocol at position 1): {reference_dir}")

    used_set = set(used_ids.values())
    csv_rows, environments, spark_settings, float_diffs = [], {}, {}, {}
    for protocol_id, (engine, path, protocol, runs) in sorted(loaded.items()):
        is_used = protocol_id in used_set
        for entry, run, run_dir in runs:
            label = entry["run_id"]
            run_number = int(label.rsplit("-", 1)[1])
            row = {"batch": batch.name, "position": position_of.get(protocol_id, ""), "engine": engine, "used": is_used,
                   "protocol_id": protocol_id, "run_id": label, "run_number": run_number, "warmup": entry["warmup"],
                   "status": entry["status"], "exit_code": entry["exit_code"],
                   **measurement_columns(run), **cpm.file_counts(run_dir),
                   **dict.fromkeys([f"{table}_vs_reference" for table in TABLE_KEYS] + ["path_days_vs_reference"], "")}
            if run is None:
                if is_used:
                    criteria["4 results"].append(f"{label}: no run.json")
                csv_rows.append(row)
                continue
            criteria["2 inputs"] += cpm.check_inputs(label, run, config)
            if is_used:
                criteria["3 settings"] += check_settings(label, engine, run, protocol)
                environments.setdefault(json.dumps(run.get("environment"), sort_keys=True), []).append(label)
                if engine == "S":
                    spark_settings.setdefault(cpm.common_settings(run), []).append(label)
                if run.get("status") != "ok" or cpm.total_violations(run) != 0:
                    criteria["4 results"].append(f"{label}: status {run.get('status')}, "
                                                 f"{cpm.total_violations(run)} check violations")
            if reference and run_dir != reference_dir:
                for table, key in TABLE_KEYS.items():
                    problems, diffs = cpm.compare_tables(reference[table], read_table(run_dir, table), key,
                                                         cpm.BREACH_FIELDS.get(table, []))
                    row[f"{table}_vs_reference"] = "fail" if problems else "pass"
                    if problems and is_used:
                        criteria["4 results"] += [f"{label} {table}: {p}" for p in problems]
                    _merge_diffs(float_diffs, f"{engine}.{table}", diffs)
                if engine == "P" and run_number == FULL_PATH_DAYS_RUN:
                    problems, diffs = cpm.compare_tables(read_table(reference_dir, "path_days"),
                                                         read_table(run_dir, "path_days"), PATH_DAYS_KEY, [])
                    row["path_days_vs_reference"] = "fail" if problems else "pass"
                    if problems and is_used:
                        criteria["4 results"] += [f"{label} path_days: {p}" for p in problems]
                    _merge_diffs(float_diffs, "P.path_days", diffs)
                for table in COUNTED_TABLES:
                    if run.get("row_counts", {}).get(table) != reference["run"]["row_counts"].get(table):
                        if is_used:
                            criteria["4 results"].append(f"{label}: {table} has {run.get('row_counts', {}).get(table)} "
                                                         f"rows; the reference has {reference['run']['row_counts'].get(table)}")
            elif run_dir == reference_dir:
                row.update(dict.fromkeys([f"{table}_vs_reference" for table in TABLE_KEYS] + ["path_days_vs_reference"],
                                         "reference"))
            csv_rows.append(row)
    if len(environments) > 1:
        criteria["3 settings"].append(f"recorded environments differ: {sorted(environments.values(), key=len)}")
    if len(spark_settings) > 1:
        criteria["3 settings"].append(f"recorded Spark settings differ between S runs: {sorted(spark_settings.values(), key=len)}")
    notes["float_differences_to_reference"] = float_diffs

    acceptance = {
        "batch": str(batch), "windows": str(windows), "repeats": repeats,
        "reference_run": str(reference_dir) if reference_dir else None,
        "used_protocols": {str(p): used_ids[p] for p in sorted(used_ids)},
        "criteria": {name: {"ok": not problems, "problems": problems} for name, problems in criteria.items()},
        "all_ok": not any(criteria.values()),
        "notes": notes,
    }
    return csv_rows, acceptance


def _merge_diffs(store: dict, prefix: str, diffs: dict) -> None:
    for column, d in diffs.items():
        best = store.setdefault(f"{prefix}.{column}", {"max_abs": 0.0, "max_rel": 0.0})
        best["max_abs"], best["max_rel"] = max(best["max_abs"], d["max_abs"]), max(best["max_rel"], d["max_rel"])


def write_csv(rows: list[dict], out: Path) -> None:
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def print_summary(rows: list[dict], acceptance: dict) -> None:
    for name, result in acceptance["criteria"].items():
        print(f"criterion {name}: {'ok' if result['ok'] else f'FAILED ({len(result['problems'])} problems)'}")
        for problem in result["problems"][:5]:
            print(f"    {problem}")
    print("used protocols (position, engine, measured ok runs, median wall_s, median peak GiB):")
    for position, protocol_id in acceptance["used_protocols"].items():
        measured = [r for r in rows if r["protocol_id"] == protocol_id and not r["warmup"] and r["status"] == "ok"]
        walls = [r["wall_s"] for r in measured if r["wall_s"] != ""]
        peaks = [r["peak_rss_total_bytes"] / 2**30 for r in measured if r["peak_rss_total_bytes"] != ""]
        engine = measured[0]["engine"] if measured else "?"
        print(f"    {position} {engine} {protocol_id}: {len(measured)} runs, "
              f"{statistics.median(walls):.3f} s, {statistics.median(peaks):.3f} GiB" if walls and peaks
              else f"    {position} {engine} {protocol_id}: {len(measured)} measured ok runs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--batch", type=Path, help="batch folder, for example data/outputs-baseline/batch-1")
    parser.add_argument("--check-protocol", type=Path, help="check one protocol's engine and settings and exit")
    parser.add_argument("--engine", choices=sorted(ENGINES), help="with --check-protocol: the position's engine")
    parser.add_argument("--windows", type=Path, default=WINDOWS, help="the window set the runs must have used")
    parser.add_argument("--repeats", type=int, default=REPEATS, help="runs per protocol")
    args = parser.parse_args(argv)
    if args.check_protocol:
        if not args.engine:
            parser.error("--check-protocol needs --engine")
        problems = check_protocol(args.check_protocol, args.engine)
        runs = len(read_json(args.check_protocol)["runs"])
        print(f"settings: ok in {runs} of {runs} runs" if not problems else "settings: PROBLEM\n  " + "\n  ".join(problems))
        return 1 if problems else 0
    if not args.batch:
        parser.error("give --batch or --check-protocol")
    if args.repeats < 2:
        parser.error("--repeats must be at least 2: the reference is a protocol's run 2")
    rows, acceptance = collect(args.batch, args.windows, args.repeats)
    write_csv(rows, args.batch / "measurements.csv")
    (args.batch / "acceptance.json").write_text(json.dumps(acceptance, indent=2, default=str) + "\n")
    print(f"{len(rows)} rows -> {args.batch / 'measurements.csv'}; criteria -> {args.batch / 'acceptance.json'}")
    print_summary(rows, acceptance)
    return 0 if acceptance["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
