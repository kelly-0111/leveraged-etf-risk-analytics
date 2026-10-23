"""etf_risk.services: memory peaks, the count of other projects' containers, and the
readiness wait, with a fake docker on PATH and a fake clock, so neither Docker nor a
service is needed.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os

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
