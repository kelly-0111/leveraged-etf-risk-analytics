"""Finding and ending the processes of a pipeline attempt (spec §11; docs/job-queue.md).

Membership:
- Every process of an attempt carries ETF_RISK_ATTEMPT=<store id>:<run id>:<attempt key> in
  its environment. The attempt key is the first 16 hex digits of SHA-256(token), so the
  token itself, which can change the job's row, never leaves the worker.
- Each step runs under a launcher that leads a session of its own, and nothing below it
  calls setsid. So every process of the step stays in that session. That includes PySpark's
  daemon, which moves itself and its Python workers to a process group of their own
  (pyspark/daemon.py: os.setpgid(0, 0)), and an orphan that launchd adopted. A process-group
  kill would miss the daemon; the session does not.
- The session id is the cheap first filter (os.getsid works for any process on macOS), and
  the marker confirms it, so a reused pid never counts. A process whose environment cannot
  be read is not counted: it is not this user's.

terminate():
1. sends SIGTERM to every process given, so the JVM's shutdown hooks can delete its scratch;
2. waits term_grace, then sends SIGKILL to whatever is left;
3. scans again, if given a way to, until nothing is left or kill_confirm has passed.
A process started meanwhile is found by the rescan.

The registry is a folder next to the host lock, with one file per launcher whose step may
have processes running: its pid, session, marker and start time. A launcher removes its file
once its tree is gone. A file left by a launcher that was killed is found by the next
launcher's survivor check. That check also finds the dead launcher's orphans, through their
session. The file is removed once nothing of that tree is left.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_processes.py
and tests/test_jobs_launcher.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import signal
import time
from collections.abc import Callable, Iterable
from pathlib import Path

import psutil

MARKER_ENV = "ETF_RISK_ATTEMPT"


def attempt_key(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()[:16]


def marker(store_id: str, run_id: str, token: str) -> str:
    return f"{store_id}:{run_id}:{attempt_key(token)}"


def parse_marker(value: str | None) -> tuple[str, str, str] | None:
    """(store id, run id, attempt key), or None for a value that is not a marker."""
    parts = (value or "").split(":")
    return tuple(parts) if len(parts) == 3 and all(parts) else None


def marker_of(process: psutil.Process) -> str | None:
    try:
        return process.environ().get(MARKER_ENV)
    except (psutil.Error, OSError):
        return None


def session_members(sid: int, *, exclude: Iterable[int] = ()) -> list[psutil.Process]:
    """The live processes whose session id is sid."""
    skip, found = set(exclude), []
    for pid in psutil.pids():
        if pid in skip or pid == 0:
            continue
        try:
            if os.getsid(pid) == sid:
                found.append(psutil.Process(pid))
        except (OSError, psutil.Error):
            continue
    return found


def attempt_members(sid: int, attempt_marker: str, *, exclude: Iterable[int] = ()) -> list[psutil.Process]:
    """The processes of one launcher's tree: in its session and carrying the attempt's marker."""
    return [p for p in session_members(sid, exclude=exclude) if marker_of(p) == attempt_marker]


def marked_processes() -> dict[str, list[psutil.Process]]:
    """Every process of this user that carries a marker, by marker (a full scan: slower)."""
    me, found = os.getuid(), {}
    for process in psutil.process_iter():
        try:
            if process.uids().real != me:
                continue
        except psutil.Error:
            continue
        value = marker_of(process)
        if parse_marker(value) is not None:
            found.setdefault(value, []).append(process)
    return found


def alive(processes: Iterable[psutil.Process]) -> list[psutil.Process]:
    live = []
    for p in processes:
        try:
            if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
                live.append(p)
        except psutil.Error:
            continue
    return live


def rss(processes: Iterable[psutil.Process]) -> int:
    """Summed resident memory of the live processes given."""
    total = 0
    for p in processes:
        try:
            total += p.memory_info().rss
        except psutil.Error:
            continue
    return total


def _signal(processes: Iterable[psutil.Process], sig: int) -> list[int]:
    sent = []
    for p in processes:
        try:
            p.send_signal(sig)
            sent.append(p.pid)
        except psutil.Error:
            continue
    return sent


def terminate(processes: list[psutil.Process], *, term_grace: float, kill_confirm: float,
              rescan: Callable[[], list[psutil.Process]] | None = None) -> dict:
    """End the processes and, with rescan, any new member it finds; what was done, by pid."""
    record = {"terminated": _signal(processes, signal.SIGTERM), "killed": [], "remaining": []}
    _, left = psutil.wait_procs(processes, timeout=term_grace)
    record["killed"] += _signal(left, signal.SIGKILL)
    deadline = time.monotonic() + kill_confirm
    psutil.wait_procs(left, timeout=kill_confirm)
    while rescan is not None and time.monotonic() < deadline:
        new = alive(rescan())
        if not new:
            break
        record["killed"] += _signal(new, signal.SIGKILL)
        psutil.wait_procs(new, timeout=max(0.0, min(0.5, deadline - time.monotonic())))
    record["remaining"] = [p.pid for p in alive(rescan() if rescan is not None else processes)]
    return record


class Registry:
    """The launchers whose trees may still have processes (see the module docstring)."""

    def __init__(self, folder: str | Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)

    def _path(self, pid: int) -> Path:
        return self.folder / f"launcher-{pid}.json"

    def register(self, attempt_marker: str) -> None:
        me = psutil.Process()
        entry = {"pid": me.pid, "sid": os.getsid(0), "marker": attempt_marker, "started": me.create_time()}
        tmp = self._path(me.pid).with_suffix(".tmp")
        tmp.write_text(json.dumps(entry))
        tmp.replace(self._path(me.pid))

    def unregister(self) -> None:
        self._path(os.getpid()).unlink(missing_ok=True)

    def entries(self) -> list[dict]:
        found = []
        for path in sorted(self.folder.glob("launcher-*.json")):
            try:
                found.append({**json.loads(path.read_text()), "path": str(path)})
            except (OSError, json.JSONDecodeError):
                continue
        return found

    def survivors(self) -> list[psutil.Process]:
        """Live processes of other launchers' trees. Entries whose trees are gone are removed."""
        found = []
        for entry in self.entries():
            if entry["pid"] == os.getpid():
                continue
            members = attempt_members(entry["sid"], entry["marker"], exclude=[os.getpid()])
            if members:
                found += members
            else:
                Path(entry["path"]).unlink(missing_ok=True)
        return found
