#!/usr/bin/env python3
"""Archive the complete Claude Code transcript after each response or session."""

# AI-assisted setup code. Review the matching session under docs/ai-usage/
# when this script is first used for project development.

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path


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
    destination_dir = project_dir / "docs" / "ai-usage"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"claude-session-{session_id}.jsonl"

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
    temp_name.replace(destination)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Transcript archive failed: {exc}", file=sys.stderr)
        sys.exit(1)
