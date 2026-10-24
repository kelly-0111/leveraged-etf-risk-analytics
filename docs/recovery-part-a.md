# Recovery experiments: Part A proposal, 28 jobs (DRAFT)

_**Draft, not approved.** A proposal for the author's decision; no formal batch has run, and the
workload, deadlines and memory rules below are provisional. It condenses
[recovery-experiments.md](recovery-experiments.md) for the preferred draft. Every command, event
and record in it was checked against the tooling at `772b647` and the fixes of section 9. The
memory rules stay provisional until M2's isolated memory-budget check. Drafted with Claude Code
(Opus 5.5) at the author's request on 2026-10-24; the decisions in section 10 are the author's._

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

A missed injection takes C0's deadline from its submit.

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
caffeinate -i uv run --group jobs python -m etf_risk.jobs.harness batch \
    --plan data/outputs-recovery/preflight/plan-1.json --out data/outputs-recovery/preflight/preflight-1
uv run --group jobs python analysis/collect_recovery_measurements.py \
    --batch data/outputs-recovery/preflight/preflight-1
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
    --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/outputs-recovery/formal/batch-1 --formal

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

| Part | Seconds | Basis |
|---|---|---|
| Containers up and ready, `init-db`, topic | about 60 | assumed |
| Reference run (windows and spark_pipeline under the launcher) | about 35 | M2's steps (25.6 s) plus starts, assumed |
| Reconciler and two workers started and joined | about 25 | assumed |
| 28 jobs | 2,806 | the estimator, 2 × 1,403 |
| Quiescence, final snapshot, `down -v` | about 60 | assumed |
| **Batch** | **2,986, about 50 min** | the estimator, with 180 s for the fixed parts |
| Plan and collection | about 120 | assumed |
| **End to end** | **about 52 min** | |

The batch comes to 52, 55 or 60 minutes if T is 45, 50 or 60 s. Restarts of 20 s instead of 12 add
about 2 minutes (16 restarts), and restores of 40 s instead of 20 add about 1 minute. A job that
hangs stops the batch at its drain limit, at most 2D from its reference (340 s for W7). The
preflight measures each of these:
- `services_up` seconds;
- the reference steps' times;
- process starts and restarts;
- T, from its two C0 jobs.

The preflight itself takes about 18 minutes for the batch and about 15 more for the two test runs.

## 9. Gaps in the service-only paths, fixed on 2026-10-24

Found by reviewing the paths that only a live batch runs; fixed at the author's approval and
checked offline only (no services yet).

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

## 10. Author decisions

| Decision | Recommended |
|---|---|
| Workload (P1) | 28 jobs in one batch; the 84 jobs stay the alternative |
| Clock (P2) | the defaults, confirmed by the preflight |
| Deadlines (P3) | as in section 3; re-derived from the measured T only if T > 70.2 s |
| Harness waits | 3 s phase delay, 90 s W7 stop, 30 s outages |
| Clock-check tolerance | 1 s |
| Injection method (P5) | the fault file, as implemented |
| Memory (P4) | flag at 90%, stop at 95%, host memory recorded and not used as a gate; provisional until M2's check |
| A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both |
| Seed | an integer the author fixes in the plan before the batch |
