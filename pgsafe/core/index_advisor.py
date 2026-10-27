"""
Index & Query Optimization Advisor (PgSafe Feature).
Analyzes WHERE filters, ORDER BY clauses, and JOIN keys to recommend optimal database indexes.
"""
import re
from typing import List, Dict, Any

class IndexAdvisor:
    @staticmethod
    def analyze_and_recommend(sql: str) -> List[Dict[str, str]]:
        """Parses SQL and suggests composite or single column indexes."""
        recommendations = []

        # Find table name: FROM table_name
        from_match = re.search(r"\bFROM\s+([A-Za-z0-9_]+)\b", sql, re.IGNORECASE)
        table_name = from_match.group(1) if from_match else "target_table"

        # Find WHERE column conditions: WHERE col = ... or col > ...
        where_match = re.search(r"\bWHERE\s+(.*?)(?:\bORDER\b|\bGROUP\b|\bLIMIT\b|$)", sql, re.IGNORECASE | re.DOTALL)
        if where_match:
            where_clause = where_match.group(1)
            # Find column identifiers compared with =, >, <, LIKE, IN
            cols = re.findall(r"([A-Za-z0-9_]+)\s*(?:=|!=|>|<|>=|<=|\bLIKE\b|\bIN\b)", where_clause, re.IGNORECASE)
            # Filter common SQL keywords
            valid_cols = [c for c in cols if c.upper() not in {"AND", "OR", "NOT", "CASE", "WHEN"}]
            if valid_cols:
                primary_col = valid_cols[0]
                idx_name = f"idx_{table_name}_{primary_col}"
                ddl = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({', '.join(valid_cols[:2])});"
                recommendations.append({
                    "table": table_name,
                    "columns": valid_cols[:2],
                    "suggested_index_ddl": ddl,
                    "reason": f"Accelerates filter lookup on filtered columns: {', '.join(valid_cols[:2])}"
                })

        return recommendations
