# Claude Code message 55

Session: `eab06baf-de8e-4e5f-830e-4907c7544308` · prompt sent 2026-10-27 19:34 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): git-user ×119, home ×861, memory ×39, model-reasoning ×42, user ×118. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-28T00:34:10.176Z



<pasted_content id="2323">
Draft the batch-3 results in Part B and update README/spec to state that valid formal E2 evidence is now available for this host and configuration. Preserve batch-1 and batch-2, their invalid verdicts and all protocol amendments.

Use explicit timing origins when comparing finish times with deadlines, particularly for service outages. Explain the expected missing W5a reports and the greater-than-expected deadline slack.

Mark the new interpretation as drafted with Claude Code and awaiting my review; do not record my approval before I give it.

Run appropriate documentation checks and provide the proposed conclusions, remaining-work list and PR title/description. Do not run more experiments, push, merge or commit AI logs.
</pasted_content id="2323">


## 2. Assistant — 2026-10-28T00:34:19.322Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; git -C $W status --short | head; git -C $W log --oneline -4; wc -l $W/docs/recovery-part-b.md $W/docs/recovery-part-a.md $W/README.md $W/docs/spec.md; grep -n \"^#\" $W/docs/recovery-part-b.md",
  "description": "Check the worktree state and outline Part B"
}
```

## 3. User — 2026-10-28T00:34:20.082Z

### Tool result

```
c5c340a Approve formal batch-3 and freeze the recovery code at 4fc550e
4fc550e Keep only the verb of a Docker event's action, never its command
12c925d Record recovery batches' page and swap counters by name, and watch containers batch-wide
ad5e476 Merge pull request #18 from [REDACTED:git-user]/docs/closeout-readme-spec
     379 ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md
     598 ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-a.md
     506 ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md
    1005 ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md
    2488 total
1:# Recovery experiments: Part B, the formal batches
22:## 1. The author's decisions (2026-10-25)
36:## 2. The two batches side by side
58:## 3. What happened
60:### 3.1 batch-1: the lid closed, then the host restarted
80:### 3.2 batch-2: another project's container
93:## 4. Correctness (E1)
95:### 4.1 batch-2: correctness observations (valid)
151:### 4.2 batch-1: no valid correctness verdict
197:## 5. Recovery times (E2)
199:### 5.1 No valid formal recovery times
204:### 5.2 Supplementary observations: batch-2, positions 1–17
247:### 5.3 Positions 18–30
253:## 6. Host conditions
268:## 7. Answers and limits
274:### 7.1 E1
292:### 7.2 E2
321:### 7.3 Limits
336:## 8. Tooling changes after the formal batches (`5ecde71`)
364:## 9. Records
```

## 4. Assistant — 2026-10-28T00:34:21.563Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md"
}
```

## 5. User — 2026-10-28T00:34:21.679Z

### Tool result

```
1	# Recovery experiments: Part B, the formal batches
2	
3	_Drafted with Claude Code (Opus 5.5) on 2026-10-25 at the author's request. Its sources are the
4	records in `data/outputs-recovery/formal/` (numbers and tables read by script) and the author's
5	decisions of 2026-10-25 (section 1). Sections 2–6 give facts. The answers in section 7 were
6	drafted with Claude Code and approved by the author, unchanged, on 2026-10-25. Part A is
7	[recovery-part-a.md](recovery-part-a.md), approved on 2026-10-25 (`1c11577`). The records stay
8	outside Git and have not been changed since the collector wrote them; later notes sit beside them
9	as separate files. Times are local (UTC−5) on 2026-10-25._
10	
11	> **Correction, 2026-10-26.** The bytes this document called "swapped in" and "swapped out"
12	> are psutil's `sin` and `sout`. On macOS they are page-ins and page-outs, not swap traffic
13	> ([host-counters-correction.md](host-counters-correction.md)). At the author's instruction:
14	> - sections 5.2 and 6 now say "paged in" and "paged out", with the figures unchanged;
15	> - "heavy swapping" (section 5.2) and "swapping heavily" (section 7.3, an answer approved on
16	>   2026-10-25) are replaced by the swap in use the records show, because the recorded counters
17	>   do not measure swap traffic.
18	>
19	> Swap in use is recorded correctly, and its figures are kept. No verdict changes: nothing gated
20	> on these counters.
21	
22	## 1. The author's decisions (2026-10-25)
23	
24	- Part A was approved with all 13 decisions of its section 10, seed 544 included. Its row 11: a
25	  formal batch that is invalid or stops early is kept and reported in full, with one rerun of the
26	  same plan.
27	- batch-1 was stopped by a restart of the host. batch-2 is the one rerun.
28	- **batch-2: correctness observations valid; recovery times invalid** under the approved
29	  batch-level protocol (Part A, section 12, condition 4), because the exclusive window was broken
30	  when another project's container started at 06:25:08.
31	- Positions 1–17 of batch-2, which ran before that container started, are not a valid formal
32	  sub-batch. They are reported only as supplementary observations (5.2), with the limitation
33	  stated.
34	- No further formal batch for now.
35	
36	## 2. The two batches side by side
37	
38	Three sources of verdicts are kept apart here and throughout:
39	- **the collector's verdicts as recorded:** written by the collector at `fcaa645` into each batch's
40	  `validity.json` when the batch was collected;
41	- **the author's decision:** recorded on 2026-10-25, in section 1 and in `batch-2.decision.txt`;
42	- **later collector results:** computed in memory with the collector at `5ecde71` (section 8) and
43	  never written to the records.
44	
45	| | batch-1 | batch-2 |
46	|---|---|---|
47	| Plan | `plan-544.json`: seed 544, 30 jobs (C0, 28 shuffled, C0) | the same plan |
48	| Code | HEAD `1c11577`, clean; the code of `fcaa645` | the same |
49	| Ran | 00:15:09 to 00:39:54, then the host restarted | 05:55:28 to 06:45:37 |
50	| Harness exit | none: the shell ended with the host | 0 |
51	| Jobs | 19 done, 1 stopped by the restart, 10 never started | 30 of 30 done |
52	| Made, missed, not run, unrecorded (collector) | 20, 0, 0, 10 | 30, 0, 0, 0 |
53	| Final snapshot | none | `status --check` exit 0; fingerprints agree (30 jobs, 40 attempts) |
54	| Collector verdicts as recorded (`fcaa645`) | correctness invalid (`fingerprints_agree`); recovery times invalid (also the clock check, the lid closed at 2 readings, power unknown); exit 1 | both valid; exit 0 |
55	| The author's decision, as recorded | none recorded; the collector's verdicts apply | correctness valid; recovery times **invalid**: the exclusive window was broken |
56	| Later collector results (`5ecde71`; computed, not written) | as recorded, plus `other_containers` unknown: no count was recorded | correctness valid; recovery times invalid, because `other_containers` is unknown: no count was recorded. Insufficient evidence, not a further violation |
57	
58	## 3. What happened
59	
60	### 3.1 batch-1: the lid closed, then the host restarted
61	
62	- Positions 1–19 finished, and all succeeded. Position 20, the third C0 control, was claimed by
63	  worker A at 00:39:54.
64	- **The lid was closed during positions 16–18.**
65	  - The power log records a clamshell sleep entered as a dark wake at 00:35:46, and a full wake on
66	    user activity at 00:38:34.
67	  - The host readings before positions 17 (00:36:37) and 18 (00:38:22) recorded the lid closed;
68	    the reading before position 19 (00:39:03) recorded it open.
69	  - No wall-minus-monotonic jump over 1 s appears between the harness's events, so the processes
70	    kept running. The batch ran under `caffeinate -dims` on AC power.
71	- **An orderly shutdown followed at about 00:40.** `last` records a shutdown at 00:40, a
72	  shutdown-stall report is dated 00:40:15, and the host booted at 00:40:38; no software update
73	  was installed. The shutdown ended job 20's attempt (its recorded error: "spark_pipeline: the
74	  worker was stopped") and the harness, before its final snapshot. What initiated the shutdown is
75	  not recorded.
76	- After the boot, Docker was not running and both containers had exited. MySQL was started again
77	  on batch-1's own volume for an export (`batch-1.after-restart/`, 4.2); then `docker compose down
78	  -v` removed the containers, the network and the four anonymous volumes.
79	
80	### 3.2 batch-2: another project's container
81	
82	- All 30 jobs ran. Quiescence left no process and no other database connection; the final
83	  snapshot and the removal of the services followed.
84	- **Another project's container started at 06:25:08** (created then; restart policy "no") and ran
85	  through the last 20 minutes of the batch; it used about 605 MiB at 06:49.
86	  - Positions 1–17 ran before it. Job 17 was accepted at 06:25:07.84, 0.21 s before the
87	    container started; the harness logged its end 0.18 s after. Positions 18–30 ran while it ran.
88	  - The harness counted other containers only at the start, where it counted 0, so batch-2's
89	    records do not show the container. The evidence is `batch-2.other-container.txt`, written at
90	    06:49 from Docker's own record of the container, which this session did not touch.
91	- The power log has no sleep, wake or clamshell line between 05:55 and 06:46.
92	
93	## 4. Correctness (E1)
94	
95	### 4.1 batch-2: correctness observations (valid)
96	
97	The checks behind this verdict do not involve time, so the other container does not bear on them.
98	
99	- **One accepted result per job:** Q1 `ok` for all 30 jobs, each with exactly one accepted result.
100	- **Results equal to the reference run:** all 30 accepted attempts pass the collector's checks: the
101	  folder's digest equals the accepted digest, the run's checks and verify output are clean, and
102	  every table matches the reference run by content.
103	- **Executions:** 10 jobs were claimed twice (W2, W3, W4, W6 and W7, two of each), and 8 of them
104	  executed twice. Both W4 jobs completed two executions and had one accepted. `cleanup.txt` lists
105	  8 unaccepted attempts' folders (16.6 MiB).
106	- **No overlapping step intervals:** every step has both monotonic times.
107	- **The job table:** `status --check` exit 0, with no invariant violation. The three fingerprints
108	  agree (30 jobs, version sum 398, 40 attempts, 278 renewals).
109	- **Q2b and Q3:** no Q2b rows (no job in the table that the harness did not record) and no Q3b
110	  mismatch. Q3a is "reported once" for 28 jobs and "no matching report" for the 2 W5a jobs, killed
111	  between the acceptance commit and its event, as designed.
112	- **Liveness:** 56 retried `accept_result` calls, 28 for each D2 job during its MySQL outage, and
113	  26 failed reconciler passes during the MySQL outages of D1 and D2; no `failed_after_ack`, no
114	  `consumer_error`, no serve restart.
115	- **Left behind:** the only new scratch entry is the JVM's perf-data folder (`hsperfdata`), absent
116	  at the batch's start and present, empty, after it.
117	
118	| Position | Case | Claims | Accepted | Executions (complete) | Q1 | Q3a | Accepted result against the reference |
119	|---:|---|---:|---:|---|---|---|---|
120	| 1 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
121	| 2 | W5a | 1 | 1 | 1 (1) | `ok` | no matching report | matches, all checks clean |
122	| 3 | W2 | 2 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
123	| 4 | W7 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
124	| 5 | W3 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
125	| 6 | W5a | 1 | 1 | 1 (1) | `ok` | no matching report | matches, all checks clean |
126	| 7 | D1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
127	| 8 | D1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
128	| 9 | W5b | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
129	| 10 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
130	| 11 | K2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
131	| 12 | X1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
132	| 13 | W2 | 2 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
133	| 14 | W3 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
134	| 15 | K1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
135	| 16 | W6 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
136	| 17 | W6 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
137	| 18 | X1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
138	| 19 | W5b | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
139	| 20 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
140	| 21 | W1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
141	| 22 | D2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
142	| 23 | W7 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |
143	| 24 | K1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
144	| 25 | W4 | 2 | 1 | 2 (2) | `ok` | reported once | matches, all checks clean |
145	| 26 | W1 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
146	| 27 | W4 | 2 | 1 | 2 (2) | `ok` | reported once | matches, all checks clean |
147	| 28 | D2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
148	| 29 | K2 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
149	| 30 | C0 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |
150	
151	### 4.2 batch-1: no valid correctness verdict
152	
153	- The collector found `fingerprints_agree` failed: the final snapshot never ran. There is no Q1 row
154	  for any submitted job, so every Q1 verdict is unknown.
155	- **Supplementary, taken after the restart and not by the harness** (`batch-1.after-restart/`):
156	  MySQL recovered on start, then `status --check` (exit 0, all invariants hold) and an export.
157	  - 19 jobs succeeded with exactly one accepted attempt each, 7 of them after an expired first
158	    attempt.
159	  - Job 20 is queued, its one attempt failed ("spark_pipeline: the worker was stopped").
160	
161	  These are not correctness observations under the protocol, since the batch's correctness verdict
162	  is invalid; they are reported as found.
163	
164	| Position | Case | Harness record | Job after the restart | Attempts (outcome) | Accepted |
165	|---:|---|---|---|---|---:|
166	| 1 | C0 | job done | succeeded | 1: accepted | 1 |
167	| 2 | W5a | job done | succeeded | 1: accepted | 1 |
168	| 3 | W2 | job done | succeeded | 1: expired, 2: accepted | 1 |
169	| 4 | W7 | job done | succeeded | 1: expired, 2: accepted | 1 |
170	| 5 | W3 | job done | succeeded | 1: expired, 2: accepted | 1 |
171	| 6 | W5a | job done | succeeded | 1: accepted | 1 |
172	| 7 | D1 | job done | succeeded | 1: accepted | 1 |
173	| 8 | D1 | job done | succeeded | 1: accepted | 1 |
174	| 9 | W5b | job done | succeeded | 1: accepted | 1 |
175	| 10 | C0 | job done | succeeded | 1: accepted | 1 |
176	| 11 | K2 | job done | succeeded | 1: accepted | 1 |
177	| 12 | X1 | job done | succeeded | 1: accepted | 1 |
178	| 13 | W2 | job done | succeeded | 1: expired, 2: accepted | 1 |
179	| 14 | W3 | job done | succeeded | 1: expired, 2: accepted | 1 |
180	| 15 | K1 | job done | succeeded | 1: accepted | 1 |
181	| 16 | W6 | job done | succeeded | 1: expired, 2: accepted | 1 |
182	| 17 | W6 | job done | succeeded | 1: expired, 2: accepted | 1 |
183	| 18 | X1 | job done | succeeded | 1: accepted | 1 |
184	| 19 | W5b | job done | succeeded | 1: accepted | 1 |
185	| 20 | C0 | started; stopped by the restart | queued | 1: failed | 0 |
186	| 21 | W1 | none: never started | — | — | — |
187	| 22 | D2 | none: never started | — | — | — |
188	| 23 | W7 | none: never started | — | — | — |
189	| 24 | K1 | none: never started | — | — | — |
190	| 25 | W4 | none: never started | — | — | — |
191	| 26 | W1 | none: never started | — | — | — |
192	| 27 | W4 | none: never started | — | — | — |
193	| 28 | D2 | none: never started | — | — | — |
194	| 29 | K2 | none: never started | — | — | — |
195	| 30 | C0 | none: never started | — | — | — |
196	
197	## 5. Recovery times (E2)
198	
199	### 5.1 No valid formal recovery times
200	
201	batch-1 is invalid for recovery times by the collector's checks, and batch-2 by the author's
202	decision. This part therefore reports no formal recovery times.
203	
204	### 5.2 Supplementary observations: batch-2, positions 1–17
205	
206	**Limitation.** These are not formal results and not a sub-batch. They were selected after the
207	batch, by the time another project's container started, and the batch they belong to is invalid
208	for recovery times. The other recorded conditions held for them: AC power and the lid open at their
209	readings, no sleep, the clock check. They were taken under memory pressure (level 2 at 16 of their
210	17 readings), with 3.86–8.25 GiB of swap in use at those readings, on this host only. They are counts per job, with no rate and no
211	performance claim. Every outcome in the range is kept, the two late jobs included.
212	
213	Detection, re-run and finish times are the collector's, as section 5 of the outline defines them:
214	from the injection, or from the submit for C0. D and the deadline column count from each case's
215	deadline reference (Part A, section 3). For W2–W7 that reference is the injection, and for C0 the
216	submit. For D1 and K2, the injection is the service's stop, while the reference is the service's
217	return, 35.3–35.8 s after the stop. Measured from the return, the D1 jobs finished in 21.7 and
218	14.9 s and the K2 job in 68.4 s.
219	
220	| Position | Case | Claims | Detection (s) | Re-run (s) | Finish (s) | D (s) | Deadline | Pressure | Available (GiB) | Paged out during (MiB) |
221	|---:|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
222	| 1 | C0 | 1 | n/a: no failure | n/a: no failure | 84.7 | 75 | late | 2 | 1.42 | 83 |
223	| 2 | W5a | 1 | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance | 75 | on time | 2 | 1.48 | 9 |
224	| 3 | W2 | 2 | 63.7 | 63.7 | 121.0 | 140 | on time | 2 | 1.41 | 38 |
225	| 4 | W7 | 2 | 60.5 | 60.5 | 165.2 | 170 | on time | 2 | 1.33 | 59 |
226	| 5 | W3 | 2 | 57.9 | 57.9 | 136.9 | 140 | on time | 2 | 1.25 | 55 |
227	| 6 | W5a | 1 | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance | 75 | on time | 2 | 1.34 | 20 |
228	| 7 | D1 | 1 | 3.6 | n/a: the attempt went on | 57.5 | 140 | on time | 2 | 1.21 | 44 |
229	| 8 | D1 | 1 | 5.9 | n/a: the attempt went on | 50.4 | 140 | on time | 2 | 1.44 | 47 |
230	| 9 | W5b | 1 | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance | 75 | on time | 2 | 1.49 | 45 |
231	| 10 | C0 | 1 | n/a: no failure | n/a: no failure | 43.2 | 75 | on time | 2 | 1.49 | 4 |
232	| 11 | K2 | 1 | 35.8 | 50.5 | 103.7 | 125 | on time | 2 | 1.51 | 26 |
233	| 12 | X1 | 1 | n/a: no failure | n/a: no failure | 61.1 | 75 | on time | 2 | 1.24 | 16 |
234	| 13 | W2 | 2 | 63.3 | 63.3 | 100.4 | 140 | on time | 2 | 1.69 | 30 |
235	| 14 | W3 | 2 | 57.4 | 57.4 | 104.1 | 140 | on time | 2 | 1.66 | 30 |
236	| 15 | K1 | 1 | n/a for the job: the attempt goes on | n/a: the attempt goes on | 47.5 | 75 | on time | 2 | 1.63 | 20 |
237	| 16 | W6 | 2 | 58.1 | 58.1 | 182.6 | 140 | late | 2 | 1.53 | 132 |
238	| 17 | W6 | 2 | 58.8 | 58.8 | 101.6 | 140 | on time | 1 | 2.04 | 98 |
239	
240	- **2 of the 17 jobs were late,** both before the other container started:
241	  - position 1 (C0, the batch's first job), 84.7 s against 75 s, with 83 MiB paged out during it;
242	  - position 16 (W6), 182.6 s against 140 s, with 132 MiB paged out during it.
243	- **The controls in this range** (positions 1 and 10) took 84.7 and 43.2 s.
244	- **Cases missing:** W1, W4 and D2 ran only at positions 18–30, so there is no supplementary
245	  observation of their times.
246	
247	### 5.3 Positions 18–30
248	
249	Their times and deadline outcomes stay in batch-2's records (`injections.csv`) and are not reported
250	here, because they ran while another project's container ran. Their correctness outcomes are in
251	4.1.
252	
253	## 6. Host conditions
254	
255	| | batch-1 | batch-2 |
256	|---|---|---|
257	| Readings | 21: the start and 20 jobs; no end reading | 32: the start, 30 jobs and the end |
258	| Power | AC at all 21 | AC at all 32 |
259	| Lid | closed at the readings before positions 17 and 18 | open at all 32 |
260	| Sleep (power log) | a clamshell dark wake from 00:35:46 to a full wake at 00:38:34; no clock jump between the harness's events | none |
261	| Clock check | failed: no `batch_ended` event | passed: wall minus monotonic −0.009 s, 19 of 19 processes on one clock |
262	| Memory pressure | level 2 at all 21 | level 2 at 31 of 32; 1 before position 17 |
263	| Available before each job | 1.45–1.83 GiB | 1.21–2.04 GiB |
264	| Swap and paging over the batch | not computable: no end reading | swap in use +2.67 GiB; 1.35 GiB paged out, 47.9 GiB paged in |
265	| Container peaks | MySQL 317 of 512 MiB (62%); Kafka 506 of 640 MiB (79%) | MySQL 269 of 512 MiB (53%); Kafka 505 of 640 MiB (79%) |
266	| Other containers | 0 at the start; no later count | 0 at the start; one from 06:25:08, outside the records (3.2) |
267	
268	## 7. Answers and limits
269	
270	_The questions are those of spec §11. Under each, the facts are drafted with Claude Code from
271	sections 4–6. The answers were drafted with Claude Code and approved by the author, unchanged, on
272	2026-10-25._
273	
274	### 7.1 E1
275	
276	> Does each job accept at most one result, and does every successfully completed job have exactly
277	> one, even when jobs execute more than once?
278	
279	_Drafted facts:_ in batch-2, whose correctness verdict is valid, all 30 jobs succeeded with exactly
280	one accepted result, which matched the reference run. 8 of them executed twice, and 2 of those
281	(the W4 jobs) completed two executions. batch-1 gives no valid correctness verdict (4.2).
282	
283	**Answer (drafted with Claude Code; approved by the author on 2026-10-25).** In batch-2, whose
284	correctness verdict is valid, every job accepted exactly one result: all 30 jobs succeeded with one
285	accepted attempt each, and every accepted result matched the reference run. This held for the 10
286	jobs claimed twice and the 8 executed twice, including the 2 W4 jobs that completed two executions
287	and had only one accepted. No job had more than one accepted result. batch-1 gives no valid
288	correctness verdict, because its final snapshot never ran. Its job table, exported after the
289	restart, shows one accepted attempt for each of its 19 succeeded jobs, but that is supplementary
290	evidence. These are counts from one batch of 30 jobs on one host, not a rate.
291	
292	### 7.2 E2
293	
294	> After a worker crash (before or after its claim), a broker restart or a database restart, how
295	> long until the job runs again and finishes, and is any job lost or accepted twice?
296	
297	_Drafted facts:_ there are no valid formal recovery times (5.1). The supplementary observations of
298	positions 1–17 (5.2) cover 11 of the 14 cases, with the limitation stated there. No job of batch-2
299	was lost or accepted twice: 30 of 30 succeeded with one accepted result each.
300	
301	**Answer (drafted with Claude Code; approved by the author on 2026-10-25).** No formal recovery
302	times are reported. batch-1 stopped when the host restarted, and batch-2's recovery times are
303	invalid under the approved batch-level protocol, because another project's container broke the
304	exclusive window from position 18 on. Positions 1–17 of batch-2 are supplementary observations
305	only: not a formal sub-batch, and taken under memory pressure on this host. They show the
306	following.
307	- After a worker was killed or stopped (W2, W3, W6, W7), the job ran again 57.4–63.7 s after the
308	  injection and finished 100.4–182.6 s after it.
309	- A Kafka restart (K1) did not interrupt the attempt; the job finished 47.5 s after the restart
310	  began.
311	- With Kafka stopped around the submit (K2), the job first ran 50.5 s after the stop and finished
312	  68.4 s after Kafka's return.
313	- After MySQL restarts (D1), the attempts went on and finished 21.7 and 14.9 s after MySQL's
314	  return.
315	- Kills after the acceptance (W5a, W5b) left each job succeeded with its one accepted result.
316	
317	15 of the 17 met their deadlines. The two late jobs, the first control at 84.7 s and a W6 at
318	182.6 s, both preceded the external container. W1, W4 and D2 have no supplementary times. No job in
319	batch-2 was lost or accepted twice: all 30 succeeded with exactly one accepted result.
320	
321	### 7.3 Limits
322	
323	- **One host:** an 8 GiB Mac under memory pressure, with 3.16–8.25 GiB of swap in use at the
324	  formal batches' readings (reworded on 2026-10-26; see the correction above). Two jobs per
325	  case, reported as counts with no rates.
326	- **No valid formal recovery times;** the supplementary observations miss W1, W4 and D2.
327	- **The exclusive window was counted only at the start in both batches.** Since `5ecde71` the count
328	  is recorded at every reading (section 8). It is still a sample: a container that starts and
329	  stops between two readings, within one job, is not seen.
330	- **Missing counts are insufficient evidence.** The later collector reports `other_containers` as
331	  unknown for every batch recorded before `5ecde71`, the preflights included. Condition 4 cannot be
332	  confirmed for them; that is not evidence that another container ran.
333	- **batch-1's export after the restart is supplementary,** taken after a crash recovery and not by
334	  the harness.
335	
336	## 8. Tooling changes after the formal batches (`5ecde71`)
337	
338	- **Containers at every reading:** the harness records, with every host reading (start, before
339	  each job, end), the running containers outside this project, or None when Docker cannot say.
340	  The collector's `other_containers` condition fails a reading with any such container. A missing
341	  count is unknown, which also fails the verdict, as insufficient evidence. It counts for recovery
342	  times only. The count is a sample at each reading, so a container that starts and stops between
343	  two readings is not seen.
344	- **The Q1 line:** the summary no longer reports "jobs whose Q1 verdict is not ok: none" when there
345	  are no Q1 rows; such jobs are unknown and listed apart (`q1_missing`).
346	- **Stale texts:** the harness's docstrings and the collector's `--clock-tolerance` help no longer
347	  describe Part A as unapproved or say that no batch has run.
348	- **Checks:**
349	  - 67 tests passed in the four recovery test files.
350	  - 19 of 19 host and collector mutations were caught, the 5 new ones included.
351	- **Later collector results on the formal records** (computed in memory, not written; the 2,359
352	  files were unchanged):
353	  - batch-1: verdicts as recorded, plus `other_containers` unknown at all 22 readings; its Q1 line
354	    now says that no Q1 rows exist.
355	  - batch-2: correctness valid. Recovery times invalid, because `other_containers` is unknown at
356	    all 32 readings: batch-2 recorded no count. That is insufficient evidence, not a further
357	    violation, and the records hold no trace of the 06:25:08 container. The recorded decision
358	    rests on that container (section 1).
359	- **The preflights:** under the later collector the correctness verdicts are unchanged. Every
360	  preflight's recovery times are invalid, preflight-4's only because `other_containers` is unknown
361	  at its 5 readings, which again is insufficient evidence.
362	- **Part A's approved sections are unchanged;** its section 13 records these changes.
363	
364	## 9. Records
365	
366	In `data/outputs-recovery/formal/`, outside Git:
367	
368	- `plan-544.json`;
369	- `batch-1/`, the harness's records with the collector's outputs (`fcaa645`), and
370	  `batch-1.console.log`;
371	- `batch-1.after-restart/`, the export and `status --check` after the restart;
372	- `batch-1.interruption.txt`, the evidence of 3.1 (the power log's sleep and wake lines, `last`,
373	  the boot time);
374	- `batch-2/`, complete, with the collector's outputs (`fcaa645`), and `batch-2.console.log`;
375	- `batch-2.other-container.txt`, the evidence of 3.2;
376	- `batch-2.decision.txt`, the author's decision of section 1.
377	
378	The live Kafka gate before the formal batches is
379	`data/outputs-recovery/preflight/kafka-live-fcaa645.txt` (27 passed, 0 failed, 0 skipped).
380	
```

## 6. Assistant — 2026-10-28T00:34:27.816Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; grep -n \"^#\" $W/docs/recovery-part-a.md; sed -n 40,135p $W/docs/recovery-part-a.md",
  "description": "Outline Part A and read its case and deadline definitions"
}
```

## 7. User — 2026-10-28T00:34:28.488Z

### Tool result

```
1:# Recovery experiments: Part A, 30 jobs (approved)
29:## 1. Workload
61:## 2. Timing (P2: the defaults of timing.py, no override)
71:## 3. Deadlines (P3)
94:## 4. Predictions
133:## 5. Injection success and misses (harness)
152:## 6. Stop rules and outcomes
173:## 7. Commands (from the repository root of the checkout that ran the plan)
176:# 0. Preconditions: the test window is released; nothing of this project runs
185:# 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results.
186:#    --jobs keeps the order as listed and adds no controls; this list has a C0 at each end
189:# Keep the host awake: on AC power with the lid open (section 12); -s works on AC power only
194:# The job tests and the live pipeline tests against both services, outputs kept with the preflight
204:# 2. Formal batch: only after the author approves Part A. The default plan is the preferred draft:
205:#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json).
206:#    <SEED> is the approved seed (section 10, row 2).
213:# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two
214:#    verdicts, correctness observations and recovery times, and exits 1 unless both are valid: any
215:#    required check that failed or is unknown gives 1 (battery, a closed lid, a missing reading)
218:# 4. Cleanup: the batch itself ends with `docker compose down -v`; check, and recover if it was killed
232:## 8. Runtime
253:## 9. Gaps in the service-only paths: G1–G9, fixed on 2026-10-24
271:## 10. Author decisions
296:## 11. Live preflight, 2026-10-24 and 2026-10-25: functional validation only
439:## 12. A protocol for recovery batches on this 8 GiB Mac
514:## 13. After approval (2026-10-25)
  records stride 21, which only rolling windows use. One job runs windows, spark_pipeline and verify
  (about 35 s of steps at M2's measurements).
- Two workers, A then B, each waited for in the assignment events, and one reconciler.

| Case | Injection | Method and phase |
|---|---|---|
| C0 | none | baseline; measures T |
| W1 | SIGKILL of the owner | fault file, `before_claim` |
| W2 | SIGKILL of the owner | fault file, `after_claim` |
| W3 | SIGKILL of the claiming worker | harness, 3 s into `spark_pipeline` |
| W4 | SIGKILL of the owner | fault file, `after_pipeline` |
| W5a | SIGKILL of the owner | fault file, `after_accept_commit` |
| W5b | SIGKILL of the owner | fault file, `after_accept` |
| W6 | SIGSTOP of the worker until the takeover, then SIGCONT and SIGTERM | harness, mid-step |
| W7 | SIGSTOP of the whole tree for 90 s, then SIGCONT and SIGTERM | harness, mid-step |
| K1 | `docker compose restart kafka` | harness, mid-step |
| K2 | Kafka stopped 30 s around the submit | harness, before the submit |
| D1 | MySQL stopped 30 s | harness, mid-step |
| D2 | MySQL stopped 30 s while the owner holds | fault file `after_pipeline` (hold) |
| X1 | the job id published again, at its claim and after its success | harness |

## 2. Timing (P2: the defaults of timing.py, no override)

| Lease L | Renewal R | Fence margin M | F | Worker tick | Watchdog t_w | Kill grace G |
|---|---|---|---|---|---|---|
| 60 s | 10 s | 10 s | last renewal + 50 s | 1 s | 0.5 s | 7 s (5 + 2) |

| Step limits | Attempt | Session S_k | Heartbeat h | Reconciler P | Publication grace g | Confirmation |
|---|---|---|---|---|---|---|
| 120 / 600 / 300 s | 900 s | 15 s | 3 s | 5 s | 30 s | 10 s |

## 3. Deadlines (P3)

D = ceil5(B + 2S): B is the design's latest start of the next run after the deadline's reference,
and 2S is 70.2 s (twice M2's slowest step sum, 35.1 s). `max_lag_s` is 1 s and the drain limit is D.

| Cases | Reference | B | D |
|---|---|---|---|
| C0, W5a, W5b, K1, X1 | submit (C0), injection | 0 | 75 s |
| W1 | injection | S_k + h + 1 = 19 s | 90 s |
| W2, W3, W4, W6 | injection | L + P = 65 s | 140 s |
| W7 | injection | max(L + P, 90 + 2 t_w + G) = 98 s | 170 s |
| K2 | Kafka's return | g + P + 19 = 54 s | 125 s |
| D1, D2 | MySQL's return | L + P = 65 s | 140 s |

A missed injection takes C0's deadline from its submit. Preflight-2's two C0 jobs took 52.4 and
46.8 s (median 49.6 s), and preflight-4's controls 45.1 and 50.9 s. All four are above the 40 s
assumed but below 70.2 s, so by P3's own rule D is not re-derived; at the median of 49.6 s the
margins shrink from 31–35 s to about 20–25 s. All four come from a host under memory pressure
(section 11), and preflight-2's are planning figures only, since its power and lid were not
recorded. S itself (35.1 s) was measured under host memory pressure too, so D rests on observations
of this host, not on a validated standard: on time and late classify jobs on this host and nothing
more.

## 4. Predictions

The table keeps the drafted assumptions, T = 40 s and restore times of about 20 s; section 11
compares them with what the preflights observed. "Finish by" is the latest finish the design
predicts, B + T, from the deadline's reference; the margin is D minus it.

| Case | Claims / accepted | Detection and window | Finish by | Margin |
|---|---|---|---|---|
| C0 | 1 / 1 | — | T, 40 s | 35 s |
| W1 | 1 / 1 | standby's `delivered`, 12–19 s | 59 s | 31 s |
| W2, W4 | 2 / 1 | reconciler's `requeued`, 60–65 s | 105 s | 35 s |
| W3, W6 | 2 / 1 | `requeued`, 50–65 s | 105 s | 35 s |
| W7 | 2 / 1 | `requeued`, 50–65 s; the replacement waits for the host lock until 98 s | 138 s | 32 s |
| W5a | 1 / 1 | — ; Q3a `no matching report`, by design | — | — |
| W5b | 1 / 1 | — | — | — |
| K1 | 1 / 1 | — (the attempt goes on) | under T | over 35 s |
| K2 | 1 / 1 | reconciler's `published`, within P of Kafka's return | 94 s | 31 s |
| D1 | 1 / 1 if MySQL is back before F, else 2 / 1 | `renewal_failed`; then `renewed` or `requeued` | 105 s | 35 s |
| D2 | 1 / 1 if MySQL is back before F, else 2 / 1 | `retry` of `accept_result`; then `accepted`, or `failed_after_ack` and `requeued` | 105 s | 35 s |
| X1 | 1 / 1 | both duplicates refused as `succeeded` | T | 35 s |

Expected for E1 on all 30 jobs: Q1 `ok`; `status --check` exits 0; no invariant violation; every
accepted result equals the reference run; no overlapping step intervals. Each of these is checked
per job and reported as found.

**Assumptions and uncertainty.**
- T was unmeasured when the table was drafted. The preflights' C0 jobs took 45.1–52.4 s
  (section 3), below 2S (70.2 s); if T exceeds 2S, re-deriving D is the author's option.
- Restore times were unmeasured too; preflight-2 observed Kafka 3.9 s and MySQL 1.6 and 10.8 s
  (section 11). From the stop, F comes 40–50 s later; MySQL returns after 30 s plus its restore.
  D1's and D2's branches therefore depend on the restore, and both branches are valid outcomes.
- A killed worker's dead group member keeps its session for 15 s, so a restart may take about 20 s
  rather than the estimator's 12 s (preflight-2 observed 3.7–5.2 s).
- During K1 and K2, consumers log `consumer_error` and keep polling, with no back-off; the rejoin
  bound of 19 s is assumed to hold.
- X1's first duplicate arrives while its owner runs the job, so it is read only afterwards. Both
  duplicates are therefore refused as `succeeded` (outline 3.1, corrected on 2026-10-24).
- Results are counts per case (k of 2; k of 4 for C0, the two controls included), with no rates.

## 5. Injection success and misses (harness)

- **Fault-file cases** (W1, W2, W4, W5a, W5b, D2): the owner is read from the assignment events,
```

## 8. Assistant — 2026-10-28T00:34:32.101Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; head -1 $W/data/outputs-recovery/formal/batch-3/injections.csv | tr , '\\n' | nl | head -60; grep -n \"overhead_s\\|finish_s\\|reference\\|t_ref\\|restored\\|\\\"ready\\\"\" $W/analysis/collect_recovery_measurements.py | head -40",
  "description": "List injections.csv columns and the collector's time origins"
}
```

## 9. User — 2026-10-28T00:34:33.097Z

### Tool result

```
     1	position
     2	case
     3	job_id
     4	status
     5	missed
     6	injection
     7	worker
     8	t_inj
     9	reference
    10	deadline_s
    11	detection_s
    12	rerun_s
    13	finish_s
    14	overhead_s
    15	claims
    16	accepted
    17	executions
    18	complete_executions
    19	wasted_step_s
    20	fenced_events
    21	timeliness
    22	deadline_met
    23	q1_verdict
    24	q3a_verdict
    25	host_available_bytes
    26	memory_pressure
    27	power_source
    28	lid_closed
    29	other_containers
    30	pageouts_during_bytes
    31	swapins_during_bytes
    32	swapouts_during_bytes
15:    reference/      the reference run, under the launcher
94:FIELDS = ["position", "case", "job_id", "status", "missed", "injection", "worker", "t_inj", "reference", "deadline_s",
95:          "detection_s", "rerun_s", "finish_s", "overhead_s", "claims", "accepted", "executions", "complete_executions",
187:        if span := interval(launcher_record(b.folder / "reference", step)):
188:            intervals.append((*span, f"reference:{step}"))
190:            missing.append(f"reference:{step}")
214:    row = {"detection_s": None, "rerun_s": None, "finish_s": None, "overhead_s": None}
251:        row["finish_s"] = row["overhead_s"] = f"n/a: {NO_OVERHEAD[case]}"
253:        row["finish_s"] = row["overhead_s"] = "unknown: no accepted event"
255:        row["finish_s"] = (accepted["mono"] - start if start is not None
258:            row["overhead_s"] = accepted["mono"] - deadline["t_submit"] - c0_median
260:            row["overhead_s"] = "unknown: no C0 median"
314:    and the tables against the reference run by content."""
318:    reference = next(iter(sorted((b.folder / "reference" / "output").glob("*/*/reference"))), None)
338:        if reference is None:
339:            problems.append("no reference run to compare with")
342:                diff, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(run_folder, table),
591:                   reference=d["reference"], deadline_s=d["deadline_s"])
```

## 10. Assistant — 2026-10-28T00:34:35.440Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; sed -n 200,262p $W/analysis/collect_recovery_measurements.py; grep -n \"def deadline\\|\\\"reference\\\"\\|t_ref\\|deadline_met\\b\" $W/src/etf_risk/jobs/harness.py | head -20",
  "description": "Read how finish and overhead times are computed"
}
```

## 11. User — 2026-10-28T00:34:36.065Z

### Tool result

```
        if latest is not None and start < latest[1]:
            overlaps.append((latest[2], label))
        if latest is None or end > latest[1]:
            latest = (start, end, label)
    verdict = "overlap" if overlaps else "unknown" if missing else "no overlap"
    return {"verdict": verdict, "overlaps": overlaps, "steps_without_interval": missing,
            "note": "monotonic launcher times (4.1)"}


def job_metrics(b: BatchFolder, position: int, case: str, injection: dict, deadline: dict,
                c0_median: float | None) -> dict:
    job_id = deadline["job_id"]
    events = [e for e in b.worker_events() if e.get("job_id") == job_id]
    t_inj, missed = injection.get("t_inj"), injection.get("missed")
    row = {"detection_s": None, "rerun_s": None, "finish_s": None, "overhead_s": None}
    reason = NO_RECOVERY.get(case)
    if missed:
        row.update(detection_s="n/a: injection missed", rerun_s="n/a: injection missed")
    elif reason:
        row.update(detection_s=f"n/a: {reason}", rerun_s=f"n/a: {reason}")
    elif case == "K1":
        row.update(detection_s="n/a for the job: the attempt goes on", rerun_s="n/a: the attempt goes on")
    elif t_inj is not None:
        if case == "W1":
            detection = b.first_after([e for e in named(events, "delivered") if e["worker"] != injection.get("worker")],
                                      t_inj)
        elif case in REQUEUED_DETECTION:
            detection = b.first_after(named(b.reconciler, "requeued", job_id=job_id), t_inj)
        elif case == "K2":
            detection = b.first_after(named(b.reconciler, "published", job_id=job_id), t_inj)
        elif case == "D1":
            detection = b.first_after(named(events, "renewal_failed"), t_inj)
        else:                                                     # D2: a retried acceptance, or none after F
            detection = b.first_after(named(events, "retry", operation="accept_result")
                                      + named(events, "fenced", during="acceptance"), t_inj)
        row["detection_s"] = detection["mono"] - t_inj if detection else "unknown: no detection event"
        before = [e for e in named(events, "claimed") if e["mono"] < t_inj]
        injected = max((e["attempt"] for e in before), default=0)
        rerun = b.first_after([e for e in named(events, "claimed") if e["attempt"] > injected], t_inj)
        if rerun:
            row["rerun_s"] = rerun["mono"] - t_inj
        elif case in ("D1", "D2"):
            row["rerun_s"] = "n/a: the attempt went on"
        else:
            row["rerun_s"] = "unknown: no new claim"
    else:                                                         # the record of the injection lacks its time
        row.update(detection_s="unknown: no injection time", rerun_s="unknown: no injection time")
    accepted = min(named(events, "accepted"), key=lambda e: e["mono"], default=None)
    from_submit = case == "C0" or missed
    start = deadline.get("t_submit") if from_submit else t_inj
    if case in NO_OVERHEAD and not missed:
        row["finish_s"] = row["overhead_s"] = f"n/a: {NO_OVERHEAD[case]}"
    elif accepted is None:
        row["finish_s"] = row["overhead_s"] = "unknown: no accepted event"
    else:
        row["finish_s"] = (accepted["mono"] - start if start is not None
                           else f"unknown: no {'submit' if from_submit else 'injection'} time")
        if deadline.get("t_submit") is not None and c0_median is not None:
            row["overhead_s"] = accepted["mono"] - deadline["t_submit"] - c0_median
        else:
            row["overhead_s"] = "unknown: no C0 median"
    claims = {e["attempt"]: e["run_id"] for e in named(events, "claimed")}
    row["executions"] = len({e["attempt"] for e in named(events, "step_started", step="windows")})
147:def deadline_reference(case: str) -> str:
173:def deadline_seconds(case: str, timing: Timing, settings: Settings) -> float:
1032:                                      worker_id="reference", lock_path=DEFAULT_LOCK, timing=self.timing)
1033:        run_dir = self.out / "reference"
1036:            run_id = "reference"
1041:        marker = processes.marker(self.store_id, "reference", secrets.token_hex(8))
```

## 12. Assistant — 2026-10-28T00:34:41.288Z

I'm working out each case's timing origin from the harness code so the Part B draft compares finish times against deadlines on the same origin.

## 13. Assistant — 2026-10-28T00:34:44.303Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; sed -n 147,172p $W/src/etf_risk/jobs/harness.py; grep -n '\"deadline\"\\|log(\"deadline\\|t_reference\\|t_ref\\b\\|reference_t\\|\"t_deadline\"' $W/src/etf_risk/jobs/harness.py | head; python3 - $W/data/outputs-recovery/formal/batch-3 <<'EOF'\nimport json, sys\nH = [json.loads(l) for l in open(sys.argv[1] + \"/harness.jsonl\")]\nnames = sorted({e[\"event\"] for e in H}); print(names)\nfor e in H:\n    if e[\"event\"] in (\"deadline\", \"deadline_set\", \"deadline_observed\") and e.get(\"job_id\") in (11, 7, 22):\n        print({k: e[k] for k in e if k not in (\"ts\", \"pid\", \"component\", \"batch\", \"clock\", \"code\")})\nEOF",
  "description": "Read the harness's deadline references and deadline records"
}
```

## 14. User — 2026-10-28T00:34:45.399Z

### Tool result

```
def deadline_reference(case: str) -> str:
    """What a job's deadline counts from (4.2): its submit, its injection, or its service's return."""
    return "submit" if case == "C0" else "restored" if case in FROM_RESTORED else "injection"


def bound_to_next_run(case: str, timing: Timing, settings: Settings) -> float:
    """B (P3): the latest the design starts the job's next run, from the deadline's reference.
    K2, D1 and D2 count from their service's return, since how long a restart takes is not
    known and is not inferred."""
    lease, period = timing.lease, RECONCILE_INTERVAL.total_seconds()
    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0     # a member gone, then a poll
    if case in NO_NEW_ATTEMPT:
        return 0.0
    if case == "W1":
        return rejoin
    if case in ("W2", "W3", "W4", "W6"):
        return lease + period
    if case == "W7":                     # the later of the takeover and the end of the stopped tree
        return max(lease + period, settings.w7_stop_s + 2 * timing.watchdog_tick + timing.kill_grace)
    if case == "K2":                     # the grace before a publication, a pass, and the group again
        return PUBLICATION_GRACE.total_seconds() + period + rejoin
    if case in ("D1", "D2"):             # a fenced attempt's lease, then a pass
        return lease + period
    raise ValueError(f"unknown case {case!r}")


988:        self.log.log("deadline", position=position, job_id=job_id, case=case, reference=reference,
1053:            proc.stdin.write((json.dumps({"monotonic": time.monotonic(), "seq": 0, "deadline": deadline}) + "\n").encode())
['armed', 'batch_ended', 'batch_started', 'container_monitor', 'deadline', 'final_snapshot', 'host_state', 'injection', 'job_done', 'observation', 'owner', 'peaks', 'power_log', 'process_started', 'published_again', 'quiescent', 'reference_step', 'restarted', 'services_up', 'spark_scratch', 'submitted']
{'mono': 51381.12248925, 'event': 'deadline', 'position': 7, 'job_id': 7, 'case': 'D1', 'reference': 'restored', 'reference_mono': 51381.122403416, 'deadline_s': 140.0, 'deadline_mono': 51521.122403416, 'max_lag_s': 1.0, 't_submit': 51343.566148916}
{'mono': 51523.024969583, 'event': 'deadline', 'position': 11, 'job_id': 11, 'case': 'K2', 'reference': 'restored', 'reference_mono': 51523.024860958, 'deadline_s': 125.0, 'deadline_mono': 51648.024860958, 'max_lag_s': 1.0, 't_submit': 51492.065771416}
{'mono': 52187.641802333, 'event': 'deadline', 'position': 22, 'job_id': 22, 'case': 'D2', 'reference': 'restored', 'reference_mono': 52187.64171175, 'deadline_s': 140.0, 'deadline_mono': 52327.64171175, 'max_lag_s': 1.0, 't_submit': 52132.56852625}
```

## 15. Assistant — 2026-10-28T00:34:53.633Z

### Tool call: Bash

```
{
  "command": "B=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/data/outputs-recovery/formal/batch-3; ls $B/events | head; head -c 600 $B/crosscheck/Q2.csv; echo; grep -h '\"event\": \"accepted\"' $B/events/* 2>/dev/null | head -1 | cut -c1-300",
  "description": "Inspect batch-3's event files and the Q2 table"
}
```

## 16. User — 2026-10-28T00:34:55.245Z

### Tool result

```
A.jsonl
B.jsonl
reconciler-34697.jsonl
submit.jsonl
case_id,job_id,final_status,status_at_deadline,observation_lag_s,attempt_number,published_at,lease_expires_at,timeliness,deadline_met
C0,1,succeeded,succeeded,-51.651,1,NULL,NULL,on time,yes
C0,10,succeeded,succeeded,-52.539,1,NULL,NULL,on time,yes
C0,20,succeeded,succeeded,-52.133,1,NULL,NULL,on time,yes
C0,30,succeeded,succeeded,-51.493,1,NULL,NULL,on time,yes
D1,7,succeeded,succeeded,-133.886,1,NULL,NULL,on time,yes
D1,8,succeeded,succeeded,-133.38,1,NULL,NULL,on time,yes
D2,22,succeeded,succeeded,-139.482,1,NULL,NULL,on time,yes
D2,28,succeeded,succeeded,-139.994,1,NULL,NULL,on tim
{"ts": "2026-10-27T21:24:50.822423+00:00", "mono": 50970.654455291, "pid": 34703, "component": "worker", "event": "accepted", "store_id": "884bf4201ebc08805c66f97111a77495", "worker_id": "A", "job_id": 1, "attempt": 1, "digest": "9e6bfb1735241ed4dab0d738c8007b74a99e964df0518b868efabea3763cfa79"}
```

## 17. Assistant — 2026-10-28T00:35:11.277Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_origins.py",
  "content": "\"\"\"Batch-3's finish times on explicit origins: submit, injection and the deadline's reference.\"\"\"\nimport csv\nimport json\nimport statistics\nimport sys\nfrom pathlib import Path\n\nfolder = Path(sys.argv[1])\nharness = [json.loads(line) for line in (folder / \"harness.jsonl\").read_text().splitlines() if line.strip()]\nworkers = [json.loads(line) for name in (\"A\", \"B\") for line in (folder / \"events\" / f\"{name}.jsonl\").read_text().splitlines()\n           if line.strip()]\ndeadlines = {e[\"job_id\"]: e for e in harness if e[\"event\"] == \"deadline\"}\ninjections = {e[\"job_id\"]: e for e in harness if e[\"event\"] == \"injection\"}\naccepted = {}\nfor e in workers:\n    if e[\"event\"] == \"accepted\":\n        accepted[e[\"job_id\"]] = min(accepted.get(e[\"job_id\"], e[\"mono\"]), e[\"mono\"])\nq2 = {int(r[\"job_id\"]): r for r in csv.DictReader(open(folder / \"crosscheck\" / \"Q2.csv\"))}\nrows = list(csv.DictReader(open(folder / \"injections.csv\")))\n\nprint(\"pos case ref       submit->acc inj->acc ref-inj  ref->acc   D   slack  at_deadline  outage(stop->return)\")\nfor r in rows:\n    job = int(r[\"job_id\"])\n    d, inj, acc = deadlines[job], injections.get(job, {}), accepted.get(job)\n    t_inj = inj.get(\"t_inj\")\n    fmt = lambda x: f\"{x:8.1f}\" if isinstance(x, float) else f\"{'-':>8}\"\n    sub_acc = acc - d[\"t_submit\"] if acc else None\n    inj_acc = acc - t_inj if acc and t_inj else None\n    ref_inj = d[\"reference_mono\"] - t_inj if t_inj else None\n    ref_acc = acc - d[\"reference_mono\"] if acc else None\n    slack = d[\"deadline_mono\"] - acc if acc else None\n    outage = inj[\"restored\"] - t_inj if \"restored\" in inj else (inj[\"ready\"] - t_inj if \"ready\" in inj else None)\n    print(f\"{r['position']:>3} {r['case']:4} {d['reference']:9} {fmt(sub_acc)} {fmt(inj_acc)} {fmt(ref_inj)} {fmt(ref_acc)}\"\n          f\" {d['deadline_s']:5.0f} {fmt(slack)}  {q2[job]['status_at_deadline']:11} {fmt(outage)}\")\n\nc0 = [accepted[int(r[\"job_id\"])] - deadlines[int(r[\"job_id\"])][\"t_submit\"] for r in rows if r[\"case\"] == \"C0\"]\nprint(\"C0 submit->accepted:\", [round(x, 1) for x in c0], \"median\", round(statistics.median(c0), 2))\nslacks = [deadlines[j][\"deadline_mono\"] - accepted[j] for j in accepted if j in deadlines]\nprint(\"slack min/max:\", round(min(slacks), 1), round(max(slacks), 1))\n"
}
```

## 18. User — 2026-10-28T00:35:12.134Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_origins.py (file state is current in your context — no need to Read it back)
```

## 19. Assistant — 2026-10-28T00:35:12.966Z

### Tool call: Bash

```
{
  "command": "python3 -I /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_origins.py ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/data/outputs-recovery/formal/batch-3",
  "description": "Compute batch-3 finish times from each timing origin"
}
```

## 20. User — 2026-10-28T00:35:13.729Z

### Tool result

```
pos case ref       submit->acc inj->acc ref-inj  ref->acc   D   slack  at_deadline  outage(stop->return)
  1 C0   submit        23.0        -        -     23.0    75     52.0  succeeded          -
  2 W5a  injection        -        -      0.0        -    75        -  succeeded          -
  3 W2   injection     84.1     83.1      0.0     83.1   140     56.9  succeeded          -
  4 W7   injection    118.5    112.4      0.0    112.4   170     57.6  succeeded          -
  5 W3   injection     86.1     79.9      0.0     79.9   140     60.1  succeeded          -
  6 W5a  injection        -        -      0.0        -    75        -  succeeded          -
  7 D1   restored      43.7     37.3     31.2      6.1   140    133.9  succeeded       31.2
  8 D1   restored      44.1     37.8     31.2      6.5   140    133.5  succeeded       31.2
  9 W5b  injection     22.0     -0.0      0.0     -0.0    75     75.0  succeeded          -
 10 C0   submit        22.5        -        -     22.5    75     52.5  succeeded          -
 11 K2   restored      67.7     68.6     31.8     36.7   125     88.3  succeeded       31.8
 12 X1   injection     23.5     22.0      0.0     22.0    75     53.0  succeeded          -
 13 W2   injection     86.2     85.2      0.0     85.2   140     54.8  succeeded          -
 14 W3   injection     86.2     80.1      0.0     80.1   140     59.9  succeeded          -
 15 K1   injection     23.5     17.2      0.0     17.2    75     57.8  succeeded        3.3
 16 W6   injection     89.5     82.9      0.0     82.9   140     57.1  succeeded          -
 17 W6   injection     87.8     81.7      0.0     81.7   140     58.3  succeeded          -
 18 X1   injection     23.0     22.0      0.0     22.0    75     53.0  succeeded          -
 19 W5b  injection     22.5     -0.0      0.0     -0.0    75     75.0  succeeded          -
 20 C0   submit        22.9        -        -     22.9    75     52.1  succeeded          -
 21 W1   injection     37.2     36.2      0.0     36.2    90     53.8  succeeded          -
 22 D2   restored      55.2     31.4     31.2      0.2   140    139.8  succeeded       31.2
 23 W7   injection    118.5    112.5      0.0    112.5   170     57.5  succeeded          -
 24 K1   injection     22.7     16.3      0.0     16.3    75     58.7  succeeded        3.1
 25 W4   injection    108.5     85.7      0.0     85.7   140     54.3  succeeded          -
 26 W1   injection     36.1     35.2      0.0     35.2    90     54.8  succeeded          -
 27 W4   injection    108.3     86.2      0.0     86.2   140     53.8  succeeded          -
 28 D2   restored      53.9     31.0     31.2     -0.1   140    140.1  succeeded       31.2
 29 K2   restored      68.0     68.8     31.9     36.9   125     88.1  succeeded       31.9
 30 C0   submit        23.1        -        -     23.1    75     51.9  succeeded          -
C0 submit->accepted: [23.0, 22.5, 22.9, 23.1] median 22.91
slack min/max: 51.9 140.1
```

## 21. Assistant — 2026-10-28T00:35:34.167Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; grep -n '\"restored\"\\|restored=\\|ready=\\|def wait_service\\|def outage\\|def restore' $W/src/etf_risk/jobs/harness.py | head; grep -n \"restored\\b\\|service's return\" $W/docs/recovery-part-a.md | head -8",
  "description": "Find what the harness records as a service's return"
}
```

## 22. User — 2026-10-28T00:35:35.032Z

### Tool result

```
149:    return "submit" if case == "C0" else "restored" if case in FROM_RESTORED else "injection"
888:                    "t_inj": t_inj, "restored": self.wait_ready("mysql")}
908:            return {"kind": "service_stop", "service": "mysql", "t_inj": t_inj, "restored": self.wait_ready("mysql")}
971:                injection["restored"] = self.wait_ready("kafka")
984:            reference_mono = injection["restored"] if reference == "restored" else injection["t_inj"]
```

## 23. Assistant — 2026-10-28T00:35:37.133Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; grep -n \"def wait_ready\" -A 14 $W/src/etf_risk/jobs/harness.py; sed -n 880,910p $W/src/etf_risk/jobs/harness.py",
  "description": "Read the harness's readiness wait and the MySQL outage code"
}
```

## 24. User — 2026-10-28T00:35:37.873Z

### Tool result

```
545:    def wait_ready(self, service: str) -> float:
546-        """Until the service works again (services.py); the harness's mono at that moment."""
547-        check = {"mysql": lambda: self.services.mysql_ready(self.mysql_url),
548-                 "kafka": lambda: self.services.kafka_ready(self.bootstrap)}[service]
549-        self.services.wait_until_ready(service, check, timeout=180)
550-        return time.monotonic()
551-
552-    def services_up(self) -> None:
553-        existing = subprocess.run(["docker", "compose", "-f", str(self.services.COMPOSE_FILE), "ps", "-a", "-q"],
554-                                  capture_output=True, text=True, timeout=60).stdout.split()
555-        if existing:
556-            raise RuntimeError("this project's containers exist already; a batch starts on fresh ones")
557-        self.services_started = True
558-        self.log.log("services_up", seconds=self.compose("up", "-d", "--wait", "mysql", "kafka"),
559-                     others=self.services.other_containers())
            event = self.wait_fault(armed, job_id, "after_pipeline")
            self.read_peaks(closes="mysql stop")
            t_inj = time.monotonic()
            self.compose("stop", "mysql")
            release.touch()                                  # acceptance meets the outage
            time.sleep(max(0.0, t_inj + s.outage_s - time.monotonic()))
            self.compose("start", "mysql")
            return {"kind": "hold+service_stop", "worker": armed, "service": "mysql", "held_mono": event["mono"],
                    "t_inj": t_inj, "restored": self.wait_ready("mysql")}
        if case in MID_STEP:
            claim = self.at_mid_step(job_id)
            worker, t_inj = claim["worker"], time.monotonic()
            if case == "W3":
                self.procs[worker].kill()                    # SIGKILL
                return {"kind": "sigkill", "worker": worker, "attempt": claim["attempt"], "phase": "spark_pipeline",
                        "t_inj": t_inj}
            if case in ("W6", "W7"):
                return self.inject_stop(case, job_id, claim, t_inj)
            service = "kafka" if case == "K1" else "mysql"
            self.read_peaks(closes=f"{service} {'restart' if case == 'K1' else 'stop'}")
            t_inj = time.monotonic()
            if case == "K1":
                seconds = self.compose("restart", "kafka")
                return {"kind": "service_restart", "service": "kafka", "t_inj": t_inj, "seconds": seconds,
                        "ready": self.wait_ready("kafka")}
            self.compose("stop", "mysql")
            time.sleep(max(0.0, t_inj + s.outage_s - time.monotonic()))
            self.compose("start", "mysql")
            return {"kind": "service_stop", "service": "mysql", "t_inj": t_inj, "restored": self.wait_ready("mysql")}
        if case == "X1":
            claim = self.wait_for(lambda: self.claim_of(job_id), s.phase_timeout_s, f"job {job_id}'s claim")
```

## 25. Assistant — 2026-10-28T00:35:41.222Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; grep -n \"E2\\|batch-2\\|batch-3\\|recovery-part-b\\|outstanding\\|recovery time\" $W/README.md | head -40",
  "description": "Find E2 status lines in the README"
}
```

## 26. User — 2026-10-28T00:35:41.889Z

### Tool result

```
24:| Optional systems extension: MySQL job table, Kafka job queue, Redis result cache ([spec §11](docs/spec.md)) | **In progress, not complete**: the outstanding items in the rows below |
26:| Extension: recovery study, E1 and E2 ([docs/recovery-part-a.md](docs/recovery-part-a.md), [docs/recovery-part-b.md](docs/recovery-part-b.md)) | Documented: E1 has supporting correctness observations; **valid formal E2 recovery-time evidence is outstanding** |
80:     protocol), [docs/recovery-part-b.md](docs/recovery-part-b.md) (the formal batches and
493:       [docs/recovery-part-b.md](docs/recovery-part-b.md));
502:     - valid formal E2 recovery-time evidence: both formal batches were invalid for timing;
```

## 27. Assistant — 2026-10-28T00:35:43.832Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; sed -n 18,32p $W/README.md; echo ....; sed -n 74,86p $W/README.md; echo ....; sed -n 470,506p $W/README.md",
  "description": "Read the README's status rows and remaining-work section"
}
```

## 28. User — 2026-10-28T00:35:44.566Z

### Tool result

```
| Docker image for the pipeline | Implemented |
| Stride experiment: runtime and memory at strides 21, 14 and 7 ([docs/experiments.md](docs/experiments.md)) | Complete; drift detected, stride 3 exploratory only |
| Shuffle-partition experiment: three Spark partition settings at stride 7 ([docs/partition-experiment.md](docs/partition-experiment.md)) | Complete; B (200 partitions, coalescing off) slower than A and C; no clear memory difference; outputs within tolerance |
| Pandas baseline: the Spark pipeline against a single-process pandas implementation, end to end, at stride 7 ([docs/pandas-baseline.md](docs/pandas-baseline.md)) | Complete; pandas had a 41.8% shorter median wall time and a 26.6% lower median peak total RSS; outputs within tolerance |
| Caching experiment: no cache, the window-member rows, and those plus the four read-back tables, at stride 7 ([docs/caching-experiment.md](docs/caching-experiment.md)) | Complete; no clear difference in runtime or peak memory; outputs within tolerance |
| Figures and final write-up: twelve figures drawn from the result files, the results write-up and a demo ([docs/results.md](docs/results.md), [docs/demo.md](docs/demo.md)) | Complete; figure numbers checked against the documented values, conclusions approved by the author; eight of the figures need the data under `data/`, which is not in Git |
| Optional systems extension: MySQL job table, Kafka job queue, Redis result cache ([spec §11](docs/spec.md)) | **In progress, not complete**: the outstanding items in the rows below |
| Extension: job table, Kafka delivery and reconciler, and a worker running the real pipeline ([docs/job-table.md](docs/job-table.md), [docs/job-queue.md](docs/job-queue.md), [docs/worker-pipeline.md](docs/worker-pipeline.md)) | Implemented; tested on SQLite and against MySQL and Kafka. The MySQL and Kafka container limits held in one isolated check under host memory pressure; **the native processes' memory is not validated** |
| Extension: recovery study, E1 and E2 ([docs/recovery-part-a.md](docs/recovery-part-a.md), [docs/recovery-part-b.md](docs/recovery-part-b.md)) | Documented: E1 has supporting correctness observations; **valid formal E2 recovery-time evidence is outstanding** |
| Extension: Redis result cache for the three summary queries ([docs/result-cache.md](docs/result-cache.md)) | Implemented: accepted and registered runs only; falls back to Spark when Redis fails |
| Extension: result-cache experiment, E3 ([docs/result-cache-experiment.md](docs/result-cache-experiment.md), [docs/result-cache-part-b.md](docs/result-cache-part-b.md)) | Complete: one valid formal batch of host-specific paired latency observations, not a general performance claim |
| Test suite | **Open**: two intermittent failures of `tests/test_baseline_collector.py`, with the cause unresolved ([spec §10](docs/spec.md)) |

## Reading guide

....
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
....
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
     - the result cache ([docs/result-cache.md](docs/result-cache.md));
     - its experiment, E3, with one valid formal batch on this Mac
       ([docs/result-cache-experiment.md](docs/result-cache-experiment.md),
       [docs/result-cache-part-b.md](docs/result-cache-part-b.md)). Against the identical
       request in a warm Spark session, a hit took a median 5.4 ms instead of 0.132 s. Blocks
       at 0%, 50% and 90% hits took a median 1.04, 0.51 and 0.14 times their controls' time.
       These are host-specific paired observations.
   - **Outstanding:**
     - valid formal E2 recovery-time evidence: both formal batches were invalid for timing;
     - a representative validation of the native processes' memory: the container limits
       held, but under host memory pressure;
     - the cause of two intermittent failures of `tests/test_baseline_collector.py`
       ([spec §10](docs/spec.md)).
```

## 29. Assistant — 2026-10-28T00:35:47.177Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; grep -n \"E2\\b\\|E2 \\|batch-2\\|batch-3\\|recovery-part-b\\|recovery-time\\|recovery time\" $W/docs/spec.md | head -40",
  "description": "Find E2 status lines in the spec"
}
```

## 30. User — 2026-10-28T00:35:48.027Z

### Tool result

```
20:  [recovery-part-b.md](recovery-part-b.md)), with supporting correctness observations for E1;
24:Outstanding (§11, open items): valid formal E2 recovery-time evidence, a representative
37:| Extension (optional) | Job queue (MySQL job table, Kafka), result cache (Redis), Docker Compose; recovery and caching experiments (§11) | **In progress**: the job queue: the MySQL job table, Kafka delivery and the reconciler ([job-table.md](job-table.md), [job-queue.md](job-queue.md)), and a worker running the real pipeline ([worker-pipeline.md](worker-pipeline.md)); the recovery study documented ([recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)): E1 has supporting correctness observations, and valid formal E2 recovery-time evidence remains outstanding; the Redis result cache ([result-cache.md](result-cache.md)) and its experiment E3, with one valid formal batch ([result-cache-experiment.md](result-cache-experiment.md), [result-cache-part-b.md](result-cache-part-b.md)). **Outstanding:** valid formal E2 recovery-time evidence; a representative validation of the native processes' memory (the container limits held under host memory pressure); two unresolved intermittent baseline-collector test failures (§10) |
247:    B --> E2[shuffle-partition experiment<br/>batch CSV and criteria]
254:    E2 --> F
709:| Systems extension | MySQL job table with guarded state transitions, attempt tokens and leases, a store id, and run digests recorded at acceptance ([job-table.md](job-table.md)); a worker running windows → spark_pipeline → verify with renewals, an absolute-deadline watchdog, a host execution lock, process-tree cleanup, reconnects and the job commands ([worker-pipeline.md](worker-pipeline.md)); Kafka delivery with confirmed publication and manual commits, and the reconciler ([job-queue.md](job-queue.md)); MySQL 8.4.13 and Kafka 4.3.1 in Compose for the integration tests; the recovery study (E1, E2): its harness, collector and cross-check SQL, with two formal batches documented ([recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)), and E1 has supporting correctness observations; the Redis result cache for the three summary queries: Redis 8.10.2 in Compose, served only for accepted job runs and registered historical runs, with a fallback to Spark when Redis fails ([result-cache.md](result-cache.md)); the result-cache experiment E3: its driver, collector and session helpers, and one valid formal batch ([result-cache-experiment.md](result-cache-experiment.md), [result-cache-part-b.md](result-cache-part-b.md)) | outstanding: valid formal E2 recovery-time evidence; a representative validation of the native processes' memory; the cause of two intermittent baseline-collector test failures (§10) |
710:| Documentation | README, [data-sources.md](data-sources.md), this specification, [experiments.md](experiments.md), [partition-experiment.md](partition-experiment.md), [pandas-baseline.md](pandas-baseline.md), [caching-experiment.md](caching-experiment.md), [job-table.md](job-table.md), [job-queue.md](job-queue.md), [worker-pipeline.md](worker-pipeline.md), [recovery-experiments.md](recovery-experiments.md), [recovery-sql.md](recovery-sql.md), [recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md), [result-cache.md](result-cache.md), [result-cache-experiment.md](result-cache-experiment.md), [result-cache-part-b.md](result-cache-part-b.md), [host-counters-correction.md](host-counters-correction.md), [results.md](results.md), [demo.md](demo.md), [measurements/README.md](measurements/README.md), [AI-usage logs](ai-usage/README.md) | design decisions |
791:- the recovery study (E1, E2): its harness, collector and cross-check, two formal
793:  [recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)).
794:  E1 has supporting correctness observations; valid formal E2 recovery-time
857:- **E2.** After a worker crash (before or after its claim), a broker restart or a
868:- Recovery (E1, E2): each failure case is injected on purpose; detection and
869:  recovery times, executions per job, accepted results per job and lost jobs are
870:  recorded. Documented in [recovery-part-b.md](recovery-part-b.md): E1 has
871:  supporting correctness observations, and valid formal E2 recovery-time evidence
971:section 9; [recovery-part-b.md](recovery-part-b.md), section 7). The result
987:- **E2.** There is no valid formal recovery-time evidence. Both formal batches
990:  ([recovery-part-b.md](recovery-part-b.md)).
997:- **Done on 2026-10-27, toward closing E2:**
1002:    fails its recovery times, and a missing or failed monitor counts as unknown.
```

## 31. Assistant — 2026-10-28T00:35:50.152Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; sed -n 12,30p $W/docs/spec.md; echo ....; sed -n 785,800p $W/docs/spec.md; echo ....; sed -n 852,875p $W/docs/spec.md; echo ....; sed -n 960,1005p $W/docs/spec.md",
  "description": "Read the spec's E2 status passages"
}
```

## 32. User — 2026-10-28T00:35:50.855Z

### Tool result

```
- the figures, results write-up and demo of Stage 4 ([results.md](results.md), [demo.md](demo.md)).

**In progress: an optional systems extension with MySQL, Kafka and Redis (§11).** Implemented so
far:
- the job queue: the job table, Kafka delivery and the reconciler ([job-table.md](job-table.md),
  [job-queue.md](job-queue.md)), and a worker that runs the real pipeline under a watchdog and a
  host execution lock ([worker-pipeline.md](worker-pipeline.md));
- the recovery study, documented ([recovery-part-a.md](recovery-part-a.md),
  [recovery-part-b.md](recovery-part-b.md)), with supporting correctness observations for E1;
- the Redis result cache ([result-cache.md](result-cache.md)), and its experiment E3, with one
  valid formal batch ([result-cache-part-b.md](result-cache-part-b.md)).

Outstanding (§11, open items): valid formal E2 recovery-time evidence, a representative
validation of the native processes' memory, and two unresolved intermittent failures of the
baseline collector's tests (§10).
Every section separates what is **implemented** from what is **planned**.
Planned parts describe intentions, not results, and may change when each stage
is reviewed.

....
  ([job-table.md](job-table.md));
- Kafka delivery with the reconciler ([job-queue.md](job-queue.md));
- a worker that runs the real pipeline: renewals, an absolute-deadline watchdog,
  a host execution lock, process-tree cleanup, reconnects, the run digest
  recorded at acceptance, and the job commands
  ([worker-pipeline.md](worker-pipeline.md));
- the recovery study (E1, E2): its harness, collector and cross-check, two formal
  batches and their results ([recovery-experiments.md](recovery-experiments.md),
  [recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)).
  E1 has supporting correctness observations; valid formal E2 recovery-time
  evidence remains outstanding;
- the result cache for the three summary queries: which runs may be served,
  the result's identity, the fallback when Redis fails, and its tests
  ([result-cache.md](result-cache.md)). Its experiment, E3, ran one valid formal batch
  ([result-cache-experiment.md](result-cache-experiment.md),
  [result-cache-part-b.md](result-cache-part-b.md)): host-specific paired latency
....

**Engineering questions**

- **E1.** Does each job accept at most one result, and does every successfully
  completed job have exactly one, even when jobs execute more than once?
- **E2.** After a worker crash (before or after its claim), a broker restart or a
  database restart, how long until the job runs again and finishes, and is any
  job lost or accepted twice?
- **E3.** How much latency does a result cache save for repeated summary queries
  compared with a warm Spark session, at which hit rates, and what happens when
  Redis is down?

**Experiments**

- An accepted result counts as correct when its run passes every check (§6) and
  matches a reference run by content (Parquet files differ in bytes between runs).
- Recovery (E1, E2): each failure case is injected on purpose; detection and
  recovery times, executions per job, accepted results per job and lost jobs are
  recorded. Documented in [recovery-part-b.md](recovery-part-b.md): E1 has
  supporting correctness observations, and valid formal E2 recovery-time evidence
  remains outstanding.
- Result cache (E3): latency of a new Spark process, a warm Spark session and a
  Redis hit, at hit rates set by the workload; the fallback to Spark with Redis
  stopped. Documented in [result-cache-part-b.md](result-cache-part-b.md): one valid
....
recovery experiments and the result cache; each stops for review. The Docker
image, the Compose services, the job table, the worker and the reconciler are
written with Claude Code; the cache logic by the project author, with tutoring.
The experiments were first planned as the author's too. At the author's decision
of 2026-10-24, the recovery
experiments' tooling (the session harness, its collector, assignment events,
code identity at launch and the fault hooks) is written with Claude Code too.
The recovery experiments themselves are contributed by both the author and
Claude Code: Claude Code proposed the design, ran the batches at the author's
instruction and drafted the answers, and the author made every decision and
approval, the answers included ([recovery-experiments.md](recovery-experiments.md),
section 9; [recovery-part-b.md](recovery-part-b.md), section 7). The result
cache follows the same split: the project author wrote the cache logic
(`cache.py`) and moved their SQL into `summary.py`, with tutoring; Claude Code
wrote the Redis service and client, the resolver and registry, `summary.py`'s
request flow, the scaffold, the tests and the mutation checks. Claude Code
proposed the designs, and the author made every decision and approval
([result-cache.md](result-cache.md)). The result-cache experiment E3 follows the
recovery experiments' arrangement, and is contributed by both:
- Claude Code proposed its design, wrote its tooling, ran the dry and functional
  checks, and drafted Part A, Part B and the answer;
- the author made every decision and approval, the protocol and the answer
  included, and ran the prepared dry runs and the formal batch
  ([result-cache-experiment.md](result-cache-experiment.md),
  [result-cache-part-b.md](result-cache-part-b.md)).

**Open items.** The extension is not complete.
- **E2.** There is no valid formal recovery-time evidence. Both formal batches
  were invalid for timing: one stopped when the host restarted, and in the other a
  container of another project broke the exclusive window
  ([recovery-part-b.md](recovery-part-b.md)).
- **Memory.** The native processes' memory has not been validated
  representatively. The MySQL and Kafka container limits held in one isolated
  check, but under host memory pressure, which also made the native figures
  unrepresentative (above).
- **Tests.** The cause of two intermittent failures of the baseline collector's
  tests is unresolved (§10).
- **Done on 2026-10-27, toward closing E2:**
  - **The page counters,** renamed in M3's code: the host readings record `vm_stat`'s four
    counters by their own names, and older records are read as page counts
    ([host-counters-correction.md](host-counters-correction.md), section 7).
  - **A whole-batch container monitor:** any other project's container event during a batch
    fails its recovery times, and a missing or failed monitor counts as unknown.
  - **Sleep and wake evidence** from the power log, recorded as evidence only
    ([recovery-part-a.md](recovery-part-a.md), section 13).
  - **Before a new formal batch:** a C0–D1–C0 preflight, once the test window is free.
```

## 33. Assistant — 2026-10-28T00:36:14.248Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; sed -n 514,530p $W/docs/recovery-part-a.md; echo ....; sed -n 560,598p $W/docs/recovery-part-a.md",
  "description": "Read Part A section 13's preamble and batch-3 item"
}
```

## 34. User — 2026-10-28T00:36:14.925Z

### Tool result

```
## 13. After approval (2026-10-25)

_Added after the formal batches. Sections 1–12 are unchanged as approved, except the wording
corrected on 2026-10-26. The items dated 2026-10-27 change the tooling and condition 4's
monitoring, at the author's decision._

- **The formal batches.** batch-1 stopped when the host restarted. batch-2, the one rerun of
  row 11, completed. The author kept batch-2's correctness observations valid and ruled its
  recovery times invalid, because another project's container broke the exclusive window
  (condition 4). The results are in [recovery-part-b.md](recovery-part-b.md).
- **Condition 4's containers.** As approved, other containers were counted at a batch's start only.
  Since `5ecde71` the harness also records the count at every host reading, and the collector
  fails recovery times on any such container. The count is a sample: a container that starts and
  stops between two readings is not seen.
- **Earlier batches under the later collector.** No batch before `5ecde71` recorded the count, so
  the later collector reports `other_containers` as unknown for all of them. Their recovery times
  come out invalid, preflight-4's for that reason alone; their correctness verdicts are unchanged.
....
- **Sleep and wake evidence (2026-10-27).** At its end, a batch records the Sleep, Wake and
  DarkWake entries of `pmset -g log` during the batch: their times and kinds, never the reasons.
  It also records whether the log reaches back to the batch's start. The evidence is reported
  beside the clock and lid checks, never as a gate, and a batch without it says so.
- **Formal batch-3 (2026-10-27, the author's decision; amends row 11 of section 10).**
  - **What is allowed.** One more formal batch, `formal/batch-3`, beyond row 11's one rerun, which
    batch-2 used. If batch-3 is invalid or stops early, it is kept and reported in full, and the
    formal batches stop. No further formal batch runs without a new decision. batch-1, batch-2 and
    batch-3 are reported side by side.
  - **The plan:** `formal/plan-544.json`, unchanged (seed 544; SHA-256 `c74b125e…5ffa7b6`).
    Regenerated at the frozen code, it gives the same 30 jobs in the same order with the same
    settings.
  - **The code is frozen at `4fc550e`** for `src`, `analysis`, `tests`, `pyproject.toml` and
    `uv.lock`, which replaces row 13's `fcaa645` for batch-3. Later commits change only documents
    and the session tooling below, which the batch does not run.
  - **Its verification:**
    - the full offline suite on `12c925d` (1078 passed, 38 skipped for live services, 0 failed);
    - a live C0–D1–C0 preflight on `12c925d`, valid on every check
      (`preflight/20261027T191959Z-e2-c0-d1-c0`);
    - then `4fc550e`.
  - **An exception to row 11's preflight-first rule, at the author's decision.** `4fc550e` changed
    one thing after that preflight: container events keep only the action's verb, never the
    command Docker appends, so that no command line of another project's container is recorded.
    It got no new live preflight and no new full suite. Its verification:
    - two regression tests with a private-looking value, absent from what is recorded;
    - the focused suites of the shared monitor, the recovery tooling and the result-cache
      experiment, 205 passed;
    - 6 of 6 mutation checks caught, among them one that restores the full action text.
  - **The session:** `docs/recovery-batch-3.zsh`, run from Terminal with the editor and other
    applications closed. It refuses to start unless all of these hold:
    - the code equals `4fc550e`, the worktree is clean and the plan is unchanged;
    - the batch folder is new;
    - no container of this project exists and no other project's container runs;
    - no test, job or Spark process runs;
    - AC power, and the lid open.

    It runs with `pipefail`, and collects the batch even when the batch ends with an error.
  - **After the session:** `docs/verify_frozen_code.py` confirms that every code record of the
    batch matches `4fc550e`, with a clean worktree and seed 544.
```

## 35. Assistant — 2026-10-28T00:36:29.344Z

I have the timing origins. Now gathering batch-3's per-job correctness counts and host readings in the same shape as batch-2's tables.

## 36. Assistant — 2026-10-28T00:36:41.499Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_facts.py",
  "content": "\"\"\"Batch-3's correctness counts, host readings and liveness, in Part B's shapes.\"\"\"\nimport collections\nimport csv\nimport json\nimport sys\nfrom pathlib import Path\n\nfolder = Path(sys.argv[1])\nvalidity = json.loads((folder / \"validity.json\").read_text())\noutcomes = validity[\"outcomes\"]\nharness = [json.loads(line) for line in (folder / \"harness.jsonl\").read_text().splitlines() if line.strip()]\nrows = list(csv.DictReader(open(folder / \"injections.csv\")))\nproblems = {a[\"job_id\"]: a[\"problems\"] for a in outcomes[\"accepted_attempts\"]}\n\nprint(\"pos case claims accepted exec(complete) q1 q3a reference wasted_step_s fenced\")\nfor r in rows:\n    print(r[\"position\"], r[\"case\"], r[\"claims\"], r[\"accepted\"], f\"{r['executions']}({r['complete_executions']})\",\n          r[\"q1_verdict\"], r[\"q3a_verdict\"], \"clean\" if problems.get(int(r[\"job_id\"])) == [] else problems.get(int(r[\"job_id\"])),\n          r[\"wasted_step_s\"], r[\"fenced_events\"])\nprint(\"claimed twice:\", sum(r[\"claims\"] == \"2\" for r in rows), \"| executed twice:\", sum(r[\"executions\"] == \"2\" for r in rows),\n      \"| two complete executions:\", [r[\"case\"] for r in rows if r[\"complete_executions\"] == \"2\"])\nprint(\"accepted attempts:\", len(problems), \"with problems:\", {k: v for k, v in problems.items() if v})\n\nhosts = [e for e in harness if e[\"event\"] == \"host_state\"]\nGiB = 2 ** 30\nprint(\"readings:\", len(hosts), collections.Counter(h.get(\"point\", h.get(\"when\")) for h in hosts).most_common(4))\nprint(\"power:\", collections.Counter(h[\"power_source\"] for h in hosts), \"| lid_closed:\", collections.Counter(h[\"lid_closed\"] for h in hosts))\nprint(\"pressure:\", collections.Counter(h[\"memory_pressure\"] for h in hosts))\nprint(\"other containers:\", collections.Counter(str(h.get(\"other_containers\")) for h in hosts))\navail = [h[\"available_bytes\"] / GiB for h in hosts]\nswap = [h[\"swap_used_bytes\"] / GiB for h in hosts]\nprint(f\"available {min(avail):.2f}-{max(avail):.2f} GiB | swap in use {min(swap):.2f}-{max(swap):.2f} GiB\")\nhost = outcomes[\"host_state\"]\nprint({k: (round(v / 2 ** 20, 1) if isinstance(v, int) else v) for k, v in host.items()})\nprint(\"peaks:\", {s: (round(p[\"peak_bytes\"] / 2 ** 20), round(p[\"limit_bytes\"] / 2 ** 20), round(100 * p[\"fraction\"])) for s, p in outcomes[\"batch_peaks\"].items()})\nprint(\"liveness:\", outcomes[\"liveness\"])\nprint(\"nothing_left:\", outcomes[\"nothing_left\"])\nclock = validity[\"validity\"][\"clock\"]\nprint(\"clock:\", {k: clock[k] for k in clock if k != \"passed\"})\nstarted = [e for e in harness if e[\"event\"] == \"batch_started\"][0]\nended = [e for e in harness if e[\"event\"] == \"batch_ended\"][-1]\nprint(\"wall:\", started[\"clock\"][\"ts\"], \"->\", ended[\"clock\"][\"ts\"], \"| ended:\", {k: ended[k] for k in ended if k in (\"stop_reason\", \"exit\", \"error\")})\nsnap = [e for e in harness if e[\"event\"] == \"final_snapshot\"]\nprint(\"final snapshot:\", json.dumps({k: snap[0][k] for k in snap[0] if k not in (\"ts\", \"pid\", \"component\", \"batch\", \"clock\", \"code\", \"mono\")})[:400] if snap else None)\nfp = validity[\"validity\"][\"fingerprints_agree\"]\nprint(\"fingerprints:\", json.dumps(fp)[:400])\nprint(\"cleanup.txt:\", (folder / \"cleanup.txt\").read_text()[:300].replace(\"\\n\", \" | \"))\nmonitor = [e for e in harness if e[\"event\"] == \"container_monitor\"]\nprint(\"monitor:\", {k: monitor[0][k] for k in monitor[0] if k in (\"error\", \"events\", \"other_project_events\")})\n"
}
```

## 37. User — 2026-10-28T00:36:42.463Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_facts.py (file state is current in your context — no need to Read it back)
```

## 38. Assistant — 2026-10-28T00:36:43.198Z

### Tool call: Bash

```
{
  "command": "python3 -I /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_facts.py ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/data/outputs-recovery/formal/batch-3",
  "description": "Gather batch-3's correctness counts and host readings"
}
```

## 39. User — 2026-10-28T00:36:44.951Z

### Tool result

```
pos case claims accepted exec(complete) q1 q3a reference wasted_step_s fenced
1 C0 1 1 1(1) ok reported once clean 0.0 0
2 W5a 1 1 1(1) ok no matching report clean 0.0 0
3 W2 2 1 1(1) ok reported once clean 0.0 0
4 W7 2 1 2(1) ok reported once clean 95.45947841699672 3
5 W3 2 1 2(1) ok reported once clean 5.433451999990211 0
6 W5a 1 1 1(1) ok no matching report clean 0.0 0
7 D1 1 1 1(1) ok reported once clean 0.0 0
8 D1 1 1 1(1) ok reported once clean 0.0 0
9 W5b 1 1 1(1) ok reported once clean 0.0 0
10 C0 1 1 1(1) ok reported once clean 0.0 0
11 K2 1 1 1(1) ok reported once clean 0.0 0
12 X1 1 1 1(1) ok reported once clean 0.0 0
13 W2 2 1 1(1) ok reported once clean 0.0 0
14 W3 2 1 2(1) ok reported once clean 5.518359250003414 0
15 K1 1 1 1(1) ok reported once clean 0.0 0
16 W6 2 1 2(1) ok reported once clean 15.078217790993222 2
17 W6 2 1 2(1) ok reported once clean 14.709345456998562 2
18 X1 1 1 1(1) ok reported once clean 0.0 0
19 W5b 1 1 1(1) ok reported once clean 0.0 0
20 C0 1 1 1(1) ok reported once clean 0.0 0
21 W1 1 1 1(1) ok reported once clean 0.0 0
22 D2 1 1 1(1) ok reported once clean 0.0 0
23 W7 2 1 2(1) ok reported once clean 95.52112437500182 3
24 K1 1 1 1(1) ok reported once clean 0.0 0
25 W4 2 1 2(2) ok reported once clean 21.041876917006448 0
26 W1 1 1 1(1) ok reported once clean 0.0 0
27 W4 2 1 2(2) ok reported once clean 20.855399833002593 0
28 D2 1 1 1(1) ok reported once clean 0.0 0
29 K2 1 1 1(1) ok reported once clean 0.0 0
30 C0 1 1 1(1) ok reported once clean 0.0 0
claimed twice: 10 | executed twice: 8 | two complete executions: ['W4', 'W4']
accepted attempts: 30 with problems: {}
readings: 32 [(None, 32)]
power: Counter({'AC Power': 32}) | lid_closed: Counter({False: 32})
pressure: Counter({1: 32})
other containers: Counter({'0': 32})
available 2.65-3.25 GiB | swap in use 0.68-0.72 GiB
{'jobs_with_a_reading': 0.0, 'power_sources': ['AC Power'], 'on_battery': [], 'lid_closed': [], 'other_containers_at': [], 'max_memory_pressure': 0.0, 'min_available_bytes': 2716.8, 'swap_used_change_bytes': -48.0, 'counters': 'vm_stat', 'pageins_batch_bytes': 3208.9, 'pageouts_batch_bytes': 40.2, 'swapins_batch_bytes': 49.0, 'swapouts_batch_bytes': 0.0}
peaks: {'mysql': (319, 512, 62), 'kafka': (497, 640, 78)}
liveness: {'serve_restarted': 0, 'retry': 55, 'rewound': 0, 'gave_up': 0, 'failed_after_ack': 0, 'consumer_error': 0, 'pass_failed': 24}
nothing_left: {'processes_left': False, 'other_connections': 0, 'spark_scratch_new': []}
clock: {'ts_minus_mono_s': 0.033583458001203326, 'tolerance_s': 1.0, 'processes_on_the_same_clock': '19 of 19'}
wall: 2026-10-27T21:23:56.364996+00:00 -> 2026-10-27T21:55:03.281226+00:00 | ended: {'stop_reason': None}
final snapshot: {"event": "final_snapshot", "status_check_exit": 0, "cleanup_exit": 0, "fingerprints": [{"n_jobs": 30, "sum_version": 296, "n_attempts": 40, "sum_renewals": 176}, {"n_jobs": 30, "sum_version": 296, "n_attempts": 40, "sum_renewals": 176}, {"n_jobs": 30, "sum_version": 296, "n_attempts": 40, "sum_renewals": 176}], "fingerprints_agree": true, "batch_peaks": {"mysql": {"peak_bytes": 334520320, "limit_
fingerprints: {"passed": true, "values": [{"n_jobs": 30, "sum_version": 296, "n_attempts": 40, "sum_renewals": 176}, {"n_jobs": 30, "sum_version": 296, "n_attempts": 40, "sum_renewals": 176}, {"n_jobs": 30, "sum_version": 296, "n_attempts": 40, "sum_renewals": 176}]}
cleanup.txt: exit 0 | ended, not accepted: ~/leveraged-etf-risk-analytics/data/outputs-recovery/formal/batch-3/jobs/884bf4201ebc08805c66f97111a77495/job-14-attempt-1  (0.0 MiB) | ended, not accepted: ~/leveraged-etf-risk-analytics/data/outputs-recovery/formal/batch-3/jobs/884bf4201ebc08805c
monitor: {'error': None, 'events': 5481, 'other_project_events': 0}
```

## 40. Assistant — 2026-10-28T00:36:57.617Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; ls -la $W/data | head -3; B=$W/data/outputs-recovery/formal/batch-3; grep -c \"ended, not accepted\" $B/cleanup.txt; grep -o \"([0-9.]* MiB)\" $B/cleanup.txt | tr -d '()MiB ' | paste -sd+ - | bc; for f in $B/events/A.jsonl $B/events/B.jsonl; do grep '\"event\": \"retry\"' $f; done | python3 -c \"\nimport sys, json, collections\nc = collections.Counter((json.loads(l)['job_id'], json.loads(l).get('operation')) for l in sys.stdin)\nprint(c)\"; ls $W/data/outputs-recovery/formal/",
  "description": "Check the data link, cleanup listing and retry counts"
}
```

## 41. User — 2026-10-28T00:36:58.522Z

### Tool result

```
lrwxr-xr-x  1 [REDACTED:user]  staff  48 Oct 27 12:30 ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/data -> ~/leveraged-etf-risk-analytics/data
8
33.0
Counter({(22, 'accept_result'): 28, (28, 'accept_result'): 27})
batch-1
batch-1.after-restart
batch-1.console.log
batch-1.interruption.txt
batch-2
batch-2.console.log
batch-2.decision.txt
batch-2.other-container.txt
batch-3
batch-3.collect.log
batch-3.console.log
plan-544.json
```

## 42. Assistant — 2026-10-28T00:37:44.398Z

Next I'll check the earlier fingerprint method and which tests cover the docs, so I can confirm the batch folder is unchanged and pick the right checks.

## 43. Assistant — 2026-10-28T00:37:46.579Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3-fingerprint.txt | head -12; echo ....; grep -ln \"README\\|recovery-part-b\\|spec.md\\|\\.md\\b\" $W/tests/*.py | head; ls $W/tests | grep -i \"doc\\|readme\\|link\" ",
  "description": "Show the fingerprint method and find documentation tests"
}
```

## 44. User — 2026-10-28T00:37:47.357Z

### Tool result

```
fingerprint: 1442 files 34fa05af8be692b3
....
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/recovery_sqlite.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/memory_check.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_cache_contract.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_cache_experiment.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/mutation_check.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_caching_options.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_jobs_live_pipeline.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_jobs_kafka.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_jobs_queue.py
~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/tests/test_jobs_harness.py
```

## 45. Assistant — 2026-10-28T00:37:51.242Z

### Tool call: Bash

```
{
  "command": "grep -o '\"command\":\"[^\"]*fingerprint[^\"]*' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308.jsonl | tail -3 | cut -c1-900",
  "description": "Find the command that computed the batch fingerprint"
}
```

## 46. User — 2026-10-28T00:37:52.794Z

### Tool result

```
"command":"W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3-fingerprint.txt | head -12; echo ....; grep -ln \
"command":"W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3-fingerprint.txt | head -12; echo ....; grep -ln \
```

## 47. Assistant — 2026-10-28T00:37:56.046Z

### Tool call: Bash

```
{
  "command": "grep -o 'batch3-fingerprint.txt[^}]\\{0,40\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308.jsonl | head -3; grep -o '\"command\":\"[^\"]\\{0,700\\}batch3-fingerprint[^\"]\\{0,100\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308.jsonl | head -1 | cut -c1-1200",
  "description": "Locate the earlier fingerprint command in the transcript"
}
```

## 48. User — 2026-10-28T00:37:59.680Z

### Tool result

```
batch3-fingerprint.txt; ls -la $B.console.log $B.collect.log |
batch3-fingerprint.txt; ls -la $B.console.log $B.collect.log |
batch3-fingerprint.txt);\n   - confirmed cleanup: 0 project co
ugrep: error: error at position 649
\x80-\xbf][\x80-\xbf]){0,100}
exceeds complexity limits___/
```

## 49. Assistant — 2026-10-28T00:38:02.114Z

### Tool call: Bash

```
{
  "command": "grep -o '.\\{0,700\\}batch3-fingerprint.txt; ls -la' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308.jsonl | head -1 | cut -c1-900",
  "description": "Show the fingerprint command's text"
}
```

## 50. User — 2026-10-28T00:39:31.745Z

### Tool result

```
se","id":"toolu_019aiYyquahsmStjeVHJRM74","name":"Bash","input":{"command":"cd ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence && B=data/outputs-recovery/formal/batch-3 && uv run --group jobs python -c '\nimport hashlib, os, sys\nroot = sys.argv[1]; h = hashlib.sha256(); n = 0\nfor dp, dn, fn in sorted(os.walk(root)):\n    dn.sort()\n    for f in sorted(fn):\n        p = os.path.join(dp, f); n += 1\n        h.update(os.path.relpath(p, root).encode()); h.update(open(p, \"rb\").read())\nprint(\"fingerprint:\", n, \"files\", h.hexdigest()[:16])' $B | tee /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3-fingerprint.txt; ls -la
```

## 51. Assistant — 2026-10-28T00:39:36.962Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/fingerprint.py",
  "content": "\"\"\"The batch folder's fingerprint, computed as on 2026-10-27 after the session (relative path, then bytes, per file).\"\"\"\nimport hashlib\nimport os\nimport sys\n\nroot = sys.argv[1]\nh = hashlib.sha256()\nn = 0\nfor dp, dn, fn in sorted(os.walk(root)):\n    dn.sort()\n    for f in sorted(fn):\n        p = os.path.join(dp, f)\n        n += 1\n        h.update(os.path.relpath(p, root).encode())\n        h.update(open(p, \"rb\").read())\nprint(\"fingerprint:\", n, \"files\", h.hexdigest()[:16])\n"
}
```

## 52. User — 2026-10-28T00:39:37.794Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/fingerprint.py (file state is current in your context — no need to Read it back)
```

## 53. Assistant — 2026-10-28T00:39:39.454Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence; python3 -I /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/fingerprint.py $W/data/outputs-recovery/formal/batch-3; ls $W/data/outputs-recovery/formal/; git -C $W status --short | head -3",
  "description": "Recompute the batch-3 fingerprint to confirm it is unchanged"
}
```

## 54. User — 2026-10-28T00:39:40.708Z

### Tool result

```
fingerprint: 1442 files 34fa05af8be692b3
batch-1
batch-1.after-restart
batch-1.console.log
batch-1.interruption.txt
batch-2
batch-2.console.log
batch-2.decision.txt
batch-2.other-container.txt
batch-3
batch-3.collect.log
batch-3.console.log
plan-544.json
```

## 55. Assistant — 2026-10-28T00:39:45.433Z

### Tool call: Bash

```
{
  "command": "cd ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence && uv run --group jobs python docs/verify_frozen_code.py data/outputs-recovery/formal/batch-3 4fc550e 544 > data/outputs-recovery/formal/batch-3.verify.txt; echo \"exit $?\"; cat data/outputs-recovery/formal/batch-3.verify.txt",
  "description": "Rerun the frozen-code check and keep its output beside batch-3"
}
```

## 56. User — 2026-10-28T00:39:51.157Z

### Tool result

```
exit 0
commit recorded: c5c340a5b6d330c7a53f11b1d546d842275dc9e7; code records: 21
source digest matches 4fc550e: True; uv.lock matches: True; clean worktree: True
plan: purpose formal, seed 544 (expected 544)
FROZEN CODE: VERIFIED
```

## 57. Assistant — 2026-10-28T00:39:53.161Z

The frozen-code check passes again, and I saved its output beside the batch. I'm drafting Part B §10 now.

## 58. Assistant — 2026-10-28T00:39:54.716Z

### Tool call: Bash

```
{
  "command": "python3 - data/outputs-recovery/formal/batch-3 <<'EOF'\nimport json, sys\nH = [json.loads(l) for l in open(sys.argv[1] + \"/harness.jsonl\")]\nfor e in H:\n    if e[\"event\"] == \"injection\" and e[\"case\"] in (\"X1\", \"W5a\", \"W5b\", \"W1\", \"W7\"):\n        print({k: e[k] for k in e if k not in (\"ts\", \"pid\", \"component\", \"batch\", \"clock\", \"code\", \"mono\", \"event\")})\nEOF",
  "description": "Read the X1, W5 and W7 injection records"
}
```

## 59. User — 2026-10-28T00:39:55.598Z

### Tool result

```
{'position': 2, 'job_id': 2, 'case': 'W5a', 'missed': None, 'kind': 'hook', 'worker': 'A', 'point': 'after_accept_commit', 't_inj': 50994.362219916}
{'position': 4, 'job_id': 4, 'case': 'W7', 'missed': None, 'kind': 'sigstop_tree', 'worker': 'A', 'attempt': 1, 't_inj': 51102.30498625, 'resumed': 51192.310040375, 'fenced_mono': 51192.33110625, 'stopped': 4}
{'position': 6, 'job_id': 6, 'case': 'W5a', 'missed': None, 'kind': 'hook', 'worker': 'B', 'point': 'after_accept_commit', 't_inj': 51329.716464958}
{'position': 9, 'job_id': 9, 'case': 'W5b', 'missed': None, 'kind': 'hook', 'worker': 'B', 'point': 'after_accept', 't_inj': 51454.032516041}
{'position': 12, 'job_id': 12, 'case': 'X1', 'missed': None, 'kind': 'publish', 'worker': 'B', 't_inj': 51580.181132041, 'published': True}
{'position': 18, 'job_id': 18, 'case': 'X1', 'missed': None, 'kind': 'publish', 'worker': 'B', 't_inj': 52009.132419666, 'published': True}
{'position': 19, 'job_id': 19, 'case': 'W5b', 'missed': None, 'kind': 'hook', 'worker': 'B', 'point': 'after_accept', 't_inj': 52054.41263125}
{'position': 21, 'job_id': 21, 'case': 'W1', 'missed': None, 'kind': 'hook', 'worker': 'B', 'point': 'before_claim', 't_inj': 52092.845112958}
{'position': 23, 'job_id': 23, 'case': 'W7', 'missed': None, 'kind': 'sigstop_tree', 'worker': 'B', 'attempt': 1, 't_inj': 52194.570951458, 'resumed': 52284.580990833, 'fenced_mono': 52284.593903666, 'stopped': 4}
{'position': 26, 'job_id': 26, 'case': 'W1', 'missed': None, 'kind': 'hook', 'worker': 'B', 'point': 'before_claim', 't_inj': 52465.231655041}
```

## 60. Assistant — 2026-10-28T00:40:02.923Z

### Tool call: Bash

```
{
  "command": "sed -n 910,925p src/etf_risk/jobs/harness.py; python3 -c \"\nimport json\nH=[json.loads(l) for l in open('data/outputs-recovery/formal/batch-3/harness.jsonl')]\nt0=[e for e in H if e['event']=='batch_started'][0]['mono']\nprint('X1 first duplicate at t+%.1f s; K2 #1 Kafka back at t+%.1f s' % (51580.181132041-t0, 51523.024860958-t0))\"",
  "description": "Check when the harness first used its Kafka publisher"
}
```

## 61. User — 2026-10-28T00:40:04.226Z

### Tool result

```
            claim = self.wait_for(lambda: self.claim_of(job_id), s.phase_timeout_s, f"job {job_id}'s claim")
            t_inj = time.monotonic()
            return {"kind": "publish", "worker": claim["worker"], "t_inj": t_inj, "published": self.publish_again(job_id)}
        raise ValueError(case)

    def inject_stop(self, case: str, job_id: int, claim: dict, t_inj: float) -> dict:
        """W6: the worker stopped until the standby takes over. W7: the whole tree, for w7_stop_s.
        Then SIGCONT, the old worker's fenced event, and SIGTERM (its attempt is no longer its own)."""
        import psutil
        worker = claim["worker"]
        if case == "W6":
            frozen = [psutil.Process(self.procs[worker].pid)]
            frozen[0].suspend()
            self.wait_for(lambda: (c := self.claim_of(job_id)) and c["attempt"] > claim["attempt"],
                          self.settings.phase_timeout_s, "the takeover")
        else:
X1 first duplicate at t+664.0 s; K2 #1 Kafka back at t+606.8 s
```

## 62. Assistant — 2026-10-28T00:41:34.722Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_details.py",
  "content": "\"\"\"Batch-3: outage windows, detection against the service's return, reconciler failures, run lengths after a recovery.\"\"\"\nimport csv\nimport json\nimport sys\nfrom pathlib import Path\n\nfolder = Path(sys.argv[1])\nread = lambda p: [json.loads(line) for line in p.read_text().splitlines() if line.strip()]\nharness = read(folder / \"harness.jsonl\")\nreconciler = [e for p in (folder / \"events\").glob(\"reconciler-*.jsonl\") for e in read(p)]\nworkers = read(folder / \"events\" / \"A.jsonl\") + read(folder / \"events\" / \"B.jsonl\")\nt0 = next(e for e in harness if e[\"event\"] == \"batch_started\")[\"mono\"]\ninjections = {e[\"job_id\"]: e for e in harness if e[\"event\"] == \"injection\"}\nrows = {int(r[\"job_id\"]): r for r in csv.DictReader(open(folder / \"injections.csv\"))}\n\nwindows = []\nfor job, e in sorted(injections.items()):\n    back = e.get(\"restored\", e.get(\"ready\"))\n    if back:\n        windows.append((e[\"case\"], e.get(\"service\"), e[\"t_inj\"], back))\n        print(f\"{e['case']} job {job}: down t+{e['t_inj'] - t0:.1f} to t+{back - t0:.1f} ({back - e['t_inj']:.2f} s)\")\n\nfailed = [e for e in reconciler if e[\"event\"] in (\"pass_failed\",)]\ninside = sum(any(w[1] == \"mysql\" and w[2] <= e[\"mono\"] <= w[3] + 1 for w in windows) for e in failed)\nprint(\"reconciler pass_failed:\", len(failed), \"within a MySQL outage (+1 s):\", inside)\nprint(\"  outside:\", [round(e[\"mono\"] - t0, 1) for e in failed if not any(w[1] == \"mysql\" and w[2] <= e[\"mono\"] <= w[3] + 1 for w in windows)])\nretries = [e for e in workers if e[\"event\"] == \"retry\"]\nprint(\"retries within a MySQL outage (+1 s):\", sum(any(w[1] == \"mysql\" and w[2] <= e[\"mono\"] <= w[3] + 1 for w in windows) for e in retries), \"of\", len(retries))\n\nfor job, e in sorted(injections.items()):\n    r = rows[job]\n    if e[\"case\"] == \"K2\":\n        back = e[\"restored\"] - e[\"t_inj\"]\n        print(f\"K2 job {job}: detection {float(r['detection_s']) - back:.1f} s and first claim {float(r['rerun_s']) - back:.1f} s after Kafka's return\")\n    if e[\"case\"] in (\"W1\", \"W2\", \"W3\", \"W4\", \"W6\"):\n        print(f\"{e['case']} job {job}: new claim to acceptance {float(r['finish_s']) - float(r['rerun_s']):.1f} s\")\n    if e[\"case\"] == \"W7\":\n        resumed = e[\"resumed\"] - e[\"t_inj\"]\n        print(f\"W7 job {job}: tree resumed {resumed:.1f} s after the stop; acceptance {float(r['finish_s']) - resumed:.1f} s after that\")\nx1 = [e for e in harness if e[\"event\"] == \"published_again\"] + [e for e in injections.values() if e[\"case\"] == \"X1\"]\nprint(\"X1 publications:\", [(e.get(\"job_id\"), e.get(\"published\"), round(e.get(\"t_inj\", e[\"mono\"]) - t0, 1)) for e in x1])\n"
}
```

## 63. User — 2026-10-28T00:41:35.855Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_details.py (file state is current in your context — no need to Read it back)
```

## 64. Assistant — 2026-10-28T00:41:36.602Z

### Tool call: Bash

```
{
  "command": "python3 -I /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/batch3_details.py data/outputs-recovery/formal/batch-3",
  "description": "Compute outage windows, detection offsets and run lengths"
}
```

## 65. User — 2026-10-28T00:41:37.492Z

### Tool result

```
D1 job 7: down t+433.7 to t+464.9 (31.24 s)
D1 job 8: down t+477.6 to t+508.8 (31.23 s)
K2 job 11: down t+575.0 to t+606.8 (31.85 s)
K1 job 15: down t+873.8 to t+877.1 (3.30 s)
D2 job 22: down t+1240.2 to t+1271.4 (31.21 s)
K1 job 24: down t+1401.7 to t+1404.8 (3.12 s)
D2 job 28: down t+1722.2 to t+1753.3 (31.17 s)
K2 job 29: down t+1753.8 to t+1785.7 (31.90 s)
reconciler pass_failed: 24 within a MySQL outage (+1 s): 24
  outside: []
retries within a MySQL outage (+1 s): 55 of 55
W2 job 3: new claim to acceptance 21.6 s
W7 job 4: tree resumed 90.0 s after the stop; acceptance 22.4 s after that
W3 job 5: new claim to acceptance 21.4 s
K2 job 11: detection 4.1 s and first claim 15.0 s after Kafka's return
W2 job 13: new claim to acceptance 21.8 s
W3 job 14: new claim to acceptance 21.8 s
W6 job 16: new claim to acceptance 22.5 s
W6 job 17: new claim to acceptance 22.4 s
W1 job 21: new claim to acceptance 21.3 s
W7 job 23: tree resumed 90.0 s after the stop; acceptance 22.4 s after that
W4 job 25: new claim to acceptance 21.9 s
W1 job 26: new claim to acceptance 21.6 s
W4 job 27: new claim to acceptance 22.2 s
K2 job 29: detection 2.9 s and first claim 15.0 s after Kafka's return
X1 publications: [(12, True, 686.4), (18, True, 1115.4), (12, True, 664.0), (18, True, 1092.9)]
```

## 66. Assistant — 2026-10-28T00:41:55.180Z

I have every figure for the draft, including outage windows, run lengths after recovery and the reconciler failures (all 24 fell inside MySQL outages). Writing Part B §10 now.

## 67. Assistant — 2026-10-28T00:41:58.268Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md",
  "old_string": "> Swap in use is recorded correctly, and its figures are kept. No verdict changes: nothing gated\n> on these counters.\n",
  "new_string": "> Swap in use is recorded correctly, and its figures are kept. No verdict changes: nothing gated\n> on these counters.\n\n> **Addition, 2026-10-27: formal batch-3 (section 10). Drafted with Claude Code; awaiting the\n> author's review.** Part A's section 13 allowed one more formal batch, batch-3, beyond row 11's\n> one rerun. Section 10 reports it, and none of it is approved yet. Sections 1–9 are unchanged.\n> Where they say that there are no valid formal recovery times (5.1, 7.2, 7.3), they describe\n> batch-1 and batch-2, which stay invalid for recovery times.\n"
}
```

## 68. Assistant — 2026-10-28T00:43:11.579Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md",
  "old_string": "The live Kafka gate before the formal batches is\n`data/outputs-recovery/preflight/kafka-live-fcaa645.txt` (27 passed, 0 failed, 0 skipped).\n",
  "new_string": "The live Kafka gate before the formal batches is\n`data/outputs-recovery/preflight/kafka-live-fcaa645.txt` (27 passed, 0 failed, 0 skipped).\n\n## 10. batch-3 (2026-10-27): drafted, awaiting the author's review\n\n_Drafted with Claude Code (Opus 5.5) on 2026-10-27 at the author's request, from the records in\n`data/outputs-recovery/formal/batch-3/` (numbers and tables read by script) and the session's\nconsole and collection logs. **Nothing in this section is approved:** the facts (10.1–10.6), the\ndrafted answers (10.7) and the limits (10.8) await the author's review, and the approved answers\nof section 7 stand unchanged until the author decides. The protocol is Part A's, with the\namendments of its section 13, the batch-3 item included. Times are local (UTC−5) on 2026-10-27._\n\n### 10.1 The three batches side by side\n\n| | batch-1 | batch-2 | batch-3 |\n|---|---|---|---|\n| Allowed by | Part A, row 11 | row 11's one rerun | Part A, section 13: one more batch, decided on 2026-10-27 |\n| Plan | `plan-544.json`: seed 544, 30 jobs | the same plan | the same plan; the session checked its SHA-256 |\n| Code | HEAD `1c11577`, clean; the code of `fcaa645` | the same | HEAD `c5c340a`, clean; the code of `4fc550e` |\n| Ran | 2026-10-25, 00:15:09 to 00:39:54, then the host restarted | 2026-10-25, 05:55:28 to 06:45:37 | 2026-10-27, 16:23:56 to 16:55:03 |\n| Harness exit | none: the shell ended with the host | 0 | 0 |\n| Made, missed, not run, unrecorded (collector) | 20, 0, 0, 10 | 30, 0, 0, 0 | 30, 0, 0, 0 |\n| Final snapshot | none | `status --check` exit 0; fingerprints agree (30 jobs, 40 attempts) | `status --check` exit 0; fingerprints agree (30 jobs, version sum 296, 40 attempts, 176 renewals) |\n| Collector verdicts as recorded | correctness invalid; recovery times invalid; exit 1 (`fcaa645`) | both valid; exit 0 (`fcaa645`) | both valid, every required check passed; exit 0 (`4fc550e`) |\n| The author's decision, as recorded | none; the collector's verdicts apply | correctness valid; recovery times **invalid**: the exclusive window was broken | none yet: this draft awaits review |\n| Other projects' containers | 0 at the start; no later count | 0 at the start; one from 06:25:08, outside the records | 0 at all 32 readings; 0 of the 5,481 container events of the whole batch |\n| Sleep and wake (power log) | a clamshell dark wake from 00:35:46 | none | none: 0 Sleep, 0 Wake, 0 DarkWake entries; the log covers the batch |\n| Clock check | failed: no `batch_ended` event | passed: −0.009 s, 19 of 19 processes on one clock | passed: +0.034 s, 19 of 19 processes on one clock |\n| Frozen code checked after the batch | no such check then | no such check then | verified: all 21 code records match `4fc550e` and its `uv.lock`, with a clean worktree and seed 544 |\n\n### 10.2 What happened\n\n- **The session:** the author ran `docs/recovery-batch-3.zsh` from Terminal. Its preconditions held,\n  both with `--check` beforehand and at the start of the run. The batch, the collection and the\n  cleanup check followed: harness exit 0, collector exit 0, and no container of this project left.\n  The author then ran `docs/verify_frozen_code.py`, which printed `FROZEN CODE: VERIFIED`.\n- **One Kafka line in the console.** The first line of `batch-3.console.log`, which has no time, is\n  a librdkafka message: a producer could not connect to `127.0.0.1:9094` (\"Connection refused\").\n  - **From the code and records:** the console receives only the harness's own output. The\n    workers, the reconciler and the reference run write to their own logs, and Docker's output is\n    captured. The harness's only Kafka client that logs is the publisher it creates for X1's\n    duplicates, first at position 12's claim. Its readiness checks use Kafka clients that log\n    nothing.\n  - **The outages:** after that publisher was created, Kafka was down three times. These were the\n    K1 restarts at positions 15 and 24, 3.3 and 3.1 s from the restart's start to the harness's\n    readiness reading, and the K2 stop at position 29, 31.9 s.\n  - **Unknown:** the line has no time, so which outage it came from is not recorded.\n  - All 4 of X1's duplicate publications were confirmed. No check bears on the line, and none\n    failed.\n\n### 10.3 Correctness (E1)\n\nThe batch's correctness verdict is valid by the collector's checks, as recorded.\n\n- **One accepted result per job:** Q1 `ok` for all 30 jobs, each with exactly one accepted result.\n- **Results equal to the reference run:** all 30 accepted attempts pass the collector's checks: the\n  folder's digest equals the accepted digest, the run's checks and verify output are clean, and\n  every table matches the reference run by content.\n- **Executions:** 10 jobs were claimed twice (W2, W3, W4, W6 and W7, two of each), and 8 of them\n  executed twice. Both W4 jobs completed two executions and had one accepted. `cleanup.txt` lists\n  8 unaccepted attempts' folders (33.0 MiB).\n- **No overlapping step intervals:** every step has both monotonic times.\n- **The job table:** `status --check` exit 0, with no invariant violation. The three fingerprints\n  agree (30 jobs, version sum 296, 40 attempts, 176 renewals).\n- **Q2b and Q3:** no Q2b rows, and Q3b matches for all 28 reports. Q3a is \"reported once\" for 28\n  jobs and \"no matching report\" for the 2 W5a jobs (positions 2 and 6).\n- **Why the W5a reports are missing.** W5a kills the owner at `after_accept_commit`: after MySQL\n  committed the acceptance, but before the worker wrote its `accepted` event. The job table\n  therefore holds the accepted result, while the worker's log has no report of it.\n  - Part A predicted exactly this (\"Q3a `no matching report`, by design\", section 4), and batch-2\n    showed the same (4.1).\n  - Both W5a jobs have Q1 `ok`, and their accepted results match the reference run.\n  - W5b kills the owner after the event, so its report exists.\n- **Liveness:** 55 retried `accept_result` calls, 28 and 27 for the two D2 jobs, and 24 failed\n  reconciler passes. All of them fell within MySQL outages. There was no `failed_after_ack`, no\n  `consumer_error` and no serve restart.\n- **Left behind:** quiescence left no process, no other database connection and no new Spark\n  scratch entry.\n\n| Case | Positions | Claims | Accepted | Executions (complete) | Q1 | Q3a | Accepted result against the reference |\n|---|---|---:|---:|---|---|---|---|\n| C0 | 1, 10, 20, 30 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| W1 | 21, 26 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| W2 | 3, 13 | 2 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| W3 | 5, 14 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |\n| W4 | 25, 27 | 2 | 1 | 2 (2) | `ok` | reported once | matches, all checks clean |\n| W5a | 2, 6 | 1 | 1 | 1 (1) | `ok` | no matching report, by design | matches, all checks clean |\n| W5b | 9, 19 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| W6 | 16, 17 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |\n| W7 | 4, 23 | 2 | 1 | 2 (1) | `ok` | reported once | matches, all checks clean |\n| K1 | 15, 24 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| K2 | 11, 29 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| D1 | 7, 8 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| D2 | 22, 28 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n| X1 | 12, 18 | 1 | 1 | 1 (1) | `ok` | reported once | matches, all checks clean |\n\n### 10.4 Recovery times (E2)\n\nThe batch's recovery-time verdict is valid by the collector's checks, as recorded. Every check\npassed, including the whole-batch container check and the clock check.\n\n**Timing origins.** Each time below counts from one of three origins, named in the column heads:\n- **the submit:** when the harness submitted the job;\n- **the injection:** when the harness made the fault. That is the kill or stop signal, the\n  duplicate publication (X1), or the start of the service's stop (K2, D1, D2) or restart (K1);\n- **the deadline's reference** (Part A, section 3): the submit for C0, the service's return for K2,\n  D1 and D2, and the injection for every other case.\n\nThe service's return is the harness's own reading: the moment its readiness check first succeeds\nafter the service is started again. A worker can reconnect slightly before that reading, so a\nfinish can come out just below zero from it (position 28, −0.1 s). Detection and re-run count from\nthe injection, as the collector computes them; D, the slack and the deadline outcome count from\nthe reference. The slack is D minus the finish from the reference: how long before its deadline the\njob's result was accepted. For K2, D1 and D2 the two origins differ by the outage: 31.8 and 31.9 s\nfor Kafka, and 31.2 s for MySQL.\n\n| Position | Case | Detection (s, from injection) | Re-run (s, from injection) | Finish from submit (s) | Finish from injection (s) | Deadline's reference | Finish from reference (s) | D (s) | Slack (s) | Deadline |\n|---:|---|---:|---:|---:|---:|---|---:|---:|---:|---|\n| 1 | C0 | n/a: no failure | n/a: no failure | 23.0 | — | submit | 23.0 | 75 | 52.0 | on time |\n| 2 | W5a | n/a: after acceptance | n/a: after acceptance | no `accepted` event, by design | n/a | injection | n/a | 75 | n/a | on time |\n| 3 | W2 | 61.5 | 61.5 | 84.1 | 83.1 | injection | 83.1 | 140 | 56.9 | on time |\n| 4 | W7 | 59.1 | 59.1 | 118.5 | 112.4 | injection | 112.4 | 170 | 57.6 | on time |\n| 5 | W3 | 58.5 | 58.5 | 86.1 | 79.9 | injection | 79.9 | 140 | 60.1 | on time |\n| 6 | W5a | n/a: after acceptance | n/a: after acceptance | no `accepted` event, by design | n/a | injection | n/a | 75 | n/a | on time |\n| 7 | D1 | 6.3 | n/a: the attempt went on | 43.7 | 37.3 | MySQL's return, 31.2 s after the stop | 6.1 | 140 | 133.9 | on time |\n| 8 | D1 | 6.3 | n/a: the attempt went on | 44.1 | 37.8 | MySQL's return, 31.2 s after the stop | 6.5 | 140 | 133.5 | on time |\n| 9 | W5b | n/a: after acceptance | n/a: after acceptance | 22.0 | n/a: accepted before the kill | injection | n/a | 75 | n/a | on time |\n| 10 | C0 | n/a: no failure | n/a: no failure | 22.5 | — | submit | 22.5 | 75 | 52.5 | on time |\n| 11 | K2 | 36.0 | 46.9 | 67.7 | 68.6 | Kafka's return, 31.8 s after the stop | 36.7 | 125 | 88.3 | on time |\n| 12 | X1 | n/a: no failure | n/a: no failure | 23.5 | 22.0 | injection | 22.0 | 75 | 53.0 | on time |\n| 13 | W2 | 63.4 | 63.4 | 86.2 | 85.2 | injection | 85.2 | 140 | 54.8 | on time |\n| 14 | W3 | 58.4 | 58.4 | 86.2 | 80.1 | injection | 80.1 | 140 | 59.9 | on time |\n| 15 | K1 | n/a for the job: the attempt goes on | n/a: the attempt goes on | 23.5 | 17.2 | injection: the restart's start; Kafka ready 3.3 s later | 17.2 | 75 | 57.8 | on time |\n| 16 | W6 | 60.4 | 60.4 | 89.5 | 82.9 | injection | 82.9 | 140 | 57.1 | on time |\n| 17 | W6 | 59.3 | 59.3 | 87.8 | 81.7 | injection | 81.7 | 140 | 58.3 | on time |\n| 18 | X1 | n/a: no failure | n/a: no failure | 23.0 | 22.0 | injection | 22.0 | 75 | 53.0 | on time |\n| 19 | W5b | n/a: after acceptance | n/a: after acceptance | 22.5 | n/a: accepted before the kill | injection | n/a | 75 | n/a | on time |\n| 20 | C0 | n/a: no failure | n/a: no failure | 22.9 | — | submit | 22.9 | 75 | 52.1 | on time |\n| 21 | W1 | 14.9 | 14.9 | 37.2 | 36.2 | injection | 36.2 | 90 | 53.8 | on time |\n| 22 | D2 | 3.1 | n/a: the attempt went on | 55.2 | 31.4 | MySQL's return, 31.2 s after the stop | 0.2 | 140 | 139.8 | on time |\n| 23 | W7 | 59.2 | 59.2 | 118.5 | 112.5 | injection | 112.5 | 170 | 57.5 | on time |\n| 24 | K1 | n/a for the job: the attempt goes on | n/a: the attempt goes on | 22.7 | 16.3 | injection: the restart's start; Kafka ready 3.1 s later | 16.3 | 75 | 58.7 | on time |\n| 25 | W4 | 63.8 | 63.8 | 108.5 | 85.7 | injection | 85.7 | 140 | 54.3 | on time |\n| 26 | W1 | 13.6 | 13.6 | 36.1 | 35.2 | injection | 35.2 | 90 | 54.8 | on time |\n| 27 | W4 | 64.0 | 64.0 | 108.3 | 86.2 | injection | 86.2 | 140 | 53.8 | on time |\n| 28 | D2 | 3.8 | n/a: the attempt went on | 53.9 | 31.0 | MySQL's return, 31.2 s after the stop | −0.1 | 140 | 140.1 | on time |\n| 29 | K2 | 34.8 | 46.9 | 68.0 | 68.8 | Kafka's return, 31.9 s after the stop | 36.9 | 125 | 88.1 | on time |\n| 30 | C0 | n/a: no failure | n/a: no failure | 23.1 | — | submit | 23.1 | 75 | 51.9 | on time |\n\n- **30 of 30 jobs met their deadlines.** The smallest slack was 51.9 s (position 30, C0).\n- **W5a and W5b** were killed after their acceptance, so they have no recovery time. Both jobs of\n  each were already succeeded at their deadline. W5b's `accepted` event came before the kill\n  (0.0 s), and W5a's never came (10.3).\n- **Detection events,** as Part A section 4 names them:\n  - the standby's `delivered` (W1);\n  - the reconciler's `requeued` (W2, W3, W4, W6, W7);\n  - the reconciler's `published` (K2), 4.1 and 2.9 s after Kafka's return;\n  - `renewal_failed` (D1), during the outage;\n  - a `retry` of `accept_result` (D2), during the outage.\n\n  K2's first claim came 15.0 s after Kafka's return in both jobs.\n- **D1 and D2 took the branch without fencing:** MySQL returned 31.2 s after the stop, before F\n  (40–50 s after it), so each attempt went on with one claim.\n- **After a recovery, the runs took about as long as a control:**\n  - from the new claim to the acceptance: 21.3–22.5 s (W1, W2, W3, W4, W6);\n  - W7's replacement waited for the stopped tree, which resumed 90.0 s after the stop; the\n    acceptance came 22.4 s after that.\n\n### 10.5 The deadline slack: larger than Part A expected\n\nPart A's predictions assumed a run of T = 40 s and gave margins of 31–35 s (section 4). Part A's\nsection 3 added that, at the preflights' median control time of 49.6 s, those margins would shrink\nto about 20–25 s. batch-3's slack, each from its deadline's reference, was larger in every case:\n\n| Cases | Slack (s) | Mainly from |\n|---|---|---|\n| C0, X1 | 51.9–53.0 | the run: 22.5–23.1 s for the controls, against the 70.2 s (2S) of D |\n| K1 | 57.8–58.7 | the run; the attempt went on through the restart |\n| W1, W2, W3, W4, W6, W7 | 53.8–60.1 | the run, 21.3–22.5 s after the new claim; detection came within B (58.4–64.0 s against L + P = 65 s for W2–W6; 13.6–14.9 s against 19 s for W1) |\n| K2 | 88.1–88.3 | B assumes the whole publication grace after Kafka's return (54 s); the first claim came 15.0 s after it |\n| D1, D2 | 133.5–140.1 | B assumes a fenced attempt and a new run (65 s); MySQL returned before F, so no new run was needed |\n\n- **The run:** D = ceil5(B + 2S) gives each run 70.2 s, twice M2's slowest step sum. The controls\n  took 22.5–23.1 s from submit to acceptance (median 22.9 s). That is below the assumed T of 40 s,\n  and below the preflights' 45.1–52.4 s on which Part A's section 3 judged the margins. Every case\n  that ran its job after the injection gains about 48 s of slack this way. Rounding D up to a\n  multiple of 5 adds up to 5 s more.\n- **What may explain the shorter runs, without a measured cause:**\n  - batch-3 ran at memory pressure level 1 at all 32 readings, with 2.65–3.25 GiB available;\n  - the preflights and batch-2 ran mostly at level 2, with 1.21–2.04 GiB available in batch-2;\n  - in batch-2's supplementary positions 1–17, under those conditions, the controls took 84.7 and\n    43.2 s, and the same deadlines gave two late jobs (5.2).\n\n  This is one batch against another, not a controlled comparison.\n- **What the slack does not show.** P3 re-derives D only if T exceeds 2S, so D was kept, and this\n  batch met it with room. On time and late still classify jobs on this host only (Part A, section\n  3). A slower state of this host can come closer to the deadlines, as batch-2's late jobs did.\n\n### 10.6 Host conditions\n\nbatch-3 records `vm_stat`'s counters by name (since `12c925d`), so its swap figures are swap\ntraffic, unlike the page counters of sections 5.2 and 6.\n\n| | batch-3 |\n|---|---|\n| Readings | 32: the start, 30 jobs and the end |\n| Power | AC at all 32 |\n| Lid | open at all 32 |\n| Sleep and wake (power log) | none; the log starts on 2026-10-20, before the batch |\n| Clock check | passed: wall minus monotonic +0.034 s, 19 of 19 processes on one clock |\n| Memory pressure | level 1 at all 32 |\n| Available at the readings | 2.65–3.25 GiB |\n| Swap over the batch | in use 0.68–0.72 GiB at the readings, 48 MiB less at the end than at the start; 49 MiB swapped in, none swapped out |\n| Paging over the batch | 3.13 GiB paged in, 40 MiB paged out |\n| Container peaks | MySQL 319 of 512 MiB (62%); Kafka 497 of 640 MiB (78%) |\n| Other containers | none at any of the 32 readings. The monitor ran for the whole batch without error: 0 events of other projects' containers, 5,481 of this project's |\n\n### 10.7 Drafted answers (awaiting the author's review)\n\n_The questions are those of spec §11. The answers below were drafted with Claude Code on\n2026-10-27 and are **not approved**. The approved answers of section 7, which rest on batch-1 and\nbatch-2, are unchanged._\n\n**E1 (drafted; awaiting review).**\n- batch-3 gives a second valid correctness verdict, with the same outcome as batch-2: all 30 jobs\n  succeeded with exactly one accepted result each, and every accepted result matched the reference\n  run.\n- This held for the 10 jobs claimed twice and the 8 executed twice, including the 2 W4 jobs that\n  completed two executions and had only one accepted.\n- No job had more than one accepted result. The two W5a jobs have no matching report in the\n  worker's log, as designed.\n- These are counts from two batches of 30 jobs on one host, not a rate.\n\n**E2 (drafted; awaiting review).** batch-3 is the formal batch with valid recovery times: one\nbatch, on this host and this configuration, with two jobs per case. Each time below names its\norigin.\n- **A worker killed before its claim (W1):** the standby received the job 13.6 and 14.9 s after\n  the kill. The job finished 35.2 and 36.2 s after it.\n- **A worker killed or stopped after its claim (W2, W3, W4, W6):** the reconciler requeued the job,\n  and it was claimed again 58.4–64.0 s after the injection. It finished 79.9–86.2 s after the\n  injection.\n- **A whole worker tree stopped for 90 s (W7):** the job was claimed again 59.1 and 59.2 s after\n  the stop. It finished 112.4 and 112.5 s after the stop, 22.4 s after the stopped tree resumed.\n- **A Kafka restart (K1):** the attempt went on. Kafka was ready again 3.1 and 3.3 s after the\n  restart began, and the job finished 16.3 and 17.2 s after that start.\n- **Kafka stopped around the submit (K2):**\n  - Kafka returned 31.8 and 31.9 s after the stop;\n  - the reconciler published the job 2.9 and 4.1 s after Kafka's return;\n  - the first claim came 15.0 s after Kafka's return;\n  - the job finished 36.7 and 36.9 s after Kafka's return, which is 68.6 and 68.8 s after the stop.\n- **A MySQL stop (D1, mid-step; D2, while the owner held its acceptance):** MySQL returned 31.2 s\n  after the stop, before the fence, and every attempt went on.\n  - D1 finished 6.1 and 6.5 s after MySQL's return.\n  - D2's retried acceptance succeeded at MySQL's return, −0.1 and 0.2 s from the harness's\n    reading of it.\n- **Kills after the acceptance (W5a, W5b):** each job stayed succeeded with its one accepted result.\n- **Duplicate publications (X1):** they were refused, with one claim per job.\n- **All 30 jobs met their deadlines,** with 51.9–140.1 s of slack. That is more than Part A\n  expected, mainly because the runs took about 22 s rather than the 40–50 s assumed (10.5).\n- **No job was lost or accepted twice:** all 30 succeeded with exactly one accepted result.\n- **No branch with fencing:** D1 and D2 ran only the branch without fencing, because MySQL\n  returned before the fence.\n\n### 10.8 Limits (drafted; awaiting review)\n\n- **One batch, one host:** an 8 GiB Mac, two jobs per case (four controls), reported as counts with\n  no rates. The results describe this host in this state, at memory pressure level 1. batch-2's\n  supplementary observations were slower, at level 2.\n- **Deadlines as set by P3,** not re-derived. On time and late classify jobs on this host only, and\n  the slack here was large (10.5).\n- **D1 and D2 show one branch only:** MySQL returned before F in all four jobs, so the fenced branch\n  of Part A's predictions was not observed.\n- **The service's return is the harness's reading,** which can trail a worker's reconnection by a\n  fraction of a second (position 28).\n- **The exclusive window:** this project's and other projects' containers were watched for the\n  whole batch. Other host processes were checked only at the session's start (no test, job or Spark\n  process), and the session asked for the editor and other applications to be closed. Neither the\n  harness nor the collector records other processes during the batch.\n- **The frozen code includes an exception:** `4fc550e`'s change to the container events' text ran\n  in this batch without a live preflight of its own, as the author decided (Part A, section 13).\n- **The Kafka line in the console** is attributed from the code and records; its time is not\n  recorded (10.2).\n- **batch-1 and batch-2 are unchanged:** both stay invalid for recovery times, and batch-3 does not\n  revise their verdicts.\n\n### 10.9 Records\n\nIn `data/outputs-recovery/formal/`, outside Git:\n\n- `batch-3/`, the harness's records with the collector's outputs (`4fc550e`). It holds 1,442 files.\n  Its fingerprint, `34fa05af8be692b3`, is the first 16 hex digits of a SHA-256 over each file's\n  relative path and bytes, in sorted order. The fingerprint was the same after the session and\n  when this section was drafted.\n- `batch-3.console.log` and `batch-3.collect.log`, the session's output.\n- `batch-3.verify.txt`, the frozen-code check. Claude Code reran it on 2026-10-27, after the\n  author's own run, with the same result: exit 0, `FROZEN CODE: VERIFIED`.\n"
}
```

## 69. User — 2026-10-28T00:43:12.398Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 70. User — 2026-10-28T00:43:13.222Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 71. Assistant — 2026-10-28T00:43:32.300Z

Checking two details before finalizing: whether X1's duplicates were logged as refused, and which Kafka clients in the harness process can log at all.

## 72. Assistant — 2026-10-28T00:43:34.525Z

### Tool call: Bash

```
{
  "command": "sed -n 1,30p src/etf_risk/jobs/kafka.py | grep -n \"log\\b\\|logging\\|getLogger\\|basicConfig\" ; grep -n \"log = \\|getLogger\\|basicConfig\\|logging\\.\" src/etf_risk/jobs/kafka.py src/etf_risk/jobs/harness.py src/etf_risk/services.py | head; sed -n 155,175p src/etf_risk/jobs/kafka.py; grep -rn \"ensure_topic\\|create_topic\\|def wait_until_ready\" src/etf_risk | grep -v \"^src/etf_risk/jobs/kafka.py:1[56]\" | head",
  "description": "Check which Kafka clients log and where topics are created"
}
```

## 73. Assistant — 2026-10-28T00:43:37.007Z

### Tool call: Bash

```
{
  "command": "for j in 12 18; do grep -h \"\\\"job_id\\\": $j[,}]\" data/outputs-recovery/formal/batch-3/events/A.jsonl data/outputs-recovery/formal/batch-3/events/B.jsonl | python3 -c \"\nimport sys, json\nfor l in sys.stdin:\n    e = json.loads(l)\n    if e['event'] not in ('step_started', 'step_ended', 'renewed', 'heartbeat'): print($j, e['worker_id'] if 'worker_id' in e else '', e['event'], {k: e[k] for k in e if k in ('status', 'reason', 'attempt', 'outcome')})\"; done | head -20; grep -n \"def start\\b\\|reconciler\" src/etf_risk/jobs/harness.py | grep -n \"start(\" | head -3",
  "description": "List X1 jobs' worker events and how the reconciler is started"
}
```

## 74. User — 2026-10-28T00:43:37.589Z

### Tool result

```
24:logged and written to the worker's event log (consumer_error).
26:Partition assignments are written to the worker's event log too: assigned, revoked and lost,
src/etf_risk/jobs/kafka.py:51:log = logging.getLogger(__name__)
src/etf_risk/jobs/harness.py:503:        self.log = EventLog(out / "harness.jsonl", "harness", batch=out.name)
src/etf_risk/jobs/harness.py:619:        log = open(self.logs_dir / f"{name}.log", "ab")
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
src/etf_risk/services.py:234:def wait_until_ready(service: str, check: Callable[[], None], *, timeout: float, interval: float = 1.0,
src/etf_risk/jobs/kafka.py:36:explicitly (create_topic: one partition, no replica), since the broker in
src/etf_risk/jobs/cli.py:163:def cmd_create_topic(args) -> int:
src/etf_risk/jobs/cli.py:164:    from etf_risk.jobs.kafka import create_topic
src/etf_risk/jobs/cli.py:166:        create_topic(args.bootstrap, args.topic)
src/etf_risk/jobs/cli.py:368:    handler = {"init-db": cmd_init_db, "create-topic": cmd_create_topic, "submit": cmd_submit, "worker": cmd_worker,
```

## 75. User — 2026-10-28T00:43:37.917Z

### Tool result

```
(eval):1: bad math expression: empty string
(eval):1: bad math expression: operand expected at `}'
(eval):1: bad math expression: empty string
(eval):1: bad math expression: operand expected at `}'
3:617:    def start(self, name: str, *argv: str, extra_env: dict | None = None) -> subprocess.Popen:
5:1185:                self.start("reconciler", "reconciler")
```

## 76. Assistant — 2026-10-28T00:43:47.722Z

### Tool call: Bash

```
{
  "command": "for j in 12 18; do cat data/outputs-recovery/formal/batch-3/events/A.jsonl data/outputs-recovery/formal/batch-3/events/B.jsonl | python3 -c \"\nimport sys, json\nfor l in sys.stdin:\n    e = json.loads(l)\n    if e.get('job_id') == ${j} and e['event'] not in ('step_started', 'step_ended', 'renewed', 'heartbeat'):\n        print(${j}, e.get('worker'), e['event'], {k: e[k] for k in e if k in ('status', 'reason', 'attempt', 'outcome', 'state')})\"; done | head -20",
  "description": "List the X1 jobs' worker events"
}
```

## 77. User — 2026-10-28T00:43:48.684Z

### Tool result

```
12 None delivered {}
12 None claimed {'attempt': 1}
12 None accepted {'attempt': 1}
12 None delivered {}
12 None refused {'reason': 'succeeded'}
12 None delivered {}
12 None refused {'reason': 'succeeded'}
18 None delivered {}
18 None claimed {'attempt': 1}
18 None accepted {'attempt': 1}
18 None delivered {}
18 None refused {'reason': 'succeeded'}
18 None delivered {}
18 None refused {'reason': 'succeeded'}
```

## 78. Assistant — 2026-10-28T00:43:53.884Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md",
  "old_string": "  - **From the code and records:** the console receives only the harness's own output. The\n    workers, the reconciler and the reference run write to their own logs, and Docker's output is\n    captured. The harness's only Kafka client that logs is the publisher it creates for X1's\n    duplicates, first at position 12's claim. Its readiness checks use Kafka clients that log\n    nothing.",
  "new_string": "  - **From the code and records:** the console receives only the harness's own output. The\n    workers, the reconciler and the reference run write to their own logs, and Docker's output is\n    captured.\n  - The line has the format of a Kafka client that was given a Python logger. In the harness, that\n    is only the publisher it creates for X1's duplicates, first at position 12's claim. Its\n    readiness checks use Kafka clients that log nothing."
}
```

## 79. Assistant — 2026-10-28T00:43:57.891Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md",
  "old_string": "  and below the preflights' 45.1–52.4 s on which Part A's section 3 judged the margins. Every case\n  that ran its job after the injection gains about 48 s of slack this way. Rounding D up to a\n  multiple of 5 adds up to 5 s more.\n- **What may explain the shorter runs, without a measured cause:**\n  - batch-3 ran at memory pressure level 1 at all 32 readings, with 2.65–3.25 GiB available;\n  - the preflights and batch-2 ran mostly at level 2, with 1.21–2.04 GiB available in batch-2;",
  "new_string": "  and below the preflights' 45.1–52.4 s on which Part A's section 3 judged the margins. Runs of\n  about 22 s, after a recovery too (10.4), leave about 48 s of the 70.2 s unused. Rounding D up to\n  a multiple of 5 adds up to 5 s more.\n- **What may explain the shorter runs, without a measured cause:**\n  - batch-3 ran at memory pressure level 1 at all 32 readings, with 2.65–3.25 GiB available;\n  - the preflights ran under memory pressure (Part A, section 11), and batch-2 at level 2 at 31 of\n    its 32 readings, with 1.21–2.04 GiB available (section 6);"
}
```

## 80. Assistant — 2026-10-28T00:43:59.382Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md",
  "old_string": "- **Duplicate publications (X1):** they were refused, with one claim per job.",
  "new_string": "- **Duplicate publications (X1):** both duplicates of each job were delivered and refused as\n  `succeeded`, with one claim per job."
}
```

## 81. User — 2026-10-28T00:44:00.178Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 82. User — 2026-10-28T00:44:00.995Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 83. User — 2026-10-28T00:44:01.821Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 84. Assistant — 2026-10-28T00:44:04.760Z

Now a pointer in Part A §13, then the README and spec.

## 85. Assistant — 2026-10-28T00:44:07.505Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-a.md",
  "old_string": "  - **After the session:** `docs/verify_frozen_code.py` confirms that every code record of the\n    batch matches `4fc550e`, with a clean worktree and seed 544.",
  "new_string": "  - **After the session:** `docs/verify_frozen_code.py` confirms that every code record of the\n    batch matches `4fc550e`, with a clean worktree and seed 544.\n  - **Ran on 2026-10-27,** from 16:23 to 16:55. The collector's verdicts were both valid, and the\n    frozen code was verified. The results are in [recovery-part-b.md](recovery-part-b.md), section\n    10, drafted with Claude Code and awaiting the author's review."
}
```

## 86. Assistant — 2026-10-28T00:44:10.049Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md",
  "old_string": "| Documented: E1 has supporting correctness observations; **valid formal E2 recovery-time evidence is outstanding** |",
  "new_string": "| Documented: E1 has supporting correctness observations. **Valid formal E2 recovery-time evidence is now available** from formal batch-3, for this host and configuration only: one batch of 30 jobs, valid for correctness and recovery times, on verified frozen code. Its interpretation (Part B, section 10) is drafted and **awaits the author's review**. batch-1 and batch-2 stay invalid for recovery times |"
}
```

## 87. Assistant — 2026-10-28T00:44:12.900Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md",
  "old_string": "     - the recovery study's documentation, with supporting correctness observations for E1\n       ([docs/recovery-part-a.md](docs/recovery-part-a.md),\n       [docs/recovery-part-b.md](docs/recovery-part-b.md));",
  "new_string": "     - the recovery study's documentation, with supporting correctness observations for E1\n       ([docs/recovery-part-a.md](docs/recovery-part-a.md),\n       [docs/recovery-part-b.md](docs/recovery-part-b.md));\n     - valid formal E2 recovery-time evidence for this host and configuration: formal batch-3,\n       on 2026-10-27, on verified frozen code. All 30 jobs met their deadlines, and none was\n       lost or accepted twice. batch-1 and batch-2 stay invalid for recovery times;"
}
```

## 88. Assistant — 2026-10-28T00:44:14.632Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md",
  "old_string": "     - valid formal E2 recovery-time evidence: both formal batches were invalid for timing;",
  "new_string": "     - the author's review of the batch-3 interpretation, drafted with Claude Code\n       ([docs/recovery-part-b.md](docs/recovery-part-b.md), section 10);"
}
```

## 89. User — 2026-10-28T00:44:15.422Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-a.md has been updated successfully.
```

## 90. User — 2026-10-28T00:44:16.241Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md has been updated successfully.
```

## 91. User — 2026-10-28T00:44:17.061Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md has been updated successfully.
```

## 92. User — 2026-10-28T00:44:17.877Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/README.md has been updated successfully.
```

## 93. Assistant — 2026-10-28T00:44:24.832Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "- the recovery study, documented ([recovery-part-a.md](recovery-part-a.md),\n  [recovery-part-b.md](recovery-part-b.md)), with supporting correctness observations for E1;",
  "new_string": "- the recovery study, documented ([recovery-part-a.md](recovery-part-a.md),\n  [recovery-part-b.md](recovery-part-b.md)), with supporting correctness observations for E1, and\n  valid formal E2 recovery-time evidence for this host and configuration from formal batch-3\n  (2026-10-27). Its interpretation is drafted and awaits the author's review;"
}
```

## 94. Assistant — 2026-10-28T00:44:26.682Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "Outstanding (§11, open items): valid formal E2 recovery-time evidence, a representative\nvalidation of the native processes' memory, and two unresolved intermittent failures of the\nbaseline collector's tests (§10).",
  "new_string": "Outstanding (§11, open items): the author's review of the batch-3 interpretation, a\nrepresentative validation of the native processes' memory, and two unresolved intermittent\nfailures of the baseline collector's tests (§10)."
}
```

## 95. Assistant — 2026-10-28T00:44:28.744Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "E1 has supporting correctness observations, and valid formal E2 recovery-time evidence remains outstanding; the Redis result cache",
  "new_string": "E1 has supporting correctness observations, and valid formal E2 recovery-time evidence for this host and configuration is available from formal batch-3, its interpretation awaiting the author's review; the Redis result cache"
}
```

## 96. Assistant — 2026-10-28T00:44:30.681Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "**Outstanding:** valid formal E2 recovery-time evidence; a representative validation of the native processes' memory (the container limits held under host memory pressure); two unresolved intermittent baseline-collector test failures (§10) |",
  "new_string": "**Outstanding:** the author's review of the batch-3 interpretation; a representative validation of the native processes' memory (the container limits held under host memory pressure); two unresolved intermittent baseline-collector test failures (§10) |"
}
```

## 97. Assistant — 2026-10-28T00:44:32.996Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "its harness, collector and cross-check SQL, with two formal batches documented ([recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)), and E1 has supporting correctness observations;",
  "new_string": "its harness, collector and cross-check SQL, with three formal batches documented ([recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)); E1 has supporting correctness observations, and batch-3 gives valid formal E2 recovery-time evidence for this host and configuration, its interpretation awaiting the author's review;"
}
```

## 98. Assistant — 2026-10-28T00:44:34.993Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "| outstanding: valid formal E2 recovery-time evidence; a representative validation of the native processes' memory; the cause of two intermittent baseline-collector test failures (§10) |",
  "new_string": "| outstanding: the author's review of the batch-3 interpretation; a representative validation of the native processes' memory; the cause of two intermittent baseline-collector test failures (§10) |"
}
```

## 99. Assistant — 2026-10-28T00:44:38.065Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "- the recovery study (E1, E2): its harness, collector and cross-check, two formal\n  batches and their results ([recovery-experiments.md](recovery-experiments.md),\n  [recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)).\n  E1 has supporting correctness observations; valid formal E2 recovery-time\n  evidence remains outstanding;",
  "new_string": "- the recovery study (E1, E2): its harness, collector and cross-check, three formal\n  batches and their results ([recovery-experiments.md](recovery-experiments.md),\n  [recovery-part-a.md](recovery-part-a.md), [recovery-part-b.md](recovery-part-b.md)).\n  E1 has supporting correctness observations. Formal batch-3 gives valid formal E2\n  recovery-time evidence for this host and configuration. Its interpretation is drafted and\n  awaits the author's review;"
}
```

## 100. Assistant — 2026-10-28T00:44:39.985Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "  recorded. Documented in [recovery-part-b.md](recovery-part-b.md): E1 has\n  supporting correctness observations, and valid formal E2 recovery-time evidence\n  remains outstanding.",
  "new_string": "  recorded. Documented in [recovery-part-b.md](recovery-part-b.md): E1 has\n  supporting correctness observations. Valid formal E2 recovery-time evidence for this\n  host and configuration comes from formal batch-3 (section 10), whose interpretation\n  awaits the author's review."
}
```

## 101. User — 2026-10-28T00:44:40.781Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 102. User — 2026-10-28T00:44:41.614Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 103. User — 2026-10-28T00:44:42.430Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 104. User — 2026-10-28T00:44:43.250Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 105. User — 2026-10-28T00:44:44.070Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 106. User — 2026-10-28T00:44:44.881Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 107. User — 2026-10-28T00:44:45.701Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 108. User — 2026-10-28T00:44:46.516Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 109. Assistant — 2026-10-28T00:44:47.805Z

Now the spec's authorship sentence and its open items.

## 110. Assistant — 2026-10-28T00:44:50.732Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "Claude Code: Claude Code proposed the design, ran the batches at the author's\ninstruction and drafted the answers, and the author made every decision and\napproval, the answers included ([recovery-experiments.md](recovery-experiments.md),\nsection 9; [recovery-part-b.md](recovery-part-b.md), section 7).",
  "new_string": "Claude Code: Claude Code proposed the design, ran the first two formal batches at\nthe author's instruction and drafted the answers, and the author made every decision\nand approval, the answers included ([recovery-experiments.md](recovery-experiments.md),\nsection 9; [recovery-part-b.md](recovery-part-b.md), section 7). The author ran the\nthird, batch-3, from a session script that Claude Code prepared. Its interpretation\nwas drafted with Claude Code and awaits the author's review\n([recovery-part-b.md](recovery-part-b.md), section 10)."
}
```

## 111. Assistant — 2026-10-28T00:44:54.186Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "- **E2.** There is no valid formal recovery-time evidence. Both formal batches\n  were invalid for timing: one stopped when the host restarted, and in the other a\n  container of another project broke the exclusive window\n  ([recovery-part-b.md](recovery-part-b.md)).",
  "new_string": "- **E2: evidence available; its interpretation awaits review.** Formal batch-3\n  (2026-10-27) gives valid formal recovery-time evidence for this host and configuration.\n  - The collector's verdicts were both valid, and the frozen code was verified.\n  - All 30 jobs met their deadlines, and none was lost or accepted twice.\n  - The drafted interpretation is not approved\n    ([recovery-part-b.md](recovery-part-b.md), section 10).\n  - The two earlier formal batches stay invalid for timing: one stopped when the host\n    restarted, and in the other a container of another project broke the exclusive window."
}
```

## 112. Assistant — 2026-10-28T00:44:56.329Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md",
  "old_string": "  - **Before a new formal batch:** a C0–D1–C0 preflight, once the test window is free.",
  "new_string": "  - **The C0–D1–C0 preflight:** valid on every check.\n  - **Formal batch-3:** the one further batch the author allowed, on the code frozen at\n    `4fc550e` ([recovery-part-a.md](recovery-part-a.md), section 13)."
}
```

## 113. Assistant — 2026-10-28T00:44:56.901Z

### Tool call: Bash

```
{
  "command": "sed -n 990,1015p docs/spec.md",
  "description": "Show the spec's updated open-items block"
}
```

## 114. User — 2026-10-28T00:44:58.588Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 115. User — 2026-10-28T00:44:59.402Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 116. User — 2026-10-28T00:45:00.221Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/spec.md has been updated successfully.
```

## 117. User — 2026-10-28T00:45:00.358Z

### Tool result

```
  ([result-cache-experiment.md](result-cache-experiment.md),
  [result-cache-part-b.md](result-cache-part-b.md)).

**Open items.** The extension is not complete.
- **E2: evidence available; its interpretation awaits review.** Formal batch-3
  (2026-10-27) gives valid formal recovery-time evidence for this host and configuration.
  - The collector's verdicts were both valid, and the frozen code was verified.
  - All 30 jobs met their deadlines, and none was lost or accepted twice.
  - The drafted interpretation is not approved
    ([recovery-part-b.md](recovery-part-b.md), section 10).
  - The two earlier formal batches stay invalid for timing: one stopped when the host
    restarted, and in the other a container of another project broke the exclusive window.
- **Memory.** The native processes' memory has not been validated
  representatively. The MySQL and Kafka container limits held in one isolated
  check, but under host memory pressure, which also made the native figures
  unrepresentative (above).
- **Tests.** The cause of two intermittent failures of the baseline collector's
  tests is unresolved (§10).
- **Done on 2026-10-27, toward closing E2:**
  - **The page counters,** renamed in M3's code: the host readings record `vm_stat`'s four
    counters by their own names, and older records are read as page counts
    ([host-counters-correction.md](host-counters-correction.md), section 7).
  - **A whole-batch container monitor:** any other project's container event during a batch
    fails its recovery times, and a missing or failed monitor counts as unknown.
  - **Sleep and wake evidence** from the power log, recorded as evidence only
    ([recovery-part-a.md](recovery-part-a.md), section 13).
```

## 118. Assistant — 2026-10-28T00:45:02.535Z

Checking other docs for stale E2 status wording.

## 119. Assistant — 2026-10-28T00:45:03.812Z

### Tool call: Bash

```
{
  "command": "grep -rn \"E2\\b.*outstanding\\|outstanding.*E2\\|no valid formal recovery\\|recovery-time evidence\\|formal E2\\|two formal batches\\|both formal batches\" --include=*.md . 2>/dev/null | grep -v \"^./docs/ai-usage/\\|^./.claude/\\|^./data/\" | cut -c1-220",
  "description": "Find other documents with stale E2 status wording"
}
```

## 120. User — 2026-10-28T00:45:04.658Z

### Tool result

```
(eval):1: no matches found: --include=*.md
```

## 121. Assistant — 2026-10-28T00:45:06.511Z

### Tool call: Bash

```
{
  "command": "git grep -n -E \"E2\\b.*outstanding|outstanding.*E2|no valid formal recovery|recovery-time evidence|formal E2|two formal batches|both formal batches\" -- '*.md' ':!docs/ai-usage' | cut -c1-230",
  "description": "Search tracked Markdown for stale E2 status wording"
}
```

## 122. User — 2026-10-28T00:45:07.069Z

### Tool result

```
README.md:26:| Extension: recovery study, E1 and E2 ([docs/recovery-part-a.md](docs/recovery-part-a.md), [docs/recovery-part-b.md](docs/recovery-part-b.md)) | Documented: E1 has supporting correctness observations. **Valid formal 
README.md:494:     - valid formal E2 recovery-time evidence for this host and configuration: formal batch-3,
docs/host-counters-correction.md:110:- 3.16–8.25 GiB at all readings of both formal batches: batch-1 4.64–5.33 GiB, batch-2
docs/recovery-experiments.md:122:    observations and valid formal E2 recovery-time evidence outstanding; the systems extension is
docs/recovery-part-b.md:25:> Where they say that there are no valid formal recovery times (5.1, 7.2, 7.3), they describe
docs/recovery-part-b.md:303:_Drafted facts:_ there are no valid formal recovery times (5.1). The supplementary observations of
docs/result-cache-experiment.md:200:- **At most two formal batches run on one frozen commit.** Each is kept and reported with its
docs/result-cache-experiment.md:468:   most two formal batches on one frozen commit; a rerun only after a host, cleanup or drift
docs/spec.md:21:  valid formal E2 recovery-time evidence for this host and configuration from formal batch-3
docs/spec.md:39:| Extension (optional) | Job queue (MySQL job table, Kafka), result cache (Redis), Docker Compose; recovery and caching experiments (§11) | **In progress**: the job queue: the MySQL job table, Kafka delivery and t
docs/spec.md:711:| Systems extension | MySQL job table with guarded state transitions, attempt tokens and leases, a store id, and run digests recorded at acceptance ([job-table.md](job-table.md)); a worker running windows → spar
docs/spec.md:796:  E1 has supporting correctness observations. Formal batch-3 gives valid formal E2
docs/spec.md:797:  recovery-time evidence for this host and configuration. Its interpretation is drafted and
docs/spec.md:874:  supporting correctness observations. Valid formal E2 recovery-time evidence for this
docs/spec.md:972:Claude Code: Claude Code proposed the design, ran the first two formal batches at
docs/spec.md:995:  (2026-10-27) gives valid formal recovery-time evidence for this host and configuration.
```

## 123. Assistant — 2026-10-28T00:45:08.853Z

### Tool call: Bash

```
{
  "command": "sed -n 112,130p docs/recovery-experiments.md; git grep -n -E \"batch-2|E2\" -- docs/results.md docs/demo.md | head -12",
  "description": "Read the design doc's status note and check results/demo docs"
}
```

## 124. User — 2026-10-28T00:45:09.380Z

### Tool result

```
  - batch-2's correctness observations stay valid; its recovery times are invalid under the
    approved batch-level protocol, because another project's container broke the exclusive window.
  - Positions 1–17 are not a valid formal sub-batch; they may be reported only as supplementary
    observations, with the limitation stated.
  - Required: Part B with both batches side by side and every outcome kept; the Q1 summary
    corrected when Q1 data is absent; the stale docstring updated; competing containers recorded
    throughout the batch so that the collector detects this; the formal records unchanged; no
    further formal batch for now.
  - Approved: the answers to E1 and E2 as drafted with Claude Code (Part B, section 7). The README
    and spec record the recovery study as documented, with E1 supported by correctness
    observations and valid formal E2 recovery-time evidence outstanding; the systems extension is
    not complete.
- **Throughout.** No formal experiment ran before Part A's approval. Until the fourth review the
  work was documents only.

## 2. Batch protocol (proposal)

### 2.1 Services, jobs and controls
```

## 125. Assistant — 2026-10-28T00:45:13.259Z

### Tool call: Bash

```
{
  "command": "sed -n 80,111p docs/recovery-experiments.md; grep -n \"^#\" docs/recovery-experiments.md | head -20",
  "description": "Read the design doc's review log structure"
}
```

## 126. User — 2026-10-28T00:45:13.809Z

### Tool result

```
  the 84 jobs kept as an alternative (8.1, section 9).
- **Sixth review (2026-10-24).** The policy stays "no acceptance call starts after F"; the
  database's token guards remain the correctness mechanism, and an acceptance transaction already
  under way may commit later ([worker-pipeline.md](worker-pipeline.md)). The live overlap test
  compares monotonic times; focused mutation checks; a code checkpoint commit without the AI logs. No
  service starts before the M2 session releases the window; then a small live preflight, clearly
  labelled, covering the default clock, the real reference launcher, partition ownership and the
  service-dependent recovery paths, with its outcomes kept apart from formal results (8.6). The
  28-job design is the preferred draft; deadlines, memory rules and runtime estimates are finalized
  only after the preflight (8.1–8.3).
- **Later reviews (2026-10-24).**
  - G1–G8 fixed before the live preflight, and G9 after preflight-1 found it
    ([recovery-part-a.md](recovery-part-a.md), section 9).
  - The preflights are functional validation under the recorded memory pressure, not performance or
    memory-budget evidence. Preflight-3 stays invalid for timing, with its correctness observations
    kept apart.
  - M2's 5 and 4.0 GiB gates and its 35.1 s are not validated standards for these experiments; a
    protocol for this 8 GiB Mac instead, with power and swap recorded and observed recovery times
    kept apart from performance claims (the same document, section 12).
  - Approved: this host for correctness observations and for recovery times under its recorded
    conditions, with the limitations stated in Part A; a control C0 at each end of the batch, making
    30 jobs.
  - Required: the collector's timing validity fails a battery reading or a closed lid, and a missing
    reading is handled explicitly, never passed silently; the exit status agrees with the verdicts,
    so any required check that failed or is unknown exits nonzero.
  - Every remaining Part A decision in one table, with its proposed value and reason, for approval
    together (the same document, section 10).
- **Approval (2026-10-25).** All 13 remaining decisions of Part A, section 10, seed 544 included;
  with the two items of 2026-10-24, Part A is approved. The formal batch runs only after the 11
  Kafka cases that skip without a broker pass on the final code and cleanup is complete; the
  documents are committed by explicit path, and the run records the actual HEAD.
- **After the formal batches (2026-10-25).**
1:# Recovery experiments (E1, E2): outline
21:## 1. Questions and scope
42:### 1.1 Decided or required by the author
127:## 2. Batch protocol (proposal)
129:### 2.1 Services, jobs and controls
139:### 2.2 Reference runs
150:### 2.3 Code identity
162:### 2.4 Worker startup order and the partition
184:### 2.5 One job at a time
190:## 3. Failure cases
192:### 3.1 Cases
218:### 3.2 Expected times and Kafka conditions
242:## 4. Clocks, deadlines and snapshots
244:### 4.1 Clock
259:### 4.2 Deadlines
283:### 4.3 The deadline observation
306:### 4.4 Quiescence
315:### 4.5 The final snapshot
325:### 4.6 Container peaks by segment
334:## 5. Metrics
```

## 127. Assistant — 2026-10-28T00:45:23.550Z

Edits are in. Running documentation checks next: links, table shapes, whitespace, a diff to confirm sections 1–9 are untouched, and a script that recomputes every §10.4 number from the records.

## 128. Assistant — 2026-10-28T00:45:25.047Z

### Tool call: Bash

```
{
  "command": "git diff --check; echo \"diff-check exit $?\"; git diff --stat; echo ---; git diff -U0 docs/recovery-part-b.md | grep -E \"^-[^-]\" | head; echo \"(removed lines above, if any)\"; git grep -n -E \"recovery-part-b|README\\.md|spec\\.md|recovery-part-a\" -- tests | head",
  "description": "Check whitespace, diff stats, removed lines and doc-reading tests"
}
```

## 129. Assistant — 2026-10-28T00:45:40.414Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/check_docs.py",
  "content": "\"\"\"Documentation checks: relative links resolve, tables keep their column count, Part B 10.4 matches the records.\"\"\"\nimport csv\nimport json\nimport re\nimport sys\nfrom pathlib import Path\n\nroot = Path(sys.argv[1])\nfiles = [root / \"README.md\", root / \"docs/spec.md\", root / \"docs/recovery-part-a.md\", root / \"docs/recovery-part-b.md\"]\nproblems = 0\n\nfor f in files:\n    text = f.read_text()\n    for target in re.findall(r\"\\]\\(([^)#\\s]+)(?:#[^)]*)?\\)\", text):\n        if target.startswith((\"http://\", \"https://\", \"mailto:\")):\n            continue\n        if not (f.parent / target).exists():\n            problems += 1\n            print(f\"{f.name}: broken link {target}\")\n    lines = text.splitlines()\n    for i, line in enumerate(lines):\n        if re.fullmatch(r\"\\|(\\s*:?-{3,}:?\\s*\\|)+\", line.strip()):\n            width = lines[i - 1].count(\"|\")\n            j = i + 1\n            while j < len(lines) and lines[j].startswith(\"|\"):\n                if lines[j].count(\"|\") != width:\n                    problems += 1\n                    print(f\"{f.name}:{j + 1}: {lines[j].count('|') - 1} cells, header has {width - 1}\")\n                j += 1\nprint(\"links and tables checked in\", len(files), \"files\")\n\n# Part B 10.4 against the records\nfolder = root / \"data/outputs-recovery/formal/batch-3\"\nread = lambda p: [json.loads(line) for line in p.read_text().splitlines() if line.strip()]\nharness = read(folder / \"harness.jsonl\")\nworkers = read(folder / \"events/A.jsonl\") + read(folder / \"events/B.jsonl\")\ndeadlines = {e[\"job_id\"]: e for e in harness if e[\"event\"] == \"deadline\"}\ninjections = {e[\"job_id\"]: e for e in harness if e[\"event\"] == \"injection\"}\naccepted = {}\nfor e in workers:\n    if e[\"event\"] == \"accepted\":\n        accepted[e[\"job_id\"]] = min(accepted.get(e[\"job_id\"], e[\"mono\"]), e[\"mono\"])\ncsv_rows = {int(r[\"position\"]): r for r in csv.DictReader(open(folder / \"injections.csv\"))}\n\npart_b = (root / \"docs/recovery-part-b.md\").read_text()\nsection = part_b[part_b.index(\"### 10.4\"):part_b.index(\"### 10.5\")]\ntable = [line for line in section.splitlines() if re.match(r\"\\| \\d+ \\|\", line)]\nassert len(table) == 30, len(table)\n\n\ndef same(doc: str, value) -> bool:\n    if value is None:\n        return not re.fullmatch(r\"−?\\d+\\.\\d\", doc)\n    return doc.replace(\"−\", \"-\") == f\"{value:.1f}\" or (doc in (\"−0.0\", \"0.0\") and abs(value) < 0.05)\n\n\nfor line in table:\n    cells = [c.strip() for c in line.strip(\"|\").split(\"|\")]\n    position, case = int(cells[0]), cells[1]\n    r = csv_rows[position]\n    job = int(r[\"job_id\"])\n    d, inj, acc = deadlines[job], injections.get(job, {}), accepted.get(job)\n    num = lambda x: float(x) if re.fullmatch(r\"-?\\d+(\\.\\d+)?\", x or \"\") else None\n    expected = {\n        2: num(r[\"detection_s\"]), 3: num(r[\"rerun_s\"]),\n        4: acc - d[\"t_submit\"] if acc else None,\n        5: acc - inj[\"t_inj\"] if acc and inj.get(\"t_inj\") and case not in (\"C0\", \"W5a\", \"W5b\") else None,\n        7: acc - d[\"reference_mono\"] if acc and case not in (\"W5a\", \"W5b\") else None,\n        8: d[\"deadline_s\"],\n        9: d[\"deadline_mono\"] - acc if acc and case not in (\"W5a\", \"W5b\") else None,\n    }\n    if case != r[\"case\"]:\n        problems += 1\n        print(f\"position {position}: case {case} != {r['case']}\")\n    for col, value in expected.items():\n        doc = cells[col].replace(\"**\", \"\")\n        if col == 8:\n            ok = float(doc) == value\n        else:\n            ok = same(doc, value)\n        if not ok:\n            problems += 1\n            print(f\"position {position} ({case}) column {col}: document {doc!r}, records {value}\")\n    deadline = \"on time\" if r[\"timeliness\"] == \"on time\" and r[\"deadline_met\"] == \"yes\" else r[\"timeliness\"]\n    if cells[10] != deadline:\n        problems += 1\n        print(f\"position {position}: deadline {cells[10]!r} != {deadline!r}\")\n    if \"return\" in cells[6]:\n        outage = float(re.search(r\"(\\d+\\.\\d) s after\", cells[6]).group(1))\n        if f\"{inj['restored'] - inj['t_inj']:.1f}\" != f\"{outage:.1f}\":\n            problems += 1\n            print(f\"position {position}: outage {outage} != {inj['restored'] - inj['t_inj']:.2f}\")\nprint(\"Part B 10.4: 30 rows checked against harness.jsonl, the worker events and injections.csv\")\nprint(\"problems:\", problems)\nsys.exit(1 if problems else 0)\n"
}
```

## 130. Assistant — 2026-10-28T00:45:42.248Z

### Tool call: Bash

```
{
  "command": "python3 -I /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/check_docs.py \"$PWD\"; echo \"exit $?\"",
  "description": "Check links, table shapes and Part B 10.4's numbers"
}
```

## 131. User — 2026-10-28T00:45:43.228Z

### Tool result

```
diff-check exit 0
 README.md               |   8 +-
 docs/recovery-part-a.md |   3 +
 docs/recovery-part-b.md | 303 ++++++++++++++++++++++++++++++++++++++++++++++++
 docs/spec.md            |  53 +++++----
 4 files changed, 345 insertions(+), 22 deletions(-)
---
(removed lines above, if any)
tests/mutation_check.py:31:The focused mutations, added on 2026-10-24 (and for the gaps of docs/recovery-part-a.md the same
tests/mutation_check.py:317:    # Focused: the gaps G1-G7 and G9 of docs/recovery-part-a.md, fixed on 2026-10-24.
tests/mutation_check.py:353:    # Focused: the power and swap recording of 2026-10-24 (docs/recovery-part-a.md, section 12).
tests/test_jobs_harness.py:307:# The setup, quiescence and the final records (gaps G1, G2, G5 and G7 of docs/recovery-part-a.md)
tests/test_jobs_harness.py:480:# The host's state (docs/recovery-part-a.md, section 12)
tests/test_model.py:1:"""Hand-calculated checks for the reference model (docs/spec.md, section 3).
tests/test_recovery_collector.py:63:    """A host_state event as the harness writes it since 2026-10-27 (docs/recovery-part-a.md, section 12)."""
tests/test_recovery_collector.py:407:# The host protocol's timing conditions (docs/recovery-part-a.md, section 12)
```

## 132. User — 2026-10-28T00:45:44.040Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/check_docs.py (file state is current in your context — no need to Read it back)
```

## 133. User — 2026-10-28T00:45:44.288Z

### Tool result

```
links and tables checked in 4 files
Part B 10.4: 30 rows checked against harness.jsonl, the worker events and injections.csv
problems: 0
exit 0
```

## 134. Assistant — 2026-10-28T00:45:57.568Z

All checks pass: no broken links, no table-shape errors, and all 30 rows of the §10.4 table match the records. One last strictness check on the "all within MySQL outages" claim, using no tolerance.

## 135. Assistant — 2026-10-28T00:46:00.981Z

### Tool call: Bash

```
{
  "command": "python3 - data/outputs-recovery/formal/batch-3 <<'EOF'\nimport json, sys\nfrom pathlib import Path\nf = Path(sys.argv[1]); read = lambda p: [json.loads(l) for l in p.read_text().splitlines() if l.strip()]\nH = read(f / \"harness.jsonl\"); R = [e for p in (f / \"events\").glob(\"reconciler-*.jsonl\") for e in read(p)]\nW = read(f / \"events/A.jsonl\") + read(f / \"events/B.jsonl\")\nwin = [(e[\"t_inj\"], e[\"restored\"]) for e in H if e[\"event\"] == \"injection\" and e.get(\"service\") == \"mysql\"]\nfor name, evs in ((\"pass_failed\", [e for e in R if e[\"event\"] == \"pass_failed\"]), (\"retry\", [e for e in W if e[\"event\"] == \"retry\"])):\n    strict = sum(any(a <= e[\"mono\"] <= b for a, b in win) for e in evs)\n    late = [round(e[\"mono\"] - b, 2) for e in evs for a, b in win if b < e[\"mono\"] <= b + 1]\n    print(name, len(evs), \"strictly inside:\", strict, \"| after the harness's return reading, by s:\", late)\nEOF",
  "description": "Check reconciler failures and retries against MySQL outages strictly"
}
```

## 136. User — 2026-10-28T00:46:01.823Z

### Tool result

```
pass_failed 24 strictly inside: 24 | after the harness's return reading, by s: []
retry 55 strictly inside: 55 | after the harness's return reading, by s: []
```

## 137. Assistant — 2026-10-28T00:46:05.400Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md",
  "old_string": "job's result was accepted. For K2, D1 and D2 the two origins differ by the outage: 31.8 and 31.9 s\nfor Kafka, and 31.2 s for MySQL.",
  "new_string": "job's result was accepted. For K2, D1 and D2 the two origins differ by the outage: 31.8 and 31.9 s\nfor Kafka, and 31.2 s for MySQL. Every time is computed from unrounded monotonic times, so a\ndifference of two rounded entries can be 0.1 s off."
}
```

## 138. Assistant — 2026-10-28T00:46:07.275Z

### Tool call: Bash

```
{
  "command": "python3 -I /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/check_docs.py \"$PWD\" | tail -1; git diff --check && echo \"diff-check clean\"; git status --short",
  "description": "Rerun the documentation checks after the last edit"
}
```

## 139. User — 2026-10-28T00:46:08.570Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-b.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 140. User — 2026-10-28T00:46:08.907Z

### Tool result

```
problems: 0
diff-check clean
 M README.md
 M docs/recovery-part-a.md
 M docs/recovery-part-b.md
 M docs/spec.md
```

## 141. Assistant — 2026-10-28T00:46:18.066Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/e2-evidence-plan.md",
  "old_string": "[REDACTED:memory]",
  "new_string": "[REDACTED:memory]"
}
```

## 142. User — 2026-10-28T00:46:18.945Z

### Tool result

```
[REDACTED:memory]
```

## 143. Assistant — 2026-10-28T00:46:20.246Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "[REDACTED:memory]"
}
```

## 144. User — 2026-10-28T00:46:21.610Z

### Tool result

```
[REDACTED:memory]
```

## 145. Assistant — 2026-10-28T00:47:03.223Z

I've drafted the batch-3 results as Part B §10 and updated the README and spec. Nothing is committed, pushed or merged, and no experiment ran.

Part B §10 says at the top that none of it is approved, and so does each drafted answer and the limits. Your approval is not recorded anywhere.

**What changed (uncommitted, in the `e2-evidence` worktree)**
- **`docs/recovery-part-b.md`:** one dated note added at the top, and a new section 10 at the end; no existing line was removed. Sections 1–9 are unchanged, so batch-1 and batch-2 keep their invalid recovery-time verdicts. The note explains that the earlier "no valid formal recovery times" statements describe those two batches.
- **Section 10's contents:**
  - all three batches side by side, as Part A §13 requires;
  - what happened during the session, including where the Kafka console line came from;
  - correctness, with the reason for the two missing W5a reports;
  - recovery times, with the timing origins spelled out;
  - why the deadline slack was larger than expected;
  - host conditions, the drafted answers, the limits and the records.
- **`docs/recovery-part-a.md` §13:** one bullet saying batch-3 ran, with a pointer to Part B §10. All amendments are kept.
- **README and spec:**
  - "outstanding" becomes "valid formal E2 evidence is available for this host and configuration; its interpretation awaits the author's review";
  - the outstanding item becomes your review;
  - the spec's credit sentence now says Claude Code ran the first two formal batches and you ran batch-3.
- **`data/outputs-recovery/formal/batch-3.verify.txt`:** I reran the frozen-code check and saved its output (exit 0, "FROZEN CODE: VERIFIED"). It sits beside the batch folder, whose fingerprint is still `34fa05af8be692b3`.

**How the times are compared.** Every column names its starting point: the submit, the fault, or the point the deadline counts from. For K2, D1 and D2 the deadline counts from the service's return, not its stop. So the table shows both times and the outage between them. For example, K2 finished 68.6 s after Kafka was stopped, which is 36.7 s after Kafka came back, against a 125 s deadline. The "service's return" is the harness's own readiness check, which can lag slightly. That explains D2's −0.1 s at position 28.

**Documentation checks (all passed)**
- `git diff --check`: clean.
- In all four files, every relative link points to an existing file and every table row has the right number of columns.
- A script recomputed every number in the 30-row timing table from the raw records and found 0 differences.
- All 24 failed reconciler passes and all 55 retries fall strictly inside MySQL outages, with no margin needed.
- No test reads these documents, so there was no test suite to run for them.

**Correction to my last report.** I said the harness's Kafka publisher was created at t+686.4 s. It was actually created at t+664.0 s, at the first duplicate when job 12 was claimed. The outage times I gave were when each outage ended. The full windows were:
- t+873.8–877.1 s (K1);
- t+1401.7–1404.8 s (K1);
- t+1753.8–1785.7 s (K2).

The conclusion doesn't change: the line comes from that publisher, and which outage caused it isn't recorded. Part B uses the corrected facts.

`★ Insight ─────────────────────────────────────`
- Each deadline is D = ceil5(B + 2S): B covers the wait before the job runs again, and 2S gives the run itself 70.2 s.
- Batch-3's detection times were close to B (58.4–64.0 s against 65 s for W2–W6). The large slack came almost entirely from the run: about 22 s used out of 70.2 s.
- So a slower state of this machine would eat into the run budget first. Batch-2's late jobs fit that pattern.
`─────────────────────────────────────────────────`

## Proposed conclusions (drafted, awaiting your review)
1. **E1:** batch-3 is a second batch whose correctness checks all pass, with the same outcome as batch-2.
   - All 30 jobs had exactly one accepted result, and every one matched the reference run.
   - This includes the 10 jobs claimed twice and the 8 run twice.
   - The two W5a jobs have no report in the worker's log, which is by design: the worker is killed after MySQL records the acceptance but before it writes its own log entry.
2. **E2:** batch-3 gives the valid formal recovery times, for this machine and configuration only, with two jobs per case.

   | Case | Recovery |
   |---|---|
   | W1 (worker killed before its claim) | standby picked up the job 13.6–14.9 s after the kill; finished 35.2–36.2 s after it |
   | W2, W3, W4, W6 (worker killed or stopped after its claim) | claimed again 58.4–64.0 s after the fault; finished 79.9–86.2 s after it |
   | W7 (whole worker tree stopped for 90 s) | finished 112.4–112.5 s after the stop |
   | K1 (Kafka restart) | the attempt went on; finished 16.3–17.2 s after the restart began |
   | K2 (Kafka stopped around the submit) | finished 36.7–36.9 s after Kafka's return |
   | D1, D2 (MySQL stopped) | MySQL was back before the job's lease ran out, so every attempt went on |
   | W5a, W5b (killed after acceptance) | stayed succeeded with one accepted result |
   | X1 (duplicate publications) | refused as already succeeded |

3. **Deadlines:** all 30 jobs met theirs, with 51.9–140.1 s to spare. That is more than Part A expected, mainly because runs took about 22 s instead of the 40–50 s assumed. The memory pressure stayed at its lowest level throughout, but nothing measured shows that as the cause.
4. **Unchanged:** batch-1 and batch-2 stay invalid for recovery times.
5. **Not observed:** the case where MySQL comes back too late and the job's first attempt is cancelled and rerun (the fenced branch for D1 and D2).

## Remaining work
1. Your review of Part B §10: facts, drafted answers and limits. Then I record the approval with its date, or make your edits.
2. Commit the four documents by explicit path. Whether to commit before or after your review is your call.
3. Push `feature/e2-evidence-tooling` and open the PR. There's no `gh` CLI here, so you open it in the browser. Then you merge it.
4. Optional: `docs/recovery-experiments.md` §1.1 still has the dated 2026-10-25 entry saying E2 is outstanding. I left it as history; I can add a dated 2026-10-27 entry if you want.
5. The extension is still incomplete:
   - checking the native processes' memory properly (your separate decision);
   - the cause of the intermittent baseline-collector test failures (PR still to open);
   - this session's AI logs, committed separately only when you name them.

## PR title and description
Written for: reviewers of the PR into `main` (you, and possibly course staff).

**Title:** Close the E2 evidence gap: named vm_stat counters, a whole-batch container monitor, and formal batch-3

```markdown
## Summary
- **Counters:** recovery host readings record `vm_stat`'s page-ins, page-outs, swap-ins and swap-outs by name, through one parser shared with E3. Older records are read as page counts, and the historical records are unchanged.
- **Container monitor:** `docker events` runs for the whole batch. It records only the time, the action's verb and whether the container belongs to this project, never names or commands. Any event from another project's container fails the recovery-time verdict, and a missing or failed monitor counts as unknown.
- **Sleep and wake evidence:** taken from `pmset -g log` and recorded as evidence only, never a gate. A batch without it says so.
- **Formal batch-3:** run on code frozen at `4fc550e` with the approved plan (`plan-544.json`, seed 544).
  - The collector's verdicts were both valid, and every code record matches the frozen commit.
  - All 30 jobs met their deadlines, none was lost or accepted twice, and there were 0 events from other projects' containers.
- **Documents:**
  - Part B §10 reports batch-3 next to batch-1 and batch-2, whose invalid verdicts are kept;
  - Part A §13 records the batch-3 amendment;
  - README and spec now say valid formal E2 evidence is available for this host and configuration.

## Status of the interpretation
Part B §10 was drafted with Claude Code and awaits the author's review; no approval is recorded. The approved answers in Part B §7 are unchanged.

## Verification
- Full offline suite on `12c925d`: 1078 passed, 38 skipped (live services only), 0 failed.
- Mutation checks: 14 of 14 caught; then 6 of 6 for `4fc550e`.
- Live C0–D1–C0 preflight on `12c925d`: valid on every check.
- `4fc550e` (record only the event verb) is a recorded exception: two regression tests and 205 focused tests passed, with no new preflight, by the author's decision.
- `docs/recovery-batch-3.zsh` enforced the preconditions. `docs/verify_frozen_code.py` confirmed all 21 code records match the frozen commit.
- Documentation checks: links, table shapes, and all 30 timing rows recomputed from the records.

## Not in this PR
- Batch records (`data/`, outside Git) and the AI logs.
- Native-memory validation.
- The baseline-collector test flake.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

If you approve §10 before committing, I'll replace the "Status of the interpretation" section with the approval date.
