# Demo

A short walk-through on the machine that holds the project's data: the tests, the figures and their
check, the SQL analyses of the run of record, and a small pipeline run with its independent check.
About ten minutes, most of it the test suite.

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 and 2026-10-23. Every command was run on the
project's machine on those days with the results described here; the figures and the pipeline run
went to a scratch folder instead of `data/figures-demo` and `data/outputs-demo`, and the fresh-clone
commands ran in a copy of the repository's committed files, without `data/`._

**Before you start.** Python 3.12, Java 17 and [uv](https://docs.astral.sh/uv/); run everything from
the repository root. Steps 2 to 4 use data under `data/`, which is not in Git and exists only on the
machine that produced it; from a fresh clone, see [From a fresh clone](#from-a-fresh-clone).

## 1. Tests

```bash
uv sync
uv run --group measure --group plots pytest
```

Every test passes, without network, in about five minutes.

## 2. The figures and their check

```bash
uv run --group plots python -m etf_risk.plots --check
uv run --group plots python -m etf_risk.plots --out data/figures-demo
diff -rq docs/figures data/figures-demo && echo identical
```

The first command prints each figure's checked numbers, then `documented values: compared for M1,
…, X4: all match`: every number it compares with spec §8, data-sources.md and the experiment
documents is the same. Its last line, `measurement CSVs: 4 of 4 copies identical to their sources
under data/`, says that the committed copies that X1–X4 read
([measurements/](measurements/README.md)) still equal the collectors' outputs. The second command
redraws the twelve figures and `figures.json`, and `diff` compares them with the committed ones: in
the same environment they are byte-identical. [results.md](results.md) shows the figures with the
findings and limitations.

## 3. The SQL analyses of the run of record

```bash
RUN=data/outputs/windows/full-2026-10-12/rolling-252-s21-r2/run-20261013T043848Z-2
uv run python analysis/sql_overview.py $RUN
uv run python analysis/sql_comparison.py $RUN
uv run python analysis/sql_sensitivity.py $RUN
```

About 10 s each. Their last tables hold the numbers of spec §8 and of the table in results.md,
section 2: for example 529, 466, 311, 174 and 310 windows, the 2x return above twice the 1x return
in 219 of AAPL's 517 compared windows, and TSLA's median 2x return of −12.3% (`-0.1225…`)
without the windows that use an unverified day. `sql_overview.py` also prints the `paired`
schema, a few rows and the physical plan of its query.

## 4. A small pipeline run and its independent check

```bash
uv run python -m etf_risk.spark_pipeline --windows data/windows/full-2026-10-12/calendar-year-r2 --out-root data/outputs-demo --run-id demo-1
uv run python -m etf_risk.verify --run data/outputs-demo/full-2026-10-12/calendar-year-r2/demo-1
```

The first runs the model in Spark over the 151 calendar-year windows, a labeled supplement to the
rolling windows, with every check at full scale, in about 20 s: it prints `demo-1: ok` with the row
counts (151 windows, 75,971 path-day rows) and the run folder, then `ok` for each of the ten groups
of checks. The second compares a sample of windows with an independent Python computation (53
windows and 106 paths on 2026-10-23) and reports 0 mismatches; both find the one breached window,
AAPL's calendar year 2000. The outputs go to `data/outputs-demo/`, outside Git; nothing is
overwritten, so another run needs a new `--run-id`.

## From a fresh clone

The tests need no data, and neither do figures X1–X4, which read the committed measurement CSVs:

```bash
uv sync
uv run --group measure --group plots pytest
uv run --group plots python -m etf_risk.plots --check --figures X1 X2 X3 X4
uv run --group plots python -m etf_risk.plots --figures X1 X2 X3 X4 --out data/figures-x
```

The check reports `documented values: compared for X1, X2, X3, X4: all match` and exits with 0; its
last line names the collectors' outputs that it could not compare the copies with, because they
exist only on the machine that ran the experiments. In the same environment as the committed
figures (this lockfile on the same platform), the four PNGs in `data/figures-x` are byte-identical
to those in `docs/figures`.

The other eight figures need inputs that are not in the repository. The documented ones, which the
documented values describe, are:

| Figures | Input | Built by the README's Running steps |
|---|---|---|
| D1 | processed snapshot `data/processed/full-2026-10-12/` | 1 (download, network) and 2 (ingest) |
| D2 | window definitions `data/windows/full-2026-10-12/rolling-252-s21-r2/` | 3 |
| M1–M5, S1 | pipeline run `data/outputs/windows/full-2026-10-12/rolling-252-s21-r2/run-20261013T043848Z-2/`, finished with status `ok` | 4 |

A new download cannot rebuild them exactly: it makes a new snapshot, and Yahoo revises adjusted
prices, so daily returns can differ slightly ([data-sources.md](data-sources.md), limitation 3).
To draw all twelve figures from a new snapshot, run the README's steps 1 to 4, which set `SNAPSHOT`
and `RUN`, and then:

```bash
uv run --group plots python -m etf_risk.plots --run $RUN --snapshot data/processed/$SNAPSHOT --windows data/windows/$SNAPSHOT/rolling-252-s21 --out data/figures-$SNAPSHOT
```

It reports that it compared X1–X4 with the documented values and did not compare the other eight,
whose inputs are not the documented ones. If an input that a selected figure needs is missing,
cannot be parsed, or lacks a column or field that the figures read, the command names the input and
what is wrong, and computes and writes nothing (exit 2). `--check` exits with 0 only when every
selected figure was compared and matches, with 1 when a value differs, and with 3 when a selected
figure was not compared.

## An intermittent test failure, fixed

`test_measure_runs_the_pandas_pipeline_in_fresh_processes` in `tests/test_pandas_pipeline.py` used
to fail now and then with `AssertionError: assert {'driver', 'spark_jvm'} == {'driver'}`. The test
times the pandas pipeline with `etf_risk.measure` and expected to see only the pipeline's own
process. About 0.4–0.6 s after it starts, though, the pipeline runs short helper commands for its
run record (`git` twice, `uname` and `file` through `platform.platform()`, and `java -version`).
When one of measure's samples, taken every 0.25 s, fell while a helper was running, measure
recorded it, and counted `java -version` as the Spark JVM. The test failed this way in 1 of 20
runs; the failure first seen, in a full test run, kept no traceback, so that it had the same cause
is likely but not shown.

- **The fix:** `measure` counts a Java process as `spark_jvm` only if its command line runs Spark
  (`org.apache.spark`, as the JVM that PySpark starts does); `java -version` and the other helpers
  count as `other`. The test accepts `other` and still fails on `spark_jvm` or `python_worker`.
- **The tests:** deterministic ones in `tests/test_measure.py` classify stand-in processes, among
  them a sample taken while `java -version` runs, and the test session's real Spark JVM; one in
  `tests/test_pandas_pipeline.py` checks that measure still records the Spark JVM of a run of the
  Spark pipeline.
- **The records:** earlier records keep the old rule, under which every process named java counted
  as `spark_jvm`; records since 2026-10-23 carry the rule in their `process_kinds` field. The pandas
  baseline's eight P runs recorded only the pipeline's process, and the pipelines' outputs never
  depended on the rule.

## The optional systems extension

This walk-through covers the pipeline only.
- **Commands:** the extension's (the job queue with a worker running the real pipeline, and the
  result cache) are in the README's
  [runbook](../README.md#systems-extension-services-runbook). They need Docker and its services
  and were not run for this demo.
- **Design, results and open items:** in the documents the README's reading guide lists under
  the extension, and in [spec §11](spec.md).
