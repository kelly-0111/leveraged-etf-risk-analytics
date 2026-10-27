# Claude Code message 1

Session: `a9a2be5c-8da0-4ec5-be57-f251b5676fe9` · prompt sent 2026-10-23 14:37 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): email ×3, git-user ×104, home ×634, memory ×15, model-reasoning ×115, user ×27. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-23T19:37:22.102Z



<pasted_content id="605f">
While M2 validation runs, draft the E1/E2 recovery experiment outline in a separate worktree.

Cover failure cases, metrics, correctness checks and a draft SQL cross-check for accepted results per job. Leave repetitions, deadlines and memory thresholds as explicit decisions pending M2’s final report.

Only read and draft files. Do not run tests, Spark, Docker, install dependencies or modify the M2 worktree. Keep authorship accurate and present the draft for my review.
</pasted_content id="605f">


## 2. Assistant — 2026-10-23T19:38:32.868Z

I'll start by orienting myself read-only: worktrees, branches, and where E1/E2 and the M2 work are defined.

## 3. Assistant — 2026-10-23T19:38:34.183Z

### Tool call: Bash

```
{
  "command": "git worktree list && echo \"--- branches\" && git for-each-ref --format='%(refname:short) %(objectname:short) %(committerdate:short) %(subject)' refs/heads && echo \"--- root\" && ls -a && echo \"--- docs\" && ls docs",
  "description": "List worktrees, local branches and top-level layout"
}
```

## 4. User — 2026-10-23T19:38:37.336Z

### Tool result

```
~/leveraged-etf-risk-analytics                                       97c35f3 [fix/measure-process-kinds]
~/leveraged-etf-risk-analytics/.claude/worktrees/extension-baseline  a70c066 [feature/extension-baseline]
~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline     d2d8615 [feature/worker-pipeline]
--- branches
docs/project-status 66a85fb 2026-10-23 Record Stage 4 as implemented in the README and spec
feature/caching ed71796 2026-10-22 Add reviewed AI logs for the caching experiment
feature/experiments 516b28a 2026-10-19 Mark the stride experiment complete in the README and spec
feature/extension-baseline a70c066 2026-10-23 Record the extension baseline in the job docs, the spec and a README runbook
feature/job-queue cd72957 2026-10-23 Record the MySQL validation of e2806bd in the job-queue docs
feature/job-table 6cfd971 2026-10-22 Record the job table's status in the README and spec
feature/pandas-baseline ed909d5 2026-10-22 Add reviewed AI logs for experiments and documentation
feature/shuffle-partitions 8067426 2026-10-21 Add the partition document's authorship line and update expectation 5
feature/stage-4 737c65d 2026-10-23 Merge pull request #9 from [REDACTED:git-user]/feature/stage-4
feature/worker-pipeline d2d8615 2026-10-23 Run windows, spark_pipeline and verify in the worker, under a watchdog and a host lock
fix/measure-process-kinds 97c35f3 2026-10-23 Count a Java process as the Spark JVM only when it runs Spark
main a628f22 2026-10-23 Merge pull request #11 from [REDACTED:git-user]/feature/extension-baseline
--- root
.
..
.DS_Store
.claude
.dockerignore
.git
.gitignore
.pytest_cache
.ruff_cache
.venv
Dockerfile
README.md
analysis
data
docker
docs
pyproject.toml
spark-warehouse
src
tests
uv.lock
--- docs
ai-usage
baseline-session.zsh
caching-experiment.md
caching-session.zsh
data-sources.md
demo.md
experiments.md
figures
implementation-plan.md
job-queue.md
job-table.md
measurements
pandas-baseline.md
partition-experiment.md
partition-session.zsh
results.md
spec.md
stride-session.zsh
```

## 5. Assistant — 2026-10-23T19:38:55.550Z

### Tool call: Bash

```
{
  "command": "SNAP=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/worktree-snapshot-before.txt && for w in .claude/worktrees/worker-pipeline .claude/worktrees/extension-baseline; do echo \"=== $w\"; git --no-optional-locks -C \"$w\" rev-parse HEAD; git --no-optional-locks -C \"$w\" status --porcelain=v1 --untracked-files=all; done | tee \"$SNAP\" | head -60; echo \"--- lines in snapshot: $(wc -l < \"$SNAP\")\"",
  "description": "Snapshot linked worktrees' HEAD and status without taking locks"
}
```

## 6. User — 2026-10-23T19:38:57.127Z

### Tool result

```
=== .claude/worktrees/worker-pipeline
d2d8615de49e33b0fc2db8b8ff768ee8085fd81b
 M README.md
 M docs/job-queue.md
 M docs/job-table.md
 M docs/spec.md
 M pyproject.toml
 M tests/mutation_check.py
 M tests/test_jobs_kafka.py
 M tests/test_jobs_launcher.py
 M tests/test_jobs_pipeline.py
 M uv.lock
?? docs/worker-pipeline.md
?? tests/test_jobs_live_pipeline.py
=== .claude/worktrees/extension-baseline
a70c066fc1c18a4b9cfea803d6e8759ff63357e7
--- lines in snapshot:       16
```

## 7. Assistant — 2026-10-23T19:39:05.213Z

### Tool call: Bash

```
{
  "command": "echo \"=== main (git grep)\" && git grep -n -E '\\bE[12]\\b|[Rr]ecovery' main -- docs README.md ':!docs/ai-usage' | cut -c1-260 | head -60; echo \"=== M2 worktree files (read-only grep)\"; grep -n -E '\\bE[12]\\b|[Rr]ecovery' .claude/worktrees/worker-pipeline/docs/*.md .claude/worktrees/worker-pipeline/README.md | cut -c1-260 | head -80",
  "description": "Search docs on main and the M2 worktree for E1/E2 and recovery"
}
```

## 8. User — 2026-10-23T19:39:05.882Z

### Tool result

```
=== main (git grep)
main:README.md:386:   and Redis for a job queue and a result cache, with recovery and caching
main:README.md:389:   the real pipeline in the worker comes next, then the recovery experiments
main:docs/spec.md:24:| Extension (optional) | Job queue (MySQL job table, Kafka), result cache (Redis), Docker Compose; recovery and caching experiments (§11) | **In progress**: the job queue with a simulated pipeline: the MySQL job table, a worker, Kafka del
main:docs/spec.md:61:recovery, result caching) are in §11; they concern the infrastructure around
main:docs/spec.md:673:| Systems extension | MySQL job table with guarded state transitions, attempt tokens and leases; a worker with a simulated pipeline ([job-table.md](job-table.md)); Kafka delivery with confirmed publication and manual commits, and the reco
main:docs/spec.md:802:- Recovery (E1, E2): each failure case is injected on purpose; detection and
main:docs/spec.md:803:  recovery times, executions per job, accepted results per job and lost jobs are
main:docs/spec.md:837:    each batch of the recovery experiments should start on a fresh MySQL
main:docs/spec.md:849:recovery experiments and the result cache; each stops for review. The Docker
=== M2 worktree files (read-only grep)
.claude/worktrees/worker-pipeline/docs/worker-pipeline.md:180:recovery times of E2 include that wait.
.claude/worktrees/worker-pipeline/docs/worker-pipeline.md:212:  recovery experiments (M3) restarts it.
.claude/worktrees/worker-pipeline/docs/spec.md:25:| Extension (optional) | Job queue (MySQL job table, Kafka), result cache (Redis), Docker Compose; recovery and caching experiments (§11) | **In progress**: the job queue: the MySQL job table, Kafka delivery a
.claude/worktrees/worker-pipeline/docs/spec.md:62:recovery, result caching) are in §11; they concern the infrastructure around
.claude/worktrees/worker-pipeline/docs/spec.md:215:    B --> E2[shuffle-partition experiment<br/>batch CSV and criteria]
.claude/worktrees/worker-pipeline/docs/spec.md:222:    E2 --> F
.claude/worktrees/worker-pipeline/docs/spec.md:677:| Systems extension | MySQL job table with guarded state transitions, attempt tokens and leases, a store id, and run digests recorded at acceptance ([job-table.md](job-table.md)); a worker running windows → 
.claude/worktrees/worker-pipeline/docs/spec.md:800:- **E1.** Does each job accept at most one result, and does every successfully
.claude/worktrees/worker-pipeline/docs/spec.md:802:- **E2.** After a worker crash (before or after its claim), a broker restart or a
.claude/worktrees/worker-pipeline/docs/spec.md:813:- Recovery (E1, E2): each failure case is injected on purpose; detection and
.claude/worktrees/worker-pipeline/docs/spec.md:814:  recovery times, executions per job, accepted results per job and lost jobs are
.claude/worktrees/worker-pipeline/docs/spec.md:848:    each batch of the recovery experiments should start on a fresh MySQL
.claude/worktrees/worker-pipeline/docs/spec.md:860:recovery experiments and the result cache; each stops for review. The Docker
.claude/worktrees/worker-pipeline/README.md:409:   and Redis for a job queue and a result cache, with recovery and caching
.claude/worktrees/worker-pipeline/README.md:412:   the real pipeline in the worker comes next, then the recovery experiments
```

## 9. Assistant — 2026-10-23T19:39:09.593Z

Spec §11 defines E1 and E2, and the M2 worktree has an in-progress revision of it. I'll read §11 in both versions (main = committed; M2 = uncommitted, possibly still changing).

## 10. Assistant — 2026-10-23T19:39:10.600Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^#{1,3} ' .claude/worktrees/worker-pipeline/docs/spec.md | sed -n '1,80p'",
  "description": "List spec section headings in the M2 worktree copy"
}
```

## 11. User — 2026-10-23T19:39:11.089Z

### Tool result

```
1:# Leveraged ETF Risk Analytics — specification
28:## 1. Purpose and scope
49:## 2. Research questions
65:## 3. Model — implemented (`src/etf_risk/model.py`)
119:## 4. Data inputs and outputs
121:### Implemented
151:### Planned
156:## 5. Module hierarchy and data flow
242:## 6. Validation approach
244:### Implemented
332:## 7. Fixed 252-trading-day windows — implemented (Stage 2)
392:## 8. Expected results
443:### What the stride-21 run showed (`full-2026-10-12`, after the cleanup)
489:### Spark SQL analyses of the run of record
509:### What the stride experiment showed (2026-10-19)
552:### What the shuffle-partition experiment showed (2026-10-22)
593:### What the pandas baseline showed (2026-10-22)
625:### What the caching experiment showed (2026-10-22)
666:## 9. Status summary
680:## 10. Known issues and open items after the Stage 2 cleanup
735:## 11. Systems extension — in progress (optional)
```

## 12. Assistant — 2026-10-23T19:39:13.771Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/docs/spec.md",
  "offset": 735
}
```

## 13. User — 2026-10-23T19:39:13.967Z

### Tool result

````
735	## 11. Systems extension — in progress (optional)
736	
737	An exploratory layer around the batch pipeline: analysis jobs are submitted,
738	queued, run by a worker and tracked, and summary queries can be served from a
739	cache. Nothing in sections 3–10 depends on it, and each of its stages can be the
740	last. These exist:
741	- the Docker image (§9);
742	- the job table, its state transitions and the store id
743	  ([job-table.md](job-table.md));
744	- Kafka delivery with the reconciler ([job-queue.md](job-queue.md));
745	- a worker that runs the real pipeline: renewals, an absolute-deadline watchdog,
746	  a host execution lock, process-tree cleanup, reconnects, the run digest
747	  recorded at acceptance, and the job commands
748	  ([worker-pipeline.md](worker-pipeline.md)).
749	
750	These are tested on SQLite and against MySQL 8.4.13 and Kafka 4.3.1. Everything
751	else below is planned and may change at review.
752	
753	| Component | Role | Notes |
754	|---|---|---|
755	| MySQL 8 | job table: the single source of truth for job state | parameters, input checksums, status, attempt number and token, lease, accepted attempt (and so its run id), error |
756	| Kafka (one broker, KRaft) | job queue: one topic carrying job ids | delivery at least once; one partition; no replica |
757	| Worker | runs the existing CLIs (`etf_risk.windows` → `etf_risk.spark_pipeline` → `etf_risk.verify`) in a subprocess for each job it claims | one job at a time on this machine, for memory |
758	| Reconciler | requeues jobs whose lease expired and republishes jobs whose publication was never confirmed | each change conditional on what it read: the attempt token for a requeue, the job's version for a recorded publication |
759	| Redis | cache-aside for summary-query results | key: run id + normalized query; run outputs never change, so entries need no invalidation |
760	| Docker Compose | starts only the services one experiment needs, each with a memory limit | service tests are excluded from the default, offline test run |
761	
762	```mermaid
763	flowchart LR
764	    S[submit CLI] -->|insert job as queued| DB[(MySQL jobs)]
765	    S -->|publish job id, wait for confirmation| K[[Kafka topic]]
766	    S -->|then set published_at| DB
767	    K --> W[worker]
768	    W -->|claim: new attempt token and lease| DB
769	    W -->|commit offset after the claim| K
770	    W --> P["windows → spark_pipeline → verify"]
771	    P --> O[run folder per attempt]
772	    W -->|accept result if the token still matches| DB
773	    R[reconciler] -->|expired lease or unconfirmed publish| DB
774	    R -->|republish| K
775	    Q[summary query] -->|hit| C[(Redis)]
776	    Q -->|miss: Spark SQL on paired| O
777	```
778	
779	**Guarantee.** Each job accepts at most one result. A successfully completed job
780	has one accepted result. A job may execute more than once: Kafka delivers at
781	least once, and a lease can expire while a slow worker still runs.
782	
783	- **Attempt tokens.** Every claim writes a new attempt token and attempt number
784	  in one conditional update. Lease renewal and the final status write both
785	  require that token; an update that matches no row means the worker was fenced
786	  off: it stops, and its outputs are not accepted.
787	- **Run ids include the attempt**, so attempts never share an output folder, and
788	  the pipeline never overwrites outputs.
789	- **Manual offset commits.** Auto-commit is off; the worker commits the Kafka
790	  offset only after its claim succeeded, or after deciding the job needs nothing
791	  (already succeeded, or held by a live lease). A worker that dies before
792	  committing gets the job redelivered.
793	- **Publish confirmation.** The producer (`acks=all`, idempotence on) waits for
794	  Kafka's delivery confirmation before `published_at` is set; otherwise the
795	  reconciler publishes again. With one broker, `acks=all` means that broker
796	  wrote the message; there is no replica.
797	
798	**Engineering questions**
799	
800	- **E1.** Does each job accept at most one result, and does every successfully
801	  completed job have exactly one, even when jobs execute more than once?
802	- **E2.** After a worker crash (before or after its claim), a broker restart or a
803	  database restart, how long until the job runs again and finishes, and is any
804	  job lost or accepted twice?
805	- **E3.** How much latency does a result cache save for repeated summary queries
806	  compared with a warm Spark session, at which hit rates, and what happens when
807	  Redis is down?
808	
809	**Planned experiments**
810	
811	- An accepted result counts as correct when its run passes every check (§6) and
812	  matches a reference run by content (Parquet files differ in bytes between runs).
813	- Recovery (E1, E2): each failure case is injected on purpose; detection and
814	  recovery times, executions per job, accepted results per job and lost jobs are
815	  recorded.
816	- Result cache (E3): latency of a new Spark process, a warm Spark session and a
817	  Redis hit, at hit rates set by the workload; the fallback to Spark with Redis
818	  stopped.
819	- Optional: Spark task retries. Local mode does not retry a failed task; a
820	  `local[N,F]` master with one injected failure shows a retry.
821	
822	**Memory budgets (to validate, not proven limits)**
823	
824	- Pipeline container: 2.5 GiB without swap. It held for stride 21 on the tested
825	  machine only (Docker Desktop's VM with 3.83 GiB on the 8 GiB Apple Silicon
826	  laptop), with peaks of 2,282 and 2,342 MiB (cgroup `memory.peak`, which
827	  includes page cache); other machines, settings and denser strides need their
828	  own check.
829	- Kafka heap 256 MiB in a 640 MiB container; MySQL with a 64 MiB buffer pool and
830	  `performance_schema` off in 512 MiB; Redis `maxmemory` 32 MiB (`allkeys-lru`)
831	  in 128 MiB. Each budget is checked against measured peaks when its service is
832	  introduced and changed if exceeded.
833	- MySQL and Kafka were measured on 2026-10-23 with the job tests (cgroup
834	  `memory.peak`, which includes page cache).
835	  - One full run on fresh containers peaked at 324–398 MiB for MySQL and
836	    354–478 MiB for Kafka, over three runs; the run of commit e2806bd gave 398 and
837	    478 MiB.
838	  - Two full runs in a row on a fresh MySQL container reached 472 MiB, 92%.
839	    Kafka reached 516 MiB, 80%, in a session that also ran three mutation checks
840	    against it, which create many short-lived topics and consumer groups.
841	  - About two hours of repeated runs on the same containers reached 511 MiB for
842	    MySQL, 99% of its budget. Its anonymous memory had grown from 264 MiB after
843	    one run to 313 MiB; the rest was page cache. Kafka reached 404 MiB, 63%.
844	    Neither container hit its limit.
845	  - MySQL's 511 MiB shows limited headroom. It is not evidence that longer runs
846	    stay within 512 MiB: its anonymous memory was still growing, and nothing
847	    longer was measured. Neither budget was exceeded, so both stand for now, but
848	    each batch of the recovery experiments should start on a fresh MySQL
849	    container and record its own peak.
850	- Docker Desktop's VM has 3.83 GiB here. Timings inside containers form a
851	  separate configuration and are not compared with the native measurements (§8).
852	
853	**Not claimed:** throughput or scaling beyond one machine (Kafka and MySQL run as
854	single instances); durability beyond one broker and one database on this
855	machine; cache results for workloads other than these small, unchanging result
856	tables; any change to the analysis results in §8.
857	
858	**Stages and authorship.** The job table and the worker, then Kafka delivery
859	and the reconciler, with the Compose services added one at a time; then the
860	recovery experiments and the result cache; each stops for review. The Docker
861	image, the Compose services, the job table, the worker and the reconciler are
862	written with Claude Code; the cache logic and the experiments by the project
863	author, with tutoring.
864	
````

## 14. Assistant — 2026-10-23T19:39:15.802Z

### Tool call: Bash

```
{
  "command": "git diff --no-index --stat <(git show main:docs/spec.md) .claude/worktrees/worker-pipeline/docs/spec.md 2>/dev/null | tail -1; echo \"--- §11 diff main -> M2 worktree\"; diff <(git show main:docs/spec.md | sed -n '/^## 11\\./,$p') <(sed -n '/^## 11\\./,$p' .claude/worktrees/worker-pipeline/docs/spec.md) | head -120",
  "description": "Diff spec §11 between main and the M2 worktree copy"
}
```

## 15. User — 2026-10-23T19:39:16.253Z

### Tool result

```
--- §11 diff main -> M2 worktree
6,10c6,17
< last. The Docker image (§9) and the job queue with a simulated pipeline exist:
< the job table, its state transitions and a worker ([job-table.md](job-table.md)),
< and Kafka delivery with the reconciler ([job-queue.md](job-queue.md)), tested
< on SQLite and against MySQL 8.4.13 and Kafka 4.3.1. Everything else below is
< planned and may change at review.
---
> last. These exist:
> - the Docker image (§9);
> - the job table, its state transitions and the store id
>   ([job-table.md](job-table.md));
> - Kafka delivery with the reconciler ([job-queue.md](job-queue.md));
> - a worker that runs the real pipeline: renewals, an absolute-deadline watchdog,
>   a host execution lock, process-tree cleanup, reconnects, the run digest
>   recorded at acceptance, and the job commands
>   ([worker-pipeline.md](worker-pipeline.md)).
> 
> These are tested on SQLite and against MySQL 8.4.13 and Kafka 4.3.1. Everything
> else below is planned and may change at review.
```

## 16. Assistant — 2026-10-23T19:39:32.826Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/docs/worker-pipeline.md"
}
```

## 17. User — 2026-10-23T19:39:34.134Z

### Tool result

```
1	# The worker's real pipeline: steps, deadlines, the host lock and cleanup
2	
3	How the worker runs a job's windows → spark_pipeline → verify, and what keeps a failure from
4	leaving a second Spark run, a stray process or a wrong result behind. This is milestone M2 of
5	the systems extension ([spec §11](spec.md)). It builds on [job-table.md](job-table.md)
6	(claims, tokens, transactions) and [job-queue.md](job-queue.md) (publication, delivery, the
7	reconciler).
8	
9	The guarantee is unchanged, and still kept only by the token guards: each job accepts at
10	most one result, and every succeeded job has exactly one. What this milestone adds:
11	- the accepted result is bound to its files: `job_attempts.result_digest`;
12	- no replacement Spark work starts while an earlier attempt's process tree survives;
13	- nothing an attempt started outlives it.
14	
15	## A job's steps
16	
17	[`SubprocessPipeline`](../src/etf_risk/jobs/pipeline.py) runs three CLIs, each as
18	`<python> -m etf_risk.<module>`, with absolute paths, under a
19	[launcher](../src/etf_risk/jobs/launcher.py) of its own:
20	
21	| Step | Command | Writes |
22	|---|---|---|
23	| windows | `windows --snapshot S --processed-root <abs> --kind K --window-days N --stride N --anchor A --out-root <run dir>/windows --name <name>` | `<run dir>/windows/S/<name>/` |
24	| spark_pipeline | `spark_pipeline --windows <that folder> --out-root <run dir>/output --run-id <run id>` | `<run dir>/output/S/<name>/<run id>/` (the run folder) |
25	| verify | `verify --run <run folder> --sample-ticker T` | `verify.json` in the run folder |
26	
27	The job's parameters ([`params.py`](../src/etf_risk/jobs/params.py)):
28	- snapshot, window kind, window days, stride (at least 21: a job has no `--allow-dense-stride`),
29	  anchor, and the ticker verify samples;
30	- unknown keys are refused;
31	- `submit` records the SHA-256 of the snapshot's return files and `quality_report.json`, and
32	  the worker checks them again before step 1. A difference fails the attempt for good.
33	
34	The run folder is `<output root>/<store id>/job-<id>-attempt-<n>/`. The store id
35	([job-table.md](job-table.md)) keeps a recreated job table from reusing old folders.
36	
37	The step's environment is built from an allowlist, so no service URL or password reaches a
38	step. It holds:
39	- the attempt's marker, `ETF_RISK_ATTEMPT=<store id>:<run id>:<attempt key>`, where the key
40	  is the first 16 hex digits of SHA-256(token); the token itself never leaves the worker;
41	- `TMPDIR` and `SPARK_LOCAL_DIRS` in `<run dir>/.work`, which is also the working directory, so
42	  `spark-warehouse` lands there too;
43	- `java.io.tmpdir` in `.work`, through `SPARK_SUBMIT_OPTS="-Djava.io.tmpdir=… -XX:-UsePerfData"`.
44	  The macOS JDK ignores `TMPDIR`. `JAVA_TOOL_OPTIONS` is never used: its "Picked up" notice
45	  would replace the Java version that `run.json` records;
46	- `PYSPARK_PYTHON` and `PYSPARK_DRIVER_PYTHON` naming this interpreter. Without them Spark's
47	  Python workers run whatever `python3` comes first on `PATH`; outside `uv run` that is not the
48	  project's.
49	
50	## Accepting a result
51	
52	A run counts as a result only if all of these hold:
53	- every step exited 0;
54	- `run.json` has status `ok`;
55	- every count in `checks.json` is 0;
56	- `verify.json` reports no mismatch and the same breached windows;
57	- each of the four tables has its `_SUCCESS` file.
58	
59	Then the worker:
60	1. removes `.work`;
61	2. writes `attempt.json` (worker, steps with exit codes, times, lock waits and peak memory,
62	   the settings, and `code_state()`);
63	3. writes `manifest.json`, the run folder's manifest ([`runs.py`](../src/etf_risk/runs.py));
64	4. renews once more;
65	5. calls `accept_result(claim, digest)`. The store records the digest in the same
66	   token-guarded transaction ([job-table.md](job-table.md)).
67	
68	Nothing in the folder changes afterwards.
69	
70	## Failures
71	
72	The worker classifies a failure from the records, not from the exit code alone: an uncaught
73	exception exits 1, as "checks failed" does.
74	
75	| What happened | Result |
76	|---|---|
77	| exit 3 (an input checksum differs); `run.json` status `checks_failed`; a verify mismatch; parameters or input checksums that do not fit | failed, not retryable |
78	| a signal; a step over its time limit; status `failed`; a missing record; the host lock still busy after the wait; a launcher that failed | failed, retryable (the job is requeued until `max_attempts`) |
79	| a renewal refused; a deadline passed without a renewal | fenced: nothing more is written |
80	
81	## Deadlines and the watchdog
82	
83	Leases in the job table are wall-clock times. Every local deadline uses the host's
84	monotonic clock ([`timing.py`](../src/etf_risk/jobs/timing.py)):
85	
86	| Setting | Value | Role |
87	|---|---|---|
88	| lease | 60 s | the store's `DEFAULT_LEASE` |
89	| renew_interval | 10 s | time between renewals while a step runs |
90	| fence_margin, M | 10 s | the deadline is `F = m0 + lease − M`, with `m0` just before the last successful renewal started |
91	| watchdog_tick, t_w | 0.5 s | how often a launcher looks at its deadline |
92	| term_grace + kill_confirm, G | 5 + 2 s | SIGTERM, then SIGKILL, then the tree must be gone |
93	| safety, ε | 2.5 s | M ≥ t_w + G + ε |
94	
95	The launcher is a process of its own:
96	- It receives absolute deadlines over a pipe: a handshake first, then one line per successful
97	  renewal, each with a sequence number. The handshake also checks that the worker and the
98	  launcher read the same clock.
99	- It ends the tree once `now ≥ F`. The tree is therefore gone by `F + t_w + G`, before the
100	  lease can expire, whatever the worker is doing: blocked in a database call, stopped or
101	  dead.
102	- The worker's own timeouts play no part in this: no time limit is claimed for a whole
103	  database operation.
104	
105	On each tick the launcher:
106	1. checks whether its deadline has passed. If it has, it fires, and firing is terminal;
107	2. only otherwise reads the waiting lines. A line moves the deadline only if its sequence
108	   number is newer, its deadline is later, and that deadline is still in the future.
109	
110	So lines that queued up while the launcher was stopped cannot revive an expired watchdog, and
111	no line can push the deadline past what the worker granted
112	(`test_stopped_past_its_deadline_…` and `test_stopped_briefly_…` in
113	[tests/test_jobs_launcher.py](../tests/test_jobs_launcher.py)).
114	
115	The worker also checks F on every 1 s tick. It renews before each step and before acceptance,
116	fences itself once F passes without a renewal, and never starts a step or accepts after F.
117	Closing the pipe (EOF) makes the launcher end the tree. If the launcher does not act within
118	the kill grace plus 10 s, because it is stopped, the worker ends the tree itself.
119	
120	## The host execution lock
121	
122	Before a step starts, its launcher:
123	- takes an exclusive `flock` on the host's lock (`~/.cache/etf-risk/locks/spark-exec.lock`;
124	  tests use their own);
125	- waits until no process of another launcher's tree survives. A registry next to the lock has
126	  one file per launcher whose tree may still run, which also finds the orphans of a launcher
127	  that was killed.
128	
129	Both waits are bounded together by the step limit + G + 30 s; after that the attempt fails as
130	retryable ("execution lock busy"). The step's driver inherits the lock. PySpark closes
131	inherited descriptors before it starts the JVM, and the JVM exits when the driver's pipe
132	breaks; the survivor check covers that window.
133	
134	So no replacement Spark step starts while an earlier tree survives, even when the whole tree
135	is stopped (watchdog included) or the wall clock jumps. On this machine, steps run one at a
136	time, which is the memory rule of spec §11.
137	
138	## Ending a process tree
139	
140	[`processes.py`](../src/etf_risk/jobs/processes.py):
141	- **Membership.** Each launcher leads a session of its own, and nothing below it calls
142	  `setsid`. An attempt's processes are those in the launcher's session that carry its marker.
143	  PySpark's daemon moves itself and its Python workers to a process group of their own
144	  (`pyspark/daemon.py`: `os.setpgid(0, 0)`), so a process-group kill would miss them; the
145	  session does not. A reused pid never counts: the marker must match.
146	- **Termination.** SIGTERM to all, so the JVM's shutdown hooks can delete its scratch; SIGKILL
147	  after the grace; then rescans until nothing is left.
148	
149	## After a lost database connection
150	
151	[`store.py`](../src/etf_risk/jobs/store.py), "Connections":
152	- the store replaces a broken connection only at the start of an operation, and after a ping
153	  that fails when the connection sat idle for 60 s. A ping never uses PyMySQL's
154	  `reconnect=True`, which would drop the session settings;
155	- a transaction whose connection broke is abandoned with it: its remaining statements never
156	  run on a new connection, since they would commit one by one there;
157	- a broken connection gets no ROLLBACK, and the failed operation is not replayed;
158	- a COMMIT whose reply was lost is resolved by repeating `accept_result`, which reports the
159	  acceptance for the same token and digest.
160	
161	Session settings ([`mysql.SERVICE_SESSION`](../src/etf_risk/jobs/mysql.py)), for liveness
162	only: connect 3 s; read and write 5 s per I/O; `innodb_lock_wait_timeout` 2 s, below the read
163	timeout, so lock waits end as definite conflicts; `wait_timeout` 120 s, so a frozen client's
164	open transaction cannot hold row locks for long.
165	
166	The worker retries `accept_result` and `fail_attempt` after a lost connection until F, and
167	renewals at the next interval.
168	
169	## Kafka group timing
170	
171	| Setting | Value | Why |
172	|---|---|---|
173	| `group.protocol` | `classic` | `session.timeout.ms` is ignored under `consumer` |
174	| `session.timeout.ms`, `heartbeat.interval.ms` | 15 s, 3 s | a stopped or crashed worker leaves the group well before its lease can expire |
175	| `max.poll.interval.ms` | attempt limit + G + 60 s = 967 s | `serve()` does not poll while a pipeline runs. A run that outlasted the interval would make the worker leave the group, and a standby could take the partition |
176	| `socket.timeout.ms` | 10 s | a commit or publication waits at most that long per request |
177	
178	Under the classic protocol, a joining standby waits for a busy worker to poll before it gets
179	the partition; `test_a_standby_gets_the_next_job_only_once_…` shows this against Kafka. The
180	recovery times of E2 include that wait.
181	
182	## Starting, stopping and sweeping
183	
184	`python -m etf_risk.jobs` ([`cli.py`](../src/etf_risk/jobs/cli.py); the README's runbook has
185	the commands). The subcommands are `init-db`, `create-topic`, `submit`, `worker`,
186	`reconciler`, `status [--check]`, `cleanup` (a dry run) and `export`.
187	
188	The worker:
189	- **Restarts its serve loop** in the same process, with backoff, after transport errors only:
190	  a lost connection, a claim race, or a Kafka error that is not fatal. Any other error ends it
191	  with exit code 1.
192	- **Stops gracefully on SIGTERM or SIGINT.** It ends the running tree, fails the attempt as
193	  retryable (so the job is requeued at once), and leaves the consumer group. On a job's last
194	  attempt that fails the job, so batches drain before their workers stop.
195	- **Sweeps at startup** (`startup_sweep`):
196	  - it ends the trees of this store's attempts that are no longer valid;
197	  - it keeps every valid active one, whoever runs it;
198	  - it leaves other stores' trees alone;
199	  - it removes only the scratch of attempts that ended;
200	  - with the database out of reach, it does nothing.
201	
202	`submit` exits 75 when the insert's outcome is unknown (its COMMIT reply was lost) and is
203	never repeated on its own.
204	
205	## Known limits
206	
207	- **One machine.** The lock, the registry and the markers are per user on one host. The
208	  launcher's clock handshake confirms that the worker and its launchers read the same
209	  monotonic clock.
210	- **Restarts.** A worker killed with SIGKILL is not restarted by anything in the project. A
211	  standby worker in the same group takes over its partition, or the session harness of the
212	  recovery experiments (M3) restarts it.
213	- **Worker memory.** The worker process imports pandas and pyarrow (through `params.py` and
214	  provenance); its memory is in the status below.
215	
216	## What is checked where
217	
218	- **Offline:**
219	  - [tests/test_jobs_launcher.py](../tests/test_jobs_launcher.py): the watchdog, with real
220	    process trees (a moved process group, a double-forked orphan), pause and resume with
221	    queued stale lines, the lock (also held by a process that is no launcher), survivors,
222	    the handshake, the step limit, EOF and SIGTERM;
223	  - [tests/test_jobs_pipeline.py](../tests/test_jobs_pipeline.py): the pipeline with stand-in
224	    steps. It covers the result rule and records; refused, failing and hanging renewals,
225	    including the watchdog ending the tree while the worker is stuck; stopping; the
226	    classification; and the environment;
227	  - [tests/test_jobs_reconnect.py](../tests/test_jobs_reconnect.py): reconnection. A break
228	    inside a transaction is never continued on a new connection, a lost COMMIT reply is
229	    resolved by a repeat, and idle pings;
230	  - [tests/test_jobs_sweep.py](../tests/test_jobs_sweep.py), test_jobs_params.py,
231	    test_jobs_timing.py, test_jobs_events.py and test_jobs_cli.py;
232	  - the identity and digest constraints in test_jobs_store.py.
233	- **Spark-marked:** [tests/test_jobs_worker_spark.py](../tests/test_jobs_worker_spark.py)
234	  runs the real steps through `Worker` and compares the accepted result with a direct run, by
235	  content.
236	- **Against the services:**
237	  - test_jobs_mysql.py: `KILL CONNECTION`, and session settings after a reconnect;
238	  - test_jobs_kafka.py: the standby and the poll interval;
239	  - [tests/test_jobs_live_pipeline.py](../tests/test_jobs_live_pipeline.py), with
240	    `ETF_RISK_LIVE_PIPELINE=1`: this milestone's acceptance runs.
241	- **[tests/mutation_check.py](../tests/mutation_check.py)** adds 18 mutations for this
242	  milestone, 49 in all ([job-queue.md](job-queue.md), "What is checked where"). Among them:
243	  - a reconnect inside a transaction, disconnects treated as conflicts, and
244	    `ping(reconnect=True)`;
245	  - the watchdog reading its lines before its deadline check;
246	  - a tree found by process group;
247	  - a step started without the host lock.
248	
249	*AI contribution: written with Claude Code (Opus 5.5).*
250	
```

## 18. Assistant — 2026-10-23T19:39:46.961Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/docs/job-table.md"
}
```

## 19. Assistant — 2026-10-23T19:39:46.970Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/docs/job-queue.md"
}
```

## 20. User — 2026-10-23T19:39:47.178Z

### Tool result

````
1	# Job table: claims, tokens and transactions
2	
3	How the job store ([`src/etf_risk/jobs/store.py`](../src/etf_risk/jobs/store.py)) keeps the
4	guarantee of [spec §11](spec.md): each job accepts at most one result, and every succeeded
5	job has exactly one accepted result. A job may execute more than once. The example follows
6	two workers, A and B, and job 7, with a lease of 60 seconds. How jobs reach the workers
7	through Kafka, and how the reconciler requeues and republishes them, is in
8	[job-queue.md](job-queue.md).
9	
10	## claim(): two guarded updates
11	
12	A claim tries two conditional updates of the job's row, in one transaction:
13	
14	```sql
15	-- 1. a queued job
16	UPDATE jobs SET status = 'running', attempt_number = attempt_number + 1, attempt_token = :token,
17	       lease_expires_at = :lease_expires_at, published_at = NULL, version = version + 1, updated_at = :now
18	 WHERE job_id = :job_id AND status = 'queued';
19	-- 2. only if 1 matched no row: a running job whose lease has expired, with attempts left
20	UPDATE jobs SET ... (the same)
21	 WHERE job_id = :job_id AND status = 'running' AND lease_expires_at <= :now
22	   AND attempt_number < max_attempts;
23	```
24	
25	The WHERE clause is the guard; the number of rows matched is the answer. If one update matched,
26	the same transaction reads the new attempt number, marks the previous attempt `expired` (after
27	a takeover only), and inserts the new attempt's row: its token, its run id `job-7-attempt-<n>`
28	and its output folder. If neither matched, a read only says why (finished, lease held, not
29	found). The one write that can follow, failing a job whose last attempt's lease expired,
30	carries its own guard on the token that read saw.
31	
32	## Token checks
33	
34	Renewal, acceptance and failure all use the same guard:
35	
36	```sql
37	UPDATE jobs SET ... WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token;
38	```
39	
40	There is no time in it: a token holds until a claim replaces it, and an update that matches no
41	row means the worker has been fenced off. Acceptance sets `succeeded`, a terminal status, and
42	clears the token, so no token matches afterwards: at most one result is accepted. A CHECK
43	constraint ties `accepted_attempt` to `succeeded`, so a succeeded job names exactly one.
44	
45	## Two workers, one job
46	
47	| Time | Worker A | Worker B | Job 7 afterwards |
48	|---|---|---|---|
49	| 0 s | claim: update 1 matches; attempt 1, token tA, lease until 60 s | | running, attempt 1, tA |
50	| 5 s | | a duplicate delivery; claim: neither update matches, refused (lease held) | unchanged |
51	| 10 s | renew with tA: lease until 70 s | | running, attempt 1, tA |
52	| 10–75 s | stalls, no heartbeat | | |
53	| 75 s | | claim: update 2 matches (70 ≤ 75); attempt 2, token tB; attempt 1 marked expired | running, attempt 2, tB |
54	| 80 s | renew with tA: no row matches, so A is fenced off and stops | | unchanged |
55	| 90 s | | accept with tB: succeeded, accepted attempt 2 | succeeded |
56	| 95 s | had A not stopped, accept with tA: no row matches, and the accepted attempt's token is tB, so false | | unchanged |
57	
58	Job 7 executed twice, in `job-7-attempt-1` and `job-7-attempt-2`, and accepted one result. Had
59	nobody claimed it at 75 s, A's renewal at 80 s would have matched, since tA would still be
60	current, and A could have finished: the lease decides only when a takeover may happen.
61	
62	## At the same moment
63	
64	If A and B claim queued job 7 at the same instant, both updates target the same row. In
65	MySQL, InnoDB lets the first lock the row and makes the second wait; when the first commits,
66	the waiting update reads the row as committed, not as an earlier snapshot of its own, finds
67	it running, and matches nothing. Update 2 matches nothing either, since the new lease is
68	live, so B is refused. In SQLite, `BEGIN IMMEDIATE` takes a write lock on the whole database,
69	so B's transaction starts only after A's has committed: the same outcome, for another reason.
70	Likewise when A accepts while B takes over an expired lease: whichever transaction holds the
71	row first decides, and the other then finds the job succeeded, or a token that is not its own.
72	
73	## Transactions
74	
75	- Every operation is one transaction. Apart from `submit` and `mark_published`, each writes
76	  both tables: the update of `jobs` decides, and the write to `job_attempts` records; that
77	  write must touch exactly one row, or the store raises and both tables roll back.
78	- Any exception rolls the transaction back, including a simulated crash. The tests raise at
79	  each gap between two statements (`FAULT_POINTS`) and check both tables afterwards.
80	- Every transaction locks the `jobs` row before any `job_attempts` row, and none spans a
81	  pipeline run: locks last milliseconds, and a crashed worker leaves an expiring lease, not a
82	  held lock.
83	- A COMMIT that fails may still have taken effect, so repeating an operation must be safe:
84	  `accept_result` returns true when the accepted attempt's token is the caller's.
85	- In MySQL, an operation rolled back by a deadlock or a lock wait timeout runs again, up to
86	  three runs in all.
87	
88	## The accepted result, the store's identity and lost connections (M2)
89	
90	- **The digest.** Acceptance records the result's run digest
91	  ([`runs.py`](../src/etf_risk/runs.py): the SHA-256 of a canonical manifest of the run
92	  folder's files) in its `job_attempts` update, inside the token-guarded transaction.
93	  `job_attempts_accepted_has_digest` requires a digest exactly for accepted attempts. A
94	  repeat after a failed COMMIT counts as accepted only for the same token and digest. The
95	  decision and the content it accepted are bound together.
96	- **The store id.** `job_store` holds one row, the store id, written once by `init-db`. Job
97	  and run ids start again at 1 when the tables are created anew, so folders, process markers
98	  and caches name an attempt by store id and run id together.
99	- **Lost connections.** Given a connection factory, the store replaces a broken connection
100	  only at the start of an operation, never inside a transaction. A transaction whose
101	  connection broke between two statements is abandoned: its later statements would otherwise
102	  commit one by one on a new connection, and the second statement of `accept_result` could
103	  then mark an attempt accepted while the job stayed running. A broken connection gets no
104	  ROLLBACK, and the failed operation is not replayed. Details are in
105	  [worker-pipeline.md](worker-pipeline.md).
106	
107	## What is checked where
108	
109	- [`tests/test_jobs_store.py`](../tests/test_jobs_store.py) and
110	  [`tests/test_jobs_worker.py`](../tests/test_jobs_worker.py) run on SQLite, and on MySQL as
111	  well when `ETF_RISK_MYSQL_URL` is set. On SQLite, competing connections run one after another
112	  under the database lock: those runs check the state logic, not InnoDB's row locks.
113	- [`tests/test_jobs_mysql.py`](../tests/test_jobs_mysql.py) checks the MySQL adapter offline
114	  and, against a server, the InnoDB behaviour the SQL relies on (setup in its docstring and in
115	  [`docker/compose.yaml`](../docker/compose.yaml)).
116	- [`tests/mutation_check.py`](../tests/mutation_check.py) breaks the guards and checks on
117	  purpose, one at a time, in a scratch copy of the repository, and expects the job tests to
118	  fail within a timeout. It covers the token, lease and attempts-left conditions, the
119	  rollback, the one-row check on `job_attempts` writes, the `version` bump, conflict
120	  detection, the output folder check, and the queue's guards in
121	  [job-queue.md](job-queue.md).
122	- Status when this table was merged (PR #7), on 2026-10-22:
123	  - with MySQL 8.4.13 from the Compose file and `ETF_RISK_MYSQL_URL` set, all 222 cases
124	    passed, in five runs in a row;
125	  - without the URL, 114 passed and the 7 tests that need a server were skipped;
126	  - breaking any one of eleven guards and checks by hand made at least one test fail.
127	    Those mutations were not recorded as a list; `tests/mutation_check.py` rebuilds them
128	    from this description;
129	  - on top of main at e55f76b (after the caching experiment), the job tests gave the same
130	    counts and the whole suite passed (350 passed, 7 skipped);
131	  - the MySQL container's memory peak in a full run was 339 MiB of its 512 MiB budget
132	    (cgroup `memory.peak`, which includes page cache).
133	
134	  The current status of the job tests, with the Kafka delivery of PR #8, is in
135	  [job-queue.md](job-queue.md).
136	
137	*AI contribution: written with Claude Code (Opus 5.5).*
138	
````

## 21. User — 2026-10-23T19:39:47.183Z

### Tool result

````
1	# Job queue: publication, delivery and the reconciler
2	
3	How a job reaches a worker through Kafka, and what happens when a step on the way fails:
4	milestone 2 of the systems extension ([spec §11](spec.md)). It builds on
5	[job-table.md](job-table.md), which explains claims, attempt tokens and transactions. The
6	guarantee is unchanged: each job accepts at most one result, and every succeeded job has
7	exactly one accepted result. A job may execute more than once.
8	
9	## The path of a job
10	
11	1. **Submit** ([`queue.submit_job`](../src/etf_risk/jobs/queue.py)). The job is inserted
12	   as queued, at version 0. Its id is published to the topic, and the submitter waits for
13	   the broker's confirmation. If the confirmation arrives, `published_at` is recorded.
14	2. **Deliver** ([`Worker.serve`](../src/etf_risk/jobs/worker.py)). A worker's consumer
15	   polls the id. The worker claims the job, then commits the message's offset. That is
16	   the acknowledgement. It then runs the pipeline and accepts the result with its run
17	   digest. Since M2 that is the real pipeline: windows → spark_pipeline → verify under a
18	   watchdog and the host's execution lock ([worker-pipeline.md](worker-pipeline.md)).
19	3. **Reconcile** ([`reconciler.py`](../src/etf_risk/jobs/reconciler.py)). Every few
20	   seconds, the reconciler requeues jobs whose lease expired, then publishes queued jobs
21	   with no recorded publication.
22	
23	Kafka is reached through [`kafka.py`](../src/etf_risk/jobs/kafka.py) (confluent-kafka). The
24	offline tests use [`simulated.MemoryQueue`](../src/etf_risk/jobs/simulated.py), which
25	models only what the job system relies on.
26	
27	## Settings
28	
29	| Setting | Value | Why |
30	|---|---|---|
31	| Producer `acks`, `enable.idempotence` | `all`, on | §11: with one broker and no replica, `acks=all` means that broker wrote the message |
32	| `CONFIRMATION_TIMEOUT` | 10 s | how long submit and the reconciler wait for the delivery report; librdkafka's message timeout is the same, so `False` is final. It means "not confirmed", not "not written" |
33	| Consumer `enable.auto.commit` | `false` | the worker commits after its claim, or after deciding that the job needs nothing |
34	| Consumer `auto.offset.reset` | `earliest`, set explicitly | a consumer group that never committed starts at the first message, so a job published before its group first starts is still delivered; librdkafka's default, `latest`, would skip it |
35	| `PUBLICATION_GRACE` | 30 s | a never-claimed job is published again only 30 s after it was queued, longer than its submitter waits for its own confirmation |
36	| Grace for a requeued job | none | nobody else publishes it, so it goes in the pass that requeued it |
37	| `RECONCILE_INTERVAL` | 5 s | time between passes |
38	| `DELIVERY_RETRIES` | 5, 1 s apart | how often `serve()` tries one message again after errors before its acknowledgement; the next error is raised, and the message stays uncommitted |
39	| Job id in a message | decimal, 1 to `MAX_JOB_ID` = 2⁶³ − 1: at most 19 digits, no sign, spaces or leading zeros | the largest id both job tables hold (SQLite's INTEGER is signed 64-bit). Any other payload is malformed |
40	| Consumer group timing, socket timeouts | classic protocol; session 15 s; heartbeats 3 s; max poll 967 s; sockets 10 s | pinned since M2; reasons in [worker-pipeline.md](worker-pipeline.md), "Kafka group timing" |
41	
42	## Recording a publication: the version guard
43	
44	```sql
45	UPDATE jobs SET published_at = :now, version = version + 1, updated_at = :now
46	 WHERE job_id = :job_id AND status = 'queued' AND published_at IS NULL AND version = :version;
47	```
48	
49	`published_at` means that a message for the job's *current* queued state was confirmed, so
50	the reconciler need not publish the job again. A CHECK constraint allows it only while the
51	job is queued, and a claim clears it.
52	
53	The version guard prevents a lost job. Suppose a message is published and the broker
54	confirms it. Before the submitter records the confirmation, a worker consumes the message,
55	claims the job and fails it back to queued. The message is gone. A guard on the status alone
56	would now record the publication. The job would then be queued with nothing to deliver it,
57	and the reconciler would never publish it again. With the version read before publishing,
58	the late record matches no row, and the reconciler publishes the job in its next pass.
59	`test_a_confirmation_after_the_job_moved_on_is_not_recorded` follows exactly this case.
60	
61	## Requeuing an expired lease: the token guard
62	
63	```sql
64	UPDATE jobs SET status = 'queued', attempt_token = NULL, lease_expires_at = NULL,
65	       version = version + 1, updated_at = :now
66	 WHERE job_id = :job_id AND status = 'running' AND attempt_token = :token
67	   AND lease_expires_at <= :now AND attempt_number < max_attempts;
68	```
69	
70	The token is the one the reconciler read with `expired_leases()`. The same transaction
71	marks that attempt as expired. With no attempts left, the job fails instead, through the
72	same statement claim uses (`_exhaust`). The lease condition alone is not enough. The
73	reconciler may read A's token, then B takes the job over, and B's lease expires as well
74	before the reconciler's change. Without the token, the change would requeue B's attempt on
75	A's token (`test_a_stale_token_is_refused_even_when_the_new_holders_lease_has_expired_too`).
76	
77	## A job, two failures
78	
79	Job 9, with a 60 s lease:
80	
81	| Time | What happens | Job 9 afterwards |
82	|---|---|---|
83	| 0 s | submit: inserted; published; the confirmation is lost, but the message was written | queued, no publication recorded; 1 message |
84	| 1 s | worker A polls the message, claims attempt 1, and dies before committing | running, attempt 1, lease until 61 s |
85	| 30 s | reconciler: the job is running, so it needs no publication | unchanged |
86	| 46 s | A has restarted. The group drops A's old member after the 45 s session timeout, and the new consumer starts at the last commit and gets the same message. The claim is refused (lease held) and the offset committed | unchanged |
87	| 61 s | reconciler: the lease has expired; it requeues with A's token; attempt 1 is expired; it publishes the job in the same pass and records the confirmation | queued, publication recorded; 2 messages |
88	| 62 s | A polls the new message, claims attempt 2, commits, runs and accepts | succeeded, accepted attempt 2 |
89	
90	Job 9 executed twice and accepted one result. Had the job still been queued at 30 s, with
91	its first confirmation lost, the reconciler would have published it then. The duplicate
92	message would later find the job running or finished, and the claim would refuse it.
93	`test_the_job_9_timeline` (tests/test_jobs_queue.py) follows this table row by row with
94	the in-memory queue, on SQLite and, when configured, on MySQL. That includes the lost
95	confirmation at 0 s and the pass at 30 s that leaves the running job alone.
96	`test_a_crash_between_claim_and_commit` runs the crash and the takeover, from a confirmed
97	publication, offline and against Kafka.
98	
99	## What the worker does with a delivery
100	
101	- **Acknowledgement** is a synchronous commit of the message's offset + 1, the next
102	  offset to read. It happens right after the claim, or at once when the claim is refused.
103	- **An error before the acknowledgement** rewinds the consumer to the message (a seek) and
104	  tries again; a consumer that keeps running does not see an uncommitted message again by
105	  itself. After `DELIVERY_RETRIES` tries in a row for one message, the next error is raised
106	  and ends `serve()`. The message stays uncommitted, and the consumer rewound to it, so
107	  this consumer or a restarted worker reads it again. The message is never skipped: the
108	  job may have a recorded publication, and the reconciler would not publish it again.
109	- **An error after the acknowledgement** is logged. The job's lease then expires, and the
110	  reconciler requeues it.
111	- **A failed commit** is logged, and the job goes on. It is claimed, so a later delivery of
112	  the same message is refused.
113	- **A message with no valid job id** (see Settings) is committed and skipped before
114	  anything touches the database, so it cannot block the partition or stop the worker.
115	  The format and the length are checked before any conversion, since `int()` refuses more
116	  than 4,300 digits; the range is checked after it.
117	
118	## Known limits
119	
120	- **A long outage ends `serve()`.** With the defaults, an error before the acknowledgement
121	  that lasts longer than about five seconds, such as an unreachable database, ends `serve()`
122	  with that error. The `worker` command then serves again in the same process, with backoff
123	  ([worker-pipeline.md](worker-pipeline.md), "Starting, stopping and sweeping"). The store
124	  reconnects at its next operation. A worker killed outright still needs a standby or a
125	  restart from outside.
126	- **A crashed worker frees its partition after the session timeout,** pinned at 15 s since
127	  M2 (it was librdkafka's default of 45 s). A worker that stops gracefully closes its
128	  consumer and leaves the group at once.
129	- **`max.poll.interval.ms`** is pinned at 967 s since M2, above the longest attempt plus the
130	  kill grace ([worker-pipeline.md](worker-pipeline.md), "Kafka group timing").
131	- **One partition, one job at a time**, as §11 plans: no claims about throughput.
132	
133	## What is checked where
134	
135	- [`tests/test_jobs_reconciler.py`](../tests/test_jobs_reconciler.py) and
136	  [`tests/test_jobs_queue.py`](../tests/test_jobs_queue.py) use the in-memory queue. They
137	  run on SQLite, and on MySQL as well when `ETF_RISK_MYSQL_URL` is set. They cover:
138	  - the guards and the grace period;
139	  - the job-id format, including a 5,000-digit payload and ids beyond the range, each
140	    followed by a valid job that must still run;
141	  - the worker's commits, rewinds and bounded retries;
142	  - whole scenarios, including the job-9 timeline above and a seeded run with lost
143	    publications and crashes at every one of the worker's fault points
144	    (`WORKER_FAULT_POINTS`; the store's own fault points are covered in
145	    tests/test_jobs_store.py).
146	  Tests that run a loop (`serve()`, the reconciler's `run()`) stop it themselves, after a
147	  number of tries or a few seconds, so a broken guard makes them fail rather than hang.
148	- [`tests/test_jobs_kafka.py`](../tests/test_jobs_kafka.py) checks the settings offline.
149	  With `ETF_RISK_KAFKA_BOOTSTRAP` set, it checks against Kafka 4.3.1 from
150	  [`docker/compose.yaml`](../docker/compose.yaml):
151	  - delivery to a fresh consumer group, and `latest` for comparison;
152	  - confirmation, including an unreachable broker;
153	  - commits and rewinds;
154	  - a 5,000-digit payload ahead of a job: both committed, and the job runs;
155	  - a message left uncommitted after the retries, for a restarted worker;
156	  - two end-to-end scenarios.
157	- [`tests/mutation_check.py`](../tests/mutation_check.py) breaks one guard or setting at a
158	  time, in a scratch copy of the repository, and expects the job tests to fail within a
159	  timeout. It has 49 mutations; two, conflict detection and a ping that reconnects, need
160	  MySQL. M1 added the first 31 and M2 the other 18.
161	  - **Coverage:**
162	    - the store's guards ([job-table.md](job-table.md));
163	    - the claim's cleared publication and version bump;
164	    - the publication's version guard;
165	    - the worker's acknowledgement, rewind, bounded retries and malformed-message commit;
166	    - the job-id format, length and range;
167	    - the grace period;
168	    - the Kafka settings above, including the group protocol;
169	    - since M2: the digest at acceptance and its repeat; reconnecting inside a transaction,
170	      disconnects treated as conflicts, and `ping(reconnect=True)`; the time relations; the
171	      watchdog's loop order and sequence check; trees found by process group instead of
172	      session; the host lock and the survivor wait; the clock handshake; the step
173	      environment; the startup sweep; the renewal before acceptance; and the result rule's
174	      check count ([worker-pipeline.md](worker-pipeline.md)).
175	  - **Running it:** `uv run --group jobs python tests/mutation_check.py --list` names them,
176	    and setting the service variables adds the MySQL and Kafka runs.
177	- [`etf_risk.services`](../src/etf_risk/services.py) supports the live runs:
178	  - `ready mysql kafka` waits until a login and `SELECT 1` succeed and the broker answers a
179	    metadata request. The Compose healthchecks only show that the ports are open.
180	  - `peaks mysql kafka` prints each container's cgroup `memory.peak` against its limit.
181	  - `others` counts containers of other projects in Docker's VM, without naming them.
182	- Status when this queue was merged (PR #8, revision e2806bd), on 2026-10-23. At that point
183	  the clients were installed with `uv run --with`, not from the lock:
184	  - **Offline:** 200 passed, and the 17 tests that need MySQL, Kafka or confluent-kafka
185	    were skipped.
186	  - **With Kafka 4.3.1** (the job table on SQLite): 210 passed, and the 7 tests that
187	    need MySQL were skipped.
188	  - **With MySQL 8.4.13 and Kafka 4.3.1, on the committed revision e2806bd:** 379
189	    passed, none failed or skipped, in one run on fresh containers (162 cases on each
190	    store). An earlier revision, before the job-id validation, had 353 passed.
191	  - **The whole suite:** 411 passed and 15 skipped. That run came before the bounded
192	    retries, the job-id validation and the test fixes; the rest of the suite does not
193	    use these files.
194	  - **Mutation checks:** 22 guards and settings were broken by hand, one at a time, in 25
195	    test runs: three were run both offline and against Kafka. They were not recorded as a
196	    list; `tests/mutation_check.py` rebuilds the set from these notes. Each run had a
197	    timeout. The 22 include 4 for the job-id format and range. Tests failed in all 25
198	    runs; none ran into the timeout. Before the fixes, three ran until it:
199	    - a claim that keeps the publication, through `serve()`'s unbounded retries;
200	    - the grace boundary off by one, through a test that waited for the publisher to
201	      stop the reconciler's loop;
202	    - the rewind removed, through a test that waited for a failing claim to come back.
203	  - **Memory:** spec §11 records the peaks. MySQL reached 511 of its 512 MiB over about
204	    two hours of repeated runs, and 472 MiB after two runs on a fresh container. That
205	    is limited headroom, not evidence that longer runs stay within the limit.
206	- Revalidation on 2026-10-23, with the clients from the lock (`--group jobs`), on revision
207	  9f347d1 of `feature/extension-baseline`:
208	  - **Offline:** 204 passed, and the 16 tests that need MySQL or Kafka were skipped. That
209	    is three new tests, plus one that needs only confluent-kafka and now runs.
210	  - **With MySQL 8.4.13 and Kafka 4.3.1** on fresh containers: 385 passed, none failed or
211	    skipped, in 59 s. That is the 379 cases of e2806bd plus the three new tests on both
212	    stores.
213	  - **The whole suite** (all dependency groups, through `uv run`): 473 passed and 16
214	    skipped.
215	  - **Mutation checks** (`tests/mutation_check.py`, 31 mutations):
216	    - **Offline:** 30 of 30 caught; conflict detection was skipped, since it needs MySQL.
217	    - **Against MySQL and Kafka:** 31 of 31 caught, on the same code just before it was
218	      committed. No run reached its timeout.
219	    - **Gaps found on the way:** the first offline run found two mutations that no test
220	      caught, the token in `_exhaust` and the commit of a malformed last message. The two
221	      tests named above now catch them.
222	  - **Memory**, from cgroup `memory.peak`:
223	    - after one full run on fresh containers: MySQL 332 MiB (65%), Kafka 355 MiB (56%);
224	    - after the mutation session on one fresh pair (one full run plus 31 shorter ones):
225	      MySQL 441 MiB (86%), Kafka 380 MiB (59%).
226	
227	    Four containers of another Compose project were running in Docker's VM at the time, so
228	    these are not budget measurements (spec §11 asks for none).
229	
230	## Code provenance
231	
232	Every run record identifies the job package's code. `provenance.code_state()` hashes every
233	Python module and SQL schema under `src/etf_risk/`, including `jobs/` and its schema files,
234	keyed by package-relative path, for example `jobs/store.py`. Records written before
235	2026-10-23 hash only the top-level modules. All of `jobs/` was written with Claude Code
236	(Opus 5.5), as each module's docstring says. It came in through two PRs:
237	
238	| Module | Commits | PR | Verified by |
239	|---|---|---|---|
240	| `store.py`, `schema/mysql.sql`, `schema/sqlite.sql`, `worker.py`, `simulated.py`, `__init__.py` | eec1032 (milestone 1), e2806bd (milestone 2) | #7, #8 | test_jobs_store, test_jobs_worker, test_jobs_queue, test_jobs_reconciler; mutation_check |
241	| `mysql.py` | eec1032 | #7 | test_jobs_mysql (offline and against MySQL 8.4.13) |
242	| `queue.py`, `kafka.py`, `reconciler.py` | e2806bd | #8 | test_jobs_queue, test_jobs_reconciler, test_jobs_kafka (offline and against Kafka 4.3.1); mutation_check |
243	| `store.py`, `mysql.py`, `kafka.py`, `worker.py`, `simulated.py`, `reconciler.py`, both schemas (M2a changes); `events.py`, `timing.py`, `../runs.py` | e7040f7 | M2 (`feature/worker-pipeline`) | test_jobs_store, test_jobs_reconnect, test_jobs_timing, test_jobs_events, test_runs, the live MySQL and Kafka tests; mutation_check |
244	| `pipeline.py`, `launcher.py`, `processes.py`, `params.py`, `cli.py`, `__main__.py` | d2d8615 | M2 | test_jobs_pipeline, test_jobs_launcher, test_jobs_sweep, test_jobs_params, test_jobs_cli, test_jobs_worker_spark, test_jobs_live_pipeline |
245	
246	The status notes of both PRs came in separate commits: 6cfd971 for #7 and cd72957 for #8.
247	
248	*AI contribution: written with Claude Code (Opus 5.5).*
249	
````

## 22. Assistant — 2026-10-23T19:39:53.538Z

Now the actual MySQL schema, since the SQL cross-check has to match real table and column names. `src/` is unmodified in the M2 worktree, so I'll read it from the committed branch tip.

## 23. Assistant — 2026-10-23T19:39:54.810Z

### Tool call: Bash

```
{
  "command": "git ls-tree -r --name-only feature/worker-pipeline -- src/etf_risk/jobs && echo \"=== mysql.sql\" && git show feature/worker-pipeline:src/etf_risk/jobs/schema/mysql.sql",
  "description": "List job package files and show the MySQL schema on the M2 branch"
}
```

## 24. User — 2026-10-23T19:39:55.365Z

### Tool result

```
src/etf_risk/jobs/__init__.py
src/etf_risk/jobs/__main__.py
src/etf_risk/jobs/cli.py
src/etf_risk/jobs/events.py
src/etf_risk/jobs/kafka.py
src/etf_risk/jobs/launcher.py
src/etf_risk/jobs/mysql.py
src/etf_risk/jobs/params.py
src/etf_risk/jobs/pipeline.py
src/etf_risk/jobs/processes.py
src/etf_risk/jobs/queue.py
src/etf_risk/jobs/reconciler.py
src/etf_risk/jobs/schema/mysql.sql
src/etf_risk/jobs/schema/sqlite.sql
src/etf_risk/jobs/simulated.py
src/etf_risk/jobs/store.py
src/etf_risk/jobs/timing.py
src/etf_risk/jobs/worker.py
=== mysql.sql
-- Job table of the optional systems extension (spec §11), for MySQL 8.0.16 or later:
-- earlier versions parse CHECK constraints but do not enforce them.
--
-- jobs holds each job's current state and is the only table the transition guards
-- read; job_attempts keeps one row per claim. Times are UTC, written by the store from
-- its clock. Statuses, outcomes, tokens and run ids are ascii_bin, compared byte for byte
-- as in SQLite (the default collation would ignore case). schema/sqlite.sql mirrors these
-- tables for the offline tests, and tests/test_jobs_store.py checks that both files name
-- the same columns and constraints.
--
-- job_store holds one row: the job table's identity, a random id written once by the store
-- (JobStore.ensure_identity). Job ids and run ids start again at 1 when the tables are
-- created anew, so output folders, process markers and caches name an attempt by store id
-- and run id together.
--
-- AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_store.py
-- (constraints, schema drift) and tests/test_jobs_mysql.py, on MySQL 8.4.13.

CREATE TABLE job_store (
    id               TINYINT UNSIGNED NOT NULL,
    store_id         CHAR(32)        CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    schema_version   INT UNSIGNED    NOT NULL,
    created_at       DATETIME(6)     NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT job_store_one_row CHECK (id = 1)
) ENGINE = InnoDB;

CREATE TABLE jobs (
    job_id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    params           JSON            NOT NULL,
    input_checksums  JSON            NOT NULL,
    status           VARCHAR(16)     CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    max_attempts     INT UNSIGNED    NOT NULL,
    attempt_number   INT UNSIGNED    NOT NULL,  -- claims so far; while running, the current attempt
    attempt_token    CHAR(32)        CHARACTER SET ascii COLLATE ascii_bin NULL,  -- only while running
    lease_expires_at DATETIME(6)     NULL,      -- only while running
    accepted_attempt INT UNSIGNED    NULL,      -- the one accepted attempt, only when succeeded
    error            TEXT            NULL,      -- why the job failed, only when failed
    version          BIGINT UNSIGNED NOT NULL,  -- +1 on every update, so a guarded UPDATE always changes the row
    created_at       DATETIME(6)     NOT NULL,
    updated_at       DATETIME(6)     NOT NULL,
    finished_at      DATETIME(6)     NULL,      -- only when succeeded or failed
    published_at     DATETIME(6)     NULL,      -- Kafka confirmed a publication of the job as now queued
    PRIMARY KEY (job_id),
    CONSTRAINT jobs_status CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    CONSTRAINT jobs_running_has_lease
        CHECK ((status = 'running') = (attempt_token IS NOT NULL AND lease_expires_at IS NOT NULL)),
    CONSTRAINT jobs_succeeded_has_one_result CHECK ((status = 'succeeded') = (accepted_attempt IS NOT NULL)),
    CONSTRAINT jobs_failed_has_error CHECK ((status = 'failed') = (error IS NOT NULL)),
    CONSTRAINT jobs_finished CHECK ((status IN ('succeeded', 'failed')) = (finished_at IS NOT NULL)),
    CONSTRAINT jobs_attempt_limit CHECK (max_attempts >= 1 AND attempt_number <= max_attempts),
    CONSTRAINT jobs_queued_has_attempts_left CHECK (status <> 'queued' OR attempt_number < max_attempts),
    CONSTRAINT jobs_published_only_queued CHECK (status = 'queued' OR published_at IS NULL)
) ENGINE = InnoDB;

CREATE TABLE job_attempts (
    job_id           BIGINT UNSIGNED NOT NULL,
    attempt_number   INT UNSIGNED    NOT NULL,
    attempt_token    CHAR(32)        CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    worker_id        VARCHAR(128)    NOT NULL,
    run_id           VARCHAR(64)     CHARACTER SET ascii COLLATE ascii_bin NOT NULL,  -- job-<id>-attempt-<n>
    output_dir       VARCHAR(1024)   NOT NULL,
    outcome          VARCHAR(16)     CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    error            TEXT            NULL,      -- why this attempt failed, only when failed
    result_digest    CHAR(64)        CHARACTER SET ascii COLLATE ascii_bin NULL,  -- run digest (etf_risk.runs), only when accepted
    claimed_at       DATETIME(6)     NOT NULL,
    lease_expires_at DATETIME(6)     NOT NULL,  -- as last claimed or renewed; the guards read the copy in jobs
    renewals         INT UNSIGNED    NOT NULL,
    ended_at         DATETIME(6)     NULL,
    PRIMARY KEY (job_id, attempt_number),
    CONSTRAINT job_attempts_token UNIQUE (attempt_token),
    CONSTRAINT job_attempts_run_id UNIQUE (run_id),
    CONSTRAINT job_attempts_job FOREIGN KEY (job_id) REFERENCES jobs (job_id),
    CONSTRAINT job_attempts_outcome CHECK (outcome IN ('running', 'accepted', 'failed', 'expired')),
    CONSTRAINT job_attempts_ended CHECK ((outcome = 'running') = (ended_at IS NULL)),
    CONSTRAINT job_attempts_failed_has_error CHECK ((outcome = 'failed') = (error IS NOT NULL)),
    CONSTRAINT job_attempts_accepted_has_digest CHECK ((outcome = 'accepted') = (result_digest IS NOT NULL))
) ENGINE = InnoDB;

-- Declared once job_attempts exists: the accepted result is one of the job's own attempts.
ALTER TABLE jobs ADD CONSTRAINT jobs_accepted_attempt
    FOREIGN KEY (job_id, accepted_attempt) REFERENCES job_attempts (job_id, attempt_number);
```

## 25. Assistant — 2026-10-23T19:40:10.948Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && echo \"=== store.py: outcome writes\" && git show $B:src/etf_risk/jobs/store.py | grep -n -E \"outcome|'expired'|'failed'|'accepted'|def (claim|accept_result|fail_attempt|renew|requeue|_exhaust|expired_leases)\" | head -60 && echo \"=== cli.py: status/check/export\" && git show $B:src/etf_risk/jobs/cli.py | grep -n -E \"def |check|export|status\" | head -80",
  "description": "Locate attempt-outcome writes in the store and the CLI status/export code"
}
```

## 26. User — 2026-10-23T19:40:11.465Z

### Tool result

```
=== store.py: outcome writes
fatal: ambiguous argument 'feature/worker-pipelinee.py': unknown revision or path not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
=== cli.py: status/check/export
17:    - Failures are classified from run.json, checks.json and verify.json,
19:      exited 0, the status is ok, the checks are 0, verify is clean, and
23:      and checks it before reading any line, so a fired watchdog stays
39:    - params.py: validated job parameters, and input checksums tying a job
43:      graceful stop), reconciler, status --check, cleanup (dry run) and
44:      export.
75:+  and marker (processes.py). Also in this group: the job's parameters and input checksums
81:-checks and the transactions with two workers. docs/job-queue.md explains publication,
83:+The result cache (Redis) comes later. docs/job-table.md explains claim(), the token checks
117:+    python -m etf_risk.jobs status [--check]        # the tables; --check: exit 1 on any invariant violation
119:+    python -m etf_risk.jobs export DIR              # tables, violations and settings, as JSON files
128:+- --timing NAME=SECONDS, overrides of etf_risk.jobs.timing, checked against its relations.
164:+from etf_risk.jobs.params import InvalidParams, JobParams, input_checksums
177:+def safe_url(url: str) -> str:
186:+def timing_from(overrides: list[str]) -> Timing:
195:+        return replace(DEFAULT_TIMING, **changes).check()
200:+def open_store(db: str, timing: Timing) -> JobStore:
205:+        return JobStore(None, SQLITE, lease=lease, connect=lambda: open_sqlite(path, check_same_thread=False))
214:+def is_transport_error(error: BaseException, store: JobStore) -> bool:
224:+def stop_on_signals() -> threading.Event:
233:+def cmd_init_db(args) -> int:
266:+def cmd_create_topic(args) -> int:
279:+def cmd_submit(args) -> int:
285:+        checksums = input_checksums(resolve(args.processed_root), params.snapshot)
291:+        job_id = store.submit(params.to_dict(), checksums, max_attempts=args.max_attempts)
296:+                  " Check with `status` before submitting again.", file=sys.stderr)
312:+def cmd_worker(args) -> int:
349:+def cmd_reconciler(args) -> int:
365:+def rows(records: list[dict]) -> list[dict]:
370:+def cmd_status(args) -> int:
376:+    counts = {s.value: sum(1 for j in jobs if j["status"] is s) for s in Status}
381:+        print(f"  job {j['job_id']}: {j['status'].value}; attempts {outcomes or '-'}"
383:+    if not args.check:
390:+def cmd_cleanup(args) -> int:
411:+def cmd_export(args) -> int:
418:+                            "exported_at_utc": datetime.now(timezone.utc).isoformat()},
422:+    print(f"exported {', '.join(files)} to {out}")
426:+def events_root(args) -> Path:
430:+def main(argv: list[str] | None = None) -> int:
459:+    status = commands.add_parser("status", parents=[common])
460:+    status.add_argument("--check", action="store_true")
461:+    status.add_argument("--job", type=int, nargs="*")
463:+    export = commands.add_parser("export", parents=[common])
464:+    export.add_argument("folder")
470:+               "reconciler": cmd_reconciler, "status": cmd_status, "cleanup": cmd_cleanup, "export": cmd_export}
516:+lock; it exits when the driver's pipe breaks, and the next launcher's survivor check covers
556:+    def __init__(self, deadline: float, seq: int):
561:+    def expired(self, now: float) -> bool:
566:+    def offer(self, line: dict, now: float) -> bool:
580:+    def __init__(self, fd: int):
584:+    def read(self) -> list[dict]:
604:+    def wait(self, timeout: float) -> None:
610:+    def __init__(self, args: argparse.Namespace):
621:+    def members(self) -> list:
624:+    def poll(self) -> str | None:
625:+        """One check of the watchdog, in the documented order; the reason to stop, if any."""
639:+    def handshake(self) -> str | None:
661:+    def acquire(self) -> str | None:
687:+    def end_tree(self, reason: str) -> None:
692:+    def drain(self) -> None:
701:+    def run(self, command: list[str]) -> int:
754:+def main(argv: list[str] | None = None) -> int:
803:+settings, not the job's: the input checksums are what tie a job to its data.
805:+input_checksums() is what submit records with the job, and what the worker checks again
839:+    def __post_init__(self) -> None:
858:+    def from_dict(cls, data: dict) -> JobParams:
869:+    def to_dict(self) -> dict:
873:+    def windows_name(self) -> str:
878:+def input_checksums(processed_root: str | Path, snapshot: str) -> dict[str, str]:
891:+def check_inputs(processed_root: str | Path, snapshot: str, recorded: dict[str, str]) -> None:
893:+    current = input_checksums(processed_root, snapshot)
945:+- run.json's status is ok;
946:+- every count in checks.json is 0;
955:+exception exits with 1, as "checks failed" does:
956:+- not retryable: a checksum error (exit 3); run.json status checks_failed; a verify
957:+  mismatch; parameters or input checksums that do not fit;
958:+- retryable: a signal; a time limit; status failed or a missing record; a busy host lock;
986:+from etf_risk.jobs.params import InvalidParams, JobParams, check_inputs
994:+def total_violations(checks: dict) -> int:
996:+    return sum(v for group in checks.values() for v in group.values())
```

## 27. Assistant — 2026-10-23T19:40:17.809Z

zsh treated `$B:s…` as a substitution modifier, so those reads hit the wrong objects (the second half grepped the commit diff, not `cli.py`). Rerunning with braces.

## 28. Assistant — 2026-10-23T19:40:19.403Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && echo \"=== store.py: outcome writes\" && git show \"${B}:src/etf_risk/jobs/store.py\" | grep -n -E \"outcome|def (claim|accept_result|fail_attempt|renew|requeue|_exhaust|expired_leases|violations|check)\" | head -70",
  "description": "Locate attempt-outcome writes and checks in the store on the M2 branch"
}
```

## 29. User — 2026-10-23T19:40:19.848Z

### Tool result

```
=== store.py: outcome writes
113:    """How an attempt ended (job_attempts.outcome); running until then."""
157:        " (SELECT COUNT(*) FROM job_attempts a WHERE a.job_id = j.job_id AND a.outcome = 'accepted')",
160:        " WHERE a.outcome = 'accepted' AND j.status <> 'succeeded'",
163:        " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt WHERE a.outcome <> 'accepted'",
168:        " AND (a.outcome IS NULL OR a.outcome <> 'running' OR a.attempt_token <> j.attempt_token)",
171:        " WHERE a.outcome = 'running' AND (j.status <> 'running' OR a.attempt_number <> j.attempt_number)",
395:    def claim(self, job_id: int, worker_id: str, output_root: str | Path) -> Claim | Refusal:
425:                self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
426:                                " WHERE job_id = :job_id AND attempt_number = :previous AND outcome = 'running'",
433:                " outcome, claimed_at, lease_expires_at, renewals)"
441:    def renew(self, claim: Claim) -> bool:
454:                            " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
460:    def accept_result(self, claim: Claim, result_digest: str) -> bool:
477:                self._write_one("UPDATE job_attempts SET outcome = 'accepted', result_digest = :digest, ended_at = :now"
478:                                " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
490:    def fail_attempt(self, claim: Claim, error: str, *, retryable: bool) -> Status | None:
507:            self._write_one("UPDATE job_attempts SET outcome = 'failed', error = :error, ended_at = :now"
508:                            " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
513:    def requeue_expired(self, job_id: int, token: str) -> Status | None:
529:                self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
530:                                " WHERE job_id = :job_id AND attempt_token = :token AND outcome = 'running'",
539:    def expired_leases(self) -> list[ExpiredLease]:
598:    def _exhaust(self, job_id: int, token: str, attempt_number: int, now: datetime) -> bool:
612:        self._write_one("UPDATE job_attempts SET outcome = 'expired', ended_at = :now"
613:                        " WHERE job_id = :job_id AND attempt_number = :attempt_number AND outcome = 'running'",
715:        if "outcome" in row:
716:            row["outcome"] = Outcome(row["outcome"])
```

## 30. Assistant — 2026-10-23T19:40:23.446Z

The store already has invariant queries around lines 150–175, presumably what `status --check` runs. I'll read them so the draft SQL either adds something new or says exactly where it overlaps.

## 31. Assistant — 2026-10-23T19:40:24.581Z

### Tool call: Bash

```
{
  "command": "git show \"feature/worker-pipeline:src/etf_risk/jobs/store.py\" | sed -n '100,200p'",
  "description": "Show the store's outcome enum and invariant queries"
}
```

## 32. User — 2026-10-23T19:40:25.329Z

### Tool result

```
class Status(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


TERMINAL = frozenset({Status.SUCCEEDED, Status.FAILED})


class Outcome(StrEnum):
    """How an attempt ended (job_attempts.outcome); running until then."""
    RUNNING = "running"
    ACCEPTED = "accepted"
    FAILED = "failed"
    EXPIRED = "expired"          # its lease expired, and a claim took the job over or failed it


class Refusal(StrEnum):
    """Why claim() started no attempt. In every case the delivery needs nothing more."""
    NOT_FOUND = "not_found"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    LEASE_HELD = "lease_held"    # running under a live lease: its holder owns the job
    EXHAUSTED = "exhausted"      # the lease expired with no attempts left: the job is now failed


# The status changes each operation may make; the tests check every change against it.
TRANSITIONS: dict[str, frozenset[tuple[Status, Status]]] = {
    "claim": frozenset({(Status.QUEUED, Status.RUNNING), (Status.RUNNING, Status.RUNNING)}),
    "renew": frozenset({(Status.RUNNING, Status.RUNNING)}),
    "accept_result": frozenset({(Status.RUNNING, Status.SUCCEEDED)}),
    "fail_attempt": frozenset({(Status.RUNNING, Status.QUEUED), (Status.RUNNING, Status.FAILED)}),
    "exhaust": frozenset({(Status.RUNNING, Status.FAILED)}),
    "mark_published": frozenset({(Status.QUEUED, Status.QUEUED)}),
    "requeue_expired": frozenset({(Status.RUNNING, Status.QUEUED), (Status.RUNNING, Status.FAILED)}),
}

# The gaps between the statements of one transaction where JobStore(fault=...) is called;
# the tests raise there and check that both tables roll back.
FAULT_POINTS = (
    "claim.jobs_updated",               # the job is taken; job_attempts not yet written
    "claim.previous_attempt_expired",   # takeover: the old attempt is marked, the new one not yet inserted
    "renew.jobs_updated",
    "accept_result.jobs_updated",
    "fail_attempt.jobs_updated",
    "exhaust.jobs_updated",
    "requeue_expired.jobs_updated",
)

# Each query lists the jobs that break one invariant of the guarantee or of the agreement
# between the two tables; the CHECK constraints cannot state these across rows.
INVARIANT_QUERIES = {
    "succeeded without exactly one accepted attempt":
        "SELECT j.job_id FROM jobs j WHERE j.status = 'succeeded' AND 1 <>"
        " (SELECT COUNT(*) FROM job_attempts a WHERE a.job_id = j.job_id AND a.outcome = 'accepted')",
    "accepted attempt of a job that did not succeed":
        "SELECT DISTINCT a.job_id FROM job_attempts a JOIN jobs j ON j.job_id = a.job_id"
        " WHERE a.outcome = 'accepted' AND j.status <> 'succeeded'",
    "accepted_attempt names an attempt that was not accepted":
        "SELECT j.job_id FROM jobs j JOIN job_attempts a"
        " ON a.job_id = j.job_id AND a.attempt_number = j.accepted_attempt WHERE a.outcome <> 'accepted'",
    "running job whose current attempt is not running under its token":
        "SELECT j.job_id FROM jobs j LEFT JOIN job_attempts a"
        " ON a.job_id = j.job_id AND a.attempt_number = j.attempt_number"
        " WHERE j.status = 'running'"
        " AND (a.outcome IS NULL OR a.outcome <> 'running' OR a.attempt_token <> j.attempt_token)",
    "running attempt that is not its job's current one":
        "SELECT DISTINCT a.job_id FROM job_attempts a JOIN jobs j ON j.job_id = a.job_id"
        " WHERE a.outcome = 'running' AND (j.status <> 'running' OR a.attempt_number <> j.attempt_number)",
    "attempt rows differ from attempt_number":
        "SELECT j.job_id FROM jobs j WHERE j.attempt_number <>"
        " (SELECT COUNT(*) FROM job_attempts a WHERE a.job_id = j.job_id)",
    "attempts share an output folder":
        "SELECT MIN(job_id) FROM job_attempts GROUP BY output_dir HAVING COUNT(*) > 1",
}

_TIME_COLUMNS = frozenset({"lease_expires_at", "created_at", "updated_at", "finished_at", "published_at",
                           "claimed_at", "ended_at"})
_JSON_COLUMNS = frozenset({"params", "input_checksums"})


class StoreInvariantError(RuntimeError):
    """A job_attempts write did not touch exactly one row: the two tables would disagree."""


class ClaimRace(RuntimeError):
    """The job changed between claim's guards and the read that classifies the refusal.

    Impossible on SQLite, whose write lock covers the whole transaction. In MySQL it should
    not happen under REPEATABLE READ, where the refused UPDATE keeps the row locked until the
    transaction ends; under READ COMMITTED that lock is released at once, so another claim
    can change the row before the read. The MySQL tests ran competing claims under both
    levels without it, but none forces that gap. The delivery then fails unacknowledged and
    is delivered again."""


class Clock(Protocol):
    def now(self) -> datetime: ...   # timezone-aware, UTC
```

## 33. Assistant — 2026-10-23T19:40:58.062Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && echo \"=== events.py (head)\" && git show \"${B}:src/etf_risk/jobs/events.py\" | sed -n '1,80p' && echo \"=== cli.py export/status\" && git show \"${B}:src/etf_risk/jobs/cli.py\" | sed -n '/^def cmd_status/,/^def events_root/p'",
  "description": "Show the events module header and the CLI status and export commands"
}
```

## 34. User — 2026-10-23T19:40:58.622Z

### Tool result

```
=== events.py (head)
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
=== cli.py export/status
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
```

## 35. Assistant — 2026-10-23T19:41:09.808Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && for f in worker reconciler queue cli pipeline launcher; do echo \"=== $f.py\"; git show \"${B}:src/etf_risk/jobs/$f.py\" | grep -n -o -E '(events|log|self\\.events|self\\._events)\\.log\\(\"[a-z_]+\"[^)]{0,110}' | head -40; done",
  "description": "List the event names logged by each job component"
}
```

## 36. User — 2026-10-23T19:41:10.180Z

### Tool result

```
=== worker.py
145:self.events.log("refused", job_id=job_id, reason=claim.value
148:self.events.log("claimed", job_id=job_id, attempt=claim.attempt_number, run_id=claim.run_id
162:self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="pipeline", why=str(fenced
171:self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="accept_result"
173:self.events.log("accepted", job_id=job_id, attempt=claim.attempt_number, digest=digest
187:self.events.log("retry", job_id=claim.job_id, attempt=claim.attempt_number, operation=name,
213:self.events.log("malformed", position=repr(delivery.position
217:self.events.log("delivered", job_id=job_id, position=repr(delivery.position
230:self.events.log("failed_after_ack", job_id=job_id
239:self.events.log("gave_up", job_id=job_id, failures=failures
242:self.events.log("rewound", job_id=job_id, failures=failures
256:self.events.log("commit_failed", position=repr(delivery.position
=== reconciler.py
69:self.events.log("requeued", job_id=lease.job_id
72:self.events.log("exhausted", job_id=lease.job_id
75:self.events.log("stale", job_id=lease.job_id, during="requeue"
82:self.events.log("unconfirmed", job_id=job.job_id
85:self.events.log("published", job_id=job.job_id, attempts_so_far=job.attempt_number
88:self.events.log("stale", job_id=job.job_id, during="publication"
99:self.events.log("pass_failed", error=f"{type(error
=== queue.py
=== cli.py
185:events.log("submit_unknown", error=f"{type(error
197:events.log("record_failed", job_id=job_id, error=f"{type(error
198:events.log("submitted", job_id=job_id, published=published, recorded=recorded, params=params.to_dict(
213:events.log("started", db=safe_url(args.db
227:events.log("worker_failed", error=f"{type(error
230:events.log("serve_restarted", error=f"{type(error
236:events.log("stopped"
249:events.log("started", db=safe_url(args.db
252:events.log("stopped"
=== pipeline.py
116:self.events.log("renewal_failed", job_id=self.claim.job_id, attempt=self.claim.attempt_number,
119:self.events.log("renewed" if ok else "renewal_refused", job_id=self.claim.job_id,
233:self.events.log("keepalive_dropped", seq=line.get("seq"
247:self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name
294:self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number,
379:events.log("sweep_skipped", error=f"{type(error
404:events.log("sweep", preserved=len(report["preserved"]
=== launcher.py
```

## 37. Assistant — 2026-10-23T19:41:18.038Z

### Tool call: Bash

```
{
  "command": "git show \"feature/worker-pipeline:src/etf_risk/jobs/worker.py\" | sed -n '125,200p'",
  "description": "Show the worker's claim, run, accept and fail path"
}
```

## 38. User — 2026-10-23T19:41:18.601Z

### Tool result

```
    commit_failures: int = 0      # commits that raised; the job went on


class Worker:
    def __init__(self, store: JobStore, pipeline: Pipeline, output_root: str | Path, *,
                 worker_id: str | None = None, fault: Callable[[str], None] | None = None,
                 events: EventLog = NO_EVENTS, sleep: Callable[[float], None] = time.sleep):
        self.store = store
        self.pipeline = pipeline
        self.output_root = Path(output_root)
        self.worker_id = worker_id or f"worker-{os.getpid()}-{secrets.token_hex(3)}"
        self._fault = fault or (lambda point: None)
        self.events = events
        self._sleep = sleep

    def handle(self, job_id: int, acknowledge: Callable[[], None]) -> Handled:
        self._fault("before_claim")
        claimed_mono = time.monotonic()
        claim = self.store.claim(job_id, self.worker_id, self.output_root)
        if isinstance(claim, Refusal):
            self.events.log("refused", job_id=job_id, reason=claim.value)
            acknowledge()
            return Handled(job_id, Result.SKIPPED, reason=claim)
        self.events.log("claimed", job_id=job_id, attempt=claim.attempt_number, run_id=claim.run_id)
        self._fault("after_claim")
        acknowledge()
        try:
            claim.output_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            # Run ids are unique within one job table, so this folder comes from elsewhere,
            # for example a job table created anew: never write into it.
            return self._failed(claim, f"output folder already exists: {claim.output_dir}", retryable=False)
        except OSError as error:
            return self._failed(claim, f"cannot create the output folder: {error}", retryable=True)
        try:
            digest = self.pipeline.run(claim, claim.output_dir, Heartbeat(self.store, claim, claimed_mono))
        except Fenced as fenced:
            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="pipeline", why=str(fenced))
            return Handled(job_id, Result.FENCED, claim=claim)
        except PipelineError as error:
            return self._failed(claim, str(error), retryable=error.retryable)
        except Exception as error:
            # Not a failure the pipeline reported: recorded with its type, and retried like one.
            return self._failed(claim, f"{type(error).__name__}: {error}", retryable=True)
        self._fault("after_pipeline")
        if not self._until_deadline(lambda: self.store.accept_result(claim, digest), claim, "accept_result"):
            self.events.log("fenced", job_id=job_id, attempt=claim.attempt_number, during="accept_result")
            return Handled(job_id, Result.FENCED, claim=claim)
        self.events.log("accepted", job_id=job_id, attempt=claim.attempt_number, digest=digest)
        self._fault("after_accept")
        return Handled(job_id, Result.ACCEPTED, claim=claim)

    def _until_deadline(self, operation: Callable[[], Any], claim: Claim, name: str) -> Any:
        """operation(), tried again after a lost connection while the pipeline's deadline
        (fence_at, time.monotonic()) has not passed; any other error, or no deadline, raises."""
        while True:
            try:
                return operation()
            except Exception as error:
                deadline = getattr(self.pipeline, "fence_at", None)
                if deadline is None or time.monotonic() >= deadline or not self.store.dialect.is_disconnect(error):
                    raise
                self.events.log("retry", job_id=claim.job_id, attempt=claim.attempt_number, operation=name,
                                error=f"{type(error).__name__}: {error}")
                self._sleep(1.0)

    def serve(self, consumer: Consumer, *, stop: Callable[[], bool] = lambda: False, stop_when_idle: bool = False,
              poll_timeout: float = 1.0, retry_delay: float = 1.0, retries: int = DELIVERY_RETRIES,
              on_handled: Callable[[Handled], None] | None = None,
              sleep: Callable[[float], None] = time.sleep) -> Served:
        """Handle deliveries one at a time until stop() is true (checked before each poll)
        or, with stop_when_idle, until a poll returns nothing. One message is tried again
        after errors before its acknowledgement at most `retries` times in a row; the next
        such error is raised, with the message uncommitted and the consumer rewound to it.
        BaseException, such as a simulated crash, ends serve() at once, with nothing more
        acknowledged."""
```

## 39. Assistant — 2026-10-23T19:41:28.761Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && echo \"=== worker.py: _failed + fault points\" && git show \"${B}:src/etf_risk/jobs/worker.py\" | grep -n -E \"def _failed|WORKER_FAULT_POINTS|_fault\\(\\\"|events.log\\(\\\"(attempt_failed|failed)\" | head; git show \"${B}:src/etf_risk/jobs/worker.py\" | sed -n '/def _failed/,/^    def /p' | head -25; echo \"=== cli.py: fault/timing/stop flags\"; git show \"${B}:src/etf_risk/jobs/cli.py\" | grep -n -E \"add_argument\" | head -40",
  "description": "Show worker failure handling, fault points and CLI flags"
}
```

## 40. User — 2026-10-23T19:41:29.667Z

### Tool result

```
=== worker.py: _failed + fault points
35:Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash
59:WORKER_FAULT_POINTS = (
141:        self._fault("before_claim")
149:        self._fault("after_claim")
169:        self._fault("after_pipeline")
174:        self._fault("after_accept")
230:                    self.events.log("failed_after_ack", job_id=job_id)
260:    def _failed(self, claim: Claim, error: str, *, retryable: bool) -> Handled:
    def _failed(self, claim: Claim, error: str, *, retryable: bool) -> Handled:
        status = self._until_deadline(lambda: self.store.fail_attempt(claim, error, retryable=retryable),
                                      claim, "fail_attempt")
        result = {None: Result.FENCED, Status.QUEUED: Result.REQUEUED, Status.FAILED: Result.FAILED}[status]
        self.events.log(result.value, job_id=claim.job_id, attempt=claim.attempt_number, retryable=retryable,
                        error=error[-2000:])
        return Handled(claim.job_id, result, claim=claim)
=== cli.py: fault/timing/stop flags
324:    common.add_argument("--db", default=os.environ.get("ETF_RISK_JOBS_DB"),
326:    common.add_argument("--bootstrap", default=os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", "127.0.0.1:9094"))
327:    common.add_argument("--topic", default=os.environ.get("ETF_RISK_JOBS_TOPIC", DEFAULT_TOPIC))
328:    common.add_argument("--output-root", default="data/outputs/jobs")
329:    common.add_argument("--processed-root", default="data/processed")
330:    common.add_argument("--events", help="folder of the event logs (default: <output root>/events)")
331:    common.add_argument("--timing", action="append", default=[], metavar="NAME=SECONDS")
336:    submit.add_argument("--snapshot", required=True)
337:    submit.add_argument("--kind", required=True)
338:    submit.add_argument("--window-days", type=int, default=JobParams.__dataclass_fields__["window_days"].default)
339:    submit.add_argument("--stride", type=int, default=JobParams.__dataclass_fields__["stride"].default)
340:    submit.add_argument("--anchor", default=JobParams.__dataclass_fields__["anchor"].default)
341:    submit.add_argument("--sample-ticker", default=JobParams.__dataclass_fields__["sample_ticker"].default)
342:    submit.add_argument("--max-attempts", type=int, default=3)
344:    worker.add_argument("--group", default=DEFAULT_GROUP)
345:    worker.add_argument("--worker-id")
346:    worker.add_argument("--lock", default=str(DEFAULT_LOCK))
347:    worker.add_argument("--standby", action="store_true", help="recorded in the events; any worker can stand by")
349:    reconciler.add_argument("--interval", type=float, default=5.0)
351:    status.add_argument("--check", action="store_true")
352:    status.add_argument("--job", type=int, nargs="*")
355:    export.add_argument("folder")
```

## 41. Assistant — 2026-10-23T19:41:42.452Z

### Tool call: Bash

```
{
  "command": "git show \"feature/worker-pipeline:src/etf_risk/jobs/worker.py\" | sed -n '1,70p'",
  "description": "Show the worker module docstring and fault point list"
}
```

## 42. User — 2026-10-23T19:41:42.845Z

### Tool result

```
"""A worker that handles one delivered job id at a time, fenced by its attempt token.

Worker.handle(job_id, acknowledge) handles one delivery:
1. claim the job (JobStore.claim);
2. acknowledge the delivery (with Kafka: commit its offset), at once if the claim was
   refused, since the job needs nothing more, or after a successful claim and before the
   run; a worker that dies before acknowledging gets the job delivered again (spec §11);
3. run the pipeline in the attempt's own new folder, <output root>/<run id>, renewing the
   lease whenever the pipeline calls its heartbeat;
4. accept the result with the run digest the pipeline returns (etf_risk.runs), or record the
   failure.
A worker whose renewal, acceptance or failure write is refused has been fenced off: it
stops and writes nothing more. Its folder stays on disk and is never referenced. After a
lost database connection, acceptance and the failure write are tried again until the
pipeline's own deadline (fence_at), if it keeps one; both are safe to repeat (store.py).
Events (claimed, refused, accepted, fenced, failed, requeued, ...) go to an EventLog.

Worker.serve(consumer) polls deliveries and hands each to handle(), acknowledging with a
synchronous commit of the message's offset. A message that carries no valid job id (as
queue.Delivery.job_id() reads it) is committed and skipped before anything touches the
database, so it cannot block the partition or stop the worker. An error before the acknowledgement rewinds the
consumer to the message and tries again after a delay, since an uncommitted message reaches
the same consumer again only that way. After DELIVERY_RETRIES such tries in a row, the next
error is raised and ends serve(). The message stays uncommitted and the consumer rewound, so
it is read again; it is never skipped, because its job may have a recorded publication, which
the reconciler does not publish again. An error after the acknowledgement is logged and left
to the lease. A commit that fails is logged and the job goes on: it is claimed, so a later
delivery of the same message is refused.

Retries after acknowledgement. Once a delivery is acknowledged, no delivery is pending for
the job. A job that fail_attempt() returned to queued, and a running job whose worker died
after acknowledging, run again only when a new delivery arrives: the reconciler publishes
them (etf_risk.jobs.reconciler).

Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash
there to model the worker process dying.

AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_worker.py,
tests/test_jobs_queue.py and tests/test_jobs_kafka.py, on SQLite and on MySQL 8.4.13.
"""
from __future__ import annotations

import logging
import os
import secrets
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from etf_risk.jobs.events import NO_EVENTS, EventLog
from etf_risk.jobs.queue import Consumer, Delivery
from etf_risk.jobs.store import Claim, JobStore, Refusal, Status

log = logging.getLogger(__name__)

WORKER_FAULT_POINTS = (
    "before_claim",
    "after_claim",       # claimed, not yet acknowledged
    "after_pipeline",    # outputs written, result not yet accepted
    "after_accept",
)
DELIVERY_RETRIES = 5    # tries again of one message after errors before its acknowledgement, then raise


class Fenced(Exception):
    """The attempt's token no longer holds the job: another attempt took it over, or it ended."""
```

## 43. Assistant — 2026-10-23T19:41:57.400Z

### Tool call: Bash

```
{
  "command": "echo \"=== main log\" && git log --oneline -8 main && echo \"=== M1 (PR #11) files\" && git diff --stat f058095 main -- . ':!docs/ai-usage' | tail -25 && echo \"=== headings: partition / caching / experiments.md\" && for f in partition-experiment caching-experiment experiments; do echo \"--- $f\"; git show \"main:docs/$f.md\" | grep -n -E '^#{1,3} |[Aa]uthorship|AI contribution|^\\*.*(written|drafted)' | head -30; done",
  "description": "Show M1's changed files and the structure of existing experiment docs"
}
```

## 44. User — 2026-10-23T19:41:58.048Z

### Tool result

```
=== main log
a628f22 Merge pull request #11 from [REDACTED:git-user]/feature/extension-baseline
a70c066 Record the extension baseline in the job docs, the spec and a README runbook
9f347d1 Add a services helper, reproducible mutation checks and three job tests
74c8481 Hash the jobs subpackage in run records and lock the job queue's clients
7b1e758 Merge pull request #10 from [REDACTED:git-user]/fix/measure-process-kinds
97c35f3 Count a Java process as the Spark JVM only when it runs Spark
f058095 Merge branch 'docs/project-status'
66a85fb Record Stage 4 as implemented in the README and spec
=== M1 (PR #11) files
 .gitignore                    |   5 +-
 README.md                     |  36 ++++++-
 docker/compose.yaml           |   2 +-
 docs/demo.md                  |  44 ++++----
 docs/job-queue.md             |  77 +++++++++++--
 docs/job-table.md             |  37 ++++---
 docs/measurements/README.md   |   6 +-
 docs/spec.md                  |  29 +++--
 pyproject.toml                |   4 +
 src/etf_risk/jobs/kafka.py    |   5 +-
 src/etf_risk/measure.py       |  78 +++++++++-----
 src/etf_risk/provenance.py    |  17 ++-
 src/etf_risk/services.py      | 156 +++++++++++++++++++++++++++
 tests/mutation_check.py       | 244 ++++++++++++++++++++++++++++++++++++++++++
 tests/test_jobs_kafka.py      |   2 +-
 tests/test_jobs_mysql.py      |   2 +-
 tests/test_jobs_queue.py      |  37 +++++++
 tests/test_jobs_reconciler.py |  14 +++
 tests/test_measure.py         |  82 +++++++++++++-
 tests/test_pandas_pipeline.py |  14 ++-
 tests/test_provenance.py      |  32 +++++-
 tests/test_services.py        |  99 +++++++++++++++++
 uv.lock                       | 117 ++++++++++++++++++++
 23 files changed, 1043 insertions(+), 96 deletions(-)
=== headings: partition / caching / experiments.md
--- partition-experiment
1:# Shuffle-partition experiment
26:## 1. Question and decisions
28:### 1.1 Question
36:### 1.2 Decided by the author (2026-10-19)
68:## 2. Configurations, workload and order
70:### 2.1 Configurations
87:### 2.2 Workload
96:### 2.3 Order and repeats
110:### 2.4 Commands and records
135:### 2.5 Earlier records with A's settings
150:## 3. Run conditions, batches and failures
152:### 3.1 Code state and batches
168:### 3.2 Machine state before each protocol
186:### 3.3 Positions
194:### 3.4 Failures and retries
215:### 3.5 Prerequisites and branch
224:## 4. Code
226:### 4.1 Pipeline flags
241:### 4.2 Execution plans and partition counts
291:### 4.3 Collector
313:### 4.4 Session helpers
336:### 4.5 Tests and validation
407:## 5. Measurements
451:## 6. Settings verification
476:## 7. Output comparison with A
517:## 8. Drift rules
534:## 9. Comparing configurations
559:## 10. Acceptance criteria
583:## 11. Predictions
600:### 11.1 Expected plans
--- caching-experiment
1:# Caching experiment
28:## 1. Question and decisions
30:### 1.1 Question
49:### 1.2 Decided by the author (2026-10-22)
83:## 2. Configurations, workload and order
85:### 2.1 Configurations
111:### 2.2 Workload
120:### 2.3 Order and repeats
129:### 2.4 Commands and records
155:### 2.5 Earlier records with A's settings
174:## 3. Run conditions, batches and failures
200:## 4. Code
202:### 4.1 The `--cache` option
236:### 4.2 Plans: the scan nodes
252:### 4.3 Collector
287:### 4.4 Session helpers
313:### 4.5 Tests and validation
405:## 5. Measurements
438:## 6. Settings and cache verification
443:### 6.1 Recorded configuration
451:### 6.2 Plan capture
458:### 6.3 Storage information, the primary proof
481:### 6.4 Fills and downstream reads in the plans
502:### 6.5 Observations
509:## 7. Output comparison with A
539:## 8. Drift rules
554:## 9. Comparing configurations
569:## 10. Acceptance criteria
591:## 11. Predictions
610:### 11.1 Expected caches
--- experiments
1:# Spark performance experiments
7:AI contribution: Claude Code (Opus 5.5) sets the tasks and acceptance criteria and reviews each
14:authorship line above, which the author chose. For Part B it wrote the shell helpers used in the
23:Status: Part A (sections 1–4) committed in `164f65a` before any measured run (the authorship line
27:## 1. Question, hypotheses and design
29:### 1.1 Question and scope
37:### 1.2 Hypotheses and measurements
50:### 1.3 Strides and order
66:## 2. Window definitions: counts and self-checks
68:### 2.1 How the sets were built
104:### 2.2 Counts
124:### 2.3 Self-checks
157:### 2.4 Count check
182:### 2.5 Baseline: the new stride-21 set equals `rolling-252-s21-r2`
200:### 2.6 Nesting
224:## 3. Run conditions and stop rules
229:### 3.1 Code state
238:### 3.2 Machine state before each protocol
253:### 3.3 Protocols
272:### 3.4 Drift check
279:### 3.5 Go/no-go for stride 3
295:### 3.6 Failures, early stops and aborts
341:### 3.7 Records and summaries
351:## 4. Predictions
357:### 4.1 Stride-21 wall time
365:### 4.2 Stride-21 peak memory
374:### 4.3 Wall time at strides 14, 7 and 3
389:### 4.4 Peak memory at strides 14, 7 and 3
413:### 4.5 Hypotheses H1 and H2
426:### 4.6 Summary
```

## 45. Assistant — 2026-10-23T19:42:03.792Z

### Tool call: Bash

```
{
  "command": "for f in partition-experiment caching-experiment; do echo \"=== $f.md 1-27\"; git show \"main:docs/$f.md\" | sed -n '1,27p'; done; echo \"=== experiments.md 1-26\"; git show main:docs/experiments.md | sed -n '1,26p'",
  "description": "Show the opening and authorship blocks of three experiment docs"
}
```

## 46. User — 2026-10-23T19:42:04.345Z

### Tool result

```
=== partition-experiment.md 1-27
# Shuffle-partition experiment

Author: I decided the configurations and rules listed in 1.2, reviewed and approved the rest of the
design and the predictions, ran the formal measurements, and wrote the Part B answers. AI
contributions are described below.

**Part A (sections 1–13): the design, the code and the predictions, committed before any measured
run (`caa0be1`).** The author approved the predictions (section 11) and the rules listed in 1.2 on
2026-10-19 and ran the formal measurements (2.4, 4.4). **Part B (sections 14–15): the results of
batch-1, run on 2026-10-22 (UTC), and the author's answers.** Batch-1 met every acceptance
criterion (10), so it is the analyzed batch, and no further batch runs (3.4). Sections 1–13, the
predictions included, are unchanged since Part A. The history of this document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-19 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the stride experiment's records. Everything not listed in
1.2 is Claude Code's proposal (section 13). The predictions in section 11 were drafted with Claude
Code and reviewed and approved by the author. Revision 1 applied a read-only review of the first
draft by a separate Claude Code session (036c80c6). Revision 2 applied the author's decisions of
the same day and described the implemented code. Revision 3 recorded the fixes from Claude Code's
review of that code (history at the end). Part B was drafted with Claude Code from batch-1's
records, with the author's statements and answers (sections 14 and 15)._

This experiment changes neither the stride experiment ([experiments.md](experiments.md)) nor its
predictions, records or collector. It writes only under `data/outputs-partitions/`.

## 1. Question and decisions

=== caching-experiment.md 1-27
# Caching experiment

Author: I decided the configurations and rules listed in 1.2, reviewed and approved the rest of the
design and the predictions, ran the formal measurements, and wrote the Part B answers. AI
contributions are described below.

**Part A (sections 1–13): the design, the code and the predictions, committed before any measured
run (`6131f83`).** The author approved the design, the predictions and the abort limits (section 11)
on 2026-10-22 as the preregistered hypotheses, and ran the formal measurements (2.4, 4.4). **Part B
(sections 14–15): the results of batch-1, run on 2026-10-22 (UTC), and the author's answers.**
Batch-1 met every acceptance criterion (10), so it is the analyzed batch, and no further batch runs
(3). Sections 1–13, the predictions included, are unchanged since Part A. The history of this
document stays at the end.

_Drafted with Claude Code (Opus 5.5) on 2026-10-22 from the author's decisions listed in 1.2, from
the code it wrote for section 4 and from the records of the shuffle-partition experiment and the
pandas baseline. Everything not listed in 1.2 as decided by the author is Claude Code's proposal
(section 13). The predictions in section 11 were drafted with Claude Code and reviewed and approved
by the author. Revision 1 applied the author's review of the draft (history at the end). Part B was
drafted with Claude Code from batch-1's records, with the author's statements and answers (sections
14 and 15)._

This experiment changes none of the earlier experiments ([experiments.md](experiments.md),
[partition-experiment.md](partition-experiment.md), [pandas-baseline.md](pandas-baseline.md)), nor
their predictions, records, collectors or session helpers. It writes only under
`data/outputs-caching/`.

=== experiments.md 1-26
# Spark performance experiments

Author: the project author, who set the question and the design (section 1), wrote the reasoning
in 2.3, 2.4 and 2.6, made the decisions behind section 3, wrote the predictions in 4.1–4.5, and
checked the parts drafted with Claude Code.

AI contribution: Claude Code (Opus 5.5) sets the tasks and acceptance criteria and reviews each
step. It drafted the parts marked _Drafted with Claude Code_: section 2, items 2.1, 2.2 and 2.5,
from the records named in each part (numbers read from the configs by script, file hashes
recomputed), section 3 from the author's decisions of 2026-10-18, and 4.6 from section 4 and the
Stage 2 records. At the author's request it also applied wording fixes from its reviews in
section 1 and in 2.1, copied the author's predictions 4.1–4.5 from the conversation into
section 4, added the sentence there that H1 is the least certain prediction, and drafted the
authorship line above, which the author chose. For Part B it wrote the shell helpers used in the
measurement session (5.2), reviewed each protocol's records, and drafted 5.1–5.5 from the records
(numbers read by script), VS Code's logs and the author's statements. At the author's request it
also wrote `analysis/collect_measurements.py`, apart from `find_protocols`, `load_runs` and
`identity_row`, which are the author's, drafted 5.6 and 5.7 from that script and its CSV, and
drafted the facts in 6.1–6.4 (the fits, the phase and memory tables and the comparison with
section 4); the answers in section 6 are the author's, with corrections and figures from its
review added at the author's request (listed at the start of section 6).

Status: Part A (sections 1–4) committed in `164f65a` before any measured run (the authorship line
was added in a later commit) and unchanged since. Five protocols were run on 2026-10-19
(section 5); Part B (sections 5 and 6) was written afterwards the same day, with no further runs.
```

## 47. Assistant — 2026-10-23T19:42:49.471Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && echo \"=== timing.py\" && git show \"${B}:src/etf_risk/jobs/timing.py\" | sed -n '1,200p' | grep -v '^\\s*$' | head -90",
  "description": "Show the job timing settings and their relations"
}
```

## 48. User — 2026-10-23T19:42:49.920Z

### Tool result

```
=== timing.py
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
        problems = []
        if self.fence_margin < self.watchdog_tick + self.kill_grace + self.safety:
            problems.append(f"fence_margin {self.fence_margin:g} s < watchdog_tick + kill_grace + safety "
                            f"({self.watchdog_tick + self.kill_grace + self.safety:g} s)")
        if self.renew_interval + self.worker_tick >= self.lease - self.fence_margin:
            problems.append(f"renew_interval + worker_tick ({self.renew_interval + self.worker_tick:g} s) must stay"
                            f" below lease - fence_margin ({self.lease - self.fence_margin:g} s)")
        if not (BROKER_MIN_SESSION_TIMEOUT <= self.session_timeout < self.lease):
            problems.append(f"session_timeout {self.session_timeout:g} s must be at least"
                            f" {BROKER_MIN_SESSION_TIMEOUT:g} s and below the lease")
        if 3 * self.heartbeat_interval > self.session_timeout:
            problems.append("the session timeout must leave room for three heartbeats")
        if self.max_poll_interval <= self.attempt_limit + self.kill_grace:
            problems.append("max_poll_interval must exceed the attempt limit plus the kill grace")
        if min(self.windows_limit, self.spark_pipeline_limit, self.verify_limit) <= 0 or self.attempt_limit <= 0:
            problems.append("limits must be positive")
        if problems:
            raise ValueError("inconsistent time settings: " + "; ".join(problems))
        return self
DEFAULT_TIMING = Timing().check()
```

## 49. Assistant — 2026-10-23T19:42:59.921Z

### Tool call: Bash

```
{
  "command": "B=feature/worker-pipeline && echo \"=== 'by content' / compare helpers on M2 branch\" && git grep -n -i -E 'by content|def (compare|same_content|content_equal|tables_equal|assert_same)' \"${B}\" -- src tests analysis | cut -c1-220 | head -20; echo \"=== runs.py defs\" && git show \"${B}:src/etf_risk/runs.py\" | grep -n -E '^def |^class ' ; echo \"=== live pipeline tests (M2 worktree, untracked; read-only)\"; W=.claude/worktrees/worker-pipeline; sed -n '1,45p' \"$W/tests/test_jobs_live_pipeline.py\"; grep -n -E '^def test_|^    def test_' \"$W/tests/test_jobs_live_pipeline.py\"",
  "description": "Find content-comparison helpers, run-record functions and M2 live tests"
}
```

## 50. User — 2026-10-23T19:43:00.608Z

### Tool result

```
=== 'by content' / compare helpers on M2 branch
feature/worker-pipeline:analysis/collect_partition_measurements.py:286:def compare_tables(ref: pa.Table, run: pa.Table, key: list[str], breach: list[str],
feature/worker-pipeline:src/etf_risk/plots.py:802:def compare_documented(results: dict) -> list[str]:
feature/worker-pipeline:src/etf_risk/plots.py:874:def compare_copies(names) -> tuple[list[str], list[str], list[str]]:
feature/worker-pipeline:src/etf_risk/runs.py:9:between runs that are equal by content, and two such runs have different digests
feature/worker-pipeline:src/etf_risk/verify.py:118:def compare(sample: pd.DataFrame, tickers: dict[str, TickerReturns], spark_summary: pd.DataFrame,
feature/worker-pipeline:tests/test_jobs_worker_spark.py:3:bound to its run digest. It matches, by content, a direct run of the same definitions in this
feature/worker-pipeline:tests/test_partition_collector.py:45:def compare(run: pa.Table) -> list[str]:
=== runs.py defs
32:def is_digest(value: object) -> bool:
37:def _sha256(path: Path) -> str:
45:def manifest(folder: str | Path) -> dict:
64:def digest(manifest: dict) -> str:
69:def folder_digest(folder: str | Path) -> str:
=== live pipeline tests (M2 worktree, untracked; read-only)
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
import pytest

from etf_risk import runs
from etf_risk.jobs import processes
from etf_risk.jobs.store import JobStore, Outcome, Status
from jobs_backends import KAFKA_BOOTSTRAP, MYSQL_URL

REPO = Path(__file__).resolve().parents[1]
SNAPSHOT = "full-2026-10-12"
PROCESSED = (REPO / "data" / "processed").resolve()
LIVE = os.environ.get("ETF_RISK_LIVE_PIPELINE") == "1"
pytestmark = [pytest.mark.spark, pytest.mark.skipif(
    not (LIVE and MYSQL_URL and KAFKA_BOOTSTRAP and (PROCESSED / SNAPSHOT).is_dir()),
    reason="set ETF_RISK_LIVE_PIPELINE=1, ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP, with the snapshot in data/")]
TIMING = ["--timing", "lease=24", "--timing", "renew_interval=4", "--timing", "session_timeout=10"]
282:def test_a_calendar_year_job_and_a_stride_21_job_succeed(services, references):
294:def test_a_worker_killed_during_step_2_leaves_nothing_and_the_job_is_recovered(services, references):
309:def test_a_stopped_worker_is_outlived_by_its_watchdog_and_fenced_when_it_resumes(services, references):
337:def test_a_whole_stopped_tree_keeps_the_replacement_from_starting_spark(services, references):
362:def test_a_step_over_its_limit_is_ended_and_retried_until_the_attempts_run_out(stack):
378:def test_a_database_stall_during_a_run_needs_no_manual_restart(services, references, stall):
407:def test_a_kafka_restart_during_a_run_needs_no_manual_restart(services, references):
427:def test_a_starting_worker_keeps_another_workers_running_attempt(services, references):
```

## 51. Assistant — 2026-10-23T19:45:11.539Z

### Tool call: Bash

```
{
  "command": "W=.claude/worktrees/worker-pipeline/tests/test_jobs_live_pipeline.py && grep -n -E '^def |^class |^@pytest.fixture' \"$W\" && echo \"=== check() and references\" && sed -n \"$(grep -n -E '^def (check|references|same_tables|tables_equal|reference)' \"$W\" | head -1 | cut -d: -f1),+0p\" \"$W\" >/dev/null; awk '/^def check\\(/,/^def [a-z_]+\\(/{print NR\": \"$0}' \"$W\" | head -60",
  "description": "List live-test helpers and print the check() function"
}
```

## 52. User — 2026-10-23T19:45:12.397Z

### Tool result

```
57:class Stack:
129:@pytest.fixture(scope="module")
130:def stack(tmp_path_factory, scratch_before):
139:@pytest.fixture
140:def services(stack):
147:@pytest.fixture(scope="module")
148:def references(tmp_path_factory):
168:def spark_scratch() -> set[str]:
177:@pytest.fixture(scope="module")
178:def scratch_before(references):
183:def wait_until(predicate, timeout: float, what: str, step: float = 0.5):
201:def finished(stack, job):
206:def run_dir(stack, attempt) -> Path:
210:def step_running(stack, job, attempt_number, step="spark_pipeline"):
218:def job_of(stack, marker_value):
226:def attempt_procs(stack, run_id):
236:def claimed_by_a(stack):
247:def launcher_intervals(stack) -> list[tuple[datetime, datetime, str]]:
257:def check(stack, references, job, params, *, attempts=None):
282:def test_a_calendar_year_job_and_a_stride_21_job_succeed(services, references):
294:def test_a_worker_killed_during_step_2_leaves_nothing_and_the_job_is_recovered(services, references):
309:def test_a_stopped_worker_is_outlived_by_its_watchdog_and_fenced_when_it_resumes(services, references):
337:def test_a_whole_stopped_tree_keeps_the_replacement_from_starting_spark(services, references):
362:def test_a_step_over_its_limit_is_ended_and_retried_until_the_attempts_run_out(stack):
378:def test_a_database_stall_during_a_run_needs_no_manual_restart(services, references, stall):
407:def test_a_kafka_restart_during_a_run_needs_no_manual_restart(services, references):
420:def _submit_when_kafka_is_back(stack):
427:def test_a_starting_worker_keeps_another_workers_running_attempt(services, references):
=== check() and references
257: def check(stack, references, job, params, *, attempts=None):
```

## 53. Assistant — 2026-10-23T19:45:16.467Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/worker-pipeline/tests/test_jobs_live_pipeline.py",
  "offset": 147,
  "limit": 135
}
```

## 54. User — 2026-10-23T19:45:16.664Z

### Tool result

```
147	@pytest.fixture(scope="module")
148	def references(tmp_path_factory):
149	    """Direct runs of the three CLIs, one per parameter set, made before any worker starts, so
150	    no reference run overlaps a worker's Spark step."""
151	    root, made = tmp_path_factory.mktemp("reference"), {}
152	    py = sys.executable
153	    for params in (CALENDAR, ROLLING):
154	        name = "calendar-year" if params["kind"] == "calendar-year" else f"rolling-252-s{params['stride']}"
155	        subprocess.run([py, "-m", "etf_risk.windows", "--snapshot", SNAPSHOT, "--processed-root", str(PROCESSED),
156	                        "--kind", params["kind"], "--stride", str(params["stride"]), "--out-root", str(root / "w"),
157	                        "--name", name], check=True, capture_output=True, timeout=300)
158	        subprocess.run([py, "-m", "etf_risk.spark_pipeline", "--windows", str(root / "w" / SNAPSHOT / name),
159	                        "--out-root", str(root / "out"), "--run-id", "reference"],
160	                       check=True, capture_output=True, timeout=900)
161	        made[params["kind"]] = root / "out" / SNAPSHOT / name / "reference"
162	    return lambda params: made[params["kind"]]
163	
164	
165	SCRATCH_PREFIXES = ("spark-", "blockmgr-", "pyspark-", "snappy-", "libzstd-jni", "liblz4-java", "hsperfdata_")
166	
167	
168	def spark_scratch() -> set[str]:
169	    """What Spark, PySpark and the JVM leave in the temporary folders when a run is killed."""
170	    names = set()
171	    for folder in {Path("/private/tmp"), Path(tempfile.gettempdir())}:
172	        if folder.is_dir():
173	            names |= {f"{folder}/{p.name}" for p in folder.iterdir() if p.name.startswith(SCRATCH_PREFIXES)}
174	    return names
175	
176	
177	@pytest.fixture(scope="module")
178	def scratch_before(references):
179	    """The temporary folders once the reference runs are done, before any worker starts."""
180	    return spark_scratch()
181	
182	
183	def wait_until(predicate, timeout: float, what: str, step: float = 0.5):
184	    """predicate()'s first true value. The test's own store loses its connection when MySQL
185	    stalls; that poll counts as "not yet", and the next one reconnects (store.py)."""
186	    from etf_risk.jobs.mysql import MYSQL
187	    deadline = time.monotonic() + timeout
188	    while True:
189	        try:
190	            value = predicate()
191	        except Exception as error:
192	            if not MYSQL.is_disconnect(error):
193	                raise
194	            value = None
195	        if value:
196	            return value
197	        assert time.monotonic() < deadline, f"timed out waiting for {what}"
198	        time.sleep(step)
199	
200	
201	def finished(stack, job):
202	    j = stack.store.job(job)
203	    return j if j["status"] in (Status.SUCCEEDED, Status.FAILED) else None
204	
205	
206	def run_dir(stack, attempt) -> Path:
207	    return Path(attempt["output_dir"])
208	
209	
210	def step_running(stack, job, attempt_number, step="spark_pipeline"):
211	    """The attempt's step has started its process (the launcher holds the lock and the log exists)."""
212	    attempts = stack.store.attempts(job)
213	    if len(attempts) < attempt_number:
214	        return False
215	    return (run_dir(stack, attempts[attempt_number - 1]) / "logs" / f"{step}.log").exists()
216	
217	
218	def job_of(stack, marker_value):
219	    """The job id a marker of this store names, or None."""
220	    owner = processes.parse_marker(marker_value)
221	    if owner is None or owner[0] != stack.store_id:
222	        return None
223	    return int(owner[1].split("-")[1])
224	
225	
226	def attempt_procs(stack, run_id):
227	    """The live processes of one attempt of this store (exact run id, never a prefix)."""
228	    found = []
229	    for value, procs in processes.marked_processes().items():
230	        owner = processes.parse_marker(value)
231	        if owner is not None and owner[0] == stack.store_id and owner[1] == run_id:
232	            found += procs
233	    return found
234	
235	
236	def claimed_by_a(stack):
237	    """Worker A claims a calendar-year job; only then does standby B join the group, so the
238	    job is A's, whatever partition assignment the group would have made with both present."""
239	    a = stack.worker("A")
240	    job = stack.submit(CALENDAR)
241	    wait_until(lambda: stack.store.attempts(job), 300, "worker A's claim")
242	    assert stack.store.attempts(job)[0]["worker_id"] == "A"
243	    stack.worker("B")
244	    return a, job
245	
246	
247	def launcher_intervals(stack) -> list[tuple[datetime, datetime, str]]:
248	    intervals = []
249	    for path in sorted((stack.output / stack.store_id).glob("job-*-attempt-*/logs/*.launcher.json")):
250	        result = json.loads(path.read_text())
251	        if result.get("step_started_at_utc") and result.get("tree_ended_at_utc"):
252	            intervals.append((datetime.fromisoformat(result["step_started_at_utc"]),
253	                              datetime.fromisoformat(result["tree_ended_at_utc"]), str(path)))
254	    return sorted(intervals)
255	
256	
257	def check(stack, references, job, params, *, attempts=None):
258	    j = stack.store.job(job)
259	    rows = stack.store.attempts(job)
260	    accepted = [a for a in rows if a["outcome"] is Outcome.ACCEPTED]
261	    assert j["status"] is Status.SUCCEEDED and len(accepted) == 1, (j, rows)
262	    if attempts is not None:
263	        assert len(rows) == attempts, rows
264	    a = accepted[0]
265	    record = json.loads((run_dir(stack, a) / "attempt.json").read_text())
266	    folder = run_dir(stack, a) / record["run_folder"]
267	    assert a["result_digest"] == runs.folder_digest(folder)
268	    reference = references(params)
269	    for table, key in ccm.TABLE_KEYS.items():
270	        problems, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(folder, table), key,
271	                                             ccm.cpm.BREACH_FIELDS.get(table, []))
272	        assert problems == [], (table, problems)
273	    assert stack.store.invariant_violations() == {}
274	    intervals = launcher_intervals(stack)
275	    for (s1, e1, p1), (s2, e2, p2) in zip(intervals, intervals[1:]):
276	        assert s2 >= e1, f"overlapping steps:\n  {p1} until {e1}\n  {p2} from {s2}"
277	    assert not [v for v in processes.marked_processes() if job_of(stack, v) == job]   # nothing of this job left
278	    assert spark_scratch() <= stack.scratch_before, spark_scratch() - stack.scratch_before
279	    return a, record
280	
281	
```

## 55. Assistant — 2026-10-23T19:45:29.781Z

### Tool call: Bash

```
{
  "command": "git show main:docs/caching-experiment.md | sed -n '28,84p;120,130p;174,200p;569,592p'",
  "description": "Show the caching doc's decisions, repeats, batches and acceptance sections"
}
```

## 56. User — 2026-10-23T19:45:30.173Z

### Tool result

```
## 1. Question and decisions

### 1.1 Question

For the stride-7 workload, how does caching intermediate data in Spark change runtime and peak
memory, and does it change any result? This is the caching part of research question 3 (spec §2).
The data, model, window set, leverages, Spark settings and outputs stay fixed; only what is cached
changes. The machine is the earlier experiments' (Apple M2 MacBook Air, 8 cores, 8 GiB RAM).

The pipeline already writes each output table and reads it back before later phases use it
(`materialize` in `spark_pipeline.compute`), so no phase recomputes an earlier phase's table. Two
kinds of repeated work remain, and they are what caching can remove:

- The window-member rows (`members`: each window expanded into its days and joined to the returns)
  are never written. They are built twice: for the window statistics and again for the model.
- Every later query that uses a read-back table reads it from its Parquet files: `path_days`, for
  example, in the summaries and in several checks.

Filling a cache costs a pass over its data, and the cached data occupies part of the driver JVM's
heap until it is released. The experiment measures the net effect.

### 1.2 Decided by the author (2026-10-22)

- Three configurations on the stride-7 window set (2.1, 2.2): A caches nothing; B caches the
  window-member rows; C caches them and also the four read-back tables, for reuse in all later
  phases.
- Order A–B–C–C–B–A, with four fresh-process runs per protocol: one warm-up, three measured, so 24
  runs in all (2.3).
- Claude Code writes the code, tests and helpers and drafts Part A, the predictions included, for
  the author's approval. The author runs the formal measurements and writes the answers, as in the
  shuffle-partition experiment.
- Part A is approved and committed before any caching measurement. The earlier experiments stay
  unchanged.
- In the review of the draft:
  - the downstream reads of cached data are verified apart from the `count()` that fills each
    cache, without requiring the numbers of reads found in the small dry batch (6.4);
  - a failed or aborted run's missing outputs are acceptance failures that the collector reports;
    they must not stop it (4.3, 7).

Approved by the author on 2026-10-22, before any measured run, as the preregistered hypotheses: the
A/B/C design (2.1), and the predictions and abort limits of section 11.

Approved by the author with the plan of 2026-10-22, as proposed by Claude Code:

- when each table is filled and released (2.1); the storage level `MEMORY_AND_DISK_DESER`, each
  cache filled by an explicit `count()` and released with `unpersist(blocking=True)`; a cleanup in
  `main()` on every other path, with the way each cache was released recorded (4.1);
- fill and release times inside the phase timings, with plan capture excluded as before (5);
- cache use verified first by Spark's storage information and then by the cached reads in the
  plans, where a read's row metric has three states: positive, zero (a read that counts as use) and
  missing (unknown, never proof) (6);
- all four output tables of every run, warm-ups included, compared with A's run 2 at position 1 (7);
- the shuffle-partition experiment's rules for batches, machine state, positions, failures, drift,
  comparisons and acceptance (3, 8–10), with cache verification as criterion 3.

## 2. Configurations, workload and order

### 2.3 Order and repeats

There are six protocols, at positions 1 to 6: A, B, C, C, B, A. Each protocol is one
`etf_risk.measure` call with `--repeats 4`: four fresh-process runs, the first of them a warm-up.
Each configuration therefore has two protocols, eight runs and six measured runs. The reasoning on
drift is that of partition-experiment.md 2.3: each configuration's two positions average 3.5, and a
drift that changes linearly with position alone cannot produce a difference under the rule of
section 9.

### 2.4 Commands and records

## 3. Run conditions, batches and failures

The rules of partition-experiment.md 3.1–3.4, which the author approved for that experiment, apply
with these changes:

- **Batches (3.1).** A batch is one A–B–C–C–B–A sequence, run in one session under one code state.
  Every protocol JSON and `run.json` records the same `source_sha256` and `uv_lock_sha256`, with the
  hashed paths clean; the commit is only reported. Any change to `src/`, `pyproject.toml` or
  `uv.lock` ends the batch, and a new one starts at position 1.
- **Machine state (3.2).** Required before each protocol:
  - Low Power Mode off and mains power;
  - apps other than Terminal and Finder quit;
  - a 5-minute pause;
  - read just before the start: at least 3.0 GiB available, a 5-minute load average of at most 4.0,
    and at least 30 minutes since boot.

  As in the pandas baseline, `position` writes the 3.2 checks into the run log right before each
  start.
- **Positions (3.3).** `positions.tsv` as there, with the result of the cache check (4.3) in the
  column `cache_check`.
- **Failures and retries (3.4).** The table of partition-experiment.md 3.4, with the abort limits of
  section 11. The check after each protocol verifies each run's settings, plan capture and caches
  (6). A failed check stops the session like any other stop.
- **Branch.** `feature/caching`, created from `e3b2621` on `main` (the merge of the pandas
  baseline), and later merged with a merge commit.

## 4. Code
## 10. Acceptance criteria

The collector evaluates these for one batch (4.3). The batch's results are used only if all of them
hold:

1. **Code state:** every protocol JSON and `run.json` of the batch records the same
   `source_sha256` and `uv_lock_sha256`, with the hashed paths clean (3).
2. **Inputs:** each run's `verified_sha256` holds exactly the seven inputs of 2.2, each equal to the
   hash in the stride-7 `config.json`, and each run's `windows_config` equals that file. After the
   session, the seven hashes are computed once more and are unchanged.
3. **Settings and caches:** section 6, items 6.1 to 6.4, holds for every run of the used protocols.
4. **Results:** every run of the used protocols ended `ok` with zero check violations and left its
   four tables complete. Section 7 passes for every run of the used protocols.
5. **Completeness:** each of the six positions has a used protocol of the configuration that 2.3
   puts there. It started 4 of 4 runs and all of them ended `ok`. None stopped early, none was
   aborted, and no sample exceeded 4.80 GiB. The used protocols ran in position order, and every
   protocol in the batch appears in `positions.tsv`.

If criterion 1, 2 or 3 fails, no configurations are compared until the cause is found. Stops and
re-runs follow 3. Drift (8) and run conditions are not acceptance criteria; a departure from 3.2 is
recorded as a deviation, and the protocol's results are labeled with it.

## 11. Predictions
```

## 57. Assistant — 2026-10-23T19:45:37.284Z

I have the conventions I need. One more read: the README runbook in the M2 worktree (services helper, how the live stack starts), so the outline points to commands that actually exist.

## 58. Assistant — 2026-10-23T19:45:39.327Z

### Tool call: Bash

```
{
  "command": "W=.claude/worktrees/worker-pipeline && grep -n -E '^#{1,4} ' \"$W/README.md\" | sed -n '1,60p' | grep -i -E 'job|extension|runbook|service|queue|worker' ; echo \"---\"; awk '/^#+ .*([Rr]unbook|job queue|Job queue)/{p=1} p{print NR\": \"$0} /^## /{if(p&&++n>1)exit}' \"$W/README.md\" | head -90",
  "description": "Show the job-queue runbook section of the M2 README"
}
```

## 59. User — 2026-10-23T19:45:39.754Z

### Tool result

````
278:### Systems extension services (runbook)
293:# The job tests against both services (offline, they run on SQLite and skip these)
---
278: ### Systems extension services (runbook)
279: 
280: These are for the optional job queue ([spec §11](docs/spec.md)).
281: - **Compose services.** MySQL and Kafka run in Docker Compose
282:   ([docker/compose.yaml](docker/compose.yaml)), each with a memory limit and reachable from
283:   this machine only.
284: - **Clients.** The job package's clients, PyMySQL and confluent-kafka, are pinned in the
285:   `jobs` dependency group.
286: - **Git worktrees.** In a worktree, `data/` is a symlink to the main checkout's (ignored by
287:   Git): `ln -s <main checkout>/data data`.
288: 
289: ```bash
290: docker compose -f docker/compose.yaml up -d --wait mysql kafka
291: # The healthchecks only see open ports; this waits for a MySQL login and SELECT 1, and Kafka metadata
292: uv run --group jobs python -m etf_risk.services ready mysql kafka
293: # The job tests against both services (offline, they run on SQLite and skip these)
294: ETF_RISK_MYSQL_URL=mysql://root:jobs-test@127.0.0.1:3307 ETF_RISK_KAFKA_BOOTSTRAP=127.0.0.1:9094 \
295:     uv run --group jobs python -m pytest tests/test_jobs_*.py
296: # Each container's cgroup memory.peak against its limit, and the containers of other projects (a count)
297: uv run python -m etf_risk.services peaks mysql kafka
298: uv run python -m etf_risk.services others
299: # Break each guard on purpose and expect a failing test; set the two variables to include MySQL and Kafka
300: uv run --group jobs python tests/mutation_check.py --out data/outputs-mutations
301: docker compose -f docker/compose.yaml down -v      # removes the data volumes as well
302: ```
303: 
304: - **Memory budgets** (spec §11) are measured with no other project's containers in Docker's
305:   VM; `services others --require-none` exits 1 otherwise.
306: 
307: The job queue with the real pipeline ([docs/worker-pipeline.md](docs/worker-pipeline.md)) runs
308: on the same two services. The worker, a standby worker and the reconciler each get a terminal
309: of their own, and stop with Ctrl-C (a graceful stop). Outputs go to
310: `data/outputs/jobs/<store id>/`, and event logs to `data/outputs/jobs/events/`.
311: 
312: ```bash
313: export ETF_RISK_JOBS_DB=mysql://root:jobs-test@127.0.0.1:3307/etf_jobs
314: docker compose -f docker/compose.yaml up -d --wait mysql kafka
315: uv run --group jobs python -m etf_risk.services ready mysql kafka
316: uv run --group jobs python -m etf_risk.jobs init-db          # database, tables and store id; safe to repeat
317: uv run --group jobs python -m etf_risk.jobs create-topic
318: uv run --group jobs python -m etf_risk.jobs reconciler       # terminal 2
319: uv run --group jobs python -m etf_risk.jobs worker --worker-id A    # terminal 3
320: uv run --group jobs python -m etf_risk.jobs worker --worker-id B    # terminal 4: a standby
321: uv run --group jobs python -m etf_risk.jobs submit --snapshot full-2026-10-12 --kind calendar-year
322: uv run --group jobs python -m etf_risk.jobs status --check  # the tables; exit 1 on an invariant violation
323: uv run --group jobs python -m etf_risk.jobs cleanup         # dry run: folders of attempts that ended unaccepted
324: uv run --group jobs python -m etf_risk.jobs export data/outputs/jobs-export   # before `down -v`
325: docker compose -f docker/compose.yaml down -v
326: ```
327: 
328: - **Acceptance runs.** The milestone's acceptance runs take minutes each:
329:   `ETF_RISK_LIVE_PIPELINE=1` together with the two service variables runs
330:   `tests/test_jobs_live_pipeline.py`.
331: - **Still to come.** The Redis result cache.
332: 
333: ## Data
334: 
335: Daily prices come from Yahoo Finance through yfinance and are not committed
336: (`data/` is gitignored; the data's terms of use have not been reviewed). The
337: run of record uses the full history of NVDA, AAPL, MSFT, TSLA and QQQ through
338: 2025-12-31 (snapshot `full-2026-10-12`); a 2020–2025 snapshot of the four
339: stocks was used for the prototype. Download settings, dates, checksums, the
340: checks run, and open limitations are in [docs/data-sources.md](docs/data-sources.md).
341: 
342: **Data status: partially checked, not fully verified.** Trading dates match
343: the NYSE schedule, and Adj Close is consistent with Yahoo's own dividend
344: records. For splits, none of the 23 split-day returns resembles an unadjusted
345: split; this does not independently prove that every split adjustment is
346: correct. A second-source comparison and a terms-of-use review have not been
347: done, and 36 extreme price moves, including AAPL on 2000-09-29, are
348: **unverified**.
349: 
350: ## Course concepts
````

## 60. Assistant — 2026-10-23T19:46:41.929Z

### Tool call: Bash

```
{
  "command": "echo \"=== analysis/ on main\" && git ls-tree -r --name-only main -- analysis | head -30 && echo \"=== stall fixture + DB/Kafka cases (M2 live tests)\" && W=.claude/worktrees/worker-pipeline/tests/test_jobs_live_pipeline.py && grep -n -E 'def stall|docker|pause|unpause|restart|KILL|SIGSTOP|SIGKILL|SIGCONT' \"$W\" | head -30",
  "description": "List analysis files and find how M2 live tests inject failures"
}
```

## 61. User — 2026-10-23T19:46:42.576Z

### Tool result

```
=== analysis/ on main
analysis/collect_baseline_measurements.py
analysis/collect_caching_measurements.py
analysis/collect_measurements.py
analysis/collect_partition_measurements.py
analysis/sql_comparison.py
analysis/sql_overview.py
analysis/sql_sensitivity.py
=== stall fixture + DB/Kafka cases (M2 live tests)
48:COMPOSE = ["docker", "compose", "-f", str(REPO / "docker" / "compose.yaml")]
109:                    os.kill(proc.pid, signal.SIGCONT)
300:    a.kill()                                                       # SIGKILL: the lifeline (EOF) ends the tree
310:    """Worker-only SIGSTOP during step 2. Before SIGCONT: attempt 1's tree is gone by its
312:    ended; attempt 1's renewal count no longer changes. After SIGCONT, worker A is fenced
317:    os.kill(a.pid, signal.SIGSTOP)
330:    os.kill(a.pid, signal.SIGCONT)
338:    """Whole-tree SIGSTOP (worker, launcher, Spark). Before SIGCONT: the replacement, worker
340:    SIGCONT the frozen launcher's deadline has passed: it ends its tree at once, and B goes on."""
377:@pytest.mark.parametrize("stall", ["lock-tables", "pause", "restart"])
378:def test_a_database_stall_during_a_run_needs_no_manual_restart(services, references, stall):
391:    elif stall == "pause":
392:        subprocess.run([*COMPOSE, "pause", "mysql"], check=True, capture_output=True)
394:        subprocess.run([*COMPOSE, "unpause", "mysql"], check=True, capture_output=True)
396:        subprocess.run([*COMPOSE, "restart", "mysql"], check=True, capture_output=True, timeout=120)
407:def test_a_kafka_restart_during_a_run_needs_no_manual_restart(services, references):
412:    subprocess.run([*COMPOSE, "restart", "kafka"], check=True, capture_output=True, timeout=120)
415:    second = wait_until(lambda: _submit_when_kafka_is_back(stack), 120, "a submission after the restart")
```

## 62. Assistant — 2026-10-23T19:46:53.292Z

### Tool call: Bash

```
{
  "command": "git show main:analysis/sql_overview.py | sed -n '1,30p' && echo \"...\" && git show main:analysis/sql_overview.py | grep -n -E 'WITH |SELECT|GROUP BY|HAVING|CASE|createOrReplaceTempView|spark.sql' | head -20 && git show main:analysis/sql_overview.py | sed -n \"$(git show main:analysis/sql_overview.py | grep -n -m1 -E '^\\s*(WITH|SELECT)' | cut -d: -f1),+22p\"",
  "description": "Show the style of the author's Spark SQL analysis file"
}
```

## 63. User — 2026-10-23T19:46:53.872Z

### Tool result

```
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
...
41:    paired.createOrReplaceTempView("paired")
43:    result = spark.sql("""
44:        SELECT
48:            SUM(CASE WHEN breached_2x THEN 1 ELSE 0 END) AS n_breached_2x,
49:            SUM(CASE WHEN contains_unverified_day THEN 1 ELSE 0 END) AS n_flagged,
53:        GROUP BY ticker
54:        ORDER BY CASE WHEN ticker = 'QQQ' THEN 1 ELSE 0 END, ticker
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
```

## 64. Assistant — 2026-10-23T19:49:28.273Z

### Tool call: Bash

```
{
  "command": "git show \"feature/worker-pipeline:src/etf_risk/jobs/params.py\" | sed -n '/^class JobParams/,/def __post_init__/p' | head -25; echo \"=== live test parameter sets\"; grep -n -E '^(CALENDAR|ROLLING)\\b' .claude/worktrees/worker-pipeline/tests/test_jobs_live_pipeline.py",
  "description": "Show job parameter defaults and the live tests' parameter sets"
}
```

## 65. User — 2026-10-23T19:49:28.902Z

### Tool result

```
class JobParams:
    snapshot: str
    kind: str
    window_days: int = ROLLING_WINDOW_DAYS
    stride: int = MIN_STRIDE
    anchor: str = DEFAULT_ANCHOR
    sample_ticker: str = "AAPL"

    def __post_init__(self) -> None:
=== live test parameter sets
46:CALENDAR = {"kind": "calendar-year", "stride": 21}
47:ROLLING = {"kind": "rolling", "stride": 21}
```

## 66. Assistant — 2026-10-23T19:49:37.328Z

### Tool call: Bash

```
{
  "command": "echo \"hooksPath: $(git config --get core.hooksPath || echo '(unset)')\"; echo \"active hooks: $(ls .git/hooks | grep -v '\\.sample$' | tr '\\n' ' ')\"; git check-ignore -q .claude/worktrees/recovery-outline; echo \"worktree path ignored (0=yes): $?\"; git rev-parse --verify -q refs/heads/docs/recovery-outline >/dev/null; echo \"branch docs/recovery-outline exists (0=yes): $?\"; test -e .claude/worktrees/recovery-outline; echo \"path exists (0=yes): $?\"",
  "description": "Check git hooks, ignore status and that the new names are free"
}
```

## 67. User — 2026-10-23T19:49:38.352Z

### Tool result

```
hooksPath: (unset)
active hooks: 
worktree path ignored (0=yes): 0
branch docs/recovery-outline exists (0=yes): 1
path exists (0=yes): 1
```

## 68. Assistant — 2026-10-23T19:49:49.280Z

No hooks will run, and the names are free. Before checking out, I'll check how big a full checkout is, since M2 validation is running on the same disk.

## 69. Assistant — 2026-10-23T19:49:51.037Z

### Tool call: Bash

```
{
  "command": "git ls-tree -r -l feature/worker-pipeline | awk '{n++; s+=$4} END {printf \"%d files, %.1f MiB\\n\", n, s/1048576}'; git ls-tree -r -l feature/worker-pipeline -- docs/ai-usage | awk '{n++; s+=$4} END {printf \"of which docs/ai-usage: %d files, %.1f MiB\\n\", n, s/1048576}'",
  "description": "Measure the size of a full checkout of the M2 branch"
}
```

## 70. User — 2026-10-23T19:49:51.665Z

### Tool result

```
310 files, 53.8 MiB
of which docs/ai-usage: 185 files, 50.7 MiB
```

## 71. Assistant — 2026-10-23T19:53:00.502Z

### Tool call: Bash

```
{
  "command": "git worktree add -b docs/recovery-outline .claude/worktrees/recovery-outline feature/worker-pipeline 2>&1 | tail -3 && git -C .claude/worktrees/recovery-outline log --oneline -1 && git -C .claude/worktrees/recovery-outline status --short | wc -l | xargs echo \"uncommitted entries in new worktree:\"",
  "description": "Create a drafting worktree on a new local branch"
}
```

## 72. User — 2026-10-23T19:53:02.056Z

### Tool result

```
Preparing worktree (new branch 'docs/recovery-outline')
HEAD is now at d2d8615 Run windows, spark_pipeline and verify in the worker, under a watchdog and a host lock
d2d8615 Run windows, spark_pipeline and verify in the worker, under a watchdog and a host lock
uncommitted entries in new worktree: 0
```

## 73. Assistant — 2026-10-23T19:55:33.910Z

### Tool call: Bash

```
{
  "command": "cd ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline && sed -n '205,232p' src/etf_risk/jobs/worker.py && echo \"=== pipeline.py step_started/step_ended\" && sed -n '244,250p;290,300p' src/etf_risk/jobs/pipeline.py",
  "description": "Show when deliveries are logged and what step_ended records"
}
```

## 74. User — 2026-10-23T19:55:34.395Z

### Tool result

```
            if delivery is None:
                if stop_when_idle:
                    break
                continue
            job_id = delivery.job_id()
            if job_id is None:
                log.warning("skipping a message with no valid job id at %r (%d bytes): %r", delivery.position,
                            len(delivery.value), delivery.value[:64])
                self.events.log("malformed", position=repr(delivery.position), size=len(delivery.value))
                served.malformed += 1
                self._commit(consumer, delivery, served)
                continue
            self.events.log("delivered", job_id=job_id, position=repr(delivery.position))
            acknowledged = False

            def acknowledge() -> None:
                nonlocal acknowledged
                acknowledged = True
                self._commit(consumer, delivery, served)

            try:
                handled = self.handle(job_id, acknowledge)
            except Exception:
                if acknowledged:
                    log.exception("job %s failed after its delivery was acknowledged; its lease will expire", job_id)
                    self.events.log("failed_after_ack", job_id=job_id)
                    served.failed_after_ack += 1
                    continue
=== pipeline.py step_started/step_ended
                   "--step-limit", str(t.step_limit(name)), "--cwd", str(work), "--step-log", str(logs / f"{name}.log"),
                   "--result", str(result_path), "--tick", str(t.watchdog_tick), "--term-grace", str(t.term_grace),
                   "--kill-confirm", str(t.kill_confirm), "--", *argv]
        self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name)
        with open(logs / f"{name}.launcher.log", "ab") as launcher_log:
            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=launcher_log, stderr=subprocess.STDOUT,
                                    env=env, cwd=work, start_new_session=True)
                "seconds": result.get("step_seconds"), "lock_wait_s": result.get("lock_wait_s"),
                "peak_rss_bytes": result.get("peak_rss_bytes"), "ended": result.get("ended"),
                "lingering": result.get("lingering"), "closed": closed, "launcher_exit": proc.returncode,
                "backstop": backstop}
        self.events.log("step_ended", job_id=claim.job_id, attempt=claim.attempt_number,
                        **{k: v for k, v in step.items() if k not in ("ended", "backstop")})
        return step

    # Records

    def _classify(self, step: dict, run_dir: Path, params: JobParams, claim: Claim) -> None:
```

## 75. Assistant — 2026-10-23T19:56:18.721Z

### Tool call: Bash

```
{
  "command": "grep -n -i -E 'on_assign|on_revoke|on_lost|assign|rebalance|events' src/etf_risk/jobs/kafka.py | head -20; echo \"--- cli worker wiring of events/consumer\"; sed -n '/^def cmd_worker/,/^def cmd_reconciler/p' src/etf_risk/jobs/cli.py | grep -n -i -E 'events|consumer|standby|EventLog' | head -12",
  "description": "Check whether Kafka partition assignments are logged as events"
}
```

## 76. User — 2026-10-23T19:56:19.411Z

### Tool result

```
40:from etf_risk.jobs.events import NO_EVENTS, EventLog
96:                 timing: Timing = DEFAULT_TIMING, events: EventLog = NO_EVENTS):
104:        self.events = events
115:            self.events.log("consumer_error", code=message.error().name(), reason=message.error().str())
129:    def assigned(self) -> bool:
131:        return bool(self._consumer.assignment())
--- cli worker wiring of events/consumer
2:    from etf_risk.jobs.kafka import KafkaConsumer
10:    events = EventLog(Path(events_root(args)) / f"{worker_id}.jsonl", "worker", store_id=store_id, worker_id=worker_id)
11:    events.log("started", db=safe_url(args.db), topic=args.topic, group=args.group, timing=asdict(timing),
12:               standby=args.standby)
13:    startup_sweep(store, output_root, timing=timing, events=events)
15:                                  lock_path=args.lock, timing=timing, events=events, stop=stop)
16:    worker = Worker(store, pipeline, output_root, worker_id=worker_id, events=events)
19:        consumer = KafkaConsumer(args.bootstrap, args.topic, args.group, timing=timing, events=events)
21:            worker.serve(consumer, stop=stop.is_set)
25:                events.log("worker_failed", error=f"{type(error).__name__}: {error}"[:1000])
28:            events.log("serve_restarted", error=f"{type(error).__name__}: {error}"[:500], backoff_s=backoff)
33:            consumer.close()                               # leave the group at once
```

## 77. Assistant — 2026-10-23T19:58:31.896Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'def test_a_crash_between_claim_and_commit|Simulated|simulated' tests/test_jobs_kafka.py tests/test_jobs_queue.py | head -8; echo \"--- final renewal before acceptance (pipeline.py)\"; grep -n -E 'renew|manifest|return digest|folder_digest|def run' src/etf_risk/jobs/pipeline.py | sed -n '1,30p'",
  "description": "Check the crash test's pipeline and the pre-acceptance renewal"
}
```

## 78. User — 2026-10-23T19:58:32.310Z

### Tool result

```
tests/test_jobs_queue.py:5:The queue is simulated.MemoryQueue, which models only what the job system relies on;
tests/test_jobs_queue.py:20:from etf_risk.jobs.simulated import MemoryQueue, PublishOutcome, SimulatedCrash, SimulatedPipeline
tests/test_jobs_queue.py:40:            raise SimulatedCrash(point)
tests/test_jobs_queue.py:259:def test_a_crash_between_claim_and_commit(env):
tests/test_jobs_queue.py:264:    with pytest.raises(SimulatedCrash):
tests/test_jobs_queue.py:285:    with pytest.raises(SimulatedCrash):
tests/test_jobs_queue.py:326:            raise SimulatedCrash(point)
tests/test_jobs_queue.py:331:            raise SimulatedCrash(f"step {step}")
--- final renewal before acceptance (pipeline.py)
22:Renewals. The worker's thread waits on the launcher one tick (1 s) at a time and renews the
23:lease every renew_interval. After each successful renewal it sends the launcher the absolute
25:m0 is the time just before the renewal started. The first F comes from the claim
27:- A renewal that raises, because the database is out of reach, is tried again at the next
29:- A refused renewal means the attempt was fenced off. So does a deadline that passed without
30:  a renewal: the worker fences itself. Either way, the worker closes the launcher's pipe and
34:- The worker renews before each step and before acceptance, so a fenced worker never starts
45:manifest.json records the run folder's manifest (etf_risk.runs). After a last renewal, run()
55:- fenced: a refused renewal, or a deadline that passed.
100:    given to the launcher, seq the number of the last successful renewal."""
109:    def renew(self) -> bool | None:
110:        """True: renewed; False: refused (fenced off); None: the call failed."""
116:            self.events.log("renewal_failed", job_id=self.claim.job_id, attempt=self.claim.attempt_number,
119:        self.events.log("renewed" if ok else "renewal_refused", job_id=self.claim.job_id,
127:        return now - self.last_attempt >= self.timing.renew_interval
147:    def run(self, claim: Claim, run_dir: Path, heartbeat) -> str:
150:        renewer = Renewer(heartbeat, self.timing, self.events, claim)
151:        self.fence_at = renewer.fence_at
164:            self._renew_before(renewer, claim, before=name)
165:            step = self._run_step(name, argv, env, work, logs, renewer, marker, claim)
178:        manifest = runs.manifest(run_folder)
179:        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
180:        self._renew_before(renewer, claim, before="acceptance")
181:        self.fence_at = renewer.fence_at
182:        return runs.digest(manifest)
199:    def run_folder(params: JobParams, claim: Claim, run_dir: Path) -> Path:
213:    def _renew_before(self, renewer: Renewer, claim: Claim, *, before: str) -> None:
218:            ok = renewer.renew()
219:            self.fence_at = renewer.fence_at
223:                raise Fenced(f"{claim.run_id}: the renewal before {before} was refused")
```

## 79. Assistant — 2026-10-23T20:02:56.377Z

### Tool call: Write

````
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md",
  "content": "# Recovery experiments (E1, E2): outline\n\nAuthor: _to be written by the author after review. Nothing below is decided by the author yet,\nbeyond what spec §11 says._\n\n_Drafted with Claude Code (Opus 5.5) on 2026-10-23 at the author's request, while M2's validation\nwas running. This is an outline for review, not a Part A: every case, metric, check and query in it\nis Claude Code's proposal unless it cites spec §11 or the M2 code. Repetitions, deadlines and memory\nthresholds are left open until M2's final report (section 7). Spec §11 gives the experiments to the\nproject author, with tutoring; section 9 lists what the author would decide or write. Sources: spec\n§11, [worker-pipeline.md](worker-pipeline.md), [job-table.md](job-table.md) and\n[job-queue.md](job-queue.md) as they stood in the M2 worktree on 2026-10-23, uncommitted and still\nsubject to change; the code at `d2d8615` (`feature/worker-pipeline`); and\n`tests/test_jobs_live_pipeline.py`, also uncommitted there. Nothing was run for this outline, and\nthe SQL in section 6 has not been run._\n\n## 1. Questions and scope\n\nSpec §11 asks two questions of the job queue:\n\n- **E1.** Does each job accept at most one result, and does every successfully completed job have\n  exactly one, even when jobs execute more than once?\n- **E2.** After a worker crash (before or after its claim), a broker restart or a database restart,\n  how long until the job runs again and finishes, and is any job lost or accepted twice?\n\nIt plans to inject each failure case on purpose and to record detection and recovery times,\nexecutions per job, accepted results per job and lost jobs. An accepted result counts as correct\nwhen its run passes every check (§6) and matches a reference run by content.\n\nThe token guards alone keep the guarantee ([job-table.md](job-table.md)); the time settings decide\nonly when a takeover may happen. E1 therefore tests the guards under real failures, and E2 measures\nwhat the time settings and the recovery paths cost.\n\n**Relation to M2's acceptance runs.** `tests/test_jobs_live_pipeline.py` has eight test functions,\nten cases with its three kinds of database stall. Each case runs once on a shorter clock (lease\n24 s, renewals every 4 s, session timeout 10 s), ending with `check()` where the job is meant to\nsucceed. E1 and E2 differ in three ways: each case is repeated (7.1), the clock is the one 7.2\ndecides, and every injection leaves records from which times and counts are computed (section 4).\nThe checks in `check()` are reused (section 5).\n\n## 2. Setup and workload (proposal)\n\n- **Services and processes**, as in the README runbook: MySQL 8.4.13 and Kafka 4.3.1 from\n  [docker/compose.yaml](../docker/compose.yaml); the reconciler, an active worker and a standby\n  worker as native processes; one job at a time on this machine (spec §11).\n- **A session harness** (M3 code, not written) submits the jobs, injects the failures, restarts each\n  killed worker as the next standby (Q-B), waits, and keeps the records of section 9.\n- **Batches.** Each batch starts on fresh containers (spec §11 asks it of MySQL) and ends with its\n  records, before `docker compose down -v`.\n- **Jobs.** The two parameter sets of M2's acceptance runs: kind `calendar-year` and kind `rolling`,\n  both with stride 21, on snapshot `full-2026-10-12`, with `submit`'s default of 3 attempts. Which\n  cases use which set, and how many jobs, depends on 7.1 and on the job durations M2 reports.\n- **Controls.** Jobs with no injection (case C0) give each parameter set's failure-free time to\n  finish, in the same batch.\n- **Reference runs.** One direct run of the three CLIs per parameter set, before any worker starts,\n  as the `references` fixture of the M2 tests does. Direct runs take no host execution lock, so they\n  must not overlap a worker's steps.\n\n## 3. Failure cases\n\nEach injection targets one job, in one phase of one attempt. The harness confirms from the event\nlogs that the injection landed in its phase (for W3: after the attempt's `step_started` for\n`spark_pipeline` and before its `step_ended`). An injection that landed elsewhere is recorded with\nthe phase it hit and does not count for its case.\n\n| Case | Injection | How | For | Expected path, from the design | Claims / accepted | In M2's live tests |\n|---|---|---|---|---|---|---|\n| C0 | none (control) | — | E2 | claim, run, accept | 1 / 1 | yes, both parameter sets |\n| W1 | SIGKILL of the worker after a delivery, before its claim | hook at `before_claim` (Q-A) | E2 | the offset stays uncommitted; after the session timeout the standby gets the partition and the message, and claims attempt 1 | 1 / 1 | no; offline, at the worker's fault points |\n| W2 | SIGKILL after the claim, before the offset commit | hook at `after_claim` | E1, E2 | the redelivery to the standby is refused (lease held) and committed; the lease expires; the reconciler requeues and republishes; attempt 2 | 2 / 1; attempt 1 ran no step | no; with the simulated pipeline (`test_a_crash_between_claim_and_commit`) |\n| W3 | SIGKILL during `spark_pipeline` | signal, once the step's log exists (as in M2) | E1, E2 | the launcher reads EOF and ends the tree; the lease expires; requeue; attempt 2 | 2 / 1; attempt 1 partial | yes, once |\n| W4 | SIGKILL after the pipeline, before acceptance | hook at `after_pipeline` | E1, E2 | attempt 1's complete folder is never accepted; the lease expires; requeue; attempt 2 runs in full | 2 / 1; two complete executions | no |\n| W5 | SIGKILL right after acceptance | hook at `after_accept` | E1 | nothing to recover: the offset was committed at the claim | 1 / 1 | no |\n| W6 | SIGSTOP of the worker during `spark_pipeline`; SIGCONT after the takeover | signals | E1 | the watchdog ends the stopped worker's tree before its lease expires; requeue; the standby claims attempt 2; after SIGCONT the old worker's renewal is refused and it is fenced | 2 / 1 | yes, once |\n| W7 | SIGSTOP of the worker's whole tree (worker, launcher, Spark) | signals | E1 | the replacement's step waits for the host lock while the stopped tree survives; after SIGCONT the stopped launcher, past its deadline, ends its tree. A stop longer than the replacement's lock wait fails that attempt as retryable | 2 or 3 / 1 | yes, once |\n| K1 | Kafka restart while a step runs | `docker compose restart kafka` | E2 | the running job goes on (the worker does not poll during a run); the next delivery waits for the broker | 1 / 1 | yes, once |\n| K2 | a submit while Kafka is stopped | stop Kafka, submit, start Kafka | E2 | the confirmation times out (10 s) and `published_at` stays empty; once Kafka is back and the 30 s grace has passed, the reconciler publishes the job | 1 / 1 | no; an unreachable broker's confirmation in `test_jobs_kafka.py` |\n| D1 | MySQL restart while a step runs | `docker compose restart mysql` | E2 | renewals fail and are tried again; back before F: the attempt goes on; otherwise the worker fences itself, the watchdog ends the tree, and the job is requeued once MySQL is back | 1 or 2 / 1 | yes, once (also a table lock and a pause) |\n| D2 | MySQL down at acceptance | hook that holds at `after_pipeline` while the harness restarts MySQL | E1, E2 | `accept_result` is tried again until F; back in time: accepted; otherwise the worker gives up (`failed_after_ack`) and the job runs again after its lease expires | 1 or 2 / 1 | no; a lost COMMIT reply offline (`test_jobs_reconnect.py`) |\n| X1 | the job id published again, while the job runs and after it succeeded | harness publishes | E1 | each extra delivery is refused (lease held, then succeeded) and committed; no new attempt | 1 / 1 | no; refusals offline (`test_jobs_queue.py`) |\n\nProposed core: C0, W1–W4, W6, K1, K2, D1 and X1. Optional: W5 (a control: no re-execution), W7\n(mostly a check of the host lock, which M2 covers) and D2 (the most elaborate hook).\n\n**Expected times, from the design.** In the symbols of [worker-pipeline.md](worker-pipeline.md) and\n[job-queue.md](job-queue.md): L the lease (60 s at the defaults), R the renewal interval (10 s),\nF the worker's fence deadline (L − M after its last renewal began, M = 10 s), G the kill grace\n(7 s), P the reconciler interval (5 s), S the session timeout (15 s), g the publication grace\n(30 s), and T a job's failure-free time to finish (from C0).\n\n| Case | Detection event | From the injection to the next claim |\n|---|---|---|\n| W1 | the standby's `delivered` | about S, plus the rebalance and a poll |\n| W2, W4 | the reconciler's `requeued` | L to L + P (the lease was just set or renewed), plus a delivery |\n| W3, W6 | `requeued` | between about L − R and L + P, plus a delivery |\n| K2 | the reconciler's `published` | the later of Kafka's return and g after the submit, plus up to P |\n| D1 | the worker's `renewal_failed`; then `renewed`, or else `requeued` | none if MySQL is back before F; otherwise once the lease has expired and MySQL is back, plus up to P |\n\nThe time to finish adds about T (a full run) wherever a new attempt starts. These bounds follow from\nthe settings; they become predictions only after 7.2 fixes the clock and the author approves them.\n\n## 4. Metrics\n\nEvery event has `ts`, in UTC and comparable across this machine's processes, and `mono`, for\ndurations within one process ([events.py](../src/etf_risk/jobs/events.py)). Durations from the\nharness to a worker or the reconciler therefore use `ts`. The harness writes each injection to a log\nof its own in the same format; t_inj is that record's `ts`.\n\n| Metric | Definition | Source |\n|---|---|---|\n| detection time | t_inj to the case's detection event (section 3) | injection log, event logs |\n| time to re-run | t_inj to the `claimed` event of the job's next attempt (W1: its first) | event logs; `job_attempts.claimed_at` as a cross-check |\n| time to finish | t_inj to the job's `accepted` event | event logs; `jobs.finished_at` as a cross-check |\n| recovery overhead | the job's `submitted` to `accepted`, minus the median of the same parameter set's C0 jobs in the batch | event logs |\n| claims per job | rows in `job_attempts` | Q1, `n_claims` |\n| executions per job | attempts with a `step_started` for `windows`; complete executions: attempts whose folder has a `manifest.json`, which is written only after the result rule held | event logs, attempt folders |\n| accepted results per job | accepted attempts in the table, and `accepted` events in the worker logs | Q1 `n_accepted`, Q2 `n_reports` |\n| lost jobs | submitted jobs with no row, or not finished by the drain deadline (7.2) | Q2, Q3 |\n| wasted step time | the step time of attempts that were not accepted | `logs/*.launcher.json`: step start to tree end |\n| fencing | `renewal_refused` and `fenced` events; the watchdog's end of a tree | worker logs, launcher records |\n| liveness | `serve_restarted`, `retry`, `rewound`, `gave_up`, `failed_after_ack`, `consumer_error` and `pass_failed`, per process | event logs |\n| memory | MySQL's and Kafka's `memory.peak` per batch; each step's `peak_rss_bytes`; the worker process's own peak | `services peaks`; `step_ended`; sampled by the harness |\n\nTwo gaps in the records at `d2d8615`:\n\n- No event marks a partition assignment or revocation, so W1's time cannot be split into the\n  session timeout and the rebalance (Q-D).\n- `ts` is a wall clock. A clock step during a batch would distort durations between processes; the\n  harness can record the offset between its `ts` and `mono` at the start and end of each batch and\n  flag a change.\n\n## 5. Correctness checks\n\nTwo kinds of check, kept apart:\n\n- **Validity** decides what counts, like the acceptance criteria of the earlier experiments: each\n  injection landed in its phase (section 3); the planned injections were all made; code state and\n  inputs did not change (all `attempt.json` records of a batch name the same `code_state()`, and the\n  snapshot's input checksums are unchanged afterwards); the machine-state rules held (7.3).\n- **Outcomes** answer E1 and E2 and are reported whatever they show. A failed outcome check is a\n  finding, never a reason to drop a batch.\n\nOutcome checks for each job, after its batch:\n\n1. Q1 (section 6): `n_accepted` is 1 for a succeeded job and 0 otherwise, and the verdict is `ok`.\n2. Q2: every submitted job has a row and finished; the workers' `accepted` reports agree with the\n   table, attempt and digest; no job was reported accepted by two attempts.\n3. The accepted attempt's `result_digest` equals `runs.folder_digest` of its run folder, recomputed\n   after the batch.\n4. The accepted run passes the result rule again from its files\n   ([worker-pipeline.md](worker-pipeline.md), \"Accepting a result\") and equals the reference run by\n   content: each table compared with `compare_tables` on `TABLE_KEYS`, as `check()` does.\n5. The folders of attempts that were not accepted are left as they are and referenced nowhere;\n   `cleanup`, a dry run, lists them.\n\nOutcome checks for each batch:\n\n6. `status --check` exits 0 before the export (the store's seven `INVARIANT_QUERIES`), and the\n   export's `invariant_violations.json` is empty.\n7. No two launchers' step intervals overlap, across all attempts of the batch (as `check()`).\n8. Afterwards no process of any attempt is left, and no Spark scratch beyond what was there before\n   the batch (as `check()`).\n\n## 6. Draft SQL cross-check\n\n_Drafted with Claude Code; not run._\n\n**What it adds.** The store's seven `INVARIANT_QUERIES` list the jobs that break an invariant, and\n`status --check` exits 1 if any does. Between them they already imply at most one accepted attempt\nper job in the database. The schema alone does not: `jobs.accepted_attempt` names one attempt, but\nno constraint stops two `job_attempts` rows of one job from both being `accepted`. The queries below\nrestate that part as counts per job, and add what the store cannot see: which jobs the harness\nsubmitted (lost jobs) and what the workers reported (a worker that believed it accepted). The\noverlap with the invariant queries is deliberate: a second reading of the same rows, by queries the\nstore does not run.\n\n**Where it runs** (proposal, Q-C): in MySQL at the end of each batch, after the memory peaks and\n`status --check` are recorded and before the export. The harness's two inputs are TEMPORARY tables\nof the cross-check's own session, so the store's tables are untouched. MySQL documents that a\nTEMPORARY table cannot be referred to more than once in the same query, so each query below names\neach of them at most once. Written for MySQL 8.4, with CTEs, joins and CASE only.\n\n```sql\n-- Inputs from the harness, in the cross-check's session only.\n-- batch_jobs: each job the harness submitted in this batch, and the case applied to it.\nCREATE TEMPORARY TABLE batch_jobs (\n    job_id          BIGINT UNSIGNED NOT NULL,\n    case_id         VARCHAR(8) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,\n    PRIMARY KEY (job_id)\n);\n-- worker_accepts: one row per `accepted` event in the worker logs (its fields job_id, attempt\n-- and digest), which a worker writes only after accept_result returned true.\nCREATE TEMPORARY TABLE worker_accepts (\n    worker_id       VARCHAR(128) NOT NULL,\n    job_id          BIGINT UNSIGNED NOT NULL,\n    attempt_number  INT UNSIGNED NOT NULL,\n    result_digest   CHAR(64) CHARACTER SET ascii COLLATE ascii_bin NOT NULL\n);\n```\n\n```sql\n-- Q1. One row per job, from the job tables alone.\nWITH attempts AS (\n    SELECT\n        job_id,\n        COUNT(*) AS n_claims,\n        SUM(CASE WHEN outcome = 'accepted' THEN 1 ELSE 0 END) AS n_accepted,\n        SUM(CASE WHEN outcome = 'failed' THEN 1 ELSE 0 END) AS n_failed,\n        SUM(CASE WHEN outcome = 'expired' THEN 1 ELSE 0 END) AS n_expired,\n        SUM(CASE WHEN outcome = 'running' THEN 1 ELSE 0 END) AS n_running,\n        COUNT(DISTINCT worker_id) AS n_workers,\n        MIN(CASE WHEN outcome = 'accepted' THEN attempt_number END) AS accepted_number,\n        MIN(CASE WHEN outcome = 'accepted' THEN result_digest END) AS accepted_digest\n    FROM job_attempts\n    GROUP BY job_id\n)\nSELECT\n    j.job_id,\n    j.status,\n    j.attempt_number,\n    j.max_attempts,\n    j.accepted_attempt,\n    COALESCE(a.n_claims, 0) AS n_claims,\n    COALESCE(a.n_accepted, 0) AS n_accepted,\n    COALESCE(a.n_failed, 0) AS n_failed,\n    COALESCE(a.n_expired, 0) AS n_expired,\n    COALESCE(a.n_running, 0) AS n_running,\n    COALESCE(a.n_workers, 0) AS n_workers,\n    a.accepted_digest,\n    CASE\n        WHEN COALESCE(a.n_accepted, 0) > 1\n            THEN 'more than one accepted attempt'\n        WHEN j.status = 'succeeded' AND COALESCE(a.n_accepted, 0) = 0\n            THEN 'succeeded without an accepted attempt'\n        WHEN j.status = 'succeeded' AND a.accepted_number <> j.accepted_attempt\n            THEN 'accepted_attempt names another attempt'\n        WHEN j.status <> 'succeeded' AND COALESCE(a.n_accepted, 0) = 1\n            THEN 'accepted attempt of a job that did not succeed'\n        WHEN COALESCE(a.n_claims, 0) <> j.attempt_number\n            THEN 'attempt rows differ from attempt_number'\n        WHEN j.status IN ('queued', 'running')\n            THEN 'not finished'\n        WHEN COALESCE(a.n_running, 0) > 0\n            THEN 'finished with an attempt still running'\n        WHEN j.status = 'failed'\n            THEN 'failed'\n        ELSE 'ok'\n    END AS verdict\nFROM jobs AS j\nLEFT JOIN attempts AS a ON a.job_id = j.job_id\nORDER BY j.job_id;\n```\n\n```sql\n-- Q2. One row per job the harness submitted: lost jobs, and the workers' reports against the\n-- table. worker_accepts is read once; each report matches at most one attempt row.\nWITH reports AS (\n    SELECT\n        w.job_id,\n        COUNT(*) AS n_reports,\n        COUNT(DISTINCT w.attempt_number) AS n_reported_attempts,\n        SUM(CASE WHEN a.job_id IS NULL THEN 1 ELSE 0 END) AS n_unmatched\n    FROM worker_accepts AS w\n    LEFT JOIN job_attempts AS a\n        ON a.job_id = w.job_id\n        AND a.attempt_number = w.attempt_number\n        AND a.outcome = 'accepted'\n        AND a.result_digest = w.result_digest\n    GROUP BY w.job_id\n)\nSELECT\n    b.case_id,\n    b.job_id,\n    j.status,\n    COALESCE(r.n_reports, 0) AS n_reports,\n    COALESCE(r.n_unmatched, 0) AS n_unmatched,\n    CASE\n        WHEN j.job_id IS NULL\n            THEN 'lost: no row'\n        WHEN j.status IN ('queued', 'running')\n            THEN 'lost: not finished by the drain deadline'\n        WHEN COALESCE(r.n_reported_attempts, 0) > 1\n            THEN 'reported accepted by more than one attempt'\n        WHEN COALESCE(r.n_unmatched, 0) > 0\n            THEN 'reported acceptance not in the table'\n        WHEN COALESCE(r.n_reports, 0) > 1\n            THEN 'acceptance reported more than once'\n        WHEN j.status = 'succeeded' AND COALESCE(r.n_reports, 0) = 0\n            THEN 'succeeded, acceptance not reported'\n        WHEN j.status = 'failed'\n            THEN 'failed'\n        ELSE 'ok'\n    END AS verdict\nFROM batch_jobs AS b\nLEFT JOIN jobs AS j ON j.job_id = b.job_id\nLEFT JOIN reports AS r ON r.job_id = b.job_id\nORDER BY b.case_id, b.job_id;\n```\n\n```sql\n-- Q2b. Jobs in the table that the harness did not record, such as a submit that exited 75\n-- (outcome unknown) although its insert committed. Each needs an explanation.\nSELECT\n    j.job_id,\n    j.status\nFROM jobs AS j\nLEFT JOIN batch_jobs AS b ON b.job_id = j.job_id\nWHERE b.job_id IS NULL\nORDER BY j.job_id;\n```\n\n```sql\n-- Q3. Per case: jobs, outcomes, claims and accepted attempts, for the batch record.\nWITH attempts AS (\n    SELECT\n        job_id,\n        COUNT(*) AS n_claims,\n        SUM(CASE WHEN outcome = 'accepted' THEN 1 ELSE 0 END) AS n_accepted\n    FROM job_attempts\n    GROUP BY job_id\n)\nSELECT\n    b.case_id,\n    COUNT(*) AS n_jobs,\n    SUM(CASE WHEN j.status = 'succeeded' THEN 1 ELSE 0 END) AS n_succeeded,\n    SUM(CASE WHEN j.status = 'failed' THEN 1 ELSE 0 END) AS n_failed,\n    SUM(CASE WHEN j.job_id IS NULL OR j.status IN ('queued', 'running') THEN 1 ELSE 0 END) AS n_lost,\n    SUM(CASE WHEN COALESCE(a.n_accepted, 0) = 1 THEN 1 ELSE 0 END) AS n_one_accepted,\n    SUM(CASE WHEN COALESCE(a.n_accepted, 0) > 1 THEN 1 ELSE 0 END) AS n_more_accepted,\n    SUM(COALESCE(a.n_claims, 0)) AS n_claims,\n    MAX(COALESCE(a.n_claims, 0)) AS max_claims\nFROM batch_jobs AS b\nLEFT JOIN jobs AS j ON j.job_id = b.job_id\nLEFT JOIN attempts AS a ON a.job_id = b.job_id\nGROUP BY b.case_id\nORDER BY b.case_id;\n```\n\n**Expected verdicts** (proposal). Q1: `ok` for every job of the planned cases. Q2: `ok` for every\nsubmitted job. `succeeded, acceptance not reported` needs an explanation from the injection log: a\nlost COMMIT reply with no successful repeat before F, or a kill between the commit and the event.\nNone of the planned cases is meant to produce it. Q2b: no rows, unless a submit exited 75 after its\ninsert committed.\n\n## 7. Decisions pending M2's final report\n\nLeft open on purpose. Each item names what it controls and the M2 results it waits for; no values\nare proposed. \"Deadlines\" is read here as the experiment's time settings and waits; if the author\nmeant something else, this section changes.\n\n### 7.1 Repetitions\n\n- **To decide:** injections per case in a batch; the number of batches; C0 jobs per batch and where\n  they go; the order of the cases (in blocks or interleaved).\n- **Waits for:** each parameter set's time to finish through the worker, and its spread; any case of\n  M2's acceptance runs that failed only sometimes.\n- **Already fixed:** one job at a time on this machine (spec §11), so a batch lasts about the sum of\n  its jobs' times to finish and recoveries. MySQL's limited memory headroom (spec §11) ties the\n  batch length to 7.3.\n- **What a count can show:** no violation in n independent injections bounds the rate per injection\n  below about 3/n at 95% confidence (the rule of three). It is not a proof; the guarantee rests on\n  the guards and their tests.\n\n### 7.2 Deadlines\n\n[timing.py](../src/etf_risk/jobs/timing.py) calls its defaults \"the M2 drafts of spec §11\".\n\n- **The clock:** those defaults (lease 60 s, renewals every 10 s, fence margin 10 s, session timeout\n  15 s); a shorter clock with the same relations, like M2's acceptance runs (lease 24 s, renewals\n  every 4 s, session timeout 10 s); or another. `Timing.check()` refuses inconsistent sets, and\n  every E2 time scales with the choice (section 3).\n- **Step and attempt limits:** windows 120 s, spark_pipeline 600 s, verify 300 s and attempt 900 s.\n  They also set the lock wait (step limit + G + 30 s) and `max.poll.interval.ms` (attempt limit +\n  G + 60 s), which bounds the classic-protocol wait.\n- **The drain deadline:** how long after a batch's last injection an unfinished job counts as lost\n  (Q2).\n- **The harness's waits:** for the intended phase before an injection; for recovery before the next\n  one; how long a process stays stopped (W6, W7); how long a service stays down (K2, D1, D2).\n- **Waits for:** M2's measured step and attempt durations, the container restart times seen in its\n  runs, and any timing change in its final report.\n\n### 7.3 Memory thresholds\n\n- **Which budgets apply:** the MySQL (512 MiB) and Kafka (640 MiB) containers of spec §11. The\n  worker and its steps run natively, so the 2.5 GiB pipeline-container budget applies only if they\n  move into a container.\n- **When a batch stops or is flagged:** the share of its limit a container's `memory.peak` may reach\n  (spec §11 records MySQL at 511 of 512 MiB after about two hours of tests), and whether fresh\n  containers for each batch are required (spec §11: \"should\").\n- **Host state before each injection:** available memory and load, as in the earlier experiments'\n  machine-state rules, with Docker's VM holding 3.83 GiB of the 8 GiB.\n- **The worker's own memory:** it imports pandas and pyarrow.\n- **Waits for:** the peaks M2 reports for the worker, each step, MySQL and Kafka.\n\n## 8. Other open design questions\n\nClaude Code's recommendation comes first in each; the author decides.\n\n- **Q-A. Injecting at the narrow points (W1, W2, W4, W5, D2).** These windows last milliseconds:\n  from a delivery to its claim, from a claim to its offset commit, from the renewal before\n  acceptance to acceptance. A signal from outside cannot land in them reliably. Recommended: a hook\n  in the `worker` command that sends SIGKILL to its own process at one named point of\n  `WORKER_FAULT_POINTS` (or holds there, for D2), enabled only by an environment variable the\n  harness sets, and recorded in the worker's `started` event. `Worker(fault=...)` already calls\n  these points; the hook only connects them to the command. It would be new code, written with\n  Claude Code, and tested and mutation-checked like the rest. Alternatives: signals timed from the\n  event logs, with misses recorded (section 3); or leaving these cases to the offline fault-point\n  tests.\n- **Q-B. Who recovers after a kill.** Recommended: a standby worker in the group, as in M2's tests,\n  with the harness restarting the killed worker as the next standby. Recovery times then hold no\n  delay chosen by the harness, and they include the classic-protocol wait that\n  [worker-pipeline.md](worker-pipeline.md) describes (\"Kafka group timing\"). Alternative: no\n  standby, and the harness restarts the killed worker after a fixed delay (7.2).\n- **Q-C. Where the SQL runs.** Recommended: in MySQL at the end of each batch (section 6). It reads\n  the rows the store wrote, with no loader in between. The export stays, so the queries can run\n  again later, for example in SQLite loaded through\n  [schema/sqlite.sql](../src/etf_risk/jobs/schema/sqlite.sql), which would also apply the CHECK\n  constraints again. Alternative: on the export only, with Spark SQL as in `analysis/`.\n- **Q-D. Partition-assignment events.** Recommended: an event for each assignment and revocation in\n  [kafka.py](../src/etf_risk/jobs/kafka.py), so that W1's time splits into the session timeout and\n  the rebalance. Without it, W1 is measured only as a whole.\n\n## 9. Records, code and authorship\n\n- **Records** (proposal), under `data/outputs-recovery/<batch>/`, outside Git like the rest of\n  `data/`: the export; the event logs; the harness's injection log; `services peaks`, taken before\n  the cross-check; Q1–Q3 as CSV; the table of section 4, one row per injection; `cleanup`'s listing.\n- **Code M3 would need**, none of it written: the harness; the collector for section 4 (event logs,\n  tables, launcher records); the cross-check runner; and the hook of Q-A and the events of Q-D, if\n  chosen.\n- **Authorship.** Spec §11: the job code is written with Claude Code; the experiments are the\n  project author's, with tutoring. In the earlier experiments the author decided the configurations\n  and rules, approved the design and the predictions, ran the formal measurements and wrote the\n  answers; Claude Code drafted Part A and wrote the code. Which of the harness, the collector and the\n  SQL the author writes is the author's decision. If the queries of section 6 are kept, the file\n  that holds them should say they were drafted with Claude Code; the author can also write their own\n  and use these as a cross-check.\n\n## 10. Not claimed\n\n- Times hold for this machine, the clock of 7.2, and one broker and one database (spec §11's\n  limits).\n- No violation in n injections is evidence, not proof (7.1).\n- The bounds in section 3 follow from the settings; they are not predictions until 7.2 is decided\n  and the author approves them.\n- Cases left to the offline tests (Q-A) are not measured by E1 or E2.\n"
}
````

## 80. User — 2026-10-23T20:02:57.519Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs/recovery-experiments.md (file state is current in your context — no need to Read it back)
```

## 81. Assistant — 2026-10-23T20:03:14.466Z

### Tool call: Bash

```
{
  "command": "SP=/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad && R=~/leveraged-etf-risk-analytics && (for w in .claude/worktrees/worker-pipeline .claude/worktrees/extension-baseline; do echo \"=== $w\"; git --no-optional-locks -C \"$R/$w\" rev-parse HEAD; git --no-optional-locks -C \"$R/$w\" status --porcelain=v1 --untracked-files=all; done) > \"$SP/worktree-snapshot-after.txt\" && if diff -q \"$SP/worktree-snapshot-before.txt\" \"$SP/worktree-snapshot-after.txt\" >/dev/null; then echo \"(1) linked worktrees: HEAD and status identical to the snapshot\"; else echo \"(1) DIFFERENCE:\"; diff \"$SP/worktree-snapshot-before.txt\" \"$SP/worktree-snapshot-after.txt\"; fi; echo \"(2) this worktree:\"; git status --porcelain=v1 --untracked-files=all; wc -l docs/recovery-experiments.md; echo \"(3) links:\"; grep -o -E '\\]\\([^)#]+' docs/recovery-experiments.md | sed 's/^](//' | sort -u | while read -r p; do test -e \"docs/$p\" && echo \"  ok      $p\" || echo \"  MISSING $p\"; done; echo \"(4) SQL columns vs schema:\"; for c in job_id outcome worker_id attempt_number result_digest status max_attempts accepted_attempt; do grep -q -E \"^\\s+$c\\s\" src/etf_risk/jobs/schema/mysql.sql && echo \"  ok $c\" || echo \"  NOT FOUND $c\"; done",
  "description": "Verify worktrees unchanged, links resolve and SQL columns exist"
}
```

## 82. User — 2026-10-23T20:03:17.124Z

### Tool result

```
(1) linked worktrees: HEAD and status identical to the snapshot
(2) this worktree:
?? docs/recovery-experiments.md
     446 docs/recovery-experiments.md
(3) links:
  ok      ../docker/compose.yaml
  ok      ../src/etf_risk/jobs/events.py
  ok      ../src/etf_risk/jobs/kafka.py
  ok      ../src/etf_risk/jobs/schema/sqlite.sql
  ok      ../src/etf_risk/jobs/timing.py
  ok      job-queue.md
  ok      job-table.md
  MISSING worker-pipeline.md
(4) SQL columns vs schema:
  ok job_id
  ok outcome
  ok worker_id
  ok attempt_number
  ok result_digest
  ok status
  ok max_attempts
  ok accepted_attempt
```

## 83. Assistant — 2026-10-23T20:03:47.211Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md",
  "content": "[REDACTED:memory]"
}
```

## 84. User — 2026-10-23T20:03:48.485Z

### Tool result

```
[REDACTED:memory]
```

## 85. Assistant — 2026-10-23T20:03:49.406Z

### Tool call: Bash

```
{
  "command": "[REDACTED:memory]",
  "description": "Append one pointer line to the memory index without printing it"
}
```

## 86. User — 2026-10-23T20:03:49.969Z

### Tool result

```
[REDACTED:memory]
```

## 87. Assistant — 2026-10-23T20:04:21.674Z

Written for: you, reviewing it as the author, and later readers of `docs/`. It follows the layout and authorship convention of the other experiment docs.

The E1/E2 outline is drafted in its own worktree, not committed, and ready for your review: [docs/recovery-experiments.md](.claude/worktrees/recovery-outline/docs/recovery-experiments.md). It's 446 lines on a new local branch, `docs/recovery-outline`, which I started from the M2 branch tip (`d2d8615`) because the outline describes M2's code.

**What it covers**
- **13 failure cases** (section 3): one no-failure control (C0), seven worker crashes or freezes (W1–W7), two Kafka cases (K1, K2), two MySQL cases (D1, D2) and one duplicate-delivery case (X1). For each: how it would be injected, which question it serves, the recovery path the design predicts, the expected claims and accepted results, and whether M2's live tests already cover it.
- **Expected recovery times** written in terms of the timing settings (lease, renewal interval, reconciler interval and so on), not as numbers. They aren't predictions until the clock is decided.
- **Metrics** (section 4), each tied to an event name or record that already exists.
- **Correctness checks** (section 5), split into checks that decide whether a run counts, and checks whose result answers E1/E2. A failed outcome is reported as a finding, never used to discard a batch.
- **Draft SQL** (section 6), for MySQL 8.4: a per-job query (accepted results, claims, outcomes, verdict), a lost-job and worker-report query, a query for jobs the harness didn't record, and a per-case summary. It's labelled "Drafted with Claude Code; not run". Every column it uses exists in `schema/mysql.sql`.
- **The three decisions you named** (section 7): repetitions, deadlines and memory thresholds. Each says what it controls and which M2 results it waits for. No values are proposed.

**Things to look at first**
1. **Authorship.** Spec §11 says the experiments are yours, with tutoring. So the draft labels everything as my proposal and leaves the "Author:" line empty for you. If you want the SQL to be your own, as in Stage 3, you could write the per-job verdict yourself and use mine as the cross-check.
2. **Five cases can't be injected reliably yet** (W1, W2, W4, W5, D2). Their windows are milliseconds wide, and the worker's fault points can only be triggered from tests. Section 8 (Q-A) recommends a small hook in the `worker` command, which would be new code; the alternative is to leave these cases to the offline tests.
3. **Kafka partition assignments aren't logged.** So W1's recovery time can only be measured whole, not split into the 15 s session timeout and the rebalance (Q-D).
4. **M2's live tests already run 6 of the 13 cases once each:** C0, W3, W6, W7, K1, D1. A MySQL restart *is* among them; I assumed otherwise partway through and corrected it after checking.
5. **The SQL repeats the store's seven built-in invariant checks on purpose.** What it adds is per-job counts, lost jobs measured against the harness's list of submitted jobs, and whether what the workers *reported* accepting matches the table.
6. **I read "deadlines" as time limits:** the lease and renewal clock, step and attempt limits, how long to wait before counting a job as lost, and the harness's waits. If you meant something else, section 7.2 changes.
7. **The links to `worker-pipeline.md` don't resolve on this branch** until M2 commits that doc.

**What I did and didn't do**
- In the M2 worktree I only ran read commands. Its HEAD and `git status` were identical before and after. That comparison covers file paths and status codes, not file contents.
- I created 1 worktree, 1 local branch and 1 repo file. No commits, tests, Spark, Docker or installs.
- I didn't read the private plan or the memory files. The outline rests on spec §11 and M2's docs and code, so tell me if the approved plan says something different about M3.
- I saved a one-line memory note pointing to this draft.

Tell me what to change. I won't commit until you say so.

`★ Insight ─────────────────────────────────────`
- **Validity versus outcome:** in the earlier experiments, a batch that failed a check was set aside. Here, a failed outcome check (say, two accepted results) would be the answer to E1, so the outline keeps "did the run count?" separate from "what did it show?".
- **The clock sets every E2 number:** a worker killed mid-step should be noticed between about lease minus renewal interval and lease plus reconciler interval, 50–65 s at today's defaults. Choosing the clock in 7.2 fixes the E2 numbers before anything runs.
`─────────────────────────────────────────────────`
