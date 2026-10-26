"""etf_risk.services.redis_client against redis-py as locked (the cache group): what one GET or
SET sends and how long it can block. A fake RESP server on a local socket records every
connection and command, so no Redis is needed; it answers, stays silent, closes at once, or
sends its reply in delayed pieces. These pin the Redis overhead bound in docs/result-cache.md:
no handshake or health-check commands, no retries, at most two connection attempts per
command, a timeout per blocking socket call rather than per command.

    uv run --group cache python -m pytest tests/test_redis_client.py

AI contribution: written with Claude Code (Opus 5.5).
"""
import socket
import threading
import time

import pytest

redis = pytest.importorskip("redis")

from etf_risk.services import redis_client  # noqa: E402

READ = 0.2


def parse_commands(buffer: bytes) -> tuple[list[list[bytes]], bytes]:
    """The complete RESP arrays at the start of buffer, and the rest."""
    commands = []
    while buffer.startswith(b"*") and b"\r\n" in buffer:
        line, rest = buffer.split(b"\r\n", 1)
        args = []
        for _ in range(int(line[1:])):
            if b"\r\n" not in rest:
                return commands, buffer
            head, body = rest.split(b"\r\n", 1)
            size = int(head[1:])
            if len(body) < size + 2:
                return commands, buffer
            args.append(body[:size])
            rest = body[size + 2:]
        commands.append(args)
        buffer = rest
    return commands, buffer


class FakeRedis:
    """mode: "answer" (GET -> nil, SET -> OK), "silent", "close" (close each connection at
    once), or "pieces" (a GET answered in three pieces, PIECE_DELAY apart)."""
    PIECE_DELAY = 0.15

    def __init__(self, mode: str):
        self.mode = mode
        self.connections = 0
        self.commands: list[list[bytes]] = []
        self.listener = socket.create_server(("127.0.0.1", 0))
        self.port = self.listener.getsockname()[1]
        self.open: list[socket.socket] = []
        threading.Thread(target=self._accept, daemon=True).start()

    @property
    def url(self) -> str:
        return f"redis://127.0.0.1:{self.port}/0"

    def _accept(self) -> None:
        while True:
            try:
                conn, _ = self.listener.accept()
            except OSError:
                return
            self.connections += 1
            self.open.append(conn)
            if self.mode == "close":
                conn.close()
                continue
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _serve(self, conn: socket.socket) -> None:
        buffer = b""
        while data := self._recv(conn):
            commands, buffer = parse_commands(buffer + data)
            for command in commands:
                self.commands.append(command)
                if self.mode == "answer":
                    conn.sendall(b"+OK\r\n" if command[0].upper() == b"SET" else b"$-1\r\n")
                elif self.mode == "pieces":
                    for piece in (b"$5\r\nhe", b"ll", b"o\r\n"):
                        conn.sendall(piece)
                        time.sleep(self.PIECE_DELAY)

    @staticmethod
    def _recv(conn: socket.socket) -> bytes:
        try:
            return conn.recv(65536)
        except OSError:
            return b""

    def drop(self) -> None:
        """Close every connection but keep listening, as a restarted server would."""
        for conn in self.open:
            conn.close()

    def close(self) -> None:
        self.listener.close()
        self.drop()


@pytest.fixture
def fake():
    servers = []

    def start(mode: str) -> FakeRedis:
        servers.append(FakeRedis(mode))
        return servers[-1]
    yield start
    for server in servers:
        server.close()


def client_for(url: str):
    return redis_client(url, connect_timeout=READ, read_timeout=READ)


@pytest.mark.parametrize("url", [
    "redis://localhost:6380/0",              # a host name: a DNS lookup, possibly several addresses
    "redis://:secret@127.0.0.1:6380/0",      # AUTH on every connection
    "redis://127.0.0.1:6380/1",              # SELECT on every connection
    "redis://127.0.0.1:6380/0?socket_timeout=5",
    "rediss://127.0.0.1:6380/0",
])
def test_urls_that_would_add_lookups_or_commands_are_refused(url):
    with pytest.raises(ValueError):
        client_for(url)


@pytest.mark.parametrize("url", ["redis://127.0.0.1:6380", "redis://127.0.0.1:6380/0", "redis://[::1]:6380/0"])
def test_ip_addresses_and_database_0_are_accepted(url):
    client_for(url).close()


def test_a_get_and_a_set_send_exactly_their_own_command_on_one_connection(fake):
    server = fake("answer")
    client = client_for(server.url)
    assert client.get("k") is None
    assert client.set("k", b"v") is True
    client.close()
    # no HELLO, CLIENT SETINFO, PING, AUTH, SELECT or CLIENT SETNAME before or between them
    assert server.commands == [[b"GET", b"k"], [b"SET", b"k", b"v"]]
    assert server.connections == 1


def test_a_silent_server_times_out_once_after_the_read_timeout_without_a_retry(fake):
    server = fake("silent")
    client = client_for(server.url)
    start = time.monotonic()
    with pytest.raises(redis.exceptions.TimeoutError):
        client.get("k")
    elapsed = time.monotonic() - start
    client.close()
    assert server.commands == [[b"GET", b"k"]] and server.connections == 1
    assert READ <= elapsed < READ + 1.0      # redis-py's default 10 retries would take over 2 s


def test_a_closed_port_fails_at_once_without_a_retry():
    probe = socket.create_server(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    client = client_for(f"redis://127.0.0.1:{port}/0")
    start = time.monotonic()
    with pytest.raises(redis.exceptions.ConnectionError):
        client.get("k")
    assert time.monotonic() - start < 0.5    # the default backoff alone would sleep longer
    client.close()


def test_a_command_makes_at_most_two_connection_attempts(fake):
    server = fake("close")
    client = client_for(server.url)
    with pytest.raises(redis.exceptions.ConnectionError):
        client.get("k")
    client.close()
    time.sleep(0.1)                          # let the accept thread count the last connection
    # two when the pool sees the close before sending (get_connection reconnects once), else one
    assert 1 <= server.connections <= 2 and server.commands == []


def test_a_pooled_connection_the_server_closed_is_replaced_by_one_new_connection(fake):
    server = fake("answer")
    client = client_for(server.url)
    assert client.get("k") is None
    server.drop()
    time.sleep(0.1)                          # the close reaches the client's socket
    assert client.get("k") is None           # no error: the pool connects again, once
    client.close()
    assert server.connections == 2 and server.commands == [[b"GET", b"k"], [b"GET", b"k"]]


def test_the_read_timeout_bounds_each_recv_not_the_whole_reply(fake):
    server = fake("pieces")
    client = client_for(server.url)
    start = time.monotonic()
    assert client.get("k") == b"hello"
    elapsed = time.monotonic() - start
    client.close()
    # three pieces, each within READ of the last: no timeout, though the reply took longer than READ
    assert elapsed > READ and server.commands == [[b"GET", b"k"]]


def test_a_command_is_sent_in_one_piece_up_to_the_buffer_cutoff_and_three_beyond_it():
    connection = client_for("redis://127.0.0.1:6380/0").connection_pool.make_connection()
    packer = connection._command_packer
    assert type(packer).__name__ == "PythonRespSerializer"     # hiredis is not installed
    assert len(packer.pack("SET", "k", b"v" * 5000)) == 1
    assert len(packer.pack("SET", "k", b"v" * 7000)) == 3
    assert len(packer.pack("GET", "etf-risk:result:v1:overview:" + "0" * 64)) == 1
