# Spark performance experiments

> **TODO (author):** authorship line in your own words.

AI contribution: Claude Code (Opus 5.5) sets the tasks and acceptance criteria and reviews each
step. It drafted the parts marked _Drafted with Claude Code_: section 2, items 2.1, 2.2 and 2.5,
from the records named in each part (numbers read from the configs by script, file hashes
recomputed), section 3 from the author's decisions of 2026-10-18, and 4.6 from section 4 and the
Stage 2 records. At the author's request it also applied wording fixes from its reviews in
section 1 and in 2.1, copied the author's predictions 4.1–4.5 from the conversation into
section 4, and added the sentence there that H1 is the least certain prediction.

Status: Part A (sections 1–4) written, apart from the authorship line; not yet committed; no
measured runs yet.

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

> **TODO (Part B):** the run log (the 3.2 checks before each protocol, the 3.5 decision and the
> checks after any abort), the measurements CSV (all runs, 3.7) and a summary table per stride over
> the measured runs that ended `ok`, with failures and early stops reported alongside.

## 6. Answers and limits

> **TODO (author, Part B):** answers to questions (a)–(e) of the task, the comparison with
> section 4, and what these measurements cannot show.
