# Shuffle-partition experiment

**Part A: the design, the code and the predictions, committed before any measured run.** The
author approved the predictions (section 11) and the rules listed in 1.2 on 2026-10-19, and runs
the formal measurements (2.4, 4.4). No formal measurement has been made yet; the code was validated
on a small window set (4.5). Part B (results and answers) will follow section 13. The history of
this document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-19 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the stride experiment's records. Everything not listed in
1.2 is Claude Code's proposal (section 13). The predictions in section 11 were drafted with Claude
Code and reviewed and approved by the author. Revision 1 applied a read-only review of the first
draft by a separate Claude Code session (036c80c6). Revision 2 applied the author's decisions of
the same day and described the implemented code. Revision 3 recorded the fixes from Claude Code's
review of that code (history at the end). The author's own authorship line is still to be added._

This experiment changes neither the stride experiment ([experiments.md](experiments.md)) nor its
predictions, records or collector. It writes only under `data/outputs-partitions/`.

## 1. Question and decisions

### 1.1 Question

For a fixed workload, how do the requested number of shuffle partitions and AQE's partition
coalescing change runtime and peak memory, and do they change any result? This is the partitioning
part of research question 3 (spec §2). The data, model, window set, leverages, code and all other
Spark settings stay fixed. The machine is the stride experiment's (Apple M2 MacBook Air, 8 cores,
8 GiB RAM).

### 1.2 Decided by the author (2026-10-19)

- Three configurations, A, B and C (2.1), with AQE enabled in all of them.
- The stride-7 window set of the stride experiment as the only workload (2.2).
- Order A–B–C–C–B–A, with four fresh-process runs per protocol: one warm-up, three measured, so
  24 runs in all (2.3).
- Source and dependency hashes match across all new runs, and the input checksums are verified.
  The new code hashes need not match the code that built the window set (3.1, 10).
- One set of failure and retry rules (3.4). A code fix starts a new batch (3.1).
- Settings are verified through the recorded configuration and the execution plans (6), and
  finality is required only of adaptive plans. Task counts are observations, not pass/fail
  criteria (5).
- The timing metric (5) and the handling of plan-capture failures (3.4, 4.2) are defined here.
- `paired` and `path_summary` of every run are compared with A by their full keys: missing and
  duplicate keys, row counts, NULLs, breach flags, and numeric values within an explicit
  tolerance (7).
- Deferred: other configurations and extensive diagnostic tooling (12).
- Claude Code writes the engineering code and tests; the author reviews the results and runs the
  formal measurements.
- Approved after review:
  - the predictions of section 11, drafted with Claude Code, with B's assumed task and file costs
    labeled as assumptions;
  - `wall_excl_capture_s` as the primary timing metric, with the raw `wall_s` reported alongside
    (5);
  - the load-average limit of 4.0 and the 30-minute wait after a boot (3.2);
  - the batch and retry rules (3.1, 3.4).
- The abort limits apply to the watcher's raw elapsed time, plan capture included: about 77 s for
  A and C, and 99 s for B (11).
- File counts are predictions, not proof of actual partition counts (11).
- The branch is `feature/shuffle-partitions`, created from the stride close-out commit `516b28a`
  (3.5).

## 2. Configurations, workload and order

### 2.1 Configurations

| Configuration | `spark.sql.shuffle.partitions` | `spark.sql.adaptive.enabled` | `spark.sql.adaptive.coalescePartitions.enabled` | Role |
| --- | ---: | --- | --- | --- |
| A | 200 | `true` | `true` | Spark's default values, set explicitly (2.4); the stride experiment left them unset |
| B | 200 | `true` | `false` | the same requested count, not coalesced |
| C | 8 | `true` | `false` | one partition per core (`default_parallelism` is 8), not coalesced |

All other settings are the pipeline's (`local[*]`, UI off, UTC session time zone) and Spark's
defaults. Because AQE stays enabled, its other runtime rules still apply in B and C. For example,
it can turn a sort-merge join into a broadcast join and then read that shuffle locally. Only
coalescing is switched off.

A against B shows what coalescing does with 200 requested partitions. B against C shows what the
requested count does without coalescing. A against C compares Spark's defaults with an explicit
small count.

### 2.2 Workload

The workload is the stride-7 set in `data/windows-experiments/full-2026-10-12/rolling-252-s7`,
unchanged: 5,364 windows and 1,351,728 window-member rows (experiments.md 2.2). Its runs in the
stride experiment wrote 2,698,866 path-day rows. It is the largest workload the stride experiment
admitted. Each run verifies seven SHA-256 values recorded in its `config.json` before Spark starts:
`windows.parquet`, the five daily-return files and `quality_report.json`. On any mismatch it exits
with code 3.

### 2.3 Order and repeats

There are six protocols, at positions 1 to 6: A, B, C, C, B, A. Each protocol is one
`etf_risk.measure` call with `--repeats 4`: four fresh-process runs, the first of them a warm-up.
`measure` summarizes the three measured runs that ended `ok`. Each configuration therefore has two
protocols, eight runs and six measured runs.

Each configuration's two positions average 3.5. If the protocols were evenly spaced in time, a
drift that changes linearly over the session would shift each configuration's mean by the same
amount, and its median approximately so. The spacing is not exactly even: the pauses are fixed, but
the protocols differ in length, so their start times are reported. A's two protocols span the
session (positions 1 and 6); C's run back to back (3 and 4). Section 9 shows why a linear drift
alone cannot produce a difference under its rule.

### 2.4 Commands and records

The session helpers (4.4) start each protocol by its position: `position 3` runs configuration C.
The command they run, from the repository root, is

```bash
caffeinate -i uv run --group measure python -m etf_risk.measure --repeats 4 -- \
    --windows data/windows-experiments/full-2026-10-12/rolling-252-s7 \
    --out-root data/outputs-partitions/<batch>/<A|B|C> \
    --shuffle-partitions <200|8> --coalesce <on|off> --record-plans
```

All three configurations pass all three flags, A as `--shuffle-partitions 200 --coalesce on`, so
they run the same code path and pay the same plan-capture cost. A batch (3.1) is one folder,
`data/outputs-partitions/<batch>/`, starting with `batch-1`. It holds:

- `A/`, `B/` and `C/`, each with `full-2026-10-12/rolling-252-s7/`: one `protocol-<UTC time>.json`
  per protocol, and one folder and one `.log` per run. Each configuration's two protocols share a
  folder.
- `positions.tsv`, the position of every protocol the helpers ran (3.3), and `run-log.txt`, the
  session's checks and notes.
- `measurements.csv` and `acceptance.json`, written by the collector (4.3).

Nothing is written under `data/outputs/` or `data/outputs-experiments/`.

### 2.5 Earlier records with A's settings

The stride experiment's stride-7 protocol `20261019T035809Z` ran this workload with A's values
(unset, so Spark's defaults) at commit `0e3c130`, without plan capture:

- median wall time 25.660 s (24.699–26.001 s);
- median peak total RSS 2.705 GiB, and 2.681–2.714 GiB over all four runs;
- in all four runs, summed stage task counts (5) of 53, 22, 81 and 100 in the phases
  `window_stats`, `model`, `summaries` and `checks`;
- in all four runs, 1, 40, 8 and 1 files written in `window_stats`, `path_days`, `path_summary` and
  `paired`.

These are earlier records under an older code state. They are used only descriptively (section 8,
item 5).

## 3. Run conditions, batches and failures

### 3.1 Code state and batches

- A **batch** is one A–B–C–C–B–A sequence, run in one session under one code state.
- Within a batch, every protocol JSON (`code`) and every `run.json` (`code`) records the same
  `source_sha256` and `uv_lock_sha256`, with `git_worktree_clean: true` for the hashed paths
  (`src/`, `pyproject.toml`, `uv.lock`).
- The commit is recorded but need not match: a commit that touches none of the hashed paths, such
  as one of this document, leaves the hashes unchanged. The collector reports the commits it finds.
- The new code state is not compared with `windows_config.code`, the code that built the window set
  (`a7fb72d`). The window set itself must be unchanged (10, criterion 2).
- Any change to `src/`, `pyproject.toml` or `uv.lock`, such as a code fix after a failure, ends
  the batch. The fix is committed, and a new batch (`batch-2`, ...) starts at position 1. Earlier
  batches are kept and reported, never mixed with a later one.
- Before the first measured run, the code of section 4 with its tests, this document and the
  author's predictions are committed.

### 3.2 Machine state before each protocol

The conditions of experiments.md 3.2 apply:

- Low Power Mode off and mains power;
- Docker Desktop, VS Code and other apps quit;
- a 5-minute pause;
- at least 3.0 GiB available just before the start.

Added, from the stride experiment's run log (experiments.md 5.2, 5.3):

- No protocol starts within 30 minutes of a boot.
- The 5-minute load average, read just before the start, is at most 4.0.
- After any app is quit, the checks are repeated, so the run log shows the state at the start.

The helpers' `prechecks` writes the checks into the run log, and `ready` reads the available
memory, the load average and the time since boot just before a start (4.4).

### 3.3 Positions

`position n` runs the protocol at position n and then appends a line to `positions.tsv`: the
position, the configuration, the protocol id that `measure` wrote, `measure`'s exit status, the
result of the plans check, and the time. The collector takes the positions from this file. It
checks them against each protocol's folder, recorded settings and start time, and against the
order of 2.3. The **used protocol** at a position is the last one run there.

### 3.4 Failures and retries

One rule set for every stop. A stop always means: keep every record, write the reason into the run
log, and come back to Claude Code before anything else runs.

| Event | Detected by | Then |
| --- | --- | --- |
| `ready` finds too little memory, a high load average or a recent boot | `ready` | The protocol does not start. This is not a failure: wait, then read again. |
| A run's raw elapsed time, plan capture included, passes its configuration's abort limit (11: 77 s for A and C, 99 s for B) | the watcher, which says ABOVE THE LIMIT | Abort it with `abort_run`, which kills only the pipeline process; the run ends `failed`. |
| A run ends `failed` (crash, kill, abort) or `memory_threshold_exceeded` | `measure` stops the protocol | Stop. One re-run of that position, in the same session and with the same code, after the 3.2 checks and the pause. |
| A run's plan capture failed (4.2) | the plans check after the protocol | Stop. As for `failed`: one re-run of that position. |
| A run ends `checks_failed` | `measure` stops the protocol | Stop. The batch ends; the cause is investigated before anything else runs. |
| The cause of a stop needs a change to `src/`, `pyproject.toml` or `uv.lock` | the investigation | The batch ends. The fix is committed, and a new batch starts at position 1 (3.1). |
| A re-run stops again, or the batch cannot continue the same day | — | The batch ends; a new batch starts at position 1. |

A batch that ended early is kept and reported but not analyzed. Only the first complete batch that
meets every acceptance criterion (10) is analyzed, and no further batch runs after it. `measure`'s
stop rule is unchanged: 60% of physical RAM, 4.80 GiB. The commands of experiments.md 3.6 are not
pasted. Pasted with its `#` comment, that line matched about 68 unrelated processes in the author's
zsh on 2026-10-18, because `interactivecomments` is off; `abort_run` replaces it.

### 3.5 Prerequisites and branch

- The stride experiment's Part B, its collector and the README and spec updates were committed on
  2026-10-19 (`6d19f1b`, `05c5a79`, `516b28a`), so the sections of experiments.md this document
  cites are committed.
- Branch: `feature/shuffle-partitions`, created from the stride close-out commit `516b28a`. Both
  `feature/experiments` and this branch are later merged into `main` with merge commits, never
  squashed or rebased, so that the commit of the formal runs stays in `main`'s history.

## 4. Code

### 4.1 Pipeline flags

`etf_risk.spark_pipeline` has three new flags. Without them, a run and its records are as before,
apart from the code state.

- `--shuffle-partitions N` (an integer of at least 1) sets `spark.sql.shuffle.partitions`.
- `--coalesce on|off` sets `spark.sql.adaptive.coalescePartitions.enabled`.
- `--record-plans` writes `plans.json` (4.2).

When any flag is given, `run.json` records them under `pipeline_options`. PySpark applies a session
builder's options to an existing session (`applyModifiableSettings` in `pyspark/sql/session.py`).
So inside an existing session, as in the tests (one `local[2]` session with 4 shuffle partitions,
`tests/conftest.py:40`), the pipeline refuses the first two flags with exit code 2 and starts
nothing. `measure` always starts a fresh process.

### 4.2 Execution plans and partition counts

With `--record-plans`, the module `etf_risk.plans` reads Spark's SQL status store through the JVM
gateway. That is an internal interface; the calls were checked on Spark 4.2.0, which `plans.json`
records. The capture has two steps:

1. Just after the session starts, the pipeline waits until Spark's listener bus has delivered every
   event, then reads the highest SQL execution id so far (the watermark). Only later executions are
   this run's. In a fresh process the watermark is −1; in the tests' shared session it excludes
   earlier tests' queries.
2. After the run's status and exit code are set, the pipeline waits for the listener bus again. It
   then waits until every execution of the run has finished and every adaptive plan (one with an
   `AdaptiveSparkPlan` node) is final (`isFinalPlan=true`), for at most 60 s. Plans that are not
   adaptive have no finality to wait for.

`plans.json` holds the format version, the Spark version, `spark.sql.ui.explainMode` (the format
of the plan text; Spark 4.2.0 reports `FORMATTED`), the first execution id, and for every SQL
execution of the run:

- its id and jobs, and its phase: the job group of its jobs, that is `window_stats`, `model`,
  `summaries` or `checks`, or `bookkeeping` for the row counts after the timed phases. An
  execution without jobs has an empty phase; in the validation (4.5) that was the one execution
  that only creates the pairing step's temporary view (`CreateViewCommand`), which is not adaptive;
- its error message (none when it succeeded), and whether it is adaptive and final;
- its final physical plan text;
- each shuffle exchange: its partitioning (`hashpartitioning`, `rangepartitioning` or a single
  partition) and requested count, from the plan graph's node description, and its runtime metrics,
  among them "number of partitions", the partitions it actually wrote;
- each shuffle read that AQE marks (an `AQEShuffleRead` node): its mark as Spark prints it (for
  example `coalesced` or `local`) and its metrics, among them "number of partitions", the
  partitions it actually read. A shuffle read without a mark has no such node: it reads all of its
  exchange's partitions, so its actual count is the exchange's runtime "number of partitions". A
  probe on a toy query showed this once: with coalescing off, its shuffle read had no
  `AQEShuffleRead` node and ran one task for each of the 50 partitions the exchange wrote.
- the joins in the plan (for example `BroadcastHashJoin`, `SortMergeJoin`).

**Capture failures.** Either step can fail: a listener timeout, an execution not finished or not
final in time, or an error from the gateway. The pipeline then deletes any partial `plans.json` and
records `plan_capture: {"status": "failed", "error": ...}` in `run.json`. The run's status and exit
code stay unchanged, so `measure` continues the protocol. The plans check after the protocol (4.4)
then stops the session, and 3.4 applies. A run without its plans fails criterion 3 (10). On success,
`run.json` records `plan_capture: {"status": "ok", "file": "plans.json", "executions": ...,
"first_execution_id": ...}`.

**Time.** Both steps together, waits included, are recorded as `timings_seconds.plan_capture`
(5). They fall inside `total_in_process` and `wall_s`, but outside every phase timing.

Spark's event log also holds plans and metrics, but it writes one record per task, so its cost
grows with the variable under test. It stays deferred (12).

### 4.3 Collector

`analysis/collect_partition_measurements.py` reads one batch folder (2.4) and writes into it:

- `measurements.csv`: one row per started run of every protocol in the batch, used or not. The
  columns are the identity (batch, position, configuration, whether used, protocol, run), the
  stride experiment's measurement columns (experiments.md 5.6), and these additions:
  - `coalesce_enabled`, `plan_capture_status`, `plan_capture_s` and `wall_excl_capture_s` (5);
  - the plan observations: SQL executions, adaptive plans, requested counts, coalesced and local
    reads, per phase the partitions each exchange wrote at runtime and the marked reads with their
    partition counts, and broadcast and sort-merge joins;
  - files written per output table, and the result of the comparisons with the reference (7).
- `acceptance.json`: each acceptance criterion (10) with every problem found, the used protocols,
  the reference run, the commits found, the largest floating-point difference per column, and the
  comparison with the stride experiment's run (7).

It prints a summary and exits with 1 if any criterion fails. With `--check-protocol <protocol
JSON> --config <A|B|C>`, it checks one protocol: every run captured its plans, and every run's
recorded settings and plans match the configuration (6). The helpers run it after each protocol, so
a wrong setting stops the session at once, not after the batch. It imports the stride collector's
column definitions but leaves that script, the stride records and the stride CSV unchanged.

### 4.4 Session helpers

`docs/partition-session.zsh` is a new file. `docs/stride-session.zsh` stays unchanged, since
experiments.md 5.2 cites it by hash. The helpers find the repository from their own path. Their
functions:

- `steps`: the checklist.
- `prechecks`: the 3.2 checks, including the time since boot, written into the run log.
- `pause5`: the 5-minute pause.
- `ready`: memory at least 3.0 GiB, load average at most `PART_LOAD_MAX`, booted at least
  `PART_BOOT_MIN` minutes ago.
- `position n`: runs the protocol at position n, then the check of its plans and settings
  (`--check-protocol` with the position's configuration) and the `positions.tsv` line. It prints
  `STOP` when `measure` stopped early or the check failed.
- `where`: the positions run so far.
- `watch_runs`: every 10 s, each running pipeline's configuration and raw elapsed time with its
  abort limit (11). It says ABOVE THE LIMIT when a run passes the limit.
- `abort_run`, `after_abort` and `note`: as in the stride session.

Variables set before loading choose the batch (`BATCH`) and the limits (`PART_LOAD_MAX`,
`PART_BOOT_MIN`). `PART_WINDOWS`, `PART_ROOT` and `PART_REPEATS` exist only for a dry run on other
data.

### 4.5 Tests and validation

**Tests.** `tests/test_partition_options.py` has 9 tests:

- the flags' defaults and rejected values, and the plan-text parsers;
- in the shared session:
  - the refusal of the partition flags;
  - unchanged records without the new flags;
  - plans limited to the run's own executions, with the plan capture's timing outside the
    unchanged phase timings;
  - a forced capture failure that leaves the status and exit code unchanged;
- in fresh processes:
  - Spark's defaults without flags;
  - 8 partitions without coalescing, with no read marked `coalesced`;
  - 200 partitions with coalescing, where coalesced reads record partition counts below 200.

  In each fresh process, every exchange's runtime partition count equals the requested count.

`tests/test_partition_collector.py` has 37 tests without Spark. They cover:

- every kind of difference in section 7;
- the plan checks, including runtime partition counts, and the code-state checks;
- a complete fake batch, and a re-run that replaces a failed protocol;
- planted problems for criteria 1, 3, 4 and 5, and changed inputs;
- the check after a protocol, with and without a configuration.

`tests/test_partition_session.py` has 8 tests of the helpers in zsh:

- the file parses;
- loading sets the order and flags and changes into the repository;
- `position` refuses numbers outside 1 to 6;
- the watcher converts elapsed times to seconds and finds each configuration's abort limit;
- `ready` passes only when the memory, load and boot limits are all met.

**Validation on a small window set.** Two dry batches, neither a formal measurement:

- The first ran on 2026-10-19 with the code of revision 2. The second ran from 00:42 to 00:49 UTC
  on 2026-10-20 with the code of revision 3, which is the committed code apart from the watcher's
  abort limits. Those were added afterwards and are covered by the helper tests.
- Both used a rolling stride-252 set of 151 windows, built from the same snapshot in a scratch
  folder.
- The helpers ran with `PART_REPEATS=2`, so one warm-up and one measured run per protocol.
- Other work ran on the machine during the first batch, so the times of both are not comparable
  and are not reported here.

What they showed, in both batches unless stated:

- **Helpers.** They ran positions 1 to 6 in the A–B–C–C–B–A order and wrote `positions.tsv`.
  Every check after a protocol passed; in the second batch, that check covered settings and plans
  against the position's configuration.
- **Plan capture.** Every run captured all 25 SQL executions of its process (ids 0 to 24, no gaps)
  in 1.02–3.30 s. The 24 adaptive plans were all final. The 25th execution is the
  `CreateViewCommand` of 4.2: not adaptive, without jobs. No execution recorded an error. The
  explain mode read back as `FORMATTED`. `plans.json` was about 0.3 MB per run.
- **Exchanges.** All 11 hash exchanges of every run requested the configuration's count: 200 in A
  and B, 8 in C. There were five in `window_stats`, two in `model`, four in `summaries` and none in
  `checks`. In the second batch, every exchange's runtime partition count equaled its requested
  count.
- **Reads.** In A, 10 shuffle reads were marked `coalesced`, each with its partition count (1 or 5
  on this small set). In B and C, no read was marked `coalesced`. Every run had one read marked
  `local`, with 1, 200 and 8 partitions in A, B and C.
- **Files written.** In `window_stats`, `path_days`, `path_summary` and `paired`: 1, 5, 1 and 1 in
  A; 110, 140, 154 and 110 in B; 8, 40, 8 and 8 in C.
- **Collector.** It found criteria 2 to 5 met. Criterion 1 failed, as it should have: the code was
  not committed yet, so all 18 records show uncommitted changes in the hashed paths, although all
  runs share the same hashes.
- **Output comparison.** Against the reference, 12 of the 28 floating-point columns differed in the
  last bits. The largest relative difference was 4.1e-12 (`approx_rel_error`); in the other 11 it
  was at most 1.8e-15. All were far inside the tolerance. Every key, NULL, breach field and other
  column matched exactly.

## 5. Measurements

| Group | Values | From |
| --- | --- | --- |
| Time | `wall_s`; the phases `session_start`, `window_stats_and_construction_check`, `model_and_path_days`, `summaries_and_pairing`, `checks`, `total_in_process`; `plan_capture` | `measure`; `timings_seconds` in `run.json` |
| Memory | free memory before the run; peak RSS in total and per process type; samples; processes seen; threshold crossing | `measure` |
| Configuration | recorded Spark settings, `pipeline_options` and environment | `run.json` |
| Execution plans | see 4.2 | `plans.json` |
| Results | status, check violations, row counts; the `paired` and `path_summary` tables | `run.json`, `checks.json`, run folder |
| Provenance | code state, verified input checksums, window config | `run.json`, protocol JSON |
| Run conditions | the 3.2 checks, boot time, load average, pauses, memory readings, positions, deviations | run log, `positions.tsv` |

**Timing metric.** The time compared between configurations is
`wall_excl_capture_s = wall_s − plan_capture_s`:

- `wall_s` is `measure`'s clock, from starting the pipeline process to its exit.
- `plan_capture_s` is the plan recording's own time (4.2).

Plan recording is instrumentation, not part of the workload, and its waits depend on Spark's
listener bus. The medians and min–max of section 5, the drift rules (8) and the comparison rule (9)
all use `wall_excl_capture_s`; `wall_s` and `plan_capture_s` are reported next to it. The stride
experiment's runs had no plan recording, so for them `wall_excl_capture_s` equals `wall_s`. The
phase timings never include the plan recording.

Reported as observations, never as pass/fail criteria:

- Summed stage task counts per phase (`stage_task_counts`): the sum of `numTasks` over the stages
  that each job of the phase lists. A stage listed by two jobs counts twice, for example a shuffle
  stage that a later job lists as skipped. The sum need not equal the number of tasks that ran;
  whether that happens here has not been checked.
- Files written per output table, counted in each run folder.
- From the plans: per phase, the partitions each exchange wrote at runtime and the partition count
  of each marked shuffle read (in A, the counts after coalescing); the reads marked `local` or
  `skewed`; and the joins.

Summaries use the measured runs that ended `ok` in the used protocols (3.3), as experiments.md 3.7
does. They give medians and min–max of `wall_excl_capture_s`, the phases and peak total RSS, per
protocol and per configuration (six runs). The memory statistic is the median of
`peak_rss_total_bytes` over the measured runs. The largest value over all runs, warm-ups included,
is reported next to it.

Recorded in `plans.json` but not analyzed: the exchanges' and reads' size and shuffle metrics,
such as data size and partition data size. Not measured (12): spill, CPU time and GC time.

## 6. Settings verification

Each run of the used protocols is checked against its configuration in two ways.

1. **Recorded configuration.** The `spark` section of `run.json` shows the configuration's three
   values (2.1), and `pipeline_options` shows the flags of 2.4. Every other recorded Spark setting,
   and the recorded environment, are identical in all used runs. Any difference from the stride
   experiment's stride-7 run, apart from the varied settings, is reported.
2. **Execution plans** (`plans.json`):
   1. The capture succeeded. The file records Spark 4.2.0 and the explain mode `formatted` (in any
      letter case), and covers every SQL execution of the process: ids 0 to n−1, without gaps.
   2. No execution ended with an error. Every adaptive plan is final; finality is not required of
      plans that are not adaptive.
   3. Every hash- or range-partitioning exchange uses the configuration's count: 200 in A and B, 8
      in C. The collector reads the requested counts from the exchange entries and, separately,
      from the plan text's `Arguments: hashpartitioning(…, n)` lines. It also checks that each such
      exchange's runtime "number of partitions" equals the count.
   4. In B and C, no shuffle read is marked `coalesced`, whether alone or with `skewed`. The
      collector checks the read entries and, separately, the plan text.
   5. In A, the coalesced reads and their partition counts are reported. Whether and where AQE
      coalesces is an outcome, not a setting.

Items 1 and 2.1–2.4 are pass/fail criteria (10, criterion 3). Item 2.5, the partition counts and
the task counts are observations.

## 7. Output comparison with A

**Reference:** run 2 of the used protocol at position 1 (3.3), the first measured run of A. Every
other run of the used protocols is compared with it, warm-ups included (23 runs). The runs of
protocols replaced by a re-run are compared as well and reported.

Run 2 of the stride experiment's stride-7 protocol is compared too. It used A's values with the
earlier code, so it shows whether the code of section 4 alters these two tables beyond the
tolerance. `path_days` and `window_stats` are compared by row count only, from `run.json`, for
every run. Tables are read with PyArrow, which keeps null and NaN distinct.

| Table | Full key | Rows at stride 7 |
| --- | --- | ---: |
| `paired` | `window_kind`, `ticker`, `window_days`, `entry_date` | 5,364 |
| `path_summary` | `window_kind`, `ticker`, `window_days`, `entry_date`, `leverage` | 10,728 |

For each table, a run passes if all of these hold:

1. **Rows:** its row count equals the reference's.
2. **Keys:** no key column is null and no key occurs twice. The run and the reference have exactly
   the same keys, matched exactly, `leverage` included: none missing, none extra.
3. **Columns:** the same columns, with the same types.
4. **NULLs:** every column is null in exactly the same rows as in the reference, with rows matched
   by key.
5. **Breach fields** are equal exactly:
   - in `paired`: `breached_1x`, `breached_2x`, `breach_date_2x`, `breach_day_2x`, `last_ok_date_2x`
     and `days_ok_2x`;
   - in `path_summary`: `breached`, `n_breach_rows`, `breach_day`, `breach_date`, `last_ok_date` and
     `days_ok`.
6. **Other non-floating columns:** every other string, date, integer and boolean column is equal
   exactly.
7. **Floating-point columns other than the keys:** each value x satisfies
   `|x − r| ≤ 1e-12 + 1e-9 × |r|`, where r is the reference value, and NaN matches only NaN. The
   largest absolute and relative difference per column is reported, even when the run passes.

The tolerance is the pipeline's own tolerance for the 1x identity (`RTOL` = 1e-9, `ATOL` = 1e-12).
Spark may add the terms of a sum or average in an order that depends on partitioning, which can
change the last bits; the reported differences show how far below the tolerance they stay. On the
stride experiment's records, the comparison of two stride-7 runs (runs 2 and 3 of
`20261019T035809Z`) found no problem and no difference in either table.

## 8. Drift rules

All rules use `wall_excl_capture_s` (5).

1. **Session drift.** If A's protocol medians at positions 1 and 6 differ by more than 10% of the
   first, drift is reported and comparisons are marked as affected. Nothing is re-run silently.
   This is the rule of experiments.md 3.4.
2. **Pairs.** The same rule applies to B (positions 2 and 5) and C (3 and 4). The C pair runs back
   to back, so it shows the variation between protocols with little time for drift.
3. **Memory.** Pairs whose median peak total RSS differs by more than 0.2 GiB are reported.
4. **Context.** For each protocol, the start time, the free memory before each run, the load
   average and the time since boot are shown next to the pair differences. No rule applies to them.
5. **Earlier records.** A is compared with the stride experiment's stride-7 protocol (2.5)
   descriptively only, since the code state and the day differ.

Drift does not void the results. It is reported, and section 9 still applies.

## 9. Comparing configurations

For two configurations X and Y, using `wall_excl_capture_s`:

- d1 is the difference between their protocol medians in positions 1–3;
- d2 is the same difference in positions 4–6;
- d is the difference between the medians of their six measured runs.

Under a drift that changes linearly with position, d1 and d2 shift in opposite directions for every
pair: by one position step for A–B and for B–C, by two for A–C. A drift alone therefore gives d1
and d2 opposite signs, and the rules below never report it as a difference.

The rules:

- **Wall time.** X and Y differ if |d| is more than 10% of A's six-run median and d1, d2 and d have
  the same sign. Otherwise there is no clear difference.
- **Peak memory.** The same rule, with a threshold of 0.2 GiB on the median peak total RSS. That is
  just above the largest spread among the measured runs of one protocol in the stride experiment
  (0.185 GiB), the runs this statistic uses. Counting warm-ups, two protocols spread more (0.246
  and 0.223 GiB).
- **Phases** are described with d1, d2 and d, without a threshold.
- **Plans, partition counts, task counts and file counts** are described, not tested.

With two protocols per configuration, this is a descriptive rule, not a statistical test.

## 10. Acceptance criteria

The collector evaluates these for one batch (4.3). The batch's results are used only if all of them
hold:

1. **Code state:** every protocol JSON and `run.json` of the batch records the same
   `source_sha256` and `uv_lock_sha256`, with the hashed paths clean (3.1).
2. **Inputs:** each run's `verified_sha256` holds exactly the seven inputs of 2.2, each equal to the
   hash in the stride-7 `config.json`, and each run's `windows_config` equals that file. After the
   session, the seven hashes are computed once more and are unchanged.
3. **Settings:** section 6, items 1 and 2.1–2.4, hold for every run of the used protocols.
4. **Results:** every run of the used protocols ended `ok` with zero check violations. Section 7
   passes for every run of the used protocols and for the stride-experiment run.
5. **Completeness:** each of the six positions has a used protocol (3.3) of the configuration that
   2.3 puts there. It started 4 of 4 runs and all of them ended `ok`. None stopped early, none was
   aborted, and no sample exceeded 4.80 GiB. The used protocols ran in position order, and every
   protocol in the batch appears in `positions.tsv`.

If criterion 1, 2 or 3 fails, no configurations are compared until the cause is found. Stops and
re-runs follow 3.4. Drift (section 8) is not an acceptance criterion.

Run conditions are not an acceptance criterion either. A departure from 3.2 is recorded as a
deviation, and the protocol's results are labeled with it, as in experiments.md 5.3.

## 11. Predictions

_Drafted with Claude Code (Opus 5.5) from the earlier records and the mechanisms below; reviewed
and approved by the author on 2026-10-19, before any measured run. The dry batches of 4.5 were not
used: their window set differed, and the machine was busy during the first. The stride
experiment's predictions (experiments.md section 4) stay unchanged._

| | A: 200, coalescing on | B: 200, coalescing off | C: 8, coalescing off |
| --- | --- | --- | --- |
| Median `wall_excl_capture_s` | 25.7 s | 33 s | 25.7 s |
| Band: a median outside it contradicts the prediction | 20.5–30.8 s (±20%) | 26–53 s (−20% / +60%) | 20.5–30.8 s (±20%) |
| Peak total RSS, median of the measured runs (5); outside the range contradicts it | 2.5–2.9 GiB | 2.5–3.1 GiB | 2.5–2.9 GiB |
| Abort a run above, on the watcher's raw elapsed time, plan capture included (3.4) | 77 s | 99 s | 77 s |

The abort limits are three times the predicted medians, rounded: 3 × 25.7 s ≈ 77 s and 3 × 33 s =
99 s.

### 11.1 Expected plans

File counts are predictions, not proof of actual partition counts; the actual counts come from the
plans (4.2, 6). Files are listed for `window_stats`, `path_days`, `path_summary` and `paired`.

- **A.** Every hash exchange requests and writes 200 partitions. AQE coalesces most reads: the
  large ones to about 8 partitions, the small ones to 1. Where a join became a broadcast join, it
  may read a shuffle locally. Predicted files: 1, 40, 8 and 1. Predicted summed stage task counts:
  about 53, 22, 81 and 100. Both are as in the stride experiment's stride-7 runs.
- **B.** Every hash exchange requests and writes 200 partitions. No read is marked `coalesced`, so
  every unmarked read reads all 200. Predicted files: about 200, 1,000, 200 and 200. `path_days`
  has 200 write tasks × 5 tickers, a little fewer if a partition holds no window of some ticker.
  Summed stage task counts several times A's.
- **C.** Every hash exchange requests and writes 8 partitions. No read is marked `coalesced`.
  Predicted files: 8, 40, 8 and 8.

### 11.2 Expected comparisons (section 9)

- No clear difference between A and C.
- B slower than A and than C by more than 10%, in both halves of the order.
- No clear difference in peak memory between any two configurations.

### 11.3 Basis

- **A** is the stride experiment's stride-7 configuration (2.5). Its median was 25.660 s
  (24.699–26.001 s). Its median peak was 2.705 GiB: JVM 1.542, Python workers 1.047 and driver
  0.115 GiB. Its 40 `path_days` files are 8 write tasks × 5 tickers, so AQE coalesced the model
  stage's read to about 8 partitions.
- **±20%.** Within that protocol the runs spread −3.7% to +1.3% around the median. But in the
  stride experiment, the repeated stride-21 protocol's median was 18.3% below the first's
  (experiments.md 5.5).
- **C against A.** A's large reads already run about 8 partitions. C runs a few nearly empty extra
  tasks where A coalesced to 1, and its map tasks write 8 partitions instead of 200. The two
  effects are small and opposite.
- **B** has no earlier record with its settings, so its prediction rests on mechanisms and
  assumptions:
  - The code has about ten hash shuffles: its window function, aggregations and joins. Without
    coalescing, each is read with 200 tasks instead of at most 8, about 1,900 extra tasks in all.
  - It writes about 1,550 more output files, about 1,000 of them in `path_days`.
  - **Assumption:** each extra task or file costs 5–20 ms of scheduling, serialization and file
    handling, spread over 8 cores. That adds 2 to 9 s.
  - **Assumption:** reading about 1,000 small `path_days` files back in later phases adds 1 to 3 s.
  - Together: 29–37 s, with 33 s as the point. The band is skewed upward because the per-task and
    per-file costs are assumed, not measured.
- **Memory.** In the stride experiment, the median peaks barely changed while the work tripled:
  2.62–2.71 GiB at strides 21 to 7. The JVM and the 8 Python workers dominate them, and every
  configuration runs the model stage 8 tasks at a time. B's upper edge allows 0.2 GiB more for the
  JVM's bookkeeping of its extra tasks and files.
- **Caution.** Stage 2's stride-21 run took twice as long, with half the memory, under different
  machine conditions (experiments.md 6.4). If conditions differ again, all three medians may fall
  outside their bands together. The comparisons of section 9 are relative and less affected.

## 12. Deferred

- other partition counts, for example 2 or 32;
- running with AQE disabled;
- Spark's event log, and task counts per stage or de-duplicated by stage;
- analysis of the size and shuffle metrics that `plans.json` records; spill, CPU time and GC time;
- a full comparison of `path_days`;
- caching.

## 13. Origin of the design

The author's decisions and approvals are in 1.2. Everything else was proposed by Claude Code; the
author reviewed the drafts and the code and asked for this document to be committed as Part A.
Claude Code's proposals, by section:

- **2.3–2.4:** the drift reasoning; explicit flags in all three configurations; the batch folder
  layout.
- **3.1:** a batch as one sequence in one session; reporting commits instead of requiring one.
- **3.2:** repeating the checks after an app is quit.
- **3.3:** positions recorded by the helpers in `positions.tsv`; the last protocol at a position is
  used.
- **3.4:** the events and actions of the table, which the author approved as the batch and retry
  rules.
- **4.1–4.4:** the code:
  - the flag names, `pipeline_options`, and refusing the partition flags inside an existing session;
  - `etf_risk.plans` and the contents of `plans.json`, including the partition counts;
  - reading Spark's SQL status store, with the watermark, the waits and the 60 s limit;
  - the error handling, the collector and the helpers.

  Capturing the partition counts keeps the spec's statement that requested and actual partition
  counts are recorded (spec §4 and §8, expectation 5).
- **5:** the summary statistics and the observations.
- **6:** the plan checks, their cross-checks against the plan text and the runtime metrics, and
  which of them are pass/fail.
- **7:** the reference run, the exact and tolerance rules with their values, and the comparison with
  the stride experiment's stride-7 run.
- **8–9:** the drift and memory thresholds and the comparison rule.
- **10:** the set of acceptance criteria, and run conditions as labels instead of a criterion.
- **11:** the draft of the predictions, which the author approved.
- **12:** the contents of the deferred list.
- Part B in this file.

## History of this document

**Revision 1** (2026-10-19) applied the findings of a read-only review of the first draft by a
separate Claude Code session (036c80c6). Numbers are the review's.

| Finding | Change | Where |
| --- | --- | --- |
| 1. Actual partition counts were still not recorded, although the spec says they will be | the partition counts of marked shuffle reads are captured with the plans | 4.2, 5, 13 |
| 2. The planned tests would change the shared test session | the partition flags are refused inside an existing session; flag tests run in a separate process; the capture is limited to the run's own executions | 4.1, 4.2 |
| 3. Plan capture: stale plans, scope, error handling, plan format | wait for the listener bus and check for final plans; bookkeeping executions included and labeled; a capture error leaves status and exit code unchanged; the explain mode is recorded and checked | 4.2, 6 |
| 4. The re-run rule contradicted completeness; positions were not recorded | positions recorded; a re-run rule; used protocols; the reference taken from the used protocol | 3.3, 3.4, 7, 10 |
| 5. Every run's records would change | plan capture is opt-in (`--record-plans`); the timing metric excludes it | 2.4, 4.2, 5, 8 |
| 6. Section 13 did not list every proposal | section 13 lists them by section | 13 |
| 7. 0.185 GiB holds for measured runs only | stated, with the larger spreads that include warm-ups | 9 |
| 8. Criterion 10.6 could not fail | run conditions moved out of the criteria and used as labels | 10 |
| 9. Drift: medians and time spacing | qualified; start times reported | 2.3, 8, 9 |
| 10. Whether A passes the flags was unclear | A passes the default values explicitly | 2.1, 2.4 |
| 11. The tolerance covered the key `leverage`; the claim about code changes went too far | key columns matched exactly; the claim limited to the two tables | 7 |
| 12. Task counts may count a stage twice | described as summed stage task counts | 2.5, 5 |
| 13. Cited sections not committed; no branch named | prerequisites and a proposed branch | 3.5 |
| 14. Extending the stride collector was risky | a separate collector; the stride collector and CSV untouched | 4.3 |
| 15. The abort command fails in the author's zsh | an abort step in the new helpers | 3.4, 4.4 |

The review's 16th finding did not concern this document.

**Revision 2** (2026-10-19) applies the author's decisions of the same day:

- Code state: matching source and dependency hashes; the commit is only reported (3.1, 10).
- One table of failure and retry rules (3.4).
- A code fix, or any other change to the hashed paths, starts a new batch (3.1, 3.4).
- Finality is required only of adaptive plans (4.2, 6).
- The timing metric is defined as `wall_excl_capture_s` (5, 8, 9), and plan-capture failures are
  handled as in 4.2 and 3.4.

It also describes the implemented code: the batch folders, `positions.tsv`, `etf_risk.plans`, the
collector, the helpers, and the tests and validation (2.4, 3.3, 4).

**Revision 3** (2026-10-19) follows the author's review request for the implementation:

- Each exchange's runtime partition count is recorded and checked against the requested count, so
  the actual counts of unmarked reads in B and C rest on runtime data (4.2, 5, 6).
- The check after each protocol also verifies the protocol's settings and plans against its
  configuration (4.3, 4.4).
- The CSV gains per-phase runtime exchange counts (4.3).
- New tests cover the timing boundary of the plan capture and the helpers' gate (4.5).
- The small-dataset validation was repeated with the final code (4.5).

**Part A** (2026-10-19). The author approved the predictions and the rules listed in 1.2.

- Section 11 was written from the approved worksheet.
- The abort limits were added to the helpers' checklist and watcher (4.4).
- Section 13 now lists Claude Code's proposals.

This version is committed before any measured run, together with the code of section 4, on
`feature/shuffle-partitions`.
