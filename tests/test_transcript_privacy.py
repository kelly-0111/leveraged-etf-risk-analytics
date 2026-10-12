"""Redaction rules for shared Claude Code transcripts (.claude/hooks/transcript_privacy.py).

Uses a made-up identity so the tests do not depend on this machine.
AI contribution: written with Claude Code (Opus 5.5).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "hooks"))

from transcript_privacy import Redactor, device_owners  # noqa: E402

IDENTITY = {
    "home": ["/Users/alice.w"],
    "user": ["alice.w", "alice-w"],
    "host": ["alices-MacBook-Air.local", "alices-MacBook-Air"],
    "git-user": ["alice-99"],
    "git-email": ["aw1@uni.edu"],
}
PRIVATE_FILE = "# Plan\nDeadline: 2026-11-18 per advisor email\nSend CV and SOP draft to Dr. Quill\nList courses and semesters taken\n"


def redactor(**kwargs):
    return Redactor(IDENTITY, **kwargs)


def test_identity_values_are_replaced_with_markers():
    r = redactor()
    out = r.text("cd /Users/alice.w/proj && whoami -> alice.w on alices-MacBook-Air.local, -Users-alice-w-proj, author alice-99")
    assert out == ("cd ~/proj && whoami -> [REDACTED:user] on [REDACTED:host], "
                   "-Users-[REDACTED:user]-proj, author [REDACTED:git-user]")
    assert r.counts == {"home": 1, "user": 2, "host": 1, "git-user": 1}


def test_owner_name_is_taken_from_macos_device_names():
    hosts = ["Alice's MacBook Air", "爱丽丝的MacBook Pro", "alicewdeMacBook-Air.local", "Alices-iMac", "build-server"]
    assert device_owners(hosts) == ["Alice", "爱丽丝", "alicewde", "Alices"]


def test_emails_are_redacted_except_allowlist():
    r = redactor()
    out = r.text("mail aw1@uni.edu or bob@gmail.com; Co-Authored-By: Claude <noreply@anthropic.com>")
    assert out == "mail [REDACTED:email] or [REDACTED:email]; Co-Authored-By: Claude <noreply@anthropic.com>"
    assert r.counts["email"] == 2


def test_code_decorators_are_not_emails():
    assert redactor().text("x = 1\n@pytest.fixture\ndef spark(): ...") == "x = 1\n@pytest.fixture\ndef spark(): ..."


def test_regex_escaped_values_are_redacted():
    # e.g. a grep command that searches for the values themselves
    out = redactor().text(r"grep -E 'bob99@gmail\.com|/Users/alice\.w|alice\.w'")
    assert out == r"grep -E '[REDACTED:email]|~|[REDACTED:user]'"


def test_code_assignments_are_not_secrets():
    code = 'SECRET_TOKEN = re.compile(r"...")\nAPI_KEY = "abc123secret"'
    assert redactor().text(code) == 'SECRET_TOKEN = re.compile(r"...")\nAPI_KEY = "[REDACTED:secret]"'


def test_private_ips_and_secrets():
    r = redactor()
    out = r.text("using 10.0.12.34 not 127.0.0.1; py4j==0.10.9.9; GROQ_API_KEY=gsk_abcdefghijklmnopqrstuvwx "
                 "token ghp_abcdefghijklmnopqrstuvwxyz0123 Authorization: Bearer abcdefghijklmnopqrstuvwxyz")
    assert "10.0.12" not in out and "127.0.0.1" in out and "0.10.9.9" in out
    assert "GROQ_API_KEY=[REDACTED:secret]" in out
    assert "ghp_" not in out and "Bearer [REDACTED:secret]" in out


def test_private_terms_are_case_insensitive():
    out = redactor(private_terms=["Quill"]).text("Per QUILL's screenshot and quill")
    assert out == "Per [REDACTED:private-term]'s screenshot and [REDACTED:private-term]"


def test_text_reproducing_a_private_file_is_replaced_whole():
    r = redactor(private_files={"docs/plan.md": PRIVATE_FILE})
    numbered = "\n".join(f"{i:>6}\t{line}" for i, line in enumerate(PRIVATE_FILE.splitlines(), 1))
    assert r.text(numbered) == "[REDACTED:private-file docs/plan.md]"
    # Mentioning the file or one line of it is fine.
    assert r.text("see docs/plan.md: Send CV and SOP draft to Dr. Quill") == "see docs/plan.md: Send CV and SOP draft to Dr. Quill"


def test_jsonl_records_stay_valid_and_reasoning_is_removed():
    raw = "\n".join(json.dumps(rec) for rec in [
        {"type": "user", "cwd": "/Users/alice.w/proj", "message": {"content": "my email is aw1@uni.edu"}},
        {"type": "attachment", "schema": {"type": {"anyOf": ["string"]}}},  # non-string "type"
        {"type": "assistant", "message": {"content": [
            {"type": "thinking", "thinking": "The user is probably in Madison", "signature": "abc123"},
            {"type": "text", "text": "Done."},
        ]}},
    ])
    r = redactor()
    lines = r.jsonl(raw).splitlines()
    user, _, assistant = (json.loads(line) for line in lines)
    assert user["cwd"] == "~/proj"
    assert user["message"]["content"] == "my email is [REDACTED:email]"
    assert assistant["message"]["content"][0] == {"type": "thinking", "thinking": "[REDACTED:model-reasoning]"}
    assert assistant["message"]["content"][1]["text"] == "Done."
    assert "Madison" not in "\n".join(lines) and "abc123" not in "\n".join(lines)
