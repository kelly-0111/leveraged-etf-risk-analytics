"""The isolated memory-budget check of the job queue with the real pipeline (spec §11,
docs/worker-pipeline.md): fresh MySQL and Kafka containers, the job suites, then the 10
acceptance cases, with the containers, the step trees and the job processes measured
throughout. It changes no budget: the containers are judged against their existing budgets
(spec §11), and every other threshold is a proposal, reported and not enforced.

    uv run --group jobs python tests/memory_check.py --preflight     # the machine checks only
    uv run --group jobs python tests/memory_check.py --out data/outputs-memory/<UTC stamp>

Outcomes, in the exit status and in record.json:
- 0, passed: the run counts, the container limits held, and both pytest runs passed with
  nothing left behind. This validates the container limits only.
- 1, failed measurement: the run counts, and a container limit was not held (memory.peak above
  its limit in a lifetime, an oom or oom_kill event, a container OOM-killed or stopped), a
  pytest run failed, or processes were left behind. Container-limit misses and test-run misses
  are listed apart; a test failure or timeout under host memory pressure is to be diagnosed
  before it is attributed to a container limit.
- 2, not counted: a required condition was not met, before the start (nothing is started) or
  during the run (an invalid run).
- 3, tool error: the check stopped on an error, or its cleanup did not finish.
- 130: interrupted; the cleanup still runs.

Conditions of the run:
- before anything starts: a clean worktree, so the record names one commit (untracked files
  under docs/ai-usage/, the AI-log transcripts that sessions write there, are ignored and
  counted in the record; approved 2026-10-24); no running
  container outside this project, and none of this project's own, which may be another
  session's (it never stops, pauses or removes a container it did not start); ports 3307,
  9094 and 6380 free; the snapshot that the acceptance cases read;
- over the run: both pytest runs reported results, with no acceptance case skipped; both
  containers were created by this run and read throughout, with their budgets as their limits
  and no counter going down within a lifetime; Docker's record of each container was read
  after each run; every step was launched; a worker and a reconciler were sampled.

Host memory (approved 2026-10-24) decides only whether the native-process figures are
representative, not whether the run counts: CONDITIONS["idle_available"] available with the
stack up and idle for SETTLE_S seconds, and the compressor and swap each growing by at most
their CONDITIONS limit. When one fails, the native figures are recorded and marked as measured
under host memory pressure. The container verdict does not depend on it: macOS compressing or
swapping the VM's memory is not seen by the cgroup accounting inside the VM (reasoning, not a
measured result). Host pressure is recorded either way.

What is measured while pytest runs the job suites and then the acceptance cases:
- every 0.5 s: the host's available memory, and the RSS of every
  `python -m etf_risk.jobs worker|reconciler|submit` process (a submit lasts about a
  second, so its figure is a lower bound);
- every 5 s, and once more after the last run: the compressor's and swap's size, and each
  container's cgroup: its identity (the inode of /sys/fs/cgroup), memory.peak,
  memory.current, memory.stat (anon, file and kernel memory) and memory.events;
- after each run and before the cleanup: Docker's record of each container (created,
  started, status, exit code, OOM-killed, restart count). An OOM kill that stops a container
  leaves no cgroup to read, and Docker's record still shows it;
- each step tree's peak summed RSS, from its launcher's record (sampled every 0.5 s).

A container's readings are split into lifetimes where its cgroup's identity changes: a restart
gives it a new cgroup, as memory.peak's reset showed in M2. Every lifetime is a verified fresh
cgroup, the first because Docker created the container after this run started it, each later
one because its identity is new; so its counters count from zero, as memory.peak does, with
startup and idle included. A lifetime's readings stop at most 5 s before its container's
restart.

The supplementary thresholds in PROPOSED are reported apart from the container limits and from
each other: the containers' anon memory and limit hits, and the native-process targets (step
trees, worker, reconciler, submit). The native-process targets are not approved budgets; a
pass does not validate them, and no supplementary threshold changes the outcome.

Why the native figures need the host conditions: M2's step trees peaked lower than the stride
experiment's (1.19-1.36 against 2.62-2.73 GiB at stride 21). One hypothesis, not
established, is that the host was short of memory, so that macOS compressed or swapped pages,
which then leave RSS. Native figures from a run that met the host conditions are free of that
effect, whatever caused the difference.

Whatever happens, the processes the runs left behind are ended, the containers are unpaused,
and the stack is removed (down -v). A process belongs to the check if its command line names
the check's temporary folder, if its environment carries RUN_ENV with that folder, or if it
carries the job-store marker of a store whose attempt folders are in it; no other process is
touched. A process still there SETTLE_LEFTOVERS_S after a run counts as left behind.

--out receives record.json (conditions, budgets, proposals, tools, code state, Docker's
records, measurements, verdict and outcome), samples.jsonl, each pytest run's log and JUnit
file, and the launchers' and attempts' records. pytest's temporary folders, with the runs'
outputs, are removed unless --keep.

AI contribution: written with Claude Code (Opus 5.5).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable

import psutil

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from etf_risk import services  # noqa: E402
from etf_risk.jobs import processes  # noqa: E402
from etf_risk.provenance import code_state  # noqa: E402

MiB, GiB = 2**20, 2**30
# The containers' budgets (spec §11), which are also their limits in docker/compose.yaml.
BUDGETS = {"mysql": 512 * MiB, "kafka": 640 * MiB}
# Approved on 2026-10-24: the host conditions for representative native-process figures (not for
# the container verdict),
CONDITIONS = {
    # one 2.7 GiB step tree (the host lock runs one at a time), 0.3 for the job processes and
    # pytest, 0.5 for both containers growing to their budgets, and 0.5 to spare
    "idle_available": 4 * GiB,
    "compressor_growth": 256 * MiB,
    "swap_growth": 256 * MiB,
}
# and supplementary thresholds, reported and never enforced: the containers' anon memory and limit
# hits, and the native-process targets ("step " and "process "), which are not approved budgets.
PROPOSED = {
    "mysql anon": 410 * MiB,          # 80% of its budget; 264 and 313 MiB after one and two runs (spec §11)
    "kafka anon": 512 * MiB,          # 80% of its budget, with a 256 MiB heap
    "mysql limit hits": 0,            # memory.events max
    "kafka limit hits": 0,
    "step windows": 512 * MiB,        # 0.12 GiB in M2
    "step spark_pipeline": 3 * GiB,   # native stride 21 in the stride experiment: 2.62-2.73 GiB
    "step verify": 3 * GiB,           # a Spark session too; 0.45-0.58 GiB in M2
    "process worker": 128 * MiB,      # 63.0 MiB in M2
    "process reconciler": 128 * MiB,  # 51.6 MiB in M2
    "process submit": 128 * MiB,      # not measured before
}
NATIVE = ("step ", "process ")   # the prefixes of the native-process targets in PROPOSED
IGNORED_UNTRACKED = "docs/ai-usage/"   # sessions write their AI-log transcripts here (approved 2026-10-24)
PORTS = (3307, 9094, 6380)
SETTLE_S = 30
SETTLE_LEFTOVERS_S = 15.0    # above a launcher's 7 s kill grace after its worker is gone
FRESH_TOLERANCE_S = 5.0      # between this machine's clock and the Docker VM's
SNAPSHOT = REPO / "data" / "processed" / "full-2026-10-12"   # what tests/test_jobs_live_pipeline.py reads
RUNS = (("suites", sorted(p.relative_to(REPO).as_posix() for p in (REPO / "tests").glob("test_jobs_*.py")), {}),
        ("acceptance", ["tests/test_jobs_live_pipeline.py"], {"ETF_RISK_LIVE_PIPELINE": "1"}))
TIMEOUTS = {"suites": 1800, "acceptance": 3600}
RUN_ENV = "ETF_RISK_MEMORY_CHECK_RUN"   # set to the temporary folder in the runs' environment
ROLES = ("worker", "reconciler", "submit")
VM_PROCESS = "com.apple.Virtualization.VirtualMachine"   # Docker Desktop's VM on Apple silicon
EVENTS = ("low", "high", "max", "oom", "oom_kill", "oom_group_kill")
KERNEL_PARTS = ("kernel_stack", "pagetables", "sec_pagetables", "percpu", "vmalloc", "slab")
CGROUP_SCRIPT = ('cd /sys/fs/cgroup && set -- $(ls -di .) && echo "cgroup $1" && '
                 'printf "peak %s\\nlimit %s\\ncurrent %s\\n" "$(cat memory.peak)" "$(cat memory.max)" '
                 '"$(cat memory.current)" && while read k v; do echo "stat_$k $v"; done < memory.stat && '
                 'while read k v; do echo "events_$k $v"; done < memory.events')
EXIT = {"passed": 0, "failed": 1, "not counted": 2, "tool error": 3, "interrupted": 130}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def size(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value / GiB:.2f} GiB" if abs(value) >= GiB else f"{value / MiB:,.0f} MiB"


def largest(values: Iterable[int | None]) -> int | None:
    return max((v for v in values if v is not None), default=None)


# Containers: cgroups and Docker's records

def parse_cgroup(text: str) -> dict | None:
    """CGROUP_SCRIPT's output as one reading: the cgroup's identity; the total peak, limit (None
    for "max") and current usage; anon, file and kernel memory (the sum of its parts on kernels
    without a kernel line); and the memory.events counters. None without a peak or an anon figure."""
    raw: dict[str, int | None] = {}
    for line in text.splitlines():
        key, _, value = line.strip().partition(" ")
        value = value.strip()
        if key and value == "max":
            raw[key] = None
        elif key and value.isdigit():
            raw[key] = int(value)
    if not isinstance(raw.get("peak"), int) or not isinstance(raw.get("stat_anon"), int):
        return None
    has_kernel = isinstance(raw.get("stat_kernel"), int)
    return {"cgroup": raw.get("cgroup"), "peak": raw["peak"], "limit": raw.get("limit"),
            "current": raw.get("current"), "anon": raw["stat_anon"], "file": raw.get("stat_file"),
            "kernel": raw["stat_kernel"] if has_kernel else sum(raw.get(f"stat_{p}") or 0 for p in KERNEL_PARTS),
            "kernel_from": "kernel" if has_kernel else "parts",
            "events": {name: raw.get(f"events_{name}") or 0 for name in EVENTS}}


def read_cgroup(service: str, run: Callable = subprocess.run) -> dict | None:
    """One reading of the service container's cgroup; None while it cannot be read (paused,
    stopped, restarting, or docker failing)."""
    try:
        out = run(["docker", "compose", "-f", str(services.COMPOSE_FILE), "exec", "-T", service, "sh", "-c",
                   CGROUP_SCRIPT], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return parse_cgroup(out.stdout) if out.returncode == 0 else None


def docker_time(text: str | None) -> datetime | None:
    """Docker's RFC 3339 time, to the microsecond (Docker gives nanoseconds)."""
    m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)", text or "")
    if not m:
        return None
    offset = "+00:00" if m.group(3) == "Z" else m.group(3)
    return datetime.fromisoformat(f"{m.group(1)}.{(m.group(2) or '0')[:6].ljust(6, '0')}{offset}")


def docker_state(service: str, run: Callable = subprocess.run) -> dict | None:
    """Docker's record of the service's container: created, started, status, exit code, OOM-killed
    and restart count. None without exactly one such container, or when docker fails."""
    try:
        ids = run(["docker", "compose", "-f", str(services.COMPOSE_FILE), "ps", "-aq", service],
                  capture_output=True, text=True, timeout=30)
        if ids.returncode != 0 or len(ids.stdout.split()) != 1:
            return None
        out = run(["docker", "inspect", "--format", "{{.Created}} {{.RestartCount}} {{json .State}}",
                   ids.stdout.split()[0]], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        created, restarts, state = out.stdout.strip().split(" ", 2)
        state = json.loads(state)
        return {"id": ids.stdout.split()[0][:12], "created": created, "restart_count": int(restarts),
                "status": state["Status"], "started": state.get("StartedAt"), "exit_code": state.get("ExitCode"),
                "oom_killed": bool(state.get("OOMKilled"))}
    except (ValueError, KeyError, TypeError):
        return None


def created_by_this_run(state: dict | None, started_utc: str) -> bool:
    """Docker created the container after this run began starting the stack."""
    created = docker_time(state["created"]) if state else None
    return created is not None and created >= datetime.fromisoformat(started_utc) - timedelta(seconds=FRESH_TOLERANCE_S)


def lifetimes(readings: Iterable[dict | None]) -> list[list[dict]]:
    """The readings of each lifetime of a container, in time order: a new lifetime starts where the
    cgroup's identity changes. A missing reading (paused, stopped, restarting) starts none."""
    lives: list[list[dict]] = []
    for r in readings:
        if r is None:
            continue
        if not lives or r.get("cgroup") != lives[-1][-1].get("cgroup"):
            lives.append([])
        lives[-1].append(r)
    return lives


def summarize_container(readings: list[dict | None], budget: int, fresh: bool) -> dict:
    """Per lifetime, and over the run. Each lifetime is one cgroup, its counters counted from zero
    like memory.peak, so startup and idle count: verified when the container was created by this
    run (fresh), every reading names its cgroup, and no counter goes down within a lifetime."""
    problems = [] if fresh else ["its container is not verified as created by this run"]
    lives = lifetimes(readings)
    if any(r.get("cgroup") is None for life in lives for r in life):
        problems.append("a reading does not name its cgroup")
    parts = []
    for n, life in enumerate(lives, 1):
        if any(b["peak"] < a["peak"] or any(b["events"][k] < a["events"][k] for k in EVENTS)
               for a, b in zip(life, life[1:])):
            problems.append(f"a counter went down within lifetime {n}")
        first, last = life[0], life[-1]
        parts.append({"cgroup": first.get("cgroup"), "readings": len(life), "from_utc": first.get("at_utc"),
                      "to_utc": last.get("at_utc"), "limit_bytes": last["limit"],
                      "peak_bytes": max(r["peak"] for r in life),
                      **{f"{kind}_bytes": largest(r[kind] for r in life) for kind in ("anon", "file", "kernel")},
                      "events_at_first_reading": dict(first["events"]), "events": dict(last["events"])})
    return {"budget_bytes": budget, "verified": not problems, "problems": problems, "lifetimes": parts,
            **{key: largest(s[key] for s in parts) for key in ("peak_bytes", "anon_bytes", "file_bytes", "kernel_bytes")},
            "events": {k: sum(s["events"][k] for s in parts) for k in EVENTS}}


# Host and processes

def compressor_bytes(vm_stat: str) -> int:
    page = re.search(r"page size of (\d+) bytes", vm_stat)
    pages = re.search(r"Pages occupied by compressor:\s+(\d+)", vm_stat)
    if not page or not pages:
        raise ValueError("vm_stat: no page size or compressor line")
    return int(pages.group(1)) * int(page.group(1))


def host_memory() -> dict:
    vm_stat = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=10).stdout
    return {"available_bytes": psutil.virtual_memory().available, "compressor_bytes": compressor_bytes(vm_stat),
            "swap_bytes": psutil.swap_memory().used}


def available_memory() -> int:
    return psutil.virtual_memory().available


def role(cmdline: list[str] | None) -> str | None:
    """worker, reconciler or submit for `python -m etf_risk.jobs <role> ...`, pytest for `python -m pytest`."""
    if not cmdline or len(cmdline) < 3 or cmdline[1] != "-m":
        return None
    if cmdline[2] == "etf_risk.jobs":
        return cmdline[3] if len(cmdline) > 3 and cmdline[3] in ROLES else None
    return "pytest" if cmdline[2] == "pytest" else None


@dataclass(frozen=True)
class Seen:
    """A process as the sampler sees it; tests make their own."""
    key: tuple                      # (pid, create time): a pid reused by a new process is a new key
    pid: int
    name: str | None
    cmdline: Callable[[], list[str]]
    rss: Callable[[], int]


def live_processes() -> Iterable[Seen]:
    for proc in psutil.process_iter(["name", "create_time"]):
        yield Seen((proc.pid, proc.info["create_time"]), proc.pid, proc.info["name"], proc.cmdline,
                   lambda proc=proc: proc.memory_info().rss)


class Sampler:
    """Two sampling threads, and what they keep: the largest of each figure, and the smallest
    available memory. Tests call sample_processes and sample_containers directly."""

    def __init__(self, samples: Path, *, read_cgroup: Callable = read_cgroup, host_memory: Callable = host_memory,
                 processes: Callable = live_processes, available: Callable = available_memory,
                 clock: Callable = now, intervals: tuple[float, float] = (0.5, 5.0)):
        self.samples = samples
        self._read_cgroup, self._host_memory, self._processes = read_cgroup, host_memory, processes
        self._available, self._clock, self._intervals = available, clock, intervals
        self.rss = {name: 0 for name in (*ROLES, "pytest", "vm")}
        self.pids: dict[str, set[int]] = {name: set() for name in self.rss}
        self.available_min: int | None = None
        self.readings: dict[str, list[dict | None]] = {service: [] for service in services.SERVICES}
        self.host: list[dict] = []
        self.errors = 0
        self._roles: dict[tuple, str | None] = {}
        self._stopping = threading.Event()
        self._threads: list[threading.Thread] = []

    def sample_processes(self) -> None:
        available = self._available()
        self.available_min = available if self.available_min is None else min(self.available_min, available)
        for seen in self._processes():
            if seen.key not in self._roles:      # a process's command line is read once
                try:
                    self._roles[seen.key] = "vm" if seen.name == VM_PROCESS else role(seen.cmdline())
                except (psutil.Error, OSError):
                    self._roles[seen.key] = None
            name = self._roles[seen.key]
            if name:
                try:
                    self.rss[name] = max(self.rss[name], seen.rss())
                except (psutil.Error, OSError):
                    continue
                self.pids[name].add(seen.pid)

    def sample_containers(self) -> None:
        line: dict = {"at_utc": self._clock()}
        try:
            line.update(self._host_memory())
        except Exception as error:          # the containers are read all the same
            self._failed(error)
        for service in services.SERVICES:
            reading = self._read_cgroup(service)
            line[service] = reading = None if reading is None else {**reading, "at_utc": line["at_utc"]}
            self.readings[service].append(reading)
        line["rss_bytes"] = dict(self.rss)
        self.host.append(line)
        with self.samples.open("a") as out:
            out.write(json.dumps(line) + "\n")

    def tick(self, sample: Callable[[], None]) -> None:
        """One sample. A failure is counted, the first three are reported, and sampling goes on."""
        try:
            sample()
        except Exception as error:
            self._failed(error)

    def _failed(self, error: Exception) -> None:
        self.errors += 1
        if self.errors <= 3:
            print(f"sampler: {type(error).__name__}: {error}", file=sys.stderr)

    def start(self) -> None:
        for sample, interval in zip((self.sample_processes, self.sample_containers), self._intervals):
            thread = threading.Thread(target=self._loop, args=(sample, interval), daemon=True)
            thread.start()
            self._threads.append(thread)

    def stop(self) -> None:
        self._stopping.set()
        for thread in self._threads:
            thread.join()

    def _loop(self, sample: Callable[[], None], interval: float) -> None:
        while not self._stopping.is_set():
            self.tick(sample)
            self._stopping.wait(interval)


# Records of the runs

def launcher_peaks(root: Path) -> dict[str, int]:
    """The largest peak summed RSS per step over every launch under root, failed ones too."""
    peaks: dict[str, int] = {}
    for path in root.glob("**/logs/*.launcher.json"):
        step = path.name.removesuffix(".launcher.json")
        peaks[step] = max(peaks.get(step, 0), json.loads(path.read_text()).get("peak_rss_bytes") or 0)
    return peaks


def job_label(params: dict) -> str:
    return "calendar-year" if params["kind"] == "calendar-year" else f"{params['kind']}, stride {params['stride']}"


def job_peaks(root: Path) -> dict[str, dict[str, int]]:
    """Per kind of job and step, the largest peak over the attempts that wrote attempt.json."""
    peaks: dict[str, dict[str, int]] = {}
    for path in root.glob("**/attempt.json"):
        record = json.loads(path.read_text())
        job = peaks.setdefault(job_label(record["params"]), {})
        for step in record.get("steps", []):
            job[step["name"]] = max(job.get(step["name"], 0), step.get("peak_rss_bytes") or 0)
    return peaks


def keep_records(temp: Path, out: Path) -> None:
    """Copy the launchers' and attempts' records out of pytest's temporary folder."""
    for path in [*temp.glob("**/logs/*.launcher.json"), *temp.glob("**/attempt.json")]:
        target = out / path.relative_to(temp)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def junit_counts(path: Path) -> dict:
    """The JUnit file's totals; readable is False when the file is missing or broken."""
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        root = None
    suite = None if root is None else root if root.tag == "testsuite" else root.find("testsuite")
    if suite is None:
        return {"readable": False, "tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    return {"readable": True, **{key: int(suite.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}}


# Running pytest, and what it leaves behind

def run_bounded(command: list[str], *, cwd: Path, env: dict, log: Path, timeout: float, grace: float = 120) -> int | None:
    """A command in a session of its own, its output in log. Past timeout, or when this process
    is interrupted, the command gets SIGINT, so pytest runs its fixtures' teardown, and after
    grace its process group gets SIGKILL. The exit code, or None after a timeout."""
    with open(log, "w") as handle:
        process = subprocess.Popen(command, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            interrupt(process, grace)
            return None
        except BaseException:
            interrupt(process, grace)
            raise


def interrupt(process: subprocess.Popen, grace: float) -> None:
    process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)   # what is left of its group, the command included
    except (ProcessLookupError, PermissionError):
        pass
    process.wait()


def run_pytest(name: str, files: list[str], env: dict, out: Path, temp: Path, timeout: float) -> dict:
    """One pytest run, with its own temporary folder under temp, and its log and JUnit file in out."""
    junit = out / f"{name}.xml"
    command = [sys.executable, "-m", "pytest", *files, "-q", "-rs", "-p", "no:cacheprovider",
               "--basetemp", str(temp / name), "--junitxml", str(junit)]
    start = time.monotonic()
    code = run_bounded(command, cwd=REPO, env=env, log=out / f"{name}.log", timeout=timeout)
    return {"exit_code": code, "seconds": round(time.monotonic() - start, 1), **junit_counts(junit)}


def leftovers(temp: Path) -> list[psutil.Process]:
    """The processes that the runs under temp left behind, among this user's: those whose command
    line names temp (workers, reconcilers, launchers, steps, reference runs), those whose
    environment carries RUN_ENV with temp (the reference runs' JVMs and PySpark daemons), and those
    carrying the marker of a store whose attempt folders are under temp, at any depth (the steps'
    JVMs and Python workers). No other process is touched."""
    me, uid, folders = os.getpid(), os.getuid(), {str(temp), str(temp.resolve())}
    stores = {path.parent.name for path in temp.glob("**/job-*-attempt-*") if path.is_dir()}
    found: dict[int, psutil.Process] = {}
    for proc in psutil.process_iter(["cmdline", "uids"]):
        uids = proc.info["uids"]
        if proc.pid == me or uids is None or uids.real != uid:
            continue
        if any(folder in arg for arg in proc.info["cmdline"] or () for folder in folders):
            found[proc.pid] = proc
            continue
        try:
            env = proc.environ()
        except (psutil.Error, OSError):
            continue
        marker = processes.parse_marker(env.get(processes.MARKER_ENV))
        if env.get(RUN_ENV) in folders or (marker is not None and marker[0] in stores):
            found[proc.pid] = proc
    return list(found.values())


def end(procs: list[psutil.Process], *, grace: float = 30.0, rescan: Callable | None = None) -> dict:
    """SIGCONT first, since a stopped process cannot act on SIGTERM; then processes.terminate:
    SIGTERM, SIGKILL to what is left after grace, and rescans."""
    for p in procs:
        try:
            p.send_signal(signal.SIGCONT)
        except psutil.Error:
            pass
    return processes.terminate(procs, term_grace=grace, kill_confirm=5.0, rescan=rescan)


# The machine, and the check

def docker_compose(*args: str, timeout: float = 300) -> None:
    subprocess.run(["docker", "compose", "-f", str(services.COMPOSE_FILE), *args], check=True,
                   capture_output=True, text=True, timeout=timeout)


def wait_ready(env: dict) -> None:
    subprocess.run([sys.executable, "-m", "etf_risk.services", "ready", *services.SERVICES], cwd=REPO, env=env,
                   check=True, timeout=300)


def project_containers() -> int:
    """This project's containers, running or not, from any worktree: the Compose name is shared."""
    out = subprocess.run(["docker", "compose", "-f", str(services.COMPOSE_FILE), "ps", "-aq"],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise RuntimeError(f"docker compose ps failed with exit code {out.returncode}")
    return len(out.stdout.split())


def worktree_changes(porcelain: str) -> tuple[list[str], list[str]]:
    """`git status --porcelain` as (the changes that leave the worktree unclean, the untracked
    paths under IGNORED_UNTRACKED). A tracked change under IGNORED_UNTRACKED still counts."""
    unclean, ignored = [], []
    for line in porcelain.splitlines():
        if line.strip():
            status, path = line[:2], line[3:]
            (ignored if status == "??" and path.startswith(IGNORED_UNTRACKED) else unclean).append(path)
    return unclean, ignored


def git_changes() -> tuple[list[str], list[str]]:
    return worktree_changes(subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True,
                                           text=True, check=True).stdout)


def git_dirty() -> bool:
    return bool(git_changes()[0])


def ignored_untracked() -> int:
    return len(git_changes()[1])


def port_in_use(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def keep_awake() -> None:
    """No idle sleep while this process runs; caffeinate ends with it."""
    try:
        subprocess.Popen(["caffeinate", "-i", "-w", str(os.getpid())])
    except OSError:
        pass


def first_line(*command: str) -> str | None:
    try:
        out = subprocess.run(command, capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    lines = (out.stdout or out.stderr).strip().splitlines()
    return lines[0] if lines else None


def tools() -> dict:
    vm_memory = first_line("docker", "info", "--format", "{{.MemTotal}}")
    return {"uv": first_line("uv", "--version"), "java": first_line("java", "-version"),
            "docker": first_line("docker", "version", "--format", "{{.Client.Version}} (server {{.Server.Version}})"),
            "compose": first_line("docker", "compose", "version", "--short"),
            "python": platform.python_version(), "macos": platform.mac_ver()[0], "cpus": psutil.cpu_count(),
            "memory_bytes": psutil.virtual_memory().total,
            "docker_vm_memory_bytes": int(vm_memory) if vm_memory and vm_memory.isdigit() else None}


@dataclass
class System:
    """Everything the check does outside this process, so that tests can stand in for each part."""
    compose: Callable[..., None]
    ready: Callable[[dict], None]
    sleep: Callable[[float], None]
    monotonic: Callable[[], float]
    now: Callable[[], str]
    host_memory: Callable[[], dict]
    available: Callable[[], int]
    docker_state: Callable[[str], dict | None]
    sampler: Callable[[Path], Sampler]
    run_pytest: Callable[..., dict]
    leftovers: Callable[[Path], list]
    end: Callable[..., dict]
    project_containers: Callable[[], int]
    other_containers: Callable[[], int]
    git_dirty: Callable[[], bool]
    ignored_untracked: Callable[[], int]
    port_in_use: Callable[[int], bool]
    snapshot_exists: Callable[[], bool]
    keep_awake: Callable[[], None]
    tools: Callable[[], dict]
    code_state: Callable[[], dict]


def this_machine() -> System:
    return System(compose=docker_compose, ready=wait_ready, sleep=time.sleep, monotonic=time.monotonic, now=now,
                  host_memory=host_memory, available=available_memory, docker_state=docker_state, sampler=Sampler,
                  run_pytest=run_pytest, leftovers=leftovers, end=end, project_containers=project_containers,
                  other_containers=services.other_containers, git_dirty=git_dirty,
                  ignored_untracked=ignored_untracked, port_in_use=port_in_use,
                  snapshot_exists=SNAPSHOT.is_dir, keep_awake=keep_awake, tools=tools, code_state=code_state)


def preflight(system: System) -> list[str]:
    """What keeps the check from starting; empty when nothing does."""
    problems = []
    try:
        if system.git_dirty():
            problems.append("the worktree has uncommitted changes")
    except (OSError, subprocess.CalledProcessError) as error:
        problems.append(f"git: {error}")
    try:
        if others := system.other_containers():
            problems.append(f"{others} running container(s) outside the {services.PROJECT} project")
        if ours := system.project_containers():
            problems.append(f"{ours} container(s) of the {services.PROJECT} project exist, maybe another session's")
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as error:
        problems.append(f"docker: {error}")
    if busy := [str(port) for port in PORTS if system.port_in_use(port)]:
        problems.append(f"port(s) in use: {', '.join(busy)}")
    if not system.snapshot_exists():
        problems.append(f"no snapshot at {SNAPSHOT.relative_to(REPO)}")
    return problems


def measure(sampler: Sampler, idle: dict, temp: Path, runs: dict, left: dict, docker: dict, started_utc: str) -> dict:
    grew = {}
    for key in ("compressor", "swap"):
        values = [line[f"{key}_bytes"] for line in sampler.host if f"{key}_bytes" in line]
        grew[key] = max(values, default=idle[f"{key}_bytes"]) - idle[f"{key}_bytes"]
    return {"pytest": runs, "leftovers": left, "docker": docker,
            "host": {"idle": idle, "available_min_bytes": sampler.available_min,
                     "compressor_growth_bytes": grew["compressor"], "swap_growth_bytes": grew["swap"],
                     "vm_rss_bytes": sampler.rss["vm"]},
            "containers": {service: summarize_container(sampler.readings[service], BUDGETS[service],
                                                        created_by_this_run(docker["started"].get(service), started_utc))
                           for service in services.SERVICES},
            "steps": launcher_peaks(temp / "acceptance"), "jobs": job_peaks(temp / "acceptance"),
            "processes": {name: {"rss_bytes": sampler.rss[name], "processes": len(sampler.pids[name])}
                          for name in (*ROLES, "pytest")},
            "sampler_errors": sampler.errors}


def host_pressure(measured: dict) -> list[str]:
    """Why the native-process figures are not representative: the host conditions they missed."""
    host, reasons = measured["host"], []
    if host["idle"]["available_bytes"] < CONDITIONS["idle_available"]:
        reasons.append(f"{size(host['idle']['available_bytes'])} available with the stack idle, below "
                       f"{CONDITIONS['idle_available'] / GiB:.1f} GiB")
    for key in ("compressor", "swap"):
        grew, limit = host[f"{key}_growth_bytes"], CONDITIONS[f"{key}_growth"]
        if grew > limit:
            reasons.append(f"the {key} grew by {size(grew)}, more than {size(limit)}")
    return reasons


def judge(measured: dict) -> dict:
    """invalid: why the run does not count. Misses: test runs that failed or left processes
    behind, and container limits not held; these alone decide a run that counts. Reported apart,
    and never deciding: the supplementary container figures, and the native-process targets,
    which are not approved and are representative only when the host conditions held."""
    invalid: list[str] = []
    run_misses: list[str] = []
    container_misses: list[str] = []
    for name, run in measured["pytest"].items():
        if not run["readable"] or not run["tests"]:
            invalid.append(f"pytest {name}: no results")
    acceptance = measured["pytest"]["acceptance"]
    if acceptance["skipped"]:
        invalid.append(f"acceptance cases: {acceptance['skipped']} of {acceptance['tests']} skipped")
    for service, c in measured["containers"].items():
        if not c["lifetimes"]:
            invalid.append(f"{service}: no cgroup reading")
        invalid += [f"{service}: {problem}" for problem in c["problems"]]
        if any(s["limit_bytes"] != c["budget_bytes"] for s in c["lifetimes"]):
            invalid.append(f"{service}: its limit is not its {size(c['budget_bytes'])} budget")
    for key in PROPOSED:
        if key.startswith("step ") and key.removeprefix("step ") not in measured["steps"]:
            invalid.append(f"no launch of {key.removeprefix('step ')} was recorded")
    for name in ("worker", "reconciler"):
        if not measured["processes"][name]["processes"]:
            invalid.append(f"no {name} process was sampled")

    for name, run in measured["pytest"].items():
        if run["exit_code"] != 0 or run["failures"] or run["errors"]:
            run_misses.append(f"pytest {name}: exit {run['exit_code']}, {run['failures']} failed, {run['errors']} errors")
        if measured["leftovers"].get(name):
            run_misses.append(f"pytest {name} left {measured['leftovers'][name]} process(es) behind")
    stopped: dict[str, list[str]] = {service: [] for service in measured["containers"]}
    for label, states in measured["docker"].items():
        if label == "started":
            continue
        for service, state in states.items():
            if state is None:
                invalid.append(f"{service}: Docker's record {label} could not be read")
            elif state["oom_killed"]:
                stopped[service].append(f"OOM-killed, exit code {state['exit_code']}, by Docker's record {label}")
            elif state["status"] != "running":
                stopped[service].append(f"{state['status']}, exit code {state['exit_code']}, by Docker's record {label}")
    limits = []
    for service, c in measured["containers"].items():
        over = [(n, s["peak_bytes"]) for n, s in enumerate(c["lifetimes"], 1) if s["peak_bytes"] > c["budget_bytes"]]
        for n, peak in over:
            container_misses.append(f"{service} lifetime {n}: memory.peak {size(peak)}, above its "
                                    f"{size(c['budget_bytes'])} limit")
        events = {event: c["events"][event] for event in ("oom", "oom_kill")}
        for event, count in events.items():
            if count:
                container_misses.append(f"{service}: {count} {event} event(s)")
        container_misses += [f"{service}: {what}" for what in stopped[service]]
        limits.append({"container": service, "limit_bytes": c["budget_bytes"], "peak_bytes": c["peak_bytes"],
                       "lifetime_peaks_bytes": [s["peak_bytes"] for s in c["lifetimes"]], **events,
                       "stopped": stopped[service],
                       "held": bool(c["lifetimes"]) and not over and not any(events.values()) and not stopped[service]})

    def against(criterion: str, value: int | None) -> dict:
        threshold = PROPOSED.get(criterion)
        return {"criterion": criterion, "value": value, "threshold": threshold,
                "within": None if threshold is None or value is None else value <= threshold}

    container_figures = [against(f"{service} {kind}", value) for service, c in measured["containers"].items()
                         for kind, value in (("anon", c["anon_bytes"]), ("limit hits", c["events"]["max"]))]
    native = [against(f"step {step}", peak) for step, peak in sorted(measured["steps"].items())]
    native += [against(f"process {name}", measured["processes"][name]["rss_bytes"]
                       if measured["processes"][name]["processes"] else None) for name in ROLES]
    pressure = host_pressure(measured)
    misses = run_misses + container_misses
    passed = not invalid and not misses
    return {"counts": not invalid, "passed": passed, "validates": "container limits only" if passed else "nothing",
            "invalid": invalid, "misses": misses, "run_misses": run_misses, "container_misses": container_misses,
            "host_pressure": pressure, "container_limits": limits, "supplementary_container": container_figures,
            "native_targets": {"approved": False, "representative": not pressure, "results": native}}


def not_counted(reason: str) -> dict:
    return {"counts": False, "passed": False, "validates": "nothing", "invalid": [reason], "misses": [],
            "run_misses": [], "container_misses": [], "host_pressure": [], "container_limits": [],
            "supplementary_container": [], "native_targets": {"approved": False, "representative": False, "results": []}}


def outcome(record: dict) -> str:
    if record.get("interrupted"):
        return "interrupted"
    if record.get("error") or record["cleanup_errors"] or record.get("project_containers_after") != 0:
        return "tool error"
    verdict = record.get("verdict")
    if verdict is None:
        return "tool error"
    return "passed" if verdict["passed"] else "failed" if verdict["counts"] else "not counted"


def end_leftovers(system: System, temp: Path, record: dict, after: str) -> int:
    """End what the runs left behind and record it under leftovers[after]. Processes that are
    ending on their own (a launcher in its kill grace, a PySpark daemon whose JVM is gone) get
    SETTLE_LEFTOVERS_S first; only those still there are ended and counted."""
    found = system.leftovers(temp)
    seen, deadline = len(found), system.monotonic() + SETTLE_LEFTOVERS_S
    while found and system.monotonic() < deadline:
        system.sleep(0.5)
        found = system.leftovers(temp)
    entry: dict = {"seen": seen, "remaining": len(found)}
    if found:
        entry["ended"] = system.end(found, rescan=lambda: system.leftovers(temp))
    record.setdefault("leftovers", {})[after] = entry
    return len(found)


def run_check(out: Path, temp: Path, keep: bool, system: System) -> int:
    """The check, from starting the stack to removing it. Its exit status is EXIT[outcome]; an
    error is recorded and raised once the cleanup has run, and main turns it into exit 3."""
    record: dict = {"format": 2, "started_at_utc": system.now(), "code": system.code_state(), "tools": system.tools(),
                    "budgets": BUDGETS, "conditions": CONDITIONS,
                    "supplementary": {"container": {k: v for k, v in PROPOSED.items() if not k.startswith(NATIVE)},
                                      "native": {k: v for k, v in PROPOSED.items() if k.startswith(NATIVE)},
                                      "native_approved": False},
                    "settle_s": SETTLE_S, "pytest_temp": str(temp), "cleanup_errors": [],
                    "worktree_ignored_untracked": {"under": IGNORED_UNTRACKED, "paths": system.ignored_untracked()}}
    env = {**os.environ, "ETF_RISK_MYSQL_URL": services.DEFAULT_MYSQL_URL,
           "ETF_RISK_KAFKA_BOOTSTRAP": services.DEFAULT_KAFKA_BOOTSTRAP, RUN_ENV: str(temp)}
    errors = record["cleanup_errors"]
    system.keep_awake()

    def docker_states() -> dict:
        return {service: system.docker_state(service) for service in services.SERVICES}

    try:
        # the preflight found none of this project's containers, so down -v follows whatever happens
        record["stack_started_at_utc"] = started = system.now()
        system.compose("up", "-d", "--wait", *services.SERVICES)
        system.ready(env)
        record["docker"] = {"started": docker_states()}
        system.sleep(SETTLE_S)
        record["idle"] = idle = system.host_memory()
        print(f"idle with the stack up: {size(idle['available_bytes'])} available"
              + ("" if idle["available_bytes"] >= CONDITIONS["idle_available"] else
                 f", below {CONDITIONS['idle_available'] / GiB:.1f} GiB: the native-process figures will not be "
                 "representative; the container verdict does not depend on it"))
        sampler, runs, left = system.sampler(out / "samples.jsonl"), {}, {}
        sampler.start()
        try:
            for name, files, extra in RUNS:
                runs[name] = system.run_pytest(name, files, {**env, **extra}, out, temp, TIMEOUTS[name])
                print(f"{name}: {runs[name]}")
                record["docker"][f"after {name}"] = docker_states()
                left[name] = end_leftovers(system, temp, record, name)
        finally:
            sampler.stop()
            sampler.tick(sampler.sample_containers)   # one more reading, after the last run
        record["measured"] = measure(sampler, idle, temp, runs, left, record["docker"], started)
        record["verdict"] = judge(record["measured"])
    except KeyboardInterrupt:
        record["interrupted"] = True
        raise
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        try:
            end_leftovers(system, temp, record, "cleanup")
        except Exception as error:
            errors.append(f"ending leftover processes: {error}")
        try:
            states = docker_states()
        except Exception as error:
            states = f"not read: {error}"
        record.setdefault("docker", {})["before cleanup"] = states
        try:
            system.compose("unpause", *services.SERVICES)   # a pause case cut short leaves one paused
        except Exception as error:
            record["unpause"] = f"not needed or not possible: {error}"
        try:
            system.compose("down", "-v")
        except Exception as error:
            errors.append(f"docker compose down -v: {error}")
        record["ended_at_utc"] = system.now()
        try:
            record["project_containers_after"] = system.project_containers()
        except Exception as error:
            record["project_containers_after"] = None
            errors.append(f"docker compose ps: {error}")
        try:
            keep_records(temp, out / "records")
        except OSError as error:
            errors.append(f"copying the records: {error}")
        if not keep:
            shutil.rmtree(temp, ignore_errors=True)
        record["outcome"] = outcome(record)
        record["exit_code"] = EXIT[record["outcome"]]
        (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        for error in errors:
            print(f"cleanup: {error}", file=sys.stderr)
    if "measured" in record:
        report(record)
    if record["outcome"] == "tool error":
        print("tool error (exit 3): the cleanup did not finish; see record.json and "
              "`docker compose -f docker/compose.yaml ps -a`")
    return record["exit_code"]


def show(criterion: str, value: int | None) -> str:
    return "-" if value is None else str(value) if criterion.endswith("limit hits") else size(value)


def state(result: dict) -> str:
    if result["threshold"] is None:
        return "no threshold"
    return "not measured" if result["value"] is None else "within" if result["within"] else "above"


def conclusion(verdict: dict) -> str:
    pressure = verdict["host_pressure"]
    if not verdict["counts"]:
        return "not counted (exit 2): an invalid run; the reasons are listed above"
    if not verdict["passed"]:
        return (f"failed measurement (exit 1): {len(verdict['container_misses'])} container-limit miss(es) and "
                f"{len(verdict['run_misses'])} test-run miss(es), listed above."
                + (" The host was under memory pressure: diagnose test failures and timeouts before attributing "
                   "them to a container limit." if pressure else ""))
    return ("passed (exit 0): the container limits held, with no oom or oom_kill event and no container stopped, "
            "and both pytest runs passed with nothing left behind. This validates the container limits only: the "
            "native-process targets are not approved budgets, and this run does not validate them."
            + (" Its native-process figures were measured under host memory pressure and are not representative."
               if pressure else ""))


def report(record: dict) -> None:
    m, verdict = record["measured"], record["verdict"]
    print("Container limits, the existing budgets (judged):")
    for limit in verdict["container_limits"]:
        c = m["containers"][limit["container"]]
        print(f"  {limit['container']}: limit {size(limit['limit_bytes'])}; memory.peak {size(limit['peak_bytes'])} "
              f"at most, over {len(c['lifetimes'])} lifetime(s); oom {limit['oom']}, oom_kill {limit['oom_kill']}"
              + "".join(f"; {what}" for what in limit["stopped"]) + (": held" if limit["held"] else ": not held"))
        for n, s in enumerate(c["lifetimes"], 1):
            print(f"    lifetime {n} (cgroup {s['cgroup']}, {s['readings']} readings from {s['from_utc']}): memory.peak "
                  f"{size(s['peak_bytes'])} of {size(s['limit_bytes'])}; anon {size(s['anon_bytes'])}, file "
                  f"{size(s['file_bytes'])}, kernel {size(s['kernel_bytes'])}; events since it began "
                  + ", ".join(f"{name} {count}" for name, count in s["events"].items()))
    print("Supplementary container figures (proposed thresholds, reported only):")
    for r in verdict["supplementary_container"]:
        print(f"  {r['criterion']}: {show(r['criterion'], r['value'])} against "
              f"{show(r['criterion'], r['threshold'])}: {state(r)}")
    print("Native-process targets (proposed, not approved budgets; reported only, and not validated by this run"
          + ("" if verdict["native_targets"]["representative"] else
             "; measured under host memory pressure, not representative") + "):")
    for r in verdict["native_targets"]["results"]:
        sampled = (f" ({m['processes'][r['criterion'].removeprefix('process ')]['processes']} process(es) sampled)"
                   if r["criterion"].startswith("process ") else "")
        print(f"  {r['criterion']}: {show(r['criterion'], r['value'])} against "
              f"{show(r['criterion'], r['threshold'])}: {state(r)}{sampled}")
    for job, steps in sorted(m["jobs"].items()):
        print(f"    {job}: " + ", ".join(f"{step} {size(peak)}" for step, peak in steps.items()))
    h = m["host"]
    print(f"Host and harness (recorded only): {size(h['idle']['available_bytes'])} available idle, "
          f"{size(h['available_min_bytes'])} at the lowest; compressor {h['compressor_growth_bytes'] / MiB:+,.0f} MiB, "
          f"swap {h['swap_growth_bytes'] / MiB:+,.0f} MiB; VM process RSS {size(h['vm_rss_bytes'])}; pytest "
          f"{size(m['processes']['pytest']['rss_bytes'])}; {m['sampler_errors']} sampler errors")
    print("  host memory pressure: " + ("; ".join(verdict["host_pressure"]) or "none (the host conditions held)"))
    for reason in verdict["invalid"]:
        print(f"does not count: {reason}")
    for miss in verdict["container_misses"]:
        print(f"container-limit miss: {miss}")
    for miss in verdict["run_misses"]:
        print(f"test-run miss: {miss}")
    print(conclusion(verdict))


def main(argv: list[str] | None = None, system: System | None = None) -> int:
    system = system or this_machine()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="a new folder for record.json, the samples and the pytest logs")
    parser.add_argument("--preflight", action="store_true", help="only check that the run can start")
    parser.add_argument("--keep", action="store_true", help="keep pytest's temporary folders with the runs' outputs")
    args = parser.parse_args(argv)
    if not args.preflight and args.out is None:
        parser.error("--out is required, unless --preflight")
    problems = preflight(system)
    print(f"available now: {size(system.available())}; representative native-process figures need "
          f"{CONDITIONS['idle_available'] / GiB:.1f} GiB with the stack up and idle (the container verdict does not)")
    for problem in problems:
        print(f"not ready: {problem}")
    if problems:
        print("not counted (exit 2): not started")
        return EXIT["not counted"]
    if args.preflight:
        return 0
    args.out.mkdir(parents=True)   # a new folder, so no record is overwritten
    temp = Path(tempfile.mkdtemp(prefix="etf-risk-memory-")).resolve()
    try:
        return run_check(args.out, temp, args.keep, system)
    except Exception as error:
        print(f"tool error (exit 3): the check stopped: {type(error).__name__}: {error}", file=sys.stderr)
        return EXIT["tool error"]


if __name__ == "__main__":
    sys.exit(main())
