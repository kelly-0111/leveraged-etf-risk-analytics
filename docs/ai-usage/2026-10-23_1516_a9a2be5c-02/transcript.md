# Claude Code message 2

Session: `a9a2be5c-8da0-4ec5-be57-f251b5676fe9` · prompt sent 2026-10-23 15:16 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): git-user ×33, home ×248, memory ×6, model-reasoning ×45, user ×11. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-23T20:16:56.958Z

<ide_opened_file>The user opened the file ~/leveraged-etf-risk-analytics/docs/spec.md in the IDE. This may or may not be related to the current task.</ide_opened_file>

1. Make deadlines explicit in the records and queries. Distinguish on-time completion, late completion and unfinished jobs; later success must not erase a deadline miss.
2. Separate database acceptance correctness from event-log completeness. Cover a crash after acceptance commits but before its event is written. Repeated reports of one attempt are not multiple accepted results.
3. Do not require successful-attempt artifacts from deliberately crashed attempts. Record code identity at process launch, and treat missing process intervals as unknown rather than proof of no overlap.
4. Use same-host monotonic timestamps for durations. Mark recovery latency as not applicable for failures injected after acceptance.
5. Include Kafka assignment/rebalance conditions in recovery predictions and fix the worker startup order.
6. Check full report identity, including store_id and worker_id.
7. Define the deadline observation, quiescence and consistent SQL/export snapshot.

Use the host lock for reference runs. Remove the pooled rule-of-three claim unless its assumptions are justified.

Add small SQL fixtures for late completion, missing acceptance events, duplicate reports and wrong-worker reports. Keep all cases and failed outcomes visible. Revise documents only for now; do not run formal experiments.

## 2. Assistant — 2026-10-23T20:23:42.594Z

I'll check three things in the code before revising, since several of the review points depend on them: the Kafka consumer's group settings (for the rebalance conditions and startup order), what `code_state()` records (for launch-time code identity), and which timestamps the launcher writes (for monotonic step intervals).

## 3. Assistant — 2026-10-23T20:23:45.692Z

### Tool call: Bash

```
{
  "command": "echo \"=== kafka.py consumer settings\" && grep -n -E '\"(client\\.id|group\\.id|group\\.protocol|group\\.instance\\.id|partition\\.assignment\\.strategy|session\\.timeout\\.ms|heartbeat\\.interval\\.ms|max\\.poll\\.interval\\.ms|enable\\.auto\\.commit|auto\\.offset\\.reset)\"' src/etf_risk/jobs/kafka.py; echo \"=== provenance.code_state\" && grep -n -A14 '^def code_state' src/etf_risk/provenance.py | head -24; echo \"=== launcher result fields\" && grep -n -o -E '\"[a-z_]+(_mono|_utc|_s|_bytes)?\":' src/etf_risk/jobs/launcher.py | sort -u -t: -k2 | head -40",
  "description": "Read Kafka consumer settings, code_state and launcher result fields"
}
```

## 4. User — 2026-10-23T20:23:46.380Z

### Tool result

```
=== kafka.py consumer settings
59:    return {"bootstrap.servers": bootstrap, "group.id": group, "enable.auto.commit": False,
60:            "enable.auto.offset.store": False, "auto.offset.reset": "earliest", "group.protocol": "classic",
61:            "session.timeout.ms": _ms(timing.session_timeout), "heartbeat.interval.ms": _ms(timing.heartbeat_interval),
62:            "max.poll.interval.ms": _ms(timing.max_poll_interval), "socket.timeout.ms": _ms(timing.socket_timeout)}
=== provenance.code_state
56:def code_state() -> dict:
57-    head = _git("rev-parse", "HEAD")
58-    status = _git("status", "--porcelain", "--untracked-files=all", "--", "src", "pyproject.toml", "uv.lock")
59-    if head:
60-        source, commit, clean = "git", head, (status == "") if status is not None else None
61-    elif os.environ.get(BUILD_COMMIT_ENV):
62-        source, commit = "build", os.environ[BUILD_COMMIT_ENV]
63-        clean = {"true": True, "false": False}.get(os.environ.get(BUILD_CLEAN_ENV, "").lower())
64-    else:
65-        source, commit, clean = "unknown", "unknown", None
66-    lock = REPO_ROOT / "uv.lock"
67-    return {
68-        "git_commit": commit,
69-        # False means the code that ran is not exactly the recorded commit; source_sha256 identifies it.
70-        "git_worktree_clean": clean,
=== launcher result fields
308:"__main__":
69:"clock_mismatch":
11:"deadline":
70:"deadline_passed":
137:"ended":
69:"eof":
252:"exited":
70:"launch_failed":
171:"launcher":
137:"lingering":
69:"lock_busy":
136:"lock_wait_s":
11:"monotonic":
70:"no_handshake":
135:"outcome":
137:"peak_rss_bytes":
135:"pid":
211:"reason":
135:"returncode":
11:"seq":
70:"signaled":
136:"started_at_utc":
70:"terminated":
69:"timeout":
171:"worker":
```

## 5. Assistant — 2026-10-23T20:24:00.226Z

### Tool call: Bash

```
{
  "command": "sed -n '128,142p' src/etf_risk/jobs/launcher.py; echo \"...\"; grep -n -E 'step_started_at_utc|tree_ended_at_utc|monotonic\\(\\)' src/etf_risk/jobs/launcher.py | head -12; echo \"=== code_state (rest)\"; sed -n '70,80p' src/etf_risk/provenance.py",
  "description": "Show the launcher's result record and the rest of code_state"
}
```

## 6. User — 2026-10-23T20:24:00.816Z

### Tool result

```
        if not self.eof and timeout > 0:
            select.select([self.fd], [], [], timeout)


class Launcher:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.result: dict = {"outcome": None, "returncode": None, "pid": os.getpid(),
                             "started_at_utc": datetime.now(timezone.utc).isoformat(), "lock_wait_s": None,
                             "peak_rss_bytes": 0, "ended": None, "lingering": None}
        self.lines = Lines(sys.stdin.fileno())
        self.watchdog: Watchdog | None = None
        self.stop_requested = False
        self.registry = processes.Registry(args.registry)
        self.lock_fd: int | None = None
...
12:  time.monotonic() when it wrote the line;
149:        now = time.monotonic()
163:        deadline = time.monotonic() + HANDSHAKE_TIMEOUT
164:        while time.monotonic() < deadline:
167:                first, now = lines[0], time.monotonic()
186:        start = time.monotonic()
195:            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
197:                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
203:            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
204:                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
207:        self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
217:        deadline = time.monotonic() + self.args.drain
=== code_state (rest)
        "git_worktree_clean": clean,
        "code_source": source,
        "image_id": os.environ.get(IMAGE_ID_ENV) or None,
        "source_sha256": {key: sha256_file(path) for key, path in source_files().items()},
        "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
    }
```

## 7. Assistant — 2026-10-23T20:24:07.595Z

### Tool call: Bash

```
{
  "command": "grep -rn -E 'step_started_at_utc|tree_ended_at_utc|launcher\\.json' src/etf_risk/jobs/ | cut -c1-200 | head -12",
  "description": "Find where step interval timestamps are written"
}
```

## 8. User — 2026-10-23T20:24:08.073Z

### Tool result

```
src/etf_risk/jobs/launcher.py:236:                self.result["step_started_at_utc"] = datetime.now(timezone.utc).isoformat()
src/etf_risk/jobs/launcher.py:258:            self.result["tree_ended_at_utc"] = datetime.now(timezone.utc).isoformat()   # no member left
src/etf_risk/jobs/pipeline.py:241:        result_path = logs / f"{name}.launcher.json"
```

## 9. Assistant — 2026-10-23T20:38:02.382Z

### Tool call: Write

````
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md",
  "content": "# Recovery experiments (E1, E2): outline\n\nAuthor: _to be written by the author after review. Beyond spec §11, the only decisions by the\nauthor so far are the review requirements in 1.1._\n\n_Drafted with Claude Code (Opus 5.5) on 2026-10-23 at the author's request, while M2's validation\nwas running, and revised the same day from the author's review (revision 1; history at the end).\nThis is an outline for review, not a Part A: every case, metric, check and query in it is Claude\nCode's proposal unless it cites spec §11, the M2 code or the author's requirements in 1.1.\nRepetitions, deadlines and memory thresholds are left open until M2's final report (section 8).\nSpec §11 gives the experiments to the project author, with tutoring; section 10 lists what the\nauthor would decide or write. Sources: spec §11, [worker-pipeline.md](worker-pipeline.md),\n[job-table.md](job-table.md) and [job-queue.md](job-queue.md) as they stood in the M2 worktree on\n2026-10-23, uncommitted and still subject to change; the code at `d2d8615`\n(`feature/worker-pipeline`); and `tests/test_jobs_live_pipeline.py`, also uncommitted there. Nothing\nwas run for this outline: the SQL in section 7 and the fixture in Appendix A have not been run, and\nthe fixture's expected results were traced by hand._\n\n## 1. Questions and scope\n\nSpec §11 asks two questions of the job queue:\n\n- **E1.** Does each job accept at most one result, and does every successfully completed job have\n  exactly one, even when jobs execute more than once?\n- **E2.** After a worker crash (before or after its claim), a broker restart or a database restart,\n  how long until the job runs again and finishes, and is any job lost or accepted twice?\n\nIt plans to inject each failure case on purpose and to record detection and recovery times,\nexecutions per job, accepted results per job and lost jobs. An accepted result counts as correct\nwhen its run passes every check (§6) and matches a reference run by content.\n\nThe token guards alone keep the guarantee ([job-table.md](job-table.md)); the time settings decide\nonly when a takeover may happen. E1 therefore tests the guards under real failures, and E2 measures\nwhat the time settings and the recovery paths cost.\n\n**Relation to M2's acceptance runs.** `tests/test_jobs_live_pipeline.py` has eight test functions,\nten cases with its three kinds of database stall. Each case runs once on a shorter clock (lease\n24 s, renewals every 4 s, session timeout 10 s; \"M2's clock\" below), ending with `check()` where the\njob is meant to succeed. E1 and E2 differ in three ways: each case is repeated (8.1), the clock is\nthe one 8.2 decides, and every injection leaves records from which times and counts are computed\n(section 5). The checks in `check()` are reused (6.2, 6.5).\n\n### 1.1 Required by the author's review (2026-10-23)\n\nThe author's review of the first draft set these requirements. How each is met is Claude Code's\nproposal, in the sections named.\n\n1. Deadlines are explicit in the records and the queries. On-time completion, late completion and\n   unfinished jobs are kept apart, and a later success never erases a deadline miss (4.2, 4.3, Q2).\n2. Database acceptance correctness is separate from event-log completeness. A crash after the\n   acceptance commits but before its event is written is covered (W5a). Repeated reports of one\n   attempt are not multiple accepted results (6.2, 6.4, Q1, Q3a).\n3. No deliberately crashed attempt is required to leave the artifacts of a successful one. Code\n   identity is recorded at each process launch. A missing process interval is unknown, never proof\n   of no overlap (2.3, 6.1, 6.5).\n4. Durations come from same-host monotonic timestamps. Recovery latency is marked not applicable\n   for failures injected after acceptance (4.1, section 5).\n5. The recovery predictions include Kafka's assignment and rebalance conditions, and the worker\n   startup order is fixed (2.4, 3.2).\n6. The full identity of each report is checked, including `store_id` and `worker_id` (6.4, Q3a,\n   Q3b).\n7. The deadline observation, quiescence and a consistent snapshot for the SQL and the export are\n   defined (4.3–4.5).\n\nAlso: reference runs take the host lock (2.2); no pooled rule-of-three claim (8.1); small SQL\nfixtures for late completion, missing acceptance events, duplicate reports and wrong-worker reports\n(Appendix A); every case and every failed outcome stays visible (3.1, section 10); documents only\nfor now, and no formal experiment is run.\n\n## 2. Setup and batch protocol (proposal)\n\n### 2.1 Services, jobs and controls\n\n- **Services and processes**, as in the README runbook: MySQL 8.4.13 and Kafka 4.3.1 from\n  [docker/compose.yaml](../docker/compose.yaml); the reconciler and two workers, A and B, as native\n  processes; one job at a time on this machine (spec §11).\n- **A session harness** (M3 code, not written) submits the jobs, injects the failures, takes the\n  deadline observations, restarts workers (2.4) and keeps the records (section 10).\n- **Batches.** Each batch starts on fresh containers (spec §11 asks it of MySQL) and ends with the\n  final snapshot (4.5), before `docker compose down -v`.\n- **Jobs.** The two parameter sets of M2's acceptance runs: kind `calendar-year` and kind `rolling`,\n  both with stride 21, on snapshot `full-2026-10-12`, with `submit`'s default of 3 attempts. Which\n  cases use which set, and how many jobs, depends on 8.1 and on the job durations M2 reports.\n- **Controls.** Jobs with no injection (case C0) give each parameter set's failure-free time to\n  finish, in the same batch.\n\n### 2.2 Reference runs\n\nOne direct run of the three CLIs per parameter set, under the host execution lock: the batch's lock\nfile and registry, taken as a launcher takes them (an exclusive `flock`, the wait until no earlier\ntree survives, and an entry in the registry, so that a later launcher also waits for the reference\nrun's survivors). A reference run therefore cannot overlap a worker's step, and its interval enters\nthe overlap check (6.5). The reference runs come before the workers start, so that they delay no\nmeasured step. The wrapper that takes the lock is M3 code and would reuse the launcher's lock and\nregistry code (section 10).\n\n### 2.3 Code identity\n\nEvery process of a batch records its code identity when it starts, in its first event: each worker\nstart (restarts included), the reconciler, each `submit`, and each step launch (in `step_started`).\nThe identity is the `source_sha256` and `uv_lock_sha256` of `provenance.code_state()`, compared as\nin the earlier experiments; the commit is only reported. The harness records the same at the start\nand the end of the batch. At `d2d8615` no start event carries it (section 10). A crashed attempt\nwrites no `attempt.json`, so the identity is never read from that file; it is read only for accepted\nattempts, to find their run folder (6.2).\n\n### 2.4 Worker startup order and the partition\n\nThe topic has one partition, so the one group member that owns it gets every delivery.\n[kafka.py](../src/etf_risk/jobs/kafka.py) at `d2d8615` sets no `client.id`, `group.instance.id` or\n`partition.assignment.strategy`, so the defaults apply: the range assignor, which orders members by\nmember id, and member ids that start with librdkafka's default client id, `rdkafka`, followed by a\nrandom suffix (to verify against Kafka 4.3.1). With two live members the owner after a rebalance is\ntherefore arbitrary. M2's tests work around this by starting B only after A has claimed a job\n(`claimed_by_a`, whose docstring says so).\n\nProposed order for each batch:\n\n1. `services ready`, `init-db` and `create-topic` on the fresh containers;\n2. the reference runs (2.2);\n3. the reconciler;\n4. worker A, then a wait for its assignment event (section 10);\n5. worker B, then a wait until the rebalance that its join causes has completed, with the owner\n   recorded;\n6. the first job.\n\n**Restart rule.** A killed worker is started again only once its job has finished (read from the\ntable); since jobs run one at a time, the other worker is then idle. The harness waits for the\nrebalance that the restart causes and records the owner before the next job. A worker that was\nstopped and then fenced (W6, W7) is first stopped with SIGTERM once its `fenced` event appears (its\nattempt is no longer its own, so the stop writes nothing) and is then started again under the same\nrule. The only rebalance inside a recovery window is therefore the one the failure causes.\n\n**Who owns the partition.** With `client.id` set to the worker id (Q-E), the range assignor would\ngive the partition to A whenever A is live. Without it, the harness reads the owner from the\nassignment events. Either way the harness injects into the worker that claimed the job, never into\na worker chosen by name.\n\n### 2.5 One job at a time\n\nThe harness submits one job, applies its case, takes its deadline observation (4.3), and waits until\nthe job has finished or its drain limit (8.2) has passed. Only then does it restart a worker (2.4)\nand start the next job. A job still unfinished at its drain limit ends the batch (4.4), and the\ninjections not yet made are recorded as not run (section 10).\n\n## 3. Failure cases\n\n### 3.1 Cases\n\nEach injection targets one job, in one phase of one attempt. The harness confirms that the injection\nlanded in its phase, from the event logs (for W3: after the attempt's `step_started` for\n`spark_pipeline` and before its `step_ended`) or, for W5a, from the table. An injection that landed\nelsewhere is recorded with the phase it hit and does not count for its case.\n\n| Case | Injection | How | For | Expected path, from the design | Claims / accepted | In M2's live tests |\n|---|---|---|---|---|---|---|\n| C0 | none (control) | — | E2 | claim, run, accept | 1 / 1 | yes, both parameter sets |\n| W1 | SIGKILL of the worker after a delivery, before its claim | hook at `before_claim` (Q-A) | E2 | the offset stays uncommitted; after the session timeout the standby gets the partition and the message, and claims attempt 1 | 1 / 1 | no; offline, at the worker's fault points |\n| W2 | SIGKILL after the claim, before the offset commit | hook at `after_claim` | E1, E2 | the redelivery to the standby is refused (lease held) and committed; the lease expires; the reconciler requeues and republishes; attempt 2 | 2 / 1; attempt 1 ran no step | no; with the simulated pipeline (`test_a_crash_between_claim_and_commit`) |\n| W3 | SIGKILL during `spark_pipeline` | signal, once the step's log exists (as in M2) | E1, E2 | the launcher reads EOF and ends the tree; the lease expires; requeue; attempt 2 | 2 / 1; attempt 1 partial | yes, once |\n| W4 | SIGKILL after the pipeline, before acceptance | hook at `after_pipeline` | E1, E2 | attempt 1's complete folder is never accepted; the lease expires; requeue; attempt 2 runs in full | 2 / 1; two complete executions | no |\n| W5a | SIGKILL after the acceptance commits, before its `accepted` event | hook at a new fault point between `accept_result`'s return and the event (Q-A) | E1 | nothing to recover; the table holds the acceptance and the log lacks its event (6.4) | 1 / 1; no report | no |\n| W5b | SIGKILL after the `accepted` event | hook at `after_accept` | E1 | nothing to recover: the offset was committed at the claim | 1 / 1 | no |\n| W6 | SIGSTOP of the worker during `spark_pipeline`; SIGCONT after the takeover | signals | E1 | the watchdog ends the stopped worker's tree before its lease expires; requeue; the standby claims attempt 2; after SIGCONT the old worker's renewal is refused, it is fenced, and the harness stops it (2.4) | 2 / 1 | yes, once |\n| W7 | SIGSTOP of the worker's whole tree (worker, launcher, Spark); SIGCONT later | signals | E1 | the replacement's step waits for the host lock while the stopped tree survives; after SIGCONT the stopped launcher, past its deadline, ends its tree, and the old worker is fenced and stopped. A stop longer than the replacement's lock wait fails that attempt as retryable | 2 or 3 / 1 | yes, once |\n| K1 | Kafka restart while a step runs | `docker compose restart kafka` | E2 | the running job goes on (the worker does not poll during a run); the next delivery waits for the group (3.2) | 1 / 1 | yes, once |\n| K2 | a submit while Kafka is stopped | stop Kafka, submit, start Kafka | E2 | the confirmation times out (10 s) and `published_at` stays empty; once Kafka is back and the 30 s grace has passed, the reconciler publishes the job | 1 / 1 | no; an unreachable broker's confirmation in `test_jobs_kafka.py` |\n| D1 | MySQL restart while a step runs | `docker compose restart mysql` | E2 | renewals fail and are tried again; back before F: the attempt goes on; otherwise the worker fences itself, the watchdog ends the tree, and the job is requeued once MySQL is back | 1 or 2 / 1 | yes, once (also a table lock and a pause) |\n| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`) and the job runs again after its lease expires | 1 or 2 / 1 | no; a lost COMMIT reply offline (`test_jobs_reconnect.py`) |\n| X1 | the job id published again, while the job runs and after it succeeded | harness publishes | E1 | each extra delivery is refused (lease held, then succeeded) and committed; no new attempt | 1 / 1 | no; refusals offline (`test_jobs_queue.py`) |\n\nAll 14 cases are kept. How many injections each gets, and their order, is 8.1's decision; a case\nthat has no injection method yet (Q-A) is recorded as not run, never dropped.\n\n### 3.2 Expected times and Kafka conditions\n\nIn the symbols of [worker-pipeline.md](worker-pipeline.md) and [job-queue.md](job-queue.md): L the\nlease (60 s at the defaults), R the renewal interval (10 s), F the worker's fence deadline (L − M\nafter its last renewal began, M = 10 s), G the kill grace (7 s), P the reconciler interval (5 s), S\nthe session timeout (15 s), h the heartbeat interval (3 s), g the publication grace (30 s), and T a\njob's failure-free time to finish (from C0).\n\n| Case | Detection event | From the injection to the next claim | Kafka condition |\n|---|---|---|---|\n| W1 | the standby's `delivered` | about S − h to S + h, plus a poll (1 s) | the killed worker owned the partition; its session expires S − h to S after the kill, since its last heartbeat came up to h before it; the standby is idle (2.4), learns of the rebalance at its next heartbeat and rejoins at its next poll |\n| W2, W4 | the reconciler's `requeued` | L to L + P (the lease was just set or renewed), plus a delivery | the standby owns the partition from about S + h after the kill, before the requeue: S + h + 1 s < L − R holds at the defaults (19 < 50 s) and at M2's clock (14 < 20 s) |\n| W3, W6 | `requeued` | between about L − R and L + P, plus a delivery | as W2; a stopped worker (W6) stops heartbeating, so it loses the partition as a dead one does |\n| W7 | `requeued` | as W3; then the replacement's step waits for the host lock until the stopped tree is resumed and ended | as W6 |\n| K1 | — (the job's attempt goes on) | n/a | the group re-forms after the restart; a member busy with a job delays a rebalance until its next poll, so the next delivery may wait for the running job to end; without Q-E the owner afterwards is arbitrary |\n| K2 | the reconciler's `published` | the later of Kafka's return and g after the submit, plus up to P, plus a delivery | a delivery needs an owner again after the restart |\n| D1 | `renewal_failed`; then `renewed`, or else `requeued` | none if MySQL is back before F; otherwise once the lease has expired and MySQL is back, plus up to P, plus a delivery | none: the owner stays, and a requeued job returns to it |\n| D2 | `retry` of `accept_result`; then `accepted`, or else `failed_after_ack` and `requeued` | as D1 | as D1 |\n| W5a, W5b, X1 | — | n/a: after the acceptance, or no failure | a killed worker (W5a, W5b) loses the partition about S after the kill; this delays only the next job, which starts after the owner is recorded (2.4) |\n\nThe time to finish adds about T wherever a new attempt starts. These bounds hold only under the\nconditions in the last column, and they become predictions only after 8.2 fixes the clock and the\nauthor approves them.\n\n## 4. Clocks, deadlines and the final snapshot\n\n### 4.1 Clock\n\nEvery duration is a difference of two `time.monotonic()` readings on this host: the `mono` field of\nthe events ([events.py](../src/etf_risk/jobs/events.py)), the harness's own readings for injections\nand observations, and the launcher's step times once it records them (section 10). On macOS this\nreads a system-wide clock; the launcher's handshake already checks that the worker and its launchers\nagree, and the harness checks each process it starts: the `mono` of the process's first event must\nlie between the harness's readings just before it started the process and just after it read that\nevent. The clock pauses while the host sleeps, so the host must not sleep during a batch (for\nexample under `caffeinate`).\n\n`ts` (UTC) orders events for people and relates them to the tables' wall-clock columns; it is never\nused for a duration. At the start and the end of each batch the harness records `ts` and `mono`\ntogether. If their elapsed times differ by more than the tolerance in 8.2, the host slept or the\nwall clock stepped, either of which would also move the tables' wall-clock leases, and the batch\nfails validity (6.1).\n\n### 4.2 Deadlines\n\nEach job has an explicit deadline, which the harness records in `batch_jobs` when the job's\nreference instant occurs:\n\n- `deadline_from`: `injection` for an injected job (its t_inj), `submit` for a control (the start of\n  its `submit` call);\n- `deadline_s`: the case's D (8.2);\n- `deadline_mono`: the harness's `mono` at the reference instant, plus D;\n- `max_lag_s`: how late the deadline observation may end and still show an on-time success (4.3,\n  8.2).\n\nQ2 classifies every job from its deadline observation (4.3) and the final snapshot (4.5):\n\n| Class | Rule |\n|---|---|\n| on time | succeeded in the deadline observation, which ended no later than `deadline_mono + max_lag_s` |\n| late | not succeeded in an observation that began at or after `deadline_mono`, and succeeded in the final snapshot |\n| unfinished | queued or running in the final snapshot |\n| failed | failed in the final snapshot; the observation shows whether it had failed by the deadline |\n| missing | no row in the final snapshot |\n| succeeded, deadline not observed | succeeded at the end, with no valid observation: none, a failed read, a success seen too late, or a miss seen before the deadline |\n\nA late job stays late: the miss is fixed by its observation, and the later success does not change\nit. Only `on time` counts as meeting the deadline. The final snapshot comes after every drain limit,\nwhich comes after every deadline, so an unfinished job has also missed its deadline.\n\n### 4.3 The deadline observation\n\nAt `deadline_mono` the harness reads the job's row in its own connection to MySQL, as one\nconsistent snapshot:\n\n```sql\nSET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;\n-- observed_from_mono: the harness's time.monotonic() just before the next statement\nSTART TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;\n-- observed_to_mono: just after it returned; InnoDB took the snapshot in between\nSELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = :job_id;\nCOMMIT;\n```\n\n- There is one observation per job, never repeated. A read that fails (for example while MySQL is\n  down in D1 or D2) is recorded with no status; the job's class then rests on the final snapshot\n  alone, or is `succeeded, deadline not observed`.\n- A terminal status never changes. A success seen in a snapshot that ended by\n  `deadline_mono + max_lag_s` is therefore on time within that lag, and a miss seen in a snapshot\n  that began at or after `deadline_mono` stays a miss.\n- The observation lag, `observed_to_mono − deadline_mono`, is reported for every job.\n\n### 4.4 Quiescence\n\nA batch is quiescent when nothing can write to the job tables any more:\n\n- every job of the batch has finished, or the last job's drain limit has passed (2.5);\n- the harness has ended every process that writes to the tables: the workers and the reconciler\n  (each `submit` has exited). It uses SIGKILL, so that no job changes state on the way out (a\n  graceful stop would requeue a running attempt); each worker's launcher then ends its tree;\n- none of those processes is alive, no attempt's process is left, and MySQL's process list shows no\n  client connection besides the harness's own, so no transaction of theirs can still commit.\n\n### 4.5 The final snapshot\n\nAfter quiescence, in this order:\n\n1. `services peaks`, before any query, so that the queries add nothing to the peaks;\n2. `status --check`;\n3. the cross-check: the harness's records loaded into TEMPORARY tables of one session; then\n   `START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY`; Q0, Q1, Q2, Q2b, Q3a and Q3b\n   (section 7); `COMMIT`; each result saved as CSV;\n4. `export`;\n5. Q0 again.\n\nQ0's fingerprint from step 3, the same four numbers computed from the export's `jobs.json` and\n`job_attempts.json`, and Q0 from step 5 must be equal. Every store operation inserts a `jobs` row or\nraises its `version`, so a write between the steps would show. If they differ, the cross-check and\nthe export did not read the same state, and the batch fails validity (6.1).\n\n## 5. Metrics\n\nDurations are monotonic (4.1); t_inj is the harness's `mono` at the injection.\n\n| Metric | Definition | Source |\n|---|---|---|\n| detection time | t_inj to the case's detection event (3.2) | injection log, event logs |\n| time to re-run | t_inj to the `claimed` event of the job's next attempt (W1: its first) | event logs |\n| time to finish | t_inj to the job's `accepted` event; unknown if that event is missing | event logs |\n| recovery overhead | from the harness's start of `submit` to the `accepted` event, minus the median of the same parameter set's C0 jobs in the batch | harness log, event logs |\n| deadline class | 4.2 | Q2 |\n| claims per job | rows in `job_attempts` | Q1, `n_claims` |\n| executions per job | attempts with a `step_started` for `windows`; complete executions: attempts whose folder has a `manifest.json`, written only after the result rule held. Counted where present, required of none | event logs, attempt folders |\n| accepted results per job | accepted attempts in the table; never the workers' reports (6.4) | Q1, `n_accepted` |\n| reports per job | the matching reports of the accepted attempt, and the distinct attempts reported | Q3a |\n| unfinished or missing jobs (E2's lost jobs) | Q2's `unfinished` and `missing`, with each job's queue state: status, attempt number, recorded publication, lease. An observation cannot tell a job lost for good from a slow one; the state shows which recovery path was still open | Q2 |\n| wasted step time | the step time of attempts that were not accepted; a step without a complete launcher record adds an unknown, not zero | launcher records |\n| fencing | `renewal_refused` and `fenced` events; the watchdog's end of a tree | worker logs, launcher records |\n| liveness | `serve_restarted`, `retry`, `rewound`, `gave_up`, `failed_after_ack`, `consumer_error` and `pass_failed`, per process | event logs |\n| partition owner | the owner before and after each case | assignment events (section 10) |\n| memory | MySQL's and Kafka's `memory.peak` per batch; each step's `peak_rss_bytes` from its launcher record, which normally exists for a crashed attempt too, since the launcher outlives a killed worker (a missing record is unknown); the worker process's own peak | `services peaks`; launcher records; sampled by the harness |\n\nWhich recovery metrics apply:\n\n| Case | Detection time | Time to re-run | Time to finish, overhead |\n|---|---|---|---|\n| C0 | n/a: no failure | n/a: no failure | yes (the control) |\n| W1–W4, W6, W7 | yes | yes | yes |\n| W5a, W5b | n/a: after acceptance | n/a: after acceptance | n/a: after acceptance |\n| K1 | n/a for the job; the broker's recovery is measured from the restart to the next `delivered` | n/a: the attempt goes on | yes |\n| K2 | yes | yes | yes |\n| D1, D2 | yes | yes if a new attempt started; otherwise n/a: the attempt went on | yes |\n| X1 | n/a: no failure | n/a: no failure | yes (as a control) |\n\n`n/a` is recorded with its reason, never as zero or as a blank. Whether an injection came after the\nacceptance is read from its verified phase (3.1): for W5a the acceptance is in the table and no\nlater attempt exists; for W5b the `accepted` event precedes t_inj.\n\n## 6. Checks\n\n### 6.1 Validity\n\nValidity decides what counts, like the acceptance criteria of the earlier experiments:\n\n- each injection landed in its phase (3.1), and the planned injections were made or recorded as not\n  run, with the reason;\n- one code identity for every process of the batch, equal to the harness's at the start and the\n  end (2.3);\n- the snapshot's input checksums are unchanged after the batch;\n- the clock check and each process's same-clock check passed (4.1);\n- the three fingerprints of the final snapshot are equal (4.5);\n- the machine-state rules held (8.3).\n\nA failed validity check is recorded with its batch. Such a batch does not count toward the answers\nto E1 and E2, as in the earlier experiments, but its records and outcomes stay visible (section 10).\n\n### 6.2 Database acceptance correctness (answers E1)\n\nFrom the job tables and the run folders only; the event logs play no part:\n\n1. Q1: `n_accepted` is 1 for each succeeded job and 0 for every other, and the verdict is `ok`.\n2. `status --check` exits 0 (the store's seven `INVARIANT_QUERIES`), and the export's\n   `invariant_violations.json` is empty.\n3. The accepted attempt's `result_digest` equals `runs.folder_digest` of its run folder,\n   recomputed after the batch.\n4. The accepted run passes the result rule again from its files\n   ([worker-pipeline.md](worker-pipeline.md), \"Accepting a result\") and equals the reference run by\n   content: each table compared with `compare_tables` on `TABLE_KEYS`, as `check()` does.\n\nThese are required of accepted attempts only. A deliberately crashed attempt needs no\n`attempt.json`, `manifest.json`, `run.json` or `verify.json`; its folder is left as it is, referenced\nnowhere, and listed by `cleanup` (a dry run).\n\n### 6.3 Timeliness and lost jobs (answers E2)\n\nQ2's class for every job (4.2). `late` counts as a deadline miss although the job succeeded;\n`unfinished` and `missing` are E2's lost jobs.\n\n### 6.4 Event-log completeness and report identity\n\nThe `accepted` events are the workers' reports. They do not decide acceptance; the table does. So:\n\n- a missing `accepted` event for an accepted attempt is a gap in the log, expected in W5a. It is\n  reported as a record defect, never as a lost or unaccepted result;\n- repeated reports of one attempt are one accepted result reported more than once, never multiple\n  accepted results;\n- each report must carry the full identity of an accepted attempt of this batch: the `store_id` in\n  `job_store`, the `job_id` and `attempt_number`, the `worker_id` that claimed that attempt\n  (`job_attempts.worker_id`), and its `result_digest`. The collector also checks that the report's\n  `pid` equals that of the `claimed` event of the same attempt, in the same log;\n- a report for an attempt that is not accepted, or from another worker, contradicts the table. It\n  does not change E1's answer, which comes from 6.2, but it is reported next to it, since it would\n  mean that a worker's belief and the table differ.\n\nQ3a gives the view per job, Q3b the view per report.\n\n### 6.5 Other outcome checks\n\n- **No overlapping Spark steps.** Every step that started (each `step_started` event) and each\n  reference run needs a complete interval, from its start to the end of its tree, in its launcher\n  record. A missing or incomplete record makes the batch's verdict `unknown`, never `no overlap`; the\n  verdict is `no overlap`, `overlap`, or `unknown` with the steps that lack an interval. Intervals\n  are compared in monotonic time once the launcher records it. At `d2d8615` its records hold UTC\n  times only (`step_started_at_utc`, `tree_ended_at_utc`), and a comparison of those holds only with\n  a passed clock check (4.1).\n- **Nothing left.** After quiescence no process of any attempt is left, and no Spark scratch beyond\n  what was there before the batch (as `check()`).\n\n## 7. Draft SQL\n\n_Drafted with Claude Code; not run._\n\n**What it adds.** The store's seven `INVARIANT_QUERIES` list the jobs that break an invariant, and\n`status --check` exits 1 if any does. Between them they already imply at most one accepted attempt\nper job in the database. The schema alone does not: `jobs.accepted_attempt` names one attempt, but\nno constraint stops two `job_attempts` rows of one job from both being `accepted`. Q1 restates that\npart as counts per job, from the tables alone (6.2). The other queries add what the store cannot\nsee: each job's deadline and its observation (Q2, 6.3), jobs the harness did not record (Q2b), and\nthe workers' reports against the table (Q3a, Q3b, 6.4). The overlap of Q1 with the invariant\nqueries is deliberate: a second reading of the same rows, by queries the store does not run.\n\n**Where it runs:** in MySQL, in the final snapshot (4.5). The harness's records are loaded into\nTEMPORARY tables of the cross-check's own session, so the store's tables are untouched. MySQL\ndocuments that a TEMPORARY table cannot be referred to more than once in the same query, so each\nquery below names each of them at most once. `worker_id` is compared with `CAST(... AS BINARY)`,\nbyte for byte, since the store's `worker_id` column, unlike its other identifiers, has no binary\ncollation. Written for MySQL 8.4, with CTEs, joins and CASE only.\n\n```sql\n-- The harness's records, in the cross-check's session only.\n-- batch_jobs: each job the harness submitted in this batch, its case and its deadline (4.2).\nCREATE TEMPORARY TABLE batch_jobs (\n    job_id              BIGINT UNSIGNED NOT NULL,\n    case_id             VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,\n    deadline_from       VARCHAR(9) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,  -- injection, submit\n    deadline_s          DOUBLE NOT NULL,\n    deadline_mono       DOUBLE NOT NULL,\n    max_lag_s           DOUBLE NOT NULL,\n    PRIMARY KEY (job_id)\n);\n-- deadline_observations: one row per job (4.3); status is NULL when the read failed.\nCREATE TEMPORARY TABLE deadline_observations (\n    job_id              BIGINT UNSIGNED NOT NULL,\n    observed_from_mono  DOUBLE NOT NULL,\n    observed_to_mono    DOUBLE NOT NULL,\n    status              VARCHAR(16) CHARACTER SET ascii COLLATE ascii_bin NULL,\n    attempt_number      INT UNSIGNED NULL,\n    accepted_attempt    INT UNSIGNED NULL,\n    PRIMARY KEY (job_id)\n);\n-- worker_accepts: one row per `accepted` event in the worker logs: store_id and worker_id from the\n-- log's context, pid, and the event's job_id, attempt and digest.\nCREATE TEMPORARY TABLE worker_accepts (\n    store_id            CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,\n    worker_id           VARCHAR(128) NOT NULL,\n    pid                 INT UNSIGNED NOT NULL,\n    job_id              BIGINT UNSIGNED NOT NULL,\n    attempt_number      INT UNSIGNED NOT NULL,\n    result_digest       CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL\n);\n```\n\n```sql\n-- Q0. Snapshot fingerprint (4.5): equal in the cross-check, in the export and after the export.\nSELECT\n    (SELECT COUNT(*) FROM jobs) AS n_jobs,\n    (SELECT COALESCE(SUM(version), 0) FROM jobs) AS sum_version,\n    (SELECT COUNT(*) FROM job_attempts) AS n_attempts,\n    (SELECT COALESCE(SUM(renewals), 0) FROM job_attempts) AS sum_renewals;\n```\n\n```sql\n-- Q1. Database acceptance correctness (6.2), one row per job, from the job tables alone.\nWITH attempts AS (\n    SELECT\n        job_id,\n        COUNT(*) AS n_claims,\n        SUM(CASE WHEN outcome = 'accepted' THEN 1 ELSE 0 END) AS n_accepted,\n        SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) AS n_failed,\n        SUM(CASE WHEN outcome = 'expired' THEN 1 ELSE 0 END) AS n_expired,\n        SUM(CASE WHEN outcome = 'running' THEN 1 ELSE 0 END) AS n_running,\n        COUNT(DISTINCT worker_id) AS n_workers,\n        MIN(CASE WHEN outcome = 'accepted' THEN attempt_number END) AS accepted_number,\n        MIN(CASE WHEN outcome = 'accepted' THEN result_digest END) AS accepted_digest\n    FROM job_attempts\n    GROUP BY job_id\n)\nSELECT\n    j.job_id,\n    j.status,\n    j.attempt_number,\n    j.max_attempts,\n    j.accepted_attempt,\n    COALESCE(a.n_claims, 0) AS n_claims,\n    COALESCE(a.n_accepted, 0) AS n_accepted,\n    COALESCE(a.n_failed, 0) AS n_failed,\n    COALESCE(a.n_expired, 0) AS n_expired,\n    COALESCE(a.n_running, 0) AS n_running,\n    COALESCE(a.n_workers, 0) AS n_workers,\n    a.accepted_digest,\n    CASE\n        WHEN COALESCE(a.n_accepted, 0) > 1\n            THEN 'more than one accepted attempt'\n        WHEN j.status = 'succeeded' AND COALESCE(a.n_accepted, 0) = 0\n            THEN 'succeeded without an accepted attempt'\n        WHEN j.status = 'succeeded' AND a.accepted_number <> j.accepted_attempt\n            THEN 'accepted_attempt names another attempt'\n        WHEN j.status <> 'succeeded' AND COALESCE(a.n_accepted, 0) = 1\n            THEN 'accepted attempt of a job that did not succeed'\n        WHEN COALESCE(a.n_claims, 0) <> j.attempt_number\n            THEN 'attempt rows differ from attempt_number'\n        WHEN j.status IN ('queued', 'running')\n            THEN 'not finished'\n        WHEN COALESCE(a.n_running, 0) > 0\n            THEN 'finished with an attempt still running'\n        WHEN j.status = 'failed'\n            THEN 'failed'\n        ELSE 'ok'\n    END AS verdict\nFROM jobs AS j\nLEFT JOIN attempts AS a ON a.job_id = j.job_id\nORDER BY j.job_id;\n```\n\n```sql\n-- Q2. Timeliness (4.2), one row per job the harness submitted.\nSELECT\n    b.case_id,\n    b.job_id,\n    j.status AS final_status,\n    d.status AS status_at_deadline,\n    ROUND(d.observed_to_mono - b.deadline_mono, 3) AS observation_lag_s,\n    j.attempt_number,\n    j.published_at,\n    j.lease_expires_at,\n    CASE\n        WHEN j.job_id IS NULL\n            THEN 'missing'\n        WHEN j.status IN ('queued', 'running')\n            THEN 'unfinished'\n        WHEN j.status = 'failed'\n            THEN 'failed'\n        WHEN d.status = 'succeeded' AND d.observed_to_mono <= b.deadline_mono + b.max_lag_s\n            THEN 'on time'\n        WHEN d.status <> 'succeeded' AND d.observed_from_mono >= b.deadline_mono\n            THEN 'late'\n        ELSE 'succeeded, deadline not observed'\n    END AS timeliness\nFROM batch_jobs AS b\nLEFT JOIN jobs AS j ON j.job_id = b.job_id\nLEFT JOIN deadline_observations AS d ON d.job_id = b.job_id\nORDER BY b.case_id, b.job_id;\n```\n\n```sql\n-- Q2b. Jobs in the table that the harness did not record, such as a submit that exited 75\n-- (outcome unknown) although its insert committed. Each needs an explanation.\nSELECT\n    j.job_id,\n    j.status\nFROM jobs AS j\nLEFT JOIN batch_jobs AS b ON b.job_id = j.job_id\nWHERE b.job_id IS NULL\nORDER BY j.job_id;\n```\n\n```sql\n-- Q3a. Event-log completeness (6.4), one row per succeeded job. Only this store's reports count,\n-- and a report matches only with the full identity of the job's accepted attempt.\nWITH reports AS (\n    SELECT\n        w.job_id,\n        COUNT(*) AS n_reports,\n        COUNT(DISTINCT w.attempt_number) AS n_reported_attempts,\n        SUM(CASE WHEN a.job_id IS NOT NULL AND w.attempt_number = j.accepted_attempt THEN 1 ELSE 0 END)\n            AS n_matching\n    FROM worker_accepts AS w\n    JOIN job_store AS s ON s.store_id = w.store_id\n    JOIN jobs AS j ON j.job_id = w.job_id\n    LEFT JOIN job_attempts AS a\n        ON a.job_id = w.job_id\n        AND a.attempt_number = w.attempt_number\n        AND a.outcome = 'accepted'\n        AND CAST(a.worker_id AS BINARY) = CAST(w.worker_id AS BINARY)\n        AND a.result_digest = w.result_digest\n    GROUP BY w.job_id\n)\nSELECT\n    j.job_id,\n    j.accepted_attempt,\n    COALESCE(r.n_reports, 0) AS n_reports,\n    COALESCE(r.n_matching, 0) AS n_matching,\n    COALESCE(r.n_reported_attempts, 0) AS n_reported_attempts,\n    CASE\n        WHEN COALESCE(r.n_reported_attempts, 0) > 1\n            THEN 'acceptance reported for more than one attempt'\n        WHEN COALESCE(r.n_matching, 0) = 0\n            THEN 'no matching report'\n        WHEN r.n_matching > 1\n            THEN 'one attempt reported more than once'\n        ELSE 'reported once'\n    END AS log_verdict\nFROM jobs AS j\nLEFT JOIN reports AS r ON r.job_id = j.job_id\nWHERE j.status = 'succeeded'\nORDER BY j.job_id;\n```\n\n```sql\n-- Q3b. Report identity (6.4), one row per report.\nSELECT\n    w.store_id,\n    w.worker_id,\n    w.pid,\n    w.job_id,\n    w.attempt_number,\n    CASE\n        WHEN w.store_id <> s.store_id\n            THEN 'other store'\n        WHEN a.job_id IS NULL\n            THEN 'no such attempt'\n        WHEN CAST(w.worker_id AS BINARY) <> CAST(a.worker_id AS BINARY)\n            THEN 'wrong worker'\n        WHEN a.outcome <> 'accepted'\n            THEN 'attempt not accepted'\n        WHEN w.result_digest <> a.result_digest\n            THEN 'wrong digest'\n        ELSE 'matches'\n    END AS report_verdict\nFROM worker_accepts AS w\nCROSS JOIN job_store AS s\nLEFT JOIN job_attempts AS a\n    ON a.job_id = w.job_id\n    AND a.attempt_number = w.attempt_number\nORDER BY w.job_id, w.attempt_number, w.worker_id, w.store_id;\n```\n\n**The per-case tally** is computed by the collector from the saved results of Q1–Q3b and the\ninjection log, with no SQL logic of its own: for each of the 14 cases, the injections planned, made,\nmissed and not run; the jobs per Q1 verdict, per Q2 class and per Q3a verdict; the reports per Q3b\nverdict; and the claims per job. Every case and every verdict value appears, with zeros.\n\n**Expected verdicts** (proposal), in a valid batch of the planned cases: Q1 `ok` for every job; Q3a\n`reported once` for every succeeded job except W5a's, which has `no matching report` and no report\nat all; Q3b `matches` for every report; Q2b no rows. Q2's classes depend on D (8.2).\n\n## 8. Decisions pending M2's final report\n\nLeft open on purpose. Each item names what it controls and the M2 results it waits for; no values\nare proposed. \"Deadlines\" is read here as the experiment's time settings and waits.\n\n### 8.1 Repetitions\n\n- **To decide:** injections per case in a batch; the number of batches; C0 jobs per batch and where\n  they go; the order of the cases (in blocks or interleaved).\n- **Waits for:** each parameter set's time to finish through the worker, and its spread; any case of\n  M2's acceptance runs that failed only sometimes.\n- **Already fixed:** one job at a time on this machine (spec §11), so a batch lasts about the sum of\n  its jobs' times to finish and recoveries. MySQL's limited memory headroom (spec §11) ties the\n  batch length to 8.3.\n- **Counts, not rates:** results are reported per case as counts (k of n injections). No rate,\n  probability or confidence bound is claimed, pooled across cases or per case: the injections are\n  not shown to be independent, and different cases are not alike.\n\n### 8.2 Deadlines\n\n[timing.py](../src/etf_risk/jobs/timing.py) calls its defaults \"the M2 drafts of spec §11\".\n\n- **The clock:** those defaults (lease 60 s, renewals every 10 s, fence margin 10 s, session timeout\n  15 s); a shorter clock with the same relations, like M2's; or another. `Timing.check()` refuses\n  inconsistent sets, and every E2 time scales with the choice (3.2).\n- **Step and attempt limits:** windows 120 s, spark_pipeline 600 s, verify 300 s and attempt 900 s.\n  They also set the lock wait (step limit + G + 30 s) and `max.poll.interval.ms` (attempt limit +\n  G + 60 s), which bounds the classic-protocol wait.\n- **Each case's deadline D** (4.2), counted from the injection, or from the start of `submit` for\n  C0.\n- **The observation lag** `max_lag_s` (4.3).\n- **The drain limit:** how long after a job's deadline the harness waits for it to finish before\n  ending the batch (2.5, 4.4).\n- **The harness's waits:** for the intended phase before an injection; how long a process stays\n  stopped (W6, W7); how long a service stays down (K2, D1, D2).\n- **The clock-check tolerance** (4.1).\n- **Waits for:** M2's measured step and attempt durations, the container restart times seen in its\n  runs, and any timing change in its final report.\n\n### 8.3 Memory thresholds\n\n- **Which budgets apply:** the MySQL (512 MiB) and Kafka (640 MiB) containers of spec §11. The\n  worker and its steps run natively, so the 2.5 GiB pipeline-container budget applies only if they\n  move into a container.\n- **When a batch stops or is flagged:** the share of its limit a container's `memory.peak` may reach\n  (spec §11 records MySQL at 511 of 512 MiB after about two hours of tests), and whether fresh\n  containers for each batch are required (spec §11: \"should\").\n- **Host state before each injection:** available memory and load, as in the earlier experiments'\n  machine-state rules, with Docker's VM holding 3.83 GiB of the 8 GiB.\n- **The worker's own memory:** it imports pandas and pyarrow.\n- **Waits for:** the peaks M2 reports for the worker, each step, MySQL and Kafka.\n\n## 9. Open design questions\n\nClaude Code's recommendation comes first in each; the author decides.\n\n- **Q-A. Injecting at the narrow points (W1, W2, W4, W5a, W5b, D2).** These windows last\n  milliseconds: from a delivery to its claim, from a claim to its offset commit, from the renewal\n  before acceptance to acceptance, from the acceptance commit to its event. A signal from outside\n  cannot land in them reliably. Recommended: a hook in the `worker` command that sends SIGKILL to\n  its own process at one named fault point (or holds there, for D2), enabled only by an environment\n  variable the harness sets, and recorded in the worker's `started` event. `Worker(fault=...)`\n  already calls the points of `WORKER_FAULT_POINTS`; W5a needs one more, between `accept_result`'s\n  return and the `accepted` event, which would also join `WORKER_FAULT_POINTS`, so that the offline\n  tests that crash at every fault point cover it. It would be new code, written with Claude Code,\n  and tested and mutation-checked like the rest. Alternatives: signals timed from the event logs,\n  with misses recorded (3.1); or leaving these cases to the offline fault-point tests, recorded as\n  not run here.\n- **Q-E. A fixed owner for the partition.** Recommended: set `client.id` to the worker id in\n  [kafka.py](../src/etf_risk/jobs/kafka.py), so that the range assignor gives the partition to A\n  whenever A is live, and roles follow from 2.4's order and restart rule. Both facts it rests on\n  (member ids that start with the client id, and the range assignor's order) are to be verified\n  against Kafka 4.3.1 first. Alternative: leave it, read the owner from the assignment events, and\n  inject into whichever worker claims the job (2.4).\n\nThe first draft's Q-B (who recovers) and Q-C (where the SQL runs) are now part of the protocol (2.4,\n4.5), and its Q-D (assignment events) is a prerequisite (section 10).\n\n## 10. Records, code and authorship\n\n- **Records** (proposal), under `data/outputs-recovery/<batch>/`, outside Git like the rest of\n  `data/`: the export; the event logs; the harness's logs (injections with their intended and\n  verified phases, deadlines and observations, process starts with their clock checks, the clock\n  check, partition owners); `services peaks`; the three fingerprints (4.5); Q0–Q3b as CSV; the table\n  of section 5, one row per injection; the per-case tally (section 7); `cleanup`'s listing.\n- **Nothing is dropped.** Every injection, including misses and those not run, every batch,\n  including invalid ones (6.1), and every verdict, including failed outcomes, stays in the records.\n  The tally lists all 14 cases and every verdict value, with zeros.\n- **Prerequisites in M3 code**, none of it written:\n  - the harness, with its injection log, deadline observations, clock checks and tally;\n  - the reference-run wrapper that takes the host lock (2.2);\n  - the collector for section 5, and the runner for section 7;\n  - an event for each partition assignment and revocation in kafka.py (2.4, 3.2);\n  - the code identity in each process's start event and in `step_started` (2.3);\n  - monotonic step-start and tree-end times in the launcher records (6.5);\n  - the injection hook and the new fault point for W5a (Q-A), and `client.id` (Q-E), if chosen.\n- **Authorship.** Spec §11: the job code is written with Claude Code; the experiments are the\n  project author's, with tutoring. In the earlier experiments the author decided the configurations\n  and rules, approved the design and the predictions, ran the formal measurements and wrote the\n  answers; Claude Code drafted Part A and wrote the code. Here the review requirements in 1.1 are\n  the author's, and everything else is Claude Code's proposal. Which of the harness, the collector\n  and the SQL the author writes is the author's decision. If the queries of section 7 are kept, the\n  file that holds them should say they were drafted with Claude Code; the author can also write\n  their own and use these as a cross-check.\n\n## 11. Not claimed\n\n- Times hold for this machine, the clock of 8.2, and one broker and one database (spec §11's\n  limits).\n- Results are counts per case, not rates (8.1).\n- The bounds in 3.2 hold only under their Kafka conditions, and they are not predictions until 8.2\n  is decided and the author approves them.\n- Cases without an injection method are not measured.\n- Nothing in this outline has been run, including its SQL and the fixture.\n\n## Appendix A. SQL fixture\n\n_Drafted with Claude Code; not run. The expected results were traced by hand._\n\nNine jobs in one store, each built to show one verdict of section 7. Load the store rows into a\nscratch database created from [schema/mysql.sql](../src/etf_risk/jobs/schema/mysql.sql), never into\na batch's database; then, in one session, create section 7's TEMPORARY tables, load their rows and\nrun Q0–Q3b. The times, deadlines and lags are made up and decide nothing in section 8.\n\n| Job | Case id | Shows |\n|---|---|---|\n| 1 | `ontime` | a job that met its deadline and was reported once |\n| 2 | `late` | late completion: running at its deadline, succeeded later (attempt 2, by B) |\n| 3 | `noevent` | a missing acceptance event, as after W5a |\n| 4 | `dupe` | duplicate reports of one attempt |\n| 5 | `wrongwkr` | a wrong-worker report: A reports attempt 2, which B claimed and accepted |\n| 6 | `unfin` | a job still running in the final snapshot |\n| 7 | `othstore` | a stale report from another store for the same job id, next to the right one |\n| 8 | `twoacc` | two accepted attempts, inserted directly; the store cannot produce this |\n| 9 | `notobs` | a success seen by an observation that ended too late |\n\n```sql\n-- Store rows. jobs and job_attempts refer to each other, so foreign key checks are off while\n-- loading; the rows satisfy both keys, and the CHECK constraints stay enforced.\nSET @s = 'fixture0000000000000000000000001', @t0 = '2026-10-24 10:00:00', @t1 = '2026-10-24 10:01:05',\n    @t2 = '2026-10-24 10:05:00', @lease = '2026-10-24 10:06:00';\nSET FOREIGN_KEY_CHECKS = 0;\n\nINSERT INTO job_store (id, store_id, schema_version, created_at) VALUES (1, @s, 1, @t0);\n\nINSERT INTO jobs (job_id, params, input_checksums, status, max_attempts, attempt_number, attempt_token,\n                  lease_expires_at, accepted_attempt, error, version, created_at, updated_at,\n                  finished_at, published_at) VALUES\n    (1, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),\n    (2, '{}', '{}', 'succeeded', 3, 2, NULL,      NULL,   2,    NULL, 7, @t0, @t2, @t2,  NULL),\n    (3, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),\n    (4, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),\n    (5, '{}', '{}', 'succeeded', 3, 2, NULL,      NULL,   2,    NULL, 7, @t0, @t2, @t2,  NULL),\n    (6, '{}', '{}', 'running',   3, 1, 'tok-6-1', @lease, NULL, NULL, 3, @t0, @t2, NULL, NULL),\n    (7, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL),\n    (8, '{}', '{}', 'succeeded', 3, 2, NULL,      NULL,   2,    NULL, 7, @t0, @t2, @t2,  NULL),\n    (9, '{}', '{}', 'succeeded', 3, 1, NULL,      NULL,   1,    NULL, 4, @t0, @t2, @t2,  NULL);\n\nINSERT INTO job_attempts (job_id, attempt_number, attempt_token, worker_id, run_id, output_dir, outcome,\n                          error, result_digest, claimed_at, lease_expires_at, renewals, ended_at) VALUES\n    (1, 1, 'tok-1-1', 'A', 'job-1-attempt-1', '/fixture/job-1-attempt-1', 'accepted', NULL, REPEAT('1', 64), @t0, @lease, 2, @t2),\n    (2, 1, 'tok-2-1', 'A', 'job-2-attempt-1', '/fixture/job-2-attempt-1', 'expired',  NULL, NULL,            @t0, @t1,    1, @t1),\n    (2, 2, 'tok-2-2', 'B', 'job-2-attempt-2', '/fixture/job-2-attempt-2', 'accepted', NULL, REPEAT('2', 64), @t1, @lease, 2, @t2),\n    (3, 1, 'tok-3-1', 'A', 'job-3-attempt-1', '/fixture/job-3-attempt-1', 'accepted', NULL, REPEAT('3', 64), @t0, @lease, 2, @t2),\n    (4, 1, 'tok-4-1', 'A', 'job-4-attempt-1', '/fixture/job-4-attempt-1', 'accepted', NULL, REPEAT('4', 64), @t0, @lease, 2, @t2),\n    (5, 1, 'tok-5-1', 'A', 'job-5-attempt-1', '/fixture/job-5-attempt-1', 'expired',  NULL, NULL,            @t0, @t1,    1, @t1),\n    (5, 2, 'tok-5-2', 'B', 'job-5-attempt-2', '/fixture/job-5-attempt-2', 'accepted', NULL, REPEAT('5', 64), @t1, @lease, 2, @t2),\n    (6, 1, 'tok-6-1', 'A', 'job-6-attempt-1', '/fixture/job-6-attempt-1', 'running',  NULL, NULL,            @t0, @lease, 4, NULL),\n    (7, 1, 'tok-7-1', 'A', 'job-7-attempt-1', '/fixture/job-7-attempt-1', 'accepted', NULL, REPEAT('7', 64), @t0, @lease, 2, @t2),\n    (8, 1, 'tok-8-1', 'A', 'job-8-attempt-1', '/fixture/job-8-attempt-1', 'accepted', NULL, REPEAT('8', 64), @t0, @t1,    1, @t1),\n    (8, 2, 'tok-8-2', 'B', 'job-8-attempt-2', '/fixture/job-8-attempt-2', 'accepted', NULL, REPEAT('f', 64), @t1, @lease, 2, @t2),\n    (9, 1, 'tok-9-1', 'A', 'job-9-attempt-1', '/fixture/job-9-attempt-1', 'accepted', NULL, REPEAT('9', 64), @t0, @lease, 2, @t2);\n\nSET FOREIGN_KEY_CHECKS = 1;\n```\n\n```sql\n-- The harness's rows, in the session that created section 7's TEMPORARY tables.\nINSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono, max_lag_s) VALUES\n    (1, 'ontime',   'submit',    100, 2000.0, 1.0),\n    (2, 'late',     'injection', 100, 2000.0, 1.0),\n    (3, 'noevent',  'injection', 100, 2000.0, 1.0),\n    (4, 'dupe',     'submit',    100, 2000.0, 1.0),\n    (5, 'wrongwkr', 'injection', 100, 2000.0, 1.0),\n    (6, 'unfin',    'injection', 100, 2000.0, 1.0),\n    (7, 'othstore', 'submit',    100, 2000.0, 1.0),\n    (8, 'twoacc',   'submit',    100, 2000.0, 1.0),\n    (9, 'notobs',   'injection', 100, 2000.0, 1.0);\n\nINSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono, status, attempt_number,\n                                   accepted_attempt) VALUES\n    (1, 2000.010, 2000.030, 'succeeded', 1, 1),\n    (2, 2000.010, 2000.030, 'running',   2, NULL),\n    (3, 2000.010, 2000.030, 'succeeded', 1, 1),\n    (4, 2000.010, 2000.030, 'succeeded', 1, 1),\n    (5, 2000.010, 2000.030, 'succeeded', 2, 2),\n    (6, 2000.010, 2000.030, 'running',   1, NULL),\n    (7, 2000.010, 2000.030, 'succeeded', 1, 1),\n    (8, 2000.010, 2000.030, 'succeeded', 2, 2),\n    (9, 2002.500, 2002.600, 'succeeded', 1, 1);\n\nINSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number, result_digest) VALUES\n    (@s, 'A', 101, 1, 1, REPEAT('1', 64)),\n    (@s, 'B', 202, 2, 2, REPEAT('2', 64)),\n    (@s, 'A', 101, 4, 1, REPEAT('4', 64)),\n    (@s, 'A', 101, 4, 1, REPEAT('4', 64)),\n    (@s, 'A', 101, 5, 2, REPEAT('5', 64)),\n    (@s, 'A', 101, 7, 1, REPEAT('7', 64)),\n    ('fixture0000000000000000000000002', 'A', 99, 7, 1, REPEAT('0', 64)),\n    (@s, 'A', 101, 8, 1, REPEAT('8', 64)),\n    (@s, 'B', 202, 8, 2, REPEAT('f', 64)),\n    (@s, 'A', 101, 9, 1, REPEAT('9', 64));\n```\n\n**Expected results.** Q0: `n_jobs` 9, `sum_version` 44, `n_attempts` 12, `sum_renewals` 23. Q2b: no\nrows. The store's own `status --check` would report job 8 only, under \"succeeded without exactly one\naccepted attempt\". The other queries, by job (Q2 itself orders by case id):\n\n| Job | Q1 `n_claims` / `n_accepted`: verdict | Q2: lag, timeliness | Q3a `n_reports` / `n_matching` / `n_reported_attempts`: verdict |\n|---|---|---|---|\n| 1 | 1 / 1: `ok` | 0.03: `on time` | 1 / 1 / 1: `reported once` |\n| 2 | 2 / 1: `ok` | 0.03: `late` | 1 / 1 / 1: `reported once` |\n| 3 | 1 / 1: `ok` | 0.03: `on time` | 0 / 0 / 0: `no matching report` |\n| 4 | 1 / 1: `ok` | 0.03: `on time` | 2 / 2 / 1: `one attempt reported more than once` |\n| 5 | 2 / 1: `ok` | 0.03: `on time` | 1 / 0 / 1: `no matching report` |\n| 6 | 1 / 0: `not finished` | 0.03: `unfinished` | — (not succeeded) |\n| 7 | 1 / 1: `ok` | 0.03: `on time` | 1 / 1 / 1: `reported once` |\n| 8 | 2 / 2: `more than one accepted attempt` | 0.03: `on time` | 2 / 1 / 2: `acceptance reported for more than one attempt` |\n| 9 | 1 / 1: `ok` | 2.6: `succeeded, deadline not observed` | 1 / 1 / 1: `reported once` |\n\nQ3b, ten rows: `matches` for jobs 1, 2, 4 (twice), 7 (store …001), 8 (both attempts) and 9; `wrong\nworker` for job 5; `other store` for job 7 (store …002). Job 8's two matches are right against a\ntable that is itself wrong; Q1 and Q3a flag the job.\n\n**Coverage.** The fixture shows 3 of Q1's 9 verdicts (`ok`, `not finished`, `more than one accepted\nattempt`), 4 of Q2's 6 classes (`on time`, `late`, `unfinished`, `succeeded, deadline not\nobserved`), all 4 of Q3a's verdicts, and 3 of Q3b's 6 (`matches`, `wrong worker`, `other store`).\nThe other verdicts have no fixture yet.\n\n## History\n\n- **Draft, 2026-10-23.** Outline drafted with Claude Code at the author's request.\n- **Revision 1, 2026-10-23.** Applied the author's review (1.1):\n  - deadlines and their observation (4.2, 4.3, Q2), quiescence and the final snapshot (4.4, 4.5,\n    Q0);\n  - database acceptance correctness apart from the event log (6.2, 6.4, Q1, Q3a, Q3b), with full\n    report identity, and the new case W5a (the first draft's W5 is now W5b);\n  - code identity at launch (2.3), and unknown intervals instead of assumed ones (6.5);\n  - monotonic durations (4.1) and `n/a` recovery metrics (section 5);\n  - Kafka conditions in the expected times (3.2), and the startup order and restart rule (2.4),\n    which replace Q-B; Q-C moved into 4.5, Q-D became a prerequisite (section 10), and Q-E is new;\n  - reference runs under the host lock (2.2); the rule-of-three sentence removed (8.1); all cases\n    kept, with no core or optional split (3.1); the fixture of Appendix A added.\n"
}
````

## 10. User — 2026-10-23T20:38:03.874Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 11. Assistant — 2026-10-23T20:38:32.266Z

### Tool call: Bash

```
{
  "command": "D=docs/recovery-experiments.md && SP=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad && R=~/leveraged-etf-risk-analytics && (for w in .claude/worktrees/worker-pipeline .claude/worktrees/extension-baseline; do echo \"=== $w\"; git --no-optional-locks -C \"$R/$w\" rev-parse HEAD; git --no-optional-locks -C \"$R/$w\" status --porcelain=v1 --untracked-files=all; done) > \"$SP/worktree-snapshot-after2.txt\"; diff -q \"$SP/worktree-snapshot-before.txt\" \"$SP/worktree-snapshot-after2.txt\" >/dev/null && echo \"(1) linked worktrees identical to the snapshot\" || diff \"$SP/worktree-snapshot-before.txt\" \"$SP/worktree-snapshot-after2.txt\"; echo \"(2) $(git status --porcelain=v1 --untracked-files=all) — $(wc -l < $D) lines\"; echo \"(3) links:\"; grep -o -E '\\]\\([^)#]+' $D | sed 's/^](//' | sort -u | while read -r p; do test -e \"docs/$p\" && echo \"  ok      $p\" || echo \"  MISSING $p\"; done; echo \"(4) section refs without a heading:\"; heads=$(grep -E '^#{2,3} ' $D | grep -o -E '^#{2,3} [0-9]+(\\.[0-9]+)?' | awk '{print $2}' | sort -u); for r in $(grep -o -E '\\b[1-9]\\.[1-5]\\b' $D | sort -u); do echo \"$heads\" | grep -qx \"$r\" || echo \"  $r\"; done; echo \"  (done)\"; echo \"(5) 3.1 case rows: $(awk '/^### 3.1/,/^### 3.2/' $D | grep -c -E '^\\| (C0|W[1-7]a?b?|K[12]|D[12]|X1) \\|')\"",
  "description": "Verify worktrees unchanged, links, section references and case count"
}
```

## 12. User — 2026-10-23T20:38:33.261Z

### Tool result

```
2,14c2
< d2d8615de49e33b0fc2db8b8ff768ee8085fd81b
<  M README.md
<  M docs/job-queue.md
<  M docs/job-table.md
<  M docs/spec.md
<  M pyproject.toml
<  M tests/mutation_check.py
<  M tests/test_jobs_kafka.py
<  M tests/test_jobs_launcher.py
<  M tests/test_jobs_pipeline.py
<  M uv.lock
< ?? docs/worker-pipeline.md
< ?? tests/test_jobs_live_pipeline.py
---
> 6d8a23214c5629f92d951ff89ecbccf873c55859
(2) ?? docs/recovery-experiments.md —      893 lines
(3) links:
  ok      ../docker/compose.yaml
  ok      ../src/etf_risk/jobs/events.py
  ok      ../src/etf_risk/jobs/kafka.py
  ok      ../src/etf_risk/jobs/schema/mysql.sql
  ok      ../src/etf_risk/jobs/timing.py
  ok      job-queue.md
  ok      job-table.md
  MISSING worker-pipeline.md
(4) section refs without a heading:
  5.5
  8.4
  (done)
(5) 3.1 case rows: 14
```

## 13. Assistant — 2026-10-23T20:38:52.653Z

### Tool call: Bash

```
{
  "command": "grep -n -o -E '.{0,12}\\b(5\\.5|8\\.4)\\b.{0,6}' docs/recovery-experiments.md | head -5; echo \"=== commits d2d8615..6d8a232\"; git log --oneline d2d8615..6d8a232; echo \"=== files changed\"; git diff --stat d2d8615 6d8a232 | tail -25",
  "description": "Confirm false positives and list what the new M2 commit changed"
}
```

## 14. User — 2026-10-23T20:38:53.132Z

### Tool result

```
6: Code (Opus 5.5) on 2
74:book: MySQL 8.4.13 an
421:n for MySQL 8.4, with
=== commits d2d8615..6d8a232
6d8a232 Document the worker's real pipeline, its runbook and M2's results
dd041c1 Add M2's acceptance runs, the standby test and ten more mutations
=== files changed
 README.md                        |  29 ++-
 docs/job-queue.md                |  38 ++--
 docs/job-table.md                |  19 ++
 docs/spec.md                     |  50 +++--
 docs/worker-pipeline.md          | 306 +++++++++++++++++++++++++++
 pyproject.toml                   |   1 +
 tests/mutation_check.py          |  30 ++-
 tests/test_jobs_kafka.py         |  22 ++
 tests/test_jobs_launcher.py      |  15 ++
 tests/test_jobs_live_pipeline.py | 436 +++++++++++++++++++++++++++++++++++++++
 tests/test_jobs_pipeline.py      |  14 ++
 uv.lock                          |   2 +
 12 files changed, 934 insertions(+), 28 deletions(-)
```

## 15. Assistant — 2026-10-23T20:39:20.012Z

### Tool call: Bash

```
{
  "command": "C=6d8a232 && chk(){ f=$1; shift; for p in \"$@\"; do if git show \"$C:$f\" | grep -q -F -- \"$p\"; then echo \"  ok   $p\"; else echo \"  GONE $p\"; fi; done; } && echo \"== worker-pipeline.md\" && chk docs/worker-pipeline.md '| lease | 60 s |' '| renew_interval | 10 s |' '| fence_margin, M | 10 s |' '| term_grace + kill_confirm, G | 5 + 2 s |' '## Accepting a result' '`group.protocol` | `classic`' '| 15 s, 3 s |' '967 s' 'recovery times of E2 include that wait' '(M3) restarts it' 'imports pandas and pyarrow' && echo \"== spec.md\" && chk docs/spec.md '**E1.** Does each job accept at most one result' '**E2.** After a worker crash (before or after its claim)' 'matches a reference run by content' 'accepted results per job and lost jobs' 'should start on a fresh MySQL' '511 MiB' '3.83 GiB' 'experiments by the project' && echo \"== job-queue.md\" && chk docs/job-queue.md '`CONFIRMATION_TIMEOUT` | 10 s' '`PUBLICATION_GRACE` | 30 s' '`RECONCILE_INTERVAL` | 5 s' 'test_a_crash_between_claim_and_commit' && echo \"== test_jobs_live_pipeline.py\" && chk tests/test_jobs_live_pipeline.py 'TIMING = [\"--timing\", \"lease=24\", \"--timing\", \"renew_interval=4\", \"--timing\", \"session_timeout=10\"]' 'CALENDAR = {\"kind\": \"calendar-year\", \"stride\": 21}' 'ROLLING = {\"kind\": \"rolling\", \"stride\": 21}' '[\"lock-tables\", \"pause\", \"restart\"]' 'whatever partition assignment' 'compare_tables' 'step_started_at_utc' 'tree_ended_at_utc' && echo \"  test functions: $(git show $C:tests/test_jobs_live_pipeline.py | grep -c -E '^def test_')\"",
  "description": "Check each cited M2 fact against the committed M2 files"
}
```

## 16. User — 2026-10-23T20:39:21.040Z

### Tool result

```
== worker-pipeline.md
  ok   | lease | 60 s |
  ok   | renew_interval | 10 s |
  ok   | fence_margin, M | 10 s |
  ok   | term_grace + kill_confirm, G | 5 + 2 s |
  ok   ## Accepting a result
  ok   `group.protocol` | `classic`
  ok   | 15 s, 3 s |
  ok   967 s
  ok   recovery times of E2 include that wait
  ok   (M3) restarts it
  ok   imports pandas and pyarrow
== spec.md
  ok   **E1.** Does each job accept at most one result
  ok   **E2.** After a worker crash (before or after its claim)
  ok   matches a reference run by content
  ok   accepted results per job and lost jobs
  ok   should start on a fresh MySQL
  ok   511 MiB
  ok   3.83 GiB
  ok   experiments by the project
== job-queue.md
  ok   `CONFIRMATION_TIMEOUT` | 10 s
  ok   `PUBLICATION_GRACE` | 30 s
  ok   `RECONCILE_INTERVAL` | 5 s
  ok   test_a_crash_between_claim_and_commit
== test_jobs_live_pipeline.py
  ok   TIMING = ["--timing", "lease=24", "--timing", "renew_interval=4", "--timing", "session_timeout=10"]
  ok   CALENDAR = {"kind": "calendar-year", "stride": 21}
  ok   ROLLING = {"kind": "rolling", "stride": 21}
  ok   ["lock-tables", "pause", "restart"]
  ok   whatever partition assignment
  ok   compare_tables
  ok   step_started_at_utc
  ok   tree_ended_at_utc
fatal: ambiguous argument '6d8a232ests/test_jobs_live_pipeline.py': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
  test functions: 0
```

## 17. Assistant — 2026-10-23T20:39:30.368Z

### Tool call: Bash

```
{
  "command": "C=6d8a232 && echo \"test functions at ${C}: $(git show \"${C}:tests/test_jobs_live_pipeline.py\" | grep -c -E '^def test_') (parametrized stall cases: lock-tables, pause, restart)\" && echo \"=== worker-pipeline.md headings at ${C}\" && git show \"${C}:docs/worker-pipeline.md\" | grep -n -E '^#{1,3} '",
  "description": "Count live test functions and list headings of the committed M2 doc"
}
```

## 18. User — 2026-10-23T20:39:30.807Z

### Tool result

```
test functions at 6d8a232: 8 (parametrized stall cases: lock-tables, pause, restart)
=== worker-pipeline.md headings at 6d8a232
1:# The worker's real pipeline: steps, deadlines, the host lock and cleanup
15:## A job's steps
50:## Accepting a result
70:## Failures
81:## Deadlines and the watchdog
120:## The host execution lock
138:## Ending a process tree
149:## After a lost database connection
169:## Kafka group timing
182:## Starting, stopping and sweeping
205:## Known limits
216:## What is checked where
249:## Status on 2026-10-23 (`feature/worker-pipeline`)
```

## 19. Assistant — 2026-10-23T20:39:42.332Z

### Tool call: Bash

```
{
  "command": "git show \"6d8a232:docs/worker-pipeline.md\" | sed -n '249,306p'",
  "description": "Show the status section of the committed M2 doc"
}
```

## 20. User — 2026-10-23T20:39:42.817Z

### Tool result

```
## Status on 2026-10-23 (`feature/worker-pipeline`)

- **Offline:** the whole suite: 551 passed and 29 skipped (the tests that need MySQL, Kafka or
  ETF_RISK_LIVE_PIPELINE). The Spark-marked end-to-end test passed.
- **Against MySQL 8.4.13 and Kafka 4.3.1** on fresh containers: the job suites, 420 passed.
  That includes the live reconnect tests (`KILL CONNECTION`, and a ping after an idle period)
  and the standby test.
- **Acceptance runs** (test_jobs_live_pipeline.py, 10 cases):
  - **First run:** 4 passed. 6 failed on three faults of the test harness: an attribute that
    hid a method, the test's own MySQL connection lost during the stalls, and a standby that
    could win the partition before worker A did.
  - **After the fixes:** the 6 passed.
  - **Final run** of all 10, on the final code: 10 passed in 11 min 20 s. It also checked
    the temporary folders: no new Spark, PySpark or JVM entries.
  - **What the cases showed:**
    - **A worker killed in step 2:** its launcher ended the tree on EOF. Attempt 1 ended
      expired, and attempt 2 was accepted.
    - **A worker stopped alone:** its launcher's watchdog ended the tree (outcome `deadline`)
      within F + t_w + G. Attempt 2's Spark step started after attempt 1's tree had ended.
      On SIGCONT the old worker was fenced, and its renewal count did not change.
    - **A whole tree stopped:** the replacement started no step until the frozen tree was
      resumed and had ended itself.
    - **A step over its limit:** three attempts failed (`timeout`), the job failed, and
      nothing was left.
    - **Database stalls:** `LOCK TABLES`, `docker compose pause` and `restart` cost 0, 1
      and 2 failed renewals. Each run continued under its first attempt, with no manual
      restart.
    - **A Kafka restart during a run:** no effect on the run, and a later submission ran.
    - **A starting worker:** its sweep kept another worker's running attempt.
- **Mutation checks** (49):
  - **Offline:** 47 of 47 caught; the 2 that need MySQL were skipped. In the first offline
    run, `no-host-lock` survived. The survivor check also stops a launcher whose
    predecessor's tree is registered. A new test now holds the lock outside any launcher.
  - **Against MySQL and Kafka:** 49 of 49 caught, none at the timeout.
- **Memory.** These figures are informational: four containers of another project shared
  Docker's VM throughout, and the host had about 1.3 GiB available.
  - **The step trees** (peak summed RSS, sampled every 0.5 s by the launchers; the range over
    the first and the final acceptance run):

    | Job | windows | spark_pipeline | verify |
    |---|---|---|---|
    | calendar-year | 2.5–3.0 s, 0.12 GiB | 22.1–22.6 s, 0.66–0.79 GiB | 9.5 s, 0.45–0.49 GiB |
    | stride 21 | 1.5 s, 0.12 GiB | 44.8–50.4 s, 1.19–1.36 GiB | 11.0–11.5 s, 0.57–0.58 GiB |

  - **The job processes** (peak RSS during a calendar-year job): the worker 63.0 MiB and the
    reconciler 51.6 MiB.
  - **MySQL:**
    - 345 MiB (67%) after the live job suites on a fresh container;
    - 501 MiB (98%) after the live mutation session (one full run and 49 shorter ones) on
      another fresh container.
  - **Kafka:** 361 to 415 MiB (56–65%).
  - **`docker compose restart` resets a container's `memory.peak`.** MySQL read 226 MiB after
    the acceptance runs' restarts, below the 345 MiB that container had reached earlier. The
    recovery harness must read peaks before each restart it injects.
- **Not done:** the isolated memory-budget check, with no other project's containers in the
  VM. Those containers were running throughout and were left alone.

*AI contribution: written with Claude Code (Opus 5.5).*
```

## 21. Assistant — 2026-10-23T20:40:34.308Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md",
  "old_string": "author would decide or write. Sources: spec §11, [worker-pipeline.md](worker-pipeline.md),\n[job-table.md](job-table.md) and [job-queue.md](job-queue.md) as they stood in the M2 worktree on\n2026-10-23, uncommitted and still subject to change; the code at `d2d8615`\n(`feature/worker-pipeline`); and `tests/test_jobs_live_pipeline.py`, also uncommitted there. Nothing\nwas run for this outline: the SQL in section 7 and the fixture in Appendix A have not been run, and\nthe fixture's expected results were traced by hand._",
  "new_string": "author would decide or write. Sources: spec §11, [worker-pipeline.md](worker-pipeline.md),\n[job-table.md](job-table.md), [job-queue.md](job-queue.md) and `tests/test_jobs_live_pipeline.py`\nas read uncommitted in the M2 worktree on 2026-10-23, and the code at `d2d8615`\n(`feature/worker-pipeline`). M2 has since committed those files (`dd041c1`, `6d8a232`) without\nchanging any file under `src/`, and every fact cited here was checked again against `6d8a232`. Its\nstatus section is cited only in 2.4; its numbers are not used for section 8. Nothing was run for\nthis outline: the SQL in section 7 and the fixture in Appendix A have not been run, and the\nfixture's expected results were traced by hand._"
}
```

## 22. Assistant — 2026-10-23T20:40:36.414Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md",
  "old_string": "therefore arbitrary. M2's tests work around this by starting B only after A has claimed a job\n(`claimed_by_a`, whose docstring says so).",
  "new_string": "therefore arbitrary. M2's tests work around this by starting B only after A has claimed a job\n(`claimed_by_a`, whose docstring says so), and M2's first acceptance run failed partly on this: \"a\nstandby that could win the partition before worker A did\" ([worker-pipeline.md](worker-pipeline.md),\nstatus of 2026-10-23)."
}
```

## 23. User — 2026-10-23T20:40:37.510Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 24. User — 2026-10-23T20:40:38.592Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 25. Assistant — 2026-10-23T20:40:53.058Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md",
  "content": "[REDACTED:memory]"
}
```

## 26. User — 2026-10-23T20:40:54.250Z

### Tool result

```
[REDACTED:memory]
```

## 27. Assistant — 2026-10-23T20:40:59.401Z

### Tool call: Bash

```
{
  "command": "D=docs/recovery-experiments.md && A=$(awk '/^## Appendix A/,/^## History/' $D) && echo \"jobs rows: $(echo \"$A\" | grep -c -E \"^    \\([1-9], '\\{\\}'\")  version sum: $(echo \"$A\" | grep -E \"^    \\([1-9], '\\{\\}'\" | sed -E 's/.*NULL, ([0-9]+), @t0, @t2, .*/\\1/' | paste -sd+ - | bc)\" && echo \"attempt rows: $(echo \"$A\" | grep -c -E \"^    \\([1-9], [12], 'tok-\")  renewals sum: $(echo \"$A\" | grep -E \"^    \\([1-9], [12], 'tok-\" | sed -E 's/.*, ([0-9]+), (@t[0-9]|NULL)\\),?$/\\1/' | paste -sd+ - | bc)\" && echo \"report rows: $(echo \"$A\" | grep -c -E \"^    \\((@s|'fixture[0-9]+'), '[AB]'\")\" && echo \"outcome/NULL rule violations:\" && echo \"$A\" | grep -E \"^    \\([1-9], [12], 'tok-\" | awk '{o=($0~/'\"'\"'running'\"'\"'/); e=($0~/NULL\\),?$/); if (o!=e) print \"  ended_at mismatch: \" $0; a=($0~/'\"'\"'accepted'\"'\"'/); d=($0~/REPEAT/); if (a!=d) print \"  digest mismatch: \" $0} END {print \"  (checked \" NR \" rows)\"}' && echo \"status: $(git status --porcelain=v1 --untracked-files=all) — $(wc -l < $D) lines\" && echo \"M2 worktree now: $(git --no-optional-locks -C ~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline rev-parse --short HEAD), $(git --no-optional-locks -C ~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline status --porcelain=v1 --untracked-files=all | wc -l | tr -d ' ') uncommitted entries\"",
  "description": "Check fixture sums, row counts and NULL rules from the doc text"
}
```

## 28. User — 2026-10-23T20:41:00.026Z

### Tool result

```
jobs rows: 9  version sum: 44

Parse error: bad expression
    <stdin>:1

attempt rows: 12  renewals sum: 
report rows: 10
outcome/NULL rule violations:
  (checked 12 rows)
status: ?? docs/recovery-experiments.md —      897 lines
M2 worktree now: 6d8a232, 0 uncommitted entries
```

## 29. Assistant — 2026-10-23T20:41:04.380Z

The renewals extraction missed the last row, which ends in `);`, not `),`. Rerunning just that sum with the fixed pattern:

## 30. Assistant — 2026-10-23T20:41:06.077Z

### Tool call: Bash

```
{
  "command": "awk '/^## Appendix A/,/^## History/' docs/recovery-experiments.md | grep -E \"^    \\([1-9], [12], 'tok-\" | sed -E 's/.*, ([0-9]+), (@t[0-9]|NULL)\\)[,;]?$/\\1/' | tee /dev/stderr | paste -sd+ - | bc | sed 's/^/renewals sum: /'",
  "description": "Sum the fixture's renewals column from the doc text"
}
```

## 31. User — 2026-10-23T20:41:06.712Z

### Tool result

```
2
    (2, 1, 'tok-2-1', 'A', 'job-2-attempt-1', '/fixture/job-2-attempt-1', 'expired',  NULL, NULL,            @t0, @t1,    1, @t1),
2
2
2
    (5, 1, 'tok-5-1', 'A', 'job-5-attempt-1', '/fixture/job-5-attempt-1', 'expired',  NULL, NULL,            @t0, @t1,    1, @t1),
2
4
2
    (8, 1, 'tok-8-1', 'A', 'job-8-attempt-1', '/fixture/job-8-attempt-1', 'accepted', NULL, REPEAT('8', 64), @t0, @t1,    1, @t1),
2
2

Parse error: bad expression
    <stdin>:1
```

## 32. Assistant — 2026-10-23T20:41:12.416Z

The alignment spaces in three rows broke the pattern; their renewals value is 1, visible in the echoed lines. Rerunning with whitespace-tolerant matching to get a mechanical total:

## 33. Assistant — 2026-10-23T20:41:14.050Z

### Tool call: Bash

```
{
  "command": "awk '/^## Appendix A/,/^## History/' docs/recovery-experiments.md | grep -E \"^    \\([1-9], [12], 'tok-\" | sed -E 's/.*,[[:space:]]+([0-9]+),[[:space:]]+(@t[0-9]|NULL)\\)[,;]?$/\\1/' | paste -sd+ - | tee /dev/stderr | bc | sed 's/^/renewals sum: /'",
  "description": "Sum the fixture's renewals column with flexible spacing"
}
```

## 34. User — 2026-10-23T20:41:14.609Z

### Tool result

```
2+1+2+2+2+1+2+4+2+1+2+2
renewals sum: 23
```

## 35. Assistant — 2026-10-23T20:42:00.291Z

Written for: you, reviewing it as the author.

Revision 1 of [docs/recovery-experiments.md](.claude/worktrees/recovery-outline/docs/recovery-experiments.md) is ready for review: 897 lines, still uncommitted. Your requirements are now listed as yours in section 1.1, each pointing to the section that meets it. Everything else is still marked as my proposal, and a history at the end lists every change.

| Your point | How it's handled | Where |
|---|---|---|
| 1. Deadlines | Each job's deadline is recorded in the harness's records. One read of the database at the deadline decides the class: on time, late, unfinished, failed, missing, or "deadline not observed". A miss seen at or after the deadline is final, so a later success can't erase it. | 4.2, 4.3, Q2 |
| 2. Database vs. event log | Q1 uses only the job tables and answers E1. Q3a and Q3b check the workers' reports separately. New case W5a covers a crash after the acceptance commits but before its event (the old W5 is now W5b). A repeated report of one attempt gets its own verdict and is never counted as a second accepted result. | 6.2, 6.4 |
| 3. Crashed attempts, code identity, intervals | Crashed attempts aren't required to leave any success files. Every process records its code identity when it starts. The overlap check returns no overlap, overlap, or unknown; a missing interval gives unknown. | 2.3, 6.1, 6.5 |
| 4. Clocks, n/a | All durations use the host's monotonic clock, with a check that each process reads the same one. A table marks recovery latency "n/a" with a reason for W5a, W5b and the no-failure cases. | 4.1, 5 |
| 5. Kafka, startup order | Each expected time now states the Kafka condition it depends on (session expiry, the standby rejoining, a busy worker delaying a rebalance). The startup order is fixed, and a killed worker restarts only after its job has finished. | 2.4, 3.2 |
| 6. Report identity | A report must match the store id, job, attempt, worker id and digest of an accepted attempt. | Q3a, Q3b |
| 7. Observation, quiescence, snapshot | Quiescence means no worker or reconciler process and no MySQL connection of theirs is left. The cross-check and the export must then show the same fingerprint, taken before and after the export. | 4.3–4.5 |

Also done:
- Reference runs now take the host lock.
- The rule-of-three claim is replaced by "counts per case, no rates".
- All 14 cases are kept, with no core/optional split.
- Appendix A adds the SQL fixture (details below).

**Needs your attention**
1. **A fixed startup order alone doesn't decide which worker owns the partition.** `kafka.py` uses Kafka's defaults, so with two live workers the owner after a rebalance is arbitrary. M2's own first acceptance run failed partly on this ("a standby that could win the partition before worker A did"). Q-E gives two options: set `client.id` to the worker id (still to verify against Kafka 4.3.1), or read the owner from assignment events.
2. **A new finding I haven't applied:** M2's status reports that `docker compose restart` resets a container's `memory.peak`. Batches with K1, K2, D1 or D2 would lose the peaks from before the restart. The fix is to read the peaks before each injected restart and keep the maximum. Say the word and I'll add it to 4.5 and 8.3.
3. **M2 committed while I worked.** Its worktree moved from `d2d8615` to `6d8a232` (two commits) and is now clean. I only ran read commands there. No file under `src/` changed, and I re-checked every fact the outline cites against `6d8a232`; all still hold.
4. **Is M2's report final?** The status section in `6d8a232` has step durations, memory peaks, the worker's memory and the cost of the database stalls: the inputs section 8 waits for. I haven't used them. Tell me if that's M2's final report.
5. **Some requirements need M3 code that doesn't exist yet:** assignment events, code identity in start events, monotonic times in the launcher records, the W5a fault point, and the lock wrapper for reference runs. They're listed in section 10; none is written.
6. **A policy choice for you to check:** each job gets one deadline read, never retried. If the read fails (say MySQL is down in D1 or D2), the class is "deadline not observed", never "on time".

**Fixture.** Nine jobs: late completion (job 2), a missing acceptance event (3), duplicate reports (4) and a wrong-worker report (5). The other five are an on-time job, an unfinished one, a report from another store, two accepted attempts and an observation taken too late. I traced the expected results by hand. I checked the arithmetic mechanically: 9 jobs with versions summing to 44, 12 attempt rows with renewals summing to 23, 10 reports, and each attempt row consistent with the schema's null rules. It exercises 3 of Q1's 9 verdicts, 4 of Q2's 6, all 4 of Q3a's and 3 of Q3b's 6. It hasn't been run; I can run it on a scratch MySQL once you confirm M2's session has ended.

I didn't run any SQL, tests, Spark or Docker, and made no commits. I also updated my memory note for this draft.

`★ Insight ─────────────────────────────────────`
- The deadline rule works because a terminal status never changes. A success seen early proves on time; a miss seen at or after the deadline proves late. Only the lag tolerance needs a decision.
- The store's `worker_id` column, unlike its other identifiers, doesn't compare byte for byte (it ignores case), so the queries compare it through `CAST(... AS BINARY)`. Otherwise "worker a" and "worker A" would count as the same reporter.
`─────────────────────────────────────────────────`
