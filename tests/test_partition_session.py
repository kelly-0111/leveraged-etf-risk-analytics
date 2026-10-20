"""The session helpers (docs/partition-session.zsh): loading, the order of positions and the ready gate.

zsh loads the helper file with a scratch batch folder; no protocol is started.

AI contribution: written with Claude Code (Opus 5.5).
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HELPER = REPO / "docs" / "partition-session.zsh"
pytestmark = pytest.mark.skipif(shutil.which("zsh") is None, reason="needs zsh")


def zsh(tmp_path: Path, script: str, **env: str) -> subprocess.CompletedProcess:
    environment = {**os.environ, "PART_ROOT": str(tmp_path), "BATCH": "t", **env}
    return subprocess.run(["zsh", "-c", f"source {HELPER} >/dev/null && {script}"], cwd=tmp_path,
                          capture_output=True, text=True, timeout=120, env=environment)


def test_the_helper_file_parses():
    assert subprocess.run(["zsh", "-n", str(HELPER)], capture_output=True).returncode == 0


def test_loading_sets_the_order_and_flags_and_changes_into_the_repository(tmp_path):
    out = zsh(tmp_path, 'print -r -- $PWD; print -r -- "${PART_ORDER[*]}"; print -r -- $PART_FLAGS[A]; '
                        'print -r -- $PART_FLAGS[B]; print -r -- $PART_FLAGS[C]; print -r -- $BATCH_DIR')
    assert out.returncode == 0, out.stderr
    assert out.stdout.splitlines() == [
        str(REPO), "A B C C B A", "--shuffle-partitions 200 --coalesce on", "--shuffle-partitions 200 --coalesce off",
        "--shuffle-partitions 8 --coalesce off", str(tmp_path / "t")]


def test_position_refuses_numbers_outside_1_to_6(tmp_path):
    out = zsh(tmp_path, "for n in 0 7 x; do position $n; print rc=$?; done")
    assert out.stdout.count("usage: position 1-6") == 3 and out.stdout.count("rc=2") == 3
    assert not any(p.is_dir() for p in (tmp_path / "t").iterdir())      # no configuration folder: nothing ran


def test_the_watcher_reads_elapsed_times_and_each_configurations_abort_limit(tmp_path):
    cases = {"45": 45, "00:08": 8, "01:17": 77, "1:39": 99, "02:03:04": 7384, "1-02:03:04": 93784}
    out = zsh(tmp_path, "; ".join(f"print -r -- $(_etime_seconds {t})" for t in cases))
    assert [int(v) for v in out.stdout.split()] == list(cases.values()), out.stderr
    commands = {"A": "--shuffle-partitions 200 --coalesce on", "B": "--shuffle-partitions 200 --coalesce off",
                "C": "--shuffle-partitions 8 --coalesce off", "?": "--windows w"}
    script = "; ".join(f'c=$(_config_of "python -m etf_risk.spark_pipeline {flags} --record-plans --run-id r"); '
                       'print -r -- "$c ${PART_ABORT_S[$c]:-none}"' for flags in commands.values())
    assert zsh(tmp_path, script).stdout.splitlines() == ["A 77", "B 99", "C 77", "? none"]


@pytest.mark.parametrize("limits, args, expected", [
    ({"PART_BOOT_MIN": "0", "PART_LOAD_MAX": "1000"}, "0", None),
    ({"PART_BOOT_MIN": "0", "PART_LOAD_MAX": "1000"}, "100000", "below 100000 GiB"),
    ({"PART_BOOT_MIN": "0", "PART_LOAD_MAX": "0"}, "0", "load above 0"),
    ({"PART_BOOT_MIN": "100000000", "PART_LOAD_MAX": "1000"}, "0", "booted less than 100000000 minutes ago"),
])
def test_ready_starts_nothing_unless_every_limit_is_met(tmp_path, limits, args, expected):
    out = zsh(tmp_path, f"ready {args}; print rc=$?", **limits)
    log = (tmp_path / "t" / "run-log.txt").read_text()
    assert "available GiB:" in out.stdout and "5-minute load:" in out.stdout and "minutes since boot:" in out.stdout
    if expected is None:
        assert "rc=0" in out.stdout and "protocol not started" not in log
    else:
        assert "rc=1" in out.stdout and expected in log and "protocol not started" in log
