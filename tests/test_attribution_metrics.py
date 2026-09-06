import pytest
from bot.research.attribution import AttributionTracker

def test_attribution_metrics():
    tracker = AttributionTracker()
    tracker.log_trade("test", 0.1)
    assert tracker.get_strategy_weight("test") == 1.0

    tracker.strategy_returns["test"] = [0.01, 0.02, -0.01, 0.015, -0.005]*4
    metrics = tracker.get_strategy_metrics("test")
    assert metrics["trade_count"] == 20
    assert metrics["win_rate"] == 0.6
    assert metrics["profit_factor"] > 1.0

    weight = tracker.get_strategy_weight("test")
    assert weight > 1.0
