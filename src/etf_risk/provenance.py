"""Record which code produced a result, including uncommitted changes.

A git commit alone does not identify the code when the worktree has changes, so
code_state() also records whether the worktree is clean and the SHA-256 of every
module in src/etf_risk/ and of uv.lock.

The Docker image has no .git: there the commit and the clean flag come from what
docker/build.sh recorded at build time (code_source = "build"), and docker/run.sh
passes the image ID.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_spark_equivalence.py (run.json carries these fields) and tests/test_provenance.py.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

from etf_risk.ingest import sha256_file

PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[1]

# Set in the Docker image (Dockerfile, from docker/build.sh) and by docker/run.sh.
BUILD_COMMIT_ENV = "ETF_RISK_GIT_COMMIT"
BUILD_CLEAN_ENV = "ETF_RISK_GIT_WORKTREE_CLEAN"
IMAGE_ID_ENV = "ETF_RISK_IMAGE_ID"


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
    if head:
        source, commit, clean = "git", head, (status == "") if status is not None else None
    elif os.environ.get(BUILD_COMMIT_ENV):
        source, commit = "build", os.environ[BUILD_COMMIT_ENV]
        clean = {"true": True, "false": False}.get(os.environ.get(BUILD_CLEAN_ENV, "").lower())
    else:
        source, commit, clean = "unknown", "unknown", None
    lock = REPO_ROOT / "uv.lock"
    return {
        "git_commit": commit,
        # False means the code that ran is not exactly the recorded commit; source_sha256 identifies it.
        "git_worktree_clean": clean,
        "code_source": source,
        "image_id": os.environ.get(IMAGE_ID_ENV) or None,
        "source_sha256": {p.name: sha256_file(p) for p in sorted(PACKAGE_DIR.glob("*.py"))},
        "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
    }
