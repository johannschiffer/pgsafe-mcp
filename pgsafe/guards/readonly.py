"""
SQL Read-Only Security Guard.
Tokenizes SQL comments and string literals safely before checking statement boundaries and keywords.
"""

import re
from typing import Tuple

BLOCKED_KEYWORDS = [
    "DROP",
    "TRUNCATE",
    "DELETE",
    "UPDATE",
    "INSERT",
    "ALTER",
    "CREATE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "CALL",
    "RENAME",
    "REPLACE",
    "MERGE",
    "VACUUM",
    "ATTACH",
    "DETACH",
    "COPY",
    "DO",
    "SET",
    "RESET",
    "LOAD_EXTENSION",
    "REINDEX",
    "CLUSTER",
    "LOCK",
    "PG_READ_FILE",
    "PG_READ_BINARY_FILE",
    "PG_LS_DIR",
    "LO_IMPORT",
    "LO_EXPORT",
    "PG_TERMINATE_BACKEND",
    "PG_CANCEL_BACKEND",
    "DBLINK",
]

COMPILED_BLOCKED = [(kw, re.compile(rf"\b{kw}\b", re.IGNORECASE)) for kw in BLOCKED_KEYWORDS]


def sanitize_sql_literals_and_comments(sql: str) -> Tuple[bool, str]:
    """
    Single-pass SQL scanner that replaces comments with spaces (preventing token coalescing)
    and masks string/dollar-quoted literals so semicolons or comment markers inside strings
    cannot bypass statement validation.
    Returns (valid_syntax, normalized_sql).
    """
    out = []
    i = 0
    n = len(sql)

    while i < n:
        ch = sql[i]

        # Single-line comment: -- ... \n
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            nl = sql.find("\n", i + 2)
            out.append(" ")
            if nl == -1:
                break
            out.append("\n")
            i = nl + 1
            continue

        # Block comment: /* ... */ (supports nested block comments)
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            depth = 1
            i += 2
            while i < n and depth > 0:
                if sql[i] == "/" and i + 1 < n and sql[i + 1] == "*":
                    depth += 1
                    i += 2
                elif sql[i] == "*" and i + 1 < n and sql[i + 1] == "/":
                    depth -= 1
                    i += 2
                else:
                    i += 1
            if depth != 0:
                return False, "Unclosed block comment in SQL query."
            out.append(" ")
            continue

        # Single-quoted string literal: '...' (with '' or \' escapes)
        if ch == "'":
            i += 1
            closed = False
            while i < n:
                if sql[i] == "'":
                    if i + 1 < n and sql[i + 1] == "'":
                        i += 2
                        continue
                    closed = True
                    i += 1
                    break
                if sql[i] == "\\" and i + 1 < n:
                    i += 2
                    continue
                i += 1
            if not closed:
                return False, "Unclosed string literal in SQL query."
            out.append(" '' ")
            continue

        # Double-quoted identifier: "..."
        if ch == '"':
            i += 1
            ident_chars = []
            closed = False
            while i < n:
                if sql[i] == '"':
                    if i + 1 < n and sql[i + 1] == '"':
                        ident_chars.append('"')
                        i += 2
                        continue
                    closed = True
                    i += 1
                    break
                ident_chars.append(sql[i])
                i += 1
            if not closed:
                return False, "Unclosed quoted identifier in SQL query."
            safe_ident = "".join(c if (c.isalnum() or c == "_") else "_" for c in ident_chars)
            out.append(f' "{safe_ident}" ')
            continue

        # PostgreSQL dollar-quoted string: $tag$...$tag$
        if ch == "$":
            m = re.match(r"\$([A-Za-z_][A-Za-z0-9_]*)?\$", sql[i:])
            if m:
                tag = m.group(0)
                end_idx = sql.find(tag, i + len(tag))
                if end_idx == -1:
                    return False, "Unclosed dollar-quoted string in SQL query."
                out.append(" '' ")
                i = end_idx + len(tag)
                continue

        out.append(ch)
        i += 1

    return True, "".join(out)


class ReadOnlyGuard:
    @staticmethod
    def validate(sql: str) -> Tuple[bool, str]:
        """
        Validates whether SQL is strictly read-only.
        Returns (is_safe: bool, reason: str).
        """
        if not isinstance(sql, str) or not sql.strip():
            return False, "Empty query provided."

        ok, normalized = sanitize_sql_literals_and_comments(sql)
        if not ok:
            return False, normalized

        cleaned = normalized.strip()
        if not cleaned:
            return False, "Empty query provided."

        statements = [s.strip() for s in cleaned.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements detected (semicolon chaining disallowed)."

        stmt = statements[0]
        tokens = stmt.split()
        first_word = tokens[0].upper() if tokens else ""
        allowed_starts = {"SELECT", "EXPLAIN", "WITH", "PRAGMA", "SHOW", "DESCRIBE"}
        if first_word not in allowed_starts:
            return False, f"Statement type '{first_word}' is disallowed. Only read-only queries are permitted."

        # EXPLAIN ANALYZE actually executes the underlying query in PostgreSQL
        if first_word == "EXPLAIN" and re.search(r"\bANALYZE\b", stmt, re.IGNORECASE):
            return False, "Blocked keyword detected in query: 'EXPLAIN ANALYZE'"

        # Disallow PRAGMA assignments (e.g., PRAGMA writable_schema = 1)
        if first_word == "PRAGMA" and "=" in stmt:
            return False, "Blocked keyword detected in query: 'PRAGMA assignment'"

        for kw, pattern in COMPILED_BLOCKED:
            if pattern.search(stmt):
                return False, f"Blocked keyword detected in query: '{kw}'"

        return True, "Query verified as read-only."
