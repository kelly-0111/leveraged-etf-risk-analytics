# Claude Code message 25

Session: `a9a2be5c-8da0-4ec5-be57-f251b5676fe9` · prompt sent 2026-10-24 23:19 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): email ×1, git-user ×93, home ×504, memory ×19, model-reasoning ×24, user ×32. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-25T04:19:10.185Z

Before final approval, make the collector exit status consistent with its verdicts: any required check that is failed or unknown must produce a nonzero exit. Add a focused regression test. Then present one compact table of all remaining Part A decisions, with the exact proposed values and their rationale, so I can approve them together. Keep the documents uncommitted until that review. Do not run the formal batch, publish a page, or commit AI logs.

## 2. Assistant — 2026-10-25T04:21:22.090Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Check the memory pointer and read the collector's verdict and exit code"
}
```

## 3. User — 2026-10-25T04:21:23.392Z

### Tool result

```
[REDACTED:memory]
```

## 4. Assistant — 2026-10-25T04:22:09.567Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; grep -n \"^def \\|^@pytest\\|main(\\[\" $W/tests/test_recovery_collector.py | cut -c1-150; grep -n \"validity_failed\\|FAILED\\|validity:\" $W/tests/*.py | cut -c1-150",
  "description": "List the collector tests and any checks on its printed output"
}
```

## 5. User — 2026-10-25T04:22:10.471Z

### Tool result

```
30:def utc(mono):
34:def write_jsonl(path, events):
39:def launcher(folder, step, start, end, *, mono=True):
48:def edit_harness(batch, change):
54:def write_csv(path, header, rows):
62:def host_reading(stage, position=None, *, power="AC Power", lid_closed=False):
70:def make_batch(tmp_path, *, step_code=CODE, host=True):
179:@pytest.fixture
180:def batch(tmp_path):
184:def test_the_metrics_of_each_job_with_their_reasons(batch, tmp_path):
198:def test_validity_passes_and_outcomes_stay_apart(batch, tmp_path):
208:def test_the_tally_lists_every_case_and_every_verdict_with_zeros(batch, tmp_path):
216:def test_a_missing_launcher_record_makes_the_overlap_unknown_never_none(batch, tmp_path):
224:def test_overlapping_steps_are_found(batch, tmp_path):
229:def test_a_step_that_ran_other_code_fails_validity_and_the_exit_code(tmp_path):
231:    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
237:def test_a_launcher_record_without_monotonic_times_counts_as_missing(batch, tmp_path):
246:def test_every_interval_that_overlaps_an_earlier_one_is_listed(batch, tmp_path):
256:def test_an_injection_record_without_its_time_leaves_its_latencies_unknown(batch, tmp_path):
269:def test_a_job_without_its_injection_record_is_counted_apart_never_as_made(batch, tmp_path):
281:def test_d2_is_detected_by_its_retried_acceptance_or_by_no_acceptance_after_f(batch, tmp_path):
303:def test_the_purpose_comes_from_the_plan_and_heads_every_summary(batch, tmp_path, capsys):
307:    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 0
312:def test_host_memory_spark_scratch_and_the_cleanup_listing_are_reported(tmp_path):
329:def test_a_recorded_setup_or_final_error_fails_validity(batch, tmp_path):
332:    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
338:def test_the_host_state_gives_each_job_its_swap_activity_power_and_pressure(tmp_path):
367:def set_reading(batch, where, **fields):
376:def test_a_reading_on_battery_fails_the_recovery_times_but_not_the_correctness(batch, tmp_path):
382:    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
385:def test_a_closed_lid_fails_the_recovery_times(batch, tmp_path):
392:def test_a_missing_reading_or_value_is_unknown_and_never_passes(batch, tmp_path):
402:def test_a_batch_from_before_the_power_readings_has_unknown_conditions(tmp_path):
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/mutation_check.py:412:    failed = next((line for line in output.
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_live_pipeline.py:203:    return j if j["status"] in (St
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_live_pipeline.py:370:        assert j["status"] is Stat
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_mysql.py:94:    assert store.requeue_expired(lapsing, s
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_reconciler.py:75:    assert env.admin.requeue_expired(j
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_reconciler.py:77:    assert j["status"] is Status.FAILE
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_reconciler.py:116:    assert env.admin.requeue_expired(
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:76:    assert env.store.fail_attempt(a, "perma
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:134:    ("expired_last", "claim"): (Refusal.EX
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:137:    ("expired_last", "fail"): (Status.FAIL
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:140:    ("expired_last", "requeue_expired"): (
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:148:    ("failed", "claim"): (Refusal.FAILED, 
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:264:    assert j["status"] is Status.FAILED an
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:266:    assert env.store.claim(job, "worker-D"
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:277:    assert env.store.fail_attempt(b, "tran
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:279:    assert (j["status"], j["error"]) == (S
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_store.py:281:        (Outcome.FAILED, "transient 1"), (
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:418:        (Outcome.FAILED, "injected failur
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:425:    assert results == [Result.REQUEUED, R
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:427:    assert (again.result, again.reason) =
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:429:    assert [a["outcome"] for a in attempt
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:436:    assert env.deliver(env.worker("A", Si
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:438:    assert (again.result, again.reason) =
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py:460:    assert env.deliver(env.worker("A", pi
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py:200:    assert result["validity_failed
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py:233:    assert validity["validity_fail
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py:334:    assert "records_complete" in v
~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py:483:    assert (result["purpose"], res
```

## 6. Assistant — 2026-10-25T04:22:15.415Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; sed -n 1,29p $W/tests/test_recovery_collector.py; echo ...; sed -n 176,236p $W/tests/test_recovery_collector.py; echo ...; sed -n 326,336p $W/tests/test_recovery_collector.py; echo ...; sed -n 360,420p $W/tests/test_recovery_collector.py; echo ...; sed -n 478,490p $W/tests/test_recovery_synthetic.py",
  "description": "Read the collector test helpers and the related tests"
}
```

## 7. User — 2026-10-25T04:22:16.212Z

### Tool result

```
"""The recovery collector (analysis/collect_recovery_measurements.py) on synthetic batch folders:
the metrics of section 5 with their n/a reasons, unknown intervals, the per-case tally with
zeros, and validity apart from outcomes. No real batch exists yet.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import csv
import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk.jobs.params import input_checksums

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("collect_recovery_measurements",
                                              REPO / "analysis" / "collect_recovery_measurements.py")
crm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crm)

BASE = datetime(2026, 10, 24, 10, 0, 0, tzinfo=timezone.utc)
STORE = "s" * 32
CODE = {"source_digest": "c" * 64, "uv_lock_sha256": "u" * 64}


...
    return b


@pytest.fixture
def batch(tmp_path):
    return make_batch(tmp_path)


def test_the_metrics_of_each_job_with_their_reasons(batch, tmp_path):
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    rows = {r["position"]: r for r in result["rows"]}
    assert result["c0_median_s"] == 40.0
    c0, w3, w5a, k2 = rows[1], rows[2], rows[3], rows[4]
    assert (c0["detection_s"], c0["rerun_s"], c0["finish_s"], c0["overhead_s"]) == (
        "n/a: no failure", "n/a: no failure", 40.0, 0.0)
    assert (w3["detection_s"], w3["rerun_s"], w3["finish_s"], w3["overhead_s"]) == (55.0, 60.0, 105.0, 85.0)
    assert (w3["claims"], w3["executions"], w3["complete_executions"], w3["wasted_step_s"]) == ("2", 2, 1, 19.0)
    assert (w5a["detection_s"], w5a["finish_s"], w5a["q3a_verdict"]) == (
        "n/a: after acceptance", "n/a: after acceptance", "no matching report")
    assert k2 == {"position": 4, "case": "K2", "status": "not run"}


def test_validity_passes_and_outcomes_stay_apart(batch, tmp_path):
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity_failed"] == []
    assert result["verdicts"] == {"correctness": {"valid": True, "failed": []}, "timing": {"valid": True, "failed": []}}
    assert result["outcomes"]["overlap"]["verdict"] == "no overlap"
    assert result["outcomes"]["q1_not_ok"] == [] and result["outcomes"]["invariant_violations"] == {}
    accepted = {a["job_id"]: a["problems"] for a in result["outcomes"]["accepted_attempts"]}
    assert accepted[1] == ["no readable attempt.json"]                           # an outcome finding, not validity


def test_the_tally_lists_every_case_and_every_verdict_with_zeros(batch, tmp_path):
    tally = {t["case"]: t for t in crm.collect(batch, processed_root=tmp_path / "processed")["tally"]}
    assert set(tally) == set(crm.CASES)
    assert (tally["W3"]["planned"], tally["W3"]["made"], tally["K2"]["not_run"], tally["X1"]["planned"]) == (1, 1, 1, 0)
    assert tally["W5a"]["q3a: no matching report"] == 1 and tally["C0"]["q2: late"] == 0
    assert all(f"q1: {v}" in tally["D2"] for v in crm.Q1_VERDICTS)


def test_a_missing_launcher_record_makes_the_overlap_unknown_never_none(batch, tmp_path):
    (batch / "jobs" / STORE / "job-2-attempt-1" / "logs" / "spark_pipeline.launcher.json").unlink()
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    overlap = result["outcomes"]["overlap"]
    assert overlap["verdict"] == "unknown" and overlap["steps_without_interval"] == ["job-2-attempt-1:spark_pipeline"]
    assert str({r["position"]: r for r in result["rows"]}[2]["wasted_step_s"]).startswith("unknown")


def test_overlapping_steps_are_found(batch, tmp_path):
    launcher(batch / "jobs" / STORE / "job-2-attempt-2", "windows", 1119, 1184)    # starts before 1121
    assert crm.collect(batch, processed_root=tmp_path / "processed")["outcomes"]["overlap"]["verdict"] == "overlap"


def test_a_step_that_ran_other_code_fails_validity_and_the_exit_code(tmp_path):
    batch = make_batch(tmp_path, step_code={**CODE, "source_digest": "x" * 64})
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
    validity = json.loads((batch / "validity.json").read_text())
    assert validity["validity_failed"] == ["code_identity"] and validity["validity"]["code_identity"]["distinct"] == 2
    assert (batch / "injections.csv").exists() and (batch / "tally.csv").exists()


...
    assert result["outcomes"]["cleanup_listing"] == "cleanup.txt"


def test_a_recorded_setup_or_final_error_fails_validity(batch, tmp_path):
    with open(batch / "harness.jsonl", "a") as f:
        f.write(json.dumps({"event": "setup_error", "error": "RuntimeError: init-db: exit 1"}) + "\n")
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
    validity = json.loads((batch / "validity.json").read_text())
    assert "records_complete" in validity["validity_failed"]
    assert validity["validity"]["records_complete"]["setup_errors"] == ["RuntimeError: init-db: exit 1"]

...
        "jobs_with_a_reading": 3, "power_sources": ["AC Power", "Battery Power"], "on_battery": [2], "lid_closed": [2],
        "max_memory_pressure": 4, "min_available_bytes": 2 * gib, "swap_used_change_bytes": 80 * mib,
        "swap_out_batch_bytes": 80 * mib, "swap_in_batch_bytes": 0}


# The host protocol's timing conditions (docs/recovery-part-a.md, section 12)

def set_reading(batch, where, **fields):
    """Change the host_state reading at a position, or at "start" or "end"."""
    def change(e):
        if e["event"] == "host_state" and (e.get("position") == where or e["stage"] == where):
            return {**e, **fields}
        return e
    edit_harness(batch, change)


def test_a_reading_on_battery_fails_the_recovery_times_but_not_the_correctness(batch, tmp_path):
    set_reading(batch, 2, power_source="Battery Power")
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["host_power"] == {"passed": False, "failed": [2], "unknown": []}
    assert result["verdicts"] == {"correctness": {"valid": True, "failed": []},
                                  "timing": {"valid": False, "failed": ["host_power"]}}
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1


def test_a_closed_lid_fails_the_recovery_times(batch, tmp_path):
    set_reading(batch, "end", lid_closed=True)
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["host_lid"] == {"passed": False, "failed": ["end"], "unknown": []}
    assert result["verdicts"]["timing"] == {"valid": False, "failed": ["host_lid"]}


def test_a_missing_reading_or_value_is_unknown_and_never_passes(batch, tmp_path):
    set_reading(batch, "start", power_source=None)                       # a reading without its power source
    edit_harness(batch, lambda e: None if e["event"] == "host_state" and e.get("position") == 3 else e)   # none at all
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["host_power"] == {"passed": False, "failed": [], "unknown": ["start", 3]}
    assert result["validity"]["host_lid"] == {"passed": False, "failed": [], "unknown": [3]}
    assert result["verdicts"]["timing"] == {"valid": False, "failed": ["host_power", "host_lid"]}
    assert result["verdicts"]["correctness"]["valid"] is True


def test_a_batch_from_before_the_power_readings_has_unknown_conditions(tmp_path):
    """Memory-only readings, as preflight-2 and -3 recorded them, say nothing of power or the lid."""
    batch = make_batch(tmp_path, host=False)
    with open(batch / "harness.jsonl", "a") as f:
        for position in (1, 2, 3):
            f.write(json.dumps({"event": "host_memory", "position": position, "available_bytes": 2**30}) + "\n")
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["host_power"]["unknown"] == ["start", 1, 2, 3, "end"]
    assert result["verdicts"]["timing"]["valid"] is False and result["verdicts"]["correctness"]["valid"] is True
...
        assert [e for w in logs for e in logs[w]
                if e["event"] == "assigned" and armed["mono"] < e["mono"] < injection["t_inj"]] == []

    assert crm.main(["--batch", str(batch.out), "--processed-root", str(processed)]) == 0
    result = crm.collect(batch.out, processed_root=processed)
    assert (result["purpose"], result["validity_failed"]) == ("preflight", [])
    assert result["validity"]["records_complete"] == {"passed": True, "setup_errors": [], "final_errors": []}
    assert result["verdicts"] == {"correctness": {"valid": True, "failed": []}, "timing": {"valid": True, "failed": []}}
    rows = {r["position"]: r for r in result["rows"]}
    assert [rows[p]["status"] for p in rows] == ["made"] * 9
    assert [rows[p]["q1_verdict"] for p in rows] == ["ok"] * 9
    assert [rows[p]["timeliness"] for p in rows] == ["on time"] * 4 + ["late"] + ["on time"] * 3 + [
        "deadline not observed"]
```

## 8. Assistant — 2026-10-25T04:22:54.636Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; grep -n \"battery-passes\\|timing-verdict-without-host\\|unknown-reading-passes\" -A 4 $W/tests/mutation_check.py | cut -c1-170; grep -n \"^COLLECTOR\\|^HARNESS\\|^FOCUSED\\|^def \\|^[A-Z_]* = \" $W/tests/mutation_check.py | head -30",
  "description": "Read how the focused collector mutations are defined"
}
```

## 9. User — 2026-10-25T04:22:55.654Z

### Tool result

```
355:    Mutation("battery-passes", COLLECTOR, 'condition("power_source", lambda value: value != "AC Power")',
356-             'condition("power_source", lambda value: False)', "a reading on battery passes the power condition",
357-             tests=COLLECTOR_TESTS),
358-    Mutation("lid-closed-passes", COLLECTOR, 'condition("lid_closed", lambda value: value is not False)',
359-             'condition("lid_closed", lambda value: False)', "a closed lid passes the lid condition",
--
361:    Mutation("unknown-reading-passes", COLLECTOR,
362-             '        return {"passed": not failed and not unknown, "failed": failed, "unknown": unknown}',
363-             '        return {"passed": not failed, "failed": failed, "unknown": unknown}',
364-             "a missing reading or value passes silently", tests=COLLECTOR_TESTS),
365:    Mutation("timing-verdict-without-host", COLLECTOR,
366-             'TIMING_CHECKS = (*CORRECTNESS_CHECKS, "clock", "host_power", "host_lid")',
367-             'TIMING_CHECKS = (*CORRECTNESS_CHECKS, "clock")', "recovery times count on battery or with the lid closed",
368-             tests=COLLECTOR_TESTS),
369-    Mutation("end-reading-not-required", COLLECTOR,
54:REPO = Path(__file__).resolve().parents[1]
58:COPIED = ("src", "tests", "analysis", "docs/recovery-sql.md", "pyproject.toml", "uv.lock")
59:JOB_TESTS = ("tests/test_jobs_store.py", "tests/test_jobs_reconnect.py", "tests/test_jobs_worker.py",
63:NEEDS = {"mysql": "ETF_RISK_MYSQL_URL", "kafka": "ETF_RISK_KAFKA_BOOTSTRAP"}
66:TIMING = "src/etf_risk/jobs/timing.py"
68:PIPELINE = "src/etf_risk/jobs/pipeline.py"
73:COLLECTOR_TESTS, SQL_TESTS = ("tests/test_recovery_collector.py",), ("tests/test_recovery_sql.py",)
74:SYNTHETIC_TESTS = ("tests/test_recovery_synthetic.py",)
88:def removing(id: str, file: str, context: str, piece: str, breaks: str, needs: tuple[str, ...] = (),
95:_RENEW = ("updated_at = :now\"\n                    \" WHERE job_id = :job_id AND status = 'running'"
97:_ACCEPT = ("'running' AND attempt_token = :token\",\n                    job_id=claim.job_id, token=claim.token,"
99:_FAIL = ("'running' AND attempt_token = :token\",\n                    job_id=claim.job_id, token=claim.token,"
101:_TAKEOVER = ("status = 'running' AND lease_expires_at <= :now\"\n                    \" AND attempt_number <"
103:_REQUEUE = ("'running' AND attempt_token = :token\"\n                    \" AND lease_expires_at <= :now AND"
105:_EXHAUST = ("'running' AND attempt_token = :token\"\n                \" AND lease_expires_at <= :now AND"
107:_CLAIM = ("published_at = NULL,\"\n                    \" version = version + 1, updated_at = :now\"\n"
109:_REPEAT = ("a.attempt_token = :token\"\n                \" AND a.result_digest = :digest\",")
110:_IN_TRANSACTION = ("        if self._in_transaction:                         # inside a transaction: this connection or none\n"
114:_IN_TRANSACTION_RETRY = ("        if self._in_transaction:\n"
125:MUTATIONS = (
379:def make_scratch() -> Path:
395:def run_tests(scratch: Path, timeout: float, tests: tuple[str, ...] | list[str] = JOB_TESTS) -> dict:
417:def outcome(result: dict) -> str:
421:def main(argv: list[str] | None = None) -> int:
```

## 10. Assistant — 2026-10-25T04:23:00.300Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; grep -n \"CORRECTNESS_CHECKS\\|TIMING_CHECKS\" $W/analysis/collect_recovery_measurements.py | cut -c1-160; sed -n 369,378p $W/tests/mutation_check.py",
  "description": "Locate the check lists and the last collector mutation"
}
```

## 11. User — 2026-10-25T04:23:01.007Z

### Tool result

```
77:CORRECTNESS_CHECKS = ("code_identity", "fingerprints_agree", "inputs_unchanged", "records_complete")
78:TIMING_CHECKS = (*CORRECTNESS_CHECKS, "clock", "host_power", "host_lid")
498:    verdicts = {"correctness": verdict(validity, CORRECTNESS_CHECKS), "timing": verdict(validity, TIMING_CHECKS)}
    Mutation("end-reading-not-required", COLLECTOR,
             '    readings = [("start", start), *[(position, host.get(position)) for position in ran], ("end", end)]',
             '    readings = [("start", start), *[(position, host.get(position)) for position in ran]]',
             "the batch's end reading is not checked", tests=COLLECTOR_TESTS),
    Mutation("legacy-host-memory-ignored", COLLECTOR,
             '    readings = {e["position"]: e for e in named(b.harness, "host_memory")}',
             "    readings = {}", "the memory readings of earlier batches are no longer read", tests=COLLECTOR_TESTS),
)
```

## 12. Assistant — 2026-10-25T04:23:04.238Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; sed -n 74,80p $W/analysis/collect_recovery_measurements.py",
  "description": "Read the comment above the check lists"
}
```

## 13. User — 2026-10-25T04:23:05.019Z

### Tool result

```
Q3B_VERDICTS = ("matches", "other store", "no such attempt", "wrong worker", "attempt not accepted", "wrong digest")
NOT_RUN = ("not run", "not submitted")
UNRECORDED = ("no record", "no injection record")     # the harness's records lack the job's deadline or injection
CORRECTNESS_CHECKS = ("code_identity", "fingerprints_agree", "inputs_unchanged", "records_complete")
TIMING_CHECKS = (*CORRECTNESS_CHECKS, "clock", "host_power", "host_lid")
LIVENESS = ("serve_restarted", "retry", "rewound", "gave_up", "failed_after_ack", "consumer_error", "pass_failed")
FIELDS = ["position", "case", "job_id", "status", "missed", "injection", "worker", "t_inj", "reference", "deadline_s",
```

## 14. Assistant — 2026-10-25T04:23:25.359Z

Adding the exit-status fix to the collector, then a regression test and a mutation that brings back the old rule.

## 15. Assistant — 2026-10-25T04:23:26.944Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; grep -n -i \"exit\" $W/analysis/collect_recovery_measurements.py | cut -c1-150; sed -n 1,30p $W/tests/mutation_check.py | grep -n \"uv run\\|--only\\|Usage\\|usage\" | cut -c1-150",
  "description": "Find exit-status mentions and the mutation runner's usage"
}
```

## 16. User — 2026-10-25T04:23:27.672Z

### Tool result

```
37:It prints a summary and exits with 1 if a validity check fails. A failed outcome check is a
38:finding: it is reported and never changes the exit code. Nothing is dropped: a missed or
501:        "status_check_exit": final.get("status_check_exit"),
587:    sys.exit(main())
4:    uv run --group jobs python tests/mutation_check.py --out <folder>       # SQLite and offline Kafka settings
6:        uv run --group jobs python tests/mutation_check.py --out <folder>   # also MySQL and Kafka
7:    uv run --group jobs python tests/mutation_check.py --list
8:    uv run --group jobs python tests/mutation_check.py --only renew-token rewind
```

## 17. Assistant — 2026-10-25T04:23:31.328Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; sed -n 30,42p $W/analysis/collect_recovery_measurements.py",
  "description": "Read the collector docstring around its exit-status sentence"
}
```

## 18. User — 2026-10-25T04:23:32.063Z

### Tool result

```
  (what counts; a recorded setup or final error fails records_complete; the host protocol's
  power and lid conditions, where a missing reading fails as unknown), two verdicts, and, apart
  from them, the outcome checks of 6.2-6.5, each with what it found (6.5's new Spark scratch
  included). The verdicts (docs/recovery-part-a.md, section 12): its correctness observations
  stand on the checks that do not involve time; its recovery times need those, the clock check,
  and AC power with the lid open at every reading.
  A preflight's results are never formal results (8.6), whatever its checks found.
It prints a summary and exits with 1 if a validity check fails. A failed outcome check is a
finding: it is reported and never changes the exit code. Nothing is dropped: a missed or
unrun job keeps its row.

Durations are differences of mono values, from one host's monotonic clock (4.1), and so are
the step intervals: each launcher record's step_started_mono and tree_ended_mono. A record
```

## 19. Assistant — 2026-10-25T04:23:44.348Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; cd $W && python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"analysis/collect_recovery_measurements.py\")\ns = p.read_text()\nreps = [\n(\"\"\"It prints a summary and exits with 1 if a validity check fails. A failed outcome check is a\nfinding: it is reported and never changes the exit code.\"\"\",\n\"\"\"It prints a summary and exits with 1 unless both verdicts are valid: any required check that\nfailed, has no result or is missing gives 1, and the summary marks the unknown ones. A failed\noutcome check is a finding: it is reported and never changes the exit code.\"\"\"),\n(\"\"\"TIMING_CHECKS = (*CORRECTNESS_CHECKS, \"clock\", \"host_power\", \"host_lid\")\n\"\"\",\n\"\"\"TIMING_CHECKS = (*CORRECTNESS_CHECKS, \"clock\", \"host_power\", \"host_lid\")   # every required check\n\"\"\"),\n('''def verdict(validity: dict, checks: tuple[str, ...]) -> dict:\n    \"\"\"Valid only if every one of checks passed; the ones that did not.\"\"\"\n    failed = [name for name in checks if validity[name].get(\"passed\") is not True]\n    return {\"valid\": not failed, \"failed\": failed}\n''',\n'''def check_state(validity: dict, name: str) -> str:\n    \"\"\"passed, failed or unknown; only an explicit pass passes. A check that is missing or has no\n    result is unknown, and so is a host condition whose only problem is the readings it lacks.\"\"\"\n    check = validity.get(name) or {}\n    if check.get(\"passed\") is True:\n        return \"passed\"\n    if check.get(\"passed\") is False and (check.get(\"failed\") or not check.get(\"unknown\")):\n        return \"failed\"\n    return \"unknown\"\n\n\ndef verdict(validity: dict, checks: tuple[str, ...]) -> dict:\n    \"\"\"Valid only if every one of checks passed; the ones that did not, failed or unknown.\"\"\"\n    failed = [name for name in checks if check_state(validity, name) != \"passed\"]\n    return {\"valid\": not failed, \"failed\": failed}\n\n\ndef listed(validity: dict, names: list[str]) -> str:\n    \"\"\"The checks named, each unknown one marked as such.\"\"\"\n    return \", \".join(name if check_state(validity, name) == \"failed\" else f\"{name} (unknown)\" for name in names)\n'''),\n(\"\"\"    validity_failed = [name for name, check in validity.items()\n                       if isinstance(check, dict) and check.get(\"passed\") is False]\n    verdicts = {\"correctness\": verdict(validity, CORRECTNESS_CHECKS), \"timing\": verdict(validity, TIMING_CHECKS)}\n\"\"\",\n\"\"\"    verdicts = {\"correctness\": verdict(validity, CORRECTNESS_CHECKS), \"timing\": verdict(validity, TIMING_CHECKS)}\n    validity_failed = verdicts[\"timing\"][\"failed\"]          # every required check that failed or is unknown\n\"\"\"),\n(\"\"\"    print(\"validity: \" + (\"all checks passed\" if not result[\"validity_failed\"]\n                          else \"FAILED: \" + \", \".join(result[\"validity_failed\"])))\n    for claim, label in ((\"correctness\", \"correctness observations\"), (\"timing\", \"recovery times\")):\n        check = result[\"verdicts\"][claim]\n        print(f\"{label}: \" + (\"valid\" if check[\"valid\"] else \"INVALID: \" + \", \".join(check[\"failed\"])))\n\"\"\",\n\"\"\"    print(\"validity: \" + (\"all checks passed\" if not result[\"validity_failed\"]\n                          else \"FAILED: \" + listed(result[\"validity\"], result[\"validity_failed\"])))\n    for claim, label in ((\"correctness\", \"correctness observations\"), (\"timing\", \"recovery times\")):\n        check = result[\"verdicts\"][claim]\n        print(f\"{label}: \" + (\"valid\" if check[\"valid\"] else \"INVALID: \" + listed(result[\"validity\"], check[\"failed\"])))\n\"\"\"),\n(\"\"\"    return 1 if result[\"validity_failed\"] else 0\n\"\"\",\n\"\"\"    return 0 if all(check[\"valid\"] for check in result[\"verdicts\"].values()) else 1\n\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"collector: applied\", len(reps))\nEOF\ngit -C $W diff --stat",
  "description": "Make the collector's exit status follow its verdicts"
}
```

## 20. User — 2026-10-25T04:23:45.159Z

### Tool result

```
collector: applied 6
 analysis/collect_recovery_measurements.py |  36 +++-
 docs/recovery-experiments.md              |  71 ++++++-
 docs/recovery-part-a.md                   | 318 +++++++++++++++++++++++-------
 3 files changed, 339 insertions(+), 86 deletions(-)
```

## 21. Assistant — 2026-10-25T04:23:49.176Z

### Tool call: Bash

```
{
  "command": "sed -n 400,430p tests/test_recovery_collector.py; wc -l tests/test_recovery_collector.py",
  "description": "Show the end of the collector tests"
}
```

## 22. User — 2026-10-25T04:23:49.968Z

### Tool result

```
def test_a_batch_from_before_the_power_readings_has_unknown_conditions(tmp_path):
    """Memory-only readings, as preflight-2 and -3 recorded them, say nothing of power or the lid."""
    batch = make_batch(tmp_path, host=False)
    with open(batch / "harness.jsonl", "a") as f:
        for position in (1, 2, 3):
            f.write(json.dumps({"event": "host_memory", "position": position, "available_bytes": 2**30}) + "\n")
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["host_power"]["unknown"] == ["start", 1, 2, 3, "end"]
    assert result["verdicts"]["timing"]["valid"] is False and result["verdicts"]["correctness"]["valid"] is True
     410 tests/test_recovery_collector.py
```

## 23. Assistant — 2026-10-25T04:24:10.067Z

### Tool call: Bash

```
{
  "command": "cat >> tests/test_recovery_collector.py <<'EOF'\n\n\n# The exit status follows the verdicts: a required check that failed or is unknown gives 1\n\nHOST_POWER_ONLY = {\"host_power\": {\"passed\": True, \"failed\": [], \"unknown\": []}}       # host_lid missing\n\n\n@pytest.mark.parametrize(\"function, returns, check, invalid\", [\n    (\"clock_check\", {\"passed\": None}, \"clock\", {\"timing\"}),\n    (\"identity_check\", {\"passed\": None}, \"code_identity\", {\"correctness\", \"timing\"}),\n    (\"host_conditions\", HOST_POWER_ONLY, \"host_lid\", {\"timing\"}),\n])\ndef test_a_required_check_that_is_unknown_or_missing_fails_its_verdicts_and_exits_1(\n        batch, tmp_path, monkeypatch, capsys, function, returns, check, invalid):\n    monkeypatch.setattr(crm, function, lambda *args, **kwargs: returns)\n    result = crm.collect(batch, processed_root=tmp_path / \"processed\")\n    assert {claim for claim, v in result[\"verdicts\"].items() if not v[\"valid\"]} == invalid\n    assert all(result[\"verdicts\"][claim][\"failed\"] == [check] for claim in invalid)\n    assert result[\"validity_failed\"] == [check]\n    assert crm.main([\"--batch\", str(batch), \"--processed-root\", str(tmp_path / \"processed\")]) == 1\n    assert f\"{check} (unknown)\" in capsys.readouterr().out\nEOF\ngrep -n \"focused\\|[0-9][0-9] mutations\" tests/mutation_check.py | head -8 | cut -c1-150; grep -n 'validity\\[\"host_\\|\\[\"host_lid\"\\]\\|\\[\"host_power\"\\]' analysis/collect_recovery_measurements.py | cut -c1-150",
  "description": "Add the regression test and check for counts and direct lookups"
}
```

## 24. User — 2026-10-25T04:24:10.930Z

### Tool result

```
13:checkout. Each mutation runs the tests it names: the job tests, unless it is one of the focused
31:The focused mutations, added on 2026-10-24 (and for the gaps of docs/recovery-part-a.md the same
```

## 25. Assistant — 2026-10-25T04:24:14.307Z

### Tool call: Bash

```
{
  "command": "sed -n 28,52p tests/mutation_check.py",
  "description": "Read the mutation runner's list of focused mutations"
}
```

## 26. User — 2026-10-25T04:24:15.112Z

### Tool result

```
make equivalent are left out; for example, mark_published's published_at condition is covered
by its version guard.

The focused mutations, added on 2026-10-24 (and for the gaps of docs/recovery-part-a.md the same
day), break the recovery experiments' tooling and the worker's acceptance deadline (docs/recovery-experiments.md, section 9; docs/worker-pipeline.md),
and each runs only the test file that should catch it: the worker's, the launcher's, the fault
hook's, the harness's, the collector's, the frozen cross-check SQL's on SQLite, or the
synthetic batch's. A catch therefore shows that this file notices the break.

AI contribution: written with Claude Code (Opus 5.5).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
```

## 27. Assistant — 2026-10-25T04:24:18.382Z

The test is written. Now adding two mutations that undo the fix, then running the tests and mutations.

## 28. Assistant — 2026-10-25T04:24:21.977Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/mutation_check.py\")\ns = p.read_text()\nold = \"\"\"             \"    readings = {}\", \"the memory readings of earlier batches are no longer read\", tests=COLLECTOR_TESTS),\n)\"\"\"\nnew = \"\"\"             \"    readings = {}\", \"the memory readings of earlier batches are no longer read\", tests=COLLECTOR_TESTS),\n    Mutation(\"exit-ignores-unknown\", COLLECTOR,\n             '    return 0 if all(check[\"valid\"] for check in result[\"verdicts\"].values()) else 1',\n             '    return 1 if any(check.get(\"passed\") is False for check in result[\"validity\"].values()\\\\n'\n             '                    if isinstance(check, dict)) else 0',\n             \"a required check without a result exits 0, as before the fix\", tests=COLLECTOR_TESTS),\n    Mutation(\"missing-check-passes\", COLLECTOR, \"    check = validity.get(name) or {}\",\n             '    check = validity.get(name) or {\"passed\": True}', \"a missing required check passes\",\n             tests=COLLECTOR_TESTS),\n)\"\"\"\nassert s.count(old) == 1\np.write_text(s.replace(old, new))\nprint(\"mutations added\")\nEOF\nuv run --group jobs python -m pytest tests/test_recovery_collector.py tests/test_recovery_synthetic.py -q 2>&1 | tail -3",
  "description": "Add the two mutations and run the collector and synthetic tests"
}
```

## 29. User — 2026-10-25T04:24:51.341Z

### Tool result

```
mutations added

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
23 passed, 185 warnings in 26.99s
```

## 30. Assistant — 2026-10-25T04:24:58.451Z

### Tool call: Bash

```
{
  "command": "uv run --group jobs python tests/mutation_check.py --list 2>&1 | grep -c \"\" ; uv run --group jobs python tests/mutation_check.py --only exit-ignores-unknown missing-check-passes unknown-reading-passes timing-verdict-without-host battery-passes lid-closed-passes end-reading-not-required legacy-host-memory-ignored --out /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/mutations-exit 2>&1 | tail -14 | cut -c1-170",
  "description": "Run the new and related collector mutations",
  "timeout": 600000
}
```

## 31. User — 2026-10-25T04:25:52.782Z

### Tool result

```
100
baseline: exit 0 in 27.5 s
caught    battery-passes (2.7 s)  FAILED tests/test_recovery_collector.py::test_a_reading_on_battery_fails_the_recovery_times_but_not_the_correctness
caught    lid-closed-passes (2.9 s)  FAILED tests/test_recovery_collector.py::test_a_closed_lid_fails_the_recovery_times
caught    unknown-reading-passes (3.0 s)  FAILED tests/test_recovery_collector.py::test_a_missing_reading_or_value_is_unknown_and_never_passes
caught    timing-verdict-without-host (2.8 s)  FAILED tests/test_recovery_collector.py::test_a_reading_on_battery_fails_the_recovery_times_but_not_the_correctness
caught    end-reading-not-required (2.9 s)  FAILED tests/test_recovery_collector.py::test_a_closed_lid_fails_the_recovery_times
caught    legacy-host-memory-ignored (2.4 s)  FAILED tests/test_recovery_collector.py::test_host_memory_spark_scratch_and_the_cleanup_listing_are_reported
caught    exit-ignores-unknown (3.2 s)  FAILED tests/test_recovery_collector.py::test_a_required_check_that_is_unknown_or_missing_fails_its_verdicts_and_exits_1[clock_che
caught    missing-check-passes (3.4 s)  FAILED tests/test_recovery_collector.py::test_a_required_check_that_is_unknown_or_missing_fails_its_verdicts_and_exits_1[host_cond
8 of 8 caught; {'caught': 8, 'survived': 0, 'error': 0, 'skipped': 0}
```

## 32. Assistant — 2026-10-25T04:26:00.900Z

8 of 8 mutations caught; the two new ones are caught by the new test. Next I'm re-checking the four preflight verdicts in memory under the new rule, without writing to their folders.

## 33. Assistant — 2026-10-25T04:26:06.005Z

### Tool call: Bash

```
{
  "command": "cat > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/exit_status.py <<'EOF'\nimport sys\nfrom pathlib import Path\nsys.path.insert(0, \"analysis\")\nsys.path.insert(0, \"tests\")\nimport collect_recovery_measurements as c\nimport mutation_check as m\n\nfocused = [x for x in m.MUTATIONS if tuple(x.tests) != tuple(m.JOB_TESTS)]\nprint(\"mutations:\", len(m.MUTATIONS), \"focused:\", len(focused))\nroot = Path(\"data/outputs-recovery/preflight\")\nstamps = lambda: {p: p.stat().st_mtime_ns for p in root.rglob(\"*\") if p.is_file()}\nbefore = stamps()\nfor name in (\"preflight-1\", \"preflight-2\", \"preflight-3\", \"preflight-4\"):\n    r = c.collect(root / name)\n    status = 0 if all(v[\"valid\"] for v in r[\"verdicts\"].values()) else 1\n    print(f\"{name}: exit {status}; validity: {c.listed(r['validity'], r['validity_failed']) or 'all checks passed'}\")\nprint(\"files:\", len(before), \"unchanged:\", before == stamps())\nEOF\nuv run --group jobs python /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/exit_status.py 2>&1 | tail -7",
  "description": "Recompute the preflights' exit status in memory and count mutations"
}
```

## 34. User — 2026-10-25T04:26:18.183Z

### Tool result

```
mutations: 100 focused: 51
preflight-1: exit 1; validity: records_complete, host_power (unknown), host_lid (unknown)
preflight-2: exit 1; validity: host_power (unknown), host_lid (unknown)
preflight-3: exit 1; validity: clock, host_power (unknown), host_lid (unknown)
preflight-4: exit 0; validity: all checks passed
files: 1109 unchanged: True
```

## 35. Assistant — 2026-10-25T04:26:25.805Z

### Tool call: Bash

```
{
  "command": "uv run --group jobs python -m pytest tests/test_jobs_harness.py tests/test_recovery_sql.py tests/test_recovery_collector.py tests/test_recovery_synthetic.py -q 2>&1 | tail -2; git log -1 --format=%B 5a81bc5",
  "description": "Run the four recovery test files and read the last commit message"
}
```

## 36. User — 2026-10-25T04:26:58.411Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
62 passed, 185 warnings in 30.91s
Bracket each plan with controls and check timing validity per batch

Two items of the draft Part A proposal were approved on 2026-10-24:
this host serves for correctness observations and for recovery times
under its recorded conditions, and every batch has a control C0 at
each end, making 30 jobs.

- harness.py: Settings.bracket_controls, on by default, puts a C0 at
  each end of the shuffled order and records it in the plan. A listed
  order (--jobs) gets no controls.
- The collector checks the host protocol's conditions 1 and 2 at the
  start, before each job that ran and at the end. A reading on
  battery, or with the lid closed, fails its condition. A missing
  reading, or one without the value, as in the memory-only readings
  of earlier batches, is unknown, and unknown fails too: nothing passes
  by default.
- The collector reports two verdicts. Correctness observations need
  the checks that do not involve time; recovery times need those, the
  clock check, and both host conditions. The superseded machine_state
  placeholder is gone.

Focused tests cover the controls, battery, a closed lid, missing
readings, earlier batches and both verdicts, and the synthetic batch
now uses a fixed host reading. Six new focused mutations, 17 of 17
caught with the collector's earlier ones.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

## 37. Assistant — 2026-10-25T04:27:05.477Z

### Tool call: Bash

```
{
  "command": "git add analysis/collect_recovery_measurements.py tests/test_recovery_collector.py tests/mutation_check.py && git diff --cached --stat && git commit -q -F - <<'EOF'\nMake the collector's exit status follow its verdicts\n\nThe exit status used a narrower rule than the verdicts: it counted\nonly checks whose result was false, so a required check without a\nresult exited 0 while its verdict was invalid. Every check returns\ntrue or false today, so no batch exited wrongly, but nothing enforced\nit.\n\n- check_state() gives passed, failed or unknown; only an explicit\n  pass passes. A missing check, or one without a result, is unknown,\n  and so is a host condition whose only problem is missing readings.\n- Both verdicts and validity_failed use it, and the exit status is 0\n  only when both verdicts are valid.\n- The summary marks the unknown checks.\n\nA focused regression test covers an unknown clock check, an unknown\ncode identity and a missing host_lid check: each fails its verdicts\nand exits 1. Two new focused mutations restore the old exit rule and\nlet a missing check pass; 8 of 8 caught with the collector's earlier\nones. The four preflights' verdicts are unchanged.\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\nEOF\ngit log --oneline -2; git status --short",
  "description": "Commit the collector fix and its tests by explicit path"
}
```

## 38. User — 2026-10-25T04:27:06.420Z

### Tool result

```
 analysis/collect_recovery_measurements.py | 36 ++++++++++++++++++++++---------
 tests/mutation_check.py                   |  8 +++++++
 tests/test_recovery_collector.py          | 21 ++++++++++++++++++
 3 files changed, 55 insertions(+), 10 deletions(-)
fcaa645 Make the collector's exit status follow its verdicts
5a81bc5 Bracket each plan with controls and check timing validity per batch
 M docs/recovery-experiments.md
 M docs/recovery-part-a.md
```

## 39. Assistant — 2026-10-25T04:27:10.576Z

Committed as `fcaa645`. Now gathering the exact values and rationales for the decisions table.

## 40. Assistant — 2026-10-25T04:27:11.348Z

### Tool call: Bash

```
{
  "command": "grep -n \"^class Settings\" -A 30 src/etf_risk/jobs/harness.py | cut -c1-160",
  "description": "Read the harness settings and their values"
}
```

## 41. User — 2026-10-25T04:27:12.032Z

### Tool result

```
95:class Settings:
96-    """The provisional values of the outline's section 8 (P1-P4) and the harness's waits (8.5)."""
97-    snapshot: str = "full-2026-10-12"
98-    kind: str = "calendar-year"          # P1: every case on the calendar-year job
99-    stride: int = 21
100-    max_attempts: int = 3
101-    jobs_per_case: int = 2               # P1, the preferred draft: 2 per case, one batch (28 jobs)
102-    bracket_controls: bool = True        # a C0 control at each end of the shuffled order (30 jobs; approved)
103-    cases: tuple[str, ...] = CASES
104-    timing: tuple[str, ...] = ()         # --timing overrides; P2: none
105-    slowest_steps_s: float = 35.1        # S (P3): M2's slowest windows + spark_pipeline + verify, calendar-year
106-    deadline_margin: float = 2.0         # P3: D = B + margin * S, rounded up
107-    deadline_round_s: float = 5.0
108-    max_lag_s: float = 1.0               # P3
109-    phase_delay_s: float = 3.0           # 8.5: after spark_pipeline starts, before a mid-step injection
110-    w7_stop_s: float = 90.0              # 8.5: how long W7's tree stays stopped (longer than a takeover)
111-    outage_s: float = 30.0               # 8.5: how long K2, D1 and D2 keep their service stopped
112-    flag_fraction: float = 0.90          # P4
113-    stop_fraction: float = 0.95          # P4
114-    poll_s: float = 0.5
115-    phase_timeout_s: float = 300.0       # the longest wait for an injection's phase; then it is missed
116-
117-    @classmethod
118-    def from_dict(cls, data: dict) -> Settings:
119-        unknown = sorted(set(data) - {f.name for f in fields(cls)})
120-        if unknown:
121-            raise ValueError(f"unknown settings: {unknown}")
122-        settings = cls(**{k: tuple(v) if k in ("cases", "timing") else v for k, v in data.items()})
123-        if bad := sorted(set(settings.cases) - set(CASES)):
124-            raise ValueError(f"unknown cases: {bad}")
125-        return settings
```

## 42. Assistant — 2026-10-25T04:27:15.462Z

### Tool call: Bash

```
{
  "command": "sed -n 404,420p docs/recovery-experiments.md; echo ...; sed -n 420,460p docs/recovery-experiments.md | cut -c1-200",
  "description": "Read the outline's Part A decision proposals, part 1"
}
```

## 43. User — 2026-10-25T04:27:16.117Z

### Tool result

```
|---|---|---|---|
| Q0 | `jobs`, `job_attempts` | the snapshot fingerprint | 4.5 |
| Q1 | `jobs`, `job_attempts` | accepted results and claims per job; one verdict per job | 6.2 |
| Q2 | `batch_jobs`, `deadline_observations`, `jobs` | each submitted job's deadline class and `deadline_met` | 4.2, 6.3 |
| Q2b | `jobs`, `batch_jobs` | jobs in the table that the harness did not record | 6.3 |
| Q3a | `worker_accepts`, `job_store`, `jobs`, `job_attempts` | event-log completeness per succeeded job | 6.4 |
| Q3b | `worker_accepts`, `job_store`, `job_attempts` | the identity of each report | 6.4 |

Q1 deliberately overlaps the store's seven `INVARIANT_QUERIES`: a second reading of the same rows by
queries the store does not run. On 2026-10-23 the queries and a fixture of 21 job ids ran once in a
throwaway MySQL 8.4.13, and all 82 expected rows, written before the run, matched
([recovery-sql.md](recovery-sql.md), section 6). That validates the queries against their rules on
made-up rows; it says nothing about the job system.

## 8. Part A decisions: proposals

_Claude Code's proposals, with reasons. None is decided, and Part A is not approved._ They rest on
...
_Claude Code's proposals, with reasons. None is decided, and Part A is not approved._ They rest on
M2's final report (`6d8a232`):

| Input from M2 | Value |
|---|---|
| steps, calendar-year job | windows 2.5–3.0 s, spark_pipeline 22.1–22.6 s, verify 9.5 s; about 34–35 s in all |
| steps, stride-21 job | 1.5 s, 44.8–50.4 s, 11.0–11.5 s; about 57–63 s in all |
| step trees' peak RSS | spark_pipeline 0.66–0.79 GiB (calendar-year), 1.19–1.36 GiB (stride 21); verify 0.45–0.58 GiB; windows 0.12 GiB |
| job processes' RSS | worker 63.0 MiB, reconciler 51.6 MiB |
| container peaks | MySQL 345 MiB (67%) after the live job suites and 501 MiB (98%) after the live mutation session; Kafka 361–415 MiB (56–65%); informational, since another project's four contain
| MySQL stalls, M2's clock | 0, 1 and 2 failed renewals for `LOCK TABLES`, `pause` and `restart`; each run kept its first attempt; no outage duration reported |
| acceptance runs | 10 of 10 passed on M2's clock in 11 min 20 s; the first run's failures were faults of the test harness |
| isolated memory-budget check | not done: pending |

### 8.1 Repetitions and workload

- **Proposal (P1), the preferred draft since 2026-10-24.** Every case on the calendar-year job; one
  batch on fresh containers with 2 jobs of each of the 14 cases (C0 included), 28 in all, in one
  shuffled order drawn from a seed recorded before the batch. It is the harness's default plan.
- **Alternative: the first P1.** 3 jobs of each case per batch, 42 in all, and 2 batches, each on
  fresh containers: 84 jobs.
- **Reasons.** The calendar-year job is the shortest (steps about 35 s against 63 s for stride 21),
  and its 22 s `spark_pipeline` step is still long enough to aim the mid-step injections; the
  stride-21 job adds run time without a recovery path of its own. The preferred draft keeps every
  case, so every failure mode and recovery path, and E1's checks on every job, in about a third of
  the alternative's time. It gives up the second batch on fresh containers, which would show whether
  results repeat across containers, and four of every six repetitions: one missed injection leaves a
  case with one made injection. Both keep each batch short of the ~50 runs after which M2 saw MySQL
  at 98% (another workload, so only a rough guide). A recorded shuffle spreads drift, such as memory
  growth, across cases instead of lining it up with one.
- **Duration** (estimates, provisional, and finalized only after the live preflight, 8.6).
  `python -m etf_risk.jobs.harness estimate` adds, per job, the design's upper bounds of 3.2 and
  these assumptions, none of them measured: T 40 s (M2's slowest steps, 35.1 s, plus 5 s of the
  worker's own work), 12 s to restart a killed worker and rebalance, 20 s for a service from start
  to ready, 2 s for the peaks after every job, 18 s for the group after a Kafka restart, and 3 minutes
  per batch for the containers, the reference run, the final snapshot and teardown. One job of each
  case takes 1,403 s (23.4 minutes), from 42 s (C0) to 159 s (W4, W7). The preferred batch of 28
  jobs: 2,986 s, about 50 minutes (52, 55 or 60 minutes if T is 45, 50 or 60 s). The alternative:
  4,389 s (73 minutes) per batch of 42, and 8,778 s (about 2 hours 26 minutes) for both; each extra
  5 s of T adds 8 minutes to the 84 jobs (T runs 16 times per 14 jobs). A longer restore lengthens K2
  and can move D1 and D2 onto their fenced paths. The figures come from the estimator's formulas,
```

## 44. Assistant — 2026-10-25T04:27:21.926Z

### Tool call: Bash

```
{
  "command": "sed -n 460,545p docs/recovery-experiments.md | cut -c1-220",
  "description": "Read the outline's Part A decision proposals, part 2"
}
```

## 45. User — 2026-10-25T04:27:22.406Z

### Tool result

```
  and can move D1 and D2 onto their fenced paths. The figures come from the estimator's formulas,
  worked out by hand; tests/test_jobs_harness.py pins them and passed on 2026-10-24.
- **Counts, not rates.** The first review removed the pooled rule-of-three claim; reporting counts
  only is Claude Code's proposal. Results are given per case as k of n, with no rate, probability or
  confidence bound, pooled or per case: the injections are not shown to be independent, and cases are
  not alike.

### 8.2 Timing and deadlines

- **Proposal (P2), the clock and the limits.** The defaults of
  [timing.py](../src/etf_risk/jobs/timing.py) (lease 60 s, renewals every 10 s, fence margin 10 s,
  session timeout 15 s, heartbeats 3 s) and its step limits (windows 120 s, spark_pipeline 600 s,
  verify 300 s, attempt 900 s), with no `--timing` override.
- **Reasons.** E2 asks how long recovery takes, and the defaults are what the job processes run
  with; the token guards that decide E1 do not depend on the clock. The limits are about 40, 12 and
  26 times the measured step maxima (3.0, 50.4 and 11.5 s) and matter only to W7's lock wait and the
  classic-protocol bound; changing them would add a configuration M2 did not test. Cost: lease-based
  recoveries take 50–65 s instead of 20–29 s on M2's clock. Risk: the default clock has not run
  live, so the first batch is also its first live run.
- **Proposal (P3), the deadlines, reassessed on 2026-10-24.** Each case's D is the bound B from its
  reference to the start of its next run, plus twice the slowest step sum M2 measured for the
  parameter set (2S: 70.2 s calendar-year, 126.8 s stride 21), rounded up to 5 s; `max_lag_s` is 1 s,
  and the drain limit equals D. The reassessment changed three things:
  - W7's B is the later of the takeover (L + P, 65 s) and the end of the stopped tree (the stop plus
    two watchdog ticks and the kill grace: 98 s for a 90 s stop), no longer 65 s plus the stop;
  - K2, D1 and D2 count from their service's return (4.2), so B holds no outage of unknown length:
    for K2 the publication grace, a reconciler pass and the group's rejoin (30 + 5 + 19 = 54 s); for
    D1 and D2 a fenced attempt's lease and a pass (65 s);
  - the observation comes at completion when that is first (4.3), so meeting a deadline costs no
    waiting.

  | Cases | B | calendar-year D | stride-21 D |
  |---|---|---|---|
  | C0, W5a, W5b, K1, X1 | 0 | 75 s | 130 s |
  | W1 | 19 s | 90 s | 150 s |
  | W2, W3, W4, W6 | 65 s | 140 s | 195 s |
  | W7, with a 90 s stop | 98 s | 170 s | 225 s |
  | K2, from the broker's return | 54 s | 125 s | 185 s |
  | D1, D2, from MySQL's return | 65 s | 140 s | 195 s |

- **Reasons.** B is where the design puts the next run's start at the latest. S is the steps alone,
  not T: T adds the worker's own work (the claim, the input checksums, the manifest, renewals, three
  launcher starts), which nothing has measured, and 2S leaves about 35 s for it and for a slower run
  (M2's `spark_pipeline` varied by up to 5.6 s) while a stalled job still misses. The first batch's
  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next
  batch is an option for the author, recorded as a deviation. A local read of one row should take
  milliseconds, so a 1 s lag classifies nearly every success seen at the deadline and leaves the rest
  visible as `deadline not observed`. A drain limit of D gives a late job as long again to finish,
  enough to tell late from unfinished without one job holding the batch indefinitely. Whether D1 at
  this clock takes one claim or two stays open: M2 reported no outage duration, and failed-renewal
  counts do not establish one. The deadlines stay a draft until the live preflight (8.6): its C0 jobs
  measure T at the default clock, and its K2, D1 and D2 show the service-dependent paths.

### 8.3 Memory

- **Proposal (P4).** Fresh MySQL and Kafka containers for each batch; `services peaks` read after
  every job as well as before every injected restart (4.6); a batch flagged when either container's
  batch peak passes 90% of its limit, and stopped (no further jobs, then quiescence, 4.4) when either
  passes 95%; the host's available memory recorded before each job but not used as a gate.
- **Reasons.** Spec §11 asks for a fresh MySQL per batch; MySQL reached 98% in M2's mutation
  session, so a stop rule keeps a batch from reaching the limit unobserved, and a reading after every
  job lets it act in time. No measurement of the host's available memory with only this project's
  containers exists (M2's 1.3 GiB had another project's containers running), so a host gate would
  have no basis yet.
- **Pending.** The isolated memory-budget check. Until it is done, these limits are provisional and
  the budgets of spec §11 are not validated. The memory rules are finalized only after the live
  preflight (8.6), which reads both containers' peaks as a batch does.

### 8.4 Injection method

- **Proposal (P5), implemented and tested offline.** `etf_risk.jobs.faults`: a worker started with
  `ETF_RISK_FAULT_FILE` looks at that file at each fault point, and its `started` event names the
  file. The harness arms one fault for one job by writing the file atomically: a point, and an
  action (SIGKILL to the worker's own process, or a hold until a release file appears, for D2). The
  worker removes the file before it acts, so an arming fires once, and logs `fault_injected`, whose
  `mono` is the injection time. A new fault point, `after_accept_commit`, lies between
  `accept_result`'s return and the `accepted` event and is in `WORKER_FAULT_POINTS`. A file, rather
  than a fault named in the environment as first proposed, lets the harness arm the owner for one
  job without restarting it: a restart would rebalance the group and could move the partition (2.4).
- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside
  cannot hit reliably. `Worker(fault=...)` already calls the fault points, so the hook only wires
  them to the command, and the new point joins the offline tests that crash at every point. The code
  is new, written with Claude Code. Its offline tests passed on 2026-10-24: arming a running worker,
  and a hold released after F, which ends without an acceptance call (tests/test_jobs_worker.py), and
  the five kill hooks in the synthetic batch. Mutation checks for it are not written. Without it,
  these six cases would be recorded as not run.
```

## 46. Assistant — 2026-10-25T04:27:26.202Z

### Tool call: Bash

```
{
  "command": "sed -n 545,600p docs/recovery-experiments.md | cut -c1-220; echo ...; grep -n -i \"rerun\\|re-run\\|new batch\\|second batch\\|another batch\\|repeat the batch\" docs/recovery-experiments.md docs/recovery-part-a.md | cut -c1-160",
  "description": "Read the outline's open items and search for a rerun rule"
}
```

## 47. User — 2026-10-25T04:27:26.940Z

### Tool result

```
  these six cases would be recorded as not run.

### 8.5 Still open

The clock-check tolerance (4.1; the collector uses 1 s until it is decided); the harness's waits
(the phase delay before a mid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep
a service down: the settings hold 3 s, 90 s and 30 s for now); a host-memory gate, after the
isolated check; and the branches: the tooling and these documents are on `feature/recovery-harness`,
created from `e4adc38`, with a code checkpoint committed on 2026-10-24 and not pushed, while the
first copies of the documents, on `docs/recovery-outline`, stay as they were at revision 3.

### 8.6 The live preflight (proposal)

- **What.** It ran on 2026-10-24; its outcomes are in [recovery-part-a.md](recovery-part-a.md),
  section 11. One small batch against the services, before any formal batch, and only after the M2
  session releases the window: the reference run through the launcher (2.2), then C0, W1, W6, W7,
  K1, K2, D1, D2 and a second C0, in that order, on the default clock (P2), with the provisional
  settings of P3 and P4 and the hooks of P5. Plan: `plan --purpose preflight --jobs
  C0,W1,W6,W7,K1,K2,D1,D2,C0`. Estimated at 1,068 s (about 18 minutes) under the assumptions of 8.1.
- **What it checks.** The default clock's first live run (P2's risk); the real reference run under
  the launcher; the partition's owner from assignment events with real Kafka, at startup, after W1's
  kill and after each restart (2.4); and the paths only the services can show: a stopped worker and a
  stopped tree (W6, W7), Kafka restarted and stopped (K1, K2), MySQL restarted during a step and at
  acceptance (D1, D2). The synthetic batch (section 9) covers none of these.
- **Kept apart.** The plan says `purpose: preflight`. The harness writes such a batch only into
  `data/outputs-recovery/preflight/<batch>/` and names its purpose in the batch's records; the
  collector heads its summary and `validity.json` with it. A preflight's outcomes are reported in
  full, failed ones included, and never pooled with or counted as formal results. A formal batch needs
  a formal plan, a folder `data/outputs-recovery/formal/<batch>/` and `--formal`, given only once the
  author has approved Part A.
- **What follows.** The deadlines (P3), the memory rules (P4) and the runtime estimates (8.1) are
  then revised from the preflight's records, as proposals for the author; the preflight decides
  nothing in this section by itself.
- **In the same window.** The job tests against both services (README), which include the new
  worker tests on MySQL and the assignment events with real Kafka, and the live pipeline tests whose
  overlap check now compares monotonic times (`tests/test_jobs_live_pipeline.py`); each run once, its
  output kept with the preflight's records and labelled as a preflight run.

## 9. Records, prerequisites and authorship

- **Records**, under `data/outputs-recovery/<purpose>/<batch>/`, outside Git: the export, the event
  logs, the harness's logs (injections with intended and verified phases, deadlines and
  observations, process starts and clock checks, partition owners, the host's memory before each
  job, Spark scratch, setup and final errors), `services peaks` by segment, the three fingerprints,
  Q0–Q3b as CSV, the table of section 5 with one row per injection, the per-case tally, and
  `cleanup`'s listing (`cleanup.txt`).
- **Nothing is dropped.** Every injection (misses, those not run, and those whose harness record is
  incomplete, counted apart as unrecorded, included), every batch (invalid ones included) and every
  verdict (failed outcomes and unknowns included) stays in the records; the tally lists all 14 cases
  and every verdict value, with zeros.
- **Tooling**, on `feature/recovery-harness` (a code checkpoint committed on 2026-10-24, not
  pushed), written with Claude Code at the author's decision of 2026-10-24:
  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs
    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)
    byte for byte (a test checks it);
  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);
...
docs/recovery-experiments.md:320:| time to re-run | t_inj to the `claimed` event of the job's next attempt (W1: its first) | event logs |
docs/recovery-experiments.md:335:| Case | Detection time | Time to re-run | Time to finish, overhead |
docs/recovery-experiments.md:445:  the alternative's time. It gives up the second batch on fresh containers, which would show whether
docs/recovery-part-a.md:303:| preflight-4: C0, W3, C0 (the W3 rerun with a control on each side), on AC power with the lid open | 3 of 3 injections made; validi
docs/recovery-part-a.md:364:Preflight-3 is **invalid for timing** and stays so. Its detection, rerun and finish times and its
```

## 48. Assistant — 2026-10-25T04:27:43.524Z

### Tool call: Bash

```
{
  "command": "git diff --stat 8c5331d fcaa645 -- src analysis tests; git diff 8c5331d fcaa645 -- src/etf_risk/jobs/harness.py | grep \"^[-+]\" | grep -v \"^+++\\|^---\" | cut -c1-150",
  "description": "Check what changed in the tooling since preflight-4's commit"
}
```

## 49. User — 2026-10-25T04:27:44.683Z

### Tool result

```
 analysis/collect_recovery_measurements.py | 75 +++++++++++++++++++++----
 src/etf_risk/jobs/harness.py              | 18 ++++--
 tests/mutation_check.py                   | 29 ++++++++++
 tests/test_jobs_harness.py                | 28 +++++++---
 tests/test_recovery_collector.py          | 91 +++++++++++++++++++++++++++++--
 tests/test_recovery_synthetic.py          |  4 ++
 6 files changed, 217 insertions(+), 28 deletions(-)
-seed (or, with --jobs, in the order listed), the case of each, the settings and the code
-identity. Settings holds every value that section 8 of the outline leaves provisional (timing,
+seed with a C0 control at each end (or, with --jobs, in the order listed, with no controls
+added), the case of each, the settings and the code identity. Settings holds every value that section 8 of the outline leaves provisional (timing,
+    bracket_controls: bool = True        # a C0 control at each end of the shuffled order (30 jobs; approved)
-    """The batch's cases in run order: jobs_per_case of each case, shuffled with the seed."""
+    """The batch's cases in run order: jobs_per_case of each case, shuffled with the seed, and,
+    with bracket_controls, a C0 control at each end, measured in the same batch as the cases
+    (docs/recovery-part-a.md, section 12, condition 6)."""
-    return jobs
+    return ["C0", *jobs, "C0"] if settings.bracket_controls else jobs
-    """A plan (8.1). jobs, if given, is the run order as listed, as a preflight's is (8.6);
-    otherwise plan_jobs shuffles every case of settings.cases with the seed."""
+    """A plan (8.1). jobs, if given, is the run order as listed, as a preflight's is (8.6), with no
+    controls added; otherwise plan_jobs shuffles every case of settings.cases with the seed and,
+    with bracket_controls, puts a C0 control at each end."""
+    controls = "a C0 at each end" if jobs is None and settings.bracket_controls else None
+            "controls": controls,
```

## 50. Assistant — 2026-10-25T04:27:54.401Z

### Tool call: Bash

```
{
  "command": "grep -n \"line-length\\|line_length\" pyproject.toml; awk 'length > 120 {print FILENAME\":\"FNR\": \"length}' src/etf_risk/jobs/harness.py analysis/collect_recovery_measurements.py tests/test_recovery_collector.py tests/mutation_check.py; grep -o '\"event\": \"peaks\"[^}]*}' data/outputs-recovery/preflight/preflight-4/harness.jsonl | head -2 | cut -c1-300; grep -c '\"event\": \"peaks\"' data/outputs-recovery/preflight/preflight-4/harness.jsonl",
  "description": "Check line limits and find preflight-4's container peaks"
}
```

## 51. User — 2026-10-25T04:27:55.353Z

### Tool result

```
src/etf_risk/jobs/harness.py:10: 146
src/etf_risk/jobs/harness.py:612: 121
src/etf_risk/jobs/harness.py:818: 122
src/etf_risk/jobs/harness.py:959: 123
analysis/collect_recovery_measurements.py:68: 121
analysis/collect_recovery_measurements.py:117: 124
analysis/collect_recovery_measurements.py:249: 123
analysis/collect_recovery_measurements.py:492: 121
tests/test_recovery_collector.py:133: 123
tests/test_recovery_collector.py:154: 123
tests/test_recovery_collector.py:162: 125
tests/test_recovery_collector.py:164: 124
tests/test_recovery_collector.py:166: 125
tests/test_recovery_collector.py:168: 125
tests/test_recovery_collector.py:318: 123
tests/mutation_check.py:32: 150
tests/mutation_check.py:96: 121
tests/mutation_check.py:104: 122
tests/mutation_check.py:110: 127
tests/mutation_check.py:127: 127
tests/mutation_check.py:133: 122
tests/mutation_check.py:136: 121
tests/mutation_check.py:163: 124
tests/mutation_check.py:172: 122
tests/mutation_check.py:183: 127
tests/mutation_check.py:197: 397
tests/mutation_check.py:198: 214
tests/mutation_check.py:224: 131
tests/mutation_check.py:225: 124
tests/mutation_check.py:237: 135
tests/mutation_check.py:240: 123
tests/mutation_check.py:246: 131
tests/mutation_check.py:247: 124
tests/mutation_check.py:261: 123
tests/mutation_check.py:264: 123
tests/mutation_check.py:277: 127
tests/mutation_check.py:301: 124
tests/mutation_check.py:327: 128
tests/mutation_check.py:332: 131
tests/mutation_check.py:336: 128
tests/mutation_check.py:337: 122
tests/mutation_check.py:348: 123
tests/mutation_check.py:350: 127
tests/mutation_check.py:475: 139
"event": "peaks", "batch": "preflight-4", "service": "mysql", "peak_bytes": 332414976, "limit_bytes": 536870912, "closes": null, "verdict": "ok"}
"event": "peaks", "batch": "preflight-4", "service": "kafka", "peak_bytes": 509206528, "limit_bytes": 671088640, "closes": null, "verdict": "ok"}
8
```

## 52. Assistant — 2026-10-25T04:28:01.259Z

Preflight-4's container peaks are in its records. Computing their maxima and the 84-job alternative's runtime for the table's rationale.

## 53. Assistant — 2026-10-25T04:28:05.407Z

### Tool call: Bash

```
{
  "command": "uv run --group jobs python - <<'EOF' 2>&1 | tail -8\nimport json\nfrom pathlib import Path\nfrom etf_risk.jobs.harness import Assumptions, Settings, estimate, make_plan\n\nevents = [json.loads(l) for l in Path(\"data/outputs-recovery/preflight/preflight-4/harness.jsonl\").read_text().splitlines() if l.strip()]\nfor service in (\"mysql\", \"kafka\"):\n    peaks = [e for e in events if e.get(\"event\") == \"peaks\" and e.get(\"service\") == service]\n    top = max(peaks, key=lambda e: e[\"peak_bytes\"])\n    print(service, f\"{top['peak_bytes'] / 2**20:.0f} of {top['limit_bytes'] / 2**20:.0f} MiB ({top['peak_bytes'] / top['limit_bytes']:.0%})\", len(peaks), \"readings\")\npre = Assumptions(time_to_finish_s=49.6, restore_s=11.0, restart_s=5.0, batch_fixed_s=100.0)\nalt = make_plan(Settings(jobs_per_case=3), 1)\nfor label, a in ((\"preflight values\", pre), (\"original assumptions\", Assumptions())):\n    e = estimate(alt, a)\n    print(\"alternative per batch,\", label, e[\"jobs\"], \"jobs\", e[\"batch_s\"], \"s; two batches\", round(2 * e[\"batch_s\"] / 60, 1), \"min\")\nEOF",
  "description": "Get preflight-4's peak memory and the alternative's runtime"
}
```

## 54. User — 2026-10-25T04:28:07.618Z

### Tool result

```
mysql 317 of 512 MiB (62%) 4 readings
kafka 486 of 640 MiB (76%) 4 readings
alternative per batch, preflight values 44 jobs 4457.2 s; two batches 148.6 min
alternative per batch, original assumptions 44 jobs 4473.0 s; two batches 149.1 min
```

## 55. Assistant — 2026-10-25T04:28:57.095Z

Collected everything for the table. Now updating Part A §7, §10 and §12 and the outline for the exit-status fix, and putting the decisions table into §10.

## 56. Assistant — 2026-10-25T04:28:57.583Z

### Tool call: Bash

```
{
  "command": "sed -n 262,284p docs/recovery-part-a.md",
  "description": "Show Part A section 10 as it stands"
}
```

## 57. User — 2026-10-25T04:28:58.816Z

### Tool result

```
## 10. Author decisions

**Approved by the author on 2026-10-24:**
- this host, for correctness observations and for recovery times under its recorded conditions,
  with section 12's limitations;
- the two controls, one C0 at each end of the batch (30 jobs).

**Still open:**

| Decision | Recommended |
|---|---|
| Workload (P1) | 28 shuffled jobs and the two approved controls, 30 in all; the 84 jobs stay the alternative (plus their own controls) |
| Clock (P2) | the defaults, confirmed by the preflight |
| Deadlines (P3) | as in section 3; the preflight's T (median 49.6 s) is below 70.2 s, so no re-derivation |
| Harness waits | 3 s phase delay, 90 s W7 stop, 30 s outages |
| Clock-check tolerance | 1 s |
| Injection method (P5) | the fault file, as implemented |
| Memory (P4) | flag containers at 90% and stop at 95% of the limits M2's check validated (under host pressure); host memory recorded, never gated (section 12) |
| Host protocol (section 12) | conditions 1–7: AC power, lid open, sleep prevented, no competing tests, memory pressure and swap recorded, controls in the same batch, every outcome kept. The collector checks 1–3 (3 through the clock check); 4 is checked before the start |
| A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labelled as such (preflight-3) |
| A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both |
| Seed | an integer the author fixes in the plan before the batch |
```

## 58. Assistant — 2026-10-25T04:29:18.133Z

### Tool call: Bash

```
{
  "command": "uv run --group jobs python - <<'EOF' 2>&1 | tail -5\nimport sys\nfrom pathlib import Path\nsys.path.insert(0, \"analysis\")\nimport collect_recovery_measurements as c\nFAULT = {\"W1\", \"W2\", \"W4\", \"W5a\", \"W5b\", \"D2\"}\nMID = {\"W3\", \"W6\", \"W7\", \"K1\", \"D1\"}\nfor name in (\"preflight-2\", \"preflight-3\", \"preflight-4\"):\n    rows = c.collect(Path(\"data/outputs-recovery/preflight\") / name)[\"rows\"]\n    real = [r for r in rows if r[\"case\"] != \"C0\"]\n    print(name, \"injections\", sum(r.get(\"status\") == \"made\" for r in real), \"of\", len(real),\n          \"| fault file\", sum(r.get(\"status\") == \"made\" for r in real if r[\"case\"] in FAULT), \"of\", sum(r[\"case\"] in FAULT for r in real),\n          \"| mid-step\", sum(r.get(\"status\") == \"made\" for r in real if r[\"case\"] in MID), \"of\", sum(r[\"case\"] in MID for r in real),\n          \"| C0\", [r.get(\"status\") for r in rows if r[\"case\"] == \"C0\"])\nEOF",
  "description": "Count the preflights' injections by method from the records"
}
```

## 59. User — 2026-10-25T04:29:30.281Z

### Tool result

```
preflight-2 injections 7 of 7 | fault file 2 of 2 | mid-step 4 of 4 | C0 ['made', 'made']
preflight-3 injections 6 of 6 | fault file 4 of 4 | mid-step 1 of 1 | C0 ['made']
preflight-4 injections 1 of 1 | fault file 0 of 0 | mid-step 1 of 1 | C0 ['made', 'made']
```

## 60. Assistant — 2026-10-25T04:30:37.492Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nreps = [\n(\"command, event and record in it was checked against the tooling at `5a81bc5`.\",\n \"command, event and record in it was checked against the tooling at `fcaa645`.\"),\n(\"\"\"# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two\n#    verdicts, correctness observations and recovery times, and exits 1 if any check fails, even\n#    one that invalidates only the recovery times (a battery reading, a closed lid, an unknown one)\n\"\"\",\n\"\"\"# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two\n#    verdicts, correctness observations and recovery times, and exits 1 unless both are valid: any\n#    required check that failed or is unknown gives 1 (a battery reading, a closed lid, a missing one)\n\"\"\"),\n(\"\"\"**Still open:**\n\n| Decision | Recommended |\n|---|---|\n| Workload (P1) | 28 shuffled jobs and the two approved controls, 30 in all; the 84 jobs stay the alternative (plus their own controls) |\n| Clock (P2) | the defaults, confirmed by the preflight |\n| Deadlines (P3) | as in section 3; the preflight's T (median 49.6 s) is below 70.2 s, so no re-derivation |\n| Harness waits | 3 s phase delay, 90 s W7 stop, 30 s outages |\n| Clock-check tolerance | 1 s |\n| Injection method (P5) | the fault file, as implemented |\n| Memory (P4) | flag containers at 90% and stop at 95% of the limits M2's check validated (under host pressure); host memory recorded, never gated (section 12) |\n| Host protocol (section 12) | conditions 1–7: AC power, lid open, sleep prevented, no competing tests, memory pressure and swap recorded, controls in the same batch, every outcome kept. The collector checks 1–3 (3 through the clock check); 4 is checked before the start |\n| A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labelled as such (preflight-3) |\n| A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both |\n| Seed | an integer the author fixes in the plan before the batch |\"\"\",\n\"\"\"**Still open, proposed for approval together** (rows 11 and 13 are new in this draft):\n\n| # | Decision | Proposed value | Rationale |\n|---|---|---|---|\n| 1 | Workload (P1) | one batch of 30 jobs: C0, 2 of each of the 14 cases in shuffled order (28), C0; the calendar-year job on `full-2026-10-12`, `max_attempts` 3; results as counts per case (k of 2; C0 k of 4), no rates | every case and recovery path twice, with E1 checked on every job, in about 51 min; the 84-job alternative (2 batches of 42 plus their controls) takes about 2 h 29 min. No rates, since the injections are not shown to be independent |\n| 2 | Seed | 544, written into the formal plan before it is generated, never redrawn | any fixed integer works; fixing it before the order is seen rules out choosing an order |\n| 3 | Clock (P2) | the timing.py defaults, no override: lease 60 s, renewal 10 s, fence margin 10 s, session 15 s, heartbeat 3 s, reconciler 5 s, publication grace 30 s; step limits 120, 600 and 300 s, attempt 900 s | E2 times the configuration the job processes run with; E1's token guards do not depend on the clock; preflights 2–4 ran these values and every path behaved as designed |\n| 4 | Deadlines (P3) | D = ceil5(B + 2S), S = 35.1 s: 75 s (C0, W5a, W5b, K1, X1), 90 s (W1), 125 s (K2, from Kafka's return), 140 s (W2, W3, W4, W6; D1 and D2 from MySQL's return), 170 s (W7); drain limit D; `max_lag_s` 1 s | B is the design's latest start of the next run; the four C0 times of preflights 2 and 4 (45.1–52.4 s) stay below 2S = 70.2 s, so P3's own rule keeps D; on time and late describe this host only |\n| 5 | Harness waits | phase delay 3 s; W7 stop 90 s; outages 30 s (K2, D1, D2); a phase not reached in 300 s is a miss | 3 s puts the kill inside spark_pipeline, the longest step (6 of 6 mid-step injections made); 90 s outlasts the takeover (65 s), so W7's replacement waits for the stopped tree; 30 s outlasts the Kafka session (15 s) and brings MySQL back near F, so D1 and D2 can take either branch (preflight-2 showed both) |\n| 6 | Clock-check tolerance | 1 s | wall minus monotonic time drifted 0.018 and 0.028 s over whole batches; preflight-3's sleep showed as 63.8 s and more |\n| 7 | Injection method (P5) | the fault file at the named points for W1, W2, W4, W5a, W5b and D2, armed only on the partition's owner; signals from the harness for W3, W6 and W7; `docker compose` for K1's restart and the outages of K2, D1 and D2; a second publication for X1 | those six windows last milliseconds, too short for an outside signal; 14 of 14 injections in preflights 2–4 were made (the 6 fault-file ones included), none missed |\n| 8 | Memory (P4) | fresh containers for the batch; peaks read after every job; flag at 90% and stop the batch at 95% of 512 MiB (MySQL) and 640 MiB (Kafka); host memory recorded, never gated | M2 validated these limits (under host pressure); the preflights peaked at 49–62% (MySQL) and 60–77% (Kafka); no measured host figure is tied to recovery behaviour |\n| 9 | Host protocol | section 12, conditions 1–7 | each answers preflight-3's failure (a sleep on battery with the lid closed) or a confound; the collector checks 1–3, `pgrep` checks 4 before the start, 5 is recorded and 6 is the default plan |\n| 10 | A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labelled as such | relabelling once a cause is known would let results pick the batches; the checks that do not involve time still hold (preflight-3) |\n| 11 | The formal batch invalid or stopped early | kept and reported in full; one rerun with the same plan in `formal/batch-2` once the cause is removed (a code fix gets a preflight of the affected cases first); both reported side by side | decided before any result is seen, so no batch is chosen afterwards; Part A had no rule for this |\n| 12 | A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both | as done for G9 (preflight-1, then preflight-3) |\n| 13 | Code for the formal batch | `fcaa645` (the commit of the approved documents adds no code); no further live preflight | since preflight-4 (`8c5331d`), only plan generation and the collector changed, both covered offline by their tests, the synthetic batch and mutations |\"\"\"),\n(\"\"\"    - a missing reading, or one without the value, is unknown, and unknown fails.\n  - `injections.csv` gives each job its power, lid, pressure and swap activity.\"\"\",\n\"\"\"    - a missing reading, or one without the value, is unknown, and unknown fails.\n  - The exit status is 0 only when both verdicts are valid, so a required check that failed, has no\n    result or is missing exits 1, and the summary marks the unknown ones (`fcaa645`).\n  - `injections.csv` gives each job its power, lid, pressure and swap activity.\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"Part A: applied\", len(reps))\n\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nreps = [\n(\"\"\"  - Required: the collector's timing validity fails a battery reading or a closed lid, and a missing\n    reading is handled explicitly, never passed silently.\"\"\",\n\"\"\"  - Required: the collector's timing validity fails a battery reading or a closed lid, and a missing\n    reading is handled explicitly, never passed silently; the exit status agrees with the verdicts,\n    so any required check that failed or is unknown exits nonzero.\n  - Every remaining Part A decision in one table, with its proposed value and reason, for approval\n    together (the same document, section 10).\"\"\"),\n(\"\"\"The clock-check tolerance (4.1; the collector uses 1 s until it is decided); the harness's waits\n(the phase delay before a mid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep\na service down: the settings hold 3 s, 90 s and 30 s for now); a host-memory gate, after the\nisolated check; and the branches: the tooling and these documents are on `feature/recovery-harness`,\ncreated from `e4adc38`, with a code checkpoint committed on 2026-10-24 and not pushed, while the\nfirst copies of the documents, on `docs/recovery-outline`, stay as they were at revision 3.\"\"\",\n\"\"\"Every remaining decision is in one table with its proposed value and reason\n([recovery-part-a.md](recovery-part-a.md), section 10), these included: the clock-check tolerance\n(4.1; the collector uses 1 s until it is decided) and the harness's waits (the phase delay before a\nmid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep a service down: 3 s, 90 s\nand 30 s). The host-memory gate is dropped: memory is recorded, never gated (the same document,\nsection 12). The branches: the tooling and these documents are on `feature/recovery-harness`,\ncreated from `e4adc38`, with commits from 2026-10-24, none pushed, while the first copies of the\ndocuments, on `docs/recovery-outline`, stay as they were at revision 3.\"\"\"),\n(\"\"\"  fails the second (`5a81bc5`). Before that commit, 17 focused mutations, its six new ones included,\n  were run: 17 caught, each by its intended test (the same document, sections 9, 11 and 12).\"\"\",\n\"\"\"  fails the second (`5a81bc5`). Before that commit, 17 focused mutations, its six new ones included,\n  were run: 17 caught, each by its intended test. Last, the exit status came to follow the verdicts,\n  so a required check that failed or is unknown exits 1 (`fcaa645`); 8 of 8 collector mutations\n  were caught, its two new ones included (the same document, sections 9, 11 and 12).\"\"\"),\n(\"\"\"  - Recomputed under these checks, without writing to the records: preflight-1 is invalid for both,\n    preflight-2 and preflight-3 are valid for correctness only, and preflight-4 is valid for both.\n\n  Part A gives the 30-job runtime (about 51 min for the batch) and the final draft for review\n  ([recovery-part-a.md](recovery-part-a.md), sections 8, 10–12).\"\"\",\n\"\"\"  - The exit status follows the verdicts: a required check that failed, has no result or is\n    missing exits 1 (`fcaa645`).\n  - Recomputed under these checks, without writing to the records: preflight-1 is invalid for both,\n    preflight-2 and preflight-3 are valid for correctness only, and preflight-4 is valid for both;\n    the first three would exit 1, preflight-4 0.\n\n  Part A gives the 30-job runtime (about 51 min for the batch) and every remaining decision in one\n  table, with values and reasons, for approval together ([recovery-part-a.md](recovery-part-a.md),\n  sections 8, 10–12).\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"outline: applied\", len(reps))\n\nfor name in (\"docs/recovery-part-a.md\", \"docs/recovery-experiments.md\"):\n    import subprocess\n    diff = subprocess.run([\"git\", \"diff\", \"-U0\", name], capture_output=True, text=True).stdout\n    long = [l for l in diff.splitlines() if l.startswith(\"+\") and not l.startswith((\"+++\", \"+|\")) and len(l) - 1 > 100]\n    print(name, \"added prose lines over 100 characters:\", len(long))\nEOF",
  "description": "Put the decisions table in Part A and record the exit fix in both docs"
}
```

## 61. User — 2026-10-25T04:30:38.692Z

### Tool result

```
Part A: applied 4
outline: applied 4
docs/recovery-part-a.md added prose lines over 100 characters: 4
docs/recovery-experiments.md added prose lines over 100 characters: 0
```

## 62. Assistant — 2026-10-25T04:30:43.766Z

### Tool call: Bash

```
{
  "command": "git diff -U0 docs/recovery-part-a.md | grep '^+' | grep -v '^+++\\|^+|' | awk '{ if (length($0) > 101) print }' | cut -c1-130; python3 -c \"\nimport subprocess\nd = subprocess.run(['git','diff','-U0','docs/recovery-part-a.md'],capture_output=True,text=True).stdout\nfor l in d.splitlines():\n    if l.startswith('+') and not l.startswith(('+++','+|')) and len(l)-1 > 100: print(len(l)-1, repr(l[:70]))\n\"",
  "description": "Show which added Part A lines are over 100 characters"
}
```

## 63. User — 2026-10-25T04:30:44.584Z

### Tool result

```
+pgrep -lf 'pytest|etf_risk\.jobs|org\.apache\.spark'           # must print nothing (section 12, condition 4)
+uv run --group jobs python -c "import psutil; print(psutil.virtual_memory().available / 2**30)"   # GiB (section 12)
+    --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/outputs-recovery/formal/batch-1 --formal
+#    required check that failed or is unknown gives 1 (a battery reading, a closed lid, a missing one)
+`crosscheck/Q0–Q3b.csv` and `export/`, and the files `status-check.txt` and `cleanup.txt`. It exits
+pressure: 1.2–1.7 GiB of 8 GiB available before each job, as recorded, and 4–10 GiB of swap in use
+- **Native processes, informational:** across preflight-2 and -3 the step trees peaked at 0.09–0.12
+  under the host lock. The C0 jobs' steps took 44.3–50.4 s in preflight-2 and -3 (and 42.8–48.4 s
+    depend on time or memory: every job that ran kept it (preflights 2–4), under memory pressure and
109 "+pgrep -lf 'pytest|etf_risk\\.jobs|org\\.apache\\.spark'           # must"
116 '+uv run --group jobs python -c "import psutil; print(psutil.virtual_me'
108 '+    --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/o'
102 '+#    required check that failed or is unknown gives 1 (a battery read'
```

## 64. Assistant — 2026-10-25T04:30:58.180Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nreps = [\n(\"#    required check that failed or is unknown gives 1 (a battery reading, a closed lid, a missing one)\\n\",\n \"#    required check that failed or is unknown gives 1 (battery, a closed lid, a missing reading)\\n\"),\n(\"#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json)\\n\",\n \"#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json).\\n\"\n \"#    <SEED> is the approved seed (section 10, row 2).\\n\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:60]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"applied\", len(reps))\nEOF\nsed -n 196,214p docs/recovery-part-a.md; uv run --group jobs python -m pytest tests/test_jobs_harness.py tests/test_recovery_sql.py tests/test_recovery_collector.py tests/test_recovery_synthetic.py tests/test_provenance.py tests/test_jobs_kafka.py -q 2>&1 | tail -1",
  "description": "Tidy the command comments and rerun the tests that read the docs"
}
```

## 65. User — 2026-10-25T04:31:33.958Z

### Tool result

````
applied 2
# 2. Formal batch: only after the author approves Part A. The default plan is the preferred draft:
#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json).
#    <SEED> is the approved seed (section 10, row 2).
uv run --group jobs python -m etf_risk.jobs.harness plan --purpose formal --seed <SEED> \
    --out data/outputs-recovery/formal/plan-<SEED>.json
uv run --group jobs python -m etf_risk.jobs.harness estimate --plan data/outputs-recovery/formal/plan-<SEED>.json
caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
    --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/outputs-recovery/formal/batch-1 --formal

# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two
#    verdicts, correctness observations and recovery times, and exits 1 unless both are valid: any
#    required check that failed or is unknown gives 1 (battery, a closed lid, a missing reading)
uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/formal/batch-1

# 4. Cleanup: the batch itself ends with `docker compose down -v`; check, and recover if it was killed
docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
docker compose -f docker/compose.yaml down -v                  # only if something was left
```

74 passed, 11 skipped, 185 warnings in 33.35s
````

## 66. Assistant — 2026-10-25T04:31:48.835Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nreps = [\n(\"| 2 | Seed | 544, written into the formal plan before it is generated, never redrawn | any fixed integer works; fixing it before the order is seen rules out choosing an order |\",\n \"| 2 | Seed | 544, given to `plan --seed` for the formal plan and never redrawn | any fixed integer works; fixing it now, before any formal order exists, rules out choosing an order |\"),\n(\"| 13 | Code for the formal batch | `fcaa645` (the commit of the approved documents adds no code); no further live preflight | since preflight-4 (`8c5331d`), only plan generation and the collector changed, both covered offline by their tests, the synthetic batch and mutations |\",\n \"| 13 | Code for the formal batch | `fcaa645` (the commit of the approved documents adds no code); no further live preflight | since preflight-4 (`8c5331d`), the tooling changed only in plan generation and the collector, both covered offline by their tests, the synthetic batch and mutations |\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:60]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"applied\", len(reps))\nEOF\nsed -n 262,288p docs/recovery-part-a.md | cut -c1-120; git status --short",
  "description": "Refine two table rows and proofread section 10"
}
```

## 67. User — 2026-10-25T04:31:49.770Z

### Tool result

```
applied 2

## 10. Author decisions

**Approved by the author on 2026-10-24:**
- this host, for correctness observations and for recovery times under its recorded conditions,
  with section 12's limitations;
- the two controls, one C0 at each end of the batch (30 jobs).

**Still open, proposed for approval together** (rows 11 and 13 are new in this draft):

| # | Decision | Proposed value | Rationale |
|---|---|---|---|
| 1 | Workload (P1) | one batch of 30 jobs: C0, 2 of each of the 14 cases in shuffled order (28), C0; the calendar-year 
| 2 | Seed | 544, given to `plan --seed` for the formal plan and never redrawn | any fixed integer works; fixing it now,
| 3 | Clock (P2) | the timing.py defaults, no override: lease 60 s, renewal 10 s, fence margin 10 s, session 15 s, heart
| 4 | Deadlines (P3) | D = ceil5(B + 2S), S = 35.1 s: 75 s (C0, W5a, W5b, K1, X1), 90 s (W1), 125 s (K2, from Kafka's re
| 5 | Harness waits | phase delay 3 s; W7 stop 90 s; outages 30 s (K2, D1, D2); a phase not reached in 300 s is a miss |
| 6 | Clock-check tolerance | 1 s | wall minus monotonic time drifted 0.018 and 0.028 s over whole batches; preflight-3'
| 7 | Injection method (P5) | the fault file at the named points for W1, W2, W4, W5a, W5b and D2, armed only on the part
| 8 | Memory (P4) | fresh containers for the batch; peaks read after every job; flag at 90% and stop the batch at 95% of
| 9 | Host protocol | section 12, conditions 1–7 | each answers preflight-3's failure (a sleep on battery with the lid
| 10 | A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labell
| 11 | The formal batch invalid or stopped early | kept and reported in full; one rerun with the same plan in `formal/ba
| 12 | A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both | as done for G9 (p
| 13 | Code for the formal batch | `fcaa645` (the commit of the approved documents adds no code); no further live prefli

## 11. Live preflight, 2026-10-24: functional validation only
 M docs/recovery-experiments.md
 M docs/recovery-part-a.md
```

## 68. Assistant — 2026-10-25T04:31:53.430Z

The table is in Part A §10 and the docs are uncommitted. Last step: updating the project memory note.

## 69. Assistant — 2026-10-25T04:32:04.152Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md",
  "content": "[REDACTED:memory]"
}
```

## 70. User — 2026-10-25T04:32:05.048Z

### Tool result

```
[REDACTED:memory]
```

## 71. Assistant — 2026-10-25T04:32:06.101Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Update the memory index pointer without printing the index"
}
```

## 72. User — 2026-10-25T04:32:06.861Z

### Tool result

```
[REDACTED:memory]
```

## 73. Assistant — 2026-10-25T04:33:02.452Z

The collector's exit status now follows its verdicts. I committed the fix and its tests by explicit path as `fcaa645`. The two documents stay uncommitted until you review the table below.

## Exit-status fix (`fcaa645`)

- **What changed:** a new `check_state()` in [collect_recovery_measurements.py](.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py) sorts each check into passed, failed or unknown. Only an explicit pass counts as passed.
  - A check that is missing, or has no result, is unknown.
  - So is a host condition whose only problem is missing readings.
- **The rule:** both verdicts and `validity_failed` use `check_state()`, and the exit status is 0 only when both verdicts are valid. Any required check that failed or is unknown now exits 1. The printed summary marks unknown checks, e.g. `host_power (unknown)`.
- **Regression test:** three cases — an unknown clock check, an unknown code identity, and a missing `host_lid` check. Each fails the right verdicts and exits 1.
- **Mutations:** two new ones. `exit-ignores-unknown` puts the old exit rule back; `missing-check-passes` lets a missing check pass. The new test catches both, and all 8 collector mutations I ran were caught.
- **Tests:** 74 passed, 11 skipped (the live Kafka cases), across the six test files that cover the collector, the harness and the docs.
- **Preflights:** I recomputed them without writing anything; the 1,109 record files are unchanged. Preflights 1–3 exit 1 and preflight-4 exits 0. That's the same as before, because every current check already returns true or false.

## Remaining Part A decisions, for approval together

This table is also in [Part A §10](.claude/worktrees/recovery-harness/docs/recovery-part-a.md), word for word.

| # | Decision | Proposed value | Rationale |
|---|---|---|---|
| 1 | Workload (P1) | one batch of 30 jobs: C0, 2 of each of the 14 cases in shuffled order (28), C0; the calendar-year job on `full-2026-10-12`, `max_attempts` 3; results as counts per case (k of 2; C0 k of 4), no rates | every case and recovery path twice, with E1 checked on every job, in about 51 min; the 84-job alternative (2 batches of 42 plus their controls) takes about 2 h 29 min. No rates, since the injections are not shown to be independent |
| 2 | Seed | 544, given to `plan --seed` for the formal plan and never redrawn | any fixed integer works; fixing it now, before any formal order exists, rules out choosing an order |
| 3 | Clock (P2) | the timing.py defaults, no override: lease 60 s, renewal 10 s, fence margin 10 s, session 15 s, heartbeat 3 s, reconciler 5 s, publication grace 30 s; step limits 120, 600 and 300 s, attempt 900 s | E2 times the configuration the job processes run with; E1's token guards do not depend on the clock; preflights 2–4 ran these values and every path behaved as designed |
| 4 | Deadlines (P3) | D = ceil5(B + 2S), S = 35.1 s: 75 s (C0, W5a, W5b, K1, X1), 90 s (W1), 125 s (K2, from Kafka's return), 140 s (W2, W3, W4, W6; D1 and D2 from MySQL's return), 170 s (W7); drain limit D; `max_lag_s` 1 s | B is the design's latest start of the next run; the four C0 times of preflights 2 and 4 (45.1–52.4 s) stay below 2S = 70.2 s, so P3's own rule keeps D; on time and late describe this host only |
| 5 | Harness waits | phase delay 3 s; W7 stop 90 s; outages 30 s (K2, D1, D2); a phase not reached in 300 s is a miss | 3 s puts the kill inside spark_pipeline, the longest step (6 of 6 mid-step injections made); 90 s outlasts the takeover (65 s), so W7's replacement waits for the stopped tree; 30 s outlasts the Kafka session (15 s) and brings MySQL back near F, so D1 and D2 can take either branch (preflight-2 showed both) |
| 6 | Clock-check tolerance | 1 s | wall minus monotonic time drifted 0.018 and 0.028 s over whole batches; preflight-3's sleep showed as 63.8 s and more |
| 7 | Injection method (P5) | the fault file at the named points for W1, W2, W4, W5a, W5b and D2, armed only on the partition's owner; signals from the harness for W3, W6 and W7; `docker compose` for K1's restart and the outages of K2, D1 and D2; a second publication for X1 | those six windows last milliseconds, too short for an outside signal; 14 of 14 injections in preflights 2–4 were made (the 6 fault-file ones included), none missed |
| 8 | Memory (P4) | fresh containers for the batch; peaks read after every job; flag at 90% and stop the batch at 95% of 512 MiB (MySQL) and 640 MiB (Kafka); host memory recorded, never gated | M2 validated these limits (under host pressure); the preflights peaked at 49–62% (MySQL) and 60–77% (Kafka); no measured host figure is tied to recovery behaviour |
| 9 | Host protocol | section 12, conditions 1–7 | each answers preflight-3's failure (a sleep on battery with the lid closed) or a confound; the collector checks 1–3, `pgrep` checks 4 before the start, 5 is recorded and 6 is the default plan |
| 10 | A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labelled as such | relabelling once a cause is known would let results pick the batches; the checks that do not involve time still hold (preflight-3) |
| 11 | The formal batch invalid or stopped early | kept and reported in full; one rerun with the same plan in `formal/batch-2` once the cause is removed (a code fix gets a preflight of the affected cases first); both reported side by side | decided before any result is seen, so no batch is chosen afterwards; Part A had no rule for this |
| 12 | A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both | as done for G9 (preflight-1, then preflight-3) |
| 13 | Code for the formal batch | `fcaa645` (the commit of the approved documents adds no code); no further live preflight | since preflight-4 (`8c5331d`), the tooling changed only in plan generation and the collector, both covered offline by their tests, the synthetic batch and mutations |

- **Rows 11 and 13 are new.** Part A had no rule for an invalid or stopped formal batch, and didn't say which code it runs on.
- **The seed (row 2) is an arbitrary number I picked.** Any integer works, as long as it's fixed before the formal plan is made.
- **Other document changes:** §7's collection comment, §12's tooling list and the outline (1.1, 8.5, §9, revision 10) now describe the new exit rule.

I haven't run the formal batch, published a page, pushed, or committed any AI logs. The branch's commits are `772b647`, `7bd4d20`, `d675c85`, `a94eefe`, `8c5331d`, `5a81bc5` and `fcaa645`; none are pushed.

`★ Insight ─────────────────────────────────────`
- The exit status is now computed from the verdicts themselves, not from a separate list kept alongside them. The two can no longer drift apart, whatever checks are added later.
- No current check ever returns "no result", so the regression test fakes one in each case. It guards the rule: a future check that reports nothing when a record is missing can't quietly exit 0.
- Preflight-2 already exited 1, because missing power readings are reported as a fail. What's new is the guarantee and the `(unknown)` label, which keeps "failed" and "unknown" apart in the summary as well as in `validity.json`.
`─────────────────────────────────────────────────`
