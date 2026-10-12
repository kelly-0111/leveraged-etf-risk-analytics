#!/usr/bin/env python3
"""Archive Claude Code transcripts: a local original plus redacted JSONL and Markdown.

Per session folder (docs/ai-usage/<start time>_<id prefix>/):
  transcript.raw.jsonl  exact copy, gitignored, never shared
  transcript.jsonl      redacted by transcript_privacy.py, for submission
  transcript.md         readable view rendered from the redacted JSONL
"""

# AI-assisted setup code. The hook idea was inspired by a CS 639 project's
# log_ai.py; this implementation was newly written for full-transcript
# archiving. See docs/ai-usage/README.md for provenance. Per-session folders
# named by start time and the redacted copies were added with Claude Code
# (Opus 5.5) and checked by running the hook on a real transcript in a
# scratch project directory and re-scanning the output for personal data.

import json
import os
import re
import shutil
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from transcript_privacy import Redactor


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


def write_markdown(source: Path, destination: Path, session_id: str, redactions: Counter) -> int:
    """Render conversation and tool messages from the redacted JSONL."""
    summary = ", ".join(f"{k} ×{v}" for k, v in sorted(redactions.items())) or "none"
    parts = [
        "# Claude Code conversation transcript",
        f"Session: `{session_id}`",
        f"Redacted record: [{source.name}]({source.name})",
        "This readable view includes user/assistant messages and tool calls/results. "
        "Internal reasoning and session metadata are omitted.",
        f"Redactions (markers like `[REDACTED:email]`; home directory shown as `~`): {summary}. "
        "Rules: `.claude/hooks/transcript_privacy.py`. The unredacted original stays local only.",
    ]
    messages = 0
    with source.open(encoding="utf-8") as transcript:
        for line in transcript:
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("type") not in {"user", "assistant"}:
                continue
            message = record.get("message", {})
            content = message.get("content", "")
            blocks = content if isinstance(content, list) else [content]
            body = "\n\n".join(filter(None, (render_block(block) for block in blocks)))
            if not body:
                continue
            role = message.get("role", record["type"]).capitalize()
            timestamp = record.get("timestamp", "")
            messages += 1
            parts.extend([f"## {messages}. {role} — {timestamp}", body])
    atomic_write_text(destination, "\n\n".join(parts) + "\n")
    return messages


def session_started_at(source: Path) -> datetime:
    """Earliest record timestamp; records are not always in time order."""
    earliest = None
    with source.open(encoding="utf-8") as transcript:
        for line in transcript:
            try:
                stamp = json.loads(line).get("timestamp")
                parsed = datetime.fromisoformat(stamp) if isinstance(stamp, str) else None
            except ValueError:
                continue
            if parsed and (earliest is None or parsed < earliest):
                earliest = parsed
    return earliest or datetime.now(timezone.utc)


def session_folder(root: Path, session_id: str, source: Path) -> Path:
    """One folder per session, e.g. 2026-10-11_2139_c6117488 (local start time).

    The hook runs after every response, so the name must not change within a
    session: it uses the session start, and an existing folder is reused.
    """
    short_id = session_id[:8]
    existing = sorted(p for p in root.glob(f"*_{short_id}") if p.is_dir())
    if existing:
        return existing[0]
    started = session_started_at(source).astimezone()
    return root / f"{started:%Y-%m-%d_%H%M}_{short_id}"


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
    destination_dir = session_folder(project_dir / "docs" / "ai-usage", session_id, source)
    destination_dir.mkdir(parents=True, exist_ok=True)
    raw = destination_dir / "transcript.raw.jsonl"  # gitignored
    shared = destination_dir / "transcript.jsonl"

    # A temporary file and atomic rename avoid leaving a partial archive.
    with tempfile.NamedTemporaryFile(dir=destination_dir, prefix=".transcript-", delete=False) as temp:
        temp_name = Path(temp.name)
        try:
            with source.open("rb") as transcript:
                shutil.copyfileobj(transcript, temp)
            temp.flush()
            os.fsync(temp.fileno())
        except BaseException:
            temp_name.unlink(missing_ok=True)
            raise
    temp_name.replace(raw)

    redactor = Redactor.for_project(project_dir)
    atomic_write_text(shared, redactor.jsonl(raw.read_text(encoding="utf-8")))
    write_markdown(shared, shared.with_suffix(".md"), session_id, redactor.counts)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Transcript archive failed: {exc}", file=sys.stderr)
        sys.exit(1)
