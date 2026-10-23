"""The reconciler and the publication record: requeue_expired(), mark_published(), the grace
period before a never-confirmed job is published again, competing reconcilers, and the
late confirmation that must not mark a job as published.

The tests run on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL (tests/jobs_backends.py),
with the in-memory queue (simulated.MemoryQueue); tests/test_jobs_kafka.py runs the
reconciler with Kafka.

AI contribution: written with Claude Code (Opus 5.5).
"""
import threading
from datetime import timedelta

import pytest

from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT
from etf_risk.jobs.reconciler import PUBLICATION_GRACE, RECONCILE_INTERVAL, Pass, Reconciler
from etf_risk.jobs.simulated import PublishOutcome, SimulatedCrash, SimulatedPipeline
from etf_risk.jobs.store import ExpiredLease, Outcome, Status
from jobs_backends import BACKENDS, DIGEST, LEASE, PARAMS, QueueEnv, make_backend, run_together

GRACE = PUBLICATION_GRACE.total_seconds()


@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = QueueEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


def lapsed(env, **kwargs):
    """A job claimed by worker A, whose lease has just expired, and A's claim."""
    job = env.admin.submit(PARAMS, {}, **kwargs)
    a = env.admin.claim(job, "worker-A", env.runs)
    env.clock.advance(LEASE.total_seconds())
    return job, a


def crash_at_step(step):
    def on_step(at, claim):
        if at == step:
            raise SimulatedCrash(f"step {step}")
    return on_step


# requeue_expired: the reconciler's change to an expired lease

def test_an_expired_lease_is_requeued_with_no_publication_recorded(env):
    job, a = lapsed(env)
    assert env.admin.expired_leases() == [ExpiredLease(job, a.token)]
    assert env.admin.requeue_expired(job, a.token) is Status.QUEUED
    j = env.admin.job(job)
    assert (j["status"], j["attempt_token"], j["lease_expires_at"], j["published_at"]) == (
        Status.QUEUED, None, None, None)
    assert [x["outcome"] for x in env.admin.attempts(job)] == [Outcome.EXPIRED]
    assert not env.admin.renew(a) and not env.admin.accept_result(a, DIGEST)           # A is fenced off
    assert env.admin.claim(job, "worker-B", env.runs).attempt_number == 2
    assert env.admin.invariant_violations() == {}


def test_a_lease_is_requeued_only_once_it_has_expired(env):
    job = env.admin.submit(PARAMS, {})
    a = env.admin.claim(job, "worker-A", env.runs)
    env.clock.advance(LEASE.total_seconds() - 0.001)
    before = env.dump()
    assert env.admin.expired_leases() == [] and env.admin.requeue_expired(job, a.token) is None
    assert env.dump() == before
    env.clock.advance(0.001)                       # lease_expires_at == now counts as expired, as for a takeover
    assert env.admin.requeue_expired(job, a.token) is Status.QUEUED


def test_with_no_attempts_left_an_expired_lease_fails_the_job(env):
    job, a = lapsed(env, max_attempts=1)
    assert env.admin.requeue_expired(job, a.token) is Status.FAILED
    j = env.admin.job(job)
    assert j["status"] is Status.FAILED and "attempts exhausted" in j["error"]
    assert [x["outcome"] for x in env.admin.attempts(job)] == [Outcome.EXPIRED]
    assert env.admin.invariant_violations() == {}


def test_a_requeue_whose_token_no_longer_holds_changes_nothing(env):
    job, a = lapsed(env)
    lease = env.admin.expired_leases()[0]                                       # the reconciler reads,
    b = env.admin.claim(job, "worker-B", env.runs)                              # a takeover happens,
    before = env.dump()
    assert env.admin.requeue_expired(lease.job_id, lease.token) is None         # and its change finds B's token
    assert env.dump() == before and env.admin.accept_result(b, DIGEST)


def test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too(env):
    """The token guard on its own: the reconciler read A's token, B took the job over, and
    B's lease expired as well before the reconciler's change. The lease condition alone
    would let the change through and requeue B's attempt on A's token."""
    job, a = lapsed(env)
    lease = env.admin.expired_leases()[0]                                       # A's token
    b = env.admin.claim(job, "worker-B", env.runs)                              # a takeover
    env.clock.advance(LEASE.total_seconds())                                    # B's lease expires too
    before = env.dump()
    assert env.admin.requeue_expired(lease.job_id, lease.token) is None
    assert env.dump() == before
    assert env.admin.requeue_expired(job, b.token) is Status.QUEUED             # B's own token: requeued


def test_a_stale_token_is_refused_on_the_last_attempt_too(env):
    """The same on the path that fails a job. The reconciler read A's token, B took the job
    over on its last attempt, and B's lease expired as well. Without the token guard in the
    update that exhausts a job, A's stale token would fail the job through B's attempt."""
    job, a = lapsed(env, max_attempts=2)
    lease = env.admin.expired_leases()[0]                                       # A's token
    b = env.admin.claim(job, "worker-B", env.runs)                              # a takeover: attempt 2 of 2
    env.clock.advance(LEASE.total_seconds())                                    # B's lease expires too
    before = env.dump()
    assert env.admin.requeue_expired(lease.job_id, lease.token) is None
    assert env.dump() == before
    assert env.admin.requeue_expired(job, b.token) is Status.FAILED             # B's own token: none left


# mark_published: recording a confirmed publication

def test_a_confirmed_publication_is_recorded_once(env):
    submitted = env.submit()
    assert (submitted.published, submitted.recorded) == (True, True)
    j = env.admin.job(submitted.job_id)
    assert j["published_at"] == env.clock.now() and j["version"] == 1
    assert not env.admin.mark_published(submitted.job_id, 0) and not env.admin.mark_published(submitted.job_id, 1)
    assert env.queue.job_ids() == [submitted.job_id] and env.admin.unconfirmed() == []


@pytest.mark.parametrize("outcome", [PublishOutcome.UNCONFIRMED, PublishOutcome.DROPPED])
def test_an_unconfirmed_publication_is_not_recorded(env, outcome):
    submitted = env.submit([outcome])
    assert (submitted.published, submitted.recorded) == (False, False)
    assert env.admin.job(submitted.job_id)["published_at"] is None
    assert [j.job_id for j in env.admin.unconfirmed()] == [submitted.job_id]
    assert env.queue.job_ids() == ([submitted.job_id] if outcome is PublishOutcome.UNCONFIRMED else [])


def test_a_confirmation_after_the_job_moved_on_is_not_recorded(env):
    """The job is published and the broker confirms, but before the confirmation is recorded,
    a worker consumes the message, claims the job and fails it back to queued. The message
    is gone; recording the confirmation now would leave a queued job that nothing delivers.
    The version guard refuses it, so the reconciler publishes the job again."""
    job = env.admin.submit(PARAMS, {})
    assert env.queue.publisher().publish(job)                                   # confirmed, not yet recorded
    assert env.serve(env.worker("A", SimulatedPipeline(fail_at={1: True}))).handled == 1
    assert env.admin.job(job)["status"] is Status.QUEUED                        # failed back to queued
    assert not env.admin.mark_published(job, 0)                                 # the late confirmation
    assert env.admin.job(job)["published_at"] is None
    assert env.reconciler().run_once() == Pass(published=1)
    assert env.queue.job_ids() == [job, job]
    assert env.serve(env.worker("B")).handled == 1
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    env.check(job)


# The grace period before a never-confirmed job is published again

def test_the_settings_are_pinned():
    assert (PUBLICATION_GRACE, CONFIRMATION_TIMEOUT, RECONCILE_INTERVAL) == (
        timedelta(seconds=30), timedelta(seconds=10), timedelta(seconds=5))


@pytest.mark.parametrize("grace", [CONFIRMATION_TIMEOUT, CONFIRMATION_TIMEOUT - timedelta(seconds=1)])
def test_a_grace_no_longer_than_the_confirmation_timeout_is_refused(grace):
    with pytest.raises(ValueError, match="must exceed the confirmation timeout"):
        Reconciler(None, None, publication_grace=grace)


def test_a_never_confirmed_job_is_published_again_once_the_grace_has_passed(env):
    submitted = env.submit([PublishOutcome.DROPPED])                            # the submitter's message was lost
    reconciler = env.reconciler()
    env.clock.advance(GRACE - 0.001)
    assert reconciler.run_once() == Pass(waiting=1) and env.queue.job_ids() == []
    env.clock.advance(0.001)
    assert reconciler.run_once() == Pass(published=1) and env.queue.job_ids() == [submitted.job_id]
    assert env.admin.job(submitted.job_id)["published_at"] == env.clock.now()
    assert reconciler.run_once() == Pass()                                      # recorded: nothing more to do


def test_a_requeued_job_is_published_at_once(env):
    submitted = env.submit()
    assert env.serve(env.worker("A", SimulatedPipeline(fail_at={2: True}))).handled == 1
    assert env.admin.job(submitted.job_id)["status"] is Status.QUEUED           # no time has passed
    assert env.reconciler().run_once() == Pass(published=1)
    assert env.queue.job_ids() == [submitted.job_id] * 2


def test_an_unconfirmed_republication_is_tried_again_on_the_next_pass(env):
    submitted = env.submit([PublishOutcome.DROPPED])
    env.clock.advance(GRACE)
    reconciler = env.reconciler([PublishOutcome.DROPPED])
    assert reconciler.run_once() == Pass(unconfirmed=1)
    assert reconciler.run_once() == Pass(published=1) and env.queue.job_ids() == [submitted.job_id]


# Whole passes

def test_an_expired_lease_is_requeued_and_published_in_one_pass(env):
    submitted = env.submit()
    with pytest.raises(SimulatedCrash):                                         # A dies mid-run, after its commit
        env.serve(env.worker("A", SimulatedPipeline(on_step=crash_at_step(2))))
    assert env.reconciler().run_once() == Pass()                               # the lease is still live
    env.clock.advance(LEASE.total_seconds())
    assert env.reconciler().run_once() == Pass(requeued=1, published=1)
    assert env.serve(env.worker("B")).handled == 1
    j = env.admin.job(submitted.job_id)
    assert j["status"] is Status.SUCCEEDED and j["accepted_attempt"] == 2
    env.check(submitted.job_id)


def test_two_reconcilers_at_once_requeue_each_job_once(env):
    jobs = [lapsed(env)[0] for _ in range(5)]
    passes = run_together(env.reconciler().run_once, env.reconciler().run_once)
    assert sum(p.requeued for p in passes) == 5 and sum(p.published for p in passes) == 5
    assert sum(p.failed + p.unconfirmed + p.waiting for p in passes) == 0
    for job in jobs:                                    # one requeue and one recorded publication per job
        assert [x["outcome"] for x in env.admin.attempts(job)] == [Outcome.EXPIRED]
        assert env.admin.job(job)["published_at"] is not None
    assert set(env.queue.job_ids()) == set(jobs)        # a job may have been published twice
    assert env.admin.invariant_violations() == {}


def run_in_thread(reconciler):
    """reconciler.run() in a thread, 10 ms between passes; the test owns the stop event."""
    stop = threading.Event()
    thread = threading.Thread(target=reconciler.run, args=(stop,), kwargs={"interval": timedelta(milliseconds=10)},
                              daemon=True)
    thread.start()
    return stop, thread


def test_run_logs_a_failing_pass_and_goes_on(env, caplog):
    """The first publication raises, and a later pass publishes the job. The test stops the
    loop itself, after the second publication or after five seconds, whatever the publisher
    does."""
    job = env.admin.submit(PARAMS, {})                  # never published
    env.clock.advance(GRACE)
    calls, published = [], threading.Event()

    class FlakyPublisher:
        def publish(self, job_id):
            calls.append(job_id)
            if len(calls) == 1:
                raise ConnectionError("broker unreachable")
            published.set()
            return env.queue.publisher().publish(job_id)

    stop, thread = run_in_thread(Reconciler(env.new_store(), FlakyPublisher()))
    published.wait(timeout=5)
    stop.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert calls == [job, job] and env.queue.job_ids() == [job]
    assert env.admin.job(job)["published_at"] is not None
    assert "reconciler pass failed" in caplog.text


def test_run_ends_when_stop_is_set_whatever_the_publisher_does(env):
    env.admin.submit(PARAMS, {})
    env.clock.advance(GRACE)

    class NeverConfirms:
        def publish(self, job_id):
            return False

    stop, thread = run_in_thread(Reconciler(env.new_store(), NeverConfirms()))
    thread.join(timeout=0.2)
    assert thread.is_alive()                             # passes go on while nothing is confirmed
    stop.set()
    thread.join(timeout=5)
    assert not thread.is_alive()
