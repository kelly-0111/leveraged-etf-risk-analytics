# Recovery experiments: Part B, the formal batches

_Drafted with Claude Code (Opus 5.5) on 2026-10-25 at the author's request. Its sources are the
records in `data/outputs-recovery/formal/` (numbers and tables read by script) and the author's
decisions of 2026-10-25 (section 1). Sections 2–6 give facts. The answers in section 7 were
drafted with Claude Code and approved by the author, unchanged, on 2026-10-25. Part A is
[recovery-part-a.md](recovery-part-a.md), approved on 2026-10-25 (`1c11577`). The records stay
outside Git and have not been changed since the collector wrote them; later notes sit beside them
as separate files. Times are local (UTC−5) on 2026-10-25._

> **Correction, 2026-10-26.** The bytes this document calls "swapped in" and "swapped out"
> (sections 5.2 and 6) are psutil's `sin` and `sout`. On macOS they are page-ins and page-outs,
> not swap traffic. Swap in use is recorded correctly. Sections 5.2 and 7.3 describe the host as
> swapping heavily; [host-counters-correction.md](host-counters-correction.md) explains what the
> records support. The text below is unchanged.

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
17 readings) with heavy swapping, on this host only. They are counts per job, with no rate and no
performance claim. Every outcome in the range is kept, the two late jobs included.

Detection, re-run and finish times are the collector's, as section 5 of the outline defines them:
from the injection, or from the submit for C0. D and the deadline column count from each case's
deadline reference (Part A, section 3). For W2–W7 that reference is the injection, and for C0 the
submit. For D1 and K2, the injection is the service's stop, while the reference is the service's
return, 35.3–35.8 s after the stop. Measured from the return, the D1 jobs finished in 21.7 and
14.9 s and the K2 job in 68.4 s.

| Position | Case | Claims | Detection (s) | Re-run (s) | Finish (s) | D (s) | Deadline | Pressure | Available (GiB) | Swapped out during (MiB) |
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
  - position 1 (C0, the batch's first job), 84.7 s against 75 s, with 83 MiB swapped out during it;
  - position 16 (W6), 182.6 s against 140 s, with 132 MiB swapped out during it.
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
| Swap over the batch | not computable: no end reading | in use +2.67 GiB; 1.35 GiB swapped out, 47.9 GiB swapped in |
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

- **One host:** an 8 GiB Mac under memory pressure, swapping heavily. Two jobs per case, reported
  as counts with no rates.
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
