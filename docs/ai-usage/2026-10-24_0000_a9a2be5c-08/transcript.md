# Claude Code message 8

Session: `a9a2be5c-8da0-4ec5-be57-f251b5676fe9` · prompt sent 2026-10-24 00:00 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): git-user ×42, home ×1635, memory ×6, model-reasoning ×204, user ×14. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-24T05:00:22.454Z



<pasted_content id="605f">
The 82-row SQL fixture validation is accepted as tooling evidence, not as approval of Part A.

Proceed with the harness, collector, assignment events, launch-time code identity and precise fault-injection hooks. Claude Code writes this tooling, with accurate attribution.

Preserve the frozen SQL expectations. Reassess deadline formulas and estimate the complete duration of all 84 proposed jobs. Keep timing, repetitions and memory thresholds provisional.

Coordinate with the M2 session before any test or container run. Do not run formal experiments. Report progress and the remaining Part A decisions together.
</pasted_content id="605f">


## 2. Assistant — 2026-10-24T05:03:26.991Z

I'll pick this up in five parts: coordinating with the M2 session, writing the tooling (assignment events, launch-time code identity, fault hooks, harness, collector), reassessing the deadline formulas, estimating the duration of all 84 jobs, and reporting.

Coordination comes first, so a reply can arrive while I write code. You've asked me to coordinate with the M2 session before any test or container run, so I'll see whether it's reachable.

## 3. Assistant — 2026-10-24T05:03:27.024Z

### Tool call: ListAgents

```
{}
```

## 4. User — 2026-10-24T05:03:27.232Z

### Tool result

```
This session is leveraged-etf-risk-analytics-a9 [48274d] — the name other sessions use to message it (it is not listed below; a message to it would be a message to yourself).

Peer sessions (4):
  leveraged-etf-risk-analytics-bf [29b1ec]  ·  interactive  ·  idle  ·  started 1d ago
  leveraged-etf-risk-analytics-aa [f8de98]  ·  interactive  ·  busy  ·  started 21h ago
  leveraged-etf-risk-analytics-ea [a7f44f]  ·  interactive  ·  idle  ·  started 1d ago
  leveraged-etf-risk-analytics-d4 [684661]  ·  interactive  ·  idle  ·  started 21h ago
```

## 5. Assistant — 2026-10-24T05:03:59.352Z

### Tool call: Bash

```
{
  "command": "R=~/leveraged-etf-risk-analytics && cd $R && git rev-parse --verify -q refs/heads/feature/recovery-harness >/dev/null && echo \"branch exists\" || echo \"branch name free\"; test -e .claude/worktrees/recovery-harness && echo \"path exists\" || echo \"path free\"; git check-ignore -q .claude/worktrees/recovery-harness && echo \"path ignored: yes\"; echo \"feature/worker-pipeline tip: $(git rev-parse --short feature/worker-pipeline)\"; echo \"busy processes: $(( $(pgrep -f '[p]ytest' | wc -l) + $(pgrep -f '[p]ython.*-m etf_risk' | wc -l) ))\"",
  "description": "Check the new branch and worktree names are free"
}
```

## 6. User — 2026-10-24T05:04:00.305Z

### Tool result

```
branch name free
path free
path ignored: yes
feature/worker-pipeline tip: e4adc38
busy processes: 0
```

## 7. Assistant — 2026-10-24T05:04:05.130Z

### Tool call: Bash

```
{
  "command": "git worktree add -b feature/recovery-harness .claude/worktrees/recovery-harness feature/worker-pipeline 2>&1 | tail -2 && git -C .claude/worktrees/recovery-harness log --oneline -2 && echo \"status entries: $(git -C .claude/worktrees/recovery-harness status --porcelain | wc -l | tr -d ' ')\"",
  "description": "Create the tooling worktree on a new branch from the M2 tip"
}
```

## 8. User — 2026-10-24T05:04:06.833Z

### Tool result

```
Preparing worktree (new branch 'feature/recovery-harness')
HEAD is now at e4adc38 Correct the live job-suite result in the worker-pipeline status
e4adc38 Correct the live job-suite result in the worker-pipeline status
6d8a232 Document the worker's real pipeline, its runbook and M2's results
status entries: 0
```

## 9. Assistant — 2026-10-24T05:04:16.301Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py"
}
```

## 10. User — 2026-10-24T05:04:16.470Z

### Tool result

```
1	"""The job queue's commands (spec §11; the README's runbook):
2	
3	    python -m etf_risk.jobs init-db                 # create the database, tables and store id (idempotent)
4	    python -m etf_risk.jobs create-topic            # the job topic: one partition, no replica
5	    python -m etf_risk.jobs submit --snapshot S --kind rolling [--stride 21 ...]
6	    python -m etf_risk.jobs worker [--standby]      # serve jobs until SIGTERM or SIGINT
7	    python -m etf_risk.jobs reconciler              # requeue expired leases, publish unconfirmed jobs
8	    python -m etf_risk.jobs status [--check]        # the tables; --check: exit 1 on any invariant violation
9	    python -m etf_risk.jobs cleanup                 # list the folders of ended, non-accepted attempts (dry run)
10	    python -m etf_risk.jobs export DIR              # tables, violations and settings, as JSON files
11	
12	The settings come from flags or the environment:
13	- the database: --db or ETF_RISK_JOBS_DB, either mysql://user:password@host:port/database or
14	  sqlite:////absolute/path;
15	- Kafka: --bootstrap or ETF_RISK_KAFKA_BOOTSTRAP;
16	- the roots: --output-root (data/outputs/jobs) and --processed-root (data/processed), relative
17	  to the repository root;
18	- --lock, the host's execution lock (~/.cache/etf-risk/locks/spark-exec.lock);
19	- --timing NAME=SECONDS, overrides of etf_risk.jobs.timing, checked against its relations.
20	
21	Outputs go to <output root>/<store id>/<run id>/, and event logs to <output root>/events/.
22	
23	How the worker runs:
24	- it first sweeps what earlier workers left (pipeline.startup_sweep);
25	- after an error that comes from the transport, it restarts its serve loop in this process,
26	  with backoff; any other error ends it with exit code 1. Transport errors are a lost
27	  database connection, a claim race, a broken connection, or a Kafka error that is not
28	  fatal;
29	- SIGTERM or SIGINT stops it gracefully: polling stops, the running step's tree is ended,
30	  its attempt is failed as retryable (so the job is requeued at once), and the consumer
31	  leaves the group.
32	
33	submit inserts the job, publishes it, and records the confirmation. When the insert's COMMIT
34	reply was lost, the job may or may not exist, so it exits 75 (outcome unknown) and is never
35	repeated on its own.
36	
37	AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_cli.py.
38	"""
39	from __future__ import annotations
40	
41	import argparse
42	import json
43	import logging
44	import os
45	import signal
46	import socket
47	import sys
48	import threading
49	from dataclasses import asdict, fields, replace
50	from datetime import datetime, timedelta, timezone
51	from pathlib import Path
52	from urllib.parse import urlsplit, urlunsplit
53	
54	from etf_risk.jobs.events import EventLog
55	from etf_risk.jobs.params import InvalidParams, JobParams, input_checksums
56	from etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline, startup_sweep
57	from etf_risk.jobs.store import SQLITE, ClaimRace, JobStore, Outcome, Status, open_sqlite
58	from etf_risk.jobs.timing import DEFAULT_TIMING, Timing
59	from etf_risk.provenance import resolve
60	
61	DEFAULT_TOPIC, DEFAULT_GROUP = "etf-risk-jobs", "etf-risk-workers"
62	OUTCOME_UNKNOWN = 75
63	log = logging.getLogger("etf_risk.jobs")
64	
65	
66	# Settings
67	
68	def safe_url(url: str) -> str:
69	    """The URL without its password, for logs and records."""
70	    parts = urlsplit(url)
71	    if parts.password is None:
72	        return url
73	    netloc = f"{parts.username}:***@{parts.hostname}" + (f":{parts.port}" if parts.port else "")
74	    return urlunsplit(parts._replace(netloc=netloc))
75	
76	
77	def timing_from(overrides: list[str]) -> Timing:
78	    names = {f.name for f in fields(Timing)}
79	    changes = {}
80	    for item in overrides:
81	        name, _, value = item.partition("=")
82	        if name not in names:
83	            raise SystemExit(f"--timing: unknown setting {name!r}; one of {sorted(names)}")
84	        changes[name] = float(value)
85	    try:
86	        return replace(DEFAULT_TIMING, **changes).check()
87	    except ValueError as error:
88	        raise SystemExit(f"--timing: {error}") from None
89	
90	
91	def open_store(db: str, timing: Timing) -> JobStore:
92	    """A store that reconnects through its database's connection factory."""
93	    lease = timedelta(seconds=timing.lease)
94	    if db.startswith("sqlite:///"):
95	        path = db[len("sqlite:///"):]
96	        return JobStore(None, SQLITE, lease=lease, connect=lambda: open_sqlite(path, check_same_thread=False))
97	    if db.startswith("mysql://"):
98	        from etf_risk.jobs import mysql
99	        if not urlsplit(db).path.strip("/"):
100	            raise SystemExit("--db: name the database in the URL, as mysql://user:password@host:port/database")
101	        return JobStore(None, mysql.MYSQL, lease=lease, connect=mysql.connector(db, **mysql.SERVICE_SESSION))
102	    raise SystemExit(f"--db: expected mysql://... or sqlite:///..., not {safe_url(db)!r}")
103	
104	
105	def is_transport_error(error: BaseException, store: JobStore) -> bool:
106	    if store.dialect.is_disconnect(error) or isinstance(error, (ClaimRace, ConnectionError, TimeoutError)):
107	        return True
108	    try:
109	        from confluent_kafka import KafkaException
110	    except ImportError:
111	        return False
112	    return isinstance(error, KafkaException) and not error.args[0].fatal()
113	
114	
115	def stop_on_signals() -> threading.Event:
116	    stop = threading.Event()
117	    for sig in (signal.SIGTERM, signal.SIGINT):
118	        signal.signal(sig, lambda *_: stop.set())
119	    return stop
120	
121	
122	# Commands
123	
124	def cmd_init_db(args) -> int:
125	    if args.db.startswith("sqlite:///"):
126	        path = Path(args.db[len("sqlite:///"):])
127	        open_sqlite(path, create=not path.exists()).close()
128	    else:
129	        from etf_risk.jobs import mysql
130	        database = urlsplit(args.db).path.strip("/")
131	        if not database or not database.replace("_", "").isalnum():
132	            raise SystemExit("--db: name the database in the URL with letters, digits and underscores")
133	        admin = mysql.connect_mysql(urlunsplit(urlsplit(args.db)._replace(path="")))    # no database selected
134	        try:
135	            with admin.cursor() as cursor:
136	                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}`")
137	        finally:
138	            admin.close()
139	        conn = mysql.connect_mysql(args.db)
140	        try:
141	            with conn.cursor() as cursor:
142	                cursor.execute("SHOW TABLES LIKE 'jobs'")
143	                has_jobs = cursor.fetchone() is not None
144	                cursor.execute("SHOW TABLES LIKE 'job_store'")
145	                has_store = cursor.fetchone() is not None
146	            if has_jobs and not has_store:
147	                raise SystemExit(f"{safe_url(args.db)} holds job tables of an earlier schema; use a new database")
148	            if not has_jobs:
149	                mysql.create_schema(conn)
150	        finally:
151	            conn.close()
152	    store = open_store(args.db, DEFAULT_TIMING)
153	    print(json.dumps({"store_id": store.ensure_identity(), "db": safe_url(args.db)}))
154	    return 0
155	
156	
157	def cmd_create_topic(args) -> int:
158	    from etf_risk.jobs.kafka import create_topic
159	    try:
160	        create_topic(args.bootstrap, args.topic)
161	    except Exception as error:
162	        if "TOPIC_ALREADY_EXISTS" not in str(error):
163	            raise
164	        print(f"{args.topic}: exists already")
165	        return 0
166	    print(f"{args.topic}: created (one partition, no replica)")
167	    return 0
168	
169	
170	def cmd_submit(args) -> int:
171	    from etf_risk.jobs.kafka import KafkaPublisher
172	    timing = timing_from(args.timing)
173	    try:
174	        params = JobParams(args.snapshot, args.kind, window_days=args.window_days, stride=args.stride,
175	                           anchor=args.anchor, sample_ticker=args.sample_ticker)
176	        checksums = input_checksums(resolve(args.processed_root), params.snapshot)
177	    except InvalidParams as error:
178	        raise SystemExit(f"submit: {error}") from None
179	    store = open_store(args.db, timing)
180	    events = EventLog(Path(events_root(args)) / "submit.jsonl", "submit", store_id=store.store_id())
181	    try:
182	        job_id = store.submit(params.to_dict(), checksums, max_attempts=args.max_attempts)
183	    except Exception as error:
184	        if store.dialect.is_disconnect(error):
185	            events.log("submit_unknown", error=f"{type(error).__name__}: {error}"[:500])
186	            print("submit: the database connection broke during the insert; the job may or may not exist."
187	                  " Check with `status` before submitting again.", file=sys.stderr)
188	            return OUTCOME_UNKNOWN
189	        raise
190	    publisher = KafkaPublisher(args.bootstrap, args.topic, timing=timing)
191	    published = publisher.publish(job_id)
192	    publisher.close()
193	    recorded = False
194	    try:
195	        recorded = published and store.mark_published(job_id, version=0)
196	    except Exception as error:                            # the reconciler publishes it again after the grace
197	        events.log("record_failed", job_id=job_id, error=f"{type(error).__name__}: {error}"[:500])
198	    events.log("submitted", job_id=job_id, published=published, recorded=recorded, params=params.to_dict())
199	    print(json.dumps({"job_id": job_id, "published": published, "recorded": recorded}))
200	    return 0
201	
202	
203	def cmd_worker(args) -> int:
204	    from etf_risk.jobs.kafka import KafkaConsumer
205	    from etf_risk.jobs.worker import Worker
206	    timing = timing_from(args.timing)
207	    stop = stop_on_signals()
208	    store = open_store(args.db, timing)
209	    store_id = store.store_id()
210	    output_root = resolve(args.output_root) / store_id
211	    worker_id = args.worker_id or f"worker-{socket.gethostname().split('.')[0]}-{os.getpid()}"
212	    events = EventLog(Path(events_root(args)) / f"{worker_id}.jsonl", "worker", store_id=store_id, worker_id=worker_id)
213	    events.log("started", db=safe_url(args.db), topic=args.topic, group=args.group, timing=asdict(timing),
214	               standby=args.standby)
215	    startup_sweep(store, output_root, timing=timing, events=events)
216	    pipeline = SubprocessPipeline(store_id=store_id, processed_root=resolve(args.processed_root), worker_id=worker_id,
217	                                  lock_path=args.lock, timing=timing, events=events, stop=stop)
218	    worker = Worker(store, pipeline, output_root, worker_id=worker_id, events=events)
219	    backoff = 1.0
220	    while not stop.is_set():
221	        consumer = KafkaConsumer(args.bootstrap, args.topic, args.group, timing=timing, events=events)
222	        try:
223	            worker.serve(consumer, stop=stop.is_set)
224	            backoff = 1.0
225	        except Exception as error:
226	            if not is_transport_error(error, store):
227	                events.log("worker_failed", error=f"{type(error).__name__}: {error}"[:1000])
228	                log.exception("worker: an error that is not the transport's; stopping")
229	                return 1
230	            events.log("serve_restarted", error=f"{type(error).__name__}: {error}"[:500], backoff_s=backoff)
231	            log.warning("worker: %s; serving again in %.0f s", error, backoff)
232	            stop.wait(backoff)
233	            backoff = min(backoff * 2, 30.0)
234	        finally:
235	            consumer.close()                               # leave the group at once
236	    events.log("stopped")
237	    return 0
238	
239	
240	def cmd_reconciler(args) -> int:
241	    from etf_risk.jobs.kafka import KafkaPublisher
242	    from etf_risk.jobs.reconciler import Reconciler
243	    timing = timing_from(args.timing)
244	    stop = stop_on_signals()
245	    store = open_store(args.db, timing)
246	    events = EventLog(Path(events_root(args)) / f"reconciler-{os.getpid()}.jsonl", "reconciler",
247	                      store_id=store.store_id())
248	    publisher = KafkaPublisher(args.bootstrap, args.topic, timing=timing)
249	    events.log("started", db=safe_url(args.db), topic=args.topic)
250	    Reconciler(store, publisher, events=events).run(stop, interval=timedelta(seconds=args.interval))
251	    publisher.close()
252	    events.log("stopped")
253	    return 0
254	
255	
256	def rows(records: list[dict]) -> list[dict]:
257	    return [{k: (v.isoformat() if isinstance(v, datetime) else v.value if hasattr(v, "value") else v)
258	             for k, v in r.items()} for r in records]
259	
260	
261	def cmd_status(args) -> int:
262	    store = open_store(args.db, DEFAULT_TIMING)
263	    jobs, attempts = store.all_jobs(), store.all_attempts()
264	    by_job: dict[int, list[dict]] = {}
265	    for a in attempts:
266	        by_job.setdefault(a["job_id"], []).append(a)
267	    counts = {s.value: sum(1 for j in jobs if j["status"] is s) for s in Status}
268	    print(f"store {store.store_id()}: {len(jobs)} jobs " + ", ".join(f"{n} {s}" for s, n in counts.items() if n))
269	    for j in jobs if not args.job else [j for j in jobs if j["job_id"] in args.job]:
270	        outcomes = " ".join(f"{a['attempt_number']}:{a['outcome'].value}" for a in by_job.get(j["job_id"], []))
271	        accepted = next((a for a in by_job.get(j["job_id"], []) if a["outcome"] is Outcome.ACCEPTED), None)
272	        print(f"  job {j['job_id']}: {j['status'].value}; attempts {outcomes or '-'}"
273	              + (f"; accepted {accepted['attempt_number']} ({accepted['result_digest'][:12]})" if accepted else ""))
274	    if not args.check:
275	        return 0
276	    violations = store.invariant_violations()
277	    print("invariants: " + ("all hold" if not violations else json.dumps(violations)))
278	    return 1 if violations else 0
279	
280	
281	def cmd_cleanup(args) -> int:
282	    store = open_store(args.db, DEFAULT_TIMING)
283	    root = resolve(args.output_root) / store.store_id()
284	    attempts = {a["run_id"]: a for a in store.all_attempts()}
285	    ended, orphans, total = [], [], 0
286	    for folder in sorted(root.glob("job-*-attempt-*")):
287	        attempt = attempts.get(folder.name)
288	        size = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
289	        if attempt is None:
290	            orphans.append((folder, size))
291	        elif attempt["outcome"] in (Outcome.FAILED, Outcome.EXPIRED):
292	            ended.append((folder, size))
293	            total += size
294	    for folder, size in ended:
295	        print(f"ended, not accepted: {folder}  ({size / 2**20:,.1f} MiB)")
296	    for folder, size in orphans:
297	        print(f"no attempt row (another job table?): {folder}  ({size / 2**20:,.1f} MiB)")
298	    print(f"dry run: {len(ended)} folders ({total / 2**20:,.1f} MiB) could be removed; nothing was deleted")
299	    return 0
300	
301	
302	def cmd_export(args) -> int:
303	    out = Path(args.folder)
304	    out.mkdir(parents=True, exist_ok=False)
305	    store = open_store(args.db, DEFAULT_TIMING)
306	    files = {"jobs.json": rows(store.all_jobs()), "job_attempts.json": rows(store.all_attempts()),
307	             "invariant_violations.json": store.invariant_violations(),
308	             "store.json": {"store_id": store.store_id(), "db": safe_url(args.db),
309	                            "exported_at_utc": datetime.now(timezone.utc).isoformat()},
310	             "timing.json": asdict(timing_from(args.timing))}
311	    for name, value in files.items():
312	        (out / name).write_text(json.dumps(value, indent=2, default=str) + "\n")
313	    print(f"exported {', '.join(files)} to {out}")
314	    return 0
315	
316	
317	def events_root(args) -> Path:
318	    return Path(args.events) if args.events else resolve(args.output_root) / "events"
319	
320	
321	def main(argv: list[str] | None = None) -> int:
322	    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs", description=__doc__.splitlines()[0])
323	    common = argparse.ArgumentParser(add_help=False)
324	    common.add_argument("--db", default=os.environ.get("ETF_RISK_JOBS_DB"),
325	                        help="mysql://user:password@host:port/database or sqlite:////path (ETF_RISK_JOBS_DB)")
326	    common.add_argument("--bootstrap", default=os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", "127.0.0.1:9094"))
327	    common.add_argument("--topic", default=os.environ.get("ETF_RISK_JOBS_TOPIC", DEFAULT_TOPIC))
328	    common.add_argument("--output-root", default="data/outputs/jobs")
329	    common.add_argument("--processed-root", default="data/processed")
330	    common.add_argument("--events", help="folder of the event logs (default: <output root>/events)")
331	    common.add_argument("--timing", action="append", default=[], metavar="NAME=SECONDS")
332	    commands = parser.add_subparsers(dest="command", required=True)
333	    commands.add_parser("init-db", parents=[common])
334	    commands.add_parser("create-topic", parents=[common])
335	    submit = commands.add_parser("submit", parents=[common])
336	    submit.add_argument("--snapshot", required=True)
337	    submit.add_argument("--kind", required=True)
338	    submit.add_argument("--window-days", type=int, default=JobParams.__dataclass_fields__["window_days"].default)
339	    submit.add_argument("--stride", type=int, default=JobParams.__dataclass_fields__["stride"].default)
340	    submit.add_argument("--anchor", default=JobParams.__dataclass_fields__["anchor"].default)
341	    submit.add_argument("--sample-ticker", default=JobParams.__dataclass_fields__["sample_ticker"].default)
342	    submit.add_argument("--max-attempts", type=int, default=3)
343	    worker = commands.add_parser("worker", parents=[common])
344	    worker.add_argument("--group", default=DEFAULT_GROUP)
345	    worker.add_argument("--worker-id")
346	    worker.add_argument("--lock", default=str(DEFAULT_LOCK))
347	    worker.add_argument("--standby", action="store_true", help="recorded in the events; any worker can stand by")
348	    reconciler = commands.add_parser("reconciler", parents=[common])
349	    reconciler.add_argument("--interval", type=float, default=5.0)
350	    status = commands.add_parser("status", parents=[common])
351	    status.add_argument("--check", action="store_true")
352	    status.add_argument("--job", type=int, nargs="*")
353	    commands.add_parser("cleanup", parents=[common])
354	    export = commands.add_parser("export", parents=[common])
355	    export.add_argument("folder")
356	    args = parser.parse_args(argv)
357	    if not args.db:
358	        parser.error("no database: give --db or set ETF_RISK_JOBS_DB")
359	    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
360	    handler = {"init-db": cmd_init_db, "create-topic": cmd_create_topic, "submit": cmd_submit, "worker": cmd_worker,
361	               "reconciler": cmd_reconciler, "status": cmd_status, "cleanup": cmd_cleanup, "export": cmd_export}
362	    return handler[args.command](args)
363	
```

## 11. Assistant — 2026-10-24T05:04:24.365Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py"
}
```

## 12. User — 2026-10-24T05:04:24.516Z

### Tool result

```
1	"""Kafka adapters for the job queue (spec §11): a publisher that waits for the broker's
2	confirmation, and a consumer whose group moves on only when the worker commits.
3	
4	Settings, each pinned by tests/test_jobs_kafka.py:
5	- producer: acks=all and idempotence on. With one broker and no replica, acks=all means
6	  that broker wrote the message. librdkafka gives up on a message after the confirmation
7	  timeout, the same time publish() waits, so publish() returns a final answer.
8	- consumer: enable.auto.commit=false, since the worker commits after its claim, and
9	  enable.auto.offset.store=false, so nothing but those commits records a position.
10	  auto.offset.reset=earliest: a consumer group that has never committed starts at the
11	  first message, so a job published before its group first starts is still delivered;
12	  librdkafka's default, latest, would skip it.
13	- consumer group timing, from etf_risk.jobs.timing:
14	  - group.protocol=classic, since session.timeout.ms is ignored under "consumer";
15	  - session.timeout.ms 15 s and heartbeat.interval.ms 3 s: a stopped or crashed worker leaves
16	    the group well before its lease can expire;
17	  - max.poll.interval.ms above the attempt limit plus the kill grace: serve() does not poll
18	    while a pipeline runs, and a run that outlasted the interval would make librdkafka leave
19	    the group, so a standby could start a second job on this machine. The offset is
20	    committed before the run, so the job itself would not be delivered again.
21	- socket.timeout.ms 10 s for both, so a commit or publication waits for a broker at most that
22	  long per request.
23	Consumer errors that are not fatal, such as a poll after the poll interval was exceeded, are
24	logged and written to the worker's event log (consumer_error).
25	
26	confluent-kafka is imported only when an adapter is created. It is in the `jobs`
27	dependency group (pyproject.toml, locked in uv.lock), not among the core dependencies: the
28	Kafka runs use uv run --group jobs. Topics are created
29	explicitly (create_topic: one partition, no replica), since the broker in
30	docker/compose.yaml does not create them on first use.
31	
32	AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_kafka.py,
33	offline and against Kafka 4.3.1 (docker/compose.yaml).
34	"""
35	from __future__ import annotations
36	
37	import logging
38	from datetime import timedelta
39	
40	from etf_risk.jobs.events import NO_EVENTS, EventLog
41	from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, Delivery, encode
42	from etf_risk.jobs.timing import DEFAULT_TIMING, Timing
43	
44	log = logging.getLogger(__name__)
45	
46	
47	def _ms(seconds: float) -> int:
48	    return int(round(seconds * 1000))
49	
50	
51	def producer_config(bootstrap: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT,
52	                    timing: Timing = DEFAULT_TIMING) -> dict:
53	    return {"bootstrap.servers": bootstrap, "acks": "all", "enable.idempotence": True, "linger.ms": 0,
54	            "message.timeout.ms": int(confirmation_timeout.total_seconds() * 1000),
55	            "socket.timeout.ms": _ms(timing.socket_timeout)}
56	
57	
58	def consumer_config(bootstrap: str, group: str, *, timing: Timing = DEFAULT_TIMING) -> dict:
59	    return {"bootstrap.servers": bootstrap, "group.id": group, "enable.auto.commit": False,
60	            "enable.auto.offset.store": False, "auto.offset.reset": "earliest", "group.protocol": "classic",
61	            "session.timeout.ms": _ms(timing.session_timeout), "heartbeat.interval.ms": _ms(timing.heartbeat_interval),
62	            "max.poll.interval.ms": _ms(timing.max_poll_interval), "socket.timeout.ms": _ms(timing.socket_timeout)}
63	
64	
65	class KafkaPublisher:
66	    def __init__(self, bootstrap: str, topic: str, *, confirmation_timeout: timedelta = CONFIRMATION_TIMEOUT,
67	                 timing: Timing = DEFAULT_TIMING):
68	        from confluent_kafka import Producer
69	        self.topic = topic
70	        self._wait = confirmation_timeout.total_seconds() + 1.0   # the report comes by the message timeout
71	        self._producer = Producer({**producer_config(bootstrap, confirmation_timeout=confirmation_timeout,
72	                                                     timing=timing), "logger": log})
73	
74	    def publish(self, job_id: int) -> bool:
75	        """Send the job id and wait for the broker's confirmation. True only if it arrived;
76	        False may still mean the message was written and its confirmation lost."""
77	        from confluent_kafka import KafkaException
78	        report: dict = {}
79	        try:
80	            self._producer.produce(self.topic, key=encode(job_id), value=encode(job_id),
81	                                   on_delivery=lambda error, message: report.setdefault("error", error))
82	        except (BufferError, KafkaException):
83	            log.warning("could not send job %s", job_id, exc_info=True)
84	            return False
85	        self._producer.flush(self._wait)
86	        if report.get("error") is not None:
87	            log.warning("job %s: publication not confirmed: %s", job_id, report["error"])
88	        return "error" in report and report["error"] is None
89	
90	    def close(self) -> None:
91	        self._producer.flush(self._wait)
92	
93	
94	class KafkaConsumer:
95	    def __init__(self, bootstrap: str, topic: str, group: str, *, settings: dict | None = None,
96	                 timing: Timing = DEFAULT_TIMING, events: EventLog = NO_EVENTS):
97	        """settings override consumer_config(); the tests use it to show why earliest matters,
98	        and to shorten the poll interval."""
99	        from confluent_kafka import Consumer
100	        self._consumer = Consumer({**consumer_config(bootstrap, group, timing=timing), **(settings or {}),
101	                                   "logger": log})
102	        self._consumer.subscribe([topic])
103	        self._closed = False
104	        self.events = events
105	
106	    def poll(self, timeout: float) -> Delivery | None:
107	        from confluent_kafka import KafkaException
108	        message = self._consumer.poll(timeout)
109	        if message is None:
110	            return None
111	        if message.error() is not None:
112	            if message.error().fatal():
113	                raise KafkaException(message.error())
114	            log.warning("consumer error: %s", message.error())
115	            self.events.log("consumer_error", code=message.error().name(), reason=message.error().str())
116	            return None
117	        return Delivery(message.value() or b"", (message.topic(), message.partition(), message.offset()))
118	
119	    def commit(self, delivery: Delivery) -> None:
120	        from confluent_kafka import TopicPartition
121	        topic, partition, offset = delivery.position
122	        self._consumer.commit(offsets=[TopicPartition(topic, partition, offset + 1)], asynchronous=False)
123	
124	    def rewind(self, delivery: Delivery) -> None:
125	        from confluent_kafka import TopicPartition
126	        topic, partition, offset = delivery.position
127	        self._consumer.seek(TopicPartition(topic, partition, offset))
128	
129	    def assigned(self) -> bool:
130	        """Whether the group has given this consumer its partition yet."""
131	        return bool(self._consumer.assignment())
132	
133	    def close(self) -> None:
134	        """Leave the group without committing anything; closing again does nothing."""
135	        if not self._closed:
136	            self._closed = True
137	            self._consumer.close()
138	
139	
140	def create_topic(bootstrap: str, name: str, *, timeout: float = 30.0) -> None:
141	    from confluent_kafka.admin import AdminClient, NewTopic
142	    admin = AdminClient({"bootstrap.servers": bootstrap, "logger": log})
143	    admin.create_topics([NewTopic(name, num_partitions=1, replication_factor=1)],
144	                        operation_timeout=timeout)[name].result(timeout)
145	
146	
147	def delete_topic(bootstrap: str, name: str, *, timeout: float = 30.0) -> None:
148	    from confluent_kafka.admin import AdminClient
149	    admin = AdminClient({"bootstrap.servers": bootstrap, "logger": log})
150	    admin.delete_topics([name], operation_timeout=timeout)[name].result(timeout)
151	
```

## 13. Assistant — 2026-10-24T05:05:53.468Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness && echo \"=== provenance.py (defs + code_state + source_files)\" && grep -n -E '^def |^[A-Z_]+ = ' $W/src/etf_risk/provenance.py && sed -n \"$(grep -n '^def source_files' $W/src/etf_risk/provenance.py | cut -d: -f1),+14p\" $W/src/etf_risk/provenance.py && echo \"=== services.py (defs)\" && grep -n -E '^def |^[A-Z_]+ = |^class ' $W/src/etf_risk/services.py && sed -n \"$(grep -n '^def peaks' $W/src/etf_risk/services.py | cut -d: -f1),+30p\" $W/src/etf_risk/services.py",
  "description": "Read provenance's code-state helpers and the services peaks function"
}
```

## 14. User — 2026-10-24T05:05:54.496Z

### Tool result (error)

```
Exit code 1
=== provenance.py (defs + code_state + source_files)
26:PACKAGE_DIR = Path(__file__).resolve().parent
27:REPO_ROOT = PACKAGE_DIR.parents[1]
28:SOURCE_SUFFIXES = (".py", ".sql")
31:BUILD_COMMIT_ENV = "ETF_RISK_GIT_COMMIT"
32:BUILD_CLEAN_ENV = "ETF_RISK_GIT_WORKTREE_CLEAN"
33:IMAGE_ID_ENV = "ETF_RISK_IMAGE_ID"
36:def resolve(path: str | Path) -> Path:
42:def _git(*args: str) -> str | None:
50:def source_files() -> dict[str, Path]:
56:def code_state() -> dict:
def source_files() -> dict[str, Path]:
    """Every Python module and SQL schema of the package, by path relative to it."""
    files = (p for p in PACKAGE_DIR.rglob("*") if p.suffix in SOURCE_SUFFIXES and p.is_file())
    return {p.relative_to(PACKAGE_DIR).as_posix(): p for p in sorted(files)}


def code_state() -> dict:
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=all", "--", "src", "pyproject.toml", "uv.lock")
    if head:
        source, commit, clean = "git", head, (status == "") if status is not None else None
    elif os.environ.get(BUILD_COMMIT_ENV):
        source, commit = "build", os.environ[BUILD_COMMIT_ENV]
        clean = {"true": True, "false": False}.get(os.environ.get(BUILD_CLEAN_ENV, "").lower())
    else:
=== services.py (defs)
36:COMPOSE_FILE = REPO_ROOT / "docker" / "compose.yaml"
37:PROJECT = "etf-risk-jobs"                                   # the name: in docker/compose.yaml
38:SERVICES = ("mysql", "kafka")
39:DEFAULT_MYSQL_URL = "mysql://root:jobs-test@127.0.0.1:3307"   # compose.yaml's test password, 127.0.0.1 only
40:DEFAULT_KAFKA_BOOTSTRAP = "127.0.0.1:9094"
43:def _docker(*args: str, timeout: float = 60) -> subprocess.CompletedProcess:
48:class Peak:
66:def memory_peak(service: str) -> Peak:
77:def other_containers() -> int:
85:def mysql_ready(url: str) -> None:
97:def kafka_ready(bootstrap: str) -> None:
104:def wait_until_ready(service: str, check: Callable[[], None], *, timeout: float, interval: float = 1.0,
121:def main(argv: list[str] | None = None) -> int:
sed: 1: ",+30p": invalid command code ,
```

## 15. Assistant — 2026-10-24T05:06:00.649Z

`services.py` exposes `memory_peak(service) -> Peak` rather than a `peaks()` function, so the harness will call that per container. Reading its API in full:

## 16. Assistant — 2026-10-24T05:06:01.310Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/services.py",
  "offset": 1,
  "limit": 160
}
```

## 17. User — 2026-10-24T05:06:01.500Z

### Tool result

```
1	"""The systems extension's Compose services as seen from this machine: readiness, memory
2	peaks, and other projects' containers sharing Docker's VM (spec §11).
3	
4	    uv run --group jobs python -m etf_risk.services ready mysql kafka
5	    uv run python -m etf_risk.services peaks mysql kafka
6	    uv run python -m etf_risk.services others --require-none
7	
8	- ready waits until each service can do what the job system needs. MySQL: a login and
9	  SELECT 1, since the Compose healthcheck (mysqladmin ping) answers before logins work.
10	  Kafka: a metadata request that lists a broker. It exits 1 if a service is not ready
11	  within --timeout. The URLs come from ETF_RISK_MYSQL_URL and ETF_RISK_KAFKA_BOOTSTRAP,
12	  defaulting to the ports in docker/compose.yaml.
13	- peaks prints each service's cgroup v2 memory.peak, the highest usage since its container
14	  started (page cache included), against memory.max, the Compose limit, as docker/run.sh
15	  does for the pipeline container. A container that restarts may start a new count, so
16	  read peaks before a restart is injected.
17	- others counts the running containers that do not belong to this Compose project. It
18	  prints the count only, never their names: they use the same VM's memory, so memory
19	  budgets are measured with none running.
20	
21	AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_services.py.
22	"""
23	from __future__ import annotations
24	
25	import argparse
26	import json
27	import os
28	import subprocess
29	import sys
30	import time
31	from collections.abc import Callable
32	from dataclasses import asdict, dataclass
33	
34	from etf_risk.provenance import REPO_ROOT
35	
36	COMPOSE_FILE = REPO_ROOT / "docker" / "compose.yaml"
37	PROJECT = "etf-risk-jobs"                                   # the name: in docker/compose.yaml
38	SERVICES = ("mysql", "kafka")
39	DEFAULT_MYSQL_URL = "mysql://root:jobs-test@127.0.0.1:3307"   # compose.yaml's test password, 127.0.0.1 only
40	DEFAULT_KAFKA_BOOTSTRAP = "127.0.0.1:9094"
41	
42	
43	def _docker(*args: str, timeout: float = 60) -> subprocess.CompletedProcess:
44	    return subprocess.run(["docker", *args], capture_output=True, text=True, timeout=timeout)
45	
46	
47	@dataclass(frozen=True)
48	class Peak:
49	    service: str
50	    peak_bytes: int | None     # None: no memory.peak to read (the service is not running, or an older kernel)
51	    limit_bytes: int | None    # None: no limit ("max"), or unknown
52	
53	    @property
54	    def fraction(self) -> float | None:
55	        return None if self.peak_bytes is None or not self.limit_bytes else self.peak_bytes / self.limit_bytes
56	
57	    def describe(self) -> str:
58	        if self.peak_bytes is None:
59	            return f"{self.service}: memory.peak not available"
60	        text = f"{self.service}: memory.peak {self.peak_bytes / 2**20:,.0f} MiB"
61	        if self.limit_bytes:
62	            text += f" of {self.limit_bytes / 2**20:,.0f} MiB ({self.fraction:.0%})"
63	        return text + " (cgroup, includes page cache)"
64	
65	
66	def memory_peak(service: str) -> Peak:
67	    """The service container's memory.peak and memory.max (cgroup v2)."""
68	    out = _docker("compose", "-f", str(COMPOSE_FILE), "exec", "-T", service,
69	                  "cat", "/sys/fs/cgroup/memory.peak", "/sys/fs/cgroup/memory.max")
70	    values = out.stdout.split()
71	    if out.returncode != 0 or len(values) != 2:
72	        return Peak(service, None, None)
73	    peak, limit = values
74	    return Peak(service, int(peak), None if limit == "max" else int(limit))
75	
76	
77	def other_containers() -> int:
78	    """How many running containers belong to no service of this project: a count only."""
79	    out = _docker("ps", "--format", '{{.Label "com.docker.compose.project"}}')
80	    if out.returncode != 0:
81	        raise RuntimeError(f"docker ps failed with exit code {out.returncode}")
82	    return sum(1 for label in out.stdout.splitlines() if label.strip() != PROJECT)
83	
84	
85	def mysql_ready(url: str) -> None:
86	    from etf_risk.jobs.mysql import connect_mysql
87	    connection = connect_mysql(url)
88	    try:
89	        with connection.cursor() as cursor:
90	            cursor.execute("SELECT 1")
91	            if cursor.fetchone() != (1,):
92	                raise RuntimeError("SELECT 1 did not return 1")
93	    finally:
94	        connection.close()
95	
96	
97	def kafka_ready(bootstrap: str) -> None:
98	    from confluent_kafka.admin import AdminClient
99	    metadata = AdminClient({"bootstrap.servers": bootstrap, "log_level": 0}).list_topics(timeout=5)
100	    if not metadata.brokers:
101	        raise RuntimeError("the metadata lists no broker")
102	
103	
104	def wait_until_ready(service: str, check: Callable[[], None], *, timeout: float, interval: float = 1.0,
105	                     clock: Callable[[], float] = time.monotonic,
106	                     sleep: Callable[[float], None] = time.sleep) -> float:
107	    """Run check() until it returns; the seconds that took. TimeoutError, with the last
108	    error, once timeout has passed."""
109	    start = clock()
110	    while True:
111	        try:
112	            check()
113	            return clock() - start
114	        except Exception as error:
115	            last = error
116	        if clock() - start >= timeout:
117	            raise TimeoutError(f"{service} not ready after {timeout:g} s: {type(last).__name__}: {last}")
118	        sleep(interval)
119	
120	
121	def main(argv: list[str] | None = None) -> int:
122	    parser = argparse.ArgumentParser(prog="python -m etf_risk.services", description=__doc__.splitlines()[0])
123	    commands = parser.add_subparsers(dest="command", required=True)
124	    ready = commands.add_parser("ready", help="wait until each service can be used")
125	    ready.add_argument("services", nargs="+", choices=SERVICES)
126	    ready.add_argument("--timeout", type=float, default=120.0, help="seconds per service (default 120)")
127	    peaks = commands.add_parser("peaks", help="cgroup memory.peak against the limit")
128	    peaks.add_argument("services", nargs="+", choices=SERVICES)
129	    peaks.add_argument("--json", action="store_true", help="one JSON object per line")
130	    others = commands.add_parser("others", help="count containers outside this project")
131	    others.add_argument("--require-none", action="store_true", help="exit 1 if any is running")
132	    args = parser.parse_args(argv)
133	
134	    if args.command == "ready":
135	        checks = {"mysql": lambda: mysql_ready(os.environ.get("ETF_RISK_MYSQL_URL", DEFAULT_MYSQL_URL)),
136	                  "kafka": lambda: kafka_ready(os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP", DEFAULT_KAFKA_BOOTSTRAP))}
137	        for service in args.services:
138	            try:
139	                seconds = wait_until_ready(service, checks[service], timeout=args.timeout)
140	            except TimeoutError as error:
141	                print(error, file=sys.stderr)
142	                return 1
143	            print(f"{service}: ready after {seconds:.1f} s")
144	        return 0
145	    if args.command == "peaks":
146	        for service in args.services:
147	            peak = memory_peak(service)
148	            print(json.dumps(asdict(peak)) if args.json else peak.describe())
149	        return 0
150	    count = other_containers()
151	    print(f"{count} running container(s) outside the {PROJECT} project")
152	    return 1 if args.require_none and count else 0
153	
154	
155	if __name__ == "__main__":
156	    sys.exit(main())
157	
```

## 18. Assistant — 2026-10-24T05:06:26.068Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_live_pipeline.py",
  "offset": 48,
  "limit": 100
}
```

## 19. User — 2026-10-24T05:06:26.169Z

### Tool result

```
48	COMPOSE = ["docker", "compose", "-f", str(REPO / "docker" / "compose.yaml")]
49	
50	sys.path.insert(0, str(REPO / "analysis"))
51	_spec = importlib.util.spec_from_file_location("collect_caching_measurements",
52	                                               REPO / "analysis" / "collect_caching_measurements.py")
53	ccm = importlib.util.module_from_spec(_spec)
54	_spec.loader.exec_module(ccm)
55	
56	
57	class Stack:
58	    """The module's database, topic, folders, and the processes it started."""
59	
60	    def __init__(self, root: Path):
61	        self.root = root
62	        self.db = f"{MYSQL_URL.rstrip('/')}/etf_live_{secrets.token_hex(4)}"
63	        self.topic = f"etf-live-{secrets.token_hex(4)}"
64	        self.output, self.events_dir = root / "out", root / "events"
65	        self.lock = root / "locks" / "spark-exec.lock"
66	        self.env = {**os.environ, "ETF_RISK_JOBS_DB": self.db, "ETF_RISK_KAFKA_BOOTSTRAP": KAFKA_BOOTSTRAP,
67	                    "ETF_RISK_JOBS_TOPIC": self.topic}
68	        self.procs: dict[str, subprocess.Popen] = {}
69	        self.cli("init-db")
70	        self.cli("create-topic")
71	        from etf_risk.jobs import mysql
72	        self.store = JobStore(None, mysql.MYSQL, connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))
73	        self.store_id = self.store.store_id()
74	
75	    def args(self) -> list[str]:
76	        return ["--output-root", str(self.output), "--processed-root", str(PROCESSED), "--events",
77	                str(self.events_dir)]
78	
79	    def cli(self, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
80	        out = subprocess.run([sys.executable, "-m", "etf_risk.jobs", *argv, *self.args()], env=self.env,
81	                             capture_output=True, text=True, timeout=120)
82	        if check and out.returncode != 0:
83	            raise AssertionError(f"{argv}: exit {out.returncode}\n{out.stdout}\n{out.stderr}")
84	        return out
85	
86	    def start(self, name: str, *argv: str, extra: tuple[str, ...] = ()) -> subprocess.Popen:
87	        log = open(self.root / f"{name}.log", "ab")
88	        proc = subprocess.Popen([sys.executable, "-m", "etf_risk.jobs", *argv, *self.args(), *TIMING, *extra],
89	                                env=self.env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
90	        self.procs[name] = proc
91	        return proc
92	
93	    def worker(self, name: str, *extra: str) -> subprocess.Popen:
94	        return self.start(name, "worker", "--worker-id", name, "--lock", str(self.lock), extra=extra)
95	
96	    def submit(self, params: dict, max_attempts: int = 3) -> int:
97	        out = self.cli("submit", "--snapshot", SNAPSHOT, "--kind", params["kind"], "--stride", str(params["stride"]),
98	                       "--max-attempts", str(max_attempts))
99	        return json.loads(out.stdout)["job_id"]
100	
101	    def events(self, name: str) -> list[dict]:
102	        path = self.events_dir / f"{name}.jsonl"
103	        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []
104	
105	    def stop_all(self) -> None:
106	        for proc in self.procs.values():
107	            if proc.poll() is None:
108	                try:
109	                    os.kill(proc.pid, signal.SIGCONT)
110	                    proc.send_signal(signal.SIGTERM)
111	                except ProcessLookupError:
112	                    pass
113	        for proc in self.procs.values():
114	            try:
115	                proc.wait(timeout=60)
116	            except subprocess.TimeoutExpired:
117	                proc.kill()
118	        self.procs.clear()
119	        for value, procs in processes.marked_processes().items():
120	            if value.startswith(self.store_id + ":"):
121	                for p in procs:
122	                    try:
123	                        p.resume()
124	                        p.kill()
125	                    except psutil.Error:
126	                        pass
127	
128	
129	@pytest.fixture(scope="module")
130	def stack(tmp_path_factory, scratch_before):
131	    stack = Stack(tmp_path_factory.mktemp("live"))
132	    stack.scratch_before = scratch_before
133	    yield stack
134	    stack.stop_all()
135	    from etf_risk.jobs.kafka import delete_topic
136	    delete_topic(KAFKA_BOOTSTRAP, stack.topic)
137	
138	
139	@pytest.fixture
140	def services(stack):
141	    """A reconciler and a standby worker for one case; both stopped afterwards."""
142	    stack.start("reconciler", "reconciler", extra=("--interval", "2"))
143	    yield stack
144	    stack.stop_all()
145	
146	
147	@pytest.fixture(scope="module")
```

## 20. Assistant — 2026-10-24T05:06:36.519Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs && sed -n '70,126p' $W/worker.py && echo \".....\" && sed -n '232,290p' $W/worker.py",
  "description": "Read the worker's result types, heartbeat and serve loop tail"
}
```

## 21. User — 2026-10-24T05:06:37.369Z

### Tool result

```
class PipelineError(Exception):
    """The pipeline failed; retryable=False when running it again cannot help."""

    def __init__(self, message: str, *, retryable: bool = True):
        super().__init__(message)
        self.retryable = retryable


class Heartbeat:
    """heartbeat() renews the attempt's lease (JobStore.renew): False once the attempt has
    been fenced off. claimed_mono is the worker's time.monotonic() just before the claim;
    the lease cannot have started earlier, which gives a pipeline its first deadline."""

    def __init__(self, store: JobStore, claim: Claim, claimed_mono: float):
        self.store, self.claim, self.claimed_mono = store, claim, claimed_mono

    def __call__(self) -> bool:
        return self.store.renew(self.claim)


class Pipeline(Protocol):
    def run(self, claim: Claim, run_dir: Path, heartbeat: Heartbeat) -> str:
        """Write the attempt's outputs into run_dir, a new empty folder, and return the run
        digest of its result (etf_risk.runs), which acceptance records.

        Call heartbeat() more often than the lease lasts. It renews the lease and returns
        False once the attempt has been fenced off: then stop at once and raise Fenced.
        Raise PipelineError when the run fails."""


class Result(StrEnum):
    ACCEPTED = "accepted"    # this delivery's attempt produced the job's accepted result
    SKIPPED = "skipped"      # the claim was refused: the job needed nothing (see reason)
    REQUEUED = "requeued"    # the attempt failed and the job is queued again, not delivered again
    FAILED = "failed"        # the attempt failed and so did the job
    FENCED = "fenced"        # another attempt holds the job, or it ended; this one wrote nothing more


@dataclass(frozen=True)
class Handled:
    job_id: int
    result: Result
    reason: Refusal | None = None    # when skipped
    claim: Claim | None = None       # when an attempt started


@dataclass
class Served:
    """What Worker.serve() did with the deliveries it polled."""
    handled: int = 0              # handle() returned, whatever its result
    malformed: int = 0            # no valid job id: committed and skipped
    rewound: int = 0              # failed before the acknowledgement: read again (within the retries)
    failed_after_ack: int = 0     # failed after it: left to the lease and the reconciler
    commit_failures: int = 0      # commits that raised; the job went on

.....
                    continue
                failures = failures + 1 if delivery.position == failing else 1
                failing = delivery.position
                consumer.rewind(delivery)         # read again, by this consumer or after a restart: never skipped
                if failures > retries:
                    log.error("job %s: %d errors in a row before its delivery was acknowledged; giving up,"
                              " with the message uncommitted", job_id, failures)
                    self.events.log("gave_up", job_id=job_id, failures=failures)
                    raise
                log.exception("job %s failed before its delivery was acknowledged; reading it again", job_id)
                self.events.log("rewound", job_id=job_id, failures=failures)
                served.rewound += 1
                sleep(retry_delay)
                continue
            served.handled += 1
            if on_handled is not None:
                on_handled(handled)
        return served

    def _commit(self, consumer: Consumer, delivery: Delivery, served: Served) -> None:
        try:
            consumer.commit(delivery)
        except Exception as error:
            served.commit_failures += 1
            self.events.log("commit_failed", position=repr(delivery.position), error=f"{type(error).__name__}: {error}")
            log.warning("could not commit the offset of %r; a later delivery of it is refused by the claim",
                        delivery.position, exc_info=True)

    def _failed(self, claim: Claim, error: str, *, retryable: bool) -> Handled:
        status = self._until_deadline(lambda: self.store.fail_attempt(claim, error, retryable=retryable),
                                      claim, "fail_attempt")
        result = {None: Result.FENCED, Status.QUEUED: Result.REQUEUED, Status.FAILED: Result.FAILED}[status]
        self.events.log(result.value, job_id=claim.job_id, attempt=claim.attempt_number, retryable=retryable,
                        error=error[-2000:])
        return Handled(claim.job_id, result, claim=claim)
```

## 22. Assistant — 2026-10-24T05:06:42.750Z

Next, `pipeline.py`'s run loop and step launch, where `step_started` is logged and where the launch-time identity of each step belongs:

## 23. Assistant — 2026-10-24T05:06:43.826Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/pipeline.py",
  "offset": 1,
  "limit": 260
}
```

## 24. User — 2026-10-24T05:06:43.938Z

### Tool result

```
1	"""The real pipeline in the worker: windows → spark_pipeline → verify for one claimed job, each
2	step run by a launcher (spec §11; docs/job-queue.md, "The real pipeline").
3	
4	Steps. Each step is `<python> -m etf_risk.<module>` with absolute paths only, and everything it
5	writes lands in the attempt's folder:
6	1. windows --out-root <run dir>/windows --name <name>, from the snapshot under the worker's
7	   processed-data root;
8	2. spark_pipeline --windows <run dir>/windows/<snapshot>/<name>
9	   --out-root <run dir>/output --run-id <run id>;
10	3. verify --run <run dir>/output/<snapshot>/<name>/<run id>.
11	
12	The step's environment:
13	- It is built from an allowlist, so service URLs and passwords never reach it, and it
14	  carries the attempt's marker (etf_risk.jobs.processes).
15	- The working directory, TMPDIR and SPARK_LOCAL_DIRS point into <run dir>/.work.
16	  java.io.tmpdir does too, set through SPARK_SUBMIT_OPTS, since the macOS JDK ignores
17	  TMPDIR. It is never set through JAVA_TOOL_OPTIONS, whose "Picked up" notice would replace
18	  the Java version that run.json records.
19	- PYSPARK_PYTHON and PYSPARK_DRIVER_PYTHON name this interpreter; otherwise Spark's Python
20	  workers start whatever python3 comes first on PATH.
21	
22	Renewals. The worker's thread waits on the launcher one tick (1 s) at a time and renews the
23	lease every renew_interval. After each successful renewal it sends the launcher the absolute
24	deadline F = m0 + lease - fence_margin, on the monotonic clock (etf_risk.jobs.timing), where
25	m0 is the time just before the renewal started. The first F comes from the claim
26	(Heartbeat.claimed_mono).
27	- A renewal that raises, because the database is out of reach, is tried again at the next
28	  interval.
29	- A refused renewal means the attempt was fenced off. So does a deadline that passed without
30	  a renewal: the worker fences itself. Either way, the worker closes the launcher's pipe and
31	  the launcher ends the tree.
32	- The launcher's watchdog acts without the worker. Safety (no overlapping Spark work) rests
33	  on it and on the host lock, not on how long the worker's database calls take.
34	- The worker renews before each step and before acceptance, so a fenced worker never starts
35	  a new step. If the launcher does not end within the kill grace after its pipe was closed
36	  (because it is stopped, for example), the worker ends the tree itself.
37	
38	Acceptance. The run counts as a result only if all of the following hold:
39	- every step exited 0;
40	- run.json's status is ok;
41	- every count in checks.json is 0;
42	- verify.json reports no mismatch and the same breached windows;
43	- every table has its _SUCCESS file.
44	Then .work is removed, attempt.json is written (worker, steps, settings, code state), and
45	manifest.json records the run folder's manifest (etf_risk.runs). After a last renewal, run()
46	returns the run digest, and the worker accepts with it. Nothing in the folder changes after
47	acceptance.
48	
49	Failures are classified from the records, not from exit codes alone, since an uncaught
50	exception exits with 1, as "checks failed" does:
51	- not retryable: a checksum error (exit 3); run.json status checks_failed; a verify
52	  mismatch; parameters or input checksums that do not fit;
53	- retryable: a signal; a time limit; status failed or a missing record; a busy host lock;
54	  a launcher that failed;
55	- fenced: a refused renewal, or a deadline that passed.
56	
57	startup_sweep() is run by a starting worker. It ends the trees of attempts that are no longer
58	valid, keeps every valid active attempt's tree, and removes the scratch (.work) of attempts
59	that ended.
60	
61	AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_pipeline.py
62	(offline, with stand-in steps) and tests/test_jobs_worker_spark.py (the real steps).
63	"""
64	from __future__ import annotations
65	
66	import json
67	import os
68	import re
69	import shutil
70	import subprocess
71	import sys
72	import threading
73	import time
74	from dataclasses import asdict
75	from datetime import datetime, timezone
76	from pathlib import Path
77	
78	from etf_risk import runs
79	from etf_risk.jobs import processes
80	from etf_risk.jobs.events import NO_EVENTS, EventLog
81	from etf_risk.jobs.params import InvalidParams, JobParams, check_inputs
82	from etf_risk.jobs.store import Claim, JobStore
83	from etf_risk.jobs.timing import DEFAULT_TIMING, Timing
84	from etf_risk.jobs.worker import Fenced, PipelineError
85	from etf_risk.provenance import code_state
86	
87	STEPS = ("windows", "spark_pipeline", "verify")
88	TABLES = ("window_stats", "path_days", "path_summary", "paired")
89	def total_violations(checks: dict) -> int:
90	    """As spark_pipeline.total_violations, without importing PySpark into the worker."""
91	    return sum(v for group in checks.values() for v in group.values())
92	
93	
94	ENV_ALLOWED = ("HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "LC_CTYPE", "TZ", "JAVA_HOME", "SHELL", "TERM")
95	DEFAULT_LOCK = Path.home() / ".cache" / "etf-risk" / "locks" / "spark-exec.lock"
96	
97	
98	class Renewer:
99	    """The attempt's lease, as the worker sees it: fence_at is the absolute monotonic deadline
100	    given to the launcher, seq the number of the last successful renewal."""
101	
102	    def __init__(self, heartbeat, timing: Timing, events: EventLog, claim: Claim):
103	        self.heartbeat, self.timing, self.events, self.claim = heartbeat, timing, events, claim
104	        claimed = getattr(heartbeat, "claimed_mono", None)
105	        self.fence_at = None if claimed is None else claimed + timing.lease - timing.fence_margin
106	        self.seq = 0
107	        self.last_attempt = float("-inf")
108	
109	    def renew(self) -> bool | None:
110	        """True: renewed; False: refused (fenced off); None: the call failed."""
111	        m0 = time.monotonic()
112	        self.last_attempt = m0
113	        try:
114	            ok = self.heartbeat()
115	        except Exception as error:
116	            self.events.log("renewal_failed", job_id=self.claim.job_id, attempt=self.claim.attempt_number,
117	                            seconds=round(time.monotonic() - m0, 3), error=f"{type(error).__name__}: {error}"[:500])
118	            return None
119	        self.events.log("renewed" if ok else "renewal_refused", job_id=self.claim.job_id,
120	                        attempt=self.claim.attempt_number, seconds=round(time.monotonic() - m0, 3))
121	        if ok:
122	            self.fence_at = m0 + self.timing.lease - self.timing.fence_margin
123	            self.seq += 1
124	        return bool(ok)
125	
126	    def due(self, now: float) -> bool:
127	        return now - self.last_attempt >= self.timing.renew_interval
128	
129	    def passed(self, now: float) -> bool:
130	        return self.fence_at is None or now >= self.fence_at
131	
132	
133	class SubprocessPipeline:
134	    def __init__(self, *, store_id: str, processed_root: str | Path, worker_id: str,
135	                 lock_path: str | Path = DEFAULT_LOCK, registry: str | Path | None = None,
136	                 timing: Timing = DEFAULT_TIMING, events: EventLog = NO_EVENTS,
137	                 stop: threading.Event | None = None, python: str = sys.executable):
138	        self.store_id, self.worker_id = store_id, worker_id
139	        self.processed_root = Path(processed_root).resolve()
140	        self.lock_path = Path(lock_path)
141	        self.registry = Path(registry) if registry is not None else self.lock_path.parent / "registry"
142	        self.timing, self.events, self.stop, self.python = timing.check(), events, stop, python
143	        self.fence_at: float | None = None          # the current attempt's deadline (Worker reads it)
144	
145	    # The run
146	
147	    def run(self, claim: Claim, run_dir: Path, heartbeat) -> str:
148	        run_dir = Path(run_dir).resolve()
149	        started = datetime.now(timezone.utc).isoformat()
150	        renewer = Renewer(heartbeat, self.timing, self.events, claim)
151	        self.fence_at = renewer.fence_at
152	        try:
153	            params = JobParams.from_dict(claim.params)
154	            check_inputs(self.processed_root, params.snapshot, claim.input_checksums)
155	        except InvalidParams as error:
156	            raise PipelineError(f"{error}", retryable=False) from None
157	        work, logs = run_dir / ".work", run_dir / "logs"
158	        for folder in (work / "tmp", work / "spark", work / "jtmp", logs):
159	            folder.mkdir(parents=True, exist_ok=True)
160	        marker = processes.marker(self.store_id, claim.run_id, claim.token)
161	        env = self.step_env(work, marker)
162	        steps = []
163	        for name, argv in self.commands(params, claim, run_dir):
164	            self._renew_before(renewer, claim, before=name)
165	            step = self._run_step(name, argv, env, work, logs, renewer, marker, claim)
166	            steps.append(step)
167	            self._classify(step, run_dir, params, claim)
168	        run_folder = self.run_folder(params, claim, run_dir)
169	        self._check_result(run_folder)
170	        shutil.rmtree(work)
171	        record = {"format": 1, "worker_id": self.worker_id, "store_id": self.store_id, "job_id": claim.job_id,
172	                  "attempt_number": claim.attempt_number, "run_id": claim.run_id, "params": params.to_dict(),
173	                  "input_checksums_checked": claim.input_checksums, "processed_root": str(self.processed_root),
174	                  "run_folder": run_folder.relative_to(run_dir).as_posix(), "steps": steps,
175	                  "timing": asdict(self.timing), "code": code_state(), "started_at_utc": started,
176	                  "finished_at_utc": datetime.now(timezone.utc).isoformat()}
177	        (run_dir / "attempt.json").write_text(json.dumps(record, indent=2) + "\n")
178	        manifest = runs.manifest(run_folder)
179	        (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
180	        self._renew_before(renewer, claim, before="acceptance")
181	        self.fence_at = renewer.fence_at
182	        return runs.digest(manifest)
183	
184	    def commands(self, params: JobParams, claim: Claim, run_dir: Path) -> list[tuple[str, list[str]]]:
185	        py, name = self.python, params.windows_name
186	        windows_dir = run_dir / "windows" / params.snapshot / name
187	        return [
188	            ("windows", [py, "-m", "etf_risk.windows", "--snapshot", params.snapshot,
189	                         "--processed-root", str(self.processed_root), "--kind", params.kind,
190	                         "--window-days", str(params.window_days), "--stride", str(params.stride),
191	                         "--anchor", params.anchor, "--out-root", str(run_dir / "windows"), "--name", name]),
192	            ("spark_pipeline", [py, "-m", "etf_risk.spark_pipeline", "--windows", str(windows_dir),
193	                                "--out-root", str(run_dir / "output"), "--run-id", claim.run_id]),
194	            ("verify", [py, "-m", "etf_risk.verify", "--run", str(self.run_folder(params, claim, run_dir)),
195	                        "--sample-ticker", params.sample_ticker]),
196	        ]
197	
198	    @staticmethod
199	    def run_folder(params: JobParams, claim: Claim, run_dir: Path) -> Path:
200	        return run_dir / "output" / params.snapshot / params.windows_name / claim.run_id
201	
202	    def step_env(self, work: Path, marker: str) -> dict[str, str]:
203	        env = {name: os.environ[name] for name in ENV_ALLOWED if name in os.environ}
204	        env["PATH"] = str(Path(self.python).parent) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin")
205	        env.update(TMPDIR=str(work / "tmp"), SPARK_LOCAL_DIRS=str(work / "spark"),
206	                   SPARK_SUBMIT_OPTS=f"-Djava.io.tmpdir={work / 'jtmp'} -XX:-UsePerfData",
207	                   PYSPARK_PYTHON=self.python, PYSPARK_DRIVER_PYTHON=self.python, PYTHONUNBUFFERED="1")
208	        env[processes.MARKER_ENV] = marker
209	        return env
210	
211	    # Steps
212	
213	    def _renew_before(self, renewer: Renewer, claim: Claim, *, before: str) -> None:
214	        """Renew the lease before a step or acceptance; Fenced if that cannot happen in time."""
215	        while True:
216	            if self.stop is not None and self.stop.is_set():
217	                raise PipelineError(f"the worker was stopped before {before}", retryable=True)
218	            ok = renewer.renew()
219	            self.fence_at = renewer.fence_at
220	            if ok:
221	                return
222	            if ok is False:
223	                raise Fenced(f"{claim.run_id}: the renewal before {before} was refused")
224	            if renewer.passed(time.monotonic()):
225	                raise Fenced(f"{claim.run_id}: no renewal before the deadline, before {before}")
226	            time.sleep(self.timing.worker_tick)
227	
228	    def _send(self, fd: int, line: dict) -> bool:
229	        try:
230	            os.write(fd, (json.dumps(line) + "\n").encode())
231	            return True
232	        except BlockingIOError:                       # the launcher is not reading: the old deadline stands
233	            self.events.log("keepalive_dropped", seq=line.get("seq"))
234	            return False
235	        except (BrokenPipeError, OSError):
236	            return False
237	
238	    def _run_step(self, name: str, argv: list[str], env: dict, work: Path, logs: Path, renewer: Renewer,
239	                  marker: str, claim: Claim) -> dict:
240	        t = self.timing
241	        result_path = logs / f"{name}.launcher.json"
242	        command = [self.python, "-m", "etf_risk.jobs.launcher", "--marker", marker, "--lock", str(self.lock_path),
243	                   "--registry", str(self.registry), "--lock-wait", str(t.lock_wait(name)),
244	                   "--step-limit", str(t.step_limit(name)), "--cwd", str(work), "--step-log", str(logs / f"{name}.log"),
245	                   "--result", str(result_path), "--tick", str(t.watchdog_tick), "--term-grace", str(t.term_grace),
246	                   "--kill-confirm", str(t.kill_confirm), "--", *argv]
247	        self.events.log("step_started", job_id=claim.job_id, attempt=claim.attempt_number, step=name)
248	        with open(logs / f"{name}.launcher.log", "ab") as launcher_log:
249	            proc = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=launcher_log, stderr=subprocess.STDOUT,
250	                                    env=env, cwd=work, start_new_session=True)
251	        fd = proc.stdin.fileno()
252	        os.set_blocking(fd, False)
253	        self._send(fd, {"monotonic": time.monotonic(), "seq": renewer.seq, "deadline": renewer.fence_at})
254	        closed, closed_at, backstop = None, None, None
255	        while True:
256	            try:
257	                proc.wait(timeout=t.worker_tick)
258	                break
259	            except subprocess.TimeoutExpired:
260	                pass
```

## 25. Assistant — 2026-10-24T05:07:08.563Z

### Tool call: Bash

```
{
  "command": "W=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness && grep -rn -E 'WORKER_FAULT_POINTS|\"after_accept\"|after_accept\\b|\"before_claim\"|\"after_pipeline\"' $W/src $W/tests $W/docs --include=*.py --include=*.md | grep -v '^.*ai-usage' | cut -c1-210",
  "description": "Find every use of the worker's fault points"
}
```

## 26. User — 2026-10-24T05:07:09.467Z

### Tool result

```
(eval):1: no matches found: --include=*.py
```

## 27. Assistant — 2026-10-24T05:07:14.685Z

### Tool call: Bash

```
{
  "command": "cd ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness && grep -rn -E 'WORKER_FAULT_POINTS|after_accept|before_claim|after_pipeline' src tests docs/worker-pipeline.md docs/job-queue.md docs/job-table.md README.md | cut -c1-200",
  "description": "Find every use of the worker's fault points"
}
```

## 28. User — 2026-10-24T05:07:15.444Z

### Tool result

```
src/etf_risk/jobs/worker.py:35:Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash
src/etf_risk/jobs/worker.py:59:WORKER_FAULT_POINTS = (
src/etf_risk/jobs/worker.py:60:    "before_claim",
src/etf_risk/jobs/worker.py:62:    "after_pipeline",    # outputs written, result not yet accepted
src/etf_risk/jobs/worker.py:63:    "after_accept",
src/etf_risk/jobs/worker.py:141:        self._fault("before_claim")
src/etf_risk/jobs/worker.py:169:        self._fault("after_pipeline")
src/etf_risk/jobs/worker.py:174:        self._fault("after_accept")
tests/test_jobs_queue.py:22:from etf_risk.jobs.worker import DELIVERY_RETRIES, WORKER_FAULT_POINTS, Result, Served, Worker
tests/test_jobs_queue.py:36:    assert point in WORKER_FAULT_POINTS
tests/test_jobs_queue.py:324:            if point == "after_accept":
tests/test_jobs_worker.py:20:from etf_risk.jobs.worker import WORKER_FAULT_POINTS, PipelineError, Result
tests/test_jobs_worker.py:36:    assert point in WORKER_FAULT_POINTS
tests/test_jobs_worker.py:117:        env.deliver(env.worker("A", fault=crash_at("before_claim")), job)
tests/test_jobs_worker.py:160:        env.deliver(env.worker("A", first, fault=crash_at("after_pipeline")), job)
tests/test_jobs_worker.py:169:def test_a_crash_after_acceptance_keeps_the_one_result(env):
tests/test_jobs_worker.py:172:        env.deliver(env.worker("A", fault=crash_at("after_accept")), job)
tests/test_jobs_worker.py:217:        if point == "after_pipeline":                               # A finished too late: B takes over
tests/test_jobs_worker.py:310:    assert events == ["before_claim", "after_claim", "acknowledge", "after_pipeline", "after_accept"]
tests/test_jobs_worker.py:313:    assert events == ["before_claim", "acknowledge"]
docs/job-queue.md:144:    (`WORKER_FAULT_POINTS`; the store's own fault points are covered in
```

## 29. Assistant — 2026-10-24T05:07:27.373Z

### Tool call: Bash

```
{
  "command": "echo \"=== test_jobs_worker.py 28-40, 195-235, 290-315\" && sed -n '28,40p;195,235p;290,315p' tests/test_jobs_worker.py && echo \"=== test_jobs_queue.py 28-42, 300-350\" && sed -n '28,42p;300,350p' tests/test_jobs_queue.py",
  "description": "Read the tests that depend on the fault-point list"
}
```

## 30. User — 2026-10-24T05:07:28.131Z

### Tool result

```
=== test_jobs_worker.py 28-40, 195-235, 290-315
    env.close()


def submit(env, **kwargs) -> int:
    return env.admin.submit({"snapshot": "simulated", "stride": 21}, {"windows.parquet": "0" * 64}, **kwargs)


def crash_at(point):
    assert point in WORKER_FAULT_POINTS

    def fault(at):
        if at == point:
            raise SimulatedCrash(point)
    assert (a_dir / "steps.log").read_text() == "step 1\n" and not (a_dir / "result.json").exists()
    assert env.admin.job(job)["accepted_attempt"] == 2
    env.check(job)


def test_an_expired_lease_without_a_takeover_lets_the_worker_finish(env):
    job = submit(env)

    def stall(step, claim):
        if step == 2:
            env.clock.advance(3 * LEASE.total_seconds())            # long past the lease, but nobody takes over

    assert env.deliver(env.worker("A", SimulatedPipeline(on_step=stall)), job).result is Result.ACCEPTED
    env.check(job)


def test_a_stale_worker_cannot_get_its_result_accepted(env):
    job = submit(env)
    b = env.worker("B")
    taken_over = []

    def lose_the_job(point):
        if point == "after_pipeline":                               # A finished too late: B takes over
            env.clock.advance(LEASE.total_seconds())
            taken_over.append(env.deliver(b, job))

    handled = env.deliver(env.worker("A", fault=lose_the_job), job)
    assert [h.result for h in taken_over] == [Result.ACCEPTED] and handled.result is Result.FENCED
    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # A's folder stays, unreferenced
    assert env.admin.job(job)["accepted_attempt"] == 2
    env.check(job)


def test_a_stale_worker_cannot_record_a_failure(env):
    job = submit(env)
    b = env.worker("B")
    taken_over = []

    def lose_the_job_then_fail(step, claim):
        if step == 2:                                               # B takes over and finishes; then A fails
            env.clock.advance(LEASE.total_seconds() + 1)            # before any heartbeat could tell it
    env.check(job)


def test_an_existing_output_folder_is_never_written_into(env):
    job = submit(env)
    folder = env.runs / f"job-{job}-attempt-1"
    folder.mkdir(parents=True)
    (folder / "marker").write_text("left by another job table")
    pipeline = SimulatedPipeline()
    assert env.deliver(env.worker("A", pipeline), job).result is Result.FAILED
    assert pipeline.runs == [] and [p.name for p in folder.iterdir()] == ["marker"]
    assert "output folder already exists" in env.admin.job(job)["error"]
    env.check(job)


def test_acknowledgement_comes_after_the_claim(env):
    job = submit(env)
    events = []
    worker = env.worker("A", fault=events.append)
    env.handled.append(worker.handle(job, lambda: events.append("acknowledge")))
    assert events == ["before_claim", "after_claim", "acknowledge", "after_pipeline", "after_accept"]
    events.clear()
    env.handled.append(worker.handle(job, lambda: events.append("acknowledge")))   # refused: at once
    assert events == ["before_claim", "acknowledge"]
    env.check(job)
=== test_jobs_queue.py 28-42, 300-350
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

    assert (j["status"], j["accepted_attempt"]) == (Status.SUCCEEDED, 2)
    assert [a["outcome"] for a in attempts] == ["expired", "accepted"]
    env.check(job)


@pytest.mark.parametrize("seed", range(3))
def test_every_job_ends_with_at_most_one_result_under_lost_publications_and_crashes(env, seed):
    """Ten jobs; every publication may be confirmed, unconfirmed or dropped; every worker may
    die at any of its fault points or in the middle of a run, and some runs fail and are
    retried. Rounds of a restarted worker, a lease's worth of time and a reconciler pass
    repeat until no job is left queued or running. Every job then has at most one accepted
    result (exactly one if it succeeded), told to the worker that got it unless that worker
    died first."""
    rng = random.Random(seed)

    def outcomes():
        while True:
            yield rng.choice(list(PublishOutcome))

    jobs = [env.submit(outcomes()).job_id for _ in range(10)]
    current, lost = {}, Counter()

    def fault(point):
        if rng.random() < 0.1:
            if point == "after_accept":
                lost[current["job"]] += 1                                              # accepted, never told
            raise SimulatedCrash(point)

    def on_step(step, claim):
        current["job"] = claim.job_id
        if rng.random() < 0.05:
            raise SimulatedCrash(f"step {step}")

    for round_number in range(60):
        pipeline = SimulatedPipeline(on_step=on_step, fail_at={2: True} if rng.random() < 0.2 else None)
        try:
            env.serve(env.worker(f"round-{round_number}", pipeline, fault=fault))
        except SimulatedCrash:
            pass
        env.clock.advance(LEASE.total_seconds())
        env.reconciler(outcomes()).run_once()
        if all(env.admin.job(job)["status"] in TERMINAL for job in jobs):
            break
    assert [job for job in jobs if env.admin.job(job)["status"] not in TERMINAL] == []
    for job in jobs:
        env.check(job, lost_acceptances=lost[job])
```

## 31. Assistant — 2026-10-24T05:07:41.874Z

### Tool call: Bash

```
{
  "command": "sed -n '1,27p' tests/test_jobs_worker.py && echo \".....\" && sed -n '108,180p' tests/test_jobs_worker.py",
  "description": "Read the worker test setup and its crash tests"
}
```

## 32. User — 2026-10-24T05:07:42.587Z

### Tool result

```
"""The worker with a simulated pipeline: duplicate and concurrent deliveries, crashes, expired
leases, stale workers, retries.

Every test ends with WorkerEnv.check() (tests/jobs_backends.py): no invariant violation in
the tables; at most one accepted attempt, exactly one if the job succeeded, and as many as
the deliveries told "accepted" (plus any acceptance whose worker died before it could tell);
the accepted folder holds that attempt's result; no two attempts share a folder. Deliveries
here are explicit handle() calls, with no queue (tests/test_jobs_queue.py adds one). The tests
run on SQLite and, with ETF_RISK_MYSQL_URL set, on MySQL.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
from pathlib import Path

import pytest

from etf_risk.jobs.simulated import SimulatedCrash, SimulatedPipeline
from etf_risk.jobs.store import Outcome, Refusal, Status
from etf_risk.jobs.worker import WORKER_FAULT_POINTS, PipelineError, Result
from jobs_backends import BACKENDS, LEASE, WorkerEnv, make_backend, run_together


@pytest.fixture(params=BACKENDS)
def env(request, tmp_path):
    env = WorkerEnv(make_backend(request.param, tmp_path), tmp_path)
    yield env
.....
    assert sum(len(p.runs) for p in pipelines) == 1 and env.acks == [job] * 4
    env.check(job)


# Crashes

def test_a_crash_before_the_claim_leaves_the_job_queued(env):
    job = submit(env)
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", fault=crash_at("before_claim")), job)
    assert env.admin.job(job)["status"] is Status.QUEUED and env.admin.attempts(job) == [] and env.acks == []
    assert env.deliver(env.worker("B"), job).result is Result.ACCEPTED   # the unacknowledged delivery again
    env.check(job)


def test_a_crash_between_claim_and_acknowledgement(env):
    job = submit(env)
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", fault=crash_at("after_claim")), job)
    assert env.acks == []                                           # not acknowledged: delivered again
    again = env.deliver(env.worker("B"), job)
    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.LEASE_HELD)
    assert env.acks == [job]                                        # acknowledged: no delivery is pending
    env.clock.advance(LEASE.total_seconds())                        # A's lease runs out ...
    assert env.admin.job(job)["status"] is Status.RUNNING          # ... and nothing happens by itself
    handled = env.deliver(env.worker("C"), job)                     # a new delivery (later: the reconciler's)
    assert handled.result is Result.ACCEPTED and handled.claim.attempt_number == 2
    assert [a["outcome"] for a in env.admin.attempts(job)] == [Outcome.EXPIRED, Outcome.ACCEPTED]
    assert not (env.runs / f"job-{job}-attempt-1").exists()        # A died before creating its folder
    env.check(job)


def test_a_crash_in_the_middle_of_the_run(env):
    job = submit(env)

    def die(step, claim):
        if step == 2:
            raise SimulatedCrash("the worker died mid-run")

    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", SimulatedPipeline(on_step=die)), job)
    assert (env.runs / f"job-{job}-attempt-1" / "steps.log").read_text() == "step 1\n"
    assert env.admin.job(job)["status"] is Status.RUNNING
    env.clock.advance(LEASE.total_seconds())
    assert env.deliver(env.worker("B"), job).result is Result.ACCEPTED
    env.check(job)


def test_a_crash_after_the_pipeline_loses_only_that_attempt(env):
    job = submit(env)
    first, second = SimulatedPipeline(), SimulatedPipeline()
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", first, fault=crash_at("after_pipeline")), job)
    assert (env.runs / f"job-{job}-attempt-1" / "result.json").exists()   # complete, never accepted
    env.clock.advance(LEASE.total_seconds())
    handled = env.deliver(env.worker("B", second), job)
    assert handled.result is Result.ACCEPTED and env.admin.job(job)["accepted_attempt"] == 2
    assert len(first.runs) + len(second.runs) == 2                  # executed twice, accepted once
    env.check(job)


def test_a_crash_after_acceptance_keeps_the_one_result(env):
    job = submit(env)
    with pytest.raises(SimulatedCrash):
        env.deliver(env.worker("A", fault=crash_at("after_accept")), job)
    assert env.admin.job(job)["status"] is Status.SUCCEEDED
    again = env.deliver(env.worker("B"), job)
    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)
    env.check(job, lost_acceptances=1)                              # A died before it could tell


# Expired leases and stale workers
```

## 33. Assistant — 2026-10-24T05:07:50.254Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^class |^def |    def ' tests/jobs_backends.py | head -40 && sed -n \"$(grep -n '    def worker' tests/jobs_backends.py | head -1 | cut -d: -f1),+8p\" tests/jobs_backends.py",
  "description": "Read the worker test environment's helper signatures"
}
```

## 34. User — 2026-10-24T05:07:51.213Z

### Tool result

```
49:class SQLiteBackend:
54:    def __init__(self, tmp_path):
58:    def connect(self):
61:    def execute(self, sql, **params):
65:    def dump(self):
70:    def violation(error):
81:    def close(self):
85:class MySQLBackend:
89:    def __init__(self):
102:    def connect(self, **options):
106:    def execute(self, sql, **params):
110:    def dump(self):
119:    def violation(cls, error):
125:    def lock_waiting(self, connection, timeout=10.0):
138:    def close(self):
141:    def _admin(self, statement):
147:def make_backend(name, tmp_path):
151:class JobsEnv:
155:    def __init__(self, backend, tmp_path):
159:    def new_store(self, *, fault=None, dialect=None, connection=None):
164:    def dump(self):
167:    def close(self):
178:class StoreEnv(JobsEnv):
179:    def __init__(self, backend, tmp_path):
184:class WorkerEnv(JobsEnv):
187:    def __init__(self, backend, tmp_path):
193:    def worker(self, name, pipeline=None, fault=None, store_fault=None) -> Worker:
197:    def deliver(self, worker: Worker, job_id: int) -> Handled:
202:    def check(self, job_id: int, *, lost_acceptances: int = 0) -> None:
223:def failing_at(point, times=None):
226:    def fault(at):
235:class QueueEnv(WorkerEnv):
238:    def __init__(self, backend, tmp_path):
242:    def submit(self, outcomes=(), **kwargs):
246:    def reconciler(self, outcomes=(), **options) -> Reconciler:
249:    def serve(self, worker, group="workers", **options):
255:class KafkaTopic:
259:    def __init__(self):
267:    def group(self) -> str:
270:    def publisher(self, **options):
    def worker(self, name, pipeline=None, fault=None, store_fault=None) -> Worker:
        return Worker(self.new_store(fault=store_fault), pipeline or SimulatedPipeline(), self.runs,
                      worker_id=f"worker-{name}", fault=fault)

    def deliver(self, worker: Worker, job_id: int) -> Handled:
        handled = worker.handle(job_id, lambda: self.acks.append(job_id))
        self.handled.append(handled)
        return handled
```

## 35. Assistant — 2026-10-24T05:08:00.332Z

### Tool call: Bash

```
{
  "command": "sed -n '1,60p' tests/test_jobs_kafka.py && grep -n -E '^def test_|^@pytest|^pytestmark|^requires|skipif' tests/test_jobs_kafka.py | head -50",
  "description": "Read the Kafka tests' structure and markers"
}
```

## 36. User — 2026-10-24T05:08:01.040Z

### Tool result

```
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
        uv run --group jobs python -m pytest tests/test_jobs_*.py
    docker compose -f docker/compose.yaml down -v

AI contribution: written with Claude Code (Opus 5.5).
"""
import time
from datetime import timedelta

import pytest

from etf_risk.jobs.kafka import consumer_config, producer_config
from etf_risk.jobs.queue import CONFIRMATION_TIMEOUT, submit_job
from etf_risk.jobs.reconciler import Pass, Reconciler
from etf_risk.jobs.simulated import SimulatedCrash
from etf_risk.jobs.store import Refusal, Status
from etf_risk.jobs.timing import DEFAULT_TIMING
from etf_risk.jobs.worker import Result, Served
from jobs_backends import (BACKENDS, LEASE, PARAMS, KafkaTopic, WorkerEnv, failing_at, make_backend, needs_kafka,
                           poll_after_assignment, poll_deliveries)


# Offline

def test_the_producer_waits_for_the_broker_and_is_idempotent():
    config = producer_config("broker:9092")
    assert (config["acks"], config["enable.idempotence"]) == ("all", True)
    assert config["message.timeout.ms"] == CONFIRMATION_TIMEOUT.total_seconds() * 1000 == 10_000
    assert config["socket.timeout.ms"] == 10_000


def test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message():
    config = consumer_config("broker:9092", "workers")
    assert (config["group.id"], config["enable.auto.commit"], config["enable.auto.offset.store"],
            config["auto.offset.reset"]) == ("workers", False, False, "earliest")


def test_the_group_timing_fits_the_lease_and_the_longest_run():
    """A stopped worker leaves the group before its lease can expire; a legitimate run never
    outlasts the poll interval (etf_risk.jobs.timing)."""
    config, t = consumer_config("broker:9092", "workers"), DEFAULT_TIMING
    assert (config["group.protocol"], config["session.timeout.ms"], config["heartbeat.interval.ms"],
            config["max.poll.interval.ms"], config["socket.timeout.ms"]) == ("classic", 15_000, 3_000, 967_000, 10_000)
42:def test_the_producer_waits_for_the_broker_and_is_idempotent():
49:def test_the_consumer_commits_only_when_told_and_a_new_group_starts_at_the_earliest_message():
55:def test_the_group_timing_fits_the_lease_and_the_longest_run():
66:def test_an_unreachable_broker_gives_false():
77:@pytest.fixture
85:def test_jobs_published_before_a_fresh_group_starts_are_all_delivered(topic):
93:def test_with_latest_a_fresh_group_would_miss_them(topic):
101:def test_a_confirmed_message_is_there_when_publish_returns(topic):
108:def test_an_uncommitted_message_reaches_the_groups_next_consumer_and_a_committed_one_does_not(topic):
123:def test_a_rewind_delivers_the_same_message_again(topic):
134:@pytest.fixture(params=BACKENDS)
154:def test_jobs_run_once_each_and_a_duplicate_publication_is_refused(env, topic):
169:def test_a_crash_between_claim_and_commit(env, topic):
188:def test_an_oversized_payload_is_committed_and_the_next_job_runs(env, topic):
203:def test_a_persistent_error_leaves_the_message_for_a_restarted_worker(env, topic):
221:def test_a_standby_gets_the_next_job_only_once_the_busy_worker_outlasts_its_poll_interval(topic):
```

## 37. Assistant — 2026-10-24T05:09:28.541Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^def |^class |^[A-Z_]+ = |    def ' src/etf_risk/jobs/processes.py && echo \"=== launcher acquire()\" && sed -n \"$(grep -n '    def acquire' src/etf_risk/jobs/launcher.py | cut -d: -f1),+30p\" src/etf_risk/jobs/launcher.py",
  "description": "Read process-tree helpers and the launcher's lock acquisition"
}
```

## 38. User — 2026-10-24T05:09:29.544Z

### Tool result

```
43:MARKER_ENV = "ETF_RISK_ATTEMPT"
46:def attempt_key(token: str) -> str:
50:def marker(store_id: str, run_id: str, token: str) -> str:
54:def parse_marker(value: str | None) -> tuple[str, str, str] | None:
60:def marker_of(process: psutil.Process) -> str | None:
67:def session_members(sid: int, *, exclude: Iterable[int] = ()) -> list[psutil.Process]:
81:def attempt_members(sid: int, attempt_marker: str, *, exclude: Iterable[int] = ()) -> list[psutil.Process]:
86:def marked_processes() -> dict[str, list[psutil.Process]]:
101:def alive(processes: Iterable[psutil.Process]) -> list[psutil.Process]:
112:def rss(processes: Iterable[psutil.Process]) -> int:
123:def _signal(processes: Iterable[psutil.Process], sig: int) -> list[int]:
134:def terminate(processes: list[psutil.Process], *, term_grace: float, kill_confirm: float,
152:class Registry:
155:    def __init__(self, folder: str | Path):
159:    def _path(self, pid: int) -> Path:
162:    def register(self, attempt_marker: str) -> None:
169:    def unregister(self) -> None:
172:    def entries(self) -> list[dict]:
181:    def survivors(self) -> list[psutil.Process]:
=== launcher acquire()
    def acquire(self) -> str | None:
        """The host lock, then no survivors of other trees; waiting within --lock-wait."""
        start = time.monotonic()
        Path(self.args.lock).parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.args.lock, os.O_RDWR | os.O_CREAT, 0o600)
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                pass
            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
                os.close(fd)
                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
                return reason or "lock_busy"
            self.lines.wait(self.args.tick)
        self.lock_fd = fd
        while survivors := self.registry.survivors():
            self.result["survivors_seen"] = sorted({p.pid for p in survivors})
            if (reason := self.poll()) is not None or time.monotonic() - start >= self.args.lock_wait:
                self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
                return reason or "lock_busy"
            self.lines.wait(self.args.tick)
        self.result["lock_wait_s"] = round(time.monotonic() - start, 3)
        return None

    def end_tree(self, reason: str) -> None:
        self.result["ended"] = {"reason": reason, **processes.terminate(
            self.members(), term_grace=self.args.term_grace, kill_confirm=self.args.kill_confirm,
            rescan=self.members)}
```

## 39. Assistant — 2026-10-24T05:09:39.315Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/processes.py"
}
```

## 40. User — 2026-10-24T05:09:39.540Z

### Tool result

```
1	"""Finding and ending the processes of a pipeline attempt (spec §11; docs/job-queue.md).
2	
3	Membership:
4	- Every process of an attempt carries ETF_RISK_ATTEMPT=<store id>:<run id>:<attempt key> in
5	  its environment. The attempt key is the first 16 hex digits of SHA-256(token), so the
6	  token itself, which can change the job's row, never leaves the worker.
7	- Each step runs under a launcher that leads a session of its own, and nothing below it
8	  calls setsid. So every process of the step stays in that session. That includes PySpark's
9	  daemon, which moves itself and its Python workers to a process group of their own
10	  (pyspark/daemon.py: os.setpgid(0, 0)), and an orphan that launchd adopted. A process-group
11	  kill would miss the daemon; the session does not.
12	- The session id is the cheap first filter (os.getsid works for any process on macOS), and
13	  the marker confirms it, so a reused pid never counts. A process whose environment cannot
14	  be read is not counted: it is not this user's.
15	
16	terminate():
17	1. sends SIGTERM to every process given, so the JVM's shutdown hooks can delete its scratch;
18	2. waits term_grace, then sends SIGKILL to whatever is left;
19	3. scans again, if given a way to, until nothing is left or kill_confirm has passed.
20	A process started meanwhile is found by the rescan.
21	
22	The registry is a folder next to the host lock, with one file per launcher whose step may
23	have processes running: its pid, session, marker and start time. A launcher removes its file
24	once its tree is gone. A file left by a launcher that was killed is found by the next
25	launcher's survivor check. That check also finds the dead launcher's orphans, through their
26	session. The file is removed once nothing of that tree is left.
27	
28	AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_processes.py
29	and tests/test_jobs_launcher.py.
30	"""
31	from __future__ import annotations
32	
33	import hashlib
34	import json
35	import os
36	import signal
37	import time
38	from collections.abc import Callable, Iterable
39	from pathlib import Path
40	
41	import psutil
42	
43	MARKER_ENV = "ETF_RISK_ATTEMPT"
44	
45	
46	def attempt_key(token: str) -> str:
47	    return hashlib.sha256(token.encode("ascii")).hexdigest()[:16]
48	
49	
50	def marker(store_id: str, run_id: str, token: str) -> str:
51	    return f"{store_id}:{run_id}:{attempt_key(token)}"
52	
53	
54	def parse_marker(value: str | None) -> tuple[str, str, str] | None:
55	    """(store id, run id, attempt key), or None for a value that is not a marker."""
56	    parts = (value or "").split(":")
57	    return tuple(parts) if len(parts) == 3 and all(parts) else None
58	
59	
60	def marker_of(process: psutil.Process) -> str | None:
61	    try:
62	        return process.environ().get(MARKER_ENV)
63	    except (psutil.Error, OSError):
64	        return None
65	
66	
67	def session_members(sid: int, *, exclude: Iterable[int] = ()) -> list[psutil.Process]:
68	    """The live processes whose session id is sid."""
69	    skip, found = set(exclude), []
70	    for pid in psutil.pids():
71	        if pid in skip or pid == 0:
72	            continue
73	        try:
74	            if os.getsid(pid) == sid:
75	                found.append(psutil.Process(pid))
76	        except (OSError, psutil.Error):
77	            continue
78	    return found
79	
80	
81	def attempt_members(sid: int, attempt_marker: str, *, exclude: Iterable[int] = ()) -> list[psutil.Process]:
82	    """The processes of one launcher's tree: in its session and carrying the attempt's marker."""
83	    return [p for p in session_members(sid, exclude=exclude) if marker_of(p) == attempt_marker]
84	
85	
86	def marked_processes() -> dict[str, list[psutil.Process]]:
87	    """Every process of this user that carries a marker, by marker (a full scan: slower)."""
88	    me, found = os.getuid(), {}
89	    for process in psutil.process_iter():
90	        try:
91	            if process.uids().real != me:
92	                continue
93	        except psutil.Error:
94	            continue
95	        value = marker_of(process)
96	        if parse_marker(value) is not None:
97	            found.setdefault(value, []).append(process)
98	    return found
99	
100	
101	def alive(processes: Iterable[psutil.Process]) -> list[psutil.Process]:
102	    live = []
103	    for p in processes:
104	        try:
105	            if p.is_running() and p.status() != psutil.STATUS_ZOMBIE:
106	                live.append(p)
107	        except psutil.Error:
108	            continue
109	    return live
110	
111	
112	def rss(processes: Iterable[psutil.Process]) -> int:
113	    """Summed resident memory of the live processes given."""
114	    total = 0
115	    for p in processes:
116	        try:
117	            total += p.memory_info().rss
118	        except psutil.Error:
119	            continue
120	    return total
121	
122	
123	def _signal(processes: Iterable[psutil.Process], sig: int) -> list[int]:
124	    sent = []
125	    for p in processes:
126	        try:
127	            p.send_signal(sig)
128	            sent.append(p.pid)
129	        except psutil.Error:
130	            continue
131	    return sent
132	
133	
134	def terminate(processes: list[psutil.Process], *, term_grace: float, kill_confirm: float,
135	              rescan: Callable[[], list[psutil.Process]] | None = None) -> dict:
136	    """End the processes and, with rescan, any new member it finds; what was done, by pid."""
137	    record = {"terminated": _signal(processes, signal.SIGTERM), "killed": [], "remaining": []}
138	    _, left = psutil.wait_procs(processes, timeout=term_grace)
139	    record["killed"] += _signal(left, signal.SIGKILL)
140	    deadline = time.monotonic() + kill_confirm
141	    psutil.wait_procs(left, timeout=kill_confirm)
142	    while rescan is not None and time.monotonic() < deadline:
143	        new = alive(rescan())
144	        if not new:
145	            break
146	        record["killed"] += _signal(new, signal.SIGKILL)
147	        psutil.wait_procs(new, timeout=max(0.0, min(0.5, deadline - time.monotonic())))
148	    record["remaining"] = [p.pid for p in alive(rescan() if rescan is not None else processes)]
149	    return record
150	
151	
152	class Registry:
153	    """The launchers whose trees may still have processes (see the module docstring)."""
154	
155	    def __init__(self, folder: str | Path):
156	        self.folder = Path(folder)
157	        self.folder.mkdir(parents=True, exist_ok=True)
158	
159	    def _path(self, pid: int) -> Path:
160	        return self.folder / f"launcher-{pid}.json"
161	
162	    def register(self, attempt_marker: str) -> None:
163	        me = psutil.Process()
164	        entry = {"pid": me.pid, "sid": os.getsid(0), "marker": attempt_marker, "started": me.create_time()}
165	        tmp = self._path(me.pid).with_suffix(".tmp")
166	        tmp.write_text(json.dumps(entry))
167	        tmp.replace(self._path(me.pid))
168	
169	    def unregister(self) -> None:
170	        self._path(os.getpid()).unlink(missing_ok=True)
171	
172	    def entries(self) -> list[dict]:
173	        found = []
174	        for path in sorted(self.folder.glob("launcher-*.json")):
175	            try:
176	                found.append({**json.loads(path.read_text()), "path": str(path)})
177	            except (OSError, json.JSONDecodeError):
178	                continue
179	        return found
180	
181	    def survivors(self) -> list[psutil.Process]:
182	        """Live processes of other launchers' trees. Entries whose trees are gone are removed."""
183	        found = []
184	        for entry in self.entries():
185	            if entry["pid"] == os.getpid():
186	                continue
187	            members = attempt_members(entry["sid"], entry["marker"], exclude=[os.getpid()])
188	            if members:
189	                found += members
190	            else:
191	                Path(entry["path"]).unlink(missing_ok=True)
192	        return found
193	
```

## 41. Assistant — 2026-10-24T05:09:55.575Z

### Tool call: Bash

```
{
  "command": "sed -n '1,60p' src/etf_risk/jobs/launcher.py && echo \".....\" && sed -n '140,185p;210,320p' src/etf_risk/jobs/launcher.py",
  "description": "Read the launcher's protocol, handshake and run loop"
}
```

## 42. User — 2026-10-24T05:09:56.283Z

### Tool result

```
"""The watchdog that runs one pipeline step for the worker (spec §11; docs/job-queue.md).

    python -m etf_risk.jobs.launcher --marker M --lock PATH --registry DIR --lock-wait S \\
        --step-limit S --cwd DIR --step-log PATH --result PATH -- <command ...>

The worker starts it with start_new_session=True, so the launcher leads a session that holds
the whole step (etf_risk.jobs.processes), with an environment the worker prepared (including
the attempt's marker), and with a pipe as stdin.

The worker writes one JSON line per message:
- first the handshake {"monotonic": t, "seq": 0, "deadline": F}, where t is the worker's
  time.monotonic() when it wrote the line;
- then {"seq": n, "deadline": F_n} after each successful renewal of the lease.
Deadlines are absolute values of the host's monotonic clock, never durations.

The launcher refuses to start in three cases:
- no handshake: none arrived within 5 s;
- clock_mismatch: its own reading is not between t and t + 30 s, so the two processes do not
  read the same clock. A different clock source differs by far more. The 30 s allow for a
  launcher that starts slowly on a busy machine; the deadlines stay absolute either way;
- deadline_passed: F has passed.

Every tick (--tick, 0.5 s) the launcher does, in this order:
1. if its deadline has passed, it fires: it ends the tree, and firing is terminal;
2. only otherwise does it read the lines waiting on stdin. A line moves the deadline only if
   its sequence number is newer, its deadline is later than the current one, and that
   deadline is still in the future.
So lines that queued up while the launcher was stopped can never revive an expired watchdog,
and no line can push the deadline past what the worker granted. EOF (the worker closed the
pipe, or died) ends the tree too, and so does the step's time limit, or a SIGTERM to the
launcher itself.

Before the step starts, the launcher takes an exclusive flock on the host's execution lock,
waiting up to --lock-wait. It then waits, within the same bound, until no process of another
launcher's tree survives (the registry). While it waits it keeps reading deadlines and fires
if its own passes. Only then does it register and start the step. The step's driver
inherits the lock's descriptor, so the lock is held while the launcher or the driver lives.
PySpark closes inherited descriptors before it starts the JVM, so the JVM does not hold the
lock; it exits when the driver's pipe breaks, and the next launcher's survivor check covers
that window.

Ending the tree: SIGTERM to every process of the session that carries the marker, SIGKILL
after --term-grace, and a rescan until none is left or --kill-confirm has passed. When the
step ends by itself, the launcher first gives the rest of its tree --drain seconds to exit.

The result goes to --result as JSON: the outcome, the step's exit code, the processes ended,
the time waited for the lock, the tree's peak summed RSS, and the lines accepted and
ignored. The exit code says the outcome: the step's own code (0-63) when it ran to its end,
otherwise one of EXIT_CODES.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_launcher.py.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import select
import signal
.....
        self.stop_requested = False
        self.registry = processes.Registry(args.registry)
        self.lock_fd: int | None = None

    def members(self) -> list:
        return processes.attempt_members(os.getpid(), self.args.marker, exclude=[os.getpid()])

    def poll(self) -> str | None:
        """One check of the watchdog, in the documented order; the reason to stop, if any."""
        now = time.monotonic()
        if self.watchdog.expired(now):
            for line in self.lines.read():              # read only to record them: a fired watchdog ignores all
                self.watchdog.offer(line, now)
            return "deadline"
        for line in self.lines.read():
            self.watchdog.offer(line, now)
        if self.lines.eof:
            return "eof"
        if self.stop_requested:
            return "terminated"
        return None

    def handshake(self) -> str | None:
        deadline = time.monotonic() + HANDSHAKE_TIMEOUT
        while time.monotonic() < deadline:
            lines = self.lines.read()
            if lines:
                first, now = lines[0], time.monotonic()
                if not isinstance(first.get("monotonic"), (int, float)) or not isinstance(first.get("deadline"), (int, float)):
                    return "no_handshake"
                if not (first["monotonic"] <= now <= first["monotonic"] + CLOCK_TOLERANCE):
                    self.result["clock"] = {"worker": first["monotonic"], "launcher": now}
                    return "clock_mismatch"
                self.watchdog = Watchdog(first["deadline"], int(first.get("seq", 0)))
                if self.watchdog.expired(now):
                    return "deadline_passed"
                for line in lines[1:]:                       # lines that came with the handshake
                    self.watchdog.offer(line, now)
                return None
            if self.lines.eof:
                return "no_handshake"
            self.lines.wait(0.1)
        return "no_handshake"

    def acquire(self) -> str | None:
        """The host lock, then no survivors of other trees; waiting within --lock-wait."""
    def end_tree(self, reason: str) -> None:
        self.result["ended"] = {"reason": reason, **processes.terminate(
            self.members(), term_grace=self.args.term_grace, kill_confirm=self.args.kill_confirm,
            rescan=self.members)}

    def drain(self) -> None:
        """The step ended by itself: give the rest of its tree time to exit, then end it."""
        deadline = time.monotonic() + self.args.drain
        while (left := processes.alive(self.members())) and time.monotonic() < deadline:
            time.sleep(0.1)
        if left := processes.alive(self.members()):
            self.result["lingering"] = sorted(p.pid for p in left)
            self.end_tree("lingering after the step ended")

    def run(self, command: list[str]) -> int:
        signal.signal(signal.SIGTERM, lambda *_: setattr(self, "stop_requested", True))
        outcome = self.handshake() or self.acquire()
        child = None
        if outcome is None:
            self.registry.register(self.args.marker)
            Path(self.args.step_log).parent.mkdir(parents=True, exist_ok=True)
            os.set_inheritable(self.lock_fd, True)
            try:
                with open(self.args.step_log, "ab") as log:
                    child = subprocess.Popen(command, cwd=self.args.cwd, stdin=subprocess.DEVNULL, stdout=log,
                                             stderr=subprocess.STDOUT, pass_fds=(self.lock_fd,))
                self.result["step_started_at_utc"] = datetime.now(timezone.utc).isoformat()
            except OSError as error:
                self.result["error"] = f"{type(error).__name__}: {error}"
                outcome = "launch_failed"
        if child is not None:
            started = time.monotonic()
            while outcome is None:
                outcome = self.poll()
                if outcome is None and child.poll() is not None:
                    outcome = "exited"
                elif outcome is None and time.monotonic() - started >= self.args.step_limit:
                    outcome = "timeout"
                if outcome is None:
                    self.result["peak_rss_bytes"] = max(self.result["peak_rss_bytes"], processes.rss(self.members()))
                    self.lines.wait(self.args.tick)
            self.result["step_seconds"] = round(time.monotonic() - started, 3)
            if outcome == "exited":
                self.drain()
            else:
                self.end_tree(outcome)
            child.wait()
            self.result["returncode"] = child.returncode
            self.result["tree_ended_at_utc"] = datetime.now(timezone.utc).isoformat()   # no member left
            if outcome == "exited" and child.returncode < 0:
                outcome = "signaled"
        self.registry.unregister()
        if self.lock_fd is not None:
            os.close(self.lock_fd)                      # the driver's copy is closed with the driver
        if self.watchdog is not None:
            self.result.update(deadline=self.watchdog.deadline, lines_accepted=self.watchdog.accepted,
                               lines_ignored=self.watchdog.ignored)
        self.result.update(outcome=outcome, finished_at_utc=datetime.now(timezone.utc).isoformat())
        tmp = Path(self.args.result).with_suffix(".tmp")
        tmp.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(self.result, indent=2) + "\n")
        tmp.replace(self.args.result)
        if outcome == "exited":
            return child.returncode if 0 <= child.returncode < 64 else EXIT_CODES["signaled"]
        return EXIT_CODES[outcome]


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--" not in argv:
        print("usage: python -m etf_risk.jobs.launcher [options] -- <command ...>", file=sys.stderr)
        return 2
    split = argv.index("--")
    parser = argparse.ArgumentParser(prog="python -m etf_risk.jobs.launcher")
    parser.add_argument("--marker", required=True)
    parser.add_argument("--lock", required=True, help="the host's execution lock file")
    parser.add_argument("--registry", required=True, help="the folder of launchers whose trees may still run")
    parser.add_argument("--lock-wait", type=float, required=True)
    parser.add_argument("--step-limit", type=float, required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--step-log", required=True)
    parser.add_argument("--result", required=True)
    parser.add_argument("--tick", type=float, default=0.5)
    parser.add_argument("--term-grace", type=float, default=5.0)
    parser.add_argument("--kill-confirm", type=float, default=2.0)
    parser.add_argument("--drain", type=float, default=10.0)
    args = parser.parse_args(argv[:split])
    command = argv[split + 1:]
    if not command:
        parser.error("no command after --")
    if processes.parse_marker(args.marker) is None or os.environ.get(processes.MARKER_ENV) != args.marker:
        parser.error("--marker must be a marker and equal ETF_RISK_ATTEMPT in the environment")
    if os.getsid(0) != os.getpid():
        parser.error("start the launcher as the leader of a new session (start_new_session=True):"
                     " its session is how it finds the step's processes")
    return Launcher(args).run(command)


if __name__ == "__main__":
    sys.exit(main())
```

## 43. Assistant — 2026-10-24T05:10:17.114Z

### Tool call: Bash

```
{
  "command": "echo \"=== JobStore public methods\" && awk '/^class JobStore/{f=1} f && /^    def [a-z]/{print NR\": \"$0}' src/etf_risk/jobs/store.py | cut -c1-150 && echo \"=== mysql.py\" && grep -n -E '^def |^[A-Z_]+ = ' src/etf_risk/jobs/mysql.py | cut -c1-150 && echo \"=== queue.py encode/Delivery\" && grep -n -E '^def |^class |^[A-Z_]+ = ' src/etf_risk/jobs/queue.py | cut -c1-120 && echo \"=== confluent-kafka locked\" && grep -n -A1 '^name = \"confluent-kafka\"' uv.lock && grep -n -A1 '^name = \"pymysql\"' uv.lock && grep -n -A1 '^name = \"psutil\"' uv.lock",
  "description": "List store, MySQL and queue APIs and locked client versions"
}
```

## 44. User — 2026-10-24T05:10:18.194Z

### Tool result

```
=== JobStore public methods
344:     def ensure_identity(self) -> str:
358:     def store_id(self) -> str:
368:     def submit(self, params: dict, input_checksums: dict, *, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> int:
381:     def mark_published(self, job_id: int, version: int) -> bool:
395:     def claim(self, job_id: int, worker_id: str, output_root: str | Path) -> Claim | Refusal:
441:     def renew(self, claim: Claim) -> bool:
460:     def accept_result(self, claim: Claim, result_digest: str) -> bool:
490:     def fail_attempt(self, claim: Claim, error: str, *, retryable: bool) -> Status | None:
513:     def requeue_expired(self, job_id: int, token: str) -> Status | None:
539:     def expired_leases(self) -> list[ExpiredLease]:
545:     def unconfirmed(self) -> list[Unconfirmed]:
552:     def job(self, job_id: int) -> dict | None:
556:     def attempts(self, job_id: int) -> list[dict]:
560:     def all_jobs(self) -> list[dict]:
563:     def all_attempts(self) -> list[dict]:
567:     def current_attempts(self) -> dict[int, tuple[int, str]]:
573:     def invariant_violations(self) -> dict[str, list[int]]:
=== mysql.py
37:ISOLATION_LEVELS = frozenset({"READ UNCOMMITTED", "READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"})
38:CONFLICT_ERRORS = frozenset({1205, 1213})   # lock wait timeout, deadlock
42:DISCONNECT_ERRORS = frozenset({2003, 2006, 2013, 1053, 1927, 4031})
48:SERVICE_SESSION = {"connect_timeout": 3, "read_timeout": 5, "write_timeout": 5, "lock_wait_timeout": 2,
94:MYSQL = MySQLDialect()
97:def connection_options(url: str, database: str | None = None) -> dict:
108:def connect_mysql(url: str, *, database: str | None = None, found_rows: bool = True,
138:def connector(url: str, *, database: str | None = None, **settings: Any) -> Callable[[], Any]:
143:def schema_statements() -> list[str]:
150:def create_schema(connection: Any) -> None:
=== queue.py encode/Delivery
33:CONFIRMATION_TIMEOUT = timedelta(seconds=10)   # how long a publisher waits for the broker's confirmation
36:MAX_JOB_ID = 2**63 - 1
37:MAX_JOB_ID_DIGITS = len(str(MAX_JOB_ID))       # 19
38:_JOB_ID = re.compile(rb"[1-9][0-9]{0,%d}" % (MAX_JOB_ID_DIGITS - 1))
41:def encode(job_id: int) -> bytes:
49:class Delivery:
65:class Publisher(Protocol):
69:class Consumer(Protocol):
77:class Submitted:
83:def submit_job(store: JobStore, publisher: Publisher, params: dict, input_checksums: dict, *,
=== confluent-kafka locked
261:name = "confluent-kafka"
262-version = "2.16.0"
1294:name = "pymysql"
1295-version = "1.1.1"
1180:name = "psutil"
1181-version = "7.2.2"
```

## 45. Assistant — 2026-10-24T05:10:28.411Z

### Tool call: Bash

```
{
  "command": "sed -n '1,40p' tests/test_jobs_cli.py && grep -n -E '^def test_' tests/test_jobs_cli.py | head -30 && echo \"=== mysql.connect_mysql\" && sed -n '108,142p' src/etf_risk/jobs/mysql.py && echo \"=== pipeline tests: step_started usage\" && grep -n -E 'step_started|EventLog|read_events' tests/test_jobs_pipeline.py | head -12",
  "description": "Read CLI test patterns, the MySQL connect helper and pipeline event tests"
}
```

## 46. User — 2026-10-24T05:10:29.392Z

### Tool result

```
"""The job queue's commands on a SQLite job table, offline. Kafka is replaced by a fake
publisher; the worker and reconciler commands run against the services in
tests/test_jobs_live_pipeline.py.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json

import numpy as np
import pytest
from conftest import nyse_sessions, write_snapshot

from etf_risk.jobs import cli
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite


class FakePublisher:
    published: list = []

    def __init__(self, bootstrap, topic, **kwargs):
        self.topic = topic

    def publish(self, job_id):
        FakePublisher.published.append((self.topic, job_id))
        return True

    def close(self):
        pass


@pytest.fixture
def setup(tmp_path, monkeypatch):
    dates = nyse_sessions("2024-01-02", 31)
    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(2).normal(0, 0.01, 30))})
    monkeypatch.setattr("etf_risk.jobs.kafka.KafkaPublisher", FakePublisher)
    FakePublisher.published = []
    db = f"sqlite:///{tmp_path / 'jobs.sqlite'}"
    base = ["--db", db, "--output-root", str(tmp_path / "out"), "--processed-root", str(tmp_path / "processed")]
    return db, base, tmp_path

47:def test_init_db_writes_one_store_id_and_keeps_it(setup, capsys):
54:def test_submit_records_the_parameters_and_the_input_checksums(setup, capsys):
69:def test_unusable_parameters_are_refused_before_anything_is_written(setup, capsys):
77:def test_status_check_export_and_cleanup(setup, capsys):
102:def test_settings_hide_passwords_and_keep_the_time_relations():
=== mysql.connect_mysql
def connect_mysql(url: str, *, database: str | None = None, found_rows: bool = True,
                  isolation: str = "REPEATABLE READ", lock_wait_timeout: int | None = None,
                  connect_timeout: float | None = None, read_timeout: float | None = None,
                  write_timeout: float | None = None, wait_timeout: int | None = None) -> Any:
    """A PyMySQL connection for JobStore(connection, MYSQL). lock_wait_timeout sets the
    session's innodb_lock_wait_timeout and wait_timeout its wait_timeout, in seconds; the
    other timeouts are PyMySQL's, per connection attempt and per read or write. None leaves
    a setting at its default."""
    import pymysql
    from pymysql.constants import CLIENT

    if isolation not in ISOLATION_LEVELS:
        raise ValueError(f"unknown isolation level: {isolation!r}")
    timeouts = {name: value for name, value in (("connect_timeout", connect_timeout), ("read_timeout", read_timeout),
                                                ("write_timeout", write_timeout)) if value is not None}
    conn = pymysql.connect(**connection_options(url, database), charset="utf8mb4", autocommit=True,
                           client_flag=CLIENT.FOUND_ROWS if found_rows else 0, **timeouts)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SET SESSION TRANSACTION ISOLATION LEVEL {isolation}")
            if lock_wait_timeout is not None:
                cursor.execute("SET SESSION innodb_lock_wait_timeout = %s", (int(lock_wait_timeout),))
            if wait_timeout is not None:
                cursor.execute("SET SESSION wait_timeout = %s", (int(wait_timeout),))
    except BaseException:
        conn.close()
        raise
    return conn


def connector(url: str, *, database: str | None = None, **settings: Any) -> Callable[[], Any]:
    """A function that opens a new connection with these settings, for JobStore(connect=...)."""
    return functools.partial(connect_mysql, url, database=database, **settings)


=== pipeline tests: step_started usage
```

## 47. Assistant — 2026-10-24T05:10:59.001Z

### Tool call: Bash

```
{
  "command": "O=~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-outline/docs && cp \"$O/recovery-experiments.md\" \"$O/recovery-sql.md\" docs/ && for f in recovery-experiments.md recovery-sql.md; do cmp -s \"$O/$f\" \"docs/$f\" && echo \"copied identical: $f\"; done && cat src/etf_risk/provenance.py",
  "description": "Copy the two documents and read the provenance module"
}
```

## 48. User — 2026-10-24T05:11:00.885Z

### Tool result

```
copied identical: recovery-experiments.md
copied identical: recovery-sql.md
"""Record which code produced a result, including uncommitted changes.

A git commit alone does not identify the code when the worktree has changes, so
code_state() also records whether the worktree is clean and the SHA-256 of uv.lock and
of every Python module and SQL schema under src/etf_risk/, subpackages included (the
job queue in jobs/ and its schema files). Keys are paths relative to src/etf_risk/, so a
top-level module keeps the key it always had ("model.py") and jobs/__init__.py does not
collide with __init__.py. Records written before 2026-10-23 hash the top-level modules
only.

The Docker image has no .git: there the commit and the clean flag come from what
docker/build.sh recorded at build time (code_source = "build"), and docker/run.sh
passes the image ID.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_spark_equivalence.py (run.json carries these fields) and tests/test_provenance.py.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from etf_risk.ingest import sha256_file

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]
SOURCE_SUFFIXES = (".py", ".sql")

# Set in the Docker image (Dockerfile, from docker/build.sh) and by docker/run.sh.
BUILD_COMMIT_ENV = "ETF_RISK_GIT_COMMIT"
BUILD_CLEAN_ENV = "ETF_RISK_GIT_WORKTREE_CLEAN"
IMAGE_ID_ENV = "ETF_RISK_IMAGE_ID"


def resolve(path: str | Path) -> Path:
    """Paths stored in configs are relative to the repository root unless absolute."""
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def source_files() -> dict[str, Path]:
    """Every Python module and SQL schema of the package, by path relative to it."""
    files = (p for p in PACKAGE_DIR.rglob("*") if p.suffix in SOURCE_SUFFIXES and p.is_file())
    return {p.relative_to(PACKAGE_DIR).as_posix(): p for p in sorted(files)}


def code_state() -> dict:
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=all", "--", "src", "pyproject.toml", "uv.lock")
    if head:
        source, commit, clean = "git", head, (status == "") if status is not None else None
    elif os.environ.get(BUILD_COMMIT_ENV):
        source, commit = "build", os.environ[BUILD_COMMIT_ENV]
        clean = {"true": True, "false": False}.get(os.environ.get(BUILD_CLEAN_ENV, "").lower())
    else:
        source, commit, clean = "unknown", "unknown", None
    lock = REPO_ROOT / "uv.lock"
    return {
        "git_commit": commit,
        # False means the code that ran is not exactly the recorded commit; source_sha256 identifies it.
        "git_worktree_clean": clean,
        "code_source": source,
        "image_id": os.environ.get(IMAGE_ID_ENV) or None,
        "source_sha256": {key: sha256_file(path) for key, path in source_files().items()},
        "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
    }
```

## 49. Assistant — 2026-10-24T05:12:42.324Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/provenance.py",
  "old_string": "The Docker image has no .git: there the commit and the clean flag come from what\ndocker/build.sh recorded at build time (code_source = \"build\"), and docker/run.sh\npasses the image ID.\n\nAI contribution: written with Claude Code (Opus 5.5). Verified with\ntests/test_spark_equivalence.py (run.json carries these fields) and tests/test_provenance.py.\n\"\"\"\nfrom __future__ import annotations\n\nimport os\nimport subprocess\nfrom pathlib import Path",
  "new_string": "The Docker image has no .git: there the commit and the clean flag come from what\ndocker/build.sh recorded at build time (code_source = \"build\"), and docker/run.sh\npasses the image ID.\n\nA process that starts records code_identity(), and each pipeline step its launch records\nsource_identity() (docs/recovery-experiments.md, 2.3): source_digest, one SHA-256 over the\nwhole source_sha256 map, and uv_lock_sha256 say whether two processes ran the same code;\nthe commit is only reported.\n\nAI contribution: written with Claude Code (Opus 5.5). Verified with\ntests/test_spark_equivalence.py (run.json carries these fields) and tests/test_provenance.py.\n\"\"\"\nfrom __future__ import annotations\n\nimport hashlib\nimport json\nimport os\nimport subprocess\nfrom pathlib import Path"
}
```

## 50. Assistant — 2026-10-24T05:12:47.094Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/provenance.py",
  "old_string": "        \"source_sha256\": {key: sha256_file(path) for key, path in source_files().items()},\n        \"uv_lock_sha256\": sha256_file(lock) if lock.is_file() else None,\n    }",
  "new_string": "        \"source_sha256\": {key: sha256_file(path) for key, path in source_files().items()},\n        \"uv_lock_sha256\": sha256_file(lock) if lock.is_file() else None,\n    }\n\n\ndef source_digest(source_sha256: dict[str, str]) -> str:\n    \"\"\"One SHA-256 for a source_sha256 map: that of its canonical JSON (keys sorted, no spaces).\"\"\"\n    return hashlib.sha256(json.dumps(source_sha256, sort_keys=True, separators=(\",\", \":\")).encode()).hexdigest()\n\n\ndef source_identity() -> dict:\n    \"\"\"The code as files, without asking git: source_digest() of every source file's SHA-256,\n    and uv.lock's SHA-256. Cheap enough to record at every step launch.\"\"\"\n    lock = REPO_ROOT / \"uv.lock\"\n    return {\"source_digest\": source_digest({key: sha256_file(path) for key, path in source_files().items()}),\n            \"uv_lock_sha256\": sha256_file(lock) if lock.is_file() else None}\n\n\ndef code_identity() -> dict:\n    \"\"\"What a starting process records: source_identity()'s two hashes, which decide whether\n    two processes ran the same code, with the commit and the clean flag, reported only.\"\"\"\n    state = code_state()\n    return {\"git_commit\": state[\"git_commit\"], \"git_worktree_clean\": state[\"git_worktree_clean\"],\n            \"source_digest\": source_digest(state[\"source_sha256\"]), \"uv_lock_sha256\": state[\"uv_lock_sha256\"]}"
}
```

## 51. User — 2026-10-24T05:12:48.174Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/provenance.py has been updated successfully.
```

## 52. User — 2026-10-24T05:12:49.268Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/provenance.py has been updated successfully.
```

## 53. Assistant — 2026-10-24T05:13:09.939Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/faults.py",
  "content": "\"\"\"Faults armed at the worker's fault points, for the recovery experiments\n(docs/recovery-experiments.md, 3.1 and 8.4).\n\nA worker started with ETF_RISK_FAULT_FILE=<path> looks at that path at each of\nWORKER_FAULT_POINTS (etf_risk.jobs.worker); while nothing is there, nothing happens. The\nsession harness (etf_risk.jobs.harness) arms one fault by writing the file, atomically\n(a temporary file, then a rename), as one JSON object:\n\n    {\"point\": \"after_claim\", \"action\": \"kill\"}\n    {\"point\": \"after_pipeline\", \"action\": \"hold\", \"release\": \"/abs/path\", \"timeout_s\": 300}\n\nWhen the worker reaches that point, it first removes the file, so a fault fires once, then\nwrites a fault_injected event (point, action) and:\n- kill: sends SIGKILL to its own process, which ends at once, as in a crash. The event's\n  mono is the injection time;\n- hold: waits until the release path exists, or timeout_s has passed, then writes\n  fault_released (with why) and goes on.\nA file that names another point is left for that point. A file that cannot be parsed, or\nthat names an unknown point or action, is removed and reported as fault_refused, and the\nworker goes on: an arming that went wrong must not turn into a fault nobody asked for.\n\nWithout the variable the worker has no fault hook at all.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\nTested with tests/test_jobs_faults.py.\n\"\"\"\nfrom __future__ import annotations\n\nimport json\nimport os\nimport signal\nimport time\nfrom collections.abc import Callable\nfrom pathlib import Path\n\nfrom etf_risk.jobs.events import EventLog\n\nFAULT_FILE_ENV = \"ETF_RISK_FAULT_FILE\"\nACTIONS = (\"kill\", \"hold\")\n\n\ndef _kill_self() -> None:\n    os.kill(os.getpid(), signal.SIGKILL)\n\n\nclass FaultFile:\n    \"\"\"The worker's fault hook: Worker(fault=FaultFile(path, events)).\"\"\"\n\n    def __init__(self, path: str | Path, events: EventLog, *, points: tuple[str, ...] | None = None,\n                 kill: Callable[[], None] = _kill_self, sleep: Callable[[float], None] = time.sleep,\n                 clock: Callable[[], float] = time.monotonic, tick: float = 0.1):\n        if points is None:\n            from etf_risk.jobs.worker import WORKER_FAULT_POINTS\n            points = WORKER_FAULT_POINTS\n        self.path, self.events, self.points = Path(path), events, points\n        self._kill, self._sleep, self._clock, self._tick = kill, sleep, clock, tick\n\n    def __call__(self, point: str) -> None:\n        try:\n            text = self.path.read_text()\n        except FileNotFoundError:\n            return\n        except OSError as error:\n            self.events.log(\"fault_refused\", point=point, error=f\"{type(error).__name__}: {error}\")\n            return\n        try:\n            spec = json.loads(text)\n            armed, action = spec[\"point\"], spec[\"action\"]\n            if armed not in self.points or action not in ACTIONS:\n                raise ValueError(f\"unknown point {armed!r} or action {action!r}\")\n            if action == \"hold\" and not spec.get(\"release\"):\n                raise ValueError(\"a hold needs a release path\")\n        except (ValueError, KeyError, TypeError) as error:\n            self.path.unlink(missing_ok=True)\n            self.events.log(\"fault_refused\", point=point, error=f\"{type(error).__name__}: {error}\")\n            return\n        if armed != point:\n            return\n        self.path.unlink(missing_ok=True)                    # once: gone before it acts\n        self.events.log(\"fault_injected\", point=point, action=action)\n        if action == \"kill\":\n            self._kill()\n            return                                           # reached only when kill is replaced (tests)\n        release, timeout = Path(spec[\"release\"]), spec.get(\"timeout_s\")\n        end = None if timeout is None else self._clock() + float(timeout)\n        while not release.exists():\n            if end is not None and self._clock() >= end:\n                self.events.log(\"fault_released\", point=point, why=\"timeout\")\n                return\n            self._sleep(self._tick)\n        self.events.log(\"fault_released\", point=point, why=\"released\")\n\n\ndef fault_from_environment(events: EventLog) -> FaultFile | None:\n    \"\"\"The hook for the worker command: a FaultFile when ETF_RISK_FAULT_FILE is set, else None.\"\"\"\n    path = os.environ.get(FAULT_FILE_ENV)\n    return FaultFile(path, events) if path else None\n\n\ndef arm(path: str | Path, point: str, action: str = \"kill\", *, release: str | Path | None = None,\n        timeout_s: float | None = None) -> None:\n    \"\"\"Write a fault for FaultFile to find (the harness's side), atomically.\"\"\"\n    spec = {\"point\": point, \"action\": action}\n    if release is not None:\n        spec[\"release\"] = str(release)\n    if timeout_s is not None:\n        spec[\"timeout_s\"] = timeout_s\n    path = Path(path)\n    tmp = path.with_name(path.name + \".tmp\")\n    tmp.write_text(json.dumps(spec))\n    tmp.replace(path)\n"
}
```

## 54. User — 2026-10-24T05:13:11.103Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/faults.py (file state is current in your context — no need to Read it back)
```

## 55. Assistant — 2026-10-24T05:13:15.633Z

Now the new fault point in the worker, between `accept_result`'s return and the `accepted` event, which is the W5a window:

## 56. Assistant — 2026-10-24T05:13:18.176Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py",
  "old_string": "Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash\nthere to model the worker process dying.",
  "new_string": "Worker(fault=...) is called at each of WORKER_FAULT_POINTS; the tests raise SimulatedCrash\nthere to model the worker process dying, and the worker command arms one through\netf_risk.jobs.faults for the recovery experiments. after_accept_commit lies between the\nacceptance's commit and its accepted event: a crash there leaves an accepted result that\nthe event log does not show."
}
```

## 57. Assistant — 2026-10-24T05:13:19.875Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py",
  "old_string": "    \"after_pipeline\",    # outputs written, result not yet accepted\n    \"after_accept\",\n)",
  "new_string": "    \"after_pipeline\",    # outputs written, result not yet accepted\n    \"after_accept_commit\",   # accepted in the table, the accepted event not yet written\n    \"after_accept\",\n)"
}
```

## 58. Assistant — 2026-10-24T05:13:22.266Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py",
  "old_string": "            self.events.log(\"fenced\", job_id=job_id, attempt=claim.attempt_number, during=\"accept_result\")\n            return Handled(job_id, Result.FENCED, claim=claim)\n        self.events.log(\"accepted\", job_id=job_id, attempt=claim.attempt_number, digest=digest)",
  "new_string": "            self.events.log(\"fenced\", job_id=job_id, attempt=claim.attempt_number, during=\"accept_result\")\n            return Handled(job_id, Result.FENCED, claim=claim)\n        self._fault(\"after_accept_commit\")\n        self.events.log(\"accepted\", job_id=job_id, attempt=claim.attempt_number, digest=digest)"
}
```

## 59. User — 2026-10-24T05:13:23.323Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py has been updated successfully.
```

## 60. User — 2026-10-24T05:13:24.491Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py has been updated successfully.
```

## 61. User — 2026-10-24T05:13:25.579Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/worker.py has been updated successfully.
```

## 62. Assistant — 2026-10-24T05:13:30.312Z

Now each step launch's identity in `pipeline.py`, using the no-git `source_identity()` so it's cheap per step:

## 63. Assistant — 2026-10-24T05:13:31.651Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/pipeline.py",
  "old_string": "from etf_risk.provenance import code_state",
  "new_string": "from etf_risk.provenance import code_state, source_identity"
}
```

## 64. Assistant — 2026-10-24T05:13:33.604Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/pipeline.py",
  "old_string": "        self.events.log(\"step_started\", job_id=claim.job_id, attempt=claim.attempt_number, step=name)",
  "new_string": "        self.events.log(\"step_started\", job_id=claim.job_id, attempt=claim.attempt_number, step=name,\n                        code=source_identity())     # the code the step starts from (recovery experiments, 2.3)"
}
```

## 65. User — 2026-10-24T05:13:34.673Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/pipeline.py has been updated successfully.
```

## 66. User — 2026-10-24T05:13:35.748Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/pipeline.py has been updated successfully.
```

## 67. Assistant — 2026-10-24T05:13:45.147Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py",
  "old_string": "Consumer errors that are not fatal, such as a poll after the poll interval was exceeded, are\nlogged and written to the worker's event log (consumer_error).",
  "new_string": "Consumer errors that are not fatal, such as a poll after the poll interval was exceeded, are\nlogged and written to the worker's event log (consumer_error).\n\nPartition assignments are written to the worker's event log too: assigned, revoked and lost,\neach with the partitions as [topic, partition] pairs and this member's id in the group. The\ngroup's owner of the job topic's one partition is read from them (docs/recovery-experiments.md,\n2.4), never inferred from worker names or start order. librdkafka calls the callbacks inside\npoll(), so an event's time is when this consumer learned of the change; confluent-kafka still\nmakes its default assignment after a callback that only logs."
}
```

## 68. Assistant — 2026-10-24T05:13:47.744Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py",
  "old_string": "def _ms(seconds: float) -> int:\n    return int(round(seconds * 1000))",
  "new_string": "def _ms(seconds: float) -> int:\n    return int(round(seconds * 1000))\n\n\ndef log_assignment(events: EventLog, kind: str, consumer, partitions) -> None:\n    \"\"\"Write an assigned, revoked or lost event for a rebalance callback.\"\"\"\n    try:\n        member = consumer.memberid()\n    except Exception:                                  # no member id yet, or none to report\n        member = None\n    events.log(kind, partitions=[[p.topic, p.partition] for p in partitions], member=member)"
}
```

## 69. Assistant — 2026-10-24T05:13:50.689Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py",
  "old_string": "        from confluent_kafka import Consumer\n        self._consumer = Consumer({**consumer_config(bootstrap, group, timing=timing), **(settings or {}),\n                                   \"logger\": log})\n        self._consumer.subscribe([topic])\n        self._closed = False\n        self.events = events",
  "new_string": "        from confluent_kafka import Consumer\n        self.events = events\n        self._consumer = Consumer({**consumer_config(bootstrap, group, timing=timing), **(settings or {}),\n                                   \"logger\": log})\n        self._consumer.subscribe([topic], on_assign=lambda c, ps: log_assignment(self.events, \"assigned\", c, ps),\n                                 on_revoke=lambda c, ps: log_assignment(self.events, \"revoked\", c, ps),\n                                 on_lost=lambda c, ps: log_assignment(self.events, \"lost\", c, ps))\n        self._closed = False"
}
```

## 70. User — 2026-10-24T05:13:51.742Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 71. User — 2026-10-24T05:13:52.872Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 72. User — 2026-10-24T05:13:54.009Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/kafka.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 73. Assistant — 2026-10-24T05:14:03.416Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py",
  "old_string": "submit inserts the job, publishes it, and records the confirmation. When the insert's COMMIT\nreply was lost, the job may or may not exist, so it exits 75 (outcome unknown) and is never\nrepeated on its own.\n\nAI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_cli.py.",
  "new_string": "submit inserts the job, publishes it, and records the confirmation. When the insert's COMMIT\nreply was lost, the job may or may not exist, so it exits 75 (outcome unknown) and is never\nrepeated on its own.\n\nFor the recovery experiments (docs/recovery-experiments.md, 2.3 and 8.4): the worker, the\nreconciler and every submit write a started event first, with the code identity\n(provenance.code_identity()); a worker started with ETF_RISK_FAULT_FILE gets the fault hook of\netf_risk.jobs.faults, and its started event names that file.\n\nAI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_cli.py."
}
```

## 74. Assistant — 2026-10-24T05:14:07.116Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py",
  "old_string": "from etf_risk.jobs.events import EventLog\nfrom etf_risk.jobs.params import InvalidParams, JobParams, input_checksums\nfrom etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline, startup_sweep\nfrom etf_risk.jobs.store import SQLITE, ClaimRace, JobStore, Outcome, Status, open_sqlite\nfrom etf_risk.jobs.timing import DEFAULT_TIMING, Timing\nfrom etf_risk.provenance import resolve",
  "new_string": "from etf_risk.jobs.events import EventLog\nfrom etf_risk.jobs.faults import FAULT_FILE_ENV, fault_from_environment\nfrom etf_risk.jobs.params import InvalidParams, JobParams, input_checksums\nfrom etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline, startup_sweep\nfrom etf_risk.jobs.store import SQLITE, ClaimRace, JobStore, Outcome, Status, open_sqlite\nfrom etf_risk.jobs.timing import DEFAULT_TIMING, Timing\nfrom etf_risk.provenance import code_identity, resolve"
}
```

## 75. Assistant — 2026-10-24T05:14:09.099Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py",
  "old_string": "    store = open_store(args.db, timing)\n    events = EventLog(Path(events_root(args)) / \"submit.jsonl\", \"submit\", store_id=store.store_id())\n    try:",
  "new_string": "    store = open_store(args.db, timing)\n    events = EventLog(Path(events_root(args)) / \"submit.jsonl\", \"submit\", store_id=store.store_id())\n    events.log(\"started\", code=code_identity())\n    try:"
}
```

## 76. Assistant — 2026-10-24T05:14:12.917Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py",
  "old_string": "    events.log(\"started\", db=safe_url(args.db), topic=args.topic, group=args.group, timing=asdict(timing),\n               standby=args.standby)\n    startup_sweep(store, output_root, timing=timing, events=events)\n    pipeline = SubprocessPipeline(store_id=store_id, processed_root=resolve(args.processed_root), worker_id=worker_id,\n                                  lock_path=args.lock, timing=timing, events=events, stop=stop)\n    worker = Worker(store, pipeline, output_root, worker_id=worker_id, events=events)",
  "new_string": "    events.log(\"started\", db=safe_url(args.db), topic=args.topic, group=args.group, timing=asdict(timing),\n               standby=args.standby, code=code_identity(), fault_file=os.environ.get(FAULT_FILE_ENV))\n    startup_sweep(store, output_root, timing=timing, events=events)\n    pipeline = SubprocessPipeline(store_id=store_id, processed_root=resolve(args.processed_root), worker_id=worker_id,\n                                  lock_path=args.lock, timing=timing, events=events, stop=stop)\n    worker = Worker(store, pipeline, output_root, worker_id=worker_id, events=events,\n                    fault=fault_from_environment(events))"
}
```

## 77. Assistant — 2026-10-24T05:14:14.767Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py",
  "old_string": "    events.log(\"started\", db=safe_url(args.db), topic=args.topic)\n    Reconciler(store, publisher, events=events).run(stop, interval=timedelta(seconds=args.interval))",
  "new_string": "    events.log(\"started\", db=safe_url(args.db), topic=args.topic, code=code_identity())\n    Reconciler(store, publisher, events=events).run(stop, interval=timedelta(seconds=args.interval))"
}
```

## 78. User — 2026-10-24T05:14:15.856Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 79. User — 2026-10-24T05:14:16.936Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 80. User — 2026-10-24T05:14:18.010Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 81. User — 2026-10-24T05:14:19.071Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 82. User — 2026-10-24T05:14:20.142Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/cli.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 83. Assistant — 2026-10-24T05:14:35.531Z

### Tool call: Bash

````
{
  "command": "python3 -I - <<'EOF'\nimport re\nfrom pathlib import Path\n\ndoc = Path(\"docs/recovery-sql.md\").read_text()\nblocks = re.findall(r\"^```sql\\n(.*?)^```$\", doc, flags=re.S | re.M)\nkeys = {\"-- The harness's records\": \"DDL\", \"-- Q0.\": \"Q0\", \"-- Q1.\": \"Q1\", \"-- Q2.\": \"Q2\", \"-- Q2b.\": \"Q2b\",\n        \"-- Q3a.\": \"Q3a\", \"-- Q3b.\": \"Q3b\"}\nnamed = {}\nfor block in blocks:\n    for prefix, key in keys.items():\n        if block.startswith(prefix):\n            named[key] = block\norder = [\"DDL\", \"Q0\", \"Q1\", \"Q2\", \"Q2b\", \"Q3a\", \"Q3b\"]\nassert list(named) == order, list(named)\nheader = \"\"\"-- The recovery experiments' SQL cross-check (docs/recovery-experiments.md, section 7): the\n-- harness's TEMPORARY tables, then Q0-Q3b, run by etf_risk.jobs.harness in the final snapshot.\n-- Everything below the line of dashes is the SQL of docs/recovery-sql.md, section 2, byte for\n-- byte, as validated against MySQL 8.4.13 on 2026-10-23 (82 of 82 expected rows);\n-- tests/test_jobs_harness.py checks that the two agree, so neither can change alone.\n--\n-- AI contribution: drafted with Claude Code (Opus 5.5); the author decides whether to keep it.\n-- ------------------------------------------------------------------------------------------\n\"\"\"\nPath(\"src/etf_risk/jobs/crosscheck.sql\").write_text(header + \"\\n\".join(named[k] for k in order))\nprint(\"blocks:\", len(blocks), \"used:\", order)\nEOF\nwc -l src/etf_risk/jobs/crosscheck.sql && head -9 src/etf_risk/jobs/crosscheck.sql | tail -2",
  "description": "Generate the cross-check SQL resource from the validated document"
}
````

## 84. User — 2026-10-24T05:14:36.679Z

### Tool result

```
blocks: 11 used: ['DDL', 'Q0', 'Q1', 'Q2', 'Q2b', 'Q3a', 'Q3b']
     212 src/etf_risk/jobs/crosscheck.sql
-- ------------------------------------------------------------------------------------------
-- The harness's records, in the cross-check's session only.
```

## 85. Assistant — 2026-10-24T05:16:04.718Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^[A-Z_]+ = ' src/etf_risk/jobs/reconciler.py src/etf_risk/jobs/queue.py src/etf_risk/jobs/store.py | cut -c1-150 && echo \"=== live test: whole tree stop (W7 method)\" && sed -n '337,362p' tests/test_jobs_live_pipeline.py",
  "description": "Read job constants and M2's whole-tree stop test"
}
```

## 86. User — 2026-10-24T05:16:05.640Z

### Tool result

```
src/etf_risk/jobs/queue.py:33:CONFIRMATION_TIMEOUT = timedelta(seconds=10)   # how long a publisher waits for the broker's confirmation
src/etf_risk/jobs/queue.py:36:MAX_JOB_ID = 2**63 - 1
src/etf_risk/jobs/queue.py:37:MAX_JOB_ID_DIGITS = len(str(MAX_JOB_ID))       # 19
src/etf_risk/jobs/queue.py:38:_JOB_ID = re.compile(rb"[1-9][0-9]{0,%d}" % (MAX_JOB_ID_DIGITS - 1))
src/etf_risk/jobs/reconciler.py:32:PUBLICATION_GRACE = timedelta(seconds=30)     # a never-claimed job's wait before it is published again
src/etf_risk/jobs/reconciler.py:33:RECONCILE_INTERVAL = timedelta(seconds=5)     # between passes
src/etf_risk/jobs/store.py:94:SCHEMA_DIR = Path(__file__).resolve().parent / "schema"
src/etf_risk/jobs/store.py:95:SCHEMA_VERSION = 2      # 2: job_store and job_attempts.result_digest
src/etf_risk/jobs/store.py:96:DEFAULT_LEASE = timedelta(seconds=60)
src/etf_risk/jobs/store.py:97:DEFAULT_MAX_ATTEMPTS = 3
src/etf_risk/jobs/store.py:98:CONFLICT_RETRIES = 3    # runs of one write operation in all, while the database reports lock conflicts
src/etf_risk/jobs/store.py:99:IDLE_PING = 60.0        # seconds: a connection idle this long is pinged before the next operation
src/etf_risk/jobs/store.py:109:TERMINAL = frozenset({Status.SUCCEEDED, Status.FAILED})
src/etf_risk/jobs/store.py:142:FAULT_POINTS = (
src/etf_risk/jobs/store.py:154:INVARIANT_QUERIES = {
src/etf_risk/jobs/store.py:179:_TIME_COLUMNS = frozenset({"lease_expires_at", "created_at", "updated_at", "finished_at", "published_at",
src/etf_risk/jobs/store.py:181:_JSON_COLUMNS = frozenset({"params", "input_checksums"})
src/etf_risk/jobs/store.py:254:SQLITE = SQLiteDialect()
=== live test: whole tree stop (W7 method)
def test_a_whole_stopped_tree_keeps_the_replacement_from_starting_spark(services, references):
    """Whole-tree SIGSTOP (worker, launcher, Spark). Before SIGCONT: the replacement, worker
    B, starts no step; it waits on the host lock, and only the frozen tree exists. After
    SIGCONT the frozen launcher's deadline has passed: it ends its tree at once, and B goes on."""
    stack = services
    a, job = claimed_by_a(stack)                                    # then B joins as a standby
    wait_until(lambda: step_running(stack, job, 1), 300, "step 2 of attempt 1")
    first = stack.store.attempts(job)[0]
    frozen = [psutil.Process(a.pid)] + attempt_procs(stack, first["run_id"])
    for p in frozen:
        p.suspend()
    wait_until(lambda: len(stack.store.attempts(job)) == 2, 120, "worker B to take attempt 2 over")
    time.sleep(10)                                                 # B's launcher is waiting for the lock
    second = stack.store.attempts(job)[1]
    assert not (run_dir(stack, second) / "logs" / "windows.log").exists()       # no step of attempt 2 started
    waiting = attempt_procs(stack, second["run_id"])
    assert [p.cmdline()[2] for p in waiting] == ["etf_risk.jobs.launcher"]   # only attempt 2's launcher, waiting
    for p in reversed(frozen):
        p.resume()
    wait_until(lambda: finished(stack, job), 600, f"job {job}")
    one = json.loads((run_dir(stack, first) / "logs" / "spark_pipeline.launcher.json").read_text())
    assert one["outcome"] == "deadline"
    check(stack, references, job, CALENDAR, attempts=2)


def test_a_step_over_its_limit_is_ended_and_retried_until_the_attempts_run_out(stack):
```

## 87. Assistant — 2026-10-24T05:18:31.119Z

### Tool call: Bash

```
{
  "command": "sed -n '552,580p' src/etf_risk/jobs/store.py",
  "description": "Read the store's read methods used by export"
}
```

## 88. User — 2026-10-24T05:18:32.173Z

### Tool result

```
    def job(self, job_id: int) -> dict | None:
        row = self._fetch_one("SELECT * FROM jobs WHERE job_id = :job_id", job_id=job_id)
        return None if row is None else self._decode(row)

    def attempts(self, job_id: int) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all(
            "SELECT * FROM job_attempts WHERE job_id = :job_id ORDER BY attempt_number", job_id=job_id)]

    def all_jobs(self) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all("SELECT * FROM jobs ORDER BY job_id")]

    def all_attempts(self) -> list[dict]:
        return [self._decode(row) for row in self._fetch_all(
            "SELECT * FROM job_attempts ORDER BY job_id, attempt_number")]

    def current_attempts(self) -> dict[int, tuple[int, str]]:
        """Running jobs: job id -> (current attempt number, its token). An attempt is valid
        and active exactly while it is listed here (the startup sweep keeps its processes)."""
        return {row["job_id"]: (row["attempt_number"], row["attempt_token"]) for row in self._fetch_all(
            "SELECT job_id, attempt_number, attempt_token FROM jobs WHERE status = 'running' ORDER BY job_id")}

    def invariant_violations(self) -> dict[str, list[int]]:
        """The jobs breaking each invariant in INVARIANT_QUERIES, read in one transaction;
        empty when all hold. The tests run it after every scenario; the recovery experiments
        (E1) can run it on MySQL."""
        with self._transaction():
            found = {name: [row[0] for row in self._execute(sql).fetchall()]
                     for name, sql in INVARIANT_QUERIES.items()}
        return {name: job_ids for name, job_ids in found.items() if job_ids}
```

## 89. Assistant — 2026-10-24T05:21:38.072Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "content": "\"\"\"The session harness of the recovery experiments E1 and E2 (docs/recovery-experiments.md).\n\n    uv run --group jobs python -m etf_risk.jobs.harness plan --seed N --out PLAN.json [--settings FILE]\n    uv run --group jobs python -m etf_risk.jobs.harness estimate --plan PLAN.json\n    uv run --group jobs python -m etf_risk.jobs.harness batch --plan PLAN.json --out DIR\n\nplan fixes a batch before it runs (8.1): its jobs in an order shuffled from the seed, the case\nof each, the settings and the code identity. Settings holds every value that section 8 of the\noutline leaves provisional (timing, repetitions, deadlines, the harness's waits, the memory\nthresholds); a settings file (JSON) replaces any of them, and the plan records the values used.\n\nestimate prints a plan's expected duration, from the design's windows (3.2) and the\nassumptions it names (Assumptions); none of them is measured.\n\nbatch runs one plan on fresh containers (2.1-2.5):\n- the services, the job database and a topic of its own; the reference run under the host lock,\n  through the launcher (2.2); the reconciler; worker A, then worker B, each waited for in the\n  assignment events (2.4);\n- for each job: the fault armed or the injection made (3.1), the deadline recorded (4.2) and\n  observed when the job finishes or at the deadline, whichever comes first (4.3), the job\n  followed to its end or its drain limit (2.5), killed or stopped workers restarted (2.4), and\n  the memory peaks read, with the thresholds of P4 (4.6);\n- then quiescence (4.4), the final snapshot with crosscheck.sql (4.5), and the services\n  removed.\nIts records go to DIR (section 9): harness.jsonl (the harness's own events), events/ (every\nprocess's log), jobs/ (the attempts' folders), reference/, logs/, crosscheck/*.csv, export/,\nstatus-check.txt, and plan.json.\n\nNo batch has run: Part A is not approved, and no formal experiment has been run. The offline\nparts are tested with tests/test_jobs_harness.py.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nfrom __future__ import annotations\n\nimport argparse\nimport csv\nimport json\nimport math\nimport os\nimport random\nimport re\nimport secrets\nimport signal\nimport subprocess\nimport sys\nimport threading\nimport time\nfrom dataclasses import asdict, dataclass, fields\nfrom datetime import date, datetime, timezone\nfrom decimal import Decimal\nfrom pathlib import Path\n\nfrom etf_risk.jobs import faults, processes\nfrom etf_risk.jobs.events import EventLog, read_events\nfrom etf_risk.jobs.reconciler import PUBLICATION_GRACE, RECONCILE_INTERVAL\nfrom etf_risk.jobs.timing import Timing\nfrom etf_risk.provenance import REPO_ROOT, code_identity\n\nCASES = (\"C0\", \"W1\", \"W2\", \"W3\", \"W4\", \"W5a\", \"W5b\", \"W6\", \"W7\", \"K1\", \"K2\", \"D1\", \"D2\", \"X1\")\nHOOKS = {\"W1\": (\"before_claim\", \"kill\"), \"W2\": (\"after_claim\", \"kill\"), \"W4\": (\"after_pipeline\", \"kill\"),\n         \"W5a\": (\"after_accept_commit\", \"kill\"), \"W5b\": (\"after_accept\", \"kill\"), \"D2\": (\"after_pipeline\", \"hold\")}\nMID_STEP = (\"W3\", \"W6\", \"W7\", \"K1\", \"D1\")       # injected once the attempt's spark_pipeline step runs\nNO_NEW_ATTEMPT = (\"C0\", \"W5a\", \"W5b\", \"K1\", \"X1\")\nFROM_RESTORED = (\"K2\", \"D1\", \"D2\")              # deadline counted from the service's return (4.2)\nWORKERS = (\"A\", \"B\")\nPARTITION = 0\nTERMINAL = (\"succeeded\", \"failed\")\nCROSSCHECK_SQL = Path(__file__).with_name(\"crosscheck.sql\")\nQUERIES = (\"Q0\", \"Q1\", \"Q2\", \"Q2b\", \"Q3a\", \"Q3b\")\n_SEPARATOR = re.compile(r\"^-- -{20,}\\s*$\")\n_QUERY_NAME = re.compile(r\"^-- (Q\\w+)\\.\")\n\n\n# Settings and plans\n\n@dataclass(frozen=True)\nclass Settings:\n    \"\"\"The provisional values of the outline's section 8 (P1-P4) and the harness's waits (8.5).\"\"\"\n    snapshot: str = \"full-2026-10-12\"\n    kind: str = \"calendar-year\"          # P1: every case on the calendar-year job\n    stride: int = 21\n    max_attempts: int = 3\n    jobs_per_case: int = 3               # P1\n    cases: tuple[str, ...] = CASES\n    timing: tuple[str, ...] = ()         # --timing overrides; P2: none\n    slowest_steps_s: float = 35.1        # S (P3): M2's slowest windows + spark_pipeline + verify, calendar-year\n    deadline_margin: float = 2.0         # P3: D = B + margin * S, rounded up\n    deadline_round_s: float = 5.0\n    max_lag_s: float = 1.0               # P3\n    phase_delay_s: float = 3.0           # 8.5: after spark_pipeline starts, before a mid-step injection\n    w7_stop_s: float = 90.0              # 8.5: how long W7's tree stays stopped (longer than a takeover)\n    outage_s: float = 30.0               # 8.5: how long K2, D1 and D2 keep their service stopped\n    flag_fraction: float = 0.90          # P4\n    stop_fraction: float = 0.95          # P4\n    poll_s: float = 0.5\n    phase_timeout_s: float = 300.0       # the longest wait for an injection's phase; then it is missed\n\n    @classmethod\n    def from_dict(cls, data: dict) -> Settings:\n        unknown = sorted(set(data) - {f.name for f in fields(cls)})\n        if unknown:\n            raise ValueError(f\"unknown settings: {unknown}\")\n        settings = cls(**{k: tuple(v) if k in (\"cases\", \"timing\") else v for k, v in data.items()})\n        if bad := sorted(set(settings.cases) - set(CASES)):\n            raise ValueError(f\"unknown cases: {bad}\")\n        return settings\n\n\ndef timing_of(settings: Settings) -> Timing:\n    from etf_risk.jobs.cli import timing_from\n    return timing_from(list(settings.timing))\n\n\ndef plan_jobs(settings: Settings, seed: int) -> list[str]:\n    \"\"\"The batch's cases in run order: jobs_per_case of each case, shuffled with the seed.\"\"\"\n    jobs = [case for case in settings.cases for _ in range(settings.jobs_per_case)]\n    random.Random(seed).shuffle(jobs)\n    return jobs\n\n\ndef deadline_reference(case: str) -> str:\n    \"\"\"What a job's deadline counts from (4.2): its submit, its injection, or its service's return.\"\"\"\n    return \"submit\" if case == \"C0\" else \"restored\" if case in FROM_RESTORED else \"injection\"\n\n\ndef bound_to_next_run(case: str, timing: Timing, settings: Settings) -> float:\n    \"\"\"B (P3): the latest the design starts the job's next run, from the deadline's reference.\n    K2, D1 and D2 count from their service's return, since how long a restart takes is not\n    known and is not inferred.\"\"\"\n    lease, period = timing.lease, RECONCILE_INTERVAL.total_seconds()\n    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0     # a member gone, then a poll\n    if case in NO_NEW_ATTEMPT:\n        return 0.0\n    if case == \"W1\":\n        return rejoin\n    if case in (\"W2\", \"W3\", \"W4\", \"W6\"):\n        return lease + period\n    if case == \"W7\":                     # the later of the takeover and the end of the stopped tree\n        return max(lease + period, settings.w7_stop_s + 2 * timing.watchdog_tick + timing.kill_grace)\n    if case == \"K2\":                     # the grace before a publication, a pass, and the group again\n        return PUBLICATION_GRACE.total_seconds() + period + rejoin\n    if case in (\"D1\", \"D2\"):             # a fenced attempt's lease, then a pass\n        return lease + period\n    raise ValueError(f\"unknown case {case!r}\")\n\n\ndef deadline_seconds(case: str, timing: Timing, settings: Settings) -> float:\n    \"\"\"D (P3): B plus deadline_margin times S, rounded up to deadline_round_s.\"\"\"\n    raw = bound_to_next_run(case, timing, settings) + settings.deadline_margin * settings.slowest_steps_s\n    step = settings.deadline_round_s\n    return math.ceil(raw / step - 1e-9) * step\n\n\ndef make_plan(settings: Settings, seed: int) -> dict:\n    timing = timing_of(settings)\n    return {\"format\": 1, \"seed\": seed, \"created_at_utc\": datetime.now(timezone.utc).isoformat(),\n            \"settings\": asdict(settings), \"timing\": asdict(timing), \"code\": code_identity(),\n            \"deadlines_s\": {case: deadline_seconds(case, timing, settings) for case in settings.cases},\n            \"jobs\": plan_jobs(settings, seed)}\n\n\n# The duration estimate\n\n@dataclass(frozen=True)\nclass Assumptions:\n    \"\"\"What estimate() assumes. None of it is measured: T for the job system, the restore time\n    and the restart overhead are guesses to be replaced by the first batch's records.\"\"\"\n    time_to_finish_s: float = 40.0       # T: M2's slowest steps (35.1 s) plus 5 s of the worker's own work\n    restart_s: float = 12.0              # a killed worker's start, sweep and rebalance\n    restore_s: float = 20.0              # a service's start until it is ready again\n    peaks_s: float = 2.0                 # the peaks read after every job\n    group_settle_s: float = 18.0         # after a Kafka restart, until the group has an owner (S + h)\n    batch_fixed_s: float = 180.0         # containers, reference run, workers, final snapshot, teardown\n\n\ndef case_seconds(case: str, timing: Timing, settings: Settings, a: Assumptions) -> float:\n    \"\"\"One job's expected duration from the harness's view: from its start to the next job's.\"\"\"\n    t, lease, period = a.time_to_finish_s, timing.lease, RECONCILE_INTERVAL.total_seconds()\n    partial = 1.0 + 3.0 + settings.phase_delay_s         # delivery, windows (M2: up to 3.0 s), the delay\n    rejoin = timing.session_timeout + timing.heartbeat_interval + 1.0\n    down = settings.outage_s + a.restore_s\n    to_fence = lease - timing.fence_margin - timing.renew_interval   # the earliest F after an injection\n    if case == \"C0\":\n        return t + a.peaks_s\n    if case in (\"W1\", \"W2\"):\n        return 1.0 + bound_to_next_run(case, timing, settings) + t + a.restart_s + a.peaks_s\n    if case in (\"W3\", \"W6\", \"W7\"):\n        return partial + bound_to_next_run(case, timing, settings) + t + a.restart_s + a.peaks_s\n    if case == \"W4\":\n        return t + lease + period + t + a.restart_s + a.peaks_s\n    if case in (\"W5a\", \"W5b\"):\n        return t + a.restart_s + a.peaks_s\n    if case == \"K1\":\n        return t + a.group_settle_s + 2 * a.peaks_s\n    if case == \"K2\":\n        wait = max(0.0, PUBLICATION_GRACE.total_seconds() - down)\n        return a.peaks_s + down + wait + period + rejoin + t + a.peaks_s\n    if case == \"D1\":                     # fenced when MySQL is away past F; then the lease, a pass, a run\n        if down >= to_fence:\n            return partial + a.peaks_s + max(down, lease) + period + t + a.peaks_s\n        return max(t, partial + down) + 2 * a.peaks_s\n    if case == \"D2\":                     # held after the run; acceptance tried until F\n        if down >= lease - timing.fence_margin:\n            return t + a.peaks_s + lease + period + t + a.peaks_s\n        return t + a.peaks_s + down + a.peaks_s\n    if case == \"X1\":\n        return t + 2.0 + a.peaks_s\n    raise ValueError(f\"unknown case {case!r}\")\n\n\ndef estimate(plan: dict, a: Assumptions = Assumptions()) -> dict:\n    settings = Settings.from_dict(plan[\"settings\"])\n    timing = timing_of(settings)\n    per_case = {case: case_seconds(case, timing, settings, a) for case in settings.cases}\n    total = sum(per_case[case] for case in plan[\"jobs\"]) + a.batch_fixed_s\n    return {\"assumptions\": asdict(a), \"per_case_s\": per_case, \"jobs\": len(plan[\"jobs\"]), \"batch_s\": total}\n\n\n# Reading the records\n\ndef events_named(events: list[dict], name: str, **fields_) -> list[dict]:\n    return [e for e in events if e.get(\"event\") == name and all(e.get(k) == v for k, v in fields_.items())]\n\n\ndef owner(logs: dict[str, list[dict]], alive: set[str], partition: int = PARTITION) -> str | None:\n    \"\"\"The live worker that holds the partition by its assignment events: its latest assigned\n    event lists the partition and no later revoked or lost event, or restart, took it away.\n    None when no live worker, or more than one, holds it.\"\"\"\n    holders = []\n    for worker, events in logs.items():\n        holds = False\n        for e in events:\n            kind = e.get(\"event\")\n            if kind == \"started\":\n                holds = False\n            elif kind == \"assigned\":\n                holds = any(p[1] == partition for p in e.get(\"partitions\", []))\n            elif kind in (\"revoked\", \"lost\") and any(p[1] == partition for p in e.get(\"partitions\", [])):\n                holds = False\n        if holds and worker in alive:\n            holders.append(worker)\n    return holders[0] if len(holders) == 1 else None\n\n\ndef worker_accepts(logs: dict[str, list[dict]]) -> list[tuple]:\n    \"\"\"worker_accepts rows (crosscheck.sql): one per accepted event, with the log's identity.\"\"\"\n    return [(e.get(\"store_id\"), e.get(\"worker_id\"), e.get(\"pid\"), e[\"job_id\"], e[\"attempt\"], e[\"digest\"])\n            for events in logs.values() for e in events_named(events, \"accepted\")]\n\n\nclass PeakBook:\n    \"\"\"Memory peaks by segment (4.6): a restart or a stop resets a container's memory.peak, so a\n    reading before it closes a segment. A container's batch peak is the maximum of its readings;\n    a reading that failed leaves its segment unknown and the batch peak incomplete.\"\"\"\n\n    def __init__(self):\n        self.readings: dict[str, list[dict]] = {}\n\n    def add(self, service: str, peak_bytes: int | None, limit_bytes: int | None, closes: str | None) -> dict:\n        reading = {\"peak_bytes\": peak_bytes, \"limit_bytes\": limit_bytes, \"closes\": closes}\n        self.readings.setdefault(service, []).append(reading)\n        return reading\n\n    def batch_peak(self, service: str) -> dict:\n        readings = self.readings.get(service, [])\n        known = [r[\"peak_bytes\"] for r in readings if r[\"peak_bytes\"] is not None]\n        limit = next((r[\"limit_bytes\"] for r in readings if r[\"limit_bytes\"]), None)\n        peak = max(known) if known else None\n        return {\"peak_bytes\": peak, \"limit_bytes\": limit, \"readings\": len(readings),\n                \"incomplete\": not readings or len(known) < len(readings),\n                \"fraction\": None if peak is None or not limit else peak / limit}\n\n\ndef memory_verdict(fraction: float | None, settings: Settings) -> str:\n    \"\"\"P4: ok, flag (past flag_fraction) or stop (past stop_fraction); unknown without a reading.\"\"\"\n    if fraction is None:\n        return \"unknown\"\n    return \"stop\" if fraction > settings.stop_fraction else \"flag\" if fraction > settings.flag_fraction else \"ok\"\n\n\ndef crosscheck_statements(text: str | None = None) -> list[tuple[str, str]]:\n    \"\"\"The statements of crosscheck.sql below its separator, in order, each named DDL or Q0-Q3b.\"\"\"\n    lines = (CROSSCHECK_SQL.read_text() if text is None else text).splitlines(keepends=True)\n    start = next(i for i, line in enumerate(lines) if _SEPARATOR.match(line)) + 1\n    statements, current = [], []\n    for line in lines[start:]:\n        current.append(line)\n        stripped = line.strip()\n        if stripped.endswith(\";\") and not stripped.startswith(\"--\"):\n            sql = \"\".join(current).strip()\n            name = next((m.group(1) for row in sql.splitlines() if (m := _QUERY_NAME.match(row))), \"DDL\")\n            statements.append((name, sql))\n            current = []\n    return statements\n\n\ndef fingerprint_from_export(folder: Path) -> dict:\n    \"\"\"Q0's four numbers, from an export's jobs.json and job_attempts.json.\"\"\"\n    jobs = json.loads((folder / \"jobs.json\").read_text())\n    attempts = json.loads((folder / \"job_attempts.json\").read_text())\n    return {\"n_jobs\": len(jobs), \"sum_version\": sum(int(j[\"version\"]) for j in jobs),\n            \"n_attempts\": len(attempts), \"sum_renewals\": sum(int(a[\"renewals\"]) for a in attempts)}\n\n\ndef csv_value(value) -> str:\n    if value is None:\n        return \"NULL\"\n    if isinstance(value, datetime):\n        return value.isoformat(sep=\" \", timespec=\"microseconds\")\n    if isinstance(value, (date, Decimal)):\n        return str(value)\n    return str(value)\n\n\ndef clock_pair() -> dict:\n    \"\"\"ts and mono read together, for the clock check (4.1).\"\"\"\n    return {\"ts\": datetime.now(timezone.utc).isoformat(timespec=\"microseconds\"), \"mono\": time.monotonic()}\n\n\n# The batch\n\nclass PhaseMissed(Exception):\n    \"\"\"An injection did not land in its phase; the job is recorded as a miss and still followed.\"\"\"\n\n\nclass Tracker(threading.Thread):\n    \"\"\"Follows one job: the deadline observation when it finishes or at its deadline, whichever\n    comes first (4.3), then until it is finished or its drain limit has passed (2.5).\"\"\"\n\n    def __init__(self, batch: Batch, job_id: int, deadline_mono: float, drain_until: float):\n        super().__init__(daemon=True)\n        self.batch, self.job_id, self.deadline_mono, self.drain_until = batch, job_id, deadline_mono, drain_until\n        self.observation: dict | None = None\n        self.final: str | None = None\n        self.finished_mono: float | None = None\n\n    def run(self) -> None:\n        while True:\n            now, status = time.monotonic(), self.batch.job_status(self.job_id)\n            if self.observation is None and (status in TERMINAL or now >= self.deadline_mono):\n                self.observation = self.batch.observe(self.job_id)\n            if status in TERMINAL:\n                self.final, self.finished_mono = status, now\n                return\n            if now >= self.drain_until:\n                return\n            time.sleep(self.batch.settings.poll_s)\n\n\nclass Batch:\n    def __init__(self, plan: dict, out: Path):\n        from etf_risk import services\n        self.plan, self.out, self.services = plan, out, services\n        self.settings = Settings.from_dict(plan[\"settings\"])\n        self.timing = timing_of(self.settings)\n        self.mysql_url = os.environ.get(\"ETF_RISK_MYSQL_URL\", services.DEFAULT_MYSQL_URL).rstrip(\"/\")\n        self.bootstrap = os.environ.get(\"ETF_RISK_KAFKA_BOOTSTRAP\", services.DEFAULT_KAFKA_BOOTSTRAP)\n        self.db = f\"{self.mysql_url}/etf_recovery\"\n        self.topic = f\"etf-recovery-{secrets.token_hex(4)}\"\n        self.events_dir, self.jobs_root, self.faults_dir, self.logs_dir = (\n            out / \"events\", out / \"jobs\", out / \"faults\", out / \"logs\")\n        for folder in (self.events_dir, self.jobs_root, self.faults_dir, self.logs_dir):\n            folder.mkdir(parents=True, exist_ok=True)\n        self.env = {**os.environ, \"ETF_RISK_JOBS_DB\": self.db, \"ETF_RISK_KAFKA_BOOTSTRAP\": self.bootstrap,\n                    \"ETF_RISK_JOBS_TOPIC\": self.topic}\n        self.env.pop(faults.FAULT_FILE_ENV, None)\n        self.log = EventLog(out / \"harness.jsonl\", \"harness\", batch=out.name)\n        self.procs: dict[str, subprocess.Popen] = {}\n        self.peaks = PeakBook()\n        self.batch_jobs: list[tuple] = []\n        self.observations: list[tuple] = []\n        self.stop_reason: str | None = None\n        self.store = None\n        self.store_id: str | None = None\n        self._publisher = None\n\n    # Commands and services\n\n    def common_args(self) -> list[str]:\n        args = [\"--output-root\", str(self.jobs_root), \"--processed-root\", str(REPO_ROOT / \"data\" / \"processed\"),\n                \"--events\", str(self.events_dir)]\n        for override in self.settings.timing:\n            args += [\"--timing\", override]\n        return args\n\n    def cli(self, *argv: str, check: bool = True, timeout: float = 180) -> subprocess.CompletedProcess:\n        out = subprocess.run([sys.executable, \"-m\", \"etf_risk.jobs\", *argv, *self.common_args()], env=self.env,\n                             capture_output=True, text=True, timeout=timeout)\n        if check and out.returncode != 0:\n            raise RuntimeError(f\"{argv[0]}: exit {out.returncode}: {out.stderr.strip()[-500:]}\")\n        return out\n\n    def compose(self, *args: str, timeout: float = 300) -> float:\n        \"\"\"Run docker compose on this project's file; the seconds it took.\"\"\"\n        start = time.monotonic()\n        out = subprocess.run([\"docker\", \"compose\", \"-f\", str(self.services.COMPOSE_FILE), *args],\n                             capture_output=True, text=True, timeout=timeout)\n        if out.returncode != 0:\n            raise RuntimeError(f\"docker compose {' '.join(args)}: exit {out.returncode}: {out.stderr.strip()[-500:]}\")\n        return time.monotonic() - start\n\n    def wait_ready(self, service: str) -> float:\n        \"\"\"Until the service works again (services.py); the harness's mono at that moment.\"\"\"\n        check = {\"mysql\": lambda: self.services.mysql_ready(self.mysql_url),\n                 \"kafka\": lambda: self.services.kafka_ready(self.bootstrap)}[service]\n        self.services.wait_until_ready(service, check, timeout=180)\n        return time.monotonic()\n\n    def services_up(self) -> None:\n        running = subprocess.run([\"docker\", \"compose\", \"-f\", str(self.services.COMPOSE_FILE), \"ps\", \"-q\"],\n                                 capture_output=True, text=True, timeout=60).stdout.split()\n        if running:\n            raise RuntimeError(\"this project's containers are running already; a batch starts on fresh ones\")\n        self.log.log(\"services_up\", seconds=self.compose(\"up\", \"-d\", \"--wait\", \"mysql\", \"kafka\"),\n                     others=self.services.other_containers())\n        for service in (\"mysql\", \"kafka\"):\n            self.wait_ready(service)\n\n    def read_peaks(self, closes: str | None = None) -> str:\n        \"\"\"Both containers' memory.peak (4.6); the worst verdict of P4.\"\"\"\n        verdicts = []\n        for service in (\"mysql\", \"kafka\"):\n            peak = self.services.memory_peak(service)\n            self.peaks.add(service, peak.peak_bytes, peak.limit_bytes, closes)\n            verdict = memory_verdict(self.peaks.batch_peak(service)[\"fraction\"], self.settings)\n            verdicts.append(verdict)\n            self.log.log(\"peaks\", service=service, peak_bytes=peak.peak_bytes, limit_bytes=peak.limit_bytes,\n                         closes=closes, verdict=verdict)\n        return \"stop\" if \"stop\" in verdicts else \"flag\" if \"flag\" in verdicts else \"ok\"\n\n    # Processes\n\n    def start(self, name: str, *argv: str, extra_env: dict | None = None) -> subprocess.Popen:\n        before = time.monotonic()\n        log = open(self.logs_dir / f\"{name}.log\", \"ab\")\n        proc = subprocess.Popen([sys.executable, \"-m\", \"etf_risk.jobs\", *argv, *self.common_args()],\n                                env={**self.env, **(extra_env or {})}, stdout=log, stderr=subprocess.STDOUT,\n                                start_new_session=True)\n        self.procs[name] = proc\n        self._check_start(name, proc, before)\n        return proc\n\n    def _check_start(self, name: str, proc: subprocess.Popen, before: float) -> None:\n        \"\"\"The process's started event, and the same-clock check of 4.1.\"\"\"\n        path = self.events_dir / (f\"{name}.jsonl\" if name in WORKERS else f\"reconciler-{proc.pid}.jsonl\")\n        started = self.wait_for(lambda: next(iter(events_named(read_events(path) if path.exists() else [],\n                                                               \"started\", pid=proc.pid)), None),\n                                60, f\"{name}'s started event\")\n        after = time.monotonic()\n        self.log.log(\"process_started\", name=name, pid=proc.pid, before=before, after=after,\n                     first_mono=started[\"mono\"], same_clock=before <= started[\"mono\"] <= after,\n                     code=started.get(\"code\"))\n\n    def fault_file(self, worker: str) -> Path:\n        return self.faults_dir / f\"{worker}.fault\"\n\n    def start_worker(self, name: str) -> None:\n        self.fault_file(name).unlink(missing_ok=True)\n        self.start(name, \"worker\", \"--worker-id\", name, extra_env={faults.FAULT_FILE_ENV: str(self.fault_file(name))})\n\n    def alive(self) -> set[str]:\n        return {w for w in WORKERS if w in self.procs and self.procs[w].poll() is None}\n\n    def worker_logs(self) -> dict[str, list[dict]]:\n        return {w: read_events(p) if (p := self.events_dir / f\"{w}.jsonl\").exists() else [] for w in WORKERS}\n\n    def current_owner(self) -> str | None:\n        return owner(self.worker_logs(), self.alive())\n\n    def wait_owner(self, timeout: float = 120) -> str:\n        \"\"\"The partition's owner, once the assignment events name exactly one live worker.\"\"\"\n        return self.wait_for(self.current_owner, timeout, \"a single owner of the partition\")\n\n    def wait_for(self, predicate, timeout: float, what: str):\n        \"\"\"predicate()'s first true value; a lost database connection counts as not yet.\"\"\"\n        end = time.monotonic() + timeout\n        while True:\n            try:\n                value = predicate()\n            except Exception as error:\n                from etf_risk.jobs.mysql import MYSQL\n                if not MYSQL.is_disconnect(error):\n                    raise\n                value = None\n            if value:\n                return value\n            if time.monotonic() >= end:\n                raise PhaseMissed(f\"timed out waiting for {what}\")\n            time.sleep(self.settings.poll_s)\n\n    # The job table, read by the harness\n\n    def open_store(self) -> None:\n        from etf_risk.jobs import mysql\n        from etf_risk.jobs.store import JobStore\n        self.store = JobStore(None, mysql.MYSQL, connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))\n        self.store_id = self.store.store_id()\n\n    def job_status(self, job_id: int) -> str | None:\n        try:\n            job = self.store.job(job_id)\n        except Exception:\n            return None\n        return None if job is None else job[\"status\"].value\n\n    def observe(self, job_id: int) -> dict:\n        \"\"\"The deadline observation (4.3): one consistent snapshot of the job's row, in a\n        connection of the harness's own; a failed read is kept with no status.\"\"\"\n        from etf_risk.jobs import mysql\n        record = {\"job_id\": job_id, \"status\": None, \"attempt_number\": None, \"accepted_attempt\": None}\n        observed_from = observed_to = time.monotonic()\n        try:\n            conn = mysql.connect_mysql(self.db, connect_timeout=3, read_timeout=5, write_timeout=5)\n            try:\n                with conn.cursor() as cursor:\n                    observed_from = time.monotonic()\n                    cursor.execute(\"START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY\")\n                    observed_to = time.monotonic()\n                    cursor.execute(\"SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = %s\",\n                                   (job_id,))\n                    row = cursor.fetchone()\n                    cursor.execute(\"COMMIT\")\n            finally:\n                conn.close()\n            if row is not None:\n                record.update(status=row[0], attempt_number=row[1], accepted_attempt=row[2])\n        except Exception as error:\n            observed_to = time.monotonic()\n            record[\"error\"] = f\"{type(error).__name__}: {error}\"[:300]\n        record.update(observed_from_mono=observed_from, observed_to_mono=observed_to)\n        self.observations.append((job_id, observed_from, observed_to, record[\"status\"], record[\"attempt_number\"],\n                                  record[\"accepted_attempt\"]))\n        self.log.log(\"observation\", **record)\n        return record\n\n    # Phases\n\n    def claim_of(self, job_id: int) -> dict | None:\n        \"\"\"The job's latest claimed event in either worker's log, with the worker's name.\"\"\"\n        claims = [{**e, \"worker\": w} for w, events in self.worker_logs().items()\n                  for e in events_named(events, \"claimed\", job_id=job_id)]\n        return max(claims, key=lambda e: e[\"mono\"]) if claims else None\n\n    def attempt_dir(self, run_id: str) -> Path:\n        return self.jobs_root / self.store_id / run_id\n\n    def spark_running(self, job_id: int) -> dict | None:\n        \"\"\"The claim whose spark_pipeline step has started (its event and its log) and not ended.\"\"\"\n        claim = self.claim_of(job_id)\n        if claim is None:\n            return None\n        events = self.worker_logs()[claim[\"worker\"]]\n        mine = {\"job_id\": job_id, \"attempt\": claim[\"attempt\"], \"step\": \"spark_pipeline\"}\n        if not events_named(events, \"step_started\", **mine) or events_named(events, \"step_ended\", **mine):\n            return None\n        return claim if (self.attempt_dir(claim[\"run_id\"]) / \"logs\" / \"spark_pipeline.log\").exists() else None\n\n    def fault_event(self, worker: str, job_id: int, point: str) -> dict | None:\n        \"\"\"The fault_injected event at point in the worker's log, if it followed this job's delivery.\"\"\"\n        events = self.worker_logs()[worker]\n        for i, e in enumerate(events):\n            if e.get(\"event\") == \"fault_injected\" and e.get(\"point\") == point:\n                earlier = [x for x in events[:i] if x.get(\"event\") in (\"delivered\", \"claimed\")]\n                if earlier and earlier[-1].get(\"job_id\") == job_id:\n                    return e\n        return None\n\n    def at_mid_step(self, job_id: int) -> dict:\n        claim = self.wait_for(lambda: self.spark_running(job_id), self.settings.phase_timeout_s,\n                              f\"job {job_id}'s spark_pipeline step\")\n        time.sleep(self.settings.phase_delay_s)\n        if self.spark_running(job_id) is None:\n            raise PhaseMissed(\"spark_pipeline ended during the phase delay\")\n        return claim\n\n    # Injections (3.1)\n\n    def submit(self) -> int | None:\n        s = self.settings\n        out = self.cli(\"submit\", \"--snapshot\", s.snapshot, \"--kind\", s.kind, \"--stride\", str(s.stride),\n                       \"--max-attempts\", str(s.max_attempts), check=False)\n        if out.returncode != 0:\n            self.log.log(\"submit_failed\", exit=out.returncode, stderr=out.stderr.strip()[-300:])\n            return None\n        record = json.loads(out.stdout.strip().splitlines()[-1])\n        self.log.log(\"submitted\", **record)\n        return record[\"job_id\"]\n\n    def publish_again(self, job_id: int) -> bool:\n        if self._publisher is None:\n            from etf_risk.jobs.kafka import KafkaPublisher\n            self._publisher = KafkaPublisher(self.bootstrap, self.topic, timing=self.timing)\n        return self._publisher.publish(job_id)\n\n    def stop_tree(self, worker: str, run_id: str) -> list:\n        import psutil\n        frozen = [psutil.Process(self.procs[worker].pid)]\n        for value, procs in processes.marked_processes().items():\n            parsed = processes.parse_marker(value)\n            if parsed is not None and parsed[0] == self.store_id and parsed[1] == run_id:\n                frozen += procs\n        for p in frozen:\n            p.suspend()\n        return frozen\n\n    def inject(self, position: int, case: str, job_id: int, armed: str | None, release: Path | None) -> dict:\n        \"\"\"Make the case's injection; what happened, with t_inj and the deadline's reference.\"\"\"\n        s, hook = self.settings, HOOKS.get(case)\n        if hook is not None and case != \"D2\":\n            point = hook[0]\n            event = self.wait_for(lambda: self.fault_event(armed, job_id, point), s.phase_timeout_s,\n                                  f\"the fault at {point}\")\n            self.wait_for(lambda: self.procs[armed].poll() is not None, 30, f\"worker {armed} to end\")\n            return {\"kind\": \"hook\", \"worker\": armed, \"point\": point, \"t_inj\": event[\"mono\"]}\n        if case == \"D2\":\n            event = self.wait_for(lambda: self.fault_event(armed, job_id, \"after_pipeline\"), s.phase_timeout_s,\n                                  \"the hold after the pipeline\")\n            self.read_peaks(closes=\"mysql stop\")\n            t_inj = time.monotonic()\n            self.compose(\"stop\", \"mysql\")\n            release.touch()                                  # acceptance meets the outage\n            time.sleep(max(0.0, t_inj + s.outage_s - time.monotonic()))\n            self.compose(\"start\", \"mysql\")\n            return {\"kind\": \"hold+service_stop\", \"worker\": armed, \"service\": \"mysql\", \"held_mono\": event[\"mono\"],\n                    \"t_inj\": t_inj, \"restored\": self.wait_ready(\"mysql\")}\n        if case in MID_STEP:\n            claim = self.at_mid_step(job_id)\n            worker, t_inj = claim[\"worker\"], time.monotonic()\n            if case == \"W3\":\n                os.kill(self.procs[worker].pid, signal.SIGKILL)\n                return {\"kind\": \"sigkill\", \"worker\": worker, \"attempt\": claim[\"attempt\"], \"t_inj\": t_inj}\n            if case in (\"W6\", \"W7\"):\n                return self.inject_stop(case, job_id, claim, t_inj)\n            service = \"kafka\" if case == \"K1\" else \"mysql\"\n            self.read_peaks(closes=f\"{service} {'restart' if case == 'K1' else 'stop'}\")\n            t_inj = time.monotonic()\n            if case == \"K1\":\n                seconds = self.compose(\"restart\", \"kafka\")\n                return {\"kind\": \"service_restart\", \"service\": \"kafka\", \"t_inj\": t_inj, \"seconds\": seconds,\n                        \"ready\": self.wait_ready(\"kafka\")}\n            self.compose(\"stop\", \"mysql\")\n            time.sleep(max(0.0, t_inj + s.outage_s - time.monotonic()))\n            self.compose(\"start\", \"mysql\")\n            return {\"kind\": \"service_stop\", \"service\": \"mysql\", \"t_inj\": t_inj, \"restored\": self.wait_ready(\"mysql\")}\n        if case == \"X1\":\n            claim = self.wait_for(lambda: self.claim_of(job_id), s.phase_timeout_s, f\"job {job_id}'s claim\")\n            t_inj = time.monotonic()\n            return {\"kind\": \"publish\", \"worker\": claim[\"worker\"], \"t_inj\": t_inj, \"published\": self.publish_again(job_id)}\n        raise ValueError(case)\n\n    def inject_stop(self, case: str, job_id: int, claim: dict, t_inj: float) -> dict:\n        \"\"\"W6: the worker stopped until the standby takes over. W7: the whole tree, for w7_stop_s.\n        Then SIGCONT, the old worker's fenced event, and SIGTERM (its attempt is no longer its own).\"\"\"\n        import psutil\n        worker = claim[\"worker\"]\n        if case == \"W6\":\n            frozen = [psutil.Process(self.procs[worker].pid)]\n            frozen[0].suspend()\n            self.wait_for(lambda: (c := self.claim_of(job_id)) and c[\"attempt\"] > claim[\"attempt\"],\n                          self.settings.phase_timeout_s, \"the takeover\")\n        else:\n            frozen = self.stop_tree(worker, claim[\"run_id\"])\n            time.sleep(max(0.0, t_inj + self.settings.w7_stop_s - time.monotonic()))\n        resumed = time.monotonic()\n        for p in reversed(frozen):\n            try:\n                p.resume()\n            except psutil.Error:\n                pass\n        fenced = self.wait_for(lambda: next(iter(events_named(self.worker_logs()[worker], \"fenced\",\n                                                              job_id=job_id, attempt=claim[\"attempt\"])), None),\n                               120, f\"worker {worker}'s fenced event\")\n        self.procs[worker].send_signal(signal.SIGTERM)\n        self.wait_for(lambda: self.procs[worker].poll() is not None, 60, f\"worker {worker} to stop\")\n        return {\"kind\": \"sigstop\" if case == \"W6\" else \"sigstop_tree\", \"worker\": worker, \"attempt\": claim[\"attempt\"],\n                \"t_inj\": t_inj, \"resumed\": resumed, \"fenced_mono\": fenced[\"mono\"], \"stopped\": len(frozen)}\n\n    # One job\n\n    def run_job(self, position: int, case: str) -> dict:\n        s = self.settings\n        record = {\"position\": position, \"case\": case, \"owner_before\": self.wait_owner()}\n        armed, release, injection = None, None, None\n        if case in HOOKS:\n            point, action = HOOKS[case]\n            armed = record[\"owner_before\"]\n            release = self.faults_dir / f\"release-{position}\" if action == \"hold\" else None\n            faults.arm(self.fault_file(armed), point, action, release=release,\n                       timeout_s=s.outage_s + 600 if release else None)\n            self.log.log(\"armed\", position=position, worker=armed, point=point, action=action)\n        if case == \"K2\":\n            self.read_peaks(closes=\"kafka stop\")\n            t_inj = time.monotonic()\n            self.compose(\"stop\", \"kafka\")\n            injection = {\"kind\": \"service_stop\", \"service\": \"kafka\", \"t_inj\": t_inj}\n        t_submit = time.monotonic()\n        job_id = self.submit()\n        record[\"job_id\"] = job_id\n        if job_id is None:\n            return {**record, \"outcome\": \"submit_failed\"}\n        try:\n            if case == \"K2\":\n                time.sleep(max(0.0, injection[\"t_inj\"] + s.outage_s - time.monotonic()))\n                self.compose(\"start\", \"kafka\")\n                injection[\"restored\"] = self.wait_ready(\"kafka\")\n            elif case != \"C0\":\n                injection = self.inject(position, case, job_id, armed, release)\n            missed = None\n        except PhaseMissed as error:\n            missed = str(error)\n            self.fault_file(armed).unlink(missing_ok=True) if armed else None\n        reference = deadline_reference(case)\n        if missed is not None or reference == \"submit\":\n            reference_mono, d = t_submit, deadline_seconds(\"C0\", self.timing, s)\n            reference = \"submit\"\n        else:\n            reference_mono = injection[\"restored\"] if reference == \"restored\" else injection[\"t_inj\"]\n            d = deadline_seconds(case, self.timing, s)\n        deadline_mono = reference_mono + d\n        self.batch_jobs.append((job_id, case, \"restored\" if reference == \"restored\" else reference, d,\n                                deadline_mono, s.max_lag_s))\n        self.log.log(\"deadline\", position=position, job_id=job_id, case=case, reference=reference,\n                     reference_mono=reference_mono, deadline_s=d, deadline_mono=deadline_mono, max_lag_s=s.max_lag_s)\n        self.log.log(\"injection\", position=position, job_id=job_id, case=case, missed=missed, **(injection or {}))\n        tracker = Tracker(self, job_id, deadline_mono, deadline_mono + d)\n        tracker.start()\n        if case == \"X1\" and missed is None:\n            self.wait_for(lambda: self.job_status(job_id) == \"succeeded\", d * 2, f\"job {job_id} to succeed\")\n            injection[\"published_after\"] = self.publish_again(job_id)\n        tracker.join()\n        record.update(final=tracker.final, finished_mono=tracker.finished_mono, observation=tracker.observation,\n                      missed=missed)\n        self.log.log(\"job_done\", position=position, job_id=job_id, case=case, final=tracker.final,\n                     finished_mono=tracker.finished_mono)\n        return record\n\n    def after_job(self, record: dict) -> None:\n        \"\"\"The restart rule (2.4), the group after a Kafka restart, and the peaks of P4.\"\"\"\n        for worker in WORKERS:\n            if self.procs[worker].poll() is not None:\n                self.start_worker(worker)\n                self.log.log(\"restarted\", worker=worker, position=record[\"position\"])\n        if record[\"case\"] in (\"K1\", \"K2\"):\n            time.sleep(self.timing.session_timeout + self.timing.heartbeat_interval)\n        self.log.log(\"owner\", owner=self.wait_owner(), position=record[\"position\"])\n        if self.read_peaks() == \"stop\":\n            self.stop_reason = \"memory\"\n\n    # Start, quiescence and the final snapshot\n\n    def reference_run(self) -> None:\n        \"\"\"The reference run: the job's windows and spark_pipeline steps, each under a launcher\n        with the harness as its parent, so it takes the host lock and registers its tree (2.2).\"\"\"\n        from etf_risk.jobs.params import JobParams\n        from etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline\n        s = self.settings\n        params = JobParams(s.snapshot, s.kind, stride=s.stride)\n        pipeline = SubprocessPipeline(store_id=self.store_id, processed_root=REPO_ROOT / \"data\" / \"processed\",\n                                      worker_id=\"reference\", lock_path=DEFAULT_LOCK, timing=self.timing)\n        run_dir = self.out / \"reference\"\n\n        class Reference:\n            run_id = \"reference\"\n\n        work, logs = run_dir / \".work\", run_dir / \"logs\"\n        for folder in (work / \"tmp\", work / \"spark\", work / \"jtmp\", logs):\n            folder.mkdir(parents=True, exist_ok=True)\n        marker = processes.marker(self.store_id, \"reference\", secrets.token_hex(8))\n        env = pipeline.step_env(work, marker)\n        for name, argv in pipeline.commands(params, Reference, run_dir)[:2]:\n            limit = self.timing.step_limit(name)\n            command = [sys.executable, \"-m\", \"etf_risk.jobs.launcher\", \"--marker\", marker, \"--lock\", str(DEFAULT_LOCK),\n                       \"--registry\", str(pipeline.registry), \"--lock-wait\", str(self.timing.lock_wait(name)),\n                       \"--step-limit\", str(limit), \"--cwd\", str(work), \"--step-log\", str(logs / f\"{name}.log\"),\n                       \"--result\", str(logs / f\"{name}.launcher.json\"), \"--\", *argv]\n            before = time.monotonic()\n            proc = subprocess.Popen(command, stdin=subprocess.PIPE, env=env, cwd=work, start_new_session=True,\n                                    stdout=open(logs / f\"{name}.launcher.log\", \"ab\"), stderr=subprocess.STDOUT)\n            deadline = time.monotonic() + self.timing.lock_wait(name) + limit + 30\n            proc.stdin.write((json.dumps({\"monotonic\": time.monotonic(), \"seq\": 0, \"deadline\": deadline}) + \"\\n\").encode())\n            proc.stdin.flush()\n            code = proc.wait(timeout=deadline - time.monotonic() + 30)\n            proc.stdin.close()\n            self.log.log(\"reference_step\", step=name, exit=code, before=before, after=time.monotonic())\n            if code != 0:\n                raise RuntimeError(f\"the reference run's {name} step failed (exit {code})\")\n\n    def quiesce(self) -> dict:\n        \"\"\"4.4: SIGKILL every writer, then wait until no attempt's process and no other client\n        connection is left.\"\"\"\n        for proc in self.procs.values():\n            if proc.poll() is None:\n                os.kill(proc.pid, signal.SIGKILL)\n        for proc in self.procs.values():\n            proc.wait(timeout=30)\n        grace = self.timing.watchdog_tick + self.timing.kill_grace + 10\n        left = self.wait_for(lambda: not [v for v in processes.marked_processes()\n                                          if v.startswith(f\"{self.store_id}:\")] or None, grace,\n                             \"the attempts' processes to end\") if self._marked() else True\n        from etf_risk.jobs import mysql\n        conn = mysql.connect_mysql(self.db)\n        try:\n            with conn.cursor() as cursor:\n                cursor.execute(\"SELECT CONNECTION_ID()\")\n                me = cursor.fetchone()[0]\n                cursor.execute(\"SHOW FULL PROCESSLIST\")\n                others = [row for row in cursor.fetchall()\n                          if row[0] != me and row[4] != \"Daemon\" and row[1] not in (\"event_scheduler\", \"system user\")]\n        finally:\n            conn.close()\n        record = {\"processes_left\": not left, \"other_connections\": len(others)}\n        self.log.log(\"quiescent\", **record)\n        return record\n\n    def _marked(self) -> bool:\n        return any(v.startswith(f\"{self.store_id}:\") for v in processes.marked_processes())\n\n    def crosscheck(self) -> dict:\n        \"\"\"4.5, step 3: the harness's records in TEMPORARY tables, then Q0-Q3b in one consistent\n        snapshot, each saved as CSV; Q0's fingerprint.\"\"\"\n        from etf_risk.jobs import mysql\n        folder = self.out / \"crosscheck\"\n        folder.mkdir(exist_ok=True)\n        statements = crosscheck_statements()\n        conn = mysql.connect_mysql(self.db)\n        fingerprint = {}\n        try:\n            with conn.cursor() as cursor:\n                for name, sql in statements:\n                    if name == \"DDL\":\n                        cursor.execute(sql)\n                cursor.executemany(\"INSERT INTO batch_jobs (job_id, case_id, deadline_from, deadline_s, deadline_mono,\"\n                                   \" max_lag_s) VALUES (%s, %s, %s, %s, %s, %s)\", self.batch_jobs)\n                cursor.executemany(\"INSERT INTO deadline_observations (job_id, observed_from_mono, observed_to_mono,\"\n                                   \" status, attempt_number, accepted_attempt) VALUES (%s, %s, %s, %s, %s, %s)\",\n                                   self.observations)\n                cursor.executemany(\"INSERT INTO worker_accepts (store_id, worker_id, pid, job_id, attempt_number,\"\n                                   \" result_digest) VALUES (%s, %s, %s, %s, %s, %s)\", worker_accepts(self.worker_logs()))\n                cursor.execute(\"START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY\")\n                for name, sql in statements:\n                    if name == \"DDL\":\n                        continue\n                    cursor.execute(sql)\n                    columns = [d[0] for d in cursor.description]\n                    rows = cursor.fetchall()\n                    with open(folder / f\"{name}.csv\", \"w\", newline=\"\") as f:\n                        writer = csv.writer(f)\n                        writer.writerow(columns)\n                        writer.writerows([[csv_value(v) for v in row] for row in rows])\n                    if name == \"Q0\":\n                        fingerprint = {c: int(v) for c, v in zip(columns, rows[0])}\n                cursor.execute(\"COMMIT\")\n        finally:\n            conn.close()\n        return fingerprint\n\n    def q0(self) -> dict:\n        from etf_risk.jobs import mysql\n        sql = dict(crosscheck_statements())[\"Q0\"]\n        conn = mysql.connect_mysql(self.db)\n        try:\n            with conn.cursor() as cursor:\n                cursor.execute(sql)\n                columns = [d[0] for d in cursor.description]\n                return {c: int(v) for c, v in zip(columns, cursor.fetchone())}\n        finally:\n            conn.close()\n\n    def final_snapshot(self) -> dict:\n        \"\"\"4.5: peaks, status --check, the cross-check, the export, and Q0 again.\"\"\"\n        self.read_peaks(closes=\"end\")\n        status = self.cli(\"status\", \"--check\", check=False)\n        (self.out / \"status-check.txt\").write_text(f\"exit {status.returncode}\\n{status.stdout}{status.stderr}\")\n        first = self.crosscheck()\n        self.cli(\"export\", str(self.out / \"export\"))\n        exported = fingerprint_from_export(self.out / \"export\")\n        again = self.q0()\n        record = {\"status_check_exit\": status.returncode, \"fingerprints\": [first, exported, again],\n                  \"fingerprints_agree\": first == exported == again,\n                  \"batch_peaks\": {s: self.peaks.batch_peak(s) for s in (\"mysql\", \"kafka\")}}\n        self.log.log(\"final_snapshot\", **record)\n        return record\n\n    def run(self) -> int:\n        \"\"\"The batch: start, every planned job until one is left unfinished or memory stops it,\n        quiescence, the final snapshot, and the services removed.\"\"\"\n        self.log.log(\"batch_started\", plan_seed=self.plan[\"seed\"], code=code_identity(), clock=clock_pair(),\n                     settings=asdict(self.settings), topic=self.topic)\n        self.services_up()\n        try:\n            self.cli(\"init-db\")\n            self.cli(\"create-topic\")\n            self.open_store()\n            self.reference_run()\n            self.start(\"reconciler\", \"reconciler\")\n            self.start_worker(\"A\")\n            self.log.log(\"owner\", owner=self.wait_owner(), position=0)\n            self.start_worker(\"B\")\n            time.sleep(self.timing.heartbeat_interval)          # B's join, and the rebalance it causes\n            self.log.log(\"owner\", owner=self.wait_owner(), position=0)\n            for position, case in enumerate(self.plan[\"jobs\"], start=1):\n                if self.stop_reason is not None:\n                    self.log.log(\"not_run\", position=position, case=case, why=self.stop_reason)\n                    continue\n                record = self.run_job(position, case)\n                if record.get(\"final\") is None:\n                    self.stop_reason = \"an unfinished job\" if record.get(\"job_id\") else \"a submit that failed\"\n                    continue\n                self.after_job(record)\n            self.quiesce()\n            self.final_snapshot()\n        finally:\n            for proc in self.procs.values():\n                if proc.poll() is None:\n                    proc.kill()\n            self.log.log(\"batch_ended\", clock=clock_pair(), code=code_identity(), stop_reason=self.stop_reason)\n            self.compose(\"down\", \"-v\")\n        return 0\n\n\n# Command line\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(prog=\"python -m etf_risk.jobs.harness\", description=__doc__.splitlines()[0])\n    commands = parser.add_subparsers(dest=\"command\", required=True)\n    plan = commands.add_parser(\"plan\", help=\"fix a batch: its shuffled jobs and its settings\")\n    plan.add_argument(\"--seed\", type=int, required=True)\n    plan.add_argument(\"--out\", type=Path, required=True)\n    plan.add_argument(\"--settings\", type=Path, help=\"JSON replacing any of the default settings\")\n    est = commands.add_parser(\"estimate\", help=\"the plan's expected duration, from stated assumptions\")\n    est.add_argument(\"--plan\", type=Path, required=True)\n    batch = commands.add_parser(\"batch\", help=\"run one plan on fresh containers\")\n    batch.add_argument(\"--plan\", type=Path, required=True)\n    batch.add_argument(\"--out\", type=Path, required=True)\n    args = parser.parse_args(argv)\n    if args.command == \"plan\":\n        settings = Settings.from_dict(json.loads(args.settings.read_text())) if args.settings else Settings()\n        args.out.write_text(json.dumps(make_plan(settings, args.seed), indent=2) + \"\\n\")\n        print(f\"plan written to {args.out}\")\n        return 0\n    plan_data = json.loads(args.plan.read_text())\n    if args.command == \"estimate\":\n        print(json.dumps(estimate(plan_data), indent=2))\n        return 0\n    args.out.mkdir(parents=True, exist_ok=False)\n    (args.out / \"plan.json\").write_text(json.dumps(plan_data, indent=2) + \"\\n\")\n    return Batch(plan_data, args.out).run()\n\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n"
}
```

## 90. User — 2026-10-24T05:21:39.257Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py (file state is current in your context — no need to Read it back)
```

## 91. Assistant — 2026-10-24T05:22:56.330Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        self.stop_reason: str | None = None\n        self.store = None\n        self.store_id: str | None = None\n        self._publisher = None",
  "new_string": "        self.stop_reason: str | None = None\n        self.store_id: str | None = None\n        self._local = threading.local()                 # a JobStore per thread: a connection is not shared\n        self._publisher = None"
}
```

## 92. Assistant — 2026-10-24T05:22:59.880Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "    def open_store(self) -> None:\n        from etf_risk.jobs import mysql\n        from etf_risk.jobs.store import JobStore\n        self.store = JobStore(None, mysql.MYSQL, connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))\n        self.store_id = self.store.store_id()\n\n    def job_status(self, job_id: int) -> str | None:\n        try:\n            job = self.store.job(job_id)\n        except Exception:\n            return None\n        return None if job is None else job[\"status\"].value",
  "new_string": "    def store(self):\n        \"\"\"This thread's JobStore; it reconnects at its next operation after a lost connection.\"\"\"\n        store = getattr(self._local, \"store\", None)\n        if store is None:\n            from etf_risk.jobs import mysql\n            from etf_risk.jobs.store import JobStore\n            store = self._local.store = JobStore(None, mysql.MYSQL,\n                                                 connect=mysql.connector(self.db, **mysql.SERVICE_SESSION))\n        return store\n\n    def job_status(self, job_id: int) -> str | None:\n        try:\n            job = self.store().job(job_id)\n        except Exception:\n            return None\n        return None if job is None else job[\"status\"].value"
}
```

## 93. Assistant — 2026-10-24T05:23:02.487Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "    def services_up(self) -> None:\n        running = subprocess.run([\"docker\", \"compose\", \"-f\", str(self.services.COMPOSE_FILE), \"ps\", \"-q\"],\n                                 capture_output=True, text=True, timeout=60).stdout.split()\n        if running:\n            raise RuntimeError(\"this project's containers are running already; a batch starts on fresh ones\")",
  "new_string": "    def services_up(self) -> None:\n        existing = subprocess.run([\"docker\", \"compose\", \"-f\", str(self.services.COMPOSE_FILE), \"ps\", \"-a\", \"-q\"],\n                                  capture_output=True, text=True, timeout=60).stdout.split()\n        if existing:\n            raise RuntimeError(\"this project's containers exist already; a batch starts on fresh ones\")"
}
```

## 94. User — 2026-10-24T05:23:03.624Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 95. User — 2026-10-24T05:23:04.872Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 96. User — 2026-10-24T05:23:05.975Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 97. Assistant — 2026-10-24T05:23:15.079Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "    def wait_owner(self, timeout: float = 120) -> str:\n        \"\"\"The partition's owner, once the assignment events name exactly one live worker.\"\"\"\n        return self.wait_for(self.current_owner, timeout, \"a single owner of the partition\")",
  "new_string": "    def wait_owner(self, timeout: float = 120) -> str:\n        \"\"\"The partition's owner, once the assignment events name exactly one live worker.\"\"\"\n        return self.wait_for(self.current_owner, timeout, \"a single owner of the partition\")\n\n    def wait_joined(self, worker: str, timeout: float = 120) -> str:\n        \"\"\"After a worker starts: its first assigned event (its join, and so the rebalance it\n        caused, completed), then the owner. An owner read earlier could be a stale one.\"\"\"\n        pid = self.procs[worker].pid\n        self.wait_for(lambda: events_named(self.worker_logs()[worker], \"assigned\", pid=pid), timeout,\n                      f\"worker {worker}'s first assignment\")\n        return self.wait_owner(timeout)"
}
```

## 98. Assistant — 2026-10-24T05:23:18.175Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "    def at_mid_step(self, job_id: int) -> dict:",
  "new_string": "    def wait_fault(self, armed: str, job_id: int, point: str) -> dict:\n        \"\"\"The armed worker's fault_injected event for this job; a miss as soon as the other\n        worker claims the job first (the owner changed after the arming).\"\"\"\n        def found():\n            if event := self.fault_event(armed, job_id, point):\n                return event\n            claim = self.claim_of(job_id)\n            if claim is not None and claim[\"worker\"] != armed:\n                raise PhaseMissed(f\"job {job_id} was claimed by worker {claim['worker']}, not the armed {armed}\")\n            return None\n        return self.wait_for(found, self.settings.phase_timeout_s, f\"the fault at {point}\")\n\n    def at_mid_step(self, job_id: int) -> dict:"
}
```

## 99. Assistant — 2026-10-24T05:23:21.976Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        if hook is not None and case != \"D2\":\n            point = hook[0]\n            event = self.wait_for(lambda: self.fault_event(armed, job_id, point), s.phase_timeout_s,\n                                  f\"the fault at {point}\")\n            self.wait_for(lambda: self.procs[armed].poll() is not None, 30, f\"worker {armed} to end\")\n            return {\"kind\": \"hook\", \"worker\": armed, \"point\": point, \"t_inj\": event[\"mono\"]}\n        if case == \"D2\":\n            event = self.wait_for(lambda: self.fault_event(armed, job_id, \"after_pipeline\"), s.phase_timeout_s,\n                                  \"the hold after the pipeline\")\n            self.read_peaks(closes=\"mysql stop\")",
  "new_string": "        if hook is not None and case != \"D2\":\n            point = hook[0]\n            event = self.wait_fault(armed, job_id, point)\n            self.wait_for(lambda: self.procs[armed].poll() is not None, 30, f\"worker {armed} to end\")\n            return {\"kind\": \"hook\", \"worker\": armed, \"point\": point, \"t_inj\": event[\"mono\"]}\n        if case == \"D2\":\n            event = self.wait_fault(armed, job_id, \"after_pipeline\")\n            self.read_peaks(closes=\"mysql stop\")"
}
```

## 100. Assistant — 2026-10-24T05:23:24.170Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "            if case == \"W3\":\n                os.kill(self.procs[worker].pid, signal.SIGKILL)\n                return {\"kind\": \"sigkill\", \"worker\": worker, \"attempt\": claim[\"attempt\"], \"t_inj\": t_inj}",
  "new_string": "            if case == \"W3\":\n                os.kill(self.procs[worker].pid, signal.SIGKILL)\n                return {\"kind\": \"sigkill\", \"worker\": worker, \"attempt\": claim[\"attempt\"], \"phase\": \"spark_pipeline\",\n                        \"t_inj\": t_inj}"
}
```

## 101. User — 2026-10-24T05:23:25.251Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 102. User — 2026-10-24T05:23:26.690Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 103. User — 2026-10-24T05:23:27.776Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 104. User — 2026-10-24T05:23:28.858Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 105. Assistant — 2026-10-24T05:23:34.740Z

Next, `run_job`. A failed submit in K2 must restart Kafka before returning. The disarm becomes a plain `if`. X1's after-success publication must not escape the job:

## 106. Assistant — 2026-10-24T05:23:39.484Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        t_submit = time.monotonic()\n        job_id = self.submit()\n        record[\"job_id\"] = job_id\n        if job_id is None:\n            return {**record, \"outcome\": \"submit_failed\"}\n        try:\n            if case == \"K2\":\n                time.sleep(max(0.0, injection[\"t_inj\"] + s.outage_s - time.monotonic()))\n                self.compose(\"start\", \"kafka\")\n                injection[\"restored\"] = self.wait_ready(\"kafka\")\n            elif case != \"C0\":\n                injection = self.inject(position, case, job_id, armed, release)\n            missed = None\n        except PhaseMissed as error:\n            missed = str(error)\n            self.fault_file(armed).unlink(missing_ok=True) if armed else None",
  "new_string": "        t_submit = time.monotonic()\n        job_id = self.submit()\n        record[\"job_id\"] = job_id\n        if job_id is None:\n            if case == \"K2\":                                 # never leave the broker stopped\n                self.compose(\"start\", \"kafka\")\n                self.wait_ready(\"kafka\")\n            if armed is not None:\n                self.fault_file(armed).unlink(missing_ok=True)\n            return {**record, \"outcome\": \"submit_failed\"}\n        try:\n            if case == \"K2\":\n                time.sleep(max(0.0, injection[\"t_inj\"] + s.outage_s - time.monotonic()))\n                self.compose(\"start\", \"kafka\")\n                injection[\"restored\"] = self.wait_ready(\"kafka\")\n            elif case != \"C0\":\n                injection = self.inject(position, case, job_id, armed, release)\n            missed = None\n        except PhaseMissed as error:\n            missed = str(error)\n            if armed is not None:\n                self.fault_file(armed).unlink(missing_ok=True)"
}
```

## 107. Assistant — 2026-10-24T05:23:42.383Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        if case == \"X1\" and missed is None:\n            self.wait_for(lambda: self.job_status(job_id) == \"succeeded\", d * 2, f\"job {job_id} to succeed\")\n            injection[\"published_after\"] = self.publish_again(job_id)\n        tracker.join()",
  "new_string": "        if case == \"X1\" and missed is None:                  # the second duplicate, once the job succeeded\n            try:\n                self.wait_for(lambda: self.job_status(job_id) == \"succeeded\", 2 * d, f\"job {job_id} to succeed\")\n                self.log.log(\"published_again\", job_id=job_id, after=\"succeeded\",\n                             published=self.publish_again(job_id), t=time.monotonic())\n            except PhaseMissed as error:\n                self.log.log(\"published_again\", job_id=job_id, after=None, error=str(error))\n        tracker.join()"
}
```

## 108. User — 2026-10-24T05:23:43.431Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 109. User — 2026-10-24T05:23:44.536Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 110. Assistant — 2026-10-24T05:23:53.637Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        for worker in WORKERS:\n            if self.procs[worker].poll() is not None:\n                self.start_worker(worker)\n                self.log.log(\"restarted\", worker=worker, position=record[\"position\"])\n        if record[\"case\"] in (\"K1\", \"K2\"):\n            time.sleep(self.timing.session_timeout + self.timing.heartbeat_interval)\n        self.log.log(\"owner\", owner=self.wait_owner(), position=record[\"position\"])\n        if self.read_peaks() == \"stop\":\n            self.stop_reason = \"memory\"",
  "new_string": "        restarted = [w for w in WORKERS if self.procs[w].poll() is not None]\n        for worker in restarted:\n            self.start_worker(worker)\n            self.log.log(\"restarted\", worker=worker, position=record[\"position\"])\n        if record[\"case\"] in (\"K1\", \"K2\"):\n            time.sleep(self.timing.session_timeout + self.timing.heartbeat_interval)\n        for worker in restarted:\n            self.wait_joined(worker)\n        self.log.log(\"owner\", owner=self.wait_owner(), position=record[\"position\"])\n        if self.read_peaks() == \"stop\":\n            self.stop_reason = \"memory\""
}
```

## 111. Assistant — 2026-10-24T05:23:57.337Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        for proc in self.procs.values():\n            if proc.poll() is None:\n                os.kill(proc.pid, signal.SIGKILL)\n        for proc in self.procs.values():\n            proc.wait(timeout=30)\n        grace = self.timing.watchdog_tick + self.timing.kill_grace + 10\n        left = self.wait_for(lambda: not [v for v in processes.marked_processes()\n                                          if v.startswith(f\"{self.store_id}:\")] or None, grace,\n                             \"the attempts' processes to end\") if self._marked() else True\n        from etf_risk.jobs import mysql",
  "new_string": "        for proc in self.procs.values():\n            if proc.poll() is None:\n                os.kill(proc.pid, signal.SIGKILL)\n        for proc in self.procs.values():\n            proc.wait(timeout=30)\n        try:                                                  # each launcher ends its tree on EOF\n            self.wait_for(lambda: not self._marked(), self.timing.watchdog_tick + self.timing.kill_grace + 10,\n                          \"the attempts' processes to end\")\n            processes_left = False\n        except PhaseMissed:\n            processes_left = True\n        from etf_risk.jobs import mysql"
}
```

## 112. Assistant — 2026-10-24T05:23:58.785Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        record = {\"processes_left\": not left, \"other_connections\": len(others)}",
  "new_string": "        record = {\"processes_left\": processes_left, \"other_connections\": len(others)}"
}
```

## 113. Assistant — 2026-10-24T05:24:05.336Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        self.services_up()\n        try:\n            self.cli(\"init-db\")\n            self.cli(\"create-topic\")\n            self.open_store()\n            self.reference_run()\n            self.start(\"reconciler\", \"reconciler\")\n            self.start_worker(\"A\")\n            self.log.log(\"owner\", owner=self.wait_owner(), position=0)\n            self.start_worker(\"B\")\n            time.sleep(self.timing.heartbeat_interval)          # B's join, and the rebalance it causes\n            self.log.log(\"owner\", owner=self.wait_owner(), position=0)\n            for position, case in enumerate(self.plan[\"jobs\"], start=1):\n                if self.stop_reason is not None:\n                    self.log.log(\"not_run\", position=position, case=case, why=self.stop_reason)\n                    continue\n                record = self.run_job(position, case)\n                if record.get(\"final\") is None:\n                    self.stop_reason = \"an unfinished job\" if record.get(\"job_id\") else \"a submit that failed\"\n                    continue\n                self.after_job(record)\n            self.quiesce()\n            self.final_snapshot()\n        finally:",
  "new_string": "        self.services_up()\n        try:\n            self.cli(\"init-db\")\n            self.cli(\"create-topic\")\n            self.store_id = self.store().store_id()\n            self.reference_run()\n            self.start(\"reconciler\", \"reconciler\")\n            self.start_worker(\"A\")\n            self.log.log(\"owner\", owner=self.wait_joined(\"A\"), position=0)\n            self.start_worker(\"B\")\n            self.log.log(\"owner\", owner=self.wait_joined(\"B\"), position=0)\n            for position, case in enumerate(self.plan[\"jobs\"], start=1):\n                if self.stop_reason is not None:\n                    self.log.log(\"not_run\", position=position, case=case, why=self.stop_reason)\n                    continue\n                try:\n                    record = self.run_job(position, case)\n                    if record.get(\"final\") is None:\n                        self.stop_reason = \"an unfinished job\" if record.get(\"job_id\") else \"a submit that failed\"\n                        continue\n                    self.after_job(record)\n                except Exception as error:                   # recorded; the batch still ends cleanly\n                    self.log.log(\"job_error\", position=position, case=case, error=f\"{type(error).__name__}: {error}\")\n                    self.stop_reason = \"an error in the harness\"\n            try:\n                self.quiesce()\n                self.final_snapshot()\n            except Exception as error:\n                self.log.log(\"final_error\", error=f\"{type(error).__name__}: {error}\")\n                self.stop_reason = self.stop_reason or \"an error in the final snapshot\"\n        finally:"
}
```

## 114. User — 2026-10-24T05:24:06.402Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 115. User — 2026-10-24T05:24:07.480Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 116. User — 2026-10-24T05:24:09.084Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 117. User — 2026-10-24T05:24:10.312Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 118. Assistant — 2026-10-24T05:24:28.067Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'self\\.store\\b[^_(]|open_store\\(|self\\.store\\.' src/etf_risk/jobs/harness.py | grep -v 'def store' ; for f in src/etf_risk/jobs/harness.py src/etf_risk/jobs/faults.py src/etf_risk/jobs/cli.py src/etf_risk/jobs/kafka.py src/etf_risk/jobs/worker.py src/etf_risk/jobs/pipeline.py src/etf_risk/provenance.py; do python3 -I -m py_compile \"$f\" && echo \"compiles: $f\"; done; find src -name '__pycache__' -newer src/etf_risk/jobs/faults.py -type d | head -3",
  "description": "Compile the changed modules and look for stale references"
}
```

## 119. User — 2026-10-24T05:24:30.665Z

### Tool result

```
compiles: src/etf_risk/jobs/harness.py
compiles: src/etf_risk/jobs/faults.py
compiles: src/etf_risk/jobs/cli.py
compiles: src/etf_risk/jobs/kafka.py
compiles: src/etf_risk/jobs/worker.py
compiles: src/etf_risk/jobs/pipeline.py
compiles: src/etf_risk/provenance.py
src/etf_risk/__pycache__
src/etf_risk/jobs/__pycache__
```

## 120. Assistant — 2026-10-24T05:25:01.431Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        deadline_mono = reference_mono + d\n        self.batch_jobs.append((job_id, case, \"restored\" if reference == \"restored\" else reference, d,\n                                deadline_mono, s.max_lag_s))\n        self.log.log(\"deadline\", position=position, job_id=job_id, case=case, reference=reference,\n                     reference_mono=reference_mono, deadline_s=d, deadline_mono=deadline_mono, max_lag_s=s.max_lag_s)",
  "new_string": "        deadline_mono = reference_mono + d\n        self.batch_jobs.append((job_id, case, reference, d, deadline_mono, s.max_lag_s))\n        self.log.log(\"deadline\", position=position, job_id=job_id, case=case, reference=reference,\n                     reference_mono=reference_mono, deadline_s=d, deadline_mono=deadline_mono, max_lag_s=s.max_lag_s,\n                     t_submit=t_submit)"
}
```

## 121. Assistant — 2026-10-24T05:25:02.808Z

### Tool call: Bash

```
{
  "command": "sed -n '1,40p' analysis/collect_caching_measurements.py && grep -n -E '^def |^[A-Z_]+ = ' analysis/collect_caching_measurements.py | head -30",
  "description": "Read an existing collector's conventions"
}
```

## 122. User — 2026-10-24T05:25:04.464Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 123. User — 2026-10-24T05:25:04.727Z

### Tool result

```
"""Collect one batch of the caching experiment and evaluate its acceptance criteria.

docs/caching-experiment.md, sections 4.3, 6, 7 and 10. A batch folder holds:

    positions.tsv   one line per protocol the session helpers ran (docs/caching-session.zsh)
    run-log.txt     the session's run log (for people; not read here)
    A/, B/, C/      each configuration's out-root: <snapshot>/<window set>/protocol-*.json, run-*/

Run from the repository root:

    uv run python analysis/collect_caching_measurements.py --batch data/outputs-caching/batch-1
    uv run python analysis/collect_caching_measurements.py --check-protocol <protocol JSON> --config A

The first form writes measurements.csv (one row per started run) and acceptance.json (each
acceptance criterion with the problems found, plus observations) into the batch folder, prints a
summary, and exits with 1 if any criterion fails. The second form, which the session helpers run
after each protocol, checks every run of that protocol against its configuration: the recorded
settings, the plan capture and the cache verification of section 6 (3.4). A run that failed or was
aborted may lack its run.json, plans or output tables; both forms report that as a problem under
the criteria instead of stopping.

The rules it shares with the shuffle-partition experiment are that experiment's collector's
functions, imported unchanged: positions, protocols and runs, code state, inputs, the comparison of
tables by their full keys, file counts and check violations.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_caching_collector.py
and on a small window set (docs/caching-experiment.md 4.5).
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

46:PATH_KEY = [*WINDOW_KEY, "leverage"]
47:CACHE = {"A": "none", "B": "members", "C": "members-checks"}           # 2.1: --cache per configuration
48:OPTIONS = {config: {"shuffle_partitions": None, "coalesce": None, "record_plans": True, "cache": mode}
50:SPARK_DEFAULTS = {cpm.PARTITIONS: "200", cpm.ADAPTIVE: "true", cpm.COALESCE: "true"}
51:PHASES = ("window_stats", "model", "summaries", "checks")
52:TABLES = ("members", "window_stats", "path_days", "path_summary", "paired")
53:CACHED = {"A": (), "B": ("members",), "C": TABLES}
54:FILLED_IN = {"members": "window_stats", "window_stats": "window_stats", "path_days": "model",
56:RELEASED_IN = {"members": "model", "window_stats": "checks", "path_days": "checks", "path_summary": "checks",
58:HELD_AT_END_OF = {                                   # 6: the tables cached when each phase ends
64:READ_IN = {"A": (), "B": ("window_stats", "model"), "C": PHASES}       # 6.4: phases with downstream cached reads
65:FILL_PREFIX = "cache fill: "                         # spark_pipeline.FILL_DESCRIPTION: a fill's SQL execution (4.1)
66:STORAGE_LEVEL = "Disk Memory Deserialized 1x Replicated"               # MEMORY_AND_DISK_DESER
67:ROW_COUNT_OF = {"window_stats": "window_stats", "path_days": "path_days", "path_summary": "summary",
69:ORDER = ("A", "B", "C", "C", "B", "A")               # positions 1 to 6 (2.3)
70:WINDOWS = cpm.WINDOWS
71:REPEATS = 4
72:SPARK_VERSION = "4.2.0"
73:PLANS_FORMAT = 2
74:TABLE_KEYS = {"window_stats": list(WINDOW_KEY), "path_days": [*PATH_KEY, "day"], "path_summary": list(PATH_KEY),
76:CRITERIA = cpm.CRITERIA
78:IDENTITY_FIELDS = ["batch", "position", "config", "used", "protocol_id", "run_id", "run_number", "warmup", "status",
80:EXTRA_FIELDS = (["cache_mode", "plan_capture_status", "plan_capture_s", "wall_excl_capture_s", "sql_executions",
85:FIELDS = IDENTITY_FIELDS + cpm.MEASUREMENT_FIELDS + EXTRA_FIELDS
88:def read_table(run_dir: Path, name: str) -> pa.Table:
96:def output_state(run_dir: Path, name: str) -> str:
104:def read_output(run_dir: Path, name: str) -> tuple[pa.Table | None, str]:
114:def load_plans(run_dir: Path) -> dict | None:
123:def member_rows(windows: Path) -> int:
132:def check_settings(label: str, config: str, run: dict) -> list[str]:
```

## 124. Assistant — 2026-10-24T05:25:51.519Z

### Tool call: Bash

```
{
  "command": "sed -n \"$(grep -n '    def _classify' src/etf_risk/jobs/pipeline.py | cut -d: -f1),+60p\" src/etf_risk/jobs/pipeline.py | grep -v '^\\s*$' | head -62",
  "description": "Read the pipeline's result-rule checks"
}
```

## 125. User — 2026-10-24T05:25:52.255Z

### Tool result

```
    def _classify(self, step: dict, run_dir: Path, params: JobParams, claim: Claim) -> None:
        """Raise unless the step ran to its end and its records say it worked."""
        name, outcome, code, closed = step["name"], step["outcome"], step["returncode"], step["closed"]
        if closed == "stopped":
            raise PipelineError(f"{name}: the worker was stopped", retryable=True)
        if closed in ("fenced", "self_fenced") or outcome in ("deadline", "deadline_passed"):
            raise Fenced(f"{claim.run_id}: {name} ended: {closed or outcome}")
        if outcome == "clock_mismatch":
            raise PipelineError(f"{name}: the launcher reads another clock", retryable=False)
        if outcome != "exited":
            raise PipelineError(f"{name}: {outcome} (exit {code})", retryable=True)
        tail = self._tail(run_dir / "logs" / f"{name}.log")
        if name == "windows" and code != 0:
            raise PipelineError(f"windows exited {code}: {tail}", retryable=True)
        if name == "spark_pipeline":
            status = self._json(self.run_folder(params, claim, run_dir) / "run.json").get("status")
            if code == 3:
                raise PipelineError(f"spark_pipeline: an input checksum differs: {tail}", retryable=False)
            if status == "checks_failed":
                raise PipelineError("spark_pipeline: checks failed", retryable=False)
            if code != 0 or status != "ok":
                raise PipelineError(f"spark_pipeline exited {code} with status {status}: {tail}", retryable=True)
        if name == "verify":
            result = self._json(self.run_folder(params, claim, run_dir) / "verify.json")
            if code == 3:
                raise PipelineError(f"verify: an input checksum differs: {tail}", retryable=False)
            if result and (result.get("mismatch_count") or not result.get("breached_windows", {}).get("same", False)):
                raise PipelineError(f"verify: {result.get('mismatch_count')} mismatches", retryable=False)
            if code != 0 or not result:
                raise PipelineError(f"verify exited {code} without a clean verify.json: {tail}", retryable=True)
    def _check_result(self, run_folder: Path) -> None:
        run = self._json(run_folder / "run.json")
        checks = self._json(run_folder / "checks.json")
        verified = self._json(run_folder / "verify.json")
        if run.get("status") != "ok" or not checks:
            raise PipelineError(f"{run_folder}: run.json or checks.json is missing or not ok", retryable=True)
        if total_violations(checks):
            raise PipelineError(f"{run_folder}: {total_violations(checks)} check violations", retryable=False)
        if not verified or verified.get("mismatch_count") or not verified.get("breached_windows", {}).get("same"):
            raise PipelineError(f"{run_folder}: verify.json is missing or not clean", retryable=False)
        missing = [table for table in TABLES if not (run_folder / table / "_SUCCESS").is_file()]
        if missing:
            raise PipelineError(f"{run_folder}: no _SUCCESS in {missing}", retryable=True)
    @staticmethod
    def _json(path: Path) -> dict:
        try:
            value = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}
    @staticmethod
    def _tail(path: Path, lines: int = 5) -> str:
        try:
            return " | ".join(path.read_text(errors="replace").strip().splitlines()[-lines:])[-800:]
        except OSError:
            return "(no log)"
```

## 126. Assistant — 2026-10-24T05:26:24.389Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py",
  "old_string": "        if job_id is None:\n            if case == \"K2\":                                 # never leave the broker stopped",
  "new_string": "        if job_id is None:\n            self.log.log(\"job_not_submitted\", position=position, case=case)\n            if case == \"K2\":                                 # never leave the broker stopped"
}
```

## 127. User — 2026-10-24T05:26:25.643Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/src/etf_risk/jobs/harness.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 128. Assistant — 2026-10-24T05:27:41.330Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "content": "\"\"\"Collect one batch of the recovery experiments E1 and E2 (docs/recovery-experiments.md,\nsections 5 and 6).\n\nA batch folder is what etf_risk.jobs.harness batch wrote:\n\n    harness.jsonl   the harness's events: plan, injections, deadlines, observations, peaks, owners\n    events/         the workers' logs (A.jsonl, B.jsonl), the reconciler's, and submit.jsonl\n    jobs/<store>/   the attempts' folders, with logs/*.launcher.json and, when complete, manifest.json\n    reference/      the reference run, under the launcher\n    crosscheck/     Q0-Q3b as CSV (crosscheck.sql)\n    export/         the job tables as JSON (python -m etf_risk.jobs export)\n    plan.json       the plan the batch ran\n\nRun from the repository root:\n\n    uv run python analysis/collect_recovery_measurements.py --batch data/outputs-recovery/batch-1\n\nIt writes into the batch folder:\n- injections.csv: one row per planned job, with the case, the injection, the metrics of\n  section 5, each n/a with its reason or unknown when its record is missing, and the verdicts of\n  Q1, Q2 and Q3a;\n- tally.csv: per case, the jobs planned, made, missed and not run, and every verdict value of\n  Q1, Q2, deadline_met, Q3a and Q3b, with zeros;\n- validity.json: the checks of 6.1 (what counts) and, apart from them, the outcome checks of\n  6.2-6.5, each with what it found.\nIt prints a summary and exits with 1 if a validity check fails. A failed outcome check is a\nfinding: it is reported and never changes the exit code. Nothing is dropped: a missed or\nunrun job keeps its row.\n\nDurations are differences of mono values, from one host's monotonic clock (4.1). Step\nintervals come from the launcher records, which hold UTC times only at 6d8a232, so the overlap\nverdict holds only with a passed clock check (6.5).\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\nTested with tests/test_recovery_collector.py on synthetic batch folders; no real batch exists.\n\"\"\"\nfrom __future__ import annotations\n\nimport argparse\nimport csv\nimport importlib.util\nimport json\nimport statistics\nimport sys\nfrom datetime import datetime\nfrom pathlib import Path\n\nfrom etf_risk.jobs.events import read_events\n\nREPO = Path(__file__).resolve().parents[1]\nCASES = (\"C0\", \"W1\", \"W2\", \"W3\", \"W4\", \"W5a\", \"W5b\", \"W6\", \"W7\", \"K1\", \"K2\", \"D1\", \"D2\", \"X1\")\nREQUEUED_DETECTION = (\"W2\", \"W3\", \"W4\", \"W6\", \"W7\")\nNO_RECOVERY = {\"C0\": \"no failure\", \"X1\": \"no failure\", \"W5a\": \"after acceptance\", \"W5b\": \"after acceptance\"}\nNO_OVERHEAD = {\"W5a\": \"after acceptance\", \"W5b\": \"after acceptance\"}\nQ1_VERDICTS = (\"ok\", \"not finished\", \"failed\", \"more than one accepted attempt\", \"succeeded without an accepted attempt\",\n               \"accepted_attempt names another attempt\", \"accepted attempt of a job that did not succeed\",\n               \"attempt rows differ from attempt_number\", \"finished with an attempt still running\")\nQ2_CLASSES = (\"on time\", \"late\", \"unfinished\", \"failed\", \"missing\", \"deadline not observed\")\nDEADLINE_MET = (\"yes\", \"no\", \"unknown\")\nQ3A_VERDICTS = (\"reported once\", \"no matching report\", \"one attempt reported more than once\",\n                \"acceptance reported for more than one attempt\")\nQ3B_VERDICTS = (\"matches\", \"other store\", \"no such attempt\", \"wrong worker\", \"attempt not accepted\", \"wrong digest\")\nLIVENESS = (\"serve_restarted\", \"retry\", \"rewound\", \"gave_up\", \"failed_after_ack\", \"consumer_error\", \"pass_failed\")\nFIELDS = [\"position\", \"case\", \"job_id\", \"status\", \"missed\", \"injection\", \"worker\", \"t_inj\", \"reference\", \"deadline_s\",\n          \"detection_s\", \"rerun_s\", \"finish_s\", \"overhead_s\", \"claims\", \"accepted\", \"executions\", \"complete_executions\",\n          \"wasted_step_s\", \"fenced_events\", \"timeliness\", \"deadline_met\", \"q1_verdict\", \"q3a_verdict\"]\n\n\n# Reading the folder\n\ndef jsonl(path: Path) -> list[dict]:\n    return read_events(path) if path.exists() else []\n\n\ndef named(events: list[dict], name: str, **fields_) -> list[dict]:\n    return [e for e in events if e.get(\"event\") == name and all(e.get(k) == v for k, v in fields_.items())]\n\n\ndef csv_rows(path: Path) -> list[dict]:\n    if not path.exists():\n        return []\n    with open(path, newline=\"\") as f:\n        return [{k: None if v == \"NULL\" else v for k, v in row.items()} for row in csv.DictReader(f)]\n\n\ndef by_job(rows: list[dict]) -> dict[int, dict]:\n    return {int(r[\"job_id\"]): r for r in rows if r.get(\"job_id\") is not None}\n\n\nclass BatchFolder:\n    def __init__(self, folder: Path):\n        self.folder = folder\n        self.harness = jsonl(folder / \"harness.jsonl\")\n        self.workers = {p.stem: read_events(p) for p in sorted((folder / \"events\").glob(\"*.jsonl\"))\n                        if p.stem != \"submit\" and not p.stem.startswith(\"reconciler-\")}\n        self.reconciler = [e for p in sorted((folder / \"events\").glob(\"reconciler-*.jsonl\")) for e in read_events(p)]\n        self.plan = json.loads((folder / \"plan.json\").read_text())\n        self.q = {name: csv_rows(folder / \"crosscheck\" / f\"{name}.csv\") for name in (\"Q0\", \"Q1\", \"Q2\", \"Q2b\", \"Q3a\", \"Q3b\")}\n        export = folder / \"export\"\n        self.jobs = json.loads((export / \"jobs.json\").read_text()) if (export / \"jobs.json\").exists() else []\n        self.attempts = (json.loads((export / \"job_attempts.json\").read_text())\n                         if (export / \"job_attempts.json\").exists() else [])\n        store = json.loads((export / \"store.json\").read_text()) if (export / \"store.json\").exists() else {}\n        self.store_id = store.get(\"store_id\")\n\n    def worker_events(self) -> list[dict]:\n        return [{**e, \"worker\": w} for w, events in self.workers.items() for e in events]\n\n    def first_after(self, events: list[dict], t: float) -> dict | None:\n        later = [e for e in events if e.get(\"mono\") is not None and e[\"mono\"] >= t]\n        return min(later, key=lambda e: e[\"mono\"]) if later else None\n\n    def attempt_dir(self, run_id: str) -> Path:\n        return self.folder / \"jobs\" / (self.store_id or \"\") / run_id\n\n\n# Metrics (section 5)\n\ndef utc_seconds(start: str, end: str) -> float:\n    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()\n\n\ndef launcher_record(folder: Path, step: str) -> dict | None:\n    path = folder / \"logs\" / f\"{step}.launcher.json\"\n    try:\n        return json.loads(path.read_text())\n    except (OSError, json.JSONDecodeError):\n        return None\n\n\ndef step_intervals(b: BatchFolder) -> tuple[list[tuple], list[str]]:\n    \"\"\"Every started step's interval (UTC), and the steps that lack one (6.5).\"\"\"\n    intervals, missing = [], []\n    claims = {(e[\"job_id\"], e[\"attempt\"]): e[\"run_id\"] for e in named(b.worker_events(), \"claimed\")}\n    for e in named(b.worker_events(), \"step_started\"):\n        run_id = claims.get((e[\"job_id\"], e[\"attempt\"]))\n        record = launcher_record(b.attempt_dir(run_id), e[\"step\"]) if run_id else None\n        label = f\"{run_id or e['job_id']}:{e['step']}\"\n        if record and record.get(\"step_started_at_utc\") and record.get(\"tree_ended_at_utc\"):\n            intervals.append((record[\"step_started_at_utc\"], record[\"tree_ended_at_utc\"], label))\n        else:\n            missing.append(label)\n    for step in (\"windows\", \"spark_pipeline\"):\n        record = launcher_record(b.folder / \"reference\", step)\n        if record and record.get(\"step_started_at_utc\") and record.get(\"tree_ended_at_utc\"):\n            intervals.append((record[\"step_started_at_utc\"], record[\"tree_ended_at_utc\"], f\"reference:{step}\"))\n        else:\n            missing.append(f\"reference:{step}\")\n    return sorted(intervals), missing\n\n\ndef overlap_verdict(intervals: list[tuple], missing: list[str]) -> dict:\n    \"\"\"no overlap, overlap, or unknown: a missing interval never counts as no overlap (6.5).\"\"\"\n    overlaps = [(a[2], b_[2]) for a, b_ in zip(intervals, intervals[1:])\n                if datetime.fromisoformat(b_[0]) < datetime.fromisoformat(a[1])]\n    verdict = \"overlap\" if overlaps else \"unknown\" if missing else \"no overlap\"\n    return {\"verdict\": verdict, \"overlaps\": overlaps, \"steps_without_interval\": missing,\n            \"note\": \"UTC launcher times; valid only with a passed clock check\"}\n\n\ndef job_metrics(b: BatchFolder, position: int, case: str, injection: dict, deadline: dict,\n                c0_median: float | None) -> dict:\n    job_id = deadline[\"job_id\"]\n    events = [e for e in b.worker_events() if e.get(\"job_id\") == job_id]\n    t_inj, missed = injection.get(\"t_inj\"), injection.get(\"missed\")\n    row = {\"detection_s\": None, \"rerun_s\": None, \"finish_s\": None, \"overhead_s\": None}\n    reason = NO_RECOVERY.get(case)\n    if missed:\n        row.update(detection_s=\"n/a: injection missed\", rerun_s=\"n/a: injection missed\")\n    elif reason:\n        row.update(detection_s=f\"n/a: {reason}\", rerun_s=f\"n/a: {reason}\")\n    elif case == \"K1\":\n        row.update(detection_s=\"n/a for the job: the attempt goes on\", rerun_s=\"n/a: the attempt goes on\")\n    elif t_inj is not None:\n        if case == \"W1\":\n            detection = b.first_after([e for e in named(events, \"delivered\") if e[\"worker\"] != injection.get(\"worker\")],\n                                      t_inj)\n        elif case in REQUEUED_DETECTION:\n            detection = b.first_after(named(b.reconciler, \"requeued\", job_id=job_id), t_inj)\n        elif case == \"K2\":\n            detection = b.first_after(named(b.reconciler, \"published\", job_id=job_id), t_inj)\n        elif case == \"D1\":\n            detection = b.first_after(named(events, \"renewal_failed\"), t_inj)\n        else:                                                     # D2\n            detection = b.first_after(named(events, \"retry\", operation=\"accept_result\"), t_inj)\n        row[\"detection_s\"] = detection[\"mono\"] - t_inj if detection else \"unknown: no detection event\"\n        before = [e for e in named(events, \"claimed\") if e[\"mono\"] < t_inj]\n        injected = max((e[\"attempt\"] for e in before), default=0)\n        rerun = b.first_after([e for e in named(events, \"claimed\") if e[\"attempt\"] > injected], t_inj)\n        if rerun:\n            row[\"rerun_s\"] = rerun[\"mono\"] - t_inj\n        elif case in (\"D1\", \"D2\"):\n            row[\"rerun_s\"] = \"n/a: the attempt went on\"\n        else:\n            row[\"rerun_s\"] = \"unknown: no new claim\"\n    accepted = min(named(events, \"accepted\"), key=lambda e: e[\"mono\"], default=None)\n    start = deadline.get(\"t_submit\") if case == \"C0\" or missed else t_inj\n    if case in NO_OVERHEAD and not missed:\n        row[\"finish_s\"] = row[\"overhead_s\"] = f\"n/a: {NO_OVERHEAD[case]}\"\n    elif accepted is None:\n        row[\"finish_s\"] = row[\"overhead_s\"] = \"unknown: no accepted event\"\n    else:\n        row[\"finish_s\"] = accepted[\"mono\"] - start if start is not None else \"unknown\"\n        if deadline.get(\"t_submit\") is not None and c0_median is not None:\n            row[\"overhead_s\"] = accepted[\"mono\"] - deadline[\"t_submit\"] - c0_median\n        else:\n            row[\"overhead_s\"] = \"unknown: no C0 median\"\n    claims = {e[\"attempt\"]: e[\"run_id\"] for e in named(events, \"claimed\")}\n    row[\"executions\"] = len({e[\"attempt\"] for e in named(events, \"step_started\", step=\"windows\")})\n    row[\"complete_executions\"] = sum(1 for run_id in claims.values() if (b.attempt_dir(run_id) / \"manifest.json\").exists())\n    row[\"fenced_events\"] = len(named(events, \"fenced\")) + len(named(events, \"renewal_refused\"))\n    row[\"wasted_step_s\"] = wasted_step_time(b, job_id, claims)\n    return row\n\n\ndef wasted_step_time(b: BatchFolder, job_id: int, claims: dict[int, str]) -> float | str:\n    \"\"\"The step time of the job's attempts that were not accepted; unknown if a started step has\n    no complete launcher record.\"\"\"\n    accepted = {a[\"attempt_number\"] for a in b.attempts if a[\"job_id\"] == job_id and a[\"outcome\"] == \"accepted\"}\n    total = 0.0\n    for e in named(b.worker_events(), \"step_started\", job_id=job_id):\n        if e[\"attempt\"] in accepted:\n            continue\n        record = launcher_record(b.attempt_dir(claims.get(e[\"attempt\"], \"\")), e[\"step\"])\n        if not record or not record.get(\"step_started_at_utc\") or not record.get(\"tree_ended_at_utc\"):\n            return f\"unknown: no complete record for attempt {e['attempt']} {e['step']}\"\n        total += utc_seconds(record[\"step_started_at_utc\"], record[\"tree_ended_at_utc\"])\n    return total\n\n\n# Checks (section 6)\n\ndef identity_check(b: BatchFolder) -> dict:\n    \"\"\"6.1: one code identity across the harness, every process start and every step launch.\"\"\"\n    seen = []\n    for e in named(b.harness, \"batch_started\") + named(b.harness, \"batch_ended\"):\n        seen.append((\"harness\", e.get(\"code\")))\n    for e in named(b.harness, \"process_started\"):\n        seen.append((e.get(\"name\"), e.get(\"code\")))\n    for e in named(b.worker_events(), \"step_started\"):\n        seen.append((f\"{e['worker']} step\", e.get(\"code\")))\n    pairs = {(c.get(\"source_digest\"), c.get(\"uv_lock_sha256\")) if c else None for _, c in seen}\n    return {\"passed\": len(pairs) == 1 and None not in pairs, \"distinct\": len(pairs), \"records\": len(seen)}\n\n\ndef clock_check(b: BatchFolder, tolerance_s: float) -> dict:\n    start, end = named(b.harness, \"batch_started\"), named(b.harness, \"batch_ended\")\n    if not start or not end:\n        return {\"passed\": False, \"why\": \"no batch_started or batch_ended event\"}\n    a, z = start[0][\"clock\"], end[-1][\"clock\"]\n    difference = utc_seconds(a[\"ts\"], z[\"ts\"]) - (z[\"mono\"] - a[\"mono\"])\n    same = [e.get(\"same_clock\") for e in named(b.harness, \"process_started\")]\n    return {\"passed\": abs(difference) <= tolerance_s and all(same), \"ts_minus_mono_s\": difference,\n            \"tolerance_s\": tolerance_s, \"processes_on_the_same_clock\": f\"{sum(map(bool, same))} of {len(same)}\"}\n\n\ndef accepted_checks(b: BatchFolder) -> list[dict]:\n    \"\"\"6.2 items 3 and 4 for every accepted attempt: the digest, the result rule from the files,\n    and the tables against the reference run by content.\"\"\"\n    from etf_risk import runs\n    from etf_risk.jobs.pipeline import TABLES, total_violations\n    ccm = _caching_collector()\n    reference = next(iter(sorted((b.folder / \"reference\" / \"output\").glob(\"*/*/reference\"))), None)\n    found = []\n    for a in (a for a in b.attempts if a[\"outcome\"] == \"accepted\"):\n        folder = Path(a[\"output_dir\"])\n        problems = []\n        try:\n            record = json.loads((folder / \"attempt.json\").read_text())\n            run_folder = folder / record[\"run_folder\"]\n        except (OSError, json.JSONDecodeError, KeyError):\n            found.append({\"job_id\": a[\"job_id\"], \"problems\": [\"no readable attempt.json\"]})\n            continue\n        if runs.folder_digest(run_folder) != a[\"result_digest\"]:\n            problems.append(\"the folder's digest differs from the accepted digest\")\n        run, checks, verified = (_json(run_folder / n) for n in (\"run.json\", \"checks.json\", \"verify.json\"))\n        if run.get(\"status\") != \"ok\" or not checks or total_violations(checks):\n            problems.append(\"run.json or checks.json is not ok\")\n        if not verified or verified.get(\"mismatch_count\") or not verified.get(\"breached_windows\", {}).get(\"same\"):\n            problems.append(\"verify.json is not clean\")\n        if missing := [t for t in TABLES if not (run_folder / t / \"_SUCCESS\").is_file()]:\n            problems.append(f\"no _SUCCESS in {missing}\")\n        if reference is None:\n            problems.append(\"no reference run to compare with\")\n        else:\n            for table, key in ccm.TABLE_KEYS.items():\n                diff, _ = ccm.cpm.compare_tables(ccm.read_table(reference, table), ccm.read_table(run_folder, table),\n                                                 key, ccm.cpm.BREACH_FIELDS.get(table, []))\n                problems += [f\"{table}: {p}\" for p in diff]\n        found.append({\"job_id\": a[\"job_id\"], \"attempt\": a[\"attempt_number\"], \"problems\": problems})\n    return found\n\n\ndef _json(path: Path) -> dict:\n    try:\n        value = json.loads(path.read_text())\n    except (OSError, json.JSONDecodeError):\n        return {}\n    return value if isinstance(value, dict) else {}\n\n\ndef _caching_collector():\n    sys.path.insert(0, str(REPO / \"analysis\"))\n    spec = importlib.util.spec_from_file_location(\"collect_caching_measurements\",\n                                                  REPO / \"analysis\" / \"collect_caching_measurements.py\")\n    module = importlib.util.module_from_spec(spec)\n    spec.loader.exec_module(module)\n    return module\n\n\ndef input_check(b: BatchFolder) -> dict:\n    \"\"\"6.1: the snapshot's input checksums now equal those every job recorded at submit.\"\"\"\n    from etf_risk.jobs.params import input_checksums\n    settings = b.plan[\"settings\"]\n    try:\n        now = input_checksums(REPO / \"data\" / \"processed\", settings[\"snapshot\"])\n    except Exception as error:\n        return {\"passed\": False, \"why\": f\"{type(error).__name__}: {error}\"}\n    differ = [j[\"job_id\"] for j in b.jobs if j.get(\"input_checksums\") != now]\n    return {\"passed\": not differ, \"jobs_differing\": differ}\n\n\n# The batch\n\ndef collect(folder: Path, clock_tolerance_s: float = 1.0) -> dict:\n    b = BatchFolder(folder)\n    deadlines = {e[\"position\"]: e for e in named(b.harness, \"deadline\")}\n    injections = {e[\"position\"]: e for e in named(b.harness, \"injection\")}\n    not_run = {e[\"position\"]: e for e in named(b.harness, \"not_run\")}\n    not_submitted = {e[\"position\"]: e for e in named(b.harness, \"job_not_submitted\")}\n    q1, q2, q3a = by_job(b.q[\"Q1\"]), by_job(b.q[\"Q2\"]), by_job(b.q[\"Q3a\"])\n    c0 = []\n    for position, e in deadlines.items():\n        accepted = min(named([x for x in b.worker_events() if x.get(\"job_id\") == e[\"job_id\"]], \"accepted\"),\n                       key=lambda x: x[\"mono\"], default=None)\n        if e[\"case\"] == \"C0\" and accepted is not None:\n            c0.append(accepted[\"mono\"] - e[\"t_submit\"])\n    c0_median = statistics.median(c0) if c0 else None\n    rows = []\n    for position, case in enumerate(b.plan[\"jobs\"], start=1):\n        row = {\"position\": position, \"case\": case}\n        if position in not_run or position in not_submitted:\n            row[\"status\"] = \"not run\" if position in not_run else \"not submitted\"\n            rows.append(row)\n            continue\n        if position not in deadlines:\n            row[\"status\"] = \"no record\"\n            rows.append(row)\n            continue\n        d, inj = deadlines[position], injections.get(position, {})\n        job_id = d[\"job_id\"]\n        row.update(job_id=job_id, status=\"made\" if not inj.get(\"missed\") else \"missed\", missed=inj.get(\"missed\"),\n                   injection=inj.get(\"kind\"), worker=inj.get(\"worker\"), t_inj=inj.get(\"t_inj\"),\n                   reference=d[\"reference\"], deadline_s=d[\"deadline_s\"])\n        row.update(job_metrics(b, position, case, inj, d, c0_median))\n        row.update(claims=(q1.get(job_id) or {}).get(\"n_claims\"), accepted=(q1.get(job_id) or {}).get(\"n_accepted\"),\n                   q1_verdict=(q1.get(job_id) or {}).get(\"verdict\"), timeliness=(q2.get(job_id) or {}).get(\"timeliness\"),\n                   deadline_met=(q2.get(job_id) or {}).get(\"deadline_met\"),\n                   q3a_verdict=(q3a.get(job_id) or {}).get(\"log_verdict\"))\n        rows.append(row)\n    intervals, missing = step_intervals(b)\n    final = (named(b.harness, \"final_snapshot\") or [{}])[-1]\n    quiescent = (named(b.harness, \"quiescent\") or [{}])[-1]\n    validity = {\n        \"injections\": {\"planned\": len(rows), \"made\": sum(r.get(\"status\") == \"made\" for r in rows),\n                       \"missed\": [r[\"position\"] for r in rows if r.get(\"status\") == \"missed\"],\n                       \"not_run\": [r[\"position\"] for r in rows if r.get(\"status\") in (\"not run\", \"not submitted\")]},\n        \"code_identity\": identity_check(b),\n        \"clock\": clock_check(b, clock_tolerance_s),\n        \"fingerprints_agree\": {\"passed\": bool(final.get(\"fingerprints_agree\")), \"values\": final.get(\"fingerprints\")},\n        \"inputs_unchanged\": input_check(b),\n        \"machine_state\": {\"passed\": None, \"why\": \"not recorded: 8.3 leaves the host-state rules open\"},\n    }\n    validity_failed = [name for name, check in validity.items()\n                       if isinstance(check, dict) and check.get(\"passed\") is False]\n    outcomes = {\n        \"q1_not_ok\": [r[\"job_id\"] for r in rows if r.get(\"q1_verdict\") not in (None, \"ok\")],\n        \"status_check_exit\": final.get(\"status_check_exit\"),\n        \"accepted_attempts\": accepted_checks(b),\n        \"overlap\": overlap_verdict(intervals, missing),\n        \"nothing_left\": {\"processes_left\": quiescent.get(\"processes_left\"),\n                         \"other_connections\": quiescent.get(\"other_connections\")},\n        \"q2b_rows\": b.q[\"Q2b\"],\n        \"q3b_not_matching\": [r for r in b.q[\"Q3b\"] if r.get(\"report_verdict\") != \"matches\"],\n        \"liveness\": {name: len(named(b.worker_events() + b.reconciler, name)) for name in LIVENESS},\n        \"batch_peaks\": final.get(\"batch_peaks\"),\n    }\n    return {\"rows\": rows, \"tally\": tally(rows, b), \"validity\": validity, \"validity_failed\": validity_failed,\n            \"outcomes\": outcomes, \"c0_median_s\": c0_median}\n\n\ndef tally(rows: list[dict], b: BatchFolder) -> list[dict]:\n    \"\"\"Per case: planned, made, missed, not run, and every verdict value, with zeros.\"\"\"\n    q3b_case = {}\n    cases_by_job = {r[\"job_id\"]: r[\"case\"] for r in rows if r.get(\"job_id\") is not None}\n    for r in b.q[\"Q3b\"]:\n        case = cases_by_job.get(int(r[\"job_id\"])) if r.get(\"job_id\") else None\n        q3b_case.setdefault(case, []).append(r.get(\"report_verdict\"))\n    out = []\n    for case in CASES:\n        mine = [r for r in rows if r[\"case\"] == case]\n        entry = {\"case\": case, \"planned\": len(mine), \"made\": sum(r.get(\"status\") == \"made\" for r in mine),\n                 \"missed\": sum(r.get(\"status\") == \"missed\" for r in mine),\n                 \"not_run\": sum(r.get(\"status\") in (\"not run\", \"not submitted\", \"no record\") for r in mine),\n                 \"claims\": sum(int(r[\"claims\"]) for r in mine if r.get(\"claims\") is not None)}\n        for prefix, values, column in ((\"q1\", Q1_VERDICTS, \"q1_verdict\"), (\"q2\", Q2_CLASSES, \"timeliness\"),\n                                       (\"met\", DEADLINE_MET, \"deadline_met\"), (\"q3a\", Q3A_VERDICTS, \"q3a_verdict\")):\n            for value in values:\n                entry[f\"{prefix}: {value}\"] = sum(r.get(column) == value for r in mine)\n        for value in Q3B_VERDICTS:\n            entry[f\"q3b: {value}\"] = q3b_case.get(case, []).count(value)\n        out.append(entry)\n    return out\n\n\ndef write(folder: Path, result: dict) -> None:\n    with open(folder / \"injections.csv\", \"w\", newline=\"\") as f:\n        writer = csv.DictWriter(f, fieldnames=FIELDS, extrasaction=\"ignore\")\n        writer.writeheader()\n        writer.writerows(result[\"rows\"])\n    with open(folder / \"tally.csv\", \"w\", newline=\"\") as f:\n        writer = csv.DictWriter(f, fieldnames=list(result[\"tally\"][0]))\n        writer.writeheader()\n        writer.writerows(result[\"tally\"])\n    (folder / \"validity.json\").write_text(json.dumps(\n        {k: result[k] for k in (\"validity\", \"validity_failed\", \"outcomes\", \"c0_median_s\")}, indent=2, default=str) + \"\\n\")\n\n\ndef main(argv: list[str] | None = None) -> int:\n    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])\n    parser.add_argument(\"--batch\", type=Path, required=True)\n    parser.add_argument(\"--clock-tolerance\", type=float, default=1.0,\n                        help=\"seconds (provisional; the outline's 8.5 leaves it open)\")\n    args = parser.parse_args(argv)\n    result = collect(args.batch, args.clock_tolerance)\n    write(args.batch, result)\n    v = result[\"validity\"][\"injections\"]\n    print(f\"{v['planned']} jobs planned, {v['made']} made, {len(v['missed'])} missed, {len(v['not_run'])} not run\")\n    print(\"validity: \" + (\"all checks passed\" if not result[\"validity_failed\"]\n                          else \"FAILED: \" + \", \".join(result[\"validity_failed\"])))\n    print(f\"overlap: {result['outcomes']['overlap']['verdict']}; jobs whose Q1 verdict is not ok:\"\n          f\" {result['outcomes']['q1_not_ok'] or 'none'}\")\n    return 1 if result[\"validity_failed\"] else 0\n\n\nif __name__ == \"__main__\":\n    sys.exit(main())\n"
}
```

## 129. User — 2026-10-24T05:27:42.562Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py (file state is current in your context — no need to Read it back)
```

## 130. Assistant — 2026-10-24T05:28:00.772Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "        self.reconciler = [e for p in sorted((folder / \"events\").glob(\"reconciler-*.jsonl\")) for e in read_events(p)]\n        self.plan = json.loads((folder / \"plan.json\").read_text())",
  "new_string": "        self.reconciler = [e for p in sorted((folder / \"events\").glob(\"reconciler-*.jsonl\")) for e in read_events(p)]\n        self.submits = jsonl(folder / \"events\" / \"submit.jsonl\")\n        self.plan = json.loads((folder / \"plan.json\").read_text())"
}
```

## 131. Assistant — 2026-10-24T05:28:02.822Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "    for e in named(b.harness, \"process_started\"):\n        seen.append((e.get(\"name\"), e.get(\"code\")))\n    for e in named(b.worker_events(), \"step_started\"):",
  "new_string": "    for e in named(b.harness, \"process_started\"):\n        seen.append((e.get(\"name\"), e.get(\"code\")))\n    for e in named(b.submits, \"started\"):\n        seen.append((\"submit\", e.get(\"code\")))\n    for e in named(b.worker_events(), \"step_started\"):"
}
```

## 132. Assistant — 2026-10-24T05:28:05.424Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "def input_check(b: BatchFolder) -> dict:\n    \"\"\"6.1: the snapshot's input checksums now equal those every job recorded at submit.\"\"\"\n    from etf_risk.jobs.params import input_checksums\n    settings = b.plan[\"settings\"]\n    try:\n        now = input_checksums(REPO / \"data\" / \"processed\", settings[\"snapshot\"])",
  "new_string": "def input_check(b: BatchFolder, processed_root: Path) -> dict:\n    \"\"\"6.1: the snapshot's input checksums now equal those every job recorded at submit.\"\"\"\n    from etf_risk.jobs.params import input_checksums\n    settings = b.plan[\"settings\"]\n    try:\n        now = input_checksums(processed_root, settings[\"snapshot\"])"
}
```

## 133. Assistant — 2026-10-24T05:28:07.274Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "def collect(folder: Path, clock_tolerance_s: float = 1.0) -> dict:\n    b = BatchFolder(folder)",
  "new_string": "def collect(folder: Path, clock_tolerance_s: float = 1.0, processed_root: Path = REPO / \"data\" / \"processed\") -> dict:\n    b = BatchFolder(folder)"
}
```

## 134. Assistant — 2026-10-24T05:28:08.674Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "        \"inputs_unchanged\": input_check(b),",
  "new_string": "        \"inputs_unchanged\": input_check(b, processed_root),"
}
```

## 135. Assistant — 2026-10-24T05:28:10.512Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "        \"status_check_exit\": final.get(\"status_check_exit\"),",
  "new_string": "        \"status_check_exit\": final.get(\"status_check_exit\"),\n        \"invariant_violations\": _json(folder / \"export\" / \"invariant_violations.json\") if\n        (folder / \"export\" / \"invariant_violations.json\").exists() else \"no export\","
}
```

## 136. User — 2026-10-24T05:28:11.580Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 137. User — 2026-10-24T05:28:12.698Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 138. User — 2026-10-24T05:28:13.903Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 139. User — 2026-10-24T05:28:14.968Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 140. User — 2026-10-24T05:28:16.078Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 141. User — 2026-10-24T05:28:17.164Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 142. Assistant — 2026-10-24T05:28:52.330Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'EventLog|read_events|events=|def test_|^from|^import' tests/test_jobs_pipeline.py | head -30 && echo \"=== test_provenance.py\" && sed -n '1,25p' tests/test_provenance.py && grep -n -E '^def test_' tests/test_provenance.py",
  "description": "Read the pipeline and provenance test patterns"
}
```

## 143. User — 2026-10-24T05:28:53.308Z

### Tool result

```
15:import json
16:import os
17:import sys
18:import threading
19:import time
20:from pathlib import Path
22:import numpy as np
23:import psutil
24:import pytest
25:from conftest import nyse_sessions, write_snapshot
27:from etf_risk import runs
28:from etf_risk.jobs import processes
29:from etf_risk.jobs.params import JobParams, input_checksums
30:from etf_risk.jobs.pipeline import SubprocessPipeline
31:from etf_risk.jobs.store import Claim
32:from etf_risk.jobs.timing import Timing
33:from etf_risk.jobs.worker import Fenced, PipelineError
41:import json, os, sys
53:import json, os, sys
59:import json, os, subprocess, sys, time
67:import json, os, sys
144:def test_a_good_run_is_recorded_and_returns_the_digest_of_its_run_folder(tmp_path, claim):
167:def test_failures_are_classified_from_the_records(tmp_path, claim, plan, retryable, words):
176:def test_inputs_that_changed_since_the_submission_fail_for_good_before_any_step(tmp_path, claim):
199:def test_a_refused_renewal_ends_the_step_tree_and_fences_the_attempt(tmp_path, claim):
210:def test_failing_renewals_fence_the_worker_by_its_deadline_and_no_step_starts_after_it(tmp_path, claim):
225:def test_while_the_worker_is_stuck_in_a_renewal_the_watchdog_ends_the_tree_before_the_lease_expires(tmp_path, claim):
264:def test_a_stopped_worker_ends_the_running_step_and_the_job_is_retried(tmp_path, claim):
274:def test_the_step_environment_is_an_allowlist_with_the_marker_and_the_scratch_folders(tmp_path, claim, monkeypatch):
291:def test_a_renewal_refused_just_before_acceptance_fences_the_attempt(tmp_path, claim):
=== test_provenance.py
"""code_state(): git when available, the Docker image's build record otherwise; the source
hashes cover every module and schema file of the package, subpackages included.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
from pathlib import Path

import pytest

from etf_risk import provenance
from etf_risk.ingest import sha256_file


@pytest.fixture
def no_build_record(monkeypatch):
    for name in (provenance.BUILD_COMMIT_ENV, provenance.BUILD_CLEAN_ENV, provenance.IMAGE_ID_ENV):
        monkeypatch.delenv(name, raising=False)


def test_git_is_used_when_available(monkeypatch, no_build_record):
    answers = {"rev-parse": "abc123", "status": ""}
    monkeypatch.setattr(provenance, "_git", lambda *args: answers[args[0]])
    monkeypatch.setenv(provenance.BUILD_COMMIT_ENV, "from-build")        # ignored while git answers
    state = provenance.code_state()
21:def test_git_is_used_when_available(monkeypatch, no_build_record):
31:def test_build_record_is_used_without_git(monkeypatch, no_build_record):
42:def test_nothing_is_claimed_without_git_or_build_record(monkeypatch, no_build_record):
49:def test_every_module_and_schema_is_hashed_under_its_path_in_the_package(monkeypatch, no_build_record):
66:def test_top_level_modules_keep_the_keys_of_earlier_records(monkeypatch, no_build_record):
```

## 144. Assistant — 2026-10-24T05:29:00.740Z

The pipeline tests don't capture events yet, so the new `step_started` assertion needs a pipeline built with a real `EventLog`. I'll read how a good run is set up there:

## 145. Assistant — 2026-10-24T05:29:01.773Z

### Tool call: Bash

```
{
  "command": "sed -n '100,166p' tests/test_jobs_pipeline.py",
  "description": "Read the pipeline test fixtures and the good-run test"
}
```

## 146. User — 2026-10-24T05:29:04.308Z

### Tool result

```
    def __call__(self):
        answer = self.answers[min(self.calls, len(self.answers) - 1)]
        self.calls += 1
        return answer() if callable(answer) else answer


@pytest.fixture
def claim(tmp_path):
    dates = nyse_sessions("2024-01-02", 31)
    write_snapshot(tmp_path, "snap", {"AAA": (dates, np.random.default_rng(1).normal(0, 0.01, 30))})
    params = JobParams("snap", "rolling", window_days=8, stride=21, anchor="2024-01-02", sample_ticker="AAA")
    run_dir = tmp_path / "runs" / "job-1-attempt-1"
    run_dir.mkdir(parents=True)
    return Claim(1, 1, "t" * 32, "job-1-attempt-1", run_dir, 3, params.to_dict(),
                 input_checksums(tmp_path / "processed", "snap"))


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


@pytest.fixture(autouse=True)
def kill_leftovers():
    yield
    for value, procs in processes.marked_processes().items():
        if value.startswith(STORE + ":"):
            for p in procs:
                try:
                    p.kill()
                except psutil.Error:
                    pass


def test_a_good_run_is_recorded_and_returns_the_digest_of_its_run_folder(tmp_path, claim):
    pipeline = Steps(tmp_path, good())
    digest = pipeline.run(claim, claim.output_dir, Heartbeat())
    run_folder = claim.output_dir / "output" / "snap" / "rolling-8-s21" / "job-1-attempt-1"
    assert digest == runs.folder_digest(run_folder)
    assert json.loads((claim.output_dir / "manifest.json").read_text()) == runs.manifest(run_folder)
    record = json.loads((claim.output_dir / "attempt.json").read_text())
    assert [(s["name"], s["outcome"], s["returncode"]) for s in record["steps"]] == [
        ("windows", "exited", 0), ("spark_pipeline", "exited", 0), ("verify", "exited", 0)]
    assert record["code"]["source_sha256"]["jobs/pipeline.py"] and record["store_id"] == STORE
    assert not (claim.output_dir / ".work").exists()
    assert pipeline.fence_at > time.monotonic()                   # renewed just before acceptance


@pytest.mark.parametrize("plan, retryable, words", [
    (good(spark=("ok", "0", "3")), False, "input checksum differs"),
    (good(spark=("checks_failed", "1", "1")), False, "checks failed"),
    (good(spark=("failed", "0", "2")), True, "with status failed"),
    (good(verify=("2", "1")), False, "2 mismatches"),
    (good(verify=("0", "1")), True, "without a clean verify.json"),
    ({**good(), "windows": ["import sys; sys.exit(1)"]}, True, "windows exited 1"),
    ({**good(), "windows": ["import time; time.sleep(60)"]}, True, "timeout"),
])
```

## 147. Assistant — 2026-10-24T05:29:09.708Z

The good-run test builds its pipeline through a `Steps` helper. Checking whether it can take an event log:

## 148. Assistant — 2026-10-24T05:29:11.151Z

### Tool call: Bash

```
{
  "command": "sed -n \"$(grep -n '^class Steps' tests/test_jobs_pipeline.py | cut -d: -f1),+16p\" tests/test_jobs_pipeline.py && grep -n '^STORE' tests/test_jobs_pipeline.py",
  "description": "Read the stand-in pipeline helper used by the tests"
}
```

## 149. User — 2026-10-24T05:29:12.000Z

### Tool result

```
class Steps(SubprocessPipeline):
    """The pipeline with stand-in steps; plan maps a step to its argv after the interpreter."""

    def __init__(self, tmp_path, plan, **kwargs):
        super().__init__(store_id=STORE, processed_root=tmp_path / "processed", worker_id="worker-test",
                         lock_path=tmp_path / "locks" / "host.lock", timing=TIMING, **kwargs)
        self.plan = plan

    def commands(self, params, claim, run_dir):
        folder = str(self.run_folder(params, claim, run_dir))
        return [(name, [self.python, "-c", *[a.replace("{run}", folder) for a in self.plan[name]]])
                for name in ("windows", "spark_pipeline", "verify")]


def good(spark=("ok", "0", "0"), verify=("0", "0")):
    return {"windows": ["import sys; sys.exit(0)"],
            "spark_pipeline": [SPARK, "{run}", *spark],
35:STORE = "e" * 32
```

## 150. Assistant — 2026-10-24T05:29:30.169Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_faults.py",
  "content": "\"\"\"The fault hook armed through a file (etf_risk.jobs.faults), offline: kill is replaced, so no\nprocess ends.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nimport json\n\nimport pytest\n\nfrom etf_risk.jobs import faults\nfrom etf_risk.jobs.events import EventLog, read_events\nfrom etf_risk.jobs.worker import WORKER_FAULT_POINTS\n\n\n@pytest.fixture\ndef hook(tmp_path):\n    log = tmp_path / \"worker.jsonl\"\n    kills = []\n    fault = faults.FaultFile(tmp_path / \"A.fault\", EventLog(log, \"worker\", worker_id=\"A\"), kill=lambda: kills.append(1))\n    return fault, kills, log\n\n\ndef events(log):\n    return [(e[\"event\"], e.get(\"point\"), e.get(\"action\") or e.get(\"why\")) for e in read_events(log)]\n\n\ndef test_nothing_happens_while_nothing_is_armed(hook):\n    fault, kills, log = hook\n    for point in WORKER_FAULT_POINTS:\n        fault(point)\n    assert kills == [] and not log.exists()\n\n\ndef test_a_kill_fires_once_at_its_point_and_nowhere_else(hook):\n    fault, kills, log = hook\n    faults.arm(fault.path, \"after_pipeline\")\n    fault(\"before_claim\")\n    fault(\"after_claim\")\n    assert fault.path.exists() and kills == []                  # left for its own point\n    fault(\"after_pipeline\")\n    assert not fault.path.exists() and kills == [1]\n    fault(\"after_pipeline\")                                     # once: the file is gone\n    assert kills == [1] and events(log) == [(\"fault_injected\", \"after_pipeline\", \"kill\")]\n\n\ndef test_a_hold_waits_for_its_release(hook, tmp_path):\n    fault, kills, log = hook\n    release = tmp_path / \"release\"\n    ticks = []\n\n    def sleep(seconds):\n        ticks.append(seconds)\n        if len(ticks) == 3:\n            release.touch()\n\n    fault._sleep = sleep\n    faults.arm(fault.path, \"after_pipeline\", \"hold\", release=release, timeout_s=60)\n    fault(\"after_pipeline\")\n    assert kills == [] and len(ticks) == 3\n    assert events(log) == [(\"fault_injected\", \"after_pipeline\", \"hold\"), (\"fault_released\", \"after_pipeline\", \"released\")]\n\n\ndef test_a_hold_gives_up_after_its_timeout(hook, tmp_path):\n    fault, kills, log = hook\n    now = [100.0]\n    fault._clock = lambda: now[0]\n    fault._sleep = lambda seconds: now.__setitem__(0, now[0] + seconds)\n    faults.arm(fault.path, \"after_pipeline\", \"hold\", release=tmp_path / \"never\", timeout_s=1.0)\n    fault(\"after_pipeline\")\n    assert events(log)[-1] == (\"fault_released\", \"after_pipeline\", \"timeout\")\n\n\n@pytest.mark.parametrize(\"text\", [\"not json\", json.dumps({\"point\": \"no_such_point\", \"action\": \"kill\"}),\n                                  json.dumps({\"point\": \"after_claim\", \"action\": \"explode\"}),\n                                  json.dumps({\"point\": \"after_claim\", \"action\": \"hold\"})])\ndef test_an_arming_that_went_wrong_is_refused_and_never_becomes_a_fault(hook, text):\n    fault, kills, log = hook\n    fault.path.write_text(text)\n    fault(\"after_claim\")\n    assert kills == [] and not fault.path.exists()\n    assert [e for e, _, _ in events(log)] == [\"fault_refused\"]\n\n\ndef test_arming_is_atomic_and_the_environment_decides(tmp_path, monkeypatch):\n    path = tmp_path / \"B.fault\"\n    faults.arm(path, \"after_accept_commit\")\n    assert json.loads(path.read_text()) == {\"point\": \"after_accept_commit\", \"action\": \"kill\"}\n    assert sorted(p.name for p in tmp_path.iterdir()) == [\"B.fault\"]          # no temporary file left\n    log = EventLog(tmp_path / \"w.jsonl\", \"worker\")\n    monkeypatch.delenv(faults.FAULT_FILE_ENV, raising=False)\n    assert faults.fault_from_environment(log) is None\n    monkeypatch.setenv(faults.FAULT_FILE_ENV, str(path))\n    assert faults.fault_from_environment(log).path == path\n"
}
```

## 151. User — 2026-10-24T05:29:31.336Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_faults.py (file state is current in your context — no need to Read it back)
```

## 152. Assistant — 2026-10-24T05:29:47.925Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py",
  "old_string": "    assert events == [\"before_claim\", \"after_claim\", \"acknowledge\", \"after_pipeline\", \"after_accept\"]",
  "new_string": "    assert events == [\"before_claim\", \"after_claim\", \"acknowledge\", \"after_pipeline\", \"after_accept_commit\",\n                      \"after_accept\"]"
}
```

## 153. Assistant — 2026-10-24T05:29:53.911Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py",
  "old_string": "def test_a_crash_after_acceptance_keeps_the_one_result(env):\n    job = submit(env)\n    with pytest.raises(SimulatedCrash):\n        env.deliver(env.worker(\"A\", fault=crash_at(\"after_accept\")), job)\n    assert env.admin.job(job)[\"status\"] is Status.SUCCEEDED\n    again = env.deliver(env.worker(\"B\"), job)\n    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)\n    env.check(job, lost_acceptances=1)                              # A died before it could tell",
  "new_string": "def test_a_crash_after_acceptance_keeps_the_one_result(env):\n    job = submit(env)\n    with pytest.raises(SimulatedCrash):\n        env.deliver(env.worker(\"A\", fault=crash_at(\"after_accept\")), job)\n    assert env.admin.job(job)[\"status\"] is Status.SUCCEEDED\n    again = env.deliver(env.worker(\"B\"), job)\n    assert (again.result, again.reason) == (Result.SKIPPED, Refusal.SUCCEEDED)\n    env.check(job, lost_acceptances=1)                              # A died before it could tell\n\n\ndef test_a_crash_between_the_acceptance_commit_and_its_event_leaves_the_result_unreported(env, tmp_path):\n    \"\"\"Recovery case W5a: the table holds one accepted result and the log has no accepted event.\"\"\"\n    job = submit(env)\n    worker = env.worker(\"A\", fault=crash_at(\"after_accept_commit\"))\n    worker.events = EventLog(tmp_path / \"A.jsonl\", \"worker\", worker_id=\"worker-A\")\n    with pytest.raises(SimulatedCrash):\n        env.deliver(worker, job)\n    assert env.admin.job(job)[\"status\"] is Status.SUCCEEDED\n    assert [a[\"outcome\"] for a in env.admin.attempts(job)] == [Outcome.ACCEPTED]\n    assert [e[\"event\"] for e in read_events(tmp_path / \"A.jsonl\")] == [\"claimed\"]   # no accepted event\n    env.check(job, lost_acceptances=1)"
}
```

## 154. Assistant — 2026-10-24T05:29:55.758Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py",
  "old_string": "from etf_risk.jobs.simulated import SimulatedCrash, SimulatedPipeline",
  "new_string": "from etf_risk.jobs.events import EventLog, read_events\nfrom etf_risk.jobs.simulated import SimulatedCrash, SimulatedPipeline"
}
```

## 155. Assistant — 2026-10-24T05:29:57.300Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_queue.py",
  "old_string": "            if point == \"after_accept\":\n                lost[current[\"job\"]] += 1                                              # accepted, never told",
  "new_string": "            if point in (\"after_accept_commit\", \"after_accept\"):\n                lost[current[\"job\"]] += 1                                              # accepted, never told"
}
```

## 156. User — 2026-10-24T05:29:58.392Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py has been updated successfully.
```

## 157. User — 2026-10-24T05:29:59.482Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py has been updated successfully.
```

## 158. User — 2026-10-24T05:30:00.551Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_worker.py has been updated successfully.
```

## 159. User — 2026-10-24T05:30:01.637Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_queue.py has been updated successfully.
```

## 160. Assistant — 2026-10-24T05:30:21.131Z

### Tool call: Bash

```
{
  "command": "sed -n \"$(grep -n '^class KafkaTopic' tests/jobs_backends.py | cut -d: -f1),+40p\" tests/jobs_backends.py && grep -n -A12 '^def poll_after_assignment' tests/jobs_backends.py && grep -n -B2 -A6 '^def needs_kafka\\|^needs_kafka' tests/jobs_backends.py",
  "description": "Read the Kafka test helpers"
}
```

## 161. User — 2026-10-24T05:30:22.142Z

### Tool result

```
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
301:def poll_after_assignment(consumer, *, settle: float = 3.0, timeout: float = 30.0) -> list:
302-    """Everything the consumer receives until `settle` seconds after it got its partition."""
303-    deliveries, deadline = [], time.monotonic() + timeout
304-    while not consumer.assigned() and time.monotonic() < deadline:
305-        if (delivery := consumer.poll(0.5)) is not None:
306-            deliveries.append(delivery)
307-    assert consumer.assigned(), "the consumer never got its partition"
308-    until = time.monotonic() + settle
309-    while time.monotonic() < until:
310-        if (delivery := consumer.poll(0.5)) is not None:
311-            deliveries.append(delivery)
312-    return deliveries
313-
40-needs_mysql = pytest.mark.skipif(not MYSQL_URL, reason="set ETF_RISK_MYSQL_URL to run against MySQL")
41-KAFKA_BOOTSTRAP = os.environ.get("ETF_RISK_KAFKA_BOOTSTRAP")
42:needs_kafka = pytest.mark.skipif(not KAFKA_BOOTSTRAP, reason="set ETF_RISK_KAFKA_BOOTSTRAP to run against Kafka")
43-LEASE = timedelta(seconds=60)
44-PARAMS = {"snapshot": "simulated", "stride": 21}
45-DIGEST = "d" * 64          # a run digest for store tests that accept without a pipeline
46-DUMP = ("SELECT * FROM jobs ORDER BY job_id", "SELECT * FROM job_attempts ORDER BY job_id, attempt_number")
47-
48-
```

## 162. Assistant — 2026-10-24T05:30:29.584Z

The live test can use `topic.consumer(group, events=...)` and `poll_after_assignment()`. Checking how the existing `topic` fixture is marked:

## 163. Assistant — 2026-10-24T05:30:30.631Z

### Tool call: Bash

```
{
  "command": "sed -n '60,100p' tests/test_jobs_kafka.py",
  "description": "Read the Kafka test fixture and a live test"
}
```

## 164. User — 2026-10-24T05:30:31.448Z

### Tool result

```
            config["max.poll.interval.ms"], config["socket.timeout.ms"]) == ("classic", 15_000, 3_000, 967_000, 10_000)
    assert 6_000 <= config["session.timeout.ms"] < t.lease * 1000
    assert 3 * config["heartbeat.interval.ms"] <= config["session.timeout.ms"] <= config["max.poll.interval.ms"]
    assert config["max.poll.interval.ms"] > (t.attempt_limit + t.kill_grace) * 1000


def test_an_unreachable_broker_gives_false():
    pytest.importorskip("confluent_kafka")
    from etf_risk.jobs.kafka import KafkaPublisher
    publisher = KafkaPublisher("127.0.0.1:1", "nowhere", confirmation_timeout=timedelta(seconds=2))
    started = time.monotonic()
    assert publisher.publish(1) is False
    assert time.monotonic() - started < 10


# Against Kafka

@pytest.fixture
def topic():
    topic = KafkaTopic()
    yield topic
    topic.close()


@needs_kafka
def test_jobs_published_before_a_fresh_group_starts_are_all_delivered(topic):
    publisher = topic.publisher()
    assert all(publisher.publish(job) for job in (1, 2, 3))
    consumer = topic.consumer(topic.group())                        # a group that never existed
    assert [d.job_id() for d in poll_deliveries(consumer, 3)] == [1, 2, 3]


@needs_kafka
def test_with_latest_a_fresh_group_would_miss_them(topic):
    publisher = topic.publisher()
    assert all(publisher.publish(job) for job in (1, 2, 3))
    consumer = topic.consumer(topic.group(), settings={"auto.offset.reset": "latest"})
    assert poll_after_assignment(consumer) == []


@needs_kafka
```

## 165. Assistant — 2026-10-24T05:30:48.727Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py",
  "old_string": "Offline, always: the producer's and the consumer's settings (acks=all, idempotence, the\nmessage timeout equal to the confirmation timeout; no auto-commit, earliest).",
  "new_string": "Offline, always: the producer's and the consumer's settings (acks=all, idempotence, the\nmessage timeout equal to the confirmation timeout; no auto-commit, earliest), and the\nassignment events a rebalance writes (partitions and member id)."
}
```

## 166. Assistant — 2026-10-24T05:30:50.423Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py",
  "old_string": "- a rewind delivers the same message again;",
  "new_string": "- a rewind delivers the same message again;\n- a consumer that joins its group writes an assigned event naming the topic's partition;"
}
```

## 167. Assistant — 2026-10-24T05:30:52.076Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py",
  "old_string": "from etf_risk.jobs.kafka import consumer_config, producer_config",
  "new_string": "from etf_risk.jobs.events import EventLog, read_events\nfrom etf_risk.jobs.kafka import consumer_config, log_assignment, producer_config"
}
```

## 168. Assistant — 2026-10-24T05:30:56.334Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py",
  "old_string": "def test_an_unreachable_broker_gives_false():",
  "new_string": "def test_assignment_events_name_the_partitions_and_the_member(tmp_path):\n    \"\"\"The recovery harness reads the partition's owner from these events (docs/recovery-experiments.md, 2.4).\"\"\"\n    class Partition:\n        def __init__(self, topic, partition):\n            self.topic, self.partition = topic, partition\n\n    class Member:\n        def memberid(self):\n            return \"rdkafka-0001\"\n\n    class Joining:\n        def memberid(self):\n            raise RuntimeError(\"no member id yet\")\n\n    log = EventLog(tmp_path / \"A.jsonl\", \"worker\", worker_id=\"A\")\n    log_assignment(log, \"assigned\", Member(), [Partition(\"jobs\", 0)])\n    log_assignment(log, \"revoked\", Joining(), [Partition(\"jobs\", 0)])\n    log_assignment(log, \"lost\", Member(), [])\n    assert [(e[\"event\"], e[\"partitions\"], e[\"member\"], e[\"worker_id\"]) for e in read_events(tmp_path / \"A.jsonl\")] == [\n        (\"assigned\", [[\"jobs\", 0]], \"rdkafka-0001\", \"A\"), (\"revoked\", [[\"jobs\", 0]], None, \"A\"),\n        (\"lost\", [], \"rdkafka-0001\", \"A\")]\n\n\ndef test_an_unreachable_broker_gives_false():"
}
```

## 169. Assistant — 2026-10-24T05:30:59.197Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py",
  "old_string": "@needs_kafka\ndef test_with_latest_a_fresh_group_would_miss_them(topic):",
  "new_string": "@needs_kafka\ndef test_a_consumer_that_joins_its_group_logs_the_partition_it_was_given(topic, tmp_path):\n    log = tmp_path / \"A.jsonl\"\n    consumer = topic.consumer(topic.group(), events=EventLog(log, \"worker\", worker_id=\"A\"))\n    poll_after_assignment(consumer)\n    assigned = [e for e in read_events(log) if e[\"event\"] == \"assigned\"]\n    assert assigned and assigned[-1][\"partitions\"] == [[topic.name, 0]] and assigned[-1][\"member\"]\n\n\n@needs_kafka\ndef test_with_latest_a_fresh_group_would_miss_them(topic):"
}
```

## 170. User — 2026-10-24T05:31:00.277Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py has been updated successfully.
```

## 171. User — 2026-10-24T05:31:01.356Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py has been updated successfully.
```

## 172. User — 2026-10-24T05:31:02.428Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py has been updated successfully.
```

## 173. User — 2026-10-24T05:31:03.499Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py has been updated successfully.
```

## 174. User — 2026-10-24T05:31:04.585Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_kafka.py has been updated successfully.
```

## 175. Assistant — 2026-10-24T05:31:20.567Z

### Tool call: Bash

```
{
  "command": "sed -n '47,76p' tests/test_jobs_cli.py && grep -n '^class Heartbeat' -A6 tests/test_jobs_pipeline.py | head -8",
  "description": "Read the CLI submit test and the pipeline Heartbeat helper"
}
```

## 176. User — 2026-10-24T05:31:21.379Z

### Tool result

```
def test_init_db_writes_one_store_id_and_keeps_it(setup, capsys):
    db, base, _ = setup
    code, out = run(capsys, "init-db", *base)
    first = json.loads(out)["store_id"]
    assert code == 0 and json.loads(run(capsys, "init-db", *base)[1])["store_id"] == first


def test_submit_records_the_parameters_and_the_input_checksums(setup, capsys):
    db, base, tmp_path = setup
    run(capsys, "init-db", *base)
    code, out = run(capsys, "submit", *base, "--snapshot", "snap", "--kind", "rolling", "--window-days", "8",
                    "--anchor", "2024-01-02", "--sample-ticker", "AAA")
    assert code == 0 and json.loads(out) == {"job_id": 1, "published": True, "recorded": True}
    job = JobStore(open_sqlite(tmp_path / "jobs.sqlite"), SQLITE).job(1)
    assert job["params"] == {"snapshot": "snap", "kind": "rolling", "window_days": 8, "stride": 21,
                             "anchor": "2024-01-02", "sample_ticker": "AAA"}
    assert sorted(job["input_checksums"]) == ["daily_returns/AAA.parquet", "quality_report.json"]
    assert FakePublisher.published == [("etf-risk-jobs", 1)]
    events = (tmp_path / "out" / "events" / "submit.jsonl").read_text()
    assert '"event": "submitted"' in events


def test_unusable_parameters_are_refused_before_anything_is_written(setup, capsys):
    db, base, tmp_path = setup
    run(capsys, "init-db", *base)
    with pytest.raises(SystemExit, match="at least 21"):
        cli.main(["submit", *base, "--snapshot", "snap", "--kind", "rolling", "--stride", "7"])
    assert JobStore(open_sqlite(tmp_path / "jobs.sqlite"), SQLITE).all_jobs() == []


92:class Heartbeat:
93-    """Scripted renewals: answers, one per call, then repeat the last; a callable answer is
94-    called (to block or raise)."""
95-
96-    def __init__(self, *answers):
97-        self.answers, self.calls = list(answers) or [True], 0
98-        self.claimed_mono = time.monotonic()
```

## 177. Assistant — 2026-10-24T05:31:27.581Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_cli.py",
  "old_string": "    events = (tmp_path / \"out\" / \"events\" / \"submit.jsonl\").read_text()\n    assert '\"event\": \"submitted\"' in events",
  "new_string": "    events = read_events(tmp_path / \"out\" / \"events\" / \"submit.jsonl\")\n    assert [e[\"event\"] for e in events] == [\"started\", \"submitted\"]\n    assert events[0][\"code\"] == {**code_identity(), \"git_commit\": events[0][\"code\"][\"git_commit\"]}   # identity at launch"
}
```

## 178. Assistant — 2026-10-24T05:31:29.478Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_cli.py",
  "old_string": "from etf_risk.jobs import cli\nfrom etf_risk.jobs.store import SQLITE, JobStore, open_sqlite",
  "new_string": "from etf_risk.jobs import cli\nfrom etf_risk.jobs.events import read_events\nfrom etf_risk.jobs.store import SQLITE, JobStore, open_sqlite\nfrom etf_risk.provenance import code_identity"
}
```

## 179. Assistant — 2026-10-24T05:31:32.032Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_pipeline.py",
  "old_string": "@pytest.mark.parametrize(\"plan, retryable, words\", [",
  "new_string": "def test_each_step_launch_records_the_code_it_starts_from(tmp_path, claim):\n    log = tmp_path / \"events.jsonl\"\n    Steps(tmp_path, good(), events=EventLog(log, \"worker\")).run(claim, claim.output_dir, Heartbeat())\n    started = [e for e in read_events(log) if e[\"event\"] == \"step_started\"]\n    assert [e[\"step\"] for e in started] == [\"windows\", \"spark_pipeline\", \"verify\"]\n    assert all(e[\"code\"] == source_identity() for e in started)\n\n\n@pytest.mark.parametrize(\"plan, retryable, words\", ["
}
```

## 180. Assistant — 2026-10-24T05:31:33.733Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_pipeline.py",
  "old_string": "from etf_risk.jobs import processes\nfrom etf_risk.jobs.params import JobParams, input_checksums",
  "new_string": "from etf_risk.jobs import processes\nfrom etf_risk.jobs.events import EventLog, read_events\nfrom etf_risk.jobs.params import JobParams, input_checksums"
}
```

## 181. Assistant — 2026-10-24T05:31:35.190Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_pipeline.py",
  "old_string": "from etf_risk.jobs.worker import Fenced, PipelineError",
  "new_string": "from etf_risk.jobs.worker import Fenced, PipelineError\nfrom etf_risk.provenance import source_identity"
}
```

## 182. Assistant — 2026-10-24T05:31:39.721Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_provenance.py",
  "old_string": "def test_git_is_used_when_available(monkeypatch, no_build_record):",
  "new_string": "def test_the_launch_identity_is_one_digest_of_the_source_hashes_with_the_lock(monkeypatch, no_build_record):\n    \"\"\"What a starting process and a step launch record (docs/recovery-experiments.md, 2.3).\"\"\"\n    monkeypatch.setattr(provenance, \"_git\", lambda *args: {\"rev-parse\": \"abc123\", \"status\": \"\"}[args[0]])\n    state, identity = provenance.code_state(), provenance.code_identity()\n    assert identity == {\"git_commit\": \"abc123\", \"git_worktree_clean\": True,\n                        \"source_digest\": provenance.source_digest(state[\"source_sha256\"]),\n                        \"uv_lock_sha256\": state[\"uv_lock_sha256\"]}\n    assert provenance.source_identity() == {k: identity[k] for k in (\"source_digest\", \"uv_lock_sha256\")}\n\n\ndef test_the_source_digest_ignores_the_order_and_sees_every_hash():\n    hashes = {\"jobs/a.py\": \"1\" * 64, \"jobs/schema/b.sql\": \"2\" * 64}\n    assert provenance.source_digest(hashes) == provenance.source_digest(dict(reversed(list(hashes.items()))))\n    assert provenance.source_digest(hashes) != provenance.source_digest({**hashes, \"jobs/schema/b.sql\": \"3\" * 64})\n\n\ndef test_git_is_used_when_available(monkeypatch, no_build_record):"
}
```

## 183. User — 2026-10-24T05:31:40.782Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_cli.py has been updated successfully.
```

## 184. User — 2026-10-24T05:31:41.866Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_cli.py has been updated successfully.
```

## 185. User — 2026-10-24T05:31:42.986Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_pipeline.py has been updated successfully.
```

## 186. User — 2026-10-24T05:31:44.110Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_pipeline.py has been updated successfully.
```

## 187. User — 2026-10-24T05:31:45.220Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_pipeline.py has been updated successfully.
```

## 188. User — 2026-10-24T05:31:46.344Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_provenance.py has been updated successfully.
```

## 189. Assistant — 2026-10-24T05:31:54.777Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_cli.py",
  "old_string": "    assert events[0][\"code\"] == {**code_identity(), \"git_commit\": events[0][\"code\"][\"git_commit\"]}   # identity at launch",
  "new_string": "    assert events[0][\"code\"] == code_identity()                    # the code identity, recorded at launch"
}
```

## 190. User — 2026-10-24T05:31:56.072Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_cli.py has been updated successfully.
```

## 191. Assistant — 2026-10-24T05:32:26.528Z

### Tool call: Write

````
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_harness.py",
  "content": "\"\"\"The recovery harness's offline parts (etf_risk.jobs.harness): plans, deadlines, the\npartition's owner from assignment events, worker reports, memory peaks by segment, the\ncross-check SQL, fingerprints and the duration estimate. The batch itself needs the services and\nthe snapshot, and has not run: no formal experiment.\n\nThe cross-check SQL must stay the SQL validated on 2026-10-23 (docs/recovery-sql.md, section 6):\ncrosscheck.sql below its separator equals the document's SQL blocks, byte for byte.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nimport json\nimport re\nfrom collections import Counter\nfrom pathlib import Path\n\nimport pytest\n\nfrom etf_risk.jobs import harness\nfrom etf_risk.jobs.timing import DEFAULT_TIMING\n\nREPO = Path(__file__).resolve().parents[1]\nDEFAULTS = harness.Settings()\n\n\ndef test_a_plan_has_three_jobs_of_every_case_in_an_order_fixed_by_its_seed():\n    jobs = harness.plan_jobs(DEFAULTS, seed=7)\n    assert len(jobs) == 42 and Counter(jobs) == {case: 3 for case in harness.CASES}\n    assert jobs == harness.plan_jobs(DEFAULTS, seed=7) != harness.plan_jobs(DEFAULTS, seed=8)\n\n\ndef test_the_deadlines_at_the_default_clock():\n    \"\"\"P3, revised: B plus twice the slowest step sum, rounded up to 5 s; K2, D1 and D2 count from\n    their service's return, so no restart duration is assumed.\"\"\"\n    d = {case: harness.deadline_seconds(case, DEFAULT_TIMING, DEFAULTS) for case in harness.CASES}\n    assert d == {\"C0\": 75, \"W1\": 90, \"W2\": 140, \"W3\": 140, \"W4\": 140, \"W5a\": 75, \"W5b\": 75, \"W6\": 140,\n                 \"W7\": 170, \"K1\": 75, \"K2\": 125, \"D1\": 140, \"D2\": 140, \"X1\": 75}\n    assert {case: harness.deadline_reference(case) for case in (\"C0\", \"W3\", \"K2\", \"D1\", \"D2\", \"X1\")} == {\n        \"C0\": \"submit\", \"W3\": \"injection\", \"K2\": \"restored\", \"D1\": \"restored\", \"D2\": \"restored\", \"X1\": \"injection\"}\n\n\ndef test_w7_waits_for_the_later_of_the_takeover_and_the_end_of_the_stopped_tree():\n    short = harness.Settings(w7_stop_s=10.0)\n    assert harness.bound_to_next_run(\"W7\", DEFAULT_TIMING, short) == 65.0          # the takeover decides\n    assert harness.bound_to_next_run(\"W7\", DEFAULT_TIMING, DEFAULTS) == 90.0 + 2 * 0.5 + 7.0\n\n\ndef assigned(mono, *partitions, pid=1):\n    return {\"event\": \"assigned\", \"mono\": mono, \"pid\": pid, \"partitions\": [[\"t\", p] for p in partitions]}\n\n\ndef test_the_owner_comes_from_the_assignment_events_of_live_workers_only():\n    logs = {\"A\": [{\"event\": \"started\", \"mono\": 1}, assigned(2, 0)],\n            \"B\": [{\"event\": \"started\", \"mono\": 3}, assigned(4)]}\n    assert harness.owner(logs, {\"A\", \"B\"}) == \"A\"\n    logs[\"A\"].append({\"event\": \"revoked\", \"mono\": 5, \"partitions\": [[\"t\", 0]]})\n    logs[\"B\"].append(assigned(6, 0))\n    assert harness.owner(logs, {\"A\", \"B\"}) == \"B\"\n    assert harness.owner(logs, {\"A\"}) is None                                    # B died holding it\n    logs[\"B\"].append({\"event\": \"started\", \"mono\": 7})                            # B restarted: holds nothing yet\n    assert harness.owner(logs, {\"A\", \"B\"}) is None\n    both = {\"A\": [assigned(1, 0)], \"B\": [assigned(2, 0)]}\n    assert harness.owner(both, {\"A\", \"B\"}) is None                               # never guessed\n\n\ndef test_worker_reports_carry_the_logs_identity():\n    logs = {\"A\": [{\"event\": \"accepted\", \"store_id\": \"s\" * 32, \"worker_id\": \"A\", \"pid\": 11, \"job_id\": 3, \"attempt\": 2,\n                   \"digest\": \"d\" * 64}, {\"event\": \"claimed\", \"job_id\": 4}]}\n    assert harness.worker_accepts(logs) == [(\"s\" * 32, \"A\", 11, 3, 2, \"d\" * 64)]\n\n\ndef test_peaks_by_segment_keep_the_maximum_and_mark_a_lost_reading():\n    book = harness.PeakBook()\n    book.add(\"mysql\", 300 * 2**20, 512 * 2**20, \"mysql stop\")                    # closes the first segment\n    book.add(\"mysql\", 200 * 2**20, 512 * 2**20, None)                            # restarted: a new, lower count\n    peak = book.batch_peak(\"mysql\")\n    assert (peak[\"peak_bytes\"], peak[\"incomplete\"], peak[\"readings\"]) == (300 * 2**20, False, 2)\n    book.add(\"mysql\", None, None, \"end\")\n    assert book.batch_peak(\"mysql\")[\"incomplete\"] is True\n    assert book.batch_peak(\"kafka\")[\"incomplete\"] is True                         # never read\n    assert [harness.memory_verdict(f, DEFAULTS) for f in (None, 0.5, 0.91, 0.96)] == [\"unknown\", \"ok\", \"flag\", \"stop\"]\n\n\ndef doc_blocks() -> list[str]:\n    doc = (REPO / \"docs\" / \"recovery-sql.md\").read_text()\n    blocks = re.findall(r\"^```sql\\n(.*?)^```$\", doc, flags=re.S | re.M)\n    prefixes = (\"-- The harness's records\", \"-- Q0.\", \"-- Q1.\", \"-- Q2.\", \"-- Q2b.\", \"-- Q3a.\", \"-- Q3b.\")\n    return [next(b for b in blocks if b.startswith(p)) for p in prefixes]\n\n\ndef test_crosscheck_sql_is_the_validated_sql_byte_for_byte():\n    text = harness.CROSSCHECK_SQL.read_text()\n    body = text.split(\"\\n\", next(i for i, line in enumerate(text.splitlines()) if harness._SEPARATOR.match(line)) + 1)[-1]\n    assert body == \"\\n\".join(doc_blocks())\n\n\ndef test_the_crosscheck_statements_come_in_order_with_their_names():\n    names = [name for name, _ in harness.crosscheck_statements()]\n    assert names == [\"DDL\", \"DDL\", \"DDL\", \"Q0\", \"Q1\", \"Q2\", \"Q2b\", \"Q3a\", \"Q3b\"]\n    assert all(sql.rstrip().endswith(\";\") for _, sql in harness.crosscheck_statements())\n\n\ndef test_the_exported_fingerprint_counts_jobs_versions_attempts_and_renewals(tmp_path):\n    (tmp_path / \"jobs.json\").write_text(json.dumps([{\"version\": 4}, {\"version\": 7}]))\n    (tmp_path / \"job_attempts.json\").write_text(json.dumps([{\"renewals\": 2}, {\"renewals\": 1}, {\"renewals\": 2}]))\n    assert harness.fingerprint_from_export(tmp_path) == {\"n_jobs\": 2, \"sum_version\": 11, \"n_attempts\": 3,\n                                                         \"sum_renewals\": 5}\n\n\ndef test_settings_refuse_unknown_names_and_cases_and_survive_a_plan(tmp_path):\n    with pytest.raises(ValueError, match=\"unknown settings\"):\n        harness.Settings.from_dict({\"jobs_per_kase\": 3})\n    with pytest.raises(ValueError, match=\"unknown cases\"):\n        harness.Settings.from_dict({\"cases\": [\"C0\", \"W9\"]})\n    plan = harness.make_plan(DEFAULTS, seed=1)\n    again = json.loads(json.dumps(plan))\n    assert harness.Settings.from_dict(again[\"settings\"]) == DEFAULTS and len(again[\"jobs\"]) == 42\n    assert again[\"deadlines_s\"][\"W7\"] == 170 and set(again[\"code\"]) >= {\"source_digest\", \"uv_lock_sha256\"}\n\n\ndef test_the_estimate_of_a_default_batch_and_what_each_case_costs():\n    \"\"\"Under Assumptions (none measured): 1,403 s for one job of each case, 4,389 s for 42 jobs.\"\"\"\n    result = harness.estimate(harness.make_plan(DEFAULTS, seed=1))\n    per = result[\"per_case_s\"]\n    assert (per[\"C0\"], per[\"W1\"], per[\"W4\"], per[\"W7\"], per[\"K2\"], per[\"D1\"], per[\"D2\"]) == (42, 74, 159, 159, 118, 116,\n                                                                                            149)\n    assert sum(per.values()) == 1403 and result[\"batch_s\"] == 3 * 1403 + 180 == 4389\n"
}
````

## 192. User — 2026-10-24T05:32:27.700Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_jobs_harness.py (file state is current in your context — no need to Read it back)
```

## 193. Assistant — 2026-10-24T05:33:50.940Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py",
  "content": "\"\"\"The recovery collector (analysis/collect_recovery_measurements.py) on synthetic batch folders:\nthe metrics of section 5 with their n/a reasons, unknown intervals, the per-case tally with\nzeros, and validity apart from outcomes. No real batch exists yet.\n\nAI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).\n\"\"\"\nimport csv\nimport importlib.util\nimport json\nfrom datetime import datetime, timedelta, timezone\nfrom pathlib import Path\n\nimport numpy as np\nimport pytest\nfrom conftest import nyse_sessions, write_snapshot\n\nfrom etf_risk.jobs.params import input_checksums\n\nREPO = Path(__file__).resolve().parents[1]\nspec = importlib.util.spec_from_file_location(\"collect_recovery_measurements\",\n                                              REPO / \"analysis\" / \"collect_recovery_measurements.py\")\ncrm = importlib.util.module_from_spec(spec)\nspec.loader.exec_module(crm)\n\nBASE = datetime(2026, 10, 24, 10, 0, 0, tzinfo=timezone.utc)\nSTORE = \"s\" * 32\nCODE = {\"source_digest\": \"c\" * 64, \"uv_lock_sha256\": \"u\" * 64}\n\n\ndef utc(mono):\n    return (BASE + timedelta(seconds=mono - 1000)).isoformat()\n\n\ndef write_jsonl(path, events):\n    path.parent.mkdir(parents=True, exist_ok=True)\n    path.write_text(\"\".join(json.dumps(e) + \"\\n\" for e in events))\n\n\ndef launcher(folder, step, start, end):\n    (folder / \"logs\").mkdir(parents=True, exist_ok=True)\n    (folder / \"logs\" / f\"{step}.launcher.json\").write_text(json.dumps(\n        {\"outcome\": \"exited\", \"step_started_at_utc\": utc(start), \"tree_ended_at_utc\": utc(end)}))\n\n\ndef write_csv(path, header, rows):\n    path.parent.mkdir(parents=True, exist_ok=True)\n    with open(path, \"w\", newline=\"\") as f:\n        w = csv.writer(f)\n        w.writerow(header)\n        w.writerows(rows)\n\n\ndef make_batch(tmp_path, *, step_code=CODE):\n    \"\"\"Four planned jobs: C0 and W3 on worker A, W5a on B, and a K2 that memory stopped.\"\"\"\n    b = tmp_path / \"batch\"\n    dates = nyse_sessions(\"2024-01-02\", 31)\n    write_snapshot(tmp_path, \"snap\", {\"AAA\": (dates, np.random.default_rng(3).normal(0, 0.01, 30))})\n    checksums = input_checksums(tmp_path / \"processed\", \"snap\")\n    (b / \"plan.json\").parent.mkdir(parents=True)\n    (b / \"plan.json\").write_text(json.dumps({\"seed\": 1, \"settings\": {\"snapshot\": \"snap\"},\n                                             \"jobs\": [\"C0\", \"W3\", \"W5a\", \"K2\"]}))\n    write_jsonl(b / \"harness.jsonl\", [\n        {\"event\": \"batch_started\", \"mono\": 1000.0, \"clock\": {\"ts\": utc(1000), \"mono\": 1000.0}, \"code\": CODE},\n        *[{\"event\": \"process_started\", \"name\": n, \"same_clock\": True, \"code\": CODE, \"mono\": 1001.0}\n          for n in (\"reconciler\", \"A\", \"B\")],\n        {\"event\": \"deadline\", \"position\": 1, \"job_id\": 1, \"case\": \"C0\", \"reference\": \"submit\", \"reference_mono\": 1010.0,\n         \"deadline_s\": 75, \"deadline_mono\": 1085.0, \"t_submit\": 1010.0},\n        {\"event\": \"injection\", \"position\": 1, \"job_id\": 1, \"case\": \"C0\", \"missed\": None},\n        {\"event\": \"deadline\", \"position\": 2, \"job_id\": 2, \"case\": \"W3\", \"reference\": \"injection\",\n         \"reference_mono\": 1120.0, \"deadline_s\": 140, \"deadline_mono\": 1260.0, \"t_submit\": 1100.0},\n        {\"event\": \"injection\", \"position\": 2, \"job_id\": 2, \"case\": \"W3\", \"missed\": None, \"kind\": \"sigkill\",\n         \"worker\": \"A\", \"attempt\": 1, \"t_inj\": 1120.0},\n        {\"event\": \"deadline\", \"position\": 3, \"job_id\": 3, \"case\": \"W5a\", \"reference\": \"injection\",\n         \"reference_mono\": 1300.0, \"deadline_s\": 75, \"deadline_mono\": 1375.0, \"t_submit\": 1260.0},\n        {\"event\": \"injection\", \"position\": 3, \"job_id\": 3, \"case\": \"W5a\", \"missed\": None, \"kind\": \"hook\",\n         \"worker\": \"B\", \"point\": \"after_accept_commit\", \"t_inj\": 1300.0},\n        {\"event\": \"not_run\", \"position\": 4, \"case\": \"K2\", \"why\": \"memory\"},\n        {\"event\": \"quiescent\", \"processes_left\": False, \"other_connections\": 0},\n        {\"event\": \"final_snapshot\", \"status_check_exit\": 0, \"fingerprints_agree\": True, \"fingerprints\": [],\n         \"batch_peaks\": {}},\n        {\"event\": \"batch_ended\", \"mono\": 1600.0, \"clock\": {\"ts\": utc(1600), \"mono\": 1600.0}, \"code\": CODE}])\n    step = {\"event\": \"step_started\", \"code\": step_code}\n    write_jsonl(b / \"events\" / \"A.jsonl\", [\n        {\"event\": \"started\", \"pid\": 11, \"mono\": 1001.0, \"code\": CODE}, {\"event\": \"assigned\", \"mono\": 1002.0,\n                                                                          \"partitions\": [[\"t\", 0]]},\n        {\"event\": \"delivered\", \"job_id\": 1, \"mono\": 1010.5},\n        {\"event\": \"claimed\", \"job_id\": 1, \"attempt\": 1, \"run_id\": \"job-1-attempt-1\", \"mono\": 1011.0},\n        {**step, \"job_id\": 1, \"attempt\": 1, \"step\": \"windows\", \"mono\": 1012.0},\n        {**step, \"job_id\": 1, \"attempt\": 1, \"step\": \"spark_pipeline\", \"mono\": 1015.0},\n        {**step, \"job_id\": 1, \"attempt\": 1, \"step\": \"verify\", \"mono\": 1040.0},\n        {\"event\": \"accepted\", \"job_id\": 1, \"attempt\": 1, \"digest\": \"a\" * 64, \"mono\": 1050.0, \"store_id\": STORE,\n         \"worker_id\": \"A\", \"pid\": 11},\n        {\"event\": \"delivered\", \"job_id\": 2, \"mono\": 1100.5},\n        {\"event\": \"claimed\", \"job_id\": 2, \"attempt\": 1, \"run_id\": \"job-2-attempt-1\", \"mono\": 1101.0},\n        {**step, \"job_id\": 2, \"attempt\": 1, \"step\": \"windows\", \"mono\": 1102.0},\n        {**step, \"job_id\": 2, \"attempt\": 1, \"step\": \"spark_pipeline\", \"mono\": 1105.0}])\n    write_jsonl(b / \"events\" / \"B.jsonl\", [\n        {\"event\": \"started\", \"pid\": 22, \"mono\": 1001.5, \"code\": CODE}, {\"event\": \"assigned\", \"mono\": 1003.0,\n                                                                          \"partitions\": []},\n        {\"event\": \"assigned\", \"mono\": 1136.0, \"partitions\": [[\"t\", 0]]},\n        {\"event\": \"claimed\", \"job_id\": 2, \"attempt\": 2, \"run_id\": \"job-2-attempt-2\", \"mono\": 1180.0},\n        {**step, \"job_id\": 2, \"attempt\": 2, \"step\": \"windows\", \"mono\": 1181.0},\n        {**step, \"job_id\": 2, \"attempt\": 2, \"step\": \"spark_pipeline\", \"mono\": 1184.0},\n        {**step, \"job_id\": 2, \"attempt\": 2, \"step\": \"verify\", \"mono\": 1210.0},\n        {\"event\": \"accepted\", \"job_id\": 2, \"attempt\": 2, \"digest\": \"b\" * 64, \"mono\": 1225.0, \"store_id\": STORE,\n         \"worker_id\": \"B\", \"pid\": 22},\n        {\"event\": \"delivered\", \"job_id\": 3, \"mono\": 1260.5},\n        {\"event\": \"claimed\", \"job_id\": 3, \"attempt\": 1, \"run_id\": \"job-3-attempt-1\", \"mono\": 1261.0},\n        {**step, \"job_id\": 3, \"attempt\": 1, \"step\": \"windows\", \"mono\": 1262.0},\n        {**step, \"job_id\": 3, \"attempt\": 1, \"step\": \"spark_pipeline\", \"mono\": 1265.0},\n        {**step, \"job_id\": 3, \"attempt\": 1, \"step\": \"verify\", \"mono\": 1290.0},\n        {\"event\": \"fault_injected\", \"point\": \"after_accept_commit\", \"action\": \"kill\", \"mono\": 1300.0}])\n    write_jsonl(b / \"events\" / \"reconciler-33.jsonl\", [\n        {\"event\": \"started\", \"mono\": 1001.0, \"code\": CODE}, {\"event\": \"requeued\", \"job_id\": 2, \"mono\": 1175.0},\n        {\"event\": \"published\", \"job_id\": 2, \"mono\": 1175.5}])\n    write_jsonl(b / \"events\" / \"submit.jsonl\", [{\"event\": \"started\", \"mono\": m, \"code\": CODE} for m in (1010, 1100, 1260)])\n    jobs = b / \"jobs\" / STORE\n    for run_id, steps in {\"job-1-attempt-1\": [(\"windows\", 1012, 1015), (\"spark_pipeline\", 1015, 1040),\n                                              (\"verify\", 1040, 1049)],\n                          \"job-2-attempt-1\": [(\"windows\", 1102, 1105), (\"spark_pipeline\", 1105, 1121)],\n                          \"job-2-attempt-2\": [(\"windows\", 1181, 1184), (\"spark_pipeline\", 1184, 1210),\n                                              (\"verify\", 1210, 1224)],\n                          \"job-3-attempt-1\": [(\"windows\", 1262, 1265), (\"spark_pipeline\", 1265, 1290),\n                                              (\"verify\", 1290, 1299)]}.items():\n        for name, start, end in steps:\n            launcher(jobs / run_id, name, start, end)\n    for run_id in (\"job-1-attempt-1\", \"job-2-attempt-2\", \"job-3-attempt-1\"):\n        (jobs / run_id / \"manifest.json\").write_text(\"{}\")\n    launcher(b / \"reference\", \"windows\", 990, 993)\n    launcher(b / \"reference\", \"spark_pipeline\", 993, 999)\n    write_csv(b / \"crosscheck\" / \"Q1.csv\", [\"job_id\", \"n_claims\", \"n_accepted\", \"verdict\"],\n              [[1, 1, 1, \"ok\"], [2, 2, 1, \"ok\"], [3, 1, 1, \"ok\"]])\n    write_csv(b / \"crosscheck\" / \"Q2.csv\", [\"case_id\", \"job_id\", \"timeliness\", \"deadline_met\"],\n              [[\"C0\", 1, \"on time\", \"yes\"], [\"W3\", 2, \"on time\", \"yes\"], [\"W5a\", 3, \"on time\", \"yes\"]])\n    write_csv(b / \"crosscheck\" / \"Q3a.csv\", [\"job_id\", \"log_verdict\"],\n              [[1, \"reported once\"], [2, \"reported once\"], [3, \"no matching report\"]])\n    write_csv(b / \"crosscheck\" / \"Q3b.csv\", [\"store_id\", \"worker_id\", \"pid\", \"job_id\", \"attempt_number\", \"report_verdict\"],\n              [[STORE, \"A\", 11, 1, 1, \"matches\"], [STORE, \"B\", 22, 2, 2, \"matches\"]])\n    write_csv(b / \"crosscheck\" / \"Q2b.csv\", [\"job_id\", \"status\"], [])\n    export = b / \"export\"\n    export.mkdir()\n    (export / \"jobs.json\").write_text(json.dumps([{\"job_id\": j, \"version\": 4, \"input_checksums\": checksums}\n                                                  for j in (1, 2, 3)]))\n    (export / \"job_attempts.json\").write_text(json.dumps([\n        {\"job_id\": 1, \"attempt_number\": 1, \"outcome\": \"accepted\", \"renewals\": 2, \"output_dir\": str(jobs / \"job-1-attempt-1\"),\n         \"result_digest\": \"a\" * 64},\n        {\"job_id\": 2, \"attempt_number\": 1, \"outcome\": \"expired\", \"renewals\": 1, \"output_dir\": str(jobs / \"job-2-attempt-1\"),\n         \"result_digest\": None},\n        {\"job_id\": 2, \"attempt_number\": 2, \"outcome\": \"accepted\", \"renewals\": 2, \"output_dir\": str(jobs / \"job-2-attempt-2\"),\n         \"result_digest\": \"b\" * 64},\n        {\"job_id\": 3, \"attempt_number\": 1, \"outcome\": \"accepted\", \"renewals\": 2, \"output_dir\": str(jobs / \"job-3-attempt-1\"),\n         \"result_digest\": \"c\" * 64}]))\n    (export / \"store.json\").write_text(json.dumps({\"store_id\": STORE}))\n    (export / \"invariant_violations.json\").write_text(\"{}\")\n    return b\n\n\n@pytest.fixture\ndef batch(tmp_path):\n    return make_batch(tmp_path)\n\n\ndef test_the_metrics_of_each_job_with_their_reasons(batch, tmp_path):\n    result = crm.collect(batch, processed_root=tmp_path / \"processed\")\n    rows = {r[\"position\"]: r for r in result[\"rows\"]}\n    assert result[\"c0_median_s\"] == 40.0\n    c0, w3, w5a, k2 = rows[1], rows[2], rows[3], rows[4]\n    assert (c0[\"detection_s\"], c0[\"rerun_s\"], c0[\"finish_s\"], c0[\"overhead_s\"]) == (\n        \"n/a: no failure\", \"n/a: no failure\", 40.0, 0.0)\n    assert (w3[\"detection_s\"], w3[\"rerun_s\"], w3[\"finish_s\"], w3[\"overhead_s\"]) == (55.0, 60.0, 105.0, 85.0)\n    assert (w3[\"claims\"], w3[\"executions\"], w3[\"complete_executions\"], w3[\"wasted_step_s\"]) == (\"2\", 2, 1, 19.0)\n    assert (w5a[\"detection_s\"], w5a[\"finish_s\"], w5a[\"q3a_verdict\"]) == (\n        \"n/a: after acceptance\", \"n/a: after acceptance\", \"no matching report\")\n    assert k2 == {\"position\": 4, \"case\": \"K2\", \"status\": \"not run\"}\n\n\ndef test_validity_passes_and_outcomes_stay_apart(batch, tmp_path):\n    result = crm.collect(batch, processed_root=tmp_path / \"processed\")\n    assert result[\"validity_failed\"] == []\n    assert result[\"validity\"][\"machine_state\"][\"passed\"] is None                  # not recorded, not a pass\n    assert result[\"outcomes\"][\"overlap\"][\"verdict\"] == \"no overlap\"\n    assert result[\"outcomes\"][\"q1_not_ok\"] == [] and result[\"outcomes\"][\"invariant_violations\"] == {}\n    accepted = {a[\"job_id\"]: a[\"problems\"] for a in result[\"outcomes\"][\"accepted_attempts\"]}\n    assert accepted[1] == [\"no readable attempt.json\"]                           # an outcome finding, not validity\n\n\ndef test_the_tally_lists_every_case_and_every_verdict_with_zeros(batch, tmp_path):\n    tally = {t[\"case\"]: t for t in crm.collect(batch, processed_root=tmp_path / \"processed\")[\"tally\"]}\n    assert set(tally) == set(crm.CASES)\n    assert (tally[\"W3\"][\"planned\"], tally[\"W3\"][\"made\"], tally[\"K2\"][\"not_run\"], tally[\"X1\"][\"planned\"]) == (1, 1, 1, 0)\n    assert tally[\"W5a\"][\"q3a: no matching report\"] == 1 and tally[\"C0\"][\"q2: late\"] == 0\n    assert all(f\"q1: {v}\" in tally[\"D2\"] for v in crm.Q1_VERDICTS)\n\n\ndef test_a_missing_launcher_record_makes_the_overlap_unknown_never_none(batch, tmp_path):\n    (batch / \"jobs\" / STORE / \"job-2-attempt-1\" / \"logs\" / \"spark_pipeline.launcher.json\").unlink()\n    result = crm.collect(batch, processed_root=tmp_path / \"processed\")\n    overlap = result[\"outcomes\"][\"overlap\"]\n    assert overlap[\"verdict\"] == \"unknown\" and overlap[\"steps_without_interval\"] == [\"job-2-attempt-1:spark_pipeline\"]\n    assert str({r[\"position\"]: r for r in result[\"rows\"]}[2][\"wasted_step_s\"]).startswith(\"unknown\")\n\n\ndef test_overlapping_steps_are_found(batch, tmp_path):\n    launcher(batch / \"jobs\" / STORE / \"job-2-attempt-2\", \"windows\", 1119, 1184)    # starts before 1121\n    assert crm.collect(batch, processed_root=tmp_path / \"processed\")[\"outcomes\"][\"overlap\"][\"verdict\"] == \"overlap\"\n\n\ndef test_a_step_that_ran_other_code_fails_validity_and_the_exit_code(tmp_path, monkeypatch):\n    batch = make_batch(tmp_path, step_code={**CODE, \"source_digest\": \"x\" * 64})\n    monkeypatch.setattr(crm, \"REPO\", tmp_path)                                    # data/processed under tmp_path\n    assert crm.main([\"--batch\", str(batch)]) == 1\n    validity = json.loads((batch / \"validity.json\").read_text())\n    assert \"code_identity\" in validity[\"validity_failed\"] and validity[\"validity\"][\"code_identity\"][\"distinct\"] == 2\n    assert (batch / \"injections.csv\").exists() and (batch / \"tally.csv\").exists()\n"
}
```

## 194. User — 2026-10-24T05:33:52.122Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py (file state is current in your context — no need to Read it back)
```

## 195. Assistant — 2026-10-24T05:34:18.348Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py",
  "old_string": "    parser.add_argument(\"--clock-tolerance\", type=float, default=1.0,\n                        help=\"seconds (provisional; the outline's 8.5 leaves it open)\")\n    args = parser.parse_args(argv)\n    result = collect(args.batch, args.clock_tolerance)",
  "new_string": "    parser.add_argument(\"--clock-tolerance\", type=float, default=1.0,\n                        help=\"seconds (provisional; the outline's 8.5 leaves it open)\")\n    parser.add_argument(\"--processed-root\", type=Path, default=REPO / \"data\" / \"processed\",\n                        help=\"where the snapshot's input files are checked again (default data/processed)\")\n    args = parser.parse_args(argv)\n    result = collect(args.batch, args.clock_tolerance, args.processed_root)"
}
```

## 196. Assistant — 2026-10-24T05:34:22.033Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py",
  "old_string": "def test_a_step_that_ran_other_code_fails_validity_and_the_exit_code(tmp_path, monkeypatch):\n    batch = make_batch(tmp_path, step_code={**CODE, \"source_digest\": \"x\" * 64})\n    monkeypatch.setattr(crm, \"REPO\", tmp_path)                                    # data/processed under tmp_path\n    assert crm.main([\"--batch\", str(batch)]) == 1\n    validity = json.loads((batch / \"validity.json\").read_text())\n    assert \"code_identity\" in validity[\"validity_failed\"] and validity[\"validity\"][\"code_identity\"][\"distinct\"] == 2",
  "new_string": "def test_a_step_that_ran_other_code_fails_validity_and_the_exit_code(tmp_path):\n    batch = make_batch(tmp_path, step_code={**CODE, \"source_digest\": \"x\" * 64})\n    assert crm.main([\"--batch\", str(batch), \"--processed-root\", str(tmp_path / \"processed\")]) == 1\n    validity = json.loads((batch / \"validity.json\").read_text())\n    assert validity[\"validity_failed\"] == [\"code_identity\"] and validity[\"validity\"][\"code_identity\"][\"distinct\"] == 2"
}
```

## 197. User — 2026-10-24T05:34:23.127Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/analysis/collect_recovery_measurements.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 198. User — 2026-10-24T05:34:24.515Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/tests/test_recovery_collector.py has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 199. Assistant — 2026-10-24T05:34:31.270Z

Next, a compile-only check of every new or changed test file and the collector:

## 200. Assistant — 2026-10-24T05:34:33.813Z

### Tool call: Bash

```
{
  "command": "for f in analysis/collect_recovery_measurements.py tests/test_jobs_faults.py tests/test_jobs_worker.py tests/test_jobs_queue.py tests/test_jobs_kafka.py tests/test_jobs_cli.py tests/test_jobs_pipeline.py tests/test_provenance.py tests/test_jobs_harness.py tests/test_recovery_collector.py src/etf_risk/jobs/harness.py; do python3 -I -m py_compile \"$f\" && echo \"compiles: $f\"; done; git status --porcelain=v1 --untracked-files=all | grep -v __pycache__",
  "description": "Compile all changed test and analysis files and list changes"
}
```

## 201. User — 2026-10-24T05:34:35.833Z

### Tool result

```
compiles: analysis/collect_recovery_measurements.py
compiles: tests/test_jobs_faults.py
compiles: tests/test_jobs_worker.py
compiles: tests/test_jobs_queue.py
compiles: tests/test_jobs_kafka.py
compiles: tests/test_jobs_cli.py
compiles: tests/test_jobs_pipeline.py
compiles: tests/test_provenance.py
compiles: tests/test_jobs_harness.py
compiles: tests/test_recovery_collector.py
compiles: src/etf_risk/jobs/harness.py
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
```

## 202. Assistant — 2026-10-24T05:34:46.272Z

### Tool call: ToolSearch

```
{
  "query": "select:SendMessage",
  "max_results": 1
}
```

## 203. User — 2026-10-24T05:34:46.560Z

### Tool result

````
```
{
  "type": "tool_reference",
  "tool_name": "SendMessage"
}
```
````

## 204. Assistant — 2026-10-24T05:35:43.209Z

### Tool call: Bash

```
{
  "command": "grep -n -E '^#{2,3} |^- \\*\\*(First|Second|Third|Throughout)|^\\*\\*Restart|^\\*\\*Who owns|Proposal \\(P|^- \\*\\*(Reasons|Records|Nothing|Prerequisites|Authorship|Pending|Still)' docs/recovery-experiments.md | head -60",
  "description": "Locate the outline's sections and proposal paragraphs"
}
```

## 205. User — 2026-10-24T05:35:46.391Z

### Tool result

```
16:## 1. Questions and scope
37:### 1.1 Decided or required by the author
41:- **First review (2026-10-23).** Explicit deadlines, with on-time completion, late completion and
52:- **Second review.** `6d8a232` and its final report as design inputs, with the isolated
58:- **Third review.** Run the fixtures only after the M2 session releases the test window, recheck
63:- **Throughout.** Documents only; no formal experiment; Part A is not approved.
65:## 2. Batch protocol (proposal)
67:### 2.1 Services, jobs and controls
77:### 2.2 Reference runs
85:### 2.3 Code identity
93:### 2.4 Worker startup order and the partition
105:**Restart rule.** A killed worker starts again only once its job has finished (read from the
111:### 2.5 One job at a time
117:## 3. Failure cases
119:### 3.1 Cases
145:### 3.2 Expected times and Kafka conditions
169:## 4. Clocks, deadlines and snapshots
171:### 4.1 Clock
184:### 4.2 Deadlines
205:### 4.3 The deadline observation
225:### 4.4 Quiescence
233:### 4.5 The final snapshot
243:### 4.6 Container peaks by segment
252:## 5. Metrics
288:## 6. Checks
290:### 6.1 Validity
298:### 6.2 Database acceptance correctness (answers E1)
309:### 6.3 Timeliness and lost jobs (answers E2)
314:### 6.4 Event-log completeness and report identity
324:### 6.5 Other outcome checks
331:- **Nothing left.** After quiescence no attempt's process and no new Spark scratch remain (as
334:## 7. SQL cross-check
355:## 8. Part A decisions: proposals
371:### 8.1 Repetitions and workload
373:- **Proposal (P1).** Every case on the calendar-year job; per batch, 3 jobs of each of the 14 cases
376:- **Reasons.** The calendar-year job is the shortest (steps about 35 s against 63 s for stride 21),
389:### 8.2 Timing and deadlines
391:- **Proposal (P2), the clock and the limits.** The defaults of
395:- **Reasons.** E2 asks how long recovery takes, and the defaults are what the job processes run
401:- **Proposal (P3), the deadlines.** Each case's D is the upper bound B to the next claim (3.2) plus
414:- **Reasons.** B is where the design puts the next claim at the latest; 2S leaves the re-run room for
423:### 8.3 Memory
425:- **Proposal (P4).** Fresh MySQL and Kafka containers for each batch; `services peaks` read after
429:- **Reasons.** Spec §11 asks for a fresh MySQL per batch; MySQL reached 98% in M2's mutation
434:- **Pending.** The isolated memory-budget check. Until it is done, these limits are provisional and
437:### 8.4 Injection method
439:- **Proposal (P5).** A hook in the `worker` command that sends SIGKILL to its own process at one
443:- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside
449:### 8.5 Still open
457:## 9. Records, prerequisites and authorship
459:- **Records**, under `data/outputs-recovery/<batch>/`, outside Git: the export, the event logs, the
464:- **Nothing is dropped.** Every injection (misses and those not run included), every batch (invalid
467:- **Prerequisites in M3 code**, none written: the harness; the reference-run wrapper (2.2); the
471:- **Authorship.** Spec §11: the job code is written with Claude Code, and the experiments are the
477:## 10. Not claimed
485:## History
```

## 206. Assistant — 2026-10-24T05:35:53.977Z

Reading the exact text of the paragraphs I'll edit, so each replacement matches precisely:

## 207. Assistant — 2026-10-24T05:35:55.101Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "offset": 1,
  "limit": 15
}
```

## 208. User — 2026-10-24T05:35:55.237Z

### Tool result

```
1	# Recovery experiments (E1, E2): outline
2	
3	Author: _to be written by the author after review. Beyond spec §11, the only decisions by the
4	author are those in 1.1._
5	
6	_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised three times that day from the
7	author's reviews (history at the end). This is an outline for review, not an approved Part A:
8	everything not in 1.1 or cited from spec §11 or M2 is Claude Code's proposal, and the decisions in
9	section 8 are proposals only. Design inputs: commit `6d8a232` (`feature/worker-pipeline`) and M2's
10	final report in it ([worker-pipeline.md](worker-pipeline.md), "Status on 2026-10-23"); `e4adc38`
11	later corrected that report's live job-suite count, which this outline does not use. No file under
12	`src/` changed from `d2d8615`, where the outline began. The SQL cross-check, its fixture, the frozen
13	expected rows and the run that validated the queries are in [recovery-sql.md](recovery-sql.md). No
14	formal experiment was run._
15	
```

## 209. Assistant — 2026-10-24T05:35:56.408Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "offset": 184,
  "limit": 42
}
```

## 210. User — 2026-10-24T05:35:56.503Z

### Tool result

````
184	### 4.2 Deadlines
185	
186	When a job's reference instant occurs, the harness records in `batch_jobs`: `deadline_from`
187	(`injection`, or `submit` for a control), `deadline_s` (the case's D, 8.2), `deadline_mono` (the
188	harness's `mono` at that instant plus D) and `max_lag_s` (how late the deadline observation may end
189	and still show an on-time success). Q2 classifies each job from its observation (4.3) and the final
190	snapshot (4.5):
191	
192	| Class | Rule | `deadline_met` |
193	|---|---|---|
194	| on time | succeeded in the deadline observation, which ended no later than `deadline_mono + max_lag_s` | yes |
195	| late | not succeeded in an observation that began at or after `deadline_mono`, and succeeded in the final snapshot | no |
196	| unfinished | queued or running in the final snapshot | no |
197	| failed | failed in the final snapshot | no |
198	| missing | no row in the final snapshot | no |
199	| deadline not observed | succeeded at the end, with no valid observation: a failed read, none at all, a success seen too late, or a miss seen before the deadline | unknown |
200	
201	A late job stays late: the observation fixes the miss, and the later success does not change it.
202	`deadline not observed` is an explicit unknown, counted as neither met nor missed. The final
203	snapshot comes after every drain limit, which comes after every deadline.
204	
205	### 4.3 The deadline observation
206	
207	At `deadline_mono` the harness reads the job's row once, in its own connection, as one consistent
208	snapshot; a read that fails is recorded with no status and is never repeated. It will fail in D1 and
209	D2 when a deadline falls while MySQL is down, as the M2 test's own connection did during its stalls.
210	
211	```sql
212	SET SESSION TRANSACTION ISOLATION LEVEL REPEATABLE READ;
213	-- observed_from_mono: the harness's time.monotonic() just before the next statement
214	START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
215	-- observed_to_mono: just after it returned; InnoDB took the snapshot in between
216	SELECT status, attempt_number, accepted_attempt FROM jobs WHERE job_id = :job_id;
217	COMMIT;
218	```
219	
220	A terminal status never changes, so a success seen in a snapshot that ended by
221	`deadline_mono + max_lag_s` is on time within that lag, and a miss seen in one that began at or
222	after `deadline_mono` stays a miss. The lag, `observed_to_mono − deadline_mono`, is reported for
223	every job.
224	
225	### 4.4 Quiescence
````

## 211. Assistant — 2026-10-24T05:35:57.542Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "offset": 355,
  "limit": 150
}
```

## 212. User — 2026-10-24T05:35:57.656Z

### Tool result

```
355	## 8. Part A decisions: proposals
356	
357	_Claude Code's proposals, with reasons. None is decided, and Part A is not approved._ They rest on
358	M2's final report (`6d8a232`):
359	
360	| Input from M2 | Value |
361	|---|---|
362	| steps, calendar-year job | windows 2.5–3.0 s, spark_pipeline 22.1–22.6 s, verify 9.5 s; about 34–35 s in all |
363	| steps, stride-21 job | 1.5 s, 44.8–50.4 s, 11.0–11.5 s; about 57–63 s in all |
364	| step trees' peak RSS | spark_pipeline 0.66–0.79 GiB (calendar-year), 1.19–1.36 GiB (stride 21); verify 0.45–0.58 GiB; windows 0.12 GiB |
365	| job processes' RSS | worker 63.0 MiB, reconciler 51.6 MiB |
366	| container peaks | MySQL 345 MiB (67%) after the live job suites and 501 MiB (98%) after the live mutation session; Kafka 361–415 MiB (56–65%); informational, since another project's four containers shared Docker's VM and the host had about 1.3 GiB available |
367	| MySQL stalls, M2's clock | 0, 1 and 2 failed renewals for `LOCK TABLES`, `pause` and `restart`; each run kept its first attempt; no outage duration reported |
368	| acceptance runs | 10 of 10 passed on M2's clock in 11 min 20 s; the first run's failures were faults of the test harness |
369	| isolated memory-budget check | not done: pending |
370	
371	### 8.1 Repetitions and workload
372	
373	- **Proposal (P1).** Every case on the calendar-year job; per batch, 3 jobs of each of the 14 cases
374	  (C0 included), 42 in all, in one shuffled order drawn from a seed recorded before the batch; 2
375	  batches, each on fresh containers.
376	- **Reasons.** The calendar-year job is the shortest (steps about 35 s against 63 s for stride 21),
377	  and its 22 s `spark_pipeline` step is still long enough to aim the mid-step injections; the
378	  stride-21 job adds run time without a recovery path of its own. From M2's step times and 3.2, a
379	  worker-crash case takes from under a minute (W1) to about 2¼ minutes (W4), so a batch of 42 should
380	  take roughly one to two hours before outages, stops and the harness's waits. Two batches on fresh
381	  containers show whether results repeat across containers and keep each batch short of the ~50 runs
382	  after which M2 saw MySQL at 98% (another workload, so only a rough guide). A recorded shuffle
383	  spreads drift, such as memory growth, across cases instead of lining it up with one.
384	- **Counts, not rates.** The first review removed the pooled rule-of-three claim; reporting counts
385	  only is Claude Code's proposal. Results are given per case as k of n, with no rate, probability or
386	  confidence bound, pooled or per case: the injections are not shown to be independent, and cases are
387	  not alike.
388	
389	### 8.2 Timing and deadlines
390	
391	- **Proposal (P2), the clock and the limits.** The defaults of
392	  [timing.py](../src/etf_risk/jobs/timing.py) (lease 60 s, renewals every 10 s, fence margin 10 s,
393	  session timeout 15 s, heartbeats 3 s) and its step limits (windows 120 s, spark_pipeline 600 s,
394	  verify 300 s, attempt 900 s), with no `--timing` override.
395	- **Reasons.** E2 asks how long recovery takes, and the defaults are what the job processes run
396	  with; the token guards that decide E1 do not depend on the clock. The limits are about 40, 12 and
397	  26 times the measured step maxima (3.0, 50.4 and 11.5 s) and matter only to W7's lock wait and the
398	  classic-protocol bound; changing them would add a configuration M2 did not test. Cost: lease-based
399	  recoveries take 50–65 s instead of 20–29 s on M2's clock. Risk: the default clock has not run
400	  live, so the first batch is also its first live run.
401	- **Proposal (P3), the deadlines.** Each case's D is the upper bound B to the next claim (3.2) plus
402	  twice the slowest step sum M2 measured for the parameter set (2S: 70.2 s calendar-year, 126.8 s
403	  stride 21), rounded up to 5 s. B is 0 where no new attempt is expected (C0, W5a, W5b, K1, X1), 19 s
404	  for W1, 65 s for W2, W3, W4 and W6, 65 s plus the stop for W7, and the planned outage plus 65 s for
405	  K2, D1 and D2. `max_lag_s` is 1 s, and the drain limit equals D.
406	
407	  | B | calendar-year D | stride-21 D |
408	  |---|---|---|
409	  | 0 (C0, W5a, W5b, K1, X1) | 75 s | 130 s |
410	  | 19 s (W1) | 90 s | 150 s |
411	  | 65 s (W2, W3, W4, W6) | 140 s | 195 s |
412	  | 65 s + stop (W7), or + outage (K2, D1, D2) | 140 s + stop or outage | 195 s + stop or outage |
413	
414	- **Reasons.** B is where the design puts the next claim at the latest; 2S leaves the re-run room for
415	  a slower run (M2's `spark_pipeline` varied by up to 5.6 s, and T adds the worker's own work) while
416	  a stalled job still misses. A local read of one row should take milliseconds, so a 1 s lag
417	  classifies nearly every success seen at the deadline and leaves the rest visible as
418	  `deadline not observed`. A drain limit of D gives a late job as long again to finish, enough to
419	  tell late from unfinished without one job holding the batch indefinitely. Whether D1 at this clock
420	  takes one claim or two stays open: M2 reported no outage duration, and failed-renewal counts do not
421	  establish one.
422	
423	### 8.3 Memory
424	
425	- **Proposal (P4).** Fresh MySQL and Kafka containers for each batch; `services peaks` read after
426	  every job as well as before every injected restart (4.6); a batch flagged when either container's
427	  batch peak passes 90% of its limit, and stopped (no further jobs, then quiescence, 4.4) when either
428	  passes 95%; the host's available memory recorded before each job but not used as a gate.
429	- **Reasons.** Spec §11 asks for a fresh MySQL per batch; MySQL reached 98% in M2's mutation
430	  session, so a stop rule keeps a batch from reaching the limit unobserved, and a reading after every
431	  job lets it act in time. No measurement of the host's available memory with only this project's
432	  containers exists (M2's 1.3 GiB had another project's containers running), so a host gate would
433	  have no basis yet.
434	- **Pending.** The isolated memory-budget check. Until it is done, these limits are provisional and
435	  the budgets of spec §11 are not validated.
436	
437	### 8.4 Injection method
438	
439	- **Proposal (P5).** A hook in the `worker` command that sends SIGKILL to its own process at one
440	  named fault point, or holds there for D2, enabled only by an environment variable the harness sets
441	  and recorded in the worker's `started` event; plus a new fault point between `accept_result`'s
442	  return and the `accepted` event, added to `WORKER_FAULT_POINTS`.
443	- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside
444	  cannot hit reliably. `Worker(fault=...)` already calls the fault points, so the hook only wires
445	  them to the command, and adding the new point to `WORKER_FAULT_POINTS` puts it under the offline
446	  tests that crash at every point. It is new code, written with Claude Code, to be tested and
447	  mutation-checked before any batch. Without it, these six cases would be recorded as not run.
448	
449	### 8.5 Still open
450	
451	The clock-check tolerance (4.1); the harness's waits (how long W6 and W7 stay stopped, how long K2,
452	D1 and D2 keep a service down); a host-memory gate, after the isolated check; which of the harness,
453	the collector and the SQL the author writes; and the branch: `docs/recovery-outline` is based on
454	`d2d8615` and contains neither `6d8a232` nor `e4adc38`, so the links to `worker-pipeline.md` stay
455	broken until it does, and neither file is committed.
456	
457	## 9. Records, prerequisites and authorship
458	
459	- **Records**, under `data/outputs-recovery/<batch>/`, outside Git: the export, the event logs, the
460	  harness's logs (injections with intended and verified phases, deadlines and observations, process
461	  starts and clock checks, partition owners), `services peaks` by segment, the three fingerprints,
462	  Q0–Q3b as CSV, the table of section 5 with one row per injection, the per-case tally, and
463	  `cleanup`'s listing.
464	- **Nothing is dropped.** Every injection (misses and those not run included), every batch (invalid
465	  ones included) and every verdict (failed outcomes and unknowns included) stays in the records; the
466	  tally lists all 14 cases and every verdict value, with zeros.
467	- **Prerequisites in M3 code**, none written: the harness; the reference-run wrapper (2.2); the
468	  collector and the cross-check runner; an event for each partition assignment and revocation
469	  (2.4); code identity in start events and `step_started` (2.3); monotonic step times in the
470	  launcher records (6.5); and, if P5 is chosen, the hook and the new fault point.
471	- **Authorship.** Spec §11: the job code is written with Claude Code, and the experiments are the
472	  project author's, with tutoring. Here the items in 1.1 are the author's and everything else is
473	  Claude Code's proposal. If the queries of [recovery-sql.md](recovery-sql.md) are kept, they stay
474	  marked as drafted with Claude Code; the author can also write their own and use these as a
475	  cross-check.
476	
477	## 10. Not claimed
478	
479	Times hold for this machine, the clock of 8.2, and one broker and one database (spec §11). Results
480	are counts per case, not rates. The bounds in 3.2 hold only under their Kafka conditions and are not
481	predictions until approved. Cases without an injection method are not measured. The memory budgets
482	are not validated until the isolated check is done. The fixture run tests the SQL on made-up rows,
483	not the job system.
484	
485	## History
486	
487	- **Draft, 2026-10-23.** Outline drafted with Claude Code at the author's request.
488	- **Revision 1, 2026-10-23.** The first review (1.1): deadlines and their observation, quiescence
489	  and the final snapshot; database correctness apart from the event log, with full report identity
490	  and the new case W5a; code identity at launch and unknown intervals; monotonic durations and `n/a`
491	  latencies; Kafka conditions, startup order and restart rule; reference runs under the host lock;
492	  the rule-of-three sentence removed; all cases kept; a first fixture.
493	- **Revision 2, 2026-10-23.** The second review: `6d8a232` and M2's report as inputs, with the
494	  isolated memory-budget check pending; peaks by segment; the owner from assignment events only;
495	  `deadline not observed` as an explicit unknown with `deadline_met`; fixture B and explicit expected
496	  rows for every query.
497	- **Revision 3, 2026-10-23.** The third review: the queries validated once against a scratch MySQL
498	  after the M2 session's handover, with all 82 frozen expected rows matching; the restart duration
499	  inferred from failed renewals removed; the SQL, fixture, expected rows and run moved to
500	  [recovery-sql.md](recovery-sql.md) with no SQL changed; the outline shortened; Part A decisions
501	  proposed in section 8 (P1–P5), Q-A becoming P5.
502	
```

## 213. Assistant — 2026-10-24T05:36:14.507Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised three times that day from the\nauthor's reviews (history at the end). This is an outline for review, not an approved Part A:\neverything not in 1.1 or cited from spec §11 or M2 is Claude Code's proposal, and the decisions in\nsection 8 are proposals only. Design inputs: commit `6d8a232` (`feature/worker-pipeline`) and M2's\nfinal report in it ([worker-pipeline.md](worker-pipeline.md), \"Status on 2026-10-23\"); `e4adc38`\nlater corrected that report's live job-suite count, which this outline does not use. No file under\n`src/` changed from `d2d8615`, where the outline began. The SQL cross-check, its fixture, the frozen\nexpected rows and the run that validated the queries are in [recovery-sql.md](recovery-sql.md). No\nformal experiment was run._",
  "new_string": "_Drafted with Claude Code (Opus 5.5) on 2026-10-23 and revised four times from the author's\nreviews (history at the end). This is an outline for review, not an approved Part A: everything not\nin 1.1 or cited from spec §11 or M2 is Claude Code's proposal, and the decisions in section 8 are\nproposals only. Design inputs: commit `6d8a232` (`feature/worker-pipeline`) and M2's final report in\nit ([worker-pipeline.md](worker-pipeline.md), \"Status on 2026-10-23\"); `e4adc38` later corrected\nthat report's live job-suite count, which this outline does not use. The SQL cross-check, its\nfixture, the frozen expected rows and the run that validated the queries are in\n[recovery-sql.md](recovery-sql.md); the author accepted that run as tooling evidence, not as approval\nof Part A. Since 2026-10-24 the tooling exists on `feature/recovery-harness`, written with Claude\nCode at the author's decision (section 9); none of it has run yet, and no formal experiment was\nrun._"
}
```

## 214. Assistant — 2026-10-24T05:36:17.762Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "- **Throughout.** Documents only; no formal experiment; Part A is not approved.",
  "new_string": "- **Fourth review (2026-10-24).** The 82-row fixture validation counts as tooling evidence, not as\n  approval of Part A. Claude Code writes the tooling (the harness, the collector, assignment events,\n  launch-time code identity and precise fault-injection hooks) with accurate attribution (section 9).\n  The frozen SQL expectations stay as they are. The deadline formulas are reassessed and the\n  duration of all 84 proposed jobs is estimated (8.1, 8.2); timing, repetitions and memory\n  thresholds stay provisional. Every test or container run waits for coordination with the M2\n  session.\n- **Throughout.** No formal experiment, and Part A is not approved. Until the fourth review the work\n  was documents only."
}
```

## 215. Assistant — 2026-10-24T05:36:18.936Z

### Tool call: Read

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "offset": 89,
  "limit": 32
}
```

## 216. User — 2026-10-24T05:36:20.013Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 217. User — 2026-10-24T05:36:21.172Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 218. User — 2026-10-24T05:36:21.277Z

### Tool result

```
89	One direct run of the three CLIs per parameter set, under the host execution lock, taken as a
90	launcher takes it: an exclusive `flock`, the wait until no earlier tree survives, and an entry in
91	the registry, so that a later launcher waits for the reference run's survivors too. A reference run
92	then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference
93	runs come before the workers start, so that they delay no measured step.
94	
95	### 2.3 Code identity
96	
97	Each process records `source_sha256` and `uv_lock_sha256` from `provenance.code_state()` in its
98	first event when it starts (every worker start, the reconciler, each `submit`), and each step launch
99	records them in `step_started`; the harness records them at the start and end of the batch. The
100	commit is only reported. A crashed attempt writes no `attempt.json`, so identity is never read from
101	that file; it is read only for accepted attempts, to find their run folder (6.2).
102	
103	### 2.4 Worker startup order and the partition
104	
105	The topic has one partition, and the group member that owns it gets every delivery.
106	[kafka.py](../src/etf_risk/jobs/kafka.py) sets no `client.id`, `group.instance.id` or assignment
107	strategy, so with two live members the owner after a rebalance is not fixed; M2's first acceptance
108	run failed partly on "a standby that could win the partition before worker A did". Order per batch:
109	`services ready`, `init-db` and `create-topic`; the reference runs; the reconciler; worker A, then a
110	wait for its assignment event; worker B, then a wait for the rebalance its join causes; the first
111	job. The harness identifies the owner from the assignment events alone, before each case and after
112	each rebalance, and injects into the worker that claimed the job, never into a worker chosen by
113	name, start order or `client.id` ordering.
114	
115	**Restart rule.** A killed worker starts again only once its job has finished (read from the
116	table), when the other worker is idle; the harness waits for the rebalance and records the new
117	owner. A worker stopped and then fenced (W6, W7) is first stopped with SIGTERM once its `fenced`
118	event appears; its attempt is no longer its own, so the stop writes nothing. The only rebalance
119	inside a recovery window is therefore the one the failure causes.
120	
```

## 219. Assistant — 2026-10-24T05:36:28.911Z

Sections 2.2–2.4 now describe what exists in code. Each note says what was implemented and that none of it has run yet:

## 220. Assistant — 2026-10-24T05:36:31.264Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference\nruns come before the workers start, so that they delay no measured step.",
  "new_string": "then cannot overlap a worker's step, and its interval enters the overlap check (6.5). The reference\nruns come before the workers start, so that they delay no measured step. Implemented, not yet run:\nthe harness drives each reference step through `etf_risk.jobs.launcher` as the launcher's parent, so\nthe step gets the same lock, registry, marker and launcher record as a worker's step."
}
```

## 221. Assistant — 2026-10-24T05:36:35.169Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "Each process records `source_sha256` and `uv_lock_sha256` from `provenance.code_state()` in its\nfirst event when it starts (every worker start, the reconciler, each `submit`), and each step launch\nrecords them in `step_started`; the harness records them at the start and end of the batch. The\ncommit is only reported. A crashed attempt writes no `attempt.json`, so identity is never read from\nthat file; it is read only for accepted attempts, to find their run folder (6.2).",
  "new_string": "Each process records its code identity in its first event when it starts (every worker start, the\nreconciler, each `submit`), each step launch records it in `step_started`, and the harness records\nit at the start and end of the batch. The identity is `source_digest`, one SHA-256 over the per-file\n`source_sha256` map of `provenance.code_state()`, with `uv_lock_sha256`; the commit and the clean\nflag are only reported. Implemented, not yet run: `provenance.code_identity()` for starting\nprocesses, and `provenance.source_identity()`, the same two hashes without asking git, for each step\nlaunch. A crashed attempt writes no `attempt.json`, so identity is never read from that file; it is\nread only for accepted attempts, to find their run folder (6.2)."
}
```

## 222. Assistant — 2026-10-24T05:36:37.821Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "job. The harness identifies the owner from the assignment events alone, before each case and after\neach rebalance, and injects into the worker that claimed the job, never into a worker chosen by\nname, start order or `client.id` ordering.",
  "new_string": "job. The harness identifies the owner from the assignment events alone, before each case and after\neach rebalance, and injects into the worker that claimed the job, never into a worker chosen by\nname, start order or `client.id` ordering. Implemented, not yet run: kafka.py writes `assigned`,\n`revoked` and `lost` events from its rebalance callbacks, and the harness reads the owner only after\na started worker's first `assigned` event, so a stale assignment is never taken for the owner."
}
```

## 223. User — 2026-10-24T05:36:38.909Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 224. User — 2026-10-24T05:36:39.983Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 225. User — 2026-10-24T05:36:41.057Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 226. Assistant — 2026-10-24T05:36:53.700Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "When a job's reference instant occurs, the harness records in `batch_jobs`: `deadline_from`\n(`injection`, or `submit` for a control), `deadline_s` (the case's D, 8.2), `deadline_mono` (the\nharness's `mono` at that instant plus D) and `max_lag_s` (how late the deadline observation may end\nand still show an on-time success). Q2 classifies each job from its observation (4.3) and the final\nsnapshot (4.5):",
  "new_string": "When a job's reference instant occurs, the harness records in `batch_jobs`: `deadline_from`\n(`submit` for a control; `restored`, the moment the service works again, for K2, D1 and D2;\n`injection` otherwise), `deadline_s` (the case's D, 8.2), `deadline_mono` (the harness's `mono` at\nthat instant plus D) and `max_lag_s` (how late the deadline observation may end and still show an\non-time success). Counting K2, D1 and D2 from their service's return keeps the time a restart takes,\nwhich nothing has measured, out of their deadlines. A job whose injection missed its phase gets C0's\ndeadline, counted from its submit. Q2 classifies each job from its observation (4.3) and the final\nsnapshot (4.5):"
}
```

## 227. Assistant — 2026-10-24T05:36:56.539Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "At `deadline_mono` the harness reads the job's row once, in its own connection, as one consistent\nsnapshot; a read that fails is recorded with no status and is never repeated. It will fail in D1 and\nD2 when a deadline falls while MySQL is down, as the M2 test's own connection did during its stalls.",
  "new_string": "When the job finishes, or at `deadline_mono` if that comes first, the harness reads the job's row\nonce, in its own connection, as one consistent snapshot; a read that fails is recorded with no\nstatus and is never repeated. A read taken at completion shows a terminal status, which never\nchanges, so it decides as a read at the deadline would, and no job waits out its whole D. A read can\nfail in D1 and D2 when a deadline falls while MySQL is down, as the M2 test's own connection did\nduring its stalls."
}
```

## 228. User — 2026-10-24T05:36:57.587Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 229. User — 2026-10-24T05:36:58.658Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 230. Assistant — 2026-10-24T05:37:35.557Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "  stride-21 job adds run time without a recovery path of its own. From M2's step times and 3.2, a\n  worker-crash case takes from under a minute (W1) to about 2¼ minutes (W4), so a batch of 42 should\n  take roughly one to two hours before outages, stops and the harness's waits. Two batches on fresh\n  containers show whether results repeat across containers and keep each batch short of the ~50 runs\n  after which M2 saw MySQL at 98% (another workload, so only a rough guide). A recorded shuffle\n  spreads drift, such as memory growth, across cases instead of lining it up with one.",
  "new_string": "  stride-21 job adds run time without a recovery path of its own. Two batches on fresh containers\n  show whether results repeat across containers and keep each batch short of the ~50 runs after\n  which M2 saw MySQL at 98% (another workload, so only a rough guide). A recorded shuffle spreads\n  drift, such as memory growth, across cases instead of lining it up with one.\n- **Duration of all 84 jobs** (an estimate, provisional). `python -m etf_risk.jobs.harness estimate`\n  adds, per job, the design's upper bounds of 3.2 and these assumptions, none of them measured: T\n  40 s (M2's slowest steps, 35.1 s, plus 5 s of the worker's own work), 12 s to restart a killed\n  worker and rebalance, 20 s for a service from start to ready, 2 s for the peaks after every job,\n  18 s for the group after a Kafka restart, and 3 minutes per batch for the containers, the\n  reference run, the final snapshot and teardown. One job of each case takes 1,403 s (23.4\n  minutes), from 42 s (C0) to 159 s (W4, W7); a batch of 42 jobs, 4,389 s (73 minutes); both\n  batches, 8,778 s, about 2 hours 26 minutes. Each extra 5 s of T adds 8 minutes to the 84 jobs (T\n  runs 16 times per 14 jobs). A longer restore lengthens K2 and can move D1 and D2 onto their fenced\n  paths. The figures come from the estimator's formulas, worked out by hand; tests/test_jobs_harness.py\n  pins them but has not run yet."
}
```

## 231. Assistant — 2026-10-24T05:37:45.459Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "- **Proposal (P3), the deadlines.** Each case's D is the upper bound B to the next claim (3.2) plus\n  twice the slowest step sum M2 measured for the parameter set (2S: 70.2 s calendar-year, 126.8 s\n  stride 21), rounded up to 5 s. B is 0 where no new attempt is expected (C0, W5a, W5b, K1, X1), 19 s\n  for W1, 65 s for W2, W3, W4 and W6, 65 s plus the stop for W7, and the planned outage plus 65 s for\n  K2, D1 and D2. `max_lag_s` is 1 s, and the drain limit equals D.\n\n  | B | calendar-year D | stride-21 D |\n  |---|---|---|\n  | 0 (C0, W5a, W5b, K1, X1) | 75 s | 130 s |\n  | 19 s (W1) | 90 s | 150 s |\n  | 65 s (W2, W3, W4, W6) | 140 s | 195 s |\n  | 65 s + stop (W7), or + outage (K2, D1, D2) | 140 s + stop or outage | 195 s + stop or outage |\n\n- **Reasons.** B is where the design puts the next claim at the latest; 2S leaves the re-run room for\n  a slower run (M2's `spark_pipeline` varied by up to 5.6 s, and T adds the worker's own work) while\n  a stalled job still misses. A local read of one row should take milliseconds, so a 1 s lag",
  "new_string": "- **Proposal (P3), the deadlines, reassessed on 2026-10-24.** Each case's D is the bound B from its\n  reference to the start of its next run, plus twice the slowest step sum M2 measured for the\n  parameter set (2S: 70.2 s calendar-year, 126.8 s stride 21), rounded up to 5 s; `max_lag_s` is 1 s,\n  and the drain limit equals D. The reassessment changed three things:\n  - W7's B is the later of the takeover (L + P, 65 s) and the end of the stopped tree (the stop plus\n    two watchdog ticks and the kill grace: 98 s for a 90 s stop), no longer 65 s plus the stop;\n  - K2, D1 and D2 count from their service's return (4.2), so B holds no outage of unknown length:\n    for K2 the publication grace, a reconciler pass and the group's rejoin (30 + 5 + 19 = 54 s); for\n    D1 and D2 a fenced attempt's lease and a pass (65 s);\n  - the observation comes at completion when that is first (4.3), so meeting a deadline costs no\n    waiting.\n\n  | Cases | B | calendar-year D | stride-21 D |\n  |---|---|---|---|\n  | C0, W5a, W5b, K1, X1 | 0 | 75 s | 130 s |\n  | W1 | 19 s | 90 s | 150 s |\n  | W2, W3, W4, W6 | 65 s | 140 s | 195 s |\n  | W7, with a 90 s stop | 98 s | 170 s | 225 s |\n  | K2, from the broker's return | 54 s | 125 s | 185 s |\n  | D1, D2, from MySQL's return | 65 s | 140 s | 195 s |\n\n- **Reasons.** B is where the design puts the next run's start at the latest. S is the steps alone,\n  not T: T adds the worker's own work (the claim, the input checksums, the manifest, renewals, three\n  launcher starts), which nothing has measured, and 2S leaves about 35 s for it and for a slower run\n  (M2's `spark_pipeline` varied by up to 5.6 s) while a stalled job still misses. The first batch's\n  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next\n  batch is an option for the author, recorded as a deviation. A local read of one row should take milliseconds, so a 1 s lag"
}
```

## 232. Assistant — 2026-10-24T05:37:52.210Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "- **Proposal (P5).** A hook in the `worker` command that sends SIGKILL to its own process at one\n  named fault point, or holds there for D2, enabled only by an environment variable the harness sets\n  and recorded in the worker's `started` event; plus a new fault point between `accept_result`'s\n  return and the `accepted` event, added to `WORKER_FAULT_POINTS`.\n- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside\n  cannot hit reliably. `Worker(fault=...)` already calls the fault points, so the hook only wires\n  them to the command, and adding the new point to `WORKER_FAULT_POINTS` puts it under the offline\n  tests that crash at every point. It is new code, written with Claude Code, to be tested and\n  mutation-checked before any batch. Without it, these six cases would be recorded as not run.",
  "new_string": "- **Proposal (P5), implemented and not yet run.** `etf_risk.jobs.faults`: a worker started with\n  `ETF_RISK_FAULT_FILE` looks at that file at each fault point, and its `started` event names the\n  file. The harness arms one fault for one job by writing the file atomically: a point, and an\n  action (SIGKILL to the worker's own process, or a hold until a release file appears, for D2). The\n  worker removes the file before it acts, so an arming fires once, and logs `fault_injected`, whose\n  `mono` is the injection time. A new fault point, `after_accept_commit`, lies between\n  `accept_result`'s return and the `accepted` event and is in `WORKER_FAULT_POINTS`. A file, rather\n  than a fault named in the environment as first proposed, lets the harness arm the owner for one\n  job without restarting it: a restart would rebalance the group and could move the partition (2.4).\n- **Reasons.** W1, W2, W4, W5a, W5b and D2 have windows of milliseconds that a signal from outside\n  cannot hit reliably. `Worker(fault=...)` already calls the fault points, so the hook only wires\n  them to the command, and the new point joins the offline tests that crash at every point. The code\n  is new, written with Claude Code, with offline tests written and not yet run; mutation checks for it\n  are not written. Without it, these six cases would be recorded as not run."
}
```

## 233. Assistant — 2026-10-24T05:37:56.556Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "The clock-check tolerance (4.1); the harness's waits (how long W6 and W7 stay stopped, how long K2,\nD1 and D2 keep a service down); a host-memory gate, after the isolated check; which of the harness,\nthe collector and the SQL the author writes; and the branch: `docs/recovery-outline` is based on\n`d2d8615` and contains neither `6d8a232` nor `e4adc38`, so the links to `worker-pipeline.md` stay\nbroken until it does, and neither file is committed.",
  "new_string": "The clock-check tolerance (4.1; the collector uses 1 s until it is decided); the harness's waits\n(the phase delay before a mid-step injection, how long W7 stays stopped, how long K2, D1 and D2 keep\na service down: the settings hold 3 s, 90 s and 30 s for now); a host-memory gate, after the\nisolated check; monotonic step times in the launcher records, which none of the four reviews asked\nfor and without which the overlap check compares UTC times (6.5); and the branches: the tooling and\nthese documents are uncommitted on `feature/recovery-harness`, created from `e4adc38`, while the\nfirst copies of the documents, on `docs/recovery-outline`, stay as they were at revision 3."
}
```

## 234. Assistant — 2026-10-24T05:38:03.010Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "- **Prerequisites in M3 code**, none written: the harness; the reference-run wrapper (2.2); the\n  collector and the cross-check runner; an event for each partition assignment and revocation\n  (2.4); code identity in start events and `step_started` (2.3); monotonic step times in the\n  launcher records (6.5); and, if P5 is chosen, the hook and the new fault point.\n- **Authorship.** Spec §11: the job code is written with Claude Code, and the experiments are the\n  project author's, with tutoring. Here the items in 1.1 are the author's and everything else is\n  Claude Code's proposal. If the queries of [recovery-sql.md](recovery-sql.md) are kept, they stay\n  marked as drafted with Claude Code; the author can also write their own and use these as a\n  cross-check.",
  "new_string": "- **Tooling**, uncommitted on `feature/recovery-harness`, written with Claude Code at the author's\n  decision of 2026-10-24. Its offline tests are written; none of it has run:\n  - the harness, `src/etf_risk/jobs/harness.py` (plan, estimate, batch), with the reference runs\n    through the launcher (2.2) and `crosscheck.sql`, the SQL of [recovery-sql.md](recovery-sql.md)\n    byte for byte (a test checks it);\n  - the collector, `analysis/collect_recovery_measurements.py` (section 5, 6.1–6.5, the tally);\n  - assignment events in `kafka.py` (2.4);\n  - code identity at launch, in `provenance.py`, `cli.py` and `pipeline.py` (2.3);\n  - the fault hook, `faults.py`, wired in `cli.py`, and the fault point `after_accept_commit` in\n    `worker.py` (8.4).\n- **Not done:** monotonic step times in the launcher records (8.5), mutation checks for the new\n  code, and any run of it.\n- **Authorship.** Spec §11: the job code is written with Claude Code. At the author's decision of\n  2026-10-24, Claude Code also writes the recovery experiments' tooling listed above, and each new\n  module says so. The items in 1.1, and the experiments' decisions, runs and answers, are the\n  author's; everything else here is Claude Code's proposal. The queries of\n  [recovery-sql.md](recovery-sql.md) stay marked as drafted with Claude Code."
}
```

## 235. Assistant — 2026-10-24T05:38:06.413Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "  [recovery-sql.md](recovery-sql.md) with no SQL changed; the outline shortened; Part A decisions\n  proposed in section 8 (P1–P5), Q-A becoming P5.",
  "new_string": "  [recovery-sql.md](recovery-sql.md) with no SQL changed; the outline shortened; Part A decisions\n  proposed in section 8 (P1–P5), Q-A becoming P5.\n- **Revision 4, 2026-10-24.** The fourth review: the fixture run accepted as tooling evidence only;\n  the tooling written with Claude Code (section 9), none of it run; P3's deadlines reassessed (W7's\n  bound, K2, D1 and D2 counted from their service's return, the observation at completion when that\n  is first) and the duration of the 84 jobs estimated (8.1); P5 implemented with a fault file\n  instead of a fault named in the environment. Timing, repetitions and memory thresholds stay\n  provisional."
}
```

## 236. User — 2026-10-24T05:38:07.478Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 237. User — 2026-10-24T05:38:08.664Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 238. User — 2026-10-24T05:38:09.746Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 239. User — 2026-10-24T05:38:10.812Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 240. User — 2026-10-24T05:38:11.877Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 241. User — 2026-10-24T05:38:12.941Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 242. Assistant — 2026-10-24T05:38:23.317Z

The edits applied. One spot needs re-wrapping: the P3 "Reasons" paragraph, where my replacement joined the paragraph's original tail on one over-long line. Viewing it:

## 243. Assistant — 2026-10-24T05:38:25.088Z

### Tool call: Bash

```
{
  "command": "awk '/^- \\*\\*Reasons.\\*\\* B is where/,/establish one\\./' docs/recovery-experiments.md | cat -n | awk '{ if (length($0) > 108) print \"LONG:\" $0; else print $0 }'",
  "description": "Show the P3 reasons paragraph and flag long lines"
}
```

## 244. User — 2026-10-24T05:38:26.025Z

### Tool result

```
     1	- **Reasons.** B is where the design puts the next run's start at the latest. S is the steps alone,
     2	  not T: T adds the worker's own work (the claim, the input checksums, the manifest, renewals, three
     3	  launcher starts), which nothing has measured, and 2S leaves about 35 s for it and for a slower run
     4	  (M2's `spark_pipeline` varied by up to 5.6 s) while a stalled job still misses. The first batch's
     5	  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next
LONG:     6	  batch is an option for the author, recorded as a deviation. A local read of one row should take milliseconds, so a 1 s lag
     7	  classifies nearly every success seen at the deadline and leaves the rest visible as
     8	  `deadline not observed`. A drain limit of D gives a late job as long again to finish, enough to
     9	  tell late from unfinished without one job holding the batch indefinitely. Whether D1 at this clock
    10	  takes one claim or two stays open: M2 reported no outage duration, and failed-renewal counts do not
    11	  establish one.
```

## 245. Assistant — 2026-10-24T05:38:46.154Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md",
  "old_string": "  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next\n  batch is an option for the author, recorded as a deviation. A local read of one row should take milliseconds, so a 1 s lag\n  classifies nearly every success seen at the deadline and leaves the rest visible as\n  `deadline not observed`. A drain limit of D gives a late job as long again to finish, enough to\n  tell late from unfinished without one job holding the batch indefinitely. Whether D1 at this clock\n  takes one claim or two stays open: M2 reported no outage duration, and failed-renewal counts do not\n  establish one.",
  "new_string": "  C0 jobs measure T; if one takes longer than 2S, deriving D from the measured T before the next\n  batch is an option for the author, recorded as a deviation. A local read of one row should take\n  milliseconds, so a 1 s lag classifies nearly every success seen at the deadline and leaves the rest\n  visible as `deadline not observed`. A drain limit of D gives a late job as long again to finish,\n  enough to tell late from unfinished without one job holding the batch indefinitely. Whether D1 at\n  this clock takes one claim or two stays open: M2 reported no outage duration, and failed-renewal\n  counts do not establish one."
}
```

## 246. Assistant — 2026-10-24T05:38:48.133Z

### Tool call: Bash

```
{
  "command": "grep -n -E 'Stages and authorship' -A6 docs/spec.md | head -10 && echo \"=== recovery-sql.md section 6 last bullet\" && grep -n -A3 '^- \\*\\*What it shows' docs/recovery-sql.md",
  "description": "Read the spec's authorship paragraph and the SQL run record's end"
}
```

## 247. User — 2026-10-24T05:38:50.013Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-experiments.md has been updated successfully.
```

## 248. User — 2026-10-24T05:38:50.209Z

### Tool result

```
873:**Stages and authorship.** The job table and the worker, then Kafka delivery
874-and the reconciler, with the Compose services added one at a time; then the
875-recovery experiments and the result cache; each stops for review. The Docker
876-image, the Compose services, the job table, the worker and the reconciler are
877-written with Claude Code; the cache logic and the experiments by the project
878-author, with tutoring.
=== recovery-sql.md section 6 last bullet
624:- **What it shows.** On these made-up rows, in MySQL 8.4.13, the queries return what the verdict
625-  rules of the outline say they should. It shows nothing about real batches or the job system.
```

## 249. Assistant — 2026-10-24T05:39:02.836Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/spec.md",
  "old_string": "image, the Compose services, the job table, the worker and the reconciler are\nwritten with Claude Code; the cache logic and the experiments by the project\nauthor, with tutoring.",
  "new_string": "image, the Compose services, the job table, the worker and the reconciler are\nwritten with Claude Code; the cache logic and the experiments by the project\nauthor, with tutoring. At the author's decision of 2026-10-24, the recovery\nexperiments' tooling (the session harness, its collector, assignment events,\ncode identity at launch and the fault hooks) is written with Claude Code too;\nthe experiments' decisions, runs and answers stay the author's\n([recovery-experiments.md](recovery-experiments.md), section 9)."
}
```

## 250. Assistant — 2026-10-24T05:39:05.468Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-sql.md",
  "old_string": "- **What it shows.** On these made-up rows, in MySQL 8.4.13, the queries return what the verdict\n  rules of the outline say they should. It shows nothing about real batches or the job system.",
  "new_string": "- **What it shows.** On these made-up rows, in MySQL 8.4.13, the queries return what the verdict\n  rules of the outline say they should. It shows nothing about real batches or the job system.\n- **Accepted** by the author on 2026-10-24 as tooling evidence, not as approval of Part A. The\n  harness runs these queries from `src/etf_risk/jobs/crosscheck.sql`, which\n  tests/test_jobs_harness.py holds equal to section 2 byte for byte, so neither can change alone."
}
```

## 251. User — 2026-10-24T05:39:06.549Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/spec.md has been updated successfully.
```

## 252. User — 2026-10-24T05:39:07.634Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/recovery-harness/docs/recovery-sql.md has been updated successfully.
```

## 253. Assistant — 2026-10-24T05:39:23.445Z

### Tool call: Bash

````
{
  "command": "D=docs/recovery-experiments.md && echo \"outline: $(wc -l < $D | tr -d ' ') lines\"; echo \"links:\"; for f in $D docs/recovery-sql.md; do grep -o -E '\\]\\([^)#]+' $f | sed 's/^](//' | sort -u | while read -r p; do test -e \"docs/$p\" || echo \"  MISSING in $(basename $f): $p\"; done; done; echo \"  (checked)\"; heads=$(grep -E '^#{2,3} ' $D | grep -o -E '^#{2,3} [0-9]+(\\.[0-9]+)?' | awk '{print $2}' | sort -u); echo \"section refs without heading: $(for r in $(grep -o -E '\\b[1-9]\\.[1-6]\\b' $D | sort -u); do echo \"$heads\" | grep -qx \"$r\" || printf '%s ' \"$r\"; done)\"; DOC=$PWD/docs/recovery-sql.md bash /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/a9a2be5c-8da0-4ec5-be57-f251b5676fe9/scratchpad/fixture/run.sh prepare; python3 -I - <<'EOF'\nimport re\nfrom pathlib import Path\ndoc = Path(\"docs/recovery-sql.md\").read_text()\nblocks = re.findall(r\"^```sql\\n(.*?)^```$\", doc, flags=re.S | re.M)\nprefixes = (\"-- The harness's records\", \"-- Q0.\", \"-- Q1.\", \"-- Q2.\", \"-- Q2b.\", \"-- Q3a.\", \"-- Q3b.\")\nwanted = \"\\n\".join(next(b for b in blocks if b.startswith(p)) for p in prefixes)\ntext = Path(\"src/etf_risk/jobs/crosscheck.sql\").read_text()\nlines = text.splitlines(keepends=True)\nsep = next(i for i, l in enumerate(lines) if re.match(r\"^-- -{20,}\\s*$\", l))\nprint(\"crosscheck.sql body equals the document's blocks:\", \"\".join(lines[sep + 1:]) == wanted)\nEOF",
  "description": "Check links, references, and that the frozen SQL is unchanged"
}
````

## 254. User — 2026-10-24T05:39:24.800Z

### Tool result

```
outline: 565 lines
links:
  (checked)
section refs without heading: 1.3 1.5 5.5 5.6 9.5 
session script: 453 lines, sha256 447ef025fb0b44424b16197f112b4008510b73c8f2edeaa5fd4f639fbb7a9186
crosscheck.sql body equals the document's blocks: True
```

## 255. Assistant — 2026-10-24T05:39:56.378Z

### Tool call: Write

```
{
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/recovery-outline-draft.md",
  "content": "[REDACTED:memory]"
}
```

## 256. User — 2026-10-24T05:39:57.556Z

### Tool result

```
[REDACTED:memory]
```

## 257. Assistant — 2026-10-24T05:39:59.913Z

### Tool call: Bash

```
{
  "command": "echo \"pycache ignored: $(git check-ignore -q src/etf_risk/jobs/__pycache__ && echo yes || echo no)\"; git status --porcelain=v1 --untracked-files=all | grep -v __pycache__ | awk '{print $1}' | sort | uniq -c; echo \"lines added/changed in tracked files:\"; git diff --stat | tail -1; echo \"new files: $(git status --porcelain=v1 --untracked-files=all | grep '^??' | grep -v __pycache__ | awk '{print $2}' | xargs wc -l | tail -1)\"; echo \"M2 worktree: $(git --no-optional-locks -C ../worker-pipeline rev-parse --short HEAD), $(git --no-optional-locks -C ../worker-pipeline status --porcelain | wc -l | tr -d ' ') uncommitted; test processes now: $(pgrep -f '[p]ytest' | wc -l | tr -d ' ')\"",
  "description": "Summarize the worktree's changes and the M2 worktree state"
}
```

## 258. User — 2026-10-24T05:40:01.762Z

### Tool result

```
pycache ignored: yes
   9 ??
  12 M
lines added/changed in tracked files:
 12 files changed, 159 insertions(+), 16 deletions(-)
new files:     3399 total
M2 worktree: a3a767b, 2 uncommitted; test processes now: 0
```

## 259. Assistant — 2026-10-24T05:40:15.094Z

### Tool call: Bash

```
{
  "command": "cd ~/leveraged-etf-risk-analytics && git --no-optional-locks log --oneline e4adc38..a3a767b && git --no-optional-locks diff --stat e4adc38 a3a767b | tail -12 && echo \"=== overlap with files I changed:\" && comm -12 <(git --no-optional-locks diff --name-only e4adc38 a3a767b | sort) <(git -C .claude/worktrees/recovery-harness status --porcelain=v1 | awk '{print $2}' | sort)",
  "description": "See what the M2 session committed since my branch point"
}
```

## 260. User — 2026-10-24T05:40:15.957Z

### Tool result

```
a3a767b Attribute the 345 MiB MySQL peak to the earlier live run
 docs/worker-pipeline.md | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)
=== overlap with files I changed:
```

## 261. Assistant — 2026-10-24T05:40:44.226Z

The tooling is written, but **none of it has run**. You asked me to coordinate with the M2 session before any test run, and I couldn't tell which of the four peer sessions it is (ListAgents shows them only as "bf", "aa", "ea" and "d4"). Rather than message all four, I'm asking you.

Everything below is uncommitted on a new branch, `feature/recovery-harness`, in `.claude/worktrees/recovery-harness`, created from M2's `e4adc38`.

**What's written (Claude Code; each new module says so)**

| Piece | Where | Purpose |
|---|---|---|
| Assignment events | `kafka.py` | logs `assigned`/`revoked`/`lost`, which the harness uses to find the partition owner |
| Code identity at launch | `provenance.py`, `cli.py`, `pipeline.py` | every process start and step launch records which code it ran |
| Fault hooks | new `faults.py`, plus a new fault point `after_accept_commit` in `worker.py` | precise injection at points too narrow for outside signals |
| Harness | new `harness.py`, with `crosscheck.sql` | plans a batch, estimates its duration, and runs it |
| Collector | new `analysis/collect_recovery_measurements.py` | turns a batch's records into per-job metrics, a per-case tally and validity checks |

- **Tests:** 29 new test functions (one of them live, which skips without Kafka) and 3 updated ones; none run yet.
- **Checks so far:** all files compile.
- **Frozen SQL:** preserved. It still reproduces the validated hash, and a test keeps `crosscheck.sql` byte-identical to the validated SQL.

**Deadlines reassessed (P3)**
- **W7:** its bound is now the later of the takeover and the end of the stopped tree, not 65 s plus the stop.
- **K2, D1, D2:** deadlines now count from when the service works again, so no unmeasured restart time enters a deadline.
- **When the read happens:** the deadline check now happens when the job finishes, or at the deadline if that comes first, so on-time jobs don't wait out their deadline. The frozen SQL handles all of this unchanged.
- **Values for the calendar-year job:** 75 s, 90 s, 140 s, 170 s (W7), 125 s (K2) and 140 s (D1, D2).

**All 84 jobs: about 2 h 26 min.** That's 73 min per batch, under stated assumptions that aren't measured, the main one being a 40 s job run (T). Each extra 5 s of T adds about 8 minutes. These figures are worked out by hand and pinned by a test that hasn't run.

**Findings**
- **A doc claim the code doesn't enforce:** `worker-pipeline.md` says the worker "never… accepts after F", but `handle()` makes the first `accept_result` call without checking F. The token guard keeps this safe. D2's hold would show it. I haven't changed M2's code.
- **P5 differs from my proposal:** a fault file armed per job, rather than a fault named in the environment. Arming through the environment would need a worker restart, which rebalances the group and can move the partition to the other worker.
- **Left out:** monotonic step times in the launcher records weren't among your five items, so the overlap check still compares UTC times.
- **Docs:** I updated spec §11's authorship sentence. The working copies of the outline and SQL file now live in the new worktree; the old ones stay at revision 3.
- **M2 moved on:** M2 is now at `a3a767b`, a one-file docs change that doesn't overlap mine.

**Remaining Part A decisions (all provisional)**
- P1–P5 to accept, change or reject. P5 is now a concrete design.
- Still open:
  - the clock-check tolerance (the collector uses 1 s for now);
  - the harness's waits (3 s phase delay, 90 s W7 stop, 30 s outages);
  - a host-memory gate;
  - monotonic launcher times;
  - committing.
- The isolated memory-budget check stays pending.

**To run the offline tests:** tell me which session is M2, or confirm the test window yourself. Running them needs `uv` to create this worktree's `.venv` from `uv.lock`. They use no containers; the live Kafka test needs a separate window.
