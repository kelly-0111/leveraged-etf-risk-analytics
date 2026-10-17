"""code_state(): git when available, the Docker image's build record otherwise.

AI contribution: written with Claude Code (Opus 5.5).
"""
import pytest

from etf_risk import provenance


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
