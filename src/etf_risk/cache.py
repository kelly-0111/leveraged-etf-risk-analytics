"""The result cache for summary queries: cache-aside in Redis (spec §11).

A cached result is identified by what it is a function of, and by nothing else:
- the cache format version (FORMAT);
- the engine (the PySpark version);
- the run digest: the content of the run's files (etf_risk.runs), never a run id, job id,
  store id or path, which can repeat or move;
- the query name, and the SHA-256 of its SQL text;
- the full parameters: every declared parameter, defaults filled in, in canonical form.
The key is a hash of that identity behind a readable prefix. The stored value repeats the
identity, and a value whose identity differs on read is a miss.

What the identity leaves out is the request's provenance: which job, store or registry entry
made the run servable. Two runs with the same files (another store's job, a registered copy)
share entries, so the provenance a response reports comes from that request's own resolution
(etf_risk.summary), never from the cache.

Behaviour (get_or_compute): a hit returns the stored result; a miss computes, writes the result
back and returns it. Redis failing never fails a query: the result is computed instead, and
nothing is written back in that request. A circuit breaker stops trying Redis after
consecutive failures, for a cooldown, and then lets one request probe it. Exceptions that are
not Redis failures (errors) propagate, and so do compute's; nothing is written then.

Entries are never invalidated: the identity changes whenever anything the result depends on
changes, and Redis evicts entries no request can reach (allkeys-lru, docker/compose.yaml).

The contract is pinned by tests/test_cache_contract.py, step by step (STEP n below).

The cache logic is written by the project author, with tutoring. AI contribution: the
scaffold (this docstring, the signatures and their docstrings, the configuration's fields
and proposed values, ResultCache.__init__) and tests/test_cache_contract.py were written
with Claude Code (Opus 5.5); the function bodies are the author's.
"""
from __future__ import annotations

import copy
import math
import hashlib
import json
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

FORMAT = 1
KEY_PREFIX = "etf-risk:result"


@dataclass(frozen=True)
class Param:
    """A declared query parameter (etf_risk.summary declares them).

    kind "string_set": a set of strings; order and repetition carry no meaning.
    default: its value when a request leaves it out.
    allowed: the values it may hold."""
    kind: str
    default: tuple[str, ...]
    allowed: tuple[str, ...]


# STEP 1

def normalize_params(declared: Mapping[str, Param], given: Mapping[str, Any]) -> dict:
    """The request's parameters in canonical form: a new dict with exactly the declared
    names. For a "string_set" parameter (the author's decisions, 2026-10-25):
    - left out of the request: its default, in canonical form;
    - given: a non-empty list or tuple of strings; each string upper-cased (no other change)
      must be in `allowed`;
    - canonical form: a sorted list without duplicates.
    Raise ValueError for an undeclared name, null, a bare string, an empty list, any other
    value that is not a list or tuple, a ticker that is not a string, or one outside
    `allowed`. `given` and its values are never changed, also when refused."""
    unknown = set(given) - set(declared)
    if unknown:
        raise ValueError(f"Unknown parameters: {sorted(unknown)}")

    result = {}
    for name, param in declared.items():
        values = given[name] if name in given else param.default

        if not isinstance(values, (list, tuple)) or not values:
            raise ValueError(f"{name} must be a non-empty list or tuple")

        normalized = []
        for value in values:
            if not isinstance(value, str):
                raise ValueError(f"{name}: invalid value {value!r}")

            ticker = value.upper()
            if ticker not in param.allowed:
                raise ValueError(f"{name}: invalid ticker {value!r}")

            normalized.append(ticker)

        result[name] = sorted(set(normalized))

    return result


# STEP 2

def identity(*, run_digest: str, query: str, sql: str, params: Mapping[str, Any], engine: str) -> dict:
    """The cached result's identity, as a dict with exactly these fields:
    format (FORMAT), engine, run_digest, query, sql_sha256 (SHA-256 of sql as UTF-8, hex),
    and params: a deep copy of the already normalized params (the author's decision,
    2026-10-25), so that later changes to the caller's dict or to its lists cannot change
    the identity or its key."""
    return {
        "format": FORMAT,
        "engine": engine,
        "run_digest": run_digest,
        "query": query,
        "sql_sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
        "params": copy.deepcopy(params),
    }


def cache_key(ident: Mapping[str, Any]) -> str:
    """The Redis key: f"{KEY_PREFIX}:v{ident['format']}:{ident['query']}:<hex SHA-256 of the
    identity>", the identity written as canonical JSON. The prefix names the identity's own
    format (the author's decision, 2026-10-25) and is for people reading keys; the hash
    decides. Equal identities give equal keys in every process."""
    canonical = json.dumps(ident, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"{KEY_PREFIX}:v{ident['format']}:{ident['query']}:{digest}"


# STEP 3

def encode(ident: Mapping[str, Any], result: Mapping[str, Any]) -> bytes:
    """The stored value: {"identity": ident, "result": result} as standard JSON in UTF-8, the
    same bytes for equal input. NaN and infinity are refused with ValueError (the author's
    decisions, 2026-10-25).

    result is {"columns": [[name, Spark type], ...], "rows": [[value, ...], ...]}; values
    are str, int, float, bool or None."""
    payload = {"identity": dict(ident), "result": dict(result)}
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def decode(raw: bytes, ident: Mapping[str, Any]) -> dict | None:
    """The result stored in raw, equal to what encode() was given, value types included.
    None (a miss), never an exception, when raw is not UTF-8 JSON, is not an object with
    "identity" and "result", holds another identity, or has a result of another shape. The
    shape (the author's decisions, 2026-10-25): an object whose "columns" and "rows" are
    lists; each column a list of two strings; each row a list as long as "columns"."""
    def reject_constant(value):
        raise ValueError(f"Invalid JSON constant: {value}")

    try:
        payload = json.loads(
            raw.decode("utf-8"),
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None
    if payload.get("identity") != dict(ident):
        return None

    result = payload.get("result")
    if not isinstance(result, dict):
        return None

    columns = result.get("columns")
    rows = result.get("rows")
    if not isinstance(columns, list) or not isinstance(rows, list):
        return None

    for column in columns:
        if (
            not isinstance(column, list)
            or len(column) != 2
            or not all(isinstance(item, str) for item in column)
        ):
            return None

    for row in rows:
        if not isinstance(row, list) or len(row) != len(columns):
            return None
        for value in row:
            if value is not None and type(value) not in (
                str, int, float, bool
            ):
                return None
            if isinstance(value, float) and not math.isfinite(value):
                return None

    return result


# STEP 4

class Breaker:
    """Whether to try Redis at all.

    closed: allow() is true. After `threshold` consecutive failures it opens.
    open: allow() is false until `cooldown` seconds (by clock) have passed since it opened;
    then it is half-open.
    half-open: allow() is true for one request, the probe. success() closes the breaker;
    failure() opens it again for another cooldown.
    A success in the closed state resets the count of consecutive failures."""

    def __init__(self, *, threshold: int, cooldown: float,
                 clock: Callable[[], float]):
        self.threshold = threshold
        self.cooldown = cooldown
        self.clock = clock
        self.failures = 0
        self.state = "closed"
        self.opened_at = None

    def allow(self) -> bool:
        if self.state == "closed":
            return True

        if self.state == "half-open":
            return False

        if self.clock() - self.opened_at >= self.cooldown:
            self.state = "half-open"
            return True

        return False

    def success(self) -> None:
        self.failures = 0
        self.state = "closed"
        self.opened_at = None

    def failure(self) -> None:
        self.failures += 1
        if self.state == "half-open" or self.failures >= self.threshold:
            self.state = "open"
            self.opened_at = self.clock()


# STEPS 5 and 6

@dataclass(frozen=True)
class CacheConfig:
    """Timeouts for etf_risk.services.redis_client, and the breaker's settings. The values
    are Claude Code's proposals; the author decides them in step 6."""
    connect_timeout: float = 0.1     # seconds per connection attempt
    read_timeout: float = 0.1        # seconds per blocking send or receive
    failure_threshold: int = 3       # consecutive failures that open the breaker
    cooldown: float = 5.0            # seconds open before one probe


@dataclass
class Counters:
    """What happened to the requests (step 6 completes them). Each request lands in exactly
    one of hits, misses, decode_misses, get_errors and skipped; each computed result in
    exactly one of writes, set_errors and write_skips."""
    hits: int = 0
    misses: int = 0            # no value under the key
    decode_misses: int = 0     # a value that decode() turned down
    get_errors: int = 0        # GET failed (an error in errors)
    skipped: int = 0           # Redis not tried: the breaker was open
    writes: int = 0
    set_errors: int = 0        # SET failed (an error in errors)
    write_skips: int = 0       # not written: Redis failed or was skipped in this request


class ResultCache:
    """Cache-aside over a Redis client.

    client: get(key) -> bytes | None and set(key, value); etf_risk.services.redis_client in
    use, a fake in the tests. errors: the exceptions that mean Redis failed
    (redis.exceptions.RedisError for the real client); anything else propagates."""

    def __init__(self, client: Any, *, errors: tuple[type[BaseException], ...],
                 config: CacheConfig = CacheConfig(), clock: Callable[[], float] = time.monotonic):
        self.client = client
        self.errors = errors
        self.config = config
        self.counters = Counters()
        self.breaker = Breaker(threshold=config.failure_threshold, cooldown=config.cooldown, clock=clock)

    def get_or_compute(self, ident: Mapping[str, Any], compute: Callable[[], dict]) -> tuple[dict, str]:
        """(the stored result, "cache") on a hit; otherwise (compute(), "spark"), written back
        when Redis worked in this request. At most one GET and at most one SET per call; no
        SET after a failed GET; none at all while the breaker is open. Every GET and SET
        reports to the breaker: success() when it worked, failure() when it raised one of
        errors (a decode miss is neither). compute's exceptions propagate and nothing is
        written.

        STEP 8 (the author's decision, 2026-10-26): a result that encode() refuses (NaN or
        infinity) is returned exactly as compute() gave it, as without the cache, and not
        written: no SET, a write skip, nothing reported to the breaker. Caching never turns a
        query that would succeed uncached into a failure.

        STEP 5: hits, misses and the write-back. STEP 6: Redis failures, the breaker and the
        counters."""
        key = cache_key(ident)

        if not self.breaker.allow():
            self.counters.skipped += 1
            result = compute()
            self.counters.write_skips += 1
            return result, "spark"

        try:
            raw = self.client.get(key)
        except self.errors:
            self.breaker.failure()
            self.counters.get_errors += 1
            result = compute()
            self.counters.write_skips += 1
            return result, "spark"

        self.breaker.success()

        if raw is None:
            self.counters.misses += 1
        else:
            result = decode(raw, ident)
            if result is not None:
                self.counters.hits += 1
                return result, "cache"
            self.counters.decode_misses += 1

        result = compute()
        encoded = encode(ident, result)

        try:
            self.client.set(key, encoded)
        except self.errors:
            self.breaker.failure()
            self.counters.set_errors += 1
        else:
            self.breaker.success()
            self.counters.writes += 1

        return result, "spark"
