"""The fault hook armed through a file (etf_risk.jobs.faults), offline: kill is replaced, so no
process ends.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import json

import pytest

from etf_risk.jobs import faults
from etf_risk.jobs.events import EventLog, read_events
from etf_risk.jobs.worker import WORKER_FAULT_POINTS


@pytest.fixture
def hook(tmp_path):
    log = tmp_path / "worker.jsonl"
    kills = []
    fault = faults.FaultFile(tmp_path / "A.fault", EventLog(log, "worker", worker_id="A"), kill=lambda: kills.append(1))
    return fault, kills, log


def events(log):
    return [(e["event"], e.get("point"), e.get("action") or e.get("why")) for e in read_events(log)]


def test_nothing_happens_while_nothing_is_armed(hook):
    fault, kills, log = hook
    for point in WORKER_FAULT_POINTS:
        fault(point)
    assert kills == [] and read_events(log) == []              # the log exists, empty: EventLog opens it


def test_a_kill_fires_once_at_its_point_and_nowhere_else(hook):
    fault, kills, log = hook
    faults.arm(fault.path, "after_pipeline")
    fault("before_claim")
    fault("after_claim")
    assert fault.path.exists() and kills == []                  # left for its own point
    fault("after_pipeline")
    assert not fault.path.exists() and kills == [1]
    fault("after_pipeline")                                     # once: the file is gone
    assert kills == [1] and events(log) == [("fault_injected", "after_pipeline", "kill")]


def test_a_hold_waits_for_its_release(hook, tmp_path):
    fault, kills, log = hook
    release = tmp_path / "release"
    ticks = []

    def sleep(seconds):
        ticks.append(seconds)
        if len(ticks) == 3:
            release.touch()

    fault._sleep = sleep
    faults.arm(fault.path, "after_pipeline", "hold", release=release, timeout_s=60)
    fault("after_pipeline")
    assert kills == [] and len(ticks) == 3
    assert events(log) == [("fault_injected", "after_pipeline", "hold"), ("fault_released", "after_pipeline", "released")]


def test_a_hold_gives_up_after_its_timeout(hook, tmp_path):
    fault, kills, log = hook
    now = [100.0]
    fault._clock = lambda: now[0]
    fault._sleep = lambda seconds: now.__setitem__(0, now[0] + seconds)
    faults.arm(fault.path, "after_pipeline", "hold", release=tmp_path / "never", timeout_s=1.0)
    fault("after_pipeline")
    assert events(log)[-1] == ("fault_released", "after_pipeline", "timeout")


@pytest.mark.parametrize("text", ["not json", json.dumps({"point": "no_such_point", "action": "kill"}),
                                  json.dumps({"point": "after_claim", "action": "explode"}),
                                  json.dumps({"point": "after_claim", "action": "hold"})])
def test_an_arming_that_went_wrong_is_refused_and_never_becomes_a_fault(hook, text):
    fault, kills, log = hook
    fault.path.write_text(text)
    fault("after_claim")
    assert kills == [] and not fault.path.exists()
    assert [e for e, _, _ in events(log)] == ["fault_refused"]


def test_arming_is_atomic_and_the_environment_decides(tmp_path, monkeypatch):
    path = tmp_path / "B.fault"
    faults.arm(path, "after_accept_commit")
    assert json.loads(path.read_text()) == {"point": "after_accept_commit", "action": "kill"}
    assert sorted(p.name for p in tmp_path.iterdir()) == ["B.fault"]          # no temporary file left
    log = EventLog(tmp_path / "w.jsonl", "worker")
    monkeypatch.delenv(faults.FAULT_FILE_ENV, raising=False)
    assert faults.fault_from_environment(log) is None
    monkeypatch.setenv(faults.FAULT_FILE_ENV, str(path))
    assert faults.fault_from_environment(log).path == path
