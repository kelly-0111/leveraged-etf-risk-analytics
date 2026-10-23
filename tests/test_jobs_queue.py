"""Delivery through a queue: the in-memory queue's Kafka semantics, submit_job(), and
Worker.serve() with commits, rewinds and malformed messages; then whole scenarios with the
reconciler, each ending with the guarantee check (WorkerEnv.check, tests/jobs_backends.py).

The queue is simulated.MemoryQueue, which models only what the job system relies on;
tests/test_jobs_kafka.py checks the same behaviour against a Kafka broker. The tests that
take `env` run on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL.

AI contribution: written with Claude Code (Opus 5.5).
"""
import inspect
import random
import time
from collections import Counter

import pytest

from etf_risk.jobs.queue import MAX_JOB_ID, MAX_JOB_ID_DIGITS, Delivery, encode, submit_job
from etf_risk.jobs.reconciler import PUBLICATION_GRACE, Pass
from etf_risk.jobs.simulated import MemoryQueue, PublishOutcome, SimulatedCrash, SimulatedPipeline
from etf_risk.jobs.store import TERMINAL, Refusal, Status
from etf_risk.jobs.worker import DELIVERY_RETRIES, WORKER_FAULT_POINTS, Result, Served, Worker
from jobs_backends import BACKENDS, LEASE, PARAMS, QueueEnv, failing_at, make_backend

GRACE = PUBLICATION_GRACE.total_seconds()


@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = QueueEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


def crash_at(point):
    assert point in WORKER_FAULT_POINTS

    def fault(at):
        if at == point:
            raise SimulatedCrash(point)
    return fault


# The in-memory queue

def test_a_new_group_starts_at_the_earliest_message():
    queue = MemoryQueue()
    publisher = queue.publisher()
    assert publisher.publish(1) and publisher.publish(2)        # before the group's first consumer
    consumer = queue.consumer("workers")
    assert [consumer.poll().job_id(), consumer.poll().job_id(), consumer.poll()] == [1, 2, None]


def test_only_a_commit_moves_the_group_on():
    queue = MemoryQueue()
    queue.publisher().publish(1)
    first = queue.consumer("workers")
    delivery = first.poll()
    assert first.poll() is None                                  # this consumer moved on, uncommitted
    assert queue.consumer("workers").poll() == delivery          # a restarted one gets the message again
    first.commit(delivery)
    assert queue.consumer("workers").poll() is None
    assert queue.consumer("others").poll() == delivery           # each group has its own position


def test_a_rewind_reads_the_message_again():
    queue = MemoryQueue()
    queue.publisher().publish(1)
    consumer = queue.consumer("workers")
    delivery = consumer.poll()
    consumer.rewind(delivery)
    assert consumer.poll() == delivery and consumer.poll() is None


def test_publish_outcomes():
    queue = MemoryQueue()
    publisher = queue.publisher([PublishOutcome.CONFIRMED, PublishOutcome.UNCONFIRMED, PublishOutcome.DROPPED])
    assert [publisher.publish(n) for n in (1, 2, 3, 4)] == [True, False, False, True]
    assert queue.job_ids() == [1, 2, 4]                          # an unconfirmed message may still be written


OVERSIZED = b"9" * 5000      # more digits than int() converts


@pytest.mark.parametrize("value, job_id", [
    (b"1", 1), (b"42", 42), (str(MAX_JOB_ID).encode(), MAX_JOB_ID),
    (b"", None), (b"0", None), (b"007", None), (b"-1", None), (b"+1", None), (b" 42", None), (b"42\n", None),
    (b"4.2", None), (b"1e3", None), ("٤٢".encode(), None), (b"not-a-job", None),
    (str(MAX_JOB_ID + 1).encode(), None),       # 19 digits, one more than SQLite's INTEGER holds
    (str(2**64 - 1).encode(), None),            # 20 digits: MySQL's BIGINT UNSIGNED maximum, outside the range too
    pytest.param(OVERSIZED, None, id="5000-digits"),
])
def test_a_delivery_carries_a_valid_job_id_or_none(value, job_id):
    assert Delivery(value, 0).job_id() == job_id


def test_an_oversized_payload_is_refused_before_any_conversion():
    with pytest.raises(ValueError):
        int(OVERSIZED)                          # what a parser that converts first would raise
    assert Delivery(OVERSIZED, 0).job_id() is None


def test_encode_writes_only_ids_that_job_id_reads_back():
    assert (MAX_JOB_ID, MAX_JOB_ID_DIGITS) == (2**63 - 1, 19)
    for job_id in (1, 42, MAX_JOB_ID):
        assert Delivery(encode(job_id), 0).job_id() == job_id
    for job_id in (0, -1, MAX_JOB_ID + 1):
        with pytest.raises(ValueError, match="outside the supported range"):
            encode(job_id)


# submit_job()

def test_a_claim_before_the_confirmation_is_recorded_leaves_it_unrecorded(env):
    """A fast worker consumes the message and finishes the job before the submitter records
    the confirmation: the record is refused, and nothing needs publishing again."""
    class ConsumedBeforeConfirmed:
        def publish(self, job_id):
            assert env.queue.publisher().publish(job_id)
            assert env.serve(env.worker("A")).handled == 1
            return True

    submitted = submit_job(env.admin, ConsumedBeforeConfirmed(), PARAMS, {})
    assert (submitted.published, submitted.recorded) == (True, False)
    assert env.admin.job(submitted.job_id)["status"] is Status.SUCCEEDED
    env.clock.advance(GRACE)
    assert env.reconciler().run_once() == Pass()
    env.check(submitted.job_id)


# Worker.serve()

def test_serve_commits_each_delivery_and_stops_when_idle(env):
    jobs = [env.submit().job_id for _ in range(3)]
    assert env.serve(env.worker("A")) == Served(handled=3)
    assert env.queue.committed["workers"] == 3
    assert [h.result for h in env.handled] == [Result.ACCEPTED] * 3
    for job in jobs:
        env.check(job)


def test_serve_stops_when_told(env):
    for _ in range(3):
        env.submit()
    worker = env.worker("A")
    served = worker.serve(env.queue.consumer("workers"), stop=lambda: len(env.handled) == 2,
                          on_handled=env.handled.append)
    assert served == Served(handled=2) and env.queue.committed["workers"] == 2


def test_an_error_before_the_acknowledgement_rewinds_and_the_job_runs_on_the_retry(env):
    job = env.submit().job_id
    worker = env.worker("A", store_fault=failing_at("claim.jobs_updated", times=1))   # the claim rolls back once
    assert env.serve(worker) == Served(handled=1, rewound=1)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED and env.queue.committed["workers"] == 1
    env.check(job)


def test_a_persistent_error_before_the_acknowledgement_is_raised_after_the_retries(env):
    """The claim fails every time. serve() tries the message again `retries` times, then
    raises, with the message uncommitted and the consumer rewound to it. The test also
    stops serve() after ten tries or five seconds, so that it fails instead of hanging when
    the retries are unbounded or the message is never read again."""
    job = env.submit().job_id
    fault, deadline = failing_at("claim.jobs_updated"), time.monotonic() + 5
    consumer = env.queue.consumer("workers")
    with pytest.raises(RuntimeError, match="injected at claim.jobs_updated"):
        env.worker("A", store_fault=fault).serve(consumer, retries=2, retry_delay=0,
                                                 stop=lambda: fault.calls >= 10 or time.monotonic() > deadline)
    assert fault.calls == 3                                         # the first try and two more
    assert "workers" not in env.queue.committed                     # nothing committed
    assert consumer.poll().job_id() == job                          # this consumer did not skip it either
    assert env.admin.job(job)["status"] is Status.QUEUED and env.admin.attempts(job) == []
    assert env.serve(env.worker("B")) == Served(handled=1)          # a restarted worker reads it again
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    env.check(job)


def test_each_message_gets_its_own_retries(env):
    jobs = [env.submit().job_id for _ in range(2)]
    claims = []

    def two_failed_claims_per_job(point):            # claims 1, 2, 4 and 5 fail; 3 and 6 hold
        if point == "claim.jobs_updated":
            claims.append(point)
            if len(claims) % 3:
                raise RuntimeError(f"injected at {point}")

    served = env.worker("A", store_fault=two_failed_claims_per_job).serve(
        env.queue.consumer("workers"), retries=2, retry_delay=0, stop_when_idle=True, on_handled=env.handled.append)
    assert served == Served(handled=2, rewound=4)    # with one count for both jobs, the second would raise
    for job in jobs:
        env.check(job)


def test_the_retry_setting_is_pinned():
    assert DELIVERY_RETRIES == 5
    assert inspect.signature(Worker.serve).parameters["retries"].default == DELIVERY_RETRIES


def test_an_error_after_the_acknowledgement_leaves_the_job_to_its_lease(env):
    job = env.submit().job_id
    worker = env.worker("A", store_fault=failing_at("accept_result.jobs_updated", times=1))
    assert env.serve(worker) == Served(failed_after_ack=1)        # committed, then the acceptance failed
    assert env.admin.job(job)["status"] is Status.RUNNING and env.queue.committed["workers"] == 1
    env.clock.advance(LEASE.total_seconds())
    assert env.reconciler().run_once() == Pass(requeued=1, published=1)
    assert env.serve(env.worker("B")) == Served(handled=1)
    assert env.admin.job(job)["accepted_attempt"] == 2
    env.check(job)


def test_a_failed_commit_does_not_stop_the_job(env):
    job = env.submit().job_id
    consumer = env.queue.consumer("workers", failing_commits=1)
    served = env.worker("A").serve(consumer, stop_when_idle=True, on_handled=env.handled.append)
    assert served == Served(handled=1, commit_failures=1)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED and "workers" not in env.queue.committed
    assert env.serve(env.worker("B")) == Served(handled=1)        # the uncommitted message comes back once
    assert env.handled[-1].reason is Refusal.SUCCEEDED and env.queue.committed["workers"] == 1
    env.check(job)


@pytest.mark.parametrize("payload", [OVERSIZED, str(MAX_JOB_ID + 1).encode(), b"0", b"not-a-job"],
                         ids=["5000-digits", "beyond-the-id-range", "zero", "text"])
def test_a_message_with_no_valid_job_id_is_committed_and_the_next_job_runs(env, payload):
    """A regression test: a 5,000-digit payload used to raise in int() outside serve()'s
    error handling, and an id beyond the range failed in the database, so the uncommitted
    message stopped the worker at every start."""
    env.queue.messages.append(payload)
    job = env.submit().job_id
    assert env.serve(env.worker("A")) == Served(handled=1, malformed=1)
    assert env.queue.committed["workers"] == 2
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    env.check(job)


def test_a_malformed_last_message_is_committed_too(env):
    """With no message after it, only its own commit moves the group past it, so a restarted
    worker does not read it again."""
    env.queue.messages.append(b"not a job id")
    assert env.serve(env.worker("A")) == Served(malformed=1)
    assert env.queue.committed["workers"] == 1
    assert env.serve(env.worker("B")) == Served()


# Whole scenarios

def test_a_lost_confirmation_leads_to_a_duplicate_that_is_refused(env):
    submitted = env.submit([PublishOutcome.UNCONFIRMED])          # written, but the confirmation was lost
    env.clock.advance(GRACE)
    assert env.reconciler().run_once() == Pass(published=1)       # published again: two messages
    assert env.serve(env.worker("A")) == Served(handled=2)
    assert [h.result for h in env.handled] == [Result.ACCEPTED, Result.SKIPPED]
    assert env.handled[1].reason is Refusal.SUCCEEDED and env.queue.committed["workers"] == 2
    env.check(submitted.job_id)


def test_a_crash_between_claim_and_commit(env):
    """A claims and dies before committing. The restarted consumer gets the message again and
    is refused while A's lease is live; once it expires, the reconciler requeues and
    publishes the job, and B runs attempt 2."""
    job = env.submit().job_id
    with pytest.raises(SimulatedCrash):
        env.serve(env.worker("A", fault=crash_at("after_claim")))
    assert "workers" not in env.queue.committed                   # nothing committed
    assert env.serve(env.worker("B")) == Served(handled=1)
    assert env.handled[-1].reason is Refusal.LEASE_HELD and env.queue.committed["workers"] == 1
    env.clock.advance(LEASE.total_seconds())
    assert env.reconciler().run_once() == Pass(requeued=1, published=1)
    assert env.serve(env.worker("B")) == Served(handled=1)
    j = env.admin.job(job)
    assert (j["status"], j["accepted_attempt"]) == (Status.SUCCEEDED, 2)
    env.check(job)


def test_the_job_9_timeline(env):
    """docs/job-queue.md, "A job, two failures", row by row: the submitter's confirmation is
    lost, A claims and dies before committing, the reconciler leaves the running job alone,
    the restarted worker is refused while A's lease holds, and once it expires the reconciler
    requeues and publishes the job in one pass."""
    job = env.submit([PublishOutcome.UNCONFIRMED]).job_id                # 0 s: written, not confirmed
    assert env.admin.job(job)["published_at"] is None and env.queue.job_ids() == [job]
    env.clock.advance(1)                                                 # 1 s: A claims and dies
    with pytest.raises(SimulatedCrash):
        env.serve(env.worker("A", fault=crash_at("after_claim")))
    assert "workers" not in env.queue.committed
    env.clock.advance(29)                                                # 30 s: running, so nothing to publish
    assert env.reconciler().run_once() == Pass()
    env.clock.advance(16)                                                # 46 s: A restarted gets the same message
    restarted = env.worker("A")
    assert env.serve(restarted) == Served(handled=1)
    assert env.handled[-1].reason is Refusal.LEASE_HELD and env.queue.committed["workers"] == 1
    env.clock.advance(15)                                                # 61 s: A's lease has expired
    assert env.reconciler().run_once() == Pass(requeued=1, published=1)
    assert env.queue.job_ids() == [job, job]
    env.clock.advance(1)                                                 # 62 s: attempt 2 runs and is accepted
    assert env.serve(restarted) == Served(handled=1)
    j, attempts = env.admin.job(job), env.admin.attempts(job)
    assert (j["status"], j["accepted_attempt"]) == (Status.SUCCEEDED, 2)
    assert [a["outcome"] for a in attempts] == ["expired", "accepted"]
    env.check(job)


@pytest.mark.parametrize("seed", range(3))
def test_every_job_ends_with_at_most_one_result_under_lost_publications_and_crashes(env, seed):
    """Ten jobs; every publication may be confirmed, unconfirmed or dropped; every worker may
    die at any of its fault points or in the middle of a run, and some runs fail and are
    retried. Rounds of a restarted worker, a lease's worth of time and a reconciler pass
    repeat until no job is left queued or running. Every job then has at most one accepted
    result (exactly one if it succeeded), told to the worker that got it unless that worker
    died first."""
    rng = random.Random(seed)

    def outcomes():
        while True:
            yield rng.choice(list(PublishOutcome))

    jobs = [env.submit(outcomes()).job_id for _ in range(10)]
    current, lost = {}, Counter()

    def fault(point):
        if rng.random() < 0.1:
            if point == "after_accept":
                lost[current["job"]] += 1                                              # accepted, never told
            raise SimulatedCrash(point)

    def on_step(step, claim):
        current["job"] = claim.job_id
        if rng.random() < 0.05:
            raise SimulatedCrash(f"step {step}")

    for round_number in range(60):
        pipeline = SimulatedPipeline(on_step=on_step, fail_at={2: True} if rng.random() < 0.2 else None)
        try:
            env.serve(env.worker(f"round-{round_number}", pipeline, fault=fault))
        except SimulatedCrash:
            pass
        env.clock.advance(LEASE.total_seconds())
        env.reconciler(outcomes()).run_once()
        if all(env.admin.job(job)["status"] in TERMINAL for job in jobs):
            break
    assert [job for job in jobs if env.admin.job(job)["status"] not in TERMINAL] == []
    for job in jobs:
        env.check(job, lost_acceptances=lost[job])
