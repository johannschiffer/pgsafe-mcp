"""
Dry-Run Mutation Simulation Harness.
Executes single DML statements inside an isolated transaction with authorizer guards
and guaranteed auto-ROLLBACK.
"""

import re
import time
import sqlite3
from typing import Dict, Any
from ..guards.readonly import sanitize_sql_literals_and_comments


def _dry_run_authorizer(action_code: int, param1, param2, db_name, trigger_name) -> int:
    if action_code in (sqlite3.SQLITE_ATTACH, sqlite3.SQLITE_DETACH):
        return sqlite3.SQLITE_DENY
    if action_code == sqlite3.SQLITE_PRAGMA:
        return sqlite3.SQLITE_DENY
    return sqlite3.SQLITE_OK


class DryRunHarness:
    @staticmethod
    def simulate_sqlite(db_path: str, mutation_sql: str) -> Dict[str, Any]:
        """Runs a single DML/DDL statement inside a transaction and rolls it back immediately."""
        if not isinstance(mutation_sql, str) or not mutation_sql.strip():
            return {"success": False, "dry_run": True, "error": "Dry-run simulation failed: Empty SQL provided."}

        ok, normalized = sanitize_sql_literals_and_comments(mutation_sql)
        if not ok:
            return {"success": False, "dry_run": True, "error": f"Dry-run simulation failed: {normalized}"}

        statements = [s.strip() for s in normalized.split(";") if s.strip()]
        if len(statements) != 1:
            return {
                "success": False,
                "dry_run": True,
                "error": "Dry-run simulation failed: Only a single SQL statement is permitted.",
            }

        if re.search(r"\b(VACUUM|ATTACH|DETACH|LOAD_EXTENSION)\b", statements[0], re.IGNORECASE):
            return {
                "success": False,
                "dry_run": True,
                "error": "Dry-run simulation failed: Filesystem or non-transactional commands (VACUUM/ATTACH) are forbidden.",
            }

        conn = sqlite3.connect(db_path, timeout=10.0, isolation_level=None)
        conn.set_authorizer(_dry_run_authorizer)
        cursor = conn.cursor()

        start_time = time.time()
        try:
            cursor.execute("BEGIN IMMEDIATE;")
            cursor.execute(mutation_sql)
            rows_affected = cursor.rowcount
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            cursor.execute("ROLLBACK;")
            return {
                "success": True,
                "dry_run": True,
                "status": "rolled_back",
                "rows_affected": rows_affected,
                "execution_time_ms": elapsed_ms,
                "message": f"Simulation successful. Query would modify {rows_affected} rows. Changes rolled back.",
            }
        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
            except Exception:
                pass
            return {
                "success": False,
                "dry_run": True,
                "error": f"Dry-run simulation failed: {str(e)}",
            }
        finally:
            conn.close()
