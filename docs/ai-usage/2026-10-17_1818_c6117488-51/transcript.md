# Claude Code message 51

Session: `c6117488-0e99-49dd-a985-5cad552900a1` · prompt sent 2026-10-17 18:18 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): git-user ×9, home ×117, memory ×22, model-reasoning ×7, user ×26. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-17T23:18:12.998Z

<ide_opened_file>The user opened the file ~/leveraged-etf-risk-analytics/docs/experiments.md in the IDE. This may or may not be related to the current task.</ide_opened_file>

check it now

## 2. Assistant — 2026-10-17T23:18:18.013Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/docs/experiments.md"
}
```

## 3. User — 2026-10-17T23:18:18.141Z

### Tool result

````
1	# Spark performance experiments
2	
3	> **TODO (author):** authorship line in your own words.
4	
5	AI contribution: Claude Code (Opus 5.5) sets the tasks and acceptance criteria and reviews each
6	step. It drafted the parts marked _Drafted with Claude Code_ (section 2, items 2.1, 2.2 and 2.5)
7	from the records named in each part: numbers read from the configs by script, file hashes
8	recomputed.
9	
10	Status: Part A (sections 1–4) in progress; no measured runs yet.
11	
12	## 1. Question, hypotheses and design
13	
14	> **TODO (author):** research question 3 and hypotheses H1–H3 (spec §8, expectation 5); the strides
15	> and why; the order; the rule for running stride 3; why no stride 1.
16	
17	## 2. Window definitions: counts and self-checks
18	
19	### 2.1 How the sets were built
20	
21	_Drafted with Claude Code (Opus 5.5) from the four `config.json` files._
22	
23	The four sets were built on 2026-10-17, between 20:45:24 and 20:45:29 UTC, from the processed
24	snapshot `full-2026-10-12`, with this loop run from the repository root:
25	
26	```bash
27	for stride in 21 14 7 3; do
28	  uv run python -m etf_risk.windows \
29	    --snapshot full-2026-10-12 \
30	    --kind rolling \
31	    --stride "$stride" \
32	    --allow-dense-stride \
33	    --out-root data/windows-experiments
34	done
35	```
36	
37	`--allow-dense-stride` matters only for strides below 21; for stride 21 it has no effect. Each set
38	is in `data/windows-experiments/full-2026-10-12/rolling-252-s<stride>/` (`windows.parquet` and
39	`config.json`). For the four existing sets in `data/windows/full-2026-10-12/`, each
40	`windows.parquet` still matches the `windows_sha256` in its config. Their current file
41	modification timestamps are all dated 2026-10-12 in America/Chicago (some are 2026-10-13 UTC).
42	These are the available checks that the earlier artifacts were preserved; timestamps alone
43	do not prove their modification history.
44	
45	The four configs record the same build:
46	
47	- **Code:** commit `a7fb72d` with `git_worktree_clean: true` for the paths checked by
48	  `code_state()` (`src/`, `pyproject.toml` and `uv.lock`, not the entire repository); identical
49	  `source_sha256` (10 source files) and `uv_lock_sha256`.
50	- **Inputs:** identical `inputs_sha256` for the five daily-return files and `quality_report.json`.
51	- **Windows:** 252 trading days; start grid anchored at the NYSE session 1980-01-02; calendar from
52	  pandas_market_calendars 5.5.0; the same unverified-day flag rule.
53	- Each `windows.parquet` matches the `windows_sha256` recorded in its config.
54	
55	### 2.2 Counts
56	
57	_Drafted with Claude Code (Opus 5.5) from the `counts` block of each `config.json`._
58	
59	| Stride | Windows | AAPL  | MSFT  | NVDA  | QQQ   | TSLA  | Window-member rows | Path-day rows, 1x and 2x (at most) | Windows vs stride 21 |
60	| ------ | ------- | ----- | ----- | ----- | ----- | ----- | ------------------ | ---------------------------------- | -------------------- |
61	| 21     | 1,790   | 529   | 466   | 311   | 310   | 174   | 451,080            | 902,160                            | 1.00                 |
62	| 14     | 2,683   | 793   | 699   | 466   | 464   | 261   | 676,116            | 1,352,232                          | 1.50                 |
63	| 7      | 5,364   | 1,586 | 1,397 | 932   | 928   | 521   | 1,351,728          | 2,703,456                          | 3.00                 |
64	| 3      | 12,518  | 3,701 | 3,259 | 2,176 | 2,165 | 1,217 | 3,154,536          | 6,309,072                          | 6.99                 |
65	
66	- Windows and the per-ticker counts are `counts.windows` and `counts.by_ticker`; in every set the
67	  per-ticker counts sum to the total.
68	- Window-member rows = 252 × windows: one row per return day of each window.
69	- Path-day rows: at most 2 × window-member rows, one row per window, leverage (1x, 2x) and day. A
70	  breached 2x path stops at its breach, so a run can write fewer. The run of record, on
71	  `rolling-252-s21-r2` (equal to this stride-21 set, see 2.5), wrote 900,714 path-day rows against
72	  the bound of 902,160 (`row_counts` in its `run.json`).
73	- The last column is the number of windows divided by 1,790, rounded to two decimals.
74	
75	### 2.3 Self-checks
76	
77	Each value is a violation count, not a count of successful checks.
78	
79	| Check                    | Stride 21 | Stride 14 | Stride 7 | Stride 3 |
80	| ------------------------ | --------: | --------: | -------: | -------: |
81	| duplicate_window_keys    |         0 |         0 |        0 |        0 |
82	| unknown_ticker           |         0 |         0 |        0 |        0 |
83	| rows_out_of_range        |         0 |         0 |        0 |        0 |
84	| row_dates_mismatch       |         0 |         0 |        0 |        0 |
85	| flag_mismatch            |         0 |         0 |        0 |        0 |
86	| not_on_grid              |         0 |         0 |        0 |        0 |
87	| wrong_window_days        |         0 |         0 |        0 |        0 |
88	| spacing_not_stride       |         0 |         0 |        0 |        0 |
89	| missing_or_extra_windows |         0 |         0 |        0 |        0 |
90	| calendar_year_mismatch   |         0 |         0 |        0 |        0 |
91	| not_full_period          |         0 |         0 |        0 |        0 |
92	
93	All applicable checks found no violations; the builder raises an error instead of writing a set
94	when a check fails, so successfully written configs are expected to contain zeros. These zeros
95	do not establish that the source prices are correct or provide a fully independent validation,
96	because some checks reuse the window-generation rules.
97	
98	For these rolling windows, the applicable checks cover unique keys, known tickers, valid row
99	bounds, entry/first-return/exit dates, unverified-day flags (including the entry price), the
100	shared start grid, the 252-day length, stride spacing and the expected number of windows.
101	In particular, `missing_or_extra_windows` recomputes the expected count using the same
102	grid-selection rule as the builder; it is not an independent proof of correct membership.
103	Section 2.4 provides a separate arithmetic count check, and section 2.6 compares actual keys.
104	
105	`calendar_year_mismatch` and `not_full_period` apply to other window kinds; their zeros here
106	do not mean that calendar-year or full-period definitions were tested in this rolling-window build.
107	
108	### 2.4 Count check
109	
110	For a ticker with P price rows, there are P − 252 possible complete 252-return windows at
111	stride 1. The five processed files give 11,103 (AAPL), 9,777 (MSFT), 6,526 (NVDA), 6,494 (QQQ)
112	and 3,650 (TSLA) eligible starts, totaling 37,550. Their price dates were checked to occupy
113	consecutive sessions on the same NYSE grid used by the definitions.
114	
115	| Stride | Actual windows N | 37,550 / stride | N − 37,550 / stride | Absolute difference < 5 |
116	| ------ | ---------------: | --------------: | ------------------: | ----------------------- |
117	| 21     |            1,790 |    1,788.095238 |           +1.904762 | Yes                     |
118	| 14     |            2,683 |    2,682.142857 |           +0.857143 | Yes                     |
119	| 7      |            5,364 |    5,364.285714 |           −0.285714 | Yes                     |
120	| 3      |           12,518 |   12,516.666667 |           +1.333333 | Yes                     |
121	
122	Each ticker's eligible first-return session indices form a consecutive integer interval.
123	For stride s, the builder selects indices divisible by s. In an interval of n eligible indices,
124	the number selected is either floor(n / s) or ceil(n / s), depending on where the interval
125	starts relative to the anchor. Its difference from n / s therefore has absolute value less
126	than 1. Summing across five tickers gives an absolute difference strictly less than 5 from
127	37,550 / s. The displayed values are rounded to six decimal places; the comparisons use the
128	unrounded values.
129	
130	All four counts satisfy this bound. This is a coarse sanity check: a wrong set of dates could
131	still have a count within the bound, so it does not replace the date and membership checks.
132	
133	### 2.5 Baseline: the new stride-21 set equals `rolling-252-s21-r2`
134	
135	_Drafted with Claude Code (Opus 5.5) from both sets' `config.json` and `windows.parquet`._
136	
137	- **Same file:** both configs record the same `windows_sha256`, and hashing both `windows.parquet`
138	  files again gives that value, so the two files are byte-identical.
139	- **Same inputs:** identical `inputs_sha256`, raw-manifest hashes and `counts`, including the
140	  unverified-day counts.
141	- **Different code state:** `-r2` was built at `cc7f83c` with uncommitted changes, the new set at
142	  `a7fb72d` with the checked code/dependency paths clean (scope in 2.1). Of the 10 source files,
143	  only `provenance.py` differs: the `-r2`
144	  build used the version committed in `f08dec5`, and `6a460b0` (the Docker image) added the
145	  build-time fallback. `windows.py` and `uv.lock` are identical. The byte-identical files show that
146	  this change did not alter the definitions.
147	
148	So the experiment's stride-21 baseline is the run of record's window set, built by the same code
149	state as the three denser sets.
150	
151	### 2.6 Nesting
152	
153	| Compared set | Total windows | Stride-21 keys present | Stride-21 keys absent | Contains every stride-21 window |
154	| ------------ | ------------: | ---------------------: | --------------------: | ------------------------------- |
155	| Stride 21    |         1,790 |                  1,790 |                     0 | Yes (baseline)                  |
156	| Stride 14    |         2,683 |                    896 |                   894 | No                              |
157	| Stride 7     |         5,364 |                  1,790 |                     0 | Yes                             |
158	| Stride 3     |        12,518 |                  1,790 |                     0 | Yes                             |
159	
160	Let j be the first-return session index counted from the common anchor, 1980-01-02. A
161	stride-21 window has j divisible by 21. Since both 7 and 3 divide 21, every such start is
162	also selected at strides 7 and 3. The snapshot, window length and eligibility bounds are
163	unchanged, so these are the same windows, not just matching start dates.
164	
165	For stride 14, a shared start must be divisible by both 21 and 14, hence by their least
166	common multiple, 42. Equivalently, among starts j = 21k, only those with even k are shared;
167	the ones with odd k are absent. Checking the actual dates confirmed exactly this rule.
168	The 896 shared keys comprise AAPL 265, MSFT 233, NVDA 156, QQQ 155 and TSLA 87. Finite
169	per-ticker boundaries explain why the intersection is not exactly half of 1,790.
170	
171	Thus a smaller stride gives more windows, but does not always give a superset of the
172	baseline. In particular, the stride-14 workload changes the selected starts as well as
173	their number; it should not be described as the baseline plus extra windows.
174	
175	## 3. Run conditions and stop rules
176	
177	> **TODO (author):** how the runs are kept comparable (code state, machine state, order, repeats,
178	> output root); the go/no-go rule for stride 3, in numbers; how failures and early stops are
179	> reported.
180	
181	## 4. Predictions
182	
183	> **TODO (author):** for each stride, the median wall time as a number and the peak memory as a
184	> range, each with its reasoning and the result that would contradict it. Written before any
185	> measured run.
186	
187	_Part A ends here; it is committed before any measured run._
188	
189	## 5. Results
190	
191	> **TODO (Part B):** the measurements CSV and a summary table per stride, with medians and min–max
192	> over the three measured runs, including failures and early stops.
193	
194	## 6. Answers and limits
195	
196	> **TODO (author, Part B):** answers to questions (a)–(e) of the task, the comparison with
197	> section 4, and what these measurements cannot show.
198	
````

## 4. Assistant — 2026-10-17T23:19:22.791Z

### Tool call: Bash

```
{
  "command": "uv run python - <<'EOF'\nimport json, math, re, datetime as dt\nfrom pathlib import Path\nimport pandas as pd, pyarrow.parquet as pq\nfrom etf_risk.windows import session_grid\n\nroot = Path(\"data/windows-experiments/full-2026-10-12\")\nS = [21, 14, 7, 3]\ncfg = {s: json.loads((root / f\"rolling-252-s{s}\" / \"config.json\").read_text()) for s in S}\ndefs = {s: pq.read_table(root / f\"rolling-252-s{s}\" / \"windows.parquet\").to_pandas() for s in S}\ndoc = Path(\"docs/experiments.md\").read_text()\n\nprint(\"=== 2.2 table still matches the configs ===\")\nrows = [l for l in doc.splitlines() if re.match(r\"\\|\\s*(21|14|7|3)\\s*\\|\\s*[\\d,]+\\s*\\|\\s*[\\d,]+\\s*\\|\", l) and \"451,080\" in l or re.match(r\"\\|\\s*(14|7|3)\\s*\\|.*\\|\\s*\\d\\.\\d\\d\\s*\\|$\", l.strip())]\nfor l in rows:\n    c = [x.strip() for x in l.strip().strip(\"|\").split(\"|\")]\n    s = int(c[0]); n = cfg[s][\"counts\"][\"windows\"]; bt = cfg[s][\"counts\"][\"by_ticker\"]\n    want = [s, n, *(bt[t] for t in [\"AAPL\",\"MSFT\",\"NVDA\",\"QQQ\",\"TSLA\"]), 252*n, 504*n]\n    print(f\"  stride {s}: {[int(x.replace(',','')) for x in c[:9]] == want and c[9] == f'{n/1790:.2f}'}\")\n\nprint(\"=== 2.3 self-checks ===\")\nnames = list(cfg[21][\"definition_checks\"])\nprint(\"  11 names in config order:\", len(names) == 11, \"| all zero in all four:\", all(v == 0 for s in S for v in cfg[s][\"definition_checks\"].values()))\nprint(\"  names in the doc table:\", all(re.search(rf\"\\|\\s*{n}\\s*\\|\", doc) for n in names))\n\nprint(\"=== 2.4 eligible starts and consecutive sessions ===\")\nframes = {t: pd.read_parquet(f\"data/processed/full-2026-10-12/daily_returns/{t}.parquet\") for t in [\"AAPL\",\"MSFT\",\"NVDA\",\"QQQ\",\"TSLA\"]}\nfirst = min(f[\"date\"].iloc[0] for f in frames.values()); last = max(f[\"date\"].iloc[-1] for f in frames.values())\ngrid = session_grid(first, last, dt.date(1980, 1, 2))\nelig = {}\nfor t, f in frames.items():\n    idx = [grid[d] for d in f[\"date\"]]\n    consecutive = all(b - a == 1 for a, b in zip(idx, idx[1:]))\n    elig[t] = len(f) - 252\n    print(f\"  {t}: P={len(f)}, P-252={elig[t]}, dates are consecutive NYSE sessions: {consecutive}\")\nprint(\"  total:\", sum(elig.values()))\nprint(\"=== 2.4 per-ticker floor/ceil (stronger than the total) ===\")\nfor s in S:\n    bt = cfg[s][\"counts\"][\"by_ticker\"]\n    ok = {t: bt[t] in (elig[t] // s, -(-elig[t] // s)) for t in bt}\n    print(f\"  stride {s}: total {cfg[s]['counts']['windows']} vs {37550/s:.6f} (diff {cfg[s]['counts']['windows'] - 37550/s:+.6f}); every ticker floor/ceil: {all(ok.values())}\")\n\nprint(\"=== 2.6 nesting ===\")\nkey = [\"window_kind\", \"ticker\", \"window_days\", \"entry_date\"]\nk21 = set(map(tuple, defs[21][key].astype(str).values))\nfor s in [14, 7, 3]:\n    ks = set(map(tuple, defs[s][key].astype(str).values))\n    print(f\"  stride {s}: stride-21 keys present {len(k21 & ks)}, absent {len(k21 - ks)}\")\nd21 = defs[21].assign(j=defs[21][\"first_return_date\"].map(grid))\nshared = set(map(tuple, defs[21][key].astype(str).values)) & set(map(tuple, defs[14][key].astype(str).values))\nd21[\"shared14\"] = [tuple(r) in shared for r in d21[key].astype(str).values]\nprint(\"  shared with stride 14 exactly when j % 42 == 0:\", bool(((d21[\"j\"] % 42 == 0) == d21[\"shared14\"]).all()))\nprint(\"  shared per ticker:\", d21[d21[\"shared14\"]].groupby(\"ticker\").size().to_dict())\n\nprint(\"=== 2.1 timestamps of the existing sets (local and UTC) ===\")\nfor d in sorted(Path(\"data/windows/full-2026-10-12\").iterdir()):\n    m = [p.stat().st_mtime for p in d.iterdir()]\n    loc = {dt.datetime.fromtimestamp(x).strftime(\"%Y-%m-%d\") for x in m}\n    utc = {dt.datetime.fromtimestamp(x, dt.timezone.utc).strftime(\"%Y-%m-%d\") for x in m}\n    print(f\"  {d.name}: local dates {sorted(loc)}, UTC dates {sorted(utc)}\")\nprint(\"  local timezone:\", dt.datetime.now().astimezone().tzname())\nEOF",
  "description": "Independently verify the user's section 2 numbers and claims"
}
```

## 5. User — 2026-10-17T23:19:25.279Z

### Tool result

```
=== 2.2 table still matches the configs ===
  stride 21: True
  stride 14: True
  stride 7: True
  stride 3: True
=== 2.3 self-checks ===
  11 names in config order: True | all zero in all four: True
  names in the doc table: True
=== 2.4 eligible starts and consecutive sessions ===
  AAPL: P=11355, P-252=11103, dates are consecutive NYSE sessions: True
  MSFT: P=10029, P-252=9777, dates are consecutive NYSE sessions: True
  NVDA: P=6778, P-252=6526, dates are consecutive NYSE sessions: True
  QQQ: P=6746, P-252=6494, dates are consecutive NYSE sessions: True
  TSLA: P=3902, P-252=3650, dates are consecutive NYSE sessions: True
  total: 37550
=== 2.4 per-ticker floor/ceil (stronger than the total) ===
  stride 21: total 1790 vs 1788.095238 (diff +1.904762); every ticker floor/ceil: True
  stride 14: total 2683 vs 2682.142857 (diff +0.857143); every ticker floor/ceil: True
  stride 7: total 5364 vs 5364.285714 (diff -0.285714); every ticker floor/ceil: True
  stride 3: total 12518 vs 12516.666667 (diff +1.333333); every ticker floor/ceil: True
=== 2.6 nesting ===
  stride 14: stride-21 keys present 896, absent 894
  stride 7: stride-21 keys present 1790, absent 0
  stride 3: stride-21 keys present 1790, absent 0
  shared with stride 14 exactly when j % 42 == 0: True
  shared per ticker: {'AAPL': 265, 'MSFT': 233, 'NVDA': 156, 'QQQ': 155, 'TSLA': 87}
=== 2.1 timestamps of the existing sets (local and UTC) ===
  calendar-year: local dates ['2026-10-12'], UTC dates ['2026-10-13']
  calendar-year-r2: local dates ['2026-10-12'], UTC dates ['2026-10-13']
  rolling-252-s21: local dates ['2026-10-12'], UTC dates ['2026-10-13']
  rolling-252-s21-r2: local dates ['2026-10-12'], UTC dates ['2026-10-13']
  local timezone: CDT
```

## 6. Assistant — 2026-10-17T23:20:58.673Z

### Tool call: Bash

```
{
  "command": "D=data/outputs/windows/full-2026-10-12/rolling-252-s21 && echo \"entries: $(ls \"$D\" | wc -l | tr -d ' ')\" && ls \"$D\" | head -8 && for r in \"$D\"/*/run.json; do python3 -c \"import json,sys; d=json.load(open(sys.argv[1])); print('  ', sys.argv[1].split('/')[-2], '-> windows_dir:', d.get('windows_dir'))\" \"$r\"; done 2>/dev/null | head -5",
  "description": "List what the default output folder for stride 21 holds"
}
```

## 7. User — 2026-10-17T23:20:59.571Z

### Tool result

```
entries: 19
SUPERSEDED.txt
protocol-20261013T000707Z.json
protocol-20261013T001105Z.json
run-20261013T000707Z-1
run-20261013T000707Z-1.log
run-20261013T000707Z-2
run-20261013T000707Z-2.log
run-20261013T000707Z-3
   run-20261013T000707Z-1 -> windows_dir: data/windows/full-2026-10-12/rolling-252-s21
   run-20261013T000707Z-2 -> windows_dir: data/windows/full-2026-10-12/rolling-252-s21
   run-20261013T000707Z-3 -> windows_dir: data/windows/full-2026-10-12/rolling-252-s21
   run-20261013T000707Z-4 -> windows_dir: data/windows/full-2026-10-12/rolling-252-s21
   run-20261013T001105Z-1 -> windows_dir: data/windows/full-2026-10-12/rolling-252-s21
```

## 8. Assistant — 2026-10-17T23:21:08.063Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/stage3-tutor-mode.md",
  "old_string": "[REDACTED:memory]",
  "new_string": "[REDACTED:memory]"
}
```

## 9. User — 2026-10-17T23:21:09.281Z

### Tool result

```
[REDACTED:memory]
```

## 10. Assistant — 2026-10-17T23:21:27.253Z

Step 1 meets all seven criteria. I checked every number in your 2.3, 2.4 and 2.6 against the data, and all of them are correct. Two things need fixing: one statement in 2.1, and the attribution markers on the parts you edited.

**What I checked (all match):**
- **2.2:** the reformatted table still matches all four configs.
- **2.3:** all 11 checks are zero in all four configs, and their names match your table.
- **2.4:**
  - The eligible starts per ticker (P − 252) are 11,103 / 9,777 / 6,526 / 6,494 / 3,650, totalling 37,550.
  - Every ticker's price dates are consecutive NYSE sessions.
  - All four differences in your table are right.
- **2.6:**
  - Present keys are 896 / 1,790 / 1,790.
  - A stride-21 window is shared with stride 14 exactly when j is a multiple of 42.
  - The per-ticker split is 265 / 233 / 156 / 155 / 87.

| Criterion | Result |
|---|---|
| 1. Clean code state, separate root, nothing changed | Met |
| 2. Numbers traceable to configs | Met |
| 3. Self-check text accurate | Met |
| 4. Count check and reasoning | Met |
| 5. Baseline equality | Met (my draft) |
| 6. Nesting counts and reason | Met. "Not the baseline plus extra windows" is exactly the right conclusion for stride 14. |
| 7. Wording | Met, apart from the 2.1 statement below |

### To fix
1. **2.1, timestamps:** every file in the four existing sets is dated 2026-10-13 in UTC, not just some. They were modified on the evening of 2026-10-12 CDT, after 19:00, which is already the next day in UTC. The configs and your build times use UTC, so give the UTC date and mention the CDT date if you like. Separately, "These are the available checks that the earlier artifacts were preserved" reads awkwardly; something like "These are the only available evidence that…" would be clearer.
2. **Attribution:** 2.1 and 2.5 now include your edits but are still marked only as drafted by me. Add "edited by the author" to those two markers. The header also lost the sentence saying who checks the drafted parts and who wrote everything else. Your authorship line (still a TODO) should cover both, because the README's convention is that a file's header says what was written with AI and how it was checked.

### Optional, for precision
- **2.3:** "expected to contain zeros" undersells it. `build_definitions()` raises an error before writing anything if any count is non-zero, so a config written by `etf_risk.windows` can contain only zeros. Also, `calendar_year_mismatch` and `not_full_period` aren't checked at all for rolling windows; they just stay at their starting value of 0.
- **2.4:**
  - You already have each ticker's n, so you can check that each ticker's count is floor or ceil of n/s. That's 20 checks with a bound of 1 each, and per-ticker errors in opposite directions could cancel out in the total. All 20 hold.
  - Also say how you checked that the dates are consecutive sessions, since the floor/ceil argument depends on it.
- **2.6:** you can say exactly where the 1 extra key over 895 comes from. Hint: which tickers have an odd number of stride-21 windows, and what does that say about their first and last k?

## Step 2: sections 1 and 3 (design and run conditions)

**Section 1: question, hypotheses and design**
1. Research question 3 and H1–H3 from spec §8 (expectation 5), in your own words but with the same meaning.
2. Your strides and why, using the window ratios from 2.2, and what the stride-14 result in 2.6 means for comparing runs later.
3. Why you run sparse to dense, given that the stop rule acts only between runs.
4. Why there's no stride 1 (spec §7 gives 37,550 windows and at most 18,925,200 path-day rows).

**Section 3: run conditions and stop rules**
1. **Code state:** how you'll meet criterion 1 and which record fields will show it.
2. **Machine state:** what you'll close or check before each protocol, and what gets recorded.
3. **Protocols:** the order, `--repeats 4`, whether all strides run in one sitting, and the `--out-root` for the runs.
4. **Go/no-go rule for stride 3:** numeric, based on quantities the stride-7 protocol will record, with thresholds fixed now.
5. **Failures and early stops:** what you keep, what you report, and what you will and won't do after a failed check, a failed run or a stop.

**Acceptance criteria**
1. H1–H3 keep the meaning they have in spec §8, with no new claims.
2. Each condition either names the record field that captures it or is stated as a check you do by hand.
3. The go/no-go rule can be evaluated mechanically from the stride-7 records, and its thresholds are fixed before stride 7 runs.
4. Runs go under their own `--out-root`, and nothing is written under `data/outputs/windows/`.
5. Nothing is deleted or overwritten, and no threshold or repeat count changes without a written reason.
6. No predictions yet; they come in step 3.

**Hints**
- With the default `--out-root`, runs on your stride-21 set would go into `data/outputs/windows/full-2026-10-12/rolling-252-s21/`. That folder already holds 19 entries from superseded pre-cleanup runs, plus a `SUPERSEDED.txt` note.
- `measure` records the free memory before each run but doesn't refuse to start when it's low, so any minimum you set is a check you make yourself.
- The stop threshold is 60% of RAM, about 4.8 GiB here. Your go/no-go rule can be stricter.

`★ Insight ─────────────────────────────────────`
- **A total can hide what the parts show:** the "within 5" check is the sum of five per-ticker checks, each with a bound of 1. Checking per ticker is tighter and also tells you which ticker is off.
- **Dates depend on the time zone:** the same file shows 2026-10-12 locally and 2026-10-13 in UTC. Your records already use UTC (`created_at_utc`, `started_at_utc`), so stating dates in UTC keeps the doc consistent with them.
`─────────────────────────────────────────────────`
