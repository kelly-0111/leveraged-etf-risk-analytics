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
uv run pytest                                              # tests (no network)

# Full-history data: needs network and creates a new snapshot folder
uv run --group download python -m etf_risk.download \
    --tickers NVDA AAPL MSFT TSLA QQQ --out data/raw/yahoo/full-<YYYY-MM-DD>
uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo/full-<YYYY-MM-DD>    # -> data/processed/full-<YYYY-MM-DD>/

# Prototype: 2020-2025 CSVs and verification.json in data/raw/yahoo/
uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo --tickers NVDA AAPL MSFT TSLA   # -> data/processed/yahoo/
uv run python -m etf_risk.spark_pipeline --leverages 1 2    # Spark model + SQL summary + Python check
```

Status: the Spark pipeline still runs one full-period path per ticker on the
prototype snapshot. Fixed 252-trading-day holding windows on the full-history
snapshot come next.
