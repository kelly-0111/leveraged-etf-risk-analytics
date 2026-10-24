"""tests/memory_check.py without Docker, services, Spark or timing. Readings of cgroups,
Docker's records, vm_stat, command lines, run records and JUnit files; container lifetimes
across restarts, each counted from zero; the sampler, one tick at a time on stand-in processes
and readings; the check's run with every effect stood in for (a fake clock included), through
success, refusal, interruption, errors and failed cleanup; and, with short-lived real processes
and handshakes in place of sleeps, the time limit and the leftovers that belong to a run. Each
planted problem must reach the outcome that covers it, failed measurements, invalid runs and
tool errors apart, and no proposed threshold may change an outcome.

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
import os
import signal
import socket
import subprocess
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import psutil
import pytest

_spec = importlib.util.spec_from_file_location("memory_check", Path(__file__).with_name("memory_check.py"))
mc = importlib.util.module_from_spec(_spec)
sys.modules["memory_check"] = mc      # dataclasses look a class's module up there
_spec.loader.exec_module(mc)

MiB, GiB = mc.MiB, mc.GiB
NO_EVENTS = dict.fromkeys(mc.EVENTS, 0)
PY = "/repo/.venv/bin/python"
STACK_STARTED = "2026-10-24T10:00:00+00:00"


def reading(peak, anon=100 * MiB, *, cgroup=1, limit=512 * MiB, file=50 * MiB, kernel=10 * MiB, at=None, **events):
    return {"at_utc": at, "cgroup": cgroup, "peak": peak, "limit": limit, "current": peak, "anon": anon,
            "file": file, "kernel": kernel, "kernel_from": "kernel", "events": {**NO_EVENTS, **events}}


def running(**change) -> dict:
    """Docker's record of a container this run created, and still running."""
    return {"id": "c0ffee000000", "created": "2026-10-24T10:00:01.123456789Z", "restart_count": 0,
            "status": "running", "started": "2026-10-24T10:00:02Z", "exit_code": 0, "oom_killed": False, **change}


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def runner(*results, seen=None):
    """A stand-in for subprocess.run that returns, or raises, each result in turn."""
    queue = list(results)

    def run(command, **kwargs):
        if seen is not None:
            seen.append((command, kwargs))
        result = queue.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result
    return run


def done(stdout="", code=0):
    return subprocess.CompletedProcess([], code, stdout, "")


# Reading a cgroup

CGROUP_OUTPUT = ("cgroup 4242\npeak 419430400\nlimit 536870912\ncurrent 400000000\nstat_anon 314572800\n"
                 "stat_file 73400320\nstat_kernel 20971520\nstat_kernel_stack 1048576\nstat_slab 8388608\n"
                 "stat_sock 0\nevents_low 0\nevents_high 0\nevents_max 7\nevents_oom 0\nevents_oom_kill 0\n"
                 "events_oom_group_kill 0\n")


def test_a_cgroup_reading_keeps_its_identity_the_total_its_kinds_of_memory_and_the_events():
    assert mc.parse_cgroup(CGROUP_OUTPUT) == {
        "cgroup": 4242, "peak": 419430400, "limit": 536870912, "current": 400000000, "anon": 314572800,
        "file": 73400320, "kernel": 20971520, "kernel_from": "kernel", "events": {**NO_EVENTS, "max": 7}}


def test_kernel_memory_is_the_sum_of_its_parts_without_a_kernel_line():
    text = CGROUP_OUTPUT.replace("stat_kernel 20971520\n", "") + "stat_pagetables 2097152\nstat_percpu 1048576\n"
    r = mc.parse_cgroup(text)
    assert (r["kernel"], r["kernel_from"]) == (1048576 + 8388608 + 2097152 + 1048576, "parts")


def test_no_limit_and_missing_counters_or_identity_read_as_such():
    r = mc.parse_cgroup("peak 1\nlimit max\nstat_anon 1\n")
    assert (r["cgroup"], r["limit"], r["file"], r["current"], r["events"]) == (None, None, None, None, NO_EVENTS)


@pytest.mark.parametrize("text", ["", "Error response from daemon: container is paused\n", "peak 1\nlimit max\n",
                                  "stat_anon 5\n", "peak x\nstat_anon 5\n"])
def test_output_without_a_total_or_an_anon_figure_is_no_reading(text):
    assert mc.parse_cgroup(text) is None


@pytest.mark.parametrize("result", [subprocess.TimeoutExpired("docker", 10), FileNotFoundError("docker"),
                                    done('service "mysql" is not running', code=1), done("garbage")])
def test_a_cgroup_that_cannot_be_read_gives_no_reading(result):
    assert mc.read_cgroup("mysql", run=runner(result)) is None


def test_a_cgroup_and_its_identity_are_read_through_docker_compose_exec_within_ten_seconds():
    seen = []
    result = mc.read_cgroup("kafka", run=runner(done(CGROUP_OUTPUT), seen=seen))
    command, kwargs = seen[0]
    assert (result["cgroup"], result["peak"]) == (4242, 419430400)
    assert command[4:9] == ["exec", "-T", "kafka", "sh", "-c"] and "ls -di ." in command[9]
    assert kwargs["timeout"] == 10


# Lifetimes

def test_lifetimes_split_where_the_cgroup_changes_and_not_at_gaps():
    # the second lifetime starts above the first one's last peak, and no counter goes down
    readings = [reading(100, cgroup=1), None, reading(150, cgroup=1), reading(400, cgroup=2), reading(420, cgroup=2),
                None, reading(90, cgroup=3)]
    assert [[r["peak"] for r in life] for life in mc.lifetimes(readings)] == [[100, 150], [400, 420], [90]]


def test_every_lifetime_counts_its_events_from_zero_with_startup_and_idle_included():
    readings = [reading(300 * MiB, 200 * MiB, cgroup=1, max=4, oom=1),   # an oom before the first reading
                reading(500 * MiB, 310 * MiB, cgroup=1, file=150 * MiB, max=9, oom=1),
                reading(200 * MiB, 150 * MiB, cgroup=2, at="restarted"),
                reading(450 * MiB, 330 * MiB, cgroup=2, kernel=30 * MiB, max=2, oom_kill=1)]
    summary = mc.summarize_container(readings, 512 * MiB, True)
    first, second = summary["lifetimes"]
    assert (summary["verified"], summary["problems"]) == (True, [])
    assert (first["cgroup"], first["readings"], first["peak_bytes"], first["anon_bytes"], first["file_bytes"]) == (
        1, 2, 500 * MiB, 310 * MiB, 150 * MiB)
    assert first["events"] == {**NO_EVENTS, "max": 9, "oom": 1}
    assert first["events_at_first_reading"] == {**NO_EVENTS, "max": 4, "oom": 1}
    assert (second["cgroup"], second["from_utc"], second["peak_bytes"], second["kernel_bytes"]) == (
        2, "restarted", 450 * MiB, 30 * MiB)
    assert second["events"] == {**NO_EVENTS, "max": 2, "oom_kill": 1}
    assert (summary["peak_bytes"], summary["anon_bytes"], summary["budget_bytes"]) == (500 * MiB, 330 * MiB, 512 * MiB)
    assert summary["events"] == {**NO_EVENTS, "max": 11, "oom": 1, "oom_kill": 1}


@pytest.mark.parametrize("readings, fresh, problem", [
    ([reading(300, max=5), reading(310, max=4)], True, "a counter went down within lifetime 1"),
    ([reading(300), reading(250)], True, "a counter went down within lifetime 1"),
    ([reading(300, cgroup=None)], True, "a reading does not name its cgroup"),
    ([reading(300)], False, "its container is not verified as created by this run"),
])
def test_a_lifetime_that_cannot_be_counted_from_zero_is_not_verified(readings, fresh, problem):
    summary = mc.summarize_container(readings, 512 * MiB, fresh)
    assert summary["verified"] is False and problem in summary["problems"]


def test_a_container_never_read_has_no_lifetimes_and_no_figures():
    summary = mc.summarize_container([None, None], 640 * MiB, True)
    assert (summary["lifetimes"], summary["peak_bytes"], summary["anon_bytes"], summary["events"]) == (
        [], None, None, NO_EVENTS)


# Docker's records

def test_docker_time_keeps_the_microseconds_of_a_nanosecond_stamp():
    assert mc.docker_time("2026-10-24T09:10:42.388096553Z") == datetime(2026, 10, 24, 9, 10, 42, 388096,
                                                                        tzinfo=timezone.utc)
    assert mc.docker_time("2026-10-24T09:10:42Z").microsecond == 0
    assert mc.docker_time("garbage") is None and mc.docker_time(None) is None


def test_dockers_record_of_a_container_is_read():
    seen = []
    state = ('2026-10-24T10:00:30.1Z 0 {"Status":"exited","StartedAt":"2026-10-24T10:00:31Z",'
             '"ExitCode":137,"OOMKilled":true}')
    assert mc.docker_state("kafka", run=runner(done("abcdef0123456789\n"), done(state), seen=seen)) == {
        "id": "abcdef012345", "created": "2026-10-24T10:00:30.1Z", "restart_count": 0, "status": "exited",
        "started": "2026-10-24T10:00:31Z", "exit_code": 137, "oom_killed": True}
    assert seen[0][0][-3:] == ["ps", "-aq", "kafka"] and seen[1][0][:2] == ["docker", "inspect"]


@pytest.mark.parametrize("results", [
    (done(""),), (done("one\ntwo\n"),), (done("", code=1),), (subprocess.TimeoutExpired("docker", 30),),
    (done("abc\n"), done("", code=1)), (done("abc\n"), done("not json")), (done("abc\n"), FileNotFoundError("docker")),
])
def test_dockers_record_is_none_without_exactly_one_container_or_when_docker_fails(results):
    assert mc.docker_state("mysql", run=runner(*results)) is None


@pytest.mark.parametrize("created, expected", [
    ("2026-10-24T10:00:03.5Z", True), ("2026-10-24T09:59:57Z", True),           # within the clocks' tolerance
    ("2026-10-24T09:59:50Z", False), ("2026-10-23T08:10:42.388096553Z", False), ("not a time", False),
])
def test_a_container_counts_as_created_by_this_run_only_after_the_stack_was_started(created, expected):
    assert mc.created_by_this_run({"created": created}, STACK_STARTED) is expected
    assert mc.created_by_this_run(None, STACK_STARTED) is False


# The sampler

class Proc:
    """A stand-in process; how often its command line is read is counted."""

    def __init__(self, pid, cmdline, rss, created=1.0, name="python3.12"):
        self.pid, self.command, self.memory, self.created, self.name, self.reads = pid, cmdline, rss, created, name, 0

    def seen(self) -> mc.Seen:
        def cmdline():
            self.reads += 1
            if isinstance(self.command, Exception):
                raise self.command
            return self.command

        def rss():
            if isinstance(self.memory, Exception):
                raise self.memory
            return self.memory
        return mc.Seen((self.pid, self.created), self.pid, self.name, cmdline, rss)


def jobs(*args):
    return [PY, "-m", "etf_risk.jobs", *args]


def sampler(tmp_path, procs=(), available=(5 * GiB,), readings=None, host=None) -> mc.Sampler:
    free = iter(available)
    return mc.Sampler(tmp_path / "samples.jsonl", processes=lambda: [p.seen() for p in procs],
                      available=lambda: next(free), read_cgroup=lambda service: (readings or {}).get(service),
                      host_memory=host or (lambda: {"available_bytes": 5 * GiB, "compressor_bytes": GiB,
                                                    "swap_bytes": 0}),
                      clock=lambda: "2026-10-24T00:00:00+00:00")


def test_job_processes_are_known_by_their_command_lines():
    assert mc.role(jobs("worker", "--worker-id", "A")) == "worker"
    assert mc.role(jobs("reconciler", "--interval", "2")) == "reconciler"
    assert mc.role(jobs("submit", "--snapshot", "s")) == "submit"
    assert mc.role([PY, "-m", "pytest", "tests/test_jobs_live_pipeline.py"]) == "pytest"
    for other in (jobs("status"), [PY, "-m", "etf_risk.jobs.launcher", "--marker", "m"],
                  [PY, "-m", "etf_risk.spark_pipeline"], [PY, "script.py"], [], None):
        assert mc.role(other) is None, other


def test_the_sampler_keeps_the_largest_rss_per_role_and_the_lowest_available_memory(tmp_path):
    worker = Proc(10, jobs("worker", "--worker-id", "A"), 60 * MiB)
    procs = [worker, Proc(11, jobs("reconciler"), 50 * MiB), Proc(12, None, 2 * GiB, name=mc.VM_PROCESS),
             Proc(13, [PY, "-m", "etf_risk.spark_pipeline"], 3 * GiB)]
    s = sampler(tmp_path, procs, available=(5 * GiB, 3 * GiB, 4 * GiB))
    s.sample_processes()
    worker.memory = 70 * MiB
    s.sample_processes()
    worker.memory = 65 * MiB
    procs.append(Proc(14, jobs("worker", "--worker-id", "B"), 66 * MiB))
    s.sample_processes()
    assert s.rss == {"worker": 70 * MiB, "reconciler": 50 * MiB, "submit": 0, "pytest": 0, "vm": 2 * GiB}
    assert (s.pids["worker"], s.available_min, s.errors) == ({10, 14}, 3 * GiB, 0)


def test_a_command_line_is_read_once_and_a_reused_pid_is_a_new_process(tmp_path):
    procs = [Proc(20, jobs("submit"), 40 * MiB, created=1.0)]
    s = sampler(tmp_path, procs, available=(GiB,) * 3)
    s.sample_processes()
    s.sample_processes()
    assert procs[0].reads == 1
    procs[0] = Proc(20, [PY, "-m", "pytest"], 200 * MiB, created=2.0)
    s.sample_processes()
    assert (s.rss["submit"], s.rss["pytest"], procs[0].reads) == (40 * MiB, 200 * MiB, 1)


def test_processes_that_deny_access_or_vanish_are_passed_over(tmp_path):
    s = sampler(tmp_path, [Proc(30, psutil.AccessDenied(30), 10 * MiB),
                           Proc(31, jobs("worker"), psutil.NoSuchProcess(31))])
    s.sample_processes()
    assert (s.rss["worker"], s.pids["worker"], s.errors) == (0, set(), 0)


def test_each_container_tick_writes_a_line_and_keeps_every_reading(tmp_path):
    s = sampler(tmp_path, readings={"mysql": reading(300 * MiB)})
    s.sample_containers()
    s.sample_containers()
    lines = [json.loads(line) for line in (tmp_path / "samples.jsonl").read_text().splitlines()]
    assert len(lines) == 2 and lines[0]["kafka"] is None and lines[0]["compressor_bytes"] == GiB
    assert (lines[0]["mysql"]["peak"], lines[0]["mysql"]["at_utc"]) == (300 * MiB, "2026-10-24T00:00:00+00:00")
    assert len(s.readings["mysql"]) == 2 and s.readings["kafka"] == [None, None] and len(s.host) == 2


def test_a_failed_host_reading_is_counted_and_the_containers_are_read_all_the_same(tmp_path):
    def broken():
        raise ValueError("vm_stat: no page size or compressor line")
    s = sampler(tmp_path, readings={"mysql": reading(1), "kafka": reading(2)}, host=broken)
    s.sample_containers()
    assert s.errors == 1 and "compressor_bytes" not in s.host[0]
    assert [s.readings[service][0]["peak"] for service in ("mysql", "kafka")] == [1, 2]


def test_a_failing_sample_is_counted_and_sampling_goes_on(tmp_path):
    s, calls = sampler(tmp_path), []

    def flaky():
        calls.append(len(calls))
        if len(calls) == 1:
            raise RuntimeError("docker did not answer")
    s.tick(flaky)
    s.tick(flaky)
    assert (s.errors, len(calls)) == (1, 2)


def test_the_sampler_threads_sample_until_they_are_stopped(tmp_path):
    ticked = {"processes": threading.Event(), "containers": threading.Event()}
    s = mc.Sampler(tmp_path / "samples.jsonl", processes=lambda: ticked["processes"].set() or [],
                   available=lambda: GiB, read_cgroup=lambda service: ticked["containers"].set(),
                   host_memory=dict, clock=lambda: "t", intervals=(0.01, 0.01))
    s.start()
    assert ticked["processes"].wait(10) and ticked["containers"].wait(10)
    s.stop()
    assert len(s._threads) == 2 and not any(thread.is_alive() for thread in s._threads)


def test_the_live_scan_sees_this_process():
    me = next(seen for seen in mc.live_processes() if seen.pid == os.getpid())
    assert me.rss() > 0 and isinstance(me.cmdline(), list) and me.key[0] == os.getpid()


def test_the_compressor_size_comes_from_vm_stat_and_anything_else_is_an_error():
    vm_stat = ("Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free:      12345.\n"
               "Pages occupied by compressor:            221184.\n")
    assert mc.compressor_bytes(vm_stat) == 221184 * 16384
    with pytest.raises(ValueError):
        mc.compressor_bytes("vm_stat: command not found")


# Records of the runs

def test_step_peaks_cover_every_launch_and_the_attempt_records_name_the_jobs(tmp_path):
    store = tmp_path / "acceptance" / "live0" / "out" / "store"
    write(store / "job-1-attempt-1" / "logs" / "spark_pipeline.launcher.json", {"peak_rss_bytes": 3 * GiB})
    write(store / "job-1-attempt-2" / "logs" / "spark_pipeline.launcher.json", {"peak_rss_bytes": 2 * GiB})
    write(store / "job-1-attempt-2" / "logs" / "windows.launcher.json", {"peak_rss_bytes": 100 * MiB})
    write(store / "job-1-attempt-2" / "attempt.json", {"params": {"kind": "calendar-year", "stride": 21}, "steps": [
        {"name": "windows", "peak_rss_bytes": 100 * MiB}, {"name": "spark_pipeline", "peak_rss_bytes": 2 * GiB}]})
    write(store / "job-2-attempt-1" / "attempt.json", {"params": {"kind": "rolling", "stride": 21}, "steps": [
        {"name": "spark_pipeline", "peak_rss_bytes": int(2.5 * GiB)}]})
    # the killed first attempt left no attempt.json, but its launch is measured all the same
    assert mc.launcher_peaks(tmp_path / "acceptance") == {"spark_pipeline": 3 * GiB, "windows": 100 * MiB}
    assert mc.job_peaks(tmp_path / "acceptance") == {
        "calendar-year": {"windows": 100 * MiB, "spark_pipeline": 2 * GiB},
        "rolling, stride 21": {"spark_pipeline": int(2.5 * GiB)}}
    mc.keep_records(tmp_path / "acceptance", tmp_path / "kept")
    assert sorted(p.relative_to(tmp_path / "kept").as_posix() for p in (tmp_path / "kept").rglob("*.json")) == [
        "live0/out/store/job-1-attempt-1/logs/spark_pipeline.launcher.json",
        "live0/out/store/job-1-attempt-2/attempt.json",
        "live0/out/store/job-1-attempt-2/logs/spark_pipeline.launcher.json",
        "live0/out/store/job-1-attempt-2/logs/windows.launcher.json",
        "live0/out/store/job-2-attempt-1/attempt.json"]


def test_the_junit_counts_are_read_and_a_missing_or_broken_file_has_none(tmp_path):
    path = tmp_path / "run.xml"
    path.write_text('<?xml version="1.0" encoding="utf-8"?><testsuites><testsuite name="pytest" errors="0" '
                    'failures="1" skipped="10" tests="473" time="172.1"></testsuite></testsuites>')
    assert mc.junit_counts(path) == {"readable": True, "tests": 473, "failures": 1, "errors": 0, "skipped": 10}
    (tmp_path / "broken.xml").write_text("<testsuites><testsuite")
    none = {"readable": False, "tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    assert mc.junit_counts(tmp_path / "missing.xml") == mc.junit_counts(tmp_path / "broken.xml") == none


def test_measure_takes_growth_from_the_idle_reading_and_freshness_from_dockers_record(tmp_path):
    write(tmp_path / "acceptance" / "live0" / "job-1-attempt-1" / "logs" / "verify.launcher.json",
          {"peak_rss_bytes": GiB})
    idle = {"available_bytes": 5 * GiB, "compressor_bytes": 100 * MiB, "swap_bytes": 0}
    fake = SimpleNamespace(
        host=[{"compressor_bytes": 150 * MiB, "swap_bytes": 0}, {"at_utc": "a failed host reading"},
              {"compressor_bytes": 120 * MiB, "swap_bytes": 8 * MiB}],
        available_min=3 * GiB, errors=1,
        readings={"mysql": [reading(300 * MiB, 250 * MiB)], "kafka": [reading(400 * MiB, limit=640 * MiB)]},
        rss={"worker": 64 * MiB, "reconciler": 52 * MiB, "submit": 0, "pytest": 200 * MiB, "vm": 2 * GiB},
        pids={"worker": {1, 2}, "reconciler": {3}, "submit": set(), "pytest": {4}, "vm": {5}})
    docker = {"started": {"mysql": running(), "kafka": running(created="2026-10-23T08:10:42.388096553Z")}}
    measured = mc.measure(fake, idle, tmp_path, {"suites": {}, "acceptance": {}}, {"suites": 0, "acceptance": 1},
                          docker, STACK_STARTED)
    assert (measured["host"]["compressor_growth_bytes"], measured["host"]["swap_growth_bytes"]) == (50 * MiB, 8 * MiB)
    assert measured["steps"] == {"verify": GiB} and measured["leftovers"] == {"suites": 0, "acceptance": 1}
    assert measured["containers"]["mysql"]["verified"] and measured["containers"]["mysql"]["anon_bytes"] == 250 * MiB
    assert measured["containers"]["kafka"]["problems"] == ["its container is not verified as created by this run"]
    assert measured["processes"]["worker"] == {"rss_bytes": 64 * MiB, "processes": 2}
    assert measured["processes"]["submit"] == {"rss_bytes": 0, "processes": 0} and measured["sampler_errors"] == 1
    assert measured["docker"] is docker


def test_a_listening_port_is_in_use():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        assert mc.port_in_use(port)
    assert not mc.port_in_use(port)


# Time limits and leftovers, with real short-lived processes

def ready_child(script: str) -> tuple[subprocess.Popen, str]:
    """A child in a session of its own that prints a line once it is ready: a handshake, not a sleep."""
    process = subprocess.Popen([sys.executable, "-c", script], stdout=subprocess.PIPE, text=True,
                               start_new_session=True)
    line = process.stdout.readline()
    assert line.startswith("ready"), line
    return process, line


def spawn(*args: str, env: dict | None = None) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)", *args],
                            env={**os.environ, **(env or {})}, start_new_session=True)


def test_a_command_that_ends_gives_its_exit_code_and_its_output(tmp_path):
    code = mc.run_bounded([sys.executable, "-c", "print('out'); raise SystemExit(3)"], cwd=tmp_path,
                          env=dict(os.environ), log=tmp_path / "log", timeout=60, grace=5)
    assert code == 3 and (tmp_path / "log").read_text() == "out\n"


def test_a_command_past_its_time_is_interrupted_and_gives_no_exit_code(tmp_path):
    assert mc.run_bounded(["sleep", "60"], cwd=tmp_path, env=dict(os.environ), log=tmp_path / "log",
                          timeout=0.2, grace=10) is None


def test_an_interrupted_command_runs_its_teardown():
    process, _ = ready_child("import time\ntry:\n    print('ready', flush=True)\n    time.sleep(60)\n"
                             "except KeyboardInterrupt:\n    print('teardown', flush=True)\n")
    mc.interrupt(process, grace=30)
    assert process.stdout.read() == "teardown\n" and process.returncode == 0
    process.stdout.close()


def test_a_command_that_ignores_the_interrupt_is_killed_with_its_group():
    process, line = ready_child(
        "import signal, subprocess, time\nsignal.signal(signal.SIGINT, signal.SIG_IGN)\n"
        "child = subprocess.Popen(['sleep', '60'])\nprint('ready', child.pid, flush=True)\ntime.sleep(60)\n")
    grandchild = psutil.Process(int(line.split()[1]))
    mc.interrupt(process, grace=0.2)
    process.stdout.close()
    assert process.returncode == -signal.SIGKILL
    try:
        grandchild.wait(timeout=10)       # killed with the group, then reaped by launchd
    except psutil.NoSuchProcess:
        pass
    assert not grandchild.is_running()


def test_an_interrupt_of_the_check_interrupts_its_command(tmp_path, monkeypatch):
    started = []

    class Interrupted(subprocess.Popen):
        def wait(self, timeout=None):
            if timeout == 3600:           # run_bounded waiting for the command
                started.append(self.pid)
                raise KeyboardInterrupt
            return super().wait(timeout)

    monkeypatch.setattr(mc.subprocess, "Popen", Interrupted)
    with pytest.raises(KeyboardInterrupt):
        mc.run_bounded(["sleep", "60"], cwd=tmp_path, env=dict(os.environ), log=tmp_path / "log", timeout=3600,
                       grace=10)
    assert started and not psutil.pid_exists(started[0])


def test_leftovers_are_the_processes_that_name_the_folder_carry_its_token_or_its_stores_marker(tmp_path):
    temp = tmp_path / "check"
    (temp / "suites" / "test_x0" / "deep" / "out" / "store1" / "job-1-attempt-1").mkdir(parents=True)
    children = {"names the folder": spawn("--output-root", str(temp / "acceptance" / "live0" / "out")),
                "carries the token": spawn(env={mc.RUN_ENV: str(temp)}),
                "a store found at any depth": spawn(env={"ETF_RISK_ATTEMPT": "store1:run-1:0123456789abcdef"}),
                "another check's token": spawn(env={mc.RUN_ENV: str(tmp_path / "other")}),
                "another store": spawn(env={"ETF_RISK_ATTEMPT": "store2:run-1:0123456789abcdef"}),
                "another folder": spawn("--output-root", str(tmp_path / "elsewhere"))}
    try:
        assert {p.pid for p in mc.leftovers(temp)} == {
            children[name].pid for name in ("names the folder", "carries the token", "a store found at any depth")}
    finally:
        for child in children.values():
            child.kill()
            child.wait()


def test_ending_continues_a_stopped_process_and_kills_one_that_ignores_sigterm():
    stopped = spawn()
    stubborn, _ = ready_child("import signal, time\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                              "print('ready', flush=True)\ntime.sleep(120)\n")
    os.kill(stopped.pid, signal.SIGSTOP)
    try:
        record = mc.end([psutil.Process(stopped.pid), psutil.Process(stubborn.pid)], grace=2.0)
        assert sorted(record["terminated"]) == sorted([stopped.pid, stubborn.pid])
        assert record["killed"] == [stubborn.pid] and record["remaining"] == []
    finally:
        stubborn.stdout.close()
        for child in (stopped, stubborn):
            if child.poll() is None:
                child.kill()
            child.wait()


# The check's run, with a stand-in machine

class FakeSampler:
    def __init__(self, samples):
        self.started = self.stopped = False
        self.final_readings = 0
        self.host = [{"compressor_bytes": GiB + 10 * MiB, "swap_bytes": 0}]
        self.available_min, self.errors = 3 * GiB, 0
        self.rss = {"worker": 64 * MiB, "reconciler": 52 * MiB, "submit": 60 * MiB, "pytest": 200 * MiB, "vm": GiB}
        self.pids = {"worker": {1}, "reconciler": {2}, "submit": {3}, "pytest": {4}, "vm": {5}}
        self.readings = {"mysql": [reading(400 * MiB, 300 * MiB, cgroup=11)],
                         "kafka": [reading(450 * MiB, 350 * MiB, cgroup=12, limit=640 * MiB)]}

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def tick(self, sample):
        sample()

    def sample_containers(self):
        self.final_readings += 1
        for readings in self.readings.values():
            readings.append(dict(readings[-1]))


class FakeSystem:
    """The machine, stood in for, with a clock of its own: every call is logged, and each failure,
    leftover and Docker record is planted where asked."""

    def __init__(self, available=5 * GiB, fail=(), left=None, docker=None, containers=0, dirty=False, others=0,
                 busy=(), snapshot=True):
        self.log, self.fail, self.available_bytes = [], dict(fail), available
        self.left, self.leftover_calls = left or (lambda call: 0), 0
        self.docker, self.docker_calls = docker or (lambda service, n: running()), {}
        self.containers, self.dirty, self.others, self.busy = containers, dirty, others, set(busy)
        self.snapshot, self.samplers, self.pytest_env, self.clock = snapshot, [], {}, 0.0

    def _call(self, name, *details):
        self.log.append((name, *details))
        if name in self.fail:
            raise self.fail[name]

    def compose(self, *args, timeout=300):
        self._call(f"compose {args[0]}")

    def ready(self, env):
        self._call("ready")

    def sleep(self, seconds):
        self.clock += seconds
        self._call("sleep", seconds)

    def monotonic(self):
        return self.clock

    def now(self):
        return STACK_STARTED

    def host_memory(self):
        self._call("host_memory")
        return {"available_bytes": self.available_bytes, "compressor_bytes": GiB, "swap_bytes": 0}

    def available(self):
        return self.available_bytes

    def docker_state(self, service):
        self._call("docker_state", service)
        n = self.docker_calls[service] = self.docker_calls.get(service, -1) + 1   # 0 started, 1 after suites, ...
        return self.docker(service, n)

    def sampler(self, samples):
        self._call("sampler")
        self.samplers.append(FakeSampler(samples))
        return self.samplers[-1]

    def run_pytest(self, name, files, env, out, temp, timeout):
        self._call(f"pytest {name}", env.get("ETF_RISK_LIVE_PIPELINE"), timeout)
        self.pytest_env[name] = env
        if name == "acceptance":
            attempt = temp / "acceptance" / "live0" / "out" / "store" / "job-1-attempt-1"
            for step, peak in (("windows", 130 * MiB), ("spark_pipeline", int(2.7 * GiB)), ("verify", 2 * GiB)):
                write(attempt / "logs" / f"{step}.launcher.json", {"peak_rss_bytes": peak})
            write(attempt / "attempt.json", {"params": {"kind": "rolling", "stride": 21},
                                             "steps": [{"name": "spark_pipeline", "peak_rss_bytes": int(2.7 * GiB)}]})
        tests, skipped = (10, 0) if name == "acceptance" else (473, 10)
        return {"exit_code": 0, "seconds": 1.0, "readable": True, "tests": tests, "failures": 0, "errors": 0,
                "skipped": skipped}

    def leftovers(self, temp):
        self._call("leftovers")
        found = [object()] * self.left(self.leftover_calls)
        self.leftover_calls += 1
        return found

    def end(self, procs, rescan=None):
        self._call("end", len(procs))
        return {"terminated": list(range(len(procs))), "killed": [], "remaining": []}

    def project_containers(self):
        self._call("project_containers")
        return self.containers

    def other_containers(self):
        return self.others

    def git_dirty(self):
        return self.dirty

    def port_in_use(self, port):
        return port in self.busy

    def snapshot_exists(self):
        return self.snapshot

    def keep_awake(self):
        self._call("keep_awake")

    def tools(self):
        return {"stand-in": True}

    def code_state(self):
        return {"commit": "0" * 40, "dirty": False}


def check(tmp_path, system, keep=False):
    out, temp = tmp_path / "out", tmp_path / "temp"
    out.mkdir()
    temp.mkdir()
    return mc.run_check(out, temp, keep, system), out, temp


def record_in(out: Path) -> dict:
    return json.loads((out / "record.json").read_text())


def names(system) -> list[str]:
    return [entry[0] for entry in system.log]


CLEANUP = ["leftovers", "docker_state", "docker_state", "compose unpause", "compose down", "project_containers"]


def test_a_clean_run_passes_and_cleans_up_in_order(tmp_path):
    system = FakeSystem()
    code, out, temp = check(tmp_path, system)
    assert code == 0
    assert names(system) == [
        "keep_awake", "compose up", "ready", "docker_state", "docker_state", "sleep", "host_memory", "sampler",
        "pytest suites", "docker_state", "docker_state", "leftovers",
        "pytest acceptance", "docker_state", "docker_state", "leftovers", *CLEANUP]
    assert ("pytest suites", None, 1800) in system.log and ("pytest acceptance", "1", 3600) in system.log
    record = record_in(out)
    assert (record["outcome"], record["exit_code"], record["verdict"]["validates"]) == (
        "passed", 0, "container limits only")
    assert record["supplementary"]["native_approved"] is False and record["verdict"]["native_targets"]["approved"] is False
    assert sorted(record["docker"]) == ["after acceptance", "after suites", "before cleanup", "started"]
    assert all(c["verified"] and len(c["lifetimes"]) == 1 for c in record["measured"]["containers"].values())
    assert system.samplers[0].final_readings == 1 and system.samplers[0].stopped
    assert record["measured"]["containers"]["mysql"]["lifetimes"][0]["readings"] == 2   # the final reading
    assert system.pytest_env["suites"][mc.RUN_ENV] == system.pytest_env["acceptance"][mc.RUN_ENV] == str(temp)
    assert record["leftovers"] == {name: {"seen": 0, "remaining": 0} for name in ("suites", "acceptance", "cleanup")}
    assert not temp.exists()
    assert (out / "records" / "acceptance" / "live0" / "out" / "store" / "job-1-attempt-1" / "attempt.json").exists()


def test_too_little_memory_with_the_stack_idle_is_not_counted_and_the_stack_is_removed(tmp_path):
    system = FakeSystem(available=3 * GiB)
    code, out, _ = check(tmp_path, system)
    record = record_in(out)
    assert (code, record["outcome"], record["exit_code"]) == (2, "not counted", 2)
    assert "sampler" not in names(system) and not any(name.startswith("pytest") for name in names(system))
    assert names(system)[-len(CLEANUP):] == CLEANUP
    assert record["verdict"]["invalid"] == ["3.00 GiB available with the stack idle, below 4.0 GiB"]


def test_a_container_this_run_did_not_create_is_not_counted(tmp_path):
    system = FakeSystem(docker=lambda service, n: running(created="2026-10-23T08:10:42.388096553Z"))
    code, out, _ = check(tmp_path, system)
    record = record_in(out)
    assert (code, record["outcome"]) == (2, "not counted")
    assert "mysql: its container is not verified as created by this run" in record["verdict"]["invalid"]


def test_an_oom_killed_container_fails_the_measurement_though_no_cgroup_reading_shows_it(tmp_path):
    def docker(service, n):
        return running(status="exited", exit_code=137, oom_killed=True) if service == "kafka" and n >= 2 else running()
    code, out, _ = check(tmp_path, FakeSystem(docker=docker))
    record = record_in(out)
    kafka = next(limit for limit in record["verdict"]["container_limits"] if limit["container"] == "kafka")
    assert (code, record["outcome"], kafka["held"], kafka["oom_kill"]) == (1, "failed", False, 0)
    assert "kafka: OOM-killed, exit code 137, by Docker's record after acceptance" in record["verdict"]["misses"]


def test_a_processes_left_behind_after_the_settle_are_ended_and_fail_the_measurement(tmp_path):
    polls = int(mc.SETTLE_LEFTOVERS_S / 0.5) + 1      # the first look, then one every 0.5 s of the settle
    system = FakeSystem(left=lambda call: 2 if call < polls else 0)
    code, out, _ = check(tmp_path, system)
    record = record_in(out)
    assert (code, record["outcome"]) == (1, "failed") and ("end", 2) in system.log
    assert record["leftovers"]["suites"] == {"seen": 2, "remaining": 2, "ended": {
        "terminated": [0, 1], "killed": [], "remaining": []}}
    assert record["verdict"]["misses"] == ["pytest suites left 2 process(es) behind"]


def test_processes_that_end_on_their_own_during_the_settle_are_not_left_behind(tmp_path):
    system, record = FakeSystem(left=lambda call: 2 if call < 3 else 0), {}
    assert mc.end_leftovers(system, tmp_path, record, "suites") == 0
    assert record["leftovers"]["suites"] == {"seen": 2, "remaining": 0}
    assert [entry for entry in system.log if entry[0] == "sleep"] == [("sleep", 0.5)] * 3
    assert "end" not in names(system)


def test_a_failed_start_is_a_tool_error_recorded_after_the_cleanup(tmp_path):
    system = FakeSystem(fail={"compose up": subprocess.CalledProcessError(1, "docker compose up")})
    with pytest.raises(subprocess.CalledProcessError):
        check(tmp_path, system)
    record = record_in(tmp_path / "out")
    assert (record["outcome"], record["exit_code"]) == ("tool error", 3)
    assert record["error"].startswith("CalledProcessError") and names(system)[-len(CLEANUP):] == CLEANUP


def test_an_interrupt_during_the_acceptance_cases_stops_sampling_and_still_cleans_up(tmp_path):
    system = FakeSystem(fail={"pytest acceptance": KeyboardInterrupt()})
    with pytest.raises(KeyboardInterrupt):
        check(tmp_path, system)
    record = record_in(tmp_path / "out")
    assert system.samplers[0].stopped and system.samplers[0].final_readings == 1
    assert names(system)[-len(CLEANUP):] == CLEANUP
    assert (record["outcome"], record["exit_code"]) == ("interrupted", 130)


def test_a_cleanup_that_fails_is_a_tool_error(tmp_path):
    system = FakeSystem(fail={"compose down": subprocess.CalledProcessError(1, "docker compose down")})
    code, out, _ = check(tmp_path, system)
    record = record_in(out)
    assert (code, record["outcome"]) == (3, "tool error") and record["verdict"]["passed"]
    assert len(record["cleanup_errors"]) == 1 and record["cleanup_errors"][0].startswith("docker compose down -v:")


def test_containers_still_there_after_the_cleanup_are_a_tool_error(tmp_path):
    code, out, _ = check(tmp_path, FakeSystem(containers=2))
    assert (code, record_in(out)["project_containers_after"]) == (3, 2)


def test_an_unpause_that_is_not_needed_is_ignored(tmp_path):
    system = FakeSystem(fail={"compose unpause": subprocess.CalledProcessError(1, "docker compose unpause")})
    code, out, _ = check(tmp_path, system)
    assert code == 0 and record_in(out)["unpause"].startswith("not needed or not possible")
    assert names(system)[-3:] == ["compose unpause", "compose down", "project_containers"]


def test_keep_leaves_the_runs_outputs(tmp_path):
    code, _, temp = check(tmp_path, FakeSystem(), keep=True)
    assert code == 0 and (temp / "acceptance" / "live0").is_dir()


def test_preflight_names_every_problem():
    system = FakeSystem(dirty=True, others=4, containers=1, busy=(3307, 6380), snapshot=False)
    assert mc.preflight(system) == [
        "the worktree has uncommitted changes", "4 running container(s) outside the etf-risk-jobs project",
        "1 container(s) of the etf-risk-jobs project exist, maybe another session's", "port(s) in use: 3307, 6380",
        "no snapshot at data/processed/full-2026-10-12"]


def test_preflight_reports_git_and_docker_failing():
    system = FakeSystem()

    def broken_git():
        raise subprocess.CalledProcessError(128, "git status")

    def broken_docker():
        raise RuntimeError("docker ps failed with exit code 1")
    system.git_dirty, system.other_containers = broken_git, broken_docker
    problems = mc.preflight(system)
    assert problems[0].startswith("git: Command 'git status' returned non-zero exit status 128")
    assert problems[1:] == ["docker: docker ps failed with exit code 1"]


def test_preflight_is_clear_on_a_ready_machine():
    assert mc.preflight(FakeSystem()) == []


def test_a_clear_preflight_alone_exits_0_and_starts_nothing():
    system = FakeSystem()
    assert mc.main(["--preflight"], system) == 0 and not any(name.startswith("compose") for name in names(system))


def test_a_preflight_that_finds_problems_is_not_counted_and_starts_nothing(capsys):
    system = FakeSystem(others=4)
    assert mc.main(["--preflight"], system) == 2
    out = capsys.readouterr().out
    assert "not ready: 4 running container(s) outside the etf-risk-jobs project" in out
    assert "not counted (exit 2): not started" in out and not any(name.startswith("compose") for name in names(system))


def test_a_machine_that_is_not_ready_gets_no_run_and_no_folder(tmp_path):
    system = FakeSystem(dirty=True)
    assert mc.main(["--out", str(tmp_path / "out")], system) == 2
    assert not (tmp_path / "out").exists() and not any(name.startswith("compose") for name in names(system))


def test_a_ready_machine_gets_a_run_in_a_new_folder_and_never_overwrites_one(tmp_path):
    system = FakeSystem()
    assert mc.main(["--out", str(tmp_path / "out")], system) == 0
    assert record_in(tmp_path / "out")["outcome"] == "passed"
    with pytest.raises(FileExistsError):
        mc.main(["--out", str(tmp_path / "out")], system)


def test_an_error_during_the_check_is_exit_3_once_the_stack_is_removed(tmp_path, capsys):
    system = FakeSystem(fail={"ready": subprocess.TimeoutExpired("services ready", 300)})
    assert mc.main(["--out", str(tmp_path / "out")], system) == 3
    assert record_in(tmp_path / "out")["outcome"] == "tool error" and names(system)[-len(CLEANUP):] == CLEANUP
    assert "tool error (exit 3): the check stopped: TimeoutExpired" in capsys.readouterr().err


@pytest.mark.parametrize("record, expected", [
    ({"verdict": {"passed": True, "counts": True}}, "passed"),
    ({"verdict": {"passed": False, "counts": True}}, "failed"),
    ({"verdict": {"passed": False, "counts": False}}, "not counted"),
    ({"verdict": {"passed": True, "counts": True}, "cleanup_errors": ["docker compose down -v: failed"]}, "tool error"),
    ({"verdict": {"passed": True, "counts": True}, "project_containers_after": 1}, "tool error"),
    ({"verdict": {"passed": True, "counts": True}, "project_containers_after": None}, "tool error"),
    ({"error": "CalledProcessError: docker compose up"}, "tool error"),
    ({}, "tool error"),
    ({"interrupted": True}, "interrupted"),
])
def test_the_outcome_keeps_failed_measurements_invalid_runs_and_tool_errors_apart(record, expected):
    assert mc.outcome({"cleanup_errors": [], "project_containers_after": 0, **record}) == expected
    assert mc.EXIT[expected] == {"passed": 0, "failed": 1, "not counted": 2, "tool error": 3,
                                 "interrupted": 130}[expected]


# Verdicts

def container(peak, anon, budget, **events):
    """A container read twice in one lifetime, created by this run, with its budget as its limit."""
    return mc.summarize_container([reading(peak // 2, anon // 2, limit=budget),
                                   reading(peak, anon, limit=budget, **events)], budget, True)


def clean() -> dict:
    """The figures of a run that counts and passes."""
    run = {"exit_code": 0, "seconds": 1.0, "readable": True, "tests": 10, "failures": 0, "errors": 0, "skipped": 0}
    states = {"mysql": running(), "kafka": running()}
    return {"pytest": {"suites": {**run, "tests": 473, "skipped": 10}, "acceptance": dict(run)},
            "leftovers": {"suites": 0, "acceptance": 0},
            "docker": {"started": dict(states), "after suites": dict(states), "after acceptance": dict(states)},
            "host": {"idle": {"available_bytes": 4 * GiB + 512 * MiB}, "available_min_bytes": 2 * GiB,
                     "compressor_growth_bytes": 10 * MiB, "swap_growth_bytes": 0, "vm_rss_bytes": GiB},
            "containers": {"mysql": container(450 * MiB, 300 * MiB, 512 * MiB),
                           "kafka": container(500 * MiB, 400 * MiB, 640 * MiB)},
            "steps": {"windows": 130 * MiB, "spark_pipeline": int(2.7 * GiB), "verify": 2 * GiB},
            "jobs": {"calendar-year": {"spark_pipeline": 2 * GiB}},
            "processes": {"worker": {"rss_bytes": 64 * MiB, "processes": 4},
                          "reconciler": {"rss_bytes": 52 * MiB, "processes": 9},
                          "submit": {"rss_bytes": 60 * MiB, "processes": 14},
                          "pytest": {"rss_bytes": 200 * MiB, "processes": 2}},
            "sampler_errors": 0}


def planted(change) -> dict:
    measured = clean()
    change(measured)
    return mc.judge(measured)


def test_a_clean_run_counts_and_passes_on_the_container_limits_alone():
    verdict = mc.judge(clean())
    assert (verdict["counts"], verdict["passed"], verdict["invalid"], verdict["misses"]) == (True, True, [], [])
    assert verdict["validates"] == "container limits only"
    assert [(limit["container"], limit["limit_bytes"], limit["held"]) for limit in verdict["container_limits"]] == [
        ("mysql", 512 * MiB, True), ("kafka", 640 * MiB, True)]
    assert [r["criterion"] for r in verdict["supplementary_container"]] == [
        "mysql anon", "mysql limit hits", "kafka anon", "kafka limit hits"]
    assert verdict["native_targets"]["approved"] is False
    assert [r["criterion"] for r in verdict["native_targets"]["results"]] == [
        "step spark_pipeline", "step verify", "step windows", "process worker", "process reconciler", "process submit"]
    assert all(r["within"] for r in verdict["supplementary_container"] + verdict["native_targets"]["results"])


def test_a_container_over_its_limit_or_oom_killed_is_not_held():
    measured = clean()
    measured["containers"]["mysql"] = mc.summarize_container(
        [reading(400 * MiB, cgroup=1), reading(100 * MiB, cgroup=2), reading(520 * MiB, cgroup=2)], 512 * MiB, True)
    measured["docker"]["after acceptance"]["kafka"] = running(status="exited", exit_code=137, oom_killed=True)
    verdict = mc.judge(measured)
    limits = {limit["container"]: limit for limit in verdict["container_limits"]}
    assert (limits["mysql"]["held"], limits["mysql"]["lifetime_peaks_bytes"]) == (False, [400 * MiB, 520 * MiB])
    assert (limits["kafka"]["held"], limits["kafka"]["stopped"]) == (
        False, ["OOM-killed, exit code 137, by Docker's record after acceptance"])
    assert verdict["validates"] == "nothing"


@pytest.mark.parametrize("change, reason", [
    (lambda m: m["host"].update(compressor_growth_bytes=300 * MiB), "the compressor grew by 300 MiB"),
    (lambda m: m["host"].update(swap_growth_bytes=257 * MiB), "the swap grew by 257 MiB"),
    (lambda m: m["pytest"]["acceptance"].update(skipped=10), "acceptance cases: 10 of 10 skipped"),
    (lambda m: m["pytest"]["suites"].update(readable=False, tests=0), "pytest suites: no results"),
    (lambda m: m["containers"].update(kafka=mc.summarize_container([None], 640 * MiB, True)),
     "kafka: no cgroup reading"),
    (lambda m: m["containers"].update(mysql=mc.summarize_container([reading(400 * MiB, limit=GiB)], 512 * MiB, True)),
     "mysql: its limit is not its 512 MiB budget"),
    (lambda m: m["containers"].update(mysql=mc.summarize_container([reading(400 * MiB)], 512 * MiB, False)),
     "mysql: its container is not verified as created by this run"),
    (lambda m: m["containers"].update(mysql=mc.summarize_container(
        [reading(400 * MiB, max=3), reading(410 * MiB, max=1)], 512 * MiB, True)),
     "mysql: a counter went down within lifetime 1"),
    (lambda m: m["docker"]["after acceptance"].update(kafka=None),
     "kafka: Docker's record after acceptance could not be read"),
    (lambda m: m["steps"].pop("verify"), "no launch of verify was recorded"),
    (lambda m: m["processes"]["reconciler"].update(processes=0), "no reconciler process was sampled"),
])
def test_an_invalid_run_does_not_count(change, reason):
    verdict = planted(change)
    assert not verdict["counts"] and not verdict["passed"] and verdict["validates"] == "nothing", verdict
    assert any(r.startswith(reason) for r in verdict["invalid"]), verdict


@pytest.mark.parametrize("change, miss", [
    (lambda m: m["pytest"]["suites"].update(exit_code=1, failures=1), "pytest suites: exit 1, 1 failed"),
    (lambda m: m["pytest"]["acceptance"].update(exit_code=None), "pytest acceptance: exit None"),
    (lambda m: m["leftovers"].update(acceptance=3), "pytest acceptance left 3 process(es) behind"),
    (lambda m: m["containers"].update(mysql=mc.summarize_container(
        [reading(400 * MiB, cgroup=1), reading(100 * MiB, cgroup=2), reading(520 * MiB, cgroup=2)], 512 * MiB, True)),
     "mysql lifetime 2: memory.peak 520 MiB, above its 512 MiB limit"),
    (lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, oom=1)), "kafka: 1 oom event"),
    (lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, oom_kill=2)),
     "kafka: 2 oom_kill event"),
    (lambda m: m["docker"]["after acceptance"].update(kafka=running(status="exited", exit_code=137, oom_killed=True)),
     "kafka: OOM-killed, exit code 137, by Docker's record after acceptance"),
    (lambda m: m["docker"]["after suites"].update(mysql=running(status="exited", exit_code=1)),
     "mysql: exited, exit code 1, by Docker's record after suites"),
])
def test_a_failed_measurement_counts_and_fails(change, miss):
    verdict = planted(change)
    assert verdict["counts"] and not verdict["passed"] and verdict["validates"] == "nothing", verdict
    assert any(m.startswith(miss) for m in verdict["misses"]), verdict


@pytest.mark.parametrize("change, section, criterion", [
    (lambda m: m["containers"].update(mysql=container(450 * MiB, 411 * MiB, 512 * MiB)), "container", "mysql anon"),
    (lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, max=3)), "container",
     "kafka limit hits"),
    (lambda m: m["steps"].update(spark_pipeline=int(3.1 * GiB)), "native", "step spark_pipeline"),
    (lambda m: m["processes"]["worker"].update(rss_bytes=129 * MiB), "native", "process worker"),
])
def test_a_supplementary_threshold_exceeded_is_reported_in_its_section_and_changes_no_outcome(change, section,
                                                                                              criterion):
    verdict = planted(change)
    results = verdict["supplementary_container"] if section == "container" else verdict["native_targets"]["results"]
    assert verdict["counts"] and verdict["passed"], verdict
    assert [r["within"] for r in results if r["criterion"] == criterion] == [False]


def test_an_unsampled_submit_is_reported_as_not_measured():
    verdict = planted(lambda m: m["processes"]["submit"].update(processes=0))
    assert verdict["passed"] and [r for r in verdict["native_targets"]["results"] if r["criterion"] == "process submit"] == [
        {"criterion": "process submit", "value": None, "threshold": 128 * MiB, "within": None}]


def test_the_conclusion_never_claims_more_than_the_verdict():
    assert mc.conclusion(mc.not_counted("too little memory")) == (
        "not counted (exit 2): an invalid run; the reasons are listed above")
    failed = planted(lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, oom=1)))
    assert mc.conclusion(failed) == "failed measurement (exit 1): 1 miss(es), listed above"
    passed = mc.conclusion(mc.judge(clean()))
    assert passed.startswith("passed (exit 0): the container limits held") and passed.endswith(
        "This validates the container limits only: the native-process targets are not approved budgets, and this "
        "run does not validate them.")


def test_the_report_keeps_the_container_limits_apart_from_the_supplementary_targets(capsys):
    measured = clean()
    measured["containers"]["mysql"] = mc.summarize_container(
        [reading(300 * MiB, max=1, cgroup=7), reading(400 * MiB, 300 * MiB, max=4, cgroup=7),
         reading(200 * MiB, cgroup=8, at="t2")], 512 * MiB, True)
    mc.report({"measured": measured, "verdict": mc.judge(measured)})
    out = capsys.readouterr().out
    sections = [out.index(header) for header in (
        "Container limits, the existing budgets (judged):",
        "Supplementary container figures (proposed thresholds, reported only):",
        "Native-process targets (proposed, not approved budgets; reported only, and not validated by this run):",
        "Host and harness (recorded only):")]
    assert sections == sorted(sections)
    for text in ("  mysql: limit 512 MiB; memory.peak 400 MiB at most, over 2 lifetime(s); oom 0, oom_kill 0: held",
                 "    lifetime 1 (cgroup 7, 2 readings from None): memory.peak 400 MiB of 512 MiB; anon 300 MiB, "
                 "file 50 MiB, kernel 10 MiB; events since it began low 0, high 0, max 4",
                 "    lifetime 2 (cgroup 8, 1 readings from t2)",
                 "  mysql anon: 300 MiB against 410 MiB: within", "  mysql limit hits: 4 against 0: above",
                 "  step spark_pipeline: 2.70 GiB against 3.00 GiB: within",
                 "  process worker: 64 MiB against 128 MiB: within (4 process(es) sampled)",
                 "    calendar-year: spark_pipeline 2.00 GiB",
                 "4.50 GiB available idle, 2.00 GiB at the lowest; compressor +10 MiB, swap +0 MiB",
                 "\npassed (exit 0): the container limits held",
                 "This validates the container limits only: the native-process targets are not approved budgets, "
                 "and this run does not validate them.\n"):
        assert text in out, (text, out)
