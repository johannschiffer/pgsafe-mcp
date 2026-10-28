import os
import sqlite3
import tempfile
from pgsafe.guards.readonly import ReadOnlyGuard
from pgsafe.core.dry_run_harness import DryRunHarness


def main():
    is_safe, verdict = ReadOnlyGuard.validate("SELECT id, name FROM users LIMIT 10")
    print("Is query safe?", is_safe, "|", verdict)

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);")
        conn.commit()
        conn.close()

        sim_result = DryRunHarness.simulate_sqlite(
            db_path,
            "INSERT INTO users (id, name) VALUES (1, 'Alice');",
        )
        print("Simulation status:", sim_result.get("status"), "| rows:", sim_result.get("rows_affected"))
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


if __name__ == "__main__":
    main()
