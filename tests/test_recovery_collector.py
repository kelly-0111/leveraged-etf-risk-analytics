"""The recovery collector (analysis/collect_recovery_measurements.py) on synthetic batch folders:
the metrics of section 5 with their n/a reasons, unknown intervals, the per-case tally with
zeros, and validity apart from outcomes.

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


def utc(mono):
    return (BASE + timedelta(seconds=mono - 1000)).isoformat()


def write_jsonl(path, events):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(e) + "\n" for e in events))


def launcher(folder, step, start, end, *, mono=True):
    """A launcher record; mono=False writes UTC times only, as the launcher did at 6d8a232."""
    record = {"outcome": "exited", "step_started_at_utc": utc(start), "tree_ended_at_utc": utc(end)}
    if mono:
        record.update(step_started_mono=float(start), tree_ended_mono=float(end))
    (folder / "logs").mkdir(parents=True, exist_ok=True)
    (folder / "logs" / f"{step}.launcher.json").write_text(json.dumps(record))


def edit_harness(batch, change):
    """Rewrite harness.jsonl through change(event), which returns the event, a new one, or None."""
    events = [json.loads(line) for line in (batch / "harness.jsonl").read_text().splitlines()]
    write_jsonl(batch / "harness.jsonl", [e for e in map(change, events) if e is not None])


def write_csv(path, header, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def host_reading(stage, position=None, *, power="AC Power", lid_closed=False, other_containers=0):
    """A host_state event as the harness writes it (docs/recovery-part-a.md, section 12)."""
    e = {"event": "host_state", "stage": stage, "available_bytes": 2 * 2**30, "total_bytes": 8 * 2**30,
         "swap_used_bytes": 0, "swap_in_bytes": 0, "swap_out_bytes": 0, "memory_pressure": 1,
         "power_source": power, "lid_closed": lid_closed, "other_containers": other_containers}
    return e if position is None else {**e, "position": position}


def make_batch(tmp_path, *, step_code=CODE, host=True):
    """Four planned jobs: C0 and W3 on worker A, W5a on B, and a K2 that memory stopped."""
    b = tmp_path / "batch"
    dates = nyse_sessions("2024-01-02", 31)
    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(3).normal(0, 0.01, 30))})
    checksums = input_checksums(tmp_path / "processed", "snap")
    (b / "plan.json").parent.mkdir(parents=True)
    (b / "plan.json").write_text(json.dumps({"seed": 1, "settings": {"snapshot": "snap"},
                                             "jobs": ["C0", "W3", "W5a", "K2"]}))
    write_jsonl(b / "harness.jsonl", [
        {"event": "batch_started", "mono": 1000.0, "clock": {"ts": utc(1000), "mono": 1000.0}, "code": CODE},
        *[{"event": "process_started", "name": n, "same_clock": True, "code": CODE, "mono": 1001.0}
          for n in ("reconciler", "A", "B")],
        {"event": "deadline", "position": 1, "job_id": 1, "case": "C0", "reference": "submit", "reference_mono": 1010.0,
         "deadline_s": 75, "deadline_mono": 1085.0, "t_submit": 1010.0},
        {"event": "injection", "position": 1, "job_id": 1, "case": "C0", "missed": None},
        {"event": "deadline", "position": 2, "job_id": 2, "case": "W3", "reference": "injection",
         "reference_mono": 1120.0, "deadline_s": 140, "deadline_mono": 1260.0, "t_submit": 1100.0},
        {"event": "injection", "position": 2, "job_id": 2, "case": "W3", "missed": None, "kind": "sigkill",
         "worker": "A", "attempt": 1, "t_inj": 1120.0},
        {"event": "deadline", "position": 3, "job_id": 3, "case": "W5a", "reference": "injection",
         "reference_mono": 1300.0, "deadline_s": 75, "deadline_mono": 1375.0, "t_submit": 1260.0},
        {"event": "injection", "position": 3, "job_id": 3, "case": "W5a", "missed": None, "kind": "hook",
         "worker": "B", "point": "after_accept_commit", "t_inj": 1300.0},
        {"event": "not_run", "position": 4, "case": "K2", "why": "memory"},
        {"event": "quiescent", "processes_left": False, "other_connections": 0},
        {"event": "final_snapshot", "status_check_exit": 0, "fingerprints_agree": True, "fingerprints": [],
         "batch_peaks": {}},
        {"event": "batch_ended", "mono": 1600.0, "clock": {"ts": utc(1600), "mono": 1600.0}, "code": CODE}])
    step = {"event": "step_started", "code": step_code}
    write_jsonl(b / "events" / "A.jsonl", [
        {"event": "started", "pid": 11, "mono": 1001.0, "code": CODE}, {"event": "assigned", "mono": 1002.0,
                                                                          "partitions": [["t", 0]]},
        {"event": "delivered", "job_id": 1, "mono": 1010.5},
        {"event": "claimed", "job_id": 1, "attempt": 1, "run_id": "job-1-attempt-1", "mono": 1011.0},
        {**step, "job_id": 1, "attempt": 1, "step": "windows", "mono": 1012.0},
        {**step, "job_id": 1, "attempt": 1, "step": "spark_pipeline", "mono": 1015.0},
        {**step, "job_id": 1, "attempt": 1, "step": "verify", "mono": 1040.0},
        {"event": "accepted", "job_id": 1, "attempt": 1, "digest": "a" * 64, "mono": 1050.0, "store_id": STORE,
         "worker_id": "A", "pid": 11},
        {"event": "delivered", "job_id": 2, "mono": 1100.5},
        {"event": "claimed", "job_id": 2, "attempt": 1, "run_id": "job-2-attempt-1", "mono": 1101.0},
        {**step, "job_id": 2, "attempt": 1, "step": "windows", "mono": 1102.0},
        {**step, "job_id": 2, "attempt": 1, "step": "spark_pipeline", "mono": 1105.0}])
    write_jsonl(b / "events" / "B.jsonl", [
        {"event": "started", "pid": 22, "mono": 1001.5, "code": CODE}, {"event": "assigned", "mono": 1003.0,
                                                                          "partitions": []},
        {"event": "assigned", "mono": 1136.0, "partitions": [["t", 0]]},
        {"event": "claimed", "job_id": 2, "attempt": 2, "run_id": "job-2-attempt-2", "mono": 1180.0},
        {**step, "job_id": 2, "attempt": 2, "step": "windows", "mono": 1181.0},
        {**step, "job_id": 2, "attempt": 2, "step": "spark_pipeline", "mono": 1184.0},
        {**step, "job_id": 2, "attempt": 2, "step": "verify", "mono": 1210.0},
        {"event": "accepted", "job_id": 2, "attempt": 2, "digest": "b" * 64, "mono": 1225.0, "store_id": STORE,
         "worker_id": "B", "pid": 22},
        {"event": "delivered", "job_id": 3, "mono": 1260.5},
        {"event": "claimed", "job_id": 3, "attempt": 1, "run_id": "job-3-attempt-1", "mono": 1261.0},
        {**step, "job_id": 3, "attempt": 1, "step": "windows", "mono": 1262.0},
        {**step, "job_id": 3, "attempt": 1, "step": "spark_pipeline", "mono": 1265.0},
        {**step, "job_id": 3, "attempt": 1, "step": "verify", "mono": 1290.0},
        {"event": "fault_injected", "point": "after_accept_commit", "action": "kill", "mono": 1300.0}])
    write_jsonl(b / "events" / "reconciler-33.jsonl", [
        {"event": "started", "mono": 1001.0, "code": CODE}, {"event": "requeued", "job_id": 2, "mono": 1175.0},
        {"event": "published", "job_id": 2, "mono": 1175.5}])
    write_jsonl(b / "events" / "submit.jsonl", [{"event": "started", "mono": m, "code": CODE} for m in (1010, 1100, 1260)])
    jobs = b / "jobs" / STORE
    for run_id, steps in {"job-1-attempt-1": [("windows", 1012, 1015), ("spark_pipeline", 1015, 1040),
                                              ("verify", 1040, 1049)],
                          "job-2-attempt-1": [("windows", 1102, 1105), ("spark_pipeline", 1105, 1121)],
                          "job-2-attempt-2": [("windows", 1181, 1184), ("spark_pipeline", 1184, 1210),
                                              ("verify", 1210, 1224)],
                          "job-3-attempt-1": [("windows", 1262, 1265), ("spark_pipeline", 1265, 1290),
                                              ("verify", 1290, 1299)]}.items():
        for name, start, end in steps:
            launcher(jobs / run_id, name, start, end)
    for run_id in ("job-1-attempt-1", "job-2-attempt-2", "job-3-attempt-1"):
        (jobs / run_id / "manifest.json").write_text("{}")
    launcher(b / "reference", "windows", 990, 993)
    launcher(b / "reference", "spark_pipeline", 993, 999)
    write_csv(b / "crosscheck" / "Q1.csv", ["job_id", "n_claims", "n_accepted", "verdict"],
              [[1, 1, 1, "ok"], [2, 2, 1, "ok"], [3, 1, 1, "ok"]])
    write_csv(b / "crosscheck" / "Q2.csv", ["case_id", "job_id", "timeliness", "deadline_met"],
              [["C0", 1, "on time", "yes"], ["W3", 2, "on time", "yes"], ["W5a", 3, "on time", "yes"]])
    write_csv(b / "crosscheck" / "Q3a.csv", ["job_id", "log_verdict"],
              [[1, "reported once"], [2, "reported once"], [3, "no matching report"]])
    write_csv(b / "crosscheck" / "Q3b.csv", ["store_id", "worker_id", "pid", "job_id", "attempt_number", "report_verdict"],
              [[STORE, "A", 11, 1, 1, "matches"], [STORE, "B", 22, 2, 2, "matches"]])
    write_csv(b / "crosscheck" / "Q2b.csv", ["job_id", "status"], [])
    export = b / "export"
    export.mkdir()
    (export / "jobs.json").write_text(json.dumps([{"job_id": j, "version": 4, "input_checksums": checksums}
                                                  for j in (1, 2, 3)]))
    (export / "job_attempts.json").write_text(json.dumps([
        {"job_id": 1, "attempt_number": 1, "outcome": "accepted", "renewals": 2, "output_dir": str(jobs / "job-1-attempt-1"),
         "result_digest": "a" * 64},
        {"job_id": 2, "attempt_number": 1, "outcome": "expired", "renewals": 1, "output_dir": str(jobs / "job-2-attempt-1"),
         "result_digest": None},
        {"job_id": 2, "attempt_number": 2, "outcome": "accepted", "renewals": 2, "output_dir": str(jobs / "job-2-attempt-2"),
         "result_digest": "b" * 64},
        {"job_id": 3, "attempt_number": 1, "outcome": "accepted", "renewals": 2, "output_dir": str(jobs / "job-3-attempt-1"),
         "result_digest": "c" * 64}]))
    (export / "store.json").write_text(json.dumps({"store_id": STORE}))
    (export / "invariant_violations.json").write_text("{}")
    if host:                                    # on AC power with the lid open, at every reading the batch needs
        with open(b / "harness.jsonl", "a") as f:
            for e in (host_reading("start"), *(host_reading("job", p) for p in (1, 2, 3)), host_reading("end")):
                f.write(json.dumps(e) + "\n")
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


def test_a_launcher_record_without_monotonic_times_counts_as_missing(batch, tmp_path):
    """A record with UTC times only gives no interval: the overlap check never falls back to UTC."""
    launcher(batch / "jobs" / STORE / "job-2-attempt-1", "windows", 1102, 1105, mono=False)
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    overlap = result["outcomes"]["overlap"]
    assert overlap["verdict"] == "unknown" and overlap["steps_without_interval"] == ["job-2-attempt-1:windows"]
    assert str({r["position"]: r for r in result["rows"]}[2]["wasted_step_s"]).startswith("unknown")


def test_every_interval_that_overlaps_an_earlier_one_is_listed(batch, tmp_path):
    launcher(batch / "jobs" / STORE / "job-2-attempt-2", "windows", 1103, 1184)      # inside attempt 1's steps
    launcher(batch / "jobs" / STORE / "job-2-attempt-2", "spark_pipeline", 1110, 1210)
    overlap = crm.collect(batch, processed_root=tmp_path / "processed")["outcomes"]["overlap"]
    assert overlap["verdict"] == "overlap" and overlap["overlaps"] == [               # verify starts as spark ends
        ("job-2-attempt-1:windows", "job-2-attempt-2:windows"),
        ("job-2-attempt-2:windows", "job-2-attempt-1:spark_pipeline"),
        ("job-2-attempt-2:windows", "job-2-attempt-2:spark_pipeline")]


def test_an_injection_record_without_its_time_leaves_its_latencies_unknown(batch, tmp_path):
    def drop_w3_time(e):
        if e["event"] == "injection" and e.get("case") == "W3":
            return {k: v for k, v in e.items() if k != "t_inj"}
        return e

    edit_harness(batch, drop_w3_time)
    w3 = {r["position"]: r for r in crm.collect(batch, processed_root=tmp_path / "processed")["rows"]}[2]
    assert w3["status"] == "made"
    assert (w3["detection_s"], w3["rerun_s"], w3["finish_s"]) == ("unknown: no injection time",) * 3
    assert w3["overhead_s"] == 85.0                                 # from the submit, which the deadline keeps


def test_a_job_without_its_injection_record_is_counted_apart_never_as_made(batch, tmp_path):
    edit_harness(batch, lambda e: None if e["event"] == "injection" and e.get("case") == "W3" else e)
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    w3 = {r["position"]: r for r in result["rows"]}[2]
    assert w3["status"] == "no injection record" and w3["detection_s"] == "unknown: no injection time"
    injections = result["validity"]["injections"]
    assert (injections["made"], injections["unrecorded"], injections["not_run"]) == (2, [2], [4])
    tally = {t["case"]: t for t in result["tally"]}
    assert (tally["W3"]["made"], tally["W3"]["unrecorded"]) == (0, 1)
    assert all(t["planned"] == t["made"] + t["missed"] + t["not_run"] + t["unrecorded"] for t in tally.values())


def test_d2_is_detected_by_its_retried_acceptance_or_by_no_acceptance_after_f(batch, tmp_path):
    """The K2 position becomes a D2 whose hold ended after F: no retry, a fenced event at acceptance."""
    plan = json.loads((batch / "plan.json").read_text())
    (batch / "plan.json").write_text(json.dumps({**plan, "jobs": ["C0", "W3", "W5a", "D2"]}))
    edit_harness(batch, lambda e: None if e["event"] == "not_run" else e)
    with open(batch / "harness.jsonl", "a") as f:
        for e in ({"event": "deadline", "position": 4, "job_id": 4, "case": "D2", "reference": "restored",
                   "reference_mono": 1420.0, "deadline_s": 140, "deadline_mono": 1560.0, "t_submit": 1350.0},
                  {"event": "injection", "position": 4, "job_id": 4, "case": "D2", "missed": None,
                   "kind": "hold+service_stop", "worker": "A", "t_inj": 1400.0, "restored": 1420.0}):
            f.write(json.dumps(e) + "\n")
    with open(batch / "events" / "A.jsonl", "a") as f:
        for e in ({"event": "claimed", "job_id": 4, "attempt": 1, "run_id": "job-4-attempt-1", "mono": 1351.0},
                  {"event": "fenced", "job_id": 4, "attempt": 1, "during": "acceptance", "mono": 1430.0}):
            f.write(json.dumps(e) + "\n")
    with open(batch / "events" / "B.jsonl", "a") as f:
        f.write(json.dumps({"event": "claimed", "job_id": 4, "attempt": 2, "run_id": "job-4-attempt-2",
                            "mono": 1500.0}) + "\n")
    d2 = {r["position"]: r for r in crm.collect(batch, processed_root=tmp_path / "processed")["rows"]}[4]
    assert (d2["status"], d2["detection_s"], d2["rerun_s"]) == ("made", 30.0, 100.0)


def test_the_purpose_comes_from_the_plan_and_heads_every_summary(batch, tmp_path, capsys):
    assert crm.collect(batch, processed_root=tmp_path / "processed")["purpose"] == "not recorded"
    plan = json.loads((batch / "plan.json").read_text())
    (batch / "plan.json").write_text(json.dumps({**plan, "purpose": "preflight"}))
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "purpose: preflight (a preflight: not a formal result)"
    assert json.loads((batch / "validity.json").read_text())["purpose"] == "preflight"


def test_host_memory_spark_scratch_and_the_cleanup_listing_are_reported(tmp_path):
    batch = make_batch(tmp_path, host=False)                   # memory-only readings, as before host_state
    with open(batch / "harness.jsonl", "a") as f:
        for position, available in ((1, 3 * 2**30), (2, 2 * 2**30), (3, 2**30)):
            f.write(json.dumps({"event": "host_memory", "position": position, "available_bytes": available,
                                "total_bytes": 8 * 2**30}) + "\n")
    edit_harness(batch, lambda e: {**e, "spark_scratch_new": ["/private/tmp/spark-x"]} if e["event"] == "quiescent" else e)
    (batch / "cleanup.txt").write_text("exit 0\ndry run: 0 folders (0.0 MiB) could be removed; nothing was deleted\n")
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    rows = {r["position"]: r for r in result["rows"]}
    assert [rows[p].get("host_available_bytes") for p in (1, 2, 3, 4)] == [3 * 2**30, 2 * 2**30, 2**30, None]
    host = result["outcomes"]["host_state"]                       # host_memory events, as recorded before host_state
    assert (host["jobs_with_a_reading"], host["min_available_bytes"], host["power_sources"]) == (3, 2**30, [])
    assert result["outcomes"]["nothing_left"]["spark_scratch_new"] == ["/private/tmp/spark-x"]
    assert result["outcomes"]["cleanup_listing"] == "cleanup.txt"


def test_a_recorded_setup_or_final_error_fails_validity(batch, tmp_path):
    with open(batch / "harness.jsonl", "a") as f:
        f.write(json.dumps({"event": "setup_error", "error": "RuntimeError: init-db: exit 1"}) + "\n")
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
    validity = json.loads((batch / "validity.json").read_text())
    assert "records_complete" in validity["validity_failed"]
    assert validity["validity"]["records_complete"]["setup_errors"] == ["RuntimeError: init-db: exit 1"]


def test_the_host_state_gives_each_job_its_swap_activity_power_and_pressure(tmp_path):
    batch = make_batch(tmp_path, host=False)
    gib, mib = 2**30, 2**20
    with open(batch / "harness.jsonl", "a") as f:
        for stage, position, swapped_out, power, pressure in (("start", None, 0, "AC Power", 1),
                                                              ("job", 1, 10, "AC Power", 1),
                                                              ("job", 2, 10, "Battery Power", 2),
                                                              ("job", 3, 50, "AC Power", 4),
                                                              ("end", None, 80, "AC Power", 1)):
            e = {"event": "host_state", "stage": stage, "available_bytes": 2 * gib, "total_bytes": 8 * gib,
                 "swap_used_bytes": swapped_out * mib, "swap_in_bytes": 0, "swap_out_bytes": swapped_out * mib,
                 "memory_pressure": pressure, "power_source": power, "lid_closed": position == 2}
            if position is not None:
                e["position"] = position
            f.write(json.dumps(e) + "\n")
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    rows = {r["position"]: r for r in result["rows"]}
    assert [rows[p]["swap_out_during_bytes"] for p in (1, 2, 3)] == [0, 40 * mib, 30 * mib]   # the last, to the end
    assert [(rows[p]["power_source"], rows[p]["memory_pressure"], rows[p]["lid_closed"]) for p in (1, 2, 3)] == [
        ("AC Power", 1, False), ("Battery Power", 2, True), ("AC Power", 4, False)]
    assert "power_source" not in rows[4]                              # K2 was not run: no reading
    assert result["outcomes"]["host_state"] == {
        "jobs_with_a_reading": 3, "power_sources": ["AC Power", "Battery Power"], "on_battery": [2], "lid_closed": [2],
        "other_containers_at": [], "max_memory_pressure": 4, "min_available_bytes": 2 * gib, "swap_used_change_bytes": 80 * mib,
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
    assert result["validity"]["other_containers"] == {"passed": False, "failed": [], "unknown": [3]}
    assert result["verdicts"]["timing"] == {"valid": False, "failed": ["host_power", "host_lid", "other_containers"]}
    assert result["verdicts"]["correctness"]["valid"] is True


def test_a_batch_from_before_the_power_readings_has_unknown_conditions(tmp_path):
    """Memory-only readings, as preflight-2 and -3 recorded them, say nothing of power or the lid."""
    batch = make_batch(tmp_path, host=False)
    with open(batch / "harness.jsonl", "a") as f:
        for position in (1, 2, 3):
            f.write(json.dumps({"event": "host_memory", "position": position, "available_bytes": 2**30}) + "\n")
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["host_power"]["unknown"] == ["start", 1, 2, 3, "end"]
    assert result["validity"]["other_containers"]["unknown"] == ["start", 1, 2, 3, "end"]
    assert result["verdicts"]["timing"]["valid"] is False and result["verdicts"]["correctness"]["valid"] is True


# The exit status follows the verdicts: a required check that failed or is unknown gives 1

HOST_LID_MISSING = {name: {"passed": True, "failed": [], "unknown": []} for name in ("host_power", "other_containers")}


@pytest.mark.parametrize("function, returns, check, invalid", [
    ("clock_check", {"passed": None}, "clock", {"timing"}),
    ("identity_check", {"passed": None}, "code_identity", {"correctness", "timing"}),
    ("host_conditions", HOST_LID_MISSING, "host_lid", {"timing"}),
])
def test_a_required_check_that_is_unknown_or_missing_fails_its_verdicts_and_exits_1(
        batch, tmp_path, monkeypatch, capsys, function, returns, check, invalid):
    monkeypatch.setattr(crm, function, lambda *args, **kwargs: returns)
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert {claim for claim, v in result["verdicts"].items() if not v["valid"]} == invalid
    assert all(result["verdicts"][claim]["failed"] == [check] for claim in invalid)
    assert result["validity_failed"] == [check]
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
    assert f"{check} (unknown)" in capsys.readouterr().out


# Condition 4's containers, at every reading (recorded since the formal batches of 2026-10-25)

def test_a_container_outside_the_project_fails_the_recovery_times_but_not_the_correctness(batch, tmp_path):
    set_reading(batch, 2, other_containers=1)
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["other_containers"] == {"passed": False, "failed": [2], "unknown": []}
    assert result["verdicts"] == {"correctness": {"valid": True, "failed": []},
                                  "timing": {"valid": False, "failed": ["other_containers"]}}
    assert result["outcomes"]["host_state"]["other_containers_at"] == [2]
    assert {r["position"]: r for r in result["rows"]}[2]["other_containers"] == 1
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1


def test_a_reading_without_the_container_count_is_unknown_and_fails(batch, tmp_path, capsys):
    set_reading(batch, "end", other_containers=None)                     # docker could not say
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert result["validity"]["other_containers"] == {"passed": False, "failed": [], "unknown": ["end"]}
    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
    assert "recovery times: INVALID: other_containers (unknown)" in capsys.readouterr().out


# The summary's Q1 line: a job without a Q1 row has an unknown verdict, never an ok one

def test_without_q1_rows_every_submitted_job_is_unknown_not_ok(batch, tmp_path, capsys):
    (batch / "crosscheck" / "Q1.csv").unlink()                          # the cross-check did not run
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert (result["outcomes"]["q1_not_ok"], result["outcomes"]["q1_missing"]) == ([], [1, 2, 3])
    crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")])
    out = capsys.readouterr().out
    assert "no Q1 rows: every submitted job's Q1 verdict is unknown" in out and "not ok: none" not in out


def test_a_job_missing_from_q1_is_listed_apart(batch, tmp_path):
    write_csv(batch / "crosscheck" / "Q1.csv", ["job_id", "n_claims", "n_accepted", "verdict"],
              [[1, 1, 1, "ok"], [3, 1, 1, "ok"]])
    result = crm.collect(batch, processed_root=tmp_path / "processed")
    assert crm.q1_summary(result["rows"], result["outcomes"]) == (
        "jobs whose Q1 verdict is not ok: none; jobs without a Q1 verdict: [2]")
    assert crm.q1_summary([], {"q1_missing": [], "q1_not_ok": []}) == "no job was submitted, so there is no Q1 verdict"
