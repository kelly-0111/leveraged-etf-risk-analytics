# Claude Code message 24

Session: `a9a2be5c-8da0-4ec5-be57-f251b5676fe9` · prompt sent 2026-10-24 23:00 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): email ×3, git-user ×96, home ×559, memory ×18, model-reasoning ×51, user ×56. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-25T04:00:48.120Z

This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

<tools-used-before-summary>AskUserQuestion, Bash, Edit, ListAgents, Monitor, Read, ToolSearch, Write</tools-used-before-summary>
Summary:
1. Primary Request and Intent:
   - **Overall project.** The recovery experiments E1/E2 (spec §11, milestone M3) of a CS544 project, in worktree `~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness`, branch `feature/recovery-harness`. Claude Code writes the tooling at the author's decision; the experiments' decisions, runs and answers are the author's.
   - **Latest user request (verbatim):** "I approve using this host for correctness observations and recovery times under its recorded conditions, with the limitations stated in Part A. I also approve adding the two bracketing controls, making 30 jobs. Implement the plan option and collector timing-validity checks for battery power or a closed lid. Handle missing power readings explicitly rather than silently passing them. Add focused tests, update Part A and the commands, and commit the tooling changes by explicit path. Then present the final Part A for review. Do not run the formal batch yet."
   - **Earlier standing instructions still in effect:**
     - Keep Part A provisional, except for the approved items: this host for correctness and recovery times under its recorded conditions; the 30 jobs with bracketing controls.
     - Do not run formal experiments, push or merge.
     - Preserve all earlier records.
     - Keep preflight-3 recorded as invalid for timing and never relabel it; keep its correctness observations.
     - Do not use M2's 5/4 GiB gates or its 35.1 s as validated standards; the 2.5 GiB threshold was withdrawn.
     - Distinguish observed recovery times on this host from performance claims.
     - Report findings before fixing out-of-scope items.

2. Key Technical Concepts:
   - **Job system:**
     - MySQL job table with attempt-token guards (the correctness mechanism); Kafka with one partition; workers, reconciler, launcher watchdog, host flock lock.
     - Deadline F = m0 + lease − fence_margin. Policy: no acceptance call (first or retried) starts after F; a transaction already started may commit later.
     - Leases are wall-clock values in the database, so a host sleep makes them expire while processes are suspended.
   - **Default timing:** lease 60, renew 10, fence_margin 10, session 15, heartbeat 3, reconciler P 5, publication grace 30. Deadlines D = ceil5(B + 2S) with S = 35.1 s (also measured under pressure).
   - **Harness** (`etf_risk.jobs.harness`):
     - Commands: `plan --purpose preflight|formal [--jobs]`, `estimate`, `batch --out .../<purpose>/<batch> [--formal]`.
     - Records: setup_error, final_error, cleanup.txt, host_state events (start / job / end), Spark scratch diff.
     - The batch folder is resolved to an absolute path (G9).
     - `Settings.bracket_controls` puts a C0 control at each end of the shuffled order (30 jobs by default).
   - **Collector** (`analysis/collect_recovery_measurements.py`):
     - Per-job metrics and verdicts; host_conditions (power and lid; unknown fails); two verdicts, correctness and timing.
     - `collect()` doesn't write; only `main()` writes validity.json, injections.csv and tally.csv.
   - **Mutation checks** (`tests/mutation_check.py`): focused mutations name their own test file. There are now 98 mutations, 49 of them focused.
   - **Host protocol** (Part A §12):
     1. AC power;
     2. lid open;
     3. `caffeinate -dims` plus the clock check;
     4. no competing tests;
     5. memory pressure and swap recorded, never gated;
     6. C0 controls in the same batch (one at each end, approved);
     7. every outcome kept, never relabelled.

     Three claim types: correctness (time-free checks); recovery times observed on this host (valid batches only, reported with the host record and controls); performance claims (not made from this host).
   - **macOS details:** clamshell sleep on battery despite `caffeinate -i`; `pmset -g batt`; `ioreg -r -k AppleClamshellState -d 4`; `sysctl kern.memorystatus_vm_pressure_level`; psutil `swap_memory` (sin/sout).

3. Files and Code Sections:
   - **src/etf_risk/jobs/harness.py**
     - Recent changes (commit 5a81bc5):
       ```python
       jobs_per_case: int = 2               # P1, the preferred draft: 2 per case, one batch (28 jobs)
       bracket_controls: bool = True        # a C0 control at each end of the shuffled order (30 jobs; approved)
       ...
       def plan_jobs(settings: Settings, seed: int) -> list[str]:
           """...with bracket_controls, a C0 control at each end ... (docs/recovery-part-a.md, section 12, condition 6)."""
           jobs = [case for case in settings.cases for _ in range(settings.jobs_per_case)]
           random.Random(seed).shuffle(jobs)
           return ["C0", *jobs, "C0"] if settings.bracket_controls else jobs
       # make_plan:
       controls = "a C0 at each end" if jobs is None and settings.bracket_controls else None
       return {"format": 1, "purpose": purpose, "seed": seed, "order": "shuffled" if jobs is None else "as listed",
               "controls": controls, ...}
       ```
     - Earlier (8c5331d): `parse_power_source(text)`, `parse_lid_closed(text)`, `_command_output(*argv)`, `host_state(command=_command_output)`. The last returns available_bytes, total_bytes, swap_used_bytes, swap_in_bytes, swap_out_bytes, memory_pressure, power_source and lid_closed. Logged as `self.log.log("host_state", stage="start"|"job"|"end", ...)`.
     - Earlier (a94eefe): `out = Path(out).resolve()  # G9` in `Batch.__init__`.
     - Earlier (7bd4d20): setup_error handling; `services_started`; `close_stores()`; cleanup.txt; host memory; `spark_scratch()`.
   - **analysis/collect_recovery_measurements.py** (commit 5a81bc5)
     ```python
     CORRECTNESS_CHECKS = ("code_identity", "fingerprints_agree", "inputs_unchanged", "records_complete")
     TIMING_CHECKS = (*CORRECTNESS_CHECKS, "clock", "host_power", "host_lid")
     def host_conditions(b, host, ran) -> dict:
         start = (named(b.harness, "host_state", stage="start") or [None])[0]
         end = (named(b.harness, "host_state", stage="end") or [None])[-1]
         readings = [("start", start), *[(position, host.get(position)) for position in ran], ("end", end)]
         def condition(key, fails) -> dict:
             failed = [where for where, r in readings if r is not None and r.get(key) is not None and fails(r[key])]
             unknown = [where for where, r in readings if r is None or r.get(key) is None]
             return {"passed": not failed and not unknown, "failed": failed, "unknown": unknown}
         return {"host_power": condition("power_source", lambda value: value != "AC Power"),
                 "host_lid": condition("lid_closed", lambda value: value is not False)}
     def verdict(validity, checks) -> dict:
         failed = [name for name in checks if validity[name].get("passed") is not True]
         return {"valid": not failed, "failed": failed}
     ```
     - `machine_state` removed; validity uses `**host_conditions(b, host, [r["position"] for r in rows if r.get("job_id") is not None])`.
     - `result["verdicts"]` is added and written to validity.json.
     - `main()` prints the "correctness observations: …" and "recovery times: …" lines; the exit code is still 1 if any validity check failed.
     - Also: `host_readings` (reads legacy host_memory), `host_row(host, position, end)` (swap_out_during_bytes), `host_summary`.
     - FIELDS now include host_available_bytes, memory_pressure, power_source, lid_closed and swap_out_during_bytes.
   - **tests/test_jobs_harness.py**
     - Updated for 30 jobs: Counter with C0 = 4; estimate (30, 3070); alternative (44, 4473).
     - New: `test_the_controls_bracket_the_shuffled_order_and_a_listed_order_gets_none`.
     - Earlier: G9 regression test; host_state parser tests; setup-failure tests (now also assert host_state start/end).
   - **tests/test_recovery_collector.py**
     - `host_reading(stage, position=None, *, power="AC Power", lid_closed=False)`; `make_batch(tmp_path, *, step_code=CODE, host=True)` writes AC/open readings for start, positions 1–3 and end.
     - `set_reading(batch, where, **fields)`.
     - New tests: battery fails timing but not correctness (main returns 1); closed lid at end; missing reading/value is unknown and never passes; a pre-power batch has unknown conditions.
     - Base validity test asserts both verdicts valid.
   - **tests/test_recovery_synthetic.py**: monkeypatches `harness.host_state` with a fixed AC/lid-open reading and asserts both verdicts valid.
   - **tests/mutation_check.py**: new focused mutations controls-not-bracketed, battery-passes, lid-closed-passes, unknown-reading-passes, timing-verdict-without-host, end-reading-not-required (98 mutations in all).
   - **docs/recovery-part-a.md** (uncommitted, to be finalized). Current state:
     - Title still "Recovery experiments: Part A proposal, 28 jobs (DRAFT)"; the header says four preflights.
     - §1: 28 jobs. §3: S-under-pressure note. §7: commands with pmset/ioreg checks and `caffeinate -dims`.
     - §8 table: 28 jobs 2,836; Batch 2,936 (about 49 min); Controls bullet "proposed".
     - §9: G1–G9 fixed.
     - §10 rows include Workload (P1) 28 jobs, Controls, "This host's memory state … the author's decision".
     - §11: preflight-1 to -4 (preflight-3 shown with correctness observations only; preflight-4 table).
     - §12: protocol and three claim types; its Tooling bullet still says the plan option and collector flag are not implemented.
   - **docs/recovery-experiments.md** (outline; uncommitted): revisions 8 and 9 added; section 9 "Not done" lists the plan option and the collector flag, both now implemented.
   - **Records** (gitignored, preserved) in `data/outputs-recovery/preflight/`: preflight-1..4, plan-1/3/4.json, console logs, job-tests.txt, live-pipeline.txt, full-offline-suite.txt.
   - **Memory file** `~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md`, with its pointer in MEMORY.md (updated via `sed`, never printed).

4. Errors and fixes:
   - zsh didn't word-split `$IDS` for `--only`; fixed with `${=IDS}` or explicit lists.
   - `events_named(events, name, ...)` clashed with a `name=` field; made the parameters positional-only (`events, event, /`).
   - The `spark_running` bug: `step_ended` uses `name`, not `step`; fixed.
   - The synthetic stand-in did not set `services_started`, so quiescence was skipped; the test caught it and it was fixed.
   - `host_row` looked up `host.get("end")` by mistake; it now takes the end reading as a parameter.
   - Doc replacements failed on exact-text mismatches (line wraps); redone with the exact text.
   - G9: relative batch folder paths broke the reference launcher (exit 71); fixed in a94eefe.
   - **User feedback applied:**
     - Don't treat M2's thresholds or its 35.1 s as standards; justify or drop 2.5 GiB (dropped).
     - Keep preflight-3 invalid and never relabel it.
     - A premature handover must not start anything.
   - preflight-3's monitor reported "30m" (wall time) while monotonic time showed 8 min; caused by the clamshell sleep.

5. Problem Solving:
   - Solved: the acceptance-deadline policy (including retries after F); monotonic overlap checks; the G1–G9 gaps; host power/swap/pressure/lid recording; the bracketing controls; explicit timing-validity checks; the W3 rerun is valid (preflight-4: 2 claims, requeue 59.1 s, finish 117.1 s; controls 45.1 and 50.9 s; AC power; pressure level 2; swap +836 MiB).
   - Verdicts under the new checks, computed in memory with folders unchanged (mtime-verified):
     - preflight-1: correctness invalid (records_complete);
     - preflight-2: correctness valid, recovery times invalid (power and lid unknown);
     - preflight-3: correctness valid, recovery times invalid (clock, power, lid);
     - preflight-4: both valid.
   - 30-job estimate: 3,039 s (50.7 min) with preflight values; 51.2 min with the original assumptions; 53.5 min if T is 55 s; 53.4 min if restores take 20 s.

6. All user messages:
   - "You have the exclusive window for offline dependency setup and tests. ... Do not start Docker or live tests yet. Run the new and affected tests, fix failures, and add deterministic coverage for: the first acceptance call after deadline F; fault arming without changing partition ownership; missing crash records and unknown observations; late completion and all frozen SQL verdicts. Fix the acceptance-deadline discrepancy... Add monotonic launcher timestamps... Then run a synthetic end-to-end harness/collector test without services... propose a smaller formal experiment... Keep the current 84-job design as an alternative. Do not change Part A decisions or run formal experiments without approval."
   - (Pasted) "The offline progress is good. Keep the policy as 'do not start an acceptance call after F'; database token guards remain the correctness mechanism. Document that an already-started transaction may commit later. Update the live overlap test to use monotonic fields, add focused mutation checks, and prepare a code checkpoint commit excluding AI logs. Keep Part A unapproved. Do not start services until M2 releases the window. Then run a small, clearly labelled live preflight... Preserve all preflight outcomes separately from formal results. Use the proposed 28-job design as the preferred draft, but finalize deadlines, memory rules and runtime estimates only after the preflight. Do not run the formal experiment yet."
   - "M2 has finished and released the test window. Run the prepared live preflight, keeping every outcome separate from formal results. Report failures, missed injections and unknown observations without discarding them. Do not run the formal experiment yet."
   - "Correction: M2's preflight failed; the memory check did not run and the window was not released. My previous handover message was premature. Do not start tests or containers. If anything has already started, report its state before taking further action. Continue read-only work only until I confirm the handover."
   - (Pasted) "Prepare a concise, executable Part A proposal for the preferred 28-job design. Include: ... Cross-check every command, event name and required record against the committed tooling. Review the service-only paths for concrete gaps, without changing the agreed scope. Put all remaining author decisions in one short table with your recommended choices. Keep memory rules provisional pending M2. Do not mark Part A approved or start services or formal runs."
   - (Pasted) "Approved: fix G1–G8 before the live preflight, with focused tests and mutation checks where useful. Ensure setup failures are recorded, quiescence handles the harness's own connections correctly, and cleanup listings, per-job host memory and Spark scratch observations are actually produced. Correct the X1 description and command examples. Commit the tooling fixes and the clearly marked draft document by explicit path. Run focused offline checks only for now; no Spark, services or full-suite runs. Part A remains unapproved. Keep the proposed workload, deadlines and memory rules provisional. Report completed fixes and the remaining live-preflight steps together."
   - "Your fixes and focused test results are noted. Wait for M2's explicit handoff, then run the live preflight and the remaining live suites sequentially. Preserve all failures and unknown outcomes, update the draft using the observations, and report readiness for formal experiments. Keep Part A provisional; do not run formal experiments, push, or merge yet."
   - "M2 has explicitly handed the exclusive test window to you. Its isolated memory check did not run because host available memory was only about 1.2 GiB; container memory budgets remain unvalidated. Proceed with the planned live preflight, job tests, and live pipeline tests sequentially. Then run the full offline suite, including Spark tests, after service cleanup. Preserve all failures, misses, and unknown outcomes. Treat the preflight as functional validation under the recorded memory pressure, not as valid performance or memory-budget evidence. Update the draft and report remaining blockers. Keep Part A provisional. Do not run formal experiments, push, or merge."
   - (Interrupted, addressed to M2) "M3 has finished ... Recheck the current machine state ... Aim for about 5 GiB available ... enforce the approved 4.0 GiB idle gate ... Do not push or merge." The user interrupted it; it was not acted on.
   - (Pasted) "M2 has completed its check and released the test window. Container limits were validated under host memory pressure, with documented sampling limitations; native-process memory remains unvalidated. Fix G9 with a regression test and mutation check, then run the six remaining live preflight cases sequentially. Preserve all outcomes and complete cleanup. Update Part A with the results and propose justified host-memory conditions for formal recovery experiments, distinguishing correctness checks from timing claims. Keep Part A provisional and do not run formal experiments, push, or merge yet."
   - (Pasted) "Keep preflight-3 recorded as invalid for timing, while retaining its independently verified correctness observations. Do not relabel the batch as valid. Revise the proposed host conditions: M2 did not establish the 5/4 GiB thresholds as requirements for recovery experiments, and its 35.1 s measurement was also taken under host memory pressure. Do not use these as validated timing standards. The proposed 2.5 GiB threshold also needs justification. Propose a feasible protocol for this 8 GiB Mac: AC power, lid open, sleep prevention, no competing tests, recorded memory pressure and swap changes, and contemporaneous control runs. Distinguish observed recovery times on this host from performance claims. Add power/swap recording with focused tests, and rerun W3 while the machine stays awake. Preserve all earlier records. Keep Part A provisional; do not run formal batches yet."
   - Answer to the AskUserQuestion about the W3 rerun: "Just plugged th ac".
   - Latest: "I approve using this host for correctness observations and recovery times under its recorded conditions, with the limitations stated in Part A. I also approve adding the two bracketing controls, making 30 jobs. Implement the plan option and collector timing-validity checks for battery power or a closed lid. Handle missing power readings explicitly rather than silently passing them. Add focused tests, update Part A and the commands, and commit the tooling changes by explicit path. Then present the final Part A for review. Do not run the formal batch yet."
   - **Security and privacy constraints (from memory, still in effect):** never print memory files, .git/info/exclude or app lists in tool calls (they land in AI logs); stage by explicit path; commit AI logs separately; keep data/ and the private plan out of Git; do not touch the hook (.claude/hooks/transcript_privacy.py) or other out-of-scope files unasked; the author pushes and merges.

7. Pending Tasks:
   - Update `docs/recovery-part-a.md`:
     - Title (30 jobs, DRAFT) and header: record the approvals of 2026-10-24.
     - §1 Workload: 30 jobs, a C0 at each end plus 28 shuffled.
     - §7 commands: the formal plan defaults to 30 jobs; the collector prints verdicts.
     - §8 runtime: 30 jobs, 3,039 s (about 50.7 min) with preflight values; 53.5 / 53.4 min ranges; 51.2 min with the original assumptions.
     - §10: mark the approved rows (host use for correctness and recovery times under recorded conditions; controls / 30 jobs); the workload row becomes 28 shuffled plus 2 controls.
     - §11: add the verdict table for preflights 1–4 (preflight-2's times invalid because power and lid are unknown; preflight-4 the only batch whose recovery times count).
     - §12: tooling implemented (plan option; collector host_power/host_lid with unknown failing; verdicts).
   - Update `docs/recovery-experiments.md` (revision 10; section 9 "Not done": only the formal batch remains).
   - Check line widths, run the doc-reading tests (test_jobs_harness, test_recovery_sql), update the memory note and MEMORY.md pointer (via sed, no printing).
   - Present the final Part A for review (summary plus file path; optionally offer an artifact page in one line).
   - Docs stay uncommitted unless asked; tooling is already committed (5a81bc5).
   - Do not run the formal batch; do not push or merge.

8. Current Work:
   Immediately before the summary I had committed the tooling as **5a81bc5** ("Bracket each plan with controls and check timing validity per batch"). I had computed the verdicts for preflights 1–4 and the 30-job estimates, and was reading the Part A passages to update. The last tool output showed:
   - lines 216–224: the Ranges, Earlier figures, Limits, Controls ("The two control C0s proposed in section 12 add about 2 minutes (30 jobs).") and Status bullets;
   - lines 240–262: the §10 decisions table;
   - lines 438–450: §12's Tooling bullet:
     ```
     - **Tooling.**
       - Implemented: conditions 1, 2 and 5 (power, lid and memory recorded per reading); the clock check.
       - Not implemented: a plan option to put a control C0 at both ends of a shuffled plan (`plan --jobs`
         can list such an order by hand); the collector's flag of a battery or closed-lid reading as a
         timing failure.
     ```
   The worktree has uncommitted `docs/recovery-experiments.md` and `docs/recovery-part-a.md`. No containers or processes are running.

9. Optional Next Step:
   Continue the latest request: "update Part A and the commands ... Then present the final Part A for review. Do not run the formal batch yet."
   - Edit `docs/recovery-part-a.md`:
     - title "30 jobs (DRAFT)" and header with the approvals;
     - §1, §7, §8 (30 jobs, 3,039 s ≈ 50.7 min with preflight values);
     - §10 approved rows;
     - §11 verdict table for preflights 1–4;
     - §12 Tooling now implemented, with missing readings failing as unknown.
   - Update the outline revision 10; verify widths and run the doc-reading tests; update the memory note.
   - Present the final Part A for review: sections, approved versus provisional items, remaining author decisions, and the path `docs/recovery-part-a.md`, noting the docs are uncommitted. Commits so far: d675c85, a94eefe, 8c5331d, 5a81bc5.

If you need specific details from before compaction (like exact code snippets, error messages, or content you generated), read the full transcript at: ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl
Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened.

The messages after this summary are the most recent messages from before compaction, kept verbatim. The summary was written without seeing them, so something it says has not happened yet may already have happened in them.

## 2. Assistant — 2026-10-25T04:00:56.591Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-part-a.md"
}
```

## 3. User — 2026-10-25T04:00:56.862Z

### Tool result

````
1	# Recovery experiments: Part A proposal, 30 jobs (DRAFT)
2	
3	_**Draft; Part A is not approved as a whole.** The author approved two items on 2026-10-24:
4	- using this host for correctness observations and for recovery times under its recorded
5	  conditions, with the limitations of section 12;
6	- a control C0 at each end of the batch, making 30 jobs.
7	
8	No formal batch has run, and the deadlines and memory rules stay provisional. This document
9	condenses [recovery-experiments.md](recovery-experiments.md) for the preferred draft. Every
10	command, event and record in it was checked against the tooling at `5a81bc5`. M2's isolated check has since validated the container limits,
11	under host memory pressure and with documented sampling limits; native-process memory remains
12	unvalidated. Four live preflight batches ran on 2026-10-24 under recorded memory pressure
13	(section 11); preflight-3 is invalid for timing. Their times and memory readings are not performance
14	or budget evidence. Section 12 proposes a protocol for recovery batches on this host. Drafted with
15	Claude Code (Opus 5.5) at the author's request on 2026-10-24; the decisions in section 10 are the
16	author's._
17	
18	## 1. Workload
19	
20	- One batch on fresh MySQL and Kafka containers. The reference run comes first, then 30 jobs:
21	  - a C0 control first;
22	  - 2 of each of the 14 cases (28 jobs, the two shuffled C0s among them), in an order shuffled from
23	    a seed recorded in the plan;
24	  - a C0 control last.
25	
26	  The controls were approved on 2026-10-24 (section 12, condition 6). The harness's default plan
27	  makes this order.
28	- Each job is the calendar-year job on `full-2026-10-12`, with `max_attempts` 3. The plan also
29	  records stride 21, which only rolling windows use. One job runs windows, spark_pipeline and verify
30	  (about 35 s of steps at M2's measurements).
31	- Two workers, A then B, each waited for in the assignment events, and one reconciler.
32	
33	| Case | Injection | Method and phase |
34	|---|---|---|
35	| C0 | none | baseline; measures T |
36	| W1 | SIGKILL of the owner | fault file, `before_claim` |
37	| W2 | SIGKILL of the owner | fault file, `after_claim` |
38	| W3 | SIGKILL of the claiming worker | harness, 3 s into `spark_pipeline` |
39	| W4 | SIGKILL of the owner | fault file, `after_pipeline` |
40	| W5a | SIGKILL of the owner | fault file, `after_accept_commit` |
41	| W5b | SIGKILL of the owner | fault file, `after_accept` |
42	| W6 | SIGSTOP of the worker until the takeover, then SIGCONT and SIGTERM | harness, mid-step |
43	| W7 | SIGSTOP of the whole tree for 90 s, then SIGCONT and SIGTERM | harness, mid-step |
44	| K1 | `docker compose restart kafka` | harness, mid-step |
45	| K2 | Kafka stopped 30 s around the submit | harness, before the submit |
46	| D1 | MySQL stopped 30 s | harness, mid-step |
47	| D2 | MySQL stopped 30 s while the owner holds | fault file `after_pipeline` (hold) |
48	| X1 | the job id published again, at its claim and after its success | harness |
49	
50	## 2. Timing (P2: the defaults of timing.py, no override)
51	
52	| Lease L | Renewal R | Fence margin M | F | Worker tick | Watchdog t_w | Kill grace G |
53	|---|---|---|---|---|---|---|
54	| 60 s | 10 s | 10 s | last renewal + 50 s | 1 s | 0.5 s | 7 s (5 + 2) |
55	
56	| Step limits | Attempt | Session S_k | Heartbeat h | Reconciler P | Publication grace g | Confirmation |
57	|---|---|---|---|---|---|---|
58	| 120 / 600 / 300 s | 900 s | 15 s | 3 s | 5 s | 30 s | 10 s |
59	
60	## 3. Deadlines (P3)
61	
62	D = ceil5(B + 2S): B is the design's latest start of the next run after the deadline's reference,
63	and 2S is 70.2 s (twice M2's slowest step sum, 35.1 s). `max_lag_s` is 1 s and the drain limit is D.
64	
65	| Cases | Reference | B | D |
66	|---|---|---|---|
67	| C0, W5a, W5b, K1, X1 | submit (C0), injection | 0 | 75 s |
68	| W1 | injection | S_k + h + 1 = 19 s | 90 s |
69	| W2, W3, W4, W6 | injection | L + P = 65 s | 140 s |
70	| W7 | injection | max(L + P, 90 + 2 t_w + G) = 98 s | 170 s |
71	| K2 | Kafka's return | g + P + 19 = 54 s | 125 s |
72	| D1, D2 | MySQL's return | L + P = 65 s | 140 s |
73	
74	A missed injection takes C0's deadline from its submit. The preflight's two C0 jobs took 52.4 and
75	46.8 s (median 49.6 s). That is above the 40 s assumed but below 70.2 s, so by P3's own rule D is
76	not re-derived; the margins shrink from 31–35 s to about 20–25 s. Both values come from a host
77	under memory pressure (section 11). S itself (35.1 s) was measured under host memory pressure too,
78	so D rests on observations of this host, not on a validated standard: on time and late classify
79	jobs on this host and nothing more.
80	
81	## 4. Predictions
82	
83	The table assumes T = 40 s and restore times of about 20 s; neither has been measured on this clock.
84	"Finish by" is the latest finish the design predicts, B + T, from the deadline's reference; the
85	margin is D minus it.
86	
87	| Case | Claims / accepted | Detection and window | Finish by | Margin |
88	|---|---|---|---|---|
89	| C0 | 1 / 1 | — | T, 40 s | 35 s |
90	| W1 | 1 / 1 | standby's `delivered`, 12–19 s | 59 s | 31 s |
91	| W2, W4 | 2 / 1 | reconciler's `requeued`, 60–65 s | 105 s | 35 s |
92	| W3, W6 | 2 / 1 | `requeued`, 50–65 s | 105 s | 35 s |
93	| W7 | 2 / 1 | `requeued`, 50–65 s; the replacement waits for the host lock until 98 s | 138 s | 32 s |
94	| W5a | 1 / 1 | — ; Q3a `no matching report`, by design | — | — |
95	| W5b | 1 / 1 | — | — | — |
96	| K1 | 1 / 1 | — (the attempt goes on) | under T | over 35 s |
97	| K2 | 1 / 1 | reconciler's `published`, within P of Kafka's return | 94 s | 31 s |
98	| D1 | 1 / 1 if MySQL is back before F, else 2 / 1 | `renewal_failed`; then `renewed` or `requeued` | 105 s | 35 s |
99	| D2 | 1 / 1 if MySQL is back before F, else 2 / 1 | `retry` of `accept_result`; then `accepted`, or `failed_after_ack` and `requeued` | 105 s | 35 s |
100	| X1 | 1 / 1 | both duplicates refused as `succeeded` | T | 35 s |
101	
102	Expected for E1 on all 28 jobs: Q1 `ok`; `status --check` exits 0; no invariant violation; every
103	accepted result equals the reference run; no overlapping step intervals. Each of these is checked
104	per job and reported as found.
105	
106	**Assumptions and uncertainty.**
107	- T is unmeasured on the default clock. The preflight's C0 jobs measure it; if T exceeds 2S (70.2 s),
108	  re-deriving D is the author's option.
109	- Restore times are unmeasured. From the stop, F comes 40–50 s later; MySQL returns after 30 s plus
110	  its restore. D1's and D2's branches therefore depend on the restore, and both branches are valid
111	  outcomes.
112	- A killed worker's dead group member keeps its session for 15 s, so a restart may take about 20 s
113	  rather than the estimator's 12 s.
114	- During K1 and K2, consumers log `consumer_error` and keep polling, with no back-off; the rejoin
115	  bound of 19 s is assumed to hold.
116	- X1's first duplicate arrives while its owner runs the job, so it is read only afterwards. Both
117	  duplicates are therefore refused as `succeeded` (outline 3.1, corrected on 2026-10-24).
118	- Results are counts per case (k of 2), with no rates.
119	
120	## 5. Injection success and misses (harness)
121	
122	- **Fault-file cases** (W1, W2, W4, W5a, W5b, D2): the owner is read from the assignment events,
123	  and only its fault file is armed (`armed` records `owner_after`).
124	  - Made: that worker's `fault_injected` at the case's point, after this job's `delivered` or
125	    `claimed`. For kills, the worker has also exited within 30 s. `t_inj` is the event's `mono`, or
126	    the MySQL stop for D2.
127	  - Missed: the other worker claims the job first (a miss at once), or no event comes within 300 s.
128	    The file is then removed.
129	- **Mid-step cases** (W3, W6, W7, K1, D1):
130	  - Made: a claim with `step_started` for `spark_pipeline`, no `step_ended` (named `name`) and the
131	    step's log file, and the step still running 3 s later.
132	  - Missed: 300 s without that phase, or the step ended during the 3 s.
133	- **K2**: the stop precedes the submit. A submit that fails is `job_not_submitted` and stops the
134	  batch.
135	- **X1**: made once a claim is seen; the second publication follows the success.
136	- **A missed job is still followed.** Its latencies are `n/a: injection missed`, and it keeps its
137	  row as `missed`.
138	
139	## 6. Stop rules and outcomes
140	
141	- **The batch stops** when one of these happens; the remaining jobs are recorded as `not_run`, with
142	  the reason:
143	  - a job is unfinished at its drain limit (`an unfinished job`);
144	  - a submit fails;
145	  - a container's batch peak passes 95% of its limit (provisional P4; 90% is flagged);
146	  - an error in the harness during a job (`job_error`).
147	
148	  Quiescence (SIGKILL of the writers), the final snapshot and `down -v` still run.
149	- **Late:** running at its deadline and succeeded later. It counts as `late` with `deadline_met` no,
150	  and the later success never changes that.
151	- **Failed:** out of attempts. Q1 `failed`, Q2 `failed`, `deadline_met` no.
152	- **Unknown:** each is reported as unknown, never as met or as no overlap:
153	  - a failed deadline read gives `deadline not observed`, with `deadline_met` unknown;
154	  - a step without both monotonic times makes the overlap `unknown`;
155	  - a missing injection time gives `unknown: no injection time`;
156	  - a missing harness record gives `unrecorded`.
157	- **Validity (6.1):** a batch that fails it does not count, and its records and outcomes stay. E1
158	  and E2 findings never change validity.
159	
160	## 7. Commands (from the repository root of the checkout that ran the plan)
161	
162	```bash
163	# 0. Preconditions: the test window is released; nothing of this project runs
164	docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
165	uv run --group jobs python -m etf_risk.services others         # other projects' containers: a count
166	git status --short                                             # clean: the batch records the commit
167	pmset -g batt | head -1                                        # 'AC Power' (section 12)
168	ioreg -r -k AppleClamshellState -d 4 | grep '"AppleClamshellState"'   # '= No': the lid is open
169	uv run --group jobs python -c "import psutil; print(psutil.virtual_memory().available / 2**30)"   # GiB (section 12)
170	
171	# 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results
172	uv run --group jobs python -m etf_risk.jobs.harness plan --purpose preflight --seed 1 \
173	    --jobs C0,W1,W6,W7,K1,K2,D1,D2,C0 --out data/outputs-recovery/preflight/plan-1.json
174	# Keep the host awake: on AC power with the lid open (section 12); -s works on AC power only
175	caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
176	    --plan data/outputs-recovery/preflight/plan-1.json --out data/outputs-recovery/preflight/<name>
177	uv run --group jobs python analysis/collect_recovery_measurements.py \
178	    --batch data/outputs-recovery/preflight/<name>
179	# The job tests and the live pipeline tests against both services, outputs kept with the preflight
180	docker compose -f docker/compose.yaml up -d --wait mysql kafka
181	uv run --group jobs python -m etf_risk.services ready mysql kafka
182	ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
183	    uv run --group jobs python -m pytest tests/test_jobs_*.py 2>&1 | tee data/outputs-recovery/preflight/job-tests.txt
184	ETF_RISK_LIVE_PIPELINE=1 ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 \
185	    ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 uv run --group jobs python -m pytest tests/test_jobs_live_pipeline.py \
186	    2>&1 | tee data/outputs-recovery/preflight/live-pipeline.txt
187	docker compose -f docker/compose.yaml down -v
188	
189	# 2. Formal batch: only after the author approves Part A; the plan is the preferred draft by default
190	uv run --group jobs python -m etf_risk.jobs.harness plan --purpose formal --seed <SEED> \
191	    --out data/outputs-recovery/formal/plan-<SEED>.json
192	uv run --group jobs python -m etf_risk.jobs.harness estimate --plan data/outputs-recovery/formal/plan-<SEED>.json
193	caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
194	    --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/outputs-recovery/formal/batch-1 --formal
195	
196	# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder; exit 1 on invalidity
197	uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/formal/batch-1
198	
199	# 4. Cleanup: the batch itself ends with `docker compose down -v`; check, and recover if it was killed
200	docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
201	docker compose -f docker/compose.yaml down -v                  # only if something was left
202	```
203	
204	`plan` creates its folder. A batch writes `harness.jsonl` (with the host's memory before each
205	job, the Spark scratch at the start and after quiescence, and any setup or final error) and
206	`plan.json`. It also writes the folders `events/` (A, B, `reconciler-<pid>`, `submit`),
207	`jobs/<store>/<run>/` (with `logs/*.launcher.json`, `attempt.json` and `manifest.json`),
208	`reference/`, `logs/`, `crosscheck/Q0–Q3b.csv` and `export/`, and the files `status-check.txt` and
209	`cleanup.txt`. The batch exits 1 if its setup or final steps failed. The collector reads these,
210	and the snapshot's input files for its input check.
211	
212	## 8. Runtime
213	
214	Revised with the preflight's measurements (section 11), all taken under memory pressure:
215	
216	| Part | Seconds | Basis |
217	|---|---|---|
218	| Containers, `init-db`, topic, reference run, the three processes | 81 | preflight-2's setup (services 14 s, reference run 58 s) |
219	| 30 jobs, the two controls included | 2,939 | the estimator with T 49.6 s, restores 11 s and restarts 5 s |
220	| Quiescence, final snapshot, `down -v` | about 20 | preflight-2 (3 s to `batch_ended`) plus teardown |
221	| **Batch** | **3,039, about 51 min** | the estimator, with 100 s for the fixed parts |
222	| Plan and collection | about 120 | assumed |
223	| **End to end** | **about 53 min** | |
224	
225	- **Ranges.** The batch comes to 53.5 min if T is 55 s. It comes to 53.4 min if restores take
226	  20 s, since D2 then takes its fenced branch, as D1 did in the preflight.
227	- **Earlier figures.** The first estimate, with unmeasured assumptions, was 49.8 min for 28 jobs
228	  (51.2 min for 30). Preflight-2 took 15.1 min against an estimated 17.8.
229	- **Limits.** A job that hangs stops the batch at its drain limit, at most 2D from its reference
230	  (340 s for W7).
231	- **Status.** Planning figures, not performance evidence.
232	
233	## 9. Gaps in the service-only paths: G1–G9, fixed on 2026-10-24
234	
235	G1–G8 were found by reviewing the paths that only a live batch runs, fixed at the author's approval,
236	and checked offline. G9 was found by preflight-1, then fixed (`a94eefe`) and checked live by
237	preflight-3, which ran from a relative folder.
238	
239	| | Gap | Now | Checked by |
240	|---|---|---|---|
241	| G1 | An error during setup was not written to `harness.jsonl`, and `batch_ended` said `stop_reason` null | `setup_error`, every planned job `not_run`, exit code 1; containers removed only if the batch started them; the collector fails `records_complete` | harness tests; mutations |
242	| G2 | Quiescence counted the harness's own store connection as another client, against 4.4 | the harness closes its own connections, then waits up to 15 s for MySQL to list no other client | harness test with a stand-in process list; mutation |
243	| G3 | 6.2 and the records rely on `cleanup`'s listing, which the harness never produced | `cleanup` (dry run) in the final snapshot, saved as `cleanup.txt` | synthetic batch; mutation |
244	| G4 | P4's host memory before each job was not recorded | `host_memory` before each job, in `injections.csv` too; never a gate | synthetic batch; mutation |
245	| G5 | 6.5's "no new Spark scratch" had nothing behind it | the scratch listed at the start and after quiescence; new entries in `quiescent` and the collector's `nothing_left` | harness and synthetic tests; mutations |
246	| G6 | The collector's example path predated the purpose folders | `.../formal/<batch>` and `.../preflight/<name>` | — |
247	| G7 | `plan --out` needed its folder to exist | `plan` creates it | harness test |
248	| G8 | The outline's X1 row predicted `lease held` for the first duplicate | `succeeded`, in the outline and here | — |
249	| G9 | With a relative batch folder, the harness passed relative paths to the reference run's launcher, which runs in `.work`; the step could not start (launcher exit 71, `launch_failed`) | the batch resolves its folder once, so every path handed to a process is absolute | regression test; mutation `batch-folder-relative`; preflight-3 from a relative folder |
250	
251	## 10. Author decisions
252	
253	**Approved by the author on 2026-10-24:**
254	- this host, for correctness observations and for recovery times under its recorded conditions,
255	  with section 12's limitations;
256	- the two controls, one C0 at each end of the batch (30 jobs).
257	
258	**Still open:**
259	
260	| Decision | Recommended |
261	|---|---|
262	| Workload (P1) | 28 shuffled jobs and the two approved controls, 30 in all; the 84 jobs stay the alternative (plus their own controls) |
263	| Clock (P2) | the defaults, confirmed by the preflight |
264	| Deadlines (P3) | as in section 3; the preflight's T (median 49.6 s) is below 70.2 s, so no re-derivation |
265	| Harness waits | 3 s phase delay, 90 s W7 stop, 30 s outages |
266	| Clock-check tolerance | 1 s |
267	| Injection method (P5) | the fault file, as implemented |
268	| Memory (P4) | flag containers at 90% and stop at 95% of the limits M2's check validated (under host pressure); host memory recorded, never gated (section 12) |
269	| Host protocol (section 12) | conditions 1–7, as checked by the collector: AC power, lid open, sleep prevented, no competing tests, memory pressure and swap recorded, controls in the same batch, every outcome kept |
270	| A batch invalid for timing | stays invalid and is never relabelled; its correctness observations are kept, labelled as such (preflight-3) |
271	| A preflight that finds a defect | fix it, then run a new preflight in a new folder; keep both |
272	| Seed | an integer the author fixes in the plan before the batch |
273	
274	## 11. Live preflight, 2026-10-24: functional validation only
275	
276	_Preflight-1 and preflight-2 ran on code `7bd4d20`, preflight-3 on `a94eefe` (the G9 fix), each in an
277	exclusive window that M2 handed over. All ran under recorded memory pressure: 1.2–1.7 GiB of 8 GiB
278	available before each job, with 4–10 GiB of swap in use. The times and memory below show that the
279	paths work; they are not performance or budget evidence. Every record stays under
280	`data/outputs-recovery/preflight/`, apart from formal results._
281	
282	| Run | Outcome |
283	|---|---|
284	| preflight-1: the plan, relative batch folder | **failed in setup**: the reference run's windows step could not start (launcher exit 71, `launch_failed`; G9). Recorded as `setup_error`, all 9 jobs `not_run`; the final snapshot and teardown ran; harness exit 1; validity failed (`records_complete`) |
285	| preflight-2: the same plan, absolute batch folder | 9 of 9 injections made, none missed or unrecorded; all 9 jobs on time; validity passed; harness exit 0; 15.1 min |
286	| job tests against MySQL 8.4 and Kafka | 515 passed, 10 skipped (the live cases, run next), 0 failed, in 2 min 53 s |
287	| live pipeline module | 10 passed, 0 failed, in 10 min 54 s; its overlap check now compares monotonic times |
288	| full offline suite, after the services were removed | 622 passed, 30 skipped (the MySQL, Kafka and live tests, which passed in the two runs above), 0 failed, in 9 min 54 s, Spark tests included |
289	| preflight-3: C0, W2, W3, W4, W5a, W5b, X1, from a relative batch folder | **invalid for timing**: the clock check failed, because the host slept for about 22 min during W3 (below). 7 of 7 injections made, none missed; its correctness observations are kept apart (below); harness exit 0; 11.6 min monotonic, 33.8 min wall |
290	| preflight-4: C0, W3, C0 (the W3 rerun with a control on each side), on AC power with the lid open | 3 of 3 injections made; validity passed, the clock check included; harness exit 0 (below) |
291	
292	Preflight-2 by case. Finish is measured from the deadline's reference; D is from section 3.
293	
294	| Case | Claims | Detection | Finish | D | Observed path |
295	|---|---|---|---|---|---|
296	| C0 | 1 | — | 52.4 s | 75 s | baseline |
297	| W1 | 1 | standby's `delivered`, 13.5 s | 69.8 s | 90 s | killed at `before_claim`; the standby took over |
298	| W6 | 2 | `requeued`, 57.9 s | 103.9 s | 140 s | the worker stopped; takeover; fenced after SIGCONT |
299	| W7 | 2 | `requeued`, 57.5 s | 132.0 s | 170 s | a tree of 4 processes stopped for 90 s; the replacement ran after it |
300	| K1 | 1 | — | 47.6 s | 75 s | Kafka ready 9.3 s after its restart began; the attempt went on |
301	| K2 | 1 | `published`, 3.0 s after Kafka's return | 64.3 s | 125 s | Kafka back 33.9 s after the stop; one claim |
302	| D1 | 2 | `renewal_failed`, 5.9 s after the stop | 54.6 s | 140 s | MySQL back 40.8 s after the stop, after F: fenced, then attempt 2 |
303	| D2 | 1 | `retry` of `accept_result`, 3.9 s after the stop | 0.5 s | 140 s | MySQL back 31.6 s after the stop, before F: accepted |
304	| C0 | 1 | — | 46.8 s | 75 s | baseline |
305	
306	- **E1 and the records:**
307	  - every Q1 verdict `ok`, no overlapping step intervals, `status --check` exit 0 and no invariant
308	    violation;
309	  - all 9 accepted results equal the reference run, with matching digests, and the three
310	    fingerprints are equal;
311	  - Q3a `reported once` and Q3b `matches` throughout;
312	  - quiescence left no process, no other client and no new Spark scratch, and the cleanup listing
313	    is recorded;
314	  - the clock check passed (`ts` minus `mono` −0.018 s over the batch), with 6 of 6 process starts
315	    on one clock and one code identity over 50 records.
316	- **Ownership:** read from the assignment events throughout. A owned the partition first, B from
317	  its join until W6, and A after that. Every arming hit the owner.
318	- **Liveness:** 28 `retry` events (D2's acceptance during the outage) and 15 failed reconciler
319	  passes (during the MySQL outages). There was no `failed_after_ack`, no `consumer_error` and no
320	  serve restart.
321	- **Against the assumptions:**
322	
323	  | Quantity | Assumed | Observed |
324	  |---|---|---|
325	  | T | 40 s | 52.4 and 46.8 s |
326	  | restart and rejoin | 12 s | 3.7–5.2 s |
327	  | restore after start | 20 s | Kafka 3.9 s; MySQL 1.6 and 10.8 s |
328	  | fixed batch parts | 180 s | about 100 s (setup 81 s) |
329	  | reference steps | 25.6 s (M2) | windows 9.1 s, spark_pipeline 48.5 s |
330	
331	- **Memory, informational only:**
332	  - container peaks in preflight-2: MySQL 250 of 512 MiB (49%) and Kafka 386 of 640 MiB (60%);
333	  - after the two test runs: 208 and 372 MiB;
334	  - host memory available before each job: 1.19–1.5 GiB.
335	- **Covered live since:** W2, W3, W4, W5a, W5b and X1, in preflight-3, below.
336	
337	Preflight-3 is **invalid for timing** and stays so. Its detection, rerun and finish times and its
338	deadline outcomes remain in its records, and none of them is reported or counted here. What follows
339	is only its correctness observations, which do not depend on the clock and were checked on their own.
340	
341	| Case | Claims | Accepted | Observed path |
342	|---|---|---|---|
343	| C0 | 1 | 1 | baseline |
344	| W2 | 2 | 1 | killed at `after_claim`; the standby's redelivery refused as `lease_held`; requeued; attempt 2 accepted |
345	| W3 | 3 | 1 | killed 3 s into spark_pipeline; then the host slept (below): early requeues, and attempt 2's renewal refused and fenced; attempt 3 accepted |
346	| W4 | 2 | 1 | killed at `after_pipeline`; two complete executions, one accepted |
347	| W5a | 1 | 1 | killed at `after_accept_commit`: Q3a `no matching report`, as designed |
348	| W5b | 1 | 1 | killed at `after_accept` |
349	| X1 | 1 | 1 | both duplicates refused as `succeeded` (G8's correction, confirmed) |
350	
351	- **Correctness observations:**
352	  - every Q1 verdict `ok`, no overlapping step intervals, `status --check` exit 0 and no invariant
353	    violation;
354	  - all 7 accepted results equal the reference run, and the fingerprints agree;
355	  - quiescence left nothing, and `cleanup.txt` lists the 3 unaccepted attempts' folders;
356	  - code identity, inputs and complete records all passed.
357	
358	  Container peaks were MySQL 317 of 512 MiB (62%) and Kafka 495 of 640 MiB (77%); host memory before
359	  each job was 1.26–1.7 GiB available.
360	- **The host sleep:**
361	  - At 21:53:28 local time, about 18 s after W3's injection, the Mac entered "Clamshell Sleep" on
362	    battery: the lid was closed. `caffeinate -i` prevents idle sleep only.
363	  - It slept until 22:16:04, apart from two maintenance wakes. Wall time minus monotonic time grew
364	    by 63.8 s, 116.9 s and 1,148.2 s (1,328.8 s in all), and the clock check failed the batch, as
365	    designed.
366	  - Leases are wall-clock times in the job table, so they expired while every process was
367	    suspended. The reconciler requeued W3 at its next pass, and again after B's attempt 2; B's
368	    renewal was refused, and the attempt was fenced and its tree ended.
369	  - One attempt was accepted, and nothing overlapped. W3's claim count and times describe the
370	    sleep, not the job system; W4 to X1 ran after the wake.
371	- **Preflight-4: W3 again, with the host awake.** It ran on `8c5331d` (power and swap recording), on
372	  AC power with the lid open, under `caffeinate -dims`, with no other containers or tests running.
373	  It passed validity: the clock check (wall minus monotonic 0.028 s over the batch, 4 of 4 process
374	  starts on one clock), Q1 `ok`, all 3 accepted results equal to the reference, no overlap, nothing
375	  left. The power log shows no sleep.
376	
377	  | Case | Claims | Detection | Finish | D | Before the job | Swapped out during it |
378	  |---|---|---|---|---|---|---|
379	  | C0 | 1 | — | 45.1 s | 75 s | AC, lid open, pressure 2, 1.71 GiB available | 5.0 MiB |
380	  | W3 | 2 | `requeued`, 59.1 s | 117.1 s | 140 s | AC, lid open, pressure 2, 1.74 GiB | 26.5 MiB |
381	  | C0 | 1 | — | 50.9 s | 75 s | AC, lid open, pressure 2, 1.48 GiB | 21.1 MiB |
382	
383	  - **W3's ordinary path:** killed 3 s into spark_pipeline, then requeued 59.1 s after the kill,
384	    inside the predicted 50–65 s. Attempt 2 was accepted, and 6.4 s of step time was wasted.
385	  - **The controls:** the C0 jobs took 45.1 s before W3 and 50.9 s after it; their steps took
386	    42.8 and 48.4 s.
387	  - **Over the batch:** AC power and the lid open throughout. Memory pressure was 2 (warning)
388	    before every job and 1 at the end, with 1.36–1.93 GiB available. Swap in use grew from 4.21 to
389	    5.03 GiB; 4.4 GiB was swapped in and 67 MiB swapped out.
390	
391	  These are recovery times observed on this host in that recorded state, next to controls measured
392	  in the same batch. They are not performance claims (section 12).
393	- **Native processes, informational:** across preflight-2 and -3 the step trees peaked at 0.09–0.12
394	  GiB (windows), 0.62–0.88 GiB (spark_pipeline) and 0.42–0.54 GiB (verify), one step at a time
395	  under the host lock. The C0 jobs' steps took 44.3–50.4 s in preflight-2 and -3 (and 42.8–48.4 s
396	  in preflight-4), against the 35.1 s M2 measured, itself under host memory pressure; T was about
397	  2 s more than the steps.
398	
399	## 12. A protocol for recovery batches on this 8 GiB Mac (proposal)
400	
401	**What is and is not established.**
402	- **M2's isolated check** validated the containers' memory limits (MySQL 512 MiB, Kafka 640 MiB),
403	  under host memory pressure and with documented sampling limits.
404	- **Its 5 GiB and 4.0 GiB figures** were the gates of that check. They were never established as
405	  requirements for recovery experiments.
406	- **Its step times** (35.1 s for the calendar-year job) were also measured under host memory
407	  pressure.
408	- **Native-process memory** (workers, launchers, the Spark driver and JVM, the reconciler, the
409	  harness) is unvalidated.
410	
411	None of these is used here as a validated standard. This draft earlier proposed a 2.5 GiB minimum
412	before each job; nothing measured ties that figure, or any other, to unchanged recovery behaviour on
413	this host, so it is withdrawn. Every live run so far had 1.2–1.9 GiB available, swap in use and
414	memory pressure at warning.
415	
416	**The protocol, for every batch, preflight or formal:**
417	1. **AC power throughout.** Checked before the start with `pmset -g batt`, and recorded in every
418	   host reading. A reading on battery fails the batch for timing.
419	2. **Lid open throughout.** Recorded (`AppleClamshellState`) in every reading. A closed reading fails
420	   the batch for timing.
421	3. **Sleep prevented.** The batch runs under `caffeinate -dims`, whose `-s` holds on AC power only.
422	   The clock check (1 s) detects any sleep that happens anyway and fails validity, as it did for
423	   preflight-3.
424	4. **No competing tests.** The exclusive window; no other containers (counted at the start); no
425	   other pytest, Spark or job processes (checked before the start).
426	5. **Memory pressure and swap recorded, never gated.** Available memory, swap in use, the bytes
427	   swapped in and out, and macOS's pressure level, at the start, before each job and at the end
428	   (`8c5331d`). Each job gets the swap activity of its window, and the batch its totals.
429	6. **Controls in the same batch.** C0 jobs measured in the same batch, under the same recorded host
430	   state: the 28-job plan's two shuffled C0s, plus, as proposed, one C0 at the start and one at the
431	   end (30 jobs, about 2 minutes more). Each case's times are reported next to these controls, for
432	   example its overhead over their median, rather than next to any external figure.
433	7. **Every outcome kept.** A batch that fails conditions 1–3 stays invalid for timing and is never
434	   relabelled.
435	
436	**Three kinds of claim.**
437	
438	| Claim | Made from | Example |
439	|---|---|---|
440	| **Correctness** (E1): one accepted result per job, no overlapping steps, fencing, Q1 and Q3, accepted results equal to the reference, invariants | any batch whose checks that do not involve time pass: code identity, unchanged inputs, equal fingerprints, complete records. From a batch invalid for timing, they are kept as that batch's correctness observations, labelled as such (preflight-3) | "W3 kept one accepted result and no overlap across a 22-min host sleep" |
441	| **Recovery times observed on this host** (E2) | only batches that meet conditions 1–4 and pass validity, clock check included; reported with the batch's host record and its controls | "W3: requeued 59.1 s after the kill, finished in 117.1 s; the controls took 45.1 and 50.9 s; pressure 2, 26.5 MiB swapped out during the job" (preflight-4) |
442	| **Performance claims**: recovery time as a property of the job system, comparable across machines or usable as a prediction | not made from this host | — |
443	
444	- **Why the line falls there.**
445	  - Correctness rests on the job table's token guards, fencing and the host lock, which do not
446	    depend on time or memory: all four preflights kept it, under memory pressure and across a sleep.
447	  - The observed times on this host depend on its memory state. They are taken with swap in use and
448	    pressure at warning, so they say how this machine recovered in that recorded state, and the
449	    controls show how fast it ran a job at the same time.
450	  - A performance claim would need what this host lacks: validated native-process budgets, and a
451	    memory state that does not swap.
452	- **The approved use of this host.** On 2026-10-24 the author approved this host's recorded memory
453	  state for correctness observations and for recovery times observed under its recorded
454	  conditions, with the limitations above. Performance claims stay out of scope.
455	- **Tooling, all implemented:**
456	  - Conditions 1, 2 and 5: power, lid, memory pressure and swap recorded at every reading
457	    (`8c5331d`).
458	  - Condition 6: the harness's default plan puts a C0 control at each end (`5a81bc5`).
459	  - The collector's verdicts (`5a81bc5`):
460	    - correctness observations rest on code identity, unchanged inputs, equal fingerprints and
461	      complete records;
462	    - recovery times also need the clock check and conditions 1 and 2 at every reading the batch
463	      needs (start, each job that ran, end);
464	    - a reading on battery or with the lid closed fails;
465	    - a missing reading, or one without the value, is unknown, and unknown fails.
466	  - `injections.csv` gives each job its power, lid, pressure and swap activity.
467	
````

## 4. Assistant — 2026-10-25T04:02:11.956Z

### Tool call: Bash

```
{
  "command": "git status --short && git log --oneline -6 && echo \"--- harness CLI\" && grep -n \"add_argument\\|bracket_controls\\|def make_plan\\|def estimate\" src/etf_risk/jobs/harness.py | cut -c1-160 && echo \"--- collector main\" && grep -n \"def main\" -A 40 analysis/collect_recovery_measurements.py | grep -n \"print\\|return\\|exit\\|verdict\" | cut -c1-170 && echo \"--- outline header\" && sed -n 1,12p docs/recovery-experiments.md | cut -c1-160",
  "description": "Check status, the plan CLI, collector output and outline header"
}
```

## 5. User — 2026-10-25T04:02:13.064Z

### Tool result

```
 M docs/recovery-experiments.md
 M docs/recovery-part-a.md
5a81bc5 Bracket each plan with controls and check timing validity per batch
8c5331d Record the host's power, lid, memory pressure and swap per job
a94eefe Make the harness's batch folder absolute (G9)
d675c85 Record the first live preflight in the draft Part A proposal
7bd4d20 Fix the harness's service-only gaps and add the draft Part A proposal
772b647 Add the recovery experiments' tooling and outline, tested offline
--- harness CLI
102:    bracket_controls: bool = True        # a C0 control at each end of the shuffled order (30 jobs; approved)
135:    with bracket_controls, a C0 control at each end, measured in the same batch as the cases
139:    return ["C0", *jobs, "C0"] if settings.bracket_controls else jobs
175:def make_plan(settings: Settings, seed: int, *, purpose: str = "formal", jobs: list[str] | None = None) -> dict:
178:    with bracket_controls, puts a C0 control at each end."""
185:    controls = "a C0 at each end" if jobs is None and settings.bracket_controls else None
243:def estimate(plan: dict, a: Assumptions = Assumptions()) -> dict:
1130:    plan.add_argument("--purpose", choices=PURPOSES, required=True,
1132:    plan.add_argument("--seed", type=int, required=True)
1133:    plan.add_argument("--out", type=Path, required=True)
1134:    plan.add_argument("--settings", type=Path, help="JSON replacing any of the default settings")
1135:    plan.add_argument("--jobs", help="cases in this order, comma-separated, instead of the shuffled plan")
1137:    est.add_argument("--plan", type=Path, required=True)
1139:    batch.add_argument("--plan", type=Path, required=True)
1140:    batch.add_argument("--out", type=Path, required=True, help="a new folder inside one named after the purpose")
1141:    batch.add_argument("--formal", action="store_true", help="run a formal plan; only once Part A is approved")
--- collector main
11:571-    print(f"purpose: {result['purpose']}" + (" (a preflight: not a formal result)" if result["purpose"] == "preflight"
14:574-    print(f"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run,"
16:576-    print("validity: " + ("all checks passed" if not result["validity_failed"]
19:579-        check = result["verdicts"][claim]
20:580-        print(f"{label}: " + ("valid" if check["valid"] else "INVALID: " + ", ".join(check["failed"])))
21:581-    print(f"overlap: {result['outcomes']['overlap']['verdict']}; jobs whose Q1 verdict is not ok:"
23:583-    return 1 if result["validity_failed"] else 0
27:587-    sys.exit(main())
--- outline header
# Recovery experiments (E1, E2): outline

Author: _to be written by the author after review. Beyond spec §11, the only decisions by the
author are those in 1.1._

_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised four times from the author's
reviews (history at the end). This is an outline for review, not an approved Part A: everything not
in 1.1 or cited from spec §11 or M2 is Claude Code's proposal, and the decisions in section 8 are
proposals only. Design inputs: commit `6d8a232` (`feature/worker-pipeline`) and M2's final report in
it ([worker-pipeline.md](worker-pipeline.md), "Status on 2026-10-23"); `e4adc38` later corrected
that report's live job-suite count, which this outline does not use. The SQL cross-check, its
fixture, the frozen expected rows and the run that validated the queries are in
```

## 6. Assistant — 2026-10-25T04:02:19.129Z

### Tool call: Bash

```
{
  "command": "grep -n \"^def collect\\|^def main\\|validity_failed\\b\" analysis/collect_recovery_measurements.py | head -8 && ls data/outputs-recovery/preflight/ && for b in preflight-1 preflight-2 preflight-3 preflight-4; do printf '%s: ' $b; grep -c '\"memory_pressure\"' data/outputs-recovery/preflight/$b/harness.jsonl; done",
  "description": "Find the collector entry point and which preflights recorded pressure"
}
```

## 7. User — 2026-10-25T04:02:19.931Z

### Tool result

```
437:def collect(folder: Path, clock_tolerance_s: float = 1.0, processed_root: Path = REPO / "data" / "processed") -> dict:
496:    validity_failed = [name for name, check in validity.items()
517:            "validity": validity, "validity_failed": validity_failed, "verdicts": verdicts, "outcomes": outcomes,
556:        {k: result[k] for k in ("purpose", "validity", "validity_failed", "verdicts", "outcomes", "c0_median_s")},
561:def main(argv: list[str] | None = None) -> int:
576:    print("validity: " + ("all checks passed" if not result["validity_failed"]
577:                          else "FAILED: " + ", ".join(result["validity_failed"])))
583:    return 1 if result["validity_failed"] else 0
full-offline-suite.txt
job-tests.txt
live-pipeline.txt
plan-1.json
plan-3.json
plan-4.json
preflight-1
preflight-1.console.log
preflight-2
preflight-2.console.log
preflight-3
preflight-3.console.log
preflight-4
preflight-4.console.log
preflight-1: 0
preflight-2: 0
preflight-3: 0
preflight-4: 5
```

## 8. Assistant — 2026-10-25T04:02:29.160Z

### Tool call: Bash

```
{
  "command": "for b in 1 2 3 4; do printf 'preflight-%s swap fields: ' $b; grep -c 'swap' data/outputs-recovery/preflight/preflight-$b/harness.jsonl; done; cat > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/verdicts.py <<'EOF'\nimport sys\nfrom pathlib import Path\nsys.path.insert(0, \"analysis\")\nimport collect_recovery_measurements as c\n\nroot = Path(\"data/outputs-recovery/preflight\")\ndef stamps():\n    return {p: p.stat().st_mtime_ns for p in root.rglob(\"*\") if p.is_file()}\nbefore = stamps()\nfor name in (\"preflight-1\", \"preflight-2\", \"preflight-3\", \"preflight-4\"):\n    r = c.collect(root / name)\n    v = r[\"verdicts\"]\n    hosts = {k: {f: r[\"validity\"][k][f] for f in (\"failed\", \"unknown\")} for k in (\"host_power\", \"host_lid\")}\n    print(name, \"| correctness:\", v[\"correctness\"], \"| timing:\", v[\"timing\"])\n    print(\"   validity_failed:\", r[\"validity_failed\"], \"| host:\", hosts)\nafter = stamps()\nprint(\"files:\", len(before), \"unchanged:\", before == after)\nEOF\nuv run --group jobs python /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/verdicts.py 2>&1 | tail -12",
  "description": "Recompute the four preflights' verdicts in memory, checking no file changes"
}
```

## 9. User — 2026-10-25T04:02:41.285Z

### Tool result

```
preflight-1 swap fields: 0
preflight-2 swap fields: 0
preflight-3 swap fields: 0
preflight-4 swap fields: 5
preflight-1 | correctness: {'valid': False, 'failed': ['records_complete']} | timing: {'valid': False, 'failed': ['records_complete', 'host_power', 'host_lid']}
   validity_failed: ['host_power', 'host_lid', 'records_complete'] | host: {'host_power': {'failed': [], 'unknown': ['start', 'end']}, 'host_lid': {'failed': [], 'unknown': ['start', 'end']}}
preflight-2 | correctness: {'valid': True, 'failed': []} | timing: {'valid': False, 'failed': ['host_power', 'host_lid']}
   validity_failed: ['host_power', 'host_lid'] | host: {'host_power': {'failed': [], 'unknown': ['start', 1, 2, 3, 4, 5, 6, 7, 8, 9, 'end']}, 'host_lid': {'failed': [], 'unknown': ['start', 1, 2, 3, 4, 5, 6, 7, 8, 9, 'end']}}
preflight-3 | correctness: {'valid': True, 'failed': []} | timing: {'valid': False, 'failed': ['clock', 'host_power', 'host_lid']}
   validity_failed: ['clock', 'host_power', 'host_lid'] | host: {'host_power': {'failed': [], 'unknown': ['start', 1, 2, 3, 4, 5, 6, 7, 'end']}, 'host_lid': {'failed': [], 'unknown': ['start', 1, 2, 3, 4, 5, 6, 7, 'end']}}
preflight-4 | correctness: {'valid': True, 'failed': []} | timing: {'valid': True, 'failed': []}
   validity_failed: [] | host: {'host_power': {'failed': [], 'unknown': []}, 'host_lid': {'failed': [], 'unknown': []}}
files: 1109 unchanged: True
```

## 10. Assistant — 2026-10-25T04:02:50.438Z

### Tool call: Bash

```
{
  "command": "grep -il \"swap\" data/outputs-recovery/preflight/*.log data/outputs-recovery/preflight/*.txt 2>/dev/null; grep -o 'vm.swapusage[^\"]\\{0,160\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | head -8; grep -o 'total = [0-9.]*M  used = [0-9.]*M' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | sort -u | head -12",
  "description": "Trace where the earlier swap figures came from"
}
```

## 11. User — 2026-10-25T04:02:51.764Z

### Tool result

```
vm.swapusage[^\
vm.swapusage[^\
```

## 12. Assistant — 2026-10-25T04:02:54.862Z

Finishing the Part A update. I'm re-checking the per-preflight figures against the batch records before presenting it.

## 13. Assistant — 2026-10-25T04:02:57.792Z

### Tool call: Bash

```
{
  "command": "grep -o '[^\"]\\{0,120\\}GiB of swap[^\"]\\{0,80\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | head -5 | cut -c1-240; echo ---; grep -o 'swap[^\"]\\{0,40\\}used[^\"]\\{0,60\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | sort -u | head -10 | cut -c1-160",
  "description": "Search the session transcript for the swap readings' source"
}
```

## 14. User — 2026-10-25T04:03:45.636Z

### Tool result

```
er, on code `7bd4d20`, under recorded memory\npressure: 1.2–1.5 GiB of 8 GiB available before each job, with about 10 GiB of swap in use. M2's\nisolated memory check could not run for the same reason, so the c
er, on code `7bd4d20`, under recorded memory\npressure: 1.2–1.5 GiB of 8 GiB available before each job, with about 10 GiB of swap in use. M2's\nisolated memory check could not run for the same reason, so the c
+pressure: 1.2–1.5 GiB of 8 GiB available before each job, with about 10 GiB of swap in use. M2's
er, on code `7bd4d20`, under recorded memory\npressure: 1.2–1.5 GiB of 8 GiB available before each job, with about 10 GiB of swap in use. M2's\nisolated memory check could not run for the same reason, so the c
are in data/outputs-recovery/preflight/ (gitignored).\n\n**Why:** host available memory was about 1.2 GiB with about 10 GiB of swap. M2's isolated memory check could not run, so container budgets are unvalidated
---
swap recorded, never used as a gate;\n  6. control runs in the same batch: I propose 
swap recording with focused tests, and rerun W3 while the machine stays awake. Preserve
swap used 10.56 GiB\nhost-lock registry entries: 0
swap used 3.90 GiB\ncontainers: 0 | pytest/jobs/java: 0/0/0 | other c
swap used 4.14 GiB\ncontainers: 0 | other containers: 0 | pytest/jobs
swap used 4.27 GiB\ndocker VM memory 4109803520 bytes\nregistry entri
swap used 9.82 GiB
swap used {psutil.swap_memory().used/2**30:.2f} GiB')\
swap used {s.used/2**30:.2f} GiB')\
swap used {s['swap_used_bytes']/2**30:.2f} GiB\\\
```

## 15. Assistant — 2026-10-25T04:03:53.317Z

### Tool call: Bash

```
{
  "command": "grep -n \"class Assumptions\" -A 16 src/etf_risk/jobs/harness.py | cut -c1-150",
  "description": "Read the estimator's assumptions"
}
```

## 16. User — 2026-10-25T04:03:53.999Z

### Tool result

```
197:class Assumptions:
198-    """What estimate() assumes. None of it is measured: T for the job system, the restore time
199-    and the restart overhead are guesses to be replaced by the first batch's records."""
200-    time_to_finish_s: float = 40.0       # T: M2's slowest steps (35.1 s) plus 5 s of the worker's own work
201-    restart_s: float = 12.0              # a killed worker's start, sweep and rebalance
202-    restore_s: float = 20.0              # a service's start until it is ready again
203-    peaks_s: float = 2.0                 # the peaks read after every job
204-    group_settle_s: float = 18.0         # after a Kafka restart, until the group has an owner (S + h)
205-    batch_fixed_s: float = 180.0         # containers, reference run, workers, final snapshot, teardown
206-
207-
208-def case_seconds(case: str, timing: Timing, settings: Settings, a: Assumptions) -> float:
209-    """One job's expected duration from the harness's view: from its start to the next job's."""
210-    t, lease, period = a.time_to_finish_s, timing.lease, RECONCILE_INTERVAL.total_seconds()
211-    partial = 1.0 + 3.0 + settings.phase_delay_s         # delivery, windows (M2: up to 3.0 s), the delay
212-    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0
213-    down = settings.outage_s + a.restore_s
```

## 17. Assistant — 2026-10-25T04:04:00.033Z

### Tool call: Bash

```
{
  "command": "uv run --group jobs python - <<'EOF' 2>&1 | tail -8\nfrom etf_risk.jobs.harness import Assumptions, Settings, estimate, make_plan\nplan = make_plan(Settings(), 1)\nprint(len(plan[\"jobs\"]) if \"jobs\" in plan else plan.keys(), plan.get(\"controls\"))\ndef mins(**kw):\n    e = estimate(plan, Assumptions(**kw))\n    return e\nbase = dict(time_to_finish_s=49.6, restore_s=11.0, restart_s=5.0, batch_fixed_s=100.0)\nfor label, kw in [(\"preflight values\", base),\n                  (\"T 55 s\", {**base, \"time_to_finish_s\": 55.0}),\n                  (\"restores 20 s\", {**base, \"restore_s\": 20.0}),\n                  (\"original assumptions\", {})]:\n    e = mins(**kw)\n    print(label, {k: v for k, v in e.items() if not isinstance(v, (list, dict))})\nEOF",
  "description": "Recompute the 30-job runtime estimates offline"
}
```

## 18. User — 2026-10-25T04:04:02.016Z

### Tool result

```
30 a C0 at each end
preflight values {'jobs': 30, 'batch_s': 3039.2}
T 55 s {'jobs': 30, 'batch_s': 3212.0}
restores 20 s {'jobs': 30, 'batch_s': 3204.4}
original assumptions {'jobs': 30, 'batch_s': 3070.0}
```

## 19. Assistant — 2026-10-25T04:04:47.117Z

### Tool call: Bash

```
{
  "command": "sed -n 470,500p analysis/collect_recovery_measurements.py | cut -c1-170; echo \"--- pgrep test\"; pgrep -lf 'pytest|etf_risk\\.jobs|org\\.apache\\.spark'; echo \"exit $?\"",
  "description": "Read the validity checks and test a competing-process check"
}
```

## 20. User — 2026-10-25T04:04:47.902Z

### Tool result

```
        row.update(job_id=job_id, status=status, missed=inj.get("missed"),
                   injection=inj.get("kind"), worker=inj.get("worker"), t_inj=inj.get("t_inj"),
                   reference=d["reference"], deadline_s=d["deadline_s"])
        row.update(job_metrics(b, position, case, inj, d, c0_median))
        row.update(claims=(q1.get(job_id) or {}).get("n_claims"), accepted=(q1.get(job_id) or {}).get("n_accepted"),
                   q1_verdict=(q1.get(job_id) or {}).get("verdict"), timeliness=(q2.get(job_id) or {}).get("timeliness"),
                   deadline_met=(q2.get(job_id) or {}).get("deadline_met"),
                   q3a_verdict=(q3a.get(job_id) or {}).get("log_verdict"))
        rows.append(row)
    intervals, missing = step_intervals(b)
    final = (named(b.harness, "final_snapshot") or [{}])[-1]
    quiescent = (named(b.harness, "quiescent") or [{}])[-1]
    validity = {
        "injections": {"planned": len(rows), "made": sum(r.get("status") == "made" for r in rows),
                       "missed": [r["position"] for r in rows if r.get("status") == "missed"],
                       "not_run": [r["position"] for r in rows if r.get("status") in NOT_RUN],
                       "unrecorded": [r["position"] for r in rows if r.get("status") in UNRECORDED]},
        "code_identity": identity_check(b),
        "clock": clock_check(b, clock_tolerance_s),
        "fingerprints_agree": {"passed": bool(final.get("fingerprints_agree")), "values": final.get("fingerprints")},
        "inputs_unchanged": input_check(b, processed_root),
        **host_conditions(b, host, [r["position"] for r in rows if r.get("job_id") is not None]),
        "records_complete": {"passed": not named(b.harness, "setup_error") and not named(b.harness, "final_error"),
                             "setup_errors": [e.get("error") for e in named(b.harness, "setup_error")],
                             "final_errors": [e.get("error") for e in named(b.harness, "final_error")]},
    }
    validity_failed = [name for name, check in validity.items()
                       if isinstance(check, dict) and check.get("passed") is False]
    verdicts = {"correctness": verdict(validity, CORRECTNESS_CHECKS), "timing": verdict(validity, TIMING_CHECKS)}
    outcomes = {
        "q1_not_ok": [r["job_id"] for r in rows if r.get("q1_verdict") not in (None, "ok")],
--- pgrep test
exit 1
```

## 21. Assistant — 2026-10-25T04:04:54.644Z

### Tool call: Bash

```
{
  "command": "grep -n '\"passed\"' analysis/collect_recovery_measurements.py | cut -c1-170",
  "description": "List every place a check sets its passed value"
}
```

## 22. User — 2026-10-25T04:04:55.347Z

### Tool result

```
283:    return {"passed": len(pairs) == 1 and None not in pairs, "distinct": len(pairs), "records": len(seen)}
289:        return {"passed": False, "why": "no batch_started or batch_ended event"}
293:    return {"passed": abs(difference) <= tolerance_s and all(same), "ts_minus_mono_s": difference,
358:        return {"passed": False, "why": f"{type(error).__name__}: {error}"}
360:    return {"passed": not differ, "jobs_differing": differ}
401:        return {"passed": not failed and not unknown, "failed": failed, "unknown": unknown}
409:    failed = [name for name in checks if validity[name].get("passed") is not True]
489:        "fingerprints_agree": {"passed": bool(final.get("fingerprints_agree")), "values": final.get("fingerprints")},
492:        "records_complete": {"passed": not named(b.harness, "setup_error") and not named(b.harness, "final_error"),
497:                       if isinstance(check, dict) and check.get("passed") is False]
```

## 23. Assistant — 2026-10-25T04:05:49.487Z

Verdicts and runtime figures check out against the records. Now applying the remaining Part A edits.

## 24. Assistant — 2026-10-25T04:06:20.076Z

### Tool call: Bash

````
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nreps = [\n# header\n(\"\"\"_**Draft; Part A is not approved as a whole.** The author approved two items on 2026-10-24:\n- using this host for correctness observations and for recovery times under its recorded\n  conditions, with the limitations of section 12;\n- a control C0 at each end of the batch, making 30 jobs.\n\nNo formal batch has run, and the deadlines and memory rules stay provisional. This document\ncondenses [recovery-experiments.md](recovery-experiments.md) for the preferred draft. Every\ncommand, event and record in it was checked against the tooling at `5a81bc5`. M2's isolated check has since validated the container limits,\nunder host memory pressure and with documented sampling limits; native-process memory remains\nunvalidated. Four live preflight batches ran on 2026-10-24 under recorded memory pressure\n(section 11); preflight-3 is invalid for timing. Their times and memory readings are not performance\nor budget evidence. Section 12 proposes a protocol for recovery batches on this host. Drafted with\nClaude Code (Opus 5.5) at the author's request on 2026-10-24; the decisions in section 10 are the\nauthor's._\"\"\",\n\"\"\"> **Draft; Part A is not approved as a whole.** No formal batch has run. The author approved two\n> items on 2026-10-24:\n> - this host, for correctness observations and for recovery times under its recorded conditions,\n>   with the limitations of section 12;\n> - a control C0 at each end of the batch, making 30 jobs.\n>\n> Everything else, the deadlines and memory rules included, stays provisional.\n\n_This document condenses [recovery-experiments.md](recovery-experiments.md) for the preferred\ndraft. Every command, event and record in it was checked against the tooling at `5a81bc5`. M2's\nisolated check has since validated the container limits, under host memory pressure and with\ndocumented sampling limits; native-process memory remains unvalidated. Four live preflight batches\nran on 2026-10-24 under memory pressure (section 11). Under the collector's current checks, only\npreflight-4 is valid for recovery times, and preflight-3 stays invalid for timing. None of their\ntimes or memory readings is performance or budget evidence. Section 12 proposes a protocol for\nrecovery batches on this host. Drafted with Claude Code (Opus 5.5) at the author's request on\n2026-10-24; the decisions in section 10 are the author's._\"\"\"),\n# section 3\n(\"\"\"A missed injection takes C0's deadline from its submit. The preflight's two C0 jobs took 52.4 and\n46.8 s (median 49.6 s). That is above the 40 s assumed but below 70.2 s, so by P3's own rule D is\nnot re-derived; the margins shrink from 31–35 s to about 20–25 s. Both values come from a host\nunder memory pressure (section 11). S itself (35.1 s) was measured under host memory pressure too,\nso D rests on observations of this host, not on a validated standard: on time and late classify\njobs on this host and nothing more.\"\"\",\n\"\"\"A missed injection takes C0's deadline from its submit. Preflight-2's two C0 jobs took 52.4 and\n46.8 s (median 49.6 s), and preflight-4's controls 45.1 and 50.9 s. All four are above the 40 s\nassumed but below 70.2 s, so by P3's own rule D is not re-derived; at the median of 49.6 s the\nmargins shrink from 31–35 s to about 20–25 s. All four come from a host under memory pressure\n(section 11), and preflight-2's are planning figures only, since its power and lid were not\nrecorded. S itself (35.1 s) was measured under host memory pressure too, so D rests on observations\nof this host, not on a validated standard: on time and late classify jobs on this host and nothing\nmore.\"\"\"),\n# section 4\n(\"Expected for E1 on all 28 jobs:\", \"Expected for E1 on all 30 jobs:\"),\n(\"- Results are counts per case (k of 2), with no rates.\",\n \"- Results are counts per case (k of 2; k of 4 for C0, the two controls included), with no rates.\"),\n# section 7\n(\"\"\"uv run --group jobs python -m etf_risk.services others         # other projects' containers: a count\n\"\"\",\n\"\"\"uv run --group jobs python -m etf_risk.services others         # other projects' containers: a count\npgrep -lf 'pytest|etf_risk\\\\.jobs|org\\\\.apache\\\\.spark'            # must print nothing: no competing tests (section 12)\n\"\"\"),\n(\"\"\"# 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results\n\"\"\",\n\"\"\"# 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results.\n#    --jobs keeps the order as listed and adds no controls; this list has a C0 at each end\n\"\"\"),\n(\"\"\"# 2. Formal batch: only after the author approves Part A; the plan is the preferred draft by default\n\"\"\",\n\"\"\"# 2. Formal batch: only after the author approves Part A. The default plan is the preferred draft:\n#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json)\n\"\"\"),\n(\"\"\"# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder; exit 1 on invalidity\n\"\"\",\n\"\"\"# 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two\n#    verdicts, correctness observations and recovery times, and exits 1 if any check fails, even\n#    one that invalidates only the recovery times (a battery reading, a closed lid, an unknown one)\n\"\"\"),\n(\"\"\"`plan` creates its folder. A batch writes `harness.jsonl` (with the host's memory before each\njob, the Spark scratch at the start and after quiescence, and any setup or final error) and\n`plan.json`. It also writes the folders `events/` (A, B, `reconciler-<pid>`, `submit`),\n`jobs/<store>/<run>/` (with `logs/*.launcher.json`, `attempt.json` and `manifest.json`),\n`reference/`, `logs/`, `crosscheck/Q0–Q3b.csv` and `export/`, and the files `status-check.txt` and\n`cleanup.txt`. The batch exits 1 if its setup or final steps failed. The collector reads these,\nand the snapshot's input files for its input check.\"\"\",\n\"\"\"`plan` creates its folder. A batch writes `harness.jsonl` and `plan.json`. The log holds the\nhost's state at the start, before each job and at the end (memory, swap, pressure level, power and\nlid), the Spark scratch at the start and after quiescence, and any setup or final error. The batch\nalso writes the folders `events/` (A, B, `reconciler-<pid>`, `submit`), `jobs/<store>/<run>/` (with\n`logs/*.launcher.json`, `attempt.json` and `manifest.json`), `reference/`, `logs/`,\n`crosscheck/Q0–Q3b.csv` and `export/`, and the files `status-check.txt` and `cleanup.txt`. It exits\n1 if its setup or final steps failed. The collector reads these, and the snapshot's input files for\nits input check; its `validity.json` holds each check and the two verdicts.\"\"\"),\n# section 10\n(\"\"\"| Host protocol (section 12) | conditions 1–7, as checked by the collector: AC power, lid open, sleep prevented, no competing tests, memory pressure and swap recorded, controls in the same batch, every outcome kept |\"\"\",\n\"\"\"| Host protocol (section 12) | conditions 1–7: AC power, lid open, sleep prevented, no competing tests, memory pressure and swap recorded, controls in the same batch, every outcome kept. The collector checks 1–3 (3 through the clock check); 4 is checked before the start |\"\"\"),\n# section 11\n(\"\"\"_Preflight-1 and preflight-2 ran on code `7bd4d20`, preflight-3 on `a94eefe` (the G9 fix), each in an\nexclusive window that M2 handed over. All ran under recorded memory pressure: 1.2–1.7 GiB of 8 GiB\navailable before each job, with 4–10 GiB of swap in use. The times and memory below show that the\npaths work; they are not performance or budget evidence. Every record stays under\n`data/outputs-recovery/preflight/`, apart from formal results._\"\"\",\n\"\"\"_Preflight-1 and preflight-2 ran on code `7bd4d20`, preflight-3 on `a94eefe` (the G9 fix) and\npreflight-4 on `8c5331d`, each in an exclusive window that M2 handed over. All ran under memory\npressure: 1.2–1.7 GiB of 8 GiB available before each job, as recorded, and 4–10 GiB of swap in use\nat the checks before each batch; swap and macOS's pressure level entered the batch records with\npreflight-4. The times and memory below show that the paths work; they are not performance or\nbudget evidence. Every record stays under `data/outputs-recovery/preflight/`, apart from formal\nresults._\"\"\"),\n(\"\"\"all 9 jobs on time; validity passed; harness exit 0; 15.1 min |\"\"\",\n \"\"\"all 9 jobs on time; validity passed under the collector of the time (`7bd4d20`); harness exit 0; 15.1 min |\"\"\"),\n(\"\"\"Preflight-2 by case. Finish is measured from the deadline's reference; D is from section 3.\"\"\",\n\"\"\"**Verdicts under the collector at `5a81bc5`.** Recomputed on 2026-10-24 without writing anything:\nthe 1,109 files under `data/outputs-recovery/preflight/` kept their modification times.\n\n| Batch | Correctness observations | Recovery times | Failed or unknown |\n|---|---|---|---|\n| preflight-1 | invalid | invalid | `records_complete` (the setup error); power and lid unknown at the start and end readings |\n| preflight-2 | valid | invalid | power and lid unknown at all 11 readings: the batch predates their recording |\n| preflight-3 | valid | invalid | the clock check (the host sleep); power and lid unknown at all 9 readings |\n| preflight-4 | valid | valid | — |\n\nPreflight-4 is the only batch whose recovery times count under section 12, and as a preflight it\nstays apart from formal results.\n\nPreflight-2 by case, functional observations only (verdicts above). Finish is measured from the\ndeadline's reference; D is from section 3.\"\"\"),\n# section 12\n(\"\"\"this host, so it is withdrawn. Every live run so far had 1.2–1.9 GiB available, swap in use and\nmemory pressure at warning.\"\"\",\n\"\"\"this host, so it is withdrawn. Every live run so far had 1.2–1.9 GiB available and swap in use;\npreflight-4, the first batch to record macOS's pressure level, had it at warning before every job.\"\"\"),\n(\"\"\"   host reading. A reading on battery fails the batch for timing.\"\"\",\n \"\"\"   host reading. A reading on battery, or a missing one, fails the batch for timing.\"\"\"),\n(\"\"\"2. **Lid open throughout.** Recorded (`AppleClamshellState`) in every reading. A closed reading fails\n   the batch for timing.\"\"\",\n\"\"\"2. **Lid open throughout.** Checked before the start with `ioreg`, and recorded\n   (`AppleClamshellState`) in every reading. A closed reading, or a missing one, fails the batch for\n   timing.\"\"\"),\n(\"\"\"   other pytest, Spark or job processes (checked before the start).\"\"\",\n \"\"\"   other pytest, Spark or job processes (`pgrep` before the start, section 7).\"\"\"),\n(\"\"\"   state: the 28-job plan's two shuffled C0s, plus, as proposed, one C0 at the start and one at the\n   end (30 jobs, about 2 minutes more). Each case's times are reported next to these controls, for\"\"\",\n\"\"\"   state: the two shuffled C0s, plus one C0 at the start and one at the end (approved on 2026-10-24;\n   30 jobs, about 2 minutes more). Each case's times are reported next to these controls, for\"\"\"),\n(\"\"\"7. **Every outcome kept.** A batch that fails conditions 1–3 stays invalid for timing and is never\n   relabelled.\"\"\",\n\"\"\"7. **Every outcome kept.** A batch that fails conditions 1–3, or lacks the readings to show them,\n   stays invalid for timing and is never relabelled.\"\"\"),\n(\"\"\"only batches that meet conditions 1–4 and pass validity, clock check included; reported with\"\"\",\n \"\"\"only batches that meet conditions 1–4 and whose recovery-times verdict is valid (the clock check, power and lid included); reported with\"\"\"),\n(\"\"\"    depend on time or memory: all four preflights kept it, under memory pressure and across a sleep.\"\"\",\n\"\"\"    depend on time or memory: every job that ran kept it (preflights 2–4), under memory pressure and\n    across a sleep.\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"applied\", len(reps))\nEOF\ngrep -n \"28\" docs/recovery-part-a.md | grep -v \"^2[0-9][0-9]:\\|0\\.28\\|1,328\\|28 \\`retry\\`\" | cut -c1-150; echo \"--- prose lines over 100 chars (tables and code excluded)\"; awk 'BEGIN{code=0} /^```/{code=!code; next} !code && !/^\\|/ && length($0)>100 {print FILENAME\":\"NR\": \"length($0)}' docs/recovery-part-a.md",
  "description": "Apply the remaining Part A edits and check widths and stale counts"
}
````

## 25. User — 2026-10-25T04:06:21.048Z

### Tool result

```
applied 21
25:  - 2 of each of the 14 cases (28 jobs, the two shuffled C0s among them), in an order shuffled from
197:#    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json)
388:  - At 21:53:28 local time, about 18 s after W3's injection, the Mac entered "Clamshell Sleep" on
400:  It passed validity: the clock check (wall minus monotonic 0.028 s over the batch, 4 of 4 process
--- prose lines over 100 chars (tables and code excluded)
docs/recovery-part-a.md:112: 101
docs/recovery-part-a.md:114: 101
docs/recovery-part-a.md:219: 101
docs/recovery-part-a.md:246: 102
docs/recovery-part-a.md:289: 102
docs/recovery-part-a.md:366: 101
docs/recovery-part-a.md:420: 101
docs/recovery-part-a.md:422: 101
docs/recovery-part-a.md:474: 102
```

## 26. Assistant — 2026-10-25T04:06:29.271Z

### Tool call: Bash

````
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\nfor name in (\"docs/recovery-part-a.md\",):\n    code = False\n    for n, line in enumerate(Path(name).read_text().splitlines(), 1):\n        if line.startswith(\"```\"):\n            code = not code\n            continue\n        if not code and not line.startswith(\"|\") and len(line) > 100:\n            print(f\"{name}:{n}: {len(line)}: {line[:60]}...\")\n    print(\"checked\", name)\nEOF\ngit diff --stat",
  "description": "Count prose line widths in characters, not bytes"
}
````

## 27. User — 2026-10-25T04:06:30.159Z

### Tool result

```
docs/recovery-part-a.md:112: 101: - T is unmeasured on the default clock. The preflight's C0 j...
docs/recovery-part-a.md:366: 101: is only its correctness observations, which do not depend on...
checked docs/recovery-part-a.md
 docs/recovery-experiments.md |  41 +++++-
 docs/recovery-part-a.md      | 299 ++++++++++++++++++++++++++++++++++---------
 2 files changed, 276 insertions(+), 64 deletions(-)
```

## 28. Assistant — 2026-10-25T04:06:43.727Z

### Tool call: Bash

```
{
  "command": "sed -n 86,92p docs/recovery-part-a.md && echo ... && sed -n 109,122p docs/recovery-part-a.md",
  "description": "Show section 4's assumption passages"
}
```

## 29. User — 2026-10-25T04:06:44.365Z

### Tool result

```
## 4. Predictions

The table assumes T = 40 s and restore times of about 20 s; neither has been measured on this clock.
"Finish by" is the latest finish the design predicts, B + T, from the deadline's reference; the
margin is D minus it.

| Case | Claims / accepted | Detection and window | Finish by | Margin |
...
per job and reported as found.

**Assumptions and uncertainty.**
- T is unmeasured on the default clock. The preflight's C0 jobs measure it; if T exceeds 2S (70.2 s),
  re-deriving D is the author's option.
- Restore times are unmeasured. From the stop, F comes 40–50 s later; MySQL returns after 30 s plus
  its restore. D1's and D2's branches therefore depend on the restore, and both branches are valid
  outcomes.
- A killed worker's dead group member keeps its session for 15 s, so a restart may take about 20 s
  rather than the estimator's 12 s.
- During K1 and K2, consumers log `consumer_error` and keep polling, with no back-off; the rejoin
  bound of 19 s is assumed to hold.
- X1's first duplicate arrives while its owner runs the job, so it is read only afterwards. Both
  duplicates are therefore refused as `succeeded` (outline 3.1, corrected on 2026-10-24).
```

## 30. Assistant — 2026-10-25T04:06:58.826Z

### Tool call: Bash

````
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nreps = [\n(\"\"\"The table assumes T = 40 s and restore times of about 20 s; neither has been measured on this clock.\n\"Finish by\" is\"\"\",\n\"\"\"The table keeps the drafted assumptions, T = 40 s and restore times of about 20 s; section 11\ncompares them with what the preflights observed. \"Finish by\" is\"\"\"),\n(\"\"\"- T is unmeasured on the default clock. The preflight's C0 jobs measure it; if T exceeds 2S (70.2 s),\n  re-deriving D is the author's option.\n- Restore times are unmeasured. From the stop,\"\"\",\n\"\"\"- T was unmeasured when the table was drafted. The preflights' C0 jobs took 45.1–52.4 s\n  (section 3), below 2S (70.2 s); if T exceeds 2S, re-deriving D is the author's option.\n- Restore times were unmeasured too; preflight-2 observed Kafka 3.9 s and MySQL 1.6 and 10.8 s\n  (section 11). From the stop,\"\"\"),\n(\"\"\"  rather than the estimator's 12 s.\"\"\",\n \"\"\"  rather than the estimator's 12 s (preflight-2 observed 3.7–5.2 s).\"\"\"),\n(\"\"\"deadline outcomes remain in its records, and none of them is reported or counted here. What follows\nis only its correctness observations, which do not depend on the clock and were checked on their own.\"\"\",\n\"\"\"deadline outcomes remain in its records, and none of them is reported or counted here. What\nfollows is only its correctness observations, which do not depend on the clock and were checked on\ntheir own.\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\ncode = False\nfor n, line in enumerate(s.splitlines(), 1):\n    if line.startswith(\"```\"):\n        code = not code\n        continue\n    if not code and not line.startswith(\"|\") and len(line) > 100:\n        print(f\"over 100: line {n}: {len(line)}\")\nprint(\"applied\", len(reps))\nEOF\nsed -n 109,122p docs/recovery-part-a.md",
  "description": "Bring section 4's assumptions in line with the observations"
}
````

## 31. User — 2026-10-25T04:06:59.699Z

### Tool result

```
over 100: line 89: 144
applied 4
per job and reported as found.

**Assumptions and uncertainty.**
- T was unmeasured when the table was drafted. The preflights' C0 jobs took 45.1–52.4 s
  (section 3), below 2S (70.2 s); if T exceeds 2S, re-deriving D is the author's option.
- Restore times were unmeasured too; preflight-2 observed Kafka 3.9 s and MySQL 1.6 and 10.8 s
  (section 11). From the stop, F comes 40–50 s later; MySQL returns after 30 s plus
  its restore. D1's and D2's branches therefore depend on the restore, and both branches are valid
  outcomes.
- A killed worker's dead group member keeps its session for 15 s, so a restart may take about 20 s
  rather than the estimator's 12 s (preflight-2 observed 3.7–5.2 s).
- During K1 and K2, consumers log `consumer_error` and keep polling, with no back-off; the rejoin
  bound of 19 s is assumed to hold.
- X1's first duplicate arrives while its owner runs the job, so it is read only afterwards. Both
```

## 32. Assistant — 2026-10-25T04:07:09.329Z

### Tool call: Bash

````
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nreps = [\n(\"\"\"compares them with what the preflights observed. \"Finish by\" is the latest finish the design predicts, B + T, from the deadline's reference; the\nmargin is D minus it.\"\"\",\n\"\"\"compares them with what the preflights observed. \"Finish by\" is the latest finish the design\npredicts, B + T, from the deadline's reference; the margin is D minus it.\"\"\"),\n(\"\"\"  (section 11). From the stop, F comes 40–50 s later; MySQL returns after 30 s plus\n  its restore. D1's and D2's branches therefore depend on the restore, and both branches are valid\n  outcomes.\"\"\",\n\"\"\"  (section 11). From the stop, F comes 40–50 s later; MySQL returns after 30 s plus its restore.\n  D1's and D2's branches therefore depend on the restore, and both branches are valid outcomes.\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\ncode = False\nover = [n for n, line in enumerate(s.splitlines(), 1)\n        if (code := (not code) if line.startswith(\"```\") else code) is not None and not line.startswith((\"```\", \"|\")) and len(line) > 100]\nprint(\"prose lines over 100 characters (code blocks included in this pass):\", over)\nEOF",
  "description": "Rewrap the two joined paragraphs and recheck widths"
}
````

## 33. User — 2026-10-25T04:07:10.307Z

### Tool result

```
prose lines over 100 characters (code blocks included in this pass): [171, 175, 190, 192, 200, 202, 207, 209]
```

## 34. Assistant — 2026-10-25T04:07:15.608Z

### Tool call: Bash

```
{
  "command": "awk 'NR>=164 && NR<=211 {printf \"%3d %3d| %s\\n\", NR, length($0), $0}' docs/recovery-part-a.md | cut -c1-150",
  "description": "Show the commands block with line lengths"
}
```

## 35. User — 2026-10-25T04:07:16.298Z

### Tool result

````
164   0| 
165  75| ## 7. Commands (from the repository root of the checkout that ran the plan)
166   0| 
167   7| ```bash
168  77| # 0. Preconditions: the test window is released; nothing of this project runs
169  83| docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
170 100| uv run --group jobs python -m etf_risk.services others         # other projects' containers: a count
171 117| pgrep -lf 'pytest|etf_risk\.jobs|org\.apache\.spark'            # must print nothing: no competing tests (section 12)
172 100| git status --short                                             # clean: the batch records the commit
173  88| pmset -g batt | head -1                                        # 'AC Power' (section 12)
174  95| ioreg -r -k AppleClamshellState -d 4 | grep '"AppleClamshellState"'   # '= No': the lid is open
175 116| uv run --group jobs python -c "import psutil; print(psutil.virtual_memory().available / 2**30)"   # GiB (section 12)
176   0| 
177  98| # 1. Live preflight (8.6 of the outline): before any formal batch, kept apart from formal results.
178  90| #    --jobs keeps the order as listed and adds no controls; this list has a C0 at each end
179  87| uv run --group jobs python -m etf_risk.jobs.harness plan --purpose preflight --seed 1 \
180  87|     --jobs C0,W1,W6,W7,K1,K2,D1,D2,C0 --out data/outputs-recovery/preflight/plan-1.json
181  92| # Keep the host awake: on AC power with the lid open (section 12); -s works on AC power only
182  76| caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
183  99|     --plan data/outputs-recovery/preflight/plan-1.json --out data/outputs-recovery/preflight/<name>
184  70| uv run --group jobs python analysis/collect_recovery_measurements.py \
185  50|     --batch data/outputs-recovery/preflight/<name>
186  98| # The job tests and the live pipeline tests against both services, outputs kept with the preflight
187  62| docker compose -f docker/compose.yaml up -d --wait mysql kafka
188  65| uv run --group jobs python -m etf_risk.services ready mysql kafka
189  98| ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
190 118|     uv run --group jobs python -m pytest tests/test_jobs_*.py 2>&1 | tee data/outputs-recovery/preflight/job-tests.txt
191  83| ETF_RISK_LIVE_PIPELINE=1 ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 \
192 115|     ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 uv run --group jobs python -m pytest tests/test_jobs_live_pipeline.py \
193  64|     2>&1 | tee data/outputs-recovery/preflight/live-pipeline.txt
194  45| docker compose -f docker/compose.yaml down -v
195   0| 
196  98| # 2. Formal batch: only after the author approves Part A. The default plan is the preferred draft:
197  88| #    30 jobs, a C0 control at each end of the 28 shuffled ones (`controls` in plan.json)
198  89| uv run --group jobs python -m etf_risk.jobs.harness plan --purpose formal --seed <SEED> \
199  55|     --out data/outputs-recovery/formal/plan-<SEED>.json
200 113| uv run --group jobs python -m etf_risk.jobs.harness estimate --plan data/outputs-recovery/formal/plan-<SEED>.json
201  76| caffeinate -dims uv run --group jobs python -m etf_risk.jobs.harness batch \
202 108|     --plan data/outputs-recovery/formal/plan-<SEED>.json --out data/outputs-recovery/formal/batch-1 --formal
203   0| 
204  95| # 3. Collection: injections.csv, tally.csv and validity.json in the batch folder. It prints two
205  96| #    verdicts, correctness observations and recovery times, and exits 1 if any check fails, even
206  99| #    one that invalidates only the recovery times (a battery reading, a closed lid, an unknown one)
207 113| uv run --group jobs python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/formal/batch-1
208   0| 
209 102| # 4. Cleanup: the batch itself ends with `docker compose down -v`; check, and recover if it was killed
210  83| docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
211  91| docker compose -f docker/compose.yaml down -v                  # only if something was left
````

## 36. Assistant — 2026-10-25T04:07:22.972Z

Part A edits are in. I'm aligning one command comment, then moving on to the outline's revision note.

## 37. Assistant — 2026-10-25T04:07:26.130Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-part-a.md\")\ns = p.read_text()\nold = \"pgrep -lf 'pytest|etf_risk\\\\.jobs|org\\\\.apache\\\\.spark'            # must print nothing: no competing tests (section 12)\\n\"\nnew = \"pgrep -lf 'pytest|etf_risk\\\\.jobs|org\\\\.apache\\\\.spark'           # must print nothing (section 12, condition 4)\\n\"\nassert s.count(old) == 1\np.write_text(s.replace(old, new))\nEOF\nawk 'NR>=169 && NR<=172' docs/recovery-part-a.md; echo \"--- outline: revisions and section 9\"; grep -n \"^## \\|^### \\|Revision\\|revision 9\\|^- \\*\\*9\\.\\|Not done\" docs/recovery-experiments.md | cut -c1-140 | tail -30",
  "description": "Align the pgrep comment and locate the outline's revision notes"
}
```

## 38. User — 2026-10-25T04:07:26.991Z

### Tool result

```
docker compose -f docker/compose.yaml ps -a -q                 # must print nothing
uv run --group jobs python -m etf_risk.services others         # other projects' containers: a count
pgrep -lf 'pytest|etf_risk\.jobs|org\.apache\.spark'           # must print nothing (section 12, condition 4)
git status --short                                             # clean: the batch records the commit
--- outline: revisions and section 9
290:### 4.6 Container peaks by segment
299:## 5. Metrics
335:## 6. Checks
337:### 6.1 Validity
345:### 6.2 Database acceptance correctness (answers E1)
356:### 6.3 Timeliness and lost jobs (answers E2)
361:### 6.4 Event-log completeness and report identity
371:### 6.5 Other outcome checks
383:## 7. SQL cross-check
404:## 8. Part A decisions: proposals
420:### 8.1 Repetitions and workload
453:### 8.2 Timing and deadlines
499:### 8.3 Memory
514:### 8.4 Injection method
533:### 8.5 Still open
542:### 8.6 The live preflight (proposal)
569:## 9. Records, prerequisites and authorship
623:- **Not done:**
638:## 10. Not claimed
646:## History
649:- **Revision 1, 2026-10-23.** The first review (1.1): deadlines and their observation, quiescence
654:- **Revision 2, 2026-10-23.** The second review: `6d8a232` and M2's report as inputs, with the
658:- **Revision 3, 2026-10-23.** The third review: the queries validated once against a scratch MySQL
663:- **Revision 4, 2026-10-24.** The fourth review: the fixture run accepted as tooling evidence only;
669:- **Revision 4, tests, 2026-10-24.** The offline tests run in an exclusive window the author gave;
675:- **Revision 5, 2026-10-24.** The sixth review (1.1): the policy stated as "no acceptance call
681:- **Revision 6, 2026-10-24.** The draft Part A proposal for 28 jobs
687:- **Revision 7, 2026-10-24.** The live preflight, the job tests against the services, the live
696:- **Revision 8, 2026-10-24.** G9 fixed (`a94eefe`), with a regression test and a focused mutation.
705:- **Revision 9, 2026-10-24.** The host conditions are replaced by a protocol for this 8 GiB Mac:
```

## 39. Assistant — 2026-10-25T04:07:31.150Z

### Tool call: Bash

```
{
  "command": "sed -n 619,640p docs/recovery-experiments.md && echo ... && sed -n 696,730p docs/recovery-experiments.md && echo \"--- 1.1 approvals\" && grep -n \"^### 1.1\\|^## 1\\b\\|^## 1\\.\" docs/recovery-experiments.md | head",
  "description": "Read the outline's section 9 list and recent revisions"
}
```

## 40. User — 2026-10-25T04:07:31.836Z

### Tool result

```
  seen the step end; fixed and tested.
- **Mutation checks, 2026-10-24.** The 27 focused mutations of `tests/mutation_check.py`, each run
  against the one test file that should catch it, after those files passed unmutated: 27 caught,
  none survived, no error. The 49 earlier mutations of the job queue were not run again.
- **Not done:**
  - any formal batch;
  - a plan option to put a control C0 at both ends of a shuffled plan;
  - the collector's flag of a battery or closed-lid reading as a timing failure (the same document,
    section 12).

  On 2026-10-24 G9 was fixed (`a94eefe`), the host's power, lid, memory pressure and swap came to be
  recorded per job (`8c5331d`), and the MySQL and Kafka variants of the tests and four live
  preflights ran (the same document, sections 9, 11 and 12).
- **Authorship.** Spec §11: the job code is written with Claude Code. At the author's decision of
  2026-10-24, Claude Code also writes the recovery experiments' tooling listed above, and each new
  module says so. The items in 1.1, and the experiments' decisions, runs and answers, are the
  author's; everything else here is Claude Code's proposal. The queries of
  [recovery-sql.md](recovery-sql.md) stay marked as drafted with Claude Code.

## 10. Not claimed

Times hold for this machine, the clock of 8.2, and one broker and one database (spec §11). Results
...
- **Revision 8, 2026-10-24.** G9 fixed (`a94eefe`), with a regression test and a focused mutation.
  Preflight-3 ran W2, W3, W4, W5a, W5b and X1 live from a relative batch folder.
  - Every correctness check held.
  - The batch failed the clock check, because the host slept on battery with its lid closed during
    W3.
  - M2's isolated check validated the container limits under host pressure.

  Host conditions for formal batches are proposed, apart for correctness and for timing claims
  ([recovery-part-a.md](recovery-part-a.md), section 12). Part A stays provisional.
- **Revision 9, 2026-10-24.** The host conditions are replaced by a protocol for this 8 GiB Mac:
  AC power, the lid open, sleep prevented, no competing tests, memory pressure and swap recorded,
  controls in the same batch, every outcome kept. No memory figure is used as a gate: M2's 5 and
  4.0 GiB were its check's own gates, and its 35.1 s was measured under host pressure too.
  - The harness records power, lid, memory pressure and swap (`8c5331d`).
  - Preflight-3 stays invalid for timing, its correctness observations kept apart.
  - Preflight-4 reran W3 on AC power with the lid open, between two controls, and passed validity.

  Recovery times observed on this host are kept apart from performance claims, which are not made
  ([recovery-part-a.md](recovery-part-a.md), sections 11 and 12). Part A stays provisional.
--- 1.1 approvals
20:## 1. Questions and scope
41:### 1.1 Decided or required by the author
```

## 41. Assistant — 2026-10-25T04:07:36.187Z

### Tool call: Bash

```
{
  "command": "sed -n 41,75p docs/recovery-experiments.md",
  "description": "Read the outline's list of author decisions"
}
```

## 42. User — 2026-10-25T04:07:36.848Z

### Tool result

```
### 1.1 Decided or required by the author

How each item is met is Claude Code's proposal, in the sections named.

- **First review (2026-10-23).** Explicit deadlines, with on-time completion, late completion and
  unfinished jobs apart, and no later success erasing a miss (4.2, 4.3). Database acceptance
  correctness apart from event-log completeness, including a crash after the acceptance commits and
  before its event (W5a); repeated reports of one attempt are not multiple accepted results (6.2,
  6.4). No artifacts required of crashed attempts; code identity at each launch; a missing interval
  is unknown (2.3, 6.5). Monotonic durations, and recovery latency `n/a` after acceptance (4.1,
  section 5). Kafka assignment conditions in the predictions and a fixed startup order (2.4, 3.2).
  Full report identity, `store_id` and `worker_id` included (6.4). A defined deadline observation,
  quiescence and consistent snapshot (4.3–4.5). Reference runs under the host lock (2.2); no pooled
  rule-of-three claim (8.1); small SQL fixtures; every case and failed outcome visible (3.1,
  section 9).
- **Second review.** `6d8a232` and its final report as design inputs, with the isolated
  memory-budget check pending (8.3). Peaks before every injected restart, maximum across segments
  (4.6). The partition owner from assignment events, never from `client.id` ordering (2.4).
  `deadline not observed` as an explicit unknown (4.2). The fixtures run against a scratch MySQL
  once no other session's tests run, compared with explicit expected rows and extended to every
  verdict ([recovery-sql.md](recovery-sql.md)).
- **Third review.** Run the fixtures only after the M2 session releases the test window, recheck
  before startup, and remove only this session's container; keep the expected rows frozen and report
  every mismatch, explaining any correction. No restart duration inferred from failed-renewal counts
  (8.2). A shorter outline with the SQL details apart, and a small set of Part A decisions proposed
  with reasons (section 8).
- **Fourth review (2026-10-24).** The 82-row fixture validation counts as tooling evidence, not as
  approval of Part A. Claude Code writes the tooling (the harness, the collector, assignment events,
  launch-time code identity and precise fault-injection hooks) with accurate attribution (section 9).
  The frozen SQL expectations stay as they are. The deadline formulas are reassessed and the
  duration of all 84 proposed jobs is estimated (8.1, 8.2); timing, repetitions and memory
  thresholds stay provisional. Every test or container run waits for coordination with the M2
  session.
- **Fifth review (2026-10-24).** An exclusive window for offline dependency setup and tests. The
  acceptance deadline enforced as the approved policy states; monotonic launcher times for same-host
```

## 43. Assistant — 2026-10-25T04:07:40.111Z

### Tool call: Bash

```
{
  "command": "sed -n 75,110p docs/recovery-experiments.md",
  "description": "Read the rest of the author decisions list"
}
```

## 44. User — 2026-10-25T04:07:40.899Z

### Tool result

```
  acceptance deadline enforced as the approved policy states; monotonic launcher times for same-host
  overlap checks; deterministic tests for the first acceptance call after F, arming without a change
  of owner, missing crash records, unknown observations, late completion and every frozen SQL
  verdict; a synthetic batch end to end without services; a smaller formal experiment proposed, with
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
- **Throughout.** No formal experiment, and Part A is not approved. Until the fourth review the work
  was documents only.

## 2. Batch protocol (proposal)

### 2.1 Services, jobs and controls

MySQL 8.4.13 and Kafka 4.3.1 from [docker/compose.yaml](../docker/compose.yaml); the reconciler and
two workers, A and B, as native processes; one job at a time on this machine (spec §11). A session
harness (M3 code, not written) submits jobs, injects failures, takes deadline observations and
container peaks, restarts workers (2.4) and keeps the records (section 9). Each batch starts on
fresh containers and ends with the final snapshot (4.5). Jobs use the parameter sets of M2's
acceptance runs (kinds `calendar-year` and `rolling`, stride 21, snapshot `full-2026-10-12`, 3
attempts; choice in 8.1). Control jobs (case C0) give the failure-free time to finish, T.

### 2.2 Reference runs

One direct run of the three CLIs per parameter set, under the host execution lock, taken as a
launcher takes it: an exclusive `flock`, the wait until no earlier tree survives, and an entry in
the registry, so that a later launcher waits for the reference run's survivors too. A reference run
then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference
runs come before the workers start, so that they delay no measured step. Implemented, and run in
```

## 45. Assistant — 2026-10-25T04:08:18.540Z

### Tool call: Bash

```
{
  "command": "grep -o 'battery-passes[^\"]\\{0,80\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | sort | uniq -c | head -8; grep -o '[0-9]* caught[^\"]\\{0,60\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | tail -5; grep -n \"add_argument\" tests/mutation_check.py | cut -c1-140",
  "description": "Check whether the newest mutations were already run"
}
```

## 46. User — 2026-10-25T04:08:20.889Z

### Tool result

```
   2 battery-passes (2.7 s)  FAILED tests/test_recovery_collector.py::test_a_reading_on_battery_fai
   5 battery-passes lid-closed-passes unknown-reading-passes timing-verdict-without-host end-readin
   2 battery-passes, lid-closed-passes, unknown-reading-passes, timing-verdict-without-host, end-re
   2 battery-passes[^\
   4 battery-passes\
8 caught).\n17\t\n18\tThe 2026-10-24 doc revisions are uncommitted f
27 caught,\n  none survived, no error. The 49 earlier mutations of th
27 caught,\n  none survived, no error. The 49 earlier mutations of th
 caught[^\
 caught[^\
423:    parser.add_argument("--only", nargs="+", metavar="ID", help="run these mutations only")
424:    parser.add_argument("--timeout", type=float, default=600.0, help="seconds per run of the job tests (default 600)")
425:    parser.add_argument("--out", type=Path, help="folder for mutations.json")
426:    parser.add_argument("--list", action="store_true", help="list the mutations and exit")
```

## 47. Assistant — 2026-10-25T04:08:30.519Z

### Tool call: Bash

```
{
  "command": "grep -o 'controls-not-bracketed ([0-9.]* s)[^\"]\\{0,60\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | head -2; grep -o '[a-z-]*passes ([0-9.]* s)  [A-Z]*\\|end-reading-not-required ([0-9.]* s)  [A-Z]*\\|timing-verdict-without-host ([0-9.]* s)  [A-Z]*' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | sort -u; grep -o 'caught: [0-9]*[^\"]\\{0,80\\}\\|[0-9]* of [0-9]* caught[^\"]\\{0,40\\}' ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl | tail -4",
  "description": "Find the newest mutation run's per-mutation results"
}
```

## 48. User — 2026-10-25T04:08:34.936Z

### Tool result

```
controls-not-bracketed (0.8 s)  FAILED tests/test_jobs_harness.py::test_a_plan_has_two_job
controls-not-bracketed (0.8 s)  FAILED tests/test_jobs_harness.py::test_a_plan_has_two_job
battery-passes (2.7 s)  FAILED
end-reading-not-required (2.9 s)  FAILED
lid-closed-passes (2.9 s)  FAILED
timing-verdict-without-host (2.7 s)  FAILED
unknown-reading-passes (2.9 s)  FAILED
17 of 17 caught, each by its intended test. Committing 
17 of 17 caught, each by its intended test. Committing 
caught: [0-9]*[^\
caught: [0-9]*[^\
```

## 49. Assistant — 2026-10-25T04:08:40.755Z

Part A is updated. Now recording the approvals and the remaining "not done" items in the outline.

## 50. Assistant — 2026-10-25T04:08:53.946Z

### Tool call: Bash

````
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nreps = [\n(\"\"\"  28-job design is the preferred draft; deadlines, memory rules and runtime estimates are finalized\n  only after the preflight (8.1–8.3).\n- **Throughout.** No formal experiment, and Part A is not approved. Until the fourth review the work\n  was documents only.\"\"\",\n\"\"\"  28-job design is the preferred draft; deadlines, memory rules and runtime estimates are finalized\n  only after the preflight (8.1–8.3).\n- **Later reviews (2026-10-24).**\n  - G1–G8 fixed before the live preflight, and G9 after preflight-1 found it\n    ([recovery-part-a.md](recovery-part-a.md), section 9).\n  - The preflights are functional validation under the recorded memory pressure, not performance or\n    memory-budget evidence. Preflight-3 stays invalid for timing, with its correctness observations\n    kept apart.\n  - M2's 5 and 4.0 GiB gates and its 35.1 s are not validated standards for these experiments; a\n    protocol for this 8 GiB Mac instead, with power and swap recorded and observed recovery times\n    kept apart from performance claims (the same document, section 12).\n  - Approved: this host for correctness observations and for recovery times under its recorded\n    conditions, with the limitations stated in Part A; a control C0 at each end of the batch, making\n    30 jobs.\n  - Required: the collector's timing validity fails a battery reading or a closed lid, and a missing\n    reading is handled explicitly, never passed silently.\n- **Throughout.** No formal experiment; Part A is not approved as a whole, only the items approved\n  above. Until the fourth review the work was documents only.\"\"\"),\n(\"\"\"- **Not done:**\n  - any formal batch;\n  - a plan option to put a control C0 at both ends of a shuffled plan;\n  - the collector's flag of a battery or closed-lid reading as a timing failure (the same document,\n    section 12).\n\n  On 2026-10-24 G9 was fixed (`a94eefe`), the host's power, lid, memory pressure and swap came to be\n  recorded per job (`8c5331d`), and the MySQL and Kafka variants of the tests and four live\n  preflights ran (the same document, sections 9, 11 and 12).\"\"\",\n\"\"\"- **Not done:** any formal batch.\n\n  On 2026-10-24 G9 was fixed (`a94eefe`), the host's power, lid, memory pressure and swap came to be\n  recorded per job (`8c5331d`), and the MySQL and Kafka variants of the tests and four live\n  preflights ran. Then the default plan gained a C0 control at each end, and the collector two\n  verdicts, correctness observations and recovery times; a battery, closed-lid or missing reading\n  fails the second (`5a81bc5`). Before that commit, 17 focused mutations, its six new ones included,\n  were run: 17 caught, each by its intended test (the same document, sections 9, 11 and 12).\"\"\"),\n(\"\"\"  Recovery times observed on this host are kept apart from performance claims, which are not made\n  ([recovery-part-a.md](recovery-part-a.md), sections 11 and 12). Part A stays provisional.\"\"\",\n\"\"\"  Recovery times observed on this host are kept apart from performance claims, which are not made\n  ([recovery-part-a.md](recovery-part-a.md), sections 11 and 12). Part A stays provisional.\n- **Revision 10, 2026-10-24.** The author approved this host for correctness observations and for\n  recovery times under its recorded conditions, and a control C0 at each end of the batch (30\n  jobs); Part A is otherwise provisional.\n  - The default plan brackets the shuffled 28 jobs with the two controls (`5a81bc5`).\n  - The collector gives two verdicts. Recovery times also need the clock check, AC power and the\n    lid open at every reading the batch needs, and a missing reading counts as unknown, which fails.\n  - Recomputed under these checks, without writing to the records: preflight-1 is invalid for both,\n    preflight-2 and preflight-3 are valid for correctness only, and preflight-4 is valid for both.\n\n  Part A gives the 30-job runtime (about 51 min for the batch) and the final draft for review\n  ([recovery-part-a.md](recovery-part-a.md), sections 8, 10–12).\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\ncode = False\nfor n, line in enumerate(s.splitlines(), 1):\n    if line.startswith(\"```\"):\n        code = not code\n        continue\n    if not code and not line.startswith(\"|\") and len(line) > 100:\n        print(f\"over 100: line {n}: {len(line)}\")\nprint(\"applied\", len(reps))\nEOF\ngrep -n \"^\\(Author\\|_Drafted\\)\" docs/recovery-experiments.md | head -3; sed -n 6,8p docs/recovery-experiments.md",
  "description": "Record the approvals, done items and revision 10 in the outline"
}
````

## 51. User — 2026-10-25T04:08:54.771Z

### Tool result

```
over 100: line 13: 101
over 100: line 69: 101
over 100: line 83: 101
over 100: line 125: 101
over 100: line 200: 101
over 100: line 367: 101
over 100: line 454: 102
over 100: line 459: 101
over 100: line 464: 101
over 100: line 481: 101
over 100: line 506: 101
over 100: line 510: 101
over 100: line 517: 101
over 100: line 520: 101
over 100: line 543: 101
over 100: line 566: 101
over 100: line 572: 102
over 100: line 573: 101
over 100: line 580: 101
over 100: line 669: 101
applied 3
3:Author: _to be written by the author after review. Beyond spec §11, the only decisions by the
6:_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised four times from the author's
_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised four times from the author's
reviews (history at the end). This is an outline for review, not an approved Part A: everything not
in 1.1 or cited from spec §11 or M2 is Claude Code's proposal, and the decisions in section 8 are
```

## 52. Assistant — 2026-10-25T04:09:07.334Z

### Tool call: Bash

```
{
  "command": "git diff -U0 docs/recovery-experiments.md | grep '^+' | awk 'length($0)>101 {print length($0)\": \"$0}' | cut -c1-120; echo \"(no output above = no new outline line over 100 characters; awk counts bytes)\"; python3 - <<'EOF'\nimport subprocess\ndiff = subprocess.run([\"git\", \"diff\", \"-U0\", \"docs/recovery-experiments.md\"], capture_output=True, text=True).stdout\nlong = [l for l in diff.splitlines() if l.startswith(\"+\") and not l.startswith(\"+++\") and not l.startswith(\"+|\") and len(l) - 1 > 100]\nprint(\"added outline lines over 100 characters:\", len(long))\nfor l in long: print(len(l) - 1, l[:90])\nEOF",
  "description": "Check only the outline lines this work added"
}
```

## 53. User — 2026-10-25T04:09:08.133Z

### Tool result

```
(no output above = no new outline line over 100 characters; awk counts bytes)
added outline lines over 100 characters: 0
```

## 54. Assistant — 2026-10-25T04:09:16.610Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nold = \"_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised four times from the author's\\n\"\nnew = \"_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised ten times from the author's\\n\"\nassert s.count(old) == 1\np.write_text(s.replace(old, new))\nEOF\ngrep -rln \"recovery-part-a.md\\|recovery-experiments.md\" tests/ | head; uv run --group jobs python -m pytest tests/test_jobs_harness.py tests/test_recovery_sql.py tests/test_recovery_collector.py tests/test_recovery_synthetic.py -q 2>&1 | tail -4",
  "description": "Fix the outline's revision count and run the doc-reading tests"
}
```

## 55. User — 2026-10-25T04:09:49.671Z

### Tool result

```
tests//test_provenance.py
tests//test_recovery_collector.py
tests//__pycache__/test_provenance.cpython-312.pyc
tests//__pycache__/test_provenance.cpython-312-pytest-9.1.1.pyc
tests//__pycache__/mutation_check.cpython-312.pyc
tests//__pycache__/test_jobs_kafka.cpython-312.pyc
tests//__pycache__/test_recovery_collector.cpython-312-pytest-9.1.1.pyc
tests//__pycache__/test_jobs_kafka.cpython-312-pytest-9.1.1.pyc
tests//test_jobs_harness.py
tests//mutation_check.py
    days = mcal.get_calendar("NYSE").valid_days(start, pd.Timestamp(start) + pd.Timedelta(days=2 * n + 30))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
59 passed, 161 warnings in 30.64s
```

## 56. Assistant — 2026-10-25T04:09:56.493Z

### Tool call: Bash

```
{
  "command": "grep -n \"recovery-part-a\\|recovery-experiments\" tests/test_provenance.py tests/test_jobs_kafka.py | cut -c1-150; uv run --group jobs python -m pytest tests/test_provenance.py tests/test_jobs_kafka.py -q 2>&1 | tail -3",
  "description": "Run the other tests that read these documents"
}
```

## 57. User — 2026-10-25T04:10:00.531Z

### Tool result

```
tests/test_provenance.py:22:    """What a starting process and a step launch record (docs/recovery-experiments.md, 2.3)."""
tests/test_jobs_kafka.py:70:    """The recovery harness reads the partition's owner from these events (docs/recovery-experiments.md, 2.4)."""

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
12 passed, 11 skipped, 1 warning in 2.36s
```

## 58. Assistant — 2026-10-25T04:10:10.392Z

### Tool call: Bash

```
{
  "command": "sed -n 1,21p docs/recovery-part-a.md; echo \"......\"; sed -n 299,335p docs/recovery-part-a.md",
  "description": "Proofread the header and the start of section 11"
}
```

## 59. User — 2026-10-25T04:10:11.042Z

### Tool result

```
# Recovery experiments: Part A proposal, 30 jobs (DRAFT)

> **Draft; Part A is not approved as a whole.** No formal batch has run. The author approved two
> items on 2026-10-24:
> - this host, for correctness observations and for recovery times under its recorded conditions,
>   with the limitations of section 12;
> - a control C0 at each end of the batch, making 30 jobs.
>
> Everything else, the deadlines and memory rules included, stays provisional.

_This document condenses [recovery-experiments.md](recovery-experiments.md) for the preferred
draft. Every command, event and record in it was checked against the tooling at `5a81bc5`. M2's
isolated check has since validated the container limits, under host memory pressure and with
documented sampling limits; native-process memory remains unvalidated. Four live preflight batches
ran on 2026-10-24 under memory pressure (section 11). Under the collector's current checks, only
preflight-4 is valid for recovery times, and preflight-3 stays invalid for timing. None of their
times or memory readings is performance or budget evidence. Section 12 proposes a protocol for
recovery batches on this host. Drafted with Claude Code (Opus 5.5) at the author's request on
2026-10-24; the decisions in section 10 are the author's._

## 1. Workload
......
| job tests against MySQL 8.4 and Kafka | 515 passed, 10 skipped (the live cases, run next), 0 failed, in 2 min 53 s |
| live pipeline module | 10 passed, 0 failed, in 10 min 54 s; its overlap check now compares monotonic times |
| full offline suite, after the services were removed | 622 passed, 30 skipped (the MySQL, Kafka and live tests, which passed in the two runs above), 0 failed, in 9 min 54 s, Spark tests included |
| preflight-3: C0, W2, W3, W4, W5a, W5b, X1, from a relative batch folder | **invalid for timing**: the clock check failed, because the host slept for about 22 min during W3 (below). 7 of 7 injections made, none missed; its correctness observations are kept apart (below); harness exit 0; 11.6 min monotonic, 33.8 min wall |
| preflight-4: C0, W3, C0 (the W3 rerun with a control on each side), on AC power with the lid open | 3 of 3 injections made; validity passed, the clock check included; harness exit 0 (below) |

**Verdicts under the collector at `5a81bc5`.** Recomputed on 2026-10-24 without writing anything:
the 1,109 files under `data/outputs-recovery/preflight/` kept their modification times.

| Batch | Correctness observations | Recovery times | Failed or unknown |
|---|---|---|---|
| preflight-1 | invalid | invalid | `records_complete` (the setup error); power and lid unknown at the start and end readings |
| preflight-2 | valid | invalid | power and lid unknown at all 11 readings: the batch predates their recording |
| preflight-3 | valid | invalid | the clock check (the host sleep); power and lid unknown at all 9 readings |
| preflight-4 | valid | valid | — |

Preflight-4 is the only batch whose recovery times count under section 12, and as a preflight it
stays apart from formal results.

Preflight-2 by case, functional observations only (verdicts above). Finish is measured from the
deadline's reference; D is from section 3.

| Case | Claims | Detection | Finish | D | Observed path |
|---|---|---|---|---|---|
| C0 | 1 | — | 52.4 s | 75 s | baseline |
| W1 | 1 | standby's `delivered`, 13.5 s | 69.8 s | 90 s | killed at `before_claim`; the standby took over |
| W6 | 2 | `requeued`, 57.9 s | 103.9 s | 140 s | the worker stopped; takeover; fenced after SIGCONT |
| W7 | 2 | `requeued`, 57.5 s | 132.0 s | 170 s | a tree of 4 processes stopped for 90 s; the replacement ran after it |
| K1 | 1 | — | 47.6 s | 75 s | Kafka ready 9.3 s after its restart began; the attempt went on |
| K2 | 1 | `published`, 3.0 s after Kafka's return | 64.3 s | 125 s | Kafka back 33.9 s after the stop; one claim |
| D1 | 2 | `renewal_failed`, 5.9 s after the stop | 54.6 s | 140 s | MySQL back 40.8 s after the stop, after F: fenced, then attempt 2 |
| D2 | 1 | `retry` of `accept_result`, 3.9 s after the stop | 0.5 s | 140 s | MySQL back 31.6 s after the stop, before F: accepted |
| C0 | 1 | — | 46.8 s | 75 s | baseline |

- **E1 and the records:**
  - every Q1 verdict `ok`, no overlapping step intervals, `status --check` exit 0 and no invariant
    violation;
```

## 60. Assistant — 2026-10-25T04:10:36.174Z

Docs are done and the tests that read them pass. Updating the project memory note next, without printing the index.

## 61. Assistant — 2026-10-25T04:10:47.046Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md",
  "content": "[REDACTED:memory]"
}
```

## 62. User — 2026-10-25T04:10:47.943Z

### Tool result

```
[REDACTED:memory]
```

## 63. Assistant — 2026-10-25T04:10:49.283Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Update the memory index pointer without printing the index"
}
```

## 64. User — 2026-10-25T04:10:50.176Z

### Tool result

```
[REDACTED:memory]
```

## 65. Assistant — 2026-10-25T04:10:56.935Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness; git -C $W status --short; git -C $W log --oneline -1; git -C $W diff --stat; docker compose -f $W/docker/compose.yaml ps -a -q | wc -l | xargs echo \"project containers:\"; sed -n 432,475p $W/docs/recovery-part-a.md",
  "description": "Confirm the worktree state and proofread section 12"
}
```

## 66. User — 2026-10-25T04:11:00.928Z

### Tool result

```
 M docs/recovery-experiments.md
 M docs/recovery-part-a.md
5a81bc5 Bracket each plan with controls and check timing validity per batch
 docs/recovery-experiments.md |  71 ++++++++--
 docs/recovery-part-a.md      | 318 ++++++++++++++++++++++++++++++++++---------
 2 files changed, 313 insertions(+), 76 deletions(-)
project containers: 0
- **Its 5 GiB and 4.0 GiB figures** were the gates of that check. They were never established as
  requirements for recovery experiments.
- **Its step times** (35.1 s for the calendar-year job) were also measured under host memory
  pressure.
- **Native-process memory** (workers, launchers, the Spark driver and JVM, the reconciler, the
  harness) is unvalidated.

None of these is used here as a validated standard. This draft earlier proposed a 2.5 GiB minimum
before each job; nothing measured ties that figure, or any other, to unchanged recovery behaviour on
this host, so it is withdrawn. Every live run so far had 1.2–1.9 GiB available and swap in use;
preflight-4, the first batch to record macOS's pressure level, had it at warning before every job.

**The protocol, for every batch, preflight or formal:**
1. **AC power throughout.** Checked before the start with `pmset -g batt`, and recorded in every
   host reading. A reading on battery, or a missing one, fails the batch for timing.
2. **Lid open throughout.** Checked before the start with `ioreg`, and recorded
   (`AppleClamshellState`) in every reading. A closed reading, or a missing one, fails the batch for
   timing.
3. **Sleep prevented.** The batch runs under `caffeinate -dims`, whose `-s` holds on AC power only.
   The clock check (1 s) detects any sleep that happens anyway and fails validity, as it did for
   preflight-3.
4. **No competing tests.** The exclusive window; no other containers (counted at the start); no
   other pytest, Spark or job processes (`pgrep` before the start, section 7).
5. **Memory pressure and swap recorded, never gated.** Available memory, swap in use, the bytes
   swapped in and out, and macOS's pressure level, at the start, before each job and at the end
   (`8c5331d`). Each job gets the swap activity of its window, and the batch its totals.
6. **Controls in the same batch.** C0 jobs measured in the same batch, under the same recorded host
   state: the two shuffled C0s, plus one C0 at the start and one at the end (approved on 2026-10-24;
   30 jobs, about 2 minutes more). Each case's times are reported next to these controls, for
   example its overhead over their median, rather than next to any external figure.
7. **Every outcome kept.** A batch that fails conditions 1–3, or lacks the readings to show them,
   stays invalid for timing and is never relabelled.

**Three kinds of claim.**

| Claim | Made from | Example |
|---|---|---|
| **Correctness** (E1): one accepted result per job, no overlapping steps, fencing, Q1 and Q3, accepted results equal to the reference, invariants | any batch whose checks that do not involve time pass: code identity, unchanged inputs, equal fingerprints, complete records. From a batch invalid for timing, they are kept as that batch's correctness observations, labelled as such (preflight-3) | "W3 kept one accepted result and no overlap across a 22-min host sleep" |
| **Recovery times observed on this host** (E2) | only batches that meet conditions 1–4 and whose recovery-times verdict is valid (the clock check, power and lid included); reported with the batch's host record and its controls | "W3: requeued 59.1 s after the kill, finished in 117.1 s; the controls took 45.1 and 50.9 s; pressure 2, 26.5 MiB swapped out during the job" (preflight-4) |
| **Performance claims**: recovery time as a property of the job system, comparable across machines or usable as a prediction | not made from this host | — |

- **Why the line falls there.**
  - Correctness rests on the job table's token guards, fencing and the host lock, which do not
    depend on time or memory: every job that ran kept it (preflights 2–4), under memory pressure and
```

## 67. Assistant — 2026-10-25T04:11:21.867Z

### Tool call: Bash

```
{
  "command": "grep -n \"^## \\|^\\*\\*Verdicts under\\|^\\*\\*Still open\" ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-part-a.md | cut -c1-90",
  "description": "List Part A's section line numbers for references"
}
```

## 68. User — 2026-10-25T04:11:22.535Z

### Tool result

```
21:## 1. Workload
53:## 2. Timing (P2: the defaults of timing.py, no override)
63:## 3. Deadlines (P3)
86:## 4. Predictions
125:## 5. Injection success and misses (harness)
144:## 6. Stop rules and outcomes
165:## 7. Commands (from the repository root of the checkout that ran the plan)
223:## 8. Runtime
244:## 9. Gaps in the service-only paths: G1–G9, fixed on 2026-10-24
262:## 10. Author decisions
269:**Still open:**
285:## 11. Live preflight, 2026-10-24: functional validation only
305:**Verdicts under the collector at `5a81bc5`.** Recomputed on 2026-10-24 without writin
427:## 12. A protocol for recovery batches on this 8 GiB Mac (proposal)
```

## 69. Assistant — 2026-10-25T04:11:58.267Z

Written for: you, as the author approving Part A. The document itself follows the style of the repository's docs.

The final Part A draft is ready: [docs/recovery-part-a.md](.claude/worktrees/recovery-harness/docs/recovery-part-a.md). I also updated [docs/recovery-experiments.md](.claude/worktrees/recovery-harness/docs/recovery-experiments.md). The tooling is committed as `5a81bc5`. Both documents are uncommitted so you can review them. I haven't run the formal batch, pushed or merged anything, and no containers are running.

## Final Part A

- **Status block:** it records your two approvals of 2026-10-24 (this host, under its recorded conditions; the two bracketing controls). Everything else stays provisional.
- **§1 Workload:** 30 jobs — a C0 control, then 28 shuffled jobs (2 per case), then another C0. The harness's default plan now builds this order.
- **§7 Commands:**
  - A new `pgrep` precondition checks for competing tests (protocol condition 4).
  - The formal plan's comment now says 30 jobs.
  - The collector prints two verdicts. It exits 1 whenever any check fails, including a failure that only invalidates the recovery times.
- **§8 Runtime:** I recomputed these just now with the estimator.
  - The batch takes 3,039 s, about 51 min; end to end about 53 min.
  - 53.5 min if T is 55 s; 53.4 min if restores take 20 s.
  - 51.2 min with the original assumptions.
- **§11:** a new table of verdicts under the current collector. I recomputed them without writing anything; the 1,109 record files kept their modification times.

  | Batch | Correctness | Recovery times | Why |
  |---|---|---|---|
  | preflight-1 | invalid | invalid | `records_complete` failed (setup error) |
  | preflight-2 | valid | invalid | power and lid unknown: the batch predates their recording |
  | preflight-3 | valid | invalid | the clock check failed (host sleep); power and lid unknown |
  | preflight-4 | valid | valid | — |

- **§12:** the tooling is now listed as implemented. A reading on battery, with the lid closed, or missing altogether fails the recovery-times verdict. A missing reading counts as unknown, and unknown always fails.

## Wording I corrected while updating — please check

1. **Swap and pressure:** swap and the pressure level appear in the batch records only from preflight-4 onward. The 4–10 GiB of swap I quoted for preflights 1–3 came from checks taken before each batch. "Pressure at warning" applies to preflight-4 only.
2. **"All four preflights kept correctness"** now reads "every job that ran (preflights 2–4)". Preflight-1 ran no jobs.
3. **§10's protocol row** said "as checked by the collector". The collector only checks conditions 1–3; condition 4 is checked before the start.
4. **§3 and §4 now quote observed values:** T of 45.1–52.4 s, restore times, restarts of 3.7–5.2 s. Preflight-2's C0 times are labelled planning figures only. The prediction table itself is unchanged.
5. **Outline:**
   - §1.1 stopped at your sixth review, though its header says it lists all your decisions. It now has a "Later reviews (2026-10-24)" entry.
   - §9 "Not done" now lists only the formal batch.
   - I added revision 10, and the header's count changes from "revised four times" to "ten".

## Still open (§10)

These still need your decision, with my recommendations unchanged:
- workload (P1), clock (P2), deadlines (P3);
- the harness's waits, the clock-check tolerance, the injection method;
- memory (P4) and the host protocol as a whole;
- the rule for batches invalid for timing, the rule for a preflight that finds a defect;
- the seed.

I kept the workload row open because you approved adding the controls, not the 28-job design as such. Tell me if you meant to approve both.

## Checks

- **Tests:** the harness, SQL, collector and synthetic test files: 59 passed. The provenance and Kafka test files: 12 passed, 11 skipped (the live Kafka cases; no services were running).
- **Mutations:** 17 of 17 focused mutations were caught before `5a81bc5`. That was recorded then; I didn't rerun them.
- **Branch:** `feature/recovery-harness` has 6 commits, none pushed: `772b647`, `7bd4d20`, `d675c85`, `a94eefe`, `8c5331d`, `5a81bc5`.

`★ Insight ─────────────────────────────────────`
- The collector treats each check's result as passed, failed or unknown. The verdicts count anything other than an explicit pass as a failure (`passed is not True`), which is how a missing power reading can't slip through.
- The exit code uses a narrower test (`passed is False`). Today the two agree only because every check returns a plain true or false. A future check that returns "no value" would fail a verdict but not the exit code, so it's worth keeping every check strictly true or false.
- Correctness checks are a subset of the timing checks, so a batch can be valid for correctness and invalid for recovery times (preflights 2 and 3), but never the reverse.
`─────────────────────────────────────────────────`

Once you approve, I'll commit the two documents by explicit path, with the AI logs in a separate commit. I can also publish Part A as a private rendered page if that would make it easier to share.
