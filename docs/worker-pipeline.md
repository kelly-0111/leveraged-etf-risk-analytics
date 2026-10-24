# The worker's real pipeline: steps, deadlines, the host lock and cleanup

How the worker runs a job's windows → spark_pipeline → verify, and what keeps a failure from
leaving a second Spark run, a stray process or a wrong result behind. This is milestone M2 of
the systems extension ([spec §11](spec.md)). It builds on [job-table.md](job-table.md)
(claims, tokens, transactions) and [job-queue.md](job-queue.md) (publication, delivery, the
reconciler).

The guarantee is unchanged, and still kept only by the token guards: each job accepts at
most one result, and every succeeded job has exactly one. What this milestone adds:
- the accepted result is bound to its files: `job_attempts.result_digest`;
- no replacement Spark work starts while an earlier attempt's process tree survives;
- nothing an attempt started outlives it.

## A job's steps

[`SubprocessPipeline`](../src/etf_risk/jobs/pipeline.py) runs three CLIs, each as
`<python> -m etf_risk.<module>`, with absolute paths, under a
[launcher](../src/etf_risk/jobs/launcher.py) of its own:

| Step | Command | Writes |
|---|---|---|
| windows | `windows --snapshot S --processed-root <abs> --kind K --window-days N --stride N --anchor A --out-root <run dir>/windows --name <name>` | `<run dir>/windows/S/<name>/` |
| spark_pipeline | `spark_pipeline --windows <that folder> --out-root <run dir>/output --run-id <run id>` | `<run dir>/output/S/<name>/<run id>/` (the run folder) |
| verify | `verify --run <run folder> --sample-ticker T` | `verify.json` in the run folder |

The job's parameters ([`params.py`](../src/etf_risk/jobs/params.py)):
- snapshot, window kind, window days, stride (at least 21: a job has no `--allow-dense-stride`),
  anchor, and the ticker verify samples;
- unknown keys are refused;
- `submit` records the SHA-256 of the snapshot's return files and `quality_report.json`, and
  the worker checks them again before step 1. A difference fails the attempt for good.

The run folder is `<output root>/<store id>/job-<id>-attempt-<n>/`. The store id
([job-table.md](job-table.md)) keeps a recreated job table from reusing old folders.

The step's environment is built from an allowlist, so no service URL or password reaches a
step. It holds:
- the attempt's marker, `ETF_RISK_ATTEMPT=<store id>:<run id>:<attempt key>`, where the key
  is the first 16 hex digits of SHA-256(token); the token itself never leaves the worker;
- `TMPDIR` and `SPARK_LOCAL_DIRS` in `<run dir>/.work`, which is also the working directory, so
  `spark-warehouse` lands there too;
- `java.io.tmpdir` in `.work`, through `SPARK_SUBMIT_OPTS="-Djava.io.tmpdir=… -XX:-UsePerfData"`.
  The macOS JDK ignores `TMPDIR`. `JAVA_TOOL_OPTIONS` is never used: its "Picked up" notice
  would replace the Java version that `run.json` records;
- `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` naming this interpreter. Without them Spark's
  Python workers run whatever `python3` comes first on `PATH`; outside `uv run` that is not the
  project's.

## Accepting a result

A run counts as a result only if all of these hold:
- every step exited 0;
- `run.json` has status `ok`;
- every count in `checks.json` is 0;
- `verify.json` reports no mismatch and the same breached windows;
- each of the four tables has its `_SUCCESS` file.

Then the worker:
1. removes `.work`;
2. writes `attempt.json` (worker, steps with exit codes, times, lock waits and peak memory,
   the settings, and `code_state()`);
3. writes `manifest.json`, the run folder's manifest ([`runs.py`](../src/etf_risk/runs.py));
4. renews once more;
5. calls `accept_result(claim, digest)`. The store records the digest in the same
   token-guarded transaction ([job-table.md](job-table.md)).

Nothing in the folder changes afterwards.

## Failures

The worker classifies a failure from the records, not from the exit code alone: an uncaught
exception exits 1, as "checks failed" does.

| What happened | Result |
|---|---|
| exit 3 (an input checksum differs); `run.json` status `checks_failed`; a verify mismatch; parameters or input checksums that do not fit | failed, not retryable |
| a signal; a step over its time limit; status `failed`; a missing record; the host lock still busy after the wait; a launcher that failed | failed, retryable (the job is requeued until `max_attempts`) |
| a renewal refused; a deadline passed without a renewal | fenced: nothing more is written |

## Deadlines and the watchdog

Leases in the job table are wall-clock times. Every local deadline uses the host's
monotonic clock ([`timing.py`](../src/etf_risk/jobs/timing.py)):

| Setting | Value | Role |
|---|---|---|
| lease | 60 s | the store's `DEFAULT_LEASE` |
| renew_interval | 10 s | time between renewals while a step runs |
| fence_margin, M | 10 s | the deadline is `F = m0 + lease − M`, with `m0` just before the last successful renewal started |
| watchdog_tick, t_w | 0.5 s | how often a launcher looks at its deadline |
| term_grace + kill_confirm, G | 5 + 2 s | SIGTERM, then SIGKILL, then the tree must be gone |
| safety, ε | 2.5 s | M ≥ t_w + G + ε |

The launcher is a process of its own:
- It receives absolute deadlines over a pipe: a handshake first, then one line per successful
  renewal, each with a sequence number. The handshake also checks that the worker and the
  launcher read the same clock.
- It ends the tree once `now ≥ F`. The tree is therefore gone by `F + t_w + G`, before the
  lease can expire, whatever the worker is doing: blocked in a database call, stopped or
  dead.
- The worker's own timeouts play no part in this: no time limit is claimed for a whole
  database operation.

On each tick the launcher:
1. checks whether its deadline has passed. If it has, it fires, and firing is terminal;
2. only otherwise reads the waiting lines. A line moves the deadline only if its sequence
   number is newer, its deadline is later, and that deadline is still in the future.

So lines that queued up while the launcher was stopped cannot revive an expired watchdog, and
no line can push the deadline past what the worker granted
(`test_stopped_past_its_deadline_…` and `test_stopped_briefly_…` in
[tests/test_jobs_launcher.py](../tests/test_jobs_launcher.py)).

The worker also checks F on every 1 s tick. It renews before each step and before acceptance,
fences itself once F passes without a renewal, and never starts a step, or an acceptance call,
after F. An acceptance transaction that started before F may still commit after it:
correctness does not rest on F but on the attempt's token in the job table, which guards that
write as it guards every other, so a job still has at most one accepted result.
Closing the pipe (EOF) makes the launcher end the tree. If the launcher does not act within
the kill grace plus 10 s, because it is stopped, the worker ends the tree itself.

## The host execution lock

Before a step starts, its launcher:
- takes an exclusive `flock` on the host's lock (`~/.cache/etf-risk/locks/spark-exec.lock`;
  tests use their own);
- waits until no process of another launcher's tree survives. A registry next to the lock has
  one file per launcher whose tree may still run, which also finds the orphans of a launcher
  that was killed.

Both waits are bounded together by the step limit + G + 30 s; after that the attempt fails as
retryable ("execution lock busy"). The step's driver inherits the lock. PySpark closes
inherited descriptors before it starts the JVM, and the JVM exits when the driver's pipe
breaks; the survivor check covers that window.

So no replacement Spark step starts while an earlier tree survives, even when the whole tree
is stopped (watchdog included) or the wall clock jumps. On this machine, steps run one at a
time, which is the memory rule of spec §11.

## Ending a process tree

[`processes.py`](../src/etf_risk/jobs/processes.py):
- **Membership.** Each launcher leads a session of its own, and nothing below it calls
  `setsid`. An attempt's processes are those in the launcher's session that carry its marker.
  PySpark's daemon moves itself and its Python workers to a process group of their own
  (`pyspark/daemon.py`: `os.setpgid(0, 0)`), so a process-group kill would miss them; the
  session does not. A reused pid never counts: the marker must match.
- **Termination.** SIGTERM to all, so the JVM's shutdown hooks can delete its scratch; SIGKILL
  after the grace; then rescans until nothing is left.

## After a lost database connection

[`store.py`](../src/etf_risk/jobs/store.py), "Connections":
- the store replaces a broken connection only at the start of an operation, and after a ping
  that fails when the connection sat idle for 60 s. A ping never uses PyMySQL's
  `reconnect=True`, which would drop the session settings;
- a transaction whose connection broke is abandoned with it: its remaining statements never
  run on a new connection, since they would commit one by one there;
- a broken connection gets no ROLLBACK, and the failed operation is not replayed;
- a COMMIT whose reply was lost is resolved by repeating `accept_result`, which reports the
  acceptance for the same token and digest.

Session settings ([`mysql.SERVICE_SESSION`](../src/etf_risk/jobs/mysql.py)), for liveness
only: connect 3 s; read and write 5 s per I/O; `innodb_lock_wait_timeout` 2 s, below the read
timeout, so lock waits end as definite conflicts; `wait_timeout` 120 s, so a frozen client's
open transaction cannot hold row locks for long.

The worker retries `accept_result` and `fail_attempt` after a lost connection while F is
ahead, starting no try at or after it, and renewals at the next interval.

## Kafka group timing

| Setting | Value | Why |
|---|---|---|
| `group.protocol` | `classic` | `session.timeout.ms` is ignored under `consumer` |
| `session.timeout.ms`, `heartbeat.interval.ms` | 15 s, 3 s | a stopped or crashed worker leaves the group well before its lease can expire |
| `max.poll.interval.ms` | attempt limit + G + 60 s = 967 s | `serve()` does not poll while a pipeline runs. A run that outlasted the interval would make the worker leave the group, and a standby could take the partition |
| `socket.timeout.ms` | 10 s | a commit or publication waits at most that long per request |

Under the classic protocol, a joining standby waits for a busy worker to poll before it gets
the partition; `test_a_standby_gets_the_next_job_only_once_…` shows this against Kafka. The
recovery times of E2 include that wait.

## Starting, stopping and sweeping

`python -m etf_risk.jobs` ([`cli.py`](../src/etf_risk/jobs/cli.py); the README's runbook has
the commands). The subcommands are `init-db`, `create-topic`, `submit`, `worker`,
`reconciler`, `status [--check]`, `cleanup` (a dry run) and `export`.

The worker:
- **Restarts its serve loop** in the same process, with backoff, after transport errors only:
  a lost connection, a claim race, or a Kafka error that is not fatal. Any other error ends it
  with exit code 1.
- **Stops gracefully on SIGTERM or SIGINT.** It ends the running tree, fails the attempt as
  retryable (so the job is requeued at once), and leaves the consumer group. On a job's last
  attempt that fails the job, so batches drain before their workers stop.
- **Sweeps at startup** (`startup_sweep`):
  - it ends the trees of this store's attempts that are no longer valid;
  - it keeps every valid active one, whoever runs it;
  - it leaves other stores' trees alone;
  - it removes only the scratch of attempts that ended;
  - with the database out of reach, it does nothing.

`submit` exits 75 when the insert's outcome is unknown (its COMMIT reply was lost) and is
never repeated on its own.

## Known limits

- **One machine.** The lock, the registry and the markers are per user on one host. The
  launcher's clock handshake confirms that the worker and its launchers read the same
  monotonic clock.
- **Restarts.** A worker killed with SIGKILL is not restarted by anything in the project. A
  standby worker in the same group takes over its partition, or the session harness of the
  recovery experiments (M3) restarts it.
- **Worker memory.** The worker process imports pandas and pyarrow (through `params.py` and
  provenance); its memory is in the status below.

## What is checked where

- **Offline:**
  - [tests/test_jobs_launcher.py](../tests/test_jobs_launcher.py): the watchdog, with real
    process trees (a moved process group, a double-forked orphan), pause and resume with
    queued stale lines, the lock (also held by a process that is no launcher), survivors,
    the handshake, the step limit, EOF and SIGTERM;
  - [tests/test_jobs_pipeline.py](../tests/test_jobs_pipeline.py): the pipeline with stand-in
    steps. It covers the result rule and records; refused, failing and hanging renewals,
    including the watchdog ending the tree while the worker is stuck; stopping; the
    classification; and the environment;
  - [tests/test_jobs_reconnect.py](../tests/test_jobs_reconnect.py): reconnection. A break
    inside a transaction is never continued on a new connection, a lost COMMIT reply is
    resolved by a repeat, and idle pings;
  - [tests/test_jobs_sweep.py](../tests/test_jobs_sweep.py), test_jobs_params.py,
    test_jobs_timing.py, test_jobs_events.py and test_jobs_cli.py;
  - the identity and digest constraints in test_jobs_store.py.
- **Spark-marked:** [tests/test_jobs_worker_spark.py](../tests/test_jobs_worker_spark.py)
  runs the real steps through `Worker` and compares the accepted result with a direct run, by
  content.
- **Against the services:**
  - test_jobs_mysql.py: `KILL CONNECTION`, and session settings after a reconnect;
  - test_jobs_kafka.py: the standby and the poll interval;
  - [tests/test_jobs_live_pipeline.py](../tests/test_jobs_live_pipeline.py), with
    `ETF_RISK_LIVE_PIPELINE=1`: this milestone's acceptance runs.
- **[tests/mutation_check.py](../tests/mutation_check.py)** adds 18 mutations for this
  milestone, 49 in all ([job-queue.md](job-queue.md), "What is checked where"). Among them:
  - a reconnect inside a transaction, disconnects treated as conflicts, and
    `ping(reconnect=True)`;
  - the watchdog reading its lines before its deadline check;
  - a tree found by process group;
  - a step started without the host lock.

## Status on 2026-10-23 (`feature/worker-pipeline`)

- **Offline:** the whole suite: 551 passed and 29 skipped (the tests that need MySQL, Kafka or
  ETF_RISK_LIVE_PIPELINE). The Spark-marked end-to-end test passed.
- **Against MySQL 8.4.13 and Kafka 4.3.1** on fresh containers: the job suites, run with the
  README's command (all of `tests/test_jobs_*.py`) on 6d8a232, 463 passed and 10 skipped. The
  10 skipped are the acceptance cases: they also need ETF_RISK_LIVE_PIPELINE, and their own
  runs are reported under "Acceptance runs" below. The 463 include the live reconnect tests
  (`KILL CONNECTION`, and a ping after an idle period) and the standby test.
- **Acceptance runs** (test_jobs_live_pipeline.py, 10 cases):
  - **First run:** 4 passed. 6 failed on three faults of the test harness: an attribute that
    hid a method, the test's own MySQL connection lost during the stalls, and a standby that
    could win the partition before worker A did.
  - **After the fixes:** the 6 passed.
  - **Final run** of all 10, on the final code: 10 passed in 11 min 20 s. It also checked
    the temporary folders: no new Spark, PySpark or JVM entries.
  - **What the cases showed:**
    - **A worker killed in step 2:** its launcher ended the tree on EOF. Attempt 1 ended
      expired, and attempt 2 was accepted.
    - **A worker stopped alone:** its launcher's watchdog ended the tree (outcome `deadline`)
      within F + t_w + G. Attempt 2's Spark step started after attempt 1's tree had ended.
      On SIGCONT the old worker was fenced, and its renewal count did not change.
    - **A whole tree stopped:** the replacement started no step until the frozen tree was
      resumed and had ended itself.
    - **A step over its limit:** three attempts failed (`timeout`), the job failed, and
      nothing was left.
    - **Database stalls:** `LOCK TABLES`, `docker compose pause` and `restart` cost 0, 1
      and 2 failed renewals. Each run continued under its first attempt, with no manual
      restart.
    - **A Kafka restart during a run:** no effect on the run, and a later submission ran.
    - **A starting worker:** its sweep kept another worker's running attempt.
- **Mutation checks** (49):
  - **Offline:** 47 of 47 caught; the 2 that need MySQL were skipped. In the first offline
    run, `no-host-lock` survived. The survivor check also stops a launcher whose
    predecessor's tree is registered. A new test now holds the lock outside any launcher.
  - **Against MySQL and Kafka:** 49 of 49 caught, none at the timeout.
- **Memory.** These figures are informational: four containers of another project shared
  Docker's VM throughout, and the host had about 1.3 GiB available.
  - **The step trees** (peak summed RSS, sampled every 0.5 s by the launchers; the range over
    the first and the final acceptance run):

    | Job | windows | spark_pipeline | verify |
    |---|---|---|---|
    | calendar-year | 2.5–3.0 s, 0.12 GiB | 22.1–22.6 s, 0.66–0.79 GiB | 9.5 s, 0.45–0.49 GiB |
    | stride 21 | 1.5 s, 0.12 GiB | 44.8–50.4 s, 1.19–1.36 GiB | 11.0–11.5 s, 0.57–0.58 GiB |

  - **The job processes** (peak RSS during a calendar-year job): the worker 63.0 MiB and the
    reconciler 51.6 MiB.
  - **MySQL:**
    - 345 MiB (67%) after the live job suites on a fresh container;
    - 501 MiB (98%) after the live mutation session (one full run and 49 shorter ones) on
      another fresh container.
  - **Kafka:** 361 to 415 MiB (56–65%).
  - **`docker compose restart` resets a container's `memory.peak`.** MySQL read 226 MiB after
    the acceptance runs' restarts, below the 345 MiB that container had reached earlier. The
    recovery harness must read peaks before each restart it injects.
- **Not done:** the isolated memory-budget check, with no other project's containers in the
  VM. Those containers were running throughout and were left alone.

*AI contribution: written with Claude Code (Opus 5.5).*
