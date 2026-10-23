"""Mutation checks of the job queue's guards and settings: break one on purpose, run the job
tests, and expect them to fail (docs/job-table.md, docs/job-queue.md).

    uv run --group jobs python tests/mutation_check.py --out <folder>       # SQLite and offline Kafka settings
    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \\
        uv run --group jobs python tests/mutation_check.py --out <folder>   # also MySQL and Kafka
    uv run --group jobs python tests/mutation_check.py --list
    uv run --group jobs python tests/mutation_check.py --only renew-token rewind

Each mutation replaces one exact piece of source text, which must occur exactly once. The
work happens in a scratch copy of the repository (src/, tests/, pyproject.toml, uv.lock) with
its own environment (uv sync --frozen --group jobs), never in this checkout. The job tests
first run unmutated and must pass. Then, for each mutation, they run in a fresh process
group with a timeout:
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

COPIED = ("src", "tests", "pyproject.toml", "uv.lock")
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


@dataclass(frozen=True)
class Mutation:
    id: str
    file: str
    old: str
    new: str
    breaks: str
    needs: tuple[str, ...] = ()


def removing(id: str, file: str, context: str, piece: str, breaks: str, needs: tuple[str, ...] = ()) -> Mutation:
    """Remove piece from context; context is what must occur exactly once in the file."""
    assert context.count(piece) == 1, (id, piece)
    return Mutation(id, file, context, context.replace(piece, "", 1), breaks, needs)


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
)


def make_scratch() -> Path:
    scratch = Path(tempfile.mkdtemp(prefix="etf-risk-mutations-"))
    ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache")
    for item in COPIED:
        source = REPO / item
        if source.is_dir():
            shutil.copytree(source, scratch / item, ignore=ignore)
        else:
            shutil.copy2(source, scratch / item)
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    subprocess.run(["uv", "sync", "--frozen", "--group", "jobs"], cwd=scratch, env=env, check=True,
                   capture_output=True, text=True)
    return scratch


def run_tests(scratch: Path, timeout: float) -> dict:
    """The job tests in a new process group; the group is killed on timeout. The scratch
    environment comes first on PATH, as under uv run, so any python3 started below is its."""
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    env["PATH"] = f"{scratch / '.venv' / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    command = [str(scratch / ".venv" / "bin" / "python"), "-m", "pytest", *JOB_TESTS, "-x", "-q",
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
            print(f"{m.id:26} {m.file.removeprefix('src/etf_risk/jobs/'):14} {m.breaks}"
                  + (f"  (needs {', '.join(m.needs)})" if m.needs else ""))
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
        baseline = run_tests(scratch, args.timeout)
        record["baseline"] = baseline
        print(f"baseline: exit {baseline['exit_code']} in {baseline['seconds']} s")
        if baseline["exit_code"] != 0:
            print(baseline["output_tail"], file=sys.stderr)
            print("the unmutated job tests must pass first", file=sys.stderr)
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
                result = run_tests(scratch, args.timeout)
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
