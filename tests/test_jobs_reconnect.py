"""The job store after a lost connection, offline: a SQLite connection that breaks on cue
stands in for a database restart (tests/test_jobs_mysql.py repeats this against MySQL).

The store replaces a broken connection only at the start of an operation, never inside a
transaction: a transaction whose connection broke after its first statement is abandoned
(the database rolls it back), and its remaining statements never run on a new connection.
The operation that saw the break raises; nothing is replayed. A COMMIT whose reply was lost
may have taken effect, and repeating accept_result() then reports the acceptance.

AI contribution: written with Claude Code (Opus 5.5).
"""
import pytest

from etf_risk.jobs import store as store_module
from etf_risk.jobs.simulated import ManualClock
from etf_risk.jobs.store import IDLE_PING, JobStore, Outcome, SQLiteDialect, Status, open_sqlite
from jobs_backends import DIGEST, LEASE


class Dropped(Exception):
    """The tests' lost connection."""


class DroppingDialect(SQLiteDialect):
    @staticmethod
    def is_disconnect(error):
        return isinstance(error, Dropped)

    @staticmethod
    def ping(connection):
        connection.ping()


class Connection:
    """A SQLite connection that breaks on cue. drop_at=n breaks it as its n-th statement is
    sent (1 is the first BEGIN): the statement does not run, and closing the connection rolls
    back the open transaction, as a server does when a session ends. commit_then_drop runs a
    COMMIT and then breaks before its reply. ping_fails makes ping() fail."""

    def __init__(self, path, *, drop_at=None, commit_then_drop=False, ping_fails=False):
        self.inner = open_sqlite(path)
        self.statements: list[str] = []
        self.drop_at, self.commit_then_drop, self.ping_fails = drop_at, commit_then_drop, ping_fails
        self.open = True

    def cursor(self):
        return Cursor(self)

    def ping(self):
        if self.ping_fails or not self.open:
            raise Dropped("no answer to the ping")

    def close(self):
        if self.open:
            self.open = False
            self.inner.close()


class Cursor:
    def __init__(self, connection):
        self.connection, self.inner = connection, None

    def execute(self, sql, params=()):
        c = self.connection
        if not c.open:
            raise Dropped("the connection is closed")
        c.statements.append(sql)
        if c.drop_at == len(c.statements):
            c.close()
            raise Dropped(f"lost at statement {len(c.statements)}")
        self.inner = c.inner.execute(sql, params)
        if c.commit_then_drop and sql == "COMMIT":
            c.close()
            raise Dropped("the COMMIT's reply was lost")
        return self

    def __getattr__(self, name):                   # rowcount, lastrowid, description, fetchone, fetchall
        return getattr(self.inner, name)


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "jobs.sqlite"
    open_sqlite(path, create=True).close()
    return path


def reconnecting(db, *connections):
    """A store that opens the given connections, one per (re)connect."""
    supply = iter(connections)
    return JobStore(None, DroppingDialect(), clock=ManualClock(), lease=LEASE, connect=lambda: next(supply))


def test_a_transaction_that_broke_is_abandoned_and_never_continued_on_a_new_connection(db):
    first, second = Connection(db), Connection(db)
    store = reconnecting(db, first, second)
    job = store.submit({"n": 1}, {})                               # on `first`: BEGIN, INSERT, COMMIT
    first.drop_at = len(first.statements) + 3                      # the claim's BEGIN, UPDATE jobs, then lost
    with pytest.raises(Dropped):
        store.claim(job, "worker-A", "runs")
    assert store.connection is None                                # dropped, not replaced inside the operation
    assert second.statements == []                                 # nothing of the claim went to the new connection
    assert store.job(job)["status"] is Status.QUEUED               # the UPDATE rolled back with the session
    assert store.attempts(job) == []
    assert second.statements[0].startswith("SELECT")               # the next operation opened `second`
    assert store.claim(job, "worker-A", "runs").attempt_number == 1


def test_a_lost_commit_reply_is_not_replayed_and_a_repeat_reports_the_acceptance(db):
    first, second = Connection(db), Connection(db)
    store = reconnecting(db, first, second)
    job = store.submit({"n": 1}, {})
    a = store.claim(job, "worker-A", "runs")
    first.commit_then_drop = True
    with pytest.raises(Dropped):
        store.accept_result(a, DIGEST)                             # applied, but the caller cannot know
    assert [s for s in first.statements if s.startswith("UPDATE jobs SET status = 'succeeded'")] != []
    assert store.accept_result(a, DIGEST) is True                  # on `second`: the acceptance is reported
    attempts = store.attempts(job)
    assert [(x["outcome"], x["result_digest"]) for x in attempts] == [(Outcome.ACCEPTED, DIGEST)]
    assert store.invariant_violations() == {}


def test_a_read_on_its_own_reconnects_too(db):
    first, second = Connection(db), Connection(db)
    store = reconnecting(db, first, second)
    job = store.submit({"n": 1}, {})
    first.drop_at = len(first.statements) + 1
    with pytest.raises(Dropped):
        store.job(job)
    assert store.job(job)["status"] is Status.QUEUED and second.statements


def test_an_idle_connection_that_fails_its_ping_is_replaced_first(db, monkeypatch):
    first, second = Connection(db), Connection(db)
    store = reconnecting(db, first, second)
    job = store.submit({"n": 1}, {})
    first.ping_fails = True
    now = store_module.time.monotonic()
    monkeypatch.setattr(store_module.time, "monotonic", lambda: now + IDLE_PING + 1)
    assert store.job(job)["status"] is Status.QUEUED               # pinged, dropped, reconnected: no error
    assert store.connection is second and not first.open


def test_without_a_way_to_reconnect_a_broken_store_says_so(db):
    connection = Connection(db)
    store = JobStore(connection, DroppingDialect(), clock=ManualClock(), lease=LEASE)
    job = store.submit({"n": 1}, {})
    connection.drop_at = len(connection.statements) + 1
    with pytest.raises(Dropped):
        store.job(job)
    with pytest.raises(ConnectionError, match="no way to reconnect"):
        store.job(job)


def test_a_store_needs_a_connection_or_a_way_to_connect():
    with pytest.raises(ValueError):
        JobStore(None, DroppingDialect())
