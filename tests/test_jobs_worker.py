"""The worker with a simulated pipeline: duplicate and concurrent deliveries, crashes, expired
leases, stale workers, retries.

Every test ends with WorkerEnv.check() (tests/jobs_backends.py): no invariant violation in
the tables; at most one accepted attempt, exactly one if the job succeeded, and as many as
the deliveries told "accepted" (plus any acceptance whose worker died before it could tell);
the accepted folder holds that attempt's result; no two attempts share a folder. Deliveries
here are explicit handle() calls, with no queue (tests/test_jobs_queue.py adds one). The tests
run on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import time
from pathlib import Path

import pytest

from etf_risk.jobs import faults
from etf_risk.jobs.events import EventLog, read_events
from etf_risk.jobs.simulated import SimulatedCrash, SimulatedPipeline
from etf_risk.jobs.store import Outcome, Refusal, Status
from etf_risk.jobs.worker import WORKER_FAULT_POINTS, PipelineError, Result
from jobs_backends import BACKENDS, LEASE, WorkerEnv, make_backend, run_together


@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = WorkerEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


def submit(env, **kwargs) -> int:
    return env.admin.submit({"snapshot": "simulated", "stride": 21}, {"windows.parquet": "0" * 64}, **kwargs)


def crash_at(point):
    assert point in WORKER_FAULT_POINTS

    def fault(at):
        if at == point:
            raise SimulatedCrash(point)
    return fault


def test_a_delivery_runs_the_job_once_and_accepts_its_result(env):
    job = submit(env)
    pipeline = SimulatedPipeline()
    handled = env.deliver(env.worker("A", pipeline), job)
    assert handled.result is Result.ACCEPTED and handled.claim.run_id == f"job-{job}-attempt-1"
    assert pipeline.runs == [f"job-{job}-attempt-1"] and env.acks == [job]
    assert (handled.claim.output_dir / "steps.log").read_text() == "step 1\nstep 2\nstep 3\n"
    assert env.admin.attempts(job)[0]["renewals"] == 3              # one heartbeat per step
    env.check(job)


# Duplicate and concurrent deliveries

def test_a_duplicate_delivery_after_success_is_skipped(env):
    job = submit(env)
    first, second = SimulatedPipeline(), SimulatedPipeline()
    env.deliver(env.worker("A", first), job)
    handled = env.deliver(env.worker("B", second), job)
    assert (handled.result, handled.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)
    assert len(first.runs) + len(second.runs) == 1 and env.acks == [job, job]
    env.check(job)


def test_a_duplicate_delivery_during_a_live_run_is_skipped(env):
    job = submit(env)
    b = env.worker("B")
    during = []

    def deliver_again(step, claim):
        if step == 2:
            during.append(env.deliver(b, job))

    env.deliver(env.worker("A", SimulatedPipeline(on_step=deliver_again)), job)
    assert [(h.result, h.reason) for h in during] == [(Result.SKIPPED, Refusal.LEASE_HELD)]
    assert b.pipeline.runs == [] and env.acks == [job, job]
    assert env.handled[-1].result is Result.ACCEPTED                # A's delivery, recorded after B's
    env.check(job)


def test_a_requeued_job_delivered_twice_is_claimed_once(env):
    job = submit(env)
    assert env.deliver(env.worker("A", SimulatedPipeline(fail_at={1: True})), job).result is Result.REQUEUED
    c = env.worker("C")
    during = []

    def deliver_again(step, claim):
        if step == 1:
            during.append(env.deliver(c, job))

    assert env.deliver(env.worker("B", SimulatedPipeline(on_step=deliver_again)), job).result is Result.ACCEPTED
    assert [(h.result, h.reason) for h in during] == [(Result.SKIPPED, Refusal.LEASE_HELD)]
    assert c.pipeline.runs == [] and env.admin.job(job)["accepted_attempt"] == 2
    env.check(job)


def test_concurrent_deliveries_of_one_job_run_it_once(env):
    """Four workers, each with a connection of its own, handle the same job id at the same moment."""
    job = submit(env)
    pipelines = [SimulatedPipeline() for _ in range(4)]
    workers = [env.worker(name, pipeline) for name, pipeline in zip("ABCD", pipelines)]
    results = run_together(*(lambda worker=worker: env.deliver(worker, job) for worker in workers))
    assert [h.result for h in results].count(Result.ACCEPTED) == 1
    assert all(h.result is Result.SKIPPED and h.reason in (Refusal.LEASE_HELD, Refusal.SUCCEEDED)
               for h in results if h.result is not Result.ACCEPTED)
    assert sum(len(p.runs) for p in pipelines) == 1 and env.acks == [job] * 4
    env.check(job)


# Crashes

def test_a_crash_before_the_claim_leaves_the_job_queued(env):
    job = submit(env)
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", fault=crash_at("before_claim")), job)
    assert env.admin.job(job)["status"] is Status.QUEUED and env.admin.attempts(job) == [] and env.acks == []
    assert env.deliver(env.worker("B"), job).result is Result.ACCEPTED   # the unacknowledged delivery again
    env.check(job)


def test_a_crash_between_claim_and_acknowledgement(env):
    job = submit(env)
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", fault=crash_at("after_claim")), job)
    assert env.acks == []                                           # not acknowledged: delivered again
    again = env.deliver(env.worker("B"), job)
    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.LEASE_HELD)
    assert env.acks == [job]                                        # acknowledged: no delivery is pending
    env.clock.advance(LEASE.total_seconds())                        # A's lease runs out ...
    assert env.admin.job(job)["status"] is Status.RUNNING          # ... and nothing happens by itself
    handled = env.deliver(env.worker("C"), job)                     # a new delivery (later: the reconciler's)
    assert handled.result is Result.ACCEPTED and handled.claim.attempt_number == 2
    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    assert not (env.runs / f"job-{job}-attempt-1").exists()        # A died before creating its folder
    env.check(job)


def test_a_crash_in_the_middle_of_the_run(env):
    job = submit(env)

    def die(step, claim):
        if step == 2:
            raise SimulatedCrash("the worker died mid-run")

    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", SimulatedPipeline(on_step=die)), job)
    assert (env.runs / f"job-{job}-attempt-1" / "steps.log").read_text() == "step 1\n"
    assert env.admin.job(job)["status"] is Status.RUNNING
    env.clock.advance(LEASE.total_seconds())
    assert env.deliver(env.worker("B"), job).result is Result.ACCEPTED
    env.check(job)


def test_a_crash_after_the_pipeline_loses_only_that_attempt(env):
    job = submit(env)
    first, second = SimulatedPipeline(), SimulatedPipeline()
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", first, fault=crash_at("after_pipeline")), job)
    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # complete, never accepted
    env.clock.advance(LEASE.total_seconds())
    handled = env.deliver(env.worker("B", second), job)
    assert handled.result is Result.ACCEPTED and env.admin.job(job)["accepted_attempt"] == 2
    assert len(first.runs) + len(second.runs) == 2                  # executed twice, accepted once
    env.check(job)


def test_a_crash_after_acceptance_keeps_the_one_result(env):
    job = submit(env)
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", fault=crash_at("after_accept")), job)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    again = env.deliver(env.worker("B"), job)
    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)
    env.check(job, lost_acceptances=1)                              # A died before it could tell


def test_a_crash_between_the_acceptance_commit_and_its_event_leaves_the_result_unreported(env, tmp_path):
    """Recovery case W5a: the table holds one accepted result and the log has no accepted event."""
    job = submit(env)
    worker = env.worker("A", fault=crash_at("after_accept_commit"))
    worker.events = EventLog(tmp_path / "A.jsonl", "worker", worker_id="worker-A")
    with pytest.raises(SimulatedCrash):
        env.deliver(worker, job)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.ACCEPTED]
    assert [e["event"] for e in read_events(tmp_path / "A.jsonl")] == ["claimed"]   # no accepted event
    env.check(job, lost_acceptances=1)


# Expired leases and stale workers

def test_an_expired_lease_mid_run_fences_the_slow_worker(env):
    job = submit(env)
    b = env.worker("B")
    taken_over = []

    def stall_then_lose_the_job(step, claim):
        if step == 2:                                               # A stalls past its lease, B takes over
            env.clock.advance(LEASE.total_seconds() + 1)
            taken_over.append(env.deliver(b, job))

    handled = env.deliver(env.worker("A", SimulatedPipeline(on_step=stall_then_lose_the_job)), job)
    assert [h.result for h in taken_over] == [Result.ACCEPTED]
    assert handled.result is Result.FENCED                          # A's next heartbeat was refused
    a_dir = env.runs / f"job-{job}-attempt-1"
    assert (a_dir / "steps.log").read_text() == "step 1\n" and not (a_dir / "result.json").exists()
    assert env.admin.job(job)["accepted_attempt"] == 2
    env.check(job)


def test_an_expired_lease_without_a_takeover_lets_the_worker_finish(env):
    job = submit(env)

    def stall(step, claim):
        if step == 2:
            env.clock.advance(3 * LEASE.total_seconds())            # long past the lease, but nobody takes over

    assert env.deliver(env.worker("A", SimulatedPipeline(on_step=stall)), job).result is Result.ACCEPTED
    env.check(job)


def test_a_stale_worker_cannot_get_its_result_accepted(env):
    job = submit(env)
    b = env.worker("B")
    taken_over = []

    def lose_the_job(point):
        if point == "after_pipeline":                               # A finished too late: B takes over
            env.clock.advance(LEASE.total_seconds())
            taken_over.append(env.deliver(b, job))

    handled = env.deliver(env.worker("A", fault=lose_the_job), job)
    assert [h.result for h in taken_over] == [Result.ACCEPTED] and handled.result is Result.FENCED
    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # A's folder stays, unreferenced
    assert env.admin.job(job)["accepted_attempt"] == 2
    env.check(job)


def test_a_stale_worker_cannot_record_a_failure(env):
    job = submit(env)
    b = env.worker("B")
    taken_over = []

    def lose_the_job_then_fail(step, claim):
        if step == 2:                                               # B takes over and finishes; then A fails
            env.clock.advance(LEASE.total_seconds() + 1)            # before any heartbeat could tell it
            taken_over.append(env.deliver(b, job))
            raise PipelineError("failed after losing the job")

    handled = env.deliver(env.worker("A", SimulatedPipeline(on_step=lose_the_job_then_fail)), job)
    assert [h.result for h in taken_over] == [Result.ACCEPTED] and handled.result is Result.FENCED
    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    env.check(job)


# The deadline F at acceptance

class DeadlinePipeline(SimulatedPipeline):
    """A simulated pipeline that keeps a deadline as SubprocessPipeline does: fence_at, on
    time.monotonic(), set `left` seconds ahead when its run returns (negative: already passed)."""

    def __init__(self, left: float, **kwargs):
        super().__init__(**kwargs)
        self.left, self.fence_at = left, None

    def run(self, claim, run_dir, heartbeat):
        digest = super().run(claim, run_dir, heartbeat)
        self.fence_at = time.monotonic() + self.left
        return digest


def test_no_acceptance_call_once_the_deadline_has_passed(env, tmp_path):
    """docs/worker-pipeline.md: the worker never accepts after F, even while its token still holds
    the job. The job runs again once its lease has expired."""
    job = submit(env)
    worker = env.worker("A", DeadlinePipeline(left=-1.0))
    worker.events = EventLog(tmp_path / "A.jsonl", "worker", worker_id="worker-A")
    calls = []
    accept = worker.store.accept_result
    worker.store.accept_result = lambda *args: calls.append(args) or accept(*args)
    assert env.deliver(worker, job).result is Result.FENCED and calls == []          # not even one call
    j = env.admin.job(job)
    assert (j["status"], j["attempt_number"]) == (Status.RUNNING, 1)              # the token still holds it
    fenced = read_events(tmp_path / "A.jsonl")[-1]
    assert (fenced["event"], fenced["during"]) == ("fenced", "acceptance")
    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()           # complete, never accepted
    env.clock.advance(LEASE.total_seconds())
    again = env.deliver(env.worker("B"), job)
    assert again.result is Result.ACCEPTED and again.claim.attempt_number == 2
    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    env.check(job)


def test_acceptance_before_the_deadline_goes_ahead(env):
    job = submit(env)
    assert env.deliver(env.worker("A", DeadlinePipeline(left=60.0)), job).result is Result.ACCEPTED
    env.check(job)


def test_a_hold_released_after_the_deadline_ends_without_acceptance(env, tmp_path):
    """Case D2's hook (etf_risk.jobs.faults) holds at after_pipeline until its release file
    appears, here only once F has passed: the worker then fences itself."""
    job = submit(env)
    pipeline = DeadlinePipeline(left=0.05)
    log = tmp_path / "A.jsonl"
    events = EventLog(log, "worker", worker_id="worker-A")
    release = tmp_path / "release"

    def sleep(seconds):                                             # the harness releases only after F
        time.sleep(0.01)
        if time.monotonic() >= pipeline.fence_at:
            release.touch()

    hook = faults.FaultFile(tmp_path / "A.fault", events, sleep=sleep)
    faults.arm(hook.path, "after_pipeline", "hold", release=release, timeout_s=60)
    worker = env.worker("A", pipeline, fault=hook)
    worker.events = events
    assert env.deliver(worker, job).result is Result.FENCED
    assert [e["event"] for e in read_events(log)] == ["claimed", "fault_injected", "fault_released", "fenced"]
    assert env.admin.attempts(job)[0]["outcome"] is Outcome.RUNNING
    env.check(job)


class LosesConnections:
    """A store's dialect, except that ConnectionResetError counts as a lost connection, which
    SQLite never reports."""

    def __init__(self, dialect):
        self._dialect = dialect

    def __getattr__(self, name):
        return getattr(self._dialect, name)

    def is_disconnect(self, error):
        return isinstance(error, ConnectionResetError)


def losing(worker, times):
    """Make the worker's first `times` acceptance calls lose their connection; the calls' start times."""
    worker.store.dialect = LosesConnections(worker.store.dialect)
    calls, accept = [], worker.store.accept_result

    def accept_result(*args):
        calls.append(time.monotonic())
        if len(calls) <= times:
            raise ConnectionResetError("the database went away")
        return accept(*args)

    worker.store.accept_result = accept_result
    return calls


def test_a_lost_connection_at_acceptance_is_tried_again_while_the_deadline_is_ahead(env, tmp_path):
    job = submit(env)
    worker = env.worker("A", DeadlinePipeline(left=60.0))
    worker.events = EventLog(tmp_path / "A.jsonl", "worker", worker_id="worker-A")
    worker._sleep = lambda seconds: None
    calls = losing(worker, times=2)
    assert env.deliver(worker, job).result is Result.ACCEPTED and len(calls) == 3
    assert [e["operation"] for e in read_events(tmp_path / "A.jsonl") if e["event"] == "retry"] == ["accept_result"] * 2
    env.check(job)


def test_no_acceptance_try_starts_once_the_deadline_passed_during_the_wait(env):
    """A try started before F may still be under way after it; a new one never starts after F."""
    job = submit(env)
    pipeline = DeadlinePipeline(left=0.3)
    worker = env.worker("A", pipeline)
    worker._sleep = lambda seconds: time.sleep(max(0.0, pipeline.fence_at - time.monotonic()) + 0.01)
    calls = losing(worker, times=10)
    with pytest.raises(ConnectionResetError):                        # serve() logs failed_after_ack
        env.deliver(worker, job)
    assert len(calls) == 1 and calls[0] < pipeline.fence_at
    assert env.admin.job(job)["status"] is Status.RUNNING           # left to its lease
    env.check(job)


def test_a_fault_armed_while_the_worker_runs_fires_without_a_restart(env, tmp_path):
    """The harness arms a running worker (outline 8.4): the same Worker and hook handle one job
    untouched, are armed, and die at the armed point of the next job."""
    first, second = submit(env), submit(env)
    log = tmp_path / "A.jsonl"
    events = EventLog(log, "worker", worker_id="worker-A")

    def kill():
        raise SimulatedCrash("SIGKILL")

    hook = faults.FaultFile(tmp_path / "A.fault", events, kill=kill)
    worker = env.worker("A", fault=hook)
    worker.events = events
    assert env.deliver(worker, first).result is Result.ACCEPTED
    faults.arm(hook.path, "after_claim")
    with pytest.raises(SimulatedCrash):
        env.deliver(worker, second)
    assert [e["event"] for e in read_events(log)] == ["claimed", "accepted", "claimed", "fault_injected"]
    assert env.acks == [first] and not hook.path.exists()          # never acknowledged; the fault fired once
    env.check(first)
    env.check(second)


# Failures and retries

def test_a_retryable_failure_is_not_delivered_again_by_itself(env):
    job = submit(env)
    handled = env.deliver(env.worker("A", SimulatedPipeline(fail_at={2: True})), job)
    assert handled.result is Result.REQUEUED and env.acks == [job]
    env.clock.advance(3600)
    j = env.admin.job(job)
    assert (j["status"], j["attempt_number"]) == (Status.QUEUED, 1)   # still waiting: nothing delivers it
    handled = env.deliver(env.worker("B"), job)                     # an explicit delivery (later: the reconciler's)
    assert handled.result is Result.ACCEPTED and handled.claim.attempt_number == 2
    assert [(a["outcome"], a["error"]) for a in env.admin.attempts(job)] == [
        (Outcome.FAILED, "injected failure at step 2"), (Outcome.ACCEPTED, None)]
    env.check(job)


def test_retries_end_when_attempts_run_out(env):
    job = submit(env, max_attempts=3)
    results = [env.deliver(env.worker(name, SimulatedPipeline(fail_at={1: True})), job).result for name in "ABC"]
    assert results == [Result.REQUEUED, Result.REQUEUED, Result.FAILED]
    again = env.deliver(env.worker("D"), job)
    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.FAILED)
    attempts = env.admin.attempts(job)
    assert [a["outcome"] for a in attempts] == [Outcome.FAILED] * 3
    assert all(Path(a["output_dir"]).is_dir() for a in attempts)  # three attempts, three folders
    env.check(job)


def test_a_permanent_failure_fails_the_job(env):
    job = submit(env)
    assert env.deliver(env.worker("A", SimulatedPipeline(fail_at={1: False})), job).result is Result.FAILED
    again = env.deliver(env.worker("B"), job)
    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.FAILED)
    assert env.admin.job(job)["error"] == "injected failure at step 1"
    env.check(job)


def test_an_unexpected_pipeline_error_counts_as_a_retryable_failure(env):
    job = submit(env)

    def bug(step, claim):
        raise ValueError("bug in the pipeline")

    assert env.deliver(env.worker("A", SimulatedPipeline(on_step=bug)), job).result is Result.REQUEUED
    assert env.admin.attempts(job)[0]["error"] == "ValueError: bug in the pipeline"
    env.check(job)


def test_an_existing_output_folder_is_never_written_into(env):
    job = submit(env)
    folder = env.runs / f"job-{job}-attempt-1"
    folder.mkdir(parents=True)
    (folder / "marker").write_text("left by another job table")
    pipeline = SimulatedPipeline()
    assert env.deliver(env.worker("A", pipeline), job).result is Result.FAILED
    assert pipeline.runs == [] and [p.name for p in folder.iterdir()] == ["marker"]
    assert "output folder already exists" in env.admin.job(job)["error"]
    env.check(job)


def test_acknowledgement_comes_after_the_claim(env):
    job = submit(env)
    events = []
    worker = env.worker("A", fault=events.append)
    env.handled.append(worker.handle(job, lambda: events.append("acknowledge")))
    assert events == ["before_claim", "after_claim", "acknowledge", "after_pipeline", "after_accept_commit",
                      "after_accept"]
    events.clear()
    env.handled.append(worker.handle(job, lambda: events.append("acknowledge")))   # refused: at once
    assert events == ["before_claim", "acknowledge"]
    env.check(job)
