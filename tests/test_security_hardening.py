"""
Security regression tests for ReadOnlyGuard, CostAnalyzer, DryRunHarness, and credential redaction.
"""

import sqlite3
from pgsafe.guards.readonly import ReadOnlyGuard
from pgsafe.guards.cost_analyzer import CostAnalyzer
from pgsafe.core.dry_run_harness import DryRunHarness
from pgsafe.server import PgSafeServer, redact_database_url


def test_comment_coalescing_and_string_literal_bypasses_blocked():
    bypasses = [
        "WITH x AS(DELETE/**/FROM/**/users/**/RETURNING/**/1)SELECT * FROM x",
        "SELECT '/*' FROM users; DROP TABLE users; SELECT '*/'",
        "EXPLAIN ANALYZE DELETE FROM users",
        "PRAGMA writable_schema = 1",
        "SELECT pg_read_file('/etc/passwd')",
        "VACUUM INTO '/tmp/leak.db'",
    ]
    for q in bypasses:
        ok, _ = ReadOnlyGuard.validate(q)
        assert ok is False, f"Bypass was not blocked: {q}"


def test_semicolon_inside_string_literal_allowed():
    ok, _ = ReadOnlyGuard.validate("SELECT 'hello; world' AS greeting")
    assert ok is True


def test_cost_analyzer_pragma_offset_cte_and_trailing_comment():
    assert CostAnalyzer.enforce_limit("PRAGMA table_info(users)") == "PRAGMA table_info(users)"
    assert CostAnalyzer.enforce_limit("EXPLAIN SELECT * FROM users") == "EXPLAIN SELECT * FROM users"

    cte_q = "WITH c AS (SELECT 1 LIMIT 5) SELECT * FROM users"
    assert CostAnalyzer.enforce_limit(cte_q, default_limit=25).endswith("LIMIT 25")

    offset_q = "SELECT * FROM users OFFSET 10"
    assert CostAnalyzer.enforce_limit(offset_q, default_limit=25) == "SELECT * FROM users LIMIT 25 OFFSET 10"

    comment_q = "SELECT * FROM users -- trailing comment"
    enforced = CostAnalyzer.enforce_limit(comment_q, default_limit=50)
    assert enforced == "SELECT * FROM users LIMIT 50"


def test_dry_run_blocks_vacuum_and_attach(tmp_path):
    db_file = tmp_path / "app.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE items (id INT, title TEXT);")
    conn.commit()
    conn.close()

    stolen = tmp_path / "stolen.db"
    res_vac = DryRunHarness.simulate_sqlite(str(db_file), f"VACUUM INTO '{stolen}';")
    assert res_vac["success"] is False
    assert not stolen.exists()

    res_att = DryRunHarness.simulate_sqlite(str(db_file), f"ATTACH DATABASE '{stolen}' AS exfil;")
    assert res_att["success"] is False


def test_security_status_redacts_password():
    redacted = redact_database_url("postgresql://admin:s3cr3tPass@db.internal:5432/prod")
    assert "s3cr3tPass" not in redacted
    assert "admin:***@db.internal:5432" in redacted

    srv = PgSafeServer(db_url="sqlite:///:memory:")
    status = srv.handle_tool_call("get_security_status", {})
    assert status["guards"]["readonly_guard"] == "ACTIVE"
