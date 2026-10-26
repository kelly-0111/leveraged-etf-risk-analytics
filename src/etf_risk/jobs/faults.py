"""Faults armed at the worker's fault points, for the recovery experiments
(docs/recovery-experiments.md, 3.1 and 8.4).

A worker started with ETF_RISK_FAULT_FILE=<path> looks at that path at each of
WORKER_FAULT_POINTS (etf_risk.jobs.worker); while nothing is there, nothing happens. The
session harness (etf_risk.jobs.harness) arms one fault by writing the file, atomically
(a temporary file, then a rename), as one JSON object:

    {"point": "after_claim", "action": "kill"}
    {"point": "after_pipeline", "action": "hold", "release": "/abs/path", "timeout_s": 300}

When the worker reaches that point, it first removes the file, so a fault fires once, then
writes a fault_injected event (point, action) and:
- kill: sends SIGKILL to its own process, which ends at once, as in a crash. The event's
  mono is the injection time;
- hold: waits until the release path exists, or timeout_s has passed, then writes
  fault_released (with why) and goes on.
A file that names another point is left for that point. A file that cannot be parsed, or
that names an unknown point or action, is removed and reported as fault_refused, and the
worker goes on: an arming that went wrong must not turn into a fault nobody asked for.

Without the variable the worker has no fault hook at all.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
Tested with tests/test_jobs_faults.py.
"""
from __future__ import annotations

import json
import os
import signal
import time
from collections.abc import Callable
from pathlib import Path

from etf_risk.jobs.events import EventLog

FAULT_FILE_ENV = "ETF_RISK_FAULT_FILE"
ACTIONS = ("kill", "hold")


def _kill_self() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


class FaultFile:
    """The worker's fault hook: Worker(fault=FaultFile(path, events))."""

    def __init__(self, path: str | Path, events: EventLog, *, points: tuple[str, ...] | None = None,
                 kill: Callable[[], None] = _kill_self, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, tick: float = 0.1):
        if points is None:
            from etf_risk.jobs.worker import WORKER_FAULT_POINTS
            points = WORKER_FAULT_POINTS
        self.path, self.events, self.points = Path(path), events, points
        self._kill, self._sleep, self._clock, self._tick = kill, sleep, clock, tick

    def __call__(self, point: str) -> None:
        try:
            text = self.path.read_text()
        except FileNotFoundError:
            return
        except OSError as error:
            self.events.log("fault_refused", point=point, error=f"{type(error).__name__}: {error}")
            return
        try:
            spec = json.loads(text)
            armed, action = spec["point"], spec["action"]
            if armed not in self.points or action not in ACTIONS:
                raise ValueError(f"unknown point {armed!r} or action {action!r}")
            if action == "hold" and not spec.get("release"):
                raise ValueError("a hold needs a release path")
        except (ValueError, KeyError, TypeError) as error:
            self.path.unlink(missing_ok=True)
            self.events.log("fault_refused", point=point, error=f"{type(error).__name__}: {error}")
            return
        if armed != point:
            return
        self.path.unlink(missing_ok=True)                    # once: gone before it acts
        self.events.log("fault_injected", point=point, action=action)
        if action == "kill":
            self._kill()
            return                                           # reached only when kill is replaced (tests)
        release, timeout = Path(spec["release"]), spec.get("timeout_s")
        end = None if timeout is None else self._clock() + float(timeout)
        while not release.exists():
            if end is not None and self._clock() >= end:
                self.events.log("fault_released", point=point, why="timeout")
                return
            self._sleep(self._tick)
        self.events.log("fault_released", point=point, why="released")


def fault_from_environment(events: EventLog) -> FaultFile | None:
    """The hook for the worker command: a FaultFile when ETF_RISK_FAULT_FILE is set, else None."""
    path = os.environ.get(FAULT_FILE_ENV)
    return FaultFile(path, events) if path else None


def arm(path: str | Path, point: str, action: str = "kill", *, release: str | Path | None = None,
        timeout_s: float | None = None) -> None:
    """Write a fault for FaultFile to find (the harness's side), atomically."""
    spec = {"point": point, "action": action}
    if release is not None:
        spec["release"] = str(release)
    if timeout_s is not None:
        spec["timeout_s"] = timeout_s
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(spec))
    tmp.replace(path)
