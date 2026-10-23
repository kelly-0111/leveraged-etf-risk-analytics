"""Record which code produced a result, including uncommitted changes.

A git commit alone does not identify the code when the worktree has changes, so
code_state() also records whether the worktree is clean and the SHA-256 of uv.lock and
of every Python module and SQL schema under src/etf_risk/, subpackages included (the
job queue in jobs/ and its schema files). Keys are paths relative to src/etf_risk/, so a
top-level module keeps the key it always had ("model.py") and jobs/__init__.py does not
collide with __init__.py. Records written before 2026-10-23 hash the top-level modules
only.

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
SOURCE_SUFFIXES = (".py", ".sql")

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


def source_files() -> dict[str, Path]:
    """Every Python module and SQL schema of the package, by path relative to it."""
    files = (p for p in PACKAGE_DIR.rglob("*") if p.suffix in SOURCE_SUFFIXES and p.is_file())
    return {p.relative_to(PACKAGE_DIR).as_posix(): p for p in sorted(files)}


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
        "source_sha256": {key: sha256_file(path) for key, path in source_files().items()},
        "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None,
    }
