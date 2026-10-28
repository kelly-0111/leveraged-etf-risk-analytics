"""One AI log per message (.claude/hooks/save_transcript.py).

Uses small fake transcripts shaped like Claude Code JSONL records.
AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from save_transcript import archive, split_messages  # noqa: E402

SESSION = "abcd1234-0000-0000-0000-000000000000"


def prompt(text, ts):
    return {"type": "user", "origin": {"kind": "human"}, "timestamp": ts, "message": {"role": "user", "content": text}}


def reply(text, ts):
    return {"type": "assistant", "timestamp": ts, "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def tool_result(ts):
    return {"type": "user", "timestamp": ts, "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}}


def meta(kind):
    return {"type": kind}


def lines(*records):
    return [json.dumps(r) for r in records]


def test_tool_results_do_not_start_a_new_message():
    msgs = split_messages(lines(
        meta("attachment"),
        prompt("first", "2026-10-11T02:00:00Z"), reply("calling a tool", "2026-10-11T02:00:05Z"),
        tool_result("2026-10-11T02:00:06Z"), reply("done", "2026-10-11T02:00:07Z"),
        meta("system"),                       # e.g. stop-hook record after the reply
        meta("attachment"),                   # context for the next prompt
        prompt("second", "2026-10-11T02:05:00Z"), reply("ok", "2026-10-11T02:05:03Z"),
    ))
    assert [p["message"]["content"] for p, _ in msgs] == ["first", "second"]
    first, second = (len(raw) for _, raw in msgs)
    assert first == 5   # leading attachment + prompt, reply, tool result, reply
    assert second == 4  # trailing metadata of message 1 moves here, + prompt, reply


def test_finished_message_files_do_not_change(tmp_path):
    source = tmp_path / "session.jsonl"
    first_turn = lines(prompt("first", "2026-10-11T02:00:00Z"), reply("one", "2026-10-11T02:00:05Z"))
    source.write_text("\n".join(first_turn + lines(meta("system"))) + "\n")
    [folder1] = archive(source, SESSION, tmp_path)
    before = {p.name: p.read_bytes() for p in folder1.iterdir()}

    with source.open("a") as f:
        f.write("\n".join(lines(meta("attachment"), prompt("second", "2026-10-11T02:09:00Z"),
                                reply("two", "2026-10-11T02:09:04Z"))) + "\n")
    folders = archive(source, SESSION, tmp_path)

    assert [f.name for f in folders] == [folder1.name, folders[1].name]
    assert {p.name: p.read_bytes() for p in folder1.iterdir()} == before
    assert folders[1].name.endswith("_abcd1234-02")
    assert "second" in (folders[1] / "transcript.md").read_text()
    assert "first" not in (folders[1] / "transcript.md").read_text()


def test_folder_has_redacted_and_raw_files(tmp_path):
    source = tmp_path / "session.jsonl"
    source.write_text("\n".join(lines(prompt("mail me at bob@example.org", "2026-10-11T02:00:00Z"),
                                      reply("ok", "2026-10-11T02:00:01Z"))) + "\n")
    [folder] = archive(source, SESSION, tmp_path)
    assert folder.parent == tmp_path / "docs" / "ai-usage"
    assert sorted(p.name for p in folder.iterdir()) == ["transcript.jsonl", "transcript.md", "transcript.raw.jsonl"]
    assert "bob@example.org" in (folder / "transcript.raw.jsonl").read_text()
    for shared in ("transcript.jsonl", "transcript.md"):
        assert "bob@example.org" not in (folder / shared).read_text()
    assert "# Claude Code message 1" in (folder / "transcript.md").read_text()


def test_existing_folder_is_reused_even_if_the_name_would_differ(tmp_path):
    # e.g. the machine's time zone changed between saves
    existing = tmp_path / "docs" / "ai-usage" / "2026-10-10_2100_abcd1234-01"
    existing.mkdir(parents=True)
    source = tmp_path / "session.jsonl"
    source.write_text("\n".join(lines(prompt("first", "2026-10-11T02:00:00Z"), reply("ok", "2026-10-11T02:00:01Z"))) + "\n")
    assert archive(source, SESSION, tmp_path) == [existing]


SEPARATORS = "line separator, paragraph separator"  # valid unescaped inside JSON strings


def test_unicode_line_separators_stay_inside_their_records(tmp_path):
    records = [prompt(f"first {SEPARATORS}", "2026-10-11T02:00:00Z"), reply(f"one {SEPARATORS}", "2026-10-11T02:00:05Z"),
               prompt("second", "2026-10-11T02:09:00Z"), reply("two", "2026-10-11T02:09:04Z")]
    source = tmp_path / "session.jsonl"
    source.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n", encoding="utf-8")
    folders = archive(source, SESSION, tmp_path)
    assert len(folders) == 2
    for folder, expected in zip(folders, (records[:2], records[2:])):
        for name in ("transcript.raw.jsonl", "transcript.jsonl"):
            text = (folder / name).read_text(encoding="utf-8")
            assert [json.loads(line) for line in text.split("\n") if line] == expected  # record count and text
    md = (folders[0] / "transcript.md").read_text(encoding="utf-8")
    assert f"first {SEPARATORS}" in md and f"one {SEPARATORS}" in md


def test_crlf_transcript_archives_like_lf(tmp_path):
    records = [prompt("first", "2026-10-11T02:00:00Z"), reply("one", "2026-10-11T02:00:05Z")]
    for name, end in (("lf", "\n"), ("crlf", "\r\n")):
        (tmp_path / name).mkdir()
        source = tmp_path / name / "session.jsonl"
        source.write_bytes((end.join(json.dumps(r) for r in records) + end).encode())
        archive(source, SESSION, tmp_path / name)
    lf, crlf = (next((tmp_path / name / "docs" / "ai-usage").iterdir()) for name in ("lf", "crlf"))
    for file in ("transcript.raw.jsonl", "transcript.jsonl", "transcript.md"):
        assert (lf / file).read_bytes() == (crlf / file).read_bytes()
    assert [json.loads(line) for line in (crlf / "transcript.raw.jsonl").read_text().split("\n") if line] == records


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), "-c", "user.name=Test", "-c", "user.email=test@example.org",
                           "-c", "commit.gpgsign=false", *args], check=True, capture_output=True, text=True).stdout


def session_in_repo(tmp_path):
    git(tmp_path, "init", "-q")
    source = tmp_path / "session.jsonl"
    source.write_text("\n".join(lines(prompt("first: secret plan", "2026-10-11T02:00:00Z"),
                                      reply("one", "2026-10-11T02:00:05Z"))) + "\n", encoding="utf-8")
    [folder] = archive(source, SESSION, tmp_path)
    return source, folder


def publish(root, folder):
    """Commit a folder's shared files as a log sanitized by hand; the raw file stays untracked."""
    shared = [folder / "transcript.jsonl", folder / "transcript.md"]
    for path in shared:
        path.write_bytes(path.read_bytes().replace(b"secret plan", b"[REDACTED:memory]"))
    git(root, "add", "--", *map(str, shared))
    git(root, "commit", "-q", "-m", "Publish a reviewed log")
    return {p.name: p.read_bytes() for p in shared}


def test_published_logs_stay_byte_identical_and_new_messages_still_save(tmp_path):
    source, folder = session_in_repo(tmp_path)
    published = publish(tmp_path, folder)
    (folder / "transcript.raw.jsonl").unlink()
    with source.open("a", encoding="utf-8") as f:
        f.write("\n".join(json.dumps(r, ensure_ascii=False) for r in (
            prompt(f"second {SEPARATORS}", "2026-10-11T02:09:00Z"), reply("two", "2026-10-11T02:09:04Z"))) + "\n")
    folders = archive(source, SESSION, tmp_path)
    archive(source, SESSION, tmp_path)  # a later run changes nothing either

    assert {name: (folder / name).read_bytes() for name in published} == published
    assert [line for line in git(tmp_path, "status", "--porcelain").splitlines() if not line.startswith("??")] == []
    assert "secret plan" in (folder / "transcript.raw.jsonl").read_text(encoding="utf-8")  # raw archive kept
    new = folders[1]
    assert sorted(p.name for p in new.iterdir()) == ["transcript.jsonl", "transcript.md", "transcript.raw.jsonl"]
    records = [json.loads(line) for line in (new / "transcript.jsonl").read_text(encoding="utf-8").split("\n") if line]
    assert len(records) == 2 and records[0]["message"]["content"] == f"second {SEPARATORS}"
    assert f"second {SEPARATORS}" in (new / "transcript.md").read_text(encoding="utf-8")


def test_local_edits_to_published_logs_are_not_overwritten(tmp_path):
    source, folder = session_in_repo(tmp_path)
    published = publish(tmp_path, folder)
    md = folder / "transcript.md"
    md.write_bytes(md.read_bytes() + b"\nA local note.\n")
    edited = md.read_bytes()
    archive(source, SESSION, tmp_path)
    assert md.read_bytes() == edited
    assert (folder / "transcript.jsonl").read_bytes() == published["transcript.jsonl"]
    assert [line[:2] for line in git(tmp_path, "status", "--porcelain").splitlines() if not line.startswith("??")] == [" M"]
