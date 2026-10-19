# Spark performance experiments

Author: the project author, who set the question and the design (section 1), wrote the reasoning
in 2.3, 2.4 and 2.6, made the decisions behind section 3, wrote the predictions in 4.1–4.5, and
checked the parts drafted with Claude Code.

AI contribution: Claude Code (Opus 5.5) sets the tasks and acceptance criteria and reviews each
step. It drafted the parts marked _Drafted with Claude Code_: section 2, items 2.1, 2.2 and 2.5,
from the records named in each part (numbers read from the configs by script, file hashes
recomputed), section 3 from the author's decisions of 2026-10-18, and 4.6 from section 4 and the
Stage 2 records. At the author's request it also applied wording fixes from its reviews in
section 1 and in 2.1, copied the author's predictions 4.1–4.5 from the conversation into
section 4, added the sentence there that H1 is the least certain prediction, and drafted the
authorship line above, which the author chose. For Part B it wrote the shell helpers used in the
measurement session (5.2), reviewed each protocol's records, and drafted 5.1–5.5 from the records
(numbers read by script), VS Code's logs and the author's statements. At the author's request it
also wrote `analysis/collect_measurements.py`, apart from `find_protocols`, `load_runs` and
`identity_row`, which are the author's, drafted 5.6 and 5.7 from that script and its CSV, and
drafted the facts in 6.1–6.4 (the fits, the phase and memory tables and the comparison with
section 4); the answers in section 6 are the author's, with corrections and figures from its
review added at the author's request (listed at the start of section 6).

Status: Part A (sections 1–4) committed in `164f65a` before any measured run (the authorship line
was added in a later commit) and unchanged since. Five protocols were run on 2026-10-19
(section 5); Part B (sections 5 and 6) was written afterwards the same day, with no further runs.

## 1. Question, hypotheses and design

### 1.1 Question and scope

How do runtime and peak memory change as the number of windows grows, and why? This is the
workload-size part of research question 3 (spec §2); partitioning and the optional caching
experiment come later, and a single-process pandas comparison is not tested. Data, model,
252-day window length, 1x/2x leverage and Spark settings stay fixed. Runs use the Apple M2
MacBook Air (8 cores, 8 GiB RAM).

### 1.2 Hypotheses and measurements

- **H1:** fixed overhead dominates at sparse strides. Fit median wall time as `a + b × windows`;
  call overhead dominant at stride 21 if `a > 0` and exceeds 50% of its median wall time. Compare
  with `session_start`, noting that Python worker startup is not timed separately. The fitted
  intercept is only an estimate; a poor fit makes this interpretation unreliable.
- **H2:** workload-dependent time grows roughly with window count. Use a positive fitted slope
  and fitted values within 20% of each measured median as descriptive criteria, not a statistical
  test. Also compare `model_and_path_days` per window and the other phase timings.
- **H3 (measurement question):** how does peak memory change? Record total and per-process-type
  RSS peaks, then compare with the prediction ranges in section 4. RSS may double-count shared
  pages; measuring it is a method, not a hypothesis.

### 1.3 Strides and order

Use strides **21, 14, 7 and conditionally 3**, giving about **1×, 1.5×, 3× and 7×** the baseline
windows. Stride 14 tests a small increase; 7 and 3 test larger workloads. Compare shared-window
results for correctness: strides 7 and 3 contain all 1,790 baseline keys, while 14 shares only
896 and changes the selected starts (section 2.6).

Run sparse to dense, with stride 3 allowed only by the numeric rule in section 3. The stop rule
acts between runs and cannot protect a run already in progress. If stride 3 is skipped, report
only the roughly 3× tested range. Exclude stride 1 for now: 37,550 windows and at most
18,925,200 path-day rows, with resource use not yet validated.

Fixed order can introduce drift from sustained load, temperature, background activity and file
caching. Section 3 will define pauses, machine checks and a repeated baseline check. Predictions
and measured results belong in later sections.

## 2. Window definitions: counts and self-checks

### 2.1 How the sets were built

_Drafted with Claude Code (Opus 5.5) from the four `config.json` files; edited by the author._

The four sets were built on 2026-10-17, between 20:45:24 and 20:45:29 UTC, from the processed
snapshot `full-2026-10-12`, with this loop run from the repository root:

```bash
for stride in 21 14 7 3; do
  uv run python -m etf_risk.windows \
    --snapshot full-2026-10-12 \
    --kind rolling \
    --stride "$stride" \
    --allow-dense-stride \
    --out-root data/windows-experiments
done
```

`--allow-dense-stride` matters only for strides below 21; for stride 21 it has no effect. Each set
is in `data/windows-experiments/full-2026-10-12/rolling-252-s<stride>/` (`windows.parquet` and
`config.json`). For the four existing sets in `data/windows/full-2026-10-12/`, each
`windows.parquet` still matches the `windows_sha256` in its config. Their current file
modification timestamps all fall on 2026-10-13 in UTC (the evening of 2026-10-12 in local time,
CDT). The hashes and timestamps are the only evidence available that the earlier sets were
preserved; timestamps alone do not prove their modification history.

The four configs record the same build:

- **Code:** commit `a7fb72d` with `git_worktree_clean: true` for the paths checked by
  `code_state()` (`src/`, `pyproject.toml` and `uv.lock`, not the entire repository); identical
  `source_sha256` (10 source files) and `uv_lock_sha256`.
- **Inputs:** identical `inputs_sha256` for the five daily-return files and `quality_report.json`.
- **Windows:** 252 trading days; start grid anchored at the NYSE session 1980-01-02; calendar from
  pandas_market_calendars 5.5.0; the same unverified-day flag rule.
- Each `windows.parquet` matches the `windows_sha256` recorded in its config.

### 2.2 Counts

_Drafted with Claude Code (Opus 5.5) from the `counts` block of each `config.json`._

| Stride | Windows | AAPL  | MSFT  | NVDA  | QQQ   | TSLA  | Window-member rows | Path-day rows, 1x and 2x (at most) | Windows vs stride 21 |
| ------ | ------- | ----- | ----- | ----- | ----- | ----- | ------------------ | ---------------------------------- | -------------------- |
| 21     | 1,790   | 529   | 466   | 311   | 310   | 174   | 451,080            | 902,160                            | 1.00                 |
| 14     | 2,683   | 793   | 699   | 466   | 464   | 261   | 676,116            | 1,352,232                          | 1.50                 |
| 7      | 5,364   | 1,586 | 1,397 | 932   | 928   | 521   | 1,351,728          | 2,703,456                          | 3.00                 |
| 3      | 12,518  | 3,701 | 3,259 | 2,176 | 2,165 | 1,217 | 3,154,536          | 6,309,072                          | 6.99                 |

- Windows and the per-ticker counts are `counts.windows` and `counts.by_ticker`; in every set the
  per-ticker counts sum to the total.
- Window-member rows = 252 × windows: one row per return day of each window.
- Path-day rows: at most 2 × window-member rows, one row per window, leverage (1x, 2x) and day. A
  breached 2x path stops at its breach, so a run can write fewer. The run of record, on
  `rolling-252-s21-r2` (equal to this stride-21 set, see 2.5), wrote 900,714 path-day rows against
  the bound of 902,160 (`row_counts` in its `run.json`).
- The last column is the number of windows divided by 1,790, rounded to two decimals.

### 2.3 Self-checks

Each value is a violation count, not a count of successful checks.

| Check                    | Stride 21 | Stride 14 | Stride 7 | Stride 3 |
| ------------------------ | --------: | --------: | -------: | -------: |
| duplicate_window_keys    |         0 |         0 |        0 |        0 |
| unknown_ticker           |         0 |         0 |        0 |        0 |
| rows_out_of_range        |         0 |         0 |        0 |        0 |
| row_dates_mismatch       |         0 |         0 |        0 |        0 |
| flag_mismatch            |         0 |         0 |        0 |        0 |
| not_on_grid              |         0 |         0 |        0 |        0 |
| wrong_window_days        |         0 |         0 |        0 |        0 |
| spacing_not_stride       |         0 |         0 |        0 |        0 |
| missing_or_extra_windows |         0 |         0 |        0 |        0 |
| calendar_year_mismatch   |         0 |         0 |        0 |        0 |
| not_full_period          |         0 |         0 |        0 |        0 |

All applicable checks found no violations; the builder raises an error instead of writing a set
when a check fails, so successfully written configs are expected to contain zeros. These zeros
do not establish that the source prices are correct or provide a fully independent validation,
because some checks reuse the window-generation rules.

For these rolling windows, the applicable checks cover unique keys, known tickers, valid row
bounds, entry/first-return/exit dates, unverified-day flags (including the entry price), the
shared start grid, the 252-day length, stride spacing and the expected number of windows.
In particular, `missing_or_extra_windows` recomputes the expected count using the same
grid-selection rule as the builder; it is not an independent proof of correct membership.
Section 2.4 provides a separate arithmetic count check, and section 2.6 compares actual keys.

`calendar_year_mismatch` and `not_full_period` apply to other window kinds; their zeros here
do not mean that calendar-year or full-period definitions were tested in this rolling-window build.

### 2.4 Count check

For a ticker with P price rows, there are P − 252 possible complete 252-return windows at
stride 1. The five processed files give 11,103 (AAPL), 9,777 (MSFT), 6,526 (NVDA), 6,494 (QQQ)
and 3,650 (TSLA) eligible starts, totaling 37,550. Their price dates were checked to occupy
consecutive sessions on the same NYSE grid used by the definitions.

| Stride | Actual windows N | 37,550 / stride | N − 37,550 / stride | Absolute difference < 5 |
| ------ | ---------------: | --------------: | ------------------: | ----------------------- |
| 21     |            1,790 |    1,788.095238 |           +1.904762 | Yes                     |
| 14     |            2,683 |    2,682.142857 |           +0.857143 | Yes                     |
| 7      |            5,364 |    5,364.285714 |           −0.285714 | Yes                     |
| 3      |           12,518 |   12,516.666667 |           +1.333333 | Yes                     |

Each ticker's eligible first-return session indices form a consecutive integer interval.
For stride s, the builder selects indices divisible by s. In an interval of n eligible indices,
the number selected is either floor(n / s) or ceil(n / s), depending on where the interval
starts relative to the anchor. Its difference from n / s therefore has absolute value less
than 1. Summing across five tickers gives an absolute difference strictly less than 5 from
37,550 / s. The displayed values are rounded to six decimal places; the comparisons use the
unrounded values.

All four counts satisfy this bound. This is a coarse sanity check: a wrong set of dates could
still have a count within the bound, so it does not replace the date and membership checks.

### 2.5 Baseline: the new stride-21 set equals `rolling-252-s21-r2`

_Drafted with Claude Code (Opus 5.5) from both sets' `config.json` and `windows.parquet`; edited by the author._

- **Same file:** both configs record the same `windows_sha256`, and hashing both `windows.parquet`
  files again gives that value, so the two files are byte-identical.
- **Same inputs:** identical `inputs_sha256`, raw-manifest hashes and `counts`, including the
  unverified-day counts.
- **Different code state:** `-r2` was built at `cc7f83c` with uncommitted changes, the new set at
  `a7fb72d` with the checked code/dependency paths clean (scope in 2.1). Of the 10 source files,
  only `provenance.py` differs: the `-r2`
  build used the version committed in `f08dec5`, and `6a460b0` (the Docker image) added the
  build-time fallback. `windows.py` and `uv.lock` are identical. The byte-identical files show that
  this change did not alter the definitions.

So the experiment's stride-21 baseline is the run of record's window set, built by the same code
state as the three denser sets.

### 2.6 Nesting

| Compared set | Total windows | Stride-21 keys present | Stride-21 keys absent | Contains every stride-21 window |
| ------------ | ------------: | ---------------------: | --------------------: | ------------------------------- |
| Stride 21    |         1,790 |                  1,790 |                     0 | Yes (baseline)                  |
| Stride 14    |         2,683 |                    896 |                   894 | No                              |
| Stride 7     |         5,364 |                  1,790 |                     0 | Yes                             |
| Stride 3     |        12,518 |                  1,790 |                     0 | Yes                             |

Let j be the first-return session index counted from the common anchor, 1980-01-02. A
stride-21 window has j divisible by 21. Since both 7 and 3 divide 21, every such start is
also selected at strides 7 and 3. The snapshot, window length and eligibility bounds are
unchanged, so these are the same windows, not just matching start dates.

For stride 14, a shared start must be divisible by both 21 and 14, hence by their least
common multiple, 42. Equivalently, among starts j = 21k, only those with even k are shared;
the ones with odd k are absent. Checking the actual dates confirmed exactly this rule.
The 896 shared keys comprise AAPL 265, MSFT 233, NVDA 156, QQQ 155 and TSLA 87. Finite
per-ticker boundaries explain why the intersection is not exactly half of 1,790.

Thus a smaller stride gives more windows, but does not always give a superset of the
baseline. In particular, the stride-14 workload changes the selected starts as well as
their number; it should not be described as the baseline plus extra windows.

## 3. Run conditions and stop rules

_Drafted with Claude Code (Opus 5.5) from the author's decisions of 2026-10-18; tool behavior and
record fields from `measure.py` and `spark_pipeline.py`._

### 3.1 Code state

- One code state for the whole experiment: identical `source_sha256` and `uv_lock_sha256`, and
  `git_worktree_clean: true`, in the four window configs and in every run record (`code` and
  `windows_config.code` in each `run.json`, `code` in each protocol JSON).
- `src/`, `pyproject.toml` and `uv.lock` do not change from the first protocol to the last; the
  `--shuffle-partitions` option for the partition experiment waits until then. Committing this
  document changes `git_commit` but not the hashes.

### 3.2 Machine state before each protocol

`run.json` does not record these, so they are checked by hand and written into the run log in
section 5:

- Low Power Mode off: `pmset -g` shows `lowpowermode 0`.
- Mains power: `pmset -g batt` shows `AC Power`.
- Docker Desktop, VS Code (with the Claude Code session) and other apps quit; commands run from
  Terminal. `pgrep -fl com.docker.backend` prints nothing.
- A 5-minute pause before each protocol.
- At least 3.0 GiB available, read just before starting with
  `uv run --group measure python -c "import psutil; print(round(psutil.virtual_memory().available / 2**30, 2))"`,
  the same quantity `measure` records per run as `free_memory_before_bytes`. A protocol starts only
  when this reading is at least 3.0 GiB.

### 3.3 Protocols

- Order: stride 21, 14, 7, then 3 only if 3.5 allows it, then stride 21 again for the drift check
  (3.4).
- Each protocol has four runs (`--repeats 4`): one warm-up and three measured; `measure`
  summarizes the measured runs that ended `ok`. The goal is four `ok` runs per protocol.
- Command, from the repository root (`caffeinate -i` keeps the Mac from idle sleep while it runs):

  ```bash
  caffeinate -i uv run --group measure python -m etf_risk.measure --repeats 4 -- \
      --windows data/windows-experiments/full-2026-10-12/rolling-252-s<stride> \
      --out-root data/outputs-experiments
  ```

- Records go to `data/outputs-experiments/full-2026-10-12/rolling-252-s<stride>/`: one
  `protocol-<UTC time>.json` per protocol and one folder and `.log` per run. Nothing is written
  under `data/outputs/windows/`. The two stride-21 protocols share a folder and are told apart by
  their protocol times.

### 3.4 Drift check

The repeated stride-21 protocol's median wall time over its measured runs is compared with the
first stride-21 protocol's. A difference of more than 10% is reported as drift, and comparisons
across strides are marked as affected; nothing is re-run silently. (Stage 2's three measured
stride-21 runs spanned 40.2–47.0 s, so 10% leaves room for ordinary run-to-run variation.)

### 3.5 Go/no-go for stride 3

Evaluated after the stride-7 protocol and the pause, from the stride-7 records (all four runs,
warm-up included). Stride 3 runs only if all three conditions hold:

1. **Status:** all four stride-7 runs ended `ok`, and the protocol did not stop early.
2. **Memory:** with P the largest `peak_rss_total_bytes` of the four runs, the projected stride-3
   peak P × 12,518 / 5,364 (≈ 2.33 P) plus a 0.5 GiB margin is at most the smaller of 4.80 GiB
   (the stop threshold, 60% of 8 GiB) and the memory available just before stride 3.
3. **Time:** with W the longest `wall_seconds` of the four runs, the projected protocol time
   4 × W × 12,518 / 5,364 is at most 60 minutes.

Both projections scale all memory and time with the number of windows and ignore fixed parts, so
they overestimate: the rule errs toward skipping stride 3. The decision and the numbers behind it
are reported in section 5 either way.

### 3.6 Failures, early stops and aborts

All runs and records are kept and reported; nothing is deleted or overwritten, and no threshold
or repeat count changes without a written reason. By the run's status in the protocol JSON:

- `checks_failed`: stop the whole experiment and investigate before any further protocol.
- `failed` (a crash, a kill or another non-zero exit code): stop that stride and keep everything;
  at most one re-run of that protocol, only with a written reason.
- `memory_threshold_exceeded`: no denser stride is run after it.

A run that takes more than 3× its predicted median wall time (section 4) is aborted by killing
its pipeline process, never with Ctrl-C:

```bash
pgrep -f etf_risk.spark_pipeline   # process id of the running pipeline
kill <pid>
```

`measure` then records the run as `failed`, stops the protocol and still writes the protocol
JSON. Ctrl-C would stop `measure` itself, which writes that JSON only at the end. After every
abort, check that no Java process from the run is left (`pgrep -fl java`) and that no new Spark
scratch folder (`spark-*`, `blockmgr-*`) remains in `$TMPDIR` or `/tmp`, and write the result
into the run log.

The aborted run's folder keeps whatever the pipeline had written (for example `window_stats/` and
an incomplete `path_days/`), plus a `run.json` that `measure` writes with status
`no run.json written` and the measurement. These partial outputs are never used as results
(3.7).

Verified on 2026-10-18, before any measured run, with the 3.3 command on the stride-21 set, a
scratch output folder and `--repeats 2`, killing the pipeline once its Python workers were
running (after 19 s):

- `measure` recorded the run as `failed` (exit code -15) and started no second run.
- It wrote the protocol JSON and exited with status 1.
- The JVM and the Python worker were gone within about a second.
- No Spark scratch folder (`spark-*`, `blockmgr-*`) was left in Java's temp folder or `/tmp`.
- Nothing changed in the repository or under `data/`.

Scope of this check: that `measure` keeps the records follows from its code, which waits for the
pipeline process and only then writes the run's measurement and the protocol JSON. The cleanup of
Spark's processes and scratch folders was observed in this one test, at one point of one run on
this machine. It is not guaranteed in every situation (for example at another moment of a run,
under memory pressure, or with other Spark or Java versions), which is why the checks above are
repeated after every abort.

### 3.7 Records and summaries

- The measurements CSV keeps every run that was started, with its status: warm-ups, failed and
  aborted runs, and runs that stopped a protocol.
- Performance summaries (medians and min–max of wall time and peak memory) use only runs that
  ended `ok` and are not warm-ups, as `measure`'s own `summary_over_measured_runs` does.
- Output tables are read only from runs that ended `ok`. Tables of other runs, such as the
  incomplete `window_stats/` and `path_days/` of an aborted run, are skipped; only their records
  (`run.json`, protocol JSON, `.log`) are used.

## 4. Predictions

_4.1–4.5 are the author's predictions, copied from the conversation of 2026-10-18 with only the
edits needed to merge revisions; the last sentence of the H1 paragraph was added at the author's
request. 4.6 is drafted with Claude Code (Opus 5.5) from 4.1–4.5 and the Stage 2 records._

### 4.1 Stride-21 wall time

I predict 45 s for the first stride-21 protocol's median measured wall time. Stage 2's median was
44.7 seconds. The quieter machine may run faster, but the records cannot quantify that effect, so I
keep the baseline estimate. The ±10 s tolerance allows roughly ±5 s for Stage 2's observed
variation and another ±5 s for uncertainty about the changed machine conditions. A median outside
35–55 s contradicts this prediction. The abort threshold is 135 s.

### 4.2 Stride-21 peak memory

I predict the maximum sampled process-tree RSS across all four runs, including warm-up, will be
1.3–1.8 GiB. Stage 2's maximum was 1.45 GiB. The JVM had the largest per-type peak, but its 1 GiB
heap limit does not cap total JVM RSS or Python workers. I allow extra headroom because lower
memory pressure may leave more pages resident. The lower edge allows modest variation around
Stage 2's 1.453 GiB maximum. A sampled maximum outside this range contradicts the prediction;
0.25 s sampling may miss higher brief peaks.

### 4.3 Wall time at strides 14, 7 and 3

I use a simple prediction model: 17 s of overhead plus 28 s multiplied by the window-count ratio.
This gives 59 s, 101 s and 213 s for strides 14, 7 and 3. The abort thresholds are 177 s, 303 s
and 639 s.

I treat 17 s as an overhead estimate anchored to the small run, not a pure fixed-cost
measurement. I use a −20% / +30% tolerance: better utilization and amortized scheduling costs
could make runs faster, while shuffle, writing and spilling could make them slower. A measured
median outside that interval contradicts the prediction.

H1 will still use the fitted intercept defined in section 1. The small run is a supporting
comparison, not a replacement test. These predictions do not distinguish linear from mildly
nonlinear growth.

### 4.4 Peak memory at strides 14, 7 and 3

My predicted ranges for the largest sampled total RSS across all four runs are:

- Stride 14: 1.3–2.0 GiB
- Stride 7: 1.3–2.4 GiB
- Stride 3: 1.4–3.2 GiB

Memory was measured at only one workload size, so these are broad, mechanism-based predictions.
Each model call still handles a 252-day window, and concurrency stays fixed, so Python-worker
memory should not grow directly with the total window count. The driver should remain relatively
small. JVM buffers, shuffle and output processing may increase memory use; the 1 GiB heap limit
does not cap total RSS. Memory pressure may also increase runtime or cause failure.

The lower edges allow modest variation around Stage 2's 1.453 GiB maximum; they do not predict
that more windows reduce memory. Stage 2's per-type peaks total about 2.0 GiB: JVM 1.06, workers
0.87 and driver 0.11. I allow greater overlap of these peaks, plus increasing JVM/buffer use at
denser strides. These are broad judgment ranges, not measured bounds. A maximum sampled RSS
outside its stated range contradicts the prediction.

Assuming 3.5 GiB available before stride 3, the rule permits a stride-7 peak up to approximately
1.29 GiB. Neither end of my 1.3–2.4 GiB range passes, so I expect stride 3 to be skipped. Actual
admission will use the recorded peak and available memory, not this assumption.

### 4.5 Hypotheses H1 and H2

**H1:** I expect an intercept near 17 s, about 38% of the predicted 45 s baseline, so I expect
H1's "over 50%" condition not to hold. A reliable fitted intercept above half the measured
baseline median would reverse that expectation. H1 is the least certain prediction: the expected
intercept is only 5.5 s below the 50% line, and noise in the three medians or curvature in the
growth could close that gap (4.6).

**H2:** I expect a positive slope with fitted values within 20% of the measured medians. However,
if stride 3 is skipped, three points leave only one residual degree of freedom, so this is weak
descriptive evidence. A non-positive slope or any fitted error above 20% would contradict the
expectation.

### 4.6 Summary

_Drafted with Claude Code (Opus 5.5) from 4.1–4.5 and the Stage 2 records listed below._

| Protocol | Windows (vs stride 21) | Median wall time | Band for the median | Abort a run above | Largest total RSS, all four runs |
|---|---|---|---|---|---|
| Stride 21, first | 1,790 (1.00) | 45 s | 35–55 s | 135 s | 1.3–1.8 GiB |
| Stride 14 | 2,683 (1.50) | 59 s | 47.2–76.7 s | 177 s | 1.3–2.0 GiB |
| Stride 7 | 5,364 (3.00) | 101 s | 80.8–131.3 s | 303 s | 1.3–2.4 GiB |
| Stride 3, only if 3.5 admits it | 12,518 (6.99) | 213 s | 170.4–276.9 s | 639 s | 1.4–3.2 GiB |
| Stride 21, repeated | 1,790 (1.00) | — | within 10% of the first stride-21 median (drift check, 3.4) | 135 s | — |

- Bands: ±10 s at stride 21 (4.1); −20% / +30% of the predicted median at strides 14, 7 and 3
  (4.3). A median outside its band contradicts the prediction, and so does a largest total RSS
  outside its range.
- Expected outcomes: H1's "over 50%" condition does not hold (intercept about 17 s, 38% of 45 s);
  H2 holds, as weak evidence with three points; stride 3 is skipped.

**Stride-3 decision.** Rearranged, the rule in 3.5 admits stride 3 only if the largest stride-7
peak P is at most (the smaller of 4.80 GiB and the memory available before stride 3, minus
0.5 GiB) / 2.334:

- At the assumed 3.5 GiB available, P must be at most about 1.29 GiB, below the whole predicted
  stride-7 range.
- The low end of that range (1.3 GiB) would pass only with more than about 3.53 GiB available.
- A stride-7 peak above about 1.84 GiB can never pass, whatever is available (the 4.80 GiB cap).

**Why H1 is the least certain prediction.**

- The predicted intercept, 17 s, is 5.5 s below the 50% line (22.5 s of 45 s).
- With three points at 1.0×, 1.5× and 3.0× the stride-21 windows, each 1 s error in a measured
  median moves the fitted intercept by about +1.0 s (stride 21), +0.6 s (stride 14) and −0.65 s
  (stride 7). Stage 2's medians varied by a few seconds.
- Concave growth would put the fitted intercept above 17 s; convex growth, for example from
  spilling, below it.

**Records used for section 4** (all from before this experiment):

- Stage 2's stride-21 protocol `20261013T043848Z` on `rolling-252-s21-r2`: measured wall times
  44.7, 47.0 and 40.2 s (median 44.7 s) and a 43.6 s warm-up; largest total RSS per run 1.344
  (warm-up), 1.244, 1.270 and 1.453 GiB; per-type peaks JVM 0.92–1.06, Python workers 0.70–0.87
  and driver 0.11 GiB; 1.0–1.6 s outside the pipeline's own clock per run.
- The 4-window full-period regression (`regression-r2`, 12,056 path-day rows) took 16.3 s inside
  the pipeline, and the 151-window calendar-year supplement (`supplement-r2`, 75,971 path-day
  rows) 21.9 s. Both ran with the run of record's code and `uv.lock`, in the same session just
  before and after its protocol; neither was measured for memory.

_Part A ends here; it is committed before any measured run._

## 5. Results

_5.1–5.5 drafted with Claude Code (Opus 5.5) from the run log
(`data/outputs-experiments/run-log.txt`), the five protocol JSONs and twenty `run.json` files
(numbers read by script), VS Code's own logs, and the author's statements (5.3) and terminal
screenshots (the watcher times in 5.2) of 2026-10-19. All times are UTC on 2026-10-19._

### 5.1 Protocols

| Order | Stride | Protocol | Role | Runs (UTC) | Status |
| ----: | -----: | -------- | ---- | ---------- | ------ |
| 1 | 21 | `20261019T030242Z` | planned: baseline | 03:02:42–03:04:07 | 4 of 4 `ok` |
| 2 | 14 | `20261019T034949Z` | planned | 03:49:49–03:51:10 | 4 of 4 `ok` |
| 3 | 7 | `20261019T035809Z` | planned | 03:58:09–03:59:51 | 4 of 4 `ok` |
| 4 | 3 | `20261019T042741Z` | **exploratory**: not admitted by 3.5, run deliberately (5.3) | 04:27:41–04:30:24 | 4 of 4 `ok` |
| 5 | 21 | `20261019T043802Z` | planned: drift check (3.4) | 04:38:02–04:39:14 | 4 of 4 `ok` |

- All 20 runs ended `ok` with zero check violations. No protocol stopped early, no run was aborted,
  and no sample crossed the 4.80 GiB threshold.
- Code state (3.1): every protocol and run record shows commit `0e3c130` with the checked paths
  clean and the same `source_sha256` and `uv_lock_sha256` as the four window configs, and each
  run's `windows_config` equals its set's `config.json`.
- Spark settings and the recorded environment are identical in all 20 `run.json` files.
- Records: `data/outputs-experiments/full-2026-10-12/rolling-252-s<stride>/`; the two stride-21
  protocols share a folder (3.3), and the stride-3 folder has an `EXPLORATORY.txt` note.

### 5.2 Run log

The session used shell helpers written by Claude Code, sourced from the home folder and committed
unchanged as `docs/stride-session.zsh` (SHA-256 starting `a190e66642d17cb8`; it hard-codes the
repository path `$HOME/leveraged-etf-risk-analytics`): `prechecks` ran the 3.2 checks and appended
them to the run log, `pause5` paused for five minutes, `avail` took the 3.2 memory reading and
started nothing below its minimum, `protocol` ran the 3.3 command unchanged apart from the stride,
and `watch_runs` printed the running pipeline's elapsed time every 10 s for the abort rule. Each
protocol started right after a five-minute pause and a reading of at least 3.0 GiB.

| Protocol | Checks | Low Power Mode, power, Docker, Java or pipeline | Apps open besides Terminal and Finder | Load average (1, 5, 15 min) | Pause before start | Available at start (GiB) | Lowest free before a run (GiB) |
| -------- | -----: | ----------------------------------------------- | ------------------------------------- | --------------------------- | ------------------ | -----------------------: | -----------------------------: |
| Stride 21 | 02:51:58 | off, AC, none, none | none | 9.63, 18.09, 10.04 | 02:57:41–03:02:41 | 3.42 | 3.02 |
| Stride 14 | 03:38:50 | off, AC, none, none | VS Code (quit at 03:44:34, 5.3) | 1.91, 2.16, 2.90 | 03:44:48–03:49:48 | 4.32 | 3.38 |
| Stride 7 | 03:52:40 | off, AC, none, none | VS Code (quit at 03:53:06, 5.3) | 16.00, 8.25, 4.83 | 03:53:08–03:58:08 | 4.51 | 3.46 |
| Stride 3 (exploratory) | 04:14:14 | off, AC, none, none | a messaging app and one further app (5.3) | 2.29, 2.55, 3.67 | 04:22:40–04:27:40 | 3.31 | 2.97 |
| Stride 21, repeated | 04:32:27 | off, AC, none, none | a messaging app (5.3) | 2.94, 4.71, 3.88 | 04:33:01–04:38:01 | 4.50 | 3.10 |

At every check the code was unchanged (`HEAD 0e3c130`, no changed code files) and no Spark scratch
folder existed. Apps are the visible apps that `lsappinfo` listed at the checks. Before strides 14,
7 and 3 and the repeated stride 21, the checks were not repeated after apps were quit (5.3). The
last column is the lowest `free_memory_before_bytes` among each protocol's four runs (the task's
criterion 5): stride 3's run 2 started with 2.97 GiB free, below 3.0 GiB, which 3.2 requires only
before a protocol starts.

- **Before stride 21:** a first attempt (checks at 02:30:27, with one other app open) did not
  start: four readings gave 1.82, 1.79, 2.19 and 2.18 GiB. The Mac was restarted (boot at
  02:47:14), and the checks were repeated with only Terminal and Finder open. The protocol started
  15.5 minutes after the boot.
- **Before stride 14:** the first pause (03:39:23–03:44:23) ended with 1.40 GiB, so nothing
  started. A further reading gave 5.11 GiB, and a second full pause preceded the protocol.
- **Before stride 7:** the checks came about 90 s after the stride-14 runs ended, so the
  1-minute load average (16.00) includes that protocol.
- **Before stride 3:** the first pause (04:14:24–04:19:24) ended with 2.20 GiB and a second reading
  gave 2.13 GiB, so nothing started; a reading of 3.43 GiB and a second full pause followed.
- **Before the repeated stride 21:** a reading of 4.51 GiB preceded the pause.
- **Abort rule:** no run came near its limit. Longest runs: 22.7, 21.2, 26.0, 42.0 and 18.8 s
  against 135, 177, 303, 639 and 135 s. The watcher covered every run except runs 1 and 2 of the
  repeated stride 21, where it started 53 s late (04:38:55); those runs took 18.8 and 18.2 s. No
  after-abort checks (3.6) were needed.

### 5.3 Deviations and uncertain conditions

1. **Stride 3 was run although 3.5 did not admit it.** The gate failed on memory (5.4). The author
   ran the stride-3 protocol deliberately, to see whether it would complete despite failing the
   gate. This departs from 1.3 and 3.5. Its four runs are kept and reported, labeled
   **exploratory**: they are shown separately from the planned protocols, and any comparison with
   section 4 is exploratory. Sections 1–4 are unchanged.
2. **The checks before strides 14 and 7 were taken while VS Code was open.** VS Code's own logs show
   it was quit before each pause, at 03:44:34 and 03:53:06; its next launches were at 03:51:26,
   after the stride-14 runs, and at 04:00:02, after the stride-7 runs. The author confirms it was
   quit with Cmd-Q. The checks were not repeated after quitting, so the run log itself does not
   show the condition at the start of these two protocols.
3. **Apps open during stride 3 and the repeated stride 21 are uncertain.** A messaging app was
   listed at both checks, and one further app at the stride-3 checks; the checks were not
   repeated. The author recalls that the messaging app may have been open during the stride-3 runs
   and cannot confirm its state during the repeated stride-21 runs. Its process running afterwards
   started at 04:41:22, after both protocols, so it was quit at some point before then; when is not
   recorded. The further app's state is unknown. VS Code was closed during both protocols (quit at
   04:14:13, next launch at 04:40:35).

### 5.4 Stride-3 decision (3.5)

From the stride-7 records, all four runs, warm-up included:

| Condition | Value | Result |
| --------- | ----- | ------ |
| 1. Status | four runs `ok`; protocol not stopped early | holds |
| 2. Memory | P = 2.714 GiB (warm-up run); 2.714 × 12,518 / 5,364 + 0.5 = 6.83 GiB, above the 4.80 GiB cap | fails whatever memory is available (the largest P that can pass is 1.84 GiB) |
| 3. Time | W = 26.0 s; 4 × 26.0 × 12,518 / 5,364 = 243 s (4.05 min), within 60 min | holds |

Decision: stride 3 was not admitted. It was run anyway as an exploratory protocol (5.3, item 1):
its largest total RSS was 2.767 GiB against the projected 6.83 GiB, and its four runs took 163 s
against the projected 243 s.

### 5.5 Drift check (3.4)

| | First stride 21 (`20261019T030242Z`) | Repeated stride 21 (`20261019T043802Z`) |
| --- | --- | --- |
| Measured wall times | 20.92, 22.71, 22.23 s | 18.15, 18.30, 18.03 s |
| Median | 22.226 s | 18.153 s |
| Median of the largest total RSS per run (no rule) | 2.619 GiB | 2.681 GiB |

The repeated median is 4.073 s (18.3%) below the first, outside the ±10% tolerance
(20.00–24.45 s). By 3.4 this is reported as drift, and comparisons across strides are marked as
affected. Nothing was re-run.

### 5.6 Measurements CSV

_Drafted with Claude Code (Opus 5.5) at the author's request, from
`analysis/collect_measurements.py` and its output._

**Location.** `uv run python analysis/collect_measurements.py` reads the five protocol JSONs and
twenty `run.json` files under `data/outputs-experiments/full-2026-10-12/` and writes
`data/outputs-experiments/measurements.csv`. Like the records, the CSV is under `data/`, which is
not in Git; it is rebuilt from the records, and rebuilding it gives a byte-identical file.

**Rows.** One row per started run (3.7): 20 rows, warm-ups included, ordered by protocol start and
run number. Before writing, the script stops unless there are five protocols; each protocol's run
count, run ids, statuses, warm-up flags and exit codes agree with its run records; the code hashes
of every run and protocol equal the window config's, with the checked paths clean (3.1); and every
protocol has a role, with the `EXPLORATORY.txt` note next to exactly the exploratory one.

**Columns.** 37, with values copied from the records without rounding and booleans written as
`True` or `False`:

| Group | Columns | From |
| ----- | ------- | ---- |
| Identity | `protocol_id` (the protocol's UTC start), `stride`, `run_id`, `run_number`, `warmup`, `status`, `exit_code` | protocol JSON; `run.json` (`windows_config.stride`, `measurement`) |
| Role | `role`: `baseline`, `planned`, `exploratory` or `drift_check` | the script's `ROLES` mapping by protocol id (5.1, 5.3) |
| Run start | `started_at_utc` | `measurement` |
| Input size | `windows`, `path_day_rows` (1x and 2x path-day rows written) | `row_counts` |
| Spark settings | `shuffle_partitions_requested`, `adaptive_enabled`, `default_parallelism`, `jvm_max_heap_bytes` | `spark` |
| Summed stage task counts | `tasks_window_stats`, `tasks_model`, `tasks_summaries`, `tasks_checks` | `stage_task_counts` |
| Time, seconds | `wall_s` (measure's clock, from process start to exit); the pipeline's own phases `session_start_s`, `window_stats_and_construction_check_s`, `model_and_path_days_s`, `summaries_and_pairing_s`, `checks_s` and `total_in_process_s` | `measurement`, `timings_seconds` |
| Memory, bytes | `free_memory_before_bytes`, `peak_rss_total_bytes`, `peak_rss_driver_bytes`, `peak_rss_spark_jvm_bytes`, `peak_rss_python_worker_bytes`, `peak_rss_other_bytes` | `measurement` |
| Sampling | `samples`, `max_processes_seen`, `threshold_crossed` | `measurement` |
| Code | `git_commit`, `git_worktree_clean` | `code` |

**Limitations.**

- **Aborted-run placeholders are not supported yet.** For an aborted run, `measure` keeps a
  placeholder `run.json` without the window config or the code state (3.6). A row needs the window
  config for its stride, so the script stops on such a run instead of writing a partial row. No run
  in this experiment was aborted, so all 20 started runs are in the CSV, as 3.7 requires.
- **Task counts are summed stage task counts, not partition counts.** `tasks_<group>` adds up the
  task counts of the stages that each job in the group lists, after adaptive execution. A stage
  listed by more than one job, such as a shuffle stage that a later job lists as skipped, is counted
  each time, so the sum need not equal the number of tasks that ran; whether that happens here was
  not checked. The sums are not the number of partitions in each shuffle, which the pipeline does
  not record, and `shuffle_partitions_requested` is the setting, not the number of partitions Spark
  used.
- **Memory is sampled RSS.** Peaks come from samples every 0.25 s, so shorter peaks can be missed;
  summed RSS counts shared pages once per process; and the per-type peaks occur at different
  moments, so they do not add up to the total (the limits `measure` records).
- **Roles are not in the records.** They come from the script's mapping (5.1); only the
  exploratory role is cross-checked, against the `EXPLORATORY.txt` note.

### 5.7 Summary tables

_Drafted with Claude Code (Opus 5.5) at the author's request, from
`data/outputs-experiments/measurements.csv` (values computed by script)._

Summaries use only runs that ended `ok` and are not warm-ups (3.7). Every run ended `ok`, so each
protocol contributes its three measured runs. Each cell gives the median and, in brackets, the
minimum and maximum of those three runs. Wall time is `wall_s`; peak memory is
`peak_rss_total_bytes` in GiB (2^30 bytes). Section 4's memory predictions concern the largest
total RSS over all four runs, warm-up included; that value is in the CSV, not in these tables. The
comparison with section 4, which is unchanged, belongs to section 6.

**Planned protocols** (comparisons across these strides are affected by drift, see below)

| Stride | Protocol | Role | Windows (vs stride 21) | Path-day rows | Runs used | Wall time (s) | Peak total RSS (GiB) |
| -----: | -------- | ---- | ---------------------: | ------------: | --------: | ------------- | -------------------- |
| 21 | `20261019T030242Z` | baseline | 1,790 (1.00) | 900,714 | 3 | 22.226 (20.918–22.711) | 2.619 (2.482–2.667) |
| 14 | `20261019T034949Z` | planned | 2,683 (1.50) | 1,350,000 | 3 | 20.294 (20.221–20.346) | 2.684 (2.676–2.686) |
| 7 | `20261019T035809Z` | planned | 5,364 (3.00) | 2,698,866 | 3 | 25.660 (24.699–26.001) | 2.705 (2.681–2.707) |

**Drift check: the repeated stride 21** (shown separately, not as a further stride)

| Stride | Protocol | Role | Windows | Path-day rows | Runs used | Wall time (s) | Peak total RSS (GiB) |
| -----: | -------- | ---- | ------: | ------------: | --------: | ------------- | -------------------- |
| 21 | `20261019T043802Z` | drift_check | 1,790 | 900,714 | 3 | 18.153 (18.029–18.295) | 2.681 (2.658–2.694) |

**Drift detected (3.4, 5.5):** the repeated median is 18.3% below the baseline's, outside the
±10% tolerance, so the comparisons across strides in the planned table are marked as affected.

**Exploratory: stride 3** (not admitted by 3.5 and run deliberately, 5.3; kept out of the planned
table)

| Stride | Protocol | Role | Windows (vs stride 21) | Path-day rows | Runs used | Wall time (s) | Peak total RSS (GiB) |
| -----: | -------- | ---- | ---------------------: | ------------: | --------: | ------------- | -------------------- |
| 3 | `20261019T042741Z` | exploratory | 12,518 (6.99) | 6,298,446 | 3 | 40.170 (39.907–42.032) | 2.733 (2.730–2.767) |

## 6. Answers and limits

_The questions are those of the Part B task of 2026-10-17. In 6.1–6.4, the parts marked as drafted
give facts, computed with Claude Code (Opus 5.5) by script from
`data/outputs-experiments/measurements.csv` (runs that ended `ok`, warm-ups excluded, unless a
part says otherwise) and from section 4. The answers, marked "Answer (author)", are the author's,
copied from the conversation of 2026-10-19; at the author's request Claude Code applied its
review's corrections and added figures the answers lacked: in (a) b, the comparison with the fixed
phases and the crossover; in (b) the explicit comparison and the ratio against the repeated
stride 21; in (c) the statistic's name, the change by type and the excess over the heap; in (d)
the H1 and drift misses and the Stage 2 facts; in (e) the sampling wording. The planned analysis
uses the baseline and the planned strides and is affected by drift (5.5); analyses with the
repeated stride 21 are post hoc, and those with stride 3 exploratory (5.3)._

### 6.1 (a) Fixed and per-window cost

> Fit wall time ≈ a + b × windows. What are a and b? How does a compare with the fixed phases?
> At which stride does the per-window part overtake the fixed part?

_Drafted with Claude Code (Opus 5.5): ordinary least squares on the medians of 5.7, with
x = windows._

| Fit | Medians used (s) | a (s) | b (ms per window) | a / stride-21 median | Largest fit error | b × windows = a at |
| --- | ---------------- | ----: | ----------------: | -------------------- | ----------------: | ------------------ |
| Planned (1.2): first stride 21, 14, 7 | 22.226, 20.294, 25.660 | 18.79 | 1.201 | 84.5% of 22.226 s | 8.5% | 15,642 windows (stride 2.4) |
| Post hoc: repeated stride 21, 14, 7 | 18.153, 20.294, 25.660 | 14.56 | 2.078 | 80.2% of 18.153 s | 0.8% | 7,006 windows (stride 5.4) |
| Exploratory: first stride 21, 14, 7, 3 | 22.226, 20.294, 25.660, 40.170 | 16.91 | 1.821 | 76.1% of 22.226 s | 9.3% | 9,286 windows (stride 4.0) |
| Post hoc and exploratory: repeated stride 21, 14, 7, 3 | 18.153, 20.294, 25.660, 40.170 | 14.67 | 2.039 | 80.8% of 18.153 s | 0.9% | 7,196 windows (stride 5.2) |

- **H1 and H2 (1.2), planned fit:** a = 18.79 s is positive and 84.5% of the stride-21 median, so
  H1's condition (over 50%) holds. b is positive and the fitted values (20.94, 22.01 and 25.23 s)
  are within 8.5% of the measured medians (22.226, 20.294 and 25.660 s), so H2's criteria hold.
  With three points the fit has one residual degree of freedom.
- **Fixed phases:** at stride 21, `session_start` has a median of 3.155 s and the time outside the
  pipeline's clock (wall minus in-process) 1.286 s, together 4.442 s. a is 5.95 times
  `session_start` and 4.23 times the two together; Python worker startup is not timed separately
  (1.2). 6.2 gives every phase.
- **Crossover:** with windows ≈ 37,550 / stride (2.4), the planned fit's per-window part equals a
  at 15,642 windows, about stride 2.4. That is beyond the largest planned workload (5,364 windows)
  and beyond stride 3 (12,518), so it is an extrapolation. The other fits put the crossover between
  7,006 and 9,286 windows (stride 5.4 to 4.0).

**Answer (author).** The intercept a is 18.79 s, or 84.5% of the baseline's median wall time
(22.226 s), and the slope b is 1.201 ms per window. a is 4.23 times the fixed phases at stride 21
(`session_start` plus the time outside the pipeline's clock, 4.442 s). The per-window part would
overtake a at about 15,642 windows, roughly stride 2.4. H1 and H2 meet their numerical criteria,
but three points and detected drift make the evidence weak. The intercept is not directly
measured overhead, and the crossover estimate is an extrapolation.

### 6.2 (b) The fastest-growing phase

> Which phase grows fastest? Does that match the hypothesis about shuffled rows growing about
> 252/stride times and one pandas call per window?

_Drafted with Claude Code (Opus 5.5): median seconds over the three measured runs of each
protocol. Each median is taken on its own, so the phases do not add up exactly to the total._

| Phase | Stride 21 (baseline) | Stride 14 | Stride 7 | Change from 21 to 7 | Stride 21, repeated | Stride 3 (exploratory) |
| ----- | -------------------: | --------: | -------: | ------------------- | ------------------: | ---------------------: |
| `session_start` | 3.155 | 2.359 | 2.478 | −0.677 (×0.79) | 2.346 | 2.487 |
| `window_stats_and_construction_check` | 4.969 | 4.252 | 5.079 | +0.110 (×1.02) | 4.013 | 7.895 |
| `model_and_path_days` | 4.872 | 5.213 | 8.099 | +3.227 (×1.66) | 4.340 | 16.279 |
| `summaries_and_pairing` | 4.293 | 4.471 | 5.780 | +1.487 (×1.35) | 3.806 | 9.622 |
| `checks` | 1.916 | 1.425 | 1.619 | −0.297 (×0.84) | 1.460 | 1.864 |
| total in-process | 20.940 | 19.057 | 24.570 | +3.630 (×1.17) | 17.352 | 39.303 |
| outside the pipeline's clock (wall − in-process) | 1.286 | 1.237 | 0.914 | −0.373 (×0.71) | 0.801 | 0.867 |
| wall time | 22.226 | 20.294 | 25.660 | +3.434 (×1.15) | 18.153 | 40.170 |

- From stride 21 to stride 7, the windows, the window-member rows (252 per window: the expansion
  that, by spec §8, multiplies the rows Spark shuffles by about 252 / stride) and the grouped pandas
  calls (one per window, spec §8) all grow 2.997 times (5,364 / 1,790); the path-day rows written
  grow 2.996 times.
- Among the planned protocols, `model_and_path_days` grows most, by 3.227 s (×1.66), then
  `summaries_and_pairing`, by 1.487 s (×1.35). `window_stats_and_construction_check` changes by
  0.110 s, and `session_start` and `checks` are shorter at stride 7 than at stride 21.
- `model_and_path_days` per window (1.2): 2.722, 1.943 and 1.510 ms at strides 21, 14 and 7
  (repeated stride 21: 2.425 ms; stride 3: 1.300 ms).
- Every phase of the repeated stride 21 is shorter than the first one's, by 0.455 to 0.955 s
  (drift, 5.5).

**Answer (author).** `model_and_path_days` grows most in seconds, by 3.227 s (×1.66), while the
windows, the shuffled rows and the pandas calls grow ×2.997; against the repeated stride 21 its
ratio is ×1.87. So the phase grows, but less than in proportion to the hypothesized costs. Its
time per window falls, consistent with shared fixed costs or better parallelism. Without
profiling, the cause remains uncertain.

### 6.3 (c) Peak memory by process type

> How does peak memory change, and which process type grows? How does that relate to the driver
> JVM's 1.0 GiB maximum heap?

_Drafted with Claude Code (Opus 5.5): median peak RSS in GiB over the three measured runs of each
protocol. `spark_jvm` is the driver JVM (Spark runs in local mode), the Python workers are
PySpark's, and the Python driver is the pipeline process itself (`etf_risk.measure`'s process
types)._

| Process type | Stride 21 (baseline) | Stride 14 | Stride 7 | Stride 21, repeated | Stride 3 (exploratory) |
| ------------ | -------------------: | --------: | -------: | ------------------: | ---------------------: |
| Spark JVM (`spark_jvm`) | 1.520 | 1.518 | 1.542 | 1.521 | 1.571 |
| Python workers | 1.032 | 1.053 | 1.047 | 1.045 | 1.050 |
| Python driver | 0.114 | 0.114 | 0.115 | 0.115 | 0.113 |
| other | 0.003 | 0.003 | 0.003 | 0.003 | 0.003 |
| total (5.7) | 2.619 | 2.684 | 2.705 | 2.681 | 2.733 |
| processes seen (median of the largest count per run) | 11 | 11 | 12 | 12 | 13 |

- From stride 21 to stride 7, the median total peak rises from 2.619 to 2.705 GiB (+0.086 GiB,
  +3.3%) while the windows grow 2.997 times. The largest change by type is the JVM's, +0.022 GiB;
  the Python workers' is +0.015 GiB and the Python driver's +0.001 GiB.
- The JVM's maximum heap is 1,073,741,824 bytes (1.000 GiB) in all 20 runs (`jvm_max_heap_bytes`).
  Its median peak RSS is 0.518 to 0.571 GiB above that in every protocol.
- The per-type medians do not add up to the total, because each type peaks at its own moment (5.6).

**Answer (author).** The median peak total RSS of the measured runs rises only 3.3% from stride 21
to 7 (2.619 to 2.705 GiB); the largest sample over all four runs rises 1.8% (2.667 to 2.714 GiB).
By type, the JVM changes most, by 0.022 GiB, then the Python workers, by 0.015 GiB. Fixed-size
windows and bounded worker concurrency may explain this. JVM RSS includes non-heap memory, so it
can exceed the 1 GiB heap limit; here it does by 0.518 to 0.571 GiB.

### 6.4 (d) Predictions against results

> Where were your predictions off, and why?

_Drafted with Claude Code (Opus 5.5) from section 4, which is unchanged, and the CSV. Memory items
use the largest total RSS over all four runs, warm-up included, as section 4 does; time items use
the medians of 5.7._

| Section 4 | Predicted | Measured | Result |
| --------- | --------- | -------- | ------ |
| 4.1 stride-21 median wall time | 45 s, band 35–55 s | 22.226 s | outside, 12.774 s below the band |
| 4.2 stride-21 largest total RSS | 1.3–1.8 GiB | 2.667 GiB | outside, 0.867 GiB above |
| 4.3 stride-14 median wall time | 59 s, band 47.2–76.7 s | 20.294 s | outside, below |
| 4.3 stride-7 median wall time | 101 s, band 80.8–131.3 s | 25.660 s | outside, below |
| 4.4 stride-14 largest total RSS | 1.3–2.0 GiB | 2.686 GiB | outside, above |
| 4.4 stride-7 largest total RSS | 1.3–2.4 GiB | 2.714 GiB | outside, above |
| 4.3 model, 17 s + 28 s × window ratio | a = 17 s, b = 15.64 ms per window | planned fit: a = 18.79 s, b = 1.201 ms per window | a 1.79 s higher; b 13.0 times smaller |
| 4.5 H1 | "over 50%" condition does not hold (a ≈ 17 s, 38% of 45 s) | a = 18.79 s, 84.5% of 22.226 s | contradicted: the condition holds |
| 4.5 H2 | positive slope, fitted values within 20% | b = 1.201 ms per window; largest error 8.5% | as expected, with one residual degree of freedom |
| 4.6 stride-3 decision | skipped (at 3.5 GiB available, P at most 1.29 GiB) | not admitted: P = 2.714 GiB, above the 1.84 GiB that could ever pass | as expected; P outside the predicted stride-7 range |
| 4.6 drift check | repeated median within 10% of the first | 18.153 s, 18.3% below | drift (5.5) |
| 4.6 abort limits | 135, 177 and 303 s | longest runs 22.7, 21.2 and 26.0 s (repeated stride 21: 18.8 s) | no run aborted |
| 4.3 and 4.4 stride 3, exploratory (they applied only if 3.5 admitted it) | 213 s, band 170.4–276.9 s; 1.4–3.2 GiB | 40.170 s; 2.767 GiB | time outside, below; memory inside |

**Answer (author).** Time predictions were too high: the baseline was faster than expected, and
predicted per-window cost was about 13 times the fitted value. Memory predictions were too low
except for exploratory stride 3. The expected H1 outcome was also wrong: the intercept was close
to the prediction (18.79 against 17 s), but the stride-21 median was about half the predicted
45 s, so the intercept exceeded 50% of it. The drift check, expected to pass, found drift. The
predictions were anchored to Stage 2's records (4.1, 4.3). Since then the code (apart from
`provenance.py`, 2.5), the windows and the Spark settings are unchanged, but free memory before
the stride-21 runs was 1.34–1.62 GiB in Stage 2 and 3.02–3.50 GiB here; Low Power Mode was off
here, and its state during Stage 2 was not recorded. Machine state may contribute, but the
records cannot establish the cause.

### 6.5 (e) What these measurements cannot show

> What can these measurements not show?

**Answer (author).** The results cover one machine, configuration and dataset. Drift, uncertain
application state and only three planned sizes limit the conclusions. RSS was sampled every
0.25 s, so short peaks can be missed, and summed RSS counts shared pages once per process. Actual
shuffle partitions, spilling and CPU use were not measured, so the results do not establish
mechanisms or predict larger-scale performance.
