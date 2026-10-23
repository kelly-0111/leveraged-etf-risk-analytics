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
-- AI contribution: written with Claude Code (Opus 5.5). Verified with tests/test_jobs_store.py
-- (constraints, schema drift) and tests/test_jobs_mysql.py, on MySQL 8.4.13.

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
    PRIMARY KEY (job_id),
    CONSTRAINT jobs_status CHECK (status IN ('queued', 'running', 'succeeded', 'failed')),
    CONSTRAINT jobs_running_has_lease
        CHECK ((status = 'running') = (attempt_token IS NOT NULL AND lease_expires_at IS NOT NULL)),
    CONSTRAINT jobs_succeeded_has_one_result CHECK ((status = 'succeeded') = (accepted_attempt IS NOT NULL)),
    CONSTRAINT jobs_failed_has_error CHECK ((status = 'failed') = (error IS NOT NULL)),
    CONSTRAINT jobs_finished CHECK ((status IN ('succeeded', 'failed')) = (finished_at IS NOT NULL)),
    CONSTRAINT jobs_attempt_limit CHECK (max_attempts >= 1 AND attempt_number <= max_attempts),
    CONSTRAINT jobs_queued_has_attempts_left CHECK (status <> 'queued' OR attempt_number < max_attempts)
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
    CONSTRAINT job_attempts_failed_has_error CHECK ((outcome = 'failed') = (error IS NOT NULL))
) ENGINE = InnoDB;

-- Declared once job_attempts exists: the accepted result is one of the job's own attempts.
ALTER TABLE jobs ADD CONSTRAINT jobs_accepted_attempt
    FOREIGN KEY (job_id, accepted_attempt) REFERENCES job_attempts (job_id, attempt_number);
