"""
Unit tests for CostAnalyzer limit enforcement and risk heuristics.
"""
from pgsafe.guards.cost_analyzer import CostAnalyzer

def test_cost_analyzer_enforce_limit():
    # Append default limit
    q1 = "SELECT * FROM users"
    capped1 = CostAnalyzer.enforce_limit(q1, default_limit=100)
    assert "LIMIT 100" in capped1

    # Keep acceptable limit
    q2 = "SELECT * FROM users LIMIT 50"
    capped2 = CostAnalyzer.enforce_limit(q2, default_limit=100, max_limit=1000)
    assert "LIMIT 50" in capped2

    # Cap excessive limit
    q3 = "SELECT * FROM users LIMIT 50000"
    capped3 = CostAnalyzer.enforce_limit(q3, default_limit=100, max_limit=1000)
    assert "LIMIT 1000" in capped3

def test_cost_analyzer_risk_evaluation():
    risky = "SELECT * FROM users"
    eval_result = CostAnalyzer.evaluate_risk(risky)
    assert eval_result["risk_level"] == "medium"
    assert any("WHERE" in w for w in eval_result["warnings"])

    safe = "SELECT * FROM users WHERE id = 10"
    eval_safe = CostAnalyzer.evaluate_risk(safe)
    assert eval_safe["risk_level"] == "low"
