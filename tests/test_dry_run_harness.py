"""
Unit tests for DryRunHarness mutation simulation with guaranteed rollback.
"""
import sqlite3
from pgsafe.core.dry_run_harness import DryRunHarness

def test_dry_run_rollback_guarantee(tmp_path):
    db_file = tmp_path / "test_sim.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
    conn.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob');")
    conn.commit()
    conn.close()

    # Dry-run mutation (DELETE all users)
    res = DryRunHarness.simulate_sqlite(str(db_file), "DELETE FROM users;")
    assert res["success"] is True
    assert res["dry_run"] is True
    assert res["status"] == "rolled_back"
    assert res["rows_affected"] == 2

    # Verify that database was NOT modified
    verify_conn = sqlite3.connect(str(db_file))
    cur = verify_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users;")
    count = cur.fetchone()[0]
    verify_conn.close()
    assert count == 2, "State must remain unchanged after dry-run mutation simulation!"
