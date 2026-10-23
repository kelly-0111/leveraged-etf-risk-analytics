"""Event logs of the job processes (worker, reconciler, submit): one JSON object per line,
written and flushed as each event happens, so a process killed by SIGKILL loses at most the
event it was writing.

Every event has:
- "ts", the time in UTC (ISO 8601, microseconds), comparable across the processes of this
  machine;
- "mono", the writing process's time.monotonic(), for durations within that process;
- "pid", "component" ("worker", "reconciler", "submit") and "event";
- the context the log was opened with (for example store_id and worker_id);
- the event's own fields.

The recovery experiments take their detection and recovery times from these logs together
with the job tables (spec §11; docs/job-queue.md lists the events).

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_events.py.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


class EventLog:
    def __init__(self, path: str | Path | None, component: str, **context: Any):
        """path None writes nothing (the tests and the simulated pipeline need no log)."""
        self.component, self.context = component, context
        self._file: TextIO | None = None
        self._lock = threading.Lock()
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._file = open(path, "a", encoding="utf-8")

    def log(self, event: str, **fields: Any) -> None:
        if self._file is None:
            return
        record = {"ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"), "mono": time.monotonic(),
                  "pid": os.getpid(), "component": self.component, "event": event, **self.context, **fields}
        line = json.dumps(record, default=str) + "\n"
        with self._lock:
            self._file.write(line)
            self._file.flush()

    def close(self) -> None:
        with self._lock:
            if self._file is not None:
                self._file.close()
                self._file = None


NO_EVENTS = EventLog(None, "none")


def read_events(path: str | Path) -> list[dict]:
    """The events of one log; a last line cut off by a crash is left out."""
    events = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
