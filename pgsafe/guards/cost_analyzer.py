"""
Query Cost and Performance Safety Guard.
Enforces query limits and guards against unconstrained table scans.
"""
import re

class CostAnalyzer:
    @staticmethod
    def enforce_limit(sql: str, default_limit: int = 100, max_limit: int = 1000) -> str:
        """
        Inspects SQL and ensures a LIMIT clause is applied.
        If a LIMIT is present and exceeds max_limit, caps it.
        If no LIMIT is present, appends default_limit.
        """
        cleaned = sql.strip().rstrip(";")
        limit_match = re.search(r"\bLIMIT\s+(\d+)\b", cleaned, re.IGNORECASE)

        if limit_match:
            current_limit = int(limit_match.group(1))
            if current_limit > max_limit:
                return re.sub(r"\bLIMIT\s+\d+\b", f"LIMIT {max_limit}", cleaned, flags=re.IGNORECASE)
            return cleaned
        else:
            return f"{cleaned} LIMIT {default_limit}"

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
