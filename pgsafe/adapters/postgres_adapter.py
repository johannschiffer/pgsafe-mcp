"""
PostgreSQL Database Adapter with engine-enforced READ ONLY sessions.
"""

from typing import List, Dict, Any, Tuple
from .base import BaseAdapter


class PostgresAdapter(BaseAdapter):
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self._conn = None

    def connect(self):
        if self._conn:
            return self._conn

        try:
            import psycopg
            conn = psycopg.connect(self.connection_url, autocommit=True)
            with conn.cursor() as cur:
                cur.execute("SET SESSION CHARACTERISTICS AS TRANSACTION READ ONLY;")
                cur.execute("SET default_transaction_read_only = on;")
            conn.read_only = True
            self._conn = conn
            return self._conn
        except ImportError:
            try:
                import psycopg2
                conn = psycopg2.connect(self.connection_url)
                conn.set_session(readonly=True, autocommit=True)
                self._conn = conn
                return self._conn
            except ImportError:
                raise RuntimeError(
                    "PostgreSQL driver not installed. Install psycopg via: pip install 'psycopg[binary]>=3.1.0'"
                )

    def _safe_rollback(self) -> None:
        if self._conn is not None:
            try:
                self._conn.rollback()
            except Exception:
                pass

    def list_tables(self) -> List[str]:
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                    """
                )
                return [r[0] for r in cur.fetchall()]
        except Exception:
            self._safe_rollback()
            raise

    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = %s
                    ORDER BY ordinal_position;
                    """,
                    (table_name,),
                )
                return [
                    {
                        "name": r[0],
                        "type": r[1],
                        "nullable": r[2] == "YES",
                        "default": r[3],
                    }
                    for r in cur.fetchall()
                ]
        except Exception:
            self._safe_rollback()
            raise

    def execute_read_only(self, sql: str) -> Tuple[List[str], List[List[Any]]]:
        conn = self.connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = [list(r) for r in cur.fetchall()] if cur.description else []
                return columns, rows
        except Exception:
            self._safe_rollback()
            raise
