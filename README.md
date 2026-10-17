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
| Model and Spark pipeline: 252-day windows on a shared trading-day grid, 1x and 2x for each window, full-scale checks, an independent sample check, measurement tooling | Implemented; one configuration measured (stride 21) |
| Three Spark SQL analyses of the results ([`analysis/`](analysis/)) | Implemented |
| Docker image for the pipeline | Implemented |
| Performance experiments (stride, partitions, caching) | Pending |
| Figures and final write-up | Planned |
| Optional systems extension: MySQL job table, Kafka job queue, Redis result cache | Planned ([spec](docs/spec.md), §11) |

## Reading guide

1. **This README**: status, key results and how to run everything.
2. **[docs/spec.md](docs/spec.md)**: the research questions (§2), the model and
   its assumptions (§3), how results are checked (§6), the window design (§7)
   and the full results of the stride-21 run (§8).
3. **[docs/data-sources.md](docs/data-sources.md)**: where the data comes from,
   the checks run on it, and what is not verified.
4. **The analyses**: [`sql_overview.py`](analysis/sql_overview.py) (counts and
   medians per ticker), [`sql_comparison.py`](analysis/sql_comparison.py) (how
   often 2x beats twice the 1x return) and
   [`sql_sensitivity.py`](analysis/sql_sensitivity.py) (medians without the
   windows that use an unverified day).
5. **The code**, in data-flow order: in `src/etf_risk/`, `download` → `ingest`
   (with `validate`) → `windows` → `spark_pipeline` (which runs `model`) →
   `verify`; `measure` times runs. Module overview: spec §5.
6. **How AI was used**: [AI assistance](#ai-assistance) below.

## Key results

From the run of record: snapshot `full-2026-10-12` (daily history through
2025-12-31), 252-day windows starting every 21 trading days. The windows
overlap, so these numbers describe one history, not independent samples; spec
§8 has the details.

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
- Runtime and memory have been measured for one configuration only: stride 21
  on one Apple Silicon laptop (8 cores, 8 GiB RAM), Spark in local mode with
  default settings. Over three measured runs, the median wall time was 44.7 s
  and the median peak memory 1.27 GiB (summed resident memory of the run's
  processes, sampled every 0.25 s). These numbers describe that machine and
  configuration, not others; the performance experiments are pending.

## Running

Requires Python 3.12, Java 17 and [uv](https://docs.astral.sh/uv/); run the
commands from the repository root. Memory use has been measured on one machine
only (see Key results): there, a stride-21 run peaked at about 1.3 GiB; other
machines, settings and denser strides have not been measured.

```bash
uv sync                                    # .venv from uv.lock
uv run --group measure pytest              # tests, no network

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
- Strides below 21 need `--allow-dense-stride` and have not been measured yet.
- The 2020–2025 prototype regression needs the prototype CSVs, which were
  downloaded outside this repository ([data-sources.md](docs/data-sources.md)).

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
  stop rule; the experiments are pending.

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
  the queries. It later added the scripts' command-line input.
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

1. **Performance experiments** (mine): stride, shuffle-partition and caching
   experiments with `etf_risk.measure`, read with `explain("formatted")`.
2. **Data**: compare the 36 unverified extreme days with a second source, and
   review the data's terms of use.
3. **Figures and the final write-up** (Stage 4).
4. **Optional systems extension** (spec §11): Docker Compose with MySQL, Kafka
   and Redis for a job queue and a result cache, with recovery and caching
   experiments.
