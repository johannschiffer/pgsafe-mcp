"""
SQLite Database Adapter with Read-Only URI and SQLite authorizer enforcement.
"""

import os
import sqlite3
from typing import List, Dict, Any, Tuple
from .base import BaseAdapter

_ALLOWED_READ_PRAGMAS = {
    "table_info",
    "table_xinfo",
    "table_list",
    "index_list",
    "index_info",
    "index_xinfo",
    "foreign_key_list",
    "database_list",
    "compile_options",
    "query_only",
}


def _readonly_authorizer(action_code: int, param1, param2, db_name, trigger_name) -> int:
    if action_code in (
        sqlite3.SQLITE_SELECT,
        sqlite3.SQLITE_READ,
        sqlite3.SQLITE_FUNCTION,
    ):
        return sqlite3.SQLITE_OK
    if action_code == sqlite3.SQLITE_PRAGMA:
        if param1 and str(param1).lower() in _ALLOWED_READ_PRAGMAS and param2 is None:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_DENY


class SQLiteAdapter(BaseAdapter):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def connect(self):
        if not self._conn:
            if self.db_path == ":memory:":
                conn = sqlite3.connect(":memory:", timeout=10.0)
                conn.execute("PRAGMA query_only = ON;")
            else:
                if not os.path.exists(self.db_path):
                    raise FileNotFoundError(f"SQLite database file not found: {self.db_path}")
                uri = f"file:{self.db_path}?mode=ro"
                conn = sqlite3.connect(uri, uri=True, timeout=10.0)
            conn.row_factory = sqlite3.Row
            conn.set_authorizer(_readonly_authorizer)
            self._conn = conn
        return self._conn

    def list_tables(self) -> List[str]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;"
        )
        return [row[0] for row in cursor.fetchall()]

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.cursor()
        safe_name = "".join(c for c in table_name if c.isalnum() or c == "_")
        if not safe_name:
            return []
        cursor.execute(f'PRAGMA table_info("{safe_name}");')
        rows = cursor.fetchall()
        return [
            {
                "cid": r[0],
                "name": r[1],
                "type": r[2],
                "notnull": bool(r[3]),
                "dflt_value": r[4],
                "pk": bool(r[5]),
            }
            for r in rows
        ]

    def execute_read_only(self, sql: str) -> Tuple[List[str], List[List[Any]]]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(r) for r in cursor.fetchall()] if cursor.description else []
        return columns, rows
