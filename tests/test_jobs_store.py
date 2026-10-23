"""The job store: transitions, tokens and leases, competing claims, repeated acceptance,
rollbacks, conflict retries, and the schema's constraints.

Every test that takes `env` runs on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL too
(tests/jobs_backends.py). On SQLite, competing connections run one after another under the
database's write lock: those runs check the state logic, not InnoDB's row locking, which the
MySQL runs and tests/test_jobs_mysql.py check.

AI contribution: written with Claude Code (Opus 5.5).
"""
import functools
import re
from dataclasses import replace

import pytest

from etf_risk.jobs.simulated import SimulatedCrash
from etf_risk.jobs.store import (CONFLICT_RETRIES, FAULT_POINTS, SCHEMA_DIR, TRANSITIONS, Claim, Outcome, Refusal,
                                 SQLiteDialect, Status, StoreInvariantError, run_id)
from jobs_backends import BACKENDS, LEASE, InThread, Paused, SQLiteBackend, StoreEnv, make_backend, run_together


@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = StoreEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


@pytest.fixture
def sqlite_env(tmp_path):
    env = StoreEnv(SQLiteBackend(tmp_path), tmp_path)
    yield env
    env.close()


# Situations: each returns a job id and worker A's claim on it (for "queued", a claim
# that never held the job).

def queued(env):
    job = env.store.submit({"n": 1}, {})
    return job, Claim(job, 1, "0" * 32, run_id(job, 1), env.runs / run_id(job, 1), 3, {}, {})


def published(env):
    job, a = queued(env)
    assert env.store.mark_published(job, 0)
    return job, a


def running(env, max_attempts=3):
    job = env.store.submit({"n": 1}, {}, max_attempts=max_attempts)
    return job, env.store.claim(job, "worker-A", env.runs)


def expired(env):
    job, a = running(env)
    env.clock.advance(LEASE.total_seconds())                    # lease_expires_at <= now: expired
    return job, a


def expired_last(env):
    job, a = running(env, max_attempts=1)
    env.clock.advance(LEASE.total_seconds())
    return job, a


def succeeded(env):
    job, a = running(env)
    assert env.store.accept_result(a)
    return job, a


def failed(env):
    job, a = running(env)
    assert env.store.fail_attempt(a, "permanent", retryable=False) is Status.FAILED
    return job, a


def requeued(env):
    job, a = running(env)
    assert env.store.fail_attempt(a, "transient", retryable=True) is Status.QUEUED
    return job, a


SITUATIONS = {"queued": queued, "published": published, "running": running, "expired": expired,
              "expired_last": expired_last, "succeeded": succeeded, "failed": failed, "requeued": requeued}

OPERATIONS = {
    "claim": lambda env, job, a: env.store.claim(job, "worker-B", env.runs),
    "renew": lambda env, job, a: env.store.renew(a),
    "accept": lambda env, job, a: env.store.accept_result(a),
    "fail": lambda env, job, a: env.store.fail_attempt(a, "transient", retryable=True),
    "foreign_token": lambda env, job, a: env.store.accept_result(replace(a, token="f" * 32)),
    "mark_published": lambda env, job, a: env.store.mark_published(job, env.store.job(job)["version"]),
    "requeue_expired": lambda env, job, a: env.store.requeue_expired(job, a.token),   # the reconciler saw A's token
}
TRANSITION_NAME = {"claim": "claim", "renew": "renew", "accept": "accept_result", "fail": "fail_attempt",
                   "foreign_token": "accept_result", "mark_published": "mark_published",
                   "requeue_expired": "requeue_expired"}

# (situation, operation) -> (what the call returns, the job's status afterwards); a status
# of None means the call must leave both tables exactly as they were.
CLAIMED = object()   # any Claim
EXPECTED = {
    ("queued", "claim"): (CLAIMED, Status.RUNNING),
    ("queued", "renew"): (False, None),
    ("queued", "accept"): (False, None),
    ("queued", "fail"): (None, None),
    ("queued", "foreign_token"): (False, None),
    ("queued", "mark_published"): (True, Status.QUEUED),
    ("queued", "requeue_expired"): (None, None),
    ("published", "claim"): (CLAIMED, Status.RUNNING),         # the claim clears the publication
    ("published", "renew"): (False, None),
    ("published", "accept"): (False, None),
    ("published", "fail"): (None, None),
    ("published", "foreign_token"): (False, None),
    ("published", "mark_published"): (False, None),            # already recorded
    ("published", "requeue_expired"): (None, None),
    ("running", "claim"): (Refusal.LEASE_HELD, None),
    ("running", "renew"): (True, Status.RUNNING),
    ("running", "accept"): (True, Status.SUCCEEDED),
    ("running", "fail"): (Status.QUEUED, Status.QUEUED),
    ("running", "foreign_token"): (False, None),
    ("running", "mark_published"): (False, None),
    ("running", "requeue_expired"): (None, None),              # the lease is live
    ("expired", "claim"): (CLAIMED, Status.RUNNING),            # takeover
    ("expired", "renew"): (True, Status.RUNNING),               # nobody took over: the token still holds
    ("expired", "accept"): (True, Status.SUCCEEDED),
    ("expired", "fail"): (Status.QUEUED, Status.QUEUED),
    ("expired", "foreign_token"): (False, None),
    ("expired", "mark_published"): (False, None),
    ("expired", "requeue_expired"): (Status.QUEUED, Status.QUEUED),
    ("expired_last", "claim"): (Refusal.EXHAUSTED, Status.FAILED),
    ("expired_last", "renew"): (True, Status.RUNNING),
    ("expired_last", "accept"): (True, Status.SUCCEEDED),
    ("expired_last", "fail"): (Status.FAILED, Status.FAILED),   # retryable, but no attempts left
    ("expired_last", "foreign_token"): (False, None),
    ("expired_last", "mark_published"): (False, None),
    ("expired_last", "requeue_expired"): (Status.FAILED, Status.FAILED),
    ("succeeded", "claim"): (Refusal.SUCCEEDED, None),
    ("succeeded", "renew"): (False, None),
    ("succeeded", "accept"): (True, None),                      # already accepted: true again, no change
    ("succeeded", "fail"): (None, None),
    ("succeeded", "foreign_token"): (False, None),
    ("succeeded", "mark_published"): (False, None),
    ("succeeded", "requeue_expired"): (None, None),
    ("failed", "claim"): (Refusal.FAILED, None),
    ("failed", "renew"): (False, None),
    ("failed", "accept"): (False, None),
    ("failed", "fail"): (None, None),
    ("failed", "foreign_token"): (False, None),
    ("failed", "mark_published"): (False, None),
    ("failed", "requeue_expired"): (None, None),
    ("requeued", "claim"): (CLAIMED, Status.RUNNING),
    ("requeued", "renew"): (False, None),
    ("requeued", "accept"): (False, None),
    ("requeued", "fail"): (None, None),
    ("requeued", "foreign_token"): (False, None),
    ("requeued", "mark_published"): (True, Status.QUEUED),     # back in queued, with no publication recorded
    ("requeued", "requeue_expired"): (None, None),
}


def test_the_matrix_covers_every_situation_and_operation():
    assert set(EXPECTED) == {(s, o) for s in SITUATIONS for o in OPERATIONS}


@pytest.mark.parametrize("situation, operation", list(EXPECTED))
def test_transition_matrix(env, situation, operation):
    job, a = SITUATIONS[situation](env)
    before, status_before = env.dump(), env.store.job(job)["status"]
    result = OPERATIONS[operation](env, job, a)
    expected_result, expected_status = EXPECTED[situation, operation]
    if expected_result is CLAIMED:
        assert isinstance(result, Claim)
    else:
        assert type(result) is type(expected_result) and result == expected_result
    if expected_status is None:
        assert env.dump() == before                              # refused: both tables unchanged
    else:
        status_after = env.store.job(job)["status"]
        name = "exhaust" if result is Refusal.EXHAUSTED else TRANSITION_NAME[operation]
        assert status_after is expected_status and (status_before, status_after) in TRANSITIONS[name]
    assert env.store.invariant_violations() == {}


# Tokens, leases and stale workers

def test_each_claim_gets_a_new_token_attempt_and_folder(env):
    job = env.store.submit({"n": 1}, {})
    claims = []
    for worker in "ABC":
        claims.append(env.store.claim(job, f"worker-{worker}", env.runs))
        env.clock.advance(LEASE.total_seconds())
    assert [c.attempt_number for c in claims] == [1, 2, 3]
    assert len({c.token for c in claims}) == 3 and all(re.fullmatch("[0-9a-f]{32}", c.token) for c in claims)
    assert [c.run_id for c in claims] == [f"job-{job}-attempt-{n}" for n in (1, 2, 3)]
    assert len({c.output_dir for c in claims}) == 3
    assert [x["outcome"] for x in env.store.attempts(job)] == [Outcome.EXPIRED, Outcome.EXPIRED, Outcome.RUNNING]
    assert env.store.invariant_violations() == {}


def test_a_takeover_needs_an_expired_lease(env):
    job, _ = running(env)
    env.clock.advance(LEASE.total_seconds() - 0.001)
    assert env.store.claim(job, "worker-B", env.runs) is Refusal.LEASE_HELD
    env.clock.advance(0.001)                                      # lease_expires_at == now counts as expired
    b = env.store.claim(job, "worker-B", env.runs)
    assert isinstance(b, Claim) and b.attempt_number == 2


def test_renewal_extends_the_lease_and_is_recorded_in_the_attempt(env):
    job, a = running(env)
    env.clock.advance(50)
    assert env.store.renew(a)
    env.clock.advance(50)                                         # 100 s after the claim, 50 after the renewal
    assert env.store.claim(job, "worker-B", env.runs) is Refusal.LEASE_HELD
    attempt = env.store.attempts(job)[0]
    assert attempt["renewals"] == 1 and attempt["lease_expires_at"] == env.store.job(job)["lease_expires_at"]
    env.clock.advance(10)                                         # 60 s after the renewal
    assert isinstance(env.store.claim(job, "worker-B", env.runs), Claim)


def test_an_expired_lease_stays_with_its_token_until_a_takeover(env):
    job, a = running(env)
    env.clock.advance(3 * LEASE.total_seconds())
    assert env.store.renew(a)                                     # nobody took over
    assert env.store.claim(job, "worker-B", env.runs) is Refusal.LEASE_HELD
    assert env.store.accept_result(a)
    assert env.store.job(job)["accepted_attempt"] == 1


def test_a_stale_worker_is_fenced_off_after_a_takeover(env):
    job, a = expired(env)
    b = env.store.claim(job, "worker-B", env.runs)
    assert not env.store.renew(a)
    assert env.store.fail_attempt(a, "late failure", retryable=True) is None
    assert not env.store.accept_result(a)
    assert env.store.accept_result(b)
    assert not env.store.accept_result(a)                         # still refused once B's result is accepted
    j = env.store.job(job)
    assert j["status"] is Status.SUCCEEDED and j["accepted_attempt"] == 2
    assert [x["outcome"] for x in env.store.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    assert env.store.invariant_violations() == {}


def test_a_stale_token_stays_fenced_after_a_retry_claimed_the_job(env):
    job, a = requeued(env)                                        # A's attempt failed; the job is queued again
    b = env.store.claim(job, "worker-B", env.runs)
    before = env.dump()
    assert not env.store.renew(a) and not env.store.accept_result(a)
    assert env.store.fail_attempt(a, "late", retryable=False) is None
    assert env.dump() == before and env.store.accept_result(b)


def test_attempts_run_out_when_leases_keep_expiring(env):
    job = env.store.submit({"n": 1}, {}, max_attempts=2)
    for worker in "AB":
        assert isinstance(env.store.claim(job, f"worker-{worker}", env.runs), Claim)
        env.clock.advance(LEASE.total_seconds())
    assert env.store.claim(job, "worker-C", env.runs) is Refusal.EXHAUSTED
    j = env.store.job(job)
    assert j["status"] is Status.FAILED and "attempts exhausted" in j["error"] and j["accepted_attempt"] is None
    assert [x["outcome"] for x in env.store.attempts(job)] == [Outcome.EXPIRED, Outcome.EXPIRED]
    assert env.store.claim(job, "worker-D", env.runs) is Refusal.FAILED
    assert env.store.invariant_violations() == {}


def test_retryable_failures_requeue_until_attempts_run_out(env):
    job = env.store.submit({"n": 1}, {}, max_attempts=2)
    a = env.store.claim(job, "worker-A", env.runs)
    assert env.store.fail_attempt(a, "transient 1", retryable=True) is Status.QUEUED
    j = env.store.job(job)
    assert (j["status"], j["error"], j["finished_at"]) == (Status.QUEUED, None, None)
    b = env.store.claim(job, "worker-B", env.runs)
    assert env.store.fail_attempt(b, "transient 2", retryable=True) is Status.FAILED
    j = env.store.job(job)
    assert (j["status"], j["error"]) == (Status.FAILED, "transient 2")
    assert [(x["outcome"], x["error"]) for x in env.store.attempts(job)] == [
        (Outcome.FAILED, "transient 1"), (Outcome.FAILED, "transient 2")]
    assert env.store.invariant_violations() == {}


def test_an_unknown_job_is_not_found(env):
    assert env.store.claim(999, "worker-A", env.runs) is Refusal.NOT_FOUND


# Competing claims: connections of their own, in threads

@pytest.mark.parametrize("situation", ["queued", "expired"])
def test_competing_claims_start_one_attempt_per_job(env, situation):
    """Six connections claim the same ten jobs at the same moment: a fresh claim of queued jobs,
    or a takeover of expired ones. Each job gets one new attempt; the other five are refused."""
    jobs = [SITUATIONS[situation](env)[0] for _ in range(10)]
    new_attempt = 1 if situation == "queued" else 2
    stores = [env.new_store() for _ in range(6)]

    def claim_all(store, worker):
        return {job: store.claim(job, worker, env.runs) for job in jobs}

    results = run_together(*(functools.partial(claim_all, store, f"worker-{i}") for i, store in enumerate(stores)))
    for job in jobs:
        outcomes = [r[job] for r in results]
        claims = [o for o in outcomes if isinstance(o, Claim)]
        assert len(claims) == 1 and claims[0].attempt_number == new_attempt
        assert [o for o in outcomes if not isinstance(o, Claim)] == [Refusal.LEASE_HELD] * 5
        assert len(env.store.attempts(job)) == new_attempt
    assert env.store.invariant_violations() == {}


def test_a_competing_claim_waits_for_the_first_and_is_refused(env):
    job = env.store.submit({"n": 1}, {})
    first = Paused(env, lambda store: store.claim(job, "worker-A", env.runs), "claim.jobs_updated").start()
    second = InThread(env, lambda store: store.claim(job, "worker-B", env.runs)).start()
    if env.backend.name == "mysql":
        assert env.backend.lock_waiting(second.connection)        # an InnoDB row-lock wait
    else:
        second.thread.join(timeout=0.5)
        assert second.thread.is_alive()                           # waiting for SQLite's write lock
    assert isinstance(first.resume(), Claim)
    assert second.outcome() is Refusal.LEASE_HELD                 # it saw the committed claim, not its own view
    assert len(env.store.attempts(job)) == 1 and env.store.invariant_violations() == {}


def test_the_old_holder_accepting_while_another_worker_takes_over(env):
    """A's lease has expired. A accepts while B claims: the transaction holding the job's row
    first decides. Here A does, so B's takeover waits and then finds the job succeeded."""
    job, a = expired(env)
    accepting = Paused(env, lambda store: store.accept_result(a), "accept_result.jobs_updated").start()
    taking_over = InThread(env, lambda store: store.claim(job, "worker-B", env.runs)).start()
    assert accepting.resume() is True and taking_over.outcome() is Refusal.SUCCEEDED
    assert env.store.job(job)["accepted_attempt"] == 1 and env.store.invariant_violations() == {}


def test_a_takeover_while_the_old_holder_tries_to_accept(env):
    """The other order: B's takeover holds the row first, so A's acceptance meets B's token."""
    job, a = expired(env)
    taking_over = Paused(env, lambda store: store.claim(job, "worker-B", env.runs), "claim.jobs_updated").start()
    accepting = InThread(env, lambda store: store.accept_result(a)).start()
    b = taking_over.resume()
    assert isinstance(b, Claim) and accepting.outcome() is False
    assert env.store.job(job)["status"] is Status.RUNNING and env.store.accept_result(b)
    assert env.store.invariant_violations() == {}


# Repeated acceptance

def test_accepting_again_changes_nothing(env):
    job, a = running(env)
    assert env.store.accept_result(a)
    before = env.dump()
    assert env.store.accept_result(a)
    assert env.dump() == before


def test_the_same_acceptance_twice_at_once_accepts_one_result(env):
    """A repeat of A's acceptance races the original: one transaction accepts, the other then
    finds A's own result accepted and reports true as well."""
    job, a = running(env)
    original = Paused(env, lambda store: store.accept_result(a), "accept_result.jobs_updated").start()
    repeat = InThread(env, lambda store: store.accept_result(a)).start()
    assert original.resume() is True and repeat.outcome() is True
    j = env.store.job(job)
    assert j["accepted_attempt"] == 1 and j["version"] == 2       # the claim and one acceptance
    assert env.store.invariant_violations() == {}


class LoseNextCommit:
    """Wraps a connection: once armed, the next COMMIT raises, after running (applied: its
    reply was lost) or instead of running (not applied)."""

    def __init__(self, connection, *, applied):
        self.connection, self.applied, self.armed = connection, applied, False

    def cursor(self):
        return _LosingCursor(self, self.connection.cursor())

    def close(self):
        self.connection.close()


class _LosingCursor:
    def __init__(self, owner, cursor):
        self._owner, self._cursor = owner, cursor

    def execute(self, sql, *args):
        if sql == "COMMIT" and self._owner.armed:
            self._owner.armed = False
            if self._owner.applied:
                self._cursor.execute(sql, *args)
            raise ConnectionError("the reply to COMMIT was lost")
        return self._cursor.execute(sql, *args)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


@pytest.mark.parametrize("applied", [True, False], ids=["commit-applied", "commit-not-applied"])
def test_acceptance_repeated_after_a_failed_commit(env, applied):
    job, a = running(env)
    connection = LoseNextCommit(env.backend.connect(), applied=applied)
    store = env.new_store(connection=connection)
    connection.armed = True
    with pytest.raises(ConnectionError):
        store.accept_result(a)
    assert env.store.job(job)["status"] is (Status.SUCCEEDED if applied else Status.RUNNING)
    assert store.accept_result(a) is True                          # repeating is safe either way
    assert env.store.job(job)["accepted_attempt"] == 1 and env.store.invariant_violations() == {}


# Rollbacks: a failure between the statements of one transaction leaves both tables as before.

class FaultAt:
    """A store fault hook that raises `error` at one point once armed, recording the points it passes."""

    def __init__(self, point, error):
        self.point, self.error, self.armed, self.seen = point, error, False, []

    def __call__(self, point):
        if self.armed:
            self.seen.append(point)
            if point == self.point:
                raise self.error(f"injected at {point}")


# fault point -> (a situation, an operation that passes through the point from there)
ROLLBACK_CASES = {
    "claim.jobs_updated": (queued, "claim"),
    "claim.previous_attempt_expired": (expired, "claim"),
    "renew.jobs_updated": (running, "renew"),
    "accept_result.jobs_updated": (running, "accept"),
    "fail_attempt.jobs_updated": (running, "fail"),
    "exhaust.jobs_updated": (expired_last, "claim"),
    "requeue_expired.jobs_updated": (expired, "requeue_expired"),
}


def test_every_fault_point_has_a_rollback_case():
    assert set(ROLLBACK_CASES) == set(FAULT_POINTS)


@pytest.mark.parametrize("error", [RuntimeError, SimulatedCrash])
@pytest.mark.parametrize("point", FAULT_POINTS)
def test_a_failure_inside_an_operation_rolls_back_both_tables(env, point, error):
    situation, operation = ROLLBACK_CASES[point]
    fault = FaultAt(point, error)
    env.store = env.new_store(fault=fault)
    job, a = situation(env)
    before = env.dump()
    fault.armed = True
    with pytest.raises(error, match="injected at"):
        OPERATIONS[operation](env, job, a)
    assert fault.seen[-1] == point
    assert env.dump() == before                                    # as a new connection sees them
    fault.armed = False
    result = OPERATIONS[operation](env, job, a)                    # the same store still works
    assert result is Refusal.EXHAUSTED if point == "exhaust.jobs_updated" else result
    assert env.store.invariant_violations() == {}


def test_a_bookkeeping_write_that_misses_its_row_rolls_back_the_job_update(env):
    job, a = running(env)
    env.backend.execute("UPDATE job_attempts SET outcome = 'expired', ended_at = :t WHERE job_id = :job",
                        t=env.backend.dialect.time(env.clock.now()), job=job)   # the tables now disagree
    before = env.dump()
    with pytest.raises(StoreInvariantError):
        env.store.accept_result(a)
    assert env.dump() == before                                    # the job was not marked succeeded


def test_a_database_error_in_the_last_statement_rolls_back_the_claim(env):
    job = env.store.submit({"n": 1}, {})
    other, _ = running(env)
    env.backend.execute("UPDATE job_attempts SET run_id = :taken WHERE job_id = :other",
                        taken=run_id(job, 1), other=other)         # the run id job's first attempt needs
    before = env.dump()
    with pytest.raises(env.backend.errors) as raised:
        env.store.claim(job, "worker-A", env.runs)                 # its INSERT breaks job_attempts_run_id
    assert env.backend.violation(raised.value) == ("unique", None)
    assert env.dump() == before                                    # the job is still queued, at attempt 0


# Conflict retries (offline: an injected conflict stands in for a deadlock or lock wait timeout)

class InjectedConflict(Exception):
    pass


class ConflictingSQLite(SQLiteDialect):
    @staticmethod
    def is_conflict(error):
        return isinstance(error, InjectedConflict)


def conflicts_at(point, times):
    """A fault hook raising InjectedConflict the first `times` times it passes point."""
    def fault(at):
        if at == point:
            fault.seen += 1
            if fault.seen <= times:
                raise InjectedConflict(at)
    fault.seen = 0
    return fault


@pytest.mark.parametrize("point, operation", [("claim.jobs_updated", "claim"),
                                              ("accept_result.jobs_updated", "accept")])
def test_an_operation_rolled_back_by_a_conflict_runs_again(sqlite_env, point, operation):
    env = sqlite_env
    fault = conflicts_at(point, CONFLICT_RETRIES - 1)
    env.store = env.new_store(fault=fault, dialect=ConflictingSQLite())
    job, a = (queued if operation == "claim" else running)(env)
    result = OPERATIONS[operation](env, job, a)
    assert isinstance(result, Claim) if operation == "claim" else result is True
    assert fault.seen == CONFLICT_RETRIES                          # rolled back twice, committed on the third run
    assert len(env.store.attempts(job)) == 1 and env.store.invariant_violations() == {}


def test_an_operation_gives_up_after_its_conflict_retries(sqlite_env):
    env = sqlite_env
    fault = conflicts_at("accept_result.jobs_updated", CONFLICT_RETRIES)
    env.store = env.new_store(fault=fault, dialect=ConflictingSQLite())
    job, a = running(env)
    before = env.dump()
    with pytest.raises(InjectedConflict):
        env.store.accept_result(a)
    assert fault.seen == CONFLICT_RETRIES and env.dump() == before


# Schema and constraints

def ddl_names(sql):
    """Table -> the names of its columns and constraints, as a schema file declares them."""
    names = {}
    for table, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\)", sql, flags=re.S):
        columns = {m.group(1) for line in body.splitlines()
                   if (m := re.match(r"\s+(\w+)\s", line)) and m.group(1) not in ("CONSTRAINT", "PRIMARY", "CHECK",
                                                                                 "FOREIGN")}
        names[table] = columns | {f"constraint {c}" for c in re.findall(r"CONSTRAINT (\w+)", body)}
    for table, constraint in re.findall(r"ALTER TABLE (\w+) ADD CONSTRAINT (\w+)", sql):
        names[table].add(f"constraint {constraint}")
    return names


def test_both_schema_files_declare_the_same_tables_columns_and_constraints():
    mysql = ddl_names((SCHEMA_DIR / "mysql.sql").read_text())
    assert mysql == ddl_names((SCHEMA_DIR / "sqlite.sql").read_text())
    assert set(mysql) == {"jobs", "job_attempts"}
    assert {"attempt_token", "lease_expires_at", "accepted_attempt", "version", "published_at",
            "constraint jobs_accepted_attempt", "constraint jobs_published_only_queued"} <= mysql["jobs"]
    assert {"renewals", "constraint job_attempts_run_id"} <= mysql["job_attempts"]


def test_the_schema_allows_exactly_the_statuses_and_outcomes_of_the_code():
    for name in ("mysql.sql", "sqlite.sql"):
        sql = (SCHEMA_DIR / name).read_text()
        statuses = re.search(r"status IN \(([^)]*)\)", sql).group(1)
        outcomes = re.search(r"outcome IN \(([^)]*)\)", sql).group(1)
        assert set(re.findall(r"'(\w+)'", statuses)) == {s.value for s in Status}
        assert set(re.findall(r"'(\w+)'", outcomes)) == {o.value for o in Outcome}


INSERT_JOB = ("INSERT INTO jobs (params, input_checksums, status, max_attempts, attempt_number, attempt_token,"
              " lease_expires_at, accepted_attempt, error, version, created_at, updated_at, finished_at, published_at)"
              " VALUES ('{}', '{}', :status, 3, :n, :token, :lease, :accepted, :error, 0, :t, :t, :finished,"
              " :published)")


@pytest.mark.parametrize("status, n, token, lease, accepted, error, finished, published, constraint", [
    ("running", 1, None, True, None, None, False, False, "jobs_running_has_lease"),
    ("queued", 0, "t" * 32, True, None, None, False, False, "jobs_running_has_lease"),
    ("succeeded", 1, None, False, None, None, True, False, "jobs_succeeded_has_one_result"),
    ("failed", 1, None, False, None, None, True, False, "jobs_failed_has_error"),
    ("failed", 1, None, False, None, "boom", False, False, "jobs_finished"),
    ("queued", 3, None, False, None, None, False, False, "jobs_queued_has_attempts_left"),
    ("running", 4, "t" * 32, True, None, None, False, False, "jobs_attempt_limit"),
    ("paused", 0, None, False, None, None, False, False, "jobs_status"),
    ("running", 1, "t" * 32, True, None, None, False, True, "jobs_published_only_queued"),
])
def test_inconsistent_job_rows_are_rejected(env, status, n, token, lease, accepted, error, finished, published,
                                            constraint):
    t = env.backend.dialect.time(env.clock.now())
    with pytest.raises(env.backend.errors) as raised:
        env.backend.execute(INSERT_JOB, status=status, n=n, token=token, lease=t if lease else None,
                            accepted=accepted, error=error, t=t, finished=t if finished else None,
                            published=t if published else None)
    assert env.backend.violation(raised.value) == ("check", constraint)


@pytest.mark.parametrize("change, constraint", [
    ("outcome = 'accepted'", "job_attempts_ended"),                        # ended, but no end time
    ("ended_at = :t", "job_attempts_ended"),                                # running, with an end time
    ("outcome = 'failed', ended_at = :t", "job_attempts_failed_has_error"),
    ("outcome = 'lost', ended_at = :t", "job_attempts_outcome"),
])
def test_inconsistent_attempt_rows_are_rejected(env, change, constraint):
    running(env)
    with pytest.raises(env.backend.errors) as raised:
        env.backend.execute(f"UPDATE job_attempts SET {change}", t=env.backend.dialect.time(env.clock.now()))
    assert env.backend.violation(raised.value) == ("check", constraint)


def test_run_ids_are_unique_and_a_job_accepts_only_its_own_attempts(env):
    job_a, _ = expired(env)
    env.store.claim(job_a, "worker-B", env.runs)                  # job_a has attempts 1 and 2
    job_b, _ = running(env)                                        # job_b has attempt 1 only
    with pytest.raises(env.backend.errors) as raised:
        env.backend.execute("UPDATE jobs SET status = 'succeeded', accepted_attempt = 2, attempt_token = NULL,"
                            " lease_expires_at = NULL, finished_at = :t WHERE job_id = :job",
                            t=env.backend.dialect.time(env.clock.now()), job=job_b)
    assert env.backend.violation(raised.value) == ("foreign key", None)
    with pytest.raises(env.backend.errors) as raised:
        env.backend.execute("UPDATE job_attempts SET run_id = 'same'")
    assert env.backend.violation(raised.value) == ("unique", None)


def test_the_invariant_check_reports_what_the_constraints_cannot_see(env):
    job, a = succeeded(env)
    t = env.backend.dialect.time(env.clock.now())
    env.backend.execute(                                           # a second accepted attempt, in the same folder
        "INSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id, output_dir, outcome,"
        " claimed_at, lease_expires_at, renewals, ended_at)"
        " VALUES (:job, 2, :token, 'worker-X', 'job-x', :folder, 'accepted', :t, :t, 0, :t)",
        job=job, token="e" * 32, folder=str(a.output_dir), t=t)
    assert env.store.invariant_violations() == {
        "succeeded without exactly one accepted attempt": [job],
        "attempt rows differ from attempt_number": [job],
        "attempts share an output folder": [job],
    }
