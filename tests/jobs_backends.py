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
WorkerEnv adds workers and the guarantee check for one job. KafkaTopic gives a test a topic
of its own on the broker at ETF_RISK_KAFKA_BOOTSTRAP; without it, the Kafka tests skip.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import closing
from datetime import timedelta
from pathlib import Path

import pytest

from etf_risk.jobs.queue import submit_job
from etf_risk.jobs.reconciler import Reconciler
from etf_risk.jobs.simulated import ManualClock, MemoryQueue, SimulatedPipeline, result_digest
from etf_risk.jobs.store import SQLITE, JobStore, Outcome, Status, open_sqlite
from etf_risk.jobs.worker import Handled, Result, Worker

MYSQL_URL = os.environ.get("ETF_RISK_MYSQL_URL")
BACKENDS = ["sqlite", "mysql"] if MYSQL_URL else ["sqlite"]
needs_mysql = pytest.mark.skipif(not MYSQL_URL, reason="set ETF_RISK_MYSQL_URL to run against MySQL")
KAFKA_BOOTSTRAP = os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP")
needs_kafka = pytest.mark.skipif(not KAFKA_BOOTSTRAP, reason="set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka")
LEASE = timedelta(seconds=60)
PARAMS = {"snapshot": "simulated", "stride": 21}
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


class WorkerEnv(JobsEnv):
    """A job table, an admin store for submitting and inspecting, and workers with a connection each."""

    def __init__(self, backend, tmp_path):
        super().__init__(backend, tmp_path)
        self.admin = self.new_store()
        self.handled: list[Handled] = []
        self.acks: list[int] = []

    def worker(self, name, pipeline=None, fault=None, store_fault=None) -> Worker:
        return Worker(self.new_store(fault=store_fault), pipeline or SimulatedPipeline(), self.runs,
                      worker_id=f"worker-{name}", fault=fault)

    def deliver(self, worker: Worker, job_id: int) -> Handled:
        handled = worker.handle(job_id, lambda: self.acks.append(job_id))
        self.handled.append(handled)
        return handled

    def check(self, job_id: int, *, lost_acceptances: int = 0) -> None:
        """The guarantee for one job: no invariant violation; at most one accepted attempt,
        exactly one if the job succeeded, as many as the deliveries told "accepted" plus any
        acceptance whose worker died before it could tell; that attempt's result in its
        folder; no two attempts sharing a folder."""
        assert self.admin.invariant_violations() == {}
        job, attempts = self.admin.job(job_id), self.admin.attempts(job_id)
        accepted = [a for a in attempts if a["outcome"] is Outcome.ACCEPTED]
        told = [h for h in self.handled if h.job_id == job_id and h.result is Result.ACCEPTED]
        assert len(accepted) == len(told) + lost_acceptances == (1 if job["status"] is Status.SUCCEEDED else 0)
        for a in accepted:
            assert job["accepted_attempt"] == a["attempt_number"]
            assert json.loads((Path(a["output_dir"]) / "result.json").read_text()) == {
                "job_id": job_id, "attempt_number": a["attempt_number"], "run_id": a["run_id"],
                "result_sha256": result_digest(job["params"])}
        assert all(h.claim.attempt_number == job["accepted_attempt"] for h in told)
        assert len({a["output_dir"] for a in attempts}) == len(attempts)


def failing_at(point, times=None):
    """A store fault hook raising RuntimeError when it passes point: the first `times` times,
    or every time (None). fault.calls counts the passes."""
    def fault(at):
        if at == point:
            fault.calls += 1
            if times is None or fault.calls <= times:
                raise RuntimeError(f"injected at {point}")
    fault.calls = 0
    return fault


class QueueEnv(WorkerEnv):
    """WorkerEnv with an in-memory queue, and helpers to submit, reconcile and serve."""

    def __init__(self, backend, tmp_path):
        super().__init__(backend, tmp_path)
        self.queue = MemoryQueue()

    def submit(self, outcomes=(), **kwargs):
        """Submit a job (PARAMS) through submit_job(); outcomes decide its publication."""
        return submit_job(self.admin, self.queue.publisher(outcomes), PARAMS, {}, **kwargs)

    def reconciler(self, outcomes=(), **options) -> Reconciler:
        return Reconciler(self.new_store(), self.queue.publisher(outcomes), **options)

    def serve(self, worker, group="workers", **options):
        """worker serves a new consumer of the group (a restarted worker) until the queue is idle."""
        return worker.serve(self.queue.consumer(group), stop_when_idle=True, retry_delay=0,
                            on_handled=self.handled.append, **options)


class KafkaTopic:
    """A topic of its own for one test, with fresh consumer group names; close() closes the
    consumers it opened and deletes the topic."""

    def __init__(self):
        pytest.importorskip("confluent_kafka")
        from etf_risk.jobs import kafka
        self._kafka, self.bootstrap = kafka, KAFKA_BOOTSTRAP
        self.name = f"etf-jobs-test-{secrets.token_hex(4)}"
        self.consumers = []
        kafka.create_topic(self.bootstrap, self.name)

    def group(self) -> str:
        return f"{self.name}-group-{secrets.token_hex(3)}"

    def publisher(self, **options):
        return self._kafka.KafkaPublisher(self.bootstrap, self.name, **options)

    def produce_raw(self, value: bytes) -> None:
        """Write a message that KafkaPublisher would not write, and wait until it is written."""
        from confluent_kafka import Producer
        producer = Producer({"bootstrap.servers": self.bootstrap, "acks": "all"})
        producer.produce(self.name, value=value)
        assert producer.flush(30) == 0, "the raw message was not written"

    def consumer(self, group: str, **options):
        consumer = self._kafka.KafkaConsumer(self.bootstrap, self.name, group, **options)
        self.consumers.append(consumer)
        return consumer

    def close(self) -> None:
        for consumer in self.consumers:
            consumer.close()
        self._kafka.delete_topic(self.bootstrap, self.name)


def poll_deliveries(consumer, count: int, *, timeout: float = 30.0) -> list:
    """The next `count` deliveries, or fewer if they do not come within timeout seconds. The
    first poll of a new consumer also waits for the group to give it its partition."""
    deliveries, deadline = [], time.monotonic() + timeout
    while len(deliveries) < count and time.monotonic() < deadline:
        if (delivery := consumer.poll(0.5)) is not None:
            deliveries.append(delivery)
    return deliveries


def poll_after_assignment(consumer, *, settle: float = 3.0, timeout: float = 30.0) -> list:
    """Everything the consumer receives until `settle` seconds after it got its partition."""
    deliveries, deadline = [], time.monotonic() + timeout
    while not consumer.assigned() and time.monotonic() < deadline:
        if (delivery := consumer.poll(0.5)) is not None:
            deliveries.append(delivery)
    assert consumer.assigned(), "the consumer never got its partition"
    until = time.monotonic() + settle
    while time.monotonic() < until:
        if (delivery := consumer.poll(0.5)) is not None:
            deliveries.append(delivery)
    return deliveries


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
