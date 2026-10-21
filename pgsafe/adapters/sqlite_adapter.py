"""
SQLite Database Adapter with Read-Only URI enforcement.
"""
import sqlite3
from typing import List, Dict, Any, Tuple
from .base import BaseAdapter

class SQLiteAdapter(BaseAdapter):
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = None

    def connect(self):
        if not self._conn:
            # Enforce read-only mode via SQLite URI if file exists
            uri = f"file:{self.db_path}?mode=ro"
            try:
                self._conn = sqlite3.connect(uri, uri=True, timeout=10.0)
            except sqlite3.OperationalError:
                # Fallback to standard connect with PRAGMA query_only
                self._conn = sqlite3.connect(self.db_path, timeout=10.0)
                self._conn.execute("PRAGMA query_only = ON;")
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def list_tables(self) -> List[str]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
        return [row[0] for row in cursor.fetchall()]

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.cursor()
        # Sanitize table_name to identifier
        safe_name = "".join(c for c in table_name if c.isalnum() or c == "_")
        cursor.execute(f"PRAGMA table_info({safe_name});")
        rows = cursor.fetchall()
        return [
            {
                "cid": r[0],
                "name": r[1],
                "type": r[2],
                "notnull": bool(r[3]),
                "dflt_value": r[4],
                "pk": bool(r[5])
            }
            for r in rows
        ]

    def execute_read_only(self, sql: str) -> Tuple[List[str], List[List[Any]]]:
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(r) for r in cursor.fetchall()]
        return columns, rows
