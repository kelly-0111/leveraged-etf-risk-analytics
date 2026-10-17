"""Memory sampler, run status rules, and the protocol stop rule.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import sys
import time

from etf_risk.measure import TreeSampler, run_protocol, run_status


def test_sampler_reports_a_positive_peak_for_this_process():
    sampler = TreeSampler(os.getpid(), interval=0.05)
    sampler.start()
    time.sleep(0.3)
    sampler.stop()
    assert sampler.samples >= 2 and sampler.peak_total > 0 and sampler.peak_by_kind["driver"] > 0
    assert not sampler.exceeded


def test_status_rules():
    assert run_status(0, False) == ("ok", [])
    assert run_status(0, True) == ("memory_threshold_exceeded", ["memory_threshold_exceeded"])
    assert run_status(1, False) == ("checks_failed", ["checks_failed"])
    assert run_status(3, True) == ("failed", ["failed (exit code 3)", "memory_threshold_exceeded"])
    assert run_status(-9, False)[0] == "failed"                       # killed by a signal


def protocol(tmp_path, code="import time; time.sleep(0.3)", **kwargs):
    def make_command(run_id):
        (tmp_path / run_id).mkdir()
        (tmp_path / run_id / "run.json").write_text(json.dumps({"run_id": run_id, "status": "ok"}))
        return [sys.executable, "-c", code]
    return run_protocol(make_command, lambda run_id: tmp_path / run_id, tmp_path, interval=0.05, **kwargs)


def test_threshold_crossing_stops_later_runs_but_not_the_current_one(tmp_path):
    result = protocol(tmp_path, code="import time; time.sleep(0.4); print('finished')",
                      repeats=3, threshold_fraction=1e-12)
    assert result["runs_started"] == 1 and result["stopped_early"]
    assert result["runs"][0]["status"] == "memory_threshold_exceeded"
    assert "finished" in (tmp_path / f"{result['runs'][0]['run_id']}.log").read_text()     # ran to completion
    record = json.loads((tmp_path / result["runs"][0]["run_id"] / "run.json").read_text())
    assert record["measurement"]["protocol_status"] == "memory_threshold_exceeded"
    assert record["measurement"]["limits"]                                                 # limits stated


def test_failed_run_stops_the_protocol(tmp_path):
    result = protocol(tmp_path, code="raise SystemExit(2)", repeats=3, threshold_fraction=1.0)
    assert result["runs_started"] == 1 and result["runs"][0]["status"] == "failed"


def test_summary_excludes_the_warmup_run(tmp_path):
    result = protocol(tmp_path, repeats=3, threshold_fraction=1.0)
    assert not result["stopped_early"] and result["runs_started"] == 3
    assert result["runs"][0]["warmup"] and not result["runs"][1]["warmup"]
    summary = result["summary_over_measured_runs"]
    assert summary["runs"] == [r["run_id"] for r in result["runs"][1:]]
    assert "source_sha256" in result["code"] and any("different moments" in line for line in result["limits"])
    assert summary["wall_seconds"]["min"] <= summary["wall_seconds"]["median"] <= summary["wall_seconds"]["max"]
