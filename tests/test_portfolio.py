import pytest
from bot.portfolio import PortfolioEngine

def test_portfolio_engine_blocks_averaging_down():
    engine = PortfolioEngine(max_portfolio_exposure=0.9, max_positions=10)
    open_positions = [{"symbol": "AAPL", "qty": 10, "current_price": 150.0}]

    # Trying to buy AAPL again should be blocked
    res = engine.evaluate("AAPL", "BUY", open_positions, 150.0, 10000.0)
    assert res["approved"] is False
    assert "Already holding" in res["reason"]

def test_portfolio_engine_max_positions():
    engine = PortfolioEngine(max_portfolio_exposure=0.9, max_positions=1)
    open_positions = [{"symbol": "AAPL", "qty": 10, "current_price": 150.0}]

    # Trying to buy TSLA when max_positions is 1
    res = engine.evaluate("TSLA", "BUY", open_positions, 200.0, 10000.0)
    assert res["approved"] is False
    assert "Max positions reached" in res["reason"]
