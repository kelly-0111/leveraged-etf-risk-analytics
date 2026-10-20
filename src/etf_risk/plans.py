"""Final execution plans and AQE shuffle-read partition counts of one pipeline run.

`spark_pipeline --record-plans` (docs/partition-experiment.md 4.2) calls `watermark` once its
session has started and `capture` after the run's status is set, and writes the result to
plans.json in the run folder. Both read Spark's SQL status store through the JVM gateway. That is
an internal interface: the calls used here were checked on Spark 4.2.0, and plans.json records the
version.

For every SQL execution with an id above the watermark, `capture` keeps:
  - the phase: the job group of its jobs (the pipeline's phases, or bookkeeping);
  - its final physical plan text, in the format of spark.sql.ui.explainMode (Spark's default is
    formatted), and whether the plan is adaptive and, if so, final (`plan_status`);
  - each shuffle exchange's partitioning and requested partition count, from its node description,
    and its runtime metrics, among them "number of partitions" (the partitions it wrote);
  - each shuffle read that AQE marks (an AQEShuffleRead node): its mark (coalesced, local, skewed)
    and its metrics, among them "number of partitions", the partitions it actually read.
An unmarked shuffle read has no node of its own: it reads all of its exchange's partitions.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_partition_options.py
and on a small window set (docs/partition-experiment.md 4.5).
"""
from __future__ import annotations

import re
import time
from collections.abc import Sequence

FORMAT = 1
DEFAULT_TIMEOUT_S = 60.0
JOIN_NODES = ("SortMergeJoin", "BroadcastHashJoin", "ShuffledHashJoin", "BroadcastNestedLoopJoin", "CartesianProduct")
_FINAL = re.compile(r"isFinalPlan=(true|false)")
_PARTITIONED = re.compile(r"^Exchange (hashpartitioning|rangepartitioning)\(.*, (\d+)\)(?:, |$)")


class PlanCaptureError(RuntimeError):
    """The status store did not give a complete set of finished, final plans in time."""


def plan_status(text: str) -> tuple[bool, bool | None]:
    """(adaptive, final). A plan is adaptive when it has an AdaptiveSparkPlan node, and final when every
    such node is. Finality applies only to adaptive plans: for the others it is None."""
    flags = _FINAL.findall(text)
    return (True, all(flag == "true" for flag in flags)) if flags else (False, None)


def exchange_partitioning(desc: str) -> tuple[str, int | None]:
    """A shuffle exchange's partitioning and requested count, from its node description:
    ('hashpartitioning' or 'rangepartitioning', n), ('single', None) or ('other', None)."""
    if match := _PARTITIONED.match(desc):
        return match.group(1), int(match.group(2))
    return ("single", None) if desc.startswith("Exchange SinglePartition") else ("other", None)


def read_mark(desc: str) -> str:
    """'AQEShuffleRead coalesced' -> 'coalesced'; '' when AQE gave the read no mark."""
    return desc.removeprefix("AQEShuffleRead").strip()


def metric_count(value: str | None) -> int | None:
    """A count metric as Spark formats it, with thousands separators ('1,000'); None if absent."""
    try:
        return int(value.replace(",", "")) if value is not None else None
    except ValueError:
        return None


def _converters(spark):
    return spark._jvm.scala.jdk.javaapi.CollectionConverters


def _store(spark):
    return spark._jsparkSession.sharedState().statusStore()


def wait_for_listeners(spark, timeout_s: float) -> None:
    """Block until Spark's listener bus has delivered every event posted so far; raises on timeout."""
    spark.sparkContext._jsc.sc().listenerBus().waitUntilEmpty(max(int(timeout_s * 1000), 1))


def watermark(spark, timeout_s: float = DEFAULT_TIMEOUT_S) -> int:
    """The highest SQL execution id in the status store once the listeners have caught up, or -1.
    The executions after it belong to the run that took the watermark."""
    wait_for_listeners(spark, timeout_s)
    return max((int(e.executionId()) for e in _converters(spark).asJava(_store(spark).executionsList())),
               default=-1)


def capture(spark, after_id: int, groups: Sequence[str], timeout_s: float = DEFAULT_TIMEOUT_S,
            poll_s: float = 0.2) -> dict:
    """The plans document for the executions after `after_id`. Waits until every one has finished and
    every adaptive plan is final, and raises PlanCaptureError if that takes longer than `timeout_s`."""
    deadline = time.monotonic() + timeout_s
    wait_for_listeners(spark, timeout_s)
    conv, store = _converters(spark), _store(spark)
    while True:
        executions = sorted((e for e in conv.asJava(store.executionsList()) if int(e.executionId()) > after_id),
                            key=lambda e: int(e.executionId()))
        pending = [int(e.executionId()) for e in executions
                   if not e.completionTime().isDefined() or plan_status(e.physicalPlanDescription())[1] is False]
        if not pending:
            break
        if time.monotonic() >= deadline:
            raise PlanCaptureError(f"executions not finished or without a final plan after {timeout_s:.0f} s: {pending}")
        time.sleep(poll_s)
        wait_for_listeners(spark, deadline - time.monotonic())
    tracker = spark.sparkContext.statusTracker()
    group_of = {int(job): group for group in groups for job in tracker.getJobIdsForGroup(group)}
    return {
        "format": FORMAT,
        "spark_version": spark.version,
        "explain_mode": spark.conf.get("spark.sql.ui.explainMode"),
        "first_execution_id": after_id + 1,
        "executions": [_execution(conv, store, e, group_of) for e in executions],
    }


def _execution(conv, store, e, group_of: dict[int, str]) -> dict:
    execution_id = int(e.executionId())
    jobs = sorted(int(job) for job in conv.asJava(e.jobs()).keySet())
    groups = sorted({group_of[job] for job in jobs if job in group_of})
    text = e.physicalPlanDescription()
    adaptive, final = plan_status(text)
    error = e.errorMessage().get() if e.errorMessage().isDefined() else ""     # "" when it succeeded
    values = dict(conv.asJava(store.executionMetrics(execution_id)))
    exchanges, reads, joins = [], [], []
    for node in conv.asJava(store.planGraph(execution_id).allNodes()):
        name, desc = node.name(), node.desc()
        if name in ("Exchange", "AQEShuffleRead"):
            metrics = {m.name(): values.get(m.accumulatorId()) for m in conv.asJava(node.metrics())}
            partitions = metric_count(metrics.get("number of partitions"))
        if name == "Exchange":       # "partitions": the count it wrote at runtime, next to the requested one
            partitioning, requested = exchange_partitioning(desc)
            exchanges.append({"partitioning": partitioning, "requested": requested, "partitions": partitions,
                              "metrics": metrics, "desc": desc})
        elif name == "AQEShuffleRead":
            reads.append({"mark": read_mark(desc), "partitions": partitions, "metrics": metrics})
        elif name in JOIN_NODES:
            joins.append(name)
    return {
        "id": execution_id, "phase": "+".join(groups), "jobs": jobs, "error": error or None,
        "adaptive": adaptive, "final": final, "exchanges": exchanges, "shuffle_reads": reads, "joins": joins,
        "plan": text,
    }
