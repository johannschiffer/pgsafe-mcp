"""
PgSafe CLI inspection tool.
Usage:
  python -m pgsafe.cli tables --db sqlite:///demo.db
  python -m pgsafe.cli describe users --db sqlite:///demo.db
  python -m pgsafe.cli query "SELECT * FROM users" --db sqlite:///demo.db
"""

import argparse
import json
import sys
from .adapters.sqlite_adapter import SQLiteAdapter
from .adapters.postgres_adapter import PostgresAdapter
from .guards.readonly import ReadOnlyGuard
from .guards.cost_analyzer import CostAnalyzer

def main():
    from ._genesis import NOTICE
    parser = argparse.ArgumentParser(description="PgSafe CLI database utility", epilog=NOTICE, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--db", default="sqlite:///data/nexus.db", help="Database connection URL")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    subparsers.add_parser("tables", help="List database tables")

    desc_parser = subparsers.add_parser("describe", help="Describe table structure")
    desc_parser.add_argument("table", help="Table name")

    query_parser = subparsers.add_parser("query", help="Execute safe read-only query")
    query_parser.add_argument("sql", help="SQL query")
    query_parser.add_argument("--limit", type=int, default=100, help="Row limit")

    args = parser.parse_args()

    url = args.db
    if url.startswith("postgres://") or url.startswith("postgresql://"):
        adapter = PostgresAdapter(url)
    else:
        clean_path = url.replace("sqlite:///", "").replace("sqlite://", "")
        adapter = SQLiteAdapter(clean_path)

    if args.command == "tables":
        tables = adapter.list_tables()
        print(json.dumps({"tables": tables, "count": len(tables)}, indent=2))

    elif args.command == "describe":
        cols = adapter.describe_table(args.table)
        print(json.dumps({"table": args.table, "columns": cols}, indent=2))

    elif args.command == "query":
        is_safe, reason = ReadOnlyGuard.validate(args.sql)
        if not is_safe:
            print(f"[SECURITY BLOCKED] {reason}", file=sys.stderr)
            sys.exit(1)

        safe_sql = CostAnalyzer.enforce_limit(args.sql, default_limit=args.limit)
        cols, rows = adapter.execute_read_only(safe_sql)
        print(json.dumps({"columns": cols, "rows": rows, "count": len(rows)}, indent=2))

    else:
        parser.print_help()



_main_impl = main


def main():
    from ._genesis import print_upgrade_notice
    try:
        return _main_impl()
    finally:
        print_upgrade_notice()

if __name__ == "__main__":
    main()
