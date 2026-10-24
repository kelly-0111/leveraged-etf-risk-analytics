"""A worker that handles one delivered job id at a time, fenced by its attempt token.

Worker.handle(job_id, acknowledge) handles one delivery:
1. claim the job (JobStore.claim);
2. acknowledge the delivery (with Kafka: commit its offset), at once if the claim was
   refused, since the job needs nothing more, or after a successful claim and before the
   run; a worker that dies before acknowledging gets the job delivered again (spec §11);
3. run the pipeline in the attempt's own new folder, <output root>/<run id>, renewing the
   lease whenever the pipeline calls its heartbeat;
4. accept the result with the run digest the pipeline returns (etf_risk.runs), or record the
   failure.
A worker whose renewal, acceptance or failure write is refused has been fenced off: it
stops and writes nothing more. Its folder stays on disk and is never referenced. After a
lost database connection, acceptance and the failure write are tried again while the
pipeline's own deadline (fence_at) is ahead, if it keeps one; no try starts at or after it,
and both are safe to repeat (store.py). If the deadline passed before the first acceptance
call, the worker makes none: it fences itself (event fenced, during acceptance). An
acceptance transaction that started before the deadline may still commit after it.
Correctness rests on the attempt's token in the job table, which guards that write as it
guards every other, not on the deadline.
Events (claimed, refused, accepted, fenced, failed, requeued, ...) go to an EventLog.

Worker.serve(consumer) polls deliveries and hands each to handle(), acknowledging with a
synchronous commit of the message's offset. A message that carries no valid job id (as
queue.Delivery.job_id() reads it) is committed and skipped before anything touches the
database, so it cannot block the partition or stop the worker. An error before the acknowledgement rewinds the
consumer to the message and tries again after a delay, since an uncommitted message reaches
the same consumer again only that way. After DELIVERY_RETRIES such tries in a row, the next
error is raised and ends serve(). The message stays uncommitted and the consumer rewound, so
it is read again; it is never skipped, because its job may have a recorded publication, which
the reconciler does not publish again. An error after the acknowledgement is logged and left
to the lease. A commit that fails is logged and the job goes on: it is claimed, so a later
delivery of the same message is refused.

Retries after acknowledgement. Once a delivery is acknowledged, no delivery is pending for
the job. A job that fail_attempt() returned to queued, and a running job whose worker died
after acknowledging, run again only when a new delivery arrives: the reconciler publishes
them (etf_risk.jobs.reconciler).

Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash
there to model the worker process dying, and the worker command arms one through
etf_risk.jobs.faults for the recovery experiments. after_accept_commit lies between the
acceptance's commit and its accepted event: a crash there leaves an accepted result that
the event log does not show.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py,
tests/test_jobs_queue.py and tests/test_jobs_kafka.py, on SQLite and on MySQL 8.4.13; the
acceptance-deadline check and after_accept_commit (2026-10-24) so far on SQLite only.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from etf_risk.jobs.events import NO_EVENTS, EventLog
from etf_risk.jobs.queue import Consumer, Delivery
from etf_risk.jobs.store import Claim, JobStore, Refusal, Status

log = logging.getLogger(__name__)

WORKER_FAULT_POINTS = (
    "before_claim",
    "after_claim",       # claimed, not yet acknowledged
    "after_pipeline",    # outputs written, result not yet accepted
    "after_accept_commit",   # accepted in the table, the accepted event not yet written
    "after_accept",
)
DELIVERY_RETRIES = 5    # tries again of one message after errors before its acknowledgement, then raise


class Fenced(Exception):
    """The attempt's token no longer holds the job: another attempt took it over, or it ended."""


class PipelineError(Exception):
    """The pipeline failed; retryable=False when running it again cannot help."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class Heartbeat:
    """heartbeat() renews the attempt's lease (JobStore.renew): False once the attempt has
    been fenced off. claimed_mono is the worker's time.monotonic() just before the claim;
    the lease cannot have started earlier, which gives a pipeline its first deadline."""

    def __init__(self, store: JobStore, claim: Claim, claimed_mono: float):
        self.store, self.claim, self.claimed_mono = store, claim, claimed_mono

    def __call__(self) -> bool:
        return self.store.renew(self.claim)


class Pipeline(Protocol):
    def run(self, claim: Claim, run_dir: Path, heartbeat: Heartbeat) -> str:
        """Write the attempt's outputs into run_dir, a new empty folder, and return the run
        digest of its result (etf_risk.runs), which acceptance records.

        Call heartbeat() more often than the lease lasts. It renews the lease and returns
        False once the attempt has been fenced off: then stop at once and raise Fenced.
        Raise PipelineError when the run fails."""


class Result(StrEnum):
    ACCEPTED = "accepted"    # this delivery's attempt produced the job's accepted result
    SKIPPED = "skipped"      # the claim was refused: the job needed nothing (see reason)
    REQUEUED = "requeued"    # the attempt failed and the job is queued again, not delivered again
    FAILED = "failed"        # the attempt failed and so did the job
    FENCED = "fenced"        # another attempt holds the job, or it ended; this one wrote nothing more


@dataclass(frozen=True)
class Handled:
    job_id: int
    result: Result
    reason: Refusal | None = None    # when skipped
    claim: Claim | None = None       # when an attempt started


@dataclass
class Served:
    """What Worker.serve() did with the deliveries it polled."""
    handled: int = 0              # handle() returned, whatever its result
    malformed: int = 0            # no valid job id: committed and skipped
    rewound: int = 0              # failed before the acknowledgement: read again (within the retries)
    failed_after_ack: int = 0     # failed after it: left to the lease and the reconciler
    commit_failures: int = 0      # commits that raised; the job went on


class Worker:
    def __init__(self, store: JobStore, pipeline: Pipeline, output_root: str | Path, *,
                 worker_id: str | None = None, fault: Callable[[str], None] | None = None,
                 events: EventLog = NO_EVENTS, sleep: Callable[[float], None] = time.sleep):
        self.store = store
        self.pipeline = pipeline
        self.output_root = Path(output_root)
        self.worker_id = worker_id or f"worker-{os.getpid()}-{secrets.token_hex(3)}"
        self._fault = fault or (lambda point: None)
        self.events = events
        self._sleep = sleep

    def handle(self, job_id: int, acknowledge: Callable[[], None]) -> Handled:
        self._fault("before_claim")
        claimed_mono = time.monotonic()
        claim = self.store.claim(job_id, self.worker_id, self.output_root)
        if isinstance(claim, Refusal):
            self.events.log("refused", job_id=job_id, reason=claim.value)
            acknowledge()
            return Handled(job_id, Result.SKIPPED, reason=claim)
        self.events.log("claimed", job_id=job_id, attempt=claim.attempt_number, run_id=claim.run_id)
        self._fault("after_claim")
        acknowledge()
        try:
            claim.output_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            # Run ids are unique within one job table, so this folder comes from elsewhere,
            # for example a job table created anew: never write into it.
            return self._failed(claim, f"output folder already exists: {claim.output_dir}", retryable=False)
        except OSError as error:
            return self._failed(claim, f"cannot create the output folder: {error}", retryable=True)
        try:
            digest = self.pipeline.run(claim, claim.output_dir, Heartbeat(self.store, claim, claimed_mono))
        except Fenced as fenced:
            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="pipeline", why=str(fenced))
            return Handled(job_id, Result.FENCED, claim=claim)
        except PipelineError as error:
            return self._failed(claim, str(error), retryable=error.retryable)
        except Exception as error:
            # Not a failure the pipeline reported: recorded with its type, and retried like one.
            return self._failed(claim, f"{type(error).__name__}: {error}", retryable=True)
        self._fault("after_pipeline")
        deadline = getattr(self.pipeline, "fence_at", None)
        if deadline is not None and time.monotonic() >= deadline:
            # Never an acceptance call after F (docs/worker-pipeline.md), even while the token holds.
            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="acceptance",
                            why=f"{claim.run_id}: the deadline passed before acceptance")
            return Handled(job_id, Result.FENCED, claim=claim)
        if not self._until_deadline(lambda: self.store.accept_result(claim, digest), claim, "accept_result"):
            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="accept_result")
            return Handled(job_id, Result.FENCED, claim=claim)
        self._fault("after_accept_commit")
        self.events.log("accepted", job_id=job_id, attempt=claim.attempt_number, digest=digest)
        self._fault("after_accept")
        return Handled(job_id, Result.ACCEPTED, claim=claim)

    def _until_deadline(self, operation: Callable[[], Any], claim: Claim, name: str) -> Any:
        """operation(), tried again after a lost connection while the pipeline's deadline
        (fence_at, time.monotonic()) has not passed; no try starts at or after it, so one that
        passes during the wait ends the retries. Any other error, or no deadline, raises."""
        while True:
            try:
                return operation()
            except Exception as error:
                deadline = getattr(self.pipeline, "fence_at", None)
                if deadline is None or time.monotonic() >= deadline or not self.store.dialect.is_disconnect(error):
                    raise
                self.events.log("retry", job_id=claim.job_id, attempt=claim.attempt_number, operation=name,
                                error=f"{type(error).__name__}: {error}")
                self._sleep(1.0)
                if time.monotonic() >= deadline:
                    raise

    def serve(self, consumer: Consumer, *, stop: Callable[[], bool] = lambda: False, stop_when_idle: bool = False,
              poll_timeout: float = 1.0, retry_delay: float = 1.0, retries: int = DELIVERY_RETRIES,
              on_handled: Callable[[Handled], None] | None = None,
              sleep: Callable[[float], None] = time.sleep) -> Served:
        """Handle deliveries one at a time until stop() is true (checked before each poll)
        or, with stop_when_idle, until a poll returns nothing. One message is tried again
        after errors before its acknowledgement at most `retries` times in a row; the next
        such error is raised, with the message uncommitted and the consumer rewound to it.
        BaseException, such as a simulated crash, ends serve() at once, with nothing more
        acknowledged."""
        served = Served()
        failing, failures = None, 0       # the position that last failed before acknowledgement, how often in a row
        while not stop():
            delivery = consumer.poll(poll_timeout)
            if delivery is None:
                if stop_when_idle:
                    break
                continue
            job_id = delivery.job_id()
            if job_id is None:
                log.warning("skipping a message with no valid job id at %r (%d bytes): %r", delivery.position,
                            len(delivery.value), delivery.value[:64])
                self.events.log("malformed", position=repr(delivery.position), size=len(delivery.value))
                served.malformed += 1
                self._commit(consumer, delivery, served)
                continue
            self.events.log("delivered", job_id=job_id, position=repr(delivery.position))
            acknowledged = False

            def acknowledge() -> None:
                nonlocal acknowledged
                acknowledged = True
                self._commit(consumer, delivery, served)

            try:
                handled = self.handle(job_id, acknowledge)
            except Exception:
                if acknowledged:
                    log.exception("job %s failed after its delivery was acknowledged; its lease will expire", job_id)
                    self.events.log("failed_after_ack", job_id=job_id)
                    served.failed_after_ack += 1
                    continue
                failures = failures + 1 if delivery.position == failing else 1
                failing = delivery.position
                consumer.rewind(delivery)         # read again, by this consumer or after a restart: never skipped
                if failures > retries:
                    log.error("job %s: %d errors in a row before its delivery was acknowledged; giving up,"
                              " with the message uncommitted", job_id, failures)
                    self.events.log("gave_up", job_id=job_id, failures=failures)
                    raise
                log.exception("job %s failed before its delivery was acknowledged; reading it again", job_id)
                self.events.log("rewound", job_id=job_id, failures=failures)
                served.rewound += 1
                sleep(retry_delay)
                continue
            served.handled += 1
            if on_handled is not None:
                on_handled(handled)
        return served

    def _commit(self, consumer: Consumer, delivery: Delivery, served: Served) -> None:
        try:
            consumer.commit(delivery)
        except Exception as error:
            served.commit_failures += 1
            self.events.log("commit_failed", position=repr(delivery.position), error=f"{type(error).__name__}: {error}")
            log.warning("could not commit the offset of %r; a later delivery of it is refused by the claim",
                        delivery.position, exc_info=True)

    def _failed(self, claim: Claim, error: str, *, retryable: bool) -> Handled:
        status = self._until_deadline(lambda: self.store.fail_attempt(claim, error, retryable=retryable),
                                      claim, "fail_attempt")
        result = {None: Result.FENCED, Status.QUEUED: Result.REQUEUED, Status.FAILED: Result.FAILED}[status]
        self.events.log(result.value, job_id=claim.job_id, attempt=claim.attempt_number, retryable=retryable,
                        error=error[-2000:])
        return Handled(claim.job_id, result, claim=claim)
