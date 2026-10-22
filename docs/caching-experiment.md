# Caching experiment

Author: I decided the configurations and rules listed in 1.2, reviewed and approved the rest of the
design and the predictions, ran the formal measurements, and wrote the Part B answers. AI
contributions are described below.

**Part A (sections 1–13): the design, the code and the predictions, committed before any measured
run (`6131f83`).** The author approved the design, the predictions and the abort limits (section 11)
on 2026-10-22 as the preregistered hypotheses, and ran the formal measurements (2.4, 4.4). **Part B
(sections 14–15): the results of batch-1, run on 2026-10-22 (UTC), and the author's answers.**
Batch-1 met every acceptance criterion (10), so it is the analyzed batch, and no further batch runs
(3). Sections 1–13, the predictions included, are unchanged since Part A. The history of this
document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the records of the shuffle-partition experiment and the
pandas baseline. Everything not listed in 1.2 as decided by the author is Claude Code's proposal
(section 13). The predictions in section 11 were drafted with Claude Code and reviewed and approved
by the author. Revision 1 applied the author's review of the draft (history at the end). Part B was
drafted with Claude Code from batch-1's records, with the author's statements and answers (sections
14 and 15)._

This experiment changes none of the earlier experiments ([experiments.md](experiments.md),
[partition-experiment.md](partition-experiment.md), [pandas-baseline.md](pandas-baseline.md)), nor
their predictions, records, collectors or session helpers. It writes only under
`data/outputs-caching/`.

## 1. Question and decisions

### 1.1 Question

For the stride-7 workload, how does caching intermediate data in Spark change runtime and peak
memory, and does it change any result? This is the caching part of research question 3 (spec §2).
The data, model, window set, leverages, Spark settings and outputs stay fixed; only what is cached
changes. The machine is the earlier experiments' (Apple M2 MacBook Air, 8 cores, 8 GiB RAM).

The pipeline already writes each output table and reads it back before later phases use it
(`materialize` in `spark_pipeline.compute`), so no phase recomputes an earlier phase's table. Two
kinds of repeated work remain, and they are what caching can remove:

- The window-member rows (`members`: each window expanded into its days and joined to the returns)
  are never written. They are built twice: for the window statistics and again for the model.
- Every later query that uses a read-back table reads it from its Parquet files: `path_days`, for
  example, in the summaries and in several checks.

Filling a cache costs a pass over its data, and the cached data occupies part of the driver JVM's
heap until it is released. The experiment measures the net effect.

### 1.2 Decided by the author (2026-10-22)

- Three configurations on the stride-7 window set (2.1, 2.2): A caches nothing; B caches the
  window-member rows; C caches them and also the four read-back tables, for reuse in all later
  phases.
- Order A–B–C–C–B–A, with four fresh-process runs per protocol: one warm-up, three measured, so 24
  runs in all (2.3).
- Claude Code writes the code, tests and helpers and drafts Part A, the predictions included, for
  the author's approval. The author runs the formal measurements and writes the answers, as in the
  shuffle-partition experiment.
- Part A is approved and committed before any caching measurement. The earlier experiments stay
  unchanged.
- In the review of the draft:
  - the downstream reads of cached data are verified apart from the `count()` that fills each
    cache, without requiring the numbers of reads found in the small dry batch (6.4);
  - a failed or aborted run's missing outputs are acceptance failures that the collector reports;
    they must not stop it (4.3, 7).

Approved by the author on 2026-10-22, before any measured run, as the preregistered hypotheses: the
A/B/C design (2.1), and the predictions and abort limits of section 11.

Approved by the author with the plan of 2026-10-22, as proposed by Claude Code:

- when each table is filled and released (2.1); the storage level `MEMORY_AND_DISK_DESER`, each
  cache filled by an explicit `count()` and released with `unpersist(blocking=True)`; a cleanup in
  `main()` on every other path, with the way each cache was released recorded (4.1);
- fill and release times inside the phase timings, with plan capture excluded as before (5);
- cache use verified first by Spark's storage information and then by the cached reads in the
  plans, where a read's row metric has three states: positive, zero (a read that counts as use) and
  missing (unknown, never proof) (6);
- all four output tables of every run, warm-ups included, compared with A's run 2 at position 1 (7);
- the shuffle-partition experiment's rules for batches, machine state, positions, failures, drift,
  comparisons and acceptance (3, 8–10), with cache verification as criterion 3.

## 2. Configurations, workload and order

### 2.1 Configurations

| Configuration | `--cache` | Cached |
| --- | --- | --- |
| A | `none` | nothing |
| B | `members` | the window-member rows |
| C | `members-checks` | the window-member rows, and `window_stats`, `path_days`, `path_summary` and `paired` |

When each cache is filled, read and released:

| Cached data | Rows at stride 7 | In | Filled | Read from the cache by | Released |
| --- | ---: | --- | --- | --- | --- |
| `members` | 1,351,728 | B, C | in `window_stats`, before the window statistics | the window statistics (`window_stats`); the simulation (`model`) | at the end of `model`, after `path_days` is written and read back |
| `window_stats` | 5,364 | C | in `window_stats`, right after its read-back | the construction checks; the pairing (`summaries`); the checks | at the end of `checks` |
| `path_days` | 2,698,866 | C | in `model`, right after its read-back | the path summaries (`summaries`); the checks | at the end of `checks` |
| `path_summary` | 10,728 | C | in `summaries`, right after its read-back | the pairing; the checks | at the end of `checks` |
| `paired` | 5,364 | C | in `summaries`, right after its read-back | the checks | at the end of `checks` |

All other settings are Spark's defaults and the pipeline's (`local[*]`, UI off, UTC session time
zone), as in configuration A of the shuffle-partition experiment: 200 shuffle partitions, AQE and
its partition coalescing enabled. Spark runs in local mode, so the driver JVM also runs every task
and holds every cache, within its default 1 GiB maximum heap.

A against B shows what caching the members does; B against C, what caching the four tables adds;
A against C, the whole.

### 2.2 Workload

The workload is the stride-7 set in `data/windows-experiments/full-2026-10-12/rolling-252-s7`,
unchanged: 5,364 windows and 1,351,728 window-member rows (experiments.md 2.2). Its runs write
5,364 `window_stats` rows, 2,698,866 `path_days` rows, 10,728 `path_summary` rows and 5,364 `paired`
rows (partition-experiment.md 14.9). Each run verifies seven SHA-256 values recorded in its
`config.json` before Spark starts: `windows.parquet`, the five daily-return files and
`quality_report.json`. On any mismatch it exits with code 3.

### 2.3 Order and repeats

There are six protocols, at positions 1 to 6: A, B, C, C, B, A. Each protocol is one
`etf_risk.measure` call with `--repeats 4`: four fresh-process runs, the first of them a warm-up.
Each configuration therefore has two protocols, eight runs and six measured runs. The reasoning on
drift is that of partition-experiment.md 2.3: each configuration's two positions average 3.5, and a
drift that changes linearly with position alone cannot produce a difference under the rule of
section 9.

### 2.4 Commands and records

The session helpers (4.4) start each protocol by its position: `position 3` runs configuration C.
The command they run, from the repository root, is

```bash
caffeinate -i uv run --group measure python -m etf_risk.measure --repeats 4 -- \
    --windows data/windows-experiments/full-2026-10-12/rolling-252-s7 \
    --out-root data/outputs-caching/<batch>/<A|B|C> \
    --cache <none|members|members-checks> --record-plans
```

All three configurations pass both flags, A as `--cache none`. So every run records a `cache`
section, reads Spark's storage information at the end of each phase, and captures its plans the
same way; the capture's time is left out of the compared time (5). No configuration passes the
partition flags: Spark's defaults apply, and each run's records show them (6.1).

A batch (3) is one folder, `data/outputs-caching/<batch>/`, starting with `batch-1`. It holds:

- `A/`, `B/` and `C/`, each with `full-2026-10-12/rolling-252-s7/`: one `protocol-<UTC time>.json`
  per protocol, and one folder and one `.log` per run. Each configuration's two protocols share a
  folder.
- `positions.tsv`, the position of every protocol the helpers ran, and `run-log.txt`, the session's
  checks and notes.
- `measurements.csv` and `acceptance.json`, written by the collector (4.3).

### 2.5 Earlier records with A's settings

- **Shuffle-partition experiment, configuration A** (Spark's default values, passed explicitly,
  with plan capture), batch-1 at commit `b1bdae6`, protocols `20261022T000523Z` and
  `20261022T030948Z` (partition-experiment.md 14.6–14.9). Over its six measured runs:
  - median `wall_excl_capture_s` 26.462 s (25.154–27.050 s); median `plan_capture_s` 0.897 s;
  - median peak total RSS 2.689 GiB (2.676–2.698 GiB), and at most 2.698 GiB over all eight runs;
    per process type, Spark JVM 1.523, Python workers 1.048 and Python driver 0.114 GiB;
  - phase medians: `session_start` 2.490 s, `window_stats_and_construction_check` 4.953 s,
    `model_and_path_days` 8.435 s, `summaries_and_pairing` 6.462 s, `checks` 1.607 s;
  - in all eight runs, 25 SQL executions, and 1, 40, 8 and 1 files in `window_stats`, `path_days`,
    `path_summary` and `paired`.
- **Pandas baseline, S** (Spark's defaults, unset, without plan capture), batch-1 at commit
  `204d04d`: median `wall_s` 26.407 s (25.621–27.152 s) and median peak total RSS 2.680 GiB
  (pandas-baseline.md 14.6).

These are earlier records under an older code state. They are used only descriptively (section 8,
item 5) and as the basis of the predictions (11).

## 3. Run conditions, batches and failures

The rules of partition-experiment.md 3.1–3.4, which the author approved for that experiment, apply
with these changes:

- **Batches (3.1).** A batch is one A–B–C–C–B–A sequence, run in one session under one code state.
  Every protocol JSON and `run.json` records the same `source_sha256` and `uv_lock_sha256`, with the
  hashed paths clean; the commit is only reported. Any change to `src/`, `pyproject.toml` or
  `uv.lock` ends the batch, and a new one starts at position 1.
- **Machine state (3.2).** Required before each protocol:
  - Low Power Mode off and mains power;
  - apps other than Terminal and Finder quit;
  - a 5-minute pause;
  - read just before the start: at least 3.0 GiB available, a 5-minute load average of at most 4.0,
    and at least 30 minutes since boot.

  As in the pandas baseline, `position` writes the 3.2 checks into the run log right before each
  start.
- **Positions (3.3).** `positions.tsv` as there, with the result of the cache check (4.3) in the
  column `cache_check`.
- **Failures and retries (3.4).** The table of partition-experiment.md 3.4, with the abort limits of
  section 11. The check after each protocol verifies each run's settings, plan capture and caches
  (6). A failed check stops the session like any other stop.
- **Branch.** `feature/caching`, created from `e3b2621` on `main` (the merge of the pandas
  baseline), and later merged with a merge commit.

## 4. Code

### 4.1 The `--cache` option

`etf_risk.spark_pipeline` has one new option, `--cache none|members|members-checks`. Without it, a
run and its records are as before, apart from the code state. Unlike the partition flags, it changes
no session setting, so it also works inside an existing session, as in the tests.

- **Fill.** Each table of the mode is persisted at `MEMORY_AND_DISK_DESER`, the level PySpark 4.2
  uses for `DataFrame.cache()`, where the pipeline creates it (2.1). It is filled at once by an
  explicit `count()`, so the cache is filled at a known point in its phase, not by the first query
  that reads it. The `count()` runs under the job description `cache fill: <table>`, which Spark
  gives to its SQL execution, so the plans tell the fill from the reads after it (6.4). The phase's
  own description is restored right after.
- **Release.** After its last reader, `unpersist(blocking=True)` releases it; the call returns once
  its blocks are removed.
- **Cleanup.** On every other path (an exception, or the early return after a failed construction
  check), `main()` releases every cache still held before it writes `run.json` and stops Spark. An
  error during that cleanup is recorded as `cache_cleanup_error`.
- **Records.** With the option, `run.json` records `pipeline_options` with the mode (`cache`) and a
  `cache` section: the mode and storage level, and for each cached table:
  - `filled_in` (its phase), `rows` (the fill's count) and `fill_s`;
  - `after_fill`: Spark's storage information for each cached RDD that the fill added, with its
    partitions, cached partitions, bytes in memory and on disk, and storage level;
  - `before_release` and `cached_after_release`: that RDD's storage information just before and
    right after the release;
  - `released_in` (its phase, or none), `released_by` (`plan` or `cleanup`) and `release_s`.

  The section also holds the storage information read at the end of each phase (`snapshots`), and
  the time spent reading storage information (`storage_info_s`).
- **Storage information** comes from `SparkContext.getRDDStorageInfo` through the JVM gateway, an
  internal interface checked on Spark 4.2.0. It lists only RDDs with cached blocks.
- **Time.** Fills, releases and storage readings fall inside the phase timings: they are part of
  what each configuration costs. Each run reads the storage information at the four phase ends, and
  twice more for each fill and each release: 4 readings in A, 8 in B and 24 in C.

### 4.2 Plans: the scan nodes

`etf_risk.plans` writes `plans.json` format 2. Everything of format 1 (partition-experiment.md 4.2)
is unchanged; format 2 adds, for each SQL execution:

- its description: the job description in effect when it started. That is its phase's (the phase's
  name, or "row counts for run.json" in bookkeeping), or `cache fill: <table>` for a fill (4.1);
- its scan nodes from the plan graph: `InMemoryTableScan`, a read of cached data, and file scans
  such as `Scan parquet`. For each: its node description, its metrics, and `rows`, its "number of
  output rows", or none when Spark recorded no such metric. A missing metric is never read as 0.

When a query reads cached data, the plan graph also lists the nodes of the cached query's own plan
below its `InMemoryTableScan`, among them that query's `Scan parquet`. Served from the cache, those
nested file scans record 0 rows or no row metric (4.5). They are recorded, but they are not reads,
and no criterion uses them.

### 4.3 Collector

`analysis/collect_caching_measurements.py` reads one batch folder (2.4) and writes into it:

- `measurements.csv`: one row per started run of every protocol in the batch, used or not. The
  columns are the identity (batch, position, configuration, whether used, protocol, run), the stride
  experiment's measurement columns (experiments.md 5.6), and these additions:
  - `cache_mode`, `plan_capture_status`, `plan_capture_s`, `wall_excl_capture_s` (5),
    `sql_executions`, `fill_executions` (the fills found in the plans) and `storage_info_s`;
  - for each of the five cacheable tables: `fill_s`, `release_s`, and the bytes in memory and on
    disk after the fill;
  - `cached_reads_<phase>` for the four phases and bookkeeping: the downstream cached reads, without
    the fills, written as positive/zero/missing (6.4);
  - files written per output table, and the result of each table's comparison with the reference
    (7): `pass`, `fail`, `reference`, `missing`, `incomplete`, `unreadable` or `no reference`.
- `acceptance.json`: each acceptance criterion (10) with every problem found, the used protocols,
  the reference run, the commits found, the member rows of the window set, and the largest
  floating-point difference per configuration, table and column.

It prints a summary and exits with 1 if any criterion fails. With `--check-protocol <protocol JSON>
--config <A|B|C>`, it checks one protocol: every run's settings, plan capture and caches against the
configuration (6), and each run's status. The helpers run it after each protocol, so a wrong
setting or cache stops the session at once, not after the batch.

**Runs without their outputs.** A run that failed or was aborted may lack its own `run.json` (when
the pipeline was killed, `measure` writes one that holds only the measurement), its plans, or some
of its tables. Spark writes a `_SUCCESS` marker into a table's folder when the table's write
commits, so a table without one is incomplete. Both forms report each missing, incomplete or
unreadable record as a problem under its criterion (3, 4 and 5) and go on; neither stops.

It imports the shuffle-partition collector's functions unchanged: positions, protocols and runs,
code state, inputs, the comparison of tables by their full keys, file counts and check violations.
That collector and its records stay unchanged. Comparing `path_days` (2,698,866 rows) takes several
seconds per run, so collecting a batch takes several minutes.

### 4.4 Session helpers

`docs/caching-session.zsh` is a new file, adapted from `docs/baseline-session.zsh`; the earlier
experiments' helpers stay unchanged. The helpers find the repository from their own path. Their
functions:

- `steps`: the checklist.
- `prechecks`: the 3.2 checks, written into the run log.
- `pause5`: the 5-minute pause.
- `ready`: memory at least 3.0 GiB, load average at most `CACHE_LOAD_MAX`, booted at least
  `CACHE_BOOT_MIN` minutes ago.
- `position n`: refuses numbers outside 1 to 6, and refuses to start while any abort limit is
  missing. It writes the 3.2 checks, runs the protocol at position n, then the check of its
  settings, plans and caches (`--check-protocol` with the position's configuration), and appends
  the `positions.tsv` line. It prints `STOP` when `measure` stopped early or the check failed.
- `where`: the positions run so far.
- `watch_runs`: every 10 s, each running pipeline's configuration, found from its `--cache` value,
  and its raw elapsed time with its abort limit (11). It says ABOVE THE LIMIT when a run passes the
  limit.
- `abort_run`, `after_abort` and `note`: as in the earlier sessions.

Variables set before loading choose the batch (`BATCH`) and the limits (`CACHE_LOAD_MAX`, default
4.0, and `CACHE_BOOT_MIN`, default 30). `CACHE_WINDOWS`, `CACHE_ROOT` and `CACHE_REPEATS` exist only
for a dry run on other data. The abort limits (`CACHE_ABORT_S`) are those of section 11: 80 s for A
and B, 81 s for C.

### 4.5 Tests and validation

**Tests.** `tests/test_caching_options.py` has 10 tests, in the tests' shared session:

- the option's default and rejected values, and the scan-node parser with format 2;
- without the option, `run.json` as before, and nothing left cached;
- for each mode: every table filled and released by the plan in its phase, the storage readings at
  the four phase ends, nothing left cached in the session, each fill's SQL execution named by its
  description in its phase while every other execution keeps its phase's description, and the
  collector's cache check passing for the mode's configuration and failing for another;
- for B and C: all four tables equal to those of a run without caching;
- a forced failure after the fills, and the early return after a failed construction check: in
  both, every cache filled is released by the cleanup, and nothing stays cached.

`tests/test_caching_collector.py` has 22 tests on a fake batch built from three fresh-process runs,
one per configuration, copied into the six positions with two runs each. They cover:

- a batch that meets every criterion, the check after a protocol with the right and a wrong
  configuration, and the CSV;
- a zero-row cached read, which counts as use;
- more and fewer downstream reads than the dry batches found, which pass (6.4);
- planted problems for criteria 1, 3, 4 and 5, among them a release by the cleanup, a partly cached
  table, a wrong fill count, an RDD left at a phase end, a wrong option, a phase without a
  downstream read, a phase whose only cached read is its fill's, a fill whose execution lacks its
  description, a read with its metric missing, a cached read where none is expected, plans of
  format 1, and a changed `path_days` value;
- a run aborted in the model phase (only the `run.json` that `measure` writes, an uncommitted
  `path_days`, no later tables, a cut-off `plans.json`) and a run that failed without `paired`:
  both reported under criteria 3, 4 and 5, by the batch and by the check after the protocol,
  without stopping the collector;
- a reference run without `path_days`: reported under criterion 4, and no run compared on it.

`tests/test_caching_session.py` has 8 tests of the helpers in zsh:

- the file parses;
- loading sets the order, the modes and the approved abort limits and changes into the repository;
- `position` refuses numbers outside 1 to 6 and starts nothing while an abort limit is missing;
- the watcher converts elapsed times to seconds and finds each configuration's abort limit,
  `members` and `members-checks` included;
- `ready` passes only when the memory, load and boot limits are all met.

The full suite, the earlier experiments' tests unchanged among them, passes: 236 tests.

**Validation on a small window set.** None of the runs below is a formal measurement, and their
times are neither reported nor used for section 11. All used the calendar-year window set
`data/windows/full-2026-10-12/calendar-year-r2`, built from the same snapshot as the stride-7 set:
151 windows and 38,017 window-member rows.

- **Probe** (2026-10-22). A toy query in a scratch session, and one run per mode with plans.
- **Dry batches** (2026-10-22). Two A–B–C–C–B–A sequences with the helpers and `CACHE_REPEATS=2`,
  so one warm-up and one measured run per protocol: the first with the draft's code, the second
  with this revision's (the fills' descriptions and the revised collector). No watcher ran. In the
  scratch shell, the helpers' list of open apps was replaced by a placeholder, and in the first
  batch the abort limits were placeholders too.

What they showed, in both dry batches unless stated:

- **Helpers.** They ran positions 1 to 6 in order and wrote `positions.tsv`. Every check after a
  protocol passed.
- **Plan capture.** Every run captured all of its SQL executions, ids 0 to n−1 without gaps: 25 in
  A, 26 in B and 30 in C, where each fill adds one. Every adaptive plan was final; no execution
  recorded an error.
- **Storage.** Every fill counted its table's rows (the members: 38,017, the sum of the windows'
  lengths) and added exactly one RDD, with all of its partitions cached, at the level "Disk Memory
  Deserialized 1x Replicated", all of it in memory and none on disk. On this set, the cached
  `path_days` had 5 partitions and every other cached table 1. Every cache was still fully cached
  just before its release, was released by the plan in its phase, and was no longer listed
  afterwards. Storage information lists only RDDs with cached blocks: after a release, the RDD is
  gone from it.
- **Cached RDDs at the four phase ends:** none in A; 1, 0, 0 and 0 in B; 2, 2, 4 and 0 in C, the
  tables that 6.3 lists.
- **Fills and downstream reads** (`InMemoryTableScan` nodes). In the second batch, each fill's SQL
  execution carried its description, in its table's phase: none in A, 1 in B and 5 in C, each
  reading its cache once. Every other execution carried its phase's description, so the phase's
  description was restored after each fill. Apart from the fills, the downstream reads were: none
  in A; 1 in `window_stats` and 1 in `model` in B; 2, 1, 3 and 14 in the four phases in C. There
  were none in bookkeeping or in the one execution without a phase. The first batch, without
  descriptions, found the same totals with the fills included (2 and 1 in B; 4, 2, 5 and 14 in C);
  there, a fill's read was the one whose node description lists no columns.
- **Zero and missing metrics.** In the probe's toy query, a cached read whose batches a filter all
  skipped recorded 0 rows: a zero is a read that counts as use. In the dry batches, no cached read,
  fill or downstream, recorded 0 rows or lacked its metric. The only missing row metrics, 16 in
  each batch, were on `Scan parquet` nodes of executions that read cached data: the nested file
  scans of 4.2.
- **Files** written: 1, 5, 1 and 1 in `window_stats`, `path_days`, `path_summary` and `paired`, in
  every run.
- **Output comparison.** In each dry batch, all four tables of the 11 other runs passed against the
  reference, run 2 at position 1. No floating-point value differed in any table.
- **Collector.** In each dry batch, it found criteria 2 to 5 met. Criterion 1 failed, as it should
  have: the code was not committed, so all 18 records (6 protocols, 12 runs) show uncommitted
  changes in the hashed paths, although all share the same hashes.

## 5. Measurements

| Group | Values | From |
| --- | --- | --- |
| Time | `wall_s`; the phases `session_start`, `window_stats_and_construction_check`, `model_and_path_days`, `summaries_and_pairing`, `checks`, `total_in_process`; `plan_capture`; fill, release and storage-reading times | `measure`; `timings_seconds` and `cache` in `run.json` |
| Memory | free memory before the run; peak RSS in total and per process type; samples; processes seen; threshold crossing | `measure` |
| Caches | per table: rows, partitions, bytes in memory and on disk, storage level, phase filled and released, how released; cached RDDs at each phase end | `cache` in `run.json` |
| Configuration | recorded Spark settings, `pipeline_options` and environment | `run.json` |
| Execution plans | the format 1 contents, and the scan nodes (4.2) | `plans.json` |
| Results | status, check violations, row counts; the four output tables | `run.json`, `checks.json`, run folder |
| Provenance | code state, verified input checksums, window config | `run.json`, protocol JSON |
| Run conditions | the 3.2 checks, boot time, load average, pauses, memory readings, positions, deviations | run log, `positions.tsv` |

**Timing metric.** The time compared between configurations is
`wall_excl_capture_s = wall_s − plan_capture_s`, as in partition-experiment.md 5: plan recording is
instrumentation, not part of the workload. Unlike plan capture, the fills, releases and storage
readings stay inside `wall_s` and the phase timings, since they are part of the configuration under
test. `wall_s` and `plan_capture_s` are reported next to `wall_excl_capture_s`.

Reported as observations, never as pass/fail criteria:

- each table's fill and release times, its bytes in memory and on disk, and `storage_info_s`;
- the number of SQL executions and of fills, and the downstream reads per phase with their row
  metrics (6.4);
- summed stage task counts per phase (`stage_task_counts`, as in partition-experiment.md 5), and
  files written per output table.

Summaries use the measured runs that ended `ok` in the used protocols. They give medians and
min–max of `wall_excl_capture_s`, the phases and peak total RSS, per protocol and per configuration
(six runs). The memory statistic is the median of `peak_rss_total_bytes` over the measured runs; the
largest value over all runs, warm-ups included, is reported next to it. Not measured (12): garbage
collection, CPU time and spill.

## 6. Settings and cache verification

Each run of the used protocols is checked against its configuration in four ways. 6.1 to 6.4 are
pass/fail (10, criterion 3); 6.5 lists observations.

### 6.1 Recorded configuration

`pipeline_options` is `{"shuffle_partitions": null, "coalesce": null, "record_plans": true, "cache":
<the configuration's mode>}`. The `spark` section shows Spark's defaults for the partition
settings: `spark.sql.shuffle.partitions` 200, `spark.sql.adaptive.enabled` true and
`spark.sql.adaptive.coalescePartitions.enabled` true. Every other recorded Spark setting, and the
recorded environment, are identical in all used runs.

### 6.2 Plan capture

The capture succeeded, and `plans.json` has format 2. It records Spark 4.2.0 and the explain mode
`formatted` (in any letter case), and covers every SQL execution of the process: ids 0 to n−1,
without gaps. No execution ended with an error, and every adaptive plan is final. Partition counts
are not checked: they are not this experiment's question.

### 6.3 Storage information, the primary proof

For each table the configuration caches (2.1), from the `cache` section of `run.json`:

1. The run cached exactly the configuration's tables, in the configuration's mode.
2. The table was filled in its phase: the members and `window_stats` in `window_stats`, `path_days`
   in `model`, `path_summary` and `paired` in `summaries`.
3. The fill counted the table's rows: for the members, the sum of `window_days` over the window set
   (1,351,728 at stride 7); for the four tables, the row counts the run recorded.
4. The fill added exactly one cached RDD, with all of its partitions cached, at the level "Disk
   Memory Deserialized 1x Replicated", and with more than 0 bytes in memory or on disk.
5. Just before its release, that RDD was still fully cached.
6. It was released by the plan, not by the cleanup, in its phase: the members in `model`, the four
   tables in `checks`. Right after the release, that RDD was no longer listed.

And at the end of each phase, the cached RDDs were exactly those of the tables held then:

| Configuration | End of `window_stats` | End of `model` | End of `summaries` | End of `checks` |
| --- | --- | --- | --- | --- |
| A | none | none | none | none |
| B | members | none | none | none |
| C | members, `window_stats` | `window_stats`, `path_days` | the four tables | none |

### 6.4 Fills and downstream reads in the plans

An `InMemoryTableScan` node in a plan (4.2) is a read of cached data. Its row metric has three
states: positive; zero, for example a read whose batches a filter all skipped, which counts as use;
and missing, which is unknown and never counts as proof. A fill's `count()` reads the cache it
fills, so its read proves only the fill. The plans' descriptions (4.1, 4.2) separate the fills from
the downstream reads, the reads by the queries after them:

1. **Fills.** For each table the configuration caches, exactly one SQL execution has the
   description `cache fill: <table>`. It is in the table's phase (6.3, item 2), and it reads cached
   data. No execution has the description of a fill for any other table.
2. **Downstream reads** are the `InMemoryTableScan` nodes of every other execution. In each phase
   where the configuration reads a cache, at least one of them has its row metric, positive or
   zero: `window_stats` and `model` in B, all four phases in C (2.1). Every other phase, bookkeeping
   and the executions without a phase have none.

Their numbers are not checked: the rule asks for downstream reads in each phase that should have
them, not for the numbers found in the dry batches (4.5), which are reported as observations. The
plans do not name the cached data a read uses, so this rule holds per phase, not per table; which
tables were cached, and when, is shown by the storage information (6.3).

### 6.5 Observations

Not pass/fail: each cache's bytes in memory and on disk, its partitions, and its fill and release
times; the number of downstream reads per phase and their row metrics; the nested file scans of
cached plans (4.2); the summed stage task counts and the files written. Part of a cache on disk is
an outcome, not a failure: `MEMORY_AND_DISK_DESER` writes to disk what does not fit in memory.

## 7. Output comparison with A

**Reference:** run 2 of the used protocol at position 1, the first measured run of A. Every other
run of the used protocols is compared with it, warm-ups included (23 runs). The runs of protocols
replaced by a re-run are compared as well and reported. Tables are read with PyArrow, which keeps
null and NaN distinct; `path_days`'s `ticker` partition column is read as plain strings.

| Table | Full key | Rows at stride 7 |
| --- | --- | ---: |
| `window_stats` | `window_kind`, `ticker`, `window_days`, `entry_date` | 5,364 |
| `path_days` | `window_kind`, `ticker`, `window_days`, `entry_date`, `leverage`, `day` | 2,698,866 |
| `path_summary` | `window_kind`, `ticker`, `window_days`, `entry_date`, `leverage` | 10,728 |
| `paired` | `window_kind`, `ticker`, `window_days`, `entry_date` | 5,364 |

For each table, a run passes if the seven rules of partition-experiment.md 7 hold: the same rows;
the same keys, none null and none twice; the same columns and types; NULLs in the same rows; breach
fields equal exactly (listed there for `paired` and `path_summary`); every other non-floating column
equal exactly; and each floating-point value x within `|x − r| ≤ 1e-12 + 1e-9 × |r|` of the
reference value r, with NaN matching only NaN. The largest absolute and relative difference per
column is reported, even when the run passes.

A table that a run did not leave complete fails that run's comparison: missing (no folder),
incomplete (no `_SUCCESS` marker, so its write never committed) or unreadable. A failed or aborted
run can leave its tables so (4.3). If one of the reference's tables is missing, incomplete or
unreadable, criterion 4 fails, and no run is compared on that table (`no reference`).

Unlike the shuffle-partition experiment, all four tables are compared in full, `path_days`
included. No earlier experiment's run is compared: the earlier records are used for times and
memory only (8, item 5).

## 8. Drift rules

All rules use `wall_excl_capture_s` (5).

1. **Session drift.** If A's protocol medians at positions 1 and 6 differ by more than 10% of the
   first, drift is reported and comparisons are marked as affected. Nothing is re-run silently.
2. **Pairs.** The same rule applies to B (positions 2 and 5) and C (3 and 4).
3. **Memory.** Pairs whose median peak total RSS differs by more than 0.2 GiB are reported.
4. **Context.** For each protocol, the start time, the free memory before each run, the load
   average and the time since boot are shown next to the pair differences. No rule applies to them.
5. **Earlier records.** A is compared with the shuffle-partition experiment's configuration A
   (2.5) descriptively only, since the code state and the session differ.

Drift does not void the results. It is reported, and section 9 still applies.

## 9. Comparing configurations

The rule of partition-experiment.md 9, unchanged. For two configurations X and Y, using
`wall_excl_capture_s`: d1 is the difference between their protocol medians in positions 1–3, d2 the
same in positions 4–6, and d the difference between the medians of their six measured runs.

- **Wall time.** X and Y differ if |d| is more than 10% of A's six-run median and d1, d2 and d have
  the same sign. Otherwise there is no clear difference.
- **Peak memory.** The same rule, with a threshold of 0.2 GiB on the median peak total RSS.
- **Phases** are described with d1, d2 and d, without a threshold.
- **Caches** (sizes, fill and release times, cached reads), task counts and file counts are
  described, not tested.

With two protocols per configuration, this is a descriptive rule, not a statistical test.

## 10. Acceptance criteria

The collector evaluates these for one batch (4.3). The batch's results are used only if all of them
hold:

1. **Code state:** every protocol JSON and `run.json` of the batch records the same
   `source_sha256` and `uv_lock_sha256`, with the hashed paths clean (3).
2. **Inputs:** each run's `verified_sha256` holds exactly the seven inputs of 2.2, each equal to the
   hash in the stride-7 `config.json`, and each run's `windows_config` equals that file. After the
   session, the seven hashes are computed once more and are unchanged.
3. **Settings and caches:** section 6, items 6.1 to 6.4, holds for every run of the used protocols.
4. **Results:** every run of the used protocols ended `ok` with zero check violations and left its
   four tables complete. Section 7 passes for every run of the used protocols.
5. **Completeness:** each of the six positions has a used protocol of the configuration that 2.3
   puts there. It started 4 of 4 runs and all of them ended `ok`. None stopped early, none was
   aborted, and no sample exceeded 4.80 GiB. The used protocols ran in position order, and every
   protocol in the batch appears in `positions.tsv`.

If criterion 1, 2 or 3 fails, no configurations are compared until the cause is found. Stops and
re-runs follow 3. Drift (8) and run conditions are not acceptance criteria; a departure from 3.2 is
recorded as a deviation, and the protocol's results are labeled with it.

## 11. Predictions

_Drafted with Claude Code (Opus 5.5) from the earlier records (2.5) and the mechanisms below;
reviewed and approved by the author on 2026-10-22, before any measured run, as the preregistered
hypotheses. The probe and the dry batches of 4.5 were not used: they ran on another window set and
are not formal measurements. Their protocol ids, which are their start times, were visible to
Claude Code: the first batch's before this section was written, the second's after the approval.
They were not used either. The predictions of the earlier experiments stay unchanged._

| | A: no cache | B: members | C: members and the four tables |
| --- | --- | --- | --- |
| Median `wall_excl_capture_s` | 26.5 s | 26.5 s | 27.0 s |
| Band: a median outside it contradicts the prediction | 21.2–31.8 s (±20%) | 21.2–31.8 s (±20%) | 21.6–35.1 s (−20% / +30%) |
| Peak total RSS, median of the measured runs (5); outside the range contradicts it | 2.5–2.9 GiB | 2.5–2.9 GiB | 2.5–3.1 GiB |
| Abort a run above, on the watcher's raw elapsed time, plan capture included (3) | 80 s | 80 s | 81 s |

The abort limits are three times the predicted medians, rounded: 3 × 26.5 s ≈ 80 s and
3 × 27.0 s = 81 s.

### 11.1 Expected caches

- **Sizes** (Claude Code's arithmetic from the schemas, not a measurement): the members about
  13–15 MB; `path_days` about 0.19 GiB; `window_stats`, `path_summary` and `paired` under 3 MB
  each. Every cache entirely in memory, with 0 bytes on disk.
- **Fill times:** the members 0.3–1.2 s; `path_days` 0.3–1.5 s; each of the three small tables
  under 0.3 s. Each release under 0.1 s.
- **Files:** 1, 40, 8 and 1 in all three configurations, as in the shuffle-partition experiment's
  A, since each table is written before it is cached.
- **Outputs:** every run's four tables equal the reference's exactly, with no floating-point
  difference.

### 11.2 Expected comparisons (section 9)

- No clear difference in wall time between any two configurations.
- No clear difference in peak memory between any two configurations.
- Phases, described without a threshold: B's `window_stats_and_construction_check` longer than A's
  and its `model_and_path_days` shorter; C's `model_and_path_days` longer than B's, and C's `checks`
  shorter than A's and B's.

### 11.3 Basis

- **A** has the Spark settings of configuration A of the shuffle-partition experiment and of the
  baseline's S (2.5): medians of 26.462 s (`wall_excl_capture_s`) and 26.407 s (`wall_s`, without
  plan capture). The caching code adds four storage readings at the phase ends, which should take
  milliseconds. The ±20% band is the earlier experiments' (partition-experiment.md 11.3): there,
  the repeated stride-21 protocol's median was 18.3% below the first's.
- **B against A.** In A, each build of the members reads the window definitions and the returns,
  numbers the returns per ticker (a shuffle and sort of about 39,000 rows), broadcasts them, and
  expands the 5,364 windows into 1,351,728 rows. A builds them twice, B once, in its fill, and B
  reads them from memory in both phases.
  - B's `window_stats` gains the fill: encoding the rows into Spark's in-memory columns, in a query
    of its own. The returns are numbered as often as in A, since the statistics also join the
    prices to the windows.
  - B's `model` loses one build of the members.
  - **Assumption:** each effect is 0.3–1.0 s, so they nearly cancel. Both are small next to the
    8.435 s of A's `model_and_path_days`, which also runs the per-window simulation and writes
    2,698,866 rows.
- **C against B.** Because of the read-back, later phases read compact local Parquet files, not
  recomputed tables. Caching the four tables replaces those reads with reads from memory: one read
  of `path_days` in the summaries, the pairing's reads, and 14 reads in the checks.
  - Costs: four more fills, each a query of its own (30 SQL executions against B's 26), the largest
    over `path_days`'s 2,698,866 rows; and about 0.2 GiB of the 1 GiB heap held from `model` to the
    end of `checks`, which may add garbage collection.
  - **Assumption:** the four fills cost 0.5–2 s together, and the memory reads save 0.3–1.5 s of
    A's 6.462 s of summaries and 1.607 s of checks. The net is about +0.5 s, so 27.0 s. The band is
    skewed upward because part of `path_days` may go to disk, or garbage collection may cost more,
    if the sizes below are underestimated.
- **Sizes and the storage share.** Spark's in-memory columns store doubles uncompressed, 8 bytes
  each, and compress integers, dates and strings that repeat or change in small steps. `path_days`
  has 9 double columns of 16, so about 75 bytes per row, 0.19 GiB in all; the members have 1 double
  column of 7, about 10 bytes per row. With Spark's defaults, 300 MiB of the 1 GiB heap is reserved
  and 60% of the rest, about 434 MiB, is shared by execution and storage; cached data keeps at least
  half of it, about 217 MiB, against execution's demands. C holds the most during its `path_days`
  fill, when the members and `window_stats` are still cached: about 0.2 GiB, well inside the 434 MiB
  and close to the protected 217 MiB. **Assumption:** the later phases need little execution memory,
  so no cache is pushed to disk.
- **Memory.** In the stride experiment, the JVM's maximum heap was 1.000 GiB in every run, and its
  median peak RSS stayed between 1.518 and 1.571 GiB from stride 21 to stride 3, while the windows
  grew about seven times (experiments.md 6.3).
  - **Assumption:** the heap is fully committed at the peak in every configuration, so caching
    changes what the heap holds, not the JVM's RSS. The Python workers and the Python driver do the
    same work in all three configurations.
  - C's upper edge allows 0.2 GiB more, the size of its largest cache, in case this assumption
    fails.
- **Outputs.** Caching changes neither the partitions nor the order in which rows reach an
  aggregation: each cache has the partitions of the query that filled it, and each cached table
  those of its read-back. In the shuffle-partition experiment, A's seven other runs had no
  difference from their reference in `paired` and `path_summary`, the two tables compared there in
  full (partition-experiment.md 14.9).
- **Caution.** If machine conditions differ from those of the earlier batches, all three medians
  may move together. The comparisons of section 9 are relative and less affected.

## 12. Deferred

- other storage levels: memory only, serialized, off-heap;
- caching other data, such as the returns or the window definitions, and checkpointing instead of
  the write and read-back;
- a larger driver heap (`spark.driver.memory`);
- other workloads, for example strides 21 and 14;
- caches filled by their first reader instead of an explicit `count()`;
- garbage collection, CPU time and spill, and Spark's event log.

## 13. Origin of the design

The author's decisions and approvals are in 1.2. Everything else was proposed by Claude Code:

- **2.1 and 2.4:** which tables each configuration caches, where each cache is filled and released,
  and passing `--cache none` and `--record-plans` in all three configurations.
- **3:** reusing the shuffle-partition experiment's rules, writing the 3.2 checks at every start,
  and the branch.
- **4:** the code:
  - the `--cache` option, its storage level, the explicit fill and blocking release, the cleanup,
    and the `cache` section of `run.json`;
  - the description that names each fill's SQL execution, and plans format 2 with descriptions and
    scan nodes;
  - the collector and its reuse of the shuffle-partition collector, and how it reports a run's
    missing outputs, using Spark's `_SUCCESS` marker;
  - the helpers, and the probe and dry batches of 4.5.
- **5–10:**
  - the time metric, with the fills, releases and storage readings inside it, and the
    observations;
  - the storage checks, the three states of a read's row metric, and the rules for fills and
    downstream reads that carry out the author's decision on 6.4;
  - the reference run and the full comparison of all four tables;
  - the drift and comparison rules and the acceptance criteria, from the shuffle-partition
    experiment.
- **11:** the draft of the predictions, which the author approved.
- **12:** the contents of the deferred list.

_Part A ends here; it was committed before any measured run (`6131f83`)._

## 14. Results

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from batch-1's run log and `positions.tsv`, the
six protocol JSONs, the 24 `run.json` and `plans.json` files and their output tables,
`measurements.csv` and `acceptance.json` (numbers read by script), the author's terminal output from
both windows, and the author's statements (14.2, 14.3). Times are UTC on 2026-10-22: the six
protocols ran from 20:28:56 to 21:43:13. Differences and percentages are computed from unrounded
values, so they can differ by 0.001 from those of the rounded values shown. This section gives facts
only; the answers are in section 15._

### 14.1 Protocols

| Position | Configuration | Protocol | Runs (UTC) | Status |
| ---: | --- | --- | --- | --- |
| 1 | A | `20261022T202856Z` | 20:28:56–20:30:47 | 4 of 4 `ok` |
| 2 | B | `20261022T210120Z` | 21:01:20–21:03:14 | 4 of 4 `ok` |
| 3 | C | `20261022T210843Z` | 21:08:43–21:10:43 | 4 of 4 `ok` |
| 4 | C | `20261022T211604Z` | 21:16:04–21:18:04 | 4 of 4 `ok` |
| 5 | B | `20261022T212322Z` | 21:23:22–21:25:15 | 4 of 4 `ok` |
| 6 | A | `20261022T214123Z` | 21:41:23–21:43:13 | 4 of 4 `ok` |

- All 24 runs ended `ok` with zero check violations. No protocol stopped early, no run was aborted,
  and no sample crossed the 4.80 GiB threshold. Each position ran once, so nothing was re-run and
  every protocol is a used protocol (3).
- **Acceptance (10):** the collector found all five criteria met and listed no problem. Batch-1 is
  therefore the analyzed batch, and no further batch runs (3).
- **Code state (3):** every protocol and run record shows commit `6131f83`, Part A's commit, with
  the hashed paths clean, and the same `source_sha256` (12 files) and `uv_lock_sha256` (starting
  `99484c14ebf3`).
- **Inputs (2.2):** every run verified the seven SHA-256 values before Spark started and recorded a
  `windows_config` equal to the stride-7 `config.json`. When the collector ran after the session,
  the seven files still had those hashes.
- **Settings (6.1):** every run records its configuration's `pipeline_options` and Spark's defaults
  for the three partition settings. Every other recorded Spark setting, and the recorded
  environment, are identical in all 24 runs.
- **Plans (6.2):** captured in all 24 runs, ids 0 to n−1 without gaps: 25 SQL executions in A, 26 in
  B and 30 in C. In every run, every plan is adaptive and final except one, the `CreateViewCommand`
  without jobs in `summaries`, which is not adaptive. No execution ended with an error. Plan capture
  took 1.062–1.429 s per run.
- **Caches (6.3, 6.4):** the check after each protocol and the collector found every run's storage
  information, fills and downstream reads as 6.3 and 6.4 require (14.8).
- **Records:** `data/outputs-caching/batch-1/`, laid out as in 2.4.

### 14.2 Run log

The session used the helpers of 4.4, `docs/caching-session.zsh` as committed in `623fe32` (SHA-256
starting `b4872ee768f0c4bc`), loaded in two Terminal windows: window 1 ran the checks, pauses,
readings and protocols, and window 2 the watcher. Each protocol started right after a five-minute
pause and a `ready` reading that met all three limits of 3.2, and `position` wrote the 3.2 checks
into the run log at each start. Before each pause, the author also ran `prechecks` by hand.

| Position | Checks by hand | Pause before the start | Available at the start (GiB) | 5-minute load at the start | Minutes since boot | Lowest free before a run (GiB) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1, A | 20:23:50 | 20:23:54–20:28:54 | 4.33 | 1.27 | 44 | 3.18 |
| 2, B | 20:56:12 | 20:56:17–21:01:18 | 3.55 | 1.37 | 76 | 2.66 |
| 3, C | 21:03:39 | 21:03:43–21:08:43 | 3.91 | 2.36 | 84 | 2.71 |
| 4, C | 21:10:58 | 21:11:03–21:16:03 | 3.95 | 2.16 | 91 | 2.64 |
| 5, B | 21:18:17 | 21:18:22–21:23:22 | 4.11 | 2.12 | 99 | 3.15 |
| 6, A | 21:36:17 | 21:36:22–21:41:22 | 3.88 | 1.37 | 117 | 2.75 |

At every start, the checks that `position` wrote show Low Power Mode off, AC power, no Docker
backend, no Java or pipeline process, only Terminal and Finder open, `HEAD 6131f83` with no changed
code file, and no Spark scratch folder. The last column is the lowest `free_memory_before_bytes`
among each protocol's four runs. Eight runs started with less than 3.0 GiB free; as in the earlier
experiments, 3.2 requires 3.0 GiB only before a protocol starts.

- **Before position 1:** the run log begins with a pause (19:38:21–19:43:21) and three readings,
  1,215 minutes after the previous boot, with 2.57–2.66 GiB available and a 5-minute load of
  4.91–5.13, so nothing started. The author restarted the Mac because the available memory was
  below the 3.0 GiB limit. The checks at 19:46:21, two minutes after the boot, showed Low Power Mode
  on and load averages of 51.53, 32.10 and 13.59; the author turned Low Power Mode off during the
  readings that followed. After a pause (19:46:31–19:51:31), 13 readings 7 to 37 minutes after the
  boot each failed at least one limit (1.83–2.99 GiB available; a 5-minute load falling from 12.46
  to 1.39), and a reading at 39 minutes met all three. Of these 17 readings, two came right after a
  pause, so two starts were refused; the other 15 were run on their own. The checks by hand at
  20:23:50 showed Low Power Mode off, and position 1 started after a further pause, 44 minutes after
  the boot.
- **Between positions:** the protocols started 32, 7, 7, 7 and 18 minutes apart. After position 1,
  whose runs ended at 20:30:47, the next checks came at 20:56:12; after position 5, whose runs ended
  at 21:25:15, at 21:36:17. The author left the computer idle during both gaps and ran no other
  programs. The checks by hand right after positions 2, 3 and 4 showed 1-minute loads of 6.98, 6.05
  and 5.96, from the protocols just finished; after each pause, the 5-minute load at the start was
  1.27–2.36.
- **Abort rule:** no run came near its limit. The longest raw wall times were 28.6 s (A), 29.3 s (B)
  and 30.5 s (C), against 80, 80 and 81 s. The watcher saw all 24 pipeline processes, four per
  protocol, and its largest readings were 26, 28 and 25 s. No abort and no after-abort check was
  needed.
- **A typo:** before position 6, `prechecks` typed with a closing curly quote left zsh waiting for
  the end of the quote; nothing ran, and the author entered the command again.
- **Notes:** after each protocol, the author recorded `4 ok, nothing unusual` with `note`.
- **After the session:** a check at 22:05 found no Spark scratch folder and no Java process.

### 14.3 Deviations and uncertain conditions

There was no departure from 3.2 at any protocol start: the checks that `position` wrote, and the
reading just before each start, met every condition (14.2). One condition is uncertain:

1. **Uneven spacing.** Positions 2 and 6 started 32 and 18 minutes after the positions before them,
   the others 7 minutes apart, so the spacing that the drift reasoning of 2.3 assumes is far from
   even. The run log does not record the Mac's state in the two gaps; the author states that the
   computer was idle and ran no other programs.

Low Power Mode was on in the checks at 19:46:21, before any protocol, and off in every check from
20:23:50 on (14.2).

### 14.4 Drift (section 8)

| Rule | Positions | Protocol medians of `wall_excl_capture_s` | Difference from the first | Median peak total RSS (GiB) | Difference |
| --- | --- | --- | --- | --- | --- |
| 1. Session drift: A | 1, 6 | 26.296, 26.613 s | +0.317 s (+1.21%) | 2.684, 2.678 | −0.006 GiB |
| 2. Pair: B | 2, 5 | 27.130, 26.940 s | −0.190 s (−0.70%) | 2.675, 2.681 | +0.007 GiB |
| 2. Pair: C | 3, 4 | 28.810, 28.633 s | −0.177 s (−0.61%) | 2.695, 2.701 | +0.006 GiB |

No time difference exceeds 10% of the first median, so no drift is reported under rules 1 and 2,
and no memory difference exceeds 0.2 GiB (rule 3). The context of rule 4 is in 14.2 and 14.3.

**Earlier records (rule 5, descriptive).** A's six measured runs have a median
`wall_excl_capture_s` of 26.485 s (raw `wall_s` 27.581 s; `plan_capture_s` 1.083 s) and a median
peak total RSS of 2.683 GiB. The shuffle-partition experiment's A (2.5) had 26.462 s (raw 27.376 s;
plan capture 0.897 s) and 2.689 GiB. A's summed stage task counts (53, 22, 81 and 100) and file
counts (1, 40, 8 and 1) equal that configuration's in all eight runs.

### 14.5 Measurements CSV

**Location.** `uv run python analysis/collect_caching_measurements.py --batch
data/outputs-caching/batch-1` reads the batch's records and writes `measurements.csv` and
`acceptance.json` into the batch folder (4.3). Like the records, they are under `data/`, which is
not in Git. Rebuilding both from the records gives byte-identical files.

**Rows.** One row per started run: 24 rows, warm-ups included, in position order. `used` marks the
runs of the used protocols, here all 24.

**Columns.** 79: the 10 identity columns, the 29 measurement columns of the stride experiment's CSV
(experiments.md 5.6), and these 40:

| Group | Columns | From |
| --- | --- | --- |
| Caching and timing | `cache_mode`; `plan_capture_status`; `plan_capture_s`; `wall_excl_capture_s`, which is `wall_s − plan_capture_s` rounded to milliseconds (5); `sql_executions`; `fill_executions`; `storage_info_s` | `cache`, `plan_capture` and `timings_seconds` in `run.json`; `plans.json` |
| Caches | for each of the five cacheable tables: `fill_s`, `release_s`, and `memory_bytes` and `disk_bytes` right after its fill | `cache` in `run.json` |
| Downstream reads | `cached_reads_<phase>` for the four phases and bookkeeping: positive/zero/missing, the fills excluded (6.4) | `plans.json` |
| Files | `files_window_stats`, `files_path_days`, `files_path_summary`, `files_paired`: the Parquet files of each output table | the run folder |
| Comparison (7) | `<table>_vs_reference` for the four tables: `reference`, `pass`, `fail`, `missing`, `incomplete`, `unreadable` or `no reference` | the tables |

**Limitations.** Those of experiments.md 5.6 apply: task counts are summed stage task counts, and
memory is sampled RSS. Each cache's bytes are Spark's storage information right after its fill.

### 14.6 Summary tables

_Drafted with Claude Code (Opus 5.5) from `measurements.csv` (values computed by script)._

Summaries use the measured runs that ended `ok` in the used protocols (5): three per protocol, six
per configuration. Each cell gives the median and, in brackets, the minimum and maximum. Peak memory
is `peak_rss_total_bytes` in GiB (2^30 bytes).

**By protocol**

| Position | Configuration | Protocol | `wall_excl_capture_s` (s) | `wall_s` (s) | `plan_capture_s` (s) | Peak total RSS (GiB) |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | A | `20261022T202856Z` | 26.296 (26.127–26.623) | 27.358 (27.222–27.693) | 1.070 (1.062–1.095) | 2.684 (2.682–2.687) |
| 2 | B | `20261022T210120Z` | 27.130 (26.747–27.257) | 28.299 (27.928–28.402) | 1.169 (1.145–1.181) | 2.675 (2.669–2.684) |
| 3 | C | `20261022T210843Z` | 28.810 (28.605–29.135) | 30.207 (30.034–30.512) | 1.397 (1.377–1.429) | 2.695 (2.688–2.702) |
| 4 | C | `20261022T211604Z` | 28.633 (28.346–28.842) | 30.014 (29.767–30.212) | 1.381 (1.370–1.421) | 2.701 (2.693–2.713) |
| 5 | B | `20261022T212322Z` | 26.940 (26.663–28.207) | 28.095 (27.811–29.337) | 1.148 (1.130–1.155) | 2.681 (2.667–2.690) |
| 6 | A | `20261022T214123Z` | 26.613 (26.357–26.624) | 27.695 (27.468–27.726) | 1.111 (1.071–1.113) | 2.678 (2.663–2.694) |

**By configuration** (six measured runs; the largest peak covers all eight runs, warm-ups included)

| Configuration | `wall_excl_capture_s` (s) | `wall_s` (s) | `plan_capture_s` (s) | Peak total RSS (GiB) | Largest peak (GiB) |
| --- | --- | --- | --- | --- | ---: |
| A: no cache | 26.485 (26.127–26.624) | 27.581 (27.222–27.726) | 1.083 (1.062–1.113) | 2.683 (2.663–2.694) | 2.694 |
| B: members | 27.035 (26.663–28.207) | 28.197 (27.811–29.337) | 1.151 (1.130–1.181) | 2.678 (2.667–2.690) | 2.690 |
| C: members and the four tables | 28.721 (28.346–29.135) | 30.120 (29.767–30.512) | 1.389 (1.370–1.429) | 2.698 (2.688–2.713) | 2.713 |

**Phases and peaks by process type** (medians of the six measured runs; each median is taken on its
own, so the phases do not add up to the total)

| | A | B | C |
| --- | ---: | ---: | ---: |
| `session_start` (s) | 2.476 | 2.469 | 2.468 |
| `window_stats_and_construction_check` (s) | 4.933 | 5.865 | 5.944 |
| `model_and_path_days` (s) | 8.534 | 8.205 | 9.490 |
| `summaries_and_pairing` (s) | 6.509 | 6.676 | 6.909 |
| `checks` (s) | 1.646 | 1.548 | 1.547 |
| `total_in_process` (s), plan capture included | 26.640 | 27.371 | 28.942 |
| Spark JVM peak (GiB) | 1.523 | 1.521 | 1.557 |
| Python workers peak (GiB) | 1.048 | 1.055 | 1.050 |
| Python driver peak (GiB) | 0.115 | 0.114 | 0.114 |

### 14.7 Comparisons (section 9)

_Drafted with Claude Code (Opus 5.5) from `measurements.csv`. For configurations X and Y,
d = X − Y between medians of measured runs: d1 in positions 1–3, d2 in positions 4–6, and d over the
six runs of each. The time threshold is 10% of A's six-run median, 2.649 s; the memory threshold is
0.2 GiB._

| X − Y | Measure | d1 | d2 | d | Same sign | Beyond the threshold | Rule (9) |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| A − B | `wall_excl_capture_s` (s) | −0.834 | −0.327 | −0.550 | yes | no | no clear difference |
| B − C | `wall_excl_capture_s` (s) | −1.680 | −1.693 | −1.686 | yes | no | no clear difference |
| A − C | `wall_excl_capture_s` (s) | −2.514 | −2.020 | −2.236 | yes | no | no clear difference |
| A − B | peak total RSS (GiB) | +0.009 | −0.004 | +0.005 | no | no | no clear difference |
| B − C | peak total RSS (GiB) | −0.020 | −0.020 | −0.020 | yes | no | no clear difference |
| A − C | peak total RSS (GiB) | −0.011 | −0.023 | −0.015 | yes | no | no clear difference |

B's six-run median is 2.1% above A's (0.550 s), C's 6.2% above B's (1.686 s) and 8.4% above A's
(2.236 s), all below the threshold. In all three time comparisons, d1, d2 and d have the same sign:
B and C were slower than A, and C slower than B, in both halves.

**Phases** (described without a threshold; seconds)

| Phase | A − B: d1, d2, d | B − C: d1, d2, d | A − C: d1, d2, d |
| --- | --- | --- | --- |
| `session_start` | +0.013, +0.017, +0.007 | −0.048, +0.032, +0.001 | −0.034, +0.049, +0.008 |
| `window_stats_and_construction_check` | −0.991, −0.802, −0.932 | −0.064, −0.138, −0.079 | −1.055, −0.940, −1.011 |
| `model_and_path_days` | +0.096, +0.463, +0.329 | −1.220, −1.246, −1.285 | −1.124, −0.783, −0.956 |
| `summaries_and_pairing` | −0.400, −0.086, −0.167 | −0.105, −0.362, −0.233 | −0.505, −0.447, −0.400 |
| `checks` | −0.054, +0.248, +0.097 | +0.091, −0.062, +0.001 | +0.038, +0.186, +0.099 |
| `total_in_process` | −1.054, −0.374, −0.731 | −1.704, −1.729, −1.571 | −2.758, −2.103, −2.302 |

In both halves, B's `window_stats_and_construction_check` and `summaries_and_pairing` were longer
than A's and its `model_and_path_days` shorter; C's `window_stats_and_construction_check`,
`model_and_path_days` and `summaries_and_pairing` were longer than B's; and C's `checks` was shorter
than A's. The `checks` of A and B, and of B and C, change sign between the halves, as does
`session_start` in two of the three pairs.

### 14.8 Caches and plans (sections 5 and 6)

_Drafted with Claude Code (Opus 5.5) from the `run.json` and `plans.json` files and the CSV. Every
count is the same in all eight runs of a configuration; times are medians (minimum–maximum) of the
six measured runs, and MB is 10^6 bytes._

| | A: no cache | B: members | C: members and the four tables |
| --- | --- | --- | --- |
| SQL executions; fills among them | 25; none | 26; 1 | 30; 5 |
| Downstream cached reads in `window_stats`, `model`, `summaries`, `checks` | 0, 0, 0, 0 | 1, 1, 0, 0 | 2, 1, 3, 14 |
| Cached RDDs at the four phase ends | 0, 0, 0, 0 | 1, 0, 0, 0 | 2, 2, 4, 0 |
| Summed stage task counts: `window_stats`, `model`, `summaries`, `checks` | 53, 22, 81, 100 | 57, 11, 81, 100 | 61, 36, 110, 100 |
| Files: `window_stats`, `path_days`, `path_summary`, `paired` | 1, 40, 8, 1 | 1, 40, 8, 1 | 1, 40, 8, 1 |
| Storage readings (`storage_info_s`) | 0.002 s | 0.008 s | 0.031 s |

| Cached data | Rows | Partitions | In memory (MB) | On disk | Fill in B (s) | Fill in C (s) | Release (s) |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| members | 1,351,728 | 1 | 13.77 | 0 | 2.481 (2.441–2.824) | 2.467 (2.424–2.559) | 0.003–0.005 |
| `window_stats` | 5,364 | 1 | 0.48 | 0 | — | 0.137 (0.129–0.176) | at most 0.001 |
| `path_days` | 2,698,866 | 8 | 202.21 | 0 | — | 1.325 (1.135–1.455) | at most 0.001 |
| `path_summary` | 10,728 | 8 | 1.03 | 0 | — | 0.093 (0.081–0.121) | at most 0.001 |
| `paired` | 5,364 | 1 | 0.91 | 0 | — | 0.075 (0.073–0.076) | at most 0.001 |

- **Storage (6.3):** in every run, each fill counted its table's rows and added one RDD, with all of
  its partitions cached at the level "Disk Memory Deserialized 1x Replicated" and every byte in
  memory. Each cache was still fully cached just before its release, was released by the plan in
  its phase, and was no longer listed afterwards. In C, the storage information at the phase ends
  shows 14.25 MB cached at the end of `window_stats`, 202.69 MB at the end of `model`, 204.63 MB at
  the end of `summaries` and none at the end of `checks`. Between the `path_days` fill and the
  members' release, the members, `window_stats` and `path_days` were cached together: 216.46 MB by
  the sizes after their fills.
- **Fills and downstream reads (6.4):** every fill's execution carried its description and read its
  cache once, in its table's phase. All 48 fill reads and all 176 downstream reads recorded a
  positive row metric; none was zero or missing. The only missing row metrics, 32, were on
  `Scan parquet` nodes of executions that read cached data: the nested file scans of 4.2.
- **Shuffle reads:** in every run, AQE coalesced the model's group-by read to 8 partitions, and the
  summaries' reads to 8, 9, 1 and 1 partitions. In A, the model phase also read the shuffle of the
  returns' window by `ticker`, coalesced to 1; in B and C, the cached members replaced that part of
  the model's plan.

### 14.9 Output comparison (section 7)

_Drafted with Claude Code (Opus 5.5) from `acceptance.json`, from the collector's comparison
function run per configuration, and from the `path_days` files of all 24 runs._

**Reference:** run 2 of position 1, `run-20261022T202856Z-2`. All 23 other runs pass in all four
tables: the reference's row counts (5,364, 2,698,866, 10,728 and 5,364) and keys, with no null or
duplicate key; the same columns and types; NULLs in the same rows; breach fields and the other
non-floating columns equal exactly. No table was missing, incomplete or unreadable.

**Floating-point columns:**

| Configuration | Runs compared | Runs with any difference | Largest absolute difference: `paired`, `path_summary` | Largest relative difference: `paired`, `path_summary` |
| --- | ---: | ---: | --- | --- |
| A | 7 | 0 | 0, 0 | 0, 0 |
| B | 8 | 8 | 7.11e-15, 3.64e-12 | 6.25e-16, 6.25e-16 |
| C | 8 | 8 | 7.11e-15, 3.64e-12 | 6.25e-16, 6.25e-16 |

In B and C, the same seven columns differ: in `paired`, `total_turnover_2x`,
`total_turnover_2x_pre_breach`, `mean_turnover_2x` and `mean_turnover_2x_pre_breach`; in
`path_summary`, `total_turnover`, `mean_turnover` and `total_abs_rebalance`. Every other
floating-point column of these two tables, and every column of `window_stats` and `path_days`, is
equal exactly in every run. Every difference is within the tolerance of section 7.

**Row order of `path_days`.** In every run, each of the 40 `path_days` files holds the same rows as
the reference's file at the same place. In A's seven other runs, all 40 files hold them in the same
order; in each of the 16 runs of B and C, 9 of the 40 files hold them in another order. The seven
differing columns are sums and means over a path's rows, and the result of a floating-point sum
depends on the order of its terms. The records do not show why caching the members changes the
order of the rows that the model phase writes.

## 15. Answers and limits

_The questions are Claude Code's proposals of 2026-10-22. In 15.1–15.4, the parts marked as drafted
give facts, computed with Claude Code (Opus 5.5) by script from batch-1's records (14) and from
section 11, which is unchanged. The answers, marked "Answer (author)", are the author's, copied from
the conversation of 2026-10-22._

### 15.1 (a) Runtime

> How did caching the members (B) and also the four tables (C) change wall time, under the rule of
> section 9?

_Drafted with Claude Code (Opus 5.5): the medians are in 14.6, and d1, d2 and d by pair and by phase
in 14.7._

**Answer (author).** B and C were slightly slower than A, but the differences were below the
predefined threshold. Under the rule in section 9, there was no clear difference in runtime.

### 15.2 (b) Phases and caches

> Where did time move between phases, and what did the fills cost against what the cached reads
> saved?

_Drafted with Claude Code (Opus 5.5): the phases are in 14.6 and 14.7, and the fills, releases and
reads in 14.8._

**Answer (author).** B's window-statistics phase was 0.93 s longer than A's, while its model phase
was 0.33 s shorter. The members fill took about 2.48 s, including data construction, so this was
not all additional work. Compared with B, C's model phase increased by 1.29 s, with no net speedup
in summaries or checks. Overall, the observed savings did not offset the added costs.

### 15.3 (c) Memory and results

> Did caching change peak memory or any result?

_Drafted with Claude Code (Opus 5.5): peak memory is in 14.6 and 14.7, the caches' sizes in 14.8,
and the output comparison in 14.9._

**Answer (author).** Peak memory differed only slightly. All outputs passed the tolerance checks,
although some floating-point summary values were not exactly equal.

### 15.4 (d) Predictions against results

> Where were the predictions off, and why?

_Drafted with Claude Code (Opus 5.5) from section 11, which is unchanged, and from section 14. Time
items use the medians of `wall_excl_capture_s` over the six measured runs, and memory items the
medians of peak total RSS._

| Section 11 | Predicted | Measured | Result |
| --- | --- | --- | --- |
| A, median time | 26.5 s, band 21.2–31.8 s | 26.485 s | inside, 0.1% below the point |
| B, median time | 26.5 s, band 21.2–31.8 s | 27.035 s | inside, 2.0% above the point |
| C, median time | 27.0 s, band 21.6–35.1 s | 28.721 s | inside, 6.4% above the point |
| A, B and C, median peak | 2.5–2.9, 2.5–2.9 and 2.5–3.1 GiB | 2.683, 2.678 and 2.698 GiB | inside |
| Abort limits | 80, 80 and 81 s | longest runs 28.6, 29.3 and 30.5 s | no run aborted |
| 11.1, sizes | members 13–15 MB; `path_days` about 0.19 GiB; the small tables under 3 MB each; nothing on disk | 13.77 MB; 0.188 GiB (202.21 MB); 0.48, 1.03 and 0.91 MB; 0 bytes on disk | as predicted |
| 11.1, fill and release times | members 0.3–1.2 s; `path_days` 0.3–1.5 s; the small tables under 0.3 s each; releases under 0.1 s | members 2.481 s (B) and 2.467 s (C); `path_days` 1.325 s; 0.075–0.137 s; releases at most 0.005 s | members above the range; the others as predicted |
| 11.1, files | 1, 40, 8 and 1 | 1, 40, 8 and 1 in all 24 runs | as predicted |
| 11.1, outputs | equal to the reference exactly | A equal; in all B and C runs, seven columns differ in the last bits (relative at most 6.25e-16), within the tolerance | not as predicted for B and C |
| 11.2, wall time | no clear difference between any two | d = −0.550 s (A − B), −1.686 s (B − C) and −2.236 s (A − C), all below the 2.649 s threshold | as predicted |
| 11.2, memory | no clear difference between any two | \|d\| at most 0.020 GiB | as predicted |
| 11.2, phases | B's `window_stats` longer and `model` shorter than A's; C's `model` longer than B's; C's `checks` shorter than A's and B's | +0.932 s and −0.329 s; +1.285 s; C − A −0.099 s, shorter in both halves, and C − B −0.001 s, with the halves differing in sign | as predicted, except C's `checks` against B's |
| 11.3, B's two effects | each 0.3–1.0 s, nearly cancelling | `window_stats` +0.932 s, `model` −0.329 s; B − A +0.550 s in all | each inside the range |
| 11.3, C against B | fills 0.5–2 s together; memory reads save 0.3–1.5 s; net about +0.5 s | fills 1.630 s (the sum of their medians); `summaries` +0.233 s and `checks` −0.001 s; net +1.686 s | fills inside; no observed net saving in these phases; net larger |
| 11.3, heap | the caches change what the heap holds, not the JVM's RSS | Spark JVM peak 1.557 GiB in C, 1.521 in B, 1.523 in A | C +0.034 GiB above A |

**Answer (author).** I underestimated the members fill time, and the prediction of exact equality
did not hold. A different order of floating-point addition is a plausible explanation, but the
specific mechanism has not been established. C's additional caching also produced less net benefit
than expected, and its checks were not consistently faster than B's.

### 15.5 (e) What these measurements cannot show

> What can these measurements not show?

**Answer (author).** These results apply to this machine, workload and caching strategy. CPU time
and garbage collection were not measured, so the conclusions cannot be generalized to all Spark
workloads.

## History of this document

**Draft** (2026-10-22): the design from the author's decisions and the plan of 2026-10-22, the code
and its validation, and the predictions, for the author's review. After the dry batch, the
cached-read rule (6.4) was tightened from "at least one cached read in each phase that reads cached
data" to the exact counts per phase, because each fill's own `count()` already counts as a cached
read in its phase.

**Revision 1** (2026-10-22), after the author's review of the draft:

- The author approved the A/B/C design and the predictions and abort limits of section 11 as the
  preregistered hypotheses. The limits were set in the helpers (4.4), and the author's authorship
  line was added.
- At the author's request, 6.4 verifies the downstream reads apart from the fills and no longer
  requires the numbers of reads found in the dry batch. Each fill's SQL execution now carries a
  description that names it (4.1, 4.2).
- At the author's request, the collector reports a failed or aborted run's missing, incomplete or
  unreadable tables and plans, and a reference run's missing table, under the acceptance criteria
  instead of stopping (4.3, 7, 10).
- A second dry batch ran with the revised code (4.5).

The author approved this version for commit on 2026-10-22. It is committed before any measured run,
together with the code of section 4, on `feature/caching`.

**Part B** (2026-10-22). Section 14 gives batch-1's results as facts, with the author's statements
in 14.2 and 14.3, and section 15 the author's answers, with facts drafted by Claude Code. After
Claude Code's review of the answers, the author added the last sentence of (d) and had one result in
15.4 changed to "no observed net saving in these phases". The status at the top now describes both
parts, the authorship line states that the author ran the formal measurements and wrote the answers,
and a line marks the end of Part A; sections 1–13, the predictions included, are unchanged. This
version is committed on `feature/caching` after the formal session.
