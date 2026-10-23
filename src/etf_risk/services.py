"""The systems extension's Compose services as seen from this machine: readiness, memory
peaks, and other projects' containers sharing Docker's VM (spec §11).

    uv run --group jobs python -m etf_risk.services ready mysql kafka
    uv run python -m etf_risk.services peaks mysql kafka
    uv run python -m etf_risk.services others --require-none

- ready waits until each service can do what the job system needs. MySQL: a login and
  SELECT 1, since the Compose healthcheck (mysqladmin ping) answers before logins work.
  Kafka: a metadata request that lists a broker. It exits 1 if a service is not ready
  within --timeout. The URLs come from ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP,
  defaulting to the ports in docker/compose.yaml.
- peaks prints each service's cgroup v2 memory.peak, the highest usage since its container
  started (page cache included), against memory.max, the Compose limit, as docker/run.sh
  does for the pipeline container. A container that restarts may start a new count, so
  read peaks before a restart is injected.
- others counts the running containers that do not belong to this Compose project. It
  prints the count only, never their names: they use the same VM's memory, so memory
  budgets are measured with none running.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_services.py.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass

from etf_risk.provenance import REPO_ROOT

COMPOSE_FILE = REPO_ROOT / "docker" / "compose.yaml"
PROJECT = "etf-risk-jobs"                                   # the name: in docker/compose.yaml
SERVICES = ("mysql", "kafka")
DEFAULT_MYSQL_URL = "mysql://root:jobs-test@127.0.0.1:3307"   # compose.yaml's test password, 127.0.0.1 only
DEFAULT_KAFKA_BOOTSTRAP = "127.0.0.1:9094"


def _docker(*args: str, timeout: float = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)


@dataclass(frozen=True)
class Peak:
    service: str
    peak_bytes: int | None     # None: no memory.peak to read (the service is not running, or an older kernel)
    limit_bytes: int | None    # None: no limit ("max"), or unknown

    @property
    def fraction(self) -> float | None:
        return None if self.peak_bytes is None or not self.limit_bytes else self.peak_bytes / self.limit_bytes

    def describe(self) -> str:
        if self.peak_bytes is None:
            return f"{self.service}: memory.peak not available"
        text = f"{self.service}: memory.peak {self.peak_bytes / 2**20:,.0f} MiB"
        if self.limit_bytes:
            text += f" of {self.limit_bytes / 2**20:,.0f} MiB ({self.fraction:.0%})"
        return text + " (cgroup, includes page cache)"


def memory_peak(service: str) -> Peak:
    """The service container's memory.peak and memory.max (cgroup v2)."""
    out = _docker("compose", "-f", str(COMPOSE_FILE), "exec", "-T", service,
                  "cat", "/sys/fs/cgroup/memory.peak", "/sys/fs/cgroup/memory.max")
    values = out.stdout.split()
    if out.returncode != 0 or len(values) != 2:
        return Peak(service, None, None)
    peak, limit = values
    return Peak(service, int(peak), None if limit == "max" else int(limit))


def other_containers() -> int:
    """How many running containers belong to no service of this project: a count only."""
    out = _docker("ps", "--format", '{{.Label "com.docker.compose.project"}}')
    if out.returncode != 0:
        raise RuntimeError(f"docker ps failed with exit code {out.returncode}")
    return sum(1 for label in out.stdout.splitlines() if label.strip() != PROJECT)


def mysql_ready(url: str) -> None:
    from etf_risk.jobs.mysql import connect_mysql
    connection = connect_mysql(url)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            if cursor.fetchone() != (1,):
                raise RuntimeError("SELECT 1 did not return 1")
    finally:
        connection.close()


def kafka_ready(bootstrap: str) -> None:
    from confluent_kafka.admin import AdminClient
    metadata = AdminClient({"bootstrap.servers": bootstrap, "log_level": 0}).list_topics(timeout=5)
    if not metadata.brokers:
        raise RuntimeError("the metadata lists no broker")


def wait_until_ready(service: str, check: Callable[[], None], *, timeout: float, interval: float = 1.0,
                     clock: Callable[[], float] = time.monotonic,
                     sleep: Callable[[float], None] = time.sleep) -> float:
    """Run check() until it returns; the seconds that took. TimeoutError, with the last
    error, once timeout has passed."""
    start = clock()
    while True:
        try:
            check()
            return clock() - start
        except Exception as error:
            last = error
        if clock() - start >= timeout:
            raise TimeoutError(f"{service} not ready after {timeout:g} s: {type(last).__name__}: {last}")
        sleep(interval)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.services", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    ready = commands.add_parser("ready", help="wait until each service can be used")
    ready.add_argument("services", nargs="+", choices=SERVICES)
    ready.add_argument("--timeout", type=float, default=120.0, help="seconds per service (default 120)")
    peaks = commands.add_parser("peaks", help="cgroup memory.peak against the limit")
    peaks.add_argument("services", nargs="+", choices=SERVICES)
    peaks.add_argument("--json", action="store_true", help="one JSON object per line")
    others = commands.add_parser("others", help="count containers outside this project")
    others.add_argument("--require-none", action="store_true", help="exit 1 if any is running")
    args = parser.parse_args(argv)

    if args.command == "ready":
        checks = {"mysql": lambda: mysql_ready(os.environ.get("ETF_RISK_MYSQL_URL", DEFAULT_MYSQL_URL)),
                  "kafka": lambda: kafka_ready(os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", DEFAULT_KAFKA_BOOTSTRAP))}
        for service in args.services:
            try:
                seconds = wait_until_ready(service, checks[service], timeout=args.timeout)
            except TimeoutError as error:
                print(error, file=sys.stderr)
                return 1
            print(f"{service}: ready after {seconds:.1f} s")
        return 0
    if args.command == "peaks":
        for service in args.services:
            peak = memory_peak(service)
            print(json.dumps(asdict(peak)) if args.json else peak.describe())
        return 0
    count = other_containers()
    print(f"{count} running container(s) outside the {PROJECT} project")
    return 1 if args.require_none and count else 0


if __name__ == "__main__":
    sys.exit(main())
