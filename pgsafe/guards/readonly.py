"""
SQL Read-Only Security Guard.
Inspects SQL statements to guarantee no mutations or destructive statements are executed.
"""
import re
from typing import Tuple

BLOCKED_PATTERNS = [
    r"\bDROP\b",
    r"\bTRUNCATE\b",
    r"\bDELETE\b",
    r"\bUPDATE\b",
    r"\bINSERT\b",
    r"\bALTER\b",
    r"\bCREATE\b",
    r"\bGRANT\b",
    r"\bREVOKE\b",
    r"\bEXEC\b",
    r"\bEXECUTE\b",
    r"\bCALL\b",
    r"\bRENAME\b",
    r"\bREPLACE\b"
]

COMPILED_BLOCKED = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

class ReadOnlyGuard:
    @staticmethod
    def validate(sql: str) -> Tuple[bool, str]:
        """
        Validates whether SQL is strictly read-only.
        Returns (is_safe: bool, reason: str).
        """
        cleaned = sql.strip()
        if not cleaned:
            return False, "Empty query provided."

        # Remove SQL comments (-- comment and /* comment */)
        cleaned_no_comments = re.sub(r"--.*?$", "", cleaned, flags=re.MULTILINE)
        cleaned_no_comments = re.sub(r"/\*.*?\*/", "", cleaned_no_comments, flags=re.DOTALL).strip()

        # Check semicolon chaining (disallow multi-statement injection)
        statements = [s.strip() for s in cleaned_no_comments.split(";") if s.strip()]
        if len(statements) > 1:
            return False, "Multiple SQL statements detected (semicolon chaining disallowed)."

        first_word = statements[0].split()[0].upper() if statements else ""
        allowed_starts = {"SELECT", "EXPLAIN", "WITH", "PRAGMA", "SHOW", "DESCRIBE"}
        if first_word not in allowed_starts:
            return False, f"Statement type '{first_word}' is disallowed. Only read-only queries are permitted."

        for pattern in COMPILED_BLOCKED:
            if pattern.search(cleaned_no_comments):
                match = pattern.pattern.replace(r"\b", "")
                return False, f"Blocked keyword detected in query: '{match}'"

        return True, "Query verified as read-only."
