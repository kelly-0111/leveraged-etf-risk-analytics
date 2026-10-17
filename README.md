# Leveraged ETF Risk Analytics

## Project Plan

I plan to build an independent data analytics project that explores the
mechanics and risks of daily leveraged single-stock ETFs. Using historical
stock returns and reproducible simulated return paths, I will examine how
daily leverage resets affect cumulative returns and drawdowns. I will also
calculate theoretical rebalancing demand under explicit assumptions about
leverage and assets under management.

## Technologies and Course Concepts

The project will apply CS544 concepts through the following tools:

- **Python:** data cleaning, a reference implementation of the model, and
  correctness checks.
- **PyArrow and Parquet:** structured storage of historical data, simulated
  paths, and calculation results.
- **PySpark and Spark SQL:** batch processing of many paths and aggregation
  of results by scenario and leverage level.
- **Docker:** a reproducible environment for running the pipeline.
- **Performance benchmarking:** experiments on how data size, partitioning,
  and, where useful, caching affect execution time.

## Basic Workflow

1. Select and document one historical stock dataset, validate its prices,
   calculate daily returns, and save the cleaned data as Parquet.
2. Implement a daily leveraged-return and theoretical rebalancing model in
   Python, checking it against simple hand-calculated examples.
3. Generate reproducible simulated return paths and replay historical returns
   using the same model assumptions.
4. Use Spark to calculate path-level results in batches, verify a small sample
   against the Python implementation, and summarize results with DataFrames
   and Spark SQL.
5. Run controlled performance experiments and produce result tables and plots.

## Expected Results

I aim to produce a reproducible pipeline with validated calculations,
comparisons of unleveraged and daily leveraged returns, drawdown statistics,
and theoretical rebalancing estimates. The final output will also include
performance measurements and explanations of the observed Spark behavior.
The model assumptions and limitations will be documented; simulated results
will not be treated as evidence of actual market impact.

## Claude Code Transcript Hook

The repository includes a hook configured to archive Claude Code session
transcripts in `docs/ai-usage/`. It does not automatically commit or push
files and does not capture conversations from other AI tools. The hook was
drafted with Codex assistance, inspired by a `log_ai.py` script from a CS639
project. The hook has been checked against a real Claude Code session.
AI-generated code will include clear comments describing the contribution
and how I checked the result.

## Data

Daily prices come from Yahoo Finance through yfinance and are not committed
(`data/` is gitignored; the data's terms of use have not been reviewed). The
main analysis uses the full history of NVDA, AAPL, MSFT, TSLA, and QQQ through
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

The research questions, model, data flow, validation approach, and what is
implemented versus planned are described in [docs/spec.md](docs/spec.md).

## Running

Requires Python 3.12, Java 17, and [uv](https://docs.astral.sh/uv/). Returns
are computed from `Adj Close`.

```bash
uv sync                                                    # create .venv from uv.lock
uv run --group measure pytest                              # tests (no network)

# Full-history data: needs network and creates a new snapshot folder
uv run --group download python -m etf_risk.download \
    --tickers NVDA AAPL MSFT TSLA QQQ --out data/raw/yahoo/full-<YYYY-MM-DD>
uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo/full-<YYYY-MM-DD>    # -> data/processed/full-<YYYY-MM-DD>/

# Window definitions -> data/windows/<snapshot>/<name>/ (strides below 21 need --allow-dense-stride)
uv run python -m etf_risk.windows --snapshot full-2026-10-12 --kind rolling --stride 21
uv run python -m etf_risk.windows --snapshot full-2026-10-12 --kind calendar-year

# Spark run: verifies the recorded SHA-256s, then writes data/outputs/windows/<snapshot>/<name>/<run id>/
uv run python -m etf_risk.spark_pipeline --windows data/windows/full-2026-10-12/rolling-252-s21
# Timed runs with peak memory (fresh process per run, stop rule at 60% of RAM)
uv run --group measure python -m etf_risk.measure --repeats 4 -- --windows data/windows/full-2026-10-12/rolling-252-s21
# Independent Python check of a sample (never inside timed runs)
uv run python -m etf_risk.verify --run data/outputs/windows/full-2026-10-12/rolling-252-s21/<run id>

# Prototype: 2020-2025 CSVs and verification.json in data/raw/yahoo/, one full-period window per ticker
uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo --tickers NVDA AAPL MSFT TSLA   # -> data/processed/yahoo/
uv run python -m etf_risk.windows --snapshot yahoo --kind full-period
uv run python -m etf_risk.spark_pipeline --windows data/windows/yahoo/full-period
```

Status: Stage 2 runs fixed 252-trading-day windows on the full-history
snapshot at a sparse stride (21); see [docs/spec.md](docs/spec.md) for what is
implemented and what is still planned.

### Docker

The image holds the code, Python 3.12, Java 17 and the locked dependencies. Data
is never copied into it: `docker/run.sh` mounts `data/processed` and
`data/windows` read-only and writes container results to `data/outputs-docker`
and `data/windows-docker`, apart from native results. Keep the image local; do
not push it.

```bash
docker/build.sh            # builds etf-risk:dev; records the commit and whether src/, pyproject.toml, uv.lock were clean
docker/run.sh              # the test suite in the container (the transcript-hook tests stay native)
# Spark run on the current stride-21 definitions (-r2) -> data/outputs-docker/windows/full-2026-10-12/rolling-252-s21-r2/<run id>/
docker/run.sh python -m etf_risk.spark_pipeline \
    --windows data/windows/full-2026-10-12/rolling-252-s21-r2 --out-root data/outputs-docker/windows
```

The image has no `.git`, so run records take the commit and clean flag from the
build (`code_source: "build"`) and the image ID from `docker/run.sh`;
`source_sha256` still identifies the code. `docker/run.sh` sets a memory limit
(`ETF_RISK_MEMORY`, default `2.5g`, a budget to validate) with no swap and
prints the container's cgroup memory peak, which includes page cache. Timings in
the container (a Linux VM on macOS, data on bind mounts) are a separate
configuration, not comparable with native measurements.
