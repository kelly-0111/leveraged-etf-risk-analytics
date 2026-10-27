# Claude Code message 2

Session: `d50bcd16-34a8-45d0-8956-1e2da5d4b461` · prompt sent 2026-10-23 05:55 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): email ×2, git-user ×349, home ×2749, memory ×27, model-reasoning ×226, user ×88. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-23T10:55:44.846Z

continue

## 2. Assistant — 2026-10-23T10:55:53.925Z

### Tool call: ToolSearch

```
{
  "query": "select:SendMessage",
  "max_results": 1
}
```

## 3. User — 2026-10-23T10:55:54.057Z

### Tool result

````
```
{
  "type": "tool_reference",
  "tool_name": "SendMessage"
}
```
````

## 4. Assistant — 2026-10-23T10:55:57.182Z

### Tool call: SendMessage

```
{
  "to": "a5b1ff52909637d3a",
  "summary": "Resume pipeline exploration and report",
  "message": "Please finish now: you were stopped by a usage limit just before writing your final report. Skip any remaining line-number polishing. Write the complete report answering questions 1–8 from the original task, with file:line citations for what you have already verified. Mark anything you did not verify as \"not checked\". Same privacy rules as before; read nothing more under docs/ai-usage/.",
  "type": "message",
  "recipient": "a5b1ff52909637d3a",
  "recipient_kind": "agent",
  "content": "Please finish now: you were stopped by a usage li…"
}
```

## 5. Assistant — 2026-10-23T10:55:58.398Z

### Tool call: SendMessage

```
{
  "to": "ae6babe7ac18c5222",
  "summary": "Resume docs exploration and report",
  "message": "Please finish now: you were stopped by a usage limit just before writing your final report. Skip the remaining line check. Write the complete report answering questions 1–9 from the original task, with file:line citations for what you have already verified. Mark anything you did not verify as \"not checked\". Same privacy rules as before.",
  "type": "message",
  "recipient": "ae6babe7ac18c5222",
  "recipient_kind": "agent",
  "content": "Please finish now: you were stopped by a usage li…"
}
```

## 6. User — 2026-10-23T10:55:58.921Z

### Tool result

```
{"success":true,"message":"Resuming agent a5b1ff5","resumedAgentId":"a5b1ff52909637d3a","pin":{"id":"a5b1ff52909637d3a","name":"a5b1ff52909637d3a","ref":"851b23"}}
```

## 7. User — 2026-10-23T10:55:59.078Z

### Tool result

```
{"success":true,"message":"Resuming agent ae6babe","resumedAgentId":"ae6babe7ac18c5222","pin":{"id":"ae6babe7ac18c5222","name":"ae6babe7ac18c5222","ref":"facaa1"}}
```

## 8. Assistant — 2026-10-23T10:56:31.219Z

While those two reports come in, I'll fold the jobs-package findings into milestone 1's audit list.

## 9. Assistant — 2026-10-23T10:56:36.603Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "   - the merged worktrees `.claude/worktrees/job-queue` and `job-table` are clean and their\n     branches are in `main`: remove them, with the author's OK;\n   - (to fill from the exploration: CLIs, stale status text, test gaps)",
  "new_string": "   - the merged worktrees `.claude/worktrees/job-queue` and `job-table` are clean and their\n     branches are in `main`: remove them, with the author's OK;\n   - the jobs package has no entry point (no `__main__`, argparse or `[project.scripts]`):\n     the \"submit CLI\" of the spec §11 diagram does not exist, and nothing configures logging\n     (the reconciler's per-pass INFO line is never shown);\n   - nothing is timed: `Pass` and `Served` hold counts only; no `requeued_at` or status\n     history; `published_at` is cleared by the claim; a crash before the claim leaves no trace;\n   - Kafka's `session.timeout.ms` and `max.poll.interval.ms` are library defaults (45 s, 300 s),\n     unpinned by any test, while `serve()` runs the pipeline inside its poll loop;\n   - the 22 mutation checks of the job docs exist only as prose (no script, not reproducible);\n   - doc drift: `job-table.md` claim SQL omits `published_at = NULL` (store.py:334) and\n     \"apart from submit\" omits `mark_published`; `job-queue.md:90` names a test that does not\n     exercise the lost confirmation of the job-9 timeline;\n   - the test helper `WorkerEnv.check` (tests/jobs_backends.py:200) ties result checks to the\n     simulated pipeline's `result.json`;\n   - (to fill from the remaining exploration: pipeline CLIs, stale status text)"
}
```

## 10. User — 2026-10-23T10:56:37.766Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 11. Assistant — 2026-10-23T10:56:42.704Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/docs/spec.md",
  "offset": 118,
  "limit": 116
}
```

## 12. User — 2026-10-23T10:56:42.807Z

### Tool result

````
118	## 4. Data inputs and outputs
119	
120	### Implemented
121	
122	| Artifact | Location (gitignored unless marked) | Produced by | Contents |
123	|---|---|---|---|
124	| Raw snapshot | `data/raw/yahoo/<snapshot>/` | `download.py` | one CSV per ticker (Date, Open, High, Low, Close, Adj Close, Volume, Dividends, Stock Splits; QQQ also has Capital Gains, all zero in `full-2026-10-12` and unused) and `manifest.json` (download time, tool versions, request settings, rows, dates, SHA-256 per file); the prototype snapshot sits in `data/raw/yahoo/` with `verification.json` |
125	| Daily returns | `data/processed/<snapshot>/daily_returns/<TICKER>.parquet` | `ingest.py` | `ticker` string, `date` date32, `adjusted_price` double, `daily_return` double (null on the first row); schema metadata naming the source, snapshot and checksums |
126	| Quality report | `data/processed/<snapshot>/quality_report.json` | `ingest.py` | per-ticker check results, a verification-status block, and the list of unverified extreme days |
127	| Window definitions | `data/windows/<snapshot>/<name>/` (`windows.parquet`, `config.json`) | `windows.py` | one row per window: `window_kind, ticker, window_days, entry_date, first_return_date, exit_date, entry_row, stride, calendar_year, contains_unverified_day, unverified_day_count, entry_on_unverified_day`; the config records the SHA-256 of every return file, of `quality_report.json` and of `windows.parquet`, the self-check results, the flag rule, each return file's raw-manifest hash, and the code that built it (commit, whether the worktree was clean, SHA-256 of every source file and of `uv.lock`) |
128	| Run output | `data/outputs/windows/<snapshot>/<name>/<run id>/` | `spark_pipeline.py`, `verify.py` | `window_stats/` (one row per window, no model), `path_days/` (per window, leverage and day; partitioned by ticker), `path_summary/` (per window and leverage), `paired/` (per window, 1x and 2x; for a breached 2x path the full-window 2x drawdown and turnover columns are null and the partial values sit in `*_pre_breach` columns with `days_ok_2x`), `checks.json`, `run.json` (including the code provenance and the JVM's measured maximum heap), and `verify.json` from the sample check |
129	| Measurement records | `data/outputs/windows/<snapshot>/<name>/protocol-<UTC time>.json`, `<run id>.log` (the stride experiment: under `data/outputs-experiments/`) | `measure.py` | per run: wall time, in-process phase timings, peak summed RSS in total and per process type, stop-rule status and its limits; since 2026-10-23 also the process types' rule (`process_kinds`), under which a Java process is `spark_jvm` only if its command line runs Spark |
130	| Measurements CSV | `data/outputs-experiments/measurements.csv` | `analysis/collect_measurements.py` | one row per started run of the stride experiment: identity and role, input size, Spark settings, summed stage task counts, wall and phase times, peak RSS by process type, sampling, code ([experiments.md](experiments.md) 5.6) |
131	| Execution plans | `plans.json` in a run folder | `spark_pipeline.py --record-plans` (`plans.py`) | for every SQL execution of the run: its phase and final plan text, each shuffle exchange's requested and runtime partition counts, each AQE shuffle read's mark and partition count ([partition-experiment.md](partition-experiment.md) 4.2); in format 2, also each execution's description and scan nodes ([caching-experiment.md](caching-experiment.md) 4.2) |
132	| Shuffle-partition batch | `data/outputs-partitions/<batch>/` | `measure.py` through `docs/partition-session.zsh`; `analysis/collect_partition_measurements.py` | protocols and runs of configurations A, B and C, `positions.tsv`, `run-log.txt`, and the collector's `measurements.csv` and `acceptance.json` ([partition-experiment.md](partition-experiment.md) 2.4, 4.3) |
133	| Pandas-baseline batch | `data/outputs-baseline/<batch>/` | `measure.py --pipeline` through `docs/baseline-session.zsh`; `analysis/collect_baseline_measurements.py` | protocols and runs of S (the Spark pipeline) and P (the pandas pipeline), `positions.tsv`, `run-log.txt`, and the collector's `measurements.csv` and `acceptance.json` ([pandas-baseline.md](pandas-baseline.md) 2.4, 4.3) |
134	| Caching batch | `data/outputs-caching/<batch>/` | `measure.py` through `docs/caching-session.zsh`; `analysis/collect_caching_measurements.py` | protocols and runs of configurations A, B and C (`spark_pipeline --cache`), `positions.tsv`, `run-log.txt`, and the collector's `measurements.csv` and `acceptance.json` ([caching-experiment.md](caching-experiment.md) 2.4, 4.3) |
135	| Figures | `docs/figures/` (committed) | `plots.py` | twelve PNGs (M1–M5, S1, D1–D2, X1–X4) and `figures.json`: each input's path and SHA-256, and each figure's checked numbers ([results.md](results.md) 8) |
136	| Measurement CSV copies | `docs/measurements/` (committed) | copied from the four collectors' outputs | reviewed copies of the experiments' measurements CSVs, which X1–X4 read ([measurements/README.md](measurements/README.md)) |
137	
138	Snapshots: `full-2026-10-12` (five tickers, each from its first trading day to
139	2025-12-31; used for the main analysis) and the 2020–2025 snapshot of the four
140	stocks (prototype only). Settings, checksums and limitations are recorded in
141	[data-sources.md](data-sources.md).
142	
143	**Data status: partially checked, not fully verified.** Trading dates match the
144	NYSE schedule from pandas_market_calendars; Adj Close is consistent with Yahoo's
145	own dividend records; none of the 23 split-day returns resembles an unadjusted
146	split, which does not prove that every split adjustment is correct. No second
147	source has been compared, the terms of use have not been reviewed, and **36
148	extreme days are unverified**, including AAPL 2000-09-29 (−51.9%).
149	
150	### Planned
151	
152	None: the figures, planned here until Stage 4, are listed above. They are
153	generated from the result files and never edited by hand.
154	
155	## 5. Module hierarchy and data flow
156	
157	```text
158	src/etf_risk/
159	  download.py        implemented  Yahoo Finance -> raw snapshot + manifest (network; "download" dependency group)
160	  ingest.py          implemented  raw snapshot -> validated daily returns (Parquet) + quality report
161	  validate.py        implemented  data checks used by ingest (pure functions)
162	  model.py           implemented  sequential reference model for one path
163	  windows.py         implemented  window definitions and their checksums; verify_checksums() for later steps
164	  spark_pipeline.py  implemented  window members, model per window, Spark summaries, 1x/2x pairing, full-scale checks,
165	                                  optional caches (--cache)
166	  verify.py          implemented  sample check against an independent Python slicing of each window
167	  measure.py         implemented  fresh-process timed runs, process-tree memory sampling, stop rule
168	  provenance.py      implemented  code state for every record (commit, worktree state, SHA-256 of sources and uv.lock); repo-relative paths
169	  plans.py           implemented  a run's final execution plans, AQE partition counts, descriptions and scan nodes
170	                                  (spark_pipeline --record-plans)
171	  pandas_pipeline.py implemented  the pipeline's results in one process with pandas, without Spark (the pandas baseline)
172	  plots.py           implemented  the twelve figures from result files, checked against the documented values (Stage 4)
173	  jobs/              implemented  optional job queue (§11): job table schema (MySQL, SQLite mirror), guarded state
174	                                  transitions (store.py), MySQL and Kafka adapters, worker and its consume loop,
175	                                  reconciler, simulated pipeline and in-memory queue
176	analysis/            implemented  three Spark SQL analyses of a run's paired table (project author):
177	                                  sql_overview.py, sql_comparison.py, sql_sensitivity.py;
178	                                  collect_measurements.py (with Claude Code): the stride experiment's measurements CSV;
179	                                  collect_partition_measurements.py (Claude Code): a shuffle-partition batch's CSV and criteria;
180	                                  collect_baseline_measurements.py (Claude Code): a pandas-baseline batch's CSV and criteria;
181	                                  collect_caching_measurements.py (Claude Code): a caching batch's CSV and criteria
182	tests/               implemented  model, validation, ingest, download, windows, Spark consistency and failure
183	                                  injection, sample check, measurement, provenance, AI-log tooling, partition
184	                                  flags, plan recording, the partition collector and session helpers, the pandas
185	                                  pipeline against the Spark pipeline, the baseline collector and session helpers,
186	                                  the caching option, the caching collector and session helpers, the job table,
187	                                  worker, queue and reconciler (on SQLite; on MySQL and Kafka when configured)
188	.claude/hooks/       implemented  per-message AI-usage logs with redaction (project tooling, not analysis)
189	Dockerfile, docker/  implemented  pipeline image and its build and run scripts (data mounted, never copied in);
190	                                  compose.yaml with the extension's services (MySQL and Kafka so far)
191	```
192	
193	```mermaid
194	flowchart TD
195	    Y[Yahoo Finance] -->|download.py| R[Raw snapshot<br/>CSV + manifest]
196	    R -->|ingest.py + validate.py| P[Daily returns Parquet<br/>+ quality report]
197	    P -->|windows.py| W[Window definitions<br/>+ config with SHA-256]
198	    W -->|checksums verified first| S[spark_pipeline.py]
199	    P --> S
200	    M[model.py<br/>reference model] --> S
201	    S --> O[window_stats, path_days,<br/>path_summary, paired, checks]
202	    O --> V[verify.py<br/>independent sample check]
203	    M --> V
204	    S -.->|started by| B[measure.py<br/>runtime and peak memory]
205	    B --> E[stride experiment<br/>measurements CSV]
206	    B --> E2[shuffle-partition experiment<br/>batch CSV and criteria]
207	    B --> E3[pandas baseline<br/>batch CSV and criteria]
208	    B --> E4[caching experiment<br/>batch CSV and criteria]
209	    O --> F[plots.py<br/>twelve figures]
210	    P --> F
211	    W --> F
212	    E --> F
213	    E2 --> F
214	    E3 --> F
215	    E4 --> F
216	```
217	
218	Every box is implemented.
219	`measure.py` starts each timed `spark_pipeline.py` run as a fresh process.
220	
221	Inside `spark_pipeline.py`: every SHA-256 in the window config is verified
222	before Spark starts. Each definition is exploded into its member rows
223	(`entry_row + 1 … entry_row + window_days`) and joined to a broadcast of the
224	returns (about 39k rows). `groupBy(window key).applyInPandas` sorts each window
225	by date, raises if it does not have exactly `window_days` rows with unique
226	dates, and runs `model.simulate_path` for every leverage on the same returns,
227	so 1x and 2x always share their input. Path summaries are computed with Spark
228	aggregations rather than by calling `summarize_path`, so comparing the two
229	(`verify.py`) is a real check; 1x and 2x are paired by conditional aggregation
230	on the window key. Each table is written and read back, so the model runs once
231	per window.
232	
233	## 6. Validation approach
````

## 13. Assistant — 2026-10-23T10:56:48.833Z

### Tool call: Bash

```
{
  "command": "grep -n -E \"add_argument|def main|__name__|sys.exit|raise SystemExit\" src/etf_risk/windows.py src/etf_risk/spark_pipeline.py src/etf_risk/verify.py | head -60",
  "description": "List the pipeline CLIs' arguments and exits"
}
```

## 14. User — 2026-10-23T10:56:49.271Z

### Tool result

```
src/etf_risk/windows.py:329:def main(argv: list[str] | None = None) -> int:
src/etf_risk/windows.py:331:    parser.add_argument("--snapshot", required=True, help="folder name under --processed-root")
src/etf_risk/windows.py:332:    parser.add_argument("--processed-root", type=Path, default=Path("data/processed"))
src/etf_risk/windows.py:333:    parser.add_argument("--kind", choices=list(KIND_NAMES), required=True)
src/etf_risk/windows.py:334:    parser.add_argument("--window-days", type=int, default=ROLLING_WINDOW_DAYS)
src/etf_risk/windows.py:335:    parser.add_argument("--stride", type=int, default=MIN_STRIDE)
src/etf_risk/windows.py:336:    parser.add_argument("--anchor", default=DEFAULT_ANCHOR)
src/etf_risk/windows.py:337:    parser.add_argument("--allow-dense-stride", action="store_true",
src/etf_risk/windows.py:339:    parser.add_argument("--out-root", type=Path, default=Path("data/windows"))
src/etf_risk/windows.py:340:    parser.add_argument("--name", help="output folder name (default: rolling-<days>-s<stride>, calendar-year or full-period)")
src/etf_risk/windows.py:341:    parser.add_argument("--overwrite", action="store_true")
src/etf_risk/windows.py:358:if __name__ == "__main__":
src/etf_risk/windows.py:359:    sys.exit(main())
src/etf_risk/spark_pipeline.py:668:    parser.add_argument("--windows", type=Path, required=True, help="window-definition folder from etf_risk.windows")
src/etf_risk/spark_pipeline.py:669:    parser.add_argument("--out-root", type=Path, default=Path("data/outputs/windows"))
src/etf_risk/spark_pipeline.py:670:    parser.add_argument("--run-id", default=None, help="default: run-<UTC time>")
src/etf_risk/spark_pipeline.py:671:    parser.add_argument("--initial-nav", type=float, default=INITIAL_NAV)
src/etf_risk/spark_pipeline.py:672:    parser.add_argument("--master", default="local[*]")
src/etf_risk/spark_pipeline.py:673:    parser.add_argument("--shuffle-partitions", type=positive_int, default=None,
src/etf_risk/spark_pipeline.py:675:    parser.add_argument("--coalesce", choices=["on", "off"], default=None,
src/etf_risk/spark_pipeline.py:677:    parser.add_argument("--record-plans", action="store_true",
src/etf_risk/spark_pipeline.py:680:    parser.add_argument("--cache", choices=CACHE_MODES, default=None,
src/etf_risk/spark_pipeline.py:709:def main(argv: list[str] | None = None) -> int:
src/etf_risk/spark_pipeline.py:800:if __name__ == "__main__":
src/etf_risk/spark_pipeline.py:801:    sys.exit(main())
src/etf_risk/verify.py:177:def main(argv: list[str] | None = None) -> int:
src/etf_risk/verify.py:179:    parser.add_argument("--run", type=Path, required=True, help="run folder written by etf_risk.spark_pipeline")
src/etf_risk/verify.py:180:    parser.add_argument("--sample-ticker", default="AAPL")
src/etf_risk/verify.py:231:if __name__ == "__main__":
src/etf_risk/verify.py:232:    sys.exit(main())
```

## 15. Assistant — 2026-10-23T10:57:12.747Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "(to fill: M2–M6)",
  "new_string": "### M2 — The worker runs the real pipeline: heartbeats, fencing, timeouts, cleanup\nBranch `feature/worker-pipeline` · Author: Claude Code (spec §11) · Depends on M1.\n\nDesign (all new code in `src/etf_risk/jobs/`; the store's SQL and guards stay as they are):\n- **Job parameters.** A validated parameter set replaces free-form `params`: snapshot, window\n  kind, window days, stride, anchor, sample ticker (draft; fixed after the pipeline report).\n  `submit` computes `input_checksums` from the snapshot's return files and quality report, the\n  same files `windows.py` records in `config.json`. The worker checks them before step 1; a\n  mismatch fails the attempt as not retryable.\n- **`pipeline.py`, `SubprocessPipeline`** (implements `worker.Pipeline`). Runs the three CLIs\n  in order, each as `sys.executable -m …` with every output inside the attempt folder:\n  `windows --out-root <run_dir>/windows`, `spark_pipeline --windows … --out-root\n  <run_dir>/output --run-id <run id>`, `verify --run …`. Each step's working directory, `TMPDIR`\n  and `SPARK_LOCAL_DIRS` point to `<run_dir>/.work`, so nothing lands in the shared `data/`\n  folders or `/tmp`; stdout and stderr go to `<run_dir>/logs/<step>.log`. The run counts as a\n  result only if every step exits 0, `checks.json` reports every check passed, `verify.json`\n  reports no mismatch, and `run.json` exists. Then `.work` is removed and the worker accepts.\n- **Heartbeats.** The worker thread waits on the child with `wait(timeout=…)` and calls\n  `heartbeat()` every `lease / 4` (15 s with the 60 s default). There is no background thread, so\n  the DB connection is used from one thread only. If a renewal raises (database unreachable),\n  the worker retries at the next tick. Once the time since its last successful renewal\n  reaches the lease minus a margin, it fences itself: it kills the run and raises `Fenced`.\n  It assumes the lease is lost rather than risk two Spark runs on one machine.\n- **Fencing.** `heartbeat()` false → terminate the step's process group (SIGTERM, grace,\n  SIGKILL), raise `Fenced`; the folder stays and is never referenced. Token guards are unchanged.\n- **Timeouts.** A wall-clock limit per step and per attempt, set from measured durations with a\n  wide margin. Exceeding it kills the process group → `PipelineError(retryable=True)`, so the\n  job is retried until `max_attempts`. Kafka `max.poll.interval.ms` and `session.timeout.ms` are\n  set explicitly in `kafka.py`, with the poll interval above the attempt limit, and pinned by a test.\n- **Cleanup.**\n  - Children start in their own process group, behind a small launcher with a \"lifeline\"\n    pipe: if the worker dies, even by SIGKILL, the launcher sees EOF and kills its group. This\n    is needed because macOS has no parent-death signal.\n  - At startup, a worker kills the process groups recorded in `.work/pgid` of unfinished\n    attempts left by an earlier worker on the same output root.\n  - `jobs cleanup` lists, and with `--delete` removes, the folders of attempts whose outcome is\n    failed or expired and that ended longer than a grace period ago. Folders with no attempt row\n    are reported but never deleted, and neither are accepted or running attempts. Dry run by default.\n- **Graceful stop.** SIGTERM/SIGINT ends polling, kills a running step, and calls\n  `fail_attempt(retryable=True)`, so the job is requeued at once instead of after its lease.\n- **Event log.** Each process (worker, reconciler, submit) appends JSON lines with UTC times,\n  one flushed line per event: delivered, claimed, renewed, renewal failed, step started or\n  ended, fenced, accepted, failed, requeued, published. E2's times come from these logs and the\n  tables. No new table is needed, and the store's transactions are unchanged.\n- **CLI** `python -m etf_risk.jobs <command>`:\n  - `init-db`: schema;\n  - `create-topic`: wraps `kafka.create_topic`;\n  - `submit`, `worker`, `reconciler`, `cleanup`;\n  - `status [--check]`: prints the job and attempt tables and `invariant_violations()`, and\n    exits 1 on any violation.\n\n  Settings come from flags or `ETF_RISK_MYSQL_URL` / `ETF_RISK_KAFKA_BOOTSTRAP`, and logging is\n  configured.\n- **Defense in depth for the guarantee** (optional, small): a unique index on accepted attempts\n  per job. SQLite: a partial unique index. MySQL: a unique index on a generated column that is\n  `job_id` only when `outcome = 'accepted'`. A test shows that a second accepted row is refused.\n- **Attempt record.** `<run_dir>/attempt.json` holds the worker id, run id, steps with exit\n  codes and times, input checksums as checked, and `code_state()` (now covering `jobs/`).\n\n(to fill: M2 deliverables/acceptance/tests after the pipeline report; M3–M6)"
}
```

## 16. User — 2026-10-23T10:57:13.895Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 17. Assistant — 2026-10-23T10:58:28.403Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "(to fill: M2 deliverables/acceptance/tests after the pipeline report; M3–M6)",
  "new_string": "(to fill: M2 deliverables/acceptance/tests after the pipeline report)\n\n### M3 — Recovery experiments E1 and E2\nBranch `feature/recovery-experiment` · Tooling: Claude Code · Experiment: the project author\n(design, predictions, formal session, answers), with tutoring · Depends on M2.\n\n- **Tooling (Claude, first commit):**\n  - crash injection at the worker's existing fault points (`Worker(fault=…)`, worker.py:112),\n    selected by an environment variable and implemented as a real SIGKILL of the process;\n  - external injections: SIGKILL of the worker while a step runs; SIGSTOP/SIGCONT for a stalled\n    worker; `docker compose restart kafka` or `mysql` at a chosen phase;\n  - a harness log of injections and readiness times;\n  - zsh session helpers in the style of `docs/caching-session.zsh`;\n  - a run-content comparison against a reference run (reusing existing comparison code if the\n    pipeline report finds it);\n  - the collector `analysis/collect_recovery_measurements.py`. It merges the tables, the event\n    logs and the harness log into `docs/measurements/recovery-experiment.csv` and\n    `acceptance.json`, and refuses inconsistent inputs;\n  - figure X5 in `plots.py` with its `figures.json` checks.\n- **Author's document `docs/recovery-experiment.md`** (scaffolded headings only):\n  - Part A: the cases (draft list below); repetitions; lease, heartbeat and reconcile\n    settings; the workload; metric definitions; predictions; acceptance criteria; stop rules\n    (memory, time); the batch rule (fresh MySQL container per batch).\n  - Part B: results, answers to E1 and E2, \"not claimed\".\n  - Draft cases, decided in Part A:\n    - worker crash before the claim, after the claim but before the acknowledgement, during a\n      step, after the pipeline but before acceptance, and after acceptance;\n    - a stalled worker taken over by a standby, then fenced on resume;\n    - Kafka restart while idle, during a submit, and during a run;\n    - MySQL restart during a run, shorter and longer than the lease;\n    - MySQL restart at acceptance (the failed-COMMIT path).\n- **Metrics per job:**\n  - from the harness log: injection time;\n  - from the expired attempt's `ended_at`, or the reconciler/redelivery event: detection time;\n  - from the next `claimed_at`: recovery;\n  - from `finished_at`: completion;\n  - executions (attempt rows and deliveries);\n  - accepted results (0 or 1);\n  - correctness: all checks passed, and content equals the reference;\n  - lost: not terminal by the deadline.\n- **E1 cross-check.** The author writes their own SQL for accepted results per job. It must agree\n  with `invariant_violations()`: two independent implementations of the same guarantee.\n- Acceptance: one batch meeting every Part A criterion. Across all batches: zero lost jobs,\n  zero jobs with more than one accepted result, and exactly one correct accepted result for\n  every succeeded job. MySQL and Kafka peaks recorded for each batch. Session on a merged, clean\n  commit. Tests: collector and helper tests in the style of `tests/test_caching_collector.py`\n  and `tests/test_caching_session.py`, plus injection-tool tests.\n\n### M4 — Redis cache for summary queries, with fallback\nBranch `feature/result-cache` · Infrastructure: Claude Code · Cache logic: the project author,\nwith tutoring · Depends on M1 (not on M2/M3: it can use the run of record).\n\n- **Claude:**\n  - a Compose service `redis`: pinned by digest, `--maxmemory 32mb --maxmemory-policy\n    allkeys-lru`, persistence off, `mem_limit`/`memswap_limit` 128m, `127.0.0.1` only, with a\n    healthcheck;\n  - a `cache` dependency group with an exact `redis` pin;\n  - `src/etf_risk/summary.py`: named, parameterized summary queries over a run's `paired/`,\n    built on the author's `analysis/sql_*.py`, with the author's consent for any refactor. It\n    has a one-shot CLI (new process) and a warm mode: one SparkSession answering requests as\n    JSON lines on stdin and stdout;\n  - an accepted-run resolver (`--job N` → the accepted attempt's folder; never a\n    non-accepted one);\n  - contract tests and fakes: an in-memory Redis stand-in that can be \"down\", a live fixture\n    gated by `ETF_RISK_REDIS_URL`, and tests for fallback and equal results.\n- **Author** (`src/etf_risk/cache.py`, scaffolded with signatures and TODOs):\n  - the key (run id + normalized query, plus a format version);\n  - serialization;\n  - cache-aside get-or-compute;\n  - the fallback policy (connect and read timeouts, a short circuit breaker, no write-back\n    while down, decode errors treated as misses);\n  - hit, miss and fallback counters.\n- Acceptance: contract tests pass offline and live; with Redis stopped, every query still\n  returns the same result as Spark, and its extra latency is bounded by the timeout or breaker;\n  Redis peak within 128 MiB; the runbook's E3 commands work as written. The guarantee is\n  untouched: the cache never reads a non-accepted run and never writes the job table.\n\n### M5 — E3: new Spark process vs warm Spark session vs Redis\nBranch `feature/result-cache-experiment` · Tooling: Claude Code · Experiment: the project\nauthor, with tutoring · Depends on M4.\n\n- **Configurations** (decided in Part A):\n  - N: a new process per query;\n  - W: a warm session, cache off;\n  - R: a warm session with Redis, at hit rates set by the workload's repeats (e.g. 0, 50 and 90%);\n  - F: Redis stopped, testing fallback latency and correctness, and recovery after Redis\n    returns.\n- **Measures:**\n  - per-query latency, client-side with a monotonic clock: medians and spread;\n  - realized vs designed hit rate;\n  - memory: the warm session's process tree (`measure.py` sampler) and Redis `memory.peak`\n    and `used_memory_peak`.\n- **Deliverables:**\n  - `docs/result-cache-experiment.md` (Parts A and B, authorship line);\n  - the collector `analysis/collect_result_cache_measurements.py` (the name avoids the\n    existing caching collector);\n  - `docs/measurements/result-cache-experiment.csv`;\n  - figure X6.\n- Acceptance as in earlier experiments: one batch meets every criterion, with no drift beyond\n  the stated tolerance.\n\n### M6 — Architecture, report and demo\nBranch `docs/extension-report` · Author: Claude Code drafts, the project author approves the\nconclusions (as for `results.md` §7) · Depends on M3 and M5.\n\n- `docs/architecture.md` (new): the batch pipeline and the extension; native vs Compose\n  deployment; failure model and guarantee; the memory budget ledger; the runbook. Spec §5's\n  mermaid node ids `E2`/`E3` (the partition and baseline experiments) are renamed so they no\n  longer read as §11's E2/E3.\n- spec §8 sections \"What the recovery experiments showed\" and \"What the result-cache experiment\n  showed\"; §9 and §11 statuses; README status and runbook; `results.md` with X5–X6;\n  `demo.md` (submit, kill the worker mid-run, watch recovery and `status --check`; cache miss →\n  hit → Redis stopped → fallback → restart); `measurements/README.md`.\n- Acceptance: every number traceable to a committed CSV or record (`figures.json` checks);\n  every demo and runbook command run as written on a fresh worktree; links valid; the author\n  approves the conclusions."
}
```

## 18. User — 2026-10-23T10:58:29.559Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 19. Assistant — 2026-10-23T10:58:34.817Z

### Tool call: Bash

```
{
  "command": "wc -l analysis/sql_*.py && sed -n '1,40p' analysis/sql_overview.py",
  "description": "Show the size of the SQL analyses and one header"
}
```

## 20. User — 2026-10-23T10:58:35.349Z

### Tool result

```
      71 analysis/sql_comparison.py
      61 analysis/sql_overview.py
      62 analysis/sql_sensitivity.py
     194 total
"""SQL analysis 1: a per-ticker overview of a run's paired table.

For each ticker: the number of windows, of 2x breaches and of windows that use an
unverified extreme day, and exact medians of the 1x and 2x returns (a breached window
has no 2x return). Also prints the table's schema, a few rows and the query's plan.

    uv run python analysis/sql_overview.py <run folder>

The run folder is one written by etf_risk.spark_pipeline (its paired/ table is read);
the paired/ folder itself also works.

The query was written by the project author; the command-line input was added with
Claude Code (Opus 5.5).
"""
import argparse
from pathlib import Path

from etf_risk.spark_pipeline import build_spark

parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("run", type=Path, help="run folder from etf_risk.spark_pipeline, or its paired/ folder")
args = parser.parse_args()
paired_dir = args.run / "paired" if (args.run / "paired").is_dir() else args.run
if not any(paired_dir.glob("*.parquet")):
    parser.error(f"no paired table (Parquet files) in {paired_dir}")

spark = build_spark()

try:
    paired = spark.read.parquet(str(paired_dir))

    paired.printSchema()
    paired.select(
        "ticker",
        "breached_2x",
        "contains_unverified_day",
        "return_1x",
        "return_2x",
    ).show(5)
```

## 21. Assistant — 2026-10-23T10:58:41.698Z

### Tool call: Bash

```
{
  "command": "sed -n '40,61p' analysis/sql_overview.py && echo \"--- build_spark:\" && grep -n -A25 \"^def build_spark\" src/etf_risk/spark_pipeline.py | head -40",
  "description": "Show the overview query and how Spark is built"
}
```

## 22. User — 2026-10-23T10:58:42.011Z

### Tool result

```
    paired.createOrReplaceTempView("paired")

    result = spark.sql("""
        SELECT
            ticker,
            COUNT(*) AS n_windows,
            COUNT(return_2x) AS n_return_2x,
            SUM(CASE WHEN breached_2x THEN 1 ELSE 0 END) AS n_breached_2x,
            SUM(CASE WHEN contains_unverified_day THEN 1 ELSE 0 END) AS n_flagged,
            percentile(return_1x, 0.5) AS median_return_1x,
            percentile(return_2x, 0.5) AS median_return_2x
        FROM paired
        GROUP BY ticker
        ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
    """)

    result.explain("formatted")
    result.show(truncate=False)

finally:
    spark.stop()
--- build_spark:
132:def build_spark(master: str = "local[*]", shuffle_partitions: int | None = None,
133-                coalesce: bool | None = None) -> SparkSession:
134-    """None leaves a setting at Spark's default. On an existing session, getOrCreate() applies these
135-    settings to it, which is why main() refuses the partition flags inside one."""
136-    # Without this, Spark binds to the Wi-Fi interface on macOS.
137-    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
138-    builder = (
139-        SparkSession.builder.master(master)
140-        .appName("etf-risk")
141-        .config("spark.ui.enabled", "false")
142-        .config("spark.sql.session.timeZone", "UTC")
143-    )
144-    if shuffle_partitions is not None:
145-        builder = builder.config("spark.sql.shuffle.partitions", str(shuffle_partitions))
146-    if coalesce is not None:
147-        builder = builder.config("spark.sql.adaptive.coalescePartitions.enabled", "true" if coalesce else "false")
148-    spark = builder.getOrCreate()
149-    spark.sparkContext.setLogLevel("ERROR")
150-    return spark
151-
152-
153-# --- building blocks -------------------------------------------------------------
154-
155-def returns_with_rows(returns: DataFrame) -> DataFrame:
156-    """Add `row` per ticker (0 = first price), the index used by the window definitions."""
157-    return returns.withColumn("row", (F.row_number().over(Window.partitionBy("ticker").orderBy("date")) - 1).cast("int"))
```

## 23. Assistant — 2026-10-23T10:59:15.220Z

### Tool call: Bash

```
{
  "command": "sed -n '709,800p' src/etf_risk/spark_pipeline.py",
  "description": "Show the Spark pipeline's main function"
}
```

## 24. User — 2026-10-23T10:59:15.810Z

### Tool result

```
def main(argv: list[str] | None = None) -> int:
    started = time.perf_counter()
    args = build_parser().parse_args(argv)
    sets_spark = args.shuffle_partitions is not None or args.coalesce is not None
    if sets_spark and SparkSession.getActiveSession() is not None:
        print("--shuffle-partitions and --coalesce need a fresh process: a Spark session already exists here, "
              "and building one would change its settings", file=sys.stderr)
        return 2
    run_id = args.run_id or "run-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    try:
        config, verified = verify_checksums(args.windows)
    except (ChecksumError, FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"checksum verification failed, Spark not started:\n{exc}", file=sys.stderr)
        return 3
    run_dir = run_dir_for(args.windows, args.out_root, run_id)
    if run_dir.exists():
        print(f"{run_dir} exists; use a new --run-id", file=sys.stderr)
        return 2
    run_dir.mkdir(parents=True)
    record = {
        "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "code": code_state(), "windows_dir": str(args.windows),
        "windows_config": config, "verified_sha256": verified, "leverages": list(LEVERAGES),
        "initial_nav": args.initial_nav, "environment": environment(), "status": "running",
    }
    if sets_spark or args.record_plans or args.cache is not None:     # without the flags, run.json is as before
        record["pipeline_options"] = {"shuffle_partitions": args.shuffle_partitions, "coalesce": args.coalesce,
                                      "record_plans": args.record_plans}
        if args.cache is not None:
            record["pipeline_options"]["cache"] = args.cache
    timings: dict[str, float] = {}
    status, code = "failed", 2
    spark = None
    caches = None
    own_session = SparkSession.getActiveSession() is None      # only stop a session started here
    plan_after, plan_start_error = None, None
    try:
        t = time.perf_counter()
        spark = build_spark(args.master, args.shuffle_partitions,
                            None if args.coalesce is None else args.coalesce == "on")
        timings["session_start"] = time.perf_counter() - t
        record["spark"] = spark_settings(spark)
        if args.record_plans:                    # the executions after this id are this run's
            t = time.perf_counter()
            try:
                plan_after = plans.watermark(spark)
            except Exception as exc:
                plan_start_error = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-500:]
            timings["plan_capture"] = time.perf_counter() - t
        defs = spark.read.parquet(str(args.windows / config["windows_file"]))
        return_files = [str(resolve(config["snapshot_dir"]) / rel) for rel in config["inputs_sha256"] if rel.startswith("daily_returns/")]
        returns = spark.read.parquet(*return_files)
        if args.cache is not None:
            caches = RunCaches(spark, args.cache)
        results = compute(spark, defs, returns, LEVERAGES, args.initial_nav, out_dir=run_dir, timings=timings,
                          caches=caches)
        checks = results["checks"]
        (run_dir / "checks.json").write_text(json.dumps(checks, indent=2) + "\n")
        record["checks"] = checks
        record["model_run"] = results["model_run"]
        spark.sparkContext.setJobGroup("bookkeeping", "row counts for run.json")   # not part of any timed phase
        record["row_counts"] = {"windows": defs.count(), "window_stats": results["stats"].count()}
        if results["model_run"]:
            record["row_counts"].update({name: results[name].count() for name in ("path_days", "summary", "paired")})
        record["stage_task_counts"] = stage_task_counts(spark, ["window_stats", "model", "summaries", "checks"])
        status, code = ("ok", 0) if total_violations(checks) == 0 else ("checks_failed", 1)
        if args.record_plans:                    # after the status is set, which it cannot change
            record["plan_capture"] = record_plans(spark, plan_after, plan_start_error, run_dir, timings)
    except Exception as exc:
        record["error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-4000:]
    finally:
        if caches is not None:                   # before spark.stop(), on every path
            try:
                caches.release_all()
            except Exception as exc:
                record["cache_cleanup_error"] = "".join(traceback.format_exception_only(type(exc), exc)).strip()[-2000:]
            record["cache"] = caches.record()
        timings["total_in_process"] = time.perf_counter() - started
        record.update({"status": status, "timings_seconds": timings, "finished_at_utc": datetime.now(timezone.utc).isoformat()})
        (run_dir / "run.json").write_text(json.dumps(record, indent=2, default=str) + "\n")
        if spark is not None and own_session:
            spark.stop()
    print(f"{run_id}: {status}  ({record.get('row_counts', {})})  -> {run_dir}")
    for group, violations in record.get("checks", {}).items():
        bad = {k: v for k, v in violations.items() if v}
        print(f"  {group}: {'ok' if not bad else bad}")
    if "error" in record:
        print("  error:", record["error"].splitlines()[-1], file=sys.stderr)
    return code


if __name__ == "__main__":
```

## 25. Assistant — 2026-10-23T11:02:57.282Z

### Tool call: Write

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "content": "# Plan: finishing the systems extension (spec §11) in six reviewed milestones\n\nStatus: draft for the author's review. Nothing is implemented until it is approved.\n\n## Context\n\nStages 1–4 are merged into `main` (f058095), and so is the extension's job queue: PR #7 (the job\ntable and fencing), PR #8 (Kafka delivery and the reconciler) and PR #9 (Stage 4). What spec\n§11 still lists as planned:\n- the real pipeline in the worker (today it runs `SimulatedPipeline`);\n- the recovery experiments E1/E2;\n- the Redis result cache;\n- the cache experiment E3;\n- their documentation.\n\nThis plan turns the author's six-point outline into milestones M1–M6, one branch and one PR\neach. Each milestone has:\n- deliverables;\n- acceptance criteria;\n- tests;\n- a statement of how it keeps the guarantee.\n\nFour cross-cutting requirements run through all of them:\n- code provenance for `jobs/`;\n- reproducible dependencies;\n- startup commands;\n- measured memory budgets.\n\nData verification, the privacy-hook fixes and AI-log review stay in separate workstreams.\n\nState observed on 2026-10-23:\n- **Main worktree.** It is on `fix/measure-process-kinds` (97c35f3). That branch is pushed but\n  not merged; it carries the fix for the intermittent `measure` test, which `main`'s README,\n  spec and demo still call open.\n- **Uncommitted W2 work.** The worktree holds uncommitted changes to the privacy hook, its tests\n  and one transcript.\n- **AI-log folders.** There are 68 untracked AI-log folders.\n- **`gh` is not installed.**\n\n## Ground rules for every milestone\n\n1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has\n   exactly one, and a job may execute more than once.\n   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it. The existing\n     `INVARIANT_QUERIES` and `JobStore.invariant_violations()` (store.py:127, :481) check it.\n     Together, the first two queries forbid a second accepted attempt for any job.\n   - **Accepting.** Nothing but `JobStore.accept_result` may produce an accepted attempt.\n   - **Cleanup** never touches an accepted attempt's folder.\n   - **The cache** reads accepted runs only and never writes the job table.\n   - **Checking.** `invariant_violations()` must be empty after every test scenario, every\n     worker run and every experiment batch.\n2. **Authorship** (spec §11, \"Stages and authorship\"). Claude Code writes:\n   - the Compose services;\n   - the worker integration;\n   - the CLIs;\n   - the injection and measurement tooling;\n   - their tests.\n\n   The project author writes the cache logic and the experiments (design, predictions,\n   formal sessions, answers), with tutoring. For the author's parts Claude prepares scaffolds\n   (signatures, docstrings, TODOs, contract tests) and reviews, but does not fill them in.\n\n   New files carry an `AI contribution:` line. Experiment documents carry an `Author:` line\n   like `docs/partition-experiment.md:3-5`, reworded for the tutored model.\n3. **Review gates.** Each milestone opens with a findings report; nothing is fixed before the\n   author has read it. Each closes with a stop for review before the PR is merged.\n4. **Git.**\n   - **Isolation.** Each milestone gets its own worktree (`.claude/worktrees/<name>`) from an\n     up-to-date `main`, so the main worktree's W2 changes never enter a milestone branch.\n   - **Staging and merging.** Stage files by explicit path only. Merge with merge commits,\n     never squash or rebase. Every commit ends with the Co-Authored-By trailer.\n   - **AI logs.** Milestone commits contain no AI logs; those go to W3.\n   - **PRs.** Claude pushes the branch; the author opens and merges the PR on GitHub.\n   - **Formal sessions** run on a merged, clean commit whose SHA lands in every record. There\n     are no commits during a session.\n5. **Privacy.** `data/` and the private plan stay out of Git. Memory files,\n   `.git/info/exclude` and app lists are never printed in tool calls. Batch folders live under\n   `data/`.\n6. **Measurement sessions.** While one runs, other sessions only write and review. They wait\n   for an explicit confirmation that it ended, then check that its worktree is unchanged.\n7. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write \"one\n   process\", never \"one core\". Give each experiment a \"not claimed\" list.\n\n## Cross-cutting requirements\n\n**A. Code provenance for `jobs/`.**\n- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob(\"*.py\")` (provenance.py:62),\n  so no record identifies any file in `jobs/`, including `schema/*.sql`. A plain recursive glob\n  would collide on `__init__.py`.\n- **M1 change.** Hash every `*.py` and `*.sql` under `src/etf_risk/` recursively, keyed by\n  package-relative POSIX path. `model.py` keeps its key; new keys look like `jobs/store.py`. Old\n  records stay comparable for the files they cover.\n- **Attempt records (M2 on).** Each attempt writes `attempt.json` with the worker's\n  `code_state()`, and so does every experiment record.\n- **Authorship provenance.** Keep the `AI contribution:` lines. Add an origin table to\n  `job-queue.md`: module → commits (eec1032, e2806bd, cd72957) → PR → tests that verify it.\n\n**B. Reproducible dependencies.**\n- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`\n  (compose.yaml:13; test docstrings) and are not in `uv.lock`.\n- **New groups.** M1 adds a `jobs` group with exactly these pins. M4 adds a `cache` group with\n  an exact `redis` pin.\n- **Lock changes.** Every lock change may only add packages. numpy 2.5.4, pandas 2.3.3,\n  pyspark 4.2.0, pyarrow 26.0.0 and psutil 7.2.2 stay unchanged, checked by a lock diff and\n  `uv lock --check`.\n- **Commands.** Documented commands use `--group …` and `uv sync --frozen`.\n- **Images.** Images are pinned by digest. Redis follows the Kafka rule: the newest release at\n  least two weeks old.\n- **Host tools.** Each formal session records host tool versions. Seen 2026-10-23: uv 0.11.16,\n  Java 17.0.10, Docker 28.3.0, Compose v2.38.1, Docker Desktop VM 3.83 GiB.\n- **Out of scope.** The NumPy pin (spec §9, planned) stays out unless approved.\n\n**C. Startup commands.**\n- **Today.** The README has no `docker compose` commands; they live only in compose.yaml\n  comments and test docstrings.\n- **Runbook.** A runbook section in the README (M1 skeleton, filled in by M2, M4 and M6) gives\n  copy-pasteable commands per configuration:\n  - test services;\n  - the E1/E2 stack: MySQL and Kafka in Compose; `init-db`, `create-topic`, worker, reconciler,\n    submit and `status` on the host;\n  - the E3 stack: Redis, the query CLI, the warm query service;\n  - teardown with `down -v`.\n- **Acceptance.** Every milestone that touches the runbook runs its commands exactly as written\n  in a fresh worktree.\n\n**D. Measured memory budgets.** A ledger in spec §11 records component, limit, measured peak,\nmethod, date and commit. Known so far:\n\n| Component | Budget | Measured | Source |\n|---|---|---|---|\n| MySQL container | 512 MiB | 324–398 MiB per full run on fresh containers; 472 after two runs; 511 after ~2 h | spec §11 |\n| Kafka container | 640 MiB (256 MiB heap) | 354–478 MiB; 516 with mutation checks | spec §11 |\n| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB at stride 21 | spec §11 |\n| Native stride-21 pipeline tree | `measure` stop at 4.8 GiB | 1.27 GiB (run of record) and 2.62–2.73 GiB (stride experiment), summed RSS | spec §8, experiments.md |\n| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |\n| Native worker, reconciler, submit | set in M2 | — (M2) | |\n| Warm query service | set in M4 | — (M4/M5) | |\n\n- **What the numbers imply.** Running the worker natively puts only the MySQL and Kafka limits\n  in the VM (1.15 GiB). But a stride-21 job may need about 2.7 GiB on the host, and earlier\n  sessions required at least 3.0 GiB free before each protocol. Hence the job-size choice in\n  M3 Part A.\n- **Container peaks** come from cgroup `memory.peak`, through a new helper (only\n  `docker/run.sh` reads it today).\n- **Native peaks** come from `measure.TreeSampler`.\n- **Batches.** Each recovery batch starts on a fresh MySQL container and records its own peak.\n- **Exceeded budgets.** A budget that is exceeded stops the session, and budgets change only\n  at review.\n\n## Milestones (numbered as in the outline)\n\nOrder: M1 → M2 → M3 and M1 → M4 → M5, then M6. M4 does not need M2 or M3, because it can use\nthe run of record. Its code can be written while M3's session runs, under ground rule 6.\n\n### M1 — Read the whole project; bring the code up to date\nBranch `feature/extension-baseline` · Author: Claude Code · Prerequisite: the author merges\n`fix/measure-process-kinds` (97c35f3) first, since M2–M5 sample memory with its process kinds.\n\n**Step 1: audit (read-only).** A findings report goes to the author, grouped as below.\n- **Reproducibility and provenance**:\n  - cross-cutting gaps A, B and C;\n  - the 22 mutation checks in the job docs exist only as prose (no script);\n  - the merged worktrees `.claude/worktrees/job-queue` and `job-table` are clean and in `main`,\n    so they can be removed with the author's OK.\n- **Missing operations**:\n  - no entry point in `jobs/`, so the \"submit CLI\" in the §11 diagram does not exist;\n  - logging is never configured;\n  - nothing is timed (`Pass` and `Served` are counts only; no `requeued_at` or history);\n  - `published_at` is cleared by the claim;\n  - a crash before the claim leaves no trace;\n  - Kafka `session.timeout.ms` and `max.poll.interval.ms` are unpinned defaults (45 s, 300 s),\n    while `serve()` runs the pipeline inside its poll loop.\n- **Pipeline CLIs**, which matter for M2:\n  - **Exit 1 is ambiguous.** Exit 1 means \"checks failed\" (spark_pipeline) or \"mismatch\"\n    (verify), but also any uncaught exception. For spark_pipeline that includes exceptions\n    outside its `try`: `mkdir`, building the record, and writing `run.json` in the `finally`.\n  - **Missing records.** `run.json` is written only in the `finally`, so a killed run leaves\n    none.\n  - **verify gaps.** verify's checksum handler misses `JSONDecodeError`, its `spark.stop()` is\n    not in a `finally`, and it never checks the run's status.\n  - **Relative paths.** verify reads `run.json`'s `windows_dir` as stored, so relative paths\n    assume the repository root.\n  - **windows refusal.** windows refuses only when `config.json` exists; README:224 says \"an\n    existing folder\".\n- **Documentation drift**:\n  - `job-table.md`'s claim SQL omits `published_at = NULL` (store.py:334), and its \"apart from\n    `submit`\" sentence omits `mark_published`;\n  - `job-queue.md:90` names tests that start from a confirmed publication, so they do not cover\n    the job-9 timeline;\n  - the status blocks of job-table.md:97-103 and job-queue.md:146-160 predate the merges;\n  - spec §5's diagram omits `jobs/` and Compose yet says \"Every box is implemented\", and its node\n    ids E2–E4 clash with §11's E1–E3;\n  - spec.md has no AI header, although README:321-323 says AI-drafted files do.\n- **Test helpers**: `WorkerEnv.check` (tests/jobs_backends.py:200) is tied to the simulated\n  pipeline's `result.json`.\n\n**Step 2: fixes, after approval.**\n- provenance (A);\n- the `jobs` group, the lock, and `--with` → `--group jobs` everywhere (B);\n- the runbook skeleton (C);\n- the `memory.peak` helper (D);\n- a reproducible mutation-check script (each mutation a patch, applied in a scratch worktree\n  with a timeout);\n- job-doc drift and stale status text; the module origin table;\n- the CLI fixes, if the author agrees:\n  - uncaught exceptions exit 2, matching spark_pipeline's docstring, so exit 1 always means\n    checks failed or a mismatch;\n  - verify catches `JSONDecodeError`;\n  - verify stops Spark in a `finally`.\n\n  These change no result, and they need tests.\n- removal of the merged worktrees, with the author's OK.\n\n**Step 3: revalidation.**\n- the offline suite;\n- the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with `--group jobs`;\n- the mutation script;\n- MySQL and Kafka peaks read through the helper.\n\n**Deliverables.** The findings report; the fixes above.\n\n**Acceptance.**\n- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in\n  `source_sha256` under a unique key, with the top-level keys unchanged.\n- `uv lock --check` passes, and the lock diff only adds the `jobs` group's packages.\n- The live suite passes with the case count of e2806bd (379), or the difference is explained.\n- Every mutation makes a test fail within its timeout.\n- Peaks stay within budget.\n- No file outside the approved scope changes.\n\n**Tests.** New cases in `test_provenance.py`; CLI exit-code tests (Spark-marked where needed);\njob suites on SQLite and live; the mutation script.\n\n**Guarantee.** No change to `store.py`'s SQL. The mutation script re-proves that breaking a guard\nfails a test.\n\n### M2 — The worker runs windows → spark_pipeline → verify\nBranch `feature/worker-pipeline` · Author: Claude Code (spec §11) · Depends on M1.\n\n**Design.** The new code is `jobs/pipeline.py`, `jobs/launcher.py`, `jobs/params.py`,\n`jobs/events.py` and `jobs/__main__.py`, plus small changes to `worker.py` and `kafka.py`. The\nstore's guards stay as they are.\n\n**Job parameters (`params.py`).**\n- **Schema.** A frozen dataclass: snapshot, kind (`rolling` / `calendar-year` / `full-period`),\n  window days, stride, anchor, sample ticker. Unknown keys are refused. Tickers come from the\n  snapshot, and leverages are fixed at 1x and 2x.\n- **Input checksums.** `submit` computes `input_checksums` from the files that `windows.py`\n  records in `inputs_sha256`: `daily_returns/*.parquet` and `quality_report.json`.\n- **Check before running.** The worker re-checks them before step 1. A mismatch fails the attempt\n  as not retryable.\n\n**Steps.** Each step runs as `sys.executable -m etf_risk.<module>` with absolute paths only.\nEverything lands inside the attempt folder:\n1. `windows --out-root <run_dir>/windows --name <name>` writes\n   `<run_dir>/windows/<snapshot>/<name>/`.\n2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>` writes\n   `<run_dir>/output/<snapshot>/<name>/<run id>/`.\n3. `verify --run …` checks that output.\n\nSetup for every step:\n- the working directory, `TMPDIR`, `SPARK_LOCAL_DIRS` and `java.io.tmpdir` all point to\n  `<run_dir>/.work`;\n- logs go to `<run_dir>/logs/<step>.log`.\n\n**Result rule.**\n- **When the worker accepts.** Every step exits 0, `run.json` has status `ok`, every\n  `checks.json` count is 0, `verify.json` has no mismatch and the same breached windows, and\n  every table has `_SUCCESS`.\n- **Then.** `.work` is removed and the worker calls `accept_result`.\n\n**Failure classification.** This is decided from the records, not the exit code alone.\n- **Not retryable:**\n  - a checksum error (exit 3);\n  - `run.json` status `checks_failed`;\n  - a verify mismatch;\n  - a parameter or input-checksum error.\n- **Retryable:**\n  - a signal;\n  - a timeout;\n  - status `failed`;\n  - a missing record.\n\nRetryable failures go back to the queue until `max_attempts` (3).\n\n**Heartbeats.**\n- **Where.** The worker thread waits on the child with `wait(timeout=…)` and calls `heartbeat()`\n  every lease/4 (15 s at the 60 s default). There is no background thread, so the database\n  connection stays on one thread.\n- **Failed renewals.** A renewal that raises (database unreachable) is retried at the next tick.\n  When the time since the last successful renewal reaches the lease minus a margin, the worker\n  fences itself: it kills the run and raises `Fenced`. Two Spark runs on one machine would risk\n  memory, and the token guard still decides acceptance.\n\n**Fencing.** When `heartbeat()` returns false, the worker sends SIGTERM to the step's process\ngroup, waits a grace period, sends SIGKILL, and raises `Fenced`. The folder stays and is never\nreferenced.\n\n**Timeouts.**\n- **Limits.** Each step and the whole attempt get a wall-clock limit. Draft values are 120 s,\n  600 s, 300 s and 900 s, against measured medians of a few seconds, 18–47 s and about 14 s;\n  they are fixed at review from M2's measurements.\n- **On timeout.** The process group is killed and the attempt fails as retryable.\n- **Kafka settings.** `max.poll.interval.ms` (above the attempt limit) and `session.timeout.ms`\n  are set in `kafka.py` and pinned by tests.\n\n**Cleanup.**\n- **Lifeline.** Each step starts in a new process group behind `launcher.py`, which holds a\n  \"lifeline\" pipe from the worker. If the worker dies, even by SIGKILL, the launcher reads EOF\n  and kills its group. macOS has no parent-death signal.\n- **Stale groups.** Each attempt writes its group id to `.work/pgid`. On startup, a worker kills\n  the groups that a previous worker left unfinished.\n- **`jobs cleanup`** is a dry run unless given `--delete`. It removes folders of failed or expired\n  attempts that ended more than a grace period ago. Folders with no attempt row are only\n  reported. It never touches accepted or running attempts.\n\n**Graceful stop.** On SIGTERM or SIGINT the worker stops polling, kills the running step and\ncalls `fail_attempt(retryable=True)`, so the job is requeued at once.\n\n**Event log (`events.py`).** Each process appends JSON lines with UTC times, one flushed line per\nevent:\n- delivered\n- claimed\n- renewed and renewal failed\n- step start and end\n- fenced\n- accepted\n- failed\n- requeued\n- published\n\nE2's timings come from these logs plus the tables, without a new table.\n\n**CLI** `python -m etf_risk.jobs`:\n- `init-db`\n- `create-topic`\n- `submit`\n- `worker`\n- `reconciler`\n- `cleanup`\n- `status [--check]`, which prints the tables and `invariant_violations()` and exits 1 on a\n  violation\n\nFlags or `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP` configure it, and logging is set up.\n\n**Attempt record.** `attempt.json` holds the worker id, run id, steps (exit code, times), the\ninput checksums as checked and `code_state()`.\n\n**Optional defense in depth.** A unique index on accepted attempts per job: a partial index in\nSQLite, and in MySQL a unique index on a generated column that is `job_id` only when the\noutcome is accepted. The schema-drift test is updated, and a test shows that a second accepted\nrow is refused.\n\n**Deliverables.** The modules above; updated `job-queue.md` (real pipeline, settings table,\nknown limits resolved); the runbook's E1/E2 section; budget rows for the worker, reconciler and\nsubmit.\n\n**Acceptance.** Native worker, MySQL and Kafka in Compose, on fresh containers:\n- **Normal runs.** A calendar-year job and a stride-21 job of `full-2026-10-12` each end\n  `succeeded`, with exactly one accepted attempt that passes every check and verify. Their\n  content equals a direct CLI run under the `compare_tables` rules\n  (analysis/collect_partition_measurements.py:286, partition-experiment.md:476-515).\n- **Stalled worker.** After SIGSTOP for longer than the lease, a standby worker takes over. On\n  SIGCONT the stalled worker's process tree is gone within the grace period, it writes nothing\n  more, and the takeover's result is accepted.\n- **Crashed worker.** After SIGKILL during step 2, no Spark process is left once the lifeline\n  grace has passed, and the job is requeued after its lease and succeeds.\n- **Timeout.** An attempt that exceeds its limit is killed and retried.\n- **Temp files.** No new `spark-*` or `blockmgr-*` folder appears in `/tmp` or `$TMPDIR`.\n- **Cleanup dry run.** It lists exactly the failed and expired attempts.\n- **Peaks.** Measured and within budget.\n- **Invariants.** `invariant_violations()` is empty throughout.\n- **Earlier tests.** Every earlier job test still passes on both stores.\n\n**Tests.**\n- **`test_jobs_pipeline.py`** (offline, with fake step scripts): heartbeat cadence; fencing kills\n  the group (checked with psutil); timeouts; failure classification; the lifeline (kill the\n  parent, the grandchild dies); `.work` cleanup; parameter and checksum refusals.\n- **CLI and cleanup tests.**\n- **A Spark-marked end-to-end test:** a tiny job through `Worker` with SQLite and `MemoryQueue`.\n- **A live end-to-end test** gated by the environment variables: real worker and reconciler\n  processes, SIGKILL mid-run, recovery, then `status --check`.\n\n**Guarantee.** Acceptance still goes only through the token guard. Fencing and self-fencing\nonly stop work. Cleanup excludes accepted attempts. The optional index makes a second accepted\nrow impossible at the storage level.\n\n### M3 — Recovery experiments E1 and E2\nBranch `feature/recovery-experiment` · Tooling: Claude Code · Experiment: the project author,\ntutored · Depends on M2.\n\n**Claude's tooling (first commit, with tests).**\n- **Crash injection.** Crashes at the existing worker fault points (`Worker(fault=…)`,\n  worker.py:112), chosen by an environment variable and carried out as a real SIGKILL.\n- **Outside injections.** SIGKILL during a step; SIGSTOP and SIGCONT; `docker compose restart\n  kafka` or `mysql` at a chosen phase.\n- **Harness log.** It records each injection and the time each service was ready again.\n- **Session helpers.** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:\n  two windows, machine checks, `case n`, a watcher, abort and note, and no commits during the\n  session.\n- **Collector.** `analysis/collect_recovery_measurements.py --batch <folder>` imports\n  `compare_tables` unchanged, as later collectors do. It merges the tables, event logs and\n  harness log and writes `measurements.csv` and `acceptance.json` (criteria 1–5 as before, plus\n  \"6 guarantee\"). It exits 1 on any failed criterion.\n- **Batches** live in `data/outputs-recovery/<batch>/`.\n\n**The author's `docs/recovery-experiment.md`.** Claude scaffolds the headings of Parts A and B\n(sections 1–15 and History) and the `Author:` line.\n- **Part A, decided by the author:**\n  - the cases;\n  - repetitions;\n  - lease, heartbeat and reconcile settings;\n  - the job size (calendar-year vs stride 21, with the memory implications in D);\n  - metric definitions;\n  - predictions;\n  - acceptance criteria;\n  - stop rules;\n  - one fresh MySQL container per batch.\n- **Draft cases offered:**\n  - worker crash before the claim;\n  - crash after the claim but before the acknowledgement (the job-9 timeline);\n  - crash during step 2;\n  - crash after the pipeline but before acceptance;\n  - crash after acceptance;\n  - a stalled worker taken over, then fenced;\n  - Kafka restart while idle, during a submit, and during a run;\n  - MySQL restart during a run, shorter and longer than the lease;\n  - MySQL restart at acceptance (the failed-COMMIT path).\n- **Metrics per job:**\n  - injection time;\n  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;\n  - recovery: the next `claimed_at`;\n  - completion: `finished_at`;\n  - executions;\n  - accepted results (0 or 1);\n  - correctness: every check passed, and the content equals the reference;\n  - lost: not terminal by the deadline.\n- **E1 cross-check.** The author writes their own SQL for accepted results per job, which must\n  agree with `invariant_violations()`.\n\n**Acceptance.**\n- One batch meets every Part A criterion.\n- Across all batches: zero lost jobs and zero jobs with two accepted results; every succeeded\n  job has exactly one correct accepted result.\n- Peaks are recorded per batch.\n- The commit sequence follows the precedent: tooling, Part A (before any measured run), dry\n  batches and the formal session, Part B, status.\n\n**Tests.** Collector and helper tests in the style of `test_caching_collector.py` and\n`test_caching_session.py`, including planted problems that each fail their criterion; tests of\nthe injection tools.\n\n**Guarantee.** This milestone measures it under failures and adds no write path.\n\n### M4 — Redis cache for summary queries, with fallback\nBranch `feature/result-cache` · Infrastructure: Claude Code · Cache logic: the project author,\ntutored · Depends on M1.\n\n**Claude's part.**\n- **Compose service `redis`:**\n  - pinned by digest;\n  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, with persistence off;\n  - `mem_limit` and `memswap_limit` 128m;\n  - port `127.0.0.1:6380`;\n  - a `redis-cli ping` healthcheck.\n- **Dependencies.** A `cache` group with an exact `redis` pin.\n- **`src/etf_risk/summary.py`.**\n  - Named queries over a run's `paired/`. Their SQL comes from the author's `analysis/sql_*.py`\n    without editing those scripts, since documents cite earlier scripts by hash. The author moves\n    their own SQL text in; Claude wires it up.\n  - A one-shot CLI, which is the new-process mode.\n  - A warm mode: one SparkSession answering JSON-lines requests on stdin and stdout.\n  - An accepted-run resolver: `--job N` maps to the accepted attempt's folder, never any\n    other.\n- **Contract tests and fakes:**\n  - an in-memory Redis stand-in that can go \"down\";\n  - a live fixture gated by `ETF_RISK_REDIS_URL`;\n  - fallback and equal-result tests;\n  - a Spark-marked test that summary queries on the run of record reproduce the values in spec\n    §8 (for example, windows 529, 466, 311, 174 and 310), skipped when `data/` is absent.\n\n**The author's part.** `src/etf_risk/cache.py`, scaffolded:\n- the key: run id + normalized query + a format version;\n- serialization;\n- cache-aside get-or-compute;\n- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while\n  Redis is down, and decode errors treated as misses;\n- counters for hits, misses and fallbacks.\n\n**Acceptance.**\n- The contract tests pass offline and live.\n- With Redis stopped, every query returns the same result as Spark, and its added latency stays\n  within the timeout and breaker bounds.\n- Redis's peak stays within 128 MiB.\n- The runbook's E3 commands work as written.\n\n**Guarantee.** The cache reads only accepted runs and never writes the job table.\n\n### M5 — E3: new Spark process vs warm Spark session vs Redis\nBranch `feature/result-cache-experiment` · Tooling: Claude Code · Experiment: the project\nauthor, tutored · Depends on M4.\n\n**Configurations** (decided in Part A):\n- N: a new process per query.\n- W: a warm session with the cache off.\n- R: a warm session plus Redis, at hit rates set by the workload's repeats (for example 0, 50\n  and 90%).\n- F: Redis stopped, measuring latency and correctness, then recovery after a restart.\n\n**Measures:**\n- client-side per-query latency on a monotonic clock (medians and spread);\n- realized vs designed hit rate;\n- the warm session's process-tree peak;\n- Redis `memory.peak` and `used_memory_peak`.\n\n**Deliverables:**\n- `docs/result-cache-experiment.md` (Parts A and B, `Author:` line);\n- `docs/result-cache-session.zsh`;\n- `analysis/collect_result_cache_measurements.py` (named apart from the existing caching\n  collector);\n- a batch in `data/outputs-result-cache/<batch>/`.\n\n**Acceptance.** As in earlier experiments: one batch meets every criterion, and drift beyond the\nstated tolerance is reported. Collector and session tests follow the same pattern.\n\n### M6 — Architecture, report and demo\nBranch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · Depends\non M3 and M5.\n\n- **`docs/architecture.md`** (new). It covers:\n  - the batch pipeline and the extension;\n  - native vs Compose placement;\n  - the failure model and the guarantee;\n  - the budget ledger;\n  - the runbook.\n\n  Spec §5's diagram gains `jobs/` and Compose, and its node ids are renamed so they no longer\n  clash with §11's E1–E3. The planned \"design decisions\" item in spec §9 moves here.\n- **Figures X5 (E1/E2) and X6 (E3)**, added together, as X1–X4 were in Stage 4:\n  - in `plots.py`: `FIGURES`, `DOCUMENTED`, and the literal tuple in `compare_documented`;\n  - `test_plots.py`'s figure count (12 → 14);\n  - CSV copies in `docs/measurements/` with their README rows;\n  - every \"twelve figures\" and \"X1–X4\" mention in README, spec, results, demo, measurements\n    README and plots.py.\n- **Spec.** §8 gains \"What the recovery experiments showed\" and \"What the result-cache\n  experiment showed\". §9 and §11 move to implemented, with the final ledger.\n- **`results.md`.** A new section on the extension. The approved §7 changes only with the\n  author's re-approval.\n- **README.** The Status row and the full runbook.\n- **`demo.md`.** A new part: submit; kill the worker mid-run; watch `status --check` recover;\n  cache miss → hit → Redis stopped → fallback → restart.\n\n**Acceptance.**\n- Every number traces to a committed CSV or record, and `plots --check` passes.\n- Every demo and runbook command has been run as written in a fresh worktree.\n- Links are valid.\n- The author has approved the conclusions.\n\n## Separate workstreams (outside M1–M6)\n\nNo milestone branch touches these files, and none waits on them.\n\n- **W1 Data verification** (`feature/data-verification`, own plan):\n  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);\n  - the terms-of-use review;\n  - the cause of the Adj Close steps;\n  - the 36 unverified days;\n  - data-sources.md's missing AI header.\n\n  The extension claims nothing about the analysis results.\n- **W2 Privacy-hook fixes** (`fix/transcript-privacy`):\n  - the uncommitted edits to `.claude/hooks/transcript_privacy.py`,\n    `tests/test_transcript_privacy.py` and one transcript;\n  - the spec §10 hook items: the separator rule, save timing, folders for interruption notices.\n\n  Claude changes the hook only when asked.\n- **W3 AI-log review** (`docs/ai-logs-<date>` branches):\n  - the 68 untracked folders, including the sessions behind PRs #7–#9;\n  - each milestone's logs;\n  - `docs/ai-usage/README.md`'s inconsistencies: it says logs are committed \"alongside the\n    related code\" although they get separate commits, and it credits the hook to Codex only.\n\n  The author reviews; commits are named \"Add reviewed AI logs for …\"; logs are never mixed with\n  code.\n\n## Verification (end to end)\n\n- **Per milestone:**\n  - the offline suite (`uv run --group measure --group plots pytest`), with counts recorded;\n  - the Spark-marked tests;\n  - the live suites on fresh containers (`--group jobs`, and `--group cache` from M4);\n  - `status --check` empty after every live run;\n  - the mutation script (from M1);\n  - the lock diff.\n- **System:** in a fresh worktree on `main` after M6, follow the runbook from `uv sync --frozen`\n  through E1/E2 and E3 smoke runs. Check that:\n  - every accepted run passes its checks and matches its reference by content;\n  - `plots --check` passes;\n  - container peaks are within the ledger.\n\n## Decisions left to review gates\n\n- **M1:** the CLI exit-code fixes; removing the merged worktrees.\n- **M2:** lease, heartbeat and timeout values; whether to add the unique index.\n- **M3 Part A:** cases, job size and repetitions.\n- **M4:** key and serialization (the author).\n- **M5 Part A:** hit rates and workload.\n- **M6:** wording of the extension section in `results.md`.\n"
}
```

## 26. User — 2026-10-23T11:02:58.620Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 27. Assistant — 2026-10-23T11:03:20.017Z

The plan is drafted. Before I ask the plan agent to check it, I want to verify one risk myself: what happens to the worker's database connection when MySQL restarts (one of the E2 cases).

## 28. Assistant — 2026-10-23T11:03:21.706Z

### Tool call: Bash

```
{
  "command": "sed -n '280,295p;520,560p' src/etf_risk/jobs/store.py && echo \"--- mysql.py\" && sed -n '25,107p' src/etf_risk/jobs/mysql.py && echo \"--- kafka.py consumer\" && sed -n '68,121p' src/etf_risk/jobs/kafka.py",
  "description": "Show store connection handling and the MySQL and Kafka adapters"
}
```

## 29. User — 2026-10-23T11:03:22.182Z

### Tool result

```
class JobStore:
    """The job table's operations, each one transaction on the given connection.

    fault, when given, is called with a name from FAULT_POINTS between the statements of a
    transaction; the tests raise there."""

    def __init__(self, connection: Any, dialect: Dialect, *, clock: Clock | None = None,
                 lease: timedelta = DEFAULT_LEASE, fault: Callable[[str], None] | None = None):
        self.connection = connection
        self.dialect = dialect
        self.clock = clock or SystemClock()
        self.lease = lease
        self._fault = fault or (lambda point: None)

    @_retry_conflicts
    def submit(self, params: dict, input_checksums: dict, *, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> int:
        self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                        " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                        job_id=job_id, attempt_number=attempt_number, now=now_value)
        return True

    @contextmanager
    def _transaction(self) -> Iterator[None]:
        cursor = self.connection.cursor()
        cursor.execute(self.dialect.begin)
        try:
            yield
            cursor.execute("COMMIT")
        except BaseException as error:
            # BaseException too: a simulated crash must not leave the transaction open (a real
            # crash closes the connection, and the database rolls back the same way). After a
            # failed COMMIT the ROLLBACK may find nothing left to undo, or fail itself.
            try:
                cursor.execute("ROLLBACK")
            except Exception as rollback_error:
                error.add_note(f"the ROLLBACK after this error failed too: {rollback_error!r}")
            raise

    def _execute(self, sql: str, **params: Any) -> Any:
        cursor = self.connection.cursor()
        cursor.execute(self.dialect.sql(sql), params)
        return cursor

    def _write_one(self, sql: str, **params: Any) -> None:
        """A job_attempts write that must touch exactly one row; otherwise the transaction rolls back."""
        count = self._execute(sql, **params).rowcount
        if count != 1:
            raise StoreInvariantError(f"{count} rows instead of one: {sql}")

    def _fetch_one(self, sql: str, **params: Any) -> dict | None:
        cursor = self._execute(sql, **params)
        row = cursor.fetchone()
        return None if row is None else dict(zip((d[0] for d in cursor.description), row))

    def _fetch_all(self, sql: str, **params: Any) -> list[dict]:
        cursor = self._execute(sql, **params)
        names = [d[0] for d in cursor.description]
--- mysql.py
from typing import Any
from urllib.parse import unquote, urlsplit

from etf_risk.jobs.store import SCHEMA_DIR

ISOLATION_LEVELS = frozenset({"READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"})
CONFLICT_ERRORS = frozenset({1205, 1213})   # lock wait timeout, deadlock


class MySQLDialect:
    name = "mysql"
    begin = "START TRANSACTION"

    @staticmethod
    def sql(text: str) -> str:
        """':name' -> '%(name)s', after doubling any '%' (the store's SQL has none, and no other colons)."""
        return re.sub(r":(\w+)", r"%(\1)s", text.replace("%", "%%"))

    @staticmethod
    def time(value: datetime) -> datetime:
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    def parse_time(value: datetime) -> datetime:
        return value.replace(tzinfo=timezone.utc)

    @staticmethod
    def is_conflict(error: BaseException) -> bool:
        """A PyMySQL error for a lock wait timeout or a deadlock. After a deadlock InnoDB has
        rolled the whole transaction back; after a timeout only the statement, and the
        store's ROLLBACK undoes the rest."""
        return (type(error).__module__.startswith("pymysql") and len(error.args) > 0
                and error.args[0] in CONFLICT_ERRORS)


MYSQL = MySQLDialect()


def connection_options(url: str, database: str | None = None) -> dict:
    """mysql://user:password@host:port[/database] as PyMySQL's connect() arguments; database
    overrides the URL's."""
    parts = urlsplit(url)
    if parts.scheme != "mysql":
        raise ValueError(f"expected a mysql:// URL, not {parts.scheme}://")
    return {"host": parts.hostname or "127.0.0.1", "port": parts.port or 3306,
            "user": unquote(parts.username or "root"), "password": unquote(parts.password or ""),
            "database": database or parts.path.lstrip("/") or None}


def connect_mysql(url: str, *, database: str | None = None, found_rows: bool = True,
                  isolation: str = "REPEATABLE READ", lock_wait_timeout: int | None = None) -> Any:
    """A PyMySQL connection for JobStore(connection, MYSQL). lock_wait_timeout sets the
    session's innodb_lock_wait_timeout, in seconds."""
    import pymysql
    from pymysql.constants import CLIENT

    if isolation not in ISOLATION_LEVELS:
        raise ValueError(f"unknown isolation level: {isolation!r}")
    conn = pymysql.connect(**connection_options(url, database), charset="utf8mb4", autocommit=True,
                           client_flag=CLIENT.FOUND_ROWS if found_rows else 0)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation}")
            if lock_wait_timeout is not None:
                cursor.execute("SET SESSION innodb_lock_wait_timeout = %s", (int(lock_wait_timeout),))
    except BaseException:
        conn.close()
        raise
    return conn


def schema_statements() -> list[str]:
    """schema/mysql.sql as separate statements. Comments go first, since they contain
    semicolons (the schema's string literals contain no '--')."""
    lines = (line.split("--", 1)[0] for line in (SCHEMA_DIR / "mysql.sql").read_text().splitlines())
    return [statement.strip() for statement in "\n".join(lines).split(";") if statement.strip()]


def create_schema(connection: Any) -> None:
    """The job tables, in the connection's database."""
    with connection.cursor() as cursor:
        for statement in schema_statements():
            cursor.execute(statement)
--- kafka.py consumer


class KafkaConsumer:
    def __init__(self, bootstrap: str, topic: str, group: str, *, settings: dict | None = None):
        """settings override consumer_config(); the tests use it to show why earliest matters."""
        from confluent_kafka import Consumer
        self._consumer = Consumer({**consumer_config(bootstrap, group), **(settings or {}), "logger": log})
        self._consumer.subscribe([topic])
        self._closed = False

    def poll(self, timeout: float) -> Delivery | None:
        from confluent_kafka import KafkaException
        message = self._consumer.poll(timeout)
        if message is None:
            return None
        if message.error() is not None:
            if message.error().fatal():
                raise KafkaException(message.error())
            log.warning("consumer error: %s", message.error())
            return None
        return Delivery(message.value() or b"", (message.topic(), message.partition(), message.offset()))

    def commit(self, delivery: Delivery) -> None:
        from confluent_kafka import TopicPartition
        topic, partition, offset = delivery.position
        self._consumer.commit(offsets=[TopicPartition(topic, partition, offset + 1)], asynchronous=False)

    def rewind(self, delivery: Delivery) -> None:
        from confluent_kafka import TopicPartition
        topic, partition, offset = delivery.position
        self._consumer.seek(TopicPartition(topic, partition, offset))

    def assigned(self) -> bool:
        """Whether the group has given this consumer its partition yet."""
        return bool(self._consumer.assignment())

    def close(self) -> None:
        """Leave the group without committing anything; closing again does nothing."""
        if not self._closed:
            self._closed = True
            self._consumer.close()


def create_topic(bootstrap: str, name: str, *, timeout: float = 30.0) -> None:
    from confluent_kafka.admin import AdminClient, NewTopic
    admin = AdminClient({"bootstrap.servers": bootstrap, "logger": log})
    admin.create_topics([NewTopic(name, num_partitions=1, replication_factor=1)],
                        operation_timeout=timeout)[name].result(timeout)


def delete_topic(bootstrap: str, name: str, *, timeout: float = 30.0) -> None:
    from confluent_kafka.admin import AdminClient
    admin = AdminClient({"bootstrap.servers": bootstrap, "logger": log})
    admin.delete_topics([name], operation_timeout=timeout)[name].result(timeout)
```

## 30. Assistant — 2026-10-23T11:04:17.075Z

### Tool call: Agent

```
{
  "description": "Critique and refine the staged plan",
  "subagent_type": "Plan",
  "prompt": "You are reviewing a DRAFT implementation plan for the repository at ~/leveraged-etf-risk-analytics (a CS544 course project: a PySpark leveraged-ETF risk pipeline plus an optional \"systems extension\" with a MySQL job table, Kafka delivery, a worker, a reconciler and, later, a Redis cache). Read the draft at ~/.claude/plans/please-turn-this-outline-cozy-candy.md first. Do NOT modify any file (read-only review). Return a critique and concrete corrections; I will edit the plan myself.\n\nPRIVACY RULES (strict): do NOT read or print `.git/info/exclude`, anything under `~/.claude/projects/` (memory files), `docs/implementation-plan.md`, transcripts under `docs/ai-usage/*/`, or file contents under `data/`. Do not list installed applications.\n\nBackground already established (verified by reading code):\n- Job store `src/etf_risk/jobs/store.py`: token-guarded UPDATEs; `invariant_violations()` (line ~481) with INVARIANT_QUERIES (~127); `DEFAULT_LEASE = 60 s`; `JobStore(connection, dialect, ...)` holds ONE connection for its lifetime with no reconnect (`_transaction` at ~526). `src/etf_risk/jobs/mysql.py`: `connect_mysql()` sets session isolation via `SET SESSION`, PyMySQL autocommit=True, CLIENT.FOUND_ROWS. `src/etf_risk/jobs/kafka.py`: consumer has enable.auto.commit=false, auto.offset.reset=earliest, no session.timeout.ms / max.poll.interval.ms set; non-fatal consumer errors are logged and poll returns None. `src/etf_risk/jobs/worker.py`: `Worker.handle()` claims, acknowledges (commits offset), runs `pipeline.run(claim, run_dir, heartbeat)` synchronously inside `serve()`'s poll loop, then `accept_result`. `src/etf_risk/jobs/reconciler.py`: `run()` loop with `log.exception` per failed pass.\n- Pipeline CLIs: `etf_risk.windows` (`--out-root`, `--name`, writes `<out-root>/<snapshot>/<name>/`), `etf_risk.spark_pipeline` (`--windows`, `--out-root`, `--run-id`, writes `<out-root>/<snapshot>/<defs name>/<run-id>/`, refuses an existing folder with exit 2; exit 0 ok / 1 checks failed / 2 run failed / 3 checksum; but uncaught exceptions outside its try also exit 1; `run.json` is written only in `finally`), `etf_risk.verify` (`--run`; exit 0/1 mismatch/3; uncaught exceptions also 1). `build_spark()` in spark_pipeline.py:132 uses `getOrCreate`, `local[*]`, sets `SPARK_LOCAL_IP`, no `spark.local.dir`. `measure.py` has `TreeSampler` (psutil) and `run_protocol`. Content comparison of two runs: `compare_tables` in analysis/collect_partition_measurements.py:286.\n- Native stride-21 pipeline: 18–47 s wall, peak summed RSS 1.27 GiB (run of record) and 2.62–2.73 GiB (stride experiment); verify ~14 s; calendar-year kind (151 windows) ~20 s. Machine: 8 GiB Apple Silicon laptop (macOS), Docker Desktop VM 3.83 GiB; MySQL container 512 MiB, Kafka 640 MiB limits.\n- Spec §11 authorship: Claude Code writes the Compose services, worker, reconciler and tooling; the project author writes the cache logic and the experiments, with tutoring.\n- I just found: after a MySQL restart, JobStore never reconnects, so the reconciler fails every pass forever and the worker's serve() raises after 5 retries. The plan must add reconnection for E2's database-restart case.\n\nPlease check these specific risks against the actual code and library behavior, and answer each with a recommendation:\n1. confluent-kafka (librdkafka) with a synchronous handler that blocks longer than max.poll.interval.ms: what happens (consumer leaves the group? rebalance? does a later poll rejoin? any redelivery given the offset was committed BEFORE the long run?). With a standby worker in the same group on a one-partition topic, could the standby start a second job while the first still runs? What settings (max.poll.interval.ms, session.timeout.ms, heartbeat) do you recommend, and should the worker instead pause() the partition during a run?\n2. SIGSTOP/SIGCONT of the worker process (the \"stalled worker\" case): librdkafka's background threads stop too; what happens to group membership and to the worker after SIGCONT? Is the planned standby takeover feasible with one partition?\n3. Process-tree cleanup on macOS: PySpark's Python daemon (pyspark/daemon.py) may call os.setpgid to create its own process group, so killpg on the launcher's group may miss Python workers. Check the installed PySpark (4.2.0, in the project's .venv if present: look for site-packages/pyspark/daemon.py) and recommend a robust approach (psutil descendant enumeration with a marker env var? lifeline pipe in a launcher?). Note psutil is only in the `measure` dependency group.\n4. Spark temp/scratch dirs: how to make sure a killed run leaves nothing in /tmp or $TMPDIR (SPARK_LOCAL_DIRS env, spark.local.dir, java.io.tmpdir via JAVA_TOOL_OPTIONS/_JAVA_OPTIONS or PYSPARK_SUBMIT_ARGS, TMPDIR for Python). Check what build_spark and PySpark's launcher honor.\n5. Database reconnect design for JobStore without changing any guard: connection factory, which PyMySQL errors count as disconnects (2003/2006/2013, InterfaceError), re-applying session settings, no automatic replay of the failed operation (a failed COMMIT may have taken effect), and the worker/reconciler retry behavior around it. Is there any way reconnect logic could break \"at most one accepted result per job\"?\n6. Are the milestone boundaries, dependencies, acceptance criteria and tests in the draft measurable and complete? Point out missing steps (e.g., a worker supervisor/restart policy for E2 crashes, max_attempts interplay with graceful stop and E2 repetitions, reference runs for content comparison, clock assumptions, the 'lost job' definition), over-engineering to cut, and anything that contradicts the repository's conventions (experiment docs Part A/B, collectors writing measurements.csv + acceptance.json, session .zsh helpers, merge commits, AI logs in separate commits).\n7. Memory: is running the worker natively (MySQL+Kafka in Compose) the right default for E1/E2 on this 8 GiB machine, and what job size would you recommend for E1/E2 given the peaks above?\n\nKeep the answer structured by the 7 points, each with: finding (with file:line or library source evidence), risk, and the exact change to make in the plan. Be concise; no full rewrite of the plan."
}
```

## 31. User — 2026-10-23T11:04:17.340Z

### Tool result

```
Async agent launched successfully. (This tool result is internal metadata — never quote or paste any part of it, including the agentId below, into a user-facing reply.)
agentId: acd5725aa7188c3c2 (internal ID - do not mention to user. Use SendMessage with to: 'acd5725aa7188c3c2', summary: '<5-10 word recap>' to continue this agent.)
The agent is working in the background. You will be notified automatically when it completes. You know nothing about its results until that notification arrives — do not report, assume, or predict them; continue other work or respond to the user in the meantime.
Do not duplicate this agent's work — avoid working with the same files or topics it is using.
output_file: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/tasks/acd5725aa7188c3c2.output
Do NOT Read or tail this file via the shell tool — it is the full subagent JSONL transcript and reading it will overflow your context. If the user asks for progress, say the agent is still running; you'll get a completion notification.
```

## 32. Assistant — 2026-10-23T11:04:19.400Z

While the plan agent works, I'm adding the reconnect gap to the plan: it goes in milestone 1's findings and milestone 2's design.

## 33. Assistant — 2026-10-23T11:04:22.661Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - Kafka `session.timeout.ms` and `max.poll.interval.ms` are unpinned defaults (45 s, 300 s),\n    while `serve()` runs the pipeline inside its poll loop.",
  "new_string": "  - Kafka `session.timeout.ms` and `max.poll.interval.ms` are unpinned defaults (45 s, 300 s),\n    while `serve()` runs the pipeline inside its poll loop;\n  - **no reconnect.** `JobStore` keeps one connection for life (store.py:286-292, 526). After\n    a MySQL restart the reconciler fails every pass until it is restarted, and the worker's\n    `serve()` raises after 5 retries. E2's database-restart case could therefore never recover\n    without a manual restart. This is fixed in M2;\n  - **no supervisor.** Nothing restarts a worker whose `serve()` ended (`job-queue.md` \"Known\n    limits\": \"by hand for now\")."
}
```

## 34. User — 2026-10-23T11:04:23.756Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 35. Assistant — 2026-10-23T11:04:28.793Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "**Graceful stop.** On SIGTERM or SIGINT the worker stops polling, kills the running step and\ncalls `fail_attempt(retryable=True)`, so the job is requeued at once.",
  "new_string": "**Database reconnect.** The guards and SQL stay unchanged.\n- **Factory.** `JobStore` accepts a connection factory, for MySQL `connect_mysql` with its\n  session settings.\n- **Detecting a lost connection.** On a PyMySQL disconnect error, the store drops the\n  connection. The disconnect errors are 2003, 2006 and 2013, and `InterfaceError`; this is a new\n  `Dialect.is_disconnect`.\n- **Next operation.** It opens a fresh connection.\n- **No replay.** The failed operation is not replayed: it raises, as today, because a failed\n  COMMIT may have taken effect.\n\nThe worker and reconciler then rely on existing semantics:\n- a renewal is tried again at the next heartbeat;\n- `accept_result` is retried within the lease, and is idempotent for the token that won;\n- a lost claim is taken over after its lease.\n\n**Supervision.**\n- **In-process restarts.** `jobs worker` restarts its serve loop in-process after an error, with\n  backoff, and recreates the consumer.\n- **Harness restarts.** A SIGKILLed worker is restarted by the session harness after a delay set\n  in M3 Part A, standing in for a process supervisor.\n- **Reconciler.** It keeps running through outages, with failed passes logged.\n\n**Graceful stop.** On SIGTERM or SIGINT the worker stops polling, kills the running step and\ncalls `fail_attempt(retryable=True)`, so the job is requeued at once. This uses one of the\njob's `max_attempts`, which E2's repetitions must allow for."
}
```

## 36. User — 2026-10-23T11:04:29.863Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 37. Assistant — 2026-10-23T11:04:33.900Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Timeout.** An attempt that exceeds its limit is killed and retried.",
  "new_string": "- **Timeout.** An attempt that exceeds its limit is killed and retried.\n- **Service restarts.** `docker compose restart mysql` and, separately, `restart kafka`, each\n  during a run: neither the worker nor the reconciler has to be restarted by hand, and the job\n  ends with one accepted result."
}
```

## 38. User — 2026-10-23T11:04:34.982Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 39. Assistant — 2026-10-23T11:04:35.615Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **CLI and cleanup tests.**",
  "new_string": "- **CLI and cleanup tests.**\n- **Reconnect tests:**\n  - offline: a connection wrapper that raises a disconnect error once; the next operation\n    reconnects, and the failed one is not replayed;\n  - live: `KILL CONNECTION` from a second session, and a container restart."
}
```

## 40. User — 2026-10-23T11:04:36.711Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 41. Assistant — 2026-10-23T11:05:01.222Z

The plan file now has every milestone in full. While the plan agent checks the riskier assumptions, two decisions shape milestone 2 and the experiments, and they are yours to make.

## 42. Assistant — 2026-10-23T11:05:07.023Z

### Tool call: AskUserQuestion

```
{
  "questions": [
    {
      "question": "Where should the worker run for milestone 2's end-to-end checks and the E1/E2 recovery experiments?",
      "header": "Worker host",
      "multiSelect": false,
      "options": [
        {
          "label": "Native on the host (Recommended)",
          "description": "MySQL and Kafka run in Compose; the worker, reconciler and submit run on macOS with uv, like every earlier native measurement. Only 1.15 GiB of container limits sit in the 3.83 GiB Docker VM. A launcher with a lifeline pipe makes sure a killed worker's Spark processes die with it."
        },
        {
          "label": "Worker in Compose",
          "description": "A worker image (the pipeline image plus the jobs group) with the 2.5 GiB pipeline budget; `docker kill` ends the whole process tree. The limits then add up to 3.65 of the VM's 3.83 GiB, which leaves little headroom, and container timings form a separate configuration."
        }
      ]
    },
    {
      "question": "Spec §11 says Claude Code writes the worker and you write the cache logic and the experiments, with tutoring. Do you also want to write one small, tutored piece of the worker in milestone 2?",
      "header": "Your code",
      "multiSelect": false,
      "options": [
        {
          "label": "Keep the spec's split",
          "description": "Claude writes milestones 1–2 and all tooling. You write cache.py (M4), the E1–E3 experiments, and your own SQL cross-check of accepted results in E1."
        },
        {
          "label": "Also the retry rule",
          "description": "You also write a ~10-line function deciding whether a failed step is worth retrying: checksum error, failed checks or verify mismatch → no; signal, timeout or missing record → yes. Claude prepares its signature, docstring and tests. Spec §11's authorship line gets updated."
        },
        {
          "label": "Also the renewal policy",
          "description": "You also write a ~10-line rule for what the worker does when lease renewals keep failing (database down): how long to keep the Spark run going before it fences itself off. Claude prepares the scaffold and tests; the spec's authorship line gets updated."
        }
      ]
    }
  ]
}
```

## 43. User — 2026-10-23T11:19:42.535Z

### Tool result

```
Your questions have been answered: "Where should the worker run for milestone 2's end-to-end checks and the E1/E2 recovery experiments?"="Native on the host (Recommended)", "Spec §11 says Claude Code writes the worker and you write the cache logic and the experiments, with tutoring. Do you also want to write one small, tutored piece of the worker in milestone 2?"="Keep the spec's split". You can now continue with these answers in mind.
```

## 44. Assistant — 2026-10-23T11:19:44.831Z

Both answers fit the draft: the worker runs natively on the host, and the authorship split stays as spec §11 has it. I'll record both in the plan while the review finishes.

## 45. Assistant — 2026-10-23T11:19:46.915Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "## Ground rules for every milestone",
  "new_string": "**Decided by the author (2026-10-23).**\n- **Worker placement.** The worker, reconciler and submit run natively on the host. MySQL and\n  Kafka (and Redis from M4) run in Compose.\n- **Authorship.** The spec §11 split stays as it is. Claude Code writes M1, M2 and all tooling.\n  The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.\n\n## Ground rules for every milestone"
}
```

## 46. User — 2026-10-23T11:19:48.012Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 47. Assistant — 2026-10-23T11:19:58.675Z

### Tool call: SendMessage

```
{
  "to": "acd5725aa7188c3c2",
  "summary": "Pass the author's two decisions to reviewer",
  "message": "The project author made two decisions that your review should take as fixed: (1) the worker, reconciler and submit run natively on the macOS host, with MySQL and Kafka (and Redis later) in Compose; (2) authorship stays as spec §11 says: Claude Code writes M1, M2 and all tooling, and the author writes cache.py, the experiments and an E1 SQL cross-check, with tutoring. The plan file now also has a database-reconnect design and supervision under M2. Please finish your review with these in mind; no need to restart.",
  "type": "message",
  "recipient": "acd5725aa7188c3c2",
  "recipient_kind": "agent",
  "content": "The project author made two decisions that your r…"
}
```

## 48. User — 2026-10-23T11:19:59.019Z

### Tool result

```
{"success":true,"message":"Message queued for delivery to acd5725aa7188c3c2 at its next tool round. If it finishes first, it is resumed with the message and notifies again, so wait for that notification before resending.","pin":{"id":"acd5725aa7188c3c2","name":"acd5725aa7188c3c2","ref":"40aa4a"}}
```

## 49. Assistant — 2026-10-23T11:20:02.720Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "limit": 60
}
```

## 50. User — 2026-10-23T11:20:02.822Z

### Tool result

```
1	# Plan: finishing the systems extension (spec §11) in six reviewed milestones
2	
3	Status: draft for the author's review. Nothing is implemented until it is approved.
4	
5	## Context
6	
7	Stages 1–4 are merged into `main` (f058095), and so is the extension's job queue: PR #7 (the job
8	table and fencing), PR #8 (Kafka delivery and the reconciler) and PR #9 (Stage 4). What spec
9	§11 still lists as planned:
10	- the real pipeline in the worker (today it runs `SimulatedPipeline`);
11	- the recovery experiments E1/E2;
12	- the Redis result cache;
13	- the cache experiment E3;
14	- their documentation.
15	
16	This plan turns the author's six-point outline into milestones M1–M6, one branch and one PR
17	each. Each milestone has:
18	- deliverables;
19	- acceptance criteria;
20	- tests;
21	- a statement of how it keeps the guarantee.
22	
23	Four cross-cutting requirements run through all of them:
24	- code provenance for `jobs/`;
25	- reproducible dependencies;
26	- startup commands;
27	- measured memory budgets.
28	
29	Data verification, the privacy-hook fixes and AI-log review stay in separate workstreams.
30	
31	State observed on 2026-10-23:
32	- **Main worktree.** It is on `fix/measure-process-kinds` (97c35f3). That branch is pushed but
33	  not merged; it carries the fix for the intermittent `measure` test, which `main`'s README,
34	  spec and demo still call open.
35	- **Uncommitted W2 work.** The worktree holds uncommitted changes to the privacy hook, its tests
36	  and one transcript.
37	- **AI-log folders.** There are 68 untracked AI-log folders.
38	- **`gh` is not installed.**
39	
40	**Decided by the author (2026-10-23).**
41	- **Worker placement.** The worker, reconciler and submit run natively on the host. MySQL and
42	  Kafka (and Redis from M4) run in Compose.
43	- **Authorship.** The spec §11 split stays as it is. Claude Code writes M1, M2 and all tooling.
44	  The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.
45	
46	## Ground rules for every milestone
47	
48	1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has
49	   exactly one, and a job may execute more than once.
50	   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it. The existing
51	     `INVARIANT_QUERIES` and `JobStore.invariant_violations()` (store.py:127, :481) check it.
52	     Together, the first two queries forbid a second accepted attempt for any job.
53	   - **Accepting.** Nothing but `JobStore.accept_result` may produce an accepted attempt.
54	   - **Cleanup** never touches an accepted attempt's folder.
55	   - **The cache** reads accepted runs only and never writes the job table.
56	   - **Checking.** `invariant_violations()` must be empty after every test scenario, every
57	     worker run and every experiment batch.
58	2. **Authorship** (spec §11, "Stages and authorship"). Claude Code writes:
59	   - the Compose services;
60	   - the worker integration;
```

## 51. Assistant — 2026-10-23T11:20:08.192Z

### Tool call: Bash

```
{
  "command": "docker ps --format '{{.Names}}\\t{{.Image}}\\t{{.Status}}' 2>&1 | head -10; echo \"---\"; ps -Ao pid,etime,command 2>/dev/null | grep -E 'etf_risk|pyspark|org.apache.spark' | grep -v grep | head -10",
  "description": "Check for running containers or pipeline processes"
}
```

## 52. User — 2026-10-23T11:20:08.779Z

### Tool result

```
buzzer-20-backend-1	d5ec25359e7e	Up 3 hours
buzzer-20-nginx-1	nginx:1.25-alpine	Up 3 hours
buzzer-20-redis-1	redis:7.0-alpine	Up 3 hours (healthy)
buzzer-20-mysql-1	mysql:8.0	Up 3 hours (healthy)
---
```

## 53. Assistant — 2026-10-23T11:20:19.873Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Batches.** Each recovery batch starts on a fresh MySQL container and records its own peak.",
  "new_string": "- **Batches.** Each recovery batch starts on a fresh MySQL container and records its own peak.\n- **Other containers.** At planning time, another project's containers were running in the same\n  Docker VM. The session helpers' pre-checks therefore count containers outside this Compose\n  project, without printing their names, and require zero before any formal session or budget\n  measurement. They also check that ports 3307, 9094 and 6380 are free."
}
```

## 54. User — 2026-10-23T11:20:20.949Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 55. Assistant — 2026-10-23T11:20:23.092Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 60,
  "limit": 200
}
```

## 56. User — 2026-10-23T11:20:23.163Z

### Tool result

```
60	   - the worker integration;
61	   - the CLIs;
62	   - the injection and measurement tooling;
63	   - their tests.
64	
65	   The project author writes the cache logic and the experiments (design, predictions,
66	   formal sessions, answers), with tutoring. For the author's parts Claude prepares scaffolds
67	   (signatures, docstrings, TODOs, contract tests) and reviews, but does not fill them in.
68	
69	   New files carry an `AI contribution:` line. Experiment documents carry an `Author:` line
70	   like `docs/partition-experiment.md:3-5`, reworded for the tutored model.
71	3. **Review gates.** Each milestone opens with a findings report; nothing is fixed before the
72	   author has read it. Each closes with a stop for review before the PR is merged.
73	4. **Git.**
74	   - **Isolation.** Each milestone gets its own worktree (`.claude/worktrees/<name>`) from an
75	     up-to-date `main`, so the main worktree's W2 changes never enter a milestone branch.
76	   - **Staging and merging.** Stage files by explicit path only. Merge with merge commits,
77	     never squash or rebase. Every commit ends with the Co-Authored-By trailer.
78	   - **AI logs.** Milestone commits contain no AI logs; those go to W3.
79	   - **PRs.** Claude pushes the branch; the author opens and merges the PR on GitHub.
80	   - **Formal sessions** run on a merged, clean commit whose SHA lands in every record. There
81	     are no commits during a session.
82	5. **Privacy.** `data/` and the private plan stay out of Git. Memory files,
83	   `.git/info/exclude` and app lists are never printed in tool calls. Batch folders live under
84	   `data/`.
85	6. **Measurement sessions.** While one runs, other sessions only write and review. They wait
86	   for an explicit confirmation that it ended, then check that its worktree is unchanged.
87	7. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write "one
88	   process", never "one core". Give each experiment a "not claimed" list.
89	
90	## Cross-cutting requirements
91	
92	**A. Code provenance for `jobs/`.**
93	- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob("*.py")` (provenance.py:62),
94	  so no record identifies any file in `jobs/`, including `schema/*.sql`. A plain recursive glob
95	  would collide on `__init__.py`.
96	- **M1 change.** Hash every `*.py` and `*.sql` under `src/etf_risk/` recursively, keyed by
97	  package-relative POSIX path. `model.py` keeps its key; new keys look like `jobs/store.py`. Old
98	  records stay comparable for the files they cover.
99	- **Attempt records (M2 on).** Each attempt writes `attempt.json` with the worker's
100	  `code_state()`, and so does every experiment record.
101	- **Authorship provenance.** Keep the `AI contribution:` lines. Add an origin table to
102	  `job-queue.md`: module → commits (eec1032, e2806bd, cd72957) → PR → tests that verify it.
103	
104	**B. Reproducible dependencies.**
105	- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`
106	  (compose.yaml:13; test docstrings) and are not in `uv.lock`.
107	- **New groups.** M1 adds a `jobs` group with exactly these pins. M4 adds a `cache` group with
108	  an exact `redis` pin.
109	- **Lock changes.** Every lock change may only add packages. numpy 2.5.4, pandas 2.3.3,
110	  pyspark 4.2.0, pyarrow 26.0.0 and psutil 7.2.2 stay unchanged, checked by a lock diff and
111	  `uv lock --check`.
112	- **Commands.** Documented commands use `--group …` and `uv sync --frozen`.
113	- **Images.** Images are pinned by digest. Redis follows the Kafka rule: the newest release at
114	  least two weeks old.
115	- **Host tools.** Each formal session records host tool versions. Seen 2026-10-23: uv 0.11.16,
116	  Java 17.0.10, Docker 28.3.0, Compose v2.38.1, Docker Desktop VM 3.83 GiB.
117	- **Out of scope.** The NumPy pin (spec §9, planned) stays out unless approved.
118	
119	**C. Startup commands.**
120	- **Today.** The README has no `docker compose` commands; they live only in compose.yaml
121	  comments and test docstrings.
122	- **Runbook.** A runbook section in the README (M1 skeleton, filled in by M2, M4 and M6) gives
123	  copy-pasteable commands per configuration:
124	  - test services;
125	  - the E1/E2 stack: MySQL and Kafka in Compose; `init-db`, `create-topic`, worker, reconciler,
126	    submit and `status` on the host;
127	  - the E3 stack: Redis, the query CLI, the warm query service;
128	  - teardown with `down -v`.
129	- **Acceptance.** Every milestone that touches the runbook runs its commands exactly as written
130	  in a fresh worktree.
131	
132	**D. Measured memory budgets.** A ledger in spec §11 records component, limit, measured peak,
133	method, date and commit. Known so far:
134	
135	| Component | Budget | Measured | Source |
136	|---|---|---|---|
137	| MySQL container | 512 MiB | 324–398 MiB per full run on fresh containers; 472 after two runs; 511 after ~2 h | spec §11 |
138	| Kafka container | 640 MiB (256 MiB heap) | 354–478 MiB; 516 with mutation checks | spec §11 |
139	| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB at stride 21 | spec §11 |
140	| Native stride-21 pipeline tree | `measure` stop at 4.8 GiB | 1.27 GiB (run of record) and 2.62–2.73 GiB (stride experiment), summed RSS | spec §8, experiments.md |
141	| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |
142	| Native worker, reconciler, submit | set in M2 | — (M2) | |
143	| Warm query service | set in M4 | — (M4/M5) | |
144	
145	- **What the numbers imply.** Running the worker natively puts only the MySQL and Kafka limits
146	  in the VM (1.15 GiB). But a stride-21 job may need about 2.7 GiB on the host, and earlier
147	  sessions required at least 3.0 GiB free before each protocol. Hence the job-size choice in
148	  M3 Part A.
149	- **Container peaks** come from cgroup `memory.peak`, through a new helper (only
150	  `docker/run.sh` reads it today).
151	- **Native peaks** come from `measure.TreeSampler`.
152	- **Batches.** Each recovery batch starts on a fresh MySQL container and records its own peak.
153	- **Other containers.** At planning time, another project's containers were running in the same
154	  Docker VM. The session helpers' pre-checks therefore count containers outside this Compose
155	  project, without printing their names, and require zero before any formal session or budget
156	  measurement. They also check that ports 3307, 9094 and 6380 are free.
157	- **Exceeded budgets.** A budget that is exceeded stops the session, and budgets change only
158	  at review.
159	
160	## Milestones (numbered as in the outline)
161	
162	Order: M1 → M2 → M3 and M1 → M4 → M5, then M6. M4 does not need M2 or M3, because it can use
163	the run of record. Its code can be written while M3's session runs, under ground rule 6.
164	
165	### M1 — Read the whole project; bring the code up to date
166	Branch `feature/extension-baseline` · Author: Claude Code · Prerequisite: the author merges
167	`fix/measure-process-kinds` (97c35f3) first, since M2–M5 sample memory with its process kinds.
168	
169	**Step 1: audit (read-only).** A findings report goes to the author, grouped as below.
170	- **Reproducibility and provenance**:
171	  - cross-cutting gaps A, B and C;
172	  - the 22 mutation checks in the job docs exist only as prose (no script);
173	  - the merged worktrees `.claude/worktrees/job-queue` and `job-table` are clean and in `main`,
174	    so they can be removed with the author's OK.
175	- **Missing operations**:
176	  - no entry point in `jobs/`, so the "submit CLI" in the §11 diagram does not exist;
177	  - logging is never configured;
178	  - nothing is timed (`Pass` and `Served` are counts only; no `requeued_at` or history);
179	  - `published_at` is cleared by the claim;
180	  - a crash before the claim leaves no trace;
181	  - Kafka `session.timeout.ms` and `max.poll.interval.ms` are unpinned defaults (45 s, 300 s),
182	    while `serve()` runs the pipeline inside its poll loop;
183	  - **no reconnect.** `JobStore` keeps one connection for life (store.py:286-292, 526). After
184	    a MySQL restart the reconciler fails every pass until it is restarted, and the worker's
185	    `serve()` raises after 5 retries. E2's database-restart case could therefore never recover
186	    without a manual restart. This is fixed in M2;
187	  - **no supervisor.** Nothing restarts a worker whose `serve()` ended (`job-queue.md` "Known
188	    limits": "by hand for now").
189	- **Pipeline CLIs**, which matter for M2:
190	  - **Exit 1 is ambiguous.** Exit 1 means "checks failed" (spark_pipeline) or "mismatch"
191	    (verify), but also any uncaught exception. For spark_pipeline that includes exceptions
192	    outside its `try`: `mkdir`, building the record, and writing `run.json` in the `finally`.
193	  - **Missing records.** `run.json` is written only in the `finally`, so a killed run leaves
194	    none.
195	  - **verify gaps.** verify's checksum handler misses `JSONDecodeError`, its `spark.stop()` is
196	    not in a `finally`, and it never checks the run's status.
197	  - **Relative paths.** verify reads `run.json`'s `windows_dir` as stored, so relative paths
198	    assume the repository root.
199	  - **windows refusal.** windows refuses only when `config.json` exists; README:224 says "an
200	    existing folder".
201	- **Documentation drift**:
202	  - `job-table.md`'s claim SQL omits `published_at = NULL` (store.py:334), and its "apart from
203	    `submit`" sentence omits `mark_published`;
204	  - `job-queue.md:90` names tests that start from a confirmed publication, so they do not cover
205	    the job-9 timeline;
206	  - the status blocks of job-table.md:97-103 and job-queue.md:146-160 predate the merges;
207	  - spec §5's diagram omits `jobs/` and Compose yet says "Every box is implemented", and its node
208	    ids E2–E4 clash with §11's E1–E3;
209	  - spec.md has no AI header, although README:321-323 says AI-drafted files do.
210	- **Test helpers**: `WorkerEnv.check` (tests/jobs_backends.py:200) is tied to the simulated
211	  pipeline's `result.json`.
212	
213	**Step 2: fixes, after approval.**
214	- provenance (A);
215	- the `jobs` group, the lock, and `--with` → `--group jobs` everywhere (B);
216	- the runbook skeleton (C);
217	- the `memory.peak` helper (D);
218	- a reproducible mutation-check script (each mutation a patch, applied in a scratch worktree
219	  with a timeout);
220	- job-doc drift and stale status text; the module origin table;
221	- the CLI fixes, if the author agrees:
222	  - uncaught exceptions exit 2, matching spark_pipeline's docstring, so exit 1 always means
223	    checks failed or a mismatch;
224	  - verify catches `JSONDecodeError`;
225	  - verify stops Spark in a `finally`.
226	
227	  These change no result, and they need tests.
228	- removal of the merged worktrees, with the author's OK.
229	
230	**Step 3: revalidation.**
231	- the offline suite;
232	- the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with `--group jobs`;
233	- the mutation script;
234	- MySQL and Kafka peaks read through the helper.
235	
236	**Deliverables.** The findings report; the fixes above.
237	
238	**Acceptance.**
239	- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in
240	  `source_sha256` under a unique key, with the top-level keys unchanged.
241	- `uv lock --check` passes, and the lock diff only adds the `jobs` group's packages.
242	- The live suite passes with the case count of e2806bd (379), or the difference is explained.
243	- Every mutation makes a test fail within its timeout.
244	- Peaks stay within budget.
245	- No file outside the approved scope changes.
246	
247	**Tests.** New cases in `test_provenance.py`; CLI exit-code tests (Spark-marked where needed);
248	job suites on SQLite and live; the mutation script.
249	
250	**Guarantee.** No change to `store.py`'s SQL. The mutation script re-proves that breaking a guard
251	fails a test.
252	
253	### M2 — The worker runs windows → spark_pipeline → verify
254	Branch `feature/worker-pipeline` · Author: Claude Code (spec §11) · Depends on M1.
255	
256	**Design.** The new code is `jobs/pipeline.py`, `jobs/launcher.py`, `jobs/params.py`,
257	`jobs/events.py` and `jobs/__main__.py`, plus small changes to `worker.py` and `kafka.py`. The
258	store's guards stay as they are.
259	
```

## 57. Assistant — 2026-10-23T11:20:28.302Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 259,
  "limit": 260
}
```

## 58. User — 2026-10-23T11:20:28.445Z

### Tool result

```
259	
260	**Job parameters (`params.py`).**
261	- **Schema.** A frozen dataclass: snapshot, kind (`rolling` / `calendar-year` / `full-period`),
262	  window days, stride, anchor, sample ticker. Unknown keys are refused. Tickers come from the
263	  snapshot, and leverages are fixed at 1x and 2x.
264	- **Input checksums.** `submit` computes `input_checksums` from the files that `windows.py`
265	  records in `inputs_sha256`: `daily_returns/*.parquet` and `quality_report.json`.
266	- **Check before running.** The worker re-checks them before step 1. A mismatch fails the attempt
267	  as not retryable.
268	
269	**Steps.** Each step runs as `sys.executable -m etf_risk.<module>` with absolute paths only.
270	Everything lands inside the attempt folder:
271	1. `windows --out-root <run_dir>/windows --name <name>` writes
272	   `<run_dir>/windows/<snapshot>/<name>/`.
273	2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>` writes
274	   `<run_dir>/output/<snapshot>/<name>/<run id>/`.
275	3. `verify --run …` checks that output.
276	
277	Setup for every step:
278	- the working directory, `TMPDIR`, `SPARK_LOCAL_DIRS` and `java.io.tmpdir` all point to
279	  `<run_dir>/.work`;
280	- logs go to `<run_dir>/logs/<step>.log`.
281	
282	**Result rule.**
283	- **When the worker accepts.** Every step exits 0, `run.json` has status `ok`, every
284	  `checks.json` count is 0, `verify.json` has no mismatch and the same breached windows, and
285	  every table has `_SUCCESS`.
286	- **Then.** `.work` is removed and the worker calls `accept_result`.
287	
288	**Failure classification.** This is decided from the records, not the exit code alone.
289	- **Not retryable:**
290	  - a checksum error (exit 3);
291	  - `run.json` status `checks_failed`;
292	  - a verify mismatch;
293	  - a parameter or input-checksum error.
294	- **Retryable:**
295	  - a signal;
296	  - a timeout;
297	  - status `failed`;
298	  - a missing record.
299	
300	Retryable failures go back to the queue until `max_attempts` (3).
301	
302	**Heartbeats.**
303	- **Where.** The worker thread waits on the child with `wait(timeout=…)` and calls `heartbeat()`
304	  every lease/4 (15 s at the 60 s default). There is no background thread, so the database
305	  connection stays on one thread.
306	- **Failed renewals.** A renewal that raises (database unreachable) is retried at the next tick.
307	  When the time since the last successful renewal reaches the lease minus a margin, the worker
308	  fences itself: it kills the run and raises `Fenced`. Two Spark runs on one machine would risk
309	  memory, and the token guard still decides acceptance.
310	
311	**Fencing.** When `heartbeat()` returns false, the worker sends SIGTERM to the step's process
312	group, waits a grace period, sends SIGKILL, and raises `Fenced`. The folder stays and is never
313	referenced.
314	
315	**Timeouts.**
316	- **Limits.** Each step and the whole attempt get a wall-clock limit. Draft values are 120 s,
317	  600 s, 300 s and 900 s, against measured medians of a few seconds, 18–47 s and about 14 s;
318	  they are fixed at review from M2's measurements.
319	- **On timeout.** The process group is killed and the attempt fails as retryable.
320	- **Kafka settings.** `max.poll.interval.ms` (above the attempt limit) and `session.timeout.ms`
321	  are set in `kafka.py` and pinned by tests.
322	
323	**Cleanup.**
324	- **Lifeline.** Each step starts in a new process group behind `launcher.py`, which holds a
325	  "lifeline" pipe from the worker. If the worker dies, even by SIGKILL, the launcher reads EOF
326	  and kills its group. macOS has no parent-death signal.
327	- **Stale groups.** Each attempt writes its group id to `.work/pgid`. On startup, a worker kills
328	  the groups that a previous worker left unfinished.
329	- **`jobs cleanup`** is a dry run unless given `--delete`. It removes folders of failed or expired
330	  attempts that ended more than a grace period ago. Folders with no attempt row are only
331	  reported. It never touches accepted or running attempts.
332	
333	**Database reconnect.** The guards and SQL stay unchanged.
334	- **Factory.** `JobStore` accepts a connection factory, for MySQL `connect_mysql` with its
335	  session settings.
336	- **Detecting a lost connection.** On a PyMySQL disconnect error, the store drops the
337	  connection. The disconnect errors are 2003, 2006 and 2013, and `InterfaceError`; this is a new
338	  `Dialect.is_disconnect`.
339	- **Next operation.** It opens a fresh connection.
340	- **No replay.** The failed operation is not replayed: it raises, as today, because a failed
341	  COMMIT may have taken effect.
342	
343	The worker and reconciler then rely on existing semantics:
344	- a renewal is tried again at the next heartbeat;
345	- `accept_result` is retried within the lease, and is idempotent for the token that won;
346	- a lost claim is taken over after its lease.
347	
348	**Supervision.**
349	- **In-process restarts.** `jobs worker` restarts its serve loop in-process after an error, with
350	  backoff, and recreates the consumer.
351	- **Harness restarts.** A SIGKILLed worker is restarted by the session harness after a delay set
352	  in M3 Part A, standing in for a process supervisor.
353	- **Reconciler.** It keeps running through outages, with failed passes logged.
354	
355	**Graceful stop.** On SIGTERM or SIGINT the worker stops polling, kills the running step and
356	calls `fail_attempt(retryable=True)`, so the job is requeued at once. This uses one of the
357	job's `max_attempts`, which E2's repetitions must allow for.
358	
359	**Event log (`events.py`).** Each process appends JSON lines with UTC times, one flushed line per
360	event:
361	- delivered
362	- claimed
363	- renewed and renewal failed
364	- step start and end
365	- fenced
366	- accepted
367	- failed
368	- requeued
369	- published
370	
371	E2's timings come from these logs plus the tables, without a new table.
372	
373	**CLI** `python -m etf_risk.jobs`:
374	- `init-db`
375	- `create-topic`
376	- `submit`
377	- `worker`
378	- `reconciler`
379	- `cleanup`
380	- `status [--check]`, which prints the tables and `invariant_violations()` and exits 1 on a
381	  violation
382	
383	Flags or `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP` configure it, and logging is set up.
384	
385	**Attempt record.** `attempt.json` holds the worker id, run id, steps (exit code, times), the
386	input checksums as checked and `code_state()`.
387	
388	**Optional defense in depth.** A unique index on accepted attempts per job: a partial index in
389	SQLite, and in MySQL a unique index on a generated column that is `job_id` only when the
390	outcome is accepted. The schema-drift test is updated, and a test shows that a second accepted
391	row is refused.
392	
393	**Deliverables.** The modules above; updated `job-queue.md` (real pipeline, settings table,
394	known limits resolved); the runbook's E1/E2 section; budget rows for the worker, reconciler and
395	submit.
396	
397	**Acceptance.** Native worker, MySQL and Kafka in Compose, on fresh containers:
398	- **Normal runs.** A calendar-year job and a stride-21 job of `full-2026-10-12` each end
399	  `succeeded`, with exactly one accepted attempt that passes every check and verify. Their
400	  content equals a direct CLI run under the `compare_tables` rules
401	  (analysis/collect_partition_measurements.py:286, partition-experiment.md:476-515).
402	- **Stalled worker.** After SIGSTOP for longer than the lease, a standby worker takes over. On
403	  SIGCONT the stalled worker's process tree is gone within the grace period, it writes nothing
404	  more, and the takeover's result is accepted.
405	- **Crashed worker.** After SIGKILL during step 2, no Spark process is left once the lifeline
406	  grace has passed, and the job is requeued after its lease and succeeds.
407	- **Timeout.** An attempt that exceeds its limit is killed and retried.
408	- **Service restarts.** `docker compose restart mysql` and, separately, `restart kafka`, each
409	  during a run: neither the worker nor the reconciler has to be restarted by hand, and the job
410	  ends with one accepted result.
411	- **Temp files.** No new `spark-*` or `blockmgr-*` folder appears in `/tmp` or `$TMPDIR`.
412	- **Cleanup dry run.** It lists exactly the failed and expired attempts.
413	- **Peaks.** Measured and within budget.
414	- **Invariants.** `invariant_violations()` is empty throughout.
415	- **Earlier tests.** Every earlier job test still passes on both stores.
416	
417	**Tests.**
418	- **`test_jobs_pipeline.py`** (offline, with fake step scripts): heartbeat cadence; fencing kills
419	  the group (checked with psutil); timeouts; failure classification; the lifeline (kill the
420	  parent, the grandchild dies); `.work` cleanup; parameter and checksum refusals.
421	- **CLI and cleanup tests.**
422	- **Reconnect tests:**
423	  - offline: a connection wrapper that raises a disconnect error once; the next operation
424	    reconnects, and the failed one is not replayed;
425	  - live: `KILL CONNECTION` from a second session, and a container restart.
426	- **A Spark-marked end-to-end test:** a tiny job through `Worker` with SQLite and `MemoryQueue`.
427	- **A live end-to-end test** gated by the environment variables: real worker and reconciler
428	  processes, SIGKILL mid-run, recovery, then `status --check`.
429	
430	**Guarantee.** Acceptance still goes only through the token guard. Fencing and self-fencing
431	only stop work. Cleanup excludes accepted attempts. The optional index makes a second accepted
432	row impossible at the storage level.
433	
434	### M3 — Recovery experiments E1 and E2
435	Branch `feature/recovery-experiment` · Tooling: Claude Code · Experiment: the project author,
436	tutored · Depends on M2.
437	
438	**Claude's tooling (first commit, with tests).**
439	- **Crash injection.** Crashes at the existing worker fault points (`Worker(fault=…)`,
440	  worker.py:112), chosen by an environment variable and carried out as a real SIGKILL.
441	- **Outside injections.** SIGKILL during a step; SIGSTOP and SIGCONT; `docker compose restart
442	  kafka` or `mysql` at a chosen phase.
443	- **Harness log.** It records each injection and the time each service was ready again.
444	- **Session helpers.** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:
445	  two windows, machine checks, `case n`, a watcher, abort and note, and no commits during the
446	  session.
447	- **Collector.** `analysis/collect_recovery_measurements.py --batch <folder>` imports
448	  `compare_tables` unchanged, as later collectors do. It merges the tables, event logs and
449	  harness log and writes `measurements.csv` and `acceptance.json` (criteria 1–5 as before, plus
450	  "6 guarantee"). It exits 1 on any failed criterion.
451	- **Batches** live in `data/outputs-recovery/<batch>/`.
452	
453	**The author's `docs/recovery-experiment.md`.** Claude scaffolds the headings of Parts A and B
454	(sections 1–15 and History) and the `Author:` line.
455	- **Part A, decided by the author:**
456	  - the cases;
457	  - repetitions;
458	  - lease, heartbeat and reconcile settings;
459	  - the job size (calendar-year vs stride 21, with the memory implications in D);
460	  - metric definitions;
461	  - predictions;
462	  - acceptance criteria;
463	  - stop rules;
464	  - one fresh MySQL container per batch.
465	- **Draft cases offered:**
466	  - worker crash before the claim;
467	  - crash after the claim but before the acknowledgement (the job-9 timeline);
468	  - crash during step 2;
469	  - crash after the pipeline but before acceptance;
470	  - crash after acceptance;
471	  - a stalled worker taken over, then fenced;
472	  - Kafka restart while idle, during a submit, and during a run;
473	  - MySQL restart during a run, shorter and longer than the lease;
474	  - MySQL restart at acceptance (the failed-COMMIT path).
475	- **Metrics per job:**
476	  - injection time;
477	  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;
478	  - recovery: the next `claimed_at`;
479	  - completion: `finished_at`;
480	  - executions;
481	  - accepted results (0 or 1);
482	  - correctness: every check passed, and the content equals the reference;
483	  - lost: not terminal by the deadline.
484	- **E1 cross-check.** The author writes their own SQL for accepted results per job, which must
485	  agree with `invariant_violations()`.
486	
487	**Acceptance.**
488	- One batch meets every Part A criterion.
489	- Across all batches: zero lost jobs and zero jobs with two accepted results; every succeeded
490	  job has exactly one correct accepted result.
491	- Peaks are recorded per batch.
492	- The commit sequence follows the precedent: tooling, Part A (before any measured run), dry
493	  batches and the formal session, Part B, status.
494	
495	**Tests.** Collector and helper tests in the style of `test_caching_collector.py` and
496	`test_caching_session.py`, including planted problems that each fail their criterion; tests of
497	the injection tools.
498	
499	**Guarantee.** This milestone measures it under failures and adds no write path.
500	
501	### M4 — Redis cache for summary queries, with fallback
502	Branch `feature/result-cache` · Infrastructure: Claude Code · Cache logic: the project author,
503	tutored · Depends on M1.
504	
505	**Claude's part.**
506	- **Compose service `redis`:**
507	  - pinned by digest;
508	  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, with persistence off;
509	  - `mem_limit` and `memswap_limit` 128m;
510	  - port `127.0.0.1:6380`;
511	  - a `redis-cli ping` healthcheck.
512	- **Dependencies.** A `cache` group with an exact `redis` pin.
513	- **`src/etf_risk/summary.py`.**
514	  - Named queries over a run's `paired/`. Their SQL comes from the author's `analysis/sql_*.py`
515	    without editing those scripts, since documents cite earlier scripts by hash. The author moves
516	    their own SQL text in; Claude wires it up.
517	  - A one-shot CLI, which is the new-process mode.
518	  - A warm mode: one SparkSession answering JSON-lines requests on stdin and stdout.
```

## 59. Assistant — 2026-10-23T11:20:33.044Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 518,
  "limit": 160
}
```

## 60. User — 2026-10-23T11:20:33.145Z

### Tool result

```
518	  - A warm mode: one SparkSession answering JSON-lines requests on stdin and stdout.
519	  - An accepted-run resolver: `--job N` maps to the accepted attempt's folder, never any
520	    other.
521	- **Contract tests and fakes:**
522	  - an in-memory Redis stand-in that can go "down";
523	  - a live fixture gated by `ETF_RISK_REDIS_URL`;
524	  - fallback and equal-result tests;
525	  - a Spark-marked test that summary queries on the run of record reproduce the values in spec
526	    §8 (for example, windows 529, 466, 311, 174 and 310), skipped when `data/` is absent.
527	
528	**The author's part.** `src/etf_risk/cache.py`, scaffolded:
529	- the key: run id + normalized query + a format version;
530	- serialization;
531	- cache-aside get-or-compute;
532	- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while
533	  Redis is down, and decode errors treated as misses;
534	- counters for hits, misses and fallbacks.
535	
536	**Acceptance.**
537	- The contract tests pass offline and live.
538	- With Redis stopped, every query returns the same result as Spark, and its added latency stays
539	  within the timeout and breaker bounds.
540	- Redis's peak stays within 128 MiB.
541	- The runbook's E3 commands work as written.
542	
543	**Guarantee.** The cache reads only accepted runs and never writes the job table.
544	
545	### M5 — E3: new Spark process vs warm Spark session vs Redis
546	Branch `feature/result-cache-experiment` · Tooling: Claude Code · Experiment: the project
547	author, tutored · Depends on M4.
548	
549	**Configurations** (decided in Part A):
550	- N: a new process per query.
551	- W: a warm session with the cache off.
552	- R: a warm session plus Redis, at hit rates set by the workload's repeats (for example 0, 50
553	  and 90%).
554	- F: Redis stopped, measuring latency and correctness, then recovery after a restart.
555	
556	**Measures:**
557	- client-side per-query latency on a monotonic clock (medians and spread);
558	- realized vs designed hit rate;
559	- the warm session's process-tree peak;
560	- Redis `memory.peak` and `used_memory_peak`.
561	
562	**Deliverables:**
563	- `docs/result-cache-experiment.md` (Parts A and B, `Author:` line);
564	- `docs/result-cache-session.zsh`;
565	- `analysis/collect_result_cache_measurements.py` (named apart from the existing caching
566	  collector);
567	- a batch in `data/outputs-result-cache/<batch>/`.
568	
569	**Acceptance.** As in earlier experiments: one batch meets every criterion, and drift beyond the
570	stated tolerance is reported. Collector and session tests follow the same pattern.
571	
572	### M6 — Architecture, report and demo
573	Branch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · Depends
574	on M3 and M5.
575	
576	- **`docs/architecture.md`** (new). It covers:
577	  - the batch pipeline and the extension;
578	  - native vs Compose placement;
579	  - the failure model and the guarantee;
580	  - the budget ledger;
581	  - the runbook.
582	
583	  Spec §5's diagram gains `jobs/` and Compose, and its node ids are renamed so they no longer
584	  clash with §11's E1–E3. The planned "design decisions" item in spec §9 moves here.
585	- **Figures X5 (E1/E2) and X6 (E3)**, added together, as X1–X4 were in Stage 4:
586	  - in `plots.py`: `FIGURES`, `DOCUMENTED`, and the literal tuple in `compare_documented`;
587	  - `test_plots.py`'s figure count (12 → 14);
588	  - CSV copies in `docs/measurements/` with their README rows;
589	  - every "twelve figures" and "X1–X4" mention in README, spec, results, demo, measurements
590	    README and plots.py.
591	- **Spec.** §8 gains "What the recovery experiments showed" and "What the result-cache
592	  experiment showed". §9 and §11 move to implemented, with the final ledger.
593	- **`results.md`.** A new section on the extension. The approved §7 changes only with the
594	  author's re-approval.
595	- **README.** The Status row and the full runbook.
596	- **`demo.md`.** A new part: submit; kill the worker mid-run; watch `status --check` recover;
597	  cache miss → hit → Redis stopped → fallback → restart.
598	
599	**Acceptance.**
600	- Every number traces to a committed CSV or record, and `plots --check` passes.
601	- Every demo and runbook command has been run as written in a fresh worktree.
602	- Links are valid.
603	- The author has approved the conclusions.
604	
605	## Separate workstreams (outside M1–M6)
606	
607	No milestone branch touches these files, and none waits on them.
608	
609	- **W1 Data verification** (`feature/data-verification`, own plan):
610	  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);
611	  - the terms-of-use review;
612	  - the cause of the Adj Close steps;
613	  - the 36 unverified days;
614	  - data-sources.md's missing AI header.
615	
616	  The extension claims nothing about the analysis results.
617	- **W2 Privacy-hook fixes** (`fix/transcript-privacy`):
618	  - the uncommitted edits to `.claude/hooks/transcript_privacy.py`,
619	    `tests/test_transcript_privacy.py` and one transcript;
620	  - the spec §10 hook items: the separator rule, save timing, folders for interruption notices.
621	
622	  Claude changes the hook only when asked.
623	- **W3 AI-log review** (`docs/ai-logs-<date>` branches):
624	  - the 68 untracked folders, including the sessions behind PRs #7–#9;
625	  - each milestone's logs;
626	  - `docs/ai-usage/README.md`'s inconsistencies: it says logs are committed "alongside the
627	    related code" although they get separate commits, and it credits the hook to Codex only.
628	
629	  The author reviews; commits are named "Add reviewed AI logs for …"; logs are never mixed with
630	  code.
631	
632	## Verification (end to end)
633	
634	- **Per milestone:**
635	  - the offline suite (`uv run --group measure --group plots pytest`), with counts recorded;
636	  - the Spark-marked tests;
637	  - the live suites on fresh containers (`--group jobs`, and `--group cache` from M4);
638	  - `status --check` empty after every live run;
639	  - the mutation script (from M1);
640	  - the lock diff.
641	- **System:** in a fresh worktree on `main` after M6, follow the runbook from `uv sync --frozen`
642	  through E1/E2 and E3 smoke runs. Check that:
643	  - every accepted run passes its checks and matches its reference by content;
644	  - `plots --check` passes;
645	  - container peaks are within the ledger.
646	
647	## Decisions left to review gates
648	
649	- **M1:** the CLI exit-code fixes; removing the merged worktrees.
650	- **M2:** lease, heartbeat and timeout values; whether to add the unique index.
651	- **M3 Part A:** cases, job size and repetitions.
652	- **M4:** key and serialization (the author).
653	- **M5 Part A:** hit rates and workload.
654	- **M6:** wording of the extension section in `results.md`.
655	
```

## 61. Assistant — 2026-10-23T11:20:36.164Z

### Tool call: Bash

```
{
  "command": "git branch --show-current && git status --short | grep -v '^?? docs/ai-usage/' && git log -1 --format='%h %s' main",
  "description": "Recheck branch and working tree state"
}
```

## 62. User — 2026-10-23T11:20:36.619Z

### Tool result

```
fix/measure-process-kinds
 M .claude/hooks/transcript_privacy.py
 M docs/ai-usage/2026-10-19_1643_c82fe879-23/transcript.jsonl
 M docs/ai-usage/2026-10-19_1643_c82fe879-23/transcript.md
 M tests/test_transcript_privacy.py
f058095 Merge branch 'docs/project-status'
```

## 63. Assistant — 2026-10-23T11:20:48.383Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- R: a warm session plus Redis, at hit rates set by the workload's repeats (for example 0, 50\n  and 90%).",
  "new_string": "- R: a warm session plus Redis, at hit rates set by the workload's repeats (for example 0, 50\n  and 90%). Three unparameterized queries on one run give only three keys. The key space\n  therefore comes from queries × accepted runs (the run of record and M2/M3 job runs), × any\n  parameter the author adds in M4, such as a ticker."
}
```

## 64. User — 2026-10-23T11:20:49.544Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 65. Assistant — 2026-10-23T11:20:54.221Z

### Tool call: Bash

```
{
  "command": "grep -n -E \"def run\\b|def run\\(|stop.wait|log.exception|log.info\" src/etf_risk/jobs/reconciler.py",
  "description": "Show the reconciler loop's error handling"
}
```

## 66. User — 2026-10-23T11:20:54.619Z

### Tool result

```
81:    def run(self, stop: threading.Event, *, interval: timedelta = RECONCILE_INTERVAL) -> None:
88:                log.exception("reconciler pass failed")
90:                log.info("reconciler pass: %s", done)
91:            stop.wait(interval.total_seconds())
```

## 67. Assistant — 2026-10-23T11:21:02.318Z

### Tool call: ListAgents

```
{}
```

## 68. User — 2026-10-23T11:21:02.608Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 16m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 69. Assistant — 2026-10-23T11:21:12.071Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/tests/conftest.py"
}
```

## 70. User — 2026-10-23T11:21:12.406Z

### Tool result

```
1	"""Shared fixtures: one local Spark session, and small synthetic snapshots on real NYSE sessions.
2	
3	AI contribution: written with Claude Code (Opus 5.5).
4	"""
5	import json
6	from datetime import date
7	from pathlib import Path
8	
9	import numpy as np
10	import pandas as pd
11	import pandas_market_calendars as mcal
12	import pytest
13	
14	from etf_risk.ingest import write_returns_parquet
15	
16	
17	def nyse_sessions(start: str, n: int) -> list[date]:
18	    days = mcal.get_calendar("NYSE").valid_days(start, pd.Timestamp(start) + pd.Timedelta(days=2 * n + 30))
19	    return [d.date() for d in days[:n]]
20	
21	
22	def write_snapshot(root: Path, name: str, series: dict[str, tuple[list[date], np.ndarray]],
23	                   unverified: list[dict] | None = None) -> Path:
24	    """series: ticker -> (dates, daily returns for rows 1..n); prices start at 100."""
25	    snap = root / "processed" / name
26	    (snap / "daily_returns").mkdir(parents=True)
27	    for ticker, (dates, returns) in series.items():
28	        prices = 100.0 * np.concatenate([[1.0], np.cumprod(1.0 + np.asarray(returns, dtype=float))])
29	        df = pd.DataFrame({"ticker": ticker, "date": dates, "adjusted_price": prices,
30	                           "daily_return": np.concatenate([[np.nan], returns])})
31	        write_returns_parquet(df, snap / "daily_returns" / f"{ticker}.parquet",
32	                              {"snapshot": name, "manifest_sha256": "test-manifest"})
33	    (snap / "quality_report.json").write_text(json.dumps({"unverified_extreme_days": unverified or []}))
34	    return snap
35	
36	
37	@pytest.fixture(scope="session")
38	def spark():
39	    from etf_risk.spark_pipeline import build_spark
40	    session = build_spark(master="local[2]", shuffle_partitions=4)
41	    yield session
42	    session.stop()
43	
```

## 71. Assistant — 2026-10-23T11:21:17.397Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **A Spark-marked end-to-end test:** a tiny job through `Worker` with SQLite and `MemoryQueue`.",
  "new_string": "- **A Spark-marked end-to-end test:** a tiny job through `Worker` with SQLite and `MemoryQueue`,\n  on a synthetic snapshot from `tests/conftest.py`'s `write_snapshot` (passed with\n  `--processed-root`). The steps start their own Spark processes, not the shared fixture\n  session."
}
```

## 72. User — 2026-10-23T11:21:18.501Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 73. Assistant — 2026-10-23T11:21:25.327Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  window days, stride, anchor, sample ticker. Unknown keys are refused. Tickers come from the\n  snapshot, and leverages are fixed at 1x and 2x.",
  "new_string": "  window days, stride, anchor, sample ticker. Unknown keys are refused. Tickers come from the\n  snapshot, and leverages are fixed at 1x and 2x. The processed-data root and the output root\n  are worker settings, not job parameters; the checksums tie a job to its data."
}
```

## 74. User — 2026-10-23T11:21:26.414Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 75. Assistant — 2026-10-23T11:21:34.257Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Then.** `.work` is removed and the worker calls `accept_result`.",
  "new_string": "- **Then.** `.work` is removed, `attempt.json` is written, and the worker calls `accept_result`.\n- **After acceptance.** Nothing in the folder changes. The cache relies on this (\"run outputs\n  never change\", spec §11), and a test checks the folder's file checksums before and after."
}
```

## 76. Assistant — 2026-10-23T11:21:34.305Z

### Tool call: ListAgents

```
{}
```

## 77. User — 2026-10-23T11:21:35.416Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 78. User — 2026-10-23T11:21:35.530Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 17m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 79. Assistant — 2026-10-23T11:21:43.517Z

### Tool call: Bash

```
{
  "command": "sed -n '58,72p' docs/demo.md",
  "description": "Show the demo's calendar-year run commands"
}
```

## 80. User — 2026-10-23T11:21:43.891Z

### Tool result

````
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
````

## 81. Assistant — 2026-10-23T11:21:47.694Z

### Tool call: ListAgents

```
{}
```

## 82. User — 2026-10-23T11:21:47.782Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 17m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 83. Assistant — 2026-10-23T11:21:58.948Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "**Acceptance.** As in earlier experiments: one batch meets every criterion, and drift beyond the\nstated tolerance is reported. Collector and session tests follow the same pattern.",
  "new_string": "**Acceptance.** As in earlier experiments: one batch meets every criterion, and drift beyond the\nstated tolerance is reported.\n\n**Tests.** Collector tests with planted problems, each failing its criterion, and session-helper\ntests, both in the pattern of `test_caching_collector.py` and `test_caching_session.py`; a test\nthat the workload generator gives the designed hit rate.\n\n**Guarantee.** Read-only for the job table; it queries accepted runs only."
}
```

## 84. User — 2026-10-23T11:22:00.085Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 85. Assistant — 2026-10-23T11:22:00.838Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- Links are valid.\n- The author has approved the conclusions.",
  "new_string": "- Links are valid.\n- The author has approved the conclusions.\n\n**Tests.** `test_plots.py` updated for 14 figures and the X5/X6 checks; `plots --check`; a link\ncheck over `docs/`; the full offline suite.\n\n**Guarantee.** Documentation only. The architecture page states the guarantee and where it is\nenforced and checked."
}
```

## 86. User — 2026-10-23T11:22:01.972Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 87. Assistant — 2026-10-23T11:22:06.766Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "**Guarantee.** The cache reads only accepted runs and never writes the job table.",
  "new_string": "**Tests.**\n- Contract tests (Claude) that the author's `cache.py` must pass: key determinism and\n  separation (different runs or queries never share a key); equal results from the cache and\n  from Spark; fallback while \"down\"; a bounded fallback cost; decode errors treated as misses.\n- The resolver refuses non-accepted runs.\n- Live tests against the Compose Redis.\n- The Spark-marked spec §8 test.\n\n**Guarantee.** The cache reads only accepted runs and never writes the job table."
}
```

## 88. User — 2026-10-23T11:22:07.894Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 89. Assistant — 2026-10-23T11:22:13.384Z

### Tool call: Bash

```
{
  "command": "git log -1 --format='%B' e2806bd | grep -n -i -E 'mutation|broke|broken|guard' | head -20",
  "description": "Find the mutation checks in a commit message"
}
```

## 90. User — 2026-10-23T11:22:13.807Z

### Tool result

```
49:that run a loop stop it themselves, so a broken guard fails them rather
56:- mutation checks of the job-id validation: 4 breakages in 5 runs, one
62:- mutation checks of the rest, after the test fixes: 18 breakages in
```

## 91. Assistant — 2026-10-23T11:22:15.696Z

### Tool call: Bash

```
{
  "command": "git log -1 --format='%B' e2806bd | sed -n '44,75p'",
  "description": "Show the mutation-check part of that commit message"
}
```

## 92. User — 2026-10-23T11:22:16.143Z

### Tool result

```
delivery and the reconciler with a timeline; the spec and README record
the status.

Tests: test_jobs_reconciler, test_jobs_queue and test_jobs_kafka, and
the store's transition matrix extended to the new operations. Tests
that run a loop stop it themselves, so a broken guard fails them rather
than hanging them.

This revision, on 2026-10-23:
- offline: 200 passed and 17 skipped;
- against Kafka 4.3.1, with the job table on SQLite: 210 passed, and
  the 7 MySQL tests skipped;
- mutation checks of the job-id validation: 4 breakages in 5 runs, one
  of them also against Kafka; tests failed in all 5, and none ran into
  the timeout.

Earlier revisions of this change, before the job-id validation:
- against MySQL 8.4.13 and Kafka 4.3.1: 353 passed;
- mutation checks of the rest, after the test fixes: 18 breakages in
  20 runs, each with a timeout; tests failed in all 20, and none ran
  into the timeout;
- the whole suite: 411 passed and 15 skipped, also before the bounded
  retries and the test fixes, which only touch the job queue.

MySQL has not been run against this revision.

Memory (cgroup memory.peak, which includes page cache): MySQL reached
472 MiB after two runs on a fresh container, and 511 MiB of its 512 MiB
over about two hours of repeated runs. Kafka reached at most 516 of
640 MiB. Neither hit its limit. MySQL's figures show limited headroom;
they are not evidence that longer runs stay within the limit (spec §11).
```

## 93. Assistant — 2026-10-23T11:22:22.621Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- a reproducible mutation-check script (each mutation a patch, applied in a scratch worktree\n  with a timeout);",
  "new_string": "- a reproducible mutation-check script (each mutation a patch, applied in a scratch worktree\n  with a timeout). The original 22 survive only as counts and partial descriptions\n  (job-table.md:98-102, job-queue.md:157-164, e2806bd's message), so the script's list is\n  rebuilt from those descriptions and documented as such, not claimed identical;"
}
```

## 94. User — 2026-10-23T11:22:23.716Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 95. Assistant — 2026-10-23T11:22:23.850Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- Every mutation makes a test fail within its timeout.",
  "new_string": "- Every mutation in the rebuilt list makes a test fail within its timeout."
}
```

## 96. User — 2026-10-23T11:22:24.906Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 97. Assistant — 2026-10-23T11:22:29.328Z

### Tool call: ListAgents

```
{}
```

## 98. User — 2026-10-23T11:22:29.416Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 18m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 99. Assistant — 2026-10-23T11:22:37.890Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "## Ground rules for every milestone",
  "new_string": "## At a glance\n\n| # | Branch (one PR each) | Written by | Needs | Main deliverable | Done when |\n|---|---|---|---|---|---|\n| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; provenance, `jobs` group, runbook skeleton, peak helper, mutation script | provenance covers `jobs/`; lock adds only; live suite 379; mutations caught |\n| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline in the worker; heartbeats, fencing, timeouts, cleanup, reconnect, CLI | crash, stall, timeout and restart cases end with one accepted, correct result |\n| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, session, batch, collector | a batch meets Part A; no lost job, no second acceptance |\n| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py` | M1 | cache-aside with fallback | contract tests pass; same results with Redis down |\n| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, session, batch, collector | a batch meets Part A |\n| M6 | `docs/extension-report` | Claude drafts, author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |\n\n## Ground rules for every milestone"
}
```

## 100. User — 2026-10-23T11:22:39.003Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 101. Assistant — 2026-10-23T11:22:41.656Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 38,
  "limit": 25
}
```

## 102. User — 2026-10-23T11:22:41.754Z

### Tool result

```
38	- **`gh` is not installed.**
39	
40	**Decided by the author (2026-10-23).**
41	- **Worker placement.** The worker, reconciler and submit run natively on the host. MySQL and
42	  Kafka (and Redis from M4) run in Compose.
43	- **Authorship.** The spec §11 split stays as it is. Claude Code writes M1, M2 and all tooling.
44	  The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.
45	
46	## At a glance
47	
48	| # | Branch (one PR each) | Written by | Needs | Main deliverable | Done when |
49	|---|---|---|---|---|---|
50	| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; provenance, `jobs` group, runbook skeleton, peak helper, mutation script | provenance covers `jobs/`; lock adds only; live suite 379; mutations caught |
51	| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline in the worker; heartbeats, fencing, timeouts, cleanup, reconnect, CLI | crash, stall, timeout and restart cases end with one accepted, correct result |
52	| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, session, batch, collector | a batch meets Part A; no lost job, no second acceptance |
53	| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py` | M1 | cache-aside with fallback | contract tests pass; same results with Redis down |
54	| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, session, batch, collector | a batch meets Part A |
55	| M6 | `docs/extension-report` | Claude drafts, author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |
56	
57	## Ground rules for every milestone
58	
59	1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has
60	   exactly one, and a job may execute more than once.
61	   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it. The existing
62	     `INVARIANT_QUERIES` and `JobStore.invariant_violations()` (store.py:127, :481) check it.
```

## 103. Assistant — 2026-10-23T11:22:48.041Z

### Tool call: Bash

```
{
  "command": "sed -n '60,89p' src/etf_risk/jobs/queue.py",
  "description": "Show the job submission function"
}
```

## 104. User — 2026-10-23T11:22:48.453Z

### Tool result

```
            return None
        job_id = int(self.value)
        return job_id if job_id <= MAX_JOB_ID else None


class Publisher(Protocol):
    def publish(self, job_id: int) -> bool: ...        # True once the broker confirmed the message


class Consumer(Protocol):
    def poll(self, timeout: float) -> Delivery | None: ...
    def commit(self, delivery: Delivery) -> None: ...  # the group resumes after this message
    def rewind(self, delivery: Delivery) -> None: ...  # this consumer reads the message again
    def close(self) -> None: ...


@dataclass(frozen=True)
class Submitted:
    job_id: int
    published: bool      # the broker confirmed the message
    recorded: bool       # and published_at was set: the job was still queued, unchanged


def submit_job(store: JobStore, publisher: Publisher, params: dict, input_checksums: dict, *,
               max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> Submitted:
    """Insert a job and publish it. recorded is False when the publication was not confirmed,
    or when a worker claimed the job before the confirmation could be recorded."""
    job_id = store.submit(params, input_checksums, max_attempts=max_attempts)
    published = publisher.publish(job_id)
    return Submitted(job_id, published, published and store.mark_published(job_id, version=0))
```

## 105. Assistant — 2026-10-23T11:22:50.075Z

### Tool call: ListAgents

```
{}
```

## 106. User — 2026-10-23T11:22:50.154Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 18m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 107. Assistant — 2026-10-23T11:22:58.797Z

### Tool call: Bash

```
{
  "command": "grep -c '' ~/.claude/plans/please-turn-this-outline-cozy-candy.md && grep -n '^### \\|^## ' ~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "description": "Show the plan file's length and section outline"
}
```

## 108. User — 2026-10-23T11:22:59.037Z

### Tool result

```
695
5:## Context
46:## At a glance
57:## Ground rules for every milestone
101:## Cross-cutting requirements
171:## Milestones (numbered as in the outline)
176:### M1 — Read the whole project; bring the code up to date
266:### M2 — The worker runs windows → spark_pipeline → verify
453:### M3 — Recovery experiments E1 and E2
520:### M4 — Redis cache for summary queries, with fallback
572:### M5 — E3: new Spark process vs warm Spark session vs Redis
607:### M6 — Architecture, report and demo
646:## Separate workstreams (outside M1–M6)
673:## Verification (end to end)
688:## Decisions left to review gates
```

## 109. Assistant — 2026-10-23T11:23:03.785Z

### Tool call: Bash

```
{
  "command": "f=$(ls .venv/lib/python3.12/site-packages/pyspark/daemon.py 2>/dev/null); echo \"${f:-no venv daemon.py}\"; [ -n \"$f\" ] && grep -n -E 'setpgid|setsid|getppid|stdin' \"$f\" | head -12",
  "description": "Check whether PySpark's daemon changes its process group"
}
```

## 110. User — 2026-10-23T11:23:04.415Z

### Tool result

```
.venv/lib/python3.12/site-packages/pyspark/daemon.py
115:    os.setpgid(0, 0)
141:    # re-open stdin/stdout in 'wb' mode
142:    stdin_bin = os.fdopen(sys.stdin.fileno(), "rb", 4)
197:                    worker_pid = read_int(stdin_bin)
199:                    # Spark told us to exit by closing stdin
```

## 111. Assistant — 2026-10-23T11:23:13.176Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "**Fencing.** When `heartbeat()` returns false, the worker sends SIGTERM to the step's process\ngroup, waits a grace period, sends SIGKILL, and raises `Fenced`. The folder stays and is never\nreferenced.",
  "new_string": "**Fencing.** When `heartbeat()` returns false, the worker terminates the step's whole process\ntree and raises `Fenced`. The folder stays and is never referenced.\n\nHow the tree is terminated:\n- **Why not a group kill.** Killing the process group is not enough: PySpark's daemon calls\n  `os.setpgid(0, 0)` (`.venv/…/pyspark/daemon.py:115`), so its Python workers leave the step's\n  group.\n- **The tree kill.** Every kill enumerates the descendants with psutil, sends SIGTERM to all,\n  waits a grace period, sends SIGKILL to any survivors, and then checks that none remain.\n- **Dependency.** psutil 7.2.2, already locked, joins the `jobs` group."
}
```

## 112. User — 2026-10-23T11:23:14.287Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 113. Assistant — 2026-10-23T11:23:16.201Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Lifeline.** Each step starts in a new process group behind `launcher.py`, which holds a\n  \"lifeline\" pipe from the worker. If the worker dies, even by SIGKILL, the launcher reads EOF\n  and kills its group. macOS has no parent-death signal.\n- **Stale groups.** Each attempt writes its group id to `.work/pgid`. On startup, a worker kills\n  the groups that a previous worker left unfinished.",
  "new_string": "- **Lifeline.** Each step starts behind `launcher.py`, which holds a \"lifeline\" pipe from the\n  worker. If the worker dies, even by SIGKILL, the launcher reads EOF and kills its descendant\n  tree in the same way as fencing. macOS has no parent-death signal.\n- **Stale trees.** Each attempt writes the launcher's pid and start time to `.work/launcher.json`.\n  On startup, a worker kills the trees that a previous worker left unfinished. The start time\n  guards against a reused pid."
}
```

## 114. User — 2026-10-23T11:23:17.252Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 115. Assistant — 2026-10-23T11:23:20.882Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **New groups.** M1 adds a `jobs` group with exactly these pins. M4 adds a `cache` group with\n  an exact `redis` pin.",
  "new_string": "- **New groups.** M1 adds a `jobs` group with exactly these pins. M2 adds `psutil==7.2.2` to it;\n  psutil is already locked through `measure`. M4 adds a `cache` group with an exact `redis` pin."
}
```

## 116. User — 2026-10-23T11:23:21.941Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 117. Assistant — 2026-10-23T11:23:22.372Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "heartbeat cadence; fencing kills\n  the group (checked with psutil);",
  "new_string": "heartbeat cadence; fencing kills\n  the whole tree, including a grandchild that moved to its own process group as PySpark's\n  daemon does (checked with psutil);"
}
```

## 118. User — 2026-10-23T11:23:23.433Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 119. Assistant — 2026-10-23T11:23:26.084Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **On timeout.** The process group is killed and the attempt fails as retryable.",
  "new_string": "- **On timeout.** The process tree is killed and the attempt fails as retryable."
}
```

## 120. Assistant — 2026-10-23T11:23:26.175Z

### Tool call: ListAgents

```
{}
```

## 121. User — 2026-10-23T11:23:27.154Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 122. User — 2026-10-23T11:23:27.238Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 19m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 123. Assistant — 2026-10-23T11:23:57.647Z

### Tool call: Bash

```
{
  "command": "grep -n -A14 \"^def environment\" src/etf_risk/spark_pipeline.py | head -24; echo \"---\"; grep -n -E \"PYSPARK_SUBMIT_ARGS|extraJavaOptions|--conf\" .venv/lib/python3.12/site-packages/pyspark/java_gateway.py | head -8",
  "description": "Show how the Java version is recorded and how PySpark starts its JVM"
}
```

## 124. User — 2026-10-23T11:23:58.172Z

### Tool result

```
628:def environment() -> dict:
629-    env = {
630-        "platform": platform.platform(), "macos": platform.mac_ver()[0] or None, "machine": platform.machine(),
631-        "cpu_count": os.cpu_count(), "python": platform.python_version(),
632-        "packages": {p: _version(p) for p in ("pyspark", "pandas", "numpy", "pyarrow", "pandas_market_calendars", "psutil")},
633-    }
634-    try:
635-        java = subprocess.run(["java", "-version"], capture_output=True, text=True, timeout=10)
636-        env["java"] = (java.stderr or java.stdout).splitlines()[0]
637-    except (OSError, subprocess.SubprocessError, IndexError):
638-        env["java"] = "unknown"
639-    try:
640-        import psutil
641-        env["ram_total_bytes"] = psutil.virtual_memory().total
642-    except ImportError:
---
71:                command += ["--conf", "%s=%s" % (k, v)]
72:        submit_args = os.environ.get("PYSPARK_SUBMIT_ARGS", "pyspark-shell")
74:            submit_args = " ".join(["--conf spark.ui.enabled=false", submit_args])
```

## 125. Assistant — 2026-10-23T11:24:05.391Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "Setup for every step:\n- the working directory, `TMPDIR`, `SPARK_LOCAL_DIRS` and `java.io.tmpdir` all point to\n  `<run_dir>/.work`;\n- logs go to `<run_dir>/logs/<step>.log`.",
  "new_string": "Setup for every step:\n- the working directory, `TMPDIR` and `SPARK_LOCAL_DIRS` point to `<run_dir>/.work`;\n- `java.io.tmpdir` is set through `PYSPARK_SUBMIT_ARGS=\"--driver-java-options\n  -Djava.io.tmpdir=<run_dir>/.work/tmp pyspark-shell\"`, which PySpark reads when it starts the\n  JVM (`pyspark/java_gateway.py:72`). It is not set through `JAVA_TOOL_OPTIONS`: its \"Picked\n  up …\" notice would replace the Java version that `environment()` records in `run.json`\n  (spark_pipeline.py:635-636);\n- logs go to `<run_dir>/logs/<step>.log`."
}
```

## 126. Assistant — 2026-10-23T11:24:05.477Z

### Tool call: ListAgents

```
{}
```

## 127. User — 2026-10-23T11:24:06.502Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 128. User — 2026-10-23T11:24:06.604Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 19m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 129. Assistant — 2026-10-23T11:24:14.467Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Kafka settings.** `max.poll.interval.ms` (above the attempt limit) and `session.timeout.ms`\n  are set in `kafka.py` and pinned by tests.",
  "new_string": "- **Kafka settings.** `max.poll.interval.ms` (above the attempt limit) and `session.timeout.ms`\n  are set in `kafka.py` and pinned by tests.\n  - **Why the poll limit matters.** `serve()` does not poll while a pipeline runs. If a run\n    outlasted the poll limit, librdkafka would leave the group, and a standby worker in the same\n    group could take the partition and start a second Spark run on this machine. The offset is\n    committed before the run, so the job itself is not redelivered.\n  - **Confirmation.** M2's live tests confirm this behaviour, and the stalled-worker case relies\n    on it: a SIGSTOPped consumer misses its session timeout, and the standby takes over."
}
```

## 130. User — 2026-10-23T11:24:15.588Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 131. Assistant — 2026-10-23T11:24:18.785Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 266,
  "limit": 80
}
```

## 132. User — 2026-10-23T11:24:18.886Z

### Tool result

```
266	### M2 — The worker runs windows → spark_pipeline → verify
267	Branch `feature/worker-pipeline` · Author: Claude Code (spec §11) · Depends on M1.
268	
269	**Design.** The new code is `jobs/pipeline.py`, `jobs/launcher.py`, `jobs/params.py`,
270	`jobs/events.py` and `jobs/__main__.py`, plus small changes to `worker.py` and `kafka.py`. The
271	store's guards stay as they are.
272	
273	**Job parameters (`params.py`).**
274	- **Schema.** A frozen dataclass: snapshot, kind (`rolling` / `calendar-year` / `full-period`),
275	  window days, stride, anchor, sample ticker. Unknown keys are refused. Tickers come from the
276	  snapshot, and leverages are fixed at 1x and 2x. The processed-data root and the output root
277	  are worker settings, not job parameters; the checksums tie a job to its data.
278	- **Input checksums.** `submit` computes `input_checksums` from the files that `windows.py`
279	  records in `inputs_sha256`: `daily_returns/*.parquet` and `quality_report.json`.
280	- **Check before running.** The worker re-checks them before step 1. A mismatch fails the attempt
281	  as not retryable.
282	
283	**Steps.** Each step runs as `sys.executable -m etf_risk.<module>` with absolute paths only.
284	Everything lands inside the attempt folder:
285	1. `windows --out-root <run_dir>/windows --name <name>` writes
286	   `<run_dir>/windows/<snapshot>/<name>/`.
287	2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>` writes
288	   `<run_dir>/output/<snapshot>/<name>/<run id>/`.
289	3. `verify --run …` checks that output.
290	
291	Setup for every step:
292	- the working directory, `TMPDIR` and `SPARK_LOCAL_DIRS` point to `<run_dir>/.work`;
293	- `java.io.tmpdir` is set through `PYSPARK_SUBMIT_ARGS="--driver-java-options
294	  -Djava.io.tmpdir=<run_dir>/.work/tmp pyspark-shell"`, which PySpark reads when it starts the
295	  JVM (`pyspark/java_gateway.py:72`). It is not set through `JAVA_TOOL_OPTIONS`: its "Picked
296	  up …" notice would replace the Java version that `environment()` records in `run.json`
297	  (spark_pipeline.py:635-636);
298	- logs go to `<run_dir>/logs/<step>.log`.
299	
300	**Result rule.**
301	- **When the worker accepts.** Every step exits 0, `run.json` has status `ok`, every
302	  `checks.json` count is 0, `verify.json` has no mismatch and the same breached windows, and
303	  every table has `_SUCCESS`.
304	- **Then.** `.work` is removed, `attempt.json` is written, and the worker calls `accept_result`.
305	- **After acceptance.** Nothing in the folder changes. The cache relies on this ("run outputs
306	  never change", spec §11), and a test checks the folder's file checksums before and after.
307	
308	**Failure classification.** This is decided from the records, not the exit code alone.
309	- **Not retryable:**
310	  - a checksum error (exit 3);
311	  - `run.json` status `checks_failed`;
312	  - a verify mismatch;
313	  - a parameter or input-checksum error.
314	- **Retryable:**
315	  - a signal;
316	  - a timeout;
317	  - status `failed`;
318	  - a missing record.
319	
320	Retryable failures go back to the queue until `max_attempts` (3).
321	
322	**Heartbeats.**
323	- **Where.** The worker thread waits on the child with `wait(timeout=…)` and calls `heartbeat()`
324	  every lease/4 (15 s at the 60 s default). There is no background thread, so the database
325	  connection stays on one thread.
326	- **Failed renewals.** A renewal that raises (database unreachable) is retried at the next tick.
327	  When the time since the last successful renewal reaches the lease minus a margin, the worker
328	  fences itself: it kills the run and raises `Fenced`. Two Spark runs on one machine would risk
329	  memory, and the token guard still decides acceptance.
330	
331	**Fencing.** When `heartbeat()` returns false, the worker terminates the step's whole process
332	tree and raises `Fenced`. The folder stays and is never referenced.
333	
334	How the tree is terminated:
335	- **Why not a group kill.** Killing the process group is not enough: PySpark's daemon calls
336	  `os.setpgid(0, 0)` (`.venv/…/pyspark/daemon.py:115`), so its Python workers leave the step's
337	  group.
338	- **The tree kill.** Every kill enumerates the descendants with psutil, sends SIGTERM to all,
339	  waits a grace period, sends SIGKILL to any survivors, and then checks that none remain.
340	- **Dependency.** psutil 7.2.2, already locked, joins the `jobs` group.
341	
342	**Timeouts.**
343	- **Limits.** Each step and the whole attempt get a wall-clock limit. Draft values are 120 s,
344	  600 s, 300 s and 900 s, against measured medians of a few seconds, 18–47 s and about 14 s;
345	  they are fixed at review from M2's measurements.
```

## 133. Assistant — 2026-10-23T11:24:24.732Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Limits.** Each step and the whole attempt get a wall-clock limit. Draft values are 120 s,\n  600 s, 300 s and 900 s, against measured medians of a few seconds, 18–47 s and about 14 s;\n  they are fixed at review from M2's measurements.",
  "new_string": "- **Limits.** Each step and the whole attempt get a wall-clock limit. The drafts, fixed at review\n  from M2's measurements:\n\n  | Limit | Draft | Measured so far |\n  |---|---|---|\n  | windows | 120 s | a few seconds |\n  | spark_pipeline | 600 s | 18–47 s at stride 21 |\n  | verify | 300 s | about 14 s |\n  | whole attempt | 900 s | — |"
}
```

## 134. Assistant — 2026-10-23T11:24:24.811Z

### Tool call: ListAgents

```
{}
```

## 135. User — 2026-10-23T11:24:25.823Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 136. User — 2026-10-23T11:24:25.913Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 20m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 137. Assistant — 2026-10-23T11:24:38.896Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Batches** live in `data/outputs-recovery/<batch>/`.",
  "new_string": "- **Batches** live in `data/outputs-recovery/<batch>/`.\n- **Reference runs.** Before each batch, the harness makes a reference run per job parameter set\n  with direct CLI calls on the same commit, not through the worker. The collector compares every\n  accepted run with it.\n- **Clock.** All times come from the host clock in UTC. The store passes times as parameters, and\n  MySQL's clock is never used, so the harness log, event logs and tables share one clock."
}
```

## 138. User — 2026-10-23T11:24:40.040Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 139. Assistant — 2026-10-23T11:24:41.082Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - lost: not terminal by the deadline.",
  "new_string": "  - lost: not terminal by the deadline. A draft deadline, for Part A to fix, is lease +\n    reconcile interval + publication grace + (attempts left × attempt limit) + margin.\n- **Attempts.** `submit --max-attempts` lets Part A give experiment jobs enough attempts for\n  cases with repeated failures. A job that runs out fails; it is not lost, and it still keeps\n  the guarantee."
}
```

## 140. User — 2026-10-23T11:24:42.149Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 141. Assistant — 2026-10-23T11:24:43.465Z

### Tool call: ListAgents

```
{}
```

## 142. User — 2026-10-23T11:24:43.594Z

### Tool result

```
This session is leveraged-etf-risk-analytics-aa [f8de98] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Subagents (1):
  acd5725aa7188c3c2  ·  Plan  ·  running  ·  started 20m ago

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 13h ago
  buzzer-20-d8 [ecb5b1]  ·  interactive  ·  idle  ·  started 6h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 13h ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 3h ago
```

## 143. Assistant — 2026-10-23T11:24:56.060Z

### Tool call: ToolSearch

```
{
  "query": "select:ExitPlanMode",
  "max_results": 1
}
```

## 144. User — 2026-10-23T11:24:56.230Z

### Tool result

````
```
{
  "type": "tool_reference",
  "tool_name": "ExitPlanMode"
}
```
````

## 145. Assistant — 2026-10-23T11:25:05.885Z

The plan is ready for your review in `~/.claude/plans/please-turn-this-outline-cozy-candy.md`. Nothing has been implemented yet.

It turns your outline into six milestones, M1–M6, numbered to match your six points. Each has its own branch and PR, deliverables, acceptance criteria, tests, and a line on how it keeps the guarantee. That guarantee is that a job accepts at most one result, and a succeeded job has exactly one. The plan also covers:

- **Provenance for `jobs/`:** today's code-state hashes skip everything under `jobs/`, including the SQL schema.
- **Dependencies:** the MySQL and Kafka clients get exact pins in `uv.lock` instead of being added with `--with`.
- **Startup commands:** one runbook in the README.
- **Memory budgets:** a table of each component's budget against its measured peak.
- **Separate workstreams:** data verification, the privacy-hook fixes and AI-log review each get their own branch, and no milestone touches their files.

Your two decisions are recorded: the worker runs natively on the host, and the authorship split stays as spec §11 has it.

`★ Insight ─────────────────────────────────────`
- **Why the new code can't break the guarantee.** In `store.py` the lease only decides *when* another worker may take a job over. The attempt token decides *whether* a write counts. So reconnecting, self-fencing and cleanup can be added without risk, because none of them writes outside the token-checked updates.
- **The worker can't trust exit codes.** The pipeline writes `run.json` only in a `finally` block, so a killed run leaves no record. Exit code 1 means both "checks failed" and "crashed". The worker therefore has to decide what's retryable from what is, or isn't, on disk.
- **The usual cleanup would leak processes.** PySpark's daemon leaves the step's process group, so "kill the process group" would leave its Python workers running. The plan kills the whole process tree instead.
`─────────────────────────────────────────────────`

Things you should know before approving:

- **A database restart can't be recovered today.** The job store keeps one connection forever. After a MySQL restart, the reconciler would fail on every pass until someone restarts it. Milestone 2 adds reconnection, which E2's database-restart cases need.
- **Something to redact in this session's AI log.** Two of my checks printed another project's container names and session name. You may want to remove them when you review the logs.
- **The review isn't finished.** The plan agent's check was still running when I handed this over. I verified its two most concrete points myself (the PySpark process groups and how to redirect Spark's temp folder) and folded both in. If the rest of the review changes anything, I'll tell you and update the plan.

## 146. Assistant — 2026-10-23T11:25:05.952Z

### Tool call: ExitPlanMode

```
{
  "plan": "# Plan: finishing the systems extension (spec §11) in six reviewed milestones\n\nStatus: draft for the author's review. Nothing is implemented until it is approved.\n\n## Context\n\nStages 1–4 are merged into `main` (f058095), and so is the extension's job queue: PR #7 (the job\ntable and fencing), PR #8 (Kafka delivery and the reconciler) and PR #9 (Stage 4). What spec\n§11 still lists as planned:\n- the real pipeline in the worker (today it runs `SimulatedPipeline`);\n- the recovery experiments E1/E2;\n- the Redis result cache;\n- the cache experiment E3;\n- their documentation.\n\nThis plan turns the author's six-point outline into milestones M1–M6, one branch and one PR\neach. Each milestone has:\n- deliverables;\n- acceptance criteria;\n- tests;\n- a statement of how it keeps the guarantee.\n\nFour cross-cutting requirements run through all of them:\n- code provenance for `jobs/`;\n- reproducible dependencies;\n- startup commands;\n- measured memory budgets.\n\nData verification, the privacy-hook fixes and AI-log review stay in separate workstreams.\n\nState observed on 2026-10-23:\n- **Main worktree.** It is on `fix/measure-process-kinds` (97c35f3). That branch is pushed but\n  not merged; it carries the fix for the intermittent `measure` test, which `main`'s README,\n  spec and demo still call open.\n- **Uncommitted W2 work.** The worktree holds uncommitted changes to the privacy hook, its tests\n  and one transcript.\n- **AI-log folders.** There are 68 untracked AI-log folders.\n- **`gh` is not installed.**\n\n**Decided by the author (2026-10-23).**\n- **Worker placement.** The worker, reconciler and submit run natively on the host. MySQL and\n  Kafka (and Redis from M4) run in Compose.\n- **Authorship.** The spec §11 split stays as it is. Claude Code writes M1, M2 and all tooling.\n  The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.\n\n## At a glance\n\n| # | Branch (one PR each) | Written by | Needs | Main deliverable | Done when |\n|---|---|---|---|---|---|\n| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; provenance, `jobs` group, runbook skeleton, peak helper, mutation script | provenance covers `jobs/`; lock adds only; live suite 379; mutations caught |\n| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline in the worker; heartbeats, fencing, timeouts, cleanup, reconnect, CLI | crash, stall, timeout and restart cases end with one accepted, correct result |\n| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, session, batch, collector | a batch meets Part A; no lost job, no second acceptance |\n| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py` | M1 | cache-aside with fallback | contract tests pass; same results with Redis down |\n| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, session, batch, collector | a batch meets Part A |\n| M6 | `docs/extension-report` | Claude drafts, author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |\n\n## Ground rules for every milestone\n\n1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has\n   exactly one, and a job may execute more than once.\n   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it. The existing\n     `INVARIANT_QUERIES` and `JobStore.invariant_violations()` (store.py:127, :481) check it.\n     Together, the first two queries forbid a second accepted attempt for any job.\n   - **Accepting.** Nothing but `JobStore.accept_result` may produce an accepted attempt.\n   - **Cleanup** never touches an accepted attempt's folder.\n   - **The cache** reads accepted runs only and never writes the job table.\n   - **Checking.** `invariant_violations()` must be empty after every test scenario, every\n     worker run and every experiment batch.\n2. **Authorship** (spec §11, \"Stages and authorship\"). Claude Code writes:\n   - the Compose services;\n   - the worker integration;\n   - the CLIs;\n   - the injection and measurement tooling;\n   - their tests.\n\n   The project author writes the cache logic and the experiments (design, predictions,\n   formal sessions, answers), with tutoring. For the author's parts Claude prepares scaffolds\n   (signatures, docstrings, TODOs, contract tests) and reviews, but does not fill them in.\n\n   New files carry an `AI contribution:` line. Experiment documents carry an `Author:` line\n   like `docs/partition-experiment.md:3-5`, reworded for the tutored model.\n3. **Review gates.** Each milestone opens with a findings report; nothing is fixed before the\n   author has read it. Each closes with a stop for review before the PR is merged.\n4. **Git.**\n   - **Isolation.** Each milestone gets its own worktree (`.claude/worktrees/<name>`) from an\n     up-to-date `main`, so the main worktree's W2 changes never enter a milestone branch.\n   - **Staging and merging.** Stage files by explicit path only. Merge with merge commits,\n     never squash or rebase. Every commit ends with the Co-Authored-By trailer.\n   - **AI logs.** Milestone commits contain no AI logs; those go to W3.\n   - **PRs.** Claude pushes the branch; the author opens and merges the PR on GitHub.\n   - **Formal sessions** run on a merged, clean commit whose SHA lands in every record. There\n     are no commits during a session.\n5. **Privacy.** `data/` and the private plan stay out of Git. Memory files,\n   `.git/info/exclude` and app lists are never printed in tool calls. Batch folders live under\n   `data/`.\n6. **Measurement sessions.** While one runs, other sessions only write and review. They wait\n   for an explicit confirmation that it ended, then check that its worktree is unchanged.\n7. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write \"one\n   process\", never \"one core\". Give each experiment a \"not claimed\" list.\n\n## Cross-cutting requirements\n\n**A. Code provenance for `jobs/`.**\n- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob(\"*.py\")` (provenance.py:62),\n  so no record identifies any file in `jobs/`, including `schema/*.sql`. A plain recursive glob\n  would collide on `__init__.py`.\n- **M1 change.** Hash every `*.py` and `*.sql` under `src/etf_risk/` recursively, keyed by\n  package-relative POSIX path. `model.py` keeps its key; new keys look like `jobs/store.py`. Old\n  records stay comparable for the files they cover.\n- **Attempt records (M2 on).** Each attempt writes `attempt.json` with the worker's\n  `code_state()`, and so does every experiment record.\n- **Authorship provenance.** Keep the `AI contribution:` lines. Add an origin table to\n  `job-queue.md`: module → commits (eec1032, e2806bd, cd72957) → PR → tests that verify it.\n\n**B. Reproducible dependencies.**\n- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`\n  (compose.yaml:13; test docstrings) and are not in `uv.lock`.\n- **New groups.** M1 adds a `jobs` group with exactly these pins. M2 adds `psutil==7.2.2` to it;\n  psutil is already locked through `measure`. M4 adds a `cache` group with an exact `redis` pin.\n- **Lock changes.** Every lock change may only add packages. numpy 2.5.4, pandas 2.3.3,\n  pyspark 4.2.0, pyarrow 26.0.0 and psutil 7.2.2 stay unchanged, checked by a lock diff and\n  `uv lock --check`.\n- **Commands.** Documented commands use `--group …` and `uv sync --frozen`.\n- **Images.** Images are pinned by digest. Redis follows the Kafka rule: the newest release at\n  least two weeks old.\n- **Host tools.** Each formal session records host tool versions. Seen 2026-10-23: uv 0.11.16,\n  Java 17.0.10, Docker 28.3.0, Compose v2.38.1, Docker Desktop VM 3.83 GiB.\n- **Out of scope.** The NumPy pin (spec §9, planned) stays out unless approved.\n\n**C. Startup commands.**\n- **Today.** The README has no `docker compose` commands; they live only in compose.yaml\n  comments and test docstrings.\n- **Runbook.** A runbook section in the README (M1 skeleton, filled in by M2, M4 and M6) gives\n  copy-pasteable commands per configuration:\n  - test services;\n  - the E1/E2 stack: MySQL and Kafka in Compose; `init-db`, `create-topic`, worker, reconciler,\n    submit and `status` on the host;\n  - the E3 stack: Redis, the query CLI, the warm query service;\n  - teardown with `down -v`.\n- **Acceptance.** Every milestone that touches the runbook runs its commands exactly as written\n  in a fresh worktree.\n\n**D. Measured memory budgets.** A ledger in spec §11 records component, limit, measured peak,\nmethod, date and commit. Known so far:\n\n| Component | Budget | Measured | Source |\n|---|---|---|---|\n| MySQL container | 512 MiB | 324–398 MiB per full run on fresh containers; 472 after two runs; 511 after ~2 h | spec §11 |\n| Kafka container | 640 MiB (256 MiB heap) | 354–478 MiB; 516 with mutation checks | spec §11 |\n| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB at stride 21 | spec §11 |\n| Native stride-21 pipeline tree | `measure` stop at 4.8 GiB | 1.27 GiB (run of record) and 2.62–2.73 GiB (stride experiment), summed RSS | spec §8, experiments.md |\n| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |\n| Native worker, reconciler, submit | set in M2 | — (M2) | |\n| Warm query service | set in M4 | — (M4/M5) | |\n\n- **What the numbers imply.** Running the worker natively puts only the MySQL and Kafka limits\n  in the VM (1.15 GiB). But a stride-21 job may need about 2.7 GiB on the host, and earlier\n  sessions required at least 3.0 GiB free before each protocol. Hence the job-size choice in\n  M3 Part A.\n- **Container peaks** come from cgroup `memory.peak`, through a new helper (only\n  `docker/run.sh` reads it today).\n- **Native peaks** come from `measure.TreeSampler`.\n- **Batches.** Each recovery batch starts on a fresh MySQL container and records its own peak.\n- **Other containers.** At planning time, another project's containers were running in the same\n  Docker VM. The session helpers' pre-checks therefore count containers outside this Compose\n  project, without printing their names, and require zero before any formal session or budget\n  measurement. They also check that ports 3307, 9094 and 6380 are free.\n- **Exceeded budgets.** A budget that is exceeded stops the session, and budgets change only\n  at review.\n\n## Milestones (numbered as in the outline)\n\nOrder: M1 → M2 → M3 and M1 → M4 → M5, then M6. M4 does not need M2 or M3, because it can use\nthe run of record. Its code can be written while M3's session runs, under ground rule 6.\n\n### M1 — Read the whole project; bring the code up to date\nBranch `feature/extension-baseline` · Author: Claude Code · Prerequisite: the author merges\n`fix/measure-process-kinds` (97c35f3) first, since M2–M5 sample memory with its process kinds.\n\n**Step 1: audit (read-only).** A findings report goes to the author, grouped as below.\n- **Reproducibility and provenance**:\n  - cross-cutting gaps A, B and C;\n  - the 22 mutation checks in the job docs exist only as prose (no script);\n  - the merged worktrees `.claude/worktrees/job-queue` and `job-table` are clean and in `main`,\n    so they can be removed with the author's OK.\n- **Missing operations**:\n  - no entry point in `jobs/`, so the \"submit CLI\" in the §11 diagram does not exist;\n  - logging is never configured;\n  - nothing is timed (`Pass` and `Served` are counts only; no `requeued_at` or history);\n  - `published_at` is cleared by the claim;\n  - a crash before the claim leaves no trace;\n  - Kafka `session.timeout.ms` and `max.poll.interval.ms` are unpinned defaults (45 s, 300 s),\n    while `serve()` runs the pipeline inside its poll loop;\n  - **no reconnect.** `JobStore` keeps one connection for life (store.py:286-292, 526). After\n    a MySQL restart the reconciler fails every pass until it is restarted, and the worker's\n    `serve()` raises after 5 retries. E2's database-restart case could therefore never recover\n    without a manual restart. This is fixed in M2;\n  - **no supervisor.** Nothing restarts a worker whose `serve()` ended (`job-queue.md` \"Known\n    limits\": \"by hand for now\").\n- **Pipeline CLIs**, which matter for M2:\n  - **Exit 1 is ambiguous.** Exit 1 means \"checks failed\" (spark_pipeline) or \"mismatch\"\n    (verify), but also any uncaught exception. For spark_pipeline that includes exceptions\n    outside its `try`: `mkdir`, building the record, and writing `run.json` in the `finally`.\n  - **Missing records.** `run.json` is written only in the `finally`, so a killed run leaves\n    none.\n  - **verify gaps.** verify's checksum handler misses `JSONDecodeError`, its `spark.stop()` is\n    not in a `finally`, and it never checks the run's status.\n  - **Relative paths.** verify reads `run.json`'s `windows_dir` as stored, so relative paths\n    assume the repository root.\n  - **windows refusal.** windows refuses only when `config.json` exists; README:224 says \"an\n    existing folder\".\n- **Documentation drift**:\n  - `job-table.md`'s claim SQL omits `published_at = NULL` (store.py:334), and its \"apart from\n    `submit`\" sentence omits `mark_published`;\n  - `job-queue.md:90` names tests that start from a confirmed publication, so they do not cover\n    the job-9 timeline;\n  - the status blocks of job-table.md:97-103 and job-queue.md:146-160 predate the merges;\n  - spec §5's diagram omits `jobs/` and Compose yet says \"Every box is implemented\", and its node\n    ids E2–E4 clash with §11's E1–E3;\n  - spec.md has no AI header, although README:321-323 says AI-drafted files do.\n- **Test helpers**: `WorkerEnv.check` (tests/jobs_backends.py:200) is tied to the simulated\n  pipeline's `result.json`.\n\n**Step 2: fixes, after approval.**\n- provenance (A);\n- the `jobs` group, the lock, and `--with` → `--group jobs` everywhere (B);\n- the runbook skeleton (C);\n- the `memory.peak` helper (D);\n- a reproducible mutation-check script (each mutation a patch, applied in a scratch worktree\n  with a timeout). The original 22 survive only as counts and partial descriptions\n  (job-table.md:98-102, job-queue.md:157-164, e2806bd's message), so the script's list is\n  rebuilt from those descriptions and documented as such, not claimed identical;\n- job-doc drift and stale status text; the module origin table;\n- the CLI fixes, if the author agrees:\n  - uncaught exceptions exit 2, matching spark_pipeline's docstring, so exit 1 always means\n    checks failed or a mismatch;\n  - verify catches `JSONDecodeError`;\n  - verify stops Spark in a `finally`.\n\n  These change no result, and they need tests.\n- removal of the merged worktrees, with the author's OK.\n\n**Step 3: revalidation.**\n- the offline suite;\n- the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with `--group jobs`;\n- the mutation script;\n- MySQL and Kafka peaks read through the helper.\n\n**Deliverables.** The findings report; the fixes above.\n\n**Acceptance.**\n- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in\n  `source_sha256` under a unique key, with the top-level keys unchanged.\n- `uv lock --check` passes, and the lock diff only adds the `jobs` group's packages.\n- The live suite passes with the case count of e2806bd (379), or the difference is explained.\n- Every mutation in the rebuilt list makes a test fail within its timeout.\n- Peaks stay within budget.\n- No file outside the approved scope changes.\n\n**Tests.** New cases in `test_provenance.py`; CLI exit-code tests (Spark-marked where needed);\njob suites on SQLite and live; the mutation script.\n\n**Guarantee.** No change to `store.py`'s SQL. The mutation script re-proves that breaking a guard\nfails a test.\n\n### M2 — The worker runs windows → spark_pipeline → verify\nBranch `feature/worker-pipeline` · Author: Claude Code (spec §11) · Depends on M1.\n\n**Design.** The new code is `jobs/pipeline.py`, `jobs/launcher.py`, `jobs/params.py`,\n`jobs/events.py` and `jobs/__main__.py`, plus small changes to `worker.py` and `kafka.py`. The\nstore's guards stay as they are.\n\n**Job parameters (`params.py`).**\n- **Schema.** A frozen dataclass: snapshot, kind (`rolling` / `calendar-year` / `full-period`),\n  window days, stride, anchor, sample ticker. Unknown keys are refused. Tickers come from the\n  snapshot, and leverages are fixed at 1x and 2x. The processed-data root and the output root\n  are worker settings, not job parameters; the checksums tie a job to its data.\n- **Input checksums.** `submit` computes `input_checksums` from the files that `windows.py`\n  records in `inputs_sha256`: `daily_returns/*.parquet` and `quality_report.json`.\n- **Check before running.** The worker re-checks them before step 1. A mismatch fails the attempt\n  as not retryable.\n\n**Steps.** Each step runs as `sys.executable -m etf_risk.<module>` with absolute paths only.\nEverything lands inside the attempt folder:\n1. `windows --out-root <run_dir>/windows --name <name>` writes\n   `<run_dir>/windows/<snapshot>/<name>/`.\n2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>` writes\n   `<run_dir>/output/<snapshot>/<name>/<run id>/`.\n3. `verify --run …` checks that output.\n\nSetup for every step:\n- the working directory, `TMPDIR` and `SPARK_LOCAL_DIRS` point to `<run_dir>/.work`;\n- `java.io.tmpdir` is set through `PYSPARK_SUBMIT_ARGS=\"--driver-java-options\n  -Djava.io.tmpdir=<run_dir>/.work/tmp pyspark-shell\"`, which PySpark reads when it starts the\n  JVM (`pyspark/java_gateway.py:72`). It is not set through `JAVA_TOOL_OPTIONS`: its \"Picked\n  up …\" notice would replace the Java version that `environment()` records in `run.json`\n  (spark_pipeline.py:635-636);\n- logs go to `<run_dir>/logs/<step>.log`.\n\n**Result rule.**\n- **When the worker accepts.** Every step exits 0, `run.json` has status `ok`, every\n  `checks.json` count is 0, `verify.json` has no mismatch and the same breached windows, and\n  every table has `_SUCCESS`.\n- **Then.** `.work` is removed, `attempt.json` is written, and the worker calls `accept_result`.\n- **After acceptance.** Nothing in the folder changes. The cache relies on this (\"run outputs\n  never change\", spec §11), and a test checks the folder's file checksums before and after.\n\n**Failure classification.** This is decided from the records, not the exit code alone.\n- **Not retryable:**\n  - a checksum error (exit 3);\n  - `run.json` status `checks_failed`;\n  - a verify mismatch;\n  - a parameter or input-checksum error.\n- **Retryable:**\n  - a signal;\n  - a timeout;\n  - status `failed`;\n  - a missing record.\n\nRetryable failures go back to the queue until `max_attempts` (3).\n\n**Heartbeats.**\n- **Where.** The worker thread waits on the child with `wait(timeout=…)` and calls `heartbeat()`\n  every lease/4 (15 s at the 60 s default). There is no background thread, so the database\n  connection stays on one thread.\n- **Failed renewals.** A renewal that raises (database unreachable) is retried at the next tick.\n  When the time since the last successful renewal reaches the lease minus a margin, the worker\n  fences itself: it kills the run and raises `Fenced`. Two Spark runs on one machine would risk\n  memory, and the token guard still decides acceptance.\n\n**Fencing.** When `heartbeat()` returns false, the worker terminates the step's whole process\ntree and raises `Fenced`. The folder stays and is never referenced.\n\nHow the tree is terminated:\n- **Why not a group kill.** Killing the process group is not enough: PySpark's daemon calls\n  `os.setpgid(0, 0)` (`.venv/…/pyspark/daemon.py:115`), so its Python workers leave the step's\n  group.\n- **The tree kill.** Every kill enumerates the descendants with psutil, sends SIGTERM to all,\n  waits a grace period, sends SIGKILL to any survivors, and then checks that none remain.\n- **Dependency.** psutil 7.2.2, already locked, joins the `jobs` group.\n\n**Timeouts.**\n- **Limits.** Each step and the whole attempt get a wall-clock limit. The drafts, fixed at review\n  from M2's measurements:\n\n  | Limit | Draft | Measured so far |\n  |---|---|---|\n  | windows | 120 s | a few seconds |\n  | spark_pipeline | 600 s | 18–47 s at stride 21 |\n  | verify | 300 s | about 14 s |\n  | whole attempt | 900 s | — |\n- **On timeout.** The process tree is killed and the attempt fails as retryable.\n- **Kafka settings.** `max.poll.interval.ms` (above the attempt limit) and `session.timeout.ms`\n  are set in `kafka.py` and pinned by tests.\n  - **Why the poll limit matters.** `serve()` does not poll while a pipeline runs. If a run\n    outlasted the poll limit, librdkafka would leave the group, and a standby worker in the same\n    group could take the partition and start a second Spark run on this machine. The offset is\n    committed before the run, so the job itself is not redelivered.\n  - **Confirmation.** M2's live tests confirm this behaviour, and the stalled-worker case relies\n    on it: a SIGSTOPped consumer misses its session timeout, and the standby takes over.\n\n**Cleanup.**\n- **Lifeline.** Each step starts behind `launcher.py`, which holds a \"lifeline\" pipe from the\n  worker. If the worker dies, even by SIGKILL, the launcher reads EOF and kills its descendant\n  tree in the same way as fencing. macOS has no parent-death signal.\n- **Stale trees.** Each attempt writes the launcher's pid and start time to `.work/launcher.json`.\n  On startup, a worker kills the trees that a previous worker left unfinished. The start time\n  guards against a reused pid.\n- **`jobs cleanup`** is a dry run unless given `--delete`. It removes folders of failed or expired\n  attempts that ended more than a grace period ago. Folders with no attempt row are only\n  reported. It never touches accepted or running attempts.\n\n**Database reconnect.** The guards and SQL stay unchanged.\n- **Factory.** `JobStore` accepts a connection factory, for MySQL `connect_mysql` with its\n  session settings.\n- **Detecting a lost connection.** On a PyMySQL disconnect error, the store drops the\n  connection. The disconnect errors are 2003, 2006 and 2013, and `InterfaceError`; this is a new\n  `Dialect.is_disconnect`.\n- **Next operation.** It opens a fresh connection.\n- **No replay.** The failed operation is not replayed: it raises, as today, because a failed\n  COMMIT may have taken effect.\n\nThe worker and reconciler then rely on existing semantics:\n- a renewal is tried again at the next heartbeat;\n- `accept_result` is retried within the lease, and is idempotent for the token that won;\n- a lost claim is taken over after its lease.\n\n**Supervision.**\n- **In-process restarts.** `jobs worker` restarts its serve loop in-process after an error, with\n  backoff, and recreates the consumer.\n- **Harness restarts.** A SIGKILLed worker is restarted by the session harness after a delay set\n  in M3 Part A, standing in for a process supervisor.\n- **Reconciler.** It keeps running through outages, with failed passes logged.\n\n**Graceful stop.** On SIGTERM or SIGINT the worker stops polling, kills the running step and\ncalls `fail_attempt(retryable=True)`, so the job is requeued at once. This uses one of the\njob's `max_attempts`, which E2's repetitions must allow for.\n\n**Event log (`events.py`).** Each process appends JSON lines with UTC times, one flushed line per\nevent:\n- delivered\n- claimed\n- renewed and renewal failed\n- step start and end\n- fenced\n- accepted\n- failed\n- requeued\n- published\n\nE2's timings come from these logs plus the tables, without a new table.\n\n**CLI** `python -m etf_risk.jobs`:\n- `init-db`\n- `create-topic`\n- `submit`\n- `worker`\n- `reconciler`\n- `cleanup`\n- `status [--check]`, which prints the tables and `invariant_violations()` and exits 1 on a\n  violation\n\nFlags or `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP` configure it, and logging is set up.\n\n**Attempt record.** `attempt.json` holds the worker id, run id, steps (exit code, times), the\ninput checksums as checked and `code_state()`.\n\n**Optional defense in depth.** A unique index on accepted attempts per job: a partial index in\nSQLite, and in MySQL a unique index on a generated column that is `job_id` only when the\noutcome is accepted. The schema-drift test is updated, and a test shows that a second accepted\nrow is refused.\n\n**Deliverables.** The modules above; updated `job-queue.md` (real pipeline, settings table,\nknown limits resolved); the runbook's E1/E2 section; budget rows for the worker, reconciler and\nsubmit.\n\n**Acceptance.** Native worker, MySQL and Kafka in Compose, on fresh containers:\n- **Normal runs.** A calendar-year job and a stride-21 job of `full-2026-10-12` each end\n  `succeeded`, with exactly one accepted attempt that passes every check and verify. Their\n  content equals a direct CLI run under the `compare_tables` rules\n  (analysis/collect_partition_measurements.py:286, partition-experiment.md:476-515).\n- **Stalled worker.** After SIGSTOP for longer than the lease, a standby worker takes over. On\n  SIGCONT the stalled worker's process tree is gone within the grace period, it writes nothing\n  more, and the takeover's result is accepted.\n- **Crashed worker.** After SIGKILL during step 2, no Spark process is left once the lifeline\n  grace has passed, and the job is requeued after its lease and succeeds.\n- **Timeout.** An attempt that exceeds its limit is killed and retried.\n- **Service restarts.** `docker compose restart mysql` and, separately, `restart kafka`, each\n  during a run: neither the worker nor the reconciler has to be restarted by hand, and the job\n  ends with one accepted result.\n- **Temp files.** No new `spark-*` or `blockmgr-*` folder appears in `/tmp` or `$TMPDIR`.\n- **Cleanup dry run.** It lists exactly the failed and expired attempts.\n- **Peaks.** Measured and within budget.\n- **Invariants.** `invariant_violations()` is empty throughout.\n- **Earlier tests.** Every earlier job test still passes on both stores.\n\n**Tests.**\n- **`test_jobs_pipeline.py`** (offline, with fake step scripts): heartbeat cadence; fencing kills\n  the whole tree, including a grandchild that moved to its own process group as PySpark's\n  daemon does (checked with psutil); timeouts; failure classification; the lifeline (kill the\n  parent, the grandchild dies); `.work` cleanup; parameter and checksum refusals.\n- **CLI and cleanup tests.**\n- **Reconnect tests:**\n  - offline: a connection wrapper that raises a disconnect error once; the next operation\n    reconnects, and the failed one is not replayed;\n  - live: `KILL CONNECTION` from a second session, and a container restart.\n- **A Spark-marked end-to-end test:** a tiny job through `Worker` with SQLite and `MemoryQueue`,\n  on a synthetic snapshot from `tests/conftest.py`'s `write_snapshot` (passed with\n  `--processed-root`). The steps start their own Spark processes, not the shared fixture\n  session.\n- **A live end-to-end test** gated by the environment variables: real worker and reconciler\n  processes, SIGKILL mid-run, recovery, then `status --check`.\n\n**Guarantee.** Acceptance still goes only through the token guard. Fencing and self-fencing\nonly stop work. Cleanup excludes accepted attempts. The optional index makes a second accepted\nrow impossible at the storage level.\n\n### M3 — Recovery experiments E1 and E2\nBranch `feature/recovery-experiment` · Tooling: Claude Code · Experiment: the project author,\ntutored · Depends on M2.\n\n**Claude's tooling (first commit, with tests).**\n- **Crash injection.** Crashes at the existing worker fault points (`Worker(fault=…)`,\n  worker.py:112), chosen by an environment variable and carried out as a real SIGKILL.\n- **Outside injections.** SIGKILL during a step; SIGSTOP and SIGCONT; `docker compose restart\n  kafka` or `mysql` at a chosen phase.\n- **Harness log.** It records each injection and the time each service was ready again.\n- **Session helpers.** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:\n  two windows, machine checks, `case n`, a watcher, abort and note, and no commits during the\n  session.\n- **Collector.** `analysis/collect_recovery_measurements.py --batch <folder>` imports\n  `compare_tables` unchanged, as later collectors do. It merges the tables, event logs and\n  harness log and writes `measurements.csv` and `acceptance.json` (criteria 1–5 as before, plus\n  \"6 guarantee\"). It exits 1 on any failed criterion.\n- **Batches** live in `data/outputs-recovery/<batch>/`.\n- **Reference runs.** Before each batch, the harness makes a reference run per job parameter set\n  with direct CLI calls on the same commit, not through the worker. The collector compares every\n  accepted run with it.\n- **Clock.** All times come from the host clock in UTC. The store passes times as parameters, and\n  MySQL's clock is never used, so the harness log, event logs and tables share one clock.\n\n**The author's `docs/recovery-experiment.md`.** Claude scaffolds the headings of Parts A and B\n(sections 1–15 and History) and the `Author:` line.\n- **Part A, decided by the author:**\n  - the cases;\n  - repetitions;\n  - lease, heartbeat and reconcile settings;\n  - the job size (calendar-year vs stride 21, with the memory implications in D);\n  - metric definitions;\n  - predictions;\n  - acceptance criteria;\n  - stop rules;\n  - one fresh MySQL container per batch.\n- **Draft cases offered:**\n  - worker crash before the claim;\n  - crash after the claim but before the acknowledgement (the job-9 timeline);\n  - crash during step 2;\n  - crash after the pipeline but before acceptance;\n  - crash after acceptance;\n  - a stalled worker taken over, then fenced;\n  - Kafka restart while idle, during a submit, and during a run;\n  - MySQL restart during a run, shorter and longer than the lease;\n  - MySQL restart at acceptance (the failed-COMMIT path).\n- **Metrics per job:**\n  - injection time;\n  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;\n  - recovery: the next `claimed_at`;\n  - completion: `finished_at`;\n  - executions;\n  - accepted results (0 or 1);\n  - correctness: every check passed, and the content equals the reference;\n  - lost: not terminal by the deadline. A draft deadline, for Part A to fix, is lease +\n    reconcile interval + publication grace + (attempts left × attempt limit) + margin.\n- **Attempts.** `submit --max-attempts` lets Part A give experiment jobs enough attempts for\n  cases with repeated failures. A job that runs out fails; it is not lost, and it still keeps\n  the guarantee.\n- **E1 cross-check.** The author writes their own SQL for accepted results per job, which must\n  agree with `invariant_violations()`.\n\n**Acceptance.**\n- One batch meets every Part A criterion.\n- Across all batches: zero lost jobs and zero jobs with two accepted results; every succeeded\n  job has exactly one correct accepted result.\n- Peaks are recorded per batch.\n- The commit sequence follows the precedent: tooling, Part A (before any measured run), dry\n  batches and the formal session, Part B, status.\n\n**Tests.** Collector and helper tests in the style of `test_caching_collector.py` and\n`test_caching_session.py`, including planted problems that each fail their criterion; tests of\nthe injection tools.\n\n**Guarantee.** This milestone measures it under failures and adds no write path.\n\n### M4 — Redis cache for summary queries, with fallback\nBranch `feature/result-cache` · Infrastructure: Claude Code · Cache logic: the project author,\ntutored · Depends on M1.\n\n**Claude's part.**\n- **Compose service `redis`:**\n  - pinned by digest;\n  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, with persistence off;\n  - `mem_limit` and `memswap_limit` 128m;\n  - port `127.0.0.1:6380`;\n  - a `redis-cli ping` healthcheck.\n- **Dependencies.** A `cache` group with an exact `redis` pin.\n- **`src/etf_risk/summary.py`.**\n  - Named queries over a run's `paired/`. Their SQL comes from the author's `analysis/sql_*.py`\n    without editing those scripts, since documents cite earlier scripts by hash. The author moves\n    their own SQL text in; Claude wires it up.\n  - A one-shot CLI, which is the new-process mode.\n  - A warm mode: one SparkSession answering JSON-lines requests on stdin and stdout.\n  - An accepted-run resolver: `--job N` maps to the accepted attempt's folder, never any\n    other.\n- **Contract tests and fakes:**\n  - an in-memory Redis stand-in that can go \"down\";\n  - a live fixture gated by `ETF_RISK_REDIS_URL`;\n  - fallback and equal-result tests;\n  - a Spark-marked test that summary queries on the run of record reproduce the values in spec\n    §8 (for example, windows 529, 466, 311, 174 and 310), skipped when `data/` is absent.\n\n**The author's part.** `src/etf_risk/cache.py`, scaffolded:\n- the key: run id + normalized query + a format version;\n- serialization;\n- cache-aside get-or-compute;\n- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while\n  Redis is down, and decode errors treated as misses;\n- counters for hits, misses and fallbacks.\n\n**Acceptance.**\n- The contract tests pass offline and live.\n- With Redis stopped, every query returns the same result as Spark, and its added latency stays\n  within the timeout and breaker bounds.\n- Redis's peak stays within 128 MiB.\n- The runbook's E3 commands work as written.\n\n**Tests.**\n- Contract tests (Claude) that the author's `cache.py` must pass: key determinism and\n  separation (different runs or queries never share a key); equal results from the cache and\n  from Spark; fallback while \"down\"; a bounded fallback cost; decode errors treated as misses.\n- The resolver refuses non-accepted runs.\n- Live tests against the Compose Redis.\n- The Spark-marked spec §8 test.\n\n**Guarantee.** The cache reads only accepted runs and never writes the job table.\n\n### M5 — E3: new Spark process vs warm Spark session vs Redis\nBranch `feature/result-cache-experiment` · Tooling: Claude Code · Experiment: the project\nauthor, tutored · Depends on M4.\n\n**Configurations** (decided in Part A):\n- N: a new process per query.\n- W: a warm session with the cache off.\n- R: a warm session plus Redis, at hit rates set by the workload's repeats (for example 0, 50\n  and 90%). Three unparameterized queries on one run give only three keys. The key space\n  therefore comes from queries × accepted runs (the run of record and M2/M3 job runs), × any\n  parameter the author adds in M4, such as a ticker.\n- F: Redis stopped, measuring latency and correctness, then recovery after a restart.\n\n**Measures:**\n- client-side per-query latency on a monotonic clock (medians and spread);\n- realized vs designed hit rate;\n- the warm session's process-tree peak;\n- Redis `memory.peak` and `used_memory_peak`.\n\n**Deliverables:**\n- `docs/result-cache-experiment.md` (Parts A and B, `Author:` line);\n- `docs/result-cache-session.zsh`;\n- `analysis/collect_result_cache_measurements.py` (named apart from the existing caching\n  collector);\n- a batch in `data/outputs-result-cache/<batch>/`.\n\n**Acceptance.** As in earlier experiments: one batch meets every criterion, and drift beyond the\nstated tolerance is reported.\n\n**Tests.** Collector tests with planted problems, each failing its criterion, and session-helper\ntests, both in the pattern of `test_caching_collector.py` and `test_caching_session.py`; a test\nthat the workload generator gives the designed hit rate.\n\n**Guarantee.** Read-only for the job table; it queries accepted runs only.\n\n### M6 — Architecture, report and demo\nBranch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · Depends\non M3 and M5.\n\n- **`docs/architecture.md`** (new). It covers:\n  - the batch pipeline and the extension;\n  - native vs Compose placement;\n  - the failure model and the guarantee;\n  - the budget ledger;\n  - the runbook.\n\n  Spec §5's diagram gains `jobs/` and Compose, and its node ids are renamed so they no longer\n  clash with §11's E1–E3. The planned \"design decisions\" item in spec §9 moves here.\n- **Figures X5 (E1/E2) and X6 (E3)**, added together, as X1–X4 were in Stage 4:\n  - in `plots.py`: `FIGURES`, `DOCUMENTED`, and the literal tuple in `compare_documented`;\n  - `test_plots.py`'s figure count (12 → 14);\n  - CSV copies in `docs/measurements/` with their README rows;\n  - every \"twelve figures\" and \"X1–X4\" mention in README, spec, results, demo, measurements\n    README and plots.py.\n- **Spec.** §8 gains \"What the recovery experiments showed\" and \"What the result-cache\n  experiment showed\". §9 and §11 move to implemented, with the final ledger.\n- **`results.md`.** A new section on the extension. The approved §7 changes only with the\n  author's re-approval.\n- **README.** The Status row and the full runbook.\n- **`demo.md`.** A new part: submit; kill the worker mid-run; watch `status --check` recover;\n  cache miss → hit → Redis stopped → fallback → restart.\n\n**Acceptance.**\n- Every number traces to a committed CSV or record, and `plots --check` passes.\n- Every demo and runbook command has been run as written in a fresh worktree.\n- Links are valid.\n- The author has approved the conclusions.\n\n**Tests.** `test_plots.py` updated for 14 figures and the X5/X6 checks; `plots --check`; a link\ncheck over `docs/`; the full offline suite.\n\n**Guarantee.** Documentation only. The architecture page states the guarantee and where it is\nenforced and checked.\n\n## Separate workstreams (outside M1–M6)\n\nNo milestone branch touches these files, and none waits on them.\n\n- **W1 Data verification** (`feature/data-verification`, own plan):\n  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);\n  - the terms-of-use review;\n  - the cause of the Adj Close steps;\n  - the 36 unverified days;\n  - data-sources.md's missing AI header.\n\n  The extension claims nothing about the analysis results.\n- **W2 Privacy-hook fixes** (`fix/transcript-privacy`):\n  - the uncommitted edits to `.claude/hooks/transcript_privacy.py`,\n    `tests/test_transcript_privacy.py` and one transcript;\n  - the spec §10 hook items: the separator rule, save timing, folders for interruption notices.\n\n  Claude changes the hook only when asked.\n- **W3 AI-log review** (`docs/ai-logs-<date>` branches):\n  - the 68 untracked folders, including the sessions behind PRs #7–#9;\n  - each milestone's logs;\n  - `docs/ai-usage/README.md`'s inconsistencies: it says logs are committed \"alongside the\n    related code\" although they get separate commits, and it credits the hook to Codex only.\n\n  The author reviews; commits are named \"Add reviewed AI logs for …\"; logs are never mixed with\n  code.\n\n## Verification (end to end)\n\n- **Per milestone:**\n  - the offline suite (`uv run --group measure --group plots pytest`), with counts recorded;\n  - the Spark-marked tests;\n  - the live suites on fresh containers (`--group jobs`, and `--group cache` from M4);\n  - `status --check` empty after every live run;\n  - the mutation script (from M1);\n  - the lock diff.\n- **System:** in a fresh worktree on `main` after M6, follow the runbook from `uv sync --frozen`\n  through E1/E2 and E3 smoke runs. Check that:\n  - every accepted run passes its checks and matches its reference by content;\n  - `plots --check` passes;\n  - container peaks are within the ledger.\n\n## Decisions left to review gates\n\n- **M1:** the CLI exit-code fixes; removing the merged worktrees.\n- **M2:** lease, heartbeat and timeout values; whether to add the unique index.\n- **M3 Part A:** cases, job size and repetitions.\n- **M4:** key and serialization (the author).\n- **M5 Part A:** hit rates and workload.\n- **M6:** wording of the extension section in `results.md`.\n",
  "planFilePath": "~/.claude/plans/please-turn-this-outline-cozy-candy.md"
}
```

## 147. User — 2026-10-23T11:40:14.366Z

### Tool result (error)

```
The user doesn't want to proceed with this tool use. The tool use was rejected (eg. if it was a file edit, the new_string was NOT written to the file). The user provided the following reason for the rejection:  1. A SIGSTOPped worker cannot run heartbeat checks, and its lifeline remains open. Define an independent watchdog or host-level execution lock that prevents replacement Spark work from overlapping a surviving old process tree. Test this before SIGCONT. Startup cleanup must also preserve valid active attempts.
2. Define bounded database connection, read/write and lock-wait timeouts, including retries. Show that blocking operations cannot defeat the self-fencing deadline. Use monotonic time for local deadlines.
3. Strengthen cache identity beyond run_id, since IDs can repeat after database recreation. Include immutable run identity and the full query parameters. Explain how M4 can use the historical run of record while enforcing its accepted-run policy.

Keep the six milestones. After approval, proceed autonomously with routine work inside each milestone; pause for material design changes, authorship decisions and formal experiment approval.
```

## 148. Assistant — 2026-10-23T11:47:28.214Z

### Tool call: Bash

```
{
  "command": "sed -n '321,420p' src/etf_risk/jobs/store.py",
  "description": "Show the store's claim, renew and accept operations"
}
```

## 149. User — 2026-10-23T11:47:28.660Z

### Tool result

```
    @_retry_conflicts
    def claim(self, job_id: int, worker_id: str, output_root: str | Path) -> Claim | Refusal:
        """Start a new attempt of the job, or say why the delivery needs nothing more.

        One transaction: take the job (from queued, or over an expired lease), mark the
        attempt that held the expired lease as expired, and insert the new attempt. The token
        is generated here, before the claim; it is the attempt's identity in every later guard."""
        now = self.clock.now()
        token = secrets.token_hex(16)
        take = dict(job_id=job_id, token=token, lease_expires_at=self._time(now + self.lease), now=self._time(now))
        with self._transaction():
            if self._execute(
                    "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1,"
                    " attempt_token = :token, lease_expires_at = :lease_expires_at, published_at = NULL,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'queued'", **take).rowcount:
                takeover = False
            elif self._execute(
                    "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1,"
                    " attempt_token = :token, lease_expires_at = :lease_expires_at, published_at = NULL,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND lease_expires_at <= :now"
                    " AND attempt_number < max_attempts", **take).rowcount:
                takeover = True
            else:
                return self._refusal(job_id, now)
            self._fault("claim.jobs_updated")
            job = self._fetch_one("SELECT attempt_number, max_attempts, params, input_checksums FROM jobs"
                                  " WHERE job_id = :job_id", job_id=job_id)
            n = job["attempt_number"]
            if takeover:
                self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_number = :previous AND outcome = 'running'",
                                job_id=job_id, previous=n - 1, now=take["now"])
                self._fault("claim.previous_attempt_expired")
            claim = Claim(job_id, n, token, run_id(job_id, n), Path(output_root) / run_id(job_id, n),
                          job["max_attempts"], json.loads(job["params"]), json.loads(job["input_checksums"]))
            self._execute(
                "INSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id, output_dir,"
                " outcome, claimed_at, lease_expires_at, renewals)"
                " VALUES (:job_id, :attempt_number, :token, :worker_id, :run_id, :output_dir,"
                " 'running', :now, :lease_expires_at, 0)",
                job_id=job_id, attempt_number=n, token=token, worker_id=worker_id, run_id=claim.run_id,
                output_dir=str(claim.output_dir), now=take["now"], lease_expires_at=take["lease_expires_at"])
            return claim

    @_retry_conflicts
    def renew(self, claim: Claim) -> bool:
        """Extend the attempt's lease from now. False: the worker has been fenced off and must stop."""
        now = self.clock.now()
        lease_expires_at = self._time(now + self.lease)
        with self._transaction():
            if not self._execute(
                    "UPDATE jobs SET lease_expires_at = :lease_expires_at, version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
                    job_id=claim.job_id, token=claim.token, lease_expires_at=lease_expires_at,
                    now=self._time(now)).rowcount:
                return False
            self._fault("renew.jobs_updated")
            self._write_one("UPDATE job_attempts SET lease_expires_at = :lease_expires_at, renewals = renewals + 1"
                            " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                            job_id=claim.job_id, attempt_number=claim.attempt_number,
                            lease_expires_at=lease_expires_at)
            return True

    @_retry_conflicts
    def accept_result(self, claim: Claim) -> bool:
        """Accept this attempt's result. True if it is the job's accepted result, now or
        already (a repeat after a failed COMMIT that took effect); False: fenced off."""
        now = self._time(self.clock.now())
        with self._transaction():
            if self._execute(
                    "UPDATE jobs SET status = 'succeeded', accepted_attempt = :attempt_number,"
                    " attempt_token = NULL, lease_expires_at = NULL, finished_at = :now,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
                    job_id=claim.job_id, token=claim.token, attempt_number=claim.attempt_number,
                    now=now).rowcount:
                self._fault("accept_result.jobs_updated")
                self._write_one("UPDATE job_attempts SET outcome = 'accepted', ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                                job_id=claim.job_id, attempt_number=claim.attempt_number, now=now)
                return True
            return self._fetch_one(
                "SELECT 1 FROM jobs j JOIN job_attempts a"
                " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt"
                " WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token",
                job_id=claim.job_id, token=claim.token) is not None

    @_retry_conflicts
    def fail_attempt(self, claim: Claim, error: str, *, retryable: bool) -> Status | None:
        """End the attempt as failed. The job returns to queued if the error is retryable and
        attempts are left, and fails otherwise; returns its new status, or None when the worker
        was fenced off. Back in queued, the job is not delivered again by this (see etf_risk.jobs)."""
        now = self._time(self.clock.now())
        requeue = retryable and claim.attempt_number < claim.max_attempts
        status = Status.QUEUED if requeue else Status.FAILED
        with self._transaction():
            if not self._execute(
                    "UPDATE jobs SET status = :status, attempt_token = NULL, lease_expires_at = NULL,"
```

## 150. Assistant — 2026-10-23T11:50:01.234Z

### Tool call: Write

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "content": "# Plan: finishing the systems extension (spec §11) in six reviewed milestones\n\nStatus: revision 2, after the author's review on 2026-10-23 and a design check against the code\nand libraries. Nothing is implemented until it is approved.\n\n## Context\n\nStages 1–4 and the extension's job queue are merged into `main` (f058095): PR #7 (job table,\nfencing), PR #8 (Kafka delivery, reconciler), PR #9 (Stage 4). Spec §11 still lists as planned:\n- the real pipeline in the worker (today `SimulatedPipeline`);\n- the recovery experiments E1/E2;\n- the Redis result cache;\n- the cache experiment E3;\n- their documentation.\n\nThis plan turns the author's six-point outline into milestones M1–M6, one branch and PR each. Each\nmilestone has deliverables, acceptance criteria, tests and a statement of how it keeps the\nguarantee. Four cross-cutting requirements run through all of them: code provenance for `jobs/`,\nreproducible dependencies, startup commands, and measured memory budgets. Data verification, the\nprivacy-hook fixes and AI-log review stay in separate workstreams.\n\nState observed on 2026-10-23:\n- the main worktree is on `fix/measure-process-kinds` (97c35f3, pushed, not merged), with\n  uncommitted privacy-hook work (W2);\n- 68 untracked AI-log folders exist;\n- another project's containers share the Docker VM;\n- `gh` is not installed.\n\n## Decisions and working mode (the author, 2026-10-23)\n\n- **Placement.** The worker, reconciler and submit run natively on the host. MySQL and Kafka (and\n  Redis from M4) run in Compose.\n- **Authorship.** The spec §11 split stays.\n  - Claude Code writes M1, M2 and all tooling.\n  - The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.\n- **Six milestones**, as in the outline.\n- **Working mode after approval.** Claude proceeds autonomously with routine work inside each\n  milestone: code, tests, docs, dry runs and commits on the milestone branch.\n- **When Claude pauses and asks.**\n  - **Material design changes:** anything this plan does not describe; any change to the store's\n    guards or SQL beyond the two additive changes in M2.1; any change to the time inequality in\n    M2.4.\n  - **Authorship decisions.**\n  - **Formal experiment approval:** Part A sign-off, and the author running the formal session.\n- **Push and merge.** The author pushes, or tells Claude to push, and opens and merges each PR.\n- **Reports.** Every milestone ends with a report: what was done, what was found and fixed, test\n  counts and measured peaks.\n\n## At a glance\n\n| # | Branch | Written by | Needs | Main deliverable | Done when |\n|---|---|---|---|---|---|\n| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; recursive provenance; `jobs` group; runbook skeleton; peak helper; mutation script | provenance covers `jobs/`; lock only adds; live suite 379 or explained; mutations caught |\n| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline; renewals with monotonic deadlines; watchdog and host lock; tree cleanup; reconnect; store identity; result digest; CLI | crash, stall, timeout and restart cases end with one accepted, correct, digest-bound result and no overlapping Spark trees |\n| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, harness, collector, batch | Part A met; no lost job; no second acceptance |\n| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py`, `runs.py` | M2 | cache-aside keyed by run digest and full query; accepted-run policy; fallback | contract tests pass; same results with Redis down; the run of record is usable through the reviewed registry |\n| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, harness, collector, batch | Part A met |\n| M6 | `docs/extension-report` | Claude drafts; author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |\n\nM4's code can be written while M3's formal session runs (ground rule 6); it does not touch M3's\nfiles.\n\n## Ground rules for every milestone\n\n1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has\n   exactly one, and a job may execute more than once.\n   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it.\n   - **Checking.** `INVARIANT_QUERIES` / `invariant_violations()` (store.py:127, :481) check it\n     after every test scenario, every worker run and every experiment batch.\n   - **Accepting.** Nothing but `JobStore.accept_result` produces an accepted attempt.\n   - **No reconnect inside a transaction** (M2.8). It could break the guarantee: the rest of a\n     transaction would commit statement by statement.\n   - **Cleanup** never touches an accepted or valid active attempt.\n   - **The cache** serves accepted runs only and never writes the job table.\n   - **No overlap.** No replacement Spark work overlaps a surviving earlier process tree (M2.5).\n2. **Authorship.**\n   - For the author's parts, Claude prepares scaffolds (signatures, docstrings, TODOs, contract\n     tests) and reviews, but does not fill them in.\n   - New files carry an `AI contribution:` line.\n   - Experiment documents carry an `Author:` line saying the author wrote Part A and the answers\n     with tutoring, unlike earlier experiments where Claude drafted Part A\n     (caching-experiment.md:56).\n3. **Git.**\n   - Each milestone has its own worktree (`.claude/worktrees/<name>`) from up-to-date `main`, with\n     a `data` symlink to the main worktree's `data/`. M1 changes `.gitignore`'s `/data/` to `/data`\n     so the symlink is ignored too.\n   - Stage files by explicit path only.\n   - Merge with merge commits; never squash or rebase.\n   - Commits end with the Co-Authored-By trailer.\n   - Formal sessions run on a merged, clean commit whose SHA lands in every record, with no\n     commits during a session.\n4. **Privacy.** `data/` and the private plan stay out of Git. Never print memory files,\n   `.git/info/exclude`, app lists, or other projects' container or session names in tool calls.\n   Helpers count other containers without naming them. Child processes get an allowlisted\n   environment, so service URLs and passwords never reach the pipeline steps.\n5. **Measurement sessions.** While one runs, other sessions only write and review. They wait for\n   the explicit end, then check that the worktree is unchanged.\n6. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write \"one process\",\n   never \"one core\". Give each experiment a \"not claimed\" list.\n\n## Cross-cutting requirements\n\n**A. Code provenance for `jobs/`.**\n- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob(\"*.py\")` (provenance.py:62).\n  No record identifies `jobs/*.py` or `jobs/schema/*.sql`, and a plain recursive glob would\n  collide on `__init__.py`.\n- **M1.** Hash every `*.py` and `*.sql` under `src/etf_risk/`, keyed by package-relative POSIX\n  path. Top-level keys stay as they are, so old records remain comparable.\n- **From M2.**\n  - `attempt.json` and every experiment record carry `code_state()`.\n  - Each accepted result is bound to its run digest in the job table (M2.1).\n- **Authorship provenance.** An origin table in `job-queue.md` maps each module → commits\n  (eec1032, e2806bd, cd72957) → PR → the tests that verify it. The `AI contribution:` lines stay.\n\n**B. Reproducible dependencies.**\n- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`\n  (docker/compose.yaml:13; test docstrings) and are not in `uv.lock`.\n- **Groups.**\n  - M1 adds a `jobs` group with these pins.\n  - M2 adds `psutil==7.2.2` to that group; it is already locked through `measure`.\n  - M4 adds a `cache` group with an exact `redis` pin.\n- **Lock changes** may only add packages. numpy 2.5.4, pandas 2.3.3, pyspark 4.2.0, pyarrow 26.0.0\n  and psutil 7.2.2 stay unchanged, checked with a lock diff and `uv lock --check`.\n- **Commands** use `--group …` and `uv sync --frozen`.\n- **Images** are pinned by digest. Redis follows the Kafka rule: the newest release at least two\n  weeks old.\n- **Host tools** are recorded with each formal session (2026-10-23: uv 0.11.16, Java 17.0.10,\n  Docker 28.3.0, Compose v2.38.1, VM 3.83 GiB).\n- **Out of scope:** the NumPy pin.\n\n**C. Startup commands.**\n- **Runbook.** A README section (skeleton in M1, filled by M2, M4 and M6) gives copy-pasteable\n  commands for:\n  - **Setup:** the worktree and `data` symlink; the test services.\n  - **The E1/E2 stack:** Compose `mysql kafka`; then `init-db`, `create-topic`, worker,\n    reconciler, submit and `status`.\n  - **The E3 stack:** Compose `redis`, the query CLI and the warm query service.\n  - **Teardown:** export first, then `down -v`.\n- **Readiness.** A service is ready only after a check that matches what will use it:\n  - MySQL: a login plus `SELECT 1` (its healthcheck answers before logins work,\n    docker/compose.yaml:35);\n  - Kafka: the batch topic's metadata and the group coordinator are available;\n  - Redis: `PING`.\n- **Acceptance.** The commands are run exactly as written in a fresh worktree.\n\n**D. Measured memory budgets.** The spec §11 ledger records component, limit, measured peak,\nmethod, date and commit.\n\n| Component | Budget | Measured | Source |\n|---|---|---|---|\n| MySQL container | 512 MiB | 324–398 MiB fresh; 472 after two runs; 511 after ~2 h | spec §11 |\n| Kafka container | 640 MiB | 354–478 MiB; 516 with mutation checks | spec §11 |\n| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB, stride 21 | spec §11 |\n| Native stride-21 tree | `measure` stop 4.8 GiB | 1.27 GiB with 1.3–1.6 GiB free; 2.62–2.73 GiB with 3.0–3.5 GiB free | spec §8, experiments.md |\n| Native calendar-year tree | — | not measured (M2) | |\n| Worker, reconciler, submit | from M2 dry runs | — | |\n| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |\n| Warm query service | from M4 dry runs | — | |\n\n- **Budgets** are set at the review gate from dry runs, then checked; never from the run that\n  checks them.\n- **Container peaks** come from cgroup `memory.peak` through a helper (M1). They are read before\n  every injected restart, since a restart may reset them; M2 verifies whether it does.\n- **Native peaks** come from a marker-based sampler (M2). `TreeSampler` misses processes that were\n  re-parented to launchd.\n- **Before any formal session or budget measurement:**\n  - zero containers outside this project (counted, not named);\n  - ports 3307, 9094 and 6380 free;\n  - host available memory at or above the Part A threshold.\n- **Each recovery batch** starts on a fresh MySQL container with a fresh topic and consumer group.\n- **A budget exceeded** stops the session.\n\n## Milestones (numbered as in the outline)\n\n### M1 — Read the whole project; bring the code up to date\nBranch `feature/extension-baseline` · Claude Code · after `fix/measure-process-kinds` is merged.\n\n**Audit.** The report lists the following. Items inside this plan are fixed as routine work;\nanything else waits for the author.\n- **Reproducibility:**\n  - gaps A, B and C;\n  - the 22 mutation checks exist only as prose;\n  - the merged worktrees `job-queue` and `job-table` are clean, so they can be removed.\n- **Missing operations:**\n  - no entry point in `jobs/` (the §11 \"submit CLI\" does not exist);\n  - logging is never configured;\n  - nothing is timed;\n  - `published_at` is cleared by the claim;\n  - a crash before the claim leaves no trace;\n  - Kafka group timings are unpinned defaults while `serve()` runs the pipeline inside its poll\n    loop;\n  - **no reconnect:** `JobStore` keeps one connection for life (store.py:286-292, 526), so after a\n    MySQL restart the reconciler fails every pass and `serve()` raises after 5 retries;\n  - no supervisor.\n- **Pipeline CLIs** (findings only; the worker works around them in M2.3):\n  - exit 1 means both \"checks failed\" or \"mismatch\" and any uncaught exception;\n  - `run.json` is written only in `finally`;\n  - verify misses `JSONDecodeError`;\n  - verify's `spark.stop()` is not in a `finally`;\n  - paths are relative to the working directory: `--processed-root` and verify's `windows_dir`;\n  - windows refuses only an existing `config.json`, while README:224 says an existing folder.\n- **Documentation drift:**\n  - job-table.md's claim SQL and \"apart from submit\";\n  - job-queue.md:90;\n  - dated status blocks in job-table.md:97-103 and job-queue.md:146-160;\n  - spec §5's diagram, its \"Every box is implemented\", and its E2–E4 node ids;\n  - spec.md has no AI header.\n- **Test helpers:** `WorkerEnv.check` is tied to the simulated `result.json`.\n\n**Fixes:**\n- provenance (A);\n- the `jobs` group and `--group jobs` everywhere (B);\n- `.gitignore` `/data/` → `/data`;\n- the runbook skeleton (C);\n- the `memory.peak` helper (D);\n- job-doc drift and stale status;\n- the module origin table;\n- a mutation-check script: each mutation a patch applied in a scratch worktree with a timeout.\n  The list is rebuilt from the surviving descriptions (job-table.md:98-102, job-queue.md:157-164,\n  e2806bd's message) and documented as rebuilt, not claimed identical to the original 22;\n- removal of the merged worktrees.\n\nThe pipeline CLIs and the analysis code are not changed.\n\n**Revalidation:** the offline suite; the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with\n`--group jobs`; the mutation script; peaks through the helper.\n\n**Acceptance.**\n- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in\n  `source_sha256` under a unique key, with top-level keys unchanged.\n- The lock diff only adds packages.\n- The live suite passes with 379 cases, or the difference is explained.\n- Every rebuilt mutation fails a test within its timeout.\n- Peaks are within budget.\n\n**Tests:** new cases in `test_provenance.py`; job suites on SQLite and live; the mutation script.\n\n**Guarantee:** no store change; the mutation script re-proves that each guard is tested.\n\n### M2 — The worker runs windows → spark_pipeline → verify\nBranch `feature/worker-pipeline` · Claude Code · after M1. Two stages in one PR, with a progress\nreport between them (not a pause):\n- **M2a:** M2.1, M2.8, M2.9, M2.10 and the CLI, exercised with the simulated pipeline.\n- **M2b:** M2.2–M2.7, the real pipeline.\n\n#### M2.1 Identity: store, output layout, result digest\n- **Store identity.**\n  - `init-db` creates a one-row table `job_store` (`store_id`, a random 128-bit hex; `created_at`;\n    `schema_version`).\n  - Job and attempt ids repeat after a database is recreated, so everything outside the database\n    uses `store_id` with them: output paths, process markers, events and cache provenance.\n- **Output layout.**\n  - The worker passes `output_root/<store_id>` to `claim()`, giving folders\n    `<root>/<store_id>/job-<id>-attempt-<n>/`.\n  - The store already builds the path from the given root (store.py:356), so the store needs no\n    change for this.\n  - A recreated database never collides with old folders, which today would fail every job\n    (worker.py:128-132).\n- **Run digest.**\n  - `src/etf_risk/runs.py` (new; shared with M4) writes a canonical manifest of the Spark run\n    folder: sorted relative paths, sizes and SHA-256 per file.\n  - Its SHA-256 is the run digest, the run's immutable identity.\n  - The worker writes `manifest.json` in the attempt folder before acceptance.\n- **Bound at acceptance** (additive store change; the guards are unchanged):\n  - `job_attempts.result_digest CHAR(64)` with a CHECK `(outcome = 'accepted') = (result_digest\n    IS NOT NULL)`;\n  - `accept_result(claim, digest)` sets it in its existing `job_attempts` update, inside the same\n    token-guarded transaction (store.py:398-402);\n  - the idempotent repeat path also compares the digest;\n  - both schema files, the drift test and the invariant queries are updated.\n\n  This ties the accepted decision and the accepted content together atomically.\n- **Simulated pipeline.** `SimulatedPipeline` produces a digest too, so all existing scenarios\n  keep running.\n\n#### M2.2 Steps and environment\n- **Steps.** Each step runs behind the launcher (M2.5) as `sys.executable -m etf_risk.<module>`,\n  with absolute paths only:\n  1. `windows --snapshot … --kind … --window-days … --stride … --anchor … --processed-root <abs>\n     --out-root <run_dir>/windows --name <name>`;\n  2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>`;\n  3. `verify --run …`.\n- **Job parameters** (`params.py`, a frozen dataclass): snapshot, kind, window days, stride,\n  anchor, sample ticker. Unknown keys are refused.\n- **Worker settings:** the processed root and the output root, both recorded in\n  `attempt.json`.\n- **Input checksums.** `submit` computes `input_checksums` from the files `windows.py` records in\n  `inputs_sha256`. The worker re-checks them before step 1; a mismatch is not retryable.\n- **Step environment** (allowlisted):\n  - `cwd` = `<run_dir>/.work`, which also catches `spark-warehouse`;\n  - `TMPDIR` = `.work/tmp`;\n  - `SPARK_LOCAL_DIRS` = `.work/spark`;\n  - `SPARK_SUBMIT_OPTS=\"-Djava.io.tmpdir=<abs>/.work/jtmp -XX:-UsePerfData\"`, which the Spark\n    launcher reads. The macOS JDK ignores `TMPDIR`.\n  - `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` = `sys.executable`. Otherwise workers use\n    `python3` from PATH (pyspark/core/context.py:342).\n  - Never `JAVA_TOOL_OPTIONS` or `_JAVA_OPTIONS`: their \"Picked up …\" notice would replace the\n    Java version that `environment()` records (spark_pipeline.py:635-636). A test checks\n    `run.json`'s `java` field.\n  - The directories are created first.\n  - Logs go to `<run_dir>/logs/<step>.log`.\n\n#### M2.3 Acceptance rule and failure classification\n- **Accept only if all hold:**\n  - every step exits 0;\n  - `run.json` status is `ok`;\n  - every `checks.json` count is 0;\n  - `verify.json` has no mismatch and the same breached windows;\n  - every table has `_SUCCESS`.\n- **Then:**\n  1. remove `.work`;\n  2. write `attempt.json`;\n  3. write `manifest.json`;\n  4. **renew**;\n  5. `accept_result(claim, digest)`.\n\n  Nothing in the folder changes after acceptance; a test compares the manifest before and after.\n- **Classification**, decided from the records, never from the exit code alone:\n  - **not retryable:** a checksum error (exit 3); `run.json` status `checks_failed`; a verify\n    mismatch; a parameter or input-checksum error;\n  - **retryable:** a signal, a timeout, status `failed`, a missing record, or \"execution lock\n    busy\" (M2.5).\n\n  Retryable failures requeue until `max_attempts`.\n\n#### M2.4 Time, deadlines and bounded operations\n- **Clocks.** Lease times in the database stay on the store's wall clock (UTC), which all\n  processes on this host share. Every local deadline uses `time.monotonic()`:\n  - self-fence;\n  - watchdog;\n  - timeouts;\n  - lock waits;\n  - operation budgets;\n  - backoff.\n\n  Event logs record UTC (shared across processes) and monotonic offsets (durations within one\n  process).\n- **Bounded database operations** (draft values, fixed at review from M2a measurements):\n  - **Session settings:** `connect_timeout` 3 s, `read_timeout` 5 s and `write_timeout` 5 s\n    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`\n    2 s, which is below the read timeout, so lock waits end as definite 1205 conflicts; session\n    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks\n    indefinitely.\n  - **Conflict retries:** the existing `CONFLICT_RETRIES` = 3 runs.\n  - **Operation budget:** B = 8 s on the monotonic clock, checked before each statement and each\n    retry; past it the operation raises without starting another statement.\n  - **Worst case:** one operation takes at most **W = B + 5 s = 13 s**.\n- **Kill grace.** G = 5 s SIGTERM + 2 s for SIGKILL to be confirmed = **7 s**.\n- **Renewal loop** (the worker thread):\n  - waits on the launcher with `wait(timeout=1 s)`;\n  - renews every 10 s;\n  - after every renewal, success or not, checks the self-fence deadline\n    `F = m₀ + L − M`, where `m₀` is the monotonic time just *before* the last successful\n    renewal started (the database lease began at or after `m₀`), with L = 60 s\n    (`DEFAULT_LEASE`) and **M = 25 s**;\n  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5).\n- **The inequality.** The longest gap between two deadline checks is W (one blocked store call).\n  Termination then takes G. The tree is therefore gone by `F + W + G = m₀ + L − M + 20 s`, which\n  is before the lease can expire (`m₀ + L`) whenever **M ≥ W + G**. The drafts give 25 ≥ 20, with\n  5 s to spare. Changing any value requires restating this inequality, and that is a pause point.\n- **No other blocking calls during a run.** From the renewal before step 1 to acceptance, the\n  worker thread makes only bounded store calls and bounded waits; it makes no Kafka calls.\n  - Kafka is used only between runs. `socket.timeout.ms` is pinned at 10 s.\n  - A commit that blocks before a run cannot cause overlap: the renewal before each step returns\n    false if the job was taken over meanwhile, and the step never starts.\n- **Retry rules:**\n  - `renew`: retried at the next interval;\n  - `accept_result` and `fail_attempt`: retried on disconnects only, until F; `accept_result` is\n    idempotent for its token;\n  - `claim`: raises into `serve()`'s rewind and retry;\n  - `submit`: never retried; the CLI exits with a distinct \"outcome unknown\" code;\n  - reconciler passes: bounded, logged and repeated.\n\n#### M2.5 No overlapping Spark work: watchdog and host execution lock\nA SIGSTOPped worker can neither renew nor check its deadline, and its pipe to the launcher stays\nopen. Two independent layers therefore protect against overlap, in addition to the worker's own\nself-fence.\n- **Watchdog (the launcher process, one per step).**\n  - The worker starts the launcher with `start_new_session=True` and a keepalive pipe as its\n    stdin.\n  - The launcher keeps a monotonic deadline. It starts from the value sent after the\n    renewal-before-step and is extended only by the worker's \"remaining time\" messages.\n  - It terminates its tree (M2.6) on EOF (the worker died) or when the deadline passes (the\n    worker is frozen, stuck or fenced by its own clock). Either way the tree is gone by\n    F + G, before the lease can expire, without any action by the worker.\n- **Host execution lock.**\n  - Before starting a step, every launcher takes an exclusive `flock` on a host-wide file\n    (default `~/.cache/etf-risk/locks/spark-exec.lock`; tests use their own path).\n  - It then checks that no process carrying another attempt's marker survives (M2.6).\n  - It passes the lock descriptor to the step's driver, so the lock is held while the launcher\n    or the driver lives. PySpark closes inherited descriptors for the JVM, and the JVM exits when\n    the driver's pipe breaks; the survivor check covers that window.\n  - A launcher that cannot get the lock, or still sees survivors, within the lock-wait bound\n    (step limit + G + 30 s) does not start Spark. It exits with \"execution lock busy\", and the\n    attempt fails as retryable.\n  - So even when the whole old tree is frozen (watchdog included) or the wall clock jumps, no\n    replacement Spark run starts while an earlier tree survives. The session harness takes the\n    same lock for its reference runs.\n- **Renewal before each step and before acceptance.** A fenced worker never starts a new step.\n\n#### M2.6 Terminating a process tree\n- **Why not a group kill.** PySpark's daemon calls `os.setpgid(0, 0)` (pyspark/daemon.py:115),\n  so its workers leave the step's group, and re-parented orphans escape child-walks.\n- **Membership.** Every step process carries the marker\n  `ETF_RISK_ATTEMPT=<store_id>:<run id>:<attempt key>`, where the attempt key is the first 16 hex\n  digits of SHA-256(token). The token itself never leaves the worker. Members are found by session\n  id (`os.getsid` = the launcher's pid; nothing in the tree calls `setsid`) as a prefilter,\n  confirmed by the marker. A pid alone is never enough.\n- **Sequence.** SIGTERM to all members (so the JVM can delete its scratch); wait 5 s; SIGKILL to\n  survivors; rescan until none remain (bounded). The pids and the reason go to\n  `logs/launcher.log`.\n\n#### M2.7 Startup sweep: preserve valid active attempts\nWhen a worker starts, it scans this host for marked process trees of its own `store_id` and looks\neach attempt up in the store.\n- **Preserved:** any tree whose attempt is still *valid active*, meaning the job is running and\n  its current attempt number and token hash match. Its lease or watchdog decides when it ends;\n  the sweep never shortens a valid attempt.\n- **Terminated:** trees whose attempt has ended (expired, failed or accepted) or was taken over.\n- **Ended attempts' folders:** their `.work` scratch is removed; the folder itself never is.\n- **Left alone and reported:** trees of other store ids.\n- **Database unreachable:** the sweep does nothing.\n- **Folder listing.** `jobs cleanup` is dry-run only: it lists the folders of ended,\n  non-accepted attempts. Deleting them is not part of M2.\n\n#### M2.8 Database connections\n- **Factory.** `JobStore` accepts a connection factory: `connect_mysql` with the M2.4 timeouts and\n  session settings. It never uses `ping(reconnect=True)`, which drops `SET SESSION`.\n- **Reconnect only at the start of an operation:** before BEGIN, after a ping when the connection\n  has been idle for 60 s or more. Never inside a transaction. A connection that broke\n  mid-transaction is discarded; the transaction's remaining statements never run on a new\n  connection.\n- **Disconnects:** PyMySQL 2003, 2006, 2013, server codes 1053, 1927 and 4031, `InterfaceError`,\n  or `open == False` after an error. The connection is marked broken in the except path, before\n  the ROLLBACK.\n- **No replay.** The failed operation raises, as today.\n\n#### M2.9 Kafka settings (pinned in `kafka.py`, with tests on values and relations)\n| Setting | Value | Why |\n|---|---|---|\n| `group.protocol` | `classic` | `session.timeout.ms` is ignored under `consumer` |\n| `heartbeat.interval.ms` | 3000 | pinned default |\n| `session.timeout.ms` | 15000 | ≥ the broker's 6 s minimum, ≥ 3 heartbeats, < L |\n| `max.poll.interval.ms` | attempt limit + G + 60 s | a legitimate run never leaves the group |\n| `socket.timeout.ms` | 10000 | bounded commits and fetches |\n- **Max-poll error.** It gets its own event.\n- **Graceful stop** closes the consumer, so the group sees an immediate LeaveGroup.\n- **Consequence for E2.** Under the classic protocol, a joining standby or restarted worker waits\n  for a busy member to poll, and E2's recovery times include that wait.\n\n#### M2.10 Supervision, graceful stop, events, CLI\n- **Supervision.**\n  - `jobs worker` restarts its serve loop in-process, with backoff, after transport errors only:\n    disconnects, `ClaimRace`, non-fatal Kafka errors. Any other error exits non-zero.\n  - SIGKILLed workers are restarted by the M3 harness after a Part A delay.\n- **Graceful stop** (SIGTERM or SIGINT): stop polling, terminate the running tree, call\n  `fail_attempt(retryable=True)`, close the consumer. On a job's last attempt this fails the job\n  (store.py:416-417), so batches drain before stopping workers.\n- **Event log.** Each process writes JSON lines, flushed per event:\n  - delivered, claimed;\n  - renewed, renewal failed;\n  - step start and end, lock wait;\n  - watchdog kill, fenced;\n  - accepted, failed, requeued, published;\n  - max-poll.\n- **Attempt record.** `attempt.json` holds the worker id, store id, run id, steps (exit code,\n  times), the input checksums as checked, the settings and `code_state()`.\n- **CLI** `python -m etf_risk.jobs`:\n  - `init-db`, `create-topic`, `submit`, `worker`, `reconciler`;\n  - `cleanup` (dry run);\n  - `status [--check]`: tables and `invariant_violations()`; exits 1 on a violation;\n  - `export <dir>`: tables, violations and settings, for M3's batches.\n\n**Deliverables.**\n- **New modules:** `jobs/{pipeline,launcher,processes,params,events,__main__}.py` and\n  `src/etf_risk/runs.py`.\n- **Changes:** `store.py` (factory, budget, digest, store id), `mysql.py` (timeouts, `is_disconnect`),\n  `kafka.py` (settings), both schema files.\n- **Docs:** `job-queue.md` and `job-table.md` updated; the runbook's E1/E2 part.\n- **Ledger rows:** idle available memory with the stack up; per-step peaks for calendar-year and\n  stride 21; the Docker VM process's memory on the host.\n\n**Acceptance** (native worker; MySQL and Kafka in Compose; fresh containers):\n- **Normal runs.** A calendar-year job and a stride-21 job (no injection, no timing claims) end\n  `succeeded`. Each has exactly one accepted attempt whose recorded digest equals its manifest.\n  Each passes every check and verify. Each equals a direct CLI run by content, using the caching\n  collector's `TABLE_KEYS` (collect_caching_measurements.py:74-75) and `compare_tables`\n  (collect_partition_measurements.py:286), with `windows.parquet` compared by its window key.\n- **Worker-only SIGSTOP during step 2.** Checked *before SIGCONT*:\n  - no process of attempt 1 is alive by its watchdog deadline + G;\n  - the lock is free;\n  - attempt 2's Spark step started after attempt 1's last process exited (event times and the\n    process scan);\n  - attempt 1's renewal count is unchanged after attempt 2's claim.\n\n  After SIGCONT, the old worker is fenced and writes nothing.\n- **Whole-tree SIGSTOP** (worker, launcher and Spark). Checked *before SIGCONT*:\n  - the replacement started no Spark process;\n  - it waited on the lock or exited \"execution lock busy\";\n  - only one tree is resident.\n\n  After SIGCONT, the old launcher terminates its tree at once, because its deadline has passed.\n  The job ends with exactly one accepted result.\n- **Worker SIGKILL during step 2.** No attempt process survives the lifeline grace, and the job\n  is requeued after its lease and succeeds.\n- **Timeouts.** An over-limit step is terminated and retried.\n- **Database stalls.** `LOCK TABLES jobs WRITE` from another session, `docker compose pause mysql`,\n  and `restart mysql`, each during a run:\n  - every store operation stays within W (measured);\n  - the run either continues or self-fences before its lease;\n  - nothing needs a manual restart;\n  - the job ends with one accepted result.\n- **Kafka restart during a run.** The same outcome.\n- **Startup sweep.** It terminates only ended attempts' trees, and preserves a live attempt run by\n  another worker.\n- **No leftovers.** The process scan shows no attempt processes. No new `spark-*`, `blockmgr-*`,\n  `pyspark-*`, `snappy-*`, `libzstd-jni*`, `liblz4-java*` or hsperfdata entries appear in\n  `/private/tmp` or `getconf DARWIN_USER_TEMP_DIR`. No new `spark-warehouse` appears in the\n  repository.\n- **Invariants.** `invariant_violations()` is always empty.\n- **Earlier tests.** All earlier job tests pass on both stores.\n\n**Tests.**\n- **Offline:**\n  - **launcher:** deadline kill; EOF kill; lock wait and refusal; survivor check; exit codes;\n  - **tree termination:** a grandchild that calls `setpgid(0, 0)`, and a double-fork orphan; none\n    survives a worker SIGKILL, a fence, a timeout or a worker-only SIGSTOP;\n  - **deadlines:** a fake store blocking W per call. The tree is gone before `m₀ + L`; no step\n    starts after F; the watchdog still ends the tree when the worker thread blocks beyond W;\n  - **sweep:** the rules of M2.7;\n  - **reconnect:**\n    - a disconnect between statements 1 and 2 never runs statement 2 on a new connection;\n    - a COMMIT that took effect but whose reply was lost: a repeated accept returns True, with\n      exactly one accepted attempt;\n    - session settings after a reconnect;\n    - the ping before an operation;\n  - **classification, parameters, checksums;** the environment allowlist (no service URL in a\n    step's environment); the `java` field;\n  - **digest and store identity:** manifest determinism, the CHECK, the drift test;\n  - **Kafka settings and their relations.**\n- **Spark-marked:** a tiny job on a `write_snapshot` snapshot (tests/conftest.py) through\n  `Worker` with SQLite and `MemoryQueue`.\n- **Live** (gated by `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP`):\n  - the acceptance cases above;\n  - a standby that receives the next message only after the primary exceeds a short\n    `max.poll.interval.ms`;\n  - store-operation durations recorded and checked against W.\n- **Mutation script:** three new mutations — a reconnect inside a transaction, disconnects treated\n  as conflicts, and `ping(reconnect=True)` in place of the factory.\n\n**Guarantee.**\n- Acceptance still goes only through the token guard, now also binding the digest.\n- Self-fence, watchdog and lock only stop or delay work.\n- The sweep and `cleanup` never touch valid or accepted attempts.\n\n**Deferred.** A unique index on accepted attempts. E1 measures whether the token guards alone\nkeep the guarantee, so this is decided after M3, in M6.\n\n### M3 — Recovery experiments E1 and E2\nBranch `feature/recovery-experiment` · Tooling Claude Code · Experiment: the project author,\ntutored · after M2.\n\n**Claude's tooling.**\n- **Session harness.** One process starts the worker(s), the standby and the reconciler, performs\n  injections, restarts crashed workers after the Part A delay, and logs everything (UTC, from the\n  host clock).\n- **Injections:**\n  - crashes at `WORKER_FAULT_POINTS` (worker.py:54-59), carried out as a real SIGKILL and fired\n    once per job (recorded in the events and `attempt.json`);\n  - SIGKILL during a step;\n  - SIGSTOP and SIGCONT of the worker alone or of the whole tree, always from the wait loop and\n    never inside a transaction;\n  - `docker compose restart` of Kafka or MySQL at a chosen phase;\n  - holding a worker at `after_pipeline` while MySQL restarts.\n- **Batch lifecycle:**\n  - a fresh MySQL container, store id, topic and consumer group;\n  - reference runs (direct CLI, same commit, under the host lock);\n  - drain at the end;\n  - `jobs export` and `memory.peak` before `down -v`. The collector reads files only.\n- **Session helpers** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:\n  machine checks adapted to Docker running, with the memory threshold from M2's dry runs; two\n  windows; `case n`; watcher; abort; note.\n- **Collector** `analysis/collect_recovery_measurements.py --batch`:\n  - imports `compare_tables` unchanged;\n  - writes `measurements.csv` and `acceptance.json`, with criteria 1–5 plus \"6 guarantee\";\n  - exits 1 on any failure.\n- **Batches** live in `data/outputs-recovery/<batch>/`.\n\n**The author's `docs/recovery-experiment.md`.** Claude scaffolds Parts A and B, History and the\n`Author:` line.\n- **Part A, decided by the author:**\n  - the cases;\n  - repetitions;\n  - the job size: the recommendation is calendar-year for every case, with stride 21 only in M2;\n  - lease, renewal, reconcile and restart-delay settings;\n  - `--max-attempts`;\n  - deadlines per case: lease + reconcile interval + publication grace + session timeout +\n    restart delay + attempts left × attempt limit;\n  - memory thresholds: suggested peak + 0.5 GiB free; with the host lock, at most one tree runs;\n  - metric definitions;\n  - predictions;\n  - acceptance criteria;\n  - stop rules.\n- **Draft cases:**\n  - a crash at each worker fault point, and during step 2;\n  - a worker-only stall and a whole-tree stall;\n  - Kafka restart while idle, during a submit, and during a run;\n  - MySQL restart during a run, shorter and longer than M (the self-fence margin);\n  - MySQL restart while held at `after_pipeline`: one execution predicted if MySQL is back before\n    F, two otherwise.\n- **Metrics per job:**\n  - injection time;\n  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;\n  - recovery: the next `claimed_at`;\n  - completion: `finished_at`;\n  - executions;\n  - **number** of accepted attempts;\n  - correctness: checks, plus content against the reference, plus digest;\n  - category: succeeded, failed (attempts exhausted), lost (not terminal by the deadline), or\n    submit outcome unknown.\n- **E1 cross-check.** The author's own SQL for accepted attempts per job must agree with\n  `invariant_violations()`.\n\n**Acceptance.**\n- One batch meets every Part A criterion.\n- Across all batches: zero lost jobs, zero jobs with two accepted results, and exactly one\n  correct, digest-bound accepted result per succeeded job.\n- Peaks are recorded per batch.\n- Commits follow the precedent: tooling → Part A (before any measured run, author-approved) →\n  dry batches → the formal session (the author) → Part B → status.\n\n**Tests:** harness, collector and helper tests in the pattern of `test_caching_collector.py` and\n`test_caching_session.py`, including planted problems, each failing its criterion.\n\n**Guarantee:** measured under failures; no new write path.\n\n### M4 — Redis cache for summary queries, with fallback\nBranch `feature/result-cache` · Infrastructure Claude Code · Cache logic: the project author,\ntutored · after M2.\n\n**Identity**, the contract the author's key must meet (the tests pin it):\n- **Run identity is the run digest** (M2.1), never the run id or path. Job and run ids repeat\n  after a database is recreated, and paths can be reused.\n- **The key** covers:\n  - the cache format version;\n  - the engine (PySpark version);\n  - the run digest;\n  - the query name;\n  - the query definition hash (SHA-256 of its SQL text);\n  - the canonical full parameters: every parameter including defaults, in canonical JSON with\n    sorted keys and normalized types.\n\n  The key is a hash of that tuple behind a readable prefix. The stored value repeats the tuple,\n  and a mismatch on read counts as a miss.\n- **Pinned by tests:**\n  - equal run ids with different digests never share a key;\n  - a changed parameter or SQL text changes the key;\n  - equal requests give equal keys across processes.\n\n**Accepted-run policy** (`runs.py` resolver, Claude). A run is servable only if one of the\nfollowing holds; anything else is refused, with no fallback to unaccepted runs.\n- **(a) A job run.** In the job table, under its `store_id`, the job is succeeded and its accepted\n  attempt's recorded `result_digest` equals the folder's manifest digest.\n- **(b) A historical run.** The reviewed registry `docs/accepted-runs.json` (committed) lists it\n  with path, digest, the basis for acceptance (`run.json` status ok, all checks 0, `verify.json`\n  clean, the spec §8 reference) and the author's approval date. The folder's digest must match.\n  - `python -m etf_risk.runs register` computes and checks the entry. The digest is stored in the\n    registry, so the historical folder is never written to.\n  - This lets M4 and E3 use the run of record without creating job rows outside\n    `accept_result`.\n  - **Pause, an authorship decision:** which run to register. `run-20261013T043848Z-4` has a clean\n    `verify.json`. The documented `-2` has none, and registering it would mean running verify into\n    it first. The four runs' tables are identical (plots.py:15-16).\n\n**Per-query check.** Each query compares file sizes and modification times against the manifest\nand fully re-hashes on any mismatch. `serve` re-hashes at startup, and `--verify-full` re-hashes\non demand. E3 reports the resolver's cost separately.\n\n**Claude's part.**\n- **Compose `redis`:**\n  - pinned by digest;\n  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, persistence off;\n  - 128m `mem_limit` and `memswap_limit`;\n  - port `127.0.0.1:6380`;\n  - a `PING` healthcheck.\n- **The `cache` group.**\n- **`src/etf_risk/summary.py`:**\n  - named queries over `paired/`. The author moves their own SQL from `analysis/sql_*.py`; those\n    scripts are not edited (documents cite them by hash), and moving the SQL is an authorship\n    step;\n  - a one-shot CLI (new process) and a warm mode (one SparkSession, JSON-lines requests on stdin\n    and stdout);\n  - the resolver and the registry tool;\n  - contract tests and fakes: a Redis stand-in that can go \"down\", and a live fixture gated by\n    `ETF_RISK_REDIS_URL`;\n  - a Spark-marked test that the queries on the registered run reproduce spec §8 (windows 529,\n    466, 311, 174, 310), skipped without `data/`.\n\n**The author's part.** `src/etf_risk/cache.py`, scaffolded:\n- the key and normalization, under the identity contract;\n- serialization;\n- cache-aside get-or-compute;\n- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while\n  Redis is down, decode errors treated as misses;\n- counters.\n\n**Acceptance.**\n- Contract tests pass offline and live.\n- With Redis stopped, every query returns the Spark result, within the timeout and breaker bound.\n- Unaccepted, unregistered or changed runs are refused.\n- Redis peak ≤ 128 MiB.\n- The runbook's E3 commands work as written.\n\n**Tests:** the identity tests above; resolver refusals (a non-accepted attempt; a digest mismatch;\nan unregistered historical run); fallback; equal results; live Redis; the spec §8 test.\n\n**Guarantee:** reads accepted runs only, verified by digest; never writes the job table.\n\n### M5 — E3: new Spark process vs warm Spark session vs Redis\nBranch `feature/result-cache-experiment` · Tooling Claude Code · Experiment: the project author,\ntutored · after M4.\n\n**Configurations** (Part A):\n- N: a new process per query;\n- W: a warm session, with no cache;\n- R: a warm session plus Redis, at hit rates set by repeats (e.g. 0, 50 and 90%);\n- F: Redis stopped, then recovered.\n\n**Key space.** Queries × accepted runs (the registered run of record and M2/M3 job runs) × any\nparameters the author adds.\n\n**Measures:**\n- client-side monotonic latency per query;\n- the resolver's cost, separately;\n- realized vs designed hit rate;\n- the warm session's process-tree peak (marker sampler);\n- Redis `memory.peak` and `used_memory_peak`.\n\n**Deliverables:** `docs/result-cache-experiment.md`, `docs/result-cache-session.zsh`,\n`analysis/collect_result_cache_measurements.py`, and a batch in\n`data/outputs-result-cache/<batch>/`.\n\n**Acceptance:** one batch meets every Part A criterion; drift is reported.\n\n**Tests:** collector (planted problems), session helpers, and the hit rate the workload generator\nproduces.\n\n**Guarantee:** read-only for the job table.\n\n### M6 — Architecture, report and demo\nBranch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · after M3\nand M5.\n\n- **`docs/architecture.md`** (new). It covers:\n  - batch pipeline plus extension;\n  - native vs Compose placement;\n  - failure model, guarantee and where it is enforced and checked;\n  - time and deadline rules (M2.4–M2.5);\n  - cache identity and the accepted-run policy;\n  - budget ledger;\n  - runbook.\n- **Spec §5's diagram:** gains `jobs/` and Compose, and its node ids are renamed.\n- **Figures X5 (E1/E2) and X6 (E3)**, added together as X1–X4 were:\n  - `plots.py` (`FIGURES`, `DOCUMENTED`, the tuple in `compare_documented`);\n  - `test_plots.py` (12 → 14);\n  - CSV copies and their README rows;\n  - every \"twelve figures\" and \"X1–X4\" mention.\n- **Spec:** §8 \"What the recovery experiments showed\" and \"What the result-cache experiment\n  showed\"; §9 and §11 marked implemented, with the final ledger.\n- **`results.md`:** a new extension section. §7 changes only with the author's re-approval.\n- **README:** status and the full runbook.\n- **`demo.md`:** submit; kill the worker mid-run; watch `status --check` recover; cache miss →\n  hit → Redis stopped → fallback → restart.\n- **The deferred unique-index decision.**\n\n**Acceptance:**\n- numbers traced to committed CSVs and records;\n- `plots --check` passes;\n- every command run as written in a fresh worktree;\n- links valid;\n- the author approves the conclusions.\n\n**Tests:** `test_plots.py`; a link check; the full offline suite.\n\n**Guarantee:** documentation only.\n\n## Separate workstreams (outside M1–M6)\n\nNo milestone branch touches these files, and no milestone waits on them.\n\n- **W1 Data verification** (`feature/data-verification`, own plan):\n  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);\n  - terms of use;\n  - the cause of the Adj Close steps;\n  - the 36 unverified days;\n  - data-sources.md's missing AI header.\n- **W2 Privacy-hook fixes** (`fix/transcript-privacy`): the uncommitted hook, test and transcript\n  edits, plus spec §10's hook items. Claude touches the hook only when asked.\n- **W3 AI-log review.**\n  - **Scope:** the 68 untracked folders (including the sessions behind PRs #7–#9) and each\n    milestone's logs.\n  - **Reviewer:** the author.\n  - **Where commits go:** following the precedent, each review lands as a separate \"Add reviewed\n    AI logs for …\" commit, last on the milestone branch (ed71796). Logs reviewed after a merge go\n    on a `docs/ai-logs-<date>` branch.\n  - **Never mixed with code.**\n  - **Also in scope:** `docs/ai-usage/README.md`'s attribution of the hook to Codex only, and the\n    redaction of other projects' names that appeared in this planning session's tool output.\n\n## Verification (end to end)\n\n- **Per milestone:**\n  - the offline suite (`uv run --group measure --group plots pytest`) with counts;\n  - Spark-marked tests;\n  - live suites on fresh containers (`--group jobs`, `--group cache`);\n  - `status --check` empty after every live run;\n  - the mutation script;\n  - the lock diff;\n  - measured peaks against the ledger.\n- **System, after M6:** in a fresh worktree on `main`, follow the runbook from\n  `uv sync --frozen` through smoke runs of E1/E2 and E3. Check that:\n  - every accepted run passes its checks, matches its reference by content, and matches its\n    recorded digest;\n  - no overlapping Spark trees appear in the event logs;\n  - `plots --check` passes;\n  - peaks are within the ledger.\n\n## Known pause points\n\n- **M2:** any change to the M2.4 values that breaks or restates M ≥ W + G; any store change beyond\n  `job_store` and `result_digest`.\n- **M3:** Part A approval (cases, job size, thresholds, deadlines); the author runs the formal\n  session.\n- **M4:** the author writes `cache.py` and moves their SQL into `summary.py`; the choice of which\n  historical run to register.\n- **M5:** Part A approval; the formal session.\n- **M6:** the conclusions' wording; the unique-index decision.\n"
}
```

## 151. User — 2026-10-23T11:50:02.564Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 152. Assistant — 2026-10-23T11:50:35.719Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - after every renewal, success or not, checks the self-fence deadline\n    `F = m₀ + L − M`, where `m₀` is the monotonic time just *before* the last successful\n    renewal started (the database lease began at or after `m₀`), with L = 60 s\n    (`DEFAULT_LEASE`) and **M = 25 s**;\n  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5).",
  "new_string": "  - checks the self-fence deadline on every tick and after every renewal, success or not. The\n    deadline is `F = m₀ + L − M`, where `m₀` is the monotonic time just *before* the last\n    successful renewal started (the database lease began at or after `m₀`), with L = 60 s\n    (`DEFAULT_LEASE`) and **M = 25 s**;\n  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5). The\n    worker's end of that pipe is non-blocking. If the pipe is full because the launcher is\n    frozen, the message is dropped, which can only make the watchdog act sooner."
}
```

## 153. User — 2026-10-23T11:50:36.898Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 154. Assistant — 2026-10-23T11:50:38.867Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **Disconnects:** PyMySQL 2003, 2006, 2013, server codes 1053, 1927 and 4031, `InterfaceError`,\n  or `open == False` after an error. The connection is marked broken in the except path, before\n  the ROLLBACK.",
  "new_string": "- **Disconnects:** PyMySQL 2003, 2006, 2013, server codes 1053, 1927 and 4031, `InterfaceError`,\n  or `open == False` after an error. The connection is marked broken in the except path, before\n  the ROLLBACK.\n- **No ROLLBACK on a broken connection.** The store closes it instead; the server rolls back the\n  open transaction when the session ends. No statement then runs after the operation budget, so\n  W holds. A COMMIT that timed out may still have taken effect on the server, which is the\n  existing \"failed COMMIT\" case, handled by idempotent repeats."
}
```

## 155. User — 2026-10-23T11:50:39.950Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 156. Assistant — 2026-10-23T11:50:40.339Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - it waited on the lock or exited \"execution lock busy\";\n  - only one tree is resident.",
  "new_string": "  - it waited on the lock or exited \"execution lock busy\";\n  - no second Spark tree exists; the only one is the frozen tree."
}
```

## 157. User — 2026-10-23T11:50:41.405Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 158. Assistant — 2026-10-23T11:50:49.495Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 1,
  "limit": 140
}
```

## 159. User — 2026-10-23T11:50:49.652Z

### Tool result

```
1	# Plan: finishing the systems extension (spec §11) in six reviewed milestones
2	
3	Status: revision 2, after the author's review on 2026-10-23 and a design check against the code
4	and libraries. Nothing is implemented until it is approved.
5	
6	## Context
7	
8	Stages 1–4 and the extension's job queue are merged into `main` (f058095): PR #7 (job table,
9	fencing), PR #8 (Kafka delivery, reconciler), PR #9 (Stage 4). Spec §11 still lists as planned:
10	- the real pipeline in the worker (today `SimulatedPipeline`);
11	- the recovery experiments E1/E2;
12	- the Redis result cache;
13	- the cache experiment E3;
14	- their documentation.
15	
16	This plan turns the author's six-point outline into milestones M1–M6, one branch and PR each. Each
17	milestone has deliverables, acceptance criteria, tests and a statement of how it keeps the
18	guarantee. Four cross-cutting requirements run through all of them: code provenance for `jobs/`,
19	reproducible dependencies, startup commands, and measured memory budgets. Data verification, the
20	privacy-hook fixes and AI-log review stay in separate workstreams.
21	
22	State observed on 2026-10-23:
23	- the main worktree is on `fix/measure-process-kinds` (97c35f3, pushed, not merged), with
24	  uncommitted privacy-hook work (W2);
25	- 68 untracked AI-log folders exist;
26	- another project's containers share the Docker VM;
27	- `gh` is not installed.
28	
29	## Decisions and working mode (the author, 2026-10-23)
30	
31	- **Placement.** The worker, reconciler and submit run natively on the host. MySQL and Kafka (and
32	  Redis from M4) run in Compose.
33	- **Authorship.** The spec §11 split stays.
34	  - Claude Code writes M1, M2 and all tooling.
35	  - The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.
36	- **Six milestones**, as in the outline.
37	- **Working mode after approval.** Claude proceeds autonomously with routine work inside each
38	  milestone: code, tests, docs, dry runs and commits on the milestone branch.
39	- **When Claude pauses and asks.**
40	  - **Material design changes:** anything this plan does not describe; any change to the store's
41	    guards or SQL beyond the two additive changes in M2.1; any change to the time inequality in
42	    M2.4.
43	  - **Authorship decisions.**
44	  - **Formal experiment approval:** Part A sign-off, and the author running the formal session.
45	- **Push and merge.** The author pushes, or tells Claude to push, and opens and merges each PR.
46	- **Reports.** Every milestone ends with a report: what was done, what was found and fixed, test
47	  counts and measured peaks.
48	
49	## At a glance
50	
51	| # | Branch | Written by | Needs | Main deliverable | Done when |
52	|---|---|---|---|---|---|
53	| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; recursive provenance; `jobs` group; runbook skeleton; peak helper; mutation script | provenance covers `jobs/`; lock only adds; live suite 379 or explained; mutations caught |
54	| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline; renewals with monotonic deadlines; watchdog and host lock; tree cleanup; reconnect; store identity; result digest; CLI | crash, stall, timeout and restart cases end with one accepted, correct, digest-bound result and no overlapping Spark trees |
55	| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, harness, collector, batch | Part A met; no lost job; no second acceptance |
56	| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py`, `runs.py` | M2 | cache-aside keyed by run digest and full query; accepted-run policy; fallback | contract tests pass; same results with Redis down; the run of record is usable through the reviewed registry |
57	| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, harness, collector, batch | Part A met |
58	| M6 | `docs/extension-report` | Claude drafts; author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |
59	
60	M4's code can be written while M3's formal session runs (ground rule 6); it does not touch M3's
61	files.
62	
63	## Ground rules for every milestone
64	
65	1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has
66	   exactly one, and a job may execute more than once.
67	   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it.
68	   - **Checking.** `INVARIANT_QUERIES` / `invariant_violations()` (store.py:127, :481) check it
69	     after every test scenario, every worker run and every experiment batch.
70	   - **Accepting.** Nothing but `JobStore.accept_result` produces an accepted attempt.
71	   - **No reconnect inside a transaction** (M2.8). It could break the guarantee: the rest of a
72	     transaction would commit statement by statement.
73	   - **Cleanup** never touches an accepted or valid active attempt.
74	   - **The cache** serves accepted runs only and never writes the job table.
75	   - **No overlap.** No replacement Spark work overlaps a surviving earlier process tree (M2.5).
76	2. **Authorship.**
77	   - For the author's parts, Claude prepares scaffolds (signatures, docstrings, TODOs, contract
78	     tests) and reviews, but does not fill them in.
79	   - New files carry an `AI contribution:` line.
80	   - Experiment documents carry an `Author:` line saying the author wrote Part A and the answers
81	     with tutoring, unlike earlier experiments where Claude drafted Part A
82	     (caching-experiment.md:56).
83	3. **Git.**
84	   - Each milestone has its own worktree (`.claude/worktrees/<name>`) from up-to-date `main`, with
85	     a `data` symlink to the main worktree's `data/`. M1 changes `.gitignore`'s `/data/` to `/data`
86	     so the symlink is ignored too.
87	   - Stage files by explicit path only.
88	   - Merge with merge commits; never squash or rebase.
89	   - Commits end with the Co-Authored-By trailer.
90	   - Formal sessions run on a merged, clean commit whose SHA lands in every record, with no
91	     commits during a session.
92	4. **Privacy.** `data/` and the private plan stay out of Git. Never print memory files,
93	   `.git/info/exclude`, app lists, or other projects' container or session names in tool calls.
94	   Helpers count other containers without naming them. Child processes get an allowlisted
95	   environment, so service URLs and passwords never reach the pipeline steps.
96	5. **Measurement sessions.** While one runs, other sessions only write and review. They wait for
97	   the explicit end, then check that the worktree is unchanged.
98	6. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write "one process",
99	   never "one core". Give each experiment a "not claimed" list.
100	
101	## Cross-cutting requirements
102	
103	**A. Code provenance for `jobs/`.**
104	- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob("*.py")` (provenance.py:62).
105	  No record identifies `jobs/*.py` or `jobs/schema/*.sql`, and a plain recursive glob would
106	  collide on `__init__.py`.
107	- **M1.** Hash every `*.py` and `*.sql` under `src/etf_risk/`, keyed by package-relative POSIX
108	  path. Top-level keys stay as they are, so old records remain comparable.
109	- **From M2.**
110	  - `attempt.json` and every experiment record carry `code_state()`.
111	  - Each accepted result is bound to its run digest in the job table (M2.1).
112	- **Authorship provenance.** An origin table in `job-queue.md` maps each module → commits
113	  (eec1032, e2806bd, cd72957) → PR → the tests that verify it. The `AI contribution:` lines stay.
114	
115	**B. Reproducible dependencies.**
116	- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`
117	  (docker/compose.yaml:13; test docstrings) and are not in `uv.lock`.
118	- **Groups.**
119	  - M1 adds a `jobs` group with these pins.
120	  - M2 adds `psutil==7.2.2` to that group; it is already locked through `measure`.
121	  - M4 adds a `cache` group with an exact `redis` pin.
122	- **Lock changes** may only add packages. numpy 2.5.4, pandas 2.3.3, pyspark 4.2.0, pyarrow 26.0.0
123	  and psutil 7.2.2 stay unchanged, checked with a lock diff and `uv lock --check`.
124	- **Commands** use `--group …` and `uv sync --frozen`.
125	- **Images** are pinned by digest. Redis follows the Kafka rule: the newest release at least two
126	  weeks old.
127	- **Host tools** are recorded with each formal session (2026-10-23: uv 0.11.16, Java 17.0.10,
128	  Docker 28.3.0, Compose v2.38.1, VM 3.83 GiB).
129	- **Out of scope:** the NumPy pin.
130	
131	**C. Startup commands.**
132	- **Runbook.** A README section (skeleton in M1, filled by M2, M4 and M6) gives copy-pasteable
133	  commands for:
134	  - **Setup:** the worktree and `data` symlink; the test services.
135	  - **The E1/E2 stack:** Compose `mysql kafka`; then `init-db`, `create-topic`, worker,
136	    reconciler, submit and `status`.
137	  - **The E3 stack:** Compose `redis`, the query CLI and the warm query service.
138	  - **Teardown:** export first, then `down -v`.
139	- **Readiness.** A service is ready only after a check that matches what will use it:
140	  - MySQL: a login plus `SELECT 1` (its healthcheck answers before logins work,
```

## 160. Assistant — 2026-10-23T11:51:06.173Z

I've revised the plan for your three points, and folded in the plan agent's review. It now holds both. The six milestones stay as they were.

**1. Stalled workers and overlapping Spark runs**
- **Watchdog.** Each pipeline step now runs under a small launcher process with its own deadline. The worker can only extend that deadline, by sending it the remaining time after each successful lease renewal. If the worker is SIGSTOPped or crashes, the launcher kills the whole step tree before the lease can expire.
- **Host-wide execution lock.** It covers the case where the whole tree is frozen. Every launcher must hold this lock, and find no surviving process from another attempt, before starting Spark. Otherwise it gives up and the attempt is retried later.
- **Tests before SIGCONT.** Milestone 2's acceptance stops either the worker alone or the whole tree, then checks before SIGCONT that no replacement Spark run overlaps the old one.
- **Startup cleanup.** A starting worker kills only leftover processes whose attempt has already ended in the job table. Any attempt still current in the database is left alone, and if the database can't be reached, nothing is killed.

**2. Bounded database operations and the self-fencing deadline**
- **Timeouts and retries.** Draft values: connect 3 s, read and write 5 s each, lock wait 2 s (below the read timeout), and the existing 3 retries on lock conflicts.
- **Time budget.** Each database operation also has an 8 s budget on the monotonic clock, so one operation takes at most 13 s.
- **The deadline.** The worker stops its own run 25 s before the lease would expire. Because 25 s covers the slowest operation (13 s) plus the time to kill the tree (7 s), the tree is always gone before the lease runs out. Any change to these values would be a pause point.
- **No other blocking calls during a run.** While Spark runs, the worker makes no Kafka calls.
- **Monotonic time.** Every local deadline uses `time.monotonic()`.

**3. Cache identity**
- **Run identity.** The cache key is built from a SHA-256 digest of the run's files, never from the run id or path, so ids that repeat after the database is recreated can't collide.
- **Recorded at acceptance.** The digest is written into the job table in the same transaction that accepts the result.
- **Full query.** The key also covers the query's name and SQL text, every parameter including defaults, the PySpark version and a format version.
- **The run of record.** It becomes usable through a reviewed registry file, `docs/accepted-runs.json`. Its digest must match, and no job rows are created outside the normal acceptance path. Which run to register (`-4`, which has a clean `verify.json`, or the documented `-2`) is your decision.

`★ Insight ─────────────────────────────────────`
- **Why both protections.** The watchdog and the lock fail differently. The watchdog limits how long an orphaned tree can run, but it can be frozen along with the tree. The lock still holds then, and also when the wall clock jumps.
- **A real bug the review found.** Reconnecting inside a transaction would make the rest of it commit statement by statement. The acceptance step could then mark an attempt accepted on a job that is still running. That's why reconnecting is only allowed before a transaction starts.
- **Why the digest goes into the job table.** If it lived only in the run folder, a replaced folder would still carry a self-consistent digest. Recording it inside the acceptance step ties what was accepted to exactly what the cache will serve.
`─────────────────────────────────────────────────`

Your working mode is in the plan. I'll proceed on my own with routine work and pause for design changes, authorship decisions, and approval of the formal experiments. Pushing branches and merging stay with you.

## 161. Assistant — 2026-10-23T11:51:06.259Z

### Tool call: ExitPlanMode

```
{
  "plan": "# Plan: finishing the systems extension (spec §11) in six reviewed milestones\n\nStatus: revision 2, after the author's review on 2026-10-23 and a design check against the code\nand libraries. Nothing is implemented until it is approved.\n\n## Context\n\nStages 1–4 and the extension's job queue are merged into `main` (f058095): PR #7 (job table,\nfencing), PR #8 (Kafka delivery, reconciler), PR #9 (Stage 4). Spec §11 still lists as planned:\n- the real pipeline in the worker (today `SimulatedPipeline`);\n- the recovery experiments E1/E2;\n- the Redis result cache;\n- the cache experiment E3;\n- their documentation.\n\nThis plan turns the author's six-point outline into milestones M1–M6, one branch and PR each. Each\nmilestone has deliverables, acceptance criteria, tests and a statement of how it keeps the\nguarantee. Four cross-cutting requirements run through all of them: code provenance for `jobs/`,\nreproducible dependencies, startup commands, and measured memory budgets. Data verification, the\nprivacy-hook fixes and AI-log review stay in separate workstreams.\n\nState observed on 2026-10-23:\n- the main worktree is on `fix/measure-process-kinds` (97c35f3, pushed, not merged), with\n  uncommitted privacy-hook work (W2);\n- 68 untracked AI-log folders exist;\n- another project's containers share the Docker VM;\n- `gh` is not installed.\n\n## Decisions and working mode (the author, 2026-10-23)\n\n- **Placement.** The worker, reconciler and submit run natively on the host. MySQL and Kafka (and\n  Redis from M4) run in Compose.\n- **Authorship.** The spec §11 split stays.\n  - Claude Code writes M1, M2 and all tooling.\n  - The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.\n- **Six milestones**, as in the outline.\n- **Working mode after approval.** Claude proceeds autonomously with routine work inside each\n  milestone: code, tests, docs, dry runs and commits on the milestone branch.\n- **When Claude pauses and asks.**\n  - **Material design changes:** anything this plan does not describe; any change to the store's\n    guards or SQL beyond the two additive changes in M2.1; any change to the time inequality in\n    M2.4.\n  - **Authorship decisions.**\n  - **Formal experiment approval:** Part A sign-off, and the author running the formal session.\n- **Push and merge.** The author pushes, or tells Claude to push, and opens and merges each PR.\n- **Reports.** Every milestone ends with a report: what was done, what was found and fixed, test\n  counts and measured peaks.\n\n## At a glance\n\n| # | Branch | Written by | Needs | Main deliverable | Done when |\n|---|---|---|---|---|---|\n| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; recursive provenance; `jobs` group; runbook skeleton; peak helper; mutation script | provenance covers `jobs/`; lock only adds; live suite 379 or explained; mutations caught |\n| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline; renewals with monotonic deadlines; watchdog and host lock; tree cleanup; reconnect; store identity; result digest; CLI | crash, stall, timeout and restart cases end with one accepted, correct, digest-bound result and no overlapping Spark trees |\n| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, harness, collector, batch | Part A met; no lost job; no second acceptance |\n| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py`, `runs.py` | M2 | cache-aside keyed by run digest and full query; accepted-run policy; fallback | contract tests pass; same results with Redis down; the run of record is usable through the reviewed registry |\n| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, harness, collector, batch | Part A met |\n| M6 | `docs/extension-report` | Claude drafts; author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |\n\nM4's code can be written while M3's formal session runs (ground rule 6); it does not touch M3's\nfiles.\n\n## Ground rules for every milestone\n\n1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has\n   exactly one, and a job may execute more than once.\n   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it.\n   - **Checking.** `INVARIANT_QUERIES` / `invariant_violations()` (store.py:127, :481) check it\n     after every test scenario, every worker run and every experiment batch.\n   - **Accepting.** Nothing but `JobStore.accept_result` produces an accepted attempt.\n   - **No reconnect inside a transaction** (M2.8). It could break the guarantee: the rest of a\n     transaction would commit statement by statement.\n   - **Cleanup** never touches an accepted or valid active attempt.\n   - **The cache** serves accepted runs only and never writes the job table.\n   - **No overlap.** No replacement Spark work overlaps a surviving earlier process tree (M2.5).\n2. **Authorship.**\n   - For the author's parts, Claude prepares scaffolds (signatures, docstrings, TODOs, contract\n     tests) and reviews, but does not fill them in.\n   - New files carry an `AI contribution:` line.\n   - Experiment documents carry an `Author:` line saying the author wrote Part A and the answers\n     with tutoring, unlike earlier experiments where Claude drafted Part A\n     (caching-experiment.md:56).\n3. **Git.**\n   - Each milestone has its own worktree (`.claude/worktrees/<name>`) from up-to-date `main`, with\n     a `data` symlink to the main worktree's `data/`. M1 changes `.gitignore`'s `/data/` to `/data`\n     so the symlink is ignored too.\n   - Stage files by explicit path only.\n   - Merge with merge commits; never squash or rebase.\n   - Commits end with the Co-Authored-By trailer.\n   - Formal sessions run on a merged, clean commit whose SHA lands in every record, with no\n     commits during a session.\n4. **Privacy.** `data/` and the private plan stay out of Git. Never print memory files,\n   `.git/info/exclude`, app lists, or other projects' container or session names in tool calls.\n   Helpers count other containers without naming them. Child processes get an allowlisted\n   environment, so service URLs and passwords never reach the pipeline steps.\n5. **Measurement sessions.** While one runs, other sessions only write and review. They wait for\n   the explicit end, then check that the worktree is unchanged.\n6. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write \"one process\",\n   never \"one core\". Give each experiment a \"not claimed\" list.\n\n## Cross-cutting requirements\n\n**A. Code provenance for `jobs/`.**\n- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob(\"*.py\")` (provenance.py:62).\n  No record identifies `jobs/*.py` or `jobs/schema/*.sql`, and a plain recursive glob would\n  collide on `__init__.py`.\n- **M1.** Hash every `*.py` and `*.sql` under `src/etf_risk/`, keyed by package-relative POSIX\n  path. Top-level keys stay as they are, so old records remain comparable.\n- **From M2.**\n  - `attempt.json` and every experiment record carry `code_state()`.\n  - Each accepted result is bound to its run digest in the job table (M2.1).\n- **Authorship provenance.** An origin table in `job-queue.md` maps each module → commits\n  (eec1032, e2806bd, cd72957) → PR → the tests that verify it. The `AI contribution:` lines stay.\n\n**B. Reproducible dependencies.**\n- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`\n  (docker/compose.yaml:13; test docstrings) and are not in `uv.lock`.\n- **Groups.**\n  - M1 adds a `jobs` group with these pins.\n  - M2 adds `psutil==7.2.2` to that group; it is already locked through `measure`.\n  - M4 adds a `cache` group with an exact `redis` pin.\n- **Lock changes** may only add packages. numpy 2.5.4, pandas 2.3.3, pyspark 4.2.0, pyarrow 26.0.0\n  and psutil 7.2.2 stay unchanged, checked with a lock diff and `uv lock --check`.\n- **Commands** use `--group …` and `uv sync --frozen`.\n- **Images** are pinned by digest. Redis follows the Kafka rule: the newest release at least two\n  weeks old.\n- **Host tools** are recorded with each formal session (2026-10-23: uv 0.11.16, Java 17.0.10,\n  Docker 28.3.0, Compose v2.38.1, VM 3.83 GiB).\n- **Out of scope:** the NumPy pin.\n\n**C. Startup commands.**\n- **Runbook.** A README section (skeleton in M1, filled by M2, M4 and M6) gives copy-pasteable\n  commands for:\n  - **Setup:** the worktree and `data` symlink; the test services.\n  - **The E1/E2 stack:** Compose `mysql kafka`; then `init-db`, `create-topic`, worker,\n    reconciler, submit and `status`.\n  - **The E3 stack:** Compose `redis`, the query CLI and the warm query service.\n  - **Teardown:** export first, then `down -v`.\n- **Readiness.** A service is ready only after a check that matches what will use it:\n  - MySQL: a login plus `SELECT 1` (its healthcheck answers before logins work,\n    docker/compose.yaml:35);\n  - Kafka: the batch topic's metadata and the group coordinator are available;\n  - Redis: `PING`.\n- **Acceptance.** The commands are run exactly as written in a fresh worktree.\n\n**D. Measured memory budgets.** The spec §11 ledger records component, limit, measured peak,\nmethod, date and commit.\n\n| Component | Budget | Measured | Source |\n|---|---|---|---|\n| MySQL container | 512 MiB | 324–398 MiB fresh; 472 after two runs; 511 after ~2 h | spec §11 |\n| Kafka container | 640 MiB | 354–478 MiB; 516 with mutation checks | spec §11 |\n| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB, stride 21 | spec §11 |\n| Native stride-21 tree | `measure` stop 4.8 GiB | 1.27 GiB with 1.3–1.6 GiB free; 2.62–2.73 GiB with 3.0–3.5 GiB free | spec §8, experiments.md |\n| Native calendar-year tree | — | not measured (M2) | |\n| Worker, reconciler, submit | from M2 dry runs | — | |\n| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |\n| Warm query service | from M4 dry runs | — | |\n\n- **Budgets** are set at the review gate from dry runs, then checked; never from the run that\n  checks them.\n- **Container peaks** come from cgroup `memory.peak` through a helper (M1). They are read before\n  every injected restart, since a restart may reset them; M2 verifies whether it does.\n- **Native peaks** come from a marker-based sampler (M2). `TreeSampler` misses processes that were\n  re-parented to launchd.\n- **Before any formal session or budget measurement:**\n  - zero containers outside this project (counted, not named);\n  - ports 3307, 9094 and 6380 free;\n  - host available memory at or above the Part A threshold.\n- **Each recovery batch** starts on a fresh MySQL container with a fresh topic and consumer group.\n- **A budget exceeded** stops the session.\n\n## Milestones (numbered as in the outline)\n\n### M1 — Read the whole project; bring the code up to date\nBranch `feature/extension-baseline` · Claude Code · after `fix/measure-process-kinds` is merged.\n\n**Audit.** The report lists the following. Items inside this plan are fixed as routine work;\nanything else waits for the author.\n- **Reproducibility:**\n  - gaps A, B and C;\n  - the 22 mutation checks exist only as prose;\n  - the merged worktrees `job-queue` and `job-table` are clean, so they can be removed.\n- **Missing operations:**\n  - no entry point in `jobs/` (the §11 \"submit CLI\" does not exist);\n  - logging is never configured;\n  - nothing is timed;\n  - `published_at` is cleared by the claim;\n  - a crash before the claim leaves no trace;\n  - Kafka group timings are unpinned defaults while `serve()` runs the pipeline inside its poll\n    loop;\n  - **no reconnect:** `JobStore` keeps one connection for life (store.py:286-292, 526), so after a\n    MySQL restart the reconciler fails every pass and `serve()` raises after 5 retries;\n  - no supervisor.\n- **Pipeline CLIs** (findings only; the worker works around them in M2.3):\n  - exit 1 means both \"checks failed\" or \"mismatch\" and any uncaught exception;\n  - `run.json` is written only in `finally`;\n  - verify misses `JSONDecodeError`;\n  - verify's `spark.stop()` is not in a `finally`;\n  - paths are relative to the working directory: `--processed-root` and verify's `windows_dir`;\n  - windows refuses only an existing `config.json`, while README:224 says an existing folder.\n- **Documentation drift:**\n  - job-table.md's claim SQL and \"apart from submit\";\n  - job-queue.md:90;\n  - dated status blocks in job-table.md:97-103 and job-queue.md:146-160;\n  - spec §5's diagram, its \"Every box is implemented\", and its E2–E4 node ids;\n  - spec.md has no AI header.\n- **Test helpers:** `WorkerEnv.check` is tied to the simulated `result.json`.\n\n**Fixes:**\n- provenance (A);\n- the `jobs` group and `--group jobs` everywhere (B);\n- `.gitignore` `/data/` → `/data`;\n- the runbook skeleton (C);\n- the `memory.peak` helper (D);\n- job-doc drift and stale status;\n- the module origin table;\n- a mutation-check script: each mutation a patch applied in a scratch worktree with a timeout.\n  The list is rebuilt from the surviving descriptions (job-table.md:98-102, job-queue.md:157-164,\n  e2806bd's message) and documented as rebuilt, not claimed identical to the original 22;\n- removal of the merged worktrees.\n\nThe pipeline CLIs and the analysis code are not changed.\n\n**Revalidation:** the offline suite; the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with\n`--group jobs`; the mutation script; peaks through the helper.\n\n**Acceptance.**\n- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in\n  `source_sha256` under a unique key, with top-level keys unchanged.\n- The lock diff only adds packages.\n- The live suite passes with 379 cases, or the difference is explained.\n- Every rebuilt mutation fails a test within its timeout.\n- Peaks are within budget.\n\n**Tests:** new cases in `test_provenance.py`; job suites on SQLite and live; the mutation script.\n\n**Guarantee:** no store change; the mutation script re-proves that each guard is tested.\n\n### M2 — The worker runs windows → spark_pipeline → verify\nBranch `feature/worker-pipeline` · Claude Code · after M1. Two stages in one PR, with a progress\nreport between them (not a pause):\n- **M2a:** M2.1, M2.8, M2.9, M2.10 and the CLI, exercised with the simulated pipeline.\n- **M2b:** M2.2–M2.7, the real pipeline.\n\n#### M2.1 Identity: store, output layout, result digest\n- **Store identity.**\n  - `init-db` creates a one-row table `job_store` (`store_id`, a random 128-bit hex; `created_at`;\n    `schema_version`).\n  - Job and attempt ids repeat after a database is recreated, so everything outside the database\n    uses `store_id` with them: output paths, process markers, events and cache provenance.\n- **Output layout.**\n  - The worker passes `output_root/<store_id>` to `claim()`, giving folders\n    `<root>/<store_id>/job-<id>-attempt-<n>/`.\n  - The store already builds the path from the given root (store.py:356), so the store needs no\n    change for this.\n  - A recreated database never collides with old folders, which today would fail every job\n    (worker.py:128-132).\n- **Run digest.**\n  - `src/etf_risk/runs.py` (new; shared with M4) writes a canonical manifest of the Spark run\n    folder: sorted relative paths, sizes and SHA-256 per file.\n  - Its SHA-256 is the run digest, the run's immutable identity.\n  - The worker writes `manifest.json` in the attempt folder before acceptance.\n- **Bound at acceptance** (additive store change; the guards are unchanged):\n  - `job_attempts.result_digest CHAR(64)` with a CHECK `(outcome = 'accepted') = (result_digest\n    IS NOT NULL)`;\n  - `accept_result(claim, digest)` sets it in its existing `job_attempts` update, inside the same\n    token-guarded transaction (store.py:398-402);\n  - the idempotent repeat path also compares the digest;\n  - both schema files, the drift test and the invariant queries are updated.\n\n  This ties the accepted decision and the accepted content together atomically.\n- **Simulated pipeline.** `SimulatedPipeline` produces a digest too, so all existing scenarios\n  keep running.\n\n#### M2.2 Steps and environment\n- **Steps.** Each step runs behind the launcher (M2.5) as `sys.executable -m etf_risk.<module>`,\n  with absolute paths only:\n  1. `windows --snapshot … --kind … --window-days … --stride … --anchor … --processed-root <abs>\n     --out-root <run_dir>/windows --name <name>`;\n  2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>`;\n  3. `verify --run …`.\n- **Job parameters** (`params.py`, a frozen dataclass): snapshot, kind, window days, stride,\n  anchor, sample ticker. Unknown keys are refused.\n- **Worker settings:** the processed root and the output root, both recorded in\n  `attempt.json`.\n- **Input checksums.** `submit` computes `input_checksums` from the files `windows.py` records in\n  `inputs_sha256`. The worker re-checks them before step 1; a mismatch is not retryable.\n- **Step environment** (allowlisted):\n  - `cwd` = `<run_dir>/.work`, which also catches `spark-warehouse`;\n  - `TMPDIR` = `.work/tmp`;\n  - `SPARK_LOCAL_DIRS` = `.work/spark`;\n  - `SPARK_SUBMIT_OPTS=\"-Djava.io.tmpdir=<abs>/.work/jtmp -XX:-UsePerfData\"`, which the Spark\n    launcher reads. The macOS JDK ignores `TMPDIR`.\n  - `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` = `sys.executable`. Otherwise workers use\n    `python3` from PATH (pyspark/core/context.py:342).\n  - Never `JAVA_TOOL_OPTIONS` or `_JAVA_OPTIONS`: their \"Picked up …\" notice would replace the\n    Java version that `environment()` records (spark_pipeline.py:635-636). A test checks\n    `run.json`'s `java` field.\n  - The directories are created first.\n  - Logs go to `<run_dir>/logs/<step>.log`.\n\n#### M2.3 Acceptance rule and failure classification\n- **Accept only if all hold:**\n  - every step exits 0;\n  - `run.json` status is `ok`;\n  - every `checks.json` count is 0;\n  - `verify.json` has no mismatch and the same breached windows;\n  - every table has `_SUCCESS`.\n- **Then:**\n  1. remove `.work`;\n  2. write `attempt.json`;\n  3. write `manifest.json`;\n  4. **renew**;\n  5. `accept_result(claim, digest)`.\n\n  Nothing in the folder changes after acceptance; a test compares the manifest before and after.\n- **Classification**, decided from the records, never from the exit code alone:\n  - **not retryable:** a checksum error (exit 3); `run.json` status `checks_failed`; a verify\n    mismatch; a parameter or input-checksum error;\n  - **retryable:** a signal, a timeout, status `failed`, a missing record, or \"execution lock\n    busy\" (M2.5).\n\n  Retryable failures requeue until `max_attempts`.\n\n#### M2.4 Time, deadlines and bounded operations\n- **Clocks.** Lease times in the database stay on the store's wall clock (UTC), which all\n  processes on this host share. Every local deadline uses `time.monotonic()`:\n  - self-fence;\n  - watchdog;\n  - timeouts;\n  - lock waits;\n  - operation budgets;\n  - backoff.\n\n  Event logs record UTC (shared across processes) and monotonic offsets (durations within one\n  process).\n- **Bounded database operations** (draft values, fixed at review from M2a measurements):\n  - **Session settings:** `connect_timeout` 3 s, `read_timeout` 5 s and `write_timeout` 5 s\n    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`\n    2 s, which is below the read timeout, so lock waits end as definite 1205 conflicts; session\n    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks\n    indefinitely.\n  - **Conflict retries:** the existing `CONFLICT_RETRIES` = 3 runs.\n  - **Operation budget:** B = 8 s on the monotonic clock, checked before each statement and each\n    retry; past it the operation raises without starting another statement.\n  - **Worst case:** one operation takes at most **W = B + 5 s = 13 s**.\n- **Kill grace.** G = 5 s SIGTERM + 2 s for SIGKILL to be confirmed = **7 s**.\n- **Renewal loop** (the worker thread):\n  - waits on the launcher with `wait(timeout=1 s)`;\n  - renews every 10 s;\n  - checks the self-fence deadline on every tick and after every renewal, success or not. The\n    deadline is `F = m₀ + L − M`, where `m₀` is the monotonic time just *before* the last\n    successful renewal started (the database lease began at or after `m₀`), with L = 60 s\n    (`DEFAULT_LEASE`) and **M = 25 s**;\n  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5). The\n    worker's end of that pipe is non-blocking. If the pipe is full because the launcher is\n    frozen, the message is dropped, which can only make the watchdog act sooner.\n- **The inequality.** The longest gap between two deadline checks is W (one blocked store call).\n  Termination then takes G. The tree is therefore gone by `F + W + G = m₀ + L − M + 20 s`, which\n  is before the lease can expire (`m₀ + L`) whenever **M ≥ W + G**. The drafts give 25 ≥ 20, with\n  5 s to spare. Changing any value requires restating this inequality, and that is a pause point.\n- **No other blocking calls during a run.** From the renewal before step 1 to acceptance, the\n  worker thread makes only bounded store calls and bounded waits; it makes no Kafka calls.\n  - Kafka is used only between runs. `socket.timeout.ms` is pinned at 10 s.\n  - A commit that blocks before a run cannot cause overlap: the renewal before each step returns\n    false if the job was taken over meanwhile, and the step never starts.\n- **Retry rules:**\n  - `renew`: retried at the next interval;\n  - `accept_result` and `fail_attempt`: retried on disconnects only, until F; `accept_result` is\n    idempotent for its token;\n  - `claim`: raises into `serve()`'s rewind and retry;\n  - `submit`: never retried; the CLI exits with a distinct \"outcome unknown\" code;\n  - reconciler passes: bounded, logged and repeated.\n\n#### M2.5 No overlapping Spark work: watchdog and host execution lock\nA SIGSTOPped worker can neither renew nor check its deadline, and its pipe to the launcher stays\nopen. Two independent layers therefore protect against overlap, in addition to the worker's own\nself-fence.\n- **Watchdog (the launcher process, one per step).**\n  - The worker starts the launcher with `start_new_session=True` and a keepalive pipe as its\n    stdin.\n  - The launcher keeps a monotonic deadline. It starts from the value sent after the\n    renewal-before-step and is extended only by the worker's \"remaining time\" messages.\n  - It terminates its tree (M2.6) on EOF (the worker died) or when the deadline passes (the\n    worker is frozen, stuck or fenced by its own clock). Either way the tree is gone by\n    F + G, before the lease can expire, without any action by the worker.\n- **Host execution lock.**\n  - Before starting a step, every launcher takes an exclusive `flock` on a host-wide file\n    (default `~/.cache/etf-risk/locks/spark-exec.lock`; tests use their own path).\n  - It then checks that no process carrying another attempt's marker survives (M2.6).\n  - It passes the lock descriptor to the step's driver, so the lock is held while the launcher\n    or the driver lives. PySpark closes inherited descriptors for the JVM, and the JVM exits when\n    the driver's pipe breaks; the survivor check covers that window.\n  - A launcher that cannot get the lock, or still sees survivors, within the lock-wait bound\n    (step limit + G + 30 s) does not start Spark. It exits with \"execution lock busy\", and the\n    attempt fails as retryable.\n  - So even when the whole old tree is frozen (watchdog included) or the wall clock jumps, no\n    replacement Spark run starts while an earlier tree survives. The session harness takes the\n    same lock for its reference runs.\n- **Renewal before each step and before acceptance.** A fenced worker never starts a new step.\n\n#### M2.6 Terminating a process tree\n- **Why not a group kill.** PySpark's daemon calls `os.setpgid(0, 0)` (pyspark/daemon.py:115),\n  so its workers leave the step's group, and re-parented orphans escape child-walks.\n- **Membership.** Every step process carries the marker\n  `ETF_RISK_ATTEMPT=<store_id>:<run id>:<attempt key>`, where the attempt key is the first 16 hex\n  digits of SHA-256(token). The token itself never leaves the worker. Members are found by session\n  id (`os.getsid` = the launcher's pid; nothing in the tree calls `setsid`) as a prefilter,\n  confirmed by the marker. A pid alone is never enough.\n- **Sequence.** SIGTERM to all members (so the JVM can delete its scratch); wait 5 s; SIGKILL to\n  survivors; rescan until none remain (bounded). The pids and the reason go to\n  `logs/launcher.log`.\n\n#### M2.7 Startup sweep: preserve valid active attempts\nWhen a worker starts, it scans this host for marked process trees of its own `store_id` and looks\neach attempt up in the store.\n- **Preserved:** any tree whose attempt is still *valid active*, meaning the job is running and\n  its current attempt number and token hash match. Its lease or watchdog decides when it ends;\n  the sweep never shortens a valid attempt.\n- **Terminated:** trees whose attempt has ended (expired, failed or accepted) or was taken over.\n- **Ended attempts' folders:** their `.work` scratch is removed; the folder itself never is.\n- **Left alone and reported:** trees of other store ids.\n- **Database unreachable:** the sweep does nothing.\n- **Folder listing.** `jobs cleanup` is dry-run only: it lists the folders of ended,\n  non-accepted attempts. Deleting them is not part of M2.\n\n#### M2.8 Database connections\n- **Factory.** `JobStore` accepts a connection factory: `connect_mysql` with the M2.4 timeouts and\n  session settings. It never uses `ping(reconnect=True)`, which drops `SET SESSION`.\n- **Reconnect only at the start of an operation:** before BEGIN, after a ping when the connection\n  has been idle for 60 s or more. Never inside a transaction. A connection that broke\n  mid-transaction is discarded; the transaction's remaining statements never run on a new\n  connection.\n- **Disconnects:** PyMySQL 2003, 2006, 2013, server codes 1053, 1927 and 4031, `InterfaceError`,\n  or `open == False` after an error. The connection is marked broken in the except path, before\n  the ROLLBACK.\n- **No ROLLBACK on a broken connection.** The store closes it instead; the server rolls back the\n  open transaction when the session ends. No statement then runs after the operation budget, so\n  W holds. A COMMIT that timed out may still have taken effect on the server, which is the\n  existing \"failed COMMIT\" case, handled by idempotent repeats.\n- **No replay.** The failed operation raises, as today.\n\n#### M2.9 Kafka settings (pinned in `kafka.py`, with tests on values and relations)\n| Setting | Value | Why |\n|---|---|---|\n| `group.protocol` | `classic` | `session.timeout.ms` is ignored under `consumer` |\n| `heartbeat.interval.ms` | 3000 | pinned default |\n| `session.timeout.ms` | 15000 | ≥ the broker's 6 s minimum, ≥ 3 heartbeats, < L |\n| `max.poll.interval.ms` | attempt limit + G + 60 s | a legitimate run never leaves the group |\n| `socket.timeout.ms` | 10000 | bounded commits and fetches |\n- **Max-poll error.** It gets its own event.\n- **Graceful stop** closes the consumer, so the group sees an immediate LeaveGroup.\n- **Consequence for E2.** Under the classic protocol, a joining standby or restarted worker waits\n  for a busy member to poll, and E2's recovery times include that wait.\n\n#### M2.10 Supervision, graceful stop, events, CLI\n- **Supervision.**\n  - `jobs worker` restarts its serve loop in-process, with backoff, after transport errors only:\n    disconnects, `ClaimRace`, non-fatal Kafka errors. Any other error exits non-zero.\n  - SIGKILLed workers are restarted by the M3 harness after a Part A delay.\n- **Graceful stop** (SIGTERM or SIGINT): stop polling, terminate the running tree, call\n  `fail_attempt(retryable=True)`, close the consumer. On a job's last attempt this fails the job\n  (store.py:416-417), so batches drain before stopping workers.\n- **Event log.** Each process writes JSON lines, flushed per event:\n  - delivered, claimed;\n  - renewed, renewal failed;\n  - step start and end, lock wait;\n  - watchdog kill, fenced;\n  - accepted, failed, requeued, published;\n  - max-poll.\n- **Attempt record.** `attempt.json` holds the worker id, store id, run id, steps (exit code,\n  times), the input checksums as checked, the settings and `code_state()`.\n- **CLI** `python -m etf_risk.jobs`:\n  - `init-db`, `create-topic`, `submit`, `worker`, `reconciler`;\n  - `cleanup` (dry run);\n  - `status [--check]`: tables and `invariant_violations()`; exits 1 on a violation;\n  - `export <dir>`: tables, violations and settings, for M3's batches.\n\n**Deliverables.**\n- **New modules:** `jobs/{pipeline,launcher,processes,params,events,__main__}.py` and\n  `src/etf_risk/runs.py`.\n- **Changes:** `store.py` (factory, budget, digest, store id), `mysql.py` (timeouts, `is_disconnect`),\n  `kafka.py` (settings), both schema files.\n- **Docs:** `job-queue.md` and `job-table.md` updated; the runbook's E1/E2 part.\n- **Ledger rows:** idle available memory with the stack up; per-step peaks for calendar-year and\n  stride 21; the Docker VM process's memory on the host.\n\n**Acceptance** (native worker; MySQL and Kafka in Compose; fresh containers):\n- **Normal runs.** A calendar-year job and a stride-21 job (no injection, no timing claims) end\n  `succeeded`. Each has exactly one accepted attempt whose recorded digest equals its manifest.\n  Each passes every check and verify. Each equals a direct CLI run by content, using the caching\n  collector's `TABLE_KEYS` (collect_caching_measurements.py:74-75) and `compare_tables`\n  (collect_partition_measurements.py:286), with `windows.parquet` compared by its window key.\n- **Worker-only SIGSTOP during step 2.** Checked *before SIGCONT*:\n  - no process of attempt 1 is alive by its watchdog deadline + G;\n  - the lock is free;\n  - attempt 2's Spark step started after attempt 1's last process exited (event times and the\n    process scan);\n  - attempt 1's renewal count is unchanged after attempt 2's claim.\n\n  After SIGCONT, the old worker is fenced and writes nothing.\n- **Whole-tree SIGSTOP** (worker, launcher and Spark). Checked *before SIGCONT*:\n  - the replacement started no Spark process;\n  - it waited on the lock or exited \"execution lock busy\";\n  - no second Spark tree exists; the only one is the frozen tree.\n\n  After SIGCONT, the old launcher terminates its tree at once, because its deadline has passed.\n  The job ends with exactly one accepted result.\n- **Worker SIGKILL during step 2.** No attempt process survives the lifeline grace, and the job\n  is requeued after its lease and succeeds.\n- **Timeouts.** An over-limit step is terminated and retried.\n- **Database stalls.** `LOCK TABLES jobs WRITE` from another session, `docker compose pause mysql`,\n  and `restart mysql`, each during a run:\n  - every store operation stays within W (measured);\n  - the run either continues or self-fences before its lease;\n  - nothing needs a manual restart;\n  - the job ends with one accepted result.\n- **Kafka restart during a run.** The same outcome.\n- **Startup sweep.** It terminates only ended attempts' trees, and preserves a live attempt run by\n  another worker.\n- **No leftovers.** The process scan shows no attempt processes. No new `spark-*`, `blockmgr-*`,\n  `pyspark-*`, `snappy-*`, `libzstd-jni*`, `liblz4-java*` or hsperfdata entries appear in\n  `/private/tmp` or `getconf DARWIN_USER_TEMP_DIR`. No new `spark-warehouse` appears in the\n  repository.\n- **Invariants.** `invariant_violations()` is always empty.\n- **Earlier tests.** All earlier job tests pass on both stores.\n\n**Tests.**\n- **Offline:**\n  - **launcher:** deadline kill; EOF kill; lock wait and refusal; survivor check; exit codes;\n  - **tree termination:** a grandchild that calls `setpgid(0, 0)`, and a double-fork orphan; none\n    survives a worker SIGKILL, a fence, a timeout or a worker-only SIGSTOP;\n  - **deadlines:** a fake store blocking W per call. The tree is gone before `m₀ + L`; no step\n    starts after F; the watchdog still ends the tree when the worker thread blocks beyond W;\n  - **sweep:** the rules of M2.7;\n  - **reconnect:**\n    - a disconnect between statements 1 and 2 never runs statement 2 on a new connection;\n    - a COMMIT that took effect but whose reply was lost: a repeated accept returns True, with\n      exactly one accepted attempt;\n    - session settings after a reconnect;\n    - the ping before an operation;\n  - **classification, parameters, checksums;** the environment allowlist (no service URL in a\n    step's environment); the `java` field;\n  - **digest and store identity:** manifest determinism, the CHECK, the drift test;\n  - **Kafka settings and their relations.**\n- **Spark-marked:** a tiny job on a `write_snapshot` snapshot (tests/conftest.py) through\n  `Worker` with SQLite and `MemoryQueue`.\n- **Live** (gated by `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP`):\n  - the acceptance cases above;\n  - a standby that receives the next message only after the primary exceeds a short\n    `max.poll.interval.ms`;\n  - store-operation durations recorded and checked against W.\n- **Mutation script:** three new mutations — a reconnect inside a transaction, disconnects treated\n  as conflicts, and `ping(reconnect=True)` in place of the factory.\n\n**Guarantee.**\n- Acceptance still goes only through the token guard, now also binding the digest.\n- Self-fence, watchdog and lock only stop or delay work.\n- The sweep and `cleanup` never touch valid or accepted attempts.\n\n**Deferred.** A unique index on accepted attempts. E1 measures whether the token guards alone\nkeep the guarantee, so this is decided after M3, in M6.\n\n### M3 — Recovery experiments E1 and E2\nBranch `feature/recovery-experiment` · Tooling Claude Code · Experiment: the project author,\ntutored · after M2.\n\n**Claude's tooling.**\n- **Session harness.** One process starts the worker(s), the standby and the reconciler, performs\n  injections, restarts crashed workers after the Part A delay, and logs everything (UTC, from the\n  host clock).\n- **Injections:**\n  - crashes at `WORKER_FAULT_POINTS` (worker.py:54-59), carried out as a real SIGKILL and fired\n    once per job (recorded in the events and `attempt.json`);\n  - SIGKILL during a step;\n  - SIGSTOP and SIGCONT of the worker alone or of the whole tree, always from the wait loop and\n    never inside a transaction;\n  - `docker compose restart` of Kafka or MySQL at a chosen phase;\n  - holding a worker at `after_pipeline` while MySQL restarts.\n- **Batch lifecycle:**\n  - a fresh MySQL container, store id, topic and consumer group;\n  - reference runs (direct CLI, same commit, under the host lock);\n  - drain at the end;\n  - `jobs export` and `memory.peak` before `down -v`. The collector reads files only.\n- **Session helpers** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:\n  machine checks adapted to Docker running, with the memory threshold from M2's dry runs; two\n  windows; `case n`; watcher; abort; note.\n- **Collector** `analysis/collect_recovery_measurements.py --batch`:\n  - imports `compare_tables` unchanged;\n  - writes `measurements.csv` and `acceptance.json`, with criteria 1–5 plus \"6 guarantee\";\n  - exits 1 on any failure.\n- **Batches** live in `data/outputs-recovery/<batch>/`.\n\n**The author's `docs/recovery-experiment.md`.** Claude scaffolds Parts A and B, History and the\n`Author:` line.\n- **Part A, decided by the author:**\n  - the cases;\n  - repetitions;\n  - the job size: the recommendation is calendar-year for every case, with stride 21 only in M2;\n  - lease, renewal, reconcile and restart-delay settings;\n  - `--max-attempts`;\n  - deadlines per case: lease + reconcile interval + publication grace + session timeout +\n    restart delay + attempts left × attempt limit;\n  - memory thresholds: suggested peak + 0.5 GiB free; with the host lock, at most one tree runs;\n  - metric definitions;\n  - predictions;\n  - acceptance criteria;\n  - stop rules.\n- **Draft cases:**\n  - a crash at each worker fault point, and during step 2;\n  - a worker-only stall and a whole-tree stall;\n  - Kafka restart while idle, during a submit, and during a run;\n  - MySQL restart during a run, shorter and longer than M (the self-fence margin);\n  - MySQL restart while held at `after_pipeline`: one execution predicted if MySQL is back before\n    F, two otherwise.\n- **Metrics per job:**\n  - injection time;\n  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;\n  - recovery: the next `claimed_at`;\n  - completion: `finished_at`;\n  - executions;\n  - **number** of accepted attempts;\n  - correctness: checks, plus content against the reference, plus digest;\n  - category: succeeded, failed (attempts exhausted), lost (not terminal by the deadline), or\n    submit outcome unknown.\n- **E1 cross-check.** The author's own SQL for accepted attempts per job must agree with\n  `invariant_violations()`.\n\n**Acceptance.**\n- One batch meets every Part A criterion.\n- Across all batches: zero lost jobs, zero jobs with two accepted results, and exactly one\n  correct, digest-bound accepted result per succeeded job.\n- Peaks are recorded per batch.\n- Commits follow the precedent: tooling → Part A (before any measured run, author-approved) →\n  dry batches → the formal session (the author) → Part B → status.\n\n**Tests:** harness, collector and helper tests in the pattern of `test_caching_collector.py` and\n`test_caching_session.py`, including planted problems, each failing its criterion.\n\n**Guarantee:** measured under failures; no new write path.\n\n### M4 — Redis cache for summary queries, with fallback\nBranch `feature/result-cache` · Infrastructure Claude Code · Cache logic: the project author,\ntutored · after M2.\n\n**Identity**, the contract the author's key must meet (the tests pin it):\n- **Run identity is the run digest** (M2.1), never the run id or path. Job and run ids repeat\n  after a database is recreated, and paths can be reused.\n- **The key** covers:\n  - the cache format version;\n  - the engine (PySpark version);\n  - the run digest;\n  - the query name;\n  - the query definition hash (SHA-256 of its SQL text);\n  - the canonical full parameters: every parameter including defaults, in canonical JSON with\n    sorted keys and normalized types.\n\n  The key is a hash of that tuple behind a readable prefix. The stored value repeats the tuple,\n  and a mismatch on read counts as a miss.\n- **Pinned by tests:**\n  - equal run ids with different digests never share a key;\n  - a changed parameter or SQL text changes the key;\n  - equal requests give equal keys across processes.\n\n**Accepted-run policy** (`runs.py` resolver, Claude). A run is servable only if one of the\nfollowing holds; anything else is refused, with no fallback to unaccepted runs.\n- **(a) A job run.** In the job table, under its `store_id`, the job is succeeded and its accepted\n  attempt's recorded `result_digest` equals the folder's manifest digest.\n- **(b) A historical run.** The reviewed registry `docs/accepted-runs.json` (committed) lists it\n  with path, digest, the basis for acceptance (`run.json` status ok, all checks 0, `verify.json`\n  clean, the spec §8 reference) and the author's approval date. The folder's digest must match.\n  - `python -m etf_risk.runs register` computes and checks the entry. The digest is stored in the\n    registry, so the historical folder is never written to.\n  - This lets M4 and E3 use the run of record without creating job rows outside\n    `accept_result`.\n  - **Pause, an authorship decision:** which run to register. `run-20261013T043848Z-4` has a clean\n    `verify.json`. The documented `-2` has none, and registering it would mean running verify into\n    it first. The four runs' tables are identical (plots.py:15-16).\n\n**Per-query check.** Each query compares file sizes and modification times against the manifest\nand fully re-hashes on any mismatch. `serve` re-hashes at startup, and `--verify-full` re-hashes\non demand. E3 reports the resolver's cost separately.\n\n**Claude's part.**\n- **Compose `redis`:**\n  - pinned by digest;\n  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, persistence off;\n  - 128m `mem_limit` and `memswap_limit`;\n  - port `127.0.0.1:6380`;\n  - a `PING` healthcheck.\n- **The `cache` group.**\n- **`src/etf_risk/summary.py`:**\n  - named queries over `paired/`. The author moves their own SQL from `analysis/sql_*.py`; those\n    scripts are not edited (documents cite them by hash), and moving the SQL is an authorship\n    step;\n  - a one-shot CLI (new process) and a warm mode (one SparkSession, JSON-lines requests on stdin\n    and stdout);\n  - the resolver and the registry tool;\n  - contract tests and fakes: a Redis stand-in that can go \"down\", and a live fixture gated by\n    `ETF_RISK_REDIS_URL`;\n  - a Spark-marked test that the queries on the registered run reproduce spec §8 (windows 529,\n    466, 311, 174, 310), skipped without `data/`.\n\n**The author's part.** `src/etf_risk/cache.py`, scaffolded:\n- the key and normalization, under the identity contract;\n- serialization;\n- cache-aside get-or-compute;\n- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while\n  Redis is down, decode errors treated as misses;\n- counters.\n\n**Acceptance.**\n- Contract tests pass offline and live.\n- With Redis stopped, every query returns the Spark result, within the timeout and breaker bound.\n- Unaccepted, unregistered or changed runs are refused.\n- Redis peak ≤ 128 MiB.\n- The runbook's E3 commands work as written.\n\n**Tests:** the identity tests above; resolver refusals (a non-accepted attempt; a digest mismatch;\nan unregistered historical run); fallback; equal results; live Redis; the spec §8 test.\n\n**Guarantee:** reads accepted runs only, verified by digest; never writes the job table.\n\n### M5 — E3: new Spark process vs warm Spark session vs Redis\nBranch `feature/result-cache-experiment` · Tooling Claude Code · Experiment: the project author,\ntutored · after M4.\n\n**Configurations** (Part A):\n- N: a new process per query;\n- W: a warm session, with no cache;\n- R: a warm session plus Redis, at hit rates set by repeats (e.g. 0, 50 and 90%);\n- F: Redis stopped, then recovered.\n\n**Key space.** Queries × accepted runs (the registered run of record and M2/M3 job runs) × any\nparameters the author adds.\n\n**Measures:**\n- client-side monotonic latency per query;\n- the resolver's cost, separately;\n- realized vs designed hit rate;\n- the warm session's process-tree peak (marker sampler);\n- Redis `memory.peak` and `used_memory_peak`.\n\n**Deliverables:** `docs/result-cache-experiment.md`, `docs/result-cache-session.zsh`,\n`analysis/collect_result_cache_measurements.py`, and a batch in\n`data/outputs-result-cache/<batch>/`.\n\n**Acceptance:** one batch meets every Part A criterion; drift is reported.\n\n**Tests:** collector (planted problems), session helpers, and the hit rate the workload generator\nproduces.\n\n**Guarantee:** read-only for the job table.\n\n### M6 — Architecture, report and demo\nBranch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · after M3\nand M5.\n\n- **`docs/architecture.md`** (new). It covers:\n  - batch pipeline plus extension;\n  - native vs Compose placement;\n  - failure model, guarantee and where it is enforced and checked;\n  - time and deadline rules (M2.4–M2.5);\n  - cache identity and the accepted-run policy;\n  - budget ledger;\n  - runbook.\n- **Spec §5's diagram:** gains `jobs/` and Compose, and its node ids are renamed.\n- **Figures X5 (E1/E2) and X6 (E3)**, added together as X1–X4 were:\n  - `plots.py` (`FIGURES`, `DOCUMENTED`, the tuple in `compare_documented`);\n  - `test_plots.py` (12 → 14);\n  - CSV copies and their README rows;\n  - every \"twelve figures\" and \"X1–X4\" mention.\n- **Spec:** §8 \"What the recovery experiments showed\" and \"What the result-cache experiment\n  showed\"; §9 and §11 marked implemented, with the final ledger.\n- **`results.md`:** a new extension section. §7 changes only with the author's re-approval.\n- **README:** status and the full runbook.\n- **`demo.md`:** submit; kill the worker mid-run; watch `status --check` recover; cache miss →\n  hit → Redis stopped → fallback → restart.\n- **The deferred unique-index decision.**\n\n**Acceptance:**\n- numbers traced to committed CSVs and records;\n- `plots --check` passes;\n- every command run as written in a fresh worktree;\n- links valid;\n- the author approves the conclusions.\n\n**Tests:** `test_plots.py`; a link check; the full offline suite.\n\n**Guarantee:** documentation only.\n\n## Separate workstreams (outside M1–M6)\n\nNo milestone branch touches these files, and no milestone waits on them.\n\n- **W1 Data verification** (`feature/data-verification`, own plan):\n  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);\n  - terms of use;\n  - the cause of the Adj Close steps;\n  - the 36 unverified days;\n  - data-sources.md's missing AI header.\n- **W2 Privacy-hook fixes** (`fix/transcript-privacy`): the uncommitted hook, test and transcript\n  edits, plus spec §10's hook items. Claude touches the hook only when asked.\n- **W3 AI-log review.**\n  - **Scope:** the 68 untracked folders (including the sessions behind PRs #7–#9) and each\n    milestone's logs.\n  - **Reviewer:** the author.\n  - **Where commits go:** following the precedent, each review lands as a separate \"Add reviewed\n    AI logs for …\" commit, last on the milestone branch (ed71796). Logs reviewed after a merge go\n    on a `docs/ai-logs-<date>` branch.\n  - **Never mixed with code.**\n  - **Also in scope:** `docs/ai-usage/README.md`'s attribution of the hook to Codex only, and the\n    redaction of other projects' names that appeared in this planning session's tool output.\n\n## Verification (end to end)\n\n- **Per milestone:**\n  - the offline suite (`uv run --group measure --group plots pytest`) with counts;\n  - Spark-marked tests;\n  - live suites on fresh containers (`--group jobs`, `--group cache`);\n  - `status --check` empty after every live run;\n  - the mutation script;\n  - the lock diff;\n  - measured peaks against the ledger.\n- **System, after M6:** in a fresh worktree on `main`, follow the runbook from\n  `uv sync --frozen` through smoke runs of E1/E2 and E3. Check that:\n  - every accepted run passes its checks, matches its reference by content, and matches its\n    recorded digest;\n  - no overlapping Spark trees appear in the event logs;\n  - `plots --check` passes;\n  - peaks are within the ledger.\n\n## Known pause points\n\n- **M2:** any change to the M2.4 values that breaks or restates M ≥ W + G; any store change beyond\n  `job_store` and `result_digest`.\n- **M3:** Part A approval (cases, job size, thresholds, deadlines); the author runs the formal\n  session.\n- **M4:** the author writes `cache.py` and moves their SQL into `summary.py`; the choice of which\n  historical run to register.\n- **M5:** Part A approval; the formal session.\n- **M6:** the conclusions' wording; the unique-index decision.\n",
  "planFilePath": "~/.claude/plans/please-turn-this-outline-cozy-candy.md"
}
```

## 162. User — 2026-10-23T12:14:03.640Z

### Tool result (error)

```
The user doesn't want to proceed with this tool use. The tool use was rejected (eg. if it was a file edit, the new_string was NOT written to the file). The user provided the following reason for the rejection:  The revised structure looks good. Approved to proceed with M1 once its prerequisite is merged.

Before implementing M2, resolve two timing details:

1. Send absolute monotonic deadlines to the launcher, rather than remaining durations. Buffered keepalive messages must never revive an expired watchdog. Add a pause/resume test with queued stale messages.

2. Revise the claimed W = 13-second database-operation bound. Separate read/write timeouts do not establish that whole-operation limit, especially with reconnect, multiple I/O operations and rollback. Either establish an enforceable bound or make execution safety rely explicitly on the independent watchdog and host lock.

Keep the six milestones and proceed with routine M1 work without another planning round. Report these M2 corrections before implementing that milestone.
```

## 163. Assistant — 2026-10-23T12:15:39.237Z

Understood. I'll record both timing corrections in the plan now, report them again before starting M2, and then exit planning so M1 can begin once `fix/measure-process-kinds` is merged.

## 164. Assistant — 2026-10-23T12:15:40.514Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'W = |W\\b|M2.4|M2.5|remaining time|F − now|M = 25|13 s|M ≥ W' ~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "description": "Find plan lines that use the old timing bound"
}
```

## 165. User — 2026-10-23T12:15:41.350Z

### Tool result

```
42:    M2.4.
75:   - **No overlap.** No replacement Spark work overlaps a surviving earlier process tree (M2.5).
277:- **Steps.** Each step runs behind the launcher (M2.5) as `sys.executable -m etf_risk.<module>`,
322:    busy" (M2.5).
326:#### M2.4 Time, deadlines and bounded operations
347:  - **Worst case:** one operation takes at most **W = B + 5 s = 13 s**.
355:    (`DEFAULT_LEASE`) and **M = 25 s**;
356:  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5). The
359:- **The inequality.** The longest gap between two deadline checks is W (one blocked store call).
360:  Termination then takes G. The tree is therefore gone by `F + W + G = m₀ + L − M + 20 s`, which
361:  is before the lease can expire (`m₀ + L`) whenever **M ≥ W + G**. The drafts give 25 ≥ 20, with
376:#### M2.5 No overlapping Spark work: watchdog and host execution lock
384:    renewal-before-step and is extended only by the worker's "remaining time" messages.
429:- **Factory.** `JobStore` accepts a connection factory: `connect_mysql` with the M2.4 timeouts and
440:  W holds. A COMMIT that timed out may still have taken effect on the server, which is the
515:  - every store operation stays within W (measured);
534:  - **deadlines:** a fake store blocking W per call. The tree is gone before `m₀ + L`; no step
535:    starts after F; the watchdog still ends the tree when the worker thread blocks beyond W;
553:  - store-operation durations recorded and checked against W.
731:- W: a warm session, with no cache;
764:  - time and deadline rules (M2.4–M2.5);
836:- **M2:** any change to the M2.4 values that breaks or restates M ≥ W + G; any store change beyond
```

## 166. Assistant — 2026-10-23T12:15:43.581Z

### Tool call: Read

```
{
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "offset": 326,
  "limit": 80
}
```

## 167. User — 2026-10-23T12:15:43.699Z

### Tool result

```
326	#### M2.4 Time, deadlines and bounded operations
327	- **Clocks.** Lease times in the database stay on the store's wall clock (UTC), which all
328	  processes on this host share. Every local deadline uses `time.monotonic()`:
329	  - self-fence;
330	  - watchdog;
331	  - timeouts;
332	  - lock waits;
333	  - operation budgets;
334	  - backoff.
335	
336	  Event logs record UTC (shared across processes) and monotonic offsets (durations within one
337	  process).
338	- **Bounded database operations** (draft values, fixed at review from M2a measurements):
339	  - **Session settings:** `connect_timeout` 3 s, `read_timeout` 5 s and `write_timeout` 5 s
340	    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`
341	    2 s, which is below the read timeout, so lock waits end as definite 1205 conflicts; session
342	    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks
343	    indefinitely.
344	  - **Conflict retries:** the existing `CONFLICT_RETRIES` = 3 runs.
345	  - **Operation budget:** B = 8 s on the monotonic clock, checked before each statement and each
346	    retry; past it the operation raises without starting another statement.
347	  - **Worst case:** one operation takes at most **W = B + 5 s = 13 s**.
348	- **Kill grace.** G = 5 s SIGTERM + 2 s for SIGKILL to be confirmed = **7 s**.
349	- **Renewal loop** (the worker thread):
350	  - waits on the launcher with `wait(timeout=1 s)`;
351	  - renews every 10 s;
352	  - checks the self-fence deadline on every tick and after every renewal, success or not. The
353	    deadline is `F = m₀ + L − M`, where `m₀` is the monotonic time just *before* the last
354	    successful renewal started (the database lease began at or after `m₀`), with L = 60 s
355	    (`DEFAULT_LEASE`) and **M = 25 s**;
356	  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5). The
357	    worker's end of that pipe is non-blocking. If the pipe is full because the launcher is
358	    frozen, the message is dropped, which can only make the watchdog act sooner.
359	- **The inequality.** The longest gap between two deadline checks is W (one blocked store call).
360	  Termination then takes G. The tree is therefore gone by `F + W + G = m₀ + L − M + 20 s`, which
361	  is before the lease can expire (`m₀ + L`) whenever **M ≥ W + G**. The drafts give 25 ≥ 20, with
362	  5 s to spare. Changing any value requires restating this inequality, and that is a pause point.
363	- **No other blocking calls during a run.** From the renewal before step 1 to acceptance, the
364	  worker thread makes only bounded store calls and bounded waits; it makes no Kafka calls.
365	  - Kafka is used only between runs. `socket.timeout.ms` is pinned at 10 s.
366	  - A commit that blocks before a run cannot cause overlap: the renewal before each step returns
367	    false if the job was taken over meanwhile, and the step never starts.
368	- **Retry rules:**
369	  - `renew`: retried at the next interval;
370	  - `accept_result` and `fail_attempt`: retried on disconnects only, until F; `accept_result` is
371	    idempotent for its token;
372	  - `claim`: raises into `serve()`'s rewind and retry;
373	  - `submit`: never retried; the CLI exits with a distinct "outcome unknown" code;
374	  - reconciler passes: bounded, logged and repeated.
375	
376	#### M2.5 No overlapping Spark work: watchdog and host execution lock
377	A SIGSTOPped worker can neither renew nor check its deadline, and its pipe to the launcher stays
378	open. Two independent layers therefore protect against overlap, in addition to the worker's own
379	self-fence.
380	- **Watchdog (the launcher process, one per step).**
381	  - The worker starts the launcher with `start_new_session=True` and a keepalive pipe as its
382	    stdin.
383	  - The launcher keeps a monotonic deadline. It starts from the value sent after the
384	    renewal-before-step and is extended only by the worker's "remaining time" messages.
385	  - It terminates its tree (M2.6) on EOF (the worker died) or when the deadline passes (the
386	    worker is frozen, stuck or fenced by its own clock). Either way the tree is gone by
387	    F + G, before the lease can expire, without any action by the worker.
388	- **Host execution lock.**
389	  - Before starting a step, every launcher takes an exclusive `flock` on a host-wide file
390	    (default `~/.cache/etf-risk/locks/spark-exec.lock`; tests use their own path).
391	  - It then checks that no process carrying another attempt's marker survives (M2.6).
392	  - It passes the lock descriptor to the step's driver, so the lock is held while the launcher
393	    or the driver lives. PySpark closes inherited descriptors for the JVM, and the JVM exits when
394	    the driver's pipe breaks; the survivor check covers that window.
395	  - A launcher that cannot get the lock, or still sees survivors, within the lock-wait bound
396	    (step limit + G + 30 s) does not start Spark. It exits with "execution lock busy", and the
397	    attempt fails as retryable.
398	  - So even when the whole old tree is frozen (watchdog included) or the wall clock jumps, no
399	    replacement Spark run starts while an earlier tree survives. The session harness takes the
400	    same lock for its reference runs.
401	- **Renewal before each step and before acceptance.** A fenced worker never starts a new step.
402	
403	#### M2.6 Terminating a process tree
404	- **Why not a group kill.** PySpark's daemon calls `os.setpgid(0, 0)` (pyspark/daemon.py:115),
405	  so its workers leave the step's group, and re-parented orphans escape child-walks.
```

## 168. Assistant — 2026-10-23T12:16:04.433Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "#### M2.4 Time, deadlines and bounded operations\n- **Clocks.** Lease times in the database stay on the store's wall clock (UTC), which all\n  processes on this host share. Every local deadline uses `time.monotonic()`:\n  - self-fence;\n  - watchdog;\n  - timeouts;\n  - lock waits;\n  - operation budgets;\n  - backoff.\n\n  Event logs record UTC (shared across processes) and monotonic offsets (durations within one\n  process).\n- **Bounded database operations** (draft values, fixed at review from M2a measurements):\n  - **Session settings:** `connect_timeout` 3 s, `read_timeout` 5 s and `write_timeout` 5 s\n    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`\n    2 s, which is below the read timeout, so lock waits end as definite 1205 conflicts; session\n    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks\n    indefinitely.\n  - **Conflict retries:** the existing `CONFLICT_RETRIES` = 3 runs.\n  - **Operation budget:** B = 8 s on the monotonic clock, checked before each statement and each\n    retry; past it the operation raises without starting another statement.\n  - **Worst case:** one operation takes at most **W = B + 5 s = 13 s**.\n- **Kill grace.** G = 5 s SIGTERM + 2 s for SIGKILL to be confirmed = **7 s**.\n- **Renewal loop** (the worker thread):\n  - waits on the launcher with `wait(timeout=1 s)`;\n  - renews every 10 s;\n  - checks the self-fence deadline on every tick and after every renewal, success or not. The\n    deadline is `F = m₀ + L − M`, where `m₀` is the monotonic time just *before* the last\n    successful renewal started (the database lease began at or after `m₀`), with L = 60 s\n    (`DEFAULT_LEASE`) and **M = 25 s**;\n  - after each successful renewal, sends the launcher the remaining time `F − now` (M2.5). The\n    worker's end of that pipe is non-blocking. If the pipe is full because the launcher is\n    frozen, the message is dropped, which can only make the watchdog act sooner.\n- **The inequality.** The longest gap between two deadline checks is W (one blocked store call).\n  Termination then takes G. The tree is therefore gone by `F + W + G = m₀ + L − M + 20 s`, which\n  is before the lease can expire (`m₀ + L`) whenever **M ≥ W + G**. The drafts give 25 ≥ 20, with\n  5 s to spare. Changing any value requires restating this inequality, and that is a pause point.\n- **No other blocking calls during a run.** From the renewal before step 1 to acceptance, the\n  worker thread makes only bounded store calls and bounded waits; it makes no Kafka calls.\n  - Kafka is used only between runs. `socket.timeout.ms` is pinned at 10 s.\n  - A commit that blocks before a run cannot cause overlap: the renewal before each step returns\n    false if the job was taken over meanwhile, and the step never starts.",
  "new_string": "#### M2.4 Time and deadlines\n*Corrected 2026-10-23 after the author's review. The corrections are reported again before M2\nstarts.*\n\n- **Safety does not rest on database timing.**\n  - No overlapping Spark work is ensured only by the launcher's watchdog and the host execution\n    lock (M2.5). Neither ever waits on the database.\n  - No time limit is claimed for a whole database operation. Per-I/O read and write timeouts do\n    not bound an operation made of a reconnect, several statements and a rollback, so the earlier\n    \"W = 13 s\" claim is withdrawn.\n  - The worker's own self-fence and all database timeouts serve liveness only.\n  - Correctness (one accepted result) never depended on time.\n- **Clocks.**\n  - Lease times in the database stay on the store's wall clock (UTC).\n  - Every local deadline uses the host's monotonic clock: `time.monotonic()`, the same\n    system-wide clock in the worker and the launcher.\n  - The worker sends the launcher **absolute** monotonic deadlines, never remaining durations.\n  - At launch, a handshake checks that both processes read the same clock: the launcher's reading\n    must be at least the worker's sent reading, and within 1 s of it. Otherwise the launcher\n    refuses to start.\n- **The deadline.**\n  - After each successful renewal, the worker computes `F = m₀ + L − M` and sends it with a\n    sequence number. `m₀` is the monotonic time just *before* that renewal started; the database\n    lease began at or after `m₀`.\n  - The launcher terminates its tree once `now ≥ F`. Termination takes at most G = 7 s (5 s after\n    SIGTERM, then SIGKILL, confirmed within 2 s).\n  - The watchdog checks every t_w = 0.5 s, so the tree is gone by `F + t_w + G`. That is before\n    the lease can expire (`m₀ + L`) whenever **M ≥ t_w + G + ε**.\n  - Draft: **M = 10 s** (0.5 + 7 + 2.5), with L = 60 s (`DEFAULT_LEASE`).\n  - This holds whatever the worker thread is doing: blocked in a database call, frozen or dead.\n  - Changing these values means restating this inequality, and that is a pause point.\n- **Wall and monotonic clocks diverging.** A wall-clock jump can make the database lease expire\n  before F, and a takeover can then come early. The replacement's launcher still cannot start\n  Spark until the lock is free and no earlier attempt's process survives, which is by F + G at\n  the latest.\n- **The worker never starts a step or accepts once `now ≥ F`.**\n  - It checks F on every 1 s tick and after every store call.\n  - It renews before each step and before acceptance.\n  - A launcher given a deadline that has already passed refuses to start.\n- **Liveness settings** (bounded waits, not a safety bound; drafts, fixed from M2a's\n  measurements):\n  - **Session settings:** `connect_timeout` 3 s; `read_timeout` and `write_timeout` 5 s per I/O\n    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`\n    2 s, below the read timeout, so lock waits end as definite 1205 conflicts; session\n    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks\n    indefinitely.\n  - **Retries and renewals:** the existing `CONFLICT_RETRIES` = 3 runs; a renewal every 10 s.\n  - **What this means for E2.** With M = 10 s, a run can survive a database outage of up to about\n    L − M − renewal interval ≈ 40 s. That number feeds the E2 predictions; it is not a claim.\n  - **Recording.** Store-operation durations are recorded in the events.\n- **Kafka.** It is used only between runs, with `socket.timeout.ms` pinned at 10 s. A commit that\n  blocks before a run cannot cause overlap: the renewal before each step returns false if the\n  job was taken over meanwhile, and the step never starts."
}
```

## 169. User — 2026-10-23T12:16:05.589Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 170. Assistant — 2026-10-23T12:16:09.179Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - The launcher keeps a monotonic deadline. It starts from the value sent after the\n    renewal-before-step and is extended only by the worker's \"remaining time\" messages.\n  - It terminates its tree (M2.6) on EOF (the worker died) or when the deadline passes (the\n    worker is frozen, stuck or fenced by its own clock). Either way the tree is gone by\n    F + G, before the lease can expire, without any action by the worker.",
  "new_string": "  - The launcher keeps an absolute monotonic deadline. It starts from the value sent after the\n    renewal-before-step and changes only through the worker's messages, each carrying an absolute\n    deadline and a sequence number.\n  - **Loop order:**\n    1. If `now ≥ deadline`, fire. Firing is terminal: no later message can extend it.\n    2. Only otherwise, read the waiting messages. A message moves the deadline only if its\n       sequence number is newer, its deadline is later than the current one, and its deadline is\n       still in the future.\n\n    So buffered messages read after a pause can never revive an expired watchdog. Because the\n    deadlines are absolute, no message can push the deadline past the time the worker granted.\n    The worker's end of the pipe is non-blocking, and a message that does not fit is dropped,\n    which can only make the watchdog act sooner.\n  - **Termination.** The launcher terminates its tree (M2.6) on EOF (the worker died) or when the\n    deadline passes (the worker is frozen, stuck or blocked). Either way the tree is gone by\n    F + t_w + G, before the lease can expire, without any action by the worker."
}
```

## 171. User — 2026-10-23T12:16:10.295Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 172. Assistant — 2026-10-23T12:16:11.777Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  the ROLLBACK.\n- **No ROLLBACK on a broken connection.** The store closes it instead; the server rolls back the\n  open transaction when the session ends. No statement then runs after the operation budget, so\n  W holds. A COMMIT that timed out may still have taken effect on the server, which is the\n  existing \"failed COMMIT\" case, handled by idempotent repeats.",
  "new_string": "  the ROLLBACK.\n- **No ROLLBACK on a broken connection.** The store closes it instead; the server rolls back the\n  open transaction when the session ends. A broken connection therefore costs no further I/O. A\n  COMMIT that timed out may still have taken effect on the server, which is the existing \"failed\n  COMMIT\" case, handled by idempotent repeats."
}
```

## 173. User — 2026-10-23T12:16:12.852Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 174. Assistant — 2026-10-23T12:16:13.274Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - every store operation stays within W (measured);\n  - the run either continues or self-fences before its lease;",
  "new_string": "  - store-operation durations are recorded, with no bound claimed;\n  - the run either continues or its tree is gone by F + t_w + G, before its lease;"
}
```

## 175. User — 2026-10-23T12:16:14.339Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 176. Assistant — 2026-10-23T12:16:16.874Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - **deadlines:** a fake store blocking W per call. The tree is gone before `m₀ + L`; no step\n    starts after F; the watchdog still ends the tree when the worker thread blocks beyond W;",
  "new_string": "  - **deadlines:** a fake store whose calls block indefinitely. The watchdog still ends the tree\n    by F + t_w + G, before `m₀ + L`, and no step starts and no acceptance happens after F;\n  - **clock handshake:** a mismatched reading is refused;\n  - **watchdog pause and resume with queued stale messages:**\n    - (a) SIGSTOP the launcher. Queue messages with past deadlines, out-of-order sequence numbers\n      and one future deadline. Keep it stopped past the current deadline, then SIGCONT. The tree\n      is terminated at once, and the log shows the buffered messages ignored.\n    - (b) The same, with a pause shorter than the current deadline. The deadline becomes exactly\n      the newest valid absolute value; stale and out-of-order messages change nothing."
}
```

## 177. User — 2026-10-23T12:16:17.939Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 178. Assistant — 2026-10-23T12:16:17.983Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "  - store-operation durations recorded and checked against W.",
  "new_string": "  - store-operation durations recorded (informational)."
}
```

## 179. User — 2026-10-23T12:16:19.052Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 180. Assistant — 2026-10-23T12:16:19.750Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "- **M2:** any change to the M2.4 values that breaks or restates M ≥ W + G; any store change beyond",
  "new_string": "- **Before M2 starts:** report the two timing corrections (absolute deadlines; no database-time\n  bound in the safety argument).\n- **M2:** any change to the M2.4 values that breaks or restates M ≥ t_w + G + ε; any store change beyond"
}
```

## 181. User — 2026-10-23T12:16:20.820Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 182. Assistant — 2026-10-23T12:16:25.499Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/plans/please-turn-this-outline-cozy-candy.md",
  "old_string": "Status: revision 2, after the author's review on 2026-10-23 and a design check against the code\nand libraries. Nothing is implemented until it is approved.",
  "new_string": "Status: revision 3 (2026-10-23).\n- **M1.** The author approved it, to start once `fix/measure-process-kinds` is merged.\n- **M2.** The timing design (M2.4–M2.5) was corrected after the author's second review: absolute\n  monotonic deadlines, and no database-time bound in the safety argument. The corrections are\n  reported again before M2 starts."
}
```

## 183. User — 2026-10-23T12:16:26.564Z

### Tool result

```
The file ~/.claude/plans/please-turn-this-outline-cozy-candy.md has been updated successfully.
```

## 184. Assistant — 2026-10-23T12:16:32.604Z

### Tool call: ExitPlanMode

```
{
  "plan": "# Plan: finishing the systems extension (spec §11) in six reviewed milestones\n\nStatus: revision 3 (2026-10-23).\n- **M1.** The author approved it, to start once `fix/measure-process-kinds` is merged.\n- **M2.** The timing design (M2.4–M2.5) was corrected after the author's second review: absolute\n  monotonic deadlines, and no database-time bound in the safety argument. The corrections are\n  reported again before M2 starts.\n\n## Context\n\nStages 1–4 and the extension's job queue are merged into `main` (f058095): PR #7 (job table,\nfencing), PR #8 (Kafka delivery, reconciler), PR #9 (Stage 4). Spec §11 still lists as planned:\n- the real pipeline in the worker (today `SimulatedPipeline`);\n- the recovery experiments E1/E2;\n- the Redis result cache;\n- the cache experiment E3;\n- their documentation.\n\nThis plan turns the author's six-point outline into milestones M1–M6, one branch and PR each. Each\nmilestone has deliverables, acceptance criteria, tests and a statement of how it keeps the\nguarantee. Four cross-cutting requirements run through all of them: code provenance for `jobs/`,\nreproducible dependencies, startup commands, and measured memory budgets. Data verification, the\nprivacy-hook fixes and AI-log review stay in separate workstreams.\n\nState observed on 2026-10-23:\n- the main worktree is on `fix/measure-process-kinds` (97c35f3, pushed, not merged), with\n  uncommitted privacy-hook work (W2);\n- 68 untracked AI-log folders exist;\n- another project's containers share the Docker VM;\n- `gh` is not installed.\n\n## Decisions and working mode (the author, 2026-10-23)\n\n- **Placement.** The worker, reconciler and submit run natively on the host. MySQL and Kafka (and\n  Redis from M4) run in Compose.\n- **Authorship.** The spec §11 split stays.\n  - Claude Code writes M1, M2 and all tooling.\n  - The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.\n- **Six milestones**, as in the outline.\n- **Working mode after approval.** Claude proceeds autonomously with routine work inside each\n  milestone: code, tests, docs, dry runs and commits on the milestone branch.\n- **When Claude pauses and asks.**\n  - **Material design changes:** anything this plan does not describe; any change to the store's\n    guards or SQL beyond the two additive changes in M2.1; any change to the time inequality in\n    M2.4.\n  - **Authorship decisions.**\n  - **Formal experiment approval:** Part A sign-off, and the author running the formal session.\n- **Push and merge.** The author pushes, or tells Claude to push, and opens and merges each PR.\n- **Reports.** Every milestone ends with a report: what was done, what was found and fixed, test\n  counts and measured peaks.\n\n## At a glance\n\n| # | Branch | Written by | Needs | Main deliverable | Done when |\n|---|---|---|---|---|---|\n| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; recursive provenance; `jobs` group; runbook skeleton; peak helper; mutation script | provenance covers `jobs/`; lock only adds; live suite 379 or explained; mutations caught |\n| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline; renewals with monotonic deadlines; watchdog and host lock; tree cleanup; reconnect; store identity; result digest; CLI | crash, stall, timeout and restart cases end with one accepted, correct, digest-bound result and no overlapping Spark trees |\n| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, harness, collector, batch | Part A met; no lost job; no second acceptance |\n| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py`, `runs.py` | M2 | cache-aside keyed by run digest and full query; accepted-run policy; fallback | contract tests pass; same results with Redis down; the run of record is usable through the reviewed registry |\n| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, harness, collector, batch | Part A met |\n| M6 | `docs/extension-report` | Claude drafts; author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |\n\nM4's code can be written while M3's formal session runs (ground rule 6); it does not touch M3's\nfiles.\n\n## Ground rules for every milestone\n\n1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has\n   exactly one, and a job may execute more than once.\n   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it.\n   - **Checking.** `INVARIANT_QUERIES` / `invariant_violations()` (store.py:127, :481) check it\n     after every test scenario, every worker run and every experiment batch.\n   - **Accepting.** Nothing but `JobStore.accept_result` produces an accepted attempt.\n   - **No reconnect inside a transaction** (M2.8). It could break the guarantee: the rest of a\n     transaction would commit statement by statement.\n   - **Cleanup** never touches an accepted or valid active attempt.\n   - **The cache** serves accepted runs only and never writes the job table.\n   - **No overlap.** No replacement Spark work overlaps a surviving earlier process tree (M2.5).\n2. **Authorship.**\n   - For the author's parts, Claude prepares scaffolds (signatures, docstrings, TODOs, contract\n     tests) and reviews, but does not fill them in.\n   - New files carry an `AI contribution:` line.\n   - Experiment documents carry an `Author:` line saying the author wrote Part A and the answers\n     with tutoring, unlike earlier experiments where Claude drafted Part A\n     (caching-experiment.md:56).\n3. **Git.**\n   - Each milestone has its own worktree (`.claude/worktrees/<name>`) from up-to-date `main`, with\n     a `data` symlink to the main worktree's `data/`. M1 changes `.gitignore`'s `/data/` to `/data`\n     so the symlink is ignored too.\n   - Stage files by explicit path only.\n   - Merge with merge commits; never squash or rebase.\n   - Commits end with the Co-Authored-By trailer.\n   - Formal sessions run on a merged, clean commit whose SHA lands in every record, with no\n     commits during a session.\n4. **Privacy.** `data/` and the private plan stay out of Git. Never print memory files,\n   `.git/info/exclude`, app lists, or other projects' container or session names in tool calls.\n   Helpers count other containers without naming them. Child processes get an allowlisted\n   environment, so service URLs and passwords never reach the pipeline steps.\n5. **Measurement sessions.** While one runs, other sessions only write and review. They wait for\n   the explicit end, then check that the worktree is unchanged.\n6. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write \"one process\",\n   never \"one core\". Give each experiment a \"not claimed\" list.\n\n## Cross-cutting requirements\n\n**A. Code provenance for `jobs/`.**\n- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob(\"*.py\")` (provenance.py:62).\n  No record identifies `jobs/*.py` or `jobs/schema/*.sql`, and a plain recursive glob would\n  collide on `__init__.py`.\n- **M1.** Hash every `*.py` and `*.sql` under `src/etf_risk/`, keyed by package-relative POSIX\n  path. Top-level keys stay as they are, so old records remain comparable.\n- **From M2.**\n  - `attempt.json` and every experiment record carry `code_state()`.\n  - Each accepted result is bound to its run digest in the job table (M2.1).\n- **Authorship provenance.** An origin table in `job-queue.md` maps each module → commits\n  (eec1032, e2806bd, cd72957) → PR → the tests that verify it. The `AI contribution:` lines stay.\n\n**B. Reproducible dependencies.**\n- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`\n  (docker/compose.yaml:13; test docstrings) and are not in `uv.lock`.\n- **Groups.**\n  - M1 adds a `jobs` group with these pins.\n  - M2 adds `psutil==7.2.2` to that group; it is already locked through `measure`.\n  - M4 adds a `cache` group with an exact `redis` pin.\n- **Lock changes** may only add packages. numpy 2.5.4, pandas 2.3.3, pyspark 4.2.0, pyarrow 26.0.0\n  and psutil 7.2.2 stay unchanged, checked with a lock diff and `uv lock --check`.\n- **Commands** use `--group …` and `uv sync --frozen`.\n- **Images** are pinned by digest. Redis follows the Kafka rule: the newest release at least two\n  weeks old.\n- **Host tools** are recorded with each formal session (2026-10-23: uv 0.11.16, Java 17.0.10,\n  Docker 28.3.0, Compose v2.38.1, VM 3.83 GiB).\n- **Out of scope:** the NumPy pin.\n\n**C. Startup commands.**\n- **Runbook.** A README section (skeleton in M1, filled by M2, M4 and M6) gives copy-pasteable\n  commands for:\n  - **Setup:** the worktree and `data` symlink; the test services.\n  - **The E1/E2 stack:** Compose `mysql kafka`; then `init-db`, `create-topic`, worker,\n    reconciler, submit and `status`.\n  - **The E3 stack:** Compose `redis`, the query CLI and the warm query service.\n  - **Teardown:** export first, then `down -v`.\n- **Readiness.** A service is ready only after a check that matches what will use it:\n  - MySQL: a login plus `SELECT 1` (its healthcheck answers before logins work,\n    docker/compose.yaml:35);\n  - Kafka: the batch topic's metadata and the group coordinator are available;\n  - Redis: `PING`.\n- **Acceptance.** The commands are run exactly as written in a fresh worktree.\n\n**D. Measured memory budgets.** The spec §11 ledger records component, limit, measured peak,\nmethod, date and commit.\n\n| Component | Budget | Measured | Source |\n|---|---|---|---|\n| MySQL container | 512 MiB | 324–398 MiB fresh; 472 after two runs; 511 after ~2 h | spec §11 |\n| Kafka container | 640 MiB | 354–478 MiB; 516 with mutation checks | spec §11 |\n| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB, stride 21 | spec §11 |\n| Native stride-21 tree | `measure` stop 4.8 GiB | 1.27 GiB with 1.3–1.6 GiB free; 2.62–2.73 GiB with 3.0–3.5 GiB free | spec §8, experiments.md |\n| Native calendar-year tree | — | not measured (M2) | |\n| Worker, reconciler, submit | from M2 dry runs | — | |\n| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |\n| Warm query service | from M4 dry runs | — | |\n\n- **Budgets** are set at the review gate from dry runs, then checked; never from the run that\n  checks them.\n- **Container peaks** come from cgroup `memory.peak` through a helper (M1). They are read before\n  every injected restart, since a restart may reset them; M2 verifies whether it does.\n- **Native peaks** come from a marker-based sampler (M2). `TreeSampler` misses processes that were\n  re-parented to launchd.\n- **Before any formal session or budget measurement:**\n  - zero containers outside this project (counted, not named);\n  - ports 3307, 9094 and 6380 free;\n  - host available memory at or above the Part A threshold.\n- **Each recovery batch** starts on a fresh MySQL container with a fresh topic and consumer group.\n- **A budget exceeded** stops the session.\n\n## Milestones (numbered as in the outline)\n\n### M1 — Read the whole project; bring the code up to date\nBranch `feature/extension-baseline` · Claude Code · after `fix/measure-process-kinds` is merged.\n\n**Audit.** The report lists the following. Items inside this plan are fixed as routine work;\nanything else waits for the author.\n- **Reproducibility:**\n  - gaps A, B and C;\n  - the 22 mutation checks exist only as prose;\n  - the merged worktrees `job-queue` and `job-table` are clean, so they can be removed.\n- **Missing operations:**\n  - no entry point in `jobs/` (the §11 \"submit CLI\" does not exist);\n  - logging is never configured;\n  - nothing is timed;\n  - `published_at` is cleared by the claim;\n  - a crash before the claim leaves no trace;\n  - Kafka group timings are unpinned defaults while `serve()` runs the pipeline inside its poll\n    loop;\n  - **no reconnect:** `JobStore` keeps one connection for life (store.py:286-292, 526), so after a\n    MySQL restart the reconciler fails every pass and `serve()` raises after 5 retries;\n  - no supervisor.\n- **Pipeline CLIs** (findings only; the worker works around them in M2.3):\n  - exit 1 means both \"checks failed\" or \"mismatch\" and any uncaught exception;\n  - `run.json` is written only in `finally`;\n  - verify misses `JSONDecodeError`;\n  - verify's `spark.stop()` is not in a `finally`;\n  - paths are relative to the working directory: `--processed-root` and verify's `windows_dir`;\n  - windows refuses only an existing `config.json`, while README:224 says an existing folder.\n- **Documentation drift:**\n  - job-table.md's claim SQL and \"apart from submit\";\n  - job-queue.md:90;\n  - dated status blocks in job-table.md:97-103 and job-queue.md:146-160;\n  - spec §5's diagram, its \"Every box is implemented\", and its E2–E4 node ids;\n  - spec.md has no AI header.\n- **Test helpers:** `WorkerEnv.check` is tied to the simulated `result.json`.\n\n**Fixes:**\n- provenance (A);\n- the `jobs` group and `--group jobs` everywhere (B);\n- `.gitignore` `/data/` → `/data`;\n- the runbook skeleton (C);\n- the `memory.peak` helper (D);\n- job-doc drift and stale status;\n- the module origin table;\n- a mutation-check script: each mutation a patch applied in a scratch worktree with a timeout.\n  The list is rebuilt from the surviving descriptions (job-table.md:98-102, job-queue.md:157-164,\n  e2806bd's message) and documented as rebuilt, not claimed identical to the original 22;\n- removal of the merged worktrees.\n\nThe pipeline CLIs and the analysis code are not changed.\n\n**Revalidation:** the offline suite; the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with\n`--group jobs`; the mutation script; peaks through the helper.\n\n**Acceptance.**\n- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in\n  `source_sha256` under a unique key, with top-level keys unchanged.\n- The lock diff only adds packages.\n- The live suite passes with 379 cases, or the difference is explained.\n- Every rebuilt mutation fails a test within its timeout.\n- Peaks are within budget.\n\n**Tests:** new cases in `test_provenance.py`; job suites on SQLite and live; the mutation script.\n\n**Guarantee:** no store change; the mutation script re-proves that each guard is tested.\n\n### M2 — The worker runs windows → spark_pipeline → verify\nBranch `feature/worker-pipeline` · Claude Code · after M1. Two stages in one PR, with a progress\nreport between them (not a pause):\n- **M2a:** M2.1, M2.8, M2.9, M2.10 and the CLI, exercised with the simulated pipeline.\n- **M2b:** M2.2–M2.7, the real pipeline.\n\n#### M2.1 Identity: store, output layout, result digest\n- **Store identity.**\n  - `init-db` creates a one-row table `job_store` (`store_id`, a random 128-bit hex; `created_at`;\n    `schema_version`).\n  - Job and attempt ids repeat after a database is recreated, so everything outside the database\n    uses `store_id` with them: output paths, process markers, events and cache provenance.\n- **Output layout.**\n  - The worker passes `output_root/<store_id>` to `claim()`, giving folders\n    `<root>/<store_id>/job-<id>-attempt-<n>/`.\n  - The store already builds the path from the given root (store.py:356), so the store needs no\n    change for this.\n  - A recreated database never collides with old folders, which today would fail every job\n    (worker.py:128-132).\n- **Run digest.**\n  - `src/etf_risk/runs.py` (new; shared with M4) writes a canonical manifest of the Spark run\n    folder: sorted relative paths, sizes and SHA-256 per file.\n  - Its SHA-256 is the run digest, the run's immutable identity.\n  - The worker writes `manifest.json` in the attempt folder before acceptance.\n- **Bound at acceptance** (additive store change; the guards are unchanged):\n  - `job_attempts.result_digest CHAR(64)` with a CHECK `(outcome = 'accepted') = (result_digest\n    IS NOT NULL)`;\n  - `accept_result(claim, digest)` sets it in its existing `job_attempts` update, inside the same\n    token-guarded transaction (store.py:398-402);\n  - the idempotent repeat path also compares the digest;\n  - both schema files, the drift test and the invariant queries are updated.\n\n  This ties the accepted decision and the accepted content together atomically.\n- **Simulated pipeline.** `SimulatedPipeline` produces a digest too, so all existing scenarios\n  keep running.\n\n#### M2.2 Steps and environment\n- **Steps.** Each step runs behind the launcher (M2.5) as `sys.executable -m etf_risk.<module>`,\n  with absolute paths only:\n  1. `windows --snapshot … --kind … --window-days … --stride … --anchor … --processed-root <abs>\n     --out-root <run_dir>/windows --name <name>`;\n  2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>`;\n  3. `verify --run …`.\n- **Job parameters** (`params.py`, a frozen dataclass): snapshot, kind, window days, stride,\n  anchor, sample ticker. Unknown keys are refused.\n- **Worker settings:** the processed root and the output root, both recorded in\n  `attempt.json`.\n- **Input checksums.** `submit` computes `input_checksums` from the files `windows.py` records in\n  `inputs_sha256`. The worker re-checks them before step 1; a mismatch is not retryable.\n- **Step environment** (allowlisted):\n  - `cwd` = `<run_dir>/.work`, which also catches `spark-warehouse`;\n  - `TMPDIR` = `.work/tmp`;\n  - `SPARK_LOCAL_DIRS` = `.work/spark`;\n  - `SPARK_SUBMIT_OPTS=\"-Djava.io.tmpdir=<abs>/.work/jtmp -XX:-UsePerfData\"`, which the Spark\n    launcher reads. The macOS JDK ignores `TMPDIR`.\n  - `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` = `sys.executable`. Otherwise workers use\n    `python3` from PATH (pyspark/core/context.py:342).\n  - Never `JAVA_TOOL_OPTIONS` or `_JAVA_OPTIONS`: their \"Picked up …\" notice would replace the\n    Java version that `environment()` records (spark_pipeline.py:635-636). A test checks\n    `run.json`'s `java` field.\n  - The directories are created first.\n  - Logs go to `<run_dir>/logs/<step>.log`.\n\n#### M2.3 Acceptance rule and failure classification\n- **Accept only if all hold:**\n  - every step exits 0;\n  - `run.json` status is `ok`;\n  - every `checks.json` count is 0;\n  - `verify.json` has no mismatch and the same breached windows;\n  - every table has `_SUCCESS`.\n- **Then:**\n  1. remove `.work`;\n  2. write `attempt.json`;\n  3. write `manifest.json`;\n  4. **renew**;\n  5. `accept_result(claim, digest)`.\n\n  Nothing in the folder changes after acceptance; a test compares the manifest before and after.\n- **Classification**, decided from the records, never from the exit code alone:\n  - **not retryable:** a checksum error (exit 3); `run.json` status `checks_failed`; a verify\n    mismatch; a parameter or input-checksum error;\n  - **retryable:** a signal, a timeout, status `failed`, a missing record, or \"execution lock\n    busy\" (M2.5).\n\n  Retryable failures requeue until `max_attempts`.\n\n#### M2.4 Time and deadlines\n*Corrected 2026-10-23 after the author's review. The corrections are reported again before M2\nstarts.*\n\n- **Safety does not rest on database timing.**\n  - No overlapping Spark work is ensured only by the launcher's watchdog and the host execution\n    lock (M2.5). Neither ever waits on the database.\n  - No time limit is claimed for a whole database operation. Per-I/O read and write timeouts do\n    not bound an operation made of a reconnect, several statements and a rollback, so the earlier\n    \"W = 13 s\" claim is withdrawn.\n  - The worker's own self-fence and all database timeouts serve liveness only.\n  - Correctness (one accepted result) never depended on time.\n- **Clocks.**\n  - Lease times in the database stay on the store's wall clock (UTC).\n  - Every local deadline uses the host's monotonic clock: `time.monotonic()`, the same\n    system-wide clock in the worker and the launcher.\n  - The worker sends the launcher **absolute** monotonic deadlines, never remaining durations.\n  - At launch, a handshake checks that both processes read the same clock: the launcher's reading\n    must be at least the worker's sent reading, and within 1 s of it. Otherwise the launcher\n    refuses to start.\n- **The deadline.**\n  - After each successful renewal, the worker computes `F = m₀ + L − M` and sends it with a\n    sequence number. `m₀` is the monotonic time just *before* that renewal started; the database\n    lease began at or after `m₀`.\n  - The launcher terminates its tree once `now ≥ F`. Termination takes at most G = 7 s (5 s after\n    SIGTERM, then SIGKILL, confirmed within 2 s).\n  - The watchdog checks every t_w = 0.5 s, so the tree is gone by `F + t_w + G`. That is before\n    the lease can expire (`m₀ + L`) whenever **M ≥ t_w + G + ε**.\n  - Draft: **M = 10 s** (0.5 + 7 + 2.5), with L = 60 s (`DEFAULT_LEASE`).\n  - This holds whatever the worker thread is doing: blocked in a database call, frozen or dead.\n  - Changing these values means restating this inequality, and that is a pause point.\n- **Wall and monotonic clocks diverging.** A wall-clock jump can make the database lease expire\n  before F, and a takeover can then come early. The replacement's launcher still cannot start\n  Spark until the lock is free and no earlier attempt's process survives, which is by F + G at\n  the latest.\n- **The worker never starts a step or accepts once `now ≥ F`.**\n  - It checks F on every 1 s tick and after every store call.\n  - It renews before each step and before acceptance.\n  - A launcher given a deadline that has already passed refuses to start.\n- **Liveness settings** (bounded waits, not a safety bound; drafts, fixed from M2a's\n  measurements):\n  - **Session settings:** `connect_timeout` 3 s; `read_timeout` and `write_timeout` 5 s per I/O\n    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`\n    2 s, below the read timeout, so lock waits end as definite 1205 conflicts; session\n    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks\n    indefinitely.\n  - **Retries and renewals:** the existing `CONFLICT_RETRIES` = 3 runs; a renewal every 10 s.\n  - **What this means for E2.** With M = 10 s, a run can survive a database outage of up to about\n    L − M − renewal interval ≈ 40 s. That number feeds the E2 predictions; it is not a claim.\n  - **Recording.** Store-operation durations are recorded in the events.\n- **Kafka.** It is used only between runs, with `socket.timeout.ms` pinned at 10 s. A commit that\n  blocks before a run cannot cause overlap: the renewal before each step returns false if the\n  job was taken over meanwhile, and the step never starts.\n- **Retry rules:**\n  - `renew`: retried at the next interval;\n  - `accept_result` and `fail_attempt`: retried on disconnects only, until F; `accept_result` is\n    idempotent for its token;\n  - `claim`: raises into `serve()`'s rewind and retry;\n  - `submit`: never retried; the CLI exits with a distinct \"outcome unknown\" code;\n  - reconciler passes: bounded, logged and repeated.\n\n#### M2.5 No overlapping Spark work: watchdog and host execution lock\nA SIGSTOPped worker can neither renew nor check its deadline, and its pipe to the launcher stays\nopen. Two independent layers therefore protect against overlap, in addition to the worker's own\nself-fence.\n- **Watchdog (the launcher process, one per step).**\n  - The worker starts the launcher with `start_new_session=True` and a keepalive pipe as its\n    stdin.\n  - The launcher keeps an absolute monotonic deadline. It starts from the value sent after the\n    renewal-before-step and changes only through the worker's messages, each carrying an absolute\n    deadline and a sequence number.\n  - **Loop order:**\n    1. If `now ≥ deadline`, fire. Firing is terminal: no later message can extend it.\n    2. Only otherwise, read the waiting messages. A message moves the deadline only if its\n       sequence number is newer, its deadline is later than the current one, and its deadline is\n       still in the future.\n\n    So buffered messages read after a pause can never revive an expired watchdog. Because the\n    deadlines are absolute, no message can push the deadline past the time the worker granted.\n    The worker's end of the pipe is non-blocking, and a message that does not fit is dropped,\n    which can only make the watchdog act sooner.\n  - **Termination.** The launcher terminates its tree (M2.6) on EOF (the worker died) or when the\n    deadline passes (the worker is frozen, stuck or blocked). Either way the tree is gone by\n    F + t_w + G, before the lease can expire, without any action by the worker.\n- **Host execution lock.**\n  - Before starting a step, every launcher takes an exclusive `flock` on a host-wide file\n    (default `~/.cache/etf-risk/locks/spark-exec.lock`; tests use their own path).\n  - It then checks that no process carrying another attempt's marker survives (M2.6).\n  - It passes the lock descriptor to the step's driver, so the lock is held while the launcher\n    or the driver lives. PySpark closes inherited descriptors for the JVM, and the JVM exits when\n    the driver's pipe breaks; the survivor check covers that window.\n  - A launcher that cannot get the lock, or still sees survivors, within the lock-wait bound\n    (step limit + G + 30 s) does not start Spark. It exits with \"execution lock busy\", and the\n    attempt fails as retryable.\n  - So even when the whole old tree is frozen (watchdog included) or the wall clock jumps, no\n    replacement Spark run starts while an earlier tree survives. The session harness takes the\n    same lock for its reference runs.\n- **Renewal before each step and before acceptance.** A fenced worker never starts a new step.\n\n#### M2.6 Terminating a process tree\n- **Why not a group kill.** PySpark's daemon calls `os.setpgid(0, 0)` (pyspark/daemon.py:115),\n  so its workers leave the step's group, and re-parented orphans escape child-walks.\n- **Membership.** Every step process carries the marker\n  `ETF_RISK_ATTEMPT=<store_id>:<run id>:<attempt key>`, where the attempt key is the first 16 hex\n  digits of SHA-256(token). The token itself never leaves the worker. Members are found by session\n  id (`os.getsid` = the launcher's pid; nothing in the tree calls `setsid`) as a prefilter,\n  confirmed by the marker. A pid alone is never enough.\n- **Sequence.** SIGTERM to all members (so the JVM can delete its scratch); wait 5 s; SIGKILL to\n  survivors; rescan until none remain (bounded). The pids and the reason go to\n  `logs/launcher.log`.\n\n#### M2.7 Startup sweep: preserve valid active attempts\nWhen a worker starts, it scans this host for marked process trees of its own `store_id` and looks\neach attempt up in the store.\n- **Preserved:** any tree whose attempt is still *valid active*, meaning the job is running and\n  its current attempt number and token hash match. Its lease or watchdog decides when it ends;\n  the sweep never shortens a valid attempt.\n- **Terminated:** trees whose attempt has ended (expired, failed or accepted) or was taken over.\n- **Ended attempts' folders:** their `.work` scratch is removed; the folder itself never is.\n- **Left alone and reported:** trees of other store ids.\n- **Database unreachable:** the sweep does nothing.\n- **Folder listing.** `jobs cleanup` is dry-run only: it lists the folders of ended,\n  non-accepted attempts. Deleting them is not part of M2.\n\n#### M2.8 Database connections\n- **Factory.** `JobStore` accepts a connection factory: `connect_mysql` with the M2.4 timeouts and\n  session settings. It never uses `ping(reconnect=True)`, which drops `SET SESSION`.\n- **Reconnect only at the start of an operation:** before BEGIN, after a ping when the connection\n  has been idle for 60 s or more. Never inside a transaction. A connection that broke\n  mid-transaction is discarded; the transaction's remaining statements never run on a new\n  connection.\n- **Disconnects:** PyMySQL 2003, 2006, 2013, server codes 1053, 1927 and 4031, `InterfaceError`,\n  or `open == False` after an error. The connection is marked broken in the except path, before\n  the ROLLBACK.\n- **No ROLLBACK on a broken connection.** The store closes it instead; the server rolls back the\n  open transaction when the session ends. A broken connection therefore costs no further I/O. A\n  COMMIT that timed out may still have taken effect on the server, which is the existing \"failed\n  COMMIT\" case, handled by idempotent repeats.\n- **No replay.** The failed operation raises, as today.\n\n#### M2.9 Kafka settings (pinned in `kafka.py`, with tests on values and relations)\n| Setting | Value | Why |\n|---|---|---|\n| `group.protocol` | `classic` | `session.timeout.ms` is ignored under `consumer` |\n| `heartbeat.interval.ms` | 3000 | pinned default |\n| `session.timeout.ms` | 15000 | ≥ the broker's 6 s minimum, ≥ 3 heartbeats, < L |\n| `max.poll.interval.ms` | attempt limit + G + 60 s | a legitimate run never leaves the group |\n| `socket.timeout.ms` | 10000 | bounded commits and fetches |\n- **Max-poll error.** It gets its own event.\n- **Graceful stop** closes the consumer, so the group sees an immediate LeaveGroup.\n- **Consequence for E2.** Under the classic protocol, a joining standby or restarted worker waits\n  for a busy member to poll, and E2's recovery times include that wait.\n\n#### M2.10 Supervision, graceful stop, events, CLI\n- **Supervision.**\n  - `jobs worker` restarts its serve loop in-process, with backoff, after transport errors only:\n    disconnects, `ClaimRace`, non-fatal Kafka errors. Any other error exits non-zero.\n  - SIGKILLed workers are restarted by the M3 harness after a Part A delay.\n- **Graceful stop** (SIGTERM or SIGINT): stop polling, terminate the running tree, call\n  `fail_attempt(retryable=True)`, close the consumer. On a job's last attempt this fails the job\n  (store.py:416-417), so batches drain before stopping workers.\n- **Event log.** Each process writes JSON lines, flushed per event:\n  - delivered, claimed;\n  - renewed, renewal failed;\n  - step start and end, lock wait;\n  - watchdog kill, fenced;\n  - accepted, failed, requeued, published;\n  - max-poll.\n- **Attempt record.** `attempt.json` holds the worker id, store id, run id, steps (exit code,\n  times), the input checksums as checked, the settings and `code_state()`.\n- **CLI** `python -m etf_risk.jobs`:\n  - `init-db`, `create-topic`, `submit`, `worker`, `reconciler`;\n  - `cleanup` (dry run);\n  - `status [--check]`: tables and `invariant_violations()`; exits 1 on a violation;\n  - `export <dir>`: tables, violations and settings, for M3's batches.\n\n**Deliverables.**\n- **New modules:** `jobs/{pipeline,launcher,processes,params,events,__main__}.py` and\n  `src/etf_risk/runs.py`.\n- **Changes:** `store.py` (factory, budget, digest, store id), `mysql.py` (timeouts, `is_disconnect`),\n  `kafka.py` (settings), both schema files.\n- **Docs:** `job-queue.md` and `job-table.md` updated; the runbook's E1/E2 part.\n- **Ledger rows:** idle available memory with the stack up; per-step peaks for calendar-year and\n  stride 21; the Docker VM process's memory on the host.\n\n**Acceptance** (native worker; MySQL and Kafka in Compose; fresh containers):\n- **Normal runs.** A calendar-year job and a stride-21 job (no injection, no timing claims) end\n  `succeeded`. Each has exactly one accepted attempt whose recorded digest equals its manifest.\n  Each passes every check and verify. Each equals a direct CLI run by content, using the caching\n  collector's `TABLE_KEYS` (collect_caching_measurements.py:74-75) and `compare_tables`\n  (collect_partition_measurements.py:286), with `windows.parquet` compared by its window key.\n- **Worker-only SIGSTOP during step 2.** Checked *before SIGCONT*:\n  - no process of attempt 1 is alive by its watchdog deadline + G;\n  - the lock is free;\n  - attempt 2's Spark step started after attempt 1's last process exited (event times and the\n    process scan);\n  - attempt 1's renewal count is unchanged after attempt 2's claim.\n\n  After SIGCONT, the old worker is fenced and writes nothing.\n- **Whole-tree SIGSTOP** (worker, launcher and Spark). Checked *before SIGCONT*:\n  - the replacement started no Spark process;\n  - it waited on the lock or exited \"execution lock busy\";\n  - no second Spark tree exists; the only one is the frozen tree.\n\n  After SIGCONT, the old launcher terminates its tree at once, because its deadline has passed.\n  The job ends with exactly one accepted result.\n- **Worker SIGKILL during step 2.** No attempt process survives the lifeline grace, and the job\n  is requeued after its lease and succeeds.\n- **Timeouts.** An over-limit step is terminated and retried.\n- **Database stalls.** `LOCK TABLES jobs WRITE` from another session, `docker compose pause mysql`,\n  and `restart mysql`, each during a run:\n  - store-operation durations are recorded, with no bound claimed;\n  - the run either continues or its tree is gone by F + t_w + G, before its lease;\n  - nothing needs a manual restart;\n  - the job ends with one accepted result.\n- **Kafka restart during a run.** The same outcome.\n- **Startup sweep.** It terminates only ended attempts' trees, and preserves a live attempt run by\n  another worker.\n- **No leftovers.** The process scan shows no attempt processes. No new `spark-*`, `blockmgr-*`,\n  `pyspark-*`, `snappy-*`, `libzstd-jni*`, `liblz4-java*` or hsperfdata entries appear in\n  `/private/tmp` or `getconf DARWIN_USER_TEMP_DIR`. No new `spark-warehouse` appears in the\n  repository.\n- **Invariants.** `invariant_violations()` is always empty.\n- **Earlier tests.** All earlier job tests pass on both stores.\n\n**Tests.**\n- **Offline:**\n  - **launcher:** deadline kill; EOF kill; lock wait and refusal; survivor check; exit codes;\n  - **tree termination:** a grandchild that calls `setpgid(0, 0)`, and a double-fork orphan; none\n    survives a worker SIGKILL, a fence, a timeout or a worker-only SIGSTOP;\n  - **deadlines:** a fake store whose calls block indefinitely. The watchdog still ends the tree\n    by F + t_w + G, before `m₀ + L`, and no step starts and no acceptance happens after F;\n  - **clock handshake:** a mismatched reading is refused;\n  - **watchdog pause and resume with queued stale messages:**\n    - (a) SIGSTOP the launcher. Queue messages with past deadlines, out-of-order sequence numbers\n      and one future deadline. Keep it stopped past the current deadline, then SIGCONT. The tree\n      is terminated at once, and the log shows the buffered messages ignored.\n    - (b) The same, with a pause shorter than the current deadline. The deadline becomes exactly\n      the newest valid absolute value; stale and out-of-order messages change nothing.\n  - **sweep:** the rules of M2.7;\n  - **reconnect:**\n    - a disconnect between statements 1 and 2 never runs statement 2 on a new connection;\n    - a COMMIT that took effect but whose reply was lost: a repeated accept returns True, with\n      exactly one accepted attempt;\n    - session settings after a reconnect;\n    - the ping before an operation;\n  - **classification, parameters, checksums;** the environment allowlist (no service URL in a\n    step's environment); the `java` field;\n  - **digest and store identity:** manifest determinism, the CHECK, the drift test;\n  - **Kafka settings and their relations.**\n- **Spark-marked:** a tiny job on a `write_snapshot` snapshot (tests/conftest.py) through\n  `Worker` with SQLite and `MemoryQueue`.\n- **Live** (gated by `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP`):\n  - the acceptance cases above;\n  - a standby that receives the next message only after the primary exceeds a short\n    `max.poll.interval.ms`;\n  - store-operation durations recorded (informational).\n- **Mutation script:** three new mutations — a reconnect inside a transaction, disconnects treated\n  as conflicts, and `ping(reconnect=True)` in place of the factory.\n\n**Guarantee.**\n- Acceptance still goes only through the token guard, now also binding the digest.\n- Self-fence, watchdog and lock only stop or delay work.\n- The sweep and `cleanup` never touch valid or accepted attempts.\n\n**Deferred.** A unique index on accepted attempts. E1 measures whether the token guards alone\nkeep the guarantee, so this is decided after M3, in M6.\n\n### M3 — Recovery experiments E1 and E2\nBranch `feature/recovery-experiment` · Tooling Claude Code · Experiment: the project author,\ntutored · after M2.\n\n**Claude's tooling.**\n- **Session harness.** One process starts the worker(s), the standby and the reconciler, performs\n  injections, restarts crashed workers after the Part A delay, and logs everything (UTC, from the\n  host clock).\n- **Injections:**\n  - crashes at `WORKER_FAULT_POINTS` (worker.py:54-59), carried out as a real SIGKILL and fired\n    once per job (recorded in the events and `attempt.json`);\n  - SIGKILL during a step;\n  - SIGSTOP and SIGCONT of the worker alone or of the whole tree, always from the wait loop and\n    never inside a transaction;\n  - `docker compose restart` of Kafka or MySQL at a chosen phase;\n  - holding a worker at `after_pipeline` while MySQL restarts.\n- **Batch lifecycle:**\n  - a fresh MySQL container, store id, topic and consumer group;\n  - reference runs (direct CLI, same commit, under the host lock);\n  - drain at the end;\n  - `jobs export` and `memory.peak` before `down -v`. The collector reads files only.\n- **Session helpers** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:\n  machine checks adapted to Docker running, with the memory threshold from M2's dry runs; two\n  windows; `case n`; watcher; abort; note.\n- **Collector** `analysis/collect_recovery_measurements.py --batch`:\n  - imports `compare_tables` unchanged;\n  - writes `measurements.csv` and `acceptance.json`, with criteria 1–5 plus \"6 guarantee\";\n  - exits 1 on any failure.\n- **Batches** live in `data/outputs-recovery/<batch>/`.\n\n**The author's `docs/recovery-experiment.md`.** Claude scaffolds Parts A and B, History and the\n`Author:` line.\n- **Part A, decided by the author:**\n  - the cases;\n  - repetitions;\n  - the job size: the recommendation is calendar-year for every case, with stride 21 only in M2;\n  - lease, renewal, reconcile and restart-delay settings;\n  - `--max-attempts`;\n  - deadlines per case: lease + reconcile interval + publication grace + session timeout +\n    restart delay + attempts left × attempt limit;\n  - memory thresholds: suggested peak + 0.5 GiB free; with the host lock, at most one tree runs;\n  - metric definitions;\n  - predictions;\n  - acceptance criteria;\n  - stop rules.\n- **Draft cases:**\n  - a crash at each worker fault point, and during step 2;\n  - a worker-only stall and a whole-tree stall;\n  - Kafka restart while idle, during a submit, and during a run;\n  - MySQL restart during a run, shorter and longer than M (the self-fence margin);\n  - MySQL restart while held at `after_pipeline`: one execution predicted if MySQL is back before\n    F, two otherwise.\n- **Metrics per job:**\n  - injection time;\n  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;\n  - recovery: the next `claimed_at`;\n  - completion: `finished_at`;\n  - executions;\n  - **number** of accepted attempts;\n  - correctness: checks, plus content against the reference, plus digest;\n  - category: succeeded, failed (attempts exhausted), lost (not terminal by the deadline), or\n    submit outcome unknown.\n- **E1 cross-check.** The author's own SQL for accepted attempts per job must agree with\n  `invariant_violations()`.\n\n**Acceptance.**\n- One batch meets every Part A criterion.\n- Across all batches: zero lost jobs, zero jobs with two accepted results, and exactly one\n  correct, digest-bound accepted result per succeeded job.\n- Peaks are recorded per batch.\n- Commits follow the precedent: tooling → Part A (before any measured run, author-approved) →\n  dry batches → the formal session (the author) → Part B → status.\n\n**Tests:** harness, collector and helper tests in the pattern of `test_caching_collector.py` and\n`test_caching_session.py`, including planted problems, each failing its criterion.\n\n**Guarantee:** measured under failures; no new write path.\n\n### M4 — Redis cache for summary queries, with fallback\nBranch `feature/result-cache` · Infrastructure Claude Code · Cache logic: the project author,\ntutored · after M2.\n\n**Identity**, the contract the author's key must meet (the tests pin it):\n- **Run identity is the run digest** (M2.1), never the run id or path. Job and run ids repeat\n  after a database is recreated, and paths can be reused.\n- **The key** covers:\n  - the cache format version;\n  - the engine (PySpark version);\n  - the run digest;\n  - the query name;\n  - the query definition hash (SHA-256 of its SQL text);\n  - the canonical full parameters: every parameter including defaults, in canonical JSON with\n    sorted keys and normalized types.\n\n  The key is a hash of that tuple behind a readable prefix. The stored value repeats the tuple,\n  and a mismatch on read counts as a miss.\n- **Pinned by tests:**\n  - equal run ids with different digests never share a key;\n  - a changed parameter or SQL text changes the key;\n  - equal requests give equal keys across processes.\n\n**Accepted-run policy** (`runs.py` resolver, Claude). A run is servable only if one of the\nfollowing holds; anything else is refused, with no fallback to unaccepted runs.\n- **(a) A job run.** In the job table, under its `store_id`, the job is succeeded and its accepted\n  attempt's recorded `result_digest` equals the folder's manifest digest.\n- **(b) A historical run.** The reviewed registry `docs/accepted-runs.json` (committed) lists it\n  with path, digest, the basis for acceptance (`run.json` status ok, all checks 0, `verify.json`\n  clean, the spec §8 reference) and the author's approval date. The folder's digest must match.\n  - `python -m etf_risk.runs register` computes and checks the entry. The digest is stored in the\n    registry, so the historical folder is never written to.\n  - This lets M4 and E3 use the run of record without creating job rows outside\n    `accept_result`.\n  - **Pause, an authorship decision:** which run to register. `run-20261013T043848Z-4` has a clean\n    `verify.json`. The documented `-2` has none, and registering it would mean running verify into\n    it first. The four runs' tables are identical (plots.py:15-16).\n\n**Per-query check.** Each query compares file sizes and modification times against the manifest\nand fully re-hashes on any mismatch. `serve` re-hashes at startup, and `--verify-full` re-hashes\non demand. E3 reports the resolver's cost separately.\n\n**Claude's part.**\n- **Compose `redis`:**\n  - pinned by digest;\n  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, persistence off;\n  - 128m `mem_limit` and `memswap_limit`;\n  - port `127.0.0.1:6380`;\n  - a `PING` healthcheck.\n- **The `cache` group.**\n- **`src/etf_risk/summary.py`:**\n  - named queries over `paired/`. The author moves their own SQL from `analysis/sql_*.py`; those\n    scripts are not edited (documents cite them by hash), and moving the SQL is an authorship\n    step;\n  - a one-shot CLI (new process) and a warm mode (one SparkSession, JSON-lines requests on stdin\n    and stdout);\n  - the resolver and the registry tool;\n  - contract tests and fakes: a Redis stand-in that can go \"down\", and a live fixture gated by\n    `ETF_RISK_REDIS_URL`;\n  - a Spark-marked test that the queries on the registered run reproduce spec §8 (windows 529,\n    466, 311, 174, 310), skipped without `data/`.\n\n**The author's part.** `src/etf_risk/cache.py`, scaffolded:\n- the key and normalization, under the identity contract;\n- serialization;\n- cache-aside get-or-compute;\n- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while\n  Redis is down, decode errors treated as misses;\n- counters.\n\n**Acceptance.**\n- Contract tests pass offline and live.\n- With Redis stopped, every query returns the Spark result, within the timeout and breaker bound.\n- Unaccepted, unregistered or changed runs are refused.\n- Redis peak ≤ 128 MiB.\n- The runbook's E3 commands work as written.\n\n**Tests:** the identity tests above; resolver refusals (a non-accepted attempt; a digest mismatch;\nan unregistered historical run); fallback; equal results; live Redis; the spec §8 test.\n\n**Guarantee:** reads accepted runs only, verified by digest; never writes the job table.\n\n### M5 — E3: new Spark process vs warm Spark session vs Redis\nBranch `feature/result-cache-experiment` · Tooling Claude Code · Experiment: the project author,\ntutored · after M4.\n\n**Configurations** (Part A):\n- N: a new process per query;\n- W: a warm session, with no cache;\n- R: a warm session plus Redis, at hit rates set by repeats (e.g. 0, 50 and 90%);\n- F: Redis stopped, then recovered.\n\n**Key space.** Queries × accepted runs (the registered run of record and M2/M3 job runs) × any\nparameters the author adds.\n\n**Measures:**\n- client-side monotonic latency per query;\n- the resolver's cost, separately;\n- realized vs designed hit rate;\n- the warm session's process-tree peak (marker sampler);\n- Redis `memory.peak` and `used_memory_peak`.\n\n**Deliverables:** `docs/result-cache-experiment.md`, `docs/result-cache-session.zsh`,\n`analysis/collect_result_cache_measurements.py`, and a batch in\n`data/outputs-result-cache/<batch>/`.\n\n**Acceptance:** one batch meets every Part A criterion; drift is reported.\n\n**Tests:** collector (planted problems), session helpers, and the hit rate the workload generator\nproduces.\n\n**Guarantee:** read-only for the job table.\n\n### M6 — Architecture, report and demo\nBranch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · after M3\nand M5.\n\n- **`docs/architecture.md`** (new). It covers:\n  - batch pipeline plus extension;\n  - native vs Compose placement;\n  - failure model, guarantee and where it is enforced and checked;\n  - time and deadline rules (M2.4–M2.5);\n  - cache identity and the accepted-run policy;\n  - budget ledger;\n  - runbook.\n- **Spec §5's diagram:** gains `jobs/` and Compose, and its node ids are renamed.\n- **Figures X5 (E1/E2) and X6 (E3)**, added together as X1–X4 were:\n  - `plots.py` (`FIGURES`, `DOCUMENTED`, the tuple in `compare_documented`);\n  - `test_plots.py` (12 → 14);\n  - CSV copies and their README rows;\n  - every \"twelve figures\" and \"X1–X4\" mention.\n- **Spec:** §8 \"What the recovery experiments showed\" and \"What the result-cache experiment\n  showed\"; §9 and §11 marked implemented, with the final ledger.\n- **`results.md`:** a new extension section. §7 changes only with the author's re-approval.\n- **README:** status and the full runbook.\n- **`demo.md`:** submit; kill the worker mid-run; watch `status --check` recover; cache miss →\n  hit → Redis stopped → fallback → restart.\n- **The deferred unique-index decision.**\n\n**Acceptance:**\n- numbers traced to committed CSVs and records;\n- `plots --check` passes;\n- every command run as written in a fresh worktree;\n- links valid;\n- the author approves the conclusions.\n\n**Tests:** `test_plots.py`; a link check; the full offline suite.\n\n**Guarantee:** documentation only.\n\n## Separate workstreams (outside M1–M6)\n\nNo milestone branch touches these files, and no milestone waits on them.\n\n- **W1 Data verification** (`feature/data-verification`, own plan):\n  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);\n  - terms of use;\n  - the cause of the Adj Close steps;\n  - the 36 unverified days;\n  - data-sources.md's missing AI header.\n- **W2 Privacy-hook fixes** (`fix/transcript-privacy`): the uncommitted hook, test and transcript\n  edits, plus spec §10's hook items. Claude touches the hook only when asked.\n- **W3 AI-log review.**\n  - **Scope:** the 68 untracked folders (including the sessions behind PRs #7–#9) and each\n    milestone's logs.\n  - **Reviewer:** the author.\n  - **Where commits go:** following the precedent, each review lands as a separate \"Add reviewed\n    AI logs for …\" commit, last on the milestone branch (ed71796). Logs reviewed after a merge go\n    on a `docs/ai-logs-<date>` branch.\n  - **Never mixed with code.**\n  - **Also in scope:** `docs/ai-usage/README.md`'s attribution of the hook to Codex only, and the\n    redaction of other projects' names that appeared in this planning session's tool output.\n\n## Verification (end to end)\n\n- **Per milestone:**\n  - the offline suite (`uv run --group measure --group plots pytest`) with counts;\n  - Spark-marked tests;\n  - live suites on fresh containers (`--group jobs`, `--group cache`);\n  - `status --check` empty after every live run;\n  - the mutation script;\n  - the lock diff;\n  - measured peaks against the ledger.\n- **System, after M6:** in a fresh worktree on `main`, follow the runbook from\n  `uv sync --frozen` through smoke runs of E1/E2 and E3. Check that:\n  - every accepted run passes its checks, matches its reference by content, and matches its\n    recorded digest;\n  - no overlapping Spark trees appear in the event logs;\n  - `plots --check` passes;\n  - peaks are within the ledger.\n\n## Known pause points\n\n- **Before M2 starts:** report the two timing corrections (absolute deadlines; no database-time\n  bound in the safety argument).\n- **M2:** any change to the M2.4 values that breaks or restates M ≥ t_w + G + ε; any store change beyond\n  `job_store` and `result_digest`.\n- **M3:** Part A approval (cases, job size, thresholds, deadlines); the author runs the formal\n  session.\n- **M4:** the author writes `cache.py` and moves their SQL into `summary.py`; the choice of which\n  historical run to register.\n- **M5:** Part A approval; the formal session.\n- **M6:** the conclusions' wording; the unique-index decision.\n",
  "planFilePath": "~/.claude/plans/please-turn-this-outline-cozy-candy.md"
}
```

## 185. User — 2026-10-23T12:23:51.327Z

### Tool result

```
User has approved your plan. You can now start coding. Start with updating your todo list if applicable

Your plan has been saved to: ~/.claude/plans/please-turn-this-outline-cozy-candy.md
You can refer back to it if needed during implementation.

## Approved Plan:
# Plan: finishing the systems extension (spec §11) in six reviewed milestones

Status: revision 3 (2026-10-23).
- **M1.** The author approved it, to start once `fix/measure-process-kinds` is merged.
- **M2.** The timing design (M2.4–M2.5) was corrected after the author's second review: absolute
  monotonic deadlines, and no database-time bound in the safety argument. The corrections are
  reported again before M2 starts.

## Context

Stages 1–4 and the extension's job queue are merged into `main` (f058095): PR #7 (job table,
fencing), PR #8 (Kafka delivery, reconciler), PR #9 (Stage 4). Spec §11 still lists as planned:
- the real pipeline in the worker (today `SimulatedPipeline`);
- the recovery experiments E1/E2;
- the Redis result cache;
- the cache experiment E3;
- their documentation.

This plan turns the author's six-point outline into milestones M1–M6, one branch and PR each. Each
milestone has deliverables, acceptance criteria, tests and a statement of how it keeps the
guarantee. Four cross-cutting requirements run through all of them: code provenance for `jobs/`,
reproducible dependencies, startup commands, and measured memory budgets. Data verification, the
privacy-hook fixes and AI-log review stay in separate workstreams.

State observed on 2026-10-23:
- the main worktree is on `fix/measure-process-kinds` (97c35f3, pushed, not merged), with
  uncommitted privacy-hook work (W2);
- 68 untracked AI-log folders exist;
- another project's containers share the Docker VM;
- `gh` is not installed.

## Decisions and working mode (the author, 2026-10-23)

- **Placement.** The worker, reconciler and submit run natively on the host. MySQL and Kafka (and
  Redis from M4) run in Compose.
- **Authorship.** The spec §11 split stays.
  - Claude Code writes M1, M2 and all tooling.
  - The author writes `cache.py`, the experiments and the E1 SQL cross-check, with tutoring.
- **Six milestones**, as in the outline.
- **Working mode after approval.** Claude proceeds autonomously with routine work inside each
  milestone: code, tests, docs, dry runs and commits on the milestone branch.
- **When Claude pauses and asks.**
  - **Material design changes:** anything this plan does not describe; any change to the store's
    guards or SQL beyond the two additive changes in M2.1; any change to the time inequality in
    M2.4.
  - **Authorship decisions.**
  - **Formal experiment approval:** Part A sign-off, and the author running the formal session.
- **Push and merge.** The author pushes, or tells Claude to push, and opens and merges each PR.
- **Reports.** Every milestone ends with a report: what was done, what was found and fixed, test
  counts and measured peaks.

## At a glance

| # | Branch | Written by | Needs | Main deliverable | Done when |
|---|---|---|---|---|---|
| M1 | `feature/extension-baseline` | Claude | `fix/measure-process-kinds` merged | audit report; recursive provenance; `jobs` group; runbook skeleton; peak helper; mutation script | provenance covers `jobs/`; lock only adds; live suite 379 or explained; mutations caught |
| M2 | `feature/worker-pipeline` | Claude | M1 | real pipeline; renewals with monotonic deadlines; watchdog and host lock; tree cleanup; reconnect; store identity; result digest; CLI | crash, stall, timeout and restart cases end with one accepted, correct, digest-bound result and no overlapping Spark trees |
| M3 | `feature/recovery-experiment` | author (tutored); tooling Claude | M2 | E1/E2 document, harness, collector, batch | Part A met; no lost job; no second acceptance |
| M4 | `feature/result-cache` | author: `cache.py`; Claude: Redis, `summary.py`, `runs.py` | M2 | cache-aside keyed by run digest and full query; accepted-run policy; fallback | contract tests pass; same results with Redis down; the run of record is usable through the reviewed registry |
| M5 | `feature/result-cache-experiment` | author (tutored); tooling Claude | M4 | E3 document, harness, collector, batch | Part A met |
| M6 | `docs/extension-report` | Claude drafts; author approves | M3, M5 | architecture, results, demo, X5–X6 | numbers traced; commands run as written |

M4's code can be written while M3's formal session runs (ground rule 6); it does not touch M3's
files.

## Ground rules for every milestone

1. **The guarantee** (spec §11): each job accepts at most one result, every succeeded job has
   exactly one, and a job may execute more than once.
   - **Enforcement.** Only the token-guarded UPDATEs in `jobs/store.py` enforce it.
   - **Checking.** `INVARIANT_QUERIES` / `invariant_violations()` (store.py:127, :481) check it
     after every test scenario, every worker run and every experiment batch.
   - **Accepting.** Nothing but `JobStore.accept_result` produces an accepted attempt.
   - **No reconnect inside a transaction** (M2.8). It could break the guarantee: the rest of a
     transaction would commit statement by statement.
   - **Cleanup** never touches an accepted or valid active attempt.
   - **The cache** serves accepted runs only and never writes the job table.
   - **No overlap.** No replacement Spark work overlaps a surviving earlier process tree (M2.5).
2. **Authorship.**
   - For the author's parts, Claude prepares scaffolds (signatures, docstrings, TODOs, contract
     tests) and reviews, but does not fill them in.
   - New files carry an `AI contribution:` line.
   - Experiment documents carry an `Author:` line saying the author wrote Part A and the answers
     with tutoring, unlike earlier experiments where Claude drafted Part A
     (caching-experiment.md:56).
3. **Git.**
   - Each milestone has its own worktree (`.claude/worktrees/<name>`) from up-to-date `main`, with
     a `data` symlink to the main worktree's `data/`. M1 changes `.gitignore`'s `/data/` to `/data`
     so the symlink is ignored too.
   - Stage files by explicit path only.
   - Merge with merge commits; never squash or rebase.
   - Commits end with the Co-Authored-By trailer.
   - Formal sessions run on a merged, clean commit whose SHA lands in every record, with no
     commits during a session.
4. **Privacy.** `data/` and the private plan stay out of Git. Never print memory files,
   `.git/info/exclude`, app lists, or other projects' container or session names in tool calls.
   Helpers count other containers without naming them. Child processes get an allowlisted
   environment, so service URLs and passwords never reach the pipeline steps.
5. **Measurement sessions.** While one runs, other sessions only write and review. They wait for
   the explicit end, then check that the worktree is unchanged.
6. **Wording.** Use explicit counts. Claim nothing beyond what was measured. Write "one process",
   never "one core". Give each experiment a "not claimed" list.

## Cross-cutting requirements

**A. Code provenance for `jobs/`.**
- **Gap.** `provenance.code_state()` hashes only `PACKAGE_DIR.glob("*.py")` (provenance.py:62).
  No record identifies `jobs/*.py` or `jobs/schema/*.sql`, and a plain recursive glob would
  collide on `__init__.py`.
- **M1.** Hash every `*.py` and `*.sql` under `src/etf_risk/`, keyed by package-relative POSIX
  path. Top-level keys stay as they are, so old records remain comparable.
- **From M2.**
  - `attempt.json` and every experiment record carry `code_state()`.
  - Each accepted result is bound to its run digest in the job table (M2.1).
- **Authorship provenance.** An origin table in `job-queue.md` maps each module → commits
  (eec1032, e2806bd, cd72957) → PR → the tests that verify it. The `AI contribution:` lines stay.

**B. Reproducible dependencies.**
- **Gap.** `pymysql[rsa]==1.1.1` and `confluent-kafka==2.16.0` come in through `uv run --with`
  (docker/compose.yaml:13; test docstrings) and are not in `uv.lock`.
- **Groups.**
  - M1 adds a `jobs` group with these pins.
  - M2 adds `psutil==7.2.2` to that group; it is already locked through `measure`.
  - M4 adds a `cache` group with an exact `redis` pin.
- **Lock changes** may only add packages. numpy 2.5.4, pandas 2.3.3, pyspark 4.2.0, pyarrow 26.0.0
  and psutil 7.2.2 stay unchanged, checked with a lock diff and `uv lock --check`.
- **Commands** use `--group …` and `uv sync --frozen`.
- **Images** are pinned by digest. Redis follows the Kafka rule: the newest release at least two
  weeks old.
- **Host tools** are recorded with each formal session (2026-10-23: uv 0.11.16, Java 17.0.10,
  Docker 28.3.0, Compose v2.38.1, VM 3.83 GiB).
- **Out of scope:** the NumPy pin.

**C. Startup commands.**
- **Runbook.** A README section (skeleton in M1, filled by M2, M4 and M6) gives copy-pasteable
  commands for:
  - **Setup:** the worktree and `data` symlink; the test services.
  - **The E1/E2 stack:** Compose `mysql kafka`; then `init-db`, `create-topic`, worker,
    reconciler, submit and `status`.
  - **The E3 stack:** Compose `redis`, the query CLI and the warm query service.
  - **Teardown:** export first, then `down -v`.
- **Readiness.** A service is ready only after a check that matches what will use it:
  - MySQL: a login plus `SELECT 1` (its healthcheck answers before logins work,
    docker/compose.yaml:35);
  - Kafka: the batch topic's metadata and the group coordinator are available;
  - Redis: `PING`.
- **Acceptance.** The commands are run exactly as written in a fresh worktree.

**D. Measured memory budgets.** The spec §11 ledger records component, limit, measured peak,
method, date and commit.

| Component | Budget | Measured | Source |
|---|---|---|---|
| MySQL container | 512 MiB | 324–398 MiB fresh; 472 after two runs; 511 after ~2 h | spec §11 |
| Kafka container | 640 MiB | 354–478 MiB; 516 with mutation checks | spec §11 |
| Pipeline container | 2.5 GiB | 2,282 / 2,342 MiB, stride 21 | spec §11 |
| Native stride-21 tree | `measure` stop 4.8 GiB | 1.27 GiB with 1.3–1.6 GiB free; 2.62–2.73 GiB with 3.0–3.5 GiB free | spec §8, experiments.md |
| Native calendar-year tree | — | not measured (M2) | |
| Worker, reconciler, submit | from M2 dry runs | — | |
| Redis container | 128 MiB, `maxmemory` 32 MiB | — (M4) | |
| Warm query service | from M4 dry runs | — | |

- **Budgets** are set at the review gate from dry runs, then checked; never from the run that
  checks them.
- **Container peaks** come from cgroup `memory.peak` through a helper (M1). They are read before
  every injected restart, since a restart may reset them; M2 verifies whether it does.
- **Native peaks** come from a marker-based sampler (M2). `TreeSampler` misses processes that were
  re-parented to launchd.
- **Before any formal session or budget measurement:**
  - zero containers outside this project (counted, not named);
  - ports 3307, 9094 and 6380 free;
  - host available memory at or above the Part A threshold.
- **Each recovery batch** starts on a fresh MySQL container with a fresh topic and consumer group.
- **A budget exceeded** stops the session.

## Milestones (numbered as in the outline)

### M1 — Read the whole project; bring the code up to date
Branch `feature/extension-baseline` · Claude Code · after `fix/measure-process-kinds` is merged.

**Audit.** The report lists the following. Items inside this plan are fixed as routine work;
anything else waits for the author.
- **Reproducibility:**
  - gaps A, B and C;
  - the 22 mutation checks exist only as prose;
  - the merged worktrees `job-queue` and `job-table` are clean, so they can be removed.
- **Missing operations:**
  - no entry point in `jobs/` (the §11 "submit CLI" does not exist);
  - logging is never configured;
  - nothing is timed;
  - `published_at` is cleared by the claim;
  - a crash before the claim leaves no trace;
  - Kafka group timings are unpinned defaults while `serve()` runs the pipeline inside its poll
    loop;
  - **no reconnect:** `JobStore` keeps one connection for life (store.py:286-292, 526), so after a
    MySQL restart the reconciler fails every pass and `serve()` raises after 5 retries;
  - no supervisor.
- **Pipeline CLIs** (findings only; the worker works around them in M2.3):
  - exit 1 means both "checks failed" or "mismatch" and any uncaught exception;
  - `run.json` is written only in `finally`;
  - verify misses `JSONDecodeError`;
  - verify's `spark.stop()` is not in a `finally`;
  - paths are relative to the working directory: `--processed-root` and verify's `windows_dir`;
  - windows refuses only an existing `config.json`, while README:224 says an existing folder.
- **Documentation drift:**
  - job-table.md's claim SQL and "apart from submit";
  - job-queue.md:90;
  - dated status blocks in job-table.md:97-103 and job-queue.md:146-160;
  - spec §5's diagram, its "Every box is implemented", and its E2–E4 node ids;
  - spec.md has no AI header.
- **Test helpers:** `WorkerEnv.check` is tied to the simulated `result.json`.

**Fixes:**
- provenance (A);
- the `jobs` group and `--group jobs` everywhere (B);
- `.gitignore` `/data/` → `/data`;
- the runbook skeleton (C);
- the `memory.peak` helper (D);
- job-doc drift and stale status;
- the module origin table;
- a mutation-check script: each mutation a patch applied in a scratch worktree with a timeout.
  The list is rebuilt from the surviving descriptions (job-table.md:98-102, job-queue.md:157-164,
  e2806bd's message) and documented as rebuilt, not claimed identical to the original 22;
- removal of the merged worktrees.

The pipeline CLIs and the analysis code are not changed.

**Revalidation:** the offline suite; the live job suite on fresh MySQL 8.4.13 and Kafka 4.3.1 with
`--group jobs`; the mutation script; peaks through the helper.

**Acceptance.**
- A test enumerates every `*.py` and `*.sql` under `src/etf_risk/` and finds each in
  `source_sha256` under a unique key, with top-level keys unchanged.
- The lock diff only adds packages.
- The live suite passes with 379 cases, or the difference is explained.
- Every rebuilt mutation fails a test within its timeout.
- Peaks are within budget.

**Tests:** new cases in `test_provenance.py`; job suites on SQLite and live; the mutation script.

**Guarantee:** no store change; the mutation script re-proves that each guard is tested.

### M2 — The worker runs windows → spark_pipeline → verify
Branch `feature/worker-pipeline` · Claude Code · after M1. Two stages in one PR, with a progress
report between them (not a pause):
- **M2a:** M2.1, M2.8, M2.9, M2.10 and the CLI, exercised with the simulated pipeline.
- **M2b:** M2.2–M2.7, the real pipeline.

#### M2.1 Identity: store, output layout, result digest
- **Store identity.**
  - `init-db` creates a one-row table `job_store` (`store_id`, a random 128-bit hex; `created_at`;
    `schema_version`).
  - Job and attempt ids repeat after a database is recreated, so everything outside the database
    uses `store_id` with them: output paths, process markers, events and cache provenance.
- **Output layout.**
  - The worker passes `output_root/<store_id>` to `claim()`, giving folders
    `<root>/<store_id>/job-<id>-attempt-<n>/`.
  - The store already builds the path from the given root (store.py:356), so the store needs no
    change for this.
  - A recreated database never collides with old folders, which today would fail every job
    (worker.py:128-132).
- **Run digest.**
  - `src/etf_risk/runs.py` (new; shared with M4) writes a canonical manifest of the Spark run
    folder: sorted relative paths, sizes and SHA-256 per file.
  - Its SHA-256 is the run digest, the run's immutable identity.
  - The worker writes `manifest.json` in the attempt folder before acceptance.
- **Bound at acceptance** (additive store change; the guards are unchanged):
  - `job_attempts.result_digest CHAR(64)` with a CHECK `(outcome = 'accepted') = (result_digest
    IS NOT NULL)`;
  - `accept_result(claim, digest)` sets it in its existing `job_attempts` update, inside the same
    token-guarded transaction (store.py:398-402);
  - the idempotent repeat path also compares the digest;
  - both schema files, the drift test and the invariant queries are updated.

  This ties the accepted decision and the accepted content together atomically.
- **Simulated pipeline.** `SimulatedPipeline` produces a digest too, so all existing scenarios
  keep running.

#### M2.2 Steps and environment
- **Steps.** Each step runs behind the launcher (M2.5) as `sys.executable -m etf_risk.<module>`,
  with absolute paths only:
  1. `windows --snapshot … --kind … --window-days … --stride … --anchor … --processed-root <abs>
     --out-root <run_dir>/windows --name <name>`;
  2. `spark_pipeline --windows … --out-root <run_dir>/output --run-id <run id>`;
  3. `verify --run …`.
- **Job parameters** (`params.py`, a frozen dataclass): snapshot, kind, window days, stride,
  anchor, sample ticker. Unknown keys are refused.
- **Worker settings:** the processed root and the output root, both recorded in
  `attempt.json`.
- **Input checksums.** `submit` computes `input_checksums` from the files `windows.py` records in
  `inputs_sha256`. The worker re-checks them before step 1; a mismatch is not retryable.
- **Step environment** (allowlisted):
  - `cwd` = `<run_dir>/.work`, which also catches `spark-warehouse`;
  - `TMPDIR` = `.work/tmp`;
  - `SPARK_LOCAL_DIRS` = `.work/spark`;
  - `SPARK_SUBMIT_OPTS="-Djava.io.tmpdir=<abs>/.work/jtmp -XX:-UsePerfData"`, which the Spark
    launcher reads. The macOS JDK ignores `TMPDIR`.
  - `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` = `sys.executable`. Otherwise workers use
    `python3` from PATH (pyspark/core/context.py:342).
  - Never `JAVA_TOOL_OPTIONS` or `_JAVA_OPTIONS`: their "Picked up …" notice would replace the
    Java version that `environment()` records (spark_pipeline.py:635-636). A test checks
    `run.json`'s `java` field.
  - The directories are created first.
  - Logs go to `<run_dir>/logs/<step>.log`.

#### M2.3 Acceptance rule and failure classification
- **Accept only if all hold:**
  - every step exits 0;
  - `run.json` status is `ok`;
  - every `checks.json` count is 0;
  - `verify.json` has no mismatch and the same breached windows;
  - every table has `_SUCCESS`.
- **Then:**
  1. remove `.work`;
  2. write `attempt.json`;
  3. write `manifest.json`;
  4. **renew**;
  5. `accept_result(claim, digest)`.

  Nothing in the folder changes after acceptance; a test compares the manifest before and after.
- **Classification**, decided from the records, never from the exit code alone:
  - **not retryable:** a checksum error (exit 3); `run.json` status `checks_failed`; a verify
    mismatch; a parameter or input-checksum error;
  - **retryable:** a signal, a timeout, status `failed`, a missing record, or "execution lock
    busy" (M2.5).

  Retryable failures requeue until `max_attempts`.

#### M2.4 Time and deadlines
*Corrected 2026-10-23 after the author's review. The corrections are reported again before M2
starts.*

- **Safety does not rest on database timing.**
  - No overlapping Spark work is ensured only by the launcher's watchdog and the host execution
    lock (M2.5). Neither ever waits on the database.
  - No time limit is claimed for a whole database operation. Per-I/O read and write timeouts do
    not bound an operation made of a reconnect, several statements and a rollback, so the earlier
    "W = 13 s" claim is withdrawn.
  - The worker's own self-fence and all database timeouts serve liveness only.
  - Correctness (one accepted result) never depended on time.
- **Clocks.**
  - Lease times in the database stay on the store's wall clock (UTC).
  - Every local deadline uses the host's monotonic clock: `time.monotonic()`, the same
    system-wide clock in the worker and the launcher.
  - The worker sends the launcher **absolute** monotonic deadlines, never remaining durations.
  - At launch, a handshake checks that both processes read the same clock: the launcher's reading
    must be at least the worker's sent reading, and within 1 s of it. Otherwise the launcher
    refuses to start.
- **The deadline.**
  - After each successful renewal, the worker computes `F = m₀ + L − M` and sends it with a
    sequence number. `m₀` is the monotonic time just *before* that renewal started; the database
    lease began at or after `m₀`.
  - The launcher terminates its tree once `now ≥ F`. Termination takes at most G = 7 s (5 s after
    SIGTERM, then SIGKILL, confirmed within 2 s).
  - The watchdog checks every t_w = 0.5 s, so the tree is gone by `F + t_w + G`. That is before
    the lease can expire (`m₀ + L`) whenever **M ≥ t_w + G + ε**.
  - Draft: **M = 10 s** (0.5 + 7 + 2.5), with L = 60 s (`DEFAULT_LEASE`).
  - This holds whatever the worker thread is doing: blocked in a database call, frozen or dead.
  - Changing these values means restating this inequality, and that is a pause point.
- **Wall and monotonic clocks diverging.** A wall-clock jump can make the database lease expire
  before F, and a takeover can then come early. The replacement's launcher still cannot start
  Spark until the lock is free and no earlier attempt's process survives, which is by F + G at
  the latest.
- **The worker never starts a step or accepts once `now ≥ F`.**
  - It checks F on every 1 s tick and after every store call.
  - It renews before each step and before acceptance.
  - A launcher given a deadline that has already passed refuses to start.
- **Liveness settings** (bounded waits, not a safety bound; drafts, fixed from M2a's
  measurements):
  - **Session settings:** `connect_timeout` 3 s; `read_timeout` and `write_timeout` 5 s per I/O
    (new optional arguments of `connect_mysql`; defaults unchanged); `innodb_lock_wait_timeout`
    2 s, below the read timeout, so lock waits end as definite 1205 conflicts; session
    `wait_timeout` 120 s, so a frozen client's open transaction cannot hold row locks
    indefinitely.
  - **Retries and renewals:** the existing `CONFLICT_RETRIES` = 3 runs; a renewal every 10 s.
  - **What this means for E2.** With M = 10 s, a run can survive a database outage of up to about
    L − M − renewal interval ≈ 40 s. That number feeds the E2 predictions; it is not a claim.
  - **Recording.** Store-operation durations are recorded in the events.
- **Kafka.** It is used only between runs, with `socket.timeout.ms` pinned at 10 s. A commit that
  blocks before a run cannot cause overlap: the renewal before each step returns false if the
  job was taken over meanwhile, and the step never starts.
- **Retry rules:**
  - `renew`: retried at the next interval;
  - `accept_result` and `fail_attempt`: retried on disconnects only, until F; `accept_result` is
    idempotent for its token;
  - `claim`: raises into `serve()`'s rewind and retry;
  - `submit`: never retried; the CLI exits with a distinct "outcome unknown" code;
  - reconciler passes: bounded, logged and repeated.

#### M2.5 No overlapping Spark work: watchdog and host execution lock
A SIGSTOPped worker can neither renew nor check its deadline, and its pipe to the launcher stays
open. Two independent layers therefore protect against overlap, in addition to the worker's own
self-fence.
- **Watchdog (the launcher process, one per step).**
  - The worker starts the launcher with `start_new_session=True` and a keepalive pipe as its
    stdin.
  - The launcher keeps an absolute monotonic deadline. It starts from the value sent after the
    renewal-before-step and changes only through the worker's messages, each carrying an absolute
    deadline and a sequence number.
  - **Loop order:**
    1. If `now ≥ deadline`, fire. Firing is terminal: no later message can extend it.
    2. Only otherwise, read the waiting messages. A message moves the deadline only if its
       sequence number is newer, its deadline is later than the current one, and its deadline is
       still in the future.

    So buffered messages read after a pause can never revive an expired watchdog. Because the
    deadlines are absolute, no message can push the deadline past the time the worker granted.
    The worker's end of the pipe is non-blocking, and a message that does not fit is dropped,
    which can only make the watchdog act sooner.
  - **Termination.** The launcher terminates its tree (M2.6) on EOF (the worker died) or when the
    deadline passes (the worker is frozen, stuck or blocked). Either way the tree is gone by
    F + t_w + G, before the lease can expire, without any action by the worker.
- **Host execution lock.**
  - Before starting a step, every launcher takes an exclusive `flock` on a host-wide file
    (default `~/.cache/etf-risk/locks/spark-exec.lock`; tests use their own path).
  - It then checks that no process carrying another attempt's marker survives (M2.6).
  - It passes the lock descriptor to the step's driver, so the lock is held while the launcher
    or the driver lives. PySpark closes inherited descriptors for the JVM, and the JVM exits when
    the driver's pipe breaks; the survivor check covers that window.
  - A launcher that cannot get the lock, or still sees survivors, within the lock-wait bound
    (step limit + G + 30 s) does not start Spark. It exits with "execution lock busy", and the
    attempt fails as retryable.
  - So even when the whole old tree is frozen (watchdog included) or the wall clock jumps, no
    replacement Spark run starts while an earlier tree survives. The session harness takes the
    same lock for its reference runs.
- **Renewal before each step and before acceptance.** A fenced worker never starts a new step.

#### M2.6 Terminating a process tree
- **Why not a group kill.** PySpark's daemon calls `os.setpgid(0, 0)` (pyspark/daemon.py:115),
  so its workers leave the step's group, and re-parented orphans escape child-walks.
- **Membership.** Every step process carries the marker
  `ETF_RISK_ATTEMPT=<store_id>:<run id>:<attempt key>`, where the attempt key is the first 16 hex
  digits of SHA-256(token). The token itself never leaves the worker. Members are found by session
  id (`os.getsid` = the launcher's pid; nothing in the tree calls `setsid`) as a prefilter,
  confirmed by the marker. A pid alone is never enough.
- **Sequence.** SIGTERM to all members (so the JVM can delete its scratch); wait 5 s; SIGKILL to
  survivors; rescan until none remain (bounded). The pids and the reason go to
  `logs/launcher.log`.

#### M2.7 Startup sweep: preserve valid active attempts
When a worker starts, it scans this host for marked process trees of its own `store_id` and looks
each attempt up in the store.
- **Preserved:** any tree whose attempt is still *valid active*, meaning the job is running and
  its current attempt number and token hash match. Its lease or watchdog decides when it ends;
  the sweep never shortens a valid attempt.
- **Terminated:** trees whose attempt has ended (expired, failed or accepted) or was taken over.
- **Ended attempts' folders:** their `.work` scratch is removed; the folder itself never is.
- **Left alone and reported:** trees of other store ids.
- **Database unreachable:** the sweep does nothing.
- **Folder listing.** `jobs cleanup` is dry-run only: it lists the folders of ended,
  non-accepted attempts. Deleting them is not part of M2.

#### M2.8 Database connections
- **Factory.** `JobStore` accepts a connection factory: `connect_mysql` with the M2.4 timeouts and
  session settings. It never uses `ping(reconnect=True)`, which drops `SET SESSION`.
- **Reconnect only at the start of an operation:** before BEGIN, after a ping when the connection
  has been idle for 60 s or more. Never inside a transaction. A connection that broke
  mid-transaction is discarded; the transaction's remaining statements never run on a new
  connection.
- **Disconnects:** PyMySQL 2003, 2006, 2013, server codes 1053, 1927 and 4031, `InterfaceError`,
  or `open == False` after an error. The connection is marked broken in the except path, before
  the ROLLBACK.
- **No ROLLBACK on a broken connection.** The store closes it instead; the server rolls back the
  open transaction when the session ends. A broken connection therefore costs no further I/O. A
  COMMIT that timed out may still have taken effect on the server, which is the existing "failed
  COMMIT" case, handled by idempotent repeats.
- **No replay.** The failed operation raises, as today.

#### M2.9 Kafka settings (pinned in `kafka.py`, with tests on values and relations)
| Setting | Value | Why |
|---|---|---|
| `group.protocol` | `classic` | `session.timeout.ms` is ignored under `consumer` |
| `heartbeat.interval.ms` | 3000 | pinned default |
| `session.timeout.ms` | 15000 | ≥ the broker's 6 s minimum, ≥ 3 heartbeats, < L |
| `max.poll.interval.ms` | attempt limit + G + 60 s | a legitimate run never leaves the group |
| `socket.timeout.ms` | 10000 | bounded commits and fetches |
- **Max-poll error.** It gets its own event.
- **Graceful stop** closes the consumer, so the group sees an immediate LeaveGroup.
- **Consequence for E2.** Under the classic protocol, a joining standby or restarted worker waits
  for a busy member to poll, and E2's recovery times include that wait.

#### M2.10 Supervision, graceful stop, events, CLI
- **Supervision.**
  - `jobs worker` restarts its serve loop in-process, with backoff, after transport errors only:
    disconnects, `ClaimRace`, non-fatal Kafka errors. Any other error exits non-zero.
  - SIGKILLed workers are restarted by the M3 harness after a Part A delay.
- **Graceful stop** (SIGTERM or SIGINT): stop polling, terminate the running tree, call
  `fail_attempt(retryable=True)`, close the consumer. On a job's last attempt this fails the job
  (store.py:416-417), so batches drain before stopping workers.
- **Event log.** Each process writes JSON lines, flushed per event:
  - delivered, claimed;
  - renewed, renewal failed;
  - step start and end, lock wait;
  - watchdog kill, fenced;
  - accepted, failed, requeued, published;
  - max-poll.
- **Attempt record.** `attempt.json` holds the worker id, store id, run id, steps (exit code,
  times), the input checksums as checked, the settings and `code_state()`.
- **CLI** `python -m etf_risk.jobs`:
  - `init-db`, `create-topic`, `submit`, `worker`, `reconciler`;
  - `cleanup` (dry run);
  - `status [--check]`: tables and `invariant_violations()`; exits 1 on a violation;
  - `export <dir>`: tables, violations and settings, for M3's batches.

**Deliverables.**
- **New modules:** `jobs/{pipeline,launcher,processes,params,events,__main__}.py` and
  `src/etf_risk/runs.py`.
- **Changes:** `store.py` (factory, budget, digest, store id), `mysql.py` (timeouts, `is_disconnect`),
  `kafka.py` (settings), both schema files.
- **Docs:** `job-queue.md` and `job-table.md` updated; the runbook's E1/E2 part.
- **Ledger rows:** idle available memory with the stack up; per-step peaks for calendar-year and
  stride 21; the Docker VM process's memory on the host.

**Acceptance** (native worker; MySQL and Kafka in Compose; fresh containers):
- **Normal runs.** A calendar-year job and a stride-21 job (no injection, no timing claims) end
  `succeeded`. Each has exactly one accepted attempt whose recorded digest equals its manifest.
  Each passes every check and verify. Each equals a direct CLI run by content, using the caching
  collector's `TABLE_KEYS` (collect_caching_measurements.py:74-75) and `compare_tables`
  (collect_partition_measurements.py:286), with `windows.parquet` compared by its window key.
- **Worker-only SIGSTOP during step 2.** Checked *before SIGCONT*:
  - no process of attempt 1 is alive by its watchdog deadline + G;
  - the lock is free;
  - attempt 2's Spark step started after attempt 1's last process exited (event times and the
    process scan);
  - attempt 1's renewal count is unchanged after attempt 2's claim.

  After SIGCONT, the old worker is fenced and writes nothing.
- **Whole-tree SIGSTOP** (worker, launcher and Spark). Checked *before SIGCONT*:
  - the replacement started no Spark process;
  - it waited on the lock or exited "execution lock busy";
  - no second Spark tree exists; the only one is the frozen tree.

  After SIGCONT, the old launcher terminates its tree at once, because its deadline has passed.
  The job ends with exactly one accepted result.
- **Worker SIGKILL during step 2.** No attempt process survives the lifeline grace, and the job
  is requeued after its lease and succeeds.
- **Timeouts.** An over-limit step is terminated and retried.
- **Database stalls.** `LOCK TABLES jobs WRITE` from another session, `docker compose pause mysql`,
  and `restart mysql`, each during a run:
  - store-operation durations are recorded, with no bound claimed;
  - the run either continues or its tree is gone by F + t_w + G, before its lease;
  - nothing needs a manual restart;
  - the job ends with one accepted result.
- **Kafka restart during a run.** The same outcome.
- **Startup sweep.** It terminates only ended attempts' trees, and preserves a live attempt run by
  another worker.
- **No leftovers.** The process scan shows no attempt processes. No new `spark-*`, `blockmgr-*`,
  `pyspark-*`, `snappy-*`, `libzstd-jni*`, `liblz4-java*` or hsperfdata entries appear in
  `/private/tmp` or `getconf DARWIN_USER_TEMP_DIR`. No new `spark-warehouse` appears in the
  repository.
- **Invariants.** `invariant_violations()` is always empty.
- **Earlier tests.** All earlier job tests pass on both stores.

**Tests.**
- **Offline:**
  - **launcher:** deadline kill; EOF kill; lock wait and refusal; survivor check; exit codes;
  - **tree termination:** a grandchild that calls `setpgid(0, 0)`, and a double-fork orphan; none
    survives a worker SIGKILL, a fence, a timeout or a worker-only SIGSTOP;
  - **deadlines:** a fake store whose calls block indefinitely. The watchdog still ends the tree
    by F + t_w + G, before `m₀ + L`, and no step starts and no acceptance happens after F;
  - **clock handshake:** a mismatched reading is refused;
  - **watchdog pause and resume with queued stale messages:**
    - (a) SIGSTOP the launcher. Queue messages with past deadlines, out-of-order sequence numbers
      and one future deadline. Keep it stopped past the current deadline, then SIGCONT. The tree
      is terminated at once, and the log shows the buffered messages ignored.
    - (b) The same, with a pause shorter than the current deadline. The deadline becomes exactly
      the newest valid absolute value; stale and out-of-order messages change nothing.
  - **sweep:** the rules of M2.7;
  - **reconnect:**
    - a disconnect between statements 1 and 2 never runs statement 2 on a new connection;
    - a COMMIT that took effect but whose reply was lost: a repeated accept returns True, with
      exactly one accepted attempt;
    - session settings after a reconnect;
    - the ping before an operation;
  - **classification, parameters, checksums;** the environment allowlist (no service URL in a
    step's environment); the `java` field;
  - **digest and store identity:** manifest determinism, the CHECK, the drift test;
  - **Kafka settings and their relations.**
- **Spark-marked:** a tiny job on a `write_snapshot` snapshot (tests/conftest.py) through
  `Worker` with SQLite and `MemoryQueue`.
- **Live** (gated by `ETF_RISK_MYSQL_URL` and `ETF_RISK_KAFKA_BOOTSTRAP`):
  - the acceptance cases above;
  - a standby that receives the next message only after the primary exceeds a short
    `max.poll.interval.ms`;
  - store-operation durations recorded (informational).
- **Mutation script:** three new mutations — a reconnect inside a transaction, disconnects treated
  as conflicts, and `ping(reconnect=True)` in place of the factory.

**Guarantee.**
- Acceptance still goes only through the token guard, now also binding the digest.
- Self-fence, watchdog and lock only stop or delay work.
- The sweep and `cleanup` never touch valid or accepted attempts.

**Deferred.** A unique index on accepted attempts. E1 measures whether the token guards alone
keep the guarantee, so this is decided after M3, in M6.

### M3 — Recovery experiments E1 and E2
Branch `feature/recovery-experiment` · Tooling Claude Code · Experiment: the project author,
tutored · after M2.

**Claude's tooling.**
- **Session harness.** One process starts the worker(s), the standby and the reconciler, performs
  injections, restarts crashed workers after the Part A delay, and logs everything (UTC, from the
  host clock).
- **Injections:**
  - crashes at `WORKER_FAULT_POINTS` (worker.py:54-59), carried out as a real SIGKILL and fired
    once per job (recorded in the events and `attempt.json`);
  - SIGKILL during a step;
  - SIGSTOP and SIGCONT of the worker alone or of the whole tree, always from the wait loop and
    never inside a transaction;
  - `docker compose restart` of Kafka or MySQL at a chosen phase;
  - holding a worker at `after_pipeline` while MySQL restarts.
- **Batch lifecycle:**
  - a fresh MySQL container, store id, topic and consumer group;
  - reference runs (direct CLI, same commit, under the host lock);
  - drain at the end;
  - `jobs export` and `memory.peak` before `down -v`. The collector reads files only.
- **Session helpers** `docs/recovery-session.zsh`, in the style of `docs/caching-session.zsh`:
  machine checks adapted to Docker running, with the memory threshold from M2's dry runs; two
  windows; `case n`; watcher; abort; note.
- **Collector** `analysis/collect_recovery_measurements.py --batch`:
  - imports `compare_tables` unchanged;
  - writes `measurements.csv` and `acceptance.json`, with criteria 1–5 plus "6 guarantee";
  - exits 1 on any failure.
- **Batches** live in `data/outputs-recovery/<batch>/`.

**The author's `docs/recovery-experiment.md`.** Claude scaffolds Parts A and B, History and the
`Author:` line.
- **Part A, decided by the author:**
  - the cases;
  - repetitions;
  - the job size: the recommendation is calendar-year for every case, with stride 21 only in M2;
  - lease, renewal, reconcile and restart-delay settings;
  - `--max-attempts`;
  - deadlines per case: lease + reconcile interval + publication grace + session timeout +
    restart delay + attempts left × attempt limit;
  - memory thresholds: suggested peak + 0.5 GiB free; with the host lock, at most one tree runs;
  - metric definitions;
  - predictions;
  - acceptance criteria;
  - stop rules.
- **Draft cases:**
  - a crash at each worker fault point, and during step 2;
  - a worker-only stall and a whole-tree stall;
  - Kafka restart while idle, during a submit, and during a run;
  - MySQL restart during a run, shorter and longer than M (the self-fence margin);
  - MySQL restart while held at `after_pipeline`: one execution predicted if MySQL is back before
    F, two otherwise.
- **Metrics per job:**
  - injection time;
  - detection: the expired attempt's `ended_at`, or the requeue or redelivery event;
  - recovery: the next `claimed_at`;
  - completion: `finished_at`;
  - executions;
  - **number** of accepted attempts;
  - correctness: checks, plus content against the reference, plus digest;
  - category: succeeded, failed (attempts exhausted), lost (not terminal by the deadline), or
    submit outcome unknown.
- **E1 cross-check.** The author's own SQL for accepted attempts per job must agree with
  `invariant_violations()`.

**Acceptance.**
- One batch meets every Part A criterion.
- Across all batches: zero lost jobs, zero jobs with two accepted results, and exactly one
  correct, digest-bound accepted result per succeeded job.
- Peaks are recorded per batch.
- Commits follow the precedent: tooling → Part A (before any measured run, author-approved) →
  dry batches → the formal session (the author) → Part B → status.

**Tests:** harness, collector and helper tests in the pattern of `test_caching_collector.py` and
`test_caching_session.py`, including planted problems, each failing its criterion.

**Guarantee:** measured under failures; no new write path.

### M4 — Redis cache for summary queries, with fallback
Branch `feature/result-cache` · Infrastructure Claude Code · Cache logic: the project author,
tutored · after M2.

**Identity**, the contract the author's key must meet (the tests pin it):
- **Run identity is the run digest** (M2.1), never the run id or path. Job and run ids repeat
  after a database is recreated, and paths can be reused.
- **The key** covers:
  - the cache format version;
  - the engine (PySpark version);
  - the run digest;
  - the query name;
  - the query definition hash (SHA-256 of its SQL text);
  - the canonical full parameters: every parameter including defaults, in canonical JSON with
    sorted keys and normalized types.

  The key is a hash of that tuple behind a readable prefix. The stored value repeats the tuple,
  and a mismatch on read counts as a miss.
- **Pinned by tests:**
  - equal run ids with different digests never share a key;
  - a changed parameter or SQL text changes the key;
  - equal requests give equal keys across processes.

**Accepted-run policy** (`runs.py` resolver, Claude). A run is servable only if one of the
following holds; anything else is refused, with no fallback to unaccepted runs.
- **(a) A job run.** In the job table, under its `store_id`, the job is succeeded and its accepted
  attempt's recorded `result_digest` equals the folder's manifest digest.
- **(b) A historical run.** The reviewed registry `docs/accepted-runs.json` (committed) lists it
  with path, digest, the basis for acceptance (`run.json` status ok, all checks 0, `verify.json`
  clean, the spec §8 reference) and the author's approval date. The folder's digest must match.
  - `python -m etf_risk.runs register` computes and checks the entry. The digest is stored in the
    registry, so the historical folder is never written to.
  - This lets M4 and E3 use the run of record without creating job rows outside
    `accept_result`.
  - **Pause, an authorship decision:** which run to register. `run-20261013T043848Z-4` has a clean
    `verify.json`. The documented `-2` has none, and registering it would mean running verify into
    it first. The four runs' tables are identical (plots.py:15-16).

**Per-query check.** Each query compares file sizes and modification times against the manifest
and fully re-hashes on any mismatch. `serve` re-hashes at startup, and `--verify-full` re-hashes
on demand. E3 reports the resolver's cost separately.

**Claude's part.**
- **Compose `redis`:**
  - pinned by digest;
  - `--maxmemory 32mb --maxmemory-policy allkeys-lru`, persistence off;
  - 128m `mem_limit` and `memswap_limit`;
  - port `127.0.0.1:6380`;
  - a `PING` healthcheck.
- **The `cache` group.**
- **`src/etf_risk/summary.py`:**
  - named queries over `paired/`. The author moves their own SQL from `analysis/sql_*.py`; those
    scripts are not edited (documents cite them by hash), and moving the SQL is an authorship
    step;
  - a one-shot CLI (new process) and a warm mode (one SparkSession, JSON-lines requests on stdin
    and stdout);
  - the resolver and the registry tool;
  - contract tests and fakes: a Redis stand-in that can go "down", and a live fixture gated by
    `ETF_RISK_REDIS_URL`;
  - a Spark-marked test that the queries on the registered run reproduce spec §8 (windows 529,
    466, 311, 174, 310), skipped without `data/`.

**The author's part.** `src/etf_risk/cache.py`, scaffolded:
- the key and normalization, under the identity contract;
- serialization;
- cache-aside get-or-compute;
- the fallback policy: connect and read timeouts, a short circuit breaker, no write-back while
  Redis is down, decode errors treated as misses;
- counters.

**Acceptance.**
- Contract tests pass offline and live.
- With Redis stopped, every query returns the Spark result, within the timeout and breaker bound.
- Unaccepted, unregistered or changed runs are refused.
- Redis peak ≤ 128 MiB.
- The runbook's E3 commands work as written.

**Tests:** the identity tests above; resolver refusals (a non-accepted attempt; a digest mismatch;
an unregistered historical run); fallback; equal results; live Redis; the spec §8 test.

**Guarantee:** reads accepted runs only, verified by digest; never writes the job table.

### M5 — E3: new Spark process vs warm Spark session vs Redis
Branch `feature/result-cache-experiment` · Tooling Claude Code · Experiment: the project author,
tutored · after M4.

**Configurations** (Part A):
- N: a new process per query;
- W: a warm session, with no cache;
- R: a warm session plus Redis, at hit rates set by repeats (e.g. 0, 50 and 90%);
- F: Redis stopped, then recovered.

**Key space.** Queries × accepted runs (the registered run of record and M2/M3 job runs) × any
parameters the author adds.

**Measures:**
- client-side monotonic latency per query;
- the resolver's cost, separately;
- realized vs designed hit rate;
- the warm session's process-tree peak (marker sampler);
- Redis `memory.peak` and `used_memory_peak`.

**Deliverables:** `docs/result-cache-experiment.md`, `docs/result-cache-session.zsh`,
`analysis/collect_result_cache_measurements.py`, and a batch in
`data/outputs-result-cache/<batch>/`.

**Acceptance:** one batch meets every Part A criterion; drift is reported.

**Tests:** collector (planted problems), session helpers, and the hit rate the workload generator
produces.

**Guarantee:** read-only for the job table.

### M6 — Architecture, report and demo
Branch `docs/extension-report` · Claude Code drafts; the author approves the conclusions · after M3
and M5.

- **`docs/architecture.md`** (new). It covers:
  - batch pipeline plus extension;
  - native vs Compose placement;
  - failure model, guarantee and where it is enforced and checked;
  - time and deadline rules (M2.4–M2.5);
  - cache identity and the accepted-run policy;
  - budget ledger;
  - runbook.
- **Spec §5's diagram:** gains `jobs/` and Compose, and its node ids are renamed.
- **Figures X5 (E1/E2) and X6 (E3)**, added together as X1–X4 were:
  - `plots.py` (`FIGURES`, `DOCUMENTED`, the tuple in `compare_documented`);
  - `test_plots.py` (12 → 14);
  - CSV copies and their README rows;
  - every "twelve figures" and "X1–X4" mention.
- **Spec:** §8 "What the recovery experiments showed" and "What the result-cache experiment
  showed"; §9 and §11 marked implemented, with the final ledger.
- **`results.md`:** a new extension section. §7 changes only with the author's re-approval.
- **README:** status and the full runbook.
- **`demo.md`:** submit; kill the worker mid-run; watch `status --check` recover; cache miss →
  hit → Redis stopped → fallback → restart.
- **The deferred unique-index decision.**

**Acceptance:**
- numbers traced to committed CSVs and records;
- `plots --check` passes;
- every command run as written in a fresh worktree;
- links valid;
- the author approves the conclusions.

**Tests:** `test_plots.py`; a link check; the full offline suite.

**Guarantee:** documentation only.

## Separate workstreams (outside M1–M6)

No milestone branch touches these files, and no milestone waits on them.

- **W1 Data verification** (`feature/data-verification`, own plan):
  - the second-source comparison (Stooq's automated download was blocked on 2026-10-12);
  - terms of use;
  - the cause of the Adj Close steps;
  - the 36 unverified days;
  - data-sources.md's missing AI header.
- **W2 Privacy-hook fixes** (`fix/transcript-privacy`): the uncommitted hook, test and transcript
  edits, plus spec §10's hook items. Claude touches the hook only when asked.
- **W3 AI-log review.**
  - **Scope:** the 68 untracked folders (including the sessions behind PRs #7–#9) and each
    milestone's logs.
  - **Reviewer:** the author.
  - **Where commits go:** following the precedent, each review lands as a separate "Add reviewed
    AI logs for …" commit, last on the milestone branch (ed71796). Logs reviewed after a merge go
    on a `docs/ai-logs-<date>` branch.
  - **Never mixed with code.**
  - **Also in scope:** `docs/ai-usage/README.md`'s attribution of the hook to Codex only, and the
    redaction of other projects' names that appeared in this planning session's tool output.

## Verification (end to end)

- **Per milestone:**
  - the offline suite (`uv run --group measure --group plots pytest`) with counts;
  - Spark-marked tests;
  - live suites on fresh containers (`--group jobs`, `--group cache`);
  - `status --check` empty after every live run;
  - the mutation script;
  - the lock diff;
  - measured peaks against the ledger.
- **System, after M6:** in a fresh worktree on `main`, follow the runbook from
  `uv sync --frozen` through smoke runs of E1/E2 and E3. Check that:
  - every accepted run passes its checks, matches its reference by content, and matches its
    recorded digest;
  - no overlapping Spark trees appear in the event logs;
  - `plots --check` passes;
  - peaks are within the ledger.

## Known pause points

- **Before M2 starts:** report the two timing corrections (absolute deadlines; no database-time
  bound in the safety argument).
- **M2:** any change to the M2.4 values that breaks or restates M ≥ t_w + G + ε; any store change beyond
  `job_store` and `result_digest`.
- **M3:** Part A approval (cases, job size, thresholds, deadlines); the author runs the formal
  session.
- **M4:** the author writes `cache.py` and moves their SQL into `summary.py`; the choice of which
  historical run to register.
- **M5:** Part A approval; the formal session.
- **M6:** the conclusions' wording; the unique-index decision.

```

## 186. Assistant — 2026-10-23T12:24:10.400Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/milestone-working-mode.md",
  "content": "[REDACTED:memory]"
}
```

## 187. User — 2026-10-23T12:24:11.593Z

### Tool result

```
[REDACTED:memory]
```

## 188. Assistant — 2026-10-23T12:24:15.845Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/extension-plan.md",
  "content": "[REDACTED:memory]"
}
```

## 189. User — 2026-10-23T12:24:16.975Z

### Tool result

```
[REDACTED:memory]
```

## 190. Assistant — 2026-10-23T12:24:19.442Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Add the new memories to the index and fix two stale lines"
}
```

## 191. User — 2026-10-23T12:24:20.614Z

### Tool result

```
[REDACTED:memory]
```

## 192. Assistant — 2026-10-23T12:24:22.326Z

Memory is updated. Now I'm checking whether the prerequisite has been merged on GitHub.

## 193. Assistant — 2026-10-23T12:24:24.131Z

### Tool call: Bash

```
{
  "command": "git fetch origin --prune 2>&1 | tail -5; echo \"--- origin/main:\"; git log -3 --format='%h %ad %s' --date=iso origin/main; echo \"---\"; if git merge-base --is-ancestor 97c35f3 origin/main; then echo \"PREREQ MERGED: 97c35f3 is in origin/main\"; else echo \"PREREQ NOT MERGED: 97c35f3 is not in origin/main\"; fi",
  "description": "Fetch from GitHub and check whether the fix branch is merged"
}
```

## 194. User — 2026-10-23T12:24:25.129Z

### Tool result

```
From https://github.com/[REDACTED:git-user]/leveraged-etf-risk-analytics
   f058095..7b1e758  main       -> origin/main
--- origin/main:
7b1e758 2026-10-23 04:42:19 -0500 Merge pull request #10 from [REDACTED:git-user]/fix/measure-process-kinds
97c35f3 2026-10-23 04:36:16 -0500 Count a Java process as the Spark JVM only when it runs Spark
f058095 2026-10-23 04:09:41 -0500 Merge branch 'docs/project-status'
---
PREREQ MERGED: 97c35f3 is in origin/main
```

## 195. Assistant — 2026-10-23T12:25:35.507Z

### Tool call: Bash

```
{
  "command": "git fetch origin main:main 2>&1 | tail -2; git log -1 --format='local main: %h %s' main && git worktree add .claude/worktrees/extension-baseline -b feature/extension-baseline main 2>&1 | tail -2 && ln -s ~/leveraged-etf-risk-analytics/data .claude/worktrees/extension-baseline/data && ls -la .claude/worktrees/extension-baseline/data | head -2 && git -C .claude/worktrees/extension-baseline status --short --branch | head -5",
  "description": "Update local main and create the M1 worktree with a data link"
}
```

## 196. User — 2026-10-23T12:25:37.370Z

### Tool result

```
From https://github.com/[REDACTED:git-user]/leveraged-etf-risk-analytics
   f058095..7b1e758  main       -> main
local main: 7b1e758 Merge pull request #10 from [REDACTED:git-user]/fix/measure-process-kinds
Preparing worktree (new branch 'feature/extension-baseline')
HEAD is now at 7b1e758 Merge pull request #10 from [REDACTED:git-user]/fix/measure-process-kinds
lrwxr-xr-x@ 1 [REDACTED:user]  staff  48 Oct 23 07:25 .claude/worktrees/extension-baseline/data -> ~/leveraged-etf-risk-analytics/data
## feature/extension-baseline
?? data
```

## 197. Assistant — 2026-10-23T12:25:42.839Z

### Tool call: Bash

```
{
  "command": "cd ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline && echo \"== --with:\"; grep -rn -- \"--with\" --include='*.py' --include='*.md' --include='*.yaml' --include='*.sh' --include='*.zsh' --include='*.toml' . | grep -v '^./docs/ai-usage/' ; echo \"== source_sha256 consumers:\"; grep -rn \"source_sha256\" --include='*.py' --include='*.md' --include='*.zsh' . | grep -v '^./docs/ai-usage/'; echo \"== gitignore data:\"; grep -n -E '^/?data' .gitignore",
  "description": "Find ad hoc dependency installs, source hash readers and the data ignore rule"
}
```

## 198. User — 2026-10-23T12:25:43.302Z

### Tool result

```
<persisted-output>
Output too large (378KB). Full output saved to: ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/tool-results/bh7xpiy8t.txt

Preview (first 2KB):
== --with:
ugrep: warning: --include=*.py: No such file or directory
ugrep: warning: --include=*.md: No such file or directory
ugrep: warning: --include=*.yaml: No such file or directory
ugrep: warning: --include=*.sh: No such file or directory
ugrep: warning: --include=*.zsh: No such file or directory
ugrep: warning: --include=*.toml: No such file or directory
docker/compose.yaml:13:#       uv run --with 'pymysql[rsa]==1.1.1' --with 'confluent-kafka==2.16.0' python -m pytest tests/test_jobs_*.py
tests/test_jobs_kafka.py:19:        uv run --with 'confluent-kafka==2.16.0' --with 'pymysql[rsa]==1.1.1' python -m pytest tests/test_jobs_*.py
tests/test_jobs_mysql.py:14:    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --with 'pymysql[rsa]==1.1.1' \\
docs/ai-usage/2026-10-12_1226_c6117488-08/transcript.jsonl:12:{"parentUuid": "83ff5d9e-f809-4373-a522-6b4527b51143", "isSidechain": false, "message": {"model": "claude-opus-5-5", "id": "msg_011CfxjcUTCXzjxc7YHqPSpX", "type": "message", "role": "assistant", "content": [{"type": "tool_use", "id": "toolu_01UrvFyYCbRXLmqQCxHRJwbv", "name": "Bash", "input": {"command": "SP=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/c6117488-0e99-49dd-a985-5cad552900a1/scratchpad && mkdir -p $SP/scripts $SP/full-history && cat > $SP/scripts/download_full_history.py <<'EOF'\n\"\"\"Scratch check: download full daily history (same settings as the 2020-2025 snapshot, but from the first available day).\"\"\"\nimport hashlib, json, platform, sys\nfrom datetime import datetime, timezone\nfrom pathlib import Path\nimport yfinance as yf\n\nout = Path(sys.argv[1])\nyf.set_tz_cache_location(str(out / \".tz-cache\"))\nreport = {\"downloaded_at_utc\": datetime.now(timezone.utc).isoformat(), \"python\": platform.python_version(),\n          \"yfinance\": yf.__version__, \"source\": \"Yahoo Finance via yfinance\", \"start\": \"1970-01-01\",\n          \"end_exclusive\": \"2026-01-01\", \"auto_adjust\": False, \"a
...
</persisted-output>
```

## 199. Assistant — 2026-10-23T12:25:48.051Z

The shell's `grep` is aliased to a different tool that ignored my filters and searched the AI logs too. I'll use `git grep` with the logs excluded.

## 200. Assistant — 2026-10-23T12:25:49.246Z

### Tool call: Bash

```
{
  "command": "echo \"== --with:\"; git grep -n -e '--with ' -- ':!docs/ai-usage'; echo \"== source_sha256 consumers:\"; git grep -n -e 'source_sha256' -- ':!docs/ai-usage'; echo \"== gitignore data:\"; git grep -n -E '^/?data' -- .gitignore",
  "description": "Search tracked files, excluding AI logs"
}
```

## 201. User — 2026-10-23T12:25:50.071Z

### Tool result

```
== --with:
docker/compose.yaml:13:#       uv run --with 'pymysql[rsa]==1.1.1' --with 'confluent-kafka==2.16.0' python -m pytest tests/test_jobs_*.py
src/etf_risk/jobs/kafka.py:15:dependency: the Kafka runs use uv run --with 'confluent-kafka==2.16.0'. Topics are created
tests/test_jobs_kafka.py:19:        uv run --with 'confluent-kafka==2.16.0' --with 'pymysql[rsa]==1.1.1' python -m pytest tests/test_jobs_*.py
tests/test_jobs_mysql.py:14:    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --with 'pymysql[rsa]==1.1.1' \\
== source_sha256 consumers:
README.md:271:(`code_source: "build"`) and the image ID from `docker/run.sh`; `source_sha256`
analysis/collect_measurements.py:86:    - code state (3.1): the protocol's and each run's source_sha256 and uv_lock_sha256 equal the
analysis/collect_measurements.py:96:    hashes = ("source_sha256", "uv_lock_sha256")
analysis/collect_partition_measurements.py:143:        hashes = (code.get("source_sha256"), code.get("uv_lock_sha256"))
docs/caching-experiment.md:180:  Every protocol JSON and `run.json` records the same `source_sha256` and `uv_lock_sha256`, with the
docs/caching-experiment.md:575:   `source_sha256` and `uv_lock_sha256`, with the hashed paths clean (3).
docs/caching-experiment.md:749:  the hashed paths clean, and the same `source_sha256` (12 files) and `uv_lock_sha256` (starting
docs/experiments.md:98:  `source_sha256` (10 source files) and `uv_lock_sha256`.
docs/experiments.md:231:- One code state for the whole experiment: identical `source_sha256` and `uv_lock_sha256`, and
docs/experiments.md:495:  clean and the same `source_sha256` and `uv_lock_sha256` as the four window configs, and each
docs/pandas-baseline.md:118:  protocol JSON and `run.json` records the same `source_sha256` and `uv_lock_sha256`, with the
docs/pandas-baseline.md:316:1. **Code state:** every protocol JSON and `run.json` of the batch records the same `source_sha256`
docs/pandas-baseline.md:442:  and the same `source_sha256` (12 files) and `uv_lock_sha256` (starting `99484c14ebf3`).
docs/partition-experiment.md:156:  `source_sha256` and `uv_lock_sha256`, with `git_worktree_clean: true` for the hashed paths
docs/partition-experiment.md:565:   `source_sha256` and `uv_lock_sha256`, with the hashed paths clean (3.1).
docs/partition-experiment.md:723:  clean, and the same `source_sha256` (11 files) and `uv_lock_sha256` (starting `99484c14ebf3`).
src/etf_risk/provenance.py:58:        # False means the code that ran is not exactly the recorded commit; source_sha256 identifies it.
src/etf_risk/provenance.py:62:        "source_sha256": {p.name: sha256_file(p) for p in sorted(PACKAGE_DIR.glob("*.py"))},
tests/test_measure.py:137:    assert "source_sha256" in result["code"] and any("different moments" in line for line in result["limits"])
tests/test_pandas_pipeline.py:217:    assert record["code"]["git_worktree_clean"] in (True, False) and "pandas_pipeline.py" in record["code"]["source_sha256"]
tests/test_partition_collector.py:129:    return {"source_sha256": {"spark_pipeline.py": source}, "uv_lock_sha256": lock, "git_commit": commit,
tests/test_provenance.py:34:    assert "provenance.py" in state["source_sha256"]                     # the code itself is still hashed
tests/test_spark_equivalence.py:203:    assert code["git_worktree_clean"] in (True, False) and {"spark_pipeline.py", "windows.py"} <= set(code["source_sha256"])
tests/test_windows.py:121:    assert {"git_commit", "git_worktree_clean", "source_sha256", "uv_lock_sha256"} <= set(config["code"])
tests/test_windows.py:122:    assert "windows.py" in config["code"]["source_sha256"]
== gitignore data:
.gitignore:223:/data/
```

## 202. Assistant — 2026-10-23T12:25:54.985Z

### Tool call: Bash

```
{
  "command": "sed -n '176,280p' README.md",
  "description": "Show the README's Running and Docker sections"
}
```

## 203. User — 2026-10-23T12:25:55.310Z

### Tool result

````
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

## Data

Daily prices come from Yahoo Finance through yfinance and are not committed
````

## 204. Assistant — 2026-10-23T12:26:00.411Z

### Tool call: Bash

```
{
  "command": "sed -n '225,268p' tests/test_jobs_queue.py; echo \"=== kafka test 150-175\"; sed -n '150,176p' tests/test_jobs_kafka.py",
  "description": "Show the crash-between-claim-and-commit tests"
}
```

## 205. User — 2026-10-23T12:26:00.869Z

### Tool result

```
                         ids=["5000-digits", "beyond-the-id-range", "zero", "text"])
def test_a_message_with_no_valid_job_id_is_committed_and_the_next_job_runs(env, payload):
    """A regression test: a 5,000-digit payload used to raise in int() outside serve()'s
    error handling, and an id beyond the range failed in the database, so the uncommitted
    message stopped the worker at every start."""
    env.queue.messages.append(payload)
    job = env.submit().job_id
    assert env.serve(env.worker("A")) == Served(handled=1, malformed=1)
    assert env.queue.committed["workers"] == 2
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    env.check(job)


# Whole scenarios

def test_a_lost_confirmation_leads_to_a_duplicate_that_is_refused(env):
    submitted = env.submit([PublishOutcome.UNCONFIRMED])          # written, but the confirmation was lost
    env.clock.advance(GRACE)
    assert env.reconciler().run_once() == Pass(published=1)       # published again: two messages
    assert env.serve(env.worker("A")) == Served(handled=2)
    assert [h.result for h in env.handled] == [Result.ACCEPTED, Result.SKIPPED]
    assert env.handled[1].reason is Refusal.SUCCEEDED and env.queue.committed["workers"] == 2
    env.check(submitted.job_id)


def test_a_crash_between_claim_and_commit(env):
    """A claims and dies before committing. The restarted consumer gets the message again and
    is refused while A's lease is live; once it expires, the reconciler requeues and
    publishes the job, and B runs attempt 2."""
    job = env.submit().job_id
    with pytest.raises(SimulatedCrash):
        env.serve(env.worker("A", fault=crash_at("after_claim")))
    assert "workers" not in env.queue.committed                   # nothing committed
    assert env.serve(env.worker("B")) == Served(handled=1)
    assert env.handled[-1].reason is Refusal.LEASE_HELD and env.queue.committed["workers"] == 1
    env.clock.advance(LEASE.total_seconds())
    assert env.reconciler().run_once() == Pass(requeued=1, published=1)
    assert env.serve(env.worker("B")) == Served(handled=1)
    j = env.admin.job(job)
    assert (j["status"], j["accepted_attempt"]) == (Status.SUCCEEDED, 2)
    env.check(job)


@pytest.mark.parametrize("seed", range(3))
=== kafka test 150-175
    assert env.handled[-1].reason is Refusal.SUCCEEDED
    for s in submitted:
        env.check(s.job_id)


@needs_kafka
def test_a_crash_between_claim_and_commit(env, topic):
    publisher, group = topic.publisher(), topic.group()
    job = submit_job(env.admin, publisher, PARAMS, {}).job_id
    crashing = topic.consumer(group)
    with pytest.raises(SimulatedCrash):
        serve(env, env.worker("A", fault=crash_after_claim), crashing, 1)
    crashing.close()                                                 # gone, with nothing committed
    worker, restarted = env.worker("B"), topic.consumer(group)
    assert serve(env, worker, restarted, 1) == Served(handled=1)     # the same message, refused while A's lease holds
    assert env.handled[-1].reason is Refusal.LEASE_HELD
    env.clock.advance(LEASE.total_seconds())
    assert Reconciler(env.new_store(), publisher).run_once() == Pass(requeued=1, published=1)
    assert serve(env, worker, restarted, 1) == Served(handled=1)
    j = env.admin.job(job)
    assert (j["status"], j["accepted_attempt"]) == (Status.SUCCEEDED, 2)
    env.check(job)


@needs_kafka
def test_an_oversized_payload_is_committed_and_the_next_job_runs(env, topic):
    """A regression test: a 5,000-digit payload ahead of a job used to stop the worker in
```

## 206. Assistant — 2026-10-23T12:26:09.658Z

### Tool call: Bash

```
{
  "command": "sed -n '1,60p' tests/jobs_backends.py; echo \"...\"; sed -n '150,250p' tests/jobs_backends.py",
  "description": "Show the shared job-test backends and environment"
}
```

## 207. User — 2026-10-23T12:26:10.143Z

### Tool result

```
"""Backends and helpers for the job-store tests: SQLite always, MySQL when ETF_RISK_MYSQL_URL is set.

A backend holds a fresh job table for one test. connect() opens a connection to it that may
be handed to another thread (one thread at a time); execute() runs one statement outside the
store, with ':name' parameters; dump() reads both tables as a new connection sees them;
violation() names the constraint an error reports. The MySQL backend creates a database of
its own and drops it afterwards; it needs PyMySQL and a server (see tests/test_jobs_mysql.py).
Without ETF_RISK_MYSQL_URL, BACKENDS holds SQLite only, so the default run neither runs nor
lists MySQL variants.

InThread and Paused run a store operation in a thread, Paused holding it at a fault point
inside its transaction, so that another connection can compete with an open transaction.
WorkerEnv adds workers and the guarantee check for one job. KafkaTopic gives a test a topic
of its own on the broker at ETF_RISK_KAFKA_BOOTSTRAP; without it, the Kafka tests skip.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import re
import secrets
import sqlite3
import threading
import time
from contextlib import closing
from datetime import timedelta
from pathlib import Path

import pytest

from etf_risk.jobs.queue import submit_job
from etf_risk.jobs.reconciler import Reconciler
from etf_risk.jobs.simulated import ManualClock, MemoryQueue, SimulatedPipeline, result_digest
from etf_risk.jobs.store import SQLITE, JobStore, Outcome, Status, open_sqlite
from etf_risk.jobs.worker import Handled, Result, Worker

MYSQL_URL = os.environ.get("ETF_RISK_MYSQL_URL")
BACKENDS = ["sqlite", "mysql"] if MYSQL_URL else ["sqlite"]
needs_mysql = pytest.mark.skipif(not MYSQL_URL, reason="set ETF_RISK_MYSQL_URL to run against MySQL")
KAFKA_BOOTSTRAP = os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP")
needs_kafka = pytest.mark.skipif(not KAFKA_BOOTSTRAP, reason="set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka")
LEASE = timedelta(seconds=60)
PARAMS = {"snapshot": "simulated", "stride": 21}
DUMP = ("SELECT * FROM jobs ORDER BY job_id", "SELECT * FROM job_attempts ORDER BY job_id, attempt_number")


class SQLiteBackend:
    name = "sqlite"
    dialect = SQLITE
    errors = (sqlite3.IntegrityError,)

    def __init__(self, tmp_path):
        self.path = tmp_path / "jobs.sqlite"
        open_sqlite(self.path, create=True).close()

    def connect(self):
        return open_sqlite(self.path, check_same_thread=False)

    def execute(self, sql, **params):
        with closing(self.connect()) as conn:
...
    """A fresh job table on one backend, a manual clock, and the connections and threads a test opened."""
    lease = LEASE

    def __init__(self, backend, tmp_path):
        self.backend, self.runs, self.clock = backend, tmp_path / "runs", ManualClock()
        self.connections, self.threads = [], []

    def new_store(self, *, fault=None, dialect=None, connection=None):
        connection = connection or self.backend.connect()
        self.connections.append(connection)
        return JobStore(connection, dialect or self.backend.dialect, clock=self.clock, lease=self.lease, fault=fault)

    def dump(self):
        return self.backend.dump()

    def close(self):
        for run in self.threads:
            if isinstance(run, Paused):
                run.released.set()
            if run.thread.ident is not None:
                run.thread.join(timeout=10)
        for connection in self.connections:
            connection.close()
        self.backend.close()


class StoreEnv(JobsEnv):
    def __init__(self, backend, tmp_path):
        super().__init__(backend, tmp_path)
        self.store = self.new_store()


class WorkerEnv(JobsEnv):
    """A job table, an admin store for submitting and inspecting, and workers with a connection each."""

    def __init__(self, backend, tmp_path):
        super().__init__(backend, tmp_path)
        self.admin = self.new_store()
        self.handled: list[Handled] = []
        self.acks: list[int] = []

    def worker(self, name, pipeline=None, fault=None, store_fault=None) -> Worker:
        return Worker(self.new_store(fault=store_fault), pipeline or SimulatedPipeline(), self.runs,
                      worker_id=f"worker-{name}", fault=fault)

    def deliver(self, worker: Worker, job_id: int) -> Handled:
        handled = worker.handle(job_id, lambda: self.acks.append(job_id))
        self.handled.append(handled)
        return handled

    def check(self, job_id: int, *, lost_acceptances: int = 0) -> None:
        """The guarantee for one job: no invariant violation; at most one accepted attempt,
        exactly one if the job succeeded, as many as the deliveries told "accepted" plus any
        acceptance whose worker died before it could tell; that attempt's result in its
        folder; no two attempts sharing a folder."""
        assert self.admin.invariant_violations() == {}
        job, attempts = self.admin.job(job_id), self.admin.attempts(job_id)
        accepted = [a for a in attempts if a["outcome"] is Outcome.ACCEPTED]
        told = [h for h in self.handled if h.job_id == job_id and h.result is Result.ACCEPTED]
        assert len(accepted) == len(told) + lost_acceptances == (1 if job["status"] is Status.SUCCEEDED else 0)
        for a in accepted:
            assert job["accepted_attempt"] == a["attempt_number"]
            assert json.loads((Path(a["output_dir"]) / "result.json").read_text()) == {
                "job_id": job_id, "attempt_number": a["attempt_number"], "run_id": a["run_id"],
                "result_sha256": result_digest(job["params"])}
        assert all(h.claim.attempt_number == job["accepted_attempt"] for h in told)
        assert len({a["output_dir"] for a in attempts}) == len(attempts)


def failing_at(point, times=None):
    """A store fault hook raising RuntimeError when it passes point: the first `times` times,
    or every time (None). fault.calls counts the passes."""
    def fault(at):
        if at == point:
            fault.calls += 1
            if times is None or fault.calls <= times:
                raise RuntimeError(f"injected at {point}")
    fault.calls = 0
    return fault


class QueueEnv(WorkerEnv):
    """WorkerEnv with an in-memory queue, and helpers to submit, reconcile and serve."""

    def __init__(self, backend, tmp_path):
        super().__init__(backend, tmp_path)
        self.queue = MemoryQueue()

    def submit(self, outcomes=(), **kwargs):
        """Submit a job (PARAMS) through submit_job(); outcomes decide its publication."""
        return submit_job(self.admin, self.queue.publisher(outcomes), PARAMS, {}, **kwargs)

    def reconciler(self, outcomes=(), **options) -> Reconciler:
        return Reconciler(self.new_store(), self.queue.publisher(outcomes), **options)

    def serve(self, worker, group="workers", **options):
        """worker serves a new consumer of the group (a restarted worker) until the queue is idle."""
        return worker.serve(self.queue.consumer(group), stop_when_idle=True, retry_delay=0,
                            on_handled=self.handled.append, **options)
```

## 208. Assistant — 2026-10-23T12:26:55.826Z

Next I'm reading the guards that the mutation script will break on purpose, so each mutation's exact text can be pinned.

## 209. Assistant — 2026-10-23T12:26:56.530Z

### Tool call: Bash

```
{
  "command": "sed -n '420,525p' src/etf_risk/jobs/store.py",
  "description": "Show the store's fail, requeue, reads and exhaust code"
}
```

## 210. Assistant — 2026-10-23T12:26:57.817Z

### Tool call: Bash

```
{
  "command": "sed -n '1,58p' src/etf_risk/jobs/queue.py; echo \"=== reconciler\"; sed -n '25,91p' src/etf_risk/jobs/reconciler.py; echo \"=== kafka cfg\"; sed -n '1,66p' src/etf_risk/jobs/kafka.py",
  "description": "Show the queue, reconciler and Kafka settings code"
}
```

## 211. User — 2026-10-23T12:26:59.041Z

### Tool result

```
                    "UPDATE jobs SET status = :status, attempt_token = NULL, lease_expires_at = NULL,"
                    " error = :job_error, finished_at = :finished_at, version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
                    job_id=claim.job_id, token=claim.token, status=status.value,
                    job_error=None if requeue else error, finished_at=None if requeue else now,
                    now=now).rowcount:
                return None
            self._fault("fail_attempt.jobs_updated")
            self._write_one("UPDATE job_attempts SET outcome = 'failed', error = :error, ended_at = :now"
                            " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                            job_id=claim.job_id, attempt_number=claim.attempt_number, error=error, now=now)
            return status

    @_retry_conflicts
    def requeue_expired(self, job_id: int, token: str) -> Status | None:
        """For the reconciler: end the attempt whose lease expired, conditional on the token
        read before (expired_leases()). The job returns to queued, with no publication
        recorded, while attempts are left, and fails otherwise; its attempt becomes expired.
        Returns the job's new status, or None when the job changed since the read (renewed
        and finished, taken over, or failed)."""
        now = self.clock.now()
        now_value = self._time(now)
        with self._transaction():
            if self._execute(
                    "UPDATE jobs SET status = 'queued', attempt_token = NULL, lease_expires_at = NULL,"
                    " version = version + 1, updated_at = :now"
                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token"
                    " AND lease_expires_at <= :now AND attempt_number < max_attempts",
                    job_id=job_id, token=token, now=now_value).rowcount:
                self._fault("requeue_expired.jobs_updated")
                self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                                " WHERE job_id = :job_id AND attempt_token = :token AND outcome = 'running'",
                                job_id=job_id, token=token, now=now_value)
                return Status.QUEUED
            attempt = self._fetch_one("SELECT attempt_number FROM job_attempts"
                                      " WHERE job_id = :job_id AND attempt_token = :token", job_id=job_id, token=token)
            if attempt is not None and self._exhaust(job_id, token, attempt["attempt_number"], now):
                return Status.FAILED
            return None

    def expired_leases(self) -> list[ExpiredLease]:
        """Running jobs whose lease has expired by the store's clock, with their tokens."""
        return [ExpiredLease(row["job_id"], row["attempt_token"]) for row in self._fetch_all(
            "SELECT job_id, attempt_token FROM jobs WHERE status = 'running' AND lease_expires_at <= :now"
            " ORDER BY job_id", now=self._time(self.clock.now()))]

    def unconfirmed(self) -> list[Unconfirmed]:
        """Queued jobs with no confirmed publication."""
        return [Unconfirmed(row["job_id"], row["version"], row["attempt_number"],
                            self.dialect.parse_time(row["updated_at"])) for row in self._fetch_all(
            "SELECT job_id, version, attempt_number, updated_at FROM jobs"
            " WHERE status = 'queued' AND published_at IS NULL ORDER BY job_id")]

    def job(self, job_id: int) -> dict | None:
        row = self._fetch_one("SELECT * FROM jobs WHERE job_id = :job_id", job_id=job_id)
        return None if row is None else self._decode(row)

    def attempts(self, job_id: int) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all(
            "SELECT * FROM job_attempts WHERE job_id = :job_id ORDER BY attempt_number", job_id=job_id)]

    def invariant_violations(self) -> dict[str, list[int]]:
        """The jobs breaking each invariant in INVARIANT_QUERIES, read in one transaction;
        empty when all hold. The tests run it after every scenario; the recovery experiments
        (E1) can run it on MySQL."""
        with self._transaction():
            found = {name: [row[0] for row in self._execute(sql).fetchall()]
                     for name, sql in INVARIANT_QUERIES.items()}
        return {name: job_ids for name, job_ids in found.items() if job_ids}

    def _refusal(self, job_id: int, now: datetime) -> Refusal:
        """Why both of claim's guards failed, read inside claim's transaction."""
        job = self._fetch_one("SELECT status, attempt_number, max_attempts, attempt_token, lease_expires_at"
                              " FROM jobs WHERE job_id = :job_id", job_id=job_id)
        if job is None:
            return Refusal.NOT_FOUND
        status = Status(job["status"])
        if status in TERMINAL:
            return Refusal.SUCCEEDED if status is Status.SUCCEEDED else Refusal.FAILED
        if status is Status.RUNNING and self.dialect.parse_time(job["lease_expires_at"]) > now:
            return Refusal.LEASE_HELD
        if (status is Status.RUNNING and job["attempt_number"] >= job["max_attempts"]
                and self._exhaust(job_id, job["attempt_token"], job["attempt_number"], now)):
            return Refusal.EXHAUSTED
        raise ClaimRace(f"job {job_id} changed while it was being claimed")

    def _exhaust(self, job_id: int, token: str, attempt_number: int, now: datetime) -> bool:
        """running -> failed: the lease expired and no attempts are left. Conditional on the
        token read before (by claim, or by the reconciler), so a change in between makes it
        match nothing."""
        now_value = self._time(now)
        if not self._execute(
                "UPDATE jobs SET status = 'failed', attempt_token = NULL, lease_expires_at = NULL,"
                " error = :error, finished_at = :now, version = version + 1, updated_at = :now"
                " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token"
                " AND lease_expires_at <= :now AND attempt_number >= max_attempts",
                job_id=job_id, token=token, now=now_value,
                error=f"attempts exhausted: the lease of the last attempt ({attempt_number}) expired").rowcount:
            return False
        self._fault("exhaust.jobs_updated")
        self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
                        " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
                        job_id=job_id, attempt_number=attempt_number, now=now_value)
        return True

    @contextmanager
```

## 212. User — 2026-10-23T12:26:59.046Z

### Tool result

```
"""Delivery of job ids: what the submitter, the worker and the reconciler need from a queue.

A Publisher sends a job id and waits for the broker's confirmation. A Consumer delivers
job ids at least once and moves its group's position only when told to: commit() records
that the group is done with a message, and a consumer that restarts resumes after the last
commit. A consumer that keeps running does not see an uncommitted message again by itself;
rewind() sends it back to that message. etf_risk.jobs.kafka implements both with Kafka,
and simulated.MemoryQueue implements them in memory for the offline tests.

submit_job() inserts the job (queued, version 0), publishes its id, and on confirmation
records published_at, conditional on version 0. A publication that is not confirmed may
still have been written; the reconciler publishes the job again after its grace period,
and claim() refuses the duplicate delivery.

A message carries one job id in decimal, exactly as encode() writes it: an integer from 1 to
MAX_JOB_ID, at most 19 digits, with no sign, spaces or leading zeros. Delivery.job_id()
checks the format and the length before converting anything, and the range after; a
message that fails returns None. The worker counts such a message as malformed, commits it
and skips it, so no payload can stop it or reach the database.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_queue.py
and tests/test_jobs_kafka.py.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Protocol

from etf_risk.jobs.store import DEFAULT_MAX_ATTEMPTS, JobStore

CONFIRMATION_TIMEOUT = timedelta(seconds=10)   # how long a publisher waits for the broker's confirmation
# The largest job id both job tables hold: SQLite's INTEGER is signed 64-bit; MySQL's BIGINT
# UNSIGNED holds more, but the store runs on both.
MAX_JOB_ID = 2**63 - 1
MAX_JOB_ID_DIGITS = len(str(MAX_JOB_ID))       # 19
_JOB_ID = re.compile(rb"[1-9][0-9]{0,%d}" % (MAX_JOB_ID_DIGITS - 1))


def encode(job_id: int) -> bytes:
    """A job id as a message carries it: its decimal digits."""
    if not 1 <= job_id <= MAX_JOB_ID:
        raise ValueError(f"job id {job_id} is outside the supported range 1..{MAX_JOB_ID}")
    return str(job_id).encode("ascii")


@dataclass(frozen=True)
class Delivery:
    """One delivered message: its value and where it sits (Kafka: topic, partition and
    offset; MemoryQueue: the offset)."""
    value: bytes
    position: Any

    def job_id(self) -> int | None:
        """The job id the message carries, or None if it carries no valid one (see the module
        docstring). The format and the length are checked first, so int() never sees a long
        payload: it refuses more than 4,300 digits with ValueError."""
=== reconciler
from dataclasses import dataclass
from datetime import timedelta

from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, Publisher
from etf_risk.jobs.store import JobStore, Status

PUBLICATION_GRACE = timedelta(seconds=30)     # a never-claimed job's wait before it is published again
RECONCILE_INTERVAL = timedelta(seconds=5)     # between passes

log = logging.getLogger(__name__)


@dataclass
class Pass:
    """What one pass did."""
    requeued: int = 0       # expired leases returned to queued
    failed: int = 0         # expired leases with no attempts left
    published: int = 0      # publications confirmed and recorded
    unconfirmed: int = 0    # publications not confirmed; the next pass tries again
    waiting: int = 0        # never-claimed jobs still within the grace period
    stale: int = 0          # jobs that changed between the read and the change: left alone


class Reconciler:
    def __init__(self, store: JobStore, publisher: Publisher, *,
                 publication_grace: timedelta = PUBLICATION_GRACE,
                 confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT):
        if publication_grace <= confirmation_timeout:
            raise ValueError(f"the publication grace ({publication_grace}) must exceed the confirmation timeout"
                             f" ({confirmation_timeout}), or the reconciler races a submitter still waiting")
        self.store = store
        self.publisher = publisher
        self.publication_grace = publication_grace

    def run_once(self) -> Pass:
        done = Pass()
        for lease in self.store.expired_leases():
            status = self.store.requeue_expired(lease.job_id, lease.token)
            if status is Status.QUEUED:
                done.requeued += 1
            elif status is Status.FAILED:
                done.failed += 1
            else:
                done.stale += 1
        now = self.store.clock.now()
        for job in self.store.unconfirmed():
            if job.attempt_number == 0 and now - job.queued_since < self.publication_grace:
                done.waiting += 1
            elif not self.publisher.publish(job.job_id):
                done.unconfirmed += 1
            elif self.store.mark_published(job.job_id, job.version):
                done.published += 1
            else:
                done.stale += 1
        return done

    def run(self, stop: threading.Event, *, interval: timedelta = RECONCILE_INTERVAL) -> None:
        """Pass after pass until stop is set. A pass that raises is logged, and the next one
        starts after the interval."""
        while not stop.is_set():
            try:
                done = self.run_once()
            except Exception:
                log.exception("reconciler pass failed")
            else:
                log.info("reconciler pass: %s", done)
            stop.wait(interval.total_seconds())
=== kafka cfg
"""Kafka adapters for the job queue (spec §11): a publisher that waits for the broker's
confirmation, and a consumer whose group moves on only when the worker commits.

Settings, each pinned by tests/test_jobs_kafka.py:
- producer: acks=all and idempotence on. With one broker and no replica, acks=all means
  that broker wrote the message. librdkafka gives up on a message after the confirmation
  timeout, the same time publish() waits, so publish() returns a final answer.
- consumer: enable.auto.commit=false, since the worker commits after its claim, and
  enable.auto.offset.store=false, so nothing but those commits records a position.
  auto.offset.reset=earliest: a consumer group that has never committed starts at the
  first message, so a job published before its group first starts is still delivered;
  librdkafka's default, latest, would skip it.

confluent-kafka is imported only when an adapter is created. It is not a declared
dependency: the Kafka runs use uv run --with 'confluent-kafka==2.16.0'. Topics are created
explicitly (create_topic: one partition, no replica), since the broker in
docker/compose.yaml does not create them on first use.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_kafka.py,
offline and against Kafka 4.3.1 (docker/compose.yaml).
"""
from __future__ import annotations

import logging
from datetime import timedelta

from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, Delivery, encode

log = logging.getLogger(__name__)


def producer_config(bootstrap: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT) -> dict:
    return {"bootstrap.servers": bootstrap, "acks": "all", "enable.idempotence": True, "linger.ms": 0,
            "message.timeout.ms": int(confirmation_timeout.total_seconds() * 1000)}


def consumer_config(bootstrap: str, group: str) -> dict:
    return {"bootstrap.servers": bootstrap, "group.id": group, "enable.auto.commit": False,
            "enable.auto.offset.store": False, "auto.offset.reset": "earliest"}


class KafkaPublisher:
    def __init__(self, bootstrap: str, topic: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT):
        from confluent_kafka import Producer
        self.topic = topic
        self._wait = confirmation_timeout.total_seconds() + 1.0   # the report comes by the message timeout
        self._producer = Producer({**producer_config(bootstrap, confirmation_timeout=confirmation_timeout),
                                   "logger": log})

    def publish(self, job_id: int) -> bool:
        """Send the job id and wait for the broker's confirmation. True only if it arrived;
        False may still mean the message was written and its confirmation lost."""
        from confluent_kafka import KafkaException
        report: dict = {}
        try:
            self._producer.produce(self.topic, key=encode(job_id), value=encode(job_id),
                                   on_delivery=lambda error, message: report.setdefault("error", error))
        except (BufferError, KafkaException):
            log.warning("could not send job %s", job_id, exc_info=True)
            return False
        self._producer.flush(self._wait)
        if report.get("error") is not None:
            log.warning("job %s: publication not confirmed: %s", job_id, report["error"])
        return "error" in report and report["error"] is None

    def close(self) -> None:
```

## 213. Assistant — 2026-10-23T12:27:03.469Z

### Tool call: Bash

```
{
  "command": "sed -n '52,63p' src/etf_risk/jobs/queue.py; echo \"=== store _transaction/_retry\"; sed -n '264,279p' src/etf_risk/jobs/store.py; sed -n '296,320p' src/etf_risk/jobs/store.py; echo \"=== sqlite dialect is_conflict & mysql\"; sed -n '192,216p' src/etf_risk/jobs/store.py",
  "description": "Show the remaining guard code for the mutation list"
}
```

## 214. User — 2026-10-23T12:27:04.033Z

### Tool result

```
    value: bytes
    position: Any

    def job_id(self) -> int | None:
        """The job id the message carries, or None if it carries no valid one (see the module
        docstring). The format and the length are checked first, so int() never sees a long
        payload: it refuses more than 4,300 digits with ValueError."""
        if _JOB_ID.fullmatch(self.value) is None:
            return None
        job_id = int(self.value)
        return job_id if job_id <= MAX_JOB_ID else None

=== store _transaction/_retry
    queued_since: datetime


def _retry_conflicts(operation: Callable[..., Any]) -> Callable[..., Any]:
    """Runs a write operation again when the database rolled it back over a lock conflict."""
    @functools.wraps(operation)
    def run(self: JobStore, *args: Any, **kwargs: Any) -> Any:
        for run_number in range(1, CONFLICT_RETRIES + 1):
            try:
                return operation(self, *args, **kwargs)
            except Exception as error:
                if run_number == CONFLICT_RETRIES or not self.dialect.is_conflict(error):
                    raise
    return run


        """Create a queued job, at version 0, and return its id. Publishing it is a separate
        step: etf_risk.jobs.queue.submit_job() publishes and records the confirmation."""
        now = self._time(self.clock.now())
        with self._transaction():
            return self._execute(
                "INSERT INTO jobs (params, input_checksums, status, max_attempts, attempt_number, version,"
                " created_at, updated_at)"
                " VALUES (:params, :input_checksums, 'queued', :max_attempts, 0, 0, :now, :now)",
                params=_json(params), input_checksums=_json(input_checksums), max_attempts=max_attempts,
                now=now).lastrowid

    @_retry_conflicts
    def mark_published(self, job_id: int, version: int) -> bool:
        """Record that Kafka confirmed a publication of the job, if the job is still as it was
        when its version was read before publishing: queued, with no publication recorded.
        Otherwise the message may already have been consumed (the job was claimed, and
        perhaps returned to queued), so nothing is recorded and the reconciler publishes the
        job again if it is queued. True: recorded."""
        now = self._time(self.clock.now())
        with self._transaction():
            return self._execute(
                "UPDATE jobs SET published_at = :now, version = version + 1, updated_at = :now"
                " WHERE job_id = :job_id AND status = 'queued' AND published_at IS NULL AND version = :version",
                job_id=job_id, version=version, now=now).rowcount == 1

=== sqlite dialect is_conflict & mysql
class SQLiteDialect:
    """sqlite3 takes ':name' parameters as written. BEGIN IMMEDIATE takes the database's
    write lock when the transaction starts, waiting for it up to the connection's busy
    timeout, so a transaction that started meets no lock conflict and nothing is run again.
    Times are fixed-width UTC text, so comparing the text compares the times."""
    name = "sqlite"
    begin = "BEGIN IMMEDIATE"

    @staticmethod
    def sql(text: str) -> str:
        return text

    @staticmethod
    def time(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")

    @staticmethod
    def parse_time(value: str) -> datetime:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=timezone.utc)

    @staticmethod
    def is_conflict(error: BaseException) -> bool:
        return False
```

## 215. Assistant — 2026-10-23T12:27:52.946Z

I have everything needed for the mutation list. Next comes the dependency change: adding the `jobs` group and locking it, then checking that the lock only gains packages.

## 216. Assistant — 2026-10-23T12:27:54.765Z

### Tool call: Bash

```
{
  "command": "sed -n '218,236p' .gitignore; echo \"---\"; cp uv.lock /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/uv.lock.before && echo \"saved lock copy\"",
  "description": "Show the ignore rules near data and save the current lock"
}
```

## 217. User — 2026-10-23T12:27:56.607Z

### Tool result

```
# Streamlit
.streamlit/secrets.toml

# Project data and run outputs (the Yahoo data's terms of use are not reviewed; see docs/data-sources.md)
/data/
# Spark local-mode artifacts
spark-warehouse/
metastore_db/
derby.log
# macOS
.DS_Store
# Unredacted Claude Code transcripts and local privacy settings stay on this machine
docs/ai-usage/**/transcript.raw.jsonl
.claude/*.local.*
# Git worktrees that Claude Code sessions create inside the repository
.claude/worktrees/
---
saved lock copy
```

## 218. Assistant — 2026-10-23T12:27:59.706Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.gitignore",
  "old_string": "# Project data and run outputs (the Yahoo data's terms of use are not reviewed; see docs/data-sources.md)\n/data/",
  "new_string": "# Project data and run outputs (the Yahoo data's terms of use are not reviewed; see docs/data-sources.md).\n# No trailing slash, so a worktree's `data` symlink to the main checkout's data/ is ignored too.\n/data"
}
```

## 219. Assistant — 2026-10-23T12:28:01.437Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/pyproject.toml",
  "old_string": "download = [\n    \"yfinance==1.7.0\",\n]",
  "new_string": "download = [\n    \"yfinance==1.7.0\",\n]\njobs = [\n    \"confluent-kafka==2.16.0\",  # exact: the job queue's Kafka settings and live tests depend on it\n    \"pymysql[rsa]==1.1.1\",      # exact: the job table's MySQL adapter and live tests depend on it\n]"
}
```

## 220. User — 2026-10-23T12:28:02.493Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.gitignore has been updated successfully.
```

## 221. User — 2026-10-23T12:28:03.626Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/pyproject.toml has been updated successfully.
```

## 222. Assistant — 2026-10-23T12:28:07.483Z

### Tool call: Bash

```
{
  "command": "uv lock 2>&1 | tail -8; echo \"--- status:\"; git status --short; echo \"--- package changes (name + version lines) in the lock diff:\"; diff <(grep -A1 '^name = ' /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/uv.lock.before | grep -E '^(name|version) = ' | paste - -) <(grep -A1 '^name = ' uv.lock | grep -E '^(name|version) = ' | paste - -)",
  "description": "Lock the new group and list the package-level changes"
}
```

## 223. User — 2026-10-23T12:28:10.700Z

### Tool result

```
Using CPython 3.12.14 interpreter at: /opt/anaconda3/bin/python3
Resolved 50 packages in 1.63s
Added confluent-kafka v2.16.0
Added cryptography v50.0.2
Added pymysql v1.1.1
--- status:
 M .gitignore
 M pyproject.toml
 M uv.lock
--- package changes (name + version lines) in the lock diff:
5a6
> name = "confluent-kafka"	version = "2.16.0"
6a8
> name = "cryptography"	version = "50.0.2"
33a36
> name = "pymysql"	version = "1.1.1"
```

## 224. Assistant — 2026-10-23T12:28:19.382Z

### Tool call: Bash

```
{
  "command": "uv lock --check 2>&1 | tail -2; echo \"--- lock diff, excluding wheel/sdist hash lines:\"; git diff uv.lock | grep -E '^[+-]' | grep -v -E '^[+-](wheels|sdist|    \\{ url)' | head -60",
  "description": "Check the lock is current and review its structural diff"
}
```

## 225. User — 2026-10-23T12:28:20.621Z

### Tool result

```
Using CPython 3.12.14 interpreter at: /opt/anaconda3/bin/python3
Resolved 50 packages in 30ms
--- lock diff, excluding wheel/sdist hash lines:
--- a/uv.lock
+++ b/uv.lock
+[[package]]
+name = "confluent-kafka"
+version = "2.16.0"
+source = { registry = "https://pypi.org/simple" }
+]
+
+[[package]]
+name = "cryptography"
+version = "50.0.2"
+source = { registry = "https://pypi.org/simple" }
+dependencies = [
+    { name = "cffi", marker = "platform_python_implementation != 'PyPy'" },
+]
+]
+
+jobs = [
+    { name = "confluent-kafka" },
+    { name = "pymysql", extra = ["rsa"] },
+]
+jobs = [
+    { name = "confluent-kafka", specifier = "==2.16.0" },
+    { name = "pymysql", extras = ["rsa"], specifier = "==1.1.1" },
+]
+[[package]]
+name = "pymysql"
+version = "1.1.1"
+source = { registry = "https://pypi.org/simple" }
+]
+
+[package.optional-dependencies]
+rsa = [
+    { name = "cryptography" },
+]
+
```

## 226. Assistant — 2026-10-23T12:28:23.299Z

The lock is consistent and the diff only adds those three packages and the `jobs` group entries. Next I'm creating this worktree's environment with every group the test suites need.

## 227. Assistant — 2026-10-23T12:28:24.813Z

### Tool call: Bash

```
{
  "command": "uv sync --frozen --group measure --group plots --group jobs 2>&1 | tail -4; .venv/bin/python -c \"import pymysql, confluent_kafka, psutil, matplotlib, pyspark; print('pymysql', pymysql.__version__, '| confluent-kafka', confluent_kafka.version()[0], '| pyspark', pyspark.__version__)\"",
  "description": "Create the worktree's environment with all test groups",
  "timeout": 600000
}
```

## 228. User — 2026-10-23T12:29:03.538Z

### Tool result

```
 + pytz==2026.5
 + six==1.17.0
 + toolz==1.2.0
 + tzdata==2026.5
pymysql 1.4.6 | confluent-kafka 2 | pyspark 4.2.0
```

## 229. Assistant — 2026-10-23T12:29:09.278Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -c \"from importlib.metadata import version as v; print({p: v(p) for p in ('pymysql','confluent-kafka','cryptography','pyspark','pandas','numpy','pyarrow','psutil')})\"",
  "description": "Show installed package versions from metadata"
}
```

## 230. User — 2026-10-23T12:29:09.912Z

### Tool result

```
{'pymysql': '1.1.1', 'confluent-kafka': '2.16.0', 'cryptography': '50.0.2', 'pyspark': '4.2.0', 'pandas': '2.3.3', 'numpy': '2.5.4', 'pyarrow': '26.0.0', 'psutil': '7.2.2'}
```

## 231. Assistant — 2026-10-23T12:29:15.382Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py",
  "old_string": "A git commit alone does not identify the code when the worktree has changes, so\ncode_state() also records whether the worktree is clean and the SHA-256 of every\nmodule in src/etf_risk/ and of uv.lock.",
  "new_string": "A git commit alone does not identify the code when the worktree has changes, so\ncode_state() also records whether the worktree is clean and the SHA-256 of uv.lock and\nof every Python module and SQL schema under src/etf_risk/, subpackages included (the\njob queue in jobs/ and its schema files). Keys are paths relative to src/etf_risk/, so a\ntop-level module keeps the key it always had (\"model.py\") and jobs/__init__.py does not\ncollide with __init__.py. Records written before 2026-10-23 hash the top-level modules\nonly."
}
```

## 232. Assistant — 2026-10-23T12:29:17.285Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py",
  "old_string": "PACKAGE_DIR = Path(__file__).resolve().parent\nREPO_ROOT = PACKAGE_DIR.parents[1]",
  "new_string": "PACKAGE_DIR = Path(__file__).resolve().parent\nREPO_ROOT = PACKAGE_DIR.parents[1]\nSOURCE_SUFFIXES = (\".py\", \".sql\")"
}
```

## 233. Assistant — 2026-10-23T12:29:19.331Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py",
  "old_string": "def code_state() -> dict:",
  "new_string": "def source_files() -> dict[str, Path]:\n    \"\"\"Every Python module and SQL schema of the package, by path relative to it.\"\"\"\n    files = (p for p in PACKAGE_DIR.rglob(\"*\") if p.suffix in SOURCE_SUFFIXES and p.is_file())\n    return {p.relative_to(PACKAGE_DIR).as_posix(): p for p in sorted(files)}\n\n\ndef code_state() -> dict:"
}
```

## 234. Assistant — 2026-10-23T12:29:20.784Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py",
  "old_string": "        \"source_sha256\": {p.name: sha256_file(p) for p in sorted(PACKAGE_DIR.glob(\"*.py\"))},",
  "new_string": "        \"source_sha256\": {key: sha256_file(path) for key, path in source_files().items()},"
}
```

## 235. User — 2026-10-23T12:29:21.876Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py has been updated successfully.
```

## 236. User — 2026-10-23T12:29:22.968Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py has been updated successfully.
```

## 237. User — 2026-10-23T12:29:24.100Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py has been updated successfully.
```

## 238. User — 2026-10-23T12:29:25.201Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/provenance.py has been updated successfully.
```

## 239. Assistant — 2026-10-23T12:29:33.208Z

Now the provenance tests. The new one walks the package independently of `source_files()`, so it isn't just restating the implementation:

## 240. Assistant — 2026-10-23T12:29:35.498Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_provenance.py",
  "old_string": "\"\"\"code_state(): git when available, the Docker image's build record otherwise.\n\nAI contribution: written with Claude Code (Opus 5.5).\n\"\"\"\nimport pytest\n\nfrom etf_risk import provenance",
  "new_string": "\"\"\"code_state(): git when available, the Docker image's build record otherwise; the source\nhashes cover every module and schema file of the package, subpackages included.\n\nAI contribution: written with Claude Code (Opus 5.5).\n\"\"\"\nimport os\nfrom pathlib import Path\n\nimport pytest\n\nfrom etf_risk import provenance\nfrom etf_risk.ingest import sha256_file"
}
```

## 241. Assistant — 2026-10-23T12:29:40.005Z

### Tool call: Bash

```
{
  "command": "cat >> tests/test_provenance.py <<'EOF'\n\n\ndef test_every_module_and_schema_is_hashed_under_its_path_in_the_package(monkeypatch, no_build_record):\n    \"\"\"jobs/ and its schema files included. Keys are relative to src/etf_risk/, so the two\n    __init__.py files do not collide. The package is walked here independently of\n    provenance.source_files().\"\"\"\n    monkeypatch.setattr(provenance, \"_git\", lambda *args: None)\n    hashed = provenance.code_state()[\"source_sha256\"]\n    on_disk = {}\n    for folder, _, names in os.walk(provenance.PACKAGE_DIR):\n        for name in names:\n            if name.endswith((\".py\", \".sql\")):\n                path = Path(folder) / name\n                on_disk[path.relative_to(provenance.PACKAGE_DIR).as_posix()] = sha256_file(path)\n    assert hashed == on_disk\n    assert {\"__init__.py\", \"jobs/__init__.py\", \"jobs/store.py\", \"jobs/schema/mysql.sql\",\n            \"jobs/schema/sqlite.sql\"} <= set(hashed)\n\n\ndef test_top_level_modules_keep_the_keys_of_earlier_records(monkeypatch, no_build_record):\n    \"\"\"Records before 2026-10-23 hashed src/etf_risk/*.py by file name; those entries are unchanged.\"\"\"\n    monkeypatch.setattr(provenance, \"_git\", lambda *args: None)\n    hashed = provenance.code_state()[\"source_sha256\"]\n    earlier = {p.name: sha256_file(p) for p in sorted(provenance.PACKAGE_DIR.glob(\"*.py\"))}\n    assert {name: hashed[name] for name in earlier} == earlier\nEOF\n.venv/bin/python -m pytest tests/test_provenance.py -q 2>&1 | tail -3",
  "description": "Add the provenance tests and run them"
}
```

## 242. User — 2026-10-23T12:29:41.404Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_provenance.py has been updated successfully.
```

## 243. User — 2026-10-23T12:30:05.111Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
5 passed, 1 warning in 0.04s
```

## 244. Assistant — 2026-10-23T12:30:09.498Z

That notice was my own append. The provenance tests pass (5 passed). Next I'm replacing every `--with` install with `--group jobs`. Here are the four places:

## 245. Assistant — 2026-10-23T12:30:11.152Z

### Tool call: Bash

```
{
  "command": "sed -n '8,16p' docker/compose.yaml; echo \"=== kafka.py 13-17\"; sed -n '13,17p' src/etf_risk/jobs/kafka.py; echo \"=== test_jobs_kafka 1-25\"; sed -n '1,25p' tests/test_jobs_kafka.py; echo \"=== test_jobs_mysql 1-22\"; sed -n '1,22p' tests/test_jobs_mysql.py",
  "description": "Show the docstrings that install the clients ad hoc"
}
```

## 246. User — 2026-10-23T12:30:11.691Z

### Tool result

```
#   containers on this Compose network will use kafka:9092. Topics are not created on
#   first use: create them with etf_risk.jobs.kafka.create_topic().
#
#   docker compose -f docker/compose.yaml up -d --wait mysql kafka
#   ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
#       uv run --with 'pymysql[rsa]==1.1.1' --with 'confluent-kafka==2.16.0' python -m pytest tests/test_jobs_*.py
#   docker compose -f docker/compose.yaml down -v        # removes the data volumes as well
#
# The tests create and drop a database and a topic of their own for each test. The root
=== kafka.py 13-17

confluent-kafka is imported only when an adapter is created. It is not a declared
dependency: the Kafka runs use uv run --with 'confluent-kafka==2.16.0'. Topics are created
explicitly (create_topic: one partition, no replica), since the broker in
docker/compose.yaml does not create them on first use.
=== test_jobs_kafka 1-25
"""The Kafka adapters, offline and against a broker.

Offline, always: the producer's and the consumer's settings (acks=all, idempotence, the
message timeout equal to the confirmation timeout; no auto-commit, earliest).
Against Kafka (skipped unless ETF_RISK_KAFKA_BOOTSTRAP is set), each test on a topic of
its own (KafkaTopic, tests/jobs_backends.py):
- jobs published before a fresh consumer group starts are all delivered, and with latest,
  librdkafka's default, the same group would get none of them;
- publish() returns True once the broker confirmed, and False for an unreachable broker;
- an uncommitted message reaches the group's next consumer, a committed one does not;
- a rewind delivers the same message again;
- end to end, submit_job(), Worker.serve() and the reconciler, with the job table on SQLite
  and, with ETF_RISK_MYSQL_URL set, on MySQL; an oversized payload ahead of a job is
  committed and skipped; after a persistent error before the acknowledgement, serve()
  gives up with the message uncommitted, for a restarted worker.

    docker compose -f docker/compose.yaml up -d --wait kafka mysql
    ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 \\
        uv run --with 'confluent-kafka==2.16.0' --with 'pymysql[rsa]==1.1.1' python -m pytest tests/test_jobs_*.py
    docker compose -f docker/compose.yaml down -v

AI contribution: written with Claude Code (Opus 5.5).
"""
import time
from datetime import timedelta
=== test_jobs_mysql 1-22
"""The MySQL adapter offline, and the MySQL behaviour the job store relies on, against a server.

Offline, always: the dialect's parameters and times for every statement the store sends, the
schema split into statements, connection options from a URL, and the conflict check.
Against MySQL (skipped unless ETF_RISK_MYSQL_URL is set): an UPDATE reads the latest committed
row whatever the transaction's snapshot; affected rows without CLIENT_FOUND_ROWS; SET clauses
evaluated left to right; competing claims under READ COMMITTED; lock wait timeouts run again.
With the URL set, tests/test_jobs_store.py and tests/test_jobs_worker.py run on MySQL as well,
including connections competing for one job.

To run everything on a local server (docker/compose.yaml):

    docker compose -f docker/compose.yaml up -d --wait mysql
    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --with 'pymysql[rsa]==1.1.1' \\
        pytest tests/test_jobs_store.py tests/test_jobs_worker.py tests/test_jobs_mysql.py
    docker compose -f docker/compose.yaml down -v

AI contribution: written with Claude Code (Opus 5.5).
"""
import re
from contextlib import closing
from datetime import datetime, timedelta, timezone
```

## 247. Assistant — 2026-10-23T12:30:14.552Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docker/compose.yaml",
  "old_string": "#       uv run --with 'pymysql[rsa]==1.1.1' --with 'confluent-kafka==2.16.0' python -m pytest tests/test_jobs_*.py",
  "new_string": "#       uv run --group jobs python -m pytest tests/test_jobs_*.py    # PyMySQL and confluent-kafka, as locked"
}
```

## 248. Assistant — 2026-10-23T12:30:16.568Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/jobs/kafka.py",
  "old_string": "confluent-kafka is imported only when an adapter is created. It is not a declared\ndependency: the Kafka runs use uv run --with 'confluent-kafka==2.16.0'. Topics are created",
  "new_string": "confluent-kafka is imported only when an adapter is created. It is in the `jobs`\ndependency group (pyproject.toml, locked in uv.lock), not among the core dependencies: the\nKafka runs use uv run --group jobs. Topics are created"
}
```

## 249. Assistant — 2026-10-23T12:30:18.150Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_kafka.py",
  "old_string": "        uv run --with 'confluent-kafka==2.16.0' --with 'pymysql[rsa]==1.1.1' python -m pytest tests/test_jobs_*.py",
  "new_string": "        uv run --group jobs python -m pytest tests/test_jobs_*.py"
}
```

## 250. Assistant — 2026-10-23T12:30:20.353Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_mysql.py",
  "old_string": "    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --with 'pymysql[rsa]==1.1.1' \\\\\n        pytest tests/test_jobs_store.py tests/test_jobs_worker.py tests/test_jobs_mysql.py",
  "new_string": "    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 uv run --group jobs \\\\\n        pytest tests/test_jobs_store.py tests/test_jobs_worker.py tests/test_jobs_mysql.py"
}
```

## 251. User — 2026-10-23T12:30:21.427Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docker/compose.yaml has been updated successfully.
```

## 252. User — 2026-10-23T12:30:22.499Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/jobs/kafka.py has been updated successfully.
```

## 253. User — 2026-10-23T12:30:23.615Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_kafka.py has been updated successfully.
```

## 254. User — 2026-10-23T12:30:24.688Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_mysql.py has been updated successfully.
```

## 255. Assistant — 2026-10-23T12:30:27.646Z

Now the test that follows `job-queue.md`'s job-9 timeline step by step. First, the imports and helpers the queue tests already use:

## 256. Assistant — 2026-10-23T12:30:28.208Z

### Tool call: Bash

```
{
  "command": "sed -n '1,60p' tests/test_jobs_queue.py",
  "description": "Show the queue tests' imports and helpers"
}
```

## 257. User — 2026-10-23T12:30:28.795Z

### Tool result

```
"""Delivery through a queue: the in-memory queue's Kafka semantics, submit_job(), and
Worker.serve() with commits, rewinds and malformed messages; then whole scenarios with the
reconciler, each ending with the guarantee check (WorkerEnv.check, tests/jobs_backends.py).

The queue is simulated.MemoryQueue, which models only what the job system relies on;
tests/test_jobs_kafka.py checks the same behaviour against a Kafka broker. The tests that
take `env` run on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL.

AI contribution: written with Claude Code (Opus 5.5).
"""
import inspect
import random
import time
from collections import Counter

import pytest

from etf_risk.jobs.queue import MAX_JOB_ID, MAX_JOB_ID_DIGITS, Delivery, encode, submit_job
from etf_risk.jobs.reconciler import PUBLICATION_GRACE, Pass
from etf_risk.jobs.simulated import MemoryQueue, PublishOutcome, SimulatedCrash, SimulatedPipeline
from etf_risk.jobs.store import TERMINAL, Refusal, Status
from etf_risk.jobs.worker import DELIVERY_RETRIES, WORKER_FAULT_POINTS, Result, Served, Worker
from jobs_backends import BACKENDS, LEASE, PARAMS, QueueEnv, failing_at, make_backend

GRACE = PUBLICATION_GRACE.total_seconds()


@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = QueueEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


def crash_at(point):
    assert point in WORKER_FAULT_POINTS

    def fault(at):
        if at == point:
            raise SimulatedCrash(point)
    return fault


# The in-memory queue

def test_a_new_group_starts_at_the_earliest_message():
    queue = MemoryQueue()
    publisher = queue.publisher()
    assert publisher.publish(1) and publisher.publish(2)        # before the group's first consumer
    consumer = queue.consumer("workers")
    assert [consumer.poll().job_id(), consumer.poll().job_id(), consumer.poll()] == [1, 2, None]


def test_only_a_commit_moves_the_group_on():
    queue = MemoryQueue()
    queue.publisher().publish(1)
    first = queue.consumer("workers")
    delivery = first.poll()
    assert first.poll() is None                                  # this consumer moved on, uncommitted
    assert queue.consumer("workers").poll() == delivery          # a restarted one gets the message again
```

## 258. Assistant — 2026-10-23T12:30:37.979Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_queue.py",
  "old_string": "    env.clock.advance(LEASE.total_seconds())\n    assert env.reconciler().run_once() == Pass(requeued=1, published=1)\n    assert env.serve(env.worker(\"B\")) == Served(handled=1)\n    j = env.admin.job(job)\n    assert (j[\"status\"], j[\"accepted_attempt\"]) == (Status.SUCCEEDED, 2)\n    env.check(job)\n\n\n@pytest.mark.parametrize(\"seed\", range(3))",
  "new_string": "    env.clock.advance(LEASE.total_seconds())\n    assert env.reconciler().run_once() == Pass(requeued=1, published=1)\n    assert env.serve(env.worker(\"B\")) == Served(handled=1)\n    j = env.admin.job(job)\n    assert (j[\"status\"], j[\"accepted_attempt\"]) == (Status.SUCCEEDED, 2)\n    env.check(job)\n\n\ndef test_the_job_9_timeline(env):\n    \"\"\"docs/job-queue.md, \"A job, two failures\", row by row: the submitter's confirmation is\n    lost, A claims and dies before committing, the reconciler leaves the running job alone,\n    the restarted worker is refused while A's lease holds, and once it expires the reconciler\n    requeues and publishes the job in one pass.\"\"\"\n    job = env.submit([PublishOutcome.UNCONFIRMED]).job_id                # 0 s: written, not confirmed\n    assert env.admin.job(job)[\"published_at\"] is None and env.queue.job_ids() == [job]\n    env.clock.advance(1)                                                 # 1 s: A claims and dies\n    with pytest.raises(SimulatedCrash):\n        env.serve(env.worker(\"A\", fault=crash_at(\"after_claim\")))\n    assert \"workers\" not in env.queue.committed\n    env.clock.advance(29)                                                # 30 s: running, so nothing to publish\n    assert env.reconciler().run_once() == Pass()\n    env.clock.advance(16)                                                # 46 s: A restarted gets the same message\n    restarted = env.worker(\"A\")\n    assert env.serve(restarted) == Served(handled=1)\n    assert env.handled[-1].reason is Refusal.LEASE_HELD and env.queue.committed[\"workers\"] == 1\n    env.clock.advance(15)                                                # 61 s: A's lease has expired\n    assert env.reconciler().run_once() == Pass(requeued=1, published=1)\n    assert env.queue.job_ids() == [job, job]\n    env.clock.advance(1)                                                 # 62 s: attempt 2 runs and is accepted\n    assert env.serve(restarted) == Served(handled=1)\n    j, attempts = env.admin.job(job), env.admin.attempts(job)\n    assert (j[\"status\"], j[\"accepted_attempt\"]) == (Status.SUCCEEDED, 2)\n    assert [a[\"outcome\"] for a in attempts] == [\"expired\", \"accepted\"]\n    env.check(job)\n\n\n@pytest.mark.parametrize(\"seed\", range(3))"
}
```

## 259. Assistant — 2026-10-23T12:30:38.716Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -m pytest tests/test_jobs_queue.py -q -k \"job_9 or crash_between\" 2>&1 | tail -3",
  "description": "Run the new timeline test and its neighbour"
}
```

## 260. User — 2026-10-23T12:30:40.294Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_queue.py has been updated successfully.
```

## 261. User — 2026-10-23T12:30:42.019Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 40 deselected, 1 warning in 0.24s
```

## 262. Assistant — 2026-10-23T12:31:44.846Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/services.py",
  "content": "\"\"\"The systems extension's Compose services as seen from this machine: readiness, memory\npeaks, and other projects' containers sharing Docker's VM (spec §11).\n\n    uv run --group jobs python -m etf_risk.services ready mysql kafka\n    uv run python -m etf_risk.services peaks mysql kafka\n    uv run python -m etf_risk.services others --require-none\n\n- ready waits until each service can do what the job system needs. MySQL: a login and\n  SELECT 1, since the Compose healthcheck (mysqladmin ping) answers before logins work.\n  Kafka: a metadata request that lists a broker. It exits 1 if a service is not ready\n  within --timeout. The URLs come from ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP,\n  defaulting to the ports in docker/compose.yaml.\n- peaks prints each service's cgroup v2 memory.peak, the highest usage since its container\n  started (page cache included), against memory.max, the Compose limit, as docker/run.sh\n  does for the pipeline container. A container that restarts may start a new count, so\n  read peaks before a restart is injected.\n- others counts the running containers that do not belong to this Compose project. It\n  prints the count only, never their names: they use the same VM's memory, so memory\n  budgets are measured with none running.\n\nAI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_services.py.\n\"\"\"\nfrom __future__ import annotations\n\nimport argparse\nimport json\nimport os\nimport subprocess\nimport sys\nimport time\nfrom collections.abc import Callable\nfrom dataclasses import asdict, dataclass\n\nfrom etf_risk.provenance import REPO_ROOT\n\nCOMPOSE_FILE = REPO_ROOT / \"docker\" / \"compose.yaml\"\nPROJECT = \"etf-risk-jobs\"                                   # the name: in docker/compose.yaml\nSERVICES = (\"mysql\", \"kafka\")\nDEFAULT_MYSQL_URL = \"mysql://root:jobs-test@127.0.0.1:3307\"   # compose.yaml's test password, 127.0.0.1 only\nDEFAULT_KAFKA_BOOTSTRAP = \"127.0.0.1:9094\"\n\n\ndef _docker(*args: str, timeout: float = 60) -> subprocess.CompletedProcess:\n    return subprocess.run([\"docker\", *args], capture_output=True, text=True, timeout=timeout)\n\n\n@dataclass(frozen=True)\nclass Peak:\n    service: str\n    peak_bytes: int | None     # None: no memory.peak to read (the service is not running, or an older kernel)\n    limit_bytes: int | None    # None: no limit (\"max\"), or unknown\n\n    @property\n    def fraction(self) -> float | None:\n        return None if self.peak_bytes is None or not self.limit_bytes else self.peak_bytes / self.limit_bytes\n\n    def describe(self) -> str:\n        if self.peak_bytes is None:\n            return f\"{self.service}: memory.peak not available\"\n        text = f\"{self.service}: memory.peak {self.peak_bytes / 2**20:,.0f} MiB\"\n        if self.limit_bytes:\n            text += f\" of {self.limit_bytes / 2**20:,.0f} MiB ({self.fraction:.0%})\"\n        return text + \" (cgroup, includes page cache)\"\n\n\ndef memory_peak(service: str) -> Peak:\n    \"\"\"The service container's memory.peak and memory.max (cgroup v2).\"\"\"\n    out = _docker(\"compose\", \"-f\", str(COMPOSE_FILE), \"exec\", \"-T\", service,\n                  \"cat\", \"/sys/fs/cgroup/memory.peak\", \"/sys/fs/cgroup/memory.max\")\n    values = out.stdout.split()\n    if out.returncode != 0 or len(values) != 2:\n        return Peak(service, None, None)\n    peak, limit = values\n    return Peak(service, int(peak), None if limit == \"max\" else int(limit))\n\n\ndef other_containers() -> int:\n    \"\"\"How many running containers belong to no service of this project: a count only.\"\"\"\n    out = _docker(\"ps\", \"--format\", '{{.Label \"com.docker.compose.project\"}}')\n    if out.returncode != 0:\n        raise RuntimeError(f\"docker ps failed with exit code {out.returncode}\")\n    return sum(1 for label in out.stdout.splitlines() if label.strip() != PROJECT)\n\n\ndef mysql_ready(url: str) -> None:\n    from etf_risk.jobs.mysql import connect_mysql\n    connection = connect_mysql(url)\n    try:\n        with connection.cursor() as cursor:\n            cursor.execute(\"SELECT 1\")\n            if cursor.fetchone() != (1,):\n                raise RuntimeError(\"SELECT 1 did not return 1\")\n    finally:\n        connection.close()\n\n\ndef kafka_ready(bootstrap: str) -> None:\n    from confluent_kafka.admin import AdminClient\n    metadata = AdminClient({\"bootstrap.servers\": bootstrap, \"log_level\": 0}).list_topics(timeout=5)\n    if not metadata.brokers:\n        raise RuntimeError(\"the metadata lists no broker\")\n\n\ndef wait_until_ready(service: str, check: Callable[[], None], *, timeout: float, interval: float = 1.0,\n                     clock: Callable[[], float] = time.monotonic,\n                     sleep: Callable[[float], None] = time.sleep) -> float:\n    \"\"\"Run check() until it returns; the seconds that took. TimeoutError, with the last\n    error, once timeout has passed.\"\"\"\n    start = clock()\n    while True:\n        try:\n            check()\n            return clock() - start\n        except Exception as error:\n            last = error\n        if clock() - start >= timeout:\n            raise TimeoutError(f\"{service} not ready after {timeout:g} s: {type(last).__name__}: {last}\")\n        sleep(interval)\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(prog=\"python -m etf_risk.services\", description=__doc__.splitlines()[0])\n    commands = parser.add_subparsers(dest=\"command\", required=True)\n    ready = commands.add_parser(\"ready\", help=\"wait until each service can be used\")\n    ready.add_argument(\"services\", nargs=\"+\", choices=SERVICES)\n    ready.add_argument(\"--timeout\", type=float, default=120.0, help=\"seconds per service (default 120)\")\n    peaks = commands.add_parser(\"peaks\", help=\"cgroup memory.peak against the limit\")\n    peaks.add_argument(\"services\", nargs=\"+\", choices=SERVICES)\n    peaks.add_argument(\"--json\", action=\"store_true\", help=\"one JSON object per line\")\n    others = commands.add_parser(\"others\", help=\"count containers outside this project\")\n    others.add_argument(\"--require-none\", action=\"store_true\", help=\"exit 1 if any is running\")\n    args = parser.parse_args(argv)\n\n    if args.command == \"ready\":\n        checks = {\"mysql\": lambda: mysql_ready(os.environ.get(\"ETF_RISK_MYSQL_URL\", DEFAULT_MYSQL_URL)),\n                  \"kafka\": lambda: kafka_ready(os.environ.get(\"ETF_RISK_KAFKA_BOOTSTRAP\", DEFAULT_KAFKA_BOOTSTRAP))}\n        for service in args.services:\n            try:\n                seconds = wait_until_ready(service, checks[service], timeout=args.timeout)\n            except TimeoutError as error:\n                print(error, file=sys.stderr)\n                return 1\n            print(f\"{service}: ready after {seconds:.1f} s\")\n        return 0\n    if args.command == \"peaks\":\n        for service in args.services:\n            peak = memory_peak(service)\n            print(json.dumps(asdict(peak)) if args.json else peak.describe())\n        return 0\n    count = other_containers()\n    print(f\"{count} running container(s) outside the {PROJECT} project\")\n    return 1 if args.require_none and count else 0\n\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n"
}
```

## 263. Assistant — 2026-10-23T12:31:57.048Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_services.py",
  "content": "\"\"\"etf_risk.services: memory peaks, the count of other projects' containers, and the\nreadiness wait, with a fake docker on PATH and a fake clock, so neither Docker nor a\nservice is needed.\n\nAI contribution: written with Claude Code (Opus 5.5).\n\"\"\"\nimport os\n\nimport pytest\n\nfrom etf_risk import services\n\nFAKE_DOCKER = r\"\"\"#!/bin/sh\n# Answers the calls etf_risk.services makes, from FAKE_* variables.\ncase \"$*\" in\n  *\"exec -T mysql cat\"*) printf '%s\\n%s\\n' \"$FAKE_PEAK\" \"$FAKE_LIMIT\" ;;\n  *\"exec -T kafka cat\"*) echo \"cat: /sys/fs/cgroup/memory.peak: No such file or directory\" >&2\n                         echo 671088640; exit 1 ;;\n  \"ps --format\"*) printf '%s' \"$FAKE_PS\" ;;\n  *) echo \"unexpected call: $*\" >&2; exit 2 ;;\nesac\n\"\"\"\n\n\n@pytest.fixture\ndef fake_docker(tmp_path, monkeypatch):\n    bin_dir = tmp_path / \"bin\"\n    bin_dir.mkdir()\n    docker = bin_dir / \"docker\"\n    docker.write_text(FAKE_DOCKER)\n    docker.chmod(0o755)\n    monkeypatch.setenv(\"PATH\", f\"{bin_dir}{os.pathsep}{os.environ['PATH']}\")\n    return monkeypatch\n\n\nclass FakeTime:\n    def __init__(self):\n        self.now = 0.0\n\n    def clock(self):\n        return self.now\n\n    def sleep(self, seconds):\n        self.now += seconds\n\n\ndef test_a_peak_is_read_with_its_limit(fake_docker, capsys):\n    fake_docker.setenv(\"FAKE_PEAK\", str(400 * 2**20))\n    fake_docker.setenv(\"FAKE_LIMIT\", str(512 * 2**20))\n    peak = services.memory_peak(\"mysql\")\n    assert (peak.peak_bytes, peak.limit_bytes, peak.fraction) == (400 * 2**20, 512 * 2**20, 400 / 512)\n    assert services.main([\"peaks\", \"mysql\"]) == 0\n    assert capsys.readouterr().out == \"mysql: memory.peak 400 MiB of 512 MiB (78%) (cgroup, includes page cache)\\n\"\n\n\ndef test_no_limit_and_a_missing_peak_are_reported_as_such(fake_docker, capsys):\n    fake_docker.setenv(\"FAKE_PEAK\", str(2**20))\n    fake_docker.setenv(\"FAKE_LIMIT\", \"max\")\n    assert services.memory_peak(\"mysql\") == services.Peak(\"mysql\", 2**20, None)\n    assert services.memory_peak(\"kafka\") == services.Peak(\"kafka\", None, None)\n    assert services.main([\"peaks\", \"kafka\", \"--json\"]) == 0\n    assert capsys.readouterr().out == '{\"service\": \"kafka\", \"peak_bytes\": null, \"limit_bytes\": null}\\n'\n\n\ndef test_other_projects_are_counted_but_never_named(fake_docker, capsys):\n    fake_docker.setenv(\"FAKE_PS\", \"etf-risk-jobs\\nsomeone-elses-project\\n\\netf-risk-jobs\\n\")\n    assert services.other_containers() == 2                  # a labelled one and one without a project\n    assert services.main([\"others\", \"--require-none\"]) == 1\n    out = capsys.readouterr()\n    assert out.out == \"2 running container(s) outside the etf-risk-jobs project\\n\"\n    assert \"someone-elses-project\" not in out.out + out.err\n\n\ndef test_none_outside_the_project(fake_docker):\n    fake_docker.setenv(\"FAKE_PS\", \"etf-risk-jobs\\netf-risk-jobs\\n\")\n    assert services.other_containers() == 0\n    assert services.main([\"others\", \"--require-none\"]) == 0\n\n\ndef test_ready_retries_until_the_check_passes():\n    fake, calls = FakeTime(), []\n\n    def check():\n        calls.append(fake.now)\n        if len(calls) < 3:\n            raise ConnectionRefusedError(\"refused\")\n\n    assert services.wait_until_ready(\"mysql\", check, timeout=60, clock=fake.clock, sleep=fake.sleep) == 2.0\n    assert calls == [0.0, 1.0, 2.0]\n\n\ndef test_ready_gives_up_after_the_timeout_with_the_last_error():\n    fake = FakeTime()\n\n    def check():\n        raise ConnectionRefusedError(f\"refused at {fake.now:g} s\")\n\n    with pytest.raises(TimeoutError, match=r\"kafka not ready after 5 s: ConnectionRefusedError: refused at 5 s\"):\n        services.wait_until_ready(\"kafka\", check, timeout=5, clock=fake.clock, sleep=fake.sleep)\n"
}
```

## 264. Assistant — 2026-10-23T12:31:57.632Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -m pytest tests/test_services.py -q 2>&1 | tail -3",
  "description": "Run the services helper tests"
}
```

## 265. User — 2026-10-23T12:31:59.185Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/src/etf_risk/services.py (file state is current in your context — no need to Read it back)
```

## 266. User — 2026-10-23T12:32:00.292Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_services.py (file state is current in your context — no need to Read it back)
```

## 267. User — 2026-10-23T12:32:03.711Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
6 passed, 1 warning in 1.43s
```

## 268. Assistant — 2026-10-23T12:32:06.781Z

The helper's tests pass (6 passed). Now the mutation script. To pin each mutation's exact source text, whitespace included, I'm printing the target lines verbatim:

## 269. Assistant — 2026-10-23T12:32:14.681Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python - <<'EOF'\nimport re\nfrom pathlib import Path\ntargets = {\n \"src/etf_risk/jobs/store.py\": [\n   \"updated_at = :now\\\"\\n                    \\\" WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token\\\",\\n                    job_id=claim.job_id, token=claim.token, lease_expires_at\",\n   \"WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token\\\",\\n                    job_id=claim.job_id, token=claim.token, attempt_number=claim.attempt_number,\",\n   \"WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token\\\",\\n                    job_id=claim.job_id, token=claim.token, status=status.value,\",\n   \"AND lease_expires_at <= :now\\\"\\n                    \\\" AND attempt_number < max_attempts\\\", **take).rowcount:\",\n   \"attempt_token = :token\\\"\\n                    \\\" AND lease_expires_at <= :now AND attempt_number < max_attempts\\\",\\n                    job_id=job_id, token=token, now=now_value).rowcount:\",\n   \"attempt_token = :token\\\"\\n                \\\" AND lease_expires_at <= :now AND attempt_number >= max_attempts\\\",\",\n   \"published_at = NULL,\\\"\\n                    \\\" version = version + 1, updated_at = :now\\\"\\n                    \\\" WHERE job_id = :job_id AND status = 'queued'\\\", **take)\",\n   \"AND published_at IS NULL AND version = :version\\\",\",\n   \"cursor.execute(\\\"ROLLBACK\\\")\",\n   \"if count != 1:\",\n   \"\\\" WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token\\\",\",\n ],\n \"src/etf_risk/jobs/worker.py\": [\"exist_ok=False\", \"        self._fault(\\\"after_claim\\\")\\n        acknowledge()\\n\", \"consumer.rewind(delivery)\", \"if failures > retries:\", \"                served.malformed += 1\\n                self._commit(consumer, delivery, served)\\n\"],\n \"src/etf_risk/jobs/queue.py\": [\"rb\\\"[1-9][0-9]{0,%d}\\\"\", \"if _JOB_ID.fullmatch(self.value) is None:\", \"return job_id if job_id <= MAX_JOB_ID else None\"],\n \"src/etf_risk/jobs/reconciler.py\": [\"now - job.queued_since < self.publication_grace\", \"if job.attempt_number == 0 and now\"],\n \"src/etf_risk/jobs/kafka.py\": [\"\\\"enable.auto.commit\\\": False\", \"\\\"auto.offset.reset\\\": \\\"earliest\\\"\", \"\\\"acks\\\": \\\"all\\\"\", \"\\\"enable.idempotence\\\": True\", \"\\\"enable.auto.offset.store\\\": False\"],\n \"src/etf_risk/jobs/mysql.py\": [\"error.args[0] in CONFLICT_ERRORS\"],\n}\nfor f, olds in targets.items():\n    text = Path(f).read_text()\n    for o in olds:\n        print(f\"{text.count(o)}  {f}: {o[:70]!r}\")\nEOF",
  "description": "Check each mutation target occurs exactly once"
}
```

## 270. User — 2026-10-23T12:32:15.337Z

### Tool result

```
1  src/etf_risk/jobs/store.py: 'updated_at = :now"\n                    " WHERE job_id = :job_id AND st'
1  src/etf_risk/jobs/store.py: "WHERE job_id = :job_id AND status = 'running' AND attempt_token = :tok"
1  src/etf_risk/jobs/store.py: "WHERE job_id = :job_id AND status = 'running' AND attempt_token = :tok"
1  src/etf_risk/jobs/store.py: 'AND lease_expires_at <= :now"\n                    " AND attempt_number'
1  src/etf_risk/jobs/store.py: 'attempt_token = :token"\n                    " AND lease_expires_at <= '
1  src/etf_risk/jobs/store.py: 'attempt_token = :token"\n                " AND lease_expires_at <= :now'
1  src/etf_risk/jobs/store.py: 'published_at = NULL,"\n                    " version = version + 1, upd'
1  src/etf_risk/jobs/store.py: 'AND published_at IS NULL AND version = :version",'
1  src/etf_risk/jobs/store.py: 'cursor.execute("ROLLBACK")'
1  src/etf_risk/jobs/store.py: 'if count != 1:'
1  src/etf_risk/jobs/store.py: '" WHERE j.job_id = :job_id AND j.status = \'succeeded\' AND a.attempt_to'
1  src/etf_risk/jobs/worker.py: 'exist_ok=False'
1  src/etf_risk/jobs/worker.py: '        self._fault("after_claim")\n        acknowledge()\n'
1  src/etf_risk/jobs/worker.py: 'consumer.rewind(delivery)'
1  src/etf_risk/jobs/worker.py: 'if failures > retries:'
1  src/etf_risk/jobs/worker.py: '                served.malformed += 1\n                self._commit(con'
1  src/etf_risk/jobs/queue.py: 'rb"[1-9][0-9]{0,%d}"'
1  src/etf_risk/jobs/queue.py: 'if _JOB_ID.fullmatch(self.value) is None:'
1  src/etf_risk/jobs/queue.py: 'return job_id if job_id <= MAX_JOB_ID else None'
1  src/etf_risk/jobs/reconciler.py: 'now - job.queued_since < self.publication_grace'
1  src/etf_risk/jobs/reconciler.py: 'if job.attempt_number == 0 and now'
1  src/etf_risk/jobs/kafka.py: '"enable.auto.commit": False'
1  src/etf_risk/jobs/kafka.py: '"auto.offset.reset": "earliest"'
1  src/etf_risk/jobs/kafka.py: '"acks": "all"'
1  src/etf_risk/jobs/kafka.py: '"enable.idempotence": True'
1  src/etf_risk/jobs/kafka.py: '"enable.auto.offset.store": False'
1  src/etf_risk/jobs/mysql.py: 'error.args[0] in CONFLICT_ERRORS'
```

## 271. Assistant — 2026-10-23T12:34:12.225Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/mutation_check.py",
  "content": "\"\"\"Mutation checks of the job queue's guards and settings: break one on purpose, run the job\ntests, and expect them to fail (docs/job-table.md, docs/job-queue.md).\n\n    uv run --group jobs python tests/mutation_check.py --out <folder>       # SQLite and offline Kafka settings\n    ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \\\\\n        uv run --group jobs python tests/mutation_check.py --out <folder>   # also MySQL and Kafka\n    uv run --group jobs python tests/mutation_check.py --list\n    uv run --group jobs python tests/mutation_check.py --only renew-token rewind\n\nEach mutation replaces one exact piece of source text, which must occur exactly once. The\nwork happens in a scratch copy of the repository (src/, tests/, pyproject.toml, uv.lock) with\nits own environment (uv sync --frozen --group jobs), never in this checkout. The job tests\nfirst run unmutated and must pass. Then, for each mutation, they run in a fresh process\ngroup with a timeout:\n- caught: pytest reports failing tests (exit 1);\n- survived: they all pass (exit 0);\n- error: any other exit, such as a collection error, or the timeout. A broken guard must\n  fail a test, not hang one.\n\nA mutation that needs a server is skipped unless its variable is set. The run exits 1 unless\nevery mutation that ran was caught. --out writes mutations.json, with this checkout's code\nstate, and the output tail of every run.\n\nThis list was rebuilt on 2026-10-23 from the descriptions of the earlier checks\n(docs/job-table.md, docs/job-queue.md, the message of commit e2806bd). Those runs left no list\nof their own, so it is not claimed to be the same set. Mutations that the remaining guards\nmake equivalent are left out; for example, mark_published's published_at condition is covered\nby its version guard.\n\nAI contribution: written with Claude Code (Opus 5.5).\n\"\"\"\nfrom __future__ import annotations\n\nimport argparse\nimport json\nimport os\nimport shutil\nimport signal\nimport subprocess\nimport sys\nimport tempfile\nimport time\nfrom dataclasses import asdict, dataclass\nfrom datetime import datetime, timezone\nfrom pathlib import Path\n\nREPO = Path(__file__).resolve().parents[1]\nsys.path.insert(0, str(REPO / \"src\"))\nfrom etf_risk.provenance import code_state  # noqa: E402\n\nCOPIED = (\"src\", \"tests\", \"pyproject.toml\", \"uv.lock\")\nJOB_TESTS = (\"tests/test_jobs_store.py\", \"tests/test_jobs_worker.py\", \"tests/test_jobs_queue.py\",\n             \"tests/test_jobs_reconciler.py\", \"tests/test_jobs_kafka.py\", \"tests/test_jobs_mysql.py\")\nNEEDS = {\"mysql\": \"ETF_RISK_MYSQL_URL\", \"kafka\": \"ETF_RISK_KAFKA_BOOTSTRAP\"}\nSTORE, WORKER, QUEUE = \"src/etf_risk/jobs/store.py\", \"src/etf_risk/jobs/worker.py\", \"src/etf_risk/jobs/queue.py\"\nRECONCILER, KAFKA, MYSQL = \"src/etf_risk/jobs/reconciler.py\", \"src/etf_risk/jobs/kafka.py\", \"src/etf_risk/jobs/mysql.py\"\n\n\n@dataclass(frozen=True)\nclass Mutation:\n    id: str\n    file: str\n    old: str\n    new: str\n    breaks: str\n    needs: tuple[str, ...] = ()\n\n\ndef removing(id: str, file: str, context: str, piece: str, breaks: str, needs: tuple[str, ...] = ()) -> Mutation:\n    \"\"\"Remove piece from context; context is what must occur exactly once in the file.\"\"\"\n    assert context.count(piece) == 1, (id, piece)\n    return Mutation(id, file, context, context.replace(piece, \"\", 1), breaks, needs)\n\n\n_RENEW = (\"updated_at = :now\\\"\\n                    \\\" WHERE job_id = :job_id AND status = 'running'\"\n          \" AND attempt_token = :token\\\",\\n                    job_id=claim.job_id, token=claim.token, lease_expires_at\")\n_ACCEPT = (\"'running' AND attempt_token = :token\\\",\\n                    job_id=claim.job_id, token=claim.token,\"\n           \" attempt_number=claim.attempt_number,\")\n_FAIL = (\"'running' AND attempt_token = :token\\\",\\n                    job_id=claim.job_id, token=claim.token,\"\n         \" status=status.value,\")\n_TAKEOVER = (\"status = 'running' AND lease_expires_at <= :now\\\"\\n                    \\\" AND attempt_number <\"\n             \" max_attempts\\\", **take).rowcount:\")\n_REQUEUE = (\"'running' AND attempt_token = :token\\\"\\n                    \\\" AND lease_expires_at <= :now AND\"\n            \" attempt_number < max_attempts\\\",\\n                    job_id=job_id, token=token, now=now_value).rowcount:\")\n_EXHAUST = (\"'running' AND attempt_token = :token\\\"\\n                \\\" AND lease_expires_at <= :now AND\"\n            \" attempt_number >= max_attempts\\\",\")\n_CLAIM = (\"published_at = NULL,\\\"\\n                    \\\" version = version + 1, updated_at = :now\\\"\\n\"\n          \"                    \\\" WHERE job_id = :job_id AND status = 'queued'\\\", **take)\")\n\nMUTATIONS = (\n    # The store's guards (docs/job-table.md).\n    removing(\"renew-token\", STORE, _RENEW, \" AND attempt_token = :token\", \"renewal without the token: a fenced worker renews\"),\n    removing(\"accept-token\", STORE, _ACCEPT, \" AND attempt_token = :token\", \"acceptance without the token\"),\n    removing(\"fail-token\", STORE, _FAIL, \" AND attempt_token = :token\", \"fail_attempt without the token\"),\n    removing(\"takeover-lease\", STORE, _TAKEOVER, \" AND lease_expires_at <= :now\", \"a claim takes over a live lease\"),\n    Mutation(\"takeover-attempts-left\", STORE, '\" AND attempt_number < max_attempts\", **take).rowcount:',\n             '\"\", **take).rowcount:', \"a claim takes over with no attempts left\"),\n    removing(\"requeue-token\", STORE, _REQUEUE, \" AND attempt_token = :token\", \"the reconciler requeues on a stale token\"),\n    removing(\"requeue-lease\", STORE, _REQUEUE, \" AND lease_expires_at <= :now\", \"the reconciler requeues a live lease\"),\n    removing(\"exhaust-token\", STORE, _EXHAUST, \" AND attempt_token = :token\", \"exhausting a job on a stale token\"),\n    removing(\"claim-keeps-publication\", STORE, _CLAIM, \"published_at = NULL,\", \"a claim keeps the recorded publication\"),\n    removing(\"claim-version-bump\", STORE, _CLAIM, \"version = version + 1, \", \"a claim does not bump the version\"),\n    removing(\"publication-version\", STORE, \"AND published_at IS NULL AND version = :version\\\",\",\n             \" AND version = :version\", \"a late confirmation is recorded after the job moved on\"),\n    Mutation(\"accept-repeat-token\", STORE,\n             \"\\\" WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token\\\",\",\n             \"\\\" WHERE j.job_id = :job_id AND j.status = 'succeeded'\\\",\",\n             \"a repeated acceptance is reported for any token\"),\n    Mutation(\"rollback\", STORE, 'cursor.execute(\"ROLLBACK\")', 'cursor.execute(\"COMMIT\")',\n             \"a failed transaction commits what it wrote\"),\n    Mutation(\"one-row-check\", STORE, \"if count != 1:\", \"if count > 1:\", \"a job_attempts write may touch no row\"),\n    Mutation(\"conflict-detection\", MYSQL, \"error.args[0] in CONFLICT_ERRORS\", \"error.args[0] in ()\",\n             \"deadlocks and lock wait timeouts are not run again\", needs=(\"mysql\",)),\n    # The worker (docs/job-queue.md, \"What the worker does with a delivery\").\n    Mutation(\"output-folder-check\", WORKER, \"exist_ok=False\", \"exist_ok=True\", \"an attempt writes into an existing folder\"),\n    Mutation(\"acknowledge-after-claim\", WORKER, '        self._fault(\"after_claim\")\\n        acknowledge()\\n',\n             '        self._fault(\"after_claim\")\\n', \"a claimed delivery is never acknowledged\"),\n    Mutation(\"rewind\", WORKER, \"consumer.rewind(delivery)\", \"pass\", \"a failed delivery is not read again\"),\n    Mutation(\"bounded-retries\", WORKER, \"if failures > retries:\", \"if False:\", \"serve() retries one message forever\"),\n    Mutation(\"malformed-commit\", WORKER,\n             \"                served.malformed += 1\\n                self._commit(consumer, delivery, served)\\n\",\n             \"                served.malformed += 1\\n\", \"a malformed message is skipped without a commit\"),\n    # Job ids in messages (docs/job-queue.md, Settings).\n    Mutation(\"job-id-leading-zero\", QUEUE, 'rb\"[1-9][0-9]{0,%d}\"', 'rb\"[0-9][0-9]{0,%d}\"', \"zero and leading zeros pass\"),\n    Mutation(\"job-id-format\", QUEUE, \"if _JOB_ID.fullmatch(self.value) is None:\", \"if False:\", \"text reaches int()\"),\n    Mutation(\"job-id-length\", QUEUE, \"MAX_JOB_ID_DIGITS - 1\", \"MAX_JOB_ID_DIGITS + 4999\", \"5,000 digits reach int()\"),\n    Mutation(\"job-id-range\", QUEUE, \"return job_id if job_id <= MAX_JOB_ID else None\", \"return job_id\",\n             \"ids beyond the range reach the database\"),\n    # The reconciler.\n    Mutation(\"grace-boundary\", RECONCILER, \"now - job.queued_since < self.publication_grace\",\n             \"now - job.queued_since <= self.publication_grace\", \"the grace period is one tick too long\"),\n    Mutation(\"grace-for-requeued\", RECONCILER, \"if job.attempt_number == 0 and now\", \"if now\",\n             \"a requeued job waits for the grace period\"),\n    # Kafka settings (etf_risk.jobs.kafka).\n    Mutation(\"auto-commit\", KAFKA, '\"enable.auto.commit\": False', '\"enable.auto.commit\": True', \"offsets commit on their own\"),\n    Mutation(\"offset-store\", KAFKA, '\"enable.auto.offset.store\": False', '\"enable.auto.offset.store\": True',\n             \"positions are stored without a commit\"),\n    Mutation(\"offset-reset\", KAFKA, '\"auto.offset.reset\": \"earliest\"', '\"auto.offset.reset\": \"latest\"',\n             \"a new group skips earlier jobs\"),\n    Mutation(\"acks\", KAFKA, '\"acks\": \"all\"', '\"acks\": \"1\"', \"the producer stops asking for acks=all\"),\n    Mutation(\"idempotence\", KAFKA, '\"enable.idempotence\": True', '\"enable.idempotence\": False', \"idempotence off\"),\n)\n\n\ndef make_scratch() -> Path:\n    scratch = Path(tempfile.mkdtemp(prefix=\"etf-risk-mutations-\"))\n    ignore = shutil.ignore_patterns(\"__pycache__\", \".pytest_cache\")\n    for item in COPIED:\n        source = REPO / item\n        if source.is_dir():\n            shutil.copytree(source, scratch / item, ignore=ignore)\n        else:\n            shutil.copy2(source, scratch / item)\n    env = {k: v for k, v in os.environ.items() if k != \"VIRTUAL_ENV\"}\n    subprocess.run([\"uv\", \"sync\", \"--frozen\", \"--group\", \"jobs\"], cwd=scratch, env=env, check=True,\n                   capture_output=True, text=True)\n    return scratch\n\n\ndef run_tests(scratch: Path, timeout: float) -> dict:\n    \"\"\"The job tests in a new process group; the group is killed on timeout.\"\"\"\n    env = {k: v for k, v in os.environ.items() if k != \"VIRTUAL_ENV\"}\n    command = [str(scratch / \".venv\" / \"bin\" / \"python\"), \"-m\", \"pytest\", *JOB_TESTS, \"-x\", \"-q\",\n               \"-p\", \"no:cacheprovider\"]\n    start = time.monotonic()\n    process = subprocess.Popen(command, cwd=scratch, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,\n                               text=True, start_new_session=True)\n    try:\n        output, _ = process.communicate(timeout=timeout)\n        code = process.returncode\n    except subprocess.TimeoutExpired:\n        os.killpg(process.pid, signal.SIGKILL)\n        output, _ = process.communicate()\n        code = None\n    failed = next((line for line in output.splitlines() if line.startswith(\"FAILED \")), None)\n    return {\"exit_code\": code, \"seconds\": round(time.monotonic() - start, 1), \"first_failure\": failed,\n            \"output_tail\": output[-3000:]}\n\n\ndef outcome(result: dict) -> str:\n    return {1: \"caught\", 0: \"survived\"}.get(result[\"exit_code\"], \"error\")\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])\n    parser.add_argument(\"--only\", nargs=\"+\", metavar=\"ID\", help=\"run these mutations only\")\n    parser.add_argument(\"--timeout\", type=float, default=600.0, help=\"seconds per run of the job tests (default 600)\")\n    parser.add_argument(\"--out\", type=Path, help=\"folder for mutations.json\")\n    parser.add_argument(\"--list\", action=\"store_true\", help=\"list the mutations and exit\")\n    args = parser.parse_args(argv)\n    if args.list:\n        for m in MUTATIONS:\n            print(f\"{m.id:26} {m.file.removeprefix('src/etf_risk/jobs/'):14} {m.breaks}\"\n                  + (f\"  (needs {', '.join(m.needs)})\" if m.needs else \"\"))\n        return 0\n    unknown = set(args.only or ()) - {m.id for m in MUTATIONS}\n    if unknown:\n        parser.error(f\"unknown mutation(s): {', '.join(sorted(unknown))}\")\n    selected = [m for m in MUTATIONS if not args.only or m.id in args.only]\n    backends = {name: bool(os.environ.get(variable)) for name, variable in NEEDS.items()}\n    record = {\"format\": 1, \"started_at_utc\": datetime.now(timezone.utc).isoformat(), \"code\": code_state(),\n              \"backends\": {\"sqlite\": True, **backends}, \"timeout_s\": args.timeout, \"mutations\": []}\n    scratch = make_scratch()\n    try:\n        baseline = run_tests(scratch, args.timeout)\n        record[\"baseline\"] = baseline\n        print(f\"baseline: exit {baseline['exit_code']} in {baseline['seconds']} s\")\n        if baseline[\"exit_code\"] != 0:\n            print(baseline[\"output_tail\"], file=sys.stderr)\n            print(\"the unmutated job tests must pass first\", file=sys.stderr)\n            return 1\n        for m in selected:\n            missing = [need for need in m.needs if not backends[need]]\n            if missing:\n                record[\"mutations\"].append({**asdict(m), \"outcome\": \"skipped\", \"missing\": missing})\n                print(f\"skipped   {m.id} (needs {', '.join(missing)})\")\n                continue\n            path = scratch / m.file\n            original = path.read_text()\n            if original.count(m.old) != 1:\n                raise SystemExit(f\"{m.id}: the text to replace occurs {original.count(m.old)} times in {m.file}\")\n            path.write_text(original.replace(m.old, m.new, 1))\n            try:\n                result = run_tests(scratch, args.timeout)\n            finally:\n                path.write_text(original)\n            record[\"mutations\"].append({**asdict(m), \"outcome\": outcome(result), **result})\n            print(f\"{outcome(result):9} {m.id} ({result['seconds']} s){'  ' + result['first_failure'] if result['first_failure'] else ''}\")\n    finally:\n        shutil.rmtree(scratch, ignore_errors=True)\n    ran = [m for m in record[\"mutations\"] if m[\"outcome\"] != \"skipped\"]\n    record[\"summary\"] = {o: sum(1 for m in record[\"mutations\"] if m[\"outcome\"] == o)\n                         for o in (\"caught\", \"survived\", \"error\", \"skipped\")}\n    print(f\"{record['summary']['caught']} of {len(ran)} caught; {record['summary']}\")\n    if args.out:\n        args.out.mkdir(parents=True, exist_ok=True)\n        (args.out / \"mutations.json\").write_text(json.dumps(record, indent=2) + \"\\n\")\n    return 0 if ran and all(m[\"outcome\"] == \"caught\" for m in ran) else 1\n\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n"
}
```

## 272. Assistant — 2026-10-23T12:34:13.056Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python tests/mutation_check.py --list && grep -c 'MAX_JOB_ID_DIGITS - 1' src/etf_risk/jobs/queue.py",
  "description": "List the mutations and confirm one target's uniqueness"
}
```

## 273. User — 2026-10-23T12:34:14.742Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/mutation_check.py (file state is current in your context — no need to Read it back)
```

## 274. User — 2026-10-23T12:34:16.091Z

### Tool result

```
renew-token                store.py       renewal without the token: a fenced worker renews
accept-token               store.py       acceptance without the token
fail-token                 store.py       fail_attempt without the token
takeover-lease             store.py       a claim takes over a live lease
takeover-attempts-left     store.py       a claim takes over with no attempts left
requeue-token              store.py       the reconciler requeues on a stale token
requeue-lease              store.py       the reconciler requeues a live lease
exhaust-token              store.py       exhausting a job on a stale token
claim-keeps-publication    store.py       a claim keeps the recorded publication
claim-version-bump         store.py       a claim does not bump the version
publication-version        store.py       a late confirmation is recorded after the job moved on
accept-repeat-token        store.py       a repeated acceptance is reported for any token
rollback                   store.py       a failed transaction commits what it wrote
one-row-check              store.py       a job_attempts write may touch no row
conflict-detection         mysql.py       deadlocks and lock wait timeouts are not run again  (needs mysql)
output-folder-check        worker.py      an attempt writes into an existing folder
acknowledge-after-claim    worker.py      a claimed delivery is never acknowledged
rewind                     worker.py      a failed delivery is not read again
bounded-retries            worker.py      serve() retries one message forever
malformed-commit           worker.py      a malformed message is skipped without a commit
job-id-leading-zero        queue.py       zero and leading zeros pass
job-id-format              queue.py       text reaches int()
job-id-length              queue.py       5,000 digits reach int()
job-id-range               queue.py       ids beyond the range reach the database
grace-boundary             reconciler.py  the grace period is one tick too long
grace-for-requeued         reconciler.py  a requeued job waits for the grace period
auto-commit                kafka.py       offsets commit on their own
offset-store               kafka.py       positions are stored without a commit
offset-reset               kafka.py       a new group skips earlier jobs
acks                       kafka.py       the producer stops asking for acks=all
idempotence                kafka.py       idempotence off
1
```

## 275. Assistant — 2026-10-23T12:34:27.729Z

### Tool call: Bash

```
{
  "command": "mkdir -p /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-offline-1 && env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python tests/mutation_check.py --timeout 300 --out /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-offline-1 > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-offline-1/console.txt 2>&1; echo \"exit $?\" >> /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-offline-1/console.txt",
  "description": "Run the offline mutation checks in the background",
  "run_in_background": true
}
```

## 276. User — 2026-10-23T12:34:28.214Z

### Tool result

```
Command running in background with ID: bglnscw9q. Output is being written to: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/tasks/bglnscw9q.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need a line it prints before you can go on, such as a server's ready line or port.
```

## 277. Assistant — 2026-10-23T12:34:38.756Z

### Tool call: Bash

```
{
  "command": "sed -n '10,24p;73,107p' docs/job-table.md",
  "description": "Show the job-table doc sections to correct"
}
```

## 278. User — 2026-10-23T12:34:39.187Z

### Tool result

````
## claim(): two guarded updates

A claim tries two conditional updates of the job's row, in one transaction:

```sql
-- 1. a queued job
UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1, attempt_token = :token,
       lease_expires_at = :lease_expires_at, version = version + 1, updated_at = :now
 WHERE job_id = :job_id AND status = 'queued';
-- 2. only if 1 matched no row: a running job whose lease has expired, with attempts left
UPDATE jobs SET ... (the same)
 WHERE job_id = :job_id AND status = 'running' AND lease_expires_at <= :now
   AND attempt_number < max_attempts;
```

## Transactions

- Every operation is one transaction. Apart from `submit`, each writes both tables: the
  update of `jobs` decides, and the write to `job_attempts` records; that write must touch
  exactly one row, or the store raises and both tables roll back.
- Any exception rolls the transaction back, including a simulated crash. The tests raise at
  each gap between two statements (`FAULT_POINTS`) and check both tables afterwards.
- Every transaction locks the `jobs` row before any `job_attempts` row, and none spans a
  pipeline run: locks last milliseconds, and a crashed worker leaves an expiring lease, not a
  held lock.
- A COMMIT that fails may still have taken effect, so repeating an operation must be safe:
  `accept_result` returns true when the accepted attempt's token is the caller's.
- In MySQL, an operation rolled back by a deadlock or a lock wait timeout runs again, up to
  three runs in all.

## What is checked where

- [`tests/test_jobs_store.py`](../tests/test_jobs_store.py) and
  [`tests/test_jobs_worker.py`](../tests/test_jobs_worker.py) run on SQLite, and on MySQL as
  well when `ETF_RISK_MYSQL_URL` is set. On SQLite, competing connections run one after another
  under the database lock: those runs check the state logic, not InnoDB's row locks.
- [`tests/test_jobs_mysql.py`](../tests/test_jobs_mysql.py) checks the MySQL adapter offline
  and, against a server, the InnoDB behaviour the SQL relies on (setup in its docstring and in
  [`docker/compose.yaml`](../docker/compose.yaml)).
- Status on 2026-10-22: with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set,
  all 222 cases pass, in five runs in a row; without the URL, 114 pass and the 7 tests that
  need a server are skipped. Breaking any one of eleven guards and checks on purpose (the
  token, lease and attempts-left conditions, the rollback, the one-row check on
  `job_attempts` writes, the `version` bump, conflict detection, the output folder check)
  makes at least one test fail. On top of main at e55f76b (after the caching experiment),
  the job tests give the same counts and the whole suite passes (350 passed, 7 skipped).
  The MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget
  (cgroup `memory.peak`, which includes page cache).

*AI contribution: written with Claude Code (Opus 5.5).*
````

## 279. Assistant — 2026-10-23T12:34:42.665Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md",
  "old_string": "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1, attempt_token = :token,\n       lease_expires_at = :lease_expires_at, version = version + 1, updated_at = :now\n WHERE job_id = :job_id AND status = 'queued';",
  "new_string": "UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1, attempt_token = :token,\n       lease_expires_at = :lease_expires_at, published_at = NULL, version = version + 1, updated_at = :now\n WHERE job_id = :job_id AND status = 'queued';"
}
```

## 280. Assistant — 2026-10-23T12:34:44.623Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md",
  "old_string": "- Every operation is one transaction. Apart from `submit`, each writes both tables: the\n  update of `jobs` decides, and the write to `job_attempts` records; that write must touch\n  exactly one row, or the store raises and both tables roll back.",
  "new_string": "- Every operation is one transaction. Apart from `submit` and `mark_published`, each writes\n  both tables: the update of `jobs` decides, and the write to `job_attempts` records; that\n  write must touch exactly one row, or the store raises and both tables roll back."
}
```

## 281. Assistant — 2026-10-23T12:34:50.503Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md",
  "old_string": "- Status on 2026-10-22: with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set,\n  all 222 cases pass, in five runs in a row; without the URL, 114 pass and the 7 tests that\n  need a server are skipped. Breaking any one of eleven guards and checks on purpose (the\n  token, lease and attempts-left conditions, the rollback, the one-row check on\n  `job_attempts` writes, the `version` bump, conflict detection, the output folder check)\n  makes at least one test fail. On top of main at e55f76b (after the caching experiment),\n  the job tests give the same counts and the whole suite passes (350 passed, 7 skipped).\n  The MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget\n  (cgroup `memory.peak`, which includes page cache).",
  "new_string": "- [`tests/mutation_check.py`](../tests/mutation_check.py) breaks the guards and checks on\n  purpose, one at a time, in a scratch copy of the repository, and expects the job tests to\n  fail within a timeout. It covers the token, lease and attempts-left conditions, the\n  rollback, the one-row check on `job_attempts` writes, the `version` bump, conflict\n  detection, the output folder check, and the queue's guards in\n  [job-queue.md](job-queue.md).\n- Status when this table was merged (PR #7), on 2026-10-22:\n  - with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set, all 222 cases\n    passed, in five runs in a row;\n  - without the URL, 114 passed and the 7 tests that need a server were skipped;\n  - breaking any one of eleven guards and checks by hand made at least one test fail.\n    Those mutations were not recorded as a list; `tests/mutation_check.py` rebuilds them\n    from this description;\n  - the MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget\n    (cgroup `memory.peak`, which includes page cache).\n\n  The current status of the job tests, with the Kafka delivery of PR #8, is in\n  [job-queue.md](job-queue.md)."
}
```

## 282. User — 2026-10-23T12:34:51.591Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md has been updated successfully.
```

## 283. User — 2026-10-23T12:34:52.665Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md has been updated successfully.
```

## 284. User — 2026-10-23T12:34:53.724Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md has been updated successfully.
```

## 285. Assistant — 2026-10-23T12:34:58.814Z

Next, `docs/job-queue.md`. For its module origin table, I'm pulling which commits and PRs touched each jobs file from git, rather than writing it from memory:

## 286. Assistant — 2026-10-23T12:35:00.871Z

### Tool call: Bash

```
{
  "command": "for f in $(git ls-files src/etf_risk/jobs); do printf '%-36s ' \"${f#src/etf_risk/}\"; git log --format='%h' --reverse -- \"$f\" | tr '\\n' ' '; echo; done; echo \"---\"; git log --merges --format='%h %s' --ancestry-path eec1032..main | grep -E 'pull request #(7|8|10)'; git log --format='%h %s' -1 6cfd971; git log --format='%h %s' -1 cd72957",
  "description": "List the commits that touched each jobs file and their PRs"
}
```

## 287. User — 2026-10-23T12:35:01.637Z

### Tool result

```
jobs/__init__.py                     eec1032 e2806bd 
jobs/kafka.py                        e2806bd 
jobs/mysql.py                        eec1032 
jobs/queue.py                        e2806bd 
jobs/reconciler.py                   e2806bd 
jobs/schema/mysql.sql                eec1032 e2806bd 
jobs/schema/sqlite.sql               eec1032 e2806bd 
jobs/simulated.py                    eec1032 e2806bd 
jobs/store.py                        eec1032 e2806bd 
jobs/worker.py                       eec1032 e2806bd 
---
7b1e758 Merge pull request #10 from [REDACTED:git-user]/fix/measure-process-kinds
ac23db6 Merge pull request #8 from [REDACTED:git-user]/feature/job-queue
6976e05 Merge pull request #7 from [REDACTED:git-user]/feature/job-table
6cfd971 Record the job table's status in the README and spec
cd72957 Record the MySQL validation of e2806bd in the job-queue docs
```

## 288. Assistant — 2026-10-23T12:35:03.261Z

### Tool call: Bash

```
{
  "command": "sed -n '84,92p;124,169p' docs/job-queue.md",
  "description": "Show the job-queue doc sections to correct"
}
```

## 289. User — 2026-10-23T12:35:03.957Z

### Tool result

```
| 61 s | reconciler: the lease has expired; it requeues with A's token; attempt 1 is expired; it publishes the job in the same pass and records the confirmation | queued, publication recorded; 2 messages |
| 62 s | A polls the new message, claims attempt 2, commits, runs and accepts | succeeded, accepted attempt 2 |

Job 9 executed twice and accepted one result. Had the job still been queued at 30 s, with
its first confirmation lost, the reconciler would have published it then. The duplicate
message would later find the job running or finished, and the claim would refuse it.
`test_a_crash_between_claim_and_commit` runs this sequence offline and against Kafka.

## What the worker does with a delivery
## What is checked where

- [`tests/test_jobs_reconciler.py`](../tests/test_jobs_reconciler.py) and
  [`tests/test_jobs_queue.py`](../tests/test_jobs_queue.py) use the in-memory queue. They
  run on SQLite, and on MySQL as well when `ETF_RISK_MYSQL_URL` is set. They cover:
  - the guards and the grace period;
  - the job-id format, including a 5,000-digit payload and ids beyond the range, each
    followed by a valid job that must still run;
  - the worker's commits, rewinds and bounded retries;
  - whole scenarios, including a seeded run with lost publications and crashes at every
    fault point.
  Tests that run a loop (`serve()`, the reconciler's `run()`) stop it themselves, after a
  number of tries or a few seconds, so a broken guard makes them fail rather than hang.
- [`tests/test_jobs_kafka.py`](../tests/test_jobs_kafka.py) checks the settings offline.
  With `ETF_RISK_KAFKA_BOOTSTRAP` set, it checks against Kafka 4.3.1 from
  [`docker/compose.yaml`](../docker/compose.yaml):
  - delivery to a fresh consumer group, and `latest` for comparison;
  - confirmation, including an unreachable broker;
  - commits and rewinds;
  - a 5,000-digit payload ahead of a job: both committed, and the job runs;
  - a message left uncommitted after the retries, for a restarted worker;
  - two end-to-end scenarios.
- Status on 2026-10-23:
  - **Offline:** 200 passed, and the 17 tests that need MySQL, Kafka or confluent-kafka
    were skipped.
  - **With Kafka 4.3.1** (the job table on SQLite): 210 passed, and the 7 tests that
    need MySQL were skipped.
  - **With MySQL 8.4.13 and Kafka 4.3.1, on the committed revision e2806bd:** 379
    passed, none failed or skipped, in one run on fresh containers (162 cases on each
    store). An earlier revision, before the job-id validation, had 353 passed.
  - **The whole suite:** 411 passed and 15 skipped. That run came before the bounded
    retries, the job-id validation and the test fixes; the rest of the suite does not
    use these files.
  - **Mutation checks:** 22 guards and settings were broken on purpose, one at a time,
    in 25 test runs: three were run both offline and against Kafka. Each run had a
    timeout. The 22 include 4 for the job-id format and range. Tests failed in all 25
    runs; none ran into the timeout. Before the fixes, three ran until it:
    - a claim that keeps the publication, through `serve()`'s unbounded retries;
    - the grace boundary off by one, through a test that waited for the publisher to
      stop the reconciler's loop;
    - the rewind removed, through a test that waited for a failing claim to come back.
  - **Memory:** spec §11 records the peaks. MySQL reached 511 of its 512 MiB over about
    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That
    is limited headroom, not evidence that longer runs stay within the limit.

*AI contribution: written with Claude Code (Opus 5.5).*
```

## 290. Assistant — 2026-10-23T12:35:10.022Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "message would later find the job running or finished, and the claim would refuse it.\n`test_a_crash_between_claim_and_commit` runs this sequence offline and against Kafka.",
  "new_string": "message would later find the job running or finished, and the claim would refuse it.\n`test_the_job_9_timeline` (tests/test_jobs_queue.py) follows this table row by row with\nthe in-memory queue, on SQLite and, when configured, on MySQL. That includes the lost\nconfirmation at 0 s and the pass at 30 s that leaves the running job alone.\n`test_a_crash_between_claim_and_commit` runs the crash and the takeover, from a confirmed\npublication, offline and against Kafka."
}
```

## 291. Assistant — 2026-10-23T12:35:11.950Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "  - whole scenarios, including a seeded run with lost publications and crashes at every\n    fault point.",
  "new_string": "  - whole scenarios, including the job-9 timeline above and a seeded run with lost\n    publications and crashes at every one of the worker's fault points\n    (`WORKER_FAULT_POINTS`; the store's own fault points are covered in\n    tests/test_jobs_store.py)."
}
```

## 292. Assistant — 2026-10-23T12:35:17.492Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "  - a message left uncommitted after the retries, for a restarted worker;\n  - two end-to-end scenarios.",
  "new_string": "  - a message left uncommitted after the retries, for a restarted worker;\n  - two end-to-end scenarios.\n- [`tests/mutation_check.py`](../tests/mutation_check.py) breaks one guard or setting at a\n  time, in a scratch copy of the repository, and expects the job tests to fail within a\n  timeout. It has 31 mutations; one, conflict detection, needs MySQL.\n  - **Coverage:**\n    - the store's guards ([job-table.md](job-table.md));\n    - the claim's cleared publication and version bump;\n    - the publication's version guard;\n    - the worker's acknowledgement, rewind, bounded retries and malformed-message commit;\n    - the job-id format, length and range;\n    - the grace period;\n    - the five Kafka settings above.\n  - **Running it:** `uv run --group jobs python tests/mutation_check.py --list` names them,\n    and setting the service variables adds the MySQL and Kafka runs.\n- [`etf_risk.services`](../src/etf_risk/services.py) supports the live runs:\n  - `ready mysql kafka` waits until a login and `SELECT 1` succeed and the broker answers a\n    metadata request. The Compose healthchecks only show that the ports are open.\n  - `peaks mysql kafka` prints each container's cgroup `memory.peak` against its limit.\n  - `others` counts containers of other projects in Docker's VM, without naming them."
}
```

## 293. User — 2026-10-23T12:35:18.577Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 294. User — 2026-10-23T12:35:19.652Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 295. User — 2026-10-23T12:35:20.720Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 296. Assistant — 2026-10-23T12:35:28.911Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "  - **Memory:** spec §11 records the peaks. MySQL reached 511 of its 512 MiB over about\n    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That\n    is limited headroom, not evidence that longer runs stay within the limit.\n\n*AI contribution: written with Claude Code (Opus 5.5).*",
  "new_string": "  - **Memory:** spec §11 records the peaks. MySQL reached 511 of its 512 MiB over about\n    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That\n    is limited headroom, not evidence that longer runs stay within the limit.\n\n## Code provenance\n\nEvery run record identifies the job package's code. `provenance.code_state()` hashes every\nPython module and SQL schema under `src/etf_risk/`, including `jobs/` and its schema files,\nkeyed by package-relative path, for example `jobs/store.py`. Records written before\n2026-10-23 hash only the top-level modules. All of `jobs/` was written with Claude Code\n(Opus 5.5), as each module's docstring says. It came in through two PRs:\n\n| Module | Commits | PR | Verified by |\n|---|---|---|---|\n| `store.py`, `schema/mysql.sql`, `schema/sqlite.sql`, `worker.py`, `simulated.py`, `__init__.py` | eec1032 (milestone 1), e2806bd (milestone 2) | #7, #8 | test_jobs_store, test_jobs_worker, test_jobs_queue, test_jobs_reconciler; mutation_check |\n| `mysql.py` | eec1032 | #7 | test_jobs_mysql (offline and against MySQL 8.4.13) |\n| `queue.py`, `kafka.py`, `reconciler.py` | e2806bd | #8 | test_jobs_queue, test_jobs_reconciler, test_jobs_kafka (offline and against Kafka 4.3.1); mutation_check |\n\nThe status notes of both PRs came in separate commits: 6cfd971 for #7 and cd72957 for #8.\n\n*AI contribution: written with Claude Code (Opus 5.5).*"
}
```

## 297. User — 2026-10-23T12:35:30.114Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 298. Assistant — 2026-10-23T12:35:46.890Z

Now the README runbook skeleton. It contains only commands that exist today; the E1/E2 and E3 stacks are marked as arriving with M2 and M4.

## 299. Assistant — 2026-10-23T12:35:54.289Z

### Tool call: Edit

````
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/README.md",
  "old_string": "in the container (a Linux VM on macOS, data on bind mounts) are a separate\nconfiguration, not comparable with native measurements.\n\n## Data",
  "new_string": "in the container (a Linux VM on macOS, data on bind mounts) are a separate\nconfiguration, not comparable with native measurements.\n\n### Systems extension services (runbook)\n\nThese are for the optional job queue ([spec §11](docs/spec.md)).\n- **Compose services.** MySQL and Kafka run in Docker Compose\n  ([docker/compose.yaml](docker/compose.yaml)), each with a memory limit and reachable from\n  this machine only.\n- **Clients.** The job package's clients, PyMySQL and confluent-kafka, are pinned in the\n  `jobs` dependency group.\n- **Git worktrees.** In a worktree, `data/` is a symlink to the main checkout's (ignored by\n  Git): `ln -s <main checkout>/data data`.\n\n```bash\ndocker compose -f docker/compose.yaml up -d --wait mysql kafka\n# The healthchecks only see open ports; this waits for a MySQL login and SELECT 1, and Kafka metadata\nuv run --group jobs python -m etf_risk.services ready mysql kafka\n# The job tests against both services (offline, they run on SQLite and skip these)\nETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \\\n    uv run --group jobs python -m pytest tests/test_jobs_*.py\n# Each container's cgroup memory.peak against its limit, and the containers of other projects (a count)\nuv run python -m etf_risk.services peaks mysql kafka\nuv run python -m etf_risk.services others\n# Break each guard on purpose and expect a failing test; set the two variables to include MySQL and Kafka\nuv run --group jobs python tests/mutation_check.py --out data/outputs-mutations\ndocker compose -f docker/compose.yaml down -v      # removes the data volumes as well\n```\n\n- **Memory budgets** (spec §11) are measured with no other project's containers in Docker's\n  VM; `services others --require-none` exits 1 otherwise.\n- **Still to come.** The worker, reconciler and submit commands, with the real pipeline, and\n  the Redis result cache are added in later milestones. Until then, the worker runs only the\n  simulated pipeline, inside the tests.\n\n## Data"
}
````

## 300. User — 2026-10-23T12:35:55.477Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/README.md has been updated successfully.
```

## 301. Assistant — 2026-10-23T12:35:59.531Z

Next, the spec. §5's module list gains `services.py` and the broader provenance scope, and §9's Environment row gains the `jobs` group.

## 302. Assistant — 2026-10-23T12:36:00.466Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'provenance.py      implemented|plots.py           implemented|jobs/              implemented|^\\| Environment|^tests/               implemented|the job table,$|worker, queue and reconciler' docs/spec.md",
  "description": "Locate the spec lines to update"
}
```

## 303. User — 2026-10-23T12:36:01.042Z

### Tool result

```
168:  provenance.py      implemented  code state for every record (commit, worktree state, SHA-256 of sources and uv.lock); repo-relative paths
172:  plots.py           implemented  the twelve figures from result files, checked against the documented values (Stage 4)
173:  jobs/              implemented  optional job queue (§11): job table schema (MySQL, SQLite mirror), guarded state
182:tests/               implemented  model, validation, ingest, download, windows, Spark consistency and failure
186:                                  the caching option, the caching collector and session helpers, the job table,
187:                                  worker, queue and reconciler (on SQLite; on MySQL and Kafka when configured)
667:| Environment | uv lockfile; pandas below 3 for PySpark; pandas-market-calendars 5.5.0, yfinance 1.7.0, psutil 7.2.2 and matplotlib 3.11.2 pinned exactly; Docker image for the pipeline (Python 3.12, Java 17, locked dependencies, base images pinned by digest; data mounted, not copied; commit recorded at build time) | a NumPy pin (pandas 2.3 emits deprecation warnings under NumPy 2.5) |
```

## 304. Assistant — 2026-10-23T12:36:02.555Z

### Tool call: Bash

```
{
  "command": "sed -n '173,176p;186,188p' docs/spec.md",
  "description": "Show the jobs and tests lines of the spec's module list"
}
```

## 305. User — 2026-10-23T12:36:03.268Z

### Tool result

```
  jobs/              implemented  optional job queue (§11): job table schema (MySQL, SQLite mirror), guarded state
                                  transitions (store.py), MySQL and Kafka adapters, worker and its consume loop,
                                  reconciler, simulated pipeline and in-memory queue
analysis/            implemented  three Spark SQL analyses of a run's paired table (project author):
                                  the caching option, the caching collector and session helpers, the job table,
                                  worker, queue and reconciler (on SQLite; on MySQL and Kafka when configured)
.claude/hooks/       implemented  per-message AI-usage logs with redaction (project tooling, not analysis)
```

## 306. Assistant — 2026-10-23T12:36:06.654Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md",
  "old_string": "  provenance.py      implemented  code state for every record (commit, worktree state, SHA-256 of sources and uv.lock); repo-relative paths",
  "new_string": "  provenance.py      implemented  code state for every record (commit, worktree state, SHA-256 of uv.lock and of every module\n                                  and SQL schema under src/etf_risk/, jobs/ included, by package-relative path, since\n                                  2026-10-23; earlier records hash the top-level modules only); repo-relative paths"
}
```

## 307. Assistant — 2026-10-23T12:36:08.411Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md",
  "old_string": "                                  reconciler, simulated pipeline and in-memory queue\nanalysis/            implemented",
  "new_string": "                                  reconciler, simulated pipeline and in-memory queue\n  services.py        implemented  the extension's Compose services from this machine: readiness (a MySQL login, Kafka\n                                  metadata), cgroup memory peaks, and a count of other projects' containers\nanalysis/            implemented"
}
```

## 308. Assistant — 2026-10-23T12:36:10.208Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md",
  "old_string": "                                  worker, queue and reconciler (on SQLite; on MySQL and Kafka when configured)",
  "new_string": "                                  worker, queue and reconciler (on SQLite; on MySQL and Kafka when configured), the\n                                  services helper, and the job queue's mutation checks (tests/mutation_check.py)"
}
```

## 309. Assistant — 2026-10-23T12:36:12.548Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md",
  "old_string": "| Environment | uv lockfile; pandas below 3 for PySpark; pandas-market-calendars 5.5.0, yfinance 1.7.0, psutil 7.2.2 and matplotlib 3.11.2 pinned exactly;",
  "new_string": "| Environment | uv lockfile; pandas below 3 for PySpark; pandas-market-calendars 5.5.0, yfinance 1.7.0, psutil 7.2.2 and matplotlib 3.11.2 pinned exactly; the job queue's clients PyMySQL 1.1.1 and confluent-kafka 2.16.0 pinned exactly in the `jobs` group;"
}
```

## 310. User — 2026-10-23T12:36:13.636Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md has been updated successfully.
```

## 311. User — 2026-10-23T12:36:14.714Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md has been updated successfully.
```

## 312. User — 2026-10-23T12:36:15.799Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md has been updated successfully.
```

## 313. User — 2026-10-23T12:36:16.911Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/spec.md has been updated successfully.
```

## 314. Assistant — 2026-10-23T12:36:21.018Z

While the mutation run continues, I'm reviewing the full diff so far.

## 315. Assistant — 2026-10-23T12:36:21.700Z

### Tool call: Bash

```
{
  "command": "git status --short && git diff --stat && git diff src/etf_risk/provenance.py",
  "description": "Show the working changes and the provenance diff"
}
```

## 316. User — 2026-10-23T12:36:22.166Z

### Tool result

```
 M .gitignore
 M README.md
 M docker/compose.yaml
 M docs/job-queue.md
 M docs/job-table.md
 M docs/spec.md
 M pyproject.toml
 M src/etf_risk/jobs/kafka.py
 M src/etf_risk/provenance.py
 M tests/test_jobs_kafka.py
 M tests/test_jobs_mysql.py
 M tests/test_jobs_queue.py
 M tests/test_provenance.py
 M uv.lock
?? src/etf_risk/services.py
?? tests/mutation_check.py
?? tests/test_services.py
 .gitignore                 |   5 +-
 README.md                  |  32 +++++++++++++
 docker/compose.yaml        |   2 +-
 docs/job-queue.md          |  46 ++++++++++++++++--
 docs/job-table.md          |  35 +++++++++-----
 docs/spec.md               |  11 +++--
 pyproject.toml             |   4 ++
 src/etf_risk/jobs/kafka.py |   5 +-
 src/etf_risk/provenance.py |  17 +++++--
 tests/test_jobs_kafka.py   |   2 +-
 tests/test_jobs_mysql.py   |   2 +-
 tests/test_jobs_queue.py   |  28 +++++++++++
 tests/test_provenance.py   |  32 ++++++++++++-
 uv.lock                    | 117 +++++++++++++++++++++++++++++++++++++++++++++
 14 files changed, 308 insertions(+), 30 deletions(-)
diff --git a/src/etf_risk/provenance.py b/src/etf_risk/provenance.py
index d4c87e3..d688c8b 100644
--- a/src/etf_risk/provenance.py
+++ b/src/etf_risk/provenance.py
@@ -1,8 +1,12 @@
 """Record which code produced a result, including uncommitted changes.
 
 A git commit alone does not identify the code when the worktree has changes, so
-code_state() also records whether the worktree is clean and the SHA-256 of every
-module in src/etf_risk/ and of uv.lock.
+code_state() also records whether the worktree is clean and the SHA-256 of uv.lock and
+of every Python module and SQL schema under src/etf_risk/, subpackages included (the
+job queue in jobs/ and its schema files). Keys are paths relative to src/etf_risk/, so a
+top-level module keeps the key it always had ("model.py") and jobs/__init__.py does not
+collide with __init__.py. Records written before 2026-10-23 hash the top-level modules
+only.
 
 The Docker image has no .git: there the commit and the clean flag come from what
 docker/build.sh recorded at build time (code_source = "build"), and docker/run.sh
@@ -21,6 +25,7 @@ from etf_risk.ingest import sha256_file
 
 PACKAGE_DIR = Path(__file__).resolve().parent
 REPO_ROOT = PACKAGE_DIR.parents[1]
+SOURCE_SUFFIXES = (".py", ".sql")
 
 # Set in the Docker image (Dockerfile, from docker/build.sh) and by docker/run.sh.
 BUILD_COMMIT_ENV = "ETF_RISK_GIT_COMMIT"
@@ -42,6 +47,12 @@ def _git(*args: str) -> str | None:
     return out.stdout.strip() if out.returncode == 0 else None
 
 
+def source_files() -> dict[str, Path]:
+    """Every Python module and SQL schema of the package, by path relative to it."""
+    files = (p for p in PACKAGE_DIR.rglob("*") if p.suffix in SOURCE_SUFFIXES and p.is_file())
+    return {p.relative_to(PACKAGE_DIR).as_posix(): p for p in sorted(files)}
+
+
 def code_state() -> dict:
     head = _git("rev-parse", "HEAD")
     status = _git("status", "--porcelain", "--untracked-files=all", "--", "src", "pyproject.toml", "uv.lock")
@@ -59,6 +70,6 @@ def code_state() -> dict:
         "git_worktree_clean": clean,
         "code_source": source,
         "image_id": os.environ.get(IMAGE_ID_ENV) or None,
-        "source_sha256": {p.name: sha256_file(p) for p in sorted(PACKAGE_DIR.glob("*.py"))},
+        "source_sha256": {key: sha256_file(path) for key, path in source_files().items()},
         "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
     }
```

## 317. Assistant — 2026-10-23T12:36:25.140Z

### Tool call: Bash

```
{
  "command": "cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-offline-1/console.txt",
  "description": "Show the offline mutation run's results"
}
```

## 318. User — 2026-10-23T12:36:25.592Z

### Tool result

```
baseline: exit 0 in 32.6 s
caught    renew-token (1.4 s)  FAILED tests/test_jobs_store.py::test_a_stale_worker_is_fenced_off_after_a_takeover[sqlite]
caught    accept-token (1.1 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-running-foreign_token]
caught    fail-token (1.2 s)  FAILED tests/test_jobs_store.py::test_a_stale_worker_is_fenced_off_after_a_takeover[sqlite]
caught    takeover-lease (1.0 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-running-claim]
caught    takeover-attempts-left (1.0 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-expired_last-claim]
caught    requeue-token (2.7 s)  FAILED tests/test_jobs_reconciler.py::test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too[sqlite]
caught    requeue-lease (0.9 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-running-requeue_expired]
survived  exhaust-token (5.1 s)
caught    claim-keeps-publication (1.0 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-published-claim]
caught    claim-version-bump (2.0 s)  FAILED tests/test_jobs_store.py::test_the_same_acceptance_twice_at_once_accepts_one_result[sqlite]
caught    publication-version (4.5 s)  FAILED tests/test_jobs_reconciler.py::test_a_confirmation_after_the_job_moved_on_is_not_recorded[sqlite]
caught    accept-repeat-token (1.3 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-succeeded-foreign_token]
caught    rollback (2.6 s)  FAILED tests/test_jobs_store.py::test_acceptance_repeated_after_a_failed_commit[sqlite-commit-not-applied]
caught    one-row-check (3.3 s)  FAILED tests/test_jobs_store.py::test_a_bookkeeping_write_that_misses_its_row_rolls_back_the_job_update[sqlite]
skipped   conflict-detection (needs mysql)
caught    output-folder-check (2.5 s)  FAILED tests/test_jobs_worker.py::test_an_existing_output_folder_is_never_written_into[sqlite]
caught    acknowledge-after-claim (2.2 s)  FAILED tests/test_jobs_worker.py::test_a_delivery_runs_the_job_once_and_accepts_its_result[sqlite]
caught    rewind (2.5 s)  FAILED tests/test_jobs_queue.py::test_an_error_before_the_acknowledgement_rewinds_and_the_job_runs_on_the_retry[sqlite]
caught    bounded-retries (2.6 s)  FAILED tests/test_jobs_queue.py::test_a_persistent_error_before_the_acknowledgement_is_raised_after_the_retries[sqlite]
survived  malformed-commit (5.3 s)
caught    job-id-leading-zero (2.4 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[0-None]
caught    job-id-format (2.6 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[-None]
caught    job-id-length (2.8 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[5000-digits]
caught    job-id-range (2.5 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[9223372036854775808-None]
caught    grace-boundary (2.5 s)  FAILED tests/test_jobs_queue.py::test_a_lost_confirmation_leads_to_a_duplicate_that_is_refused[sqlite]
caught    grace-for-requeued (2.5 s)  FAILED tests/test_jobs_queue.py::test_an_error_after_the_acknowledgement_leaves_the_job_to_its_lease[sqlite]
caught    auto-commit (6.5 s)  FAILED tests/test_jobs_kafka.py::test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message
caught    offset-store (3.1 s)  FAILED tests/test_jobs_kafka.py::test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message
caught    offset-reset (3.2 s)  FAILED tests/test_jobs_kafka.py::test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message
caught    acks (3.1 s)  FAILED tests/test_jobs_kafka.py::test_the_producer_waits_for_the_broker_and_is_idempotent
caught    idempotence (3.1 s)  FAILED tests/test_jobs_kafka.py::test_the_producer_waits_for_the_broker_and_is_idempotent
28 of 30 caught; {'caught': 28, 'survived': 2, 'error': 0, 'skipped': 1}
exit 1
```

## 319. Assistant — 2026-10-23T12:36:51.317Z

### Tool call: Bash

```
{
  "command": "grep -n \"def test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too\" -A 30 tests/test_jobs_reconciler.py | head -45; echo \"=== fixtures/imports\"; sed -n '1,45p' tests/test_jobs_reconciler.py | grep -n -E 'import|def env|fixture|max_attempts|LEASE' ",
  "description": "Show the existing stale-token reconciler test"
}
```

## 320. User — 2026-10-23T12:36:51.702Z

### Tool result

```
91:def test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too(env):
92-    """The token guard on its own: the reconciler read A's token, B took the job over, and
93-    B's lease expired as well before the reconciler's change. The lease condition alone
94-    would let the change through and requeue B's attempt on A's token."""
95-    job, a = lapsed(env)
96-    lease = env.admin.expired_leases()[0]                                       # A's token
97-    b = env.admin.claim(job, "worker-B", env.runs)                              # a takeover
98-    env.clock.advance(LEASE.total_seconds())                                    # B's lease expires too
99-    before = env.dump()
100-    assert env.admin.requeue_expired(lease.job_id, lease.token) is None
101-    assert env.dump() == before
102-    assert env.admin.requeue_expired(job, b.token) is Status.QUEUED             # B's own token: requeued
103-
104-
105-# mark_published: recording a confirmed publication
106-
107-def test_a_confirmed_publication_is_recorded_once(env):
108-    submitted = env.submit()
109-    assert (submitted.published, submitted.recorded) == (True, True)
110-    j = env.admin.job(submitted.job_id)
111-    assert j["published_at"] == env.clock.now() and j["version"] == 1
112-    assert not env.admin.mark_published(submitted.job_id, 0) and not env.admin.mark_published(submitted.job_id, 1)
113-    assert env.queue.job_ids() == [submitted.job_id] and env.admin.unconfirmed() == []
114-
115-
[REDACTED:email]("outcome", [PublishOutcome.UNCONFIRMED, PublishOutcome.DROPPED])
117-def test_an_unconfirmed_publication_is_not_recorded(env, outcome):
118-    submitted = env.submit([outcome])
119-    assert (submitted.published, submitted.recorded) == (False, False)
120-    assert env.admin.job(submitted.job_id)["published_at"] is None
121-    assert [j.job_id for j in env.admin.unconfirmed()] == [submitted.job_id]
=== fixtures/imports
11:import threading
12:from datetime import timedelta
14:import pytest
16:from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT
17:from etf_risk.jobs.reconciler import PUBLICATION_GRACE, RECONCILE_INTERVAL, Pass, Reconciler
18:from etf_risk.jobs.simulated import PublishOutcome, SimulatedCrash, SimulatedPipeline
19:from etf_risk.jobs.store import ExpiredLease, Outcome, Status
20:from jobs_backends import BACKENDS, LEASE, PARAMS, QueueEnv, make_backend, run_together
25:@pytest.fixture(params=BACKENDS)
26:def env(request, tmp_path):
36:    env.clock.advance(LEASE.total_seconds())
```

## 321. Assistant — 2026-10-23T12:36:53.301Z

### Tool call: Bash

```
{
  "command": "sed -n '25,45p' tests/test_jobs_reconciler.py",
  "description": "Show the reconciler test fixture and its lapsed helper"
}
```

## 322. User — 2026-10-23T12:36:53.741Z

### Tool result

```
@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = QueueEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
    env.close()


def lapsed(env, **kwargs):
    """A job claimed by worker A, whose lease has just expired, and A's claim."""
    job = env.admin.submit(PARAMS, {}, **kwargs)
    a = env.admin.claim(job, "worker-A", env.runs)
    env.clock.advance(LEASE.total_seconds())
    return job, a


def crash_at_step(step):
    def on_step(at, claim):
        if at == step:
            raise SimulatedCrash(f"step {step}")
    return on_step
```

## 323. Assistant — 2026-10-23T12:37:07.469Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_reconciler.py",
  "old_string": "    assert env.admin.requeue_expired(job, b.token) is Status.QUEUED             # B's own token: requeued\n\n\n",
  "new_string": "    assert env.admin.requeue_expired(job, b.token) is Status.QUEUED             # B's own token: requeued\n\n\ndef test_a_stale_token_is_refused_on_the_last_attempt_too(env):\n    \"\"\"The same on the path that fails a job. The reconciler read A's token, B took the job\n    over on its last attempt, and B's lease expired as well. Without the token guard in the\n    update that exhausts a job, A's stale token would fail the job through B's attempt.\"\"\"\n    job, a = lapsed(env, max_attempts=2)\n    lease = env.admin.expired_leases()[0]                                       # A's token\n    b = env.admin.claim(job, \"worker-B\", env.runs)                              # a takeover: attempt 2 of 2\n    env.clock.advance(LEASE.total_seconds())                                    # B's lease expires too\n    before = env.dump()\n    assert env.admin.requeue_expired(lease.job_id, lease.token) is None\n    assert env.dump() == before\n    assert env.admin.requeue_expired(job, b.token) is Status.FAILED             # B's own token: none left\n\n\n"
}
```

## 324. Assistant — 2026-10-23T12:37:10.024Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_queue.py",
  "old_string": "    assert env.admin.job(job)[\"status\"] is Status.SUCCEEDED\n    env.check(job)\n\n\n# Whole scenarios",
  "new_string": "    assert env.admin.job(job)[\"status\"] is Status.SUCCEEDED\n    env.check(job)\n\n\ndef test_a_malformed_last_message_is_committed_too(env):\n    \"\"\"With no message after it, only its own commit moves the group past it, so a restarted\n    worker does not read it again.\"\"\"\n    env.queue.messages.append(b\"not a job id\")\n    assert env.serve(env.worker(\"A\")) == Served(malformed=1)\n    assert env.queue.committed[\"workers\"] == 1\n    assert env.serve(env.worker(\"B\")) == Served()\n\n\n# Whole scenarios"
}
```

## 325. Assistant — 2026-10-23T12:37:11.681Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -m pytest tests/test_jobs_reconciler.py tests/test_jobs_queue.py -q -k \"last_attempt_too or malformed_last\" 2>&1 | tail -2 && env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python tests/mutation_check.py --only exhaust-token malformed-commit --timeout 300 2>&1 | tail -4",
  "description": "Run the two new tests and re-check the two survivors",
  "timeout": 600000
}
```

## 326. User — 2026-10-23T12:37:13.207Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_reconciler.py has been updated successfully.
```

## 327. User — 2026-10-23T12:37:14.334Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/test_jobs_queue.py has been updated successfully.
```

## 328. User — 2026-10-23T12:37:53.759Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
2 passed, 61 deselected, 1 warning in 0.23s
baseline: exit 0 in 30.1 s
caught    exhaust-token (2.9 s)  FAILED tests/test_jobs_reconciler.py::test_a_stale_token_is_refused_on_the_last_attempt_too[sqlite]
caught    malformed-commit (2.4 s)  FAILED tests/test_jobs_queue.py::test_a_malformed_last_message_is_committed_too[sqlite]
2 of 2 caught; {'caught': 2, 'survived': 0, 'error': 0, 'skipped': 0}
```

## 329. Assistant — 2026-10-23T12:37:58.973Z

Both new tests pass on the real code and catch their mutations. Next is revalidation, starting with the full offline suite, Spark tests included:

## 330. Assistant — 2026-10-23T12:37:59.961Z

### Tool call: Bash

```
{
  "command": "env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python -m pytest -q -p no:cacheprovider 2>&1 | tail -6",
  "description": "Run the full offline test suite",
  "timeout": 1200000
}
```

## 331. User — 2026-10-23T12:40:28.418Z

### Tool result

```
ERROR tests/test_spark_equivalence.py::test_pairing_refuses_leverages_other_than_1x_and_2x
ERROR tests/test_spark_equivalence.py::test_duplicated_leverage_row_breaks_pairing
ERROR tests/test_verify.py::test_clean_run_has_no_mismatches - AssertionError...
ERROR tests/test_verify.py::test_altered_summary_value_is_reported - Assertio...
ERROR tests/test_verify.py::test_changed_input_file_stops_verification - Asse...
17 failed, 383 passed, 16 skipped, 884 warnings, 73 errors in 146.49s (0:02:26)
```

## 332. Assistant — 2026-10-23T12:40:30.966Z

Most Spark tests errored (17 failed, 73 errors). Before assuming anything, I'm looking at the first error in detail:

## 333. Assistant — 2026-10-23T12:40:32.591Z

### Tool call: Bash

```
{
  "command": "env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_verify.py -x 2>&1 | grep -v '^\\s*$' | grep -E -i 'error|exception|assert|java|spark|python' | head -30",
  "description": "Show the first Spark test error's details",
  "timeout": 300000
}
```

## 334. User — 2026-10-23T12:40:45.750Z

### Tool result

```
==================================== ERRORS ====================================
______________ ERROR at setup of test_clean_run_has_no_mismatches ______________
spark = <pyspark.sql.session.SparkSession object at 0x120223aa0>
    def run(spark, tmp_path_factory):
>       assert spark_pipeline.main(["--windows", str(windows), "--out-root", str(root / "out"), "--run-id", "r1"]) == 0
E       AssertionError: assert 2 == 0
E        +    where <function main at 0x130338fe0> = spark_pipeline.main
tests/test_verify.py:32: AssertionError
Using Spark's default log4j profile: org/apache/spark/log4j2-defaults.properties
To adjust logging level use sc.setLogLevel(newLevel). For SparkR, use setLogLevel(newLevel).
26/10/23 07:40:35 WARN NativeCodeLoader: Unable to load native-hadoop library for your platform... using builtin-java classes where applicable
[Stage 0:>                                                          (0 + 1) / 1]                                                                                [Stage 3:>                                                          (0 + 2) / 2]                                                                                [Stage 26:>                                                         (0 + 1) / 1]26/10/23 07:40:45 ERROR Utils: Aborting task
org.apache.spark.api.python.PythonException: [PYTHON_EXCEPTION] An exception was thrown from the Python worker: Traceback (most recent call last):
  File "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.venv/lib/python3.12/site-packages/pyspark/python/lib/pyspark.zip/pyspark/worker.py", line 3602, in main
  File "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.venv/lib/python3.12/site-packages/pyspark/python/lib/pyspark.zip/pyspark/worker.py", line 2496, in read_udfs
  File "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.venv/lib/python3.12/site-packages/pyspark/python/lib/pyspark.zip/pyspark/worker.py", line 1079, in read_single_udf
  File "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.venv/lib/python3.12/site-packages/pyspark/python/lib/pyspark.zip/pyspark/worker_util.py", line 73, in read_command
  File "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.venv/lib/python3.12/site-packages/pyspark/python/lib/pyspark.zip/pyspark/serializers.py", line 171, in _read_with_length
  File "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/.venv/lib/python3.12/site-packages/pyspark/python/lib/pyspark.zip/pyspark/serializers.py", line 454, in loads
ModuleNotFoundError: No module named 'etf_risk'
	at org.apache.spark.api.python.BasePythonRunner$ReaderIterator.handlePythonException(PythonRunner.scala:665)
	at org.apache.spark.sql.execution.python.PythonArrowOutput$$anon$1.read(PythonArrowOutput.scala:142)
	at org.apache.spark.api.python.BasePythonRunner$ReaderIterator.hasNext(PythonRunner.scala:602)
	at org.apache.spark.InterruptibleIterator.hasNext(InterruptibleIterator.scala:37)
	at org.apache.spark.sql.catalyst.expressions.GeneratedClass$GeneratedIteratorForCodegenStage6.sort_addToSorter_0$(Unknown Source)
	at org.apache.spark.sql.catalyst.expressions.GeneratedClass$GeneratedIteratorForCodegenStage6.processNext(Unknown Source)
	at org.apache.spark.sql.execution.BufferedRowIterator.hasNext(BufferedRowIterator.java:44)
	at org.apache.spark.sql.execution.WholeStageCodegenEvaluatorFactory$WholeStageCodegenPartitionEvaluator$$anon$1.hasNext(WholeStageCodegenEvaluatorFactory.scala:50)
	at org.apache.spark.sql.execution.datasources.FileFormatDataWriter.writeWithIterator(FileFormatDataWriter.scala:110)
	at org.apache.spark.sql.execution.datasources.FileFormatWriter$.$anonfun$executeTask$1(FileFormatWriter.scala:415)
```

## 335. Assistant — 2026-10-23T12:40:54.853Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/mutation_check.py",
  "old_string": "    \"\"\"The job tests in a new process group; the group is killed on timeout.\"\"\"\n    env = {k: v for k, v in os.environ.items() if k != \"VIRTUAL_ENV\"}",
  "new_string": "    \"\"\"The job tests in a new process group; the group is killed on timeout. The scratch\n    environment comes first on PATH, as under uv run, so any python3 started below is its.\"\"\"\n    env = {k: v for k, v in os.environ.items() if k != \"VIRTUAL_ENV\"}\n    env[\"PATH\"] = f\"{scratch / '.venv' / 'bin'}{os.pathsep}{env.get('PATH', '')}\""
}
```

## 336. Assistant — 2026-10-23T12:40:55.958Z

### Tool call: Bash

```
{
  "command": "env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP uv run --frozen --group measure --group plots --group jobs pytest -q -p no:cacheprovider 2>&1 | tail -4",
  "description": "Run the full offline suite through uv run",
  "timeout": 1200000
}
```

## 337. User — 2026-10-23T12:40:57.503Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/tests/mutation_check.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 338. User — 2026-10-23T12:47:23.285Z

### Tool result

```
    days = mcal.get_calendar("NYSE").valid_days(start, pd.Timestamp(start) + pd.Timedelta(days=3 * n + 10))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
473 passed, 16 skipped, 884 warnings in 383.53s (0:06:23)
```

## 339. Assistant — 2026-10-23T12:47:39.531Z

### Tool call: Bash

```
{
  "command": "uv run --frozen python -m etf_risk.services others; .venv/bin/python - <<'EOF'\nimport socket\nfor port in (3307, 9094):\n    s = socket.socket(); s.settimeout(1)\n    busy = s.connect_ex((\"127.0.0.1\", port)) == 0\n    s.close()\n    print(f\"port {port}: {'in use' if busy else 'free'}\")\nEOF\ndocker compose -f docker/compose.yaml ps -a --format '{{.Service}} {{.State}}' 2>&1 | head -5; echo \"(end of this project's containers)\"",
  "description": "Count other containers and check the service ports"
}
```

## 340. User — 2026-10-23T12:47:41.575Z

### Tool result

```
4 running container(s) outside the etf-risk-jobs project
port 3307: free
port 9094: free
(end of this project's containers)
```

## 341. Assistant — 2026-10-23T12:47:45.424Z

### Tool call: Bash

```
{
  "command": "docker compose -f docker/compose.yaml up -d --wait mysql kafka 2>&1 | tail -4 && uv run --frozen --group jobs python -m etf_risk.services ready mysql kafka",
  "description": "Start MySQL and Kafka and wait until both are usable",
  "timeout": 300000
}
```

## 342. User — 2026-10-23T12:47:58.810Z

### Tool result

```
 Container etf-risk-jobs-mysql-1  Waiting
 Container etf-risk-jobs-kafka-1  Waiting
 Container etf-risk-jobs-kafka-1  Healthy
 Container etf-risk-jobs-mysql-1  Healthy
mysql: ready after 0.2 s
kafka: ready after 0.2 s
```

## 343. Assistant — 2026-10-23T12:48:02.032Z

### Tool call: Bash

```
{
  "command": "ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 uv run --frozen --group jobs pytest tests/test_jobs_store.py tests/test_jobs_worker.py tests/test_jobs_queue.py tests/test_jobs_reconciler.py tests/test_jobs_kafka.py tests/test_jobs_mysql.py -q -p no:cacheprovider 2>&1 | tail -3; uv run --frozen python -m etf_risk.services peaks mysql kafka",
  "description": "Run the job suite against MySQL and Kafka, then read peaks",
  "timeout": 1200000
}
```

## 344. User — 2026-10-23T12:49:03.749Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
385 passed, 1 warning in 58.98s
mysql: memory.peak 332 MiB of 512 MiB (65%) (cgroup, includes page cache)
kafka: memory.peak 355 MiB of 640 MiB (56%) (cgroup, includes page cache)
```

## 345. Assistant — 2026-10-23T12:49:14.385Z

### Tool call: Bash

```
{
  "command": "docker compose -f docker/compose.yaml down -v 2>&1 | tail -1 && docker compose -f docker/compose.yaml up -d --wait mysql kafka 2>&1 | tail -1 && uv run --frozen --group jobs python -m etf_risk.services ready mysql kafka",
  "description": "Recreate fresh MySQL and Kafka containers",
  "timeout": 300000
}
```

## 346. User — 2026-10-23T12:49:30.325Z

### Tool result

```
 Network etf-risk-jobs_default  Removed
 Container etf-risk-jobs-mysql-1  Healthy
mysql: ready after 0.1 s
kafka: ready after 0.1 s
```

## 347. Assistant — 2026-10-23T12:49:34.164Z

### Tool call: Bash

```
{
  "command": "OUT=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-live-1; mkdir -p $OUT && ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 .venv/bin/python tests/mutation_check.py --timeout 600 --out $OUT > $OUT/console.txt 2>&1; echo \"exit $?\" >> $OUT/console.txt; uv run --frozen python -m etf_risk.services peaks mysql kafka >> $OUT/console.txt 2>&1",
  "description": "Run all mutation checks against MySQL and Kafka",
  "run_in_background": true
}
```

## 348. User — 2026-10-23T12:49:34.642Z

### Tool result

```
Command running in background with ID: b99wvr9ym. Output is being written to: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/tasks/b99wvr9ym.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need a line it prints before you can go on, such as a server's ready line or port.
```

## 349. Assistant — 2026-10-23T12:49:50.823Z

### Tool call: Bash

```
{
  "command": "grep -n \"Status on 2026-10-23\" -A 32 docs/job-queue.md | head -36",
  "description": "Show the job-queue status block"
}
```

## 350. User — 2026-10-23T12:49:51.350Z

### Tool result

```
170:- Status on 2026-10-23:
171-  - **Offline:** 200 passed, and the 17 tests that need MySQL, Kafka or confluent-kafka
172-    were skipped.
173-  - **With Kafka 4.3.1** (the job table on SQLite): 210 passed, and the 7 tests that
174-    need MySQL were skipped.
175-  - **With MySQL 8.4.13 and Kafka 4.3.1, on the committed revision e2806bd:** 379
176-    passed, none failed or skipped, in one run on fresh containers (162 cases on each
177-    store). An earlier revision, before the job-id validation, had 353 passed.
178-  - **The whole suite:** 411 passed and 15 skipped. That run came before the bounded
179-    retries, the job-id validation and the test fixes; the rest of the suite does not
180-    use these files.
181-  - **Mutation checks:** 22 guards and settings were broken on purpose, one at a time,
182-    in 25 test runs: three were run both offline and against Kafka. Each run had a
183-    timeout. The 22 include 4 for the job-id format and range. Tests failed in all 25
184-    runs; none ran into the timeout. Before the fixes, three ran until it:
185-    - a claim that keeps the publication, through `serve()`'s unbounded retries;
186-    - the grace boundary off by one, through a test that waited for the publisher to
187-      stop the reconciler's loop;
188-    - the rewind removed, through a test that waited for a failing claim to come back.
189-  - **Memory:** spec §11 records the peaks. MySQL reached 511 of its 512 MiB over about
190-    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That
191-    is limited headroom, not evidence that longer runs stay within the limit.
192-
193-## Code provenance
194-
195-Every run record identifies the job package's code. `provenance.code_state()` hashes every
196-Python module and SQL schema under `src/etf_risk/`, including `jobs/` and its schema files,
197-keyed by package-relative path, for example `jobs/store.py`. Records written before
198-2026-10-23 hash only the top-level modules. All of `jobs/` was written with Claude Code
199-(Opus 5.5), as each module's docstring says. It came in through two PRs:
200-
201-| Module | Commits | PR | Verified by |
202-|---|---|---|---|
```

## 351. Assistant — 2026-10-23T12:49:55.818Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "- Status on 2026-10-23:\n  - **Offline:** 200 passed, and the 17 tests that need MySQL, Kafka or confluent-kafka\n    were skipped.",
  "new_string": "- Status when this queue was merged (PR #8, revision e2806bd), on 2026-10-23. At that point\n  the clients were installed with `uv run --with`, not from the lock:\n  - **Offline:** 200 passed, and the 17 tests that need MySQL, Kafka or confluent-kafka\n    were skipped."
}
```

## 352. User — 2026-10-23T12:49:56.955Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 353. Assistant — 2026-10-23T12:50:00.783Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "  - **Mutation checks:** 22 guards and settings were broken on purpose, one at a time,\n    in 25 test runs: three were run both offline and against Kafka. Each run had a\n    timeout.",
  "new_string": "  - **Mutation checks:** 22 guards and settings were broken by hand, one at a time, in 25\n    test runs: three were run both offline and against Kafka. They were not recorded as a\n    list; `tests/mutation_check.py` rebuilds the set from these notes. Each run had a\n    timeout."
}
```

## 354. User — 2026-10-23T12:50:01.883Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 355. Assistant — 2026-10-23T12:50:04.322Z

### Tool call: Bash

```
{
  "command": "git diff docs/spec.md docs/job-table.md | head -80",
  "description": "Review the spec and job-table diffs"
}
```

## 356. User — 2026-10-23T12:50:04.948Z

### Tool result

````
diff --git a/docs/job-table.md b/docs/job-table.md
index 901d226..7e7f83d 100644
--- a/docs/job-table.md
+++ b/docs/job-table.md
@@ -14,7 +14,7 @@ A claim tries two conditional updates of the job's row, in one transaction:
 ```sql
 -- 1. a queued job
 UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1, attempt_token = :token,
-       lease_expires_at = :lease_expires_at, version = version + 1, updated_at = :now
+       lease_expires_at = :lease_expires_at, published_at = NULL, version = version + 1, updated_at = :now
  WHERE job_id = :job_id AND status = 'queued';
 -- 2. only if 1 matched no row: a running job whose lease has expired, with attempts left
 UPDATE jobs SET ... (the same)
@@ -72,9 +72,9 @@ row first decides, and the other then finds the job succeeded, or a token that i
 
 ## Transactions
 
-- Every operation is one transaction. Apart from `submit`, each writes both tables: the
-  update of `jobs` decides, and the write to `job_attempts` records; that write must touch
-  exactly one row, or the store raises and both tables roll back.
+- Every operation is one transaction. Apart from `submit` and `mark_published`, each writes
+  both tables: the update of `jobs` decides, and the write to `job_attempts` records; that
+  write must touch exactly one row, or the store raises and both tables roll back.
 - Any exception rolls the transaction back, including a simulated crash. The tests raise at
   each gap between two statements (`FAULT_POINTS`) and check both tables afterwards.
 - Every transaction locks the `jobs` row before any `job_attempts` row, and none spans a
@@ -94,14 +94,23 @@ row first decides, and the other then finds the job succeeded, or a token that i
 - [`tests/test_jobs_mysql.py`](../tests/test_jobs_mysql.py) checks the MySQL adapter offline
   and, against a server, the InnoDB behaviour the SQL relies on (setup in its docstring and in
   [`docker/compose.yaml`](../docker/compose.yaml)).
-- Status on 2026-10-22: with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set,
-  all 222 cases pass, in five runs in a row; without the URL, 114 pass and the 7 tests that
-  need a server are skipped. Breaking any one of eleven guards and checks on purpose (the
-  token, lease and attempts-left conditions, the rollback, the one-row check on
-  `job_attempts` writes, the `version` bump, conflict detection, the output folder check)
-  makes at least one test fail. On top of main at e55f76b (after the caching experiment),
-  the job tests give the same counts and the whole suite passes (350 passed, 7 skipped).
-  The MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget
-  (cgroup `memory.peak`, which includes page cache).
+- [`tests/mutation_check.py`](../tests/mutation_check.py) breaks the guards and checks on
+  purpose, one at a time, in a scratch copy of the repository, and expects the job tests to
+  fail within a timeout. It covers the token, lease and attempts-left conditions, the
+  rollback, the one-row check on `job_attempts` writes, the `version` bump, conflict
+  detection, the output folder check, and the queue's guards in
+  [job-queue.md](job-queue.md).
+- Status when this table was merged (PR #7), on 2026-10-22:
+  - with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set, all 222 cases
+    passed, in five runs in a row;
+  - without the URL, 114 passed and the 7 tests that need a server were skipped;
+  - breaking any one of eleven guards and checks by hand made at least one test fail.
+    Those mutations were not recorded as a list; `tests/mutation_check.py` rebuilds them
+    from this description;
+  - the MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget
+    (cgroup `memory.peak`, which includes page cache).
+
+  The current status of the job tests, with the Kafka delivery of PR #8, is in
+  [job-queue.md](job-queue.md).
 
 *AI contribution: written with Claude Code (Opus 5.5).*
diff --git a/docs/spec.md b/docs/spec.md
index e64fa75..153f8a3 100644
--- a/docs/spec.md
+++ b/docs/spec.md
@@ -165,7 +165,9 @@ src/etf_risk/
                                   optional caches (--cache)
   verify.py          implemented  sample check against an independent Python slicing of each window
   measure.py         implemented  fresh-process timed runs, process-tree memory sampling, stop rule
-  provenance.py      implemented  code state for every record (commit, worktree state, SHA-256 of sources and uv.lock); repo-relative paths
+  provenance.py      implemented  code state for every record (commit, worktree state, SHA-256 of uv.lock and of every module
+                                  and SQL schema under src/etf_risk/, jobs/ included, by package-relative path, since
+                                  2026-10-23; earlier records hash the top-level modules only); repo-relative paths
   plans.py           implemented  a run's final execution plans, AQE partition counts, descriptions and scan nodes
                                   (spark_pipeline --record-plans)
   pandas_pipeline.py implemented  the pipeline's results in one process with pandas, without Spark (the pandas baseline)
@@ -173,6 +175,8 @@ src/etf_risk/
   jobs/              implemented  optional job queue (§11): job table schema (MySQL, SQLite mirror), guarded state
                                   transitions (store.py), MySQL and Kafka adapters, worker and its consume loop,
                                   reconciler, simulated pipeline and in-memory queue
+  services.py        implemented  the extension's Compose services from this machine: readiness (a MySQL login, Kafka
+                                  metadata), cgroup memory peaks, and a count of other projects' containers
````

## 357. Assistant — 2026-10-23T12:50:08.969Z

I dropped one historical fact from `job-table.md` in the rewrite: the whole-suite count on top of e55f76b. Restoring it:

## 358. Assistant — 2026-10-23T12:50:10.411Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md",
  "old_string": "    Those mutations were not recorded as a list; `tests/mutation_check.py` rebuilds them\n    from this description;\n  - the MySQL container's memory peak",
  "new_string": "    Those mutations were not recorded as a list; `tests/mutation_check.py` rebuilds them\n    from this description;\n  - on top of main at e55f76b (after the caching experiment), the job tests gave the same\n    counts and the whole suite passed (350 passed, 7 skipped);\n  - the MySQL container's memory peak"
}
```

## 359. User — 2026-10-23T12:50:11.524Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-table.md has been updated successfully.
```

## 360. Assistant — 2026-10-23T12:50:18.597Z

The live mutation run is still going. Once it finishes, I'll fill in the revalidation numbers, commit M1 in three commits, remove the two merged worktrees and write the milestone report.

## 361. Assistant — 2026-10-23T12:50:19.164Z

### Tool call: Bash

```
{
  "command": "git diff --stat; git status --short | grep '^??'",
  "description": "Show what M1 will commit"
}
```

## 362. User — 2026-10-23T12:50:19.803Z

### Tool result

```
 .gitignore                    |   5 +-
 README.md                     |  32 ++++++++++++
 docker/compose.yaml           |   2 +-
 docs/job-queue.md             |  54 ++++++++++++++++---
 docs/job-table.md             |  37 ++++++++-----
 docs/spec.md                  |  11 ++--
 pyproject.toml                |   4 ++
 src/etf_risk/jobs/kafka.py    |   5 +-
 src/etf_risk/provenance.py    |  17 ++++--
 tests/test_jobs_kafka.py      |   2 +-
 tests/test_jobs_mysql.py      |   2 +-
 tests/test_jobs_queue.py      |  37 +++++++++++++
 tests/test_jobs_reconciler.py |  14 +++++
 tests/test_provenance.py      |  32 +++++++++++-
 uv.lock                       | 117 ++++++++++++++++++++++++++++++++++++++++++
 15 files changed, 338 insertions(+), 33 deletions(-)
?? src/etf_risk/services.py
?? tests/mutation_check.py
?? tests/test_services.py
```

## 363. Assistant — 2026-10-23T12:50:33.443Z

### Tool call: Bash

```
{
  "command": "git add -- .gitignore pyproject.toml uv.lock src/etf_risk/provenance.py tests/test_provenance.py docker/compose.yaml src/etf_risk/jobs/kafka.py tests/test_jobs_kafka.py tests/test_jobs_mysql.py && git commit -q -F - <<'EOF'\nHash the jobs subpackage in run records and lock the job queue's clients\n\n- provenance.code_state() now hashes every Python module and SQL schema\n  under src/etf_risk/, subpackages included, keyed by package-relative\n  path. Before, it hashed src/etf_risk/*.py only, so no record identified\n  jobs/ or its schema files, and a recursive glob keyed by file name\n  would have collided on __init__.py. Top-level modules keep the keys\n  earlier records used (\"model.py\"); new keys look like jobs/store.py.\n  Two tests: every .py/.sql file, walked independently, is hashed under\n  a unique key; the top-level entries equal what the old code recorded.\n- A `jobs` dependency group pins PyMySQL 1.1.1 (with the rsa extra) and\n  confluent-kafka 2.16.0, the versions the live tests used through\n  `uv run --with`. uv.lock adds exactly three packages (confluent-kafka\n  2.16.0, pymysql 1.1.1, cryptography 50.0.2) and changes no existing\n  version; `uv lock --check` passes. The Compose file's comment, the\n  Kafka adapter's docstring and the test docstrings now use\n  `uv run --group jobs`.\n- .gitignore: `/data` instead of `/data/`, so a Git worktree's `data`\n  symlink to the main checkout's data/ is ignored as well.\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\nEOF\ngit log -1 --format='%h %s' && git show --stat --format= HEAD | tail -1",
  "description": "Commit the provenance and dependency changes"
}
```

## 364. User — 2026-10-23T12:50:34.235Z

### Tool result

```
74c8481 Hash the jobs subpackage in run records and lock the job queue's clients
 9 files changed, 175 insertions(+), 11 deletions(-)
```

## 365. Assistant — 2026-10-23T12:50:41.905Z

### Tool call: Bash

```
{
  "command": "git add -- src/etf_risk/services.py tests/test_services.py tests/mutation_check.py tests/test_jobs_queue.py tests/test_jobs_reconciler.py && git commit -q -F - <<'EOF'\nAdd a services helper, reproducible mutation checks and three job tests\n\n- etf_risk.services, for the extension's Compose services:\n  - `ready mysql kafka` waits until a MySQL login and SELECT 1 succeed\n    and the broker answers a metadata request. The Compose healthchecks\n    answer earlier, as soon as the ports are open.\n  - `peaks` reads each container's cgroup memory.peak against its limit.\n  - `others` counts the running containers of other Compose projects,\n    without naming them, since they share Docker's VM memory.\n  Tested offline with a fake docker on PATH and a fake clock.\n- tests/mutation_check.py breaks one guard or setting at a time in a\n  scratch copy of the repository and expects the job tests to fail\n  within a timeout. A timeout or a collection error counts as an error,\n  not a catch. It has 31 mutations: the store's guards, the claim's\n  publication reset and version bump, the publication's version guard,\n  the worker's acknowledgement, rewind, bounded retries and\n  malformed-message commit, the job-id checks, the grace period, and\n  five Kafka settings. Conflict detection needs MySQL. The list is\n  rebuilt from the notes of the earlier hand-made checks, which kept no\n  list; it is not claimed to be the same set.\n- Its first run found two gaps, now covered by tests:\n  - test_a_stale_token_is_refused_on_the_last_attempt_too: without\n    _exhaust's token guard, a stale token failed the job through the\n    new holder's last attempt. Only the one-row check turned this into\n    an exception rather than a clean refusal.\n  - test_a_malformed_last_message_is_committed_too: the existing test\n    put a job after the malformed message, and its commit hid a\n    missing one.\n- test_the_job_9_timeline follows docs/job-queue.md's table row by row.\n  The test the doc named started from a confirmed publication, so it\n  never covered the lost confirmation or the pass at 30 s.\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\nEOF\ngit log -1 --format='%h %s' && git show --stat --format= HEAD | tail -1",
  "description": "Commit the helper, mutation checks and new tests"
}
```

## 366. User — 2026-10-23T12:50:42.500Z

### Tool result

```
9f347d1 Add a services helper, reproducible mutation checks and three job tests
 5 files changed, 550 insertions(+)
```

## 367. Assistant — 2026-10-23T12:50:49.946Z

### Tool call: Bash

```
{
  "command": "for w in job-queue job-table; do p=~/leveraged-etf-risk-analytics/.claude/worktrees/$w; echo \"== $w: branch $(git -C $p branch --show-current), HEAD $(git -C $p rev-parse --short HEAD)\"; git -C $p status --short | head -3; echo \"ignored:\"; git -C $p status --ignored --short | grep '^!!' | head -10; done",
  "description": "Show tracked and ignored content in the two merged worktrees"
}
```

## 368. User — 2026-10-23T12:50:50.797Z

### Tool result

```
== job-queue: branch feature/job-queue, HEAD cd72957
ignored:
!! .claude/hooks/__pycache__/
!! .venv/
!! analysis/__pycache__/
!! src/etf_risk/__pycache__/
!! src/etf_risk/jobs/__pycache__/
!! tests/__pycache__/
== job-table: branch feature/job-table, HEAD 6cfd971
ignored:
!! .claude/hooks/__pycache__/
!! .pytest_cache/
!! .venv/
!! analysis/__pycache__/
!! src/etf_risk/__pycache__/
!! src/etf_risk/jobs/__pycache__/
!! tests/__pycache__/
```

## 369. Assistant — 2026-10-23T12:50:52.781Z

The two merged worktrees hold only caches and virtual environments, and both of their commits are in `main`. Removing them; their branches stay:

## 370. Assistant — 2026-10-23T12:50:54.366Z

### Tool call: Bash

```
{
  "command": "git merge-base --is-ancestor cd72957 main && git merge-base --is-ancestor 6cfd971 main && git worktree remove ~/leveraged-etf-risk-analytics/.claude/worktrees/job-queue && git worktree remove ~/leveraged-etf-risk-analytics/.claude/worktrees/job-table && git worktree list && git branch --list 'feature/job-*'",
  "description": "Remove the two merged worktrees after confirming the merge"
}
```

## 371. User — 2026-10-23T12:50:56.929Z

### Tool result

```
~/leveraged-etf-risk-analytics                                       97c35f3 [fix/measure-process-kinds]
~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline  9f347d1 [feature/extension-baseline]
  feature/job-queue
  feature/job-table
```

## 372. Assistant — 2026-10-23T12:51:04.615Z

M1's code is committed (`74c8481`, `9f347d1`) and the merged worktrees are removed. The live mutation run against MySQL and Kafka is still going in the background. When it finishes, I'll add its numbers to the docs, make the last commit and send you the M1 report with the two M2 timing corrections.

## 373. User — 2026-10-23T12:58:09.358Z

<task-notification>
<task-id>b99wvr9ym</task-id>
<tool-use-id>toolu_01UpnMqnLuBh3bzcAaDSKcDE</tool-use-id>
<output-file>/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/tasks/b99wvr9ym.output</output-file>
<status>completed</status>
<summary>Background command "Run all mutation checks against MySQL and Kafka" completed (exit code 0)</summary>
</task-notification>

## 374. Assistant — 2026-10-23T12:58:13.395Z

### Tool call: Bash

```
{
  "command": "cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-live-1/console.txt",
  "description": "Show the live mutation run's results and peaks"
}
```

## 375. User — 2026-10-23T12:58:13.854Z

### Tool result

```
baseline: exit 0 in 87.5 s
caught    renew-token (10.3 s)  FAILED tests/test_jobs_store.py::test_a_stale_worker_is_fenced_off_after_a_takeover[sqlite]
caught    accept-token (1.3 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-running-foreign_token]
caught    fail-token (7.5 s)  FAILED tests/test_jobs_store.py::test_a_stale_worker_is_fenced_off_after_a_takeover[sqlite]
caught    takeover-lease (1.0 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-running-claim]
caught    takeover-attempts-left (1.1 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-expired_last-claim]
caught    requeue-token (19.0 s)  FAILED tests/test_jobs_reconciler.py::test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too[sqlite]
caught    requeue-lease (1.2 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-running-requeue_expired]
caught    exhaust-token (18.2 s)  FAILED tests/test_jobs_reconciler.py::test_a_stale_token_is_refused_on_the_last_attempt_too[sqlite]
caught    claim-keeps-publication (1.2 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-published-claim]
caught    claim-version-bump (8.8 s)  FAILED tests/test_jobs_store.py::test_the_same_acceptance_twice_at_once_accepts_one_result[sqlite]
caught    publication-version (18.8 s)  FAILED tests/test_jobs_reconciler.py::test_a_confirmation_after_the_job_moved_on_is_not_recorded[sqlite]
caught    accept-repeat-token (1.2 s)  FAILED tests/test_jobs_store.py::test_transition_matrix[sqlite-succeeded-foreign_token]
caught    rollback (8.8 s)  FAILED tests/test_jobs_store.py::test_acceptance_repeated_after_a_failed_commit[sqlite-commit-not-applied]
caught    one-row-check (10.6 s)  FAILED tests/test_jobs_store.py::test_a_bookkeeping_write_that_misses_its_row_rolls_back_the_job_update[sqlite]
caught    conflict-detection (48.4 s)  FAILED tests/test_jobs_mysql.py::test_lock_conflicts_are_recognised_by_their_error_codes
caught    output-folder-check (14.8 s)  FAILED tests/test_jobs_worker.py::test_an_existing_output_folder_is_never_written_into[sqlite]
caught    acknowledge-after-claim (11.9 s)  FAILED tests/test_jobs_worker.py::test_a_delivery_runs_the_job_once_and_accepts_its_result[sqlite]
caught    rewind (14.8 s)  FAILED tests/test_jobs_queue.py::test_an_error_before_the_acknowledgement_rewinds_and_the_job_runs_on_the_retry[sqlite]
caught    bounded-retries (14.8 s)  FAILED tests/test_jobs_queue.py::test_a_persistent_error_before_the_acknowledgement_is_raised_after_the_retries[sqlite]
caught    malformed-commit (16.6 s)  FAILED tests/test_jobs_queue.py::test_a_malformed_last_message_is_committed_too[sqlite]
caught    job-id-leading-zero (15.0 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[0-None]
caught    job-id-format (14.8 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[-None]
caught    job-id-length (14.4 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[5000-digits]
caught    job-id-range (15.3 s)  FAILED tests/test_jobs_queue.py::test_a_delivery_carries_a_valid_job_id_or_none[9223372036854775808-None]
caught    grace-boundary (16.2 s)  FAILED tests/test_jobs_queue.py::test_a_lost_confirmation_leads_to_a_duplicate_that_is_refused[sqlite]
caught    grace-for-requeued (15.6 s)  FAILED tests/test_jobs_queue.py::test_an_error_after_the_acknowledgement_leaves_the_job_to_its_lease[sqlite]
caught    auto-commit (20.5 s)  FAILED tests/test_jobs_kafka.py::test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message
caught    offset-store (20.3 s)  FAILED tests/test_jobs_kafka.py::test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message
caught    offset-reset (20.1 s)  FAILED tests/test_jobs_kafka.py::test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message
caught    acks (20.0 s)  FAILED tests/test_jobs_kafka.py::test_the_producer_waits_for_the_broker_and_is_idempotent
caught    idempotence (20.1 s)  FAILED tests/test_jobs_kafka.py::test_the_producer_waits_for_the_broker_and_is_idempotent
31 of 31 caught; {'caught': 31, 'survived': 0, 'error': 0, 'skipped': 0}
exit 0
mysql: memory.peak 441 MiB of 512 MiB (86%) (cgroup, includes page cache)
kafka: memory.peak 380 MiB of 640 MiB (59%) (cgroup, includes page cache)
```

## 376. Assistant — 2026-10-23T12:58:25.536Z

### Tool call: Bash

```
{
  "command": "docker compose -f docker/compose.yaml down -v 2>&1 | tail -1; env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP uv run --frozen --group jobs pytest tests/test_jobs_store.py tests/test_jobs_worker.py tests/test_jobs_queue.py tests/test_jobs_reconciler.py tests/test_jobs_kafka.py tests/test_jobs_mysql.py -q -p no:cacheprovider 2>&1 | tail -1",
  "description": "Stop the services and count the offline job tests",
  "timeout": 600000
}
```

## 377. User — 2026-10-23T12:58:34.558Z

### Tool result

```
 Network etf-risk-jobs_default  Removed
204 passed, 16 skipped, 1 warning in 4.71s
```

## 378. Assistant — 2026-10-23T12:58:39.023Z

### Tool call: Bash

```
{
  "command": "OUT=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/d50bcd16-34a8-45d0-8956-1e2da5d4b461/scratchpad/mutations-offline-2; mkdir -p $OUT && env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python tests/mutation_check.py --timeout 300 --out $OUT 2>&1 | tail -3; .venv/bin/python -c \"import json,sys; r=json.load(open('$OUT/mutations.json')); c=r['code']; print('code:', c['git_commit'][:7], 'clean' if c['git_worktree_clean'] else 'DIRTY', '| hashed files:', len(c['source_sha256']), '| jobs/ keys:', sum(k.startswith('jobs/') for k in c['source_sha256']))\"",
  "description": "Run all offline mutation checks on the committed code",
  "timeout": 1200000
}
```

## 379. User — 2026-10-23T13:00:16.587Z

### Tool result

```
caught    acks (2.9 s)  FAILED tests/test_jobs_kafka.py::test_the_producer_waits_for_the_broker_and_is_idempotent
caught    idempotence (3.0 s)  FAILED tests/test_jobs_kafka.py::test_the_producer_waits_for_the_broker_and_is_idempotent
30 of 30 caught; {'caught': 30, 'survived': 0, 'error': 0, 'skipped': 1}
code: 9f347d1 clean | hashed files: 24 | jobs/ keys: 10
```

## 380. Assistant — 2026-10-23T13:00:33.845Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md",
  "old_string": "    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That\n    is limited headroom, not evidence that longer runs stay within the limit.\n\n## Code provenance",
  "new_string": "    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That\n    is limited headroom, not evidence that longer runs stay within the limit.\n- Revalidation on 2026-10-23, with the clients from the lock (`--group jobs`), on revision\n  9f347d1 of `feature/extension-baseline`:\n  - **Offline:** 204 passed, and the 16 tests that need MySQL or Kafka were skipped. That\n    is three new tests, plus one that needs only confluent-kafka and now runs.\n  - **With MySQL 8.4.13 and Kafka 4.3.1** on fresh containers: 385 passed, none failed or\n    skipped, in 59 s. That is the 379 cases of e2806bd plus the three new tests on both\n    stores.\n  - **The whole suite** (all dependency groups, through `uv run`): 473 passed and 16\n    skipped.\n  - **Mutation checks** (`tests/mutation_check.py`, 31 mutations):\n    - **Offline:** 30 of 30 caught; conflict detection was skipped, since it needs MySQL.\n    - **Against MySQL and Kafka:** 31 of 31 caught, on the same code just before it was\n      committed. No run reached its timeout.\n    - **Gaps found on the way:** the first offline run found two mutations that no test\n      caught, the token in `_exhaust` and the commit of a malformed last message. The two\n      tests named above now catch them.\n  - **Memory**, from cgroup `memory.peak`:\n    - after one full run on fresh containers: MySQL 332 MiB (65%), Kafka 355 MiB (56%);\n    - after the mutation session on one fresh pair (one full run plus 31 shorter ones):\n      MySQL 441 MiB (86%), Kafka 380 MiB (59%).\n\n    Four containers of another Compose project were running in Docker's VM at the time, so\n    these are not budget measurements (spec §11 asks for none).\n\n## Code provenance"
}
```

## 381. User — 2026-10-23T13:00:35.012Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline/docs/job-queue.md has been updated successfully.
```

## 382. Assistant — 2026-10-23T13:00:41.328Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python - <<'EOF'\nimport re\nfrom pathlib import Path\nbad = []\nfor doc in (\"README.md\", \"docs/job-queue.md\", \"docs/job-table.md\", \"docs/spec.md\"):\n    base = Path(doc).parent\n    for target in re.findall(r\"\\]\\(([^)#\\s]+)(?:#[^)]*)?\\)\", Path(doc).read_text()):\n        if target.startswith((\"http://\", \"https://\", \"mailto:\")):\n            continue\n        if not (base / target).exists():\n            bad.append((doc, target))\nprint(\"broken links:\", bad or \"none\")\nEOF\ngit diff --stat",
  "description": "Check the edited docs' relative links"
}
```

## 383. User — 2026-10-23T13:00:41.944Z

### Tool result

```
broken links: none
 README.md         | 32 +++++++++++++++++++++++
 docs/job-queue.md | 77 ++++++++++++++++++++++++++++++++++++++++++++++++++-----
 docs/job-table.md | 37 ++++++++++++++++----------
 docs/spec.md      | 11 +++++---
 4 files changed, 135 insertions(+), 22 deletions(-)
```

## 384. Assistant — 2026-10-23T13:00:49.369Z

### Tool call: Bash

```
{
  "command": "git add -- README.md docs/job-queue.md docs/job-table.md docs/spec.md && git commit -q -F - <<'EOF'\nRecord the extension baseline in the job docs, the spec and a README runbook\n\n- README: a runbook for the extension's services, using only commands\n  that exist now: Compose up, `etf_risk.services ready`, the live job\n  tests with `--group jobs`, `peaks`, `others`, the mutation checks, and\n  `down -v`. It covers the `data` symlink in a Git worktree and notes\n  that the worker, reconciler and submit commands come later.\n- docs/job-table.md:\n  - the claim SQL shows `published_at = NULL`;\n  - \"apart from submit\" now also names mark_published;\n  - the status block is dated to PR #7, and says the eleven\n    hand-made mutations were not recorded and are rebuilt by\n    tests/mutation_check.py.\n- docs/job-queue.md:\n  - the job-9 timeline names the test that follows it row by row;\n  - \"What is checked where\" adds the mutation checks and\n    etf_risk.services;\n  - the status block is split into the state at PR #8 and today's\n    revalidation;\n  - a new \"Code provenance\" section records what the run records now\n    hash, and maps each module to its commits, PR and tests.\n- Revalidation, on 9f347d1:\n  - offline job tests: 204 passed, 16 skipped;\n  - against MySQL 8.4.13 and Kafka 4.3.1: 385 passed;\n  - whole suite: 473 passed, 16 skipped;\n  - mutations: 30 of 30 caught offline and 31 of 31 against the\n    services.\n  The memory peaks are recorded as not being budget measurements:\n  another project's containers shared Docker's VM.\n- docs/spec.md: §5 adds services.py, the wider provenance hashing and\n  the new tests; the §9 Environment row adds the `jobs` group.\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\nEOF\ngit log --oneline main..HEAD && git status --short | head -5; echo \"(status end)\"",
  "description": "Commit the docs and list the milestone's commits"
}
```

## 385. User — 2026-10-23T13:00:49.924Z

### Tool result

```
a70c066 Record the extension baseline in the job docs, the spec and a README runbook
9f347d1 Add a services helper, reproducible mutation checks and three job tests
74c8481 Hash the jobs subpackage in run records and lock the job queue's clients
(status end)
```

## 386. Assistant — 2026-10-23T13:00:58.359Z

M1 is complete: three commits on `feature/extension-baseline`, not pushed, and a clean worktree. I'm updating my project notes so the next session knows M1's state.

## 387. Assistant — 2026-10-23T13:01:00.799Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/extension-plan.md",
  "old_string": "[REDACTED:memory]",
  "new_string": "[REDACTED:memory]"
}
```

## 388. User — 2026-10-23T13:01:01.925Z

### Tool result

```
[REDACTED:memory]
```

## 389. Assistant — 2026-10-23T13:01:04.808Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Update the memory index line for the plan"
}
```

## 390. User — 2026-10-23T13:01:05.356Z

### Tool result

```
[REDACTED:memory]
```

## 391. Assistant — 2026-10-23T13:01:27.061Z

M1 is done: three commits on `feature/extension-baseline` (in `.claude/worktrees/extension-baseline`), not pushed. Everything passes, and the mutation checks found two test gaps, now closed.

**What changed**
- **`74c8481` Provenance and dependencies.**
  - Run records now hash every `.py` and `.sql` file under `src/etf_risk/`, including `jobs/` and its schema files, keyed by path inside the package. Older modules keep the keys they had, so earlier records stay comparable.
  - A new `jobs` dependency group pins PyMySQL 1.1.1 and confluent-kafka 2.16.0. The lock only gained three packages, these two plus cryptography 50.0.2, and changed no existing version.
  - All `uv run --with` installs became `--group jobs`.
  - `.gitignore` now uses `/data` (no trailing slash), so a worktree's `data` symlink is ignored too.
- **`9f347d1` Tooling and tests.**
  - `etf_risk.services` waits until MySQL accepts a login and Kafka answers, reads each container's peak memory, and counts other projects' containers without naming them.
  - `tests/mutation_check.py` breaks each of 31 guards and settings on purpose and expects a failing test.
  - Three new tests: one follows the job-9 timeline in `job-queue.md` row by row, and two close the gaps below.
- **`a70c066` Docs.** A README runbook with only commands that exist today; the doc drift found in the audit fixed; a provenance table mapping each `jobs/` module to its commits, PR and tests; and dated status blocks.

**Verification**

| Check | Result |
|---|---|
| Offline job tests | 204 passed, 16 skipped (the MySQL and Kafka tests) |
| Job tests on fresh MySQL 8.4.13 and Kafka 4.3.1 | 385 passed: the 379 from before plus 3 new tests on both databases |
| Whole suite | 473 passed, 16 skipped |
| Mutation checks | 30 of 30 caught offline on 9f347d1 (one needs MySQL); 31 of 31 against the live services on the same code; no timeouts |

The first offline mutation run caught only 28 of 30. Two breakages went unnoticed by any test:
- removing the stale-token check when the reconciler fails a job on its last attempt;
- not committing a malformed message when it is the last one in the queue.

The two new tests catch both now.

`★ Insight ─────────────────────────────────────`
- **Why the malformed-message breakage went unnoticed.** Kafka offsets are cumulative: committing a later message also covers every earlier one. The existing test put a valid job after the malformed message, so the job's commit hid the missing one.
- **Why the stale-token breakage was harmless but still worth a test.** Removing that token check didn't corrupt any state, because a separate check that each write touches exactly one row raised an error and rolled everything back. But a safety net isn't a specification: the new test pins the intended behaviour, which is to refuse a stale token cleanly rather than throw.
`─────────────────────────────────────────────────`

**Findings left for you** (outside M1's agreed fixes):
- The pipeline commands use exit code 1 both for "checks failed" and for any crash. M2 works around this by reading the run records instead.
- README line 224 says `windows` refuses an existing folder; it only refuses when `config.json` already exists.
- `spec.md` has no AI-contribution header. That is a wording decision about authorship, so I left it.
- The spec §5 diagram is scheduled for M6.

**Notes**
- My first full-suite run had 90 Spark errors because I called the venv's Python directly. Spark's worker processes then start `python3` from `PATH`, which was a Python without `etf_risk`. Through `uv run` everything passes. This confirms M2's plan to set `PYSPARK_PYTHON` explicitly.
- Four containers from another project shared the Docker VM. The memory peaks are recorded as informational, not as budget measurements. After the mutation session MySQL peaked at 441 of 512 MiB (86%), which repeats the limited headroom spec §11 already notes.
- Earlier tool output in this session printed that project's container and session names. They should be redacted when the AI logs are reviewed (W3). This session's logs are not committed.

**M2 timing corrections, reported before starting M2**
1. **Absolute deadlines.** The worker sends the launcher absolute deadlines on the shared monotonic clock, each with a sequence number. The launcher checks whether its current deadline has passed before reading any message, and once it fires, it stays fired. It accepts a message only if it is newer and still in the future. So messages that queue up while the launcher is paused can neither revive it nor push the deadline beyond what the worker granted. Two pause-and-resume tests with queued stale messages check this.
2. **No database time bound in the safety argument.** I've withdrawn the "W = 13 s" claim. Preventing overlapping Spark runs rests only on the launcher's watchdog, which never waits on the database, and the host-wide execution lock. The tree is gone by the deadline plus 0.5 s plus the 7 s kill time, before the lease expires, as long as the safety margin M is at least 0.5 + 7 s plus a small buffer. That gives a draft M of 10 s, and it holds even if the worker is stuck in a database call. The database timeouts remain, but only to keep the worker responsive.

**Your next steps:** push `feature/extension-baseline` (or tell me to), then open and merge the PR with a merge commit. `gh` isn't installed here. M2 will branch from `main` once that merge is in.
