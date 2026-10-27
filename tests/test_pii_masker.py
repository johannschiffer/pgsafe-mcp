"""
Unit tests for PIIMasker data redaction engine.
"""
from pgsafe.core.pii_masker import PIIMasker

def test_pii_mask_email():
    raw = "Contact admin@example.com for support"
    masked = PIIMasker.mask_string(raw)
    assert "admin@example.com" not in masked
    assert "a***@example.com" in masked

def test_pii_mask_credit_card():
    raw = "Card: 4532-1234-5678-9012"
    masked = PIIMasker.mask_string(raw)
    assert "4532-1234-5678" not in masked
    assert "****-****-****-9012" in masked

def test_pii_mask_password_hash():
    raw = "$2b$12$e8MrOoJ5Vq3jX9H3lX3Qqe8R1S5eX2w1O4P7q0K8L9M6N4P2Q0R1S"
    masked = PIIMasker.mask_string(raw)
    assert "[REDACTED_PASSWORD_HASH]" in masked

def test_pii_mask_dataset():
    cols = ["id", "username", "password_hash", "email"]
    rows = [
        [1, "alice", "super_secret_raw_pass", "alice.smith@company.org"],
        [2, "bob", "another_secret", "bob_dev@startup.io"]
    ]
    masked = PIIMasker.mask_dataset(cols, rows)
    # Password column must be fully redacted
    assert masked[0][2] == "[REDACTED_CONFIDENTIAL]"
    assert masked[1][2] == "[REDACTED_CONFIDENTIAL]"
    # Email column must have masked string
    assert "alice.smith@company.org" not in masked[0][3]
    assert "a***@company.org" in masked[0][3]
