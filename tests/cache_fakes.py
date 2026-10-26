"""Fakes for the result cache's tests: a clock, a Redis stand-in that can fail, and the error it
raises in place of redis.exceptions.RedisError, so the cache's tests need neither Redis nor
redis-py. Also WRITTEN, the tutoring steps whose code exists, and step(), their mark.

AI contribution: written with Claude Code (Opus 5.5).
"""
import pytest

# The author's steps: 1-6 etf_risk.cache, 7 the SQL in etf_risk.summary.QUERIES. Add a step's
# number once its code is written. Until then its tests are expected to raise
# NotImplementedError (a strict xfail limited to that error): a wrong implementation fails with
# its own error at once, and a right one shows as XPASS, which strict mode fails until the step
# is listed here.
WRITTEN: set[int] = {1, 2, 3, 4, 5, 6, 7, 8}


def step(n: int, raises: type[BaseException] = NotImplementedError):
    """raises: what the code does until the step exists. NotImplementedError for a missing
    function; for a change to existing code (step 8), the error the current code raises."""
    if n in WRITTEN:
        return lambda test: test
    return pytest.mark.xfail(raises=raises, strict=True, reason=f"tutoring step {n} is not written yet")


class FakeClock:
    def __init__(self, now: float = 1000.0):
        self.now = now

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeRedisError(Exception):
    """Stands in for redis.exceptions.RedisError: passed to ResultCache as its errors."""


class FakeRedis:
    """get and set over a dict, with every call logged as (command, key).

    mode: "up"; "down" (every call fails); "get_down" or "set_down" (that command fails);
    "bug" (every call raises TypeError, which is not a Redis failure). cost: seconds each
    call advances clock, standing for the time spent in the client."""

    def __init__(self, clock: FakeClock | None = None, cost: float = 0.0):
        self.data: dict[str, bytes] = {}
        self.calls: list[tuple[str, str]] = []
        self.mode = "up"
        self.clock = clock
        self.cost = cost

    def _call(self, command: str, key: str) -> None:
        self.calls.append((command, key))
        if self.clock is not None:
            self.clock.advance(self.cost)
        if self.mode == "bug":
            raise TypeError("a bug, not a Redis failure")
        if self.mode == "down" or self.mode == f"{command.lower()}_down":
            raise FakeRedisError(f"{command} failed")

    def get(self, key: str) -> bytes | None:
        self._call("GET", key)
        return self.data.get(key)

    def set(self, key: str, value: bytes) -> bool:
        self._call("SET", key)
        self.data[key] = value
        return True

    def count(self, command: str) -> int:
        return sum(1 for c, _ in self.calls if c == command)
