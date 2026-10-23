"""Memory sampler, process types, run status rules, and the protocol stop rule.

The process types are checked deterministically on stand-in processes with fixed names, command lines and
memory, among them a sample taken while a `java -version` helper runs: the case that made
tests/test_pandas_pipeline.py's measurement test fail intermittently when such a helper counted as the Spark
JVM. A real Spark JVM, the test session's, is checked as well.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import sys
import time
from types import SimpleNamespace

import psutil
import pytest

from etf_risk.measure import PROCESS_KINDS, TreeSampler, process_kind, run_protocol, run_status

MIB = 2**20
SPARK_JVM = ["/usr/bin/java", "-cp", "/spark/conf/:/spark/jars/*", "-Xmx1g", "org.apache.spark.deploy.SparkSubmit",
             "--master", "local[2]", "pyspark-shell"]
SPARK_LAUNCHER = ["/usr/bin/java", "-Xmx128m", "-cp", "/spark/jars/*", "org.apache.spark.launcher.Main",
                  "org.apache.spark.deploy.SparkSubmit", "pyspark-shell"]
HELPERS = {"java": ["java", "-version"], "git": ["git", "-C", "/repo", "rev-parse", "HEAD"], "uname": ["uname", "-p"],
           "file": ["file", "-b", "/usr/bin/python3"]}          # what the pipelines start for their run record


class FakeProcess:
    """A psutil.Process stand-in: a fixed pid, name, command line and RSS, and its descendants."""

    def __init__(self, pid, name, cmdline, rss, descendants=()):
        self.pid, self._name, self._cmdline, self._rss, self._descendants = pid, name, cmdline, rss, list(descendants)

    def name(self):
        return self._name

    def cmdline(self):
        return self._cmdline

    def memory_info(self):
        return SimpleNamespace(rss=self._rss)

    def children(self, recursive=False):
        return self._descendants


def test_sampler_reports_a_positive_peak_for_this_process():
    sampler = TreeSampler(os.getpid(), interval=0.05)
    sampler.start()
    time.sleep(0.3)
    sampler.stop()
    assert sampler.samples >= 2 and sampler.peak_total > 0 and sampler.peak_by_kind["driver"] > 0
    assert not sampler.exceeded


def test_a_java_process_is_the_spark_jvm_only_if_its_command_line_runs_spark():
    root = FakeProcess(100, "python3.12", ["python", "-m", "etf_risk.pandas_pipeline"], MIB)
    assert process_kind(root, root.pid) == "driver"
    assert {name: process_kind(FakeProcess(101, name, cmdline, MIB), root.pid) for name, cmdline in HELPERS.items()} \
        == {"java": "other", "git": "other", "uname": "other", "file": "other"}
    assert process_kind(FakeProcess(102, "java", SPARK_JVM, MIB), root.pid) == "spark_jvm"
    assert process_kind(FakeProcess(103, "java", SPARK_LAUNCHER, MIB), root.pid) == "spark_jvm"
    assert process_kind(FakeProcess(104, "python3.12", ["python", "-m", "pyspark.daemon"], MIB), root.pid) \
        == "python_worker"


def test_a_sample_during_java_version_records_other_while_a_spark_jvm_still_counts():
    helper = FakeProcess(201, "java", HELPERS["java"], 30 * MIB)
    pandas_run = FakeProcess(200, "python3.12", ["python", "-m", "etf_risk.pandas_pipeline"], 100 * MIB, [helper])
    sampler = TreeSampler(pandas_run.pid)
    assert sampler.sample(pandas_run)              # the sample that used to record a spark_jvm for the pandas run
    assert sampler.peak_by_kind == {"driver": 100 * MIB, "other": 30 * MIB} and sampler.max_processes == 2
    jvm = FakeProcess(301, "java", SPARK_JVM, 900 * MIB)
    spark_run = FakeProcess(300, "python3.12", ["python", "-m", "etf_risk.spark_pipeline"], 120 * MIB, [jvm, helper])
    sampler = TreeSampler(spark_run.pid)
    assert sampler.sample(spark_run)
    assert sampler.peak_by_kind == {"driver": 120 * MIB, "spark_jvm": 900 * MIB, "other": 30 * MIB}
    assert sampler.peak_total == 1050 * MIB


def test_a_sample_of_a_finished_process_ends_the_sampling():
    class Finished(FakeProcess):
        def children(self, recursive=False):
            raise psutil.NoSuchProcess(self.pid)

    sampler = TreeSampler(400)
    assert not sampler.sample(Finished(400, "python3.12", [], MIB)) and sampler.samples == 0


@pytest.mark.spark
def test_the_spark_jvm_of_this_test_session_counts_as_spark_jvm(spark):
    sampler = TreeSampler(os.getpid())
    assert sampler.sample(psutil.Process()) and sampler.peak_by_kind["spark_jvm"] > 0


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
    assert record["measurement"]["process_kinds"] == PROCESS_KINDS                         # and the types' rule


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
    assert result["process_kinds"] == PROCESS_KINDS
    assert summary["wall_seconds"]["min"] <= summary["wall_seconds"]["median"] <= summary["wall_seconds"]["max"]
