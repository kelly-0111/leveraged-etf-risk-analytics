"""The real pipeline in the worker: windows → spark_pipeline → verify for one claimed job, each
step run by a launcher (spec §11; docs/job-queue.md, "The real pipeline").

Steps. Each step is `<python> -m etf_risk.<module>` with absolute paths only, and everything it
writes lands in the attempt's folder:
1. windows --out-root <run dir>/windows --name <name>, from the snapshot under the worker's
   processed-data root;
2. spark_pipeline --windows <run dir>/windows/<snapshot>/<name>
   --out-root <run dir>/output --run-id <run id>;
3. verify --run <run dir>/output/<snapshot>/<name>/<run id>.

The step's environment:
- It is built from an allowlist, so service URLs and passwords never reach it, and it
  carries the attempt's marker (etf_risk.jobs.processes).
- The working directory, TMPDIR and SPARK_LOCAL_DIRS point into <run dir>/.work.
  java.io.tmpdir does too, set through SPARK_SUBMIT_OPTS, since the macOS JDK ignores
  TMPDIR. It is never set through JAVA_TOOL_OPTIONS, whose "Picked up" notice would replace
  the Java version that run.json records.
- PYSPARK_PYTHON and PYSPARK_DRIVER_PYTHON name this interpreter; otherwise Spark's Python
  workers start whatever python3 comes first on PATH.

Renewals. The worker's thread waits on the launcher one tick (1 s) at a time and renews the
lease every renew_interval. After each successful renewal it sends the launcher the absolute
deadline F = m0 + lease - fence_margin, on the monotonic clock (etf_risk.jobs.timing), where
m0 is the time just before the renewal started. The first F comes from the claim
(Heartbeat.claimed_mono).
- A renewal that raises, because the database is out of reach, is tried again at the next
  interval.
- A refused renewal means the attempt was fenced off. So does a deadline that passed without
  a renewal: the worker fences itself. Either way, the worker closes the launcher's pipe and
  the launcher ends the tree.
- The launcher's watchdog acts without the worker. Safety (no overlapping Spark work) rests
  on it and on the host lock, not on how long the worker's database calls take.
- The worker renews before each step and before acceptance, so a fenced worker never starts
  a new step. If the launcher does not end within the kill grace after its pipe was closed
  (because it is stopped, for example), the worker ends the tree itself.

Acceptance. The run counts as a result only if all of the following hold:
- every step exited 0;
- run.json's status is ok;
- every count in checks.json is 0;
- verify.json reports no mismatch and the same breached windows;
- every table has its _SUCCESS file.
Then .work is removed, attempt.json is written (worker, steps, settings, code state), and
manifest.json records the run folder's manifest (etf_risk.runs). After a last renewal, run()
returns the run digest, and the worker accepts with it. Nothing in the folder changes after
acceptance.

Failures are classified from the records, not from exit codes alone, since an uncaught
exception exits with 1, as "checks failed" does:
- not retryable: a checksum error (exit 3); run.json status checks_failed; a verify
  mismatch; parameters or input checksums that do not fit;
- retryable: a signal; a time limit; status failed or a missing record; a busy host lock;
  a launcher that failed;
- fenced: a refused renewal, or a deadline that passed.

startup_sweep() is run by a starting worker. It ends the trees of attempts that are no longer
valid, keeps every valid active attempt's tree, and removes the scratch (.work) of attempts
that ended.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_pipeline.py
(offline, with stand-in steps) and tests/test_jobs_worker_spark.py (the real steps).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from etf_risk import runs
from etf_risk.jobs import processes
from etf_risk.jobs.events import NO_EVENTS, EventLog
from etf_risk.jobs.params import InvalidParams, JobParams, check_inputs
from etf_risk.jobs.store import Claim, JobStore
from etf_risk.jobs.timing import DEFAULT_TIMING, Timing
from etf_risk.jobs.worker import Fenced, PipelineError
from etf_risk.provenance import code_state, source_identity

STEPS = ("windows", "spark_pipeline", "verify")
TABLES = ("window_stats", "path_days", "path_summary", "paired")
def total_violations(checks: dict) -> int:
    """As spark_pipeline.total_violations, without importing PySpark into the worker."""
    return sum(v for group in checks.values() for v in group.values())


ENV_ALLOWED = ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "JAVA_HOME", "SHELL", "TERM")
DEFAULT_LOCK = Path.home() / ".cache" / "etf-risk" / "locks" / "spark-exec.lock"


class Renewer:
    """The attempt's lease, as the worker sees it: fence_at is the absolute monotonic deadline
    given to the launcher, seq the number of the last successful renewal."""

    def __init__(self, heartbeat, timing: Timing, events: EventLog, claim: Claim):
        self.heartbeat, self.timing, self.events, self.claim = heartbeat, timing, events, claim
        claimed = getattr(heartbeat, "claimed_mono", None)
        self.fence_at = None if claimed is None else claimed + timing.lease - timing.fence_margin
        self.seq = 0
        self.last_attempt = float("-inf")

    def renew(self) -> bool | None:
        """True: renewed; False: refused (fenced off); None: the call failed."""
        m0 = time.monotonic()
        self.last_attempt = m0
        try:
            ok = self.heartbeat()
        except Exception as error:
            self.events.log("renewal_failed", job_id=self.claim.job_id, attempt=self.claim.attempt_number,
                            seconds=round(time.monotonic() - m0, 3), error=f"{type(error).__name__}: {error}"[:500])
            return None
        self.events.log("renewed" if ok else "renewal_refused", job_id=self.claim.job_id,
                        attempt=self.claim.attempt_number, seconds=round(time.monotonic() - m0, 3))
        if ok:
            self.fence_at = m0 + self.timing.lease - self.timing.fence_margin
            self.seq += 1
        return bool(ok)

    def due(self, now: float) -> bool:
        return now - self.last_attempt >= self.timing.renew_interval

    def passed(self, now: float) -> bool:
        return self.fence_at is None or now >= self.fence_at


class SubprocessPipeline:
    def __init__(self, *, store_id: str, processed_root: str | Path, worker_id: str,
                 lock_path: str | Path = DEFAULT_LOCK, registry: str | Path | None = None,
                 timing: Timing = DEFAULT_TIMING, events: EventLog = NO_EVENTS,
                 stop: threading.Event | None = None, python: str = sys.executable):
        self.store_id, self.worker_id = store_id, worker_id
        self.processed_root = Path(processed_root).resolve()
        self.lock_path = Path(lock_path)
        self.registry = Path(registry) if registry is not None else self.lock_path.parent / "registry"
        self.timing, self.events, self.stop, self.python = timing.check(), events, stop, python
        self.fence_at: float | None = None          # the current attempt's deadline (Worker reads it)

    # The run

    def run(self, claim: Claim, run_dir: Path, heartbeat) -> str:
        run_dir = Path(run_dir).resolve()
        started = datetime.now(timezone.utc).isoformat()
        renewer = Renewer(heartbeat, self.timing, self.events, claim)
        self.fence_at = renewer.fence_at
        try:
            params = JobParams.from_dict(claim.params)
            check_inputs(self.processed_root, params.snapshot, claim.input_checksums)
        except InvalidParams as error:
            raise PipelineError(f"{error}", retryable=False) from None
        work, logs = run_dir / ".work", run_dir / "logs"
        for folder in (work / "tmp", work / "spark", work / "jtmp", logs):
            folder.mkdir(parents=True, exist_ok=True)
        marker = processes.marker(self.store_id, claim.run_id, claim.token)
        env = self.step_env(work, marker)
        steps = []
        for name, argv in self.commands(params, claim, run_dir):
            self._renew_before(renewer, claim, before=name)
            step = self._run_step(name, argv, env, work, logs, renewer, marker, claim)
            steps.append(step)
            self._classify(step, run_dir, params, claim)
        run_folder = self.run_folder(params, claim, run_dir)
        self._check_result(run_folder)
        shutil.rmtree(work)
        record = {"format": 1, "worker_id": self.worker_id, "store_id": self.store_id, "job_id": claim.job_id,
                  "attempt_number": claim.attempt_number, "run_id": claim.run_id, "params": params.to_dict(),
                  "input_checksums_checked": claim.input_checksums, "processed_root": str(self.processed_root),
                  "run_folder": run_folder.relative_to(run_dir).as_posix(), "steps": steps,
                  "timing": asdict(self.timing), "code": code_state(), "started_at_utc": started,
                  "finished_at_utc": datetime.now(timezone.utc).isoformat()}
        (run_dir / "attempt.json").write_text(json.dumps(record, indent=2) + "\n")
        manifest = runs.manifest(run_folder)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        self._renew_before(renewer, claim, before="acceptance")
        self.fence_at = renewer.fence_at
        return runs.digest(manifest)

    def commands(self, params: JobParams, claim: Claim, run_dir: Path) -> list[tuple[str, list[str]]]:
        py, name = self.python, params.windows_name
        windows_dir = run_dir / "windows" / params.snapshot / name
        return [
            ("windows", [py, "-m", "etf_risk.windows", "--snapshot", params.snapshot,
                         "--processed-root", str(self.processed_root), "--kind", params.kind,
                         "--window-days", str(params.window_days), "--stride", str(params.stride),
                         "--anchor", params.anchor, "--out-root", str(run_dir / "windows"), "--name", name]),
            ("spark_pipeline", [py, "-m", "etf_risk.spark_pipeline", "--windows", str(windows_dir),
                                "--out-root", str(run_dir / "output"), "--run-id", claim.run_id]),
            ("verify", [py, "-m", "etf_risk.verify", "--run", str(self.run_folder(params, claim, run_dir)),
                        "--sample-ticker", params.sample_ticker]),
        ]

    @staticmethod
    def run_folder(params: JobParams, claim: Claim, run_dir: Path) -> Path:
        return run_dir / "output" / params.snapshot / params.windows_name / claim.run_id

    def step_env(self, work: Path, marker: str) -> dict[str, str]:
        env = {name: os.environ[name] for name in ENV_ALLOWED if name in os.environ}
        env["PATH"] = str(Path(self.python).parent) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin")
        env.update(TMPDIR=str(work / "tmp"), SPARK_LOCAL_DIRS=str(work / "spark"),
                   SPARK_SUBMIT_OPTS=f"-Djava.io.tmpdir={work / 'jtmp'} -XX:-UsePerfData",
                   PYSPARK_PYTHON=self.python, PYSPARK_DRIVER_PYTHON=self.python, PYTHONUNBUFFERED="1")
        env[processes.MARKER_ENV] = marker
        return env

    # Steps

    def _renew_before(self, renewer: Renewer, claim: Claim, *, before: str) -> None:
        """Renew the lease before a step or acceptance; Fenced if that cannot happen in time."""
        while True:
            if self.stop is not None and self.stop.is_set():
                raise PipelineError(f"the worker was stopped before {before}", retryable=True)
            ok = renewer.renew()
            self.fence_at = renewer.fence_at
            if ok:
                return
            if ok is False:
                raise Fenced(f"{claim.run_id}: the renewal before {before} was refused")
            if renewer.passed(time.monotonic()):
                raise Fenced(f"{claim.run_id}: no renewal before the deadline, before {before}")
            time.sleep(self.timing.worker_tick)

    def _send(self, fd: int, line: dict) -> bool:
        try:
            os.write(fd, (json.dumps(line) + "\n").encode())
            return True
        except BlockingIOError:                       # the launcher is not reading: the old deadline stands
            self.events.log("keepalive_dropped", seq=line.get("seq"))
            return False
        except (BrokenPipeError, OSError):
            return False

    def _run_step(self, name: str, argv: list[str], env: dict, work: Path, logs: Path, renewer: Renewer,
                  marker: str, claim: Claim) -> dict:
        t = self.timing
        result_path = logs / f"{name}.launcher.json"
        command = [self.python, "-m", "etf_risk.jobs.launcher", "--marker", marker, "--lock", str(self.lock_path),
                   "--registry", str(self.registry), "--lock-wait", str(t.lock_wait(name)),
                   "--step-limit", str(t.step_limit(name)), "--cwd", str(work), "--step-log", str(logs / f"{name}.log"),
                   "--result", str(result_path), "--tick", str(t.watchdog_tick), "--term-grace", str(t.term_grace),
                   "--kill-confirm", str(t.kill_confirm), "--", *argv]
        self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name,
                        code=source_identity())     # the code the step starts from (recovery experiments, 2.3)
        with open(logs / f"{name}.launcher.log", "ab") as launcher_log:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=launcher_log, stderr=subprocess.STDOUT,
                                    env=env, cwd=work, start_new_session=True)
        fd = proc.stdin.fileno()
        os.set_blocking(fd, False)
        self._send(fd, {"monotonic": time.monotonic(), "seq": renewer.seq, "deadline": renewer.fence_at})
        closed, closed_at, backstop = None, None, None
        while True:
            try:
                proc.wait(timeout=t.worker_tick)
                break
            except subprocess.TimeoutExpired:
                pass
            now = time.monotonic()
            if closed is None:
                if self.stop is not None and self.stop.is_set():
                    closed = "stopped"
                elif renewer.due(now):
                    ok = renewer.renew()
                    self.fence_at = renewer.fence_at
                    if ok:
                        self._send(fd, {"seq": renewer.seq, "deadline": renewer.fence_at})
                    elif ok is False:
                        closed = "fenced"
                if closed is None and renewer.passed(time.monotonic()):
                    closed = "self_fenced"
                if closed is not None:
                    proc.stdin.close()                   # EOF: the launcher ends the tree
                    closed_at = time.monotonic()
                    self.events.log(closed, job_id=claim.job_id, attempt=claim.attempt_number, step=name)
            elif backstop is None and now - closed_at > t.kill_grace + 10:
                # The launcher did not act on the EOF (it is stopped, perhaps): end the tree here.
                backstop = processes.terminate(processes.attempt_members(proc.pid, marker, exclude=[proc.pid]),
                                               term_grace=t.term_grace, kill_confirm=t.kill_confirm)
                proc.kill()
        if not proc.stdin.closed:
            proc.stdin.close()
        try:
            result = json.loads(result_path.read_text())
        except (OSError, json.JSONDecodeError):
            result = {"outcome": "launcher_died", "returncode": None}
        step = {"name": name, "outcome": result.get("outcome"), "returncode": result.get("returncode"),
                "seconds": result.get("step_seconds"), "lock_wait_s": result.get("lock_wait_s"),
                "peak_rss_bytes": result.get("peak_rss_bytes"), "ended": result.get("ended"),
                "lingering": result.get("lingering"), "closed": closed, "launcher_exit": proc.returncode,
                "backstop": backstop}
        self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number,
                        **{k: v for k, v in step.items() if k not in ("ended", "backstop")})
        return step

    # Records

    def _classify(self, step: dict, run_dir: Path, params: JobParams, claim: Claim) -> None:
        """Raise unless the step ran to its end and its records say it worked."""
        name, outcome, code, closed = step["name"], step["outcome"], step["returncode"], step["closed"]
        if closed == "stopped":
            raise PipelineError(f"{name}: the worker was stopped", retryable=True)
        if closed in ("fenced", "self_fenced") or outcome in ("deadline", "deadline_passed"):
            raise Fenced(f"{claim.run_id}: {name} ended: {closed or outcome}")
        if outcome == "clock_mismatch":
            raise PipelineError(f"{name}: the launcher reads another clock", retryable=False)
        if outcome != "exited":
            raise PipelineError(f"{name}: {outcome} (exit {code})", retryable=True)
        tail = self._tail(run_dir / "logs" / f"{name}.log")
        if name == "windows" and code != 0:
            raise PipelineError(f"windows exited {code}: {tail}", retryable=True)
        if name == "spark_pipeline":
            status = self._json(self.run_folder(params, claim, run_dir) / "run.json").get("status")
            if code == 3:
                raise PipelineError(f"spark_pipeline: an input checksum differs: {tail}", retryable=False)
            if status == "checks_failed":
                raise PipelineError("spark_pipeline: checks failed", retryable=False)
            if code != 0 or status != "ok":
                raise PipelineError(f"spark_pipeline exited {code} with status {status}: {tail}", retryable=True)
        if name == "verify":
            result = self._json(self.run_folder(params, claim, run_dir) / "verify.json")
            if code == 3:
                raise PipelineError(f"verify: an input checksum differs: {tail}", retryable=False)
            if result and (result.get("mismatch_count") or not result.get("breached_windows", {}).get("same", False)):
                raise PipelineError(f"verify: {result.get('mismatch_count')} mismatches", retryable=False)
            if code != 0 or not result:
                raise PipelineError(f"verify exited {code} without a clean verify.json: {tail}", retryable=True)

    def _check_result(self, run_folder: Path) -> None:
        run = self._json(run_folder / "run.json")
        checks = self._json(run_folder / "checks.json")
        verified = self._json(run_folder / "verify.json")
        if run.get("status") != "ok" or not checks:
            raise PipelineError(f"{run_folder}: run.json or checks.json is missing or not ok", retryable=True)
        if total_violations(checks):
            raise PipelineError(f"{run_folder}: {total_violations(checks)} check violations", retryable=False)
        if not verified or verified.get("mismatch_count") or not verified.get("breached_windows", {}).get("same"):
            raise PipelineError(f"{run_folder}: verify.json is missing or not clean", retryable=False)
        missing = [table for table in TABLES if not (run_folder / table / "_SUCCESS").is_file()]
        if missing:
            raise PipelineError(f"{run_folder}: no _SUCCESS in {missing}", retryable=True)

    @staticmethod
    def _json(path: Path) -> dict:
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _tail(path: Path, lines: int = 5) -> str:
        try:
            return " | ".join(path.read_text(errors="replace").strip().splitlines()[-lines:])[-800:]
        except OSError:
            return "(no log)"


_RUN_ID = re.compile(r"job-(\d+)-attempt-(\d+)")


def startup_sweep(store: JobStore, output_root: str | Path, *, timing: Timing = DEFAULT_TIMING,
                  events: EventLog = NO_EVENTS) -> dict:
    """What a starting worker does with what earlier workers left on this machine.

    It ends the process trees of this store's attempts that are no longer valid, and keeps
    every valid active one: the job is running, and its current attempt number and token hash
    match. A valid attempt's own lease or watchdog decides when it ends; the sweep never
    shortens it. It also removes the scratch (.work) of attempts that ended, never a folder.
    Trees of other stores are left alone and reported. With the database out of reach it
    does nothing."""
    output_root = Path(output_root)
    try:
        store_id = store.store_id()
        current = store.current_attempts()
    except Exception as error:
        events.log("sweep_skipped", error=f"{type(error).__name__}: {error}"[:500])
        return {"skipped": True}
    valid = {f"{store_id}:job-{job}-attempt-{n}:{processes.attempt_key(token)}" for job, (n, token) in current.items()}
    report: dict = {"preserved": [], "terminated": [], "other_stores": [], "scratch_removed": []}
    marked = processes.marked_processes()
    for value, procs in marked.items():
        owner = processes.parse_marker(value)
        if owner[0] != store_id:
            report["other_stores"].append(value)
        elif value in valid:
            report["preserved"].append(value)
        else:
            report["terminated"].append({"marker": value, **processes.terminate(
                procs, term_grace=timing.term_grace, kill_confirm=timing.kill_confirm)})
    live_runs = {processes.parse_marker(v)[1] for v in marked if processes.parse_marker(v)[0] == store_id
                 and v in valid}
    for work in sorted(output_root.glob("job-*-attempt-*/.work")):
        match = _RUN_ID.fullmatch(work.parent.name)
        if match is None or work.parent.name in live_runs:
            continue
        job, attempt = int(match.group(1)), int(match.group(2))
        if current.get(job, (None,))[0] == attempt:
            continue                                     # still running, here or elsewhere
        shutil.rmtree(work, ignore_errors=True)
        report["scratch_removed"].append(work.parent.name)
    events.log("sweep", preserved=len(report["preserved"]), terminated=len(report["terminated"]),
               other_stores=len(report["other_stores"]), scratch_removed=report["scratch_removed"])
    return report
