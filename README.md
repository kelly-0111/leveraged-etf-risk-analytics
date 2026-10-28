# Leveraged ETF Risk Analytics

How does a fund that resets to twice its underlying every trading day behave
over a one-year holding period, compared with the underlying and with twice its
return? This CS544 independent project replays a daily-reset 1x/2x model on the
daily return history of NVDA, AAPL, MSFT, TSLA and QQQ over 252-trading-day
windows, runs it in PySpark with full-scale checks, and analyzes the results
with Spark SQL. The results describe historical windows of a few tickers; they
are not forecasts, and the model ignores fees, financing and execution.

## Status

| Part | Status |
|---|---|
| Data: download with manifest, checksum-enforced ingest, validation, daily returns in Parquet | Implemented |
| Model and Spark pipeline: 252-day windows on a shared trading-day grid, 1x and 2x for each window, full-scale checks, an independent sample check, measurement tooling | Implemented |
| Three Spark SQL analyses of the results ([`analysis/`](analysis/)) | Implemented |
| Docker image for the pipeline | Implemented |
| Stride experiment: runtime and memory at strides 21, 14 and 7 ([docs/experiments.md](docs/experiments.md)) | Complete; drift detected, stride 3 exploratory only |
| Shuffle-partition experiment: three Spark partition settings at stride 7 ([docs/partition-experiment.md](docs/partition-experiment.md)) | Complete; B (200 partitions, coalescing off) slower than A and C; no clear memory difference; outputs within tolerance |
| Pandas baseline: the Spark pipeline against a single-process pandas implementation, end to end, at stride 7 ([docs/pandas-baseline.md](docs/pandas-baseline.md)) | Complete; pandas had a 41.8% shorter median wall time and a 26.6% lower median peak total RSS; outputs within tolerance |
| Caching experiment: no cache, the window-member rows, and those plus the four read-back tables, at stride 7 ([docs/caching-experiment.md](docs/caching-experiment.md)) | Complete; no clear difference in runtime or peak memory; outputs within tolerance |
| Figures and final write-up: twelve figures drawn from the result files, the results write-up and a demo ([docs/results.md](docs/results.md), [docs/demo.md](docs/demo.md)) | Complete; figure numbers checked against the documented values, conclusions approved by the author; eight of the figures need the data under `data/`, which is not in Git |
| Optional systems extension: MySQL job table, Kafka job queue, Redis result cache ([spec §11](docs/spec.md)) | **In progress, not complete**: the outstanding items in the rows below |
| Extension: job table, Kafka delivery and reconciler, and a worker running the real pipeline ([docs/job-table.md](docs/job-table.md), [docs/job-queue.md](docs/job-queue.md), [docs/worker-pipeline.md](docs/worker-pipeline.md)) | Implemented; tested on SQLite and against MySQL and Kafka. The MySQL and Kafka container limits held in one isolated check under host memory pressure; **the native processes' memory is not validated** |
| Extension: recovery study, E1 and E2 ([docs/recovery-part-a.md](docs/recovery-part-a.md), [docs/recovery-part-b.md](docs/recovery-part-b.md)) | Documented: E1 has supporting correctness observations. **Valid formal E2 recovery-time evidence is now available** from formal batch-3, for this host and configuration only: one batch of 30 jobs, valid for correctness and recovery times, on verified frozen code. Its answers and limits (Part B, section 10) were drafted with Claude Code and approved by the author on 2026-10-27. batch-1 and batch-2 stay invalid for recovery times |
| Extension: Redis result cache for the three summary queries ([docs/result-cache.md](docs/result-cache.md)) | Implemented: accepted and registered runs only; falls back to Spark when Redis fails |
| Extension: result-cache experiment, E3 ([docs/result-cache-experiment.md](docs/result-cache-experiment.md), [docs/result-cache-part-b.md](docs/result-cache-part-b.md)) | Complete: one valid formal batch of host-specific paired latency observations, not a general performance claim |
| Test suite | **Open**: two intermittent failures of `tests/test_baseline_collector.py`, with the cause unresolved ([spec §10](docs/spec.md)) |

## Reading guide

1. **This README**: status, key results and how to run everything.
2. **[docs/results.md](docs/results.md)**: the final write-up, with the findings
   for each research question, the twelve figures, the limitations and the
   conclusions; [docs/demo.md](docs/demo.md) walks through the tests, the
   figures, the SQL analyses and a small pipeline run, and says what a fresh
   clone can reproduce.
3. **[docs/spec.md](docs/spec.md)**: the research questions (§2), the model and
   its assumptions (§3), how results are checked (§6), the window design (§7),
   the full results of the stride-21 run and summaries of the stride,
   shuffle-partition and caching experiments and the pandas baseline (§8).
4. **[docs/data-sources.md](docs/data-sources.md)**: where the data comes from,
   the checks run on it, and what is not verified.
5. **[docs/experiments.md](docs/experiments.md)**: the stride experiment, with
   its design and predictions (committed before any measured run), run log,
   deviations, measurements and answers;
   [`collect_measurements.py`](analysis/collect_measurements.py) builds its
   measurements CSV from the run records.
6. **[docs/partition-experiment.md](docs/partition-experiment.md)**: the
   shuffle-partition experiment, with its design, rules and predictions
   (committed before any measured run), run log, deviations, measurements,
   plans and answers; the [session helpers](docs/partition-session.zsh) ran
   its session, and the [collector](analysis/collect_partition_measurements.py)
   builds its measurements CSV and checks its acceptance criteria.
7. **[docs/pandas-baseline.md](docs/pandas-baseline.md)**: the pandas
   baseline, an end-to-end comparison of the Spark pipeline with a
   single-process pandas implementation of the same computation, with its
   design, rules and predictions (committed before any measured run), run log,
   measurements and answers; the [session helpers](docs/baseline-session.zsh)
   ran its session, and the
   [collector](analysis/collect_baseline_measurements.py) builds its
   measurements CSV and checks its acceptance criteria.
8. **[docs/caching-experiment.md](docs/caching-experiment.md)**: the caching
   experiment, which compared no cache, a cache of the window-member rows, and
   one of those rows plus the four read-back tables, with its design, rules and
   predictions (committed before any measured run), run log, measurements,
   cache checks and answers; the [session helpers](docs/caching-session.zsh)
   ran its session, and the
   [collector](analysis/collect_caching_measurements.py) builds its
   measurements CSV and checks its acceptance criteria.
9. **The optional systems extension** ([spec §11](docs/spec.md), in progress; its
   architecture diagram, guarantees and open items are there):
   - **the job queue:** [docs/job-table.md](docs/job-table.md) (the job table and its
     guarantees), [docs/job-queue.md](docs/job-queue.md) (Kafka delivery and the
     reconciler) and [docs/worker-pipeline.md](docs/worker-pipeline.md) (the worker
     with the real pipeline, and the memory check);
   - **the recovery study:** [docs/recovery-experiments.md](docs/recovery-experiments.md)
     (the design), [docs/recovery-part-a.md](docs/recovery-part-a.md) (the approved
     protocol), [docs/recovery-part-b.md](docs/recovery-part-b.md) (the formal batches and
     the answers) and [docs/recovery-sql.md](docs/recovery-sql.md) (the cross-check);
   - **the result cache:** [docs/result-cache.md](docs/result-cache.md) (identity, fallback,
     and the reviewed registry [docs/accepted-runs.json](docs/accepted-runs.json));
   - **its experiment E3:** [docs/result-cache-experiment.md](docs/result-cache-experiment.md)
     (Part A, the approved protocol, with the
     [session helpers](docs/result-cache-session.zsh)) and
     [docs/result-cache-part-b.md](docs/result-cache-part-b.md) (the formal batch and the
     answer);
   - **a correction:** [docs/host-counters-correction.md](docs/host-counters-correction.md)
     (page counters that were recorded as swap traffic).

   The commands are in the [runbook](#systems-extension-services-runbook) below.
10. **The analyses**: [`sql_overview.py`](analysis/sql_overview.py) (counts and
    medians per ticker), [`sql_comparison.py`](analysis/sql_comparison.py) (how
    often 2x beats twice the 1x return) and
    [`sql_sensitivity.py`](analysis/sql_sensitivity.py) (medians without the
    windows that use an unverified day).
11. **The code**, in data-flow order: in `src/etf_risk/`, `download` →
    `ingest` (with `validate`) → `windows` → `spark_pipeline` (which runs
    `model`) → `verify`.
    - **Around the pipeline:** `measure` times runs, `plans` records a run's execution plans,
      `pandas_pipeline` computes the same results in one process without Spark, and `plots`
      draws the figures from the result files.
    - **The extension:**
      - `jobs/`: the job table, worker, Kafka delivery, reconciler, the recovery harness and
        its fault hooks;
      - `runs`: which runs the cache may serve;
      - `services`: the Compose services' readiness, memory peaks and the Redis client;
      - `cache`: the result cache's logic;
      - `summary`: the three queries, one-shot or warm;
      - `cache_experiment`: E3's driver.
    - **Collectors:** each experiment's batch collector is in `analysis/`.

    Module overview: spec §5.
12. **How AI was used**: [AI assistance](#ai-assistance) below.

## Key results

From the run of record: snapshot `full-2026-10-12` (daily history through
2025-12-31), 252-day windows starting every 21 trading days. The windows
overlap, so these numbers describe one history, not independent samples; spec
§8 has the details, and [docs/results.md](docs/results.md) the figures and the
conclusions.

- All 46 check tests passed with no violation on 1,790 windows, and the
  independent Python check matched all 1,074 paths it compared. Every window
  without a breach (1,778) passes the two identity checks of the 2x model (exact
  log gap, drawdown bound).
- 12 AAPL windows breach at 2x (a daily loss of 50% or more); all contain
  2000-09-29, a day not yet checked against a second source. They have no 2x
  return and are left out of the 2x statistics below.

| | AAPL | MSFT | NVDA | TSLA | QQQ |
|---|---|---|---|---|---|
| Windows | 529 | 466 | 311 | 174 | 310 |
| Median 1x return | 24.4% | 22.8% | 39.5% | 22.5% | 16.6% |
| Median 2x return | 35.2% (517 windows) | 39.9% | 51.3% | 13.5% | 31.4% |
| 2x return above twice the 1x return | 219 of 517 (42.4%) | 164 of 466 (35.2%) | 141 of 311 (45.3%) | 43 of 174 (24.7%) | 140 of 310 (45.2%) |
| Windows using an unverified extreme day | 78 | 12 | 92 | 57 | 0 |
| Median 2x return without those windows | 48.5% (451) | 41.4% (454) | 52.2% (219) | −12.3% (117) | 31.4% (310) |

- For every ticker, the daily-reset 2x return exceeded twice the 1x return in
  fewer than half of the windows.
- The last row is a sensitivity analysis: TSLA's 2x median falls from 13.5% to
  −12.3%, while AAPL's rises from 35.2% to 48.5%. It shows how much a result
  depends on periods with extreme days, not whether those days are data errors.
- Runtime and memory were measured on one Apple Silicon laptop (8 cores, 8 GiB
  RAM), with Spark in local mode and, apart from the shuffle-partition
  experiment, default settings; the numbers describe that machine and those
  configurations, not others. For the run of record, the median wall time over
  three measured runs was 44.7 s and the median peak memory 1.27 GiB (summed
  resident memory of the run's processes, sampled every 0.25 s).
- The stride experiment ([docs/experiments.md](docs/experiments.md)) measured
  the same stride-21 workload and strides 14 and 7 (1.5 and 3 times the
  windows) on 2026-10-19: median wall times 22.2, 20.3 and 25.7 s, median
  peaks 2.62 to 2.70 GiB, and every check passed in all 20 runs. At stride 21
  that is half the run of record's time and about twice its memory, with more
  memory free before the runs; the records do not establish why. A linear fit
  over the three strides gives an intercept of 18.8 s (85% of the stride-21
  median) and 1.2 ms per window: an estimate from three points, not measured
  overhead. A repeated stride-21 protocol at the end had an 18.3% shorter
  median wall time than the first, beyond the 10% drift tolerance, so
  comparisons across strides are marked as affected. Stride 3 was run although
  the experiment's memory rule did not admit it; its results (40.2 s,
  2.73 GiB) are exploratory only.
- The shuffle-partition experiment
  ([docs/partition-experiment.md](docs/partition-experiment.md)) ran the
  stride-7 workload on 2026-10-22 (UTC) with three settings: A, Spark's
  defaults (200 shuffle partitions, AQE coalescing on); B, 200 partitions with
  coalescing off; C, 8 partitions with coalescing off. Eight runs each, in the
  order A–B–C–C–B–A, all passed every check. Median times without the plan
  recording were 26.5, 44.6 and 25.3 s: B's was 69% longer than A's and 77%
  longer than C's, in the same direction in both halves of the order, while A
  and C showed no clear difference. Median peaks were 2.69 GiB in all three,
  and `paired` and `path_summary` matched A's within the tolerance. In B, one
  join stayed a sort-merge join where AQE chose a broadcast join in A and C.
  No drift was detected; the machine checks were recorded only before the
  first protocol, and the last protocol followed a two-hour break.
- The pandas baseline
  ([docs/pandas-baseline.md](docs/pandas-baseline.md)) compared the Spark
  pipeline at Spark's defaults end to end with a single-process pandas
  implementation of the same computation, on the stride-7 workload on
  2026-10-22 (UTC): eight runs each, in the order Spark–pandas–pandas–Spark,
  all passing every check. The pandas implementation's median wall time was
  15.4 s against Spark's 26.4 s (41.8% shorter), and its median peak total RSS
  1.97 against 2.68 GiB (26.6% lower), in the same direction in both halves of
  the order; its outputs matched Spark's within the tolerance. Its model phase
  took longer than Spark's and its other phases less time. Both call the same
  model function but handle data, aggregate and write in their own ways, so
  the comparison does not isolate Spark's overhead. The prediction had put
  pandas at about 40 s, slower than Spark; no drift was detected.
- The caching experiment
  ([docs/caching-experiment.md](docs/caching-experiment.md)) ran the stride-7
  workload on 2026-10-22 (UTC) with three caching strategies: A, no cache; B,
  the window-member rows cached from the window statistics through the model
  phase; C, those rows and the four tables read back after each phase, cached
  through the checks. Eight runs each, in the order A–B–C–C–B–A, all passed
  every check, and Spark's storage information and the execution plans
  verified every cache's fill and release and the cached reads in each phase.
  Median times without the plan recording were 26.5, 27.0 and 28.7 s: B's and
  C's were 2.1% and 8.4% longer than A's, below the 10% threshold, so there was
  no clear difference. Caching the members lengthened the window statistics by
  0.9 s and shortened the model phase by 0.3 s; C's further caches lengthened
  the model phase by 1.3 s, with no observed net saving in the later phases.
  Median peaks were 2.68–2.70 GiB, with C's caches, about 0.2 GiB, held in the
  JVM heap. All outputs matched A's within the tolerance; in B and C, seven
  floating-point summary columns differed in the last bits, and a different
  order of addition is a plausible but unestablished explanation. No drift was
  detected.

## Running

Requires Python 3.12, Java 17 and [uv](https://docs.astral.sh/uv/); run the
commands from the repository root. Memory use has been measured on one machine
only (see Key results): there, runs at strides 21 to 7 peaked at 1.2 to 2.8 GiB,
and the exploratory stride-3 runs at up to 2.8 GiB; other machines, and Spark
settings beyond the shuffle-partition experiment's three, have not been
measured.

```bash
uv sync                                    # .venv from uv.lock
uv run --group measure --group plots pytest  # tests, no network

# 1. Download a snapshot (network). Set SNAPSHOT once; the later steps use it.
SNAPSHOT=full-$(date +%Y-%m-%d)
uv run --group download python -m etf_risk.download \
    --tickers NVDA AAPL MSFT TSLA QQQ --out data/raw/yahoo/$SNAPSHOT
# 2. Check the prices, then write daily returns       -> data/processed/$SNAPSHOT/
uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo/$SNAPSHOT
# 3. Define 252-day windows at stride 21              -> data/windows/$SNAPSHOT/rolling-252-s21/
uv run python -m etf_risk.windows --snapshot $SNAPSHOT --kind rolling --stride 21
# 4. Run the model in Spark; every check runs at full scale -> $RUN
RUN=data/outputs/windows/$SNAPSHOT/rolling-252-s21/first
uv run python -m etf_risk.spark_pipeline --windows data/windows/$SNAPSHOT/rolling-252-s21 --run-id first
# 5. Compare a sample of windows with an independent Python computation
uv run python -m etf_risk.verify --run $RUN
# 6. The three SQL analyses of the run
uv run python analysis/sql_overview.py $RUN
uv run python analysis/sql_comparison.py $RUN
uv run python analysis/sql_sensitivity.py $RUN
# 7. The figures of this run; X1-X4 read the committed CSVs -> data/figures-$SNAPSHOT/
uv run --group plots python -m etf_risk.plots --run $RUN --snapshot data/processed/$SNAPSHOT \
    --windows data/windows/$SNAPSHOT/rolling-252-s21 --out data/figures-$SNAPSHOT
```

Optional steps, with the same variables:

```bash
# Calendar-year windows, a labeled supplement
uv run python -m etf_risk.windows --snapshot $SNAPSHOT --kind calendar-year
uv run python -m etf_risk.spark_pipeline --windows data/windows/$SNAPSHOT/calendar-year --run-id first
# Timed runs with peak memory: a fresh process per run; no further run once 60% of RAM is crossed
uv run --group measure python -m etf_risk.measure --repeats 4 -- --windows data/windows/$SNAPSHOT/rolling-252-s21
```

- Unless `--end` is changed, the download stops at 2025-12-31, the same range as
  the run of record. Yahoo can revise adjusted prices, so a new snapshot can
  differ slightly ([data-sources.md](docs/data-sources.md)).
- Nothing is overwritten: `windows` refuses an existing folder (unless
  `--overwrite`), and `spark_pipeline` asks for a new `--run-id`.
- `spark_pipeline` also takes `--shuffle-partitions N` and `--coalesce on|off`
  (Spark settings, refused inside an existing Spark session) and
  `--record-plans`, which writes `plans.json` with the run's final plans and
  the partition counts Spark used
  ([partition-experiment.md](docs/partition-experiment.md) 4).
- `spark_pipeline --cache none|members|members-checks` caches the
  window-member rows, or those and the four read-back tables, and records the
  fills, releases and Spark's storage information in `run.json`
  ([caching-experiment.md](docs/caching-experiment.md) 4).
- `etf_risk.pandas_pipeline` takes `--windows`, `--out-root` and `--run-id`
  and writes the Spark pipeline's outputs from one process, without Spark;
  `etf_risk.measure --pipeline pandas` times it
  ([pandas-baseline.md](docs/pandas-baseline.md) 4).
- Strides below 21 need `--allow-dense-stride`. Strides 14, 7 and 3 were
  measured in the stride experiment (stride 3 as exploratory only); stride 1
  has not been run.
- The 2020–2025 prototype regression needs the prototype CSVs, which were
  downloaded outside this repository ([data-sources.md](docs/data-sources.md)).
- `etf_risk.plots` draws the figures of [docs/results.md](docs/results.md).
  X1–X4 read the experiments' measurement CSVs, committed in
  [docs/measurements](docs/measurements/README.md), so they also work from a
  fresh clone (`--figures X1 X2 X3 X4`). An input that is missing, cannot be
  parsed or lacks a column the figures read is named, and nothing is drawn;
  `--check` compares the numbers with the documented values and says which
  figures it could not compare ([docs/demo.md](docs/demo.md)).

### Docker

The image holds the code, Python 3.12, Java 17 and the locked dependencies. Data
is never copied into it: `docker/run.sh` mounts `data/processed` and
`data/windows` read-only and writes container results to `data/outputs-docker`
and `data/windows-docker`, apart from native results. Keep the image local; do
not push it.

```bash
docker/build.sh            # builds etf-risk:dev; records the commit and whether src/, pyproject.toml, uv.lock were clean
docker/run.sh              # the test suite in the container (the transcript-hook tests stay native)
# Steps 4-5 in the container, on the definitions from step 3
docker/run.sh python -m etf_risk.spark_pipeline --windows data/windows/$SNAPSHOT/rolling-252-s21 \
    --out-root data/outputs-docker/windows --run-id first
docker/run.sh python -m etf_risk.verify --run data/outputs-docker/windows/$SNAPSHOT/rolling-252-s21/first
```

The SQL analyses run natively on a container run's folder as well. The image
has no `.git`, so run records take the commit and clean flag from the build
(`code_source: "build"`) and the image ID from `docker/run.sh`; `source_sha256`
still identifies the code. `docker/run.sh` sets a memory limit
(`ETF_RISK_MEMORY`, default `2.5g`, a budget to validate) with no swap and
prints the container's cgroup memory peak, which includes page cache. Timings
in the container (a Linux VM on macOS, data on bind mounts) are a separate
configuration, not comparable with native measurements.

### Systems extension services (runbook)

These are for the optional job queue and result cache ([spec §11](docs/spec.md)).
- **Compose services.** MySQL, Kafka and Redis run in Docker Compose
  ([docker/compose.yaml](docker/compose.yaml)), each with a memory limit and reachable from
  this machine only.
- **Clients.** The job package's clients, PyMySQL and confluent-kafka, are pinned in the
  `jobs` dependency group; the result cache's, redis-py, in the `cache` group.
- **Git worktrees.** In a worktree, `data/` is a symlink to the main checkout's (ignored by
  Git): `ln -s <main checkout>/data data`.

```bash
docker compose -f docker/compose.yaml up -d --wait mysql kafka
# The healthchecks only see open ports; this waits for a MySQL login and SELECT 1, and Kafka metadata
uv run --group jobs python -m etf_risk.services ready mysql kafka
# The job tests against both services (offline, they run on SQLite and skip these)
ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
    uv run --group jobs python -m pytest tests/test_jobs_*.py
# Each container's cgroup memory.peak against its limit, and the containers of other projects (a count)
uv run python -m etf_risk.services peaks mysql kafka
uv run python -m etf_risk.services others
# Break each guard on purpose and expect a failing test; set the two variables to include MySQL and Kafka
uv run --group jobs python tests/mutation_check.py --out data/outputs-mutations
docker compose -f docker/compose.yaml down -v      # removes the data volumes as well
```

- **Memory budgets** (spec §11) are measured with no other project's containers in Docker's
  VM; `services others --require-none` exits 1 otherwise.

The job queue with the real pipeline ([docs/worker-pipeline.md](docs/worker-pipeline.md)) runs
on the same two services. The worker, a standby worker and the reconciler each get a terminal
of their own, and stop with Ctrl-C (a graceful stop). Outputs go to
`data/outputs/jobs/<store id>/`, and event logs to `data/outputs/jobs/events/`.

```bash
export ETF_RISK_JOBS_DB=mysql://root:jobs-test@127.0.0.1:3307/etf_jobs
docker compose -f docker/compose.yaml up -d --wait mysql kafka
uv run --group jobs python -m etf_risk.services ready mysql kafka
uv run --group jobs python -m etf_risk.jobs init-db          # database, tables and store id; safe to repeat
uv run --group jobs python -m etf_risk.jobs create-topic
uv run --group jobs python -m etf_risk.jobs reconciler       # terminal 2
uv run --group jobs python -m etf_risk.jobs worker --worker-id A    # terminal 3
uv run --group jobs python -m etf_risk.jobs worker --worker-id B    # terminal 4: a standby
uv run --group jobs python -m etf_risk.jobs submit --snapshot full-2026-10-12 --kind calendar-year
uv run --group jobs python -m etf_risk.jobs status --check  # the tables; exit 1 on an invariant violation
uv run --group jobs python -m etf_risk.jobs cleanup         # dry run: folders of attempts that ended unaccepted
uv run --group jobs python -m etf_risk.jobs export data/outputs/jobs-export   # before `down -v`
docker compose -f docker/compose.yaml down -v
```

- **Acceptance runs.** The milestone's acceptance runs take minutes each:
  `ETF_RISK_LIVE_PIPELINE=1` together with the two service variables runs
  `tests/test_jobs_live_pipeline.py`.

The result cache ([docs/result-cache.md](docs/result-cache.md)) needs Redis only. Its client,
redis-py, is pinned in the `cache` dependency group. It serves a run only if the job table
accepted it or the reviewed registry `docs/accepted-runs.json` lists it; the run of record is
registered. Every Compose project here shares one name, so the last line stops and removes
the redis service alone (`down -v` would remove MySQL and Kafka too).

```bash
docker compose -f docker/compose.yaml up -d --wait redis
uv run --group cache python -m etf_risk.services ready redis      # a PING through the cache's client
RUN=data/outputs/windows/full-2026-10-12/rolling-252-s21-r2/run-20261013T043848Z-4
# One request in a new process: a miss runs Spark and stores the result, a repeat is a hit
uv run --group cache python -m etf_risk.summary query overview --run $RUN
uv run --group cache python -m etf_risk.summary query overview --run $RUN --tickers QQQ TSLA
# A warm process: one JSON request per line on stdin, one answer per line on stdout
printf '{"query": "comparison", "run": "%s"}\n' $RUN $RUN | uv run --group cache python -m etf_risk.summary serve
# Spark only, without Redis
uv run --group cache python -m etf_risk.summary --no-cache query sensitivity --run $RUN
# A job run instead: --job <id> with ETF_RISK_JOBS_DB set, and --group jobs as well
# Check a historical run and print its registry entry (--write adds it; the author approves it)
uv run python -m etf_risk.runs register $RUN --approved-on 2026-10-25
# The cache's tests offline, then against this Redis; then its focused mutations
uv run --group cache --group jobs python -m pytest tests/test_cache_contract.py tests/test_summary.py \
    tests/test_runs_resolver.py tests/test_redis_client.py
ETF_RISK_REDIS_URL=redis://127.0.0.1:6380/0 uv run --group cache python -m pytest tests/test_redis_live.py
uv run --group jobs python tests/mutation_check.py --out data/outputs-mutations --only key-ignores-digest \
    params-shallow-copy decode-ignores-identity breaker-ignored client-retries
uv run python -m etf_risk.services peaks redis
docker compose -f docker/compose.yaml rm --stop --force redis
```

## Data

Daily prices come from Yahoo Finance through yfinance and are not committed
(`data/` is gitignored; the data's terms of use have not been reviewed). The
run of record uses the full history of NVDA, AAPL, MSFT, TSLA and QQQ through
2025-12-31 (snapshot `full-2026-10-12`); a 2020–2025 snapshot of the four
stocks was used for the prototype. Download settings, dates, checksums, the
checks run, and open limitations are in [docs/data-sources.md](docs/data-sources.md).

**Data status: partially checked, not fully verified.** Trading dates match
the NYSE schedule, and Adj Close is consistent with Yahoo's own dividend
records. For splits, none of the 23 split-day returns resembles an unadjusted
split; this does not independently prove that every split adjustment is
correct. A second-source comparison and a terms-of-use review have not been
done, and 36 extreme price moves, including AAPL on 2000-09-29, are
**unverified**.

## Course concepts

- **Python**: a sequential reference model with hand-calculated tests, and the
  data checks.
- **PyArrow and Parquet**: daily returns, window definitions and results with
  explicit schemas.
- **PySpark and Spark SQL**: grouped pandas functions and a broadcast join over
  every window; DataFrame aggregation and three SQL analyses; execution plans
  read with `explain("formatted")`.
- **Docker**: an image that reproduces the native results exactly on this
  project's machine.
- **Performance measurement**: fresh-process runs with memory sampling and a
  stop rule; a stride experiment whose design and predictions were committed
  before any measured run; a shuffle-partition experiment, likewise committed
  in advance, that compared three partition settings and recorded the
  partition counts Spark used; a pandas baseline, committed the same way, that
  compared the Spark pipeline end to end with a single-process pandas
  implementation; and a caching experiment, committed the same way, that
  compared three caching strategies and checked every cache in Spark's storage
  information and execution plans.
- **Systems** (the optional extension):
  - a MySQL job table with conditional state transitions and attempt tokens;
  - at-least-once Kafka delivery with manual offset commits, and a reconciler;
  - a cache-aside Redis cache keyed by the result's content, with a circuit breaker;
  - Docker Compose services with memory limits;
  - failure-injection (recovery) and paired-latency (cache) experiments, each with a protocol
    approved before its formal batch.

## AI assistance

Most of the code, tests and documentation were written with Claude Code (Opus
5.5) in reviewable stages. I set the requirements and constraints of each
stage, made the design decisions (often choosing among options Claude Code
proposed), reviewed results and diffs, and approved each commit. Each file
written or drafted with AI says so in its header (`AI contribution: ...`),
together with how it was checked.

- **Written by me:** the breach branch of `simulate_path()` in
  `src/etf_risk/model.py`, and the SQL queries in `analysis/`. The queries were
  tutored exercises: Claude Code set the tasks and acceptance criteria and
  reviewed my attempts and my reading of the execution plan, without writing
  the queries. It later added the scripts' command-line input. Likewise
  tutored: the result cache's logic in `src/etf_risk/cache.py`, and moving the
  SQL into `src/etf_risk/summary.py`.
- **Contributed by both:** the recovery experiments and the result-cache
  experiment (E3). Claude Code proposed their designs, wrote the tooling and
  drafted the documents and answers, and ran the recovery batches at my
  instruction; I made every decision and approval, and ran E3's prepared dry
  runs and formal batch.
- **Other tools:** the transcript hook (`.claude/hooks/save_transcript.py`) was
  first drafted with Codex assistance, inspired by a `log_ai.py` script from a
  CS639 project; Claude Code later changed it to save one log per message and
  wrote its redaction module. The 2020–2025 prototype data was downloaded by a
  check written with Codex assistance outside this repository.
- **Records:** `docs/ai-usage/` holds redacted per-message transcripts of the
  Claude Code sessions, which I review before committing them
  ([docs/ai-usage/README.md](docs/ai-usage/README.md)). The hook does not commit
  or push files and has been checked against real sessions; conversations with
  other AI tools are not recorded.

## Next steps

1. **Performance experiments** (mine): the stride, shuffle-partition and
   caching experiments and the pandas baseline are complete
   ([docs/experiments.md](docs/experiments.md),
   [docs/partition-experiment.md](docs/partition-experiment.md),
   [docs/pandas-baseline.md](docs/pandas-baseline.md),
   [docs/caching-experiment.md](docs/caching-experiment.md)).
2. **Data**: compare the 36 unverified extreme days with a second source, and
   review the data's terms of use.
3. **Figures and the final write-up** (Stage 4) are complete
   ([docs/results.md](docs/results.md), [docs/demo.md](docs/demo.md)).
4. **Optional systems extension** (spec §11): in progress, not complete.
   - **Done:**
     - the job queue, which runs the real pipeline
       ([docs/job-table.md](docs/job-table.md), [docs/job-queue.md](docs/job-queue.md),
       [docs/worker-pipeline.md](docs/worker-pipeline.md));
     - the recovery study's documentation, with supporting correctness observations for E1
       ([docs/recovery-part-a.md](docs/recovery-part-a.md),
       [docs/recovery-part-b.md](docs/recovery-part-b.md));
     - valid formal E2 recovery-time evidence for this host and configuration: formal batch-3,
       on 2026-10-27, on verified frozen code. All 30 jobs met their deadlines, and none was
       lost or accepted twice. The answers were approved by the author on 2026-10-27. batch-1
       and batch-2 stay invalid for recovery times;
     - the result cache ([docs/result-cache.md](docs/result-cache.md));
     - its experiment, E3, with one valid formal batch on this Mac
       ([docs/result-cache-experiment.md](docs/result-cache-experiment.md),
       [docs/result-cache-part-b.md](docs/result-cache-part-b.md)). Against the identical
       request in a warm Spark session, a hit took a median 5.4 ms instead of 0.132 s. Blocks
       at 0%, 50% and 90% hits took a median 1.04, 0.51 and 0.14 times their controls' time.
       These are host-specific paired observations.
   - **Outstanding:**
     - a representative validation of the native processes' memory: the container limits
       held, but under host memory pressure;
     - the cause of two intermittent failures of `tests/test_baseline_collector.py`
       ([spec §10](docs/spec.md)).
