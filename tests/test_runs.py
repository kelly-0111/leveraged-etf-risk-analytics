"""etf_risk.runs: the manifest of a run folder and its digest.

AI contribution: written with Claude Code (Opus 5.5).
"""
import hashlib
import os

import pytest

from etf_risk import runs


@pytest.fixture
def folder(tmp_path):
    run = tmp_path / "run"
    (run / "paired").mkdir(parents=True)
    (run / "paired" / "part-0.parquet").write_bytes(b"\x00" * 3000)
    (run / "paired" / "._SUCCESS.crc").write_bytes(b"crc")
    (run / "run.json").write_text('{"status": "ok"}\n')
    return run


def test_the_manifest_lists_every_file_sorted_with_size_and_sha256(folder):
    m = runs.manifest(folder)
    assert m["format"] == 1
    assert [f["path"] for f in m["files"]] == ["paired/._SUCCESS.crc", "paired/part-0.parquet", "run.json"]
    part = m["files"][1]
    assert (part["size"], part["sha256"]) == (3000, hashlib.sha256(b"\x00" * 3000).hexdigest())


def test_the_digest_ignores_times_and_location_but_not_content_or_names(folder, tmp_path):
    before = runs.folder_digest(folder)
    assert runs.is_digest(before)
    os.utime(folder / "run.json", (0, 0))
    moved = tmp_path / "elsewhere"
    folder.rename(moved)
    assert runs.folder_digest(moved) == before
    (moved / "run.json").write_text('{"status": "failed"}\n')
    assert runs.folder_digest(moved) != before
    (moved / "run.json").write_text('{"status": "ok"}\n')
    assert runs.folder_digest(moved) == before
    (moved / "run.json").rename(moved / "run2.json")
    assert runs.folder_digest(moved) != before


def test_a_link_or_an_empty_folder_has_no_digest(folder, tmp_path):
    (folder / "link").symlink_to(folder / "run.json")
    with pytest.raises(ValueError, match="symbolic link"):
        runs.manifest(folder)
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="no files"):
        runs.manifest(tmp_path / "empty")


@pytest.mark.parametrize("value, ok", [("a" * 64, True), ("A" * 64, False), ("a" * 63, False), (None, False)])
def test_a_digest_is_64_lowercase_hex_digits(value, ok):
    assert runs.is_digest(value) is ok
