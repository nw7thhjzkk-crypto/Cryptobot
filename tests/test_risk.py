import pytest
from bot.risk import RiskEngine, check_portfolio_risk

def test_risk_engine_paper_mode():
    engine = RiskEngine(paper_mode=True, max_position_pct=0.20)

    res = engine.evaluate_order("AAPL", "BUY", 10, 150.0, 10000.0, 10000.0)
    assert res["approved"] is True

    res2 = engine.evaluate_order("AAPL", "BUY", 100, 150.0, 10000.0, 10000.0)
    assert res2["approved"] is False
    assert "exceeds max allowed" in res2["reason"]

def test_risk_engine_invalid_data():
    engine = RiskEngine(paper_mode=True, max_position_pct=0.20)

    res = engine.evaluate_order("AAPL", "BUY", 10, 150.0, -100.0, 10000.0)
    assert res["approved"] is False

    res2 = engine.evaluate_order("AAPL", "BUY", 10, float('nan'), 10000.0, 10000.0)
    assert res2["approved"] is False

def test_check_portfolio_risk():
    open_pos = [
        {"symbol": "MSFT", "unrealized_pl": -50.0},
        {"symbol": "TSLA", "unrealized_pl": 20.0}
    ]

    res = check_portfolio_risk(open_pos, 400.0, 0.05, 10000.0)
    assert res is True

    res2 = check_portfolio_risk(open_pos, 460.0, 0.05, 10000.0)
    assert res2 is False
