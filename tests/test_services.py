"""etf_risk.services: memory peaks, the count of other projects' containers, the
readiness wait, and the whole-session container monitor, with a fake docker on PATH, a
fake clock and stand-in event streams, so neither Docker nor a service is needed.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import sys
import time

import pytest

from etf_risk import services

FAKE_DOCKER = r"""#!/bin/sh
# Answers the calls etf_risk.services makes, from FAKE_* variables.
case "$*" in
  *"exec -T mysql cat"*) printf '%s\n%s\n' "$FAKE_PEAK" "$FAKE_LIMIT" ;;
  *"exec -T kafka cat"*) echo "cat: /sys/fs/cgroup/memory.peak: No such file or directory" >&2
                         echo 671088640; exit 1 ;;
  "ps --format"*) printf '%s' "$FAKE_PS" ;;
  *) echo "unexpected call: $*" >&2; exit 2 ;;
esac
"""


@pytest.fixture
def fake_docker(tmp_path, monkeypatch):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    docker = bin_dir / "docker"
    docker.write_text(FAKE_DOCKER)
    docker.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")
    return monkeypatch


class FakeTime:
    def __init__(self):
        self.now = 0.0

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


def test_a_peak_is_read_with_its_limit(fake_docker, capsys):
    fake_docker.setenv("FAKE_PEAK", str(400 * 2**20))
    fake_docker.setenv("FAKE_LIMIT", str(512 * 2**20))
    peak = services.memory_peak("mysql")
    assert (peak.peak_bytes, peak.limit_bytes, peak.fraction) == (400 * 2**20, 512 * 2**20, 400 / 512)
    assert services.main(["peaks", "mysql"]) == 0
    assert capsys.readouterr().out == "mysql: memory.peak 400 MiB of 512 MiB (78%) (cgroup, includes page cache)\n"


def test_no_limit_and_a_missing_peak_are_reported_as_such(fake_docker, capsys):
    fake_docker.setenv("FAKE_PEAK", str(2**20))
    fake_docker.setenv("FAKE_LIMIT", "max")
    assert services.memory_peak("mysql") == services.Peak("mysql", 2**20, None)
    assert services.memory_peak("kafka") == services.Peak("kafka", None, None)
    assert services.main(["peaks", "kafka", "--json"]) == 0
    assert capsys.readouterr().out == '{"service": "kafka", "peak_bytes": null, "limit_bytes": null}\n'


def test_other_projects_are_counted_but_never_named(fake_docker, capsys):
    fake_docker.setenv("FAKE_PS", "etf-risk-jobs\nsomeone-elses-project\n\netf-risk-jobs\n")
    assert services.other_containers() == 2                  # a labelled one and one without a project
    assert services.main(["others", "--require-none"]) == 1
    out = capsys.readouterr()
    assert out.out == "2 running container(s) outside the etf-risk-jobs project\n"
    assert "someone-elses-project" not in out.out + out.err


def test_none_outside_the_project(fake_docker):
    fake_docker.setenv("FAKE_PS", "etf-risk-jobs\netf-risk-jobs\n")
    assert services.other_containers() == 0
    assert services.main(["others", "--require-none"]) == 0


def test_ready_retries_until_the_check_passes():
    fake, calls = FakeTime(), []

    def check():
        calls.append(fake.now)
        if len(calls) < 3:
            raise ConnectionRefusedError("refused")

    assert services.wait_until_ready("mysql", check, timeout=60, clock=fake.clock, sleep=fake.sleep) == 2.0
    assert calls == [0.0, 1.0, 2.0]


def test_ready_gives_up_after_the_timeout_with_the_last_error():
    fake = FakeTime()

    def check():
        raise ConnectionRefusedError(f"refused at {fake.now:g} s")

    with pytest.raises(TimeoutError, match=r"kafka not ready after 5 s: ConnectionRefusedError: refused at 5 s"):
        services.wait_until_ready("kafka", check, timeout=5, clock=fake.clock, sleep=fake.sleep)


def test_the_job_services_stay_mysql_and_kafka_and_redis_is_apart():
    """tests/memory_check.py starts, measures and removes exactly SERVICES; the cache's Redis is
    not part of that check."""
    assert services.SERVICES == ("mysql", "kafka") and services.CACHE_SERVICES == ("redis",)


# The whole-session container monitor, shared by the result-cache experiment and the recovery harness

def _events(*pairs):
    return "\n".join(json.dumps({"Action": a, "Actor": {"Attributes": {"com.docker.compose.project": p}}})
                     for a, p in pairs)


def test_the_monitor_records_each_event_with_whether_it_is_ours_and_stops_cleanly():
    script = f"import sys, time; print({_events(('start', services.PROJECT), ('start', 'other'))!r}, flush=True); time.sleep(60)"
    monitor = services.ContainerEvents(command=[sys.executable, "-c", script])
    monitor.start()
    deadline = time.monotonic() + 10
    while len(monitor.events) < 2 and time.monotonic() < deadline:
        time.sleep(0.05)
    monitor.stop()
    assert [(e["action"], e["ours"]) for e in monitor.events] == [("start", True), ("start", False)]
    assert monitor.error is None and all("mono" in e for e in monitor.events)


def test_a_stream_that_ends_before_stop_is_an_error_so_the_session_counts_as_unmonitored():
    monitor = services.ContainerEvents(command=[sys.executable, "-c", "pass"])
    monitor.start()
    monitor.join(timeout=10)                          # the stream has ended; the session has not
    monitor.stop()
    assert monitor.error.startswith("the event stream ended before the session did")


def test_a_command_that_cannot_start_and_a_monitor_never_started_are_errors():
    failing = services.ContainerEvents(command=["/nonexistent/docker-for-this-test", "events"])
    failing.start()
    failing.stop()
    assert failing.error.startswith(("FileNotFoundError", "PermissionError", "OSError"))
    never = services.ContainerEvents()
    never.stop()
    assert never.error == "the event stream never started"


def test_the_result_cache_experiment_and_the_harness_share_the_monitor():
    from etf_risk import cache_experiment
    assert cache_experiment.ContainerEvents is services.ContainerEvents
    assert cache_experiment.parse_container_event is services.parse_container_event


PRIVATE = "s3cret-token-0f9a"     # a private-looking value in a command another project's container runs


def test_an_events_command_suffix_is_never_recorded_only_its_verb():
    line = json.dumps({"Action": f"exec_create: curl -H 'Authorization: Bearer {PRIVATE}' http://db:5432",
                       "status": f"exec_create: curl -H 'Authorization: Bearer {PRIVATE}' http://db:5432",
                       "Actor": {"ID": "abc123", "Attributes": {"name": "someone-else-1", "execID": "e1",
                                                               "com.docker.compose.project": "elsewhere"}},
                       "time": 7})
    event = services.parse_container_event(line, services.PROJECT)
    assert event == {"action": "exec_create", "ours": False, "time": 7}
    assert PRIVATE not in json.dumps(event) and "curl" not in json.dumps(event)


def test_the_monitor_keeps_no_command_suffix_in_what_it_records():
    line = json.dumps({"Action": f"exec_start: sh -c 'echo {PRIVATE}'",
                       "Actor": {"Attributes": {"com.docker.compose.project": "elsewhere"}}})
    script = f"import time; print({line!r}, flush=True); time.sleep(60)"
    monitor = services.ContainerEvents(command=[sys.executable, "-c", script])
    monitor.start()
    deadline = time.monotonic() + 10
    while not monitor.events and time.monotonic() < deadline:
        time.sleep(0.05)
    monitor.stop()
    assert [e["action"] for e in monitor.events] == ["exec_start"]
    assert PRIVATE not in json.dumps(monitor.events)
