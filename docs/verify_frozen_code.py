"""Did a recovery batch run on the frozen code? (docs/recovery-part-a.md, section 13)

    uv run --group jobs python docs/verify_frozen_code.py <batch folder> <frozen commit> <seed>

Recomputes, from the frozen commit's files, the source digest that every process of the batch
records (etf_risk.provenance: the SHA-256 of every .py and .sql file under src/etf_risk) and
uv.lock's SHA-256, then compares them with every code record in harness.jsonl: the batch's start
and end, and every process it started. Exits 0 only if all match, every record was taken with a
clean worktree, and the batch's plan has the expected seed.

Not run by the batch: a check after it, kept beside the session script
(docs/recovery-batch-3.zsh).

AI contribution: written with Claude Code (Opus 5.5) on 2026-10-27; checked by hand on a
preflight batch, against the commit it ran on (exit 0) and against a later commit (exit 1).
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from etf_risk.provenance import source_digest


def at(commit: str, path: str) -> bytes:
    return subprocess.run(["git", "show", f"{commit}:{path}"], capture_output=True, check=True).stdout


def main(folder: Path, frozen: str, seed: int) -> int:
    names = subprocess.run(["git", "ls-tree", "-r", "--name-only", frozen, "src/etf_risk"],
                           capture_output=True, text=True, check=True).stdout.split()
    digest = source_digest({n[len("src/etf_risk/"):]: hashlib.sha256(at(frozen, n)).hexdigest()
                            for n in names if n.endswith((".py", ".sql"))})
    lock = hashlib.sha256(at(frozen, "uv.lock")).hexdigest()
    events = [json.loads(line) for line in (folder / "harness.jsonl").read_text().splitlines() if line.strip()]
    codes = [e["code"] for e in events if e.get("event") in ("batch_started", "batch_ended", "process_started")
             and "code" in e]
    plan = json.loads((folder / "plan.json").read_text())
    same = bool(codes) and all(c.get("source_digest") == digest for c in codes)
    locked = bool(codes) and all(c.get("uv_lock_sha256") == lock for c in codes)
    clean = bool(codes) and all(c.get("git_worktree_clean") is True for c in codes)
    print(f"commit recorded: {codes[0].get('git_commit') if codes else None}; code records: {len(codes)}")
    print(f"source digest matches {frozen}: {same}; uv.lock matches: {locked}; clean worktree: {clean}")
    print(f"plan: purpose {plan.get('purpose')}, seed {plan.get('seed')} (expected {seed})")
    ok = same and locked and clean and plan.get("seed") == seed
    print("FROZEN CODE: VERIFIED" if ok else "FROZEN CODE: NOT VERIFIED")
    return 0 if ok else 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])))
