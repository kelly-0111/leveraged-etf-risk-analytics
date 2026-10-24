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
