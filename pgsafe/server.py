"""
PgSafe MCP: Model Context Protocol Server
Includes Zero-Trust Read-Only Guard, Real-Time PII Masking,
Dry-Run Mutation Simulation Harness, and Index Recommendation Advisor.
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
from .core.pii_masker import PIIMasker
from .core.dry_run_harness import DryRunHarness
from .core.index_advisor import IndexAdvisor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [PgSafe] %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger("PgSafeServer")

class PgSafeServer:
    def __init__(self, db_url: Optional[str] = None):
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///data/nexus.db")
        self.server_name = "pgsafe-mcp"
        self.server_version = "1.0.0"
        self.adapter = self._init_adapter(self.db_url)

    def _init_adapter(self, url: str):
        if url.startswith("postgres://") or url.startswith("postgresql://"):
            return PostgresAdapter(url)
        else:
            clean_path = url.replace("sqlite:///", "").replace("sqlite://", "")
            return SQLiteAdapter(clean_path)

    def get_tools_definition(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list_tables",
                "description": "List all database tables available for inspection.",
                "inputSchema": {"type": "object", "properties": {}}
            },
            {
                "name": "describe_table",
                "description": "Inspect column names, data types, nullability, and primary keys for a table.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "table_name": {"type": "string", "description": "Table name to inspect"}
                    },
                    "required": ["table_name"]
                }
            },
            {
                "name": "safe_query",
                "description": "Execute a strictly read-only SQL query with automatic LIMIT enforcement and real-time PII redaction.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL SELECT/EXPLAIN query"},
                        "limit": {"type": "integer", "description": "Max rows to return (default: 100, max: 1000)"},
                        "mask_pii": {"type": "boolean", "description": "Redact customer emails, credit cards and password hashes (default: true)"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "dry_run_mutation",
                "description": "Simulate an INSERT, UPDATE, or DELETE query in an isolated transaction with guaranteed auto-ROLLBACK.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "mutation_sql": {"type": "string", "description": "Mutation SQL statement to test"}
                    },
                    "required": ["mutation_sql"]
                }
            },
            {
                "name": "analyze_query",
                "description": "Evaluate query complexity, full table scan risks, and missing filters without execution.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to inspect"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "recommend_indexes",
                "description": "Analyze SQL query filters to recommend optimal composite or single-column indexes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "SQL query to optimize"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_security_status",
                "description": "Check status of active zero-trust security engines (PII Masker, Read-Only Guard, Dry-Run Harness).",
                "inputSchema": {"type": "object", "properties": {}}
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
            mask_pii = arguments.get("mask_pii", True)

            is_safe, reason = ReadOnlyGuard.validate(raw_sql)
            if not is_safe:
                return {
                    "success": False,
                    "error": f"Security Guard Blocked Query: {reason}",
                    "blocked": True
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
                    "risk_analysis": risk
                }
            except Exception as e:
                return {"success": False, "error": f"Database execution error: {str(e)}"}

        elif name == "dry_run_mutation":
            mutation_sql = arguments.get("mutation_sql", "")
            # Only supports SQLite or local adapters with transaction rollback
            if isinstance(self.adapter, SQLiteAdapter):
                return DryRunHarness.simulate_sqlite(self.adapter.db_path, mutation_sql)
            else:
                return {
                    "success": False,
                    "error": "Dry-run mutation currently configured for SQLite/Local engines in this version."
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

        elif name == "recommend_indexes":
            raw_sql = arguments.get("query", "")
            recommendations = IndexAdvisor.analyze_and_recommend(raw_sql)
            return {
                "success": True,
                "query": raw_sql,
                "recommendations": recommendations,
                "count": len(recommendations)
            }

        elif name == "get_security_status":
            return {
                
                "database_url": self.db_url,
                "guards": {
                    "readonly_guard": "ACTIVE",
                    "pii_masking_engine": "ACTIVE",
                    "dry_run_mutation_harness": "ACTIVE",
                    "cost_analyzer": "ACTIVE",
                    "index_advisor": "ACTIVE"
                }
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
    server = PgSafeServer()
    server.run_stdio()

if __name__ == "__main__":
    main()
