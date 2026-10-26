"""The contract of etf_risk.cache (spec §11), one group per tutoring step. Offline: Redis is the
fake in tests/cache_fakes.py, where WRITTEN lists the steps whose code exists (see step()).

The conditional calculation of a request's Redis waiting time (docs/result-cache.md §6; not an
end-to-end bound) is composed from two parts: the calls per request pinned here (at most one
GET and one SET, none while the breaker is open, no SET after a failed GET) and the cost of one
call against redis-py as locked, pinned in tests/test_redis_client.py.

AI contribution: written with Claude Code (Opus 5.5). The step-1 decisions these tests pin
(the canonical form, upper-casing, what is refused) are the author's, of 2026-10-25.
"""
import hashlib
import inspect
import json
import math
import os
import re
import subprocess
import sys

import pytest

from cache_fakes import FakeClock, FakeRedis, FakeRedisError, step
from etf_risk import cache
from etf_risk.cache import FORMAT, KEY_PREFIX, Param

TICKERS = ("AAPL", "MSFT", "NVDA", "TSLA", "QQQ")
DECLARED = {"tickers": Param(kind="string_set", default=TICKERS, allowed=TICKERS)}
NORMALIZED = {"tickers": ["AAPL", "MSFT"]}       # stands for normalize_params' output in steps 2 to 6
IDENT_ARGS = dict(run_digest="a" * 64, query="overview", sql="SELECT ticker FROM paired",
                  params=NORMALIZED, engine="pyspark 4.2.0")
RESULT = {"columns": [["ticker", "string"], ["n_windows", "bigint"], ["median_return_2x", "double"],
                      ["breached", "boolean"]],
          "rows": [["AAPL", 529, 0.35200000000000004, True], ["MSFT", 466, 0.1 + 0.2, False],
                   ["NVDA", 311, 1e-300, False], ["TSLA", 174, -0.0, False], ["QQQ", 310, None, False]]}


def typed(value):
    """value with every leaf tagged by its type, so 1 == 1.0 and -0.0 == 0.0 no longer hold."""
    if isinstance(value, dict):
        return {k: typed(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [typed(v) for v in value]
    return (type(value).__name__, repr(value))


def ident(**changes):
    return cache.identity(**{**IDENT_ARGS, **changes})


# STEP 1: normalize_params

@step(1)
def test_a_parameter_left_out_takes_its_default():
    assert cache.normalize_params(DECLARED, {}) == cache.normalize_params(DECLARED, {"tickers": list(TICKERS)})


@step(1)
def test_every_declared_parameter_is_in_the_result():
    assert set(cache.normalize_params(DECLARED, {"tickers": ["QQQ"]})) == set(DECLARED)


@step(1)
def test_order_and_repetition_do_not_matter_but_membership_does():
    a = cache.normalize_params(DECLARED, {"tickers": ["QQQ", "AAPL"]})
    assert a == cache.normalize_params(DECLARED, {"tickers": ["AAPL", "QQQ", "AAPL"]})
    assert a == cache.normalize_params(DECLARED, {"tickers": ("AAPL", "QQQ")})
    assert a != cache.normalize_params(DECLARED, {"tickers": ["AAPL"]})


@step(1)
def test_the_result_is_json_and_survives_a_round_trip():
    result = cache.normalize_params(DECLARED, {"tickers": ["TSLA", "AAPL"]})
    assert json.loads(json.dumps(result)) == result


@step(1)
@pytest.mark.parametrize("given", [{"ticker": ["AAPL"]}, {"tickers": ["AAPL"], "stride": 21}])
def test_an_undeclared_parameter_is_refused(given):
    with pytest.raises(ValueError):
        cache.normalize_params(DECLARED, given)


@step(1)
@pytest.mark.parametrize("tickers", [["SPY"], ["AAPL", "SPY"]])
def test_a_ticker_outside_the_declaration_is_refused(tickers):
    with pytest.raises(ValueError):
        cache.normalize_params(DECLARED, {"tickers": tickers})


# The author's decisions (2026-10-25): a sorted list without duplicates; tickers upper-cased;
# an empty list, null and a bare string refused; non-string tickers refused; the input unchanged.

@step(1)
def test_the_canonical_form_is_a_sorted_list_without_duplicates():
    result = cache.normalize_params(DECLARED, {"tickers": ["QQQ", "AAPL", "QQQ"]})
    assert result == {"tickers": ["AAPL", "QQQ"]} and type(result["tickers"]) is list


@step(1)
def test_the_default_comes_out_sorted():
    assert cache.normalize_params(DECLARED, {}) == {"tickers": ["AAPL", "MSFT", "NVDA", "QQQ", "TSLA"]}


@step(1)
@pytest.mark.parametrize("tickers, expected", [(["aapl"], ["AAPL"]), (["Aapl", "AAPL", "qqq"], ["AAPL", "QQQ"])])
def test_tickers_are_upper_cased_before_they_are_checked_and_deduplicated(tickers, expected):
    assert cache.normalize_params(DECLARED, {"tickers": tickers}) == {"tickers": expected}


@step(1)
@pytest.mark.parametrize("tickers", [[" AAPL"], ["AAPL "], ["spy"]])
def test_upper_casing_is_the_only_change_made_to_a_ticker(tickers):
    with pytest.raises(ValueError):
        cache.normalize_params(DECLARED, {"tickers": tickers})


@step(1)
@pytest.mark.parametrize("value", [[], None, "AAPL", "aapl", ""])
def test_an_empty_list_null_and_a_bare_string_are_refused(value):
    with pytest.raises(ValueError):
        cache.normalize_params(DECLARED, {"tickers": value})


@step(1)
@pytest.mark.parametrize("tickers", [[1], [None], [True], [1.5], [b"AAPL"], [["AAPL"]], ["AAPL", 2]])
def test_a_ticker_that_is_not_a_string_is_refused(tickers):
    with pytest.raises(ValueError):
        cache.normalize_params(DECLARED, {"tickers": tickers})


@step(1)
@pytest.mark.parametrize("value", [42, {"AAPL": True}])
def test_a_value_that_is_neither_a_list_nor_a_tuple_is_refused(value):
    with pytest.raises(ValueError):
        cache.normalize_params(DECLARED, {"tickers": value})


@step(1)
@pytest.mark.parametrize("given, refused", [({"tickers": ["qqq", "AAPL", "aapl"]}, False),
                                            ({"tickers": ["aapl"], "stride": 21}, True)])
def test_the_request_is_not_changed_even_when_it_is_refused(given, refused):
    tickers = given["tickers"]
    before = {k: list(v) if isinstance(v, list) else v for k, v in given.items()}
    if refused:
        with pytest.raises(ValueError):
            cache.normalize_params(DECLARED, given)
    else:
        cache.normalize_params(DECLARED, given)
    assert given == before and given["tickers"] is tickers


# STEP 2: identity and cache_key

@step(2)
def test_the_identity_has_exactly_its_fields():
    i = ident()
    assert i == {"format": FORMAT, "engine": "pyspark 4.2.0", "run_digest": "a" * 64, "query": "overview",
                 "sql_sha256": hashlib.sha256(IDENT_ARGS["sql"].encode()).hexdigest(), "params": NORMALIZED}


def test_the_identity_takes_nothing_about_the_request():
    assert set(inspect.signature(cache.identity).parameters) == {"run_digest", "query", "sql", "params", "engine"}


@step(2)
def test_the_key_has_a_readable_prefix_and_a_sha256():
    assert re.fullmatch(rf"{re.escape(KEY_PREFIX)}:v{FORMAT}:overview:[0-9a-f]{{64}}", cache.cache_key(ident()))


@step(2)
@pytest.mark.parametrize("change", [
    {"run_digest": "b" * 64},                      # equal run ids, other files: never one key
    {"query": "comparison"},
    {"sql": "SELECT  ticker FROM paired"},         # whitespace too
    {"params": {"tickers": ["AAPL"]}},
    {"engine": "pyspark 4.2.1"},
])
def test_each_part_of_the_identity_changes_the_key(change):
    assert cache.cache_key(ident(**change)) != cache.cache_key(ident())


@step(2)
def test_the_format_version_changes_the_key():
    assert cache.cache_key({**ident(), "format": FORMAT + 1}) != cache.cache_key(ident())


@step(2)
def test_the_order_of_fields_does_not_change_the_key():
    i = ident(params={"tickers": ["AAPL", "MSFT"], "b": ["x"]})
    shuffled = dict(reversed(list(i.items())))
    shuffled["params"] = dict(reversed(list(i["params"].items())))
    assert cache.cache_key(shuffled) == cache.cache_key(i)


@step(2)
def test_equal_requests_give_equal_keys_across_processes():
    code = ("import json, sys; from etf_risk import cache; "
            "print(cache.cache_key(cache.identity(**json.loads(sys.argv[1]))))")
    keys = []
    for seed in ("1", "2"):
        out = subprocess.run([sys.executable, "-c", code, json.dumps(IDENT_ARGS)], capture_output=True, text=True,
                             env={**os.environ, "PYTHONHASHSEED": seed})
        if "NotImplementedError" in out.stderr:
            raise NotImplementedError("tutoring step 2")
        assert out.returncode == 0, out.stderr
        keys.append(out.stdout.strip())
    assert keys[0] == keys[1] == cache.cache_key(ident())


# The author's decisions (2026-10-25): the prefix names the identity's own format, and
# identity() keeps a deep copy of params.

@step(2)
def test_the_prefix_names_the_identitys_own_format():
    assert cache.cache_key({**ident(), "format": 7}).startswith(f"{KEY_PREFIX}:v7:overview:")


@step(2)
def test_changing_the_callers_params_afterwards_changes_neither_the_identity_nor_its_key():
    params = {"tickers": ["AAPL", "MSFT"]}
    i = cache.identity(**{**IDENT_ARGS, "params": params})
    key = cache.cache_key(i)
    params["tickers"].append("QQQ")          # inside a nested list: a shallow copy would follow this
    params["tickers"][0] = "TSLA"
    params["extra"] = ["x"]                   # the dict itself
    assert i["params"] == {"tickers": ["AAPL", "MSFT"]} and cache.cache_key(i) == key


# STEP 3: encode and decode

@step(3)
def test_a_result_round_trips_with_its_value_types():
    raw = cache.encode(ident(), RESULT)
    assert isinstance(raw, bytes)
    assert typed(cache.decode(raw, ident())) == typed(RESULT)


@step(3)
def test_encoding_is_deterministic():
    assert cache.encode(ident(), RESULT) == cache.encode(ident(), json.loads(json.dumps(RESULT)))


@step(3)
@pytest.mark.parametrize("change", [{"run_digest": "b" * 64}, {"params": {"tickers": ["AAPL"]}},
                                    {"sql": "SELECT 2"}, {"engine": "pyspark 4.2.1"}])
def test_a_value_of_another_identity_is_a_miss(change):
    assert cache.decode(cache.encode(ident(**change), RESULT), ident()) is None


@step(3)
def test_bad_values_are_misses_never_errors():
    good = cache.encode(ident(), RESULT)
    for raw in (b"", b"not json", b"\xff\xfe\x00", good[:-7], b"[1, 2]", b'{"format": 99}', b"null",
                json.dumps({"identity": ident(), "result": "rows"}).encode()):
        assert cache.decode(raw, ident()) is None, raw


# The author's decisions (2026-10-25): the layout {"identity", "result"}; standard JSON (no NaN
# or infinity); decode checks the result's shape; anything malformed or foreign is a miss.

@step(3)
def test_the_stored_value_is_the_identity_and_the_result():
    assert json.loads(cache.encode(ident(), RESULT)) == {"identity": ident(), "result": RESULT}


@step(3)
@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_nan_and_infinity_are_refused(value):
    with pytest.raises(ValueError):
        cache.encode(ident(), {"columns": [["x", "double"]], "rows": [[value]]})


@step(3)
def test_a_result_without_rows_round_trips():
    empty = {"columns": [["ticker", "string"]], "rows": []}
    assert cache.decode(cache.encode(ident(), empty), ident()) == empty


COLUMNS = [["ticker", "string"], ["n_windows", "bigint"]]


@step(3)
@pytest.mark.parametrize("stored", [
    {"identity": "IDENT"},                                              # no result
    {"result": {"columns": COLUMNS, "rows": []}},                       # no identity
    {"identity": "IDENT", "result": [COLUMNS, []]},                     # result not an object
    {"identity": "IDENT", "result": {"columns": "ticker", "rows": []}},
    {"identity": "IDENT", "result": {"columns": COLUMNS, "rows": "AAPL"}},
    {"identity": "IDENT", "result": {"rows": []}},
    {"identity": "IDENT", "result": {"columns": ["ticker"], "rows": []}},           # a column not a list
    {"identity": "IDENT", "result": {"columns": [["ticker"]], "rows": []}},         # one string
    {"identity": "IDENT", "result": {"columns": [["ticker", "string", "x"]], "rows": []}},
    {"identity": "IDENT", "result": {"columns": [["ticker", 1]], "rows": []}},      # not two strings
    {"identity": "IDENT", "result": {"columns": COLUMNS, "rows": ["AAPL"]}},        # a row not a list
    {"identity": "IDENT", "result": {"columns": COLUMNS, "rows": [["AAPL"]]}},      # too short
    {"identity": "IDENT", "result": {"columns": COLUMNS, "rows": [["AAPL", 1, 2]]}},  # too long
])
def test_a_malformed_stored_value_is_a_miss(stored):
    if stored.get("identity") == "IDENT":
        stored = {**stored, "identity": ident()}
    assert cache.decode(json.dumps(stored).encode(), ident()) is None


# The author's further checks on read (step 3): a stored row holding NaN or infinity (also as a
# number too large for a float, which json.loads reads as inf), or a value that is not a JSON
# scalar, is a miss.

@step(3)
@pytest.mark.parametrize("cell", ["NaN", "Infinity", "-Infinity", "1e999", "-1e999", "[1]", '{"a": 1}'])
def test_a_stored_row_with_a_non_finite_or_non_scalar_value_is_a_miss(cell):
    stored = json.dumps({"identity": ident(), "result": {"columns": [["x", "double"]], "rows": [["CELL"]]}})
    assert cache.decode(stored.replace('"CELL"', cell).encode(), ident()) is None


# STEP 4: the breaker

@pytest.fixture
def clock():
    return FakeClock()


def breaker(clock):
    return cache.Breaker(threshold=3, cooldown=5.0, clock=clock)


@step(4)
def test_the_breaker_opens_after_the_threshold_of_consecutive_failures(clock):
    b = breaker(clock)
    for _ in range(2):
        assert b.allow()
        b.failure()
    assert b.allow()
    b.failure()
    assert not b.allow()


@step(4)
def test_a_success_resets_the_count(clock):
    b = breaker(clock)
    for outcome in ("failure", "failure", "success", "failure", "failure"):
        assert b.allow()
        getattr(b, outcome)()
    assert b.allow()


@step(4)
def test_after_the_cooldown_exactly_one_probe_is_allowed(clock):
    b = breaker(clock)
    for _ in range(3):
        b.failure()
    clock.advance(4.99)
    assert not b.allow()
    clock.advance(0.02)
    assert b.allow()
    assert not b.allow()                  # one probe until it reports


@step(4)
def test_a_successful_probe_closes_the_breaker(clock):
    b = breaker(clock)
    for _ in range(3):
        b.failure()
    clock.advance(5.0)
    assert b.allow()
    b.success()
    assert b.allow() and b.allow()


@step(4)
def test_a_failed_probe_opens_it_for_a_whole_cooldown(clock):
    b = breaker(clock)
    for _ in range(3):
        b.failure()
    clock.advance(5.0)
    assert b.allow()
    b.failure()
    clock.advance(4.99)
    assert not b.allow()
    clock.advance(0.02)
    assert b.allow()


# The author's behaviour while open, outside a probe (step 4): failure() restarts the cooldown;
# success() closes the breaker.

@step(4)
def test_a_failure_reported_while_open_restarts_the_cooldown(clock):
    b = breaker(clock)
    for _ in range(3):
        b.failure()
    clock.advance(4.0)
    b.failure()                           # open, no probe out
    clock.advance(4.0)                    # 8 s after it opened, 4 s after the restart
    assert not b.allow()
    clock.advance(1.0)
    assert b.allow()


@step(4)
def test_a_success_reported_while_open_closes_the_breaker(clock):
    b = breaker(clock)
    for _ in range(3):
        b.failure()
    b.success()
    assert b.allow() and b.allow()


# STEP 5: hits, misses and the write-back

def compute_counting(result=RESULT):
    calls = []

    def compute():
        calls.append(1)
        return json.loads(json.dumps(result))
    return compute, calls


def new_cache(clock=None, cost=0.0, **config):
    clock = clock or FakeClock()
    redis = FakeRedis(clock, cost)
    return cache.ResultCache(redis, errors=(FakeRedisError,), config=cache.CacheConfig(**config), clock=clock), redis


@step(5)
def test_a_miss_computes_and_writes_back_then_a_hit_returns_the_same_result():
    rc, redis = new_cache()
    compute, calls = compute_counting()
    first = rc.get_or_compute(ident(), compute)
    second = rc.get_or_compute(ident(), compute)
    assert first[1] == "spark" and second[1] == "cache" and len(calls) == 1
    assert typed(first[0]) == typed(second[0]) == typed(RESULT)
    assert typed(cache.decode(redis.data[cache.cache_key(ident())], ident())) == typed(RESULT)


@step(5)
def test_another_identity_misses():
    rc, _ = new_cache()
    compute, calls = compute_counting()
    rc.get_or_compute(ident(), compute)
    assert rc.get_or_compute(ident(run_digest="b" * 64), compute)[1] == "spark" and len(calls) == 2


@step(5)
@pytest.mark.parametrize("stored", ["another identity", "garbage"])
def test_a_bad_stored_value_is_a_miss_and_is_replaced(stored):
    rc, redis = new_cache()
    key = cache.cache_key(ident())
    redis.data[key] = cache.encode(ident(run_digest="b" * 64), RESULT) if stored == "another identity" else b"\x00garbage"
    compute, calls = compute_counting()
    assert rc.get_or_compute(ident(), compute)[1] == "spark" and len(calls) == 1
    assert typed(cache.decode(redis.data[key], ident())) == typed(RESULT)
    assert rc.get_or_compute(ident(), compute)[1] == "cache"


class ComputeFailed(Exception):
    """Not a RuntimeError: NotImplementedError is one, and would satisfy pytest.raises."""


@step(5)
def test_a_failing_compute_propagates_and_nothing_is_written():
    rc, redis = new_cache()

    def compute():
        raise ComputeFailed("the folder changed during the query")
    with pytest.raises(ComputeFailed):
        rc.get_or_compute(ident(), compute)
    assert redis.data == {} and redis.count("SET") == 0


@step(5)
def test_one_get_and_at_most_one_set_per_request():
    rc, redis = new_cache()
    compute, _ = compute_counting()
    rc.get_or_compute(ident(), compute)
    assert [c for c, _ in redis.calls] == ["GET", "SET"]
    rc.get_or_compute(ident(), compute)
    assert [c for c, _ in redis.calls] == ["GET", "SET", "GET"]


# STEP 6: Redis failures, the breaker and the counters

@step(6)
def test_a_failed_get_falls_back_to_compute_and_writes_nothing():
    rc, redis = new_cache()
    redis.mode = "get_down"
    compute, calls = compute_counting()
    result, source = rc.get_or_compute(ident(), compute)
    assert source == "spark" and typed(result) == typed(RESULT) and len(calls) == 1
    assert [c for c, _ in redis.calls] == ["GET"]
    assert (rc.counters.get_errors, rc.counters.write_skips) == (1, 1)


@step(6)
def test_a_failed_set_still_returns_the_result():
    rc, redis = new_cache()
    redis.mode = "set_down"
    compute, _ = compute_counting()
    result, source = rc.get_or_compute(ident(), compute)
    assert source == "spark" and typed(result) == typed(RESULT)
    assert (rc.counters.misses, rc.counters.set_errors, rc.counters.writes) == (1, 1, 0)


@step(6)
def test_an_error_that_is_not_a_redis_failure_propagates():
    rc, redis = new_cache()
    redis.mode = "bug"
    compute, calls = compute_counting()
    with pytest.raises(TypeError):
        rc.get_or_compute(ident(), compute)
    assert rc.counters.get_errors == 0 and calls == []


@step(6)
def test_the_breaker_stops_redis_calls_and_one_probe_restores_them():
    clock = FakeClock()
    rc, redis = new_cache(clock, failure_threshold=3, cooldown=5.0)
    compute, _ = compute_counting()
    redis.mode = "down"
    for _ in range(3):
        assert rc.get_or_compute(ident(), compute)[1] == "spark"
    assert len(redis.calls) == 3
    for _ in range(4):                                         # open: Redis is not called
        assert rc.get_or_compute(ident(), compute)[1] == "spark"
    assert len(redis.calls) == 3 and rc.counters.skipped == 4
    redis.mode = "up"
    clock.advance(5.0)
    assert rc.get_or_compute(ident(), compute)[1] == "spark"   # the probe: a miss, written back
    assert rc.get_or_compute(ident(), compute)[1] == "cache"


@step(6)
def test_decode_misses_are_not_redis_failures():
    rc, redis = new_cache(failure_threshold=2)
    compute, _ = compute_counting()
    key = cache.cache_key(ident())
    for _ in range(4):
        redis.data[key] = b"garbage"
        rc.get_or_compute(ident(), compute)
    assert rc.counters.decode_misses == 4 and rc.counters.skipped == 0


@step(6)
def test_every_request_lands_in_one_outcome_and_every_computed_result_in_one_write_outcome():
    clock = FakeClock()
    rc, redis = new_cache(clock, failure_threshold=2, cooldown=5.0)
    compute, calls = compute_counting()
    script = [("up", {}), ("up", {}), ("get_down", {"run_digest": "c" * 64}), ("set_down", {"run_digest": "d" * 64}),
              ("down", {}), ("down", {}), ("up", {"run_digest": "e" * 64})]
    for mode, change in script:
        redis.mode = mode
        rc.get_or_compute(ident(**change), compute)
    c = rc.counters
    assert c.hits + c.misses + c.decode_misses + c.get_errors + c.skipped == len(script)
    assert c.writes + c.set_errors + c.write_skips == len(calls)


@step(6)
def test_the_redis_calls_of_one_request_stay_within_the_conditional_calculation():
    """At most one GET and one SET; only the GET when it fails; none while the breaker is
    open. With each call costing at most `cost`, a request spends at most 2 * cost in Redis."""
    clock = FakeClock()
    rc, redis = new_cache(clock, cost=0.4, failure_threshold=3, cooldown=5.0)
    compute, _ = compute_counting()
    for mode, change, most in [("up", {}, 0.8), ("up", {}, 0.4), ("get_down", {"run_digest": "c" * 64}, 0.4),
                               ("set_down", {"run_digest": "d" * 64}, 0.8), ("down", {}, 0.4), ("down", {}, 0.4),
                               ("down", {}, 0.0), ("down", {}, 0.0)]:
        redis.mode = mode
        start = clock()
        rc.get_or_compute(ident(**change), compute)
        assert clock() - start <= most + 1e-9, (mode, change)


@step(6)
def test_an_outage_reaches_redis_at_most_threshold_plus_one_probe_per_cooldown():
    clock = FakeClock()
    rc, redis = new_cache(clock, failure_threshold=3, cooldown=5.0)
    redis.mode = "down"
    compute, _ = compute_counting()
    window = 60.0
    while clock() < 1000.0 + window:
        rc.get_or_compute(ident(), compute)
        clock.advance(0.25)
    assert redis.count("GET") <= 3 + math.ceil(window / 5.0) and redis.count("SET") == 0


# STEP 8 (the author's decision, 2026-10-26): a result that encode() refuses (NaN or infinity) is
# returned as the query gave it, as without the cache, and is not written; caching adds no
# failure. It counts as a write skip and is not a Redis failure. Until the step is written,
# encode's ValueError escapes, which is what these strict xfails expect.

NON_FINITE = [math.nan, math.inf, -math.inf]


@step(8, raises=ValueError)
@pytest.mark.parametrize("value", NON_FINITE)
def test_a_non_finite_result_is_returned_as_computed_and_not_written(value):
    rc, redis = new_cache()
    result = {"columns": [["x", "double"]], "rows": [[value]]}
    out, source = rc.get_or_compute(ident(), lambda: result)
    assert out is result and source == "spark"
    assert redis.count("SET") == 0 and redis.data == {}
    c = rc.counters
    assert (c.misses, c.write_skips, c.writes, c.set_errors) == (1, 1, 0, 0)


@step(8, raises=ValueError)
def test_a_non_finite_result_is_not_a_redis_failure():
    rc, redis = new_cache(failure_threshold=1)
    result = {"columns": [["x", "double"]], "rows": [[math.nan]]}
    for _ in range(3):
        assert rc.get_or_compute(ident(), lambda: result)[1] == "spark"
    assert redis.count("GET") == 3 and rc.counters.skipped == 0       # the breaker stayed closed
