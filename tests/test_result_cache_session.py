"""The E3 session helpers (docs/result-cache-session.zsh): loading, and the refusals that keep a
step from running out of order. zsh loads the file; no service, plan or batch is started.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "docs" / "result-cache-session.zsh"
pytestmark = pytest.mark.skipif(shutil.which("zsh") is None, reason="needs zsh")


def zsh(script: str, **env: str) -> subprocess.CompletedProcess:
    environment = {**os.environ, "E3_BATCH": "t-batch", **env}
    return subprocess.run(["zsh", "-c", f"source {HELPER} >/dev/null && {script}"], cwd=REPO, capture_output=True,
                          text=True, timeout=60, env=environment)


def test_the_helper_file_parses():
    assert subprocess.run(["zsh", "-n", str(HELPER)], capture_output=True).returncode == 0


def test_loading_sets_the_defaults_and_changes_into_the_repository():
    out = zsh('print -r -- $PWD; print -r -- $E3_PURPOSE $E3_SEED $E3_SWAP_OUT_MIB $E3_DRIFT; print -r -- $E3_DIR')
    assert out.returncode == 0, out.stderr
    assert out.stdout.splitlines() == [str(REPO), "dry-run 1 64 0.20", "data/outputs-result-cache/dry-run/t-batch"]


def test_the_checklist_names_every_step():
    out = zsh("e3_steps")
    assert all(f in out.stdout for f in ("e3_redis", "e3_preflight", "e3_plan", "e3_run", "e3_collect", "e3_cleanup"))


def test_an_unknown_purpose_plans_nothing():
    out = zsh("e3_plan", E3_PURPOSE="practice")
    assert out.returncode == 2 and "must be formal, dry-run or sizing" in out.stdout


def test_run_refuses_without_a_plan():
    out = zsh("e3_run", E3_BATCH="no-such-batch")
    assert out.returncode == 2 and "e3_plan first" in out.stdout


def test_cleanup_names_the_redis_service_alone():
    body = HELPER.read_text().split("e3_cleanup() {", 1)[1].split("}", 1)[0]
    assert "rm --stop --force redis" in body and "down" not in body
