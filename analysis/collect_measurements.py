"""Collect the stride experiment's run records into one CSV (docs/experiments.md, 3.7 and 5.6).

One row per started run, warm-ups and stopped runs included, read only from the records that
etf_risk.measure and etf_risk.spark_pipeline wrote: each protocol-<UTC time>.json and the
run.json of every run it lists. Run from the repository root:

    uv run python analysis/collect_measurements.py [--records FOLDER] [--out FILE]

Steps: B2.1 the rows and identity columns, B2.2 the measurement columns and the code check,
B2.3 the protocol role.

Who wrote what: find_protocols, load_runs and identity_row are the project author's. Claude Code
(Opus 5.5) wrote the outline and, at the author's request, the rest: ROLES, check_protocol,
protocol_role, measurement_columns, write_csv and main.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

RECORDS = Path("data/outputs-experiments/full-2026-10-12")
OUT = Path("data/outputs-experiments/measurements.csv")   # B2.3 decides where the CSV lives
EXPECTED_PROTOCOLS = 5                                     # docs/experiments.md 5.1

# B2.1: identity_row returns these, in output order.
IDENTITY_FIELDS = ["protocol_id", "stride", "run_id", "run_number", "warmup", "status", "exit_code"]
# B2.3: the column that protocol_role fills.
ROLE_FIELD = "role"
# B2.2: measurement_columns returns these. Names carry their units: _s seconds, _bytes bytes.
PHASES = ["session_start", "window_stats_and_construction_check", "model_and_path_days",
          "summaries_and_pairing", "checks", "total_in_process"]     # run.json timings_seconds
TASK_GROUPS = ["window_stats", "model", "summaries", "checks"]      # run.json stage_task_counts
PROCESS_KINDS = ["driver", "spark_jvm", "python_worker", "other"]   # etf_risk.measure.process_kind
MEASUREMENT_FIELDS = (
    ["started_at_utc", "windows", "path_day_rows", "shuffle_partitions_requested", "adaptive_enabled",
     "default_parallelism", "jvm_max_heap_bytes"]
    + [f"tasks_{group}" for group in TASK_GROUPS]
    + ["wall_s"] + [f"{phase}_s" for phase in PHASES]
    + ["free_memory_before_bytes", "peak_rss_total_bytes"] + [f"peak_rss_{kind}_bytes" for kind in PROCESS_KINDS]
    + ["samples", "max_processes_seen", "threshold_crossed", "git_commit", "git_worktree_clean"]
)
FIELDS = IDENTITY_FIELDS + [ROLE_FIELD] + MEASUREMENT_FIELDS

# B2.3: each protocol's role (docs/experiments.md 5.1). The records cannot hold it, so it is listed
# here by protocol id: the planned protocols in their order (3.3), the stride-3 protocol that 3.5
# did not admit and that was run deliberately (5.3), and the repeated stride 21 for the drift check (3.4).
ROLES = {
    "20261019T030242Z": "baseline",      # stride 21, first protocol
    "20261019T034949Z": "planned",       # stride 14
    "20261019T035809Z": "planned",       # stride 7
    "20261019T042741Z": "exploratory",   # stride 3; its folder has EXPLORATORY.txt
    "20261019T043802Z": "drift_check",   # stride 21, repeated
}


def find_protocols(records: Path) -> list[Path]:
    """Every protocol-*.json below `records`: one folder per window set, and the two stride-21
    protocols share a folder."""
    return sorted(records.glob("*/protocol-*.json"))


def load_runs(protocol_path: Path, protocol: dict) -> list[dict]:
    """The run.json of each run in protocol["runs"], in that order. A run's folder sits next to
    the protocol JSON and is named by its run_id; stop with a clear message if one is missing."""
    runs = []

    for entry in protocol["runs"]:
        run_path = protocol_path.parent / entry["run_id"] / "run.json"

        if not run_path.is_file():
            raise SystemExit(f"Missing run record: {run_path}")

        runs.append(json.loads(run_path.read_text(encoding="utf-8")))

    return runs


def check_protocol(protocol_path: Path, protocol: dict, runs: list[dict]) -> None:
    """Stop, naming the protocol and every failing run, unless the protocol and its run records agree:
    - one run.json per started run (protocol["runs_started"]);
    - per run: the same run id, status, warm-up flag and exit code in the protocol and in the
      run.json (its measurement section);
    - code state (3.1): the protocol's and each run's source_sha256 and uv_lock_sha256 equal the
      window config's, with the checked paths clean.
    All problems in the protocol are collected before stopping. A run without a full run.json (an
    aborted run's placeholder) is reported as unsupported: identity_row needs its window config,
    and this experiment has no such run."""
    problems = []
    entries = protocol["runs"]
    if not len(entries) == len(runs) == protocol["runs_started"]:
        problems.append(f"{protocol['runs_started']} runs started, {len(entries)} listed, {len(runs)} run.json loaded")

    hashes = ("source_sha256", "uv_lock_sha256")
    window_code = None
    for entry, run in zip(entries, runs):
        run_id, recorded = entry["run_id"], run.get("measurement", {})
        for name, in_protocol, in_run in (("run id", run_id, run.get("run_id")),
                                          ("status", entry["status"], recorded.get("protocol_status")),
                                          ("warm-up flag", entry["warmup"], recorded.get("warmup")),
                                          ("exit code", entry["exit_code"], recorded.get("exit_code"))):
            if in_protocol != in_run:
                problems.append(f"{run_id}: {name} {in_protocol!r} in the protocol, {in_run!r} in run.json")
        if "code" not in run or "windows_config" not in run:
            problems.append(f"{run_id}: no full run.json (an aborted run's placeholder?), not supported")
            continue
        window_code, code = run["windows_config"]["code"], run["code"]
        if any(code[h] != window_code[h] for h in hashes) or code["git_worktree_clean"] is not True:
            problems.append(f"{run_id}: code state differs from the window config's, or the worktree was not clean")

    if window_code is not None:
        code = protocol["code"]
        if any(code[h] != window_code[h] for h in hashes) or code["git_worktree_clean"] is not True:
            problems.append("protocol: code state differs from the window config's, or the worktree was not clean")
    if problems:
        raise SystemExit(f"{protocol_path}:\n  " + "\n  ".join(problems))


def identity_row(protocol: dict, entry: dict, run: dict) -> dict:
    """The IDENTITY_FIELDS values for one run. `entry` is the run's item in protocol["runs"], `run` its
    run.json. The stride comes from run["windows_config"]["stride"] (recorded when the windows
    were built), the run number from the end of the run id."""
    return {
        "protocol_id": protocol["protocol_started"],
        "stride": run["windows_config"]["stride"],
        "run_id": entry["run_id"],
        "run_number": int(entry["run_id"].rsplit("-", 1)[1]),
        "warmup": run["measurement"]["warmup"],
        "status": entry["status"],
        "exit_code": run["measurement"]["exit_code"],
    }


def protocol_role(protocol_path: Path, protocol: dict) -> str:
    """The protocol's role in docs/experiments.md 5.1, from ROLES: the records cannot say it
    (measure knows nothing of the gate), and it is never inferred from times or values. Stops on
    a protocol missing from ROLES, and unless the EXPLORATORY.txt note sits next to exactly the
    exploratory protocol."""
    protocol_id = protocol["protocol_started"]
    if protocol_id not in ROLES:
        raise SystemExit(f"{protocol_path}: protocol {protocol_id} has no role in ROLES (docs/experiments.md 5.1)")
    role = ROLES[protocol_id]
    noted = (protocol_path.parent / "EXPLORATORY.txt").is_file()
    if noted != (role == "exploratory"):
        raise SystemExit(f"{protocol_path}: role {role!r} disagrees with the EXPLORATORY.txt note "
                         f"({'present' if noted else 'absent'})")
    return role


def measurement_columns(run: dict) -> dict:
    """The MEASUREMENT_FIELDS values for one run, copied from its run.json without rounding.

    A run that did not end ok may lack whole sections (an aborted run's run.json holds only
    measure's measurement), so its missing values are left empty; in a run that ended ok a
    missing value stops the script. A process type that was never sampled is left empty."""
    strict = run.get("status") == "ok"

    def get(*keys: str, optional: bool = False):
        value = run
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                if strict and not optional:
                    raise SystemExit(f"{run.get('run_id', '?')}: run.json has no {' > '.join(keys)}")
                return ""
            value = value[key]
        return value

    partitions = get("spark", "spark.sql.shuffle.partitions")      # recorded as a string, e.g. "200"
    adaptive = get("spark", "spark.sql.adaptive.enabled")           # recorded as "true" or "false"
    exceeded = get("measurement", "threshold_first_exceeded_after_seconds")   # None if never crossed
    return {
        "started_at_utc": get("measurement", "started_at_utc"),
        "windows": get("row_counts", "windows"),
        "path_day_rows": get("row_counts", "path_days"),
        "shuffle_partitions_requested": int(partitions) if partitions != "" else "",
        "adaptive_enabled": adaptive == "true" if adaptive != "" else "",
        "default_parallelism": get("spark", "default_parallelism"),
        "jvm_max_heap_bytes": get("spark", "jvm_max_heap_bytes"),
        **{f"tasks_{group}": get("stage_task_counts", group, "tasks") for group in TASK_GROUPS},
        "wall_s": get("measurement", "wall_seconds"),
        **{f"{phase}_s": get("timings_seconds", phase) for phase in PHASES},
        "free_memory_before_bytes": get("measurement", "free_memory_before_bytes"),
        "peak_rss_total_bytes": get("measurement", "peak_rss_total_bytes"),
        **{f"peak_rss_{kind}_bytes": get("measurement", "peak_rss_by_kind_bytes", kind, optional=True)
           for kind in PROCESS_KINDS},
        "samples": get("measurement", "samples"),
        "max_processes_seen": get("measurement", "max_processes_seen"),
        "threshold_crossed": exceeded is not None if exceeded != "" else "",
        "git_commit": get("code", "git_commit"),
        "git_worktree_clean": get("code", "git_worktree_clean"),
    }


def write_csv(rows: list[dict], out: Path) -> None:
    """Write `rows` under the FIELDS header. The same records must give a byte-identical file:
    fixed column order, fixed line ending, no build time in the file. The CSV is derived from the
    records, so an existing file is replaced."""
    for row in rows:
        missing, extra = set(FIELDS) - set(row), set(row) - set(FIELDS)
        if missing or extra:
            raise SystemExit(f"{row.get('run_id', '?')}: missing columns {sorted(missing)}, unexpected {sorted(extra)}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--records", type=Path, default=RECORDS, help="folder with one subfolder per window set")
    parser.add_argument("--out", type=Path, default=OUT, help="CSV file to write")
    args = parser.parse_args(argv)

    protocol_paths = find_protocols(args.records)
    if len(protocol_paths) != EXPECTED_PROTOCOLS:
        raise SystemExit(f"expected {EXPECTED_PROTOCOLS} protocols in {args.records}, found {len(protocol_paths)}")

    rows = []
    for path in protocol_paths:
        protocol = json.loads(path.read_text(encoding="utf-8"))
        runs = load_runs(path, protocol)
        check_protocol(path, protocol, runs)
        role = protocol_role(path, protocol)
        for entry, run in zip(protocol["runs"], runs, strict=True):
            rows.append({**identity_row(protocol, entry, run), ROLE_FIELD: role, **measurement_columns(run)})

    rows.sort(key=lambda row: (row["protocol_id"], row["run_number"]))   # the stamp sorts as text
    write_csv(rows, args.out)
    print(f"{len(rows)} rows from {len(protocol_paths)} protocols -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
