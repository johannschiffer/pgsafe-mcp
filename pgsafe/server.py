"""
PgSafe MCP: Model Context Protocol Server (Lite Edition)
Implements standard JSON-RPC 2.0 stdio transport with Zero-Trust database access.
"""

import sys
import os
import json
import logging
from typing import Dict, Any, List, Optional
from .guards.readonly import ReadOnlyGuard
from .guards.cost_analyzer import CostAnalyzer
from .adapters.sqlite_adapter import SQLiteAdapter
from .adapters.postgres_adapter import PostgresAdapter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [PgSafe] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("PgSafeServer")

class PgSafeMCPServer:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///demo.db")
        self.server_name = "pgsafe-mcp"
        self.server_version = "1.0.0"
        self.adapter = self._init_adapter(self.db_url)

    def _init_adapter(self, url: str):
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            return PostgresAdapter(url)
        else:
            # Assume SQLite path or sqlite:///
            clean_path = url.replace("sqlite:///", "").replace("sqlite://", "")
            return SQLiteAdapter(clean_path)

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_tables",
                "description": "List all public database tables available for inspection and querying.",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "describe_table",
                "description": "Retrieve column definitions, data types, nullability, and keys for a specific table.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to inspect"
                        }
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "safe_query",
                "description": "Execute a strictly read-only SQL query with automatic LIMIT enforcement and mutation blocking.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to execute (must be SELECT/EXPLAIN)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum rows to return (default: 100, max: 1000)"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "analyze_query",
                "description": "Analyze a SQL query for dangerous operations, unindexed scans, and Cartesian join risks without executing it.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "SQL query to inspect"
                        }
                    },
                    "required": ["query"]
                }
            }
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

            # 1. Read-only validation
            is_safe, reason = ReadOnlyGuard.validate(raw_sql)
            if not is_safe:
                return {
                    "success": False,
                    "error": f"Security Guard Blocked Query: {reason}",
                    "blocked": True
                }

            # 2. Limit enforcement & risk evaluation
            safe_sql = CostAnalyzer.enforce_limit(raw_sql, default_limit=limit, max_limit=1000)
            risk = CostAnalyzer.evaluate_risk(raw_sql)

            # 3. Execution
            try:
                cols, rows = self.adapter.execute_read_only(safe_sql)
                return {
                    "success": True,
                    "query_executed": safe_sql,
                    "columns": cols,
                    "rows": rows,
                    "row_count": len(rows),
                    "risk_analysis": risk
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Database execution error: {str(e)}"
                }

        elif name == "analyze_query":
            raw_sql = arguments.get("query", "")
            is_safe, reason = ReadOnlyGuard.validate(raw_sql)
            risk = CostAnalyzer.evaluate_risk(raw_sql)
            return {
                "success": True,
                "is_read_only": is_safe,
                "security_verdict": reason,
                "performance_risk": risk
            }

        else:
            raise ValueError(f"Unknown tool: {name}")

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        req_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})

        if req_id is None:
            if method == "notifications/initialized":
                logger.info("Client completed initialization handshake.")
            return None

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": self.server_name,
                        "version": self.server_version
                    }
                }
            }

        elif method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.get_tools_definition()}
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            try:
                output = self.handle_tool_call(tool_name, tool_args)
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(output, indent=2, ensure_ascii=False)
                            }
                        ],
                        "isError": not output.get("success", True) if "success" in output else False
                    }
                }
            except Exception as e:
                logger.error(f"Error calling tool {tool_name}: {e}")
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": str(e)}
                }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }

    def run_stdio(self):
        logger.info(f"Starting {self.server_name} v{self.server_version} stdio listener...")
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                if response is not None:
                    sys.stdout.write(json.dumps(response) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                logger.error(f"Error processing stdio line: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(
        prog="pgsafe-mcp",
        description="PgSafe MCP: Zero-Trust Database Inspection & Safe Query Guard for AI Agents"
    )
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0.0")
    parser.add_argument("--db-url", type=str, default=None, help="Database connection URL (Postgres or SQLite). Defaults to DATABASE_URL or sqlite:///demo.db")
    args, unknown = parser.parse_known_args()
    server = PgSafeMCPServer(db_url=args.db_url)
    server.run_stdio()

if __name__ == "__main__":
    main()
