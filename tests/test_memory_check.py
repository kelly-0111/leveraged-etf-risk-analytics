"""tests/memory_check.py without Docker, services, Spark or timing. Readings of cgroups,
vm_stat, command lines, records and JUnit files; segments across restarts; the sampler, one
tick at a time on stand-in processes and readings; the check's run with every effect stood in
for, through success, refusal, interruption and failed cleanup; and, with short-lived real
processes and handshakes in place of sleeps, the time limit and the ending of leftovers. Each
planted problem must reach the verdict that covers it, and no proposed threshold may change a
verdict.

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


def reading(peak, anon=100 * MiB, *, limit=512 * MiB, file=50 * MiB, kernel=10 * MiB, at=None, **events):
    return {"at_utc": at, "peak": peak, "limit": limit, "current": peak, "anon": anon, "file": file,
            "kernel": kernel, "kernel_from": "kernel", "events": {**NO_EVENTS, **events}}


def write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


# Reading a cgroup

CGROUP_OUTPUT = ("peak 419430400\nlimit 536870912\ncurrent 400000000\nstat_anon 314572800\nstat_file 73400320\n"
                 "stat_kernel 20971520\nstat_kernel_stack 1048576\nstat_slab 8388608\nstat_sock 0\n"
                 "events_low 0\nevents_high 0\nevents_max 7\nevents_oom 0\nevents_oom_kill 0\nevents_oom_group_kill 0\n")


def test_a_cgroup_reading_keeps_the_total_its_kinds_of_memory_and_the_events():
    assert mc.parse_cgroup(CGROUP_OUTPUT) == {
        "peak": 419430400, "limit": 536870912, "current": 400000000, "anon": 314572800, "file": 73400320,
        "kernel": 20971520, "kernel_from": "kernel", "events": {**NO_EVENTS, "max": 7}}


def test_kernel_memory_is_the_sum_of_its_parts_without_a_kernel_line():
    text = CGROUP_OUTPUT.replace("stat_kernel 20971520\n", "") + "stat_pagetables 2097152\nstat_percpu 1048576\n"
    r = mc.parse_cgroup(text)
    assert (r["kernel"], r["kernel_from"]) == (1048576 + 8388608 + 2097152 + 1048576, "parts")


def test_no_limit_and_missing_counters_read_as_such():
    r = mc.parse_cgroup("peak 1\nlimit max\nstat_anon 1\n")
    assert (r["limit"], r["file"], r["current"], r["events"]) == (None, None, None, NO_EVENTS)


@pytest.mark.parametrize("text", ["", "Error response from daemon: container is paused\n", "peak 1\nlimit max\n",
                                  "stat_anon 5\n", "peak x\nstat_anon 5\n"])
def test_output_without_a_total_or_an_anon_figure_is_no_reading(text):
    assert mc.parse_cgroup(text) is None


def runner(result=None, error=None, seen=None):
    def run(command, **kwargs):
        if seen is not None:
            seen.append((command, kwargs))
        if error is not None:
            raise error
        return result
    return run


@pytest.mark.parametrize("run", [
    runner(error=subprocess.TimeoutExpired("docker", 10)),
    runner(error=FileNotFoundError("docker")),
    runner(subprocess.CompletedProcess([], 1, "", 'service "mysql" is not running')),
    runner(subprocess.CompletedProcess([], 0, "garbage", "")),
])
def test_a_cgroup_that_cannot_be_read_gives_no_reading(run):
    assert mc.read_cgroup("mysql", run=run) is None


def test_a_cgroup_is_read_through_docker_compose_exec_within_ten_seconds():
    seen = []
    result = mc.read_cgroup("kafka", run=runner(subprocess.CompletedProcess([], 0, CGROUP_OUTPUT, ""), seen=seen))
    command, kwargs = seen[0]
    assert result["peak"] == 419430400 and command[4:9] == ["exec", "-T", "kafka", "sh", "-c"]
    assert kwargs["timeout"] == 10


# Restarts

def test_segments_start_where_a_counter_goes_down_and_not_at_gaps():
    readings = [reading(100), None, reading(150), reading(60), reading(80), reading(90, max=3), None,
                reading(95, max=1)]
    assert [[r["peak"] for r in life] for life in mc.segments(readings)] == [[100, 150], [60, 80, 90], [95]]


def test_events_count_from_the_run_start_and_from_zero_after_each_restart():
    readings = [reading(300 * MiB, 200 * MiB, max=4, oom=1),      # the run's first reading
                reading(500 * MiB, 310 * MiB, file=150 * MiB, max=9, oom=1),
                reading(200 * MiB, 150 * MiB, at="restarted"),     # a restart: new counters
                reading(450 * MiB, 330 * MiB, kernel=30 * MiB, max=2, oom_kill=1)]
    summary = mc.summarize_container(readings, 512 * MiB)
    first, second = summary["segments"]
    assert (first["readings"], first["peak_bytes"], first["anon_bytes"], first["file_bytes"]) == (
        2, 500 * MiB, 310 * MiB, 150 * MiB)
    assert first["events"] == {**NO_EVENTS, "max": 5}                   # the oom came before the run
    assert (second["from_utc"], second["peak_bytes"], second["kernel_bytes"]) == ("restarted", 450 * MiB, 30 * MiB)
    assert second["events"] == {**NO_EVENTS, "max": 2, "oom_kill": 1}   # counted from zero
    assert (summary["peak_bytes"], summary["anon_bytes"], summary["budget_bytes"]) == (
        500 * MiB, 330 * MiB, 512 * MiB)
    assert summary["events"] == {**NO_EVENTS, "max": 7, "oom_kill": 1}


def test_a_container_never_read_has_no_segments_and_no_figures():
    summary = mc.summarize_container([None, None], 640 * MiB)
    assert (summary["segments"], summary["peak_bytes"], summary["anon_bytes"], summary["events"]) == (
        [], None, None, NO_EVENTS)


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


def test_measure_takes_growth_from_the_idle_reading_and_peaks_from_the_records(tmp_path):
    write(tmp_path / "acceptance" / "live0" / "job-1-attempt-1" / "logs" / "verify.launcher.json",
          {"peak_rss_bytes": GiB})
    idle = {"available_bytes": 5 * GiB, "compressor_bytes": 100 * MiB, "swap_bytes": 0}
    fake = SimpleNamespace(
        host=[{"compressor_bytes": 150 * MiB, "swap_bytes": 0}, {"at_utc": "a failed host reading"},
              {"compressor_bytes": 120 * MiB, "swap_bytes": 8 * MiB}],
        available_min=3 * GiB, errors=1, readings={"mysql": [reading(300 * MiB, 250 * MiB)], "kafka": [None]},
        rss={"worker": 64 * MiB, "reconciler": 52 * MiB, "submit": 0, "pytest": 200 * MiB, "vm": 2 * GiB},
        pids={"worker": {1, 2}, "reconciler": {3}, "submit": set(), "pytest": {4}, "vm": {5}})
    measured = mc.measure(fake, idle, tmp_path, {"suites": {}, "acceptance": {}}, {"suites": 0, "acceptance": 1})
    assert (measured["host"]["compressor_growth_bytes"], measured["host"]["swap_growth_bytes"]) == (50 * MiB, 8 * MiB)
    assert measured["steps"] == {"verify": GiB} and measured["leftovers"] == {"suites": 0, "acceptance": 1}
    assert measured["containers"]["mysql"]["anon_bytes"] == 250 * MiB
    assert measured["containers"]["kafka"]["segments"] == []
    assert measured["processes"]["worker"] == {"rss_bytes": 64 * MiB, "processes": 2}
    assert measured["processes"]["submit"] == {"rss_bytes": 0, "processes": 0} and measured["sampler_errors"] == 1


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


def test_leftovers_are_the_processes_that_name_the_folder_or_carry_its_stores_markers(tmp_path):
    temp = tmp_path / "check"
    (temp / "acceptance" / "live0" / "out" / "store1").mkdir(parents=True)
    children = {"names the folder": spawn("--output-root", str(temp / "acceptance" / "live0" / "out")),
                "marked by its store": spawn(env={"ETF_RISK_ATTEMPT": "store1:run-1:0123456789abcdef"}),
                "another store": spawn(env={"ETF_RISK_ATTEMPT": "store2:run-1:0123456789abcdef"}),
                "another folder": spawn("--output-root", str(tmp_path / "elsewhere"))}
    try:
        assert {p.pid for p in mc.leftovers(temp)} == {children["names the folder"].pid,
                                                       children["marked by its store"].pid}
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
        self.host = [{"compressor_bytes": GiB + 10 * MiB, "swap_bytes": 0}]
        self.available_min, self.errors = 3 * GiB, 0
        self.rss = {"worker": 64 * MiB, "reconciler": 52 * MiB, "submit": 60 * MiB, "pytest": 200 * MiB, "vm": GiB}
        self.pids = {"worker": {1}, "reconciler": {2}, "submit": {3}, "pytest": {4}, "vm": {5}}
        self.readings = {"mysql": [reading(400 * MiB, 300 * MiB)],
                         "kafka": [reading(450 * MiB, 350 * MiB, limit=640 * MiB)]}

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class FakeSystem:
    """The machine, stood in for: every call is logged, and each failure is planted where asked."""

    def __init__(self, available=5 * GiB, fail=(), left=0, containers=0, dirty=False, others=0, busy=(),
                 snapshot=True):
        self.log, self.fail, self.available_bytes, self.left = [], dict(fail), available, left
        self.containers, self.dirty, self.others, self.busy = containers, dirty, others, set(busy)
        self.snapshot, self.samplers = snapshot, []

    def _call(self, name, *details):
        self.log.append((name, *details))
        if name in self.fail:
            raise self.fail[name]

    def compose(self, *args, timeout=300):
        self._call(f"compose {args[0]}")

    def ready(self, env):
        self._call("ready")

    def sleep(self, seconds):
        self._call("sleep", seconds)

    def host_memory(self):
        self._call("host_memory")
        return {"available_bytes": self.available_bytes, "compressor_bytes": GiB, "swap_bytes": 0}

    def available(self):
        return self.available_bytes

    def sampler(self, samples):
        self._call("sampler")
        self.samplers.append(FakeSampler(samples))
        return self.samplers[-1]

    def run_pytest(self, name, files, env, out, temp, timeout):
        self._call(f"pytest {name}", env.get("ETF_RISK_LIVE_PIPELINE"), timeout)
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
        found, self.left = [object()] * self.left, 0    # what a run left is found once
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


def test_a_clean_run_passes_and_cleans_up_in_order(tmp_path):
    system = FakeSystem()
    code, out, temp = check(tmp_path, system)
    assert code == 0
    assert [entry[0] for entry in system.log] == [
        "keep_awake", "compose up", "ready", "sleep", "host_memory", "sampler", "pytest suites", "leftovers",
        "pytest acceptance", "leftovers", "leftovers", "compose down", "project_containers"]
    assert ("sleep", mc.SETTLE_S) in system.log
    assert ("pytest suites", None, 1800) in system.log and ("pytest acceptance", "1", 3600) in system.log
    record = record_in(out)
    assert record["verdict"]["passed"] and record["cleanup_errors"] == [] and record["project_containers_after"] == 0
    assert record["measured"]["jobs"] == {"rolling, stride 21": {"spark_pipeline": int(2.7 * GiB)}}
    assert record["supplementary"]["native_approved"] is False and record["verdict"]["native_targets"]["approved"] is False
    assert sorted(record["supplementary"]["native"]) == [
        "process reconciler", "process submit", "process worker", "step spark_pipeline", "step verify", "step windows"]
    assert system.samplers[0].started and system.samplers[0].stopped and not temp.exists()
    assert (out / "records" / "acceptance" / "live0" / "out" / "store" / "job-1-attempt-1" / "attempt.json").exists()


def test_too_little_memory_with_the_stack_idle_stops_before_any_test_and_cleans_up(tmp_path):
    system = FakeSystem(available=3 * GiB)
    code, out, _ = check(tmp_path, system)
    names = [entry[0] for entry in system.log]
    assert code == 2 and "sampler" not in names and not any(name.startswith("pytest") for name in names)
    assert names[-3:] == ["leftovers", "compose down", "project_containers"]
    assert record_in(out)["verdict"]["invalid"] == ["3.00 GiB available with the stack idle, below 4.0 GiB"]


def test_a_failed_start_still_removes_the_stack_and_writes_the_record(tmp_path):
    system = FakeSystem(fail={"compose up": subprocess.CalledProcessError(1, "docker compose up")})
    with pytest.raises(subprocess.CalledProcessError):
        check(tmp_path, system)
    record = record_in(tmp_path / "out")
    assert ("compose down",) in system.log and "measured" not in record and record["cleanup_errors"] == []


def test_an_interrupt_during_the_acceptance_cases_stops_sampling_and_still_cleans_up(tmp_path):
    system = FakeSystem(fail={"pytest acceptance": KeyboardInterrupt()})
    with pytest.raises(KeyboardInterrupt):
        check(tmp_path, system)
    assert system.samplers[0].stopped
    assert [entry[0] for entry in system.log][-3:] == ["leftovers", "compose down", "project_containers"]
    assert record_in(tmp_path / "out")["ended_at_utc"]


def test_a_cleanup_that_fails_is_recorded_and_the_run_does_not_count(tmp_path):
    system = FakeSystem(fail={"compose down": subprocess.CalledProcessError(1, "docker compose down")})
    code, out, _ = check(tmp_path, system)
    errors = record_in(out)["cleanup_errors"]
    assert code == 2 and len(errors) == 1 and errors[0].startswith("docker compose down -v:")


def test_containers_still_there_after_the_cleanup_mean_the_run_does_not_count(tmp_path):
    code, out, _ = check(tmp_path, FakeSystem(containers=2))
    assert code == 2 and record_in(out)["project_containers_after"] == 2


def test_processes_a_run_left_behind_are_ended_and_fail_the_run(tmp_path):
    system = FakeSystem(left=2)
    code, out, _ = check(tmp_path, system)
    record = record_in(out)
    assert code == 1 and ("end", 2) in system.log and record["ended"]["suites"]["terminated"] == [0, 1]
    assert record["verdict"]["misses"] == ["pytest suites left 2 process(es) behind"]


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


def test_the_preflight_alone_starts_nothing(capsys):
    system = FakeSystem(others=4)
    assert mc.main(["--preflight"], system) == 2
    assert "not ready: 4 running container(s) outside the etf-risk-jobs project" in capsys.readouterr().out
    assert not any(entry[0].startswith("compose") for entry in system.log)


def test_a_machine_that_is_not_ready_gets_no_run_and_no_folder(tmp_path):
    system = FakeSystem(dirty=True)
    assert mc.main(["--out", str(tmp_path / "out")], system) == 2
    assert not (tmp_path / "out").exists() and not any(entry[0].startswith("compose") for entry in system.log)


def test_a_ready_machine_gets_a_run_in_a_new_folder_and_never_overwrites_one(tmp_path):
    system = FakeSystem()
    assert mc.main(["--out", str(tmp_path / "out")], system) == 0
    assert (tmp_path / "out" / "record.json").exists()
    with pytest.raises(FileExistsError):
        mc.main(["--out", str(tmp_path / "out")], system)


# Verdicts

def container(peak, anon, budget, **events):
    """A container read twice in one life, with its budget as its limit."""
    return mc.summarize_container([reading(peak // 2, anon // 2, limit=budget),
                                   reading(peak, anon, limit=budget, **events)], budget)


def clean() -> dict:
    """The figures of a run that counts and passes."""
    run = {"exit_code": 0, "seconds": 1.0, "readable": True, "tests": 10, "failures": 0, "errors": 0, "skipped": 0}
    return {"pytest": {"suites": {**run, "tests": 473, "skipped": 10}, "acceptance": dict(run)},
            "leftovers": {"suites": 0, "acceptance": 0},
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
    assert [(limit["container"], limit["limit_bytes"], limit["held"]) for limit in verdict["container_limits"]] == [
        ("mysql", 512 * MiB, True), ("kafka", 640 * MiB, True)]
    assert [r["criterion"] for r in verdict["supplementary_container"]] == [
        "mysql anon", "mysql limit hits", "kafka anon", "kafka limit hits"]
    assert verdict["native_targets"]["approved"] is False
    assert [r["criterion"] for r in verdict["native_targets"]["results"]] == [
        "step spark_pipeline", "step verify", "step windows", "process worker", "process reconciler", "process submit"]
    assert all(r["within"] for r in verdict["supplementary_container"] + verdict["native_targets"]["results"])


def test_a_container_over_its_limit_or_with_an_oom_kill_is_not_held():
    measured = clean()
    measured["containers"]["mysql"] = mc.summarize_container(
        [reading(400 * MiB), reading(100 * MiB), reading(520 * MiB)], 512 * MiB)
    measured["containers"]["kafka"] = container(500 * MiB, 400 * MiB, 640 * MiB, oom_kill=1)
    limits = {limit["container"]: limit for limit in mc.judge(measured)["container_limits"]}
    assert (limits["mysql"]["held"], limits["mysql"]["segment_peaks_bytes"]) == (False, [400 * MiB, 520 * MiB])
    assert (limits["kafka"]["held"], limits["kafka"]["oom_kill"]) == (False, 1)


@pytest.mark.parametrize("change, reason", [
    (lambda m: m["host"].update(compressor_growth_bytes=300 * MiB), "the compressor grew by 300 MiB"),
    (lambda m: m["host"].update(swap_growth_bytes=257 * MiB), "the swap grew by 257 MiB"),
    (lambda m: m["pytest"]["acceptance"].update(skipped=10), "acceptance cases: 10 of 10 skipped"),
    (lambda m: m["pytest"]["suites"].update(readable=False, tests=0), "pytest suites: no results"),
    (lambda m: m["containers"].update(kafka=mc.summarize_container([None], 640 * MiB)), "kafka: no cgroup reading"),
    (lambda m: m["containers"].update(mysql=mc.summarize_container([reading(400 * MiB, limit=GiB)], 512 * MiB)),
     "mysql: its limit is not its 512 MiB budget"),
    (lambda m: m["steps"].pop("verify"), "no launch of verify was recorded"),
    (lambda m: m["processes"]["reconciler"].update(processes=0), "no reconciler process was sampled"),
])
def test_a_run_short_of_memory_or_of_its_measurements_does_not_count(change, reason):
    verdict = planted(change)
    assert not verdict["counts"] and not verdict["passed"], verdict
    assert any(r.startswith(reason) for r in verdict["invalid"]), verdict


@pytest.mark.parametrize("change, miss", [
    (lambda m: m["pytest"]["suites"].update(exit_code=1, failures=1), "pytest suites: exit 1, 1 failed"),
    (lambda m: m["pytest"]["acceptance"].update(exit_code=None), "pytest acceptance: exit None"),
    (lambda m: m["leftovers"].update(acceptance=3), "pytest acceptance left 3 process(es) behind"),
    (lambda m: m["containers"].update(mysql=mc.summarize_container(
        [reading(400 * MiB), reading(100 * MiB), reading(520 * MiB)], 512 * MiB)),
     "mysql segment 2: memory.peak 520 MiB, above its 512 MiB limit"),
    (lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, oom=1)), "kafka: 1 oom event"),
    (lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, oom_kill=2)),
     "kafka: 2 oom_kill event"),
])
def test_failed_runs_leftovers_and_the_containers_budgets_are_misses(change, miss):
    verdict = planted(change)
    assert verdict["counts"] and not verdict["passed"], verdict
    assert any(m.startswith(miss) for m in verdict["misses"]), verdict


@pytest.mark.parametrize("change, section, criterion", [
    (lambda m: m["containers"].update(mysql=container(450 * MiB, 411 * MiB, 512 * MiB)), "container", "mysql anon"),
    (lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, max=3)), "container",
     "kafka limit hits"),
    (lambda m: m["steps"].update(spark_pipeline=int(3.1 * GiB)), "native", "step spark_pipeline"),
    (lambda m: m["processes"]["worker"].update(rss_bytes=129 * MiB), "native", "process worker"),
])
def test_a_supplementary_threshold_exceeded_is_reported_in_its_section_and_changes_no_verdict(change, section,
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
    assert mc.conclusion(mc.not_counted("too little memory")) == "does not count"
    failed = planted(lambda m: m["containers"].update(kafka=container(500 * MiB, 400 * MiB, 640 * MiB, oom=1)))
    assert mc.conclusion(failed) == "failed: 1 miss(es), listed above"
    passed = mc.conclusion(mc.judge(clean()))
    assert passed.startswith("passed: the container limits held") and passed.endswith(
        "This validates the container limits only: the native-process targets are not approved budgets, and this "
        "run does not validate them.")


def test_the_report_keeps_the_container_limits_apart_from_the_supplementary_targets(capsys):
    measured = clean()
    measured["containers"]["mysql"] = mc.summarize_container(
        [reading(300 * MiB, max=1), reading(400 * MiB, 300 * MiB, max=4), reading(200 * MiB, at="t2")], 512 * MiB)
    mc.report({"measured": measured, "verdict": mc.judge(measured)})
    out = capsys.readouterr().out
    sections = [out.index(header) for header in (
        "Container limits, the existing budgets (judged):",
        "Supplementary container figures (proposed thresholds, reported only):",
        "Native-process targets (proposed, not approved budgets; reported only, and not validated by this run):",
        "Host and harness (recorded only):")]
    assert sections == sorted(sections)
    for text in ("  mysql: limit 512 MiB; memory.peak 400 MiB at most, over 2 segment(s); oom 0, oom_kill 0: held",
                 "    segment 1 (2 readings from None): memory.peak 400 MiB of 512 MiB; anon 300 MiB, file 50 MiB, "
                 "kernel 10 MiB; events low +0, high +0, max +3",
                 "    segment 2 (1 readings from t2)",
                 "  mysql anon: 300 MiB against 410 MiB: within", "  mysql limit hits: 3 against 0: above",
                 "  step spark_pipeline: 2.70 GiB against 3.00 GiB: within",
                 "  process worker: 64 MiB against 128 MiB: within (4 process(es) sampled)",
                 "    calendar-year: spark_pipeline 2.00 GiB",
                 "4.50 GiB available idle, 2.00 GiB at the lowest; compressor +10 MiB, swap +0 MiB",
                 "\npassed: the container limits held",
                 "This validates the container limits only: the native-process targets are not approved budgets, "
                 "and this run does not validate them.\n"):
        assert text in out, (text, out)
