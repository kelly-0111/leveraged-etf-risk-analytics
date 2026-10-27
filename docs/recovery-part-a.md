# Recovery experiments: Part A, 30 jobs (approved)

> **Approved by the author.** No formal batch had run when Part A was approved.
> - 2026-10-24: this host, for correctness observations and for recovery times under its recorded
>   conditions, with the limitations of section 12; a control C0 at each end of the batch, making
>   30 jobs.
> - 2026-10-25: the 13 remaining decisions of section 10, seed 544 included.
>
> **After approval:** the formal batches ran on 2026-10-25. Their results and the author's decision
> are in [recovery-part-b.md](recovery-part-b.md); section 13 lists what changed since.

> **Correction, 2026-10-26.** The bytes this document called "swapped in" and "swapped out" are
> psutil's `sin` and `sout`, which `harness.host_state()` records as `swap_in_bytes` and
> `swap_out_bytes`. On macOS they are page-ins and page-outs, not swap traffic. At the author's
> instruction, sections 11 and 12 now say "paged in" and "paged out", with the figures unchanged
> (section 13 lists the changes). Swap in use is recorded correctly, and its figures are kept.
> See [host-counters-correction.md](host-counters-correction.md).

_This document condenses [recovery-experiments.md](recovery-experiments.md) for the preferred
draft. Every command, event and record in it was checked against the tooling at `fcaa645`. M2's
isolated check has since validated the container limits, under host memory pressure and with
documented sampling limits; native-process memory remains unvalidated. Four live preflight batches
ran on 2026-10-24 under memory pressure (section 11). Under the collector's current checks, only
preflight-4 is valid for recovery times, and preflight-3 stays invalid for timing. None of their
times or memory readings is performance or budget evidence. Section 12 sets the protocol for
recovery batches on this host. Drafted with Claude Code (Opus 5.5) at the author's request on
2026-10-24; the decisions in section 10 are the author's._

## 1. Workload

- One batch on fresh MySQL and Kafka containers. The reference run comes first, then 30 jobs:
  - a C0 control first;
  - 2 of each of the 14 cases (28 jobs, the two shuffled C0s among them), in an order shuffled from
    a seed recorded in the plan;
  - a C0 control last.

  The controls were approved on 2026-10-24 (section 12, condition 6). The harness's default plan
  makes this order.
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

A missed injection takes C0's deadline from its submit. Preflight-2's two C0 jobs took 52.4 and
46.8 s (median 49.6 s), and preflight-4's controls 45.1 and 50.9 s. All four are above the 40 s
assumed but below 70.2 s, so by P3's own rule D is not re-derived; at the median of 49.6 s the
margins shrink from 31–35 s to about 20–25 s. All four come from a host under memory pressure
(section 11), and preflight-2's are planning figures only, since its power and lid were not
recorded. S itself (35.1 s) was measured under host memory pressure too, so D rests on observations
of this host, not on a validated standard: on time and late classify jobs on this host and nothing
more.

## 4. Predictions

The table keeps the drafted assumptions, T = 40 s and restore times of about 20 s; section 11
compares them with what the preflights observed. "Finish by" is the latest finish the design
predicts, B + T, from the deadline's reference; the margin is D minus it.

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

Expected for E1 on all 30 jobs: Q1 `ok`; `status --check` exits 0; no invariant violation; every
accepted result equals the reference run; no overlapping step intervals. Each of these is checked
per job and reported as found.

**Assumptions and uncertainty.**
- T was unmeasured when the table was drafted. The preflights' C0 jobs took 45.1–52.4 s
  (section 3), below 2S (70.2 s); if T exceeds 2S, re-deriving D is the author's option.
- Restore times were unmeasured too; preflight-2 observed Kafka 3.9 s and MySQL 1.6 and 10.8 s
  (section 11). From the stop, F comes 40–50 s later; MySQL returns after 30 s plus its restore.
  D1's and D2's branches therefore depend on the restore, and both branches are valid outcomes.
- A killed worker's dead group member keeps its session for 15 s, so a restart may take about 20 s
  rather than the estimator's 12 s (preflight-2 observed 3.7–5.2 s).
- During K1 and K2, consumers log `consumer_error` and keep polling, with no back-off; the rejoin
  bound of 19 s is assumed to hold.
- X1's first duplicate arrives while its owner runs the job, so it is read only afterwards. Both
  duplicates are therefore refused as `succeeded` (outline 3.1, corrected on 2026-10-24).
- Results are counts per case (k of 2; k of 4 for C0, the two controls included), with no rates.

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
  - a container's batch peak passes 95% of its limit (P4; 90% is flagged);
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
pgrep -lf 'pytest|etf_risk\.jobs|org\.apache\.spark'           # must print nothing (section 12, condition 4)
git status --short                                             # clean: the batch records the commit
pmset -g batt | head -1                                        # 'AC Power' (section 12)
ioreg -r -k AppleClamshellState -d 4 | grep '"AppleClamshellState"'   # '= No': the lid is open
uv run --group jobs python -c "import psutil; print(psutil.virtual_memory().available / 2**30)"   # GiB (section 12)

# 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results.
#    --jobs keeps the order as listed and adds no controls; this list has a C0 at each end
uv run --group jobs python -m etf_risk.jobs.harness plan --purpose preflight --seed 1 \
    --jobs C0,W1,W6,W7,K1,K2,D1,D2,C0 --out data/outputs-recovery/preflight/plan-1.json
# Keep the host awake: on AC power with the lid open (section 12); -s works on AC power only
caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
    --plan data/outputs-recovery/preflight/plan-1.json --out data/outputs-recovery/preflight/<name>
uv run --group jobs python analysis/collect_recovery_measurements.py \
    --batch data/outputs-recovery/preflight/<name>
# The job tests and the live pipeline tests against both services, outputs kept with the preflight
docker compose -f docker/compose.yaml up -d --wait mysql kafka
uv run --group jobs python -m etf_risk.services ready mysql kafka
ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
    uv run --group jobs python -m pytest tests/test_jobs_*.py 2>&1 | tee data/outputs-recovery/preflight/job-tests.txt
ETF_RISK_LIVE_PIPELINE=1 ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 \
    ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 uv run --group jobs python -m pytest tests/test_jobs_live_pipeline.py \
    2>&1 | tee data/outputs-recovery/preflight/live-pipeline.txt
docker compose -f docker/compose.yaml down -v

# 2. Formal batch: only after the author approves Part A. The default plan is the preferred draft:
#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json).
#    <SEED> is the approved seed (section 10, row 2).
uv run --group jobs python -m etf_risk.jobs.harness plan --purpose formal --seed <SEED> \
    --out data/outputs-recovery/formal/plan-<SEED>.json
uv run --group jobs python -m etf_risk.jobs.harness estimate --plan data/outputs-recovery/formal/plan-<SEED>.json
caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
    --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/outputs-recovery/formal/batch-1 --formal

# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two
#    verdicts, correctness observations and recovery times, and exits 1 unless both are valid: any
#    required check that failed or is unknown gives 1 (battery, a closed lid, a missing reading)
uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/formal/batch-1

# 4. Cleanup: the batch itself ends with `docker compose down -v`; check, and recover if it was killed
docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
docker compose -f docker/compose.yaml down -v                  # only if something was left
```

`plan` creates its folder. A batch writes `harness.jsonl` and `plan.json`. The log holds the
host's state at the start, before each job and at the end (memory, swap, pressure level, power and
lid), the Spark scratch at the start and after quiescence, and any setup or final error. The batch
also writes the folders `events/` (A, B, `reconciler-<pid>`, `submit`), `jobs/<store>/<run>/` (with
`logs/*.launcher.json`, `attempt.json` and `manifest.json`), `reference/`, `logs/`,
`crosscheck/Q0–Q3b.csv` and `export/`, and the files `status-check.txt` and `cleanup.txt`. It exits
1 if its setup or final steps failed. The collector reads these, and the snapshot's input files for
its input check; its `validity.json` holds each check and the two verdicts.

## 8. Runtime

Revised with the preflight's measurements (section 11), all taken under memory pressure:

| Part | Seconds | Basis |
|---|---|---|
| Containers, `init-db`, topic, reference run, the three processes | 81 | preflight-2's setup (services 14 s, reference run 58 s) |
| 30 jobs, the two controls included | 2,939 | the estimator with T 49.6 s, restores 11 s and restarts 5 s |
| Quiescence, final snapshot, `down -v` | about 20 | preflight-2 (3 s to `batch_ended`) plus teardown |
| **Batch** | **3,039, about 51 min** | the estimator, with 100 s for the fixed parts |
| Plan and collection | about 120 | assumed |
| **End to end** | **about 53 min** | |

- **Ranges.** The batch comes to 53.5 min if T is 55 s. It comes to 53.4 min if restores take
  20 s, since D2 then takes its fenced branch, as D1 did in the preflight.
- **Earlier figures.** The first estimate, with unmeasured assumptions, was 49.8 min for 28 jobs
  (51.2 min for 30). Preflight-2 took 15.1 min against an estimated 17.8.
- **Limits.** A job that hangs stops the batch at its drain limit, at most 2D from its reference
  (340 s for W7).
- **Status.** Planning figures, not performance evidence.

## 9. Gaps in the service-only paths: G1–G9, fixed on 2026-10-24

G1–G8 were found by reviewing the paths that only a live batch runs, fixed at the author's approval,
and checked offline. G9 was found by preflight-1, then fixed (`a94eefe`) and checked live by
preflight-3, which ran from a relative folder.

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
| G9 | With a relative batch folder, the harness passed relative paths to the reference run's launcher, which runs in `.work`; the step could not start (launcher exit 71, `launch_failed`) | the batch resolves its folder once, so every path handed to a process is absolute | regression test; mutation `batch-folder-relative`; preflight-3 from a relative folder |

## 10. Author decisions

**Approved by the author on 2026-10-24:**
- this host, for correctness observations and for recovery times under its recorded conditions,
  with section 12's limitations;
- the two controls, one C0 at each end of the batch (30 jobs).

**Approved by the author on 2026-10-25, together** (rows 11 and 13 were added in the last draft):

| # | Decision | Proposed value | Rationale |
|---|---|---|---|
| 1 | Workload (P1) | one batch of 30 jobs: C0, 2 of each of the 14 cases in shuffled order (28), C0; the calendar-year job on `full-2026-10-12`, `max_attempts` 3; results as counts per case (k of 2; C0 k of 4), no rates | every case and recovery path twice, with E1 checked on every job, in about 51 min; the 84-job alternative (2 batches of 42 plus their controls) takes about 2 h 29 min. No rates, since the injections are not shown to be independent |
| 2 | Seed | 544, given to `plan --seed` for the formal plan and never redrawn | any fixed integer works; fixing it now, before any formal order exists, rules out choosing an order |
| 3 | Clock (P2) | the timing.py defaults, no override: lease 60 s, renewal 10 s, fence margin 10 s, session 15 s, heartbeat 3 s, reconciler 5 s, publication grace 30 s; step limits 120, 600 and 300 s, attempt 900 s | E2 times the configuration the job processes run with; E1's token guards do not depend on the clock; preflights 2–4 ran these values and every path behaved as designed |
| 4 | Deadlines (P3) | D = ceil5(B + 2S), S = 35.1 s: 75 s (C0, W5a, W5b, K1, X1), 90 s (W1), 125 s (K2, from Kafka's return), 140 s (W2, W3, W4, W6; D1 and D2 from MySQL's return), 170 s (W7); drain limit D; `max_lag_s` 1 s | B is the design's latest start of the next run; the four C0 times of preflights 2 and 4 (45.1–52.4 s) stay below 2S = 70.2 s, so P3's own rule keeps D; on time and late describe this host only |
| 5 | Harness waits | phase delay 3 s; W7 stop 90 s; outages 30 s (K2, D1, D2); a phase not reached in 300 s is a miss | 3 s puts the kill inside spark_pipeline, the longest step (6 of 6 mid-step injections made); 90 s outlasts the takeover (65 s), so W7's replacement waits for the stopped tree; 30 s outlasts the Kafka session (15 s) and brings MySQL back near F, so D1 and D2 can take either branch (preflight-2 showed both) |
| 6 | Clock-check tolerance | 1 s | wall minus monotonic time drifted 0.018 and 0.028 s over whole batches; preflight-3's sleep showed as 63.8 s and more |
| 7 | Injection method (P5) | the fault file at the named points for W1, W2, W4, W5a, W5b and D2, armed only on the partition's owner; signals from the harness for W3, W6 and W7; `docker compose` for K1's restart and the outages of K2, D1 and D2; a second publication for X1 | those six windows last milliseconds, too short for an outside signal; 14 of 14 injections in preflights 2–4 were made (the 6 fault-file ones included), none missed |
| 8 | Memory (P4) | fresh containers for the batch; peaks read after every job; flag at 90% and stop the batch at 95% of 512 MiB (MySQL) and 640 MiB (Kafka); host memory recorded, never gated | M2 validated these limits (under host pressure); the preflights peaked at 49–62% (MySQL) and 60–77% (Kafka); no measured host figure is tied to recovery behaviour |
| 9 | Host protocol | section 12, conditions 1–7 | each answers preflight-3's failure (a sleep on battery with the lid closed) or a confound; the collector checks 1–3, `pgrep` checks 4 before the start, 5 is recorded and 6 is the default plan |
| 10 | A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labelled as such | relabelling once a cause is known would let results pick the batches; the checks that do not involve time still hold (preflight-3) |
| 11 | The formal batch invalid or stopped early | kept and reported in full; one rerun with the same plan in `formal/batch-2` once the cause is removed (a code fix gets a preflight of the affected cases first); both reported side by side | decided before any result is seen, so no batch is chosen afterwards; Part A had no rule for this |
| 12 | A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both | as done for G9 (preflight-1, then preflight-3) |
| 13 | Code for the formal batch | `fcaa645` (the commit of the approved documents adds no code); no further live preflight | since preflight-4 (`8c5331d`), the tooling changed only in plan generation and the collector, both covered offline by their tests, the synthetic batch and mutations |

## 11. Live preflight, 2026-10-24 and 2026-10-25: functional validation only

_Preflight-1 and preflight-2 ran on code `7bd4d20`, preflight-3 on `a94eefe` (the G9 fix) and
preflight-4 on `8c5331d`, each in an exclusive window that M2 handed over; each test run in the
table names the commit it ran on. All four preflights ran under memory pressure: 1.2–1.7 GiB of
8 GiB available before each job, as recorded, and 4–10 GiB of swap in use at the checks before each
batch; swap in use, the page counters and macOS's pressure level entered the batch records with preflight-4. The times and
memory below show that the paths work; they are not performance or budget evidence. Every record
stays under `data/outputs-recovery/preflight/`, apart from formal results._

| Run | Outcome |
|---|---|
| preflight-1: the plan, relative batch folder | **failed in setup**: the reference run's windows step could not start (launcher exit 71, `launch_failed`; G9). Recorded as `setup_error`, all 9 jobs `not_run`; the final snapshot and teardown ran; harness exit 1; validity failed (`records_complete`) |
| preflight-2: the same plan, absolute batch folder | 9 of 9 injections made, none missed or unrecorded; all 9 jobs on time; validity passed under the collector of the time (`7bd4d20`); harness exit 0; 15.1 min |
| job tests against MySQL 8.4 and Kafka, on `7bd4d20` | 515 passed, 10 skipped (the live cases, run next), 0 failed, in 2 min 53 s |
| live pipeline module, on `7bd4d20` | 10 passed, 0 failed, in 10 min 54 s; its overlap check now compares monotonic times |
| full offline suite, after the services were removed, on `7bd4d20` | 622 passed, 30 skipped (the MySQL, Kafka and live tests, which passed in the two runs above), 0 failed, in 9 min 54 s, Spark tests included |
| preflight-3: C0, W2, W3, W4, W5a, W5b, X1, from a relative batch folder | **invalid for timing**: the clock check failed, because the host slept for about 22 min during W3 (below). 7 of 7 injections made, none missed; its correctness observations are kept apart (below); harness exit 0; 11.6 min monotonic, 33.8 min wall |
| preflight-4: C0, W3, C0 (the W3 rerun with a control on each side), on AC power with the lid open | 3 of 3 injections made; validity passed, the clock check included; harness exit 0 (below) |
| the Kafka cases on `fcaa645`, 2026-10-25, against Kafka and MySQL (`kafka-live-fcaa645.txt`) | 27 passed, 0 failed, 0 skipped, in 43.9 s: the 11 cases that skip without a broker, the MySQL variants of the 4 end-to-end ones, and 12 offline tests. No other container or test process ran; `down -v` then left no container or volume |

**Verdicts under the collector at `5a81bc5`.** Recomputed on 2026-10-24 without writing anything:
the 1,109 files under `data/outputs-recovery/preflight/` kept their modification times.

| Batch | Correctness observations | Recovery times | Failed or unknown |
|---|---|---|---|
| preflight-1 | invalid | invalid | `records_complete` (the setup error); power and lid unknown at the start and end readings |
| preflight-2 | valid | invalid | power and lid unknown at all 11 readings: the batch predates their recording |
| preflight-3 | valid | invalid | the clock check (the host sleep); power and lid unknown at all 9 readings |
| preflight-4 | valid | valid | — |

Preflight-4 is the only batch whose recovery times count under section 12, and as a preflight it
stays apart from formal results.

Preflight-2 by case, functional observations only (verdicts above). Finish is measured from the
deadline's reference; D is from section 3.

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
- **Covered live since:** W2, W3, W4, W5a, W5b and X1, in preflight-3, below.

Preflight-3 is **invalid for timing** and stays so. Its detection, rerun and finish times and its
deadline outcomes remain in its records, and none of them is reported or counted here. What
follows is only its correctness observations, which do not depend on the clock and were checked on
their own.

| Case | Claims | Accepted | Observed path |
|---|---|---|---|
| C0 | 1 | 1 | baseline |
| W2 | 2 | 1 | killed at `after_claim`; the standby's redelivery refused as `lease_held`; requeued; attempt 2 accepted |
| W3 | 3 | 1 | killed 3 s into spark_pipeline; then the host slept (below): early requeues, and attempt 2's renewal refused and fenced; attempt 3 accepted |
| W4 | 2 | 1 | killed at `after_pipeline`; two complete executions, one accepted |
| W5a | 1 | 1 | killed at `after_accept_commit`: Q3a `no matching report`, as designed |
| W5b | 1 | 1 | killed at `after_accept` |
| X1 | 1 | 1 | both duplicates refused as `succeeded` (G8's correction, confirmed) |

- **Correctness observations:**
  - every Q1 verdict `ok`, no overlapping step intervals, `status --check` exit 0 and no invariant
    violation;
  - all 7 accepted results equal the reference run, and the fingerprints agree;
  - quiescence left nothing, and `cleanup.txt` lists the 3 unaccepted attempts' folders;
  - code identity, inputs and complete records all passed.

  Container peaks were MySQL 317 of 512 MiB (62%) and Kafka 495 of 640 MiB (77%); host memory before
  each job was 1.26–1.7 GiB available.
- **The host sleep:**
  - At 21:53:28 local time, about 18 s after W3's injection, the Mac entered "Clamshell Sleep" on
    battery: the lid was closed. `caffeinate -i` prevents idle sleep only.
  - It slept until 22:16:04, apart from two maintenance wakes. Wall time minus monotonic time grew
    by 63.8 s, 116.9 s and 1,148.2 s (1,328.8 s in all), and the clock check failed the batch, as
    designed.
  - Leases are wall-clock times in the job table, so they expired while every process was
    suspended. The reconciler requeued W3 at its next pass, and again after B's attempt 2; B's
    renewal was refused, and the attempt was fenced and its tree ended.
  - One attempt was accepted, and nothing overlapped. W3's claim count and times describe the
    sleep, not the job system; W4 to X1 ran after the wake.
- **Preflight-4: W3 again, with the host awake.** It ran on `8c5331d` (power and swap recording), on
  AC power with the lid open, under `caffeinate -dims`, with no other containers or tests running.
  It passed validity: the clock check (wall minus monotonic 0.028 s over the batch, 4 of 4 process
  starts on one clock), Q1 `ok`, all 3 accepted results equal to the reference, no overlap, nothing
  left. The power log shows no sleep.

  | Case | Claims | Detection | Finish | D | Before the job | Paged out during it |
  |---|---|---|---|---|---|---|
  | C0 | 1 | — | 45.1 s | 75 s | AC, lid open, pressure 2, 1.71 GiB available | 5.0 MiB |
  | W3 | 2 | `requeued`, 59.1 s | 117.1 s | 140 s | AC, lid open, pressure 2, 1.74 GiB | 26.5 MiB |
  | C0 | 1 | — | 50.9 s | 75 s | AC, lid open, pressure 2, 1.48 GiB | 21.1 MiB |

  - **W3's ordinary path:** killed 3 s into spark_pipeline, then requeued 59.1 s after the kill,
    inside the predicted 50–65 s. Attempt 2 was accepted, and 6.4 s of step time was wasted.
  - **The controls:** the C0 jobs took 45.1 s before W3 and 50.9 s after it; their steps took
    42.8 and 48.4 s.
  - **Over the batch:** AC power and the lid open throughout. Memory pressure was 2 (warning)
    before every job and 1 at the end, with 1.36–1.93 GiB available. Swap in use grew from 4.21 to
    5.03 GiB; 4.4 GiB was paged in and 67 MiB paged out.

  These are recovery times observed on this host in that recorded state, next to controls measured
  in the same batch. They are not performance claims (section 12).
- **Native processes, informational:** across preflight-2 and -3 the step trees peaked at 0.09–0.12
  GiB (windows), 0.62–0.88 GiB (spark_pipeline) and 0.42–0.54 GiB (verify), one step at a time
  under the host lock. The C0 jobs' steps took 44.3–50.4 s in preflight-2 and -3 (and 42.8–48.4 s
  in preflight-4), against the 35.1 s M2 measured, itself under host memory pressure; T was about
  2 s more than the steps.

## 12. A protocol for recovery batches on this 8 GiB Mac

**What is and is not established.**
- **M2's isolated check** validated the containers' memory limits (MySQL 512 MiB, Kafka 640 MiB),
  under host memory pressure and with documented sampling limits.
- **Its 5 GiB and 4.0 GiB figures** were the gates of that check. They were never established as
  requirements for recovery experiments.
- **Its step times** (35.1 s for the calendar-year job) were also measured under host memory
  pressure.
- **Native-process memory** (workers, launchers, the Spark driver and JVM, the reconciler, the
  harness) is unvalidated.

None of these is used here as a validated standard. This draft earlier proposed a 2.5 GiB minimum
before each job; nothing measured ties that figure, or any other, to unchanged recovery behaviour on
this host, so it is withdrawn. Every live run so far had 1.2–1.9 GiB available and swap in use;
preflight-4, the first batch to record macOS's pressure level, had it at warning before every job.

**The protocol, for every batch, preflight or formal:**
1. **AC power throughout.** Checked before the start with `pmset -g batt`, and recorded in every
   host reading. A reading on battery, or a missing one, fails the batch for timing.
2. **Lid open throughout.** Checked before the start with `ioreg`, and recorded
   (`AppleClamshellState`) in every reading. A closed reading, or a missing one, fails the batch for
   timing.
3. **Sleep prevented.** The batch runs under `caffeinate -dims`, whose `-s` holds on AC power only.
   The clock check (1 s) detects any sleep that happens anyway and fails validity, as it did for
   preflight-3.
4. **No competing tests.** The exclusive window; no other containers (counted at the start); no
   other pytest, Spark or job processes (`pgrep` before the start, section 7).
5. **Memory pressure, swap in use and paging recorded, never gated.** Available memory, swap in
   use, the bytes paged in and out (psutil's `sin` and `sout`, recorded as `swap_in_bytes` and
   `swap_out_bytes`), and macOS's pressure level, at the start, before each job and at the end
   (`8c5331d`). Each job gets the bytes paged out in its window, and the batch its totals.
6. **Controls in the same batch.** C0 jobs measured in the same batch, under the same recorded host
   state: the two shuffled C0s, plus one C0 at the start and one at the end (approved on 2026-10-24;
   30 jobs, about 2 minutes more). Each case's times are reported next to these controls, for
   example its overhead over their median, rather than next to any external figure.
7. **Every outcome kept.** A batch that fails conditions 1–3, or lacks the readings to show them,
   stays invalid for timing and is never relabelled.

**Three kinds of claim.**

| Claim | Made from | Example |
|---|---|---|
| **Correctness** (E1): one accepted result per job, no overlapping steps, fencing, Q1 and Q3, accepted results equal to the reference, invariants | any batch whose checks that do not involve time pass: code identity, unchanged inputs, equal fingerprints, complete records. From a batch invalid for timing, they are kept as that batch's correctness observations, labelled as such (preflight-3) | "W3 kept one accepted result and no overlap across a 22-min host sleep" |
| **Recovery times observed on this host** (E2) | only batches that meet conditions 1–4 and whose recovery-times verdict is valid (the clock check, power and lid included); reported with the batch's host record and its controls | "W3: requeued 59.1 s after the kill, finished in 117.1 s; the controls took 45.1 and 50.9 s; pressure 2, 26.5 MiB paged out during the job" (preflight-4) |
| **Performance claims**: recovery time as a property of the job system, comparable across machines or usable as a prediction | not made from this host | — |

- **Why the line falls there.**
  - Correctness rests on the job table's token guards, fencing and the host lock, which do not
    depend on time or memory: every job that ran kept it (preflights 2–4), under memory pressure and
    across a sleep.
  - The observed times on this host depend on its memory state. They are taken with swap in use and
    pressure at warning, so they say how this machine recovered in that recorded state, and the
    controls show how fast it ran a job at the same time.
  - A performance claim would need what this host lacks: validated native-process budgets, and a
    memory state that does not swap.
- **The approved use of this host.** On 2026-10-24 the author approved this host's recorded memory
  state for correctness observations and for recovery times observed under its recorded
  conditions, with the limitations above. Performance claims stay out of scope.
- **Tooling, all implemented:**
  - Conditions 1, 2 and 5: power, lid, memory pressure and swap recorded at every reading
    (`8c5331d`).
  - Condition 6: the harness's default plan puts a C0 control at each end (`5a81bc5`).
  - The collector's verdicts (`5a81bc5`):
    - correctness observations rest on code identity, unchanged inputs, equal fingerprints and
      complete records;
    - recovery times also need the clock check and conditions 1 and 2 at every reading the batch
      needs (start, each job that ran, end);
    - a reading on battery or with the lid closed fails;
    - a missing reading, or one without the value, is unknown, and unknown fails.
  - The exit status is 0 only when both verdicts are valid, so a required check that failed, has no
    result or is missing exits 1, and the summary marks the unknown ones (`fcaa645`).
  - `injections.csv` gives each job its power, lid, pressure and the bytes paged out during it
    (the column `swap_out_during_bytes`, named before the correction of 2026-10-26).

## 13. After approval (2026-10-25)

_Added after the formal batches. Sections 1–12 are unchanged as approved, except the wording
corrected on 2026-10-26. The items dated 2026-10-27 change the tooling and condition 4's
monitoring, at the author's decision._

- **The formal batches.** batch-1 stopped when the host restarted. batch-2, the one rerun of
  row 11, completed. The author kept batch-2's correctness observations valid and ruled its
  recovery times invalid, because another project's container broke the exclusive window
  (condition 4). The results are in [recovery-part-b.md](recovery-part-b.md).
- **Condition 4's containers.** As approved, other containers were counted at a batch's start only.
  Since `5ecde71` the harness also records the count at every host reading, and the collector
  fails recovery times on any such container. The count is a sample: a container that starts and
  stops between two readings is not seen.
- **Earlier batches under the later collector.** No batch before `5ecde71` recorded the count, so
  the later collector reports `other_containers` as unknown for all of them. Their recovery times
  come out invalid, preflight-4's for that reason alone; their correctness verdicts are unchanged.
  An unknown count is insufficient evidence for condition 4, not evidence of a violation. The
  verdicts in section 11 are those of the collector at `5a81bc5`, as labelled there.
- **The page counters (2026-10-26).** psutil's `sin` and `sout` are page-ins and page-outs on
  macOS, not swap traffic ([host-counters-correction.md](host-counters-correction.md)). At the
  author's instruction, these passages were reworded with their figures unchanged:
  - section 11: the line on what entered the batch records, preflight-4's column "Swapped out
    during it" (now "Paged out during it"), and "4.4 GiB was swapped in and 67 MiB swapped out"
    (now paged);
  - section 12: condition 5, the example "26.5 MiB swapped out during the job" (now paged out),
    and what `injections.csv` gives each job.

  Swap in use and its figures are unchanged. No condition gated on these counters, so no verdict
  changes. The harness and the collector keep the names `swap_in_bytes`, `swap_out_bytes` and
  `swap_out_during_bytes`, so that they match the records.
- **The counters renamed in the code (2026-10-27, the author's decision).** New readings record
  `vm_stat`'s page-in, page-out, swap-in and swap-out counters by their own names, and the
  collector's columns are renamed to match. Older records' `swap_in_bytes` and `swap_out_bytes`
  are read as page counts, and their swap traffic as not recorded
  ([host-counters-correction.md](host-counters-correction.md), section 7). No record changes.
- **Condition 4 over the whole batch (2026-10-27, the author's decision).**
  - **The monitor.** The harness runs `docker events` from the batch's start to its end
    (`containers.jsonl`: time, the action's verb only, and whether a container is this project's; never a name
    or a command).
  - **The rule.** Any event of another project's container in that time, the gaps between readings
    included, fails the recovery-times verdict for the whole batch. A monitor that is missing or
    failed gives unknown, which fails too. This closes the gap noted above: the count at the
    readings remains, but it is no longer the only check.
  - **Earlier batches** have no monitor record, so this check is unknown for them. Their recorded
    verdicts stand as collected.
- **Sleep and wake evidence (2026-10-27).** At its end, a batch records the Sleep, Wake and
  DarkWake entries of `pmset -g log` during the batch: their times and kinds, never the reasons.
  It also records whether the log reaches back to the batch's start. The evidence is reported
  beside the clock and lid checks, never as a gate, and a batch without it says so.
