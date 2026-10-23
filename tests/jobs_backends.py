"""Backends and helpers for the job-store tests: SQLite always, MySQL when ETF_RISK_MYSQL_URL is set.

A backend holds a fresh job table for one test. connect() opens a connection to it that may
be handed to another thread (one thread at a time); execute() runs one statement outside the
store, with ':name' parameters; dump() reads both tables as a new connection sees them;
violation() names the constraint an error reports. The MySQL backend creates a database of
its own and drops it afterwards; it needs PyMySQL and a server (see tests/test_jobs_mysql.py).
Without ETF_RISK_MYSQL_URL, BACKENDS holds SQLite only, so the default run neither runs nor
lists MySQL variants.

InThread and Paused run a store operation in a thread, Paused holding it at a fault point
inside its transaction, so that another connection can compete with an open transaction.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import closing
from datetime import timedelta

import pytest

from etf_risk.jobs.simulated import ManualClock
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite

MYSQL_URL = os.environ.get("ETF_RISK_MYSQL_URL")
BACKENDS = ["sqlite", "mysql"] if MYSQL_URL else ["sqlite"]
needs_mysql = pytest.mark.skipif(not MYSQL_URL, reason="set ETF_RISK_MYSQL_URL to run against MySQL")
LEASE = timedelta(seconds=60)
DUMP = ("SELECT * FROM jobs ORDER BY job_id", "SELECT * FROM job_attempts ORDER BY job_id, attempt_number")


class SQLiteBackend:
    name = "sqlite"
    dialect = SQLITE
    errors = (sqlite3.IntegrityError,)

    def __init__(self, tmp_path):
        self.path = tmp_path / "jobs.sqlite"
        open_sqlite(self.path, create=True).close()

    def connect(self):
        return open_sqlite(self.path, check_same_thread=False)

    def execute(self, sql, **params):
        with closing(self.connect()) as conn:
            conn.execute(sql, params)

    def dump(self):
        with closing(sqlite3.connect(self.path)) as conn:
            return tuple(conn.execute(sql).fetchall() for sql in DUMP)

    @staticmethod
    def violation(error):
        """("check", name), ("foreign key", None) or ("unique", None) for a constraint error."""
        message = str(error)
        if match := re.match(r"CHECK constraint failed: (\w+)", message):
            return "check", match.group(1)
        if message.startswith("FOREIGN KEY constraint failed"):
            return "foreign key", None
        if message.startswith("UNIQUE constraint failed"):
            return "unique", None
        return None

    def close(self):
        pass


class MySQLBackend:
    name = "mysql"
    CHECK_VIOLATED, NO_REFERENCED_ROW, DUPLICATE_ENTRY = 3819, 1452, 1062

    def __init__(self):
        pymysql = pytest.importorskip("pymysql")
        from etf_risk.jobs import mysql
        self._mysql, self.dialect, self.errors = mysql, mysql.MYSQL, (pymysql.MySQLError,)
        self.database = f"etf_jobs_test_{secrets.token_hex(4)}"
        self._admin(f"CREATE DATABASE {self.database}")
        try:
            with closing(self.connect()) as conn:
                mysql.create_schema(conn)
        except BaseException:
            self.close()
            raise

    def connect(self, **options):
        options.setdefault("lock_wait_timeout", 10)
        return self._mysql.connect_mysql(MYSQL_URL, database=self.database, **options)

    def execute(self, sql, **params):
        with closing(self.connect()) as conn, conn.cursor() as cursor:
            cursor.execute(self.dialect.sql(sql), params)

    def dump(self):
        with closing(self.connect()) as conn, conn.cursor() as cursor:
            tables = []
            for sql in DUMP:
                cursor.execute(sql)
                tables.append(cursor.fetchall())
            return tuple(tables)

    @classmethod
    def violation(cls, error):
        code, message = error.args[0], str(error.args[1])
        if code == cls.CHECK_VIOLATED:
            return "check", re.search(r"constraint '(\w+)'", message).group(1)
        return {cls.NO_REFERENCED_ROW: ("foreign key", None), cls.DUPLICATE_ENTRY: ("unique", None)}.get(code)

    def lock_waiting(self, connection, timeout=10.0):
        """Whether the connection's transaction comes to wait for an InnoDB row lock within timeout seconds."""
        deadline = time.monotonic() + timeout
        with closing(self.connect()) as conn, conn.cursor() as cursor:
            while time.monotonic() < deadline:
                cursor.execute("SELECT trx_state FROM information_schema.INNODB_TRX WHERE trx_mysql_thread_id = %s",
                               (connection.thread_id(),))
                row = cursor.fetchone()
                if row is not None and row[0] == "LOCK WAIT":
                    return True
                time.sleep(0.05)
        return False

    def close(self):
        self._admin(f"DROP DATABASE IF EXISTS {self.database}")

    def _admin(self, statement):
        with closing(self._mysql.connect_mysql(MYSQL_URL)) as conn, conn.cursor() as cursor:
            cursor.execute("SET SESSION lock_wait_timeout = 30")   # a metadata lock left behind fails, not hangs
            cursor.execute(statement)


def make_backend(name, tmp_path):
    return SQLiteBackend(tmp_path) if name == "sqlite" else MySQLBackend()


class JobsEnv:
    """A fresh job table on one backend, a manual clock, and the connections and threads a test opened."""
    lease = LEASE

    def __init__(self, backend, tmp_path):
        self.backend, self.runs, self.clock = backend, tmp_path / "runs", ManualClock()
        self.connections, self.threads = [], []

    def new_store(self, *, fault=None, dialect=None, connection=None):
        connection = connection or self.backend.connect()
        self.connections.append(connection)
        return JobStore(connection, dialect or self.backend.dialect, clock=self.clock, lease=self.lease, fault=fault)

    def dump(self):
        return self.backend.dump()

    def close(self):
        for run in self.threads:
            if isinstance(run, Paused):
                run.released.set()
            if run.thread.ident is not None:
                run.thread.join(timeout=10)
        for connection in self.connections:
            connection.close()
        self.backend.close()


class StoreEnv(JobsEnv):
    def __init__(self, backend, tmp_path):
        super().__init__(backend, tmp_path)
        self.store = self.new_store()


class InThread:
    """Runs operation(store) in a thread, on a store with a connection of its own."""

    def __init__(self, env, operation, *, fault=None, dialect=None, **connect_options):
        self.connection = env.backend.connect(**connect_options)
        self.store = env.new_store(fault=fault, dialect=dialect, connection=self.connection)
        self.result = self.error = None
        self.thread = threading.Thread(target=self._run, args=(operation,), daemon=True)
        env.threads.append(self)

    def _run(self, operation):
        try:
            self.result = operation(self.store)
        except BaseException as error:      # raised again by outcome()
            self.error = error

    def start(self):
        self.thread.start()
        return self

    def outcome(self, timeout=60.0):
        """The operation's result once it finished; its exception, if any, is raised here."""
        self.thread.join(timeout)
        assert not self.thread.is_alive(), "the operation did not finish"
        if self.error is not None:
            raise self.error
        return self.result


class Paused(InThread):
    """InThread, held at a fault point inside its transaction until resume()."""

    def __init__(self, env, operation, point, **kwargs):
        self.point, self.inside, self.released = point, threading.Event(), threading.Event()
        super().__init__(env, operation, fault=self._hold, **kwargs)

    def _hold(self, point):
        if point == self.point:
            self.inside.set()
            if not self.released.wait(timeout=60):
                raise RuntimeError(f"never resumed at {point}")

    def start(self):
        super().start()
        assert self.inside.wait(timeout=30), f"never reached {self.point}"
        return self

    def resume(self):
        self.released.set()
        return self.outcome()


def run_together(*functions, timeout=60.0):
    """Runs the functions in threads that start at the same moment; returns their results in
    order, or raises the first exception one of them raised."""
    start = threading.Barrier(len(functions))
    results, errors = [None] * len(functions), []

    def run(index, function):
        try:
            start.wait(timeout)
            results[index] = function()
        except BaseException as error:
            errors.append(error)

    threads = [threading.Thread(target=run, args=item, daemon=True) for item in enumerate(functions)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout)
    assert not any(thread.is_alive() for thread in threads), "a thread did not finish"
    if errors:
        raise errors[0]
    return results
