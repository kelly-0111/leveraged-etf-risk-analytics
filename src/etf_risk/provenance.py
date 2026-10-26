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

A process that starts records code_identity(), and each pipeline step its launch records
source_identity() (docs/recovery-experiments.md, 2.3): source_digest, one SHA-256 over the
whole source_sha256 map, and uv_lock_sha256 say whether two processes ran the same code;
the commit is only reported.

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_spark_equivalence.py (run.json carries these fields) and tests/test_provenance.py.
"""
from __future__ import annotations

import hashlib
import json
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


def source_digest(source_sha256: dict[str, str]) -> str:
    """One SHA-256 for a source_sha256 map: that of its canonical JSON (keys sorted, no spaces)."""
    return hashlib.sha256(json.dumps(source_sha256, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def source_identity() -> dict:
    """The code as files, without asking git: source_digest() of every source file's SHA-256,
    and uv.lock's SHA-256. Cheap enough to record at every step launch."""
    lock = REPO_ROOT / "uv.lock"
    return {"source_digest": source_digest({key: sha256_file(path) for key, path in source_files().items()}),
            "uv_lock_sha256": sha256_file(lock) if lock.is_file() else None}


def code_identity() -> dict:
    """What a starting process records: source_identity()'s two hashes, which decide whether
    two processes ran the same code, with the commit and the clean flag, reported only."""
    state = code_state()
    return {"git_commit": state["git_commit"], "git_worktree_clean": state["git_worktree_clean"],
            "source_digest": source_digest(state["source_sha256"]), "uv_lock_sha256": state["uv_lock_sha256"]}
