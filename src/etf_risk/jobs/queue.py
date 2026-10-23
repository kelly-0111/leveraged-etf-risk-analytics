"""Delivery of job ids: what the submitter, the worker and the reconciler need from a queue.

A Publisher sends a job id and waits for the broker's confirmation. A Consumer delivers
job ids at least once and moves its group's position only when told to: commit() records
that the group is done with a message, and a consumer that restarts resumes after the last
commit. A consumer that keeps running does not see an uncommitted message again by itself;
rewind() sends it back to that message. etf_risk.jobs.kafka implements both with Kafka,
and simulated.MemoryQueue implements them in memory for the offline tests.

submit_job() inserts the job (queued, version 0), publishes its id, and on confirmation
records published_at, conditional on version 0. A publication that is not confirmed may
still have been written; the reconciler publishes the job again after its grace period,
and claim() refuses the duplicate delivery.

A message carries one job id in decimal, exactly as encode() writes it: an integer from 1 to
MAX_JOB_ID, at most 19 digits, with no sign, spaces or leading zeros. Delivery.job_id()
checks the format and the length before converting anything, and the range after; a
message that fails returns None. The worker counts such a message as malformed, commits it
and skips it, so no payload can stop it or reach the database.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_queue.py
and tests/test_jobs_kafka.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Protocol

from etf_risk.jobs.store import DEFAULT_MAX_ATTEMPTS, JobStore

CONFIRMATION_TIMEOUT = timedelta(seconds=10)   # how long a publisher waits for the broker's confirmation
# The largest job id both job tables hold: SQLite's INTEGER is signed 64-bit; MySQL's BIGINT
# UNSIGNED holds more, but the store runs on both.
MAX_JOB_ID = 2**63 - 1
MAX_JOB_ID_DIGITS = len(str(MAX_JOB_ID))       # 19
_JOB_ID = re.compile(rb"[1-9][0-9]{0,%d}" % (MAX_JOB_ID_DIGITS - 1))


def encode(job_id: int) -> bytes:
    """A job id as a message carries it: its decimal digits."""
    if not 1 <= job_id <= MAX_JOB_ID:
        raise ValueError(f"job id {job_id} is outside the supported range 1..{MAX_JOB_ID}")
    return str(job_id).encode("ascii")


@dataclass(frozen=True)
class Delivery:
    """One delivered message: its value and where it sits (Kafka: topic, partition and
    offset; MemoryQueue: the offset)."""
    value: bytes
    position: Any

    def job_id(self) -> int | None:
        """The job id the message carries, or None if it carries no valid one (see the module
        docstring). The format and the length are checked first, so int() never sees a long
        payload: it refuses more than 4,300 digits with ValueError."""
        if _JOB_ID.fullmatch(self.value) is None:
            return None
        job_id = int(self.value)
        return job_id if job_id <= MAX_JOB_ID else None


class Publisher(Protocol):
    def publish(self, job_id: int) -> bool: ...        # True once the broker confirmed the message


class Consumer(Protocol):
    def poll(self, timeout: float) -> Delivery | None: ...
    def commit(self, delivery: Delivery) -> None: ...  # the group resumes after this message
    def rewind(self, delivery: Delivery) -> None: ...  # this consumer reads the message again
    def close(self) -> None: ...


@dataclass(frozen=True)
class Submitted:
    job_id: int
    published: bool      # the broker confirmed the message
    recorded: bool       # and published_at was set: the job was still queued, unchanged


def submit_job(store: JobStore, publisher: Publisher, params: dict, input_checksums: dict, *,
               max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> Submitted:
    """Insert a job and publish it. recorded is False when the publication was not confirmed,
    or when a worker claimed the job before the confirmation could be recorded."""
    job_id = store.submit(params, input_checksums, max_attempts=max_attempts)
    published = publisher.publish(job_id)
    return Submitted(job_id, published, published and store.mark_published(job_id, version=0))
