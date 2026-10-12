# Claude Code conversation records

The project hook in `.claude/settings.json` saves the complete Claude Code
JSONL transcript after each response and when a session ends, together with
a readable Markdown version. Each session gets its own folder named by its
local start time and the first 8 characters of the session id, so folders
sort chronologically:

```text
docs/ai-usage/
  2026-10-11_2139_c6117488/
    transcript.raw.jsonl   # exact original; gitignored, stays on this machine
    transcript.jsonl       # redacted record, for submission
    transcript.md          # readable view of the redacted record
```

The full session id is at the top of `transcript.md` and in every JSONL
record. Later saves in the same session replace that folder's files. The
hook does not commit or push files.

## Redaction

The shared files are produced by `.claude/hooks/transcript_privacy.py`.
Every redaction leaves a marker such as `[REDACTED:email]` (the home
directory is shown as `~`), and the top of `transcript.md` lists how many
of each kind were made. Redacted automatically:

- this machine's identity: home directory, username, hostname and computer
  name (including the owner name macOS puts in it), git `user.name` and
  `user.email`
- any e-mail address except `noreply@anthropic.com` and `git@github.com`
- private-network IPv4 addresses and common API-key / token formats
- model reasoning (thinking blocks); the Markdown view never included it

Project-specific additions go in `.claude/transcript-privacy.local.json`,
which is gitignored because it can itself contain names:

```json
{
  "private_terms": ["a name or other word to hide, matched case-insensitively"],
  "private_files": ["docs/a-file-not-in-git.md"]
}
```

Text that reproduces three or more lines of a private file is replaced as a
whole with `[REDACTED:private-file <path>]`. The rules are pattern-based and
cannot recognise every kind of personal data (for example, details typed
into a prompt), so still read `transcript.md` before committing a session
folder, and commit it alongside the related code. If AI generates
code, add a nearby comment describing its contribution and how you verified
the result. The hook records only Claude Code conversations in this project.

This hook and its configuration were drafted with Codex assistance during
project setup.

The first analysis framework (`src/etf_risk/` ingest, validate, model and
spark_pipeline modules, plus `tests/`) was drafted with Claude Code (Opus 5.5)
on 2026-10-11. Each file's docstring states the AI contribution and how it
was verified; the model-breach branch in `model.simulate_path` was written
by the project author.

The transcript hook was inspired by the log_ai.py script in a CS639 project.
