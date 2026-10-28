"""
PgSafe CLI inspection tool.
Usage:
  pgsafe-cli tables --db sqlite:///demo.db
  pgsafe-cli describe users --db sqlite:///demo.db
  pgsafe-cli query "SELECT * FROM users" --db sqlite:///demo.db
"""

import argparse
import json
import sys
from . import __version__
from .server import PgSafeServer
from .guards.readonly import ReadOnlyGuard
from .guards.cost_analyzer import CostAnalyzer


def main():
    parser = argparse.ArgumentParser(
        prog="pgsafe-cli",
        description="PgSafe CLI database utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-v", "--version", action="version", version=f"pgsafe-mcp {__version__}")
    parser.add_argument("--db", default=None, help="Database connection URL")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    subparsers.add_parser("tables", help="List database tables")

    desc_parser = subparsers.add_parser("describe", help="Describe table structure")
    desc_parser.add_argument("table", help="Table name")

    query_parser = subparsers.add_parser("query", help="Execute safe read-only query")
    query_parser.add_argument("sql", help="SQL query")
    query_parser.add_argument("--limit", type=int, default=100, help="Row limit")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    server = PgSafeServer(db_url=args.db)
    adapter = server.adapter

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


if __name__ == "__main__":
    main()
