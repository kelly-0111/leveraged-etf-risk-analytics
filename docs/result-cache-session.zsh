# Result-cache experiment (E3) session helpers (docs/result-cache-experiment.md, sections 5 and 7).
# Written by Claude Code (Opus 5.5) on 2026-10-26 for the author's session.
# Load once in a Terminal window:   source <repository>/docs/result-cache-session.zsh
# Loading only defines the functions below, sets the variables and changes into the repository;
# nothing runs until a function is called. Type  e3_steps  for the checklist.
#
# Variables, read when the file is loaded (set them before loading to change them):
#   E3_PURPOSE   formal, dry-run or sizing (default dry-run); only formal batches answer E3
#   E3_SEED      the workload's seed (default 1); Part A names the formal seed
#   E3_BATCH     the batch folder's name (default: the UTC time at loading)
#   E3_SWAP_OUT_MIB, E3_SWAP_IN_MIB, E3_DRIFT   the collector's limits (Part A, section 6)

REPO=${${(%):-%x}:A:h:h}
cd $REPO || return 1
E3_PURPOSE=${E3_PURPOSE:-dry-run}
E3_SEED=${E3_SEED:-1}
E3_BATCH=${E3_BATCH:-$(date -u +%Y%m%dT%H%M%SZ)}
E3_SWAP_OUT_MIB=${E3_SWAP_OUT_MIB:-64}
E3_SWAP_IN_MIB=${E3_SWAP_IN_MIB:-256}
E3_DRIFT=${E3_DRIFT:-0.20}
E3_DIR=data/outputs-result-cache/$E3_PURPOSE/$E3_BATCH
E3_COMPOSE=(docker compose -f docker/compose.yaml)
E3_UV=(uv run --group cache --group jobs)

e3_steps() {
  cat <<EOF
E3 session ($E3_PURPOSE), batch: $E3_DIR
  0. Quit other applications (the editor included); AC power, lid open; nothing else in Docker.
  1. e3_redis        start the redis service alone and wait for PING
  2. e3_preflight    exits 1 with the reasons unless a batch may start
  3. e3_plan         write the plan (seed $E3_SEED)
  4. e3_run          run it, the Mac kept awake (caffeinate -i); no other work until it ends
  5. e3_collect      check validity and summarize; exits 1 unless valid
     (e3_run and e3_collect append everything they print to \$E3_DIR/session.log)
  6. e3_cleanup      stop and remove the redis service only
EOF
}

e3_redis() {
  $E3_COMPOSE up -d --wait redis && $E3_UV python -m etf_risk.services ready redis
}

e3_preflight() {
  if [[ $E3_PURPOSE == formal ]]; then
    $E3_UV python -m etf_risk.cache_experiment preflight --formal
  else
    $E3_UV python -m etf_risk.cache_experiment preflight
  fi
}

e3_plan() {
  [[ $E3_PURPOSE == (formal|dry-run|sizing) ]] || { echo "E3_PURPOSE must be formal, dry-run or sizing"; return 2 }
  $E3_UV python -m etf_risk.cache_experiment plan --seed $E3_SEED --out $E3_DIR
}

e3_run() {
  [[ -f $E3_DIR/plan.json ]] || { echo "no plan in $E3_DIR: e3_plan first"; return 2 }
  { e3_preflight && if [[ $E3_PURPOSE == formal ]]; then
      caffeinate -i $E3_UV python -m etf_risk.cache_experiment run $E3_DIR --formal
    else
      caffeinate -i $E3_UV python -m etf_risk.cache_experiment run $E3_DIR
    fi } 2>&1 | tee -a $E3_DIR/session.log
  return ${pipestatus[1]}
}

e3_collect() {
  $E3_UV python analysis/collect_result_cache_measurements.py $E3_DIR \
    --swap-out-limit-mib $E3_SWAP_OUT_MIB --swap-in-limit-mib $E3_SWAP_IN_MIB --drift-limit $E3_DRIFT \
    2>&1 | tee -a $E3_DIR/session.log
  return ${pipestatus[1]}
}

e3_cleanup() {
  $E3_COMPOSE rm --stop --force redis
}
