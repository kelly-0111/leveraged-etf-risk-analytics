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
    CONSTRAINT job_attempts_failed_has_error CHECK ((outcome = 'failed') = (error IS NOT NULL))
) STRICT;
