"""A worker that handles one delivered job id at a time, fenced by its attempt token.

Worker.handle(job_id, acknowledge) handles one delivery:
1. claim the job (JobStore.claim);
2. acknowledge the delivery (with Kafka: commit its offset), at once if the claim was
   refused, since the job needs nothing more, or after a successful claim and before the
   run; a worker that dies before acknowledging gets the job delivered again (spec §11);
3. run the pipeline in the attempt's own new folder, <output root>/<run id>, renewing the
   lease whenever the pipeline calls its heartbeat;
4. accept the result, or record the failure.
A worker whose renewal, acceptance or failure write is refused has been fenced off: it
stops and writes nothing more. Its folder stays on disk and is never referenced.

Retries after acknowledgement. Once a delivery is acknowledged, no delivery is pending for
the job. A job that fail_attempt() returned to queued, and a running job whose worker died
after acknowledging, run again only when a new delivery arrives: in this milestone another
handle() call, later a publication by the reconciler (see etf_risk.jobs).

Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash
there to model the worker process dying.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py,
on SQLite and on MySQL 8.4.13.
"""
from __future__ import annotations

import os
import secrets
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from etf_risk.jobs.store import Claim, JobStore, Refusal, Status

WORKER_FAULT_POINTS = (
    "before_claim",
    "after_claim",       # claimed, not yet acknowledged
    "after_pipeline",    # outputs written, result not yet accepted
    "after_accept",
)


class Fenced(Exception):
    """The attempt's token no longer holds the job: another attempt took it over, or it ended."""


class PipelineError(Exception):
    """The pipeline failed; retryable=False when running it again cannot help."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class Pipeline(Protocol):
    def run(self, claim: Claim, run_dir: Path, heartbeat: Callable[[], bool]) -> None:
        """Write the attempt's outputs into run_dir, a new empty folder.

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


class Worker:
    def __init__(self, store: JobStore, pipeline: Pipeline, output_root: str | Path, *,
                 worker_id: str | None = None, fault: Callable[[str], None] | None = None):
        self.store = store
        self.pipeline = pipeline
        self.output_root = Path(output_root)
        self.worker_id = worker_id or f"worker-{os.getpid()}-{secrets.token_hex(3)}"
        self._fault = fault or (lambda point: None)

    def handle(self, job_id: int, acknowledge: Callable[[], None]) -> Handled:
        self._fault("before_claim")
        claim = self.store.claim(job_id, self.worker_id, self.output_root)
        if isinstance(claim, Refusal):
            acknowledge()
            return Handled(job_id, Result.SKIPPED, reason=claim)
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
            self.pipeline.run(claim, claim.output_dir, lambda: self.store.renew(claim))
        except Fenced:
            return Handled(job_id, Result.FENCED, claim=claim)
        except PipelineError as error:
            return self._failed(claim, str(error), retryable=error.retryable)
        except Exception as error:
            # Not a failure the pipeline reported: recorded with its type, and retried like one.
            return self._failed(claim, f"{type(error).__name__}: {error}", retryable=True)
        self._fault("after_pipeline")
        if not self.store.accept_result(claim):
            return Handled(job_id, Result.FENCED, claim=claim)
        self._fault("after_accept")
        return Handled(job_id, Result.ACCEPTED, claim=claim)

    def _failed(self, claim: Claim, error: str, *, retryable: bool) -> Handled:
        status = self.store.fail_attempt(claim, error, retryable=retryable)
        result = {None: Result.FENCED, Status.QUEUED: Result.REQUEUED, Status.FAILED: Result.FAILED}[status]
        return Handled(claim.job_id, result, claim=claim)
