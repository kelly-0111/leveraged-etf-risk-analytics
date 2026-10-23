"""Stand-ins for the offline tests: a manual clock, a simulated pipeline and a simulated crash.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from etf_risk.jobs.store import Claim
from etf_risk.jobs.worker import Fenced, PipelineError


class SimulatedCrash(BaseException):
    """The worker process dies here. Nothing in the worker catches it as an error (it is a
    BaseException, like KeyboardInterrupt), so nothing more is written; an open transaction
    rolls back, as it would when a dead process's connection closes."""


class ManualClock:
    """A UTC clock that moves only when told to."""

    def __init__(self, start: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc)):
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += timedelta(seconds=seconds)


def result_digest(params: dict) -> str:
    """The simulated analysis result: the same for every attempt of a job."""
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()


class SimulatedPipeline:
    """Stands in for windows -> spark_pipeline -> verify.

    Each of `steps` steps calls on_step(step, claim) if given, then the heartbeat (raising
    Fenced once it returns False), then fails if fail_at names the step (it maps a step to
    whether that failure is retryable), then appends a line to steps.log in the run folder.
    After the last step it writes result.json: the attempt that wrote it and the job's
    result digest. on_step lets a test step the clock or run another worker in the middle
    of this run. runs lists the run ids of the executions this pipeline started."""

    def __init__(self, steps: int = 3, *, fail_at: dict[int, bool] | None = None,
                 on_step: Callable[[int, Claim], None] | None = None):
        self.steps = steps
        self.fail_at = fail_at or {}
        self.on_step = on_step
        self.runs: list[str] = []

    def run(self, claim: Claim, run_dir: Path, heartbeat: Callable[[], bool]) -> None:
        self.runs.append(claim.run_id)
        for step in range(1, self.steps + 1):
            if self.on_step is not None:
                self.on_step(step, claim)
            if not heartbeat():
                raise Fenced(f"{claim.run_id}: fenced off before step {step}")
            if step in self.fail_at:
                raise PipelineError(f"injected failure at step {step}", retryable=self.fail_at[step])
            with (run_dir / "steps.log").open("a") as log:
                log.write(f"step {step}\n")
        (run_dir / "result.json").write_text(json.dumps(
            {"job_id": claim.job_id, "attempt_number": claim.attempt_number, "run_id": claim.run_id,
             "result_sha256": result_digest(claim.params)}, sort_keys=True))
