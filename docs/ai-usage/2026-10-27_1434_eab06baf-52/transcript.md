# Claude Code message 52

Session: `eab06baf-de8e-4e5f-830e-4907c7544308` · prompt sent 2026-10-27 14:34 (local time)

Redacted record: [transcript.jsonl](transcript.jsonl)

This readable view includes user/assistant messages and tool calls/results. Internal reasoning and session metadata are omitted.

Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): git-user ×15, home ×210, memory ×28, model-reasoning ×23, private-term ×3, user ×51. Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.

## 1. User — 2026-10-27T19:34:36.973Z



<pasted_content id="2323">
I approve one additional formal batch, batch-3, reusing plan-544.json unchanged. Freeze the executable code at 4fc550e. The localized event-text privacy fix does not require another live preflight; record this exception and its verification.

If batch-3 is invalid, retain and report it and stop. No further formal batch is authorized automatically.

Commit the protocol amendment and freeze documentation by explicit path. Then provide a short session script with enforced preconditions, pipefail, and a separate frozen-code verification command. Avoid a long inline Python command and ensure failed preconditions prevent the batch from starting.

Do not start the batch automatically.
</pasted_content id="2323">


## 2. Assistant — 2026-10-27T19:34:59.001Z

Before writing, one constraint shapes where the new files go. The freeze check compares `src`, `analysis`, `tests`, `pyproject.toml` and `uv.lock` against `4fc550e`, so a new script in any of those would break the freeze. The session script and the verifier aren't run by the batch, so I'll put them in `docs/`, next to the existing session helpers, and the freeze record will say so.

I'll also fingerprint `plan-544.json` now, so the session script can refuse a plan that has changed:

## 3. Assistant — 2026-10-27T19:35:01.337Z

### Tool call: Bash

```
{
  "command": "shasum -a 256 data/outputs-recovery/formal/plan-544.json && stat -f \"%Sm\" data/outputs-recovery/formal/plan-544.json && python3 -c \"import json; p=json.load(open('data/outputs-recovery/formal/plan-544.json')); print(p['seed'], p['purpose'], len(p['jobs']))\"; uv run --group jobs python -m etf_risk.services others --help 2>&1 | grep -i -E \"require\" | head -2",
  "description": "Fingerprint the approved plan and check the services option"
}
```

## 4. User — 2026-10-27T19:35:03.115Z

### Tool result

```
c74b125eddd87ca1ce891a63f11fe72b0da8b00f2bf6db651020c370d5ffa7b6  data/outputs-recovery/formal/plan-544.json
Oct 25 00:14:50 2026
544 formal 30
usage: python -m etf_risk.services others [-h] [--require-none]
  --require-none  exit 1 if any is running
```

## 5. Assistant — 2026-10-27T19:35:14.944Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/verify_frozen_code.py",
  "content": "\"\"\"Did a recovery batch run on the frozen code? (docs/recovery-part-a.md, section 13)\n\n    uv run --group jobs python docs/verify_frozen_code.py <batch folder> <frozen commit> <seed>\n\nRecomputes, from the frozen commit's files, the source digest that every process of the batch\nrecords (etf_risk.provenance: the SHA-256 of every .py and .sql file under src/etf_risk) and\nuv.lock's SHA-256, then compares them with every code record in harness.jsonl: the batch's start\nand end, and every process it started. Exits 0 only if all match, every record was taken with a\nclean worktree, and the batch's plan has the expected seed.\n\nNot run by the batch: a check after it, kept beside the session script\n(docs/recovery-batch-3.zsh).\n\nAI contribution: written with Claude Code (Opus 5.5) on 2026-10-27; checked by hand on a\npreflight batch, against the commit it ran on (exit 0) and against a later commit (exit 1).\n\"\"\"\nimport hashlib\nimport json\nimport subprocess\nimport sys\nfrom pathlib import Path\n\nfrom etf_risk.provenance import source_digest\n\n\ndef at(commit: str, path: str) -> bytes:\n    return subprocess.run([\"git\", \"show\", f\"{commit}:{path}\"], capture_output=True, check=True).stdout\n\n\ndef main(folder: Path, frozen: str, seed: int) -> int:\n    names = subprocess.run([\"git\", \"ls-tree\", \"-r\", \"--name-only\", frozen, \"src/etf_risk\"],\n                           capture_output=True, text=True, check=True).stdout.split()\n    digest = source_digest({n[len(\"src/etf_risk/\"):]: hashlib.sha256(at(frozen, n)).hexdigest()\n                            for n in names if n.endswith((\".py\", \".sql\"))})\n    lock = hashlib.sha256(at(frozen, \"uv.lock\")).hexdigest()\n    events = [json.loads(line) for line in (folder / \"harness.jsonl\").read_text().splitlines() if line.strip()]\n    codes = [e[\"code\"] for e in events if e.get(\"event\") in (\"batch_started\", \"batch_ended\", \"process_started\")\n             and \"code\" in e]\n    plan = json.loads((folder / \"plan.json\").read_text())\n    same = bool(codes) and all(c.get(\"source_digest\") == digest for c in codes)\n    locked = bool(codes) and all(c.get(\"uv_lock_sha256\") == lock for c in codes)\n    clean = bool(codes) and all(c.get(\"git_worktree_clean\") is True for c in codes)\n    print(f\"commit recorded: {codes[0].get('git_commit') if codes else None}; code records: {len(codes)}\")\n    print(f\"source digest matches {frozen}: {same}; uv.lock matches: {locked}; clean worktree: {clean}\")\n    print(f\"plan: purpose {plan.get('purpose')}, seed {plan.get('seed')} (expected {seed})\")\n    ok = same and locked and clean and plan.get(\"seed\") == seed\n    print(\"FROZEN CODE: VERIFIED\" if ok else \"FROZEN CODE: NOT VERIFIED\")\n    return 0 if ok else 1\n\n\nif __name__ == \"__main__\":\n    if len(sys.argv) != 4:\n        sys.exit(__doc__)\n    sys.exit(main(Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])))\n"
}
```

## 6. User — 2026-10-27T19:35:15.806Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/verify_frozen_code.py (file state is current in your context — no need to Read it back)
```

## 7. Assistant — 2026-10-27T19:35:18.637Z

Now the session script. It refuses to start the batch unless every precondition passes. A `--check` mode runs only the preconditions, so it can be exercised safely without starting anything.

## 8. Assistant — 2026-10-27T19:35:28.327Z

### Tool call: Write

```
{
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-batch-3.zsh",
  "content": "#!/bin/zsh\n# The recovery experiments' formal batch-3 (docs/recovery-part-a.md, section 13): one batch on the\n# frozen code 4fc550e with the approved plan-544.json, run by the author from Terminal with the\n# editor and other applications closed. Written with Claude Code (Opus 5.5) on 2026-10-27.\n#\n#   zsh docs/recovery-batch-3.zsh --check   preconditions only; starts nothing\n#   zsh docs/recovery-batch-3.zsh           preconditions, then the batch, the collection and the cleanup check\n#\n# Any failed precondition stops the script before the batch starts. Afterwards, separately:\n#   uv run --group jobs python docs/verify_frozen_code.py data/outputs-recovery/formal/batch-3 4fc550e 544\n\nset -euo pipefail\ncd ${0:A:h:h}\n\nFROZEN=4fc550e\nPLAN=data/outputs-recovery/formal/plan-544.json\nPLAN_SHA256=c74b125eddd87ca1ce891a63f11fe72b0da8b00f2bf6db651020c370d5ffa7b6\nOUT=data/outputs-recovery/formal/batch-3\nUV=(uv run --group jobs)\n\nfail() { print -r -- \"PRECONDITION FAILED: $1\"; exit 2 }\n\ngit diff --quiet $FROZEN -- src analysis tests pyproject.toml uv.lock || fail \"the code differs from $FROZEN\"\n[[ -z \"$(git status --porcelain)\" ]] || fail \"the worktree is not clean\"\n[[ \"$(shasum -a 256 $PLAN | cut -d' ' -f1)\" == $PLAN_SHA256 ]] || fail \"$PLAN is not the approved plan\"\n[[ ! -e $OUT ]] || fail \"$OUT exists: a batch is never overwritten\"\n[[ -z \"$(docker compose -f docker/compose.yaml ps -a -q)\" ]] || fail \"this project's containers exist\"\n$UV python -m etf_risk.services others --require-none || fail \"another project's container is running\"\n! pgrep -f 'pytest|etf_risk\\.jobs|org\\.apache\\.spark' >/dev/null || fail \"a test, job or Spark process is running\"\npmset -g batt | head -1 | grep -q \"'AC Power'\" || fail \"not on AC power\"\nioreg -r -k AppleClamshellState -d 4 | grep -q '\"AppleClamshellState\" = No' || fail \"the lid is closed or unknown\"\nprint \"preconditions: all hold (code $FROZEN, plan $PLAN, folder $OUT)\"\n[[ ${1:-} == --check ]] && exit 0\n\ncaffeinate -dims $UV python -m etf_risk.jobs.harness batch --plan $PLAN --out $OUT --formal 2>&1 | tee $OUT.console.log\ncollected=0\n$UV python analysis/collect_recovery_measurements.py --batch $OUT 2>&1 | tee $OUT.collect.log || collected=$?\nleft=$(docker compose -f docker/compose.yaml ps -a -q)\n[[ -z $left ]] && print \"cleanup: no container of this project left\" || print \"CLEANUP NEEDED: this project's containers remain\"\nprint \"collector exit $collected (0 only if both verdicts are valid); now run docs/verify_frozen_code.py\"\nexit $collected\n"
}
```

## 9. User — 2026-10-27T19:35:29.160Z

### Tool result

```
File created successfully at: ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-batch-3.zsh (file state is current in your context — no need to Read it back)
```

## 10. Assistant — 2026-10-27T19:35:40.436Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-batch-3.zsh",
  "old_string": "caffeinate -dims $UV python -m etf_risk.jobs.harness batch --plan $PLAN --out $OUT --formal 2>&1 | tee $OUT.console.log\ncollected=0\n$UV python analysis/collect_recovery_measurements.py --batch $OUT 2>&1 | tee $OUT.collect.log || collected=$?\nleft=$(docker compose -f docker/compose.yaml ps -a -q)\n[[ -z $left ]] && print \"cleanup: no container of this project left\" || print \"CLEANUP NEEDED: this project's containers remain\"\nprint \"collector exit $collected (0 only if both verdicts are valid); now run docs/verify_frozen_code.py\"\nexit $collected",
  "new_string": "ran=0                                  # a batch that ends with an error is still collected and kept\ncaffeinate -dims $UV python -m etf_risk.jobs.harness batch --plan $PLAN --out $OUT --formal 2>&1 | tee $OUT.console.log || ran=$?\ncollected=0\n$UV python analysis/collect_recovery_measurements.py --batch $OUT 2>&1 | tee $OUT.collect.log || collected=$?\nleft=$(docker compose -f docker/compose.yaml ps -a -q)\n[[ -z $left ]] && print \"cleanup: no container of this project left\" || print \"CLEANUP NEEDED: this project's containers remain\"\nprint \"batch exit $ran; collector exit $collected (0 only if both verdicts are valid)\"\nprint \"next: uv run --group jobs python docs/verify_frozen_code.py $OUT $FROZEN 544\"\n(( ran == 0 && collected == 0 ))"
}
```

## 11. Assistant — 2026-10-27T19:35:44.272Z

### Tool call: Bash

```
{
  "command": "zsh -n docs/recovery-batch-3.zsh && echo \"zsh syntax ok\"; python3 -c \"import ast; ast.parse(open('docs/verify_frozen_code.py').read()); print('py syntax ok')\"; B=$(sed -n 2p /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/e2_preflight.txt); uv run --group jobs python docs/verify_frozen_code.py $B 12c925d 1; echo \"exit $? (expected 0)\"; uv run --group jobs python docs/verify_frozen_code.py $B 4fc550e 1; echo \"exit $? (expected 1)\"; uv run --group jobs python docs/verify_frozen_code.py $B 12c925d 544; echo \"exit $? (expected 1: wrong seed)\"",
  "description": "Check syntax and test the verifier file three ways"
}
```

## 12. User — 2026-10-27T19:35:46.475Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-batch-3.zsh has been updated successfully. (file state is current in your context — no need to Read it back)
```

## 13. User — 2026-10-27T19:35:49.642Z

### Tool result

```
zsh syntax ok
py syntax ok
commit recorded: 12c925d12bdef26f44279c64932a63daddab461f; code records: 5
source digest matches 12c925d: True; uv.lock matches: True; clean worktree: True
plan: purpose preflight, seed 1 (expected 1)
FROZEN CODE: VERIFIED
exit 0 (expected 0)
commit recorded: 12c925d12bdef26f44279c64932a63daddab461f; code records: 5
source digest matches 4fc550e: False; uv.lock matches: True; clean worktree: True
plan: purpose preflight, seed 1 (expected 1)
FROZEN CODE: NOT VERIFIED
exit 1 (expected 1)
commit recorded: 12c925d12bdef26f44279c64932a63daddab461f; code records: 5
source digest matches 12c925d: True; uv.lock matches: True; clean worktree: True
plan: purpose preflight, seed 1 (expected 544)
FROZEN CODE: NOT VERIFIED
exit 1 (expected 1: wrong seed)
```

## 14. Assistant — 2026-10-27T19:36:02.308Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-a.md",
  "old_string": "  It also records whether the log reaches back to the batch's start. The evidence is reported\n  beside the clock and lid checks, never as a gate, and a batch without it says so.",
  "new_string": "  It also records whether the log reaches back to the batch's start. The evidence is reported\n  beside the clock and lid checks, never as a gate, and a batch without it says so.\n- **Formal batch-3 (2026-10-27, the author's decision; amends row 11 of section 10).**\n  - **What is allowed.** One more formal batch, `formal/batch-3`, beyond row 11's one rerun, which\n    batch-2 used. If batch-3 is invalid or stops early, it is kept and reported in full, and the\n    formal batches stop. No further formal batch runs without a new decision. batch-1, batch-2 and\n    batch-3 are reported side by side.\n  - **The plan:** `formal/plan-544.json`, unchanged (seed 544; SHA-256 `c74b125e…5ffa7b6`).\n    Regenerated at the frozen code, it gives the same 30 jobs in the same order with the same\n    settings.\n  - **The code is frozen at `4fc550e`** for `src`, `analysis`, `tests`, `pyproject.toml` and\n    `uv.lock`, which replaces row 13's `fcaa645` for batch-3. Later commits change only documents\n    and the session tooling below, which the batch does not run.\n  - **Its verification:**\n    - the full offline suite on `12c925d` (1078 passed, 38 skipped for live services, 0 failed);\n    - a live C0–D1–C0 preflight on `12c925d`, valid on every check\n      (`preflight/20261027T191959Z-e2-c0-d1-c0`);\n    - then `4fc550e`.\n  - **An exception to row 11's preflight-first rule, at the author's decision.** `4fc550e` changed\n    one thing after that preflight: container events keep only the action's verb, never the\n    command Docker appends, so that no command line of another project's container is recorded.\n    It got no new live preflight and no new full suite. Its verification:\n    - two regression tests with a private-looking value, absent from what is recorded;\n    - the focused suites of the shared monitor, the recovery tooling and the result-cache\n      experiment, 205 passed;\n    - 6 of 6 mutation checks caught, among them one that restores the full action text.\n  - **The session:** `docs/recovery-batch-3.zsh`, run from Terminal with the editor and other\n    applications closed. It refuses to start unless all of these hold:\n    - the code equals `4fc550e`, the worktree is clean and the plan is unchanged;\n    - the batch folder is new;\n    - no container of this project exists and no other project's container runs;\n    - no test, job or Spark process runs;\n    - AC power, and the lid open.\n\n    It runs with `pipefail`, and collects the batch even when the batch ends with an error.\n  - **After the session:** `docs/verify_frozen_code.py` confirms that every code record of the\n    batch matches `4fc550e`, with a clean worktree and seed 544."
}
```

## 15. Assistant — 2026-10-27T19:36:04.409Z

### Tool call: Bash

```
{
  "command": "{ git diff; cat docs/recovery-batch-3.zsh docs/verify_frozen_code.py; } | grep -n -i -E \"/Users/|/private/|[REDACTED:private-term]\\.|jyr2006|gmail|implementation-plan|scratchpad|\\.claude/projects\" || echo \"privacy scan: no hits\"; git status --porcelain; git diff --quiet 4fc550e -- src analysis tests pyproject.toml uv.lock && echo \"frozen paths unchanged vs 4fc550e\"",
  "description": "Privacy scan and confirm frozen paths are untouched"
}
```

## 16. User — 2026-10-27T19:36:06.689Z

### Tool result

```
The file ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence/docs/recovery-part-a.md has been updated successfully.
```

## 17. User — 2026-10-27T19:36:06.883Z

### Tool result

```
privacy scan: no hits
 M docs/recovery-part-a.md
?? docs/recovery-batch-3.zsh
?? docs/verify_frozen_code.py
frozen paths unchanged vs 4fc550e
```

## 18. Assistant — 2026-10-27T19:36:09.007Z

The privacy scan is clean and the frozen paths are unchanged. Committing the amendment, session script and verifier by explicit path:

## 19. Assistant — 2026-10-27T19:36:16.082Z

### Tool call: Write

```
{
  "file_path": "/private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/commit-freeze-batch3.txt",
  "content": "Approve formal batch-3 and freeze the recovery code at 4fc550e\n\nDocuments and session tooling only; src, analysis, tests, pyproject.toml and uv.lock are\nunchanged against 4fc550e. As the author decided on 2026-10-27 (recovery-part-a.md, section 13):\n- One more formal batch, formal/batch-3, beyond row 11's one rerun, which batch-2 used. If\n  batch-3 is invalid or stops early, it is kept and reported, and the formal batches stop; no\n  further batch runs without a new decision.\n- The plan: formal/plan-544.json, unchanged (seed 544), whose SHA-256 the session checks.\n- The code is frozen at 4fc550e. Its verification: the full offline suite and the C0-D1-C0\n  preflight on 12c925d. The event-text privacy fix in 4fc550e is a recorded exception to the\n  preflight-first rule: two regression tests, 205 focused tests passed and 6 of 6 mutations\n  caught, with no new live preflight or full suite.\n- docs/recovery-batch-3.zsh: the session. It refuses to start unless the code equals 4fc550e,\n  the worktree is clean, the plan is unchanged, the folder is new, no container of this project\n  exists, no other project's container runs, no test, job or Spark process runs, and the Mac is\n  on AC power with the lid open. It runs with pipefail, collects even a batch that ended with an\n  error, and checks the cleanup. --check runs the preconditions only.\n- docs/verify_frozen_code.py: after the session, checks every code record of the batch against\n  the frozen commit's source digest and uv.lock, the clean worktree and the seed. It was checked\n  on a preflight batch: verified against the commit it ran on, not verified against a later\n  commit or with the wrong seed.\n\nContributed by both: Claude Code drafted and wrote the tooling; the author decided.\n\nCo-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>\n"
}
```

## 20. User — 2026-10-27T19:36:16.951Z

### Tool result

```
File created successfully at: /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/commit-freeze-batch3.txt (file state is current in your context — no need to Read it back)
```

## 21. Assistant — 2026-10-27T19:36:18.882Z

### Tool call: Bash

```
{
  "command": "git add -- docs/recovery-part-a.md docs/recovery-batch-3.zsh docs/verify_frozen_code.py && git commit -q -F /private/tmp/claude-501/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/eab06baf-de8e-4e5f-830e-4907c7544308/scratchpad/commit-freeze-batch3.txt && git log --oneline -3 && echo \"status lines: $(git status --porcelain | wc -l | tr -d ' ')\" && git diff --name-only 4fc550e HEAD",
  "description": "Commit the freeze and session tooling by explicit path"
}
```

## 22. User — 2026-10-27T19:36:21.344Z

### Tool result

```
c5c340a Approve formal batch-3 and freeze the recovery code at 4fc550e
4fc550e Keep only the verb of a Docker event's action, never its command
12c925d Record recovery batches' page and swap counters by name, and watch containers batch-wide
status lines: 0
docs/recovery-batch-3.zsh
docs/recovery-part-a.md
docs/verify_frozen_code.py
```

## 23. Assistant — 2026-10-27T19:36:28.242Z

### Tool call: Bash

```
{
  "command": "zsh docs/recovery-batch-3.zsh --check; echo \"exit $?\"; touch precondition-probe.tmp; zsh docs/recovery-batch-3.zsh --check; echo \"exit $? (expected 2)\"; rm -f precondition-probe.tmp; echo \"status lines: $(git status --porcelain | wc -l | tr -d ' ')\"; ls -d data/outputs-recovery/formal/batch-3 2>/dev/null || echo \"batch-3 not created\"",
  "description": "Exercise the session script's precondition gate both ways"
}
```

## 24. User — 2026-10-27T19:36:35.251Z

### Tool result

```
0 running container(s) outside the etf-risk-jobs project
preconditions: all hold (code 4fc550e, plan data/outputs-recovery/formal/plan-544.json, folder data/outputs-recovery/formal/batch-3)
exit 0
PRECONDITION FAILED: the worktree is not clean
exit 2 (expected 2)
status lines: 0
batch-3 not created
```

## 25. Assistant — 2026-10-27T19:36:43.798Z

### Tool call: Edit

```
{
  "replace_all": false,
  "file_path": "~/.claude/projects/-Users-[REDACTED:user]-leveraged-etf-risk-analytics/memory/e2-evidence-plan.md",
  "old_string": "[REDACTED:memory]",
  "new_string": "[REDACTED:memory]"
}
```

## 26. User — 2026-10-27T19:36:44.618Z

### Tool result

```
[REDACTED:memory]
```

## 27. Assistant — 2026-10-27T19:36:56.015Z

The protocol amendment and freeze are committed (`c5c340a`), and the session script and verifier are ready and checked. I haven't started batch-3, pushed or merged.

## What's committed
`c5c340a` changes only documentation and session tooling: `src`, `analysis`, `tests`, `pyproject.toml` and `uv.lock` are identical to `4fc550e`. It adds a dated entry to M3 Part A §13:
- **batch-3 approved** as one batch beyond the original single rerun. If it's invalid or stops early, it's kept and reported, and formal batches stop until you decide otherwise.
- **The plan:** `plan-544.json` reused unchanged (seed 544). The script checks its SHA-256 (`c74b125e…`).
- **Code frozen at `4fc550e`.** The verification behind it:
  - the full offline suite on `12c925d`: 1078 passed, 38 live-service skips, 0 failed;
  - the valid C0–D1–C0 preflight on `12c925d`.
- **The recorded exception:** the event-text privacy fix in `4fc550e` got no new live preflight or full suite. It was verified by two regression tests, 205 focused tests passing, and 6 of 6 mutation checks caught.

## The session script: `docs/recovery-batch-3.zsh`
- **Strict mode:** it runs with `set -euo pipefail`.
- **Enforced preconditions** (exit 2 on the first failure, before the batch starts):
  - the code equals `4fc550e`;
  - the worktree is clean;
  - the plan is unchanged;
  - `batch-3` doesn't exist yet;
  - no container of this project exists, and no other project's container is running;
  - no test, job or Spark process is running;
  - AC power, and the lid open.
- **Then:** the batch under `caffeinate -dims`, the collection (run even if the batch ends with an error), and a cleanup check. Console and collector output go to `batch-3.console.log` and `batch-3.collect.log`.
- **`--check`** runs the preconditions only. I tried it on the real state (all hold, exit 0) and with a stray file in the worktree (stopped with exit 2).

**The separate check, `docs/verify_frozen_code.py`,** runs after the batch. It confirms every code record matches `4fc550e`, the worktree was clean, and the seed is 544. On the earlier preflight it returned verified for the commit that preflight ran on, and not verified for a different commit or the wrong seed.

## To run (from Terminal, with the editor and other apps closed)
```zsh
cd ~/leveraged-etf-risk-analytics/.claude/worktrees/e2-evidence
deactivate 2>/dev/null
zsh docs/recovery-batch-3.zsh --check
zsh docs/recovery-batch-3.zsh
uv run --group jobs python docs/verify_frozen_code.py data/outputs-recovery/formal/batch-3 4fc550e 544
```

The batch is estimated at about 51 minutes. The script exits 0 only if the batch and the collector both succeed, meaning both verdicts are valid; the verifier must then print `FROZEN CODE: VERIFIED`. Closing the editor ends this session, so send me the output afterwards and I'll analyse it. The branch `feature/e2-evidence-tooling` is three commits ahead of `main` and not pushed.
