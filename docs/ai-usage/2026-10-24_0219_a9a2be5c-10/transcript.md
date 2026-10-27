# Claude Code message 10

Session: `a9a2be5c-8da0-4ec5-be57-f251b5676fe9` · prompt sent 2026-10-24 02:19 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): email ×3, git-user ×408, home ×2396, memory ×25, model-reasoning ×226, private-file ×2, user ×182. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-24T07:19:42.359Z

This session is being continued from a previous conversation that ran out of context. The summary below covers the earlier portion of the conversation.

<tools-used-before-summary>Bash, Edit, ListAgents, Read, ToolSearch, Write</tools-used-before-summary>
Summary:
1. Primary Request and Intent:
   - **Original task (completed):** draft the E1/E2 recovery-experiment outline (spec §11) in a separate worktree, covering failure cases, metrics, correctness checks and a draft SQL cross-check of accepted results per job. Repetitions, deadlines and memory thresholds were left as pending decisions.
   - **Four review rounds (completed):**
     - Revision 1 answered the 7-point review.
     - Revision 2: M2 6d8a232 as design inputs, peaks by segment, owner from assignment events, explicit "deadline not observed", fixture B.
     - Revision 3: the validated SQL run (82/82), the SQL moved to recovery-sql.md, Part A proposals P1–P5.
     - Revision 4 / tooling: the harness, collector, assignment events, code identity at launch and fault hooks, written by Claude Code with accurate attribution; deadlines reassessed; 84 jobs estimated.
   - **Current request (latest user message), verbatim:**
     "You have the exclusive window for offline dependency setup and tests. Proceed without waiting for another session identifier. Do not start Docker or live tests yet.

     Run the new and affected tests, fix failures, and add deterministic coverage for:
     - the first acceptance call after deadline F;
     - fault arming without changing partition ownership;
     - missing crash records and unknown observations;
     - late completion and all frozen SQL verdicts.

     Fix the acceptance-deadline discrepancy consistently with the approved policy. Add monotonic launcher timestamps and use them for same-host overlap checks.

     Then run a synthetic end-to-end harness/collector test without services. Report actual results and remaining gaps together.

     Also propose a smaller formal experiment that preserves the main safety and recovery questions, with estimated runtime. Keep the current 84-job design as an alternative. Do not change Part A decisions or run formal experiments without approval."

2. Key Technical Concepts:
   - Job system (spec §11): MySQL job table with token guards, Kafka (classic protocol, one partition), worker, reconciler, launcher watchdog, host flock lock plus registry, process markers (ETF_RISK_ATTEMPT).
   - Default timing: lease 60, renew 10, fence_margin 10, worker_tick 1, watchdog 0.5, G = 5 + 2, step limits 120/600/300, attempt 900, session 15, heartbeat 3.
   - Reconciler: RECONCILE_INTERVAL 5 s, PUBLICATION_GRACE 30 s, CONFIRMATION_TIMEOUT 10 s.
   - Cases: C0, W1, W2, W3, W4, W5a, W5b, W6, W7, K1, K2, D1, D2, X1 (14 in all).
   - Hooks:
     - W1 before_claim (kill)
     - W2 after_claim (kill)
     - W4 after_pipeline (kill)
     - W5a after_accept_commit (kill)
     - W5b after_accept (kill)
     - D2 after_pipeline (hold)
   - Deadline observation is a consistent snapshot: `START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY`. It is taken at completion or at the deadline, whichever comes first.
   - Q2 classes: on time, late, unfinished, failed, missing, deadline not observed. deadline_met is yes/no/unknown.
   - deadline_from values: submit, injection, restored (K2/D1/D2). All fit VARCHAR(9).
   - Reassessed deadline formula: D = ceil5(B + 2S), with S = 35.1 s for calendar-year (2S = 70.2) and 63.4 s for stride 21.

     | Cases | B | Calendar-year D | Stride-21 D |
     |---|---|---|---|
     | C0, W5a, W5b, K1, X1 | 0 | 75 | 130 |
     | W1 | 19 | 90 | 150 |
     | W2, W3, W4, W6 | 65 | 140 | 195 |
     | W7 (σ = 90 s) | max(65, σ + 2·0.5 + 7) = 98 | 170 | 225 |
     | K2 (from restore) | 30 + 5 + 19 = 54 | 125 | 185 |
     | D1, D2 (from restore) | 65 | 140 | 195 |

     max_lag_s is 1 s; drain = D.
   - Duration estimate (Assumptions: T 40, restart 12, restore 20, peaks 2, group_settle 18, fixed 180).

     | Case | s | Case | s |
     |---|---|---|---|
     | C0 | 42 | W6 | 126 |
     | W1 | 74 | W7 | 159 |
     | W2 | 120 | K1 | 62 |
     | W3 | 126 | K2 | 118 |
     | W4 | 159 | D1 | 116 |
     | W5a | 54 | D2 | 149 |
     | W5b | 54 | X1 | 44 |

     - One round of 14 cases = 1,403 s; one batch of 42 jobs = 4,389 s; two batches = 8,778 s (about 2 h 26 min).
     - Each +5 s of T adds about 8 minutes.
   - Frozen SQL hash 447ef025fb0b44424b16197f112b4008510b73c8f2edeaa5fd4f639fbb7a9186. It was validated 82/82 on MySQL 8.4.13 on 2026-10-23 and is accepted as tooling evidence only.
   - MySQL constraints on the SQL: a TEMPORARY table cannot be referenced twice in one query; `CAST(... AS BINARY)` is used for worker_id.
   - SQLite translation notes (for offline SQL verdict tests):
     - remove `CHARACTER SET ascii COLLATE ascii_bin`;
     - replace `CAST(x AS BINARY)` with `x`, because SQLite gives "BINARY" NUMERIC affinity, which casts text to 0;
     - load schema/sqlite.sql;
     - store timestamps with a ".000000" suffix to match the expected rows.

3. Files and Code Sections:
   - **Worktree .claude/worktrees/recovery-harness** (branch feature/recovery-harness from e4adc38; uncommitted; .venv created; data symlinked)
   - **src/etf_risk/provenance.py**: added imports (hashlib, json) and three functions:
     ```python
     def source_digest(source_sha256: dict[str, str]) -> str:
         return hashlib.sha256(json.dumps(source_sha256, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
     def source_identity() -> dict:  # {"source_digest", "uv_lock_sha256"}, no git
     def code_identity() -> dict:    # git_commit, git_worktree_clean, source_digest, uv_lock_sha256
     ```
   - **src/etf_risk/jobs/faults.py** (new):
     - `FAULT_FILE_ENV = "ETF_RISK_FAULT_FILE"` and `ACTIONS = ("kill", "hold")`.
     - `class FaultFile(path, events, *, points=None, kill=_kill_self, sleep, clock, tick=0.1)`, called as `__call__(point)`:
       - reads the JSON spec; refuses malformed or unknown specs (fault_refused);
       - leaves a spec for a different point in place;
       - otherwise unlinks the file, logs fault_injected, then kills, or holds until the release path exists or timeout_s passes (fault_released, with why).
     - `fault_from_environment(events)`
     - `arm(path, point, action="kill", *, release=None, timeout_s=None)` writes the file atomically (tmp then replace).
   - **src/etf_risk/jobs/worker.py**:
     - WORKER_FAULT_POINTS now includes "after_accept_commit", between after_pipeline and after_accept.
     - In handle(): `self._fault("after_accept_commit")` runs after a successful accept and before `events.log("accepted", ...)`.
     - The docstring was updated.
     - The acceptance-deadline F check is not yet added (pending).
   - **src/etf_risk/jobs/pipeline.py**: imports source_identity; `step_started` now logs `code=source_identity()`.
   - **src/etf_risk/jobs/kafka.py**:
     - `log_assignment(events, kind, consumer, partitions)` logs `partitions=[[p.topic, p.partition]...]` and `member=consumer.memberid()` (None on error).
     - KafkaConsumer sets `self.events` before `subscribe([topic], on_assign=..., on_revoke=..., on_lost=...)`.
     - The docstring was updated.
   - **src/etf_risk/jobs/cli.py**: imports FAULT_FILE_ENV, fault_from_environment and code_identity.
     - submit logs `events.log("started", code=code_identity())`.
     - The worker's started event adds `code=code_identity(), fault_file=os.environ.get(FAULT_FILE_ENV)`.
     - `Worker(..., fault=fault_from_environment(events))`.
     - The reconciler's started event adds `code=code_identity()`.
     - The docstring was updated.
   - **src/etf_risk/jobs/crosscheck.sql** (new, generated): an attribution header, a dashes separator, then the doc's DDL and Q0–Q3b blocks joined by "\n", byte-identical to the doc.
   - **src/etf_risk/jobs/harness.py** (new, about 800 lines).
     - Constants: CASES, HOOKS, MID_STEP=(W3, W6, W7, K1, D1), NO_NEW_ATTEMPT, FROM_RESTORED, WORKERS=(A, B), CROSSCHECK_SQL, `_SEPARATOR`, `_QUERY_NAME`.
     - Settings (frozen dataclass): snapshot, kind="calendar-year", stride 21, max_attempts 3, jobs_per_case 3, cases, timing=(), slowest_steps_s 35.1, deadline_margin 2.0, deadline_round_s 5, max_lag_s 1, phase_delay_s 3, w7_stop_s 90, outage_s 30, flag 0.90, stop 0.95, poll_s 0.5, phase_timeout_s 300. `from_dict` validates names and cases.
     - Pure functions: timing_of, plan_jobs (seeded shuffle), deadline_reference, bound_to_next_run, deadline_seconds, make_plan.
     - Estimator: Assumptions, case_seconds, estimate.
     - Record helpers: events_named, owner(logs, alive) (resets on "started"; None if 0 or 2 holders), worker_accepts, PeakBook (add, batch_peak, incomplete), memory_verdict, crosscheck_statements (names DDL ×3, Q0, Q1, Q2, Q2b, Q3a, Q3b), fingerprint_from_export, csv_value, clock_pair.
     - Runtime: PhaseMissed; Tracker thread (observes at terminal status or at the deadline, then follows until terminal or drain); Batch class.
     - Batch methods:
       - per-thread store() via threading.local;
       - common_args, cli, compose, wait_ready, services_up (ps -a -q must be empty), read_peaks;
       - start with a same-clock check (_check_start);
       - fault_file, start_worker, alive, worker_logs, current_owner, wait_owner, wait_joined, wait_for;
       - job_status, observe;
       - claim_of, attempt_dir, spark_running, fault_event, wait_fault (missed as soon as the other worker claims), at_mid_step;
       - submit, publish_again, stop_tree, inject, inject_stop;
       - run_job (arming, K2 start-on-failure, deadline logged with t_submit, X1 second publish) and after_job (restart rule, wait_joined, peaks);
       - reference_run (via the launcher, with the harness as parent and a handshake line);
       - quiesce, _marked, crosscheck (temp tables, executemany, consistent snapshot, CSVs), q0, final_snapshot, run (try/except per job; final steps guarded; finally kill procs and `down -v`).
     - Logged events: job_not_submitted, published_again.
     - CLI subcommands: plan, estimate, batch.
   - **analysis/collect_recovery_measurements.py** (new).
     - BatchFolder reads harness.jsonl, worker logs, reconciler logs, submit.jsonl, plan.json, crosscheck CSVs (NULL → None), the export and the store_id.
     - Functions: step_intervals (currently UTC; must switch to mono), overlap_verdict (unknown if any missing), job_metrics (detection rules per case, rerun, finish, overhead against the C0 median, executions, complete executions via manifest.json, fenced events, wasted_step_time), identity_check (harness, process_started, submit started, step_started), clock_check(tolerance), accepted_checks (digest, result rule via pipeline.TABLES/total_violations, compare_tables via the caching collector), input_check(b, processed_root), collect(folder, clock_tolerance_s=1.0, processed_root=...), tally (all verdict columns with zeros), write (injections.csv, tally.csv, validity.json), main (with `--processed-root`; exits 1 on validity failure).
     - Pending gap: when no injection time exists, job_metrics should return "unknown: no injection time" instead of a blank.
   - **Tests written**:
     - tests/test_jobs_faults.py: 6 functions; the first test was fixed to `read_events(log) == []`.
     - tests/test_jobs_harness.py: 11 functions, including the deadline values, crosscheck byte-identity against the doc, the estimate (1403 / 4389), owner and PeakBook.
     - tests/test_recovery_collector.py: 6 functions, built on a synthetic `make_batch` (jobs C0, W3, W5a, K2-not-run; W3 expected detection 55, rerun 60, finish 105, overhead 85, wasted 19).
     - Edits:
       - test_jobs_worker.py: order now includes after_accept_commit; new W5a test using EventLog with no accepted event.
       - test_jobs_queue.py: the lost count covers after_accept_commit.
       - test_jobs_kafka.py: offline log_assignment test, plus a live needs_kafka assignment test.
       - test_jobs_cli.py: submit's events are [started, submitted] and code == code_identity().
       - test_jobs_pipeline.py: step_started carries source_identity().
       - test_provenance.py: two identity tests.
   - **Docs**:
     - docs/recovery-experiments.md (565 lines; revision 4): 1.1 fourth review; 2.2, 2.3 and 2.4 marked "implemented, not yet run"; 4.2 adds 'restored'; 4.3 observation at completion; 8.1 the 84-job estimate; 8.2 P3 reassessed with its table; 8.4 P5 as a fault file; 8.5 still open; section 9 tooling list and attribution; history entry for revision 4.
     - docs/recovery-sql.md: an added "Accepted" bullet; the SQL blocks are unchanged.
     - docs/spec.md §11: an authorship sentence added for the tooling.
   - **Read for context**:
     - simulated.py: SimulatedPipeline(steps, fail_at, on_step) writes steps.log and result.json, returns folder_digest, and has no fence_at; MemoryQueue has publisher(outcomes), consumer(group) with poll/commit/rewind/close, and the PublishOutcome values CONFIRMED, UNCONFIRMED and DROPPED; ManualClock; SimulatedCrash (a BaseException).
     - launcher.py run(): sets step_started_at_utc after Popen and tree_ended_at_utc after the tree ends. Monotonic fields still need to be added.
   - **Scratchpad** /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/fixture/: expected/*.tsv (frozen), markdown/*.md, kit/, run.sh (DOC defaults to recovery-sql.md), wait-release.sh.

4. Errors and fixes:
   - zsh `$B:s…` and `$C:t…` modifiers broke `git show` paths; fixed by using `${B}:` braces or literal strings.
   - A sed range command failed on macOS; worked around.
   - Fixture renewals extraction: the regex missed the final `);` row and aligned spacing; fixed with `[[:space:]]+` and `[,;]?`.
   - The fixture run aborted twice because of the other session's tests. This was correct behaviour: nothing was started.
   - Harness self-review fixed 8 defects:
     - a shared PyMySQL connection across threads (now per-thread stores);
     - ps without -a;
     - K2 left Kafka stopped when its submit failed;
     - a stale owner was read before the join (now wait_joined);
     - the wrong-worker claim was only caught by the 300 s timeout (now immediate);
     - a quiesce timeout crashed instead of being recorded;
     - a job error skipped the final steps;
     - X1's publish error was uncaught.
   - Collector gaps fixed: submit identity; processed_root as a parameter (a monkeypatched REPO doesn't affect default arguments); invariant_violations outcome.
   - "Counts, not rates" was mislabelled as decided; relabelled as a proposal.
   - test_jobs_faults: an EventLog file exists at construction; the assertion was fixed.
   - User feedback incorporated: remove inferred restart durations; owner never from client.id; keep the expected rows frozen; do not broadcast messages to unidentified sessions (I chose to ask instead).

5. Problem Solving:
   - Solved: the frozen-SQL identity (hash reproduced; crosscheck.sql body equals the doc); doc links and references verified; the M2 worktree never modified by me (read-only, lock-free checks); the M2 a3a767b commit has no overlap with my files.
   - Current test status after setup: 123 passed, 1 failed (fixed but not yet re-run), 11 skipped (services).
   - Finding to fix now (approved policy, worker-pipeline.md): "never starts a step or accepts after F". handle() calls accept_result without checking F.

6. All user messages:
   - Msg 1: "While M2 validation runs, draft the E1/E2 recovery experiment outline in a separate worktree. Cover failure cases, metrics, correctness checks and a draft SQL cross-check for accepted results per job. Leave repetitions, deadlines and memory thresholds as explicit decisions pending M2's final report. Only read and draft files. Do not run tests, Spark, Docker, install dependencies or modify the M2 worktree. Keep authorship accurate and present the draft for my review."
   - Msg 2: the 7 review points (deadlines explicit, on-time/late/unfinished, later success must not erase a miss; separate DB acceptance correctness from event-log completeness, cover a crash after the commit before the event, repeated reports are not multiple accepted results; no successful-attempt artifacts from crashed attempts, record code identity at launch, missing intervals unknown; same-host monotonic timestamps, recovery latency n/a after acceptance; Kafka assignment conditions and a fixed worker startup order; full report identity incl. store_id and worker_id; define the deadline observation, quiescence and consistent SQL/export snapshot), plus "Use the host lock for reference runs. Remove the pooled rule-of-three claim unless its assumptions are justified. Add small SQL fixtures for late completion, missing acceptance events, duplicate reports and wrong-worker reports. Keep all cases and failed outcomes visible. Revise documents only for now; do not run formal experiments."
   - Msg 3: "M2's functional validation has finished. Use commit 6d8a232 and its final report as the current design inputs, while keeping the isolated memory-budget check marked pending. Proceed with these draft corrections: Record container peaks before every injected restart and retain the maximum across all segments. Identify the actual partition owner from assignment events; do not rely on client.id ordering. Keep 'deadline not observed' as an explicit unknown outcome when observation fails. You may now run the SQL fixtures against a scratch MySQL database, after confirming no other session's tests are running. Compare actual rows with explicit expected results and add fixtures for the currently uncovered verdicts. Revise the draft and report SQL results and remaining decisions together. Do not run formal experiments or treat Part A as approved."
   - Msg: "continue"
   - Msg 4, first paste (meant for the M2 session; interrupted; not acted on): correct the 420 figure to 463 passed with 10 skipped; commit and push; hand over the test window; do not merge yet.
   - Msg 4, second paste: "Once the M2 session confirms the test window is released, run the prepared fixtures against scratch MySQL. Recheck immediately before startup and clean up only your own container. Keep the expected rows frozen. Compare all actual rows with the 82 expected rows, report every mismatch, and explain any proposed correction rather than adjusting expectations merely to match the output. Remove the inferred 4–12-second MySQL downtime: failed-renewal counts alone do not establish restart duration. After validation, shorten the main outline and keep detailed SQL fixtures in an appendix or separate file. Propose a small set of Part A decisions with reasons, clearly marked as proposals. Do not run formal experiments or mark Part A approved."
   - Msg 5: "The 82-row SQL fixture validation is accepted as tooling evidence, not as approval of Part A. Proceed with the harness, collector, assignment events, launch-time code identity and precise fault-injection hooks. Claude Code writes this tooling, with accurate attribution. Preserve the frozen SQL expectations. Reassess deadline formulas and estimate the complete duration of all 84 proposed jobs. Keep timing, repetitions and memory thresholds provisional. Coordinate with the M2 session before any test or container run. Do not run formal experiments. Report progress and the remaining Part A decisions together."
   - Msg 6 (latest): quoted verbatim in section 1.
   - Standing constraints:
     - Never print memory files, .git/info/exclude or app lists in tool calls.
     - Do not modify the M2 worktree.
     - Do not start Docker or live tests (current).
     - No formal experiments; do not mark Part A approved or change Part A decisions without approval.
     - Keep the expected rows frozen (the frozen SQL must keep reproducing hash 447ef025…).
     - Keep the isolated memory-budget check pending.
     - Report findings before fixing out-of-scope items.
     - The author commits, pushes and merges (no commits by me without being asked).

7. Pending Tasks:
   - Fix the acceptance-deadline discrepancy in worker.handle(): before the first accept_result call, if the pipeline's `fence_at` is set and `time.monotonic() >= fence_at`, log `fenced` (during="acceptance") and return Result.FENCED without calling accept_result. Update the docstring and docs (the D2 path).
   - Add monotonic launcher timestamps: `step_started_mono` and `tree_ended_mono` in launcher.py's result, next to the UTC fields. Update the docstring. Add a test in test_jobs_launcher.py. Change the collector's step_intervals and wasted_step_time to use mono, treating records without mono as missing (unknown). Update the collector tests' launcher() helper and add a missing-mono case.
   - Add deterministic coverage:
     - (a) The first acceptance call after F: worker test with a pipeline whose fence_at is in the past → FENCED, accept_result never called, job still running, a later attempt accepted. Also a D2-like FaultFile hold released after F.
     - (b) Fault arming without changing partition ownership: refactor arming into a Batch method; test that the owner is unchanged, no restart happens, and only the owner's file is armed; Worker-level arming after construction fires; wait_fault misses when the other worker claims.
     - (c) Missing crash records and unknown observations: collector "unknown: no injection time"; missing launcher records; Tracker test with a fake batch (observation at completion, at the deadline, a failed observation with status None).
     - (d) Late completion and all frozen SQL verdicts: SQLite translation of the frozen crosscheck.sql plus doc fixtures A and B (translate @vars and REPEAT, skip SET) against the expected rows parsed from docs/recovery-sql.md §4 (c×64 expanded), covering all verdicts including late; plus the Tracker late path.
   - Re-run all new and affected tests (including test_jobs_launcher and possibly the full offline suite); fix failures.
   - Build and run a synthetic end-to-end harness and collector test without services. Planned approach: a SyntheticBatch subclass overriding environment methods, with in-process Worker/Reconciler on SQLite, MemoryQueue with assignment events logged by wrappers, SimulatedPipeline, FaultFile hooks with kill replaced by SimulatedCrash, the SQLite-translated crosscheck, and the in-process export. Then run the collector and assert the metrics, tally and validity. List the cases not covered synthetically (e.g., W6/W7 stops, K/D service cases).
   - Propose a smaller formal experiment that keeps the main safety and recovery questions, with an estimated runtime computed using the harness estimator's formulas, keeping the 84-job design as the alternative. Do not change the P1–P5 decisions.
   - Report actual results (test counts and outputs) and remaining gaps together. Update the memory note.

8. Current Work:
   I was starting on the latest user message. Completed so far:
   - data symlink created; `uv sync --group jobs` done;
   - first test run: "1 failed, 123 passed, 11 skipped in 30.21s";
   - fixed the test_jobs_faults assertion to `assert kills == [] and read_events(log) == []`.

   I had just read simulated.py in full (SimulatedPipeline lines 46–78, MemoryQueue lines 87–146) to design the synthetic E2E runtime, and confirmed that SimulatedPipeline has no `fence_at`, so the planned F check `getattr(self.pipeline, "fence_at", None)` won't affect the existing simulated tests. The planned worker change in handle():
   ```python
   self._fault("after_pipeline")
   deadline = getattr(self.pipeline, "fence_at", None)
   if deadline is not None and time.monotonic() >= deadline:
       self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="acceptance",
                       why="the deadline passed before acceptance")
       return Handled(job_id, Result.FENCED, claim=claim)
   if not self._until_deadline(lambda: self.store.accept_result(claim, digest), claim, "accept_result"):
       ...
   ```

9. Optional Next Step:
   Implement the acceptance-deadline fix in src/etf_risk/jobs/worker.py (the check above) with its deterministic worker tests. Then add the monotonic launcher timestamps (launcher.py result fields `step_started_mono` / `tree_ended_mono`, a test in test_jobs_launcher.py, and the collector switched to mono intervals). Then re-run the affected offline tests, as the user directed: "Run the new and affected tests, fix failures, and add deterministic coverage for: the first acceptance call after deadline F; fault arming without changing partition ownership; missing crash records and unknown observations; late completion and all frozen SQL verdicts. Fix the acceptance-deadline discrepancy consistently with the approved policy. Add monotonic launcher timestamps and use them for same-host overlap checks." After that, build the synthetic end-to-end harness/collector test without services, propose the smaller formal experiment with its estimated runtime, and report actual results and remaining gaps together. No Docker, no live tests, no formal experiments, and no Part A changes.

If you need specific details from before compaction (like exact code snippets, error messages, or content you generated), read the full transcript at: ~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9.jsonl
Continue the conversation from where it left off without asking the user any further questions. Resume directly — do not acknowledge the summary, do not recap what was happening, do not preface with "I'll continue" or similar. Pick up the last task as if the break never happened.

The messages after this summary are the most recent messages from before compaction, kept verbatim. The summary was written without seeing them, so something it says has not happened yet may already have happened in them.

## 2. Assistant — 2026-10-24T07:19:57.545Z

### Tool call: Bash

```
{
  "command": "git status --short | head -40 && wc -l src/etf_risk/jobs/worker.py src/etf_risk/jobs/launcher.py src/etf_risk/jobs/harness.py analysis/collect_recovery_measurements.py tests/test_jobs_worker.py tests/test_jobs_launcher.py tests/test_jobs_harness.py tests/test_recovery_collector.py",
  "description": "Show worktree changes and file sizes"
}
```

## 3. User — 2026-10-24T07:19:58.442Z

### Tool result

```
 M docs/spec.md
 M src/etf_risk/jobs/cli.py
 M src/etf_risk/jobs/kafka.py
 M src/etf_risk/jobs/pipeline.py
 M src/etf_risk/jobs/worker.py
 M src/etf_risk/provenance.py
 M tests/test_jobs_cli.py
 M tests/test_jobs_kafka.py
 M tests/test_jobs_pipeline.py
 M tests/test_jobs_queue.py
 M tests/test_jobs_worker.py
 M tests/test_provenance.py
?? analysis/collect_recovery_measurements.py
?? docs/recovery-experiments.md
?? docs/recovery-sql.md
?? src/etf_risk/jobs/crosscheck.sql
?? src/etf_risk/jobs/faults.py
?? src/etf_risk/jobs/harness.py
?? tests/test_jobs_faults.py
?? tests/test_jobs_harness.py
?? tests/test_recovery_collector.py
     271 src/etf_risk/jobs/worker.py
     309 src/etf_risk/jobs/launcher.py
     997 src/etf_risk/jobs/harness.py
     454 analysis/collect_recovery_measurements.py
     329 tests/test_jobs_worker.py
     298 tests/test_jobs_launcher.py
     126 tests/test_jobs_harness.py
     213 tests/test_recovery_collector.py
    2997 total
```

## 4. Assistant — 2026-10-24T07:20:01.449Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py"
}
```

## 5. User — 2026-10-24T07:20:01.574Z

### Tool result

```
1	"""A worker that handles one delivered job id at a time, fenced by its attempt token.
2	
3	Worker.handle(job_id, acknowledge) handles one delivery:
4	1. claim the job (JobStore.claim);
5	2. acknowledge the delivery (with Kafka: commit its offset), at once if the claim was
6	   refused, since the job needs nothing more, or after a successful claim and before the
7	   run; a worker that dies before acknowledging gets the job delivered again (spec §11);
8	3. run the pipeline in the attempt's own new folder, <output root>/<run id>, renewing the
9	   lease whenever the pipeline calls its heartbeat;
10	4. accept the result with the run digest the pipeline returns (etf_risk.runs), or record the
11	   failure.
12	A worker whose renewal, acceptance or failure write is refused has been fenced off: it
13	stops and writes nothing more. Its folder stays on disk and is never referenced. After a
14	lost database connection, acceptance and the failure write are tried again until the
15	pipeline's own deadline (fence_at), if it keeps one; both are safe to repeat (store.py).
16	Events (claimed, refused, accepted, fenced, failed, requeued, ...) go to an EventLog.
17	
18	Worker.serve(consumer) polls deliveries and hands each to handle(), acknowledging with a
19	synchronous commit of the message's offset. A message that carries no valid job id (as
20	queue.Delivery.job_id() reads it) is committed and skipped before anything touches the
21	database, so it cannot block the partition or stop the worker. An error before the acknowledgement rewinds the
22	consumer to the message and tries again after a delay, since an uncommitted message reaches
23	the same consumer again only that way. After DELIVERY_RETRIES such tries in a row, the next
24	error is raised and ends serve(). The message stays uncommitted and the consumer rewound, so
25	it is read again; it is never skipped, because its job may have a recorded publication, which
26	the reconciler does not publish again. An error after the acknowledgement is logged and left
27	to the lease. A commit that fails is logged and the job goes on: it is claimed, so a later
28	delivery of the same message is refused.
29	
30	Retries after acknowledgement. Once a delivery is acknowledged, no delivery is pending for
31	the job. A job that fail_attempt() returned to queued, and a running job whose worker died
32	after acknowledging, run again only when a new delivery arrives: the reconciler publishes
33	them (etf_risk.jobs.reconciler).
34	
35	Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash
36	there to model the worker process dying, and the worker command arms one through
37	etf_risk.jobs.faults for the recovery experiments. after_accept_commit lies between the
38	acceptance's commit and its accepted event: a crash there leaves an accepted result that
39	the event log does not show.
40	
41	AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py,
42	tests/test_jobs_queue.py and tests/test_jobs_kafka.py, on SQLite and on MySQL 8.4.13.
43	"""
44	from __future__ import annotations
45	
46	import logging
47	import os
48	import secrets
49	import time
50	from collections.abc import Callable
51	from dataclasses import dataclass
52	from enum import StrEnum
53	from pathlib import Path
54	from typing import Any, Protocol
55	
56	from etf_risk.jobs.events import NO_EVENTS, EventLog
57	from etf_risk.jobs.queue import Consumer, Delivery
58	from etf_risk.jobs.store import Claim, JobStore, Refusal, Status
59	
60	log = logging.getLogger(__name__)
61	
62	WORKER_FAULT_POINTS = (
63	    "before_claim",
64	    "after_claim",       # claimed, not yet acknowledged
65	    "after_pipeline",    # outputs written, result not yet accepted
66	    "after_accept_commit",   # accepted in the table, the accepted event not yet written
67	    "after_accept",
68	)
69	DELIVERY_RETRIES = 5    # tries again of one message after errors before its acknowledgement, then raise
70	
71	
72	class Fenced(Exception):
73	    """The attempt's token no longer holds the job: another attempt took it over, or it ended."""
74	
75	
76	class PipelineError(Exception):
77	    """The pipeline failed; retryable=False when running it again cannot help."""
78	
79	    def __init__(self, message: str, *, retryable: bool = True):
80	        super().__init__(message)
81	        self.retryable = retryable
82	
83	
84	class Heartbeat:
85	    """heartbeat() renews the attempt's lease (JobStore.renew): False once the attempt has
86	    been fenced off. claimed_mono is the worker's time.monotonic() just before the claim;
87	    the lease cannot have started earlier, which gives a pipeline its first deadline."""
88	
89	    def __init__(self, store: JobStore, claim: Claim, claimed_mono: float):
90	        self.store, self.claim, self.claimed_mono = store, claim, claimed_mono
91	
92	    def __call__(self) -> bool:
93	        return self.store.renew(self.claim)
94	
95	
96	class Pipeline(Protocol):
97	    def run(self, claim: Claim, run_dir: Path, heartbeat: Heartbeat) -> str:
98	        """Write the attempt's outputs into run_dir, a new empty folder, and return the run
99	        digest of its result (etf_risk.runs), which acceptance records.
100	
101	        Call heartbeat() more often than the lease lasts. It renews the lease and returns
102	        False once the attempt has been fenced off: then stop at once and raise Fenced.
103	        Raise PipelineError when the run fails."""
104	
105	
106	class Result(StrEnum):
107	    ACCEPTED = "accepted"    # this delivery's attempt produced the job's accepted result
108	    SKIPPED = "skipped"      # the claim was refused: the job needed nothing (see reason)
109	    REQUEUED = "requeued"    # the attempt failed and the job is queued again, not delivered again
110	    FAILED = "failed"        # the attempt failed and so did the job
111	    FENCED = "fenced"        # another attempt holds the job, or it ended; this one wrote nothing more
112	
113	
114	@dataclass(frozen=True)
115	class Handled:
116	    job_id: int
117	    result: Result
118	    reason: Refusal | None = None    # when skipped
119	    claim: Claim | None = None       # when an attempt started
120	
121	
122	@dataclass
123	class Served:
124	    """What Worker.serve() did with the deliveries it polled."""
125	    handled: int = 0              # handle() returned, whatever its result
126	    malformed: int = 0            # no valid job id: committed and skipped
127	    rewound: int = 0              # failed before the acknowledgement: read again (within the retries)
128	    failed_after_ack: int = 0     # failed after it: left to the lease and the reconciler
129	    commit_failures: int = 0      # commits that raised; the job went on
130	
131	
132	class Worker:
133	    def __init__(self, store: JobStore, pipeline: Pipeline, output_root: str | Path, *,
134	                 worker_id: str | None = None, fault: Callable[[str], None] | None = None,
135	                 events: EventLog = NO_EVENTS, sleep: Callable[[float], None] = time.sleep):
136	        self.store = store
137	        self.pipeline = pipeline
138	        self.output_root = Path(output_root)
139	        self.worker_id = worker_id or f"worker-{os.getpid()}-{secrets.token_hex(3)}"
140	        self._fault = fault or (lambda point: None)
141	        self.events = events
142	        self._sleep = sleep
143	
144	    def handle(self, job_id: int, acknowledge: Callable[[], None]) -> Handled:
145	        self._fault("before_claim")
146	        claimed_mono = time.monotonic()
147	        claim = self.store.claim(job_id, self.worker_id, self.output_root)
148	        if isinstance(claim, Refusal):
149	            self.events.log("refused", job_id=job_id, reason=claim.value)
150	            acknowledge()
151	            return Handled(job_id, Result.SKIPPED, reason=claim)
152	        self.events.log("claimed", job_id=job_id, attempt=claim.attempt_number, run_id=claim.run_id)
153	        self._fault("after_claim")
154	        acknowledge()
155	        try:
156	            claim.output_dir.mkdir(parents=True, exist_ok=False)
157	        except FileExistsError:
158	            # Run ids are unique within one job table, so this folder comes from elsewhere,
159	            # for example a job table created anew: never write into it.
160	            return self._failed(claim, f"output folder already exists: {claim.output_dir}", retryable=False)
161	        except OSError as error:
162	            return self._failed(claim, f"cannot create the output folder: {error}", retryable=True)
163	        try:
164	            digest = self.pipeline.run(claim, claim.output_dir, Heartbeat(self.store, claim, claimed_mono))
165	        except Fenced as fenced:
166	            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="pipeline", why=str(fenced))
167	            return Handled(job_id, Result.FENCED, claim=claim)
168	        except PipelineError as error:
169	            return self._failed(claim, str(error), retryable=error.retryable)
170	        except Exception as error:
171	            # Not a failure the pipeline reported: recorded with its type, and retried like one.
172	            return self._failed(claim, f"{type(error).__name__}: {error}", retryable=True)
173	        self._fault("after_pipeline")
174	        if not self._until_deadline(lambda: self.store.accept_result(claim, digest), claim, "accept_result"):
175	            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="accept_result")
176	            return Handled(job_id, Result.FENCED, claim=claim)
177	        self._fault("after_accept_commit")
178	        self.events.log("accepted", job_id=job_id, attempt=claim.attempt_number, digest=digest)
179	        self._fault("after_accept")
180	        return Handled(job_id, Result.ACCEPTED, claim=claim)
181	
182	    def _until_deadline(self, operation: Callable[[], Any], claim: Claim, name: str) -> Any:
183	        """operation(), tried again after a lost connection while the pipeline's deadline
184	        (fence_at, time.monotonic()) has not passed; any other error, or no deadline, raises."""
185	        while True:
186	            try:
187	                return operation()
188	            except Exception as error:
189	                deadline = getattr(self.pipeline, "fence_at", None)
190	                if deadline is None or time.monotonic() >= deadline or not self.store.dialect.is_disconnect(error):
191	                    raise
192	                self.events.log("retry", job_id=claim.job_id, attempt=claim.attempt_number, operation=name,
193	                                error=f"{type(error).__name__}: {error}")
194	                self._sleep(1.0)
195	
196	    def serve(self, consumer: Consumer, *, stop: Callable[[], bool] = lambda: False, stop_when_idle: bool = False,
197	              poll_timeout: float = 1.0, retry_delay: float = 1.0, retries: int = DELIVERY_RETRIES,
198	              on_handled: Callable[[Handled], None] | None = None,
199	              sleep: Callable[[float], None] = time.sleep) -> Served:
200	        """Handle deliveries one at a time until stop() is true (checked before each poll)
201	        or, with stop_when_idle, until a poll returns nothing. One message is tried again
202	        after errors before its acknowledgement at most `retries` times in a row; the next
203	        such error is raised, with the message uncommitted and the consumer rewound to it.
204	        BaseException, such as a simulated crash, ends serve() at once, with nothing more
205	        acknowledged."""
206	        served = Served()
207	        failing, failures = None, 0       # the position that last failed before acknowledgement, how often in a row
208	        while not stop():
209	            delivery = consumer.poll(poll_timeout)
210	            if delivery is None:
211	                if stop_when_idle:
212	                    break
213	                continue
214	            job_id = delivery.job_id()
215	            if job_id is None:
216	                log.warning("skipping a message with no valid job id at %r (%d bytes): %r", delivery.position,
217	                            len(delivery.value), delivery.value[:64])
218	                self.events.log("malformed", position=repr(delivery.position), size=len(delivery.value))
219	                served.malformed += 1
220	                self._commit(consumer, delivery, served)
221	                continue
222	            self.events.log("delivered", job_id=job_id, position=repr(delivery.position))
223	            acknowledged = False
224	
225	            def acknowledge() -> None:
226	                nonlocal acknowledged
227	                acknowledged = True
228	                self._commit(consumer, delivery, served)
229	
230	            try:
231	                handled = self.handle(job_id, acknowledge)
232	            except Exception:
233	                if acknowledged:
234	                    log.exception("job %s failed after its delivery was acknowledged; its lease will expire", job_id)
235	                    self.events.log("failed_after_ack", job_id=job_id)
236	                    served.failed_after_ack += 1
237	                    continue
238	                failures = failures + 1 if delivery.position == failing else 1
239	                failing = delivery.position
240	                consumer.rewind(delivery)         # read again, by this consumer or after a restart: never skipped
241	                if failures > retries:
242	                    log.error("job %s: %d errors in a row before its delivery was acknowledged; giving up,"
243	                              " with the message uncommitted", job_id, failures)
244	                    self.events.log("gave_up", job_id=job_id, failures=failures)
245	                    raise
246	                log.exception("job %s failed before its delivery was acknowledged; reading it again", job_id)
247	                self.events.log("rewound", job_id=job_id, failures=failures)
248	                served.rewound += 1
249	                sleep(retry_delay)
250	                continue
251	            served.handled += 1
252	            if on_handled is not None:
253	                on_handled(handled)
254	        return served
255	
256	    def _commit(self, consumer: Consumer, delivery: Delivery, served: Served) -> None:
257	        try:
258	            consumer.commit(delivery)
259	        except Exception as error:
260	            served.commit_failures += 1
261	            self.events.log("commit_failed", position=repr(delivery.position), error=f"{type(error).__name__}: {error}")
262	            log.warning("could not commit the offset of %r; a later delivery of it is refused by the claim",
263	                        delivery.position, exc_info=True)
264	
265	    def _failed(self, claim: Claim, error: str, *, retryable: bool) -> Handled:
266	        status = self._until_deadline(lambda: self.store.fail_attempt(claim, error, retryable=retryable),
267	                                      claim, "fail_attempt")
268	        result = {None: Result.FENCED, Status.QUEUED: Result.REQUEUED, Status.FAILED: Result.FAILED}[status]
269	        self.events.log(result.value, job_id=claim.job_id, attempt=claim.attempt_number, retryable=retryable,
270	                        error=error[-2000:])
271	        return Handled(claim.job_id, result, claim=claim)
272	
```

## 6. Assistant — 2026-10-24T07:20:02.029Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py"
}
```

## 7. User — 2026-10-24T07:20:02.147Z

### Tool result

```
1	"""The watchdog that runs one pipeline step for the worker (spec §11; docs/job-queue.md).
2	
3	    python -m etf_risk.jobs.launcher --marker M --lock PATH --registry DIR --lock-wait S \\
4	        --step-limit S --cwd DIR --step-log PATH --result PATH -- <command ...>
5	
6	The worker starts it with start_new_session=True, so the launcher leads a session that holds
7	the whole step (etf_risk.jobs.processes), with an environment the worker prepared (including
8	the attempt's marker), and with a pipe as stdin.
9	
10	The worker writes one JSON line per message:
11	- first the handshake {"monotonic": t, "seq": 0, "deadline": F}, where t is the worker's
12	  time.monotonic() when it wrote the line;
13	- then {"seq": n, "deadline": F_n} after each successful renewal of the lease.
14	Deadlines are absolute values of the host's monotonic clock, never durations.
15	
16	The launcher refuses to start in three cases:
17	- no handshake: none arrived within 5 s;
18	- clock_mismatch: its own reading is not between t and t + 30 s, so the two processes do not
19	  read the same clock. A different clock source differs by far more. The 30 s allow for a
20	  launcher that starts slowly on a busy machine; the deadlines stay absolute either way;
21	- deadline_passed: F has passed.
22	
23	Every tick (--tick, 0.5 s) the launcher does, in this order:
24	1. if its deadline has passed, it fires: it ends the tree, and firing is terminal;
25	2. only otherwise does it read the lines waiting on stdin. A line moves the deadline only if
26	   its sequence number is newer, its deadline is later than the current one, and that
27	   deadline is still in the future.
28	So lines that queued up while the launcher was stopped can never revive an expired watchdog,
29	and no line can push the deadline past what the worker granted. EOF (the worker closed the
30	pipe, or died) ends the tree too, and so does the step's time limit, or a SIGTERM to the
31	launcher itself.
32	
33	Before the step starts, the launcher takes an exclusive flock on the host's execution lock,
34	waiting up to --lock-wait. It then waits, within the same bound, until no process of another
35	launcher's tree survives (the registry). While it waits it keeps reading deadlines and fires
36	if its own passes. Only then does it register and start the step. The step's driver
37	inherits the lock's descriptor, so the lock is held while the launcher or the driver lives.
38	PySpark closes inherited descriptors before it starts the JVM, so the JVM does not hold the
39	lock; it exits when the driver's pipe breaks, and the next launcher's survivor check covers
40	that window.
41	
42	Ending the tree: SIGTERM to every process of the session that carries the marker, SIGKILL
43	after --term-grace, and a rescan until none is left or --kill-confirm has passed. When the
44	step ends by itself, the launcher first gives the rest of its tree --drain seconds to exit.
45	
46	The result goes to --result as JSON: the outcome, the step's exit code, the processes ended,
47	the time waited for the lock, the tree's peak summed RSS, and the lines accepted and
48	ignored. The exit code says the outcome: the step's own code (0-63) when it ran to its end,
49	otherwise one of EXIT_CODES.
50	
51	AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_launcher.py.
52	"""
53	from __future__ import annotations
54	
55	import argparse
56	import fcntl
57	import json
58	import os
59	import select
60	import signal
61	import subprocess
62	import sys
63	import time
64	from datetime import datetime, timezone
65	from pathlib import Path
66	
67	from etf_risk.jobs import processes
68	
69	EXIT_CODES = {"deadline": 64, "eof": 65, "timeout": 66, "lock_busy": 67, "clock_mismatch": 68,
70	              "deadline_passed": 69, "signaled": 70, "launch_failed": 71, "no_handshake": 72, "terminated": 73}
71	HANDSHAKE_TIMEOUT = 5.0
72	CLOCK_TOLERANCE = 30.0     # seconds a launcher may take to read the handshake; never a reading from the future
73	
74	
75	class Watchdog:
76	    """The deadline: absolute, on the monotonic clock, moved only by newer, later, future
77	    lines; once fired it stays fired."""
78	
79	    def __init__(self, deadline: float, seq: int):
80	        self.deadline, self.seq = float(deadline), seq
81	        self.fired = False
82	        self.accepted = self.ignored = 0
83	
84	    def expired(self, now: float) -> bool:
85	        if not self.fired and now >= self.deadline:
86	            self.fired = True
87	        return self.fired
88	
89	    def offer(self, line: dict, now: float) -> bool:
90	        seq, deadline = line.get("seq"), line.get("deadline")
91	        if (self.fired or not isinstance(seq, int) or not isinstance(deadline, (int, float)) or seq <= self.seq
92	                or deadline <= self.deadline or deadline <= now):
93	            self.ignored += 1
94	            return False
95	        self.seq, self.deadline = seq, float(deadline)
96	        self.accepted += 1
97	        return True
98	
99	
100	class Lines:
101	    """The worker's lines on a non-blocking stdin."""
102	
103	    def __init__(self, fd: int):
104	        self.fd, self.buffer, self.eof = fd, b"", False
105	        os.set_blocking(fd, False)
106	
107	    def read(self) -> list[dict]:
108	        while not self.eof:
109	            try:
110	                chunk = os.read(self.fd, 65536)
111	            except BlockingIOError:
112	                break
113	            if not chunk:
114	                self.eof = True
115	            self.buffer += chunk
116	        *complete, self.buffer = self.buffer.split(b"\n")
117	        lines = []
118	        for raw in complete:
119	            try:
120	                value = json.loads(raw)
121	            except ValueError:
122	                continue
123	            if isinstance(value, dict):
124	                lines.append(value)
125	        return lines
126	
127	    def wait(self, timeout: float) -> None:
128	        if not self.eof and timeout > 0:
129	            select.select([self.fd], [], [], timeout)
130	
131	
132	class Launcher:
133	    def __init__(self, args: argparse.Namespace):
134	        self.args = args
135	        self.result: dict = {"outcome": None, "returncode": None, "pid": os.getpid(),
136	                             "started_at_utc": datetime.now(timezone.utc).isoformat(), "lock_wait_s": None,
137	                             "peak_rss_bytes": 0, "ended": None, "lingering": None}
138	        self.lines = Lines(sys.stdin.fileno())
139	        self.watchdog: Watchdog | None = None
140	        self.stop_requested = False
141	        self.registry = processes.Registry(args.registry)
142	        self.lock_fd: int | None = None
143	
144	    def members(self) -> list:
145	        return processes.attempt_members(os.getpid(), self.args.marker, exclude=[os.getpid()])
146	
147	    def poll(self) -> str | None:
148	        """One check of the watchdog, in the documented order; the reason to stop, if any."""
149	        now = time.monotonic()
150	        if self.watchdog.expired(now):
151	            for line in self.lines.read():              # read only to record them: a fired watchdog ignores all
152	                self.watchdog.offer(line, now)
153	            return "deadline"
154	        for line in self.lines.read():
155	            self.watchdog.offer(line, now)
156	        if self.lines.eof:
157	            return "eof"
158	        if self.stop_requested:
159	            return "terminated"
160	        return None
161	
162	    def handshake(self) -> str | None:
163	        deadline = time.monotonic() + HANDSHAKE_TIMEOUT
164	        while time.monotonic() < deadline:
165	            lines = self.lines.read()
166	            if lines:
167	                first, now = lines[0], time.monotonic()
168	                if not isinstance(first.get("monotonic"), (int, float)) or not isinstance(first.get("deadline"), (int, float)):
169	                    return "no_handshake"
170	                if not (first["monotonic"] <= now <= first["monotonic"] + CLOCK_TOLERANCE):
171	                    self.result["clock"] = {"worker": first["monotonic"], "launcher": now}
172	                    return "clock_mismatch"
173	                self.watchdog = Watchdog(first["deadline"], int(first.get("seq", 0)))
174	                if self.watchdog.expired(now):
175	                    return "deadline_passed"
176	                for line in lines[1:]:                       # lines that came with the handshake
177	                    self.watchdog.offer(line, now)
178	                return None
179	            if self.lines.eof:
180	                return "no_handshake"
181	            self.lines.wait(0.1)
182	        return "no_handshake"
183	
184	    def acquire(self) -> str | None:
185	        """The host lock, then no survivors of other trees; waiting within --lock-wait."""
186	        start = time.monotonic()
187	        Path(self.args.lock).parent.mkdir(parents=True, exist_ok=True)
188	        fd = os.open(self.args.lock, os.O_RDWR | os.O_CREAT, 0o600)
189	        while True:
190	            try:
191	                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
192	                break
193	            except BlockingIOError:
194	                pass
195	            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
196	                os.close(fd)
197	                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
198	                return reason or "lock_busy"
199	            self.lines.wait(self.args.tick)
200	        self.lock_fd = fd
201	        while survivors := self.registry.survivors():
202	            self.result["survivors_seen"] = sorted({p.pid for p in survivors})
203	            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
204	                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
205	                return reason or "lock_busy"
206	            self.lines.wait(self.args.tick)
207	        self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
208	        return None
209	
210	    def end_tree(self, reason: str) -> None:
211	        self.result["ended"] = {"reason": reason, **processes.terminate(
212	            self.members(), term_grace=self.args.term_grace, kill_confirm=self.args.kill_confirm,
213	            rescan=self.members)}
214	
215	    def drain(self) -> None:
216	        """The step ended by itself: give the rest of its tree time to exit, then end it."""
217	        deadline = time.monotonic() + self.args.drain
218	        while (left := processes.alive(self.members())) and time.monotonic() < deadline:
219	            time.sleep(0.1)
220	        if left := processes.alive(self.members()):
221	            self.result["lingering"] = sorted(p.pid for p in left)
222	            self.end_tree("lingering after the step ended")
223	
224	    def run(self, command: list[str]) -> int:
225	        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "stop_requested", True))
226	        outcome = self.handshake() or self.acquire()
227	        child = None
228	        if outcome is None:
229	            self.registry.register(self.args.marker)
230	            Path(self.args.step_log).parent.mkdir(parents=True, exist_ok=True)
231	            os.set_inheritable(self.lock_fd, True)
232	            try:
233	                with open(self.args.step_log, "ab") as log:
234	                    child = subprocess.Popen(command, cwd=self.args.cwd, stdin=subprocess.DEVNULL, stdout=log,
235	                                             stderr=subprocess.STDOUT, pass_fds=(self.lock_fd,))
236	                self.result["step_started_at_utc"] = datetime.now(timezone.utc).isoformat()
237	            except OSError as error:
238	                self.result["error"] = f"{type(error).__name__}: {error}"
239	                outcome = "launch_failed"
240	        if child is not None:
241	            started = time.monotonic()
242	            while outcome is None:
243	                outcome = self.poll()
244	                if outcome is None and child.poll() is not None:
245	                    outcome = "exited"
246	                elif outcome is None and time.monotonic() - started >= self.args.step_limit:
247	                    outcome = "timeout"
248	                if outcome is None:
249	                    self.result["peak_rss_bytes"] = max(self.result["peak_rss_bytes"], processes.rss(self.members()))
250	                    self.lines.wait(self.args.tick)
251	            self.result["step_seconds"] = round(time.monotonic() - started, 3)
252	            if outcome == "exited":
253	                self.drain()
254	            else:
255	                self.end_tree(outcome)
256	            child.wait()
257	            self.result["returncode"] = child.returncode
258	            self.result["tree_ended_at_utc"] = datetime.now(timezone.utc).isoformat()   # no member left
259	            if outcome == "exited" and child.returncode < 0:
260	                outcome = "signaled"
261	        self.registry.unregister()
262	        if self.lock_fd is not None:
263	            os.close(self.lock_fd)                      # the driver's copy is closed with the driver
264	        if self.watchdog is not None:
265	            self.result.update(deadline=self.watchdog.deadline, lines_accepted=self.watchdog.accepted,
266	                               lines_ignored=self.watchdog.ignored)
267	        self.result.update(outcome=outcome, finished_at_utc=datetime.now(timezone.utc).isoformat())
268	        tmp = Path(self.args.result).with_suffix(".tmp")
269	        tmp.parent.mkdir(parents=True, exist_ok=True)
270	        tmp.write_text(json.dumps(self.result, indent=2) + "\n")
271	        tmp.replace(self.args.result)
272	        if outcome == "exited":
273	            return child.returncode if 0 <= child.returncode < 64 else EXIT_CODES["signaled"]
274	        return EXIT_CODES[outcome]
275	
276	
277	def main(argv: list[str] | None = None) -> int:
278	    argv = sys.argv[1:] if argv is None else argv
279	    if "--" not in argv:
280	        print("usage: python -m etf_risk.jobs.launcher [options] -- <command ...>", file=sys.stderr)
281	        return 2
282	    split = argv.index("--")
283	    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs.launcher")
284	    parser.add_argument("--marker", required=True)
285	    parser.add_argument("--lock", required=True, help="the host's execution lock file")
286	    parser.add_argument("--registry", required=True, help="the folder of launchers whose trees may still run")
287	    parser.add_argument("--lock-wait", type=float, required=True)
288	    parser.add_argument("--step-limit", type=float, required=True)
289	    parser.add_argument("--cwd", required=True)
290	    parser.add_argument("--step-log", required=True)
291	    parser.add_argument("--result", required=True)
292	    parser.add_argument("--tick", type=float, default=0.5)
293	    parser.add_argument("--term-grace", type=float, default=5.0)
294	    parser.add_argument("--kill-confirm", type=float, default=2.0)
295	    parser.add_argument("--drain", type=float, default=10.0)
296	    args = parser.parse_args(argv[:split])
297	    command = argv[split + 1:]
298	    if not command:
299	        parser.error("no command after --")
300	    if processes.parse_marker(args.marker) is None or os.environ.get(processes.MARKER_ENV) != args.marker:
301	        parser.error("--marker must be a marker and equal ETF_RISK_ATTEMPT in the environment")
302	    if os.getsid(0) != os.getpid():
303	        parser.error("start the launcher as the leader of a new session (start_new_session=True):"
304	                     " its session is how it finds the step's processes")
305	    return Launcher(args).run(command)
306	
307	
308	if __name__ == "__main__":
309	    sys.exit(main())
310	
```

## 8. Assistant — 2026-10-24T07:20:07.396Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'fence_at|fence_margin|F[ ,.)]|after F|never (starts|accepts)' src/etf_risk/jobs/pipeline.py | head -40; echo ---; grep -rn -E 'after F|accepts after|never starts a step|fence_at' docs/*.md | head -30",
  "description": "Find the deadline F policy in pipeline code and docs"
}
```

## 9. User — 2026-10-24T07:20:08.178Z

### Tool result

```
24:deadline F = m0 + lease - fence_margin, on the monotonic clock (etf_risk.jobs.timing), where
25:m0 is the time just before the renewal started. The first F comes from the claim
34:- The worker renews before each step and before acceptance, so a fenced worker never starts
99:    """The attempt's lease, as the worker sees it: fence_at is the absolute monotonic deadline
105:        self.fence_at = None if claimed is None else claimed + timing.lease - timing.fence_margin
122:            self.fence_at = m0 + self.timing.lease - self.timing.fence_margin
130:        return self.fence_at is None or now >= self.fence_at
143:        self.fence_at: float | None = None          # the current attempt's deadline (Worker reads it)
151:        self.fence_at = renewer.fence_at
181:        self.fence_at = renewer.fence_at
219:            self.fence_at = renewer.fence_at
254:        self._send(fd, {"monotonic": time.monotonic(), "seq": renewer.seq, "deadline": renewer.fence_at})
268:                    self.fence_at = renewer.fence_at
270:                        self._send(fd, {"seq": renewer.seq, "deadline": renewer.fence_at})
280:                # The launcher did not act on the EOF (it is stopped, perhaps): end the tree here.
---
docs/worker-pipeline.md:116:fences itself once F passes without a renewal, and never starts a step or accepts after F.
```

## 10. Assistant — 2026-10-24T07:20:13.321Z

### Tool call: Bash

```
{
  "command": "sed -n 1,60p src/etf_risk/jobs/pipeline.py && echo ---- && sed -n 95,230p src/etf_risk/jobs/pipeline.py && echo ---- && sed -n 100,135p docs/worker-pipeline.md",
  "description": "Read pipeline deadline logic and worker-pipeline policy"
}
```

## 11. User — 2026-10-24T07:20:14.049Z

### Tool result

```
"""The real pipeline in the worker: windows → spark_pipeline → verify for one claimed job, each
step run by a launcher (spec §11; docs/job-queue.md, "The real pipeline").

Steps. Each step is `<python> -m etf_risk.<module>` with absolute paths only, and everything it
writes lands in the attempt's folder:
1. windows --out-root <run dir>/windows --name <name>, from the snapshot under the worker's
   processed-data root;
2. spark_pipeline --windows <run dir>/windows/<snapshot>/<name>
   --out-root <run dir>/output --run-id <run id>;
3. verify --run <run dir>/output/<snapshot>/<name>/<run id>.

The step's environment:
- It is built from an allowlist, so service URLs and passwords never reach it, and it
  carries the attempt's marker (etf_risk.jobs.processes).
- The working directory, TMPDIR and SPARK_LOCAL_DIRS point into <run dir>/.work.
  java.io.tmpdir does too, set through SPARK_SUBMIT_OPTS, since the macOS JDK ignores
  TMPDIR. It is never set through JAVA_TOOL_OPTIONS, whose "Picked up" notice would replace
  the Java version that run.json records.
- PYSPARK_PYTHON and PYSPARK_DRIVER_PYTHON name this interpreter; otherwise Spark's Python
  workers start whatever python3 comes first on PATH.

Renewals. The worker's thread waits on the launcher one tick (1 s) at a time and renews the
lease every renew_interval. After each successful renewal it sends the launcher the absolute
deadline F = m0 + lease - fence_margin, on the monotonic clock (etf_risk.jobs.timing), where
m0 is the time just before the renewal started. The first F comes from the claim
(Heartbeat.claimed_mono).
- A renewal that raises, because the database is out of reach, is tried again at the next
  interval.
- A refused renewal means the attempt was fenced off. So does a deadline that passed without
  a renewal: the worker fences itself. Either way, the worker closes the launcher's pipe and
  the launcher ends the tree.
- The launcher's watchdog acts without the worker. Safety (no overlapping Spark work) rests
  on it and on the host lock, not on how long the worker's database calls take.
- The worker renews before each step and before acceptance, so a fenced worker never starts
  a new step. If the launcher does not end within the kill grace after its pipe was closed
  (because it is stopped, for example), the worker ends the tree itself.

Acceptance. The run counts as a result only if all of the following hold:
- every step exited 0;
- run.json's status is ok;
- every count in checks.json is 0;
- verify.json reports no mismatch and the same breached windows;
- every table has its _SUCCESS file.
Then .work is removed, attempt.json is written (worker, steps, settings, code state), and
manifest.json records the run folder's manifest (etf_risk.runs). After a last renewal, run()
returns the run digest, and the worker accepts with it. Nothing in the folder changes after
acceptance.

Failures are classified from the records, not from exit codes alone, since an uncaught
exception exits with 1, as "checks failed" does:
- not retryable: a checksum error (exit 3); run.json status checks_failed; a verify
  mismatch; parameters or input checksums that do not fit;
- retryable: a signal; a time limit; status failed or a missing record; a busy host lock;
  a launcher that failed;
- fenced: a refused renewal, or a deadline that passed.

startup_sweep() is run by a starting worker. It ends the trees of attempts that are no longer
valid, keeps every valid active attempt's tree, and removes the scratch (.work) of attempts
that ended.

----
DEFAULT_LOCK = Path.home() / ".cache" / "etf-risk" / "locks" / "spark-exec.lock"


class Renewer:
    """The attempt's lease, as the worker sees it: fence_at is the absolute monotonic deadline
    given to the launcher, seq the number of the last successful renewal."""

    def __init__(self, heartbeat, timing: Timing, events: EventLog, claim: Claim):
        self.heartbeat, self.timing, self.events, self.claim = heartbeat, timing, events, claim
        claimed = getattr(heartbeat, "claimed_mono", None)
        self.fence_at = None if claimed is None else claimed + timing.lease - timing.fence_margin
        self.seq = 0
        self.last_attempt = float("-inf")

    def renew(self) -> bool | None:
        """True: renewed; False: refused (fenced off); None: the call failed."""
        m0 = time.monotonic()
        self.last_attempt = m0
        try:
            ok = self.heartbeat()
        except Exception as error:
            self.events.log("renewal_failed", job_id=self.claim.job_id, attempt=self.claim.attempt_number,
                            seconds=round(time.monotonic() - m0, 3), error=f"{type(error).__name__}: {error}"[:500])
            return None
        self.events.log("renewed" if ok else "renewal_refused", job_id=self.claim.job_id,
                        attempt=self.claim.attempt_number, seconds=round(time.monotonic() - m0, 3))
        if ok:
            self.fence_at = m0 + self.timing.lease - self.timing.fence_margin
            self.seq += 1
        return bool(ok)

    def due(self, now: float) -> bool:
        return now - self.last_attempt >= self.timing.renew_interval

    def passed(self, now: float) -> bool:
        return self.fence_at is None or now >= self.fence_at


class SubprocessPipeline:
    def __init__(self, *, store_id: str, processed_root: str | Path, worker_id: str,
                 lock_path: str | Path = DEFAULT_LOCK, registry: str | Path | None = None,
                 timing: Timing = DEFAULT_TIMING, events: EventLog = NO_EVENTS,
                 stop: threading.Event | None = None, python: str = sys.executable):
        self.store_id, self.worker_id = store_id, worker_id
        self.processed_root = Path(processed_root).resolve()
        self.lock_path = Path(lock_path)
        self.registry = Path(registry) if registry is not None else self.lock_path.parent / "registry"
        self.timing, self.events, self.stop, self.python = timing.check(), events, stop, python
        self.fence_at: float | None = None          # the current attempt's deadline (Worker reads it)

    # The run

    def run(self, claim: Claim, run_dir: Path, heartbeat) -> str:
        run_dir = Path(run_dir).resolve()
        started = datetime.now(timezone.utc).isoformat()
        renewer = Renewer(heartbeat, self.timing, self.events, claim)
        self.fence_at = renewer.fence_at
        try:
            params = JobParams.from_dict(claim.params)
            check_inputs(self.processed_root, params.snapshot, claim.input_checksums)
        except InvalidParams as error:
            raise PipelineError(f"{error}", retryable=False) from None
        work, logs = run_dir / ".work", run_dir / "logs"
        for folder in (work / "tmp", work / "spark", work / "jtmp", logs):
            folder.mkdir(parents=True, exist_ok=True)
        marker = processes.marker(self.store_id, claim.run_id, claim.token)
        env = self.step_env(work, marker)
        steps = []
        for name, argv in self.commands(params, claim, run_dir):
            self._renew_before(renewer, claim, before=name)
            step = self._run_step(name, argv, env, work, logs, renewer, marker, claim)
            steps.append(step)
            self._classify(step, run_dir, params, claim)
        run_folder = self.run_folder(params, claim, run_dir)
        self._check_result(run_folder)
        shutil.rmtree(work)
        record = {"format": 1, "worker_id": self.worker_id, "store_id": self.store_id, "job_id": claim.job_id,
                  "attempt_number": claim.attempt_number, "run_id": claim.run_id, "params": params.to_dict(),
                  "input_checksums_checked": claim.input_checksums, "processed_root": str(self.processed_root),
                  "run_folder": run_folder.relative_to(run_dir).as_posix(), "steps": steps,
                  "timing": asdict(self.timing), "code": code_state(), "started_at_utc": started,
                  "finished_at_utc": datetime.now(timezone.utc).isoformat()}
        (run_dir / "attempt.json").write_text(json.dumps(record, indent=2) + "\n")
        manifest = runs.manifest(run_folder)
        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        self._renew_before(renewer, claim, before="acceptance")
        self.fence_at = renewer.fence_at
        return runs.digest(manifest)

    def commands(self, params: JobParams, claim: Claim, run_dir: Path) -> list[tuple[str, list[str]]]:
        py, name = self.python, params.windows_name
        windows_dir = run_dir / "windows" / params.snapshot / name
        return [
            ("windows", [py, "-m", "etf_risk.windows", "--snapshot", params.snapshot,
                         "--processed-root", str(self.processed_root), "--kind", params.kind,
                         "--window-days", str(params.window_days), "--stride", str(params.stride),
                         "--anchor", params.anchor, "--out-root", str(run_dir / "windows"), "--name", name]),
            ("spark_pipeline", [py, "-m", "etf_risk.spark_pipeline", "--windows", str(windows_dir),
                                "--out-root", str(run_dir / "output"), "--run-id", claim.run_id]),
            ("verify", [py, "-m", "etf_risk.verify", "--run", str(self.run_folder(params, claim, run_dir)),
                        "--sample-ticker", params.sample_ticker]),
        ]

    @staticmethod
    def run_folder(params: JobParams, claim: Claim, run_dir: Path) -> Path:
        return run_dir / "output" / params.snapshot / params.windows_name / claim.run_id

    def step_env(self, work: Path, marker: str) -> dict[str, str]:
        env = {name: os.environ[name] for name in ENV_ALLOWED if name in os.environ}
        env["PATH"] = str(Path(self.python).parent) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin")
        env.update(TMPDIR=str(work / "tmp"), SPARK_LOCAL_DIRS=str(work / "spark"),
                   SPARK_SUBMIT_OPTS=f"-Djava.io.tmpdir={work / 'jtmp'} -XX:-UsePerfData",
                   PYSPARK_PYTHON=self.python, PYSPARK_DRIVER_PYTHON=self.python, PYTHONUNBUFFERED="1")
        env[processes.MARKER_ENV] = marker
        return env

    # Steps

    def _renew_before(self, renewer: Renewer, claim: Claim, *, before: str) -> None:
        """Renew the lease before a step or acceptance; Fenced if that cannot happen in time."""
        while True:
            if self.stop is not None and self.stop.is_set():
                raise PipelineError(f"the worker was stopped before {before}", retryable=True)
            ok = renewer.renew()
            self.fence_at = renewer.fence_at
            if ok:
                return
            if ok is False:
                raise Fenced(f"{claim.run_id}: the renewal before {before} was refused")
            if renewer.passed(time.monotonic()):
                raise Fenced(f"{claim.run_id}: no renewal before the deadline, before {before}")
            time.sleep(self.timing.worker_tick)

    def _send(self, fd: int, line: dict) -> bool:
        try:
            os.write(fd, (json.dumps(line) + "\n").encode())
----
  lease can expire, whatever the worker is doing: blocked in a database call, stopped or
  dead.
- The worker's own timeouts play no part in this: no time limit is claimed for a whole
  database operation.

On each tick the launcher:
1. checks whether its deadline has passed. If it has, it fires, and firing is terminal;
2. only otherwise reads the waiting lines. A line moves the deadline only if its sequence
   number is newer, its deadline is later, and that deadline is still in the future.

So lines that queued up while the launcher was stopped cannot revive an expired watchdog, and
no line can push the deadline past what the worker granted
(`test_stopped_past_its_deadline_…` and `test_stopped_briefly_…` in
[tests/test_jobs_launcher.py](../tests/test_jobs_launcher.py)).

The worker also checks F on every 1 s tick. It renews before each step and before acceptance,
fences itself once F passes without a renewal, and never starts a step or accepts after F.
Closing the pipe (EOF) makes the launcher end the tree. If the launcher does not act within
the kill grace plus 10 s, because it is stopped, the worker ends the tree itself.

## The host execution lock

Before a step starts, its launcher:
- takes an exclusive `flock` on the host's lock (`~/.cache/etf-risk/locks/spark-exec.lock`;
  tests use their own);
- waits until no process of another launcher's tree survives. A registry next to the lock has
  one file per launcher whose tree may still run, which also finds the orphans of a launcher
  that was killed.

Both waits are bounded together by the step limit + G + 30 s; after that the attempt fails as
retryable ("execution lock busy"). The step's driver inherits the lock. PySpark closes
inherited descriptors before it starts the JVM, and the JVM exits when the driver's pipe
breaks; the survivor check covers that window.

So no replacement Spark step starts while an earlier tree survives, even when the whole tree
is stopped (watchdog included) or the wall clock jumps. On this machine, steps run one at a
```

## 12. Assistant — 2026-10-24T07:20:23.849Z

### Tool call: Bash

```
{
  "command": "grep -n -A30 'def accept_result' src/etf_risk/jobs/store.py | head -60",
  "description": "Read the acceptance guard in the job store"
}
```

## 13. User — 2026-10-24T07:20:24.576Z

### Tool result

```
460:    def accept_result(self, claim: Claim, result_digest: str) -> bool:
461-        """Accept this attempt's result, whose files have the run digest result_digest
462-        (etf_risk.runs), recorded with the acceptance. True if it is the job's accepted
463-        result, now or already (a repeat, with the same token and digest, after a failed
464-        COMMIT that took effect); False: fenced off."""
465-        if not is_digest(result_digest):
466-            raise ValueError(f"not a run digest: {result_digest!r}")
467-        now = self._time(self.clock.now())
468-        with self._transaction():
469-            if self._execute(
470-                    "UPDATE jobs SET status = 'succeeded', accepted_attempt = :attempt_number,"
471-                    " attempt_token = NULL, lease_expires_at = NULL, finished_at = :now,"
472-                    " version = version + 1, updated_at = :now"
473-                    " WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token",
474-                    job_id=claim.job_id, token=claim.token, attempt_number=claim.attempt_number,
475-                    now=now).rowcount:
476-                self._fault("accept_result.jobs_updated")
477-                self._write_one("UPDATE job_attempts SET outcome = 'accepted', result_digest = :digest, ended_at = :now"
478-                                " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
479-                                job_id=claim.job_id, attempt_number=claim.attempt_number, digest=result_digest,
480-                                now=now)
481-                return True
482-            return self._fetch_one(
483-                "SELECT 1 FROM jobs j JOIN job_attempts a"
484-                " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt"
485-                " WHERE j.job_id = :job_id AND j.status = 'succeeded' AND a.attempt_token = :token"
486-                " AND a.result_digest = :digest",
487-                job_id=claim.job_id, token=claim.token, digest=result_digest) is not None
488-
489-    @_retry_conflicts
490-    def fail_attempt(self, claim: Claim, error: str, *, retryable: bool) -> Status | None:
```

## 14. Assistant — 2026-10-24T07:20:28.753Z

Status: I'm adding the acceptance-deadline check to the worker. Next come the monotonic launcher timestamps, then the tests.

## 15. Assistant — 2026-10-24T07:20:29.914Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'fence_at|class .*Pipeline|def test_|SimulatedCrash|Fenced' tests/test_jobs_worker.py | head -60",
  "description": "List worker tests and pipeline stubs"
}
```

## 16. User — 2026-10-24T07:20:30.622Z

### Tool result

```
19:from etf_risk.jobs.simulated import SimulatedCrash, SimulatedPipeline
41:            raise SimulatedCrash(point)
45:def test_a_delivery_runs_the_job_once_and_accepts_its_result(env):
58:def test_a_duplicate_delivery_after_success_is_skipped(env):
68:def test_a_duplicate_delivery_during_a_live_run_is_skipped(env):
84:def test_a_requeued_job_delivered_twice_is_claimed_once(env):
100:def test_concurrent_deliveries_of_one_job_run_it_once(env):
115:def test_a_crash_before_the_claim_leaves_the_job_queued(env):
117:    with pytest.raises(SimulatedCrash):
124:def test_a_crash_between_claim_and_acknowledgement(env):
126:    with pytest.raises(SimulatedCrash):
141:def test_a_crash_in_the_middle_of_the_run(env):
146:            raise SimulatedCrash("the worker died mid-run")
148:    with pytest.raises(SimulatedCrash):
157:def test_a_crash_after_the_pipeline_loses_only_that_attempt(env):
160:    with pytest.raises(SimulatedCrash):
170:def test_a_crash_after_acceptance_keeps_the_one_result(env):
172:    with pytest.raises(SimulatedCrash):
180:def test_a_crash_between_the_acceptance_commit_and_its_event_leaves_the_result_unreported(env, tmp_path):
185:    with pytest.raises(SimulatedCrash):
195:def test_an_expired_lease_mid_run_fences_the_slow_worker(env):
214:def test_an_expired_lease_without_a_takeover_lets_the_worker_finish(env):
225:def test_a_stale_worker_cannot_get_its_result_accepted(env):
242:def test_a_stale_worker_cannot_record_a_failure(env):
261:def test_a_retryable_failure_is_not_delivered_again_by_itself(env):
275:def test_retries_end_when_attempts_run_out(env):
287:def test_a_permanent_failure_fails_the_job(env):
296:def test_an_unexpected_pipeline_error_counts_as_a_retryable_failure(env):
307:def test_an_existing_output_folder_is_never_written_into(env):
319:def test_acknowledgement_comes_after_the_claim(env):
```

## 17. Assistant — 2026-10-24T07:20:33.554Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py"
}
```

## 18. User — 2026-10-24T07:20:33.992Z

### Tool result

```
1	"""The worker with a simulated pipeline: duplicate and concurrent deliveries, crashes, expired
2	leases, stale workers, retries.
3	
4	Every test ends with WorkerEnv.check() (tests/jobs_backends.py): no invariant violation in
5	the tables; at most one accepted attempt, exactly one if the job succeeded, and as many as
6	the deliveries told "accepted" (plus any acceptance whose worker died before it could tell);
7	the accepted folder holds that attempt's result; no two attempts share a folder. Deliveries
8	here are explicit handle() calls, with no queue (tests/test_jobs_queue.py adds one). The tests
9	run on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL.
10	
11	AI contribution: written with Claude Code (Opus 5.5).
12	"""
13	import json
14	from pathlib import Path
15	
16	import pytest
17	
18	from etf_risk.jobs.events import EventLog, read_events
19	from etf_risk.jobs.simulated import SimulatedCrash, SimulatedPipeline
20	from etf_risk.jobs.store import Outcome, Refusal, Status
21	from etf_risk.jobs.worker import WORKER_FAULT_POINTS, PipelineError, Result
22	from jobs_backends import BACKENDS, LEASE, WorkerEnv, make_backend, run_together
23	
24	
25	@pytest.fixture(params=BACKENDS)
26	def env(request, tmp_path):
27	    env = WorkerEnv(make_backend(request.param, tmp_path), tmp_path)
28	    yield env
29	    env.close()
30	
31	
32	def submit(env, **kwargs) -> int:
33	    return env.admin.submit({"snapshot": "simulated", "stride": 21}, {"windows.parquet": "0" * 64}, **kwargs)
34	
35	
36	def crash_at(point):
37	    assert point in WORKER_FAULT_POINTS
38	
39	    def fault(at):
40	        if at == point:
41	            raise SimulatedCrash(point)
42	    return fault
43	
44	
45	def test_a_delivery_runs_the_job_once_and_accepts_its_result(env):
46	    job = submit(env)
47	    pipeline = SimulatedPipeline()
48	    handled = env.deliver(env.worker("A", pipeline), job)
49	    assert handled.result is Result.ACCEPTED and handled.claim.run_id == f"job-{job}-attempt-1"
50	    assert pipeline.runs == [f"job-{job}-attempt-1"] and env.acks == [job]
51	    assert (handled.claim.output_dir / "steps.log").read_text() == "step 1\nstep 2\nstep 3\n"
52	    assert env.admin.attempts(job)[0]["renewals"] == 3              # one heartbeat per step
53	    env.check(job)
54	
55	
56	# Duplicate and concurrent deliveries
57	
58	def test_a_duplicate_delivery_after_success_is_skipped(env):
59	    job = submit(env)
60	    first, second = SimulatedPipeline(), SimulatedPipeline()
61	    env.deliver(env.worker("A", first), job)
62	    handled = env.deliver(env.worker("B", second), job)
63	    assert (handled.result, handled.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)
64	    assert len(first.runs) + len(second.runs) == 1 and env.acks == [job, job]
65	    env.check(job)
66	
67	
68	def test_a_duplicate_delivery_during_a_live_run_is_skipped(env):
69	    job = submit(env)
70	    b = env.worker("B")
71	    during = []
72	
73	    def deliver_again(step, claim):
74	        if step == 2:
75	            during.append(env.deliver(b, job))
76	
77	    env.deliver(env.worker("A", SimulatedPipeline(on_step=deliver_again)), job)
78	    assert [(h.result, h.reason) for h in during] == [(Result.SKIPPED, Refusal.LEASE_HELD)]
79	    assert b.pipeline.runs == [] and env.acks == [job, job]
80	    assert env.handled[-1].result is Result.ACCEPTED                # A's delivery, recorded after B's
81	    env.check(job)
82	
83	
84	def test_a_requeued_job_delivered_twice_is_claimed_once(env):
85	    job = submit(env)
86	    assert env.deliver(env.worker("A", SimulatedPipeline(fail_at={1: True})), job).result is Result.REQUEUED
87	    c = env.worker("C")
88	    during = []
89	
90	    def deliver_again(step, claim):
91	        if step == 1:
92	            during.append(env.deliver(c, job))
93	
94	    assert env.deliver(env.worker("B", SimulatedPipeline(on_step=deliver_again)), job).result is Result.ACCEPTED
95	    assert [(h.result, h.reason) for h in during] == [(Result.SKIPPED, Refusal.LEASE_HELD)]
96	    assert c.pipeline.runs == [] and env.admin.job(job)["accepted_attempt"] == 2
97	    env.check(job)
98	
99	
100	def test_concurrent_deliveries_of_one_job_run_it_once(env):
101	    """Four workers, each with a connection of its own, handle the same job id at the same moment."""
102	    job = submit(env)
103	    pipelines = [SimulatedPipeline() for _ in range(4)]
104	    workers = [env.worker(name, pipeline) for name, pipeline in zip("ABCD", pipelines)]
105	    results = run_together(*(lambda worker=worker: env.deliver(worker, job) for worker in workers))
106	    assert [h.result for h in results].count(Result.ACCEPTED) == 1
107	    assert all(h.result is Result.SKIPPED and h.reason in (Refusal.LEASE_HELD, Refusal.SUCCEEDED)
108	               for h in results if h.result is not Result.ACCEPTED)
109	    assert sum(len(p.runs) for p in pipelines) == 1 and env.acks == [job] * 4
110	    env.check(job)
111	
112	
113	# Crashes
114	
115	def test_a_crash_before_the_claim_leaves_the_job_queued(env):
116	    job = submit(env)
117	    with pytest.raises(SimulatedCrash):
118	        env.deliver(env.worker("A", fault=crash_at("before_claim")), job)
119	    assert env.admin.job(job)["status"] is Status.QUEUED and env.admin.attempts(job) == [] and env.acks == []
120	    assert env.deliver(env.worker("B"), job).result is Result.ACCEPTED   # the unacknowledged delivery again
121	    env.check(job)
122	
123	
124	def test_a_crash_between_claim_and_acknowledgement(env):
125	    job = submit(env)
126	    with pytest.raises(SimulatedCrash):
127	        env.deliver(env.worker("A", fault=crash_at("after_claim")), job)
128	    assert env.acks == []                                           # not acknowledged: delivered again
129	    again = env.deliver(env.worker("B"), job)
130	    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.LEASE_HELD)
131	    assert env.acks == [job]                                        # acknowledged: no delivery is pending
132	    env.clock.advance(LEASE.total_seconds())                        # A's lease runs out ...
133	    assert env.admin.job(job)["status"] is Status.RUNNING          # ... and nothing happens by itself
134	    handled = env.deliver(env.worker("C"), job)                     # a new delivery (later: the reconciler's)
135	    assert handled.result is Result.ACCEPTED and handled.claim.attempt_number == 2
136	    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
137	    assert not (env.runs / f"job-{job}-attempt-1").exists()        # A died before creating its folder
138	    env.check(job)
139	
140	
141	def test_a_crash_in_the_middle_of_the_run(env):
142	    job = submit(env)
143	
144	    def die(step, claim):
145	        if step == 2:
146	            raise SimulatedCrash("the worker died mid-run")
147	
148	    with pytest.raises(SimulatedCrash):
149	        env.deliver(env.worker("A", SimulatedPipeline(on_step=die)), job)
150	    assert (env.runs / f"job-{job}-attempt-1" / "steps.log").read_text() == "step 1\n"
151	    assert env.admin.job(job)["status"] is Status.RUNNING
152	    env.clock.advance(LEASE.total_seconds())
153	    assert env.deliver(env.worker("B"), job).result is Result.ACCEPTED
154	    env.check(job)
155	
156	
157	def test_a_crash_after_the_pipeline_loses_only_that_attempt(env):
158	    job = submit(env)
159	    first, second = SimulatedPipeline(), SimulatedPipeline()
160	    with pytest.raises(SimulatedCrash):
161	        env.deliver(env.worker("A", first, fault=crash_at("after_pipeline")), job)
162	    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # complete, never accepted
163	    env.clock.advance(LEASE.total_seconds())
164	    handled = env.deliver(env.worker("B", second), job)
165	    assert handled.result is Result.ACCEPTED and env.admin.job(job)["accepted_attempt"] == 2
166	    assert len(first.runs) + len(second.runs) == 2                  # executed twice, accepted once
167	    env.check(job)
168	
169	
170	def test_a_crash_after_acceptance_keeps_the_one_result(env):
171	    job = submit(env)
172	    with pytest.raises(SimulatedCrash):
173	        env.deliver(env.worker("A", fault=crash_at("after_accept")), job)
174	    assert env.admin.job(job)["status"] is Status.SUCCEEDED
175	    again = env.deliver(env.worker("B"), job)
176	    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)
177	    env.check(job, lost_acceptances=1)                              # A died before it could tell
178	
179	
180	def test_a_crash_between_the_acceptance_commit_and_its_event_leaves_the_result_unreported(env, tmp_path):
181	    """Recovery case W5a: the table holds one accepted result and the log has no accepted event."""
182	    job = submit(env)
183	    worker = env.worker("A", fault=crash_at("after_accept_commit"))
184	    worker.events = EventLog(tmp_path / "A.jsonl", "worker", worker_id="worker-A")
185	    with pytest.raises(SimulatedCrash):
186	        env.deliver(worker, job)
187	    assert env.admin.job(job)["status"] is Status.SUCCEEDED
188	    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.ACCEPTED]
189	    assert [e["event"] for e in read_events(tmp_path / "A.jsonl")] == ["claimed"]   # no accepted event
190	    env.check(job, lost_acceptances=1)
191	
192	
193	# Expired leases and stale workers
194	
195	def test_an_expired_lease_mid_run_fences_the_slow_worker(env):
196	    job = submit(env)
197	    b = env.worker("B")
198	    taken_over = []
199	
200	    def stall_then_lose_the_job(step, claim):
201	        if step == 2:                                               # A stalls past its lease, B takes over
202	            env.clock.advance(LEASE.total_seconds() + 1)
203	            taken_over.append(env.deliver(b, job))
204	
205	    handled = env.deliver(env.worker("A", SimulatedPipeline(on_step=stall_then_lose_the_job)), job)
206	    assert [h.result for h in taken_over] == [Result.ACCEPTED]
207	    assert handled.result is Result.FENCED                          # A's next heartbeat was refused
208	    a_dir = env.runs / f"job-{job}-attempt-1"
209	    assert (a_dir / "steps.log").read_text() == "step 1\n" and not (a_dir / "result.json").exists()
210	    assert env.admin.job(job)["accepted_attempt"] == 2
211	    env.check(job)
212	
213	
214	def test_an_expired_lease_without_a_takeover_lets_the_worker_finish(env):
215	    job = submit(env)
216	
217	    def stall(step, claim):
218	        if step == 2:
219	            env.clock.advance(3 * LEASE.total_seconds())            # long past the lease, but nobody takes over
220	
221	    assert env.deliver(env.worker("A", SimulatedPipeline(on_step=stall)), job).result is Result.ACCEPTED
222	    env.check(job)
223	
224	
225	def test_a_stale_worker_cannot_get_its_result_accepted(env):
226	    job = submit(env)
227	    b = env.worker("B")
228	    taken_over = []
229	
230	    def lose_the_job(point):
231	        if point == "after_pipeline":                               # A finished too late: B takes over
232	            env.clock.advance(LEASE.total_seconds())
233	            taken_over.append(env.deliver(b, job))
234	
235	    handled = env.deliver(env.worker("A", fault=lose_the_job), job)
236	    assert [h.result for h in taken_over] == [Result.ACCEPTED] and handled.result is Result.FENCED
237	    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # A's folder stays, unreferenced
238	    assert env.admin.job(job)["accepted_attempt"] == 2
239	    env.check(job)
240	
241	
242	def test_a_stale_worker_cannot_record_a_failure(env):
243	    job = submit(env)
244	    b = env.worker("B")
245	    taken_over = []
246	
247	    def lose_the_job_then_fail(step, claim):
248	        if step == 2:                                               # B takes over and finishes; then A fails
249	            env.clock.advance(LEASE.total_seconds() + 1)            # before any heartbeat could tell it
250	            taken_over.append(env.deliver(b, job))
251	            raise PipelineError("failed after losing the job")
252	
253	    handled = env.deliver(env.worker("A", SimulatedPipeline(on_step=lose_the_job_then_fail)), job)
254	    assert [h.result for h in taken_over] == [Result.ACCEPTED] and handled.result is Result.FENCED
255	    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
256	    env.check(job)
257	
258	
259	# Failures and retries
260	
261	def test_a_retryable_failure_is_not_delivered_again_by_itself(env):
262	    job = submit(env)
263	    handled = env.deliver(env.worker("A", SimulatedPipeline(fail_at={2: True})), job)
264	    assert handled.result is Result.REQUEUED and env.acks == [job]
265	    env.clock.advance(3600)
266	    j = env.admin.job(job)
267	    assert (j["status"], j["attempt_number"]) == (Status.QUEUED, 1)   # still waiting: nothing delivers it
268	    handled = env.deliver(env.worker("B"), job)                     # an explicit delivery (later: the reconciler's)
269	    assert handled.result is Result.ACCEPTED and handled.claim.attempt_number == 2
270	    assert [(a["outcome"], a["error"]) for a in env.admin.attempts(job)] == [
271	        (Outcome.FAILED, "injected failure at step 2"), (Outcome.ACCEPTED, None)]
272	    env.check(job)
273	
274	
275	def test_retries_end_when_attempts_run_out(env):
276	    job = submit(env, max_attempts=3)
277	    results = [env.deliver(env.worker(name, SimulatedPipeline(fail_at={1: True})), job).result for name in "ABC"]
278	    assert results == [Result.REQUEUED, Result.REQUEUED, Result.FAILED]
279	    again = env.deliver(env.worker("D"), job)
280	    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.FAILED)
281	    attempts = env.admin.attempts(job)
282	    assert [a["outcome"] for a in attempts] == [Outcome.FAILED] * 3
283	    assert all(Path(a["output_dir"]).is_dir() for a in attempts)  # three attempts, three folders
284	    env.check(job)
285	
286	
287	def test_a_permanent_failure_fails_the_job(env):
288	    job = submit(env)
289	    assert env.deliver(env.worker("A", SimulatedPipeline(fail_at={1: False})), job).result is Result.FAILED
290	    again = env.deliver(env.worker("B"), job)
291	    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.FAILED)
292	    assert env.admin.job(job)["error"] == "injected failure at step 1"
293	    env.check(job)
294	
295	
296	def test_an_unexpected_pipeline_error_counts_as_a_retryable_failure(env):
297	    job = submit(env)
298	
299	    def bug(step, claim):
300	        raise ValueError("bug in the pipeline")
301	
302	    assert env.deliver(env.worker("A", SimulatedPipeline(on_step=bug)), job).result is Result.REQUEUED
303	    assert env.admin.attempts(job)[0]["error"] == "ValueError: bug in the pipeline"
304	    env.check(job)
305	
306	
307	def test_an_existing_output_folder_is_never_written_into(env):
308	    job = submit(env)
309	    folder = env.runs / f"job-{job}-attempt-1"
310	    folder.mkdir(parents=True)
311	    (folder / "marker").write_text("left by another job table")
312	    pipeline = SimulatedPipeline()
313	    assert env.deliver(env.worker("A", pipeline), job).result is Result.FAILED
314	    assert pipeline.runs == [] and [p.name for p in folder.iterdir()] == ["marker"]
315	    assert "output folder already exists" in env.admin.job(job)["error"]
316	    env.check(job)
317	
318	
319	def test_acknowledgement_comes_after_the_claim(env):
320	    job = submit(env)
321	    events = []
322	    worker = env.worker("A", fault=events.append)
323	    env.handled.append(worker.handle(job, lambda: events.append("acknowledge")))
324	    assert events == ["before_claim", "after_claim", "acknowledge", "after_pipeline", "after_accept_commit",
325	                      "after_accept"]
326	    events.clear()
327	    env.handled.append(worker.handle(job, lambda: events.append("acknowledge")))   # refused: at once
328	    assert events == ["before_claim", "acknowledge"]
329	    env.check(job)
330	
```

## 19. Assistant — 2026-10-24T07:20:40.556Z

### Tool call: Bash

```
{
  "command": "sed -n 40,80p src/etf_risk/jobs/simulated.py && grep -n -E 'def (worker|deliver|check|close)|class WorkerEnv|lost_acceptances' tests/jobs_backends.py",
  "description": "Read the simulated pipeline and worker test helpers"
}
```

## 20. User — 2026-10-24T07:20:41.282Z

### Tool result

```
def result_digest(params: dict) -> str:
    """The simulated analysis result: the same for every attempt of a job."""
    return hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest()


class SimulatedPipeline:
    """Stands in for windows -> spark_pipeline -> verify.

    Each of `steps` steps calls on_step(step, claim) if given, then the heartbeat (raising
    Fenced once it returns False), then fails if fail_at names the step (it maps a step to
    whether that failure is retryable), then appends a line to steps.log in the run folder.
    After the last step it writes result.json: the attempt that wrote it and the job's
    result digest. It returns the run folder's digest (etf_risk.runs), which acceptance
    records. on_step lets a test step the clock or run another worker in the middle of this
    run. runs lists the run ids of the executions this pipeline started."""

    def __init__(self, steps: int = 3, *, fail_at: dict[int, bool] | None = None,
                 on_step: Callable[[int, Claim], None] | None = None):
        self.steps = steps
        self.fail_at = fail_at or {}
        self.on_step = on_step
        self.runs: list[str] = []

    def run(self, claim: Claim, run_dir: Path, heartbeat: Callable[[], bool]) -> str:
        self.runs.append(claim.run_id)
        for step in range(1, self.steps + 1):
            if self.on_step is not None:
                self.on_step(step, claim)
            if not heartbeat():
                raise Fenced(f"{claim.run_id}: fenced off before step {step}")
            if step in self.fail_at:
                raise PipelineError(f"injected failure at step {step}", retryable=self.fail_at[step])
            with (run_dir / "steps.log").open("a") as log:
                log.write(f"step {step}\n")
        (run_dir / "result.json").write_text(json.dumps(
            {"job_id": claim.job_id, "attempt_number": claim.attempt_number, "run_id": claim.run_id,
             "result_sha256": result_digest(claim.params)}, sort_keys=True))
        return folder_digest(run_dir)


81:    def close(self):
138:    def close(self):
167:    def close(self):
184:class WorkerEnv(JobsEnv):
193:    def worker(self, name, pipeline=None, fault=None, store_fault=None) -> Worker:
197:    def deliver(self, worker: Worker, job_id: int) -> Handled:
202:    def check(self, job_id: int, *, lost_acceptances: int = 0) -> None:
212:        assert len(accepted) == len(told) + lost_acceptances == (1 if job["status"] is Status.SUCCEEDED else 0)
285:    def close(self) -> None:
```

## 21. Assistant — 2026-10-24T07:20:54.690Z

### Tool call: Bash

```
{
  "command": "grep -n -E '\\bD2\\b' docs/recovery-experiments.md | head -30; echo ---; grep -n -E 'during|\"fenced\"|fenced' analysis/collect_recovery_measurements.py src/etf_risk/jobs/harness.py | head -30",
  "description": "Find D2 descriptions and fenced-event handling"
}
```

## 22. User — 2026-10-24T07:20:55.448Z

### Tool result

```
157:| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL, after a peak reading | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`) and the job runs again after its lease expires | 1 or 2 / 1 | no; a lost COMMIT reply offline (`test_jobs_reconnect.py`) |
178:| D2 | `retry` of `accept_result`; then `accepted`, or else `failed_after_ack` and `requeued` | as D1 | as D1 |
204:(`submit` for a control; `restored`, the moment the service works again, for K2, D1 and D2;
207:on-time success). Counting K2, D1 and D2 from their service's return keeps the time a restart takes,
231:fail in D1 and D2 when a deadline falls while MySQL is down, as the M2 test's own connection did
269:and start does the same. Before every injected restart or stop (K1, K2, D1, D2) the harness records
304:| D1, D2 | yes | yes if a new attempt started; otherwise n/a | yes |
413:  runs 16 times per 14 jobs). A longer restore lengthens K2 and can move D1 and D2 onto their fenced
439:  - K2, D1 and D2 count from their service's return (4.2), so B holds no outage of unknown length:
441:    D1 and D2 a fenced attempt's lease and a pass (65 s);
452:  | D1, D2, from MySQL's return | 65 s | 140 s | 195 s |
485:  action (SIGKILL to the worker's own process, or a hold until a release file appears, for D2). The
491:- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside
500:(the phase delay before a mid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep
562:  bound, K2, D1 and D2 counted from their service's return, the observation at completion when that
---
analysis/collect_recovery_measurements.py:66:          "wasted_step_s", "fenced_events", "timeliness", "deadline_met", "q1_verdict", "q3a_verdict"]
analysis/collect_recovery_measurements.py:212:    row["fenced_events"] = len(named(events, "fenced")) + len(named(events, "renewal_refused"))
src/etf_risk/jobs/harness.py:143:    if case in ("D1", "D2"):             # a fenced attempt's lease, then a pass
src/etf_risk/jobs/harness.py:199:    if case == "D1":                     # fenced when MySQL is away past F; then the lease, a pass, a run
src/etf_risk/jobs/harness.py:598:            raise PhaseMissed("spark_pipeline ended during the phase delay")
src/etf_risk/jobs/harness.py:677:        Then SIGCONT, the old worker's fenced event, and SIGTERM (its attempt is no longer its own)."""
src/etf_risk/jobs/harness.py:694:        fenced = self.wait_for(lambda: next(iter(events_named(self.worker_logs()[worker], "fenced",
src/etf_risk/jobs/harness.py:696:                               120, f"worker {worker}'s fenced event")
src/etf_risk/jobs/harness.py:700:                "t_inj": t_inj, "resumed": resumed, "fenced_mono": fenced["mono"], "stopped": len(frozen)}
```

## 23. Assistant — 2026-10-24T07:20:59.853Z

### Tool call: Bash

```
{
  "command": "sed -n 150,182p docs/recovery-experiments.md; echo ----; sed -n 225,236p docs/recovery-experiments.md; echo ----; sed -n 130,215p src/etf_risk/jobs/harness.py",
  "description": "Read D2 rows and the harness deadline/estimate code"
}
```

## 24. User — 2026-10-24T07:21:00.618Z

### Tool result

````
| W5a | SIGKILL after the acceptance commits, before its `accepted` event | hook at a new fault point between `accept_result`'s return and the event (8.4) | E1 | nothing to recover; the table holds the acceptance and the log lacks its event (6.4) | 1 / 1; no report | no |
| W5b | SIGKILL after the `accepted` event | hook at `after_accept` | E1 | nothing to recover: the offset was committed at the claim | 1 / 1 | no |
| W6 | SIGSTOP of the worker during `spark_pipeline`; SIGCONT after the takeover | signals | E1 | the watchdog ends the stopped worker's tree before its lease expires; requeue; the standby claims attempt 2; after SIGCONT the old worker's renewal is refused, it is fenced, and the harness stops it (2.4) | 2 / 1 | yes, once |
| W7 | SIGSTOP of the worker's whole tree (worker, launcher, Spark); SIGCONT later | signals | E1 | the replacement's step waits for the host lock while the stopped tree survives; after SIGCONT the stopped launcher, past its deadline, ends its tree, and the old worker is fenced and stopped. A stop longer than the replacement's lock wait fails that attempt as retryable | 2 or 3 / 1 | yes, once |
| K1 | Kafka restart while a step runs | `docker compose restart kafka`, after a peak reading (4.6) | E2 | the running job goes on (the worker does not poll during a run); the next delivery waits for the group (3.2) | 1 / 1 | yes, once |
| K2 | a submit while Kafka is stopped | a peak reading, stop Kafka, submit, start Kafka | E2 | the confirmation times out (10 s) and `published_at` stays empty; once Kafka is back and the 30 s grace has passed, the reconciler publishes the job | 1 / 1 | no; an unreachable broker's confirmation in `test_jobs_kafka.py` |
| D1 | MySQL restart while a step runs | `docker compose restart mysql`, after a peak reading | E2 | renewals fail and are tried again; back before F: the attempt goes on; otherwise the worker fences itself, the watchdog ends the tree, and the job is requeued once MySQL is back | 1 or 2 / 1 | yes, once (also a table lock and a pause) |
| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL, after a peak reading | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`) and the job runs again after its lease expires | 1 or 2 / 1 | no; a lost COMMIT reply offline (`test_jobs_reconnect.py`) |
| X1 | the job id published again, while the job runs and after it succeeded | harness publishes | E1 | each extra delivery is refused (lease held, then succeeded) and committed; no new attempt | 1 / 1 | no; refusals offline (`test_jobs_queue.py`) |

All 14 cases are kept; a case without an injection method is recorded as not run, never dropped.

### 3.2 Expected times and Kafka conditions

Symbols, from [worker-pipeline.md](worker-pipeline.md) and [job-queue.md](job-queue.md), with the
default values: lease L 60 s, renewal interval R 10 s, fence deadline F (L − M after the last renewal
began, M 10 s), kill grace G 7 s, reconciler interval P 5 s, session timeout S 15 s, heartbeat
interval h 3 s, publication grace g 30 s; T is a job's failure-free time to finish.

| Case | Detection event | From the injection to the next claim | Kafka condition |
|---|---|---|---|
| W1 | the standby's `delivered` | about S − h to S + h, plus a poll (1 s) | the killed worker owned the partition; its session expires S − h to S after the kill; the idle standby (2.4) learns of the rebalance at its next heartbeat and rejoins at its next poll |
| W2, W4 | the reconciler's `requeued` | L to L + P (the lease was just set or renewed), plus a delivery | the standby owns the partition from about S + h after the kill, before the requeue: S + h + 1 s < L − R (19 < 50 s at the defaults, 14 < 20 s on M2's clock) |
| W3, W6 | `requeued` | about L − R to L + P, plus a delivery | as W2; a stopped worker (W6) stops heartbeating, so it loses the partition as a dead one does |
| W7 | `requeued` | as W3; then the replacement's step waits for the host lock until the stopped tree is resumed and ended | as W6 |
| K1 | — (the attempt goes on) | n/a | the group re-forms after the restart; a member busy with a job delays a rebalance until its next poll; the owner afterwards comes from the assignment events |
| K2 | the reconciler's `published` | the later of Kafka's return and g after the submit, plus up to P, plus a delivery | a delivery needs an owner again after the restart |
| D1 | `renewal_failed`; then `renewed`, or else `requeued` | none if MySQL is back before F; otherwise once the lease has expired and MySQL is back, plus up to P, plus a delivery | none: the owner stays |
| D2 | `retry` of `accept_result`; then `accepted`, or else `failed_after_ack` and `requeued` | as D1 | as D1 |
| W5a, W5b, X1 | — | n/a: after the acceptance, or no failure | a killed worker loses the partition about S after the kill, which delays only the next job (2.4) |

The time to finish adds about T wherever a new attempt starts. At the defaults the windows are about
12–19 s (W1), 60–65 s (W2, W4) and 50–65 s (W3, W6); M2's steps alone took about 34–35 s for the
----
### 4.3 The deadline observation

When the job finishes, or at `deadline_mono` if that comes first, the harness reads the job's row
once, in its own connection, as one consistent snapshot; a read that fails is recorded with no
status and is never repeated. A read taken at completion shows a terminal status, which never
changes, so it decides as a read at the deadline would, and no job waits out its whole D. A read can
fail in D1 and D2 when a deadline falls while MySQL is down, as the M2 test's own connection did
during its stalls.

```sql
SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
-- observed_from_mono: the harness's time.monotonic() just before the next statement
----
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


def deadline_seconds(case: str, timing: Timing, settings: Settings) -> float:
    """D (P3): B plus deadline_margin times S, rounded up to deadline_round_s."""
    raw = bound_to_next_run(case, timing, settings) + settings.deadline_margin * settings.slowest_steps_s
    step = settings.deadline_round_s
    return math.ceil(raw / step - 1e-9) * step


def make_plan(settings: Settings, seed: int) -> dict:
    timing = timing_of(settings)
    return {"format": 1, "seed": seed, "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "settings": asdict(settings), "timing": asdict(timing), "code": code_identity(),
            "deadlines_s": {case: deadline_seconds(case, timing, settings) for case in settings.cases},
            "jobs": plan_jobs(settings, seed)}


# The duration estimate

@dataclass(frozen=True)
class Assumptions:
    """What estimate() assumes. None of it is measured: T for the job system, the restore time
    and the restart overhead are guesses to be replaced by the first batch's records."""
    time_to_finish_s: float = 40.0       # T: M2's slowest steps (35.1 s) plus 5 s of the worker's own work
    restart_s: float = 12.0              # a killed worker's start, sweep and rebalance
    restore_s: float = 20.0              # a service's start until it is ready again
    peaks_s: float = 2.0                 # the peaks read after every job
    group_settle_s: float = 18.0         # after a Kafka restart, until the group has an owner (S + h)
    batch_fixed_s: float = 180.0         # containers, reference run, workers, final snapshot, teardown


def case_seconds(case: str, timing: Timing, settings: Settings, a: Assumptions) -> float:
    """One job's expected duration from the harness's view: from its start to the next job's."""
    t, lease, period = a.time_to_finish_s, timing.lease, RECONCILE_INTERVAL.total_seconds()
    partial = 1.0 + 3.0 + settings.phase_delay_s         # delivery, windows (M2: up to 3.0 s), the delay
    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0
    down = settings.outage_s + a.restore_s
    to_fence = lease - timing.fence_margin - timing.renew_interval   # the earliest F after an injection
    if case == "C0":
        return t + a.peaks_s
    if case in ("W1", "W2"):
        return 1.0 + bound_to_next_run(case, timing, settings) + t + a.restart_s + a.peaks_s
    if case in ("W3", "W6", "W7"):
        return partial + bound_to_next_run(case, timing, settings) + t + a.restart_s + a.peaks_s
    if case == "W4":
        return t + lease + period + t + a.restart_s + a.peaks_s
    if case in ("W5a", "W5b"):
        return t + a.restart_s + a.peaks_s
    if case == "K1":
        return t + a.group_settle_s + 2 * a.peaks_s
    if case == "K2":
        wait = max(0.0, PUBLICATION_GRACE.total_seconds() - down)
        return a.peaks_s + down + wait + period + rejoin + t + a.peaks_s
    if case == "D1":                     # fenced when MySQL is away past F; then the lease, a pass, a run
        if down >= to_fence:
            return partial + a.peaks_s + max(down, lease) + period + t + a.peaks_s
        return max(t, partial + down) + 2 * a.peaks_s
    if case == "D2":                     # held after the run; acceptance tried until F
        if down >= lease - timing.fence_margin:
            return t + a.peaks_s + lease + period + t + a.peaks_s
        return t + a.peaks_s + down + a.peaks_s
    if case == "X1":
        return t + 2.0 + a.peaks_s
    raise ValueError(f"unknown case {case!r}")


def estimate(plan: dict, a: Assumptions = Assumptions()) -> dict:
    settings = Settings.from_dict(plan["settings"])
    timing = timing_of(settings)
    per_case = {case: case_seconds(case, timing, settings, a) for case in settings.cases}
````

## 25. Assistant — 2026-10-24T07:21:12.402Z

### Tool call: Bash

```
{
  "command": "grep -n -E '\"D2\"|D2|release' src/etf_risk/jobs/harness.py | head -40",
  "description": "Find the D2 injection path in the harness"
}
```

## 26. User — 2026-10-24T07:21:13.212Z

### Tool result

```
60:CASES = ("C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "W6", "W7", "K1", "K2", "D1", "D2", "X1")
62:         "W5a": ("after_accept_commit", "kill"), "W5b": ("after_accept", "kill"), "D2": ("after_pipeline", "hold")}
65:FROM_RESTORED = ("K2", "D1", "D2")              # deadline counted from the service's return (4.2)
93:    outage_s: float = 30.0               # 8.5: how long K2, D1 and D2 keep their service stopped
129:    K2, D1 and D2 count from their service's return, since how long a restart takes is not
143:    if case in ("D1", "D2"):             # a fenced attempt's lease, then a pass
203:    if case == "D2":                     # held after the run; acceptance tried until F
631:    def inject(self, position: int, case: str, job_id: int, armed: str | None, release: Path | None) -> dict:
634:        if hook is not None and case != "D2":
639:        if case == "D2":
644:            release.touch()                                  # acceptance meets the outage
707:        armed, release, injection = None, None, None
711:            release = self.faults_dir / f"release-{position}" if action == "hold" else None
712:            faults.arm(self.fault_file(armed), point, action, release=release,
713:                       timeout_s=s.outage_s + 600 if release else None)
737:                injection = self.inject(position, case, job_id, armed, release)
```

## 27. Assistant — 2026-10-24T07:21:16.774Z

### Tool call: Bash

```
{
  "command": "sed -n 625,800p src/etf_risk/jobs/harness.py",
  "description": "Read the harness inject and run_job code"
}
```

## 28. User — 2026-10-24T07:21:17.526Z

### Tool result

```
            if parsed is not None and parsed[0] == self.store_id and parsed[1] == run_id:
                frozen += procs
        for p in frozen:
            p.suspend()
        return frozen

    def inject(self, position: int, case: str, job_id: int, armed: str | None, release: Path | None) -> dict:
        """Make the case's injection; what happened, with t_inj and the deadline's reference."""
        s, hook = self.settings, HOOKS.get(case)
        if hook is not None and case != "D2":
            point = hook[0]
            event = self.wait_fault(armed, job_id, point)
            self.wait_for(lambda: self.procs[armed].poll() is not None, 30, f"worker {armed} to end")
            return {"kind": "hook", "worker": armed, "point": point, "t_inj": event["mono"]}
        if case == "D2":
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
                os.kill(self.procs[worker].pid, signal.SIGKILL)
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
            frozen = self.stop_tree(worker, claim["run_id"])
            time.sleep(max(0.0, t_inj + self.settings.w7_stop_s - time.monotonic()))
        resumed = time.monotonic()
        for p in reversed(frozen):
            try:
                p.resume()
            except psutil.Error:
                pass
        fenced = self.wait_for(lambda: next(iter(events_named(self.worker_logs()[worker], "fenced",
                                                              job_id=job_id, attempt=claim["attempt"])), None),
                               120, f"worker {worker}'s fenced event")
        self.procs[worker].send_signal(signal.SIGTERM)
        self.wait_for(lambda: self.procs[worker].poll() is not None, 60, f"worker {worker} to stop")
        return {"kind": "sigstop" if case == "W6" else "sigstop_tree", "worker": worker, "attempt": claim["attempt"],
                "t_inj": t_inj, "resumed": resumed, "fenced_mono": fenced["mono"], "stopped": len(frozen)}

    # One job

    def run_job(self, position: int, case: str) -> dict:
        s = self.settings
        record = {"position": position, "case": case, "owner_before": self.wait_owner()}
        armed, release, injection = None, None, None
        if case in HOOKS:
            point, action = HOOKS[case]
            armed = record["owner_before"]
            release = self.faults_dir / f"release-{position}" if action == "hold" else None
            faults.arm(self.fault_file(armed), point, action, release=release,
                       timeout_s=s.outage_s + 600 if release else None)
            self.log.log("armed", position=position, worker=armed, point=point, action=action)
        if case == "K2":
            self.read_peaks(closes="kafka stop")
            t_inj = time.monotonic()
            self.compose("stop", "kafka")
            injection = {"kind": "service_stop", "service": "kafka", "t_inj": t_inj}
        t_submit = time.monotonic()
        job_id = self.submit()
        record["job_id"] = job_id
        if job_id is None:
            self.log.log("job_not_submitted", position=position, case=case)
            if case == "K2":                                 # never leave the broker stopped
                self.compose("start", "kafka")
                self.wait_ready("kafka")
            if armed is not None:
                self.fault_file(armed).unlink(missing_ok=True)
            return {**record, "outcome": "submit_failed"}
        try:
            if case == "K2":
                time.sleep(max(0.0, injection["t_inj"] + s.outage_s - time.monotonic()))
                self.compose("start", "kafka")
                injection["restored"] = self.wait_ready("kafka")
            elif case != "C0":
                injection = self.inject(position, case, job_id, armed, release)
            missed = None
        except PhaseMissed as error:
            missed = str(error)
            if armed is not None:
                self.fault_file(armed).unlink(missing_ok=True)
        reference = deadline_reference(case)
        if missed is not None or reference == "submit":
            reference_mono, d = t_submit, deadline_seconds("C0", self.timing, s)
            reference = "submit"
        else:
            reference_mono = injection["restored"] if reference == "restored" else injection["t_inj"]
            d = deadline_seconds(case, self.timing, s)
        deadline_mono = reference_mono + d
        self.batch_jobs.append((job_id, case, reference, d, deadline_mono, s.max_lag_s))
        self.log.log("deadline", position=position, job_id=job_id, case=case, reference=reference,
                     reference_mono=reference_mono, deadline_s=d, deadline_mono=deadline_mono, max_lag_s=s.max_lag_s,
                     t_submit=t_submit)
        self.log.log("injection", position=position, job_id=job_id, case=case, missed=missed, **(injection or {}))
        tracker = Tracker(self, job_id, deadline_mono, deadline_mono + d)
        tracker.start()
        if case == "X1" and missed is None:                  # the second duplicate, once the job succeeded
            try:
                self.wait_for(lambda: self.job_status(job_id) == "succeeded", 2 * d, f"job {job_id} to succeed")
                self.log.log("published_again", job_id=job_id, after="succeeded",
                             published=self.publish_again(job_id), t=time.monotonic())
            except PhaseMissed as error:
                self.log.log("published_again", job_id=job_id, after=None, error=str(error))
        tracker.join()
        record.update(final=tracker.final, finished_mono=tracker.finished_mono, observation=tracker.observation,
                      missed=missed)
        self.log.log("job_done", position=position, job_id=job_id, case=case, final=tracker.final,
                     finished_mono=tracker.finished_mono)
        return record

    def after_job(self, record: dict) -> None:
        """The restart rule (2.4), the group after a Kafka restart, and the peaks of P4."""
        restarted = [w for w in WORKERS if self.procs[w].poll() is not None]
        for worker in restarted:
            self.start_worker(worker)
            self.log.log("restarted", worker=worker, position=record["position"])
        if record["case"] in ("K1", "K2"):
            time.sleep(self.timing.session_timeout + self.timing.heartbeat_interval)
        for worker in restarted:
            self.wait_joined(worker)
        self.log.log("owner", owner=self.wait_owner(), position=record["position"])
        if self.read_peaks() == "stop":
            self.stop_reason = "memory"

    # Start, quiescence and the final snapshot

    def reference_run(self) -> None:
        """The reference run: the job's windows and spark_pipeline steps, each under a launcher
        with the harness as its parent, so it takes the host lock and registers its tree (2.2)."""
        from etf_risk.jobs.params import JobParams
        from etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline
        s = self.settings
        params = JobParams(s.snapshot, s.kind, stride=s.stride)
        pipeline = SubprocessPipeline(store_id=self.store_id, processed_root=REPO_ROOT / "data" / "processed",
                                      worker_id="reference", lock_path=DEFAULT_LOCK, timing=self.timing)
        run_dir = self.out / "reference"

        class Reference:
            run_id = "reference"
```

## 29. Assistant — 2026-10-24T07:21:53.429Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'read_timeout|write_timeout|connect_timeout|lock_wait|innodb' src/etf_risk/jobs/*.py | head -20",
  "description": "Find database call timeouts that bound a blocked call"
}
```

## 30. User — 2026-10-24T07:21:54.390Z

### Tool result

```
src/etf_risk/jobs/launcher.py:136:                             "started_at_utc": datetime.now(timezone.utc).isoformat(), "lock_wait_s": None,
src/etf_risk/jobs/launcher.py:195:            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
src/etf_risk/jobs/launcher.py:197:                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
src/etf_risk/jobs/launcher.py:203:            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
src/etf_risk/jobs/launcher.py:204:                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
src/etf_risk/jobs/launcher.py:207:        self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
src/etf_risk/jobs/mysql.py:48:SERVICE_SESSION = {"connect_timeout": 3, "read_timeout": 5, "write_timeout": 5, "lock_wait_timeout": 2,
src/etf_risk/jobs/mysql.py:109:                  isolation: str = "REPEATABLE READ", lock_wait_timeout: int | None = None,
src/etf_risk/jobs/mysql.py:110:                  connect_timeout: float | None = None, read_timeout: float | None = None,
src/etf_risk/jobs/mysql.py:111:                  write_timeout: float | None = None, wait_timeout: int | None = None) -> Any:
src/etf_risk/jobs/mysql.py:112:    """A PyMySQL connection for JobStore(connection, MYSQL). lock_wait_timeout sets the
src/etf_risk/jobs/mysql.py:113:    session's innodb_lock_wait_timeout and wait_timeout its wait_timeout, in seconds; the
src/etf_risk/jobs/mysql.py:121:    timeouts = {name: value for name, value in (("connect_timeout", connect_timeout), ("read_timeout", read_timeout),
src/etf_risk/jobs/mysql.py:122:                                                ("write_timeout", write_timeout)) if value is not None}
src/etf_risk/jobs/mysql.py:128:            if lock_wait_timeout is not None:
src/etf_risk/jobs/mysql.py:129:                cursor.execute("SET SESSION innodb_lock_wait_timeout = %s", (int(lock_wait_timeout),))
src/etf_risk/jobs/harness.py:526:            conn = mysql.connect_mysql(self.db, connect_timeout=3, read_timeout=5, write_timeout=5)
src/etf_risk/jobs/harness.py:810:                       "--registry", str(pipeline.registry), "--lock-wait", str(self.timing.lock_wait(name)),
src/etf_risk/jobs/harness.py:816:            deadline = time.monotonic() + self.timing.lock_wait(name) + limit + 30
src/etf_risk/jobs/timing.py:72:    def lock_wait(self, step: str) -> float:
```

## 31. Assistant — 2026-10-24T07:22:00.053Z

Adding the check before the first acceptance call:

## 32. Assistant — 2026-10-24T07:22:03.207Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py",
  "old_string": "        self._fault(\"after_pipeline\")\n        if not self._until_deadline(lambda: self.store.accept_result(claim, digest), claim, \"accept_result\"):",
  "new_string": "        self._fault(\"after_pipeline\")\n        deadline = getattr(self.pipeline, \"fence_at\", None)\n        if deadline is not None and time.monotonic() >= deadline:\n            # Never an acceptance call after F (docs/worker-pipeline.md), even while the token holds.\n            self.events.log(\"fenced\", job_id=job_id, attempt=claim.attempt_number, during=\"acceptance\",\n                            why=f\"{claim.run_id}: the deadline passed before acceptance\")\n            return Handled(job_id, Result.FENCED, claim=claim)\n        if not self._until_deadline(lambda: self.store.accept_result(claim, digest), claim, \"accept_result\"):"
}
```

## 33. Assistant — 2026-10-24T07:22:06.049Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py",
  "old_string": "lost database connection, acceptance and the failure write are tried again until the\npipeline's own deadline (fence_at), if it keeps one; both are safe to repeat (store.py).",
  "new_string": "lost database connection, acceptance and the failure write are tried again until the\npipeline's own deadline (fence_at), if it keeps one; both are safe to repeat (store.py).\nOnce that deadline has passed, the worker makes no acceptance call at all: it fences itself\n(event fenced, during acceptance). A call that started before the deadline can still finish\nafter it; the attempt's token guards that call as it guards every other."
}
```

## 34. User — 2026-10-24T07:22:07.168Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 35. User — 2026-10-24T07:22:08.334Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 36. Assistant — 2026-10-24T07:22:18.148Z

### Tool call: Bash

```
{
  "command": "sed -n 1,60p tests/jobs_backends.py && sed -n 180,300p tests/jobs_backends.py",
  "description": "Read the shared job test backends and WorkerEnv"
}
```

## 37. User — 2026-10-24T07:22:19.039Z

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
from etf_risk.runs import folder_digest

MYSQL_URL = os.environ.get("ETF_RISK_MYSQL_URL")
BACKENDS = ["sqlite", "mysql"] if MYSQL_URL else ["sqlite"]
needs_mysql = pytest.mark.skipif(not MYSQL_URL, reason="set ETF_RISK_MYSQL_URL to run against MySQL")
KAFKA_BOOTSTRAP = os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP")
needs_kafka = pytest.mark.skipif(not KAFKA_BOOTSTRAP, reason="set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka")
LEASE = timedelta(seconds=60)
PARAMS = {"snapshot": "simulated", "stride": 21}
DIGEST = "d" * 64          # a run digest for store tests that accept without a pipeline
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
        folder, whose run digest is the one recorded with the acceptance; no two attempts
        sharing a folder."""
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
            assert a["result_digest"] == folder_digest(a["output_dir"])
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


class KafkaTopic:
    """A topic of its own for one test, with fresh consumer group names; close() closes the
    consumers it opened and deletes the topic."""

    def __init__(self):
        pytest.importorskip("confluent_kafka")
        from etf_risk.jobs import kafka
        self._kafka, self.bootstrap = kafka, KAFKA_BOOTSTRAP
        self.name = f"etf-jobs-test-{secrets.token_hex(4)}"
        self.consumers = []
        kafka.create_topic(self.bootstrap, self.name)

    def group(self) -> str:
        return f"{self.name}-group-{secrets.token_hex(3)}"

    def publisher(self, **options):
        return self._kafka.KafkaPublisher(self.bootstrap, self.name, **options)

    def produce_raw(self, value: bytes) -> None:
        """Write a message that KafkaPublisher would not write, and wait until it is written."""
        from confluent_kafka import Producer
        producer = Producer({"bootstrap.servers": self.bootstrap, "acks": "all"})
        producer.produce(self.name, value=value)
        assert producer.flush(30) == 0, "the raw message was not written"

    def consumer(self, group: str, **options):
        consumer = self._kafka.KafkaConsumer(self.bootstrap, self.name, group, **options)
        self.consumers.append(consumer)
        return consumer

    def close(self) -> None:
        for consumer in self.consumers:
            consumer.close()
        self._kafka.delete_topic(self.bootstrap, self.name)


def poll_deliveries(consumer, count: int, *, timeout: float = 30.0) -> list:
    """The next `count` deliveries, or fewer if they do not come within timeout seconds. The
    first poll of a new consumer also waits for the group to give it its partition."""
    deliveries, deadline = [], time.monotonic() + timeout
    while len(deliveries) < count and time.monotonic() < deadline:
        if (delivery := consumer.poll(0.5)) is not None:
            deliveries.append(delivery)
    return deliveries
```

## 38. Assistant — 2026-10-24T07:22:41.511Z

### Tool call: Bash

```
{
  "command": "cat src/etf_risk/jobs/faults.py",
  "description": "Read the fault-file module"
}
```

## 39. User — 2026-10-24T07:22:42.255Z

### Tool result

```
"""Faults armed at the worker's fault points, for the recovery experiments
(docs/recovery-experiments.md, 3.1 and 8.4).

A worker started with ETF_RISK_FAULT_FILE=<path> looks at that path at each of
WORKER_FAULT_POINTS (etf_risk.jobs.worker); while nothing is there, nothing happens. The
session harness (etf_risk.jobs.harness) arms one fault by writing the file, atomically
(a temporary file, then a rename), as one JSON object:

    {"point": "after_claim", "action": "kill"}
    {"point": "after_pipeline", "action": "hold", "release": "/abs/path", "timeout_s": 300}

When the worker reaches that point, it first removes the file, so a fault fires once, then
writes a fault_injected event (point, action) and:
- kill: sends SIGKILL to its own process, which ends at once, as in a crash. The event's
  mono is the injection time;
- hold: waits until the release path exists, or timeout_s has passed, then writes
  fault_released (with why) and goes on.
A file that names another point is left for that point. A file that cannot be parsed, or
that names an unknown point or action, is removed and reported as fault_refused, and the
worker goes on: an arming that went wrong must not turn into a fault nobody asked for.

Without the variable the worker has no fault hook at all.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
Tested with tests/test_jobs_faults.py.
"""
from __future__ import annotations

import json
import os
import signal
import time
from collections.abc import Callable
from pathlib import Path

from etf_risk.jobs.events import EventLog

FAULT_FILE_ENV = "ETF_RISK_FAULT_FILE"
ACTIONS = ("kill", "hold")


def _kill_self() -> None:
    os.kill(os.getpid(), signal.SIGKILL)


class FaultFile:
    """The worker's fault hook: Worker(fault=FaultFile(path, events))."""

    def __init__(self, path: str | Path, events: EventLog, *, points: tuple[str, ...] | None = None,
                 kill: Callable[[], None] = _kill_self, sleep: Callable[[float], None] = time.sleep,
                 clock: Callable[[], float] = time.monotonic, tick: float = 0.1):
        if points is None:
            from etf_risk.jobs.worker import WORKER_FAULT_POINTS
            points = WORKER_FAULT_POINTS
        self.path, self.events, self.points = Path(path), events, points
        self._kill, self._sleep, self._clock, self._tick = kill, sleep, clock, tick

    def __call__(self, point: str) -> None:
        try:
            text = self.path.read_text()
        except FileNotFoundError:
            return
        except OSError as error:
            self.events.log("fault_refused", point=point, error=f"{type(error).__name__}: {error}")
            return
        try:
            spec = json.loads(text)
            armed, action = spec["point"], spec["action"]
            if armed not in self.points or action not in ACTIONS:
                raise ValueError(f"unknown point {armed!r} or action {action!r}")
            if action == "hold" and not spec.get("release"):
                raise ValueError("a hold needs a release path")
        except (ValueError, KeyError, TypeError) as error:
            self.path.unlink(missing_ok=True)
            self.events.log("fault_refused", point=point, error=f"{type(error).__name__}: {error}")
            return
        if armed != point:
            return
        self.path.unlink(missing_ok=True)                    # once: gone before it acts
        self.events.log("fault_injected", point=point, action=action)
        if action == "kill":
            self._kill()
            return                                           # reached only when kill is replaced (tests)
        release, timeout = Path(spec["release"]), spec.get("timeout_s")
        end = None if timeout is None else self._clock() + float(timeout)
        while not release.exists():
            if end is not None and self._clock() >= end:
                self.events.log("fault_released", point=point, why="timeout")
                return
            self._sleep(self._tick)
        self.events.log("fault_released", point=point, why="released")


def fault_from_environment(events: EventLog) -> FaultFile | None:
    """The hook for the worker command: a FaultFile when ETF_RISK_FAULT_FILE is set, else None."""
    path = os.environ.get(FAULT_FILE_ENV)
    return FaultFile(path, events) if path else None


def arm(path: str | Path, point: str, action: str = "kill", *, release: str | Path | None = None,
        timeout_s: float | None = None) -> None:
    """Write a fault for FaultFile to find (the harness's side), atomically."""
    spec = {"point": point, "action": action}
    if release is not None:
        spec["release"] = str(release)
    if timeout_s is not None:
        spec["timeout_s"] = timeout_s
    path = Path(path)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(spec))
    tmp.replace(path)
```

## 40. Assistant — 2026-10-24T07:22:51.742Z

### Tool call: Bash

```
{
  "command": "sed -n 1,130p src/etf_risk/jobs/harness.py",
  "description": "Read the harness header, settings and planning code"
}
```

## 41. Assistant — 2026-10-24T07:22:53.081Z

### Tool call: Bash

```
{
  "command": "sed -n 215,625p src/etf_risk/jobs/harness.py",
  "description": "Read the harness record helpers, Tracker and Batch"
}
```

## 42. User — 2026-10-24T07:22:54.365Z

### Tool result

```
    per_case = {case: case_seconds(case, timing, settings, a) for case in settings.cases}
    total = sum(per_case[case] for case in plan["jobs"]) + a.batch_fixed_s
    return {"assumptions": asdict(a), "per_case_s": per_case, "jobs": len(plan["jobs"]), "batch_s": total}


# Reading the records

def events_named(events: list[dict], name: str, **fields_) -> list[dict]:
    return [e for e in events if e.get("event") == name and all(e.get(k) == v for k, v in fields_.items())]


def owner(logs: dict[str, list[dict]], alive: set[str], partition: int = PARTITION) -> str | None:
    """The live worker that holds the partition by its assignment events: its latest assigned
    event lists the partition and no later revoked or lost event, or restart, took it away.
    None when no live worker, or more than one, holds it."""
    holders = []
    for worker, events in logs.items():
        holds = False
        for e in events:
            kind = e.get("event")
            if kind == "started":
                holds = False
            elif kind == "assigned":
                holds = any(p[1] == partition for p in e.get("partitions", []))
            elif kind in ("revoked", "lost") and any(p[1] == partition for p in e.get("partitions", [])):
                holds = False
        if holds and worker in alive:
            holders.append(worker)
    return holders[0] if len(holders) == 1 else None


def worker_accepts(logs: dict[str, list[dict]]) -> list[tuple]:
    """worker_accepts rows (crosscheck.sql): one per accepted event, with the log's identity."""
    return [(e.get("store_id"), e.get("worker_id"), e.get("pid"), e["job_id"], e["attempt"], e["digest"])
            for events in logs.values() for e in events_named(events, "accepted")]


class PeakBook:
    """Memory peaks by segment (4.6): a restart or a stop resets a container's memory.peak, so a
    reading before it closes a segment. A container's batch peak is the maximum of its readings;
    a reading that failed leaves its segment unknown and the batch peak incomplete."""

    def __init__(self):
        self.readings: dict[str, list[dict]] = {}

    def add(self, service: str, peak_bytes: int | None, limit_bytes: int | None, closes: str | None) -> dict:
        reading = {"peak_bytes": peak_bytes, "limit_bytes": limit_bytes, "closes": closes}
        self.readings.setdefault(service, []).append(reading)
        return reading

    def batch_peak(self, service: str) -> dict:
        readings = self.readings.get(service, [])
        known = [r["peak_bytes"] for r in readings if r["peak_bytes"] is not None]
        limit = next((r["limit_bytes"] for r in readings if r["limit_bytes"]), None)
        peak = max(known) if known else None
        return {"peak_bytes": peak, "limit_bytes": limit, "readings": len(readings),
                "incomplete": not readings or len(known) < len(readings),
                "fraction": None if peak is None or not limit else peak / limit}


def memory_verdict(fraction: float | None, settings: Settings) -> str:
    """P4: ok, flag (past flag_fraction) or stop (past stop_fraction); unknown without a reading."""
    if fraction is None:
        return "unknown"
    return "stop" if fraction > settings.stop_fraction else "flag" if fraction > settings.flag_fraction else "ok"


def crosscheck_statements(text: str | None = None) -> list[tuple[str, str]]:
    """The statements of crosscheck.sql below its separator, in order, each named DDL or Q0-Q3b."""
    lines = (CROSSCHECK_SQL.read_text() if text is None else text).splitlines(keepends=True)
    start = next(i for i, line in enumerate(lines) if _SEPARATOR.match(line)) + 1
    statements, current = [], []
    for line in lines[start:]:
        current.append(line)
        stripped = line.strip()
        if stripped.endswith(";") and not stripped.startswith("--"):
            sql = "".join(current).strip()
            name = next((m.group(1) for row in sql.splitlines() if (m := _QUERY_NAME.match(row))), "DDL")
            statements.append((name, sql))
            current = []
    return statements


def fingerprint_from_export(folder: Path) -> dict:
    """Q0's four numbers, from an export's jobs.json and job_attempts.json."""
    jobs = json.loads((folder / "jobs.json").read_text())
    attempts = json.loads((folder / "job_attempts.json").read_text())
    return {"n_jobs": len(jobs), "sum_version": sum(int(j["version"]) for j in jobs),
            "n_attempts": len(attempts), "sum_renewals": sum(int(a["renewals"]) for a in attempts)}


def csv_value(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, datetime):
        return value.isoformat(sep=" ", timespec="microseconds")
    if isinstance(value, (date, Decimal)):
        return str(value)
    return str(value)


def clock_pair() -> dict:
    """ts and mono read together, for the clock check (4.1)."""
    return {"ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"), "mono": time.monotonic()}


# The batch

class PhaseMissed(Exception):
    """An injection did not land in its phase; the job is recorded as a miss and still followed."""


class Tracker(threading.Thread):
    """Follows one job: the deadline observation when it finishes or at its deadline, whichever
    comes first (4.3), then until it is finished or its drain limit has passed (2.5)."""

    def __init__(self, batch: Batch, job_id: int, deadline_mono: float, drain_until: float):
        super().__init__(daemon=True)
        self.batch, self.job_id, self.deadline_mono, self.drain_until = batch, job_id, deadline_mono, drain_until
        self.observation: dict | None = None
        self.final: str | None = None
        self.finished_mono: float | None = None

    def run(self) -> None:
        while True:
            now, status = time.monotonic(), self.batch.job_status(self.job_id)
            if self.observation is None and (status in TERMINAL or now >= self.deadline_mono):
                self.observation = self.batch.observe(self.job_id)
            if status in TERMINAL:
                self.final, self.finished_mono = status, now
                return
            if now >= self.drain_until:
                return
            time.sleep(self.batch.settings.poll_s)


class Batch:
    def __init__(self, plan: dict, out: Path):
        from etf_risk import services
        self.plan, self.out, self.services = plan, out, services
        self.settings = Settings.from_dict(plan["settings"])
        self.timing = timing_of(self.settings)
        self.mysql_url = os.environ.get("ETF_RISK_MYSQL_URL", services.DEFAULT_MYSQL_URL).rstrip("/")
        self.bootstrap = os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", services.DEFAULT_KAFKA_BOOTSTRAP)
        self.db = f"{self.mysql_url}/etf_recovery"
        self.topic = f"etf-recovery-{secrets.token_hex(4)}"
        self.events_dir, self.jobs_root, self.faults_dir, self.logs_dir = (
            out / "events", out / "jobs", out / "faults", out / "logs")
        for folder in (self.events_dir, self.jobs_root, self.faults_dir, self.logs_dir):
            folder.mkdir(parents=True, exist_ok=True)
        self.env = {**os.environ, "ETF_RISK_JOBS_DB": self.db, "ETF_RISK_KAFKA_BOOTSTRAP": self.bootstrap,
                    "ETF_RISK_JOBS_TOPIC": self.topic}
        self.env.pop(faults.FAULT_FILE_ENV, None)
        self.log = EventLog(out / "harness.jsonl", "harness", batch=out.name)
        self.procs: dict[str, subprocess.Popen] = {}
        self.peaks = PeakBook()
        self.batch_jobs: list[tuple] = []
        self.observations: list[tuple] = []
        self.stop_reason: str | None = None
        self.store_id: str | None = None
        self._local = threading.local()                 # a JobStore per thread: a connection is not shared
        self._publisher = None

    # Commands and services

    def common_args(self) -> list[str]:
        args = ["--output-root", str(self.jobs_root), "--processed-root", str(REPO_ROOT / "data" / "processed"),
                "--events", str(self.events_dir)]
        for override in self.settings.timing:
            args += ["--timing", override]
        return args

    def cli(self, *argv: str, check: bool = True, timeout: float = 180) -> subprocess.CompletedProcess:
        out = subprocess.run([sys.executable, "-m", "etf_risk.jobs", *argv, *self.common_args()], env=self.env,
                             capture_output=True, text=True, timeout=timeout)
        if check and out.returncode != 0:
            raise RuntimeError(f"{argv[0]}: exit {out.returncode}: {out.stderr.strip()[-500:]}")
        return out

    def compose(self, *args: str, timeout: float = 300) -> float:
        """Run docker compose on this project's file; the seconds it took."""
        start = time.monotonic()
        out = subprocess.run(["docker", "compose", "-f", str(self.services.COMPOSE_FILE), *args],
                             capture_output=True, text=True, timeout=timeout)
        if out.returncode != 0:
            raise RuntimeError(f"docker compose {' '.join(args)}: exit {out.returncode}: {out.stderr.strip()[-500:]}")
        return time.monotonic() - start

    def wait_ready(self, service: str) -> float:
        """Until the service works again (services.py); the harness's mono at that moment."""
        check = {"mysql": lambda: self.services.mysql_ready(self.mysql_url),
                 "kafka": lambda: self.services.kafka_ready(self.bootstrap)}[service]
        self.services.wait_until_ready(service, check, timeout=180)
        return time.monotonic()

    def services_up(self) -> None:
        existing = subprocess.run(["docker", "compose", "-f", str(self.services.COMPOSE_FILE), "ps", "-a", "-q"],
                                  capture_output=True, text=True, timeout=60).stdout.split()
        if existing:
            raise RuntimeError("this project's containers exist already; a batch starts on fresh ones")
        self.log.log("services_up", seconds=self.compose("up", "-d", "--wait", "mysql", "kafka"),
                     others=self.services.other_containers())
        for service in ("mysql", "kafka"):
            self.wait_ready(service)

    def read_peaks(self, closes: str | None = None) -> str:
        """Both containers' memory.peak (4.6); the worst verdict of P4."""
        verdicts = []
        for service in ("mysql", "kafka"):
            peak = self.services.memory_peak(service)
            self.peaks.add(service, peak.peak_bytes, peak.limit_bytes, closes)
            verdict = memory_verdict(self.peaks.batch_peak(service)["fraction"], self.settings)
            verdicts.append(verdict)
            self.log.log("peaks", service=service, peak_bytes=peak.peak_bytes, limit_bytes=peak.limit_bytes,
                         closes=closes, verdict=verdict)
        return "stop" if "stop" in verdicts else "flag" if "flag" in verdicts else "ok"

    # Processes

    def start(self, name: str, *argv: str, extra_env: dict | None = None) -> subprocess.Popen:
        before = time.monotonic()
        log = open(self.logs_dir / f"{name}.log", "ab")
        proc = subprocess.Popen([sys.executable, "-m", "etf_risk.jobs", *argv, *self.common_args()],
                                env={**self.env, **(extra_env or {})}, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        self.procs[name] = proc
        self._check_start(name, proc, before)
        return proc

    def _check_start(self, name: str, proc: subprocess.Popen, before: float) -> None:
        """The process's started event, and the same-clock check of 4.1."""
        path = self.events_dir / (f"{name}.jsonl" if name in WORKERS else f"reconciler-{proc.pid}.jsonl")
        started = self.wait_for(lambda: next(iter(events_named(read_events(path) if path.exists() else [],
                                                               "started", pid=proc.pid)), None),
                                60, f"{name}'s started event")
        after = time.monotonic()
        self.log.log("process_started", name=name, pid=proc.pid, before=before, after=after,
                     first_mono=started["mono"], same_clock=before <= started["mono"] <= after,
                     code=started.get("code"))

    def fault_file(self, worker: str) -> Path:
        return self.faults_dir / f"{worker}.fault"

    def start_worker(self, name: str) -> None:
        self.fault_file(name).unlink(missing_ok=True)
        self.start(name, "worker", "--worker-id", name, extra_env={faults.FAULT_FILE_ENV: str(self.fault_file(name))})

    def alive(self) -> set[str]:
        return {w for w in WORKERS if w in self.procs and self.procs[w].poll() is None}

    def worker_logs(self) -> dict[str, list[dict]]:
        return {w: read_events(p) if (p := self.events_dir / f"{w}.jsonl").exists() else [] for w in WORKERS}

    def current_owner(self) -> str | None:
        return owner(self.worker_logs(), self.alive())

    def wait_owner(self, timeout: float = 120) -> str:
        """The partition's owner, once the assignment events name exactly one live worker."""
        return self.wait_for(self.current_owner, timeout, "a single owner of the partition")

    def wait_joined(self, worker: str, timeout: float = 120) -> str:
        """After a worker starts: its first assigned event (its join, and so the rebalance it
        caused, completed), then the owner. An owner read earlier could be a stale one."""
        pid = self.procs[worker].pid
        self.wait_for(lambda: events_named(self.worker_logs()[worker], "assigned", pid=pid), timeout,
                      f"worker {worker}'s first assignment")
        return self.wait_owner(timeout)

    def wait_for(self, predicate, timeout: float, what: str):
        """predicate()'s first true value; a lost database connection counts as not yet."""
        end = time.monotonic() + timeout
        while True:
            try:
                value = predicate()
            except Exception as error:
                from etf_risk.jobs.mysql import MYSQL
                if not MYSQL.is_disconnect(error):
                    raise
                value = None
            if value:
                return value
            if time.monotonic() >= end:
                raise PhaseMissed(f"timed out waiting for {what}")
            time.sleep(self.settings.poll_s)

    # The job table, read by the harness

    def store(self):
        """This thread's JobStore; it reconnects at its next operation after a lost connection."""
        store = getattr(self._local, "store", None)
        if store is None:
            from etf_risk.jobs import mysql
            from etf_risk.jobs.store import JobStore
            store = self._local.store = JobStore(None, mysql.MYSQL,
                                                 connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))
        return store

    def job_status(self, job_id: int) -> str | None:
        try:
            job = self.store().job(job_id)
        except Exception:
            return None
        return None if job is None else job["status"].value

    def observe(self, job_id: int) -> dict:
        """The deadline observation (4.3): one consistent snapshot of the job's row, in a
        connection of the harness's own; a failed read is kept with no status."""
        from etf_risk.jobs import mysql
        record = {"job_id": job_id, "status": None, "attempt_number": None, "accepted_attempt": None}
        observed_from = observed_to = time.monotonic()
        try:
            conn = mysql.connect_mysql(self.db, connect_timeout=3, read_timeout=5, write_timeout=5)
            try:
                with conn.cursor() as cursor:
                    observed_from = time.monotonic()
                    cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
                    observed_to = time.monotonic()
                    cursor.execute("SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = %s",
                                   (job_id,))
                    row = cursor.fetchone()
                    cursor.execute("COMMIT")
            finally:
                conn.close()
            if row is not None:
                record.update(status=row[0], attempt_number=row[1], accepted_attempt=row[2])
        except Exception as error:
            observed_to = time.monotonic()
            record["error"] = f"{type(error).__name__}: {error}"[:300]
        record.update(observed_from_mono=observed_from, observed_to_mono=observed_to)
        self.observations.append((job_id, observed_from, observed_to, record["status"], record["attempt_number"],
                                  record["accepted_attempt"]))
        self.log.log("observation", **record)
        return record

    # Phases

    def claim_of(self, job_id: int) -> dict | None:
        """The job's latest claimed event in either worker's log, with the worker's name."""
        claims = [{**e, "worker": w} for w, events in self.worker_logs().items()
                  for e in events_named(events, "claimed", job_id=job_id)]
        return max(claims, key=lambda e: e["mono"]) if claims else None

    def attempt_dir(self, run_id: str) -> Path:
        return self.jobs_root / self.store_id / run_id

    def spark_running(self, job_id: int) -> dict | None:
        """The claim whose spark_pipeline step has started (its event and its log) and not ended."""
        claim = self.claim_of(job_id)
        if claim is None:
            return None
        events = self.worker_logs()[claim["worker"]]
        mine = {"job_id": job_id, "attempt": claim["attempt"], "step": "spark_pipeline"}
        if not events_named(events, "step_started", **mine) or events_named(events, "step_ended", **mine):
            return None
        return claim if (self.attempt_dir(claim["run_id"]) / "logs" / "spark_pipeline.log").exists() else None

    def fault_event(self, worker: str, job_id: int, point: str) -> dict | None:
        """The fault_injected event at point in the worker's log, if it followed this job's delivery."""
        events = self.worker_logs()[worker]
        for i, e in enumerate(events):
            if e.get("event") == "fault_injected" and e.get("point") == point:
                earlier = [x for x in events[:i] if x.get("event") in ("delivered", "claimed")]
                if earlier and earlier[-1].get("job_id") == job_id:
                    return e
        return None

    def wait_fault(self, armed: str, job_id: int, point: str) -> dict:
        """The armed worker's fault_injected event for this job; a miss as soon as the other
        worker claims the job first (the owner changed after the arming)."""
        def found():
            if event := self.fault_event(armed, job_id, point):
                return event
            claim = self.claim_of(job_id)
            if claim is not None and claim["worker"] != armed:
                raise PhaseMissed(f"job {job_id} was claimed by worker {claim['worker']}, not the armed {armed}")
            return None
        return self.wait_for(found, self.settings.phase_timeout_s, f"the fault at {point}")

    def at_mid_step(self, job_id: int) -> dict:
        claim = self.wait_for(lambda: self.spark_running(job_id), self.settings.phase_timeout_s,
                              f"job {job_id}'s spark_pipeline step")
        time.sleep(self.settings.phase_delay_s)
        if self.spark_running(job_id) is None:
            raise PhaseMissed("spark_pipeline ended during the phase delay")
        return claim

    # Injections (3.1)

    def submit(self) -> int | None:
        s = self.settings
        out = self.cli("submit", "--snapshot", s.snapshot, "--kind", s.kind, "--stride", str(s.stride),
                       "--max-attempts", str(s.max_attempts), check=False)
        if out.returncode != 0:
            self.log.log("submit_failed", exit=out.returncode, stderr=out.stderr.strip()[-300:])
            return None
        record = json.loads(out.stdout.strip().splitlines()[-1])
        self.log.log("submitted", **record)
        return record["job_id"]

    def publish_again(self, job_id: int) -> bool:
        if self._publisher is None:
            from etf_risk.jobs.kafka import KafkaPublisher
            self._publisher = KafkaPublisher(self.bootstrap, self.topic, timing=self.timing)
        return self._publisher.publish(job_id)

    def stop_tree(self, worker: str, run_id: str) -> list:
        import psutil
        frozen = [psutil.Process(self.procs[worker].pid)]
        for value, procs in processes.marked_processes().items():
            parsed = processes.parse_marker(value)
            if parsed is not None and parsed[0] == self.store_id and parsed[1] == run_id:
```

## 43. User — 2026-10-24T07:22:54.377Z

### Tool result

```
"""The session harness of the recovery experiments E1 and E2 (docs/recovery-experiments.md).

    uv run --group jobs python -m etf_risk.jobs.harness plan --seed N --out PLAN.json [--settings FILE]
    uv run --group jobs python -m etf_risk.jobs.harness estimate --plan PLAN.json
    uv run --group jobs python -m etf_risk.jobs.harness batch --plan PLAN.json --out DIR

plan fixes a batch before it runs (8.1): its jobs in an order shuffled from the seed, the case
of each, the settings and the code identity. Settings holds every value that section 8 of the
outline leaves provisional (timing, repetitions, deadlines, the harness's waits, the memory
thresholds); a settings file (JSON) replaces any of them, and the plan records the values used.

estimate prints a plan's expected duration, from the design's windows (3.2) and the
assumptions it names (Assumptions); none of them is measured.

batch runs one plan on fresh containers (2.1-2.5):
- the services, the job database and a topic of its own; the reference run under the host lock,
  through the launcher (2.2); the reconciler; worker A, then worker B, each waited for in the
  assignment events (2.4);
- for each job: the fault armed or the injection made (3.1), the deadline recorded (4.2) and
  observed when the job finishes or at the deadline, whichever comes first (4.3), the job
  followed to its end or its drain limit (2.5), killed or stopped workers restarted (2.4), and
  the memory peaks read, with the thresholds of P4 (4.6);
- then quiescence (4.4), the final snapshot with crosscheck.sql (4.5), and the services
  removed.
Its records go to DIR (section 9): harness.jsonl (the harness's own events), events/ (every
process's log), jobs/ (the attempts' folders), reference/, logs/, crosscheck/*.csv, export/,
status-check.txt, and plan.json.

No batch has run: Part A is not approved, and no formal experiment has been run. The offline
parts are tested with tests/test_jobs_harness.py.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import random
import re
import secrets
import signal
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from etf_risk.jobs import faults, processes
from etf_risk.jobs.events import EventLog, read_events
from etf_risk.jobs.reconciler import PUBLICATION_GRACE, RECONCILE_INTERVAL
from etf_risk.jobs.timing import Timing
from etf_risk.provenance import REPO_ROOT, code_identity

CASES = ("C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "W6", "W7", "K1", "K2", "D1", "D2", "X1")
HOOKS = {"W1": ("before_claim", "kill"), "W2": ("after_claim", "kill"), "W4": ("after_pipeline", "kill"),
         "W5a": ("after_accept_commit", "kill"), "W5b": ("after_accept", "kill"), "D2": ("after_pipeline", "hold")}
MID_STEP = ("W3", "W6", "W7", "K1", "D1")       # injected once the attempt's spark_pipeline step runs
NO_NEW_ATTEMPT = ("C0", "W5a", "W5b", "K1", "X1")
FROM_RESTORED = ("K2", "D1", "D2")              # deadline counted from the service's return (4.2)
WORKERS = ("A", "B")
PARTITION = 0
TERMINAL = ("succeeded", "failed")
CROSSCHECK_SQL = Path(__file__).with_name("crosscheck.sql")
QUERIES = ("Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b")
_SEPARATOR = re.compile(r"^-- -{20,}\s*$")
_QUERY_NAME = re.compile(r"^-- (Q\w+)\.")


# Settings and plans

@dataclass(frozen=True)
class Settings:
    """The provisional values of the outline's section 8 (P1-P4) and the harness's waits (8.5)."""
    snapshot: str = "full-2026-10-12"
    kind: str = "calendar-year"          # P1: every case on the calendar-year job
    stride: int = 21
    max_attempts: int = 3
    jobs_per_case: int = 3               # P1
    cases: tuple[str, ...] = CASES
    timing: tuple[str, ...] = ()         # --timing overrides; P2: none
    slowest_steps_s: float = 35.1        # S (P3): M2's slowest windows + spark_pipeline + verify, calendar-year
    deadline_margin: float = 2.0         # P3: D = B + margin * S, rounded up
    deadline_round_s: float = 5.0
    max_lag_s: float = 1.0               # P3
    phase_delay_s: float = 3.0           # 8.5: after spark_pipeline starts, before a mid-step injection
    w7_stop_s: float = 90.0              # 8.5: how long W7's tree stays stopped (longer than a takeover)
    outage_s: float = 30.0               # 8.5: how long K2, D1 and D2 keep their service stopped
    flag_fraction: float = 0.90          # P4
    stop_fraction: float = 0.95          # P4
    poll_s: float = 0.5
    phase_timeout_s: float = 300.0       # the longest wait for an injection's phase; then it is missed

    @classmethod
    def from_dict(cls, data: dict) -> Settings:
        unknown = sorted(set(data) - {f.name for f in fields(cls)})
        if unknown:
            raise ValueError(f"unknown settings: {unknown}")
        settings = cls(**{k: tuple(v) if k in ("cases", "timing") else v for k, v in data.items()})
        if bad := sorted(set(settings.cases) - set(CASES)):
            raise ValueError(f"unknown cases: {bad}")
        return settings


def timing_of(settings: Settings) -> Timing:
    from etf_risk.jobs.cli import timing_from
    return timing_from(list(settings.timing))


def plan_jobs(settings: Settings, seed: int) -> list[str]:
    """The batch's cases in run order: jobs_per_case of each case, shuffled with the seed."""
    jobs = [case for case in settings.cases for _ in range(settings.jobs_per_case)]
    random.Random(seed).shuffle(jobs)
    return jobs


def deadline_reference(case: str) -> str:
    """What a job's deadline counts from (4.2): its submit, its injection, or its service's return."""
    return "submit" if case == "C0" else "restored" if case in FROM_RESTORED else "injection"


def bound_to_next_run(case: str, timing: Timing, settings: Settings) -> float:
    """B (P3): the latest the design starts the job's next run, from the deadline's reference.
    K2, D1 and D2 count from their service's return, since how long a restart takes is not
    known and is not inferred."""
```

## 44. Assistant — 2026-10-24T07:23:04.137Z

### Tool call: Bash

```
{
  "command": "sed -n 800,997p src/etf_risk/jobs/harness.py",
  "description": "Read the harness reference run, crosscheck and batch run"
}
```

## 45. User — 2026-10-24T07:23:04.863Z

### Tool result

```
            run_id = "reference"

        work, logs = run_dir / ".work", run_dir / "logs"
        for folder in (work / "tmp", work / "spark", work / "jtmp", logs):
            folder.mkdir(parents=True, exist_ok=True)
        marker = processes.marker(self.store_id, "reference", secrets.token_hex(8))
        env = pipeline.step_env(work, marker)
        for name, argv in pipeline.commands(params, Reference, run_dir)[:2]:
            limit = self.timing.step_limit(name)
            command = [sys.executable, "-m", "etf_risk.jobs.launcher", "--marker", marker, "--lock", str(DEFAULT_LOCK),
                       "--registry", str(pipeline.registry), "--lock-wait", str(self.timing.lock_wait(name)),
                       "--step-limit", str(limit), "--cwd", str(work), "--step-log", str(logs / f"{name}.log"),
                       "--result", str(logs / f"{name}.launcher.json"), "--", *argv]
            before = time.monotonic()
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, env=env, cwd=work, start_new_session=True,
                                    stdout=open(logs / f"{name}.launcher.log", "ab"), stderr=subprocess.STDOUT)
            deadline = time.monotonic() + self.timing.lock_wait(name) + limit + 30
            proc.stdin.write((json.dumps({"monotonic": time.monotonic(), "seq": 0, "deadline": deadline}) + "\n").encode())
            proc.stdin.flush()
            code = proc.wait(timeout=deadline - time.monotonic() + 30)
            proc.stdin.close()
            self.log.log("reference_step", step=name, exit=code, before=before, after=time.monotonic())
            if code != 0:
                raise RuntimeError(f"the reference run's {name} step failed (exit {code})")

    def quiesce(self) -> dict:
        """4.4: SIGKILL every writer, then wait until no attempt's process and no other client
        connection is left."""
        for proc in self.procs.values():
            if proc.poll() is None:
                os.kill(proc.pid, signal.SIGKILL)
        for proc in self.procs.values():
            proc.wait(timeout=30)
        try:                                                  # each launcher ends its tree on EOF
            self.wait_for(lambda: not self._marked(), self.timing.watchdog_tick + self.timing.kill_grace + 10,
                          "the attempts' processes to end")
            processes_left = False
        except PhaseMissed:
            processes_left = True
        from etf_risk.jobs import mysql
        conn = mysql.connect_mysql(self.db)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT CONNECTION_ID()")
                me = cursor.fetchone()[0]
                cursor.execute("SHOW FULL PROCESSLIST")
                others = [row for row in cursor.fetchall()
                          if row[0] != me and row[4] != "Daemon" and row[1] not in ("event_scheduler", "system user")]
        finally:
            conn.close()
        record = {"processes_left": processes_left, "other_connections": len(others)}
        self.log.log("quiescent", **record)
        return record

    def _marked(self) -> bool:
        return any(v.startswith(f"{self.store_id}:") for v in processes.marked_processes())

    def crosscheck(self) -> dict:
        """4.5, step 3: the harness's records in TEMPORARY tables, then Q0-Q3b in one consistent
        snapshot, each saved as CSV; Q0's fingerprint."""
        from etf_risk.jobs import mysql
        folder = self.out / "crosscheck"
        folder.mkdir(exist_ok=True)
        statements = crosscheck_statements()
        conn = mysql.connect_mysql(self.db)
        fingerprint = {}
        try:
            with conn.cursor() as cursor:
                for name, sql in statements:
                    if name == "DDL":
                        cursor.execute(sql)
                cursor.executemany("INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono,"
                                   " max_lag_s) VALUES (%s, %s, %s, %s, %s, %s)", self.batch_jobs)
                cursor.executemany("INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono,"
                                   " status, attempt_number, accepted_attempt) VALUES (%s, %s, %s, %s, %s, %s)",
                                   self.observations)
                cursor.executemany("INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number,"
                                   " result_digest) VALUES (%s, %s, %s, %s, %s, %s)", worker_accepts(self.worker_logs()))
                cursor.execute("START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY")
                for name, sql in statements:
                    if name == "DDL":
                        continue
                    cursor.execute(sql)
                    columns = [d[0] for d in cursor.description]
                    rows = cursor.fetchall()
                    with open(folder / f"{name}.csv", "w", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows([[csv_value(v) for v in row] for row in rows])
                    if name == "Q0":
                        fingerprint = {c: int(v) for c, v in zip(columns, rows[0])}
                cursor.execute("COMMIT")
        finally:
            conn.close()
        return fingerprint

    def q0(self) -> dict:
        from etf_risk.jobs import mysql
        sql = dict(crosscheck_statements())["Q0"]
        conn = mysql.connect_mysql(self.db)
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                columns = [d[0] for d in cursor.description]
                return {c: int(v) for c, v in zip(columns, cursor.fetchone())}
        finally:
            conn.close()

    def final_snapshot(self) -> dict:
        """4.5: peaks, status --check, the cross-check, the export, and Q0 again."""
        self.read_peaks(closes="end")
        status = self.cli("status", "--check", check=False)
        (self.out / "status-check.txt").write_text(f"exit {status.returncode}\n{status.stdout}{status.stderr}")
        first = self.crosscheck()
        self.cli("export", str(self.out / "export"))
        exported = fingerprint_from_export(self.out / "export")
        again = self.q0()
        record = {"status_check_exit": status.returncode, "fingerprints": [first, exported, again],
                  "fingerprints_agree": first == exported == again,
                  "batch_peaks": {s: self.peaks.batch_peak(s) for s in ("mysql", "kafka")}}
        self.log.log("final_snapshot", **record)
        return record

    def run(self) -> int:
        """The batch: start, every planned job until one is left unfinished or memory stops it,
        quiescence, the final snapshot, and the services removed."""
        self.log.log("batch_started", plan_seed=self.plan["seed"], code=code_identity(), clock=clock_pair(),
                     settings=asdict(self.settings), topic=self.topic)
        self.services_up()
        try:
            self.cli("init-db")
            self.cli("create-topic")
            self.store_id = self.store().store_id()
            self.reference_run()
            self.start("reconciler", "reconciler")
            self.start_worker("A")
            self.log.log("owner", owner=self.wait_joined("A"), position=0)
            self.start_worker("B")
            self.log.log("owner", owner=self.wait_joined("B"), position=0)
            for position, case in enumerate(self.plan["jobs"], start=1):
                if self.stop_reason is not None:
                    self.log.log("not_run", position=position, case=case, why=self.stop_reason)
                    continue
                try:
                    record = self.run_job(position, case)
                    if record.get("final") is None:
                        self.stop_reason = "an unfinished job" if record.get("job_id") else "a submit that failed"
                        continue
                    self.after_job(record)
                except Exception as error:                   # recorded; the batch still ends cleanly
                    self.log.log("job_error", position=position, case=case, error=f"{type(error).__name__}: {error}")
                    self.stop_reason = "an error in the harness"
            try:
                self.quiesce()
                self.final_snapshot()
            except Exception as error:
                self.log.log("final_error", error=f"{type(error).__name__}: {error}")
                self.stop_reason = self.stop_reason or "an error in the final snapshot"
        finally:
            for proc in self.procs.values():
                if proc.poll() is None:
                    proc.kill()
            self.log.log("batch_ended", clock=clock_pair(), code=code_identity(), stop_reason=self.stop_reason)
            self.compose("down", "-v")
        return 0


# Command line

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs.harness", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("plan", help="fix a batch: its shuffled jobs and its settings")
    plan.add_argument("--seed", type=int, required=True)
    plan.add_argument("--out", type=Path, required=True)
    plan.add_argument("--settings", type=Path, help="JSON replacing any of the default settings")
    est = commands.add_parser("estimate", help="the plan's expected duration, from stated assumptions")
    est.add_argument("--plan", type=Path, required=True)
    batch = commands.add_parser("batch", help="run one plan on fresh containers")
    batch.add_argument("--plan", type=Path, required=True)
    batch.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "plan":
        settings = Settings.from_dict(json.loads(args.settings.read_text())) if args.settings else Settings()
        args.out.write_text(json.dumps(make_plan(settings, args.seed), indent=2) + "\n")
        print(f"plan written to {args.out}")
        return 0
    plan_data = json.loads(args.plan.read_text())
    if args.command == "estimate":
        print(json.dumps(estimate(plan_data), indent=2))
        return 0
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "plan.json").write_text(json.dumps(plan_data, indent=2) + "\n")
    return Batch(plan_data, args.out).run()


if __name__ == "__main__":
    sys.exit(main())
```

## 46. Assistant — 2026-10-24T07:23:08.741Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py"
}
```

## 47. User — 2026-10-24T07:23:09.040Z

### Tool result

```
1	"""Collect one batch of the recovery experiments E1 and E2 (docs/recovery-experiments.md,
2	sections 5 and 6).
3	
4	A batch folder is what etf_risk.jobs.harness batch wrote:
5	
6	    harness.jsonl   the harness's events: plan, injections, deadlines, observations, peaks, owners
7	    events/         the workers' logs (A.jsonl, B.jsonl), the reconciler's, and submit.jsonl
8	    jobs/<store>/   the attempts' folders, with logs/*.launcher.json and, when complete, manifest.json
9	    reference/      the reference run, under the launcher
10	    crosscheck/     Q0-Q3b as CSV (crosscheck.sql)
11	    export/         the job tables as JSON (python -m etf_risk.jobs export)
12	    plan.json       the plan the batch ran
13	
14	Run from the repository root:
15	
16	    uv run python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/batch-1
17	
18	It writes into the batch folder:
19	- injections.csv: one row per planned job, with the case, the injection, the metrics of
20	  section 5, each n/a with its reason or unknown when its record is missing, and the verdicts of
21	  Q1, Q2 and Q3a;
22	- tally.csv: per case, the jobs planned, made, missed and not run, and every verdict value of
23	  Q1, Q2, deadline_met, Q3a and Q3b, with zeros;
24	- validity.json: the checks of 6.1 (what counts) and, apart from them, the outcome checks of
25	  6.2-6.5, each with what it found.
26	It prints a summary and exits with 1 if a validity check fails. A failed outcome check is a
27	finding: it is reported and never changes the exit code. Nothing is dropped: a missed or
28	unrun job keeps its row.
29	
30	Durations are differences of mono values, from one host's monotonic clock (4.1). Step
31	intervals come from the launcher records, which hold UTC times only at 6d8a232, so the overlap
32	verdict holds only with a passed clock check (6.5).
33	
34	AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
35	Tested with tests/test_recovery_collector.py on synthetic batch folders; no real batch exists.
36	"""
37	from __future__ import annotations
38	
39	import argparse
40	import csv
41	import importlib.util
42	import json
43	import statistics
44	import sys
45	from datetime import datetime
46	from pathlib import Path
47	
48	from etf_risk.jobs.events import read_events
49	
50	REPO = Path(__file__).resolve().parents[1]
51	CASES = ("C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "W6", "W7", "K1", "K2", "D1", "D2", "X1")
52	REQUEUED_DETECTION = ("W2", "W3", "W4", "W6", "W7")
53	NO_RECOVERY = {"C0": "no failure", "X1": "no failure", "W5a": "after acceptance", "W5b": "after acceptance"}
54	NO_OVERHEAD = {"W5a": "after acceptance", "W5b": "after acceptance"}
55	Q1_VERDICTS = ("ok", "not finished", "failed", "more than one accepted attempt", "succeeded without an accepted attempt",
56	               "accepted_attempt names another attempt", "accepted attempt of a job that did not succeed",
57	               "attempt rows differ from attempt_number", "finished with an attempt still running")
58	Q2_CLASSES = ("on time", "late", "unfinished", "failed", "missing", "deadline not observed")
59	DEADLINE_MET = ("yes", "no", "unknown")
60	Q3A_VERDICTS = ("reported once", "no matching report", "one attempt reported more than once",
61	                "acceptance reported for more than one attempt")
62	Q3B_VERDICTS = ("matches", "other store", "no such attempt", "wrong worker", "attempt not accepted", "wrong digest")
63	LIVENESS = ("serve_restarted", "retry", "rewound", "gave_up", "failed_after_ack", "consumer_error", "pass_failed")
64	FIELDS = ["position", "case", "job_id", "status", "missed", "injection", "worker", "t_inj", "reference", "deadline_s",
65	          "detection_s", "rerun_s", "finish_s", "overhead_s", "claims", "accepted", "executions", "complete_executions",
66	          "wasted_step_s", "fenced_events", "timeliness", "deadline_met", "q1_verdict", "q3a_verdict"]
67	
68	
69	# Reading the folder
70	
71	def jsonl(path: Path) -> list[dict]:
72	    return read_events(path) if path.exists() else []
73	
74	
75	def named(events: list[dict], name: str, **fields_) -> list[dict]:
76	    return [e for e in events if e.get("event") == name and all(e.get(k) == v for k, v in fields_.items())]
77	
78	
79	def csv_rows(path: Path) -> list[dict]:
80	    if not path.exists():
81	        return []
82	    with open(path, newline="") as f:
83	        return [{k: None if v == "NULL" else v for k, v in row.items()} for row in csv.DictReader(f)]
84	
85	
86	def by_job(rows: list[dict]) -> dict[int, dict]:
87	    return {int(r["job_id"]): r for r in rows if r.get("job_id") is not None}
88	
89	
90	class BatchFolder:
91	    def __init__(self, folder: Path):
92	        self.folder = folder
93	        self.harness = jsonl(folder / "harness.jsonl")
94	        self.workers = {p.stem: read_events(p) for p in sorted((folder / "events").glob("*.jsonl"))
95	                        if p.stem != "submit" and not p.stem.startswith("reconciler-")}
96	        self.reconciler = [e for p in sorted((folder / "events").glob("reconciler-*.jsonl")) for e in read_events(p)]
97	        self.submits = jsonl(folder / "events" / "submit.jsonl")
98	        self.plan = json.loads((folder / "plan.json").read_text())
99	        self.q = {name: csv_rows(folder / "crosscheck" / f"{name}.csv") for name in ("Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b")}
100	        export = folder / "export"
101	        self.jobs = json.loads((export / "jobs.json").read_text()) if (export / "jobs.json").exists() else []
102	        self.attempts = (json.loads((export / "job_attempts.json").read_text())
103	                         if (export / "job_attempts.json").exists() else [])
104	        store = json.loads((export / "store.json").read_text()) if (export / "store.json").exists() else {}
105	        self.store_id = store.get("store_id")
106	
107	    def worker_events(self) -> list[dict]:
108	        return [{**e, "worker": w} for w, events in self.workers.items() for e in events]
109	
110	    def first_after(self, events: list[dict], t: float) -> dict | None:
111	        later = [e for e in events if e.get("mono") is not None and e["mono"] >= t]
112	        return min(later, key=lambda e: e["mono"]) if later else None
113	
114	    def attempt_dir(self, run_id: str) -> Path:
115	        return self.folder / "jobs" / (self.store_id or "") / run_id
116	
117	
118	# Metrics (section 5)
119	
120	def utc_seconds(start: str, end: str) -> float:
121	    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()
122	
123	
124	def launcher_record(folder: Path, step: str) -> dict | None:
125	    path = folder / "logs" / f"{step}.launcher.json"
126	    try:
127	        return json.loads(path.read_text())
128	    except (OSError, json.JSONDecodeError):
129	        return None
130	
131	
132	def step_intervals(b: BatchFolder) -> tuple[list[tuple], list[str]]:
133	    """Every started step's interval (UTC), and the steps that lack one (6.5)."""
134	    intervals, missing = [], []
135	    claims = {(e["job_id"], e["attempt"]): e["run_id"] for e in named(b.worker_events(), "claimed")}
136	    for e in named(b.worker_events(), "step_started"):
137	        run_id = claims.get((e["job_id"], e["attempt"]))
138	        record = launcher_record(b.attempt_dir(run_id), e["step"]) if run_id else None
139	        label = f"{run_id or e['job_id']}:{e['step']}"
140	        if record and record.get("step_started_at_utc") and record.get("tree_ended_at_utc"):
141	            intervals.append((record["step_started_at_utc"], record["tree_ended_at_utc"], label))
142	        else:
143	            missing.append(label)
144	    for step in ("windows", "spark_pipeline"):
145	        record = launcher_record(b.folder / "reference", step)
146	        if record and record.get("step_started_at_utc") and record.get("tree_ended_at_utc"):
147	            intervals.append((record["step_started_at_utc"], record["tree_ended_at_utc"], f"reference:{step}"))
148	        else:
149	            missing.append(f"reference:{step}")
150	    return sorted(intervals), missing
151	
152	
153	def overlap_verdict(intervals: list[tuple], missing: list[str]) -> dict:
154	    """no overlap, overlap, or unknown: a missing interval never counts as no overlap (6.5)."""
155	    overlaps = [(a[2], b_[2]) for a, b_ in zip(intervals, intervals[1:])
156	                if datetime.fromisoformat(b_[0]) < datetime.fromisoformat(a[1])]
157	    verdict = "overlap" if overlaps else "unknown" if missing else "no overlap"
158	    return {"verdict": verdict, "overlaps": overlaps, "steps_without_interval": missing,
159	            "note": "UTC launcher times; valid only with a passed clock check"}
160	
161	
162	def job_metrics(b: BatchFolder, position: int, case: str, injection: dict, deadline: dict,
163	                c0_median: float | None) -> dict:
164	    job_id = deadline["job_id"]
165	    events = [e for e in b.worker_events() if e.get("job_id") == job_id]
166	    t_inj, missed = injection.get("t_inj"), injection.get("missed")
167	    row = {"detection_s": None, "rerun_s": None, "finish_s": None, "overhead_s": None}
168	    reason = NO_RECOVERY.get(case)
169	    if missed:
170	        row.update(detection_s="n/a: injection missed", rerun_s="n/a: injection missed")
171	    elif reason:
172	        row.update(detection_s=f"n/a: {reason}", rerun_s=f"n/a: {reason}")
173	    elif case == "K1":
174	        row.update(detection_s="n/a for the job: the attempt goes on", rerun_s="n/a: the attempt goes on")
175	    elif t_inj is not None:
176	        if case == "W1":
177	            detection = b.first_after([e for e in named(events, "delivered") if e["worker"] != injection.get("worker")],
178	                                      t_inj)
179	        elif case in REQUEUED_DETECTION:
180	            detection = b.first_after(named(b.reconciler, "requeued", job_id=job_id), t_inj)
181	        elif case == "K2":
182	            detection = b.first_after(named(b.reconciler, "published", job_id=job_id), t_inj)
183	        elif case == "D1":
184	            detection = b.first_after(named(events, "renewal_failed"), t_inj)
185	        else:                                                     # D2
186	            detection = b.first_after(named(events, "retry", operation="accept_result"), t_inj)
187	        row["detection_s"] = detection["mono"] - t_inj if detection else "unknown: no detection event"
188	        before = [e for e in named(events, "claimed") if e["mono"] < t_inj]
189	        injected = max((e["attempt"] for e in before), default=0)
190	        rerun = b.first_after([e for e in named(events, "claimed") if e["attempt"] > injected], t_inj)
191	        if rerun:
192	            row["rerun_s"] = rerun["mono"] - t_inj
193	        elif case in ("D1", "D2"):
194	            row["rerun_s"] = "n/a: the attempt went on"
195	        else:
196	            row["rerun_s"] = "unknown: no new claim"
197	    accepted = min(named(events, "accepted"), key=lambda e: e["mono"], default=None)
198	    start = deadline.get("t_submit") if case == "C0" or missed else t_inj
199	    if case in NO_OVERHEAD and not missed:
200	        row["finish_s"] = row["overhead_s"] = f"n/a: {NO_OVERHEAD[case]}"
201	    elif accepted is None:
202	        row["finish_s"] = row["overhead_s"] = "unknown: no accepted event"
203	    else:
204	        row["finish_s"] = accepted["mono"] - start if start is not None else "unknown"
205	        if deadline.get("t_submit") is not None and c0_median is not None:
206	            row["overhead_s"] = accepted["mono"] - deadline["t_submit"] - c0_median
207	        else:
208	            row["overhead_s"] = "unknown: no C0 median"
209	    claims = {e["attempt"]: e["run_id"] for e in named(events, "claimed")}
210	    row["executions"] = len({e["attempt"] for e in named(events, "step_started", step="windows")})
211	    row["complete_executions"] = sum(1 for run_id in claims.values() if (b.attempt_dir(run_id) / "manifest.json").exists())
212	    row["fenced_events"] = len(named(events, "fenced")) + len(named(events, "renewal_refused"))
213	    row["wasted_step_s"] = wasted_step_time(b, job_id, claims)
214	    return row
215	
216	
217	def wasted_step_time(b: BatchFolder, job_id: int, claims: dict[int, str]) -> float | str:
218	    """The step time of the job's attempts that were not accepted; unknown if a started step has
219	    no complete launcher record."""
220	    accepted = {a["attempt_number"] for a in b.attempts if a["job_id"] == job_id and a["outcome"] == "accepted"}
221	    total = 0.0
222	    for e in named(b.worker_events(), "step_started", job_id=job_id):
223	        if e["attempt"] in accepted:
224	            continue
225	        record = launcher_record(b.attempt_dir(claims.get(e["attempt"], "")), e["step"])
226	        if not record or not record.get("step_started_at_utc") or not record.get("tree_ended_at_utc"):
227	            return f"unknown: no complete record for attempt {e['attempt']} {e['step']}"
228	        total += utc_seconds(record["step_started_at_utc"], record["tree_ended_at_utc"])
229	    return total
230	
231	
232	# Checks (section 6)
233	
234	def identity_check(b: BatchFolder) -> dict:
235	    """6.1: one code identity across the harness, every process start and every step launch."""
236	    seen = []
237	    for e in named(b.harness, "batch_started") + named(b.harness, "batch_ended"):
238	        seen.append(("harness", e.get("code")))
239	    for e in named(b.harness, "process_started"):
240	        seen.append((e.get("name"), e.get("code")))
241	    for e in named(b.submits, "started"):
242	        seen.append(("submit", e.get("code")))
243	    for e in named(b.worker_events(), "step_started"):
244	        seen.append((f"{e['worker']} step", e.get("code")))
245	    pairs = {(c.get("source_digest"), c.get("uv_lock_sha256")) if c else None for _, c in seen}
246	    return {"passed": len(pairs) == 1 and None not in pairs, "distinct": len(pairs), "records": len(seen)}
247	
248	
249	def clock_check(b: BatchFolder, tolerance_s: float) -> dict:
250	    start, end = named(b.harness, "batch_started"), named(b.harness, "batch_ended")
251	    if not start or not end:
252	        return {"passed": False, "why": "no batch_started or batch_ended event"}
253	    a, z = start[0]["clock"], end[-1]["clock"]
254	    difference = utc_seconds(a["ts"], z["ts"]) - (z["mono"] - a["mono"])
255	    same = [e.get("same_clock") for e in named(b.harness, "process_started")]
256	    return {"passed": abs(difference) <= tolerance_s and all(same), "ts_minus_mono_s": difference,
257	            "tolerance_s": tolerance_s, "processes_on_the_same_clock": f"{sum(map(bool, same))} of {len(same)}"}
258	
259	
260	def accepted_checks(b: BatchFolder) -> list[dict]:
261	    """6.2 items 3 and 4 for every accepted attempt: the digest, the result rule from the files,
262	    and the tables against the reference run by content."""
263	    from etf_risk import runs
264	    from etf_risk.jobs.pipeline import TABLES, total_violations
265	    ccm = _caching_collector()
266	    reference = next(iter(sorted((b.folder / "reference" / "output").glob("*/*/reference"))), None)
267	    found = []
268	    for a in (a for a in b.attempts if a["outcome"] == "accepted"):
269	        folder = Path(a["output_dir"])
270	        problems = []
271	        try:
272	            record = json.loads((folder / "attempt.json").read_text())
273	            run_folder = folder / record["run_folder"]
274	        except (OSError, json.JSONDecodeError, KeyError):
275	            found.append({"job_id": a["job_id"], "problems": ["no readable attempt.json"]})
276	            continue
277	        if runs.folder_digest(run_folder) != a["result_digest"]:
278	            problems.append("the folder's digest differs from the accepted digest")
279	        run, checks, verified = (_json(run_folder / n) for n in ("run.json", "checks.json", "verify.json"))
280	        if run.get("status") != "ok" or not checks or total_violations(checks):
281	            problems.append("run.json or checks.json is not ok")
282	        if not verified or verified.get("mismatch_count") or not verified.get("breached_windows", {}).get("same"):
283	            problems.append("verify.json is not clean")
284	        if missing := [t for t in TABLES if not (run_folder / t / "_SUCCESS").is_file()]:
285	            problems.append(f"no _SUCCESS in {missing}")
286	        if reference is None:
287	            problems.append("no reference run to compare with")
288	        else:
289	            for table, key in ccm.TABLE_KEYS.items():
290	                diff, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(run_folder, table),
291	                                                 key, ccm.cpm.BREACH_FIELDS.get(table, []))
292	                problems += [f"{table}: {p}" for p in diff]
293	        found.append({"job_id": a["job_id"], "attempt": a["attempt_number"], "problems": problems})
294	    return found
295	
296	
297	def _json(path: Path) -> dict:
298	    try:
299	        value = json.loads(path.read_text())
300	    except (OSError, json.JSONDecodeError):
301	        return {}
302	    return value if isinstance(value, dict) else {}
303	
304	
305	def _caching_collector():
306	    sys.path.insert(0, str(REPO / "analysis"))
307	    spec = importlib.util.spec_from_file_location("collect_caching_measurements",
308	                                                  REPO / "analysis" / "collect_caching_measurements.py")
309	    module = importlib.util.module_from_spec(spec)
310	    spec.loader.exec_module(module)
311	    return module
312	
313	
314	def input_check(b: BatchFolder, processed_root: Path) -> dict:
315	    """6.1: the snapshot's input checksums now equal those every job recorded at submit."""
316	    from etf_risk.jobs.params import input_checksums
317	    settings = b.plan["settings"]
318	    try:
319	        now = input_checksums(processed_root, settings["snapshot"])
320	    except Exception as error:
321	        return {"passed": False, "why": f"{type(error).__name__}: {error}"}
322	    differ = [j["job_id"] for j in b.jobs if j.get("input_checksums") != now]
323	    return {"passed": not differ, "jobs_differing": differ}
324	
325	
326	# The batch
327	
328	def collect(folder: Path, clock_tolerance_s: float = 1.0, processed_root: Path = REPO / "data" / "processed") -> dict:
329	    b = BatchFolder(folder)
330	    deadlines = {e["position"]: e for e in named(b.harness, "deadline")}
331	    injections = {e["position"]: e for e in named(b.harness, "injection")}
332	    not_run = {e["position"]: e for e in named(b.harness, "not_run")}
333	    not_submitted = {e["position"]: e for e in named(b.harness, "job_not_submitted")}
334	    q1, q2, q3a = by_job(b.q["Q1"]), by_job(b.q["Q2"]), by_job(b.q["Q3a"])
335	    c0 = []
336	    for position, e in deadlines.items():
337	        accepted = min(named([x for x in b.worker_events() if x.get("job_id") == e["job_id"]], "accepted"),
338	                       key=lambda x: x["mono"], default=None)
339	        if e["case"] == "C0" and accepted is not None:
340	            c0.append(accepted["mono"] - e["t_submit"])
341	    c0_median = statistics.median(c0) if c0 else None
342	    rows = []
343	    for position, case in enumerate(b.plan["jobs"], start=1):
344	        row = {"position": position, "case": case}
345	        if position in not_run or position in not_submitted:
346	            row["status"] = "not run" if position in not_run else "not submitted"
347	            rows.append(row)
348	            continue
349	        if position not in deadlines:
350	            row["status"] = "no record"
351	            rows.append(row)
352	            continue
353	        d, inj = deadlines[position], injections.get(position, {})
354	        job_id = d["job_id"]
355	        row.update(job_id=job_id, status="made" if not inj.get("missed") else "missed", missed=inj.get("missed"),
356	                   injection=inj.get("kind"), worker=inj.get("worker"), t_inj=inj.get("t_inj"),
357	                   reference=d["reference"], deadline_s=d["deadline_s"])
358	        row.update(job_metrics(b, position, case, inj, d, c0_median))
359	        row.update(claims=(q1.get(job_id) or {}).get("n_claims"), accepted=(q1.get(job_id) or {}).get("n_accepted"),
360	                   q1_verdict=(q1.get(job_id) or {}).get("verdict"), timeliness=(q2.get(job_id) or {}).get("timeliness"),
361	                   deadline_met=(q2.get(job_id) or {}).get("deadline_met"),
362	                   q3a_verdict=(q3a.get(job_id) or {}).get("log_verdict"))
363	        rows.append(row)
364	    intervals, missing = step_intervals(b)
365	    final = (named(b.harness, "final_snapshot") or [{}])[-1]
366	    quiescent = (named(b.harness, "quiescent") or [{}])[-1]
367	    validity = {
368	        "injections": {"planned": len(rows), "made": sum(r.get("status") == "made" for r in rows),
369	                       "missed": [r["position"] for r in rows if r.get("status") == "missed"],
370	                       "not_run": [r["position"] for r in rows if r.get("status") in ("not run", "not submitted")]},
371	        "code_identity": identity_check(b),
372	        "clock": clock_check(b, clock_tolerance_s),
373	        "fingerprints_agree": {"passed": bool(final.get("fingerprints_agree")), "values": final.get("fingerprints")},
374	        "inputs_unchanged": input_check(b, processed_root),
375	        "machine_state": {"passed": None, "why": "not recorded: 8.3 leaves the host-state rules open"},
376	    }
377	    validity_failed = [name for name, check in validity.items()
378	                       if isinstance(check, dict) and check.get("passed") is False]
379	    outcomes = {
380	        "q1_not_ok": [r["job_id"] for r in rows if r.get("q1_verdict") not in (None, "ok")],
381	        "status_check_exit": final.get("status_check_exit"),
382	        "invariant_violations": _json(folder / "export" / "invariant_violations.json") if
383	        (folder / "export" / "invariant_violations.json").exists() else "no export",
384	        "accepted_attempts": accepted_checks(b),
385	        "overlap": overlap_verdict(intervals, missing),
386	        "nothing_left": {"processes_left": quiescent.get("processes_left"),
387	                         "other_connections": quiescent.get("other_connections")},
388	        "q2b_rows": b.q["Q2b"],
389	        "q3b_not_matching": [r for r in b.q["Q3b"] if r.get("report_verdict") != "matches"],
390	        "liveness": {name: len(named(b.worker_events() + b.reconciler, name)) for name in LIVENESS},
391	        "batch_peaks": final.get("batch_peaks"),
392	    }
393	    return {"rows": rows, "tally": tally(rows, b), "validity": validity, "validity_failed": validity_failed,
394	            "outcomes": outcomes, "c0_median_s": c0_median}
395	
396	
397	def tally(rows: list[dict], b: BatchFolder) -> list[dict]:
398	    """Per case: planned, made, missed, not run, and every verdict value, with zeros."""
399	    q3b_case = {}
400	    cases_by_job = {r["job_id"]: r["case"] for r in rows if r.get("job_id") is not None}
401	    for r in b.q["Q3b"]:
402	        case = cases_by_job.get(int(r["job_id"])) if r.get("job_id") else None
403	        q3b_case.setdefault(case, []).append(r.get("report_verdict"))
404	    out = []
405	    for case in CASES:
406	        mine = [r for r in rows if r["case"] == case]
407	        entry = {"case": case, "planned": len(mine), "made": sum(r.get("status") == "made" for r in mine),
408	                 "missed": sum(r.get("status") == "missed" for r in mine),
409	                 "not_run": sum(r.get("status") in ("not run", "not submitted", "no record") for r in mine),
410	                 "claims": sum(int(r["claims"]) for r in mine if r.get("claims") is not None)}
411	        for prefix, values, column in (("q1", Q1_VERDICTS, "q1_verdict"), ("q2", Q2_CLASSES, "timeliness"),
412	                                       ("met", DEADLINE_MET, "deadline_met"), ("q3a", Q3A_VERDICTS, "q3a_verdict")):
413	            for value in values:
414	                entry[f"{prefix}: {value}"] = sum(r.get(column) == value for r in mine)
415	        for value in Q3B_VERDICTS:
416	            entry[f"q3b: {value}"] = q3b_case.get(case, []).count(value)
417	        out.append(entry)
418	    return out
419	
420	
421	def write(folder: Path, result: dict) -> None:
422	    with open(folder / "injections.csv", "w", newline="") as f:
423	        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
424	        writer.writeheader()
425	        writer.writerows(result["rows"])
426	    with open(folder / "tally.csv", "w", newline="") as f:
427	        writer = csv.DictWriter(f, fieldnames=list(result["tally"][0]))
428	        writer.writeheader()
429	        writer.writerows(result["tally"])
430	    (folder / "validity.json").write_text(json.dumps(
431	        {k: result[k] for k in ("validity", "validity_failed", "outcomes", "c0_median_s")}, indent=2, default=str) + "\n")
432	
433	
434	def main(argv: list[str] | None = None) -> int:
435	    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
436	    parser.add_argument("--batch", type=Path, required=True)
437	    parser.add_argument("--clock-tolerance", type=float, default=1.0,
438	                        help="seconds (provisional; the outline's 8.5 leaves it open)")
439	    parser.add_argument("--processed-root", type=Path, default=REPO / "data" / "processed",
440	                        help="where the snapshot's input files are checked again (default data/processed)")
441	    args = parser.parse_args(argv)
442	    result = collect(args.batch, args.clock_tolerance, args.processed_root)
443	    write(args.batch, result)
444	    v = result["validity"]["injections"]
445	    print(f"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run")
446	    print("validity: " + ("all checks passed" if not result["validity_failed"]
447	                          else "FAILED: " + ", ".join(result["validity_failed"])))
448	    print(f"overlap: {result['outcomes']['overlap']['verdict']}; jobs whose Q1 verdict is not ok:"
449	          f" {result['outcomes']['q1_not_ok'] or 'none'}")
450	    return 1 if result["validity_failed"] else 0
451	
452	
453	if __name__ == "__main__":
454	    sys.exit(main())
455	
```

## 48. Assistant — 2026-10-24T07:23:18.306Z

Now the monotonic launcher timestamps. Checking who reads the launcher result first:

## 49. Assistant — 2026-10-24T07:23:20.020Z

### Tool call: Bash

```
{
  "command": "grep -rn -E 'step_started_at_utc|tree_ended_at_utc|step_started_mono|tree_ended_mono' --include=*.py --include=*.md . | grep -v '^./.venv' | head -30",
  "description": "Find every reader of the launcher's step times"
}
```

## 50. User — 2026-10-24T07:23:20.798Z

### Tool result

```
(eval):1: no matches found: --include=*.py
```

## 51. Assistant — 2026-10-24T07:23:24.840Z

### Tool call: Bash

```
{
  "command": "grep -rn -E 'step_started_at_utc|tree_ended_at_utc|step_started_mono|tree_ended_mono' src tests analysis docs | head -30",
  "description": "Find every reader of the launcher's step times"
}
```

## 52. User — 2026-10-24T07:23:25.713Z

### Tool result

```
src/etf_risk/jobs/launcher.py:236:                self.result["step_started_at_utc"] = datetime.now(timezone.utc).isoformat()
src/etf_risk/jobs/launcher.py:258:            self.result["tree_ended_at_utc"] = datetime.now(timezone.utc).isoformat()   # no member left
tests/test_recovery_collector.py:42:        {"outcome": "exited", "step_started_at_utc": utc(start), "tree_ended_at_utc": utc(end)}))
tests/test_jobs_live_pipeline.py:251:        if result.get("step_started_at_utc") and result.get("tree_ended_at_utc"):
tests/test_jobs_live_pipeline.py:252:            intervals.append((datetime.fromisoformat(result["step_started_at_utc"]),
tests/test_jobs_live_pipeline.py:253:                              datetime.fromisoformat(result["tree_ended_at_utc"]), str(path)))
tests/test_jobs_live_pipeline.py:329:    assert datetime.fromisoformat(two["step_started_at_utc"]) >= datetime.fromisoformat(one["tree_ended_at_utc"])
analysis/collect_recovery_measurements.py:140:        if record and record.get("step_started_at_utc") and record.get("tree_ended_at_utc"):
analysis/collect_recovery_measurements.py:141:            intervals.append((record["step_started_at_utc"], record["tree_ended_at_utc"], label))
analysis/collect_recovery_measurements.py:146:        if record and record.get("step_started_at_utc") and record.get("tree_ended_at_utc"):
analysis/collect_recovery_measurements.py:147:            intervals.append((record["step_started_at_utc"], record["tree_ended_at_utc"], f"reference:{step}"))
analysis/collect_recovery_measurements.py:226:        if not record or not record.get("step_started_at_utc") or not record.get("tree_ended_at_utc"):
analysis/collect_recovery_measurements.py:228:        total += utc_seconds(record["step_started_at_utc"], record["tree_ended_at_utc"])
```

## 53. Assistant — 2026-10-24T07:23:32.678Z

### Tool call: Bash

```
{
  "command": "sed -n 1,30p tests/test_jobs_live_pipeline.py && echo ---- && sed -n 238,262p tests/test_jobs_live_pipeline.py && echo ---- && sed -n 300,335p tests/test_jobs_live_pipeline.py && git log --oneline -3 -- tests/test_jobs_live_pipeline.py",
  "description": "Read the live pipeline test's overlap checks"
}
```

## 54. User — 2026-10-24T07:23:33.503Z

### Tool result

```
"""M2's acceptance runs against the services: workers and a reconciler started as
`python -m etf_risk.jobs` processes, real jobs on the full-2026-10-12 snapshot (data/processed),
and failures injected on purpose. They take minutes per case, so they run only with
ETF_RISK_LIVE_PIPELINE=1 as well as ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP (README
runbook), and each module run uses a database and a topic of its own.

The lease is 24 s here, renewed every 4 s, so F = m0 + 14 s: the same relations as the
defaults (etf_risk.jobs.timing), on a shorter clock. Every case ends with check():
- the job succeeded, with exactly one accepted attempt;
- that attempt's recorded digest equals its run folder's digest;
- its tables equal a reference run's by content;
- invariant_violations() is empty;
- no two launchers' step intervals overlap, across every attempt of the module;
- no process of any attempt is left.

AI contribution: written with Claude Code (Opus 5.5).
"""
import importlib.util
import json
import os
import secrets
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import psutil
----
    job is A's, whatever partition assignment the group would have made with both present."""
    a = stack.worker("A")
    job = stack.submit(CALENDAR)
    wait_until(lambda: stack.store.attempts(job), 300, "worker A's claim")
    assert stack.store.attempts(job)[0]["worker_id"] == "A"
    stack.worker("B")
    return a, job


def launcher_intervals(stack) -> list[tuple[datetime, datetime, str]]:
    intervals = []
    for path in sorted((stack.output / stack.store_id).glob("job-*-attempt-*/logs/*.launcher.json")):
        result = json.loads(path.read_text())
        if result.get("step_started_at_utc") and result.get("tree_ended_at_utc"):
            intervals.append((datetime.fromisoformat(result["step_started_at_utc"]),
                              datetime.fromisoformat(result["tree_ended_at_utc"]), str(path)))
    return sorted(intervals)


def check(stack, references, job, params, *, attempts=None):
    j = stack.store.job(job)
    rows = stack.store.attempts(job)
    accepted = [a for a in rows if a["outcome"] is Outcome.ACCEPTED]
    assert j["status"] is Status.SUCCEEDED and len(accepted) == 1, (j, rows)
    if attempts is not None:
----
    a.kill()                                                       # SIGKILL: the lifeline (EOF) ends the tree
    wait_until(lambda: not attempt_procs(stack, first["run_id"]), 7 + 3, "the end of attempt 1's tree")
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    _, record = check(stack, references, job, CALENDAR, attempts=2)
    assert [r["outcome"] for r in stack.store.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    result = json.loads((run_dir(stack, first) / "logs" / "spark_pipeline.launcher.json").read_text())
    assert result["outcome"] == "eof"


def test_a_stopped_worker_is_outlived_by_its_watchdog_and_fenced_when_it_resumes(services, references):
    """Worker-only SIGSTOP during step 2. Before SIGCONT: attempt 1's tree is gone by its
    deadline plus the kill grace; attempt 2's Spark step started after attempt 1's tree
    ended; attempt 1's renewal count no longer changes. After SIGCONT, worker A is fenced
    and writes nothing."""
    stack = services
    a, job = claimed_by_a(stack)                                    # then B joins as a standby
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    os.kill(a.pid, signal.SIGSTOP)
    stopped = time.monotonic()
    first = stack.store.attempts(job)[0]
    wait_until(lambda: not attempt_procs(stack, first["run_id"]), 14 + 0.5 + 7 + 5,
               "the watchdog to end attempt 1's tree")
    assert time.monotonic() - stopped <= 14 + 0.5 + 7 + 5          # F is at most 14 s after the last renewal
    wait_until(lambda: finished(stack, job), 600, f"job {job}")   # attempt 2, by worker B, while A is stopped
    rows = stack.store.attempts(job)
    renewals_at_takeover = rows[0]["renewals"]
    one = json.loads((run_dir(stack, rows[0]) / "logs" / "spark_pipeline.launcher.json").read_text())
    two = json.loads((run_dir(stack, rows[1]) / "logs" / "spark_pipeline.launcher.json").read_text())
    assert one["outcome"] == "deadline"
    assert datetime.fromisoformat(two["step_started_at_utc"]) >= datetime.fromisoformat(one["tree_ended_at_utc"])
    os.kill(a.pid, signal.SIGCONT)
    wait_until(lambda: any(e["event"] == "fenced" for e in stack.events("A")), 60, "worker A to see it was fenced")
    time.sleep(3)
    assert stack.store.attempts(job)[0]["renewals"] == renewals_at_takeover
    check(stack, references, job, CALENDAR, attempts=2)

dd041c1 Add M2's acceptance runs, the standby test and ten more mutations
```

## 55. Assistant — 2026-10-24T07:23:48.540Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'UTC|overlap|monotonic|_utc|step_started|tree_ended' docs/recovery-experiments.md | head -40",
  "description": "Find the outline's clock and overlap passages"
}
```

## 56. User — 2026-10-24T07:23:50.501Z

### Tool result

```
92:then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference
100:reconciler, each `submit`), each step launch records it in `step_started`, and the harness records
139:event logs (for W3: after the attempt's `step_started` for `spark_pipeline`, before its
190:Every duration is a difference of two `time.monotonic()` readings on this host: the events' `mono`
196:a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock columns, never for a
236:-- observed_from_mono: the harness's time.monotonic() just before the next statement
277:Durations are monotonic (4.1); t_inj is the harness's `mono` at the injection.
287:| executions per job | attempts with a `step_started` for `windows`; complete ones have a `manifest.json`, written only after the result rule held; required of none | event logs, attempt folders |
349:- **No overlapping Spark steps.** Every started step and every reference run needs a complete
351:  `unknown`, never `no overlap`. Intervals are compared in monotonic time once the launcher records
352:  it; at `6d8a232` it records UTC times only, and their comparison holds only with a passed clock
372:Q1 deliberately overlaps the store's seven `INVARIANT_QUERIES`: a second reading of the same rows by
502:isolated check; monotonic step times in the launcher records, which none of the four reviews asked
503:for and without which the overlap check compares UTC times (6.5); and the branches: the tooling and
527:- **Not done:** monotonic step times in the launcher records (8.5), mutation checks for the new
548:  and the new case W5a; code identity at launch and unknown intervals; monotonic durations and `n/a`
```

## 57. Assistant — 2026-10-24T07:23:54.793Z

### Tool call: Bash

```
{
  "command": "sed -n 186,200p docs/recovery-experiments.md; echo ----; sed -n 344,356p docs/recovery-experiments.md; echo ----; sed -n 494,565p docs/recovery-experiments.md",
  "description": "Read the clock, overlap and open-items passages"
}
```

## 58. User — 2026-10-24T07:23:55.527Z

### Tool result

```
## 4. Clocks, deadlines and snapshots

### 4.1 Clock

Every duration is a difference of two `time.monotonic()` readings on this host: the events' `mono`
([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step
times once it records them (section 9). On macOS this reads a system-wide clock; the launcher's
handshake checks the worker and its launchers, and the harness checks each process it starts (the
`mono` of its first event must lie between the harness's readings just before the start and just
after it read that event). The clock pauses while the host sleeps, so the host must not sleep during
a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock columns, never for a
duration. The harness records `ts` and `mono` together at the start and end of a batch; a difference
in their elapsed times beyond a tolerance (8.5) means a sleep or a clock step and fails validity
(6.1).

----
`pid` against the `claimed` event of the same attempt. A report contradicting the table does not
change E1's answer (6.2) but is reported next to it.

### 6.5 Other outcome checks

- **No overlapping Spark steps.** Every started step and every reference run needs a complete
  interval, start to tree end, in its launcher record; a missing or incomplete one makes the verdict
  `unknown`, never `no overlap`. Intervals are compared in monotonic time once the launcher records
  it; at `6d8a232` it records UTC times only, and their comparison holds only with a passed clock
  check.
- **Nothing left.** After quiescence no attempt's process and no new Spark scratch remain (as
  `check()`).

----
  is new, written with Claude Code, with offline tests written and not yet run; mutation checks for it
  are not written. Without it, these six cases would be recorded as not run.

### 8.5 Still open

The clock-check tolerance (4.1; the collector uses 1 s until it is decided); the harness's waits
(the phase delay before a mid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep
a service down: the settings hold 3 s, 90 s and 30 s for now); a host-memory gate, after the
isolated check; monotonic step times in the launcher records, which none of the four reviews asked
for and without which the overlap check compares UTC times (6.5); and the branches: the tooling and
these documents are uncommitted on `feature/recovery-harness`, created from `e4adc38`, while the
first copies of the documents, on `docs/recovery-outline`, stay as they were at revision 3.

## 9. Records, prerequisites and authorship

- **Records**, under `data/outputs-recovery/<batch>/`, outside Git: the export, the event logs, the
  harness's logs (injections with intended and verified phases, deadlines and observations, process
  starts and clock checks, partition owners), `services peaks` by segment, the three fingerprints,
  Q0–Q3b as CSV, the table of section 5 with one row per injection, the per-case tally, and
  `cleanup`'s listing.
- **Nothing is dropped.** Every injection (misses and those not run included), every batch (invalid
  ones included) and every verdict (failed outcomes and unknowns included) stays in the records; the
  tally lists all 14 cases and every verdict value, with zeros.
- **Tooling**, uncommitted on `feature/recovery-harness`, written with Claude Code at the author's
  decision of 2026-10-24. Its offline tests are written; none of it has run:
  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs
    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)
    byte for byte (a test checks it);
  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);
  - assignment events in `kafka.py` (2.4);
  - code identity at launch, in `provenance.py`, `cli.py` and `pipeline.py` (2.3);
  - the fault hook, `faults.py`, wired in `cli.py`, and the fault point `after_accept_commit` in
    `worker.py` (8.4).
- **Not done:** monotonic step times in the launcher records (8.5), mutation checks for the new
  code, and any run of it.
- **Authorship.** Spec §11: the job code is written with Claude Code. At the author's decision of
  2026-10-24, Claude Code also writes the recovery experiments' tooling listed above, and each new
  module says so. The items in 1.1, and the experiments' decisions, runs and answers, are the
  author's; everything else here is Claude Code's proposal. The queries of
  [recovery-sql.md](recovery-sql.md) stay marked as drafted with Claude Code.

## 10. Not claimed

Times hold for this machine, the clock of 8.2, and one broker and one database (spec §11). Results
are counts per case, not rates. The bounds in 3.2 hold only under their Kafka conditions and are not
predictions until approved. Cases without an injection method are not measured. The memory budgets
are not validated until the isolated check is done. The fixture run tests the SQL on made-up rows,
not the job system.

## History

- **Draft, 2026-10-23.** Outline drafted with Claude Code at the author's request.
- **Revision 1, 2026-10-23.** The first review (1.1): deadlines and their observation, quiescence
  and the final snapshot; database correctness apart from the event log, with full report identity
  and the new case W5a; code identity at launch and unknown intervals; monotonic durations and `n/a`
  latencies; Kafka conditions, startup order and restart rule; reference runs under the host lock;
  the rule-of-three sentence removed; all cases kept; a first fixture.
- **Revision 2, 2026-10-23.** The second review: `6d8a232` and M2's report as inputs, with the
  isolated memory-budget check pending; peaks by segment; the owner from assignment events only;
  `deadline not observed` as an explicit unknown with `deadline_met`; fixture B and explicit expected
  rows for every query.
- **Revision 3, 2026-10-23.** The third review: the queries validated once against a scratch MySQL
  after the M2 session's handover, with all 82 frozen expected rows matching; the restart duration
  inferred from failed renewals removed; the SQL, fixture, expected rows and run moved to
  [recovery-sql.md](recovery-sql.md) with no SQL changed; the outline shortened; Part A decisions
  proposed in section 8 (P1–P5), Q-A becoming P5.
- **Revision 4, 2026-10-24.** The fourth review: the fixture run accepted as tooling evidence only;
  the tooling written with Claude Code (section 9), none of it run; P3's deadlines reassessed (W7's
  bound, K2, D1 and D2 counted from their service's return, the observation at completion when that
  is first) and the duration of the 84 jobs estimated (8.1); P5 implemented with a fault file
  instead of a fault named in the environment. Timing, repetitions and memory thresholds stay
  provisional.
```

## 59. Assistant — 2026-10-24T07:24:01.995Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py",
  "old_string": "                    child = subprocess.Popen(command, cwd=self.args.cwd, stdin=subprocess.DEVNULL, stdout=log,\n                                             stderr=subprocess.STDOUT, pass_fds=(self.lock_fd,))\n                self.result[\"step_started_at_utc\"] = datetime.now(timezone.utc).isoformat()",
  "new_string": "                    child = subprocess.Popen(command, cwd=self.args.cwd, stdin=subprocess.DEVNULL, stdout=log,\n                                             stderr=subprocess.STDOUT, pass_fds=(self.lock_fd,))\n                self.result[\"step_started_mono\"] = time.monotonic()\n                self.result[\"step_started_at_utc\"] = datetime.now(timezone.utc).isoformat()"
}
```

## 60. Assistant — 2026-10-24T07:24:04.242Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py",
  "old_string": "            self.result[\"returncode\"] = child.returncode\n            self.result[\"tree_ended_at_utc\"] = datetime.now(timezone.utc).isoformat()   # no member left",
  "new_string": "            self.result[\"returncode\"] = child.returncode\n            self.result[\"tree_ended_mono\"] = time.monotonic()                          # no member left\n            self.result[\"tree_ended_at_utc\"] = datetime.now(timezone.utc).isoformat()"
}
```

## 61. Assistant — 2026-10-24T07:24:08.092Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py",
  "old_string": "The result goes to --result as JSON: the outcome, the step's exit code, the processes ended,\nthe time waited for the lock, the tree's peak summed RSS, and the lines accepted and\nignored. The exit code says the outcome: the step's own code (0-63) when it ran to its end,\notherwise one of EXIT_CODES.",
  "new_string": "The result goes to --result as JSON: the outcome, the step's exit code, the processes ended,\nthe time waited for the lock, the tree's peak summed RSS, and the lines accepted and\nignored. A step that started also has its interval, from just after the step's process\nstarted to when no member of the tree was left: step_started_mono and tree_ended_mono, on\nthe host's monotonic clock, which the handshake checked and which same-host overlap checks\ncompare, and the same moments in UTC (*_at_utc), for reading only. The exit code says the\noutcome: the step's own code (0-63) when it ran to its end, otherwise one of EXIT_CODES."
}
```

## 62. User — 2026-10-24T07:24:09.227Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 63. User — 2026-10-24T07:24:10.414Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 64. User — 2026-10-24T07:24:11.560Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/launcher.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 65. Assistant — 2026-10-24T07:24:15.191Z

Status: the deadline check and the monotonic launcher fields are written. Now adding the launcher test.

## 66. Assistant — 2026-10-24T07:24:16.700Z

### Tool call: Bash

```
{
  "command": "sed -n 1,80p tests/test_jobs_launcher.py && grep -n 'def test_' tests/test_jobs_launcher.py",
  "description": "Read the launcher test helpers and test names"
}
```

## 67. User — 2026-10-24T07:24:17.635Z

### Tool result

```
"""The launcher, with real processes: the absolute-deadline watchdog (including lines queued
while it was stopped), the end of the whole tree, the host lock and the survivor check, the
handshake, the step limit and EOF.

A step here is a small Python script. TREE starts what a Spark step looks like to the
launcher: a child that moves to a process group of its own, as PySpark's daemon does, and an
orphan whose parent exits at once. Every test uses its own lock file and registry, never the
host's.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import psutil
import pytest

from etf_risk.jobs.launcher import EXIT_CODES
from etf_risk.jobs.processes import MARKER_ENV, Registry

TREE = r"""
import json, os, subprocess, sys, time
pids = {"step": os.getpid()}
child = subprocess.Popen([sys.executable, "-c", "import os, time; os.setpgid(0, 0); time.sleep(600)"])
pids["moved_group"] = child.pid
while os.getpgid(child.pid) == os.getpgid(0):          # until it has moved to a group of its own
    time.sleep(0.01)
r, w = os.pipe()
if os.fork() == 0:
    if os.fork() == 0:
        os.write(w, str(os.getpid()).encode()); os.close(w)
        time.sleep(600); os._exit(0)
    os._exit(0)
os.close(w)
pids["orphan"] = int(os.read(r, 32)); os.wait()
with open(sys.argv[1] + ".tmp", "w") as f:
    json.dump(pids, f)
os.replace(sys.argv[1] + ".tmp", sys.argv[1])
time.sleep(float(sys.argv[2]))
"""

# A step whose orphan lets go of every inherited descriptor (as the JVM does), then exits.
DETACHED = r"""
import json, os, sys, time
r, w = os.pipe()
if os.fork() == 0:
    if os.fork() == 0:
        for fd in range(3, 256):
            if fd != w:
                try: os.close(fd)
                except OSError: pass
        os.write(w, str(os.getpid()).encode()); os.close(w)
        time.sleep(600); os._exit(0)
    os._exit(0)
os.close(w)
orphan = int(os.read(r, 32)); os.wait()
with open(sys.argv[1] + ".tmp", "w") as f:
    json.dump({"orphan": orphan}, f)
os.replace(sys.argv[1] + ".tmp", sys.argv[1])
time.sleep(float(sys.argv[2]))
"""


class Run:
    """One launcher, started as the worker starts it, and helpers to talk to it."""

    def __init__(self, tmp_path, name, command, *, deadline_in=30.0, seq=0, handshake_offset=0.0,
                 step_limit=60.0, lock_wait=5.0, marker=None, drain=2.0, handshake=True):
        self.name, self.dir = name, tmp_path / name
        self.dir.mkdir(parents=True, exist_ok=True)
        self.marker = marker or f"{'s' * 32}:{name}:{'k' * 16}"
        self.result_path = self.dir / "result.json"
        args = [sys.executable, "-m", "etf_risk.jobs.launcher", "--marker", self.marker,
                "--lock", str(tmp_path / "host.lock"), "--registry", str(tmp_path / "registry"),
                "--lock-wait", str(lock_wait), "--step-limit", str(step_limit), "--cwd", str(self.dir),
139:def test_a_step_that_ends_by_itself_reports_its_exit_code_and_releases_the_lock(tmp_path):
149:def test_at_its_deadline_the_watchdog_ends_the_whole_tree_including_a_moved_group_and_an_orphan(tmp_path):
160:def test_keepalive_lines_move_the_deadline_so_the_step_can_finish(tmp_path):
170:def test_eof_from_the_worker_ends_the_tree(tmp_path):
179:def test_the_step_limit_ends_the_tree(tmp_path):
187:def test_a_sigterm_to_the_launcher_ends_its_tree_first(tmp_path):
196:def test_stopped_past_its_deadline_the_launcher_fires_on_resume_and_queued_lines_change_nothing(tmp_path):
219:def test_stopped_briefly_only_a_newer_later_future_line_moves_the_deadline(tmp_path):
239:def test_the_handshake_must_read_the_same_clock_and_a_live_deadline(tmp_path):
254:def test_the_host_lock_lets_one_step_run_at_a_time(tmp_path):
266:def test_a_survivor_of_a_dead_launchers_tree_blocks_the_next_step_until_it_is_gone(tmp_path):
286:def test_a_lock_held_outside_any_launcher_keeps_the_step_from_starting(tmp_path):
```

## 68. Assistant — 2026-10-24T07:24:22.152Z

### Tool call: Bash

```
{
  "command": "sed -n 80,170p tests/test_jobs_launcher.py && sed -n 250,298p tests/test_jobs_launcher.py",
  "description": "Read the Run helper and the lock tests"
}
```

## 69. User — 2026-10-24T07:24:22.885Z

### Tool result

```
                "--lock-wait", str(lock_wait), "--step-limit", str(step_limit), "--cwd", str(self.dir),
                "--step-log", str(self.dir / "step.log"), "--result", str(self.result_path),
                "--tick", "0.1", "--term-grace", "0.5", "--kill-confirm", "1.0", "--drain", str(drain), "--", *command]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, env={**os.environ, MARKER_ENV: self.marker},
                                     start_new_session=True)
        os.set_blocking(self.proc.stdin.fileno(), False)
        self.deadline = time.monotonic() + deadline_in
        if handshake:
            self.write({"monotonic": time.monotonic() + handshake_offset, "seq": seq, "deadline": self.deadline})

    def write(self, line):
        os.write(self.proc.stdin.fileno(), (json.dumps(line) + "\n").encode())

    def close(self):
        self.proc.stdin.close()

    def wait(self, timeout=30.0):
        code = self.proc.wait(timeout=timeout)
        return code, json.loads(self.result_path.read_text())


def tree(tmp_path, name, seconds=600.0):
    pids_file = tmp_path / f"{name}.pids"
    return [sys.executable, "-c", TREE, str(pids_file), str(seconds)], pids_file


def wait_for(path, timeout=20.0):
    deadline = time.monotonic() + timeout
    while not Path(path).exists():
        assert time.monotonic() < deadline, f"{path} never appeared"
        time.sleep(0.05)
    return json.loads(Path(path).read_text())


def gone(pid):
    try:
        return psutil.Process(pid).status() == psutil.STATUS_ZOMBIE
    except psutil.NoSuchProcess:
        return True


TEST_STORE = "s" * 32                                  # every marker in this file starts with it


@pytest.fixture(autouse=True)
def kill_leftovers():
    """Ends what a failing test left behind: only processes with this file's markers, never
    those of a real worker that may be running on this machine."""
    yield
    from etf_risk.jobs.processes import marked_processes
    for value, procs in marked_processes().items():
        if value.startswith(TEST_STORE + ":"):
            for p in procs:
                try:
                    p.kill()
                except psutil.Error:
                    pass


def test_a_step_that_ends_by_itself_reports_its_exit_code_and_releases_the_lock(tmp_path):
    run = Run(tmp_path, "a", [sys.executable, "-c", "import sys; sys.exit(3)"])
    code, result = run.wait()
    assert (code, result["outcome"], result["returncode"]) == (3, "exited", 3)
    import fcntl
    with open(tmp_path / "host.lock", "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)            # free again
    assert Registry(tmp_path / "registry").entries() == []


def test_at_its_deadline_the_watchdog_ends_the_whole_tree_including_a_moved_group_and_an_orphan(tmp_path):
    command, pids_file = tree(tmp_path, "t")
    run = Run(tmp_path, "t", command, deadline_in=3.0)
    pids = wait_for(pids_file)
    assert os.getpgid(pids["moved_group"]) != os.getpgid(pids["step"])   # what a process-group kill would miss
    code, result = run.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["deadline"], "deadline")
    assert all(gone(pid) for pid in pids.values()) and result["ended"]["remaining"] == []
    assert set(pids.values()) <= set(result["ended"]["terminated"])


def test_keepalive_lines_move_the_deadline_so_the_step_can_finish(tmp_path):
    command, _ = tree(tmp_path, "k", seconds=2.5)
    run = Run(tmp_path, "k", command, deadline_in=1.5)
    for seq in (1, 2, 3):
        time.sleep(0.7)
        run.write({"seq": seq, "deadline": time.monotonic() + 1.5})
    code, result = run.wait()
    assert (code, result["outcome"], result["lines_accepted"]) == (0, "exited", 3)


def test_eof_from_the_worker_ends_the_tree(tmp_path):
    assert silent.wait()[0] == EXIT_CODES["no_handshake"]
    assert not marker.exists()                                   # no step started


def test_the_host_lock_lets_one_step_run_at_a_time(tmp_path):
    command, pids_file = tree(tmp_path, "first")
    first = Run(tmp_path, "first", command)
    wait_for(pids_file)
    started = tmp_path / "second-started"
    second = Run(tmp_path, "second", [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"], lock_wait=1.5)
    code, result = second.wait()
    assert (code, result["outcome"]) == (EXIT_CODES["lock_busy"], "lock_busy") and not started.exists()
    first.close()
    assert first.wait()[1]["outcome"] == "eof"


def test_a_survivor_of_a_dead_launchers_tree_blocks_the_next_step_until_it_is_gone(tmp_path):
    pids_file = tmp_path / "dead.pids"
    dead = Run(tmp_path, "dead", [sys.executable, "-c", DETACHED, str(pids_file), "0.2"], drain=30.0)
    orphan = wait_for(pids_file)["orphan"]
    time.sleep(0.5)                                              # the step has exited; the launcher waits for its orphan
    dead.proc.kill()                                             # the launcher dies, its orphan survives
    dead.proc.wait()
    assert not gone(orphan) and len(Registry(tmp_path / "registry").entries()) == 1
    started = tmp_path / "next-started"
    blocked = Run(tmp_path, "next", [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"], lock_wait=1.5)
    code, result = blocked.wait()
    assert (code, result["outcome"], result["survivors_seen"]) == (EXIT_CODES["lock_busy"], "lock_busy", [orphan])
    assert not started.exists()
    psutil.Process(orphan).kill()
    psutil.Process(orphan).wait(timeout=5)
    after = Run(tmp_path, "after", [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"])
    assert after.wait()[1]["outcome"] == "exited" and started.exists()
    assert Registry(tmp_path / "registry").entries() == []       # the dead launcher's entry was cleaned up


def test_a_lock_held_outside_any_launcher_keeps_the_step_from_starting(tmp_path):
    """The lock, not only the survivor check: a process that is no launcher and has no tree
    in the registry can hold it, as the recovery harness does for its reference runs. It
    also makes "check survivors, register, start" one step across launchers."""
    import fcntl
    started = tmp_path / "started"
    command = [sys.executable, "-c", f"open({str(started)!r}, 'w').close()"]
    (tmp_path / "registry").mkdir()
    with open(tmp_path / "host.lock", "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        code, result = Run(tmp_path, "held", command, lock_wait=1.5).wait()
        assert (code, result["outcome"]) == (EXIT_CODES["lock_busy"], "lock_busy") and not started.exists()
    assert Run(tmp_path, "released", command).wait()[1]["outcome"] == "exited" and started.exists()
```

## 70. Assistant — 2026-10-24T07:24:54.072Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py"
}
```

## 71. User — 2026-10-24T07:24:54.684Z

### Tool result

```
1	"""The recovery collector (analysis/collect_recovery_measurements.py) on synthetic batch folders:
2	the metrics of section 5 with their n/a reasons, unknown intervals, the per-case tally with
3	zeros, and validity apart from outcomes. No real batch exists yet.
4	
5	AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
6	"""
7	import csv
8	import importlib.util
9	import json
10	from datetime import datetime, timedelta, timezone
11	from pathlib import Path
12	
13	import numpy as np
14	import pytest
15	from conftest import nyse_sessions, write_snapshot
16	
17	from etf_risk.jobs.params import input_checksums
18	
19	REPO = Path(__file__).resolve().parents[1]
20	spec = importlib.util.spec_from_file_location("collect_recovery_measurements",
21	                                              REPO / "analysis" / "collect_recovery_measurements.py")
22	crm = importlib.util.module_from_spec(spec)
23	spec.loader.exec_module(crm)
24	
25	BASE = datetime(2026, 10, 24, 10, 0, 0, tzinfo=timezone.utc)
26	STORE = "s" * 32
27	CODE = {"source_digest": "c" * 64, "uv_lock_sha256": "u" * 64}
28	
29	
30	def utc(mono):
31	    return (BASE + timedelta(seconds=mono - 1000)).isoformat()
32	
33	
34	def write_jsonl(path, events):
35	    path.parent.mkdir(parents=True, exist_ok=True)
36	    path.write_text("".join(json.dumps(e) + "\n" for e in events))
37	
38	
39	def launcher(folder, step, start, end):
40	    (folder / "logs").mkdir(parents=True, exist_ok=True)
41	    (folder / "logs" / f"{step}.launcher.json").write_text(json.dumps(
42	        {"outcome": "exited", "step_started_at_utc": utc(start), "tree_ended_at_utc": utc(end)}))
43	
44	
45	def write_csv(path, header, rows):
46	    path.parent.mkdir(parents=True, exist_ok=True)
47	    with open(path, "w", newline="") as f:
48	        w = csv.writer(f)
49	        w.writerow(header)
50	        w.writerows(rows)
51	
52	
53	def make_batch(tmp_path, *, step_code=CODE):
54	    """Four planned jobs: C0 and W3 on worker A, W5a on B, and a K2 that memory stopped."""
55	    b = tmp_path / "batch"
56	    dates = nyse_sessions("2024-01-02", 31)
57	    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(3).normal(0, 0.01, 30))})
58	    checksums = input_checksums(tmp_path / "processed", "snap")
59	    (b / "plan.json").parent.mkdir(parents=True)
60	    (b / "plan.json").write_text(json.dumps({"seed": 1, "settings": {"snapshot": "snap"},
61	                                             "jobs": ["C0", "W3", "W5a", "K2"]}))
62	    write_jsonl(b / "harness.jsonl", [
63	        {"event": "batch_started", "mono": 1000.0, "clock": {"ts": utc(1000), "mono": 1000.0}, "code": CODE},
64	        *[{"event": "process_started", "name": n, "same_clock": True, "code": CODE, "mono": 1001.0}
65	          for n in ("reconciler", "A", "B")],
66	        {"event": "deadline", "position": 1, "job_id": 1, "case": "C0", "reference": "submit", "reference_mono": 1010.0,
67	         "deadline_s": 75, "deadline_mono": 1085.0, "t_submit": 1010.0},
68	        {"event": "injection", "position": 1, "job_id": 1, "case": "C0", "missed": None},
69	        {"event": "deadline", "position": 2, "job_id": 2, "case": "W3", "reference": "injection",
70	         "reference_mono": 1120.0, "deadline_s": 140, "deadline_mono": 1260.0, "t_submit": 1100.0},
71	        {"event": "injection", "position": 2, "job_id": 2, "case": "W3", "missed": None, "kind": "sigkill",
72	         "worker": "A", "attempt": 1, "t_inj": 1120.0},
73	        {"event": "deadline", "position": 3, "job_id": 3, "case": "W5a", "reference": "injection",
74	         "reference_mono": 1300.0, "deadline_s": 75, "deadline_mono": 1375.0, "t_submit": 1260.0},
75	        {"event": "injection", "position": 3, "job_id": 3, "case": "W5a", "missed": None, "kind": "hook",
76	         "worker": "B", "point": "after_accept_commit", "t_inj": 1300.0},
77	        {"event": "not_run", "position": 4, "case": "K2", "why": "memory"},
78	        {"event": "quiescent", "processes_left": False, "other_connections": 0},
79	        {"event": "final_snapshot", "status_check_exit": 0, "fingerprints_agree": True, "fingerprints": [],
80	         "batch_peaks": {}},
81	        {"event": "batch_ended", "mono": 1600.0, "clock": {"ts": utc(1600), "mono": 1600.0}, "code": CODE}])
82	    step = {"event": "step_started", "code": step_code}
83	    write_jsonl(b / "events" / "A.jsonl", [
84	        {"event": "started", "pid": 11, "mono": 1001.0, "code": CODE}, {"event": "assigned", "mono": 1002.0,
85	                                                                          "partitions": [["t", 0]]},
86	        {"event": "delivered", "job_id": 1, "mono": 1010.5},
87	        {"event": "claimed", "job_id": 1, "attempt": 1, "run_id": "job-1-attempt-1", "mono": 1011.0},
88	        {**step, "job_id": 1, "attempt": 1, "step": "windows", "mono": 1012.0},
89	        {**step, "job_id": 1, "attempt": 1, "step": "spark_pipeline", "mono": 1015.0},
90	        {**step, "job_id": 1, "attempt": 1, "step": "verify", "mono": 1040.0},
91	        {"event": "accepted", "job_id": 1, "attempt": 1, "digest": "a" * 64, "mono": 1050.0, "store_id": STORE,
92	         "worker_id": "A", "pid": 11},
93	        {"event": "delivered", "job_id": 2, "mono": 1100.5},
94	        {"event": "claimed", "job_id": 2, "attempt": 1, "run_id": "job-2-attempt-1", "mono": 1101.0},
95	        {**step, "job_id": 2, "attempt": 1, "step": "windows", "mono": 1102.0},
96	        {**step, "job_id": 2, "attempt": 1, "step": "spark_pipeline", "mono": 1105.0}])
97	    write_jsonl(b / "events" / "B.jsonl", [
98	        {"event": "started", "pid": 22, "mono": 1001.5, "code": CODE}, {"event": "assigned", "mono": 1003.0,
99	                                                                          "partitions": []},
100	        {"event": "assigned", "mono": 1136.0, "partitions": [["t", 0]]},
101	        {"event": "claimed", "job_id": 2, "attempt": 2, "run_id": "job-2-attempt-2", "mono": 1180.0},
102	        {**step, "job_id": 2, "attempt": 2, "step": "windows", "mono": 1181.0},
103	        {**step, "job_id": 2, "attempt": 2, "step": "spark_pipeline", "mono": 1184.0},
104	        {**step, "job_id": 2, "attempt": 2, "step": "verify", "mono": 1210.0},
105	        {"event": "accepted", "job_id": 2, "attempt": 2, "digest": "b" * 64, "mono": 1225.0, "store_id": STORE,
106	         "worker_id": "B", "pid": 22},
107	        {"event": "delivered", "job_id": 3, "mono": 1260.5},
108	        {"event": "claimed", "job_id": 3, "attempt": 1, "run_id": "job-3-attempt-1", "mono": 1261.0},
109	        {**step, "job_id": 3, "attempt": 1, "step": "windows", "mono": 1262.0},
110	        {**step, "job_id": 3, "attempt": 1, "step": "spark_pipeline", "mono": 1265.0},
111	        {**step, "job_id": 3, "attempt": 1, "step": "verify", "mono": 1290.0},
112	        {"event": "fault_injected", "point": "after_accept_commit", "action": "kill", "mono": 1300.0}])
113	    write_jsonl(b / "events" / "reconciler-33.jsonl", [
114	        {"event": "started", "mono": 1001.0, "code": CODE}, {"event": "requeued", "job_id": 2, "mono": 1175.0},
115	        {"event": "published", "job_id": 2, "mono": 1175.5}])
116	    write_jsonl(b / "events" / "submit.jsonl", [{"event": "started", "mono": m, "code": CODE} for m in (1010, 1100, 1260)])
117	    jobs = b / "jobs" / STORE
118	    for run_id, steps in {"job-1-attempt-1": [("windows", 1012, 1015), ("spark_pipeline", 1015, 1040),
119	                                              ("verify", 1040, 1049)],
120	                          "job-2-attempt-1": [("windows", 1102, 1105), ("spark_pipeline", 1105, 1121)],
121	                          "job-2-attempt-2": [("windows", 1181, 1184), ("spark_pipeline", 1184, 1210),
122	                                              ("verify", 1210, 1224)],
123	                          "job-3-attempt-1": [("windows", 1262, 1265), ("spark_pipeline", 1265, 1290),
124	                                              ("verify", 1290, 1299)]}.items():
125	        for name, start, end in steps:
126	            launcher(jobs / run_id, name, start, end)
127	    for run_id in ("job-1-attempt-1", "job-2-attempt-2", "job-3-attempt-1"):
128	        (jobs / run_id / "manifest.json").write_text("{}")
129	    launcher(b / "reference", "windows", 990, 993)
130	    launcher(b / "reference", "spark_pipeline", 993, 999)
131	    write_csv(b / "crosscheck" / "Q1.csv", ["job_id", "n_claims", "n_accepted", "verdict"],
132	              [[1, 1, 1, "ok"], [2, 2, 1, "ok"], [3, 1, 1, "ok"]])
133	    write_csv(b / "crosscheck" / "Q2.csv", ["case_id", "job_id", "timeliness", "deadline_met"],
134	              [["C0", 1, "on time", "yes"], ["W3", 2, "on time", "yes"], ["W5a", 3, "on time", "yes"]])
135	    write_csv(b / "crosscheck" / "Q3a.csv", ["job_id", "log_verdict"],
136	              [[1, "reported once"], [2, "reported once"], [3, "no matching report"]])
137	    write_csv(b / "crosscheck" / "Q3b.csv", ["store_id", "worker_id", "pid", "job_id", "attempt_number", "report_verdict"],
138	              [[STORE, "A", 11, 1, 1, "matches"], [STORE, "B", 22, 2, 2, "matches"]])
139	    write_csv(b / "crosscheck" / "Q2b.csv", ["job_id", "status"], [])
140	    export = b / "export"
141	    export.mkdir()
142	    (export / "jobs.json").write_text(json.dumps([{"job_id": j, "version": 4, "input_checksums": checksums}
143	                                                  for j in (1, 2, 3)]))
144	    (export / "job_attempts.json").write_text(json.dumps([
145	        {"job_id": 1, "attempt_number": 1, "outcome": "accepted", "renewals": 2, "output_dir": str(jobs / "job-1-attempt-1"),
146	         "result_digest": "a" * 64},
147	        {"job_id": 2, "attempt_number": 1, "outcome": "expired", "renewals": 1, "output_dir": str(jobs / "job-2-attempt-1"),
148	         "result_digest": None},
149	        {"job_id": 2, "attempt_number": 2, "outcome": "accepted", "renewals": 2, "output_dir": str(jobs / "job-2-attempt-2"),
150	         "result_digest": "b" * 64},
151	        {"job_id": 3, "attempt_number": 1, "outcome": "accepted", "renewals": 2, "output_dir": str(jobs / "job-3-attempt-1"),
152	         "result_digest": "c" * 64}]))
153	    (export / "store.json").write_text(json.dumps({"store_id": STORE}))
154	    (export / "invariant_violations.json").write_text("{}")
155	    return b
156	
157	
158	@pytest.fixture
159	def batch(tmp_path):
160	    return make_batch(tmp_path)
161	
162	
163	def test_the_metrics_of_each_job_with_their_reasons(batch, tmp_path):
164	    result = crm.collect(batch, processed_root=tmp_path / "processed")
165	    rows = {r["position"]: r for r in result["rows"]}
166	    assert result["c0_median_s"] == 40.0
167	    c0, w3, w5a, k2 = rows[1], rows[2], rows[3], rows[4]
168	    assert (c0["detection_s"], c0["rerun_s"], c0["finish_s"], c0["overhead_s"]) == (
169	        "n/a: no failure", "n/a: no failure", 40.0, 0.0)
170	    assert (w3["detection_s"], w3["rerun_s"], w3["finish_s"], w3["overhead_s"]) == (55.0, 60.0, 105.0, 85.0)
171	    assert (w3["claims"], w3["executions"], w3["complete_executions"], w3["wasted_step_s"]) == ("2", 2, 1, 19.0)
172	    assert (w5a["detection_s"], w5a["finish_s"], w5a["q3a_verdict"]) == (
173	        "n/a: after acceptance", "n/a: after acceptance", "no matching report")
174	    assert k2 == {"position": 4, "case": "K2", "status": "not run"}
175	
176	
177	def test_validity_passes_and_outcomes_stay_apart(batch, tmp_path):
178	    result = crm.collect(batch, processed_root=tmp_path / "processed")
179	    assert result["validity_failed"] == []
180	    assert result["validity"]["machine_state"]["passed"] is None                  # not recorded, not a pass
181	    assert result["outcomes"]["overlap"]["verdict"] == "no overlap"
182	    assert result["outcomes"]["q1_not_ok"] == [] and result["outcomes"]["invariant_violations"] == {}
183	    accepted = {a["job_id"]: a["problems"] for a in result["outcomes"]["accepted_attempts"]}
184	    assert accepted[1] == ["no readable attempt.json"]                           # an outcome finding, not validity
185	
186	
187	def test_the_tally_lists_every_case_and_every_verdict_with_zeros(batch, tmp_path):
188	    tally = {t["case"]: t for t in crm.collect(batch, processed_root=tmp_path / "processed")["tally"]}
189	    assert set(tally) == set(crm.CASES)
190	    assert (tally["W3"]["planned"], tally["W3"]["made"], tally["K2"]["not_run"], tally["X1"]["planned"]) == (1, 1, 1, 0)
191	    assert tally["W5a"]["q3a: no matching report"] == 1 and tally["C0"]["q2: late"] == 0
192	    assert all(f"q1: {v}" in tally["D2"] for v in crm.Q1_VERDICTS)
193	
194	
195	def test_a_missing_launcher_record_makes_the_overlap_unknown_never_none(batch, tmp_path):
196	    (batch / "jobs" / STORE / "job-2-attempt-1" / "logs" / "spark_pipeline.launcher.json").unlink()
197	    result = crm.collect(batch, processed_root=tmp_path / "processed")
198	    overlap = result["outcomes"]["overlap"]
199	    assert overlap["verdict"] == "unknown" and overlap["steps_without_interval"] == ["job-2-attempt-1:spark_pipeline"]
200	    assert str({r["position"]: r for r in result["rows"]}[2]["wasted_step_s"]).startswith("unknown")
201	
202	
203	def test_overlapping_steps_are_found(batch, tmp_path):
204	    launcher(batch / "jobs" / STORE / "job-2-attempt-2", "windows", 1119, 1184)    # starts before 1121
205	    assert crm.collect(batch, processed_root=tmp_path / "processed")["outcomes"]["overlap"]["verdict"] == "overlap"
206	
207	
208	def test_a_step_that_ran_other_code_fails_validity_and_the_exit_code(tmp_path):
209	    batch = make_batch(tmp_path, step_code={**CODE, "source_digest": "x" * 64})
210	    assert crm.main(["--batch", str(batch), "--processed-root", str(tmp_path / "processed")]) == 1
211	    validity = json.loads((batch / "validity.json").read_text())
212	    assert validity["validity_failed"] == ["code_identity"] and validity["validity"]["code_identity"]["distinct"] == 2
213	    assert (batch / "injections.csv").exists() and (batch / "tally.csv").exists()
214	
```

## 72. Assistant — 2026-10-24T07:25:09.431Z

### Tool call: Bash

```
{
  "command": "sed -n 1,200p src/etf_risk/jobs/events.py",
  "description": "Read the event log writer and reader"
}
```

## 73. User — 2026-10-24T07:25:10.215Z

### Tool result

```
"""Event logs of the job processes (worker, reconciler, submit): one JSON object per line,
written and flushed as each event happens, so a process killed by SIGKILL loses at most the
event it was writing.

Every event has:
- "ts", the time in UTC (ISO 8601, microseconds), comparable across the processes of this
  machine;
- "mono", the writing process's time.monotonic(), for durations within that process;
- "pid", "component" ("worker", "reconciler", "submit") and "event";
- the context the log was opened with (for example store_id and worker_id);
- the event's own fields.

The recovery experiments take their detection and recovery times from these logs together
with the job tables (spec §11; docs/job-queue.md lists the events).

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_events.py.
"""
from __future__ import annotations

import json
import os
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO


class EventLog:
    def __init__(self, path: str | Path | None, component: str, **context: Any):
        """path None writes nothing (the tests and the simulated pipeline need no log)."""
        self.component, self.context = component, context
        self._file: TextIO | None = None
        self._lock = threading.Lock()
        if path is not None:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            self._file = open(path, "a", encoding="utf-8")

    def log(self, event: str, **fields: Any) -> None:
        if self._file is None:
            return
        record = {"ts": datetime.now(timezone.utc).isoformat(timespec="microseconds"), "mono": time.monotonic(),
                  "pid": os.getpid(), "component": self.component, "event": event, **self.context, **fields}
        line = json.dumps(record, default=str) + "\n"
        with self._lock:
            self._file.write(line)
            self._file.flush()

    def close(self) -> None:
        with self._lock:
            if self._file is not None:
                self._file.close()
                self._file = None


NO_EVENTS = EventLog(None, "none")


def read_events(path: str | Path) -> list[dict]:
    """The events of one log; a last line cut off by a crash is left out."""
    events = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events
```

## 74. Assistant — 2026-10-24T07:25:27.473Z

### Tool call: Bash

```
{
  "command": "sed -n '/^-- Q2\\./,/^-- Q3a\\./p' src/etf_risk/jobs/crosscheck.sql",
  "description": "Read the frozen Q2 and Q2b queries"
}
```

## 75. User — 2026-10-24T07:25:28.370Z

### Tool result

```
-- Q2. Timeliness (4.2), one row per job the harness submitted. deadline_met is yes, no or
-- unknown, and only "deadline not observed" is unknown.
SELECT
    t.*,
    CASE t.timeliness
        WHEN 'on time' THEN 'yes'
        WHEN 'deadline not observed' THEN 'unknown'
        ELSE 'no'
    END AS deadline_met
FROM (
    SELECT
        b.case_id,
        b.job_id,
        j.status AS final_status,
        d.status AS status_at_deadline,
        ROUND(d.observed_to_mono - b.deadline_mono, 3) AS observation_lag_s,
        j.attempt_number,
        j.published_at,
        j.lease_expires_at,
        CASE
            WHEN j.job_id IS NULL
                THEN 'missing'
            WHEN j.status IN ('queued', 'running')
                THEN 'unfinished'
            WHEN j.status = 'failed'
                THEN 'failed'
            WHEN d.status = 'succeeded' AND d.observed_to_mono <= b.deadline_mono + b.max_lag_s
                THEN 'on time'
            WHEN d.status <> 'succeeded' AND d.observed_from_mono >= b.deadline_mono
                THEN 'late'
            ELSE 'deadline not observed'
        END AS timeliness
    FROM batch_jobs AS b
    LEFT JOIN jobs AS j ON j.job_id = b.job_id
    LEFT JOIN deadline_observations AS d ON d.job_id = b.job_id
) AS t
ORDER BY t.case_id, t.job_id;

-- Q2b. Jobs in the table that the harness did not record, such as a submit that exited 75
-- (outcome unknown) although its insert committed. Each needs an explanation.
SELECT
    j.job_id,
    j.status
FROM jobs AS j
LEFT JOIN batch_jobs AS b ON b.job_id = j.job_id
WHERE b.job_id IS NULL
ORDER BY j.job_id;

-- Q3a. Event-log completeness (6.4), one row per succeeded job. Only this store's reports count,
```

## 76. Assistant — 2026-10-24T07:25:38.684Z

### Tool call: Bash

````
{
  "command": "grep -n -E '^#|^```' docs/recovery-sql.md | head -80; ls -la /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/fixture/ /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/fixture/kit 2>/dev/null | head -40",
  "description": "Outline the SQL doc and the scratch fixture kit"
}
````

## 77. User — 2026-10-24T07:25:39.524Z

### Tool result

````
1:# Recovery experiments: SQL cross-check and fixture
14:## 1. What the queries add, and where they run
32:## 2. The harness's tables and the queries
34:```sql
66:```
68:```sql
75:```
77:```sql
128:```
130:```sql
168:```
170:```sql
180:```
182:```sql
222:```
224:```sql
251:```
264:## 3. Fixture
266:### 3.1 Jobs
300:### 3.2 Fixture A, store rows
302:```sql
340:```
342:### 3.3 Fixture B, store rows
344:```sql
384:```
386:### 3.4 The harness's rows
388:```sql
424:```
426:```sql
463:```
465:## 4. Expected rows (frozen)
593:## 5. Coverage
599:## 6. Run
/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/fixture/:
total 32
drwxr-xr-x@ 10 [REDACTED:user]  wheel   320 Oct 23 17:19 .
drwx------@  6 [REDACTED:user]  wheel   192 Oct 23 16:19 ..
drwxr-xr-x@ 12 [REDACTED:user]  wheel   384 Oct 23 17:13 actual
drwxr-xr-x@  9 [REDACTED:user]  wheel   288 Oct 23 16:19 expected
drwxr-xr-x@  9 [REDACTED:user]  wheel   288 Oct 23 16:19 expected-src
-rw-r--r--@  1 [REDACTED:user]  wheel   726 Oct 23 16:19 gen.awk
drwxr-xr-x@  6 [REDACTED:user]  wheel   192 Oct 24 00:39 kit
drwxr-xr-x@  9 [REDACTED:user]  wheel   288 Oct 23 16:19 markdown
-rw-r--r--@  1 [REDACTED:user]  wheel  4375 Oct 23 17:19 run.sh
-rw-r--r--@  1 [REDACTED:user]  wheel  1432 Oct 23 17:12 wait-release.sh

/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/fixture/kit:
total 64
drwxr-xr-x@  6 [REDACTED:user]  wheel    192 Oct 24 00:39 .
drwxr-xr-x@ 10 [REDACTED:user]  wheel    320 Oct 23 17:19 ..
drwxr-xr-x@ 13 [REDACTED:user]  wheel    416 Oct 24 00:39 blocks
-rw-r--r--@  1 [REDACTED:user]  wheel    670 Oct 23 16:45 inv.py
drwxr-xr-x@ 14 [REDACTED:user]  wheel    448 Oct 24 00:39 named
-rw-r--r--@  1 [REDACTED:user]  wheel  26695 Oct 24 00:39 run.sql
````

## 78. Assistant — 2026-10-24T07:25:43.209Z

Status: reading the frozen SQL fixtures so an offline SQLite test can check every verdict, including "late".

## 79. Assistant — 2026-10-24T07:25:44.323Z

### Tool call: Bash

```
{
  "command": "sed -n 260,470p docs/recovery-sql.md",
  "description": "Read the SQL doc's fixture section"
}
```

## 80. User — 2026-10-24T07:25:45.016Z

### Tool result

````
job; Q3a `reported once` for every succeeded job except W5a's, which has `no matching report` and no
report at all; Q3b `matches` for every report; Q2b no rows. Q2's classes depend on the deadlines
(outline 8.2), and `deadline_met` is `unknown` only where an observation failed or was not valid.

## 3. Fixture

### 3.1 Jobs

Twenty jobs in one store, plus one job id that only the harness recorded. Fixture A (jobs 1–9)
covers the first review's cases; fixture B (jobs 10–20 and 99) covers every verdict that fixture A
does not. The times, deadlines and lags are made up and decide nothing in the outline's section 8.

| Job | Case id | Shows |
|---|---|---|
| 1 | `ontime` | a job that met its deadline and was reported once |
| 2 | `late` | late completion: running at its deadline, succeeded later (attempt 2, by B) |
| 3 | `noevent` | a missing acceptance event, as after W5a |
| 4 | `dupe` | duplicate reports of one attempt |
| 5 | `wrongwkr` | a wrong-worker report: A reports attempt 2, which B claimed and accepted |
| 6 | `unfin` | a job still running in the final snapshot |
| 7 | `othstore` | a stale report from another store for the same job id, next to the right one |
| 8 | `twoacc` | two accepted attempts, inserted directly; the store cannot produce this |
| 9 | `notobs` | a success seen by an observation that ended too late |
| 10 | `noaccrow` | succeeded, but its only attempt expired: no accepted attempt |
| 11 | `othernum` | `accepted_attempt` names attempt 2, which failed, while attempt 1 is accepted |
| 12 | `accfail` | a failed job with an accepted attempt |
| 13 | `rowsdiff` | `attempt_number` 2 with a single attempt row |
| 14 | `runleft` | succeeded, with attempt 1 still running |
| 15 | `failed` | a job that ran out of attempts, and a report from B for its failed attempt 3 |
| 16 | `wrongdig` | a report with the wrong digest |
| 17 | `noattmpt` | a report for an attempt that does not exist |
| 18 | — | a queued job the harness did not record (Q2b); not in `batch_jobs` |
| 19 | `obsfail` | a deadline observation whose read failed |
| 20 | `noobsrow` | no deadline observation at all |
| 99 | `missing` | a job the harness recorded, with no row in the table |

Load the store rows into a scratch database created from
[schema/mysql.sql](../src/etf_risk/jobs/schema/mysql.sql), never into a batch's database; then, in
the same session, create the TEMPORARY tables of section 2, load the harness's rows and run Q0–Q3b.

### 3.2 Fixture A, store rows

```sql
-- Fixture A, store rows. jobs and job_attempts refer to each other, so foreign key checks are off
-- while loading; the rows satisfy both keys, and the CHECK constraints stay enforced.
SET @s = 'fixture0000000000000000000000001', @t0 = '2026-10-24 10:00:00', @t1 = '2026-10-24 10:01:05',
    @t2 = '2026-10-24 10:05:00', @lease = '2026-10-24 10:06:00';
SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO job_store (id, store_id, schema_version, created_at) VALUES (1, @s, 1, @t0);

INSERT INTO jobs (job_id, params, input_checksums, status, max_attempts, attempt_number, attempt_token,
                  lease_expires_at, accepted_attempt, error, version, created_at, updated_at,
                  finished_at, published_at) VALUES
    (1, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),
    (2, '{}', '{}', 'succeeded', 3, 2, NULL,      NULL,   2,    NULL, 7, @t0, @t2, @t2,  NULL),
    (3, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),
    (4, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),
    (5, '{}', '{}', 'succeeded', 3, 2, NULL,      NULL,   2,    NULL, 7, @t0, @t2, @t2,  NULL),
    (6, '{}', '{}', 'running',   3, 1, 'tok-6-1', @lease, NULL, NULL, 3, @t0, @t2, NULL, NULL),
    (7, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),
    (8, '{}', '{}', 'succeeded', 3, 2, NULL,      NULL,   2,    NULL, 7, @t0, @t2, @t2,  NULL),
    (9, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL);

INSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id, output_dir, outcome,
                          error, result_digest, claimed_at, lease_expires_at, renewals, ended_at) VALUES
    (1, 1, 'tok-1-1', 'A', 'job-1-attempt-1', '/fixture/job-1-attempt-1', 'accepted', NULL, REPEAT('1', 64), @t0, @lease, 2, @t2),
    (2, 1, 'tok-2-1', 'A', 'job-2-attempt-1', '/fixture/job-2-attempt-1', 'expired',  NULL, NULL,            @t0, @t1,    1, @t1),
    (2, 2, 'tok-2-2', 'B', 'job-2-attempt-2', '/fixture/job-2-attempt-2', 'accepted', NULL, REPEAT('2', 64), @t1, @lease, 2, @t2),
    (3, 1, 'tok-3-1', 'A', 'job-3-attempt-1', '/fixture/job-3-attempt-1', 'accepted', NULL, REPEAT('3', 64), @t0, @lease, 2, @t2),
    (4, 1, 'tok-4-1', 'A', 'job-4-attempt-1', '/fixture/job-4-attempt-1', 'accepted', NULL, REPEAT('4', 64), @t0, @lease, 2, @t2),
    (5, 1, 'tok-5-1', 'A', 'job-5-attempt-1', '/fixture/job-5-attempt-1', 'expired',  NULL, NULL,            @t0, @t1,    1, @t1),
    (5, 2, 'tok-5-2', 'B', 'job-5-attempt-2', '/fixture/job-5-attempt-2', 'accepted', NULL, REPEAT('5', 64), @t1, @lease, 2, @t2),
    (6, 1, 'tok-6-1', 'A', 'job-6-attempt-1', '/fixture/job-6-attempt-1', 'running',  NULL, NULL,            @t0, @lease, 4, NULL),
    (7, 1, 'tok-7-1', 'A', 'job-7-attempt-1', '/fixture/job-7-attempt-1', 'accepted', NULL, REPEAT('7', 64), @t0, @lease, 2, @t2),
    (8, 1, 'tok-8-1', 'A', 'job-8-attempt-1', '/fixture/job-8-attempt-1', 'accepted', NULL, REPEAT('8', 64), @t0, @t1,    1, @t1),
    (8, 2, 'tok-8-2', 'B', 'job-8-attempt-2', '/fixture/job-8-attempt-2', 'accepted', NULL, REPEAT('f', 64), @t1, @lease, 2, @t2),
    (9, 1, 'tok-9-1', 'A', 'job-9-attempt-1', '/fixture/job-9-attempt-1', 'accepted', NULL, REPEAT('9', 64), @t0, @lease, 2, @t2);

SET FOREIGN_KEY_CHECKS = 1;
```

### 3.3 Fixture B, store rows

```sql
-- Fixture B, store rows: the verdicts fixture A does not show. Same session as fixture A's rows,
-- with the same settings.
SET @s = 'fixture0000000000000000000000001', @t0 = '2026-10-24 10:00:00', @t1 = '2026-10-24 10:01:05',
    @t2 = '2026-10-24 10:05:00', @lease = '2026-10-24 10:06:00';
SET FOREIGN_KEY_CHECKS = 0;

INSERT INTO jobs (job_id, params, input_checksums, status, max_attempts, attempt_number, attempt_token,
                  lease_expires_at, accepted_attempt, error, version, created_at, updated_at,
                  finished_at, published_at) VALUES
    (10, '{}', '{}', 'succeeded', 3, 1, NULL, NULL, 1,    NULL,                       4,  @t0, @t2, @t2,  NULL),
    (11, '{}', '{}', 'succeeded', 3, 2, NULL, NULL, 2,    NULL,                       7,  @t0, @t2, @t2,  NULL),
    (12, '{}', '{}', 'failed',    3, 1, NULL, NULL, NULL, 'fixture: failed',          4,  @t0, @t2, @t2,  NULL),
    (13, '{}', '{}', 'succeeded', 3, 2, NULL, NULL, 1,    NULL,                       6,  @t0, @t2, @t2,  NULL),
    (14, '{}', '{}', 'succeeded', 3, 2, NULL, NULL, 2,    NULL,                       7,  @t0, @t2, @t2,  NULL),
    (15, '{}', '{}', 'failed',    3, 3, NULL, NULL, NULL, 'fixture: out of attempts', 10, @t0, @t2, @t2,  NULL),
    (16, '{}', '{}', 'succeeded', 3, 1, NULL, NULL, 1,    NULL,                       4,  @t0, @t2, @t2,  NULL),
    (17, '{}', '{}', 'succeeded', 3, 1, NULL, NULL, 1,    NULL,                       4,  @t0, @t2, @t2,  NULL),
    (18, '{}', '{}', 'queued',    3, 0, NULL, NULL, NULL, NULL,                       0,  @t0, @t0, NULL, NULL),
    (19, '{}', '{}', 'succeeded', 3, 1, NULL, NULL, 1,    NULL,                       4,  @t0, @t2, @t2,  NULL),
    (20, '{}', '{}', 'succeeded', 3, 1, NULL, NULL, 1,    NULL,                       4,  @t0, @t2, @t2,  NULL);

INSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id, output_dir, outcome,
                          error, result_digest, claimed_at, lease_expires_at, renewals, ended_at) VALUES
    (10, 1, 'tok-10-1', 'A', 'job-10-attempt-1', '/fixture/job-10-attempt-1', 'expired',  NULL,               NULL,            @t0, @t1,    1, @t1),
    (11, 1, 'tok-11-1', 'A', 'job-11-attempt-1', '/fixture/job-11-attempt-1', 'accepted', NULL,               REPEAT('b', 64), @t0, @t1,    1, @t1),
    (11, 2, 'tok-11-2', 'B', 'job-11-attempt-2', '/fixture/job-11-attempt-2', 'failed',   'fixture: failed',  NULL,            @t1, @lease, 2, @t2),
    (12, 1, 'tok-12-1', 'A', 'job-12-attempt-1', '/fixture/job-12-attempt-1', 'accepted', NULL,               REPEAT('c', 64), @t0, @lease, 2, @t2),
    (13, 1, 'tok-13-1', 'A', 'job-13-attempt-1', '/fixture/job-13-attempt-1', 'accepted', NULL,               REPEAT('d', 64), @t0, @lease, 2, @t2),
    (14, 1, 'tok-14-1', 'A', 'job-14-attempt-1', '/fixture/job-14-attempt-1', 'running',  NULL,               NULL,            @t0, @t1,    1, NULL),
    (14, 2, 'tok-14-2', 'B', 'job-14-attempt-2', '/fixture/job-14-attempt-2', 'accepted', NULL,               REPEAT('e', 64), @t1, @lease, 2, @t2),
    (15, 1, 'tok-15-1', 'A', 'job-15-attempt-1', '/fixture/job-15-attempt-1', 'failed',   'fixture: timeout', NULL,            @t0, @t1,    1, @t1),
    (15, 2, 'tok-15-2', 'A', 'job-15-attempt-2', '/fixture/job-15-attempt-2', 'failed',   'fixture: timeout', NULL,            @t1, @t1,    1, @t1),
    (15, 3, 'tok-15-3', 'B', 'job-15-attempt-3', '/fixture/job-15-attempt-3', 'failed',   'fixture: timeout', NULL,            @t1, @lease, 1, @t2),
    (16, 1, 'tok-16-1', 'A', 'job-16-attempt-1', '/fixture/job-16-attempt-1', 'accepted', NULL,               REPEAT('6', 64), @t0, @lease, 2, @t2),
    (17, 1, 'tok-17-1', 'A', 'job-17-attempt-1', '/fixture/job-17-attempt-1', 'accepted', NULL,               REPEAT('g', 64), @t0, @lease, 2, @t2),
    (19, 1, 'tok-19-1', 'A', 'job-19-attempt-1', '/fixture/job-19-attempt-1', 'accepted', NULL,               REPEAT('h', 64), @t0, @lease, 2, @t2),
    (20, 1, 'tok-20-1', 'A', 'job-20-attempt-1', '/fixture/job-20-attempt-1', 'accepted', NULL,               REPEAT('i', 64), @t0, @lease, 2, @t2);

SET FOREIGN_KEY_CHECKS = 1;
```

### 3.4 The harness's rows

```sql
-- Fixture A, the harness's rows, in the session that created section 7's TEMPORARY tables.
INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono, max_lag_s) VALUES
    (1, 'ontime',   'submit',    100, 2000.0, 1.0),
    (2, 'late',     'injection', 100, 2000.0, 1.0),
    (3, 'noevent',  'injection', 100, 2000.0, 1.0),
    (4, 'dupe',     'submit',    100, 2000.0, 1.0),
    (5, 'wrongwkr', 'injection', 100, 2000.0, 1.0),
    (6, 'unfin',    'injection', 100, 2000.0, 1.0),
    (7, 'othstore', 'submit',    100, 2000.0, 1.0),
    (8, 'twoacc',   'submit',    100, 2000.0, 1.0),
    (9, 'notobs',   'injection', 100, 2000.0, 1.0);

INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono, status, attempt_number,
                                   accepted_attempt) VALUES
    (1, 2000.010, 2000.030, 'succeeded', 1, 1),
    (2, 2000.010, 2000.030, 'running',   2, NULL),
    (3, 2000.010, 2000.030, 'succeeded', 1, 1),
    (4, 2000.010, 2000.030, 'succeeded', 1, 1),
    (5, 2000.010, 2000.030, 'succeeded', 2, 2),
    (6, 2000.010, 2000.030, 'running',   1, NULL),
    (7, 2000.010, 2000.030, 'succeeded', 1, 1),
    (8, 2000.010, 2000.030, 'succeeded', 2, 2),
    (9, 2002.500, 2002.600, 'succeeded', 1, 1);

INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number, result_digest) VALUES
    (@s, 'A', 101, 1, 1, REPEAT('1', 64)),
    (@s, 'B', 202, 2, 2, REPEAT('2', 64)),
    (@s, 'A', 101, 4, 1, REPEAT('4', 64)),
    (@s, 'A', 101, 4, 1, REPEAT('4', 64)),
    (@s, 'A', 101, 5, 2, REPEAT('5', 64)),
    (@s, 'A', 101, 7, 1, REPEAT('7', 64)),
    ('fixture0000000000000000000000002', 'A', 99, 7, 1, REPEAT('0', 64)),
    (@s, 'A', 101, 8, 1, REPEAT('8', 64)),
    (@s, 'B', 202, 8, 2, REPEAT('f', 64)),
    (@s, 'A', 101, 9, 1, REPEAT('9', 64));
```

```sql
-- Fixture B, the harness's rows, in the same session. Job 18 has no batch row, job 20 no
-- observation, and job 99 no row in the table.
INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono, max_lag_s) VALUES
    (10, 'noaccrow', 'submit',    100, 2000.0, 1.0),
    (11, 'othernum', 'submit',    100, 2000.0, 1.0),
    (12, 'accfail',  'injection', 100, 2000.0, 1.0),
    (13, 'rowsdiff', 'submit',    100, 2000.0, 1.0),
    (14, 'runleft',  'submit',    100, 2000.0, 1.0),
    (15, 'failed',   'submit',    100, 2000.0, 1.0),
    (16, 'wrongdig', 'submit',    100, 2000.0, 1.0),
    (17, 'noattmpt', 'submit',    100, 2000.0, 1.0),
    (19, 'obsfail',  'injection', 100, 2000.0, 1.0),
    (20, 'noobsrow', 'injection', 100, 2000.0, 1.0),
    (99, 'missing',  'submit',    100, 2000.0, 1.0);

INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono, status, attempt_number,
                                   accepted_attempt) VALUES
    (10, 2000.010, 2000.030, 'succeeded', 1,    1),
    (11, 2000.010, 2000.030, 'succeeded', 2,    2),
    (12, 2000.010, 2000.030, 'failed',    1,    NULL),
    (13, 2000.010, 2000.030, 'succeeded', 2,    1),
    (14, 2000.010, 2000.030, 'succeeded', 2,    2),
    (15, 2000.010, 2000.030, 'failed',    3,    NULL),
    (16, 2000.010, 2000.030, 'succeeded', 1,    1),
    (17, 2000.010, 2000.030, 'succeeded', 1,    1),
    (19, 2000.010, 2000.030, NULL,        NULL, NULL),
    (99, 2000.010, 2000.030, NULL,        NULL, NULL);

INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number, result_digest) VALUES
    (@s, 'A', 101, 13, 1, REPEAT('d', 64)),
    (@s, 'B', 202, 14, 2, REPEAT('e', 64)),
    (@s, 'B', 202, 15, 3, REPEAT('a', 64)),
    (@s, 'A', 101, 16, 1, REPEAT('x', 64)),
    (@s, 'A', 101, 17, 5, REPEAT('g', 64)),
    (@s, 'A', 101, 19, 1, REPEAT('h', 64)),
    (@s, 'A', 101, 20, 1, REPEAT('i', 64));
```

## 4. Expected rows (frozen)

Every row of every query, in the query's own order: 82 rows in all. They were written before the
run and have not changed since (section 6); a later change to them would be a reviewed correction
recorded here, never an adjustment to output. A digest written `c×64` is the character `c` repeated
64 times (`REPEAT('c', 64)`); the comparison uses the full values.
````

## 81. Assistant — 2026-10-24T07:25:49.207Z

### Tool call: Bash

```
{
  "command": "sed -n 470,640p docs/recovery-sql.md",
  "description": "Read the frozen expected rows and run notes"
}
```

## 82. User — 2026-10-24T07:25:49.947Z

### Tool result

```
64 times (`REPEAT('c', 64)`); the comparison uses the full values.

**Q0**

| n_jobs | sum_version | n_attempts | sum_renewals |
|---|---|---|---|
| 20 | 98 | 26 | 45 |

**Q1**

| job_id | status | attempt_number | max_attempts | accepted_attempt | n_claims | n_accepted | n_failed | n_expired | n_running | n_workers | accepted_digest | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 1×64 | ok |
| 2 | succeeded | 2 | 3 | 2 | 2 | 1 | 0 | 1 | 0 | 2 | 2×64 | ok |
| 3 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 3×64 | ok |
| 4 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 4×64 | ok |
| 5 | succeeded | 2 | 3 | 2 | 2 | 1 | 0 | 1 | 0 | 2 | 5×64 | ok |
| 6 | running | 1 | 3 | NULL | 1 | 0 | 0 | 0 | 1 | 1 | NULL | not finished |
| 7 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 7×64 | ok |
| 8 | succeeded | 2 | 3 | 2 | 2 | 2 | 0 | 0 | 0 | 2 | 8×64 | more than one accepted attempt |
| 9 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 9×64 | ok |
| 10 | succeeded | 1 | 3 | 1 | 1 | 0 | 0 | 1 | 0 | 1 | NULL | succeeded without an accepted attempt |
| 11 | succeeded | 2 | 3 | 2 | 2 | 1 | 1 | 0 | 0 | 2 | b×64 | accepted_attempt names another attempt |
| 12 | failed | 1 | 3 | NULL | 1 | 1 | 0 | 0 | 0 | 1 | c×64 | accepted attempt of a job that did not succeed |
| 13 | succeeded | 2 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | d×64 | attempt rows differ from attempt_number |
| 14 | succeeded | 2 | 3 | 2 | 2 | 1 | 0 | 0 | 1 | 2 | e×64 | finished with an attempt still running |
| 15 | failed | 3 | 3 | NULL | 3 | 0 | 3 | 0 | 0 | 2 | NULL | failed |
| 16 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | 6×64 | ok |
| 17 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | g×64 | ok |
| 18 | queued | 0 | 3 | NULL | 0 | 0 | 0 | 0 | 0 | 0 | NULL | not finished |
| 19 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | h×64 | ok |
| 20 | succeeded | 1 | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 1 | i×64 | ok |

**Q2**

| case_id | job_id | final_status | status_at_deadline | observation_lag_s | attempt_number | published_at | lease_expires_at | timeliness | deadline_met |
|---|---|---|---|---|---|---|---|---|---|
| accfail | 12 | failed | failed | 0.03 | 1 | NULL | NULL | failed | no |
| dupe | 4 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| failed | 15 | failed | failed | 0.03 | 3 | NULL | NULL | failed | no |
| late | 2 | succeeded | running | 0.03 | 2 | NULL | NULL | late | no |
| missing | 99 | NULL | NULL | 0.03 | NULL | NULL | NULL | missing | no |
| noaccrow | 10 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| noattmpt | 17 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| noevent | 3 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| noobsrow | 20 | succeeded | NULL | NULL | 1 | NULL | NULL | deadline not observed | unknown |
| notobs | 9 | succeeded | succeeded | 2.6 | 1 | NULL | NULL | deadline not observed | unknown |
| obsfail | 19 | succeeded | NULL | 0.03 | 1 | NULL | NULL | deadline not observed | unknown |
| ontime | 1 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| othernum | 11 | succeeded | succeeded | 0.03 | 2 | NULL | NULL | on time | yes |
| othstore | 7 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| rowsdiff | 13 | succeeded | succeeded | 0.03 | 2 | NULL | NULL | on time | yes |
| runleft | 14 | succeeded | succeeded | 0.03 | 2 | NULL | NULL | on time | yes |
| twoacc | 8 | succeeded | succeeded | 0.03 | 2 | NULL | NULL | on time | yes |
| unfin | 6 | running | running | 0.03 | 1 | NULL | 2026-10-24 10:06:00.000000 | unfinished | no |
| wrongdig | 16 | succeeded | succeeded | 0.03 | 1 | NULL | NULL | on time | yes |
| wrongwkr | 5 | succeeded | succeeded | 0.03 | 2 | NULL | NULL | on time | yes |

**Q2b**

| job_id | status |
|---|---|
| 18 | queued |

**Q3a**

| job_id | accepted_attempt | n_reports | n_matching | n_reported_attempts | log_verdict |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 1 | 1 | reported once |
| 2 | 2 | 1 | 1 | 1 | reported once |
| 3 | 1 | 0 | 0 | 0 | no matching report |
| 4 | 1 | 2 | 2 | 1 | one attempt reported more than once |
| 5 | 2 | 1 | 0 | 1 | no matching report |
| 7 | 1 | 1 | 1 | 1 | reported once |
| 8 | 2 | 2 | 1 | 2 | acceptance reported for more than one attempt |
| 9 | 1 | 1 | 1 | 1 | reported once |
| 10 | 1 | 0 | 0 | 0 | no matching report |
| 11 | 2 | 0 | 0 | 0 | no matching report |
| 13 | 1 | 1 | 1 | 1 | reported once |
| 14 | 2 | 1 | 1 | 1 | reported once |
| 16 | 1 | 1 | 0 | 1 | no matching report |
| 17 | 1 | 1 | 0 | 1 | no matching report |
| 19 | 1 | 1 | 1 | 1 | reported once |
| 20 | 1 | 1 | 1 | 1 | reported once |

**Q3b**

| store_id | worker_id | pid | job_id | attempt_number | report_verdict |
|---|---|---|---|---|---|
| fixture0000000000000000000000001 | A | 101 | 1 | 1 | matches |
| fixture0000000000000000000000001 | B | 202 | 2 | 2 | matches |
| fixture0000000000000000000000001 | A | 101 | 4 | 1 | matches |
| fixture0000000000000000000000001 | A | 101 | 4 | 1 | matches |
| fixture0000000000000000000000001 | A | 101 | 5 | 2 | wrong worker |
| fixture0000000000000000000000001 | A | 101 | 7 | 1 | matches |
| fixture0000000000000000000000002 | A | 99 | 7 | 1 | other store |
| fixture0000000000000000000000001 | A | 101 | 8 | 1 | matches |
| fixture0000000000000000000000001 | B | 202 | 8 | 2 | matches |
| fixture0000000000000000000000001 | A | 101 | 9 | 1 | matches |
| fixture0000000000000000000000001 | A | 101 | 13 | 1 | matches |
| fixture0000000000000000000000001 | B | 202 | 14 | 2 | matches |
| fixture0000000000000000000000001 | B | 202 | 15 | 3 | attempt not accepted |
| fixture0000000000000000000000001 | A | 101 | 16 | 1 | wrong digest |
| fixture0000000000000000000000001 | A | 101 | 17 | 5 | no such attempt |
| fixture0000000000000000000000001 | A | 101 | 19 | 1 | matches |
| fixture0000000000000000000000001 | A | 101 | 20 | 1 | matches |

Job 8's two matches are right against a table that is itself wrong; Q1 and Q3a flag the job.

**The store's seven invariant queries**, taken from `INVARIANT_QUERIES` in store.py and run as one
`UNION ALL` on the same rows, ordered by invariant and job, flag six jobs under five of the seven
invariants:

| invariant | job_id |
|---|---|
| accepted attempt of a job that did not succeed | 12 |
| accepted_attempt names an attempt that was not accepted | 10 |
| accepted_attempt names an attempt that was not accepted | 11 |
| attempt rows differ from attempt_number | 13 |
| running attempt that is not its job's current one | 14 |
| succeeded without exactly one accepted attempt | 8 |
| succeeded without exactly one accepted attempt | 10 |

## 5. Coverage

Every verdict and class has at least one row: Q1's 9 verdicts, Q2's 6 classes and the 3 values of
`deadline_met`, Q3a's 4 verdicts and Q3b's 6. Q2b has one row. Both ways of not observing a deadline
are covered: a failed read (job 19) and no observation (job 20).

## 6. Run

Run once, on 2026-10-23 (local time), by Claude Code at the author's request. It tests the queries,
not the job system.

- **When.** After the M2 session's handover was visible at 17:12:54: its commit `e4adc38` pushed,
  its worktree clean, no test or job processes, and no containers of this project. The runner
  checked again immediately before starting MySQL. Earlier, a check before the outline's revision 2
  and a start attempt after it had each found another session's tests running in
  `.claude/worktrees/worker-pipeline`, and nothing was started either time.
- **Where.** MySQL 8.4.13 (`SELECT VERSION()`) in a throwaway container from the image Compose pins
  (`mysql@sha256:76f0358884cb92d9a086d24e5671c38048d3fef40f2588703d73eb55392d6b69`, with
  `--pull never`), 512 MiB, a 64 MiB buffer pool and `performance_schema` off; not the project's
  Compose services. The container was stopped and removed on exit, and none was left.
- **What.** One session of 453 lines: `schema/mysql.sql` and the seven `INVARIANT_QUERIES` of
  `store.py`, both at `6d8a232`, and the SQL blocks of sections 2 and 3, as they were in the
  outline then. Its SHA-256,
  `447ef025fb0b44424b16197f112b4008510b73c8f2edeaa5fd4f639fbb7a9186`, was recorded before the run
  and was checked at the start of it.
- **Result.** `mysql` exited 0, with no error and no warning. All 82 expected rows of section 4
  equal the actual rows byte for byte, header lines included: Q0 1, Q1 20, Q2 20, Q2b 1, Q3a 16,
  Q3b 17, and the invariant queries 7. There is no mismatch, so no correction is proposed.
- **Frozen expectations.** The expected rows were written at 16:19:37 and the run's output at
  17:13:57; the expected rows have not changed since. The seven expected files and the seven result
  sets, each concatenated in name order, have the same SHA-256 (`5e7d06cb2e3ca3a1…`).
- **What it shows.** On these made-up rows, in MySQL 8.4.13, the queries return what the verdict
  rules of the outline say they should. It shows nothing about real batches or the job system.
- **Accepted** by the author on 2026-10-24 as tooling evidence, not as approval of Part A. The
  harness runs these queries from `src/etf_risk/jobs/crosscheck.sql`, which
  tests/test_jobs_harness.py holds equal to section 2 byte for byte, so neither can change alone.
```

## 83. Assistant — 2026-10-24T07:26:04.430Z

### Tool call: Bash

```
{
  "command": "sed -n '1,/^-- Q2\\./p' src/etf_risk/jobs/crosscheck.sql; echo ......; sed -n '/^-- Q3a\\./,$p' src/etf_risk/jobs/crosscheck.sql",
  "description": "Read the frozen crosscheck DDL, Q0, Q1 and Q3 queries"
}
```

## 84. User — 2026-10-24T07:26:05.207Z

### Tool result

```
-- The recovery experiments' SQL cross-check (docs/recovery-experiments.md, section 7): the
-- harness's TEMPORARY tables, then Q0-Q3b, run by etf_risk.jobs.harness in the final snapshot.
-- Everything below the line of dashes is the SQL of docs/recovery-sql.md, section 2, byte for
-- byte, as validated against MySQL 8.4.13 on 2026-10-23 (82 of 82 expected rows);
-- tests/test_jobs_harness.py checks that the two agree, so neither can change alone.
--
-- AI contribution: drafted with Claude Code (Opus 5.5); the author decides whether to keep it.
-- ------------------------------------------------------------------------------------------
-- The harness's records, in the cross-check's session only.
-- batch_jobs: each job the harness submitted in this batch, its case and its deadline (4.2).
CREATE TEMPORARY TABLE batch_jobs (
    job_id              BIGINT UNSIGNED NOT NULL,
    case_id             VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    deadline_from       VARCHAR(9) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,  -- injection, submit
    deadline_s          DOUBLE NOT NULL,
    deadline_mono       DOUBLE NOT NULL,
    max_lag_s           DOUBLE NOT NULL,
    PRIMARY KEY (job_id)
);
-- deadline_observations: one row per job (4.3); status is NULL when the read failed.
CREATE TEMPORARY TABLE deadline_observations (
    job_id              BIGINT UNSIGNED NOT NULL,
    observed_from_mono  DOUBLE NOT NULL,
    observed_to_mono    DOUBLE NOT NULL,
    status              VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NULL,
    attempt_number      INT UNSIGNED NULL,
    accepted_attempt    INT UNSIGNED NULL,
    PRIMARY KEY (job_id)
);
-- worker_accepts: one row per `accepted` event in the worker logs: store_id and worker_id from the
-- log's context, pid, and the event's job_id, attempt and digest.
CREATE TEMPORARY TABLE worker_accepts (
    store_id            CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    worker_id           VARCHAR(128) NOT NULL,
    pid                 INT UNSIGNED NOT NULL,
    job_id              BIGINT UNSIGNED NOT NULL,
    attempt_number      INT UNSIGNED NOT NULL,
    result_digest       CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL
);

-- Q0. Snapshot fingerprint (4.5): equal in the cross-check, in the export and after the export.
SELECT
    (SELECT COUNT(*) FROM jobs) AS n_jobs,
    (SELECT COALESCE(SUM(version), 0) FROM jobs) AS sum_version,
    (SELECT COUNT(*) FROM job_attempts) AS n_attempts,
    (SELECT COALESCE(SUM(renewals), 0) FROM job_attempts) AS sum_renewals;

-- Q1. Database acceptance correctness (6.2), one row per job, from the job tables alone.
WITH attempts AS (
    SELECT
        job_id,
        COUNT(*) AS n_claims,
        SUM(CASE WHEN outcome = 'accepted' THEN 1 ELSE 0 END) AS n_accepted,
        SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) AS n_failed,
        SUM(CASE WHEN outcome = 'expired' THEN 1 ELSE 0 END) AS n_expired,
        SUM(CASE WHEN outcome = 'running' THEN 1 ELSE 0 END) AS n_running,
        COUNT(DISTINCT worker_id) AS n_workers,
        MIN(CASE WHEN outcome = 'accepted' THEN attempt_number END) AS accepted_number,
        MIN(CASE WHEN outcome = 'accepted' THEN result_digest END) AS accepted_digest
    FROM job_attempts
    GROUP BY job_id
)
SELECT
    j.job_id,
    j.status,
    j.attempt_number,
    j.max_attempts,
    j.accepted_attempt,
    COALESCE(a.n_claims, 0) AS n_claims,
    COALESCE(a.n_accepted, 0) AS n_accepted,
    COALESCE(a.n_failed, 0) AS n_failed,
    COALESCE(a.n_expired, 0) AS n_expired,
    COALESCE(a.n_running, 0) AS n_running,
    COALESCE(a.n_workers, 0) AS n_workers,
    a.accepted_digest,
    CASE
        WHEN COALESCE(a.n_accepted, 0) > 1
            THEN 'more than one accepted attempt'
        WHEN j.status = 'succeeded' AND COALESCE(a.n_accepted, 0) = 0
            THEN 'succeeded without an accepted attempt'
        WHEN j.status = 'succeeded' AND a.accepted_number <> j.accepted_attempt
            THEN 'accepted_attempt names another attempt'
        WHEN j.status <> 'succeeded' AND COALESCE(a.n_accepted, 0) = 1
            THEN 'accepted attempt of a job that did not succeed'
        WHEN COALESCE(a.n_claims, 0) <> j.attempt_number
            THEN 'attempt rows differ from attempt_number'
        WHEN j.status IN ('queued', 'running')
            THEN 'not finished'
        WHEN COALESCE(a.n_running, 0) > 0
            THEN 'finished with an attempt still running'
        WHEN j.status = 'failed'
            THEN 'failed'
        ELSE 'ok'
    END AS verdict
FROM jobs AS j
LEFT JOIN attempts AS a ON a.job_id = j.job_id
ORDER BY j.job_id;

-- Q2. Timeliness (4.2), one row per job the harness submitted. deadline_met is yes, no or
......
-- Q3a. Event-log completeness (6.4), one row per succeeded job. Only this store's reports count,
-- and a report matches only with the full identity of the job's accepted attempt.
WITH reports AS (
    SELECT
        w.job_id,
        COUNT(*) AS n_reports,
        COUNT(DISTINCT w.attempt_number) AS n_reported_attempts,
        SUM(CASE WHEN a.job_id IS NOT NULL AND w.attempt_number = j.accepted_attempt THEN 1 ELSE 0 END)
            AS n_matching
    FROM worker_accepts AS w
    JOIN job_store AS s ON s.store_id = w.store_id
    JOIN jobs AS j ON j.job_id = w.job_id
    LEFT JOIN job_attempts AS a
        ON a.job_id = w.job_id
        AND a.attempt_number = w.attempt_number
        AND a.outcome = 'accepted'
        AND CAST(a.worker_id AS BINARY) = CAST(w.worker_id AS BINARY)
        AND a.result_digest = w.result_digest
    GROUP BY w.job_id
)
SELECT
    j.job_id,
    j.accepted_attempt,
    COALESCE(r.n_reports, 0) AS n_reports,
    COALESCE(r.n_matching, 0) AS n_matching,
    COALESCE(r.n_reported_attempts, 0) AS n_reported_attempts,
    CASE
        WHEN COALESCE(r.n_reported_attempts, 0) > 1
            THEN 'acceptance reported for more than one attempt'
        WHEN COALESCE(r.n_matching, 0) = 0
            THEN 'no matching report'
        WHEN r.n_matching > 1
            THEN 'one attempt reported more than once'
        ELSE 'reported once'
    END AS log_verdict
FROM jobs AS j
LEFT JOIN reports AS r ON r.job_id = j.job_id
WHERE j.status = 'succeeded'
ORDER BY j.job_id;

-- Q3b. Report identity (6.4), one row per report.
SELECT
    w.store_id,
    w.worker_id,
    w.pid,
    w.job_id,
    w.attempt_number,
    CASE
        WHEN w.store_id <> s.store_id
            THEN 'other store'
        WHEN a.job_id IS NULL
            THEN 'no such attempt'
        WHEN CAST(w.worker_id AS BINARY) <> CAST(a.worker_id AS BINARY)
            THEN 'wrong worker'
        WHEN a.outcome <> 'accepted'
            THEN 'attempt not accepted'
        WHEN w.result_digest <> a.result_digest
            THEN 'wrong digest'
        ELSE 'matches'
    END AS report_verdict
FROM worker_accepts AS w
CROSS JOIN job_store AS s
LEFT JOIN job_attempts AS a
    ON a.job_id = w.job_id
    AND a.attempt_number = w.attempt_number
ORDER BY w.job_id, w.attempt_number, w.worker_id, w.store_id;
```

## 85. Assistant — 2026-10-24T07:26:19.394Z

### Tool call: Bash

```
{
  "command": "cat src/etf_risk/jobs/schema/sqlite.sql | head -120",
  "description": "Read the SQLite job schema"
}
```

## 86. User — 2026-10-24T07:26:20.067Z

### Tool result

```
-- SQLite copy of schema/mysql.sql for the offline tests: the same tables, columns and
-- constraint names (tests/test_jobs_store.py compares them). What differs: STRICT tables
-- with SQLite's types; times are UTC text with microseconds ('YYYY-MM-DD HH:MM:SS.ffffff',
-- fixed width, so comparing the text compares the times); JSON is text; and jobs declares
-- its foreign key to job_attempts inline, since SQLite cannot add a constraint to an
-- existing table. Foreign keys are enforced only with PRAGMA foreign_keys = ON, which
-- store.open_sqlite() sets on every connection.
--
-- AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_store.py
-- (constraints, schema drift).

CREATE TABLE job_store (
    id               INTEGER PRIMARY KEY,
    store_id         TEXT    NOT NULL,
    schema_version   INTEGER NOT NULL,
    created_at       TEXT    NOT NULL,
    CONSTRAINT job_store_one_row CHECK (id = 1)
) STRICT;

CREATE TABLE jobs (
    job_id           INTEGER PRIMARY KEY,
    params           TEXT    NOT NULL,
    input_checksums  TEXT    NOT NULL,
    status           TEXT    NOT NULL,
    max_attempts     INTEGER NOT NULL,
    attempt_number   INTEGER NOT NULL,
    attempt_token    TEXT,
    lease_expires_at TEXT,
    accepted_attempt INTEGER,
    error            TEXT,
    version          INTEGER NOT NULL,
    created_at       TEXT    NOT NULL,
    updated_at       TEXT    NOT NULL,
    finished_at      TEXT,
    published_at     TEXT,
    CONSTRAINT jobs_status CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    CONSTRAINT jobs_running_has_lease
        CHECK ((status = 'running') = (attempt_token IS NOT NULL AND lease_expires_at IS NOT NULL)),
    CONSTRAINT jobs_succeeded_has_one_result CHECK ((status = 'succeeded') = (accepted_attempt IS NOT NULL)),
    CONSTRAINT jobs_failed_has_error CHECK ((status = 'failed') = (error IS NOT NULL)),
    CONSTRAINT jobs_finished CHECK ((status IN ('succeeded', 'failed')) = (finished_at IS NOT NULL)),
    CONSTRAINT jobs_attempt_limit CHECK (max_attempts >= 1 AND attempt_number <= max_attempts),
    CONSTRAINT jobs_queued_has_attempts_left CHECK (status <> 'queued' OR attempt_number < max_attempts),
    CONSTRAINT jobs_published_only_queued CHECK (status = 'queued' OR published_at IS NULL),
    CONSTRAINT jobs_accepted_attempt
        FOREIGN KEY (job_id, accepted_attempt) REFERENCES job_attempts (job_id, attempt_number)
) STRICT;

CREATE TABLE job_attempts (
    job_id           INTEGER NOT NULL,
    attempt_number   INTEGER NOT NULL,
    attempt_token    TEXT    NOT NULL,
    worker_id        TEXT    NOT NULL,
    run_id           TEXT    NOT NULL,
    output_dir       TEXT    NOT NULL,
    outcome          TEXT    NOT NULL,
    error            TEXT,
    result_digest    TEXT,
    claimed_at       TEXT    NOT NULL,
    lease_expires_at TEXT    NOT NULL,
    renewals         INTEGER NOT NULL,
    ended_at         TEXT,
    PRIMARY KEY (job_id, attempt_number),
    CONSTRAINT job_attempts_token UNIQUE (attempt_token),
    CONSTRAINT job_attempts_run_id UNIQUE (run_id),
    CONSTRAINT job_attempts_job FOREIGN KEY (job_id) REFERENCES jobs (job_id),
    CONSTRAINT job_attempts_outcome CHECK (outcome IN ('running', 'accepted', 'failed', 'expired')),
    CONSTRAINT job_attempts_ended CHECK ((outcome = 'running') = (ended_at IS NULL)),
    CONSTRAINT job_attempts_failed_has_error CHECK ((outcome = 'failed') = (error IS NOT NULL)),
    CONSTRAINT job_attempts_accepted_has_digest CHECK ((outcome = 'accepted') = (result_digest IS NOT NULL))
) STRICT;
```

## 87. Assistant — 2026-10-24T07:26:43.264Z

### Tool call: Bash

```
{
  "command": "cat tests/test_jobs_harness.py; grep -n -E 'INVARIANT_QUERIES|def invariant_violations' -A6 src/etf_risk/jobs/store.py | head -60",
  "description": "Read the harness tests and the store's invariant queries"
}
```

## 88. User — 2026-10-24T07:26:43.975Z

### Tool result

````
"""The recovery harness's offline parts (etf_risk.jobs.harness): plans, deadlines, the
partition's owner from assignment events, worker reports, memory peaks by segment, the
cross-check SQL, fingerprints and the duration estimate. The batch itself needs the services and
the snapshot, and has not run: no formal experiment.

The cross-check SQL must stay the SQL validated on 2026-10-23 (docs/recovery-sql.md, section 6):
crosscheck.sql below its separator equals the document's SQL blocks, byte for byte.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import json
import re
from collections import Counter
from pathlib import Path

import pytest

from etf_risk.jobs import harness
from etf_risk.jobs.timing import DEFAULT_TIMING

REPO = Path(__file__).resolve().parents[1]
DEFAULTS = harness.Settings()


def test_a_plan_has_three_jobs_of_every_case_in_an_order_fixed_by_its_seed():
    jobs = harness.plan_jobs(DEFAULTS, seed=7)
    assert len(jobs) == 42 and Counter(jobs) == {case: 3 for case in harness.CASES}
    assert jobs == harness.plan_jobs(DEFAULTS, seed=7) != harness.plan_jobs(DEFAULTS, seed=8)


def test_the_deadlines_at_the_default_clock():
    """P3, revised: B plus twice the slowest step sum, rounded up to 5 s; K2, D1 and D2 count from
    their service's return, so no restart duration is assumed."""
    d = {case: harness.deadline_seconds(case, DEFAULT_TIMING, DEFAULTS) for case in harness.CASES}
    assert d == {"C0": 75, "W1": 90, "W2": 140, "W3": 140, "W4": 140, "W5a": 75, "W5b": 75, "W6": 140,
                 "W7": 170, "K1": 75, "K2": 125, "D1": 140, "D2": 140, "X1": 75}
    assert {case: harness.deadline_reference(case) for case in ("C0", "W3", "K2", "D1", "D2", "X1")} == {
        "C0": "submit", "W3": "injection", "K2": "restored", "D1": "restored", "D2": "restored", "X1": "injection"}


def test_w7_waits_for_the_later_of_the_takeover_and_the_end_of_the_stopped_tree():
    short = harness.Settings(w7_stop_s=10.0)
    assert harness.bound_to_next_run("W7", DEFAULT_TIMING, short) == 65.0          # the takeover decides
    assert harness.bound_to_next_run("W7", DEFAULT_TIMING, DEFAULTS) == 90.0 + 2 * 0.5 + 7.0


def assigned(mono, *partitions, pid=1):
    return {"event": "assigned", "mono": mono, "pid": pid, "partitions": [["t", p] for p in partitions]}


def test_the_owner_comes_from_the_assignment_events_of_live_workers_only():
    logs = {"A": [{"event": "started", "mono": 1}, assigned(2, 0)],
            "B": [{"event": "started", "mono": 3}, assigned(4)]}
    assert harness.owner(logs, {"A", "B"}) == "A"
    logs["A"].append({"event": "revoked", "mono": 5, "partitions": [["t", 0]]})
    logs["B"].append(assigned(6, 0))
    assert harness.owner(logs, {"A", "B"}) == "B"
    assert harness.owner(logs, {"A"}) is None                                    # B died holding it
    logs["B"].append({"event": "started", "mono": 7})                            # B restarted: holds nothing yet
    assert harness.owner(logs, {"A", "B"}) is None
    both = {"A": [assigned(1, 0)], "B": [assigned(2, 0)]}
    assert harness.owner(both, {"A", "B"}) is None                               # never guessed


def test_worker_reports_carry_the_logs_identity():
    logs = {"A": [{"event": "accepted", "store_id": "s" * 32, "worker_id": "A", "pid": 11, "job_id": 3, "attempt": 2,
                   "digest": "d" * 64}, {"event": "claimed", "job_id": 4}]}
    assert harness.worker_accepts(logs) == [("s" * 32, "A", 11, 3, 2, "d" * 64)]


def test_peaks_by_segment_keep_the_maximum_and_mark_a_lost_reading():
    book = harness.PeakBook()
    book.add("mysql", 300 * 2**20, 512 * 2**20, "mysql stop")                    # closes the first segment
    book.add("mysql", 200 * 2**20, 512 * 2**20, None)                            # restarted: a new, lower count
    peak = book.batch_peak("mysql")
    assert (peak["peak_bytes"], peak["incomplete"], peak["readings"]) == (300 * 2**20, False, 2)
    book.add("mysql", None, None, "end")
    assert book.batch_peak("mysql")["incomplete"] is True
    assert book.batch_peak("kafka")["incomplete"] is True                         # never read
    assert [harness.memory_verdict(f, DEFAULTS) for f in (None, 0.5, 0.91, 0.96)] == ["unknown", "ok", "flag", "stop"]


def doc_blocks() -> list[str]:
    doc = (REPO / "docs" / "recovery-sql.md").read_text()
    blocks = re.findall(r"^```sql\n(.*?)^```$", doc, flags=re.S | re.M)
    prefixes = ("-- The harness's records", "-- Q0.", "-- Q1.", "-- Q2.", "-- Q2b.", "-- Q3a.", "-- Q3b.")
    return [next(b for b in blocks if b.startswith(p)) for p in prefixes]


def test_crosscheck_sql_is_the_validated_sql_byte_for_byte():
    text = harness.CROSSCHECK_SQL.read_text()
    body = text.split("\n", next(i for i, line in enumerate(text.splitlines()) if harness._SEPARATOR.match(line)) + 1)[-1]
    assert body == "\n".join(doc_blocks())


def test_the_crosscheck_statements_come_in_order_with_their_names():
    names = [name for name, _ in harness.crosscheck_statements()]
    assert names == ["DDL", "DDL", "DDL", "Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b"]
    assert all(sql.rstrip().endswith(";") for _, sql in harness.crosscheck_statements())


def test_the_exported_fingerprint_counts_jobs_versions_attempts_and_renewals(tmp_path):
    (tmp_path / "jobs.json").write_text(json.dumps([{"version": 4}, {"version": 7}]))
    (tmp_path / "job_attempts.json").write_text(json.dumps([{"renewals": 2}, {"renewals": 1}, {"renewals": 2}]))
    assert harness.fingerprint_from_export(tmp_path) == {"n_jobs": 2, "sum_version": 11, "n_attempts": 3,
                                                         "sum_renewals": 5}


def test_settings_refuse_unknown_names_and_cases_and_survive_a_plan(tmp_path):
    with pytest.raises(ValueError, match="unknown settings"):
        harness.Settings.from_dict({"jobs_per_kase": 3})
    with pytest.raises(ValueError, match="unknown cases"):
        harness.Settings.from_dict({"cases": ["C0", "W9"]})
    plan = harness.make_plan(DEFAULTS, seed=1)
    again = json.loads(json.dumps(plan))
    assert harness.Settings.from_dict(again["settings"]) == DEFAULTS and len(again["jobs"]) == 42
    assert again["deadlines_s"]["W7"] == 170 and set(again["code"]) >= {"source_digest", "uv_lock_sha256"}


def test_the_estimate_of_a_default_batch_and_what_each_case_costs():
    """Under Assumptions (none measured): 1,403 s for one job of each case, 4,389 s for 42 jobs."""
    result = harness.estimate(harness.make_plan(DEFAULTS, seed=1))
    per = result["per_case_s"]
    assert (per["C0"], per["W1"], per["W4"], per["W7"], per["K2"], per["D1"], per["D2"]) == (42, 74, 159, 159, 118, 116,
                                                                                            149)
    assert sum(per.values()) == 1403 and result["batch_s"] == 3 * 1403 + 180 == 4389
154:INVARIANT_QUERIES = {
155-    "succeeded without exactly one accepted attempt":
156-        "SELECT j.job_id FROM jobs j WHERE j.status = 'succeeded' AND 1 <>"
157-        " (SELECT COUNT(*) FROM job_attempts a WHERE a.job_id = j.job_id AND a.outcome = 'accepted')",
158-    "accepted attempt of a job that did not succeed":
159-        "SELECT DISTINCT a.job_id FROM job_attempts a JOIN jobs j ON j.job_id = a.job_id"
160-        " WHERE a.outcome = 'accepted' AND j.status <> 'succeeded'",
--
573:    def invariant_violations(self) -> dict[str, list[int]]:
574:        """The jobs breaking each invariant in INVARIANT_QUERIES, read in one transaction;
575-        empty when all hold. The tests run it after every scenario; the recovery experiments
576-        (E1) can run it on MySQL."""
577-        with self._transaction():
578-            found = {name: [row[0] for row in self._execute(sql).fetchall()]
579:                     for name, sql in INVARIANT_QUERIES.items()}
580-        return {name: job_ids for name, job_ids in found.items() if job_ids}
581-
582-    def _refusal(self, job_id: int, now: datetime) -> Refusal:
583-        """Why both of claim's guards failed, read inside claim's transaction."""
584-        job = self._fetch_one("SELECT status, attempt_number, max_attempts, attempt_token, lease_expires_at"
585-                              " FROM jobs WHERE job_id = :job_id", job_id=job_id)
````

## 89. Assistant — 2026-10-24T07:27:39.956Z

### Tool call: Bash

```
{
  "command": "sed -n 80,200p src/etf_risk/jobs/simulated.py; grep -n -E 'events.log\\(\"' src/etf_risk/jobs/pipeline.py src/etf_risk/jobs/reconciler.py src/etf_risk/jobs/cli.py | head -40",
  "description": "Read MemoryQueue and the events the pipeline and reconciler log"
}
```

## 90. User — 2026-10-24T07:27:40.720Z

### Tool result

```
class PublishOutcome(StrEnum):
    CONFIRMED = "confirmed"        # written, and the confirmation arrived
    UNCONFIRMED = "unconfirmed"    # written, but the confirmation was lost
    DROPPED = "dropped"            # not written


class MemoryQueue:
    """One topic with one partition, in memory: the Kafka behaviour the job system relies on.

    Messages keep their order. Each consumer group has a committed offset. A consumer starts
    at its group's committed offset, or at the earliest message for a group that never
    committed (auto.offset.reset=earliest), and moves on as it polls, whether it commits or
    not; a new consumer of the group stands in for a restarted worker."""

    def __init__(self) -> None:
        self.messages: list[bytes] = []
        self.committed: dict[str, int] = {}

    def publisher(self, outcomes: Iterable[PublishOutcome] = ()) -> MemoryPublisher:
        """A publisher whose publications end as `outcomes` says, one by one, then confirmed."""
        return MemoryPublisher(self, outcomes)

    def consumer(self, group: str, *, failing_commits: int = 0) -> MemoryConsumer:
        """A consumer of the group; its first `failing_commits` commits raise."""
        return MemoryConsumer(self, group, failing_commits)

    def job_ids(self) -> list[int | None]:
        return [Delivery(value, offset).job_id() for offset, value in enumerate(self.messages)]


class MemoryPublisher:
    def __init__(self, queue: MemoryQueue, outcomes: Iterable[PublishOutcome]):
        self.queue = queue
        self._outcomes = iter(outcomes)

    def publish(self, job_id: int) -> bool:
        outcome = next(self._outcomes, PublishOutcome.CONFIRMED)
        if outcome is not PublishOutcome.DROPPED:
            self.queue.messages.append(encode(job_id))
        return outcome is PublishOutcome.CONFIRMED


class MemoryConsumer:
    def __init__(self, queue: MemoryQueue, group: str, failing_commits: int):
        self.queue, self.group = queue, group
        self.position = queue.committed.get(group, 0)
        self._failing_commits = failing_commits

    def poll(self, timeout: float = 0.0) -> Delivery | None:
        if self.position >= len(self.queue.messages):
            return None
        delivery = Delivery(self.queue.messages[self.position], self.position)
        self.position += 1
        return delivery

    def commit(self, delivery: Delivery) -> None:
        if self._failing_commits:
            self._failing_commits -= 1
            raise ConnectionError(f"the commit of offset {delivery.position} failed (simulated)")
        self.queue.committed[self.group] = delivery.position + 1

    def rewind(self, delivery: Delivery) -> None:
        self.position = delivery.position

    def close(self) -> None:
        pass
src/etf_risk/jobs/reconciler.py:69:                self.events.log("requeued", job_id=lease.job_id)
src/etf_risk/jobs/reconciler.py:72:                self.events.log("exhausted", job_id=lease.job_id)
src/etf_risk/jobs/reconciler.py:75:                self.events.log("stale", job_id=lease.job_id, during="requeue")
src/etf_risk/jobs/reconciler.py:82:                self.events.log("unconfirmed", job_id=job.job_id)
src/etf_risk/jobs/reconciler.py:85:                self.events.log("published", job_id=job.job_id, attempts_so_far=job.attempt_number)
src/etf_risk/jobs/reconciler.py:88:                self.events.log("stale", job_id=job.job_id, during="publication")
src/etf_risk/jobs/reconciler.py:99:                self.events.log("pass_failed", error=f"{type(error).__name__}: {error}"[:500])
src/etf_risk/jobs/cli.py:187:    events.log("started", code=code_identity())
src/etf_risk/jobs/cli.py:192:            events.log("submit_unknown", error=f"{type(error).__name__}: {error}"[:500])
src/etf_risk/jobs/cli.py:204:        events.log("record_failed", job_id=job_id, error=f"{type(error).__name__}: {error}"[:500])
src/etf_risk/jobs/cli.py:205:    events.log("submitted", job_id=job_id, published=published, recorded=recorded, params=params.to_dict())
src/etf_risk/jobs/cli.py:220:    events.log("started", db=safe_url(args.db), topic=args.topic, group=args.group, timing=asdict(timing),
src/etf_risk/jobs/cli.py:235:                events.log("worker_failed", error=f"{type(error).__name__}: {error}"[:1000])
src/etf_risk/jobs/cli.py:238:            events.log("serve_restarted", error=f"{type(error).__name__}: {error}"[:500], backoff_s=backoff)
src/etf_risk/jobs/cli.py:244:    events.log("stopped")
src/etf_risk/jobs/cli.py:257:    events.log("started", db=safe_url(args.db), topic=args.topic, code=code_identity())
src/etf_risk/jobs/cli.py:260:    events.log("stopped")
src/etf_risk/jobs/pipeline.py:116:            self.events.log("renewal_failed", job_id=self.claim.job_id, attempt=self.claim.attempt_number,
src/etf_risk/jobs/pipeline.py:119:        self.events.log("renewed" if ok else "renewal_refused", job_id=self.claim.job_id,
src/etf_risk/jobs/pipeline.py:233:            self.events.log("keepalive_dropped", seq=line.get("seq"))
src/etf_risk/jobs/pipeline.py:247:        self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name,
src/etf_risk/jobs/pipeline.py:295:        self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number,
src/etf_risk/jobs/pipeline.py:380:        events.log("sweep_skipped", error=f"{type(error).__name__}: {error}"[:500])
src/etf_risk/jobs/pipeline.py:405:    events.log("sweep", preserved=len(report["preserved"]), terminated=len(report["terminated"]),
```

## 91. Assistant — 2026-10-24T07:27:59.241Z

### Tool call: Bash

```
{
  "command": "sed -n 1,110p src/etf_risk/jobs/reconciler.py; sed -n 1,80p src/etf_risk/jobs/timing.py",
  "description": "Read the reconciler and the timing constraints"
}
```

## 92. User — 2026-10-24T07:27:59.990Z

### Tool result

```
"""The reconciler (spec §11): requeues jobs whose lease expired and publishes queued jobs
whose publication was never confirmed, each change conditional on the state it read.

One pass, run_once():
1. Expired leases. For each running job whose lease has expired, requeue_expired() with the
   token read: the job returns to queued with no publication recorded, or fails when no
   attempts are left. A job renewed, taken over or finished since the read is left alone.
2. Unconfirmed publications. Each queued job with no publication recorded is published and,
   once the broker confirms, recorded with mark_published() and the version read. A job
   that was never claimed (attempt 0) waits PUBLICATION_GRACE after it was queued: its
   submitter may still be waiting for its own confirmation, for CONFIRMATION_TIMEOUT at
   most, so the grace must be longer. A job that returned to queued has nobody else to
   publish it and goes at once, in the same pass as its requeue.
A duplicate publication is harmless: claim() refuses a delivery that finds the job running
under a live lease or finished. Two reconcilers may run at once; the guards let one change
win, and the other counts it as stale.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_reconciler.py,
tests/test_jobs_queue.py and tests/test_jobs_kafka.py.
"""
from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import timedelta

from etf_risk.jobs.events import NO_EVENTS, EventLog
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
                 confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT, events: EventLog = NO_EVENTS):
        if publication_grace <= confirmation_timeout:
            raise ValueError(f"the publication grace ({publication_grace}) must exceed the confirmation timeout"
                             f" ({confirmation_timeout}), or the reconciler races a submitter still waiting")
        self.store = store
        self.publisher = publisher
        self.publication_grace = publication_grace
        self.events = events

    def run_once(self) -> Pass:
        """One pass; each job it changed or left alone is an event (requeued, failed, stale,
        published, unconfirmed), for the recovery experiments' timings."""
        done = Pass()
        for lease in self.store.expired_leases():
            status = self.store.requeue_expired(lease.job_id, lease.token)
            if status is Status.QUEUED:
                done.requeued += 1
                self.events.log("requeued", job_id=lease.job_id)
            elif status is Status.FAILED:
                done.failed += 1
                self.events.log("exhausted", job_id=lease.job_id)
            else:
                done.stale += 1
                self.events.log("stale", job_id=lease.job_id, during="requeue")
        now = self.store.clock.now()
        for job in self.store.unconfirmed():
            if job.attempt_number == 0 and now - job.queued_since < self.publication_grace:
                done.waiting += 1
            elif not self.publisher.publish(job.job_id):
                done.unconfirmed += 1
                self.events.log("unconfirmed", job_id=job.job_id)
            elif self.store.mark_published(job.job_id, job.version):
                done.published += 1
                self.events.log("published", job_id=job.job_id, attempts_so_far=job.attempt_number)
            else:
                done.stale += 1
                self.events.log("stale", job_id=job.job_id, during="publication")
        return done

    def run(self, stop: threading.Event, *, interval: timedelta = RECONCILE_INTERVAL) -> None:
        """Pass after pass until stop is set. A pass that raises is logged, and the next one
        starts after the interval."""
        while not stop.is_set():
            try:
                done = self.run_once()
            except Exception as error:
                log.exception("reconciler pass failed")
                self.events.log("pass_failed", error=f"{type(error).__name__}: {error}"[:500])
            else:
                log.info("reconciler pass: %s", done)
            stop.wait(interval.total_seconds())
"""The job processes' time settings and the relations between them (spec §11;
docs/job-queue.md, "Deadlines").

Leases are wall-clock times in the job table. Every local deadline uses the host's monotonic
clock (time.monotonic()), the same clock in the worker and its launchers:
- After each successful renewal, the worker sends its launcher the absolute deadline
  F = m0 + lease - fence_margin. m0 is the monotonic time just before that renewal started;
  the lease in the table began at or after m0.
- The launcher ends the step's process tree once F has passed: within watchdog_tick, then
  term_grace after SIGTERM, then kill_confirm after SIGKILL.

The tree is therefore gone by F + watchdog_tick + kill_grace, before the lease can expire
(m0 + lease), whenever fence_margin >= watchdog_tick + kill_grace + safety. That holds
whatever the worker is doing: blocked in a database call, stopped, or dead. Safety (no
overlapping Spark work) rests on this watchdog and the host execution lock, never on how long
a database operation takes. The database timeouts (mysql.SERVICE_SESSION) serve liveness
only. Correctness (one accepted result per job) never depends on time: the token guards in
store.py decide it.

check() refuses settings that break any of these relations:
- fence_margin >= watchdog_tick + kill_grace + safety: the watchdog finishes before the lease
  can expire;
- renew_interval + worker_tick < lease - fence_margin: a renewal comes before the deadline;
- Kafka's session timeout at least the broker's 6 s minimum, at least three heartbeats, and
  below the lease, so a standby takes over a stalled worker's partition before its job can
  be requeued;
- max_poll_interval above the attempt limit plus the kill grace, so a legitimate run never
  makes the worker leave its consumer group.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_timing.py.
"""
from __future__ import annotations

from dataclasses import dataclass

from etf_risk.jobs.store import DEFAULT_LEASE

BROKER_MIN_SESSION_TIMEOUT = 6.0   # Kafka's group.min.session.timeout.ms default, in seconds


@dataclass(frozen=True)
class Timing:
    """Seconds throughout. The defaults are the M2 drafts of spec §11; change them only
    together with check()."""
    lease: float = DEFAULT_LEASE.total_seconds()
    renew_interval: float = 10.0
    fence_margin: float = 10.0          # M
    worker_tick: float = 1.0
    watchdog_tick: float = 0.5          # t_w
    term_grace: float = 5.0             # after SIGTERM, before SIGKILL
    kill_confirm: float = 2.0           # after SIGKILL, before the tree must be gone
    safety: float = 2.5                 # ε
    windows_limit: float = 120.0
    spark_pipeline_limit: float = 600.0
    verify_limit: float = 300.0
    attempt_limit: float = 900.0
    lock_slack: float = 30.0
    poll_slack: float = 60.0
    session_timeout: float = 15.0
    heartbeat_interval: float = 3.0
    socket_timeout: float = 10.0

    @property
    def kill_grace(self) -> float:
        """G: the longest an ending tree takes once the watchdog acted."""
        return self.term_grace + self.kill_confirm

    def step_limit(self, step: str) -> float:
        return {"windows": self.windows_limit, "spark_pipeline": self.spark_pipeline_limit,
                "verify": self.verify_limit}[step]

    def lock_wait(self, step: str) -> float:
        """How long a launcher waits for the host lock, and for an earlier tree to end."""
        return self.step_limit(step) + self.kill_grace + self.lock_slack

    @property
    def max_poll_interval(self) -> float:
        return self.attempt_limit + self.kill_grace + self.poll_slack

    def check(self) -> Timing:
```

## 93. Assistant — 2026-10-24T07:28:17.487Z

### Tool call: Bash

```
{
  "command": "sed -n 150,330p src/etf_risk/jobs/cli.py",
  "description": "Read the CLI's submit, worker, reconciler and export commands"
}
```

## 94. User — 2026-10-24T07:28:18.199Z

### Tool result

```
                cursor.execute("SHOW TABLES LIKE 'job_store'")
                has_store = cursor.fetchone() is not None
            if has_jobs and not has_store:
                raise SystemExit(f"{safe_url(args.db)} holds job tables of an earlier schema; use a new database")
            if not has_jobs:
                mysql.create_schema(conn)
        finally:
            conn.close()
    store = open_store(args.db, DEFAULT_TIMING)
    print(json.dumps({"store_id": store.ensure_identity(), "db": safe_url(args.db)}))
    return 0


def cmd_create_topic(args) -> int:
    from etf_risk.jobs.kafka import create_topic
    try:
        create_topic(args.bootstrap, args.topic)
    except Exception as error:
        if "TOPIC_ALREADY_EXISTS" not in str(error):
            raise
        print(f"{args.topic}: exists already")
        return 0
    print(f"{args.topic}: created (one partition, no replica)")
    return 0


def cmd_submit(args) -> int:
    from etf_risk.jobs.kafka import KafkaPublisher
    timing = timing_from(args.timing)
    try:
        params = JobParams(args.snapshot, args.kind, window_days=args.window_days, stride=args.stride,
                           anchor=args.anchor, sample_ticker=args.sample_ticker)
        checksums = input_checksums(resolve(args.processed_root), params.snapshot)
    except InvalidParams as error:
        raise SystemExit(f"submit: {error}") from None
    store = open_store(args.db, timing)
    events = EventLog(Path(events_root(args)) / "submit.jsonl", "submit", store_id=store.store_id())
    events.log("started", code=code_identity())
    try:
        job_id = store.submit(params.to_dict(), checksums, max_attempts=args.max_attempts)
    except Exception as error:
        if store.dialect.is_disconnect(error):
            events.log("submit_unknown", error=f"{type(error).__name__}: {error}"[:500])
            print("submit: the database connection broke during the insert; the job may or may not exist."
                  " Check with `status` before submitting again.", file=sys.stderr)
            return OUTCOME_UNKNOWN
        raise
    publisher = KafkaPublisher(args.bootstrap, args.topic, timing=timing)
    published = publisher.publish(job_id)
    publisher.close()
    recorded = False
    try:
        recorded = published and store.mark_published(job_id, version=0)
    except Exception as error:                            # the reconciler publishes it again after the grace
        events.log("record_failed", job_id=job_id, error=f"{type(error).__name__}: {error}"[:500])
    events.log("submitted", job_id=job_id, published=published, recorded=recorded, params=params.to_dict())
    print(json.dumps({"job_id": job_id, "published": published, "recorded": recorded}))
    return 0


def cmd_worker(args) -> int:
    from etf_risk.jobs.kafka import KafkaConsumer
    from etf_risk.jobs.worker import Worker
    timing = timing_from(args.timing)
    stop = stop_on_signals()
    store = open_store(args.db, timing)
    store_id = store.store_id()
    output_root = resolve(args.output_root) / store_id
    worker_id = args.worker_id or f"worker-{socket.gethostname().split('.')[0]}-{os.getpid()}"
    events = EventLog(Path(events_root(args)) / f"{worker_id}.jsonl", "worker", store_id=store_id, worker_id=worker_id)
    events.log("started", db=safe_url(args.db), topic=args.topic, group=args.group, timing=asdict(timing),
               standby=args.standby, code=code_identity(), fault_file=os.environ.get(FAULT_FILE_ENV))
    startup_sweep(store, output_root, timing=timing, events=events)
    pipeline = SubprocessPipeline(store_id=store_id, processed_root=resolve(args.processed_root), worker_id=worker_id,
                                  lock_path=args.lock, timing=timing, events=events, stop=stop)
    worker = Worker(store, pipeline, output_root, worker_id=worker_id, events=events,
                    fault=fault_from_environment(events))
    backoff = 1.0
    while not stop.is_set():
        consumer = KafkaConsumer(args.bootstrap, args.topic, args.group, timing=timing, events=events)
        try:
            worker.serve(consumer, stop=stop.is_set)
            backoff = 1.0
        except Exception as error:
            if not is_transport_error(error, store):
                events.log("worker_failed", error=f"{type(error).__name__}: {error}"[:1000])
                log.exception("worker: an error that is not the transport's; stopping")
                return 1
            events.log("serve_restarted", error=f"{type(error).__name__}: {error}"[:500], backoff_s=backoff)
            log.warning("worker: %s; serving again in %.0f s", error, backoff)
            stop.wait(backoff)
            backoff = min(backoff * 2, 30.0)
        finally:
            consumer.close()                               # leave the group at once
    events.log("stopped")
    return 0


def cmd_reconciler(args) -> int:
    from etf_risk.jobs.kafka import KafkaPublisher
    from etf_risk.jobs.reconciler import Reconciler
    timing = timing_from(args.timing)
    stop = stop_on_signals()
    store = open_store(args.db, timing)
    events = EventLog(Path(events_root(args)) / f"reconciler-{os.getpid()}.jsonl", "reconciler",
                      store_id=store.store_id())
    publisher = KafkaPublisher(args.bootstrap, args.topic, timing=timing)
    events.log("started", db=safe_url(args.db), topic=args.topic, code=code_identity())
    Reconciler(store, publisher, events=events).run(stop, interval=timedelta(seconds=args.interval))
    publisher.close()
    events.log("stopped")
    return 0


def rows(records: list[dict]) -> list[dict]:
    return [{k: (v.isoformat() if isinstance(v, datetime) else v.value if hasattr(v, "value") else v)
             for k, v in r.items()} for r in records]


def cmd_status(args) -> int:
    store = open_store(args.db, DEFAULT_TIMING)
    jobs, attempts = store.all_jobs(), store.all_attempts()
    by_job: dict[int, list[dict]] = {}
    for a in attempts:
        by_job.setdefault(a["job_id"], []).append(a)
    counts = {s.value: sum(1 for j in jobs if j["status"] is s) for s in Status}
    print(f"store {store.store_id()}: {len(jobs)} jobs " + ", ".join(f"{n} {s}" for s, n in counts.items() if n))
    for j in jobs if not args.job else [j for j in jobs if j["job_id"] in args.job]:
        outcomes = " ".join(f"{a['attempt_number']}:{a['outcome'].value}" for a in by_job.get(j["job_id"], []))
        accepted = next((a for a in by_job.get(j["job_id"], []) if a["outcome"] is Outcome.ACCEPTED), None)
        print(f"  job {j['job_id']}: {j['status'].value}; attempts {outcomes or '-'}"
              + (f"; accepted {accepted['attempt_number']} ({accepted['result_digest'][:12]})" if accepted else ""))
    if not args.check:
        return 0
    violations = store.invariant_violations()
    print("invariants: " + ("all hold" if not violations else json.dumps(violations)))
    return 1 if violations else 0


def cmd_cleanup(args) -> int:
    store = open_store(args.db, DEFAULT_TIMING)
    root = resolve(args.output_root) / store.store_id()
    attempts = {a["run_id"]: a for a in store.all_attempts()}
    ended, orphans, total = [], [], 0
    for folder in sorted(root.glob("job-*-attempt-*")):
        attempt = attempts.get(folder.name)
        size = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
        if attempt is None:
            orphans.append((folder, size))
        elif attempt["outcome"] in (Outcome.FAILED, Outcome.EXPIRED):
            ended.append((folder, size))
            total += size
    for folder, size in ended:
        print(f"ended, not accepted: {folder}  ({size / 2**20:,.1f} MiB)")
    for folder, size in orphans:
        print(f"no attempt row (another job table?): {folder}  ({size / 2**20:,.1f} MiB)")
    print(f"dry run: {len(ended)} folders ({total / 2**20:,.1f} MiB) could be removed; nothing was deleted")
    return 0


def cmd_export(args) -> int:
    out = Path(args.folder)
    out.mkdir(parents=True, exist_ok=False)
    store = open_store(args.db, DEFAULT_TIMING)
    files = {"jobs.json": rows(store.all_jobs()), "job_attempts.json": rows(store.all_attempts()),
             "invariant_violations.json": store.invariant_violations(),
             "store.json": {"store_id": store.store_id(), "db": safe_url(args.db),
                            "exported_at_utc": datetime.now(timezone.utc).isoformat()},
             "timing.json": asdict(timing_from(args.timing))}
    for name, value in files.items():
        (out / name).write_text(json.dumps(value, indent=2, default=str) + "\n")
    print(f"exported {', '.join(files)} to {out}")
    return 0


def events_root(args) -> Path:
    return Path(args.events) if args.events else resolve(args.output_root) / "events"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs", description=__doc__.splitlines()[0])
```

## 95. Assistant — 2026-10-24T07:28:24.495Z

### Tool call: Bash

```
{
  "command": "grep -n -A22 'def open_store' src/etf_risk/jobs/cli.py; grep -n -E 'def __init__' -A12 src/etf_risk/jobs/store.py | sed -n 1,40p",
  "description": "Check whether the CLI store opener accepts SQLite"
}
```

## 96. User — 2026-10-24T07:28:25.204Z

### Tool result

```
97:def open_store(db: str, timing: Timing) -> JobStore:
98-    """A store that reconnects through its database's connection factory."""
99-    lease = timedelta(seconds=timing.lease)
100-    if db.startswith("sqlite:///"):
101-        path = db[len("sqlite:///"):]
102-        return JobStore(None, SQLITE, lease=lease, connect=lambda: open_sqlite(path, check_same_thread=False))
103-    if db.startswith("mysql://"):
104-        from etf_risk.jobs import mysql
105-        if not urlsplit(db).path.strip("/"):
106-            raise SystemExit("--db: name the database in the URL, as mysql://user:password@host:port/database")
107-        return JobStore(None, mysql.MYSQL, lease=lease, connect=mysql.connector(db, **mysql.SERVICE_SESSION))
108-    raise SystemExit(f"--db: expected mysql://... or sqlite:///..., not {safe_url(db)!r}")
109-
110-
111-def is_transport_error(error: BaseException, store: JobStore) -> bool:
112-    if store.dialect.is_disconnect(error) or isinstance(error, (ClaimRace, ConnectionError, TimeoutError)):
113-        return True
114-    try:
115-        from confluent_kafka import KafkaException
116-    except ImportError:
117-        return False
118-    return isinstance(error, KafkaException) and not error.args[0].fatal()
119-
326:    def __init__(self, connection: Any | None, dialect: Dialect, *, clock: Clock | None = None,
327-                 lease: timedelta = DEFAULT_LEASE, fault: Callable[[str], None] | None = None,
328-                 connect: Callable[[], Any] | None = None):
329-        if connection is None and connect is None:
330-            raise ValueError("give the store a connection or a way to connect")
331-        self.connection = connection
332-        self.connect = connect
333-        self.dialect = dialect
334-        self.clock = clock or SystemClock()
335-        self.lease = lease
336-        self._fault = fault or (lambda point: None)
337-        self._in_transaction = False
338-        self._last_used = time.monotonic()
```

## 97. Assistant — 2026-10-24T07:29:26.996Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^TABLE_KEYS|^def read_table|^import|^from|cpm' analysis/collect_caching_measurements.py | head -20; grep -n -A14 '^def read_table' analysis/collect_caching_measurements.py; grep -n -E '^TABLES|^def total_violations' -A6 src/etf_risk/jobs/pipeline.py | head -30",
  "description": "Check what the accepted-result comparison reads"
}
```

## 98. User — 2026-10-24T07:29:27.743Z

### Tool result

```
29:from __future__ import annotations
31:import argparse
32:import csv
33:import json
34:import statistics
35:import sys
36:from pathlib import Path
38:import pyarrow as pa
39:import pyarrow.parquet as pq
42:import collect_partition_measurements as cpm  # noqa: E402
44:from etf_risk.windows import WINDOW_KEY, ChecksumError, verify_checksums  # noqa: E402
50:SPARK_DEFAULTS = {cpm.PARTITIONS: "200", cpm.ADAPTIVE: "true", cpm.COALESCE: "true"}
70:WINDOWS = cpm.WINDOWS
74:TABLE_KEYS = {"window_stats": list(WINDOW_KEY), "path_days": [*PATH_KEY, "day"], "path_summary": list(PATH_KEY),
76:CRITERIA = cpm.CRITERIA
84:                + [f"files_{table}" for table in cpm.OUTPUT_TABLES] + [f"{table}_vs_reference" for table in TABLE_KEYS])
85:FIELDS = IDENTITY_FIELDS + cpm.MEASUREMENT_FIELDS + EXTRA_FIELDS
88:def read_table(run_dir: Path, name: str) -> pa.Table:
118:        return cpm.load_plans(run_dir)
272:    protocol = cpm.read_json(protocol_path)
88:def read_table(run_dir: Path, name: str) -> pa.Table:
89-    """A table with the ticker partition column as plain strings (path_days is partitioned by ticker)."""
90-    table = pq.read_table(run_dir / name)
91-    if "ticker" in table.column_names and pa.types.is_dictionary(table.schema.field("ticker").type):
92-        table = table.set_column(table.column_names.index("ticker"), "ticker", table["ticker"].cast(pa.string()))
93-    return table
94-
95-
96-def output_state(run_dir: Path, name: str) -> str:
97-    """'' for a complete output table, else why not. Spark writes _SUCCESS when a table's write commits,
98-    so a run that failed or was aborted may leave a table missing or incomplete (7)."""
99-    if not (run_dir / name).is_dir():
100-        return "missing"
101-    return "" if (run_dir / name / "_SUCCESS").is_file() else "incomplete (no _SUCCESS marker)"
102-
88:TABLES = ("window_stats", "path_days", "path_summary", "paired")
89:def total_violations(checks: dict) -> int:
90-    """As spark_pipeline.total_violations, without importing PySpark into the worker."""
91-    return sum(v for group in checks.values() for v in group.values())
92-
93-
94-ENV_ALLOWED = ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "JAVA_HOME", "SHELL", "TERM")
95-DEFAULT_LOCK = Path.home() / ".cache" / "etf-risk" / "locks" / "spark-exec.lock"
```

## 99. Assistant — 2026-10-24T07:29:38.233Z

### Tool call: Bash

```
{
  "command": "sed -n 70,80p analysis/collect_caching_measurements.py; grep -n -E '^PATH_KEY|^WINDOW_KEY|^PAIR' -A2 analysis/collect_caching_measurements.py src/etf_risk/windows.py analysis/collect_partition_measurements.py | head; grep -n -A30 '^def compare_tables' analysis/collect_partition_measurements.py; grep -n -E '^BREACH_FIELDS' -A6 analysis/collect_partition_measurements.py",
  "description": "Read the table keys and the table comparison"
}
```

## 100. User — 2026-10-24T07:29:39.009Z

### Tool result

```
WINDOWS = cpm.WINDOWS
REPEATS = 4
SPARK_VERSION = "4.2.0"
PLANS_FORMAT = 2
TABLE_KEYS = {"window_stats": list(WINDOW_KEY), "path_days": [*PATH_KEY, "day"], "path_summary": list(PATH_KEY),
              "paired": list(WINDOW_KEY)}
CRITERIA = cpm.CRITERIA

IDENTITY_FIELDS = ["batch", "position", "config", "used", "protocol_id", "run_id", "run_number", "warmup", "status",
                   "exit_code"]
EXTRA_FIELDS = (["cache_mode", "plan_capture_status", "plan_capture_s", "wall_excl_capture_s", "sql_executions",
analysis/collect_caching_measurements.py:46:PATH_KEY = [*WINDOW_KEY, "leverage"]
analysis/collect_caching_measurements.py-47-CACHE = {"A": "none", "B": "members", "C": "members-checks"}           # 2.1: --cache per configuration
analysis/collect_caching_measurements.py-48-OPTIONS = {config: {"shuffle_partitions": None, "coalesce": None, "record_plans": True, "cache": mode}
src/etf_risk/windows.py:67:WINDOW_KEY = ["window_kind", "ticker", "window_days", "entry_date"]
src/etf_risk/windows.py-68-
src/etf_risk/windows.py-69-DEFINITION_SCHEMA = pa.schema([
286:def compare_tables(ref: pa.Table, run: pa.Table, key: list[str], breach: list[str],
287-                   rtol: float = RTOL, atol: float = ATOL) -> tuple[list[str], dict]:
288-    """Section 7: (problems, largest differences per floating-point column). Rows are matched by `key`,
289-    and key, breach, string, date, integer and boolean columns must be equal exactly."""
290-    problems, diffs = [], {}
291-    if run.num_rows != ref.num_rows:
292-        problems.append(f"{run.num_rows} rows; the reference has {ref.num_rows}")
293-    ref_types, run_types = ({f.name: f.type for f in t.schema} for t in (ref, run))
294-    if run_types != ref_types:
295-        problems.append(f"columns differ: missing {sorted(set(ref_types) - set(run_types))}, extra "
296-                        f"{sorted(set(run_types) - set(ref_types))}, other type "
297-                        f"{sorted(n for n in set(ref_types) & set(run_types) if ref_types[n] != run_types[n])}")
298-    if any(k not in ref_types or k not in run_types for k in key):
299-        return problems + [f"key columns {key} missing"], diffs
300-    key_problems = []
301-    keysets = {}
302-    for name, table in (("run", run), ("reference", ref)):
303-        if nulls := [k for k in key if table.column(k).null_count]:
304-            key_problems.append(f"{name}: null in key columns {nulls}")
305-        keys = list(zip(*(table.column(k).to_pylist() for k in key)))
306-        keysets[name] = set(keys)
307-        if len(keysets[name]) != len(keys):
308-            key_problems.append(f"{name}: {len(keys) - len(keysets[name])} duplicate keys")
309-    if keysets["run"] != keysets["reference"]:
310-        key_problems.append(f"keys differ: {len(keysets['reference'] - keysets['run'])} missing, "
311-                            f"{len(keysets['run'] - keysets['reference'])} extra")
312-    if key_problems:
313-        return problems + key_problems, diffs
314-    order = [(k, "ascending") for k in key]
315-    ref, run = ref.sort_by(order), run.sort_by(order)
316-    for name in sorted(set(ref_types) & set(run_types) - set(key)):
66:BREACH_FIELDS = {    # 7, item 5
67-    "paired": ["breached_1x", "breached_2x", "breach_date_2x", "breach_day_2x", "last_ok_date_2x", "days_ok_2x"],
68-    "path_summary": ["breached", "n_breach_rows", "breach_day", "breach_date", "last_ok_date", "days_ok"],
69-}
70-COUNTED_TABLES = ("window_stats", "path_days")         # compared by row count only (7)
71-OUTPUT_TABLES = ("window_stats", "path_days", "path_summary", "paired")
72-PHASES = ("window_stats", "model", "summaries", "checks")
```

## 101. Assistant — 2026-10-24T07:30:12.254Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^## 8|^### 8' docs/recovery-experiments.md && sed -n \"$(grep -n '^## 8' docs/recovery-experiments.md | cut -d: -f1),$(grep -n '^### 8.3' docs/recovery-experiments.md | cut -d: -f1)p\" docs/recovery-experiments.md",
  "description": "Read the outline's Part A proposals and estimate"
}
```

## 102. User — 2026-10-24T07:30:13.012Z

### Tool result

```
378:## 8. Part A decisions: proposals
394:### 8.1 Repetitions and workload
421:### 8.2 Timing and deadlines
466:### 8.3 Memory
480:### 8.4 Injection method
497:### 8.5 Still open
## 8. Part A decisions: proposals

_Claude Code's proposals, with reasons. None is decided, and Part A is not approved._ They rest on
M2's final report (`6d8a232`):

| Input from M2 | Value |
|---|---|
| steps, calendar-year job | windows 2.5–3.0 s, spark_pipeline 22.1–22.6 s, verify 9.5 s; about 34–35 s in all |
| steps, stride-21 job | 1.5 s, 44.8–50.4 s, 11.0–11.5 s; about 57–63 s in all |
| step trees' peak RSS | spark_pipeline 0.66–0.79 GiB (calendar-year), 1.19–1.36 GiB (stride 21); verify 0.45–0.58 GiB; windows 0.12 GiB |
| job processes' RSS | worker 63.0 MiB, reconciler 51.6 MiB |
| container peaks | MySQL 345 MiB (67%) after the live job suites and 501 MiB (98%) after the live mutation session; Kafka 361–415 MiB (56–65%); informational, since another project's four containers shared Docker's VM and the host had about 1.3 GiB available |
| MySQL stalls, M2's clock | 0, 1 and 2 failed renewals for `LOCK TABLES`, `pause` and `restart`; each run kept its first attempt; no outage duration reported |
| acceptance runs | 10 of 10 passed on M2's clock in 11 min 20 s; the first run's failures were faults of the test harness |
| isolated memory-budget check | not done: pending |

### 8.1 Repetitions and workload

- **Proposal (P1).** Every case on the calendar-year job; per batch, 3 jobs of each of the 14 cases
  (C0 included), 42 in all, in one shuffled order drawn from a seed recorded before the batch; 2
  batches, each on fresh containers.
- **Reasons.** The calendar-year job is the shortest (steps about 35 s against 63 s for stride 21),
  and its 22 s `spark_pipeline` step is still long enough to aim the mid-step injections; the
  stride-21 job adds run time without a recovery path of its own. Two batches on fresh containers
  show whether results repeat across containers and keep each batch short of the ~50 runs after
  which M2 saw MySQL at 98% (another workload, so only a rough guide). A recorded shuffle spreads
  drift, such as memory growth, across cases instead of lining it up with one.
- **Duration of all 84 jobs** (an estimate, provisional). `python -m etf_risk.jobs.harness estimate`
  adds, per job, the design's upper bounds of 3.2 and these assumptions, none of them measured: T
  40 s (M2's slowest steps, 35.1 s, plus 5 s of the worker's own work), 12 s to restart a killed
  worker and rebalance, 20 s for a service from start to ready, 2 s for the peaks after every job,
  18 s for the group after a Kafka restart, and 3 minutes per batch for the containers, the
  reference run, the final snapshot and teardown. One job of each case takes 1,403 s (23.4
  minutes), from 42 s (C0) to 159 s (W4, W7); a batch of 42 jobs, 4,389 s (73 minutes); both
  batches, 8,778 s, about 2 hours 26 minutes. Each extra 5 s of T adds 8 minutes to the 84 jobs (T
  runs 16 times per 14 jobs). A longer restore lengthens K2 and can move D1 and D2 onto their fenced
  paths. The figures come from the estimator's formulas, worked out by hand; tests/test_jobs_harness.py
  pins them but has not run yet.
- **Counts, not rates.** The first review removed the pooled rule-of-three claim; reporting counts
  only is Claude Code's proposal. Results are given per case as k of n, with no rate, probability or
  confidence bound, pooled or per case: the injections are not shown to be independent, and cases are
  not alike.

### 8.2 Timing and deadlines

- **Proposal (P2), the clock and the limits.** The defaults of
  [timing.py](../src/etf_risk/jobs/timing.py) (lease 60 s, renewals every 10 s, fence margin 10 s,
  session timeout 15 s, heartbeats 3 s) and its step limits (windows 120 s, spark_pipeline 600 s,
  verify 300 s, attempt 900 s), with no `--timing` override.
- **Reasons.** E2 asks how long recovery takes, and the defaults are what the job processes run
  with; the token guards that decide E1 do not depend on the clock. The limits are about 40, 12 and
  26 times the measured step maxima (3.0, 50.4 and 11.5 s) and matter only to W7's lock wait and the
  classic-protocol bound; changing them would add a configuration M2 did not test. Cost: lease-based
  recoveries take 50–65 s instead of 20–29 s on M2's clock. Risk: the default clock has not run
  live, so the first batch is also its first live run.
- **Proposal (P3), the deadlines, reassessed on 2026-10-24.** Each case's D is the bound B from its
  reference to the start of its next run, plus twice the slowest step sum M2 measured for the
  parameter set (2S: 70.2 s calendar-year, 126.8 s stride 21), rounded up to 5 s; `max_lag_s` is 1 s,
  and the drain limit equals D. The reassessment changed three things:
  - W7's B is the later of the takeover (L + P, 65 s) and the end of the stopped tree (the stop plus
    two watchdog ticks and the kill grace: 98 s for a 90 s stop), no longer 65 s plus the stop;
  - K2, D1 and D2 count from their service's return (4.2), so B holds no outage of unknown length:
    for K2 the publication grace, a reconciler pass and the group's rejoin (30 + 5 + 19 = 54 s); for
    D1 and D2 a fenced attempt's lease and a pass (65 s);
  - the observation comes at completion when that is first (4.3), so meeting a deadline costs no
    waiting.

  | Cases | B | calendar-year D | stride-21 D |
  |---|---|---|---|
  | C0, W5a, W5b, K1, X1 | 0 | 75 s | 130 s |
  | W1 | 19 s | 90 s | 150 s |
  | W2, W3, W4, W6 | 65 s | 140 s | 195 s |
  | W7, with a 90 s stop | 98 s | 170 s | 225 s |
  | K2, from the broker's return | 54 s | 125 s | 185 s |
  | D1, D2, from MySQL's return | 65 s | 140 s | 195 s |

- **Reasons.** B is where the design puts the next run's start at the latest. S is the steps alone,
  not T: T adds the worker's own work (the claim, the input checksums, the manifest, renewals, three
  launcher starts), which nothing has measured, and 2S leaves about 35 s for it and for a slower run
  (M2's `spark_pipeline` varied by up to 5.6 s) while a stalled job still misses. The first batch's
  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next
  batch is an option for the author, recorded as a deviation. A local read of one row should take
  milliseconds, so a 1 s lag classifies nearly every success seen at the deadline and leaves the rest
  visible as `deadline not observed`. A drain limit of D gives a late job as long again to finish,
  enough to tell late from unfinished without one job holding the batch indefinitely. Whether D1 at
  this clock takes one claim or two stays open: M2 reported no outage duration, and failed-renewal
  counts do not establish one.

### 8.3 Memory
```

## 103. Assistant — 2026-10-24T07:30:18.742Z

Status: collector next. It moves to monotonic intervals and reports a missing injection time as unknown.

## 104. Assistant — 2026-10-24T07:30:33.622Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"analysis/collect_recovery_measurements.py\")\ns = p.read_text()\nold_doc = \"\"\"Durations are differences of mono values, from one host's monotonic clock (4.1). Step\nintervals come from the launcher records, which hold UTC times only at 6d8a232, so the overlap\nverdict holds only with a passed clock check (6.5).\n\"\"\"\nnew_doc = \"\"\"Durations are differences of mono values, from one host's monotonic clock (4.1), and so are\nthe step intervals: each launcher record's step_started_mono and tree_ended_mono. A record\nwithout them leaves its step's interval missing, which makes the overlap verdict unknown (6.5).\n\"\"\"\nassert old_doc in s\ns = s.replace(old_doc, new_doc)\n\nold = '''def step_intervals(b: BatchFolder) -> tuple[list[tuple], list[str]]:\n    \"\"\"Every started step's interval (UTC), and the steps that lack one (6.5).\"\"\"\n    intervals, missing = [], []\n    claims = {(e[\"job_id\"], e[\"attempt\"]): e[\"run_id\"] for e in named(b.worker_events(), \"claimed\")}\n    for e in named(b.worker_events(), \"step_started\"):\n        run_id = claims.get((e[\"job_id\"], e[\"attempt\"]))\n        record = launcher_record(b.attempt_dir(run_id), e[\"step\"]) if run_id else None\n        label = f\"{run_id or e['job_id']}:{e['step']}\"\n        if record and record.get(\"step_started_at_utc\") and record.get(\"tree_ended_at_utc\"):\n            intervals.append((record[\"step_started_at_utc\"], record[\"tree_ended_at_utc\"], label))\n        else:\n            missing.append(label)\n    for step in (\"windows\", \"spark_pipeline\"):\n        record = launcher_record(b.folder / \"reference\", step)\n        if record and record.get(\"step_started_at_utc\") and record.get(\"tree_ended_at_utc\"):\n            intervals.append((record[\"step_started_at_utc\"], record[\"tree_ended_at_utc\"], f\"reference:{step}\"))\n        else:\n            missing.append(f\"reference:{step}\")\n    return sorted(intervals), missing\n\n\ndef overlap_verdict(intervals: list[tuple], missing: list[str]) -> dict:\n    \"\"\"no overlap, overlap, or unknown: a missing interval never counts as no overlap (6.5).\"\"\"\n    overlaps = [(a[2], b_[2]) for a, b_ in zip(intervals, intervals[1:])\n                if datetime.fromisoformat(b_[0]) < datetime.fromisoformat(a[1])]\n    verdict = \"overlap\" if overlaps else \"unknown\" if missing else \"no overlap\"\n    return {\"verdict\": verdict, \"overlaps\": overlaps, \"steps_without_interval\": missing,\n            \"note\": \"UTC launcher times; valid only with a passed clock check\"}\n'''\nnew = '''def interval(record: dict | None) -> tuple[float, float] | None:\n    \"\"\"A launcher record's step interval on the host's monotonic clock; None without both ends.\"\"\"\n    if not record:\n        return None\n    start, end = record.get(\"step_started_mono\"), record.get(\"tree_ended_mono\")\n    if isinstance(start, (int, float)) and isinstance(end, (int, float)):\n        return float(start), float(end)\n    return None\n\n\ndef step_intervals(b: BatchFolder) -> tuple[list[tuple], list[str]]:\n    \"\"\"Every started step's interval (monotonic), and the steps that lack one (6.5).\"\"\"\n    intervals, missing = [], []\n    claims = {(e[\"job_id\"], e[\"attempt\"]): e[\"run_id\"] for e in named(b.worker_events(), \"claimed\")}\n    for e in named(b.worker_events(), \"step_started\"):\n        run_id = claims.get((e[\"job_id\"], e[\"attempt\"]))\n        span = interval(launcher_record(b.attempt_dir(run_id), e[\"step\"])) if run_id else None\n        label = f\"{run_id or e['job_id']}:{e['step']}\"\n        if span:\n            intervals.append((*span, label))\n        else:\n            missing.append(label)\n    for step in (\"windows\", \"spark_pipeline\"):\n        if span := interval(launcher_record(b.folder / \"reference\", step)):\n            intervals.append((*span, f\"reference:{step}\"))\n        else:\n            missing.append(f\"reference:{step}\")\n    return sorted(intervals), missing\n\n\ndef overlap_verdict(intervals: list[tuple], missing: list[str]) -> dict:\n    \"\"\"no overlap, overlap, or unknown: a missing interval never counts as no overlap (6.5).\n    Each interval that starts before an earlier tree ended is listed with the earlier one\n    whose tree ended last.\"\"\"\n    overlaps, latest = [], None\n    for start, end, label in intervals:\n        if latest is not None and start < latest[1]:\n            overlaps.append((latest[2], label))\n        if latest is None or end > latest[1]:\n            latest = (start, end, label)\n    verdict = \"overlap\" if overlaps else \"unknown\" if missing else \"no overlap\"\n    return {\"verdict\": verdict, \"overlaps\": overlaps, \"steps_without_interval\": missing,\n            \"note\": \"monotonic launcher times (4.1)\"}\n'''\nassert old in s\ns = s.replace(old, new)\n\nold = '''        record = launcher_record(b.attempt_dir(claims.get(e[\"attempt\"], \"\")), e[\"step\"])\n        if not record or not record.get(\"step_started_at_utc\") or not record.get(\"tree_ended_at_utc\"):\n            return f\"unknown: no complete record for attempt {e['attempt']} {e['step']}\"\n        total += utc_seconds(record[\"step_started_at_utc\"], record[\"tree_ended_at_utc\"])\n    return total'''\nnew = '''        span = interval(launcher_record(b.attempt_dir(claims.get(e[\"attempt\"], \"\")), e[\"step\"]))\n        if span is None:\n            return f\"unknown: no complete record for attempt {e['attempt']} {e['step']}\"\n        total += span[1] - span[0]\n    return total'''\nassert old in s\ns = s.replace(old, new)\np.write_text(s)\nEOF",
  "description": "Switch collector step intervals to monotonic times"
}
```

## 105. User — 2026-10-24T07:30:34.547Z

### Tool result

```
(Bash completed with no output)
```

## 106. Assistant — 2026-10-24T07:30:53.825Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"analysis/collect_recovery_measurements.py\")\ns = p.read_text()\nreps = [\n('''        row[\"rerun_s\"] = \"unknown: no new claim\"\n    accepted = min(named(events, \"accepted\"), key=lambda e: e[\"mono\"], default=None)\n    start = deadline.get(\"t_submit\") if case == \"C0\" or missed else t_inj\n    if case in NO_OVERHEAD and not missed:\n        row[\"finish_s\"] = row[\"overhead_s\"] = f\"n/a: {NO_OVERHEAD[case]}\"\n    elif accepted is None:\n        row[\"finish_s\"] = row[\"overhead_s\"] = \"unknown: no accepted event\"\n    else:\n        row[\"finish_s\"] = accepted[\"mono\"] - start if start is not None else \"unknown\"\n''',\n'''        row[\"rerun_s\"] = \"unknown: no new claim\"\n    else:                                                         # the record of the injection lacks its time\n        row.update(detection_s=\"unknown: no injection time\", rerun_s=\"unknown: no injection time\")\n    accepted = min(named(events, \"accepted\"), key=lambda e: e[\"mono\"], default=None)\n    from_submit = case == \"C0\" or missed\n    start = deadline.get(\"t_submit\") if from_submit else t_inj\n    if case in NO_OVERHEAD and not missed:\n        row[\"finish_s\"] = row[\"overhead_s\"] = f\"n/a: {NO_OVERHEAD[case]}\"\n    elif accepted is None:\n        row[\"finish_s\"] = row[\"overhead_s\"] = \"unknown: no accepted event\"\n    else:\n        row[\"finish_s\"] = (accepted[\"mono\"] - start if start is not None\n                           else f\"unknown: no {'submit' if from_submit else 'injection'} time\")\n'''),\n('''        d, inj = deadlines[position], injections.get(position, {})\n        job_id = d[\"job_id\"]\n        row.update(job_id=job_id, status=\"made\" if not inj.get(\"missed\") else \"missed\", missed=inj.get(\"missed\"),\n''',\n'''        d, inj = deadlines[position], injections.get(position)\n        status = \"no injection record\" if inj is None else \"missed\" if inj.get(\"missed\") else \"made\"\n        inj = inj or {}\n        job_id = d[\"job_id\"]\n        row.update(job_id=job_id, status=status, missed=inj.get(\"missed\"),\n'''),\n('''                       \"not_run\": [r[\"position\"] for r in rows if r.get(\"status\") in (\"not run\", \"not submitted\")]},\n''',\n'''                       \"not_run\": [r[\"position\"] for r in rows if r.get(\"status\") in NOT_RUN],\n                       \"unrecorded\": [r[\"position\"] for r in rows if r.get(\"status\") in UNRECORDED]},\n'''),\n('''                 \"not_run\": sum(r.get(\"status\") in (\"not run\", \"not submitted\", \"no record\") for r in mine),\n''',\n'''                 \"not_run\": sum(r.get(\"status\") in NOT_RUN for r in mine),\n                 \"unrecorded\": sum(r.get(\"status\") in UNRECORDED for r in mine),\n'''),\n('''LIVENESS = (\"serve_restarted\",''',\n'''NOT_RUN = (\"not run\", \"not submitted\")\nUNRECORDED = (\"no record\", \"no injection record\")     # the harness's records lack the job's deadline or injection\nLIVENESS = (\"serve_restarted\",'''),\n('''    \"\"\"Per case: planned, made, missed, not run, and every verdict value, with zeros.\"\"\"''',\n'''    \"\"\"Per case: planned, made, missed, not run, unrecorded, and every verdict value, with zeros.\"\"\"'''),\n('''- tally.csv: per case, the jobs planned, made, missed and not run, and every verdict value of''',\n'''- tally.csv: per case, the jobs planned, made, missed, not run and unrecorded, and every verdict value of'''),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\np.write_text(s)\nEOF\ngrep -n -E 'NOT_RUN|UNRECORDED|unrecorded|print\\(f\"\\{v' analysis/collect_recovery_measurements.py",
  "description": "Report missing injection times and records as unknown"
}
```

## 107. User — 2026-10-24T07:30:54.764Z

### Tool result

```
22:- tally.csv: per case, the jobs planned, made, missed, not run and unrecorded, and every verdict value of
63:NOT_RUN = ("not run", "not submitted")
64:UNRECORDED = ("no record", "no injection record")     # the harness's records lack the job's deadline or injection
393:                       "not_run": [r["position"] for r in rows if r.get("status") in NOT_RUN],
394:                       "unrecorded": [r["position"] for r in rows if r.get("status") in UNRECORDED]},
422:    """Per case: planned, made, missed, not run, unrecorded, and every verdict value, with zeros."""
433:                 "not_run": sum(r.get("status") in NOT_RUN for r in mine),
434:                 "unrecorded": sum(r.get("status") in UNRECORDED for r in mine),
470:    print(f"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run")
```

## 108. Assistant — 2026-10-24T07:31:00.529Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"analysis/collect_recovery_measurements.py\")\ns = p.read_text()\nold = '''    print(f\"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run\")'''\nnew = '''    print(f\"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run,\"\n          f\" {len(v['unrecorded'])} without a complete harness record\")'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\ngrep -n 'utc_seconds\\|from datetime' analysis/collect_recovery_measurements.py",
  "description": "Print the unrecorded count in the collector summary"
}
```

## 109. User — 2026-10-24T07:31:01.438Z

### Tool result

```
45:from datetime import datetime
122:def utc_seconds(start: str, end: str) -> float:
275:    difference = utc_seconds(a["ts"], z["ts"]) - (z["mono"] - a["mono"])
```

## 110. Assistant — 2026-10-24T07:31:06.222Z

Now the harness refactors that make it testable offline. Popen.kill() sends the same SIGKILL as before.

## 111. Assistant — 2026-10-24T07:31:27.811Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/etf_risk/jobs/harness.py\")\ns = p.read_text()\nreps = [\n# W3's kill: Popen.kill() is SIGKILL on POSIX, as before\n('''            if case == \"W3\":\n                os.kill(self.procs[worker].pid, signal.SIGKILL)\n''',\n'''            if case == \"W3\":\n                self.procs[worker].kill()                    # SIGKILL\n'''),\n# quiesce\n('''        for proc in self.procs.values():\n            if proc.poll() is None:\n                os.kill(proc.pid, signal.SIGKILL)\n        for proc in self.procs.values():\n            proc.wait(timeout=30)\n''',\n'''        for proc in self.procs.values():\n            if proc.poll() is None:\n                proc.kill()                                  # SIGKILL\n        for proc in self.procs.values():\n            proc.wait(timeout=30)\n'''),\n('''        from etf_risk.jobs import mysql\n        conn = mysql.connect_mysql(self.db)\n        try:\n            with conn.cursor() as cursor:\n                cursor.execute(\"SELECT CONNECTION_ID()\")\n                me = cursor.fetchone()[0]\n                cursor.execute(\"SHOW FULL PROCESSLIST\")\n                others = [row for row in cursor.fetchall()\n                          if row[0] != me and row[4] != \"Daemon\" and row[1] not in (\"event_scheduler\", \"system user\")]\n        finally:\n            conn.close()\n        record = {\"processes_left\": processes_left, \"other_connections\": len(others)}\n''',\n'''        record = {\"processes_left\": processes_left, \"other_connections\": self.other_connections()}\n'''),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:80]\n    s = s.replace(old, new)\n\n# DB hooks after wait_for... insert before \"# The job table, read by the harness\"\nold = '''    # The job table, read by the harness\n\n    def store(self):'''\nnew = '''    # The job table, read by the harness\n\n    SNAPSHOT = \"START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY\"     # 4.3 and 4.5\n    PARAM = \"%s\"                                                            # the driver's placeholder\n\n    def connect(self, **timeouts):\n        \"\"\"A DB-API connection of the harness's own to the batch's database.\"\"\"\n        from etf_risk.jobs import mysql\n        return mysql.connect_mysql(self.db, **timeouts)\n\n    def statement(self, sql: str) -> str:\n        \"\"\"A statement of crosscheck.sql as this database runs it: MySQL runs it as written.\"\"\"\n        return sql\n\n    def other_connections(self) -> int:\n        \"\"\"4.4: client connections to the database other than this one.\"\"\"\n        conn = self.connect()\n        try:\n            with closing(conn.cursor()) as cursor:\n                cursor.execute(\"SELECT CONNECTION_ID()\")\n                me = cursor.fetchone()[0]\n                cursor.execute(\"SHOW FULL PROCESSLIST\")\n                return len([row for row in cursor.fetchall()\n                            if row[0] != me and row[4] != \"Daemon\" and row[1] not in (\"event_scheduler\", \"system user\")])\n        finally:\n            conn.close()\n\n    def store(self):'''\nassert s.count(old) == 1\ns = s.replace(old, new)\n\n# observe\nold = '''        from etf_risk.jobs import mysql\n        record = {\"job_id\": job_id, \"status\": None, \"attempt_number\": None, \"accepted_attempt\": None}\n        observed_from = observed_to = time.monotonic()\n        try:\n            conn = mysql.connect_mysql(self.db, connect_timeout=3, read_timeout=5, write_timeout=5)\n            try:\n                with conn.cursor() as cursor:\n                    observed_from = time.monotonic()\n                    cursor.execute(\"START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY\")\n                    observed_to = time.monotonic()\n                    cursor.execute(\"SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = %s\",\n                                   (job_id,))\n                    row = cursor.fetchone()\n                    cursor.execute(\"COMMIT\")\n            finally:\n                conn.close()'''\nnew = '''        record = {\"job_id\": job_id, \"status\": None, \"attempt_number\": None, \"accepted_attempt\": None}\n        observed_from = observed_to = time.monotonic()\n        try:\n            conn = self.connect(connect_timeout=3, read_timeout=5, write_timeout=5)\n            try:\n                with closing(conn.cursor()) as cursor:\n                    observed_from = time.monotonic()\n                    cursor.execute(self.SNAPSHOT)\n                    observed_to = time.monotonic()\n                    cursor.execute(\"SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = \"\n                                   + self.PARAM, (job_id,))\n                    row = cursor.fetchone()\n                    cursor.execute(\"COMMIT\")\n            finally:\n                conn.close()'''\nassert s.count(old) == 1\ns = s.replace(old, new)\n\n# crosscheck\nold = '''        from etf_risk.jobs import mysql\n        folder = self.out / \"crosscheck\"\n        folder.mkdir(exist_ok=True)\n        statements = crosscheck_statements()\n        conn = mysql.connect_mysql(self.db)\n        fingerprint = {}\n        try:\n            with conn.cursor() as cursor:\n                for name, sql in statements:\n                    if name == \"DDL\":\n                        cursor.execute(sql)\n                cursor.executemany(\"INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono,\"\n                                   \" max_lag_s) VALUES (%s, %s, %s, %s, %s, %s)\", self.batch_jobs)\n                cursor.executemany(\"INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono,\"\n                                   \" status, attempt_number, accepted_attempt) VALUES (%s, %s, %s, %s, %s, %s)\",\n                                   self.observations)\n                cursor.executemany(\"INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number,\"\n                                   \" result_digest) VALUES (%s, %s, %s, %s, %s, %s)\", worker_accepts(self.worker_logs()))\n                cursor.execute(\"START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY\")\n                for name, sql in statements:\n                    if name == \"DDL\":\n                        continue\n                    cursor.execute(sql)'''\nnew = '''        folder = self.out / \"crosscheck\"\n        folder.mkdir(exist_ok=True)\n        statements = crosscheck_statements()\n        values = \", \".join([self.PARAM] * 6)\n        conn = self.connect()\n        fingerprint = {}\n        try:\n            with closing(conn.cursor()) as cursor:\n                for name, sql in statements:\n                    if name == \"DDL\":\n                        cursor.execute(self.statement(sql))\n                cursor.executemany(\"INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono,\"\n                                   f\" max_lag_s) VALUES ({values})\", self.batch_jobs)\n                cursor.executemany(\"INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono,\"\n                                   f\" status, attempt_number, accepted_attempt) VALUES ({values})\", self.observations)\n                cursor.executemany(\"INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number,\"\n                                   f\" result_digest) VALUES ({values})\", worker_accepts(self.worker_logs()))\n                cursor.execute(self.SNAPSHOT)\n                for name, sql in statements:\n                    if name == \"DDL\":\n                        continue\n                    cursor.execute(self.statement(sql))'''\nassert s.count(old) == 1\ns = s.replace(old, new)\n\n# q0\nold = '''        from etf_risk.jobs import mysql\n        sql = dict(crosscheck_statements())[\"Q0\"]\n        conn = mysql.connect_mysql(self.db)\n        try:\n            with conn.cursor() as cursor:\n                cursor.execute(sql)'''\nnew = '''        sql = dict(crosscheck_statements())[\"Q0\"]\n        conn = self.connect()\n        try:\n            with closing(conn.cursor()) as cursor:\n                cursor.execute(self.statement(sql))'''\nassert s.count(old) == 1\ns = s.replace(old, new)\n\nold = '''import time\nfrom dataclasses import asdict, dataclass, fields'''\nnew = '''import time\nfrom contextlib import closing\nfrom dataclasses import asdict, dataclass, fields'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\ngrep -n -E 'os\\.kill|signal\\.' src/etf_risk/jobs/harness.py",
  "description": "Route harness database access through overridable hooks"
}
```

## 112. User — 2026-10-24T07:31:32.384Z

### Tool result

```
722:        self.procs[worker].send_signal(signal.SIGTERM)
```

## 113. Assistant — 2026-10-24T07:31:47.543Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/etf_risk/jobs/harness.py\")\ns = p.read_text()\nold = '''        armed, release, injection = None, None, None\n        if case in HOOKS:\n            point, action = HOOKS[case]\n            armed = record[\"owner_before\"]\n            release = self.faults_dir / f\"release-{position}\" if action == \"hold\" else None\n            faults.arm(self.fault_file(armed), point, action, release=release,\n                       timeout_s=s.outage_s + 600 if release else None)\n            self.log.log(\"armed\", position=position, worker=armed, point=point, action=action)\n'''\nnew = '''        armed, release, injection = None, None, None\n        if case in HOOKS:\n            armed, release = self.arm_fault(position, case, record[\"owner_before\"])\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\nold = '''    # Injections (3.1)\n\n'''\nnew = '''    # Injections (3.1)\n\n    def arm_fault(self, position: int, case: str, owner: str) -> tuple[str, Path | None]:\n        \"\"\"Arm the case's hook (8.4) in the owner's fault file, which that worker reads at each\n        fault point. Arming writes a file and starts or stops nothing, so the partition keeps its\n        owner (logged again as owner_after) and the other worker's file stays empty. Returns the\n        armed worker and, for a hold, the release path.\"\"\"\n        point, action = HOOKS[case]\n        release = self.faults_dir / f\"release-{position}\" if action == \"hold\" else None\n        faults.arm(self.fault_file(owner), point, action, release=release,\n                   timeout_s=self.settings.outage_s + 600 if release else None)\n        self.log.log(\"armed\", position=position, worker=owner, point=point, action=action,\n                     owner_after=self.current_owner())\n        return owner, release\n\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\n.venv/bin/python -c \"import ast,sys; ast.parse(open('src/etf_risk/jobs/harness.py').read()); ast.parse(open('analysis/collect_recovery_measurements.py').read()); print('ok')\"",
  "description": "Move fault arming into a harness method"
}
```

## 114. User — 2026-10-24T07:31:48.578Z

### Tool result

```
ok
```

## 115. Assistant — 2026-10-24T07:32:10.591Z

### Tool call: Bash

```
{
  "command": "grep -n -A6 '^class Outcome' src/etf_risk/jobs/store.py",
  "description": "Check the attempt outcome enum names"
}
```

## 116. User — 2026-10-24T07:32:11.373Z

### Tool result

```
112:class Outcome(StrEnum):
113-    """How an attempt ended (job_attempts.outcome); running until then."""
114-    RUNNING = "running"
115-    ACCEPTED = "accepted"
116-    FAILED = "failed"
117-    EXPIRED = "expired"          # its lease expired, and a claim took the job over or failed it
118-
```

## 117. Assistant — 2026-10-24T07:32:14.816Z

Writing the worker tests for the deadline at acceptance and for arming a running worker:

## 118. Assistant — 2026-10-24T07:32:29.374Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/test_jobs_worker.py\")\ns = p.read_text()\nold = '''import json\nfrom pathlib import Path\n\nimport pytest\n\nfrom etf_risk.jobs.events import EventLog, read_events\n'''\nnew = '''import json\nimport time\nfrom pathlib import Path\n\nimport pytest\n\nfrom etf_risk.jobs import faults\nfrom etf_risk.jobs.events import EventLog, read_events\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\n\nold = '''# Failures and retries\n'''\nnew = '''# The deadline F at acceptance\n\nclass DeadlinePipeline(SimulatedPipeline):\n    \"\"\"A simulated pipeline that keeps a deadline as SubprocessPipeline does: fence_at, on\n    time.monotonic(), set `left` seconds ahead when its run returns (negative: already passed).\"\"\"\n\n    def __init__(self, left: float, **kwargs):\n        super().__init__(**kwargs)\n        self.left, self.fence_at = left, None\n\n    def run(self, claim, run_dir, heartbeat):\n        digest = super().run(claim, run_dir, heartbeat)\n        self.fence_at = time.monotonic() + self.left\n        return digest\n\n\ndef test_no_acceptance_call_once_the_deadline_has_passed(env, tmp_path):\n    \"\"\"docs/worker-pipeline.md: the worker never accepts after F, even while its token still holds\n    the job. The job runs again once its lease has expired.\"\"\"\n    job = submit(env)\n    worker = env.worker(\"A\", DeadlinePipeline(left=-1.0))\n    worker.events = EventLog(tmp_path / \"A.jsonl\", \"worker\", worker_id=\"worker-A\")\n    calls = []\n    accept = worker.store.accept_result\n    worker.store.accept_result = lambda *args: calls.append(args) or accept(*args)\n    assert env.deliver(worker, job).result is Result.FENCED and calls == []          # not even one call\n    j = env.admin.job(job)\n    assert (j[\"status\"], j[\"attempt_number\"]) == (Status.RUNNING, 1)              # the token still holds it\n    fenced = read_events(tmp_path / \"A.jsonl\")[-1]\n    assert (fenced[\"event\"], fenced[\"during\"]) == (\"fenced\", \"acceptance\")\n    assert (env.runs / f\"job-{job}-attempt-1\" / \"result.json\").exists()           # complete, never accepted\n    env.clock.advance(LEASE.total_seconds())\n    again = env.deliver(env.worker(\"B\"), job)\n    assert again.result is Result.ACCEPTED and again.claim.attempt_number == 2\n    assert [a[\"outcome\"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]\n    env.check(job)\n\n\ndef test_acceptance_before_the_deadline_goes_ahead(env):\n    job = submit(env)\n    assert env.deliver(env.worker(\"A\", DeadlinePipeline(left=60.0)), job).result is Result.ACCEPTED\n    env.check(job)\n\n\ndef test_a_hold_released_after_the_deadline_ends_without_acceptance(env, tmp_path):\n    \"\"\"Case D2's hook (etf_risk.jobs.faults) holds at after_pipeline until its release file\n    appears, here only once F has passed: the worker then fences itself.\"\"\"\n    job = submit(env)\n    pipeline = DeadlinePipeline(left=0.05)\n    log = tmp_path / \"A.jsonl\"\n    events = EventLog(log, \"worker\", worker_id=\"worker-A\")\n    release = tmp_path / \"release\"\n\n    def sleep(seconds):                                             # the harness releases only after F\n        time.sleep(0.01)\n        if time.monotonic() >= pipeline.fence_at:\n            release.touch()\n\n    hook = faults.FaultFile(tmp_path / \"A.fault\", events, sleep=sleep)\n    faults.arm(hook.path, \"after_pipeline\", \"hold\", release=release, timeout_s=60)\n    worker = env.worker(\"A\", pipeline, fault=hook)\n    worker.events = events\n    assert env.deliver(worker, job).result is Result.FENCED\n    assert [e[\"event\"] for e in read_events(log)] == [\"claimed\", \"fault_injected\", \"fault_released\", \"fenced\"]\n    assert env.admin.attempts(job)[0][\"outcome\"] is Outcome.RUNNING\n    env.check(job)\n\n\ndef test_a_fault_armed_while_the_worker_runs_fires_without_a_restart(env, tmp_path):\n    \"\"\"The harness arms a running worker (outline 8.4): the same Worker and hook handle one job\n    untouched, are armed, and die at the armed point of the next job.\"\"\"\n    first, second = submit(env), submit(env)\n    log = tmp_path / \"A.jsonl\"\n    events = EventLog(log, \"worker\", worker_id=\"worker-A\")\n\n    def kill():\n        raise SimulatedCrash(\"SIGKILL\")\n\n    hook = faults.FaultFile(tmp_path / \"A.fault\", events, kill=kill)\n    worker = env.worker(\"A\", fault=hook)\n    worker.events = events\n    assert env.deliver(worker, first).result is Result.ACCEPTED\n    faults.arm(hook.path, \"after_claim\")\n    with pytest.raises(SimulatedCrash):\n        env.deliver(worker, second)\n    assert [e[\"event\"] for e in read_events(log)] == [\"claimed\", \"accepted\", \"claimed\", \"fault_injected\"]\n    assert env.acks == [first] and not hook.path.exists()          # never acknowledged; the fault fired once\n    env.check(first)\n    env.check(second)\n\n\n# Failures and retries\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q tests/test_jobs_worker.py tests/test_jobs_faults.py 2>&1 | tail -5",
  "description": "Add deadline-at-acceptance worker tests and run them"
}
```

## 119. User — 2026-10-24T07:32:32.758Z

### Tool result

```
  ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/.venv/lib/python3.12/site-packages/exchange_calendars/exchange_calendar.py:65: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
    ONE_HOUR = pd.Timedelta("1h")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 1 warning in 0.50s
```

## 120. Assistant — 2026-10-24T07:32:40.402Z

34 passed. Checking that the new test fails when the check is removed:

## 121. Assistant — 2026-10-24T07:32:43.819Z

### Tool call: Bash

```
{
  "command": "S=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad && cp src/etf_risk/jobs/worker.py $S/worker.py.bak && python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/etf_risk/jobs/worker.py\")\ns = p.read_text()\nold = \"        if deadline is not None and time.monotonic() >= deadline:\\n\"\nassert s.count(old) == 1\np.write_text(s.replace(old, \"        if False:\\n\"))\nEOF\n.venv/bin/python -m pytest -q tests/test_jobs_worker.py -k \"deadline\" 2>&1 | grep -E 'passed|failed'; cp $S/worker.py.bak src/etf_risk/jobs/worker.py && grep -c 'time.monotonic() >= deadline:' src/etf_risk/jobs/worker.py",
  "description": "Mutate the deadline check to confirm the tests catch it"
}
```

## 122. User — 2026-10-24T07:32:46.053Z

### Tool result

```
_________ test_no_acceptance_call_once_the_deadline_has_passed[sqlite] _________
    def test_no_acceptance_call_once_the_deadline_has_passed(env, tmp_path):
        appears, here only once F has passed: the worker then fences itself."""
FAILED tests/test_jobs_worker.py::test_no_acceptance_call_once_the_deadline_has_passed[sqlite]
2 failed, 1 passed, 22 deselected, 1 warning in 0.25s
1
```

## 123. Assistant — 2026-10-24T07:33:02.768Z

### Tool call: Bash

```
{
  "command": "cat >> tests/test_jobs_launcher.py <<'EOF'\n\n\ndef test_a_steps_interval_is_on_the_monotonic_clock_that_the_handshake_checked(tmp_path):\n    \"\"\"step_started_mono and tree_ended_mono read the host's monotonic clock, as this process\n    does, so intervals of different launchers compare directly: the host lock puts the later\n    step after the earlier tree has ended. A launcher that starts no step records neither.\"\"\"\n    before = time.monotonic()\n    sleeper = Run(tmp_path, \"sleeper\", [sys.executable, \"-c\", \"import time; time.sleep(0.3)\"])\n    quick = Run(tmp_path, \"quick\", [sys.executable, \"-c\", \"pass\"])\n    one, two = sleeper.wait()[1], quick.wait()[1]\n    after = time.monotonic()\n    for result in (one, two):\n        assert before < result[\"step_started_mono\"] < result[\"tree_ended_mono\"] < after\n    assert one[\"tree_ended_mono\"] - one[\"step_started_mono\"] >= 0.3\n    earlier, later = sorted((one, two), key=lambda r: r[\"step_started_mono\"])\n    assert later[\"step_started_mono\"] > earlier[\"tree_ended_mono\"]\n    code, result = Run(tmp_path, \"late\", [sys.executable, \"-c\", \"pass\"], deadline_in=-1.0).wait()\n    assert (code, result[\"outcome\"]) == (EXIT_CODES[\"deadline_passed\"], \"deadline_passed\")\n    assert \"step_started_mono\" not in result and \"tree_ended_mono\" not in result\nEOF\n.venv/bin/python -m pytest -q tests/test_jobs_launcher.py 2>&1 | tail -2",
  "description": "Add and run the launcher monotonic-interval test"
}
```

## 124. User — 2026-10-24T07:33:33.120Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
13 passed, 1 warning in 27.63s
```

## 125. Assistant — 2026-10-24T07:33:52.291Z

Launcher: 13 passed. Now the collector tests for missing monotonic times, a missing injection time and a missing injection record:

## 126. Assistant — 2026-10-24T07:34:05.306Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/test_recovery_collector.py\")\ns = p.read_text()\nold = '''def launcher(folder, step, start, end):\n    (folder / \"logs\").mkdir(parents=True, exist_ok=True)\n    (folder / \"logs\" / f\"{step}.launcher.json\").write_text(json.dumps(\n        {\"outcome\": \"exited\", \"step_started_at_utc\": utc(start), \"tree_ended_at_utc\": utc(end)}))\n'''\nnew = '''def launcher(folder, step, start, end, *, mono=True):\n    \"\"\"A launcher record; mono=False writes UTC times only, as the launcher did at 6d8a232.\"\"\"\n    record = {\"outcome\": \"exited\", \"step_started_at_utc\": utc(start), \"tree_ended_at_utc\": utc(end)}\n    if mono:\n        record.update(step_started_mono=float(start), tree_ended_mono=float(end))\n    (folder / \"logs\").mkdir(parents=True, exist_ok=True)\n    (folder / \"logs\" / f\"{step}.launcher.json\").write_text(json.dumps(record))\n\n\ndef edit_harness(batch, change):\n    \"\"\"Rewrite harness.jsonl through change(event), which returns the event, a new one, or None.\"\"\"\n    events = [json.loads(line) for line in (batch / \"harness.jsonl\").read_text().splitlines()]\n    write_jsonl(batch / \"harness.jsonl\", [e for e in map(change, events) if e is not None])\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\ns += '''\n\ndef test_a_launcher_record_without_monotonic_times_counts_as_missing(batch, tmp_path):\n    \"\"\"A record with UTC times only gives no interval: the overlap check never falls back to UTC.\"\"\"\n    launcher(batch / \"jobs\" / STORE / \"job-2-attempt-1\", \"windows\", 1102, 1105, mono=False)\n    result = crm.collect(batch, processed_root=tmp_path / \"processed\")\n    overlap = result[\"outcomes\"][\"overlap\"]\n    assert overlap[\"verdict\"] == \"unknown\" and overlap[\"steps_without_interval\"] == [\"job-2-attempt-1:windows\"]\n    assert str({r[\"position\"]: r for r in result[\"rows\"]}[2][\"wasted_step_s\"]).startswith(\"unknown\")\n\n\ndef test_every_interval_that_overlaps_an_earlier_one_is_listed(batch, tmp_path):\n    launcher(batch / \"jobs\" / STORE / \"job-2-attempt-2\", \"windows\", 1103, 1184)      # inside attempt 1's steps\n    launcher(batch / \"jobs\" / STORE / \"job-2-attempt-2\", \"spark_pipeline\", 1110, 1210)\n    overlap = crm.collect(batch, processed_root=tmp_path / \"processed\")[\"outcomes\"][\"overlap\"]\n    assert overlap[\"verdict\"] == \"overlap\" and [later for _, later in overlap[\"overlaps\"]] == [\n        \"job-2-attempt-2:windows\", \"job-2-attempt-1:spark_pipeline\", \"job-2-attempt-2:spark_pipeline\",\n        \"job-2-attempt-2:verify\"]\n\n\ndef test_an_injection_record_without_its_time_leaves_its_latencies_unknown(batch, tmp_path):\n    def drop_w3_time(e):\n        if e[\"event\"] == \"injection\" and e.get(\"case\") == \"W3\":\n            return {k: v for k, v in e.items() if k != \"t_inj\"}\n        return e\n\n    edit_harness(batch, drop_w3_time)\n    w3 = {r[\"position\"]: r for r in crm.collect(batch, processed_root=tmp_path / \"processed\")[\"rows\"]}[2]\n    assert w3[\"status\"] == \"made\"\n    assert (w3[\"detection_s\"], w3[\"rerun_s\"], w3[\"finish_s\"]) == (\"unknown: no injection time\",) * 3\n    assert w3[\"overhead_s\"] == 85.0                                 # from the submit, which the deadline keeps\n\n\ndef test_a_job_without_its_injection_record_is_counted_apart_never_as_made(batch, tmp_path):\n    edit_harness(batch, lambda e: None if e[\"event\"] == \"injection\" and e.get(\"case\") == \"W3\" else e)\n    result = crm.collect(batch, processed_root=tmp_path / \"processed\")\n    w3 = {r[\"position\"]: r for r in result[\"rows\"]}[2]\n    assert w3[\"status\"] == \"no injection record\" and w3[\"detection_s\"] == \"unknown: no injection time\"\n    injections = result[\"validity\"][\"injections\"]\n    assert (injections[\"made\"], injections[\"unrecorded\"], injections[\"not_run\"]) == (2, [2], [4])\n    tally = {t[\"case\"]: t for t in result[\"tally\"]}\n    assert (tally[\"W3\"][\"made\"], tally[\"W3\"][\"unrecorded\"]) == (0, 1)\n    assert all(t[\"planned\"] == t[\"made\"] + t[\"missed\"] + t[\"not_run\"] + t[\"unrecorded\"] for t in tally.values())\n'''\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q tests/test_recovery_collector.py 2>&1 | grep -E 'passed|failed|Error|assert' | head -20",
  "description": "Add collector tests for missing records and run them"
}
```

## 127. User — 2026-10-24T07:34:09.358Z

### Tool result

```
>       assert overlap["verdict"] == "overlap" and [later for _, later in overlap["overlaps"]] == [
E       AssertionError: assert ('overlap' == 'overlap'
tests/test_recovery_collector.py:238: AssertionError
1 failed, 9 passed, 81 warnings in 1.57s
```

## 128. Assistant — 2026-10-24T07:34:13.975Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -m pytest -q tests/test_recovery_collector.py -k every_interval 2>&1 | grep -E \"^E \" | head -12",
  "description": "Show the overlap listing assertion details"
}
```

## 129. User — 2026-10-24T07:34:17.855Z

### Tool result

```
E       AssertionError: assert ('overlap' == 'overlap'
E         
E           overlap and ['job-2-attem...ark_pipeline'] == ['job-2-attem...mpt-2:verify']
E         
E         Right contains one more item: 'job-2-attempt-2:verify'
E         Use -v to get more diff)
```

## 130. Assistant — 2026-10-24T07:34:25.385Z

The code is right; my expected list was wrong. verify starts at 1210, exactly when the spark step's tree ended, and touching ends do not overlap. Fixing the expectation:

## 131. Assistant — 2026-10-24T07:34:28.921Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/test_recovery_collector.py\")\ns = p.read_text()\nold = '''    assert overlap[\"verdict\"] == \"overlap\" and [later for _, later in overlap[\"overlaps\"]] == [\n        \"job-2-attempt-2:windows\", \"job-2-attempt-1:spark_pipeline\", \"job-2-attempt-2:spark_pipeline\",\n        \"job-2-attempt-2:verify\"]\n'''\nnew = '''    assert overlap[\"verdict\"] == \"overlap\" and overlap[\"overlaps\"] == [               # verify starts as spark ends\n        (\"job-2-attempt-1:windows\", \"job-2-attempt-2:windows\"),\n        (\"job-2-attempt-2:windows\", \"job-2-attempt-1:spark_pipeline\"),\n        (\"job-2-attempt-2:windows\", \"job-2-attempt-2:spark_pipeline\")]\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q tests/test_recovery_collector.py 2>&1 | grep -E 'passed|failed'",
  "description": "Correct the overlap listing expectation and rerun"
}
```

## 132. User — 2026-10-24T07:34:32.369Z

### Tool result

```
10 passed, 81 warnings in 1.29s
```

## 133. Assistant — 2026-10-24T07:34:37.040Z

Collector: 10 passed. Next, harness tests for arming, the early miss and the Tracker's observations. Checking that Batch can be built offline:

## 134. Assistant — 2026-10-24T07:34:38.939Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python - <<'EOF'\nimport tempfile, json\nfrom pathlib import Path\nfrom etf_risk.jobs import harness\nwith tempfile.TemporaryDirectory() as d:\n    plan = harness.make_plan(harness.Settings(), seed=1)\n    b = harness.Batch(plan, Path(d) / \"batch\")\n    print(type(b).__name__, b.db, sorted(p.name for p in (Path(d) / \"batch\").iterdir()))\nEOF",
  "description": "Construct a harness Batch without services"
}
```

## 135. User — 2026-10-24T07:34:40.834Z

### Tool result

```
Batch mysql://root:jobs-test@127.0.0.1:3307/etf_recovery ['events', 'faults', 'harness.jsonl', 'jobs', 'logs']
```

## 136. Assistant — 2026-10-24T07:35:46.718Z

### Tool call: Bash

```
{
  "command": "sed -n '/\\[tool.pytest/,/^\\[/p' pyproject.toml; ls tests/ | head -50; sed -n 1,40p tests/conftest.py",
  "description": "Read the pytest configuration and test helpers"
}
```

## 137. User — 2026-10-24T07:35:47.531Z

### Tool result

```
[REDACTED:private-file docs/implementation-plan.md]
```

## 138. Assistant — 2026-10-24T07:36:11.825Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/test_jobs_harness.py\")\ns = p.read_text()\nold = '''import json\nimport re\nfrom collections import Counter\nfrom pathlib import Path\n\nimport pytest\n\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.timing import DEFAULT_TIMING\n'''\nnew = '''import json\nimport re\nimport time\nfrom collections import Counter\nfrom pathlib import Path\n\nimport pytest\n\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.events import read_events\nfrom etf_risk.jobs.timing import DEFAULT_TIMING\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\ns += '''\n\n# Arming, phases and the deadline observation, on a batch with no services\n\nclass FakeProc:\n    \"\"\"A worker's Popen as the harness reads it: alive until killed.\"\"\"\n\n    def __init__(self, pid):\n        self.pid, self.code = pid, None\n\n    def poll(self):\n        return self.code\n\n    def kill(self):\n        self.code = -9\n\n\ndef offline_batch(tmp_path, **settings) -> harness.Batch:\n    batch = harness.Batch(harness.make_plan(harness.Settings(**settings), seed=1), tmp_path / \"batch\")\n    batch.procs = {\"A\": FakeProc(11), \"B\": FakeProc(22)}\n    return batch\n\n\ndef log(batch, worker, *events):\n    with open(batch.events_dir / f\"{worker}.jsonl\", \"a\") as f:\n        f.writelines(json.dumps(e) + \"\\\\n\" for e in events)\n\n\ndef test_arming_writes_only_the_owners_fault_file_and_leaves_the_partition_where_it_was(tmp_path):\n    batch = offline_batch(tmp_path)\n    log(batch, \"A\", {\"event\": \"started\", \"pid\": 11, \"mono\": 1}, assigned(2, 0, pid=11))\n    log(batch, \"B\", {\"event\": \"started\", \"pid\": 22, \"mono\": 3}, assigned(4, pid=22))\n    procs = dict(batch.procs)\n    assert batch.wait_owner(timeout=1) == \"A\"\n    assert batch.arm_fault(5, \"W2\", \"A\") == (\"A\", None)\n    assert json.loads(batch.fault_file(\"A\").read_text()) == {\"point\": \"after_claim\", \"action\": \"kill\"}\n    assert not batch.fault_file(\"B\").exists()\n    assert batch.procs == procs and all(p.poll() is None for p in procs.values())    # nothing started or stopped\n    assert batch.current_owner() == \"A\" and len(harness.events_named(batch.worker_logs()[\"A\"], \"assigned\")) == 1\n    armed = harness.events_named(read_events(batch.out / \"harness.jsonl\"), \"armed\")[-1]\n    assert (armed[\"worker\"], armed[\"point\"], armed[\"action\"], armed[\"owner_after\"]) == (\"A\", \"after_claim\", \"kill\", \"A\")\n    batch.fault_file(\"A\").unlink()                                   # the W2 fault fired\n    _, release = batch.arm_fault(6, \"D2\", \"A\")\n    assert json.loads(batch.fault_file(\"A\").read_text()) == {\n        \"point\": \"after_pipeline\", \"action\": \"hold\", \"release\": str(release), \"timeout_s\": 630.0}\n\n\ndef test_a_fault_counts_only_after_this_jobs_delivery_and_is_missed_once_the_other_worker_claims(tmp_path):\n    batch = offline_batch(tmp_path, phase_timeout_s=1.0, poll_s=0.05)\n    log(batch, \"A\", {\"event\": \"delivered\", \"job_id\": 6, \"mono\": 1},\n        {\"event\": \"fault_injected\", \"point\": \"after_claim\", \"mono\": 2})          # an earlier job's\n    with pytest.raises(harness.PhaseMissed, match=\"timed out\"):\n        batch.wait_fault(\"A\", 7, \"after_claim\")\n    log(batch, \"A\", {\"event\": \"delivered\", \"job_id\": 7, \"mono\": 3},\n        {\"event\": \"claimed\", \"job_id\": 7, \"attempt\": 1, \"run_id\": \"job-7-attempt-1\", \"mono\": 4},\n        {\"event\": \"fault_injected\", \"point\": \"after_claim\", \"mono\": 5})\n    assert batch.wait_fault(\"A\", 7, \"after_claim\")[\"mono\"] == 5\n    slow = offline_batch(tmp_path / \"slow\", phase_timeout_s=60.0, poll_s=0.05)\n    log(slow, \"B\", {\"event\": \"delivered\", \"job_id\": 8, \"mono\": 1},\n        {\"event\": \"claimed\", \"job_id\": 8, \"attempt\": 1, \"run_id\": \"job-8-attempt-1\", \"mono\": 2})\n    start = time.monotonic()\n    with pytest.raises(harness.PhaseMissed, match=\"claimed by worker B, not the armed A\"):\n        slow.wait_fault(\"A\", 8, \"after_claim\")\n    assert time.monotonic() - start < 5                                          # not the 60 s phase timeout\n\n\nclass Statuses:\n    \"\"\"What a Tracker reads: job_status() returns the status the clock has reached in `timeline`\n    ([(seconds from start, status)]); observe() returns that status, or fails (status None).\"\"\"\n\n    def __init__(self, timeline, *, failing=False):\n        self.start, self.timeline, self.failing = time.monotonic(), timeline, failing\n        self.settings = harness.Settings(poll_s=0.01)\n        self.observed = []\n\n    def job_status(self, job_id):\n        elapsed = time.monotonic() - self.start\n        return [status for at, status in self.timeline if at <= elapsed][-1]\n\n    def observe(self, job_id):\n        t = time.monotonic()\n        record = {\"job_id\": job_id, \"observed_from_mono\": t, \"observed_to_mono\": t,\n                  \"status\": None if self.failing else self.job_status(job_id)}\n        self.observed.append(record)\n        return record\n\n\ndef track(fake, deadline_s, drain_s):\n    tracker = harness.Tracker(fake, 1, fake.start + deadline_s, fake.start + deadline_s + drain_s)\n    tracker.start()\n    tracker.join(10)\n    return tracker\n\n\ndef test_a_job_that_finishes_first_is_observed_at_completion_and_never_waits_out_its_deadline():\n    fake = Statuses([(0, \"running\"), (0.1, \"succeeded\")])\n    tracker = track(fake, deadline_s=30, drain_s=30)\n    assert [o[\"status\"] for o in fake.observed] == [\"succeeded\"] and tracker.final == \"succeeded\"\n    assert tracker.finished_mono - fake.start < 5\n\n\ndef test_a_late_job_is_observed_once_at_its_deadline_and_followed_to_its_end():\n    fake = Statuses([(0, \"running\"), (0.6, \"succeeded\")])\n    tracker = track(fake, deadline_s=0.2, drain_s=5)\n    assert [o[\"status\"] for o in fake.observed] == [\"running\"] and tracker.final == \"succeeded\"\n    assert fake.observed[0][\"observed_from_mono\"] >= tracker.deadline_mono          # Q2: late\n    assert tracker.finished_mono >= fake.start + 0.6\n\n\ndef test_a_failed_observation_is_kept_and_never_repeated():\n    fake = Statuses([(0, \"running\"), (0.5, \"succeeded\")], failing=True)\n    tracker = track(fake, deadline_s=0.1, drain_s=5)\n    assert [o[\"status\"] for o in fake.observed] == [None] and tracker.final == \"succeeded\"   # Q2: not observed\n\n\ndef test_an_unfinished_job_is_followed_until_its_drain_limit_only():\n    fake = Statuses([(0, \"running\")])\n    tracker = track(fake, deadline_s=0.1, drain_s=0.2)\n    assert [o[\"status\"] for o in fake.observed] == [\"running\"]\n    assert (tracker.final, tracker.finished_mono) == (None, None) and not tracker.is_alive()\n'''\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q tests/test_jobs_harness.py 2>&1 | grep -E 'passed|failed|Error' | head",
  "description": "Add harness arming, phase and Tracker tests and run them"
}
```

## 139. User — 2026-10-24T07:36:17.049Z

### Tool result

```
17 passed, 1 warning in 2.91s
```

## 140. Assistant — 2026-10-24T07:36:44.458Z

Harness: 17 passed. Now the frozen SQL on SQLite, checked against all 82 frozen expected rows. First the shared translation helper:

## 141. Assistant — 2026-10-24T07:36:59.086Z

### Tool call: Write

````
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/recovery_sqlite.py",
  "content": "\"\"\"The recovery experiments' frozen cross-check SQL (src/etf_risk/jobs/crosscheck.sql) and the\nfixture of docs/recovery-sql.md, translated for SQLite, for the offline tests.\n\nThe translation changes only this:\n- the DDL loses CHARACTER SET ascii COLLATE ascii_bin: SQLite compares text byte by byte\n  (its BINARY collation) by default, as ascii_bin does;\n- CAST(x AS BINARY) becomes x: SQLite reads BINARY as a NUMERIC type name and would turn every\n  worker id into 0, while MySQL compares the bytes, as SQLite does by default;\n- in the fixture, the session variables (@s, @t0, ...) become their values, with the times\n  given six decimals as MySQL's DATETIME(6) prints them; REPEAT('c', 64) becomes the literal;\n  SET FOREIGN_KEY_CHECKS becomes PRAGMA foreign_keys.\nThe run on MySQL 8.4.13 (docs/recovery-sql.md, section 6) stays the evidence for MySQL; the\ntranslation checks the same verdict rules offline, on every test run.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nimport re\nfrom pathlib import Path\n\nREPO = Path(__file__).resolve().parents[1]\nDOC = REPO / \"docs\" / \"recovery-sql.md\"\nFIXTURE_BLOCKS = (\"-- Fixture A, store rows\", \"-- Fixture B, store rows\", \"-- Fixture A, the harness's rows\",\n                  \"-- Fixture B, the harness's rows\")\nEXPECTED = (\"Q0\", \"Q1\", \"Q2\", \"Q2b\", \"Q3a\", \"Q3b\")\n_TIME = re.compile(r\"^\\d{4}-\\d\\d-\\d\\d \\d\\d:\\d\\d:\\d\\d$\")\n\n\ndef sqlite_statement(sql: str) -> str:\n    \"\"\"A statement of crosscheck.sql as SQLite runs it.\"\"\"\n    sql = sql.replace(\" CHARACTER SET ascii COLLATE ascii_bin\", \"\")\n    return re.sub(r\"CAST\\(([\\w.]+) AS BINARY\\)\", r\"\\1\", sql)\n\n\ndef _blocks() -> list[str]:\n    return re.findall(r\"^```sql\\n(.*?)^```$\", DOC.read_text(), flags=re.S | re.M)\n\n\ndef fixture_scripts() -> list[str]:\n    \"\"\"The fixture's four SQL blocks (store rows A and B, then the harness's rows A and B), as\n    SQLite scripts. The harness's rows use the variables the store rows set, as in one session.\"\"\"\n    blocks = [next(b for b in _blocks() if b.startswith(prefix)) for prefix in FIXTURE_BLOCKS]\n    values = {}\n    for block in blocks:\n        values.update(re.findall(r\"@(\\w+)\\s*=\\s*'([^']*)'\", block))\n    literals = {name: f\"'{value}.000000'\" if _TIME.match(value) else f\"'{value}'\" for name, value in values.items()}\n    scripts = []\n    for block in blocks:\n        statements = [st for st in re.split(r\";\\s*\\n\", block) if st.strip()]\n        out = []\n        for statement in statements:\n            body = \"\\n\".join(line for line in statement.splitlines() if not line.lstrip().startswith(\"--\")).strip()\n            if body.startswith(\"SET @\"):\n                continue\n            if body.startswith(\"SET FOREIGN_KEY_CHECKS\"):\n                body = \"PRAGMA foreign_keys = \" + (\"ON\" if body.rstrip(\";\").endswith(\"1\") else \"OFF\")\n            body = re.sub(r\"REPEAT\\('(.)', 64\\)\", lambda m: f\"'{m.group(1) * 64}'\", body)\n            body = re.sub(r\"@(\\w+)\", lambda m: literals[m.group(1)], body)\n            out.append(body.rstrip(\";\") + \";\")\n        scripts.append(\"\\n\".join(out))\n    return scripts\n\n\ndef expected_rows() -> dict[str, list[list[str]]]:\n    \"\"\"Section 4's frozen tables, header first, with c×64 written out: Q0-Q3b and\n    \"invariants\" (the store's seven invariant queries).\"\"\"\n    text = DOC.read_text()\n    section = text[text.index(\"## 4. Expected rows (frozen)\"):text.index(\"## 5. Coverage\")]\n    names = {f\"**{name}**\": name for name in EXPECTED}\n    tables, current = {}, None\n    for line in section.splitlines():\n        if line.strip() in names:\n            current = names[line.strip()]\n        elif line.startswith(\"**The store's seven invariant queries**\"):\n            current = \"invariants\"\n        elif line.startswith(\"|\") and current is not None:\n            cells = [c.strip() for c in line.strip().strip(\"|\").split(\"|\")]\n            if set(\"\".join(cells)) <= set(\"-\"):\n                continue\n            tables.setdefault(current, []).append([_expand(c) for c in cells])\n        elif line.strip() and not line.startswith(\"|\") and current in tables:\n            current = None\n    return tables\n\n\ndef _expand(cell: str) -> str:\n    match = re.fullmatch(r\"(.)×64\", cell)\n    return match.group(1) * 64 if match else cell\n\n\ndef as_text(value) -> str:\n    \"\"\"A value as section 4 writes it: NULL, or the value's text.\"\"\"\n    return \"NULL\" if value is None else str(value)\n"
}
````

## 142. User — 2026-10-24T07:37:00.321Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/recovery_sqlite.py (file state is current in your context — no need to Read it back)
```

## 143. Assistant — 2026-10-24T07:37:25.174Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_sql.py",
  "content": "\"\"\"The frozen cross-check SQL on SQLite: fixtures A and B of docs/recovery-sql.md, loaded and\nqueried with crosscheck.sql as the harness runs it, and every row compared with the 82 frozen\nexpected rows of section 4. Every verdict is covered, late completion (job 2) included, and both\nways of not observing a deadline (jobs 19 and 20). The translation for SQLite is in\ntests/recovery_sqlite.py; the expected rows are read from the document, never copied here.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nimport pytest\nfrom recovery_sqlite import as_text, expected_rows, fixture_scripts, sqlite_statement\n\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.store import SQLITE, JobStore, open_sqlite\n\n\n@pytest.fixture(scope=\"module\")\ndef actual(tmp_path_factory):\n    \"\"\"Each query's rows, header first, in one connection: the schema, the store rows, the\n    TEMPORARY tables, the harness's rows, then Q0-Q3b and the store's invariant queries.\"\"\"\n    conn = open_sqlite(tmp_path_factory.mktemp(\"recovery-sql\") / \"jobs.sqlite\", create=True)\n    store_a, store_b, harness_a, harness_b = fixture_scripts()\n    conn.executescript(store_a + store_b)\n    statements = harness.crosscheck_statements()\n    for name, sql in statements:\n        if name == \"DDL\":\n            conn.execute(sqlite_statement(sql))\n    conn.executescript(harness_a + harness_b)\n    tables = {}\n    for name, sql in statements:\n        if name != \"DDL\":\n            cursor = conn.execute(sqlite_statement(sql))\n            tables[name] = [[d[0] for d in cursor.description]] + [[as_text(v) for v in row] for row in cursor]\n    violations = JobStore(conn, SQLITE).invariant_violations()\n    tables[\"invariants\"] = [[\"invariant\", \"job_id\"]] + sorted([name, str(job)] for name, jobs in violations.items()\n                                                              for job in jobs)\n    conn.close()\n    return tables\n\n\ndef test_the_document_holds_82_expected_rows():\n    expected = expected_rows()\n    assert {name: len(rows) - 1 for name, rows in expected.items()} == {\n        \"Q0\": 1, \"Q1\": 20, \"Q2\": 20, \"Q2b\": 1, \"Q3a\": 16, \"Q3b\": 17, \"invariants\": 7}\n\n\n@pytest.mark.parametrize(\"query\", [\"Q0\", \"Q1\", \"Q2\", \"Q2b\", \"Q3a\", \"Q3b\", \"invariants\"])\ndef test_every_row_equals_its_frozen_expected_row(actual, query):\n    expected = expected_rows()[query]\n    assert actual[query][0] == expected[0]                                   # the header\n    assert actual[query][1:] == expected[1:]\n\n\ndef test_every_verdict_and_class_occurs(actual):\n    def column(query, name):\n        header, *rows = actual[query]\n        return {row[header.index(name)] for row in rows}\n\n    from collect_recovery_measurements_path import crm\n    assert column(\"Q1\", \"verdict\") == set(crm.Q1_VERDICTS)\n    assert column(\"Q2\", \"timeliness\") == set(crm.Q2_CLASSES)\n    assert column(\"Q2\", \"deadline_met\") == set(crm.DEADLINE_MET)\n    assert column(\"Q3a\", \"log_verdict\") == set(crm.Q3A_VERDICTS)\n    assert column(\"Q3b\", \"report_verdict\") == set(crm.Q3B_VERDICTS)\n\n\ndef test_late_completion_is_late_and_never_on_time(actual):\n    \"\"\"Job 2: running at its deadline, observed after it, succeeded later by attempt 2.\"\"\"\n    header, *rows = actual[\"Q2\"]\n    late = dict(zip(header, next(r for r in rows if r[header.index(\"job_id\")] == \"2\")))\n    assert (late[\"status_at_deadline\"], late[\"final_status\"], late[\"timeliness\"], late[\"deadline_met\"]) == (\n        \"running\", \"succeeded\", \"late\", \"no\")\n"
}
```

## 144. User — 2026-10-24T07:37:26.302Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_sql.py (file state is current in your context — no need to Read it back)
```

## 145. Assistant — 2026-10-24T07:37:32.798Z

That import doesn't exist. I'll load the collector the way test_recovery_collector.py does:

## 146. Assistant — 2026-10-24T07:37:36.833Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/test_recovery_sql.py\")\ns = p.read_text()\nold = '''import pytest\nfrom recovery_sqlite import as_text, expected_rows, fixture_scripts, sqlite_statement\n\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.store import SQLITE, JobStore, open_sqlite\n'''\nnew = '''import importlib.util\n\nimport pytest\nfrom recovery_sqlite import REPO, as_text, expected_rows, fixture_scripts, sqlite_statement\n\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.store import SQLITE, JobStore, open_sqlite\n\nspec = importlib.util.spec_from_file_location(\"collect_recovery_measurements\",\n                                              REPO / \"analysis\" / \"collect_recovery_measurements.py\")\ncrm = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(crm)\n'''\nassert s.count(old) == 1\ns = s.replace(old, new)\nold = '''\n    from collect_recovery_measurements_path import crm\n    assert column(\"Q1\", \"verdict\")'''\nnew = '''\n    assert column(\"Q1\", \"verdict\")'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q tests/test_recovery_sql.py 2>&1 | grep -E 'passed|failed|Error|^E ' | head -30",
  "description": "Fix the collector import and run the SQL tests"
}
```

## 147. User — 2026-10-24T07:37:39.510Z

### Tool result

```
E       AssertionError: assert [['accepted a...', '10'], ...] == [['accepted a...t', '8'], ...]
E         
E         At index 5 diff: ['succeeded without exactly one accepted attempt', '10'] != ['succeeded without exactly one accepted attempt', '8']
E         Use -v to get more diff
tests/test_recovery_sql.py:57: AssertionError
1 failed, 9 passed, 1 warning in 0.15s
```

## 148. Assistant — 2026-10-24T07:37:45.047Z

Every query matched its frozen rows. The one failure is my own sort: job ids sorted as text put '10' before '8'. Fixing it to sort numerically:

## 149. Assistant — 2026-10-24T07:37:47.001Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_sql.py",
  "old_string": "    tables[\"invariants\"] = [[\"invariant\", \"job_id\"]] + sorted([name, str(job)] for name, jobs in violations.items()\n                                                              for job in jobs)",
  "new_string": "    tables[\"invariants\"] = [[\"invariant\", \"job_id\"]] + [[name, str(job)] for name, job in sorted(\n        (name, job) for name, jobs in violations.items() for job in jobs)]          # by invariant, then job"
}
```

## 150. Assistant — 2026-10-24T07:37:48.107Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -m pytest -q tests/test_recovery_sql.py 2>&1 | grep -E 'passed|failed|^E ' | head",
  "description": "Rerun the frozen SQL tests on SQLite"
}
```

## 151. User — 2026-10-24T07:37:49.778Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_sql.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 152. User — 2026-10-24T07:37:51.794Z

### Tool result

```
10 passed, 1 warning in 0.12s
```

## 153. Assistant — 2026-10-24T07:37:58.296Z

All 10 pass: translated for SQLite, the frozen SQL reproduces all 82 expected rows. A quick mutation check to confirm the comparison is sensitive:

## 154. Assistant — 2026-10-24T07:38:03.200Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python - <<'EOF'\nimport sys, tempfile\nfrom pathlib import Path\nsys.path.insert(0, \"tests\")\nfrom recovery_sqlite import as_text, expected_rows, fixture_scripts, sqlite_statement\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.store import open_sqlite\n\ndef q2(mutate):\n    with tempfile.TemporaryDirectory() as d:\n        conn = open_sqlite(Path(d) / \"j.sqlite\", create=True)\n        a, b, ha, hb = fixture_scripts()\n        conn.executescript(a + b)\n        st = harness.crosscheck_statements()\n        for n, sql in st:\n            if n == \"DDL\":\n                conn.execute(sqlite_statement(sql))\n        conn.executescript(ha + hb)\n        sql = mutate(dict(st)[\"Q2\"])\n        cur = conn.execute(sqlite_statement(sql))\n        return [[c[0] for c in cur.description]] + [[as_text(v) for v in r] for r in cur]\n\nexp = expected_rows()[\"Q2\"]\nprint(\"unchanged equal:\", q2(lambda s: s) == exp)\nm = lambda s: s.replace(\"d.observed_from_mono >= b.deadline_mono\", \"d.observed_from_mono >= b.deadline_mono + 100\")\nprint(\"late rule mutated equal:\", q2(m) == exp)\nm2 = lambda s: s.replace(\"b.deadline_mono + b.max_lag_s\", \"b.deadline_mono + 10\")\nprint(\"lag rule mutated equal:\", q2(m2) == exp)\nEOF",
  "description": "Mutate Q2 rules to confirm the SQL test detects changes"
}
```

## 155. User — 2026-10-24T07:38:04.994Z

### Tool result

```
unchanged equal: True
late rule mutated equal: False
lag rule mutated equal: False
```

## 156. Assistant — 2026-10-24T07:38:13.142Z

The SQL test catches changes to both rules. Now running the full set of new and affected offline tests before building the synthetic end-to-end test:

## 157. Assistant — 2026-10-24T07:38:15.024Z

### Tool call: Bash

```
{
  "command": "env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_jobs_*.py tests/test_provenance.py tests/test_recovery_collector.py tests/test_recovery_sql.py 2>&1 | tail -4",
  "description": "Run all job, provenance and recovery tests offline",
  "timeout": 600000
}
```

## 158. User — 2026-10-24T07:40:07.366Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_jobs_worker_spark.py::test_a_job_runs_the_real_steps_and_its_accepted_result_matches_a_direct_run
1 failed, 335 passed, 30 skipped, 279 warnings in 110.06s (0:01:50)
```

## 159. Assistant — 2026-10-24T07:40:13.168Z

### Tool call: Bash

```
{
  "command": "env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_jobs_worker_spark.py -x 2>&1 | grep -E '^E |Error|error|assert|FAILED|passed|failed' | head -40",
  "description": "Show why the real-steps worker test failed",
  "timeout": 600000
}
```

## 160. User — 2026-10-24T07:40:56.791Z

### Tool result

```
        assert handled.result is Result.ACCEPTED, (tmp_path / "runs").rglob("*.log")
        assert (store.job(job)["status"], attempt["outcome"]) == (Status.SUCCEEDED, Outcome.ACCEPTED)
        assert attempt["result_digest"] == runs.folder_digest(run_folder)
        assert store.invariant_violations() == {}
        assert record["status"] == "ok" and not record["environment"]["java"].startswith("Picked up")
        assert "jobs/pipeline.py" in record["code"]["source_sha256"]
        assert verified["mismatch_count"] == 0 and verified["breached_windows"] == {"python": 1, "spark": 1, "same": True}
        assert [s["outcome"] for s in attempt_record["steps"]] == ["exited"] * 3
        assert all(s["peak_rss_bytes"] > 0 for s in attempt_record["steps"])
        assert not (run_dir / ".work").exists() and not any(processes.marked_processes())
        assert spark_scratch() <= scratch_before                         # nothing left in the temporary folders
        assert not (REPO / "spark-warehouse").exists() or (REPO / "spark-warehouse").stat().st_mtime < os.path.getmtime(
>       assert spark_pipeline.main(["--windows", str(windows), "--out-root", str(tmp_path / "ref" / "out"),
E       AssertionError: assert 2 == 0
E        +  where 2 = <function main at 0x120a3a020>(['--windows', '/private/var/folders/v3/vrsj5my17pz05dhqq55gl_zm0000gn/T/pytest-of-[REDACTED:user]/pytest-455/test_a_job_runs_t...y17pz05dhqq55gl_zm0000gn/T/pytest-of-[REDACTED:user]/pytest-455/test_a_job_runs_the_real_steps0/ref/out', '--run-id', 'direct'])
E        +    where <function main at 0x120a3a020> = spark_pipeline.main
tests/test_jobs_worker_spark.py:90: AssertionError
direct: failed  ({})  -> /private/var/folders/v3/vrsj5my17pz05dhqq55gl_zm0000gn/T/pytest-of-[REDACTED:user]/pytest-455/test_a_job_runs_the_real_steps0/ref/out/snap/w/direct
ModuleNotFoundError: No module named 'etf_risk'
	at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally(SparkErrorUtils.scala:86)
	at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally$(SparkErrorUtils.scala:83)
ModuleNotFoundError: No module named 'etf_risk'
	at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally(SparkErrorUtils.scala:86)
	at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally$(SparkErrorUtils.scala:83)
26/10/24 02:40:56 ERROR TaskSetManager: Task 0 in stage 26.0 failed 1 times; aborting job
ModuleNotFoundError: No module named 'etf_risk'
	at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally(SparkErrorUtils.scala:86)
	at org.apache.spark.util.SparkErrorUtils.tryWithSafeFinally$(SparkErrorUtils.scala:83)
  error: ModuleNotFoundError: No module named 'etf_risk'
  ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/.venv/lib/python3.12/site-packages/exchange_calendars/exchange_calendar.py:65: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
  ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/.venv/lib/python3.12/site-packages/pandas_market_calendars/market_calendar.py:100: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
  ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/conftest.py:18: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
FAILED tests/test_jobs_worker_spark.py::test_a_job_runs_the_real_steps_and_its_accepted_result_matches_a_direct_run
1 failed, 23 warnings in 41.93s
```

## 161. Assistant — 2026-10-24T07:41:09.970Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider tests/test_jobs_worker_spark.py 2>&1 | tail -1",
  "description": "Rerun the real-steps worker test with the venv on PATH",
  "timeout": 600000
}
```

## 162. User — 2026-10-24T07:41:56.675Z

### Tool result

```
1 passed, 23 warnings in 44.65s
```

## 163. Assistant — 2026-10-24T07:43:32.637Z

### Tool call: Bash

```
{
  "command": "sed -n 120,150p src/etf_risk/jobs/cli.py && sed -n \"$(grep -n '^def main' src/etf_risk/jobs/cli.py | cut -d: -f1),+45p\" src/etf_risk/jobs/cli.py && sed -n 236,300p src/etf_risk/jobs/pipeline.py && sed -n 1,30p src/etf_risk/jobs/kafka.py | grep -n import",
  "description": "Read CLI init-db, argument defaults and the step events"
}
```

## 164. User — 2026-10-24T07:43:33.449Z

### Tool result

```
def stop_on_signals() -> threading.Event:
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    return stop


# Commands

def cmd_init_db(args) -> int:
    if args.db.startswith("sqlite:///"):
        path = Path(args.db[len("sqlite:///"):])
        open_sqlite(path, create=not path.exists()).close()
    else:
        from etf_risk.jobs import mysql
        database = urlsplit(args.db).path.strip("/")
        if not database or not database.replace("_", "").isalnum():
            raise SystemExit("--db: name the database in the URL with letters, digits and underscores")
        admin = mysql.connect_mysql(urlunsplit(urlsplit(args.db)._replace(path="")))    # no database selected
        try:
            with admin.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
        finally:
            admin.close()
        conn = mysql.connect_mysql(args.db)
        try:
            with conn.cursor() as cursor:
                cursor.execute("SHOW TABLES LIKE 'jobs'")
                has_jobs = cursor.fetchone() is not None
                cursor.execute("SHOW TABLES LIKE 'job_store'")
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs", description=__doc__.splitlines()[0])
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--db", default=os.environ.get("ETF_RISK_JOBS_DB"),
                        help="mysql://user:password@host:port/database or sqlite:////path (ETF_RISK_JOBS_DB)")
    common.add_argument("--bootstrap", default=os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", "127.0.0.1:9094"))
    common.add_argument("--topic", default=os.environ.get("ETF_RISK_JOBS_TOPIC", DEFAULT_TOPIC))
    common.add_argument("--output-root", default="data/outputs/jobs")
    common.add_argument("--processed-root", default="data/processed")
    common.add_argument("--events", help="folder of the event logs (default: <output root>/events)")
    common.add_argument("--timing", action="append", default=[], metavar="NAME=SECONDS")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init-db", parents=[common])
    commands.add_parser("create-topic", parents=[common])
    submit = commands.add_parser("submit", parents=[common])
    submit.add_argument("--snapshot", required=True)
    submit.add_argument("--kind", required=True)
    submit.add_argument("--window-days", type=int, default=JobParams.__dataclass_fields__["window_days"].default)
    submit.add_argument("--stride", type=int, default=JobParams.__dataclass_fields__["stride"].default)
    submit.add_argument("--anchor", default=JobParams.__dataclass_fields__["anchor"].default)
    submit.add_argument("--sample-ticker", default=JobParams.__dataclass_fields__["sample_ticker"].default)
    submit.add_argument("--max-attempts", type=int, default=3)
    worker = commands.add_parser("worker", parents=[common])
    worker.add_argument("--group", default=DEFAULT_GROUP)
    worker.add_argument("--worker-id")
    worker.add_argument("--lock", default=str(DEFAULT_LOCK))
    worker.add_argument("--standby", action="store_true", help="recorded in the events; any worker can stand by")
    reconciler = commands.add_parser("reconciler", parents=[common])
    reconciler.add_argument("--interval", type=float, default=5.0)
    status = commands.add_parser("status", parents=[common])
    status.add_argument("--check", action="store_true")
    status.add_argument("--job", type=int, nargs="*")
    commands.add_parser("cleanup", parents=[common])
    export = commands.add_parser("export", parents=[common])
    export.add_argument("folder")
    args = parser.parse_args(argv)
    if not args.db:
        parser.error("no database: give --db or set ETF_RISK_JOBS_DB")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    handler = {"init-db": cmd_init_db, "create-topic": cmd_create_topic, "submit": cmd_submit, "worker": cmd_worker,
               "reconciler": cmd_reconciler, "status": cmd_status, "cleanup": cmd_cleanup, "export": cmd_export}
    return handler[args.command](args)
            return False

    def _run_step(self, name: str, argv: list[str], env: dict, work: Path, logs: Path, renewer: Renewer,
                  marker: str, claim: Claim) -> dict:
        t = self.timing
        result_path = logs / f"{name}.launcher.json"
        command = [self.python, "-m", "etf_risk.jobs.launcher", "--marker", marker, "--lock", str(self.lock_path),
                   "--registry", str(self.registry), "--lock-wait", str(t.lock_wait(name)),
                   "--step-limit", str(t.step_limit(name)), "--cwd", str(work), "--step-log", str(logs / f"{name}.log"),
                   "--result", str(result_path), "--tick", str(t.watchdog_tick), "--term-grace", str(t.term_grace),
                   "--kill-confirm", str(t.kill_confirm), "--", *argv]
        self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name,
                        code=source_identity())     # the code the step starts from (recovery experiments, 2.3)
        with open(logs / f"{name}.launcher.log", "ab") as launcher_log:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=launcher_log, stderr=subprocess.STDOUT,
                                    env=env, cwd=work, start_new_session=True)
        fd = proc.stdin.fileno()
        os.set_blocking(fd, False)
        self._send(fd, {"monotonic": time.monotonic(), "seq": renewer.seq, "deadline": renewer.fence_at})
        closed, closed_at, backstop = None, None, None
        while True:
            try:
                proc.wait(timeout=t.worker_tick)
                break
            except subprocess.TimeoutExpired:
                pass
            now = time.monotonic()
            if closed is None:
                if self.stop is not None and self.stop.is_set():
                    closed = "stopped"
                elif renewer.due(now):
                    ok = renewer.renew()
                    self.fence_at = renewer.fence_at
                    if ok:
                        self._send(fd, {"seq": renewer.seq, "deadline": renewer.fence_at})
                    elif ok is False:
                        closed = "fenced"
                if closed is None and renewer.passed(time.monotonic()):
                    closed = "self_fenced"
                if closed is not None:
                    proc.stdin.close()                   # EOF: the launcher ends the tree
                    closed_at = time.monotonic()
                    self.events.log(closed, job_id=claim.job_id, attempt=claim.attempt_number, step=name)
            elif backstop is None and now - closed_at > t.kill_grace + 10:
                # The launcher did not act on the EOF (it is stopped, perhaps): end the tree here.
                backstop = processes.terminate(processes.attempt_members(proc.pid, marker, exclude=[proc.pid]),
                                               term_grace=t.term_grace, kill_confirm=t.kill_confirm)
                proc.kill()
        if not proc.stdin.closed:
            proc.stdin.close()
        try:
            result = json.loads(result_path.read_text())
        except (OSError, json.JSONDecodeError):
            result = {"outcome": "launcher_died", "returncode": None}
        step = {"name": name, "outcome": result.get("outcome"), "returncode": result.get("returncode"),
                "seconds": result.get("step_seconds"), "lock_wait_s": result.get("lock_wait_s"),
                "peak_rss_bytes": result.get("peak_rss_bytes"), "ended": result.get("ended"),
                "lingering": result.get("lingering"), "closed": closed, "launcher_exit": proc.returncode,
                "backstop": backstop}
        self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number,
                        **{k: v for k, v in step.items() if k not in ("ended", "backstop")})
        return step

    # Records
```

## 165. Assistant — 2026-10-24T07:43:54.525Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/etf_risk/jobs/harness.py\")\ns = p.read_text()\nold = '''        events = self.worker_logs()[claim[\"worker\"]]\n        mine = {\"job_id\": job_id, \"attempt\": claim[\"attempt\"], \"step\": \"spark_pipeline\"}\n        if not events_named(events, \"step_started\", **mine) or events_named(events, \"step_ended\", **mine):\n            return None'''\nnew = '''        events = self.worker_logs()[claim[\"worker\"]]\n        mine = {\"job_id\": job_id, \"attempt\": claim[\"attempt\"]}\n        # step_started names its step in \"step\"; step_ended, the pipeline's step record, in \"name\"\n        if (not events_named(events, \"step_started\", step=\"spark_pipeline\", **mine)\n                or events_named(events, \"step_ended\", name=\"spark_pipeline\", **mine)):\n            return None'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\ngrep -n '\"step_ended\"\\|step_ended' src/etf_risk/jobs/harness.py analysis/collect_recovery_measurements.py docs/recovery-experiments.md | head",
  "description": "Match step_ended by its name field in the harness"
}
```

## 166. User — 2026-10-24T07:43:55.381Z

### Tool result

```
src/etf_risk/jobs/harness.py:592:        # step_started names its step in "step"; step_ended, the pipeline's step record, in "name"
src/etf_risk/jobs/harness.py:594:                or events_named(events, "step_ended", name="spark_pipeline", **mine)):
docs/recovery-experiments.md:140:`step_ended`) or, for W5a, from the table; an injection that lands elsewhere is recorded with the
```

## 167. Assistant — 2026-10-24T07:44:04.683Z

Adding a unit test for the fix, then checking what submit needs from a snapshot:

## 168. Assistant — 2026-10-24T07:44:09.426Z

### Tool call: Bash

```
{
  "command": "cat >> tests/test_jobs_harness.py <<'EOF'\n\n\ndef test_the_spark_step_counts_as_running_from_its_start_until_its_step_ended_record(tmp_path):\n    \"\"\"step_ended is the pipeline's step record, which names the step in \"name\", not \"step\".\"\"\"\n    batch = offline_batch(tmp_path)\n    batch.store_id = \"s\" * 32\n    log(batch, \"A\", {\"event\": \"claimed\", \"job_id\": 7, \"attempt\": 1, \"run_id\": \"job-7-attempt-1\", \"mono\": 1})\n    assert batch.spark_running(7) is None                                        # not started\n    log(batch, \"A\", {\"event\": \"step_started\", \"job_id\": 7, \"attempt\": 1, \"step\": \"spark_pipeline\", \"mono\": 2})\n    assert batch.spark_running(7) is None                                        # no step log yet\n    logs = batch.attempt_dir(\"job-7-attempt-1\") / \"logs\"\n    logs.mkdir(parents=True)\n    (logs / \"spark_pipeline.log\").touch()\n    assert batch.spark_running(7)[\"worker\"] == \"A\"\n    log(batch, \"A\", {\"event\": \"step_ended\", \"job_id\": 7, \"attempt\": 1, \"name\": \"spark_pipeline\", \"outcome\": \"exited\",\n                     \"mono\": 3})\n    assert batch.spark_running(7) is None\nEOF\n.venv/bin/python -m pytest -q tests/test_jobs_harness.py -k spark_step 2>&1 | tail -1; grep -n -E 'sample_ticker|class JobParams|def input_checksums|def check_inputs' -A3 src/etf_risk/jobs/params.py | head -40",
  "description": "Test the spark-step detection and read job parameter rules"
}
```

## 169. User — 2026-10-24T07:44:11.997Z

### Tool result

```
1 failed, 17 deselected, 1 warning in 0.52s
39:class JobParams:
40-    snapshot: str
41-    kind: str
42-    window_days: int = ROLLING_WINDOW_DAYS
--
45:    sample_ticker: str = "AAPL"
46-
47-    def __post_init__(self) -> None:
48-        if not isinstance(self.snapshot, str) or not _NAME.fullmatch(self.snapshot) or ".." in self.snapshot:
--
62:        if not isinstance(self.sample_ticker, str) or not _TICKER.fullmatch(self.sample_ticker):
63:            raise InvalidParams(f"sample_ticker must be a ticker symbol, not {self.sample_ticker!r}")
64-
65-    @classmethod
66-    def from_dict(cls, data: dict) -> JobParams:
--
86:def input_checksums(processed_root: str | Path, snapshot: str) -> dict[str, str]:
87-    """SHA-256 of each file in the snapshot that windows.py reads, keyed by its path relative
88-    to the snapshot folder, as windows.py's config keys them."""
89-    snapshot_dir = Path(processed_root) / snapshot
--
99:def check_inputs(processed_root: str | Path, snapshot: str, recorded: dict[str, str]) -> None:
100-    """Raise InvalidParams unless the snapshot's files are exactly those the job recorded."""
101-    current = input_checksums(processed_root, snapshot)
102-    if current != recorded:
```

## 170. Assistant — 2026-10-24T07:44:19.318Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python -m pytest -q tests/test_jobs_harness.py -k spark_step 2>&1 | grep -E '^E |Error' | head -10",
  "description": "Show the spark-step test failure"
}
```

## 171. User — 2026-10-24T07:44:21.752Z

### Tool result

```
E               TypeError: events_named() got multiple values for argument 'name'
src/etf_risk/jobs/harness.py:594: TypeError
```

## 172. Assistant — 2026-10-24T07:44:28.845Z

The test caught a bug in my fix: `events_named`'s second parameter is itself called `name`, so `name=` clashes. Making the leading parameters positional-only lets any field name pass as a keyword:

## 173. Assistant — 2026-10-24T07:44:33.190Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/etf_risk/jobs/harness.py\")\ns = p.read_text()\nold = '''def events_named(events: list[dict], name: str, **fields_) -> list[dict]:\n    return [e for e in events if e.get(\"event\") == name and all(e.get(k) == v for k, v in fields_.items())]'''\nnew = '''def events_named(events: list[dict], event: str, /, **fields_) -> list[dict]:\n    \"\"\"The events called `event` whose fields equal fields_ (any field, \"name\" included).\"\"\"\n    return [e for e in events if e.get(\"event\") == event and all(e.get(k) == v for k, v in fields_.items())]'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\np = Path(\"analysis/collect_recovery_measurements.py\")\ns = p.read_text()\nold = '''def named(events: list[dict], name: str, **fields_) -> list[dict]:\n    return [e for e in events if e.get(\"event\") == name and all(e.get(k) == v for k, v in fields_.items())]'''\nnew = '''def named(events: list[dict], event: str, /, **fields_) -> list[dict]:\n    return [e for e in events if e.get(\"event\") == event and all(e.get(k) == v for k, v in fields_.items())]'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q tests/test_jobs_harness.py tests/test_recovery_collector.py 2>&1 | tail -1",
  "description": "Make event filters accept a name field and rerun tests"
}
```

## 174. User — 2026-10-24T07:44:39.549Z

### Tool result

```
28 passed, 81 warnings in 4.23s
```

## 175. Assistant — 2026-10-24T07:44:46.391Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^import|^from|def log_assignment' -A0 src/etf_risk/jobs/kafka.py | head; sed -n \"$(grep -n 'def log_assignment' src/etf_risk/jobs/kafka.py | cut -d: -f1),+12p\" src/etf_risk/jobs/kafka.py; grep -n -E '^def (folder_digest|manifest|digest)' src/etf_risk/runs.py; .venv/bin/python -c \"\nimport time\nfrom etf_risk.provenance import source_identity, code_identity\nt=time.monotonic(); source_identity(); print('source_identity s', round(time.monotonic()-t,3))\nt=time.monotonic(); code_identity(); print('code_identity s', round(time.monotonic()-t,3))\"",
  "description": "Check the Kafka helper, run digests and identity cost"
}
```

## 176. User — 2026-10-24T07:44:48.070Z

### Tool result

```
42:from __future__ import annotations
44:import logging
45:from datetime import timedelta
47:from etf_risk.jobs.events import NO_EVENTS, EventLog
48:from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, Delivery, encode
49:from etf_risk.jobs.timing import DEFAULT_TIMING, Timing
58:def log_assignment(events: EventLog, kind: str, consumer, partitions) -> None:
def log_assignment(events: EventLog, kind: str, consumer, partitions) -> None:
    """Write an assigned, revoked or lost event for a rebalance callback."""
    try:
        member = consumer.memberid()
    except Exception:                                  # no member id yet, or none to report
        member = None
    events.log(kind, partitions=[[p.topic, p.partition] for p in partitions], member=member)


def producer_config(bootstrap: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT,
                    timing: Timing = DEFAULT_TIMING) -> dict:
    return {"bootstrap.servers": bootstrap, "acks": "all", "enable.idempotence": True, "linger.ms": 0,
            "message.timeout.ms": int(confirmation_timeout.total_seconds() * 1000),
45:def manifest(folder: str | Path) -> dict:
64:def digest(manifest: dict) -> str:
69:def folder_digest(folder: str | Path) -> str:
source_identity s 0.009
code_identity s 0.041
```

## 177. Assistant — 2026-10-24T07:47:01.076Z

Checking that the run digest the pipeline returns equals what the collector recomputes, and what JobParams accepts:

## 178. Assistant — 2026-10-24T07:47:02.446Z

### Tool call: Bash

```
{
  "command": "sed -n 45,80p src/etf_risk/runs.py; sed -n 47,64p src/etf_risk/jobs/params.py; sed -n 86,98p src/etf_risk/jobs/params.py",
  "description": "Read the run digest functions and parameter checks"
}
```

## 179. User — 2026-10-24T07:47:03.219Z

### Tool result

```
def manifest(folder: str | Path) -> dict:
    """Every file below folder, by relative POSIX path, with its size and SHA-256."""
    folder = Path(folder)
    if not folder.is_dir() or folder.is_symlink():
        raise NotADirectoryError(f"{folder}: not a folder")
    files = []
    for parent, dirs, names in os.walk(folder):
        for name in dirs + names:
            if (Path(parent) / name).is_symlink():
                raise ValueError(f"{Path(parent) / name}: a symbolic link; a run folder holds plain files only")
        for name in names:
            path = Path(parent) / name
            files.append({"path": path.relative_to(folder).as_posix(), "size": path.stat().st_size,
                          "sha256": _sha256(path)})
    if not files:
        raise ValueError(f"{folder}: no files")
    return {"format": MANIFEST_FORMAT, "files": sorted(files, key=lambda f: f["path"])}


def digest(manifest: dict) -> str:
    """The run digest of a manifest: the SHA-256 of its canonical JSON."""
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def folder_digest(folder: str | Path) -> str:
    return digest(manifest(folder))
    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, str) or not _NAME.fullmatch(self.snapshot) or ".." in self.snapshot:
            raise InvalidParams(f"snapshot must be a plain folder name, not {self.snapshot!r}")
        if self.kind not in KIND_NAMES:
            raise InvalidParams(f"kind must be one of {sorted(KIND_NAMES)}, not {self.kind!r}")
        for name in ("window_days", "stride"):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise InvalidParams(f"{name} must be a positive integer, not {value!r}")
        if self.kind == "rolling" and self.stride < MIN_STRIDE:
            raise InvalidParams(f"a job's stride must be at least {MIN_STRIDE} (there is no --allow-dense-stride)")
        try:
            date.fromisoformat(self.anchor)
        except (TypeError, ValueError):
            raise InvalidParams(f"anchor must be an ISO date, not {self.anchor!r}") from None
        if not isinstance(self.sample_ticker, str) or not _TICKER.fullmatch(self.sample_ticker):
            raise InvalidParams(f"sample_ticker must be a ticker symbol, not {self.sample_ticker!r}")

def input_checksums(processed_root: str | Path, snapshot: str) -> dict[str, str]:
    """SHA-256 of each file in the snapshot that windows.py reads, keyed by its path relative
    to the snapshot folder, as windows.py's config keys them."""
    snapshot_dir = Path(processed_root) / snapshot
    files = sorted((snapshot_dir / "daily_returns").glob("*.parquet"))
    if not files:
        raise InvalidParams(f"{snapshot_dir}: no daily returns")
    files.append(snapshot_dir / "quality_report.json")
    if not files[-1].is_file():
        raise InvalidParams(f"{snapshot_dir}: no quality_report.json")
    return {path.relative_to(snapshot_dir).as_posix(): sha256_file(path) for path in files}
```

## 180. Assistant — 2026-10-24T07:47:10.609Z

Writing the synthetic end-to-end test:

## 181. Assistant — 2026-10-24T07:48:14.892Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py",
  "content": "\"\"\"A synthetic batch of the recovery experiments, end to end, with no services: the harness's own\nBatch.run (etf_risk.jobs.harness) drives workers and a reconciler in this process, on a SQLite job\ntable, and the collector (analysis/collect_recovery_measurements.py) then reads the batch folder\nas it would read a real one. No formal experiment: nothing here measures the job system.\n\nReal code: the harness's run, run_job, after_job, arming, phases, Tracker, observation, cross-check\nand final snapshot; the CLI's init-db, submit, status --check and export, run in process; Worker,\nFaultFile, Reconciler and the job store; the frozen crosscheck.sql, translated for SQLite\n(tests/recovery_sqlite.py); the collector.\nStand-ins: Kafka (Group: one partition in memory, with the assignment events kafka.log_assignment\nwrites); the Spark steps and their launchers (SyntheticPipeline); the job processes (ThreadProc,\nwhere a SIGKILL lands within a tick); MySQL (SQLite); the containers (no peaks, no restarts). The\nlease is 2 s and a dead member loses the partition after 0.5 s.\n\nCovered: C0 twice, the second with a deadline observation that fails on purpose; W1, W2, W3; W4,\nwhose deadline is set short so that it completes late; W5a, W5b and X1. Not covered: W6 and W7\n(SIGSTOP of processes), K1 and K2 (Kafka down), D1 and D2 (MySQL down), which need the services.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nimport importlib.util\nimport io\nimport itertools\nimport json\nimport os\nimport signal\nimport subprocess\nimport threading\nimport time\nimport traceback\nfrom contextlib import redirect_stderr, redirect_stdout\nfrom datetime import date, timedelta\nfrom types import SimpleNamespace\n\nimport numpy as np\nimport pyarrow as pa\nimport pyarrow.parquet as pq\nfrom conftest import nyse_sessions, write_snapshot\nfrom recovery_sqlite import REPO, sqlite_statement\n\nfrom etf_risk import runs\nfrom etf_risk.jobs import cli, faults, harness, kafka\nfrom etf_risk.jobs.events import EventLog, read_events\nfrom etf_risk.jobs.queue import Delivery\nfrom etf_risk.jobs.reconciler import Reconciler\nfrom etf_risk.jobs.simulated import MemoryQueue, SimulatedCrash\nfrom etf_risk.jobs.store import SQLITE, JobStore, open_sqlite\nfrom etf_risk.jobs.worker import Fenced, Worker\nfrom etf_risk.provenance import code_identity, source_identity\n\nspec = importlib.util.spec_from_file_location(\"collect_recovery_measurements\",\n                                              REPO / \"analysis\" / \"collect_recovery_measurements.py\")\ncrm = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(crm)\n\nLEASE_S, MARGIN_S = 2.0, 0.5            # the synthetic lease; F = m0 + LEASE_S - MARGIN_S\nSESSION_S = 0.5                         # a dead member loses the partition this long after its death\nSTEPS = ((\"windows\", 0.05), (\"spark_pipeline\", 0.6), (\"verify\", 0.05))\nTICK = 0.01\nJOBS = [\"C0\", \"W1\", \"W2\", \"W3\", \"W4\", \"W5a\", \"W5b\", \"X1\", \"C0\"]     # job ids 1-9, in this order\nUNOBSERVED = {9}                        # the second C0's deadline observation fails\nLATE = {\"W4\": 2.5}                      # seconds; its next run starts after the 2 s lease\nDEADLINE_S = 20.0                       # every other case's deadline\n\n\nclass ThreadProc:\n    \"\"\"A job process as the harness drives it (poll, kill, send_signal, wait), run as a thread. A\n    SIGKILL lands at the thread's next check, within a tick; SIGTERM asks it to stop.\"\"\"\n    _pids = itertools.count(60001)\n\n    def __init__(self, target):\n        self.pid = next(ThreadProc._pids)\n        self.killed, self.stopping = threading.Event(), threading.Event()\n        self.code, self.died_at, self.error = None, None, None\n        self._thread = threading.Thread(target=self._run, args=(target,), daemon=True)\n        self._thread.start()\n\n    def _run(self, target):\n        code = 0\n        try:\n            target(self)\n        except SimulatedCrash:\n            code = -signal.SIGKILL\n        except BaseException:\n            code, self.error = 1, traceback.format_exc()\n        self.died_at = time.monotonic()\n        self.code = code\n\n    def poll(self):\n        return self.code\n\n    def kill(self):\n        self.killed.set()\n\n    def send_signal(self, sig):\n        (self.killed if sig == signal.SIGKILL else self.stopping).set()\n\n    def halted(self) -> bool:\n        return self.killed.is_set() or self.stopping.is_set()\n\n    def check(self):\n        \"\"\"Where a SIGKILL lands.\"\"\"\n        if self.killed.is_set():\n            raise SimulatedCrash(\"SIGKILL\")\n\n    def wait(self, timeout=None):\n        self._thread.join(timeout)\n        if self._thread.is_alive():\n            raise subprocess.TimeoutExpired(f\"thread {self.pid}\", timeout)\n        return self.code\n\n\nclass Group:\n    \"\"\"One partition and one consumer group, with what the harness relies on from Kafka (outline\n    2.4): the first member to join owns the partition, and a newcomer gets nothing while the\n    owner lives; a member that died loses the partition SESSION_S later, one that left at once,\n    to the earliest live member, which reads on from the group's committed offset. Assignments go\n    to the member's event log as kafka.log_assignment writes them.\"\"\"\n\n    def __init__(self, queue: MemoryQueue, topic: str):\n        self.queue, self.topic = queue, topic\n        self.lock = threading.Lock()\n        self.members, self.owner, self.committed = [], None, 0\n\n    def join(self, events: EventLog, proc: ThreadProc) -> \"Member\":\n        member = Member(self, events, proc)\n        with self.lock:\n            self.members.append(member)\n            self._rebalance()\n            if member is not self.owner:\n                member.assigned([])\n        return member\n\n    def _rebalance(self):\n        owner = self.owner\n        if owner is not None and not owner.left and owner.proc.poll() is None:\n            return\n        if owner is not None and not owner.left and time.monotonic() - owner.proc.died_at < SESSION_S:\n            return                                                   # its session has not expired yet\n        live = [m for m in self.members if not m.left and m.proc.poll() is None]\n        self.owner = live[0] if live else None\n        if self.owner is not None:\n            self.owner.position = self.committed\n            self.owner.assigned([SimpleNamespace(topic=self.topic, partition=0)])\n\n\nclass Member:\n    \"\"\"A worker's consumer in the Group.\"\"\"\n\n    def __init__(self, group: Group, events: EventLog, proc: ThreadProc):\n        self.group, self.events, self.proc = group, events, proc\n        self.position, self.left = 0, False\n\n    def memberid(self):\n        return f\"member-{self.proc.pid}\"\n\n    def assigned(self, partitions):\n        kafka.log_assignment(self.events, \"assigned\", self, partitions)\n\n    def poll(self, timeout: float = 0.0):\n        self.proc.check()\n        with self.group.lock:\n            self.group._rebalance()\n            messages = self.group.queue.messages\n            if self.group.owner is self and self.position < len(messages):\n                delivery = Delivery(messages[self.position], self.position)\n                self.position += 1\n                return delivery\n        time.sleep(min(timeout, TICK))\n        return None\n\n    def commit(self, delivery: Delivery):\n        with self.group.lock:\n            if self.group.owner is not self:\n                raise ConnectionError(\"the partition was reassigned\")\n            self.group.committed = max(self.group.committed, delivery.position + 1)\n\n    def rewind(self, delivery: Delivery):\n        self.position = delivery.position\n\n    def close(self):\n        self.left = True\n\n\ndef write_tables(folder) -> None:\n    \"\"\"Four small tables, the same in every run, as the reference comparison of 6.2 reads them.\"\"\"\n    day = date(2024, 1, 2)\n    key = {\"window_kind\": [\"calendar-year\"] * 2, \"ticker\": [\"AAA\", \"BBB\"], \"window_days\": [252, 252],\n           \"entry_date\": [day, day]}\n    tables = {\n        \"window_stats\": {**key, \"mean_return\": [0.01, 0.02]},\n        \"path_days\": {**key, \"leverage\": [2, 2], \"day\": [1, 1], \"value\": [101.0, 99.0]},\n        \"path_summary\": {**key, \"leverage\": [2, 2], \"breached\": [False, True], \"n_breach_rows\": [0, 1],\n                         \"breach_day\": [None, 1], \"breach_date\": [None, day], \"last_ok_date\": [day, None],\n                         \"days_ok\": [1, 0]},\n        \"paired\": {**key, \"breached_1x\": [False, False], \"breached_2x\": [False, True], \"breach_date_2x\": [None, day],\n                   \"breach_day_2x\": [None, 1], \"last_ok_date_2x\": [day, None], \"days_ok_2x\": [1, 0]},\n    }\n    for name, columns in tables.items():\n        (folder / name).mkdir(parents=True)\n        pq.write_table(pa.table(columns), folder / name / \"part-00000.parquet\")\n        (folder / name / \"_SUCCESS\").touch()\n\n\ndef write_result(folder) -> None:\n    folder.mkdir(parents=True)\n    write_tables(folder)\n    (folder / \"run.json\").write_text(json.dumps({\"status\": \"ok\"}))\n    (folder / \"checks.json\").write_text(json.dumps({\"window_stats\": {\"nulls\": 0}, \"paired\": {\"mismatched\": 0}}))\n\n\nclass SyntheticPipeline:\n    \"\"\"Stands in for SubprocessPipeline in a worker thread, with what the harness and the collector\n    read from a real run: a renewal before each step and before acceptance, with F as fence_at;\n    step_started (with the launch-time code identity) and step_ended as the pipeline logs them;\n    logs/<step>.log from the step's start; logs/<step>.launcher.json with the step's monotonic\n    interval once its tree has ended, also when the worker was killed mid-step, since a launcher\n    outlives its worker (EOF); attempt.json, a run folder whose tables equal the reference run's,\n    and manifest.json.\"\"\"\n\n    def __init__(self, events: EventLog, proc: ThreadProc, snapshot: str):\n        self.events, self.proc, self.snapshot = events, proc, snapshot\n        self.fence_at = None\n\n    def _renew(self, heartbeat, claim, before: str):\n        m0 = time.monotonic()\n        ok = heartbeat()\n        self.events.log(\"renewed\" if ok else \"renewal_refused\", job_id=claim.job_id, attempt=claim.attempt_number,\n                        seconds=round(time.monotonic() - m0, 3))\n        if not ok:\n            raise Fenced(f\"{claim.run_id}: the renewal before {before} was refused\")\n        self.fence_at = m0 + LEASE_S - MARGIN_S\n\n    def run(self, claim, run_dir, heartbeat) -> str:\n        self.fence_at = heartbeat.claimed_mono + LEASE_S - MARGIN_S\n        logs, run_folder = run_dir / \"logs\", run_dir / \"output\" / self.snapshot / \"w\" / claim.run_id\n        logs.mkdir()\n        for name, seconds in STEPS:\n            self._renew(heartbeat, claim, before=name)\n            self.events.log(\"step_started\", job_id=claim.job_id, attempt=claim.attempt_number, step=name,\n                            code=source_identity())\n            (logs / f\"{name}.log\").write_text(f\"{name} started\\n\")\n            started, outcome = time.monotonic(), \"eof\"\n            try:\n                while time.monotonic() - started < seconds:\n                    self.proc.check()\n                    time.sleep(TICK)\n                outcome = \"exited\"\n            finally:\n                ended = time.monotonic()\n                (logs / f\"{name}.launcher.json\").write_text(json.dumps(\n                    {\"outcome\": outcome, \"returncode\": 0 if outcome == \"exited\" else -15,\n                     \"step_started_mono\": started, \"tree_ended_mono\": ended, \"step_seconds\": round(ended - started, 3)}))\n            if name == \"spark_pipeline\":\n                write_result(run_folder)\n            elif name == \"verify\":\n                (run_folder / \"verify.json\").write_text(json.dumps(\n                    {\"mismatch_count\": 0, \"breached_windows\": {\"python\": 1, \"spark\": 1, \"same\": True}}))\n            self.events.log(\"step_ended\", job_id=claim.job_id, attempt=claim.attempt_number, name=name,\n                            outcome=outcome, returncode=0, seconds=round(ended - started, 3))\n        (run_dir / \"attempt.json\").write_text(json.dumps(\n            {\"worker_id\": claim.output_dir.name, \"run_folder\": run_folder.relative_to(run_dir).as_posix()}))\n        manifest = runs.manifest(run_folder)\n        (run_dir / \"manifest.json\").write_text(json.dumps(manifest))\n        self._renew(heartbeat, claim, before=\"acceptance\")\n        return runs.digest(manifest)\n\n\ndef worker_main(batch: \"SyntheticBatch\", name: str):\n    \"\"\"What cmd_worker does, in a thread: the started event, the fault file, serve; no sweep (no processes).\"\"\"\n    def main(proc: ThreadProc):\n        store = batch.job_store()\n        store_id = store.store_id()\n        events = EventLog(batch.events_dir / f\"{name}.jsonl\", \"worker\", store_id=store_id, worker_id=name, pid=proc.pid)\n        events.log(\"started\", topic=batch.topic, code=code_identity(), fault_file=str(batch.fault_file(name)))\n\n        def kill():\n            proc.kill()\n            proc.check()\n\n        worker = Worker(store, SyntheticPipeline(events, proc, batch.settings.snapshot), batch.jobs_root / store_id,\n                        worker_id=name, events=events, fault=faults.FaultFile(batch.fault_file(name), events, kill=kill))\n        consumer = batch.group.join(events, proc)\n        worker.serve(consumer, stop=proc.halted, poll_timeout=0.05, retry_delay=0.1)\n        proc.check()                                                   # killed: no orderly leave\n        consumer.close()\n        events.log(\"stopped\")\n    return main\n\n\ndef reconciler_main(batch: \"SyntheticBatch\"):\n    def main(proc: ThreadProc):\n        store = batch.job_store()\n        events = EventLog(batch.events_dir / f\"reconciler-{proc.pid}.jsonl\", \"reconciler\", store_id=store.store_id(),\n                          pid=proc.pid)\n        events.log(\"started\", topic=batch.topic, code=code_identity())\n        halt = SimpleNamespace(is_set=proc.halted, wait=time.sleep)\n        Reconciler(store, batch.queue.publisher(), events=events,\n                   publication_grace=timedelta(seconds=11)).run(halt, interval=timedelta(seconds=0.2))\n        proc.check()\n        events.log(\"stopped\")\n    return main\n\n\nclass SyntheticBatch(harness.Batch):\n    \"\"\"harness.Batch with SQLite, the Group, ThreadProc processes and no containers.\"\"\"\n    SNAPSHOT, PARAM = \"BEGIN\", \"?\"\n\n    def __init__(self, plan, out, processed_root):\n        super().__init__(plan, out)\n        self.processed_root = processed_root\n        self.db_path = out / \"jobs.sqlite\"\n        self.db = self.env[\"ETF_RISK_JOBS_DB\"] = f\"sqlite:///{self.db_path}\"\n        self.queue = MemoryQueue()\n        self.group = Group(self.queue, self.topic)\n\n    def job_store(self) -> JobStore:\n        return JobStore(None, SQLITE, lease=timedelta(seconds=LEASE_S),\n                        connect=lambda: open_sqlite(self.db_path, check_same_thread=False))\n\n    # No containers\n\n    def services_up(self):\n        self.log.log(\"services_up\", seconds=0.0, others=[])\n\n    def compose(self, *args, timeout=300):\n        return 0.0\n\n    def wait_ready(self, service):\n        return time.monotonic()\n\n    def read_peaks(self, closes=None):\n        for service in (\"mysql\", \"kafka\"):\n            self.peaks.add(service, None, None, closes)\n            self.log.log(\"peaks\", service=service, peak_bytes=None, limit_bytes=None, closes=closes, verdict=\"unknown\")\n        return \"ok\"\n\n    def reference_run(self):\n        \"\"\"The reference's two steps, with launcher records as the real ones are written, and its tables.\"\"\"\n        run_dir = self.out / \"reference\"\n        (run_dir / \"logs\").mkdir(parents=True)\n        for name in (\"windows\", \"spark_pipeline\"):\n            before = started = time.monotonic()\n            if name == \"spark_pipeline\":\n                write_result(run_dir / \"output\" / self.settings.snapshot / \"w\" / \"reference\")\n            time.sleep(0.02)\n            (run_dir / \"logs\" / f\"{name}.launcher.json\").write_text(json.dumps(\n                {\"outcome\": \"exited\", \"returncode\": 0, \"step_started_mono\": started, \"tree_ended_mono\": time.monotonic()}))\n            self.log.log(\"reference_step\", step=name, exit=0, before=before, after=time.monotonic())\n\n    # The CLI and the processes, in this process\n\n    def common_args(self):\n        args = super().common_args()\n        args[args.index(\"--processed-root\") + 1] = str(self.processed_root)\n        return args\n\n    def cli(self, *argv, check=True, timeout=180):\n        if argv[0] == \"create-topic\":                                 # no broker\n            return subprocess.CompletedProcess(argv, 0, \"\", \"\")\n        names = (\"ETF_RISK_JOBS_DB\", \"ETF_RISK_KAFKA_BOOTSTRAP\", \"ETF_RISK_JOBS_TOPIC\")\n        saved = {k: os.environ.get(k) for k in names}\n        os.environ.update({k: self.env[k] for k in names})\n        out, err = io.StringIO(), io.StringIO()\n        try:\n            with redirect_stdout(out), redirect_stderr(err):\n                try:\n                    code = cli.main([*argv, *self.common_args()])\n                except SystemExit as exit_:\n                    code = exit_.code if isinstance(exit_.code, int) else 1\n        finally:\n            for k, v in saved.items():\n                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)\n        done = subprocess.CompletedProcess(argv, code, out.getvalue(), err.getvalue())\n        if check and code != 0:\n            raise RuntimeError(f\"{argv[0]}: exit {code}: {done.stderr.strip()[-500:]}\")\n        return done\n\n    def start(self, name, *argv, extra_env=None):\n        before = time.monotonic()\n        proc = self.procs[name] = ThreadProc(reconciler_main(self) if argv[0] == \"reconciler\" else worker_main(self, name))\n        self._check_start(name, proc, before)\n        return proc\n\n    def publish_again(self, job_id):\n        return self.queue.publisher().publish(job_id)\n\n    # SQLite\n\n    def store(self):\n        store = getattr(self._local, \"store\", None)\n        if store is None:\n            store = self._local.store = self.job_store()\n        return store\n\n    def connect(self, **timeouts):\n        if getattr(self._local, \"unreachable\", False):\n            raise ConnectionRefusedError(\"synthetic: the database cannot be reached\")\n        return open_sqlite(self.db_path, check_same_thread=False)\n\n    def statement(self, sql):\n        return sqlite_statement(sql)\n\n    def other_connections(self):\n        return 0                                                       # SQLite: no server to ask\n\n    def observe(self, job_id):\n        self._local.unreachable = job_id in UNOBSERVED\n        try:\n            return super().observe(job_id)\n        finally:\n            self._local.unreachable = False\n\n\ndef run_batch(tmp_path, monkeypatch):\n    dates = nyse_sessions(\"2024-01-02\", 31)\n    write_snapshot(tmp_path, \"snap\", {\"AAA\": (dates, np.random.default_rng(5).normal(0, 0.01, 30))})\n    processed = tmp_path / \"processed\"\n    settings = harness.Settings(snapshot=\"snap\", poll_s=0.05, phase_delay_s=0.2, phase_timeout_s=15.0)\n    plan = {**harness.make_plan(settings, seed=1), \"jobs\": JOBS}\n    out = tmp_path / \"batch\"\n    batch = SyntheticBatch(plan, out, processed)\n    (out / \"plan.json\").write_text(json.dumps(plan, indent=2))\n    queue = batch.queue\n\n    class QueuePublisher:                                              # what cmd_submit publishes with\n        def __init__(self, *args, **kwargs):\n            self._publisher = queue.publisher()\n\n        def publish(self, job_id):\n            return self._publisher.publish(job_id)\n\n        def close(self):\n            pass\n\n    monkeypatch.setattr(kafka, \"KafkaPublisher\", QueuePublisher)\n    monkeypatch.setattr(harness, \"deadline_seconds\", lambda case, timing, s: LATE.get(case, DEADLINE_S))\n    assert batch.run() == 0\n    return batch, processed\n\n\ndef test_a_synthetic_batch_runs_end_to_end_and_the_collector_reads_it(tmp_path, monkeypatch):\n    batch, processed = run_batch(tmp_path, monkeypatch)\n    assert [p.error for p in batch.procs.values() if p.error] == []\n    events = read_events(batch.out / \"harness.jsonl\")\n    assert harness.events_named(events, \"job_error\") == [] and harness.events_named(events, \"final_error\") == []\n    assert harness.events_named(events, \"batch_ended\")[0][\"stop_reason\"] is None\n    assert len(harness.events_named(events, \"restarted\")) == 6           # W1, W2, W3, W4, W5a and W5b each killed one\n\n    # Arming changed no ownership: the armed worker owned the partition before and after it, its\n    # fault fired, and no assignment moved between the arming and the fault.\n    logs = batch.worker_logs()\n    for armed in harness.events_named(events, \"armed\"):\n        injection = harness.events_named(events, \"injection\", position=armed[\"position\"])[0]\n        assert armed[\"worker\"] == armed[\"owner_after\"] == injection[\"worker\"]\n        assert [e for w in logs for e in logs[w]\n                if e[\"event\"] == \"assigned\" and armed[\"mono\"] < e[\"mono\"] < injection[\"t_inj\"]] == []\n\n    assert crm.main([\"--batch\", str(batch.out), \"--processed-root\", str(processed)]) == 0\n    result = crm.collect(batch.out, processed_root=processed)\n    assert result[\"validity_failed\"] == []\n    rows = {r[\"position\"]: r for r in result[\"rows\"]}\n    assert [rows[p][\"status\"] for p in rows] == [\"made\"] * 9\n    assert [rows[p][\"q1_verdict\"] for p in rows] == [\"ok\"] * 9\n    assert [rows[p][\"timeliness\"] for p in rows] == [\"on time\"] * 4 + [\"late\"] + [\"on time\"] * 3 + [\n        \"deadline not observed\"]\n    assert (rows[5][\"deadline_met\"], rows[9][\"deadline_met\"]) == (\"no\", \"unknown\")\n    assert [rows[p][\"q3a_verdict\"] for p in rows] == [\"reported once\"] * 5 + [\"no matching report\"] + [\n        \"reported once\"] * 3\n    assert [rows[p][\"claims\"] for p in rows] == [\"1\", \"1\", \"2\", \"2\", \"2\", \"1\", \"1\", \"1\", \"1\"]\n    assert [rows[p][\"executions\"] for p in rows] == [1, 1, 1, 2, 2, 1, 1, 1, 1]          # W2's first claim ran nothing\n    assert [rows[p][\"complete_executions\"] for p in rows] == [1, 1, 1, 1, 2, 1, 1, 1, 1]  # W4's first run was complete\n    for p in (2, 3, 4, 5):                                                               # W1-W4: measured\n        assert isinstance(rows[p][\"detection_s\"], float) and isinstance(rows[p][\"rerun_s\"], float)\n        assert isinstance(rows[p][\"finish_s\"], float) and isinstance(rows[p][\"overhead_s\"], float)\n    assert rows[2][\"detection_s\"] >= SESSION_S and min(rows[p][\"detection_s\"] for p in (3, 4, 5)) > 1.0\n    assert (rows[1][\"detection_s\"], rows[6][\"detection_s\"], rows[8][\"finish_s\"] > 0) == (\n        \"n/a: no failure\", \"n/a: after acceptance\", True)\n    assert rows[4][\"wasted_step_s\"] > 0 and rows[5][\"wasted_step_s\"] >= sum(s for _, s in STEPS)\n    assert [rows[p][\"wasted_step_s\"] for p in (1, 2, 3, 6, 7, 8, 9)] == [0.0] * 7\n\n    outcomes = result[\"outcomes\"]\n    assert outcomes[\"overlap\"][\"verdict\"] == \"no overlap\" and outcomes[\"overlap\"][\"steps_without_interval\"] == []\n    assert outcomes[\"q1_not_ok\"] == [] and outcomes[\"invariant_violations\"] == {} and outcomes[\"status_check_exit\"] == 0\n    assert len(outcomes[\"accepted_attempts\"]) == 9 and all(a[\"problems\"] == [] for a in outcomes[\"accepted_attempts\"])\n    assert outcomes[\"q3b_not_matching\"] == [] and outcomes[\"q2b_rows\"] == []\n    assert outcomes[\"nothing_left\"] == {\"processes_left\": False, \"other_connections\": 0}\n    tally = {t[\"case\"]: t for t in result[\"tally\"]}\n    for case in set(JOBS):\n        assert (tally[case][\"made\"], tally[case][\"missed\"], tally[case][\"not_run\"], tally[case][\"unrecorded\"]) == (\n            JOBS.count(case), 0, 0, 0)\n    assert (tally[\"W4\"][\"q2: late\"], tally[\"C0\"][\"q2: deadline not observed\"], tally[\"W5a\"][\"q3a: no matching report\"]) \\\n        == (1, 1, 1)\n    assert sum(t[\"planned\"] for t in tally.values()) == 9 and tally[\"D2\"][\"planned\"] == 0\n"
}
```

## 182. User — 2026-10-24T07:48:16.205Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py (file state is current in your context — no need to Read it back)
```

## 183. Assistant — 2026-10-24T07:49:05.715Z

One fix before running: the synthetic attempt.json put the run id under "worker_id", which is wrong and nothing reads it. Dropping the field:

## 184. Assistant — 2026-10-24T07:49:07.563Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py",
  "old_string": "        (run_dir / \"attempt.json\").write_text(json.dumps(\n            {\"worker_id\": claim.output_dir.name, \"run_folder\": run_folder.relative_to(run_dir).as_posix()}))",
  "new_string": "        (run_dir / \"attempt.json\").write_text(json.dumps({\"run_folder\": run_folder.relative_to(run_dir).as_posix()}))"
}
```

## 185. Assistant — 2026-10-24T07:49:09.671Z

### Tool call: Bash

```
{
  "command": "time (env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_recovery_synthetic.py -x 2>&1 | grep -E '^E |passed|failed|Error' | head -30)",
  "description": "Run the synthetic end-to-end batch test",
  "timeout": 300000
}
```

## 186. User — 2026-10-24T07:49:11.537Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 187. User — 2026-10-24T07:49:33.230Z

### Tool result

```
1 passed, 9 warnings in 18.30s
( env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python -m  )  3.47s user 1.42s system 23% cpu 20.818 total
```

## 188. Assistant — 2026-10-24T07:49:39.814Z

Passed on the first run, in 18 s. A first-time pass deserves a look at the actual output, so I'll rerun with the batch folder kept in the scratchpad:

## 189. Assistant — 2026-10-24T07:49:43.218Z

### Tool call: Bash

```
{
  "command": "S=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic && rm -rf \"$S\" && env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_recovery_synthetic.py --basetemp=\"$S\" 2>&1 | tail -1 && B=$(ls -d \"$S\"/*/batch) && column -s, -t < \"$B/injections.csv\" | cut -c1-230",
  "description": "Rerun keeping the batch folder and show its injections table",
  "timeout": 300000
}
```

## 190. User — 2026-10-24T07:50:02.758Z

### Tool result

```
1 passed, 9 warnings in 17.57s
(eval):1: no such file or directory: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic/test_a_synthetic_batch_runs_en0/batch\n/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic/test_a_synthetic_batch_runs_encurrent/batch/injections.csv
```

## 191. Assistant — 2026-10-24T07:50:16.636Z

### Tool call: Bash

```
{
  "command": "B=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic/test_a_synthetic_batch_runs_en0/batch && column -s, -t < \"$B/injections.csv\" | cut -c1-250; echo; .venv/bin/python - \"$B\" <<'EOF' 2>/dev/null || ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/.venv/bin/python - \"$B\" <<'EOF2'\nEOF\nimport json, sys\nfrom pathlib import Path\nb = Path(sys.argv[1])\nv = json.loads((b / \"validity.json\").read_text())\nprint(\"validity_failed:\", v[\"validity_failed\"])\nprint(\"clock:\", {k: v[\"validity\"][\"clock\"][k] for k in (\"passed\", \"ts_minus_mono_s\", \"processes_on_the_same_clock\")})\nprint(\"identity:\", v[\"validity\"][\"code_identity\"])\nprint(\"fingerprints:\", v[\"validity\"][\"fingerprints_agree\"])\nprint(\"overlap:\", v[\"outcomes\"][\"overlap\"][\"verdict\"], \"steps without interval:\", v[\"outcomes\"][\"overlap\"][\"steps_without_interval\"])\nprint(\"accepted checks:\", [(a[\"job_id\"], a[\"problems\"]) for a in v[\"outcomes\"][\"accepted_attempts\"]])\nprint(\"liveness:\", v[\"outcomes\"][\"liveness\"])\nprint(\"c0 median:\", v[\"c0_median_s\"])\nEOF2",
  "description": "Show the synthetic batch's metrics and validity summary"
}
```

## 192. User — 2026-10-24T07:50:17.752Z

### Tool result

```
position  case  job_id  status  missed   injection  worker           t_inj            reference           deadline_s             detection_s            rerun_s                finish_s               overhead_s  claims  accepted  executions            
1         C0    1       made    submit   20.0       n/a: no failure  n/a: no failure  0.8002104999904986  0.001762103995133657   1                      1                      1                      1           0.0     0         on time               
2         W1    2       made    hook     A          95815.754744333  injection        20.0                0.507600208002259      0.5096105830016313     1.278594792005606      0.5435792710122769     1           1       1         1                     
3         W2    3       made    hook     B          95817.155801458  injection        20.0                2.025873375008814      2.034386417013593      2.792900542001007      2.0485000209955615     2           1       1         1                     
4         W3    4       made    sigkill  A          95820.418226083  injection        20.0                1.8407070829998702     1.8533444170025177     2.612564333001501      2.176830479009368      2           1       2         1                     
5         W4    5       made    hook     B          95823.931812875  injection        2.5                 2.205712915994809      2.2152051250013756     2.978200999990804      2.9676144379991456     2           1       2         2                     
6         W5a   6       made    hook     A          95827.800149666  injection        20.0                n/a: after acceptance  n/a: after acceptance  n/a: after acceptance  n/a: after acceptance  1           1       1         1                     
7         W5b   7       made    hook     B          95829.178558583  injection        20.0                n/a: after acceptance  n/a: after acceptance  n/a: after acceptance  n/a: after acceptance  1           1       1         1                     
8         X1    8       made    publish  A          95829.822480041  injection        20.0                n/a: no failure        n/a: no failure        0.7080592499987688     0.009519311999611091   1           1       1         1                     
9         C0    9       made    submit   20.0       n/a: no failure  n/a: no failure  0.7966862920002313  -0.001762103995133657  1                      1                      1                      1           0.0     0         deadline not observed
```

## 193. Assistant — 2026-10-24T07:50:30.025Z

### Tool call: Bash

```
{
  "command": "B=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic/test_a_synthetic_batch_runs_en0/batch && .venv/bin/python - \"$B\" <<'EOF'\nimport csv, json, sys\nfrom pathlib import Path\nb = Path(sys.argv[1])\nv = json.loads((b / \"validity.json\").read_text())\nprint(\"validity_failed:\", v[\"validity_failed\"])\nprint(\"clock:\", {k: v[\"validity\"][\"clock\"][k] for k in (\"passed\", \"ts_minus_mono_s\", \"processes_on_the_same_clock\")})\nprint(\"identity:\", v[\"validity\"][\"code_identity\"])\nprint(\"fingerprints:\", v[\"validity\"][\"fingerprints_agree\"])\nprint(\"inputs:\", v[\"validity\"][\"inputs_unchanged\"])\nprint(\"overlap:\", v[\"outcomes\"][\"overlap\"][\"verdict\"], \"| without interval:\", v[\"outcomes\"][\"overlap\"][\"steps_without_interval\"])\nprint(\"accepted checks:\", [(a[\"job_id\"], a[\"problems\"]) for a in v[\"outcomes\"][\"accepted_attempts\"]])\nprint(\"liveness:\", v[\"outcomes\"][\"liveness\"])\nprint(\"c0 median:\", round(v[\"c0_median_s\"], 3))\nrows = list(csv.DictReader(open(b / \"injections.csv\")))\nfor r in rows:\n    print(r[\"position\"], r[\"case\"], \"| wasted\", r[\"wasted_step_s\"][:6], \"| fenced\", r[\"fenced_events\"], \"|\", r[\"timeliness\"], r[\"deadline_met\"], \"|\", r[\"q1_verdict\"], \"|\", r[\"q3a_verdict\"])\nh = [json.loads(l) for l in open(b / \"harness.jsonl\")]\nprint(\"harness events:\", sorted({e[\"event\"] for e in h}))\nprint(\"observations:\", [(e[\"job_id\"], e[\"status\"], e.get(\"error\", \"\")[:40]) for e in h if e[\"event\"] == \"observation\"])\nEOF",
  "description": "Summarize the synthetic batch's validity and outcomes"
}
```

## 194. User — 2026-10-24T07:50:30.932Z

### Tool result

```
validity_failed: []
clock: {'passed': True, 'ts_minus_mono_s': 0.0009269579984199083, 'processes_on_the_same_clock': '9 of 9'}
identity: {'passed': True, 'distinct': 1, 'records': 52}
fingerprints: {'passed': True, 'values': [{'n_jobs': 9, 'sum_version': 78, 'n_attempts': 12, 'sum_renewals': 42}, {'n_jobs': 9, 'sum_version': 78, 'n_attempts': 12, 'sum_renewals': 42}, {'n_jobs': 9, 'sum_version': 78, 'n_attempts': 12, 'sum_renewals': 42}]}
inputs: {'passed': True, 'jobs_differing': []}
overlap: no overlap | without interval: []
accepted checks: [(1, []), (2, []), (3, []), (4, []), (5, []), (6, []), (7, []), (8, []), (9, [])]
liveness: {'serve_restarted': 0, 'retry': 0, 'rewound': 0, 'gave_up': 0, 'failed_after_ack': 0, 'consumer_error': 0, 'pass_failed': 0}
c0 median: 0.798
1 C0 | wasted 0.0 | fenced 0 | on time yes | ok | reported once
2 W1 | wasted 0.0 | fenced 0 | on time yes | ok | reported once
3 W2 | wasted 0.0 | fenced 0 | on time yes | ok | reported once
4 W3 | wasted 0.3042 | fenced 0 | on time yes | ok | reported once
5 W4 | wasted 0.7029 | fenced 0 | late no | ok | reported once
6 W5a | wasted 0.0 | fenced 0 | on time yes | ok | no matching report
7 W5b | wasted 0.0 | fenced 0 | on time yes | ok | reported once
8 X1 | wasted 0.0 | fenced 0 | on time yes | ok | reported once
9 C0 | wasted 0.0 | fenced 0 | deadline not observed unknown | ok | reported once
harness events: ['armed', 'batch_ended', 'batch_started', 'deadline', 'final_snapshot', 'injection', 'job_done', 'observation', 'owner', 'peaks', 'process_started', 'published_again', 'quiescent', 'reference_step', 'restarted', 'services_up', 'submitted']
observations: [(1, 'succeeded', ''), (2, 'succeeded', ''), (3, 'succeeded', ''), (4, 'succeeded', ''), (5, 'running', ''), (6, 'succeeded', ''), (7, 'succeeded', ''), (8, 'succeeded', ''), (9, None, 'ConnectionRefusedError: synthetic: the d')]
```

## 195. Assistant — 2026-10-24T07:50:47.836Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -15 > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt; echo exit=$? >> /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Run the full offline test suite in the background",
  "timeout": 1800000,
  "run_in_background": true
}
```

## 196. User — 2026-10-24T07:50:48.629Z

### Tool result

```
Command running in background with ID: be14lqjbv. Output is being written to: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/tasks/be14lqjbv.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need a line it prints before you can go on, such as a server's ready line or port.
```

## 197. Assistant — 2026-10-24T07:51:11.320Z

While the suite runs, I'm working out the smaller experiment with the harness's own estimator:

## 198. Assistant — 2026-10-24T07:51:15.529Z

### Tool call: Bash

```
{
  "command": ".venv/bin/python - <<'EOF'\nfrom dataclasses import replace\nfrom etf_risk.jobs import harness as h\n\ndef batch_s(jobs_per_case, a=h.Assumptions()):\n    plan = h.make_plan(h.Settings(jobs_per_case=jobs_per_case), seed=1)\n    e = h.estimate(plan, a)\n    return e[\"jobs\"], e[\"batch_s\"], e[\"per_case_s\"]\n\nfor n, batches in ((3, 2), (2, 1), (1, 1), (2, 2)):\n    jobs, s, per = batch_s(n)\n    print(f\"{n} per case x {batches} batch(es): {jobs * batches} jobs, {s * batches:.0f} s = {s * batches / 60:.1f} min\")\nprint(\"per case:\", {k: round(v) for k, v in per.items()})\nfor t in (40, 45, 50, 60):\n    a = h.Assumptions(time_to_finish_s=t)\n    jobs, s, _ = batch_s(2, a)\n    print(f\"T={t}: 2 per case, 1 batch: {s:.0f} s = {s / 60:.1f} min\")\na = h.Assumptions(restore_s=40)\nprint(\"restore 40 s, 2 per case:\", round(batch_s(2, a)[1]), \"s\")\nEOF",
  "description": "Estimate smaller designs with the harness estimator"
}
```

## 199. User — 2026-10-24T07:51:17.924Z

### Tool result

```
3 per case x 2 batch(es): 84 jobs, 8778 s = 146.3 min
2 per case x 1 batch(es): 28 jobs, 2986 s = 49.8 min
1 per case x 1 batch(es): 14 jobs, 1583 s = 26.4 min
2 per case x 2 batch(es): 56 jobs, 5972 s = 99.5 min
per case: {'C0': 42, 'W1': 74, 'W2': 120, 'W3': 126, 'W4': 159, 'W5a': 54, 'W5b': 54, 'W6': 126, 'W7': 159, 'K1': 62, 'K2': 118, 'D1': 116, 'D2': 149, 'X1': 44}
T=40: 2 per case, 1 batch: 2986 s = 49.8 min
T=45: 2 per case, 1 batch: 3146 s = 52.4 min
T=50: 2 per case, 1 batch: 3306 s = 55.1 min
T=60: 2 per case, 1 batch: 3626 s = 60.4 min
restore 40 s, 2 per case: 3046 s
```

## 200. Assistant — 2026-10-24T07:51:23.211Z

### Tool call: Bash

```
{
  "command": "cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Show the full suite result"
}
```

## 201. User — 2026-10-24T07:51:23.959Z

### Tool result

```
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests/test_plots.py:20: in <module>
    import matplotlib.pyplot as plt
E   ModuleNotFoundError: No module named 'matplotlib'
=============================== warnings summary ===============================
.venv/lib/python3.12/site-packages/exchange_calendars/exchange_calendar.py:65
  ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/.venv/lib/python3.12/site-packages/exchange_calendars/exchange_calendar.py:65: DeprecationWarning: The 'generic' unit for NumPy timedelta is deprecated, and will raise an error in the future. This includes implicit conversion of bare integers (e.g. `+ 1`). Please use a specific unit instead.
    ONE_HOUR = pd.Timedelta("1h")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR tests/test_plots.py
!!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 1 error in 0.80s
exit=0
```

## 202. Assistant — 2026-10-24T07:51:31.521Z

The full suite did not run. Collection stopped at tests/test_plots.py because matplotlib is not installed in this venv: I synced only the jobs group. Checking which dependency group provides it:

## 203. Assistant — 2026-10-24T07:51:32.730Z

### Tool call: Bash

```
{
  "command": "sed -n '/^\\[dependency-groups\\]/,/^\\[tool/p' pyproject.toml | head -30; grep -n -B2 -A8 '^dependencies' pyproject.toml | head -30",
  "description": "Read the project's dependency groups"
}
```

## 204. User — 2026-10-24T07:51:33.651Z

### Tool result

```
[dependency-groups]
dev = ["pytest>=8"]
download = [
    "yfinance==1.7.0",
]
jobs = [
    "confluent-kafka==2.16.0",  # exact: the job queue's Kafka settings and live tests depend on it
    "psutil==7.2.2",            # exact, as in `measure`: the worker finds and ends a step's processes with it
    "pymysql[rsa]==1.1.1",      # exact: the job table's MySQL adapter and live tests depend on it
]
measure = [
    "psutil==7.2.2",  # exact: peak-memory measurements depend on it
]
plots = [
    "matplotlib==3.11.2",  # exact: the committed figures' rendering depends on it
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
4-description = "Daily-reset leveraged return model on historical stock returns, with a PySpark batch version."
5-requires-python = ">=3.12"
6:dependencies = [
7-    "numpy>=2.0",
8-    "pandas>=2.2,<3",  # PySpark 4.2 warns pandas 3 is not fully supported
9-    "pandas-market-calendars==5.5.0",  # exact: trading-calendar checks depend on its holiday rules
10-    "pyarrow>=18",
11-    "pyspark>=4.0",
12-]
13-
14-[dependency-groups]
```

## 205. Assistant — 2026-10-24T07:51:42.235Z

The full suite needs the plots group (matplotlib), and probably download (yfinance) as well. Installing every dependency group from uv's local cache, without network:

## 206. Assistant — 2026-10-24T07:51:43.244Z

### Tool call: Bash

```
{
  "command": "uv sync --all-groups --offline 2>&1 | tail -8",
  "description": "Install all dependency groups from the local cache",
  "timeout": 300000
}
```

## 207. User — 2026-10-24T07:51:44.251Z

### Tool result

```
 + protobuf==7.36.2
 + pyparsing==3.3.3
 + requests==2.34.2
 + soupsieve==3.0.3
 + typing-extensions==4.16.0
 + urllib3==2.8.0
 + websockets==17.2
 + yfinance==1.7.0
```

## 208. Assistant — 2026-10-24T07:51:54.541Z

### Tool call: Bash

```
{
  "command": "git status --short uv.lock pyproject.toml; PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -15 > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt; echo \"exit=${pipestatus[1]}\" >> /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Rerun the full offline suite in the background",
  "timeout": 1800000,
  "run_in_background": true
}
```

## 209. User — 2026-10-24T07:51:55.230Z

### Tool result

```
Command running in background with ID: buduuarrm. Output is being written to: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/tasks/buduuarrm.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need a line it prints before you can go on, such as a server's ready line or port.
```

## 210. Assistant — 2026-10-24T07:52:13.820Z

While the suite runs, I'll update the outline where it no longer matches the code. First, places that describe the launcher record or acceptance after F:

## 211. Assistant — 2026-10-24T07:52:15.302Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'launcher.json|step_seconds|peak summed|result goes to|accept.{0,30}after F|after F' docs/*.md README.md | head -20",
  "description": "Find docs describing launcher results or acceptance after F"
}
```

## 212. User — 2026-10-24T07:52:16.078Z

### Tool result

```
docs/spec.md:130:| Measurement records | `data/outputs/windows/<snapshot>/<name>/protocol-<UTC time>.json`, `<run id>.log` (the stride experiment: under `data/outputs-experiments/`) | `measure.py` | per run: wall time, in-process phase timings, peak summed RSS in total and per process type, stop-rule status and its limits; since 2026-10-23 also the process types' rule (`process_kinds`), under which a Java process is `spark_jvm` only if its command line runs Spark |
docs/spec.md:479:  median peak summed RSS 1.27 GiB (1.24–1.45 GiB) against a 4.8 GiB stop threshold,
docs/spec.md:854:  - **Each step's process tree,** peak summed RSS over two acceptance runs:
docs/worker-pipeline.md:116:fences itself once F passes without a renewal, and never starts a step or accepts after F.
docs/worker-pipeline.md:287:  - **The step trees** (peak summed RSS, sampled every 0.5 s by the launchers; the range over
```

## 213. Assistant — 2026-10-24T07:52:24.307Z

### Tool call: Bash

```
{
  "command": "sed -n 480,497p docs/recovery-experiments.md; grep -n 'has not run yet\\|not yet run\\|none of it has run\\|None of it has run\\|not yet been run' docs/recovery-experiments.md docs/recovery-sql.md docs/spec.md src/etf_risk/jobs/harness.py analysis/collect_recovery_measurements.py tests/test_jobs_harness.py tests/test_recovery_collector.py",
  "description": "Find statements that the tooling has not run"
}
```

## 214. User — 2026-10-24T07:52:25.072Z

### Tool result

```
### 8.4 Injection method

- **Proposal (P5), implemented and not yet run.** `etf_risk.jobs.faults`: a worker started with
  `ETF_RISK_FAULT_FILE` looks at that file at each fault point, and its `started` event names the
  file. The harness arms one fault for one job by writing the file atomically: a point, and an
  action (SIGKILL to the worker's own process, or a hold until a release file appears, for D2). The
  worker removes the file before it acts, so an arming fires once, and logs `fault_injected`, whose
  `mono` is the injection time. A new fault point, `after_accept_commit`, lies between
  `accept_result`'s return and the `accepted` event and is in `WORKER_FAULT_POINTS`. A file, rather
  than a fault named in the environment as first proposed, lets the harness arm the owner for one
  job without restarting it: a restart would rebalance the group and could move the partition (2.4).
- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside
  cannot hit reliably. `Worker(fault=...)` already calls the fault points, so the hook only wires
  them to the command, and the new point joins the offline tests that crash at every point. The code
  is new, written with Claude Code, with offline tests written and not yet run; mutation checks for it
  are not written. Without it, these six cases would be recorded as not run.

### 8.5 Still open
docs/recovery-experiments.md:15:Code at the author's decision (section 9); none of it has run yet, and no formal experiment was
docs/recovery-experiments.md:93:runs come before the workers start, so that they delay no measured step. Implemented, not yet run:
docs/recovery-experiments.md:103:flag are only reported. Implemented, not yet run: `provenance.code_identity()` for starting
docs/recovery-experiments.md:118:name, start order or `client.id` ordering. Implemented, not yet run: kafka.py writes `assigned`,
docs/recovery-experiments.md:415:  pins them but has not run yet.
docs/recovery-experiments.md:482:- **Proposal (P5), implemented and not yet run.** `etf_risk.jobs.faults`: a worker started with
docs/recovery-experiments.md:494:  is new, written with Claude Code, with offline tests written and not yet run; mutation checks for it
docs/recovery-experiments.md:518:  decision of 2026-10-24. Its offline tests are written; none of it has run:
```

## 215. Assistant — 2026-10-24T07:52:30.444Z

### Tool call: Bash

```
{
  "command": "sed -n 10,20p docs/recovery-experiments.md; echo ...; sed -n 88,122p docs/recovery-experiments.md",
  "description": "Read the outline's status lines in sections 1 and 2"
}
```

## 216. User — 2026-10-24T07:52:31.274Z

### Tool result

```
it ([worker-pipeline.md](worker-pipeline.md), "Status on 2026-10-23"); `e4adc38` later corrected
that report's live job-suite count, which this outline does not use. The SQL cross-check, its
fixture, the frozen expected rows and the run that validated the queries are in
[recovery-sql.md](recovery-sql.md); the author accepted that run as tooling evidence, not as approval
of Part A. Since 2026-10-24 the tooling exists on `feature/recovery-harness`, written with Claude
Code at the author's decision (section 9); none of it has run yet, and no formal experiment was
run._

## 1. Questions and scope

Spec §11 asks:
...

One direct run of the three CLIs per parameter set, under the host execution lock, taken as a
launcher takes it: an exclusive `flock`, the wait until no earlier tree survives, and an entry in
the registry, so that a later launcher waits for the reference run's survivors too. A reference run
then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference
runs come before the workers start, so that they delay no measured step. Implemented, not yet run:
the harness drives each reference step through `etf_risk.jobs.launcher` as the launcher's parent, so
the step gets the same lock, registry, marker and launcher record as a worker's step.

### 2.3 Code identity

Each process records its code identity in its first event when it starts (every worker start, the
reconciler, each `submit`), each step launch records it in `step_started`, and the harness records
it at the start and end of the batch. The identity is `source_digest`, one SHA-256 over the per-file
`source_sha256` map of `provenance.code_state()`, with `uv_lock_sha256`; the commit and the clean
flag are only reported. Implemented, not yet run: `provenance.code_identity()` for starting
processes, and `provenance.source_identity()`, the same two hashes without asking git, for each step
launch. A crashed attempt writes no `attempt.json`, so identity is never read from that file; it is
read only for accepted attempts, to find their run folder (6.2).

### 2.4 Worker startup order and the partition

The topic has one partition, and the group member that owns it gets every delivery.
[kafka.py](../src/etf_risk/jobs/kafka.py) sets no `client.id`, `group.instance.id` or assignment
strategy, so with two live members the owner after a rebalance is not fixed; M2's first acceptance
run failed partly on "a standby that could win the partition before worker A did". Order per batch:
`services ready`, `init-db` and `create-topic`; the reference runs; the reconciler; worker A, then a
wait for its assignment event; worker B, then a wait for the rebalance its join causes; the first
job. The harness identifies the owner from the assignment events alone, before each case and after
each rebalance, and injects into the worker that claimed the job, never into a worker chosen by
name, start order or `client.id` ordering. Implemented, not yet run: kafka.py writes `assigned`,
`revoked` and `lost` events from its rebalance callbacks, and the harness reads the owner only after
a started worker's first `assigned` event, so a stale assignment is never taken for the owner.

**Restart rule.** A killed worker starts again only once its job has finished (read from the
```

## 217. Assistant — 2026-10-24T07:53:03.512Z

Making the D2 detection rule consistent with the fix: when the hold ends after F there is no `retry`, and the detection event is the `fenced` event at acceptance.

## 218. Assistant — 2026-10-24T07:53:12.337Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"analysis/collect_recovery_measurements.py\")\ns = p.read_text()\nold = '''        else:                                                     # D2\n            detection = b.first_after(named(events, \"retry\", operation=\"accept_result\"), t_inj)'''\nnew = '''        else:                                                     # D2: a retried acceptance, or none after F\n            detection = b.first_after(named(events, \"retry\", operation=\"accept_result\")\n                                      + named(events, \"fenced\", during=\"acceptance\"), t_inj)'''\nassert s.count(old) == 1\ns = s.replace(old, new)\nold = '''Tested with tests/test_recovery_collector.py on synthetic batch folders; no real batch exists.'''\nnew = '''Tested with tests/test_recovery_collector.py on synthetic batch folders, and on the batch that\ntests/test_recovery_synthetic.py runs end to end without services; no real batch exists.'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\n\np = Path(\"tests/test_recovery_collector.py\")\ns = p.read_text()\ns += '''\n\ndef test_d2_is_detected_by_its_retried_acceptance_or_by_no_acceptance_after_f(batch, tmp_path):\n    \"\"\"The K2 position becomes a D2 whose hold ended after F: no retry, a fenced event at acceptance.\"\"\"\n    plan = json.loads((batch / \"plan.json\").read_text())\n    (batch / \"plan.json\").write_text(json.dumps({**plan, \"jobs\": [\"C0\", \"W3\", \"W5a\", \"D2\"]}))\n    edit_harness(batch, lambda e: None if e[\"event\"] == \"not_run\" else e)\n    with open(batch / \"harness.jsonl\", \"a\") as f:\n        for e in ({\"event\": \"deadline\", \"position\": 4, \"job_id\": 4, \"case\": \"D2\", \"reference\": \"restored\",\n                   \"reference_mono\": 1420.0, \"deadline_s\": 140, \"deadline_mono\": 1560.0, \"t_submit\": 1350.0},\n                  {\"event\": \"injection\", \"position\": 4, \"job_id\": 4, \"case\": \"D2\", \"missed\": None,\n                   \"kind\": \"hold+service_stop\", \"worker\": \"A\", \"t_inj\": 1400.0, \"restored\": 1420.0}):\n            f.write(json.dumps(e) + \"\\\\n\")\n    with open(batch / \"events\" / \"A.jsonl\", \"a\") as f:\n        for e in ({\"event\": \"claimed\", \"job_id\": 4, \"attempt\": 1, \"run_id\": \"job-4-attempt-1\", \"mono\": 1351.0},\n                  {\"event\": \"fenced\", \"job_id\": 4, \"attempt\": 1, \"during\": \"acceptance\", \"mono\": 1430.0}):\n            f.write(json.dumps(e) + \"\\\\n\")\n    with open(batch / \"events\" / \"B.jsonl\", \"a\") as f:\n        f.write(json.dumps({\"event\": \"claimed\", \"job_id\": 4, \"attempt\": 2, \"run_id\": \"job-4-attempt-2\",\n                            \"mono\": 1500.0}) + \"\\\\n\")\n    d2 = {r[\"position\"]: r for r in crm.collect(batch, processed_root=tmp_path / \"processed\")[\"rows\"]}[4]\n    assert (d2[\"status\"], d2[\"detection_s\"], d2[\"rerun_s\"]) == (\"made\", 30.0, 100.0)\n'''\np.write_text(s)\nEOF\n.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_recovery_collector.py 2>&1 | tail -1",
  "description": "Detect D2 by a fenced acceptance too, and test it"
}
```

## 219. User — 2026-10-24T07:53:15.568Z

### Tool result

```
11 passed, 89 warnings in 1.45s
```

## 220. Assistant — 2026-10-24T07:53:19.708Z

Collector: 11 passed. Now the outline's text, edited in place with exact replacements:

## 221. Assistant — 2026-10-24T07:53:34.901Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nreps = [\n(\"\"\"Since 2026-10-24 the tooling exists on `feature/recovery-harness`, written with Claude\nCode at the author's decision (section 9); none of it has run yet, and no formal experiment was\nrun._\"\"\",\n\"\"\"Since 2026-10-24 the tooling exists on `feature/recovery-harness`, written with Claude\nCode at the author's decision (section 9). Its offline tests passed on 2026-10-24, one of them a\nsynthetic batch run end to end without services; none of it has run against the services, and no\nformal experiment was run._\"\"\"),\n(\"\"\"runs come before the workers start, so that they delay no measured step. Implemented, not yet run:\nthe harness drives each reference step through `etf_risk.jobs.launcher` as the launcher's parent, so\nthe step gets the same lock, registry, marker and launcher record as a worker's step.\"\"\",\n\"\"\"runs come before the workers start, so that they delay no measured step. Implemented, not yet run\n(the synthetic batch replaces it): the harness drives each reference step through\n`etf_risk.jobs.launcher` as the launcher's parent, so the step gets the same lock, registry, marker\nand launcher record as a worker's step.\"\"\"),\n(\"\"\"flag are only reported. Implemented, not yet run: `provenance.code_identity()` for starting\nprocesses,\"\"\",\n\"\"\"flag are only reported. Implemented and tested offline, not yet run against the services:\n`provenance.code_identity()` for starting processes,\"\"\"),\n(\"\"\"name, start order or `client.id` ordering. Implemented, not yet run: kafka.py writes `assigned`,\n`revoked` and `lost` events from its rebalance callbacks, and the harness reads the owner only after\na started worker's first `assigned` event, so a stale assignment is never taken for the owner.\"\"\",\n\"\"\"name, start order or `client.id` ordering. Implemented: kafka.py writes `assigned`, `revoked` and\n`lost` events from its rebalance callbacks, and the harness reads the owner only after a started\nworker's first `assigned` event, so a stale assignment is never taken for the owner. The offline\ntests and the synthetic batch exercise the events and the harness's reading of them with a\nstand-in group; the live Kafka test has not run.\"\"\"),\n(\"\"\"| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL, after a peak reading | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`) and the job runs again after its lease expires |\"\"\",\n\"\"\"| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL, after a peak reading | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`), or, if the hold ends at or after F, makes no acceptance call (`fenced`, during acceptance); either way the job runs again after its lease expires |\"\"\"),\n(\"\"\"| D2 | `retry` of `accept_result`; then `accepted`, or else `failed_after_ack` and `requeued` | as D1 | as D1 |\"\"\",\n\"\"\"| D2 | `retry` of `accept_result`, or `fenced` during acceptance if the hold outlasted F; then `accepted`, or else `failed_after_ack` or that `fenced`, and `requeued` | as D1 | as D1 |\"\"\"),\n(\"\"\"([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step\ntimes once it records them (section 9).\"\"\",\n\"\"\"([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step\ntimes (`step_started_mono` and `tree_ended_mono` in its record).\"\"\"),\n(\"\"\"  `unknown`, never `no overlap`. Intervals are compared in monotonic time once the launcher records\n  it; at `6d8a232` it records UTC times only, and their comparison holds only with a passed clock\n  check.\"\"\",\n\"\"\"  `unknown`, never `no overlap`. Intervals are compared in monotonic time: the launcher records\n  `step_started_mono` and `tree_ended_mono`. A record without them, such as one written at\n  `6d8a232`, which recorded UTC times only, leaves its interval missing; UTC times are never\n  compared.\"\"\"),\n(\"\"\"  paths. The figures come from the estimator's formulas, worked out by hand; tests/test_jobs_harness.py\n  pins them but has not run yet.\"\"\",\n\"\"\"  paths. The figures come from the estimator's formulas, worked out by hand; tests/test_jobs_harness.py\n  pins them and passed on 2026-10-24.\"\"\"),\n(\"\"\"- **Proposal (P5), implemented and not yet run.**\"\"\",\n\"\"\"- **Proposal (P5), implemented and tested offline.**\"\"\"),\n(\"\"\"  them to the command, and the new point joins the offline tests that crash at every point. The code\n  is new, written with Claude Code, with offline tests written and not yet run; mutation checks for it\n  are not written. Without it, these six cases would be recorded as not run.\"\"\",\n\"\"\"  them to the command, and the new point joins the offline tests that crash at every point. The code\n  is new, written with Claude Code. Its offline tests passed on 2026-10-24: arming a running worker,\n  and a hold released after F, which ends without an acceptance call (tests/test_jobs_worker.py), and\n  the five kill hooks in the synthetic batch. Mutation checks for it are not written. Without it,\n  these six cases would be recorded as not run.\"\"\"),\n(\"\"\"isolated check; monotonic step times in the launcher records, which none of the four reviews asked\nfor and without which the overlap check compares UTC times (6.5); and the branches:\"\"\",\n\"\"\"isolated check; and the branches:\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:90]\n    s = s.replace(old, new)\np.write_text(s)\nprint(\"ok\")\nEOF",
  "description": "Update the outline's status, D2 path, clock and overlap text"
}
```

## 222. User — 2026-10-24T07:53:35.785Z

### Tool result

```
ok
```

## 223. Assistant — 2026-10-24T07:53:47.333Z

Now the module docstrings, where they describe test status:

## 224. Assistant — 2026-10-24T07:53:52.119Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"src/etf_risk/jobs/harness.py\")\ns = p.read_text()\nold = '''No batch has run: Part A is not approved, and no formal experiment has been run. The offline\nparts are tested with tests/test_jobs_harness.py.'''\nnew = '''No batch has run against the services: Part A is not approved, and no formal experiment has been\nrun. The offline parts are tested with tests/test_jobs_harness.py, and a synthetic batch, with\nSQLite and in-process stand-ins for the services, runs end to end in\ntests/test_recovery_synthetic.py.'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\np = Path(\"src/etf_risk/jobs/worker.py\")\ns = p.read_text()\nold = '''AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py,\ntests/test_jobs_queue.py and tests/test_jobs_kafka.py, on SQLite and on MySQL 8.4.13.'''\nnew = '''AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py,\ntests/test_jobs_queue.py and tests/test_jobs_kafka.py, on SQLite and on MySQL 8.4.13; the\nacceptance-deadline check and after_accept_commit (2026-10-24) so far on SQLite only.'''\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\ngit diff --stat",
  "description": "Update harness and worker docstrings on test status"
}
```

## 225. User — 2026-10-24T07:53:53.235Z

### Tool result

```
 docs/spec.md                  |   6 ++-
 src/etf_risk/jobs/cli.py      |  16 ++++--
 src/etf_risk/jobs/kafka.py    |  22 ++++++++-
 src/etf_risk/jobs/launcher.py |  11 +++--
 src/etf_risk/jobs/pipeline.py |   5 +-
 src/etf_risk/jobs/worker.py   |  19 +++++++-
 src/etf_risk/provenance.py    |  28 +++++++++++
 tests/test_jobs_cli.py        |   7 ++-
 tests/test_jobs_kafka.py      |  39 ++++++++++++++-
 tests/test_jobs_launcher.py   |  19 ++++++++
 tests/test_jobs_pipeline.py   |  10 ++++
 tests/test_jobs_queue.py      |   2 +-
 tests/test_jobs_worker.py     | 110 +++++++++++++++++++++++++++++++++++++++++-
 tests/test_provenance.py      |  16 ++++++
 14 files changed, 290 insertions(+), 20 deletions(-)
```

## 226. Assistant — 2026-10-24T07:54:15.208Z

While the suite finishes, rereading the harness parts I changed:

## 227. Assistant — 2026-10-24T07:54:16.980Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'def (arm_fault|other_connections|connect|statement|observe|crosscheck|q0|quiesce)|SNAPSHOT|PARAM|closing\\(' src/etf_risk/jobs/harness.py && sed -n \"$(grep -n 'def quiesce' src/etf_risk/jobs/harness.py | cut -d: -f1),+20p\" src/etf_risk/jobs/harness.py",
  "description": "Review the refactored harness database hooks and quiesce"
}
```

## 228. User — 2026-10-24T07:54:18.078Z

### Tool result

```
286:def crosscheck_statements(text: str | None = None) -> list[tuple[str, str]]:
506:    SNAPSHOT = "START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY"     # 4.3 and 4.5
507:    PARAM = "%s"                                                            # the driver's placeholder
509:    def connect(self, **timeouts):
514:    def statement(self, sql: str) -> str:
518:    def other_connections(self) -> int:
522:            with closing(conn.cursor()) as cursor:
548:    def observe(self, job_id: int) -> dict:
556:                with closing(conn.cursor()) as cursor:
558:                    cursor.execute(self.SNAPSHOT)
561:                                   + self.PARAM, (job_id,))
633:    def arm_fault(self, position: int, case: str, owner: str) -> tuple[str, Path | None]:
863:    def quiesce(self) -> dict:
884:    def crosscheck(self) -> dict:
890:        values = ", ".join([self.PARAM] * 6)
894:            with closing(conn.cursor()) as cursor:
904:                cursor.execute(self.SNAPSHOT)
922:    def q0(self) -> dict:
926:            with closing(conn.cursor()) as cursor:
    def quiesce(self) -> dict:
        """4.4: SIGKILL every writer, then wait until no attempt's process and no other client
        connection is left."""
        for proc in self.procs.values():
            if proc.poll() is None:
                proc.kill()                                  # SIGKILL
        for proc in self.procs.values():
            proc.wait(timeout=30)
        try:                                                  # each launcher ends its tree on EOF
            self.wait_for(lambda: not self._marked(), self.timing.watchdog_tick + self.timing.kill_grace + 10,
                          "the attempts' processes to end")
            processes_left = False
        except PhaseMissed:
            processes_left = True
        record = {"processes_left": processes_left, "other_connections": self.other_connections()}
        self.log.log("quiescent", **record)
        return record

    def _marked(self) -> bool:
        return any(v.startswith(f"{self.store_id}:") for v in processes.marked_processes())
```

## 229. Assistant — 2026-10-24T07:54:27.693Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^\\[tool\\.(ruff|flake8|black|isort|mypy)' pyproject.toml; ls .venv/bin | grep -E '^(ruff|flake8|pyflakes)$' ; .venv/bin/python -m pyflakes --version 2>/dev/null | head -1; uvx --offline ruff --version 2>/dev/null | head -1",
  "description": "Check for a configured linter"
}
```

## 230. User — 2026-10-24T07:54:29.287Z

### Tool result

```
ruff 0.17.1
```

## 231. Assistant — 2026-10-24T07:54:35.345Z

### Tool call: Bash

```
{
  "command": "uvx --offline ruff check --select F,E9 --no-cache src/etf_risk/jobs/harness.py src/etf_risk/jobs/worker.py src/etf_risk/jobs/launcher.py src/etf_risk/jobs/faults.py analysis/collect_recovery_measurements.py tests/test_recovery_synthetic.py tests/test_recovery_sql.py tests/recovery_sqlite.py tests/test_jobs_harness.py tests/test_jobs_worker.py tests/test_recovery_collector.py tests/test_jobs_launcher.py 2>&1 | tail -15",
  "description": "Check changed files for unused names and syntax errors"
}
```

## 232. User — 2026-10-24T07:54:37.878Z

### Tool result

```
12 | """
13 | import json
   |        ^^^^
14 | import time
15 | from pathlib import Path
   |
help: Remove unused import: `json`
   |
12 | """
   - import json
13 | import time
   |

Found 1 error.
[*] 1 fixable with `--fix`.
```

## 233. Assistant — 2026-10-24T07:54:43.889Z

### Tool call: Bash

```
{
  "command": "git show HEAD:tests/test_jobs_worker.py | grep -n 'json' | head -5",
  "description": "Check whether the unused import predates my change"
}
```

## 234. User — 2026-10-24T07:54:45.811Z

### Tool result

```
13:import json
161:    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # complete, never accepted
195:    assert (a_dir / "steps.log").read_text() == "step 1\n" and not (a_dir / "result.json").exists()
223:    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # A's folder stays, unreferenced
```

## 235. Assistant — 2026-10-24T07:55:00.698Z

That unused import was already there at HEAD, so I left it; the new code lints clean. Now the outline's tooling and history text. The test counts go in once the suite finishes:

## 236. Assistant — 2026-10-24T07:55:01.837Z

### Tool call: Bash

```
{
  "command": "sed -n \"$(grep -n '^- \\*\\*Tooling\\*\\*' docs/recovery-experiments.md | cut -d: -f1),+16p\" docs/recovery-experiments.md",
  "description": "Read the outline's current tooling list"
}
```

## 237. User — 2026-10-24T07:55:02.644Z

### Tool result

```
- **Tooling**, uncommitted on `feature/recovery-harness`, written with Claude Code at the author's
  decision of 2026-10-24. Its offline tests are written; none of it has run:
  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs
    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)
    byte for byte (a test checks it);
  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);
  - assignment events in `kafka.py` (2.4);
  - code identity at launch, in `provenance.py`, `cli.py` and `pipeline.py` (2.3);
  - the fault hook, `faults.py`, wired in `cli.py`, and the fault point `after_accept_commit` in
    `worker.py` (8.4).
- **Not done:** monotonic step times in the launcher records (8.5), mutation checks for the new
  code, and any run of it.
- **Authorship.** Spec §11: the job code is written with Claude Code. At the author's decision of
  2026-10-24, Claude Code also writes the recovery experiments' tooling listed above, and each new
  module says so. The items in 1.1, and the experiments' decisions, runs and answers, are the
  author's; everything else here is Claude Code's proposal. The queries of
  [recovery-sql.md](recovery-sql.md) stay marked as drafted with Claude Code.
```

## 238. Assistant — 2026-10-24T07:55:39.882Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"tests/test_recovery_synthetic.py\")\ns = p.read_text()\nreps = [\n('''LEASE_S, MARGIN_S = 2.0, 0.5            # the synthetic lease; F = m0 + LEASE_S - MARGIN_S\nSESSION_S = 0.5                         # a dead member loses the partition this long after its death\nSTEPS = ((\"windows\", 0.05), (\"spark_pipeline\", 0.6), (\"verify\", 0.05))''',\n'''LEASE_S, MARGIN_S = 3.0, 0.5            # the synthetic lease; F = m0 + LEASE_S - MARGIN_S\nSESSION_S = 0.5                         # a dead member loses the partition this long after its death\nSTEPS = ((\"windows\", 0.05), (\"spark_pipeline\", 1.0), (\"verify\", 0.05))     # mid-step: 0.2 s into 1 s'''),\n('''LATE = {\"W4\": 2.5}                      # seconds; its next run starts after the 2 s lease''',\n'''LATE = {\"W4\": 3.0}                      # seconds: it cannot succeed before the lease (3 s) and a run (1.1 s)'''),\n('''table, and the collector (analysis/collect_recovery_measurements.py) then reads the batch folder''',\n'''table, and the collector (analysis/collect_recovery_measurements.py) then reads the batch folder'''),\n('''SIGKILL lands within a tick); MySQL (SQLite); the containers (no peaks, no restarts). The\nlease is 2 s and a dead member loses the partition after 0.5 s.''',\n'''SIGKILL lands within a tick); MySQL (SQLite); the containers (no peaks, no restarts). The\nlease is 3 s and a dead member loses the partition after 0.5 s.'''),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:60]\n    s = s.replace(old, new)\np.write_text(s)\nEOF\ngrep -n \"lease is\\|where a SIGKILL\" tests/test_recovery_synthetic.py | head",
  "description": "Widen the synthetic test's timing margins"
}
```

## 239. User — 2026-10-24T07:55:41.835Z

### Tool result

```
12:where a SIGKILL lands within a tick); MySQL (SQLite); the containers (no peaks, no restarts). The
13:lease is 3 s and a dead member loses the partition after 0.5 s.
```

## 240. Assistant — 2026-10-24T07:55:51.102Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'planned|not run|missed' docs/recovery-experiments.md | sed -n 1,20p",
  "description": "Find where the outline lists injection counts"
}
```

## 241. User — 2026-10-24T07:55:51.976Z

### Tool result

```
124:stand-in group; the live Kafka test has not run.
136:(4.4), and the injections not yet made are recorded as not run.
164:All 14 cases are kept; a case without an injection method is recorded as not run, never dropped.
212:which nothing has measured, out of their deadlines. A job whose injection missed its phase gets C0's
226:`deadline not observed` is an explicit unknown, counted as neither met nor missed. The final
320:injection landed in its phase, and planned injections were made or recorded as not run; one code
378:queries the store does not run. On 2026-10-23 the queries and a fixture of 21 job ids ran once in a
436:  recoveries take 50–65 s instead of 20–29 s on M2's clock. Risk: the default clock has not run
502:  these six cases would be recorded as not run.
520:- **Nothing is dropped.** Every injection (misses and those not run included), every batch (invalid
```

## 242. Assistant — 2026-10-24T07:55:57.198Z

### Tool call: Bash

```
{
  "command": "sed -n 316,324p docs/recovery-experiments.md; sed -n 518,524p docs/recovery-experiments.md",
  "description": "Read the validity and nothing-dropped passages"
}
```

## 243. User — 2026-10-24T07:56:00.381Z

### Tool result

```
### 6.1 Validity

Validity decides what counts, like the acceptance criteria of the earlier experiments: each
injection landed in its phase, and planned injections were made or recorded as not run; one code
identity across the batch (2.3); input checksums unchanged; the clock checks passed (4.1); the three
fingerprints equal (4.5); the machine-state rules held (8.3). A batch that fails validity does not
count toward the answers, but its records and outcomes stay visible (section 9).

  Q0–Q3b as CSV, the table of section 5 with one row per injection, the per-case tally, and
  `cleanup`'s listing.
- **Nothing is dropped.** Every injection (misses and those not run included), every batch (invalid
  ones included) and every verdict (failed outcomes and unknowns included) stays in the records; the
  tally lists all 14 cases and every verdict value, with zeros.
- **Tooling**, uncommitted on `feature/recovery-harness`, written with Claude Code at the author's
  decision of 2026-10-24. Its offline tests are written; none of it has run:
```

## 244. Assistant — 2026-10-24T07:56:10.165Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nold = \"\"\"- **Nothing is dropped.** Every injection (misses and those not run included), every batch (invalid\n  ones included) and every verdict (failed outcomes and unknowns included) stays in the records; the\n  tally lists all 14 cases and every verdict value, with zeros.\"\"\"\nnew = \"\"\"- **Nothing is dropped.** Every injection (misses, those not run, and those whose harness record is\n  incomplete, counted apart as unrecorded, included), every batch (invalid ones included) and every\n  verdict (failed outcomes and unknowns included) stays in the records; the tally lists all 14 cases\n  and every verdict value, with zeros.\"\"\"\nassert s.count(old) == 1\ns = s.replace(old, new)\np.write_text(s)\nEOF\necho done",
  "description": "Note unrecorded injections in the outline's records rule"
}
```

## 245. User — 2026-10-24T07:56:11.128Z

### Tool result

```
done
```

## 246. Assistant — 2026-10-24T07:56:16.369Z

### Tool call: Bash

```
{
  "command": "pgrep -fl \"pytest -q -p no:cacheprovider tests\" | head -3 || echo \"not running\"",
  "description": "Check whether the full suite is still running"
}
```

## 247. User — 2026-10-24T07:56:17.190Z

### Tool result

```
79791 /bin/zsh -c source ~/.claude/shell-snapshots/snapshot-zsh-1792784314761-3973u4.sh 2>/dev/null || true && setopt NO_EXTENDED_GLOB NO_BARE_GLOB_QUAL 2>/dev/null || true && { \builtin unalias -- 'unsetenv'; \builtin unset -f -- 'unsetenv'; } >/dev/null 2>&1 || true && eval 'git status --short uv.lock pyproject.toml; PATH="$PWD/.venv/bin:$PATH" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider tests 2>&1 | tail -15 > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt; echo "exit=${pipestatus[1]}" >> /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt' < /dev/null && pwd -P >| /tmp/claude-cb49-cwd
79800 python -m pytest -q -p no:cacheprovider tests
```

## 248. Assistant — 2026-10-24T07:56:32.944Z

### Tool call: Bash

```
{
  "command": "git diff --stat -- src analysis docs tests | tail -3; git status --short | grep '^??'",
  "description": "Summarize tracked and new files changed in the worktree"
}
```

## 249. User — 2026-10-24T07:56:33.844Z

### Tool result

```
 tests/test_jobs_worker.py     | 110 +++++++++++++++++++++++++++++++++++++++++-
 tests/test_provenance.py      |  16 ++++++
 14 files changed, 290 insertions(+), 20 deletions(-)
?? analysis/collect_recovery_measurements.py
?? docs/recovery-experiments.md
?? docs/recovery-sql.md
?? src/etf_risk/jobs/crosscheck.sql
?? src/etf_risk/jobs/faults.py
?? src/etf_risk/jobs/harness.py
?? tests/recovery_sqlite.py
?? tests/test_jobs_faults.py
?? tests/test_jobs_harness.py
?? tests/test_recovery_collector.py
?? tests/test_recovery_sql.py
?? tests/test_recovery_synthetic.py
```

## 250. Assistant — 2026-10-24T07:56:42.042Z

### Tool call: Bash

```
{
  "command": "shasum -a 256 docs/recovery-sql.md src/etf_risk/jobs/crosscheck.sql | cut -c1-16; ls -la -T docs/recovery-sql.md | awk '{print $6, $7, $8, $9}'",
  "description": "Confirm the frozen SQL files were not modified this session"
}
```

## 251. User — 2026-10-24T07:56:42.985Z

### Tool result

```
f305bfc94cba3c96
52ea17a4f4f65757
Oct 24 00:39:06 2026
```

## 252. Assistant — 2026-10-24T07:56:48.627Z

### Tool call: Bash

```
{
  "command": "pgrep -f \"python -m pytest -q -p no:cacheprovider tests\" >/dev/null && echo running || cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Check once whether the full suite has finished"
}
```

## 253. User — 2026-10-24T07:56:49.401Z

### Tool result

```
running
```

## 254. Assistant — 2026-10-24T07:57:03.954Z

### Tool call: Bash

```
{
  "command": "grep -c \"def test_\" tests/test_*.py | awk -F: '{s+=$2} END {print s \" test functions in tests/\"}'; grep -l \"pytest.mark.spark\\|@spark\\|spark)\" tests/test_*.py | head -20",
  "description": "Count test functions and find Spark-marked test files"
}
```

## 255. User — 2026-10-24T07:57:04.930Z

### Tool result

```
429 test functions in tests/
tests/test_caching_collector.py
tests/test_caching_options.py
tests/test_baseline_collector.py
tests/test_jobs_live_pipeline.py
tests/test_measure.py
tests/test_pandas_pipeline.py
tests/test_partition_options.py
tests/test_jobs_worker_spark.py
tests/test_plots.py
tests/test_verify.py
tests/test_spark_equivalence.py
```

## 256. Assistant — 2026-10-24T07:57:11.642Z

### Tool call: Bash

```
{
  "command": "pgrep -f \"python -m pytest -q -p no:cacheprovider tests\" >/dev/null && echo running || cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Check once more whether the full suite has finished"
}
```

## 257. User — 2026-10-24T07:57:12.359Z

### Tool result

```
running
```

## 258. Assistant — 2026-10-24T07:57:26.119Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py",
  "offset": 1,
  "limit": 60
}
```

## 259. User — 2026-10-24T07:57:26.455Z

### Tool result

```
1	"""A synthetic batch of the recovery experiments, end to end, with no services: the harness's own
2	Batch.run (etf_risk.jobs.harness) drives workers and a reconciler in this process, on a SQLite job
3	table, and the collector (analysis/collect_recovery_measurements.py) then reads the batch folder
4	as it would read a real one. No formal experiment: nothing here measures the job system.
5	
6	Real code: the harness's run, run_job, after_job, arming, phases, Tracker, observation, cross-check
7	and final snapshot; the CLI's init-db, submit, status --check and export, run in process; Worker,
8	FaultFile, Reconciler and the job store; the frozen crosscheck.sql, translated for SQLite
9	(tests/recovery_sqlite.py); the collector.
10	Stand-ins: Kafka (Group: one partition in memory, with the assignment events kafka.log_assignment
11	writes); the Spark steps and their launchers (SyntheticPipeline); the job processes (ThreadProc,
12	where a SIGKILL lands within a tick); MySQL (SQLite); the containers (no peaks, no restarts). The
13	lease is 3 s and a dead member loses the partition after 0.5 s.
14	
15	Covered: C0 twice, the second with a deadline observation that fails on purpose; W1, W2, W3; W4,
16	whose deadline is set short so that it completes late; W5a, W5b and X1. Not covered: W6 and W7
17	(SIGSTOP of processes), K1 and K2 (Kafka down), D1 and D2 (MySQL down), which need the services.
18	
19	AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
20	"""
21	import importlib.util
22	import io
23	import itertools
24	import json
25	import os
26	import signal
27	import subprocess
28	import threading
29	import time
30	import traceback
31	from contextlib import redirect_stderr, redirect_stdout
32	from datetime import date, timedelta
33	from types import SimpleNamespace
34	
35	import numpy as np
36	import pyarrow as pa
37	import pyarrow.parquet as pq
38	from conftest import nyse_sessions, write_snapshot
39	from recovery_sqlite import REPO, sqlite_statement
40	
41	from etf_risk import runs
42	from etf_risk.jobs import cli, faults, harness, kafka
43	from etf_risk.jobs.events import EventLog, read_events
44	from etf_risk.jobs.queue import Delivery
45	from etf_risk.jobs.reconciler import Reconciler
46	from etf_risk.jobs.simulated import MemoryQueue, SimulatedCrash
47	from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite
48	from etf_risk.jobs.worker import Fenced, Worker
49	from etf_risk.provenance import code_identity, source_identity
50	
51	spec = importlib.util.spec_from_file_location("collect_recovery_measurements",
52	                                              REPO / "analysis" / "collect_recovery_measurements.py")
53	crm = importlib.util.module_from_spec(spec)
54	spec.loader.exec_module(crm)
55	
56	LEASE_S, MARGIN_S = 3.0, 0.5            # the synthetic lease; F = m0 + LEASE_S - MARGIN_S
57	SESSION_S = 0.5                         # a dead member loses the partition this long after its death
58	STEPS = (("windows", 0.05), ("spark_pipeline", 1.0), ("verify", 0.05))     # mid-step: 0.2 s into 1 s
59	TICK = 0.01
60	JOBS = ["C0", "W1", "W2", "W3", "W4", "W5a", "W5b", "X1", "C0"]     # job ids 1-9, in this order
```

## 260. Assistant — 2026-10-24T07:57:33.245Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py",
  "old_string": "            for k, v in saved.items():\n                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)",
  "new_string": "            for k, v in saved.items():\n                if v is None:\n                    os.environ.pop(k, None)\n                else:\n                    os.environ[k] = v"
}
```

## 261. Assistant — 2026-10-24T07:57:34.763Z

### Tool call: Bash

```
{
  "command": "pgrep -f \"python -m pytest -q -p no:cacheprovider tests\" >/dev/null && echo running || cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Check whether the full suite has finished"
}
```

## 262. User — 2026-10-24T07:57:36.563Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py has been updated successfully.
```

## 263. User — 2026-10-24T07:57:37.069Z

### Tool result

```
running
```

## 264. Assistant — 2026-10-24T07:57:40.990Z

Still waiting on the full suite (Spark tests make it the slow part). Meanwhile I'm reviewing the remaining synthetic-test code.

## 265. Assistant — 2026-10-24T07:57:42.116Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_synthetic.py",
  "offset": 255,
  "limit": 60
}
```

## 266. User — 2026-10-24T07:57:42.469Z

### Tool result

```
255	                write_result(run_folder)
256	            elif name == "verify":
257	                (run_folder / "verify.json").write_text(json.dumps(
258	                    {"mismatch_count": 0, "breached_windows": {"python": 1, "spark": 1, "same": True}}))
259	            self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number, name=name,
260	                            outcome=outcome, returncode=0, seconds=round(ended - started, 3))
261	        (run_dir / "attempt.json").write_text(json.dumps({"run_folder": run_folder.relative_to(run_dir).as_posix()}))
262	        manifest = runs.manifest(run_folder)
263	        (run_dir / "manifest.json").write_text(json.dumps(manifest))
264	        self._renew(heartbeat, claim, before="acceptance")
265	        return runs.digest(manifest)
266	
267	
268	def worker_main(batch: "SyntheticBatch", name: str):
269	    """What cmd_worker does, in a thread: the started event, the fault file, serve; no sweep (no processes)."""
270	    def main(proc: ThreadProc):
271	        store = batch.job_store()
272	        store_id = store.store_id()
273	        events = EventLog(batch.events_dir / f"{name}.jsonl", "worker", store_id=store_id, worker_id=name, pid=proc.pid)
274	        events.log("started", topic=batch.topic, code=code_identity(), fault_file=str(batch.fault_file(name)))
275	
276	        def kill():
277	            proc.kill()
278	            proc.check()
279	
280	        worker = Worker(store, SyntheticPipeline(events, proc, batch.settings.snapshot), batch.jobs_root / store_id,
281	                        worker_id=name, events=events, fault=faults.FaultFile(batch.fault_file(name), events, kill=kill))
282	        consumer = batch.group.join(events, proc)
283	        worker.serve(consumer, stop=proc.halted, poll_timeout=0.05, retry_delay=0.1)
284	        proc.check()                                                   # killed: no orderly leave
285	        consumer.close()
286	        events.log("stopped")
287	    return main
288	
289	
290	def reconciler_main(batch: "SyntheticBatch"):
291	    def main(proc: ThreadProc):
292	        store = batch.job_store()
293	        events = EventLog(batch.events_dir / f"reconciler-{proc.pid}.jsonl", "reconciler", store_id=store.store_id(),
294	                          pid=proc.pid)
295	        events.log("started", topic=batch.topic, code=code_identity())
296	        halt = SimpleNamespace(is_set=proc.halted, wait=time.sleep)
297	        Reconciler(store, batch.queue.publisher(), events=events,
298	                   publication_grace=timedelta(seconds=11)).run(halt, interval=timedelta(seconds=0.2))
299	        proc.check()
300	        events.log("stopped")
301	    return main
302	
303	
304	class SyntheticBatch(harness.Batch):
305	    """harness.Batch with SQLite, the Group, ThreadProc processes and no containers."""
306	    SNAPSHOT, PARAM = "BEGIN", "?"
307	
308	    def __init__(self, plan, out, processed_root):
309	        super().__init__(plan, out)
310	        self.processed_root = processed_root
311	        self.db_path = out / "jobs.sqlite"
312	        self.db = self.env["ETF_RISK_JOBS_DB"] = f"sqlite:///{self.db_path}"
313	        self.queue = MemoryQueue()
314	        self.group = Group(self.queue, self.topic)
```

## 267. Assistant — 2026-10-24T07:57:49.381Z

### Tool call: Bash

```
{
  "command": "pgrep -f \"python -m pytest -q -p no:cacheprovider tests\" >/dev/null && echo running || cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Check whether the full suite has finished"
}
```

## 268. User — 2026-10-24T07:57:50.210Z

### Tool result

```
running
```

## 269. Assistant — 2026-10-24T07:57:55.679Z

### Tool call: ToolSearch

```
{
  "query": "select:Monitor",
  "max_results": 1
}
```

## 270. User — 2026-10-24T07:57:56.141Z

### Tool result

````
```
{
  "type": "tool_reference",
  "tool_name": "Monitor"
}
```
````

## 271. Assistant — 2026-10-24T07:58:22.457Z

### Tool call: Bash

```
{
  "command": "S=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic2 && rm -rf \"$S\" && env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_recovery_synthetic.py --basetemp=\"$S\" 2>&1 | tail -1",
  "description": "Rerun the synthetic batch test with wider margins under load",
  "timeout": 300000
}
```

## 272. User — 2026-10-24T07:58:49.738Z

### Tool result

```
1 passed, 9 warnings in 24.77s
```

## 273. Assistant — 2026-10-24T07:59:00.261Z

### Tool call: Bash

```
{
  "command": "B=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic2/test_a_synthetic_batch_runs_en0/batch && .venv/bin/python - \"$B\" <<'EOF'\nimport csv, json, sys\nfrom pathlib import Path\nb = Path(sys.argv[1])\ndef f(x):\n    try:\n        return f\"{float(x):.2f}\"\n    except ValueError:\n        return x\nprint(\"pos case  detection rerun finish overhead claims exec complete wasted timeliness / met / q3a\")\nfor r in csv.DictReader(open(b / \"injections.csv\")):\n    print(r[\"position\"], r[\"case\"].ljust(4), *(f(r[k]) for k in (\"detection_s\", \"rerun_s\", \"finish_s\", \"overhead_s\")),\n          r[\"claims\"], r[\"executions\"], r[\"complete_executions\"], f(r[\"wasted_step_s\"]), \"|\", r[\"timeliness\"], \"/\",\n          r[\"deadline_met\"], \"/\", r[\"q3a_verdict\"])\nv = json.loads((b / \"validity.json\").read_text())\nprint(\"validity_failed:\", v[\"validity_failed\"], \"| clock ts-mono:\", round(v[\"validity\"][\"clock\"][\"ts_minus_mono_s\"], 4),\n      \"| identity records:\", v[\"validity\"][\"code_identity\"][\"records\"], \"| c0 median:\", round(v[\"c0_median_s\"], 3))\nprint(\"overlap:\", v[\"outcomes\"][\"overlap\"][\"verdict\"], \"| accepted checks clean:\",\n      sum(not a[\"problems\"] for a in v[\"outcomes\"][\"accepted_attempts\"]), \"of\", len(v[\"outcomes\"][\"accepted_attempts\"]))\nEOF",
  "description": "Show the second synthetic batch's per-job metrics"
}
```

## 274. User — 2026-10-24T07:59:01.090Z

### Tool result

```
pos case  detection rerun finish overhead claims exec complete wasted timeliness / met / q3a
1 C0   n/a: no failure n/a: no failure 1.22 0.02 1 1 1 0.00 | on time / yes / reported once
2 W1   0.50 0.50 1.74 0.61 1 1 1 0.00 | on time / yes / reported once
3 W2   3.00 3.01 4.15 3.06 2 1 1 0.00 | on time / yes / reported once
4 W3   2.92 2.93 4.07 3.22 2 2 1 0.31 | on time / yes / reported once
5 W4   3.06 3.07 4.23 4.22 2 2 2 1.12 | late / no / reported once
6 W5a  n/a: after acceptance n/a: after acceptance n/a: after acceptance n/a: after acceptance 1 1 1 0.00 | on time / yes / no matching report
7 W5b  n/a: after acceptance n/a: after acceptance n/a: after acceptance n/a: after acceptance 1 1 1 0.00 | on time / yes / reported once
8 X1   n/a: no failure n/a: no failure 1.09 0.01 1 1 1 0.00 | on time / yes / reported once
9 C0   n/a: no failure n/a: no failure 1.18 -0.02 1 1 1 0.00 | deadline not observed / unknown / reported once
validity_failed: [] | clock ts-mono: 0.0001 | identity records: 52 | c0 median: 1.199
overlap: no overlap | accepted checks clean: 9 of 9
```

## 275. Assistant — 2026-10-24T07:59:09.404Z

### Tool call: Bash

```
{
  "command": "pgrep -f \"python -m pytest -q -p no:cacheprovider tests\" >/dev/null && echo running || cat /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Check whether the full suite has finished"
}
```

## 276. User — 2026-10-24T07:59:10.206Z

### Tool result

```
running
```

## 277. Assistant — 2026-10-24T07:59:16.157Z

### Tool call: Monitor

```
{
  "command": "while pgrep -f \"python -m pytest -q -p no:cacheprovider tests\" >/dev/null; do sleep 5; done; grep -E \"passed|failed|error|exit=\" /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt || echo \"suite ended; no summary line found\"",
  "description": "full offline pytest suite: final summary line",
  "timeout_ms": 1800000
}
```

## 278. User — 2026-10-24T07:59:17.109Z

### Tool result

```
Monitor started (task bu3a4cyip, expires in 30m unless the source ends first; you get one notice at expiry — re-arm if you still need the watch). You will be notified on each event. Keep working — do not poll or sleep. Events may arrive while you are waiting for the user — an event is not their reply.
```

## 279. Assistant — 2026-10-24T07:59:26.338Z

While the monitor waits, I'm preparing the outline's tooling and history text so it can go in as soon as the counts are known:

## 280. Assistant — 2026-10-24T07:59:41.284Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/doc_section9.py",
  "content": "\"\"\"Fills section 9 and the history of docs/recovery-experiments.md; SUITE is the full suite's result.\"\"\"\nimport sys\nfrom pathlib import Path\n\nsuite = sys.argv[1]\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nold = \"\"\"- **Tooling**, uncommitted on `feature/recovery-harness`, written with Claude Code at the author's\n  decision of 2026-10-24. Its offline tests are written; none of it has run:\n  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs\n    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)\n    byte for byte (a test checks it);\n  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);\n  - assignment events in `kafka.py` (2.4);\n  - code identity at launch, in `provenance.py`, `cli.py` and `pipeline.py` (2.3);\n  - the fault hook, `faults.py`, wired in `cli.py`, and the fault point `after_accept_commit` in\n    `worker.py` (8.4).\n- **Not done:** monotonic step times in the launcher records (8.5), mutation checks for the new\n  code, and any run of it.\"\"\"\nnew = f\"\"\"- **Tooling**, uncommitted on `feature/recovery-harness`, written with Claude Code at the author's\n  decision of 2026-10-24:\n  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs\n    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)\n    byte for byte (a test checks it);\n  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);\n  - assignment events in `kafka.py` (2.4);\n  - code identity at launch, in `provenance.py`, `cli.py` and `pipeline.py` (2.3);\n  - the fault hook, `faults.py`, wired in `cli.py`, and the fault point `after_accept_commit` in\n    `worker.py` (8.4);\n  - each step's interval on the monotonic clock in the launcher's record, `step_started_mono` and\n    `tree_ended_mono` (4.1, 6.5);\n  - in `worker.py`, no acceptance call once F has passed, as [worker-pipeline.md](worker-pipeline.md)\n    states; before 2026-10-24 the first call was made without that check (D2's path in 3.1).\n- **Tests, offline only, run on 2026-10-24.** The full suite without the services: {suite}. Among\n  them: the frozen queries on SQLite against all 82 expected rows of [recovery-sql.md](recovery-sql.md)\n  (`tests/test_recovery_sql.py`; the translation drops MySQL's collation clauses and\n  `CAST(... AS BINARY)`, so the MySQL run stays the evidence for MySQL); and one synthetic batch, end\n  to end (`tests/test_recovery_synthetic.py`): the harness's own run on SQLite, with workers and a\n  reconciler in its process, a one-partition stand-in for the Kafka group and stand-ins for the\n  Spark steps and their launchers, read by the collector. It covers C0, W1, W2, W3, W4 (completing\n  late on purpose), W5a, W5b and X1, and one failed deadline observation; W6, W7, K1, K2, D1 and D2\n  need the services. Writing it found that the harness matched `step_ended` by a `step` field, which\n  that event does not have (it names its step `name`), so a mid-step phase check would never have\n  seen the step end; fixed and tested.\n- **Not done:** mutation checks for the new code (two spot checks only: the acceptance deadline and\n  Q2's rules), the MySQL and Kafka variants of the tests, and any run against the services.\"\"\"\nassert s.count(old) == 1, \"section 9\"\ns = s.replace(old, new)\nold = \"\"\"  instead of a fault named in the environment. Timing, repetitions and memory thresholds stay\n  provisional.\"\"\"\nnew = \"\"\"  instead of a fault named in the environment. Timing, repetitions and memory thresholds stay\n  provisional.\n- **Revision 4, tests, 2026-10-24.** The offline tests run in an exclusive window the author gave;\n  the acceptance deadline enforced before the first acceptance call, as the approved policy states;\n  monotonic step times in the launcher records, which the overlap check now compares; the frozen\n  queries checked on SQLite against the 82 expected rows; a synthetic batch run end to end without\n  services; a harness bug in the mid-step phase check fixed. Part A and section 8 unchanged.\"\"\"\nassert s.count(old) == 1, \"history\"\ns = s.replace(old, new)\np.write_text(s)\nprint(\"section 9 and history updated\")\n"
}
```

## 281. User — 2026-10-24T07:59:43.280Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/doc_section9.py (file state is current in your context — no need to Read it back)
```

## 282. Assistant — 2026-10-24T07:59:52.301Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/doc_section9.py",
  "old_string": "  services; a harness bug in the mid-step phase check fixed. Part A and section 8 unchanged.\"\"\"",
  "new_string": "  services; a harness bug in the mid-step phase check fixed. The proposals P1–P5 are unchanged;\n  section 8 changed only where it said that tests had not run, and in 8.5's open items.\"\"\""
}
```

## 283. User — 2026-10-24T07:59:53.936Z

### Tool result

```
The file /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/doc_section9.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 284. Assistant — 2026-10-24T08:00:05.422Z

Updating the project memory note while the suite runs:

## 285. Assistant — 2026-10-24T08:00:13.008Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md",
  "content": "[REDACTED:memory]"
}
```

## 286. User — 2026-10-24T08:00:14.815Z

### Tool result

```
[REDACTED:memory]
```

## 287. Assistant — 2026-10-24T08:00:25.096Z

The memory index has no entry for this note, so I'll add one by appending, without printing the index:

## 288. Assistant — 2026-10-24T08:00:27.060Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Append the memory note's pointer to the index"
}
```

## 289. User — 2026-10-24T08:00:28.978Z

### Tool result

```
[REDACTED:memory]
```

## 290. Assistant — 2026-10-24T08:00:37.823Z

The count is 2, so the index already had a pointer that the snapshot I saw didn't show. Removing my duplicate and updating the existing line in place, without printing the file:

## 291. Assistant — 2026-10-24T08:00:40.302Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Remove the duplicate pointer and update the existing one"
}
```

## 292. User — 2026-10-24T08:00:41.494Z

### Tool result

```
[REDACTED:memory]
```

## 293. Assistant — 2026-10-24T08:00:52.256Z

The index now has one up-to-date pointer. While the suite finishes, proofreading the outline's edited D2 rows:

## 294. Assistant — 2026-10-24T08:00:53.513Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^\\| D2 \\|' docs/recovery-experiments.md | cut -c1-400",
  "description": "Show the outline's D2 rows after the edit"
}
```

## 295. User — 2026-10-24T08:00:54.324Z

### Tool result

```
161:| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL, after a peak reading | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`), or, if the hold ends at or after F, makes no acceptance call (`fenced`, during acceptance); either way the job runs again after its lease expire
182:| D2 | `retry` of `accept_result`, or `fenced` during acceptance if the hold outlasted F; then `accepted`, or else `failed_after_ack` or that `fenced`, and `requeued` | as D1 | as D1 |
```

## 296. Assistant — 2026-10-24T08:01:11.040Z

### Tool call: Bash

```
{
  "command": "grep -ln \"recovery-experiments\" tests/*.py; echo \"---\"; grep -rn \"recovery-experiments.md\" tests/*.py | head -3",
  "description": "Check whether any test reads the outline document"
}
```

## 297. User — 2026-10-24T08:01:12.068Z

### Tool result

```
tests/test_jobs_kafka.py
tests/test_provenance.py
---
tests/test_jobs_kafka.py:70:    """The recovery harness reads the partition's owner from these events (docs/recovery-experiments.md, 2.4)."""
tests/test_provenance.py:22:    """What a starting process and a step launch record (docs/recovery-experiments.md, 2.3)."""
```

## 298. Assistant — 2026-10-24T08:01:19.646Z

Status: everything is written. The first full run started before my last few edits: the collector's D2 rule and its test, the wider synthetic-test margins, and two docstrings. Once it reports, I'll run the full suite once more so the final count covers exactly the current code, then fill that count into the outline and give you the report. The monitor will wake me when the first run ends.

## 299. User — 2026-10-24T08:02:56.281Z

<task-notification>
<task-id>buduuarrm</task-id>
<tool-use-id>toolu_01EsPVE9QirFJpnRBEh5Ks6r</tool-use-id>
<output-file>/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/tasks/buduuarrm.output</output-file>
<status>completed</status>
<summary>Background command "Rerun the full offline suite in the background" completed (exit code 0)</summary>
</task-notification>

## 300. Assistant — 2026-10-24T08:03:06.339Z

Both background runs have ended. First, a memory-index check: the re-read index shows the older pointer text, and the extension-plan line has also changed, so another session may have rewritten MEMORY.md after my edit. Checking with counts only, without printing the file:

## 301. Assistant — 2026-10-24T08:03:08.098Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Count which memory pointer text is present now"
}
```

## 302. User — 2026-10-24T08:03:10.157Z

### Tool result

```
[REDACTED:memory]
```

## 303. Assistant — 2026-10-24T08:03:16.866Z

The memory pointer is intact; the re-read snapshot was older than my edit. The first full run gave 608 passed, 1 failed and 30 skipped in 11 min. Finding the failure:

## 304. Assistant — 2026-10-24T08:03:19.229Z

### Tool call: Bash

```
{
  "command": "grep -E \"FAILED|ERROR|^E \" /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt | head -10; grep -c \"\" /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite.txt",
  "description": "Find the failing test's name in the saved summary"
}
```

## 305. User — 2026-10-24T08:03:20.123Z

### Tool result

```
FAILED tests/test_caching_collector.py::test_the_batch_meets_every_criterion
16
```

## 306. Assistant — 2026-10-24T08:03:33.832Z

The failure is tests/test_caching_collector.py::test_the_batch_meets_every_criterion, which I did not touch. Running it alone to see whether it fails by itself:

## 307. Assistant — 2026-10-24T08:03:35.251Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" python -m pytest -q -p no:cacheprovider tests/test_caching_collector.py 2>&1 | grep -E \"^E |passed|failed|Error\" | head -20",
  "description": "Run the caching collector tests alone",
  "timeout": 900000
}
```

## 308. User — 2026-10-24T08:05:11.931Z

### Tool result

```
22 passed, 23 warnings in 94.29s (0:01:34)
```

## 309. Assistant — 2026-10-24T08:05:23.489Z

Alone, all 22 pass. So the failure depends on context: ordering, load, or something I ran alongside. Looking at what the test checks:

## 310. Assistant — 2026-10-24T08:05:24.526Z

### Tool call: Bash

```
{
  "command": "grep -n -A25 \"def test_the_batch_meets_every_criterion\" tests/test_caching_collector.py | head -45",
  "description": "Read the failing caching collector test"
}
```

## 311. User — 2026-10-24T08:05:25.425Z

### Tool result

```
123:def test_the_batch_meets_every_criterion(batch, windows):
124-    rows, acceptance = collect(batch, windows)
125-    assert acceptance["all_ok"], failing(acceptance)
126-    assert len(rows) == len(ccm.ORDER) * REPEATS
127-    for table in ccm.TABLE_KEYS:
128-        assert {r[f"{table}_vs_reference"] for r in rows} == {"pass", "reference"}
129-    by_config = {r["config"]: r for r in rows}
130-    assert by_config["A"]["cached_reads_checks"] == "0/0/0" and by_config["C"]["cached_reads_checks"].split("/")[0] != "0"
131-    assert by_config["C"]["path_days_memory_bytes"] > 0 and by_config["A"]["path_days_memory_bytes"] == ""
132-    assert {c: {r["fill_executions"] for r in rows if r["config"] == c} for c in "ABC"} == {"A": {0}, "B": {1}, "C": {5}}
133-
134-
135-def test_the_check_after_each_protocol_knows_the_configuration(batch):
136-    for config, wrong in (("A", "B"), ("B", "C"), ("C", "A")):
137-        protocol = next((batch / config).rglob("protocol-*.json"))
138-        assert ccm.check_protocol(protocol, config) == []
139-        assert ccm.check_protocol(protocol, wrong)
140-
141-
142-def test_the_csv_has_one_row_per_started_run_and_the_documented_columns(batch, windows, tmp_path):
143-    rows, _ = collect(batch, windows)
144-    ccm.write_csv(rows, tmp_path / "m.csv")
145-    with (tmp_path / "m.csv").open() as f:
146-        reader = csv.reader(f)
147-        assert next(reader) == ccm.FIELDS
148-        assert sum(1 for _ in reader) == len(rows)
```

## 312. Assistant — 2026-10-24T08:05:30.863Z

### Tool call: Bash

```
{
  "command": "sed -n 1,60p tests/test_caching_collector.py | grep -n -E \"^\\\"\\\"\\\"|import|fixture|def batch|def windows|spark|measure|REPEATS|criteria|stop\" | head -30; grep -n -E \"def check_criteria|CRITERIA|stop_rule|peak|memory|rss\" analysis/collect_caching_measurements.py | head -20",
  "description": "Find what the batch fixture runs and which criteria it checks"
}
```

## 313. User — 2026-10-24T08:05:31.655Z

### Tool result

```
1:"""The caching collector (analysis/collect_caching_measurements.py) on a fake batch built from real runs.
3:The fixture runs the pipeline once per configuration in a fresh process, as etf_risk.measure starts
5:per protocol, with protocol JSONs, measurement sections and positions.tsv as measure and the session
8:covers it. Runs that failed or were aborted without their outputs must be reported, not stop it.
11:"""
12:import csv
13:import importlib.util
14:import json
15:import shutil
16:import subprocess
17:import sys
18:from pathlib import Path
20:import numpy as np
21:import pyarrow as pa
22:import pyarrow.parquet as pq
23:import pytest
24:from conftest import nyse_sessions, write_snapshot
26:from etf_risk.windows import build_definitions, write_definitions
31:_spec = importlib.util.spec_from_file_location("collect_caching_measurements", ANALYSIS / "collect_caching_measurements.py")
32:ccm = importlib.util.module_from_spec(_spec)
35:pytestmark = pytest.mark.spark
37:REPEATS = 2
41:@pytest.fixture(scope="module")
42:def windows(tmp_path_factory):
53:@pytest.fixture(scope="module")
58:        proc = subprocess.run([sys.executable, "-m", "etf_risk.spark_pipeline", "--windows", str(windows),
76:CRITERIA = cpm.CRITERIA
82:                + [f"{table}_{field}" for table in TABLES for field in ("fill_s", "release_s", "memory_bytes", "disk_bytes")]
222:            if rdd["memory_bytes"] + rdd["disk_bytes"] <= 0:
300:                    f"{table}_memory_bytes": rdd.get("memory_bytes", ""), f"{table}_disk_bytes": rdd.get("disk_bytes", "")})
313:    criteria = {name: [] for name in CRITERIA}
354:                criteria["5 completeness"].append(f"position {position}: {entry['run_id']} crossed the memory threshold")
477:    print("used protocols (position, configuration, measured ok runs, median wall_excl_capture_s, median peak GiB):")
481:        peaks = [r["peak_rss_total_bytes"] / 2**30 for r in measured if r["peak_rss_total_bytes"] != ""]
484:              f"{statistics.median(walls):.3f} s, {statistics.median(peaks):.3f} GiB" if walls and peaks
```

## 314. Assistant — 2026-10-24T08:05:45.984Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider -rfE tests > /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite-final.txt 2>&1; echo \"exit=$?\" >> /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite-final.txt",
  "description": "Run the final full offline suite, saving all output",
  "timeout": 1800000,
  "run_in_background": true
}
```

## 315. User — 2026-10-24T08:05:46.916Z

### Tool result

```
Command running in background with ID: bz0t6265w. Output is being written to: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/tasks/bz0t6265w.output. You will be notified when it completes — do not poll that file or sleep while waiting. Read the file only if the user asks for progress, or if you need a line it prints before you can go on, such as a server's ready line or port.
```

## 316. Assistant — 2026-10-24T08:06:16.299Z

The final full run is in progress, with nothing else running alongside it. When it finishes I'll fill its count into the outline and report. If the caching-collector test fails again, the saved output will show why.

## 317. User — 2026-10-24T08:16:50.900Z

<task-notification>
<task-id>bz0t6265w</task-id>
<tool-use-id>toolu_01Qry8NR4HRWe3eNYXu3TUBf</tool-use-id>
<output-file>/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/tasks/bz0t6265w.output</output-file>
<status>completed</status>
<summary>Background command "Run the final full offline suite, saving all output" completed (exit code 0)</summary>
</task-notification>

## 318. Assistant — 2026-10-24T08:17:08.551Z

### Tool call: Bash

```
{
  "command": "F=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/full-suite-final.txt; tail -3 \"$F\"; grep -E \"^(FAILED|ERROR) \" \"$F\" | head",
  "description": "Show the final full suite result"
}
```

## 319. User — 2026-10-24T08:17:09.472Z

### Tool result

```
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
610 passed, 30 skipped, 1178 warnings in 661.90s (0:11:01)
exit=0
```

## 320. Assistant — 2026-10-24T08:17:22.390Z

Final full run: 610 passed, 30 skipped, 0 failed, in 11 min 2 s. That is 608 + the caching test that failed once + the D2 test added after the first run started. Listing why the 30 were skipped:

## 321. Assistant — 2026-10-24T08:17:25.098Z

### Tool call: Bash

```
{
  "command": "FILES=$(grep -l -E \"needs_mysql|needs_kafka|skipif|importorskip|pytest.skip\" tests/test_*.py | tr '\\n' ' ') && PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider -rs -m \"not spark\" $FILES 2>&1 | grep -E \"^SKIPPED\" | sed -E 's/^SKIPPED \\[([0-9]+)\\] [^:]+:[0-9]+: /\\1 x /' | sort | uniq -c | sort -rn | head -12",
  "description": "Summarize the skip reasons of the skipped tests",
  "timeout": 600000
}
```

## 322. User — 2026-10-24T08:17:27.162Z

### Tool result

```
(Bash completed with no output)
```

## 323. Assistant — 2026-10-24T08:17:33.570Z

### Tool call: Bash

```
{
  "command": "FILES=$(grep -l -E \"needs_mysql|needs_kafka|skipif|importorskip|pytest.skip\" tests/test_*.py | tr '\\n' ' ') && echo \"$FILES\" && PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider -rs $FILES 2>&1 | grep -E \"SKIPPED|passed|skipped\" | head -20",
  "description": "List skip reasons from the files that skip",
  "timeout": 900000
}
```

## 324. User — 2026-10-24T08:17:35.590Z

### Tool result

```
tests/test_baseline_session.py tests/test_caching_session.py tests/test_jobs_mysql.py tests/test_jobs_live_pipeline.py tests/test_jobs_kafka.py tests/test_partition_session.py
```

## 325. Assistant — 2026-10-24T08:17:41.799Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider -rs tests/test_jobs_mysql.py tests/test_jobs_live_pipeline.py tests/test_jobs_kafka.py 2>&1 | tail -12",
  "description": "Show skip reasons for the service-backed job tests",
  "timeout": 600000
}
```

## 326. User — 2026-10-24T08:17:46.313Z

### Tool result

```
SKIPPED [1] tests/test_jobs_kafka.py:110: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:118: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:127: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:135: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:142: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:157: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:188: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:203: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:222: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:237: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
SKIPPED [1] tests/test_jobs_kafka.py:255: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
12 passed, 30 skipped, 1 warning in 2.39s
```

## 327. Assistant — 2026-10-24T08:17:52.159Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider -rs tests/test_jobs_mysql.py tests/test_jobs_live_pipeline.py tests/test_jobs_kafka.py 2>&1 | grep -E \"^SKIPPED\" | sed -E 's/^SKIPPED \\[([0-9]+)\\] (tests\\/[a-z_]+\\.py):[0-9]+: (.*)$/\\2: \\3/' | sort | uniq -c",
  "description": "Count skips per file and reason",
  "timeout": 600000
}
```

## 328. User — 2026-10-24T08:17:57.690Z

### Tool result

```
  11 tests/test_jobs_kafka.py: set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka
   8 tests/test_jobs_live_pipeline.py: set ETF_RISK_LIVE_PIPELINE=1, ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP, with the snapshot in data/
   9 tests/test_jobs_mysql.py: set ETF_RISK_MYSQL_URL to run against MySQL
```

## 329. Assistant — 2026-10-24T08:18:03.911Z

### Tool call: Bash

```
{
  "command": "grep -n -E \"skipif|pytest.skip\\(|importorskip\" tests/test_baseline_session.py tests/test_caching_session.py tests/test_partition_session.py | head",
  "description": "Find the skip conditions in the session tests"
}
```

## 330. User — 2026-10-24T08:18:04.641Z

### Tool result

```
tests/test_caching_session.py:16:pytestmark = pytest.mark.skipif(shutil.which("zsh") is None, reason="needs zsh")
tests/test_baseline_session.py:16:pytestmark = pytest.mark.skipif(shutil.which("zsh") is None, reason="needs zsh")
tests/test_partition_session.py:16:pytestmark = pytest.mark.skipif(shutil.which("zsh") is None, reason="needs zsh")
```

## 331. Assistant — 2026-10-24T08:18:12.537Z

28 of the 30 skips are the three service-backed files. Finding the other two with a quicker run that deselects the Spark-marked tests:

## 332. Assistant — 2026-10-24T08:18:14.713Z

### Tool call: Bash

```
{
  "command": "PATH=\"$PWD/.venv/bin:$PATH\" env -u ETF_RISK_MYSQL_URL -u ETF_RISK_KAFKA_BOOTSTRAP -u ETF_RISK_LIVE_PIPELINE python -m pytest -q -p no:cacheprovider -rs -m \"not spark\" tests --deselect tests/test_jobs_worker_spark.py 2>&1 | grep -E \"^SKIPPED\" | grep -v -E \"test_jobs_(kafka|mysql|live_pipeline)\\.py\" | head -5",
  "description": "Find the remaining two skip reasons outside the service files",
  "timeout": 900000
}
```

## 333. User — 2026-10-24T08:20:05.650Z

### Tool result

```
(Bash completed with no output)
```

## 334. Assistant — 2026-10-24T08:20:19.497Z

### Tool call: Bash

```
{
  "command": "python3 /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/doc_section9.py \"610 passed and 30 skipped, none failed; the skipped ones are the MySQL, Kafka and live-pipeline tests, which need the services\" && grep -n -A3 \"^- \\*\\*Tests, offline only\" docs/recovery-experiments.md | head -5 && wc -l docs/recovery-experiments.md",
  "description": "Write the final test result into the outline's section 9"
}
```

## 335. User — 2026-10-24T08:20:20.842Z

### Tool result

```
section 9 and history updated
538:- **Tests, offline only, run on 2026-10-24.** The full suite without the services: 610 passed and 30 skipped, none failed; the skipped ones are the MySQL, Kafka and live-pipeline tests, which need the services. Among
539-  them: the frozen queries on SQLite against all 82 expected rows of [recovery-sql.md](recovery-sql.md)
540-  (`tests/test_recovery_sql.py`; the translation drops MySQL's collation clauses and
541-  `CAST(... AS BINARY)`, so the MySQL run stays the evidence for MySQL); and one synthetic batch, end
     593 docs/recovery-experiments.md
```

## 336. Assistant — 2026-10-24T08:20:25.527Z

That first line runs past the document's line width. Rewrapping it:

## 337. Assistant — 2026-10-24T08:20:27.968Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "- **Tests, offline only, run on 2026-10-24.** The full suite without the services: 610 passed and 30 skipped, none failed; the skipped ones are the MySQL, Kafka and live-pipeline tests, which need the services. Among\n  them: the frozen queries on SQLite against all 82 expected rows of [recovery-sql.md](recovery-sql.md)",
  "new_string": "- **Tests, offline only, run on 2026-10-24.** The full suite without the services: 610 passed and 30\n  skipped, none failed; the skipped ones are the MySQL, Kafka and live-pipeline tests, which need the\n  services. Among them: the frozen queries on SQLite against all 82 expected rows of\n  [recovery-sql.md](recovery-sql.md)"
}
```

## 338. Assistant — 2026-10-24T08:20:29.643Z

### Tool call: Bash

```
{
  "command": "awk 'length > 104 && !/^\\|/ {print FILENAME\": \"FNR\": \"length}' docs/recovery-experiments.md | head; sed -n \"$(grep -n '^- \\*\\*Tests, offline only' docs/recovery-experiments.md | cut -d: -f1),+20p\" docs/recovery-experiments.md",
  "description": "Check line widths and read the new tests passage"
}
```

## 339. User — 2026-10-24T08:20:32.067Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully. (note: the file had been modified on disk since you last read it — the edit applied cleanly, but the file contains other changes not in your context. Read it before edits that depend on surrounding content.)
```

## 340. User — 2026-10-24T08:20:32.750Z

### Tool result

```
docs/recovery-experiments.md: 106: 142
docs/recovery-experiments.md: 196: 120
- **Tests, offline only, run on 2026-10-24.** The full suite without the services: 610 passed and 30
  skipped, none failed; the skipped ones are the MySQL, Kafka and live-pipeline tests, which need the
  services. Among them: the frozen queries on SQLite against all 82 expected rows of
  [recovery-sql.md](recovery-sql.md)
  (`tests/test_recovery_sql.py`; the translation drops MySQL's collation clauses and
  `CAST(... AS BINARY)`, so the MySQL run stays the evidence for MySQL); and one synthetic batch, end
  to end (`tests/test_recovery_synthetic.py`): the harness's own run on SQLite, with workers and a
  reconciler in its process, a one-partition stand-in for the Kafka group and stand-ins for the
  Spark steps and their launchers, read by the collector. It covers C0, W1, W2, W3, W4 (completing
  late on purpose), W5a, W5b and X1, and one failed deadline observation; W6, W7, K1, K2, D1 and D2
  need the services. Writing it found that the harness matched `step_ended` by a `step` field, which
  that event does not have (it names its step `name`), so a mid-step phase check would never have
  seen the step end; fixed and tested.
- **Not done:** mutation checks for the new code (two spot checks only: the acceptance deadline and
  Q2's rules), the MySQL and Kafka variants of the tests, and any run against the services.
- **Authorship.** Spec §11: the job code is written with Claude Code. At the author's decision of
  2026-10-24, Claude Code also writes the recovery experiments' tooling listed above, and each new
  module says so. The items in 1.1, and the experiments' decisions, runs and answers, are the
  author's; everything else here is Claude Code's proposal. The queries of
  [recovery-sql.md](recovery-sql.md) stay marked as drafted with Claude Code.
```

## 341. Assistant — 2026-10-24T08:20:37.706Z

Two other lines run long. Checking whether my edits caused them:

## 342. Assistant — 2026-10-24T08:20:38.528Z

### Tool call: Bash

```
{
  "command": "sed -n '106p;196p' docs/recovery-experiments.md",
  "description": "Show the two long lines"
}
```

## 343. User — 2026-10-24T08:20:41.416Z

### Tool result

```
`provenance.code_identity()` for starting processes, and `provenance.source_identity()`, the same two hashes without asking git, for each step
times (`step_started_mono` and `tree_ended_mono` in its record). On macOS this reads a system-wide clock; the launcher's
```

## 344. Assistant — 2026-10-24T08:20:45.418Z

Both come from my replacements. Rewrapping those two paragraphs and tidying the short line in the tests passage:

## 345. Assistant — 2026-10-24T08:20:46.404Z

### Tool call: Bash

```
{
  "command": "sed -n '103,110p;193,202p' docs/recovery-experiments.md",
  "description": "Read the two paragraphs around the long lines"
}
```

## 346. User — 2026-10-24T08:20:47.208Z

### Tool result

```
it at the start and end of the batch. The identity is `source_digest`, one SHA-256 over the per-file
`source_sha256` map of `provenance.code_state()`, with `uv_lock_sha256`; the commit and the clean
flag are only reported. Implemented and tested offline, not yet run against the services:
`provenance.code_identity()` for starting processes, and `provenance.source_identity()`, the same two hashes without asking git, for each step
launch. A crashed attempt writes no `attempt.json`, so identity is never read from that file; it is
read only for accepted attempts, to find their run folder (6.2).

### 2.4 Worker startup order and the partition

Every duration is a difference of two `time.monotonic()` readings on this host: the events' `mono`
([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step
times (`step_started_mono` and `tree_ended_mono` in its record). On macOS this reads a system-wide clock; the launcher's
handshake checks the worker and its launchers, and the harness checks each process it starts (the
`mono` of its first event must lie between the harness's readings just before the start and just
after it read that event). The clock pauses while the host sleeps, so the host must not sleep during
a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock columns, never for a
duration. The harness records `ts` and `mono` together at the start and end of a batch; a difference
in their elapsed times beyond a tolerance (8.5) means a sleep or a clock step and fails validity
```

## 347. Assistant — 2026-10-24T08:20:58.063Z

### Tool call: Bash

```
{
  "command": "python3 - <<'EOF'\nfrom pathlib import Path\np = Path(\"docs/recovery-experiments.md\")\ns = p.read_text()\nreps = [\n(\"\"\"flag are only reported. Implemented and tested offline, not yet run against the services:\n`provenance.code_identity()` for starting processes, and `provenance.source_identity()`, the same two hashes without asking git, for each step\nlaunch. A crashed attempt writes no `attempt.json`, so identity is never read from that file; it is\nread only for accepted attempts, to find their run folder (6.2).\"\"\",\n\"\"\"flag are only reported. Implemented and tested offline, not yet run against the services:\n`provenance.code_identity()` for starting processes, and `provenance.source_identity()`, the same\ntwo hashes without asking git, for each step launch. A crashed attempt writes no `attempt.json`, so\nidentity is never read from that file; it is read only for accepted attempts, to find their run\nfolder (6.2).\"\"\"),\n(\"\"\"([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step\ntimes (`step_started_mono` and `tree_ended_mono` in its record). On macOS this reads a system-wide clock; the launcher's\nhandshake checks the worker and its launchers, and the harness checks each process it starts (the\n`mono` of its first event must lie between the harness's readings just before the start and just\nafter it read that event).\"\"\",\n\"\"\"([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step\ntimes (`step_started_mono` and `tree_ended_mono` in its record). On macOS this reads a system-wide\nclock; the launcher's handshake checks the worker and its launchers, and the harness checks each\nprocess it starts (the `mono` of its first event must lie between the harness's readings just before\nthe start and just after it read that event).\"\"\"),\n(\"\"\"  services. Among them: the frozen queries on SQLite against all 82 expected rows of\n  [recovery-sql.md](recovery-sql.md)\n  (`tests/test_recovery_sql.py`; the translation drops MySQL's collation clauses and\n  `CAST(... AS BINARY)`, so the MySQL run stays the evidence for MySQL); and one synthetic batch, end\"\"\",\n\"\"\"  services. Among them: the frozen queries on SQLite against all 82 expected rows of\n  [recovery-sql.md](recovery-sql.md) (`tests/test_recovery_sql.py`; the translation drops MySQL's\n  collation clauses and `CAST(... AS BINARY)`, so the MySQL run stays the evidence for MySQL); and\n  one synthetic batch, end\"\"\"),\n]\nfor old, new in reps:\n    assert s.count(old) == 1, old[:70]\n    s = s.replace(old, new)\np.write_text(s)\nEOF\nawk 'length > 104 && !/^\\|/ {print FNR\": \"length}' docs/recovery-experiments.md | head -3; echo \"long lines checked\"",
  "description": "Rewrap the edited outline paragraphs"
}
```

## 348. User — 2026-10-24T08:20:59.034Z

### Tool result

```
200: 119
long lines checked
```

## 349. Assistant — 2026-10-24T08:21:03.707Z

### Tool call: Bash

```
{
  "command": "sed -n '196,206p' docs/recovery-experiments.md",
  "description": "Read the paragraph that still has a long line"
}
```

## 350. User — 2026-10-24T08:21:04.508Z

### Tool result

```
([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings, and the launcher's step
times (`step_started_mono` and `tree_ended_mono` in its record). On macOS this reads a system-wide
clock; the launcher's handshake checks the worker and its launchers, and the harness checks each
process it starts (the `mono` of its first event must lie between the harness's readings just before
the start and just after it read that event). The clock pauses while the host sleeps, so the host must not sleep during
a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock columns, never for a
duration. The harness records `ts` and `mono` together at the start and end of a batch; a difference
in their elapsed times beyond a tolerance (8.5) means a sleep or a clock step and fails validity
(6.1).

### 4.2 Deadlines
```

## 351. Assistant — 2026-10-24T08:21:09.612Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "the start and just after it read that event). The clock pauses while the host sleeps, so the host must not sleep during\na batch. `ts` (UTC) orders events and relates them to the tables' wall-clock columns, never for a\nduration.",
  "new_string": "the start and just after it read that event). The clock pauses while the host sleeps, so the host\nmust not sleep during a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock\ncolumns, never for a duration."
}
```

## 352. Assistant — 2026-10-24T08:21:11.169Z

### Tool call: Bash

```
{
  "command": "awk 'length > 104 && !/^\\|/ {print FNR\": \"length}' docs/recovery-experiments.md | head -3; echo \"widths ok\"; grep -n \"none of it has run\\|not yet run\\b\\|has not run yet\" docs/recovery-experiments.md | head",
  "description": "Recheck widths and leftover not-run statements"
}
```

## 353. User — 2026-10-24T08:21:12.984Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 354. User — 2026-10-24T08:21:13.222Z

### Tool result

```
202: 121
widths ok
16:synthetic batch run end to end without services; none of it has run against the services, and no
94:runs come before the workers start, so that they delay no measured step. Implemented, not yet run
105:flag are only reported. Implemented and tested offline, not yet run against the services:
```

## 355. Assistant — 2026-10-24T08:21:18.304Z

### Tool call: Bash

```
{
  "command": "sed -n '200,206p' docs/recovery-experiments.md",
  "description": "Read the remaining long line's paragraph"
}
```

## 356. User — 2026-10-24T08:21:19.019Z

### Tool result

```
the start and just after it read that event). The clock pauses while the host sleeps, so the host
must not sleep during a batch. `ts` (UTC) orders events and relates them to the tables' wall-clock
columns, never for a duration. The harness records `ts` and `mono` together at the start and end of a batch; a difference
in their elapsed times beyond a tolerance (8.5) means a sleep or a clock step and fails validity
(6.1).

### 4.2 Deadlines
```

## 357. Assistant — 2026-10-24T08:21:24.254Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "columns, never for a duration. The harness records `ts` and `mono` together at the start and end of a batch; a difference\nin their elapsed times beyond a tolerance (8.5) means a sleep or a clock step and fails validity\n(6.1).",
  "new_string": "columns, never for a duration. The harness records `ts` and `mono` together at the start and end of\na batch; a difference in their elapsed times beyond a tolerance (8.5) means a sleep or a clock step\nand fails validity (6.1)."
}
```

## 358. Assistant — 2026-10-24T08:21:25.964Z

### Tool call: Bash

```
{
  "command": "awk 'length > 104 && !/^\\|/ {print FNR\": \"length}' docs/recovery-experiments.md | head -3; echo \"widths checked\"; PATH=\"$PWD/.venv/bin:$PATH\" python -m pytest -q -p no:cacheprovider tests/test_jobs_harness.py tests/test_recovery_sql.py 2>&1 | tail -1",
  "description": "Recheck widths and rerun the document-reading tests"
}
```

## 359. User — 2026-10-24T08:21:27.898Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 360. User — 2026-10-24T08:21:32.338Z

### Tool result

```
widths checked
28 passed, 1 warning in 2.92s
```

## 361. Assistant — 2026-10-24T08:21:38.878Z

Status: everything is done and verified, and I'm writing up the report. A last check that the worktree holds only the expected files:

## 362. Assistant — 2026-10-24T08:21:39.837Z

### Tool call: Bash

```
{
  "command": "git status --short && git diff --stat | tail -1 && git log --oneline -1",
  "description": "Show the worktree's final changed files"
}
```

## 363. User — 2026-10-24T08:21:40.711Z

### Tool result

```
 M docs/spec.md
 M src/etf_risk/jobs/cli.py
 M src/etf_risk/jobs/kafka.py
 M src/etf_risk/jobs/launcher.py
 M src/etf_risk/jobs/pipeline.py
 M src/etf_risk/jobs/worker.py
 M src/etf_risk/provenance.py
 M tests/test_jobs_cli.py
 M tests/test_jobs_kafka.py
 M tests/test_jobs_launcher.py
 M tests/test_jobs_pipeline.py
 M tests/test_jobs_queue.py
 M tests/test_jobs_worker.py
 M tests/test_provenance.py
?? analysis/collect_recovery_measurements.py
?? docs/recovery-experiments.md
?? docs/recovery-sql.md
?? src/etf_risk/jobs/crosscheck.sql
?? src/etf_risk/jobs/faults.py
?? src/etf_risk/jobs/harness.py
?? tests/recovery_sqlite.py
?? tests/test_jobs_faults.py
?? tests/test_jobs_harness.py
?? tests/test_recovery_collector.py
?? tests/test_recovery_sql.py
?? tests/test_recovery_synthetic.py
 14 files changed, 290 insertions(+), 20 deletions(-)
e4adc38 Correct the live job-suite result in the worker-pipeline status
```

## 364. Assistant — 2026-10-24T08:22:40.211Z

All four coverage items are in place, the acceptance-deadline fix and the monotonic launcher timestamps are done, and the final full offline run passed: **610 passed, 30 skipped, 0 failed** (11 min). The 30 skipped tests are in test_jobs_kafka, test_jobs_mysql and test_jobs_live_pipeline, which need the services. Nothing ran against Docker or the live services, no formal experiment ran, nothing is committed, and the proposals P1–P5 are unchanged.

**Other test runs**
- An earlier full run had one failure, `tests/test_caching_collector.py::test_the_batch_meets_every_criterion`, while I was running the synthetic test alongside it. It passed alone (22 of 22) and in the final run. I saved only the summary line, so the cause is not established.
- `test_jobs_worker_spark` fails when pytest runs without `.venv/bin` first on PATH: its direct Spark run picks up the system python3, which can't import etf_risk. With the venv on PATH it passes. This is how the test depends on its environment, not a code fault.
- Setup: `uv sync --all-groups --offline`, from the local cache only. Only `.venv` changed; the lock file and pyproject did not.

**Fixes**
- **Acceptance deadline:** once F has passed, the worker now makes no acceptance call. It logs `fenced` (during acceptance), and the job runs again after its lease expires, as worker-pipeline.md says. With the check removed, 2 of the new tests fail.
- **Monotonic launcher timestamps:** the launcher records `step_started_mono` and `tree_ended_mono`. The collector's overlap check and wasted step time use only these; a record with UTC times only counts as a missing interval, so the verdict is unknown.
- **Harness bug, found while building the synthetic test:** `spark_running()` looked for the step's name in a `step` field of `step_ended`, but the real event names it in `name`. A W3, W6, W7, K1 or D1 injection could therefore land after the spark step had ended without being recorded as a miss. Fixed. My first fix crashed (`name=` clashed with a parameter name), and the new unit test caught it.
- **Collector:**
  - a missing injection time is reported as "unknown: no injection time";
  - a job with no injection record is counted as unrecorded, never as made;
  - D2 is also detected by its `fenced` event at acceptance.

**Coverage you asked for** (28 new tests)
- **First acceptance call after F:** 4 worker tests, including a D2-style hold released after F.
- **Arming without changing ownership:** only the owner's fault file is written, no worker is started or stopped, and the owner is the same after arming. A fault armed in a running worker fires without a restart. If the other worker claims the job, the injection is marked missed at once instead of after the 300 s timeout.
- **Missing records and unknown observations:**
  - collector cases for each missing record;
  - a failed deadline observation is kept and never repeated;
  - an unfinished job is followed only until its drain limit.
- **Late completion and every SQL verdict:** the frozen crosscheck.sql, translated for SQLite, reproduces all 82 frozen rows, and every verdict appears. Changing the late rule or the lag rule breaks the match. The MySQL run is still the evidence for MySQL.

**Synthetic end-to-end run**
The harness's own batch run executes on SQLite. The CLI commands (init-db, submit, status --check, export), Worker, fault hook and Reconciler are the real code; Kafka, the Spark steps and the processes are stand-ins, with a 3 s lease. The test runs 9 jobs: C0, W1, W2, W3, W4 (deadline set short so it finishes late), W5a, W5b, X1, and a second C0 whose observation fails on purpose. In the kept run (24.8 s):
- all validity checks pass, there is no overlap, and all 9 accepted results match the reference tables;
- detection took 0.50 s for W1 and about 3 s for W2–W4;
- W4 is late, the second C0 is "deadline not observed", and W5a has "no matching report".

These timings come from stand-ins and measure nothing about the job system. The batch folder is at `/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/synthetic2/test_a_synthetic_batch_runs_en0/batch`.

**Smaller formal experiment (proposal)**
I recommend one batch on fresh containers with 2 jobs of each of the 14 cases: 28 jobs, about **50 min**, using the estimator's unmeasured assumptions. If the job's failure-free time is 45, 50 or 60 s instead of 40, that becomes 52, 55 or 60 min. It runs on the existing tooling with `{"jobs_per_case": 2}`.
- It keeps every failure mode and recovery path, and the safety checks on every job.
- It gives up the second batch on fresh containers, and has 2 jobs per case instead of 6.

| Design | Jobs | Estimated time |
|---|---|---|
| Recommended: 2 per case, 1 batch | 28 | about 50 min |
| 2 per case, 2 batches (keeps the repeat across containers) | 56 | about 1 h 40 min |
| 1 per case, 1 batch (one missed injection leaves a case unmeasured) | 14 | about 26 min |
| Current P1: 3 per case, 2 batches | 84 | about 2 h 26 min |

I did not add this to the outline.

**Remaining gaps**
1. Nothing has run against the services. The new worker tests are SQLite-only, and the real reference run through the launcher is replaced in the synthetic test.
2. The synthetic run covers 8 of the 14 cases. W6, W7, K1, K2, D1 and D2 need the services.
3. The stand-ins differ from the real system:
   - a kill lands within about 10 ms rather than instantly;
   - the stand-in group never moves the partition when a worker rejoins;
   - there is no startup sweep;
   - SQLite replaces MySQL's consistent snapshot.
4. **Decision for you:** an acceptance call that starts before F can still commit after it. The attempt's token still guards it. The check now guarantees "no call after F"; making it "no commit after F" would need a store change, which I did not make.
5. M2's live test still compares UTC launcher times; switching it to the new fields is a two-line change. I left it alone because it is M2's test and can't run in this window.
6. Mutation checks exist only as the two spot checks above.

**Outline changes:** D2's expected path, the status sentences, the clock and overlap sections, the open items in 8.5, section 9 and a history entry.

`★ Insight ─────────────────────────────────────`
- The `step`/`name` mismatch got past the unit tests because their hand-written events made the same wrong assumption. The synthetic run caught it only because it had to copy the real event shapes.
- The deadline check is check-then-act, so it narrows the window but can't make an acceptance safe on its own. The attempt's token in the database is what keeps a result from being accepted twice; the F check keeps the worker's behaviour consistent with the stated policy.
`─────────────────────────────────────────────────`
