"""
Unit tests for PgSafe MCP Server JSON-RPC protocol compliance.
"""
import pytest
import sqlite3
import json
from pgsafe.server import PgSafeServer

@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_mcp.db"
    conn = sqlite3.connect(str(db_file))
    conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY, title TEXT, price REAL, secret_sku TEXT);")
    conn.execute("INSERT INTO products (title, price, secret_sku) VALUES ('Laptop', 999.99, 'SKU-SECRET-1234');")
    conn.commit()
    conn.close()
    return str(db_file)

def test_mcp_initialize(test_db):
    server = PgSafeServer(db_url=f"sqlite:///{test_db}")
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    }
    resp = server.handle_request(req)
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "pgsafe-mcp"

def test_mcp_list_and_safe_query(test_db):
    server = PgSafeServer(db_url=f"sqlite:///{test_db}")

    # 1. list_tables
    req_list = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "list_tables", "arguments": {}}
    }
    resp_list = server.handle_request(req_list)
    content = json.loads(resp_list["result"]["content"][0]["text"])
    assert "products" in content["tables"]

    # 2. safe_query
    req_query = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "safe_query",
            "arguments": {"query": "SELECT * FROM products"}
        }
    }
    resp_query = server.handle_request(req_query)
    q_content = json.loads(resp_query["result"]["content"][0]["text"])
    assert q_content["success"] is True
    assert q_content["row_count"] == 1

    # 3. Blocked query
    req_blocked = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "safe_query",
            "arguments": {"query": "DROP TABLE products;"}
        }
    }
    resp_blocked = server.handle_request(req_blocked)
    b_content = json.loads(resp_blocked["result"]["content"][0]["text"])
    assert b_content["success"] is False
    assert b_content["blocked"] is True

def test_mcp_security_status(test_db):
    server = PgSafeServer(db_url=f"sqlite:///{test_db}")
    req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {"name": "get_security_status", "arguments": {}}
    }
    resp = server.handle_request(req)
    content = json.loads(resp["result"]["content"][0]["text"])
    assert content["guards"]["readonly_guard"] == "ACTIVE"
    assert content["guards"]["pii_masking_engine"] == "ACTIVE"
