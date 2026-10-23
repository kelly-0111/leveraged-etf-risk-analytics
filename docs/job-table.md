# Job table: claims, tokens and transactions

How the job store ([`src/etf_risk/jobs/store.py`](../src/etf_risk/jobs/store.py)) keeps the
guarantee of [spec §11](spec.md): each job accepts at most one result, and every succeeded
job has exactly one accepted result. A job may execute more than once. The example follows
two workers, A and B, and job 7, with a lease of 60 seconds. How jobs reach the workers
through Kafka, and how the reconciler requeues and republishes them, is in
[job-queue.md](job-queue.md).

## claim(): two guarded updates

A claim tries two conditional updates of the job's row, in one transaction:

```sql
-- 1. a queued job
UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1, attempt_token = :token,
       lease_expires_at = :lease_expires_at, published_at = NULL, version = version + 1, updated_at = :now
 WHERE job_id = :job_id AND status = 'queued';
-- 2. only if 1 matched no row: a running job whose lease has expired, with attempts left
UPDATE jobs SET ... (the same)
 WHERE job_id = :job_id AND status = 'running' AND lease_expires_at <= :now
   AND attempt_number < max_attempts;
```

The WHERE clause is the guard; the number of rows matched is the answer. If one update matched,
the same transaction reads the new attempt number, marks the previous attempt `expired` (after
a takeover only), and inserts the new attempt's row: its token, its run id `job-7-attempt-<n>`
and its output folder. If neither matched, a read only says why (finished, lease held, not
found). The one write that can follow, failing a job whose last attempt's lease expired,
carries its own guard on the token that read saw.

## Token checks

Renewal, acceptance and failure all use the same guard:

```sql
UPDATE jobs SET ... WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token;
```

There is no time in it: a token holds until a claim replaces it, and an update that matches no
row means the worker has been fenced off. Acceptance sets `succeeded`, a terminal status, and
clears the token, so no token matches afterwards: at most one result is accepted. A CHECK
constraint ties `accepted_attempt` to `succeeded`, so a succeeded job names exactly one.

## Two workers, one job

| Time | Worker A | Worker B | Job 7 afterwards |
|---|---|---|---|
| 0 s | claim: update 1 matches; attempt 1, token tA, lease until 60 s | | running, attempt 1, tA |
| 5 s | | a duplicate delivery; claim: neither update matches, refused (lease held) | unchanged |
| 10 s | renew with tA: lease until 70 s | | running, attempt 1, tA |
| 10–75 s | stalls, no heartbeat | | |
| 75 s | | claim: update 2 matches (70 ≤ 75); attempt 2, token tB; attempt 1 marked expired | running, attempt 2, tB |
| 80 s | renew with tA: no row matches, so A is fenced off and stops | | unchanged |
| 90 s | | accept with tB: succeeded, accepted attempt 2 | succeeded |
| 95 s | had A not stopped, accept with tA: no row matches, and the accepted attempt's token is tB, so false | | unchanged |

Job 7 executed twice, in `job-7-attempt-1` and `job-7-attempt-2`, and accepted one result. Had
nobody claimed it at 75 s, A's renewal at 80 s would have matched, since tA would still be
current, and A could have finished: the lease decides only when a takeover may happen.

## At the same moment

If A and B claim queued job 7 at the same instant, both updates target the same row. In
MySQL, InnoDB lets the first lock the row and makes the second wait; when the first commits,
the waiting update reads the row as committed, not as an earlier snapshot of its own, finds
it running, and matches nothing. Update 2 matches nothing either, since the new lease is
live, so B is refused. In SQLite, `BEGIN IMMEDIATE` takes a write lock on the whole database,
so B's transaction starts only after A's has committed: the same outcome, for another reason.
Likewise when A accepts while B takes over an expired lease: whichever transaction holds the
row first decides, and the other then finds the job succeeded, or a token that is not its own.

## Transactions

- Every operation is one transaction. Apart from `submit` and `mark_published`, each writes
  both tables: the update of `jobs` decides, and the write to `job_attempts` records; that
  write must touch exactly one row, or the store raises and both tables roll back.
- Any exception rolls the transaction back, including a simulated crash. The tests raise at
  each gap between two statements (`FAULT_POINTS`) and check both tables afterwards.
- Every transaction locks the `jobs` row before any `job_attempts` row, and none spans a
  pipeline run: locks last milliseconds, and a crashed worker leaves an expiring lease, not a
  held lock.
- A COMMIT that fails may still have taken effect, so repeating an operation must be safe:
  `accept_result` returns true when the accepted attempt's token is the caller's.
- In MySQL, an operation rolled back by a deadlock or a lock wait timeout runs again, up to
  three runs in all.

## The accepted result, the store's identity and lost connections (M2)

- **The digest.** Acceptance records the result's run digest
  ([`runs.py`](../src/etf_risk/runs.py): the SHA-256 of a canonical manifest of the run
  folder's files) in its `job_attempts` update, inside the token-guarded transaction.
  `job_attempts_accepted_has_digest` requires a digest exactly for accepted attempts. A
  repeat after a failed COMMIT counts as accepted only for the same token and digest. The
  decision and the content it accepted are bound together.
- **The store id.** `job_store` holds one row, the store id, written once by `init-db`. Job
  and run ids start again at 1 when the tables are created anew, so folders, process markers
  and caches name an attempt by store id and run id together.
- **Lost connections.** Given a connection factory, the store replaces a broken connection
  only at the start of an operation, never inside a transaction. A transaction whose
  connection broke between two statements is abandoned: its later statements would otherwise
  commit one by one on a new connection, and the second statement of `accept_result` could
  then mark an attempt accepted while the job stayed running. A broken connection gets no
  ROLLBACK, and the failed operation is not replayed. Details are in
  [worker-pipeline.md](worker-pipeline.md).

## What is checked where

- [`tests/test_jobs_store.py`](../tests/test_jobs_store.py) and
  [`tests/test_jobs_worker.py`](../tests/test_jobs_worker.py) run on SQLite, and on MySQL as
  well when `ETF_RISK_MYSQL_URL` is set. On SQLite, competing connections run one after another
  under the database lock: those runs check the state logic, not InnoDB's row locks.
- [`tests/test_jobs_mysql.py`](../tests/test_jobs_mysql.py) checks the MySQL adapter offline
  and, against a server, the InnoDB behaviour the SQL relies on (setup in its docstring and in
  [`docker/compose.yaml`](../docker/compose.yaml)).
- [`tests/mutation_check.py`](../tests/mutation_check.py) breaks the guards and checks on
  purpose, one at a time, in a scratch copy of the repository, and expects the job tests to
  fail within a timeout. It covers the token, lease and attempts-left conditions, the
  rollback, the one-row check on `job_attempts` writes, the `version` bump, conflict
  detection, the output folder check, and the queue's guards in
  [job-queue.md](job-queue.md).
- Status when this table was merged (PR #7), on 2026-10-22:
  - with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set, all 222 cases
    passed, in five runs in a row;
  - without the URL, 114 passed and the 7 tests that need a server were skipped;
  - breaking any one of eleven guards and checks by hand made at least one test fail.
    Those mutations were not recorded as a list; `tests/mutation_check.py` rebuilds them
    from this description;
  - on top of main at e55f76b (after the caching experiment), the job tests gave the same
    counts and the whole suite passed (350 passed, 7 skipped);
  - the MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget
    (cgroup `memory.peak`, which includes page cache).

  The current status of the job tests, with the Kafka delivery of PR #8, is in
  [job-queue.md](job-queue.md).

*AI contribution: written with Claude Code (Opus 5.5).*
