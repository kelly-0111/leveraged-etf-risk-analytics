"""The job processes' event logs: one flushed JSON line per event, with UTC and monotonic times.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
from datetime import datetime

from etf_risk.jobs.events import NO_EVENTS, EventLog, read_events


def test_each_event_is_a_line_with_its_times_component_context_and_fields(tmp_path):
    path = tmp_path / "events" / "worker.jsonl"
    log = EventLog(path, "worker", store_id="s" * 32, worker_id="worker-A")
    log.log("claimed", job_id=7, attempt=1)
    first = json.loads(path.read_text())                              # on disk before close()
    log.log("accepted", job_id=7, digest="d" * 64)
    log.close()
    second = read_events(path)[1]
    assert first["event"] == "claimed" and (first["job_id"], first["attempt"]) == (7, 1)
    assert (first["component"], first["store_id"], first["worker_id"]) == ("worker", "s" * 32, "worker-A")
    assert datetime.fromisoformat(first["ts"]).tzinfo is not None
    assert second["mono"] >= first["mono"] and second["event"] == "accepted"


def test_a_line_cut_off_by_a_crash_is_left_out(tmp_path):
    path = tmp_path / "worker.jsonl"
    path.write_text('{"event": "claimed"}\n{"event": "acc')
    assert read_events(path) == [{"event": "claimed"}]


def test_no_events_writes_nothing():
    NO_EVENTS.log("claimed", job_id=1)
    NO_EVENTS.close()
