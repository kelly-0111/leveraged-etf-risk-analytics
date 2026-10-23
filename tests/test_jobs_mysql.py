"""The MySQL adapter offline, and the MySQL behaviour the job store relies on, against a server.

Offline, always: the dialect's parameters and times for every statement the store sends, the
schema split into statements, connection options from a URL, and the conflict check.
Against MySQL (skipped unless ETF_RISK_MYSQL_URL is set): an UPDATE reads the latest committed
row whatever the transaction's snapshot; affected rows without CLIENT_FOUND_ROWS; SET clauses
evaluated left to right; competing claims under READ COMMITTED; lock wait timeouts run again.
With the URL set, tests/test_jobs_store.py and tests/test_jobs_worker.py run on MySQL as well,
including connections competing for one job.

To run everything on a local server (docker/compose.yaml):

    docker compose -f docker/compose.yaml up -d --wait mysql
    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --with 'pymysql[rsa]==1.1.1' \\
        pytest tests/test_jobs_store.py tests/test_jobs_worker.py tests/test_jobs_mysql.py
    docker compose -f docker/compose.yaml down -v

AI contribution: written with Claude Code (Opus 5.5).
"""
import re
from contextlib import closing
from datetime import datetime, timedelta, timezone

import pytest

from etf_risk.jobs.mysql import MYSQL, MySQLDialect, connection_options, schema_statements
from etf_risk.jobs.simulated import ManualClock
from etf_risk.jobs.store import Claim, JobStore, Refusal, SQLiteDialect, Status, open_sqlite
from jobs_backends import LEASE, InThread, MySQLBackend, Paused, StoreEnv, needs_mysql


# Offline

def test_the_dialect_rewrites_parameters_and_doubles_percent_signs():
    assert MYSQL.sql("SELECT 1 FROM jobs WHERE job_id = :job_id AND error LIKE 'x%'") == (
        "SELECT 1 FROM jobs WHERE job_id = %(job_id)s AND error LIKE 'x%%'")


def test_times_go_in_as_naive_utc_and_come_back_aware():
    aware = datetime(2026, 1, 1, 12, 0, 0, 123456, tzinfo=timezone(timedelta(hours=2)))
    naive = MYSQL.time(aware)
    assert naive == datetime(2026, 1, 1, 10, 0, 0, 123456) and naive.tzinfo is None
    assert MYSQL.parse_time(naive) == aware


class Recording(SQLiteDialect):
    """SQLite, recording each statement the store sends."""

    def __init__(self):
        self.statements = set()

    def sql(self, text):
        self.statements.add(text)
        return text


def test_every_statement_the_store_sends_converts_to_pymysql_parameters(tmp_path):
    with closing(open_sqlite(tmp_path / "jobs.sqlite", create=True)) as conn:
        statements = send_every_statement(JobStore(conn, Recording(), clock=ManualClock(), lease=LEASE), tmp_path)
    # 24 statements in the operations (insert, mark_published, two claim guards, claim's read,
    # takeover, attempt insert, refusal read, exhaust and its attempt, renew and its attempt,
    # accept, its attempt and its read, fail and its attempt, requeue and its attempt, requeue's
    # read, expired_leases(), unconfirmed(), job(), attempts()) and the 7 invariant queries
    assert len(statements) == 31
    for text in statements:
        converted = MYSQL.sql(text)
        assert sorted(re.findall(r":(\w+)", text)) == sorted(re.findall(r"%\((\w+)\)s", converted))
        assert ":" not in converted and "%" not in re.sub(r"%\(\w+\)s", "", converted)


def send_every_statement(store, root):
    """Takes the store through every path of every operation; returns the statements it sent."""
    clock = store.clock
    job = store.submit({"n": 1}, {})
    assert store.mark_published(job, 0) and store.unconfirmed() == []
    a = store.claim(job, "worker-A", root)
    assert store.renew(a) and store.claim(job, "worker-B", root) is Refusal.LEASE_HELD
    clock.advance(LEASE.total_seconds())
    b = store.claim(job, "worker-B", root)                         # a takeover
    assert not store.accept_result(a) and store.accept_result(b)   # refused (its read), then accepted
    failing = store.submit({"n": 2}, {}, max_attempts=1)
    assert store.fail_attempt(store.claim(failing, "worker-A", root), "boom", retryable=True) is not None
    last = store.submit({"n": 3}, {}, max_attempts=1)
    store.claim(last, "worker-A", root)
    clock.advance(LEASE.total_seconds())
    assert store.claim(last, "worker-B", root) is Refusal.EXHAUSTED
    lapsing = store.submit({"n": 4}, {}, max_attempts=2)
    first = store.claim(lapsing, "worker-A", root)
    clock.advance(LEASE.total_seconds())
    assert [lease.job_id for lease in store.expired_leases()] == [lapsing]
    assert store.requeue_expired(lapsing, first.token) is Status.QUEUED      # the requeue and its attempt
    second = store.claim(lapsing, "worker-B", root)
    clock.advance(LEASE.total_seconds())
    assert store.requeue_expired(lapsing, second.token) is Status.FAILED     # its read, then exhaust
    assert store.job(job) is not None and store.attempts(job) and store.invariant_violations() == {}
    return store.dialect.statements


def test_the_schema_splits_into_its_three_statements():
    statements = schema_statements()
    assert [s.split()[:3] for s in statements] == [
        ["CREATE", "TABLE", "jobs"], ["CREATE", "TABLE", "job_attempts"], ["ALTER", "TABLE", "jobs"]]
    assert all("--" not in s and s.count("(") == s.count(")") for s in statements)


def test_connection_options_come_from_the_url():
    assert connection_options("mysql://jobs:p%40ss@db.local:3307/etf") == {
        "host": "db.local", "port": 3307, "user": "jobs", "password": "p@ss", "database": "etf"}
    assert connection_options("mysql://root@127.0.0.1", database="other")["database"] == "other"
    with pytest.raises(ValueError):
        connection_options("postgres://root@127.0.0.1")


def test_lock_conflicts_are_recognised_by_their_error_codes():
    pymysql_error = type("OperationalError", (Exception,), {"__module__": "pymysql.err"})
    assert MYSQL.is_conflict(pymysql_error(1213, "Deadlock found")) and MYSQL.is_conflict(
        pymysql_error(1205, "Lock wait timeout exceeded"))
    assert not MYSQL.is_conflict(pymysql_error(1062, "Duplicate entry"))
    assert not MYSQL.is_conflict(OSError(1213, "not from PyMySQL"))


# Against MySQL

@pytest.fixture
def mysql_env(tmp_path):
    env = StoreEnv(MySQLBackend(), tmp_path)
    yield env
    env.close()


@needs_mysql
def test_an_update_reads_the_latest_committed_row_not_the_transactions_snapshot(mysql_env):
    env = mysql_env
    job = env.store.submit({"n": 1}, {})
    with closing(env.backend.connect()) as conn, conn.cursor() as cursor:
        cursor.execute("START TRANSACTION")
        cursor.execute("SELECT status FROM jobs WHERE job_id = %s", (job,))
        assert cursor.fetchone() == ("queued",)                    # this transaction's snapshot
        assert isinstance(env.store.claim(job, "worker-A", env.runs), Claim)   # committed meanwhile
        cursor.execute("SELECT status FROM jobs WHERE job_id = %s", (job,))
        assert cursor.fetchone() == ("queued",)                    # REPEATABLE READ: still the snapshot
        cursor.execute("UPDATE jobs SET version = version + 1 WHERE job_id = %s AND status = 'queued'", (job,))
        assert cursor.rowcount == 0                                # the UPDATE saw the committed row
        cursor.execute("ROLLBACK")


@needs_mysql
def test_affected_rows_count_changed_rows_unless_found_rows_is_set(mysql_env):
    env = mysql_env
    job = env.store.submit({"n": 1}, {})
    for found_rows, expected in ((False, 0), (True, 1)):
        with closing(env.backend.connect(found_rows=found_rows)) as conn, conn.cursor() as cursor:
            cursor.execute("UPDATE jobs SET max_attempts = max_attempts WHERE job_id = %s", (job,))
            assert cursor.rowcount == expected


@needs_mysql
def test_version_keeps_a_same_instant_renewal_a_match_without_found_rows(mysql_env):
    """Renewing twice at one clock reading sets the same lease twice; only version changes,
    and that is enough for the store to see its guard matched."""
    env = mysql_env
    job = env.store.submit({"n": 1}, {})
    store = env.new_store(connection=env.backend.connect(found_rows=False))
    a = store.claim(job, "worker-A", env.runs)
    assert store.renew(a) and store.renew(a)                       # the clock has not moved


@needs_mysql
def test_single_table_set_clauses_run_left_to_right(mysql_env):
    with closing(mysql_env.backend.connect()) as conn, conn.cursor() as cursor:
        cursor.execute("CREATE TABLE set_order (a INT, b INT)")
        cursor.execute("INSERT INTO set_order VALUES (1, 0)")
        cursor.execute("UPDATE set_order SET a = a + 1, b = a")
        cursor.execute("SELECT a, b FROM set_order")
        assert cursor.fetchone() == (2, 2)          # b got the new a; standard SQL (and SQLite) give (2, 1)


@needs_mysql
def test_competing_claims_under_read_committed(mysql_env):
    """READ COMMITTED releases the lock of a row an UPDATE did not match; the guards still decide."""
    env = mysql_env
    job = env.store.submit({"n": 1}, {})
    first = Paused(env, lambda store: store.claim(job, "worker-A", env.runs), "claim.jobs_updated",
                   isolation="READ COMMITTED").start()
    second = InThread(env, lambda store: store.claim(job, "worker-B", env.runs), isolation="READ COMMITTED").start()
    assert env.backend.lock_waiting(second.connection)
    assert isinstance(first.resume(), Claim) and second.outcome() is Refusal.LEASE_HELD
    assert env.store.invariant_violations() == {}


class CountingConflicts(MySQLDialect):
    def __init__(self):
        self.conflicts = 0

    def is_conflict(self, error):
        found = super().is_conflict(error)
        self.conflicts += found
        return found


@needs_mysql
def test_a_lock_wait_timeout_runs_the_claim_again(mysql_env):
    env = mysql_env
    job = env.store.submit({"n": 1}, {})
    holder = Paused(env, lambda store: store.claim(job, "worker-A", env.runs), "claim.jobs_updated").start()
    dialect = CountingConflicts()
    waiting = InThread(env, lambda store: store.claim(job, "worker-B", env.runs), dialect=dialect,
                       lock_wait_timeout=1).start()
    waiting.thread.join(timeout=1.6)                                # its first run times out after 1 s
    assert isinstance(holder.resume(), Claim)
    assert waiting.outcome() is Refusal.LEASE_HELD and dialect.conflicts >= 1


@needs_mysql
def test_a_claim_gives_up_while_the_lock_stays_held(mysql_env):
    env = mysql_env
    job = env.store.submit({"n": 1}, {})
    holder = Paused(env, lambda store: store.claim(job, "worker-A", env.runs), "claim.jobs_updated").start()
    dialect = CountingConflicts()
    waiting = InThread(env, lambda store: store.claim(job, "worker-B", env.runs), dialect=dialect,
                       lock_wait_timeout=1).start()
    with pytest.raises(env.backend.errors) as raised:
        waiting.outcome()                                           # three runs, each timed out
    assert raised.value.args[0] == 1205 and dialect.conflicts == 2  # two ran it again; the third is raised
    assert isinstance(holder.resume(), Claim) and env.store.invariant_violations() == {}
