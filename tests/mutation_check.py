"""Mutation checks of the job queue's guards and settings: break one on purpose, run the job
tests, and expect them to fail (docs/job-table.md, docs/job-queue.md).

    uv run --group jobs python tests/mutation_check.py --out <folder>       # SQLite and offline Kafka settings
    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \\
        uv run --group jobs python tests/mutation_check.py --out <folder>   # also MySQL and Kafka
    uv run --group jobs python tests/mutation_check.py --list
    uv run --group jobs python tests/mutation_check.py --only renew-token rewind

Each mutation replaces one exact piece of source text, which must occur exactly once. The
work happens in a scratch copy of the repository (src/, tests/, analysis/, docs/recovery-sql.md,
pyproject.toml, uv.lock) with its own environment (uv sync --frozen --group jobs), never in this
checkout. Each mutation runs the tests it names: the job tests, unless it is one of the focused
mutations below. All the tests the selected mutations name first run unmutated and must pass.
Then, for each mutation, its tests run in a fresh process group with a timeout:
- caught: pytest reports failing tests (exit 1);
- survived: they all pass (exit 0);
- error: any other exit, such as a collection error, or the timeout. A broken guard must
  fail a test, not hang one.

A mutation that needs a server is skipped unless its variable is set. The run exits 1 unless
every mutation that ran was caught. --out writes mutations.json, with this checkout's code
state, and the output tail of every run.

This list was rebuilt on 2026-10-23 from the descriptions of the earlier checks
(docs/job-table.md, docs/job-queue.md, the message of commit e2806bd). Those runs left no list
of their own, so it is not claimed to be the same set. Mutations that the remaining guards
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from etf_risk.provenance import code_state  # noqa: E402

COPIED = ("src", "tests", "analysis", "docs/recovery-sql.md", "pyproject.toml", "uv.lock")
JOB_TESTS = ("tests/test_jobs_store.py", "tests/test_jobs_reconnect.py", "tests/test_jobs_worker.py",
             "tests/test_jobs_queue.py", "tests/test_jobs_reconciler.py", "tests/test_jobs_timing.py",
             "tests/test_jobs_kafka.py", "tests/test_jobs_mysql.py", "tests/test_jobs_launcher.py",
             "tests/test_jobs_pipeline.py", "tests/test_jobs_sweep.py")
NEEDS = {"mysql": "ETF_RISK_MYSQL_URL", "kafka": "ETF_RISK_KAFKA_BOOTSTRAP"}
STORE, WORKER, QUEUE = "src/etf_risk/jobs/store.py", "src/etf_risk/jobs/worker.py", "src/etf_risk/jobs/queue.py"
RECONCILER, KAFKA, MYSQL = "src/etf_risk/jobs/reconciler.py", "src/etf_risk/jobs/kafka.py", "src/etf_risk/jobs/mysql.py"
TIMING = "src/etf_risk/jobs/timing.py"
LAUNCHER, PROCESSES = "src/etf_risk/jobs/launcher.py", "src/etf_risk/jobs/processes.py"
PIPELINE = "src/etf_risk/jobs/pipeline.py"
FAULTS, HARNESS = "src/etf_risk/jobs/faults.py", "src/etf_risk/jobs/harness.py"
CROSSCHECK, COLLECTOR = "src/etf_risk/jobs/crosscheck.sql", "analysis/collect_recovery_measurements.py"
WORKER_TESTS, LAUNCHER_TESTS = ("tests/test_jobs_worker.py",), ("tests/test_jobs_launcher.py",)
FAULT_TESTS, HARNESS_TESTS = ("tests/test_jobs_faults.py",), ("tests/test_jobs_harness.py",)
COLLECTOR_TESTS, SQL_TESTS = ("tests/test_recovery_collector.py",), ("tests/test_recovery_sql.py",)
SYNTHETIC_TESTS = ("tests/test_recovery_synthetic.py",)


@dataclass(frozen=True)
class Mutation:
    id: str
    file: str
    old: str
    new: str
    breaks: str
    needs: tuple[str, ...] = ()
    tests: tuple[str, ...] = JOB_TESTS


def removing(id: str, file: str, context: str, piece: str, breaks: str, needs: tuple[str, ...] = (),
             tests: tuple[str, ...] = JOB_TESTS) -> Mutation:
    """Remove piece from context; context is what must occur exactly once in the file."""
    assert context.count(piece) == 1, (id, piece)
    return Mutation(id, file, context, context.replace(piece, "", 1), breaks, needs, tests)


_RENEW = ("updated_at = :now\"\n                    \" WHERE job_id = :job_id AND status = 'running'"
          " AND attempt_token = :token\",\n                    job_id=claim.job_id, token=claim.token, lease_expires_at")
_ACCEPT = ("'running' AND attempt_token = :token\",\n                    job_id=claim.job_id, token=claim.token,"
           " attempt_number=claim.attempt_number,")
_FAIL = ("'running' AND attempt_token = :token\",\n                    job_id=claim.job_id, token=claim.token,"
         " status=status.value,")
_TAKEOVER = ("status = 'running' AND lease_expires_at <= :now\"\n                    \" AND attempt_number <"
             " max_attempts\", **take).rowcount:")
_REQUEUE = ("'running' AND attempt_token = :token\"\n                    \" AND lease_expires_at <= :now AND"
            " attempt_number < max_attempts\",\n                    job_id=job_id, token=token, now=now_value).rowcount:")
_EXHAUST = ("'running' AND attempt_token = :token\"\n                \" AND lease_expires_at <= :now AND"
            " attempt_number >= max_attempts\",")
_CLAIM = ("published_at = NULL,\"\n                    \" version = version + 1, updated_at = :now\"\n"
          "                    \" WHERE job_id = :job_id AND status = 'queued'\", **take)")
_REPEAT = ("a.attempt_token = :token\"\n                \" AND a.result_digest = :digest\",")
_IN_TRANSACTION = ("        if self._in_transaction:                         # inside a transaction: this connection or none\n"
                   "            cursor = self.connection.cursor()\n"
                   "            cursor.execute(self.dialect.sql(sql), params)\n"
                   "            return cursor\n")
_IN_TRANSACTION_RETRY = ("        if self._in_transaction:\n"
                         "            try:\n"
                         "                cursor = self.connection.cursor()\n"
                         "                cursor.execute(self.dialect.sql(sql), params)\n"
                         "            except BaseException as error:\n"
                         "                if not self._forget_if_broken(error):\n"
                         "                    raise\n"
                         "                cursor = self._open().cursor()\n"
                         "                cursor.execute(self.dialect.sql(sql), params)\n"
                         "            return cursor\n")

MUTATIONS = (
    # The store's guards (docs/job-table.md).
    removing("renew-token", STORE, _RENEW, " AND attempt_token = :token", "renewal without the token: a fenced worker renews"),
    removing("accept-token", STORE, _ACCEPT, " AND attempt_token = :token", "acceptance without the token"),
    removing("fail-token", STORE, _FAIL, " AND attempt_token = :token", "fail_attempt without the token"),
    removing("takeover-lease", STORE, _TAKEOVER, " AND lease_expires_at <= :now", "a claim takes over a live lease"),
    Mutation("takeover-attempts-left", STORE, '" AND attempt_number < max_attempts", **take).rowcount:',
             '"", **take).rowcount:', "a claim takes over with no attempts left"),
    removing("requeue-token", STORE, _REQUEUE, " AND attempt_token = :token", "the reconciler requeues on a stale token"),
    removing("requeue-lease", STORE, _REQUEUE, " AND lease_expires_at <= :now", "the reconciler requeues a live lease"),
    removing("exhaust-token", STORE, _EXHAUST, " AND attempt_token = :token", "exhausting a job on a stale token"),
    removing("claim-keeps-publication", STORE, _CLAIM, "published_at = NULL,", "a claim keeps the recorded publication"),
    removing("claim-version-bump", STORE, _CLAIM, "version = version + 1, ", "a claim does not bump the version"),
    removing("publication-version", STORE, "AND published_at IS NULL AND version = :version\",",
             " AND version = :version", "a late confirmation is recorded after the job moved on"),
    Mutation("accept-repeat-token", STORE,
             "\" WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token\"",
             "\" WHERE j.job_id = :job_id AND j.status = 'succeeded'\"",
             "a repeated acceptance is reported for any token"),
    removing("accept-repeat-digest", STORE, _REPEAT, "\n                \" AND a.result_digest = :digest\"",
             "a repeated acceptance is reported for any digest"),
    removing("accept-records-digest", STORE, "SET outcome = 'accepted', result_digest = :digest, ended_at",
             " result_digest = :digest,", "acceptance does not record the run digest"),
    Mutation("digest-check", STORE, "if not is_digest(result_digest):", "if False:",
             "anything is accepted as a run digest"),
    Mutation("reconnect-inside-transaction", STORE, _IN_TRANSACTION, _IN_TRANSACTION_RETRY,
             "a statement inside a transaction runs again on a new connection"),
    Mutation("disconnect-as-conflict", STORE, "or not self.dialect.is_conflict(error):",
             "or not (self.dialect.is_conflict(error) or self.dialect.is_disconnect(error)):",
             "an operation that lost its connection is replayed"),
    Mutation("ping-reconnect", MYSQL, "connection.ping(reconnect=False)", "connection.ping(reconnect=True)",
             "a ping reconnects without the session settings", needs=("mysql",)),
    Mutation("rollback", STORE, 'cursor.execute("ROLLBACK")', 'cursor.execute("COMMIT")',
             "a failed transaction commits what it wrote"),
    Mutation("one-row-check", STORE, "if count != 1:", "if count > 1:", "a job_attempts write may touch no row"),
    Mutation("conflict-detection", MYSQL, "error.args[0] in CONFLICT_ERRORS", "error.args[0] in ()",
             "deadlocks and lock wait timeouts are not run again", needs=("mysql",)),
    # The worker (docs/job-queue.md, "What the worker does with a delivery").
    Mutation("output-folder-check", WORKER, "exist_ok=False", "exist_ok=True", "an attempt writes into an existing folder"),
    Mutation("acknowledge-after-claim", WORKER, '        self._fault("after_claim")\n        acknowledge()\n',
             '        self._fault("after_claim")\n', "a claimed delivery is never acknowledged"),
    Mutation("rewind", WORKER, "consumer.rewind(delivery)", "pass", "a failed delivery is not read again"),
    Mutation("bounded-retries", WORKER, "if failures > retries:", "if False:", "serve() retries one message forever"),
    Mutation("malformed-commit", WORKER,
             "                served.malformed += 1\n                self._commit(consumer, delivery, served)\n",
             "                served.malformed += 1\n", "a malformed message is skipped without a commit"),
    # Job ids in messages (docs/job-queue.md, Settings).
    Mutation("job-id-leading-zero", QUEUE, 'rb"[1-9][0-9]{0,%d}"', 'rb"[0-9][0-9]{0,%d}"', "zero and leading zeros pass"),
    Mutation("job-id-format", QUEUE, "if _JOB_ID.fullmatch(self.value) is None:", "if False:", "text reaches int()"),
    Mutation("job-id-length", QUEUE, "MAX_JOB_ID_DIGITS - 1", "MAX_JOB_ID_DIGITS + 4999", "5,000 digits reach int()"),
    Mutation("job-id-range", QUEUE, "return job_id if job_id <= MAX_JOB_ID else None", "return job_id",
             "ids beyond the range reach the database"),
    # The reconciler.
    Mutation("grace-boundary", RECONCILER, "now - job.queued_since < self.publication_grace",
             "now - job.queued_since <= self.publication_grace", "the grace period is one tick too long"),
    Mutation("grace-for-requeued", RECONCILER, "if job.attempt_number == 0 and now", "if now",
             "a requeued job waits for the grace period"),
    # Kafka settings (etf_risk.jobs.kafka).
    Mutation("auto-commit", KAFKA, '"enable.auto.commit": False', '"enable.auto.commit": True', "offsets commit on their own"),
    Mutation("offset-store", KAFKA, '"enable.auto.offset.store": False', '"enable.auto.offset.store": True',
             "positions are stored without a commit"),
    Mutation("offset-reset", KAFKA, '"auto.offset.reset": "earliest"', '"auto.offset.reset": "latest"',
             "a new group skips earlier jobs"),
    Mutation("acks", KAFKA, '"acks": "all"', '"acks": "1"', "the producer stops asking for acks=all"),
    Mutation("idempotence", KAFKA, '"enable.idempotence": True', '"enable.idempotence": False', "idempotence off"),
    Mutation("group-protocol", KAFKA, '"group.protocol": "classic"', '"group.protocol": "consumer"',
             "the session timeout is ignored"),
    # The time settings' relations (etf_risk.jobs.timing).
    Mutation("fence-margin-check", TIMING,
             "if self.fence_margin < self.watchdog_tick + self.kill_grace + self.safety:", "if False:",
             "a fence margin too short for the watchdog is accepted"),
    # The watchdog, the host lock and process trees (etf_risk.jobs.launcher, processes, pipeline).
    Mutation("watchdog-reads-first", LAUNCHER, '        now = time.monotonic()\n        if self.watchdog.expired(now):\n            for line in self.lines.read():              # read only to record them: a fired watchdog ignores all\n                self.watchdog.offer(line, now)\n            return "deadline"\n        for line in self.lines.read():\n            self.watchdog.offer(line, now)',
             '        now = time.monotonic()\n        for line in self.lines.read():\n            self.watchdog.offer(line, now)\n        if self.watchdog.expired(time.monotonic()):\n            return "deadline"',
             "lines queued while the launcher was stopped are read before the deadline check"),
    Mutation("watchdog-older-sequence", LAUNCHER, " or seq <= self.seq", "",
             "a line with an older sequence number moves the deadline"),
    Mutation("tree-by-group", PROCESSES, "if os.getsid(pid) == sid:", "if os.getpgid(pid) == sid:",
             "a tree is its process group, which PySpark's daemon leaves"),
    Mutation("no-host-lock", LAUNCHER, "fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)", "pass",
             "a step starts without the host's execution lock"),
    Mutation("no-survivor-wait", LAUNCHER, "while survivors := self.registry.survivors():", "while False:",
             "a step starts while an earlier tree survives"),
    Mutation("no-clock-check", LAUNCHER,
             'if not (first["monotonic"] <= now <= first["monotonic"] + CLOCK_TOLERANCE):', "if False:",
             "the launcher accepts a worker that reads another clock"),
    Mutation("environment-passed-through", PIPELINE,
             "env = {name: os.environ[name] for name in ENV_ALLOWED if name in os.environ}", "env = dict(os.environ)",
             "service URLs and passwords reach the steps"),
    Mutation("sweep-ends-valid-attempts", PIPELINE, "        elif value in valid:\n", "        elif False:\n",
             "the startup sweep ends a valid active attempt"),
    Mutation("no-renewal-before-acceptance", PIPELINE,
             '        self._renew_before(renewer, claim, before="acceptance")\n', "",
             "a digest is returned without renewing after the steps"),
    Mutation("result-rule-checks", PIPELINE, "        if total_violations(checks):", "        if False:",
             "a run with check violations is accepted when its status says ok"),
    # Focused: the worker's acceptance deadline (docs/worker-pipeline.md).
    Mutation("accept-after-deadline", WORKER, "        if deadline is not None and time.monotonic() >= deadline:\n",
             "        if False:\n", "an acceptance call starts after F", tests=WORKER_TESTS),
    removing("retry-after-deadline", WORKER, "                self._sleep(1.0)\n                if time.monotonic() >= deadline:\n"
             "                    raise\n", "                if time.monotonic() >= deadline:\n                    raise\n",
             "a retried acceptance starts after F passed during the wait", tests=WORKER_TESTS),
    Mutation("no-after-accept-commit-point", WORKER, '        self._fault("after_accept_commit")\n', "",
             "W5a's fault point, between the acceptance's commit and its event, is never reached", tests=WORKER_TESTS),
    # Focused: the launcher's monotonic interval (outline 4.1, 6.5).
    Mutation("step-start-mono-early", LAUNCHER, 'self.result["step_started_mono"] = time.monotonic()',
             'self.result["step_started_mono"] = time.monotonic() - 1.0', "a step's interval starts before the step",
             tests=LAUNCHER_TESTS),
    Mutation("tree-end-mono-at-start", LAUNCHER, 'self.result["tree_ended_mono"] = time.monotonic()',
             'self.result["tree_ended_mono"] = started', "a tree's end is read when its step starts",
             tests=LAUNCHER_TESTS),
    # Focused: the fault hook (outline 8.4).
    Mutation("fault-fires-again", FAULTS, "        self.path.unlink(missing_ok=True)                    # once: gone before it acts\n",
             "", "an armed fault fires again at the next pass", tests=FAULT_TESTS),
    Mutation("refused-arming-acts", FAULTS, "            if armed not in self.points or action not in ACTIONS:",
             "            if False:", "an arming that names an unknown point or action is not refused", tests=FAULT_TESTS),
    # Focused: the harness (outline 2.4, 3.1, 4.3, 8.6).
    Mutation("arm-other-worker", HARNESS, "faults.arm(self.fault_file(owner), point, action,",
             'faults.arm(self.fault_file("B" if owner == "A" else "A"), point, action,',
             "the fault is armed in the worker that does not own the partition", tests=HARNESS_TESTS),
    Mutation("no-early-miss", HARNESS,
             "                raise PhaseMissed(f\"job {job_id} was claimed by worker {claim['worker']}, not the armed {armed}\")",
             "                return None", "a claim by the other worker waits for the phase timeout", tests=HARNESS_TESTS),
    Mutation("spark-step-end-by-step", HARNESS, 'events_named(events, "step_ended", name="spark_pipeline", **mine)',
             'events_named(events, "step_ended", step="spark_pipeline", **mine)',
             "the end of the spark step is looked for in a field step_ended does not have", tests=HARNESS_TESTS),
    Mutation("observation-repeated", HARNESS,
             "if self.observation is None and (status in TERMINAL or now >= self.deadline_mono):",
             "if status in TERMINAL or now >= self.deadline_mono:", "the deadline observation is taken again",
             tests=HARNESS_TESTS),
    Mutation("observation-waits-for-deadline", HARNESS,
             "if self.observation is None and (status in TERMINAL or now >= self.deadline_mono):",
             "if self.observation is None and now >= self.deadline_mono:",
             "a finished job is observed only at its deadline", tests=HARNESS_TESTS),
    Mutation("formal-without-flag", HARNESS, '    if purpose == "formal" and not args.formal:', "    if False:",
             "a formal batch starts without --formal", tests=HARNESS_TESTS),
    Mutation("batch-outside-purpose-folder", HARNESS, "    if args.out.resolve().parent.name != purpose:", "    if False:",
             "a batch writes outside the folder of its purpose", tests=HARNESS_TESTS),
    # Focused: the collector (outline sections 5 and 6).
    Mutation("overlap-never-found", COLLECTOR, "        if latest is not None and start < latest[1]:", "        if False:",
             "overlapping steps are not found", tests=COLLECTOR_TESTS),
    Mutation("missing-interval-no-overlap", COLLECTOR,
             '    verdict = "overlap" if overlaps else "unknown" if missing else "no overlap"',
             '    verdict = "overlap" if overlaps else "no overlap"', "a missing interval counts as no overlap",
             tests=COLLECTOR_TESTS),
    Mutation("utc-interval-fallback", COLLECTOR, "        return float(start), float(end)\n    return None\n",
             "        return float(start), float(end)\n"
             '    if record.get("step_started_at_utc") and record.get("tree_ended_at_utc"):\n'
             '        return (datetime.fromisoformat(record["step_started_at_utc"]).timestamp(),\n'
             '                datetime.fromisoformat(record["tree_ended_at_utc"]).timestamp())\n    return None\n',
             "a launcher record with UTC times only is compared in UTC", tests=COLLECTOR_TESTS),
    Mutation("no-injection-time-unknown", COLLECTOR,
             "    else:                                                         # the record of the injection lacks its time\n"
             '        row.update(detection_s="unknown: no injection time", rerun_s="unknown: no injection time")\n', "",
             "latencies without an injection time are left blank, not unknown", tests=COLLECTOR_TESTS),
    Mutation("unrecorded-counted-as-made", COLLECTOR,
             '        status = "no injection record" if inj is None else "missed" if inj.get("missed") else "made"',
             '        status = "missed" if inj and inj.get("missed") else "made"',
             "a job without its injection record counts as made", tests=COLLECTOR_TESTS),
    Mutation("d2-without-fenced", COLLECTOR,
             'named(events, "retry", operation="accept_result")\n'
             '                                      + named(events, "fenced", during="acceptance"), t_inj)',
             'named(events, "retry", operation="accept_result"), t_inj)',
             "D2 without a retry, fenced at acceptance after F, has no detection", tests=COLLECTOR_TESTS),
    Mutation("purpose-dropped", COLLECTOR, '    return {"purpose": b.plan.get("purpose", "not recorded"),',
             '    return {"purpose": "not recorded",', "the summary loses the batch's purpose", tests=COLLECTOR_TESTS),
    # Focused: the frozen cross-check SQL, on SQLite against the 82 expected rows (recovery-sql.md).
    Mutation("q2-late-rule", CROSSCHECK, "WHEN d.status <> 'succeeded' AND d.observed_from_mono >= b.deadline_mono\n",
             "WHEN d.status <> 'succeeded' AND d.observed_from_mono > b.deadline_mono + 1\n",
             "a job running at its deadline is not called late", tests=SQL_TESTS),
    Mutation("q2-lag-rule", CROSSCHECK, "d.observed_to_mono <= b.deadline_mono + b.max_lag_s",
             "d.observed_to_mono <= b.deadline_mono", "a success seen within the lag is not on time", tests=SQL_TESTS),
    Mutation("q1-two-accepted", CROSSCHECK, "        WHEN COALESCE(a.n_accepted, 0) > 1\n",
             "        WHEN COALESCE(a.n_accepted, 0) > 2\n", "two accepted attempts pass Q1", tests=SQL_TESTS),
    Mutation("q3a-other-store", CROSSCHECK, "    JOIN job_store AS s ON s.store_id = w.store_id\n",
             "    JOIN job_store AS s ON 1 = 1\n", "another store's report counts in Q3a", tests=SQL_TESTS),
    Mutation("q3b-worker-identity", CROSSCHECK, "        WHEN CAST(w.worker_id AS BINARY) <> CAST(a.worker_id AS BINARY)\n",
             "        WHEN 1 = 0\n", "a report from the wrong worker matches", tests=SQL_TESTS),
    # Focused: the synthetic batch, end to end (tests/test_recovery_synthetic.py).
    Mutation("no-restart", HARNESS, "        restarted = [w for w in WORKERS if self.procs[w].poll() is not None]",
             "        restarted = []", "a killed worker is never started again", tests=SYNTHETIC_TESTS),
    # Focused: the gaps G1-G7 and G9 of docs/recovery-part-a.md, fixed on 2026-10-24.
    Mutation("setup-error-unrecorded", HARNESS,
             '                self.log.log("setup_error", error=f"{type(error).__name__}: {error}"[:1000])\n', "",
             "a failure in the setup leaves no record", tests=HARNESS_TESTS),
    Mutation("teardown-not-started", HARNESS,
             "            if self.services_started:                       # never containers this batch did not start\n"
             '                self.compose("down", "-v")\n',
             '            self.compose("down", "-v")\n', "containers the batch did not start are taken down",
             tests=HARNESS_TESTS),
    Mutation("own-connections-counted", HARNESS, "        self.close_stores()\n", "",
             "quiescence counts the harness's own connections as other clients", tests=HARNESS_TESTS),
    Mutation("scratch-new-ignored", HARNESS,
             "        new = sorted(set(spark_scratch(self.scratch_folders())) - set(self.scratch_before))",
             "        new = []", "new Spark scratch is never reported", tests=HARNESS_TESTS),
    Mutation("scratch-before-ignored", HARNESS, "        self.scratch_before = spark_scratch(self.scratch_folders())\n",
             "        self.scratch_before = []\n", "Spark scratch from before the batch is reported as new",
             tests=SYNTHETIC_TESTS),
    Mutation("cleanup-lists-status", HARNESS, '        cleanup = self.cli("cleanup", check=False)',
             '        cleanup = self.cli("status", check=False)', "cleanup.txt holds no cleanup listing",
             tests=SYNTHETIC_TESTS),
    Mutation("host-memory-unrecorded", HARNESS,
             '        self.log.log("host_memory", position=position, **host_memory())    # P4: recorded, never a gate\n',
             "", "the host's memory before a job is not recorded", tests=SYNTHETIC_TESTS),
    Mutation("plan-folder-not-created", HARNESS, "        args.out.parent.mkdir(parents=True, exist_ok=True)\n", "",
             "plan cannot write into a new folder", tests=HARNESS_TESTS),
    Mutation("records-complete-ignored", COLLECTOR,
             '        "records_complete": {"passed": not named(b.harness, "setup_error") and not named(b.harness, "final_error"),',
             '        "records_complete": {"passed": True,', "a recorded setup or final error passes validity",
             tests=COLLECTOR_TESTS),
    Mutation("batch-folder-relative", HARNESS,
             "        out = Path(out).resolve()           # G9: every path handed to a process is absolute, whatever its cwd\n",
             "        out = Path(out)\n", "a relative batch folder reaches the reference launcher as relative paths (G9)",
             tests=HARNESS_TESTS),
    Mutation("host-memory-column-dropped", COLLECTOR,
             '        if position in host:\n            row["host_available_bytes"] = host[position].get("available_bytes")\n',
             "", "the per-job host memory is left out of injections.csv", tests=COLLECTOR_TESTS),
)


def make_scratch() -> Path:
    scratch = Path(tempfile.mkdtemp(prefix="etf-risk-mutations-"))
    ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache")
    for item in COPIED:
        source = REPO / item
        if source.is_dir():
            shutil.copytree(source, scratch / item, ignore=ignore)
        else:
            (scratch / item).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, scratch / item)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    subprocess.run(["uv", "sync", "--frozen", "--group", "jobs"], cwd=scratch, env=env, check=True,
                   capture_output=True, text=True)
    return scratch


def run_tests(scratch: Path, timeout: float, tests: tuple[str, ...] | list[str] = JOB_TESTS) -> dict:
    """The tests in a new process group; the group is killed on timeout. The scratch
    environment comes first on PATH, as under uv run, so any python3 started below is its."""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["PATH"] = f"{scratch / '.venv' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    command = [str(scratch / ".venv" / "bin" / "python"), "-m", "pytest", *tests, "-x", "-q",
               "-p", "no:cacheprovider"]
    start = time.monotonic()
    process = subprocess.Popen(command, cwd=scratch, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, start_new_session=True)
    try:
        output, _ = process.communicate(timeout=timeout)
        code = process.returncode
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        output, _ = process.communicate()
        code = None
    failed = next((line for line in output.splitlines() if line.startswith("FAILED ")), None)
    return {"exit_code": code, "seconds": round(time.monotonic() - start, 1), "first_failure": failed,
            "output_tail": output[-3000:]}


def outcome(result: dict) -> str:
    return {1: "caught", 0: "survived"}.get(result["exit_code"], "error")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", nargs="+", metavar="ID", help="run these mutations only")
    parser.add_argument("--timeout", type=float, default=600.0, help="seconds per run of the job tests (default 600)")
    parser.add_argument("--out", type=Path, help="folder for mutations.json")
    parser.add_argument("--list", action="store_true", help="list the mutations and exit")
    args = parser.parse_args(argv)
    if args.list:
        for m in MUTATIONS:
            print(f"{m.id:30} {m.file.removeprefix('src/etf_risk/jobs/'):14} {m.breaks}"
                  + (f"  (needs {', '.join(m.needs)})" if m.needs else "")
                  + (f"  [{', '.join(t.removeprefix('tests/') for t in m.tests)}]" if m.tests != JOB_TESTS else ""))
        return 0
    unknown = set(args.only or ()) - {m.id for m in MUTATIONS}
    if unknown:
        parser.error(f"unknown mutation(s): {', '.join(sorted(unknown))}")
    selected = [m for m in MUTATIONS if not args.only or m.id in args.only]
    backends = {name: bool(os.environ.get(variable)) for name, variable in NEEDS.items()}
    record = {"format": 1, "started_at_utc": datetime.now(timezone.utc).isoformat(), "code": code_state(),
              "backends": {"sqlite": True, **backends}, "timeout_s": args.timeout, "mutations": []}
    scratch = make_scratch()
    try:
        needed = list(dict.fromkeys(t for m in selected for t in m.tests))
        baseline = run_tests(scratch, args.timeout, needed)
        record["baseline"] = {"tests": needed, **baseline}
        print(f"baseline: exit {baseline['exit_code']} in {baseline['seconds']} s")
        if baseline["exit_code"] != 0:
            print(baseline["output_tail"], file=sys.stderr)
            print("the unmutated tests must pass first", file=sys.stderr)
            return 1
        for m in selected:
            missing = [need for need in m.needs if not backends[need]]
            if missing:
                record["mutations"].append({**asdict(m), "outcome": "skipped", "missing": missing})
                print(f"skipped   {m.id} (needs {', '.join(missing)})")
                continue
            path = scratch / m.file
            original = path.read_text()
            if original.count(m.old) != 1:
                raise SystemExit(f"{m.id}: the text to replace occurs {original.count(m.old)} times in {m.file}")
            path.write_text(original.replace(m.old, m.new, 1))
            try:
                result = run_tests(scratch, args.timeout, m.tests)
            finally:
                path.write_text(original)
            record["mutations"].append({**asdict(m), "outcome": outcome(result), **result})
            print(f"{outcome(result):9} {m.id} ({result['seconds']} s){'  ' + result['first_failure'] if result['first_failure'] else ''}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    ran = [m for m in record["mutations"] if m["outcome"] != "skipped"]
    record["summary"] = {o: sum(1 for m in record["mutations"] if m["outcome"] == o)
                         for o in ("caught", "survived", "error", "skipped")}
    print(f"{record['summary']['caught']} of {len(ran)} caught; {record['summary']}")
    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        (args.out / "mutations.json").write_text(json.dumps(record, indent=2) + "\n")
    return 0 if ran and all(m["outcome"] == "caught" for m in ran) else 1


if __name__ == "__main__":
    sys.exit(main())
