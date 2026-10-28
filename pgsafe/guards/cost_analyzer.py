"""
Query Cost and Performance Safety Guard.
Enforces top-level query limits and guards against unconstrained table scans.
"""

import re
from typing import Optional, Tuple


def _strip_trailing_comments_and_semicolon(sql: str) -> str:
    """Removes trailing comments and semicolons so appended clauses are never commented out."""
    s = sql.strip()
    changed = True
    while changed and s:
        changed = False
        if s.endswith(";"):
            s = s[:-1].rstrip()
            changed = True
        # Strip trailing line comment on the final line if not inside quotes
        last_nl = s.rfind("\n")
        last_line = s[last_nl + 1:]
        dash_idx = last_line.find("--")
        if dash_idx != -1 and last_line[:dash_idx].count("'") % 2 == 0:
            s = (s[:last_nl + 1] + last_line[:dash_idx]).rstrip()
            changed = True
        if s.endswith("*/"):
            open_idx = s.rfind("/*")
            if open_idx != -1:
                s = s[:open_idx].rstrip()
                changed = True
    return s


def _mask_top_level(sql: str) -> str:
    """Replaces parenthesized subqueries, comments, and string literals with spaces of identical length."""
    chars = list(sql)
    n = len(chars)
    i = 0
    depth = 0
    while i < n:
        c = sql[i]
        if c == "'" :
            chars[i] = " "
            i += 1
            while i < n:
                if sql[i] == "'" and i + 1 < n and sql[i + 1] == "'":
                    chars[i] = " "
                    chars[i + 1] = " "
                    i += 2
                    continue
                if sql[i] == "'":
                    chars[i] = " "
                    i += 1
                    break
                chars[i] = " "
                i += 1
            continue
        if c == "-" and i + 1 < n and sql[i + 1] == "-":
            while i < n and sql[i] != "\n":
                chars[i] = " "
                i += 1
            continue
        if c == "/" and i + 1 < n and sql[i + 1] == "*":
            chars[i] = " "
            chars[i + 1] = " "
            i += 2
            while i < n:
                if sql[i] == "*" and i + 1 < n and sql[i + 1] == "/":
                    chars[i] = " "
                    chars[i + 1] = " "
                    i += 2
                    break
                chars[i] = " "
                i += 1
            continue
        if c == "(":
            depth += 1
            chars[i] = " "
        elif c == ")":
            chars[i] = " "
            depth = max(0, depth - 1)
        elif depth > 0:
            chars[i] = " "
        i += 1
    return "".join(chars)


class CostAnalyzer:
    @staticmethod
    def enforce_limit(sql: str, default_limit: int = 100, max_limit: int = 1000) -> str:
        """
        Inspects SQL and ensures a top-level LIMIT clause is applied to SELECT/WITH queries.
        Leaves PRAGMA, EXPLAIN, SHOW, and DESCRIBE untouched.
        """
        effective_default = max(1, min(int(default_limit), int(max_limit)))
        cleaned = _strip_trailing_comments_and_semicolon(sql)
        if not cleaned:
            return cleaned

        top_level = _mask_top_level(cleaned)
        first_tokens = top_level.strip().split()
        first_kw = first_tokens[0].upper() if first_tokens else ""
        if first_kw not in ("SELECT", "WITH"):
            return cleaned

        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", top_level, re.IGNORECASE)
        if limit_match:
            current_limit = int(limit_match.group(1))
            if current_limit > max_limit:
                start, end = limit_match.span()
                return f"{cleaned[:start]}LIMIT {max_limit}{cleaned[end:]}"
            return cleaned

        offset_match = re.search(r"\bOFFSET\s+\d+\b", top_level, re.IGNORECASE)
        if offset_match:
            pos = offset_match.start()
            return f"{cleaned[:pos].rstrip()} LIMIT {effective_default} {cleaned[pos:]}"

        return f"{cleaned} LIMIT {effective_default}"

    @staticmethod
    def evaluate_risk(sql: str) -> dict:
        """Evaluates heuristic risk metrics."""
        warnings = []
        sql_upper = sql.upper()

        if "WHERE" not in sql_upper and "SELECT" in sql_upper:
            warnings.append("Query lacks a WHERE clause; full table scan may occur.")

        if "JOIN" in sql_upper and "ON" not in sql_upper and "USING" not in sql_upper:
            warnings.append("JOIN statement without explicit ON/USING condition (possible Cartesian product).")

        return {
            "risk_level": "medium" if warnings else "low",
            "warnings": warnings
        }
