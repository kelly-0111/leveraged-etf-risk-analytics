"""code_state(): git when available, the Docker image's build record otherwise; the source
hashes cover every module and schema file of the package, subpackages included.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
from pathlib import Path

import pytest

from etf_risk import provenance
from etf_risk.ingest import sha256_file


@pytest.fixture
def no_build_record(monkeypatch):
    for name in (provenance.BUILD_COMMIT_ENV, provenance.BUILD_CLEAN_ENV, provenance.IMAGE_ID_ENV):
        monkeypatch.delenv(name, raising=False)


def test_git_is_used_when_available(monkeypatch, no_build_record):
    answers = {"rev-parse": "abc123", "status": ""}
    monkeypatch.setattr(provenance, "_git", lambda *args: answers[args[0]])
    monkeypatch.setenv(provenance.BUILD_COMMIT_ENV, "from-build")        # ignored while git answers
    state = provenance.code_state()
    assert (state["git_commit"], state["git_worktree_clean"], state["code_source"]) == ("abc123", True, "git")
    answers["status"] = " M src/etf_risk/model.py"
    assert provenance.code_state()["git_worktree_clean"] is False


def test_build_record_is_used_without_git(monkeypatch, no_build_record):
    monkeypatch.setattr(provenance, "_git", lambda *args: None)
    monkeypatch.setenv(provenance.BUILD_COMMIT_ENV, "def456")
    monkeypatch.setenv(provenance.BUILD_CLEAN_ENV, "false")
    monkeypatch.setenv(provenance.IMAGE_ID_ENV, "sha256:0123")
    state = provenance.code_state()
    assert (state["git_commit"], state["git_worktree_clean"], state["code_source"], state["image_id"]) == (
        "def456", False, "build", "sha256:0123")
    assert "provenance.py" in state["source_sha256"]                     # the code itself is still hashed


def test_nothing_is_claimed_without_git_or_build_record(monkeypatch, no_build_record):
    monkeypatch.setattr(provenance, "_git", lambda *args: None)
    state = provenance.code_state()
    assert (state["git_commit"], state["git_worktree_clean"], state["code_source"], state["image_id"]) == (
        "unknown", None, "unknown", None)


def test_every_module_and_schema_is_hashed_under_its_path_in_the_package(monkeypatch, no_build_record):
    """jobs/ and its schema files included. Keys are relative to src/etf_risk/, so the two
    __init__.py files do not collide. The package is walked here independently of
    provenance.source_files()."""
    monkeypatch.setattr(provenance, "_git", lambda *args: None)
    hashed = provenance.code_state()["source_sha256"]
    on_disk = {}
    for folder, _, names in os.walk(provenance.PACKAGE_DIR):
        for name in names:
            if name.endswith((".py", ".sql")):
                path = Path(folder) / name
                on_disk[path.relative_to(provenance.PACKAGE_DIR).as_posix()] = sha256_file(path)
    assert hashed == on_disk
    assert {"__init__.py", "jobs/__init__.py", "jobs/store.py", "jobs/schema/mysql.sql",
            "jobs/schema/sqlite.sql"} <= set(hashed)


def test_top_level_modules_keep_the_keys_of_earlier_records(monkeypatch, no_build_record):
    """Records before 2026-10-23 hashed src/etf_risk/*.py by file name; those entries are unchanged."""
    monkeypatch.setattr(provenance, "_git", lambda *args: None)
    hashed = provenance.code_state()["source_sha256"]
    earlier = {p.name: sha256_file(p) for p in sorted(provenance.PACKAGE_DIR.glob("*.py"))}
    assert {name: hashed[name] for name in earlier} == earlier
