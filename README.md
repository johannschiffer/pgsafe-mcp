# pgsafe-mcp

[![PyPI](https://img.shields.io/pypi/v/pgsafe-mcp.svg)](https://pypi.org/project/pgsafe-mcp/)
[![CI](https://github.com/johannschiffer/pgsafe-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/johannschiffer/pgsafe-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![MCP Compliant](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Support on Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-ff5e5b.svg)](https://ko-fi.com/johannschiffer)

<a href="https://glama.ai/mcp/servers/@johannschiffer/pgsafe-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@johannschiffer/pgsafe-mcp/badge" alt="pgsafe-mcp MCP server" />
</a>

**PgSafe MCP** is a read-only Model Context Protocol server for PostgreSQL and SQLite that enables AI coding agents in Claude Desktop, Cursor, Windsurf, and Antigravity to inspect schemas, run bounded analytical SQL queries with automatic PII masking, and test DML statements inside rolled-back SQLite transactions.

---

## Quickstart

Run directly via `uvx`:

```bash
uvx pgsafe-mcp
```

Claude Desktop / Cursor configuration:

```json
{
  "mcpServers": {
    "pgsafe-mcp": {
      "command": "uvx",
      "args": ["pgsafe-mcp"],
      "env": {
        "DATABASE_URL": "postgresql://readonly_user:password@localhost:5432/analytics_db"
      }
    }
  }
}
```

For SQLite databases:

```json
{
  "mcpServers": {
    "pgsafe-mcp": {
      "command": "uvx",
      "args": ["pgsafe-mcp"],
      "env": {
        "DATABASE_URL": "sqlite:///path/to/database.db"
      }
    }
  }
}
```

For PostgreSQL support when installing from source:

```bash
pip install "pgsafe-mcp[postgres]"
```

---

## Core Capabilities

1. **Lexer-Aware Read-Only SQL Guard:** Tokenizes SQL comments and string/dollar-quoted literals before validating statement boundaries, blocking `DROP`, `TRUNCATE`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `COPY`, `VACUUM`, `ATTACH`, `EXPLAIN ANALYZE`, and semicolon chaining.
2. **Engine-Level Read-Only Enforcement:** Configures PostgreSQL sessions with `SET default_transaction_read_only = on` and SQLite connections with `?mode=ro` plus `sqlite3.Connection.set_authorizer`.
3. **Top-Level Row Limit Enforcement:** Applies `LIMIT` bounds to outer `SELECT` and `WITH` queries without corrupting `PRAGMA`, `EXPLAIN`, `OFFSET`, or trailing SQL comments.
4. **Live PII Redaction:** Masks emails, payment card numbers, phone numbers, password hashes, and sensitive column values before returning rows to the LLM context.
5. **SQLite Dry-Run Mutation Harness:** Simulates single-statement `INSERT`, `UPDATE`, or `DELETE` changes inside an immediate transaction with authorizer restrictions and automatic `ROLLBACK`.
6. **Heuristic Query & Index Inspection:** Flags missing `WHERE` clauses, unconstrained joins, and candidate filter columns for indexing.

---

## MCP Tools

| Tool | Parameters | Description |
|---|---|---|
| `list_tables` | *(none)* | Lists user tables in the connected PostgreSQL or SQLite database |
| `describe_table` | `table_name` | Returns column names, types, nullability, defaults, and primary key metadata |
| `safe_query` | `query`, `limit`, `mask_pii` | Validates read-only SQL, enforces row limits, executes query, and masks PII |
| `dry_run_mutation` | `mutation_sql` | Simulates a single DML statement on SQLite inside an auto-rolled-back transaction |
| `analyze_query` | `query` | Evaluates read-only safety and full-scan / Cartesian join risk heuristics |
| `recommend_indexes` | `query` | Suggests candidate indexes from `WHERE` and `ORDER BY` predicates |
| `get_security_status` | *(none)* | Reports active guard status and credential-redacted `DATABASE_URL` |

---

## Related Open-Source MCP Servers

| Package | Description | Repository |
|---|---|---|
| **genesis-blackbox** | Runtime flight recorder and AST blast-radius crash compiler | [GitHub](https://github.com/johannschiffer/genesis-blackbox) |
| **crawlengine-mcp** | HTTP web extraction, clean Markdown conversion, and proxy rotation | [GitHub](https://github.com/johannschiffer/crawlengine-mcp) |
| **browserbridge-mcp** | Session-pooled HTTP DOM inspection and SHA-256 action trail receipts | [GitHub](https://github.com/johannschiffer/browserbridge-mcp) |
| **omnibridge-mcp** | Multi-channel notification bus with SQLite retry queue | [GitHub](https://github.com/johannschiffer/omnibridge-mcp) |
| **sysflow-mcp** | Linux resource inspection, systemd unit generator, and log tailer | [GitHub](https://github.com/johannschiffer/sysflow-mcp) |
| **fastmcp-forge** | MCP server framework and project scaffolder | [GitHub](https://github.com/johannschiffer/fastmcp-forge) |

## Support

If this project is useful in your workflow, you can support ongoing maintenance on [Ko-fi](https://ko-fi.com/johannschiffer).

## License

MIT License. Copyright (c) 2026 [Johann Schiffer](https://github.com/johannschiffer).
