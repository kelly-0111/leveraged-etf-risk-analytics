"""The MySQL side of the job store: its dialect, a connection, and the schema.

MySQLDialect rewrites the store's ':name' parameters into PyMySQL's '%(name)s' and passes
times as naive UTC datetimes, which DATETIME(6) stores unchanged. connect_mysql() opens a
connection the store can use:
- autocommit on, so a read outside the store's transactions sees the latest committed
  state, not an old REPEATABLE READ snapshot; the store's START TRANSACTION ... COMMIT
  blocks are transactions all the same;
- CLIENT_FOUND_ROWS on unless found_rows=False, so affected rows count matched rows (the
  store's version column makes MySQL's default count, changed rows, work as well);
- the isolation level set explicitly, REPEATABLE READ unless told otherwise;
- optionally, bounded waits: connect, read and write timeouts on the client, and the
  session's lock wait timeout and wait_timeout (SERVICE_SESSION holds the values the job
  processes use).
connector() returns a function that opens such a connection, for JobStore(connect=...),
which reconnects with it after a disconnect (is_disconnect). create_schema() runs
schema/mysql.sql one statement at a time.

PyMySQL is in the `jobs` dependency group (uv run --group jobs). MySQL 8's default
authentication (caching_sha2_password) over a connection without TLS needs PyMySQL's "rsa"
extra.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_mysql.py,
offline and against MySQL 8.4.13 (docker/compose.yaml).
"""
from __future__ import annotations

import functools
import re
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any
from urllib.parse import unquote, urlsplit

from etf_risk.jobs.store import SCHEMA_DIR

ISOLATION_LEVELS = frozenset({"READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"})
CONFLICT_ERRORS = frozenset({1205, 1213})   # lock wait timeout, deadlock
# The connection is gone: can't connect (2003), server has gone away (2006), lost connection
# (2013, also a read or write timeout), server shutdown (1053), connection killed (1927),
# disconnected for inactivity (4031).
DISCONNECT_ERRORS = frozenset({2003, 2006, 2013, 1053, 1927, 4031})
# Session settings of the worker, the reconciler and submit (docs/job-queue.md, "Settings").
# The timeouts bound each wait for the server; they keep the processes responsive and are not
# part of any safety argument. The lock wait timeout stays below the read timeout, so a lock
# wait ends as a definite conflict (1205) rather than an ambiguous client timeout. wait_timeout
# bounds how long a frozen client's open transaction can hold row locks.
SERVICE_SESSION = {"connect_timeout": 3, "read_timeout": 5, "write_timeout": 5, "lock_wait_timeout": 2,
                   "wait_timeout": 120}


class MySQLDialect:
    name = "mysql"
    begin = "START TRANSACTION"

    @staticmethod
    def sql(text: str) -> str:
        """':name' -> '%(name)s', after doubling any '%' (the store's SQL has none, and no other colons)."""
        return re.sub(r":(\w+)", r"%(\1)s", text.replace("%", "%%"))

    @staticmethod
    def time(value: datetime) -> datetime:
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def parse_time(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc)

    @staticmethod
    def is_conflict(error: BaseException) -> bool:
        """A PyMySQL error for a lock wait timeout or a deadlock. After a deadlock InnoDB has
        rolled the whole transaction back; after a timeout only the statement, and the
        store's ROLLBACK undoes the rest."""
        return (type(error).__module__.startswith("pymysql") and len(error.args) > 0
                and error.args[0] in CONFLICT_ERRORS)

    @staticmethod
    def is_disconnect(error: BaseException) -> bool:
        """A PyMySQL error saying the connection is gone (DISCONNECT_ERRORS), or any
        InterfaceError, which PyMySQL raises for a connection already closed."""
        if not type(error).__module__.startswith("pymysql"):
            return False
        if type(error).__name__ == "InterfaceError":
            return True
        return len(error.args) > 0 and error.args[0] in DISCONNECT_ERRORS

    @staticmethod
    def ping(connection: Any) -> None:
        """Raises if the server no longer answers. Never reconnect=True: PyMySQL's reconnect
        would drop the session settings that connect_mysql() set."""
        connection.ping(reconnect=False)


MYSQL = MySQLDialect()


def connection_options(url: str, database: str | None = None) -> dict:
    """mysql://user:password@host:port[/database] as PyMySQL's connect() arguments; database
    overrides the URL's."""
    parts = urlsplit(url)
    if parts.scheme != "mysql":
        raise ValueError(f"expected a mysql:// URL, not {parts.scheme}://")
    return {"host": parts.hostname or "127.0.0.1", "port": parts.port or 3306,
            "user": unquote(parts.username or "root"), "password": unquote(parts.password or ""),
            "database": database or parts.path.lstrip("/") or None}


def connect_mysql(url: str, *, database: str | None = None, found_rows: bool = True,
                  isolation: str = "REPEATABLE READ", lock_wait_timeout: int | None = None,
                  connect_timeout: float | None = None, read_timeout: float | None = None,
                  write_timeout: float | None = None, wait_timeout: int | None = None) -> Any:
    """A PyMySQL connection for JobStore(connection, MYSQL). lock_wait_timeout sets the
    session's innodb_lock_wait_timeout and wait_timeout its wait_timeout, in seconds; the
    other timeouts are PyMySQL's, per connection attempt and per read or write. None leaves
    a setting at its default."""
    import pymysql
    from pymysql.constants import CLIENT

    if isolation not in ISOLATION_LEVELS:
        raise ValueError(f"unknown isolation level: {isolation!r}")
    timeouts = {name: value for name, value in (("connect_timeout", connect_timeout), ("read_timeout", read_timeout),
                                                ("write_timeout", write_timeout)) if value is not None}
    conn = pymysql.connect(**connection_options(url, database), charset="utf8mb4", autocommit=True,
                           client_flag=CLIENT.FOUND_ROWS if found_rows else 0, **timeouts)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation}")
            if lock_wait_timeout is not None:
                cursor.execute("SET SESSION innodb_lock_wait_timeout = %s", (int(lock_wait_timeout),))
            if wait_timeout is not None:
                cursor.execute("SET SESSION wait_timeout = %s", (int(wait_timeout),))
    except BaseException:
        conn.close()
        raise
    return conn


def connector(url: str, *, database: str | None = None, **settings: Any) -> Callable[[], Any]:
    """A function that opens a new connection with these settings, for JobStore(connect=...)."""
    return functools.partial(connect_mysql, url, database=database, **settings)


def schema_statements() -> list[str]:
    """schema/mysql.sql as separate statements. Comments go first, since they contain
    semicolons (the schema's string literals contain no '--')."""
    lines = (line.split("--", 1)[0] for line in (SCHEMA_DIR / "mysql.sql").read_text().splitlines())
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def create_schema(connection: Any) -> None:
    """The job tables, in the connection's database."""
    with connection.cursor() as cursor:
        for statement in schema_statements():
            cursor.execute(statement)
