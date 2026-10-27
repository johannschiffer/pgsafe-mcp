"""
Real-Time PII (Personally Identifiable Information) Redaction Engine.
Prevents customer emails, credit cards, password hashes, and tokens from leaking into LLM context windows.
"""
import re
from typing import List, Any, Union

EMAIL_REGEX = re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b")
CREDIT_CARD_REGEX = re.compile(r"\b(?:\d{4}[-\s]?){3}(\d{4})\b")
PHONE_REGEX = re.compile(r"\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?(\d{4})\b")
HASH_REGEX = re.compile(r"(?:\$2[aby]?\$\d{2}\$[./A-Za-z0-9]{53}|\$argon2[a-z]?\$[^\s]+|\b[a-fA-F0-9]{64}\b)")

SENSITIVE_COLUMN_KEYWORDS = {
    "password", "passwd", "pwd", "hash", "secret", "token", "auth",
    "ssn", "cvv", "credit_card", "card_number", "pin", "api_key"
}

class PIIMasker:
    @staticmethod
    def mask_string(val: str) -> str:
        if not isinstance(val, str) or not val:
            return val

        # 1. Mask Hashes
        val = HASH_REGEX.sub("[REDACTED_PASSWORD_HASH]", val)

        # 2. Mask Credit Cards (keep last 4 digits)
        val = CREDIT_CARD_REGEX.sub(r"****-****-****-\1", val)

        # 3. Mask Emails (keep first char and domain)
        val = EMAIL_REGEX.sub(r"\1***@\2", val)

        # 4. Mask Phone Numbers (keep last 4)
        val = PHONE_REGEX.sub(r"***-***-\2", val)

        return val

    @classmethod
    def mask_dataset(cls, columns: List[str], rows: List[List[Any]]) -> List[List[Any]]:
        """Masks rows based on column name heuristics and cell regex matching."""
        sensitive_col_indices = {
            i for i, col in enumerate(columns)
            if any(k in col.lower() for k in SENSITIVE_COLUMN_KEYWORDS)
        }

        masked_rows = []
        for row in rows:
            new_row = []
            for i, cell in enumerate(row):
                if cell is None:
                    new_row.append(None)
                    continue

                if i in sensitive_col_indices:
                    new_row.append("[REDACTED_CONFIDENTIAL]")
                elif isinstance(cell, str):
                    new_row.append(cls.mask_string(cell))
                else:
                    new_row.append(cell)
            masked_rows.append(new_row)

        return masked_rows
