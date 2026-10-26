"""etf_risk.runs: which runs may be served (spec §11), the warm folder check, and the registry
of historical runs. Job runs come from a real job table on SQLite; run folders are small
fakes with the files the worker's acceptance rule reads.

AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import os
import shutil

import pytest

from etf_risk import runs
from etf_risk.jobs.pipeline import SubprocessPipeline
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite
from etf_risk.jobs.worker import PipelineError
from run_fakes import PARAMS, accepted_job, job_table, write_run


@pytest.fixture
def store(tmp_path):
    return job_table(tmp_path / "jobs.sqlite")


# Job runs

def test_an_accepted_job_run_resolves_to_its_folder_digest_and_provenance(store, tmp_path):
    job_id, folder = accepted_job(store, tmp_path / "out")
    store.statements.clear()
    run = runs.resolve_job(store, job_id)
    assert run.folder == folder and run.digest == runs.folder_digest(folder)
    assert run.provenance == {"basis": "job", "store_id": store.store_id(), "job_id": job_id,
                              "attempt_number": 1, "run_id": folder.name}
    runs.FolderCheck(run.folder, run.digest)                     # the files still have that digest


def test_resolving_only_reads_the_job_table(store, tmp_path):
    job_id, _ = accepted_job(store, tmp_path / "out")
    fresh = JobStore(open_sqlite(tmp_path / "jobs.sqlite"), SQLITE)
    statements = []
    fresh.connection.set_trace_callback(statements.append)
    runs.resolve_job(fresh, job_id, store_id=store.store_id())
    assert statements and all(s.lstrip().upper().startswith("SELECT") for s in statements)


def test_a_job_that_has_not_succeeded_is_refused(store, tmp_path):
    queued = store.submit(PARAMS, {})
    running = store.submit(PARAMS, {})
    store.claim(running, "worker-a", tmp_path / "out")
    for job_id in (queued, running):
        with pytest.raises(runs.Refused, match="not succeeded"):
            runs.resolve_job(store, job_id)


def test_an_unknown_job_another_store_and_a_table_without_identity_are_refused(store, tmp_path):
    job_id, _ = accepted_job(store, tmp_path / "out")
    with pytest.raises(runs.Refused, match="no job"):
        runs.resolve_job(store, job_id + 1)
    with pytest.raises(runs.Refused, match="not " + "f" * 32):
        runs.resolve_job(store, job_id, store_id="f" * 32)
    bare = JobStore(open_sqlite(tmp_path / "bare.sqlite", create=True), SQLITE)
    with pytest.raises(runs.Refused, match="no store id"):
        runs.resolve_job(bare, 1)


def test_an_accepted_folder_whose_files_changed_is_refused(store, tmp_path):
    job_id, folder = accepted_job(store, tmp_path / "out")
    (folder / "paired" / "part-00000.parquet").write_bytes(b"other content")
    run = runs.resolve_job(store, job_id)
    with pytest.raises(runs.Refused, match="not the accepted"):
        runs.FolderCheck(run.folder, run.digest)


# The folder check

@pytest.fixture
def checked(tmp_path):
    folder = write_run(tmp_path / "run-1")
    return runs.FolderCheck(folder, runs.folder_digest(folder))


def test_the_full_hash_gives_folder_digest(checked):
    assert runs._hash_with_stats(checked.folder)[0] == runs.folder_digest(checked.folder)


def test_an_unchanged_folder_passes_without_hashing_again(checked):
    checked.check()
    checked.check()
    assert checked.full_hashes == 1


def test_a_touched_file_is_hashed_again_and_passes_with_a_new_snapshot(checked):
    part = checked.folder / "paired" / "part-00000.parquet"
    os.utime(part, ns=(0, part.stat().st_mtime_ns + 10**9))
    checked.check()
    checked.check()
    assert checked.full_hashes == 2


@pytest.mark.parametrize("change", ["size", "added", "removed", "renamed", "symlink"])
def test_detected_changes_are_refused(checked, change):
    folder, part = checked.folder, checked.folder / "paired" / "part-00000.parquet"
    if change == "size":
        part.write_bytes(part.read_bytes() + b"x")
    elif change == "added":
        (folder / "extra.json").write_text("{}")
    elif change == "removed":
        part.unlink()
    elif change == "renamed":
        part.rename(folder / "paired" / "part-00001.parquet")
    else:
        (folder / "link").symlink_to(part)
    with pytest.raises(runs.Refused):
        checked.check()


def test_a_same_length_overwrite_with_its_mtime_set_back_is_not_detected_by_the_check(checked):
    """The documented limitation: only a full hash finds this change."""
    part = checked.folder / "paired" / "part-00000.parquet"
    before = part.stat()
    part.write_bytes(b"Z" * before.st_size)
    os.utime(part, ns=(before.st_atime_ns, before.st_mtime_ns))
    checked.check()                                             # passes: path, size and mtime are as before
    assert checked.full_hashes == 1
    with pytest.raises(runs.Refused, match="not the accepted"):
        checked.verify_full()


def test_a_file_that_changes_while_it_is_hashed_is_refused(tmp_path, monkeypatch):
    folder = write_run(tmp_path / "run-1")
    expected = runs.folder_digest(folder)
    original = runs._sha256

    def hash_then_append(path):
        sha = original(path)
        if path.name == "run.json":
            with path.open("ab") as f:
                f.write(b" ")
        return sha
    monkeypatch.setattr(runs, "_sha256", hash_then_append)
    with pytest.raises(runs.Refused, match="changed while it was being hashed"):
        runs.FolderCheck(folder, expected)


# The registry

@pytest.fixture
def registered(tmp_path):
    repo = tmp_path / "repo"
    folder = write_run(repo / "data" / "outputs" / "run-4")
    registry = repo / "docs" / "accepted-runs.json"
    entry = runs.registry_entry(folder, approved_on="2026-10-25", registry=registry)
    registry.parent.mkdir(parents=True)
    registry.write_text(json.dumps({"format": runs.REGISTRY_FORMAT, "runs": [entry]}))
    return repo, folder, registry


def test_a_registered_run_resolves_with_its_approval(registered):
    repo, folder, registry = registered
    run = runs.resolve_registered(folder, registry=registry)
    assert run.digest == runs.folder_digest(folder)
    assert run.provenance == {"basis": "registry", "path": "data/outputs/run-4",
                              "approved_by": "the project author", "approved_on": "2026-10-25"}


def test_a_registered_run_is_found_through_a_linked_data_folder(registered, tmp_path):
    repo, folder, registry = registered
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / "data").symlink_to(repo / "data")
    run = runs.resolve_registered(worktree / "data" / "outputs" / "run-4", registry=registry)
    runs.FolderCheck(run.folder, run.digest)


def test_an_unregistered_run_is_refused(registered):
    repo, folder, registry = registered
    other = write_run(folder.parent / "run-5")
    with pytest.raises(runs.Refused, match="not in the registry"):
        runs.resolve_registered(other, registry=registry)


def test_a_registered_run_whose_files_changed_is_refused(registered):
    repo, folder, registry = registered
    (folder / "run.json").write_text('{"status": "ok", "run_id": "edited"}')
    run = runs.resolve_registered(folder, registry=registry)
    with pytest.raises(runs.Refused, match="not the accepted"):
        runs.FolderCheck(run.folder, run.digest)


def test_a_malformed_registry_is_an_error_not_an_empty_list(tmp_path):
    bad = tmp_path / "accepted-runs.json"
    bad.write_text(json.dumps({"format": 1, "runs": [{"path": "x", "digest": "not a digest", "approved_on": "2026-10-25"}]}))
    with pytest.raises(ValueError):
        runs.load_registry(bad)
    assert runs.load_registry(tmp_path / "missing.json") == []


@pytest.mark.parametrize("change, problem", [
    (dict(status="checks_failed"), "status"),
    (dict(violations=2), "2 violations"),
    (dict(mismatches=1), "not clean"),
    (dict(same=False), "not clean"),
    (dict(with_verify_json=False), "verify.json is missing"),
    (dict(success=runs.TABLES[:-1]), "paired/ has no _SUCCESS"),
])
def test_registration_refuses_what_the_worker_would_not_accept(tmp_path, change, problem):
    folder = write_run(tmp_path / "run-4", **change)
    with pytest.raises(runs.Refused, match=problem):
        runs.registry_entry(folder, approved_on="2026-10-25", registry=tmp_path / "docs" / "accepted-runs.json")


@pytest.mark.parametrize("change", [{}, dict(status="checks_failed"), dict(violations=1), dict(mismatches=3),
                                    dict(same=False), dict(with_verify_json=False), dict(success=runs.TABLES[1:])])
def test_the_acceptance_rule_is_the_workers(tmp_path, change):
    folder = write_run(tmp_path / "run", **change)
    try:
        object.__new__(SubprocessPipeline)._check_result(folder)
        worker_accepts = True
    except PipelineError:
        worker_accepts = False
    assert (runs.acceptance_problems(folder) == []) == worker_accepts


def test_registration_refuses_a_verify_json_written_for_another_run(tmp_path):
    folder = write_run(tmp_path / "run-4", verify_run=tmp_path / "run-2")
    with pytest.raises(runs.Refused, match="written for"):
        runs.registry_entry(folder, approved_on="2026-10-25", registry=tmp_path / "docs" / "accepted-runs.json")


def test_registering_never_writes_into_the_run_folder(registered, tmp_path):
    repo, folder, registry = registered
    before = runs._stats(folder), runs.folder_digest(folder)
    assert runs.main(["register", str(folder), "--approved-on", "2026-10-25", "--registry", str(registry),
                      "--write"]) == 0
    assert (runs._stats(folder), runs.folder_digest(folder)) == before
    assert len(runs.load_registry(registry)) == 1                # already there with the same digest


def test_register_write_adds_once_and_refuses_a_different_digest(registered, capsys):
    repo, folder, registry = registered
    copy = folder.parent / "run-7"
    shutil.copytree(folder, copy)
    (copy / "verify.json").write_text(json.dumps({"run": str(copy), "mismatch_count": 0,
                                                  "breached_windows": {"same": True}}))
    args = ["register", str(copy), "--approved-on", "2026-10-25", "--registry", str(registry), "--write"]
    assert runs.main(args) == 0
    assert [e["path"] for e in runs.load_registry(registry)] == ["data/outputs/run-4", "data/outputs/run-7"]
    (copy / "run.json").write_text('{"status": "ok", "run_id": "run-7b"}')
    assert runs.main(args) == 1
    assert "registered with digest" in capsys.readouterr().err


def test_the_repo_root_is_provenances():
    from etf_risk.provenance import REPO_ROOT
    assert runs.REPO_ROOT == REPO_ROOT
