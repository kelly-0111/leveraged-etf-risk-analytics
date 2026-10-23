"""The job queue's commands (spec §11; the README's runbook):

    python -m etf_risk.jobs init-db                 # create the database, tables and store id (idempotent)
    python -m etf_risk.jobs create-topic            # the job topic: one partition, no replica
    python -m etf_risk.jobs submit --snapshot S --kind rolling [--stride 21 ...]
    python -m etf_risk.jobs worker [--standby]      # serve jobs until SIGTERM or SIGINT
    python -m etf_risk.jobs reconciler              # requeue expired leases, publish unconfirmed jobs
    python -m etf_risk.jobs status [--check]        # the tables; --check: exit 1 on any invariant violation
    python -m etf_risk.jobs cleanup                 # list the folders of ended, non-accepted attempts (dry run)
    python -m etf_risk.jobs export DIR              # tables, violations and settings, as JSON files

The settings come from flags or the environment:
- the database: --db or ETF_RISK_JOBS_DB, either mysql://user:password@host:port/database or
  sqlite:////absolute/path;
- Kafka: --bootstrap or ETF_RISK_KAFKA_BOOTSTRAP;
- the roots: --output-root (data/outputs/jobs) and --processed-root (data/processed), relative
  to the repository root;
- --lock, the host's execution lock (~/.cache/etf-risk/locks/spark-exec.lock);
- --timing NAME=SECONDS, overrides of etf_risk.jobs.timing, checked against its relations.

Outputs go to <output root>/<store id>/<run id>/, and event logs to <output root>/events/.

How the worker runs:
- it first sweeps what earlier workers left (pipeline.startup_sweep);
- after an error that comes from the transport, it restarts its serve loop in this process,
  with backoff; any other error ends it with exit code 1. Transport errors are a lost
  database connection, a claim race, a broken connection, or a Kafka error that is not
  fatal;
- SIGTERM or SIGINT stops it gracefully: polling stops, the running step's tree is ended,
  its attempt is failed as retryable (so the job is requeued at once), and the consumer
  leaves the group.

submit inserts the job, publishes it, and records the confirmation. When the insert's COMMIT
reply was lost, the job may or may not exist, so it exits 75 (outcome unknown) and is never
repeated on its own.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_jobs_cli.py.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import socket
import sys
import threading
from dataclasses import asdict, fields, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from etf_risk.jobs.events import EventLog
from etf_risk.jobs.params import InvalidParams, JobParams, input_checksums
from etf_risk.jobs.pipeline import DEFAULT_LOCK, SubprocessPipeline, startup_sweep
from etf_risk.jobs.store import SQLITE, ClaimRace, JobStore, Outcome, Status, open_sqlite
from etf_risk.jobs.timing import DEFAULT_TIMING, Timing
from etf_risk.provenance import resolve

DEFAULT_TOPIC, DEFAULT_GROUP = "etf-risk-jobs", "etf-risk-workers"
OUTCOME_UNKNOWN = 75
log = logging.getLogger("etf_risk.jobs")


# Settings

def safe_url(url: str) -> str:
    """The URL without its password, for logs and records."""
    parts = urlsplit(url)
    if parts.password is None:
        return url
    netloc = f"{parts.username}:***@{parts.hostname}" + (f":{parts.port}" if parts.port else "")
    return urlunsplit(parts._replace(netloc=netloc))


def timing_from(overrides: list[str]) -> Timing:
    names = {f.name for f in fields(Timing)}
    changes = {}
    for item in overrides:
        name, _, value = item.partition("=")
        if name not in names:
            raise SystemExit(f"--timing: unknown setting {name!r}; one of {sorted(names)}")
        changes[name] = float(value)
    try:
        return replace(DEFAULT_TIMING, **changes).check()
    except ValueError as error:
        raise SystemExit(f"--timing: {error}") from None


def open_store(db: str, timing: Timing) -> JobStore:
    """A store that reconnects through its database's connection factory."""
    lease = timedelta(seconds=timing.lease)
    if db.startswith("sqlite:///"):
        path = db[len("sqlite:///"):]
        return JobStore(None, SQLITE, lease=lease, connect=lambda: open_sqlite(path, check_same_thread=False))
    if db.startswith("mysql://"):
        from etf_risk.jobs import mysql
        if not urlsplit(db).path.strip("/"):
            raise SystemExit("--db: name the database in the URL, as mysql://user:password@host:port/database")
        return JobStore(None, mysql.MYSQL, lease=lease, connect=mysql.connector(db, **mysql.SERVICE_SESSION))
    raise SystemExit(f"--db: expected mysql://... or sqlite:///..., not {safe_url(db)!r}")


def is_transport_error(error: BaseException, store: JobStore) -> bool:
    if store.dialect.is_disconnect(error) or isinstance(error, (ClaimRace, ConnectionError, TimeoutError)):
        return True
    try:
        from confluent_kafka import KafkaException
    except ImportError:
        return False
    return isinstance(error, KafkaException) and not error.args[0].fatal()


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
               standby=args.standby)
    startup_sweep(store, output_root, timing=timing, events=events)
    pipeline = SubprocessPipeline(store_id=store_id, processed_root=resolve(args.processed_root), worker_id=worker_id,
                                  lock_path=args.lock, timing=timing, events=events, stop=stop)
    worker = Worker(store, pipeline, output_root, worker_id=worker_id, events=events)
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
    events.log("started", db=safe_url(args.db), topic=args.topic)
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
