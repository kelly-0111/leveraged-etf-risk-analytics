# Measurement CSVs

Reviewed copies of the four experiments' measurements CSVs, the inputs of figures X1–X4. They are
committed so that those figures can be redrawn and checked from a fresh clone; the records they were
collected from stay under `data/`, which is not in Git.

_Copied and reviewed with Claude Code (Opus 5.5) on 2026-10-23. Each copy was byte-identical to the
collector's output named below. The files hold run identities, UTC start times, Spark settings,
counts, timings, memory readings, plan descriptors, output-comparison results and commit hashes: no
prices, returns or other market data, and no local paths._

| File | Experiment (columns described in) | Copy of | Rows | Columns |
|---|---|---|---:|---:|
| `stride-experiment.csv` | [experiments.md](../experiments.md) 5.6 | `data/outputs-experiments/measurements.csv` | 20 | 37 |
| `shuffle-partition-experiment.csv` | [partition-experiment.md](../partition-experiment.md) 14.5 | `data/outputs-partitions/batch-1/measurements.csv` | 24 | 64 |
| `pandas-baseline.csv` | [pandas-baseline.md](../pandas-baseline.md) 14.5 | `data/outputs-baseline/batch-1/measurements.csv` | 16 | 48 |
| `caching-experiment.csv` | [caching-experiment.md](../caching-experiment.md) 14.5 | `data/outputs-caching/batch-1/measurements.csv` | 24 | 79 |

Each row is a started run, warm-ups included. The figures summarize only the measured runs: not
warm-ups, ended `ok`, and in a used protocol where the CSV marks one. The peaks per process type
(`peak_rss_<type>_bytes`) follow the rule of their time, under which every process named java
counted as the Spark JVM. Since 2026-10-23 `etf_risk.measure` counts a Java process as the Spark JVM
only if its command line runs Spark, so later records can differ for short helpers such as
`java -version`; these copies stay as they were collected.

**Checks.** `uv run --group plots python -m etf_risk.plots --check --figures X1 X2 X3 X4` compares
the numbers computed from these files with the experiment documents' summary tables. Where the
collectors' outputs exist, which is only on the machine that ran the experiments, it also compares
each copy with its source byte for byte, and otherwise names the sources it could not find.
[figures.json](../figures/figures.json) records each copy's SHA-256.

**Rebuilding the sources.** On the machine that holds the records (protocol JSONs, `run.json` and
`plans.json` files, output tables):

```bash
uv run python analysis/collect_measurements.py
uv run python analysis/collect_partition_measurements.py --batch data/outputs-partitions/batch-1
uv run python analysis/collect_baseline_measurements.py --batch data/outputs-baseline/batch-1
uv run python analysis/collect_caching_measurements.py --batch data/outputs-caching/batch-1
```

The batch collectors write `measurements.csv` and `acceptance.json` into the batch folder itself.
experiments.md 5.6, partition-experiment.md 14.5 and caching-experiment.md 14.5 record that
rebuilding gives byte-identical files; pandas-baseline.md records no such check. The records
themselves come from the formal measurement sessions and cannot be rebuilt elsewhere: new sessions
would give new measurements.

**Updating a copy**, after a new batch for example, is a reviewed change: copy the collector's
output over the file here, then update the experiment document, `DOCUMENTED` in
`src/etf_risk/plots.py` and the figures.
