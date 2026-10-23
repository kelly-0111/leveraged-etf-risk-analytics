"""The job processes' time settings and the relations between them (spec §11;
docs/job-queue.md, "Deadlines").

Leases are wall-clock times in the job table. Every local deadline uses the host's monotonic
clock (time.monotonic()), the same clock in the worker and its launchers:
- After each successful renewal, the worker sends its launcher the absolute deadline
  F = m0 + lease - fence_margin. m0 is the monotonic time just before that renewal started;
  the lease in the table began at or after m0.
- The launcher ends the step's process tree once F has passed: within watchdog_tick, then
  term_grace after SIGTERM, then kill_confirm after SIGKILL.

The tree is therefore gone by F + watchdog_tick + kill_grace, before the lease can expire
(m0 + lease), whenever fence_margin >= watchdog_tick + kill_grace + safety. That holds
whatever the worker is doing: blocked in a database call, stopped, or dead. Safety (no
overlapping Spark work) rests on this watchdog and the host execution lock, never on how long
a database operation takes. The database timeouts (mysql.SERVICE_SESSION) serve liveness
only. Correctness (one accepted result per job) never depends on time: the token guards in
store.py decide it.

check() refuses settings that break any of these relations:
- fence_margin >= watchdog_tick + kill_grace + safety: the watchdog finishes before the lease
  can expire;
- renew_interval + worker_tick < lease - fence_margin: a renewal comes before the deadline;
- Kafka's session timeout at least the broker's 6 s minimum, at least three heartbeats, and
  below the lease, so a standby takes over a stalled worker's partition before its job can
  be requeued;
- max_poll_interval above the attempt limit plus the kill grace, so a legitimate run never
  makes the worker leave its consumer group.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_timing.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from etf_risk.jobs.store import DEFAULT_LEASE

BROKER_MIN_SESSION_TIMEOUT = 6.0   # Kafka's group.min.session.timeout.ms default, in seconds


@dataclass(frozen=True)
class Timing:
    """Seconds throughout. The defaults are the M2 drafts of spec §11; change them only
    together with check()."""
    lease: float = DEFAULT_LEASE.total_seconds()
    renew_interval: float = 10.0
    fence_margin: float = 10.0          # M
    worker_tick: float = 1.0
    watchdog_tick: float = 0.5          # t_w
    term_grace: float = 5.0             # after SIGTERM, before SIGKILL
    kill_confirm: float = 2.0           # after SIGKILL, before the tree must be gone
    safety: float = 2.5                 # ε
    windows_limit: float = 120.0
    spark_pipeline_limit: float = 600.0
    verify_limit: float = 300.0
    attempt_limit: float = 900.0
    lock_slack: float = 30.0
    poll_slack: float = 60.0
    session_timeout: float = 15.0
    heartbeat_interval: float = 3.0
    socket_timeout: float = 10.0

    @property
    def kill_grace(self) -> float:
        """G: the longest an ending tree takes once the watchdog acted."""
        return self.term_grace + self.kill_confirm

    def step_limit(self, step: str) -> float:
        return {"windows": self.windows_limit, "spark_pipeline": self.spark_pipeline_limit,
                "verify": self.verify_limit}[step]

    def lock_wait(self, step: str) -> float:
        """How long a launcher waits for the host lock, and for an earlier tree to end."""
        return self.step_limit(step) + self.kill_grace + self.lock_slack

    @property
    def max_poll_interval(self) -> float:
        return self.attempt_limit + self.kill_grace + self.poll_slack

    def check(self) -> Timing:
        problems = []
        if self.fence_margin < self.watchdog_tick + self.kill_grace + self.safety:
            problems.append(f"fence_margin {self.fence_margin:g} s < watchdog_tick + kill_grace + safety "
                            f"({self.watchdog_tick + self.kill_grace + self.safety:g} s)")
        if self.renew_interval + self.worker_tick >= self.lease - self.fence_margin:
            problems.append(f"renew_interval + worker_tick ({self.renew_interval + self.worker_tick:g} s) must stay"
                            f" below lease - fence_margin ({self.lease - self.fence_margin:g} s)")
        if not (BROKER_MIN_SESSION_TIMEOUT <= self.session_timeout < self.lease):
            problems.append(f"session_timeout {self.session_timeout:g} s must be at least"
                            f" {BROKER_MIN_SESSION_TIMEOUT:g} s and below the lease")
        if 3 * self.heartbeat_interval > self.session_timeout:
            problems.append("the session timeout must leave room for three heartbeats")
        if self.max_poll_interval <= self.attempt_limit + self.kill_grace:
            problems.append("max_poll_interval must exceed the attempt limit plus the kill grace")
        if min(self.windows_limit, self.spark_pipeline_limit, self.verify_limit) <= 0 or self.attempt_limit <= 0:
            problems.append("limits must be positive")
        if problems:
            raise ValueError("inconsistent time settings: " + "; ".join(problems))
        return self


DEFAULT_TIMING = Timing().check()
