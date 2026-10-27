"""Collect one batch of the recovery experiments E1 and E2 (docs/recovery-experiments.md,
sections 5 and 6).

A batch folder is what etf_risk.jobs.harness batch wrote:

    harness.jsonl   the harness's events: plan, injections, deadlines, observations, peaks, owners,
                    the host's state (memory, swap in use, page and swap counters, pressure, power,
                    lid) at the start, before each job and at the end, Spark scratch, setup and
                    final errors, the container monitor's record and the power log's sleep and
                    wake entries
    containers.jsonl  every container event from the batch's start to its end (time, action, and
                    whether it is this project's; never a name), since 2026-10-27
    events/         the workers' logs (A.jsonl, B.jsonl), the reconciler's, and submit.jsonl
    jobs/<store>/   the attempts' folders, with logs/*.launcher.json and, when complete, manifest.json
    reference/      the reference run, under the launcher
    crosscheck/     Q0-Q3b as CSV (crosscheck.sql)
    export/         the job tables as JSON (python -m etf_risk.jobs export)
    status-check.txt, cleanup.txt   status --check, and cleanup's dry-run listing
    plan.json       the plan the batch ran

Run from the repository root, on a batch in the folder of its purpose:

    uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/formal/batch-1
    uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/preflight/<name>

It writes into the batch folder:
- injections.csv: one row per planned job, with the case, the injection, the metrics of
  section 5, each n/a with its reason or unknown when its record is missing, the verdicts of
  Q1, Q2 and Q3a, and the host before the job (available memory, memory pressure, power source,
  lid, running containers outside this project) with the bytes paged out, swapped in and
  swapped out until the next reading (pageouts_during_bytes, swapins_during_bytes,
  swapouts_during_bytes; until 2026-10-27 the page-out column was named swap_out_during_bytes,
  and older batches' swap columns are empty: see counters());
- tally.csv: per case, the jobs planned, made, missed, not run and unrecorded, and every verdict value of
  Q1, Q2, deadline_met, Q3a and Q3b, with zeros;
- validity.json: the batch's purpose (preflight or formal, from its plan), the checks of 6.1
  (what counts; a recorded setup or final error fails records_complete; the host protocol's
  power, lid and other-container conditions, where a missing reading fails as unknown), two
  verdicts, and, apart
  from them, the outcome checks of 6.2-6.5, each with what it found (6.5's new Spark scratch
  included), and the sleep and wake evidence of the power log, stated as not recorded where it
  is missing. The verdicts (docs/recovery-part-a.md, section 12): its correctness observations
  stand on the checks that do not involve time; its recovery times need those, the clock check,
  at every reading AC power, the lid open and no running container outside this project, and,
  over the whole batch, no event of another project's container (container_events; a monitor
  that is missing or failed makes it unknown, which fails too).
  A preflight's results are never formal results (8.6), whatever its checks found.
It prints a summary and exits with 1 unless both verdicts are valid: any required check that
failed, has no result or is missing gives 1, and the summary marks the unknown ones. A failed
outcome check is a finding: it is reported and never changes the exit code. Nothing is dropped: a missed or
unrun job keeps its row.

Durations are differences of mono values, from one host's monotonic clock (4.1), and so are
the step intervals: each launcher record's step_started_mono and tree_ended_mono. A record
without them leaves its step's interval missing, which makes the overlap verdict unknown (6.5).

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
Tested with tests/test_recovery_collector.py on synthetic batch folders, and on the batch that
tests/test_recovery_synthetic.py runs end to end without services; no real batch exists.
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import statistics
import sys
from datetime import datetime
from pathlib import Path

from etf_risk.jobs.events import read_events

REPO = Path(__file__).resolve().parents[1]
CASES = ("C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "W6", "W7", "K1", "K2", "D1", "D2", "X1")
REQUEUED_DETECTION = ("W2", "W3", "W4", "W6", "W7")
NO_RECOVERY = {"C0": "no failure", "X1": "no failure", "W5a": "after acceptance", "W5b": "after acceptance"}
NO_OVERHEAD = {"W5a": "after acceptance", "W5b": "after acceptance"}
Q1_VERDICTS = ("ok", "not finished", "failed", "more than one accepted attempt", "succeeded without an accepted attempt",
               "accepted_attempt names another attempt", "accepted attempt of a job that did not succeed",
               "attempt rows differ from attempt_number", "finished with an attempt still running")
Q2_CLASSES = ("on time", "late", "unfinished", "failed", "missing", "deadline not observed")
DEADLINE_MET = ("yes", "no", "unknown")
Q3A_VERDICTS = ("reported once", "no matching report", "one attempt reported more than once",
                "acceptance reported for more than one attempt")
Q3B_VERDICTS = ("matches", "other store", "no such attempt", "wrong worker", "attempt not accepted", "wrong digest")
NOT_RUN = ("not run", "not submitted")
UNRECORDED = ("no record", "no injection record")     # the harness's records lack the job's deadline or injection
CORRECTNESS_CHECKS = ("code_identity", "fingerprints_agree", "inputs_unchanged", "records_complete")
TIMING_CHECKS = (*CORRECTNESS_CHECKS, "clock", "host_power", "host_lid", "other_containers",   # every required check
                 "container_events")
COUNTER_KEYS = ("pageins_bytes", "pageouts_bytes", "swapins_bytes", "swapouts_bytes")
LIVENESS = ("serve_restarted", "retry", "rewound", "gave_up", "failed_after_ack", "consumer_error", "pass_failed")
FIELDS = ["position", "case", "job_id", "status", "missed", "injection", "worker", "t_inj", "reference", "deadline_s",
          "detection_s", "rerun_s", "finish_s", "overhead_s", "claims", "accepted", "executions", "complete_executions",
          "wasted_step_s", "fenced_events", "timeliness", "deadline_met", "q1_verdict", "q3a_verdict",
          "host_available_bytes", "memory_pressure", "power_source", "lid_closed", "other_containers",
          "pageouts_during_bytes", "swapins_during_bytes", "swapouts_during_bytes"]


# Reading the folder

def jsonl(path: Path) -> list[dict]:
    return read_events(path) if path.exists() else []


def named(events: list[dict], event: str, /, **fields_) -> list[dict]:
    return [e for e in events if e.get("event") == event and all(e.get(k) == v for k, v in fields_.items())]


def csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, newline="") as f:
        return [{k: None if v == "NULL" else v for k, v in row.items()} for row in csv.DictReader(f)]


def by_job(rows: list[dict]) -> dict[int, dict]:
    return {int(r["job_id"]): r for r in rows if r.get("job_id") is not None}


class BatchFolder:
    def __init__(self, folder: Path):
        self.folder = folder
        self.harness = jsonl(folder / "harness.jsonl")
        self.workers = {p.stem: read_events(p) for p in sorted((folder / "events").glob("*.jsonl"))
                        if p.stem != "submit" and not p.stem.startswith("reconciler-")}
        self.reconciler = [e for p in sorted((folder / "events").glob("reconciler-*.jsonl")) for e in read_events(p)]
        self.submits = jsonl(folder / "events" / "submit.jsonl")
        self.plan = json.loads((folder / "plan.json").read_text())
        self.q = {name: csv_rows(folder / "crosscheck" / f"{name}.csv") for name in ("Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b")}
        export = folder / "export"
        self.jobs = json.loads((export / "jobs.json").read_text()) if (export / "jobs.json").exists() else []
        self.attempts = (json.loads((export / "job_attempts.json").read_text())
                         if (export / "job_attempts.json").exists() else [])
        store = json.loads((export / "store.json").read_text()) if (export / "store.json").exists() else {}
        self.store_id = store.get("store_id")

    def worker_events(self) -> list[dict]:
        return [{**e, "worker": w} for w, events in self.workers.items() for e in events]

    def first_after(self, events: list[dict], t: float) -> dict | None:
        later = [e for e in events if e.get("mono") is not None and e["mono"] >= t]
        return min(later, key=lambda e: e["mono"]) if later else None

    def attempt_dir(self, run_id: str) -> Path:
        return self.folder / "jobs" / (self.store_id or "") / run_id


# Metrics (section 5)

def utc_seconds(start: str, end: str) -> float:
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def launcher_record(folder: Path, step: str) -> dict | None:
    path = folder / "logs" / f"{step}.launcher.json"
    try:
        return json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def interval(record: dict | None) -> tuple[float, float] | None:
    """A launcher record's step interval on the host's monotonic clock; None without both ends."""
    if not record:
        return None
    start, end = record.get("step_started_mono"), record.get("tree_ended_mono")
    if isinstance(start, (int, float)) and isinstance(end, (int, float)):
        return float(start), float(end)
    return None


def step_intervals(b: BatchFolder) -> tuple[list[tuple], list[str]]:
    """Every started step's interval (monotonic), and the steps that lack one (6.5)."""
    intervals, missing = [], []
    claims = {(e["job_id"], e["attempt"]): e["run_id"] for e in named(b.worker_events(), "claimed")}
    for e in named(b.worker_events(), "step_started"):
        run_id = claims.get((e["job_id"], e["attempt"]))
        span = interval(launcher_record(b.attempt_dir(run_id), e["step"])) if run_id else None
        label = f"{run_id or e['job_id']}:{e['step']}"
        if span:
            intervals.append((*span, label))
        else:
            missing.append(label)
    for step in ("windows", "spark_pipeline"):
        if span := interval(launcher_record(b.folder / "reference", step)):
            intervals.append((*span, f"reference:{step}"))
        else:
            missing.append(f"reference:{step}")
    return sorted(intervals), missing


def overlap_verdict(intervals: list[tuple], missing: list[str]) -> dict:
    """no overlap, overlap, or unknown: a missing interval never counts as no overlap (6.5).
    Each interval that starts before an earlier tree ended is listed with the earlier one
    whose tree ended last."""
    overlaps, latest = [], None
    for start, end, label in intervals:
        if latest is not None and start < latest[1]:
            overlaps.append((latest[2], label))
        if latest is None or end > latest[1]:
            latest = (start, end, label)
    verdict = "overlap" if overlaps else "unknown" if missing else "no overlap"
    return {"verdict": verdict, "overlaps": overlaps, "steps_without_interval": missing,
            "note": "monotonic launcher times (4.1)"}


def job_metrics(b: BatchFolder, position: int, case: str, injection: dict, deadline: dict,
                c0_median: float | None) -> dict:
    job_id = deadline["job_id"]
    events = [e for e in b.worker_events() if e.get("job_id") == job_id]
    t_inj, missed = injection.get("t_inj"), injection.get("missed")
    row = {"detection_s": None, "rerun_s": None, "finish_s": None, "overhead_s": None}
    reason = NO_RECOVERY.get(case)
    if missed:
        row.update(detection_s="n/a: injection missed", rerun_s="n/a: injection missed")
    elif reason:
        row.update(detection_s=f"n/a: {reason}", rerun_s=f"n/a: {reason}")
    elif case == "K1":
        row.update(detection_s="n/a for the job: the attempt goes on", rerun_s="n/a: the attempt goes on")
    elif t_inj is not None:
        if case == "W1":
            detection = b.first_after([e for e in named(events, "delivered") if e["worker"] != injection.get("worker")],
                                      t_inj)
        elif case in REQUEUED_DETECTION:
            detection = b.first_after(named(b.reconciler, "requeued", job_id=job_id), t_inj)
        elif case == "K2":
            detection = b.first_after(named(b.reconciler, "published", job_id=job_id), t_inj)
        elif case == "D1":
            detection = b.first_after(named(events, "renewal_failed"), t_inj)
        else:                                                     # D2: a retried acceptance, or none after F
            detection = b.first_after(named(events, "retry", operation="accept_result")
                                      + named(events, "fenced", during="acceptance"), t_inj)
        row["detection_s"] = detection["mono"] - t_inj if detection else "unknown: no detection event"
        before = [e for e in named(events, "claimed") if e["mono"] < t_inj]
        injected = max((e["attempt"] for e in before), default=0)
        rerun = b.first_after([e for e in named(events, "claimed") if e["attempt"] > injected], t_inj)
        if rerun:
            row["rerun_s"] = rerun["mono"] - t_inj
        elif case in ("D1", "D2"):
            row["rerun_s"] = "n/a: the attempt went on"
        else:
            row["rerun_s"] = "unknown: no new claim"
    else:                                                         # the record of the injection lacks its time
        row.update(detection_s="unknown: no injection time", rerun_s="unknown: no injection time")
    accepted = min(named(events, "accepted"), key=lambda e: e["mono"], default=None)
    from_submit = case == "C0" or missed
    start = deadline.get("t_submit") if from_submit else t_inj
    if case in NO_OVERHEAD and not missed:
        row["finish_s"] = row["overhead_s"] = f"n/a: {NO_OVERHEAD[case]}"
    elif accepted is None:
        row["finish_s"] = row["overhead_s"] = "unknown: no accepted event"
    else:
        row["finish_s"] = (accepted["mono"] - start if start is not None
                           else f"unknown: no {'submit' if from_submit else 'injection'} time")
        if deadline.get("t_submit") is not None and c0_median is not None:
            row["overhead_s"] = accepted["mono"] - deadline["t_submit"] - c0_median
        else:
            row["overhead_s"] = "unknown: no C0 median"
    claims = {e["attempt"]: e["run_id"] for e in named(events, "claimed")}
    row["executions"] = len({e["attempt"] for e in named(events, "step_started", step="windows")})
    row["complete_executions"] = sum(1 for run_id in claims.values() if (b.attempt_dir(run_id) / "manifest.json").exists())
    row["fenced_events"] = len(named(events, "fenced")) + len(named(events, "renewal_refused"))
    row["wasted_step_s"] = wasted_step_time(b, job_id, claims)
    return row


def wasted_step_time(b: BatchFolder, job_id: int, claims: dict[int, str]) -> float | str:
    """The step time of the job's attempts that were not accepted; unknown if a started step has
    no complete launcher record."""
    accepted = {a["attempt_number"] for a in b.attempts if a["job_id"] == job_id and a["outcome"] == "accepted"}
    total = 0.0
    for e in named(b.worker_events(), "step_started", job_id=job_id):
        if e["attempt"] in accepted:
            continue
        span = interval(launcher_record(b.attempt_dir(claims.get(e["attempt"], "")), e["step"]))
        if span is None:
            return f"unknown: no complete record for attempt {e['attempt']} {e['step']}"
        total += span[1] - span[0]
    return total


# Checks (section 6)

def identity_check(b: BatchFolder) -> dict:
    """6.1: one code identity across the harness, every process start and every step launch."""
    seen = []
    for e in named(b.harness, "batch_started") + named(b.harness, "batch_ended"):
        seen.append(("harness", e.get("code")))
    for e in named(b.harness, "process_started"):
        seen.append((e.get("name"), e.get("code")))
    for e in named(b.submits, "started"):
        seen.append(("submit", e.get("code")))
    for e in named(b.worker_events(), "step_started"):
        seen.append((f"{e['worker']} step", e.get("code")))
    pairs = {(c.get("source_digest"), c.get("uv_lock_sha256")) if c else None for _, c in seen}
    return {"passed": len(pairs) == 1 and None not in pairs, "distinct": len(pairs), "records": len(seen)}


def clock_check(b: BatchFolder, tolerance_s: float) -> dict:
    start, end = named(b.harness, "batch_started"), named(b.harness, "batch_ended")
    if not start or not end:
        return {"passed": False, "why": "no batch_started or batch_ended event"}
    a, z = start[0]["clock"], end[-1]["clock"]
    difference = utc_seconds(a["ts"], z["ts"]) - (z["mono"] - a["mono"])
    same = [e.get("same_clock") for e in named(b.harness, "process_started")]
    return {"passed": abs(difference) <= tolerance_s and all(same), "ts_minus_mono_s": difference,
            "tolerance_s": tolerance_s, "processes_on_the_same_clock": f"{sum(map(bool, same))} of {len(same)}"}


def accepted_checks(b: BatchFolder) -> list[dict]:
    """6.2 items 3 and 4 for every accepted attempt: the digest, the result rule from the files,
    and the tables against the reference run by content."""
    from etf_risk import runs
    from etf_risk.jobs.pipeline import TABLES, total_violations
    ccm = _caching_collector()
    reference = next(iter(sorted((b.folder / "reference" / "output").glob("*/*/reference"))), None)
    found = []
    for a in (a for a in b.attempts if a["outcome"] == "accepted"):
        folder = Path(a["output_dir"])
        problems = []
        try:
            record = json.loads((folder / "attempt.json").read_text())
            run_folder = folder / record["run_folder"]
        except (OSError, json.JSONDecodeError, KeyError):
            found.append({"job_id": a["job_id"], "problems": ["no readable attempt.json"]})
            continue
        if runs.folder_digest(run_folder) != a["result_digest"]:
            problems.append("the folder's digest differs from the accepted digest")
        run, checks, verified = (_json(run_folder / n) for n in ("run.json", "checks.json", "verify.json"))
        if run.get("status") != "ok" or not checks or total_violations(checks):
            problems.append("run.json or checks.json is not ok")
        if not verified or verified.get("mismatch_count") or not verified.get("breached_windows", {}).get("same"):
            problems.append("verify.json is not clean")
        if missing := [t for t in TABLES if not (run_folder / t / "_SUCCESS").is_file()]:
            problems.append(f"no _SUCCESS in {missing}")
        if reference is None:
            problems.append("no reference run to compare with")
        else:
            for table, key in ccm.TABLE_KEYS.items():
                diff, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(run_folder, table),
                                                 key, ccm.cpm.BREACH_FIELDS.get(table, []))
                problems += [f"{table}: {p}" for p in diff]
        found.append({"job_id": a["job_id"], "attempt": a["attempt_number"], "problems": problems})
    return found


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _caching_collector():
    sys.path.insert(0, str(REPO / "analysis"))
    spec = importlib.util.spec_from_file_location("collect_caching_measurements",
                                                  REPO / "analysis" / "collect_caching_measurements.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def input_check(b: BatchFolder, processed_root: Path) -> dict:
    """6.1: the snapshot's input checksums now equal those every job recorded at submit."""
    from etf_risk.jobs.params import input_checksums
    settings = b.plan["settings"]
    try:
        now = input_checksums(processed_root, settings["snapshot"])
    except Exception as error:
        return {"passed": False, "why": f"{type(error).__name__}: {error}"}
    differ = [j["job_id"] for j in b.jobs if j.get("input_checksums") != now]
    return {"passed": not differ, "jobs_differing": differ}


# The host (docs/recovery-part-a.md, section 12)

def host_readings(b: BatchFolder) -> dict:
    """The reading before each job, by position: host_state events, or the host_memory events of
    batches recorded before 2026-10-24's power and swap recording, which hold memory only."""
    readings = {e["position"]: e for e in named(b.harness, "host_memory")}
    readings.update({e["position"]: e for e in named(b.harness, "host_state", stage="job")})
    return readings


def counters(reading: dict | None) -> dict:
    """A reading's cumulative page and swap counters in bytes (COUNTER_KEYS). Readings since
    2026-10-27 hold vm_stat's four by their own names. Older ones held psutil's sin and sout as
    swap_in_bytes and swap_out_bytes, which on macOS are page-ins and page-outs
    (docs/host-counters-correction.md): they are read as such, and those readings' swap traffic as
    not recorded, never inferred from them."""
    reading = reading or {}
    if any(key in reading for key in COUNTER_KEYS):
        return {key: reading.get(key) for key in COUNTER_KEYS}
    return {"pageins_bytes": reading.get("swap_in_bytes"), "pageouts_bytes": reading.get("swap_out_bytes"),
            "swapins_bytes": None, "swapouts_bytes": None}


def host_row(host: dict, position: int, end: dict | None) -> dict:
    """A job's host columns. The *_during_bytes columns are what the host paged out, swapped in and
    swapped out from this reading to the next one (the next job's, or the batch's end reading), so
    they cover the job; None without both readings' counter (swap traffic in batches recorded
    before 2026-10-27, which did not record it)."""
    reading = host[position]
    later = sorted(p for p in host if p > position)
    after = host[later[0]] if later else end
    a, z = counters(reading), counters(after) if after is not None else None

    def during(key: str) -> int | None:
        return None if z is None or a[key] is None or z[key] is None else z[key] - a[key]
    return {"host_available_bytes": reading.get("available_bytes"), "memory_pressure": reading.get("memory_pressure"),
            "power_source": reading.get("power_source"), "lid_closed": reading.get("lid_closed"),
            "other_containers": reading.get("other_containers"), "pageouts_during_bytes": during("pageouts_bytes"),
            "swapins_during_bytes": during("swapins_bytes"), "swapouts_during_bytes": during("swapouts_bytes")}


def host_conditions(b: BatchFolder, host: dict, ran: list[int]) -> dict:
    """Conditions 1 and 2 of the protocol (docs/recovery-part-a.md, section 12), and condition 4's
    containers, over the readings a batch needs: its start, before each job that ran, and its end.
    A reading on battery, with the lid closed, or with a running container outside this project
    fails its condition. A missing reading, or one without the value (as the readings of batches
    recorded before each value was are), is unknown, and unknown fails too: no condition ever
    passes by default."""
    start = (named(b.harness, "host_state", stage="start") or [None])[0]
    end = (named(b.harness, "host_state", stage="end") or [None])[-1]
    readings = [("start", start), *[(position, host.get(position)) for position in ran], ("end", end)]

    def condition(key, fails) -> dict:
        failed = [where for where, r in readings if r is not None and r.get(key) is not None and fails(r[key])]
        unknown = [where for where, r in readings if r is None or r.get(key) is None]
        return {"passed": not failed and not unknown, "failed": failed, "unknown": unknown}

    return {"host_power": condition("power_source", lambda value: value != "AC Power"),
            "host_lid": condition("lid_closed", lambda value: value is not False),
            "other_containers": condition("other_containers", lambda value: value != 0)}


def container_events_check(b: BatchFolder) -> dict:
    """Condition 4 over the whole batch, not only at the readings: no event of another project's
    container from the batch's start to its end (containers.jsonl, from the harness's docker-events
    monitor), so that a container that starts or stops between two readings fails it too. Any
    such event fails the recovery-times verdict for the whole batch. A batch without the monitor's
    record (every batch before 2026-10-27), or whose monitor failed, is unknown, and unknown fails
    too: the condition never passes by default."""
    record = (named(b.harness, "container_monitor") or [None])[-1]
    path = b.folder / "containers.jsonl"
    if record is None:
        return {"passed": False, "failed": [], "unknown": ["no container_monitor record (monitor absent)"]}
    if record.get("error"):
        return {"passed": False, "failed": [], "unknown": [f"the monitor failed: {record['error']}"]}
    if not path.exists():
        return {"passed": False, "failed": [], "unknown": ["containers.jsonl is missing"]}
    events = jsonl(path)
    foreign = [e for e in events if not e.get("ours")]
    start = (named(b.harness, "batch_started") or [{}])[0].get("mono")
    return {"passed": not foreign, "unknown": [],
            "failed": [f"{len(foreign)} event(s) of other projects' containers during the batch"] if foreign else [],
            "other_project_events": len(foreign), "own_events": len(events) - len(foreign),
            "first_other_s_after_start": (min(e["mono"] for e in foreign) - start
                                          if foreign and start is not None else None)}


def sleep_wake_evidence(b: BatchFolder) -> dict:
    """The power log's sleep and wake entries during the batch (the harness's power_log event):
    evidence beside the clock and lid checks, never a gate. Missing evidence is stated as missing,
    and a log that does not reach back to the batch's start is no evidence for its first part."""
    record = (named(b.harness, "power_log") or [None])[-1]
    if record is None:
        return {"recorded": False, "why": "no power_log record (batches before 2026-10-27 did not record it)"}
    if not record.get("available"):
        return {"recorded": False, "why": record.get("why") or "not available"}
    entries = record.get("entries") or []
    kinds = {kind: sum(1 for e in entries if e.get("kind") == kind) for kind in ("Sleep", "Wake", "DarkWake")}
    return {"recorded": True, "covers_batch": bool(record.get("covers_batch")), "log_starts": record.get("log_starts"),
            "entries": kinds, "sleep_times": [e.get("ts") for e in entries if e.get("kind") == "Sleep"]}


def describe_sleep_wake(evidence: dict) -> str:
    if not evidence["recorded"]:
        return f"sleep/wake evidence: NOT RECORDED ({evidence['why']})"
    counts = ", ".join(f"{k} {v}" for k, v in evidence["entries"].items())
    coverage = "the log covers the whole batch" if evidence["covers_batch"] else (
        f"the log starts at {evidence['log_starts']}, after the batch began: no evidence for its first part")
    return f"sleep/wake evidence: {counts}; {coverage}"


def check_state(validity: dict, name: str) -> str:
    """passed, failed or unknown; only an explicit pass passes. A check that is missing or has no
    result is unknown, and so is a host condition whose only problem is the readings it lacks."""
    check = validity.get(name) or {}
    if check.get("passed") is True:
        return "passed"
    if check.get("passed") is False and (check.get("failed") or not check.get("unknown")):
        return "failed"
    return "unknown"


def verdict(validity: dict, checks: tuple[str, ...]) -> dict:
    """Valid only if every one of checks passed; the ones that did not, failed or unknown."""
    failed = [name for name in checks if check_state(validity, name) != "passed"]
    return {"valid": not failed, "failed": failed}


def q1_summary(rows: list[dict], outcomes: dict) -> str:
    """The summary's Q1 line. A submitted job without a Q1 row has an unknown verdict, never an ok
    one, so a batch whose cross-check did not run says so instead of "none"."""
    submitted = [r for r in rows if r.get("job_id") is not None]
    if not submitted:
        return "no job was submitted, so there is no Q1 verdict"
    if len(outcomes["q1_missing"]) == len(submitted):
        return "no Q1 rows: every submitted job's Q1 verdict is unknown (the cross-check did not run)"
    text = f"jobs whose Q1 verdict is not ok: {outcomes['q1_not_ok'] or 'none'}"
    return text + (f"; jobs without a Q1 verdict: {outcomes['q1_missing']}" if outcomes["q1_missing"] else "")


def listed(validity: dict, names: list[str]) -> str:
    """The checks named, each unknown one marked as such."""
    return ", ".join(name if check_state(validity, name) == "failed" else f"{name} (unknown)" for name in names)


def host_summary(b: BatchFolder, host: dict) -> dict:
    """The batch's host record: where it ran on battery, with the lid closed or with another
    project's container, the highest memory pressure, the lowest available memory, the change in
    swap in use, and the page and swap traffic from its start to its end (counters(): swap traffic
    is None for batches that did not record it)."""
    start = (named(b.harness, "host_state", stage="start") or [{}])[0]
    end = (named(b.harness, "host_state", stage="end") or [{}])[-1]
    jobs = list(host.values())
    a, z = counters(start), counters(end)

    def change(key):
        return end[key] - start[key] if start.get(key) is not None and end.get(key) is not None else None

    def traffic(key):
        return z[key] - a[key] if a[key] is not None and z[key] is not None else None

    return {"jobs_with_a_reading": len(jobs),
            "power_sources": sorted({e["power_source"] for e in [start, *jobs, end] if e.get("power_source")}),
            "on_battery": [p for p, e in sorted(host.items()) if e.get("power_source") == "Battery Power"],
            "lid_closed": [p for p, e in sorted(host.items()) if e.get("lid_closed")],
            "other_containers_at": [p for p, e in sorted(host.items()) if e.get("other_containers")],
            "max_memory_pressure": max((e["memory_pressure"] for e in [start, *jobs, end]
                                        if e.get("memory_pressure") is not None), default=None),
            "min_available_bytes": min((e["available_bytes"] for e in jobs if e.get("available_bytes") is not None),
                                       default=None),
            "swap_used_change_bytes": change("swap_used_bytes"),
            "counters": "vm_stat" if any(key in start for key in COUNTER_KEYS) else "psutil sin/sout (page counts only)",
            "pageins_batch_bytes": traffic("pageins_bytes"), "pageouts_batch_bytes": traffic("pageouts_bytes"),
            "swapins_batch_bytes": traffic("swapins_bytes"), "swapouts_batch_bytes": traffic("swapouts_bytes")}


# The batch

def collect(folder: Path, clock_tolerance_s: float = 1.0, processed_root: Path = REPO / "data" / "processed") -> dict:
    b = BatchFolder(folder)
    deadlines = {e["position"]: e for e in named(b.harness, "deadline")}
    injections = {e["position"]: e for e in named(b.harness, "injection")}
    not_run = {e["position"]: e for e in named(b.harness, "not_run")}
    not_submitted = {e["position"]: e for e in named(b.harness, "job_not_submitted")}
    host = host_readings(b)
    host_end = (named(b.harness, "host_state", stage="end") or [None])[-1]
    q1, q2, q3a = by_job(b.q["Q1"]), by_job(b.q["Q2"]), by_job(b.q["Q3a"])
    c0 = []
    for position, e in deadlines.items():
        accepted = min(named([x for x in b.worker_events() if x.get("job_id") == e["job_id"]], "accepted"),
                       key=lambda x: x["mono"], default=None)
        if e["case"] == "C0" and accepted is not None:
            c0.append(accepted["mono"] - e["t_submit"])
    c0_median = statistics.median(c0) if c0 else None
    rows = []
    for position, case in enumerate(b.plan["jobs"], start=1):
        row = {"position": position, "case": case}
        if position in host:
            row.update(host_row(host, position, host_end))
        if position in not_run or position in not_submitted:
            row["status"] = "not run" if position in not_run else "not submitted"
            rows.append(row)
            continue
        if position not in deadlines:
            row["status"] = "no record"
            rows.append(row)
            continue
        d, inj = deadlines[position], injections.get(position)
        status = "no injection record" if inj is None else "missed" if inj.get("missed") else "made"
        inj = inj or {}
        job_id = d["job_id"]
        row.update(job_id=job_id, status=status, missed=inj.get("missed"),
                   injection=inj.get("kind"), worker=inj.get("worker"), t_inj=inj.get("t_inj"),
                   reference=d["reference"], deadline_s=d["deadline_s"])
        row.update(job_metrics(b, position, case, inj, d, c0_median))
        row.update(claims=(q1.get(job_id) or {}).get("n_claims"), accepted=(q1.get(job_id) or {}).get("n_accepted"),
                   q1_verdict=(q1.get(job_id) or {}).get("verdict"), timeliness=(q2.get(job_id) or {}).get("timeliness"),
                   deadline_met=(q2.get(job_id) or {}).get("deadline_met"),
                   q3a_verdict=(q3a.get(job_id) or {}).get("log_verdict"))
        rows.append(row)
    intervals, missing = step_intervals(b)
    final = (named(b.harness, "final_snapshot") or [{}])[-1]
    quiescent = (named(b.harness, "quiescent") or [{}])[-1]
    validity = {
        "injections": {"planned": len(rows), "made": sum(r.get("status") == "made" for r in rows),
                       "missed": [r["position"] for r in rows if r.get("status") == "missed"],
                       "not_run": [r["position"] for r in rows if r.get("status") in NOT_RUN],
                       "unrecorded": [r["position"] for r in rows if r.get("status") in UNRECORDED]},
        "code_identity": identity_check(b),
        "clock": clock_check(b, clock_tolerance_s),
        "fingerprints_agree": {"passed": bool(final.get("fingerprints_agree")), "values": final.get("fingerprints")},
        "inputs_unchanged": input_check(b, processed_root),
        **host_conditions(b, host, [r["position"] for r in rows if r.get("job_id") is not None]),
        "container_events": container_events_check(b),
        "records_complete": {"passed": not named(b.harness, "setup_error") and not named(b.harness, "final_error"),
                             "setup_errors": [e.get("error") for e in named(b.harness, "setup_error")],
                             "final_errors": [e.get("error") for e in named(b.harness, "final_error")]},
    }
    verdicts = {"correctness": verdict(validity, CORRECTNESS_CHECKS), "timing": verdict(validity, TIMING_CHECKS)}
    validity_failed = verdicts["timing"]["failed"]          # every required check that failed or is unknown
    outcomes = {
        "q1_not_ok": [r["job_id"] for r in rows if r.get("q1_verdict") not in (None, "ok")],
        "q1_missing": [r["job_id"] for r in rows if r.get("job_id") is not None and r.get("q1_verdict") is None],
        "status_check_exit": final.get("status_check_exit"),
        "invariant_violations": _json(folder / "export" / "invariant_violations.json") if
        (folder / "export" / "invariant_violations.json").exists() else "no export",
        "accepted_attempts": accepted_checks(b),
        "overlap": overlap_verdict(intervals, missing),
        "nothing_left": {"processes_left": quiescent.get("processes_left"),
                         "other_connections": quiescent.get("other_connections"),
                         "spark_scratch_new": quiescent.get("spark_scratch_new")},
        "cleanup_listing": "cleanup.txt" if (folder / "cleanup.txt").exists() else "not recorded",
        "host_state": host_summary(b, host),
        "sleep_wake": sleep_wake_evidence(b),
        "q2b_rows": b.q["Q2b"],
        "q3b_not_matching": [r for r in b.q["Q3b"] if r.get("report_verdict") != "matches"],
        "liveness": {name: len(named(b.worker_events() + b.reconciler, name)) for name in LIVENESS},
        "batch_peaks": final.get("batch_peaks"),
    }
    return {"purpose": b.plan.get("purpose", "not recorded"), "rows": rows, "tally": tally(rows, b),
            "validity": validity, "validity_failed": validity_failed, "verdicts": verdicts, "outcomes": outcomes,
            "c0_median_s": c0_median}


def tally(rows: list[dict], b: BatchFolder) -> list[dict]:
    """Per case: planned, made, missed, not run, unrecorded, and every verdict value, with zeros."""
    q3b_case = {}
    cases_by_job = {r["job_id"]: r["case"] for r in rows if r.get("job_id") is not None}
    for r in b.q["Q3b"]:
        case = cases_by_job.get(int(r["job_id"])) if r.get("job_id") else None
        q3b_case.setdefault(case, []).append(r.get("report_verdict"))
    out = []
    for case in CASES:
        mine = [r for r in rows if r["case"] == case]
        entry = {"case": case, "planned": len(mine), "made": sum(r.get("status") == "made" for r in mine),
                 "missed": sum(r.get("status") == "missed" for r in mine),
                 "not_run": sum(r.get("status") in NOT_RUN for r in mine),
                 "unrecorded": sum(r.get("status") in UNRECORDED for r in mine),
                 "claims": sum(int(r["claims"]) for r in mine if r.get("claims") is not None)}
        for prefix, values, column in (("q1", Q1_VERDICTS, "q1_verdict"), ("q2", Q2_CLASSES, "timeliness"),
                                       ("met", DEADLINE_MET, "deadline_met"), ("q3a", Q3A_VERDICTS, "q3a_verdict")):
            for value in values:
                entry[f"{prefix}: {value}"] = sum(r.get(column) == value for r in mine)
        for value in Q3B_VERDICTS:
            entry[f"q3b: {value}"] = q3b_case.get(case, []).count(value)
        out.append(entry)
    return out


def write(folder: Path, result: dict) -> None:
    with open(folder / "injections.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["rows"])
    with open(folder / "tally.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(result["tally"][0]))
        writer.writeheader()
        writer.writerows(result["tally"])
    (folder / "validity.json").write_text(json.dumps(
        {k: result[k] for k in ("purpose", "validity", "validity_failed", "verdicts", "outcomes", "c0_median_s")},
        indent=2,
        default=str) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument("--clock-tolerance", type=float, default=1.0,
                        help="seconds (1 s as Part A approved, docs/recovery-part-a.md, section 10)")
    parser.add_argument("--processed-root", type=Path, default=REPO / "data" / "processed",
                        help="where the snapshot's input files are checked again (default data/processed)")
    args = parser.parse_args(argv)
    result = collect(args.batch, args.clock_tolerance, args.processed_root)
    write(args.batch, result)
    print(f"purpose: {result['purpose']}" + (" (a preflight: not a formal result)" if result["purpose"] == "preflight"
                                             else ""))
    v = result["validity"]["injections"]
    print(f"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run,"
          f" {len(v['unrecorded'])} without a complete harness record")
    print("validity: " + ("all checks passed" if not result["validity_failed"]
                          else "FAILED: " + listed(result["validity"], result["validity_failed"])))
    for claim, label in (("correctness", "correctness observations"), ("timing", "recovery times")):
        check = result["verdicts"][claim]
        print(f"{label}: " + ("valid" if check["valid"] else "INVALID: " + listed(result["validity"], check["failed"])))
    print(f"overlap: {result['outcomes']['overlap']['verdict']}; {q1_summary(result['rows'], result['outcomes'])}")
    events = result["validity"]["container_events"]
    print("container events during the batch: " + (
        f"{events['other_project_events']} of other projects, {events['own_events']} of this project's"
        if "other_project_events" in events else f"UNKNOWN ({'; '.join(events['unknown'])})"))
    print(describe_sleep_wake(result["outcomes"]["sleep_wake"]))
    return 0 if all(check["valid"] for check in result["verdicts"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
