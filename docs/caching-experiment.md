# Caching experiment

Author: I decided the configurations and rules listed in 1.2, reviewed and approved the rest of the
design and the predictions, and will run the formal measurements and write the Part B answers. AI
contributions are described below.

**Part A (sections 1–13): the design, the code and the predictions, committed before any measured
run.** The author approved the design, the predictions and the abort limits (section 11) on
2026-10-22 as the preregistered hypotheses, and runs the formal measurements (2.4, 4.4). No formal
measurement has been made yet; the code was validated on a small window set (4.5). Part B (results
and answers) will follow section 13. The history of this document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the records of the shuffle-partition experiment and the
pandas baseline. Everything not listed in 1.2 as decided by the author is Claude Code's proposal
(section 13). The predictions in section 11 were drafted with Claude Code and reviewed and approved
by the author. Revision 1 applied the author's review of the draft (history at the end)._

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
