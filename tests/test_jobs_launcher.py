"""The launcher, with real processes: the absolute-deadline watchdog (including lines queued
while it was stopped), the end of the whole tree, the host lock and the survivor check, the
handshake, the step limit and EOF.

A step here is a small Python script. TREE starts what a Spark step looks like to the
launcher: a child that moves to a process group of its own, as PySpark's daemon does, and an
orphan whose parent exits at once. Every test uses its own lock file and registry, never the
host's.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest

from etf_risk.jobs.launcher import EXIT_CODES
from etf_risk.jobs.processes import MARKER_ENV, Registry

TREE = r"""
import json, os, subprocess, sys, time
pids = {"step": os.getpid()}
child = subprocess.Popen([sys.executable, "-c", "import os, time; os.setpgid(0, 0); time.sleep(600)"])
pids["moved_group"] = child.pid
while os.getpgid(child.pid) == os.getpgid(0):          # until it has moved to a group of its own
    time.sleep(0.01)
r, w = os.pipe()
if os.fork() == 0:
    if os.fork() == 0:
        os.write(w, str(os.getpid()).encode()); os.close(w)
        time.sleep(600); os._exit(0)
    os._exit(0)
os.close(w)
pids["orphan"] = int(os.read(r, 32)); os.wait()
with open(sys.argv[1] + ".tmp", "w") as f:
    json.dump(pids, f)
os.replace(sys.argv[1] + ".tmp", sys.argv[1])
time.sleep(float(sys.argv[2]))
"""

# A step whose orphan lets go of every inherited descriptor (as the JVM does), then exits.
DETACHED = r"""
import json, os, sys, time
r, w = os.pipe()
if os.fork() == 0:
    if os.fork() == 0:
        for fd in range(3, 256):
            if fd != w:
                try: os.close(fd)
                except OSError: pass
        os.write(w, str(os.getpid()).encode()); os.close(w)
        time.sleep(600); os._exit(0)
    os._exit(0)
os.close(w)
orphan = int(os.read(r, 32)); os.wait()
with open(sys.argv[1] + ".tmp", "w") as f:
    json.dump({"orphan": orphan}, f)
os.replace(sys.argv[1] + ".tmp", sys.argv[1])
time.sleep(float(sys.argv[2]))
"""


class Run:
    """One launcher, started as the worker starts it, and helpers to talk to it."""

    def __init__(self, tmp_path, name, command, *, deadline_in=30.0, seq=0, handshake_offset=0.0,
                 step_limit=60.0, lock_wait=5.0, marker=None, drain=2.0, handshake=True):
        self.name, self.dir = name, tmp_path / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.marker = marker or f"{'s' * 32}:{name}:{'k' * 16}"
        self.result_path = self.dir / "result.json"
        args = [sys.executable, "-m", "etf_risk.jobs.launcher", "--marker", self.marker,
                "--lock", str(tmp_path / "host.lock"), "--registry", str(tmp_path / "registry"),
                "--lock-wait", str(lock_wait), "--step-limit", str(step_limit), "--cwd", str(self.dir),
                "--step-log", str(self.dir / "step.log"), "--result", str(self.result_path),
                "--tick", "0.1", "--term-grace", "0.5", "--kill-confirm", "1.0", "--drain", str(drain), "--", *command]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, env={**os.environ, MARKER_ENV: self.marker},
                                     start_new_session=True)
        os.set_blocking(self.proc.stdin.fileno(), False)
        self.deadline = time.monotonic() + deadline_in
        if handshake:
            self.write({"monotonic": time.monotonic() + handshake_offset, "seq": seq, "deadline": self.deadline})

    def write(self, line):
        os.write(self.proc.stdin.fileno(), (json.dumps(line) + "\n").encode())

    def close(self):
        self.proc.stdin.close()

    def wait(self, timeout=30.0):
        code = self.proc.wait(timeout=timeout)
        return code, json.loads(self.result_path.read_text())


def tree(tmp_path, name, seconds=600.0):
    pids_file = tmp_path / f"{name}.pids"
    return [sys.executable, "-c", TREE, str(pids_file), str(seconds)], pids_file


def wait_for(path, timeout=20.0):
    deadline = time.monotonic() + timeout
    while not Path(path).exists():
        assert time.monotonic() < deadline, f"{path} never appeared"
        time.sleep(0.05)
    return json.loads(Path(path).read_text())


def gone(pid):
    try:
        return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return True


TEST_STORE = "s" * 32                                  # every marker in this file starts with it


@pytest.fixture(autouse=True)
def kill_leftovers():
    """Ends what a failing test left behind: only processes with this file's markers, never
    those of a real worker that may be running on this machine."""
    yield
    from etf_risk.jobs.processes import marked_processes
    for value, procs in marked_processes().items():
        if value.startswith(TEST_STORE + ":"):
            for p in procs:
                try:
                    p.kill()
                except psutil.Error:
                    pass


def test_a_step_that_ends_by_itself_reports_its_exit_code_and_releases_the_lock(tmp_path):
    run = Run(tmp_path, "a", [sys.executable, "-c", "import sys; sys.exit(3)"])
    code, result = run.wait()
    assert (code, result["outcome"], result["returncode"]) == (3, "exited", 3)
    import fcntl
    with open(tmp_path / "host.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)            # free again
    assert Registry(tmp_path / "registry").entries() == []


def test_at_its_deadline_the_watchdog_ends_the_whole_tree_including_a_moved_group_and_an_orphan(tmp_path):
    command, pids_file = tree(tmp_path, "t")
    run = Run(tmp_path, "t", command, deadline_in=3.0)
    pids = wait_for(pids_file)
    assert os.getpgid(pids["moved_group"]) != os.getpgid(pids["step"])   # what a process-group kill would miss
    code, result = run.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["deadline"], "deadline")
    assert all(gone(pid) for pid in pids.values()) and result["ended"]["remaining"] == []
    assert set(pids.values()) <= set(result["ended"]["terminated"])


def test_keepalive_lines_move_the_deadline_so_the_step_can_finish(tmp_path):
    command, _ = tree(tmp_path, "k", seconds=2.5)
    run = Run(tmp_path, "k", command, deadline_in=1.5)
    for seq in (1, 2, 3):
        time.sleep(0.7)
        run.write({"seq": seq, "deadline": time.monotonic() + 1.5})
    code, result = run.wait()
    assert (code, result["outcome"], result["lines_accepted"]) == (0, "exited", 3)


def test_eof_from_the_worker_ends_the_tree(tmp_path):
    command, pids_file = tree(tmp_path, "e")
    run = Run(tmp_path, "e", command)
    pids = wait_for(pids_file)
    run.close()
    code, result = run.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["eof"], "eof") and all(gone(p) for p in pids.values())


def test_the_step_limit_ends_the_tree(tmp_path):
    command, pids_file = tree(tmp_path, "l")
    run = Run(tmp_path, "l", command, step_limit=2.0)
    pids = wait_for(pids_file)
    code, result = run.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["timeout"], "timeout") and all(gone(p) for p in pids.values())


def test_a_sigterm_to_the_launcher_ends_its_tree_first(tmp_path):
    command, pids_file = tree(tmp_path, "s")
    run = Run(tmp_path, "s", command)
    pids = wait_for(pids_file)
    run.proc.send_signal(signal.SIGTERM)
    code, result = run.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["terminated"], "terminated") and all(gone(p) for p in pids.values())


def test_stopped_past_its_deadline_the_launcher_fires_on_resume_and_queued_lines_change_nothing(tmp_path):
    """Pause and resume (a): lines that queued up while the launcher was stopped, stale or
    not, can never revive a watchdog whose deadline passed meanwhile."""
    command, pids_file = tree(tmp_path, "p")
    run = Run(tmp_path, "p", command, deadline_in=2.0)
    pids = wait_for(pids_file)
    original = run.deadline
    run.proc.send_signal(signal.SIGSTOP)
    now = time.monotonic()
    run.write({"seq": 1, "deadline": now - 1.0})                 # already past
    run.write({"seq": 0, "deadline": now + 60.0})                # an older sequence number
    run.write({"seq": 2, "deadline": now + 60.0})                # newer and later, but read only after the deadline
    time.sleep(3.0)                                              # the deadline passes while it is stopped
    assert all(not gone(p) for p in pids.values())               # nothing can act while it is stopped
    resumed = time.monotonic()
    run.proc.send_signal(signal.SIGCONT)
    code, result = run.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["deadline"], "deadline")
    assert result["deadline"] == pytest.approx(original) and (result["lines_accepted"], result["lines_ignored"]) == (0, 3)
    assert time.monotonic() - resumed < 0.5 + 1.0 + 3.0           # term grace + kill confirm + slack
    assert all(gone(p) for p in pids.values())


def test_stopped_briefly_only_a_newer_later_future_line_moves_the_deadline(tmp_path):
    """Pause and resume (b): the deadline becomes exactly the newest valid absolute value;
    a stale, an earlier and an out-of-order line change nothing."""
    command, pids_file = tree(tmp_path, "b", seconds=4.0)
    run = Run(tmp_path, "b", command, deadline_in=4.0)
    wait_for(pids_file)                                          # the launcher has read its handshake
    run.proc.send_signal(signal.SIGSTOP)
    now = time.monotonic()
    valid = now + 10.0
    run.write({"seq": 1, "deadline": now + 1.0})                 # earlier than the current deadline
    run.write({"seq": 3, "deadline": valid})                     # newer, later, in the future: taken
    run.write({"seq": 2, "deadline": now + 20.0})                # an older sequence number than 3
    run.write({"seq": 4, "deadline": now - 5.0})                 # in the past
    time.sleep(1.0)                                              # less than the current deadline
    run.proc.send_signal(signal.SIGCONT)
    code, result = run.wait()
    assert (code, result["outcome"]) == (0, "exited")
    assert result["deadline"] == pytest.approx(valid) and (result["lines_accepted"], result["lines_ignored"]) == (1, 3)


def test_the_handshake_must_read_the_same_clock_and_a_live_deadline(tmp_path):
    marker = tmp_path / "started"
    command = [sys.executable, "-c", f"open({str(marker)!r}, 'w').close()"]
    skewed = Run(tmp_path, "skew", command, handshake_offset=-60.0)       # another clock, far behind
    assert skewed.wait()[0] == EXIT_CODES["clock_mismatch"]
    ahead = Run(tmp_path, "ahead", command, handshake_offset=5.0)         # a reading from the future
    assert ahead.wait()[0] == EXIT_CODES["clock_mismatch"]
    late = Run(tmp_path, "late", command, deadline_in=-1.0)
    assert late.wait()[0] == EXIT_CODES["deadline_passed"]
    silent = Run(tmp_path, "silent", command, handshake=False)
    silent.close()
    assert silent.wait()[0] == EXIT_CODES["no_handshake"]
    assert not marker.exists()                                   # no step started


def test_the_host_lock_lets_one_step_run_at_a_time(tmp_path):
    command, pids_file = tree(tmp_path, "first")
    first = Run(tmp_path, "first", command)
    wait_for(pids_file)
    started = tmp_path / "second-started"
    second = Run(tmp_path, "second", [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"], lock_wait=1.5)
    code, result = second.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["lock_busy"], "lock_busy") and not started.exists()
    first.close()
    assert first.wait()[1]["outcome"] == "eof"


def test_a_survivor_of_a_dead_launchers_tree_blocks_the_next_step_until_it_is_gone(tmp_path):
    pids_file = tmp_path / "dead.pids"
    dead = Run(tmp_path, "dead", [sys.executable, "-c", DETACHED, str(pids_file), "0.2"], drain=30.0)
    orphan = wait_for(pids_file)["orphan"]
    time.sleep(0.5)                                              # the step has exited; the launcher waits for its orphan
    dead.proc.kill()                                             # the launcher dies, its orphan survives
    dead.proc.wait()
    assert not gone(orphan) and len(Registry(tmp_path / "registry").entries()) == 1
    started = tmp_path / "next-started"
    blocked = Run(tmp_path, "next", [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"], lock_wait=1.5)
    code, result = blocked.wait()
    assert (code, result["outcome"], result["survivors_seen"]) == (EXIT_CODES["lock_busy"], "lock_busy", [orphan])
    assert not started.exists()
    psutil.Process(orphan).kill()
    psutil.Process(orphan).wait(timeout=5)
    after = Run(tmp_path, "after", [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"])
    assert after.wait()[1]["outcome"] == "exited" and started.exists()
    assert Registry(tmp_path / "registry").entries() == []       # the dead launcher's entry was cleaned up


def test_a_lock_held_outside_any_launcher_keeps_the_step_from_starting(tmp_path):
    """The lock, not only the survivor check: a process that is no launcher and has no tree
    in the registry can hold it, as the recovery harness does for its reference runs. It
    also makes "check survivors, register, start" one step across launchers."""
    import fcntl
    started = tmp_path / "started"
    command = [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"]
    (tmp_path / "registry").mkdir()
    with open(tmp_path / "host.lock", "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        code, result = Run(tmp_path, "held", command, lock_wait=1.5).wait()
        assert (code, result["outcome"]) == (EXIT_CODES["lock_busy"], "lock_busy") and not started.exists()
    assert Run(tmp_path, "released", command).wait()[1]["outcome"] == "exited" and started.exists()


def test_a_steps_interval_is_on_the_monotonic_clock_that_the_handshake_checked(tmp_path):
    """step_started_mono and tree_ended_mono read the host's monotonic clock, as this process
    does, so intervals of different launchers compare directly: the host lock puts the later
    step after the earlier tree has ended. A launcher that starts no step records neither."""
    before = time.monotonic()
    sleeper = Run(tmp_path, "sleeper", [sys.executable, "-c", "import time; time.sleep(0.3)"])
    quick = Run(tmp_path, "quick", [sys.executable, "-c", "pass"])
    one, two = sleeper.wait()[1], quick.wait()[1]
    after = time.monotonic()
    for result in (one, two):
        assert before < result["step_started_mono"] < result["tree_ended_mono"] < after
    assert one["tree_ended_mono"] - one["step_started_mono"] >= 0.3
    earlier, later = sorted((one, two), key=lambda r: r["step_started_mono"])
    assert later["step_started_mono"] > earlier["tree_ended_mono"]
    code, result = Run(tmp_path, "late", [sys.executable, "-c", "pass"], deadline_in=-1.0).wait()
    assert (code, result["outcome"]) == (EXIT_CODES["deadline_passed"], "deadline_passed")
    assert "step_started_mono" not in result and "tree_ended_mono" not in result
