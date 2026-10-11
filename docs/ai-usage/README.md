# Claude Code conversation records

The project hook in `.claude/settings.json` saves the complete Claude Code
JSONL transcript after each response and when a session ends. Each session
has one file named `claude-session-<session-id>.jsonl`; later saves replace
that session's earlier snapshot. The hook does not commit or push files.

Before committing a transcript, review it for credentials and private data.
Commit the reviewed transcript alongside the related code. If AI generates
code, add a nearby comment describing its contribution and how you verified
the result. The hook records only Claude Code conversations in this project.

This hook and its configuration were drafted with Codex assistance during
project setup. No project analysis code has been generated yet.

The transcript hook was inspired by the log_ai.py script in a CS639 project.
