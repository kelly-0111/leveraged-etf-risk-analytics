# Stride experiment session helpers (docs/experiments.md, sections 3.2-3.6).
# Written by Claude Code (Opus 5.5) on 2026-10-18 for the author's measurement session.
# Load once in each Terminal window:   source ~/stride-session.zsh
# Loading only defines the functions below, sets LOG and changes into the repository;
# nothing runs until a function is called. Type  steps  for the checklist.

REPO=$HOME/leveraged-etf-risk-analytics
LOG=$REPO/data/outputs-experiments/run-log.txt
cd $REPO || return 1
mkdir -p ${LOG:h}

steps() {
  cat <<'EOF'
Stride experiment session (docs/experiments.md 3.2-3.6)
Window 1 runs the commands; window 2 runs the watcher. Load this file in each window first.
Never press Ctrl-C in window 1 or close it while a protocol runs (Ctrl-C during pause5 is fine).

Before each protocol:
  1. Window 1:  prechecks 'stride 21 (first)'        (name the protocol you are about to run)
     want: lowpowermode 0 | 'AC Power' | docker backend: none | java/etf_risk: none |
           apps: only "Terminal" "Finder" | changed code files: 0 | spark scratch folders: 0
     If anything differs, fix it and run prechecks again.
  2. Window 2:  watch_runs        (waits for measure, then prints the run's elapsed time every 10 s)
  3. Window 1:  pause5 && avail 3.0 && protocol 21
     Leave the Mac alone. If avail is below the minimum, nothing starts: quit what is left and
     repeat step 3. Stride 3 only after the gate:  pause5 && avail <minimum from the gate> && protocol 3

Abort a run above:  s21 135 s (02:15) | s14 177 s (02:57) | s7 303 s (05:03) | s3 639 s (10:39)
  Window 2: Ctrl-C (stops only the watcher), then  abort_run  and answer y.
  After window 1 prints measure's summary:  after_abort    want: java: none | spark scratch folders: 0
  Then stop and come back to Claude.

After each protocol, read measure's summary in window 1.
  want: "runs started 4 of 4", four runs "ok", no "stopped:" line. Then record it, for example:
  note 'stride 21 (first): 4 ok, nothing unusual'        (single quotes; describe anything unusual)
  Anything else (failed, checks_failed, memory_threshold_exceeded, stopped): stop, come back.

Order: 21 -> Claude reviews -> 14 -> 7 -> Claude applies the 3.5 gate -> 3 only if admitted
       -> 21 again -> Claude.
Back to Claude: in window 1,  claude --continue  (or  claude --resume  and pick the conversation).
Before the next protocol: /exit, then start again at step 1. No git commits during the session.
Run log: data/outputs-experiments/run-log.txt (prechecks, pause5, avail, abort_run, after_abort, note).
EOF
}

_scratch_count() {
  find "$TMPDIR" /private/tmp -maxdepth 1 \( -name 'spark-*' -o -name 'blockmgr-*' \) 2>/dev/null | wc -l | tr -d ' '
}

prechecks() {
  {
    echo "=== ${1:-protocol}: checks at $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    pmset -g | grep lowpowermode
    pmset -g batt | head -n 1
    pgrep -fl com.docker.backend || echo "docker backend: none"
    pgrep -fl 'java|etf_risk' || echo "java/etf_risk: none"
    echo "apps: $(lsappinfo visibleProcessList | grep -o '"[^"]*"' | tr '\n' ' ')"
    echo "load average: $(sysctl -n vm.loadavg)"
    echo "HEAD $(git -C $REPO rev-parse --short HEAD), changed code files: $(git -C $REPO status --porcelain -- src pyproject.toml uv.lock | wc -l | tr -d ' ')"
    echo "spark scratch folders: $(_scratch_count)"
  } | tee -a $LOG
}

pause5() {
  echo "pause start $(date -u +%H:%M:%SZ)" | tee -a $LOG
  caffeinate -i sleep 300 || { echo "pause interrupted $(date -u +%H:%M:%SZ)" | tee -a $LOG; return 1; }
  echo "pause end $(date -u +%H:%M:%SZ)" | tee -a $LOG
}

# The 3.2 reading (the quantity measure records as free_memory_before_bytes); fails below the minimum.
avail() {
  local min=${1:-3.0} gib
  gib=$(uv run --group measure python -c "import psutil; print(round(psutil.virtual_memory().available / 2**30, 2))") || return 2
  echo "available GiB: $gib (minimum $min)" | tee -a $LOG
  (( gib >= min )) && return 0
  echo "below $min GiB: protocol not started" | tee -a $LOG
  return 1
}

# The 3.3 command, unchanged apart from the stride.
protocol() {
  case $1 in
    21|14|7|3) ;;
    *) echo "usage: protocol 21|14|7|3"; return 2 ;;
  esac
  [[ $PWD == $REPO ]] || { echo "run from $REPO"; return 2; }
  caffeinate -i uv run --group measure python -m etf_risk.measure --repeats 4 -- \
    --windows data/windows-experiments/full-2026-10-12/rolling-252-s$1 \
    --out-root data/outputs-experiments
}

watch_runs() {
  local pid
  until pgrep -qf etf_risk.measure; do sleep 5; done
  while pgrep -qf etf_risk.measure; do
    pid=$(pgrep -f etf_risk.spark_pipeline | head -n 1)
    [[ -n $pid ]] && echo "$(date +%H:%M:%S)  pipeline $pid  running $(ps -o etime= -p $pid | tr -d ' ')"
    sleep 10
  done
  echo "measure finished"
}

# 3.6: kill the pipeline process only, never measure, so the protocol JSON is still written.
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

echo "stride-session loaded: run log $LOG; type  steps  for the checklist"
