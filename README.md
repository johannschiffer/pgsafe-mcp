# pgsafe-mcp (v2.0.0)

[![PyPI version](https://img.shields.io/badge/PyPI-v2.0.0-blue.svg)](https://pypi.org/project/pgsafe-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Support on Ko-fi](https://img.shields.io/badge/Support%20on-Ko--fi-ff5e5b.svg)](https://ko-fi.com/johannschiffer)

> **100% Free & Open Source (MIT)**: All features, proxy rotation, migration simulation, Docker stacks, and recipes are completely unlocked. Support open development on [Ko-fi](https://ko-fi.com/johannschiffer).

> ### ⚡ Open Source Ecosystem & Community Tools
> | Resource | Access | Description |
> |---|---|---|
> | **Ruleset Bundle** | **100% Free** | 55+ production rulesets & MCP config templates. [Download Free](https://johannschiffer.github.io/) |
> | **Support & Donate** | **Ko-fi** | Support open-source maintenance. [Support on Ko-fi](https://ko-fi.com/johannschiffer) |

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

## ⚡ Features (Open Source v2.0)

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

| Feature | v1.0 (Legacy) | v2.0 (Open Source) |
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

[Live config builder](https://johannschiffer.github.io) | [GitHub Profile](https://github.com/johannschiffer) | [Support on Ko-fi ☕](https://ko-fi.com/johannschiffer)

## Recommended Infrastructure & Sponsorship

- **Sponsorship & Corporate Support**: Support continued maintenance and priority feature requests via [GitHub Sponsors](https://github.com/sponsors/johannschiffer).
- **Verified Cloud & Network Infrastructure**:
  - **High-Performance VPS & Nodes**: [Hetzner Cloud](https://www.hetzner.com/cloud) & [DigitalOcean](https://m.do.co/c/johannschiffer)
  - **Reliable Proxy Pool & IP Rotation**: [Webshare](https://www.webshare.io/) & [Bright Data](https://brightdata.com/)
  - **Documentation & Setup Guides**: [johannschiffer.github.io](https://johannschiffer.github.io/)