import pytest
from bot.risk import RiskEngine

def test_daily_loss_limit():
    engine = RiskEngine(paper_mode=True, max_position_pct=0.2, max_daily_loss=0.05)
    res1 = engine.evaluate_order("AAPL", "BUY", 10, 100, 9400.0, 9000.0, start_of_day_equity=10000.0)
    assert res1["approved"] is False
    assert "DAILY_LOSS_LIMIT" in res1["reason"]

    res2 = engine.evaluate_order("AAPL", "BUY", 10, 100, 9600.0, 9000.0, start_of_day_equity=10000.0)
    assert res2["approved"] is True
