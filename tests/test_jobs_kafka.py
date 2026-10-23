"""The Kafka adapters, offline and against a broker.

Offline, always: the producer's and the consumer's settings (acks=all, idempotence, the
message timeout equal to the confirmation timeout; no auto-commit, earliest).
Against Kafka (skipped unless ETF_RISK_KAFKA_BOOTSTRAP is set), each test on a topic of
its own (KafkaTopic, tests/jobs_backends.py):
- jobs published before a fresh consumer group starts are all delivered, and with latest,
  librdkafka's default, the same group would get none of them;
- publish() returns True once the broker confirmed, and False for an unreachable broker;
- an uncommitted message reaches the group's next consumer, a committed one does not;
- a rewind delivers the same message again;
- end to end, submit_job(), Worker.serve() and the reconciler, with the job table on SQLite
  and, with ETF_RISK_MYSQL_URL set, on MySQL; an oversized payload ahead of a job is
  committed and skipped; after a persistent error before the acknowledgement, serve()
  gives up with the message uncommitted, for a restarted worker.

    docker compose -f docker/compose.yaml up -d --wait kafka mysql
    ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 \\
        uv run --with 'confluent-kafka==2.16.0' --with 'pymysql[rsa]==1.1.1' python -m pytest tests/test_jobs_*.py
    docker compose -f docker/compose.yaml down -v

AI contribution: written with Claude Code (Opus 5.5).
"""
import time
from datetime import timedelta

import pytest

from etf_risk.jobs.kafka import consumer_config, producer_config
from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, submit_job
from etf_risk.jobs.reconciler import Pass, Reconciler
from etf_risk.jobs.simulated import SimulatedCrash
from etf_risk.jobs.store import Refusal, Status
from etf_risk.jobs.worker import Result, Served
from jobs_backends import (BACKENDS, LEASE, PARAMS, KafkaTopic, WorkerEnv, failing_at, make_backend, needs_kafka,
                           poll_after_assignment, poll_deliveries)


# Offline

def test_the_producer_waits_for_the_broker_and_is_idempotent():
    config = producer_config("broker:9092")
    assert (config["acks"], config["enable.idempotence"]) == ("all", True)
    assert config["message.timeout.ms"] == CONFIRMATION_TIMEOUT.total_seconds() * 1000 == 10_000


def test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message():
    config = consumer_config("broker:9092", "workers")
    assert (config["group.id"], config["enable.auto.commit"], config["enable.auto.offset.store"],
            config["auto.offset.reset"]) == ("workers", False, False, "earliest")


def test_an_unreachable_broker_gives_false():
    pytest.importorskip("confluent_kafka")
    from etf_risk.jobs.kafka import KafkaPublisher
    publisher = KafkaPublisher("127.0.0.1:1", "nowhere", confirmation_timeout=timedelta(seconds=2))
    started = time.monotonic()
    assert publisher.publish(1) is False
    assert time.monotonic() - started < 10


# Against Kafka

@pytest.fixture
def topic():
    topic = KafkaTopic()
    yield topic
    topic.close()


@needs_kafka
def test_jobs_published_before_a_fresh_group_starts_are_all_delivered(topic):
    publisher = topic.publisher()
    assert all(publisher.publish(job) for job in (1, 2, 3))
    consumer = topic.consumer(topic.group())                        # a group that never existed
    assert [d.job_id() for d in poll_deliveries(consumer, 3)] == [1, 2, 3]


@needs_kafka
def test_with_latest_a_fresh_group_would_miss_them(topic):
    publisher = topic.publisher()
    assert all(publisher.publish(job) for job in (1, 2, 3))
    consumer = topic.consumer(topic.group(), settings={"auto.offset.reset": "latest"})
    assert poll_after_assignment(consumer) == []


@needs_kafka
def test_a_confirmed_message_is_there_when_publish_returns(topic):
    assert topic.publisher().publish(7)
    [delivery] = poll_deliveries(topic.consumer(topic.group()), 1)
    assert delivery.job_id() == 7 and delivery.position == (topic.name, 0, 0)


@needs_kafka
def test_an_uncommitted_message_reaches_the_groups_next_consumer_and_a_committed_one_does_not(topic):
    assert topic.publisher().publish(5)
    group = topic.group()
    first = topic.consumer(group)
    [delivery] = poll_deliveries(first, 1)
    first.close()               # leaves the group without committing; a crashed worker leaves after its session timeout
    second = topic.consumer(group)
    [again] = poll_deliveries(second, 1)
    assert again == delivery
    second.commit(again)
    second.close()
    assert poll_after_assignment(topic.consumer(group)) == []


@needs_kafka
def test_a_rewind_delivers_the_same_message_again(topic):
    publisher = topic.publisher()
    assert publisher.publish(5) and publisher.publish(6)
    consumer = topic.consumer(topic.group())
    [first] = poll_deliveries(consumer, 1)
    consumer.rewind(first)
    assert [d.job_id() for d in poll_deliveries(consumer, 2)] == [5, 6]


# End to end: the job table, Kafka, workers and the reconciler

@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = WorkerEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


def serve(env, worker, consumer, count, *, timeout=60.0):
    """worker handles deliveries until `count` more were handled, or until timeout."""
    target, deadline = len(env.handled) + count, time.monotonic() + timeout
    return worker.serve(consumer, stop=lambda: len(env.handled) >= target or time.monotonic() > deadline,
                        poll_timeout=0.5, retry_delay=0, on_handled=env.handled.append)


def crash_after_claim(point):
    if point == "after_claim":
        raise SimulatedCrash(point)


@needs_kafka
def test_jobs_run_once_each_and_a_duplicate_publication_is_refused(env, topic):
    publisher = topic.publisher()
    submitted = [submit_job(env.admin, publisher, PARAMS, {}) for _ in range(3)]
    assert all(s.published and s.recorded for s in submitted)
    worker, consumer = env.worker("A"), topic.consumer(topic.group())
    assert serve(env, worker, consumer, 3) == Served(handled=3)
    assert [h.result for h in env.handled] == [Result.ACCEPTED] * 3
    assert publisher.publish(submitted[0].job_id)                    # a duplicate publication
    assert serve(env, worker, consumer, 1) == Served(handled=1)
    assert env.handled[-1].reason is Refusal.SUCCEEDED
    for s in submitted:
        env.check(s.job_id)


@needs_kafka
def test_a_crash_between_claim_and_commit(env, topic):
    publisher, group = topic.publisher(), topic.group()
    job = submit_job(env.admin, publisher, PARAMS, {}).job_id
    crashing = topic.consumer(group)
    with pytest.raises(SimulatedCrash):
        serve(env, env.worker("A", fault=crash_after_claim), crashing, 1)
    crashing.close()                                                 # gone, with nothing committed
    worker, restarted = env.worker("B"), topic.consumer(group)
    assert serve(env, worker, restarted, 1) == Served(handled=1)     # the same message, refused while A's lease holds
    assert env.handled[-1].reason is Refusal.LEASE_HELD
    env.clock.advance(LEASE.total_seconds())
    assert Reconciler(env.new_store(), publisher).run_once() == Pass(requeued=1, published=1)
    assert serve(env, worker, restarted, 1) == Served(handled=1)
    j = env.admin.job(job)
    assert (j["status"], j["accepted_attempt"]) == (Status.SUCCEEDED, 2)
    env.check(job)


@needs_kafka
def test_an_oversized_payload_is_committed_and_the_next_job_runs(env, topic):
    """A regression test: a 5,000-digit payload ahead of a job used to stop the worker in
    int(), uncommitted, at every start. Now both messages are committed and the job runs."""
    group = topic.group()
    topic.produce_raw(b"9" * 5000)
    job = submit_job(env.admin, topic.publisher(), PARAMS, {}).job_id
    consumer = topic.consumer(group)
    assert serve(env, env.worker("A"), consumer, 1) == Served(handled=1, malformed=1)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    consumer.close()
    assert poll_after_assignment(topic.consumer(group)) == []      # both messages were committed
    env.check(job)


@needs_kafka
def test_a_persistent_error_leaves_the_message_for_a_restarted_worker(env, topic):
    """Every claim fails: serve() rewinds twice with a seek, then raises. Nothing was
    committed, so the group's next consumer gets the message. The stop condition ends
    serve() after ten tries or a minute, should the retries be unbounded."""
    group = topic.group()
    job = submit_job(env.admin, topic.publisher(), PARAMS, {}).job_id
    fault, deadline, failing = failing_at("claim.jobs_updated"), time.monotonic() + 60, topic.consumer(group)
    with pytest.raises(RuntimeError, match="injected at claim.jobs_updated"):
        env.worker("A", store_fault=fault).serve(failing, retries=2, retry_delay=0, poll_timeout=0.5,
                                                 stop=lambda: fault.calls >= 10 or time.monotonic() > deadline)
    assert fault.calls == 3
    failing.close()                                                  # leaves the group with nothing committed
    assert serve(env, env.worker("B"), topic.consumer(group), 1) == Served(handled=1)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    env.check(job)
