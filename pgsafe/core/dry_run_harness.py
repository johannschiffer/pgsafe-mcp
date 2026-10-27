"""
Dry-Run Mutation Simulation Harness (PgSafe Pro Feature).
Allows AI agents to test INSERT/UPDATE/DELETE statements in an isolated transaction
with guaranteed auto-ROLLBACK, returning simulated rows affected without modifying state.
"""
import time
from typing import Dict, Any

class DryRunHarness:
    @staticmethod
    def simulate_sqlite(db_path: str, mutation_sql: str) -> Dict[str, Any]:
        """Runs mutation inside a transaction and rolls it back immediately."""
        import sqlite3
        conn = sqlite3.connect(db_path, timeout=10.0)
        cursor = conn.cursor()

        start_time = time.time()
        try:
            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute(mutation_sql)
            rows_affected = cursor.rowcount
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            cursor.execute("ROLLBACK;")
            conn.close()

            return {
                "success": True,
                "dry_run": True,
                "status": "rolled_back",
                "rows_affected": rows_affected,
                "execution_time_ms": elapsed_ms,
                "message": f"Simulation successful. Query would modify {rows_affected} rows. Changes rolled back."
            }
        except Exception as e:
            try:
                cursor.execute("ROLLBACK;")
                conn.close()
            except Exception:
                pass
            return {
                "success": False,
                "dry_run": True,
                "error": f"Dry-run simulation failed: {str(e)}"
            }
