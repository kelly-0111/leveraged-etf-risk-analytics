"""The frozen cross-check SQL on SQLite: fixtures A and B of docs/recovery-sql.md, loaded and
queried with crosscheck.sql as the harness runs it, and every row compared with the 82 frozen
expected rows of section 4. Every verdict is covered, late completion (job 2) included, and both
ways of not observing a deadline (jobs 19 and 20). The translation for SQLite is in
tests/recovery_sqlite.py; the expected rows are read from the document, never copied here.

AI contribution: written with Claude Code (Opus 5.5), at the author's request (2026-10-24).
"""
import importlib.util

import pytest
from recovery_sqlite import REPO, as_text, expected_rows, fixture_scripts, sqlite_statement

from etf_risk.jobs import harness
from etf_risk.jobs.store import SQLITE, JobStore, open_sqlite

spec = importlib.util.spec_from_file_location("collect_recovery_measurements",
                                              REPO / "analysis" / "collect_recovery_measurements.py")
crm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(crm)


@pytest.fixture(scope="module")
def actual(tmp_path_factory):
    """Each query's rows, header first, in one connection: the schema, the store rows, the
    TEMPORARY tables, the harness's rows, then Q0-Q3b and the store's invariant queries."""
    conn = open_sqlite(tmp_path_factory.mktemp("recovery-sql") / "jobs.sqlite", create=True)
    store_a, store_b, harness_a, harness_b = fixture_scripts()
    conn.executescript(store_a + store_b)
    statements = harness.crosscheck_statements()
    for name, sql in statements:
        if name == "DDL":
            conn.execute(sqlite_statement(sql))
    conn.executescript(harness_a + harness_b)
    tables = {}
    for name, sql in statements:
        if name != "DDL":
            cursor = conn.execute(sqlite_statement(sql))
            tables[name] = [[d[0] for d in cursor.description]] + [[as_text(v) for v in row] for row in cursor]
    violations = JobStore(conn, SQLITE).invariant_violations()
    tables["invariants"] = [["invariant", "job_id"]] + [[name, str(job)] for name, job in sorted(
        (name, job) for name, jobs in violations.items() for job in jobs)]          # by invariant, then job
    conn.close()
    return tables


def test_the_document_holds_82_expected_rows():
    expected = expected_rows()
    assert {name: len(rows) - 1 for name, rows in expected.items()} == {
        "Q0": 1, "Q1": 20, "Q2": 20, "Q2b": 1, "Q3a": 16, "Q3b": 17, "invariants": 7}


@pytest.mark.parametrize("query", ["Q0", "Q1", "Q2", "Q2b", "Q3a", "Q3b", "invariants"])
def test_every_row_equals_its_frozen_expected_row(actual, query):
    expected = expected_rows()[query]
    assert actual[query][0] == expected[0]                                   # the header
    assert actual[query][1:] == expected[1:]


def test_every_verdict_and_class_occurs(actual):
    def column(query, name):
        header, *rows = actual[query]
        return {row[header.index(name)] for row in rows}

    assert column("Q1", "verdict") == set(crm.Q1_VERDICTS)
    assert column("Q2", "timeliness") == set(crm.Q2_CLASSES)
    assert column("Q2", "deadline_met") == set(crm.DEADLINE_MET)
    assert column("Q3a", "log_verdict") == set(crm.Q3A_VERDICTS)
    assert column("Q3b", "report_verdict") == set(crm.Q3B_VERDICTS)


def test_late_completion_is_late_and_never_on_time(actual):
    """Job 2: running at its deadline, observed after it, succeeded later by attempt 2."""
    header, *rows = actual["Q2"]
    late = dict(zip(header, next(r for r in rows if r[header.index("job_id")] == "2")))
    assert (late["status_at_deadline"], late["final_status"], late["timeliness"], late["deadline_met"]) == (
        "running", "succeeded", "late", "no")
