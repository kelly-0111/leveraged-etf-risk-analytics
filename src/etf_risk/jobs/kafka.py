"""Kafka adapters for the job queue (spec §11): a publisher that waits for the broker's
confirmation, and a consumer whose group moves on only when the worker commits.

Settings, each pinned by tests/test_jobs_kafka.py:
- producer: acks=all and idempotence on. With one broker and no replica, acks=all means
  that broker wrote the message. librdkafka gives up on a message after the confirmation
  timeout, the same time publish() waits, so publish() returns a final answer.
- consumer: enable.auto.commit=false, since the worker commits after its claim, and
  enable.auto.offset.store=false, so nothing but those commits records a position.
  auto.offset.reset=earliest: a consumer group that has never committed starts at the
  first message, so a job published before its group first starts is still delivered;
  librdkafka's default, latest, would skip it.
- consumer group timing, from etf_risk.jobs.timing:
  - group.protocol=classic, since session.timeout.ms is ignored under "consumer";
  - session.timeout.ms 15 s and heartbeat.interval.ms 3 s: a stopped or crashed worker leaves
    the group well before its lease can expire;
  - max.poll.interval.ms above the attempt limit plus the kill grace: serve() does not poll
    while a pipeline runs, and a run that outlasted the interval would make librdkafka leave
    the group, so a standby could start a second job on this machine. The offset is
    committed before the run, so the job itself would not be delivered again.
- socket.timeout.ms 10 s for both, so a commit or publication waits for a broker at most that
  long per request.
Consumer errors that are not fatal, such as a poll after the poll interval was exceeded, are
logged and written to the worker's event log (consumer_error).

confluent-kafka is imported only when an adapter is created. It is in the `jobs`
dependency group (pyproject.toml, locked in uv.lock), not among the core dependencies: the
Kafka runs use uv run --group jobs. Topics are created
explicitly (create_topic: one partition, no replica), since the broker in
docker/compose.yaml does not create them on first use.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_kafka.py,
offline and against Kafka 4.3.1 (docker/compose.yaml).
"""
from __future__ import annotations

import logging
from datetime import timedelta

from etf_risk.jobs.events import NO_EVENTS, EventLog
from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, Delivery, encode
from etf_risk.jobs.timing import DEFAULT_TIMING, Timing

log = logging.getLogger(__name__)


def _ms(seconds: float) -> int:
    return int(round(seconds * 1000))


def producer_config(bootstrap: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT,
                    timing: Timing = DEFAULT_TIMING) -> dict:
    return {"bootstrap.servers": bootstrap, "acks": "all", "enable.idempotence": True, "linger.ms": 0,
            "message.timeout.ms": int(confirmation_timeout.total_seconds() * 1000),
            "socket.timeout.ms": _ms(timing.socket_timeout)}


def consumer_config(bootstrap: str, group: str, *, timing: Timing = DEFAULT_TIMING) -> dict:
    return {"bootstrap.servers": bootstrap, "group.id": group, "enable.auto.commit": False,
            "enable.auto.offset.store": False, "auto.offset.reset": "earliest", "group.protocol": "classic",
            "session.timeout.ms": _ms(timing.session_timeout), "heartbeat.interval.ms": _ms(timing.heartbeat_interval),
            "max.poll.interval.ms": _ms(timing.max_poll_interval), "socket.timeout.ms": _ms(timing.socket_timeout)}


class KafkaPublisher:
    def __init__(self, bootstrap: str, topic: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT,
                 timing: Timing = DEFAULT_TIMING):
        from confluent_kafka import Producer
        self.topic = topic
        self._wait = confirmation_timeout.total_seconds() + 1.0   # the report comes by the message timeout
        self._producer = Producer({**producer_config(bootstrap, confirmation_timeout=confirmation_timeout,
                                                     timing=timing), "logger": log})

    def publish(self, job_id: int) -> bool:
        """Send the job id and wait for the broker's confirmation. True only if it arrived;
        False may still mean the message was written and its confirmation lost."""
        from confluent_kafka import KafkaException
        report: dict = {}
        try:
            self._producer.produce(self.topic, key=encode(job_id), value=encode(job_id),
                                   on_delivery=lambda error, message: report.setdefault("error", error))
        except (BufferError, KafkaException):
            log.warning("could not send job %s", job_id, exc_info=True)
            return False
        self._producer.flush(self._wait)
        if report.get("error") is not None:
            log.warning("job %s: publication not confirmed: %s", job_id, report["error"])
        return "error" in report and report["error"] is None

    def close(self) -> None:
        self._producer.flush(self._wait)


class KafkaConsumer:
    def __init__(self, bootstrap: str, topic: str, group: str, *, settings: dict | None = None,
                 timing: Timing = DEFAULT_TIMING, events: EventLog = NO_EVENTS):
        """settings override consumer_config(); the tests use it to show why earliest matters,
        and to shorten the poll interval."""
        from confluent_kafka import Consumer
        self._consumer = Consumer({**consumer_config(bootstrap, group, timing=timing), **(settings or {}),
                                   "logger": log})
        self._consumer.subscribe([topic])
        self._closed = False
        self.events = events

    def poll(self, timeout: float) -> Delivery | None:
        from confluent_kafka import KafkaException
        message = self._consumer.poll(timeout)
        if message is None:
            return None
        if message.error() is not None:
            if message.error().fatal():
                raise KafkaException(message.error())
            log.warning("consumer error: %s", message.error())
            self.events.log("consumer_error", code=message.error().name(), reason=message.error().str())
            return None
        return Delivery(message.value() or b"", (message.topic(), message.partition(), message.offset()))

    def commit(self, delivery: Delivery) -> None:
        from confluent_kafka import TopicPartition
        topic, partition, offset = delivery.position
        self._consumer.commit(offsets=[TopicPartition(topic, partition, offset + 1)], asynchronous=False)

    def rewind(self, delivery: Delivery) -> None:
        from confluent_kafka import TopicPartition
        topic, partition, offset = delivery.position
        self._consumer.seek(TopicPartition(topic, partition, offset))

    def assigned(self) -> bool:
        """Whether the group has given this consumer its partition yet."""
        return bool(self._consumer.assignment())

    def close(self) -> None:
        """Leave the group without committing anything; closing again does nothing."""
        if not self._closed:
            self._closed = True
            self._consumer.close()


def create_topic(bootstrap: str, name: str, *, timeout: float = 30.0) -> None:
    from confluent_kafka.admin import AdminClient, NewTopic
    admin = AdminClient({"bootstrap.servers": bootstrap, "logger": log})
    admin.create_topics([NewTopic(name, num_partitions=1, replication_factor=1)],
                        operation_timeout=timeout)[name].result(timeout)


def delete_topic(bootstrap: str, name: str, *, timeout: float = 30.0) -> None:
    from confluent_kafka.admin import AdminClient
    admin = AdminClient({"bootstrap.servers": bootstrap, "logger": log})
    admin.delete_topics([name], operation_timeout=timeout)[name].result(timeout)
