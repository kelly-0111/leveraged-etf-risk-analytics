"""The job processes' time settings: the drafts of spec §11 and the relations check() keeps.

AI contribution: written with Claude Code (Opus 5.5).
"""
from dataclasses import replace

import pytest

from etf_risk.jobs.store import DEFAULT_LEASE
from etf_risk.jobs.timing import DEFAULT_TIMING, Timing


def test_the_defaults_are_the_drafts_and_keep_the_watchdog_inside_the_lease():
    t = DEFAULT_TIMING
    assert (t.lease, t.renew_interval, t.fence_margin, t.watchdog_tick, t.kill_grace) == (
        DEFAULT_LEASE.total_seconds(), 10.0, 10.0, 0.5, 7.0)
    assert t.fence_margin >= t.watchdog_tick + t.kill_grace + t.safety
    # The tree is gone by F + t_w + G, before the lease, which began no earlier than m0, expires.
    m0 = 1000.0
    deadline = m0 + t.lease - t.fence_margin
    assert deadline + t.watchdog_tick + t.kill_grace < m0 + t.lease
    assert t.max_poll_interval == t.attempt_limit + t.kill_grace + 60 == 967.0
    assert t.lock_wait("spark_pipeline") == 600 + 7 + 30


@pytest.mark.parametrize("change, problem", [
    ({"fence_margin": 9.0}, "fence_margin"),
    ({"renew_interval": 49.0}, "renew_interval"),
    ({"session_timeout": 5.0}, "session_timeout"),
    ({"session_timeout": 60.0}, "session_timeout"),
    ({"heartbeat_interval": 6.0}, "three heartbeats"),
    ({"poll_slack": 0.0}, "max_poll_interval"),
])
def test_inconsistent_settings_are_refused(change, problem):
    with pytest.raises(ValueError, match=problem):
        replace(DEFAULT_TIMING, **change).check()


def test_a_shorter_lease_for_the_live_tests_keeps_every_relation():
    Timing(lease=24.0, renew_interval=4.0, session_timeout=10.0).check()
