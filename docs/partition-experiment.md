# Shuffle-partition experiment

**Part A (sections 1–13): the design, the code and the predictions, committed before any measured
run (`caa0be1`).** The author approved the predictions (section 11) and the rules listed in 1.2 on
2026-10-19 and ran the formal measurements (2.4, 4.4). **Part B (sections 14–15): the results of
batch-1, run on 2026-10-22 (UTC), and the author's answers.** Batch-1 met every acceptance
criterion (10), so it is the analyzed batch, and no further batch runs (3.4). Sections 1–13, the
predictions included, are unchanged since Part A. The history of this document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-19 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the stride experiment's records. Everything not listed in
1.2 is Claude Code's proposal (section 13). The predictions in section 11 were drafted with Claude
Code and reviewed and approved by the author. Revision 1 applied a read-only review of the first
draft by a separate Claude Code session (036c80c6). Revision 2 applied the author's decisions of
the same day and described the implemented code. Revision 3 recorded the fixes from Claude Code's
review of that code (history at the end). Part B was drafted with Claude Code from batch-1's
records, with the author's statements and answers (sections 14 and 15). The author's own authorship
line is still to be added._

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

_Part A ends here; it was committed before any measured run (`caa0be1`)._

## 14. Results

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from batch-1's run log and `positions.tsv`, the
six protocol JSONs, the 24 `run.json` and `plans.json` files, `measurements.csv` and
`acceptance.json` (numbers read by script), the author's terminal output from both windows, and the
author's statements (14.3). Times are UTC: the session ran from 23:10 on 2026-10-21 to 03:12 on
2026-10-22. Differences and percentages are computed from unrounded values, so they can differ by
0.001 from those of the rounded values shown. This section gives facts only; the answers are in
section 15._

### 14.1 Protocols

| Position | Configuration | Protocol | Runs (UTC, 2026-10-22) | Status |
| ---: | --- | --- | --- | --- |
| 1 | A | `20261022T000523Z` | 00:05:23–00:07:14 | 4 of 4 `ok` |
| 2 | B | `20261022T003600Z` | 00:36:00–00:38:59 | 4 of 4 `ok` |
| 3 | C | `20261022T005010Z` | 00:50:10–00:51:52 | 4 of 4 `ok` |
| 4 | C | `20261022T005714Z` | 00:57:14–00:58:56 | 4 of 4 `ok` |
| 5 | B | `20261022T010717Z` | 01:07:17–01:10:21 | 4 of 4 `ok` |
| 6 | A | `20261022T030948Z` | 03:09:48–03:11:37 | 4 of 4 `ok` |

- All 24 runs ended `ok` with zero check violations. No protocol stopped early, no run was aborted,
  and no sample crossed the 4.80 GiB threshold. Each position ran once, so nothing was re-run (3.4)
  and every protocol is a used protocol (3.3).
- **Acceptance (10):** the collector found all five criteria met and listed no problem. Batch-1 is
  therefore the analyzed batch, and no further batch runs (3.4).
- **Code state (3.1):** every protocol and run record shows commit `b1bdae6` with the hashed paths
  clean, and the same `source_sha256` (11 files) and `uv_lock_sha256` (starting `99484c14ebf3`).
  Both equal the files at Part A's commit `caa0be1`; `b1bdae6` adds AI-usage logs only.
- **Inputs (2.2):** every run verified the seven SHA-256 values before Spark started and recorded a
  `windows_config` equal to the stride-7 `config.json`. When the collector ran after the session,
  the seven files still had those hashes.
- **Settings (6, item 1):** every run records its configuration's three values (2.1) and flags
  (2.4). Every other recorded Spark setting, and the recorded environment (CPU count, Java, machine,
  macOS, packages, platform, Python and RAM), are identical in all 24 runs. The reference run's
  recorded Spark settings equal those of run 2 of the stride experiment's stride-7 protocol in every
  key, A's three values included, and so does its recorded environment.
- **Plans (4.2; 6, item 2):** captured in all 24 runs, each with 25 SQL executions, ids 0 to 24
  without gaps. In every run, 24 plans are adaptive and final, and one, the `CreateViewCommand`
  without jobs, is not adaptive. No execution ended with an error. Each run's 11 hash exchanges
  requested and wrote 200 partitions in A and B and 8 in C, and there was no range exchange. No read
  in B or C is marked `coalesced`. Plan capture took 0.778–0.969 s per run.
- **Records:** `data/outputs-partitions/batch-1/`, laid out as in 2.4.

### 14.2 Run log

The session used the helpers of 4.4, `docs/partition-session.zsh` as committed in `e6fa339`
(SHA-256 starting `ca4ceac6332de0d6`), loaded in two Terminal windows: window 1 ran the checks,
pauses, readings and protocols, and window 2 the watcher. Each protocol started right after a
five-minute pause and a `ready` reading that met all three limits of 3.2.

| Position | Checks (3.2) | Pause before the start | Available at the start (GiB) | 5-minute load at the start | Minutes since boot | Lowest free before a run (GiB) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1, A | 23:29:39 on 2026-10-21 (14.3) | 00:00:22–00:05:22 | 3.37 | 2.32 | 37 | 3.25 |
| 2, B | not repeated | 00:31:00–00:36:00 | 3.95 | 1.44 | 67 | 3.13 |
| 3, C | not repeated | 00:45:09–00:50:09 | 4.27 | 2.50 | 81 | 2.84 |
| 4, C | not repeated | 00:52:14–00:57:14 | 4.19 | 2.63 | 88 | 3.29 |
| 5, B | not repeated | 01:02:16–01:07:16 | 3.74 | 2.38 | 98 | 2.99 |
| 6, A | not repeated | 03:04:46–03:09:46 | 3.24 | 1.31 | 221 | 3.05 |

The last column is the lowest `free_memory_before_bytes` among each protocol's four runs. Three
runs started with less than 3.0 GiB free (runs 2 and 4 at position 3, run 4 at position 5); as in
experiments.md 5.2, 3.2 requires 3.0 GiB only before a protocol starts.

- **Before position 1:** checks at 23:10:14 on 2026-10-21, 4,103 minutes after the previous boot,
  were followed by two pauses whose readings gave 1.2 and 2.14 GiB, so nothing started. The Mac was
  restarted (boot at 23:28:17). The checks at 23:29:39, a minute after the boot and labeled
  `position n`, showed Low Power Mode off, AC power, no Docker backend, no Java or pipeline process,
  only Terminal and Finder open, `HEAD b1bdae6` with no changed code file, and no Spark scratch
  folder. Readings 6, 10 and 15 minutes after the boot failed all three limits (2.89, 2.2 and
  1.84 GiB; 5-minute load 10.40, 8.21 and 5.36); one at 18 minutes failed only the wait after the
  boot. A reading at 31 minutes met all three limits, and position 1 started after a further pause,
  37 minutes after the boot.
- **Before position 3:** the first pause (00:39:36–00:44:36) ended with a 5-minute load of 4.25, so
  nothing started. Readings of 4.05 and then 4.00 followed, and a second full pause preceded the
  start.
- **Before position 6:** the pause 01:11:05–01:16:05 ended with a 5-minute load of 4.26, so nothing
  started. The next pause began at 03:04:46 (14.3, item 2).
- **Readings on their own:** besides the readings that ended a pause, `ready` was run on its own in
  both windows, for example in window 2 during the pauses at 84–85 and 102–105 minutes after the
  boot. It logs `protocol not started` whenever a reading fails, so those lines in the run log are
  not refused starts. Five starts were refused, each at the end of a pause: two before the restart,
  one at 23:34:51, and one each before positions 3 and 6.
- **Abort rule:** no run came near its limit. The longest raw wall times were 28.6 s (A), 46.5 s (B)
  and 26.4 s (C), against 77, 99 and 77 s. The watcher saw all 24 pipeline processes, four per
  protocol, and its largest readings were 26, 45 and 24 s. No abort and no after-abort check was
  needed.
- **Notes:** after each protocol, the author recorded `4 ok, nothing unusual` with `note`.
- **After the session:** a check before 03:26 found no Spark scratch folder and no Java process.

### 14.3 Deviations and uncertain conditions

1. **The 3.2 checks were recorded once, before position 1.** `prechecks` ran at 23:29:39, a minute
   after the boot and 36 minutes before position 1 started, and not again before any position, as
   the helpers' checklist asks (4.4). For all six protocols the run log shows the pause and the
   `ready` reading just before the start, but not Low Power Mode, the power source, Docker, Java or
   pipeline processes, or the open apps at the start. Every run records its own code state (14.1).
   The author states that these conditions were unchanged from the checks at 23:29:39 throughout
   the session.
2. **Position 6 started about two hours after position 5.** Position 5's runs ended at 01:10:21;
   after the start refused at 01:16:05, the next pause began at 03:04:46. The protocols' starts were
   31, 14, 7, 10 and 123 minutes apart, so the spacing of 2.3 is far from even. The run log does not
   record the Mac's state between 01:16 and 03:04. Position 6 started with the least available
   memory of the six (3.24 GiB), and its warm-up had the lowest peak total RSS of the 24 runs
   (2.458 GiB; the other warm-ups 2.625–2.684 GiB). Its measured runs (2.676–2.698 GiB) are within
   the range of the other protocols. The author had dinner during the gap.

Item 1 is a departure from 3.2 in the record and labels all six protocols (10); item 2 is an
uncertain condition of position 6.

### 14.4 Drift (section 8)

| Rule | Positions | Protocol medians of `wall_excl_capture_s` | Difference from the first | Median peak total RSS (GiB) | Difference |
| --- | --- | --- | --- | --- | --- |
| 1. Session drift: A | 1, 6 | 26.581, 26.343 s | −0.238 s (−0.90%) | 2.686, 2.696 | +0.011 GiB |
| 2. Pair: B | 2, 5 | 44.083, 45.248 s | +1.165 s (+2.64%) | 2.718, 2.687 | −0.030 GiB |
| 2. Pair: C | 3, 4 | 25.286, 25.269 s | −0.017 s (−0.07%) | 2.693, 2.688 | −0.005 GiB |

No time difference exceeds 10% of the first median, so no drift is reported under rules 1 and 2,
and no memory difference exceeds 0.2 GiB (rule 3). The context of rule 4 is in 14.2 and 14.3.

**Earlier records (rule 5, descriptive).** A's six measured runs have a median
`wall_excl_capture_s` of 26.462 s (raw `wall_s` 27.376 s) and a median peak total RSS of 2.689 GiB.
The stride experiment's stride-7 protocol (2.5), without plan capture, had 25.660 s and 2.705 GiB.
A's summed stage task counts (53, 22, 81 and 100) and file counts (1, 40, 8 and 1) equal that
protocol's in all eight runs.

### 14.5 Measurements CSV

**Location.** `uv run python analysis/collect_partition_measurements.py --batch
data/outputs-partitions/batch-1` reads the batch's records and writes `measurements.csv` and
`acceptance.json` into the batch folder (4.3). Like the records, they are under `data/`, which is
not in Git. Rebuilding both from the records gives byte-identical files.

**Rows.** One row per started run: 24 rows, warm-ups included, in position order. `used` marks the
runs of the used protocols, here all 24.

**Columns.** 64: the 35 columns of the stride experiment's CSV (experiments.md 5.6) other than
`stride` and `role`, and these 29:

| Group | Columns | From |
| --- | --- | --- |
| Identity | `batch`, `position`, `config`, `used` | the batch folder and `positions.tsv` (3.3) |
| Coalescing and timing | `coalesce_enabled`; `plan_capture_status`; `plan_capture_s`; `wall_excl_capture_s`, which is `wall_s − plan_capture_s` rounded to milliseconds (5) | `spark`, `plan_capture` and `timings_seconds` in `run.json` |
| Plans | `sql_executions`, `adaptive_plans`, `requested_partitions`, `coalesced_reads`, `local_reads`, `broadcast_joins`, `sort_merge_joins`; per phase, `exchanges_<phase>` (the partitions each hash- or range-partitioning exchange wrote at runtime) and `reads_<phase>` (the mark and partitions of each `AQEShuffleRead`) | `plans.json` |
| Files | `files_window_stats`, `files_path_days`, `files_path_summary`, `files_paired`: the Parquet files of each output table | the run folder |
| Comparison (7) | `paired_vs_reference`, `path_summary_vs_reference`: `reference`, `pass` or `fail` | the two tables |

**Limitations.** Those of experiments.md 5.6 apply: task counts are summed stage task counts, and
memory is sampled RSS. In addition, `exchanges_<phase>` leaves out single-partition exchanges, such
as those of the global aggregates in `checks`, and `reads_<phase>` lists only reads with an
`AQEShuffleRead` node. A shuffle stage read without one, as everywhere in B, reads all of its
exchange's partitions.

### 14.6 Summary tables

_Drafted with Claude Code (Opus 5.5) from `measurements.csv` (values computed by script)._

Summaries use the measured runs that ended `ok` in the used protocols (5): three per protocol, six
per configuration. Each cell gives the median and, in brackets, the minimum and maximum. Peak memory
is `peak_rss_total_bytes` in GiB (2^30 bytes).

**By protocol**

| Position | Configuration | Protocol | `wall_excl_capture_s` (s) | `wall_s` (s) | `plan_capture_s` (s) | Peak total RSS (GiB) |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | A | `20261022T000523Z` | 26.581 (25.154–26.996) | 27.475 (26.123–27.835) | 0.894 (0.839–0.969) | 2.686 (2.683–2.693) |
| 2 | B | `20261022T003600Z` | 44.083 (43.090–44.453) | 44.878 (43.912–45.292) | 0.822 (0.795–0.839) | 2.718 (2.659–2.793) |
| 3 | C | `20261022T005010Z` | 25.286 (23.738–25.381) | 26.131 (24.544–26.211) | 0.830 (0.806–0.845) | 2.693 (2.671–2.702) |
| 4 | C | `20261022T005714Z` | 25.269 (23.783–25.555) | 26.129 (24.630–26.395) | 0.847 (0.840–0.860) | 2.688 (2.684–2.697) |
| 5 | B | `20261022T010717Z` | 45.248 (44.811–45.708) | 46.049 (45.618–46.486) | 0.801 (0.778–0.807) | 2.687 (2.682–2.694) |
| 6 | A | `20261022T030948Z` | 26.343 (25.226–27.050) | 27.277 (26.072–27.951) | 0.901 (0.846–0.934) | 2.696 (2.676–2.698) |

**By configuration** (six measured runs; the largest peak covers all eight runs, warm-ups included)

| Configuration | `wall_excl_capture_s` (s) | `wall_s` (s) | `plan_capture_s` (s) | Peak total RSS (GiB) | Largest peak (GiB) |
| --- | --- | --- | --- | --- | ---: |
| A: 200, coalescing on | 26.462 (25.154–27.050) | 27.376 (26.072–27.951) | 0.897 (0.839–0.969) | 2.689 (2.676–2.698) | 2.698 |
| B: 200, coalescing off | 44.632 (43.090–45.708) | 45.455 (43.912–46.486) | 0.804 (0.778–0.839) | 2.691 (2.659–2.793) | 2.793 |
| C: 8, coalescing off | 25.277 (23.738–25.555) | 26.130 (24.544–26.395) | 0.843 (0.806–0.860) | 2.691 (2.671–2.702) | 2.702 |

**Phases and peaks by process type** (medians of the six measured runs; each median is taken on its
own, so the phases do not add up to the total)

| | A | B | C |
| --- | ---: | ---: | ---: |
| `session_start` (s) | 2.490 | 2.476 | 2.514 |
| `window_stats_and_construction_check` (s) | 4.953 | 10.447 | 4.665 |
| `model_and_path_days` (s) | 8.435 | 12.477 | 8.314 |
| `summaries_and_pairing` (s) | 6.462 | 14.043 | 5.090 |
| `checks` (s) | 1.607 | 2.552 | 1.831 |
| `total_in_process` (s), plan capture included | 26.368 | 44.517 | 24.874 |
| Spark JVM peak (GiB) | 1.523 | 1.540 | 1.525 |
| Python workers peak (GiB) | 1.048 | 1.049 | 1.050 |
| Python driver peak (GiB) | 0.114 | 0.114 | 0.115 |

### 14.7 Comparisons (section 9)

_Drafted with Claude Code (Opus 5.5) from `measurements.csv`. For configurations X and Y,
d = X − Y between medians of measured runs: d1 in positions 1–3, d2 in positions 4–6, and d over the
six runs of each. The time threshold is 10% of A's six-run median, 2.646 s; the memory threshold is
0.2 GiB._

| X − Y | Measure | d1 | d2 | d | Same sign | Beyond the threshold | Rule (9) |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| A − B | `wall_excl_capture_s` (s) | −17.502 | −18.905 | −18.170 | yes | yes | differ: B slower |
| B − C | `wall_excl_capture_s` (s) | +18.797 | +19.979 | +19.355 | yes | yes | differ: B slower |
| A − C | `wall_excl_capture_s` (s) | +1.295 | +1.074 | +1.184 | yes | no | no clear difference |
| A − B | peak total RSS (GiB) | −0.032 | +0.009 | −0.001 | no | no | no clear difference |
| B − C | peak total RSS (GiB) | +0.024 | −0.001 | +0.000 | no | no | no clear difference |
| A − C | peak total RSS (GiB) | −0.008 | +0.008 | −0.001 | no | no | no clear difference |

B's six-run median is 68.7% above A's and 76.6% above C's. A's is 1.184 s (4.7%) above C's, below
the threshold.

**Phases** (described without a threshold; seconds)

| Phase | A − B: d1, d2, d | B − C: d1, d2, d | A − C: d1, d2, d |
| --- | --- | --- | --- |
| `session_start` | −0.024, +0.055, +0.014 | +0.007, −0.085, −0.038 | −0.017, −0.030, −0.024 |
| `window_stats_and_construction_check` | −5.074, −5.636, −5.494 | +5.457, +5.893, +5.781 | +0.383, +0.256, +0.288 |
| `model_and_path_days` | −3.889, −4.189, −4.042 | +3.963, +4.357, +4.163 | +0.075, +0.168, +0.121 |
| `summaries_and_pairing` | −7.619, −7.543, −7.581 | +8.969, +8.938, +8.953 | +1.350, +1.394, +1.372 |
| `checks` | −0.926, −0.948, −0.945 | +0.749, +0.692, +0.721 | −0.177, −0.255, −0.224 |
| `total_in_process` | −17.749, −18.646, −18.149 | +19.053, +20.275, +19.643 | +1.304, +1.629, +1.494 |

In every phase other than `session_start`, d1, d2 and d have the same sign for all three pairs; in
`session_start` their signs differ for A − B and B − C. B's largest excess over A is in
`summaries_and_pairing` (7.581 s), then `window_stats_and_construction_check` (5.494 s) and
`model_and_path_days` (4.042 s). C's `checks` phase is longer than A's in both halves.

### 14.8 Plans, partitions, tasks and files (sections 5 and 6)

_Drafted with Claude Code (Opus 5.5) from the `plans.json` files and the CSV. Every value is the
same in all eight runs of a configuration._

| | A: 200, coalescing on | B: 200, coalescing off | C: 8, coalescing off |
| --- | --- | --- | --- |
| Hash exchanges: partitions written at runtime | 200 in each of 11: 5 in `window_stats`, 2 in `model`, 4 in `summaries` | 200 in each of the same 11 | 8 in each of the same 11 |
| Reads marked by AQE (partitions read) | `window_stats`: local 1; coalesced 1, 3, 9, 1. `model`: coalesced 8, 1. `summaries`: coalesced 8, 9, 1, 1 | none | `window_stats`: local 8 |
| Joins in the final plans | 9 broadcast hash | 8 broadcast hash, 1 sort-merge | 9 broadcast hash |
| Summed stage task counts: `window_stats`, `model`, `summaries`, `checks` | 53, 22, 81, 100 | 1,043, 413, 1,331, 329 | 91, 29, 107, 233 |
| Files: `window_stats`, `path_days`, `path_summary`, `paired` | 1, 40, 8, 1 | 200, 984, 200, 200 | 8, 40, 8, 8 |

**The sort-merge join in B.** SQL execution 0 (`window_stats`) joins the windows with an aggregate
of their member rows, a left outer join on the four window keys. Its initial plan has the same
operators in A, B and C, with a sort-merge join there. The aggregate runs in two steps, first by the
window keys and `date`, then by the window keys alone (Spark's plan for a distinct count of dates).
The exchange between the second step's partial and final aggregates wrote, by its runtime metrics:

| | Partitions read by the second step's partial aggregate | Records written | Data size | That join in the final plan |
| --- | ---: | ---: | ---: | --- |
| A | 9 (coalesced) | 48,266 | 6.3 MiB | broadcast hash join; the left side read locally (1 partition) |
| B | 200 | 769,886 | 99.9 MiB | sort-merge join |
| C | 8 | 42,912 | 5.6 MiB | broadcast hash join; the left side read locally (8 partitions) |

Every run records `spark.sql.autoBroadcastJoinThreshold` as 10,485,760 bytes (10 MiB). The partial
aggregate writes one record per window and partition holding any of the window's 252 dates: in C,
5,364 × 8 = 42,912 exactly, and in A 48,266, close to 5,364 × 9 = 48,276. If the dates hash evenly
over 200 partitions, B's expected count is 5,364 × 200 × (1 − (199/200)^252) ≈ 769,456, within
0.06% of the 769,886 written (Claude Code's arithmetic, not a measurement).

### 14.9 Output comparison (section 7)

_Drafted with Claude Code (Opus 5.5) from `acceptance.json` and from the collector's comparison
function, run per configuration._

**Reference:** run 2 of position 1, `run-20261022T000523Z-2`. All 23 other runs pass in both tables:
the reference's row counts (5,364 and 10,728) and keys, with no null or duplicate key; the same
columns and types; NULLs in the same rows; breach fields and the other non-floating columns equal
exactly. Every run's `window_stats` and `path_days` row counts (5,364 and 2,698,866) equal the
reference's.

**Floating-point columns:**

| Configuration | Runs compared | Runs with any difference | Largest absolute difference: `paired`, `path_summary` | Largest relative difference: `paired`, `path_summary` |
| --- | ---: | ---: | --- | --- |
| A | 7 | 0 | 0, 0 | 0, 0 |
| B | 8 | 8 | 2.13e-14, 1.82e-11 | 8.80e-11, 1.36e-15 |
| C | 8 | 8 | 1.07e-14, 7.28e-12 | 1.76e-11, 5.97e-16 |

In B and C, the same 12 columns differ: in `paired`, `realized_variance`, `sum_abs_return`,
`total_turnover_2x`, `total_turnover_2x_pre_breach`, `mean_turnover_2x`,
`mean_turnover_2x_pre_breach`, `exact_gap`, `approx_gap` and `approx_rel_error`; in `path_summary`,
`total_turnover`, `mean_turnover` and `total_abs_rebalance`. Every other floating-point column,
among them the returns, drawdowns, maxima, `log_gap` and `final_nav`, is equal exactly in every run.
`approx_rel_error` has the largest relative difference (8.80e-11); its largest absolute difference
is 2.0e-15. Every difference is within the tolerance of section 7.

**The stride experiment's run** (run 2 of `20261019T035809Z`) passes, with no difference in any
column of either table and equal row counts.

## 15. Answers and limits

_The questions are Claude Code's proposals of 2026-10-22, grouped as the author answered them. In
15.1–15.4, the parts marked as drafted give facts, computed with Claude Code (Opus 5.5) by script
from batch-1's records (14) and from section 11, which is unchanged. The answers, marked "Answer
(author)", are the author's, copied from the conversation of 2026-10-22; at the author's request
Claude Code applied its review's corrections: in (a), times compared as longer median times, the
A–C difference on the threshold's base and "no clear difference" for A and C; in (b), the measured
quantities; in (d), B's excess over the predicted range, the mechanisms the measurements cannot
separate, and "no clear difference" for A and C._

### 15.1 (a) Runtime

> How do coalescing (A against B) and the requested count (B against C) change runtime, and how
> does C compare with A?

_Drafted with Claude Code (Opus 5.5): the medians are in 14.6, and d1, d2 and d by pair and by phase
in 14.7._

**Answer (author).** B's median time was 68.7% longer than A's and 76.6% longer than C's. Both
halves showed the same direction. A's median was 1.18 s (4.5%) above C's, below the threshold of 10%
of A's median. For this workload, A and C showed no clear difference, although A was slightly slower
in both halves.

### 15.2 (b) Plans

> What do the plans show, including B's sort-merge join?

_Drafted with Claude Code (Opus 5.5): the plans, task counts and file counts are in 14.8, and the
differences by phase in 14.7._

**Answer (author).** A wrote 200 partitions per exchange, but AQE coalesced reads to fewer
partitions. B kept 200 without coalescing and had much higher summed stage task counts and more
output files. B also retained a sort-merge join where A and C used broadcast joins. These
observations help explain B's longer runtime, but do not isolate the cost of each mechanism.

### 15.3 (c) Memory and results

> Do the configurations change peak memory or any result?

_Drafted with Claude Code (Opus 5.5): peak memory is in 14.6 and 14.7, and the output comparison in
14.9._

**Answer (author).** Median peak RSS was about 2.69 GiB in all configurations, with no clear
difference under the predefined rule. All output comparisons passed. Small floating-point
differences stayed within tolerance.

### 15.4 (d) Predictions against results

> Where were the predictions off, and why?

_Drafted with Claude Code (Opus 5.5) from section 11, which is unchanged, and from section 14. Time
items use the medians of `wall_excl_capture_s` over the six measured runs, and memory items the
medians of peak total RSS._

| Section 11 | Predicted | Measured | Result |
| --- | --- | --- | --- |
| A, median time | 25.7 s, band 20.5–30.8 s | 26.462 s | inside, 3.0% above the point |
| B, median time | 33 s, band 26–53 s | 44.632 s | inside, 35.2% above the point and above the 29–37 s of 11.3 |
| C, median time | 25.7 s, band 20.5–30.8 s | 25.277 s | inside, 1.6% below the point |
| A, B and C, median peak | 2.5–2.9, 2.5–3.1 and 2.5–2.9 GiB | 2.689, 2.691 and 2.691 GiB | inside |
| Abort limits | 77, 99 and 77 s | longest runs 28.6, 46.5 and 26.4 s | no run aborted |
| 11.1, A | 200 partitions per exchange; large reads coalesced to about 8, small ones to 1; a local read possible; files 1, 40, 8, 1; task counts about 53, 22, 81, 100 | 200; four reads coalesced to 8 or 9, one to 3 and five to 1; one local read; files and task counts as predicted | as predicted, with one read of 3 partitions |
| 11.1, B | 200 per exchange; no coalesced read; files about 200, 1,000, 200, 200; task counts several times A's | 200; no coalesced read; files 200, 984, 200, 200; task counts 3.3 to 19.7 times A's | as predicted; not predicted: one join stays a sort-merge join (14.8) |
| 11.1, C | 8 per exchange; no coalesced read; files 8, 40, 8, 8 | 8; no coalesced read; files 8, 40, 8, 8; one local read of 8 partitions | as predicted; the local read was not mentioned |
| 11.2, A against C | no clear difference | d = +1.184 s, below the 2.646 s threshold | as predicted |
| 11.2, B against A and C | slower by more than 10%, in both halves | d = −18.170 s (A − B) and +19.355 s (B − C), with d1 and d2 of the same sign | as predicted |
| 11.2, memory | no clear difference between any two | none | as predicted |
| 11.3, B's excess over A | 3.3–11.3 s (29–37 s against 25.7 s): about 1,900 extra tasks and 1,550 extra files at 5–20 ms each over 8 cores, and 1–3 s for reading `path_days` | 18.170 s; 2,860 more summed stage tasks and 1,534 more files than A | above the range |

If all of B's excess over A came from its extra summed stage tasks and files, spread over 8 cores
as 11.3 assumes, each would cost about 33 ms (18.170 s × 8 / 4,394), against the assumed 5–20 ms.
The measurements cannot separate those costs from the sort-merge join and the larger shuffle of
14.8, and summed stage task counts may count a stage twice (5), so this is arithmetic, not a
measured cost.

**Answer (author).** All runtime and memory medians were within their predicted bands. B's median
was 44.63 s rather than the predicted 33 s: its excess over A (18.2 s) was larger than the
prediction allowed (3.3–11.3 s), although the broad band covered the result. The prediction left
out the sort-merge join, and the measurements cannot show whether the assumed per-task and per-file
costs were also too low. The predicted comparison outcomes held: B was slower, A and C showed no
clear difference, and memory showed no clear difference.

### 15.5 (e) What these measurements cannot show

> What can these measurements not show?

**Answer (author).** This experiment covers one workload on one machine, with two protocols per
configuration. Prechecks were not repeated, and position 6 followed a roughly two-hour gap with
uncertain machine conditions. No drift was detected under the predefined rule, but this does not
prove stable conditions throughout. CPU, spill and GC costs were not measured, so the results cannot
establish each mechanism's contribution or generalize to larger workloads.

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

**Part B** (2026-10-22). Section 14 gives batch-1's results as facts, with the author's statements
in 14.3, and section 15 the author's answers, with facts drafted by Claude Code and the review's
corrections applied at the author's request. The status at the top now describes both parts, and a
line marks the end of Part A; sections 1–13, the predictions included, are unchanged. This version
is committed on `feature/shuffle-partitions` after the formal session.
