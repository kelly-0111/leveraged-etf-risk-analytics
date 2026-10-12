# Data sources

**Status: not fully verified.** The checks below have been run; each one
passed or its result is recorded as a limitation, and the results table states
what each check does **not** establish. A comparison with a second data source
and a review of the data's terms of use have **not** been done. The extreme
price moves listed at the end are **unverified** and must not be presented as
findings until a second source checks them.

## Source

- Provider: Yahoo Finance (<https://finance.yahoo.com/>), accessed with
  [yfinance](https://github.com/ranaroussi/yfinance) 1.7.0.
- Request: `Ticker.history(start, end, interval="1d", auto_adjust=False, actions=True)`;
  `end` is exclusive. A `start` before a ticker's first trading day returns
  history from that first day.
- Fields returned: Date, Open, High, Low, Close, Adj Close, Volume, Dividends,
  Stock Splits. QQQ, a fund, also has a Capital Gains column; the four stocks
  do not.
- Terms of use: not reviewed. The open-source license of yfinance does not
  cover the data itself. Raw and processed files are therefore not committed
  (`data/` is gitignored); they are re-created with the commands below.

## Snapshots

### `full-2026-10-12` — full history (main analysis)

Downloaded 2026-10-12 21:13:10 UTC by `src/etf_risk/download.py`
(Python 3.12.14, yfinance 1.7.0), `start=1970-01-01`, `end=2026-01-01`.
Files: `data/raw/yahoo/full-2026-10-12/<TICKER>.csv` and `manifest.json`
(SHA-256 `803485e37893376516d4565b6ceb270c2ed348b495121df17e72c66d1723e520`).

| Ticker | Rows | First date | Last date | Bytes | SHA-256 |
|---|---|---|---|---|---|
| NVDA | 6,778 | 1999-01-22 | 2025-12-31 | 939,990 | `b1e9850eb1fc4bba7dff9b592cb984ff163640eef76369cb2a4bb68513548145` |
| AAPL | 11,355 | 1980-12-12 | 2025-12-31 | 1,545,170 | `2d9e33615f682ec73a9815781a0ca4966c89c088d9d210feabbbc86e6b5c55cc` |
| MSFT | 10,029 | 1986-03-13 | 2025-12-31 | 1,268,244 | `44352f1ea3afb229232503f1675d87d2a7dce917ba9bd5a9e9428c9c9d81fdf8` |
| TSLA | 3,902 | 2010-06-29 | 2025-12-31 | 523,796 | `15a6051110399fd71700930e96e81a5e90220aff9cb0e3ff2884e20d38c424b8` |
| QQQ | 6,746 | 1999-03-10 | 2025-12-31 | 900,899 | `baa549c88c0d11a119c83a7d8ca3e7b510ee8544ce222e864f10ca918df8567a` |

### Prototype snapshot — 2020–2025

Downloaded 2026-10-11 06:50:35 UTC (Python 3.12.10, yfinance 1.7.0) by a
download check written with Codex assistance and run outside this repository;
same request settings with `start=2020-01-01`, `end=2026-01-01`. Files:
`data/raw/yahoo/<TICKER>-2020-2025.csv` and `verification.json`. Used by the
prototype only.

| Ticker | Rows | First date | Last date | Bytes | SHA-256 |
|---|---|---|---|---|---|
| NVDA | 1,508 | 2020-01-02 | 2025-12-31 | 203,481 | `ed5fb8e0af56f286c28bf096197e4e29826594f84a567547c3fe693e8f1e0ed8` |
| AAPL | 1,508 | 2020-01-02 | 2025-12-31 | 200,289 | `9237e695a2e29b6f4b200e3a3b3bea2975af268db285060041735c5ba46b3025` |
| MSFT | 1,508 | 2020-01-02 | 2025-12-31 | 197,668 | `c6e6268ed7a5332967848bbd63522650f2f21142fca7a9ecde5b4e169a001961` |
| TSLA | 1,508 | 2020-01-02 | 2025-12-31 | 198,408 | `8ceca614c3043f47a8f1489e6be62cfd4fb8f498e0b0bc865aff711857e71dec` |

## Reproducing

```bash
uv sync --group download
uv run --group download python -m etf_risk.download \
    --tickers NVDA AAPL MSFT TSLA QQQ --out data/raw/yahoo/full-<YYYY-MM-DD>
uv run python -m etf_risk.ingest --raw-dir data/raw/yahoo/full-<YYYY-MM-DD>
```

A new download goes into a new folder and will not reproduce the checksums
above (see limitation 3). Ingest refuses any CSV whose SHA-256 differs from its
manifest, so processed data always names the snapshot it came from
(`data/processed/<snapshot>/`, also stored in the Parquet metadata).

## Field conventions

- **Date**: midnight exchange time with a UTC offset that changes with daylight
  saving time; the first 10 characters are the trading date.
- **Close**: split-adjusted, not dividend-adjusted (Yahoo's convention; the
  split-day check below is consistent with it but does not prove it).
- **Adj Close**: split- and dividend-adjusted (Yahoo's convention). Used for
  returns.
- **Dividends**: cash per share on the ex-dividend date, in the same
  split-adjusted units as Close (the dividend check below matches on that basis).
- **Stock Splits**: ratio on the split date (2.0 = 2-for-1, 1.5 = 3-for-2).
- **Volume**: shares, split-adjusted (NVDA volumes in 2000 exceed 2 billion).
- **Capital Gains** (QQQ only): capital-gain distributions per share, which
  yfinance reports for funds. All 6,746 values in `full-2026-10-12` are exactly
  0, with none missing. The column is not used, since returns come from Adj
  Close. Whether Adj Close would include a nonzero distribution has not been
  checked, so a future snapshot with nonzero values needs that check before use.
- **daily_return** (processed): `Adj Close_t / Adj Close_(t-1) - 1` between
  consecutive trading days; null on each ticker's first row, never zero-filled.

Processed output: `data/processed/<snapshot>/daily_returns/<TICKER>.parquet`
(`ticker` string, `date` date32, `adjusted_price` double, `daily_return`
double) and `quality_report.json`.

## Checks and results (`full-2026-10-12`)

Run by `etf_risk.ingest` with `etf_risk.validate`; full results in
`data/processed/full-2026-10-12/quality_report.json`.

| Check | Result | What it does not establish |
|---|---|---|
| CSV SHA-256 against the manifest | all five match | that the data is correct; only that each file is unchanged since its download |
| Duplicate dates; missing, infinite or non-positive prices; negative volume | none | that the values themselves are right |
| Trading calendar: each ticker's dates compared with the NYSE schedule from pandas_market_calendars 5.5.0, only between its own first and last date | 0 missing rows and 0 extra rows for all five tickers | agreement with an official exchange record: the library's schedule is the reference, and NYSE stands in for Nasdaq (limitation 6) |
| Weekdays without a session | all are regular holidays or special closures: 1985-09-27 (Hurricane Gloria), 2001-09-11 to 09-14, 2012-10-29 to 10-30 (Hurricane Sandy), and national days of mourning 1994-04-27, 2004-06-11, 2007-01-02, 2018-12-05, 2025-01-09 | that the library's list of closures is complete |
| Split-day returns (23 splits) | for each split, the Adj Close return on the split date is compared with the move an unadjusted split would show, 1/ratio − 1 (−50% for 2-for-1); a return within 5 percentage points of it counts as an error. None of the 23 split-day returns resembles an unadjusted split | that each split adjustment is correct: the ratio, the date, and the adjustment of earlier prices, volumes and dividends are not independently checked. An adjustment with a wrong ratio or on the wrong day would show up as an unusual move rather than as an error, so split days with moves of 10% or more are listed as unverified below |
| Dividend adjustment (317 ex-dividend days) | on every ex-dividend day the step in log(Adj Close / Close) equals −log(1 − dividend / previous close) within 9.1e−7 | that the dividend amounts and dates are correct: Adj Close is only shown to be consistent with Yahoo's own dividend records; 38 small steps on other days remain unexplained (limitation 2) |
| Zero-volume rows | AAPL 1981-08-10 | whether that day's price was traded (limitation 5) |
| Rows with Open = High = Low = Close | AAPL only: 28 rows (1981: 1, 1984: 2, 1985: 25); 27 of them have volume and a nonzero return | whether those closes are correct |
| QQQ Capital Gains column (6,746 rows) | every value exactly 0; no missing values | how Adj Close would treat a nonzero distribution (not needed for this snapshot) |

## Limitations and unresolved items

1. **Unverified: no second source yet.** An automated download from Stooq was
   attempted on 2026-10-12 and blocked by a browser check. Until a second source
   is compared, the days listed below may be data errors as well as market
   events, and results that depend on them are labeled unverified.
2. **Unresolved Adj Close / Close steps.** Besides the ex-dividend steps, 38
   small steps occur on days without a dividend (NVDA 3, AAPL 4, MSFT 18, QQQ 13,
   TSLA 0), each at most 1.4e−6 in log units, against roughly 1e−3 to 1e−2 for
   real dividend steps. A second download the same day (17:29 UTC) had 50 such
   steps (AAPL 20, MSFT 16, NVDA 1, QQQ 13), so their number and dates change
   between downloads. Rounding of stored prices is a plausible cause (63–91% of
   Adj Close values in that download were exactly representable as 32-bit
   floats), but the cause has **not** been confirmed. Each step changes one daily
   return by at most about 1.4e−6.
3. **Re-downloads are not byte-identical.** Compared with this snapshot:

   | Other download | Rows and dates | Largest daily-return difference |
   |---|---|---|
   | 2026-10-12 17:29 UTC, full history | identical | NVDA 1.5e−6, AAPL 1.7e−6, MSFT 1.8e−6, QQQ 1.9e−6, TSLA 0 (same SHA-256) |
   | 2026-10-11 06:50 UTC, prototype 2020–2025 | identical over 2020–2025 | NVDA 8.4e−7, AAPL 8.8e−7, MSFT 8.7e−7, TSLA 0 |

   Only TSLA, which pays no dividend, was reproduced exactly. Comparisons across
   downloads need a tolerance of about 1e−5; Python-versus-Spark comparisons on
   the same files use 1e−9.
4. **Coarse prices before 2001.** US stock prices were quoted in fractions of a
   dollar until 2001, so early years have many unchanged-price days: zero
   daily returns are 9.3% of AAPL's 1984–85 rows, against 3.3% of all AAPL rows
   (MSFT 2.1%, NVDA 0.75%, QQQ 0.56%, TSLA 0.26%). Early volatility is measured
   on coarser prices.
5. **Close-only bars.** The AAPL rows with Open = High = Low = Close have no
   intraday range; close-to-close returns still use them. The zero-volume row on
   1981-08-10 may carry the previous price rather than a trade.
6. **Calendar reference.** The NYSE schedule is used for the Nasdaq-listed
   stocks and QQQ. It matched every date, but a Nasdaq-only closure would not be
   distinguished from a missing row.
7. **Tickers are not independent.** QQQ tracks the Nasdaq-100, which includes
   the other four tickers for at least part of the period, and all five share
   market-wide shocks (1987, 2000–2002, 2008, 2020). The four stocks are current
   large companies, so their histories are those of survivors.
8. **Terms of use not reviewed** (see Source).

## Unverified: days to confirm with a second source

Rule in `etf_risk.validate.unverified_extreme_days`: |daily return| ≥ 20%; a
move over 15% reversed the next day by over 13% (both days listed); or a split
day with |return| ≥ 10%. All 36 days are **unverified** (second-source status:
not checked).

AAPL 2000-09-29 (−51.87%) is the only day in the data below −50%, so it is the
only day that would trigger the 2x model's breach rule. The NVDA moves in 2000
(+42.4% on 03-07, +26.5% and −26.2% on 03-13 and 03-14, −14.1% on the 2-for-1
split day 06-27) have internally consistent prices and volumes, which does not
confirm them.

| Ticker | Date | Return | Reason |
|---|---|---|---|
| NVDA | 1999-08-19 | +21.2% | \|return\| ≥ 20% |
| NVDA | 2000-02-10 | +20.5% | \|return\| ≥ 20% |
| NVDA | 2000-03-07 | +42.4% | \|return\| ≥ 20% |
| NVDA | 2000-03-13 | +26.5% | \|return\| ≥ 20%; reversed by the next day |
| NVDA | 2000-03-14 | −26.2% | \|return\| ≥ 20%; reverses the previous day |
| NVDA | 2000-04-05 | +22.3% | \|return\| ≥ 20% |
| NVDA | 2000-06-27 | −14.1% | split day with \|return\| ≥ 10% |
| NVDA | 2000-12-08 | +22.8% | \|return\| ≥ 20% |
| NVDA | 2000-12-22 | +25.8% | \|return\| ≥ 20% |
| NVDA | 2001-01-03 | +30.7% | \|return\| ≥ 20% |
| NVDA | 2002-07-31 | −31.8% | \|return\| ≥ 20% |
| NVDA | 2002-11-08 | −21.9% | \|return\| ≥ 20% |
| NVDA | 2003-02-14 | +22.0% | \|return\| ≥ 20% |
| NVDA | 2003-05-09 | +33.1% | \|return\| ≥ 20% |
| NVDA | 2004-08-06 | −35.2% | \|return\| ≥ 20% |
| NVDA | 2008-07-03 | −30.7% | \|return\| ≥ 20% |
| NVDA | 2016-11-11 | +29.8% | \|return\| ≥ 20% |
| NVDA | 2023-05-25 | +24.4% | \|return\| ≥ 20% |
| AAPL | 1983-09-23 | −25.4% | \|return\| ≥ 20% |
| AAPL | 1987-10-19 | −24.4% | \|return\| ≥ 20% |
| AAPL | 1987-10-26 | −21.1% | \|return\| ≥ 20% |
| AAPL | 1993-07-16 | −23.1% | \|return\| ≥ 20% |
| AAPL | 1996-07-18 | +23.7% | \|return\| ≥ 20% |
| AAPL | 1997-08-06 | +33.2% | \|return\| ≥ 20% |
| AAPL | 1998-01-02 | +23.8% | \|return\| ≥ 20% |
| AAPL | 2000-09-29 | −51.9% | \|return\| ≥ 20% |
| MSFT | 1987-10-19 | −30.1% | \|return\| ≥ 20% |
| TSLA | 2012-01-13 | −19.3% | reversed by the next day |
| TSLA | 2012-01-17 | +16.7% | reverses the previous day |
| TSLA | 2013-05-09 | +24.4% | \|return\| ≥ 20% |
| TSLA | 2020-03-18 | −16.0% | reversed by the next day |
| TSLA | 2020-03-19 | +18.4% | reverses the previous day |
| TSLA | 2020-08-31 | +12.6% | split day with \|return\| ≥ 10% |
| TSLA | 2020-09-08 | −21.1% | \|return\| ≥ 20% |
| TSLA | 2024-10-24 | +21.9% | \|return\| ≥ 20% |
| TSLA | 2025-04-09 | +22.7% | \|return\| ≥ 20% |

QQQ has no day matching the rule.
