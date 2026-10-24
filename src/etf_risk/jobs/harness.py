"""The session harness of the recovery experiments E1 and E2 (docs/recovery-experiments.md).

    uv run --group jobs python -m etf_risk.jobs.harness plan --purpose preflight|formal --seed N --out PLAN.json
        [--settings FILE] [--jobs C0,W1,...]
    uv run --group jobs python -m etf_risk.jobs.harness estimate --plan PLAN.json
    uv run --group jobs python -m etf_risk.jobs.harness batch --plan PLAN.json --out .../<purpose>/<batch> [--formal]

plan fixes a batch before it runs (8.1): its purpose, its jobs in an order shuffled from the
seed (or, with --jobs, in the order listed), the case of each, the settings and the code
identity. Settings holds every value that section 8 of the outline leaves provisional (timing,
repetitions, deadlines, the harness's waits, the memory thresholds); a settings file (JSON)
replaces any of them, and the plan records the values used.

A plan's purpose keeps a preflight apart from formal results (8.6): batch writes only into a
folder named after the purpose (data/outputs-recovery/preflight/<batch> or .../formal/<batch>),
every record of the batch names it, and a formal batch also needs --formal, which is given only
once the author has approved Part A.

estimate prints a plan's expected duration, from the design's windows (3.2) and the
assumptions it names (Assumptions); none of them is measured.

batch runs one plan on fresh containers (2.1-2.5):
- the services, the job database and a topic of its own; the reference run under the host lock,
  through the launcher (2.2); the reconciler; worker A, then worker B, each waited for in the
  assignment events (2.4);
- for each job: the fault armed or the injection made (3.1), the deadline recorded (4.2) and
  observed when the job finishes or at the deadline, whichever comes first (4.3), the job
  followed to its end or its drain limit (2.5), killed or stopped workers restarted (2.4), and
  the memory peaks read, with the thresholds of P4 (4.6);
- then quiescence (4.4), the final snapshot with crosscheck.sql (4.5), and the services
  removed.
Its records go to DIR (section 9): harness.jsonl (the harness's own events), events/ (every
process's log), jobs/ (the attempts' folders), reference/, logs/, crosscheck/*.csv, export/,
status-check.txt, and plan.json.

No batch has run against the services: Part A is not approved, and no formal experiment has been
run. The offline parts are tested with tests/test_jobs_harness.py, and a synthetic batch, with
SQLite and in-process stand-ins for the services, runs end to end in
tests/test_recovery_synthetic.py.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from contextlib import closing
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from etf_risk.jobs import faults, processes
from etf_risk.jobs.events import EventLog, read_events
from etf_risk.jobs.reconciler import PUBLICATION_GRACE, RECONCILE_INTERVAL
from etf_risk.jobs.timing import Timing
from etf_risk.provenance import REPO_ROOT, code_identity

CASES = ("C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "W6", "W7", "K1", "K2", "D1", "D2", "X1")
PURPOSES = ("preflight", "formal")
HOOKS = {"W1": ("before_claim", "kill"), "W2": ("after_claim", "kill"), "W4": ("after_pipeline", "kill"),
         "W5a": ("after_accept_commit", "kill"), "W5b": ("after_accept", "kill"), "D2": ("after_pipeline", "hold")}
MID_STEP = ("W3", "W6", "W7", "K1", "D1")       # injected once the attempt's spark_pipeline step runs
NO_NEW_ATTEMPT = ("C0", "W5a", "W5b", "K1", "X1")
FROM_RESTORED = ("K2", "D1", "D2")              # deadline counted from the service's return (4.2)
WORKERS = ("A", "B")
PARTITION = 0
TERMINAL = ("succeeded", "failed")
CROSSCHECK_SQL = Path(__file__).with_name("crosscheck.sql")
QUERIES = ("Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b")
_SEPARATOR = re.compile(r"^-- -{20,}\s*$")
_QUERY_NAME = re.compile(r"^-- (Q\w+)\.")


# Settings and plans

@dataclass(frozen=True)
class Settings:
    """The provisional values of the outline's section 8 (P1-P4) and the harness's waits (8.5)."""
    snapshot: str = "full-2026-10-12"
    kind: str = "calendar-year"          # P1: every case on the calendar-year job
    stride: int = 21
    max_attempts: int = 3
    jobs_per_case: int = 2               # P1, the preferred draft: 2 per case, one batch (28 jobs)
    cases: tuple[str, ...] = CASES
    timing: tuple[str, ...] = ()         # --timing overrides; P2: none
    slowest_steps_s: float = 35.1        # S (P3): M2's slowest windows + spark_pipeline + verify, calendar-year
    deadline_margin: float = 2.0         # P3: D = B + margin * S, rounded up
    deadline_round_s: float = 5.0
    max_lag_s: float = 1.0               # P3
    phase_delay_s: float = 3.0           # 8.5: after spark_pipeline starts, before a mid-step injection
    w7_stop_s: float = 90.0              # 8.5: how long W7's tree stays stopped (longer than a takeover)
    outage_s: float = 30.0               # 8.5: how long K2, D1 and D2 keep their service stopped
    flag_fraction: float = 0.90          # P4
    stop_fraction: float = 0.95          # P4
    poll_s: float = 0.5
    phase_timeout_s: float = 300.0       # the longest wait for an injection's phase; then it is missed

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        unknown = sorted(set(data) - {f.name for f in fields(cls)})
        if unknown:
            raise ValueError(f"unknown settings: {unknown}")
        settings = cls(**{k: tuple(v) if k in ("cases", "timing") else v for k, v in data.items()})
        if bad := sorted(set(settings.cases) - set(CASES)):
            raise ValueError(f"unknown cases: {bad}")
        return settings


def timing_of(settings: Settings) -> Timing:
    from etf_risk.jobs.cli import timing_from
    return timing_from(list(settings.timing))


def plan_jobs(settings: Settings, seed: int) -> list[str]:
    """The batch's cases in run order: jobs_per_case of each case, shuffled with the seed."""
    jobs = [case for case in settings.cases for _ in range(settings.jobs_per_case)]
    random.Random(seed).shuffle(jobs)
    return jobs


def deadline_reference(case: str) -> str:
    """What a job's deadline counts from (4.2): its submit, its injection, or its service's return."""
    return "submit" if case == "C0" else "restored" if case in FROM_RESTORED else "injection"


def bound_to_next_run(case: str, timing: Timing, settings: Settings) -> float:
    """B (P3): the latest the design starts the job's next run, from the deadline's reference.
    K2, D1 and D2 count from their service's return, since how long a restart takes is not
    known and is not inferred."""
    lease, period = timing.lease, RECONCILE_INTERVAL.total_seconds()
    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0     # a member gone, then a poll
    if case in NO_NEW_ATTEMPT:
        return 0.0
    if case == "W1":
        return rejoin
    if case in ("W2", "W3", "W4", "W6"):
        return lease + period
    if case == "W7":                     # the later of the takeover and the end of the stopped tree
        return max(lease + period, settings.w7_stop_s + 2 * timing.watchdog_tick + timing.kill_grace)
    if case == "K2":                     # the grace before a publication, a pass, and the group again
        return PUBLICATION_GRACE.total_seconds() + period + rejoin
    if case in ("D1", "D2"):             # a fenced attempt's lease, then a pass
        return lease + period
    raise ValueError(f"unknown case {case!r}")


def deadline_seconds(case: str, timing: Timing, settings: Settings) -> float:
    """D (P3): B plus deadline_margin times S, rounded up to deadline_round_s."""
    raw = bound_to_next_run(case, timing, settings) + settings.deadline_margin * settings.slowest_steps_s
    step = settings.deadline_round_s
    return math.ceil(raw / step - 1e-9) * step


def make_plan(settings: Settings, seed: int, *, purpose: str = "formal", jobs: list[str] | None = None) -> dict:
    """A plan (8.1). jobs, if given, is the run order as listed, as a preflight's is (8.6);
    otherwise plan_jobs shuffles every case of settings.cases with the seed."""
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}, not {purpose!r}")
    if jobs is not None and (bad := sorted(set(jobs) - set(CASES))):
        raise ValueError(f"unknown cases: {bad}")
    timing = timing_of(settings)
    cases = settings.cases if jobs is None else tuple(c for c in CASES if c in jobs)
    return {"format": 1, "purpose": purpose, "seed": seed, "order": "shuffled" if jobs is None else "as listed",
            "created_at_utc": datetime.now(timezone.utc).isoformat(), "settings": asdict(settings),
            "timing": asdict(timing), "code": code_identity(),
            "deadlines_s": {case: deadline_seconds(case, timing, settings) for case in cases},
            "jobs": plan_jobs(settings, seed) if jobs is None else list(jobs)}


# The duration estimate

@dataclass(frozen=True)
class Assumptions:
    """What estimate() assumes. None of it is measured: T for the job system, the restore time
    and the restart overhead are guesses to be replaced by the first batch's records."""
    time_to_finish_s: float = 40.0       # T: M2's slowest steps (35.1 s) plus 5 s of the worker's own work
    restart_s: float = 12.0              # a killed worker's start, sweep and rebalance
    restore_s: float = 20.0              # a service's start until it is ready again
    peaks_s: float = 2.0                 # the peaks read after every job
    group_settle_s: float = 18.0         # after a Kafka restart, until the group has an owner (S + h)
    batch_fixed_s: float = 180.0         # containers, reference run, workers, final snapshot, teardown


def case_seconds(case: str, timing: Timing, settings: Settings, a: Assumptions) -> float:
    """One job's expected duration from the harness's view: from its start to the next job's."""
    t, lease, period = a.time_to_finish_s, timing.lease, RECONCILE_INTERVAL.total_seconds()
    partial = 1.0 + 3.0 + settings.phase_delay_s         # delivery, windows (M2: up to 3.0 s), the delay
    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0
    down = settings.outage_s + a.restore_s
    to_fence = lease - timing.fence_margin - timing.renew_interval   # the earliest F after an injection
    if case == "C0":
        return t + a.peaks_s
    if case in ("W1", "W2"):
        return 1.0 + bound_to_next_run(case, timing, settings) + t + a.restart_s + a.peaks_s
    if case in ("W3", "W6", "W7"):
        return partial + bound_to_next_run(case, timing, settings) + t + a.restart_s + a.peaks_s
    if case == "W4":
        return t + lease + period + t + a.restart_s + a.peaks_s
    if case in ("W5a", "W5b"):
        return t + a.restart_s + a.peaks_s
    if case == "K1":
        return t + a.group_settle_s + 2 * a.peaks_s
    if case == "K2":
        wait = max(0.0, PUBLICATION_GRACE.total_seconds() - down)
        return a.peaks_s + down + wait + period + rejoin + t + a.peaks_s
    if case == "D1":                     # fenced when MySQL is away past F; then the lease, a pass, a run
        if down >= to_fence:
            return partial + a.peaks_s + max(down, lease) + period + t + a.peaks_s
        return max(t, partial + down) + 2 * a.peaks_s
    if case == "D2":                     # held after the run; acceptance tried until F
        if down >= lease - timing.fence_margin:
            return t + a.peaks_s + lease + period + t + a.peaks_s
        return t + a.peaks_s + down + a.peaks_s
    if case == "X1":
        return t + 2.0 + a.peaks_s
    raise ValueError(f"unknown case {case!r}")


def estimate(plan: dict, a: Assumptions = Assumptions()) -> dict:
    settings = Settings.from_dict(plan["settings"])
    timing = timing_of(settings)
    per_case = {case: case_seconds(case, timing, settings, a) for case in settings.cases}
    total = sum(per_case[case] for case in plan["jobs"]) + a.batch_fixed_s
    return {"assumptions": asdict(a), "per_case_s": per_case, "jobs": len(plan["jobs"]), "batch_s": total}


# Reading the records

def events_named(events: list[dict], event: str, /, **fields_) -> list[dict]:
    """The events called `event` whose fields equal fields_ (any field, "name" included)."""
    return [e for e in events if e.get("event") == event and all(e.get(k) == v for k, v in fields_.items())]


def owner(logs: dict[str, list[dict]], alive: set[str], partition: int = PARTITION) -> str | None:
    """The live worker that holds the partition by its assignment events: its latest assigned
    event lists the partition and no later revoked or lost event, or restart, took it away.
    None when no live worker, or more than one, holds it."""
    holders = []
    for worker, events in logs.items():
        holds = False
        for e in events:
            kind = e.get("event")
            if kind == "started":
                holds = False
            elif kind == "assigned":
                holds = any(p[1] == partition for p in e.get("partitions", []))
            elif kind in ("revoked", "lost") and any(p[1] == partition for p in e.get("partitions", [])):
                holds = False
        if holds and worker in alive:
            holders.append(worker)
    return holders[0] if len(holders) == 1 else None


def worker_accepts(logs: dict[str, list[dict]]) -> list[tuple]:
    """worker_accepts rows (crosscheck.sql): one per accepted event, with the log's identity."""
    return [(e.get("store_id"), e.get("worker_id"), e.get("pid"), e["job_id"], e["attempt"], e["digest"])
            for events in logs.values() for e in events_named(events, "accepted")]


class PeakBook:
    """Memory peaks by segment (4.6): a restart or a stop resets a container's memory.peak, so a
    reading before it closes a segment. A container's batch peak is the maximum of its readings;
    a reading that failed leaves its segment unknown and the batch peak incomplete."""

    def __init__(self):
        self.readings: dict[str, list[dict]] = {}

    def add(self, service: str, peak_bytes: int | None, limit_bytes: int | None, closes: str | None) -> dict:
        reading = {"peak_bytes": peak_bytes, "limit_bytes": limit_bytes, "closes": closes}
        self.readings.setdefault(service, []).append(reading)
        return reading

    def batch_peak(self, service: str) -> dict:
        readings = self.readings.get(service, [])
        known = [r["peak_bytes"] for r in readings if r["peak_bytes"] is not None]
        limit = next((r["limit_bytes"] for r in readings if r["limit_bytes"]), None)
        peak = max(known) if known else None
        return {"peak_bytes": peak, "limit_bytes": limit, "readings": len(readings),
                "incomplete": not readings or len(known) < len(readings),
                "fraction": None if peak is None or not limit else peak / limit}


def memory_verdict(fraction: float | None, settings: Settings) -> str:
    """P4: ok, flag (past flag_fraction) or stop (past stop_fraction); unknown without a reading."""
    if fraction is None:
        return "unknown"
    return "stop" if fraction > settings.stop_fraction else "flag" if fraction > settings.flag_fraction else "ok"


def crosscheck_statements(text: str | None = None) -> list[tuple[str, str]]:
    """The statements of crosscheck.sql below its separator, in order, each named DDL or Q0-Q3b."""
    lines = (CROSSCHECK_SQL.read_text() if text is None else text).splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if _SEPARATOR.match(line)) + 1
    statements, current = [], []
    for line in lines[start:]:
        current.append(line)
        stripped = line.strip()
        if stripped.endswith(";") and not stripped.startswith("--"):
            sql = "".join(current).strip()
            name = next((m.group(1) for row in sql.splitlines() if (m := _QUERY_NAME.match(row))), "DDL")
            statements.append((name, sql))
            current = []
    return statements


def fingerprint_from_export(folder: Path) -> dict:
    """Q0's four numbers, from an export's jobs.json and job_attempts.json."""
    jobs = json.loads((folder / "jobs.json").read_text())
    attempts = json.loads((folder / "job_attempts.json").read_text())
    return {"n_jobs": len(jobs), "sum_version": sum(int(j["version"]) for j in jobs),
            "n_attempts": len(attempts), "sum_renewals": sum(int(a["renewals"]) for a in attempts)}


def csv_value(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="microseconds")
    if isinstance(value, (date, Decimal)):
        return str(value)
    return str(value)


def clock_pair() -> dict:
    """ts and mono read together, for the clock check (4.1)."""
    return {"ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"), "mono": time.monotonic()}


# The batch

class PhaseMissed(Exception):
    """An injection did not land in its phase; the job is recorded as a miss and still followed."""


class Tracker(threading.Thread):
    """Follows one job: the deadline observation when it finishes or at its deadline, whichever
    comes first (4.3), then until it is finished or its drain limit has passed (2.5)."""

    def __init__(self, batch: Batch, job_id: int, deadline_mono: float, drain_until: float):
        super().__init__(daemon=True)
        self.batch, self.job_id, self.deadline_mono, self.drain_until = batch, job_id, deadline_mono, drain_until
        self.observation: dict | None = None
        self.final: str | None = None
        self.finished_mono: float | None = None

    def run(self) -> None:
        while True:
            now, status = time.monotonic(), self.batch.job_status(self.job_id)
            if self.observation is None and (status in TERMINAL or now >= self.deadline_mono):
                self.observation = self.batch.observe(self.job_id)
            if status in TERMINAL:
                self.final, self.finished_mono = status, now
                return
            if now >= self.drain_until:
                return
            time.sleep(self.batch.settings.poll_s)


class Batch:
    def __init__(self, plan: dict, out: Path):
        from etf_risk import services
        self.plan, self.out, self.services = plan, out, services
        self.purpose = plan.get("purpose")
        self.settings = Settings.from_dict(plan["settings"])
        self.timing = timing_of(self.settings)
        self.mysql_url = os.environ.get("ETF_RISK_MYSQL_URL", services.DEFAULT_MYSQL_URL).rstrip("/")
        self.bootstrap = os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", services.DEFAULT_KAFKA_BOOTSTRAP)
        self.db = f"{self.mysql_url}/etf_recovery"
        self.topic = f"etf-recovery-{secrets.token_hex(4)}"
        self.events_dir, self.jobs_root, self.faults_dir, self.logs_dir = (
            out / "events", out / "jobs", out / "faults", out / "logs")
        for folder in (self.events_dir, self.jobs_root, self.faults_dir, self.logs_dir):
            folder.mkdir(parents=True, exist_ok=True)
        self.env = {**os.environ, "ETF_RISK_JOBS_DB": self.db, "ETF_RISK_KAFKA_BOOTSTRAP": self.bootstrap,
                    "ETF_RISK_JOBS_TOPIC": self.topic}
        self.env.pop(faults.FAULT_FILE_ENV, None)
        self.log = EventLog(out / "harness.jsonl", "harness", batch=out.name)
        self.procs: dict[str, subprocess.Popen] = {}
        self.peaks = PeakBook()
        self.batch_jobs: list[tuple] = []
        self.observations: list[tuple] = []
        self.stop_reason: str | None = None
        self.store_id: str | None = None
        self._local = threading.local()                 # a JobStore per thread: a connection is not shared
        self._publisher = None

    # Commands and services

    def common_args(self) -> list[str]:
        args = ["--output-root", str(self.jobs_root), "--processed-root", str(REPO_ROOT / "data" / "processed"),
                "--events", str(self.events_dir)]
        for override in self.settings.timing:
            args += ["--timing", override]
        return args

    def cli(self, *argv: str, check: bool = True, timeout: float = 180) -> subprocess.CompletedProcess:
        out = subprocess.run([sys.executable, "-m", "etf_risk.jobs", *argv, *self.common_args()], env=self.env,
                             capture_output=True, text=True, timeout=timeout)
        if check and out.returncode != 0:
            raise RuntimeError(f"{argv[0]}: exit {out.returncode}: {out.stderr.strip()[-500:]}")
        return out

    def compose(self, *args: str, timeout: float = 300) -> float:
        """Run docker compose on this project's file; the seconds it took."""
        start = time.monotonic()
        out = subprocess.run(["docker", "compose", "-f", str(self.services.COMPOSE_FILE), *args],
                             capture_output=True, text=True, timeout=timeout)
        if out.returncode != 0:
            raise RuntimeError(f"docker compose {' '.join(args)}: exit {out.returncode}: {out.stderr.strip()[-500:]}")
        return time.monotonic() - start

    def wait_ready(self, service: str) -> float:
        """Until the service works again (services.py); the harness's mono at that moment."""
        check = {"mysql": lambda: self.services.mysql_ready(self.mysql_url),
                 "kafka": lambda: self.services.kafka_ready(self.bootstrap)}[service]
        self.services.wait_until_ready(service, check, timeout=180)
        return time.monotonic()

    def services_up(self) -> None:
        existing = subprocess.run(["docker", "compose", "-f", str(self.services.COMPOSE_FILE), "ps", "-a", "-q"],
                                  capture_output=True, text=True, timeout=60).stdout.split()
        if existing:
            raise RuntimeError("this project's containers exist already; a batch starts on fresh ones")
        self.log.log("services_up", seconds=self.compose("up", "-d", "--wait", "mysql", "kafka"),
                     others=self.services.other_containers())
        for service in ("mysql", "kafka"):
            self.wait_ready(service)

    def read_peaks(self, closes: str | None = None) -> str:
        """Both containers' memory.peak (4.6); the worst verdict of P4."""
        verdicts = []
        for service in ("mysql", "kafka"):
            peak = self.services.memory_peak(service)
            self.peaks.add(service, peak.peak_bytes, peak.limit_bytes, closes)
            verdict = memory_verdict(self.peaks.batch_peak(service)["fraction"], self.settings)
            verdicts.append(verdict)
            self.log.log("peaks", service=service, peak_bytes=peak.peak_bytes, limit_bytes=peak.limit_bytes,
                         closes=closes, verdict=verdict)
        return "stop" if "stop" in verdicts else "flag" if "flag" in verdicts else "ok"

    # Processes

    def start(self, name: str, *argv: str, extra_env: dict | None = None) -> subprocess.Popen:
        before = time.monotonic()
        log = open(self.logs_dir / f"{name}.log", "ab")
        proc = subprocess.Popen([sys.executable, "-m", "etf_risk.jobs", *argv, *self.common_args()],
                                env={**self.env, **(extra_env or {})}, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        self.procs[name] = proc
        self._check_start(name, proc, before)
        return proc

    def _check_start(self, name: str, proc: subprocess.Popen, before: float) -> None:
        """The process's started event, and the same-clock check of 4.1."""
        path = self.events_dir / (f"{name}.jsonl" if name in WORKERS else f"reconciler-{proc.pid}.jsonl")
        started = self.wait_for(lambda: next(iter(events_named(read_events(path) if path.exists() else [],
                                                               "started", pid=proc.pid)), None),
                                60, f"{name}'s started event")
        after = time.monotonic()
        self.log.log("process_started", name=name, pid=proc.pid, before=before, after=after,
                     first_mono=started["mono"], same_clock=before <= started["mono"] <= after,
                     code=started.get("code"))

    def fault_file(self, worker: str) -> Path:
        return self.faults_dir / f"{worker}.fault"

    def start_worker(self, name: str) -> None:
        self.fault_file(name).unlink(missing_ok=True)
        self.start(name, "worker", "--worker-id", name, extra_env={faults.FAULT_FILE_ENV: str(self.fault_file(name))})

    def alive(self) -> set[str]:
        return {w for w in WORKERS if w in self.procs and self.procs[w].poll() is None}

    def worker_logs(self) -> dict[str, list[dict]]:
        return {w: read_events(p) if (p := self.events_dir / f"{w}.jsonl").exists() else [] for w in WORKERS}

    def current_owner(self) -> str | None:
        return owner(self.worker_logs(), self.alive())

    def wait_owner(self, timeout: float = 120) -> str:
        """The partition's owner, once the assignment events name exactly one live worker."""
        return self.wait_for(self.current_owner, timeout, "a single owner of the partition")

    def wait_joined(self, worker: str, timeout: float = 120) -> str:
        """After a worker starts: its first assigned event (its join, and so the rebalance it
        caused, completed), then the owner. An owner read earlier could be a stale one."""
        pid = self.procs[worker].pid
        self.wait_for(lambda: events_named(self.worker_logs()[worker], "assigned", pid=pid), timeout,
                      f"worker {worker}'s first assignment")
        return self.wait_owner(timeout)

    def wait_for(self, predicate, timeout: float, what: str):
        """predicate()'s first true value; a lost database connection counts as not yet."""
        end = time.monotonic() + timeout
        while True:
            try:
                value = predicate()
            except Exception as error:
                from etf_risk.jobs.mysql import MYSQL
                if not MYSQL.is_disconnect(error):
                    raise
                value = None
            if value:
                return value
            if time.monotonic() >= end:
                raise PhaseMissed(f"timed out waiting for {what}")
            time.sleep(self.settings.poll_s)

    # The job table, read by the harness

    SNAPSHOT = "START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY"     # 4.3 and 4.5
    PARAM = "%s"                                                            # the driver's placeholder

    def connect(self, **timeouts):
        """A DB-API connection of the harness's own to the batch's database."""
        from etf_risk.jobs import mysql
        return mysql.connect_mysql(self.db, **timeouts)

    def statement(self, sql: str) -> str:
        """A statement of crosscheck.sql as this database runs it: MySQL runs it as written."""
        return sql

    def other_connections(self) -> int:
        """4.4: client connections to the database other than this one."""
        conn = self.connect()
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute("SELECT CONNECTION_ID()")
                me = cursor.fetchone()[0]
                cursor.execute("SHOW FULL PROCESSLIST")
                return len([row for row in cursor.fetchall()
                            if row[0] != me and row[4] != "Daemon" and row[1] not in ("event_scheduler", "system user")])
        finally:
            conn.close()

    def store(self):
        """This thread's JobStore; it reconnects at its next operation after a lost connection."""
        store = getattr(self._local, "store", None)
        if store is None:
            from etf_risk.jobs import mysql
            from etf_risk.jobs.store import JobStore
            store = self._local.store = JobStore(None, mysql.MYSQL,
                                                 connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))
        return store

    def job_status(self, job_id: int) -> str | None:
        try:
            job = self.store().job(job_id)
        except Exception:
            return None
        return None if job is None else job["status"].value

    def observe(self, job_id: int) -> dict:
        """The deadline observation (4.3): one consistent snapshot of the job's row, in a
        connection of the harness's own; a failed read is kept with no status."""
        record = {"job_id": job_id, "status": None, "attempt_number": None, "accepted_attempt": None}
        observed_from = observed_to = time.monotonic()
        try:
            conn = self.connect(connect_timeout=3, read_timeout=5, write_timeout=5)
            try:
                with closing(conn.cursor()) as cursor:
                    observed_from = time.monotonic()
                    cursor.execute(self.SNAPSHOT)
                    observed_to = time.monotonic()
                    cursor.execute("SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = "
                                   + self.PARAM, (job_id,))
                    row = cursor.fetchone()
                    cursor.execute("COMMIT")
            finally:
                conn.close()
            if row is not None:
                record.update(status=row[0], attempt_number=row[1], accepted_attempt=row[2])
        except Exception as error:
            observed_to = time.monotonic()
            record["error"] = f"{type(error).__name__}: {error}"[:300]
        record.update(observed_from_mono=observed_from, observed_to_mono=observed_to)
        self.observations.append((job_id, observed_from, observed_to, record["status"], record["attempt_number"],
                                  record["accepted_attempt"]))
        self.log.log("observation", **record)
        return record

    # Phases

    def claim_of(self, job_id: int) -> dict | None:
        """The job's latest claimed event in either worker's log, with the worker's name."""
        claims = [{**e, "worker": w} for w, events in self.worker_logs().items()
                  for e in events_named(events, "claimed", job_id=job_id)]
        return max(claims, key=lambda e: e["mono"]) if claims else None

    def attempt_dir(self, run_id: str) -> Path:
        return self.jobs_root / self.store_id / run_id

    def spark_running(self, job_id: int) -> dict | None:
        """The claim whose spark_pipeline step has started (its event and its log) and not ended."""
        claim = self.claim_of(job_id)
        if claim is None:
            return None
        events = self.worker_logs()[claim["worker"]]
        mine = {"job_id": job_id, "attempt": claim["attempt"]}
        # step_started names its step in "step"; step_ended, the pipeline's step record, in "name"
        if (not events_named(events, "step_started", step="spark_pipeline", **mine)
                or events_named(events, "step_ended", name="spark_pipeline", **mine)):
            return None
        return claim if (self.attempt_dir(claim["run_id"]) / "logs" / "spark_pipeline.log").exists() else None

    def fault_event(self, worker: str, job_id: int, point: str) -> dict | None:
        """The fault_injected event at point in the worker's log, if it followed this job's delivery."""
        events = self.worker_logs()[worker]
        for i, e in enumerate(events):
            if e.get("event") == "fault_injected" and e.get("point") == point:
                earlier = [x for x in events[:i] if x.get("event") in ("delivered", "claimed")]
                if earlier and earlier[-1].get("job_id") == job_id:
                    return e
        return None

    def wait_fault(self, armed: str, job_id: int, point: str) -> dict:
        """The armed worker's fault_injected event for this job; a miss as soon as the other
        worker claims the job first (the owner changed after the arming)."""
        def found():
            if event := self.fault_event(armed, job_id, point):
                return event
            claim = self.claim_of(job_id)
            if claim is not None and claim["worker"] != armed:
                raise PhaseMissed(f"job {job_id} was claimed by worker {claim['worker']}, not the armed {armed}")
            return None
        return self.wait_for(found, self.settings.phase_timeout_s, f"the fault at {point}")

    def at_mid_step(self, job_id: int) -> dict:
        claim = self.wait_for(lambda: self.spark_running(job_id), self.settings.phase_timeout_s,
                              f"job {job_id}'s spark_pipeline step")
        time.sleep(self.settings.phase_delay_s)
        if self.spark_running(job_id) is None:
            raise PhaseMissed("spark_pipeline ended during the phase delay")
        return claim

    # Injections (3.1)

    def arm_fault(self, position: int, case: str, owner: str) -> tuple[str, Path | None]:
        """Arm the case's hook (8.4) in the owner's fault file, which that worker reads at each
        fault point. Arming writes a file and starts or stops nothing, so the partition keeps its
        owner (logged again as owner_after) and the other worker's file stays empty. Returns the
        armed worker and, for a hold, the release path."""
        point, action = HOOKS[case]
        release = self.faults_dir / f"release-{position}" if action == "hold" else None
        faults.arm(self.fault_file(owner), point, action, release=release,
                   timeout_s=self.settings.outage_s + 600 if release else None)
        self.log.log("armed", position=position, worker=owner, point=point, action=action,
                     owner_after=self.current_owner())
        return owner, release

    def submit(self) -> int | None:
        s = self.settings
        out = self.cli("submit", "--snapshot", s.snapshot, "--kind", s.kind, "--stride", str(s.stride),
                       "--max-attempts", str(s.max_attempts), check=False)
        if out.returncode != 0:
            self.log.log("submit_failed", exit=out.returncode, stderr=out.stderr.strip()[-300:])
            return None
        record = json.loads(out.stdout.strip().splitlines()[-1])
        self.log.log("submitted", **record)
        return record["job_id"]

    def publish_again(self, job_id: int) -> bool:
        if self._publisher is None:
            from etf_risk.jobs.kafka import KafkaPublisher
            self._publisher = KafkaPublisher(self.bootstrap, self.topic, timing=self.timing)
        return self._publisher.publish(job_id)

    def stop_tree(self, worker: str, run_id: str) -> list:
        import psutil
        frozen = [psutil.Process(self.procs[worker].pid)]
        for value, procs in processes.marked_processes().items():
            parsed = processes.parse_marker(value)
            if parsed is not None and parsed[0] == self.store_id and parsed[1] == run_id:
                frozen += procs
        for p in frozen:
            p.suspend()
        return frozen

    def inject(self, position: int, case: str, job_id: int, armed: str | None, release: Path | None) -> dict:
        """Make the case's injection; what happened, with t_inj and the deadline's reference."""
        s, hook = self.settings, HOOKS.get(case)
        if hook is not None and case != "D2":
            point = hook[0]
            event = self.wait_fault(armed, job_id, point)
            self.wait_for(lambda: self.procs[armed].poll() is not None, 30, f"worker {armed} to end")
            return {"kind": "hook", "worker": armed, "point": point, "t_inj": event["mono"]}
        if case == "D2":
            event = self.wait_fault(armed, job_id, "after_pipeline")
            self.read_peaks(closes="mysql stop")
            t_inj = time.monotonic()
            self.compose("stop", "mysql")
            release.touch()                                  # acceptance meets the outage
            time.sleep(max(0.0, t_inj + s.outage_s - time.monotonic()))
            self.compose("start", "mysql")
            return {"kind": "hold+service_stop", "worker": armed, "service": "mysql", "held_mono": event["mono"],
                    "t_inj": t_inj, "restored": self.wait_ready("mysql")}
        if case in MID_STEP:
            claim = self.at_mid_step(job_id)
            worker, t_inj = claim["worker"], time.monotonic()
            if case == "W3":
                self.procs[worker].kill()                    # SIGKILL
                return {"kind": "sigkill", "worker": worker, "attempt": claim["attempt"], "phase": "spark_pipeline",
                        "t_inj": t_inj}
            if case in ("W6", "W7"):
                return self.inject_stop(case, job_id, claim, t_inj)
            service = "kafka" if case == "K1" else "mysql"
            self.read_peaks(closes=f"{service} {'restart' if case == 'K1' else 'stop'}")
            t_inj = time.monotonic()
            if case == "K1":
                seconds = self.compose("restart", "kafka")
                return {"kind": "service_restart", "service": "kafka", "t_inj": t_inj, "seconds": seconds,
                        "ready": self.wait_ready("kafka")}
            self.compose("stop", "mysql")
            time.sleep(max(0.0, t_inj + s.outage_s - time.monotonic()))
            self.compose("start", "mysql")
            return {"kind": "service_stop", "service": "mysql", "t_inj": t_inj, "restored": self.wait_ready("mysql")}
        if case == "X1":
            claim = self.wait_for(lambda: self.claim_of(job_id), s.phase_timeout_s, f"job {job_id}'s claim")
            t_inj = time.monotonic()
            return {"kind": "publish", "worker": claim["worker"], "t_inj": t_inj, "published": self.publish_again(job_id)}
        raise ValueError(case)

    def inject_stop(self, case: str, job_id: int, claim: dict, t_inj: float) -> dict:
        """W6: the worker stopped until the standby takes over. W7: the whole tree, for w7_stop_s.
        Then SIGCONT, the old worker's fenced event, and SIGTERM (its attempt is no longer its own)."""
        import psutil
        worker = claim["worker"]
        if case == "W6":
            frozen = [psutil.Process(self.procs[worker].pid)]
            frozen[0].suspend()
            self.wait_for(lambda: (c := self.claim_of(job_id)) and c["attempt"] > claim["attempt"],
                          self.settings.phase_timeout_s, "the takeover")
        else:
            frozen = self.stop_tree(worker, claim["run_id"])
            time.sleep(max(0.0, t_inj + self.settings.w7_stop_s - time.monotonic()))
        resumed = time.monotonic()
        for p in reversed(frozen):
            try:
                p.resume()
            except psutil.Error:
                pass
        fenced = self.wait_for(lambda: next(iter(events_named(self.worker_logs()[worker], "fenced",
                                                              job_id=job_id, attempt=claim["attempt"])), None),
                               120, f"worker {worker}'s fenced event")
        self.procs[worker].send_signal(signal.SIGTERM)
        self.wait_for(lambda: self.procs[worker].poll() is not None, 60, f"worker {worker} to stop")
        return {"kind": "sigstop" if case == "W6" else "sigstop_tree", "worker": worker, "attempt": claim["attempt"],
                "t_inj": t_inj, "resumed": resumed, "fenced_mono": fenced["mono"], "stopped": len(frozen)}

    # One job

    def run_job(self, position: int, case: str) -> dict:
        s = self.settings
        record = {"position": position, "case": case, "owner_before": self.wait_owner()}
        armed, release, injection = None, None, None
        if case in HOOKS:
            armed, release = self.arm_fault(position, case, record["owner_before"])
        if case == "K2":
            self.read_peaks(closes="kafka stop")
            t_inj = time.monotonic()
            self.compose("stop", "kafka")
            injection = {"kind": "service_stop", "service": "kafka", "t_inj": t_inj}
        t_submit = time.monotonic()
        job_id = self.submit()
        record["job_id"] = job_id
        if job_id is None:
            self.log.log("job_not_submitted", position=position, case=case)
            if case == "K2":                                 # never leave the broker stopped
                self.compose("start", "kafka")
                self.wait_ready("kafka")
            if armed is not None:
                self.fault_file(armed).unlink(missing_ok=True)
            return {**record, "outcome": "submit_failed"}
        try:
            if case == "K2":
                time.sleep(max(0.0, injection["t_inj"] + s.outage_s - time.monotonic()))
                self.compose("start", "kafka")
                injection["restored"] = self.wait_ready("kafka")
            elif case != "C0":
                injection = self.inject(position, case, job_id, armed, release)
            missed = None
        except PhaseMissed as error:
            missed = str(error)
            if armed is not None:
                self.fault_file(armed).unlink(missing_ok=True)
        reference = deadline_reference(case)
        if missed is not None or reference == "submit":
            reference_mono, d = t_submit, deadline_seconds("C0", self.timing, s)
            reference = "submit"
        else:
            reference_mono = injection["restored"] if reference == "restored" else injection["t_inj"]
            d = deadline_seconds(case, self.timing, s)
        deadline_mono = reference_mono + d
        self.batch_jobs.append((job_id, case, reference, d, deadline_mono, s.max_lag_s))
        self.log.log("deadline", position=position, job_id=job_id, case=case, reference=reference,
                     reference_mono=reference_mono, deadline_s=d, deadline_mono=deadline_mono, max_lag_s=s.max_lag_s,
                     t_submit=t_submit)
        self.log.log("injection", position=position, job_id=job_id, case=case, missed=missed, **(injection or {}))
        tracker = Tracker(self, job_id, deadline_mono, deadline_mono + d)
        tracker.start()
        if case == "X1" and missed is None:                  # the second duplicate, once the job succeeded
            try:
                self.wait_for(lambda: self.job_status(job_id) == "succeeded", 2 * d, f"job {job_id} to succeed")
                self.log.log("published_again", job_id=job_id, after="succeeded",
                             published=self.publish_again(job_id), t=time.monotonic())
            except PhaseMissed as error:
                self.log.log("published_again", job_id=job_id, after=None, error=str(error))
        tracker.join()
        record.update(final=tracker.final, finished_mono=tracker.finished_mono, observation=tracker.observation,
                      missed=missed)
        self.log.log("job_done", position=position, job_id=job_id, case=case, final=tracker.final,
                     finished_mono=tracker.finished_mono)
        return record

    def after_job(self, record: dict) -> None:
        """The restart rule (2.4), the group after a Kafka restart, and the peaks of P4."""
        restarted = [w for w in WORKERS if self.procs[w].poll() is not None]
        for worker in restarted:
            self.start_worker(worker)
            self.log.log("restarted", worker=worker, position=record["position"])
        if record["case"] in ("K1", "K2"):
            time.sleep(self.timing.session_timeout + self.timing.heartbeat_interval)
        for worker in restarted:
            self.wait_joined(worker)
        self.log.log("owner", owner=self.wait_owner(), position=record["position"])
        if self.read_peaks() == "stop":
            self.stop_reason = "memory"

    # Start, quiescence and the final snapshot

    def reference_run(self) -> None:
        """The reference run: the job's windows and spark_pipeline steps, each under a launcher
        with the harness as its parent, so it takes the host lock and registers its tree (2.2)."""
        from etf_risk.jobs.params import JobParams
        from etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline
        s = self.settings
        params = JobParams(s.snapshot, s.kind, stride=s.stride)
        pipeline = SubprocessPipeline(store_id=self.store_id, processed_root=REPO_ROOT / "data" / "processed",
                                      worker_id="reference", lock_path=DEFAULT_LOCK, timing=self.timing)
        run_dir = self.out / "reference"

        class Reference:
            run_id = "reference"

        work, logs = run_dir / ".work", run_dir / "logs"
        for folder in (work / "tmp", work / "spark", work / "jtmp", logs):
            folder.mkdir(parents=True, exist_ok=True)
        marker = processes.marker(self.store_id, "reference", secrets.token_hex(8))
        env = pipeline.step_env(work, marker)
        for name, argv in pipeline.commands(params, Reference, run_dir)[:2]:
            limit = self.timing.step_limit(name)
            command = [sys.executable, "-m", "etf_risk.jobs.launcher", "--marker", marker, "--lock", str(DEFAULT_LOCK),
                       "--registry", str(pipeline.registry), "--lock-wait", str(self.timing.lock_wait(name)),
                       "--step-limit", str(limit), "--cwd", str(work), "--step-log", str(logs / f"{name}.log"),
                       "--result", str(logs / f"{name}.launcher.json"), "--", *argv]
            before = time.monotonic()
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, env=env, cwd=work, start_new_session=True,
                                    stdout=open(logs / f"{name}.launcher.log", "ab"), stderr=subprocess.STDOUT)
            deadline = time.monotonic() + self.timing.lock_wait(name) + limit + 30
            proc.stdin.write((json.dumps({"monotonic": time.monotonic(), "seq": 0, "deadline": deadline}) + "\n").encode())
            proc.stdin.flush()
            code = proc.wait(timeout=deadline - time.monotonic() + 30)
            proc.stdin.close()
            self.log.log("reference_step", step=name, exit=code, before=before, after=time.monotonic())
            if code != 0:
                raise RuntimeError(f"the reference run's {name} step failed (exit {code})")

    def quiesce(self) -> dict:
        """4.4: SIGKILL every writer, then wait until no attempt's process and no other client
        connection is left."""
        for proc in self.procs.values():
            if proc.poll() is None:
                proc.kill()                                  # SIGKILL
        for proc in self.procs.values():
            proc.wait(timeout=30)
        try:                                                  # each launcher ends its tree on EOF
            self.wait_for(lambda: not self._marked(), self.timing.watchdog_tick + self.timing.kill_grace + 10,
                          "the attempts' processes to end")
            processes_left = False
        except PhaseMissed:
            processes_left = True
        record = {"processes_left": processes_left, "other_connections": self.other_connections()}
        self.log.log("quiescent", **record)
        return record

    def _marked(self) -> bool:
        return any(v.startswith(f"{self.store_id}:") for v in processes.marked_processes())

    def crosscheck(self) -> dict:
        """4.5, step 3: the harness's records in TEMPORARY tables, then Q0-Q3b in one consistent
        snapshot, each saved as CSV; Q0's fingerprint."""
        folder = self.out / "crosscheck"
        folder.mkdir(exist_ok=True)
        statements = crosscheck_statements()
        values = ", ".join([self.PARAM] * 6)
        conn = self.connect()
        fingerprint = {}
        try:
            with closing(conn.cursor()) as cursor:
                for name, sql in statements:
                    if name == "DDL":
                        cursor.execute(self.statement(sql))
                cursor.executemany("INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono,"
                                   f" max_lag_s) VALUES ({values})", self.batch_jobs)
                cursor.executemany("INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono,"
                                   f" status, attempt_number, accepted_attempt) VALUES ({values})", self.observations)
                cursor.executemany("INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number,"
                                   f" result_digest) VALUES ({values})", worker_accepts(self.worker_logs()))
                cursor.execute(self.SNAPSHOT)
                for name, sql in statements:
                    if name == "DDL":
                        continue
                    cursor.execute(self.statement(sql))
                    columns = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    with open(folder / f"{name}.csv", "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows([[csv_value(v) for v in row] for row in rows])
                    if name == "Q0":
                        fingerprint = {c: int(v) for c, v in zip(columns, rows[0])}
                cursor.execute("COMMIT")
        finally:
            conn.close()
        return fingerprint

    def q0(self) -> dict:
        sql = dict(crosscheck_statements())["Q0"]
        conn = self.connect()
        try:
            with closing(conn.cursor()) as cursor:
                cursor.execute(self.statement(sql))
                columns = [d[0] for d in cursor.description]
                return {c: int(v) for c, v in zip(columns, cursor.fetchone())}
        finally:
            conn.close()

    def final_snapshot(self) -> dict:
        """4.5: peaks, status --check, the cross-check, the export, and Q0 again."""
        self.read_peaks(closes="end")
        status = self.cli("status", "--check", check=False)
        (self.out / "status-check.txt").write_text(f"exit {status.returncode}\n{status.stdout}{status.stderr}")
        first = self.crosscheck()
        self.cli("export", str(self.out / "export"))
        exported = fingerprint_from_export(self.out / "export")
        again = self.q0()
        record = {"status_check_exit": status.returncode, "fingerprints": [first, exported, again],
                  "fingerprints_agree": first == exported == again,
                  "batch_peaks": {s: self.peaks.batch_peak(s) for s in ("mysql", "kafka")}}
        self.log.log("final_snapshot", **record)
        return record

    def run(self) -> int:
        """The batch: start, every planned job until one is left unfinished or memory stops it,
        quiescence, the final snapshot, and the services removed."""
        self.log.log("batch_started", purpose=self.purpose, plan_seed=self.plan["seed"], code=code_identity(),
                     clock=clock_pair(), settings=asdict(self.settings), topic=self.topic)
        self.services_up()
        try:
            self.cli("init-db")
            self.cli("create-topic")
            self.store_id = self.store().store_id()
            self.reference_run()
            self.start("reconciler", "reconciler")
            self.start_worker("A")
            self.log.log("owner", owner=self.wait_joined("A"), position=0)
            self.start_worker("B")
            self.log.log("owner", owner=self.wait_joined("B"), position=0)
            for position, case in enumerate(self.plan["jobs"], start=1):
                if self.stop_reason is not None:
                    self.log.log("not_run", position=position, case=case, why=self.stop_reason)
                    continue
                try:
                    record = self.run_job(position, case)
                    if record.get("final") is None:
                        self.stop_reason = "an unfinished job" if record.get("job_id") else "a submit that failed"
                        continue
                    self.after_job(record)
                except Exception as error:                   # recorded; the batch still ends cleanly
                    self.log.log("job_error", position=position, case=case, error=f"{type(error).__name__}: {error}")
                    self.stop_reason = "an error in the harness"
            try:
                self.quiesce()
                self.final_snapshot()
            except Exception as error:
                self.log.log("final_error", error=f"{type(error).__name__}: {error}")
                self.stop_reason = self.stop_reason or "an error in the final snapshot"
        finally:
            for proc in self.procs.values():
                if proc.poll() is None:
                    proc.kill()
            self.log.log("batch_ended", clock=clock_pair(), code=code_identity(), stop_reason=self.stop_reason)
            self.compose("down", "-v")
        return 0


# Command line

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs.harness", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="fix a batch: its purpose, its jobs and its settings")
    plan.add_argument("--purpose", choices=PURPOSES, required=True,
                      help="preflight records are kept apart and never count as formal results (8.6)")
    plan.add_argument("--seed", type=int, required=True)
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--settings", type=Path, help="JSON replacing any of the default settings")
    plan.add_argument("--jobs", help="cases in this order, comma-separated, instead of the shuffled plan")
    est = commands.add_parser("estimate", help="the plan's expected duration, from stated assumptions")
    est.add_argument("--plan", type=Path, required=True)
    batch = commands.add_parser("batch", help="run one plan on fresh containers")
    batch.add_argument("--plan", type=Path, required=True)
    batch.add_argument("--out", type=Path, required=True, help="a new folder inside one named after the purpose")
    batch.add_argument("--formal", action="store_true", help="run a formal plan; only once Part A is approved")
    args = parser.parse_args(argv)
    if args.command == "plan":
        settings = Settings.from_dict(json.loads(args.settings.read_text())) if args.settings else Settings()
        jobs = [c.strip() for c in args.jobs.split(",")] if args.jobs else None
        args.out.write_text(json.dumps(make_plan(settings, args.seed, purpose=args.purpose, jobs=jobs), indent=2)
                            + "\n")
        print(f"{args.purpose} plan written to {args.out}")
        return 0
    plan_data = json.loads(args.plan.read_text())
    if args.command == "estimate":
        print(json.dumps(estimate(plan_data), indent=2))
        return 0
    purpose = plan_data.get("purpose")
    if purpose not in PURPOSES:
        parser.error("the plan names no purpose: make it again with plan --purpose")
    if args.out.resolve().parent.name != purpose:
        parser.error(f"a {purpose} batch goes in a folder named {purpose}, such as"
                     f" data/outputs-recovery/{purpose}/<batch>, so that its records stay apart")
    if purpose == "formal" and not args.formal:
        parser.error("a formal batch needs --formal, given only once the author has approved Part A")
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "plan.json").write_text(json.dumps(plan_data, indent=2) + "\n")
    return Batch(plan_data, args.out).run()


if __name__ == "__main__":
    sys.exit(main())
