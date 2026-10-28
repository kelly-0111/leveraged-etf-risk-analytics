#!/bin/zsh
# The systems extension end to end, once, on fresh services (docs/demo.md, section 5):
#   1. a job submitted to the job table and published to Kafka;
#   2. run by worker A with the real pipeline, and its result accepted;
#   3. that accepted run's summary served by the result cache: a miss runs Spark and stores the
#      result, the same request again is a hit;
#   4. Redis stopped, and the same request answered by Spark, with nothing written.
# Written with Claude Code (Opus 5.5) on 2026-10-27.
#
#   zsh docs/extension-demo.zsh        about 5 minutes; records in data/outputs-demo/<UTC stamp>/
#
# A functional demo, not an experiment: its times are one run's and support no claim. It refuses
# to start while this project's containers exist, since another session may be using them. It
# removes the services and their volumes when it ends, after an error too, and exits 0 only if
# every expected outcome was seen.

set -euo pipefail
cd ${0:A:h:h}

OUT=data/outputs-demo/$(date -u +%Y%m%dT%H%M%SZ)
COMPOSE=(docker compose -f docker/compose.yaml)
export ETF_RISK_JOBS_DB=mysql://root:jobs-test@127.0.0.1:3307/etf_jobs
export ETF_RISK_REDIS_URL=redis://127.0.0.1:6380/0

[[ -z "$($COMPOSE ps -a -q)" ]] || { print -r -- "NOT STARTED: this project's containers exist"; exit 2 }
mkdir -p $OUT
exec > >(tee $OUT/demo.log) 2>&1

PY=$(uv run --group jobs --group cache python -c 'import sys; print(sys.executable)')
pids=()
unexpected=0
step() { print -r -- "== $(date -u +%H:%M:%S) $*" }
job_cmd() { $PY -m etf_risk.jobs "$@" --output-root $OUT/jobs }
wait_for() {                                   # seconds, what, a condition evaluated each second
    local limit=$1 what=$2 waited=0
    until eval $3; do
        (( waited++ < limit )) || { print -r -- "TIMED OUT after ${limit} s: $what"; exit 1 }
        sleep 1
    done
}
stop_processes() {
    for p in $pids; do kill -INT $p 2>/dev/null || true; done
    for p in $pids; do wait $p 2>/dev/null || true; done
    pids=()
}
finish() {
    stop_processes
    $COMPOSE down -v >> $OUT/services-down.log 2>&1 || true
    [[ -z "$($COMPOSE ps -a -q)" ]] && print "cleanup: no container of this project left" \
        || print "CLEANUP NEEDED: this project's containers remain"
}
trap finish EXIT
query() {                                      # the record's name; one summary request in a new process
    $PY -m etf_risk.summary query overview --job $JOB > $OUT/$1.json || true
    jq -c '{status, source, run: (.run | {basis, job_id, attempt_number, digest: .digest[0:12]}),
            counters: (.counters | {hits, misses, get_errors, writes, write_skips}),
            seconds: (.seconds | map_values(. * 1000 | round / 1000))}' $OUT/$1.json
}
expect() {                                     # the record, a jq condition, what it means
    if jq -e "$2" $OUT/$1.json > /dev/null; then print -r -- "   as expected: $3"
    else print -r -- "   NOT AS EXPECTED: $3"; unexpected=1; fi
}

step "code"
{ print "commit $(git rev-parse HEAD)"; print "uncommitted paths: $(git status --porcelain | wc -l | tr -d ' ')" } \
    | tee $OUT/code.txt

step "services: MySQL, Kafka and Redis, on fresh volumes"
$COMPOSE up -d --wait mysql kafka redis > $OUT/services-up.log 2>&1
$PY -m etf_risk.services ready mysql kafka redis

step "the job table and the topic"
job_cmd init-db
job_cmd create-topic

step "a reconciler and worker A, until worker A owns the partition"
job_cmd reconciler > $OUT/reconciler.log 2>&1 & pids+=($!)
job_cmd worker --worker-id A > $OUT/worker-A.log 2>&1 & pids+=($!)
wait_for 120 "worker A's partition" 'grep -q "\"event\": \"assigned\"" $OUT/jobs/events/A.jsonl 2>/dev/null'

step "1. submit a calendar-year job on the snapshot full-2026-10-12"
job_cmd submit --snapshot full-2026-10-12 --kind calendar-year | tee $OUT/submit.json
JOB=$(jq -r .job_id $OUT/submit.json)

step "2. worker A runs windows, spark_pipeline and verify; the job table accepts one result"
wait_for 600 "job $JOB to end" 'job_cmd status --job $JOB | grep -qE "job $JOB: (succeeded|failed)"'
job_cmd status --check --job $JOB | tee $OUT/status.txt
grep -q "job $JOB: succeeded" $OUT/status.txt && print "   as expected: succeeded, one accepted attempt" \
    || { print "   NOT AS EXPECTED: the job did not succeed"; exit 1 }

step "3a. the result cache: a miss runs the query in Spark and stores the result"
query query-1-miss
expect query-1-miss '.status == "ok" and .source == "spark" and .counters.misses == 1 and .counters.writes == 1' \
    "ok, computed in Spark, written to Redis"
step "3b. the same request in a new process: a hit"
query query-2-hit
expect query-2-hit '.status == "ok" and .source == "cache" and .counters.hits == 1' "ok, from Redis"

step "4. Redis stopped: the same request falls back to Spark"
$PY -m etf_risk.services peaks redis > $OUT/peaks-redis.txt       # a stopped container has no cgroup to read
$COMPOSE stop redis > $OUT/redis-stop.log 2>&1
query query-3-redis-down
expect query-3-redis-down '.status == "ok" and .source == "spark" and .counters.get_errors == 1 and .counters.write_skips == 1' \
    "ok, computed in Spark; Redis failed, nothing written"
jq -s -e '.[0].result == .[1].result and .[1].result == .[2].result' \
    $OUT/query-1-miss.json $OUT/query-2-hit.json $OUT/query-3-redis-down.json > /dev/null \
    && print "   as expected: the three answers are identical" \
    || { print "   NOT AS EXPECTED: the answers differ"; unexpected=1 }

step "records: the job table's export, the cleanup listing and the containers' memory peaks"
stop_processes
job_cmd export $OUT/export > $OUT/export.log
job_cmd cleanup > $OUT/cleanup.txt
$PY -m etf_risk.services peaks mysql kafka | cat - $OUT/peaks-redis.txt | tee $OUT/peaks.txt
print "records: $OUT"
(( unexpected == 0 ))
