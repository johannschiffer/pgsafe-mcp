import sqlite3
from pgsafe.guards.readonly import ReadOnlyGuard
from pgsafe.core.dry_run_harness import DryRunHarness

def main():
    guard = ReadOnlyGuard()
    # Verifies SQL AST syntax and blocks unauthorized write queries
    is_safe, error = guard.validate_query("SELECT id, name FROM users LIMIT 10;")
    print("Is query safe?", is_safe)

    # Dry-run harness simulates mutations within an auto-rollback transaction
    harness = DryRunHarness("sqlite:///:memory:")
    sim_result = harness.simulate("CREATE TABLE test (id INT); INSERT INTO test VALUES (1);")
    print("Simulation status:", sim_result.get("status"))

if __name__ == "__main__":
    main()
