"""Collect one batch of the caching experiment and evaluate its acceptance criteria.

docs/caching-experiment.md, sections 4.3, 6, 7 and 10. A batch folder holds:

    positions.tsv   one line per protocol the session helpers ran (docs/caching-session.zsh)
    run-log.txt     the session's run log (for people; not read here)
    A/, B/, C/      each configuration's out-root: <snapshot>/<window set>/protocol-*.json, run-*/

Run from the repository root:

    uv run python analysis/collect_caching_measurements.py --batch data/outputs-caching/batch-1
    uv run python analysis/collect_caching_measurements.py --check-protocol <protocol JSON> --config A

The first form writes measurements.csv (one row per started run) and acceptance.json (each
acceptance criterion with the problems found, plus observations) into the batch folder, prints a
summary, and exits with 1 if any criterion fails. The second form, which the session helpers run
after each protocol, checks every run of that protocol against its configuration: the recorded
settings, the plan capture and the cache verification of section 6 (3.4). A run that failed or was
aborted may lack its run.json, plans or output tables; both forms report that as a problem under
the criteria instead of stopping.

The rules it shares with the shuffle-partition experiment are that experiment's collector's
functions, imported unchanged: positions, protocols and runs, code state, inputs, the comparison of
tables by their full keys, file counts and check violations.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_caching_collector.py
and on a small window set (docs/caching-experiment.md 4.5).
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
CACHE = {"A": "none", "B": "members", "C": "members-checks"}           # 2.1: --cache per configuration
OPTIONS = {config: {"shuffle_partitions": None, "coalesce": None, "record_plans": True, "cache": mode}
           for config, mode in CACHE.items()}
SPARK_DEFAULTS = {cpm.PARTITIONS: "200", cpm.ADAPTIVE: "true", cpm.COALESCE: "true"}
PHASES = ("window_stats", "model", "summaries", "checks")
TABLES = ("members", "window_stats", "path_days", "path_summary", "paired")
CACHED = {"A": (), "B": ("members",), "C": TABLES}
FILLED_IN = {"members": "window_stats", "window_stats": "window_stats", "path_days": "model",
             "path_summary": "summaries", "paired": "summaries"}
RELEASED_IN = {"members": "model", "window_stats": "checks", "path_days": "checks", "path_summary": "checks",
               "paired": "checks"}
HELD_AT_END_OF = {                                   # 6: the tables cached when each phase ends
    "A": {phase: () for phase in PHASES},
    "B": {"window_stats": ("members",), "model": (), "summaries": (), "checks": ()},
    "C": {"window_stats": ("members", "window_stats"), "model": ("window_stats", "path_days"),
          "summaries": ("window_stats", "path_days", "path_summary", "paired"), "checks": ()},
}
READ_IN = {"A": (), "B": ("window_stats", "model"), "C": PHASES}       # 6.4: phases with downstream cached reads
FILL_PREFIX = "cache fill: "                         # spark_pipeline.FILL_DESCRIPTION: a fill's SQL execution (4.1)
STORAGE_LEVEL = "Disk Memory Deserialized 1x Replicated"               # MEMORY_AND_DISK_DESER
ROW_COUNT_OF = {"window_stats": "window_stats", "path_days": "path_days", "path_summary": "summary",
                "paired": "paired"}                                    # run.json row_counts names
ORDER = ("A", "B", "C", "C", "B", "A")               # positions 1 to 6 (2.3)
WINDOWS = cpm.WINDOWS
REPEATS = 4
SPARK_VERSION = "4.2.0"
PLANS_FORMAT = 2
TABLE_KEYS = {"window_stats": list(WINDOW_KEY), "path_days": [*PATH_KEY, "day"], "path_summary": list(PATH_KEY),
              "paired": list(WINDOW_KEY)}
CRITERIA = cpm.CRITERIA

IDENTITY_FIELDS = ["batch", "position", "config", "used", "protocol_id", "run_id", "run_number", "warmup", "status",
                   "exit_code"]
EXTRA_FIELDS = (["cache_mode", "plan_capture_status", "plan_capture_s", "wall_excl_capture_s", "sql_executions",
                 "fill_executions", "storage_info_s"]
                + [f"{table}_{field}" for table in TABLES for field in ("fill_s", "release_s", "memory_bytes", "disk_bytes")]
                + [f"cached_reads_{phase}" for phase in (*PHASES, "bookkeeping")]
                + [f"files_{table}" for table in cpm.OUTPUT_TABLES] + [f"{table}_vs_reference" for table in TABLE_KEYS])
FIELDS = IDENTITY_FIELDS + cpm.MEASUREMENT_FIELDS + EXTRA_FIELDS


def read_table(run_dir: Path, name: str) -> pa.Table:
    """A table with the ticker partition column as plain strings (path_days is partitioned by ticker)."""
    table = pq.read_table(run_dir / name)
    if "ticker" in table.column_names and pa.types.is_dictionary(table.schema.field("ticker").type):
        table = table.set_column(table.column_names.index("ticker"), "ticker", table["ticker"].cast(pa.string()))
    return table


def output_state(run_dir: Path, name: str) -> str:
    """'' for a complete output table, else why not. Spark writes _SUCCESS when a table's write commits,
    so a run that failed or was aborted may leave a table missing or incomplete (7)."""
    if not (run_dir / name).is_dir():
        return "missing"
    return "" if (run_dir / name / "_SUCCESS").is_file() else "incomplete (no _SUCCESS marker)"


def read_output(run_dir: Path, name: str) -> tuple[pa.Table | None, str]:
    """(table, '') for a complete, readable output table; otherwise (None, why), never an exception."""
    if state := output_state(run_dir, name):
        return None, state
    try:
        return read_table(run_dir, name), ""
    except (OSError, pa.ArrowException) as exc:
        return None, f"unreadable ({type(exc).__name__})"


def load_plans(run_dir: Path) -> dict | None:
    """The run's plans.json, or None if it is missing or cannot be parsed, as when a run is killed while
    writing it; criterion 3 reports both."""
    try:
        return cpm.load_plans(run_dir)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


def member_rows(windows: Path) -> int:
    """The window-member rows the run must cache: the sum of window_days over the verified window set."""
    config = json.loads((windows / "config.json").read_text())
    return int(pq.read_table(windows / config["windows_file"], columns=["window_days"])["window_days"]
               .to_numpy().sum())


# --- criterion 3: settings, plan capture and cache verification (6) ----------------

def check_settings(label: str, config: str, run: dict) -> list[str]:
    """6.1: the configuration's option and Spark's defaults for the partition settings."""
    problems = []
    if run.get("pipeline_options") != OPTIONS[config]:
        problems.append(f"{label}: pipeline options {run.get('pipeline_options')} instead of {OPTIONS[config]}")
    spark = run.get("spark") or {}
    for key, value in SPARK_DEFAULTS.items():
        if spark.get(key) != value:
            problems.append(f"{label}: {key} is {spark.get(key)!r}; Spark's default is {value!r}")
    return problems


def check_plan_capture(label: str, capture: dict | None, doc: dict | None) -> list[str]:
    """6.2: a complete capture of final plans; the partition counts are not this experiment's question."""
    if not capture or capture.get("status") != "ok":
        return [f"{label}: plan capture {'missing' if not capture else capture.get('status')}"]
    if doc is None:
        return [f"{label}: plans.json missing or unreadable"]
    problems = []
    if doc.get("format") != PLANS_FORMAT:
        problems.append(f"{label}: plans format {doc.get('format')}, the scan nodes need format {PLANS_FORMAT}")
    if doc.get("spark_version") != SPARK_VERSION:
        problems.append(f"{label}: plans from Spark {doc.get('spark_version')}, checked for {SPARK_VERSION}")
    if str(doc.get("explain_mode", "")).lower() != "formatted":
        problems.append(f"{label}: plan text in explain mode {doc.get('explain_mode')!r}")
    executions = doc.get("executions", [])
    if doc.get("first_execution_id") != 0 or [e["id"] for e in executions] != list(range(len(executions))):
        problems.append(f"{label}: the plans do not cover every SQL execution of the process without gaps")
    for e in executions:
        if e.get("error"):
            problems.append(f"{label}, SQL execution {e['id']}: ended with an error")
        if e.get("adaptive") and e.get("final") is not True:
            problems.append(f"{label}, SQL execution {e['id']}: adaptive plan not final")
    return problems


def cache_scans(doc: dict | None) -> tuple[list[dict], dict[str, dict[str, int]]]:
    """(fills, downstream reads) in the plans (6.4). A fill is a SQL execution whose description names it
    as one (4.1); its count() reads the cache it fills. Every InMemoryTableScan of any other execution is a
    downstream read, counted per phase by the state of its row metric: rows > 0, rows = 0, or missing."""
    fills = []
    reads = {phase: {"positive": 0, "zero": 0, "missing": 0} for phase in (*PHASES, "bookkeeping", "")}
    for e in (doc or {}).get("executions", []):
        scans = [s for s in e.get("scans", []) if s["node"] == "InMemoryTableScan"]
        description = e.get("description") or ""
        if description.startswith(FILL_PREFIX):
            fills.append({"table": description.removeprefix(FILL_PREFIX), "phase": e["phase"], "id": e["id"],
                          "cached_reads": len(scans)})
            continue
        for scan in scans:
            state = "missing" if scan["rows"] is None else "zero" if scan["rows"] == 0 else "positive"
            for phase in e["phase"].split("+"):
                reads.setdefault(phase, {"positive": 0, "zero": 0, "missing": 0})[state] += 1
    return fills, reads


def check_cache(label: str, config: str, run: dict, doc: dict | None, members: int) -> list[str]:
    """6.3 and 6.4: storage info, the primary proof; then, in the plans, each fill and, apart from the fills,
    the downstream reads of cached data in each phase."""
    cache = run.get("cache")
    if not cache:
        return [f"{label}: no cache section"]
    problems = []
    if cache.get("mode") != CACHE[config]:
        problems.append(f"{label}: cache mode {cache.get('mode')!r}, configuration {config} is {CACHE[config]!r}")
    tables = cache.get("tables") or {}
    if set(tables) != set(CACHED[config]):
        problems.append(f"{label}: cached tables {sorted(tables)}, configuration {config} caches {sorted(CACHED[config])}")
    counts = run.get("row_counts") or {}
    expected_rows = {"members": members, **{t: counts.get(c) for t, c in ROW_COUNT_OF.items()}}
    rdd_of = {}
    for name in CACHED[config]:
        entry = tables.get(name)
        if entry is None:
            continue
        where = f"{label}, {name}"
        if entry.get("filled_in") != FILLED_IN[name]:
            problems.append(f"{where}: filled in {entry.get('filled_in')!r}, not {FILLED_IN[name]!r}")
        if entry.get("rows") != expected_rows[name]:
            problems.append(f"{where}: the fill counted {entry.get('rows')} rows, not {expected_rows[name]}")
        after = entry.get("after_fill") or []
        if len(after) != 1:
            problems.append(f"{where}: {len(after)} cached RDDs after the fill, not 1")
        else:
            rdd = after[0]
            rdd_of[name] = rdd["rdd_id"]
            if not 0 < rdd["cached_partitions"] == rdd["partitions"]:
                problems.append(f"{where}: {rdd['cached_partitions']} of {rdd['partitions']} partitions cached after the fill")
            if rdd["storage_level"] != STORAGE_LEVEL:
                problems.append(f"{where}: storage level {rdd['storage_level']!r}, not {STORAGE_LEVEL!r}")
            if rdd["memory_bytes"] + rdd["disk_bytes"] <= 0:
                problems.append(f"{where}: no bytes cached after the fill")
        before = entry.get("before_release") or []
        if not (len(before) == 1 and before[0]["rdd_id"] == rdd_of.get(name)
                and 0 < before[0]["cached_partitions"] == before[0]["partitions"]):
            problems.append(f"{where}: not fully cached just before its release")
        if entry.get("released_by") != "plan" or entry.get("released_in") != RELEASED_IN[name]:
            problems.append(f"{where}: released by {entry.get('released_by')!r} in {entry.get('released_in')!r}, "
                            f"not by the plan in {RELEASED_IN[name]!r}")
        if entry.get("cached_after_release"):
            problems.append(f"{where}: still cached after its release")
    snapshots = {s["at"]: sorted(i["rdd_id"] for i in s["cached"]) for s in cache.get("snapshots", [])}
    for phase in PHASES:
        if phase not in snapshots:
            problems.append(f"{label}: no storage reading at the end of {phase}")
            continue
        expected = sorted(rdd_of[name] for name in HELD_AT_END_OF[config][phase] if name in rdd_of)
        if snapshots[phase] != expected:
            problems.append(f"{label}: cached RDDs at the end of {phase} {snapshots[phase]}, expected {expected}")
    if doc is None:                                  # check_plan_capture reports the missing plans
        return problems
    fills, reads = cache_scans(doc)
    filled: dict[str, list[dict]] = {}
    for fill in fills:
        filled.setdefault(fill["table"], []).append(fill)
    for name in sorted(set(filled) - set(CACHED[config])):
        problems.append(f"{label}: a fill of {name} in the plans; configuration {config} does not cache it")
    for name in CACHED[config]:
        found = filled.get(name, [])
        if len(found) != 1:
            problems.append(f"{label}, {name}: {len(found)} fill executions in the plans, not 1")
        elif found[0]["phase"] != FILLED_IN[name]:
            problems.append(f"{label}, {name}: its fill execution is in {found[0]['phase']!r}, not {FILLED_IN[name]!r}")
        elif not found[0]["cached_reads"]:
            problems.append(f"{label}, {name}: its fill execution reads no cached data")
    for phase, states in reads.items():
        if phase in READ_IN[config]:
            if states["positive"] + states["zero"] == 0:
                problems.append(f"{label}: no downstream cached read with a row metric in {phase} "
                                f"({states['missing']} with the metric missing)")
        elif count := sum(states.values()):
            problems.append(f"{label}: {count} downstream cached reads in {phase or 'executions without a phase'}, "
                            f"where configuration {config} reads no cache")
    return problems


def check_protocol(protocol_path: Path, config: str) -> list[str]:
    """The check after each protocol (3.4): status, settings, plan capture and caches of every run. The
    member rows expected are those of the window set each run recorded; criterion 2 checks that set
    itself. A run that was aborted has only the run.json that measure wrote, without a window set."""
    protocol = cpm.read_json(protocol_path)
    problems = []
    members = None
    for entry, run, run_dir in cpm.load_runs(protocol_path, protocol):
        label = entry["run_id"]
        if entry["status"] != "ok":
            problems.append(f"{label}: ended {entry['status']}")
        if run is None:
            problems.append(f"{label}: no run.json")
            continue
        if members is None and run.get("windows_dir"):
            members = member_rows(Path(run["windows_dir"]))
        doc = load_plans(run_dir)
        problems += check_settings(label, config, run)
        problems += check_plan_capture(label, run.get("plan_capture"), doc)
        problems += check_cache(label, config, run, doc, members)
    return problems


# --- rows ------------------------------------------------------------------------------

def cache_columns(run: dict | None, doc: dict | None) -> dict:
    cache = (run or {}).get("cache") or {}
    row = {"cache_mode": cache.get("mode", ""), "storage_info_s": cache.get("storage_info_s", "")}
    for table in TABLES:
        entry = (cache.get("tables") or {}).get(table) or {}
        rdd = (entry.get("after_fill") or [{}])[0]
        row.update({f"{table}_fill_s": entry.get("fill_s", ""), f"{table}_release_s": entry.get("release_s", ""),
                    f"{table}_memory_bytes": rdd.get("memory_bytes", ""), f"{table}_disk_bytes": rdd.get("disk_bytes", "")})
    fills, reads = cache_scans(doc) if doc else ([], {})
    row["fill_executions"] = len(fills) if doc else ""
    for phase in (*PHASES, "bookkeeping"):                  # downstream reads only: the fills are counted apart
        states = reads.get(phase)
        row[f"cached_reads_{phase}"] = f"{states['positive']}/{states['zero']}/{states['missing']}" if states else ""
    return row


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
    for protocol_id, (config, path) in cpm.find_protocols(batch).items():
        protocol = cpm.read_json(path)
        loaded[protocol_id] = (config, path, protocol, cpm.load_runs(path, protocol))

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
        config, _, protocol, runs = loaded[protocol_id]
        if row["config"] != expected or config != expected:
            criteria["5 completeness"].append(f"position {position}: protocol {protocol_id} is configuration "
                                              f"{config} (positions.tsv: {row['config']}), not {expected}")
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
    config_json = cpm.read_json(windows / "config.json")
    try:
        verify_checksums(windows)
    except (ChecksumError, FileNotFoundError, KeyError) as exc:
        criteria["2 inputs"].append(f"the window set's inputs changed after the session: {exc}")
    members = member_rows(windows)

    # the reference run (7): run 2 of the used protocol at position 1, A's first measured run
    reference_dir, reference = None, {}
    if 1 in used_ids and used_ids[1] in loaded:
        reference_dir = loaded[used_ids[1]][1].parent / f"run-{used_ids[1]}-2"
    if reference_dir is not None and (reference_dir / "run.json").is_file():
        reference = {"run": cpm.read_json(reference_dir / "run.json")}
    else:
        criteria["4 results"].append(f"no reference run (run 2 of the used protocol at position 1): {reference_dir}")

    used_set = set(used_ids.values())
    csv_rows, settings_seen, float_diffs = [], {}, {}
    reference_tables = {}
    for protocol_id, (config, path, protocol, runs) in sorted(loaded.items()):
        is_used = protocol_id in used_set
        for entry, run, run_dir in runs:
            label = entry["run_id"]
            doc = load_plans(run_dir)
            capture = (run or {}).get("plan_capture")
            plan_s = (run or {}).get("timings_seconds", {}).get("plan_capture")
            wall = (run or {}).get("measurement", {}).get("wall_seconds")
            row = {"batch": batch.name, "position": position_of.get(protocol_id, ""), "config": config,
                   "used": is_used, "protocol_id": protocol_id, "run_id": label,
                   "run_number": int(label.rsplit("-", 1)[1]), "warmup": entry["warmup"], "status": entry["status"],
                   "exit_code": entry["exit_code"]}
            row.update(cpm.measurement_columns(run) if run else dict.fromkeys(cpm.MEASUREMENT_FIELDS, ""))
            row.update({"plan_capture_status": capture.get("status", "") if capture else "",
                        "plan_capture_s": plan_s if plan_s is not None else "",
                        "wall_excl_capture_s": round(wall - plan_s, 3) if wall is not None and plan_s is not None else "",
                        "sql_executions": len(doc["executions"]) if doc else "",
                        **cache_columns(run, doc), **cpm.file_counts(run_dir),
                        **dict.fromkeys((f"{table}_vs_reference" for table in TABLE_KEYS), "")})
            if run is None:
                if is_used:
                    criteria["4 results"].append(f"{label}: no run.json")
                csv_rows.append(row)
                continue
            criteria["2 inputs"] += cpm.check_inputs(label, run, config_json)
            if is_used:
                criteria["3 settings"] += check_settings(label, config, run)
                criteria["3 settings"] += check_plan_capture(label, capture, doc)
                criteria["3 settings"] += check_cache(label, config, run, doc, members)
                settings_seen.setdefault(cpm.common_settings(run), []).append(label)
                if run.get("status") != "ok" or cpm.total_violations(run) != 0:
                    criteria["4 results"].append(f"{label}: status {run.get('status')}, "
                                                 f"{cpm.total_violations(run)} check violations")
            if reference and run_dir != reference_dir:
                for table, key in TABLE_KEYS.items():
                    if table not in reference_tables:
                        reference_tables[table], why = read_output(reference_dir, table)
                        if why:
                            criteria["4 results"].append(f"the reference run's {table}: {why}")
                    output, why = read_output(run_dir, table)
                    if why:                                  # a table that a failed or aborted run left (7)
                        row[f"{table}_vs_reference"] = why.split(" ")[0]
                        if is_used:
                            criteria["4 results"].append(f"{label} {table}: {why}")
                        continue
                    if reference_tables[table] is None:
                        row[f"{table}_vs_reference"] = "no reference"
                        continue
                    problems, diffs = cpm.compare_tables(reference_tables[table], output, key,
                                                         cpm.BREACH_FIELDS.get(table, []))
                    row[f"{table}_vs_reference"] = "fail" if problems else "pass"
                    if problems and is_used:
                        criteria["4 results"] += [f"{label} {table}: {p}" for p in problems]
                    for column, d in diffs.items():
                        best = float_diffs.setdefault(f"{config}.{table}.{column}", {"max_abs": 0.0, "max_rel": 0.0})
                        best["max_abs"], best["max_rel"] = max(best["max_abs"], d["max_abs"]), max(best["max_rel"], d["max_rel"])
            elif run_dir == reference_dir:
                row.update({f"{table}_vs_reference": output_state(run_dir, table).split(" ")[0] or "reference"
                            for table in TABLE_KEYS})
            csv_rows.append(row)
    if len(settings_seen) > 1:
        groups = sorted(settings_seen.values(), key=len, reverse=True)
        criteria["3 settings"].append(f"recorded Spark settings or environment differ: {len(groups)} groups, the "
                                      f"smaller ones {groups[1:]}")
    notes["float_differences_to_reference"] = float_diffs
    notes["member_rows"] = members

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
    """The partition collector's writer, with this experiment's columns."""
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
    parser.add_argument("--batch", type=Path, help="batch folder, for example data/outputs-caching/batch-1")
    parser.add_argument("--check-protocol", type=Path, help="check one protocol's settings, plans and caches and exit")
    parser.add_argument("--config", choices=sorted(CACHE), help="with --check-protocol: the position's configuration")
    parser.add_argument("--windows", type=Path, default=WINDOWS, help="the window set the runs must have used")
    parser.add_argument("--repeats", type=int, default=REPEATS, help="runs per protocol")
    args = parser.parse_args(argv)
    if args.check_protocol:
        if not args.config:
            parser.error("--check-protocol needs --config")
        problems = check_protocol(args.check_protocol, args.config)
        runs = len(cpm.read_json(args.check_protocol)["runs"])
        print(f"settings, plans and caches: ok in {runs} of {runs} runs" if not problems
              else "settings, plans and caches: PROBLEM\n  " + "\n  ".join(problems))
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
