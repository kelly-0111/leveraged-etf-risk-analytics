"""Collect one batch of the shuffle-partition experiment and evaluate its acceptance criteria.

docs/partition-experiment.md, sections 4.3, 6, 7 and 10. A batch folder holds:

    positions.tsv   one line per protocol the session helpers ran (docs/partition-session.zsh)
    run-log.txt     the session's run log (for people; not read here)
    A/, B/, C/      each configuration's out-root: <snapshot>/<window set>/protocol-*.json, run-*/

Run from the repository root:

    uv run python analysis/collect_partition_measurements.py --batch data/outputs-partitions/batch-1
    uv run python analysis/collect_partition_measurements.py --check-protocol <protocol JSON> --config A

The first form writes measurements.csv (one row per started run) and acceptance.json (each
acceptance criterion with the problems found, plus observations) into the batch folder, prints a
summary, and exits with 1 if any criterion fails. The second form, which the session helpers run
after each protocol, checks that every run of that protocol captured its plans and, with --config,
that its recorded settings and plans match that configuration (3.4, 6).

It reads the stride experiment's records but never writes them, and it leaves the stride
collector (collect_measurements.py) unchanged; it only imports its column definitions.

AI contribution: written with Claude Code (Opus 5.5) at the author's request. Tested with
tests/test_partition_collector.py and on a small window set (docs/partition-experiment.md 4.5).
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parent))      # the stride collector, next to this script
from collect_measurements import MEASUREMENT_FIELDS, measurement_columns  # noqa: E402

from etf_risk import plans  # noqa: E402
from etf_risk.spark_pipeline import ATOL, PATH_KEY, RTOL  # noqa: E402
from etf_risk.windows import WINDOW_KEY, ChecksumError, verify_checksums  # noqa: E402

PARTITIONS = "spark.sql.shuffle.partitions"
ADAPTIVE = "spark.sql.adaptive.enabled"
COALESCE = "spark.sql.adaptive.coalescePartitions.enabled"
CONFIGS = {          # 2.1
    "A": {PARTITIONS: "200", ADAPTIVE: "true", COALESCE: "true"},
    "B": {PARTITIONS: "200", ADAPTIVE: "true", COALESCE: "false"},
    "C": {PARTITIONS: "8", ADAPTIVE: "true", COALESCE: "false"},
}
OPTIONS = {          # 2.4: every configuration passes all three flags
    "A": {"shuffle_partitions": 200, "coalesce": "on", "record_plans": True},
    "B": {"shuffle_partitions": 200, "coalesce": "off", "record_plans": True},
    "C": {"shuffle_partitions": 8, "coalesce": "off", "record_plans": True},
}
ORDER = ("A", "B", "C", "C", "B", "A")      # positions 1 to 6 (2.3)
WINDOWS = Path("data/windows-experiments/full-2026-10-12/rolling-252-s7")
STRIDE_RUN = Path("data/outputs-experiments/full-2026-10-12/rolling-252-s7/run-20261019T035809Z-2")
REPEATS = 4
SPARK_VERSION = "4.2.0"
TABLE_KEYS = {"paired": list(WINDOW_KEY), "path_summary": list(PATH_KEY)}
BREACH_FIELDS = {    # 7, item 5
    "paired": ["breached_1x", "breached_2x", "breach_date_2x", "breach_day_2x", "last_ok_date_2x", "days_ok_2x"],
    "path_summary": ["breached", "n_breach_rows", "breach_day", "breach_date", "last_ok_date", "days_ok"],
}
COUNTED_TABLES = ("window_stats", "path_days")         # compared by row count only (7)
OUTPUT_TABLES = ("window_stats", "path_days", "path_summary", "paired")
PHASES = ("window_stats", "model", "summaries", "checks")
CRITERIA = ("1 code state", "2 inputs", "3 settings", "4 results", "5 completeness")
POSITION_FIELDS = ["position", "config", "protocol", "measure_exit", "plans_check", "logged_at_utc"]
_ARG_PARTITIONED = re.compile(r"^Arguments: (?:hash|range)partitioning\(.*, (\d+)\)(?:, |$)")
_ARG_COALESCED = re.compile(r"^Arguments: coalesced\b")

IDENTITY_FIELDS = ["batch", "position", "config", "used", "protocol_id", "run_id", "run_number", "warmup", "status",
                   "exit_code"]
EXTRA_FIELDS = (["coalesce_enabled", "plan_capture_status", "plan_capture_s", "wall_excl_capture_s", "sql_executions",
                 "adaptive_plans", "requested_partitions", "coalesced_reads", "local_reads"]
                + [f"exchanges_{phase}" for phase in PHASES] + [f"reads_{phase}" for phase in PHASES]
                + ["broadcast_joins", "sort_merge_joins"]
                + [f"files_{table}" for table in OUTPUT_TABLES] + [f"{table}_vs_reference" for table in TABLE_KEYS])
FIELDS = IDENTITY_FIELDS + MEASUREMENT_FIELDS + EXTRA_FIELDS


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --- inputs ------------------------------------------------------------------------

def read_positions(path: Path) -> list[dict]:
    """The helpers' positions.tsv: one line per protocol, in the order the protocols ran."""
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    for row in rows:
        row["position"] = int(row["position"])
    return rows


def used_protocols(rows: list[dict]) -> dict[int, dict]:
    """The used protocol at each position: the last one run there (3.3)."""
    return {row["position"]: row for row in rows}


def find_protocols(batch: Path) -> dict[str, tuple[str, Path]]:
    """Protocol id -> (configuration, path) for every protocol JSON in the batch's configuration folders."""
    found = {}
    for config in CONFIGS:
        for path in sorted((batch / config).rglob("protocol-*.json")):
            found[path.stem.removeprefix("protocol-")] = (config, path)
    return found


def load_runs(protocol_path: Path, protocol: dict) -> list[tuple[dict, dict | None, Path]]:
    """(protocol entry, run.json or None, run folder) for every run the protocol started."""
    runs = []
    for entry in protocol["runs"]:
        run_dir = protocol_path.parent / entry["run_id"]
        run_json = run_dir / "run.json"
        runs.append((entry, read_json(run_json) if run_json.is_file() else None, run_dir))
    return runs


def load_plans(run_dir: Path) -> dict | None:
    path = run_dir / "plans.json"
    return read_json(path) if path.is_file() else None


# --- criteria 1 to 3 ------------------------------------------------------------------

def check_code_state(records: list[tuple[str, dict | None]]) -> tuple[list[str], list[str]]:
    """Criterion 1 (3.1): (problems, commits seen). `records` is (label, code record) for every protocol
    JSON and run.json. Source and dependency hashes must match and the hashed paths be clean; the commit
    may differ between commits that leave the hashes unchanged, so commits are only reported."""
    problems, first = [], None
    for label, code in records:
        if not code:
            problems.append(f"{label}: no code record")
            continue
        hashes = (code.get("source_sha256"), code.get("uv_lock_sha256"))
        if first is None:
            first = (label, hashes)
        elif hashes != first[1]:
            problems.append(f"{label}: source or dependency hashes differ from {first[0]}")
        if code.get("git_worktree_clean") is not True:
            problems.append(f"{label}: src/, pyproject.toml or uv.lock had uncommitted changes")
    return problems, sorted({code.get("git_commit") for _, code in records if code})


def expected_inputs(config: dict) -> dict[str, str]:
    """The seven input hashes a window config records, by file name."""
    expected = {config["windows_file"]: config["windows_sha256"]}
    expected.update({Path(rel).name: sha for rel, sha in config["inputs_sha256"].items()})
    return expected


def check_inputs(label: str, run: dict, config: dict) -> list[str]:
    """Criterion 2 (10): the inputs the run verified are the window set's, and so is its config."""
    problems = []
    verified = {Path(path).name: sha for path, sha in (run.get("verified_sha256") or {}).items()}
    if verified != expected_inputs(config):
        problems.append(f"{label}: verified input checksums differ from the window set's config "
                        f"({len(verified)} recorded, {len(expected_inputs(config))} expected)")
    if run.get("windows_config") != config:
        problems.append(f"{label}: its window config differs from the window set's config.json")
    return problems


def check_settings(label: str, config_name: str, run: dict) -> list[str]:
    """Section 6, item 1, for one run: the configuration's values and the flags that set them."""
    problems = []
    spark = run.get("spark") or {}
    for key, value in CONFIGS[config_name].items():
        if spark.get(key) != value:
            problems.append(f"{label}: {key} is {spark.get(key)!r}; configuration {config_name} needs {value!r}")
    if run.get("pipeline_options") != OPTIONS[config_name]:
        problems.append(f"{label}: pipeline options {run.get('pipeline_options')} instead of {OPTIONS[config_name]}")
    return problems


def common_settings(run: dict) -> str:
    """What must be identical in every run (6, item 1): the Spark settings apart from the varied ones,
    and the environment."""
    spark = {k: v for k, v in (run.get("spark") or {}).items() if k not in CONFIGS["A"]}
    return json.dumps({"spark": spark, "environment": run.get("environment")}, sort_keys=True)


def requested_counts(execution: dict) -> set[int]:
    """Partition counts requested by the execution's hash and range exchanges, from the parsed nodes and,
    independently, from the plan text's argument lines."""
    counts = {x["requested"] for x in execution["exchanges"]
              if x["partitioning"] in ("hashpartitioning", "rangepartitioning")}
    for line in execution["plan"].splitlines():
        if match := _ARG_PARTITIONED.match(line.strip()):
            counts.add(int(match.group(1)))
    return counts


def partitioned(execution: dict) -> list[dict]:
    """The execution's hash and range exchanges: the ones spark.sql.shuffle.partitions sets."""
    return [x for x in execution["exchanges"] if x["partitioning"] in ("hashpartitioning", "rangepartitioning")]


def has_coalesced_read(execution: dict) -> bool:
    return (any("coalesced" in read["mark"] for read in execution["shuffle_reads"])
            or any(_ARG_COALESCED.match(line.strip()) for line in execution["plan"].splitlines()))


def check_plans(label: str, config_name: str, capture: dict | None, doc: dict | None) -> list[str]:
    """Section 6, item 2, for one run. Finality is required of adaptive plans only."""
    if not capture or capture.get("status") != "ok":
        return [f"{label}: plan capture {'missing' if not capture else capture.get('status')}"]
    if doc is None:
        return [f"{label}: plans.json missing"]
    problems = []
    if doc.get("spark_version") != SPARK_VERSION:
        problems.append(f"{label}: plans from Spark {doc.get('spark_version')}, checked for {SPARK_VERSION}")
    if str(doc.get("explain_mode", "")).lower() != "formatted":
        problems.append(f"{label}: plan text in explain mode {doc.get('explain_mode')!r}, the checks read 'formatted'")
    executions = doc.get("executions", [])
    if doc.get("first_execution_id") != 0 or [e["id"] for e in executions] != list(range(len(executions))):
        problems.append(f"{label}: the plans do not cover every SQL execution of the process (ids 0 to "
                        f"{len(executions) - 1} without gaps)")
    requested = int(CONFIGS[config_name][PARTITIONS])
    coalescing = CONFIGS[config_name][COALESCE] == "true"
    for e in executions:
        where = f"{label}, SQL execution {e['id']}"
        if e.get("error"):
            problems.append(f"{where}: ended with an error")
        adaptive, final = plans.plan_status(e["plan"])
        if adaptive and not final:
            problems.append(f"{where}: adaptive plan not final")
        if counts := requested_counts(e) - {requested}:
            problems.append(f"{where}: exchanges request {sorted(counts)} partitions, not {requested}")
        if ran := [x["partitions"] for x in partitioned(e) if x.get("partitions") != requested]:
            problems.append(f"{where}: exchanges wrote {ran} partitions at runtime, not {requested}")
        if not coalescing and has_coalesced_read(e):
            problems.append(f"{where}: a shuffle read is marked coalesced")
    return problems


def plan_observations(doc: dict | None) -> dict:
    """The plan columns of the CSV (observations, not criteria)."""
    keys = ["sql_executions", "adaptive_plans", "requested_partitions", "coalesced_reads", "local_reads",
            *[f"exchanges_{phase}" for phase in PHASES], *[f"reads_{phase}" for phase in PHASES],
            "broadcast_joins", "sort_merge_joins"]
    if not doc:
        return dict.fromkeys(keys, "")
    exchanges = {phase: [] for phase in PHASES}      # partitions each exchange wrote at runtime
    reads = {phase: [] for phase in PHASES}          # marked reads; an unmarked read reads all of its exchange
    executions = doc["executions"]
    for e in executions:
        for phase in e["phase"].split("+"):
            if phase in exchanges:
                exchanges[phase] += [str(x.get("partitions")) for x in partitioned(e)]
                reads[phase] += [f"{read['mark'] or 'unmarked'}:{read['partitions']}" for read in e["shuffle_reads"]]
    all_reads = [read for e in executions for read in e["shuffle_reads"]]
    joins = [join for e in executions for join in e["joins"]]
    return {
        "sql_executions": len(executions),
        "adaptive_plans": sum(bool(e["adaptive"]) for e in executions),
        "requested_partitions": ";".join(str(n) for n in sorted(set().union(*map(requested_counts, executions)))),
        "coalesced_reads": sum("coalesced" in read["mark"] for read in all_reads),
        "local_reads": sum(read["mark"] == "local" for read in all_reads),
        **{f"exchanges_{phase}": ";".join(values) for phase, values in exchanges.items()},
        **{f"reads_{phase}": ";".join(values) for phase, values in reads.items()},
        "broadcast_joins": joins.count("BroadcastHashJoin"),
        "sort_merge_joins": joins.count("SortMergeJoin"),
    }


def file_counts(run_dir: Path) -> dict:
    return {f"files_{table}": sum(1 for _ in (run_dir / table).rglob("*.parquet")) if (run_dir / table).is_dir() else ""
            for table in OUTPUT_TABLES}


# --- criterion 4: outputs ------------------------------------------------------------

def read_table(run_dir: Path, name: str) -> pa.Table:
    return pq.read_table(run_dir / name)


def compare_tables(ref: pa.Table, run: pa.Table, key: list[str], breach: list[str],
                   rtol: float = RTOL, atol: float = ATOL) -> tuple[list[str], dict]:
    """Section 7: (problems, largest differences per floating-point column). Rows are matched by `key`,
    and key, breach, string, date, integer and boolean columns must be equal exactly."""
    problems, diffs = [], {}
    if run.num_rows != ref.num_rows:
        problems.append(f"{run.num_rows} rows; the reference has {ref.num_rows}")
    ref_types, run_types = ({f.name: f.type for f in t.schema} for t in (ref, run))
    if run_types != ref_types:
        problems.append(f"columns differ: missing {sorted(set(ref_types) - set(run_types))}, extra "
                        f"{sorted(set(run_types) - set(ref_types))}, other type "
                        f"{sorted(n for n in set(ref_types) & set(run_types) if ref_types[n] != run_types[n])}")
    if any(k not in ref_types or k not in run_types for k in key):
        return problems + [f"key columns {key} missing"], diffs
    key_problems = []
    keysets = {}
    for name, table in (("run", run), ("reference", ref)):
        if nulls := [k for k in key if table.column(k).null_count]:
            key_problems.append(f"{name}: null in key columns {nulls}")
        keys = list(zip(*(table.column(k).to_pylist() for k in key)))
        keysets[name] = set(keys)
        if len(keysets[name]) != len(keys):
            key_problems.append(f"{name}: {len(keys) - len(keysets[name])} duplicate keys")
    if keysets["run"] != keysets["reference"]:
        key_problems.append(f"keys differ: {len(keysets['reference'] - keysets['run'])} missing, "
                            f"{len(keysets['run'] - keysets['reference'])} extra")
    if key_problems:
        return problems + key_problems, diffs
    order = [(k, "ascending") for k in key]
    ref, run = ref.sort_by(order), run.sort_by(order)
    for name in sorted(set(ref_types) & set(run_types) - set(key)):
        x_col, r_col = run.column(name), ref.column(name)
        label = f"breach field {name}" if name in breach else name
        x_null = np.asarray(x_col.is_null().to_pylist(), dtype=bool)
        r_null = np.asarray(r_col.is_null().to_pylist(), dtype=bool)
        if not np.array_equal(x_null, r_null):
            problems.append(f"{label}: null in {int((x_null != r_null).sum())} rows where the reference is not, "
                            "or the reverse")
            continue
        if pa.types.is_floating(ref_types[name]) and name not in breach:
            valid = ~r_null
            x = np.asarray(x_col.to_numpy(), dtype=float)[valid]
            r = np.asarray(r_col.to_numpy(), dtype=float)[valid]
            x_nan, r_nan = np.isnan(x), np.isnan(r)
            if not np.array_equal(x_nan, r_nan):
                problems.append(f"{label}: NaN in {int((x_nan != r_nan).sum())} rows where the reference has a "
                                "number, or the reverse")
            both = ~x_nan & ~r_nan
            delta, scale = np.abs(x[both] - r[both]), np.abs(r[both])
            relative = np.divide(delta, scale, out=np.zeros_like(delta), where=scale > 0)
            diffs[name] = {"max_abs": float(delta.max(initial=0.0)), "max_rel": float(relative.max(initial=0.0))}
            if over := int((delta > atol + rtol * scale).sum()):
                problems.append(f"{label}: {over} values outside |x - r| <= {atol:g} + {rtol:g} * |r|")
        else:
            x_values, r_values = x_col.to_pylist(), r_col.to_pylist()
            if differing := sum(a != b for a, b in zip(x_values, r_values)):
                problems.append(f"{label}: {differing} values differ")
    return problems, diffs


def total_violations(run: dict) -> int | None:
    checks = run.get("checks")
    return sum(v for group in checks.values() for v in group.values()) if checks else None


# --- --check-protocol ----------------------------------------------------------------

def check_protocol_plans(protocol_path: Path) -> list[str]:
    """3.4: after each protocol, every run must have captured its plans."""
    protocol = read_json(protocol_path)
    problems = []
    for entry, run, run_dir in load_runs(protocol_path, protocol):
        label = entry["run_id"]
        if run is None:
            problems.append(f"{label}: no run.json")
            continue
        capture = run.get("plan_capture")
        if not capture:
            problems.append(f"{label}: no plan capture recorded (was --record-plans passed?)")
        elif capture.get("status") != "ok":
            problems.append(f"{label}: plan capture {capture.get('status')}: {str(capture.get('error', ''))[-300:]}")
        elif not (run_dir / "plans.json").is_file():
            problems.append(f"{label}: plans.json missing")
    return problems


def check_protocol(protocol_path: Path, config_name: str | None = None) -> list[str]:
    """The check after each protocol (3.4). With a configuration, each run's recorded settings and
    plans must also match it (6), so a wrong setting stops the session at once, not after the batch."""
    problems = check_protocol_plans(protocol_path)
    if config_name is not None:
        for entry, run, run_dir in load_runs(protocol_path, read_json(protocol_path)):
            if run is None:
                continue
            problems += check_settings(entry["run_id"], config_name, run)
            doc = load_plans(run_dir)
            if doc is not None and (run.get("plan_capture") or {}).get("status") == "ok":
                problems += check_plans(entry["run_id"], config_name, run["plan_capture"], doc)
    return problems


# --- the whole batch -----------------------------------------------------------------

def collect(batch: Path, windows: Path, stride_run: Path | None, repeats: int) -> tuple[list[dict], dict]:
    """(CSV rows, acceptance document) for one batch."""
    criteria = {name: [] for name in CRITERIA}
    notes: dict = {}
    positions_path = batch / "positions.tsv"
    rows = read_positions(positions_path) if positions_path.is_file() else []
    if not rows:
        criteria["5 completeness"].append(f"{positions_path} is missing or empty")
    used = used_protocols(rows)
    position_of = {row["protocol"]: row["position"] for row in rows}
    protocols = find_protocols(batch)
    loaded = {}
    for protocol_id, (config_name, path) in protocols.items():
        protocol = read_json(path)
        loaded[protocol_id] = (config_name, path, protocol, load_runs(path, protocol))

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
        config_name, _, protocol, runs = loaded[protocol_id]
        if row["config"] != expected or config_name != expected:
            criteria["5 completeness"].append(f"position {position}: protocol {protocol_id} is configuration "
                                              f"{config_name} (positions.tsv: {row['config']}), not {expected}")
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
    criteria["1 code state"], notes["commits"] = check_code_state(records)

    # criterion 2: inputs, and the inputs still unchanged now
    config = read_json(windows / "config.json")
    try:
        verify_checksums(windows)
    except (ChecksumError, FileNotFoundError, KeyError) as exc:
        criteria["2 inputs"].append(f"the window set's inputs changed after the session: {exc}")

    # the reference run (7) and the stride experiment's run
    reference_dir = None
    if 1 in used_ids and used_ids[1] in loaded:
        _, path, _, _ = loaded[used_ids[1]]
        reference_dir = path.parent / f"run-{used_ids[1]}-2"
    reference = {}
    if reference_dir is not None and (reference_dir / "run.json").is_file():
        reference = {"run": read_json(reference_dir / "run.json"),
                     **{table: read_table(reference_dir, table) for table in TABLE_KEYS}}
    else:
        criteria["4 results"].append(f"no reference run (run 2 of the used protocol at position 1): {reference_dir}")

    used_set = set(used_ids.values())
    csv_rows, settings_seen, float_diffs = [], {}, {}
    for protocol_id, (config_name, path, protocol, runs) in sorted(loaded.items()):
        is_used = protocol_id in used_set
        for entry, run, run_dir in runs:
            label = entry["run_id"]
            doc = load_plans(run_dir)
            row = {"batch": batch.name, "position": position_of.get(protocol_id, ""), "config": config_name,
                   "used": is_used, "protocol_id": protocol_id, "run_id": label,
                   "run_number": int(label.rsplit("-", 1)[1]), "warmup": entry["warmup"], "status": entry["status"],
                   "exit_code": entry["exit_code"]}
            row.update(measurement_columns(run) if run else dict.fromkeys(MEASUREMENT_FIELDS, ""))
            capture = run.get("plan_capture") if run else None
            plan_s = (run or {}).get("timings_seconds", {}).get("plan_capture")
            wall = (run or {}).get("measurement", {}).get("wall_seconds")
            row.update({
                "coalesce_enabled": (run or {}).get("spark", {}).get(COALESCE, "") == "true" if run else "",
                "plan_capture_status": capture.get("status", "") if capture else "",
                "plan_capture_s": plan_s if plan_s is not None else "",
                "wall_excl_capture_s": round(wall - plan_s, 3) if wall is not None and plan_s is not None else "",
                **plan_observations(doc), **file_counts(run_dir),
                **dict.fromkeys((f"{table}_vs_reference" for table in TABLE_KEYS), ""),
            })
            if run is None:
                if is_used:
                    criteria["4 results"].append(f"{label}: no run.json")
                csv_rows.append(row)
                continue
            criteria["2 inputs"] += check_inputs(label, run, config)
            if is_used:
                criteria["3 settings"] += check_settings(label, config_name, run)
                criteria["3 settings"] += check_plans(label, config_name, capture, doc)
                settings_seen.setdefault(common_settings(run), []).append(label)
                if run.get("status") != "ok" or total_violations(run) != 0:
                    criteria["4 results"].append(f"{label}: status {run.get('status')}, "
                                                 f"{total_violations(run)} check violations")
            if reference and run_dir != reference_dir:
                for table, key in TABLE_KEYS.items():
                    problems, diffs = compare_tables(reference[table], read_table(run_dir, table), key,
                                                     BREACH_FIELDS[table])
                    row[f"{table}_vs_reference"] = "fail" if problems else "pass"
                    if problems and is_used:
                        criteria["4 results"] += [f"{label} {table}: {p}" for p in problems]
                    for column, d in diffs.items():
                        best = float_diffs.setdefault(f"{table}.{column}", {"max_abs": 0.0, "max_rel": 0.0})
                        best["max_abs"], best["max_rel"] = max(best["max_abs"], d["max_abs"]), max(best["max_rel"], d["max_rel"])
                for table in COUNTED_TABLES:
                    if run.get("row_counts", {}).get(table) != reference["run"]["row_counts"].get(table):
                        if is_used:
                            criteria["4 results"].append(f"{label}: {table} has {run.get('row_counts', {}).get(table)} "
                                                         f"rows; the reference has {reference['run']['row_counts'].get(table)}")
            elif run_dir == reference_dir:
                row.update(dict.fromkeys((f"{table}_vs_reference" for table in TABLE_KEYS), "reference"))
            csv_rows.append(row)
    if len(settings_seen) > 1:
        groups = sorted(settings_seen.values(), key=len, reverse=True)
        criteria["3 settings"].append(f"recorded Spark settings or environment differ: {len(groups)} groups, the "
                                      f"smaller ones {groups[1:]}")
    notes["float_differences_to_reference"] = float_diffs

    # the stride experiment's stride-7 run: same settings as A, earlier code (7)
    notes["stride_run"] = None
    if stride_run is not None and reference:
        stride_record = read_json(stride_run / "run.json")
        result = {"run": str(stride_run), "problems": [], "settings_differences": []}
        for table, key in TABLE_KEYS.items():
            problems, diffs = compare_tables(reference[table], read_table(stride_run, table), key, BREACH_FIELDS[table])
            result["problems"] += [f"{table}: {p}" for p in problems]
            result[f"{table}_float_differences"] = diffs
        for table in COUNTED_TABLES:
            if stride_record["row_counts"].get(table) != reference["run"]["row_counts"].get(table):
                result["problems"].append(f"{table}: row counts differ")
        ref_spark, stride_spark = reference["run"]["spark"], stride_record["spark"]
        result["settings_differences"] = sorted(k for k in set(ref_spark) | set(stride_spark)
                                                if ref_spark.get(k) != stride_spark.get(k))
        criteria["4 results"] += [f"stride-experiment run: {p}" for p in result["problems"]]
        notes["stride_run"] = result

    acceptance = {
        "batch": str(batch), "windows": str(windows), "repeats": repeats,
        "reference_run": str(reference_dir) if reference_dir else None,
        "used_protocols": {str(p): used_ids[p] for p in sorted(used_ids)},
        "criteria": {name: {"ok": not problems, "problems": problems} for name, problems in criteria.items()},
        "all_ok": not any(criteria.values()),
        "notes": notes,
    }
    return csv_rows, acceptance


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
    print("used protocols (position, configuration, measured ok runs, median wall_excl_capture_s, median peak GiB):")
    for position, protocol_id in acceptance["used_protocols"].items():
        measured = [r for r in rows if r["protocol_id"] == protocol_id and not r["warmup"] and r["status"] == "ok"]
        walls = [r["wall_excl_capture_s"] for r in measured if r["wall_excl_capture_s"] != ""]
        peaks = [r["peak_rss_total_bytes"] / 2**30 for r in measured if r["peak_rss_total_bytes"] != ""]
        config = measured[0]["config"] if measured else "?"
        print(f"    {position} {config} {protocol_id}: {len(measured)} runs, "
              f"{statistics.median(walls):.3f} s, {statistics.median(peaks):.3f} GiB" if walls and peaks
              else f"    {position} {config} {protocol_id}: {len(measured)} measured ok runs")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--batch", type=Path, help="batch folder, for example data/outputs-partitions/batch-1")
    parser.add_argument("--check-protocol", type=Path, help="check one protocol's plan capture and exit")
    parser.add_argument("--config", choices=sorted(CONFIGS),
                        help="with --check-protocol: also check the runs' settings and plans against this configuration")
    parser.add_argument("--windows", type=Path, default=WINDOWS, help="the window set the runs must have used")
    parser.add_argument("--stride-run", default=str(STRIDE_RUN),
                        help="stride-experiment run compared with the reference, or 'none'")
    parser.add_argument("--repeats", type=int, default=REPEATS, help="runs per protocol")
    args = parser.parse_args(argv)
    if args.check_protocol:
        problems = check_protocol(args.check_protocol, args.config)
        runs = len(read_json(args.check_protocol)["runs"])
        what = "plans and settings" if args.config else "plans"
        print(f"{what}: ok in {runs} of {runs} runs" if not problems else f"{what}: PROBLEM\n  " + "\n  ".join(problems))
        return 1 if problems else 0
    if not args.batch:
        parser.error("give --batch or --check-protocol")
    if args.repeats < 2:
        parser.error("--repeats must be at least 2: the reference is a protocol's run 2")
    stride_run = None if args.stride_run == "none" else Path(args.stride_run)
    rows, acceptance = collect(args.batch, args.windows, stride_run, args.repeats)
    write_csv(rows, args.batch / "measurements.csv")
    (args.batch / "acceptance.json").write_text(json.dumps(acceptance, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"{len(rows)} rows -> {args.batch / 'measurements.csv'}; criteria -> {args.batch / 'acceptance.json'}")
    print_summary(rows, acceptance)
    return 0 if acceptance["all_ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
