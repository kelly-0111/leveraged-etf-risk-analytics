# Recovery experiments: Part B, the formal batches

_Drafted with Claude Code (Opus 5.5) on 2026-10-25 at the author's request. Its sources are the
records in `data/outputs-recovery/formal/` (numbers and tables read by script) and the author's
decisions of 2026-10-25 (section 1). Sections 2–6 give facts. The answers in section 7 were
drafted with Claude Code and approved by the author, unchanged, on 2026-10-25. Part A is
[recovery-part-a.md](recovery-part-a.md), approved on 2026-10-25 (`1c11577`). The records stay
outside Git and have not been changed since the collector wrote them; later notes sit beside them
as separate files. Times are local (UTC−5) on 2026-10-25._

> **Correction, 2026-10-26.** The bytes this document called "swapped in" and "swapped out"
> are psutil's `sin` and `sout`. On macOS they are page-ins and page-outs, not swap traffic
> ([host-counters-correction.md](host-counters-correction.md)). At the author's instruction:
> - sections 5.2 and 6 now say "paged in" and "paged out", with the figures unchanged;
> - "heavy swapping" (section 5.2) and "swapping heavily" (section 7.3, an answer approved on
>   2026-10-25) are replaced by the swap in use the records show, because the recorded counters
>   do not measure swap traffic.
>
> Swap in use is recorded correctly, and its figures are kept. No verdict changes: nothing gated
> on these counters.

> **Addition, 2026-10-27: formal batch-3 (section 10).** Part A's section 13 allowed one more
> formal batch, batch-3, beyond row 11's one rerun. Section 10 reports it. It was drafted with
> Claude Code, and its answers and limits were approved by the author, unchanged, on 2026-10-27.
> Sections 1–9 are unchanged.
> Where they say that there are no valid formal recovery times (5.1, 7.2, 7.3), they describe
> batch-1 and batch-2, which stay invalid for recovery times.

## 1. The author's decisions (2026-10-25)

- Part A was approved with all 13 decisions of its section 10, seed 544 included. Its row 11: a
  formal batch that is invalid or stops early is kept and reported in full, with one rerun of the
  same plan.
- batch-1 was stopped by a restart of the host. batch-2 is the one rerun.
- **batch-2: correctness observations valid; recovery times invalid** under the approved
  batch-level protocol (Part A, section 12, condition 4), because the exclusive window was broken
  when another project's container started at 06:25:08.
- Positions 1–17 of batch-2, which ran before that container started, are not a valid formal
  sub-batch. They are reported only as supplementary observations (5.2), with the limitation
  stated.
- No further formal batch for now.

## 2. The two batches side by side

Three sources of verdicts are kept apart here and throughout:
- **the collector's verdicts as recorded:** written by the collector at `fcaa645` into each batch's
  `validity.json` when the batch was collected;
- **the author's decision:** recorded on 2026-10-25, in section 1 and in `batch-2.decision.txt`;
- **later collector results:** computed in memory with the collector at `5ecde71` (section 8) and
  never written to the records.

| | batch-1 | batch-2 |
|---|---|---|
| Plan | `plan-544.json`: seed 544, 30 jobs (C0, 28 shuffled, C0) | the same plan |
| Code | HEAD `1c11577`, clean; the code of `fcaa645` | the same |
| Ran | 00:15:09 to 00:39:54, then the host restarted | 05:55:28 to 06:45:37 |
| Harness exit | none: the shell ended with the host | 0 |
| Jobs | 19 done, 1 stopped by the restart, 10 never started | 30 of 30 done |
| Made, missed, not run, unrecorded (collector) | 20, 0, 0, 10 | 30, 0, 0, 0 |
| Final snapshot | none | `status --check` exit 0; fingerprints agree (30 jobs, 40 attempts) |
| Collector verdicts as recorded (`fcaa645`) | correctness invalid (`fingerprints_agree`); recovery times invalid (also the clock check, the lid closed at 2 readings, power unknown); exit 1 | both valid; exit 0 |
| The author's decision, as recorded | none recorded; the collector's verdicts apply | correctness valid; recovery times **invalid**: the exclusive window was broken |
| Later collector results (`5ecde71`; computed, not written) | as recorded, plus `other_containers` unknown: no count was recorded | correctness valid; recovery times invalid, because `other_containers` is unknown: no count was recorded. Insufficient evidence, not a further violation |

## 3. What happened

### 3.1 batch-1: the lid closed, then the host restarted

- Positions 1–19 finished, and all succeeded. Position 20, the third C0 control, was claimed by
  worker A at 00:39:54.
- **The lid was closed during positions 16–18.**
  - The power log records a clamshell sleep entered as a dark wake at 00:35:46, and a full wake on
    user activity at 00:38:34.
  - The host readings before positions 17 (00:36:37) and 18 (00:38:22) recorded the lid closed;
    the reading before position 19 (00:39:03) recorded it open.
  - No wall-minus-monotonic jump over 1 s appears between the harness's events, so the processes
    kept running. The batch ran under `caffeinate -dims` on AC power.
- **An orderly shutdown followed at about 00:40.** `last` records a shutdown at 00:40, a
  shutdown-stall report is dated 00:40:15, and the host booted at 00:40:38; no software update
  was installed. The shutdown ended job 20's attempt (its recorded error: "spark_pipeline: the
  worker was stopped") and the harness, before its final snapshot. What initiated the shutdown is
  not recorded.
- After the boot, Docker was not running and both containers had exited. MySQL was started again
  on batch-1's own volume for an export (`batch-1.after-restart/`, 4.2); then `docker compose down
  -v` removed the containers, the network and the four anonymous volumes.

### 3.2 batch-2: another project's container

- All 30 jobs ran. Quiescence left no process and no other database connection; the final
  snapshot and the removal of the services followed.
- **Another project's container started at 06:25:08** (created then; restart policy "no") and ran
  through the last 20 minutes of the batch; it used about 605 MiB at 06:49.
  - Positions 1–17 ran before it. Job 17 was accepted at 06:25:07.84, 0.21 s before the
    container started; the harness logged its end 0.18 s after. Positions 18–30 ran while it ran.
  - The harness counted other containers only at the start, where it counted 0, so batch-2's
    records do not show the container. The evidence is `batch-2.other-container.txt`, written at
    06:49 from Docker's own record of the container, which this session did not touch.
- The power log has no sleep, wake or clamshell line between 05:55 and 06:46.

## 4. Correctness (E1)

### 4.1 batch-2: correctness observations (valid)

The checks behind this verdict do not involve time, so the other container does not bear on them.

- **One accepted result per job:** Q1 `ok` for all 30 jobs, each with exactly one accepted result.
- **Results equal to the reference run:** all 30 accepted attempts pass the collector's checks: the
  folder's digest equals the accepted digest, the run's checks and verify output are clean, and
  every table matches the reference run by content.
- **Executions:** 10 jobs were claimed twice (W2, W3, W4, W6 and W7, two of each), and 8 of them
  executed twice. Both W4 jobs completed two executions and had one accepted. `cleanup.txt` lists
  8 unaccepted attempts' folders (16.6 MiB).
- **No overlapping step intervals:** every step has both monotonic times.
- **The job table:** `status --check` exit 0, with no invariant violation. The three fingerprints
  agree (30 jobs, version sum 398, 40 attempts, 278 renewals).
- **Q2b and Q3:** no Q2b rows (no job in the table that the harness did not record) and no Q3b
  mismatch. Q3a is "reported once" for 28 jobs and "no matching report" for the 2 W5a jobs, killed
  between the acceptance commit and its event, as designed.
- **Liveness:** 56 retried `accept_result` calls, 28 for each D2 job during its MySQL outage, and
  26 failed reconciler passes during the MySQL outages of D1 and D2; no `failed_after_ack`, no
  `consumer_error`, no serve restart.
- **Left behind:** the only new scratch entry is the JVM's perf-data folder (`hsperfdata`), absent
  at the batch's start and present, empty, after it.

| Position | Case | Claims | Accepted | Executions (complete) | Q1 | Q3a | Accepted result against the reference |
|---:|---|---:|---:|---|---|---|---|
| 1 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 2 | W5a | 1 | 1 | 1 (1) | `ok` | no matching report | matches, all checks clean |
| 3 | W2 | 2 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 4 | W7 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| 5 | W3 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| 6 | W5a | 1 | 1 | 1 (1) | `ok` | no matching report | matches, all checks clean |
| 7 | D1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 8 | D1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 9 | W5b | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 10 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 11 | K2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 12 | X1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 13 | W2 | 2 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 14 | W3 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| 15 | K1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 16 | W6 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| 17 | W6 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| 18 | X1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 19 | W5b | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 20 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 21 | W1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 22 | D2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 23 | W7 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| 24 | K1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 25 | W4 | 2 | 1 | 2 (2) | `ok` | reported once | matches, all checks clean |
| 26 | W1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 27 | W4 | 2 | 1 | 2 (2) | `ok` | reported once | matches, all checks clean |
| 28 | D2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 29 | K2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| 30 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |

### 4.2 batch-1: no valid correctness verdict

- The collector found `fingerprints_agree` failed: the final snapshot never ran. There is no Q1 row
  for any submitted job, so every Q1 verdict is unknown.
- **Supplementary, taken after the restart and not by the harness** (`batch-1.after-restart/`):
  MySQL recovered on start, then `status --check` (exit 0, all invariants hold) and an export.
  - 19 jobs succeeded with exactly one accepted attempt each, 7 of them after an expired first
    attempt.
  - Job 20 is queued, its one attempt failed ("spark_pipeline: the worker was stopped").

  These are not correctness observations under the protocol, since the batch's correctness verdict
  is invalid; they are reported as found.

| Position | Case | Harness record | Job after the restart | Attempts (outcome) | Accepted |
|---:|---|---|---|---|---:|
| 1 | C0 | job done | succeeded | 1: accepted | 1 |
| 2 | W5a | job done | succeeded | 1: accepted | 1 |
| 3 | W2 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 4 | W7 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 5 | W3 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 6 | W5a | job done | succeeded | 1: accepted | 1 |
| 7 | D1 | job done | succeeded | 1: accepted | 1 |
| 8 | D1 | job done | succeeded | 1: accepted | 1 |
| 9 | W5b | job done | succeeded | 1: accepted | 1 |
| 10 | C0 | job done | succeeded | 1: accepted | 1 |
| 11 | K2 | job done | succeeded | 1: accepted | 1 |
| 12 | X1 | job done | succeeded | 1: accepted | 1 |
| 13 | W2 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 14 | W3 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 15 | K1 | job done | succeeded | 1: accepted | 1 |
| 16 | W6 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 17 | W6 | job done | succeeded | 1: expired, 2: accepted | 1 |
| 18 | X1 | job done | succeeded | 1: accepted | 1 |
| 19 | W5b | job done | succeeded | 1: accepted | 1 |
| 20 | C0 | started; stopped by the restart | queued | 1: failed | 0 |
| 21 | W1 | none: never started | — | — | — |
| 22 | D2 | none: never started | — | — | — |
| 23 | W7 | none: never started | — | — | — |
| 24 | K1 | none: never started | — | — | — |
| 25 | W4 | none: never started | — | — | — |
| 26 | W1 | none: never started | — | — | — |
| 27 | W4 | none: never started | — | — | — |
| 28 | D2 | none: never started | — | — | — |
| 29 | K2 | none: never started | — | — | — |
| 30 | C0 | none: never started | — | — | — |

## 5. Recovery times (E2)

### 5.1 No valid formal recovery times

batch-1 is invalid for recovery times by the collector's checks, and batch-2 by the author's
decision. This part therefore reports no formal recovery times.

### 5.2 Supplementary observations: batch-2, positions 1–17

**Limitation.** These are not formal results and not a sub-batch. They were selected after the
batch, by the time another project's container started, and the batch they belong to is invalid
for recovery times. The other recorded conditions held for them: AC power and the lid open at their
readings, no sleep, the clock check. They were taken under memory pressure (level 2 at 16 of their
17 readings), with 3.86–8.25 GiB of swap in use at those readings, on this host only. They are counts per job, with no rate and no
performance claim. Every outcome in the range is kept, the two late jobs included.

Detection, re-run and finish times are the collector's, as section 5 of the outline defines them:
from the injection, or from the submit for C0. D and the deadline column count from each case's
deadline reference (Part A, section 3). For W2–W7 that reference is the injection, and for C0 the
submit. For D1 and K2, the injection is the service's stop, while the reference is the service's
return, 35.3–35.8 s after the stop. Measured from the return, the D1 jobs finished in 21.7 and
14.9 s and the K2 job in 68.4 s.

| Position | Case | Claims | Detection (s) | Re-run (s) | Finish (s) | D (s) | Deadline | Pressure | Available (GiB) | Paged out during (MiB) |
|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| 1 | C0 | 1 | n/a: no failure | n/a: no failure | 84.7 | 75 | late | 2 | 1.42 | 83 |
| 2 | W5a | 1 | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance | 75 | on time | 2 | 1.48 | 9 |
| 3 | W2 | 2 | 63.7 | 63.7 | 121.0 | 140 | on time | 2 | 1.41 | 38 |
| 4 | W7 | 2 | 60.5 | 60.5 | 165.2 | 170 | on time | 2 | 1.33 | 59 |
| 5 | W3 | 2 | 57.9 | 57.9 | 136.9 | 140 | on time | 2 | 1.25 | 55 |
| 6 | W5a | 1 | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance | 75 | on time | 2 | 1.34 | 20 |
| 7 | D1 | 1 | 3.6 | n/a: the attempt went on | 57.5 | 140 | on time | 2 | 1.21 | 44 |
| 8 | D1 | 1 | 5.9 | n/a: the attempt went on | 50.4 | 140 | on time | 2 | 1.44 | 47 |
| 9 | W5b | 1 | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance | 75 | on time | 2 | 1.49 | 45 |
| 10 | C0 | 1 | n/a: no failure | n/a: no failure | 43.2 | 75 | on time | 2 | 1.49 | 4 |
| 11 | K2 | 1 | 35.8 | 50.5 | 103.7 | 125 | on time | 2 | 1.51 | 26 |
| 12 | X1 | 1 | n/a: no failure | n/a: no failure | 61.1 | 75 | on time | 2 | 1.24 | 16 |
| 13 | W2 | 2 | 63.3 | 63.3 | 100.4 | 140 | on time | 2 | 1.69 | 30 |
| 14 | W3 | 2 | 57.4 | 57.4 | 104.1 | 140 | on time | 2 | 1.66 | 30 |
| 15 | K1 | 1 | n/a for the job: the attempt goes on | n/a: the attempt goes on | 47.5 | 75 | on time | 2 | 1.63 | 20 |
| 16 | W6 | 2 | 58.1 | 58.1 | 182.6 | 140 | late | 2 | 1.53 | 132 |
| 17 | W6 | 2 | 58.8 | 58.8 | 101.6 | 140 | on time | 1 | 2.04 | 98 |

- **2 of the 17 jobs were late,** both before the other container started:
  - position 1 (C0, the batch's first job), 84.7 s against 75 s, with 83 MiB paged out during it;
  - position 16 (W6), 182.6 s against 140 s, with 132 MiB paged out during it.
- **The controls in this range** (positions 1 and 10) took 84.7 and 43.2 s.
- **Cases missing:** W1, W4 and D2 ran only at positions 18–30, so there is no supplementary
  observation of their times.

### 5.3 Positions 18–30

Their times and deadline outcomes stay in batch-2's records (`injections.csv`) and are not reported
here, because they ran while another project's container ran. Their correctness outcomes are in
4.1.

## 6. Host conditions

| | batch-1 | batch-2 |
|---|---|---|
| Readings | 21: the start and 20 jobs; no end reading | 32: the start, 30 jobs and the end |
| Power | AC at all 21 | AC at all 32 |
| Lid | closed at the readings before positions 17 and 18 | open at all 32 |
| Sleep (power log) | a clamshell dark wake from 00:35:46 to a full wake at 00:38:34; no clock jump between the harness's events | none |
| Clock check | failed: no `batch_ended` event | passed: wall minus monotonic −0.009 s, 19 of 19 processes on one clock |
| Memory pressure | level 2 at all 21 | level 2 at 31 of 32; 1 before position 17 |
| Available before each job | 1.45–1.83 GiB | 1.21–2.04 GiB |
| Swap and paging over the batch | not computable: no end reading | swap in use +2.67 GiB; 1.35 GiB paged out, 47.9 GiB paged in |
| Container peaks | MySQL 317 of 512 MiB (62%); Kafka 506 of 640 MiB (79%) | MySQL 269 of 512 MiB (53%); Kafka 505 of 640 MiB (79%) |
| Other containers | 0 at the start; no later count | 0 at the start; one from 06:25:08, outside the records (3.2) |

## 7. Answers and limits

_The questions are those of spec §11. Under each, the facts are drafted with Claude Code from
sections 4–6. The answers were drafted with Claude Code and approved by the author, unchanged, on
2026-10-25._

### 7.1 E1

> Does each job accept at most one result, and does every successfully completed job have exactly
> one, even when jobs execute more than once?

_Drafted facts:_ in batch-2, whose correctness verdict is valid, all 30 jobs succeeded with exactly
one accepted result, which matched the reference run. 8 of them executed twice, and 2 of those
(the W4 jobs) completed two executions. batch-1 gives no valid correctness verdict (4.2).

**Answer (drafted with Claude Code; approved by the author on 2026-10-25).** In batch-2, whose
correctness verdict is valid, every job accepted exactly one result: all 30 jobs succeeded with one
accepted attempt each, and every accepted result matched the reference run. This held for the 10
jobs claimed twice and the 8 executed twice, including the 2 W4 jobs that completed two executions
and had only one accepted. No job had more than one accepted result. batch-1 gives no valid
correctness verdict, because its final snapshot never ran. Its job table, exported after the
restart, shows one accepted attempt for each of its 19 succeeded jobs, but that is supplementary
evidence. These are counts from one batch of 30 jobs on one host, not a rate.

### 7.2 E2

> After a worker crash (before or after its claim), a broker restart or a database restart, how
> long until the job runs again and finishes, and is any job lost or accepted twice?

_Drafted facts:_ there are no valid formal recovery times (5.1). The supplementary observations of
positions 1–17 (5.2) cover 11 of the 14 cases, with the limitation stated there. No job of batch-2
was lost or accepted twice: 30 of 30 succeeded with one accepted result each.

**Answer (drafted with Claude Code; approved by the author on 2026-10-25).** No formal recovery
times are reported. batch-1 stopped when the host restarted, and batch-2's recovery times are
invalid under the approved batch-level protocol, because another project's container broke the
exclusive window from position 18 on. Positions 1–17 of batch-2 are supplementary observations
only: not a formal sub-batch, and taken under memory pressure on this host. They show the
following.
- After a worker was killed or stopped (W2, W3, W6, W7), the job ran again 57.4–63.7 s after the
  injection and finished 100.4–182.6 s after it.
- A Kafka restart (K1) did not interrupt the attempt; the job finished 47.5 s after the restart
  began.
- With Kafka stopped around the submit (K2), the job first ran 50.5 s after the stop and finished
  68.4 s after Kafka's return.
- After MySQL restarts (D1), the attempts went on and finished 21.7 and 14.9 s after MySQL's
  return.
- Kills after the acceptance (W5a, W5b) left each job succeeded with its one accepted result.

15 of the 17 met their deadlines. The two late jobs, the first control at 84.7 s and a W6 at
182.6 s, both preceded the external container. W1, W4 and D2 have no supplementary times. No job in
batch-2 was lost or accepted twice: all 30 succeeded with exactly one accepted result.

### 7.3 Limits

- **One host:** an 8 GiB Mac under memory pressure, with 3.16–8.25 GiB of swap in use at the
  formal batches' readings (reworded on 2026-10-26; see the correction above). Two jobs per
  case, reported as counts with no rates.
- **No valid formal recovery times;** the supplementary observations miss W1, W4 and D2.
- **The exclusive window was counted only at the start in both batches.** Since `5ecde71` the count
  is recorded at every reading (section 8). It is still a sample: a container that starts and
  stops between two readings, within one job, is not seen.
- **Missing counts are insufficient evidence.** The later collector reports `other_containers` as
  unknown for every batch recorded before `5ecde71`, the preflights included. Condition 4 cannot be
  confirmed for them; that is not evidence that another container ran.
- **batch-1's export after the restart is supplementary,** taken after a crash recovery and not by
  the harness.

## 8. Tooling changes after the formal batches (`5ecde71`)

- **Containers at every reading:** the harness records, with every host reading (start, before
  each job, end), the running containers outside this project, or None when Docker cannot say.
  The collector's `other_containers` condition fails a reading with any such container. A missing
  count is unknown, which also fails the verdict, as insufficient evidence. It counts for recovery
  times only. The count is a sample at each reading, so a container that starts and stops between
  two readings is not seen.
- **The Q1 line:** the summary no longer reports "jobs whose Q1 verdict is not ok: none" when there
  are no Q1 rows; such jobs are unknown and listed apart (`q1_missing`).
- **Stale texts:** the harness's docstrings and the collector's `--clock-tolerance` help no longer
  describe Part A as unapproved or say that no batch has run.
- **Checks:**
  - 67 tests passed in the four recovery test files.
  - 19 of 19 host and collector mutations were caught, the 5 new ones included.
- **Later collector results on the formal records** (computed in memory, not written; the 2,359
  files were unchanged):
  - batch-1: verdicts as recorded, plus `other_containers` unknown at all 22 readings; its Q1 line
    now says that no Q1 rows exist.
  - batch-2: correctness valid. Recovery times invalid, because `other_containers` is unknown at
    all 32 readings: batch-2 recorded no count. That is insufficient evidence, not a further
    violation, and the records hold no trace of the 06:25:08 container. The recorded decision
    rests on that container (section 1).
- **The preflights:** under the later collector the correctness verdicts are unchanged. Every
  preflight's recovery times are invalid, preflight-4's only because `other_containers` is unknown
  at its 5 readings, which again is insufficient evidence.
- **Part A's approved sections are unchanged;** its section 13 records these changes.

## 9. Records

In `data/outputs-recovery/formal/`, outside Git:

- `plan-544.json`;
- `batch-1/`, the harness's records with the collector's outputs (`fcaa645`), and
  `batch-1.console.log`;
- `batch-1.after-restart/`, the export and `status --check` after the restart;
- `batch-1.interruption.txt`, the evidence of 3.1 (the power log's sleep and wake lines, `last`,
  the boot time);
- `batch-2/`, complete, with the collector's outputs (`fcaa645`), and `batch-2.console.log`;
- `batch-2.other-container.txt`, the evidence of 3.2;
- `batch-2.decision.txt`, the author's decision of section 1.

The live Kafka gate before the formal batches is
`data/outputs-recovery/preflight/kafka-live-fcaa645.txt` (27 passed, 0 failed, 0 skipped).

## 10. batch-3 (2026-10-27)

_Drafted with Claude Code (Opus 5.5) on 2026-10-27 at the author's request, from the records in
`data/outputs-recovery/formal/batch-3/` (numbers and tables read by script) and the session's
console and collection logs. Sections 10.1–10.6 give facts. The answers (10.7) and the limits
(10.8) were drafted with Claude Code and approved by the author, unchanged, on 2026-10-27, after
the author's review of this section. The approved answers of section 7, which rest on batch-1 and
batch-2, are unchanged. The protocol is Part A's, with the amendments of its section 13, the
batch-3 item included. Times are local (UTC−5) on 2026-10-27._

### 10.1 The three batches side by side

| | batch-1 | batch-2 | batch-3 |
|---|---|---|---|
| Allowed by | Part A, row 11 | row 11's one rerun | Part A, section 13: one more batch, decided on 2026-10-27 |
| Plan | `plan-544.json`: seed 544, 30 jobs | the same plan | the same plan; the session checked its SHA-256 |
| Code | HEAD `1c11577`, clean; the code of `fcaa645` | the same | HEAD `c5c340a`, clean; the code of `4fc550e` |
| Ran | 2026-10-25, 00:15:09 to 00:39:54, then the host restarted | 2026-10-25, 05:55:28 to 06:45:37 | 2026-10-27, 16:23:56 to 16:55:03 |
| Harness exit | none: the shell ended with the host | 0 | 0 |
| Made, missed, not run, unrecorded (collector) | 20, 0, 0, 10 | 30, 0, 0, 0 | 30, 0, 0, 0 |
| Final snapshot | none | `status --check` exit 0; fingerprints agree (30 jobs, 40 attempts) | `status --check` exit 0; fingerprints agree (30 jobs, version sum 296, 40 attempts, 176 renewals) |
| Collector verdicts as recorded | correctness invalid; recovery times invalid; exit 1 (`fcaa645`) | both valid; exit 0 (`fcaa645`) | both valid, every required check passed; exit 0 (`4fc550e`) |
| The author's decision, as recorded | none; the collector's verdicts apply | correctness valid; recovery times **invalid**: the exclusive window was broken | correctness valid; recovery times valid: this section's answers and limits, approved on 2026-10-27 |
| Other projects' containers | 0 at the start; no later count | 0 at the start; one from 06:25:08, outside the records | 0 at all 32 readings; 0 of the 5,481 container events of the whole batch |
| Sleep and wake (power log) | a clamshell dark wake from 00:35:46 | none | none: 0 Sleep, 0 Wake, 0 DarkWake entries; the log covers the batch |
| Clock check | failed: no `batch_ended` event | passed: −0.009 s, 19 of 19 processes on one clock | passed: +0.034 s, 19 of 19 processes on one clock |
| Frozen code checked after the batch | no such check then | no such check then | verified: all 21 code records match `4fc550e` and its `uv.lock`, with a clean worktree and seed 544 |

### 10.2 What happened

- **The session:** the author ran `docs/recovery-batch-3.zsh` from Terminal. Its preconditions held,
  both with `--check` beforehand and at the start of the run. The batch, the collection and the
  cleanup check followed: harness exit 0, collector exit 0, and no container of this project left.
  The author then ran `docs/verify_frozen_code.py`, which printed `FROZEN CODE: VERIFIED`.
- **One Kafka line in the console.** The first line of `batch-3.console.log`, which has no time, is
  a librdkafka message: a producer could not connect to `127.0.0.1:9094` ("Connection refused").
  - **From the code and records:** the console receives only the harness's own output. The
    workers, the reconciler and the reference run write to their own logs, and Docker's output is
    captured.
  - The line has the format of a Kafka client that was given a Python logger. In the harness, that
    is only the publisher it creates for X1's duplicates, first at position 12's claim. Its
    readiness checks use Kafka clients that log nothing.
  - **The outages:** after that publisher was created, Kafka was down three times. These were the
    K1 restarts at positions 15 and 24, 3.3 and 3.1 s from the restart's start to the harness's
    readiness reading, and the K2 stop at position 29, 31.9 s.
  - **Unknown:** the line has no time, so which outage it came from is not recorded.
  - All 4 of X1's duplicate publications were confirmed. No check bears on the line, and none
    failed.

### 10.3 Correctness (E1)

The batch's correctness verdict is valid by the collector's checks, as recorded.

- **One accepted result per job:** Q1 `ok` for all 30 jobs, each with exactly one accepted result.
- **Results equal to the reference run:** all 30 accepted attempts pass the collector's checks: the
  folder's digest equals the accepted digest, the run's checks and verify output are clean, and
  every table matches the reference run by content.
- **Executions:** 10 jobs were claimed twice (W2, W3, W4, W6 and W7, two of each), and 8 of them
  executed twice. Both W4 jobs completed two executions and had one accepted. `cleanup.txt` lists
  8 unaccepted attempts' folders (33.0 MiB).
- **No overlapping step intervals:** every step has both monotonic times.
- **The job table:** `status --check` exit 0, with no invariant violation. The three fingerprints
  agree (30 jobs, version sum 296, 40 attempts, 176 renewals).
- **Q2b and Q3:** no Q2b rows, and Q3b matches for all 28 reports. Q3a is "reported once" for 28
  jobs and "no matching report" for the 2 W5a jobs (positions 2 and 6).
- **Why the W5a reports are missing.** W5a kills the owner at `after_accept_commit`: after MySQL
  committed the acceptance, but before the worker wrote its `accepted` event. The job table
  therefore holds the accepted result, while the worker's log has no report of it.
  - Part A predicted exactly this ("Q3a `no matching report`, by design", section 4), and batch-2
    showed the same (4.1).
  - Both W5a jobs have Q1 `ok`, and their accepted results match the reference run.
  - W5b kills the owner after the event, so its report exists.
- **Liveness:** 55 retried `accept_result` calls, 28 and 27 for the two D2 jobs, and 24 failed
  reconciler passes. All of them fell within MySQL outages. There was no `failed_after_ack`, no
  `consumer_error` and no serve restart.
- **Left behind:** quiescence left no process, no other database connection and no new Spark
  scratch entry.

| Case | Positions | Claims | Accepted | Executions (complete) | Q1 | Q3a | Accepted result against the reference |
|---|---|---:|---:|---|---|---|---|
| C0 | 1, 10, 20, 30 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| W1 | 21, 26 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| W2 | 3, 13 | 2 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| W3 | 5, 14 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| W4 | 25, 27 | 2 | 1 | 2 (2) | `ok` | reported once | matches, all checks clean |
| W5a | 2, 6 | 1 | 1 | 1 (1) | `ok` | no matching report, by design | matches, all checks clean |
| W5b | 9, 19 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| W6 | 16, 17 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| W7 | 4, 23 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
| K1 | 15, 24 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| K2 | 11, 29 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| D1 | 7, 8 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| D2 | 22, 28 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
| X1 | 12, 18 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |

### 10.4 Recovery times (E2)

The batch's recovery-time verdict is valid by the collector's checks, as recorded. Every check
passed, including the whole-batch container check and the clock check.

**Timing origins.** Each time below counts from one of three origins, named in the column heads:
- **the submit:** when the harness submitted the job;
- **the injection:** when the harness made the fault. That is the kill or stop signal, the
  duplicate publication (X1), or the start of the service's stop (K2, D1, D2) or restart (K1);
- **the deadline's reference** (Part A, section 3): the submit for C0, the service's return for K2,
  D1 and D2, and the injection for every other case.

The service's return is the harness's own reading: the moment its readiness check first succeeds
after the service is started again. A worker can reconnect slightly before that reading, so a
finish can come out just below zero from it (position 28, −0.1 s). Detection and re-run count from
the injection, as the collector computes them; D, the slack and the deadline outcome count from
the reference. The slack is D minus the finish from the reference: how long before its deadline the
job's result was accepted. For K2, D1 and D2 the two origins differ by the outage: 31.8 and 31.9 s
for Kafka, and 31.2 s for MySQL. Every time is computed from unrounded monotonic times, so a
difference of two rounded entries can be 0.1 s off.

| Position | Case | Detection (s, from injection) | Re-run (s, from injection) | Finish from submit (s) | Finish from injection (s) | Deadline's reference | Finish from reference (s) | D (s) | Slack (s) | Deadline |
|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---|
| 1 | C0 | n/a: no failure | n/a: no failure | 23.0 | — | submit | 23.0 | 75 | 52.0 | on time |
| 2 | W5a | n/a: after acceptance | n/a: after acceptance | no `accepted` event, by design | n/a | injection | n/a | 75 | n/a | on time |
| 3 | W2 | 61.5 | 61.5 | 84.1 | 83.1 | injection | 83.1 | 140 | 56.9 | on time |
| 4 | W7 | 59.1 | 59.1 | 118.5 | 112.4 | injection | 112.4 | 170 | 57.6 | on time |
| 5 | W3 | 58.5 | 58.5 | 86.1 | 79.9 | injection | 79.9 | 140 | 60.1 | on time |
| 6 | W5a | n/a: after acceptance | n/a: after acceptance | no `accepted` event, by design | n/a | injection | n/a | 75 | n/a | on time |
| 7 | D1 | 6.3 | n/a: the attempt went on | 43.7 | 37.3 | MySQL's return, 31.2 s after the stop | 6.1 | 140 | 133.9 | on time |
| 8 | D1 | 6.3 | n/a: the attempt went on | 44.1 | 37.8 | MySQL's return, 31.2 s after the stop | 6.5 | 140 | 133.5 | on time |
| 9 | W5b | n/a: after acceptance | n/a: after acceptance | 22.0 | n/a: accepted before the kill | injection | n/a | 75 | n/a | on time |
| 10 | C0 | n/a: no failure | n/a: no failure | 22.5 | — | submit | 22.5 | 75 | 52.5 | on time |
| 11 | K2 | 36.0 | 46.9 | 67.7 | 68.6 | Kafka's return, 31.8 s after the stop | 36.7 | 125 | 88.3 | on time |
| 12 | X1 | n/a: no failure | n/a: no failure | 23.5 | 22.0 | injection | 22.0 | 75 | 53.0 | on time |
| 13 | W2 | 63.4 | 63.4 | 86.2 | 85.2 | injection | 85.2 | 140 | 54.8 | on time |
| 14 | W3 | 58.4 | 58.4 | 86.2 | 80.1 | injection | 80.1 | 140 | 59.9 | on time |
| 15 | K1 | n/a for the job: the attempt goes on | n/a: the attempt goes on | 23.5 | 17.2 | injection: the restart's start; Kafka ready 3.3 s later | 17.2 | 75 | 57.8 | on time |
| 16 | W6 | 60.4 | 60.4 | 89.5 | 82.9 | injection | 82.9 | 140 | 57.1 | on time |
| 17 | W6 | 59.3 | 59.3 | 87.8 | 81.7 | injection | 81.7 | 140 | 58.3 | on time |
| 18 | X1 | n/a: no failure | n/a: no failure | 23.0 | 22.0 | injection | 22.0 | 75 | 53.0 | on time |
| 19 | W5b | n/a: after acceptance | n/a: after acceptance | 22.5 | n/a: accepted before the kill | injection | n/a | 75 | n/a | on time |
| 20 | C0 | n/a: no failure | n/a: no failure | 22.9 | — | submit | 22.9 | 75 | 52.1 | on time |
| 21 | W1 | 14.9 | 14.9 | 37.2 | 36.2 | injection | 36.2 | 90 | 53.8 | on time |
| 22 | D2 | 3.1 | n/a: the attempt went on | 55.2 | 31.4 | MySQL's return, 31.2 s after the stop | 0.2 | 140 | 139.8 | on time |
| 23 | W7 | 59.2 | 59.2 | 118.5 | 112.5 | injection | 112.5 | 170 | 57.5 | on time |
| 24 | K1 | n/a for the job: the attempt goes on | n/a: the attempt goes on | 22.7 | 16.3 | injection: the restart's start; Kafka ready 3.1 s later | 16.3 | 75 | 58.7 | on time |
| 25 | W4 | 63.8 | 63.8 | 108.5 | 85.7 | injection | 85.7 | 140 | 54.3 | on time |
| 26 | W1 | 13.6 | 13.6 | 36.1 | 35.2 | injection | 35.2 | 90 | 54.8 | on time |
| 27 | W4 | 64.0 | 64.0 | 108.3 | 86.2 | injection | 86.2 | 140 | 53.8 | on time |
| 28 | D2 | 3.8 | n/a: the attempt went on | 53.9 | 31.0 | MySQL's return, 31.2 s after the stop | −0.1 | 140 | 140.1 | on time |
| 29 | K2 | 34.8 | 46.9 | 68.0 | 68.8 | Kafka's return, 31.9 s after the stop | 36.9 | 125 | 88.1 | on time |
| 30 | C0 | n/a: no failure | n/a: no failure | 23.1 | — | submit | 23.1 | 75 | 51.9 | on time |

- **30 of 30 jobs met their deadlines.** The smallest slack was 51.9 s (position 30, C0).
- **W5a and W5b** were killed after their acceptance, so they have no recovery time. Both jobs of
  each were already succeeded at their deadline. W5b's `accepted` event came before the kill
  (0.0 s), and W5a's never came (10.3).
- **Detection events,** as Part A section 4 names them:
  - the standby's `delivered` (W1);
  - the reconciler's `requeued` (W2, W3, W4, W6, W7);
  - the reconciler's `published` (K2), 4.1 and 2.9 s after Kafka's return;
  - `renewal_failed` (D1), during the outage;
  - a `retry` of `accept_result` (D2), during the outage.

  K2's first claim came 15.0 s after Kafka's return in both jobs.
- **D1 and D2 took the branch without fencing:** MySQL returned 31.2 s after the stop, before F
  (40–50 s after it), so each attempt went on with one claim.
- **After a recovery, the runs took about as long as a control:**
  - from the new claim to the acceptance: 21.3–22.5 s (W1, W2, W3, W4, W6);
  - W7's replacement waited for the stopped tree, which resumed 90.0 s after the stop; the
    acceptance came 22.4 s after that.

### 10.5 The deadline slack: larger than Part A expected

Part A's predictions assumed a run of T = 40 s and gave margins of 31–35 s (section 4). Part A's
section 3 added that, at the preflights' median control time of 49.6 s, those margins would shrink
to about 20–25 s. batch-3's slack, each from its deadline's reference, was larger in every case:

| Cases | Slack (s) | Mainly from |
|---|---|---|
| C0, X1 | 51.9–53.0 | the run: 22.5–23.1 s for the controls, against the 70.2 s (2S) of D |
| K1 | 57.8–58.7 | the run; the attempt went on through the restart |
| W1, W2, W3, W4, W6, W7 | 53.8–60.1 | the run, 21.3–22.5 s after the new claim; detection came within B (58.4–64.0 s against L + P = 65 s for W2–W6; 13.6–14.9 s against 19 s for W1) |
| K2 | 88.1–88.3 | B assumes the whole publication grace after Kafka's return (54 s); the first claim came 15.0 s after it |
| D1, D2 | 133.5–140.1 | B assumes a fenced attempt and a new run (65 s); MySQL returned before F, so no new run was needed |

- **The run:** D = ceil5(B + 2S) gives each run 70.2 s, twice M2's slowest step sum. The controls
  took 22.5–23.1 s from submit to acceptance (median 22.9 s). That is below the assumed T of 40 s,
  and below the preflights' 45.1–52.4 s on which Part A's section 3 judged the margins. Runs of
  about 22 s, after a recovery too (10.4), leave about 48 s of the 70.2 s unused. Rounding D up to
  a multiple of 5 adds up to 5 s more.
- **What may explain the shorter runs, without a measured cause:**
  - batch-3 ran at memory pressure level 1 at all 32 readings, with 2.65–3.25 GiB available;
  - the preflights ran under memory pressure (Part A, section 11), and batch-2 at level 2 at 31 of
    its 32 readings, with 1.21–2.04 GiB available (section 6);
  - in batch-2's supplementary positions 1–17, under those conditions, the controls took 84.7 and
    43.2 s, and the same deadlines gave two late jobs (5.2).

  This is one batch against another, not a controlled comparison.
- **What the slack does not show.** P3 re-derives D only if T exceeds 2S, so D was kept, and this
  batch met it with room. On time and late still classify jobs on this host only (Part A, section
  3). A slower state of this host can come closer to the deadlines, as batch-2's late jobs did.

### 10.6 Host conditions

batch-3 records `vm_stat`'s counters by name (since `12c925d`), so its swap figures are swap
traffic, unlike the page counters of sections 5.2 and 6.

| | batch-3 |
|---|---|
| Readings | 32: the start, 30 jobs and the end |
| Power | AC at all 32 |
| Lid | open at all 32 |
| Sleep and wake (power log) | none; the log starts on 2026-10-20, before the batch |
| Clock check | passed: wall minus monotonic +0.034 s, 19 of 19 processes on one clock |
| Memory pressure | level 1 at all 32 |
| Available at the readings | 2.65–3.25 GiB |
| Swap over the batch | in use 0.68–0.72 GiB at the readings, 48 MiB less at the end than at the start; 49 MiB swapped in, none swapped out |
| Paging over the batch | 3.13 GiB paged in, 40 MiB paged out |
| Container peaks | MySQL 319 of 512 MiB (62%); Kafka 497 of 640 MiB (78%) |
| Other containers | none at any of the 32 readings. The monitor ran for the whole batch without error: 0 events of other projects' containers, 5,481 of this project's |

### 10.7 Answers

_The questions are those of spec §11. The answers below were drafted with Claude Code and
approved by the author, unchanged, on 2026-10-27. The approved answers of section 7, which rest on
batch-1 and batch-2, are unchanged._

**E1 (drafted with Claude Code; approved by the author on 2026-10-27).**
- batch-3 gives a second valid correctness verdict, with the same outcome as batch-2: all 30 jobs
  succeeded with exactly one accepted result each, and every accepted result matched the reference
  run.
- This held for the 10 jobs claimed twice and the 8 executed twice, including the 2 W4 jobs that
  completed two executions and had only one accepted.
- No job had more than one accepted result. The two W5a jobs have no matching report in the
  worker's log, as designed.
- These are counts from two batches of 30 jobs on one host, not a rate.

**E2 (drafted with Claude Code; approved by the author on 2026-10-27).** batch-3 is the formal batch with valid recovery times: one
batch, on this host and this configuration, with two jobs per case. Each time below names its
origin.
- **A worker killed before its claim (W1):** the standby received the job 13.6 and 14.9 s after
  the kill. The job finished 35.2 and 36.2 s after it.
- **A worker killed or stopped after its claim (W2, W3, W4, W6):** the reconciler requeued the job,
  and it was claimed again 58.4–64.0 s after the injection. It finished 79.9–86.2 s after the
  injection.
- **A whole worker tree stopped for 90 s (W7):** the job was claimed again 59.1 and 59.2 s after
  the stop. It finished 112.4 and 112.5 s after the stop, 22.4 s after the stopped tree resumed.
- **A Kafka restart (K1):** the attempt went on. Kafka was ready again 3.1 and 3.3 s after the
  restart began, and the job finished 16.3 and 17.2 s after that start.
- **Kafka stopped around the submit (K2):**
  - Kafka returned 31.8 and 31.9 s after the stop;
  - the reconciler published the job 2.9 and 4.1 s after Kafka's return;
  - the first claim came 15.0 s after Kafka's return;
  - the job finished 36.7 and 36.9 s after Kafka's return, which is 68.6 and 68.8 s after the stop.
- **A MySQL stop (D1, mid-step; D2, while the owner held its acceptance):** MySQL returned 31.2 s
  after the stop, before the fence, and every attempt went on.
  - D1 finished 6.1 and 6.5 s after MySQL's return.
  - D2's retried acceptance succeeded at MySQL's return, −0.1 and 0.2 s from the harness's
    reading of it.
- **Kills after the acceptance (W5a, W5b):** each job stayed succeeded with its one accepted result.
- **Duplicate publications (X1):** both duplicates of each job were delivered and refused as
  `succeeded`, with one claim per job.
- **All 30 jobs met their deadlines,** with 51.9–140.1 s of slack. That is more than Part A
  expected, mainly because the runs took about 22 s rather than the 40–50 s assumed (10.5).
- **No job was lost or accepted twice:** all 30 succeeded with exactly one accepted result.
- **No branch with fencing:** D1 and D2 ran only the branch without fencing, because MySQL
  returned before the fence.

### 10.8 Limits (drafted with Claude Code; approved by the author on 2026-10-27)

- **One batch, one host:** an 8 GiB Mac, two jobs per case (four controls), reported as counts with
  no rates. The results describe this host in this state, at memory pressure level 1. batch-2's
  supplementary observations were slower, at level 2.
- **Deadlines as set by P3,** not re-derived. On time and late classify jobs on this host only, and
  the slack here was large (10.5).
- **D1 and D2 show one branch only:** MySQL returned before F in all four jobs, so the fenced branch
  of Part A's predictions was not observed.
- **The service's return is the harness's reading,** which can trail a worker's reconnection by a
  fraction of a second (position 28).
- **The exclusive window:** this project's and other projects' containers were watched for the
  whole batch. Other host processes were checked only at the session's start (no test, job or Spark
  process), and the session asked for the editor and other applications to be closed. Neither the
  harness nor the collector records other processes during the batch.
- **The frozen code includes an exception:** `4fc550e`'s change to the container events' text ran
  in this batch without a live preflight of its own, as the author decided (Part A, section 13).
- **The Kafka line in the console** is attributed from the code and records; its time is not
  recorded (10.2).
- **batch-1 and batch-2 are unchanged:** both stay invalid for recovery times, and batch-3 does not
  revise their verdicts.

### 10.9 Records

In `data/outputs-recovery/formal/`, outside Git:

- `batch-3/`, the harness's records with the collector's outputs (`4fc550e`). It holds 1,442 files.
  Its fingerprint, `34fa05af8be692b3`, is the first 16 hex digits of a SHA-256 over each file's
  relative path and bytes, in sorted order. The fingerprint was the same after the session and
  when this section was drafted.
- `batch-3.console.log` and `batch-3.collect.log`, the session's output.
- `batch-3.verify.txt`, the frozen-code check. Claude Code reran it on 2026-10-27, after the
  author's own run, with the same result: exit 0, `FROZEN CODE: VERIFIED`.
