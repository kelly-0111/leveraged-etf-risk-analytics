# Recovery experiments: Part A proposal, 28 jobs (DRAFT)

_**Draft, not approved.** A proposal for the author's decision; no formal batch has run, and the
workload, deadlines and memory rules below are provisional. It condenses
[recovery-experiments.md](recovery-experiments.md) for the preferred draft. Every command, event
and record in it was checked against the tooling at `772b647` and the fixes of section 9. The
memory rules stay provisional until M2's isolated memory-budget check. A live preflight ran on
2026-10-24 as functional validation under recorded memory pressure (section 11); its times and
memory readings are not performance or budget evidence. Drafted with Claude Code (Opus 5.5) at the
author's request on 2026-10-24; the decisions in section 10 are the author's._

## 1. Workload

- One batch on fresh MySQL and Kafka containers. The reference run comes first, then 28 jobs: 2 of
  each of the 14 cases, in an order shuffled from a seed recorded in the plan.
- Each job is the calendar-year job on `full-2026-10-12`, with `max_attempts` 3. The plan also
  records stride 21, which only rolling windows use. One job runs windows, spark_pipeline and verify
  (about 35 s of steps at M2's measurements).
- Two workers, A then B, each waited for in the assignment events, and one reconciler.

| Case | Injection | Method and phase |
|---|---|---|
| C0 | none | baseline; measures T |
| W1 | SIGKILL of the owner | fault file, `before_claim` |
| W2 | SIGKILL of the owner | fault file, `after_claim` |
| W3 | SIGKILL of the claiming worker | harness, 3 s into `spark_pipeline` |
| W4 | SIGKILL of the owner | fault file, `after_pipeline` |
| W5a | SIGKILL of the owner | fault file, `after_accept_commit` |
| W5b | SIGKILL of the owner | fault file, `after_accept` |
| W6 | SIGSTOP of the worker until the takeover, then SIGCONT and SIGTERM | harness, mid-step |
| W7 | SIGSTOP of the whole tree for 90 s, then SIGCONT and SIGTERM | harness, mid-step |
| K1 | `docker compose restart kafka` | harness, mid-step |
| K2 | Kafka stopped 30 s around the submit | harness, before the submit |
| D1 | MySQL stopped 30 s | harness, mid-step |
| D2 | MySQL stopped 30 s while the owner holds | fault file `after_pipeline` (hold) |
| X1 | the job id published again, at its claim and after its success | harness |

## 2. Timing (P2: the defaults of timing.py, no override)

| Lease L | Renewal R | Fence margin M | F | Worker tick | Watchdog t_w | Kill grace G |
|---|---|---|---|---|---|---|
| 60 s | 10 s | 10 s | last renewal + 50 s | 1 s | 0.5 s | 7 s (5 + 2) |

| Step limits | Attempt | Session S_k | Heartbeat h | Reconciler P | Publication grace g | Confirmation |
|---|---|---|---|---|---|---|
| 120 / 600 / 300 s | 900 s | 15 s | 3 s | 5 s | 30 s | 10 s |

## 3. Deadlines (P3)

D = ceil5(B + 2S): B is the design's latest start of the next run after the deadline's reference,
and 2S is 70.2 s (twice M2's slowest step sum, 35.1 s). `max_lag_s` is 1 s and the drain limit is D.

| Cases | Reference | B | D |
|---|---|---|---|
| C0, W5a, W5b, K1, X1 | submit (C0), injection | 0 | 75 s |
| W1 | injection | S_k + h + 1 = 19 s | 90 s |
| W2, W3, W4, W6 | injection | L + P = 65 s | 140 s |
| W7 | injection | max(L + P, 90 + 2 t_w + G) = 98 s | 170 s |
| K2 | Kafka's return | g + P + 19 = 54 s | 125 s |
| D1, D2 | MySQL's return | L + P = 65 s | 140 s |

A missed injection takes C0's deadline from its submit. The preflight's two C0 jobs took 52.4 and
46.8 s (median 49.6 s). That is above the 40 s assumed but below 70.2 s, so by P3's own rule D is
not re-derived; the margins shrink from 31–35 s to about 20–25 s. Both values come from a host
under memory pressure (section 11).

## 4. Predictions

The table assumes T = 40 s and restore times of about 20 s; neither has been measured on this clock.
"Finish by" is the latest finish the design predicts, B + T, from the deadline's reference; the
margin is D minus it.

| Case | Claims / accepted | Detection and window | Finish by | Margin |
|---|---|---|---|---|
| C0 | 1 / 1 | — | T, 40 s | 35 s |
| W1 | 1 / 1 | standby's `delivered`, 12–19 s | 59 s | 31 s |
| W2, W4 | 2 / 1 | reconciler's `requeued`, 60–65 s | 105 s | 35 s |
| W3, W6 | 2 / 1 | `requeued`, 50–65 s | 105 s | 35 s |
| W7 | 2 / 1 | `requeued`, 50–65 s; the replacement waits for the host lock until 98 s | 138 s | 32 s |
| W5a | 1 / 1 | — ; Q3a `no matching report`, by design | — | — |
| W5b | 1 / 1 | — | — | — |
| K1 | 1 / 1 | — (the attempt goes on) | under T | over 35 s |
| K2 | 1 / 1 | reconciler's `published`, within P of Kafka's return | 94 s | 31 s |
| D1 | 1 / 1 if MySQL is back before F, else 2 / 1 | `renewal_failed`; then `renewed` or `requeued` | 105 s | 35 s |
| D2 | 1 / 1 if MySQL is back before F, else 2 / 1 | `retry` of `accept_result`; then `accepted`, or `failed_after_ack` and `requeued` | 105 s | 35 s |
| X1 | 1 / 1 | both duplicates refused as `succeeded` | T | 35 s |

Expected for E1 on all 28 jobs: Q1 `ok`; `status --check` exits 0; no invariant violation; every
accepted result equals the reference run; no overlapping step intervals. Each of these is checked
per job and reported as found.

**Assumptions and uncertainty.**
- T is unmeasured on the default clock. The preflight's C0 jobs measure it; if T exceeds 2S (70.2 s),
  re-deriving D is the author's option.
- Restore times are unmeasured. From the stop, F comes 40–50 s later; MySQL returns after 30 s plus
  its restore. D1's and D2's branches therefore depend on the restore, and both branches are valid
  outcomes.
- A killed worker's dead group member keeps its session for 15 s, so a restart may take about 20 s
  rather than the estimator's 12 s.
- During K1 and K2, consumers log `consumer_error` and keep polling, with no back-off; the rejoin
  bound of 19 s is assumed to hold.
- X1's first duplicate arrives while its owner runs the job, so it is read only afterwards. Both
  duplicates are therefore refused as `succeeded` (outline 3.1, corrected on 2026-10-24).
- Results are counts per case (k of 2), with no rates.

## 5. Injection success and misses (harness)

- **Fault-file cases** (W1, W2, W4, W5a, W5b, D2): the owner is read from the assignment events,
  and only its fault file is armed (`armed` records `owner_after`).
  - Made: that worker's `fault_injected` at the case's point, after this job's `delivered` or
    `claimed`. For kills, the worker has also exited within 30 s. `t_inj` is the event's `mono`, or
    the MySQL stop for D2.
  - Missed: the other worker claims the job first (a miss at once), or no event comes within 300 s.
    The file is then removed.
- **Mid-step cases** (W3, W6, W7, K1, D1):
  - Made: a claim with `step_started` for `spark_pipeline`, no `step_ended` (named `name`) and the
    step's log file, and the step still running 3 s later.
  - Missed: 300 s without that phase, or the step ended during the 3 s.
- **K2**: the stop precedes the submit. A submit that fails is `job_not_submitted` and stops the
  batch.
- **X1**: made once a claim is seen; the second publication follows the success.
- **A missed job is still followed.** Its latencies are `n/a: injection missed`, and it keeps its
  row as `missed`.

## 6. Stop rules and outcomes

- **The batch stops** when one of these happens; the remaining jobs are recorded as `not_run`, with
  the reason:
  - a job is unfinished at its drain limit (`an unfinished job`);
  - a submit fails;
  - a container's batch peak passes 95% of its limit (provisional P4; 90% is flagged);
  - an error in the harness during a job (`job_error`).

  Quiescence (SIGKILL of the writers), the final snapshot and `down -v` still run.
- **Late:** running at its deadline and succeeded later. It counts as `late` with `deadline_met` no,
  and the later success never changes that.
- **Failed:** out of attempts. Q1 `failed`, Q2 `failed`, `deadline_met` no.
- **Unknown:** each is reported as unknown, never as met or as no overlap:
  - a failed deadline read gives `deadline not observed`, with `deadline_met` unknown;
  - a step without both monotonic times makes the overlap `unknown`;
  - a missing injection time gives `unknown: no injection time`;
  - a missing harness record gives `unrecorded`.
- **Validity (6.1):** a batch that fails it does not count, and its records and outcomes stay. E1
  and E2 findings never change validity.

## 7. Commands (from the repository root of the checkout that ran the plan)

```bash
# 0. Preconditions: the test window is released; nothing of this project runs
docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
uv run --group jobs python -m etf_risk.services others         # other projects' containers: a count
git status --short                                             # clean: the batch records the commit

# 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results
uv run --group jobs python -m etf_risk.jobs.harness plan --purpose preflight --seed 1 \
    --jobs C0,W1,W6,W7,K1,K2,D1,D2,C0 --out data/outputs-recovery/preflight/plan-1.json
# --out must be an absolute path until G9 is fixed (section 9)
caffeinate -i uv run --group jobs python -m etf_risk.jobs.harness batch \
    --plan data/outputs-recovery/preflight/plan-1.json --out "$PWD/data/outputs-recovery/preflight/preflight-2"
uv run --group jobs python analysis/collect_recovery_measurements.py \
    --batch data/outputs-recovery/preflight/preflight-2
# The job tests and the live pipeline tests against both services, outputs kept with the preflight
docker compose -f docker/compose.yaml up -d --wait mysql kafka
uv run --group jobs python -m etf_risk.services ready mysql kafka
ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
    uv run --group jobs python -m pytest tests/test_jobs_*.py 2>&1 | tee data/outputs-recovery/preflight/job-tests.txt
ETF_RISK_LIVE_PIPELINE=1 ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 \
    ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 uv run --group jobs python -m pytest tests/test_jobs_live_pipeline.py \
    2>&1 | tee data/outputs-recovery/preflight/live-pipeline.txt
docker compose -f docker/compose.yaml down -v

# 2. Formal batch: only after the author approves Part A; the plan is the preferred draft by default
uv run --group jobs python -m etf_risk.jobs.harness plan --purpose formal --seed <SEED> \
    --out data/outputs-recovery/formal/plan-<SEED>.json
uv run --group jobs python -m etf_risk.jobs.harness estimate --plan data/outputs-recovery/formal/plan-<SEED>.json
caffeinate -i uv run --group jobs python -m etf_risk.jobs.harness batch \
    --plan data/outputs-recovery/formal/plan-<SEED>.json --out "$PWD/data/outputs-recovery/formal/batch-1" --formal

# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder; exit 1 on invalidity
uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/formal/batch-1

# 4. Cleanup: the batch itself ends with `docker compose down -v`; check, and recover if it was killed
docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
docker compose -f docker/compose.yaml down -v                  # only if something was left
```

`plan` creates its folder. A batch writes `harness.jsonl` (with the host's memory before each
job, the Spark scratch at the start and after quiescence, and any setup or final error) and
`plan.json`. It also writes the folders `events/` (A, B, `reconciler-<pid>`, `submit`),
`jobs/<store>/<run>/` (with `logs/*.launcher.json`, `attempt.json` and `manifest.json`),
`reference/`, `logs/`, `crosscheck/Q0–Q3b.csv` and `export/`, and the files `status-check.txt` and
`cleanup.txt`. The batch exits 1 if its setup or final steps failed. The collector reads these,
and the snapshot's input files for its input check.

## 8. Runtime

Revised with the preflight's measurements (section 11), all taken under memory pressure:

| Part | Seconds | Basis |
|---|---|---|
| Containers, `init-db`, topic, reference run, the three processes | 81 | preflight-2's setup (services 14 s, reference run 58 s) |
| 28 jobs | 2,836 | the estimator with T 49.6 s, restores 11 s and restarts 5 s |
| Quiescence, final snapshot, `down -v` | about 20 | preflight-2 (3 s to `batch_ended`) plus teardown |
| **Batch** | **2,936, about 49 min** | the estimator, with 100 s for the fixed parts |
| Plan and collection | about 120 | assumed |
| **End to end** | **about 51 min** | |

- **Ranges.** The batch comes to 51.6 min if T is 55 s. It comes to 51.7 min if restores take
  20 s, since D2 then takes its fenced branch, as D1 did in the preflight.
- **Earlier figures.** The first estimate, with unmeasured assumptions, was 49.8 min. Preflight-2
  took 15.1 min against an estimated 17.8.
- **Limits.** A job that hangs stops the batch at its drain limit, at most 2D from its reference
  (340 s for W7).
- **Status.** Planning figures, not performance evidence.

## 9. Gaps in the service-only paths: G1–G8 fixed on 2026-10-24, G9 open

G1–G8 were found by reviewing the paths that only a live batch runs, fixed at the author's approval,
and checked offline. G9 was found by preflight-1 and is not fixed.

| | Gap | Now | Checked by |
|---|---|---|---|
| G1 | An error during setup was not written to `harness.jsonl`, and `batch_ended` said `stop_reason` null | `setup_error`, every planned job `not_run`, exit code 1; containers removed only if the batch started them; the collector fails `records_complete` | harness tests; mutations |
| G2 | Quiescence counted the harness's own store connection as another client, against 4.4 | the harness closes its own connections, then waits up to 15 s for MySQL to list no other client | harness test with a stand-in process list; mutation |
| G3 | 6.2 and the records rely on `cleanup`'s listing, which the harness never produced | `cleanup` (dry run) in the final snapshot, saved as `cleanup.txt` | synthetic batch; mutation |
| G4 | P4's host memory before each job was not recorded | `host_memory` before each job, in `injections.csv` too; never a gate | synthetic batch; mutation |
| G5 | 6.5's "no new Spark scratch" had nothing behind it | the scratch listed at the start and after quiescence; new entries in `quiescent` and the collector's `nothing_left` | harness and synthetic tests; mutations |
| G6 | The collector's example path predated the purpose folders | `.../formal/<batch>` and `.../preflight/<name>` | — |
| G7 | `plan --out` needed its folder to exist | `plan` creates it | harness test |
| G8 | The outline's X1 row predicted `lease held` for the first duplicate | `succeeded`, in the outline and here | — |
| G9 | With a relative batch folder, the harness passed relative paths to the reference run's launcher, which runs in `.work`; the step could not start (launcher exit 71, `launch_failed`) | **open**: run with an absolute `--out`, as preflight-2 did; proposed fix: the batch makes its folder absolute, with a test and a mutation | preflight-1 (failed), preflight-2 (absolute) |

## 10. Author decisions

| Decision | Recommended |
|---|---|
| Workload (P1) | 28 jobs in one batch; the 84 jobs stay the alternative |
| Clock (P2) | the defaults, confirmed by the preflight |
| Deadlines (P3) | as in section 3; the preflight's T (median 49.6 s) is below 70.2 s, so no re-derivation |
| Harness waits | 3 s phase delay, 90 s W7 stop, 30 s outages |
| Clock-check tolerance | 1 s |
| Injection method (P5) | the fault file, as implemented |
| Memory (P4) | flag at 90%, stop at 95%, host memory recorded and not used as a gate; provisional until M2's isolated check, which could not run with about 1.2 GiB available |
| G9 | fix it (the batch makes its folder absolute) before any formal batch, with a test and a mutation |
| Live coverage of W2, W3, W4, W5a, W5b and X1 | after the G9 fix, a second preflight with C0 and these six (about 12 min), rather than their first live run in the formal batch |
| Host state for a formal batch | first the isolated memory check, passing on a host with enough free memory; then a stated minimum of available memory before each job, recorded per job (8.3) |
| A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both |
| Seed | an integer the author fixes in the plan before the batch |

## 11. Live preflight, 2026-10-24: functional validation only

_Run in the exclusive window that M2 handed over, on code `7bd4d20`, under recorded memory
pressure: 1.2–1.5 GiB of 8 GiB available before each job, with about 10 GiB of swap in use. M2's
isolated memory check could not run for the same reason, so the container budgets are unvalidated.
The times and memory below show that the paths work; they are not performance or budget evidence.
Every record stays under `data/outputs-recovery/preflight/`, apart from formal results._

| Run | Outcome |
|---|---|
| preflight-1: the plan, relative batch folder | **failed in setup**: the reference run's windows step could not start (launcher exit 71, `launch_failed`; G9). Recorded as `setup_error`, all 9 jobs `not_run`; the final snapshot and teardown ran; harness exit 1; validity failed (`records_complete`) |
| preflight-2: the same plan, absolute batch folder | 9 of 9 injections made, none missed or unrecorded; all 9 jobs on time; validity passed; harness exit 0; 15.1 min |
| job tests against MySQL 8.4 and Kafka | 515 passed, 10 skipped (the live cases, run next), 0 failed, in 2 min 53 s |
| live pipeline module | 10 passed, 0 failed, in 10 min 54 s; its overlap check now compares monotonic times |
| full offline suite, after the services were removed | 622 passed, 30 skipped (the MySQL, Kafka and live tests, which passed in the two runs above), 0 failed, in 9 min 54 s, Spark tests included |

Preflight-2 by case. Finish is measured from the deadline's reference; D is from section 3.

| Case | Claims | Detection | Finish | D | Observed path |
|---|---|---|---|---|---|
| C0 | 1 | — | 52.4 s | 75 s | baseline |
| W1 | 1 | standby's `delivered`, 13.5 s | 69.8 s | 90 s | killed at `before_claim`; the standby took over |
| W6 | 2 | `requeued`, 57.9 s | 103.9 s | 140 s | the worker stopped; takeover; fenced after SIGCONT |
| W7 | 2 | `requeued`, 57.5 s | 132.0 s | 170 s | a tree of 4 processes stopped for 90 s; the replacement ran after it |
| K1 | 1 | — | 47.6 s | 75 s | Kafka ready 9.3 s after its restart began; the attempt went on |
| K2 | 1 | `published`, 3.0 s after Kafka's return | 64.3 s | 125 s | Kafka back 33.9 s after the stop; one claim |
| D1 | 2 | `renewal_failed`, 5.9 s after the stop | 54.6 s | 140 s | MySQL back 40.8 s after the stop, after F: fenced, then attempt 2 |
| D2 | 1 | `retry` of `accept_result`, 3.9 s after the stop | 0.5 s | 140 s | MySQL back 31.6 s after the stop, before F: accepted |
| C0 | 1 | — | 46.8 s | 75 s | baseline |

- **E1 and the records:**
  - every Q1 verdict `ok`, no overlapping step intervals, `status --check` exit 0 and no invariant
    violation;
  - all 9 accepted results equal the reference run, with matching digests, and the three
    fingerprints are equal;
  - Q3a `reported once` and Q3b `matches` throughout;
  - quiescence left no process, no other client and no new Spark scratch, and the cleanup listing
    is recorded;
  - the clock check passed (`ts` minus `mono` −0.018 s over the batch), with 6 of 6 process starts
    on one clock and one code identity over 50 records.
- **Ownership:** read from the assignment events throughout. A owned the partition first, B from
  its join until W6, and A after that. Every arming hit the owner.
- **Liveness:** 28 `retry` events (D2's acceptance during the outage) and 15 failed reconciler
  passes (during the MySQL outages). There was no `failed_after_ack`, no `consumer_error` and no
  serve restart.
- **Against the assumptions:**

  | Quantity | Assumed | Observed |
  |---|---|---|
  | T | 40 s | 52.4 and 46.8 s |
  | restart and rejoin | 12 s | 3.7–5.2 s |
  | restore after start | 20 s | Kafka 3.9 s; MySQL 1.6 and 10.8 s |
  | fixed batch parts | 180 s | about 100 s (setup 81 s) |
  | reference steps | 25.6 s (M2) | windows 9.1 s, spark_pipeline 48.5 s |

- **Memory, informational only:**
  - container peaks in preflight-2: MySQL 250 of 512 MiB (49%) and Kafka 386 of 640 MiB (60%);
  - after the two test runs: 208 and 372 MiB;
  - host memory available before each job: 1.19–1.5 GiB.
- **Not covered live:** W2, W3, W4, W5a, W5b and X1 ran only in the synthetic batch. The live
  hook path was exercised through W1, and the mid-step path through W6, W7, K1 and D1.
