# Recovery experiments (E1, E2): outline

Author: _to be written by the author after review. Beyond spec §11, the only decisions by the
author are those in 1.1._

_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised four times from the author's
reviews (history at the end). This is an outline for review, not an approved Part A: everything not
in 1.1 or cited from spec §11 or M2 is Claude Code's proposal, and the decisions in section 8 are
proposals only. Design inputs: commit `6d8a232` (`feature/worker-pipeline`) and M2's final report in
it ([worker-pipeline.md](worker-pipeline.md), "Status on 2026-10-23"); `e4adc38` later corrected
that report's live job-suite count, which this outline does not use. The SQL cross-check, its
fixture, the frozen expected rows and the run that validated the queries are in
[recovery-sql.md](recovery-sql.md); the author accepted that run as tooling evidence, not as approval
of Part A. Since 2026-10-24 the tooling exists on `feature/recovery-harness`, written with Claude
Code at the author's decision (section 9). Its offline tests passed on 2026-10-24, one of them a
synthetic batch run end to end without services; none of it has run against the services, and no
formal experiment was run._

## 1. Questions and scope

Spec §11 asks:

- **E1.** Does each job accept at most one result, and does every successfully completed job have
  exactly one, even when jobs execute more than once?
- **E2.** After a worker crash (before or after its claim), a broker restart or a database restart,
  how long until the job runs again and finishes, and is any job lost or accepted twice?

It plans to inject each failure on purpose and to record detection and recovery times, executions
per job, accepted results per job and lost jobs; an accepted result is correct when its run passes
every check (§6) and matches a reference run by content. The token guards alone keep the guarantee
([job-table.md](job-table.md)); the time settings decide only when a takeover may happen. So E1
tests the guards under real failures, and E2 measures what the time settings and recovery paths
cost.

M2's acceptance runs (`tests/test_jobs_live_pipeline.py`) ran ten cases once each on a shorter clock
(lease 24 s, renewals every 4 s, session timeout 10 s: "M2's clock" below), and the final run passed
all ten. E1 and E2 repeat each case (8.1) on the clock of 8.2 and record times and counts for every
injection (section 5), reusing the checks of its `check()` (6.2, 6.5).

### 1.1 Decided or required by the author

How each item is met is Claude Code's proposal, in the sections named.

- **First review (2026-10-23).** Explicit deadlines, with on-time completion, late completion and
  unfinished jobs apart, and no later success erasing a miss (4.2, 4.3). Database acceptance
  correctness apart from event-log completeness, including a crash after the acceptance commits and
  before its event (W5a); repeated reports of one attempt are not multiple accepted results (6.2,
  6.4). No artifacts required of crashed attempts; code identity at each launch; a missing interval
  is unknown (2.3, 6.5). Monotonic durations, and recovery latency `n/a` after acceptance (4.1,
  section 5). Kafka assignment conditions in the predictions and a fixed startup order (2.4, 3.2).
  Full report identity, `store_id` and `worker_id` included (6.4). A defined deadline observation,
  quiescence and consistent snapshot (4.3–4.5). Reference runs under the host lock (2.2); no pooled
  rule-of-three claim (8.1); small SQL fixtures; every case and failed outcome visible (3.1,
  section 9).
- **Second review.** `6d8a232` and its final report as design inputs, with the isolated
  memory-budget check pending (8.3). Peaks before every injected restart, maximum across segments
  (4.6). The partition owner from assignment events, never from `client.id` ordering (2.4).
  `deadline not observed` as an explicit unknown (4.2). The fixtures run against a scratch MySQL
  once no other session's tests run, compared with explicit expected rows and extended to every
  verdict ([recovery-sql.md](recovery-sql.md)).
- **Third review.** Run the fixtures only after the M2 session releases the test window, recheck
  before startup, and remove only this session's container; keep the expected rows frozen and report
  every mismatch, explaining any correction. No restart duration inferred from failed-renewal counts
  (8.2). A shorter outline with the SQL details apart, and a small set of Part A decisions proposed
  with reasons (section 8).
- **Fourth review (2026-10-24).** The 82-row fixture validation counts as tooling evidence, not as
  approval of Part A. Claude Code writes the tooling (the harness, the collector, assignment events,
  launch-time code identity and precise fault-injection hooks) with accurate attribution (section 9).
  The frozen SQL expectations stay as they are. The deadline formulas are reassessed and the
  duration of all 84 proposed jobs is estimated (8.1, 8.2); timing, repetitions and memory
  thresholds stay provisional. Every test or container run waits for coordination with the M2
  session.
- **Fifth review (2026-10-24).** An exclusive window for offline dependency setup and tests. The
  acceptance deadline enforced as the approved policy states; monotonic launcher times for same-host
  overlap checks; deterministic tests for the first acceptance call after F, arming without a change
  of owner, missing crash records, unknown observations, late completion and every frozen SQL
  verdict; a synthetic batch end to end without services; a smaller formal experiment proposed, with
  the 84 jobs kept as an alternative (8.1, section 9).
- **Sixth review (2026-10-24).** The policy stays "no acceptance call starts after F"; the
  database's token guards remain the correctness mechanism, and an acceptance transaction already
  under way may commit later ([worker-pipeline.md](worker-pipeline.md)). The live overlap test
  compares monotonic times; focused mutation checks; a code checkpoint commit without the AI logs. No
  service starts before the M2 session releases the window; then a small live preflight, clearly
  labelled, covering the default clock, the real reference launcher, partition ownership and the
  service-dependent recovery paths, with its outcomes kept apart from formal results (8.6). The
  28-job design is the preferred draft; deadlines, memory rules and runtime estimates are finalized
  only after the preflight (8.1–8.3).
- **Throughout.** No formal experiment, and Part A is not approved. Until the fourth review the work
  was documents only.

## 2. Batch protocol (proposal)

### 2.1 Services, jobs and controls

MySQL 8.4.13 and Kafka 4.3.1 from [docker/compose.yaml](../docker/compose.yaml); the reconciler and
two workers, A and B, as native processes; one job at a time on this machine (spec §11). A session
harness (M3 code, not written) submits jobs, injects failures, takes deadline observations and
container peaks, restarts workers (2.4) and keeps the records (section 9). Each batch starts on
fresh containers and ends with the final snapshot (4.5). Jobs use the parameter sets of M2's
acceptance runs (kinds `calendar-year` and `rolling`, stride 21, snapshot `full-2026-10-12`, 3
attempts; choice in 8.1). Control jobs (case C0) give the failure-free time to finish, T.

### 2.2 Reference runs

One direct run of the three CLIs per parameter set, under the host execution lock, taken as a
launcher takes it: an exclusive `flock`, the wait until no earlier tree survives, and an entry in
the registry, so that a later launcher waits for the reference run's survivors too. A reference run
then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference
runs come before the workers start, so that they delay no measured step. Implemented, not yet run
(the synthetic batch replaces it): the harness drives each reference step through
`etf_risk.jobs.launcher` as the launcher's parent, so the step gets the same lock, registry, marker
and launcher record as a worker's step.

### 2.3 Code identity

Each process records its code identity in its first event when it starts (every worker start, the
reconciler, each `submit`), each step launch records it in `step_started`, and the harness records
it at the start and end of the batch. The identity is `source_digest`, one SHA-256 over the per-file
`source_sha256` map of `provenance.code_state()`, with `uv_lock_sha256`; the commit and the clean
flag are only reported. Implemented and tested offline, not yet run against the services:
`provenance.code_identity()` for starting processes, and `provenance.source_identity()`, the same
two hashes without asking git, for each step launch. A crashed attempt writes no `attempt.json`, so
identity is never read from that file; it is read only for accepted attempts, to find their run
folder (6.2).

### 2.4 Worker startup order and the partition

The topic has one partition, and the group member that owns it gets every delivery.
[kafka.py](../src/etf_risk/jobs/kafka.py) sets no `client.id`, `group.instance.id` or assignment
strategy, so with two live members the owner after a rebalance is not fixed; M2's first acceptance
run failed partly on "a standby that could win the partition before worker A did". Order per batch:
`services ready`, `init-db` and `create-topic`; the reference runs; the reconciler; worker A, then a
wait for its assignment event; worker B, then a wait for the rebalance its join causes; the first
job. The harness identifies the owner from the assignment events alone, before each case and after
each rebalance, and injects into the worker that claimed the job, never into a worker chosen by
name, start order or `client.id` ordering. Implemented: kafka.py writes `assigned`, `revoked` and
`lost` events from its rebalance callbacks, and the harness reads the owner only after a started
worker's first `assigned` event, so a stale assignment is never taken for the owner. The offline
tests and the synthetic batch exercise the events and the harness's reading of them with a
stand-in group; the live Kafka test has not run.

**Restart rule.** A killed worker starts again only once its job has finished (read from the
table), when the other worker is idle; the harness waits for the rebalance and records the new
owner. A worker stopped and then fenced (W6, W7) is first stopped with SIGTERM once its `fenced`
event appears; its attempt is no longer its own, so the stop writes nothing. The only rebalance
inside a recovery window is therefore the one the failure causes.

### 2.5 One job at a time

The harness submits a job, applies its case, takes its deadline observation (4.3), and waits until
the job finishes or its drain limit passes (8.2). A job unfinished at its drain limit ends the batch
(4.4), and the injections not yet made are recorded as not run.

## 3. Failure cases

### 3.1 Cases

Each injection targets one job, in one phase of one attempt. The harness confirms the phase from the
event logs (for W3: after the attempt's `step_started` for `spark_pipeline`, before its
`step_ended`) or, for W5a, from the table; an injection that lands elsewhere is recorded with the
phase it hit and does not count for its case.

| Case | Injection | How | For | Expected path, from the design | Claims / accepted | In M2's live tests |
|---|---|---|---|---|---|---|
| C0 | none (control) | — | E2 | claim, run, accept | 1 / 1 | yes, both parameter sets |
| W1 | SIGKILL of the worker after a delivery, before its claim | hook at `before_claim` (8.4) | E2 | the offset stays uncommitted; after the session timeout the standby gets the partition and the message, and claims attempt 1 | 1 / 1 | no; offline, at the worker's fault points |
| W2 | SIGKILL after the claim, before the offset commit | hook at `after_claim` | E1, E2 | the redelivery to the standby is refused (lease held) and committed; the lease expires; the reconciler requeues and republishes; attempt 2 | 2 / 1; attempt 1 ran no step | no; with the simulated pipeline (`test_a_crash_between_claim_and_commit`) |
| W3 | SIGKILL during `spark_pipeline` | signal, once the step's log exists (as in M2) | E1, E2 | the launcher reads EOF and ends the tree; the lease expires; requeue; attempt 2 | 2 / 1; attempt 1 partial | yes, once |
| W4 | SIGKILL after the pipeline, before acceptance | hook at `after_pipeline` | E1, E2 | attempt 1's complete folder is never accepted; the lease expires; requeue; attempt 2 runs in full | 2 / 1; two complete executions | no |
| W5a | SIGKILL after the acceptance commits, before its `accepted` event | hook at a new fault point between `accept_result`'s return and the event (8.4) | E1 | nothing to recover; the table holds the acceptance and the log lacks its event (6.4) | 1 / 1; no report | no |
| W5b | SIGKILL after the `accepted` event | hook at `after_accept` | E1 | nothing to recover: the offset was committed at the claim | 1 / 1 | no |
| W6 | SIGSTOP of the worker during `spark_pipeline`; SIGCONT after the takeover | signals | E1 | the watchdog ends the stopped worker's tree before its lease expires; requeue; the standby claims attempt 2; after SIGCONT the old worker's renewal is refused, it is fenced, and the harness stops it (2.4) | 2 / 1 | yes, once |
| W7 | SIGSTOP of the worker's whole tree (worker, launcher, Spark); SIGCONT later | signals | E1 | the replacement's step waits for the host lock while the stopped tree survives; after SIGCONT the stopped launcher, past its deadline, ends its tree, and the old worker is fenced and stopped. A stop longer than the replacement's lock wait fails that attempt as retryable | 2 or 3 / 1 | yes, once |
| K1 | Kafka restart while a step runs | `docker compose restart kafka`, after a peak reading (4.6) | E2 | the running job goes on (the worker does not poll during a run); the next delivery waits for the group (3.2) | 1 / 1 | yes, once |
| K2 | a submit while Kafka is stopped | a peak reading, stop Kafka, submit, start Kafka | E2 | the confirmation times out (10 s) and `published_at` stays empty; once Kafka is back and the 30 s grace has passed, the reconciler publishes the job | 1 / 1 | no; an unreachable broker's confirmation in `test_jobs_kafka.py` |
| D1 | MySQL restart while a step runs | `docker compose restart mysql`, after a peak reading | E2 | renewals fail and are tried again; back before F: the attempt goes on; otherwise the worker fences itself, the watchdog ends the tree, and the job is requeued once MySQL is back | 1 or 2 / 1 | yes, once (also a table lock and a pause) |
| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL, after a peak reading | E1, E2 | `accept_result` is tried again while F is ahead, and no try starts after F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`), or, if the hold ends at or after F, makes no acceptance call (`fenced`, during acceptance); either way the job runs again after its lease expires. A try under way at F may still commit: the token decides, not F | 1 or 2 / 1 | no; a lost COMMIT reply offline (`test_jobs_reconnect.py`) |
| X1 | the job id published again, while the job runs and after it succeeded | harness publishes | E1 | each extra delivery is refused (lease held, then succeeded) and committed; no new attempt | 1 / 1 | no; refusals offline (`test_jobs_queue.py`) |

All 14 cases are kept; a case without an injection method is recorded as not run, never dropped.

### 3.2 Expected times and Kafka conditions

Symbols, from [worker-pipeline.md](worker-pipeline.md) and [job-queue.md](job-queue.md), with the
default values: lease L 60 s, renewal interval R 10 s, fence deadline F (L − M after the last renewal
began, M 10 s), kill grace G 7 s, reconciler interval P 5 s, session timeout S 15 s, heartbeat
interval h 3 s, publication grace g 30 s; T is a job's failure-free time to finish.

| Case | Detection event | From the injection to the next claim | Kafka condition |
|---|---|---|---|
| W1 | the standby's `delivered` | about S − h to S + h, plus a poll (1 s) | the killed worker owned the partition; its session expires S − h to S after the kill; the idle standby (2.4) learns of the rebalance at its next heartbeat and rejoins at its next poll |
| W2, W4 | the reconciler's `requeued` | L to L + P (the lease was just set or renewed), plus a delivery | the standby owns the partition from about S + h after the kill, before the requeue: S + h + 1 s < L − R (19 < 50 s at the defaults, 14 < 20 s on M2's clock) |
| W3, W6 | `requeued` | about L − R to L + P, plus a delivery | as W2; a stopped worker (W6) stops heartbeating, so it loses the partition as a dead one does |
| W7 | `requeued` | as W3; then the replacement's step waits for the host lock until the stopped tree is resumed and ended | as W6 |
| K1 | — (the attempt goes on) | n/a | the group re-forms after the restart; a member busy with a job delays a rebalance until its next poll; the owner afterwards comes from the assignment events |
| K2 | the reconciler's `published` | the later of Kafka's return and g after the submit, plus up to P, plus a delivery | a delivery needs an owner again after the restart |
| D1 | `renewal_failed`; then `renewed`, or else `requeued` | none if MySQL is back before F; otherwise once the lease has expired and MySQL is back, plus up to P, plus a delivery | none: the owner stays |
| D2 | `retry` of `accept_result`, or `fenced` during acceptance if the hold outlasted F; then `accepted`, or else `failed_after_ack` or that `fenced`, and `requeued` | as D1 | as D1 |
| W5a, W5b, X1 | — | n/a: after the acceptance, or no failure | a killed worker loses the partition about S after the kill, which delays only the next job (2.4) |

The time to finish adds about T wherever a new attempt starts. At the defaults the windows are about
12–19 s (W1), 60–65 s (W2, W4) and 50–65 s (W3, W6); M2's steps alone took about 34–35 s for the
calendar-year job and 57–63 s for the stride-21 job. The bounds hold only under the conditions in
the last column and are not predictions until the author approves them.

## 4. Clocks, deadlines and snapshots

### 4.1 Clock

Every duration is a difference of two `time.monotonic()` readings on this host: the events' `mono`
([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step
times (`step_started_mono` and `tree_ended_mono` in its record). On macOS this reads a system-wide
clock; the launcher's handshake checks the worker and its launchers, and the harness checks each
process it starts (the `mono` of its first event must lie between the harness's readings just before
the start and just after it read that event). The clock pauses while the host sleeps, so the host
must not sleep during a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock
columns, never for a duration. The harness records `ts` and `mono` together at the start and end of
a batch; a difference in their elapsed times beyond a tolerance (8.5) means a sleep or a clock step
and fails validity (6.1).

### 4.2 Deadlines

When a job's reference instant occurs, the harness records in `batch_jobs`: `deadline_from`
(`submit` for a control; `restored`, the moment the service works again, for K2, D1 and D2;
`injection` otherwise), `deadline_s` (the case's D, 8.2), `deadline_mono` (the harness's `mono` at
that instant plus D) and `max_lag_s` (how late the deadline observation may end and still show an
on-time success). Counting K2, D1 and D2 from their service's return keeps the time a restart takes,
which nothing has measured, out of their deadlines. A job whose injection missed its phase gets C0's
deadline, counted from its submit. Q2 classifies each job from its observation (4.3) and the final
snapshot (4.5):

| Class | Rule | `deadline_met` |
|---|---|---|
| on time | succeeded in the deadline observation, which ended no later than `deadline_mono + max_lag_s` | yes |
| late | not succeeded in an observation that began at or after `deadline_mono`, and succeeded in the final snapshot | no |
| unfinished | queued or running in the final snapshot | no |
| failed | failed in the final snapshot | no |
| missing | no row in the final snapshot | no |
| deadline not observed | succeeded at the end, with no valid observation: a failed read, none at all, a success seen too late, or a miss seen before the deadline | unknown |

A late job stays late: the observation fixes the miss, and the later success does not change it.
`deadline not observed` is an explicit unknown, counted as neither met nor missed. The final
snapshot comes after every drain limit, which comes after every deadline.

### 4.3 The deadline observation

When the job finishes, or at `deadline_mono` if that comes first, the harness reads the job's row
once, in its own connection, as one consistent snapshot; a read that fails is recorded with no
status and is never repeated. A read taken at completion shows a terminal status, which never
changes, so it decides as a read at the deadline would, and no job waits out its whole D. A read can
fail in D1 and D2 when a deadline falls while MySQL is down, as the M2 test's own connection did
during its stalls.

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- observed_from_mono: the harness's time.monotonic() just before the next statement
START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
-- observed_to_mono: just after it returned; InnoDB took the snapshot in between
SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = :job_id;
COMMIT;
```

A terminal status never changes, so a success seen in a snapshot that ended by
`deadline_mono + max_lag_s` is on time within that lag, and a miss seen in one that began at or
after `deadline_mono` stays a miss. The lag, `observed_to_mono − deadline_mono`, is reported for
every job.

### 4.4 Quiescence

A batch is quiescent when nothing can write to the job tables: every job has finished or the last
drain limit has passed; the harness has ended the workers and the reconciler with SIGKILL, so that
no job changes state on the way out (each worker's launcher then ends its tree); none of them is
alive, no attempt's process is left, and MySQL's process list shows no client connection but the
harness's.

### 4.5 The final snapshot

After quiescence: (1) `services peaks`, before any query, closing the last segment (4.6); (2)
`status --check`; (3) the cross-check in one session, with the harness's records in TEMPORARY tables
and Q0–Q3b inside one `START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY`, each result saved as
CSV; (4) `export`; (5) Q0 again. Q0's fingerprint from (3), the same numbers from the export's
`jobs.json` and `job_attempts.json`, and Q0 from (5) must be equal: every store operation inserts a
`jobs` row or raises its `version`, so a write in between would show, and the batch would fail
validity (6.1).

### 4.6 Container peaks by segment

`docker compose restart` resets the restarted container's `memory.peak` (M2's report), and a stop
and start does the same. Before every injected restart or stop (K1, K2, D1, D2) the harness records
`services peaks` for MySQL and Kafka; each reading closes a segment, and the final reading closes
the last. A container's batch peak is the maximum over its segments, and every reading is kept. A
restart with no reading before it leaves that segment unknown: the batch peak is then reported as at
least the maximum of the other segments, marked incomplete.

## 5. Metrics

Durations are monotonic (4.1); t_inj is the harness's `mono` at the injection.

| Metric | Definition | Source |
|---|---|---|
| detection time | t_inj to the case's detection event (3.2) | injection log, event logs |
| time to re-run | t_inj to the `claimed` event of the job's next attempt (W1: its first) | event logs |
| time to finish | t_inj to the job's `accepted` event; unknown if that event is missing | event logs |
| recovery overhead | from the harness's start of `submit` to `accepted`, minus the median of the batch's C0 jobs of the same parameter set | harness log, event logs |
| deadline class, `deadline_met` | 4.2 | Q2 |
| claims per job | rows in `job_attempts` | Q1 |
| executions per job | attempts with a `step_started` for `windows`; complete ones have a `manifest.json`, written only after the result rule held; required of none | event logs, attempt folders |
| accepted results per job | accepted attempts in the table, never the workers' reports (6.4) | Q1 |
| reports per job | matching reports of the accepted attempt, and distinct attempts reported | Q3a |
| unfinished or missing jobs (E2's lost jobs) | Q2's `unfinished` and `missing`, with each job's queue state | Q2 |
| wasted step time | step time of attempts not accepted; a step without a complete launcher record adds an unknown, not zero | launcher records |
| fencing | `renewal_refused` and `fenced` events; the watchdog's end of a tree | worker logs, launcher records |
| liveness | `serve_restarted`, `retry`, `rewound`, `gave_up`, `failed_after_ack`, `consumer_error`, `pass_failed` per process | event logs |
| partition owner | before and after each case | assignment events (section 9) |
| memory | each container's batch peak over its segments (4.6); each step's `peak_rss_bytes` from its launcher record, which outlives a killed worker (a missing record is unknown); the worker's own peak | `services peaks`, launcher records, the harness |

| Case | Detection time | Time to re-run | Time to finish, overhead |
|---|---|---|---|
| C0 | n/a: no failure | n/a: no failure | yes (the control) |
| W1–W4, W6, W7 | yes | yes | yes |
| W5a, W5b | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance |
| K1 | n/a for the job; the broker's recovery is the restart to the next `delivered` | n/a: the attempt goes on | yes |
| K2 | yes | yes | yes |
| D1, D2 | yes | yes if a new attempt started; otherwise n/a | yes |
| X1 | n/a: no failure | n/a: no failure | yes (as a control) |

`n/a` is recorded with its reason, never as zero or blank. Whether an injection came after the
acceptance is read from its verified phase: for W5a the acceptance is in the table with no later
attempt; for W5b the `accepted` event precedes t_inj.

## 6. Checks

### 6.1 Validity

Validity decides what counts, like the acceptance criteria of the earlier experiments: each
injection landed in its phase, and planned injections were made or recorded as not run; one code
identity across the batch (2.3); input checksums unchanged; the clock checks passed (4.1); the three
fingerprints equal (4.5); the machine-state rules held (8.3). A batch that fails validity does not
count toward the answers, but its records and outcomes stay visible (section 9).

### 6.2 Database acceptance correctness (answers E1)

From the job tables and run folders only: (1) Q1 gives `n_accepted` 1 for each succeeded job and 0
otherwise, with verdict `ok`; (2) `status --check` exits 0 and the export's
`invariant_violations.json` is empty; (3) the accepted attempt's `result_digest` equals
`runs.folder_digest` of its run folder, recomputed after the batch; (4) the accepted run passes the
result rule again from its files and equals the reference run by content (`compare_tables` on
`TABLE_KEYS`, as `check()` does). These are required of accepted attempts only: a crashed attempt
needs no `attempt.json`, `manifest.json`, `run.json` or `verify.json`; its folder stays unreferenced,
and `cleanup` (a dry run) lists it.

### 6.3 Timeliness and lost jobs (answers E2)

Q2's class and `deadline_met` for every job (4.2): `late` is a miss although the job succeeded,
`deadline not observed` is unknown, and `unfinished` and `missing` are E2's lost jobs.

### 6.4 Event-log completeness and report identity

The `accepted` events are the workers' reports; the table, not the log, decides acceptance. A
missing event for an accepted attempt is a log gap (expected in W5a), never a lost result; repeated
reports of one attempt are one result reported more than once. Each report must carry the full
identity of an accepted attempt of this batch: `store_id`, `job_id`, `attempt_number`, the
`worker_id` that claimed the attempt and its `result_digest`; the collector also checks the report's
`pid` against the `claimed` event of the same attempt. A report contradicting the table does not
change E1's answer (6.2) but is reported next to it.

### 6.5 Other outcome checks

- **No overlapping Spark steps.** Every started step and every reference run needs a complete
  interval, start to tree end, in its launcher record; a missing or incomplete one makes the verdict
  `unknown`, never `no overlap`. Intervals are compared in monotonic time: the launcher records
  `step_started_mono` and `tree_ended_mono`. A record without them, such as one written at
  `6d8a232`, which recorded UTC times only, leaves its interval missing; UTC times are never
  compared.
- **Nothing left.** After quiescence no attempt's process and no new Spark scratch remain (as
  `check()`).

## 7. SQL cross-check

The queries run in MySQL in the final snapshot (4.5), with the harness's records in TEMPORARY tables
of their own session ("section 7's TEMPORARY tables" in the fixture's comments; their definitions
are in section 2 of [recovery-sql.md](recovery-sql.md)).

| Query | Reads | Checks | Used in |
|---|---|---|---|
| Q0 | `jobs`, `job_attempts` | the snapshot fingerprint | 4.5 |
| Q1 | `jobs`, `job_attempts` | accepted results and claims per job; one verdict per job | 6.2 |
| Q2 | `batch_jobs`, `deadline_observations`, `jobs` | each submitted job's deadline class and `deadline_met` | 4.2, 6.3 |
| Q2b | `jobs`, `batch_jobs` | jobs in the table that the harness did not record | 6.3 |
| Q3a | `worker_accepts`, `job_store`, `jobs`, `job_attempts` | event-log completeness per succeeded job | 6.4 |
| Q3b | `worker_accepts`, `job_store`, `job_attempts` | the identity of each report | 6.4 |

Q1 deliberately overlaps the store's seven `INVARIANT_QUERIES`: a second reading of the same rows by
queries the store does not run. On 2026-10-23 the queries and a fixture of 21 job ids ran once in a
throwaway MySQL 8.4.13, and all 82 expected rows, written before the run, matched
([recovery-sql.md](recovery-sql.md), section 6). That validates the queries against their rules on
made-up rows; it says nothing about the job system.

## 8. Part A decisions: proposals

_Claude Code's proposals, with reasons. None is decided, and Part A is not approved._ They rest on
M2's final report (`6d8a232`):

| Input from M2 | Value |
|---|---|
| steps, calendar-year job | windows 2.5–3.0 s, spark_pipeline 22.1–22.6 s, verify 9.5 s; about 34–35 s in all |
| steps, stride-21 job | 1.5 s, 44.8–50.4 s, 11.0–11.5 s; about 57–63 s in all |
| step trees' peak RSS | spark_pipeline 0.66–0.79 GiB (calendar-year), 1.19–1.36 GiB (stride 21); verify 0.45–0.58 GiB; windows 0.12 GiB |
| job processes' RSS | worker 63.0 MiB, reconciler 51.6 MiB |
| container peaks | MySQL 345 MiB (67%) after the live job suites and 501 MiB (98%) after the live mutation session; Kafka 361–415 MiB (56–65%); informational, since another project's four containers shared Docker's VM and the host had about 1.3 GiB available |
| MySQL stalls, M2's clock | 0, 1 and 2 failed renewals for `LOCK TABLES`, `pause` and `restart`; each run kept its first attempt; no outage duration reported |
| acceptance runs | 10 of 10 passed on M2's clock in 11 min 20 s; the first run's failures were faults of the test harness |
| isolated memory-budget check | not done: pending |

### 8.1 Repetitions and workload

- **Proposal (P1), the preferred draft since 2026-10-24.** Every case on the calendar-year job; one
  batch on fresh containers with 2 jobs of each of the 14 cases (C0 included), 28 in all, in one
  shuffled order drawn from a seed recorded before the batch. It is the harness's default plan.
- **Alternative: the first P1.** 3 jobs of each case per batch, 42 in all, and 2 batches, each on
  fresh containers: 84 jobs.
- **Reasons.** The calendar-year job is the shortest (steps about 35 s against 63 s for stride 21),
  and its 22 s `spark_pipeline` step is still long enough to aim the mid-step injections; the
  stride-21 job adds run time without a recovery path of its own. The preferred draft keeps every
  case, so every failure mode and recovery path, and E1's checks on every job, in about a third of
  the alternative's time. It gives up the second batch on fresh containers, which would show whether
  results repeat across containers, and four of every six repetitions: one missed injection leaves a
  case with one made injection. Both keep each batch short of the ~50 runs after which M2 saw MySQL
  at 98% (another workload, so only a rough guide). A recorded shuffle spreads drift, such as memory
  growth, across cases instead of lining it up with one.
- **Duration** (estimates, provisional, and finalized only after the live preflight, 8.6).
  `python -m etf_risk.jobs.harness estimate` adds, per job, the design's upper bounds of 3.2 and
  these assumptions, none of them measured: T 40 s (M2's slowest steps, 35.1 s, plus 5 s of the
  worker's own work), 12 s to restart a killed worker and rebalance, 20 s for a service from start
  to ready, 2 s for the peaks after every job, 18 s for the group after a Kafka restart, and 3 minutes
  per batch for the containers, the reference run, the final snapshot and teardown. One job of each
  case takes 1,403 s (23.4 minutes), from 42 s (C0) to 159 s (W4, W7). The preferred batch of 28
  jobs: 2,986 s, about 50 minutes (52, 55 or 60 minutes if T is 45, 50 or 60 s). The alternative:
  4,389 s (73 minutes) per batch of 42, and 8,778 s (about 2 hours 26 minutes) for both; each extra
  5 s of T adds 8 minutes to the 84 jobs (T runs 16 times per 14 jobs). A longer restore lengthens K2
  and can move D1 and D2 onto their fenced paths. The figures come from the estimator's formulas,
  worked out by hand; tests/test_jobs_harness.py pins them and passed on 2026-10-24.
- **Counts, not rates.** The first review removed the pooled rule-of-three claim; reporting counts
  only is Claude Code's proposal. Results are given per case as k of n, with no rate, probability or
  confidence bound, pooled or per case: the injections are not shown to be independent, and cases are
  not alike.

### 8.2 Timing and deadlines

- **Proposal (P2), the clock and the limits.** The defaults of
  [timing.py](../src/etf_risk/jobs/timing.py) (lease 60 s, renewals every 10 s, fence margin 10 s,
  session timeout 15 s, heartbeats 3 s) and its step limits (windows 120 s, spark_pipeline 600 s,
  verify 300 s, attempt 900 s), with no `--timing` override.
- **Reasons.** E2 asks how long recovery takes, and the defaults are what the job processes run
  with; the token guards that decide E1 do not depend on the clock. The limits are about 40, 12 and
  26 times the measured step maxima (3.0, 50.4 and 11.5 s) and matter only to W7's lock wait and the
  classic-protocol bound; changing them would add a configuration M2 did not test. Cost: lease-based
  recoveries take 50–65 s instead of 20–29 s on M2's clock. Risk: the default clock has not run
  live, so the first batch is also its first live run.
- **Proposal (P3), the deadlines, reassessed on 2026-10-24.** Each case's D is the bound B from its
  reference to the start of its next run, plus twice the slowest step sum M2 measured for the
  parameter set (2S: 70.2 s calendar-year, 126.8 s stride 21), rounded up to 5 s; `max_lag_s` is 1 s,
  and the drain limit equals D. The reassessment changed three things:
  - W7's B is the later of the takeover (L + P, 65 s) and the end of the stopped tree (the stop plus
    two watchdog ticks and the kill grace: 98 s for a 90 s stop), no longer 65 s plus the stop;
  - K2, D1 and D2 count from their service's return (4.2), so B holds no outage of unknown length:
    for K2 the publication grace, a reconciler pass and the group's rejoin (30 + 5 + 19 = 54 s); for
    D1 and D2 a fenced attempt's lease and a pass (65 s);
  - the observation comes at completion when that is first (4.3), so meeting a deadline costs no
    waiting.

  | Cases | B | calendar-year D | stride-21 D |
  |---|---|---|---|
  | C0, W5a, W5b, K1, X1 | 0 | 75 s | 130 s |
  | W1 | 19 s | 90 s | 150 s |
  | W2, W3, W4, W6 | 65 s | 140 s | 195 s |
  | W7, with a 90 s stop | 98 s | 170 s | 225 s |
  | K2, from the broker's return | 54 s | 125 s | 185 s |
  | D1, D2, from MySQL's return | 65 s | 140 s | 195 s |

- **Reasons.** B is where the design puts the next run's start at the latest. S is the steps alone,
  not T: T adds the worker's own work (the claim, the input checksums, the manifest, renewals, three
  launcher starts), which nothing has measured, and 2S leaves about 35 s for it and for a slower run
  (M2's `spark_pipeline` varied by up to 5.6 s) while a stalled job still misses. The first batch's
  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next
  batch is an option for the author, recorded as a deviation. A local read of one row should take
  milliseconds, so a 1 s lag classifies nearly every success seen at the deadline and leaves the rest
  visible as `deadline not observed`. A drain limit of D gives a late job as long again to finish,
  enough to tell late from unfinished without one job holding the batch indefinitely. Whether D1 at
  this clock takes one claim or two stays open: M2 reported no outage duration, and failed-renewal
  counts do not establish one. The deadlines stay a draft until the live preflight (8.6): its C0 jobs
  measure T at the default clock, and its K2, D1 and D2 show the service-dependent paths.

### 8.3 Memory

- **Proposal (P4).** Fresh MySQL and Kafka containers for each batch; `services peaks` read after
  every job as well as before every injected restart (4.6); a batch flagged when either container's
  batch peak passes 90% of its limit, and stopped (no further jobs, then quiescence, 4.4) when either
  passes 95%; the host's available memory recorded before each job but not used as a gate.
- **Reasons.** Spec §11 asks for a fresh MySQL per batch; MySQL reached 98% in M2's mutation
  session, so a stop rule keeps a batch from reaching the limit unobserved, and a reading after every
  job lets it act in time. No measurement of the host's available memory with only this project's
  containers exists (M2's 1.3 GiB had another project's containers running), so a host gate would
  have no basis yet.
- **Pending.** The isolated memory-budget check. Until it is done, these limits are provisional and
  the budgets of spec §11 are not validated. The memory rules are finalized only after the live
  preflight (8.6), which reads both containers' peaks as a batch does.

### 8.4 Injection method

- **Proposal (P5), implemented and tested offline.** `etf_risk.jobs.faults`: a worker started with
  `ETF_RISK_FAULT_FILE` looks at that file at each fault point, and its `started` event names the
  file. The harness arms one fault for one job by writing the file atomically: a point, and an
  action (SIGKILL to the worker's own process, or a hold until a release file appears, for D2). The
  worker removes the file before it acts, so an arming fires once, and logs `fault_injected`, whose
  `mono` is the injection time. A new fault point, `after_accept_commit`, lies between
  `accept_result`'s return and the `accepted` event and is in `WORKER_FAULT_POINTS`. A file, rather
  than a fault named in the environment as first proposed, lets the harness arm the owner for one
  job without restarting it: a restart would rebalance the group and could move the partition (2.4).
- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside
  cannot hit reliably. `Worker(fault=...)` already calls the fault points, so the hook only wires
  them to the command, and the new point joins the offline tests that crash at every point. The code
  is new, written with Claude Code. Its offline tests passed on 2026-10-24: arming a running worker,
  and a hold released after F, which ends without an acceptance call (tests/test_jobs_worker.py), and
  the five kill hooks in the synthetic batch. Mutation checks for it are not written. Without it,
  these six cases would be recorded as not run.

### 8.5 Still open

The clock-check tolerance (4.1; the collector uses 1 s until it is decided); the harness's waits
(the phase delay before a mid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep
a service down: the settings hold 3 s, 90 s and 30 s for now); a host-memory gate, after the
isolated check; and the branches: the tooling and these documents are on `feature/recovery-harness`,
created from `e4adc38`, with a code checkpoint committed on 2026-10-24 and not pushed, while the
first copies of the documents, on `docs/recovery-outline`, stay as they were at revision 3.

### 8.6 The live preflight (proposal)

- **What.** One small batch against the services, before any formal batch, and only after the M2
  session releases the window: the reference run through the launcher (2.2), then C0, W1, W6, W7,
  K1, K2, D1, D2 and a second C0, in that order, on the default clock (P2), with the provisional
  settings of P3 and P4 and the hooks of P5. Plan: `plan --purpose preflight --jobs
  C0,W1,W6,W7,K1,K2,D1,D2,C0`. Estimated at 1,068 s (about 18 minutes) under the assumptions of 8.1.
- **What it checks.** The default clock's first live run (P2's risk); the real reference run under
  the launcher; the partition's owner from assignment events with real Kafka, at startup, after W1's
  kill and after each restart (2.4); and the paths only the services can show: a stopped worker and a
  stopped tree (W6, W7), Kafka restarted and stopped (K1, K2), MySQL restarted during a step and at
  acceptance (D1, D2). The synthetic batch (section 9) covers none of these.
- **Kept apart.** The plan says `purpose: preflight`. The harness writes such a batch only into
  `data/outputs-recovery/preflight/<batch>/` and names its purpose in the batch's records; the
  collector heads its summary and `validity.json` with it. A preflight's outcomes are reported in
  full, failed ones included, and never pooled with or counted as formal results. A formal batch needs
  a formal plan, a folder `data/outputs-recovery/formal/<batch>/` and `--formal`, given only once the
  author has approved Part A.
- **What follows.** The deadlines (P3), the memory rules (P4) and the runtime estimates (8.1) are
  then revised from the preflight's records, as proposals for the author; the preflight decides
  nothing in this section by itself.
- **In the same window.** The job tests against both services (README), which include the new
  worker tests on MySQL and the assignment events with real Kafka, and the live pipeline tests whose
  overlap check now compares monotonic times (`tests/test_jobs_live_pipeline.py`); each run once, its
  output kept with the preflight's records and labelled as a preflight run.

## 9. Records, prerequisites and authorship

- **Records**, under `data/outputs-recovery/<batch>/`, outside Git: the export, the event logs, the
  harness's logs (injections with intended and verified phases, deadlines and observations, process
  starts and clock checks, partition owners), `services peaks` by segment, the three fingerprints,
  Q0–Q3b as CSV, the table of section 5 with one row per injection, the per-case tally, and
  `cleanup`'s listing.
- **Nothing is dropped.** Every injection (misses, those not run, and those whose harness record is
  incomplete, counted apart as unrecorded, included), every batch (invalid ones included) and every
  verdict (failed outcomes and unknowns included) stays in the records; the tally lists all 14 cases
  and every verdict value, with zeros.
- **Tooling**, on `feature/recovery-harness` (a code checkpoint committed on 2026-10-24, not
  pushed), written with Claude Code at the author's decision of 2026-10-24:
  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs
    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)
    byte for byte (a test checks it);
  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);
  - assignment events in `kafka.py` (2.4);
  - code identity at launch, in `provenance.py`, `cli.py` and `pipeline.py` (2.3);
  - the fault hook, `faults.py`, wired in `cli.py`, and the fault point `after_accept_commit` in
    `worker.py` (8.4);
  - each step's interval on the monotonic clock in the launcher's record, `step_started_mono` and
    `tree_ended_mono` (4.1, 6.5);
  - in `worker.py`, no acceptance call, first or retried, starts at or after F, as
    [worker-pipeline.md](worker-pipeline.md) states; one already under way may commit after F, and
    the token guards it. Before 2026-10-24 the first call was made without that check, and a retry
    could start up to 1 s after F (D2's path in 3.1);
  - in `harness.py`, a plan's purpose (preflight or formal), a listed order for a preflight, and the
    guards that keep a preflight's records in their own folder and a formal batch behind `--formal`
    (8.6); in the collector, the purpose at the head of every summary;
  - in `tests/mutation_check.py`, focused mutations of all of the above, each run against the test
    file that should catch it.
- **Tests, offline only, run on 2026-10-24.** The full suite without the services, last run before
  the checkpoint commit: 615 passed and 30 skipped, none failed; the skipped ones are the MySQL,
  Kafka and live-pipeline tests, which need the services. Among them: the frozen queries on SQLite
  against all 82 expected rows of [recovery-sql.md](recovery-sql.md) (`tests/test_recovery_sql.py`;
  the translation drops MySQL's collation clauses and `CAST(... AS BINARY)`, so the MySQL run stays
  the evidence for MySQL); and one synthetic batch, end to end (`tests/test_recovery_synthetic.py`):
  the harness's own run on SQLite, with workers and a reconciler in its process, a one-partition
  stand-in for the Kafka group and stand-ins for the Spark steps and their launchers, read by the
  collector. It covers C0, W1, W2, W3, W4 (completing
  late on purpose), W5a, W5b and X1, and one failed deadline observation; W6, W7, K1, K2, D1 and D2
  need the services. Writing it found that the harness matched `step_ended` by a `step` field, which
  that event does not have (it names its step `name`), so a mid-step phase check would never have
  seen the step end; fixed and tested.
- **Mutation checks, 2026-10-24.** The 27 focused mutations of `tests/mutation_check.py`, each run
  against the one test file that should catch it, after those files passed unmutated: 27 caught,
  none survived, no error. The 49 earlier mutations of the job queue were not run again.
- **Not done:** the MySQL and Kafka variants of the tests, the live preflight (8.6), and any formal
  batch.
- **Authorship.** Spec §11: the job code is written with Claude Code. At the author's decision of
  2026-10-24, Claude Code also writes the recovery experiments' tooling listed above, and each new
  module says so. The items in 1.1, and the experiments' decisions, runs and answers, are the
  author's; everything else here is Claude Code's proposal. The queries of
  [recovery-sql.md](recovery-sql.md) stay marked as drafted with Claude Code.

## 10. Not claimed

Times hold for this machine, the clock of 8.2, and one broker and one database (spec §11). Results
are counts per case, not rates. The bounds in 3.2 hold only under their Kafka conditions and are not
predictions until approved. Cases without an injection method are not measured. The memory budgets
are not validated until the isolated check is done. The fixture run tests the SQL on made-up rows,
not the job system.

## History

- **Draft, 2026-10-23.** Outline drafted with Claude Code at the author's request.
- **Revision 1, 2026-10-23.** The first review (1.1): deadlines and their observation, quiescence
  and the final snapshot; database correctness apart from the event log, with full report identity
  and the new case W5a; code identity at launch and unknown intervals; monotonic durations and `n/a`
  latencies; Kafka conditions, startup order and restart rule; reference runs under the host lock;
  the rule-of-three sentence removed; all cases kept; a first fixture.
- **Revision 2, 2026-10-23.** The second review: `6d8a232` and M2's report as inputs, with the
  isolated memory-budget check pending; peaks by segment; the owner from assignment events only;
  `deadline not observed` as an explicit unknown with `deadline_met`; fixture B and explicit expected
  rows for every query.
- **Revision 3, 2026-10-23.** The third review: the queries validated once against a scratch MySQL
  after the M2 session's handover, with all 82 frozen expected rows matching; the restart duration
  inferred from failed renewals removed; the SQL, fixture, expected rows and run moved to
  [recovery-sql.md](recovery-sql.md) with no SQL changed; the outline shortened; Part A decisions
  proposed in section 8 (P1–P5), Q-A becoming P5.
- **Revision 4, 2026-10-24.** The fourth review: the fixture run accepted as tooling evidence only;
  the tooling written with Claude Code (section 9), none of it run; P3's deadlines reassessed (W7's
  bound, K2, D1 and D2 counted from their service's return, the observation at completion when that
  is first) and the duration of the 84 jobs estimated (8.1); P5 implemented with a fault file
  instead of a fault named in the environment. Timing, repetitions and memory thresholds stay
  provisional.
- **Revision 4, tests, 2026-10-24.** The offline tests run in an exclusive window the author gave;
  the acceptance deadline enforced before the first acceptance call, as the approved policy states;
  monotonic step times in the launcher records, which the overlap check now compares; the frozen
  queries checked on SQLite against the 82 expected rows; a synthetic batch run end to end without
  services; a harness bug in the mid-step phase check fixed. The proposals P1–P5 are unchanged;
  section 8 changed only where it said that tests had not run, and in 8.5's open items.
- **Revision 5, 2026-10-24.** The sixth review (1.1): the policy stated as "no acceptance call
  starts after F", with the token guards as the correctness mechanism and a retry no longer starting
  after F; the live overlap test on monotonic times; focused mutation checks; P1's 28 jobs as the
  preferred draft, with the 84 jobs as the alternative; the live preflight proposed (8.6), with the
  harness keeping its records apart; deadlines, memory rules and runtime estimates left to be
  finalized after it; a code checkpoint committed. Part A is not approved.
