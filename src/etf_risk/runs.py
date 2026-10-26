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

Which runs may be served (the result cache, spec §11). A run is servable in two cases only;
anything else is refused (Refused), with no fallback to another run:
- a job run: the job table (resolve_job) says the job succeeded, and its accepted attempt
  recorded the digest that the attempt's run folder must have;
- a historical run: the reviewed registry docs/accepted-runs.json lists the folder with its
  digest, the basis for accepting it and the author's approval. `register` checks the basis
  and computes the entry; it never writes into the run folder.
Either way the folder must still have that digest. FolderCheck holds the result of the last
full hash; see it for what its cheaper per-request check detects and what it does not.
Resolving reads the job table and never writes it.

    uv run python -m etf_risk.runs register <run folder> --approved-on YYYY-MM-DD [--write]

AI contribution: written with Claude Code (Opus 5.5). Tested with tests/test_runs.py and
tests/test_runs_resolver.py.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]   # as provenance.REPO_ROOT, without importing pandas
MANIFEST_FORMAT = 1
REGISTRY = REPO_ROOT / "docs" / "accepted-runs.json"
REGISTRY_FORMAT = 1
REGISTRY_ABOUT = ("The historical runs the result cache may serve (spec §11). Each entry was computed and checked by "
                  "python -m etf_risk.runs register, written with Claude Code (Opus 5.5), and approved by the project "
                  "author on the date it gives. The digest is checked again before every use.")
TABLES = ("window_stats", "path_days", "path_summary", "paired")   # as jobs.pipeline.TABLES
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


def _files(folder: Path) -> Iterator[tuple[str, Path]]:
    """Every file below folder with its relative POSIX path; symbolic links are refused."""
    if not folder.is_dir() or folder.is_symlink():
        raise NotADirectoryError(f"{folder}: not a folder")
    for parent, dirs, names in os.walk(folder):
        for name in dirs + names:
            if (Path(parent) / name).is_symlink():
                raise ValueError(f"{Path(parent) / name}: a symbolic link; a run folder holds plain files only")
        for name in names:
            path = Path(parent) / name
            yield path.relative_to(folder).as_posix(), path


def manifest(folder: str | Path) -> dict:
    """Every file below folder, by relative POSIX path, with its size and SHA-256."""
    files = [{"path": rel, "size": path.stat().st_size, "sha256": _sha256(path)} for rel, path in _files(Path(folder))]
    if not files:
        raise ValueError(f"{folder}: no files")
    return {"format": MANIFEST_FORMAT, "files": sorted(files, key=lambda f: f["path"])}


def digest(manifest: dict) -> str:
    """The run digest of a manifest: the SHA-256 of its canonical JSON."""
    return hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def folder_digest(folder: str | Path) -> str:
    return digest(manifest(folder))


class Refused(Exception):
    """The run may not be served: not accepted, not registered, or its files changed."""


Stats = dict[str, tuple[int, int]]          # relative path -> (st_size, st_mtime_ns)


def _stat(path: Path) -> tuple[int, int]:
    st = os.lstat(path)
    return st.st_size, st.st_mtime_ns


def _stats(folder: Path) -> Stats:
    return {rel: _stat(path) for rel, path in _files(folder)}


def _hash_with_stats(folder: Path) -> tuple[str, Stats]:
    """The folder's digest, as folder_digest computes it, and each file's size and
    modification time as they were while it was hashed: stat, hash, stat again, and refuse a
    file whose size or modification time changed in between."""
    files, stats = [], {}
    for rel, path in _files(folder):
        before = _stat(path)
        sha = _sha256(path)
        if _stat(path) != before:
            raise Refused(f"{path}: changed while it was being hashed")
        stats[rel] = before
        files.append({"path": rel, "size": before[0], "sha256": sha})
    if not files:
        raise Refused(f"{folder}: no files")
    return digest({"format": MANIFEST_FORMAT, "files": sorted(files, key=lambda f: f["path"])}), stats


@dataclass
class FolderCheck:
    """A servable run folder as last fully hashed: the digest it must have, and each file's
    size and modification time (st_mtime_ns) from that hash.

    Creating one hashes the folder in full and refuses a digest other than expected.
    check() is the warm process's cheap check before and after each query: it walks the
    folder again (lstat, no reads) and compares the set of relative file paths and each
    file's size and st_mtime_ns with the snapshot. Any difference triggers a full hash; the
    folder is refused unless the digest is unchanged, and then the snapshot is renewed.
    verify_full() hashes in full regardless.

    What check() detects: a file added, removed or renamed; a symbolic link anywhere; a
    change in any file's size; a change in any file's st_mtime_ns.
    What it does not detect: a change of content that leaves every path, size and
    st_mtime_ns equal to the snapshot. Examples: a same-length overwrite whose modification
    time is set back afterwards (touch -r, os.utime, cp -p or rsync -t from a same-length
    file); a same-length overwrite that lands on the same timestamp because the file system
    records time coarsely (APFS keeps nanoseconds; HFS+ one second, FAT two) or because the
    clock was set back. Such a change is found only by a full hash: when the check is
    created (each one-shot request, the start of a warm process), by verify_full(), or once
    any other difference triggers one. ctime and inode numbers are not compared."""
    folder: Path
    expected: str
    stats: Stats = field(default_factory=dict, repr=False)
    full_hashes: int = 0

    def __post_init__(self) -> None:
        self.folder = Path(self.folder)
        self.verify_full()

    def verify_full(self) -> None:
        try:
            found, stats = _hash_with_stats(self.folder)
        except (OSError, ValueError) as error:
            raise Refused(f"{self.folder}: {error}") from None
        self.full_hashes += 1
        if found != self.expected:
            raise Refused(f"{self.folder}: its files have digest {found}, not the accepted {self.expected}")
        self.stats = stats

    def check(self) -> None:
        try:
            unchanged = _stats(self.folder) == self.stats
        except (OSError, ValueError) as error:
            raise Refused(f"{self.folder}: {error}") from None
        if not unchanged:
            self.verify_full()


@dataclass(frozen=True)
class Servable:
    """A run that may be served: its folder, the digest its files must have, and why it may
    be served (provenance, for the request that resolved it: never shared through the cache)."""
    folder: Path
    digest: str
    provenance: dict


def resolve_job(store: Any, job_id: int, *, store_id: str | None = None) -> Servable:
    """A job run: the job succeeded, and its accepted attempt recorded the run digest. Only
    store.store_id(), store.job() and store.attempts() are called, all reads. store_id, when
    given, must be the job table's: job ids start again at 1 in a recreated table."""
    from etf_risk.jobs.params import InvalidParams, JobParams
    from etf_risk.jobs.store import Outcome, Status
    try:
        current = store.store_id()
    except LookupError as error:
        raise Refused(str(error)) from None
    if store_id is not None and store_id != current:
        raise Refused(f"the job table is store {current}, not {store_id}")
    job = store.job(job_id)
    if job is None:
        raise Refused(f"store {current} has no job {job_id}")
    if job["status"] != Status.SUCCEEDED:
        raise Refused(f"job {job_id} is {job['status']}, not succeeded")
    accepted = [a for a in store.attempts(job_id) if a["attempt_number"] == job["accepted_attempt"]]
    if len(accepted) != 1 or accepted[0]["outcome"] != Outcome.ACCEPTED or not is_digest(accepted[0]["result_digest"]):
        raise Refused(f"job {job_id}: its accepted attempt has no recorded digest")
    attempt = accepted[0]
    try:
        params = JobParams.from_dict(job["params"])
    except InvalidParams as error:
        raise Refused(f"job {job_id}: {error}") from None
    # as jobs.pipeline.SubprocessPipeline.run_folder lays it out
    folder = Path(attempt["output_dir"]) / "output" / params.snapshot / params.windows_name / attempt["run_id"]
    return Servable(folder, attempt["result_digest"],
                    {"basis": "job", "store_id": current, "job_id": job_id,
                     "attempt_number": attempt["attempt_number"], "run_id": attempt["run_id"]})


def load_registry(path: str | Path = REGISTRY) -> list[dict]:
    """The registry's entries. A missing registry has none; a malformed one is an error."""
    path = Path(path)
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    if data.get("format") != REGISTRY_FORMAT or not isinstance(data.get("runs"), list):
        raise ValueError(f"{path}: not a registry of format {REGISTRY_FORMAT}")
    for entry in data["runs"]:
        if not isinstance(entry.get("path"), str) or not is_digest(entry.get("digest")) or not entry.get("approved_on"):
            raise ValueError(f"{path}: an entry without path, digest or approval: {entry}")
    return data["runs"]


def registry_root(registry: str | Path) -> Path:
    """The repository a registry belongs to (<repository>/docs/accepted-runs.json): its paths
    are relative to it."""
    return Path(os.path.abspath(registry)).parent.parent


def resolve_registered(folder: str | Path, *, registry: str | Path = REGISTRY) -> Servable:
    """A historical run listed in the registry. Paths are compared after resolving symbolic
    links above the folder, such as a worktree's data link."""
    wanted = Path(folder).resolve()
    for entry in load_registry(registry):
        if (registry_root(registry) / entry["path"]).resolve() == wanted:
            return Servable(Path(folder), entry["digest"],
                            {"basis": "registry", "path": entry["path"], "approved_by": entry["approved_by"],
                             "approved_on": entry["approved_on"]})
    raise Refused(f"{folder}: not in the registry {registry}, and not a job run")


def _json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def acceptance_problems(folder: str | Path) -> list[str]:
    """Why the worker would not accept this run folder (jobs.pipeline.SubprocessPipeline._check_result,
    without importing the worker): run.json ok, every check 0, verify.json clean, every
    table complete. An empty list: none."""
    folder = Path(folder)
    run, checks, verified = _json(folder / "run.json"), _json(folder / "checks.json"), _json(folder / "verify.json")
    problems = []
    if run.get("status") != "ok":
        problems.append(f"run.json status is {run.get('status')!r}, not 'ok'")
    if not checks:
        problems.append("checks.json is missing or empty")
    else:
        violations = sum(v for group in checks.values() for v in group.values())
        if violations:
            problems.append(f"checks.json reports {violations} violations")
    if not verified:
        problems.append("verify.json is missing")
    elif verified.get("mismatch_count") or not verified.get("breached_windows", {}).get("same"):
        problems.append(f"verify.json is not clean: {verified.get('mismatch_count')} mismatches, "
                        f"breached windows same: {verified.get('breached_windows', {}).get('same')}")
    problems += [f"{table}/ has no _SUCCESS" for table in TABLES if not (folder / table / "_SUCCESS").is_file()]
    return problems


def registry_entry(folder: str | Path, *, approved_on: str, registry: str | Path = REGISTRY) -> dict:
    """The registry entry for a historical run, after checking the basis for accepting it:
    the worker's acceptance rule, and a verify.json written for this run folder. Reads only."""
    folder = Path(folder)
    problems = acceptance_problems(folder)
    verified_run = _json(folder / "verify.json").get("run")
    if verified_run is not None and Path(verified_run).name != folder.name:
        problems.append(f"verify.json was written for {verified_run}, not this folder")
    if problems:
        raise Refused(f"{folder}: " + "; ".join(problems))
    date.fromisoformat(approved_on)
    rel = os.path.relpath(os.path.abspath(folder), registry_root(registry))
    if rel.startswith(".."):
        raise Refused(f"{folder}: outside the repository")
    run = _json(folder / "run.json")
    return {"path": Path(rel).as_posix(), "digest": folder_digest(folder), "manifest_format": MANIFEST_FORMAT,
            "run_id": run.get("run_id"),
            "basis": {"run_json_status": "ok", "check_violations": 0, "verify_mismatch_count": 0,
                      "verify_breached_windows_same": True, "tables_complete": list(TABLES),
                      "verify_run_name": Path(verified_run).name},      # the name only: never a local path
            "approved_by": "the project author", "approved_on": approved_on}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m etf_risk.runs", description="Register a historical run.")
    commands = parser.add_subparsers(dest="command", required=True)
    register = commands.add_parser("register", help="check a run folder and print its registry entry")
    register.add_argument("folder", type=Path)
    register.add_argument("--approved-on", required=True, help="the author's approval date, YYYY-MM-DD")
    register.add_argument("--note", help="a note kept with the entry")
    register.add_argument("--registry", type=Path, default=REGISTRY)
    register.add_argument("--write", action="store_true", help="add the entry to the registry")
    args = parser.parse_args(argv)
    try:
        entry = registry_entry(args.folder, approved_on=args.approved_on, registry=args.registry)
    except Refused as error:
        print(f"refused: {error}", file=sys.stderr)
        return 1
    if args.note:
        entry["note"] = args.note
    print(json.dumps(entry, indent=2))
    if not args.write:
        return 0
    entries = load_registry(args.registry)
    same = [e for e in entries if e["path"] == entry["path"]]
    if same and same[0]["digest"] != entry["digest"]:
        print(f"refused: {entry['path']} is registered with digest {same[0]['digest']}", file=sys.stderr)
        return 1
    if not same:
        about = json.loads(args.registry.read_text()).get("about", REGISTRY_ABOUT) if entries else REGISTRY_ABOUT
        args.registry.write_text(json.dumps({"format": REGISTRY_FORMAT, "about": about, "runs": entries + [entry]},
                                            indent=2) + "\n")
        print(f"added to {args.registry}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
