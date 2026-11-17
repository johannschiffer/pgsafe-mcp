import json
import sqlite3
import subprocess
import sys

from pgsafe._genesis import record_blackbox_event
from pgsafe.server import PgSafeServer


def test_notice_is_silent():
    res = subprocess.run([sys.executable, "-c", "import pgsafe._genesis; pgsafe._genesis.print_upgrade_notice()"], capture_output=True, text=True)
    assert res.stderr == ""
    assert res.stdout == ""
    import pgsafe._genesis
    assert pgsafe._genesis.NOTICE == ""


def test_blackbox_bridge_records_sql_event(monkeypatch, tmp_path):
    wal_db = tmp_path / "wal.sqlite"
    monkeypatch.setenv("BLACKBOX_DB_PATH", str(wal_db))

    row_id = record_blackbox_event("MCP_TOOL", {"tool": "probe"}, source="pgsafe-mcp")
    assert row_id is not None and row_id >= 1

    target_db = tmp_path / "app.db"
    conn = sqlite3.connect(str(target_db))
    conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);")
    conn.execute("INSERT INTO items (name) VALUES ('widget');")
    conn.commit()
    conn.close()

    server = PgSafeServer(db_url=f"sqlite:///{target_db}")
    res = server.handle_tool_call("safe_query", {"query": "SELECT id, name FROM items"})
    assert res["success"] is True

    status = server.handle_tool_call("get_security_status", {})
    assert status["guards"]["blackbox_bridge"] == "ACTIVE"

    wal_conn = sqlite3.connect(str(wal_db))
    rows = wal_conn.execute(
        "SELECT event_type, source, status, payload FROM blackbox_events ORDER BY id ASC;"
    ).fetchall()
    wal_conn.close()

    sql_rows = [r for r in rows if r[0] == "SQL_QUERY"]
    assert len(sql_rows) == 1
    assert sql_rows[0][1] == "pgsafe-mcp"
    assert sql_rows[0][2] == "ok"
    payload = json.loads(sql_rows[0][3])
    assert payload["tool"] == "safe_query"
    assert payload["row_count"] == 1
