# Claude Code conversation records

The project hook in `.claude/settings.json` runs after each response and
when a session ends. It saves one log per message: a prompt typed by the
user plus everything Claude did in response (replies, tool calls and
results). Each message gets its own folder named by the local time the
prompt was sent, the first 8 characters of the session id, and the
message's number in that session, so folders sort chronologically:

```text
docs/ai-usage/
  2026-10-11_2242_c6117488-03/
    transcript.raw.jsonl   # exact records; gitignored, stays on this machine
    transcript.jsonl       # redacted records, for submission
    transcript.md          # readable view of the redacted records
```

A message ends at the last user/assistant record before the next prompt;
records written after it (hook output, context for the next prompt) go to
the next message. So once the next prompt is sent, a message's folder no
longer changes and can be committed. The full session id is at the top of
each `transcript.md` and in every JSONL record. The hook does not commit or
push files.

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

**Memory content, removed by hand (2026-10-27).** Claude Code's memory files are not shared. In
the folders added on 2026-10-27, their content was replaced with `[REDACTED:memory]` before
committing, and each affected `transcript.md` lists `memory ×N` among its redactions. It covered:
- tool calls on memory files (and their results);
- the memory index and memory files that Claude Code embeds in system context, attachments and
  API-request records;
- notes about memory files changing on disk.

The Markdown view was re-rendered from the sanitized JSONL with this hook's `render_markdown`,
so the two formats agree. Paths and file names of memory files are kept.

**Corrections to committed logs (2026-10-28).** A review of all 185 committed folders found
content that the earlier reviews missed. Both formats of 50 folders were sanitized, nothing else:
- Memory content in 47 folders: 46 from batches committed before 2026-10-27, which had not been
  memory-sanitized, and one line left in a folder added on 2026-10-27. 1,335 items were replaced
  with `[REDACTED:memory]` as above, including copies in tool results' record fields
  (`toolUseResult`) and in API-request records. Memory text that the user typed in a prompt is
  kept, as the user's own words.
- Container names of two other Docker Compose projects in 3 folders, one of them added on
  2026-10-27, whose review had found none: 90 were replaced with `[REDACTED:container]`.

Each changed `transcript.md` was re-rendered with `render_markdown`, and its header counts the
new markers. `[REDACTED:private-file]` markers were left as they were. Reviewed and kept, as
they disclose nothing private:
- two reads of `.git/info/exclude`, showing Git's default comments and the name of a private
  planning file that these logs already show;
- app paths: Python's framework bundle, and VS Code, the editor used for this project;
- home-folder paths: this project's helper script, the tests' example `~/proj`, macOS crash
  reports and VS Code's support folder.

The earlier versions remain in Git history. The unsanitized originals are kept locally, out of Git.

**Whitespace, an accepted exception.** Transcripts are verbatim, so lines of tool output can end in
spaces or tabs, and `git diff --check` reports them when a folder is added. They are not removed:
each `transcript.md` must stay identical to the rendering of its `transcript.jsonl`.

This hook and its configuration were drafted with Codex assistance during
project setup.

The first analysis framework (`src/etf_risk/` ingest, validate, model and
spark_pipeline modules, plus `tests/`) was drafted with Claude Code (Opus 5.5)
on 2026-10-11. Each file's docstring states the AI contribution and how it
was verified; the model-breach branch in `model.simulate_path` was written
by the project author.

The transcript hook was inspired by the log_ai.py script in a CS639 project.
