"""The job system's state transitions, each one transaction of conditional SQL.

JobStore holds every SQL statement of the job system. A state change is one UPDATE of
the job's row in jobs whose WHERE clause is the transition's guard, and the number of
rows it matched is the answer: 1, the change happened; 0, it was refused, or the worker
asking has been fenced off. The same transaction records the change in job_attempts,
where every statement must touch exactly one row; anything else raises and rolls back
both tables. Reads only classify a refusal: a write that follows a read carries its own
guard, which checks again what the read saw.

    operation      from -> to                                  guard
    submit         -> queued                                   (insert)
    claim          queued -> running                           status queued
                   running -> running (takeover)               lease expired, attempts left
    renew          running -> running                          status running, the attempt's token
    accept_result  running -> succeeded                        status running, the attempt's token
    fail_attempt   running -> queued (retryable, attempts      status running, the attempt's token
                   left) or running -> failed
    exhaust        running -> failed (inside claim)            lease expired, no attempts left,
                                                               the token claim read

succeeded and failed are terminal. Renewal and acceptance need only status running and
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

MySQL behaviour this SQL is written for, for the MySQL integration tests to confirm: an
UPDATE reads the latest committed version of the row and locks it, so concurrent claims
of one job take effect one after the other; affected rows count only changed rows unless
the connection sets CLIENT_FOUND_ROWS, so every guarded UPDATE also sets
version = version + 1; single-table SET clauses are evaluated left to right, so no SET
expression reads a column assigned earlier in the statement (computed values are
parameters); CHECK constraints are enforced from MySQL 8.0.16. SQLiteDialect is below; the
MySQL dialect and connection are in etf_risk.jobs.mysql.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_store.py and
tests/test_jobs_worker.py, on SQLite and on MySQL 8.4.13.
"""
from __future__ import annotations

import functools
import json
import secrets
import sqlite3
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
DEFAULT_LEASE = timedelta(seconds=60)
DEFAULT_MAX_ATTEMPTS = 3
CONFLICT_RETRIES = 3    # runs of one write operation in all, while the database reports lock conflicts


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

_TIME_COLUMNS = frozenset({"lease_expires_at", "created_at", "updated_at", "finished_at", "claimed_at", "ended_at"})
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
    """The job table's operations, each one transaction on the given connection.

    fault, when given, is called with a name from FAULT_POINTS between the statements of a
    transaction; the tests raise there."""

    def __init__(self, connection: Any, dialect: Dialect, *, clock: Clock | None = None,
                 lease: timedelta = DEFAULT_LEASE, fault: Callable[[str], None] | None = None):
        self.connection = connection
        self.dialect = dialect
        self.clock = clock or SystemClock()
        self.lease = lease
        self._fault = fault or (lambda point: None)

    @_retry_conflicts
    def submit(self, params: dict, input_checksums: dict, *, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> int:
        """Create a queued job and return its id. Publishing it is a separate step (Kafka, later)."""
        now = self._time(self.clock.now())
        with self._transaction():
            return self._execute(
                "INSERT INTO jobs (params, input_checksums, status, max_attempts, attempt_number, version,"
                " created_at, updated_at)"
                " VALUES (:params, :input_checksums, 'queued', :max_attempts, 0, 0, :now, :now)",
                params=_json(params), input_checksums=_json(input_checksums), max_attempts=max_attempts,
                now=now).lastrowid

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
                    " attempt_token = :token, lease_expires_at = :lease_expires_at,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'queued'", **take).rowcount:
                takeover = False
            elif self._execute(
                    "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1,"
                    " attempt_token = :token, lease_expires_at = :lease_expires_at,"
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
    def accept_result(self, claim: Claim) -> bool:
        """Accept this attempt's result. True if it is the job's accepted result, now or
        already (a repeat after a failed COMMIT that took effect); False: fenced off."""
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
                self._write_one("UPDATE job_attempts SET outcome = 'accepted', ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                                job_id=claim.job_id, attempt_number=claim.attempt_number, now=now)
                return True
            return self._fetch_one(
                "SELECT 1 FROM jobs j JOIN job_attempts a"
                " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt"
                " WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token",
                job_id=claim.job_id, token=claim.token) is not None

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

    def job(self, job_id: int) -> dict | None:
        row = self._fetch_one("SELECT * FROM jobs WHERE job_id = :job_id", job_id=job_id)
        return None if row is None else self._decode(row)

    def attempts(self, job_id: int) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all(
            "SELECT * FROM job_attempts WHERE job_id = :job_id ORDER BY attempt_number", job_id=job_id)]

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
        token claim read, so a change in between makes it match nothing."""
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
        cursor = self.connection.cursor()
        cursor.execute(self.dialect.begin)
        try:
            yield
            cursor.execute("COMMIT")
        except BaseException as error:
            # BaseException too: a simulated crash must not leave the transaction open (a real
            # crash closes the connection, and the database rolls back the same way). After a
            # failed COMMIT the ROLLBACK may find nothing left to undo, or fail itself.
            try:
                cursor.execute("ROLLBACK")
            except Exception as rollback_error:
                error.add_note(f"the ROLLBACK after this error failed too: {rollback_error!r}")
            raise

    def _execute(self, sql: str, **params: Any) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(self.dialect.sql(sql), params)
        return cursor

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
