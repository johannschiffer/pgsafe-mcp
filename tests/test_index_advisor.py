"""
Unit tests for IndexAdvisor.
"""
from pgsafe.core.index_advisor import IndexAdvisor

def test_index_advisor_recommendation():
    sql = "SELECT id, name FROM customers WHERE email = 'test@example.com' AND status = 'active';"
    recs = IndexAdvisor.analyze_and_recommend(sql)
    assert len(recs) > 0
    rec = recs[0]
    assert rec["table"] == "customers"
    assert "email" in rec["columns"]
    assert "CREATE INDEX" in rec["suggested_index_ddl"]
