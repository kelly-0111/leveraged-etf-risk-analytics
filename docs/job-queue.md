# Job queue: publication, delivery and the reconciler

How a job reaches a worker through Kafka, and what happens when a step on the way fails:
milestone 2 of the systems extension ([spec §11](spec.md)). It builds on
[job-table.md](job-table.md), which explains claims, attempt tokens and transactions. The
guarantee is unchanged: each job accepts at most one result, and every succeeded job has
exactly one accepted result. A job may execute more than once.

## The path of a job

1. **Submit** ([`queue.submit_job`](../src/etf_risk/jobs/queue.py)). The job is inserted
   as queued, at version 0. Its id is published to the topic, and the submitter waits for
   the broker's confirmation. If the confirmation arrives, `published_at` is recorded.
2. **Deliver** ([`Worker.serve`](../src/etf_risk/jobs/worker.py)). A worker's consumer
   polls the id. The worker claims the job, then commits the message's offset. That is
   the acknowledgement. It then runs the pipeline and accepts the result.
3. **Reconcile** ([`reconciler.py`](../src/etf_risk/jobs/reconciler.py)). Every few
   seconds, the reconciler requeues jobs whose lease expired, then publishes queued jobs
   with no recorded publication.

Kafka is reached through [`kafka.py`](../src/etf_risk/jobs/kafka.py) (confluent-kafka). The
offline tests use [`simulated.MemoryQueue`](../src/etf_risk/jobs/simulated.py), which
models only what the job system relies on.

## Settings

| Setting | Value | Why |
|---|---|---|
| Producer `acks`, `enable.idempotence` | `all`, on | §11: with one broker and no replica, `acks=all` means that broker wrote the message |
| `CONFIRMATION_TIMEOUT` | 10 s | how long submit and the reconciler wait for the delivery report; librdkafka's message timeout is the same, so `False` is final. It means "not confirmed", not "not written" |
| Consumer `enable.auto.commit` | `false` | the worker commits after its claim, or after deciding that the job needs nothing |
| Consumer `auto.offset.reset` | `earliest`, set explicitly | a consumer group that never committed starts at the first message, so a job published before its group first starts is still delivered; librdkafka's default, `latest`, would skip it |
| `PUBLICATION_GRACE` | 30 s | a never-claimed job is published again only 30 s after it was queued, longer than its submitter waits for its own confirmation |
| Grace for a requeued job | none | nobody else publishes it, so it goes in the pass that requeued it |
| `RECONCILE_INTERVAL` | 5 s | time between passes |
| `DELIVERY_RETRIES` | 5, 1 s apart | how often `serve()` tries one message again after errors before its acknowledgement; the next error is raised, and the message stays uncommitted |
| Job id in a message | decimal, 1 to `MAX_JOB_ID` = 2⁶³ − 1: at most 19 digits, no sign, spaces or leading zeros | the largest id both job tables hold (SQLite's INTEGER is signed 64-bit). Any other payload is malformed |

## Recording a publication: the version guard

```sql
UPDATE jobs SET published_at = :now, version = version + 1, updated_at = :now
 WHERE job_id = :job_id AND status = 'queued' AND published_at IS NULL AND version = :version;
```

`published_at` means that a message for the job's *current* queued state was confirmed, so
the reconciler need not publish the job again. A CHECK constraint allows it only while the
job is queued, and a claim clears it.

The version guard prevents a lost job. Suppose a message is published and the broker
confirms it. Before the submitter records the confirmation, a worker consumes the message,
claims the job and fails it back to queued. The message is gone. A guard on the status alone
would now record the publication. The job would then be queued with nothing to deliver it,
and the reconciler would never publish it again. With the version read before publishing,
the late record matches no row, and the reconciler publishes the job in its next pass.
`test_a_confirmation_after_the_job_moved_on_is_not_recorded` follows exactly this case.

## Requeuing an expired lease: the token guard

```sql
UPDATE jobs SET status = 'queued', attempt_token = NULL, lease_expires_at = NULL,
       version = version + 1, updated_at = :now
 WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token
   AND lease_expires_at <= :now AND attempt_number < max_attempts;
```

The token is the one the reconciler read with `expired_leases()`. The same transaction
marks that attempt as expired. With no attempts left, the job fails instead, through the
same statement claim uses (`_exhaust`). The lease condition alone is not enough. The
reconciler may read A's token, then B takes the job over, and B's lease expires as well
before the reconciler's change. Without the token, the change would requeue B's attempt on
A's token (`test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too`).

## A job, two failures

Job 9, with a 60 s lease:

| Time | What happens | Job 9 afterwards |
|---|---|---|
| 0 s | submit: inserted; published; the confirmation is lost, but the message was written | queued, no publication recorded; 1 message |
| 1 s | worker A polls the message, claims attempt 1, and dies before committing | running, attempt 1, lease until 61 s |
| 30 s | reconciler: the job is running, so it needs no publication | unchanged |
| 46 s | A has restarted. The group drops A's old member after the 45 s session timeout, and the new consumer starts at the last commit and gets the same message. The claim is refused (lease held) and the offset committed | unchanged |
| 61 s | reconciler: the lease has expired; it requeues with A's token; attempt 1 is expired; it publishes the job in the same pass and records the confirmation | queued, publication recorded; 2 messages |
| 62 s | A polls the new message, claims attempt 2, commits, runs and accepts | succeeded, accepted attempt 2 |

Job 9 executed twice and accepted one result. Had the job still been queued at 30 s, with
its first confirmation lost, the reconciler would have published it then. The duplicate
message would later find the job running or finished, and the claim would refuse it.
`test_a_crash_between_claim_and_commit` runs this sequence offline and against Kafka.

## What the worker does with a delivery

- **Acknowledgement** is a synchronous commit of the message's offset + 1, the next
  offset to read. It happens right after the claim, or at once when the claim is refused.
- **An error before the acknowledgement** rewinds the consumer to the message (a seek) and
  tries again; a consumer that keeps running does not see an uncommitted message again by
  itself. After `DELIVERY_RETRIES` tries in a row for one message, the next error is raised
  and ends `serve()`. The message stays uncommitted, and the consumer rewound to it, so
  this consumer or a restarted worker reads it again. The message is never skipped: the
  job may have a recorded publication, and the reconciler would not publish it again.
- **An error after the acknowledgement** is logged. The job's lease then expires, and the
  reconciler requeues it.
- **A failed commit** is logged, and the job goes on. It is claimed, so a later delivery of
  the same message is refused.
- **A message with no valid job id** (see Settings) is committed and skipped before
  anything touches the database, so it cannot block the partition or stop the worker.
  The format and the length are checked before any conversion, since `int()` refuses more
  than 4,300 digits; the range is checked after it.

## Known limits

- **A long outage stops the worker.** With the defaults, an error before the
  acknowledgement that lasts longer than about five seconds, such as an unreachable
  database, ends `serve()` with that error. Something must then restart the worker: by hand
  for now, and a Compose restart policy once the worker runs there.
- **A crashed worker frees its partition late.** It leaves the group only after the
  session timeout (45 s by default). The live tests close their consumers instead, which
  leaves the group at once.
- **`max.poll.interval.ms` (300 s by default).** It is long enough for the simulated
  pipeline. The real pipeline's runs need a check against it.
- **One partition, one job at a time**, as §11 plans: no claims about throughput.

## What is checked where

- [`tests/test_jobs_reconciler.py`](../tests/test_jobs_reconciler.py) and
  [`tests/test_jobs_queue.py`](../tests/test_jobs_queue.py) use the in-memory queue. They
  run on SQLite, and on MySQL as well when `ETF_RISK_MYSQL_URL` is set. They cover:
  - the guards and the grace period;
  - the job-id format, including a 5,000-digit payload and ids beyond the range, each
    followed by a valid job that must still run;
  - the worker's commits, rewinds and bounded retries;
  - whole scenarios, including a seeded run with lost publications and crashes at every
    fault point.
  Tests that run a loop (`serve()`, the reconciler's `run()`) stop it themselves, after a
  number of tries or a few seconds, so a broken guard makes them fail rather than hang.
- [`tests/test_jobs_kafka.py`](../tests/test_jobs_kafka.py) checks the settings offline.
  With `ETF_RISK_KAFKA_BOOTSTRAP` set, it checks against Kafka 4.3.1 from
  [`docker/compose.yaml`](../docker/compose.yaml):
  - delivery to a fresh consumer group, and `latest` for comparison;
  - confirmation, including an unreachable broker;
  - commits and rewinds;
  - a 5,000-digit payload ahead of a job: both committed, and the job runs;
  - a message left uncommitted after the retries, for a restarted worker;
  - two end-to-end scenarios.
- Status on 2026-10-23:
  - **Offline:** 200 passed, and the 17 tests that need MySQL, Kafka or confluent-kafka
    were skipped.
  - **With Kafka 4.3.1** (the job table on SQLite): 210 passed, and the 7 tests that
    need MySQL were skipped.
  - **With MySQL 8.4.13 as well:** 353 passed, before the job-id validation, which
    changes nothing that reaches the database.
  - **The whole suite:** 411 passed and 15 skipped. That run came before the bounded
    retries, the job-id validation and the test fixes; the rest of the suite does not
    use these files.
  - **Mutation checks:** 22 guards and settings were broken on purpose, one at a time,
    in 25 test runs: three were run both offline and against Kafka. Each run had a
    timeout. The 22 include 4 for the job-id format and range. Tests failed in all 25
    runs; none ran into the timeout. Before the fixes, three ran until it:
    - a claim that keeps the publication, through `serve()`'s unbounded retries;
    - the grace boundary off by one, through a test that waited for the publisher to
      stop the reconciler's loop;
    - the rewind removed, through a test that waited for a failing claim to come back.
  - **Memory:** spec §11 records the peaks. MySQL reached 511 of its 512 MiB over about
    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That
    is limited headroom, not evidence that longer runs stay within the limit.

*AI contribution: written with Claude Code (Opus 5.5).*
