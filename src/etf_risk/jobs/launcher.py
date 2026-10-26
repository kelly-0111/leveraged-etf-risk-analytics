"""The watchdog that runs one pipeline step for the worker (spec §11; docs/job-queue.md).

    python -m etf_risk.jobs.launcher --marker M --lock PATH --registry DIR --lock-wait S \\
        --step-limit S --cwd DIR --step-log PATH --result PATH -- <command ...>

The worker starts it with start_new_session=True, so the launcher leads a session that holds
the whole step (etf_risk.jobs.processes), with an environment the worker prepared (including
the attempt's marker), and with a pipe as stdin.

The worker writes one JSON line per message:
- first the handshake {"monotonic": t, "seq": 0, "deadline": F}, where t is the worker's
  time.monotonic() when it wrote the line;
- then {"seq": n, "deadline": F_n} after each successful renewal of the lease.
Deadlines are absolute values of the host's monotonic clock, never durations.

The launcher refuses to start in three cases:
- no handshake: none arrived within 5 s;
- clock_mismatch: its own reading is not between t and t + 30 s, so the two processes do not
  read the same clock. A different clock source differs by far more. The 30 s allow for a
  launcher that starts slowly on a busy machine; the deadlines stay absolute either way;
- deadline_passed: F has passed.

Every tick (--tick, 0.5 s) the launcher does, in this order:
1. if its deadline has passed, it fires: it ends the tree, and firing is terminal;
2. only otherwise does it read the lines waiting on stdin. A line moves the deadline only if
   its sequence number is newer, its deadline is later than the current one, and that
   deadline is still in the future.
So lines that queued up while the launcher was stopped can never revive an expired watchdog,
and no line can push the deadline past what the worker granted. EOF (the worker closed the
pipe, or died) ends the tree too, and so does the step's time limit, or a SIGTERM to the
launcher itself.

Before the step starts, the launcher takes an exclusive flock on the host's execution lock,
waiting up to --lock-wait. It then waits, within the same bound, until no process of another
launcher's tree survives (the registry). While it waits it keeps reading deadlines and fires
if its own passes. Only then does it register and start the step. The step's driver
inherits the lock's descriptor, so the lock is held while the launcher or the driver lives.
PySpark closes inherited descriptors before it starts the JVM, so the JVM does not hold the
lock; it exits when the driver's pipe breaks, and the next launcher's survivor check covers
that window.

Ending the tree: SIGTERM to every process of the session that carries the marker, SIGKILL
after --term-grace, and a rescan until none is left or --kill-confirm has passed. When the
step ends by itself, the launcher first gives the rest of its tree --drain seconds to exit.

The result goes to --result as JSON: the outcome, the step's exit code, the processes ended,
the time waited for the lock, the tree's peak summed RSS, and the lines accepted and
ignored. A step that started also has its interval, from just after the step's process
started to when no member of the tree was left: step_started_mono and tree_ended_mono, on
the host's monotonic clock, which the handshake checked and which same-host overlap checks
compare, and the same moments in UTC (*_at_utc), for reading only. The exit code says the
outcome: the step's own code (0-63) when it ran to its end, otherwise one of EXIT_CODES.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_launcher.py.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import select
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from etf_risk.jobs import processes

EXIT_CODES = {"deadline": 64, "eof": 65, "timeout": 66, "lock_busy": 67, "clock_mismatch": 68,
              "deadline_passed": 69, "signaled": 70, "launch_failed": 71, "no_handshake": 72, "terminated": 73}
HANDSHAKE_TIMEOUT = 5.0
CLOCK_TOLERANCE = 30.0     # seconds a launcher may take to read the handshake; never a reading from the future


class Watchdog:
    """The deadline: absolute, on the monotonic clock, moved only by newer, later, future
    lines; once fired it stays fired."""

    def __init__(self, deadline: float, seq: int):
        self.deadline, self.seq = float(deadline), seq
        self.fired = False
        self.accepted = self.ignored = 0

    def expired(self, now: float) -> bool:
        if not self.fired and now >= self.deadline:
            self.fired = True
        return self.fired

    def offer(self, line: dict, now: float) -> bool:
        seq, deadline = line.get("seq"), line.get("deadline")
        if (self.fired or not isinstance(seq, int) or not isinstance(deadline, (int, float)) or seq <= self.seq
                or deadline <= self.deadline or deadline <= now):
            self.ignored += 1
            return False
        self.seq, self.deadline = seq, float(deadline)
        self.accepted += 1
        return True


class Lines:
    """The worker's lines on a non-blocking stdin."""

    def __init__(self, fd: int):
        self.fd, self.buffer, self.eof = fd, b"", False
        os.set_blocking(fd, False)

    def read(self) -> list[dict]:
        while not self.eof:
            try:
                chunk = os.read(self.fd, 65536)
            except BlockingIOError:
                break
            if not chunk:
                self.eof = True
            self.buffer += chunk
        *complete, self.buffer = self.buffer.split(b"\n")
        lines = []
        for raw in complete:
            try:
                value = json.loads(raw)
            except ValueError:
                continue
            if isinstance(value, dict):
                lines.append(value)
        return lines

    def wait(self, timeout: float) -> None:
        if not self.eof and timeout > 0:
            select.select([self.fd], [], [], timeout)


class Launcher:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.result: dict = {"outcome": None, "returncode": None, "pid": os.getpid(),
                             "started_at_utc": datetime.now(timezone.utc).isoformat(), "lock_wait_s": None,
                             "peak_rss_bytes": 0, "ended": None, "lingering": None}
        self.lines = Lines(sys.stdin.fileno())
        self.watchdog: Watchdog | None = None
        self.stop_requested = False
        self.registry = processes.Registry(args.registry)
        self.lock_fd: int | None = None

    def members(self) -> list:
        return processes.attempt_members(os.getpid(), self.args.marker, exclude=[os.getpid()])

    def poll(self) -> str | None:
        """One check of the watchdog, in the documented order; the reason to stop, if any."""
        now = time.monotonic()
        if self.watchdog.expired(now):
            for line in self.lines.read():              # read only to record them: a fired watchdog ignores all
                self.watchdog.offer(line, now)
            return "deadline"
        for line in self.lines.read():
            self.watchdog.offer(line, now)
        if self.lines.eof:
            return "eof"
        if self.stop_requested:
            return "terminated"
        return None

    def handshake(self) -> str | None:
        deadline = time.monotonic() + HANDSHAKE_TIMEOUT
        while time.monotonic() < deadline:
            lines = self.lines.read()
            if lines:
                first, now = lines[0], time.monotonic()
                if not isinstance(first.get("monotonic"), (int, float)) or not isinstance(first.get("deadline"), (int, float)):
                    return "no_handshake"
                if not (first["monotonic"] <= now <= first["monotonic"] + CLOCK_TOLERANCE):
                    self.result["clock"] = {"worker": first["monotonic"], "launcher": now}
                    return "clock_mismatch"
                self.watchdog = Watchdog(first["deadline"], int(first.get("seq", 0)))
                if self.watchdog.expired(now):
                    return "deadline_passed"
                for line in lines[1:]:                       # lines that came with the handshake
                    self.watchdog.offer(line, now)
                return None
            if self.lines.eof:
                return "no_handshake"
            self.lines.wait(0.1)
        return "no_handshake"

    def acquire(self) -> str | None:
        """The host lock, then no survivors of other trees; waiting within --lock-wait."""
        start = time.monotonic()
        Path(self.args.lock).parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.args.lock, os.O_RDWR | os.O_CREAT, 0o600)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                pass
            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
                os.close(fd)
                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
                return reason or "lock_busy"
            self.lines.wait(self.args.tick)
        self.lock_fd = fd
        while survivors := self.registry.survivors():
            self.result["survivors_seen"] = sorted({p.pid for p in survivors})
            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
                return reason or "lock_busy"
            self.lines.wait(self.args.tick)
        self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
        return None

    def end_tree(self, reason: str) -> None:
        self.result["ended"] = {"reason": reason, **processes.terminate(
            self.members(), term_grace=self.args.term_grace, kill_confirm=self.args.kill_confirm,
            rescan=self.members)}

    def drain(self) -> None:
        """The step ended by itself: give the rest of its tree time to exit, then end it."""
        deadline = time.monotonic() + self.args.drain
        while (left := processes.alive(self.members())) and time.monotonic() < deadline:
            time.sleep(0.1)
        if left := processes.alive(self.members()):
            self.result["lingering"] = sorted(p.pid for p in left)
            self.end_tree("lingering after the step ended")

    def run(self, command: list[str]) -> int:
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "stop_requested", True))
        outcome = self.handshake() or self.acquire()
        child = None
        if outcome is None:
            self.registry.register(self.args.marker)
            Path(self.args.step_log).parent.mkdir(parents=True, exist_ok=True)
            os.set_inheritable(self.lock_fd, True)
            try:
                with open(self.args.step_log, "ab") as log:
                    child = subprocess.Popen(command, cwd=self.args.cwd, stdin=subprocess.DEVNULL, stdout=log,
                                             stderr=subprocess.STDOUT, pass_fds=(self.lock_fd,))
                self.result["step_started_mono"] = time.monotonic()
                self.result["step_started_at_utc"] = datetime.now(timezone.utc).isoformat()
            except OSError as error:
                self.result["error"] = f"{type(error).__name__}: {error}"
                outcome = "launch_failed"
        if child is not None:
            started = time.monotonic()
            while outcome is None:
                outcome = self.poll()
                if outcome is None and child.poll() is not None:
                    outcome = "exited"
                elif outcome is None and time.monotonic() - started >= self.args.step_limit:
                    outcome = "timeout"
                if outcome is None:
                    self.result["peak_rss_bytes"] = max(self.result["peak_rss_bytes"], processes.rss(self.members()))
                    self.lines.wait(self.args.tick)
            self.result["step_seconds"] = round(time.monotonic() - started, 3)
            if outcome == "exited":
                self.drain()
            else:
                self.end_tree(outcome)
            child.wait()
            self.result["returncode"] = child.returncode
            self.result["tree_ended_mono"] = time.monotonic()                          # no member left
            self.result["tree_ended_at_utc"] = datetime.now(timezone.utc).isoformat()
            if outcome == "exited" and child.returncode < 0:
                outcome = "signaled"
        self.registry.unregister()
        if self.lock_fd is not None:
            os.close(self.lock_fd)                      # the driver's copy is closed with the driver
        if self.watchdog is not None:
            self.result.update(deadline=self.watchdog.deadline, lines_accepted=self.watchdog.accepted,
                               lines_ignored=self.watchdog.ignored)
        self.result.update(outcome=outcome, finished_at_utc=datetime.now(timezone.utc).isoformat())
        tmp = Path(self.args.result).with_suffix(".tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(self.result, indent=2) + "\n")
        tmp.replace(self.args.result)
        if outcome == "exited":
            return child.returncode if 0 <= child.returncode < 64 else EXIT_CODES["signaled"]
        return EXIT_CODES[outcome]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--" not in argv:
        print("usage: python -m etf_risk.jobs.launcher [options] -- <command ...>", file=sys.stderr)
        return 2
    split = argv.index("--")
    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs.launcher")
    parser.add_argument("--marker", required=True)
    parser.add_argument("--lock", required=True, help="the host's execution lock file")
    parser.add_argument("--registry", required=True, help="the folder of launchers whose trees may still run")
    parser.add_argument("--lock-wait", type=float, required=True)
    parser.add_argument("--step-limit", type=float, required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--step-log", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--tick", type=float, default=0.5)
    parser.add_argument("--term-grace", type=float, default=5.0)
    parser.add_argument("--kill-confirm", type=float, default=2.0)
    parser.add_argument("--drain", type=float, default=10.0)
    args = parser.parse_args(argv[:split])
    command = argv[split + 1:]
    if not command:
        parser.error("no command after --")
    if processes.parse_marker(args.marker) is None or os.environ.get(processes.MARKER_ENV) != args.marker:
        parser.error("--marker must be a marker and equal ETF_RISK_ATTEMPT in the environment")
    if os.getsid(0) != os.getpid():
        parser.error("start the launcher as the leader of a new session (start_new_session=True):"
                     " its session is how it finds the step's processes")
    return Launcher(args).run(command)


if __name__ == "__main__":
    sys.exit(main())
