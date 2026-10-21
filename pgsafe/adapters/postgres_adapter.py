"""
PostgreSQL Database Adapter with READ ONLY transaction guarantees.
"""
from typing import List, Dict, Any, Tuple, Optional
from .base import BaseAdapter

class PostgresAdapter(BaseAdapter):
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self._conn = None

    def connect(self):
        if self._conn:
            return self._conn

        try:
            # Attempt psycopg2 or psycopg or asyncpg
            import psycopg
            self._conn = psycopg.connect(self.connection_url)
            # Guarantee read-only session at PostgreSQL engine level
            with self._conn.cursor() as cur:
                cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")
            return self._conn
        except ImportError:
            try:
                import psycopg2
                self._conn = psycopg2.connect(self.connection_url)
                self._conn.set_session(readonly=True)
                return self._conn
            except ImportError:
                raise RuntimeError(
                    "PostgreSQL driver not installed. Install psycopg via: pip install psycopg[binary] "
                    "or use SQLite adapter."
                )

    def list_tables(self) -> List[str]:
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            return [r[0] for r in cur.fetchall()]

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s
                ORDER BY ordinal_position;
            """, (table_name,))
            return [
                {
                    "name": r[0],
                    "type": r[1],
                    "nullable": r[2] == "YES",
                    "default": r[3]
                }
                for r in cur.fetchall()
            ]

    def execute_read_only(self, sql: str) -> Tuple[List[str], List[List[Any]]]:
        conn = self.connect()
        with conn.cursor() as cur:
            cur.execute(sql)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = [list(r) for r in cur.fetchall()]
            return columns, rows
