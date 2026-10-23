"""The job system's state transitions, each one transaction of conditional SQL.

JobStore holds every SQL statement of the job system. A state change is one UPDATE of
the job's row in jobs whose WHERE clause is the transition's guard, and the number of
rows it matched is the answer: 1, the change happened; 0, it was refused, or the worker
asking has been fenced off. The same transaction records the change in job_attempts,
where every statement must touch exactly one row; anything else raises and rolls back
both tables (submit and mark_published change jobs only). Reads only classify a refusal
or report what the reconciler observed: a write that follows a read carries its own
guard, which checks again what the read saw.

    operation        from -> to                                guard
    submit           -> queued                                 (insert)
    mark_published   queued -> queued, publication recorded    status queued, none recorded yet,
                                                               the version read before publishing
    claim            queued -> running                         status queued
                     running -> running (takeover)             lease expired, attempts left
    renew            running -> running                        status running, the attempt's token
    accept_result    running -> succeeded, recording the       status running, the attempt's token
                     result's run digest
    fail_attempt     running -> queued (retryable, attempts    status running, the attempt's token
                     left) or running -> failed
    requeue_expired  running -> queued (for the reconciler)    status running, the token read before,
                                                               lease expired, attempts left
    exhaust          running -> failed (inside claim and       lease expired, no attempts left,
                     requeue_expired)                          the token read before

succeeded and failed are terminal. published_at is set only while a job is queued: it says
a message for the job's current queued state was confirmed, so the reconciler need not
publish it again. A claim clears it, and a job that returns to queued has none. Renewal and acceptance need only status running and
the attempt's token: a worker whose lease expired keeps the job until another claim takes
it over. The lease decides only when that may happen, so a wrong clock can cause an extra
execution but never a second accepted result. Times come from the store's Clock and are
passed as parameters, not taken from NOW(), so the tests can step time. docs/job-table.md
walks through claim(), the token checks and the transactions with two workers.

A write operation that the database rolled back over a lock conflict (MySQL: a deadlock or
a lock wait timeout) runs again, up to CONFLICT_RETRIES runs in all; the guards make a
repeated run safe. A failed COMMIT may still have taken effect, so the operation raises and
leaves the decision to the caller: repeating accept_result() reports an acceptance that did
happen, and an attempt whose claim was lost this way is taken over once its lease expires.

The accepted result. accept_result() records the run digest of the attempt's result
(etf_risk.runs) in the same update that marks the attempt accepted, and a CHECK constraint
requires a digest exactly for accepted attempts. The decision and the content it accepted
are therefore bound in one transaction. A repeat after a failed COMMIT counts as accepted
only for the same token and the same digest.

Identity. job_store holds one row: a random store id, written once (ensure_identity()). Job
and run ids start again at 1 when the tables are created anew, so whatever lives outside the
database names an attempt by store id and run id together: output folders, process markers
and cache keys.

Connections. Given a way to connect (connect=...), the store replaces a connection that
broke. It does so only at the start of an operation: before BEGIN, or before a read that
runs on its own. It also replaces a connection idle for IDLE_PING seconds whose ping fails.
It never reconnects inside a transaction. A transaction whose connection broke between two
statements is abandoned with that connection, since its later statements would otherwise
commit one by one on a new one. A broken connection gets no ROLLBACK, because the server
rolls back the open transaction when the session ends. The operation that saw the break
raises (no replay); the next one connects again. Which errors mean a broken connection is
the dialect's decision (is_disconnect).

MySQL behaviour this SQL is written for, for the MySQL integration tests to confirm: an
UPDATE reads the latest committed version of the row and locks it, so concurrent claims
of one job take effect one after the other; affected rows count only changed rows unless
the connection sets CLIENT_FOUND_ROWS, so every guarded UPDATE also sets
version = version + 1; single-table SET clauses are evaluated left to right, so no SET
expression reads a column assigned earlier in the statement (computed values are
parameters); CHECK constraints are enforced from MySQL 8.0.16. SQLiteDialect is below; the
MySQL dialect and connection are in etf_risk.jobs.mysql.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_store.py,
tests/test_jobs_worker.py, tests/test_jobs_reconciler.py and tests/test_jobs_queue.py, on
SQLite and on MySQL 8.4.13.
"""
from __future__ import annotations

import functools
import json
import secrets
import sqlite3
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from etf_risk.runs import is_digest

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
SCHEMA_VERSION = 2      # 2: job_store and job_attempts.result_digest
DEFAULT_LEASE = timedelta(seconds=60)
DEFAULT_MAX_ATTEMPTS = 3
CONFLICT_RETRIES = 3    # runs of one write operation in all, while the database reports lock conflicts
IDLE_PING = 60.0        # seconds: a connection idle this long is pinged before the next operation


class Status(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


TERMINAL = frozenset({Status.SUCCEEDED, Status.FAILED})


class Outcome(StrEnum):
    """How an attempt ended (job_attempts.outcome); running until then."""
    RUNNING = "running"
    ACCEPTED = "accepted"
    FAILED = "failed"
    EXPIRED = "expired"          # its lease expired, and a claim took the job over or failed it


class Refusal(StrEnum):
    """Why claim() started no attempt. In every case the delivery needs nothing more."""
    NOT_FOUND = "not_found"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    LEASE_HELD = "lease_held"    # running under a live lease: its holder owns the job
    EXHAUSTED = "exhausted"      # the lease expired with no attempts left: the job is now failed


# The status changes each operation may make; the tests check every change against it.
TRANSITIONS: dict[str, frozenset[tuple[Status, Status]]] = {
    "claim": frozenset({(Status.QUEUED, Status.RUNNING), (Status.RUNNING, Status.RUNNING)}),
    "renew": frozenset({(Status.RUNNING, Status.RUNNING)}),
    "accept_result": frozenset({(Status.RUNNING, Status.SUCCEEDED)}),
    "fail_attempt": frozenset({(Status.RUNNING, Status.QUEUED), (Status.RUNNING, Status.FAILED)}),
    "exhaust": frozenset({(Status.RUNNING, Status.FAILED)}),
    "mark_published": frozenset({(Status.QUEUED, Status.QUEUED)}),
    "requeue_expired": frozenset({(Status.RUNNING, Status.QUEUED), (Status.RUNNING, Status.FAILED)}),
}

# The gaps between the statements of one transaction where JobStore(fault=...) is called;
# the tests raise there and check that both tables roll back.
FAULT_POINTS = (
    "claim.jobs_updated",               # the job is taken; job_attempts not yet written
    "claim.previous_attempt_expired",   # takeover: the old attempt is marked, the new one not yet inserted
    "renew.jobs_updated",
    "accept_result.jobs_updated",
    "fail_attempt.jobs_updated",
    "exhaust.jobs_updated",
    "requeue_expired.jobs_updated",
)

# Each query lists the jobs that break one invariant of the guarantee or of the agreement
# between the two tables; the CHECK constraints cannot state these across rows.
INVARIANT_QUERIES = {
    "succeeded without exactly one accepted attempt":
        "SELECT j.job_id FROM jobs j WHERE j.status = 'succeeded' AND 1 <>"
        " (SELECT COUNT(*) FROM job_attempts a WHERE a.job_id = j.job_id AND a.outcome = 'accepted')",
    "accepted attempt of a job that did not succeed":
        "SELECT DISTINCT a.job_id FROM job_attempts a JOIN jobs j ON j.job_id = a.job_id"
        " WHERE a.outcome = 'accepted' AND j.status <> 'succeeded'",
    "accepted_attempt names an attempt that was not accepted":
        "SELECT j.job_id FROM jobs j JOIN job_attempts a"
        " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt WHERE a.outcome <> 'accepted'",
    "running job whose current attempt is not running under its token":
        "SELECT j.job_id FROM jobs j LEFT JOIN job_attempts a"
        " ON a.job_id = j.job_id AND a.attempt_number = j.attempt_number"
        " WHERE j.status = 'running'"
        " AND (a.outcome IS NULL OR a.outcome <> 'running' OR a.attempt_token <> j.attempt_token)",
    "running attempt that is not its job's current one":
        "SELECT DISTINCT a.job_id FROM job_attempts a JOIN jobs j ON j.job_id = a.job_id"
        " WHERE a.outcome = 'running' AND (j.status <> 'running' OR a.attempt_number <> j.attempt_number)",
    "attempt rows differ from attempt_number":
        "SELECT j.job_id FROM jobs j WHERE j.attempt_number <>"
        " (SELECT COUNT(*) FROM job_attempts a WHERE a.job_id = j.job_id)",
    "attempts share an output folder":
        "SELECT MIN(job_id) FROM job_attempts GROUP BY output_dir HAVING COUNT(*) > 1",
}

_TIME_COLUMNS = frozenset({"lease_expires_at", "created_at", "updated_at", "finished_at", "published_at",
                           "claimed_at", "ended_at"})
_JSON_COLUMNS = frozenset({"params", "input_checksums"})


class StoreInvariantError(RuntimeError):
    """A job_attempts write did not touch exactly one row: the two tables would disagree."""


class ClaimRace(RuntimeError):
    """The job changed between claim's guards and the read that classifies the refusal.

    Impossible on SQLite, whose write lock covers the whole transaction. In MySQL it should
    not happen under REPEATABLE READ, where the refused UPDATE keeps the row locked until the
    transaction ends; under READ COMMITTED that lock is released at once, so another claim
    can change the row before the read. The MySQL tests ran competing claims under both
    levels without it, but none forces that gap. The delivery then fails unacknowledged and
    is delivered again."""


class Clock(Protocol):
    def now(self) -> datetime: ...   # timezone-aware, UTC


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class Dialect(Protocol):
    """What the shared SQL needs from one database: SQLiteDialect here, MySQLDialect in etf_risk.jobs.mysql."""
    name: str
    begin: str                                          # starts a write transaction

    def sql(self, text: str) -> str: ...                # ':name' parameters in the driver's style
    def time(self, value: datetime) -> Any: ...         # a UTC time as the driver takes it
    def parse_time(self, value: Any) -> datetime: ...
    def is_conflict(self, error: BaseException) -> bool: ...   # rolled back over a lock conflict: run again
    def is_disconnect(self, error: BaseException) -> bool: ...  # the connection is gone: open a new one, later
    def ping(self, connection: Any) -> None: ...                # raises if the connection is no longer usable


class SQLiteDialect:
    """sqlite3 takes ':name' parameters as written. BEGIN IMMEDIATE takes the database's
    write lock when the transaction starts, waiting for it up to the connection's busy
    timeout, so a transaction that started meets no lock conflict and nothing is run again.
    Times are fixed-width UTC text, so comparing the text compares the times."""
    name = "sqlite"
    begin = "BEGIN IMMEDIATE"

    @staticmethod
    def sql(text: str) -> str:
        return text

    @staticmethod
    def time(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

    @staticmethod
    def parse_time(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)

    @staticmethod
    def is_conflict(error: BaseException) -> bool:
        return False

    @staticmethod
    def is_disconnect(error: BaseException) -> bool:
        return False                                    # a file database has no connection to lose

    @staticmethod
    def ping(connection: Any) -> None:
        return None


SQLITE = SQLiteDialect()


def open_sqlite(path: str | Path, *, create: bool = False, check_same_thread: bool = True) -> sqlite3.Connection:
    """A connection for the offline tests. The driver opens no transactions of its own
    (isolation_level=None): the store issues BEGIN and COMMIT. Foreign keys are enforced.
    check_same_thread=False lets a test hand the connection to another thread (one at a time)."""
    conn = sqlite3.connect(path, isolation_level=None, check_same_thread=check_same_thread)
    conn.execute("PRAGMA foreign_keys = ON")
    if create:
        conn.executescript((SCHEMA_DIR / "sqlite.sql").read_text())
    return conn


def run_id(job_id: int, attempt_number: int) -> str:
    """Names the attempt's output folder; unique, since attempt numbers are unique per job."""
    return f"job-{job_id}-attempt-{attempt_number}"


@dataclass(frozen=True)
class Claim:
    """A started attempt: what the worker needs to run, renew and finish it."""
    job_id: int
    attempt_number: int
    token: str
    run_id: str
    output_dir: Path
    max_attempts: int
    params: dict
    input_checksums: dict


@dataclass(frozen=True)
class ExpiredLease:
    """A running job whose lease had expired when the reconciler looked, with the token it saw."""
    job_id: int
    token: str


@dataclass(frozen=True)
class Unconfirmed:
    """A queued job with no confirmed publication when the reconciler looked. version makes
    the reconciler's change conditional on this state; queued_since is the last change of
    the row, which for such a job is when it became queued."""
    job_id: int
    version: int
    attempt_number: int
    queued_since: datetime


def _retry_conflicts(operation: Callable[..., Any]) -> Callable[..., Any]:
    """Runs a write operation again when the database rolled it back over a lock conflict."""
    @functools.wraps(operation)
    def run(self: JobStore, *args: Any, **kwargs: Any) -> Any:
        for run_number in range(1, CONFLICT_RETRIES + 1):
            try:
                return operation(self, *args, **kwargs)
            except Exception as error:
                if run_number == CONFLICT_RETRIES or not self.dialect.is_conflict(error):
                    raise
    return run


class JobStore:
    """The job table's operations, each one transaction on the store's connection.

    connection is an open connection, or None when connect is given. connect, when given,
    opens a new connection with the session settings it needs: the store calls it for its
    first operation and again after a connection broke (see Connections above). Without it a
    broken connection stays broken. fault, when given, is called with a name from
    FAULT_POINTS between the statements of a transaction; the tests raise there."""

    def __init__(self, connection: Any | None, dialect: Dialect, *, clock: Clock | None = None,
                 lease: timedelta = DEFAULT_LEASE, fault: Callable[[str], None] | None = None,
                 connect: Callable[[], Any] | None = None):
        if connection is None and connect is None:
            raise ValueError("give the store a connection or a way to connect")
        self.connection = connection
        self.connect = connect
        self.dialect = dialect
        self.clock = clock or SystemClock()
        self.lease = lease
        self._fault = fault or (lambda point: None)
        self._in_transaction = False
        self._last_used = time.monotonic()
        self._store_id: str | None = None

    # Identity

    @_retry_conflicts
    def ensure_identity(self) -> str:
        """Write the job table's store id if it has none yet, and return it."""
        with self._transaction():
            row = self._fetch_one("SELECT store_id FROM job_store WHERE id = 1")
            if row is None:
                store_id = secrets.token_hex(16)
                self._execute("INSERT INTO job_store (id, store_id, schema_version, created_at)"
                              " VALUES (1, :store_id, :version, :now)",
                              store_id=store_id, version=SCHEMA_VERSION, now=self._time(self.clock.now()))
            else:
                store_id = row["store_id"]
        self._store_id = store_id
        return store_id

    def store_id(self) -> str:
        """The job table's identity (see Identity above), read once and then kept."""
        if self._store_id is None:
            row = self._fetch_one("SELECT store_id FROM job_store WHERE id = 1")
            if row is None:
                raise LookupError("the job table has no store id yet: set it up with ensure_identity() (init-db)")
            self._store_id = row["store_id"]
        return self._store_id

    @_retry_conflicts
    def submit(self, params: dict, input_checksums: dict, *, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> int:
        """Create a queued job, at version 0, and return its id. Publishing it is a separate
        step: etf_risk.jobs.queue.submit_job() publishes and records the confirmation."""
        now = self._time(self.clock.now())
        with self._transaction():
            return self._execute(
                "INSERT INTO jobs (params, input_checksums, status, max_attempts, attempt_number, version,"
                " created_at, updated_at)"
                " VALUES (:params, :input_checksums, 'queued', :max_attempts, 0, 0, :now, :now)",
                params=_json(params), input_checksums=_json(input_checksums), max_attempts=max_attempts,
                now=now).lastrowid

    @_retry_conflicts
    def mark_published(self, job_id: int, version: int) -> bool:
        """Record that Kafka confirmed a publication of the job, if the job is still as it was
        when its version was read before publishing: queued, with no publication recorded.
        Otherwise the message may already have been consumed (the job was claimed, and
        perhaps returned to queued), so nothing is recorded and the reconciler publishes the
        job again if it is queued. True: recorded."""
        now = self._time(self.clock.now())
        with self._transaction():
            return self._execute(
                "UPDATE jobs SET published_at = :now, version = version + 1, updated_at = :now"
                " WHERE job_id = :job_id AND status = 'queued' AND published_at IS NULL AND version = :version",
                job_id=job_id, version=version, now=now).rowcount == 1

    @_retry_conflicts
    def claim(self, job_id: int, worker_id: str, output_root: str | Path) -> Claim | Refusal:
        """Start a new attempt of the job, or say why the delivery needs nothing more.

        One transaction: take the job (from queued, or over an expired lease), mark the
        attempt that held the expired lease as expired, and insert the new attempt. The token
        is generated here, before the claim; it is the attempt's identity in every later guard."""
        now = self.clock.now()
        token = secrets.token_hex(16)
        take = dict(job_id=job_id, token=token, lease_expires_at=self._time(now + self.lease), now=self._time(now))
        with self._transaction():
            if self._execute(
                    "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1,"
                    " attempt_token = :token, lease_expires_at = :lease_expires_at, published_at = NULL,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'queued'", **take).rowcount:
                takeover = False
            elif self._execute(
                    "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1,"
                    " attempt_token = :token, lease_expires_at = :lease_expires_at, published_at = NULL,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND lease_expires_at <= :now"
                    " AND attempt_number < max_attempts", **take).rowcount:
                takeover = True
            else:
                return self._refusal(job_id, now)
            self._fault("claim.jobs_updated")
            job = self._fetch_one("SELECT attempt_number, max_attempts, params, input_checksums FROM jobs"
                                  " WHERE job_id = :job_id", job_id=job_id)
            n = job["attempt_number"]
            if takeover:
                self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_number = :previous AND outcome = 'running'",
                                job_id=job_id, previous=n - 1, now=take["now"])
                self._fault("claim.previous_attempt_expired")
            claim = Claim(job_id, n, token, run_id(job_id, n), Path(output_root) / run_id(job_id, n),
                          job["max_attempts"], json.loads(job["params"]), json.loads(job["input_checksums"]))
            self._execute(
                "INSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id, output_dir,"
                " outcome, claimed_at, lease_expires_at, renewals)"
                " VALUES (:job_id, :attempt_number, :token, :worker_id, :run_id, :output_dir,"
                " 'running', :now, :lease_expires_at, 0)",
                job_id=job_id, attempt_number=n, token=token, worker_id=worker_id, run_id=claim.run_id,
                output_dir=str(claim.output_dir), now=take["now"], lease_expires_at=take["lease_expires_at"])
            return claim

    @_retry_conflicts
    def renew(self, claim: Claim) -> bool:
        """Extend the attempt's lease from now. False: the worker has been fenced off and must stop."""
        now = self.clock.now()
        lease_expires_at = self._time(now + self.lease)
        with self._transaction():
            if not self._execute(
                    "UPDATE jobs SET lease_expires_at = :lease_expires_at, version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
                    job_id=claim.job_id, token=claim.token, lease_expires_at=lease_expires_at,
                    now=self._time(now)).rowcount:
                return False
            self._fault("renew.jobs_updated")
            self._write_one("UPDATE job_attempts SET lease_expires_at = :lease_expires_at, renewals = renewals + 1"
                            " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                            job_id=claim.job_id, attempt_number=claim.attempt_number,
                            lease_expires_at=lease_expires_at)
            return True

    @_retry_conflicts
    def accept_result(self, claim: Claim, result_digest: str) -> bool:
        """Accept this attempt's result, whose files have the run digest result_digest
        (etf_risk.runs), recorded with the acceptance. True if it is the job's accepted
        result, now or already (a repeat, with the same token and digest, after a failed
        COMMIT that took effect); False: fenced off."""
        if not is_digest(result_digest):
            raise ValueError(f"not a run digest: {result_digest!r}")
        now = self._time(self.clock.now())
        with self._transaction():
            if self._execute(
                    "UPDATE jobs SET status = 'succeeded', accepted_attempt = :attempt_number,"
                    " attempt_token = NULL, lease_expires_at = NULL, finished_at = :now,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
                    job_id=claim.job_id, token=claim.token, attempt_number=claim.attempt_number,
                    now=now).rowcount:
                self._fault("accept_result.jobs_updated")
                self._write_one("UPDATE job_attempts SET outcome = 'accepted', result_digest = :digest, ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                                job_id=claim.job_id, attempt_number=claim.attempt_number, digest=result_digest,
                                now=now)
                return True
            return self._fetch_one(
                "SELECT 1 FROM jobs j JOIN job_attempts a"
                " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt"
                " WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token"
                " AND a.result_digest = :digest",
                job_id=claim.job_id, token=claim.token, digest=result_digest) is not None

    @_retry_conflicts
    def fail_attempt(self, claim: Claim, error: str, *, retryable: bool) -> Status | None:
        """End the attempt as failed. The job returns to queued if the error is retryable and
        attempts are left, and fails otherwise; returns its new status, or None when the worker
        was fenced off. Back in queued, the job is not delivered again by this (see etf_risk.jobs)."""
        now = self._time(self.clock.now())
        requeue = retryable and claim.attempt_number < claim.max_attempts
        status = Status.QUEUED if requeue else Status.FAILED
        with self._transaction():
            if not self._execute(
                    "UPDATE jobs SET status = :status, attempt_token = NULL, lease_expires_at = NULL,"
                    " error = :job_error, finished_at = :finished_at, version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
                    job_id=claim.job_id, token=claim.token, status=status.value,
                    job_error=None if requeue else error, finished_at=None if requeue else now,
                    now=now).rowcount:
                return None
            self._fault("fail_attempt.jobs_updated")
            self._write_one("UPDATE job_attempts SET outcome = 'failed', error = :error, ended_at = :now"
                            " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                            job_id=claim.job_id, attempt_number=claim.attempt_number, error=error, now=now)
            return status

    @_retry_conflicts
    def requeue_expired(self, job_id: int, token: str) -> Status | None:
        """For the reconciler: end the attempt whose lease expired, conditional on the token
        read before (expired_leases()). The job returns to queued, with no publication
        recorded, while attempts are left, and fails otherwise; its attempt becomes expired.
        Returns the job's new status, or None when the job changed since the read (renewed
        and finished, taken over, or failed)."""
        now = self.clock.now()
        now_value = self._time(now)
        with self._transaction():
            if self._execute(
                    "UPDATE jobs SET status = 'queued', attempt_token = NULL, lease_expires_at = NULL,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token"
                    " AND lease_expires_at <= :now AND attempt_number < max_attempts",
                    job_id=job_id, token=token, now=now_value).rowcount:
                self._fault("requeue_expired.jobs_updated")
                self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_token = :token AND outcome = 'running'",
                                job_id=job_id, token=token, now=now_value)
                return Status.QUEUED
            attempt = self._fetch_one("SELECT attempt_number FROM job_attempts"
                                      " WHERE job_id = :job_id AND attempt_token = :token", job_id=job_id, token=token)
            if attempt is not None and self._exhaust(job_id, token, attempt["attempt_number"], now):
                return Status.FAILED
            return None

    def expired_leases(self) -> list[ExpiredLease]:
        """Running jobs whose lease has expired by the store's clock, with their tokens."""
        return [ExpiredLease(row["job_id"], row["attempt_token"]) for row in self._fetch_all(
            "SELECT job_id, attempt_token FROM jobs WHERE status = 'running' AND lease_expires_at <= :now"
            " ORDER BY job_id", now=self._time(self.clock.now()))]

    def unconfirmed(self) -> list[Unconfirmed]:
        """Queued jobs with no confirmed publication."""
        return [Unconfirmed(row["job_id"], row["version"], row["attempt_number"],
                            self.dialect.parse_time(row["updated_at"])) for row in self._fetch_all(
            "SELECT job_id, version, attempt_number, updated_at FROM jobs"
            " WHERE status = 'queued' AND published_at IS NULL ORDER BY job_id")]

    def job(self, job_id: int) -> dict | None:
        row = self._fetch_one("SELECT * FROM jobs WHERE job_id = :job_id", job_id=job_id)
        return None if row is None else self._decode(row)

    def attempts(self, job_id: int) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all(
            "SELECT * FROM job_attempts WHERE job_id = :job_id ORDER BY attempt_number", job_id=job_id)]

    def all_jobs(self) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all("SELECT * FROM jobs ORDER BY job_id")]

    def all_attempts(self) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all(
            "SELECT * FROM job_attempts ORDER BY job_id, attempt_number")]

    def current_attempts(self) -> dict[int, tuple[int, str]]:
        """Running jobs: job id -> (current attempt number, its token). An attempt is valid
        and active exactly while it is listed here (the startup sweep keeps its processes)."""
        return {row["job_id"]: (row["attempt_number"], row["attempt_token"]) for row in self._fetch_all(
            "SELECT job_id, attempt_number, attempt_token FROM jobs WHERE status = 'running' ORDER BY job_id")}

    def invariant_violations(self) -> dict[str, list[int]]:
        """The jobs breaking each invariant in INVARIANT_QUERIES, read in one transaction;
        empty when all hold. The tests run it after every scenario; the recovery experiments
        (E1) can run it on MySQL."""
        with self._transaction():
            found = {name: [row[0] for row in self._execute(sql).fetchall()]
                     for name, sql in INVARIANT_QUERIES.items()}
        return {name: job_ids for name, job_ids in found.items() if job_ids}

    def _refusal(self, job_id: int, now: datetime) -> Refusal:
        """Why both of claim's guards failed, read inside claim's transaction."""
        job = self._fetch_one("SELECT status, attempt_number, max_attempts, attempt_token, lease_expires_at"
                              " FROM jobs WHERE job_id = :job_id", job_id=job_id)
        if job is None:
            return Refusal.NOT_FOUND
        status = Status(job["status"])
        if status in TERMINAL:
            return Refusal.SUCCEEDED if status is Status.SUCCEEDED else Refusal.FAILED
        if status is Status.RUNNING and self.dialect.parse_time(job["lease_expires_at"]) > now:
            return Refusal.LEASE_HELD
        if (status is Status.RUNNING and job["attempt_number"] >= job["max_attempts"]
                and self._exhaust(job_id, job["attempt_token"], job["attempt_number"], now)):
            return Refusal.EXHAUSTED
        raise ClaimRace(f"job {job_id} changed while it was being claimed")

    def _exhaust(self, job_id: int, token: str, attempt_number: int, now: datetime) -> bool:
        """running -> failed: the lease expired and no attempts are left. Conditional on the
        token read before (by claim, or by the reconciler), so a change in between makes it
        match nothing."""
        now_value = self._time(now)
        if not self._execute(
                "UPDATE jobs SET status = 'failed', attempt_token = NULL, lease_expires_at = NULL,"
                " error = :error, finished_at = :now, version = version + 1, updated_at = :now"
                " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token"
                " AND lease_expires_at <= :now AND attempt_number >= max_attempts",
                job_id=job_id, token=token, now=now_value,
                error=f"attempts exhausted: the lease of the last attempt ({attempt_number}) expired").rowcount:
            return False
        self._fault("exhaust.jobs_updated")
        self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                        " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                        job_id=job_id, attempt_number=attempt_number, now=now_value)
        return True

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        cursor = self._open().cursor()                  # the start of an operation: the only place to reconnect
        try:
            cursor.execute(self.dialect.begin)
        except BaseException as error:
            self._forget_if_broken(error)
            raise
        self._in_transaction = True
        try:
            yield
            cursor.execute("COMMIT")
        except BaseException as error:
            # BaseException too: a simulated crash must not leave the transaction open (a real
            # crash closes the connection, and the database rolls back the same way). After a
            # failed COMMIT the ROLLBACK may find nothing left to undo, or fail itself. A broken
            # connection gets no ROLLBACK and no further statement: the server rolls back the
            # open transaction when its session ends.
            if not self._forget_if_broken(error):
                try:
                    cursor.execute("ROLLBACK")
                except Exception as rollback_error:
                    error.add_note(f"the ROLLBACK after this error failed too: {rollback_error!r}")
                    self._forget_if_broken(rollback_error)
            raise
        finally:
            self._in_transaction = False
            self._last_used = time.monotonic()

    def _execute(self, sql: str, **params: Any) -> Any:
        if self._in_transaction:                         # inside a transaction: this connection or none
            cursor = self.connection.cursor()
            cursor.execute(self.dialect.sql(sql), params)
            return cursor
        try:                                             # a read on its own is an operation of its own
            cursor = self._open().cursor()
            cursor.execute(self.dialect.sql(sql), params)
            return cursor
        except BaseException as error:
            self._forget_if_broken(error)
            raise
        finally:
            self._last_used = time.monotonic()

    def _open(self) -> Any:
        """The connection for a new operation, after replacing one that broke, or one that sat
        idle for IDLE_PING seconds and no longer answers a ping."""
        if self.connection is not None and self.connect is not None \
                and time.monotonic() - self._last_used >= IDLE_PING:
            try:
                self.dialect.ping(self.connection)
            except Exception as error:
                if not self._forget_if_broken(error):
                    raise
        if self.connection is None:
            if self.connect is None:
                raise ConnectionError("the job store's connection broke, and the store was given no way to reconnect")
            self.connection = self.connect()
            self._last_used = time.monotonic()
        return self.connection

    def _forget_if_broken(self, error: BaseException) -> bool:
        """Drop the connection if error means it is gone; whether it was dropped."""
        if self.connection is None:
            return True
        if not (self.dialect.is_disconnect(error) or getattr(self.connection, "open", True) is False):
            return False
        try:
            self.connection.close()
        except Exception:
            pass
        self.connection = None
        return True

    def _write_one(self, sql: str, **params: Any) -> None:
        """A job_attempts write that must touch exactly one row; otherwise the transaction rolls back."""
        count = self._execute(sql, **params).rowcount
        if count != 1:
            raise StoreInvariantError(f"{count} rows instead of one: {sql}")

    def _fetch_one(self, sql: str, **params: Any) -> dict | None:
        cursor = self._execute(sql, **params)
        row = cursor.fetchone()
        return None if row is None else dict(zip((d[0] for d in cursor.description), row))

    def _fetch_all(self, sql: str, **params: Any) -> list[dict]:
        cursor = self._execute(sql, **params)
        names = [d[0] for d in cursor.description]
        return [dict(zip(names, row)) for row in cursor.fetchall()]

    def _decode(self, row: dict) -> dict:
        for column in row.keys() & _TIME_COLUMNS:
            if row[column] is not None:
                row[column] = self.dialect.parse_time(row[column])
        for column in row.keys() & _JSON_COLUMNS:
            row[column] = json.loads(row[column])
        if "status" in row:
            row["status"] = Status(row["status"])
        if "outcome" in row:
            row["outcome"] = Outcome(row["outcome"])
        return row

    def _time(self, value: datetime) -> Any:
        return self.dialect.time(value)


def _json(value: dict) -> str:
    return json.dumps(value, sort_keys=True)
