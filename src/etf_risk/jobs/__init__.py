"""Job table, attempt fencing and a worker: the optional systems extension (spec §11).

This first milestone builds the job-state core: the schema (schema/mysql.sql, mirrored for
SQLite in schema/sqlite.sql), the state transitions (store.py), the MySQL dialect and
connection (mysql.py), and a worker with a simulated pipeline (worker.py, simulated.py).
Kafka, Redis, the reconciler and the real pipeline come later. docs/job-table.md explains
claim(), the token checks and the transactions with two workers.

Guarantee. Each job accepts at most one result, and a job that succeeds has exactly one
accepted result. A job may execute more than once: a delivery can repeat, and a lease can
expire while a slow worker still runs. Every attempt writes to its own output folder.

How the store keeps it
- jobs holds each job's current state, job_attempts one row per claim. Every operation is
  one transaction; apart from submit, each writes both tables, so they never disagree.
- Each state change is one UPDATE of the job's row whose WHERE clause is the guard; the
  number of rows it matched says whether the change happened.
- A claim writes a new attempt token and attempt number. Renewal, acceptance and failure
  require that token and status running: a worker whose token no longer matches has been
  fenced off and writes nothing more. The lease decides only when another worker may take
  a job over. Tokens keep the result unique; leases let a crashed worker's job finish.
- CHECK constraints state the invariants of one row: a running job has a token and a
  lease; a succeeded job names its one accepted attempt, a job in any other status none.

Delivery and retries
A delivery carries a job id. The worker acknowledges it (with Kafka: commits the offset)
right after a successful claim, or at once when the claim shows the job needs nothing
(finished, or held by a live lease). Once a delivery is acknowledged, no delivery is
pending for that job, so two kinds of job run again only when a new delivery arrives:
- a job that fail_attempt() returned to queued: returning a job to queued does not
  deliver it again;
- a running job whose worker died after acknowledging, once its lease has expired.
Nothing in this milestone produces that delivery; the tests call Worker.handle() again.
The future reconciler must publish both kinds again: queued jobs that need a publication
(never confirmed, or requeued after their delivery was acknowledged) and running jobs
whose lease has expired, each change conditional on the state it observed. Telling which
queued jobs need a publication takes a marker, such as a published_at column reset when a
job returns to queued; it comes with Kafka.

What the tests show
tests/test_jobs_store.py and tests/test_jobs_worker.py run on SQLite (the standard library's
sqlite3) with a manual clock, and on MySQL as well when ETF_RISK_MYSQL_URL is set. On SQLite
they check the state logic: the guards, the constraints, rollbacks inside each transaction,
and the worker under duplicate deliveries, crashes, expired leases and stale workers; there,
competing connections run one after another under SQLite's database lock. How MySQL behaves,
InnoDB's row locks under competing claims, isolation levels, the affected-rows count and
CHECK enforcement, takes the MySQL runs and tests/test_jobs_mysql.py, a separate and
required step.

AI contribution: written with Claude Code (Opus 5.5). Verified with the tests named above,
on SQLite and on MySQL 8.4.13.
"""
