#!/usr/bin/env python3
"""Archive Claude Code transcripts as one log per message (prompt + response).

Per message folder (docs/ai-usage/<prompt time>_<session id prefix>-<NN>/):
  transcript.raw.jsonl  exact records of this message, gitignored, never shared
  transcript.jsonl      redacted by transcript_privacy.py, for submission
  transcript.md         readable view rendered from the redacted JSONL

A message starts at a prompt the user typed and ends at the last user /
assistant record before the next prompt. Metadata written after that (hook
records, context for the next prompt) belongs to the next message, so a
finished message's files do not change once the next one starts.
"""

# AI-assisted setup code. The hook idea was inspired by a CS 639 project's
# log_ai.py; this implementation was newly written for full-transcript
# archiving. See docs/ai-usage/README.md for provenance. Per-message folders
# and the redacted copies were added with Claude Code (Opus 5.5) and checked
# with tests/test_save_transcript.py, by running the hook on a real session
# transcript, and by re-scanning the output for personal data.

import json
import os
import re
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from transcript_privacy import Redactor, jsonl_records


def fenced(value: object) -> str:
    """Keep tool content literal even when it contains Markdown fences."""
    body = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2)
    fence = "`" * max(3, max((len(x) for x in re.findall(r"`+", body)), default=0) + 1)
    return f"{fence}\n{body}\n{fence}"


def render_block(block: object) -> str:
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return fenced(block)
    kind = block.get("type")
    if kind in {"thinking", "redacted_thinking"}:
        return ""
    if kind == "text":
        return block.get("text", "")
    if kind == "tool_use":
        return f"### Tool call: {block.get('name', 'unknown')}\n\n{fenced(block.get('input', {}))}"
    if kind == "tool_result":
        content = block.get("content", "")
        if isinstance(content, list):
            content = "\n\n".join(filter(None, (render_block(item) for item in content)))
        label = "Tool result (error)" if block.get("is_error") else "Tool result"
        return f"### {label}\n\n{fenced(content)}"
    # Preserve unfamiliar visible blocks and attachment references for review.
    return fenced(block)


def atomic_write_text(destination: Path, text: str) -> None:
    """A temporary file and atomic rename avoid leaving a partial archive."""
    with tempfile.NamedTemporaryFile(
        dir=destination.parent, prefix=".transcript-", mode="w", encoding="utf-8", delete=False
    ) as temp:
        temp_name = Path(temp.name)
        try:
            temp.write(text)
            temp.flush()
            os.fsync(temp.fileno())
        except BaseException:
            temp_name.unlink(missing_ok=True)
            raise
    temp_name.replace(destination)


def write_if_changed(destination: Path, text: str) -> None:
    """Leave finished messages untouched so their mtimes stay meaningful."""
    if destination.is_file() and destination.read_text(encoding="utf-8") == text:
        return
    atomic_write_text(destination, text)


def render_markdown(redacted_jsonl: str, session_id: str, number: int, sent: datetime, redactions: Counter) -> str:
    """Readable view of one message, from its redacted JSONL."""
    summary = ", ".join(f"{k} ×{v}" for k, v in sorted(redactions.items())) or "none"
    parts = [
        f"# Claude Code message {number}",
        f"Session: `{session_id}` · prompt sent {sent:%Y-%m-%d %H:%M} (local time)",
        "Redacted record: [transcript.jsonl](transcript.jsonl)",
        "This readable view includes user/assistant messages and tool calls/results. "
        "Internal reasoning and session metadata are omitted.",
        f"Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): {summary}. "
        "Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.",
    ]
    entries = 0
    for line in jsonl_records(redacted_jsonl):
        record = json.loads(line)
        if not is_message(record):
            continue
        message = record.get("message", {})
        content = message.get("content", "")
        blocks = content if isinstance(content, list) else [content]
        body = "\n\n".join(filter(None, (render_block(block) for block in blocks)))
        if not body:
            continue
        role = message.get("role", record["type"]).capitalize()
        entries += 1
        parts.extend([f"## {entries}. {role} — {record.get('timestamp', '')}", body])
    return "\n\n".join(parts) + "\n"


def is_message(record: dict) -> bool:
    return record.get("type") in {"user", "assistant"}


def is_prompt(record: dict) -> bool:
    """A prompt the user typed (not a tool result or injected meta message)."""
    if record.get("type") != "user" or record.get("isMeta"):
        return False
    origin = record.get("origin")
    if isinstance(origin, dict) and "kind" in origin:
        return origin["kind"] == "human"
    # Older transcripts without "origin": any user record that is not a tool result.
    content = record.get("message", {}).get("content")
    blocks = content if isinstance(content, list) else [content]
    return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in blocks)


def split_messages(lines: list[str]) -> list[tuple[dict, list[str]]]:
    """(prompt record, raw lines) for each message, in file order."""
    records = [json.loads(line) for line in lines]
    prompts = [i for i, r in enumerate(records) if is_prompt(r)]
    messages = []
    start = 0
    for k, p in enumerate(prompts):
        stop = prompts[k + 1] if k + 1 < len(prompts) else len(records)
        last = max(i for i in range(p, stop) if is_message(records[i]))
        messages.append((records[p], lines[start:last + 1]))
        start = last + 1
    return messages


def message_folder(root: Path, session_id: str, number: int, sent: datetime) -> Path:
    """e.g. 2026-10-11_2244_c6117488-03; an existing folder for the message is reused."""
    suffix = f"_{session_id[:8]}-{number:02d}"
    existing = sorted(p for p in root.glob(f"*{suffix}") if p.is_dir())
    return existing[0] if existing else root / f"{sent:%Y-%m-%d_%H%M}{suffix}"


def prompt_time(prompt: dict) -> datetime:
    try:
        return datetime.fromisoformat(prompt["timestamp"]).astimezone()
    except (KeyError, TypeError, ValueError):
        return datetime.now(timezone.utc).astimezone()


def archive(source: Path, session_id: str, project_dir: Path) -> list[Path]:
    root = project_dir / "docs" / "ai-usage"
    # Bytes, not read_text(): its newline translation would also turn a lone CR into a line break.
    lines = jsonl_records(source.read_bytes().decode("utf-8"))
    redactor = Redactor.for_project(project_dir)
    folders = []
    for number, (prompt, raw_lines) in enumerate(split_messages(lines), start=1):
        sent = prompt_time(prompt)
        folder = message_folder(root, session_id, number, sent)
        folder.mkdir(parents=True, exist_ok=True)
        raw = "\n".join(raw_lines) + "\n"
        redactor.counts = Counter()  # per-message redaction summary
        shared = redactor.jsonl(raw)
        write_if_changed(folder / "transcript.raw.jsonl", raw)  # gitignored
        write_if_changed(folder / "transcript.jsonl", shared)
        write_if_changed(folder / "transcript.md", render_markdown(shared, session_id, number, sent, redactor.counts))
        folders.append(folder)
    return folders


def main() -> None:
    event = json.load(sys.stdin)
    session_id = event.get("session_id")
    source_name = event.get("transcript_path")
    if not isinstance(session_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
        raise ValueError("Missing or invalid session_id")
    if not isinstance(source_name, str) or not source_name:
        raise ValueError("Missing transcript_path")

    source = Path(source_name)
    if not source.is_file():
        raise FileNotFoundError(source)

    project_dir = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
    archive(source, session_id, project_dir)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Transcript archive failed: {exc}", file=sys.stderr)
        sys.exit(1)
