# pgsafe-mcp (v1.0.0)

[![PyPI version](https://img.shields.io/badge/PyPI-v1.0.0-blue.svg)](https://pypi.org/project/pgsafe-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Support on Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-ff5e5b.svg)](https://ko-fi.com/johannschiffer)

<a href="https://glama.ai/mcp/servers/@johannschiffer/pgsafe-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@johannschiffer/pgsafe-mcp/badge" alt="pgsafe-mcp MCP server" />
</a>

[![PyPI](https://img.shields.io/pypi/v/pgsafe-mcp.svg)](https://pypi.org/project/pgsafe-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-brightgreen.svg)](https://python.org)
[![MCP Compliant](https://img.shields.io/badge/MCP-2024--11--05-purple.svg)](https://modelcontextprotocol.io)

**PgSafe MCP** is a Zero-Trust Model Context Protocol server that enables AI agents in **Claude Desktop**, **Cursor**, **Windsurf**, and **Antigravity** to inspect schemas and run analytical SQL queries without risking accidental data loss, destructive mutations (`DROP`, `TRUNCATE`, `DELETE`), or runaway table scans.

---

## Run without cloning

```bash
uvx pgsafe-mcp
```

Claude Desktop / Cursor config entry:

```json
{
  "mcpServers": {
    "pgsafe-mcp": {
      "command": "uvx",
      "args": [
        "pgsafe-mcp"
      ]
    }
  }
}
```

[![CI](https://github.com/johannschiffer/pgsafe-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/johannschiffer/pgsafe-mcp/actions/workflows/ci.yml)

## 🛡️ Why PgSafe MCP?

Giving an AI assistant raw access to your database is terrifying:
1. **Accidental Deletions:** One ambiguous prompt can lead an LLM to generate `DROP TABLE` or `DELETE FROM users;`.
2. **Production Table Locks:** An unindexed query with a multi-table Cartesian product can consume 100% CPU and lock production tables.
3. **Multi-Statement Injection:** LLMs can be tricked via prompt injection into chaining malicious SQL commands (`SELECT 1; TRUNCATE audit_logs;`).

**PgSafe** acts as a strict guardrail sitting between the AI agent and your database engine.

---

## Features

- 🛡️ **Read-Only SQL Validation**: Zero-trust AST query validation blocking destructive statements (`DROP`, `TRUNCATE`, `DELETE`, `ALTER`).
- 🛑 **Anti-Chaining Protection**: Disallows multi-statement execution via semicolons.
- 🔍 **Safe Schema Inspector**: Read-only table schema and column definition discovery.
- ⏱️ **Auto-LIMIT Injection**: Enforces max row caps to prevent memory exhaustion and table locks.
- 🌐 **Multi-Database Support**: PostgreSQL, SQLite, MySQL, MariaDB, and ClickHouse.
- 🎭 **Automatic PII Redaction & Masking**: Masks emails, credit cards, and sensitive identifiers on the fly.
- 🧪 **Dry-Run Mutation Simulation**: Auto-rollback transaction harness for testing migrations safely.
- 💡 **Index Recommendation Advisor**: Analyzes query execution plans and suggests missing indexes.
- 🐳 **Production Docker & Compose**: Sandboxed container environment.
---

## 🚀 Quick Setup in 2 Minutes

### 1. Installation

```bash
git clone https://github.com/johannschiffer/pgsafe-mcp.git
cd pgsafe-mcp
pip install .
```

For PostgreSQL support:
```bash
pip install "psycopg[binary]>=3.1.0"
```

### 2. Configure Claude Desktop (`claude_desktop_config.json`)

On Linux: `~/.config/Claude/claude_desktop_config.json`  
On macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`  
On Windows: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "pgsafe": {
      "command": "python",
      "args": ["-m", "pgsafe.server"],
      "cwd": "/path/to/pgsafe-mcp",
      "env": {
        "DATABASE_URL": "postgresql://user:password@localhost:5432/production_db"
      }
    }
  }
}
```

For SQLite, simply point to your `.db` file:
```json
{
  "mcpServers": {
    "pgsafe": {
      "command": "python",
      "args": ["-m", "pgsafe.server"],
      "cwd": "/path/to/pgsafe-mcp",
      "env": {
        "DATABASE_URL": "sqlite:///data/nexus.db"
      }
    }
  }
}
```

---

## 🛠️ MCP Tools Exposed to AI Agents

| Tool | Parameters | Description |
|---|---|---|
| `list_tables` | *(none)* | Returns list of all user tables in the database |
| `describe_table` | `table_name` | Returns column names, data types, nullability, and primary keys |
| `safe_query` | `query`, `limit` | Executes strictly read-only SQL with forced LIMIT enforcement |
| `analyze_query` | `query` | Inspects SQL for unindexed table scan and Cartesian join risks |

---

## Genesis MCP Ecosystem

| Module | Description | Repository |
|---|---|---|
| **CrawlEngine MCP** | Anti-bot web scraping, clean Markdown, proxy rotation, and TLS evasion | [GitHub](https://github.com/johannschiffer/crawlengine-mcp) |
| **BrowserBridge MCP** | Deterministic headless browser automation with cryptographic action receipts | [GitHub](https://github.com/johannschiffer/browserbridge-mcp) |
| **PgSafe MCP** | Zero-trust PostgreSQL/SQLite guard, live PII masking, and schema inspection | [GitHub](https://github.com/johannschiffer/pgsafe-mcp) |
| **OmniBridge MCP** | Multi-channel notification bus with persistent SQLite queue | [GitHub](https://github.com/johannschiffer/omnibridge-mcp) |
| **SysFlow MCP** | Safe Linux administration, systemd automation, and port auditing | [GitHub](https://github.com/johannschiffer/sysflow-mcp) |
| **FastMCP Forge** | Production FastMCP server scaffolder with stdio and SSE middleware | [GitHub](https://github.com/johannschiffer/fastmcp-forge) |

## Support

If you find this project helpful, you can support its ongoing maintenance on [Ko-fi](https://ko-fi.com/johannschiffer).

## License

MIT © 2026 [Johann Schiffer](https://github.com/johannschiffer)
