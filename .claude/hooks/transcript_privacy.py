"""Redact personal data from Claude Code transcripts before they are shared.

save_transcript.py applies this to every string and dict key of every JSONL
record. Each redaction leaves a visible marker such as [REDACTED:email]; the
home directory is shown as ~. What is redacted:

  - this machine's identity: home directory, username, hostname / computer
    name (and the owner name macOS puts in it), git user.name and user.email
  - any e-mail address (except EMAIL_ALLOWLIST), private-network IPv4
    addresses, common API-key / token formats, and NAME_KEY=value secrets
  - model reasoning (thinking blocks), which the Markdown view also omits
  - optional, from .claude/transcript-privacy.local.json (gitignored):
        {"private_terms": ["a name"], "private_files": ["docs/private.md"]}
    terms are replaced case-insensitively; any text that reproduces
    MIN_FILE_LINE_MATCHES or more distinct lines of a private file is replaced
    whole. Lines shorter than MIN_FILE_LINE_CHARS, or without a letter or digit
    (Markdown table rules, separators), are too generic to count.

Rules are pattern-based, so a reviewed transcript is still required before
committing (see docs/ai-usage/README.md).

AI contribution: written with Claude Code (Opus 5.5). Verified with
tests/test_transcript_privacy.py and by re-scanning a real redacted session
transcript for the identity values, e-mails, IPs and private-file lines.
"""
from __future__ import annotations

import getpass
import json
import re
import socket
import subprocess
from collections import Counter
from pathlib import Path

CONFIG_PATH = Path(".claude") / "transcript-privacy.local.json"
EMAIL_ALLOWLIST = {"noreply@anthropic.com", "git@github.com"}
MIN_LITERAL_CHARS = 3            # never redact a value so short it matches everywhere
MIN_FILE_LINE_CHARS = 12         # ignore short, generic lines of private files
MIN_FILE_LINE_MATCHES = 3        # distinct lines; a line repeated in a text counts once
HAS_LETTER_OR_DIGIT = re.compile(r"[^\W_]")   # lines without one, e.g. |---|---|, are generic

# "\\?" also catches regex-escaped addresses such as name@mail\.com in commands.
EMAIL = re.compile(r"[\w.%+-]+@[A-Za-z0-9-]+(?:\\*\.[A-Za-z0-9-]+)*\\*\.[A-Za-z]{2,}")
# macOS default device names embed the owner's name: "Name's MacBook Air",
# "Name的MacBook Air", hostname "Names-MacBook-Air".
MAC_MODEL_SUFFIX = re.compile(r"[-\s]*(?:MacBook|iMac|Mac[-\s]?mini|Mac[-\s]?Pro|Mac[-\s]?Studio)\b.*$", re.IGNORECASE)
OWNER_SUFFIX = re.compile(r"(?:'s|’s|的)$")
PRIVATE_IPV4 = re.compile(
    r"\b(?:10(?:\.\d{1,3}){3}|192\.168(?:\.\d{1,3}){2}|172\.(?:1[6-9]|2\d|3[01])(?:\.\d{1,3}){2})\b"
)
SECRET_TOKEN = re.compile(
    r"\b(?:sk-ant-[\w-]{20,}|sk-[\w-]{20,}|gh[pousr]_\w{20,}|github_pat_\w{20,}"
    r"|AKIA[0-9A-Z]{16}|gsk_\w{20,}|xox[abprs]-[\w-]{10,})"
    r"|(?<=[Bb]earer )[\w.~+/=-]{20,}"
)
# NAME_KEY=value, or a quoted value after spaced "=" / ":" (so code like
# SECRET_TOKEN = re.compile(...) is left alone).
SECRET_ASSIGNMENT = re.compile(
    r"\b([A-Z0-9_]*(?:API_KEY|SECRET|TOKEN|PASSWORD)[A-Z0-9_]*(?:=|\s*[:=]\s*(?=['\"]))['\"]?)[^\s'\"]+"
)
LINE_NUMBER_PREFIX = re.compile(r"^\s*\d+\t")  # "  12\t" prefix of file-reading tool output


def marker(category: str) -> str:
    return f"[REDACTED:{category}]"


def jsonl_records(text: str) -> list[str]:
    """Non-blank JSONL records. Split on LF only: str.splitlines() also breaks on U+2028, U+2029
    and U+0085, which JSON allows unescaped inside strings. The CR of a CRLF line end is dropped;
    a CR inside a string is always escaped, so it is never part of the content."""
    return [line.removesuffix("\r") for line in text.split("\n") if line.strip()]


class Redactor:
    def __init__(self, identity: dict[str, list[str]], private_terms=(), private_files: dict[str, str] | None = None):
        """identity: category -> literal values (category "home" is shown as ~)."""
        self.counts: Counter[str] = Counter()
        self._literals = [
            (value, "~" if category == "home" else marker(category), category)
            for category, values in identity.items()
            # re.escape variants catch values written inside regexes, e.g. user\.name
            for value in sorted({v for raw in values if raw and len(raw) >= MIN_LITERAL_CHARS
                                 for v in (raw, re.escape(raw))}, key=len, reverse=True)
        ]
        terms = sorted({t for t in private_terms if len(t) >= MIN_LITERAL_CHARS}, key=len, reverse=True)
        self._terms = re.compile("|".join(map(re.escape, terms)), re.IGNORECASE) if terms else None
        self._private_lines = {
            name: {line for line in map(_normalize_line, text.splitlines())
                   if len(line) >= MIN_FILE_LINE_CHARS and HAS_LETTER_OR_DIGIT.search(line)}
            for name, text in (private_files or {}).items()
        }

    @classmethod
    def for_project(cls, project_dir: Path) -> "Redactor":
        terms, files = load_config(project_dir)
        return cls(detect_identity(project_dir), terms, files)

    def text(self, s: str) -> str:
        for name, lines in self._private_lines.items():
            if len(lines.intersection(map(_normalize_line, s.splitlines()))) >= MIN_FILE_LINE_MATCHES:
                self.counts["private-file"] += 1
                return marker(f"private-file {name}")
        s = self._sub(SECRET_TOKEN, marker("secret"), s, "secret")
        s = self._sub(SECRET_ASSIGNMENT, r"\1" + marker("secret"), s, "secret")
        s = EMAIL.sub(self._email, s)
        for value, replacement, category in self._literals:
            if value in s:
                self.counts[category] += s.count(value)
                s = s.replace(value, replacement)
        s = self._sub(PRIVATE_IPV4, marker("ip"), s, "ip")
        if self._terms:
            s = self._sub(self._terms, marker("private-term"), s, "private-term")
        return s

    def record(self, obj):
        """Redact one parsed JSONL record (recursively)."""
        if isinstance(obj, str):
            return self.text(obj)
        if isinstance(obj, list):
            return [self.record(v) for v in obj]
        if not isinstance(obj, dict):
            return obj
        # "type" can itself be a dict (e.g. in tool schemas), so compare, don't hash.
        if obj.get("type") == "thinking" or obj.get("type") == "redacted_thinking":
            self.counts["model-reasoning"] += 1
            return {"type": obj["type"], "thinking": marker("model-reasoning")}
        return {self.text(k): self.record(v) for k, v in obj.items()}

    def jsonl(self, raw: str) -> str:
        out = [json.dumps(self.record(json.loads(line)), ensure_ascii=False) for line in jsonl_records(raw)]
        return "\n".join(out) + "\n"

    def _sub(self, pattern: re.Pattern, replacement: str, s: str, category: str) -> str:
        s, n = pattern.subn(replacement, s)
        if n:
            self.counts[category] += n
        return s

    def _email(self, match: re.Match) -> str:
        if match[0].lower() in EMAIL_ALLOWLIST:
            return match[0]
        self.counts["email"] += 1
        return marker("email")


def detect_identity(project_dir: Path) -> dict[str, list[str]]:
    user = getpass.getuser()
    hostname = socket.gethostname()
    hosts = [hostname, hostname.split(".")[0]]
    hosts += [_run(["scutil", "--get", key]) for key in ("LocalHostName", "ComputerName")]  # macOS only
    return {
        "home": [str(Path.home())],
        "user": [user, re.sub(r"[^A-Za-z0-9]", "-", user)],
        "host": hosts,
        "device-owner": device_owners(hosts),
        "git-user": [_run(["git", "-C", str(project_dir), "config", "user.name"])],
        "git-email": [_run(["git", "-C", str(project_dir), "config", "user.email"])],
    }


def device_owners(hosts: list[str]) -> list[str]:
    """Owner names in macOS-style device names; empty for other hostnames."""
    return [OWNER_SUFFIX.sub("", MAC_MODEL_SUFFIX.sub("", h).strip(" -")) for h in hosts if MAC_MODEL_SUFFIX.search(h)]


def load_config(project_dir: Path) -> tuple[list[str], dict[str, str]]:
    path = project_dir / CONFIG_PATH
    if not path.is_file():
        return [], {}
    config = json.loads(path.read_text(encoding="utf-8"))
    files = {}
    for name in config.get("private_files", []):
        file = project_dir / name
        if file.is_file():
            files[name] = file.read_text(encoding="utf-8", errors="replace")
    return list(config.get("private_terms", [])), files


def _normalize_line(line: str) -> str:
    return LINE_NUMBER_PREFIX.sub("", line).strip()


def _run(cmd: list[str]) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""
