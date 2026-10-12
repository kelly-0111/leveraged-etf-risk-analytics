"""One AI log per message (.claude/hooks/save_transcript.py).

Uses small fake transcripts shaped like Claude Code JSONL records.
AI contribution: written with Claude Code (Opus 5.5).
"""
import json
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
