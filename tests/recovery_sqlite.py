"""The recovery experiments' frozen cross-check SQL (src/etf_risk/jobs/crosscheck.sql) and the
fixture of docs/recovery-sql.md, translated for SQLite, for the offline tests.

The translation changes only this:
- the DDL loses CHARACTER SET ascii COLLATE ascii_bin: SQLite compares text byte by byte
  (its BINARY collation) by default, as ascii_bin does;
- CAST(x AS BINARY) becomes x: SQLite reads BINARY as a NUMERIC type name and would turn every
  worker id into 0, while MySQL compares the bytes, as SQLite does by default;
- in the fixture, the session variables (@s, @t0, ...) become their values, with the times
  given six decimals as MySQL's DATETIME(6) prints them; REPEAT('c', 64) becomes the literal;
  SET FOREIGN_KEY_CHECKS becomes PRAGMA foreign_keys.
The run on MySQL 8.4.13 (docs/recovery-sql.md, section 6) stays the evidence for MySQL; the
translation checks the same verdict rules offline, on every test run.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "recovery-sql.md"
FIXTURE_BLOCKS = ("-- Fixture A, store rows", "-- Fixture B, store rows", "-- Fixture A, the harness's rows",
                  "-- Fixture B, the harness's rows")
EXPECTED = ("Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b")
_TIME = re.compile(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$")


def sqlite_statement(sql: str) -> str:
    """A statement of crosscheck.sql as SQLite runs it."""
    sql = sql.replace(" CHARACTER SET ascii COLLATE ascii_bin", "")
    return re.sub(r"CAST\(([\w.]+) AS BINARY\)", r"\1", sql)


def _blocks() -> list[str]:
    return re.findall(r"^```sql\n(.*?)^```$", DOC.read_text(), flags=re.S | re.M)


def fixture_scripts() -> list[str]:
    """The fixture's four SQL blocks (store rows A and B, then the harness's rows A and B), as
    SQLite scripts. The harness's rows use the variables the store rows set, as in one session."""
    blocks = [next(b for b in _blocks() if b.startswith(prefix)) for prefix in FIXTURE_BLOCKS]
    values = {}
    for block in blocks:
        values.update(re.findall(r"@(\w+)\s*=\s*'([^']*)'", block))
    literals = {name: f"'{value}.000000'" if _TIME.match(value) else f"'{value}'" for name, value in values.items()}
    scripts = []
    for block in blocks:
        statements = [st for st in re.split(r";\s*\n", block) if st.strip()]
        out = []
        for statement in statements:
            body = "\n".join(line for line in statement.splitlines() if not line.lstrip().startswith("--")).strip()
            if body.startswith("SET @"):
                continue
            if body.startswith("SET FOREIGN_KEY_CHECKS"):
                body = "PRAGMA foreign_keys = " + ("ON" if body.rstrip(";").endswith("1") else "OFF")
            body = re.sub(r"REPEAT\('(.)', 64\)", lambda m: f"'{m.group(1) * 64}'", body)
            body = re.sub(r"@(\w+)", lambda m: literals[m.group(1)], body)
            out.append(body.rstrip(";") + ";")
        scripts.append("\n".join(out))
    return scripts


def expected_rows() -> dict[str, list[list[str]]]:
    """Section 4's frozen tables, header first, with c×64 written out: Q0-Q3b and
    "invariants" (the store's seven invariant queries)."""
    text = DOC.read_text()
    section = text[text.index("## 4. Expected rows (frozen)"):text.index("## 5. Coverage")]
    names = {f"**{name}**": name for name in EXPECTED}
    tables, current = {}, None
    for line in section.splitlines():
        if line.strip() in names:
            current = names[line.strip()]
        elif line.startswith("**The store's seven invariant queries**"):
            current = "invariants"
        elif line.startswith("|") and current is not None:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if set("".join(cells)) <= set("-"):
                continue
            tables.setdefault(current, []).append([_expand(c) for c in cells])
        elif line.strip() and not line.startswith("|") and current in tables:
            current = None
    return tables


def _expand(cell: str) -> str:
    match = re.fullmatch(r"(.)×64", cell)
    return match.group(1) * 64 if match else cell


def as_text(value) -> str:
    """A value as section 4 writes it: NULL, or the value's text."""
    return "NULL" if value is None else str(value)
