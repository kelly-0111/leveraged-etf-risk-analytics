# Recovery experiments: SQL cross-check and fixture

_Drafted with Claude Code (Opus 5.5) on 2026-10-23 for [recovery-experiments.md](recovery-experiments.md),
the outline of E1 and E2 ("the outline" below). Moved there from the outline's section 7 and
Appendix A in its revision 3, with no SQL changed: the script assembled from this file has the
SHA-256 recorded before the run (section 6). The queries and the fixture are Claude Code's
proposals; the author decides whether to keep, rewrite or replace them (outline, section 9). They
were run once against a scratch MySQL, and all 82 expected rows matched (section 6)._

Section numbers inside the SQL comments refer to the outline. "Section 7's TEMPORARY tables" in
fixture A's harness block names the place the queries had before the move; they are now in section
2 of this file.

## 1. What the queries add, and where they run

The store's seven `INVARIANT_QUERIES` list the jobs that break an invariant, and `status --check`
exits 1 if any does. Between them they already imply at most one accepted attempt per job in the
database. The schema alone does not: `jobs.accepted_attempt` names one attempt, but no constraint
stops two `job_attempts` rows of one job from both being `accepted`. Q1 restates that part as counts
per job, from the tables alone (outline 6.2). The other queries add what the store cannot see: each
job's deadline and its observation (Q2, outline 6.3), jobs the harness did not record (Q2b), and the
workers' reports against the table (Q3a, Q3b, outline 6.4). The overlap of Q1 with the invariant
queries is deliberate: a second reading of the same rows, by queries the store does not run.

The queries run in MySQL, in the final snapshot (outline 4.5). The harness's records are loaded into
TEMPORARY tables of the cross-check's own session, so the store's tables are untouched. MySQL
documents that a TEMPORARY table cannot be referred to more than once in the same query, so each
query names each of them at most once. `worker_id` is compared with `CAST(... AS BINARY)`, byte for
byte, since the store's `worker_id` column, unlike its other identifiers, has no binary collation.
Written for MySQL 8.4, with CTEs, joins and CASE only.

## 2. The harness's tables and the queries

```sql
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
```

```sql
-- Q0. Snapshot fingerprint (4.5): equal in the cross-check, in the export and after the export.
SELECT
    (SELECT COUNT(*) FROM jobs) AS n_jobs,
    (SELECT COALESCE(SUM(version), 0) FROM jobs) AS sum_version,
    (SELECT COUNT(*) FROM job_attempts) AS n_attempts,
    (SELECT COALESCE(SUM(renewals), 0) FROM job_attempts) AS sum_renewals;
```

```sql
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
```

```sql
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
```

```sql
-- Q2b. Jobs in the table that the harness did not record, such as a submit that exited 75
-- (outcome unknown) although its insert committed. Each needs an explanation.
SELECT
    j.job_id,
    j.status
FROM jobs AS j
LEFT JOIN batch_jobs AS b ON b.job_id = j.job_id
WHERE b.job_id IS NULL
ORDER BY j.job_id;
```

```sql
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
```

```sql
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

**The per-case tally** is computed by the collector from the saved results of Q1–Q3b and the
injection log, with no SQL logic of its own: for each of the 14 cases, the injections planned, made,
missed and not run; the jobs per Q1 verdict, per Q2 class, per `deadline_met` value and per Q3a
verdict; the reports per Q3b verdict; and the claims per job. Every case and every verdict value
appears, with zeros.

**Expected verdicts in a real batch** (proposal), valid and of the planned cases: Q1 `ok` for every
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
