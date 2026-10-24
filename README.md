# PgSafe MCP (Lite Edition)

<a href="https://glama.ai/mcp/servers/@johannschiffer/pgsafe-mcp">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@johannschiffer/pgsafe-mcp/badge" alt="pgsafe-mcp MCP server" />
</a>


> **Free:** [Genesis Starter Kit](https://johanld.gumroad.com/l/genesis-starter-kit) (25 `.cursorrules`/`CLAUDE.md` rulesets + MCP configs). Try the [live config builder](https://johannschiffer.github.io).
> **Full stack:** all six servers in [Genesis Enterprise Suite ($19)](https://johanld.gumroad.com/l/genesis-enterprise-suite).


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
        "--from",
        "git+https://github.com/johannschiffer/pgsafe-mcp",
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

## ⚡ Features (Lite Edition)

- 🔒 **Enforced Read-Only Guard**: Automatically detects and blocks all destructive statements (`DROP`, `TRUNCATE`, `ALTER`, `UPDATE`, `INSERT`, `DELETE`).
- 🛑 **Anti-Chaining Protection**: Disallows multi-statement execution via semicolons.
- ⏱️ **Automatic LIMIT Injection**: Ensures every `SELECT` query has a capped `LIMIT` clause (default: 100 rows, max: 1,000) to protect database memory.
- 📊 **Zero-Cost Schema Reflection**: Tools to explore public tables and columns without executing custom introspection queries.
- 🪶 **Zero Dependency Core**: Native support for SQLite out of the box; optional PostgreSQL adapter.

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

## 💎 Need Enterprise Data Protection? Upgrade to PgSafe Pro

Running against live production workloads with sensitive customer data?

| Feature | Lite (Open Source) | Enterprise Suite ($19) |
|---|:---:|:---:|
| **Read-Only SQL Validation** | ✅ | ✅ |
| **Forced LIMIT Injection** | ✅ | ✅ |
| **PostgreSQL & SQLite** | ✅ | ✅ |
| **MySQL, MariaDB & ClickHouse** | ❌ | ✅ |
| **Automatic PII Redaction & Masking** *(Emails, Cards, Hashes)* | ❌ | ✅ |
| **Dry-Run Mutation Simulation** *(Auto-Rollback Test Harness)* | ❌ | ✅ |
| **Index Recommendation Advisor** | ❌ | ✅ |
| **Production Docker & Compose** | ❌ | ✅ |
| **Full Pytest Suite & Architecture Guide** | ❌ | ✅ |

👉 **[Get the Genesis Enterprise Suite ($19)](https://johanld.gumroad.com/l/genesis-enterprise-suite)**

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.

## Genesis MCP Ecosystem

| Module | What it does | Repo |
|---|---|---|
| **CrawlEngine MCP** | Anti-bot web scraping, clean Markdown, proxy rotation and TLS evasion | [GitHub](https://github.com/johannschiffer/crawlengine-mcp) |
| **BrowserBridge MCP** | Deterministic headless browser automation with cryptographic action receipts | [GitHub](https://github.com/johannschiffer/browserbridge-mcp) |
| **PgSafe MCP** (this repo) | Zero-trust PostgreSQL/SQLite guard, live PII masking, zero-downtime migration checks | [GitHub](https://github.com/johannschiffer/pgsafe-mcp) |
| **OmniBridge MCP** | Multi-channel notification and webhook bus with a persistent SQLite WAL queue | [GitHub](https://github.com/johannschiffer/omnibridge-mcp) |
| **SysFlow MCP** | Safe Linux administration plane: systemd, port audit, isolated execution | [GitHub](https://github.com/johannschiffer/sysflow-mcp) |
| **FastMCP Forge** | Production MCP server scaffolder: stdio, SSE and auth middleware | [GitHub](https://github.com/johannschiffer/fastmcp-forge) |

[Live config builder](https://johannschiffer.github.io) | [Starter Kit, free](https://johanld.gumroad.com/l/genesis-starter-kit) | [Enterprise Suite, $19](https://johanld.gumroad.com/l/genesis-enterprise-suite)