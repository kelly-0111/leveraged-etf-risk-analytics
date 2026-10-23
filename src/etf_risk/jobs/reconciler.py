"""The reconciler (spec §11): requeues jobs whose lease expired and publishes queued jobs
whose publication was never confirmed, each change conditional on the state it read.

One pass, run_once():
1. Expired leases. For each running job whose lease has expired, requeue_expired() with the
   token read: the job returns to queued with no publication recorded, or fails when no
   attempts are left. A job renewed, taken over or finished since the read is left alone.
2. Unconfirmed publications. Each queued job with no publication recorded is published and,
   once the broker confirms, recorded with mark_published() and the version read. A job
   that was never claimed (attempt 0) waits PUBLICATION_GRACE after it was queued: its
   submitter may still be waiting for its own confirmation, for CONFIRMATION_TIMEOUT at
   most, so the grace must be longer. A job that returned to queued has nobody else to
   publish it and goes at once, in the same pass as its requeue.
A duplicate publication is harmless: claim() refuses a delivery that finds the job running
under a live lease or finished. Two reconcilers may run at once; the guards let one change
win, and the other counts it as stale.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_reconciler.py,
tests/test_jobs_queue.py and tests/test_jobs_kafka.py.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import timedelta

from etf_risk.jobs.events import NO_EVENTS, EventLog
from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, Publisher
from etf_risk.jobs.store import JobStore, Status

PUBLICATION_GRACE = timedelta(seconds=30)     # a never-claimed job's wait before it is published again
RECONCILE_INTERVAL = timedelta(seconds=5)     # between passes

log = logging.getLogger(__name__)


@dataclass
class Pass:
    """What one pass did."""
    requeued: int = 0       # expired leases returned to queued
    failed: int = 0         # expired leases with no attempts left
    published: int = 0      # publications confirmed and recorded
    unconfirmed: int = 0    # publications not confirmed; the next pass tries again
    waiting: int = 0        # never-claimed jobs still within the grace period
    stale: int = 0          # jobs that changed between the read and the change: left alone


class Reconciler:
    def __init__(self, store: JobStore, publisher: Publisher, *,
                 publication_grace: timedelta = PUBLICATION_GRACE,
                 confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT, events: EventLog = NO_EVENTS):
        if publication_grace <= confirmation_timeout:
            raise ValueError(f"the publication grace ({publication_grace}) must exceed the confirmation timeout"
                             f" ({confirmation_timeout}), or the reconciler races a submitter still waiting")
        self.store = store
        self.publisher = publisher
        self.publication_grace = publication_grace
        self.events = events

    def run_once(self) -> Pass:
        """One pass; each job it changed or left alone is an event (requeued, failed, stale,
        published, unconfirmed), for the recovery experiments' timings."""
        done = Pass()
        for lease in self.store.expired_leases():
            status = self.store.requeue_expired(lease.job_id, lease.token)
            if status is Status.QUEUED:
                done.requeued += 1
                self.events.log("requeued", job_id=lease.job_id)
            elif status is Status.FAILED:
                done.failed += 1
                self.events.log("exhausted", job_id=lease.job_id)
            else:
                done.stale += 1
                self.events.log("stale", job_id=lease.job_id, during="requeue")
        now = self.store.clock.now()
        for job in self.store.unconfirmed():
            if job.attempt_number == 0 and now - job.queued_since < self.publication_grace:
                done.waiting += 1
            elif not self.publisher.publish(job.job_id):
                done.unconfirmed += 1
                self.events.log("unconfirmed", job_id=job.job_id)
            elif self.store.mark_published(job.job_id, job.version):
                done.published += 1
                self.events.log("published", job_id=job.job_id, attempts_so_far=job.attempt_number)
            else:
                done.stale += 1
                self.events.log("stale", job_id=job.job_id, during="publication")
        return done

    def run(self, stop: threading.Event, *, interval: timedelta = RECONCILE_INTERVAL) -> None:
        """Pass after pass until stop is set. A pass that raises is logged, and the next one
        starts after the interval."""
        while not stop.is_set():
            try:
                done = self.run_once()
            except Exception as error:
                log.exception("reconciler pass failed")
                self.events.log("pass_failed", error=f"{type(error).__name__}: {error}"[:500])
            else:
                log.info("reconciler pass: %s", done)
            stop.wait(interval.total_seconds())
