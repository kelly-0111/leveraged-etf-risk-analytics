"""Record which code produced a result, including uncommitted changes.

A git commit alone does not identify the code when the worktree has changes, so
code_state() also records whether the worktree is clean and the SHA-256 of every
module in src/etf_risk/ and of uv.lock.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_spark_equivalence.py (run.json carries these fields).
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from etf_risk.ingest import sha256_file

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]


def resolve(path: str | Path) -> Path:
    """Paths stored in configs are relative to the repository root unless absolute."""
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def code_state() -> dict:
    head = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain", "--untracked-files=all", "--", "src", "pyproject.toml", "uv.lock")
    lock = REPO_ROOT / "uv.lock"
    return {
        "git_commit": head or "unknown",
        # False means the code that ran is not exactly the recorded commit; source_sha256 identifies it.
        "git_worktree_clean": (status == "") if head and status is not None else None,
        "source_sha256": {p.name: sha256_file(p) for p in sorted(PACKAGE_DIR.glob("*.py"))},
        "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
    }
