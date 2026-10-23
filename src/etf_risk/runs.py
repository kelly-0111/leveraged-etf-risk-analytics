"""The identity of a run's results: a canonical manifest of the files in a run folder, and
its SHA-256, the run digest (spec §11).

manifest() lists every file below the folder, sorted by its POSIX path relative to the
folder, with its size and SHA-256. digest() is the SHA-256 of that manifest written as
canonical JSON (sorted keys, no spaces). The digest therefore changes when a file is added,
removed, renamed or changed. It does not depend on modification times or on where the
folder lives. It identifies one run's files, not a result: Parquet files differ in bytes
between runs that are equal by content, and two such runs have different digests
(compare_tables in analysis/collect_partition_measurements.py compares content).

The job store records the digest when it accepts an attempt (job_attempts.result_digest), so
the accepted decision and the accepted files are bound together. A symbolic link anywhere in
the folder is refused, since the manifest would otherwise depend on where the link points.
Files are hashed in chunks, so a large Parquet part never has to fit in memory.

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_runs.py.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

MANIFEST_FORMAT = 1
_DIGEST = re.compile(r"[0-9a-f]{64}")
_CHUNK = 1 << 20


def is_digest(value: object) -> bool:
    """A run digest as the store records it: 64 lowercase hexadecimal digits."""
    return isinstance(value, str) and _DIGEST.fullmatch(value) is not None


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def manifest(folder: str | Path) -> dict:
    """Every file below folder, by relative POSIX path, with its size and SHA-256."""
    folder = Path(folder)
    if not folder.is_dir() or folder.is_symlink():
        raise NotADirectoryError(f"{folder}: not a folder")
    files = []
    for parent, dirs, names in os.walk(folder):
        for name in dirs + names:
            if (Path(parent) / name).is_symlink():
                raise ValueError(f"{Path(parent) / name}: a symbolic link; a run folder holds plain files only")
        for name in names:
            path = Path(parent) / name
            files.append({"path": path.relative_to(folder).as_posix(), "size": path.stat().st_size,
                          "sha256": _sha256(path)})
    if not files:
        raise ValueError(f"{folder}: no files")
    return {"format": MANIFEST_FORMAT, "files": sorted(files, key=lambda f: f["path"])}


def digest(manifest: dict) -> str:
    """The run digest of a manifest: the SHA-256 of its canonical JSON."""
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def folder_digest(folder: str | Path) -> str:
    return digest(manifest(folder))
