"""The job queue of the optional systems extension (spec §11), with a simulated pipeline.

- The job table: the schema (schema/mysql.sql, mirrored for SQLite in schema/sqlite.sql),
  the state transitions (store.py), and the MySQL dialect and connection (mysql.py).
- Delivery: the queue interfaces and submit_job() (queue.py), the Kafka adapters
  (kafka.py), and the in-memory queue for the offline tests (simulated.py).
- The worker, which handles one delivered job at a time (worker.py), and the
  reconciler (reconciler.py).

Redis and the real pipeline come later. docs/job-table.md explains claim(), the token
checks and the transactions with two workers. docs/job-queue.md explains publication,
delivery and the reconciler with a timeline.

Guarantee. Each job accepts at most one result, and a job that succeeds has exactly one
accepted result. A job may execute more than once: a delivery can repeat, and a lease can
expire while a slow worker still runs. Every attempt writes to its own output folder.

How the store keeps it
- jobs holds each job's current state, job_attempts one row per claim. Every operation is
  one transaction. Apart from submit and mark_published, each writes both tables, so they
  never disagree.
- Each state change is one UPDATE of the job's row whose WHERE clause is the guard; the
  number of rows it matched says whether the change happened.
- A claim writes a new attempt token and attempt number. Renewal, acceptance and failure
  require that token and status running: a worker whose token no longer matches has been
  fenced off and writes nothing more. The lease decides only when another worker may take
  a job over. Tokens keep the result unique; leases let a crashed worker's job finish.
- CHECK constraints state the invariants of one row: a running job has a token and a
  lease; a succeeded job names its one accepted attempt, a job in any other status none;
  only a queued job can have a recorded publication.

Delivery and retries
A delivery carries a job id. The worker acknowledges it by committing the message's offset:
right after a successful claim, or at once when the claim shows the job needs nothing
(finished, or held by a live lease). A worker that dies before acknowledging gets the job
delivered again. Once a delivery is acknowledged, no delivery is pending for that job, and
two kinds of job need a new one: a job that fail_attempt() returned to queued, and a
running job whose worker died after acknowledging. The reconciler handles both:
- it requeues each expired lease, conditional on the token it read;
- it publishes each queued job with no recorded publication: a requeued job at once, and a
  job never claimed once PUBLICATION_GRACE has passed, so it does not race the job's
  submitter.
A publication is recorded (published_at) only once Kafka confirmed it, and only if the job
has not changed since its version was read.

What the tests show
tests/test_jobs_store.py, test_jobs_worker.py, test_jobs_reconciler.py and
test_jobs_queue.py run on SQLite (the standard library's sqlite3) with a manual clock and
the in-memory queue, and on MySQL as well when ETF_RISK_MYSQL_URL is set. On SQLite they
check the state logic:
- the guards, the constraints, and rollbacks inside each transaction;
- the worker under duplicate deliveries, crashes, expired leases and stale workers;
- publication, commits, rewinds and the reconciler, including a seeded run with lost
  publications and crashes.
There, competing connections run one after another under SQLite's database lock.

How MySQL and Kafka behave takes the live runs, a separate and required step:
- tests/test_jobs_mysql.py and the MySQL runs of the files above: InnoDB's row locks under
  competing claims, isolation levels, the affected-rows count and CHECK enforcement;
- tests/test_jobs_kafka.py: confirmation, consumer groups, commits, rewinds, and two
  end-to-end scenarios.

AI contribution: written with Claude Code (Opus 5.5). Verified with the tests named above,
on SQLite and against MySQL 8.4.13 and Kafka 4.3.1.
"""
