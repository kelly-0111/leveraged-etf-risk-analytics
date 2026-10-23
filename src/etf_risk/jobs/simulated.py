"""Stand-ins for the offline tests: a manual clock, a simulated pipeline, a simulated crash
and an in-memory queue.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py
and tests/test_jobs_queue.py.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path

from etf_risk.jobs.queue import Delivery, encode
from etf_risk.jobs.store import Claim
from etf_risk.jobs.worker import Fenced, PipelineError
from etf_risk.runs import folder_digest


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
    result digest. It returns the run folder's digest (etf_risk.runs), which acceptance
    records. on_step lets a test step the clock or run another worker in the middle of this
    run. runs lists the run ids of the executions this pipeline started."""

    def __init__(self, steps: int = 3, *, fail_at: dict[int, bool] | None = None,
                 on_step: Callable[[int, Claim], None] | None = None):
        self.steps = steps
        self.fail_at = fail_at or {}
        self.on_step = on_step
        self.runs: list[str] = []

    def run(self, claim: Claim, run_dir: Path, heartbeat: Callable[[], bool]) -> str:
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
        return folder_digest(run_dir)


class PublishOutcome(StrEnum):
    CONFIRMED = "confirmed"        # written, and the confirmation arrived
    UNCONFIRMED = "unconfirmed"    # written, but the confirmation was lost
    DROPPED = "dropped"            # not written


class MemoryQueue:
    """One topic with one partition, in memory: the Kafka behaviour the job system relies on.

    Messages keep their order. Each consumer group has a committed offset. A consumer starts
    at its group's committed offset, or at the earliest message for a group that never
    committed (auto.offset.reset=earliest), and moves on as it polls, whether it commits or
    not; a new consumer of the group stands in for a restarted worker."""

    def __init__(self) -> None:
        self.messages: list[bytes] = []
        self.committed: dict[str, int] = {}

    def publisher(self, outcomes: Iterable[PublishOutcome] = ()) -> MemoryPublisher:
        """A publisher whose publications end as `outcomes` says, one by one, then confirmed."""
        return MemoryPublisher(self, outcomes)

    def consumer(self, group: str, *, failing_commits: int = 0) -> MemoryConsumer:
        """A consumer of the group; its first `failing_commits` commits raise."""
        return MemoryConsumer(self, group, failing_commits)

    def job_ids(self) -> list[int | None]:
        return [Delivery(value, offset).job_id() for offset, value in enumerate(self.messages)]


class MemoryPublisher:
    def __init__(self, queue: MemoryQueue, outcomes: Iterable[PublishOutcome]):
        self.queue = queue
        self._outcomes = iter(outcomes)

    def publish(self, job_id: int) -> bool:
        outcome = next(self._outcomes, PublishOutcome.CONFIRMED)
        if outcome is not PublishOutcome.DROPPED:
            self.queue.messages.append(encode(job_id))
        return outcome is PublishOutcome.CONFIRMED


class MemoryConsumer:
    def __init__(self, queue: MemoryQueue, group: str, failing_commits: int):
        self.queue, self.group = queue, group
        self.position = queue.committed.get(group, 0)
        self._failing_commits = failing_commits

    def poll(self, timeout: float = 0.0) -> Delivery | None:
        if self.position >= len(self.queue.messages):
            return None
        delivery = Delivery(self.queue.messages[self.position], self.position)
        self.position += 1
        return delivery

    def commit(self, delivery: Delivery) -> None:
        if self._failing_commits:
            self._failing_commits -= 1
            raise ConnectionError(f"the commit of offset {delivery.position} failed (simulated)")
        self.queue.committed[self.group] = delivery.position + 1

    def rewind(self, delivery: Delivery) -> None:
        self.position = delivery.position

    def close(self) -> None:
        pass
