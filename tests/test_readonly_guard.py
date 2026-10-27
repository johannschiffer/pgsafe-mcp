"""
Unit tests for ReadOnlyGuard security validation.
"""
import pytest
from pgsafe.guards.readonly import ReadOnlyGuard

def test_readonly_allowed_queries():
    allowed = [
        "SELECT * FROM users",
        "SELECT id, name FROM customers WHERE active = 1",
        "EXPLAIN SELECT count(*) FROM orders",
        "WITH active_users AS (SELECT id FROM users WHERE active = 1) SELECT * FROM active_users",
        "SELECT 1",
        "PRAGMA table_info(users)"
    ]
    for sql in allowed:
        is_safe, reason = ReadOnlyGuard.validate(sql)
        assert is_safe is True, f"Failed for query: {sql} - Reason: {reason}"

def test_readonly_blocked_destructive_mutations():
    blocked = [
        "DROP TABLE users",
        "TRUNCATE TABLE audit_logs",
        "DELETE FROM orders WHERE id = 1",
        "UPDATE users SET role = 'admin' WHERE id = 5",
        "INSERT INTO users (name) VALUES ('hacker')",
        "ALTER TABLE users DROP COLUMN email",
        "GRANT ALL PRIVILEGES ON DATABASE db TO user",
        "EXEC sp_executesql N'SELECT 1'"
    ]
    for sql in blocked:
        is_safe, reason = ReadOnlyGuard.validate(sql)
        assert is_safe is False, f"Expected blocked for query: {sql}"
        assert "Blocked keyword" in reason or "disallowed" in reason

def test_semicolon_chaining_blocked():
    malicious = "SELECT * FROM users; DROP TABLE logs;"
    is_safe, reason = ReadOnlyGuard.validate(malicious)
    assert is_safe is False
    assert "Multiple SQL statements" in reason
