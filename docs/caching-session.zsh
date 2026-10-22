# Caching-experiment session helpers (docs/caching-experiment.md, sections 2-3).
# Written by Claude Code (Opus 5.5) on 2026-10-22 for the author's measurement session, from
# docs/baseline-session.zsh and docs/partition-session.zsh, which stay unchanged.
# Load once in each Terminal window:   source <repository>/docs/caching-session.zsh
# Loading only defines the functions below, sets the variables and changes into the repository;
# nothing runs until a function is called. Type  steps  for the checklist.
#
# Variables, read when the file is loaded (set them before loading to change them):
#   BATCH           batch folder under data/outputs-caching (default batch-1). A batch is one
#                   A-B-C-C-B-A sequence under one code state; any change to src/, pyproject.toml
#                   or uv.lock needs a new batch (3.1, 3.4).
#   CACHE_LOAD_MAX  upper limit for the 5-minute load average before a protocol (default 4.0)
#   CACHE_BOOT_MIN  minutes since boot before a protocol may start (default 30)
#   CACHE_WINDOWS, CACHE_ROOT, CACHE_REPEATS: only for a dry run on other data (default: the
#                   stride-7 set, data/outputs-caching, 4 runs per protocol).

REPO=${${(%):-%x}:A:h:h}
cd $REPO || return 1
BATCH=${BATCH:-batch-1}
CACHE_WINDOWS=${CACHE_WINDOWS:-data/windows-experiments/full-2026-10-12/rolling-252-s7}
CACHE_ROOT=${CACHE_ROOT:-data/outputs-caching}
CACHE_REPEATS=${CACHE_REPEATS:-4}
CACHE_LOAD_MAX=${CACHE_LOAD_MAX:-4.0}
CACHE_BOOT_MIN=${CACHE_BOOT_MIN:-30}
BATCH_DIR=$CACHE_ROOT/$BATCH
LOG=$BATCH_DIR/run-log.txt
POSITIONS=$BATCH_DIR/positions.tsv
CACHE_ORDER=(A B C C B A)
typeset -A CACHE_MODE
CACHE_MODE=(A none B members C members-checks)
# Abort limits (section 11), on a run's raw elapsed time as the watcher shows it, plan capture
# included: three times the predicted medians, approved by the author on 2026-10-22. position
# refuses to start while one is missing.
typeset -A CACHE_ABORT_S
CACHE_ABORT_S=(A 80 B 80 C 81)
mkdir -p $BATCH_DIR

steps() {
  cat <<EOF
Caching session (docs/caching-experiment.md 2-3), batch: $BATCH_DIR
Positions 1-6 are configurations A B C C B A (A: no cache, B: the window-member rows, C: B and the
four read-back tables), one protocol each ($CACHE_REPEATS runs). Window 1 runs the commands; window 2
runs the watcher. Load this file in each window first. Never press Ctrl-C in window 1 or close it
while a protocol runs (Ctrl-C during pause5 is fine). Never paste a command that contains a #
comment: this zsh does not ignore comments.

For each position n = 1 to 6, in order:
  1. Window 2:  watch_runs
  2. Window 1:  pause5 && ready && position n
     ready wants: at least 3.0 GiB available, 5-minute load at most $CACHE_LOAD_MAX,
     booted at least $CACHE_BOOT_MIN minutes ago. If it fails, nothing starts: wait, then step 2 again.
     position first writes the 3.2 checks into the run log, then starts measure. Before step 2,
     quit every app but Terminal and Finder, and keep the Mac on mains power.
  3. Window 1 shows measure's summary ("runs started $CACHE_REPEATS of $CACHE_REPEATS", every run "ok",
     no "stopped:" line) and "settings, plans and caches: ok in $CACHE_REPEATS of $CACHE_REPEATS runs".
     Record it:  note 'position n: 4 ok, nothing unusual'   (single quotes; describe anything unusual)
  where   lists the positions run so far.

Abort limits (section 11), on a run's raw elapsed time, plan capture included:
  A ${CACHE_ABORT_S[A]:-unset} s, B ${CACHE_ABORT_S[B]:-unset} s, C ${CACHE_ABORT_S[C]:-unset} s.
  The watcher prints each run's elapsed time with its limit and says ABOVE THE LIMIT when a run
  passes it. Then:  Window 2: Ctrl-C (stops only the watcher), then  abort_run  and answer y.
  After window 1 prints measure's summary:  after_abort    want: java: none | spark scratch folders: 0

Any stop (a run not ok, measure stopped early, a failed check, an abort, STOP):
  stop the session and come back to Claude. Section 3.4 allows one re-run per position in the
  same session; otherwise the batch ends. A change to src/, pyproject.toml or uv.lock ends the
  batch: the next one is loaded with  BATCH=batch-2 source docs/caching-session.zsh
Back to Claude: in window 1,  claude --continue. No git commits during the session.
Run log: $LOG
Positions: $POSITIONS
EOF
}

_scratch_count() {
  find "$TMPDIR" /private/tmp -maxdepth 1 \( -name 'spark-*' -o -name 'blockmgr-*' \) 2>/dev/null | wc -l | tr -d ' '
}

_boot_minutes() {
  local boot
  boot=$(sysctl -n kern.boottime | sed -E 's/^\{ sec = ([0-9]+),.*/\1/')
  echo $(( ($(date +%s) - boot) / 60 ))
}

prechecks() {
  {
    echo "=== ${1:-protocol}: checks at $(date -u +%Y-%m-%dT%H:%M:%SZ), batch $BATCH"
    pmset -g | grep lowpowermode
    pmset -g batt | head -n 1
    pgrep -fl com.docker.backend || echo "docker backend: none"
    pgrep -fl 'java|etf_risk' || echo "java/etf_risk: none"
    echo "apps: $(lsappinfo visibleProcessList | grep -o '"[^"]*"' | tr '\n' ' ')"
    echo "load average: $(sysctl -n vm.loadavg)"
    echo "minutes since boot: $(_boot_minutes)"
    echo "HEAD $(git -C $REPO rev-parse --short HEAD), changed code files: $(git -C $REPO status --porcelain -- src pyproject.toml uv.lock | wc -l | tr -d ' ')"
    echo "spark scratch folders: $(_scratch_count)"
  } | tee -a $LOG
}

pause5() {
  echo "pause start $(date -u +%H:%M:%SZ)" | tee -a $LOG
  caffeinate -i sleep 300 || { echo "pause interrupted $(date -u +%H:%M:%SZ)" | tee -a $LOG; return 1; }
  echo "pause end $(date -u +%H:%M:%SZ)" | tee -a $LOG
}

# The 3.2 readings just before a start; fails, and nothing starts, unless all three are met.
ready() {
  local min=${1:-3.0} gib load5 boot problems=0
  gib=$(uv run --group measure python -c "import psutil; print(round(psutil.virtual_memory().available / 2**30, 2))") || return 2
  load5=$(sysctl -n vm.loadavg | awk '{print $3}')
  boot=$(_boot_minutes)
  echo "available GiB: $gib (minimum $min); 5-minute load: $load5 (limit $CACHE_LOAD_MAX); minutes since boot: $boot (minimum $CACHE_BOOT_MIN)" | tee -a $LOG
  (( gib >= min )) || { echo "  below $min GiB" | tee -a $LOG; problems=1; }
  (( load5 <= CACHE_LOAD_MAX )) || { echo "  load above $CACHE_LOAD_MAX" | tee -a $LOG; problems=1; }
  (( boot >= CACHE_BOOT_MIN )) || { echo "  booted less than $CACHE_BOOT_MIN minutes ago" | tee -a $LOG; problems=1; }
  (( problems == 0 )) && return 0
  echo "protocol not started" | tee -a $LOG
  return 1
}

# One protocol at position n (2.4): the configuration comes from the order, the protocol JSON from
# what measure wrote. The 3.2 checks are written first, so the run log shows the state at every
# start; afterwards the check of the runs' settings, plans and caches (3.4) and one line in
# positions.tsv (3.3).
position() {
  local n=$1 config out before proto rc check result
  [[ $n == <1-6> ]] || { echo "usage: position 1-6"; return 2; }
  [[ $PWD == $REPO ]] || { echo "run from $REPO"; return 2; }
  config=${CACHE_ORDER[$n]}
  [[ -n ${CACHE_ABORT_S[A]} && -n ${CACHE_ABORT_S[B]} && -n ${CACHE_ABORT_S[C]} ]] || { echo "an abort limit is missing (section 11)"; return 2; }
  out=$BATCH_DIR/$config
  before=$(find $out -name 'protocol-*.json' 2>/dev/null | sort)
  prechecks "position $n"
  echo "=== position $n (configuration $config): measure starts $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a $LOG
  caffeinate -i uv run --group measure python -m etf_risk.measure --repeats $CACHE_REPEATS -- \
    --windows $CACHE_WINDOWS --out-root $out --cache ${CACHE_MODE[$config]} --record-plans 2>&1 | tee -a $LOG
  rc=${pipestatus[1]}
  proto=$(comm -13 <(print -r -- "$before") <(find $out -name 'protocol-*.json' 2>/dev/null | sort) | tail -n 1)
  if [[ -z $proto ]]; then
    echo "STOP: position $n wrote no protocol JSON (measure exit $rc); come back to Claude" | tee -a $LOG
    return 1
  fi
  uv run python analysis/collect_caching_measurements.py --check-protocol $proto --config $config | tee -a $LOG
  check=${pipestatus[1]}
  (( check == 0 )) && result=ok || result=failed
  [[ -f $POSITIONS ]] || print -r -- $'position\tconfig\tprotocol\tmeasure_exit\tcache_check\tlogged_at_utc' > $POSITIONS
  print -r -- "$n"$'\t'"$config"$'\t'"${${proto:t:r}#protocol-}"$'\t'"$rc"$'\t'"$result"$'\t'"$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> $POSITIONS
  echo "position $n ($config): ${proto:t}, measure exit $rc, cache check $result" | tee -a $LOG
  (( rc == 0 && check == 0 )) || { echo "STOP: a run did not end ok, or its settings, plans or caches are wrong; come back to Claude" | tee -a $LOG; return 1; }
}

where() {
  if [[ -f $POSITIONS ]]; then column -t -s $'\t' $POSITIONS; else echo "no protocol yet in $BATCH_DIR"; fi
}

# ps etime, [[dd-]hh:]mm:ss, in seconds.
_etime_seconds() {
  local t=$1 d=0 h=0 m=0 s=0
  local -a parts
  if [[ $t == *-* ]]; then d=${t%%-*}; t=${t#*-}; fi
  parts=(${(s.:.)t})
  case ${#parts} in
    3) h=$parts[1]; m=$parts[2]; s=$parts[3] ;;
    2) m=$parts[1]; s=$parts[2] ;;
    1) s=$parts[1] ;;
  esac
  echo $(( ((d * 24 + h) * 60 + m) * 60 + s ))
}

# The configuration a pipeline's command line runs, from its --cache value; ? if none matches.
_config_of() {
  case "$1" in
    *"--cache none "*|*"--cache none") echo A ;;
    *"--cache members "*|*"--cache members") echo B ;;
    *"--cache members-checks"*) echo C ;;
    *) echo "?" ;;
  esac
}

watch_runs() {
  local pid config secs limit
  until pgrep -qf etf_risk.measure; do sleep 5; done
  while pgrep -qf etf_risk.measure; do
    pid=$(pgrep -f etf_risk.spark_pipeline | head -n 1)
    if [[ -n $pid ]]; then
      config=$(_config_of "$(ps -o command= -p $pid)")
      secs=$(_etime_seconds $(ps -o etime= -p $pid | tr -d ' '))
      limit=${CACHE_ABORT_S[$config]:-}
      if [[ -n $limit ]] && (( secs > limit )); then
        echo "$(date +%H:%M:%S)  pipeline $pid ($config) running $secs s: ABOVE THE $limit s LIMIT, abort it"
      else
        echo "$(date +%H:%M:%S)  pipeline $pid ($config) running $secs s (limit ${limit:-unknown} s)"
      fi
    fi
    sleep 10
  done
  echo "measure finished"
}

# 3.4: kill the pipeline process only, never measure, so the protocol JSON is still written.
abort_run() {
  local pid age
  pid=$(pgrep -f etf_risk.spark_pipeline | head -n 1)
  [[ -n $pid ]] || { echo "no pipeline running"; return 1; }
  age=$(ps -o etime= -p $pid | tr -d ' ')
  ps -o pid=,etime=,command= -p $pid
  read -q "?Kill this pipeline process (measure keeps running and records it)? [y/n] " || { echo; return 1; }
  echo
  kill $pid && echo "$(date -u +%H:%M:%SZ) aborted: killed pipeline $pid after $age" | tee -a $LOG
}

after_abort() {
  {
    echo "=== after abort $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    pgrep -fl java || echo "java: none"
    echo "spark scratch folders: $(_scratch_count)"
  } | tee -a $LOG
}

note() {
  echo "$(date -u +%H:%M:%SZ) $*" | tee -a $LOG
}

echo "caching-session loaded: batch $BATCH_DIR, run log $LOG; type  steps  for the checklist"
