#!/bin/zsh
# The recovery experiments' formal batch-3 (docs/recovery-part-a.md, section 13): one batch on the
# frozen code 4fc550e with the approved plan-544.json, run by the author from Terminal with the
# editor and other applications closed. Written with Claude Code (Opus 5.5) on 2026-10-27.
#
#   zsh docs/recovery-batch-3.zsh --check   preconditions only; starts nothing
#   zsh docs/recovery-batch-3.zsh           preconditions, then the batch, the collection and the cleanup check
#
# Any failed precondition stops the script before the batch starts. Afterwards, separately:
#   uv run --group jobs python docs/verify_frozen_code.py data/outputs-recovery/formal/batch-3 4fc550e 544

set -euo pipefail
cd ${0:A:h:h}

FROZEN=4fc550e
PLAN=data/outputs-recovery/formal/plan-544.json
PLAN_SHA256=c74b125eddd87ca1ce891a63f11fe72b0da8b00f2bf6db651020c370d5ffa7b6
OUT=data/outputs-recovery/formal/batch-3
UV=(uv run --group jobs)

fail() { print -r -- "PRECONDITION FAILED: $1"; exit 2 }

git diff --quiet $FROZEN -- src analysis tests pyproject.toml uv.lock || fail "the code differs from $FROZEN"
[[ -z "$(git status --porcelain)" ]] || fail "the worktree is not clean"
[[ "$(shasum -a 256 $PLAN | cut -d' ' -f1)" == $PLAN_SHA256 ]] || fail "$PLAN is not the approved plan"
[[ ! -e $OUT ]] || fail "$OUT exists: a batch is never overwritten"
[[ -z "$(docker compose -f docker/compose.yaml ps -a -q)" ]] || fail "this project's containers exist"
$UV python -m etf_risk.services others --require-none || fail "another project's container is running"
! pgrep -f 'pytest|etf_risk\.jobs|org\.apache\.spark' >/dev/null || fail "a test, job or Spark process is running"
pmset -g batt | head -1 | grep -q "'AC Power'" || fail "not on AC power"
ioreg -r -k AppleClamshellState -d 4 | grep -q '"AppleClamshellState" = No' || fail "the lid is closed or unknown"
print "preconditions: all hold (code $FROZEN, plan $PLAN, folder $OUT)"
[[ ${1:-} == --check ]] && exit 0

ran=0                                  # a batch that ends with an error is still collected and kept
caffeinate -dims $UV python -m etf_risk.jobs.harness batch --plan $PLAN --out $OUT --formal 2>&1 | tee $OUT.console.log || ran=$?
collected=0
$UV python analysis/collect_recovery_measurements.py --batch $OUT 2>&1 | tee $OUT.collect.log || collected=$?
left=$(docker compose -f docker/compose.yaml ps -a -q)
[[ -z $left ]] && print "cleanup: no container of this project left" || print "CLEANUP NEEDED: this project's containers remain"
print "batch exit $ran; collector exit $collected (0 only if both verdicts are valid)"
print "next: uv run --group jobs python docs/verify_frozen_code.py $OUT $FROZEN 544"
(( ran == 0 && collected == 0 ))
