# Pandas baseline

**Part A: the design, the code and the predictions, committed before any measured run.** The
author approved the predictions (section 11) and the rules listed in 1.2 on 2026-10-22, and runs the
formal measurements (2.4, 4.4). No formal measurement has been made yet; the code was validated on
small window sets (4.5). Part B (results and answers) will follow section 13. The history of this
document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the records of the stride and shuffle-partition
experiments. Everything not listed in 1.2 is Claude Code's proposal (section 13). The predictions in
section 11 were drafted with Claude Code and reviewed and approved by the author. The author's own
authorship line is still to be added._

This experiment changes neither the stride experiment ([experiments.md](experiments.md)) nor the
shuffle-partition experiment ([partition-experiment.md](partition-experiment.md)), nor their
predictions, records or collectors. It writes only under `data/outputs-baseline/`.

## 1. Question and decisions

### 1.1 Question

For the stride-7 workload, how do the Spark pipeline and a single-process pandas implementation of
the same computation compare end to end, in wall time, peak memory and results? This tests the last
hypothesis of expectation 5 (spec §8): "A single-process pandas run may be faster at these sizes."
The data, model, window set, leverages, outputs and checks stay fixed; the implementation changes.
The machine is the earlier experiments' (Apple M2 MacBook Air, 8 cores, 8 GiB RAM).

This is an end-to-end comparison of two implementations, not a measurement of engine overhead. Both
call the same model function for each window, so the model's arithmetic is the same. They differ in
how they build the window members, aggregate, run the checks and write their outputs, and in how
they use the machine:

- The Spark pipeline runs the per-window function in eight Python workers. It pays for a JVM, data
  transfer between the JVM and the workers, and shuffles.
- The pandas pipeline runs everything in one process on one core.

The measurements cannot attribute a difference to any one of these.

### 1.2 Decided by the author (2026-10-22)

- The single-process pandas baseline stays in Stage 3 and is done now.
- The stride-7 window set of the earlier experiments as the only workload (2.2).
- Order S–P–P–S, with four fresh-process runs per protocol: one warm-up, three measured, so 16 runs
  in all (2.3).
- The pandas pipeline computes the same results from the same inputs: the same checksum
  verification, the same four Parquet tables, the same ten checks and the same model function (4.1).
- The Spark side uses Spark's defaults, configuration A of the shuffle-partition experiment. Neither
  side records execution plans (2.1).
- The comparison is described as an end-to-end comparison of the two implementations. Sharing the
  model function does not isolate engine overhead from differences in data handling, aggregation
  and output writing (1.1).
- Approved after review: the predictions of section 11, drafted with Claude Code, and the abort
  limits of 80 s for S and 120 s for P, on the watcher's raw elapsed time.

## 2. Implementations, workload and order

### 2.1 Implementations

| Label | Pipeline | Settings | Role |
| --- | --- | --- | --- |
| S | `etf_risk.spark_pipeline` | Spark's defaults (200 shuffle partitions, AQE and its coalescing on), `local[*]`, as in the stride experiment | the pipeline of every earlier record |
| P | `etf_risk.pandas_pipeline` | one Python process, no Spark | the single-process baseline |

The records label the implementation as `engine` (the CSV, `positions.tsv` and the collector's
`--engine`), and P's `run.json` records `"engine": "pandas"`. S runs without any pipeline flag, so
its settings are unset and its `run.json` has no `pipeline_options`. Its recorded values equal
configuration A's (partition-experiment.md 2.1, 14.1), which set them explicitly. Neither
implementation passes `--record-plans`, so the time compared needs no correction for plan capture
(5).

### 2.2 Workload

The stride-7 set in `data/windows-experiments/full-2026-10-12/rolling-252-s7`, unchanged: 5,364
windows, 1,351,728 window-member rows and 2,698,866 path-day rows (experiments.md 2.2,
partition-experiment.md 2.2). Both pipelines verify its seven SHA-256 values before any work and
exit with code 3 on a mismatch.

### 2.3 Order and repeats

There are four protocols, at positions 1 to 4: S, P, P, S. Each protocol is one `etf_risk.measure`
call with `--repeats 4`: four fresh-process runs, the first a warm-up. Each implementation therefore
has two protocols, eight runs and six measured runs.

Each implementation's two positions average 2.5. If the protocols were evenly spaced, a drift that
changes linearly over the session would shift both implementations' means by the same amount; their
start times are reported (8). The P pair runs back to back. Section 9 shows why a linear drift alone
cannot produce a difference under its rule.

### 2.4 Commands and records

The session helpers (4.4) start each protocol by its position. The command they run, from the
repository root, is

```bash
caffeinate -i uv run --group measure python -m etf_risk.measure --pipeline <spark|pandas> --repeats 4 -- \
    --windows data/windows-experiments/full-2026-10-12/rolling-252-s7 \
    --out-root data/outputs-baseline/<batch>/<S|P>
```

Both implementations are started with `--pipeline`, so both protocol JSONs record their pipeline. A
batch (3) is one folder, `data/outputs-baseline/<batch>/`, starting with `batch-1`. It holds `S/`
and `P/`, each with `full-2026-10-12/rolling-252-s7/`: one protocol JSON per protocol, and one
folder and one `.log` per run. It also holds `positions.tsv`, `run-log.txt`, and the collector's
`measurements.csv` and `acceptance.json`.

## 3. Run conditions, batches and failures

The rules of partition-experiment.md 3.1–3.4, which the author approved for that experiment, apply
with these changes:

- **Batches (3.1).** A batch is one S–P–P–S sequence, run in one session under one code state. Every
  protocol JSON and `run.json` records the same `source_sha256` and `uv_lock_sha256`, with the
  hashed paths clean; the commit is only reported. Any change to `src/`, `pyproject.toml` or
  `uv.lock` ends the batch, and a new one starts at position 1.
- **Machine state (3.2).** Required before each protocol:
  - Low Power Mode off and mains power;
  - apps other than Terminal and Finder quit;
  - a 5-minute pause;
  - read just before the start: at least 3.0 GiB available, a 5-minute load average of at most 4.0,
    and at least 30 minutes since boot.

  New: `position` writes the 3.2 checks into the run log right before each start, so the run log
  shows the state at every start. In the shuffle-partition experiment they were recorded only once
  (partition-experiment.md 14.3).
- **Positions (3.3).** `positions.tsv` as there, with the implementation's label (`engine`) instead
  of the configuration.
- **Failures and retries (3.4).** The table of partition-experiment.md 3.4, with the abort limits of
  section 11 and without the plan-capture row. The check after each protocol verifies each run's
  implementation and settings (6) instead of its plans.
- **Branch.** `feature/pandas-baseline`, created from `8067426` on `feature/shuffle-partitions`, and
  later merged with merge commits.

## 4. Code

### 4.1 The pandas pipeline

`src/etf_risk/pandas_pipeline.py` takes the Spark pipeline's arguments (`--windows`, `--out-root`,
`--run-id`, `--initial-nav`), verifies the same checksums and writes the same run folder. It never
imports pyspark. It is a separate implementation: apart from the model function, it builds the
member rows, aggregates, checks and writes in its own way. Its phases correspond to the Spark
pipeline's:

- **Window statistics** (`window_stats_and_construction_check`): each definition's member rows are
  looked up in its ticker's returns, and rows that do not exist are dropped, as by the Spark
  pipeline's inner join. The count-guarded aggregates and the construction check follow the Spark
  pipeline's rules. Reading the inputs counts toward this phase, where the Spark pipeline reads
  them.
- **Model** (`model_and_path_days`): one call per window runs the body of the Spark pipeline's
  grouped pandas function. It sorts the window by date, checks it is complete and runs
  `model.simulate_path` for each leverage on the same returns.
- **Summaries and pairing** (`summaries_and_pairing`): the Spark pipeline's aggregations,
  completeness rules and pairing, computed with pandas grouping.
- **Checks** (`checks`): the ten checks with the same names, conditions and tolerances. They use
  nullable pandas types, so a null compares as in SQL and is never a violation by itself. A NaN from
  the model is stored as null, as the Spark pipeline stores it.

Each table is written once, with the Spark pipeline's Parquet column types; the Spark pipeline
writes each table and reads it back. `path_days` is partitioned by ticker in both. `run.json` has
the Spark pipeline's fields apart from `spark`, `stage_task_counts` and the `session_start` timing,
and adds `"engine": "pandas"`. The Spark pipeline is unchanged.

### 4.2 `measure --pipeline`

`etf_risk.measure --pipeline pandas` starts `python -m etf_risk.pandas_pipeline` instead of the
Spark pipeline; the sampling, stop rule and records are unchanged. With `--pipeline`, the protocol
JSON records the pipeline. Without it, measure starts the Spark pipeline, and its records are as
before.

### 4.3 Collector

`analysis/collect_baseline_measurements.py` writes `measurements.csv` and `acceptance.json` for one
batch and evaluates the criteria of section 10. The rules it shares with the shuffle-partition
experiment are that experiment's collector's functions, imported unchanged: code state, inputs,
positions, and the comparison of tables by their full keys. `--check-protocol <protocol JSON>
--engine S|P` checks one protocol's implementation and settings (6); the helpers run it after each
protocol.

### 4.4 Session helpers

`docs/baseline-session.zsh`, adapted from `docs/partition-session.zsh`, which stays unchanged. It
keeps `ready`, `pause5`, the watcher, `abort_run`, `after_abort`, `note` and `where`. `position n`
writes the 3.2 checks into the run log (3), runs the protocol of position n, then runs the check of
4.3 and appends to `positions.tsv`. The watcher recognizes both pipelines and shows each run's abort
limit (section 11). `position` refuses to start while an abort limit is missing.

### 4.5 Tests and validation

- `tests/test_pandas_pipeline.py` (19 tests). On the synthetic snapshot of
  `tests/test_spark_equivalence.py`, the four tables of both pipelines are equal by the rules of 7,
  types included, and the check counts are equal, in the same order. The same holds for the failures
  that test file injects: a dropped return row, a changed price, a duplicated leverage row and an
  invalid log term. The module never imports pyspark, its constants are the Spark pipeline's, and
  `measure --pipeline pandas` runs it in fresh processes.
- `tests/test_baseline_collector.py` (12 tests): a real S–P–P–S batch of two runs per protocol on
  that snapshot meets every criterion, and each planted problem fails its criterion. The planted
  problems are a Spark setting, a pipeline option, a missing `engine` field, a different
  environment, a code hash, the verified inputs, a run's status, an output value and the positions.
- `tests/test_baseline_session.py` (8 tests): the helper file parses and loads with the abort limits
  of section 11. `position` refuses invalid numbers and starts nothing while an abort limit is
  missing, and the watcher reads both pipelines. `ready` starts nothing unless all three limits are
  met.
- **Real data.** On the calendar-year windows (`calendar-year-r2`, 151 windows, including the
  breached AAPL 2000 window), both pipelines' four tables are equal by the rules of 7:
  - `path_days` is bit-identical;
  - the largest float difference is 9.1e-13, in `total_abs_rebalance`, whose values are in the
    thousands;
  - `checks.json` is byte-identical.

  Code state, environment and verified inputs are recorded identically.
- **Dry batch.** The helpers ran S–P–P–S with two runs per protocol on that window set. Every check
  after a protocol passed, and the collector found criteria 2 to 5 met; criterion 1 failed only
  because the code was not yet committed. The timings of these runs are not used: they come from
  another window set and are not formal measurements.
- Full suite: 196 passed.

## 5. Measurements

The time compared is `wall_s`, `measure`'s clock from starting the pipeline process to its exit.
Neither implementation records plans, so no plan-capture time is excluded. The phases of 4.1 are
reported next to it: S has a `session_start` phase and P none, and P's window-statistics phase
includes reading the inputs. The phases correspond by name, but the two implementations do not
divide their work between phases in the same way. Phase differences are therefore described, not
attributed to a cause.

Memory is peak total RSS: in S the Python driver, the JVM and the Python workers; in P one process.
Free memory before each run, the samples, the processes seen and the threshold crossing are
recorded as before.

Reported as observations, never as pass/fail criteria: the phases, the peaks per process type, the
files written per output table, and S's summed stage task counts. Summaries use the measured runs
that ended `ok` in the used protocols: medians and min–max per protocol and per implementation (six
runs), with the largest peak over all runs, warm-ups included.

## 6. Settings verification

Every run of the used protocols is checked against its implementation:

- **S:** the recorded Spark settings show Spark's default values for `spark.sql.shuffle.partitions`
  (200), `spark.sql.adaptive.enabled` and `spark.sql.adaptive.coalescePartitions.enabled` (both
  true); `run.json` has neither `pipeline_options` nor `engine`; the protocol records the pipeline
  `spark`. All of S's other recorded Spark settings are identical in all its runs.
- **P:** `run.json` records `"engine": "pandas"` and no Spark settings; the protocol records the
  pipeline `pandas`.
- **Both:** the recorded environment (CPU count, Java, machine, macOS, packages, platform, Python,
  RAM) is identical in all used runs of both implementations.

## 7. Output comparison with S

**Reference:** run 2 of the used protocol at position 1, the first measured run of S. Every other
run of the used protocols is compared with it, warm-ups included (15 runs), by the rules of
partition-experiment.md 7:

- row counts, keys, columns and types are equal exactly;
- NULLs are in the same rows;
- breach fields and other non-floating values are equal exactly;
- floats satisfy `|x − r| ≤ 1e-12 + 1e-9 × |r|`.

| Table | Full key | Compared |
| --- | --- | --- |
| `window_stats` | `window_kind`, `ticker`, `window_days`, `entry_date` | every run |
| `path_summary` | the window key and `leverage` | every run |
| `paired` | the window key | every run |
| `path_days` | the window key, `leverage` and `day` | run 2 of each P protocol in full; every run by row count |

`path_days` has 2,698,866 rows, so its full comparison is limited to one run per P protocol. Both
implementations produce it with the same model function, and on the calendar-year windows it was
bit-identical (4.5). The largest absolute and relative difference per column is reported per
implementation.

## 8. Drift rules

As in partition-experiment.md 8, with `wall_s`:

1. **S pair.** If S's protocol medians at positions 1 and 4 differ by more than 10% of the first,
   drift is reported and comparisons are marked as affected; nothing is re-run silently.
2. **P pair.** The same rule for P (positions 2 and 3), which runs back to back.
3. **Memory.** Pairs whose median peak total RSS differs by more than 0.2 GiB are reported.
4. **Context.** Each protocol's start time, free memory before each run, load average and time since
   boot are shown next to the pair differences.
5. **Earlier records.** S is compared with configuration A of the shuffle-partition experiment's
   batch-1 (`wall_s` minus its plan capture) descriptively only.

Drift does not void the results; it is reported, and section 9 still applies.

## 9. Comparing S and P

With `wall_s`:

- d1 is S's protocol median at position 1 minus P's at position 2;
- d2 is S's at position 4 minus P's at position 3;
- d is the difference between the medians of their six measured runs.

Under a drift that changes linearly with position, d1 and d2 shift by one position step in opposite
directions, so a drift alone gives them opposite signs.

- **Wall time.** S and P differ if |d| is more than 10% of S's six-run median and d1, d2 and d have
  the same sign. Otherwise there is no clear difference.
- **Peak memory.** The same rule with a threshold of 0.2 GiB on the median peak total RSS.
- **Phases** are described with d1, d2 and d, without a threshold and without attributing them to a
  cause (5). S's `session_start` has no P counterpart.

With two protocols per implementation, this is a descriptive rule, not a statistical test. A
difference it finds is a difference between the two implementations end to end (1.1).

## 10. Acceptance criteria

The collector evaluates these for one batch (4.3). The batch's results are used only if all of them
hold:

1. **Code state:** every protocol JSON and `run.json` of the batch records the same `source_sha256`
   and `uv_lock_sha256`, with the hashed paths clean (3).
2. **Inputs:** each run's `verified_sha256` holds exactly the seven inputs of 2.2, each equal to the
   hash in the stride-7 `config.json`, and each run's `windows_config` equals that file. After the
   session the seven hashes are computed once more and are unchanged.
3. **Settings:** section 6 holds for every run of the used protocols.
4. **Results:** every run of the used protocols ended `ok` with zero check violations, and section 7
   passes for each of them.
5. **Completeness:** each of the four positions has a used protocol of the implementation that 2.3
   puts there. It started 4 of 4 runs and all of them ended `ok`. None stopped early, none was
   aborted, and no sample exceeded 4.80 GiB. The used protocols ran in position order, and every
   protocol in the batch appears in `positions.tsv`.

Drift (8) and run conditions are not acceptance criteria. A departure from 3 is recorded as a
deviation, and the protocol's results are labeled with it.

## 11. Predictions

_Drafted with Claude Code (Opus 5.5) from the earlier records and the mechanisms below; reviewed
and approved by the author on 2026-10-22, before any measured run. The runs of 4.5 were not used:
they ran on other window sets and are not formal measurements. The dry batch's start and end times
were visible to Claude Code only after the estimate for P had been drafted, and they were not used
either. The predictions of the earlier experiments stay unchanged._

| | S: the Spark pipeline, Spark's defaults | P: the pandas pipeline, one process |
| --- | --- | --- |
| Median `wall_s` | 26.5 s | 40 s |
| Band: a median outside it contradicts the prediction | 21.2–31.8 s (±20%) | 28–60 s (−30% / +50%) |
| Peak total RSS, median of the measured runs (5); outside the range contradicts it | 2.5–2.9 GiB | 0.8–1.8 GiB |
| Abort a run above, on the watcher's raw elapsed time (3) | 80 s | 120 s |

The abort limits are three times the predicted medians, rounded: 3 × 26.5 s ≈ 80 s and
3 × 40 s = 120 s.

### 11.1 Expected comparisons (section 9)

- P slower than S by more than 10% of S's median, in both halves of the order. Expectation 5's "a
  single-process pandas run may be faster at these sizes" would then not hold for this workload.
- P's median peak total RSS lower than S's by more than 0.2 GiB, in both halves.

### 11.2 Basis

- **S** has the settings of configuration A in the shuffle-partition experiment's batch-1, whose six
  measured runs had a median `wall_excl_capture_s` of 26.462 s (partition-experiment.md 14.6). S
  records no plans, so its `wall_s` should be about that value. The ±20% band is the earlier
  experiments' (partition-experiment.md 11.3); there, the repeated stride-21 protocol's median was
  18.3% below the first's. A's median peak was 2.689 GiB: Spark JVM 1.523, Python workers 1.048 and
  Python driver 0.114 GiB.
- **P's model phase** runs the same per-window function on one core instead of eight workers. In the
  stride experiment, the model phase took 4.872 s at stride 21 and 8.099 s at stride 7
  (experiments.md 6.2), about 0.90 ms of wall time per additional window on eight workers.
  - **Assumption:** those workers ran in parallel at 50–100% efficiency, so one core needs
    3.6–7.2 ms per window, or 19–39 s for 5,364 windows.
  - The Spark figure also covers the data transfer and the `path_days` write, so this range may be
    high for the model alone.
- **P's other phases**, estimated from their sizes, not measured:
  - about 1 s to start the process;
  - 1–3 s to read the inputs and compute the window statistics;
  - 2–5 s to build and write the 2,698,866 path-day rows;
  - 3–6 s for the summaries' grouped aggregation over those rows;
  - 1–3 s for the checks.
- **Together** these give about 27–57 s, with 40 s as the point. The band around it, −30% / +50%, is
  skewed upward because the one-core cost per window is inferred from Spark's wall times, not
  measured.
- **P's memory.** One copy of the path-day rows takes about 0.35 GiB: 13 numbers and 3 string
  references per row. There are briefly two copies while the per-window frames are concatenated,
  besides the member rows and the summaries' grouping frame. This gives 0.8–1.8 GiB, where S's peak
  includes a JVM and eight Python workers.
- **Caution.** If machine conditions differ from batch-1's, both medians may move together. The
  comparison of section 9 is relative and less affected.

## 12. Deferred

- other workloads, for example strides 21 and 14;
- a vectorized or multi-process pandas pipeline;
- the Spark pipeline with other settings, for example configuration C of the shuffle-partition
  experiment;
- CPU time, spilling and garbage collection.

## 13. Origin of the design

The author's decisions and approvals are in 1.2. Everything else was proposed by Claude Code:

- **2.1 and 2.4:** running S without flags, and recording the pipeline in both protocols.
- **3:** reusing the shuffle-partition experiment's rules, writing the 3.2 checks at every start,
  and the branch.
- **4:** the code:
  - the pandas pipeline, and how it follows the Spark pipeline's phases, types and null rules;
  - `measure --pipeline`;
  - the collector and its reuse of the shuffle-partition collector;
  - the helpers.
- **5–10:**
  - the time metric and the observations;
  - the settings checks;
  - the reference run and the scope of the `path_days` comparison;
  - the drift and comparison rules;
  - the acceptance criteria.
- **11:** the draft of the predictions, which the author approved.
- **12:** the contents of the deferred list.

## History of this document

**Draft** (2026-10-22): the design from the author's decisions, the code and its validation, for the
author's review.

**Part A** (2026-10-22). The author approved the predictions and the abort limits:

- Section 11 was written from the approved worksheet, and the limits were set in the helpers (4.4).
- At the author's request, 1.1 now describes an end-to-end comparison of the two implementations.
  It states that sharing the model function does not isolate engine overhead; 5 and 9 follow it.

This version is committed before any measured run, together with the code of section 4, on
`feature/pandas-baseline`.
