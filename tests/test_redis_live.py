"""The Compose redis service and the result cache's client against it: the memory and persistence
settings the spec's budget assumes, and what the server sees of the client (RESP2, no library
name set). Skipped unless ETF_RISK_REDIS_URL names a running server:

    docker compose -f docker/compose.yaml up -d --wait redis
    ETF_RISK_REDIS_URL=redis://127.0.0.1:6380/0 uv run --group cache python -m pytest tests/test_redis_live.py

Each test uses keys under a prefix of its own and deletes them; nothing is flushed.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
import secrets

import pytest

redis = pytest.importorskip("redis")

from etf_risk.services import redis_client, redis_ready  # noqa: E402

URL = os.environ.get("ETF_RISK_REDIS_URL")
pytestmark = pytest.mark.skipif(not URL, reason="set ETF_RISK_REDIS_URL to run against Redis")


@pytest.fixture
def client():
    c = redis_client(URL, connect_timeout=1.0, read_timeout=1.0)
    prefix = f"etf-risk:test:{secrets.token_hex(6)}:"
    c.test_prefix = prefix
    yield c
    keys = list(c.scan_iter(match=prefix + "*"))
    if keys:
        c.delete(*keys)
    c.close()


def test_ready_is_a_ping():
    redis_ready(URL)


def test_the_server_has_the_budgeted_memory_and_no_persistence(client):
    config = {k: v for k, v in client.config_get("*").items()
              if k in ("maxmemory", "maxmemory-policy", "save", "appendonly")}
    assert config == {"maxmemory": "33554432", "maxmemory-policy": "allkeys-lru", "save": "", "appendonly": "no"}


def test_a_value_round_trips(client):
    key = client.test_prefix + "k"
    assert client.set(key, b"\x00value\xff") is True
    assert client.get(key) == b"\x00value\xff"


def test_the_server_sees_resp2_and_no_library_name(client):
    info = client.execute_command("CLIENT", "INFO")
    fields = dict(part.split("=", 1) for part in (info.decode() if isinstance(info, bytes) else info).split())
    assert fields["resp"] == "2" and fields["lib-name"] == "" and fields["lib-ver"] == ""
