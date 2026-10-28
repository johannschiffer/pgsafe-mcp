"""
PgSafe MCP: Model Context Protocol Server
Provides read-only SQL validation, PII masking, dry-run mutation simulation,
and index recommendation tools over stdio.
"""

import sys
import os
import json
import logging
import argparse
from urllib.parse import urlsplit, urlunsplit
from typing import Dict, Any, List, Optional
from . import __version__
from .guards.readonly import ReadOnlyGuard
from .guards.cost_analyzer import CostAnalyzer
from .adapters.sqlite_adapter import SQLiteAdapter
from .adapters.postgres_adapter import PostgresAdapter
from .core.pii_masker import PIIMasker
from .core.dry_run_harness import DryRunHarness
from .core.index_advisor import IndexAdvisor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [PgSafe] %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("PgSafeServer")


def _default_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    if os.path.exists("data/nexus.db"):
        return "sqlite:///data/nexus.db"
    return "sqlite:///:memory:"


def redact_database_url(url: str) -> str:
    """Redacts password credentials from database connection strings before returning to callers."""
    if not url or url.startswith("sqlite:"):
        return url
    try:
        parts = urlsplit(url)
        if parts.password:
            host_part = f"{parts.hostname or ''}"
            if parts.port:
                host_part = f"{host_part}:{parts.port}"
            user_part = f"{parts.username}:***@" if parts.username else "***@"
            return urlunsplit((parts.scheme, f"{user_part}{host_part}", parts.path, parts.query, parts.fragment))
    except Exception:
        pass
    return url


class PgSafeServer:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or _default_database_url()
        self.server_name = "pgsafe-mcp"
        self.server_version = __version__
        self.adapter = self._init_adapter(self.db_url)

    def _init_adapter(self, url: str):
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            return PostgresAdapter(url)
        if url.startswith("sqlite:///"):
            return SQLiteAdapter(url[len("sqlite:///"):])
        if url.startswith("sqlite://"):
            return SQLiteAdapter(url[len("sqlite://"):])
        if "://" in url:
            scheme = url.split("://", 1)[0]
            raise ValueError(
                f"Unsupported database scheme '{scheme}'. Supported schemes: postgresql://, postgres://, sqlite:///"
            )
        return SQLiteAdapter(url)

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_tables",
                "description": "List all database tables available for inspection.",
                "inputSchema": {"type": "object", "properties": {}},
            },
            {
                "name": "describe_table",
                "description": "Inspect column names, data types, nullability, and primary keys for a table.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Table name to inspect"}
                    },
                    "required": ["table_name"],
                },
            },
            {
                "name": "safe_query",
                "description": "Execute a strictly read-only SQL query with automatic LIMIT enforcement and real-time PII redaction.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL SELECT/EXPLAIN query"},
                        "limit": {"type": "integer", "description": "Max rows to return (default: 100, max: 1000)"},
                        "mask_pii": {
                            "type": "boolean",
                            "description": "Redact customer emails, credit cards and password hashes (default: true)",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "dry_run_mutation",
                "description": "Simulate an INSERT, UPDATE, or DELETE query in an isolated SQLite transaction with guaranteed auto-ROLLBACK.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mutation_sql": {"type": "string", "description": "Mutation SQL statement to test"}
                    },
                    "required": ["mutation_sql"],
                },
            },
            {
                "name": "analyze_query",
                "description": "Evaluate query complexity, full table scan risks, and missing filters without execution.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to inspect"}
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "recommend_indexes",
                "description": "Analyze SQL query filters to recommend composite or single-column indexes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to optimize"}
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_security_status",
                "description": "Check status of active security engines (PII Masker, Read-Only Guard, Dry-Run Harness).",
                "inputSchema": {"type": "object", "properties": {}},
            },
        ]

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if name == "list_tables":
            tables = self.adapter.list_tables()
            return {"success": True, "tables": tables, "count": len(tables)}

        elif name == "describe_table":
            table_name = arguments.get("table_name", "")
            columns = self.adapter.describe_table(table_name)
            return {"success": True, "table": table_name, "columns": columns}

        elif name == "safe_query":
            raw_sql = arguments.get("query", "")
            limit = arguments.get("limit", 100)
            mask_pii = arguments.get("mask_pii", True)

            is_safe, reason = ReadOnlyGuard.validate(raw_sql)
            if not is_safe:
                return {
                    "success": False,
                    "error": f"Security Guard Blocked Query: {reason}",
                    "blocked": True,
                }

            safe_sql = CostAnalyzer.enforce_limit(raw_sql, default_limit=limit)
            risk = CostAnalyzer.evaluate_risk(raw_sql)

            try:
                cols, rows = self.adapter.execute_read_only(safe_sql)
                if mask_pii:
                    rows = PIIMasker.mask_dataset(cols, rows)

                return {
                    "success": True,
                    "query_executed": safe_sql,
                    "columns": cols,
                    "rows": rows,
                    "row_count": len(rows),
                    "pii_redacted": mask_pii,
                    "risk_analysis": risk,
                }
            except Exception as e:
                return {"success": False, "error": f"Database execution error: {str(e)}"}

        elif name == "dry_run_mutation":
            mutation_sql = arguments.get("mutation_sql", "")
            if isinstance(self.adapter, SQLiteAdapter):
                return DryRunHarness.simulate_sqlite(self.adapter.db_path, mutation_sql)
            return {
                "success": False,
                "error": "Dry-run mutation is configured for SQLite engines.",
            }

        elif name == "analyze_query":
            raw_sql = arguments.get("query", "")
            is_safe, reason = ReadOnlyGuard.validate(raw_sql)
            risk = CostAnalyzer.evaluate_risk(raw_sql)
            return {
                "success": True,
                "is_read_only": is_safe,
                "security_verdict": reason,
                "performance_risk": risk,
            }

        elif name == "recommend_indexes":
            raw_sql = arguments.get("query", "")
            recommendations = IndexAdvisor.analyze_and_recommend(raw_sql)
            return {
                "success": True,
                "query": raw_sql,
                "recommendations": recommendations,
                "count": len(recommendations),
            }

        elif name == "get_security_status":
            return {
                "database_url": redact_database_url(self.db_url),
                "guards": {
                    "readonly_guard": "ACTIVE",
                    "pii_masking_engine": "ACTIVE",
                    "dry_run_mutation_harness": "ACTIVE",
                    "cost_analyzer": "ACTIVE",
                    "index_advisor": "ACTIVE",
                },
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not isinstance(request, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32600, "message": "Invalid Request"},
            }

        method = request.get("method")
        if "id" not in request or request.get("id") is None:
            if method == "notifications/initialized":
                logger.info("Client completed initialization handshake.")
            return None

        req_id = request.get("id")
        params = request.get("params") or {}

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": self.server_name,
                        "version": self.server_version,
                    },
                },
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tools_definition()},
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments") or {}
            try:
                output = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(output, indent=2, ensure_ascii=False),
                            }
                        ],
                        "isError": not output.get("success", True) if "success" in output else False,
                    },
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)},
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

    def run_stdio(self):
        logger.info(f"Starting {self.server_name} v{self.server_version} stdio listener...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
            except json.JSONDecodeError as e:
                sys.stdout.write(
                    json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}})
                    + "\n"
                )
                sys.stdout.flush()
                continue
            try:
                response = self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                logger.error(f"Error processing stdio line: {e}")


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(prog="pgsafe-mcp", description="PgSafe Model Context Protocol stdio server")
    parser.add_argument("-v", "--version", action="version", version=f"pgsafe-mcp {__version__}")
    parser.add_argument("--db", default=None, help="Database connection URL (overrides DATABASE_URL)")
    args = parser.parse_args(argv)
    server = PgSafeServer(db_url=args.db)
    server.run_stdio()


if __name__ == "__main__":
    main()
