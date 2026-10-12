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

## Running the Current Prototype

Requires Python 3.12, Java 17, and [uv](https://docs.astral.sh/uv/). Raw CSVs
are expected in `data/raw/yahoo/` and are not committed. They were downloaded
from Yahoo Finance using yfinance for NVDA, AAPL, MSFT, and TSLA, with daily
data from `2020-01-01` through `2025-12-31` (`end=2026-01-01`, exclusive),
`auto_adjust=False`, and `actions=True`. The ingestion step uses `Adj Close`
for returns. Place each ticker's CSV at
`data/raw/yahoo/<TICKER>-2020-2025.csv`, along with a local
`data/raw/yahoo/verification.json` manifest containing its SHA-256 checksum,
before running the prototype.

```bash
uv sync                                                    # create .venv from uv.lock
uv run python -m etf_risk.ingest --tickers NVDA AAPL MSFT TSLA   # clean -> Parquet + quality report
uv run python -m etf_risk.spark_pipeline --leverages 1 2         # Spark model + SQL summary + Python check
uv run pytest                                              # model, validation, Spark consistency tests
```

Status: all tests pass. Paths are currently one full 2020–2025 history per
ticker; rolling holding windows come next.
