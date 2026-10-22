# Pandas baseline

Author: I decided the scope, workload, order and settings listed in 1.2, reviewed and approved the
rest of the design and the predictions, ran the formal measurements, and wrote the Part B answers.
AI contributions are described below.

**Part A (sections 1–13): the design, the code and the predictions, committed before any measured
run (`204d04d`).** The author approved the predictions (section 11) and the rules listed in 1.2 on
2026-10-22 and ran the formal measurements (2.4, 4.4). **Part B (sections 14–15): the results of
batch-1, run on 2026-10-22 (UTC), and the author's answers.** Batch-1 met every acceptance criterion
(10), so it is the analyzed batch, and no further batch runs (3). Sections 1–13, the predictions
included, are unchanged since Part A. The history of this document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the records of the stride and shuffle-partition
experiments. Everything not listed in 1.2 is Claude Code's proposal (section 13). The predictions in
section 11 were drafted with Claude Code and reviewed and approved by the author. Part B was drafted
with Claude Code from batch-1's records, with the author's answers (sections 14 and 15)._

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

_Part A ends here; it was committed before any measured run (`204d04d`)._

## 14. Results

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from batch-1's run log and `positions.tsv`, the
four protocol JSONs, the 16 `run.json` files, `measurements.csv` and `acceptance.json` (numbers read
by script), and the author's terminal output from both windows. Times are UTC: the session ran from
05:28 to 05:57 on 2026-10-22. Differences and percentages are computed from unrounded values, so
they can differ by 0.001 from those of the rounded values shown. This section gives facts only; the
answers will follow in section 15._

### 14.1 Protocols

| Position | Implementation | Protocol | Runs (UTC, 2026-10-22) | Status |
| ---: | --- | --- | --- | --- |
| 1 | S | `20261022T053314Z` | 05:33:14–05:35:01 | 4 of 4 `ok` |
| 2 | P | `20261022T054121Z` | 05:41:21–05:42:22 | 4 of 4 `ok` |
| 3 | P | `20261022T054752Z` | 05:47:52–05:48:53 | 4 of 4 `ok` |
| 4 | S | `20261022T055420Z` | 05:54:20–05:56:06 | 4 of 4 `ok` |

- All 16 runs ended `ok` with zero check violations. No protocol stopped early, no run was aborted,
  and no sample crossed the 4.80 GiB threshold. Each position ran once, so nothing was re-run (3)
  and every protocol is a used protocol.
- **Acceptance (10):** the collector found all five criteria met and listed no problem. Batch-1 is
  therefore the analyzed batch, and no further batch runs (3).
- **Code state:** every protocol and run record shows commit `204d04d` with the hashed paths clean,
  and the same `source_sha256` (12 files) and `uv_lock_sha256` (starting `99484c14ebf3`).
- **Inputs:** every run verified the seven SHA-256 values of 2.2 and recorded a `windows_config`
  equal to the stride-7 `config.json`. When the collector ran after the session, the seven files
  still had those hashes.
- **Settings (6):** every S run recorded Spark's default values for the three partition settings and
  no `pipeline_options`; every P run recorded `"engine": "pandas"` and no Spark settings; each
  protocol recorded its pipeline. S's other recorded Spark settings are identical in its eight runs,
  and the recorded environment is identical in all 16 runs.
- **Records:** `data/outputs-baseline/batch-1/`, laid out as in 2.4.

### 14.2 Run log

The session used the helpers of 4.4 as committed in `f1b3222`, loaded in two Terminal windows:
window 1 ran the pauses, readings and protocols, and window 2 the watcher. Each protocol started
right after a five-minute pause and a `ready` reading that met all three limits of 3, and `position`
wrote the 3.2 checks into the run log at each start.

| Position | Checks at the start | Pause before the start | Available at the start (GiB) | 5-minute load at the start | Minutes since boot | Lowest free before a run (GiB) |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 1, S | 05:33:13 | 05:28:13–05:33:13 | 3.88 | 1.58 | 364 | 2.83 |
| 2, P | 05:41:20 | 05:36:20–05:41:20 | 4.19 | 2.42 | 373 | 4.11 |
| 3, P | 05:47:51 | 05:42:51–05:47:51 | 4.11 | 1.71 | 379 | 4.00 |
| 4, S | 05:54:20 | 05:49:20–05:54:20 | 4.08 | 1.50 | 386 | 2.95 |

Every check at a start showed Low Power Mode off, AC power, no Docker backend, no Java or pipeline
process, only Terminal and Finder open, `HEAD 204d04d` with no changed code file, and no Spark
scratch folder. The last column is the lowest `free_memory_before_bytes` among each protocol's four
runs. In each S protocol one run started with less than 3.0 GiB free (run 4: 2.83 and 2.95 GiB); 3
requires 3.0 GiB only before a protocol starts.

- **The boot** was the one of the shuffle-partition experiment's session, at 23:28 on 2026-10-21;
  the Mac had not been restarted since.
- **Spacing:** the protocols started 8.1, 6.5 and 6.5 minutes apart.
- **Further checks:** the author ran `prechecks` three more times between protocols (at 05:35:32,
  labeled `position n`, then at 05:42:41 and 05:49:12), before the pauses. They showed the same
  state.
- **Readings on their own:** in window 2, during the pause before position 1, `ready` read 2.41 GiB
  (logged as `protocol not started`) and then 4.53 GiB. No start was refused: each `pause5 && ready
  && position n` started at its first attempt.
- **Abort rule:** no run came near its limit. The longest raw wall times were 27.9 s (S) and 15.7 s
  (P), against 80 and 120 s. The watcher saw all 16 pipeline processes, four per protocol, and its
  largest readings were 24 s (S) and 16 s (P). No abort and no after-abort check was needed.
- **Notes:** after each protocol, the author recorded `4 ok, nothing unusual` with `note`.
- **After the session:** a check found no Spark scratch folder and no Java process.

### 14.3 Deviations and uncertain conditions

None found. Every start has its 3.2 checks in the run log, and each start met 3.

### 14.4 Drift (section 8)

| Rule | Positions | Protocol medians of `wall_s` | Difference from the first | Median peak total RSS (GiB) | Difference |
| --- | --- | --- | --- | --- | --- |
| 1. S pair | 1, 4 | 26.206, 26.460 s | +0.254 s (+0.97%) | 2.679, 2.682 | +0.003 GiB |
| 2. P pair | 2, 3 | 15.262, 15.440 s | +0.178 s (+1.17%) | 1.953, 1.990 | +0.037 GiB |

No time difference exceeds 10% of the first median, so no drift is reported under rules 1 and 2,
and no memory difference exceeds 0.2 GiB (rule 3). The context of rule 4 is in 14.2.

**Earlier records (rule 5, descriptive).** S's six measured runs have a median `wall_s` of 26.407 s
and a median peak total RSS of 2.680 GiB, against 26.462 s (`wall_excl_capture_s`) and 2.689 GiB for
configuration A in the shuffle-partition experiment's batch-1 (partition-experiment.md 14.6). S's
summed stage task counts (53, 22, 81 and 100) and file counts (1, 40, 8 and 1) equal A's in all
eight runs.

### 14.5 Measurements CSV

**Location.** `uv run python analysis/collect_baseline_measurements.py --batch
data/outputs-baseline/batch-1` reads the batch's records and writes `measurements.csv` and
`acceptance.json` into the batch folder (4.3). Like the records, they are under `data/`, which is
not in Git.

**Rows.** One row per started run: 16 rows, warm-ups included, in protocol order. `used` marks the
runs of the used protocols, here all 16.

**Columns.** 48:

| Group | Columns | From |
| --- | --- | --- |
| Identity | `batch`, `position`, `engine` (the implementation's label, S or P), `used`, `protocol_id`, `run_id`, `run_number`, `warmup`, `status`, `exit_code` | the batch folder, `positions.tsv`, the protocol JSON |
| Measurements | `started_at_utc`, `windows`, `path_day_rows`, `wall_s`, the six phases of 5 (`session_start_s` empty for P), `free_memory_before_bytes`, `peak_rss_total_bytes` and the peaks per process type, `samples`, `max_processes_seen`, `threshold_crossed`, `git_commit`, `git_worktree_clean` | `run.json`: `measurement`, `row_counts`, `timings_seconds`, `code` |
| Spark (empty for P) | `shuffle_partitions_requested`, `adaptive_enabled`, `coalesce_enabled`, `default_parallelism`, `jvm_max_heap_bytes`, `tasks_<phase>` | `spark`, `stage_task_counts` |
| Files | `files_window_stats`, `files_path_days`, `files_path_summary`, `files_paired` | the run folder |
| Comparison (7) | `window_stats_vs_reference`, `path_summary_vs_reference`, `paired_vs_reference`, `path_days_vs_reference`: `reference`, `pass`, `fail` or empty | the tables |

**Limitations.** Memory is sampled RSS, as in experiments.md 5.6. S's task counts are summed stage
task counts. The phases correspond by name but not by work (5).

### 14.6 Summary tables

_Drafted with Claude Code (Opus 5.5) from `measurements.csv` (values computed by script)._

Summaries use the measured runs that ended `ok` in the used protocols (5): three per protocol, six
per implementation. Each cell gives the median and, in brackets, the minimum and maximum. Peak
memory is `peak_rss_total_bytes` in GiB (2^30 bytes).

**By protocol**

| Position | Implementation | Protocol | `wall_s` (s) | Peak total RSS (GiB) |
| ---: | --- | --- | --- | --- |
| 1 | S | `20261022T053314Z` | 26.206 (25.621–27.152) | 2.679 (2.667–2.698) |
| 2 | P | `20261022T054121Z` | 15.262 (15.202–15.652) | 1.953 (1.924–1.978) |
| 3 | P | `20261022T054752Z` | 15.440 (15.314–15.515) | 1.990 (1.959–2.054) |
| 4 | S | `20261022T055420Z` | 26.460 (26.353–26.686) | 2.682 (2.672–2.707) |

**By implementation** (six measured runs; the largest peak covers all eight runs, warm-ups included)

| Implementation | `wall_s` (s) | Peak total RSS (GiB) | Largest peak (GiB) |
| --- | --- | --- | ---: |
| S: the Spark pipeline, Spark's defaults | 26.407 (25.621–27.152) | 2.680 (2.667–2.707) | 2.707 |
| P: the pandas pipeline, one process | 15.377 (15.202–15.652) | 1.968 (1.924–2.054) | 2.054 |

**Phases and peaks by process type** (medians of the six measured runs; each median is taken on its
own, so the phases do not add up to the total)

| | S | P |
| --- | ---: | ---: |
| `session_start` (s) | 2.440 | — |
| `window_stats_and_construction_check` (s) | 4.943 | 0.308 |
| `model_and_path_days` (s) | 8.622 | 12.134 |
| `summaries_and_pairing` (s) | 6.459 | 1.479 |
| `checks` (s) | 1.535 | 0.974 |
| `total_in_process` (s) | 25.281 | 14.970 |
| outside the pipeline's clock, `wall_s` − `total_in_process` (s) | 1.065 | 0.408 |
| Python driver peak (GiB) | 0.114 | 1.968 |
| Spark JVM peak (GiB) | 1.521 | — |
| Python workers peak (GiB) | 1.046 | — |
| processes seen, largest count per run (all eight runs) | 11–14 | 1 |

### 14.7 Comparison (section 9)

_Drafted with Claude Code (Opus 5.5) from `measurements.csv`. d = S − P between medians of measured
runs: d1 from positions 1 and 2, d2 from positions 4 and 3, d over the six runs of each. The time
threshold is 10% of S's six-run median, 2.641 s; the memory threshold is 0.2 GiB._

| Measure | d1 | d2 | d | Same sign | Beyond the threshold | Rule (9) |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `wall_s` (s) | +10.944 | +11.020 | +11.030 | yes | yes | differ: P shorter |
| peak total RSS (GiB) | +0.726 | +0.692 | +0.712 | yes | yes | differ: P lower |

S's six-run median `wall_s` is 71.7% above P's, and P's is 41.8% below S's. P's median peak is
0.712 GiB (26.6%) below S's. These are differences between the two implementations end to end
(1.1).

**Phases** (described without a threshold and not attributed to a cause, 5; seconds)

| Phase | d1 | d2 | d |
| --- | ---: | ---: | ---: |
| `window_stats_and_construction_check` | +4.646 | +4.624 | +4.635 |
| `model_and_path_days` | −3.249 | −3.658 | −3.512 |
| `summaries_and_pairing` | +5.205 | +4.766 | +4.980 |
| `checks` | +0.499 | +0.540 | +0.561 |
| `total_in_process` | +10.623 | +9.980 | +10.311 |

In both halves, P's model phase took longer than S's, and each of its other phases took less time.
S's `session_start` (2.440 s) has no P counterpart, and the time outside the pipeline's clock was
1.065 s in S and 0.408 s in P.

**Observations.** S wrote 1, 40, 8 and 1 files for `window_stats`, `path_days`, `path_summary` and
`paired`, and P wrote 1, 5, 1 and 1. P ran as one process in every run.

### 14.8 Output comparison (section 7)

_Drafted with Claude Code (Opus 5.5) from `acceptance.json`._

**Reference:** run 2 of position 1, `run-20261022T053314Z-2`. All 15 other runs pass for
`window_stats`, `path_summary` and `paired`:

- the reference's row counts (5,364, 10,728 and 5,364) and keys, with no null or duplicate key;
- the same columns and types, and NULLs in the same rows;
- breach fields and the other non-floating columns equal exactly.

Every run's `window_stats` and `path_days` row counts (5,364 and 2,698,866) equal the reference's.
`path_days`, compared in full for run 2 of both P protocols, passes with no difference in any
column.

**Floating-point columns:** the seven other S runs show no difference in any compared column. In the
eight P runs, 16 columns differ in the last bits. The largest absolute difference is 7.28e-12, in
`path_summary.total_abs_rebalance`, whose values are in the thousands (relative 4.4e-16). The
largest relative difference is 3.52e-11, in `paired.approx_rel_error`, whose values are near zero;
there the largest absolute difference is 2.56e-15. Every difference is within the tolerance of 7.
The columns are `sum_abs_return`, `realized_variance` and `exact_gap` in `window_stats` and in
`paired`; in `paired` also `total_turnover_2x`, `total_turnover_2x_pre_breach`, `mean_turnover_2x`,
`mean_turnover_2x_pre_breach`, `approx_gap`, `approx_rel_error` and `log_gap`; and `total_turnover`,
`mean_turnover` and `total_abs_rebalance` in `path_summary`.

## 15. Answers and limits

_The questions are Claude Code's proposals of 2026-10-22; the author divided the first into two
(15.1 and 15.2) when answering. In 15.1–15.4, the parts marked as drafted give facts, computed with
Claude Code (Opus 5.5) by script from batch-1's records (14) and from section 11, which is
unchanged. The answers, marked "Answer (author)", are the author's, copied from the conversation of
2026-10-22. After Claude Code's review, the author added the last two sentences of 15.4, which say
why the predictions were off, and at the author's request Claude Code applied the review's wording
"median wall time" in 15.1 and "median peak total RSS" in 15.3._

### 15.1 (a) Wall time

> How do the two implementations compare end to end in wall time?

_Drafted with Claude Code (Opus 5.5): the medians are in 14.6, and d1, d2 and d in 14.7._

**Answer (author).** Pandas's median wall time was 41.8% shorter than Spark's: 15.38 versus
26.41 s. Both halves supported this difference.

### 15.2 (b) Phases

> How do their phases differ?

_Drafted with Claude Code (Opus 5.5): the phases are in 14.6 and their differences in 14.7. The
phases correspond by name but not by work (5)._

**Answer (author).** Spark's model phase was shorter, but pandas saved more time in window
statistics, summaries and startup. This compares two implementations, not isolated engine overhead.

### 15.3 (c) Memory and correctness

> How do peak memory and the outputs compare?

_Drafted with Claude Code (Opus 5.5): peak memory is in 14.6 and 14.7, and the output comparison in
14.8._

**Answer (author).** Pandas's median peak total RSS was 26.6% lower than Spark's: 1.97 versus
2.68 GiB. All required output comparisons passed within tolerance.

### 15.4 (d) Predictions against results

> Where were the predictions off, and why?

_Drafted with Claude Code (Opus 5.5) from section 11, which is unchanged, and from section 14. Time
items use the medians of `wall_s` and of the phases over the six measured runs, and memory items the
medians of peak total RSS._

| Section 11 | Predicted | Measured | Result |
| --- | --- | --- | --- |
| S, median time | 26.5 s, band 21.2–31.8 s | 26.407 s | inside, 0.4% below the point |
| P, median time | 40 s, band 28–60 s | 15.377 s | outside: 61.6% below the point, 12.6 s below the band |
| S, median peak | 2.5–2.9 GiB | 2.680 GiB | inside |
| P, median peak | 0.8–1.8 GiB | 1.968 GiB | outside: 0.168 GiB above the range |
| Abort limits | 80 and 120 s | longest runs 27.9 and 15.7 s | no run aborted |
| 11.1, time | P slower than S by more than 10%, in both halves | P shorter: d = +11.030 s, with d1 and d2 of the same sign | contradicted: the ranking is reversed |
| 11.1, memory | P lower than S by more than 0.2 GiB, in both halves | d = +0.712 GiB, with d1 and d2 of the same sign | as predicted |
| 11.2, P's `model_and_path_days` | 21–44 s: the model alone 19–39 s, and building and writing the path-day rows 2–5 s | 12.134 s | below the range |
| 11.2, P's other phases | window statistics with input reading 1–3 s, summaries 3–6 s, checks 1–3 s, process start about 1 s | 0.308, 1.479 and 0.974 s, and 0.408 s outside the pipeline's clock | each below its estimate |

- The model's estimate rested on an assumption (11.2): S's model phase used its eight workers at
  50–100% efficiency, so one core would need 3.6–7.2 ms per window for the model alone. P's whole
  model phase, the `path_days` write included, took 12.134 s, or 2.26 ms per window.
- P's model phase took 1.41 times as long as S's (12.134 against 8.622 s). The two phases do not do
  the same work (5), so this ratio does not measure parallel efficiency.
- P's peak, all in one process, exceeded the predicted range; the records do not show which data
  the process held at its peak.

**Answer (author).** Spark matched its predicted ranges. Pandas was faster than predicted but used
more memory than predicted, reversing the expected time ranking. The estimate overstated pandas's
model and other phase times. The predicted memory ranking held, but the records do not explain why
pandas's peak exceeded its range.

### 15.5 (e) What these measurements cannot show

> What can these measurements not show?

**Answer (author).** These results cover one machine and workload. No drift was detected, but that
does not prove constant conditions. Sampling and implementation differences limit causal claims and
conclusions about larger workloads.

**Limitation added at the author's request** (drafted with Claude Code (Opus 5.5) after the Part B
commit). Library thread counts were not controlled or measured in either implementation. PyArrow
permits multithreaded reads and conversion by default; actual thread usage during the measurements
was not recorded. The records show that P ran in one process (14.7), not that it used a single
core, so "in one process on one core" in 1.1 holds only for the process count.

## History of this document

**Draft** (2026-10-22): the design from the author's decisions, the code and its validation, for the
author's review.

**Part A** (2026-10-22). The author approved the predictions and the abort limits:

- Section 11 was written from the approved worksheet, and the limits were set in the helpers (4.4).
- At the author's request, 1.1 now describes an end-to-end comparison of the two implementations.
  It states that sharing the model function does not isolate engine overhead; 5 and 9 follow it.

This version is committed before any measured run, together with the code of section 4, on
`feature/pandas-baseline`.

**Part B** (2026-10-22). Section 14 gives batch-1's results as facts, and section 15 the author's
answers, with facts drafted by Claude Code; the changes after Claude Code's review are listed at the
start of section 15. The status at the top now describes both parts, the author's authorship line
was added, and a line marks the end of Part A. Sections 1–13, the predictions included, are
unchanged. This version is committed on `feature/pandas-baseline` after the formal session.

**Part B, revision** (2026-10-22). At the author's request, 15.5 adds a limitation: library thread
counts were not controlled or measured, so the records show that P ran in one process, not on one
core. Sections 1–13 stay unchanged.
